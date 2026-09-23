# T7 Production-Faithful Simulation Report
**Dates:** 2026-01-28 to 2026-02-09
**Total KZ candles:** 270
**Total API cost:** $0.82
**Batch reference:** T7: CR=86.7%, WR=66.3%, +39.5R (n=121, no L2); P2A v1: CR=38%, WR=69.6% (n=104)

**Production gates simulated:** prescreen, deterministic bias, skip_first_ny,
L2 verification, inverted TP auto-correction, max 2 trades/day, max 1 trade/KZ.

## Summary by Instrument

| Symbol | KZ Candles | API Calls | T7 CAND | L2 Reject | Limit Block | Final Trades | CR (raw) | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|--------|-----------|-----------|---------|-----------|-------------|-------------|----------|-----------|------|--------|----|---------|-----------|
| XAUUSD   |       270 |        38 |      24 |        14 |           7 |           3 |    63.2% |      7.9% |    0 |      3 |   0% |   -3.0R | -1.000R |

## Pipeline Funnel

- Total KZ candles: 270
- Skipped (prescreen D1/H4): 25
- Skipped (no bias): 0
- Skipped (OB proximity): 198
- Skipped (first NY candle): 9
- Sent to API: 38
- AI returned CANDIDATE: 24 (raw CR: 63.2%)
  - Inverted TP corrected: 0
  - L2 Rejected: 14
  - PA parse failed → NO_TRADE: 0 (production would retry then reject)
  - Blocked by trade limits: 7
- **Final CANDIDATE decisions: 3** (live CR: 7.9%)

## Monthly Breakdown

| Month | API Calls | Raw CAND | Final Trades | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|-------|-----------|----------|-------------|-----------|------|--------|----|---------|-----------|
| 2026-01 |        11 |        8 |           2 |     18.2% |    0 |      2 |   0% |   -2.0R | -1.000R |
| 2026-02 |        27 |       16 |           1 |      3.7% |    0 |      1 |   0% |   -1.0R | -1.000R |

## Risk Metrics

- Total resolved trades: 3
- Win rate: 0.0%
- Expectancy per trade: -1.000R
- Total R: -3.0R
- Max consecutive losses: 3
- Max drawdown: 3.0R
- Trades per week: 1.6
- Trades per month: 3.0

## Trade Distribution

- London: 2 (67%)
- NY: 1 (33%)
- LONG: 3 (100%)
- SHORT: 0 (0%)

## Day-by-Day Detail

### 2026-01-28
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-01-29
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-01-30
- API calls: 11 | Trades: 2 | L2 rejected: 0 | Limit blocked: 6
  - london 2026-01-30T08:00 → LONG entry=5094.12 SL=5061.47 TP1=5143.35 → **LOSS** -1.0R
  - ny 2026-01-30T13:15 → LONG entry=4832.49 SL=4809.57 TP1=4866.84 → **LOSS** -1.0R

### 2026-02-02
- API calls: 3 | Trades: 0 | L2 rejected: 1 | Limit blocked: 0

### 2026-02-03
- API calls: 11 | Trades: 1 | L2 rejected: 9 | Limit blocked: 1
  - london 2026-02-03T10:00 → LONG entry=4824.97 SL=4745.35 TP1=4944.38 → **LOSS** -1.0R

### 2026-02-04
- API calls: 3 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-05
- API calls: 1 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-06
- API calls: 9 | Trades: 0 | L2 rejected: 4 | Limit blocked: 0

### 2026-02-09
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

## T7 vs P2A v1 Decision Comparison

- Both CANDIDATE: 0
- T7 CANDIDATE, P2A NO_TRADE: 3
- T7 NO_TRADE, P2A CANDIDATE: 0

## Caveats

- **SL-first on wide candles:** If both SL and TP are hit in one M15 candle, SL wins (conservative bias).
- **No spread simulation:** Entry prices are AI-quoted, no spread added.
- **No tick data:** Outcome determined by M15 OHLC only, not intra-candle sequence.
- **KB context empty:** Production passes last-10-trade context; simulation does not.
