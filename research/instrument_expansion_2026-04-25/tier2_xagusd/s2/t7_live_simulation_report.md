# T7 Production-Faithful Simulation Report
**Dates:** 2026-01-16 to 2026-01-31
**Total KZ candles:** 330
**Total API cost:** $3.95
**Batch reference:** T7: CR=86.7%, WR=66.3%, +39.5R (n=121, no L2); P2A v1: CR=38%, WR=69.6% (n=104)

**Production gates simulated:** prescreen, deterministic bias, skip_first_ny,
L2 verification, inverted TP auto-correction, max 2 trades/day, max 1 trade/KZ.

## Summary by Instrument

| Symbol | KZ Candles | API Calls | T7 CAND | L2 Reject | Limit Block | Final Trades | CR (raw) | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|--------|-----------|-----------|---------|-----------|-------------|-------------|----------|-----------|------|--------|----|---------|-----------|
| XAGUSD   |       330 |        68 |      53 |         5 |          40 |           8 |    77.9% |     11.8% |    4 |      4 |  50% |   +2.0R | +0.250R |

## Pipeline Funnel

- Total KZ candles: 330
- Skipped (prescreen D1/H4): 0
- Skipped (no bias): 0
- Skipped (OB proximity): 262
- Skipped (first NY candle): 0
- Sent to API: 68
- AI returned CANDIDATE: 53 (raw CR: 77.9%)
  - Inverted TP corrected: 0
  - L2 Rejected: 5
  - PA parse failed → NO_TRADE: 0 (production would retry then reject)
  - Blocked by trade limits: 40
- **Final CANDIDATE decisions: 8** (live CR: 11.8%)

## Monthly Breakdown

| Month | API Calls | Raw CAND | Final Trades | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|-------|-----------|----------|-------------|-----------|------|--------|----|---------|-----------|
| 2026-01 |        68 |       53 |           8 |     11.8% |    4 |      4 |  50% |   +2.0R | +0.250R |

## Risk Metrics

- Total resolved trades: 8
- Win rate: 50.0%
- Expectancy per trade: +0.250R
- Total R: +2.0R
- Max consecutive losses: 2
- Max drawdown: 2.0R
- Trades per week: 3.5
- Trades per month: 8.0

## Trade Distribution

- London: 3 (38%)
- NY: 5 (62%)
- LONG: 8 (100%)
- SHORT: 0 (0%)

## Day-by-Day Detail

### 2026-01-16
- API calls: 3 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-01-19
- API calls: 4 | Trades: 1 | L2 rejected: 0 | Limit blocked: 3
  - ny 2026-01-19T16:00 → LONG entry=93.55 SL=92.88 TP1=94.55 → **WIN** 1.5R

### 2026-01-20
- API calls: 10 | Trades: 2 | L2 rejected: 0 | Limit blocked: 6
  - london 2026-01-20T10:00 → LONG entry=94.49 SL=93.12 TP1=96.55 → **LOSS** -1.0R
  - ny 2026-01-20T13:00 → LONG entry=94.49 SL=93.14 TP1=95.51 → **LOSS** -1.0R

### 2026-01-21
- API calls: 4 | Trades: 0 | L2 rejected: 4 | Limit blocked: 0

### 2026-01-22
- API calls: 26 | Trades: 2 | L2 rejected: 1 | Limit blocked: 20
  - london 2026-01-22T07:00 → LONG entry=93.41 SL=92.79 TP1=94.34 → **WIN** 1.5R
  - ny 2026-01-22T14:30 → LONG entry=85.79 SL=85.19 TP1=86.70 → **LOSS** -1.0R

### 2026-01-23
- API calls: 8 | Trades: 1 | L2 rejected: 0 | Limit blocked: 7
  - ny 2026-01-23T15:00 → LONG entry=98.73 SL=97.32 TP1=100.84 → **WIN** 1.5R

### 2026-01-26
- API calls: 4 | Trades: 1 | L2 rejected: 0 | Limit blocked: 3
  - ny 2026-01-26T16:00 → LONG entry=110.35 SL=108.33 TP1=113.38 → **WIN** 1.5R

### 2026-01-27
- API calls: 4 | Trades: 1 | L2 rejected: 0 | Limit blocked: 1
  - london 2026-01-27T09:00 → LONG entry=110.52 SL=108.54 TP1=113.50 → **LOSS** -1.0R

### 2026-01-28
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-01-29
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-01-30
- API calls: 5 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

## T7 vs P2A v1 Decision Comparison

- Both CANDIDATE: 0
- T7 CANDIDATE, P2A NO_TRADE: 8
- T7 NO_TRADE, P2A CANDIDATE: 0

## Caveats

- **SL-first on wide candles:** If both SL and TP are hit in one M15 candle, SL wins (conservative bias).
- **No spread simulation:** Entry prices are AI-quoted, no spread added.
- **No tick data:** Outcome determined by M15 OHLC only, not intra-candle sequence.
- **KB context empty:** Production passes last-10-trade context; simulation does not.
