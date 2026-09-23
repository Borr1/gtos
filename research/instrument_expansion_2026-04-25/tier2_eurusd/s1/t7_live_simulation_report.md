# T7 Production-Faithful Simulation Report
**Dates:** 2026-01-02 to 2026-01-15
**Total KZ candles:** 230
**Total API cost:** $4.02
**Batch reference:** T7: CR=86.7%, WR=66.3%, +39.5R (n=121, no L2); P2A v1: CR=38%, WR=69.6% (n=104)

**Production gates simulated:** prescreen, deterministic bias, skip_first_ny,
L2 verification, inverted TP auto-correction, max 2 trades/day, max 1 trade/KZ.

## Summary by Instrument

| Symbol | KZ Candles | API Calls | T7 CAND | L2 Reject | Limit Block | Final Trades | CR (raw) | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|--------|-----------|-----------|---------|-----------|-------------|-------------|----------|-----------|------|--------|----|---------|-----------|
| EURUSD   |       230 |        72 |      29 |        24 |           4 |           1 |    40.3% |      1.4% |    1 |      0 | 100% |   +1.5R | +1.500R |

## Pipeline Funnel

- Total KZ candles: 230
- Skipped (prescreen D1/H4): 100
- Skipped (no bias): 0
- Skipped (OB proximity): 58
- Skipped (first NY candle): 0
- Sent to API: 72
- AI returned CANDIDATE: 29 (raw CR: 40.3%)
  - Inverted TP corrected: 0
  - L2 Rejected: 24
  - PA parse failed → NO_TRADE: 0 (production would retry then reject)
  - Blocked by trade limits: 4
- **Final CANDIDATE decisions: 1** (live CR: 1.4%)

## Monthly Breakdown

| Month | API Calls | Raw CAND | Final Trades | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|-------|-----------|----------|-------------|-----------|------|--------|----|---------|-----------|
| 2026-01 |        72 |       29 |           1 |      1.4% |    1 |      0 | 100% |   +1.5R | +1.500R |

## Risk Metrics

- Total resolved trades: 1
- Win rate: 100.0%
- Expectancy per trade: +1.500R
- Total R: +1.5R
- Max consecutive losses: 0
- Max drawdown: 0.0R
- Trades per week: 0.5
- Trades per month: 1.0

## Trade Distribution

- London: 1 (100%)
- NY: 0 (0%)
- LONG: 0 (0%)
- SHORT: 1 (100%)

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
- API calls: 12 | Trades: 1 | L2 rejected: 7 | Limit blocked: 4
  - london 2026-01-07T09:30 → SHORT entry=1.17 SL=1.17 TP1=1.17 → **WIN** 1.5R

### 2026-01-08
- API calls: 10 | Trades: 0 | L2 rejected: 10 | Limit blocked: 0

### 2026-01-09
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-01-12
- API calls: 30 | Trades: 0 | L2 rejected: 1 | Limit blocked: 0

### 2026-01-13
- API calls: 20 | Trades: 0 | L2 rejected: 6 | Limit blocked: 0

## T7 vs P2A v1 Decision Comparison

- Both CANDIDATE: 0
- T7 CANDIDATE, P2A NO_TRADE: 1
- T7 NO_TRADE, P2A CANDIDATE: 0

## Caveats

- **SL-first on wide candles:** If both SL and TP are hit in one M15 candle, SL wins (conservative bias).
- **No spread simulation:** Entry prices are AI-quoted, no spread added.
- **No tick data:** Outcome determined by M15 OHLC only, not intra-candle sequence.
- **KB context empty:** Production passes last-10-trade context; simulation does not.
