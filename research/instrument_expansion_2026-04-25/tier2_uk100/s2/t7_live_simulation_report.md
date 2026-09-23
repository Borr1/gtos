# T7 Production-Faithful Simulation Report
**Dates:** 2026-01-16 to 2026-01-31
**Total KZ candles:** 67
**Total API cost:** $4.01
**Batch reference:** T7: CR=86.7%, WR=66.3%, +39.5R (n=121, no L2); P2A v1: CR=38%, WR=69.6% (n=104)

**Production gates simulated:** prescreen, deterministic bias, skip_first_ny,
L2 verification, inverted TP auto-correction, max 2 trades/day, max 1 trade/KZ.

## Summary by Instrument

| Symbol | KZ Candles | API Calls | T7 CAND | L2 Reject | Limit Block | Final Trades | CR (raw) | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|--------|-----------|-----------|---------|-----------|-------------|-------------|----------|-----------|------|--------|----|---------|-----------|
| UK100    |        67 |        67 |      54 |        23 |          28 |           3 |    80.6% |      4.5% |    0 |      3 |   0% |   -3.0R | -1.000R |

## Pipeline Funnel

- Total KZ candles: 67
- Skipped (prescreen D1/H4): 0
- Skipped (no bias): 0
- Skipped (OB proximity): 0
- Skipped (first NY candle): 0
- Sent to API: 67
- AI returned CANDIDATE: 54 (raw CR: 80.6%)
  - Inverted TP corrected: 0
  - L2 Rejected: 23
  - PA parse failed → NO_TRADE: 0 (production would retry then reject)
  - Blocked by trade limits: 28
- **Final CANDIDATE decisions: 3** (live CR: 4.5%)

## Monthly Breakdown

| Month | API Calls | Raw CAND | Final Trades | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|-------|-----------|----------|-------------|-----------|------|--------|----|---------|-----------|
| 2026-01 |        67 |       54 |           3 |      4.5% |    0 |      3 |   0% |   -3.0R | -1.000R |

## Risk Metrics

- Total resolved trades: 3
- Win rate: 0.0%
- Expectancy per trade: -1.000R
- Total R: -3.0R
- Max consecutive losses: 3
- Max drawdown: 3.0R
- Trades per week: 1.3
- Trades per month: 3.0

## Trade Distribution

- London: 2 (67%)
- NY: 1 (33%)
- LONG: 3 (100%)
- SHORT: 0 (0%)

## Day-by-Day Detail

### 2026-01-16
- API calls: 36 | Trades: 2 | L2 rejected: 8 | Limit blocked: 25
  - london 2026-01-16T08:00 → LONG entry=10201.70 SL=10165.60 TP1=10255.90 → **LOSS** -1.0R
  - ny 2026-01-16T15:00 → LONG entry=10201.70 SL=10161.00 TP1=10262.80 → **LOSS** -1.0R

### 2026-01-19
- API calls: 31 | Trades: 1 | L2 rejected: 15 | Limit blocked: 3
  - london 2026-01-19T10:00 → LONG entry=10189.60 SL=10168.50 TP1=10221.30 → **LOSS** -1.0R

## T7 vs P2A v1 Decision Comparison

- Both CANDIDATE: 0
- T7 CANDIDATE, P2A NO_TRADE: 3
- T7 NO_TRADE, P2A CANDIDATE: 0

## Caveats

- **SL-first on wide candles:** If both SL and TP are hit in one M15 candle, SL wins (conservative bias).
- **No spread simulation:** Entry prices are AI-quoted, no spread added.
- **No tick data:** Outcome determined by M15 OHLC only, not intra-candle sequence.
- **KB context empty:** Production passes last-10-trade context; simulation does not.
