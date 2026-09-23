# Constrained Kelly Analysis — GTOS (Q-7.1)

**Script:** `compute_constrained_kelly_v1.py`  
**Date:** 2026-04-11  
**Seed:** 42  
**Monte Carlo paths:** 50,000 per risk fraction  
**Author:** Claude Code (Opus 4.6)

---

## 0. Data Sources

| Instrument | Source | Format |
|------------|--------|--------|
| XAUUSD | `research/kap_outputs/tests/trailing_stop_details_overall.csv` | `original_r` column (no trailing stop) |
| US30 | `knowledge_base/sessions/US30_cash/*.json` | `trade_summary.r_multiple` |
| USDJPY | `knowledge_base/sessions/USDJPY/*.json` | `trade_summary.r_multiple` |
| GBPUSD | `knowledge_base/sessions/GBPUSD/*.json` | `trade_summary.r_multiple` |
| GBPJPY | `knowledge_base_backtest/sessions/GBPJPY/*.json` | `trade_summary.r_multiple` |

---

## 1. Empirical R-Distribution Summary

### 1a. Per-Instrument Statistics

| Instrument | n | WR | Mean R | Median R | Std | Skew | Ex.Kurt | Min | Max | Avg Win | Avg Loss |
|------------|---|----|----|------|-----|------|---------|-----|-----|---------|----------|
| XAUUSD | 100 | 65.0% | +0.4748 | +0.2200 | 1.3399 | +0.866 | +0.144 | -1.0000 | +4.1400 | +1.1785 | -0.8320 |
| US30 | 37 | 59.5% | +0.3978 | +0.5200 | 1.1487 | +0.305 | -0.880 | -1.0000 | +2.6700 | +1.1805 | -0.7500 |
| USDJPY | 28 | 75.0% | +0.5446 | +0.3700 | 1.1704 | +0.461 | -0.200 | -1.0000 | +3.5100 | +1.0248 | -0.8957 |
| GBPJPY | 40 | 62.5% | +0.2165 | +0.1850 | 1.1061 | +0.848 | +0.166 | -1.0000 | +2.9700 | +0.8448 | -0.8307 |
| GBPUSD | 21 | 66.7% | +0.6990 | +0.7500 | 1.3445 | -0.025 | -1.395 | -1.0000 | +2.7000 | +1.4800 | -0.8629 |
| COMBINED | 226 | 65.0% | +0.4460 | +0.2600 | 1.2472 | +0.684 | -0.124 | -1.0000 | +4.1400 | +1.1288 | -0.8246 |

### 1b. Combined Histogram (n=226)

```
  [-1.00,-0.66) | ############################## 63
  [-0.66,-0.31) | #                              3
  [-0.31,+0.03) | ######                         14
  [+0.03,+0.37) | ###################            41
  [+0.37,+0.71) | ##########                     23
  [+0.71,+1.06) | ##########                     21
  [+1.06,+1.40) | #####                          12
  [+1.40,+1.74) | ####                           10
  [+1.74,+2.08) | ######                         13
  [+2.08,+2.43) | ###                            7
  [+2.43,+2.77) | ###                            8
  [+2.77,+3.11) | #                              4
  [+3.11,+3.45) |                                1
  [+3.45,+3.80) | #                              4
  [+3.80,+4.14) |                                2
```

> **Note:** GBPJPY canonical WR should be ~57% per QRC; observed 62.5% here reflects the
> specific backtest subset loaded. GBPUSD sample (n=21) is at the minimum threshold for
> per-instrument analysis. USDJPY shows the highest empirical WR (75%) consistent with QRC.

---

## 2. Kelly Estimates

### 2a. Combined Distribution

**Combined n = 226**, WR = 65.0%, Mean R = +0.4460

| Method | f* | Notes |
|--------|-----|-------|
| Binary Kelly | 0.3951 (39.51%) | p=65.0%, b=1.1288/0.8246=1.369 |
| Empirical Kelly | 0.3650 (36.50%) | Grid search, E[log(1+f·R)] maximized |
| Fat-tail (Osorio) | 0.3187 (31.87%) | ν=15.76, g(ν)=(ν-2)/ν=0.8731 |

