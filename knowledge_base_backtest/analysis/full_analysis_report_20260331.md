# COMPREHENSIVE BACKTEST ANALYSIS — XAUUSD AI TRADING AGENT
Generated: 2026-03-31 16:07:39
Total sessions: 174 | Total trades: 91
======================================================================

## 3.1 DATA INTEGRITY REPORT

**Batch3** (Oct 2024 – Mar 2025)
  Sessions evaluated: 49
  Sessions with trades: 25
  Date range: 2024-10-02 to 2025-03-25
  Total weekdays in range: 125
  Pre-screened out (estimated): 76
  Pre-screen pass rate: 39.2%

**Batch4A** (Apr 2025 – Mar 2026)
  Sessions evaluated: 101
  Sessions with trades: 47
  Date range: 2025-04-03 to 2026-03-13
  Total weekdays in range: 247
  Pre-screened out (estimated): 146
  Pre-screen pass rate: 40.9%

**Batch4B** (Apr 2024 – Sep 2024)
  Sessions evaluated: 24
  Sessions with trades: 8
  Date range: 2024-04-01 to 2024-09-30
  Total weekdays in range: 131
  Pre-screened out (estimated): 107
  Pre-screen pass rate: 18.3%

**Combined Totals**
  Total sessions: 174
  Total trades: 91
  Earliest trade: 2024-04-02
  Latest trade: 2026-03-13
  No duplicate dates across canonical batches

**Batch 4B Anomaly Investigation (expected ~95 sessions, got 24):**
  Actual dates processed: 24
  Date range: 2024-04-01 to 2024-09-30
  Monthly distribution: {'2024-04': 11, '2024-05': 1, '2024-06': 2, '2024-07': 4, '2024-08': 4, '2024-09': 2}
  Note: This batch covers Apr-Sep 2024 but only has 24 sessions
  ~126 weekdays in that range → pre-screen pass rate: 19.0%
  This suggests heavy pre-screening OR limited M15 data availability

## 3.2 COMBINED OVERVIEW

Total trades: 91
  Wins: 40  |  Losses: 51  |  Breakeven: 0
  Win rate: 44.0%  (95% CI: [34.2%, 54.2%])
  Total R: +2.93R
  Expectancy: +0.032R per trade  (95% CI: [-0.234R, +0.312R])
  Avg winner: 1.285R  |  Avg loser: 0.950R
  Median winner: 0.980R  |  Median loser: 1.000R
  Profit factor: 1.060
  Max single win: +4.80R  |  Max single loss: -1.00R
  Std dev of R: 1.345
  Payoff ratio: 1.352
  Active months: 16  |  Trades/month: 5.7

## 3.3 FRAMEWORK BREAKDOWN

**equal_sweep**: 1 trades, 0W/1L, WR 0.0%, Total -1.00R, Exp -1.000R, Avg W 0.00R, Avg L 1.00R ⚠️ LOW SAMPLE
**ob_retest**: 9 trades, 9W/0L, WR 100.0%, Total +8.10R, Exp +0.900R, Avg W 0.90R, Avg L 0.00R ⚠️ LOW SAMPLE
**session_sweep**: 81 trades, 31W/50L, WR 38.3%, Total -4.17R, Exp -0.051R, Avg W 1.40R, Avg L 0.95R

## 3.4 KILL ZONE BREAKDOWN (DETAILED)

**LONDON**: 57 trades (23W/34L), WR 40.4%, Total -9.35R, Exp -0.164R
  Avg winner: 1.07R  |  Avg loser: 1.00R
  Best: +3.66R  |  Worst: -1.00R
  Monthly dist: {'2024-04': 3, '2024-08': 1, '2024-10': 1, '2025-01': 1, '2025-02': 7, '2025-03': 8, '2025-04': 3, '2025-06': 4, '2025-09': 2, '2025-10': 7, '2025-12': 2, '2026-01': 9, '2026-02': 4, '2026-03': 5}

