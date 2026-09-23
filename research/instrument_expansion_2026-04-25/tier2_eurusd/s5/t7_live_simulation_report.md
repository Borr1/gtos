# T7 Production-Faithful Simulation Report
**Dates:** 2026-03-03 to 2026-03-22
**Total KZ candles:** 117
**Total API cost:** $4.06
**Batch reference:** T7: CR=86.7%, WR=66.3%, +39.5R (n=121, no L2); P2A v1: CR=38%, WR=69.6% (n=104)

**Production gates simulated:** prescreen, deterministic bias, skip_first_ny,
L2 verification, inverted TP auto-correction, max 2 trades/day, max 1 trade/KZ.

## Summary by Instrument

| Symbol | KZ Candles | API Calls | T7 CAND | L2 Reject | Limit Block | Final Trades | CR (raw) | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|--------|-----------|-----------|---------|-----------|-------------|-------------|----------|-----------|------|--------|----|---------|-----------|
| EURUSD   |       117 |        69 |      37 |        33 |           3 |           1 |    53.6% |      1.4% |    0 |      1 |   0% |   -1.0R | -1.000R |

## Pipeline Funnel

- Total KZ candles: 117
- Skipped (prescreen D1/H4): 0
- Skipped (no bias): 0
- Skipped (OB proximity): 48
- Skipped (first NY candle): 0
- Sent to API: 69
- AI returned CANDIDATE: 37 (raw CR: 53.6%)
  - Inverted TP corrected: 0
  - L2 Rejected: 33
  - PA parse failed → NO_TRADE: 0 (production would retry then reject)
  - Blocked by trade limits: 3
- **Final CANDIDATE decisions: 1** (live CR: 1.4%)

## Monthly Breakdown

| Month | API Calls | Raw CAND | Final Trades | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|-------|-----------|----------|-------------|-----------|------|--------|----|---------|-----------|
| 2026-03 |        69 |       37 |           1 |      1.4% |    0 |      1 |   0% |   -1.0R | -1.000R |

## Risk Metrics

- Total resolved trades: 1
- Win rate: 0.0%
- Expectancy per trade: -1.000R
- Total R: -1.0R
- Max consecutive losses: 1
- Max drawdown: 1.0R
- Trades per week: 0.3
- Trades per month: 1.0

## Trade Distribution

- London: 0 (0%)
- NY: 1 (100%)
- LONG: 0 (0%)
- SHORT: 1 (100%)

## Day-by-Day Detail

### 2026-03-03
- API calls: 28 | Trades: 0 | L2 rejected: 16 | Limit blocked: 0

### 2026-03-04
- API calls: 10 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-03-05
- API calls: 16 | Trades: 0 | L2 rejected: 12 | Limit blocked: 0

### 2026-03-06
- API calls: 15 | Trades: 1 | L2 rejected: 5 | Limit blocked: 3
  - ny 2026-03-06T13:30 → SHORT entry=1.16 SL=1.16 TP1=1.16 → **LOSS** -1.0R

## T7 vs P2A v1 Decision Comparison

- Both CANDIDATE: 0
- T7 CANDIDATE, P2A NO_TRADE: 1
- T7 NO_TRADE, P2A CANDIDATE: 0

## Caveats

- **SL-first on wide candles:** If both SL and TP are hit in one M15 candle, SL wins (conservative bias).
- **No spread simulation:** Entry prices are AI-quoted, no spread added.
- **No tick data:** Outcome determined by M15 OHLC only, not intra-candle sequence.
- **KB context empty:** Production passes last-10-trade context; simulation does not.
