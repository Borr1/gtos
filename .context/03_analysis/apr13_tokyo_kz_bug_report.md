# April 13 Tokyo KZ — Live Bug Report & Fix Validation

**Date:** April 13, 2026
**Session:** Tokyo Kill Zone (00:15–02:45 UTC)
**Author:** Claude Code (engineering agent)
**Audience:** Strategic advisors, future engineering sessions
**Status:** All fixes deployed, validated in production, uncommitted

---

## Executive Summary

During active per-candle monitoring of the Tokyo kill zone, we discovered and fixed **5 issues** — 2 in trading logic (one of which killed a live CANDIDATE signal), and 3 in operational tooling. All fixes were deployed mid-session and validated against subsequent candle processing. Zero new errors after fixes were applied.

**Impact of the most critical bug:** A CANDIDATE signal (grade A+, conf=82) on USDJPY at 00:30 UTC was killed by a Pydantic validation error before it could reach L2 verification. The AI's response was structurally correct — the only problem was `"pool_type": "PDH"` (uppercase) vs the expected `"pdh"` (lowercase). After the fix, subsequent CANDIDATEs parsed cleanly and reached L2 verification (where they were correctly rejected on other grounds).

---

## Bug 1: Pool_type Case Sensitivity (CRITICAL — killed a CANDIDATE)

### How it was found

During active monitoring, the USDJPY 00:15 and 00:30 candles returned `no_trade_reason: "ai_output_malformed"` in the evaluation log at `knowledge_base/live_evaluations/USDJPY/2026-04-13.jsonl`. The system was treating a valid AI response as unparseable.

At the time of discovery, we had no way to see what the AI actually returned (see Bug 2 below). We added diagnostic logging first, then triggered the bug analysis from the captured data.

### Root cause

The AI (Sonnet 4.6 with effort=max) returned `"pool_type": "PDH"` in the `liquidity_sweep` object. The Pydantic model `LiquiditySweepAnalysis` defines `pool_type` as a `Literal` type with **lowercase-only** values: `"pdh"`, `"pdl"`, `"asian_high"`, etc. The existing `_normalize_pa_fields()` function had a `_POOL_MAP` dictionary for variant normalization, but it only handled a few specific aliases (`"equal_high"` -> `"equal_highs"`) and did **no case normalization at all**.

**File:** `src/components/primary_analyzer.py`, function `_normalize_pa_fields()` (line ~440)

**Old code:**
```python
_POOL_MAP = {
    "equal_high": "equal_highs", "equal_low": "equal_lows",
    "session_high": "session_high", "session_low": "session_low",
}
sweep = r.get("liquidity_sweep", {})
if sweep:
    pt = sweep.get("pool_type", "")
    if pt in _POOL_MAP:
        sweep["pool_type"] = _POOL_MAP[pt]
```

This would catch `"equal_high"` but not `"PDH"`, `"Pdh"`, `"Asian_High"`, or any other case variant.

### Fix applied

Replaced with case-insensitive normalization that:
1. Lowercases and strips the incoming value
2. Checks against a complete set of valid pool types (`_VALID_POOLS`)
3. Maps common AI output variants to canonical values (`_POOL_MAP` — expanded from 4 to 12 entries)
4. Falls back to `"none"` for truly unknown values rather than crashing

```python
_VALID_POOLS = {
    "asian_high", "asian_low", "pdh", "pdl",
    "equal_highs", "equal_lows",
    "session_high", "session_low",
    "london_high", "london_low",
    "none",
}
_POOL_MAP = {
    "equal_high": "equal_highs", "equal_low": "equal_lows",
    "session_high": "session_high", "session_low": "session_low",
    "pdh run": "pdh", "pdl run": "pdl",
    "previous day high": "pdh", "previous day low": "pdl",
    "prev day high": "pdh", "prev day low": "pdl",
    "asian high": "asian_high", "asian low": "asian_low",
    "london high": "london_high", "london low": "london_low",
}
sweep = r.get("liquidity_sweep", {})
if sweep:
    pt = sweep.get("pool_type", "")
    pt_lower = pt.lower().strip()
    if pt_lower in _VALID_POOLS:
        sweep["pool_type"] = pt_lower
    elif pt_lower in _POOL_MAP:
        sweep["pool_type"] = _POOL_MAP[pt_lower]
    elif pt and pt_lower not in _VALID_POOLS:
        sweep["pool_type"] = "none"
```

### Validation

