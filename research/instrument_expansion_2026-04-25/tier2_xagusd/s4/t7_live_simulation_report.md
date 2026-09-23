# T7 Production-Faithful Simulation Report
**Dates:** 2026-02-16 to 2026-03-02
**Total KZ candles:** 330
**Total API cost:** $3.12
**Batch reference:** T7: CR=86.7%, WR=66.3%, +39.5R (n=121, no L2); P2A v1: CR=38%, WR=69.6% (n=104)

**Production gates simulated:** prescreen, deterministic bias, skip_first_ny,
L2 verification, inverted TP auto-correction, max 2 trades/day, max 1 trade/KZ.

## Summary by Instrument

| Symbol | KZ Candles | API Calls | T7 CAND | L2 Reject | Limit Block | Final Trades | CR (raw) | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|--------|-----------|-----------|---------|-----------|-------------|-------------|----------|-----------|------|--------|----|---------|-----------|
| XAGUSD   |       330 |        54 |      35 |         4 |          26 |           5 |    64.8% |      9.3% |    4 |      1 |  80% |   +5.0R | +1.000R |

## Pipeline Funnel

- Total KZ candles: 330
- Skipped (prescreen D1/H4): 0
- Skipped (no bias): 0
- Skipped (OB proximity): 276
- Skipped (first NY candle): 0
- Sent to API: 54
- AI returned CANDIDATE: 35 (raw CR: 64.8%)
  - Inverted TP corrected: 0
  - L2 Rejected: 4
  - PA parse failed → NO_TRADE: 0 (production would retry then reject)
  - Blocked by trade limits: 26
- **Final CANDIDATE decisions: 5** (live CR: 9.3%)

## Monthly Breakdown

| Month | API Calls | Raw CAND | Final Trades | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|-------|-----------|----------|-------------|-----------|------|--------|----|---------|-----------|
| 2026-02 |        54 |       35 |           5 |      9.3% |    4 |      1 |  80% |   +5.0R | +1.000R |
| 2026-03 |         0 |        0 |           0 |      0.0% |    0 |      0 |   0% |   +0.0R | +0.000R |

## Risk Metrics

- Total resolved trades: 5
- Win rate: 80.0%
- Expectancy per trade: +1.000R
- Total R: +5.0R
- Max consecutive losses: 1
- Max drawdown: 1.0R
- Trades per week: 2.3
- Trades per month: 5.0

## Trade Distribution

- London: 3 (60%)
- NY: 2 (40%)
- LONG: 4 (80%)
- SHORT: 1 (20%)

## Day-by-Day Detail

### 2026-02-16
- API calls: 4 | Trades: 0 | L2 rejected: 4 | Limit blocked: 0

### 2026-02-17
- API calls: 3 | Trades: 1 | L2 rejected: 0 | Limit blocked: 2
  - ny 2026-02-17T15:00 → SHORT entry=74.85 SL=75.55 TP1=73.80 → **LOSS** -1.0R

### 2026-02-18
- API calls: 2 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-19
- API calls: 6 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-20
- API calls: 14 | Trades: 1 | L2 rejected: 0 | Limit blocked: 9
  - london 2026-02-20T08:00 → LONG entry=78.59 SL=77.23 TP1=80.62 → **WIN** 1.5R

### 2026-02-23
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-24
- API calls: 6 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-25
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-26
- API calls: 2 | Trades: 1 | L2 rejected: 0 | Limit blocked: 1
  - london 2026-02-26T07:00 → LONG entry=78.59 SL=77.14 TP1=80.77 → **WIN** 1.5R

### 2026-02-27
- API calls: 17 | Trades: 2 | L2 rejected: 0 | Limit blocked: 14
  - london 2026-02-27T07:00 → LONG entry=87.32 SL=86.08 TP1=89.18 → **WIN** 1.5R
  - ny 2026-02-27T13:00 → LONG entry=88.93 SL=88.10 TP1=90.18 → **WIN** 1.5R

### 2026-03-02
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

## T7 vs P2A v1 Decision Comparison

- Both CANDIDATE: 0
- T7 CANDIDATE, P2A NO_TRADE: 5
- T7 NO_TRADE, P2A CANDIDATE: 0

## Caveats

- **SL-first on wide candles:** If both SL and TP are hit in one M15 candle, SL wins (conservative bias).
- **No spread simulation:** Entry prices are AI-quoted, no spread added.
- **No tick data:** Outcome determined by M15 OHLC only, not intra-candle sequence.
- **KB context empty:** Production passes last-10-trade context; simulation does not.
