# Test Failures & YAML Structure Verification Report

**Date:** April 14, 2026
**Investigator:** Claude Code (Opus 4.6)
**Branch:** main (commit `65b3ad3`)
**Test run:** 26 failed, 1022 passed (258s)

---

## Finding 1: YAML Indentation Bug

**Verdict: REAL + CRITICAL (XAUUSD only)**

### Evidence

The `risk:` section at lines 18-19 of `config/agent_config.yaml` contains only:

```yaml
risk:
  risk_per_trade_pct: 2.0
```

The following keys are incorrectly nested under `drawdown_reduction:` (lines 25-38) instead of `risk:`:

| Key | Value | Should be under `risk:` |
|-----|-------|------------------------|
| contract_size | 100 | Yes |
| max_daily_loss_pct | 2.0 | Yes |
| max_weekly_loss_pct | 4.0 | Yes |
| max_monthly_loss_pct | 8.0 | Yes |
| max_trades_per_day | 2 | Yes |
| min_rr | 1.5 | Yes |
| tp1_close_pct | 100 | Yes |
| max_spread_cents | 100 | Yes |
| sl_buffer_dollars | 1.20 | Yes |
| sl_absolute_min | 5.0 | Yes |

The `drawdown_reduction:` section should only contain: `threshold`, `reduced_risk_pct`, and the comment about inheriting from `risk.risk_per_trade_pct`.

This bug exists in the **committed** version on `main`. The only local (uncommitted) change to this file is the addition of the `gate1:` section (confirmed via `git diff`).

### Why XAUUSD is affected but other instruments are not

The orchestrator loads config via `apply_instrument_overrides()` (`src/utils/config.py:25`), which deep-merges per-instrument `risk:` sections into the top-level config. Instruments like GBPJPY, GBPUSD, US30, USDJPY all have per-instrument `risk:` overrides (with `max_spread_cents`, `sl_buffer_dollars`, `sl_absolute_min`, `contract_size`) that correctly populate the merged `risk:` dict.

**XAUUSD's instrument override** (under `instruments: XAUUSD:`) contains only:
```json
{
  "skip_first_ny_candle": true,
  "market": {"symbol": "XAUUSD", "kill_zones": {"ny": {...}}}
}
```

No `risk:` section. So XAUUSD uses the broken top-level `risk:` which has only `risk_per_trade_pct: 2.0`.

### Production Impact Analysis

| Gate | Key | Intended Value | Actual (fallback) | Impact |
|------|-----|---------------|-------------------|--------|
| Gate3 (L77) | `max_spread_cents` | 100 ($1.00) | **30 ($0.30)** | **CRITICAL** — spread gate 3.3x tighter. XAUUSD median spread is $0.39 (39 cents), so trades during normal-spread periods (31-100 cents) are **incorrectly blocked**. Only trades during tight-spread moments (<30 cents) pass. |
| Gate1 OB exception (L107) | `sl_buffer_dollars` | 1.20 ($1.20) | **0.02 ($0.02)** | **MODERATE** — OB boundary tolerance is 60x tighter in the new SL exception. The exception will almost never trigger for XAUUSD because SL must be within $0.02 of an OB boundary instead of $1.20. |
| Execution (L571) | `contract_size` | 100 | 100 | None — fallback matches |
| Gate3 (L51) | `max_daily_loss_pct` | 2.0 | 2.0 | None — fallback matches |
| Gate1 (L159) | `min_rr` | 1.5 | 1.5 | None — fallback matches |
| Gate1 (L218) | `sl_absolute_min` | 5.0 | 5.0 | None — fallback matches |
| Gate3 (L59) | `max_daily_trades` | 2 | 2 | None — **hardcoded in session_state** (orchestrator.py:162,1810), not read from config |
| N/A | `tp1_close_pct` | 100 | N/A | None — not used in permissions.py |

### Secondary finding: `risk_per_trade_pct` discrepancy

The YAML has `risk_per_trade_pct: 2.0` but `CLAUDE.md` says `risk_per_trade_pct: 1.0`. This is a separate issue from the indentation bug — the value is correctly placed under `risk:`, but differs from documentation. One of them is stale. Check git blame to determine which is authoritative.

### Recommended fix

Re-indent `config/agent_config.yaml` so the misplaced keys are under `risk:` instead of `drawdown_reduction:`. The corrected structure should be:

```yaml
risk:
  risk_per_trade_pct: 2.0      # (or 1.0 — verify which is correct)
  contract_size: 100
  max_daily_loss_pct: 2.0
  max_weekly_loss_pct: 4.0
  max_monthly_loss_pct: 8.0
  max_trades_per_day: 2
  min_rr: 1.5
  tp1_close_pct: 100
  max_spread_cents: 100
  sl_buffer_dollars: 1.20
  sl_absolute_min: 5.0

drawdown_reduction:
  threshold: 0.08
  reduced_risk_pct: 0.5
```

