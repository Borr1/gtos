# T7 Production-Faithful Simulation Report
**Dates:** 2026-02-01 to 2026-02-15
**Total KZ candles:** 108
**Total API cost:** $4.02
**Batch reference:** T7: CR=86.7%, WR=66.3%, +39.5R (n=121, no L2); P2A v1: CR=38%, WR=69.6% (n=104)

**Production gates simulated:** prescreen, deterministic bias, skip_first_ny,
L2 verification, inverted TP auto-correction, max 2 trades/day, max 1 trade/KZ.

## Summary by Instrument

| Symbol | KZ Candles | API Calls | T7 CAND | L2 Reject | Limit Block | Final Trades | CR (raw) | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|--------|-----------|-----------|---------|-----------|-------------|-------------|----------|-----------|------|--------|----|---------|-----------|
| GER40    |       108 |        67 |      41 |         6 |          30 |           5 |    61.2% |      7.5% |    5 |      0 | 100% |   +7.5R | +1.500R |

## Pipeline Funnel

- Total KZ candles: 108
- Skipped (prescreen D1/H4): 30
- Skipped (no bias): 0
- Skipped (OB proximity): 11
- Skipped (first NY candle): 0
- Sent to API: 67
- AI returned CANDIDATE: 41 (raw CR: 61.2%)
  - Inverted TP corrected: 5
  - L2 Rejected: 6
  - PA parse failed → NO_TRADE: 0 (production would retry then reject)
  - Blocked by trade limits: 30
- **Final CANDIDATE decisions: 5** (live CR: 7.5%)

## Monthly Breakdown

| Month | API Calls | Raw CAND | Final Trades | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|-------|-----------|----------|-------------|-----------|------|--------|----|---------|-----------|
| 2026-02 |        67 |       41 |           5 |      7.5% |    5 |      0 | 100% |   +7.5R | +1.500R |

## Risk Metrics

- Total resolved trades: 5
- Win rate: 100.0%
- Expectancy per trade: +1.500R
- Total R: +7.5R
- Max consecutive losses: 0
- Max drawdown: 0.0R
- Trades per week: 2.3
- Trades per month: 5.0

## Trade Distribution

- London: 2 (40%)
- NY: 3 (60%)
- LONG: 5 (100%)
- SHORT: 0 (0%)

## Day-by-Day Detail

### 2026-02-02
- API calls: 19 | Trades: 1 | L2 rejected: 6 | Limit blocked: 4
  - ny 2026-02-02T13:00 → LONG entry=24324.80 SL=24220.50 TP1=24481.00 → **WIN** 1.5R

### 2026-02-03
- API calls: 30 | Trades: 2 | L2 rejected: 0 | Limit blocked: 17
  - london 2026-02-03T07:00 → LONG entry=24836.10 SL=24793.90 TP1=24899.40 → **WIN** 1.5R
  - ny 2026-02-03T13:15 → LONG entry=24324.80 SL=24228.20 TP1=24469.70 → **WIN** 1.5R

### 2026-02-04
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-05
- API calls: 18 | Trades: 2 | L2 rejected: 0 | Limit blocked: 9
  - london 2026-02-05T07:15 → LONG entry=24324.80 SL=24226.50 TP1=24472.00 → **WIN** 1.5R
  - ny 2026-02-05T13:00 → LONG entry=24324.80 SL=24225.40 TP1=24473.50 → **WIN** 1.5R

## T7 vs P2A v1 Decision Comparison

- Both CANDIDATE: 0
- T7 CANDIDATE, P2A NO_TRADE: 5
- T7 NO_TRADE, P2A CANDIDATE: 0

## Caveats

- **SL-first on wide candles:** If both SL and TP are hit in one M15 candle, SL wins (conservative bias).
- **No spread simulation:** Entry prices are AI-quoted, no spread added.
- **No tick data:** Outcome determined by M15 OHLC only, not intra-candle sequence.
- **KB context empty:** Production passes last-10-trade context; simulation does not.
