# T7 Production-Faithful Simulation Report
**Dates:** 2026-03-01 to 2026-04-13
**Total KZ candles:** 930
**Total API cost:** $4.78
**Batch reference:** T7: CR=86.7%, WR=66.3%, +39.5R (n=121, no L2); P2A v1: CR=38%, WR=69.6% (n=104)

**Production gates simulated:** prescreen, deterministic bias, skip_first_ny,
L2 verification, inverted TP auto-correction, max 2 trades/day, max 1 trade/KZ.

## Summary by Instrument

| Symbol | KZ Candles | API Calls | T7 CAND | L2 Reject | Limit Block | Final Trades | CR (raw) | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|--------|-----------|-----------|---------|-----------|-------------|-------------|----------|-----------|------|--------|----|---------|-----------|
| EURUSD   |       930 |       164 |      18 |        15 |           1 |           2 |    11.0% |      1.2% |    1 |      1 |  50% |   +0.3R | +0.165R |

## Pipeline Funnel

- Total KZ candles: 930
- Skipped (prescreen D1/H4): 714
- Skipped (no bias): 0
- Skipped (OB proximity): 52
- Skipped (first NY candle): 0
- Sent to API: 164
- AI returned CANDIDATE: 18 (raw CR: 11.0%)
  - Inverted TP corrected: 0
  - L2 Rejected: 15
  - PA parse failed → NO_TRADE: 0 (production would retry then reject)
  - Blocked by trade limits: 1
- **Final CANDIDATE decisions: 2** (live CR: 1.2%)

## Monthly Breakdown

| Month | API Calls | Raw CAND | Final Trades | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|-------|-----------|----------|-------------|-----------|------|--------|----|---------|-----------|
| 2026-03 |       164 |       18 |           2 |      1.2% |    1 |      1 |  50% |   +0.3R | +0.165R |
| 2026-04 |         0 |        0 |           0 |      0.0% |    0 |      0 |   0% |   +0.0R | +0.000R |

## Risk Metrics

- Total resolved trades: 2
- Win rate: 50.0%
- Expectancy per trade: +0.165R
- Total R: +0.3R
- Max consecutive losses: 1
- Max drawdown: 1.0R
- Trades per week: 0.3
- Trades per month: 1.4

## Trade Distribution

- London: 1 (50%)
- NY: 1 (50%)
- LONG: 0 (0%)
- SHORT: 2 (100%)

## Day-by-Day Detail

### 2026-03-02
- API calls: 26 | Trades: 1 | L2 rejected: 1 | Limit blocked: 1
  - london 2026-03-02T09:00 → SHORT entry=1.18 SL=1.18 TP1=1.18 → **WIN** 1.33R

### 2026-03-03
- API calls: 28 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-03-04
- API calls: 10 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-03-05
- API calls: 16 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-03-06
- API calls: 18 | Trades: 1 | L2 rejected: 0 | Limit blocked: 0
  - ny 2026-03-06T13:45 → SHORT entry=1.16 SL=1.16 TP1=1.16 → **LOSS** -1.0R

### 2026-03-09
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-03-10
- API calls: 26 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-03-11
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-03-12
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-03-13
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-03-16
- API calls: 10 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-03-17
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-03-18
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-03-19
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-03-20
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

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
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-03-27
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-03-30
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-03-31
- API calls: 30 | Trades: 0 | L2 rejected: 14 | Limit blocked: 0

### 2026-04-01
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-04-02
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-04-03
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-04-06
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
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-04-13
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

## T7 vs P2A v1 Decision Comparison

- Both CANDIDATE: 0
- T7 CANDIDATE, P2A NO_TRADE: 2
- T7 NO_TRADE, P2A CANDIDATE: 0

## Caveats

- **SL-first on wide candles:** If both SL and TP are hit in one M15 candle, SL wins (conservative bias).
- **No spread simulation:** Entry prices are AI-quoted, no spread added.
- **No tick data:** Outcome determined by M15 OHLC only, not intra-candle sequence.
- **KB context empty:** Production passes last-10-trade context; simulation does not.
