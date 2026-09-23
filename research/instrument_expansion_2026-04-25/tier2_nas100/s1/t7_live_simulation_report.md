# T7 Production-Faithful Simulation Report
**Dates:** 2026-01-02 to 2026-01-15
**Total KZ candles:** 300
**Total API cost:** $3.30
**Batch reference:** T7: CR=86.7%, WR=66.3%, +39.5R (n=121, no L2); P2A v1: CR=38%, WR=69.6% (n=104)

**Production gates simulated:** prescreen, deterministic bias, skip_first_ny,
L2 verification, inverted TP auto-correction, max 2 trades/day, max 1 trade/KZ.

## Summary by Instrument

| Symbol | KZ Candles | API Calls | T7 CAND | L2 Reject | Limit Block | Final Trades | CR (raw) | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|--------|-----------|-----------|---------|-----------|-------------|-------------|----------|-----------|------|--------|----|---------|-----------|
| NAS100   |       300 |        58 |      27 |         1 |          23 |           3 |    46.6% |      5.2% |    3 |      0 | 100% |   +4.5R | +1.500R |

## Pipeline Funnel

- Total KZ candles: 300
- Skipped (prescreen D1/H4): 158
- Skipped (no bias): 0
- Skipped (OB proximity): 84
- Skipped (first NY candle): 0
- Sent to API: 58
- AI returned CANDIDATE: 27 (raw CR: 46.6%)
  - Inverted TP corrected: 0
  - L2 Rejected: 1
  - PA parse failed → NO_TRADE: 0 (production would retry then reject)
  - Blocked by trade limits: 23
- **Final CANDIDATE decisions: 3** (live CR: 5.2%)

## Monthly Breakdown

| Month | API Calls | Raw CAND | Final Trades | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|-------|-----------|----------|-------------|-----------|------|--------|----|---------|-----------|
| 2026-01 |        58 |       27 |           3 |      5.2% |    3 |      0 | 100% |   +4.5R | +1.500R |

## Risk Metrics

- Total resolved trades: 3
- Win rate: 100.0%
- Expectancy per trade: +1.500R
- Total R: +4.5R
- Max consecutive losses: 0
- Max drawdown: 0.0R
- Trades per week: 1.5
- Trades per month: 3.0

## Trade Distribution

- London: 1 (33%)
- NY: 2 (67%)
- LONG: 3 (100%)
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
- API calls: 16 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-01-09
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-01-12
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-01-13
- API calls: 8 | Trades: 1 | L2 rejected: 0 | Limit blocked: 7
  - ny 2026-01-13T15:00 → LONG entry=25752.40 SL=25691.40 TP1=25843.90 → **WIN** 1.5R

### 2026-01-14
- API calls: 16 | Trades: 0 | L2 rejected: 1 | Limit blocked: 0

### 2026-01-15
- API calls: 18 | Trades: 2 | L2 rejected: 0 | Limit blocked: 16
  - london 2026-01-15T08:00 → LONG entry=25438.50 SL=25389.80 TP1=25511.60 → **WIN** 1.5R
  - ny 2026-01-15T13:00 → LONG entry=25438.50 SL=25390.90 TP1=25509.90 → **WIN** 1.5R

## T7 vs P2A v1 Decision Comparison

- Both CANDIDATE: 0
- T7 CANDIDATE, P2A NO_TRADE: 3
- T7 NO_TRADE, P2A CANDIDATE: 0

## Caveats

- **SL-first on wide candles:** If both SL and TP are hit in one M15 candle, SL wins (conservative bias).
- **No spread simulation:** Entry prices are AI-quoted, no spread added.
- **No tick data:** Outcome determined by M15 OHLC only, not intra-candle sequence.
- **KB context empty:** Production passes last-10-trade context; simulation does not.
