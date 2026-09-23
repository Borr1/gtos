# Phase 1: Trade Index Analyses — 2026-04-04 10:14

## 1A: Monte Carlo Equity Curve

### Combined (129 trades)
- Win Rate: 62.8% | Mean R: 0.2776 | PF: 1.9421
- Kelly Full: 19.82% | Half-Kelly: 9.91%

| Risk % | P(+8% before -5%) | P(+8% before -10%) | P(DD>5%) | P(DD>10%) | Median Final | 5th pct | 95th pct | Max Consec Loss (95th) | Median to +3% |
|--------|-------------------|-------------------|----------|-----------|-------------|---------|---------|----------------------|---------------|
| 0.5% | 87.9% | 88.7% | 3.7% | 0.0% | $114,493 | $104,265 | $126,529 | 7 | 19 |
| 0.75% | 87.8% | 95.7% | 24.6% | 0.5% | $122,277 | $106,101 | $142,203 | 6 | 12 |
| 1.0% | 81.4% | 97.3% | 52.7% | 3.5% | $130,501 | $108,392 | $159,186 | 6 | 9 |
| 1.25% | 76.3% | 96.6% | 76.1% | 10.0% | $139,848 | $111,298 | $178,512 | 7 | 7 |
| 1.5% | 69.3% | 94.0% | 90.0% | 22.9% | $148,534 | $112,242 | $198,820 | 6 | 6 |
| 2.0% | 63.4% | 89.7% | 99.0% | 50.4% | $169,037 | $116,634 | $247,998 | 6 | 5 |

### Block Bootstrap (autocorrelation check at 1.0% risk)
- i.i.d. P(+8% before -5%): 81.4%
- Block P(+8% before -5%): 78.9%
- Difference: -2.53pp
- Autocorrelation detected: NO

### XAUUSD Only (105 trades)
- Win Rate: 61.9% | Mean R: 0.204 | PF: 1.6916
- Kelly Full: 15.51% | Half-Kelly: 7.76%

| Risk % | P(+8% before -5%) | P(+8% before -10%) | P(DD>5%) | Median Final |
|--------|-------------------|-------------------|----------|-------------|
| 0.5% | 72.2% | 73.0% | 7.9% | $110,392 |
| 0.75% | 77.5% | 87.0% | 34.6% | $115,799 |
| 1.0% | 71.9% | 91.2% | 64.1% | $121,434 |
| 1.25% | 66.0% | 90.5% | 83.8% | $127,189 |
| 1.5% | 61.1% | 88.6% | 94.1% | $133,517 |
| 2.0% | 56.1% | 83.9% | 99.5% | $145,480 |

## 1B: Rolling Edge Stability
- Total 20-trade windows: 110
- Negative expectancy windows: 9
- Best window: 2025-03-05 to 2025-05-06 (Total R: 17.2, WR: 80.0%)
- Worst window: 2025-12-23 to 2026-01-21 (Total R: -2.75, WR: 50.0%)

### First Half vs Second Half
| Half | N | WR | Mean R | Total R |
|------|---|-----|--------|---------|
| First | 64 | 67.2% | 0.3717 | 23.79 |
| Second | 65 | 58.5% | 0.1849 | 12.02 |

## 1C: Trade Autocorrelation
- Binary lag-1: -0.0333
- Binary lag-2: -0.0471
- R-multiple lag-1: 0.1933
- Runs test: z=0, p=1 → random
- Longest win streak: 10 | Longest loss streak: 5

## 1D: Drawdown Analysis
- Final equity (R-units): 35.81
- Max drawdown: 6.02R over 21 trades
- At 1% risk on $100K: max DD = 5.89% ($7,741)
- EXCEEDS 5% prop firm limit
- WITHIN 10% prop firm limit

## 1E: Day-of-Week × Kill Zone
| Cell | N | WR | Mean R | Total R | Low N? |
|------|---|-----|--------|---------|--------|
| Fri_london | 8 | 62.5% | -0.1263 | -1.01 | ⚠️ |
| Fri_ny | 16 | 50.0% | 0.0306 | 0.49 |  |
| Mon_london | 14 | 78.6% | 0.5236 | 7.33 |  |
| Mon_ny | 10 | 50.0% | 0.127 | 1.27 |  |
| Thu_london | 12 | 58.3% | 0.2783 | 3.34 |  |
| Thu_ny | 10 | 50.0% | 0.363 | 3.63 |  |
| Tue_london | 14 | 78.6% | 0.5343 | 7.48 |  |
| Tue_ny | 19 | 73.7% | 0.5121 | 9.73 |  |
| Wed_london | 13 | 61.5% | 0.1962 | 2.55 |  |
| Wed_ny | 13 | 46.2% | 0.0769 | 1.0 |  |

- Best vs Worst DOW Fisher exact p: 0.1003
- Significant: NO

## 1F: Trade Timing
- Mean gap between trades: 7.7 days
- Longest dry spell: 106 days
- Avg trades/month: 5.2
- Zero-trade months: 5/25
