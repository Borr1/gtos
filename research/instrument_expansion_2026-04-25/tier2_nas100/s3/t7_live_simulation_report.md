# T7 Production-Faithful Simulation Report
**Dates:** 2026-02-01 to 2026-02-15
**Total KZ candles:** 136
**Total API cost:** $4.00
**Batch reference:** T7: CR=86.7%, WR=66.3%, +39.5R (n=121, no L2); P2A v1: CR=38%, WR=69.6% (n=104)

**Production gates simulated:** prescreen, deterministic bias, skip_first_ny,
L2 verification, inverted TP auto-correction, max 2 trades/day, max 1 trade/KZ.

## Summary by Instrument

| Symbol | KZ Candles | API Calls | T7 CAND | L2 Reject | Limit Block | Final Trades | CR (raw) | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|--------|-----------|-----------|---------|-----------|-------------|-------------|----------|-----------|------|--------|----|---------|-----------|
| NAS100   |       136 |        69 |      35 |         1 |          29 |           5 |    50.7% |      7.2% |    4 |      1 |  80% |   +5.0R | +1.000R |

## Pipeline Funnel

- Total KZ candles: 136
- Skipped (prescreen D1/H4): 0
- Skipped (no bias): 0
- Skipped (OB proximity): 67
- Skipped (first NY candle): 0
- Sent to API: 69
- AI returned CANDIDATE: 35 (raw CR: 50.7%)
  - Inverted TP corrected: 0
  - L2 Rejected: 1
  - PA parse failed → NO_TRADE: 0 (production would retry then reject)
  - Blocked by trade limits: 29
- **Final CANDIDATE decisions: 5** (live CR: 7.2%)

## Monthly Breakdown

| Month | API Calls | Raw CAND | Final Trades | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|-------|-----------|----------|-------------|-----------|------|--------|----|---------|-----------|
| 2026-02 |        69 |       35 |           5 |      7.2% |    4 |      1 |  80% |   +5.0R | +1.000R |

## Risk Metrics

- Total resolved trades: 5
- Win rate: 80.0%
- Expectancy per trade: +1.000R
- Total R: +5.0R
- Max consecutive losses: 1
- Max drawdown: 1.0R
- Trades per week: 2.3
- Trades per month: 5.0

## Trade Distribution

- London: 3 (60%)
- NY: 2 (40%)
- LONG: 5 (100%)
- SHORT: 0 (0%)

## Day-by-Day Detail

### 2026-02-02
- API calls: 9 | Trades: 0 | L2 rejected: 1 | Limit blocked: 0

### 2026-02-03
- API calls: 30 | Trades: 2 | L2 rejected: 0 | Limit blocked: 18
  - london 2026-02-03T07:00 → LONG entry=25360.40 SL=25258.30 TP1=25513.20 → **WIN** 1.5R
  - ny 2026-02-03T14:30 → LONG entry=25360.40 SL=25262.10 TP1=25507.90 → **WIN** 1.5R

### 2026-02-04
- API calls: 12 | Trades: 1 | L2 rejected: 0 | Limit blocked: 3
  - london 2026-02-04T09:00 → LONG entry=25367.80 SL=25272.70 TP1=25510.10 → **LOSS** -1.0R

### 2026-02-05
- API calls: 8 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-06
- API calls: 10 | Trades: 2 | L2 rejected: 0 | Limit blocked: 8
  - london 2026-02-06T07:00 → LONG entry=24431.10 SL=24290.00 TP1=24642.80 → **WIN** 1.5R
  - ny 2026-02-06T13:00 → LONG entry=24515.30 SL=24408.30 TP1=24675.80 → **WIN** 1.5R

## T7 vs P2A v1 Decision Comparison

- Both CANDIDATE: 0
- T7 CANDIDATE, P2A NO_TRADE: 5
- T7 NO_TRADE, P2A CANDIDATE: 0

## Caveats

- **SL-first on wide candles:** If both SL and TP are hit in one M15 candle, SL wins (conservative bias).
- **No spread simulation:** Entry prices are AI-quoted, no spread added.
- **No tick data:** Outcome determined by M15 OHLC only, not intra-candle sequence.
- **KB context empty:** Production passes last-10-trade context; simulation does not.
