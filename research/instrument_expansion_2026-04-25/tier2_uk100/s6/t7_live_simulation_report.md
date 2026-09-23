# T7 Production-Faithful Simulation Report
**Dates:** 2026-03-23 to 2026-04-13
**Total KZ candles:** 117
**Total API cost:** $4.02
**Batch reference:** T7: CR=86.7%, WR=66.3%, +39.5R (n=121, no L2); P2A v1: CR=38%, WR=69.6% (n=104)

**Production gates simulated:** prescreen, deterministic bias, skip_first_ny,
L2 verification, inverted TP auto-correction, max 2 trades/day, max 1 trade/KZ.

## Summary by Instrument

| Symbol | KZ Candles | API Calls | T7 CAND | L2 Reject | Limit Block | Final Trades | CR (raw) | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|--------|-----------|-----------|---------|-----------|-------------|-------------|----------|-----------|------|--------|----|---------|-----------|
| UK100    |       117 |        66 |      62 |         1 |          56 |           5 |    93.9% |      7.6% |    0 |      3 |   0% |   -3.0R | -1.000R |

## Pipeline Funnel

- Total KZ candles: 117
- Skipped (prescreen D1/H4): 0
- Skipped (no bias): 0
- Skipped (OB proximity): 51
- Skipped (first NY candle): 0
- Sent to API: 66
- AI returned CANDIDATE: 62 (raw CR: 93.9%)
  - Inverted TP corrected: 3
  - L2 Rejected: 1
  - PA parse failed → NO_TRADE: 0 (production would retry then reject)
  - Blocked by trade limits: 56
- **Final CANDIDATE decisions: 5** (live CR: 7.6%)
  - ⚠ Entry limit never filled (unfilled): 2 — excluded from WR/expectancy

## Monthly Breakdown

| Month | API Calls | Raw CAND | Final Trades | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|-------|-----------|----------|-------------|-----------|------|--------|----|---------|-----------|
| 2026-03 |        66 |       62 |           5 |      7.6% |    0 |      3 |   0% |   -3.0R | -1.000R |

## Risk Metrics

- ⚠ Unfilled (entry limit never reached): 2 — excluded from all metrics below
- Total resolved trades: 3
- Win rate: 0.0%
- Expectancy per trade: -1.000R
- Total R: -3.0R
- Max consecutive losses: 3
- Max drawdown: 3.0R
- Trades per week: 1.0
- Trades per month: 3.0

## Trade Distribution

- London: 2 (40%)
- NY: 3 (60%)
- LONG: 5 (100%)
- SHORT: 0 (0%)

## Day-by-Day Detail

### 2026-03-23
- API calls: 13 | Trades: 1 | L2 rejected: 0 | Limit blocked: 8
  - ny 2026-03-23T14:45 → LONG entry=9726.70 SL=9656.90 TP1=9831.40 → **UNFILLED** ?R

### 2026-03-24
- API calls: 8 | Trades: 1 | L2 rejected: 0 | Limit blocked: 7
  - ny 2026-03-24T17:00 → LONG entry=9726.70 SL=9659.60 TP1=9827.30 → **UNFILLED** ?R

### 2026-03-25
- API calls: 36 | Trades: 2 | L2 rejected: 0 | Limit blocked: 34
  - london 2026-03-25T08:00 → LONG entry=9987.00 SL=9925.80 TP1=10079.00 → **LOSS** -1.0R
  - ny 2026-03-25T14:00 → LONG entry=9987.00 SL=9926.10 TP1=10078.40 → **LOSS** -1.0R

### 2026-03-26
- API calls: 9 | Trades: 1 | L2 rejected: 1 | Limit blocked: 7
  - london 2026-03-26T08:00 → LONG entry=9987.00 SL=9919.30 TP1=10088.50 → **LOSS** -1.0R

## T7 vs P2A v1 Decision Comparison

- Both CANDIDATE: 0
- T7 CANDIDATE, P2A NO_TRADE: 5
- T7 NO_TRADE, P2A CANDIDATE: 0

## Caveats

- **SL-first on wide candles:** If both SL and TP are hit in one M15 candle, SL wins (conservative bias).
- **No spread simulation:** Entry prices are AI-quoted, no spread added.
- **No tick data:** Outcome determined by M15 OHLC only, not intra-candle sequence.
- **KB context empty:** Production passes last-10-trade context; simulation does not.
