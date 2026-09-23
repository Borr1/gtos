========================================================================
SESSION 1: DEEP DIAGNOSTIC ANALYSIS
========================================================================

Loaded 91 trades from unified_trades.json

========================================================================
PHASE 2: CROSS-FILTER ANALYSIS
========================================================================

## 2.1 THE CRITICAL 2×2: FRAMEWORK × KILL ZONE

| Framework       | KZ      | Trades |   W |   L |     WR |  Total R |      Exp |
|-----------------|---------|--------|-----|-----|--------|----------|----------|
| equal_sweep     | london  |      1 |   0 |   1 |   0.0% |   -1.00R |  -1.000R | ⚠️ LOW SAMPLE
| equal_sweep     | ny      |      0 |   - |   - |    --% |      --R |      --R |
| ob_retest       | london  |      1 |   1 |   0 | 100.0% |   +0.45R |  +0.450R | ⚠️ LOW SAMPLE
| ob_retest       | ny      |      8 |   8 |   0 | 100.0% |   +7.65R |  +0.956R | ⚠️ LOW SAMPLE
| session_sweep   | london  |     55 |  22 |  33 |  40.0% |   -8.80R |  -0.160R |
| session_sweep   | ny      |     26 |   9 |  17 |  34.6% |   +4.63R |  +0.178R |

## 2.2 FULL CROSS-FILTER TABLE

| Filter                       |    N |   W |   L |     WR | Exp/Trade |  Total R |
|------------------------------|------|-----|-----|--------|-----------|----------|
| ob_retest + NOT Wed          |    8 |   8 |   0 | 100.0% |   +0.957R |   +7.66R | ⚠️
| ob_retest + NY               |    8 |   8 |   0 | 100.0% |   +0.956R |   +7.65R | ⚠️
| ob_retest                    |    9 |   9 |   0 | 100.0% |   +0.900R |   +8.10R | ⚠️
| ob_retest + A+               |    9 |   9 |   0 | 100.0% |   +0.900R |   +8.10R | ⚠️
| NY + LONG + NOT Wed          |   25 |  16 |   9 |  64.0% |   +0.766R |  +19.14R |
| NY + NOT Wed                 |   28 |  16 |  12 |  57.1% |   +0.576R |  +16.14R |
| NY + A                       |    5 |   2 |   3 |  40.0% |   +0.546R |   +2.73R | ⚠️
| NY + LONG                    |   31 |  17 |  14 |  54.8% |   +0.493R |  +15.28R |
| NY + A+ + LONG               |   26 |  15 |  11 |  57.7% |   +0.483R |  +12.55R |
| ob_retest + London           |    1 |   1 |   0 | 100.0% |   +0.450R |   +0.45R | ⚠️
| Monday only                  |   20 |  12 |   8 |  60.0% |   +0.384R |   +7.68R |
| NY only                      |   34 |  17 |  17 |  50.0% |   +0.361R |  +12.28R |
| ss + NY + LONG               |   23 |   9 |  14 |  39.1% |   +0.332R |   +7.63R |
| NY + A+                      |   29 |  15 |  14 |  51.7% |   +0.329R |   +9.55R |
| session_sweep + NY           |   26 |   9 |  17 |  34.6% |   +0.178R |   +4.63R |
| NOT Wednesday                |   73 |  36 |  37 |  49.3% |   +0.145R |  +10.61R |
| session_sweep + NY + A+      |   21 |   7 |  14 |  33.3% |   +0.090R |   +1.90R |
| A+ only                      |   70 |  33 |  37 |  47.1% |   +0.083R |   +5.78R |
| LONG only                    |   86 |  39 |  47 |  45.3% |   +0.075R |   +6.46R |
| ALL trades                   |   91 |  40 |  51 |  44.0% |   +0.032R |   +2.93R |
| session_sweep + A+           |   61 |  24 |  37 |  39.3% |   -0.038R |   -2.32R |
| session_sweep                |   81 |  31 |  50 |  38.3% |   -0.051R |   -4.17R |
| London + A+                  |   41 |  18 |  23 |  43.9% |   -0.092R |   -3.77R |
| ss + London + A+             |   40 |  17 |  23 |  42.5% |   -0.106R |   -4.22R |
| A only                       |   21 |   7 |  14 |  33.3% |   -0.136R |   -2.85R |
| session_sweep + London       |   55 |  22 |  33 |  40.0% |   -0.160R |   -8.80R |
| London + LONG                |   55 |  22 |  33 |  40.0% |   -0.160R |   -8.82R |
| London only                  |   57 |  23 |  34 |  40.4% |   -0.164R |   -9.35R |
| London + SHORT               |    2 |   1 |   1 |  50.0% |   -0.265R |   -0.53R | ⚠️
| London + A                   |   16 |   5 |  11 |  31.2% |   -0.349R |   -5.58R |
| SHORT only                   |    5 |   1 |   4 |  20.0% |   -0.706R |   -3.53R | ⚠️
| NY + SHORT                   |    3 |   0 |   3 |   0.0% |   -1.000R |   -3.00R | ⚠️

