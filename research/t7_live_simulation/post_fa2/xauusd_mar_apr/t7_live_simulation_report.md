# T7 Production-Faithful Simulation Report
**Dates:** 2026-03-01 to 2026-04-13
**Total KZ candles:** 900
**Total API cost:** $10.65
**Batch reference:** T7: CR=86.7%, WR=66.3%, +39.5R (n=121, no L2); P2A v1: CR=38%, WR=69.6% (n=104)

**Production gates simulated:** prescreen, deterministic bias, skip_first_ny,
L2 verification, inverted TP auto-correction, max 2 trades/day, max 1 trade/KZ.

## Summary by Instrument

| Symbol | KZ Candles | API Calls | T7 CAND | L2 Reject | Limit Block | Final Trades | CR (raw) | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|--------|-----------|-----------|---------|-----------|-------------|-------------|----------|-----------|------|--------|----|---------|-----------|
| XAUUSD   |       900 |       349 |     101 |        24 |          58 |          19 |    28.9% |      5.4% |    3 |     15 |  17% |  -10.5R | -0.583R |

## Pipeline Funnel

- Total KZ candles: 900
- Skipped (prescreen D1/H4): 29
- Skipped (no bias): 0
- Skipped (OB proximity): 492
- Skipped (first NY candle): 30
- Sent to API: 349
- AI returned CANDIDATE: 101 (raw CR: 28.9%)
  - Inverted TP corrected: 0
  - L2 Rejected: 24
  - PA parse failed → NO_TRADE: 0 (production would retry then reject)
  - Blocked by trade limits: 58
- **Final CANDIDATE decisions: 19** (live CR: 5.4%)
  - ⚠ Entry limit never filled (unfilled): 1 — excluded from WR/expectancy

## Monthly Breakdown

| Month | API Calls | Raw CAND | Final Trades | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|-------|-----------|----------|-------------|-----------|------|--------|----|---------|-----------|
| 2026-03 |       237 |       47 |           8 |      3.4% |    2 |      5 |  29% |   -2.0R | -0.286R |
| 2026-04 |       112 |       54 |          11 |      9.8% |    1 |     10 |   9% |   -8.5R | -0.773R |

## Risk Metrics

- ⚠ Unfilled (entry limit never reached): 1 — excluded from all metrics below
- Total resolved trades: 18
- Win rate: 16.7%
- Expectancy per trade: -0.583R
- Total R: -10.5R
- Max consecutive losses: 8
- Max drawdown: 12.0R
- Trades per week: 2.9
- Trades per month: 12.5

## Trade Distribution

- London: 7 (37%)
- NY: 12 (63%)
- LONG: 18 (95%)
- SHORT: 1 (5%)

## Day-by-Day Detail

### 2026-03-02
- API calls: 21 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-03-03
- API calls: 20 | Trades: 1 | L2 rejected: 2 | Limit blocked: 0
  - ny 2026-03-03T13:15 → SHORT entry=5305.78 SL=5342.79 TP1=5250.23 → **UNFILLED** ?R

### 2026-03-04
- API calls: 16 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-03-05
- API calls: 8 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-03-06
- API calls: 4 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-03-09
- API calls: 4 | Trades: 1 | L2 rejected: 0 | Limit blocked: 0
  - ny 2026-03-09T16:00 → LONG entry=5111.96 SL=5071.39 TP1=5172.89 → **WIN** 1.5R

### 2026-03-10
- API calls: 4 | Trades: 1 | L2 rejected: 0 | Limit blocked: 0
  - ny 2026-03-10T16:00 → LONG entry=5106.53 SL=5082.34 TP1=5142.82 → **LOSS** -1.0R

### 2026-03-11
- API calls: 4 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-03-12
- API calls: 24 | Trades: 1 | L2 rejected: 4 | Limit blocked: 0
  - ny 2026-03-12T13:45 → LONG entry=5153.69 SL=5130.79 TP1=5188.04 → **LOSS** -1.0R

### 2026-03-13
- API calls: 25 | Trades: 0 | L2 rejected: 12 | Limit blocked: 0

