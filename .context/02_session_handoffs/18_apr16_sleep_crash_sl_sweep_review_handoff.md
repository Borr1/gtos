# Session 18 Handoff — Sleep Crash Fix, SL Sweep Margin, Full Apr 16 Review

**Date:** April 16-17, 2026
**Session type:** Live bug investigation + fixes + full day review
**Branch:** main
**Commits this session:**
- `acf530f` — fix: sleep race condition crash + SL sweep margin for OB exception
- `91f27b6` — chore: commit Apr 16 runtime data — evaluations, sessions, trade records
- `997c96d` — chore: commit Apr 16 logs, shadow data, and pipeline state

---

## EXECUTIVE SUMMARY

Two bugs fixed, one confirmed -1R loss caused by the first bug's cascading effects. Full day review of all 5 instruments completed — no other missed trades or system errors beyond the two fixed bugs.

**Bug 1 — Sleep TOCTOU race condition:** `_interruptible_sleep()` crashed with `ValueError: sleep length must be non-negative` when `end_time - time.time()` went negative between the while-loop check and the `time.sleep()` call. Hit XAUUSD at 17:33 local and USDJPY at 17:23 local on Apr 16. The XAUUSD crash destroyed a London limit order with a wide SL (0.74 ATR below OB) and forced a tighter NY replacement (0.12 ATR) that got swept as liquidity.

**Bug 2 — OB retest SL exception too permissive:** The `_ob_retest_sl_exception_applies()` function bypassed the sl_too_tight gate for any SL below the OB boundary, regardless of how close. This allowed stops clustered at the obvious OB edge — the primary target for liquidity sweeps. Added ATR-scaled minimum buffer (0.3 * M15_ATR).

**Net impact:** The Apr 16 XAUUSD -1R loss was directly caused by Bug 1 (crash destroyed London limit) compounded by Bug 2 (tight NY replacement was allowed through). Both are now fixed.

---

## WHAT HAPPENED — APRIL 16 FULL DAY

### Trade Activity

| Instrument | CANDIDATEs | Limits Placed | Filled | Outcome | Notes |
|------------|-----------|---------------|--------|---------|-------|
| XAUUSD | 3 | 2 (London + NY) | 1 (NY) | **-1R** | Sleep crash lost London limit; NY replacement swept |
| GBPJPY | 1 | 1 (Tokyo) | 0 | Unfilled | Price never reached 214.129 entry |
| US30 | 1 | 1 (NY) | 0 | Aborted | sl_too_close gate correctly blocked (0.69 pts < 27.0 min) |
| USDJPY | 5 | 0 | 0 | L2-blocked | All 10 H1 OBs genuinely mitigated in ranging market |
| GBPUSD | 0 | 0 | 0 | — | Zero setups; calendar block (US Building Permits) |

**Net P&L: -1R**

### XAUUSD — The Core Story (Cascading Bug Impact)

1. London 08:00: CANDIDATE, limit at 4788.62, SL=4782.44 (0.74 ATR below OB)
2. **17:33 local: Sleep crash** — `ValueError: sleep length must be non-negative` in `_interruptible_sleep()`
3. London limit destroyed (pending_intent is in-memory only)
4. NY 13:16: New CANDIDATE, limit at 4789.38, SL=4788.08 (0.12 ATR below OB — too tight but OB exception allowed it)
5. NY 22:06: Filled, then price swept to 4785.05 — SL hit at 4788.08
6. **The London limit's SL (4782.44) would have survived the sweep by 2.61 pts**
7. Root cause chain: Sleep bug → crash → lost limit → tight replacement → swept

### USDJPY — 5 L2 Blocks Were Correct

All 5 London CANDIDATEs blocked by `h1_poi_not_found` in L2 verification. Investigation confirmed all 10 H1 OBs were genuinely mitigated (158.69-159.32 range, repeated touches). The AI hallucinated unmitigated zones; verification correctly rejected.

### US30 — Safety Gate Worked

NY CANDIDATE at 48473.61. On fill attempt, price at 48452.50 with SL at 48451.81 — only 0.69 pts remaining vs 27.0 minimum. `sl_too_close` gate correctly aborted. Price had crashed through both entry and SL — would have been instant loss.

### Calendar Block

US Building Permits event blocked evaluations on XAUUSD, US30, and GBPUSD from ~10:30 UTC through London close (~2 hours across 3 instruments). Filter working as designed.

---

## BUGS FIXED