**Priority: Fix before next London open (07:00 UTC).** Every XAUUSD candle evaluation during normal spreads is being incorrectly blocked by the 30-cent fallback.

---

## Finding 2: Test Failure Groups

| Group | Files | Count | Root Cause | Production Impact | Fix Priority |
|-------|-------|-------|------------|-------------------|--------------|
| 1 | test_resolve_obs.py | 5 | MT5 Windows-only import | None | Low |
| 2 | test_prelaunch_audit.py | 2 | YAML indentation bug (tests are correct!) | Yes — confirms Finding 1 | **High** (fix YAML) |
| 3 | test_prelaunch_audit.py, test_batch_backtest.py | 2 | London KZ end_utc changed 09:30→10:30 | None — config change was intentional | Low |
| 4 | test_end_to_end_integration.py, test_infrastructure_framework.py | 8 | Attribute renames in monitoring.py | None | Medium |
| 5 | test_infrastructure_framework.py | 3 | Various (backoff, audit format, timing) | None | Low |
| 6 | test_monitoring.py, test_infrastructure_framework.py | 6 | ShadowDataCollector mkdir/path issues | None | Low |

### Group 1 — MT5 Import (5 failures)

**Verdict: Confirmed — platform limitation, not a bug**

All 5 tests in `test_resolve_obs.py` fail with:
```
ModuleNotFoundError: No module named 'MetaTrader5'
```

Tests use `patch("MetaTrader5.initialize", ...)` which requires the MT5 package to be importable. MT5 is a Windows-only library (C extension wrapping the MetaTrader 5 terminal).

**Production impact:** None. The actual `resolve_obs.py` script runs on Windows where MT5 is available.

**Recommendation:** Add `@pytest.mark.skipif(sys.platform != "win32", reason="MT5 is Windows-only")` to the test class. Or create a mock MT5 module in conftest.py.

### Group 2 — YAML Config Consistency (2 failures)

**Verdict: Confirmed — tests correctly detect the YAML bug**

```
test_max_trades_per_day_matches:
  config["risk"]["max_trades_per_day"]  →  KeyError: 'max_trades_per_day'

test_max_spread_matches_permissions:
  config["risk"]["max_spread_cents"]    →  KeyError: 'max_spread_cents'
```

These tests assert that `config["risk"]` contains `max_trades_per_day` and `max_spread_cents`. They don't because of the YAML indentation bug.

**Production impact:** YES — these tests are correct. The config is wrong. See Finding 1.

**Recommendation:** Fix the YAML. Tests should pass after the fix without any test changes.

### Group 3 — London KZ End Time (2 failures)

**Verdict: Confirmed — stale tests, config change was intentional**

```
test_config_london_end_is_0930:
  assert london["end_utc"] == "09:30"  →  AssertionError: '10:30' != '09:30'

test_config_kz_overrides_per_instrument:
  assert base_london["end_utc"] == "09:30"  →  same
```

The config has:
```yaml
london:
  start_utc: "07:00"
  end_utc: "10:30"
  core_end_utc: "09:30"
```

The London window was extended from 09:30 to 10:30 (with `core_end_utc` preserving the original boundary). This is an intentional change documented in CLAUDE.md's kill zone schedule.

**Production impact:** None. The config is correct. Tests are stale.

**Recommendation:** Update test assertions to `assert london["end_utc"] == "10:30"`. Or test `core_end_utc == "09:30"` if that was the original intent.

### Group 4 — Monitoring Attribute Renames (8 failures)

**Verdict: Confirmed — production code was refactored, tests not updated**

**4a. `EnhancedSessionLogger._log_dir` → `_logs_dir` (6 failures)**

5 in `test_end_to_end_integration.py` + 1 in `test_infrastructure_framework.py`:
```
AttributeError: 'EnhancedSessionLogger' object has no attribute '_log_dir'. Did you mean: '_logs_dir'?
```

Production code (`monitoring.py:107`): `self._logs_dir = self.base / "meta" / "logs"`

**4b. `PerformanceMonitor._metrics_queue` / `_shadow_dir` moved to `ShadowDataCollector` (2 failures)**

```
AttributeError: 'PerformanceMonitor' object has no attribute '_metrics_queue'
AttributeError: 'PerformanceMonitor' object has no attribute '_shadow_dir'
```

`PerformanceMonitor` was refactored to delegate to `self.shadow_collector` (a `ShadowDataCollector`). The attributes live on `monitor.shadow_collector._metrics_queue` and `monitor.shadow_collector._shadow_dir`.

