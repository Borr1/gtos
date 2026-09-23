# T7 Production-Faithful Simulation Report
**Dates:** 2026-02-10 to 2026-02-22
**Total KZ candles:** 270
**Total API cost:** $0.29
**Batch reference:** T7: CR=86.7%, WR=66.3%, +39.5R (n=121, no L2); P2A v1: CR=38%, WR=69.6% (n=104)

**Production gates simulated:** prescreen, deterministic bias, skip_first_ny,
L2 verification, inverted TP auto-correction, max 2 trades/day, max 1 trade/KZ.

## Summary by Instrument

| Symbol | KZ Candles | API Calls | T7 CAND | L2 Reject | Limit Block | Final Trades | CR (raw) | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|--------|-----------|-----------|---------|-----------|-------------|-------------|----------|-----------|------|--------|----|---------|-----------|
| XAUUSD   |       270 |         7 |       1 |         1 |           0 |           0 |    14.3% |      0.0% |    0 |      0 |   0% |   +0.0R | +0.000R |

## Pipeline Funnel

- Total KZ candles: 270
- Skipped (prescreen D1/H4): 198
- Skipped (no bias): 0
- Skipped (OB proximity): 56
- Skipped (first NY candle): 9
- Sent to API: 7
- AI returned CANDIDATE: 1 (raw CR: 14.3%)
  - Inverted TP corrected: 0
  - L2 Rejected: 1
  - PA parse failed → NO_TRADE: 0 (production would retry then reject)
  - Blocked by trade limits: 0
- **Final CANDIDATE decisions: 0** (live CR: 0.0%)

## Monthly Breakdown

| Month | API Calls | Raw CAND | Final Trades | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|-------|-----------|----------|-------------|-----------|------|--------|----|---------|-----------|
| 2026-02 |         7 |        1 |           0 |      0.0% |    0 |      0 |   0% |   +0.0R | +0.000R |

## Trade Distribution


## Day-by-Day Detail

### 2026-02-10
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-11
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-12
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-13
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-16
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-17
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-18
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-19
- API calls: 7 | Trades: 0 | L2 rejected: 1 | Limit blocked: 0

### 2026-02-20
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

## T7 vs P2A v1 Decision Comparison

- Both CANDIDATE: 0
- T7 CANDIDATE, P2A NO_TRADE: 0
- T7 NO_TRADE, P2A CANDIDATE: 0

## Caveats

- **SL-first on wide candles:** If both SL and TP are hit in one M15 candle, SL wins (conservative bias).
- **No spread simulation:** Entry prices are AI-quoted, no spread added.
- **No tick data:** Outcome determined by M15 OHLC only, not intra-candle sequence.
- **KB context empty:** Production passes last-10-trade context; simulation does not.
