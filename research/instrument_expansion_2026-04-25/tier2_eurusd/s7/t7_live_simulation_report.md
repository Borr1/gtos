# T7 Production-Faithful Simulation Report
**Dates:** 2026-04-14 to 2026-04-24
**Total KZ candles:** 210
**Total API cost:** $4.05
**Batch reference:** T7: CR=86.7%, WR=66.3%, +39.5R (n=121, no L2); P2A v1: CR=38%, WR=69.6% (n=104)

**Production gates simulated:** prescreen, deterministic bias, skip_first_ny,
L2 verification, inverted TP auto-correction, max 2 trades/day, max 1 trade/KZ.

## Summary by Instrument

| Symbol | KZ Candles | API Calls | T7 CAND | L2 Reject | Limit Block | Final Trades | CR (raw) | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|--------|-----------|-----------|---------|-----------|-------------|-------------|----------|-----------|------|--------|----|---------|-----------|
| EURUSD   |       210 |        70 |      47 |        40 |           5 |           2 |    67.1% |      2.9% |    0 |      2 |   0% |   -2.0R | -1.000R |

## Pipeline Funnel

- Total KZ candles: 210
- Skipped (prescreen D1/H4): 120
- Skipped (no bias): 0
- Skipped (OB proximity): 20
- Skipped (first NY candle): 0
- Sent to API: 70
- AI returned CANDIDATE: 47 (raw CR: 67.1%)
  - Inverted TP corrected: 0
  - L2 Rejected: 40
  - PA parse failed → NO_TRADE: 0 (production would retry then reject)
  - Blocked by trade limits: 5
- **Final CANDIDATE decisions: 2** (live CR: 2.9%)

## Monthly Breakdown

| Month | API Calls | Raw CAND | Final Trades | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|-------|-----------|----------|-------------|-----------|------|--------|----|---------|-----------|
| 2026-04 |        70 |       47 |           2 |      2.9% |    0 |      2 |   0% |   -2.0R | -1.000R |

## Risk Metrics

- Total resolved trades: 2
- Win rate: 0.0%
- Expectancy per trade: -1.000R
- Total R: -2.0R
- Max consecutive losses: 2
- Max drawdown: 2.0R
- Trades per week: 1.3
- Trades per month: 2.0

## Trade Distribution

- London: 1 (50%)
- NY: 1 (50%)
- LONG: 2 (100%)
- SHORT: 0 (0%)

## Day-by-Day Detail

### 2026-04-14
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-04-15
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-04-16
- API calls: 30 | Trades: 2 | L2 rejected: 18 | Limit blocked: 5
  - london 2026-04-16T10:30 → LONG entry=1.18 SL=1.18 TP1=1.18 → **LOSS** -1.0R
  - ny 2026-04-16T13:00 → LONG entry=1.18 SL=1.18 TP1=1.18 → **LOSS** -1.0R

### 2026-04-17
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-04-20
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-04-21
- API calls: 30 | Trades: 0 | L2 rejected: 18 | Limit blocked: 0

### 2026-04-22
- API calls: 10 | Trades: 0 | L2 rejected: 4 | Limit blocked: 0

## T7 vs P2A v1 Decision Comparison

- Both CANDIDATE: 0
- T7 CANDIDATE, P2A NO_TRADE: 2
- T7 NO_TRADE, P2A CANDIDATE: 0

## Caveats

- **SL-first on wide candles:** If both SL and TP are hit in one M15 candle, SL wins (conservative bias).
- **No spread simulation:** Entry prices are AI-quoted, no spread added.
- **No tick data:** Outcome determined by M15 OHLC only, not intra-candle sequence.
- **KB context empty:** Production passes last-10-trade context; simulation does not.
