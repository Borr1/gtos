# Domain 03 — Distributional Characteristics & Tails

**Owner:** Phase 1 Worker Agent #3
**Date compiled:** 2026-04-28
**Method:** WebSearch + WebFetch (Google Scholar / arXiv / SSRN / journal pages / institutional repositories). Every paper has at least one verifiable URL; abstracts are summarised from the source page (1-3 sentences).
**Target paper count:** 40-55. **Delivered:** 50.

---

## 1. Scope statement (as executed)

This file collects empirical and theoretical studies of asset-return **distributions** and their **tails**: heavy tails, power-law scaling, stable distributions, generalised hyperbolic / NIG / VG, EVT (POT, block maxima, Hill estimator), volatility clustering as observed phenomenon, GARCH families and their stationary distributions, leverage effect, asymmetric tails, time-aggregation, multifractal moment scaling, copula tail dependence (bivariate-fact level only).

Papers are organised across the five clusters required by the domain spec:

- (a) **Tails / EVT** — Hill / POT / GPD / GEV / power laws / block-maxima / threshold selection
- (b) **Volatility clustering / GARCH families** — ARCH, GARCH, EGARCH, GJR, FIGARCH
- (c) **Realised volatility / high-frequency** — RV, bipower variation, kernels, HEAVY, jump tests
- (d) **Scaling / multifractal** — Mandelbrot, MMAR, MSM, multiscaling, MF-DFA, rough volatility
- (e) **Leverage / asymmetry & dependence** — leverage effect, conditional skew/kurt, copula tails

Each entry carries the special `gtos_diagnostic` field requested by spec §7: an MT5-runnable diagnostic GTOS could execute on its own XAU/USDJPY/etc data to test whether the paper's distributional claim holds.

Cross-domain handoff conflicts are flagged in `cross_domain_links`; full overlap rules are in spec `_INDEX.md` §2.

---

## 2. Foundational papers (pre-2010)

### 2.1 The Variation of Certain Speculative Prices

- **id:** 03-001
- **authors:** Benoit Mandelbrot
- **year:** 1963
- **source:** Journal of Business 36(4): 394-419
- **url:** https://web.williams.edu/Mathematics/sjmiller/public_html/341Fa09/econ/Mandelbroit_VariationCertainSpeculativePrices.pdf
- **abstract:** Studies cotton prices and concludes the empirical distribution is heavy-tailed and best described by a stable Paretian (Lévy alpha-stable) law rather than the Gaussian. Introduces the use of stable distributions (proposed alpha ≈ 1.7 for cotton) into finance and notes that price-change distributions look the same across time scales.
- **key_findings:**
  - Daily and monthly cotton returns have power-law (fat) tails, not Gaussian.
  - Stable Paretian distribution with α<2 implies infinite second moment.
  - Visible self-similarity ("all charts look alike") across timescales.
  - Extreme moves dominate return-distribution second moments.
  - Variance of returns is empirically unbounded as sample grows.
- **relevance_to_gtos:** Foundational anchor for `project_distributional_findings` (xi=0.35 for gold). Justifies treating XAU SL buffer with non-Gaussian quantiles, not z-score multiples of historical sigma. Heartbeat-flatten kill switch should sit on EVT-derived loss budget rather than 4-sigma threshold.
- **potential_hypothesis:** XAU 1m log returns should reject Gaussian fit at any sample size > 2000 (Anderson-Darling p < 1e-6) and admit a stable-Pareto fit with α in [1.5, 1.85].
- **cross_domain_links:** 04 (multifractal scaling), 21 (sizing under fat tails)
- **gtos_diagnostic:** Pull 6mo of XAU M1 from MT5; compute returns; fit Gaussian, t, stable; report KS, AIC.

### 2.2 The Long-Term Storage Capacity of Reservoirs

- **id:** 03-002
- **authors:** Harold Edwin Hurst
- **year:** 1951
- **source:** Transactions of the American Society of Civil Engineers 116: 770-808
- **url:** https://ascelibrary.org/doi/10.1061/TACEAT.0006518
- **abstract:** Introduces R/S (rescaled-range) analysis to quantify long-range dependence in geophysical and hydrological time series. The Hurst exponent H is now widely used to test for long memory in financial returns and volatility, with H ≠ 0.5 indicating dependence.
- **key_findings:**
  - R/S statistic scales as a power of time, with exponent H.
  - H = 0.5 indicates Brownian motion (no memory); H > 0.5 indicates persistence; H < 0.5 indicates anti-persistence.
  - Many natural series (Nile floods, tree rings, varves) show H ~ 0.7-0.8.
  - The estimator is biased in finite samples and sensitive to short-range dependence.
- **relevance_to_gtos:** Direct test of mean-reversion vs trending behaviour by instrument and timeframe. The OB-zone edge (~70%) should manifest as anti-persistence near key levels (H < 0.5 around OB midpoints). Provides framework for evaluating whether KZ-internal returns differ in memory structure from background.
- **potential_hypothesis:** H4 returns of XAUUSD will exhibit H ∈ [0.45, 0.50] (slight anti-persistence) inside London KZ but H ≈ 0.50 outside; the test discriminates KZ as a real liquidity regime.
- **cross_domain_links:** 04 (Hurst-of-volatility, Hurst-of-orderflow), 14 (trend persistence)
- **gtos_diagnostic:** R/S + DFA on 12mo M15 for each instrument; partition by KZ vs non-KZ; report H delta and bootstrap CI.

### 2.3 Autoregressive Conditional Heteroscedasticity with Estimates of the Variance of UK Inflation

- **id:** 03-003
- **authors:** Robert F. Engle
- **year:** 1982
- **source:** Econometrica 50(4): 987-1008
- **url:** http://www.econ.uiuc.edu/~econ536/Papers/engle82.pdf
- **abstract:** Introduces ARCH — a stochastic process whose conditional variance depends on past squared innovations. Formalises volatility clustering and is the parametric foundation for modern volatility modelling.
- **key_findings:**
  - Conditional variance can be modelled as autoregressive in past squared residuals.
  - MLE recovers parameters; OLS retains optimality of mean estimates under correct specification.
  - UK inflation variance increased materially in the chaotic 1970s, captured by ARCH.
  - ARCH effects are pervasive in financial returns.
- **relevance_to_gtos:** The H25 session-volatility shadow logger and any future XAU vol-conditioning prompt rely on this framework; ATR is a crude proxy for ARCH conditional sigma.
- **potential_hypothesis:** ARCH(p)-fitted variance for XAU M15 will outperform 14-bar ATR in predicting next-bar realized variance (out-of-sample MSE reduction ≥ 15%).
- **cross_domain_links:** 16 (vol regime trading), 02 (ML estimation issues)
- **gtos_diagnostic:** Fit ARCH(5) to XAU M15 returns; compare next-bar absolute-return prediction MSE vs ATR-14.

### 2.4 Generalized Autoregressive Conditional Heteroskedasticity (GARCH)

- **id:** 03-004
- **authors:** Tim Bollerslev
- **year:** 1986
- **source:** Journal of Econometrics 31(3): 307-327
- **url:** https://public.econ.duke.edu/~boller/Published_Papers/joe_86.pdf
- **abstract:** Generalises ARCH by adding lagged conditional variance terms, yielding a parsimonious workhorse model (typically GARCH(1,1)) whose unconditional kurtosis exceeds 3 for fat-tailed innovations. Establishes stationarity conditions and likelihood-based inference.
- **key_findings:**
  - GARCH(1,1) often suffices where ARCH(p) needed many lags.
  - Stationarity requires α + β < 1; persistence near the boundary is the empirical norm.
  - Implied unconditional distribution is leptokurtic even with Gaussian innovations.
  - More plausible learning mechanism than pure ARCH.
- **relevance_to_gtos:** GTOS observed GARCH persistence 0.9906 on XAU returns (memory `project_distributional_findings`); this paper is the canonical anchor. The drawdown manager (H29) and heartbeat thresholds should be calibrated on persistence-aware vol projections, not on rolling-window stdev.
- **potential_hypothesis:** GARCH(1,1)-projected 1-week VaR(99%) for XAU will outperform empirical-quantile VaR by ≥10% in unconditional Christoffersen coverage tests.
- **cross_domain_links:** 16, 02
- **gtos_diagnostic:** Fit GARCH(1,1) on XAU D1 over 1y; plot α+β rolling; flag any drop below 0.97 as regime change.

### 2.5 A Long Memory Property of Stock Market Returns and a New Model

- **id:** 03-005
- **authors:** Zhuanxin Ding, Clive W. J. Granger, Robert F. Engle
- **year:** 1993
- **source:** Journal of Empirical Finance 1(1): 83-106
- **url:** https://www.sciepub.com/reference/152633
- **abstract:** Documents that |r_t|^d for d ∈ (0,2) shows much stronger and longer autocorrelation than r_t^2 in S&P 500 daily returns. Introduces the asymmetric power ARCH (APARCH) model that nests several GARCH variants.
- **key_findings:**
  - Maximum autocorrelation occurs at d ≈ 1.0, not d = 2.
  - Hyperbolic decay of |r_t| autocorrelation evidences long memory.
  - APARCH nests GARCH, GJR, and TARCH as special cases.
  - Long memory in absolute returns coexists with no memory in raw returns.
- **relevance_to_gtos:** Justifies using |r_t| (not r_t^2) when GTOS measures vol persistence. Intra-day session-vol logger H25 should track |r| rolling sums, which is what most ATR-style measures effectively do.
- **potential_hypothesis:** XAU |r_t|^1.0 autocorrelation at lag 100 will exceed |r_t|^2.0 autocorrelation at the same lag (one-sided p < 0.01).
- **cross_domain_links:** 04 (long memory), 16
- **gtos_diagnostic:** Compute ACF of |r|^d for d ∈ {0.5,1,1.5,2} on XAU H1, 12mo; report d* maximising integrated ACF.