**NY**: 34 trades (17W/17L), WR 50.0%, Total +12.28R, Exp +0.361R
  Avg winner: 1.57R  |  Avg loser: 0.85R
  Best: +4.80R  |  Worst: -1.00R
  Monthly dist: {'2024-04': 3, '2024-06': 1, '2024-08': 1, '2024-11': 2, '2025-01': 2, '2025-02': 5, '2025-03': 1, '2025-04': 2, '2025-09': 2, '2025-10': 4, '2025-12': 1, '2026-01': 4, '2026-02': 2, '2026-03': 4}

**London vs NY difference test (Mann-Whitney U):**
  U-statistic: 769.0, p-value: 0.0780
  → Marginally significant at p<0.10

## 3.5 GRADE BREAKDOWN

**A**: 21 trades, 7W/14L, WR 33.3%, Total -2.85R, Exp -0.136R, Avg W 1.53R, Avg L 0.97R
**A+**: 70 trades, 33W/37L, WR 47.1%, Total +5.78R, Exp +0.083R, Avg W 1.23R, Avg L 0.94R

### Grade × Kill Zone

  A + london: 16 trades, WR 31.2%, Exp -0.349R, Total -5.58R
  A + ny: 5 trades, WR 40.0%, Exp +0.546R, Total +2.73R ⚠️ LOW SAMPLE
  A+ + london: 41 trades, WR 43.9%, Exp -0.092R, Total -3.77R
  A+ + ny: 29 trades, WR 51.7%, Exp +0.329R, Total +9.55R

## 3.6 DIRECTION BREAKDOWN

**LONG**: 86 trades, 39W/47L, WR 45.3%, Total +6.46R, Exp +0.075R, Avg W 1.31R, Avg L 0.95R
**SHORT**: 5 trades, 1W/4L, WR 20.0%, Total -3.53R, Exp -0.706R, Avg W 0.47R, Avg L 1.00R ⚠️ LOW SAMPLE

### Direction × Kill Zone

  LONG + london: 55 trades, WR 40.0%, Exp -0.160R, Total -8.82R
  LONG + ny: 31 trades, WR 54.8%, Exp +0.493R, Total +15.28R
  SHORT + london: 2 trades, WR 50.0%, Exp -0.265R, Total -0.53R ⚠️ LOW SAMPLE
  SHORT + ny: 3 trades, WR 0.0%, Exp -1.000R, Total -3.00R ⚠️ LOW SAMPLE

## 3.7 DAY OF WEEK

**Friday**: 16 trades, 8W/8L, WR 50.0%, Total -1.16R, Exp -0.072R, Avg W 0.75R, Avg L 0.89R
**Monday**: 20 trades, 12W/8L, WR 60.0%, Total +7.68R, Exp +0.384R, Avg W 1.31R, Avg L 1.00R
**Thursday**: 19 trades, 8W/11L, WR 42.1%, Total +6.04R, Exp +0.318R, Avg W 2.01R, Avg L 0.91R
**Tuesday**: 18 trades, 8W/10L, WR 44.4%, Total -1.95R, Exp -0.108R, Avg W 1.01R, Avg L 1.00R
**Wednesday**: 18 trades, 4W/14L, WR 22.2%, Total -7.68R, Exp -0.427R, Avg W 1.41R, Avg L 0.95R