🏆 BEST FILTER (≥15 trades): NY + LONG + NOT Wed
   25 trades, WR 64.0%, Exp +0.766R, Total +19.14R

========================================================================
## 2.3 TEMPORAL DECAY DRILL-DOWN
========================================================================

**First third** (30 trades, 2024-04-02 to 2025-03-14)
  Months: 2024-04, 2024-06, 2024-08, 2024-10, 2024-11, 2025-01, 2025-02, 2025-03
  WR: 43.3%, Exp: +0.193R, Total: +5.80R
  Frameworks: {'session_sweep': 27, 'ob_retest': 3}
  Kill zones: {'london': 15, 'ny': 15}
    session_sweep+london: 15 trades, 5W/10L, -4.02R
    session_sweep+ny: 12 trades, 5W/7L, +7.23R
    ob_retest+ny: 3 trades, 3W/0L, +2.59R

**Second third** (30 trades, 2025-03-17 to 2025-10-24)
  Months: 2025-03, 2025-04, 2025-06, 2025-09, 2025-10
  WR: 50.0%, Exp: +0.280R, Total: +8.40R
  Frameworks: {'session_sweep': 26, 'ob_retest': 3, 'equal_sweep': 1}
  Kill zones: {'london': 22, 'ny': 8}
    session_sweep+london: 21 trades, 11W/10L, +6.38R
    session_sweep+ny: 5 trades, 1W/4L, +0.36R
    ob_retest+ny: 3 trades, 3W/0L, +2.66R

**Final third** (31 trades, 2025-12-16 to 2026-03-13)
  Months: 2025-12, 2026-01, 2026-02, 2026-03
  WR: 38.7%, Exp: -0.364R, Total: -11.27R
  Frameworks: {'ob_retest': 3, 'session_sweep': 28}
  Kill zones: {'ny': 11, 'london': 20}
    session_sweep+london: 19 trades, 6W/13L, -11.16R
    session_sweep+ny: 9 trades, 3W/6L, -2.96R
    ob_retest+london: 1 trades, 1W/0L, +0.45R
    ob_retest+ny: 2 trades, 2W/0L, +2.40R

