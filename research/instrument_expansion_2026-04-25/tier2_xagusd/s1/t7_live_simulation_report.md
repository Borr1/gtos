# T7 Production-Faithful Simulation Report
**Dates:** 2026-01-02 to 2026-01-15
**Total KZ candles:** 300
**Total API cost:** $1.25
**Batch reference:** T7: CR=86.7%, WR=66.3%, +39.5R (n=121, no L2); P2A v1: CR=38%, WR=69.6% (n=104)

**Production gates simulated:** prescreen, deterministic bias, skip_first_ny,
L2 verification, inverted TP auto-correction, max 2 trades/day, max 1 trade/KZ.

## Summary by Instrument

| Symbol | KZ Candles | API Calls | T7 CAND | L2 Reject | Limit Block | Final Trades | CR (raw) | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|--------|-----------|-----------|---------|-----------|-------------|-------------|----------|-----------|------|--------|----|---------|-----------|
| XAGUSD   |       300 |        22 |       7 |         1 |           2 |           4 |    31.8% |     18.2% |    3 |      1 |  75% |   +3.5R | +0.875R |

## Pipeline Funnel

- Total KZ candles: 300
- Skipped (prescreen D1/H4): 124
- Skipped (no bias): 0
- Skipped (OB proximity): 154
- Skipped (first NY candle): 0
- Sent to API: 22
- AI returned CANDIDATE: 7 (raw CR: 31.8%)
  - Inverted TP corrected: 0
  - L2 Rejected: 1
  - PA parse failed → NO_TRADE: 0 (production would retry then reject)
  - Blocked by trade limits: 2
- **Final CANDIDATE decisions: 4** (live CR: 18.2%)

## Monthly Breakdown

| Month | API Calls | Raw CAND | Final Trades | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|-------|-----------|----------|-------------|-----------|------|--------|----|---------|-----------|
| 2026-01 |        22 |        7 |           4 |     18.2% |    3 |      1 |  75% |   +3.5R | +0.875R |

## Risk Metrics

- Total resolved trades: 4
- Win rate: 75.0%
- Expectancy per trade: +0.875R
- Total R: +3.5R
- Max consecutive losses: 1
- Max drawdown: 1.0R
- Trades per week: 2.0
- Trades per month: 4.0

## Trade Distribution

- London: 2 (50%)
- NY: 2 (50%)
- LONG: 4 (100%)
- SHORT: 0 (0%)

## Day-by-Day Detail

### 2026-01-02
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-01-05
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-01-06
- API calls: 2 | Trades: 1 | L2 rejected: 0 | Limit blocked: 1
  - ny 2026-01-06T16:00 → LONG entry=76.72 SL=75.67 TP1=78.30 → **WIN** 1.5R

### 2026-01-07
- API calls: 10 | Trades: 1 | L2 rejected: 0 | Limit blocked: 0
  - london 2026-01-07T08:45 → LONG entry=76.72 SL=75.59 TP1=78.41 → **WIN** 1.5R

### 2026-01-08
- API calls: 8 | Trades: 1 | L2 rejected: 1 | Limit blocked: 0
  - london 2026-01-08T10:15 → LONG entry=72.04 SL=71.16 TP1=73.36 → **LOSS** -1.0R

### 2026-01-09
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-01-12
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-01-13
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-01-14
- API calls: 2 | Trades: 1 | L2 rejected: 0 | Limit blocked: 1
  - ny 2026-01-14T14:00 → LONG entry=90.66 SL=89.82 TP1=91.92 → **WIN** 1.5R

### 2026-01-15
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

## T7 vs P2A v1 Decision Comparison

- Both CANDIDATE: 0
- T7 CANDIDATE, P2A NO_TRADE: 4
- T7 NO_TRADE, P2A CANDIDATE: 0

## Caveats

- **SL-first on wide candles:** If both SL and TP are hit in one M15 candle, SL wins (conservative bias).
- **No spread simulation:** Entry prices are AI-quoted, no spread added.
- **No tick data:** Outcome determined by M15 OHLC only, not intra-candle sequence.
- **KB context empty:** Production passes last-10-trade context; simulation does not.
