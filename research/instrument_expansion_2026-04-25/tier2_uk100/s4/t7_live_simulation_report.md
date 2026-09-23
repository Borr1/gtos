# T7 Production-Faithful Simulation Report
**Dates:** 2026-02-16 to 2026-03-02
**Total KZ candles:** 70
**Total API cost:** $4.05
**Batch reference:** T7: CR=86.7%, WR=66.3%, +39.5R (n=121, no L2); P2A v1: CR=38%, WR=69.6% (n=104)

**Production gates simulated:** prescreen, deterministic bias, skip_first_ny,
L2 verification, inverted TP auto-correction, max 2 trades/day, max 1 trade/KZ.

## Summary by Instrument

| Symbol | KZ Candles | API Calls | T7 CAND | L2 Reject | Limit Block | Final Trades | CR (raw) | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|--------|-----------|-----------|---------|-----------|-------------|-------------|----------|-----------|------|--------|----|---------|-----------|
| UK100    |        70 |        70 |      66 |         0 |          62 |           4 |    94.3% |      5.7% |    4 |      0 | 100% |   +6.0R | +1.500R |

## Pipeline Funnel

- Total KZ candles: 70
- Skipped (prescreen D1/H4): 0
- Skipped (no bias): 0
- Skipped (OB proximity): 0
- Skipped (first NY candle): 0
- Sent to API: 70
- AI returned CANDIDATE: 66 (raw CR: 94.3%)
  - Inverted TP corrected: 0
  - L2 Rejected: 0
  - PA parse failed → NO_TRADE: 0 (production would retry then reject)
  - Blocked by trade limits: 62
- **Final CANDIDATE decisions: 4** (live CR: 5.7%)

## Monthly Breakdown

| Month | API Calls | Raw CAND | Final Trades | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|-------|-----------|----------|-------------|-----------|------|--------|----|---------|-----------|
| 2026-02 |        70 |       66 |           4 |      5.7% |    4 |      0 | 100% |   +6.0R | +1.500R |

## Risk Metrics

- Total resolved trades: 4
- Win rate: 100.0%
- Expectancy per trade: +1.500R
- Total R: +6.0R
- Max consecutive losses: 0
- Max drawdown: 0.0R
- Trades per week: 1.9
- Trades per month: 4.0

## Trade Distribution

- London: 2 (50%)
- NY: 2 (50%)
- LONG: 4 (100%)
- SHORT: 0 (0%)

## Day-by-Day Detail

### 2026-02-16
- API calls: 36 | Trades: 2 | L2 rejected: 0 | Limit blocked: 31
  - london 2026-02-16T08:00 → LONG entry=10416.70 SL=10371.90 TP1=10483.80 → **WIN** 1.5R
  - ny 2026-02-16T14:00 → LONG entry=10416.70 SL=10372.10 TP1=10483.60 → **WIN** 1.5R

### 2026-02-17
- API calls: 34 | Trades: 2 | L2 rejected: 0 | Limit blocked: 31
  - london 2026-02-17T08:00 → LONG entry=10416.70 SL=10373.20 TP1=10481.90 → **WIN** 1.5R
  - ny 2026-02-17T14:00 → LONG entry=10460.20 SL=10437.20 TP1=10494.70 → **WIN** 1.5R

## T7 vs P2A v1 Decision Comparison

- Both CANDIDATE: 0
- T7 CANDIDATE, P2A NO_TRADE: 4
- T7 NO_TRADE, P2A CANDIDATE: 0

## Caveats

- **SL-first on wide candles:** If both SL and TP are hit in one M15 candle, SL wins (conservative bias).
- **No spread simulation:** Entry prices are AI-quoted, no spread added.
- **No tick data:** Outcome determined by M15 OHLC only, not intra-candle sequence.
- **KB context empty:** Production passes last-10-trade context; simulation does not.
