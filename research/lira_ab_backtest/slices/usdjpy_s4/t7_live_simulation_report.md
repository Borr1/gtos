# T7 Production-Faithful Simulation Report
**Dates:** 2026-03-18 to 2026-04-13
**Total KZ candles:** 406
**Total API cost:** $6.01
**Batch reference:** T7: CR=86.7%, WR=66.3%, +39.5R (n=121, no L2); P2A v1: CR=38%, WR=69.6% (n=104)

**Production gates simulated:** prescreen, deterministic bias, skip_first_ny,
L2 verification, inverted TP auto-correction, max 2 trades/day, max 1 trade/KZ.

## Summary by Instrument

| Symbol | KZ Candles | API Calls | T7 CAND | L2 Reject | Limit Block | Final Trades | CR (raw) | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|--------|-----------|-----------|---------|-----------|-------------|-------------|----------|-----------|------|--------|----|---------|-----------|
| USDJPY   |       406 |       230 |      98 |        30 |          59 |           9 |    42.6% |      3.9% |    2 |      7 |  22% |   -4.0R | -0.444R |

## Pipeline Funnel

- Total KZ candles: 406
- Skipped (prescreen D1/H4): 52
- Skipped (no bias): 0
- Skipped (OB proximity): 124
- Skipped (first NY candle): 0
- Sent to API: 230
- AI returned CANDIDATE: 98 (raw CR: 42.6%)
  - Inverted TP corrected: 0
  - L2 Rejected: 30
  - PA parse failed → NO_TRADE: 0 (production would retry then reject)
  - Blocked by trade limits: 59
- **Final CANDIDATE decisions: 9** (live CR: 3.9%)

## Monthly Breakdown

| Month | API Calls | Raw CAND | Final Trades | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|-------|-----------|----------|-------------|-----------|------|--------|----|---------|-----------|
| 2026-03 |       196 |       79 |           7 |      3.6% |    2 |      5 |  29% |   -2.0R | -0.286R |
| 2026-04 |        34 |       19 |           2 |      5.9% |    0 |      2 |   0% |   -2.0R | -1.000R |

## Risk Metrics

- Total resolved trades: 9
- Win rate: 22.2%
- Expectancy per trade: -0.444R
- Total R: -4.0R
- Max consecutive losses: 3
- Max drawdown: 4.0R
- Trades per week: 2.3
- Trades per month: 9.0

## Trade Distribution

- London: 4 (44%)
- NY: 2 (22%)
- LONG: 9 (100%)
- SHORT: 0 (0%)

## Day-by-Day Detail

### 2026-03-18
- API calls: 12 | Trades: 0 | L2 rejected: 1 | Limit blocked: 0

### 2026-03-19
- API calls: 22 | Trades: 2 | L2 rejected: 3 | Limit blocked: 17
  - tokyo 2026-03-19T00:00 → LONG entry=159.54 SL=159.20 TP1=160.05 → **LOSS** -1.0R
  - london 2026-03-19T07:45 → LONG entry=159.11 SL=158.85 TP1=159.50 → **LOSS** -1.0R

### 2026-03-20
- API calls: 20 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-03-23
- API calls: 12 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-03-24
- API calls: 32 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-03-25
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-03-26
- API calls: 12 | Trades: 1 | L2 rejected: 2 | Limit blocked: 5
  - ny 2026-03-26T14:00 → LONG entry=159.55 SL=159.38 TP1=159.80 → **WIN** 1.5R

### 2026-03-27
- API calls: 32 | Trades: 1 | L2 rejected: 5 | Limit blocked: 9
  - ny 2026-03-27T13:00 → LONG entry=159.59 SL=159.33 TP1=159.98 → **LOSS** -1.0R

### 2026-03-30
- API calls: 32 | Trades: 1 | L2 rejected: 11 | Limit blocked: 5
  - london 2026-03-30T08:00 → LONG entry=159.59 SL=159.38 TP1=159.91 → **LOSS** -1.0R

### 2026-03-31
- API calls: 22 | Trades: 2 | L2 rejected: 0 | Limit blocked: 14
  - tokyo 2026-03-31T00:00 → LONG entry=159.50 SL=159.28 TP1=159.83 → **LOSS** -1.0R
  - london 2026-03-31T07:00 → LONG entry=159.50 SL=159.37 TP1=159.70 → **WIN** 1.5R

### 2026-04-01
- API calls: 12 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-04-02
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-04-03
- API calls: 22 | Trades: 2 | L2 rejected: 8 | Limit blocked: 9
  - tokyo 2026-04-03T00:00 → LONG entry=158.76 SL=158.53 TP1=159.10 → **LOSS** -1.0R
  - london 2026-04-03T07:30 → LONG entry=158.76 SL=158.50 TP1=159.14 → **LOSS** -1.0R

## T7 vs P2A v1 Decision Comparison

- Both CANDIDATE: 0
- T7 CANDIDATE, P2A NO_TRADE: 9
- T7 NO_TRADE, P2A CANDIDATE: 0

## Caveats

- **SL-first on wide candles:** If both SL and TP are hit in one M15 candle, SL wins (conservative bias).
- **No spread simulation:** Entry prices are AI-quoted, no spread added.
- **No tick data:** Outcome determined by M15 OHLC only, not intra-candle sequence.
- **KB context empty:** Production passes last-10-trade context; simulation does not.
