# T7 Production-Faithful Simulation Report
**Dates:** 2026-04-14 to 2026-04-24
**Total KZ candles:** 120
**Total API cost:** $2.61
**Batch reference:** T7: CR=86.7%, WR=66.3%, +39.5R (n=121, no L2); P2A v1: CR=38%, WR=69.6% (n=104)

**Production gates simulated:** prescreen, deterministic bias, skip_first_ny,
L2 verification, inverted TP auto-correction, max 2 trades/day, max 1 trade/KZ.

## Summary by Instrument

| Symbol | KZ Candles | API Calls | T7 CAND | L2 Reject | Limit Block | Final Trades | CR (raw) | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|--------|-----------|-----------|---------|-----------|-------------|-------------|----------|-----------|------|--------|----|---------|-----------|
| NAS100   |       120 |        44 |      32 |         0 |          27 |           5 |    72.7% |     11.4% |    1 |      1 |  50% |   +0.5R | +0.250R |

## Pipeline Funnel

- Total KZ candles: 120
- Skipped (prescreen D1/H4): 30
- Skipped (no bias): 0
- Skipped (OB proximity): 46
- Skipped (first NY candle): 0
- Sent to API: 44
- AI returned CANDIDATE: 32 (raw CR: 72.7%)
  - Inverted TP corrected: 0
  - L2 Rejected: 0
  - PA parse failed → NO_TRADE: 0 (production would retry then reject)
  - Blocked by trade limits: 27
- **Final CANDIDATE decisions: 5** (live CR: 11.4%)
  - ⚠ Entry limit never filled (unfilled): 3 — excluded from WR/expectancy

## Monthly Breakdown

| Month | API Calls | Raw CAND | Final Trades | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|-------|-----------|----------|-------------|-----------|------|--------|----|---------|-----------|
| 2026-04 |        44 |       32 |           5 |     11.4% |    1 |      1 |  50% |   +0.5R | +0.250R |

## Risk Metrics

- ⚠ Unfilled (entry limit never reached): 3 — excluded from all metrics below
- Total resolved trades: 2
- Win rate: 50.0%
- Expectancy per trade: +0.250R
- Total R: +0.5R
- Max consecutive losses: 1
- Max drawdown: 1.0R
- Trades per week: 1.3
- Trades per month: 2.0

## Trade Distribution

- London: 2 (40%)
- NY: 3 (60%)
- LONG: 5 (100%)
- SHORT: 0 (0%)

## Day-by-Day Detail

### 2026-04-14
- API calls: 18 | Trades: 2 | L2 rejected: 0 | Limit blocked: 16
  - london 2026-04-14T10:00 → LONG entry=25436.50 SL=25396.80 TP1=25496.10 → **UNFILLED** ?R
  - ny 2026-04-14T13:00 → LONG entry=25436.50 SL=25397.00 TP1=25495.80 → **UNFILLED** ?R

### 2026-04-15
- API calls: 8 | Trades: 1 | L2 rejected: 0 | Limit blocked: 3
  - ny 2026-04-15T16:00 → LONG entry=25842.50 SL=25783.80 TP1=25930.40 → **WIN** 1.5R

### 2026-04-16
- API calls: 18 | Trades: 2 | L2 rejected: 0 | Limit blocked: 8
  - london 2026-04-16T09:00 → LONG entry=26283.70 SL=26241.70 TP1=26346.70 → **LOSS** -1.0R
  - ny 2026-04-16T14:15 → LONG entry=25842.50 SL=25784.20 TP1=25929.80 → **UNFILLED** ?R

### 2026-04-17
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

## T7 vs P2A v1 Decision Comparison

- Both CANDIDATE: 0
- T7 CANDIDATE, P2A NO_TRADE: 5
- T7 NO_TRADE, P2A CANDIDATE: 0

## Caveats

- **SL-first on wide candles:** If both SL and TP are hit in one M15 candle, SL wins (conservative bias).
- **No spread simulation:** Entry prices are AI-quoted, no spread added.
- **No tick data:** Outcome determined by M15 OHLC only, not intra-candle sequence.
- **KB context empty:** Production passes last-10-trade context; simulation does not.