**Ratio empirical/binary Kelly:** 0.9238  
*(Using empirical distribution deflates the Kelly fraction by 7.6% vs. the binary approximation)*

### 2b. Student-t Fit Diagnostics

- Representative ν (used for fat-tail adjustment) = 15.758
- Fat tails present (ν<30)
- Osorio shrinkage g(ν) = (ν-2)/ν = 0.8731
- **Note:** Combined distribution has negative excess kurtosis (platykurtic) due to cross-instrument mixing. Raw combined ν = 29257028141 (≈ Gaussian). Per-instrument XAUUSD ν = 15.76 used as conservative representative for fat-tail risk.

---

## 3. FTMO-Constrained Kelly (Monte Carlo)

**FTMO Parameters:**
- Starting equity: $100,000
- Profit target: $110,000 (+10%)
- Max daily loss: $5,000 from intraday daily peak (5%)
- Max total loss: $10,000 from all-time equity peak (10%)
- Time limit: 22 trading days (~30 calendar)
- Trade frequency: 17/month → Poisson(0.773) per trading day
- Seed: 42 (seed+i per fraction for independence)

**Model note:** Daily DD is tracked intraday (per-trade), not end-of-day.
This is conservative vs. FTMO's stated EOD measurement, so actual P(fail_daily)
is an upper bound on real risk.

### 3a. Full Results Table (combined n=226 distribution)

| f% | P(pass) | P(fail daily) | P(fail total) | P(total fail) | P(timeout) | Median Final | Median Surv | 5th Pctl Surv | DD med% | DD p95% | DD p99% |
|----|---------|--------------|--------------|----------------|------------|-------------|-------------|----------------|---------|---------|---------|
| 0.25% | **0.000** | 0.000 | 0.000 | 0.000 | 1.000 | $101,816 | $100,000 | $nan | 0.52% | 1.20% | 1.59% |
| 0.50% | **0.027** | 0.000 | 0.000 | 0.000 | 0.973 | $103,660 | $110,368 | $110,026 | 1.05% | 2.43% | 3.17% |
| 0.75% | **0.186** | 0.000 | 0.000 | 0.000 | 0.814 | $105,467 | $110,598 | $110,047 | 1.59% | 3.63% | 4.81% |
| 1.00% | **0.375** | 0.000 | 0.000 | 0.000 | 0.625 | $107,472 | $110,800 | $110,060 | 2.09% | 4.81% | 6.40% |
| 1.25% | **0.520** | 0.001 | 0.001 | 0.002 | 0.478 | $110,058 | $111,001 | $110,075 | 2.55% | 5.93% | 7.87% |
| 1.50% | **0.620** | 0.001 | 0.006 | 0.007 | 0.372 | $110,372 | $111,197 | $110,087 | 2.98% | 6.91% | 9.03% |
| 2.00% | **0.733** | 0.015 | 0.027 | 0.042 | 0.225 | $110,908 | $111,612 | $110,123 | 2.95% | 8.44% | 9.70% |
| 2.50% | **0.746** | 0.095 | 0.044 | 0.139 | 0.114 | $111,136 | $111,944 | $110,154 | 2.72% | 8.77% | 9.76% |
| 3.00% | **0.745** | 0.152 | 0.043 | 0.195 | 0.059 | $111,342 | $112,347 | $110,189 | 3.16% | 8.83% | 9.63% |
| 4.00% | **0.757** | 0.134 | 0.088 | 0.223 | 0.020 | $111,860 | $113,122 | $110,268 | 4.02% | 8.61% | 9.64% |
| 5.00% | **0.554** | 0.404 | 0.041 | 0.445 | 0.001 | $110,600 | $113,792 | $110,316 | 0.00% | 9.61% | 9.75% |

**f* (optimal) = 4.00%** → P(pass) = 0.757
**f_safe = 3.00%** (largest f where P(total DD violation) < 5%, monotone region)

> **Non-monotonicity note:** At very high f (e.g., 5%), P(fail_total) can appear to drop
> below 5% even though total failure rate is high. This happens because daily DD limits kill
> paths *before* they reach total DD — so P(fail_total specifically) decreases while
> P(fail_daily) explodes. f_safe is computed from the monotone increasing region only.

