# T7 Production-Faithful Simulation Report
**Dates:** 2026-01-02 to 2026-04-10
**Total KZ candles:** 1464
**Total API cost:** $35.03
**Batch reference:** T7: CR=86.7%, WR=66.3%, +39.5R (n=121, no L2); P2A v1: CR=38%, WR=69.6% (n=104)

**Production gates simulated:** prescreen, deterministic bias, skip_first_ny,
L2 verification, inverted TP auto-correction, max 2 trades/day, max 1 trade/KZ.

## Summary by Instrument

| Symbol | KZ Candles | API Calls | T7 CAND | L2 Reject | Limit Block | Final Trades | CR (raw) | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|--------|-----------|-----------|---------|-----------|-------------|-------------|----------|-----------|------|--------|----|---------|-----------|
| XAUUSD   |      1464 |      1198 |     899 |       591 |          12 |           7 |    75.0% |      0.6% |    3 |      4 |  43% |   +0.6R | +0.079R |

## Pipeline Funnel

- Total KZ candles: 1464
- Skipped (prescreen D1/H4): 217
- Skipped (no bias): 0
- Skipped (first NY candle): 49
- Sent to API: 1198
- AI returned CANDIDATE: 899 (raw CR: 75.0%)
  - Inverted TP corrected: 0
  - L2 Rejected: 591
  - PA parse failed → NO_TRADE: 289 (production would retry then reject)
  - Blocked by trade limits: 12
- **Final executable trades: 7** (live CR: 0.6%)

## Monthly Breakdown

| Month | API Calls | Raw CAND | Final Trades | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|-------|-----------|----------|-------------|-----------|------|--------|----|---------|-----------|
| 2026-01 |       392 |      312 |           4 |      1.0% |    2 |      2 |  50% |   +1.1R | +0.263R |
| 2026-02 |       580 |      429 |           2 |      0.3% |    1 |      1 |  50% |   +0.5R | +0.250R |
| 2026-03 |       226 |      158 |           1 |      0.4% |    0 |      1 |   0% |   -1.0R | -1.000R |

## Risk Metrics

- Total resolved trades: 7
- Win rate: 42.9%
- Expectancy per trade: +0.079R
- Total R: +0.6R
- Max consecutive losses: 2
- Max drawdown: 2.0R
- Trades per week: 0.5
- Trades per month: 2.2

## Trade Distribution

- London: 2 (29%)
- NY: 5 (71%)
- LONG: 7 (100%)
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
- API calls: 25 | Trades: 0 | L2 rejected: 9 | Limit blocked: 0

### 2026-01-08
- API calls: 29 | Trades: 0 | L2 rejected: 17 | Limit blocked: 0

### 2026-01-09
- API calls: 4 | Trades: 0 | L2 rejected: 3 | Limit blocked: 0

### 2026-01-12
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-01-13
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-01-14
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-01-15
- API calls: 15 | Trades: 1 | L2 rejected: 7 | Limit blocked: 2
  - ny 2026-01-15T13:15 → LONG entry=4618.93 SL=4597.79 TP1=4650.62 → **LOSS** -1.0R

### 2026-01-16
- API calls: 29 | Trades: 0 | L2 rejected: 11 | Limit blocked: 0

### 2026-01-19
- API calls: 29 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-01-20
- API calls: 29 | Trades: 1 | L2 rejected: 24 | Limit blocked: 3
  - ny 2026-01-20T16:00 → LONG entry=4727.61 SL=4715.35 TP1=4745.99 → **WIN** 1.5R

### 2026-01-21
- API calls: 29 | Trades: 1 | L2 rejected: 17 | Limit blocked: 3
  - ny 2026-01-21T15:00 → LONG entry=4869.07 SL=4855.09 TP1=4890.04 → **LOSS** -1.0R

### 2026-01-22
- API calls: 29 | Trades: 0 | L2 rejected: 16 | Limit blocked: 0

### 2026-01-23
- API calls: 29 | Trades: 0 | L2 rejected: 14 | Limit blocked: 0

### 2026-01-26
- API calls: 29 | Trades: 0 | L2 rejected: 12 | Limit blocked: 0

### 2026-01-27
- API calls: 29 | Trades: 1 | L2 rejected: 18 | Limit blocked: 2
  - london 2026-01-27T07:00 → LONG entry=5064.67 SL=5055.17 TP1=5079.42 → **WIN** 1.55R

### 2026-01-28
- API calls: 29 | Trades: 0 | L2 rejected: 27 | Limit blocked: 0

