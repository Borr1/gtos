# T7 Production-Faithful Simulation Report
**Dates:** 2026-04-14 to 2026-04-24
**Total KZ candles:** 162
**Total API cost:** $4.03
**Batch reference:** T7: CR=86.7%, WR=66.3%, +39.5R (n=121, no L2); P2A v1: CR=38%, WR=69.6% (n=104)

**Production gates simulated:** prescreen, deterministic bias, skip_first_ny,
L2 verification, inverted TP auto-correction, max 2 trades/day, max 1 trade/KZ.

## Summary by Instrument

| Symbol | KZ Candles | API Calls | T7 CAND | L2 Reject | Limit Block | Final Trades | CR (raw) | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|--------|-----------|-----------|---------|-----------|-------------|-------------|----------|-----------|------|--------|----|---------|-----------|
| UK100    |       162 |        70 |      42 |         1 |          36 |           5 |    60.0% |      7.1% |    3 |      2 |  60% |   +2.5R | +0.500R |

## Pipeline Funnel

- Total KZ candles: 162
- Skipped (prescreen D1/H4): 0
- Skipped (no bias): 0
- Skipped (OB proximity): 92
- Skipped (first NY candle): 0
- Sent to API: 70
- AI returned CANDIDATE: 42 (raw CR: 60.0%)
  - Inverted TP corrected: 0
  - L2 Rejected: 1
  - PA parse failed → NO_TRADE: 0 (production would retry then reject)
  - Blocked by trade limits: 36
- **Final CANDIDATE decisions: 5** (live CR: 7.1%)

## Monthly Breakdown

| Month | API Calls | Raw CAND | Final Trades | CR (live) | Wins | Losses | WR | Total R | Exp/trade |
|-------|-----------|----------|-------------|-----------|------|--------|----|---------|-----------|
| 2026-04 |        70 |       42 |           5 |      7.1% |    3 |      2 |  60% |   +2.5R | +0.500R |

## Risk Metrics

- Total resolved trades: 5
- Win rate: 60.0%
- Expectancy per trade: +0.500R
- Total R: +2.5R
- Max consecutive losses: 1
- Max drawdown: 1.0R
- Trades per week: 3.2
- Trades per month: 5.0

## Trade Distribution

- London: 3 (60%)
- NY: 2 (40%)
- LONG: 5 (100%)
- SHORT: 0 (0%)

## Day-by-Day Detail

### 2026-04-14
- API calls: 4 | Trades: 1 | L2 rejected: 0 | Limit blocked: 3
  - ny 2026-04-14T18:00 → LONG entry=10608.60 SL=10558.80 TP1=10683.30 → **LOSS** -1.0R

### 2026-04-15
- API calls: 12 | Trades: 1 | L2 rejected: 0 | Limit blocked: 0
  - london 2026-04-15T08:00 → LONG entry=10393.00 SL=10365.20 TP1=10434.70 → **WIN** 1.5R

### 2026-04-16
- API calls: 12 | Trades: 1 | L2 rejected: 0 | Limit blocked: 8
  - london 2026-04-16T08:00 → LONG entry=10393.00 SL=10365.60 TP1=10434.10 → **WIN** 1.5R

### 2026-04-17
- API calls: 24 | Trades: 1 | L2 rejected: 0 | Limit blocked: 15
  - ny 2026-04-17T15:00 → LONG entry=10579.30 SL=10549.00 TP1=10624.70 → **WIN** 1.5R

### 2026-04-20
- API calls: 18 | Trades: 1 | L2 rejected: 1 | Limit blocked: 10
  - london 2026-04-20T08:00 → LONG entry=10579.30 SL=10552.30 TP1=10619.80 → **LOSS** -1.0R

## T7 vs P2A v1 Decision Comparison

- Both CANDIDATE: 0
- T7 CANDIDATE, P2A NO_TRADE: 5
- T7 NO_TRADE, P2A CANDIDATE: 0

## Caveats

- **SL-first on wide candles:** If both SL and TP are hit in one M15 candle, SL wins (conservative bias).
- **No spread simulation:** Entry prices are AI-quoted, no spread added.
- **No tick data:** Outcome determined by M15 OHLC only, not intra-candle sequence.
- **KB context empty:** Production passes last-10-trade context; simulation does not.