### 2.6 Empirical Properties of Asset Returns: Stylized Facts and Statistical Issues

- **id:** 03-006
- **authors:** Rama Cont
- **year:** 2001
- **source:** Quantitative Finance 1(2): 223-236
- **url:** http://rama.cont.perso.math.cnrs.fr/pdf/empirical.pdf
- **abstract:** Synthesises 11 stylized facts for asset-return distributions: heavy tails, gain/loss asymmetry, aggregational normality, intermittency, volatility clustering, conditional heavy tails, slow decay of |r| autocorr, leverage, volume/volatility correlation, asymmetry in time scales, fine structure. Each fact is presented as a constraint a model must satisfy.
- **key_findings:**
  - Returns are unconditionally heavy-tailed; tail index typically 2-5.
  - Aggregational Gaussianity: distributions become more Gaussian at lower frequencies.
  - Volatility clustering is universal and persistent.
  - Returns are uncorrelated but not independent (long memory in |r|).
  - Leverage effect documented across equity classes.
- **relevance_to_gtos:** This is the master rubric against which any GTOS distributional assumption must be checked. The K54 ML classifier features should be screened for stylized-fact alignment before being used as model inputs.
- **potential_hypothesis:** GTOS's per-instrument distribution audits will recover ≥9 of Cont's 11 stylized facts on XAU/USDJPY/GBPJPY M15 returns.
- **cross_domain_links:** 02, 04
- **gtos_diagnostic:** Run all 11 Cont diagnostics on each of the 7 GTOS instruments; produce a stylized-fact matrix.

### 2.7 The Distribution of Realized Exchange Rate Volatility

- **id:** 03-007
- **authors:** Torben G. Andersen, Tim Bollerslev, Francis X. Diebold, Paul Labys
- **year:** 2001
- **source:** Journal of the American Statistical Association 96(453): 42-55
- **url:** https://www.sas.upenn.edu/~fdiebold/papers/paper31/final2.pdf
- **abstract:** Constructs realized volatility from 5-min DEM/JPY-vs-USD returns over a decade. Documents that returns standardised by realized volatility are approximately Gaussian, that log RV is approximately Gaussian, and that RV has long-memory dynamics.
- **key_findings:**
  - r/sqrt(RV) is nearly N(0,1).
  - log RV is approximately Gaussian (the so-called "Gaussian transformation").
  - RV exhibits long memory; fractionally-integrated dynamics fit well.
  - RV correlates strongly across currency pairs.
- **relevance_to_gtos:** Foundational for any high-frequency-vol measurement on GTOS instruments. The tick-capture daemon makes RV computation possible; this paper says RV is the right summary statistic.
- **potential_hypothesis:** XAU 1m-tick-derived daily RV will satisfy Gaussian log-RV with KS p > 0.10 and exhibit ARFIMA-best-fit d ∈ [0.4, 0.5].
- **cross_domain_links:** 16, 04
- **gtos_diagnostic:** From tick daemon, compute daily RV for XAU = sum of 5-min squared returns; QQ-plot log RV against N.

### 2.8 Modeling and Forecasting Realized Volatility

- **id:** 03-008
- **authors:** Torben G. Andersen, Tim Bollerslev, Francis X. Diebold, Paul Labys
- **year:** 2003
- **source:** Econometrica 71(2): 579-625
- **url:** https://onlinelibrary.wiley.com/doi/abs/10.1111/1468-0262.00418
- **abstract:** Develops a framework for measuring, modeling, and forecasting integrated variance using high-frequency data. ARFIMA models on log RV deliver substantial forecast gains over GARCH at daily horizons.
- **key_findings:**
  - High-frequency-derived RV is a consistent estimator of integrated variance.
  - ARFIMA(1,d,1) captures long memory in RV with d ≈ 0.4.
  - Multivariate VAR-RCOV approach generalises to portfolio variance.
  - Daily volatility forecasts improve materially when using HF data.
- **relevance_to_gtos:** Justifies using the tick-capture daemon outputs (microstructure features) plus aggregated RV for daily-vol forecasts feeding the heartbeat / drawdown manager.
- **potential_hypothesis:** ARFIMA on log-RV will improve XAU-daily-vol forecast MSE by ≥20% over GARCH(1,1) at h=1 day.
- **cross_domain_links:** 16, 04
- **gtos_diagnostic:** Time-series cross-validation: ARFIMA vs GARCH on XAU D1 RV; report MSE ratio.

### 2.9 Modelling Extremal Events for Insurance and Finance

- **id:** 03-009
- **authors:** Paul Embrechts, Claudia Klueppelberg, Thomas Mikosch
- **year:** 1997
- **source:** Springer (textbook), Applications of Mathematics 33
- **url:** https://link.springer.com/book/10.1007/978-3-642-33483-2
- **abstract:** Definitive textbook on EVT for insurance and finance — block maxima (Fisher-Tippett, GEV), POT (Pickands-Balkema-de Haan, GPD), Hill estimator, max-stable processes, and their applications to VaR/ES.
- **key_findings:**
  - Block maxima asymptotically follow GEV with shape ξ.
  - Excesses over high threshold u follow GPD with shape ξ.
  - Hill estimator is consistent for ξ > 0 with bias-variance trade-off in k.
  - VaR and ES at very high confidence are tail-shape-dominated.
- **relevance_to_gtos:** Bedrock methodology for `project_distributional_findings` (xi=0.35) and any drawdown / heartbeat threshold work. The 4% portfolio DD hard rule is implicitly an EVT problem when persistence is high.
- **potential_hypothesis:** Daily XAU returns will have GPD shape parameter ξ ∈ [0.20, 0.45] for thresholds at the 95th and 99th absolute-return percentiles.
- **cross_domain_links:** 21 (sizing), 02 (estimation methodology)
- **gtos_diagnostic:** POT/GPD on XAU D1 absolute returns over 1y; report ξ at u=q90 and u=q95; assess threshold stability via Hill plot.

### 2.10 A Multifractal Model of Asset Returns (MMAR)

- **id:** 03-010
- **authors:** Benoit Mandelbrot, Adlai Fisher, Laurent Calvet
- **year:** 1997
- **source:** Cowles Foundation Discussion Paper #1164
- **url:** https://users.math.yale.edu/~bbm3/web_pdfs/Cowles1164.pdf
- **abstract:** Constructs a return process driven by FBM time-changed by a multifractal cascade clock. Returns moments E[|r|^q] scale as power laws of the time interval with non-linear exponent τ(q), generalising self-similarity to multifractality.
- **key_findings:**
  - Moment scaling τ(q) is non-linear in q (vs τ(q) = q/2 for Brownian).
  - Long memory in |r| arises endogenously without unbounded variance.
  - DEM/USD and equity series confirm multifractal moment scaling.
  - Provides alternative to ARCH for stylized facts.
- **relevance_to_gtos:** Provides theoretical justification for the OB-zone edge degrading at different rates across timeframes (multifractality predicts cross-timescale heterogeneity in volatility). Phase-1 finding F11 (decay velocity per timeframe) is consistent with multifractal time deformation.
- **potential_hypothesis:** XAU absolute-return moments E[|r|^q] for q ∈ {0.5, 1, 2, 3, 4} on M15-to-D1 aggregation will exhibit non-linear τ(q), rejecting monofractality at p < 0.01.
- **cross_domain_links:** 04 (decomposition application)
- **gtos_diagnostic:** Compute log E[|r|^q] vs log Δt for q ∈ {0.5, 1, ..., 5}; fit τ(q); test linearity.

### 2.11 On the Relation Between Expected Value and Volatility (GJR-GARCH)

- **id:** 03-011
- **authors:** Lawrence Glosten, Ravi Jagannathan, David Runkle
- **year:** 1993
- **source:** Journal of Finance 48(5): 1779-1801
- **url:** https://faculty.washington.edu/ezivot/econ589/GJRJOF1993.pdf
- **abstract:** Generalises GARCH-M to allow asymmetric impact of positive vs negative shocks (γ × I[ε<0] × ε² term). Documents leverage effect in monthly US equity returns and finds negative excess-return / variance relation under modifications.
- **key_findings:**
  - Negative shocks raise next-period variance more than positive shocks of equal magnitude.
  - Conditional volatility is less persistent than originally thought once asymmetry is added.
  - Monthly US equity excess returns show negative variance correlation under modified GARCH-M.
  - GJR is one of the three workhorse asymmetric models.
- **relevance_to_gtos:** Critical for proper specification of the H25 session-vol logger and any forward XAU vol-feature for K54. GTOS instruments differ in leverage strength (gold often inverse-leverage, indices strong leverage); per-symbol GJR fits would inform per-symbol risk param tightening.
- **potential_hypothesis:** US30 (index) will show positive γ in GJR(1,1) at p < 0.05; XAU may show γ ≤ 0 (no equity-style leverage), as suggested by recent literature.
- **cross_domain_links:** 16, 12
- **gtos_diagnostic:** Fit GJR(1,1) to D1 returns of each instrument; compare γ across symbols; bootstrap 95% CI.

### 2.12 Conditional Heteroskedasticity in Asset Returns: A New Approach (EGARCH)

