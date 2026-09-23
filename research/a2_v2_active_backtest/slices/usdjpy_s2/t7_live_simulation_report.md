# T7 Production-Faithful Simulation Report
**Dates:** 2026-01-27 to 2026-02-20
**Total KZ candles:** 290
**Total API cost:** $6.04
**Batch reference:** T7: CR=86.7%, WR=66.3%, +39.5R (n=121, no L2); P2A v1: CR=38%, WR=69.6% (n=104)

**Production gates simulated:** prescreen, deterministic bias, skip_first_ny,
L2 verification, inverted TP auto-correction, max 2 trades/day, max 1 trade/KZ.

## Summary by Instrument

| Symbol | KZ Candles | API Calls | T7 CAND | L2 Reject | Limit Block | Final Trades | CR (raw) | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|--------|-----------|-----------|---------|-----------|-------------|-------------|----------|-----------|------|--------|----|---------|-----------|
| USDJPY   |       290 |       142 |     126 |        78 |          42 |           6 |    88.7% |      4.2% |    5 |      1 |  83% |   +6.5R | +1.083R |

## Pipeline Funnel

- Total KZ candles: 290
- Skipped (prescreen D1/H4): 128
- Skipped (no bias): 0
- Skipped (OB proximity): 20
- Skipped (first NY candle): 0
- Sent to API: 142
- AI returned CANDIDATE: 126 (raw CR: 88.7%)
  - Inverted TP corrected: 0
  - L2 Rejected: 78
  - PA parse failed → NO_TRADE: 0 (production would retry then reject)
  - Blocked by trade limits: 42
- **Final CANDIDATE decisions: 6** (live CR: 4.2%)

## Monthly Breakdown

| Month | API Calls | Raw CAND | Final Trades | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|-------|-----------|----------|-------------|-----------|------|--------|----|---------|-----------|
| 2026-01 |        12 |        1 |           0 |      0.0% |    0 |      0 |   0% |   +0.0R | +0.000R |
| 2026-02 |       130 |      125 |           6 |      4.6% |    5 |      1 |  83% |   +6.5R | +1.083R |

## Risk Metrics

- Total resolved trades: 6
- Win rate: 83.3%
- Expectancy per trade: +1.083R
- Total R: +6.5R
- Max consecutive losses: 1
- Max drawdown: 1.0R
- Trades per week: 1.7
- Trades per month: 6.0

## Trade Distribution

- London: 3 (50%)
- NY: 1 (17%)
- LONG: 6 (100%)
- SHORT: 0 (0%)

## Day-by-Day Detail

### 2026-01-27
- API calls: 12 | Trades: 0 | L2 rejected: 1 | Limit blocked: 0

### 2026-01-28
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-01-29
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-01-30
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-02
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-03
- API calls: 32 | Trades: 0 | L2 rejected: 32 | Limit blocked: 0

### 2026-02-04
- API calls: 32 | Trades: 2 | L2 rejected: 20 | Limit blocked: 10
  - london 2026-02-04T09:00 → LONG entry=156.36 SL=156.19 TP1=156.62 → **WIN** 1.5R
  - ny 2026-02-04T13:00 → LONG entry=156.36 SL=156.19 TP1=156.62 → **WIN** 1.5R

### 2026-02-05
- API calls: 32 | Trades: 2 | L2 rejected: 8 | Limit blocked: 20
  - tokyo 2026-02-05T00:00 → LONG entry=156.74 SL=156.31 TP1=157.39 → **WIN** 1.5R
  - london 2026-02-05T07:15 → LONG entry=155.52 SL=155.25 TP1=155.92 → **WIN** 1.5R

### 2026-02-06
- API calls: 32 | Trades: 2 | L2 rejected: 17 | Limit blocked: 12
  - tokyo 2026-02-06T00:45 → LONG entry=155.81 SL=155.59 TP1=156.14 → **LOSS** -1.0R
  - london 2026-02-06T07:00 → LONG entry=155.52 SL=155.25 TP1=155.93 → **WIN** 1.5R

### 2026-02-09
- API calls: 2 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
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