## 3.8 MONTHLY PERFORMANCE

  2024-04: 6 trades (3W/3L), -1.17R, Cumulative: -1.17R
  2024-06: 1 trades (1W/0L), +3.08R, Cumulative: +1.91R
  2024-08: 2 trades (1W/1L), +0.59R, Cumulative: +2.50R
  2024-10: 1 trades (0W/1L), -1.00R, Cumulative: +1.50R
  2024-11: 2 trades (1W/1L), +1.05R, Cumulative: +2.55R
  2025-01: 3 trades (1W/2L), +0.20R, Cumulative: +2.75R
  2025-02: 12 trades (4W/8L), -1.79R, Cumulative: +0.96R
  2025-03: 9 trades (4W/5L), +3.31R, Cumulative: +4.27R
  2025-04: 5 trades (2W/3L), +0.94R, Cumulative: +5.21R
  2025-06: 4 trades (2W/2L), +1.90R, Cumulative: +7.11R
  2025-09: 4 trades (0W/4L), -3.55R, Cumulative: +3.56R
  2025-10: 11 trades (9W/2L), +10.64R, Cumulative: +14.20R
  2025-12: 3 trades (1W/2L), -1.36R, Cumulative: +12.84R
  2026-01: 13 trades (6W/7L), -4.08R, Cumulative: +8.76R
  2026-02: 6 trades (3W/3L), -1.60R, Cumulative: +7.16R
  2026-03: 9 trades (2W/7L), -4.23R, Cumulative: +2.93R

  Linear trend: slope=-0.153R/month, R²=0.041, p=0.453
  → Degrading trend

## 3.9 TEMPORAL STABILITY

**First third** (30 trades, 2024-04-02 to 2025-03-14):
  WR 43.3%, Exp +0.193R, Avg W 1.63R, Avg L 0.91R, Total +5.80R
**Second third** (30 trades, 2025-03-17 to 2025-10-24):
  WR 50.0%, Exp +0.280R, Avg W 1.53R, Avg L 0.97R, Total +8.40R
**Final third** (31 trades, 2025-12-16 to 2026-03-13):
  WR 38.7%, Exp -0.364R, Avg W 0.60R, Avg L 0.97R, Total -11.27R

## 3.10 SAFETY CHECK ANALYSIS

Total candle evaluations: 3480
CANDIDATE signals generated: 156
Trades executed: 91
Note: In batch backtest, CANDIDATE → trade is near-automatic (debate auto-approved)
      Safety checks are embedded in the PA prompt, not a separate step

NO_TRADE reason categories (from 2815 candle evaluations):
  No M15 CHoCH/confirmation: 1012 (36.0%)
  Other: 692 (24.6%)
  No liquidity sweep: 535 (19.0%)
  Bias conflict: 338 (12.0%)
  No POI interaction: 153 (5.4%)
  No displacement: 67 (2.4%)
  Structure unclear: 18 (0.6%)

## 3.11-3.12 MFE/MAE ANALYSIS

MFE (Max Favorable Excursion) and MAE (Max Adverse Excursion) data is NOT
tracked in the batch backtest results. Only final outcome (WIN/LOSS at -1R/+XR)
is recorded. To enable TP optimization and near-miss analysis, MFE tracking
must be added to the outcome evaluation logic.
**This is the single most important missing data point for system improvement.**

## 3.13 TP HIT RATE / PLANNED RR ANALYSIS

Trades with planned RR: 91/91
Planned RR distribution: min 1.28, median 3.01, mean 3.06, max 4.90

