# T7 Production-Faithful Simulation Report
**Dates:** 2026-02-16 to 2026-03-02
**Total KZ candles:** 115
**Total API cost:** $4.05
**Batch reference:** T7: CR=86.7%, WR=66.3%, +39.5R (n=121, no L2); P2A v1: CR=38%, WR=69.6% (n=104)

**Production gates simulated:** prescreen, deterministic bias, skip_first_ny,
L2 verification, inverted TP auto-correction, max 2 trades/day, max 1 trade/KZ.

## Summary by Instrument

| Symbol | KZ Candles | API Calls | T7 CAND | L2 Reject | Limit Block | Final Trades | CR (raw) | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|--------|-----------|-----------|---------|-----------|-------------|-------------|----------|-----------|------|--------|----|---------|-----------|
| NAS100   |       115 |        70 |      24 |         4 |          16 |           4 |    34.3% |      5.7% |    0 |      4 |   0% |   -4.0R | -1.000R |

## Pipeline Funnel

- Total KZ candles: 115
- Skipped (prescreen D1/H4): 0
- Skipped (no bias): 0
- Skipped (OB proximity): 45
- Skipped (first NY candle): 0
- Sent to API: 70
- AI returned CANDIDATE: 24 (raw CR: 34.3%)
  - Inverted TP corrected: 0
  - L2 Rejected: 4
  - PA parse failed → NO_TRADE: 0 (production would retry then reject)
  - Blocked by trade limits: 16
- **Final CANDIDATE decisions: 4** (live CR: 5.7%)

## Monthly Breakdown

| Month | API Calls | Raw CAND | Final Trades | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|-------|-----------|----------|-------------|-----------|------|--------|----|---------|-----------|
| 2026-02 |        70 |       24 |           4 |      5.7% |    0 |      4 |   0% |   -4.0R | -1.000R |

## Risk Metrics

- Total resolved trades: 4
- Win rate: 0.0%
- Expectancy per trade: -1.000R
- Total R: -4.0R
- Max consecutive losses: 4
- Max drawdown: 4.0R
- Trades per week: 1.9
- Trades per month: 4.0

## Trade Distribution

- London: 2 (50%)
- NY: 2 (50%)
- LONG: 4 (100%)
- SHORT: 0 (0%)

## Day-by-Day Detail

### 2026-02-16
- API calls: 29 | Trades: 2 | L2 rejected: 0 | Limit blocked: 12
  - london 2026-02-16T10:00 → LONG entry=24759.10 SL=24706.50 TP1=24837.90 → **LOSS** -1.0R
  - ny 2026-02-16T13:00 → LONG entry=24759.10 SL=24707.50 TP1=24836.50 → **LOSS** -1.0R

### 2026-02-17
- API calls: 12 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-02-18
- API calls: 18 | Trades: 2 | L2 rejected: 4 | Limit blocked: 4
  - london 2026-02-18T10:00 → LONG entry=24780.20 SL=24722.30 TP1=24867.10 → **LOSS** -1.0R
  - ny 2026-02-18T13:00 → LONG entry=24780.20 SL=24706.50 TP1=24890.70 → **LOSS** -1.0R

### 2026-02-19
- API calls: 11 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

## T7 vs P2A v1 Decision Comparison

- Both CANDIDATE: 0
- T7 CANDIDATE, P2A NO_TRADE: 4
- T7 NO_TRADE, P2A CANDIDATE: 0

## Caveats

- **SL-first on wide candles:** If both SL and TP are hit in one M15 candle, SL wins (conservative bias).
- **No spread simulation:** Entry prices are AI-quoted, no spread added.
- **No tick data:** Outcome determined by M15 OHLC only, not intra-candle sequence.
- **KB context empty:** Production passes last-10-trade context; simulation does not.
