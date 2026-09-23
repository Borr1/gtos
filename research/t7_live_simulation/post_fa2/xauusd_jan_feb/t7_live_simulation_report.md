# T7 Production-Faithful Simulation Report
**Dates:** 2026-01-02 to 2026-02-28
**Total KZ candles:** 1230
**Total API cost:** $7.62
**Batch reference:** T7: CR=86.7%, WR=66.3%, +39.5R (n=121, no L2); P2A v1: CR=38%, WR=69.6% (n=104)

**Production gates simulated:** prescreen, deterministic bias, skip_first_ny,
L2 verification, inverted TP auto-correction, max 2 trades/day, max 1 trade/KZ.

## Summary by Instrument

| Symbol | KZ Candles | API Calls | T7 CAND | L2 Reject | Limit Block | Final Trades | CR (raw) | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|--------|-----------|-----------|---------|-----------|-------------|-------------|----------|-----------|------|--------|----|---------|-----------|
| XAUUSD   |      1230 |       250 |      83 |        10 |          59 |          14 |    33.2% |      5.6% |    5 |      9 |  36% |   -1.5R | -0.107R |

## Pipeline Funnel

- Total KZ candles: 1230
- Skipped (prescreen D1/H4): 217
- Skipped (no bias): 0
- Skipped (OB proximity): 722
- Skipped (first NY candle): 41
- Sent to API: 250
- AI returned CANDIDATE: 83 (raw CR: 33.2%)
  - Inverted TP corrected: 0
  - L2 Rejected: 10
  - PA parse failed → NO_TRADE: 0 (production would retry then reject)
  - Blocked by trade limits: 59
- **Final CANDIDATE decisions: 14** (live CR: 5.6%)

## Monthly Breakdown

| Month | API Calls | Raw CAND | Final Trades | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|-------|-----------|----------|-------------|-----------|------|--------|----|---------|-----------|
| 2026-01 |        89 |       27 |           4 |      4.5% |    0 |      4 |   0% |   -4.0R | -1.000R |
| 2026-02 |       161 |       56 |          10 |      6.2% |    5 |      5 |  50% |   +2.5R | +0.250R |

## Risk Metrics

- Total resolved trades: 14
- Win rate: 35.7%
- Expectancy per trade: -0.107R
- Total R: -1.5R
- Max consecutive losses: 5
- Max drawdown: 5.0R
- Trades per week: 1.7
- Trades per month: 7.3

## Trade Distribution

- London: 6 (43%)
- NY: 8 (57%)
- LONG: 14 (100%)
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
- API calls: 25 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-01-08
- API calls: 8 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-01-09
- API calls: 4 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

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
- API calls: 7 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-01-16
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-01-19
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-01-20
- API calls: 18 | Trades: 2 | L2 rejected: 1 | Limit blocked: 14
  - london 2026-01-20T07:00 → LONG entry=4674.73 SL=4661.95 TP1=4693.90 → **LOSS** -1.0R
  - ny 2026-01-20T16:15 → LONG entry=4674.73 SL=4656.76 TP1=4701.68 → **LOSS** -1.0R

### 2026-01-21
- API calls: 8 | Trades: 1 | L2 rejected: 2 | Limit blocked: 3
  - ny 2026-01-21T15:00 → LONG entry=4870.77 SL=4827.00 TP1=4936.38 → **LOSS** -1.0R

### 2026-01-22
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-01-23
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-01-26
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-01-27
- API calls: 8 | Trades: 1 | L2 rejected: 0 | Limit blocked: 3
  - london 2026-01-27T07:00 → LONG entry=5078.62 SL=5052.47 TP1=5117.87 → **LOSS** -1.0R

### 2026-01-28
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-01-29
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-01-30
- API calls: 11 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-02
- API calls: 3 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-03
- API calls: 11 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-04
- API calls: 7 | Trades: 1 | L2 rejected: 0 | Limit blocked: 0
  - ny 2026-02-04T13:45 → LONG entry=4957.40 SL=4898.64 TP1=5045.51 → **LOSS** -1.0R

### 2026-02-05
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-06
- API calls: 6 | Trades: 1 | L2 rejected: 0 | Limit blocked: 2
  - london 2026-02-06T07:00 → LONG entry=4831.50 SL=4801.54 TP1=4876.44 → **WIN** 1.5R

### 2026-02-09
- API calls: 7 | Trades: 2 | L2 rejected: 0 | Limit blocked: 2
  - london 2026-02-09T09:45 → LONG entry=4958.88 SL=4926.62 TP1=5007.16 → **WIN** 1.5R
  - ny 2026-02-09T15:15 → LONG entry=4958.88 SL=4927.58 TP1=5005.73 → **WIN** 1.5R

### 2026-02-10
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-11
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-12
- API calls: 4 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-13
- API calls: 9 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-16
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-17
- API calls: 8 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-18
- API calls: 22 | Trades: 1 | L2 rejected: 0 | Limit blocked: 8
  - ny 2026-02-18T14:00 → LONG entry=4917.55 SL=4901.15 TP1=4941.95 → **LOSS** -1.0R

### 2026-02-19
- API calls: 21 | Trades: 2 | L2 rejected: 1 | Limit blocked: 16
  - london 2026-02-19T07:00 → LONG entry=4917.55 SL=4902.02 TP1=4940.88 → **LOSS** -1.0R
  - ny 2026-02-19T13:15 → LONG entry=4917.55 SL=4901.84 TP1=4941.08 → **LOSS** -1.0R

### 2026-02-20
- API calls: 25 | Trades: 2 | L2 rejected: 6 | Limit blocked: 8
  - london 2026-02-20T09:15 → LONG entry=4999.11 SL=4976.04 TP1=5033.72 → **WIN** 1.5R
  - ny 2026-02-20T13:15 → LONG entry=4917.55 SL=4901.63 TP1=4941.43 → **LOSS** -1.0R

### 2026-02-23
- API calls: 4 | Trades: 1 | L2 rejected: 0 | Limit blocked: 3
  - ny 2026-02-23T16:00 → LONG entry=5165.02 SL=5137.52 TP1=5206.27 → **WIN** 1.5R

### 2026-02-24
- API calls: 12 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-25
- API calls: 14 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-26
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-27
- API calls: 8 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

## T7 vs P2A v1 Decision Comparison

- Both CANDIDATE: 0
- T7 CANDIDATE, P2A NO_TRADE: 14
- T7 NO_TRADE, P2A CANDIDATE: 0

## Caveats

- **SL-first on wide candles:** If both SL and TP are hit in one M15 candle, SL wins (conservative bias).
- **No spread simulation:** Entry prices are AI-quoted, no spread added.
- **No tick data:** Outcome determined by M15 OHLC only, not intra-candle sequence.
- **KB context empty:** Production passes last-10-trade context; simulation does not.
