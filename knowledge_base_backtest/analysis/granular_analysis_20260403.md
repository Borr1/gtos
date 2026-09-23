
# Gold System Granular Analysis — Monte Carlo, Kelly, MFE/MAE

**Generated:** 2026-04-03 11:07

**Data:** Phase 1 (18 trades), Unified (111 trades), M5 validation (14 AI trades)

---


# Section 1: MFE/MAE Distribution Analysis


## 1.1 Phase 1 (18 trades, 1.5R TP)


### MFE Distribution — % of trades reaching each R level

| R Level | % Reaching |
| --- | --- |
| 0.25R | 83.3% |
| 0.5R | 66.7% |
| 0.75R | 61.1% |
| 1.0R | 50.0% |
| 1.25R | 44.4% |
| 1.5R | 38.9% |
| 1.75R | 22.2% |
| 2.0R | 22.2% |
| 2.5R | 11.1% |
| 3.0R | 11.1% |


### MAE Distribution — % of trades experiencing each adverse R level

| Adverse R | % Experiencing |
| --- | --- |
| 0.25R | 66.7% |
| 0.5R | 61.1% |
| 0.75R | 38.9% |
| 1.0R | 33.3% |


### MFE/MAE by Outcome

| Metric | Winners | Losers |
| --- | --- | --- |
| Count | 9 | 8 |
| Median MFE | 1.516 | 0.333 |
| Median MAE | 0.164 | 1.04 |
| Mean MFE | 1.937 | 0.682 |
| Mean MAE | 0.491 | 0.947 |


### Efficiency Ratio (MFE / (MFE + MAE))

- Median: **0.626** | Mean: 0.607 | P25: 0.344 | P75: 0.902

*(Higher = cleaner directional moves. 1.0 = no adverse excursion, 0.5 = equal MFE/MAE)*


### Time to MFE (M15 candles from entry to peak)

- Median: **12.5** candles (188 min)

- P25: 6.5 candles | P75: 33.8 candles

- Range: 0 to 63 candles

### Optimal TP Simulation (Phase 1, r_path-based)

| TP Level | Win Rate | Avg R/Trade | Total R |
| --- | --- | --- | --- |
| 0.5R | 66.7% | 0.123 | 2.22 |
| 0.75R | 61.1% | 0.268 | 4.83 |
| 1.0R | 50.0% | 0.354 | 6.36 |
| 1.25R | 44.4% | 0.460 | 8.28 |
| **1.5R** | **38.9%** | **0.503** | **9.05** |
| 1.75R | 22.2% | 0.403 | 7.26 |
| 2.0R | 22.2% | 0.459 | 8.26 |
| 2.5R | 11.1% | 0.342 | 6.15 |
| 3.0R | 11.1% | 0.397 | 7.15 |

**Optimal TP: 1.5R** -- maximizes expected R per trade at +0.503R. Confirms the 1.5R TP decision.

*Note: Sharp drop at 1.75R (from 38.9% WR to 22.2%) indicates a cliff -- many trades reach 1.5R but not 1.75R.*

## 1.2 Unified Dataset (111 trades, original 2.5R TP)


### MFE Distribution — % of trades reaching each R level

| R Level | % Reaching |
| --- | --- |
| 0.25R | 71.4% |
| 0.5R | 54.3% |
| 0.75R | 46.7% |
| 1.0R | 35.2% |
| 1.25R | 26.7% |
| 1.5R | 21.9% |
| 1.75R | 17.1% |
| 2.0R | 12.4% |
| 2.5R | 9.5% |
| 3.0R | 8.6% |

*Limitation: The unified 111-trade dataset has mfe_r/mae_r fields but no r_path (candle-by-candle). TP simulation at hypothetical levels is not possible without r_path. Phase 1 TP simulation above (18 trades with r_path) is the definitive TP optimization.*

*Note: The unified dataset was collected at the original 2.5R TP. Lower MFE rates vs Phase 1 reflect older, less refined trade selection.*

# Section 2: Monte Carlo Simulation


## 2.1 Phase 1 Base Scenario (avg R ≈ 0.503)

**Source:** 18 trades, avg R = 0.5026, win rate = 61.1%


### Final R after 50 trades — Percentile Distribution

| Percentile | Cumulative R |
| --- | --- |
| P1 | 9.34 |
| P5 | 14.12 |
| P10 | 16.61 |
| P25 | 20.61 |
| P50 | 25.2 |
| P75 | 29.67 |
| P90 | 33.74 |
| P95 | 36.15 |
| P99 | 40.97 |

**Mean final R:** 25.16


**Probability of being negative after 20 trades:** 1.0%