- **id:** 03-012
- **authors:** Daniel B. Nelson
- **year:** 1991
- **source:** Econometrica 59(2): 347-370
- **url:** https://www.finance.martinsewell.com/stylized-facts/distribution/Nelson1991.pdf
- **abstract:** Introduces EGARCH, modelling log conditional variance to handle asymmetric news impact and remove non-negativity constraints on parameters. The asymmetry term g(z) = θz + γ(|z| - E|z|) captures sign-dependent volatility response.
- **key_findings:**
  - log h_t formulation guarantees positive variance without parameter restrictions.
  - Asymmetric leverage cleanly identified by θ < 0.
  - Allows GED-distributed innovations capturing fat tails.
  - Often outperforms standard GARCH on equity data.
- **relevance_to_gtos:** Alternative to GJR for asymmetric vol modelling; relevant for daily vol feature engineering (K54 candidate).
- **potential_hypothesis:** EGARCH(1,1) will recover θ < 0 (leverage) for US30 and θ ≈ 0 for XAU on 5-yr daily data, distinguishing equity-like from commodity-like vol response.
- **cross_domain_links:** 16
- **gtos_diagnostic:** EGARCH(1,1) per instrument; rank by |θ| asymmetry and pin per-symbol heartbeat sensitivity to asymmetry.

### 2.13 Power and Bipower Variation with Stochastic Volatility and Jumps

- **id:** 03-013
- **authors:** Ole Barndorff-Nielsen, Neil Shephard
- **year:** 2004
- **source:** Journal of Financial Econometrics 2(1): 1-37
- **url:** https://public.econ.duke.edu/~get/browse/courses/201/spr16/COURSE-MATERIALS/Z_Papers/BNSJFEC2004.pdf
- **abstract:** Introduces bipower variation BV = sum |r_i||r_{i-1}|, a jump-robust estimator of integrated variance. The difference RV - BV consistently estimates the squared-jump component of quadratic variation.
- **key_findings:**
  - BV converges to integrated variance even when jumps are present.
  - RV - BV converges to sum of squared jumps.
  - Allows non-parametric jump tests at intra-day frequency.
  - Generalises to multipower variation for higher robustness.
- **relevance_to_gtos:** GTOS tick daemon enables BV and jump detection. Microstructure-validated jump events around news could feed regime classifier and inform FN-equity-correlation gate.
- **potential_hypothesis:** Removing detected-jump 5-min intervals from XAU returns will reduce kurtosis by ≥30% but leave |r| ACF largely unchanged (showing continuous-vol clustering is the dominant memory source).
- **cross_domain_links:** 06 (microstructure)
- **gtos_diagnostic:** Compute RV and BV daily for XAU 5-min; flag days where (RV - BV)/RV > 0.30 as jump days.

### 2.14 Designing Realized Kernels to Measure Variation in the Presence of Noise

- **id:** 03-014
- **authors:** Ole Barndorff-Nielsen, Peter R. Hansen, Asger Lunde, Neil Shephard
- **year:** 2008
- **source:** Econometrica 76(6): 1481-1536
- **url:** https://onlinelibrary.wiley.com/doi/abs/10.3982/ECTA6495
- **abstract:** Develops realized kernels, kernel-weighted realized variance estimators consistent under market-microstructure noise. Symmetric flat-top kernels deliver mixed-Gaussian asymptotics and avoid bandwidth-cherrypicking.
- **key_findings:**
  - Naive RV at very high frequency is biased by microstructure noise.
  - Kernel weighting reduces bias while retaining consistency.
  - Optimal bandwidth depends on noise-to-signal ratio.
  - Multivariate version handles non-synchronous trading.
- **relevance_to_gtos:** Tick-daemon RV computation should use realized kernels (or 5-min subsampled RV as a robust shortcut), not naive 1-tick RV.
- **potential_hypothesis:** Realized-kernel RV on XAU will deliver more stable daily RV than naive 1-min RV (variance-of-variance reduction ≥ 25%).
- **cross_domain_links:** 06
- **gtos_diagnostic:** Compute kernel RV vs naive RV on XAU tick data; compare day-to-day stability.

### 2.15 Estimation of Tail-Related Risk Measures for Heteroscedastic Financial Time Series: An Extreme Value Approach

- **id:** 03-015
- **authors:** Alexander J. McNeil, Rüdiger Frey
- **year:** 2000
- **source:** Journal of Empirical Finance 7(3-4): 271-300
- **url:** https://faculty.washington.edu/ezivot/econ589/EVT_Mcneil_Frey_2000.pdf
- **abstract:** Combines GARCH (for serial-dependence and conditional vol) with EVT (POT/GPD for innovation tails) in a two-step procedure for VaR and ES. Out-performs both pure GARCH and unconditional EVT in backtests.
- **key_findings:**
  - Two-step "filter then EVT-tail" gives best 1-day VaR/ES.
  - ES is theoretically and empirically more reliable than VaR.
  - Naive GARCH-Gaussian underestimates tails; pure EVT misses dynamics.
  - Christoffersen / Kupiec coverage tests favour the hybrid.
- **relevance_to_gtos:** Direct prescription for GTOS heartbeat / DD limit calibration: filter XAU returns by GARCH, fit GPD to standardised residuals, project ES at the heartbeat horizon.
- **potential_hypothesis:** GARCH-EVT 1-day 99%-ES on XAU will outperform 99%-historical-VaR by ≥30% in expected-shortfall coverage.
- **cross_domain_links:** 21
- **gtos_diagnostic:** Implement GARCH-EVT pipeline on XAU D1, 2y; compare ES backtests against historical-quantile baseline.

### 2.16 Expected Shortfall: A Natural Coherent Alternative to VaR

- **id:** 03-016
- **authors:** Carlo Acerbi, Dirk Tasche
- **year:** 2002
- **source:** Economic Notes 31(2): 379-388
- **url:** https://www.financerisks.com/filedati/WP/EVT/CHOERENT%20EXPECTED%20SHORTFALL.pdf
- **abstract:** Demonstrates that ES (average of losses beyond VaR) satisfies the coherent risk-measure axioms (monotonicity, subadditivity, positive homogeneity, translation invariance), unlike VaR. Provides a definition that remains coherent even under discontinuous loss distributions.
- **key_findings:**
  - VaR fails subadditivity; portfolio diversification can increase VaR.
  - ES is coherent for any loss distribution.
  - Definition matters at jumps; the "average of worst (1-α)% losses" formulation is robust.
  - Foundation for Basel's shift toward ES.
- **relevance_to_gtos:** Hard rules in CLAUDE.md (e.g., "single trade > 1.5R") are coherent; a portfolio rule built on VaR could fail. Move heartbeat budget to ES at 99% over 1-day horizon.
- **potential_hypothesis:** Portfolio-level 99%-ES under multivariate-Student-t fit on XAU/US30/USDJPY/GBPJPY will materially exceed univariate-summed ES, evidencing tail-comonotonicity (FE_diversification < 0.10).
- **cross_domain_links:** 21
- **gtos_diagnostic:** Compute portfolio ES via Monte Carlo from fitted multivariate-t at 99% / 1d; compare to sum of univariate ES.

### 2.17 CAViaR: Conditional Autoregressive VaR by Regression Quantiles

- **id:** 03-017
- **authors:** Robert F. Engle, Simone Manganelli
- **year:** 2004
- **source:** Journal of Business and Economic Statistics 22(4): 367-381
- **url:** http://www.simonemanganelli.org/Simone/Research_files/caviarPublished.pdf
- **abstract:** Models the conditional quantile (VaR) directly using quantile regression rather than the entire distribution. Avoids parametric distributional assumptions and provides dynamic-quantile testing for misspecification.
- **key_findings:**
  - Direct quantile dynamics: VaR_t = β0 + β1 VaR_{t-1} + β2 f(r_{t-1}).
  - Symmetric absolute value, asymmetric slope, indirect GARCH variants compared.
  - Dynamic quantile (DQ) test for adequacy.
  - Often competitive with GARCH-EVT under nonstationarity.
- **relevance_to_gtos:** Useful for daily portfolio-loss-quantile dashboarding without fitting full conditional distribution. Pairs with the heartbeat-flatten threshold.
- **potential_hypothesis:** Asymmetric-slope CAViaR for XAU 5%-VaR will pass the DQ test (p > 0.10) over a 1y rolling test, while a Gaussian-GARCH baseline will fail.
- **cross_domain_links:** 21
- **gtos_diagnostic:** Implement asymmetric-slope CAViaR on XAU D1; run DQ test on 1y holdout.

### 2.18 Power Laws in Economics and Finance

- **id:** 03-018
- **authors:** Xavier Gabaix
- **year:** 2009
- **source:** Annual Review of Economics 1: 255-294
- **url:** https://pages.stern.nyu.edu/~xgabaix/papers/pl-ar.pdf
- **abstract:** Survey of empirical power laws in economics and finance — Pareto wealth, Zipf city size, the "cubic law" of stock returns and "half-cubic law" of trading volume. Lays out theoretical generators (random multiplicative growth, large-trader/Pareto-investor mechanisms).
- **key_findings:**
  - Cubic law: P(|r| > x) ~ x^{-3} across markets, sizes, periods.
  - Volume distribution exponent ~3/2 (half-cubic).
  - Number-of-trades exponent ~3.
  - Random multiplicative growth + reflection generates Pareto.
- **relevance_to_gtos:** Explains why XAU 1-day extreme returns concentrate near a tail-index of ~3 in GTOS data (`project_distributional_findings`). Setting heartbeat thresholds requires extrapolating tail with α≈3 not Gaussian.
- **potential_hypothesis:** Hill estimator on XAU daily |returns|, k = sqrt(n), will yield α-hat ∈ [2.7, 3.5].
- **cross_domain_links:** 13, 21
- **gtos_diagnostic:** Hill plot for each instrument; report stable α region.