### Final Third — EVERY TRADE:
| Date       | FW             | KZ      | Dir   | Grade |      R | Batch   |
|------------|----------------|---------|-------|-------|--------|---------|
| 2025-12-16 | ob_retest      | ny      | LONG  | A+    | +0.64R | Batch4A |
| 2025-12-17 | session_sweep  | london  | LONG  | A+    | -1.00R | Batch4A |
| 2025-12-29 | session_sweep  | london  | LONG  | A+    | -1.00R | Batch4A |
| 2026-01-05 | session_sweep  | london  | LONG  | A     | -1.00R | Batch4A |
| 2026-01-06 | session_sweep  | london  | LONG  | A+    | -1.00R | Batch4A |
| 2026-01-08 | ob_retest      | ny      | LONG  | A+    | +1.76R | Batch4A |
| 2026-01-09 | ob_retest      | london  | LONG  | A+    | +0.45R | Batch4A |
| 2026-01-09 | session_sweep  | ny      | SHORT | A+    | -1.00R | Batch4A |
| 2026-01-12 | session_sweep  | london  | LONG  | A+    | +0.17R | Batch4A |
| 2026-01-13 | session_sweep  | london  | LONG  | A     | +0.23R | Batch4A |
| 2026-01-15 | session_sweep  | london  | LONG  | A+    | +0.17R | Batch4A |
| 2026-01-16 | session_sweep  | london  | LONG  | A+    | +0.14R | Batch4A |
| 2026-01-21 | session_sweep  | london  | LONG  | A+    | -1.00R | Batch4A |
| 2026-01-21 | session_sweep  | ny      | LONG  | A+    | -1.00R | Batch4A |
| 2026-01-26 | session_sweep  | london  | LONG  | A+    | -1.00R | Batch4A |
| 2026-01-26 | session_sweep  | ny      | LONG  | A+    | -1.00R | Batch4A |
| 2026-02-02 | session_sweep  | london  | LONG  | A+    | +0.55R | Batch4A |
| 2026-02-02 | session_sweep  | ny      | LONG  | A+    | +0.27R | Batch4A |
| 2026-02-03 | session_sweep  | london  | LONG  | A+    | +0.58R | Batch4A |
| 2026-02-04 | session_sweep  | london  | SHORT | A+    | -1.00R | Batch4A |
| 2026-02-05 | session_sweep  | london  | LONG  | A+    | -1.00R | Batch4A |
| 2026-02-05 | session_sweep  | ny      | LONG  | A+    | -1.00R | Batch4A |
| 2026-03-05 | session_sweep  | london  | LONG  | A     | -1.00R | Batch4A |
| 2026-03-05 | session_sweep  | ny      | LONG  | A+    | -0.48R | Batch4A |
| 2026-03-06 | session_sweep  | ny      | LONG  | A+    | +0.35R | Batch4A |
| 2026-03-09 | session_sweep  | london  | LONG  | A+    | -1.00R | Batch4A |
| 2026-03-09 | session_sweep  | ny      | LONG  | A+    | +1.90R | Batch4A |
| 2026-03-10 | session_sweep  | ny      | SHORT | A+    | -1.00R | Batch4A |
| 2026-03-11 | session_sweep  | london  | LONG  | A     | -1.00R | Batch4A |
| 2026-03-12 | session_sweep  | london  | LONG  | A+    | -1.00R | Batch4A |
| 2026-03-13 | session_sweep  | london  | LONG  | A+    | -1.00R | Batch4A |

### Final Third — Monthly Breakdown:
  2025-12: 3 trades (1W/2L), -1.36R — KZ: {'ny': 1, 'london': 2}
  2026-01: 13 trades (6W/7L), -4.08R — KZ: {'london': 9, 'ny': 4}
  2026-02: 6 trades (3W/3L), -1.60R — KZ: {'london': 4, 'ny': 2}
  2026-03: 9 trades (2W/7L), -4.23R — KZ: {'london': 5, 'ny': 4}

========================================================================
## 2.4 OB_RETEST TRADE DETAIL DUMP
========================================================================

Total ob_retest trades: 9
✓ No duplicate dates

| Date       | Batch   | KZ      | Dir   | Grade |     Entry |        SL |    SL$ |       TP1 |       TP2 |       TP3 |      R | Conf | Day        | LiqPool      |
|------------|---------|---------|-------|-------|-----------|-----------|--------|-----------|-----------|-----------|--------|------|------------|--------------|
| 2024-04-03 | Batch4B | ny      | LONG  | A+    |   2273.27 |   2240.97 |  32.3$ |   2280.00 |   2290.00 |   2310.00 | +0.44R |   85 | Wednesday  | none         |
| 2024-04-18 | Batch4B | ny      | LONG  | A+    |   2379.28 |   2367.67 |  11.6$ |   2381.50 |   2390.00 |   2400.00 | +0.10R |   85 | Thursday   | none         |
| 2024-11-07 | Batch3  | ny      | LONG  | A+    |   2667.57 |   2648.69 |  18.9$ |   2724.21 |   2749.69 |   2780.00 | +2.05R |   85 | Thursday   | none         |
| 2025-04-04 | Batch4A | ny      | LONG  | A+    |   3096.19 |   3063.09 |  33.1$ |   3115.00 |   3140.00 |   3167.73 | +0.28R |   92 | Friday     | none         |
| 2025-10-20 | Batch4A | ny      | LONG  | A+    |   4253.26 |   4220.88 |  32.4$ |   4270.00 |   4290.00 |   4320.00 | +1.06R |   85 | Monday     | none         |
| 2025-10-24 | Batch4A | ny      | LONG  | A+    |   4065.58 |   4025.25 |  40.3$ |   4125.48 |   4167.69 |   4206.18 | +1.32R |   85 | Friday     | none         |
| 2025-12-16 | Batch4A | ny      | LONG  | A+    |   4284.35 |   4256.11 |  28.2$ |   4369.07 |   4400.00 |   4450.00 | +0.64R |   85 | Tuesday    | none         |
| 2026-01-08 | Batch4A | ny      | LONG  | A+    |   4431.34 |   4405.00 |  26.3$ |   4510.36 |   4560.00 |   4620.00 | +1.76R |   85 | Thursday   | none         |
| 2026-01-09 | Batch4A | london  | LONG  | A+    |   4473.58 |   4395.59 |  78.0$ |   4507.55 |   4541.52 |   4575.49 | +0.45R |   85 | Friday     | none         |

