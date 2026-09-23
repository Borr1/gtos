# T7 Production-Faithful Simulation Report
**Dates:** 2026-02-16 to 2026-03-02
**Total KZ candles:** 91
**Total API cost:** $4.00
**Batch reference:** T7: CR=86.7%, WR=66.3%, +39.5R (n=121, no L2); P2A v1: CR=38%, WR=69.6% (n=104)

**Production gates simulated:** prescreen, deterministic bias, skip_first_ny,
L2 verification, inverted TP auto-correction, max 2 trades/day, max 1 trade/KZ.

## Summary by Instrument

| Symbol | KZ Candles | API Calls | T7 CAND | L2 Reject | Limit Block | Final Trades | CR (raw) | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|--------|-----------|-----------|---------|-----------|-------------|-------------|----------|-----------|------|--------|----|---------|-----------|
| GER40    |        91 |        69 |      53 |         2 |          45 |           6 |    76.8% |      8.7% |    3 |      3 |  50% |   +1.5R | +0.250R |

## Pipeline Funnel

- Total KZ candles: 91
- Skipped (prescreen D1/H4): 0
- Skipped (no bias): 0
- Skipped (OB proximity): 22
- Skipped (first NY candle): 0
- Sent to API: 69
- AI returned CANDIDATE: 53 (raw CR: 76.8%)
  - Inverted TP corrected: 0
  - L2 Rejected: 2
  - PA parse failed → NO_TRADE: 0 (production would retry then reject)
  - Blocked by trade limits: 45
- **Final CANDIDATE decisions: 6** (live CR: 8.7%)

## Monthly Breakdown

| Month | API Calls | Raw CAND | Final Trades | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|-------|-----------|----------|-------------|-----------|------|--------|----|---------|-----------|
| 2026-02 |        69 |       53 |           6 |      8.7% |    3 |      3 |  50% |   +1.5R | +0.250R |

## Risk Metrics

- Total resolved trades: 6
- Win rate: 50.0%
- Expectancy per trade: +0.250R
- Total R: +1.5R
- Max consecutive losses: 3
- Max drawdown: 3.0R
- Trades per week: 2.8
- Trades per month: 6.0

## Trade Distribution

- London: 4 (67%)
- NY: 2 (33%)
- LONG: 6 (100%)
- SHORT: 0 (0%)

## Day-by-Day Detail

### 2026-02-16
- API calls: 12 | Trades: 1 | L2 rejected: 2 | Limit blocked: 3
  - london 2026-02-16T09:00 → LONG entry=24950.20 SL=24904.20 TP1=25019.20 → **LOSS** -1.0R

### 2026-02-17
- API calls: 26 | Trades: 2 | L2 rejected: 0 | Limit blocked: 17
  - london 2026-02-17T07:30 → LONG entry=24531.60 SL=24375.30 TP1=24766.00 → **LOSS** -1.0R
  - ny 2026-02-17T13:00 → LONG entry=24531.60 SL=24373.10 TP1=24769.40 → **LOSS** -1.0R

### 2026-02-18
- API calls: 30 | Trades: 2 | L2 rejected: 0 | Limit blocked: 25
  - london 2026-02-18T07:00 → LONG entry=25028.10 SL=25000.00 TP1=25070.30 → **WIN** 1.5R
  - ny 2026-02-18T13:00 → LONG entry=25028.10 SL=25000.30 TP1=25069.80 → **WIN** 1.5R

### 2026-02-19
- API calls: 1 | Trades: 1 | L2 rejected: 0 | Limit blocked: 0
  - london 2026-02-19T07:00 → LONG entry=25028.10 SL=25000.90 TP1=25069.00 → **WIN** 1.5R

## T7 vs P2A v1 Decision Comparison

- Both CANDIDATE: 0
- T7 CANDIDATE, P2A NO_TRADE: 6
- T7 NO_TRADE, P2A CANDIDATE: 0

## Caveats

- **SL-first on wide candles:** If both SL and TP are hit in one M15 candle, SL wins (conservative bias).
- **No spread simulation:** Entry prices are AI-quoted, no spread added.
- **No tick data:** Outcome determined by M15 OHLC only, not intra-candle sequence.
- **KB context empty:** Production passes last-10-trade context; simulation does not.
