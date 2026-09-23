# T7 Production-Faithful Simulation Report
**Dates:** 2026-01-02 to 2026-02-28
**Total KZ candles:** 1230
**Total API cost:** $26.39
**Batch reference:** T7: CR=86.7%, WR=66.3%, +39.5R (n=121, no L2); P2A v1: CR=38%, WR=69.6% (n=104)

**Production gates simulated:** prescreen, deterministic bias, skip_first_ny,
L2 verification, inverted TP auto-correction, max 2 trades/day, max 1 trade/KZ.

## Summary by Instrument

| Symbol | KZ Candles | API Calls | T7 CAND | L2 Reject | Limit Block | Final Trades | CR (raw) | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|--------|-----------|-----------|---------|-----------|-------------|-------------|----------|-----------|------|--------|----|---------|-----------|
| EURUSD   |      1230 |       912 |     175 |       155 |          15 |           5 |    19.2% |      0.5% |    0 |      5 |   0% |   -5.0R | -1.000R |

## Pipeline Funnel

- Total KZ candles: 1230
- Skipped (prescreen D1/H4): 100
- Skipped (no bias): 0
- Skipped (OB proximity): 218
- Skipped (first NY candle): 0
- Sent to API: 912
- AI returned CANDIDATE: 175 (raw CR: 19.2%)
  - Inverted TP corrected: 0
  - L2 Rejected: 155
  - PA parse failed → NO_TRADE: 0 (production would retry then reject)
  - Blocked by trade limits: 15
- **Final CANDIDATE decisions: 5** (live CR: 0.5%)

## Monthly Breakdown

| Month | API Calls | Raw CAND | Final Trades | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|-------|-----------|----------|-------------|-----------|------|--------|----|---------|-----------|
| 2026-01 |       402 |       54 |           2 |      0.5% |    0 |      2 |   0% |   -2.0R | -1.000R |
| 2026-02 |       510 |      121 |           3 |      0.6% |    0 |      3 |   0% |   -3.0R | -1.000R |

## Risk Metrics

- Total resolved trades: 5
- Win rate: 0.0%
- Expectancy per trade: -1.000R
- Total R: -5.0R
- Max consecutive losses: 5
- Max drawdown: 5.0R
- Trades per week: 0.6
- Trades per month: 2.6

## Trade Distribution

- London: 4 (80%)
- NY: 1 (20%)
- LONG: 4 (80%)
- SHORT: 1 (20%)

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
- API calls: 12 | Trades: 1 | L2 rejected: 0 | Limit blocked: 0
  - london 2026-01-07T09:30 → SHORT entry=1.17 SL=1.17 TP1=1.17 → **LOSS** -1.0R

### 2026-01-08
- API calls: 10 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-01-09
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-01-12
- API calls: 30 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-01-13
- API calls: 30 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-01-14
- API calls: 30 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-01-15
- API calls: 14 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-01-16
- API calls: 4 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-01-19
- API calls: 30 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-01-20
- API calls: 30 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-01-21
- API calls: 30 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-01-22
- API calls: 30 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-01-23
- API calls: 30 | Trades: 0 | L2 rejected: 6 | Limit blocked: 0

### 2026-01-26
- API calls: 4 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-01-27
- API calls: 30 | Trades: 0 | L2 rejected: 6 | Limit blocked: 0

### 2026-01-28
- API calls: 28 | Trades: 0 | L2 rejected: 10 | Limit blocked: 0

### 2026-01-29
- API calls: 30 | Trades: 0 | L2 rejected: 12 | Limit blocked: 0

### 2026-01-30
- API calls: 30 | Trades: 1 | L2 rejected: 18 | Limit blocked: 0
  - ny 2026-01-30T13:00 → LONG entry=1.19 SL=1.19 TP1=1.19 → **LOSS** -1.0R

### 2026-02-02
- API calls: 30 | Trades: 0 | L2 rejected: 9 | Limit blocked: 0

### 2026-02-03
- API calls: 30 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-04
- API calls: 30 | Trades: 1 | L2 rejected: 2 | Limit blocked: 14
  - london 2026-02-04T07:00 → LONG entry=1.18 SL=1.18 TP1=1.18 → **LOSS** -1.0R

### 2026-02-05
- API calls: 30 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-06
- API calls: 30 | Trades: 0 | L2 rejected: 19 | Limit blocked: 0

### 2026-02-09
- API calls: 30 | Trades: 0 | L2 rejected: 13 | Limit blocked: 0

### 2026-02-10
- API calls: 30 | Trades: 1 | L2 rejected: 17 | Limit blocked: 1
  - london 2026-02-10T08:15 → LONG entry=1.18 SL=1.17 TP1=1.19 → **LOSS** -1.0R

### 2026-02-11
- API calls: 30 | Trades: 0 | L2 rejected: 23 | Limit blocked: 0

### 2026-02-12
- API calls: 30 | Trades: 0 | L2 rejected: 11 | Limit blocked: 0

### 2026-02-13
- API calls: 30 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-16
- API calls: 30 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-17
- API calls: 26 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-18
- API calls: 14 | Trades: 0 | L2 rejected: 2 | Limit blocked: 0

### 2026-02-19
- API calls: 26 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-20
- API calls: 30 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-23
- API calls: 30 | Trades: 1 | L2 rejected: 7 | Limit blocked: 0
  - london 2026-02-23T08:00 → LONG entry=1.18 SL=1.17 TP1=1.19 → **LOSS** -1.0R

### 2026-02-24
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-25
- API calls: 20 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-26
- API calls: 20 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-27
- API calls: 14 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

## T7 vs P2A v1 Decision Comparison

- Both CANDIDATE: 0
- T7 CANDIDATE, P2A NO_TRADE: 5
- T7 NO_TRADE, P2A CANDIDATE: 0

## Caveats

- **SL-first on wide candles:** If both SL and TP are hit in one M15 candle, SL wins (conservative bias).
- **No spread simulation:** Entry prices are AI-quoted, no spread added.
- **No tick data:** Outcome determined by M15 OHLC only, not intra-candle sequence.
- **KB context empty:** Production passes last-10-trade context; simulation does not.
