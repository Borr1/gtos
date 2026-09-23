# T7 Production-Faithful Simulation Report
**Dates:** 2026-01-16 to 2026-01-31
**Total KZ candles:** 81
**Total API cost:** $4.03
**Batch reference:** T7: CR=86.7%, WR=66.3%, +39.5R (n=121, no L2); P2A v1: CR=38%, WR=69.6% (n=104)

**Production gates simulated:** prescreen, deterministic bias, skip_first_ny,
L2 verification, inverted TP auto-correction, max 2 trades/day, max 1 trade/KZ.

## Summary by Instrument

| Symbol | KZ Candles | API Calls | T7 CAND | L2 Reject | Limit Block | Final Trades | CR (raw) | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|--------|-----------|-----------|---------|-----------|-------------|-------------|----------|-----------|------|--------|----|---------|-----------|
| NAS100   |        81 |        70 |      30 |         6 |          22 |           2 |    42.9% |      2.9% |    2 |      0 | 100% |   +3.0R | +1.500R |

## Pipeline Funnel

- Total KZ candles: 81
- Skipped (prescreen D1/H4): 0
- Skipped (no bias): 0
- Skipped (OB proximity): 11
- Skipped (first NY candle): 0
- Sent to API: 70
- AI returned CANDIDATE: 30 (raw CR: 42.9%)
  - Inverted TP corrected: 0
  - L2 Rejected: 6
  - PA parse failed → NO_TRADE: 0 (production would retry then reject)
  - Blocked by trade limits: 22
- **Final CANDIDATE decisions: 2** (live CR: 2.9%)

## Monthly Breakdown

| Month | API Calls | Raw CAND | Final Trades | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|-------|-----------|----------|-------------|-----------|------|--------|----|---------|-----------|
| 2026-01 |        70 |       30 |           2 |      2.9% |    2 |      0 | 100% |   +3.0R | +1.500R |

## Risk Metrics

- Total resolved trades: 2
- Win rate: 100.0%
- Expectancy per trade: +1.500R
- Total R: +3.0R
- Max consecutive losses: 0
- Max drawdown: 0.0R
- Trades per week: 0.9
- Trades per month: 2.0

## Trade Distribution

- London: 1 (50%)
- NY: 1 (50%)
- LONG: 2 (100%)
- SHORT: 0 (0%)

## Day-by-Day Detail

### 2026-01-16
- API calls: 28 | Trades: 2 | L2 rejected: 0 | Limit blocked: 22
  - london 2026-01-16T07:00 → LONG entry=25438.50 SL=25394.90 TP1=25503.90 → **WIN** 1.5R
  - ny 2026-01-16T13:30 → LONG entry=25438.50 SL=25396.30 TP1=25501.80 → **WIN** 1.5R

### 2026-01-19
- API calls: 21 | Trades: 0 | L2 rejected: 2 | Limit blocked: 0

### 2026-01-20
- API calls: 21 | Trades: 0 | L2 rejected: 4 | Limit blocked: 0

## T7 vs P2A v1 Decision Comparison

- Both CANDIDATE: 0
- T7 CANDIDATE, P2A NO_TRADE: 2
- T7 NO_TRADE, P2A CANDIDATE: 0

## Caveats

- **SL-first on wide candles:** If both SL and TP are hit in one M15 candle, SL wins (conservative bias).
- **No spread simulation:** Entry prices are AI-quoted, no spread added.
- **No tick data:** Outcome determined by M15 OHLC only, not intra-candle sequence.
- **KB context empty:** Production passes last-10-trade context; simulation does not.
