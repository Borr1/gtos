# T7 Production-Faithful Simulation Report
**Dates:** 2026-04-14 to 2026-04-24
**Total KZ candles:** 169
**Total API cost:** $4.03
**Batch reference:** T7: CR=86.7%, WR=66.3%, +39.5R (n=121, no L2); P2A v1: CR=38%, WR=69.6% (n=104)

**Production gates simulated:** prescreen, deterministic bias, skip_first_ny,
L2 verification, inverted TP auto-correction, max 2 trades/day, max 1 trade/KZ.

## Summary by Instrument

| Symbol | KZ Candles | API Calls | T7 CAND | L2 Reject | Limit Block | Final Trades | CR (raw) | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|--------|-----------|-----------|---------|-----------|-------------|-------------|----------|-----------|------|--------|----|---------|-----------|
| XAGUSD   |       169 |        67 |      43 |         4 |          31 |           8 |    64.2% |     11.9% |    6 |      2 |  75% |   +7.0R | +0.875R |

## Pipeline Funnel

- Total KZ candles: 169
- Skipped (prescreen D1/H4): 30
- Skipped (no bias): 0
- Skipped (OB proximity): 72
- Skipped (first NY candle): 0
- Sent to API: 67
- AI returned CANDIDATE: 43 (raw CR: 64.2%)
  - Inverted TP corrected: 0
  - L2 Rejected: 4
  - PA parse failed → NO_TRADE: 0 (production would retry then reject)
  - Blocked by trade limits: 31
- **Final CANDIDATE decisions: 8** (live CR: 11.9%)

## Monthly Breakdown

| Month | API Calls | Raw CAND | Final Trades | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|-------|-----------|----------|-------------|-----------|------|--------|----|---------|-----------|
| 2026-04 |        67 |       43 |           8 |     11.9% |    6 |      2 |  75% |   +7.0R | +0.875R |

## Risk Metrics

- Total resolved trades: 8
- Win rate: 75.0%
- Expectancy per trade: +0.875R
- Total R: +7.0R
- Max consecutive losses: 1
- Max drawdown: 1.0R
- Trades per week: 5.1
- Trades per month: 8.0

## Trade Distribution

- London: 5 (62%)
- NY: 3 (38%)
- LONG: 8 (100%)
- SHORT: 0 (0%)

## Day-by-Day Detail

### 2026-04-14
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-04-15
- API calls: 8 | Trades: 2 | L2 rejected: 0 | Limit blocked: 3
  - london 2026-04-15T09:00 → LONG entry=77.76 SL=77.00 TP1=78.90 → **WIN** 1.5R
  - ny 2026-04-15T13:30 → LONG entry=77.76 SL=77.00 TP1=78.90 → **WIN** 1.5R

### 2026-04-16
- API calls: 5 | Trades: 1 | L2 rejected: 0 | Limit blocked: 0
  - london 2026-04-16T10:00 → LONG entry=79.38 SL=78.78 TP1=80.27 → **LOSS** -1.0R

### 2026-04-17
- API calls: 19 | Trades: 2 | L2 rejected: 0 | Limit blocked: 17
  - london 2026-04-17T07:00 → LONG entry=78.56 SL=78.08 TP1=79.27 → **WIN** 1.5R
  - ny 2026-04-17T13:00 → LONG entry=79.00 SL=78.34 TP1=79.98 → **WIN** 1.5R

### 2026-04-20
- API calls: 16 | Trades: 2 | L2 rejected: 0 | Limit blocked: 9
  - london 2026-04-20T07:00 → LONG entry=74.31 SL=73.58 TP1=75.41 → **WIN** 1.5R
  - ny 2026-04-20T16:00 → LONG entry=79.91 SL=79.22 TP1=80.94 → **LOSS** -1.0R

### 2026-04-21
- API calls: 19 | Trades: 1 | L2 rejected: 4 | Limit blocked: 2
  - london 2026-04-21T07:15 → LONG entry=74.31 SL=73.62 TP1=75.34 → **WIN** 1.5R

## T7 vs P2A v1 Decision Comparison

- Both CANDIDATE: 0
- T7 CANDIDATE, P2A NO_TRADE: 8
- T7 NO_TRADE, P2A CANDIDATE: 0

## Caveats

- **SL-first on wide candles:** If both SL and TP are hit in one M15 candle, SL wins (conservative bias).
- **No spread simulation:** Entry prices are AI-quoted, no spread added.
- **No tick data:** Outcome determined by M15 OHLC only, not intra-candle sequence.
- **KB context empty:** Production passes last-10-trade context; simulation does not.