### 2026-03-16
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-03-17
- API calls: 15 | Trades: 2 | L2 rejected: 0 | Limit blocked: 7
  - london 2026-03-17T07:00 → LONG entry=5013.92 SL=4992.22 TP1=5046.42 → **LOSS** -1.0R
  - ny 2026-03-17T14:00 → LONG entry=5029.36 SL=4986.94 TP1=5092.93 → **LOSS** -1.0R

### 2026-03-18
- API calls: 10 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-03-19
- API calls: 2 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-03-20
- API calls: 7 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-03-23
- API calls: 4 | Trades: 0 | L2 rejected: 1 | Limit blocked: 0

### 2026-03-24
- API calls: 11 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-03-25
- API calls: 4 | Trades: 1 | L2 rejected: 0 | Limit blocked: 3
  - ny 2026-03-25T14:00 → LONG entry=4567.30 SL=4518.27 TP1=4640.70 → **LOSS** -1.0R

### 2026-03-26
- API calls: 4 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-03-27
- API calls: 12 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-03-30
- API calls: 12 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-03-31
- API calls: 26 | Trades: 1 | L2 rejected: 0 | Limit blocked: 10
  - ny 2026-03-31T14:00 → LONG entry=4561.59 SL=4521.46 TP1=4621.88 → **WIN** 1.5R

### 2026-04-01
- API calls: 11 | Trades: 2 | L2 rejected: 0 | Limit blocked: 7
  - london 2026-04-01T09:00 → LONG entry=4681.85 SL=4659.35 TP1=4715.63 → **LOSS** -1.0R
  - ny 2026-04-01T13:15 → LONG entry=4681.85 SL=4659.57 TP1=4715.22 → **LOSS** -1.0R

### 2026-04-02
- API calls: 11 | Trades: 1 | L2 rejected: 0 | Limit blocked: 1
  - london 2026-04-02T07:00 → LONG entry=4561.59 SL=4520.66 TP1=4622.98 → **WIN** 1.5R

### 2026-04-06
- API calls: 17 | Trades: 2 | L2 rejected: 2 | Limit blocked: 4
  - london 2026-04-06T10:00 → LONG entry=4678.46 SL=4634.55 TP1=4744.42 → **LOSS** -1.0R
  - ny 2026-04-06T13:15 → LONG entry=4678.46 SL=4643.65 TP1=4730.64 → **LOSS** -1.0R

### 2026-04-07
- API calls: 1 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-04-08
- API calls: 15 | Trades: 2 | L2 rejected: 0 | Limit blocked: 1
  - london 2026-04-08T07:00 → LONG entry=4686.12 SL=4648.54 TP1=4742.49 → **LOSS** -1.0R
  - ny 2026-04-08T14:15 → LONG entry=4686.12 SL=4649.77 TP1=4740.70 → **LOSS** -1.0R

### 2026-04-09
- API calls: 28 | Trades: 2 | L2 rejected: 2 | Limit blocked: 17
  - london 2026-04-09T07:00 → LONG entry=4686.12 SL=4650.77 TP1=4739.20 → **LOSS** -1.0R
  - ny 2026-04-09T14:00 → LONG entry=4686.12 SL=4651.54 TP1=4737.99 → **LOSS** -1.0R

### 2026-04-10
- API calls: 29 | Trades: 2 | L2 rejected: 1 | Limit blocked: 8
  - london 2026-04-10T07:00 → LONG entry=4686.12 SL=4652.25 TP1=4737.00 → **LOSS** -1.0R
  - ny 2026-04-10T14:00 → LONG entry=4686.12 SL=4651.89 TP1=4737.43 → **LOSS** -1.0R

### 2026-04-13
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

## T7 vs P2A v1 Decision Comparison

- Both CANDIDATE: 0
- T7 CANDIDATE, P2A NO_TRADE: 19
- T7 NO_TRADE, P2A CANDIDATE: 0

## Caveats

- **SL-first on wide candles:** If both SL and TP are hit in one M15 candle, SL wins (conservative bias).
- **No spread simulation:** Entry prices are AI-quoted, no spread added.
- **No tick data:** Outcome determined by M15 OHLC only, not intra-candle sequence.
- **KB context empty:** Production passes last-10-trade context; simulation does not.