Winners (40):
  2024-04-02  london   session_sweep: Planned RR 3.20, Actual +0.59R
  2024-04-03      ny       ob_retest: Planned RR 3.20, Actual +0.44R
  2024-04-18      ny       ob_retest: Planned RR 3.20, Actual +0.10R
  2024-06-03      ny   session_sweep: Planned RR 3.00, Actual +3.08R
  2024-08-26  london   session_sweep: Planned RR 3.00, Actual +1.59R
  2024-11-07      ny       ob_retest: Planned RR 3.00, Actual +2.05R
  2025-01-21      ny   session_sweep: Planned RR 3.00, Actual +2.20R
  2025-02-03      ny   session_sweep: Planned RR 3.20, Actual +1.49R
  2025-02-04      ny   session_sweep: Planned RR 3.20, Actual +1.10R
  2025-02-10  london   session_sweep: Planned RR 3.20, Actual +2.29R
  2025-02-14  london   session_sweep: Planned RR 3.10, Actual +0.47R
  2025-03-13      ny   session_sweep: Planned RR 1.28, Actual +4.80R
  2025-03-14  london   session_sweep: Planned RR 1.28, Actual +1.04R
  2025-03-17  london   session_sweep: Planned RR 3.20, Actual +0.27R
  2025-03-18  london   session_sweep: Planned RR 3.00, Actual +2.20R
  2025-04-04      ny       ob_retest: Planned RR 3.20, Actual +0.28R
  2025-04-16  london   session_sweep: Planned RR 3.02, Actual +3.66R
  2025-06-23  london   session_sweep: Planned RR 3.00, Actual +2.09R
  2025-06-26  london   session_sweep: Planned RR 3.20, Actual +1.81R
  2025-10-01  london   session_sweep: Planned RR 3.20, Actual +0.83R
  2025-10-02  london   session_sweep: Planned RR 1.85, Actual +1.47R
  2025-10-06  london   session_sweep: Planned RR 3.20, Actual +0.92R
  2025-10-10  london   session_sweep: Planned RR 4.90, Actual +1.93R
  2025-10-14  london   session_sweep: Planned RR 3.20, Actual +0.51R
  2025-10-15  london   session_sweep: Planned RR 3.00, Actual +0.69R
  2025-10-16      ny   session_sweep: Planned RR 3.00, Actual +3.91R
  2025-10-20      ny       ob_retest: Planned RR 3.20, Actual +1.06R
  2025-10-24      ny       ob_retest: Planned RR 3.48, Actual +1.32R
  2025-12-16      ny       ob_retest: Planned RR 3.00, Actual +0.64R
  2026-01-08      ny       ob_retest: Planned RR 3.00, Actual +1.76R
  2026-01-09  london       ob_retest: Planned RR 3.00, Actual +0.45R
  2026-01-12  london   session_sweep: Planned RR 3.20, Actual +0.17R
  2026-01-13  london   session_sweep: Planned RR 1.89, Actual +0.23R
  2026-01-15  london   session_sweep: Planned RR 3.20, Actual +0.17R
  2026-01-16  london   session_sweep: Planned RR 3.40, Actual +0.14R
  2026-02-02  london   session_sweep: Planned RR 3.20, Actual +0.55R
  2026-02-02      ny   session_sweep: Planned RR 3.20, Actual +0.27R
  2026-02-03  london   session_sweep: Planned RR 3.55, Actual +0.58R
  2026-03-06      ny   session_sweep: Planned RR 3.20, Actual +0.35R
  2026-03-09      ny   session_sweep: Planned RR 3.00, Actual +1.90R

