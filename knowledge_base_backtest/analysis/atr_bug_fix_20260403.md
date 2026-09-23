# ATR Zero Bug — Diagnostic & Fix Report
**Date:** 2026-04-03
**Severity:** Critical (affected GBPUSD SL validation + prompt accuracy)

---

## 1. Root Cause

**File:** `src/components/market_state.py`, line 629

```python
# BEFORE (broken)
atr_14=round(atr, 2),

# AFTER (fixed)
atr_14=atr,
```

`round(atr, 2)` rounds to 2 decimal places. For GBPUSD:
- H1 ATR = 0.00298 -> rounds to **0.00** (zero!)
- M15 ATR = 0.00129 -> rounds to **0.00** (zero!)
- D1 ATR = 0.01136 -> rounds to **0.01** (loses 88% precision)
- H4 ATR = 0.00546 -> rounds to **0.01** (makes D1 and H4 appear identical)

For XAUUSD, ATR values are in dollars (e.g., M15 ATR = 3.40), so `round(x, 2)` preserves them correctly. The bug was forex-specific.

## 2. Impact Assessment

### Display Impact (prompt text)
The original GBPUSD sample prompt showed:
```
H1: Avg body: 0.00195  ATR(14): 0.00000    <- ZERO
M15: Avg body: 0.00108  ATR(14): 0.00000   <- ZERO
D1: Avg body: 0.00526  ATR(14): 0.01000    <- Imprecise
H4: Avg body: 0.00221  ATR(14): 0.01000    <- Same as D1 (wrong)
```

The LLM evaluating the prompt would see zero ATR for H1 and M15, making it impossible to correctly assess SL adequacy relative to ATR (rule U6).

### Validation Impact (SL checks)
Both `permissions.py` (live orchestrator) and `batch_backtest.py` (batch scoring) contain:
```python
m15_atr = getattr(m15_tf, "atr_14", 0) or 0
if m15_atr > 0 and sl_distance < m15_atr * 1.5:
    # reject SL as too tight
```

With `atr_14 = 0.00`, the condition `m15_atr > 0` was **always false** for GBPUSD, meaning the 1.5x ATR SL floor check was **silently skipped** for all forex instruments. Trades with dangerously tight SLs could pass validation unchallenged.

### Gold Impact
None. Gold ATR values (e.g., M15 = 3.40) round safely to 2 decimals.

## 3. Correct ATR Values (manual verification)

Computed independently using Wilder's smoothing (14-period) on GBPUSD candles up to 2025-01-21:

| Timeframe | Correct ATR | Old (rounded) | Error |
|-----------|------------|---------------|-------|
| D1 | 0.01136 | 0.01 | -12% precision loss |
| H4 | 0.00546 | 0.01 | +83% inflation |
| H1 | 0.00298 | 0.00 | -100% (zero!) |
| M15 | 0.00129 | 0.00 | -100% (zero!) |

Manual computation matched `calculate_atr()` output to 9 decimal places for all timeframes.

## 4. Fix Applied

### Primary fix: `src/components/market_state.py`
Removed `round(atr, 2)` — ATR is now stored at full `float` precision. The prompt formatter (`primary_analyzer_prompt.py`) already uses `_PRICE_FMT` (`.5f` for GBPUSD, `.2f` for gold) to control display precision, so no display changes were needed.

### Secondary fix: format strings in denial messages
- `src/components/permissions.py` line 140: `.2f` -> `.5f`
- `scripts/batch_backtest.py` line 770: `.2f` -> `.5f`

These ensure that if a GBPUSD trade is rejected for tight SL, the denial message shows meaningful values (e.g., `SL_dist=0.00150 < 1.5*ATR=0.00194`) instead of `SL_dist=0.00 < 1.5*ATR=0.00`.

## 5. Corrected Prompt ATR Values

After fix, GBPUSD prompt for 2025-01-21 shows:

```
D1:  Avg body: 0.00526  ATR(14): 0.01136
H4:  Avg body: 0.00221  ATR(14): 0.00546
H1:  Avg body: 0.00195  ATR(14): 0.00298
M15: Avg body: 0.00108  ATR(14): 0.00129
```

All four timeframes show distinct, non-zero, correctly-scaled ATR values.

## 6. Gold Prompt ATR Values (unchanged)

Gold prompt for 2025-01-21 (same date, for comparison):

```
D1:  Avg body: 15.85  ATR(14): 31.70
H4:  Avg body: 5.50   ATR(14): 11.44
H1:  Avg body: 3.29   ATR(14): 6.56
M15: Avg body: 1.99   ATR(14): 3.40
```

Unchanged and correct. Gold was never affected by this bug.

## 7. Verification

- 463/463 tests passing
- GBPUSD dry run successful (20 prompts collected, $0.19 est cost)
- Gold dry run successful (100 prompts collected, $0.97 est cost)
- Manual ATR computation matches function output for all timeframes
- Permissions SL-ATR check now correctly blocks tight SLs for forex
- No other `round()` calls on ATR found in codebase

## 8. Files Modified

1. `src/components/market_state.py` — removed `round(atr, 2)`
2. `src/components/permissions.py` — format string `.2f` -> `.5f` in denial message
3. `scripts/batch_backtest.py` — format string `.2f` -> `.5f` in scoring rejection

## 9. Saved Artifacts

- `knowledge_base_backtest/analysis/gbpusd_sample_prompt_corrected_20260403.txt` — full corrected prompt
