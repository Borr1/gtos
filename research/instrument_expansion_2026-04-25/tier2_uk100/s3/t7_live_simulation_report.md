# T7 Production-Faithful Simulation Report
**Dates:** 2026-02-01 to 2026-02-15
**Total KZ candles:** 122
**Total API cost:** $4.02
**Batch reference:** T7: CR=86.7%, WR=66.3%, +39.5R (n=121, no L2); P2A v1: CR=38%, WR=69.6% (n=104)

**Production gates simulated:** prescreen, deterministic bias, skip_first_ny,
L2 verification, inverted TP auto-correction, max 2 trades/day, max 1 trade/KZ.

## Summary by Instrument

| Symbol | KZ Candles | API Calls | T7 CAND | L2 Reject | Limit Block | Final Trades | CR (raw) | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|--------|-----------|-----------|---------|-----------|-------------|-------------|----------|-----------|------|--------|----|---------|-----------|
| UK100    |       122 |        69 |      44 |         7 |          32 |           5 |    63.8% |      7.2% |    2 |      3 |  40% |   +0.0R | +0.000R |

## Pipeline Funnel

- Total KZ candles: 122
- Skipped (prescreen D1/H4): 0
- Skipped (no bias): 0
- Skipped (OB proximity): 53
- Skipped (first NY candle): 0
- Sent to API: 69
- AI returned CANDIDATE: 44 (raw CR: 63.8%)
  - Inverted TP corrected: 0
  - L2 Rejected: 7
  - PA parse failed → NO_TRADE: 0 (production would retry then reject)
  - Blocked by trade limits: 32
- **Final CANDIDATE decisions: 5** (live CR: 7.2%)

## Monthly Breakdown

| Month | API Calls | Raw CAND | Final Trades | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|-------|-----------|----------|-------------|-----------|------|--------|----|---------|-----------|
| 2026-02 |        69 |       44 |           5 |      7.2% |    2 |      3 |  40% |   +0.0R | +0.000R |

## Risk Metrics

- Total resolved trades: 5
- Win rate: 40.0%
- Expectancy per trade: +0.000R
- Total R: +0.0R
- Max consecutive losses: 2
- Max drawdown: 2.0R
- Trades per week: 2.3
- Trades per month: 5.0

## Trade Distribution

- London: 3 (60%)
- NY: 2 (40%)
- LONG: 5 (100%)
- SHORT: 0 (0%)

## Day-by-Day Detail

### 2026-02-02
- API calls: 16 | Trades: 0 | L2 rejected: 5 | Limit blocked: 0

### 2026-02-03
- API calls: 24 | Trades: 2 | L2 rejected: 2 | Limit blocked: 9
  - london 2026-02-03T10:00 → LONG entry=10332.90 SL=10309.50 TP1=10368.00 → **LOSS** -1.0R
  - ny 2026-02-03T14:15 → LONG entry=10142.80 SL=10115.40 TP1=10184.00 → **WIN** 1.5R

### 2026-02-04
- API calls: 15 | Trades: 2 | L2 rejected: 0 | Limit blocked: 12
  - london 2026-02-04T09:00 → LONG entry=10320.20 SL=10301.10 TP1=10348.90 → **WIN** 1.5R
  - ny 2026-02-04T18:30 → LONG entry=10320.20 SL=10299.70 TP1=10350.90 → **LOSS** -1.0R

### 2026-02-05
- API calls: 14 | Trades: 1 | L2 rejected: 0 | Limit blocked: 11
  - london 2026-02-05T08:00 → LONG entry=10320.20 SL=10300.70 TP1=10349.50 → **LOSS** -1.0R

## T7 vs P2A v1 Decision Comparison

- Both CANDIDATE: 0
- T7 CANDIDATE, P2A NO_TRADE: 5
- T7 NO_TRADE, P2A CANDIDATE: 0

## Caveats

- **SL-first on wide candles:** If both SL and TP are hit in one M15 candle, SL wins (conservative bias).
- **No spread simulation:** Entry prices are AI-quoted, no spread added.
- **No tick data:** Outcome determined by M15 OHLC only, not intra-candle sequence.
- **KB context empty:** Production passes last-10-trade context; simulation does not.
