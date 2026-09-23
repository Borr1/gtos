# T7 Production-Faithful Simulation Report
**Dates:** 2026-03-03 to 2026-03-22
**Total KZ candles:** 420
**Total API cost:** $3.05
**Batch reference:** T7: CR=86.7%, WR=66.3%, +39.5R (n=121, no L2); P2A v1: CR=38%, WR=69.6% (n=104)

**Production gates simulated:** prescreen, deterministic bias, skip_first_ny,
L2 verification, inverted TP auto-correction, max 2 trades/day, max 1 trade/KZ.

## Summary by Instrument

| Symbol | KZ Candles | API Calls | T7 CAND | L2 Reject | Limit Block | Final Trades | CR (raw) | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|--------|-----------|-----------|---------|-----------|-------------|-------------|----------|-----------|------|--------|----|---------|-----------|
| XAGUSD   |       420 |        53 |      34 |         9 |          16 |           9 |    64.2% |     17.0% |    7 |      2 |  78% |   +7.3R | +0.812R |

## Pipeline Funnel

- Total KZ candles: 420
- Skipped (prescreen D1/H4): 0
- Skipped (no bias): 0
- Skipped (OB proximity): 367
- Skipped (first NY candle): 0
- Sent to API: 53
- AI returned CANDIDATE: 34 (raw CR: 64.2%)
  - Inverted TP corrected: 0
  - L2 Rejected: 9
  - PA parse failed → NO_TRADE: 0 (production would retry then reject)
  - Blocked by trade limits: 16
- **Final CANDIDATE decisions: 9** (live CR: 17.0%)

## Monthly Breakdown

| Month | API Calls | Raw CAND | Final Trades | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|-------|-----------|----------|-------------|-----------|------|--------|----|---------|-----------|
| 2026-03 |        53 |       34 |           9 |     17.0% |    7 |      2 |  78% |   +7.3R | +0.812R |

## Risk Metrics

- Total resolved trades: 9
- Win rate: 77.8%
- Expectancy per trade: +0.812R
- Total R: +7.3R
- Max consecutive losses: 1
- Max drawdown: 1.0R
- Trades per week: 3.1
- Trades per month: 9.0

## Trade Distribution

- London: 4 (44%)
- NY: 5 (56%)
- LONG: 4 (44%)
- SHORT: 5 (56%)

## Day-by-Day Detail

### 2026-03-03
- API calls: 5 | Trades: 1 | L2 rejected: 0 | Limit blocked: 1
  - london 2026-03-03T08:00 → SHORT entry=89.66 SL=90.70 TP1=88.09 → **WIN** 1.5R

### 2026-03-04
- API calls: 5 | Trades: 1 | L2 rejected: 0 | Limit blocked: 2
  - ny 2026-03-04T15:00 → LONG entry=82.67 SL=81.44 TP1=84.51 → **WIN** 1.5R

### 2026-03-05
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-03-06
- API calls: 5 | Trades: 1 | L2 rejected: 0 | Limit blocked: 3
  - london 2026-03-06T09:00 → LONG entry=84.29 SL=83.03 TP1=84.69 → **WIN** 0.31R

### 2026-03-09
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-03-10
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-03-11
- API calls: 7 | Trades: 1 | L2 rejected: 0 | Limit blocked: 0
  - ny 2026-03-11T14:30 → LONG entry=84.75 SL=83.58 TP1=86.51 → **WIN** 1.5R

### 2026-03-12
- API calls: 2 | Trades: 1 | L2 rejected: 0 | Limit blocked: 1
  - london 2026-03-12T09:00 → LONG entry=84.90 SL=84.10 TP1=85.70 → **LOSS** -1.0R

### 2026-03-13
- API calls: 5 | Trades: 0 | L2 rejected: 3 | Limit blocked: 0

### 2026-03-16
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-03-17
- API calls: 4 | Trades: 1 | L2 rejected: 0 | Limit blocked: 3
  - ny 2026-03-17T13:00 → SHORT entry=80.56 SL=81.56 TP1=79.06 → **WIN** 1.5R

### 2026-03-18
- API calls: 10 | Trades: 1 | L2 rejected: 3 | Limit blocked: 4
  - ny 2026-03-18T15:00 → SHORT entry=79.14 SL=79.61 TP1=78.43 → **LOSS** -1.0R

### 2026-03-19
- API calls: 2 | Trades: 0 | L2 rejected: 2 | Limit blocked: 0

### 2026-03-20
- API calls: 8 | Trades: 2 | L2 rejected: 1 | Limit blocked: 2
  - london 2026-03-20T09:00 → SHORT entry=73.75 SL=74.75 TP1=72.26 → **WIN** 1.5R
  - ny 2026-03-20T16:00 → SHORT entry=71.41 SL=72.67 TP1=69.52 → **WIN** 1.5R

## T7 vs P2A v1 Decision Comparison

- Both CANDIDATE: 0
- T7 CANDIDATE, P2A NO_TRADE: 9
- T7 NO_TRADE, P2A CANDIDATE: 0

## Caveats

- **SL-first on wide candles:** If both SL and TP are hit in one M15 candle, SL wins (conservative bias).
- **No spread simulation:** Entry prices are AI-quoted, no spread added.
- **No tick data:** Outcome determined by M15 OHLC only, not intra-candle sequence.
- **KB context empty:** Production passes last-10-trade context; simulation does not.