### 2.19 A Theory of Power-Law Distributions in Financial Market Fluctuations

- **id:** 03-019
- **authors:** Xavier Gabaix, Parameswaran Gopikrishnan, Vasiliki Plerou, H. Eugene Stanley
- **year:** 2003
- **source:** Nature 423: 267-270
- **url:** https://www.nature.com/articles/nature01624
- **abstract:** Proposes that power-law tails of returns and volumes arise from optimal trading by large institutional investors who themselves have a Pareto size distribution. Connects the cubic law of returns to the half-cubic law of volume via market-impact theory.
- **key_findings:**
  - Investor size has Pareto tail (consistent with mutual fund data).
  - Optimal-execution market impact ~ V^(1/2) gives volume α ≈ 3/2.
  - Implies return α ≈ 3 from volume α and impact concavity.
  - 1929 and 1987 crashes are not outliers to the power law.
- **relevance_to_gtos:** Mechanism-level explanation for why GTOS-instrument extreme moves cluster around α ≈ 3. Implies that extreme XAU moves coincide with large-fund flows; could be detected via volume features.
- **potential_hypothesis:** Days where XAU realized volume exceeds 95th percentile will show 5x higher probability of |r| > q99 than baseline.
- **cross_domain_links:** 06, 08
- **gtos_diagnostic:** Cross-tabulate XAU daily-volume quantile vs |r| quantile.

### 2.20 Stochastic Process with Ultra-Slow Convergence to a Gaussian: The Truncated Lévy Flight

- **id:** 03-020
- **authors:** Rosario N. Mantegna, H. Eugene Stanley
- **year:** 1994
- **source:** Physical Review Letters 73(22): 2946-2949
- **url:** https://www.researchgate.net/publication/13233663
- **abstract:** Introduces the truncated Lévy flight, a stable distribution with abrupt cut-offs in the extreme tails. Recovers finite variance while preserving Lévy-like behaviour over many time scales; convergence to Gaussian under aggregation is ultra-slow (10^4 steps).
- **key_findings:**
  - S&P 500 fits truncated Lévy with α ≈ 1.4 from minutes to ~1 day.
  - Convergence to Gaussian only emerges around monthly aggregation.
  - Truncation reconciles infinite-variance Lévy with finite empirical moments.
  - Fits central body of return distribution very well.
- **relevance_to_gtos:** Explains why XAU intraday and daily distributions differ qualitatively — the system operates in the truncated-Lévy regime, not Gaussian, for all GTOS-relevant horizons.
- **potential_hypothesis:** XAU returns fit truncated Lévy with α ∈ [1.3, 1.7] across M1, M15, H1; α drifts toward 2 only at D1 or weekly.
- **cross_domain_links:** 04
- **gtos_diagnostic:** Fit truncated Lévy on XAU at multiple aggregations; track α(Δt).

---

## 3. Recent advances 2020-2025

### 3.1 Revisiting Cont's Stylized Facts for Modern Stock Markets

- **id:** 03-021
- **authors:** Ethan Ratliff-Crain, Colin Van Oort, James Bagrow, Brian Tivnan, Matthew Koehler (MITRE / Univ. of Vermont)
- **year:** 2023 (published Quantitative Finance 2025, vol. 25, no. 9)
- **source:** arXiv:2311.07738; Quantitative Finance 25(9)
- **url:** https://arxiv.org/html/2311.07738v2
- **abstract:** Re-tests all 11 of Cont's 2001 stylized facts on intraday returns of Dow-30 stocks (Oct 2018 - Mar 2019) using SEC consolidated tape data. Confirms 8/11 facts; 3 are weakened or absent in modern microstructure.
- **key_findings:**
  - Heavy tails, volatility clustering, leverage, |r|-autocorrelation persistence — all confirmed.
  - Aggregational Gaussianity weakened: intraday HFT smoothing yields more Gaussian-like minute-scale returns.
  - Gain-loss asymmetry weakened.
  - Some facts are now resolution-dependent.
- **relevance_to_gtos:** Modern microstructure (HFT, fragmentation) means historical-stylized-facts may not transfer; GTOS should re-verify on its own M15 data per instrument before tuning. Resolution-dependent stylized facts directly motivate tick-daemon coverage.
- **potential_hypothesis:** GTOS M15 XAU returns will confirm 8-9 of Cont's facts but will weaken on aggregational-Gaussianity at sub-5-minute scales.
- **cross_domain_links:** 02
- **gtos_diagnostic:** Replicate the MITRE 11-fact battery on each of the 7 GTOS instruments.

### 3.2 Pricing under Rough Volatility

- **id:** 03-022
- **authors:** Christian Bayer, Peter Friz, Jim Gatheral
- **year:** 2016
- **source:** Quantitative Finance 16(6): 887-904
- **url:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2554754
- **abstract:** Argues that log-volatility is well-described by a fractional Brownian motion with Hurst exponent H ≈ 0.1, implying volatility paths are rougher than Brownian. Develops the rBergomi model and shows it fits the SPX implied vol surface materially better than Markovian SV models.
- **key_findings:**
  - H ≈ 0.1 across asset classes implies rough volatility.
  - rBergomi pricing fits SPX vols with fewer parameters.
  - Roughness is a stylized fact, not a calibration trick.
  - Term-structure of vol-vol implies non-Markovian dynamics.
- **relevance_to_gtos:** Volatility-of-volatility is rougher than Brownian; this matters for projecting heartbeat thresholds at multi-hour horizons. ATR-based heuristics implicitly assume Brownian-like vol — rough-volatility implies more peaked short-horizon spikes.
- **potential_hypothesis:** Hurst exponent of log RV for XAU on 1-min sampled data, 30-day rolling window, will satisfy H ∈ [0.05, 0.20].
- **cross_domain_links:** 04, 16
- **gtos_diagnostic:** Compute log-RV from tick daemon; estimate H via DFA / wavelet-leader methods.

### 3.3 The Microstructural Foundations of Leverage Effect and Rough Volatility

- **id:** 03-023
- **authors:** Omar El Euch, Masaaki Fukasawa, Mathieu Rosenbaum
- **year:** 2018
- **source:** Finance and Stochastics 22(2): 241-280
- **url:** https://link.springer.com/article/10.1007/s00780-018-0360-z
- **abstract:** Shows that Hawkes-process microscopic order-flow models with three stylized facts (high endogeneity, no-arbitrage, buy/sell asymmetry) converge in scaling limit to Heston-with-leverage stochastic volatility, and adding metaorder-style impact yields rough Heston with H < 0.5.
- **key_findings:**
  - Rough-vol is endogenous to LOB self-excitation.
  - Leverage effect emerges from buy/sell asymmetry, not from accounting leverage.
  - Hurst H is determined by Hawkes-kernel power-law exponent.
  - Strong micro/macro bridge.
- **relevance_to_gtos:** Provides theoretical link between order-flow microstructure (potential future GTOS feature) and observed return-distribution asymmetry. Suggests detecting regime via Hawkes-process kernel parameters.
- **potential_hypothesis:** XAU tick-arrival process during NY KZ will exhibit Hawkes-kernel power-law decay with exponent in [0.3, 0.5] (consistent with rough vol).
- **cross_domain_links:** 06
- **gtos_diagnostic:** Fit Hawkes process to XAU tick arrivals during KZ; estimate kernel exponent.

### 3.4 Tail Index Estimation: Quantile-Driven Threshold Selection

- **id:** 03-024
- **authors:** Jon Danielsson, Lerby M. Ergun, Laurens de Haan, Casper G. de Vries
- **year:** 2019
- **source:** Bank of Canada Staff Working Paper 2019-28
- **url:** https://www.bankofcanada.ca/wp-content/uploads/2019/08/swp2019-28.pdf
- **abstract:** Proposes a quantile-driven threshold-selection procedure for the Hill estimator that minimises max-distance between fitted-Pareto tail and empirical quantile. Out-performs MSE-minimisation and bootstrap methods in finite samples.
- **key_findings:**
  - KS-distance-driven choice of k stable across heavy-tail regimes.
  - "Eye-Ball" automated method robust for α ≤ 4.
  - MSE-minimisation methods fail in finite samples.
  - Demonstrated on CRSP equity data.
- **relevance_to_gtos:** Best-practice choice for k in Hill estimator on GTOS-instrument tails. Replaces ad-hoc k = sqrt(n) heuristic.
- **potential_hypothesis:** Quantile-driven k for XAU daily |r| will produce α-hat with bootstrap CI half-width < 0.20, while sqrt(n) k will produce wider CI.
- **cross_domain_links:** 02
- **gtos_diagnostic:** Compare Hill α-hat under quantile-driven k vs sqrt(n) k; compare CI widths via bootstrap.

### 3.5 Stylized Facts of High-Frequency Bitcoin Time Series

- **id:** 03-025
- **authors:** various (arXiv 2402.11930)
- **year:** 2024
- **source:** arXiv:2402.11930
- **url:** https://arxiv.org/html/2402.11930v2
- **abstract:** Tests the canonical stylized facts on Bitcoin minute-scale returns 2018-2023. Finds heavy tails (best fit q-Gaussian), volatility clustering, slow Gaussianisation under aggregation, and weak gain-loss asymmetry vs equity.
- **key_findings:**
  - q-Gaussian (Tsallis) often outperforms power-law and stable fits for body+tails.
  - 24/7 trading reduces overnight-jump signature seen in equities.
  - Volatility clustering present at 1-min to daily scales.
  - Long-memory in |r| similar to FX.
