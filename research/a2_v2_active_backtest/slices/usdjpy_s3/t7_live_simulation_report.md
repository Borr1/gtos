# T7 Production-Faithful Simulation Report
**Dates:** 2026-02-21 to 2026-03-17
**Total KZ candles:** 237
**Total API cost:** $6.04
**Batch reference:** T7: CR=86.7%, WR=66.3%, +39.5R (n=121, no L2); P2A v1: CR=38%, WR=69.6% (n=104)

**Production gates simulated:** prescreen, deterministic bias, skip_first_ny,
L2 verification, inverted TP auto-correction, max 2 trades/day, max 1 trade/KZ.

## Summary by Instrument

| Symbol | KZ Candles | API Calls | T7 CAND | L2 Reject | Limit Block | Final Trades | CR (raw) | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|--------|-----------|-----------|---------|-----------|-------------|-------------|----------|-----------|------|--------|----|---------|-----------|
| USDJPY   |       237 |       141 |     126 |        52 |          67 |           7 |    89.4% |      5.0% |    1 |      1 |  50% |   +0.5R | +0.250R |

## Pipeline Funnel

- Total KZ candles: 237
- Skipped (prescreen D1/H4): 96
- Skipped (no bias): 0
- Skipped (OB proximity): 0
- Skipped (first NY candle): 0
- Sent to API: 141
- AI returned CANDIDATE: 126 (raw CR: 89.4%)
  - Inverted TP corrected: 0
  - L2 Rejected: 52
  - PA parse failed → NO_TRADE: 0 (production would retry then reject)
  - Blocked by trade limits: 67
- **Final CANDIDATE decisions: 7** (live CR: 5.0%)
  - ⚠ Entry limit never filled (unfilled): 5 — excluded from WR/expectancy

## Monthly Breakdown

| Month | API Calls | Raw CAND | Final Trades | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|-------|-----------|----------|-------------|-----------|------|--------|----|---------|-----------|
| 2026-02 |        64 |       52 |           4 |      6.2% |    0 |      0 |   0% |   +0.0R | +0.000R |
| 2026-03 |        77 |       74 |           3 |      3.9% |    1 |      1 |  50% |   +0.5R | +0.250R |

## Risk Metrics

- ⚠ Unfilled (entry limit never reached): 5 — excluded from all metrics below
- Total resolved trades: 2
- Win rate: 50.0%
- Expectancy per trade: +0.250R
- Total R: +0.5R
- Max consecutive losses: 1
- Max drawdown: 1.0R
- Trades per week: 0.6
- Trades per month: 2.0

## Trade Distribution

- London: 3 (43%)
- NY: 1 (14%)
- LONG: 7 (100%)
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
- API calls: 32 | Trades: 2 | L2 rejected: 3 | Limit blocked: 25
  - tokyo 2026-02-26T00:15 → LONG entry=155.19 SL=154.92 TP1=155.60 → **UNFILLED** ?R
  - london 2026-02-26T07:00 → LONG entry=155.19 SL=154.91 TP1=155.61 → **UNFILLED** ?R

### 2026-02-27
- API calls: 32 | Trades: 2 | L2 rejected: 2 | Limit blocked: 18
  - tokyo 2026-02-27T00:30 → LONG entry=155.19 SL=154.92 TP1=155.59 → **UNFILLED** ?R
  - london 2026-02-27T07:00 → LONG entry=155.19 SL=154.91 TP1=155.60 → **UNFILLED** ?R

### 2026-03-02
- API calls: 32 | Trades: 2 | L2 rejected: 10 | Limit blocked: 20
  - tokyo 2026-03-02T00:00 → LONG entry=155.19 SL=154.92 TP1=155.59 → **UNFILLED** ?R
  - london 2026-03-02T07:00 → LONG entry=156.60 SL=156.15 TP1=157.28 → **WIN** 1.5R

### 2026-03-03
- API calls: 32 | Trades: 1 | L2 rejected: 24 | Limit blocked: 4
  - ny 2026-03-03T13:00 → LONG entry=157.48 SL=157.12 TP1=158.01 → **LOSS** -1.0R

### 2026-03-04
- API calls: 13 | Trades: 0 | L2 rejected: 13 | Limit blocked: 0

## T7 vs P2A v1 Decision Comparison

- Both CANDIDATE: 0
- T7 CANDIDATE, P2A NO_TRADE: 7
- T7 NO_TRADE, P2A CANDIDATE: 0

## Caveats

- **SL-first on wide candles:** If both SL and TP are hit in one M15 candle, SL wins (conservative bias).
- **No spread simulation:** Entry prices are AI-quoted, no spread added.
- **No tick data:** Outcome determined by M15 OHLC only, not intra-candle sequence.
- **KB context empty:** Production passes last-10-trade context; simulation does not.
