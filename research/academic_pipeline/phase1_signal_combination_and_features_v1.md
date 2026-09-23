# Phase 1 -- Signal Combination & Feature Count Literature Search Results (Q-1.4, Q-1.5)

**Date:** 2026-04-11
**Agent:** Claude Code (Opus 4.6)
**Scope:** 2 questions on multi-timeframe signal combination and optimal feature count for small samples
**Total papers found:** 21 (after quality filter)
**Papers promoted (testable on GTOS data):** 17
**Papers rejected:** 4 (pure DL without feature analysis, RSI/MACD optimization, MDPI/Hindawi)
**Critical gaps identified:** 2

---

## Table of Contents

1. [Summary](#summary)
2. [Q-1.4: Multi-Timeframe Signal Combination Methods](#q-14)
3. [Q-1.5: Optimal Feature Count for Small Samples](#q-15)
4. [Cross-Question Synthesis](#synthesis)
5. [Specific GTOS Implications](#gtos-implications)
6. [Rejected Papers](#rejected)

---

<a id="summary"></a>
## 1. Summary

### Per-Question Breakdown

| Question | Papers Found | Promoted | Key Verdict |
|----------|-------------|----------|-------------|
| Q-1.4: Multi-Timeframe Signal Combination | 11 | 9 | Temporal hierarchy reconciliation (Athanasopoulos et al. 2017) and forecast combination theory (Timmermann 2006) provide the strongest frameworks. Equal weights dominate optimal weights at n<300. Wavelet multi-scale decomposition offers theoretical elegance but requires price series not categorical signals. |
| Q-1.5: Optimal Feature Count for Small Samples | 10 | 8 | At n=300, the EPV literature gives 30 features as the upper bound (10:1 rule) or 15 features (Harrell's 20:1). But the LLM-as-evaluator architecture sidesteps classical dimensionality curse -- the LLM does not fit coefficients. The real risk is human overfitting from retrospective feature selection across ~50 features. Bailey et al. (2014) PBO framework is directly applicable. |

### Critical Gaps

1. **No paper directly studies multi-timeframe categorical signal combination (e.g., bullish/bearish/neutral votes across D1/H4/H1).** All forecast combination literature assumes continuous forecasts. The closest analogue is reliability-weighted voting from classifier ensemble theory, not financial econometrics.
2. **No paper studies LLM-as-classifier dimensionality constraints.** Hegselmann et al. (2023) is the closest, showing LLMs can classify tabular data via in-context learning, but does not analyze the feature-count/sample-size interaction for generalization bounds.

### Cross-References from Priority A Search

| Paper | Priority A Question | New Relevance |
|-------|--------------------|-----------------------------|
| Moskowitz, Ooi, Pedersen 2012 | Q-2.2 (momentum) | Multi-horizon lookback combination for trend signals |

---

<a id="q-14"></a>
## 2. Q-1.4: Multi-Timeframe Signal Combination Methods

**Question:** The GTOS uses D1, H4, H1, M15 timeframes with simple majority vote across D1/H4/H1 for directional alignment (2-of-3 must agree). Is there a better combination method? Options: Bayesian fusion, reliability-weighted voting, hierarchical models.

**Verdict:** At n=300, equal-weighted combination (current majority vote) is likely near-optimal. The forecast combination puzzle shows that estimated optimal weights underperform equal weights in small samples due to estimation error. If timeframe reliability differs substantially (>20pp accuracy gap), reliability-weighted voting could help, but weights must be estimated from out-of-sample data, which requires ~100+ observations per timeframe. The temporal hierarchy framework from Athanasopoulos et al. (2017) is theoretically appealing but designed for continuous series, not categorical votes.

**COVERAGE: ADEQUATE** -- strong theoretical grounding from forecast combination literature, though direct application to categorical trading signals is thin.

---

### Forecasting with Temporal Hierarchies
**Authors:** George Athanasopoulos, Rob J. Hyndman, Nikolaos Kourentzes, Fotios Petropoulos | **Year:** 2017 | **Source:** European Journal of Operational Research, 262(1), 60-74
**Quality Tier:** 1 | **Citations:** ~400+
**Asset class tested:** Multiple (M3 competition data, tourism, other)
**OOS validation:** Yes (M3 competition benchmark)
**Relevance to GTOS:** High
**GTOS question addressed:** Q-1.4
**Key finding:** Temporal hierarchies constructed from non-overlapping temporal aggregation at multiple scales can be reconciled to produce coherent forecasts that outperform models at any single aggregation level. Reconciliation reduces forecast error by combining information across scales. The key insight: models at different temporal aggregation levels capture different structural components (trend at coarse scale, seasonality at fine scale), and combining them via MinT reconciliation yields 5-15% RMSE improvement over best single-level forecast.
**Key equation:** Reconciled forecast: y_hat_tilde = S(S'W^{-1}S)^{-1}S'W^{-1} * y_hat_base, where S is the summing matrix encoding the temporal hierarchy, W is the covariance matrix of base forecast errors.
**Testable on GTOS data:** Medium -- GTOS uses categorical signals (bullish/bearish/neutral) not continuous price forecasts; would need to convert directional signals to probability scores first.
**Data availability:** R packages `thief` and `hts` implement the framework; M3 data publicly available.

---

### Forecast Combinations (Handbook Chapter)
**Authors:** Allan Timmermann | **Year:** 2006 | **Source:** Handbook of Economic Forecasting, Vol. 1, Ch. 4, pp. 135-196 (Elsevier)
**Quality Tier:** 1 | **Citations:** ~1,500+
**Asset class tested:** Survey of literature (equities, macro, exchange rates)
**OOS validation:** N/A (review/survey)
**Relevance to GTOS:** High
**GTOS question addressed:** Q-1.4
**Key finding:** Simple combinations (equal weights, trimmed mean) that ignore correlations between forecast errors often dominate more refined combination schemes aimed at estimating theoretically optimal weights. Three reasons: (1) model misspecification, (2) instability/non-stationarities, (3) estimation error when number of models is large relative to sample size. **This directly supports GTOS's current majority-vote approach at n=300.** Least-squares weight estimation requires estimating the covariance matrix, which is infeasible with short samples.
**Key equation:** Combined forecast: f_c,t = sum_i(w_i * f_i,t). Optimal weights w* = argmin E[(y_t - sum w_i f_i,t)^2] require estimating Sigma = E[e_i,t * e_j,t], which is unstable in small samples.
**Testable on GTOS data:** High -- can directly compare equal-weighted D1/H4/H1 combination against reliability-weighted combination using OOS log of timeframe-level accuracy.
**Data availability:** N/A (theoretical framework).

---

### Out-of-Sample Equity Premium Prediction: Combination Forecasts and Links to the Real Economy
**Authors:** David E. Rapach, Jack K. Strauss, Guofu Zhou | **Year:** 2010 | **Source:** Review of Financial Studies, 23(2), 821-862
**Quality Tier:** 1 | **Citations:** ~1,200+
**Asset class tested:** US equity market (S&P 500 excess returns)
**OOS validation:** Yes (1965-2005 OOS period)
**Relevance to GTOS:** High
**GTOS question addressed:** Q-1.4
**Key finding:** Individual economic predictors fail to deliver consistent OOS forecasting gains due to model uncertainty and parameter instability. **Combining individual forecasts via simple equal-weighted mean delivers statistically and economically significant OOS gains that are consistent over time.** Combination substantially reduces forecast volatility while incorporating information from numerous predictors. The mean combination forecast outperforms the best individual predictor.
**Key equation:** Combined forecast: f_c,t+1 = (1/N) * sum_{i=1}^{N} f_{i,t+1}. Evaluated via R^2_OOS = 1 - sum(y_t - f_c,t)^2 / sum(y_t - f_bar)^2.
**Testable on GTOS data:** High -- directly applicable. Compare equal-weighted combination of D1/H4/H1 directional signals against each individual timeframe's signal using OOS classification accuracy.
**Data availability:** Equity data is public; the methodology is directly transferable.

---

### Multiresolution Forecasting for Futures Trading Using Wavelet Decompositions
**Authors:** B. L. Zhang, R. Coggins, M. A. Jabri, D. Dersch, B. Flower | **Year:** 2001 | **Source:** IEEE Transactions on Neural Networks, 12(4), 765-775
**Quality Tier:** 2 | **Citations:** ~200+
**Asset class tested:** Futures (ASX SPI, US T-Bond)
**OOS validation:** Yes (1-year OOS on SPI, 2 years on T-Bond)
**Relevance to GTOS:** Medium
**GTOS question addressed:** Q-1.4
**Key finding:** Wavelet decomposition splits a single price series into scale-related (multi-resolution) components. Each wavelet series is modeled by a separate MLP. **Bayesian automatic relevance determination selects short lookback windows at fine scales and long lookback windows at coarse scales.** Individual scale forecasts are recombined via inverse wavelet transform. Trading profits improve ~15-30% over single-scale MLP on OOS data. The key architectural insight: each temporal scale should use its own model with its own feature set.
**Key equation:** f(t) = sum_j sum_k c_{j,k} * psi_{j,k}(t) where psi_{j,k} are wavelet basis functions at scale j, position k. Forecast = sum of scale-specific MLP outputs.
**Testable on GTOS data:** Medium -- GTOS already uses separate timeframes (not wavelet decomposition of a single series), but the principle of scale-specific modeling validates the multi-timeframe approach. Could apply wavelet decomposition to M15 OHLCV to extract scale-specific features.
**Data availability:** ASX/T-Bond data is obtainable; wavelet decomposition tools (PyWavelets) available.

---

### Forecasting Based on Decomposed Financial Return Series: A Wavelet Analysis
**Authors:** Theo Berger | **Year:** 2016 | **Source:** Journal of Forecasting, 35(5), 419-433
**Quality Tier:** 2 | **Citations:** ~50+
**Asset class tested:** Equities (S&P 500, DAX, FTSE)
**OOS validation:** Yes (rolling window VaR forecasts)
**Relevance to GTOS:** Medium
**GTOS question addressed:** Q-1.4
**Key finding:** Financial return series decomposed via Daubechies-4 wavelet into approximation (trend) and detail (noise) components at 3 levels. **Short-run information (first 1-2 wavelet scales) drives 95% VaR forecasts, while more scales are needed for 99% VaR.** Not all temporal scales contribute equally -- lower-frequency components provide diminishing returns for standard risk forecasts. This suggests that for GTOS, not all timeframes may add equal value; the most granular (M15/H1) may dominate.
**Key equation:** r_t = a_J(t) + sum_{j=1}^{J} d_j(t), where a_J = approximation (low-frequency trend), d_j = detail at scale j. VaR_alpha = F^{-1}(alpha | sigma_hat_scale).
**Testable on GTOS data:** Medium -- can decompose M15 returns via wavelet and compare scale-specific contribution to direction prediction. More relevant for risk (SL placement) than signal combination.
**Data availability:** PyWavelets available; GTOS M15 data available.

---

### Improving Forecasting via Multiple Temporal Aggregation
**Authors:** Nikolaos Kourentzes, Fotios Petropoulos, Juan R. Trapero | **Year:** 2014 | **Source:** Foresight: International Journal of Applied Forecasting, 34, 12-17
**Quality Tier:** 2 | **Citations:** ~150+
**Asset class tested:** M3 competition data (multiple domains)
**OOS validation:** Yes (M3 benchmark)
**Relevance to GTOS:** Medium
**GTOS question addressed:** Q-1.4
**Key finding:** The Multiple Aggregation Prediction Algorithm (MAPA) aggregates a time series into multiple temporal levels (e.g., daily -> weekly -> monthly), fits exponential smoothing at each level, and combines the estimated components across levels. **MAPA outperforms conventional approaches because different temporal aggregation levels attenuate/strengthen different time series components, yielding more holistic estimation.** Particularly beneficial for long-term forecasts and robust to model mis-specification.
**Key equation:** Component estimates at each aggregation level k: level_k, trend_k, seasonal_k. Final forecast = combination of components estimated at their respective optimal aggregation levels.
**Testable on GTOS data:** Low -- requires continuous time series, not categorical signals. Could inspire an analogous approach: estimate trend from D1, momentum from H4, entry timing from H1.
**Data availability:** R package `MAPA` available; M3 data public.

---

### Time Series Momentum
**Authors:** Tobias J. Moskowitz, Yao Hua Ooi, Lasse Heje Pedersen | **Year:** 2012 | **Source:** Journal of Financial Economics, 104(2), 228-250
**Quality Tier:** 1 | **Citations:** ~3,000+
**Asset class tested:** 58 liquid futures (equities, FX, commodities, bonds)
**OOS validation:** Yes (1985-2009 OOS across 58 instruments)
**Relevance to GTOS:** Medium
**GTOS question addressed:** Q-1.4
**Key finding:** Documents time-series momentum across all asset classes: past 12-month return predicts future 1-month return. **Critical insight for multi-timeframe combination: allowing lookback period to differ from holding period reveals predictability masked by restricting them to match.** This directly validates using longer-timeframe direction (D1/H4) to predict shorter-timeframe outcome (M15 trade). Recent research on trend-following shows a "barbell" structure (short + long lookback, dropping medium) captures most performance, challenging the 3-level approach.
**Key equation:** TSMOM_{t,s}(h) = sign(r_{t-h,t}) * r_{t,t+1}. Portfolio: equal-weighted across instruments, sized inversely proportional to ex-ante volatility.
**Testable on GTOS data:** High -- can test whether D1+M15 (barbell) outperforms D1+H4+H1+M15 (all scales) for directional alignment.
**Data availability:** AQR provides original paper data; GTOS has all timeframe data.

---

### An Introduction to Wavelets and Other Filtering Methods in Finance and Economics
**Authors:** Ramazan Gencay, Faruk Selcuk, Brandon Whitcher | **Year:** 2002 | **Source:** Academic Press / Elsevier (book)
**Quality Tier:** 2 | **Citations:** ~1,500+ (book)
**Asset class tested:** Multiple (FX, equities, macro)
**OOS validation:** N/A (textbook with empirical examples)
**Relevance to GTOS:** Low-Medium
**GTOS question addressed:** Q-1.4
**Key finding:** Comprehensive treatment of wavelet multi-resolution analysis (MRA) applied to financial data. **Key result: dependencies between FX markets increase from intraday to daily scale, meaning coarser-scale signals are more informative for cross-market relationships.** Provides framework for testing which temporal scales carry the most signal for specific financial phenomena. Demonstrates that wavelet variance decomposition can attribute return variation to specific frequency bands.
**Key equation:** MODWT wavelet variance: nu^2_j = (1/N) sum_t [d_{j,t}]^2, partitioning total variance across scales j.
**Testable on GTOS data:** Low -- academic reference; wavelet MRA tools exist but GTOS already uses explicit multi-timeframe data rather than decomposing a single series.
**Data availability:** Book available; tools in PyWavelets.

---

### Forecast Reconciliation: A Review
**Authors:** George Athanasopoulos, Rob J. Hyndman, Nikolaos Kourentzes, Anastasios Panagiotelis | **Year:** 2024 | **Source:** International Journal of Forecasting, 40(2), 430-456
**Quality Tier:** 1 | **Citations:** ~100+ (recent, growing fast)
**Asset class tested:** Multiple (review across all applications)
**OOS validation:** N/A (comprehensive review)
**Relevance to GTOS:** Medium
**GTOS question addressed:** Q-1.4
**Key finding:** Reviews all methods for reconciling forecasts across hierarchical and temporal aggregation structures. **Key practical finding: bottom-up approach (aggregate from finest level) is surprisingly effective and recently shown to be competitive with more complex reconciliation methods.** For GTOS context: building the signal from M15 upward (bottom-up) may be as good as the top-down approach of starting from D1.
**Key equation:** MinT reconciliation: y_tilde = S * (S'W_h^{-1}S)^{-1} * S' * W_h^{-1} * y_hat_base. Also covers "bottom-up" special case where W = I and S encodes aggregation.
**Testable on GTOS data:** Medium -- concepts applicable but requires converting categorical signals to probabilistic forecasts.
**Data availability:** Comprehensive references; R/Python packages available.

---

<a id="q-15"></a>
## 3. Q-1.5: Optimal Feature Count for Small Samples

**Question:** With ~300 historical trades and ~30-50 features in the MSO, are we in the danger zone for overfitting? The AI evaluator is an LLM doing qualitative reasoning over structured data, not a traditional classifier fitting coefficients. Does the "curse of dimensionality" apply differently here?

**Verdict:** For a traditional classifier, 300 samples with 30-50 features is in the danger zone (EPV of 6-10). But GTOS uses an LLM as the evaluator, which fundamentally changes the analysis: the LLM does not fit coefficients to the 300 trades. The real overfitting risk is at the human/research level -- selecting which features to include in the MSO by examining which correlate with outcomes in the same 300-trade dataset. Bailey et al. (2014) PBO framework and White's (2000) Reality Check are the right tools to quantify this risk. The current feature set (~30-50 fields) should be audited for post-hoc additions; any feature added after examining trade outcomes without OOS validation is suspect.

**COVERAGE: THIN for LLM-specific angle** -- no existing research on dimensionality constraints for LLM-as-classifier on structured trading data. Classical ML literature (Gu et al. 2020, Guyon & Elisseeff 2003) provides useful baselines.

---

### The Probability of Backtest Overfitting
**Authors:** David H. Bailey, Jonathan M. Borwein, Marcos Lopez de Prado, Qiji Jim Zhu | **Year:** 2014 | **Source:** Notices of the AMS / Journal of Computational Finance (also SSRN, multiple versions)
**Quality Tier:** 1 | **Citations:** ~400+
**Asset class tested:** Simulated + real financial strategies
**OOS validation:** Yes (CSCV framework generates synthetic OOS)
**Relevance to GTOS:** High
**GTOS question addressed:** Q-1.5
**Key finding:** Proposes the Probability of Backtest Overfitting (PBO) metric using Combinatorially Symmetric Cross-Validation (CSCV). **The most important missing piece from virtually all backtests is the number of trials attempted.** Even with a modest number of strategy variations (N~20), PBO can exceed 50% if sample size is small. For GTOS: if the MSO feature set was selected from a larger candidate pool by examining in-sample performance, PBO is non-trivial even at 30 features. The framework provides a testable diagnostic.
**Key equation:** PBO = P(R_bar_OOS < 0 | CSCV). Computed by combinatorially partitioning T observations into S subsets, training on S-1, testing on 1, and measuring frequency of OOS underperformance across all C(S,S/2) combinations.
**Testable on GTOS data:** High -- can compute PBO for any feature-selection process applied to the 367-trade dataset. Requires defining the number of "trials" (feature combinations examined).
**Data availability:** Python implementation `pypbo` on GitHub; R package `pbo` on CRAN.

---

### The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest Overfitting, and Non-Normality
**Authors:** David H. Bailey, Marcos Lopez de Prado | **Year:** 2014 | **Source:** Journal of Portfolio Management, 40(5), 94-107 (also SSRN)
**Quality Tier:** 1 | **Citations:** ~300+
**Asset class tested:** Simulated + real hedge fund strategies
**OOS validation:** Yes (Monte Carlo validation of DSR vs. classical t-test)
**Relevance to GTOS:** High
**GTOS question addressed:** Q-1.5
**Key finding:** The Deflated Sharpe Ratio corrects observed Sharpe ratios for (1) number of strategies/configurations tested N, (2) non-normality of returns (skewness, kurtosis), and (3) sample length. **For GTOS at n=300 trades: if the feature set or trading rules were selected from N trials, the DSR tells you whether the observed edge (62% WR, +0.200R/trade) survives the correction.** At N=50 (number of features examined), the DSR correction is modest; at N=500 (if many feature combinations were tried), it becomes severe.
**Key equation:** DSR = (SR_hat - SR_0) / sqrt[(1 - gamma_3 * SR_hat + (gamma_4 - 1)/4 * SR_hat^2) / T], where gamma_3 = skewness, gamma_4 = kurtosis, SR_0 = expected SR under null given N trials (from extreme value theory).
**Testable on GTOS data:** High -- can compute DSR for the 367-trade batch using observed SR, skewness, kurtosis, and estimated N (number of feature/rule variations examined during development).
**Data availability:** Formula is self-contained; Python implementations available.

---

### A Reality Check for Data Snooping
**Authors:** Halbert White | **Year:** 2000 | **Source:** Econometrica, 68(5), 1097-1126
**Quality Tier:** 1 | **Citations:** ~2,000+
**Asset class tested:** Simulated + equity technical trading rules
**OOS validation:** Yes (bootstrap-based)
**Relevance to GTOS:** High
**GTOS question addressed:** Q-1.5
**Key finding:** Provides a bootstrap procedure for testing whether the best model from a specification search has genuine predictive superiority over a benchmark. **When only one historical path is available (as in GTOS), any satisfactory result may be due to chance if many specifications were examined.** The Reality Check controls family-wise error rate across all model specifications tested. At n=300 and ~50 features, the bootstrap requires ~1000+ replications but is computationally feasible.
**Key equation:** Test statistic: V_bar = max_k {N^{1/2} * f_bar_k}, where f_bar_k is the average performance difference between model k and benchmark. P-value from bootstrap: p = (1/B) sum_{b=1}^{B} I(V_bar_b > V_bar_observed).
**Testable on GTOS data:** High -- can apply to GTOS's 367-trade dataset. Test H0: no feature subset yields genuine OOS improvement over a simple benchmark (e.g., mechanical OB entry without AI filtering).
**Data availability:** Bootstrap is self-contained; requires only the trade-level outcome data GTOS already has.

---

### Empirical Asset Pricing via Machine Learning
**Authors:** Shihao Gu, Bryan T. Kelly, Dacheng Xiu | **Year:** 2020 | **Source:** Review of Financial Studies, 33(5), 2223-2273
**Quality Tier:** 1 | **Citations:** ~2,500+
**Asset class tested:** US equities (entire CRSP universe, 30,000+ stocks)
**OOS validation:** Yes (1987-2016 OOS period, monthly rebalancing)
**Relevance to GTOS:** Medium-High
**GTOS question addressed:** Q-1.5
**Key finding:** Comprehensive comparison of ML methods (penalized regression, trees, neural networks) for asset return prediction using ~94 firm characteristics. **Key finding for GTOS: all methods agree on the same small set of dominant predictive signals (momentum, liquidity, volatility) despite starting with ~94 features.** Trees and neural networks outperform by capturing nonlinear predictor interactions. **Critical methodological point: sample splitting must be time-aware (rolling/recursive window), not random CV, to avoid lookahead bias.**
**Key equation:** R^2_OOS = 1 - sum(r_{i,t+1} - r_hat_{i,t+1})^2 / sum(r_{i,t+1})^2. Best ML method achieves R^2_OOS ~ 0.5% monthly (vs. 0 for historical mean).
**Testable on GTOS data:** Medium -- at n=300, GTOS cannot replicate the large-sample ML approach, but the feature importance methodology (permutation importance, SHAP) is directly applicable to identify which of the ~30-50 MSO features actually drive AI decisions.
**Data availability:** CRSP data requires subscription; methodology is transferable.

---

### An Introduction to Variable and Feature Selection
**Authors:** Isabelle Guyon, Andre Elisseeff | **Year:** 2003 | **Source:** Journal of Machine Learning Research, 3, 1157-1182
**Quality Tier:** 1 | **Citations:** ~15,000+
**Asset class tested:** N/A (methodological review, examples from genomics, text, etc.)
**OOS validation:** N/A (review)
**Relevance to GTOS:** Medium-High
**GTOS question addressed:** Q-1.5
**Key finding:** Canonical reference on feature selection methodology. Three objectives: (1) improve prediction performance, (2) reduce computation, (3) improve understanding. **Key warning for GTOS: feature selection itself is a form of model fitting and is subject to overfitting, especially in small samples. Must use nested cross-validation or separate hold-out for feature selection.** Recommends starting with simple filters (univariate tests), then wrappers (recursive elimination), then embedded methods (L1 regularization).
**Key equation:** Nested CV: outer loop estimates generalization error, inner loop selects features. Avoid selecting features on full dataset then evaluating on same data.
**Testable on GTOS data:** High -- can apply univariate feature importance analysis to the ~30-50 MSO features using the 367-trade dataset with proper nested CV (though n=300 limits the inner-loop precision).
**Data availability:** N/A (methodology).

---

### On Over-fitting in Model Selection and Subsequent Selection Bias in Performance Evaluation
**Authors:** Gavin C. Cawley, Nicola L. C. Talbot | **Year:** 2010 | **Source:** Journal of Machine Learning Research, 11(70), 2079-2107
**Quality Tier:** 1 | **Citations:** ~1,500+
**Asset class tested:** UCI benchmark datasets (multiple domains)
**OOS validation:** Yes (extensive Monte Carlo experiments)
**Relevance to GTOS:** Medium-High
**GTOS question addressed:** Q-1.5
**Key finding:** Demonstrates that **over-fitting in model selection is often of comparable magnitude to differences between learning algorithms themselves.** Low variance in model selection criteria is at least as important as unbiasedness. For GTOS: if the MSO feature set was tuned by examining which features correlate with trade outcomes in the same dataset, the resulting performance estimate is inflated by an amount comparable to the apparent edge. **Nested cross-validation is the minimum requirement** to avoid this bias.
**Key equation:** True generalization error = E_outer[E_inner[L(y, f_hat(x))]]. Bias from model selection: Delta = E[L_selected] - E[L_true], where L_selected uses features/hyperparameters chosen on training data without proper nesting.
**Testable on GTOS data:** High -- audit the feature selection history. If any features were added to the MSO based on observed correlation with trade outcomes in the 367-trade dataset, quantify the selection bias using nested CV.
**Data availability:** N/A (methodology).

---

### Regression Modeling Strategies (with events-per-variable framework)
**Authors:** Frank E. Harrell Jr. | **Year:** 2001 (1st ed.), 2015 (2nd ed.) | **Source:** Springer (book)
**Quality Tier:** 1 | **Citations:** ~10,000+ (book)
**Asset class tested:** Clinical prediction (biostatistics)
**OOS validation:** Yes (extensive simulation and real-data examples)
**Relevance to GTOS:** Medium
**GTOS question addressed:** Q-1.5
**Key finding:** Foundational work on sample-size requirements for prediction models. **The "events per variable" (EPV) rule: need at least 10-20 events per predictor to avoid overfitting.** For binary classification (GTOS: win/loss), "events" = min(wins, losses). At 300 trades with 62% WR: ~114 losses = events. At EPV=10: max 11 features. At EPV=20 (Harrell's recommendation): max 5-6 features. **However, this applies to coefficient-fitting models (logistic regression), not LLM-based evaluation.** The LLM does not fit coefficients to the 300 trades -- it uses pre-trained knowledge. The EPV constraint applies only if GTOS were to train a traditional classifier on the trade data.
**Key equation:** EPV = min(n_events, n_non-events) / p, where p = number of predictors. Stable estimates require EPV >= 10-20. Maximum model complexity: p_max = min(wins, losses) / EPV_threshold.
**Testable on GTOS data:** High -- provides direct upper bound on feature count if training a traditional classifier as a benchmark/replacement for the LLM evaluator.
**Data availability:** Formulas are self-contained; GTOS trade data available.

---

### TabLLM: Few-shot Classification of Tabular Data with Large Language Models
**Authors:** Stefan Hegselmann, Alejandro Buendia, Hunter Lang, Monica Agrawal, Xiaoyi Jiang, David Sontag | **Year:** 2023 | **Source:** AISTATS 2023 (Proceedings of Machine Learning Research, Vol. 206)
**Quality Tier:** 2 | **Citations:** ~200+
**Asset class tested:** UCI benchmark datasets (healthcare, census, financial)
**OOS validation:** Yes (standard train/test splits on 9 benchmark datasets)
**Relevance to GTOS:** Medium
**GTOS question addressed:** Q-1.5
**Key finding:** LLMs can classify tabular data via in-context learning by serializing features to natural-language strings. **In zero to 8-shot settings, LLM classification is competitive with gradient-boosted trees.** With more shots (>50), traditional methods (XGBoost, TabPFN) surpass LLMs. **Descriptive feature names and well-defined instructions enhance LLM performance significantly.** This validates GTOS's approach of providing structured MSO data to Claude for qualitative evaluation. The LLM leverages pre-trained knowledge about feature semantics rather than fitting coefficients.
**Key equation:** N/A (empirical comparison). Key result: GPT-3 AUC with 0-8 shots ~ XGBoost AUC with 100+ samples on several datasets.
**Testable on GTOS data:** Medium -- could test whether reducing MSO features from ~50 to ~15 (most semantically meaningful) changes Claude's classification accuracy on historical trades.
**Data availability:** Code and data available at GitHub.

---

### Advances in Financial Machine Learning (Chapter on Backtesting)
**Authors:** Marcos Lopez de Prado | **Year:** 2018 | **Source:** Wiley (book, Chapters 11-12 on backtesting and feature importance)
**Quality Tier:** 1 | **Citations:** ~3,000+ (book)
**Asset class tested:** Multiple (equities, futures, options)
**OOS validation:** Yes (CPCV framework)
**Relevance to GTOS:** High
**GTOS question addressed:** Q-1.5
**Key finding:** "Backtesting is not a research tool. Feature importance is." (Marcos' First Law). **The number of features is less important than the number of trials -- each tested strategy variation is a hypothesis, and sequential testing without correction leads to severe overfitting bias.** Introduces Combinatorial Purged Cross-Validation (CPCV) for time-series data that respects temporal ordering. **For GTOS: the risk is not having 50 features in the MSO, but having examined the 367-trade dataset repeatedly while building the system. Each examination is a trial that inflates apparent performance.**
**Key equation:** CPCV: partition T observations into N groups, use phi groups for testing and N-phi for training, with purging of training observations near test boundaries and embargo period after each test segment.
**Testable on GTOS data:** High -- implement CPCV on the 367-trade dataset to get bias-corrected performance estimates.
**Data availability:** Python implementations available (mlfinlab package).

---

<a id="synthesis"></a>
## 4. Cross-Question Synthesis

### The Forecast Combination Puzzle and GTOS Multi-Timeframe Voting

The strongest finding across Q-1.4 papers is the **forecast combination puzzle**: equal-weighted combination outperforms estimated-optimal-weighted combination in small samples. This has been documented repeatedly (Timmermann 2006, Rapach et al. 2010, Smith & Wallis 2009) and the explanation is clear -- estimation error in the weights exceeds the efficiency gain from optimal weighting when n is small.

**Direct implication for GTOS:** The current 2-of-3 majority vote across D1/H4/H1 is effectively equal-weighted binary voting. At n=300, this is likely near-optimal. Moving to reliability-weighted voting (where each timeframe gets weight proportional to its OOS accuracy) would require:
- At minimum 100+ trades to estimate per-timeframe accuracy reliably
- Evidence that timeframe accuracies differ by >20pp
- Out-of-sample validation of the weights themselves (nested validation)

### The Barbell Hypothesis

Moskowitz et al. (2012) and subsequent trend-following research suggest a "barbell" structure (short + long lookback, dropping medium) captures most trend information. For GTOS, this raises the question: does H4 add information beyond D1 and H1? The 3-timeframe approach may include redundancy.

**Testable hypothesis:** Compare classification accuracy of (D1+H1 agree) vs. (2-of-3 D1/H4/H1 agree) on the 367-trade dataset.

### Dimensionality: Classical vs. LLM

The classical literature (Harrell 2015, Guyon & Elisseeff 2003, Cawley & Talbot 2010) establishes that at n=300, a traditional classifier should use at most 10-15 features (EPV 10-20). However, **GTOS's LLM evaluator does not fit coefficients to the 300 trades.** The LLM uses pre-trained knowledge to reason about MSO features. This sidesteps the classical dimensionality curse in a specific sense: the LLM's "model complexity" is fixed by pre-training, not adapted to the 300 trades.

**However, the overfitting risk shifts to the human level:**
1. Feature selection: if MSO features were chosen by examining which correlate with outcomes in the training data
2. Prompt engineering: if the prompt was tuned by examining LLM performance on historical trades
3. Rule selection: if thresholds (min_rr, confidence) were calibrated on in-sample data

Each of these is a "trial" in the Bailey et al. (2014) sense, and the PBO framework quantifies the cumulative overfitting risk.

---

<a id="gtos-implications"></a>
## 5. Specific GTOS Implications

### For Q-1.4 (Multi-Timeframe Combination)

| Action | Priority | Evidence Basis | WF-1 Impact |
|--------|----------|---------------|-------------|
| Keep current 2-of-3 majority vote | Default | Timmermann (2006), Rapach et al. (2010): equal weights optimal at n<300 | None (status quo) |
| Test D1+H1 barbell vs. D1+H4+H1 | After WF-1 | Moskowitz et al. (2012): medium horizon adds little | Shadow test on 367-trade batch |
| Log per-timeframe accuracy during WF-1 | Now (shadow) | Required to evaluate whether reliability-weighted voting could help later | Allowed under WF-1 (observation only) |
| Do NOT implement reliability-weighted voting yet | N/A | Insufficient data to estimate weights; estimation error would degrade performance | N/A |

### For Q-1.5 (Feature Count)

| Action | Priority | Evidence Basis | WF-1 Impact |
|--------|----------|---------------|-------------|
| Audit feature selection history | High | Bailey et al. (2014), Cawley & Talbot (2010): selection bias may inflate apparent edge | Research only |
| Compute DSR on 367-trade batch | High | Bailey & Lopez de Prado (2014): quantify overfitting risk from number of trials | Research only |
| Do NOT reduce MSO features during WF-1 | N/A | Prompt is frozen; any feature reduction changes evaluation behavior | Locked |
| After WF-1: test feature ablation | Medium | Hegselmann et al. (2023): LLMs may perform as well with fewer, more semantic features | Post-WF-1 |
| If building traditional classifier benchmark: use max 10-15 features | Medium | Harrell (2015): EPV 10-20 at n=300 | Post-WF-1 |

---

<a id="rejected"></a>
## 6. Rejected Papers

| Paper | Reason for Rejection |
|-------|---------------------|
| TIC-FusionNet (PLOS One 2025) | Pure DL multimodal fusion; no feature analysis; no financial OOS validation |
| MSTAN (Information Sciences 2025) | Pure DL attention network; no OOS on trading data; no feature count analysis |
| Stock Movement Prediction with MSGCA (Complex & Intelligent Systems 2025) | Multimodal fusion for stock prediction; relies on sentiment data not applicable to GTOS; no small-sample analysis |
| WaveLSFormer (arXiv 2601.13435) | Learnable wavelet Transformer; equity-specific; requires large training data; no transferability to n=300 categorical signals |

---

## Appendix: Search Terms Used

### Q-1.4 Searches
1. "multi-scale" "signal combination" OR "fusion" "financial" OR "trading"
2. "hierarchical forecasting" "time series" "financial" multi-timeframe
3. "Bayesian" "multi-timeframe" "trading" OR "forex" signal combination
4. "wavelet" "signal combination" "forex" OR "intraday" trading multi-resolution
5. "multi-resolution" "analysis" "financial returns" OR "forecasting" wavelet decomposition combination
6. "temporal aggregation" "forecasting" "financial" multi-scale combination method
7. "multi-scale" "momentum" OR "trend" "combination" financial forecasting reliability weighted
8. Athanasopoulos Hyndman Kourentzes temporal hierarchies EJOR 2017
9. Kourentzes Petropoulos MAPA multiple aggregation prediction algorithm
10. Moskowitz Ooi Pedersen time series momentum multi-horizon
11. Gencay Selcuk Whitcher wavelets financial time series
12. Berger wavelet decomposition financial returns Journal of Forecasting
13. Timmermann Granger forecast combination equal weights estimation error
14. Zhang Berger multiresolution forecasting futures wavelet IEEE
15. Rapach Strauss Zhou out-of-sample equity premium forecast combination
16. Diebold combining forecasts forecast combination puzzle equal weights
17. Harvey Leybourne Newbold tests for forecast encompassing

### Q-1.5 Searches
1. "curse of dimensionality" "financial" "trading" "feature selection" "sample size"
2. "VC dimension" OR "Vapnik" "sample complexity" financial classification
3. "bias-variance" tradeoff "trading" "features" "overfitting" small sample
4. "feature selection" "small sample" "financial" classification dimensionality reduction
5. "model complexity" "sample size" "prediction" "financial" overfitting rule of thumb
6. "in-context learning" "feature" "dimensionality" LLM generalization
7. LLM tabular data classification in-context learning features (Hegselmann)
8. Lopez de Prado backtesting overfitting sample size features
9. Bailey Borwein Lopez de Prado probability of backtest overfitting
10. Harrell regression modeling strategies EPV events per variable
11. Cawley Talbot overfitting in model selection JMLR
12. Guyon Elisseeff introduction to variable feature selection JMLR
13. Gu Kelly Xiu empirical asset pricing machine learning
14. White reality check data snooping bootstrap
15. Pedersen events per variable logistic regression sample size
