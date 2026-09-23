# T7 Production-Faithful Simulation Report
**Dates:** 2026-01-28 to 2026-02-09
**Total KZ candles:** 270
**Total API cost:** $1.19
**Batch reference:** T7: CR=86.7%, WR=66.3%, +39.5R (n=121, no L2); P2A v1: CR=38%, WR=69.6% (n=104)

**Production gates simulated:** prescreen, deterministic bias, skip_first_ny,
L2 verification, inverted TP auto-correction, max 2 trades/day, max 1 trade/KZ.

## Summary by Instrument

| Symbol | KZ Candles | API Calls | T7 CAND | L2 Reject | Limit Block | Final Trades | CR (raw) | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|--------|-----------|-----------|---------|-----------|-------------|-------------|----------|-----------|------|--------|----|---------|-----------|
| XAUUSD   |       270 |        38 |      30 |         5 |          17 |           8 |    78.9% |     21.1% |    5 |      3 |  62% |   +4.5R | +0.562R |

## Pipeline Funnel

- Total KZ candles: 270
- Skipped (prescreen D1/H4): 25
- Skipped (no bias): 0
- Skipped (OB proximity): 198
- Skipped (first NY candle): 9
- Sent to API: 38
- AI returned CANDIDATE: 30 (raw CR: 78.9%)
  - Inverted TP corrected: 0
  - L2 Rejected: 5
  - PA parse failed → NO_TRADE: 0 (production would retry then reject)
  - Blocked by trade limits: 17
- **Final CANDIDATE decisions: 8** (live CR: 21.1%)

## Monthly Breakdown

| Month | API Calls | Raw CAND | Final Trades | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|-------|-----------|----------|-------------|-----------|------|--------|----|---------|-----------|
| 2026-01 |        11 |        9 |           2 |     18.2% |    0 |      2 |   0% |   -2.0R | -1.000R |
| 2026-02 |        27 |       21 |           6 |     22.2% |    5 |      1 |  83% |   +6.5R | +1.083R |

## Risk Metrics

- Total resolved trades: 8
- Win rate: 62.5%
- Expectancy per trade: +0.562R
- Total R: +4.5R
- Max consecutive losses: 2
- Max drawdown: 2.0R
- Trades per week: 4.3
- Trades per month: 8.0

## Trade Distribution

- London: 4 (50%)
- NY: 4 (50%)
- LONG: 8 (100%)
- SHORT: 0 (0%)

## Day-by-Day Detail

### 2026-01-28
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-01-29
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-01-30
- API calls: 11 | Trades: 2 | L2 rejected: 0 | Limit blocked: 7
  - london 2026-01-30T08:00 → LONG entry=5094.12 SL=5069.27 TP1=5131.41 → **LOSS** -1.0R
  - ny 2026-01-30T13:15 → LONG entry=4832.49 SL=4804.07 TP1=4875.12 → **LOSS** -1.0R

### 2026-02-02
- API calls: 3 | Trades: 1 | L2 rejected: 0 | Limit blocked: 0
  - london 2026-02-02T07:15 → LONG entry=4603.47 SL=4568.59 TP1=4655.77 → **WIN** 1.5R

### 2026-02-03
- API calls: 11 | Trades: 2 | L2 rejected: 2 | Limit blocked: 7
  - london 2026-02-03T08:00 → LONG entry=4824.97 SL=4799.00 TP1=4863.92 → **WIN** 1.5R
  - ny 2026-02-03T14:00 → LONG entry=4824.97 SL=4800.37 TP1=4861.87 → **WIN** 1.5R

### 2026-02-04
- API calls: 3 | Trades: 1 | L2 rejected: 0 | Limit blocked: 1
  - ny 2026-02-04T13:30 → LONG entry=4957.40 SL=4898.62 TP1=5045.57 → **LOSS** -1.0R

### 2026-02-05
- API calls: 1 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-06
- API calls: 9 | Trades: 2 | L2 rejected: 3 | Limit blocked: 2
  - london 2026-02-06T07:15 → LONG entry=4831.50 SL=4800.93 TP1=4877.33 → **WIN** 1.5R
  - ny 2026-02-06T15:00 → LONG entry=4861.53 SL=4825.59 TP1=4915.42 → **WIN** 1.5R

### 2026-02-09
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

## T7 vs P2A v1 Decision Comparison

- Both CANDIDATE: 0
- T7 CANDIDATE, P2A NO_TRADE: 8
- T7 NO_TRADE, P2A CANDIDATE: 0

## Caveats

- **SL-first on wide candles:** If both SL and TP are hit in one M15 candle, SL wins (conservative bias).
- **No spread simulation:** Entry prices are AI-quoted, no spread added.
- **No tick data:** Outcome determined by M15 OHLC only, not intra-candle sequence.
- **KB context empty:** Production passes last-10-trade context; simulation does not.