Losers (51):
  2024-04-04  london   session_sweep: Planned RR 3.20, Actual -1.00R
  2024-04-24  london   session_sweep: Planned RR 3.00, Actual -1.00R
  2024-04-24      ny   session_sweep: Planned RR 3.01, Actual -0.30R
  2024-08-27      ny   session_sweep: Planned RR 3.20, Actual -1.00R
  2024-10-04  london   session_sweep: Planned RR 3.14, Actual -1.00R
  2024-11-13      ny   session_sweep: Planned RR 3.00, Actual -1.00R
  2025-01-21  london   session_sweep: Planned RR 3.01, Actual -1.00R
  2025-01-24      ny   session_sweep: Planned RR 3.01, Actual -1.00R
  2025-02-06      ny   session_sweep: Planned RR 3.20, Actual -1.00R
  2025-02-07      ny   session_sweep: Planned RR 3.00, Actual -0.14R
  2025-02-12  london   session_sweep: Planned RR 3.00, Actual -1.00R
  2025-02-17  london   session_sweep: Planned RR 3.00, Actual -1.00R
  2025-02-21  london   session_sweep: Planned RR 3.00, Actual -1.00R
  2025-02-25  london   session_sweep: Planned RR 4.00, Actual -1.00R
  2025-02-26  london   session_sweep: Planned RR 3.90, Actual -1.00R
  2025-02-26      ny   session_sweep: Planned RR 3.20, Actual -1.00R
  2025-03-04  london   session_sweep: Planned RR 3.00, Actual -1.00R
  2025-03-19  london   session_sweep: Planned RR 3.00, Actual -1.00R
  2025-03-20  london   session_sweep: Planned RR 3.20, Actual -1.00R
  2025-03-21  london   session_sweep: Planned RR 2.04, Actual -1.00R
  2025-03-24  london   session_sweep: Planned RR 3.00, Actual -1.00R
  2025-04-03  london   session_sweep: Planned RR 2.52, Actual -1.00R
  2025-04-07      ny   session_sweep: Planned RR 3.20, Actual -1.00R
  2025-04-08  london   session_sweep: Planned RR 3.00, Actual -1.00R
  2025-06-24  london   session_sweep: Planned RR 3.20, Actual -1.00R
  2025-06-25  london     equal_sweep: Planned RR 3.06, Actual -1.00R
  2025-09-16  london   session_sweep: Planned RR 3.00, Actual -1.00R
  2025-09-18      ny   session_sweep: Planned RR 3.20, Actual -0.55R
  2025-09-24      ny   session_sweep: Planned RR 3.20, Actual -1.00R
  2025-09-30  london   session_sweep: Planned RR 3.00, Actual -1.00R
  2025-10-09      ny   session_sweep: Planned RR 3.00, Actual -1.00R
  2025-10-24  london   session_sweep: Planned RR 3.10, Actual -1.00R
  2025-12-17  london   session_sweep: Planned RR 3.00, Actual -1.00R
  2025-12-29  london   session_sweep: Planned RR 3.78, Actual -1.00R
  2026-01-05  london   session_sweep: Planned RR 3.01, Actual -1.00R
  2026-01-06  london   session_sweep: Planned RR 3.00, Actual -1.00R
  2026-01-09      ny   session_sweep: Planned RR 3.00, Actual -1.00R
  2026-01-21  london   session_sweep: Planned RR 3.00, Actual -1.00R
  2026-01-21      ny   session_sweep: Planned RR 3.00, Actual -1.00R
  2026-01-26  london   session_sweep: Planned RR 3.00, Actual -1.00R
  2026-01-26      ny   session_sweep: Planned RR 3.00, Actual -1.00R
  2026-02-04  london   session_sweep: Planned RR 3.02, Actual -1.00R
  2026-02-05  london   session_sweep: Planned RR 3.40, Actual -1.00R
  2026-02-05      ny   session_sweep: Planned RR 3.10, Actual -1.00R
  2026-03-05  london   session_sweep: Planned RR 3.00, Actual -1.00R
  2026-03-05      ny   session_sweep: Planned RR 3.20, Actual -0.48R
  2026-03-09  london   session_sweep: Planned RR 3.00, Actual -1.00R
  2026-03-10      ny   session_sweep: Planned RR 3.00, Actual -1.00R
  2026-03-11  london   session_sweep: Planned RR 3.40, Actual -1.00R
  2026-03-12  london   session_sweep: Planned RR 3.00, Actual -1.00R
  2026-03-13  london   session_sweep: Planned RR 3.00, Actual -1.00R

## 3.14 SL SIZING ANALYSIS

Trades with SL data: 91/91
SL distribution: min $2.23, median $13.50, mean $24.03, max $185.19
  <$5: 6 trades, WR 33.3%, Exp +0.398R ⚠️ LOW SAMPLE
  $5-$8: 19 trades, WR 26.3%, Exp -0.188R
  $8-$12: 16 trades, WR 43.8%, Exp -0.130R
  $12-$18: 14 trades, WR 42.9%, Exp +0.361R ⚠️ LOW SAMPLE
  $18+: 36 trades, WR 55.6%, Exp +0.032R

## 3.15 CONFIDENCE SCORE VS OUTCOME

Trades with confidence data: 91/91
Confidence distribution: min 85, median 85, mean 85.1, max 92
  Confidence 85: 90 trades, WR 43.3%, Exp +0.029R
  Confidence 90+: 1 trades, WR 100.0%, Exp +0.280R ⚠️ LOW SAMPLE

  Spearman correlation (confidence vs R): ρ=0.056, p=0.5969
  → Confidence is NOT predictive