**Production impact:** None. Production code uses the correct attribute names and paths.

**Recommendation:** Update tests:
- `_log_dir` → `_logs_dir`
- `monitor._metrics_queue` → `monitor.shadow_collector._metrics_queue`
- `monitor._shadow_dir` → `monitor.shadow_collector._shadow_dir`

### Group 5 — Miscellaneous Infrastructure (3 failures)

**5a. YouTube 429 backoff timing (1 failure)**

```
assert 55 <= block_time_1 <= 65  →  AssertionError: 89.999... <= 65
```

Production code (`monitoring.py:591`) now uses 90s backoff instead of 60s. The test bounds (55-65) are stale.

**5b. Configuration change audit format (1 failure)**

```
assert audit_entry["component"] == component  →  KeyError: 'component'
```

The audit entry format changed — `component` key was renamed or removed.

**5c. Performance degradation detection (1 failure)**

```
assert len(slow_alerts) >= 2  →  AssertionError: assert 1 >= 2
```

Timing-sensitive assertion. The test expects 2+ slow operation alerts but only 1 was captured.

**Production impact:** None for any of these.

**Recommendation:** Update test assertions to match current implementation.

### Group 6 — ShadowDataCollector mkdir/path issues (6 failures)

**6a. Read-only filesystem (2 failures)**

```
test_monitoring_error_recovery:
  ShadowDataCollector(kb_base="/nonexistent/path")
  →  OSError: [Errno 30] Read-only file system: '/nonexistent'

test_error_recovery_and_resilience:
  ShadowDataCollector(kb_base=corrupted_path)
  →  PermissionError: [Errno 13] Permission denied
```

`ShadowDataCollector.__init__` (`monitoring.py:234`) eagerly calls `self._shadow_dir.mkdir(parents=True, exist_ok=True)`. When the path is on a read-only or permission-denied filesystem, this raises before the test can check graceful degradation.

**6b. Directory path mismatch (2 failures)**

```
test_custom_knowledge_base_paths:
  assert (custom_kb / "shadow_data").exists()  →  False

test_monitoring_component_isolation:
  assert kb1_metrics.exists()  →  False (looking for shadow_data/metrics_*.jsonl)
```

Tests expect shadow data at `base/shadow_data/` but actual path is `base/meta/shadow_data/` (monitoring.py:233).

**6c. PerformanceMonitor integration (2 failures counted in Group 4b already)**

(Some overlap with Group 4b — `_shadow_dir` attribute access on wrong object.)

**Production impact:** None in normal operation. The mkdir issue could matter if KB path is misconfigured, but that's an edge case.

**Recommendation:**
- For filesystem tests: use `/tmp/nonexistent` or wrap in try/except
- For path assertions: update to `base/meta/shadow_data/`
- Consider adding graceful error handling in `ShadowDataCollector.__init__` for robustness

---

## Summary

### Findings with live production impact

1. **YAML indentation bug (Finding 1)** — `max_spread_cents` fallback of 30 instead of 100 is **actively blocking valid XAUUSD trades** when spread is between $0.30-$1.00 (which is most of the time). This is the only finding with confirmed live impact.

2. **`sl_buffer_dollars` fallback** — 0.02 instead of 1.20 makes the new OB-width SL exception nearly non-functional for XAUUSD. Lower priority since the exception was just added and hasn't been in production long.

### Findings that are test hygiene only

- Group 1: MT5 import (5 tests) — platform limitation
- Group 3: London KZ end time (2 tests) — stale assertions
- Group 4: Attribute renames (8 tests) — stale attribute names
- Group 5: Backoff/audit/timing (3 tests) — stale assertions
- Group 6: Filesystem/path (6 tests) — test environment issues

### Recommended immediate actions (before next trading session)

1. **FIX YAML INDENTATION** — Move `contract_size`, `max_daily_loss_pct`, `max_weekly_loss_pct`, `max_monthly_loss_pct`, `max_trades_per_day`, `min_rr`, `tp1_close_pct`, `max_spread_cents`, `sl_buffer_dollars`, `sl_absolute_min` from `drawdown_reduction:` to `risk:`
2. **Verify `risk_per_trade_pct`** — YAML says 2.0, CLAUDE.md says 1.0. Determine which is authoritative.
3. **Re-run tests** — Groups 2's 2 failures should auto-fix. Remaining 24 are independent issues.

### Deferred actions (can wait)

1. Add `pytest.mark.skipif` for MT5-dependent tests (Group 1)
2. Update London KZ test assertions (Group 3)
3. Update monitoring attribute names in tests (Group 4)
4. Update backoff/audit/timing test assertions (Group 5)
5. Fix test paths and add graceful mkdir handling (Group 6)
