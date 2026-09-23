# T7 Production-Faithful Simulation Report
**Dates:** 2026-01-02 to 2026-01-15
**Total KZ candles:** 199
**Total API cost:** $4.05
**Batch reference:** T7: CR=86.7%, WR=66.3%, +39.5R (n=121, no L2); P2A v1: CR=38%, WR=69.6% (n=104)

**Production gates simulated:** prescreen, deterministic bias, skip_first_ny,
L2 verification, inverted TP auto-correction, max 2 trades/day, max 1 trade/KZ.

## Summary by Instrument

| Symbol | KZ Candles | API Calls | T7 CAND | L2 Reject | Limit Block | Final Trades | CR (raw) | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|--------|-----------|-----------|---------|-----------|-------------|-------------|----------|-----------|------|--------|----|---------|-----------|
| GER40    |       199 |        67 |      60 |         2 |          52 |           6 |    89.6% |      9.0% |    3 |      3 |  50% |   +1.5R | +0.250R |

## Pipeline Funnel

- Total KZ candles: 199
- Skipped (prescreen D1/H4): 120
- Skipped (no bias): 0
- Skipped (OB proximity): 12
- Skipped (first NY candle): 0
- Sent to API: 67
- AI returned CANDIDATE: 60 (raw CR: 89.6%)
  - Inverted TP corrected: 2
  - L2 Rejected: 2
  - PA parse failed → NO_TRADE: 0 (production would retry then reject)
  - Blocked by trade limits: 52
- **Final CANDIDATE decisions: 6** (live CR: 9.0%)

## Monthly Breakdown

| Month | API Calls | Raw CAND | Final Trades | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|-------|-----------|----------|-------------|-----------|------|--------|----|---------|-----------|
| 2026-01 |        67 |       60 |           6 |      9.0% |    3 |      3 |  50% |   +1.5R | +0.250R |

## Risk Metrics

- Total resolved trades: 6
- Win rate: 50.0%
- Expectancy per trade: +0.250R
- Total R: +1.5R
- Max consecutive losses: 1
- Max drawdown: 1.0R
- Trades per week: 3.0
- Trades per month: 6.0

## Trade Distribution

- London: 3 (50%)
- NY: 3 (50%)
- LONG: 6 (100%)
- SHORT: 0 (0%)

## Day-by-Day Detail

### 2026-01-02
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-01-05
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-01-06
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-01-07
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-01-08
- API calls: 30 | Trades: 2 | L2 rejected: 2 | Limit blocked: 20
  - london 2026-01-08T08:00 → LONG entry=24968.60 SL=24929.40 TP1=25027.50 → **LOSS** -1.0R
  - ny 2026-01-08T13:00 → LONG entry=25049.90 SL=24990.50 TP1=25139.00 → **WIN** 1.5R

### 2026-01-09
- API calls: 30 | Trades: 2 | L2 rejected: 0 | Limit blocked: 27
  - london 2026-01-09T07:00 → LONG entry=24968.60 SL=24929.60 TP1=27027.10 → **LOSS** -1.0R
  - ny 2026-01-09T13:00 → LONG entry=25151.30 SL=25093.80 TP1=25237.60 → **WIN** 1.5R

### 2026-01-12
- API calls: 7 | Trades: 2 | L2 rejected: 0 | Limit blocked: 5
  - london 2026-01-12T07:45 → LONG entry=24546.50 SL=24515.80 TP1=24592.50 → **WIN** 1.5R
  - ny 2026-01-12T13:00 → LONG entry=25266.20 SL=25154.10 TP1=25434.40 → **LOSS** -1.0R

## T7 vs P2A v1 Decision Comparison

- Both CANDIDATE: 0
- T7 CANDIDATE, P2A NO_TRADE: 6
- T7 NO_TRADE, P2A CANDIDATE: 0

## Caveats

- **SL-first on wide candles:** If both SL and TP are hit in one M15 candle, SL wins (conservative bias).
- **No spread simulation:** Entry prices are AI-quoted, no spread added.
- **No tick data:** Outcome determined by M15 OHLC only, not intra-candle sequence.
- **KB context empty:** Production passes last-10-trade context; simulation does not.
