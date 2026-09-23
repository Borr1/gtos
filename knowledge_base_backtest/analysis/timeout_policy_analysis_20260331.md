# Session Timeout Policy Analysis — Session 4
Generated: 2026-03-31

## Data: 40 timeout trades from Session 3 validation batch

## Current Behavior
Trades that don't hit SL or any TP within the kill zone window are closed at the
last candle's close price. These 40 trades average +0.81R — the single largest
contributor to system profitability.

## Post-Timeout Price Action (next 4 hours)
| Metric | Value |
|--------|-------|
| Trades analyzed | 40 |
| Avg R at timeout | +0.81R |
| Avg post-timeout MFE | +0.65R |
| Avg post-timeout MAE | +0.37R |
| Continued favorable (MFE > 0.3R) | 23/40 (57%) |
| Reversed significantly (MAE > 0.5R) | 11/40 (28%) |

## Trailing 2h with BE Stop Simulation
| Metric | Value |
|--------|-------|
| Avg additional R per trade | +0.167R |
| Positive outcomes | 12/40 (30%) |
| Total extra R across all 40 trades | +6.67R |

## Recommendation: TRAIL WITH BE STOP FOR 2 HOURS

**Rationale:**
- Post-timeout MFE (+0.65R) significantly exceeds MAE (+0.37R)
- 57% of trades continue favorably vs 28% reversing significantly
- Trailing with BE stop adds estimated +0.167R/trade (+6.67R total)
- Downside is limited: BE stop protects existing gains

**Implementation (for Component 4 execution engine):**
After session window closes, if trade is still open:
1. Move SL to entry price (breakeven stop)
2. Continue monitoring for up to 2 hours (8 M15 candles)
3. Close at first of: TP hit, BE stop hit, or 2-hour timeout
4. This applies to BOTH London and NY timeouts

**Expected Impact:**
- Current timeout avg: +0.81R
- With trailing: estimated +0.98R avg (+0.167R improvement)
- Over 40 timeout trades: +6.67R additional profit

**Note:** This is analysis only. Implementation deferred to live pipeline build.
