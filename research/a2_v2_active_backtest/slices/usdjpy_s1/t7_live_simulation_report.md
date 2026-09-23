# T7 Production-Faithful Simulation Report
**Dates:** 2026-01-02 to 2026-01-26
**Total KZ candles:** 359
**Total API cost:** $6.03
**Batch reference:** T7: CR=86.7%, WR=66.3%, +39.5R (n=121, no L2); P2A v1: CR=38%, WR=69.6% (n=104)

**Production gates simulated:** prescreen, deterministic bias, skip_first_ny,
L2 verification, inverted TP auto-correction, max 2 trades/day, max 1 trade/KZ.

## Summary by Instrument

| Symbol | KZ Candles | API Calls | T7 CAND | L2 Reject | Limit Block | Final Trades | CR (raw) | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|--------|-----------|-----------|---------|-----------|-------------|-------------|----------|-----------|------|--------|----|---------|-----------|
| USDJPY   |       359 |       143 |     101 |        50 |          45 |           6 |    70.6% |      4.2% |    3 |      3 |  50% |   +1.5R | +0.250R |

## Pipeline Funnel

- Total KZ candles: 359
- Skipped (prescreen D1/H4): 176
- Skipped (no bias): 0
- Skipped (OB proximity): 40
- Skipped (first NY candle): 0
- Sent to API: 143
- AI returned CANDIDATE: 101 (raw CR: 70.6%)
  - Inverted TP corrected: 0
  - L2 Rejected: 50
  - PA parse failed → NO_TRADE: 0 (production would retry then reject)
  - Blocked by trade limits: 45
- **Final CANDIDATE decisions: 6** (live CR: 4.2%)

## Monthly Breakdown

| Month | API Calls | Raw CAND | Final Trades | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|-------|-----------|----------|-------------|-----------|------|--------|----|---------|-----------|
| 2026-01 |       143 |      101 |           6 |      4.2% |    3 |      3 |  50% |   +1.5R | +0.250R |

## Risk Metrics

- Total resolved trades: 6
- Win rate: 50.0%
- Expectancy per trade: +0.250R
- Total R: +1.5R
- Max consecutive losses: 3
- Max drawdown: 3.0R
- Trades per week: 1.7
- Trades per month: 6.0

## Trade Distribution

- London: 2 (33%)
- NY: 1 (17%)
- LONG: 6 (100%)
- SHORT: 0 (0%)

## Day-by-Day Detail

### 2026-01-02
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-01-05
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-01-06
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-01-07
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-01-08
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-01-09
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-01-12
- API calls: 12 | Trades: 1 | L2 rejected: 0 | Limit blocked: 7
  - tokyo 2026-01-12T00:00 → LONG entry=157.80 SL=157.32 TP1=158.51 → **WIN** 1.5R

### 2026-01-13
- API calls: 28 | Trades: 2 | L2 rejected: 2 | Limit blocked: 21
  - tokyo 2026-01-13T00:15 → LONG entry=157.90 SL=157.62 TP1=158.32 → **WIN** 1.5R
  - london 2026-01-13T07:00 → LONG entry=158.18 SL=157.84 TP1=158.69 → **WIN** 1.5R

### 2026-01-14
- API calls: 32 | Trades: 2 | L2 rejected: 4 | Limit blocked: 16
  - tokyo 2026-01-14T00:00 → LONG entry=158.96 SL=158.39 TP1=159.82 → **LOSS** -1.0R
  - london 2026-01-14T07:00 → LONG entry=158.96 SL=158.53 TP1=159.61 → **LOSS** -1.0R

### 2026-01-15
- API calls: 32 | Trades: 1 | L2 rejected: 26 | Limit blocked: 1
  - ny 2026-01-15T15:00 → LONG entry=158.70 SL=158.24 TP1=159.39 → **LOSS** -1.0R

### 2026-01-16
- API calls: 32 | Trades: 0 | L2 rejected: 18 | Limit blocked: 0

### 2026-01-19
- API calls: 7 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

## T7 vs P2A v1 Decision Comparison

- Both CANDIDATE: 0
- T7 CANDIDATE, P2A NO_TRADE: 6
- T7 NO_TRADE, P2A CANDIDATE: 0

## Caveats

- **SL-first on wide candles:** If both SL and TP are hit in one M15 candle, SL wins (conservative bias).
- **No spread simulation:** Entry prices are AI-quoted, no spread added.
- **No tick data:** Outcome determined by M15 OHLC only, not intra-candle sequence.
- **KB context empty:** Production passes last-10-trade context; simulation does not.