- **Immediate:** Processes restarted at ~00:40 UTC. The 00:45 candle (USDJPY) parsed cleanly — NO_TRADE with conf=72, reason "OB Retest condition unmet". No malformed error.
- **Extended:** 9 subsequent USDJPY candles (00:45 through 02:45) all parsed without error. 5 of those returned CANDIDATE A+ — all parsed correctly and reached L2 verification. Zero new entries in `shadow_logs/malformed_responses.jsonl` after the fix.
- **Regression scope:** The change only affects the normalization layer — it maps AI output to valid enum values before Pydantic validation. No trade logic, scoring, or execution paths are altered. Existing valid lowercase values pass through unchanged (`pt_lower in _VALID_POOLS` is the first check).

### Risk assessment

**Low risk.** The fix is purely additive normalization in a pre-validation layer. The fallback to `"none"` for unknown values prevents future crashes from novel AI output variants. The worst case is a genuinely unknown pool_type being silently mapped to `"none"` — but `"none"` is already a valid value the system handles, and the alternative (crashing) is strictly worse.

### Broader implication

Every `Literal` type in the Pydantic models is a potential case-sensitivity landmine when the AI generates the values. The `_normalize_pa_fields()` function already handles several fields (`poi_type`, `choch_type`, `sweep_type`). A future audit should verify that **all** Literal-typed fields have case-insensitive normalization. This is not urgent — `pool_type` was the only one that surfaced in production — but it's a known class of risk.

---

## Bug 2: Malformed Response Logging Gap (HIGH — lost diagnostic data)

### How it was found

When Bug 1 was discovered, we wanted to see what the AI actually returned. The system logged `no_trade_reason: "ai_output_malformed"` but the raw AI response was **discarded**. The retry block caught the exception, attempted a format-correction retry, and when that also failed, returned a NO_TRADE result — but neither the original nor retry response was preserved anywhere.

This meant the 00:15 candle's raw response was lost forever. We could only diagnose Bug 1 because we added this logging before the 00:30 candle, which exhibited the same bug and was captured.

### Root cause

The retry block in `PrimaryAnalyzer.evaluate()` (line ~276) caught exceptions generically and did not preserve the raw text:

```python
except Exception:
    logger.info("Malformed response -- retrying with format correction")
    # ... retry ...
    except Exception:
        result = _make_no_trade("ai_output_malformed", self.model)
```

No diagnostic data was saved — not the raw response, not the error message, not the attempt number.

### Fix applied

Added `_log_malformed_response()` function that writes to `shadow_logs/malformed_responses.jsonl`:

```python
_MALFORMED_LOG = Path("shadow_logs/malformed_responses.jsonl")

def _log_malformed_response(raw_text: str, error_msg: str, attempt: int = 1) -> None:
    """Save raw AI response when parsing fails -- diagnostic only."""
    try:
        _MALFORMED_LOG.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "attempt": attempt,
            "error": error_msg,
            "raw_response_length": len(raw_text),
            "raw_response": raw_text[:2000],
        }
        with open(_MALFORMED_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass  # Never let diagnostic logging crash the pipeline
```

Called at both exception points (first parse attempt and retry attempt). The function is wrapped in a bare `except` to ensure diagnostic logging can never crash the trading pipeline.

### Validation

- The 00:30 candle's malformed response was captured (2 entries — attempt 1 and attempt 2).
- Both entries correctly show `pool_type` Pydantic validation as the error.
- The `raw_response` field captured the AI's full JSON output, confirming `"PDH"` as the root cause.
- After Bug 1 was fixed, no new entries appeared (9 subsequent candles).

### Risk assessment

**Zero risk.** This is observation-only shadow logging in a try/except block. It cannot affect trade decisions or system behavior. The `raw_response[:2000]` truncation prevents unbounded file growth from pathological responses.

---

## Bug 3: monitor.sh Process Counting (MEDIUM — false alarm display)

### How it was found

The CEO ran `bash monitor.sh` and it displayed `Processes: 0/5 ALL DOWN` despite all 5 processes being alive and actively trading.

### Root cause

The original process counting used:
```bash
local count=$(ps aux | grep python | grep -v grep | wc -l | tr -d ' ')
```

This only works in Unix-native environments. On Windows with Git Bash, `ps aux` only sees processes that are children of the current bash session. Trading processes launched via PowerShell (`System.Diagnostics.Process.Start()`) or `wmic` are Windows-native detached processes — invisible to bash's `ps`.

### Fix applied

Replaced with PID lock file verification against Windows `tasklist.exe`:
```bash
local count=0
local proclist
proclist=$(MSYS_NO_PATHCONV=1 /c/Windows/System32/tasklist.exe 2>/dev/null)
for lf in knowledge_base/meta/.orchestrator_*.lock; do
    [ -f "$lf" ] || continue
    local lpid=$(grep -ao '"pid": [0-9]*' "$lf" | grep -o '[0-9]*')
    if [ -n "$lpid" ] && echo "$proclist" | grep -q " ${lpid} "; then
        count=$((count + 1))
    fi
done
```