## 3.16 DISPLACEMENT QUALITY VS OUTCOME

**medium**: 19 trades, 5W/14L, WR 26.3%, Total -8.13R, Exp -0.428R, Avg W 1.08R, Avg L 0.97R
**none**: 3 trades, 2W/1L, WR 66.7%, Total +6.00R, Exp +2.000R, Avg W 3.50R, Avg L 1.00R ⚠️ LOW SAMPLE
**strong**: 68 trades, 32W/36L, WR 47.1%, Total +1.98R, Exp +0.029R, Avg W 1.12R, Avg L 0.94R
**weak**: 1 trades, 1W/0L, WR 100.0%, Total +3.08R, Exp +3.080R, Avg W 3.08R, Avg L 0.00R ⚠️ LOW SAMPLE

## 3.17 LIQUIDITY POOL TYPE VS OUTCOME

**asian_high**: 37 trades, 14W/23L, WR 37.8%, Total +7.18R, Exp +0.194R, Avg W 2.06R, Avg L 0.94R
**asian_low**: 26 trades, 10W/16L, WR 38.5%, Total -5.91R, Exp -0.227R, Avg W 0.94R, Avg L 0.96R
**equal_highs**: 2 trades, 0W/2L, WR 0.0%, Total -2.00R, Exp -1.000R, Avg W 0.00R, Avg L 1.00R ⚠️ LOW SAMPLE
**london_low**: 1 trades, 1W/0L, WR 100.0%, Total +0.14R, Exp +0.140R, Avg W 0.14R, Avg L 0.00R ⚠️ LOW SAMPLE
**none**: 9 trades, 9W/0L, WR 100.0%, Total +8.10R, Exp +0.900R, Avg W 0.90R, Avg L 0.00R ⚠️ LOW SAMPLE
**pdh**: 5 trades, 2W/3L, WR 40.0%, Total -1.02R, Exp -0.204R, Avg W 0.99R, Avg L 1.00R ⚠️ LOW SAMPLE
**pdl**: 7 trades, 2W/5L, WR 28.6%, Total -4.56R, Exp -0.651R, Avg W 0.22R, Avg L 1.00R ⚠️ LOW SAMPLE
**session_low**: 4 trades, 2W/2L, WR 50.0%, Total +1.00R, Exp +0.250R, Avg W 1.24R, Avg L 0.74R ⚠️ LOW SAMPLE

## 3.17b SWEEP QUALITY VS OUTCOME

**ambiguous**: 9 trades, 9W/0L, WR 100.0%, Total +8.10R, Exp +0.900R, Avg W 0.90R, Avg L 0.00R ⚠️ LOW SAMPLE
**clean**: 82 trades, 31W/51L, WR 37.8%, Total -5.17R, Exp -0.063R, Avg W 1.40R, Avg L 0.95R

## 3.18 WIN/LOSS STREAK ANALYSIS

Max consecutive wins: 5
Max consecutive losses: 6
Avg win streak: 2.0
Avg loss streak: 2.5
Max drawdown: 11.91R (peak to trough)

## 3.19 CROSS-FILTER ANALYSIS

