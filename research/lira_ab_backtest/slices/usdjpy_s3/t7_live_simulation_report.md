# T7 Production-Faithful Simulation Report
**Dates:** 2026-02-21 to 2026-03-17
**Total KZ candles:** 469
**Total API cost:** $6.00
**Batch reference:** T7: CR=86.7%, WR=66.3%, +39.5R (n=121, no L2); P2A v1: CR=38%, WR=69.6% (n=104)

**Production gates simulated:** prescreen, deterministic bias, skip_first_ny,
L2 verification, inverted TP auto-correction, max 2 trades/day, max 1 trade/KZ.

## Summary by Instrument

| Symbol | KZ Candles | API Calls | T7 CAND | L2 Reject | Limit Block | Final Trades | CR (raw) | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|--------|-----------|-----------|---------|-----------|-------------|-------------|----------|-----------|------|--------|----|---------|-----------|
| USDJPY   |       469 |       215 |     161 |        54 |          94 |          13 |    74.9% |      6.0% |    3 |      5 |  38% |   -0.5R | -0.062R |

## Pipeline Funnel

- Total KZ candles: 469
- Skipped (prescreen D1/H4): 136
- Skipped (no bias): 0
- Skipped (OB proximity): 118
- Skipped (first NY candle): 0
- Sent to API: 215
- AI returned CANDIDATE: 161 (raw CR: 74.9%)
  - Inverted TP corrected: 0
  - L2 Rejected: 54
  - PA parse failed → NO_TRADE: 0 (production would retry then reject)
  - Blocked by trade limits: 94
- **Final CANDIDATE decisions: 13** (live CR: 6.0%)
  - ⚠ Entry limit never filled (unfilled): 5 — excluded from WR/expectancy

## Monthly Breakdown

| Month | API Calls | Raw CAND | Final Trades | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|-------|-----------|----------|-------------|-----------|------|--------|----|---------|-----------|
| 2026-02 |        64 |       49 |           4 |      6.2% |    1 |      0 | 100% |   +1.5R | +1.500R |
| 2026-03 |       151 |      112 |           9 |      6.0% |    2 |      5 |  29% |   -2.0R | -0.286R |

## Risk Metrics

- ⚠ Unfilled (entry limit never reached): 5 — excluded from all metrics below
- Total resolved trades: 8
- Win rate: 37.5%
- Expectancy per trade: -0.062R
- Total R: -0.5R
- Max consecutive losses: 3
- Max drawdown: 3.5R
- Trades per week: 2.2
- Trades per month: 8.0

## Trade Distribution

- London: 4 (31%)
- NY: 3 (23%)
- LONG: 13 (100%)
- SHORT: 0 (0%)

## Day-by-Day Detail

### 2026-02-23
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-24
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-25
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-26
- API calls: 32 | Trades: 2 | L2 rejected: 0 | Limit blocked: 21
  - tokyo 2026-02-26T00:15 → LONG entry=155.80 SL=155.52 TP1=156.22 → **WIN** 1.5R
  - london 2026-02-26T07:00 → LONG entry=155.19 SL=154.93 TP1=155.58 → **UNFILLED** ?R

### 2026-02-27
- API calls: 32 | Trades: 2 | L2 rejected: 0 | Limit blocked: 24
  - tokyo 2026-02-27T00:30 → LONG entry=155.19 SL=154.85 TP1=155.71 → **UNFILLED** ?R
  - london 2026-02-27T07:00 → LONG entry=155.19 SL=154.91 TP1=155.60 → **UNFILLED** ?R

### 2026-03-02
- API calls: 32 | Trades: 2 | L2 rejected: 6 | Limit blocked: 24
  - tokyo 2026-03-02T00:00 → LONG entry=155.19 SL=154.92 TP1=155.59 → **UNFILLED** ?R
  - london 2026-03-02T07:00 → LONG entry=155.19 SL=154.91 TP1=155.62 → **UNFILLED** ?R

### 2026-03-03
- API calls: 32 | Trades: 2 | L2 rejected: 19 | Limit blocked: 8
  - tokyo 2026-03-03T00:15 → LONG entry=157.01 SL=156.73 TP1=157.43 → **LOSS** -1.0R
  - ny 2026-03-03T13:00 → LONG entry=157.48 SL=157.09 TP1=158.07 → **LOSS** -1.0R

### 2026-03-04
- API calls: 32 | Trades: 1 | L2 rejected: 29 | Limit blocked: 1
  - tokyo 2026-03-04T00:15 → LONG entry=157.01 SL=156.72 TP1=157.45 → **LOSS** -1.0R

### 2026-03-05
- API calls: 4 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-03-06
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-03-09
- API calls: 10 | Trades: 1 | L2 rejected: 0 | Limit blocked: 9
  - ny 2026-03-09T13:00 → LONG entry=158.08 SL=157.94 TP1=158.28 → **WIN** 1.5R

### 2026-03-10
- API calls: 14 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-03-11
- API calls: 18 | Trades: 1 | L2 rejected: 0 | Limit blocked: 2
  - ny 2026-03-11T13:00 → LONG entry=158.18 SL=157.81 TP1=158.74 → **LOSS** -1.0R

### 2026-03-12
- API calls: 8 | Trades: 1 | L2 rejected: 0 | Limit blocked: 5
  - tokyo 2026-03-12T01:30 → LONG entry=158.91 SL=158.71 TP1=159.21 → **LOSS** -1.0R

### 2026-03-13
- API calls: 1 | Trades: 1 | L2 rejected: 0 | Limit blocked: 0
  - london 2026-03-13T09:00 → LONG entry=159.23 SL=158.98 TP1=159.60 → **WIN** 1.5R

## T7 vs P2A v1 Decision Comparison

- Both CANDIDATE: 0
- T7 CANDIDATE, P2A NO_TRADE: 13
- T7 NO_TRADE, P2A CANDIDATE: 0

## Caveats

- **SL-first on wide candles:** If both SL and TP are hit in one M15 candle, SL wins (conservative bias).
- **No spread simulation:** Entry prices are AI-quoted, no spread added.
- **No tick data:** Outcome determined by M15 OHLC only, not intra-candle sequence.
- **KB context empty:** Production passes last-10-trade context; simulation does not.