### OB_RETEST Characteristics:
  Kill zones: Counter({'ny': 8, 'london': 1})
  Directions: Counter({'LONG': 9})
  Grades: Counter({'A+': 9})
  Days: Counter({'Thursday': 3, 'Friday': 3, 'Monday': 1, 'Tuesday': 1, 'Wednesday': 1})
  Batches: Counter({'Batch4A': 6, 'Batch4B': 2, 'Batch3': 1})
  Liquidity pools: Counter({'none': 9})
  Sweep quality: Counter({'ambiguous': 9})

  OB_RETEST avg SL: $33.46 (median $32.30)
  SESSION_SWEEP avg SL: $23.16 (median $12.43)
  Months active: ['2024-04', '2024-11', '2025-04', '2025-10', '2025-12', '2026-01']

## 2.4b GRADE × FRAMEWORK CROSS-TAB

session_sweep + A+: 61 trades, 24W/37L, WR 39.3%, Total -2.32R, Exp -0.038R
session_sweep + A: 20 trades, 7W/13L, WR 35.0%, Total -1.85R, Exp -0.092R
ob_retest + A+: 9 trades, 9W/0L, WR 100.0%, Total +8.10R, Exp +0.900R ⚠️ LOW SAMPLE
ob_retest + A: 0 trades
equal_sweep + A+: 0 trades
equal_sweep + A: 1 trades, 0W/1L, WR 0.0%, Total -1.00R, Exp -1.000R ⚠️ LOW SAMPLE

========================================================================
## 2.5 WEDNESDAY INVESTIGATION
========================================================================

| Day        |    N |   W |   L |     WR | WR 95% CI        |      Exp |  Total R |
|------------|------|-----|-----|--------|------------------|----------|----------|
| Monday     |   20 |  12 |   8 |  60.0% | [38.7%, 78.1%] |  +0.384R |   +7.68R |
| Tuesday    |   18 |   8 |  10 |  44.4% | [24.6%, 66.3%] |  -0.108R |   -1.95R |
| Wednesday  |   18 |   4 |  14 |  22.2% | [ 9.0%, 45.2%] |  -0.427R |   -7.68R |
| Thursday   |   19 |   8 |  11 |  42.1% | [23.1%, 63.7%] |  +0.318R |   +6.04R |
| Friday     |   16 |   8 |   8 |  50.0% | [28.0%, 72.0%] |  -0.072R |   -1.16R |

### Wednesday breakdown by Framework × KZ:
  Wed session_sweep+london: 11 trades, 3W/8L, -2.82R
  Wed session_sweep+ny: 5 trades, 0W/5L, -4.30R
  Wed ob_retest+ny: 1 trades, 1W/0L, +0.44R

### Day-of-week expectancies: {'Monday': 0.38400000000000006, 'Tuesday': -0.10833333333333332, 'Wednesday': -0.42666666666666664, 'Thursday': 0.31789473684210523, 'Friday': -0.07249999999999998}
  Wednesday exp: -0.427R
  All other days mean exp: +0.130R
  Wednesday is -0.557R worse than average

========================================================================
PHASE 3: DEEP DIVES
========================================================================

## 3.1 BATCH 4B ANOMALY DIAGNOSIS

M15 CSV data range: 2024-04-01 to 2026-03-30
Batch 4B configured range: Apr 2024 – Sep 2024
**Batch3** (2024-10-01 to 2025-03-31):
  Total weekdays: 130
  M15 data days available: 128
  Sessions actually run: 49
  Pre-screened out or no data: 79
  Pre-screen pass rate: 38.3%
  Monthly M15 data days: {'2024-10': 23, '2024-11': 21, '2024-12': 21, '2025-01': 22, '2025-02': 20, '2025-03': 21}
  Monthly sessions run:  {'2024-10': 4, '2024-11': 6, '2025-01': 10, '2025-02': 18, '2025-03': 11}