| Filter                         | Trades | Win Rate | Expectancy |  Total R |
|--------------------------------|--------|----------|------------|----------|
| ALL trades                     |     91 |    44.0% |    +0.032R |   +2.93R |
| NY only                        |     34 |    50.0% |    +0.361R |  +12.28R |
| London only                    |     57 |    40.4% |    -0.164R |   -9.35R |
| A+ only                        |     70 |    47.1% |    +0.083R |   +5.78R |
| A only                         |     21 |    33.3% |    -0.136R |   -2.85R |
| NY + A+                        |     29 |    51.7% |    +0.329R |   +9.55R |
| NY + A                         |      5 |    40.0% |    +0.546R |   +2.73R | ⚠️
| London + A+                    |     41 |    43.9% |    -0.092R |   -3.77R |
| London + A                     |     16 |    31.2% |    -0.349R |   -5.58R |
| LONG only                      |     86 |    45.3% |    +0.075R |   +6.46R |
| SHORT only                     |      5 |    20.0% |    -0.706R |   -3.53R | ⚠️
| Confidence >= 75               |     91 |    44.0% |    +0.032R |   +2.93R |
| Confidence >= 80               |     91 |    44.0% |    +0.032R |   +2.93R |
| Confidence >= 85               |     91 |    44.0% |    +0.032R |   +2.93R |
| NY + Confidence >= 75          |     34 |    50.0% |    +0.361R |  +12.28R |
| SL <= $8                       |     26 |    26.9% |    -0.084R |   -2.19R |
| SL > $8                        |     65 |    50.8% |    +0.079R |   +5.12R |
| session_sweep only             |     81 |    38.3% |    -0.051R |   -4.17R |
| Batch3                         |     27 |    37.0% |    +0.066R |   +1.77R |
| Batch4A                        |     55 |    45.5% |    -0.024R |   -1.34R |
| Batch4B                        |      9 |    55.6% |    +0.278R |   +2.50R | ⚠️

**Best filter (≥20 trades): NY only with expectancy +0.361R**

## 3.20 STATISTICAL SIGNIFICANCE

**All trades (n=91)**
  H0: true expectancy = 0
  t-statistic: 0.228
  p-value: 0.8199
  → FAIL TO REJECT H0 (p = 0.820)
  Bootstrap 95% CI on expectancy: [-0.234R, +0.312R]
  → CI spans zero — cannot confirm edge
  Sample size needed for 95% CI to exclude zero: ~6704 trades

**Best filter subset: NY only (n=34)**
  t-stat: 1.353, p-value: 0.1853
  Bootstrap 95% CI: [-0.133R, +0.914R]

## 3.21 MONTE CARLO EQUITY SIMULATION

**All trades (91 actual trades, simulated to 100):**
  Median final R after 100 trades: +2.99R
  5th percentile (worst case): -17.88R
  95th percentile (best case): +25.69R
  P(profitable after 50 trades): 55.4%
  P(profitable after 100 trades): 58.6%
  Max drawdown — median: 12.47R, 5th pct: 6.50R, 95th pct: 24.96R

**Best filter: NY only (34 actual trades, simulated to 100):**
  Median final R after 100 trades: +35.64R
  5th percentile (worst case): +11.10R
  95th percentile (best case): +62.31R
  P(profitable after 50 trades): 96.1%
  P(profitable after 100 trades): 99.4%
  Max drawdown — median: 6.82R, 5th pct: 4.00R, 95th pct: 12.43R

## 3.22 KELLY CRITERION

Win rate (W): 44.0%
Avg winner: 1.285R  |  Avg loser: 0.950R
Payoff ratio (b): 1.352
Full Kelly: 2.51% of capital per trade
Half Kelly: 1.25%
Quarter Kelly: 0.63%
Current system: 1.00% per trade
→ 1% is between quarter and half Kelly — appropriate

## 3.23 OPTIMAL TP PLACEMENT MODEL

Cannot perform this analysis without MFE data. See 3.11-3.12 note above.

## 3.24 PRE-SCREENING EFFICIENCY

**Batch3:**
  Total weekdays in range: 125
  Sessions that passed pre-screening: 49 (39.2%)
  Pre-screened out: ~76 (60.8%)
  Sessions → trades: 25/49 (51.0%)
  Sessions → winning trades: 9/49 (18.4%)
  Monthly session counts: {'2024-10': 4, '2024-11': 6, '2025-01': 10, '2025-02': 18, '2025-03': 11}

**Batch4A:**
  Total weekdays in range: 247
  Sessions that passed pre-screening: 101 (40.9%)
  Pre-screened out: ~146 (59.1%)
  Sessions → trades: 47/101 (46.5%)
  Sessions → winning trades: 22/101 (21.8%)
  Monthly session counts: {'2025-04': 7, '2025-05': 7, '2025-06': 12, '2025-09': 12, '2025-10': 16, '2025-11': 2, '2025-12': 14, '2026-01': 20, '2026-02': 4, '2026-03': 7}

