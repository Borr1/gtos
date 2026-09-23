# Bug Fix Validation Report
**Date:** 2026-04-02 (file timestamp UTC: 2026-04-01 18:22)
**Fixes:** TP1 placement, outcome simulation labeling, null trade_parameters guard, file versioning

---

## Bug 1: TP1 Placement — ROOT CAUSE + FIX

### Root Cause
The PA prompt (OB7) instructed the AI: *"TP1 above/below the OB origin (the high/low that was broken)"*. This caused the AI to set TP1 at the nearest structural level instead of at the minimum 2.5R distance required by U5.

**Impact:** 70% of the 111 batch trades (77/110) had TP1 below 2.0R from entry. Median TP1 was at 0.63R. This meant partial closes at TP1 captured tiny profits (0.1-0.5R) instead of the intended 2.5R.

The safety check (Gate 1) only validated the AI's self-reported `risk_reward_ratio` field, not the actual TP1/SL distance. The AI could report R:R=2.5 (based on TP2 or TP3) while TP1 sat at 0.17R.

### Fix Applied
1. **Prompt fix** (`src/prompts/primary_analyzer_prompt.py`):
   - OB7: Added "TP1 MUST be at minimum 2.5× SL distance from entry"
   - BR7: Same explicit TP1 distance requirement added

2. **Safety check** (`src/components/permissions.py`):
   - Added actual TP1 distance validation: `tp1_r = tp1_distance / sl_distance`
   - Rejects if TP1 < 2.0R from entry
   - Rejects if TP1 is on wrong side of entry (LONG with TP1 <= entry)

3. **Post-parse warning** (`src/components/primary_analyzer.py`):
   - `_warn_tp1_placement()` logs warning if TP1 < 2.0R
   - Logs error if TP1 on wrong side of entry

### Effect on Replay Trades
Of the 7 replay trades, the new safety check would reject 6:

| Trade | TP1/SL Ratio | New Verdict |
|-------|-------------|-------------|
| #1 (2025-02-13) | 2.49R | PASS |
| #2 (2025-02-21) | 0.59R | REJECTED — tp1_too_close |
| #3 (2025-02-25) | 0.50R | REJECTED — tp1_too_close |
| #4 (2025-03-18) | 0.17R | REJECTED — tp1_too_close |
| #5 (2025-03-21) | -0.02R | REJECTED — tp1_below_entry |
| #6 (2025-03-21) | 0.55R | REJECTED — tp1_too_close |
| #7 (2025-03-24) | 0.16R | REJECTED — tp1_too_close |

Only Trade #1 would have passed. The prompt fix should cause the AI to set TP1 correctly going forward, so future trades won't be rejected — they'll have proper TP1 placement.

---

## Bug 2: Outcome Simulation — NOT A CODE BUG

### Finding
The outcome simulation (`evaluate_hypothetical_outcome`) was **already correct**:
- SL detection uses candle LOW for LONG (line 192): `c_low <= current_sl`
- TP1 detection uses candle HIGH for LONG (line 232): `c_high >= tp1`
- SL is checked before TP on same candle (conservative)
- Partial close logic: 50% at TP1, SL to breakeven, 25% at TP2, runner at TP3

### Trade #4 Verification
Reproduced with actual candle data:
- TP1 WAS detected at 14:00:00 (candle high = $3031.17 >= TP1 $3030.00)
- 50% closed at TP1 (+0.085R), remainder timed out at $3033.76 (+0.125R)
- Total: +0.21R — matches exactly

### Fix Applied
Improved exit_substate labeling only:
- Before: All timeouts labeled `CLOSED_SESSION_TIMEOUT` even if partial TPs hit
- After: `CLOSED_TP1_THEN_TIMEOUT` when TP1 was hit before timeout

This is a reporting improvement, not a simulation fix.

---

## Bug 3: Null Trade Parameters — FIX

### Root Cause
The AI occasionally returns `decision: "CANDIDATE"` with malformed or missing `trade_parameters`. Pydantic validates the outer structure but `trade_parameters` is `Optional[TradeParameters]`, so `None` passes validation.

When `trade_parameters` is None, downstream code (session memory `_compress`, permissions checks) crashes with `AttributeError: 'NoneType' object has no attribute 'direction'`.

### Fix Applied
1. **Guard function** (`guard_candidate_null_params` in `primary_analyzer.py`):
   - If CANDIDATE with null params → demote to NO_TRADE
   - Sets `no_trade_reason = "null_trade_parameters"`
   - Appends `[SYSTEM: Demoted]` to reasoning

2. **Integrated into `analyze()` method** — called after parse/validate

3. **SessionMemory._compress()** — added null check before accessing `tp.direction`

---

## Bug 0: File Versioning — NEW

### Implementation
- `src/utils/file_versioning.py` — `get_versioned_path(base_dir, name, ext)` utility
- Format: `{name}_{YYYYMMDD_HHMM}{ext}`, collision-safe with `_2`, `_3` suffixes
- Applied to replay_session.py report output
- `knowledge_base_backtest/analysis/INDEX.md` created with all existing files
- 17 existing bare-named files retroactively renamed with creation dates

---

## Test Results

**20 new tests, all passing:**
- 4 file versioning tests
- 5 TP1 safety check tests (correct passes, too-close rejected, below-entry rejected, above-entry rejected, boundary 2.0R)
- 8 outcome simulation tests (SL detection, TP1 detection, labeling, SL priority, short trades, partial close math, Trade #4 reproduction)
- 3 null params guard tests

**429/430 full suite passing** (1 pre-existing failure in test_market_state unrelated to changes)

---

## Files Modified

| File | Changes |
|------|---------|
| `src/utils/file_versioning.py` | NEW — versioning utility |
| `src/prompts/primary_analyzer_prompt.py` | OB7 + BR7: explicit TP1 >= 2.5× SL distance |
| `src/components/permissions.py` | Gate 1: actual TP1 distance validation |
| `src/components/primary_analyzer.py` | `_warn_tp1_placement()`, `guard_candidate_null_params()` |
| `scripts/replay_session.py` | Versioned report output, null-safe SessionMemory._compress |
| `scripts/backtest_runner.py` | `CLOSED_TP1_THEN_TIMEOUT` exit_substate label |
| `tests/test_bugfixes_0.py` | NEW — 20 tests |
| `knowledge_base_backtest/analysis/INDEX.md` | NEW — analysis index |

---

## Re-Run Decision

A full re-run of the 66 replay dates is **not necessary at this time** because:

1. The TP1 **prompt fix** changes AI output (new TP1 placements). Any re-run would test the FIXED prompt, not validate the bug fix on the old results.
2. The outcome simulation was already correct — no code change to validate.
3. The null params guard is tested with unit tests.

**What IS needed:** A fresh batch or replay run with the fixed prompt to measure the actual system performance with correct TP1 placement. This should be a new validation run, not a re-run of the same dates.

---

## Impact Assessment

The TP1 bug was the primary driver of the -0.48R expectancy in the replay blitz:
- Average win was +0.20R because TP1 was at 0.17-0.59R, capturing tiny partial profits
- With correct 2.5R TP1 placement, a TP1 hit would yield 50% × 2.5R = +1.25R partial close
- Even with a lower hit rate on the higher TP1, the R:R improvement is dramatic

The 101-trade batch's +0.22R expectancy was also depressed by this same bug (70% of trades affected). True system performance with correct TP1 placement is unknown and requires a fresh run.
