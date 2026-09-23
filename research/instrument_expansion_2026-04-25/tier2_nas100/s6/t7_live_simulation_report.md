# T7 Production-Faithful Simulation Report
**Dates:** 2026-03-23 to 2026-04-13
**Total KZ candles:** 234
**Total API cost:** $4.02
**Batch reference:** T7: CR=86.7%, WR=66.3%, +39.5R (n=121, no L2); P2A v1: CR=38%, WR=69.6% (n=104)

**Production gates simulated:** prescreen, deterministic bias, skip_first_ny,
L2 verification, inverted TP auto-correction, max 2 trades/day, max 1 trade/KZ.

## Summary by Instrument

| Symbol | KZ Candles | API Calls | T7 CAND | L2 Reject | Limit Block | Final Trades | CR (raw) | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|--------|-----------|-----------|---------|-----------|-------------|-------------|----------|-----------|------|--------|----|---------|-----------|
| NAS100   |       234 |        70 |      22 |        12 |           8 |           2 |    31.4% |      2.9% |    0 |      2 |   0% |   -2.0R | -1.000R |

## Pipeline Funnel

- Total KZ candles: 234
- Skipped (prescreen D1/H4): 30
- Skipped (no bias): 0
- Skipped (OB proximity): 134
- Skipped (first NY candle): 0
- Sent to API: 70
- AI returned CANDIDATE: 22 (raw CR: 31.4%)
  - Inverted TP corrected: 0
  - L2 Rejected: 12
  - PA parse failed → NO_TRADE: 0 (production would retry then reject)
  - Blocked by trade limits: 8
- **Final CANDIDATE decisions: 2** (live CR: 2.9%)

## Monthly Breakdown

| Month | API Calls | Raw CAND | Final Trades | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|-------|-----------|----------|-------------|-----------|------|--------|----|---------|-----------|
| 2026-03 |        54 |       22 |           2 |      3.7% |    0 |      2 |   0% |   -2.0R | -1.000R |
| 2026-04 |        16 |        0 |           0 |      0.0% |    0 |      0 |   0% |   +0.0R | +0.000R |

## Risk Metrics

- Total resolved trades: 2
- Win rate: 0.0%
- Expectancy per trade: -1.000R
- Total R: -2.0R
- Max consecutive losses: 2
- Max drawdown: 2.0R
- Trades per week: 0.6
- Trades per month: 2.0

## Trade Distribution

- London: 1 (50%)
- NY: 1 (50%)
- LONG: 0 (0%)
- SHORT: 2 (100%)

## Day-by-Day Detail

### 2026-03-23
- API calls: 11 | Trades: 1 | L2 rejected: 0 | Limit blocked: 5
  - london 2026-03-23T09:00 → SHORT entry=23792.20 SL=23823.50 TP1=23745.30 → **LOSS** -1.0R

### 2026-03-24
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-03-25
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-03-26
- API calls: 15 | Trades: 0 | L2 rejected: 5 | Limit blocked: 0

### 2026-03-27
- API calls: 25 | Trades: 1 | L2 rejected: 7 | Limit blocked: 3
  - ny 2026-03-27T13:30 → SHORT entry=23719.60 SL=23803.10 TP1=23594.40 → **LOSS** -1.0R

### 2026-03-30
- API calls: 0 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-03-31
- API calls: 3 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
  - (no candidates)

### 2026-04-01
- API calls: 16 | Trades: 0 | L2 rejected: 0 | Limit blocked: 0
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