**Batch4B:**
  Total weekdays in range: 131
  Sessions that passed pre-screening: 24 (18.3%)
  Pre-screened out: ~107 (81.7%)
  Sessions → trades: 8/24 (33.3%)
  Sessions → winning trades: 5/24 (20.8%)
  Monthly session counts: {'2024-04': 11, '2024-05': 1, '2024-06': 2, '2024-07': 4, '2024-08': 4, '2024-09': 2}


## 3.25 FRAMEWORK 2-4 INVESTIGATION

**session_sweep**:
  Evaluated: 2815 times
  Qualified: 0 (0.0% of evaluations)
  Not qualified: 2815
  Top rejection reasons:
    - All sweeps were runs (body closed beyond levels), not sweeps (wick beyond + b...: 193
    - No valid sweep detected - all PDH interactions were runs (body closed beyond ...: 135
    - No valid sweep detected - all Asian high interactions were runs (body closed ...: 134

**ob_retest**:
  Evaluated: 2815 times
  Qualified: 0 (0.0% of evaluations)
  Not qualified: 2815
  Top rejection reasons:
    - No current retest of H1 order blocks - price not at any unmitigated OB zones: 86
    - No current retest of H1 order blocks - price is above all unmitigated OBs: 80
    - No current retest of H1 order blocks - price not at OB zones: 45

**equal_sweep**:
  Evaluated: 2815 times
  Qualified: 0 (0.0% of evaluations)
  Not qualified: 2815
  Top rejection reasons:
    - No equal highs/lows sweep detected in current timeframe: 220
    - No equal highs/lows sweep detected during kill zone window: 163
    - No equal highs/lows sweep detected in current session: 70

**fvg_fill**:
  Evaluated: 2815 times
  Qualified: 0 (0.0% of evaluations)
  Not qualified: 2815
  Top rejection reasons:
    - No H1 FVG being tested at current price level: 83
    - No M15 CHoCH + displacement detected upon FVG interaction: 76
    - No M15 CHoCH + displacement detected after FVG interaction: 58


## STEP 4: SUMMARY RECOMMENDATIONS

### 1. KILL/KEEP DECISIONS

London: 57 trades, WR 40.4%, Exp -0.164R
NY:     34 trades, WR 50.0%, Exp +0.361R
→ CONSIDER dropping London (negative expectancy) but sample sizes are small

Grade A: 21 trades, WR 33.3%, Exp -0.136R
Grade A+: 70 trades, WR 47.1%, Exp +0.083R

### 2. TP OPTIMIZATION

Average winner achieves: 1.28R
Note: MFE data not available in batch results — cannot do precise TP optimization
Recommendation: Track MFE in live/demo to enable this analysis

### 3. FRAMEWORK PRUNING

session_sweep: 81 trades, Exp -0.051R
ob_retest: 9 trades, Exp +0.900R
equal_sweep: 1 trades, Exp -1.000R
→ session_sweep dominates. Other frameworks rarely trigger.
→ Consider: either fix framework 2-4 triggers or simplify to session_sweep only

### 4. FILTER RECOMMENDATIONS

See cross-filter table (3.19) for the optimal filter combination.

### 5. STATISTICAL VERDICT

Overall expectancy: +0.032R per trade
t-test p-value: 0.8199
Bootstrap 95% CI: [-0.234R, +0.312R]
→ NO CONFIRMED EDGE: Cannot reject null hypothesis

### 6. KELLY SIZING VERDICT

Full Kelly: 2.51%
Quarter Kelly: 0.63%
→ 1% risk is near or above quarter Kelly — appropriate

### 7. GO/NO-GO FOR DEMO TRADING

VERDICT: NOT READY for demo trading
Rationale:
  - Expectancy +0.032R is insufficient
  - Bootstrap CI includes zero
Required before demo:
  - Identify and fix the losing filter combinations
  - Add MFE tracking to optimize TP placement
  - Re-run backtest on new date ranges for validation