- **relevance_to_gtos:** Useful comparator; XAU/FX have weekend gaps comparable to crypto's session-less property only on Sunday open. q-Gaussian may fit XAU intraday better than stable.
- **potential_hypothesis:** XAU 1-min returns fit q-Gaussian with q ∈ [1.4, 1.7] better than stable-Lévy by AIC.
- **cross_domain_links:** 04
- **gtos_diagnostic:** Fit q-Gaussian, stable, Student-t to XAU M1 returns; compare AIC.

### 3.6 Volatility Modeling and Tail Risk Estimation of Financial Assets: Evidence from Gold, Oil, Bitcoin, and Stocks for Selected Markets

- **id:** 03-026
- **authors:** various
- **year:** 2025
- **source:** Risks 13(7): 138 (MDPI)
- **url:** https://www.mdpi.com/2227-9091/13/7/138
- **abstract:** Compares GARCH, EGARCH, GJR, FIGARCH, and IGARCH on gold, oil, BTC, and equities for VaR and ES estimation. Finds asymmetric models (EGARCH, GJR) materially outperform symmetric GARCH on all assets and that fat-tailed innovations (skewed-t, GED) dominate Gaussian.
- **key_findings:**
  - sGARCH best for gold by AIC; EGARCH best for stocks.
  - Skewed-t innovations consistently outperform Gaussian.
  - VaR coverage at 99% is reliable; 99.5% remains underestimated.
  - Bitcoin requires highest GARCH(1,1) persistence.
- **relevance_to_gtos:** Direct empirical justification for asymmetric-GARCH + fat-tail innovations on every GTOS instrument. The "sGARCH best for gold" finding is consistent with GTOS-observed XAU GARCH persistence.
- **potential_hypothesis:** Skewed-t-EGARCH will dominate Gaussian-sGARCH for daily-VaR coverage on each of the 7 GTOS instruments by Christoffersen-test rejection rate.
- **cross_domain_links:** 21, 16
- **gtos_diagnostic:** Bake-off: 6 GARCH variants × 2 innovation distributions on each instrument.

### 3.7 Tail Risk and Asset Prices

- **id:** 03-027
- **authors:** Bryan Kelly, Hao Jiang
- **year:** 2014
- **source:** Review of Financial Studies 27(10): 2841-2871
- **url:** https://www.nber.org/system/files/working_papers/w19375/w19375.pdf
- **abstract:** Constructs a cross-sectional tail-risk measure from the Hill estimator on monthly stock-level crashes. Tail risk has strong predictive power for aggregate market returns (1-σ rise → +4.5%/yr) and explains a 5.4% three-factor alpha cross-sectionally.
- **key_findings:**
  - Time-varying tail-risk measure recoverable from cross-section, not just time series.
  - Strong tail risk → high subsequent returns (compensation for tail-risk).
  - Cross-sectional pricing: high tail-loading stocks earn premium.
  - Macro-relevant: tail risk forecasts industrial production.
- **relevance_to_gtos:** Suggests building a cross-instrument tail-risk index from XAU + 6 instruments via Hill on aggregated extreme returns; could feed K54 as a regime feature.
- **potential_hypothesis:** Cross-instrument Hill α-hat (rolling 30-day, pooled across all 7 GTOS instruments) is negatively correlated with XAU forward 30-day returns at the 5% level.
- **cross_domain_links:** 13, 17
- **gtos_diagnostic:** Compute pooled Hill estimate weekly across 7 instruments; correlate with forward returns.

### 3.8 Long Memory Volatility of Gold Price Returns

- **id:** 03-028
- **authors:** various (Bonato et al)
- **year:** 2015
- **source:** Physica A 438: 355-364
- **url:** https://ideas.repec.org/a/eee/phsmap/v438y2015icp355-364.html
- **abstract:** Tests gold-price volatility under GARCH, IGARCH, and FIGARCH across distinct economic-cycle subperiods. Finds robust long-memory in gold conditional variance with d ≈ 0.4 and that FIGARCH dominates GARCH out-of-sample.
- **key_findings:**
  - Gold vol has robust long memory (d ≈ 0.4).
  - FIGARCH wins by AIC and forecast MSE.
  - Subperiod analysis confirms robustness across cycles.
  - GARCH-IGARCH hybrid intermediate.
- **relevance_to_gtos:** XAU-specific; supports GTOS-observed GARCH persistence near 1.0 (which approximates fractional integration). Heartbeat / DD models should use FIGARCH for XAU not vanilla GARCH.
- **potential_hypothesis:** FIGARCH(1,d,1) on XAU D1 will recover d ∈ [0.35, 0.45] and AIC-dominate GARCH(1,1).
- **cross_domain_links:** 10, 16
- **gtos_diagnostic:** Fit FIGARCH on XAU D1; report d-hat and AIC vs GARCH.

### 3.9 Modelling Asymmetric Market Volatility with Univariate GARCH Models: Evidence from Nasdaq-100

- **id:** 03-029
- **authors:** various
- **year:** 2020
- **source:** Journal of Economic Asymmetries (Elsevier)
- **url:** https://www.sciencedirect.com/science/article/abs/pii/S1703494920300141
- **abstract:** Comprehensive comparison of GARCH, EGARCH, GJR, TGARCH on NASDAQ-100. Documents pronounced leverage effect; asymmetric models AIC-dominate; tail innovations are fat (skewed-t).
- **key_findings:**
  - NASDAQ-100 leverage parameter γ > 0 highly significant.
  - EGARCH outperforms GJR for NDX during crisis subperiods.
  - Skewed-t innovations dominate.
  - Daily 1%-VaR underestimated by Gaussian-GARCH.
- **relevance_to_gtos:** Direct relevance to NAS100 instrument (3-day observe). Justifies tighter heartbeat threshold for NAS100 than for XAU, and motivates per-symbol asymmetric-GARCH features for K54.
- **potential_hypothesis:** EGARCH on NAS100 daily returns 2024-2026 will recover θ < 0 at p < 0.01.
- **cross_domain_links:** 12, 16
- **gtos_diagnostic:** EGARCH on NAS100 daily, 5y; report θ, robustness across subsamples.

### 3.10 Multiscaling and Rough Volatility: An Empirical Investigation

- **id:** 03-030
- **authors:** various
- **year:** 2022
- **source:** International Review of Financial Analysis (Elsevier)
- **url:** https://www.sciencedirect.com/science/article/pii/S1057521922002757
- **abstract:** Tests whether rough-volatility's H ≈ 0.1 is consistent with multiscaling moment exponents on equity, FX, commodity. Finds H estimates depend on moment q used and on filtering procedure; "rough" H robust but precise estimates differ.
- **key_findings:**
  - H estimates vary by method (DFA, wavelet, MLE, Whittle).
  - Multiscaling tests refine H beyond pointwise estimation.
  - Commodity (gold) Hurst lower than equity.
  - Filtering microstructure-noise critical.
- **relevance_to_gtos:** Cautions GTOS against single-method H estimation; require ensemble. Supports per-instrument H heterogeneity that K54 could exploit.
- **potential_hypothesis:** XAU H estimated via DFA, wavelet leaders, and Whittle MLE will agree to within ±0.05 on D1 RV from 2 years of tick data.
- **cross_domain_links:** 04
- **gtos_diagnostic:** Multi-method H estimation pipeline on XAU; report ensemble.

### 3.11 Forecasting Tail Risk Measures for Financial Time Series: An Extreme Value Approach with Covariates

- **id:** 03-031
- **authors:** various
- **year:** 2023
- **source:** Journal of Empirical Finance (Elsevier)
- **url:** https://www.sciencedirect.com/science/article/abs/pii/S0927539823000026
- **abstract:** Extends McNeil-Frey EVT with covariate-dependent GPD parameters (e.g., VIX, lagged RV). Improves dynamic VaR/ES forecasts, especially during stress.
- **key_findings:**
  - Covariate-GPD reduces ES error during crises by 20-40%.
  - VIX and lagged-RV are strongest covariates.
  - Recursive estimation feasible at daily frequency.
  - Backtesting passes Christoffersen and DQ tests.
- **relevance_to_gtos:** Direct upgrade path for GTOS heartbeat: gate threshold by current XAU GVZ (CBOE Gold Vol Index) plus lagged tick-RV.
- **potential_hypothesis:** Covariate-GPD with GVZ as scale-covariate will improve XAU 99.5%-ES coverage by ≥15% over static GPD.
- **cross_domain_links:** 21
- **gtos_diagnostic:** Build covariate-GPD pipeline on XAU; backtest vs static GPD on 1y holdout.

### 3.12 Persistence in High Frequency Financial Data: The Case of EuroStoxx 50 Futures Prices

- **id:** 03-032
- **authors:** various (Caporale, Gil-Alana et al)
- **year:** 2024
- **source:** Cogent Economics & Finance
- **url:** https://www.tandfonline.com/doi/full/10.1080/23322039.2024.2302639
- **abstract:** Documents long memory in volatility of EuroStoxx 50 5-min returns; d ≈ 0.4-0.5 robust. Confirms classic stylized facts persist in modern equity-index futures.
- **key_findings:**
  - 5-min |r| has persistent ACF, fractionally integrated d ≈ 0.45.
  - Returns themselves d ≈ 0 (no memory).
  - Gain-loss asymmetry weakened in modern HF data.
  - Microstructure noise shifts d-hat toward 0.5 if uncorrected.
- **relevance_to_gtos:** Index futures (US30, NAS100) likely behave similarly; supports |r|-memory feature in K54 for index instruments.
- **potential_hypothesis:** US30 5-min |r| over 1y will have ARFIMA-d ∈ [0.40, 0.50] surviving microstructure correction.
- **cross_domain_links:** 04, 12
- **gtos_diagnostic:** ARFIMA on US30 5-min |r|; correct for tick noise; report d-hat with CI.

