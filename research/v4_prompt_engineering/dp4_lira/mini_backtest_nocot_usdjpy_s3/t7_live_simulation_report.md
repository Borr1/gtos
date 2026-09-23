# T7 Production-Faithful Simulation Report
**Dates:** 2026-02-21 to 2026-03-17
**Total KZ candles:** 250
**Total API cost:** $3.01
**Batch reference:** T7: CR=86.7%, WR=66.3%, +39.5R (n=121, no L2); P2A v1: CR=38%, WR=69.6% (n=104)

**Production gates simulated:** prescreen, deterministic bias, skip_first_ny,
L2 verification, inverted TP auto-correction, max 2 trades/day, max 1 trade/KZ.

## Summary by Instrument

| Symbol | KZ Candles | API Calls | T7 CAND | L2 Reject | Limit Block | Final Trades | CR (raw) | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|--------|-----------|-----------|---------|-----------|-------------|-------------|----------|-----------|------|--------|----|---------|-----------|
| USDJPY   |       250 |       154 |     148 |        36 |         103 |           9 |    96.1% |      5.8% |    5 |      0 | 100% |   +7.5R | +1.500R |

## Pipeline Funnel

- Total KZ candles: 250
- Skipped (prescreen D1/H4): 96
- Skipped (no bias): 0
- Skipped (OB proximity): 0
- Skipped (first NY candle): 0
- Sent to API: 154
- AI returned CANDIDATE: 148 (raw CR: 96.1%)
  - Inverted TP corrected: 0
  - L2 Rejected: 36
  - PA parse failed → NO_TRADE: 0 (production would retry then reject)
  - Blocked by trade limits: 103
- **Final CANDIDATE decisions: 9** (live CR: 5.8%)
  - ⚠ Entry limit never filled (unfilled): 4 — excluded from WR/expectancy

## Monthly Breakdown

| Month | API Calls | Raw CAND | Final Trades | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|-------|-----------|----------|-------------|-----------|------|--------|----|---------|-----------|
| 2026-02 |        64 |       60 |           4 |      6.2% |    1 |      0 | 100% |   +1.5R | +1.500R |
| 2026-03 |        90 |       88 |           5 |      5.6% |    4 |      0 | 100% |   +6.0R | +1.500R |

## Risk Metrics

- ⚠ Unfilled (entry limit never reached): 4 — excluded from all metrics below
- Total resolved trades: 5
- Win rate: 100.0%
- Expectancy per trade: +1.500R
- Total R: +7.5R
- Max consecutive losses: 0
- Max drawdown: 0.0R
- Trades per week: 1.4
- Trades per month: 5.0

## Trade Distribution

- London: 4 (44%)
- NY: 0 (0%)
- LONG: 9 (100%)
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
- API calls: 32 | Trades: 2 | L2 rejected: 1 | Limit blocked: 29
  - tokyo 2026-02-26T00:00 → LONG entry=155.80 SL=155.54 TP1=156.18 → **WIN** 1.5R
  - london 2026-02-26T07:00 → LONG entry=155.19 SL=154.96 TP1=155.53 → **UNFILLED** ?R

### 2026-02-27
- API calls: 32 | Trades: 2 | L2 rejected: 6 | Limit blocked: 20
  - tokyo 2026-02-27T00:00 → LONG entry=155.19 SL=154.94 TP1=155.56 → **UNFILLED** ?R
  - london 2026-02-27T07:00 → LONG entry=155.19 SL=154.94 TP1=155.56 → **UNFILLED** ?R

### 2026-03-02
- API calls: 32 | Trades: 2 | L2 rejected: 8 | Limit blocked: 22
  - tokyo 2026-03-02T00:00 → LONG entry=155.19 SL=154.94 TP1=155.56 → **UNFILLED** ?R
  - london 2026-03-02T07:00 → LONG entry=156.60 SL=156.15 TP1=157.28 → **WIN** 1.5R

### 2026-03-03
- API calls: 32 | Trades: 2 | L2 rejected: 7 | Limit blocked: 22
  - tokyo 2026-03-03T00:00 → LONG entry=157.01 SL=156.77 TP1=157.37 → **WIN** 1.5R
  - london 2026-03-03T07:00 → LONG entry=157.01 SL=156.76 TP1=157.38 → **WIN** 1.5R

### 2026-03-04
- API calls: 26 | Trades: 1 | L2 rejected: 14 | Limit blocked: 10
  - tokyo 2026-03-04T00:00 → LONG entry=157.01 SL=156.76 TP1=157.38 → **WIN** 1.5R

## T7 vs P2A v1 Decision Comparison

- Both CANDIDATE: 0
- T7 CANDIDATE, P2A NO_TRADE: 9
- T7 NO_TRADE, P2A CANDIDATE: 0

## Caveats

- **SL-first on wide candles:** If both SL and TP are hit in one M15 candle, SL wins (conservative bias).
- **No spread simulation:** Entry prices are AI-quoted, no spread added.
- **No tick data:** Outcome determined by M15 OHLC only, not intra-candle sequence.
- **KB context empty:** Production passes last-10-trade context; simulation does not.
