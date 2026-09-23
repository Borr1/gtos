# T7 Production-Faithful Simulation Report
**Dates:** 2026-03-18 to 2026-04-13
**Total KZ candles:** 264
**Total API cost:** $6.02
**Batch reference:** T7: CR=86.7%, WR=66.3%, +39.5R (n=121, no L2); P2A v1: CR=38%, WR=69.6% (n=104)

**Production gates simulated:** prescreen, deterministic bias, skip_first_ny,
L2 verification, inverted TP auto-correction, max 2 trades/day, max 1 trade/KZ.

## Summary by Instrument

| Symbol | KZ Candles | API Calls | T7 CAND | L2 Reject | Limit Block | Final Trades | CR (raw) | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|--------|-----------|-----------|---------|-----------|-------------|-------------|----------|-----------|------|--------|----|---------|-----------|
| USDJPY   |       264 |       150 |      65 |        29 |          31 |           5 |    43.3% |      3.3% |    2 |      3 |  40% |   +0.0R | +0.000R |

## Pipeline Funnel

- Total KZ candles: 264
- Skipped (prescreen D1/H4): 0
- Skipped (no bias): 0
- Skipped (OB proximity): 114
- Skipped (first NY candle): 0
- Sent to API: 150
- AI returned CANDIDATE: 65 (raw CR: 43.3%)
  - Inverted TP corrected: 0
  - L2 Rejected: 29
  - PA parse failed → NO_TRADE: 0 (production would retry then reject)
  - Blocked by trade limits: 31
- **Final CANDIDATE decisions: 5** (live CR: 3.3%)

## Monthly Breakdown

| Month | API Calls | Raw CAND | Final Trades | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|-------|-----------|----------|-------------|-----------|------|--------|----|---------|-----------|
| 2026-03 |       150 |       65 |           5 |      3.3% |    2 |      3 |  40% |   +0.0R | +0.000R |

## Risk Metrics

- Total resolved trades: 5
- Win rate: 40.0%
- Expectancy per trade: +0.000R
- Total R: +0.0R
- Max consecutive losses: 2
- Max drawdown: 2.0R
- Trades per week: 1.3
- Trades per month: 5.0

## Trade Distribution

- London: 1 (20%)
- NY: 3 (60%)
- LONG: 5 (100%)
- SHORT: 0 (0%)

## Day-by-Day Detail

### 2026-03-18
- API calls: 12 | Trades: 0 | L2 rejected: 2 | Limit blocked: 0

### 2026-03-19
- API calls: 22 | Trades: 2 | L2 rejected: 4 | Limit blocked: 16
  - tokyo 2026-03-19T00:00 → LONG entry=159.54 SL=159.20 TP1=160.05 → **LOSS** -1.0R
  - london 2026-03-19T08:00 → LONG entry=159.11 SL=158.87 TP1=159.46 → **LOSS** -1.0R

### 2026-03-20
- API calls: 20 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-03-23
- API calls: 12 | Trades: 0 | L2 rejected: 3 | Limit blocked: 0

### 2026-03-24
- API calls: 32 | Trades: 1 | L2 rejected: 0 | Limit blocked: 1
  - ny 2026-03-24T15:00 → LONG entry=158.77 SL=158.54 TP1=159.12 → **WIN** 1.5R

### 2026-03-25
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-03-26
- API calls: 12 | Trades: 1 | L2 rejected: 1 | Limit blocked: 5
  - ny 2026-03-26T14:00 → LONG entry=159.55 SL=159.25 TP1=160.00 → **WIN** 1.5R

### 2026-03-27
- API calls: 32 | Trades: 1 | L2 rejected: 11 | Limit blocked: 9
  - ny 2026-03-27T13:00 → LONG entry=159.59 SL=159.39 TP1=159.89 → **LOSS** -1.0R

### 2026-03-30
- API calls: 8 | Trades: 0 | L2 rejected: 8 | Limit blocked: 0

## T7 vs P2A v1 Decision Comparison

- Both CANDIDATE: 0
- T7 CANDIDATE, P2A NO_TRADE: 5
- T7 NO_TRADE, P2A CANDIDATE: 0

## Caveats

- **SL-first on wide candles:** If both SL and TP are hit in one M15 candle, SL wins (conservative bias).
- **No spread simulation:** Entry prices are AI-quoted, no spread added.
- **No tick data:** Outcome determined by M15 OHLC only, not intra-candle sequence.
- **KB context empty:** Production passes last-10-trade context; simulation does not.