### 3.13 Volatility Models for Stylized Facts of High-Frequency Financial Data

- **id:** 03-033
- **authors:** Yong Sik Kim et al
- **year:** 2023
- **source:** Journal of Time Series Analysis
- **url:** https://onlinelibrary.wiley.com/doi/10.1111/jtsa.12666
- **abstract:** Presents new volatility models specifically tailored to HF stylized facts: intraday seasonality, jump components, microstructure noise, and overnight returns. Out-performs HAR-RV on out-of-sample forecast.
- **key_findings:**
  - Intraday seasonality (U-shape) needs explicit modelling.
  - Combining jump-robust BV with seasonality boosts forecasts.
  - Overnight return treatment matters for FX vs equity.
  - HF-tailored model out-performs HAR-RV by ~10% MSE.
- **relevance_to_gtos:** GTOS can implement intraday seasonality and jump separation in tick-daemon vol features. Direct candidate for K54 input feature engineering.
- **potential_hypothesis:** Adding intraday-seasonality-corrected RV plus BV as features to K54 will lift AUC by ≥0.02 vs raw RV.
- **cross_domain_links:** 04, 06
- **gtos_diagnostic:** Compute seasonality-adjusted intraday RV per instrument; feed to K54 ablation study.

### 3.14 EVT and Tail-Risk Modelling: Evidence from Market Indices and Volatility Series

- **id:** 03-034
- **authors:** various
- **year:** 2013
- **source:** North American Journal of Economics and Finance 26: 174-188
- **url:** https://www.sciencedirect.com/science/article/abs/pii/S1062940813000259
- **abstract:** Applies EVT (POT/GPD) to S&P 500 returns and VIX. Shows that VaR and ES from EVT outperform parametric Gaussian and Student-t at high quantiles. Documents heavy-tail VIX changes.
- **key_findings:**
  - GPD-fitted ES at 99.5% materially exceeds Gaussian/t-implied ES.
  - VIX log-changes exhibit heavier tails than equity returns.
  - Threshold u ≈ 95th percentile is empirically stable.
  - Backtests favour EVT-based ES.
- **relevance_to_gtos:** Supports use of EVT-based heartbeat thresholds. The result that vol-of-vol (VIX changes) has heavier tails than returns is critical — heartbeat metrics built on rolling-stdev differences may themselves be tail-vulnerable.
- **potential_hypothesis:** Daily ATR(14) percent-changes for XAU will have GPD-shape ξ ≥ ξ of XAU returns themselves.
- **cross_domain_links:** 16, 21
- **gtos_diagnostic:** GPD on Δ(ATR-14)/ATR-14 daily for XAU; compare ξ to GPD-ξ on returns.

### 3.15 Generalized Pareto Distribution Modelling of Bitcoin Extreme Returns

- **id:** 03-035
- **authors:** various
- **year:** 2024
- **source:** IntechOpen book chapter
- **url:** https://www.intechopen.com/chapters/1173468
- **abstract:** Fits GPD to Bitcoin returns 2008-2023 across both tails. Documents asymmetric tails (left heavier than right), threshold u ≈ q97-q98 stable, ξ ≈ 0.25.
- **key_findings:**
  - Both tails fit GPD; left tail heavier than right.
  - ξ-hat stable across rolling 1-yr windows.
  - 99.9% VaR/ES under-estimated by Gaussian by 3-4×.
  - Shows EVT scales to volatile new asset classes.
- **relevance_to_gtos:** Methodology directly transferable to XAU/instrument tails. GTOS distribution memory (xi=0.35 for gold) is consistent with Bitcoin range, suggesting heartbeat thresholds for crypto-volatile periods may rhyme.
- **potential_hypothesis:** GPD-ξ on XAU left-tail will exceed ξ on right-tail by 0.05 or more (consistent with safe-haven flight asymmetry).
- **cross_domain_links:** 21
- **gtos_diagnostic:** GPD fits both tails XAU D1; compare ξ_left vs ξ_right with bootstrap CI.

### 3.16 Stylized Facts in Web3 (Token Markets)

