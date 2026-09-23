# T7 Production-Faithful Simulation Report
**Dates:** 2026-03-21 to 2026-04-02
**Total KZ candles:** 270
**Total API cost:** $0.81
**Batch reference:** T7: CR=86.7%, WR=66.3%, +39.5R (n=121, no L2); P2A v1: CR=38%, WR=69.6% (n=104)

**Production gates simulated:** prescreen, deterministic bias, skip_first_ny,
L2 verification, inverted TP auto-correction, max 2 trades/day, max 1 trade/KZ.

## Summary by Instrument

| Symbol | KZ Candles | API Calls | T7 CAND | L2 Reject | Limit Block | Final Trades | CR (raw) | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|--------|-----------|-----------|---------|-----------|-------------|-------------|----------|-----------|------|--------|----|---------|-----------|
| XAUUSD   |       270 |        39 |      13 |         7 |           4 |           2 |    33.3% |      5.1% |    2 |      0 | 100% |   +3.0R | +1.500R |

## Pipeline Funnel

- Total KZ candles: 270
- Skipped (prescreen D1/H4): 128
- Skipped (no bias): 0
- Skipped (OB proximity): 94
- Skipped (first NY candle): 9
- Sent to API: 39
- AI returned CANDIDATE: 13 (raw CR: 33.3%)
  - Inverted TP corrected: 0
  - L2 Rejected: 7
  - PA parse failed → NO_TRADE: 0 (production would retry then reject)
  - Blocked by trade limits: 4
- **Final CANDIDATE decisions: 2** (live CR: 5.1%)

## Monthly Breakdown

| Month | API Calls | Raw CAND | Final Trades | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|-------|-----------|----------|-------------|-----------|------|--------|----|---------|-----------|
| 2026-03 |        34 |       13 |           2 |      5.9% |    2 |      0 | 100% |   +3.0R | +1.500R |
| 2026-04 |         5 |        0 |           0 |      0.0% |    0 |      0 |   0% |   +0.0R | +0.000R |

## Risk Metrics

- Total resolved trades: 2
- Win rate: 100.0%
- Expectancy per trade: +1.500R
- Total R: +3.0R
- Max consecutive losses: 0
- Max drawdown: 0.0R
- Trades per week: 1.1
- Trades per month: 2.0

## Trade Distribution

- London: 2 (100%)
- NY: 0 (0%)
- LONG: 0 (0%)
- SHORT: 2 (100%)

## Day-by-Day Detail

### 2026-03-23
- API calls: 6 | Trades: 1 | L2 rejected: 2 | Limit blocked: 1
  - london 2026-03-23T08:00 → SHORT entry=4349.89 SL=4390.76 TP1=4288.52 → **WIN** 1.5R

### 2026-03-24
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-03-25
- API calls: 8 | Trades: 0 | L2 rejected: 2 | Limit blocked: 0

### 2026-03-26
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-03-27
- API calls: 8 | Trades: 1 | L2 rejected: 0 | Limit blocked: 3
  - london 2026-03-27T07:30 → SHORT entry=4511.32 SL=4529.32 TP1=4484.32 → **WIN** 1.5R

### 2026-03-30
- API calls: 12 | Trades: 0 | L2 rejected: 3 | Limit blocked: 0

### 2026-03-31
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-04-01
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-04-02
- API calls: 5 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
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