### 2026-01-29
- API calls: 29 | Trades: 0 | L2 rejected: 1 | Limit blocked: 0

### 2026-01-30
- API calls: 29 | Trades: 0 | L2 rejected: 19 | Limit blocked: 0

### 2026-02-02
- API calls: 29 | Trades: 0 | L2 rejected: 3 | Limit blocked: 0

### 2026-02-03
- API calls: 29 | Trades: 0 | L2 rejected: 24 | Limit blocked: 0

### 2026-02-04
- API calls: 29 | Trades: 0 | L2 rejected: 13 | Limit blocked: 0

### 2026-02-05
- API calls: 29 | Trades: 0 | L2 rejected: 2 | Limit blocked: 0

### 2026-02-06
- API calls: 29 | Trades: 1 | L2 rejected: 25 | Limit blocked: 0
  - london 2026-02-06T07:00 → LONG entry=4826.29 SL=4801.10 TP1=4864.03 → **WIN** 1.5R

### 2026-02-09
- API calls: 29 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-10
- API calls: 29 | Trades: 0 | L2 rejected: 24 | Limit blocked: 0

### 2026-02-11
- API calls: 29 | Trades: 0 | L2 rejected: 22 | Limit blocked: 0

### 2026-02-12
- API calls: 29 | Trades: 0 | L2 rejected: 13 | Limit blocked: 0

### 2026-02-13
- API calls: 29 | Trades: 0 | L2 rejected: 10 | Limit blocked: 0

### 2026-02-16
- API calls: 29 | Trades: 0 | L2 rejected: 15 | Limit blocked: 0

### 2026-02-17
- API calls: 29 | Trades: 0 | L2 rejected: 12 | Limit blocked: 0

### 2026-02-18
- API calls: 29 | Trades: 0 | L2 rejected: 17 | Limit blocked: 0

### 2026-02-19
- API calls: 29 | Trades: 0 | L2 rejected: 26 | Limit blocked: 0

### 2026-02-20
- API calls: 29 | Trades: 1 | L2 rejected: 17 | Limit blocked: 2
  - ny 2026-02-20T15:00 → LONG entry=5042.42 SL=5007.00 TP1=5095.49 → **LOSS** -1.0R

### 2026-02-23
- API calls: 29 | Trades: 0 | L2 rejected: 2 | Limit blocked: 0

### 2026-02-24
- API calls: 29 | Trades: 0 | L2 rejected: 10 | Limit blocked: 0

### 2026-02-25
- API calls: 29 | Trades: 0 | L2 rejected: 25 | Limit blocked: 0

### 2026-02-26
- API calls: 29 | Trades: 0 | L2 rejected: 18 | Limit blocked: 0

### 2026-02-27
- API calls: 29 | Trades: 0 | L2 rejected: 14 | Limit blocked: 0

### 2026-03-02
- API calls: 29 | Trades: 0 | L2 rejected: 17 | Limit blocked: 0

### 2026-03-03
- API calls: 29 | Trades: 0 | L2 rejected: 7 | Limit blocked: 0

### 2026-03-04
- API calls: 29 | Trades: 0 | L2 rejected: 18 | Limit blocked: 0

### 2026-03-05
- API calls: 29 | Trades: 0 | L2 rejected: 16 | Limit blocked: 0

### 2026-03-06
- API calls: 29 | Trades: 0 | L2 rejected: 17 | Limit blocked: 0

### 2026-03-09
- API calls: 29 | Trades: 0 | L2 rejected: 12 | Limit blocked: 0

### 2026-03-10
- API calls: 29 | Trades: 1 | L2 rejected: 3 | Limit blocked: 0
  - ny 2026-03-10T16:00 → LONG entry=5200.47 SL=5162.26 TP1=5257.78 → **LOSS** -1.0R

### 2026-03-11
- API calls: 23 | Trades: 0 | L2 rejected: 14 | Limit blocked: 0

## T7 vs P2A v1 Decision Comparison

- Both CANDIDATE: 0
- T7 CANDIDATE, P2A NO_TRADE: 7
- T7 NO_TRADE, P2A CANDIDATE: 0

## Caveats

- **SL-first on wide candles:** If both SL and TP are hit in one M15 candle, SL wins (conservative bias).
- **No spread simulation:** Entry prices are AI-quoted, no spread added.
- **No tick data:** Outcome determined by M15 OHLC only, not intra-candle sequence.
- **KB context empty:** Production passes last-10-trade context; simulation does not.
