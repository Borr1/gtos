# T7 Production-Faithful Simulation Report
**Dates:** 2026-04-14 to 2026-04-24
**Total KZ candles:** 81
**Total API cost:** $4.06
**Batch reference:** T7: CR=86.7%, WR=66.3%, +39.5R (n=121, no L2); P2A v1: CR=38%, WR=69.6% (n=104)

**Production gates simulated:** prescreen, deterministic bias, skip_first_ny,
L2 verification, inverted TP auto-correction, max 2 trades/day, max 1 trade/KZ.

## Summary by Instrument

| Symbol | KZ Candles | API Calls | T7 CAND | L2 Reject | Limit Block | Final Trades | CR (raw) | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|--------|-----------|-----------|---------|-----------|-------------|-------------|----------|-----------|------|--------|----|---------|-----------|
| GER40    |        81 |        69 |      63 |         0 |          57 |           6 |    91.3% |      8.7% |    6 |      0 | 100% |   +9.0R | +1.505R |

## Pipeline Funnel

- Total KZ candles: 81
- Skipped (prescreen D1/H4): 0
- Skipped (no bias): 0
- Skipped (OB proximity): 12
- Skipped (first NY candle): 0
- Sent to API: 69
- AI returned CANDIDATE: 63 (raw CR: 91.3%)
  - Inverted TP corrected: 0
  - L2 Rejected: 0
  - PA parse failed → NO_TRADE: 0 (production would retry then reject)
  - Blocked by trade limits: 57
- **Final CANDIDATE decisions: 6** (live CR: 8.7%)

## Monthly Breakdown

| Month | API Calls | Raw CAND | Final Trades | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|-------|-----------|----------|-------------|-----------|------|--------|----|---------|-----------|
| 2026-04 |        69 |       63 |           6 |      8.7% |    6 |      0 | 100% |   +9.0R | +1.505R |

## Risk Metrics

- Total resolved trades: 6
- Win rate: 100.0%
- Expectancy per trade: +1.505R
- Total R: +9.0R
- Max consecutive losses: 0
- Max drawdown: 0.0R
- Trades per week: 3.8
- Trades per month: 6.0

## Trade Distribution

- London: 3 (50%)
- NY: 3 (50%)
- LONG: 6 (100%)
- SHORT: 0 (0%)

## Day-by-Day Detail

### 2026-04-14
- API calls: 18 | Trades: 2 | L2 rejected: 0 | Limit blocked: 15
  - london 2026-04-14T10:00 → LONG entry=23893.60 SL=23860.20 TP1=23944.70 → **WIN** 1.53R
  - ny 2026-04-14T13:00 → LONG entry=23893.60 SL=23859.40 TP1=23944.90 → **WIN** 1.5R

### 2026-04-15
- API calls: 30 | Trades: 2 | L2 rejected: 0 | Limit blocked: 25
  - london 2026-04-15T07:00 → LONG entry=23893.60 SL=23851.50 TP1=23956.80 → **WIN** 1.5R
  - ny 2026-04-15T13:00 → LONG entry=23893.60 SL=23861.50 TP1=23941.70 → **WIN** 1.5R

### 2026-04-16
- API calls: 21 | Trades: 2 | L2 rejected: 0 | Limit blocked: 17
  - london 2026-04-16T07:00 → LONG entry=24076.90 SL=24039.90 TP1=24132.40 → **WIN** 1.5R
  - ny 2026-04-16T13:00 → LONG entry=24157.20 SL=24043.40 TP1=24327.90 → **WIN** 1.5R

## T7 vs P2A v1 Decision Comparison

- Both CANDIDATE: 0
- T7 CANDIDATE, P2A NO_TRADE: 6
- T7 NO_TRADE, P2A CANDIDATE: 0

## Caveats

- **SL-first on wide candles:** If both SL and TP are hit in one M15 candle, SL wins (conservative bias).
- **No spread simulation:** Entry prices are AI-quoted, no spread added.
- **No tick data:** Outcome determined by M15 OHLC only, not intra-candle sequence.
- **KB context empty:** Production passes last-10-trade context; simulation does not.
