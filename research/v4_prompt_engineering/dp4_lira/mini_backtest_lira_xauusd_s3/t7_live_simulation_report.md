# T7 Production-Faithful Simulation Report
**Dates:** 2026-01-28 to 2026-02-09
**Total KZ candles:** 270
**Total API cost:** $1.17
**Batch reference:** T7: CR=86.7%, WR=66.3%, +39.5R (n=121, no L2); P2A v1: CR=38%, WR=69.6% (n=104)

**Production gates simulated:** prescreen, deterministic bias, skip_first_ny,
L2 verification, inverted TP auto-correction, max 2 trades/day, max 1 trade/KZ.

## Summary by Instrument

| Symbol | KZ Candles | API Calls | T7 CAND | L2 Reject | Limit Block | Final Trades | CR (raw) | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|--------|-----------|-----------|---------|-----------|-------------|-------------|----------|-----------|------|--------|----|---------|-----------|
| XAUUSD   |       270 |        38 |      21 |         0 |          16 |           5 |    55.3% |     13.2% |    3 |      2 |  60% |   +2.5R | +0.500R |

## Pipeline Funnel

- Total KZ candles: 270
- Skipped (prescreen D1/H4): 25
- Skipped (no bias): 0
- Skipped (OB proximity): 198
- Skipped (first NY candle): 9
- Sent to API: 38
- AI returned CANDIDATE: 21 (raw CR: 55.3%)
  - Inverted TP corrected: 0
  - L2 Rejected: 0
  - PA parse failed → NO_TRADE: 0 (production would retry then reject)
  - Blocked by trade limits: 16
- **Final CANDIDATE decisions: 5** (live CR: 13.2%)

## Monthly Breakdown

| Month | API Calls | Raw CAND | Final Trades | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|-------|-----------|----------|-------------|-----------|------|--------|----|---------|-----------|
| 2026-01 |        11 |        9 |           2 |     18.2% |    0 |      2 |   0% |   -2.0R | -1.000R |
| 2026-02 |        27 |       12 |           3 |     11.1% |    3 |      0 | 100% |   +4.5R | +1.500R |

## Risk Metrics

- Total resolved trades: 5
- Win rate: 60.0%
- Expectancy per trade: +0.500R
- Total R: +2.5R
- Max consecutive losses: 2
- Max drawdown: 2.0R
- Trades per week: 2.7
- Trades per month: 5.0

## Trade Distribution

- London: 3 (60%)
- NY: 2 (40%)
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
- API calls: 11 | Trades: 2 | L2 rejected: 0 | Limit blocked: 7
  - london 2026-01-30T08:00 → LONG entry=5094.12 SL=5068.83 TP1=5132.11 → **LOSS** -1.0R
  - ny 2026-01-30T13:15 → LONG entry=4832.49 SL=4796.07 TP1=4887.12 → **LOSS** -1.0R

### 2026-02-02
- API calls: 3 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-03
- API calls: 11 | Trades: 2 | L2 rejected: 0 | Limit blocked: 9
  - london 2026-02-03T08:00 → LONG entry=4824.97 SL=4799.09 TP1=4863.79 → **WIN** 1.5R
  - ny 2026-02-03T14:00 → LONG entry=4824.97 SL=4800.15 TP1=4862.19 → **WIN** 1.5R

### 2026-02-04
- API calls: 3 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-05
- API calls: 1 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-06
- API calls: 9 | Trades: 1 | L2 rejected: 0 | Limit blocked: 0
  - london 2026-02-06T07:15 → LONG entry=4831.50 SL=4804.52 TP1=4872.00 → **WIN** 1.5R

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