**Batch4A** (2025-04-01 to 2026-03-31):
  Total weekdays: 261
  M15 data days available: 257
  Sessions actually run: 101
  Pre-screened out or no data: 156
  Pre-screen pass rate: 39.3%
  Monthly M15 data days: {'2025-04': 21, '2025-05': 22, '2025-06': 21, '2025-07': 23, '2025-08': 21, '2025-09': 22, '2025-10': 23, '2025-11': 20, '2025-12': 22, '2026-01': 21, '2026-02': 20, '2026-03': 21}
  Monthly sessions run:  {'2025-04': 7, '2025-05': 7, '2025-06': 12, '2025-09': 12, '2025-10': 16, '2025-11': 2, '2025-12': 14, '2026-01': 20, '2026-02': 4, '2026-03': 7}

**Batch4B** (2024-04-01 to 2024-09-30):
  Total weekdays: 131
  M15 data days available: 131
  Sessions actually run: 24
  Pre-screened out or no data: 107
  Pre-screen pass rate: 18.3%
  Monthly M15 data days: {'2024-04': 22, '2024-05': 23, '2024-06': 20, '2024-07': 23, '2024-08': 22, '2024-09': 21}
  Monthly sessions run:  {'2024-04': 11, '2024-05': 1, '2024-06': 2, '2024-07': 4, '2024-08': 4, '2024-09': 2}


## 3.2 OB_RETEST NEAR-MISS ANALYSIS

Total candle responses scanned: 3472
OB_RETEST near-misses found: 2804
  Has OB/CHoCH but no BOS: 1449
  No retest of OB: 652
  Other OB-related rejection: 402
  Has OB but no CHoCH: 259
  No pullback to OB: 42

### All ob_retest rejection reasons (top 10):
  [ 203] unknown
  [ 104] No current retest of H1 order blocks - price not at any unmitigated OB zones
  [  87] No current retest of H1 order blocks - price is above all unmitigated OBs
  [  47] No current retest of H1 order blocks - price not at OB zones
  [  40] No M15 CHoCH + displacement detected at current candle to confirm entry
  [  32] No current retest of H1 order blocks - price not in any OB zone
  [  31] Daily bias is bearish but H1 structure is bullish - no alignment
  [  23] H4 structure shows bearish CHoCH conflicting with bullish daily bias
  [  21] No current price interaction with unmitigated H1 order blocks
  [  20] M15 CHoCH is bearish but daily bias is bullish - direction mismatch violates U4

========================================================================
## 3.3 SESSION_SWEEP FAILURE MODE ANALYSIS
========================================================================

Session_sweep: 81 total, 31W/50L

### SL Size Buckets:
  <$5: 6 trades, 2W/4L, WR 33.3%, Exp +0.398R ⚠️ LOW SAMPLE
  $5-$8: 19 trades, 5W/14L, WR 26.3%, Exp -0.188R
  $8-$12: 14 trades, 6W/8L, WR 42.9%, Exp -0.084R ⚠️ LOW SAMPLE
  $12+: 42 trades, 18W/24L, WR 42.9%, Exp -0.043R

### SS losses by Kill Zone:
  london: 33 losses
    SL range: $3.23 - $112.12, median $10.91
  ny: 17 losses
    SL range: $4.82 - $84.10, median $13.50

### SS by Liquidity Pool Type:
  asian_high: 37 trades, 14W/23L, WR 37.8%, Exp +0.194R
  asian_low: 26 trades, 10W/16L, WR 38.5%, Exp -0.227R
  equal_highs: 1 trades, 0W/1L, WR 0.0%, Exp -1.000R ⚠️ LOW SAMPLE
  london_low: 1 trades, 1W/0L, WR 100.0%, Exp +0.140R ⚠️ LOW SAMPLE
  pdh: 5 trades, 2W/3L, WR 40.0%, Exp -0.204R ⚠️ LOW SAMPLE
  pdl: 7 trades, 2W/5L, WR 28.6%, Exp -0.651R ⚠️ LOW SAMPLE
  session_low: 4 trades, 2W/2L, WR 50.0%, Exp +0.250R ⚠️ LOW SAMPLE

