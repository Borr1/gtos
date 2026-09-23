# T7 Production-Faithful Simulation Report
**Dates:** 2026-03-03 to 2026-03-22
**Total KZ candles:** 110
**Total API cost:** $4.02
**Batch reference:** T7: CR=86.7%, WR=66.3%, +39.5R (n=121, no L2); P2A v1: CR=38%, WR=69.6% (n=104)

**Production gates simulated:** prescreen, deterministic bias, skip_first_ny,
L2 verification, inverted TP auto-correction, max 2 trades/day, max 1 trade/KZ.

## Summary by Instrument

| Symbol | KZ Candles | API Calls | T7 CAND | L2 Reject | Limit Block | Final Trades | CR (raw) | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|--------|-----------|-----------|---------|-----------|-------------|-------------|----------|-----------|------|--------|----|---------|-----------|
| NAS100   |       110 |        69 |      54 |         2 |          46 |           6 |    78.3% |      8.7% |    5 |      1 |  83% |   +6.5R | +1.083R |

## Pipeline Funnel

- Total KZ candles: 110
- Skipped (prescreen D1/H4): 0
- Skipped (no bias): 0
- Skipped (OB proximity): 41
- Skipped (first NY candle): 0
- Sent to API: 69
- AI returned CANDIDATE: 54 (raw CR: 78.3%)
  - Inverted TP corrected: 0
  - L2 Rejected: 2
  - PA parse failed → NO_TRADE: 0 (production would retry then reject)
  - Blocked by trade limits: 46
- **Final CANDIDATE decisions: 6** (live CR: 8.7%)

## Monthly Breakdown

| Month | API Calls | Raw CAND | Final Trades | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|-------|-----------|----------|-------------|-----------|------|--------|----|---------|-----------|
| 2026-03 |        69 |       54 |           6 |      8.7% |    5 |      1 |  83% |   +6.5R | +1.083R |

## Risk Metrics

- Total resolved trades: 6
- Win rate: 83.3%
- Expectancy per trade: +1.083R
- Total R: +6.5R
- Max consecutive losses: 1
- Max drawdown: 1.0R
- Trades per week: 2.1
- Trades per month: 6.0

## Trade Distribution

- London: 3 (50%)
- NY: 3 (50%)
- LONG: 6 (100%)
- SHORT: 0 (0%)

## Day-by-Day Detail

### 2026-03-03
- API calls: 14 | Trades: 1 | L2 rejected: 2 | Limit blocked: 6
  - london 2026-03-03T07:00 → LONG entry=24699.40 SL=24531.70 TP1=24950.70 → **LOSS** -1.0R

### 2026-03-04
- API calls: 16 | Trades: 1 | L2 rejected: 0 | Limit blocked: 15
  - ny 2026-03-04T13:00 → LONG entry=24652.20 SL=24546.70 TP1=24810.50 → **WIN** 1.5R

### 2026-03-05
- API calls: 21 | Trades: 2 | L2 rejected: 0 | Limit blocked: 16
  - london 2026-03-05T07:00 → LONG entry=24652.20 SL=24526.90 TP1=24840.00 → **WIN** 1.5R
  - ny 2026-03-05T13:00 → LONG entry=24652.20 SL=24551.90 TP1=24802.70 → **WIN** 1.5R

### 2026-03-06
- API calls: 18 | Trades: 2 | L2 rejected: 0 | Limit blocked: 9
  - london 2026-03-06T07:00 → LONG entry=24652.20 SL=24551.70 TP1=24803.00 → **WIN** 1.5R
  - ny 2026-03-06T14:15 → LONG entry=24652.20 SL=24551.80 TP1=24803.00 → **WIN** 1.5R

## T7 vs P2A v1 Decision Comparison

- Both CANDIDATE: 0
- T7 CANDIDATE, P2A NO_TRADE: 6
- T7 NO_TRADE, P2A CANDIDATE: 0

## Caveats

- **SL-first on wide candles:** If both SL and TP are hit in one M15 candle, SL wins (conservative bias).
- **No spread simulation:** Entry prices are AI-quoted, no spread added.
- **No tick data:** Outcome determined by M15 OHLC only, not intra-candle sequence.
- **KB context empty:** Production passes last-10-trade context; simulation does not.