- **id:** 03-036
- **authors:** various
- **year:** 2024
- **source:** arXiv:2408.07653
- **url:** https://arxiv.org/html/2408.07653v3
- **abstract:** Empirical study of stylized facts on Web3 token returns: heavy tails, aggregational quasi-Gaussianity, volatility clustering, leverage, time-reversal asymmetry. Confirms most facts despite different microstructure and 24/7 trading.
- **key_findings:**
  - Heavy tails persist for tokens.
  - Volatility clustering present.
  - Leverage effect weaker than equity but present.
  - Time-reversal asymmetry (Cont's "fine structure") detectable.
- **relevance_to_gtos:** Demonstrates the stylized facts are universal; XAU and crypto rhyme more than they differ in distribution shape, lending confidence to using crypto-tested EVT methods on XAU.
- **potential_hypothesis:** XAU and major-crypto-tokens will share Hill α-hat within ±0.5 over 1y.
- **cross_domain_links:** 04
- **gtos_diagnostic:** Cross-pair Hill comparison XAU vs BTC, ETH at q95.

### 3.17 Adaptive Fractal Dynamics: A Time-Varying Hurst Approach to Volatility Modelling in Equity Markets

- **id:** 03-037
- **authors:** various
- **year:** 2025
- **source:** Frontiers in Applied Mathematics and Statistics
- **url:** https://www.frontiersin.org/journals/applied-mathematics-and-statistics/articles/10.3389/fams.2025.1554144/full
- **abstract:** Models the Hurst exponent itself as time-varying; documents shifts in H during crises and shows that fixed-H models systematically misprice tail risk during regime changes. Recovers crisis-period H drops.
- **key_findings:**
  - H is regime-dependent; equity H drops during crises.
  - TV-Hurst materially improves tail forecasting.
  - Filter framework (state-space) recovers H_t.
  - Validated on multiple equity indices.
- **relevance_to_gtos:** Direct candidate feature for K54: rolling H of XAU/instrument, regime-tagged. Connects to F15 finding that GTOS edge decay is regime-conditioned.
- **potential_hypothesis:** Rolling-30d H of XAU log-vol will Granger-cause regime-classifier transitions at p < 0.01.
- **cross_domain_links:** 04, 05
- **gtos_diagnostic:** TV-Hurst rolling estimate on XAU 5-min RV; lag against regime-classifier output.

### 3.18 A Note on the Gumbel Convergence for the Lee-Mykland Jump Tests

- **id:** 03-038
- **authors:** various
- **year:** 2024
- **source:** Finance Research Letters
- **url:** https://www.sciencedirect.com/science/article/pii/S1544612323011868
- **abstract:** Refines critical-value calculation for Lee-Mykland intraday jump tests, correcting finite-sample bias in Gumbel limit. Extends test to higher frequencies than originally validated.
- **key_findings:**
  - Original LM critical values too lenient at very high frequencies.
  - Corrected Gumbel bounds restore size control.
  - Extends LM to 1-second intervals validly.
  - Important for tick-level jump detection.
- **relevance_to_gtos:** Tick daemon allows GTOS to detect intraday jumps at 1-min or finer. This refinement matters for any decision rule conditional on jump events.
- **potential_hypothesis:** Detected intraday jump events on XAU coincide with FOMC / NFP timestamps with hit-rate > 70%.
- **cross_domain_links:** 06, 16
- **gtos_diagnostic:** Run corrected LM on XAU 1-min; cross-tab with macro-event timestamps.

### 3.19 Modelling Intraday Jumps and Cojumps in Oil and Currency Markets: The Role of US Macroeconomic News

- **id:** 03-039
- **authors:** various
- **year:** 2025
- **source:** Review of Quantitative Finance and Accounting
- **url:** https://link.springer.com/article/10.1007/s11156-025-01461-x
- **abstract:** Intraday jump detection on oil, EUR/USD, JPY/USD around US macro news. Cojumps cluster around CPI, NFP, FOMC; cross-asset jump propagation is asymmetric (oil leads FX in some contexts).
- **key_findings:**
  - 70-80% of significant intraday jumps within 30 minutes of scheduled macro news.
  - Cojumps oil-FX strongest around CPI.
  - Asymmetric lead-lag.
  - Supports event-conditioned risk management.
- **relevance_to_gtos:** GTOS already has news-time skip rules; this paper supports also using non-skipped jumps as a feature for the cross-instrument-correlation gate.
- **potential_hypothesis:** Cojumps detected across XAU and US30 within ±5 minutes of FOMC will exceed baseline cojump rate by 10×.
- **cross_domain_links:** 11, 13, 06
- **gtos_diagnostic:** LM on XAU and US30 1-min; build cojump indicator; cross-tab with FOMC times.

### 3.20 Forecasting Volatility in Commodity Markets with Long-Memory Models

- **id:** 03-040
- **authors:** Pierre Giot et al
- **year:** 2022
- **source:** Energy Economics (Elsevier)
- **url:** https://www.sciencedirect.com/science/article/abs/pii/S240585132200006X
- **abstract:** Compares FIGARCH, HAR, FSV on 22 commodities including gold. For gold, daily-frequency components dominate; for energy, weekly. HAR-RV with realized-quarticity correction wins overall.
- **key_findings:**
  - Long memory in commodity vol robust across the panel.
  - Gold: daily HAR component dominates; oil: weekly.
  - Quarticity-corrected HAR best out-of-sample.
  - Implies different feature horizons per commodity.
- **relevance_to_gtos:** Per-instrument vol-feature horizons for K54: gold daily, equity-index weekly, FX likely weekly. Also rationalises tighter heartbeat reaction-time on XAU than on US30.
- **potential_hypothesis:** HAR-RV with daily-only component will out-perform HAR-RV with weekly-only on XAU; reverse ordering on US30.
- **cross_domain_links:** 10
- **gtos_diagnostic:** HAR-RV variants on XAU vs US30; compare 1-day forecast MSE.

---

## 4. Methodological / cross-cutting

### 4.1 Power-Law Distributions in Empirical Data

- **id:** 03-041
- **authors:** Aaron Clauset, Cosma R. Shalizi, Mark E. J. Newman
- **year:** 2009
- **source:** SIAM Review 51(4): 661-703
- **url:** https://aaronclauset.github.io/courses/3352/readings/Clauset_Shalizi_Newman_09_PowerlawDistributionsInEmpiricalData.pdf
- **abstract:** Definitive methodological paper on fitting and testing power-law distributions to empirical data. MLE with KS-statistic-based lower-cut-off selection; goodness-of-fit via parametric bootstrap; likelihood-ratio against log-normal / exponential / stretched exponential alternatives.
- **key_findings:**
  - OLS log-log regression is biased and unreliable for power-law fits.
  - MLE + bootstrap is the right pipeline.
  - Many "power laws" in the literature do not survive proper testing.
  - Provides freely-downloadable code (`plfit`).
- **relevance_to_gtos:** Mandatory reading for GTOS Hill / power-law analysis. Many ad-hoc claims of "fat tail" need to be re-checked using their pipeline. Tests for GTOS-instrument α-hat values should follow Clauset et al.
- **potential_hypothesis:** Some GTOS instruments (likely FX majors EURUSD, GBPUSD) will fail Clauset-LR test favoring power law over log-normal at 5%.
- **cross_domain_links:** 02
- **gtos_diagnostic:** Apply `plfit` to each instrument's daily |r| and intraday |r|; report α-hat, x_min, p-value, LR vs log-normal.

### 4.2 Realized Kernels in Practice: Trades and Quotes

- **id:** 03-042
- **authors:** Ole Barndorff-Nielsen, Peter Hansen, Asger Lunde, Neil Shephard
- **year:** 2009
- **source:** Econometrics Journal 12(s3): C1-C32
- **url:** https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1368-423X.2008.00275.x
- **abstract:** Practical guide to computing realized kernels on trade and quote data. Documents implementation choices (jittering, end-point handling, trade vs midquote) on Dow stocks.
- **key_findings:**
  - Quote midpoint reduces noise vs trades.
  - Jittering smooths boundary bias.
  - Optimal bandwidth determined by ω/σ ratio.
  - Implementation guide reproducible.
- **relevance_to_gtos:** Operational reference for GTOS tick-daemon RV implementation. Should follow these steps verbatim.
- **potential_hypothesis:** Jittered quote-midpoint RV on XAU will reduce day-to-day RV variance by ≥15% vs naive trade-RV.
- **cross_domain_links:** 06
- **gtos_diagnostic:** Implement BHLS realized-kernel pipeline on XAU; compare to current RV.

### 4.3 Realising the Future: Forecasting with HEAVY Models

- **id:** 03-043
- **authors:** Neil Shephard, Kevin Sheppard
- **year:** 2010
- **source:** Journal of Applied Econometrics 25(2): 197-231
- **url:** https://onlinelibrary.wiley.com/doi/abs/10.1002/jae.1158
- **abstract:** HEAVY models use realized measures (RV, BV) directly as inputs in a vector autoregression for both daily-return-variance and realized-variance dynamics. Out-perform GARCH at short horizons across asset classes.
- **key_findings:**
  - HEAVY responds faster to vol shifts than GARCH.
  - Captures structural breaks in vol level.
  - Two-equation system: return-variance and RV-variance.
  - Multivariate version handles covariances.
- **relevance_to_gtos:** Best-in-class candidate for short-horizon vol forecast feeding the heartbeat. Beats GARCH where regime breaks are common (i.e., during high-impact news).
- **potential_hypothesis:** HEAVY on XAU 5-min RV will beat GARCH(1,1) for 1-day-ahead RV by ≥15% MSE.
- **cross_domain_links:** 16
- **gtos_diagnostic:** HEAVY on XAU; backtest 1-day RV forecasts vs GARCH(1,1) over 1y.

### 4.4 Volatility Clustering in Financial Markets: Empirical Facts and Agent-Based Models

- **id:** 03-044
- **authors:** Rama Cont
- **year:** 2007
- **source:** in "Long Memory in Economics" (Springer)
- **url:** http://rama.cont.perso.math.cnrs.fr/pdf/clustering.pdf
- **abstract:** Reviews empirical evidence for volatility clustering and surveys economic mechanisms that could generate it (regime-switching, threshold heterogeneity, news arrival). Presents simple agent-based model where threshold-driven trader activation produces empirical-grade clustering.
- **key_findings:**
  - Volatility clustering is universal across asset classes.
  - GARCH gives exponential ACF decay; empirical decay is slower.
  - Threshold-trader agent-based models match empirics.
  - Investor inertia is a candidate mechanism.
- **relevance_to_gtos:** Theoretical motivation for treating vol as endogenously regime-clustered, supporting the regime-classifier and per-regime parameter tuning in K54.
- **potential_hypothesis:** Daily |r| ACF for XAU at lag 100 will exceed GARCH(1,1)-implied ACF at lag 100 by ≥0.02 (slow-decay test).
- **cross_domain_links:** 17
- **gtos_diagnostic:** Compare empirical vs GARCH-implied |r| ACF on XAU at lags 1, 10, 50, 100.

### 4.5 Continuous-Time Models, Realized Volatilities, and Testable Distributional Implications for Daily Stock Returns

- **id:** 03-045
- **authors:** Torben G. Andersen, Tim Bollerslev, Per Frederiksen, Morten Ø. Nielsen
- **year:** 2010
- **source:** Journal of Applied Econometrics 25(2): 233-261
- **url:** https://onlinelibrary.wiley.com/doi/abs/10.1002/jae.1105
- **abstract:** Tests distributional implications of continuous-time SV-with-jumps models against daily-equity data. Returns standardised by integrated-volatility-plus-jumps approach Gaussianity; shows empirical support for SVJ over pure-SV.
- **key_findings:**
  - r/sqrt(IV+J) approximately Gaussian.
  - Pure-SV cannot match observed kurtosis without jumps.
  - Daily SVJ statistically validated against ABDL framework.
  - Connects continuous-time theory and HF empirical work.
- **relevance_to_gtos:** Framework for using GTOS tick-daemon to disentangle continuous vol from jumps in distributional fits. Suggests separately monitoring jump frequency for risk dashboards.
- **potential_hypothesis:** Daily XAU returns standardised by sqrt(BV + (RV - BV)) will reduce kurtosis from ~6 to <4.
- **cross_domain_links:** 16
- **gtos_diagnostic:** Standardise XAU daily returns by sqrt(BV+J); test Gaussianity (Jarque-Bera).

### 4.6 Dragon-Kings, Black Swans and the Prediction of Crises

- **id:** 03-046
- **authors:** Didier Sornette
- **year:** 2009
- **source:** International Journal of Terraspace Science and Engineering 2(1)
- **url:** https://arxiv.org/pdf/0907.4290
- **abstract:** Argues that some "extreme events" are not power-law-tail outliers (Black Swans) but "Dragon Kings" — outliers from a different generative mechanism (e.g., super-exponential bubble). They are larger than power-law extrapolation predicts and are partially predictable.
- **key_findings:**
  - Dragon Kings = outliers above power-law tail.
  - Mechanism = positive-feedback bubble.
  - Drawdown distributions in equity show DK signature.
  - Suggests non-EVT preparation for largest crises.
- **relevance_to_gtos:** Contrarian to pure-EVT framework. Implies the heartbeat-flatten kill switch should not solely rely on stable-α extrapolation; should also watch for super-exponential price-action signatures (early-warning regime shift).
- **potential_hypothesis:** XAU's 3 largest daily-loss events 2018-2025 will lie above the GPD upper-tail extrapolation curve fit on the rest of the sample by ≥1.5σ.
- **cross_domain_links:** 21
- **gtos_diagnostic:** Plot ranked drawdowns on XAU; overlay GPD fit; flag departures above tail.

### 4.7 Multifractal Detrended Fluctuation Analysis: Practical Applications to Financial Time Series

- **id:** 03-047
- **authors:** various (Kantelhardt et al's framework, applied)
- **year:** 2016
- **source:** Mathematics and Computers in Simulation 126: 63-88
- **url:** https://ideas.repec.org/a/eee/matcom/v126y2016icp63-88.html
- **abstract:** Practical guide to MF-DFA for financial time series; discusses scale ranges, polynomial detrending order, q-spectrum interpretation, finite-sample issues.
- **key_findings:**
  - MF-DFA more robust than R/S for non-stationary series.
  - q-spectrum width measures multifractality strength.
  - Order-1 detrending often sufficient.
  - Sample size 2-5k bars recommended.
- **relevance_to_gtos:** Operational reference for any MF-DFA implementation on GTOS instruments. Suggests minimum data requirements before drawing conclusions about per-instrument multifractality.
- **potential_hypothesis:** XAU H4 returns will exhibit q-spectrum width ≥0.15 (clear multifractality) vs ≤0.05 for ideal Gaussian.
- **cross_domain_links:** 04
- **gtos_diagnostic:** MF-DFA on each instrument H4; report Δh = h(q=-5) - h(q=+5).

### 4.8 The Markov-Switching Multifractal Model of Asset Returns

- **id:** 03-048
- **authors:** Laurent E. Calvet, Adlai J. Fisher
- **year:** 2008
- **source:** Journal of Empirical Finance / Mathematical Finance (book chapter / SSRN)
- **url:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1299397
- **abstract:** MSM models conditional volatility as the product of independent two-state Markov volatility components with frequencies that scale geometrically. Generates pseudo-long-memory and outperforms GARCH/FIGARCH on FX.
- **key_findings:**
  - MSM with k components produces ACF decay matching empirical.
  - ML estimation tractable for moderate k.
  - Out-of-sample beats GARCH on EUR/USD, JPY/USD.
  - Multifractal spectrum recoverable.
- **relevance_to_gtos:** Candidate vol model for FX instruments (USDJPY, GBPJPY, GBPUSD). MSM explicitly multifractal and could feed K54 with regime-mixture probabilities.
- **potential_hypothesis:** MSM with k=8 components on USDJPY D1 will dominate GARCH(1,1) by AIC.
- **cross_domain_links:** 04, 05
- **gtos_diagnostic:** Fit MSM and GARCH on USDJPY D1; AIC compare.

### 4.9 Conditional Skewness in Asset Pricing Tests

- **id:** 03-049
- **authors:** Campbell R. Harvey, Akhtar Siddique
- **year:** 2000
- **source:** Journal of Finance 55(3): 1263-1295
- **url:** https://people.duke.edu/~charvey/Research/Published_Papers/P56_Conditional_skewness_in.pdf
- **abstract:** Documents that conditional skewness of equity returns is time-varying, and that systematic skewness is priced; high conditional skewness implies higher returns. Companion 1999 JFQA paper introduces the autoregressive conditional skewness model.
- **key_findings:**
  - Conditional skewness time-varying.
  - Co-skewness with market priced in cross-section.
  - Three-moment CAPM has explanatory power.
  - Provides AR-skewness specification.
- **relevance_to_gtos:** Skewness of XAU returns may be regime-dependent (gold often positive-skew in safe-haven flight, neutral otherwise). Can feed K54 as a regime feature.
- **potential_hypothesis:** Rolling 30-day skewness of XAU D1 will switch sign at regime transitions detected by the regime classifier; sign-change rate ≥ 70% of transitions.
- **cross_domain_links:** 17
- **gtos_diagnostic:** Compute rolling skew XAU; align with regime classifier; report transition skew flips.

### 4.10 The Generalized Hyperbolic Model

- **id:** 03-050
- **authors:** Karsten Prause; Eberlein and Keller
- **year:** 1995-1999 (foundational Eberlein-Keller; Prause thesis 1999)
- **source:** Bernoulli 1995 / Prause Univ. Freiburg PhD thesis 1999
- **url:** https://webdoc.sub.gwdg.de/ebook/e/2001/freidok/15.pdf
- **abstract:** The GH distribution family contains hyperbolic, NIG, and VG as subclasses; semi-heavy tails interpolate between exponential and power-law. Empirically dominates Gaussian and Student-t for most equity series and exchange rates.
- **key_findings:**
  - GH semi-heavy tails approximate empirical fat-tail behaviour.
  - NIG (λ = -0.5) often the best fit for equity returns.
  - VG (limit case) useful for option pricing.
  - GH supports generalised Black-Scholes pricing.
- **relevance_to_gtos:** Candidate parametric distribution for risk-of-ruin calculations on GTOS. NIG fit on XAU returns provides a closed-form-ish alternative to non-parametric EVT for ES projection.
- **potential_hypothesis:** NIG fit on XAU D1 returns will dominate Gaussian, Student-t (df ∈ {3,4,5,6,7,8}) and skewed-t by AIC.
- **cross_domain_links:** 16, 21
- **gtos_diagnostic:** Fit NIG/GH on each instrument's D1 returns; rank vs Gaussian/t/skew-t by AIC.

---

## 5. Contrarian / under-cited findings

(Selected from above; reproduced for clarity in synthesis.)

- **03-046 Sornette Dragon Kings** — Power-law / EVT extrapolation may underestimate the largest events; super-exponential bubble dynamics are a separate generative mechanism. Recommends event-physics warning systems alongside statistical EVT.
- **03-021 Vyetrenko / MITRE** — Some of Cont's 2001 stylized facts are weakened in modern HFT-era markets; aggregational Gaussianity at 1-min resolution differs from 1990s data. GTOS's facts must be checked on its own data.
- **03-029 NDX asymmetric GARCH** — Leverage parameter γ can change sign across asset classes (equity-index strong, gold often weak / inverse). Universal GARCH risk parameters for a multi-asset book are inappropriate.
- **03-016 Acerbi & Tasche** — VaR is not subadditive; portfolio-level VaR can be misleading. ES is the right coherent risk measure for GTOS portfolio aggregation.
- **03-014 Realized Kernels** — Naive 1-tick RV is biased by microstructure noise; GTOS should not deploy raw-tick RV without kernel correction or sub-sampling.

---

## 6. Top-10 papers most relevant to GTOS

Ordered by direct subsystem leverage.

| Rank | id | Short title | Why top-10 for GTOS |
|------|----|-------------|---------------------|
| 1 | 03-015 | McNeil-Frey GARCH-EVT 2000 | Direct prescription for heartbeat / DD threshold calibration; combines persistence + tail correctly. |
| 2 | 03-009 | Embrechts et al EVT textbook | Methodological bedrock for `project_distributional_findings` xi=0.35; underwrites POT/GPD on GTOS data. |
| 3 | 03-006 | Cont 2001 stylized facts | Master rubric for any GTOS distributional assumption; per-instrument verification baseline. |
| 4 | 03-016 | Acerbi-Tasche coherent ES | VaR can fail subadditivity; portfolio-level GTOS risk must use ES. |
| 5 | 03-011 / 03-029 | GJR-GARCH (and NDX leverage paper) | Per-symbol asymmetric vol modelling; γ varies materially across XAU vs indices vs FX. |
| 6 | 03-026 | 2025 multi-asset GARCH/EVT comparison | Empirical bake-off across gold, oil, BTC, equities — direct guidance for per-instrument vol model choice. |
| 7 | 03-022 / 03-037 | Rough volatility + TV-Hurst | H_t feature for K54 + heartbeat sensitivity to short-horizon vol-spike risk. |
| 8 | 03-041 | Clauset-Shalizi-Newman power-law fitting | Mandatory pipeline upgrade for any GTOS Hill / power-law claim. |
| 9 | 03-027 | Kelly-Jiang tail risk pricing | Tail-risk index across GTOS instruments could feed K54 as regime feature. |
| 10 | 03-046 | Sornette Dragon Kings | Caution against over-relying on EVT extrapolation for largest events; motivates super-exponential warning monitor. |

---

## 7. Cross-domain handoffs & gaps

### Cross-domain handoffs (papers more naturally homed elsewhere)

- **03-013 Bipower variation** — also relevant to **06** (microstructure noise / jump-vs-continuous decomposition).
- **03-022 Rough volatility** — pricing-side belongs to **16**; we keep the empirical-fit-of-vol-roughness-as-stylized-fact angle.
- **03-027 Kelly-Jiang tail risk** — cross-section asset-pricing belongs to **13**; kept here for the tail-index estimator construction itself.
- **03-039 Cojumps + macro news** — cojump propagation belongs to **13**; kept for the within-asset jump-distribution fact.
- **03-028 Gold long memory** — applied gold-specific belongs to **10**; kept for the FIGARCH-d-on-gold descriptive result.
- **03-032 EuroStoxx HF persistence** — equity-index applied belongs to **12**; kept for the d-of-|r| descriptive result.
- **03-014 Realized kernels** — primarily a microstructure paper (06); kept here for its operational role in measuring distributional moments under noise.
- **03-049 Conditional skewness Harvey-Siddique** — asset-pricing belongs to **13**; kept for the AR-skewness time-series specification.

### Identified gaps in this domain

- **Per-symbol GTOS validation.** No paper in this corpus directly fits XAU's exact M15 distribution. GTOS must do this in-house using the diagnostics flagged per-paper.
- **Stable-vs-truncated-Lévy at GTOS-relevant intraday frequencies.** Mantegna-Stanley dates from 1994; modern HFT-era equivalents on FX and gold would be highly relevant but were not directly located in this pass.
- **Tail-comonotonicity in stress periods for GTOS instrument set.** Copula tail-dependence papers exist but do not cover the specific XAU+US30+USDJPY+GBPJPY+GBPUSD+NAS100+XAGUSD bundle. K54 cross-instrument feature work could fill this.
- **Liquidity-tier-conditional EVT.** Most EVT literature uses unconditional or vol-conditional sampling; KZ-conditioned tail estimation would be directly GTOS-relevant and appears under-studied.
- **Order-flow-conditioned tails.** Hawkes-process / rough-vol papers connect microstructure to vol but do not deliver an empirical operational tail-estimator conditional on observed order-flow imbalance.

### Caveats / recommendations for synthesis

1. The CSV `papers.csv` is the machine-readable mirror of this MD; both MUST be edited together.
2. Every `gtos_diagnostic` field is an MT5-runnable test — they collectively define a Phase-2 candidate work-package.
3. The strongest action item from this domain is to **run the McNeil-Frey GARCH-EVT pipeline on every GTOS instrument** and re-cut the heartbeat / drawdown-manager thresholds against ES at 99% / 1d. Without this, the 4% portfolio-DD hard rule is implicitly Gaussian under heavy-tailed reality.
4. The decay-anchored rationale for K54 (per-regime LightGBM) is reinforced by 03-006, 03-021, 03-037, 03-046 — distribution and tail behaviour are themselves regime-dependent.

---

*End of papers.md. Companion file: `papers.csv`.*
