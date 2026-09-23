# T7 Production-Faithful Simulation Report
**Dates:** 2026-03-03 to 2026-03-22
**Total KZ candles:** 188
**Total API cost:** $4.00
**Batch reference:** T7: CR=86.7%, WR=66.3%, +39.5R (n=121, no L2); P2A v1: CR=38%, WR=69.6% (n=104)

**Production gates simulated:** prescreen, deterministic bias, skip_first_ny,
L2 verification, inverted TP auto-correction, max 2 trades/day, max 1 trade/KZ.

## Summary by Instrument

| Symbol | KZ Candles | API Calls | T7 CAND | L2 Reject | Limit Block | Final Trades | CR (raw) | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|--------|-----------|-----------|---------|-----------|-------------|-------------|----------|-----------|------|--------|----|---------|-----------|
| GER40    |       188 |        67 |      47 |         1 |          38 |           8 |    70.1% |     11.9% |    0 |      8 |   0% |   -8.0R | -1.000R |

## Pipeline Funnel

- Total KZ candles: 188
- Skipped (prescreen D1/H4): 0
- Skipped (no bias): 0
- Skipped (OB proximity): 121
- Skipped (first NY candle): 0
- Sent to API: 67
- AI returned CANDIDATE: 47 (raw CR: 70.1%)
  - Inverted TP corrected: 0
  - L2 Rejected: 1
  - PA parse failed → NO_TRADE: 0 (production would retry then reject)
  - Blocked by trade limits: 38
- **Final CANDIDATE decisions: 8** (live CR: 11.9%)

## Monthly Breakdown

| Month | API Calls | Raw CAND | Final Trades | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|-------|-----------|----------|-------------|-----------|------|--------|----|---------|-----------|
| 2026-03 |        67 |       47 |           8 |     11.9% |    0 |      8 |   0% |   -8.0R | -1.000R |

## Risk Metrics

- Total resolved trades: 8
- Win rate: 0.0%
- Expectancy per trade: -1.000R
- Total R: -8.0R
- Max consecutive losses: 8
- Max drawdown: 8.0R
- Trades per week: 2.8
- Trades per month: 8.0

## Trade Distribution

- London: 4 (50%)
- NY: 4 (50%)
- LONG: 6 (75%)
- SHORT: 2 (25%)

## Day-by-Day Detail

### 2026-03-03
- API calls: 9 | Trades: 1 | L2 rejected: 1 | Limit blocked: 1
  - london 2026-03-03T08:00 → SHORT entry=24558.30 SL=24664.70 TP1=24399.00 → **LOSS** -1.0R

### 2026-03-04
- API calls: 13 | Trades: 1 | L2 rejected: 0 | Limit blocked: 12
  - ny 2026-03-04T13:00 → LONG entry=23948.40 SL=23779.30 TP1=24201.90 → **LOSS** -1.0R

### 2026-03-05
- API calls: 19 | Trades: 2 | L2 rejected: 0 | Limit blocked: 14
  - london 2026-03-05T07:00 → LONG entry=23948.40 SL=23787.70 TP1=24189.00 → **LOSS** -1.0R
  - ny 2026-03-05T14:45 → LONG entry=23948.40 SL=23785.60 TP1=24192.70 → **LOSS** -1.0R

### 2026-03-06
- API calls: 11 | Trades: 1 | L2 rejected: 0 | Limit blocked: 0
  - ny 2026-03-06T14:00 → SHORT entry=23881.70 SL=23911.10 TP1=23837.50 → **LOSS** -1.0R

### 2026-03-09
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-03-10
- API calls: 14 | Trades: 2 | L2 rejected: 0 | Limit blocked: 11
  - london 2026-03-10T07:00 → LONG entry=23459.00 SL=23271.40 TP1=23740.60 → **LOSS** -1.0R
  - ny 2026-03-10T15:15 → LONG entry=23636.50 SL=23486.80 TP1=23861.20 → **LOSS** -1.0R

### 2026-03-11
- API calls: 1 | Trades: 1 | L2 rejected: 0 | Limit blocked: 0
  - london 2026-03-11T08:45 → LONG entry=23636.50 SL=23495.40 TP1=23848.20 → **LOSS** -1.0R

## T7 vs P2A v1 Decision Comparison

- Both CANDIDATE: 0
- T7 CANDIDATE, P2A NO_TRADE: 8
- T7 NO_TRADE, P2A CANDIDATE: 0

## Caveats

- **SL-first on wide candles:** If both SL and TP are hit in one M15 candle, SL wins (conservative bias).
- **No spread simulation:** Entry prices are AI-quoted, no spread added.
- **No tick data:** Outcome determined by M15 OHLC only, not intra-candle sequence.
- **KB context empty:** Production passes last-10-trade context; simulation does not.
