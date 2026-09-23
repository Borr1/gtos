# T7 Production-Faithful Simulation Report
**Dates:** 2026-02-01 to 2026-02-15
**Total KZ candles:** 300
**Total API cost:** $1.63
**Batch reference:** T7: CR=86.7%, WR=66.3%, +39.5R (n=121, no L2); P2A v1: CR=38%, WR=69.6% (n=104)

**Production gates simulated:** prescreen, deterministic bias, skip_first_ny,
L2 verification, inverted TP auto-correction, max 2 trades/day, max 1 trade/KZ.

## Summary by Instrument

| Symbol | KZ Candles | API Calls | T7 CAND | L2 Reject | Limit Block | Final Trades | CR (raw) | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|--------|-----------|-----------|---------|-----------|-------------|-------------|----------|-----------|------|--------|----|---------|-----------|
| XAGUSD   |       300 |        28 |      20 |         0 |          16 |           4 |    71.4% |     14.3% |    3 |      1 |  75% |   +3.5R | +0.875R |

## Pipeline Funnel

- Total KZ candles: 300
- Skipped (prescreen D1/H4): 90
- Skipped (no bias): 0
- Skipped (OB proximity): 182
- Skipped (first NY candle): 0
- Sent to API: 28
- AI returned CANDIDATE: 20 (raw CR: 71.4%)
  - Inverted TP corrected: 0
  - L2 Rejected: 0
  - PA parse failed → NO_TRADE: 0 (production would retry then reject)
  - Blocked by trade limits: 16
- **Final CANDIDATE decisions: 4** (live CR: 14.3%)

## Monthly Breakdown

| Month | API Calls | Raw CAND | Final Trades | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|-------|-----------|----------|-------------|-----------|------|--------|----|---------|-----------|
| 2026-02 |        28 |       20 |           4 |     14.3% |    3 |      1 |  75% |   +3.5R | +0.875R |

## Risk Metrics

- Total resolved trades: 4
- Win rate: 75.0%
- Expectancy per trade: +0.875R
- Total R: +3.5R
- Max consecutive losses: 1
- Max drawdown: 1.0R
- Trades per week: 1.9
- Trades per month: 4.0

## Trade Distribution

- London: 2 (50%)
- NY: 2 (50%)
- LONG: 4 (100%)
- SHORT: 0 (0%)

## Day-by-Day Detail

### 2026-02-02
- API calls: 4 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-03
- API calls: 2 | Trades: 1 | L2 rejected: 0 | Limit blocked: 1
  - ny 2026-02-03T15:00 → LONG entry=83.85 SL=82.20 TP1=86.32 → **WIN** 1.5R

### 2026-02-04
- API calls: 11 | Trades: 2 | L2 rejected: 0 | Limit blocked: 9
  - london 2026-02-04T08:00 → LONG entry=88.24 SL=87.22 TP1=89.76 → **WIN** 1.5R
  - ny 2026-02-04T15:00 → LONG entry=90.78 SL=89.15 TP1=93.22 → **LOSS** -1.0R

### 2026-02-05
- API calls: 1 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-06
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-09
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-10
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-11
- API calls: 7 | Trades: 1 | L2 rejected: 0 | Limit blocked: 6
  - london 2026-02-11T08:00 → LONG entry=82.64 SL=81.73 TP1=84.00 → **WIN** 1.5R

### 2026-02-12
- API calls: 3 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-13
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

## T7 vs P2A v1 Decision Comparison

- Both CANDIDATE: 0
- T7 CANDIDATE, P2A NO_TRADE: 4
- T7 NO_TRADE, P2A CANDIDATE: 0

## Caveats

- **SL-first on wide candles:** If both SL and TP are hit in one M15 candle, SL wins (conservative bias).
- **No spread simulation:** Entry prices are AI-quoted, no spread added.
- **No tick data:** Outcome determined by M15 OHLC only, not intra-candle sequence.
- **KB context empty:** Production passes last-10-trade context; simulation does not.