---

## 4. Sensitivity Analysis

### 4a. WR=59% Stress Test (conservative estimate)

The 2026-only WR is 59.5%. This resamples the combined distribution by randomly
flipping winners to losers until WR=59% (seed=42).

| f% | P(pass) | P(fail daily DD) | P(fail total DD) | P(timeout) | Median Final |
|----|---------|-----------------|-----------------|------------|-------------|
| 0.25% | **0.000** | 0.000 | 0.000 | 1.000 | $101,291 |
| 0.50% | **0.013** | 0.000 | 0.000 | 0.987 | $102,574 |
| 0.75% | **0.111** | 0.000 | 0.000 | 0.889 | $103,856 |
| 1.00% | **0.254** | 0.000 | 0.001 | 0.744 | $105,200 |
| 1.25% | **0.380** | 0.001 | 0.007 | 0.611 | $106,663 |
| 1.50% | **0.480** | 0.003 | 0.024 | 0.494 | $108,961 |
| 2.00% | **0.602** | 0.029 | 0.070 | 0.299 | $110,434 |
| 2.50% | **0.622** | 0.140 | 0.096 | 0.141 | $110,622 |
| 3.00% | **0.622** | 0.227 | 0.083 | 0.068 | $110,721 |
| 4.00% | **0.644** | 0.193 | 0.143 | 0.020 | $111,088 |
| 5.00% | **0.466** | 0.464 | 0.069 | 0.001 | $103,560 |

**f* at WR=59% = 4.00%** → P(pass) = 0.644
**f_safe at WR=59% = 1.50%** (P(total DD violation) < 5%)
*(vs. f*=4.00% at WR=65% — shift of +0.00pp in optimal fraction)*

### 4b. Per-Instrument Kelly

| Instrument | n | WR | Binary f* | Empirical f* | ν (Student-t) | Fat-tail f* |
|------------|---|----|-----------|-----------|----|-------------|
| XAUUSD | 100 | 65.0% | 0.4029 (40.29%) | 0.3620 (36.20%) | 15.76 | 0.3161 |
| US30 | 37 | 59.5% | 0.3370 (33.70%) | 0.3520 (35.20%) | ~∞ (Gaussian) | 0.3520 |
| USDJPY | 28 | 75.0% | 0.5315 (53.15%) | 0.4900 (49.00%) | ~∞ (Gaussian) | 0.4900 |
| GBPJPY | 40 | 62.5% | 0.2563 (25.63%) | 0.2140 (21.40%) | 11.00 | 0.1751 |
| GBPUSD | 21 | 66.7% | 0.4723 (47.23%) | 0.4640 (46.40%) | ~∞ (Gaussian) | 0.4640 |

> GBPUSD (n=21) and GBPJPY (n=40) have smaller samples; use their Kelly estimates
> with caution. USDJPY shows highest per-instrument Kelly due to 75% WR.

### 4c. Fractional Kelly Mapping (vs. current 1%)

Using combined distribution (WR=65%), nearest simulated risk fraction:

| Fraction | f | f% | Nearest Sim | P(pass)† | P(fail total DD)† |
|----------|---|--|----|---------|-----------------|
| Full Kelly | 0.3650 | 36.50% ⚠† | 5.00% | 0.554 | 0.041 |
| Half Kelly | 0.1825 | 18.25% ⚠† | 5.00% | 0.554 | 0.041 |
| Quarter Kelly | 0.0912 | 9.12% ⚠† | 5.00% | 0.554 | 0.041 |
| Eighth Kelly | 0.0456 | 4.56% | 5.00% | 0.554 | 0.041 |
| Current (1%) | 0.0100 | 1.00% | 1.00% | 0.375 | 0.000 |

> **Current system (1%):** P(pass) = 0.375, P(fail total DD) = 0.000
>
> **†** Full/Half/Quarter Kelly all exceed 5% (top of simulation grid). P(pass) shown is for the nearest simulated fraction (5%). At those actual fractions, ruin is near-certain — unconstrained Kelly is far too aggressive for FTMO.

---

## 5. Summary and Recommendation

