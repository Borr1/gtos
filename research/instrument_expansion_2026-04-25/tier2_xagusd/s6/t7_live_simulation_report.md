# T7 Production-Faithful Simulation Report
**Dates:** 2026-03-23 to 2026-04-13
**Total KZ candles:** 450
**Total API cost:** $3.89
**Batch reference:** T7: CR=86.7%, WR=66.3%, +39.5R (n=121, no L2); P2A v1: CR=38%, WR=69.6% (n=104)

**Production gates simulated:** prescreen, deterministic bias, skip_first_ny,
L2 verification, inverted TP auto-correction, max 2 trades/day, max 1 trade/KZ.

## Summary by Instrument

| Symbol | KZ Candles | API Calls | T7 CAND | L2 Reject | Limit Block | Final Trades | CR (raw) | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|--------|-----------|-----------|---------|-----------|-------------|-------------|----------|-----------|------|--------|----|---------|-----------|
| XAGUSD   |       450 |        67 |      45 |         4 |          32 |           9 |    67.2% |     13.4% |    6 |      2 |  75% |   +7.0R | +0.874R |

## Pipeline Funnel

- Total KZ candles: 450
- Skipped (prescreen D1/H4): 42
- Skipped (no bias): 0
- Skipped (OB proximity): 341
- Skipped (first NY candle): 0
- Sent to API: 67
- AI returned CANDIDATE: 45 (raw CR: 67.2%)
  - Inverted TP corrected: 1
  - L2 Rejected: 4
  - PA parse failed → NO_TRADE: 0 (production would retry then reject)
  - Blocked by trade limits: 32
- **Final CANDIDATE decisions: 9** (live CR: 13.4%)
  - ⚠ Entry limit never filled (unfilled): 1 — excluded from WR/expectancy

## Monthly Breakdown

| Month | API Calls | Raw CAND | Final Trades | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|-------|-----------|----------|-------------|-----------|------|--------|----|---------|-----------|
| 2026-03 |        28 |       14 |           3 |     10.7% |    3 |      0 | 100% |   +4.5R | +1.500R |
| 2026-04 |        39 |       31 |           6 |     15.4% |    3 |      2 |  60% |   +2.5R | +0.498R |

## Risk Metrics

- ⚠ Unfilled (entry limit never reached): 1 — excluded from all metrics below
- Total resolved trades: 8
- Win rate: 75.0%
- Expectancy per trade: +0.874R
- Total R: +7.0R
- Max consecutive losses: 2
- Max drawdown: 2.0R
- Trades per week: 2.5
- Trades per month: 8.0

## Trade Distribution

- London: 3 (33%)
- NY: 6 (67%)
- LONG: 7 (78%)
- SHORT: 2 (22%)

## Day-by-Day Detail

### 2026-03-23
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-03-24
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-03-25
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-03-26
- API calls: 5 | Trades: 1 | L2 rejected: 2 | Limit blocked: 1
  - london 2026-03-26T08:15 → SHORT entry=71.15 SL=72.11 TP1=69.72 → **WIN** 1.5R

### 2026-03-27
- API calls: 19 | Trades: 1 | L2 rejected: 2 | Limit blocked: 3
  - ny 2026-03-27T13:30 → SHORT entry=69.04 SL=69.28 TP1=68.69 → **WIN** 1.5R

### 2026-03-30
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-03-31
- API calls: 4 | Trades: 1 | L2 rejected: 0 | Limit blocked: 3
  - ny 2026-03-31T16:00 → LONG entry=73.47 SL=72.39 TP1=75.09 → **WIN** 1.5R

### 2026-04-01
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-04-02
- API calls: 2 | Trades: 1 | L2 rejected: 0 | Limit blocked: 1
  - london 2026-04-02T07:00 → LONG entry=69.99 SL=69.18 TP1=71.20 → **WIN** 1.5R

### 2026-04-06
- API calls: 12 | Trades: 1 | L2 rejected: 0 | Limit blocked: 11
  - ny 2026-04-06T13:00 → LONG entry=70.98 SL=69.83 TP1=72.70 → **WIN** 1.49R

### 2026-04-07
- API calls: 4 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-04-08
- API calls: 15 | Trades: 2 | L2 rejected: 0 | Limit blocked: 9
  - london 2026-04-08T08:00 → LONG entry=76.40 SL=75.85 TP1=77.23 → **LOSS** -1.0R
  - ny 2026-04-08T13:00 → LONG entry=76.40 SL=75.87 TP1=77.20 → **LOSS** -1.0R

### 2026-04-09
- API calls: 4 | Trades: 1 | L2 rejected: 0 | Limit blocked: 3
  - ny 2026-04-09T14:00 → LONG entry=74.23 SL=73.43 TP1=75.43 → **WIN** 1.5R

### 2026-04-10
- API calls: 2 | Trades: 1 | L2 rejected: 0 | Limit blocked: 1
  - ny 2026-04-10T16:00 → LONG entry=72.19 SL=71.12 TP1=73.80 → **UNFILLED** ?R

### 2026-04-13
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