### Bug 1: Sleep TOCTOU Race Condition

**File:** `src/components/orchestrator.py` (lines 2135-2148)
**Commit:** `acf530f`

**Root cause:** In `_interruptible_sleep()`, the `while time.time() < end_time` check passes, then `time.sleep(min(1.0, end_time - time.time()))` executes — but between these two operations, `time.time()` advances past `end_time`, producing a negative sleep value.

**Fix:**
```python
def _interruptible_sleep(self, seconds: float):
    if seconds <= 0:          # Guard non-positive input
        return
    end_time = time.time() + seconds
    while time.time() < end_time and self.running:
        remaining = end_time - time.time()
        if remaining <= 0:    # Guard TOCTOU gap
            break
        time.sleep(min(1.0, remaining))
```

Same pattern applied to `_monitored_sleep()`.

### Bug 2: OB Retest SL Sweep Margin

**File:** `src/components/permissions.py` (lines 86-156)
**Config:** `config/agent_config.yaml` — `gate1.ob_retest_sl_min_buffer_atr: 0.3`
**Tests:** `tests/test_permissions.py` — 2 existing tests updated, 2 new tests added (29/29 pass)
**Commit:** `acf530f`

**Root cause:** `_ob_retest_sl_exception_applies()` only checked that SL was beyond the OB boundary — no minimum distance. Stops at 0.01 below the OB edge passed the same as stops 5.00 below.

**Fix:** Added condition 5 — SL must have at least `0.3 * M15_ATR` buffer beyond the OB boundary. This clears the typical retail stop-hunt sweep zone. Evidence from Apr 16: NY SL at 0.12 ATR got swept, London SL at 0.74 ATR would have survived (sweep was 0.36 ATR deep).

---

## WHAT IS NOT BROKEN (Reviewed, Confirmed Working)

- **Gate1 R:R check:** Config `min_rr: 1.5`, gate accepts 1.3R-2.0R band. TP1 at 1.50R is the target, not a warning.
- **Displacement ratio verification:** MSO's deterministic ratio is used for pass/fail (verification.py:191). AI's self-reported ratio is logged for comparison only — mismatch warnings are diagnostic, don't affect decisions.
- **L2 verification:** Correctly blocking hallucinated OB zones across all instruments.
- **Calendar filter:** Correctly blocking during news events.
- **sl_too_close safety gate:** Correctly prevented US30 fill that would have been instant loss.

---

## OPEN ITEMS FOR CEO INVESTIGATION

The following 5 items were flagged during review. Session 18 assessment is that items 3-5 are noise, but **the CEO wants to verify independently, especially items 1 and 2:**

1. **R:R rejection at 2R vs 1.5R target** — CEO reports seeing trades rejected because "projected RR is 1.5 and it got rejected because it wasn't 2R." Current config is `min_rr: 1.5` with gate accepting >= 1.3R. If real, there may be a stale 2R check somewhere (prompt? evaluation? old config on a running process?). Needs investigation.

2. **Displacement ratio — AI vs MSO mismatch impact** — MSO ratio is used for pass/fail decisions, AI's ratio is logged only. But if the AI is consistently misreporting displacement, it could indicate the AI is evaluating the wrong candle or misunderstanding the structure. Needs deeper audit of whether this matters for setup quality.

3. **TP1 placement warnings** — "TP1 at 1.50R" appears on every trade. This is the system hitting its target, not a warning. Informational noise.

4. **Calendar block coverage** — Working as designed. Not an issue.

5. **Pending intent not persisted** — Known architectural limitation (in-memory only, lost on crash/restart). Documented since handoff 17. The sleep crash fix reduces the crash risk, but restarts still lose limits.

---

## PROCESS STATE AFTER FIXES

- All 5 instrument processes restarted at ~22:42 local (Apr 16) with fixes deployed
- No new sleep crashes observed post-fix
- All processes running cleanly through Apr 17 sessions
- 29/29 permission tests pass
- 3 pre-existing test failures unrelated to changes (test_orchestrator mock issue, test_integration_live BE assertion, test_infrastructure_framework timeout)

---

## COMMITS TO VERIFY

```
acf530f fix: sleep race condition crash + SL sweep margin for OB exception
91f27b6 chore: commit Apr 16 runtime data — evaluations, sessions, trade records
997c96d chore: commit Apr 16 logs, shadow data, and pipeline state
```

---

*Next session: CEO to verify R:R rejection issue and displacement ratio impact using provided investigation prompt.*
