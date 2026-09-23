# T7 Production-Faithful Simulation Report
**Dates:** 2026-01-16 to 2026-01-31
**Total KZ candles:** 98
**Total API cost:** $4.03
**Batch reference:** T7: CR=86.7%, WR=66.3%, +39.5R (n=121, no L2); P2A v1: CR=38%, WR=69.6% (n=104)

**Production gates simulated:** prescreen, deterministic bias, skip_first_ny,
L2 verification, inverted TP auto-correction, max 2 trades/day, max 1 trade/KZ.

## Summary by Instrument

| Symbol | KZ Candles | API Calls | T7 CAND | L2 Reject | Limit Block | Final Trades | CR (raw) | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|--------|-----------|-----------|---------|-----------|-------------|-------------|----------|-----------|------|--------|----|---------|-----------|
| EURUSD   |        98 |        72 |       6 |         6 |           0 |           0 |     8.3% |      0.0% |    0 |      0 |   0% |   +0.0R | +0.000R |

## Pipeline Funnel

- Total KZ candles: 98
- Skipped (prescreen D1/H4): 0
- Skipped (no bias): 0
- Skipped (OB proximity): 26
- Skipped (first NY candle): 0
- Sent to API: 72
- AI returned CANDIDATE: 6 (raw CR: 8.3%)
  - Inverted TP corrected: 0
  - L2 Rejected: 6
  - PA parse failed → NO_TRADE: 0 (production would retry then reject)
  - Blocked by trade limits: 0
- **Final CANDIDATE decisions: 0** (live CR: 0.0%)

## Monthly Breakdown

| Month | API Calls | Raw CAND | Final Trades | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|-------|-----------|----------|-------------|-----------|------|--------|----|---------|-----------|
| 2026-01 |        72 |        6 |           0 |      0.0% |    0 |      0 |   0% |   +0.0R | +0.000R |

## Trade Distribution


## Day-by-Day Detail

### 2026-01-16
- API calls: 4 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-01-19
- API calls: 30 | Trades: 0 | L2 rejected: 4 | Limit blocked: 0

### 2026-01-20
- API calls: 30 | Trades: 0 | L2 rejected: 2 | Limit blocked: 0

### 2026-01-21
- API calls: 8 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
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