### Optimal f* = 4.00%  
### Safe f_safe (P(total DD violation) < 5%) = 3.00%

### Key Findings

1. **Empirical Kelly vs. Binary Kelly:**
   - Binary Kelly = 0.3951 (39.51%)
   - Empirical Kelly = 0.3650 (36.50%)
   - Fat-tail adjusted = 0.3187 (31.87%)
   - The real distribution reduces the estimate by 7.6% vs. the binary approximation

2. **FTMO Constraint Impact:**
   - Unconstrained empirical Kelly = 36.50% — significantly above FTMO safe limits
   - FTMO-optimal f* = 4.00% — what maximizes P(pass challenge)
   - f_safe = 3.00% — largest fraction with P(total DD fail) < 5%

3. **Current 1% Risk Assessment:**
   - At 1%: P(pass) = 0.375, P(fail total DD) = 0.000, P(fail daily DD) = 0.000
   - Current 1% is within f_safe bounds.
   - Increasing to f*=4.00% would improve P(pass) by 38.2pp

4. **WR=59% Sensitivity:**
   - Optimal f* drops to 4.00% under conservative WR
   - P(pass) drops by 11.3pp
   - Even at conservative WR, system remains viable for FTMO

### Plain-Language Recommendation

The current **1% risk per trade** is:

- **Below optimal:** P(pass FTMO challenge) < 50%
- If WF-1 walk-forward confirms edge, **4.00%** risk maximizes FTMO pass rate.
- Do not exceed **3.00%** if maintaining P(10% DD violation) < 5%.
- The H29 drawdown reduction (1% → 0.5% at 8% DD) is consistent with these bounds.
- Fat-tail risk is real (ν≈15.8): the Osorio shrinkage toward 31.87% is well-motivated.

**Decision:** No immediate change recommended. Current 1% is within safe bounds.
Revisit after 30+ live trades with WF-1 data.

---

## 6. Assumptions and Limitations

1. **Data source mixing:** XAUUSD R from `original_r` (no trailing stop); other instruments
   from `r_multiple` in session JSON files (may include partial close behavior differences).

2. **Sample sizes:** GBPUSD (n=21) is at minimum threshold. Treat per-instrument Kelly for
   GBPUSD as indicative only.

3. **IID assumption:** Monte Carlo draws with replacement assumes trades are independent.
   Autocorrelation in W/L runs (checked at lag-1 in weekly monitoring) would alter results.

4. **Daily DD modeling:** Tracking daily DD intraday (per-trade) is conservative vs. FTMO's
   EOD-measured daily DD rule. Actual P(fail_daily) in live trading would be lower.

5. **Trade frequency:** 17 trades/month is the batch average across all instruments.
   Current live system has zero trades in first 4 days — frequency may be lower in WF-1.
   Lower frequency reduces both P(pass) and P(DD violation) proportionally.

6. **Stationarity:** The empirical distribution spans Oct 2025 to Mar 2026 (primarily).
   CLAUDE.md confirms WR decay: 73% → 59% over 4 quarters. If decay continues, the
   conservative WR=59% scenario is the more relevant estimate.

7. **No slippage or spread:** R-multiples from batch may not fully account for spread.
   Live execution costs would shift the distribution left (lower mean R).

8. **Single-path compounding:** Each trade risks `f × current_equity` (compound Kelly).
   In practice, lot sizing is discrete — fractional lots create small deviations.

9. **365 total trades:** CLAUDE.md states 367 batch trades. Only 226 unique trades were
   found across all session files. The remaining ~141 trades are not accessible in this
   run. Results reflect 226/367 (62%) of the available batch population.

10. **Correlation structure ignored:** Multi-instrument correlation (USDJPY+GBPJPY ≈ 0.6)
    means concurrent trades are NOT independent. Portfolio-level Kelly would be lower.
    This analysis treats each trade as standalone — appropriate for single-instrument sizing
    but not for portfolio-wide sizing decisions.

---

*Report generated: 2026-04-11*  
*n_paths = 50,000  |  seed = 42  |  FTMO params: start=$100,000, target=$110,000, max_daily=$5,000, max_total=$10,000*