**Probability of being negative after 50 trades:** 0.0%


### Maximum Drawdown Distribution (in R)

| Percentile | Max DD (R) |
| --- | --- |
| P1 | 1.0 |
| P5 | 1.17 |
| P10 | 1.44 |
| P25 | 2.0 |
| P50 | 2.34 |
| P75 | 3.01 |
| P90 | 3.9 |
| P95 | 4.36 |
| P99 | 5.83 |


## 2.2 M5-Enhanced Scenario (avg R approx +0.81)

**Method:** Remove 4 worst-performing trades from Phase 1 (proxy for M5 filter)

**Resulting avg R:** 0.892 (target: +0.81)



**BIAS WARNING:** This proxy removes the 4 worst trades by R-multiple, which is an UPPER BOUND.

The actual M5 filter is structural (body >= $10), not performance-based. True M5 distribution

likely falls between base scenario (+0.503R) and this proxy (+0.892R).

Treat M5 Monte Carlo results as optimistic; Phase 1 base scenario is the conservative floor.


### Final R after 50 trades — Percentile Distribution

| Percentile | Cumulative R |
| --- | --- |
| P1 | 33.13 |
| P5 | 36.49 |
| P10 | 38.29 |
| P25 | 41.31 |
| P50 | 44.61 |
| P75 | 47.87 |
| P90 | 50.73 |
| P95 | 52.42 |
| P99 | 55.39 |

**Mean final R:** 44.55


**Probability of being negative after 20 trades:** 0.0%

**Probability of being negative after 50 trades:** 0.0%


### Maximum Drawdown Distribution (in R)

| Percentile | Max DD (R) |
| --- | --- |
| P1 | 0.17 |
| P5 | 0.17 |
| P10 | 0.17 |
| P25 | 0.18 |
| P50 | 0.34 |
| P75 | 0.35 |
| P90 | 0.51 |
| P95 | 0.52 |
| P99 | 0.69 |


## 2.3 Ruin Probability at Different Risk Levels

| Risk/Trade | Phase 1 P(20% DD) | M5 Enhanced P(20% DD) |
| --- | --- | --- |
| 1.0% | 0.0% | 0.0% |
| 1.5% | 0.0% | 0.0% |
| 2.0% | 0.0% | 0.0% |


### Ruin Probability — 10% DD Threshold (Prop Firm)

| Risk/Trade | Phase 1 P(10% DD) | M5 Enhanced P(10% DD) |
| --- | --- | --- |
| 0.5% | 0.0% | 0.0% |
| 1.0% | 0.01% | 0.0% |
| 1.5% | 0.25% | 0.0% |
| 2.0% | 1.94% | 0.0% |


# Section 3: Kelly Criterion


## 3.1 Phase 1 Kelly

| Metric | Value |
| --- | --- |
| Win Rate | 61.1% |
| Avg Win (R) | 1.1674 |
| Avg Loss (R) | 0.5421 |
| Odds Ratio (b) | 2.1536 |
| Full Kelly | 43.05% |
| Half Kelly | 21.53% |
| Quarter Kelly | 10.76% |


### Kelly Bootstrap Uncertainty (1,000 iterations)

| Metric | Value |
| --- | --- |
| Median Kelly | 42.91% |
| P5 (worst case) | 11.45% |
| P25 | 30.09% |
| P75 | 55.33% |
| P95 (best case) | 70.71% |
| P(negative Kelly) | 1.3% |

**P5 Kelly is positive (11.45%)** — even worst-case bootstrap suggests a real edge.


## 3.2 M5 Enhanced Kelly

| Metric | Value |
| --- | --- |
| Win Rate | 78.6% |
| Avg Win (R) | 1.1674 |
| Avg Loss (R) | 0.1179 |
| Full Kelly | 76.41% |
| Half Kelly | 38.2% |
| Quarter Kelly | 19.1% |


### Kelly Bootstrap Uncertainty

| Metric | Value |
| --- | --- |
| Median Kelly | 76.31% |
| P5 | 52.94% |
| P95 | 91.92% |
| P(negative Kelly) | 0.0% |


## 3.3 Practical Position Sizing Recommendation

Given the small sample sizes (14-18 trades), Kelly fractions are unreliable as absolute sizing guides.



**Recommendation:**

- Use **1.0% risk per trade** as the baseline (well below any Kelly estimate)

- This is conservative enough to survive even adversarial sequences

- Only increase to 1.5% after 50+ validated trades with sustained positive expectancy

- For prop firm challenges (10% DD limit): stay at **0.75-1.0%** per trade


# Section 4: Per-Framework Breakdown


## 4.1 ob_retest (101 trades)

