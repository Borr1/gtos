# T7 Production-Faithful Simulation Report
**Dates:** 2026-03-03 to 2026-03-22
**Total KZ candles:** 102
**Total API cost:** $4.03
**Batch reference:** T7: CR=86.7%, WR=66.3%, +39.5R (n=121, no L2); P2A v1: CR=38%, WR=69.6% (n=104)

**Production gates simulated:** prescreen, deterministic bias, skip_first_ny,
L2 verification, inverted TP auto-correction, max 2 trades/day, max 1 trade/KZ.

## Summary by Instrument

| Symbol | KZ Candles | API Calls | T7 CAND | L2 Reject | Limit Block | Final Trades | CR (raw) | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|--------|-----------|-----------|---------|-----------|-------------|-------------|----------|-----------|------|--------|----|---------|-----------|
| UK100    |       102 |        68 |      42 |        10 |          29 |           3 |    61.8% |      4.4% |    0 |      3 |   0% |   -3.0R | -1.000R |

## Pipeline Funnel

- Total KZ candles: 102
- Skipped (prescreen D1/H4): 0
- Skipped (no bias): 0
- Skipped (OB proximity): 34
- Skipped (first NY candle): 0
- Sent to API: 68
- AI returned CANDIDATE: 42 (raw CR: 61.8%)
  - Inverted TP corrected: 0
  - L2 Rejected: 10
  - PA parse failed → NO_TRADE: 0 (production would retry then reject)
  - Blocked by trade limits: 29
- **Final CANDIDATE decisions: 3** (live CR: 4.4%)

## Monthly Breakdown

| Month | API Calls | Raw CAND | Final Trades | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|-------|-----------|----------|-------------|-----------|------|--------|----|---------|-----------|
| 2026-03 |        68 |       42 |           3 |      4.4% |    0 |      3 |   0% |   -3.0R | -1.000R |

## Risk Metrics

- Total resolved trades: 3
- Win rate: 0.0%
- Expectancy per trade: -1.000R
- Total R: -3.0R
- Max consecutive losses: 3
- Max drawdown: 3.0R
- Trades per week: 1.1
- Trades per month: 3.0

## Trade Distribution

- London: 1 (33%)
- NY: 2 (67%)
- LONG: 3 (100%)
- SHORT: 0 (0%)

## Day-by-Day Detail

### 2026-03-03
- API calls: 18 | Trades: 0 | L2 rejected: 10 | Limit blocked: 0

### 2026-03-04
- API calls: 20 | Trades: 1 | L2 rejected: 0 | Limit blocked: 18
  - ny 2026-03-04T14:00 → LONG entry=10513.00 SL=10435.40 TP1=10629.40 → **LOSS** -1.0R

### 2026-03-05
- API calls: 30 | Trades: 2 | L2 rejected: 0 | Limit blocked: 11
  - london 2026-03-05T08:15 → LONG entry=10513.00 SL=10437.60 TP1=10626.10 → **LOSS** -1.0R
  - ny 2026-03-05T14:30 → LONG entry=10513.00 SL=10437.10 TP1=10627.30 → **LOSS** -1.0R

## T7 vs P2A v1 Decision Comparison

- Both CANDIDATE: 0
- T7 CANDIDATE, P2A NO_TRADE: 3
- T7 NO_TRADE, P2A CANDIDATE: 0

## Caveats

- **SL-first on wide candles:** If both SL and TP are hit in one M15 candle, SL wins (conservative bias).
- **No spread simulation:** Entry prices are AI-quoted, no spread added.
- **No tick data:** Outcome determined by M15 OHLC only, not intra-candle sequence.
- **KB context empty:** Production passes last-10-trade context; simulation does not.
