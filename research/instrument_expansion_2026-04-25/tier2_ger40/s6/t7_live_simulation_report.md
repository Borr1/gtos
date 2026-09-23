# T7 Production-Faithful Simulation Report
**Dates:** 2026-03-23 to 2026-04-13
**Total KZ candles:** 363
**Total API cost:** $4.02
**Batch reference:** T7: CR=86.7%, WR=66.3%, +39.5R (n=121, no L2); P2A v1: CR=38%, WR=69.6% (n=104)

**Production gates simulated:** prescreen, deterministic bias, skip_first_ny,
L2 verification, inverted TP auto-correction, max 2 trades/day, max 1 trade/KZ.

## Summary by Instrument

| Symbol | KZ Candles | API Calls | T7 CAND | L2 Reject | Limit Block | Final Trades | CR (raw) | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|--------|-----------|-----------|---------|-----------|-------------|-------------|----------|-----------|------|--------|----|---------|-----------|
| GER40    |       363 |        68 |      60 |         7 |          45 |           8 |    88.2% |     11.8% |    4 |      3 |  57% |   +3.0R | +0.429R |

## Pipeline Funnel

- Total KZ candles: 363
- Skipped (prescreen D1/H4): 150
- Skipped (no bias): 0
- Skipped (OB proximity): 145
- Skipped (first NY candle): 0
- Sent to API: 68
- AI returned CANDIDATE: 60 (raw CR: 88.2%)
  - Inverted TP corrected: 0
  - L2 Rejected: 7
  - PA parse failed → NO_TRADE: 0 (production would retry then reject)
  - Blocked by trade limits: 45
- **Final CANDIDATE decisions: 8** (live CR: 11.8%)
  - ⚠ Entry limit never filled (unfilled): 1 — excluded from WR/expectancy

## Monthly Breakdown

| Month | API Calls | Raw CAND | Final Trades | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|-------|-----------|----------|-------------|-----------|------|--------|----|---------|-----------|
| 2026-03 |        65 |       57 |           7 |     10.8% |    4 |      2 |  67% |   +4.0R | +0.667R |
| 2026-04 |         3 |        3 |           1 |     33.3% |    0 |      1 |   0% |   -1.0R | -1.000R |

## Risk Metrics

- ⚠ Unfilled (entry limit never reached): 1 — excluded from all metrics below
- Total resolved trades: 7
- Win rate: 57.1%
- Expectancy per trade: +0.429R
- Total R: +3.0R
- Max consecutive losses: 1
- Max drawdown: 1.0R
- Trades per week: 2.2
- Trades per month: 7.0

## Trade Distribution

- London: 4 (50%)
- NY: 4 (50%)
- LONG: 8 (100%)
- SHORT: 0 (0%)

## Day-by-Day Detail

### 2026-03-23
- API calls: 2 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-03-24
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-03-25
- API calls: 17 | Trades: 2 | L2 rejected: 0 | Limit blocked: 15
  - london 2026-03-25T07:00 → LONG entry=22662.60 SL=22536.80 TP1=22851.30 → **LOSS** -1.0R
  - ny 2026-03-25T13:00 → LONG entry=22883.50 SL=22807.00 TP1=22998.30 → **WIN** 1.5R

### 2026-03-26
- API calls: 18 | Trades: 2 | L2 rejected: 0 | Limit blocked: 12
  - london 2026-03-26T07:00 → LONG entry=22662.60 SL=22546.60 TP1=22836.60 → **LOSS** -1.0R
  - ny 2026-03-26T14:30 → LONG entry=21975.90 SL=21837.70 TP1=22183.20 → **WIN** 1.5R

### 2026-03-27
- API calls: 2 | Trades: 1 | L2 rejected: 0 | Limit blocked: 1
  - ny 2026-03-27T13:15 → LONG entry=21975.90 SL=21835.70 TP1=22186.20 → **WIN** 1.5R

### 2026-03-30
- API calls: 12 | Trades: 1 | L2 rejected: 7 | Limit blocked: 3
  - ny 2026-03-30T15:00 → LONG entry=22373.30 SL=22207.50 TP1=22621.60 → **WIN** 1.5R

### 2026-03-31
- API calls: 14 | Trades: 1 | L2 rejected: 0 | Limit blocked: 12
  - london 2026-03-31T07:00 → LONG entry=22430.40 SL=22325.50 TP1=22587.70 → **UNFILLED** ?R

### 2026-04-01
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-04-02
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-04-07
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-04-08
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-04-09
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-04-10
- API calls: 3 | Trades: 1 | L2 rejected: 0 | Limit blocked: 2
  - london 2026-04-10T07:00 → LONG entry=23729.30 SL=23651.40 TP1=23846.30 → **LOSS** -1.0R

## T7 vs P2A v1 Decision Comparison

- Both CANDIDATE: 0
- T7 CANDIDATE, P2A NO_TRADE: 8
- T7 NO_TRADE, P2A CANDIDATE: 0

## Caveats

- **SL-first on wide candles:** If both SL and TP are hit in one M15 candle, SL wins (conservative bias).
- **No spread simulation:** Entry prices are AI-quoted, no spread added.
- **No tick data:** Outcome determined by M15 OHLC only, not intra-candle sequence.
- **KB context empty:** Production passes last-10-trade context; simulation does not.