| Metric | Value |
| --- | --- |
| Total Trades | 101 |
| Win Rate | 69.3% |
| Avg R | 0.235 |
| Total R | 23.69 |
| Median R | 0.19 |


### By Kill Zone

| Kill Zone | Trades | Win Rate | Avg R | Total R |
| --- | --- | --- | --- | --- |
| london | 58 | 74.1% | 0.194 | 11.24 |
| ny | 43 | 62.8% | 0.29 | 12.45 |


### By Grade

| Grade | Trades | Win Rate | Avg R |
| --- | --- | --- | --- |
| A+ | 70 | 71.4% | 0.312 |
| A | 31 | 64.5% | 0.06 |


### By Direction

| Direction | Trades | Win Rate | Avg R |
| --- | --- | --- | --- |
| LONG | 95 | 68.4% | 0.242 |
| SHORT | 5 | 80.0% | 0.072 |


### Monthly Equity Curve

| Month | Trades | R Earned |
| --- | --- | --- |
| 2024-04 | 3 | 1.82 |
| 2024-07 | 3 | 2.11 |
| 2024-08 | 1 | 0.16 |
| 2024-09 | 1 | -1.0 |
| 2024-10 | 2 | 0.03 |
| 2025-01 | 5 | 5.31 |
| 2025-02 | 13 | -0.92 |
| 2025-03 | 10 | 2.36 |
| 2025-04 | 4 | -1.17 |
| 2025-05 | 3 | 2.68 |
| 2025-06 | 7 | -2.3 |
| 2025-09 | 7 | 2.11 |
| 2025-10 | 8 | 4.4 |
| 2025-12 | 9 | 3.58 |
| 2026-01 | 16 | 2.99 |
| 2026-02 | 6 | 2.15 |
| 2026-03 | 3 | -0.62 |


## 4.2 session_sweep (10 trades)

| Metric | Value |
| --- | --- |
| Total Trades | 10 |
| Win Rate | 20.0% |
| Avg R | -0.152 |
| Total R | -1.52 |


*session_sweep was retired due to poor performance. Data confirms the decision.*


# Section 5: Drawdown Analysis

| Metric | Value |
| --- | --- |
| Total Trades | 111 |
| Total R Earned | 22.17 |
| Max Drawdown (R) | 4.79 |
| DD Peak Date | 2025-03-19 |
| DD Trough Date | 2025-06-26 |
| DD Duration (trades) | 18 |
| Recovery (trades) | 17 |
| Max Consecutive Losses | 4 |


## Monthly R (Chronological)

| Month | Total R |
| --- | --- |
| 2024-04 | 1.82 |
| 2024-07 | 2.11 |
| 2024-08 | 0.16 |
| 2024-09 | -1.0 |
| 2024-10 | 0.03 |
| 2025-01 | 5.31 |
| 2025-02 | -1.92 |
| 2025-03 | 1.36 |
| 2025-04 | -1.17 |
| 2025-05 | 2.68 |
| 2025-06 | -3.3 |
| 2025-09 | 1.11 |
| 2025-10 | 6.85 |
| 2025-12 | 3.58 |
| 2026-01 | 0.99 |
| 2026-02 | 2.15 |
| 2026-03 | 1.41 |


### Months Below -2R

- **2025-06**: -3.3R (8 trades)


# Section 6: Multi-Instrument Sizing Framework


## 6.1 Independent Sizing

- Per-instrument risk: **1.0%**

- Max concurrent exposure: **2.0%**


## 6.2 Two Instruments (Gold + GBPUSD, ρ = 0.36)

- To keep portfolio risk at **2.0%**: size each at **1.21%**

- If both at 1%: combined risk = **1.65%**

- Diversification benefit: **17.5%** vs. uncorrelated


## 6.3 Three Instruments (Gold + GBPUSD + NAS100)

- Correlations: Gold-GBP=0.36, Gold-NAS=0.16, GBP-NAS=0.25

- To keep portfolio risk at **2.0%**: size each at **0.94%**

- If all at 1%: combined risk = **2.13%**


# Summary & Recommendations

### Key Findings



1. **Edge confirmed:** Phase 1 avg R = +0.503 per trade at 1.5R TP

2. **Monte Carlo (50 trades):** P5 outcome = 14.12R, P50 = 25.2R, Prob negative after 50 = 0.0%

3. **Kelly:** Full = 43.05%, Bootstrap P5 = 11.45%

4. **Max drawdown (111 trades):** 4.79R, max 4 consecutive losses

5. **Position sizing:** 1% per trade is well within safe parameters

6. **Multi-instrument:** 1% per instrument is fine — combined risk at 1.65%
