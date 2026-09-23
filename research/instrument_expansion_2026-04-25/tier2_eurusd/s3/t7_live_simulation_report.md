# T7 Production-Faithful Simulation Report
**Dates:** 2026-02-01 to 2026-02-15
**Total KZ candles:** 70
**Total API cost:** $4.01
**Batch reference:** T7: CR=86.7%, WR=66.3%, +39.5R (n=121, no L2); P2A v1: CR=38%, WR=69.6% (n=104)

**Production gates simulated:** prescreen, deterministic bias, skip_first_ny,
L2 verification, inverted TP auto-correction, max 2 trades/day, max 1 trade/KZ.

## Summary by Instrument

| Symbol | KZ Candles | API Calls | T7 CAND | L2 Reject | Limit Block | Final Trades | CR (raw) | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|--------|-----------|-----------|---------|-----------|-------------|-------------|----------|-----------|------|--------|----|---------|-----------|
| EURUSD   |        70 |        70 |      18 |         8 |           9 |           1 |    25.7% |      1.4% |    0 |      1 |   0% |   -1.0R | -1.000R |

## Pipeline Funnel

- Total KZ candles: 70
- Skipped (prescreen D1/H4): 0
- Skipped (no bias): 0
- Skipped (OB proximity): 0
- Skipped (first NY candle): 0
- Sent to API: 70
- AI returned CANDIDATE: 18 (raw CR: 25.7%)
  - Inverted TP corrected: 0
  - L2 Rejected: 8
  - PA parse failed → NO_TRADE: 0 (production would retry then reject)
  - Blocked by trade limits: 9
- **Final CANDIDATE decisions: 1** (live CR: 1.4%)

## Monthly Breakdown

| Month | API Calls | Raw CAND | Final Trades | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|-------|-----------|----------|-------------|-----------|------|--------|----|---------|-----------|
| 2026-02 |        70 |       18 |           1 |      1.4% |    0 |      1 |   0% |   -1.0R | -1.000R |

## Risk Metrics

- Total resolved trades: 1
- Win rate: 0.0%
- Expectancy per trade: -1.000R
- Total R: -1.0R
- Max consecutive losses: 1
- Max drawdown: 1.0R
- Trades per week: 0.5
- Trades per month: 1.0

## Trade Distribution

- London: 1 (100%)
- NY: 0 (0%)
- LONG: 1 (100%)
- SHORT: 0 (0%)

## Day-by-Day Detail

### 2026-02-02
- API calls: 30 | Trades: 0 | L2 rejected: 3 | Limit blocked: 0

### 2026-02-03
- API calls: 30 | Trades: 0 | L2 rejected: 5 | Limit blocked: 0

### 2026-02-04
- API calls: 10 | Trades: 1 | L2 rejected: 0 | Limit blocked: 9
  - london 2026-02-04T07:00 → LONG entry=1.18 SL=1.18 TP1=1.18 → **LOSS** -1.0R

## T7 vs P2A v1 Decision Comparison

- Both CANDIDATE: 0
- T7 CANDIDATE, P2A NO_TRADE: 1
- T7 NO_TRADE, P2A CANDIDATE: 0

## Caveats

- **SL-first on wide candles:** If both SL and TP are hit in one M15 candle, SL wins (conservative bias).
- **No spread simulation:** Entry prices are AI-quoted, no spread added.
- **No tick data:** Outcome determined by M15 OHLC only, not intra-candle sequence.
- **KB context empty:** Production passes last-10-trade context; simulation does not.