The same pattern was applied to the `kill_all()` function's remaining-process count.

### Validation

- After the fix, `monitor.sh` correctly shows `Processes: 5/5 OK`.
- The `MSYS_NO_PATHCONV=1` prefix prevents Git Bash from mangling the Windows path.
- The lock file approach is consistent with the watchdog's process detection method.

---

## Bug 4: monitor.sh Binary File Grep (LOW — display errors)

### How it was found

Several monitor views (instrument details, error scanning) showed no output or "Binary file matches" warnings instead of actual log content.

### Root cause

Log files contain UTF-8 characters — specifically the arrow character (used in log messages like `"Processing candle -> tokyo KZ"`). Without the `-a` flag, GNU `grep` detects non-ASCII bytes and treats the file as binary, suppressing normal output.

### Fix applied

Added `-a` (treat binary as text) flag to **all 12 grep calls** on log files throughout `monitor.sh`:
- `grep -a "INFO"` (dashboard status, 2 occurrences)
- `grep -a "ERROR"` (dashboard error check, error views)
- `grep -a "Align score"` (align score view)
- `grep -ai "CANDIDATE|..."` (candidates/trades views, 2 occurrences)
- `grep -a "ERROR|CRITICAL"` (all-errors view)
- `grep -ao` (lock file PID extraction, 2 occurrences)

### Validation

All monitor views now display correctly with full log content including Unicode characters.

---

## Bug 5: Watchdog Visible Windows (LOW — user experience)

### How it was found

When the watchdog first ran and started all 5 processes, 5 blank black terminal windows appeared on the desktop. The CEO asked whether to close them (closing would kill the trading processes).

### Root cause

The original watchdog used `wmic process call create "cmd /c ..."` to launch processes. On Windows, `wmic` spawns a visible `cmd.exe` window for the child process.

### Fix applied

Replaced with `System.Diagnostics.Process.Start()` using hidden window settings:
```powershell
$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = "cmd.exe"
$psi.Arguments = "/c cd /d ${ProjectDir} && ${PythonExe} run_agent.py --symbol ${symbol} --mode demo >> ""${logFile}"" 2>&1"
$psi.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden
$psi.CreateNoWindow = $true
$proc = [System.Diagnostics.Process]::Start($psi)
```

### Validation

- Killed all 5 old processes (visible windows), restarted via updated watchdog.
- All 5 processes started with no visible windows.
- Confirmed alive via lock files and `tasklist.exe`.
- Processes have been stable for 6+ hours since the fix (same PIDs in every watchdog check from 08:46 onward).

---

## Session Statistics

| Metric | Value |
|--------|-------|
| Total candles monitored | 22 (11 USDJPY + 11 GBPJPY) |
| USDJPY CANDIDATEs | 5 (all A+, all correctly L2-rejected) |
| USDJPY NO_TRADEs | 4 (clean) |
| USDJPY malformed | 2 (pre-fix, both pool_type) |
| GBPJPY NO_TRADEs | 11/11 (all C1 fail — H1 bullish vs required SHORT) |
| Malformed responses after fix | 0 (9 consecutive clean candles) |
| Process errors after fix | 0 across all 5 instruments |
| Watchdog health checks (post-stabilization) | 19/19 all 5/5 healthy |

## Files Changed (uncommitted)

| File | Type | Lines changed |
|------|------|---------------|
| `src/components/primary_analyzer.py` | Bug fix + diagnostic logging | +39 lines |
| `monitor.sh` | Bug fixes (process counting + grep) | +13/-8 lines |
| `scripts/watchdog.ps1` | New infrastructure | 125 lines |
| `scripts/watchdog.bat` | New infrastructure | 5 lines |

## Recommendations for Strategic Review

1. **Commit these changes** — All fixes are validated and production-proven. The primary_analyzer.py changes are within WF-1 allowances (bug fix + safety logging, no trading logic changes).

2. **Audit all Literal-typed Pydantic fields** — Bug 1 is a class of vulnerability, not a one-off. Any field where the AI generates a value that must match a `Literal` set is at risk of case mismatch. Low urgency (only pool_type surfaced) but worth a systematic check.

3. **The killed CANDIDATE at 00:30 UTC** — This was USDJPY, grade A+, conf=82. It would have reached L2 verification where it likely would have been rejected (price was ~33 pips from the OB zone at that time). The fix ensures no future CANDIDATEs are lost to formatting issues.

4. **Watchdog is now autonomous** — Runs every 15 minutes via Task Scheduler + on login via Startup folder. No manual intervention needed for process recovery.

---

*Report generated April 13, 2026. All fixes deployed and validated during live Tokyo KZ session.*
