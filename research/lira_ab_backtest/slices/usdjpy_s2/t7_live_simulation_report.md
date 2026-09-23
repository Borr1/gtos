# T7 Production-Faithful Simulation Report
**Dates:** 2026-01-27 to 2026-02-20
**Total KZ candles:** 608
**Total API cost:** $5.64
**Batch reference:** T7: CR=86.7%, WR=66.3%, +39.5R (n=121, no L2); P2A v1: CR=38%, WR=69.6% (n=104)

**Production gates simulated:** prescreen, deterministic bias, skip_first_ny,
L2 verification, inverted TP auto-correction, max 2 trades/day, max 1 trade/KZ.

## Summary by Instrument

| Symbol | KZ Candles | API Calls | T7 CAND | L2 Reject | Limit Block | Final Trades | CR (raw) | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|--------|-----------|-----------|---------|-----------|-------------|-------------|----------|-----------|------|--------|----|---------|-----------|
| USDJPY   |       608 |       195 |     144 |        89 |          46 |           9 |    73.8% |      4.6% |    5 |      4 |  56% |   +3.5R | +0.389R |

## Pipeline Funnel

- Total KZ candles: 608
- Skipped (prescreen D1/H4): 320
- Skipped (no bias): 0
- Skipped (OB proximity): 93
- Skipped (first NY candle): 0
- Sent to API: 195
- AI returned CANDIDATE: 144 (raw CR: 73.8%)
  - Inverted TP corrected: 0
  - L2 Rejected: 89
  - PA parse failed → NO_TRADE: 0 (production would retry then reject)
  - Blocked by trade limits: 46
- **Final CANDIDATE decisions: 9** (live CR: 4.6%)

## Monthly Breakdown

| Month | API Calls | Raw CAND | Final Trades | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|-------|-----------|----------|-------------|-----------|------|--------|----|---------|-----------|
| 2026-01 |        12 |        0 |           0 |      0.0% |    0 |      0 |   0% |   +0.0R | +0.000R |
| 2026-02 |       183 |      144 |           9 |      4.9% |    5 |      4 |  56% |   +3.5R | +0.389R |

## Risk Metrics

- Total resolved trades: 9
- Win rate: 55.6%
- Expectancy per trade: +0.389R
- Total R: +3.5R
- Max consecutive losses: 1
- Max drawdown: 1.0R
- Trades per week: 2.5
- Trades per month: 9.0

## Trade Distribution

- London: 4 (44%)
- NY: 0 (0%)
- LONG: 8 (89%)
- SHORT: 1 (11%)

## Day-by-Day Detail

### 2026-01-27
- API calls: 12 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-01-28
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-01-29
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-01-30
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-02
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-03
- API calls: 32 | Trades: 0 | L2 rejected: 32 | Limit blocked: 0

### 2026-02-04
- API calls: 32 | Trades: 2 | L2 rejected: 17 | Limit blocked: 13
  - tokyo 2026-02-04T02:45 → LONG entry=155.52 SL=155.24 TP1=155.95 → **WIN** 1.5R
  - london 2026-02-04T07:15 → LONG entry=155.81 SL=155.65 TP1=156.06 → **LOSS** -1.0R

### 2026-02-05
- API calls: 32 | Trades: 2 | L2 rejected: 9 | Limit blocked: 16
  - tokyo 2026-02-05T00:00 → LONG entry=156.74 SL=156.51 TP1=157.09 → **WIN** 1.5R
  - london 2026-02-05T07:00 → LONG entry=154.88 SL=154.68 TP1=155.19 → **LOSS** -1.0R

### 2026-02-06
- API calls: 32 | Trades: 2 | L2 rejected: 18 | Limit blocked: 9
  - tokyo 2026-02-06T00:00 → LONG entry=155.52 SL=155.21 TP1=155.98 → **WIN** 1.5R
  - london 2026-02-06T07:30 → LONG entry=154.88 SL=154.67 TP1=155.19 → **LOSS** -1.0R

### 2026-02-09
- API calls: 27 | Trades: 2 | L2 rejected: 9 | Limit blocked: 7
  - tokyo 2026-02-09T01:45 → LONG entry=155.52 SL=155.16 TP1=156.05 → **WIN** 1.5R
  - london 2026-02-09T08:00 → LONG entry=155.52 SL=155.23 TP1=155.95 → **WIN** 1.5R

### 2026-02-10
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-11
- API calls: 22 | Trades: 1 | L2 rejected: 4 | Limit blocked: 1
  - tokyo 2026-02-11T02:30 → SHORT entry=154.36 SL=154.57 TP1=153.05 → **LOSS** -1.0R

### 2026-02-12
- API calls: 6 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-13
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-16
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-17
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-18
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-19
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-20
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

## T7 vs P2A v1 Decision Comparison

- Both CANDIDATE: 0
- T7 CANDIDATE, P2A NO_TRADE: 9
- T7 NO_TRADE, P2A CANDIDATE: 0

## Caveats

- **SL-first on wide candles:** If both SL and TP are hit in one M15 candle, SL wins (conservative bias).
- **No spread simulation:** Entry prices are AI-quoted, no spread added.
- **No tick data:** Outcome determined by M15 OHLC only, not intra-candle sequence.
- **KB context empty:** Production passes last-10-trade context; simulation does not.
