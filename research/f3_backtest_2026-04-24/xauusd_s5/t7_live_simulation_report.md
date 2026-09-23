# T7 Production-Faithful Simulation Report
**Dates:** 2026-02-23 to 2026-03-07
**Total KZ candles:** 300
**Total API cost:** $4.24
**Batch reference:** T7: CR=86.7%, WR=66.3%, +39.5R (n=121, no L2); P2A v1: CR=38%, WR=69.6% (n=104)

**Production gates simulated:** prescreen, deterministic bias, skip_first_ny,
L2 verification, inverted TP auto-correction, max 2 trades/day, max 1 trade/KZ.

## Summary by Instrument

| Symbol | KZ Candles | API Calls | T7 CAND | L2 Reject | Limit Block | Final Trades | CR (raw) | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|--------|-----------|-----------|---------|-----------|-------------|-------------|----------|-----------|------|--------|----|---------|-----------|
| XAUUSD   |       300 |        99 |      65 |        46 |          16 |           3 |    65.7% |      3.0% |    0 |      2 |   0% |   -2.0R | -1.000R |

## Pipeline Funnel

- Total KZ candles: 300
- Skipped (prescreen D1/H4): 18
- Skipped (no bias): 0
- Skipped (OB proximity): 173
- Skipped (first NY candle): 10
- Sent to API: 99
- AI returned CANDIDATE: 65 (raw CR: 65.7%)
  - Inverted TP corrected: 0
  - L2 Rejected: 46
  - PA parse failed → NO_TRADE: 0 (production would retry then reject)
  - Blocked by trade limits: 16
- **Final CANDIDATE decisions: 3** (live CR: 3.0%)
  - ⚠ Entry limit never filled (unfilled): 1 — excluded from WR/expectancy

## Monthly Breakdown

| Month | API Calls | Raw CAND | Final Trades | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|-------|-----------|----------|-------------|-----------|------|--------|----|---------|-----------|
| 2026-02 |        34 |       22 |           0 |      0.0% |    0 |      0 |   0% |   +0.0R | +0.000R |
| 2026-03 |        65 |       43 |           3 |      4.6% |    0 |      2 |   0% |   -2.0R | -1.000R |

## Risk Metrics

- ⚠ Unfilled (entry limit never reached): 1 — excluded from all metrics below
- Total resolved trades: 2
- Win rate: 0.0%
- Expectancy per trade: -1.000R
- Total R: -2.0R
- Max consecutive losses: 2
- Max drawdown: 2.0R
- Trades per week: 1.1
- Trades per month: 2.0

## Trade Distribution

- London: 1 (33%)
- NY: 2 (67%)
- LONG: 2 (67%)
- SHORT: 1 (33%)

## Day-by-Day Detail

### 2026-02-23
- API calls: 4 | Trades: 0 | L2 rejected: 4 | Limit blocked: 0

### 2026-02-24
- API calls: 12 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-25
- API calls: 14 | Trades: 0 | L2 rejected: 14 | Limit blocked: 0

### 2026-02-26
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-27
- API calls: 4 | Trades: 0 | L2 rejected: 4 | Limit blocked: 0

### 2026-03-02
- API calls: 21 | Trades: 2 | L2 rejected: 0 | Limit blocked: 16
  - london 2026-03-02T09:00 → LONG entry=5366.74 SL=5337.41 TP1=5410.74 → **LOSS** -1.0R
  - ny 2026-03-02T13:15 → LONG entry=5366.74 SL=5337.79 TP1=5410.09 → **LOSS** -1.0R

### 2026-03-03
- API calls: 20 | Trades: 1 | L2 rejected: 7 | Limit blocked: 0
  - ny 2026-03-03T13:15 → SHORT entry=5305.78 SL=5336.84 TP1=5259.20 → **UNFILLED** ?R

### 2026-03-04
- API calls: 16 | Trades: 0 | L2 rejected: 16 | Limit blocked: 0

### 2026-03-05
- API calls: 8 | Trades: 0 | L2 rejected: 1 | Limit blocked: 0

### 2026-03-06
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

## T7 vs P2A v1 Decision Comparison

- Both CANDIDATE: 0
- T7 CANDIDATE, P2A NO_TRADE: 3
- T7 NO_TRADE, P2A CANDIDATE: 0

## Caveats

- **SL-first on wide candles:** If both SL and TP are hit in one M15 candle, SL wins (conservative bias).
- **No spread simulation:** Entry prices are AI-quoted, no spread added.
- **No tick data:** Outcome determined by M15 OHLC only, not intra-candle sequence.
- **KB context empty:** Production passes last-10-trade context; simulation does not.