========================================================================
## 3.4 WINNER EXIT ANALYSIS
========================================================================

Winners: 40 total

### Winner R-multiple Distribution:
  Min: 0.10R
  25th pct: 0.45R
  Median: 0.98R
  75th pct: 1.91R
  Max: 4.80R

  Tiny wins (<0.5R): 12 — likely timeout or barely profitable
  Small wins (0.5-1.0R): 8 — TP1 hit, remainder BE'd
  Medium wins (1.0-2.0R): 11 — TP1+partial TP2 or good timeout
  Large wins (2.0+R): 9 — TP2+ hit or runner success

### TP1 theoretical R for winners (50% position at TP1):
  Avg TP1 distance in R: 1.58R
  Avg contribution of TP1 alone (50%): 0.79R
  Actual avg winner R: 1.28R

  Winners achieving LESS than TP1 alone would give: 8/40
  → These are likely profitable timeouts (didn't even hit TP1)

========================================================================
## 3.5 TRADE TIMING WITHIN KILL ZONE
========================================================================

Trades with timing data: 91/91
  Early (0-45 min): 36 trades, 13W/23L, WR 36.1%, Exp -0.056R
  Middle (46-90 min): 32 trades, 17W/15L, WR 53.1%, Exp +0.207R
  Late (91+ min): 23 trades, 10W/13L, WR 43.5%, Exp -0.073R

  LONDON timing distribution:
    Median entry: 60 min into window
    Range: 15 - 150 min

  NY timing distribution:
    Median entry: 60 min into window
    Range: 15 - 150 min

========================================================================
## 3.6 CONFIDENCE SCORE DEEP DIVE
========================================================================

Confidence score distribution: {85: 90, 92: 1}

Outlier(s):
  2025-04-04 ny ob_retest: conf=92, WIN +0.28R

### Confidence scoring in Primary Analyzer prompt:
  Could not load PA prompt: No module named 'src'

========================================================================
## 3.7 PRE-SCREENING RATE BY PERIOD
========================================================================

| Month   | M15 Days | Sessions | Pass Rate | Trades | Batch    |
|---------|----------|----------|-----------|--------|----------|
| 2024-04 |       22 |       11 |     50.0% |      6 | Batch4B  |
| 2024-05 |       23 |        1 |      4.3% |      0 | Batch4B  |
| 2024-06 |       20 |        2 |     10.0% |      1 | Batch4B  |
| 2024-07 |       23 |        4 |     17.4% |      0 | Batch4B  |
| 2024-08 |       22 |        4 |     18.2% |      2 | Batch4B  |
| 2024-09 |       21 |        2 |      9.5% |      0 | Batch4B  |
| 2024-10 |       23 |        4 |     17.4% |      1 | Batch3   |
| 2024-11 |       21 |        6 |     28.6% |      2 | Batch3   |
| 2024-12 |       21 |        0 |      0.0% |      0 | Batch3   |
| 2025-01 |       22 |       10 |     45.5% |      3 | Batch3   |
| 2025-02 |       20 |       18 |     90.0% |     12 | Batch3   |
| 2025-03 |       21 |       11 |     52.4% |      9 | Batch3   |
| 2025-04 |       21 |        7 |     33.3% |      5 | Batch4A  |
| 2025-05 |       22 |        7 |     31.8% |      0 | Batch4A  |
| 2025-06 |       21 |       12 |     57.1% |      4 | Batch4A  |
| 2025-07 |       23 |        0 |      0.0% |      0 | Batch4A  |
| 2025-08 |       21 |        0 |      0.0% |      0 | Batch4A  |
| 2025-09 |       22 |       12 |     54.5% |      4 | Batch4A  |
| 2025-10 |       23 |       16 |     69.6% |     11 | Batch4A  |
| 2025-11 |       20 |        2 |     10.0% |      0 | Batch4A  |
| 2025-12 |       22 |       14 |     63.6% |      3 | Batch4A  |
| 2026-01 |       21 |       20 |     95.2% |     13 | Batch4A  |
| 2026-02 |       20 |        4 |     20.0% |      6 | Batch4A  |
| 2026-03 |       21 |        7 |     33.3% |      9 | Batch4A  |

========================================================================
PHASE 4: SYNTHESIS
========================================================================

## 4.1 DECISION TABLE

### Drop London entirely?
  London session_sweep: 55 trades, Exp -0.160R
  London ob_retest: 1 trades, Exp +0.450R
  NY session_sweep: 26 trades, Exp +0.178R
  NY ob_retest: 8 trades, Exp +0.956R
  → CONDITIONAL: Drop London for session_sweep; KEEP for ob_retest [MEDIUM]

### Drop session_sweep?
  session_sweep overall: 81 trades, Exp -0.051R
  session_sweep NY: 26 trades, Exp +0.178R
  → NO: Keep session_sweep (marginally negative, may improve with fixes) [LOW]

### Pivot to ob_retest as primary?
  ob_retest: 9 trades, ALL wins, Exp +0.900R
  BUT: only 9 trades across 6 months
  Near-misses found: 2804
  → CONDITIONAL: Investigate relaxing ob_retest triggers to increase frequency. Too rare to be primary alone. [MEDIUM]

### Restrict to A+ only?
  A+: 70 trades, Exp +0.083R
  A:  21 trades, Exp -0.136R
  → YES: Drop A-grade trades (negative expectancy, dilute the edge) [MEDIUM]

### Exclude Wednesdays?
  Wednesday: 18 trades, WR 22.2% CI [9.0%,45.2%], Exp -0.427R
  Not Wed:   73 trades, WR 49.3% CI [38.2%,60.5%], Exp +0.145R
  → CONDITIONAL: Wednesday is worse but CIs overlap. Add to demo monitoring. [LOW]

### Fix confidence scoring?
  → YES: Confidence is a constant (85 for 90/91 trades), providing zero discriminative signal. [HIGH]

### Shorten kill zone window?
  Early (0-45 min): 36 trades, Exp -0.056R
  Late (91+ min): 23 trades, Exp -0.073R
  → NO: Insufficient evidence to shorten [LOW]

## 4.2 BEST FILTER CONFIGURATION

| Filter                    |    N |     WR |      Exp |  Total R | Trades/mo |
|---------------------------|------|--------|----------|----------|-----------|
| NY only                   |   34 |  50.0% |  +0.361R |  +12.28R |      2.4 |
| NOT Wednesday             |   73 |  49.3% |  +0.145R |  +10.61R |      4.6 |
| NY + A+                   |   29 |  51.7% |  +0.329R |   +9.55R |      2.6 |
| NY + NOT Wed              |   28 |  57.1% |  +0.576R |  +16.14R |      2.0 |
| A+ only                   |   70 |  47.1% |  +0.083R |   +5.78R |      5.0 |
| NY + LONG                 |   31 |  54.8% |  +0.493R |  +15.28R |      2.2 |
| session_sweep + NY        |   26 |  34.6% |  +0.178R |   +4.63R |      2.0 |

Recommended production filter: NY kill zone only
  Expected trade frequency: ~2.1 trades/month
  Expected expectancy: +0.361R/trade
  Sample size: 34 trades (below 95% confidence threshold)
  Needed for 95% confidence: ~60-80 NY trades (estimate ~30-38 more months)

## 4.3 OPEN QUESTIONS FOR SESSION 2

  1. MFE/MAE data not tracked in batch results — need to add max_favorable_excursion and max_adverse_excursion to evaluate_hypothetical_outcome(). This is the #1 priority for TP optimization.
  2. OB_RETEST triggers too rarely (9/174 sessions). Near-miss analysis shows the specific rejection reasons. Need to examine whether relaxing BOS requirement or widening OB zone definitions would safely increase frequency.
  3. Confidence score is a constant 85 — the PA prompt needs explicit calibration tiers with examples. Currently the AI defaults to 85 for everything.
  4. Winner exit types unclear — the batch runner tracks events[] in evaluate_hypothetical_outcome but they're not stored in the session/result files. Need to persist exit_substate and events to understand TP1/TP2/TP3 hit rates.
  5. The final third collapse (-11.27R) needs to be checked against gold market regime (was Q1 2026 fundamentally different?). If it's a regime-specific issue, the system may need market regime detection.
  6. Session_sweep sweep-vs-breakdown confusion is the known failure mode but cannot be quantified from current data. Would need to parse raw AI reasoning text for uncertainty language.

Saved: /Users/borr/Documents/trading/gold-agent/knowledge_base_backtest/analysis/session1_decisions.json
