# T7 Production-Faithful Simulation Report
**Dates:** 2026-01-28 to 2026-02-09
**Total KZ candles:** 270
**Total API cost:** $1.73
**Batch reference:** T7: CR=86.7%, WR=66.3%, +39.5R (n=121, no L2); P2A v1: CR=38%, WR=69.6% (n=104)

**Production gates simulated:** prescreen, deterministic bias, skip_first_ny,
L2 verification, inverted TP auto-correction, max 2 trades/day, max 1 trade/KZ.

## Summary by Instrument

| Symbol | KZ Candles | API Calls | T7 CAND | L2 Reject | Limit Block | Final Trades | CR (raw) | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|--------|-----------|-----------|---------|-----------|-------------|-------------|----------|-----------|------|--------|----|---------|-----------|
| XAUUSD   |       270 |        38 |      24 |         6 |          12 |           6 |    63.2% |     15.8% |    3 |      3 |  50% |   +1.5R | +0.250R |

## Pipeline Funnel

- Total KZ candles: 270
- Skipped (prescreen D1/H4): 25
- Skipped (no bias): 0
- Skipped (OB proximity): 198
- Skipped (first NY candle): 9
- Sent to API: 38
- AI returned CANDIDATE: 24 (raw CR: 63.2%)
  - Inverted TP corrected: 1
  - L2 Rejected: 6
  - PA parse failed → NO_TRADE: 0 (production would retry then reject)
  - Blocked by trade limits: 12
- **Final CANDIDATE decisions: 6** (live CR: 15.8%)

## Monthly Breakdown

| Month | API Calls | Raw CAND | Final Trades | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|-------|-----------|----------|-------------|-----------|------|--------|----|---------|-----------|
| 2026-01 |        11 |        9 |           2 |     18.2% |    1 |      1 |  50% |   +0.5R | +0.250R |
| 2026-02 |        27 |       15 |           4 |     14.8% |    2 |      2 |  50% |   +1.0R | +0.250R |

## Risk Metrics

- Total resolved trades: 6
- Win rate: 50.0%
- Expectancy per trade: +0.250R
- Total R: +1.5R
- Max consecutive losses: 2
- Max drawdown: 2.0R
- Trades per week: 3.2
- Trades per month: 6.0

## Trade Distribution

- London: 3 (50%)
- NY: 3 (50%)
- LONG: 5 (83%)
- SHORT: 1 (17%)

## Day-by-Day Detail

### 2026-01-28
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-01-29
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-01-30
- API calls: 11 | Trades: 2 | L2 rejected: 4 | Limit blocked: 3
  - london 2026-01-30T08:00 → LONG entry=5094.12 SL=5056.33 TP1=5150.81 → **WIN** 1.5R
  - ny 2026-01-30T13:45 → LONG entry=4832.49 SL=4810.29 TP1=4865.79 → **LOSS** -1.0R

### 2026-02-02
- API calls: 3 | Trades: 1 | L2 rejected: 2 | Limit blocked: 0
  - london 2026-02-02T07:30 → SHORT entry=4603.47 SL=4743.26 TP1=4393.78 → **LOSS** -1.0R

### 2026-02-03
- API calls: 11 | Trades: 2 | L2 rejected: 0 | Limit blocked: 9
  - london 2026-02-03T08:00 → LONG entry=4824.97 SL=4795.00 TP1=4869.92 → **WIN** 1.5R
  - ny 2026-02-03T14:00 → LONG entry=4824.97 SL=4787.58 TP1=4881.04 → **WIN** 1.5R

### 2026-02-04
- API calls: 3 | Trades: 1 | L2 rejected: 0 | Limit blocked: 0
  - ny 2026-02-04T13:45 → LONG entry=4957.40 SL=4898.62 TP1=5045.57 → **LOSS** -1.0R [inverted→corrected]

### 2026-02-05
- API calls: 1 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-06
- API calls: 9 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-09
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

## T7 vs P2A v1 Decision Comparison

- Both CANDIDATE: 0
- T7 CANDIDATE, P2A NO_TRADE: 6
- T7 NO_TRADE, P2A CANDIDATE: 0

## Caveats

- **SL-first on wide candles:** If both SL and TP are hit in one M15 candle, SL wins (conservative bias).
- **No spread simulation:** Entry prices are AI-quoted, no spread added.
- **No tick data:** Outcome determined by M15 OHLC only, not intra-candle sequence.
- **KB context empty:** Production passes last-10-trade context; simulation does not.
