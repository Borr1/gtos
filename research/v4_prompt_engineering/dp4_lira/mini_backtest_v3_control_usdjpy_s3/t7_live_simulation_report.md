# T7 Production-Faithful Simulation Report
**Dates:** 2026-02-21 to 2026-03-17
**Total KZ candles:** 167
**Total API cost:** $3.02
**Batch reference:** T7: CR=86.7%, WR=66.3%, +39.5R (n=121, no L2); P2A v1: CR=38%, WR=69.6% (n=104)

**Production gates simulated:** prescreen, deterministic bias, skip_first_ny,
L2 verification, inverted TP auto-correction, max 2 trades/day, max 1 trade/KZ.

## Summary by Instrument

| Symbol | KZ Candles | API Calls | T7 CAND | L2 Reject | Limit Block | Final Trades | CR (raw) | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|--------|-----------|-----------|---------|-----------|-------------|-------------|----------|-----------|------|--------|----|---------|-----------|
| USDJPY   |       167 |        71 |      61 |         8 |          48 |           5 |    85.9% |      7.0% |    1 |      0 | 100% |   +1.5R | +1.500R |

## Pipeline Funnel

- Total KZ candles: 167
- Skipped (prescreen D1/H4): 96
- Skipped (no bias): 0
- Skipped (OB proximity): 0
- Skipped (first NY candle): 0
- Sent to API: 71
- AI returned CANDIDATE: 61 (raw CR: 85.9%)
  - Inverted TP corrected: 0
  - L2 Rejected: 8
  - PA parse failed → NO_TRADE: 0 (production would retry then reject)
  - Blocked by trade limits: 48
- **Final CANDIDATE decisions: 5** (live CR: 7.0%)
  - ⚠ Entry limit never filled (unfilled): 4 — excluded from WR/expectancy

## Monthly Breakdown

| Month | API Calls | Raw CAND | Final Trades | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|-------|-----------|----------|-------------|-----------|------|--------|----|---------|-----------|
| 2026-02 |        64 |       54 |           4 |      6.2% |    1 |      0 | 100% |   +1.5R | +1.500R |
| 2026-03 |         7 |        7 |           1 |     14.3% |    0 |      0 |   0% |   +0.0R | +0.000R |

## Risk Metrics

- ⚠ Unfilled (entry limit never reached): 4 — excluded from all metrics below
- Total resolved trades: 1
- Win rate: 100.0%
- Expectancy per trade: +1.500R
- Total R: +1.5R
- Max consecutive losses: 0
- Max drawdown: 0.0R
- Trades per week: 0.3
- Trades per month: 1.0

## Trade Distribution

- London: 2 (40%)
- NY: 0 (0%)
- LONG: 5 (100%)
- SHORT: 0 (0%)

## Day-by-Day Detail

### 2026-02-23
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-24
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-25
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-26
- API calls: 32 | Trades: 2 | L2 rejected: 6 | Limit blocked: 24
  - tokyo 2026-02-26T00:00 → LONG entry=155.80 SL=155.55 TP1=156.18 → **WIN** 1.5R
  - london 2026-02-26T07:00 → LONG entry=155.19 SL=154.91 TP1=155.61 → **UNFILLED** ?R

### 2026-02-27
- API calls: 32 | Trades: 2 | L2 rejected: 1 | Limit blocked: 19
  - tokyo 2026-02-27T00:30 → LONG entry=155.19 SL=154.73 TP1=155.88 → **UNFILLED** ?R
  - london 2026-02-27T07:00 → LONG entry=155.19 SL=154.91 TP1=155.60 → **UNFILLED** ?R

### 2026-03-02
- API calls: 7 | Trades: 1 | L2 rejected: 1 | Limit blocked: 5
  - tokyo 2026-03-02T00:00 → LONG entry=155.19 SL=154.93 TP1=155.58 → **UNFILLED** ?R

## T7 vs P2A v1 Decision Comparison

- Both CANDIDATE: 0
- T7 CANDIDATE, P2A NO_TRADE: 5
- T7 NO_TRADE, P2A CANDIDATE: 0

## Caveats

- **SL-first on wide candles:** If both SL and TP are hit in one M15 candle, SL wins (conservative bias).
- **No spread simulation:** Entry prices are AI-quoted, no spread added.
- **No tick data:** Outcome determined by M15 OHLC only, not intra-candle sequence.
- **KB context empty:** Production passes last-10-trade context; simulation does not.
