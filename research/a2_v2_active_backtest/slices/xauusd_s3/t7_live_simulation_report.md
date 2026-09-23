# T7 Production-Faithful Simulation Report
**Dates:** 2026-01-28 to 2026-02-09
**Total KZ candles:** 270
**Total API cost:** $1.70
**Batch reference:** T7: CR=86.7%, WR=66.3%, +39.5R (n=121, no L2); P2A v1: CR=38%, WR=69.6% (n=104)

**Production gates simulated:** prescreen, deterministic bias, skip_first_ny,
L2 verification, inverted TP auto-correction, max 2 trades/day, max 1 trade/KZ.

## Summary by Instrument

| Symbol | KZ Candles | API Calls | T7 CAND | L2 Reject | Limit Block | Final Trades | CR (raw) | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|--------|-----------|-----------|---------|-----------|-------------|-------------|----------|-----------|------|--------|----|---------|-----------|
| XAUUSD   |       270 |        38 |      25 |         5 |          15 |           5 |    65.8% |     13.2% |    3 |      2 |  60% |   +2.5R | +0.500R |

## Pipeline Funnel

- Total KZ candles: 270
- Skipped (prescreen D1/H4): 25
- Skipped (no bias): 0
- Skipped (OB proximity): 198
- Skipped (first NY candle): 9
- Sent to API: 38
- AI returned CANDIDATE: 25 (raw CR: 65.8%)
  - Inverted TP corrected: 0
  - L2 Rejected: 5
  - PA parse failed → NO_TRADE: 0 (production would retry then reject)
  - Blocked by trade limits: 15
- **Final CANDIDATE decisions: 5** (live CR: 13.2%)

## Monthly Breakdown

| Month | API Calls | Raw CAND | Final Trades | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|-------|-----------|----------|-------------|-----------|------|--------|----|---------|-----------|
| 2026-01 |        11 |       10 |           2 |     18.2% |    1 |      1 |  50% |   +0.5R | +0.250R |
| 2026-02 |        27 |       15 |           3 |     11.1% |    2 |      1 |  67% |   +2.0R | +0.667R |

## Risk Metrics

- Total resolved trades: 5
- Win rate: 60.0%
- Expectancy per trade: +0.500R
- Total R: +2.5R
- Max consecutive losses: 1
- Max drawdown: 1.0R
- Trades per week: 2.7
- Trades per month: 5.0

## Trade Distribution

- London: 2 (40%)
- NY: 3 (60%)
- LONG: 5 (100%)
- SHORT: 0 (0%)

## Day-by-Day Detail

### 2026-01-28
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-01-29
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-01-30
- API calls: 11 | Trades: 2 | L2 rejected: 2 | Limit blocked: 6
  - london 2026-01-30T08:00 → LONG entry=5094.12 SL=5056.33 TP1=5150.84 → **WIN** 1.5R
  - ny 2026-01-30T13:15 → LONG entry=4832.49 SL=4796.07 TP1=4887.12 → **LOSS** -1.0R

### 2026-02-02
- API calls: 3 | Trades: 0 | L2 rejected: 2 | Limit blocked: 0

### 2026-02-03
- API calls: 11 | Trades: 2 | L2 rejected: 0 | Limit blocked: 9
  - london 2026-02-03T08:00 → LONG entry=4824.97 SL=4779.52 TP1=4893.19 → **WIN** 1.5R
  - ny 2026-02-03T14:00 → LONG entry=4824.97 SL=4787.27 TP1=4881.52 → **WIN** 1.5R

### 2026-02-04
- API calls: 3 | Trades: 1 | L2 rejected: 0 | Limit blocked: 0
  - ny 2026-02-04T13:30 → LONG entry=4957.40 SL=4898.63 TP1=5045.52 → **LOSS** -1.0R

### 2026-02-05
- API calls: 1 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-06
- API calls: 9 | Trades: 0 | L2 rejected: 1 | Limit blocked: 0

### 2026-02-09
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
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
