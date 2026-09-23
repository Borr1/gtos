# Domain 02 — Statistical Methodology & Validation in Finance

**Worker:** Phase 1 Literature Agent #2 (Opus 4.7 max effort)
**Date:** 2026-04-28
**Spec:** `research/ml_program/literature/_specs/02_statistical_methodology.md`
**Target:** 40-60 papers; quality bar dominates

---

## Section 1 — Domain scope (covered + deferred)

**Covered (in this paper set):**
- Multiple-testing correction in finance (Bonferroni; Benjamini-Hochberg FDR; Romano-Wolf step-down; Harvey-Liu-Zhu haircut)
- Backtest overfitting + selection bias (Bailey-Lopez de Prado deflated Sharpe; PBO; Probability of Backtest Overfitting)
- Forecast comparison (Diebold-Mariano; Giacomini-White; encompassing tests; Mincer-Zarnowitz)
- Reality check / superior predictive ability (White RC; Hansen SPA; Romano-Wolf stepwise SPA)
- Cross-validation for time series (Combinatorial Purged CV; walk-forward; rolling vs expanding window)
- Triple-barrier labeling and meta-labeling (Lopez de Prado AFML)
- Sequential testing and change-point monitoring (SPRT, Page CUSUM, Generalized CUSUM)
- Bootstrap inference for non-iid time series (stationary bootstrap; circular block; subsampling)
- Bayesian model selection / Bayesian backtesting in finance
- Sharpe ratio confidence intervals; haircuts; minimum-track-record-length
- Replication crisis in asset pricing / factor zoo

**Deferred (cross-link only, not full entries):**
- GARCH families and EVT inference → 03 (distributional)
- Specific stochastic-process theory (Ito, Levy) → 01
- ML model architectures / asset-pricing ML applications → 19/20
- Hedge-fund alpha decay quantification (McLean-Pontiff) → 22 (cross-link recorded)
- Regime-switching / change-point detection methodology specific to vol regimes → 05 (we keep general SPRT/CUSUM)

**Methodology bias note:** We aim for breadth over Sharpe-ratio variant proliferation. Domain 02 owns multiple-testing + forecast-comparison + sequential-monitoring + CV-for-time-series. Roughly equal weight across these subtopics.

---

## Section 2 — Foundational papers

### Comparing Predictive Accuracy
- **Authors / Year:** Diebold, F. X., & Mariano, R. S., 1995
- **Source / URL:** Journal of Business & Economic Statistics, 13(3), 253-263. https://www.tandfonline.com/doi/abs/10.1080/07350015.1995.10524599
- **Abstract:** Proposes asymptotic and exact finite-sample tests for the null hypothesis of equal predictive accuracy of two competing forecasts. The DM test is non-parametric in its accuracy metric (any user-supplied loss function) and accommodates non-Gaussian, serially correlated, and contemporaneously correlated forecast errors. The test has become the workhorse for forecast-pair comparison.
- **Key findings:**
  - Standard t-test on loss-difference is asymptotically valid under wide conditions when standard errors are HAC-corrected.
  - Sign-test and Wilcoxon-signed-rank variants robust to outliers in loss-differences.
  - Power dominates earlier Granger-Newbold encompassing-style tests for general loss functions.
- **Relevance to GTOS:** Direct framework for comparing two prompt versions, two SL/TP rule variants, or two regime-classifier signals on realized-R or hit-rate-loss. The K54 vs Sonnet-4.6-on-MSO comparison should report DM statistics on per-trade-loss series, not just point estimates. Joining walk-level and realized-R discipline (memory `feedback_walk_level_evidence_not_predictive`) is a natural DM-style test.
- **Hypothesis implied:** *DM test on loss-differential between v1 (LONG-only-detector) and v2 (regime-conditioned) market-state classifiers will detect significant directional improvement in H2-2026 if regime-conditioned features are genuinely orthogonal predictors.*
- **Cross-domain links:** none (canonical Domain 02).

### A Reality Check for Data Snooping
- **Authors / Year:** White, H., 2000
- **Source / URL:** Econometrica, 68(5), 1097-1126. https://onlinelibrary.wiley.com/doi/abs/10.1111/1468-0262.00152
- **Abstract:** Introduces the "Reality Check" bootstrap test for the null that the best of a set of forecasts/strategies has zero performance vs a benchmark, controlling family-wise error rate (FWER) under data snooping. Stationary-bootstrap based; works under serial dependence and non-Gaussianity. Foundational paper for backtest-search significance.
- **Key findings:**
  - Naive significance tests on the best-strategy-from-N severely understate p-values.
  - Stationary-bootstrap p-values control FWER under broad serial dependence assumptions.
  - Empirical illustration: technical-trading rules on Dow Jones lose all significance after correction.
- **Relevance to GTOS:** Multiple-testing correction is the operative discipline for our K-series re-tests (K52 retested 5 Validated Numbers; F-series re-tested ~12 features). Any "best-of-N strategy" claim from the canary fixture set or per-regime cell explorations should be Reality Check-corrected before promotion.
- **Hypothesis implied:** *After Reality Check correction over the 47 instrument×side×regime cells we monitor, fewer than 3 cells will retain significance vs benchmark — implying most "regime-pinpointed" findings (e.g., F2 trending_bull LONG -59.8pp) are within data-snooping noise unless cross-validated out-of-sample.*
- **Cross-domain links:** none.

### A Test for Superior Predictive Ability
- **Authors / Year:** Hansen, P. R., 2005
- **Source / URL:** Journal of Business & Economic Statistics, 23(4), 365-380. https://www.tandfonline.com/doi/abs/10.1198/073500105000000063 ; SSRN: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=264569
- **Abstract:** Proposes the SPA test, an improvement on White's Reality Check that uses a studentized statistic and a sample-dependent (rather than least-favorable) null distribution. SPA is more powerful and less sensitive to poor/irrelevant alternatives in the candidate set.
- **Key findings:**
  - Studentization stabilizes test performance when candidate strategies have heterogeneous variance (very common in factor zoos).
  - Sample-dependent null avoids the conservative bias of LFC.
  - Empirical illustration: regression-based US-inflation forecasts beat random walk only after SPA correction; Phillips-curve-style models survive.
- **Relevance to GTOS:** SPA is the upgrade of choice for canary-fixture regression: when we evaluate N prompt versions or N gate configurations, SPA gives the right p-value. Strictly stronger than Bonferroni for this use case.
- **Hypothesis implied:** *Re-running the full 75-fixture canary across the 6 prompt variants tested in research/prompt_cascade_ab_test under SPA would reduce the apparent "winners" by ≥50% relative to per-fixture Bonferroni.*
- **Cross-domain links:** none.

### Continuous Inspection Schemes (CUSUM)
- **Authors / Year:** Page, E. S., 1954
- **Source / URL:** Biometrika, 41(1/2), 100-115. https://academic.oup.com/biomet/article-abstract/41/1-2/100/456627
- **Abstract:** Introduces the cumulative sum control chart (CUSUM) for sequential change-point detection. Designed for industrial quality control but adopted broadly across financial monitoring. Fundamental reference for online detection of mean-shifts in a stream.
- **Key findings:**
  - CUSUM detects small persistent shifts in mean faster than Shewhart-style charts.
  - Average run length (ARL) tradeoff: low false-alarm ARL at the cost of detection delay.
  - V-mask geometry yields a graphically interpretable decision rule.
- **Relevance to GTOS:** `shadow_logs/cusum_candidate_rate_daily.csv` is the live use of this method. CUSUM grounding here is direct. Also relevant for OB continuation rolling-50 monitor, which is a moving-window precursor to CUSUM.
- **Hypothesis implied:** *Replacing the rolling-50 OB-continuation alarm (<60% threshold) with a Page CUSUM tuned to detect a 10pp drop with ARL₀ ≥ 200 will reduce false alarms and detection delay simultaneously.*
- **Cross-domain links:** 05 (change-point detection methodology) — paper sits squarely in 02 because of its sequential-monitoring methodology angle.

### Sequential Tests of Statistical Hypotheses
- **Authors / Year:** Wald, A., 1945
- **Source / URL:** Annals of Mathematical Statistics, 16(2), 117-186. https://projecteuclid.org/journals/annals-of-mathematical-statistics/volume-16/issue-2/Sequential-Tests-of-Statistical-Hypotheses/10.1214/aoms/1177731118.full
- **Abstract:** Foundational paper for the Sequential Probability Ratio Test (SPRT). Defines the optimal sample-size-not-fixed-in-advance test that minimizes expected sample size at given Type I/II errors via the likelihood ratio process and Wald boundaries.
- **Key findings:**
  - SPRT minimizes both E[N | H0] and E[N | H1] subject to error constraints (Wald-Wolfowitz optimality).
  - Decision boundaries are A = (1−β)/α and B = β/(1−α) on the likelihood ratio.
  - Generalizes to composite hypotheses via approximations.
- **Relevance to GTOS:** Direct foundation for our XAUUSD LONG-WR-watch SPRT halt rule (item #4 of CLAUDE.md unresolved). Also drives any per-instrument SPRT halt protocol on edge-decay detection.
- **Hypothesis implied:** *An SPRT calibrated to detect drop from 60% to 45% WR with α=β=0.05 will halt XAUUSD LONG within ~22 trades if the H2-2026 regime persists, vs ~50+ trades for fixed-N significance testing.*
- **Cross-domain links:** none.

### Stock Market Prices Do Not Follow Random Walks (Variance Ratio Test)
- **Authors / Year:** Lo, A. W., & MacKinlay, A. C., 1988
- **Source / URL:** Review of Financial Studies, 1(1), 41-66. https://www-2.rotman.utoronto.ca/~kan/3032/pdf/PredictabilityOfReturns_ShortHorizon/Lo_MacKinlay_RFS_1988.pdf
- **Abstract:** Develops the variance-ratio (VR) test for the random-walk null using the property that under iid, Var(r_q)/q × Var(r_1) = 1. Robust to heteroskedasticity. Rejects RW for weekly US returns over 1962-1985.
- **Key findings:**
  - VR(q)>1 indicates positive serial correlation; VR<1 indicates negative.
  - Heteroskedasticity-consistent variance estimator robust under non-iid noise.
  - Strong rejection of RW for weekly returns; weaker for individual stocks (size-stratified).
- **Relevance to GTOS:** OB continuation = a form of short-horizon directional persistence — VR test on M15 returns at OB-touch events would quantify whether the edge is genuine vs noise. Also relevant to A1 dumb-baseline reversal: VR(q) sign-flip from H1 to H2 would corroborate "regime-conditioned momentum decay."
- **Hypothesis implied:** *VR(q=4) computed on 60-minute returns post-OB-touch will be significantly >1 in pre-2026 sample but indistinguishable from 1 in H2-2026 — providing model-free corroboration of F11's OB decay finding.*
- **Cross-domain links:** 14 (momentum / mean-reversion stylized fact); 03 (random-walk distributional benchmark). Cross-link only.

### Predictability of Stock Returns: Robustness and Economic Significance
- **Authors / Year:** Pesaran, M. H., & Timmermann, A., 1995
- **Source / URL:** Journal of Finance, 50(4), 1201-1228. https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.1995.tb04055.x
- **Abstract:** Recursive predictive modeling of S&P returns using model-selection and out-of-sample evaluation. Shows in-sample R² inflated relative to true predictive performance; introduces hyperparameter-search-corrected predictive metrics.
- **Key findings:**
  - Recursive model selection (BIC at each step) generates positive economic value over passive benchmark.
  - Trading rules robust to transaction costs only in 1980s subsample; degrade thereafter.
  - Out-of-sample R² is heavily inflated by hyperparameter search.
- **Relevance to GTOS:** Methodological template for recursive-window evaluation of K-series ML pipeline. Directly addresses the "edge decay" pattern: a regime that enabled OB-edge in 2024-25 does not guarantee 2026 performance.
- **Hypothesis implied:** *A recursive (expanding-window) backtest of the K54 LightGBM pipeline starting 2025-Q1 with quarterly retraining will produce a confidence interval for live H2-2026 performance that is much tighter than naive split-sample CV.*
- **Cross-domain links:** 19 (ML for finance, recursive-fit angle); 14 (return predictability content). Method dominates → kept here.

### A Comprehensive Look at the Empirical Performance of Equity Premium Prediction
- **Authors / Year:** Goyal, A., & Welch, I., 2008
- **Source / URL:** Review of Financial Studies, 21(4), 1455-1508. https://www.ivo-welch.info/research/journalcopy/2008-rfs.pdf
- **Abstract:** Critical evaluation of decades of equity-premium-predictability claims. Re-runs the canonical predictors (D/P, E/P, T-bill rate, term spread) using strict out-of-sample protocols. Finds that very few predictors out-perform the historical mean.
- **Key findings:**
  - Of 14 canonical predictors, virtually none generate stable out-of-sample R² > 0 across periods.
  - Out-of-sample R² is the right metric; in-sample R² massively overstates power.
  - "Constancy of conditional expectation" benchmark is brutally hard to beat.
- **Relevance to GTOS:** This is the empirical pre-decay analogue of GTOS's 2026 H2 collapse: predictors that "worked" in subsamples failed once stress-tested out-of-sample. Methodological lesson: report rolling out-of-sample R² (or hit rate, or realized-R), not only full-sample-fit metrics, in K54 evaluation.
- **Hypothesis implied:** *Applying the Goyal-Welch out-of-sample-R² protocol to GTOS regime classifier signals will show OOS-R² ≤ 0 for ≥50% of "in-sample-significant" features — corroborating F5's "K51 does NOT replicate under proper SHAP" finding.*
- **Cross-domain links:** 14 (return predictability content); 19 (predictive-model methodology).

### Advances in Financial Machine Learning (AFML, esp. Ch. 7-12)
- **Authors / Year:** Lopez de Prado, M., 2018
- **Source / URL:** Wiley. ISBN 978-1-119-48208-6. https://philpapers.org/rec/LPEAIF (description) ; SSRN excerpts: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3193556
- **Abstract:** Comprehensive textbook covering financial-ML practice with strong methodological discipline. Chapters 7-12 cover purged CV, embargoing, combinatorial purged cross-validation (CPCV), backtest statistics, deflated Sharpe, and the probability of backtest overfitting (PBO). De-facto standard reference for ML-discipline in finance.
- **Key findings:**
  - Naive k-fold CV in time-series leaks information across folds; purged CV plus embargoing fixes leakage.
  - CPCV samples ≥10² distinct test-train paths from the data, dramatically more robust than walk-forward.
  - Triple-barrier labeling (Ch. 3) creates labels for ML that mirror real trade outcomes (TP, SL, time-out).
  - Meta-labeling (Ch. 3) layers a binary skill classifier above a base predictor — directly applicable.
- **Relevance to GTOS:** This is THE methodological reference for K54 v2 ML pipeline (CLAUDE.md item #11). Triple-barrier + meta-labeling map cleanly onto our existing TP/SL/time-out labeling. CPCV is the validation-method the spec mandates.
- **Hypothesis implied:** *Replacing the K54 baseline's stratified-k-fold CV with CPCV will reduce the train-test AUC gap by ≥0.05 and provide a tighter CI on the live realized-R lift estimate.*
- **Cross-domain links:** 19 (ML methodology); 21 (sizing for triple-barrier). Method dominates → kept here.

### The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest Overfitting and Non-Normality
- **Authors / Year:** Bailey, D. H., & Lopez de Prado, M., 2014
- **Source / URL:** Journal of Portfolio Management, 40(5), 94-107. SSRN: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551 ; PDF: https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf
- **Abstract:** Defines a "deflated" Sharpe ratio that adjusts for (i) non-normality of returns (skewness, kurtosis), and (ii) selection bias from multiple testing under N candidate strategies. Provides a formula for minimum track record length (MinTRL) needed for a Sharpe to be statistically significant at chosen confidence.
- **Key findings:**
  - DSR formula: SR* corrects PSR (probabilistic SR) by an effective N (number of trials) using the variance of trialed SRs.
  - Non-normality correction: high-skew, fat-tail PnL distributions inflate naive SR significance.
  - MinTRL provides actionable rule-of-thumb: a SR of 1.0 from one model needs 9 years of monthly returns; from 100 trialed models, ~30+ years.
- **Relevance to GTOS:** Directly applicable to evaluating any "outlier" Sharpe metric in the J46-J49 portfolio policy work (project_j46_j49_position_mgmt_findings) and the K54 baseline lift. Also gives MinTRL for the live-trading authorization (n=321 trades is short by deflated-SR standards).
- **Hypothesis implied:** *J46-J49's reported +0.742R/trade lift will pass the DSR test at p<0.05 only if effective N (trial count over walk-forward) is documented and ≤30; any larger candidate-pool inflates DSR-corrected p above 0.10.*
- **Cross-domain links:** 21 (sizing implications); cross-link only.

### ...and the Cross-Section of Expected Returns
- **Authors / Year:** Harvey, C. R., Liu, Y., & Zhu, H., 2016
- **Source / URL:** Review of Financial Studies, 29(1), 5-68. https://academic.oup.com/rfs/article/29/1/5/1843824 ; SSRN: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2249314 ; NBER: https://www.nber.org/papers/w20592 ; Duke PDF: https://people.duke.edu/~charvey/Research/Published_Papers/P118_and_the_cross.PDF
- **Abstract:** Surveys hundreds of papers proposing factors explaining the cross-section. Argues that conventional t > 2.0 cutoff is grossly insufficient given multiple testing across 300+ factors. Proposes t > 3.0 as new threshold and applies Holm/BHY/Romano-Wolf haircuts to historical t-stats.
- **Key findings:**
  - Most published factors fail under multiple-testing-corrected thresholds.
  - Holm step-down + BHY are appropriate corrections; standard Bonferroni too conservative.
  - Provides a time-series of cumulative discovered-factor count → required-t-threshold function.
  - Strong empirical evidence for asset-pricing replication crisis.
- **Relevance to GTOS:** Direct precedent for our Validated Numbers Bonferroni discipline (4 of 5 survive K52). Suggests we should track running count of "tests we have taken" and adjust threshold accordingly. Item #11 in unresolved list (Phase 2 K-series) needs this discipline.
- **Hypothesis implied:** *Adopting the Harvey-Liu-Zhu running-haircut with current-cumulative-test-count for the GTOS Validated Numbers regime will downgrade ≥1 of the 4 currently-surviving findings to "not corrected significant" within 12 months of continued K-series exploration.*
- **Cross-domain links:** 13 (factor-zoo content); 22 (alpha-decay quantification cross-link). Method dominates → kept.

### Probability of Backtest Overfitting (PBO)
- **Authors / Year:** Bailey, D. H., Borwein, J., Lopez de Prado, M., & Zhu, Q. J., 2017
- **Source / URL:** Journal of Computational Finance, 20(4), 39-69. SSRN: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2326253 ; PDF: https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf
- **Abstract:** Defines PBO as the probability that the strategy selected as "best in-sample" out of N candidates will rank below median out-of-sample. Estimable via combinatorial-symmetric-cross-validation (CSCV). Threshold PBO > 0.5 = highly overfit.
- **Key findings:**
  - PBO is computable with no assumptions on return distribution.
  - PBO scales rapidly with N candidates and shrinks slowly with sample length.
  - Simple visual diagnostic (in-sample vs out-of-sample SR scatter) discriminates overfit from real strategies.
- **Relevance to GTOS:** PBO is the right diagnostic for the K-series and prompt-cascade work. Computing PBO over the 6 prompt-cascade variants × 75 canary fixtures would directly quantify overfit risk.
- **Hypothesis implied:** *The published "v3 cascade" prompt template (research/prompt_cascade_ab_test/RECOVERED_v3_cascade_template.py.txt) when re-evaluated in PBO terms over its variant siblings will exceed PBO = 0.4, justifying the post-Phase-2-research-candidate deferral.*
- **Cross-domain links:** 19 (overfitting in ML).

### Pseudo-Mathematics and Financial Charlatanism: The Effects of Backtest Overfitting on Out-of-Sample Performance
- **Authors / Year:** Bailey, D. H., Borwein, J., Lopez de Prado, M., & Zhu, Q. J., 2014
- **Source / URL:** Notices of the American Mathematical Society, 61(5), 458-471. https://www.ams.org/notices/201405/rnoti-p458.pdf
- **Abstract:** Companion to PBO with a polemic edge: shows analytically and via simulation that with sufficient candidate strategies, ANY desired Sharpe in-sample is achievable on random data. Shows the sharp curvature: small N (10) → modest overstatement; large N (1000+) → near-arbitrary IS Sharpe.
- **Key findings:**
  - With n historical observations and N trials, expected best in-sample Sharpe ≈ √(2 ln N / n) under iid noise.
  - The relationship is independent of true Sharpe, making naive backtests dangerous.
  - Industry standard reporting "best Sharpe" without N is mathematically meaningless.
- **Relevance to GTOS:** A reminder for any "best-fixture" or "best-prompt-variant" claim: must report N and apply DSR or PBO. Also a great paper for the broader research-program training material.
- **Hypothesis implied:** *Applying the formula E[max IS SR] ≈ √(2 ln N / n) to the cumulative GTOS prompt-cascade trial count (~200 across all phases) suggests baseline noise-only IS Sharpe ≈ 0.6-0.8 — anything below this in our backtest population is statistically attributable to chance.*
- **Cross-domain links:** none.

### Combinatorial Purged Cross-Validation Method
- **Authors / Year:** Lopez de Prado, M. (popularized; Hudson and Thames + others extended), 2018+
- **Source / URL:** AFML Ch. 12; Towards AI tutorial: https://towardsai.net/p/l/the-combinatorial-purged-cross-validation-method ; Hudson and Thames implementation: https://hudsonthames.org/combinatorial-purged-cross-validation-explained/
- **Abstract:** Generalizes walk-forward by enumerating all C(N, k) train-test combinations on N time-blocks with k blocks held out. Purges training blocks adjacent to test blocks; embargos training blocks immediately following test. Yields ≥10² distinct paths instead of walk-forward's 1.
- **Key findings:**
  - Variance of estimated Sharpe across CPCV paths quantifies path-dependence risk.
  - Each CPCV path is a valid simulated alternative-history performance estimate.
  - Purging removes label-overlap leakage; embargoing removes serial-correlation leakage.
- **Relevance to GTOS:** Mandated method for K54 v2 (Section 5 of spec). Provides the right CI on K54 lift estimate, much tighter than the AUC 0.571 naive split.
- **Hypothesis implied:** *Re-running K54 baseline under CPCV with k=2 on N=12 monthly blocks (66 paths) will report a 5-95% CI on hit-rate-lift that excludes 0 in <30% of configurations — a stricter promotion gate than the current single-AUC headline.*
- **Cross-domain links:** 19 (ML methodology).

### Triple-Barrier Method and Meta-Labeling
- **Authors / Year:** Lopez de Prado, M. (AFML Ch. 3), 2018
- **Source / URL:** AFML Ch. 3. SSRN excerpt: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3193556 ; Quantopian/QF lectures and Hudson and Thames blog posts.
- **Abstract:** Triple-barrier labels each observation by which of {TP, SL, time-out} is hit first, generating realistic R-multiple labels for ML. Meta-labeling adds a binary "skill" model on top of a primary model, used to size or filter signals.
- **Key findings:**
  - TBM labels have direct realized-R interpretation, unlike fixed-horizon returns.
  - Meta-labeling improves precision at cost of recall — a sizing layer, not a signal layer.
  - Empirically, meta-labeling stabilizes Sharpe under non-stationarity.
- **Relevance to GTOS:** Existing GTOS labels (TP/SL/BE/time-stop) align directly with the triple-barrier method. K54 should explicitly use TBM labels. Meta-labeling pattern matches GTOS architecture: Component 3A primary signal + meta-classifier (K54) for skill filtering.
- **Hypothesis implied:** *Wiring K54 as a meta-labeler over Component 3A (rather than a side-by-side replacement) preserves the AI's directional signal while filtering the H2-2026 LONG-bias decay; expected lift +0.10R/trade vs current state.*
- **Cross-domain links:** 19 (ML methodology), 21 (sizing).

---

### Stepwise Multiple Testing as Formalized Data Snooping
- **Authors / Year:** Romano, J. P., & Wolf, M., 2005
- **Source / URL:** Econometrica, 73(4), 1237-1282. https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1468-0262.2005.00615.x ; PDF (Wisconsin): https://users.ssc.wisc.edu/~behansen/718/RomanoWolf2005.pdf
- **Abstract:** Develops the StepM stepwise procedure that asymptotically controls FWER under arbitrary dependence among test statistics, using studentized statistics + bootstrap. Strictly more powerful than single-step (e.g., Bonferroni / Holm) since it captures joint dependence structure.
- **Key findings:**
  - Studentized statistics give bootstrap refinements (asymptotic-coverage-correctness).
  - StepM iteratively rejects: at each step, compute critical value from remaining hypothesis subset.
  - Simulation: substantial power gain over Holm / Bonferroni, especially when test statistics are correlated.
- **Relevance to GTOS:** The right method for multi-fixture canary or multi-cell SPRT analysis. Spec §7 explicitly recommends "Romano-Wolf step-down on the 47 SPRT-tested instrument-side cells" — this paper is the canonical reference.
- **Hypothesis implied:** *Romano-Wolf StepM at α=0.05 over the 47 instrument×side×regime cells will reject ≤7 cells (vs Bonferroni's ~3 and uncorrected ≥15) — a power-vs-discipline sweet spot for production gate decisions.*
- **Cross-domain links:** none (canonical 02).

### Tests of Conditional Predictive Ability
- **Authors / Year:** Giacomini, R., & White, H., 2006
- **Source / URL:** Econometrica, 74(6), 1545-1578. https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1468-0262.2006.00718.x ; PDF: http://fmwww.bc.edu/EC-P/wp572.pdf
- **Abstract:** Generalizes Diebold-Mariano to conditional comparisons: at any given point, given current information, which forecast will be more accurate? Captures finite-sample-estimation uncertainty asymptotically. Two-step decision rule for forecast selection conditional on regime.
- **Key findings:**
  - Conditional tests can detect time-varying forecast superiority that unconditional tests miss.
  - Test statistic asymptotically chi-squared; tractable.
  - Empirical example: yen/dollar exchange-rate forecasts → conditional rule outperforms each unconditional model.
- **Relevance to GTOS:** Critically relevant given F15 (regime-conditioned decay): a forecast comparison that ignores regime will mask a model's regime-specific dominance. The conditional framework is essentially what we need to evaluate K54-vs-Sonnet 4.6 under regime conditioning.
- **Hypothesis implied:** *A conditional Giacomini-White test on K54 vs Sonnet-4.6 (current Component 3A) using current regime as conditioner will detect K54-superiority within H2 trending_bull (where Sonnet underperforms) even if unconditional DM is null — directly informing K54 production-gate design.*
- **Cross-domain links:** 05 (regime classification feeds the conditioner), 19 (model comparison).

### Controlling the False Discovery Rate
- **Authors / Year:** Benjamini, Y., & Hochberg, Y., 1995
- **Source / URL:** Journal of the Royal Statistical Society Series B, 57(1), 289-300. https://rss.onlinelibrary.wiley.com/doi/10.1111/j.2517-6161.1995.tb02031.x
- **Abstract:** Introduces the False Discovery Rate (FDR) as a multiple-testing error metric: expected proportion of false positives among rejections. Proposes the BH step-up procedure that controls FDR under independence (and positive dependence). Foundation for "discovery" workflows.
- **Key findings:**
  - FDR ≤ FWER; controlling FDR is much more powerful than controlling FWER when many hypotheses are non-null.
  - BH procedure: order p-values, find largest k such that p(k) ≤ q × k / m, reject all p(1)...p(k).
  - Applies to most genomics / large-scale screening; appropriate when the discovery cost vs miss cost favors rejection power.
- **Relevance to GTOS:** A more permissive (and arguably more appropriate) gate than Bonferroni for the "screening" K-series feature exploration. Better metric for the K50/K51/K53 SHAP-style importance ranking. Also right for the Validated Numbers regime if the tradeoff is "we tolerate 10% false positives in exchange for not missing real signals".
- **Hypothesis implied:** *BH-FDR at q=0.10 across the 12 K-series feature-importance tests will retain 5-7 features as "discovered", vs Bonferroni's 1-2 — providing a richer feature set for K54 ML pipeline.*
- **Cross-domain links:** none.

### The Stationary Bootstrap
- **Authors / Year:** Politis, D. N., & Romano, J. P., 1994
- **Source / URL:** Journal of the American Statistical Association, 89(428), 1303-1313. https://www.tandfonline.com/doi/abs/10.1080/01621459.1994.10476870 ; PDF: https://users.ssc.wisc.edu/~behansen/718/Politis%20Romano.pdf
- **Abstract:** Proposes resampling blocks of geometric-distributed random length to preserve stationarity in the bootstrap distribution. Generalizes block-bootstrap; appropriate for general weakly-dependent stationary time series with unknown dependence structure.
- **Key findings:**
  - Geometric block lengths break the boundary effects of fixed-block bootstrap.
  - Bootstrap-CIs for mean, variance, and stationary functionals consistent for weak-dependent series.
  - Practical implementation: resample blocks of length ~ 1/p, where p is geometric parameter.
- **Relevance to GTOS:** Use in computing realistic confidence intervals on Sharpe / hit-rate / expectancy metrics in the K54 evaluation. Naive iid bootstrap would be wrong; stationary bootstrap is the right answer for trade-by-trade non-iid data.
- **Hypothesis implied:** *Stationary-bootstrap-CI on the J46-J49 portfolio +0.742R/trade lift (n=321) will be wider than the implied iid CI (which gives the n=321 p=3.3e-20 figure) by ≥30% — possibly removing the "extreme significance" headline.*
- **Cross-domain links:** 03 (bootstrap inference for fat tails), 19 (ML CI).

### The Evaluation of Economic Forecasts (Mincer-Zarnowitz)
- **Authors / Year:** Mincer, J., & Zarnowitz, V., 1969
- **Source / URL:** NBER chapter. https://www.nber.org/system/files/chapters/c1214/c1214.pdf
- **Abstract:** Proposes the Mincer-Zarnowitz regression: regress realized values on forecasts and test (intercept, slope) = (0, 1). Joint test of forecast unbiasedness + efficiency. Becomes the standard rationality test for any point-forecast.
- **Key findings:**
  - Optimal forecast satisfies α=0, β=1 in the Y_t = α + β × F_t + ε_t regression.
  - Provides decomposition of forecast MSE: bias + slope error + residual.
  - Robust to wide classes of loss functions when extended (quantile / expectile MZ regressions).
- **Relevance to GTOS:** Excellent diagnostic for AI-emitted price predictions vs realized prices in our trade journal. If Component 3A's predicted entry / SL / TP have systematic α≠0 or β≠1, it pinpoints calibration error vs perception error (resonates with F8: hallucination is NOT the decay mechanism, decision-making calibration is).
- **Hypothesis implied:** *Mincer-Zarnowitz regression of realized-take-profit-price on AI-emitted-take-profit (over n>200 closed trades) will reject (α=0, β=1) for XAUUSD H2-2026 with α<0 (overstated TP) — quantifying AI's H2 over-optimism in TP placement.*
- **Cross-domain links:** 18 (decision-calibration angle).

### The Statistics of Sharpe Ratios
- **Authors / Year:** Lo, A. W., 2002
- **Source / URL:** Financial Analysts Journal, 58(4), 36-52. https://rpc.cfainstitute.org/research/financial-analysts-journal/2002/the-statistics-of-sharpe-ratios ; Two Sigma report: https://www.twosigma.com/wp-content/uploads/sharpe-tr-1.pdf
- **Abstract:** Derives asymptotic distribution of the Sharpe ratio under iid, stationary, and serially-correlated returns. Shows monthly Sharpe cannot be √12-annualized except under iid; correct annualization uses HAC. Hedge fund SR can be inflated up to 65% due to serial correlation.
- **Key findings:**
  - HAC-adjusted SR confidence intervals are the right benchmark.
  - √T scaling assumes iid; real returns have SR-time dependence.
  - Practical implication: many published SR are over-stated by 30-65%.
- **Relevance to GTOS:** A reminder that any GTOS Sharpe metric must be HAC-adjusted (we have intra-day, intra-week serial correlation in PnL), and that comparing across instruments/strategies must account for it. K54 Sharpe lift estimate must use HAC SE.
- **Hypothesis implied:** *HAC-adjusted SR confidence intervals on GTOS portfolio (across 7 instruments) will widen the implied SR by 20-40% vs naive √T-scaling — possibly removing currently-claimed CI exclusions of zero.*
- **Cross-domain links:** 21 (Sharpe-as-sizing-input).

### A Comprehensive 2022 Look at the Empirical Performance of Equity Premium Prediction
- **Authors / Year:** Goyal, A., Welch, I., & Zafirov, A., 2024 (RFS published; 2022 SSRN)
- **Source / URL:** Review of Financial Studies, 37(11), 3490-3557. https://academic.oup.com/rfs/article/37/11/3490/7749383 ; SSRN: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3929119
- **Abstract:** Updated 2022-version of Goyal-Welch (2008): tests 29 newly-published predictors plus the original 17. Finds >1/3 lose in-sample significance; of survivors, half lose out-of-sample. Severe replication crisis confirmation.
- **Key findings:**
  - Of 46 candidate predictors, only ~5 retain reasonable OOS performance.
  - "New" post-2008 variables degrade as fast as the originals — implying the data-snooping cost of the entire factor literature is enormous.
  - Confirms that out-of-sample R²>0 is the tight constraint, not in-sample t > 2.
- **Relevance to GTOS:** Directly speaks to GTOS edge decay (item #4): we are watching live what Goyal-Welch describe in long-run cross-section. Methodology is the OOS/IS split test we need to apply systematically.
- **Hypothesis implied:** *Decomposing GTOS-edge by Goyal-Welch protocol (in-sample 2024-25 vs OOS Q1-Q2 2026) will show ≥3 of the 5 currently-confirmed Validated Numbers losing OOS-R²>0 status — identifying the next K-series re-tests.*
- **Cross-domain links:** 14, 19, 22.

### The Three Types of Backtests
- **Authors / Year:** Joubert, J., Sestovic, D., Barziy, I., Distaso, W., & Lopez de Prado, M., 2024
- **Source / URL:** SSRN: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4897573
- **Abstract:** Defines three classes of backtest: walk-forward, resampling-based, and Monte-Carlo / simulation-based. Argues for explicit reporting of which class is used, with their respective strengths and pathologies.
- **Key findings:**
  - Walk-forward has highest face-validity but smallest effective sample (1 path).
  - Resampling (CPCV, bootstrap) provides distribution but assumes stationarity.
  - Monte-Carlo / simulation can stress-test under explicit non-stationarity but requires generative models.
  - Recommendation: use all three; report each with caveats.
- **Relevance to GTOS:** Direct prescription for K54 evaluation regime: should report walk-forward + CPCV + a Monte-Carlo simulation under regime-shift assumptions, not just one. Currently-reported AUC 0.571 is single-class; we need multi-class.
- **Hypothesis implied:** *K54 baseline reported across all three backtest types (walk-forward + CPCV + Monte-Carlo with 30%-shift regime stress) will produce ≥2× difference between best and worst metric — corroborating MARGINAL_WITH_PRACTICAL_LIFT verdict.*
- **Cross-domain links:** 19.

### Backtesting (Lopez de Prado standalone)
- **Authors / Year:** Lopez de Prado, M., 2015
- **Source / URL:** SSRN: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2606462
- **Abstract:** Critical look at common backtest pathologies. Catalogs ten backtest "sins" (overfit, data-mining bias, look-ahead, survivorship, transaction-cost neglect, etc.) with diagnostics. Strong practitioner reference.
- **Key findings:**
  - The single biggest backtest sin is selection bias (best-of-N inflation).
  - Look-ahead is subtle: even "obvious" leakage like using close-to-place-stop on the same bar is invisible to many tools.
  - Transaction-cost realism (slippage, partial-fills, queue position) cuts most backtest Sharpe by ≥30%.
- **Relevance to GTOS:** Pre-flight checklist for any K54 / J-series / S-series backtest run. Already integrated as discipline; this paper is the citation.
- **Hypothesis implied:** *Re-running J46-J49 with explicit slippage (current best-fill assumption + 0.5pt FX, 1pt indices) will reduce the +0.742R/trade lift by 0.05-0.15R, but preserve significance.*
- **Cross-domain links:** 21 (transaction cost sizing).

---

## Section 3 — Recent advances 2020-2025

### Backtest Overfitting in the Machine Learning Era: A Comparison of Out-of-Sample Testing Methods in a Synthetic Controlled Environment
- **Authors / Year:** Arian, H. R., Norouzi, D., & Seco, L. A., 2024
- **Source / URL:** Knowledge-Based Systems, vol. 305. https://www.sciencedirect.com/science/article/abs/pii/S0950705124011110 ; SSRN: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4686376
- **Abstract:** Compares walk-forward, k-fold, purged-CV, and CPCV (plus novel Bagged-CPCV / Adaptive-CPCV variants) under controlled synthetic environments using Heston SV, Merton jump diffusion, drift-burst, and regime-switching simulators. Measures both PBO and DSR.
- **Key findings:**
  - CPCV produces lowest PBO and highest DSR across all tested ML strategies.
  - Walk-forward has highest false-discovery rate due to single-path estimation.
  - Bagged-CPCV improves stability under regime shifts; Adaptive-CPCV adjusts purge/embargo based on detected change-points.
  - Synthetic-environment design isolates the cross-validation effect from data-quirk effects.
- **Relevance to GTOS:** Essentially an empirical-study version of the Lopez de Prado prescription. Direct guidance for K54 v2 design: use CPCV, verify on synthetic environments matching gold/FX dynamics, report PBO + DSR alongside Sharpe.
- **Hypothesis implied:** *Building a regime-shift synthetic environment (matching XAUUSD H2-2026 trending_bull → ranging) and running K54 baseline through CPCV+Bagged-CPCV will rank the variants by PBO; the lowest-PBO variant should be promoted regardless of headline Sharpe.*
- **Cross-domain links:** 19 (ML methodology), 21 (DSR-as-sizing-input).

### The Model Confidence Set
- **Authors / Year:** Hansen, P. R., Lunde, A., & Nason, J. M., 2011
- **Source / URL:** Econometrica, 79(2), 453-497. https://onlinelibrary.wiley.com/doi/abs/10.3982/ECTA5771 ; SSRN: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=522382
- **Abstract:** Generalizes pairwise SPA to a multi-model "confidence set" of best models — analogous to a CI for parameters. Uninformative data → wide MCS containing many models; informative data → narrow MCS with few. Doesn't assume a true model exists.
- **Key findings:**
  - MCS based on EPA (Equal Predictive Ability) test sequence; eliminates inferior models stepwise.
  - Yields a set, not a singleton — appropriate when data cannot resolve which model is best.
  - R package implementation widely available; easy practical adoption.
- **Relevance to GTOS:** Direct application: when comparing 5 K54 hyperparameter configurations or 5 prompt variants, MCS gives the set of "candidates not significantly inferior to the best" — a richer answer than DM-pairwise. The right method when we want to avoid prematurely selecting a winner.
- **Hypothesis implied:** *MCS at 0.10 confidence over the 6 prompt-cascade variants will likely contain ≥3 variants — implying the data does NOT decisively select a single best, contrary to current "v3 cascade is best" framing.*
- **Cross-domain links:** 19 (ML model selection).

### Comparing Predictive Accuracy, Twenty Years Later: A Personal Perspective on the Use and Abuse of Diebold-Mariano Tests
- **Authors / Year:** Diebold, F. X., 2015
- **Source / URL:** Journal of Business & Economic Statistics, 33(1), 1-9. https://www.tandfonline.com/doi/full/10.1080/07350015.2014.983236 ; PDF: https://www.sas.upenn.edu/~fdiebold/papers/paper113/Diebold_DM%20Test.pdf ; NBER: https://www.nber.org/papers/w18391
- **Abstract:** Diebold's reflection on the DM test 20 years later. Emphasizes that DM is for comparing FORECASTS, not MODELS. Cautions against (pseudo-)out-of-sample analysis as a panacea against in-sample overfitting; argues full-sample model-comparison procedures are often simpler and more compelling.
- **Key findings:**
  - DM test for forecasts: still appropriate, widely used.
  - DM test for models: misuse — full-sample-fit + tractable model-comparison better.
  - OOS analysis is NOT inherently superior; it depends on hypothesis being tested.
  - Belief that "pseudo-OOS guards against IS-overfit" is largely false.
- **Relevance to GTOS:** A counterweight to the GTOS lean toward "OOS-only" rigor. Suggests the right framing for K54 is "comparing the K54 forecast vs the AI forecast" not "comparing K54 model vs AI model" — and forecasts can be compared on full-sample DM with proper standard errors.
- **Hypothesis implied:** *Reframing K54-vs-AI as a forecast-comparison (not a model-comparison) and applying full-sample DM with HAC SE will produce more decisive p-values than an OOS walk-forward — and may shift the verdict.*
- **Cross-domain links:** 19.

### A Bayesian Approach to Backtest Overfitting
- **Authors / Year:** Witzany, J., 2017
- **Source / URL:** SSRN: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3002503 ; Journal of Risk Model Validation
- **Abstract:** Proposes Bayesian-MCMC-based estimation of strategy performance metrics with priors over the population of trialed strategies. Yields posterior-corrected Sharpe (and other metric) distributions that account for selection-bias-from-N.
- **Key findings:**
  - Posterior Sharpe distribution accounts for prior on candidate-strategy population.
  - More flexible than DSR's frequentist N-correction (which assumes iid Sharpe under null).
  - MCMC chain provides full posterior, not just point estimate.
- **Relevance to GTOS:** Bayesian alternative to DSR for K54 evaluation. Useful when prior over backtest-population is informative (e.g., we have strong reasons to believe most prompt-variants have small lift around zero).
- **Hypothesis implied:** *Bayesian backtest evaluation (Witzany method) of J46-J49 with informative prior (Sharpe ~ N(0, 0.5)) will produce posterior 95% credible interval for Sharpe-lift that is more conservative than the frequentist DSR.*
- **Cross-domain links:** 19, 21.

### Testing the Predictive Ability of Technical Analysis Using a New Stepwise Test (Stepwise SPA)
- **Authors / Year:** Hsu, P.-H., Hsu, Y.-C., & Kuan, C.-M., 2010
- **Source / URL:** Journal of Empirical Finance, 17(3), 471-484. https://www.sciencedirect.com/science/article/abs/pii/S0927539810000022 ; SSRN: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1087044
- **Abstract:** Extends Hansen's SPA to a stepwise procedure that identifies all individual models with significant outperformance (rather than just testing the best). Strictly more powerful than Romano-Wolf StepM. Applied to technical-trading rules on small/growth indices.
- **Key findings:**
  - Stepwise-SPA controls FWER while identifying multiple superior strategies.
  - Empirical: technical rules significant pre-ETF launch, lose significance post-ETF (efficiency improvement).
  - More powerful than Romano-Wolf StepM in simulations.
- **Relevance to GTOS:** Methodologically very relevant — almost certain that GTOS prompt/setting variations need stepwise-SPA-style assessment, not all-pairs-DM. Also the empirical "post-ETF-decay" pattern parallels the H2-2026 GTOS edge decay.
- **Hypothesis implied:** *Stepwise-SPA over 6 prompt variants × 75 canary fixtures will reveal subset of (variant×fixture-cluster) cells that maintain significance vs noise — informing per-cluster prompt assignment.*
- **Cross-domain links:** 14 (technical trading rules content).

### In-Sample or Out-of-Sample Tests of Predictability: Which One Should We Use?
- **Authors / Year:** Inoue, A., & Kilian, L., 2005
- **Source / URL:** Econometric Reviews, 23(4), 371-402. https://www.tandfonline.com/doi/abs/10.1081/ETC-200040785 ; SSRN: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=369560
- **Abstract:** Argues that the conventional wisdom "OOS tests are more reliable than IS tests" is wrong. IS tests have higher power and the OOS-IS gap can be explained by data-mining bias correction *of OOS itself*, not unique-OOS-virtue.
- **Key findings:**
  - Power: IS tests > OOS tests under the same data-mining discipline.
  - Both tests are subject to data-mining; OOS is NOT a free pass.
  - The widely-held belief in OOS superiority is contested.
- **Relevance to GTOS:** Counterweight to "OOS-purity-fetish" approach in K-series re-tests. Suggests we should adjust IS tests for proper multiple-testing AND retain them — not blindly defer to OOS.
- **Hypothesis implied:** *Re-running F11 (OB zone decay velocity) under IS test with Romano-Wolf correction will produce the same direction (decay) as OOS, but with tighter CIs — corroborating the verdict at lower data cost.*
- **Cross-domain links:** 19.

### Tests of Equal Forecast Accuracy and Encompassing for Nested Models (ENC-NEW + MSE-F)
- **Authors / Year:** Clark, T. E., & McCracken, M. W., 2001
- **Source / URL:** Journal of Econometrics, 105(1), 85-110. https://www.sciencedirect.com/science/article/abs/pii/S0304407601000719 ; PDF: https://www.kansascityfed.org/documents/5266/pdf-rwp99-11.pdf
- **Abstract:** Develops the ENC-NEW (encompassing) test and MSE-F (mean-squared-error F-statistic) for forecast comparison between nested models. Standard DM test breaks under nested-model nulls due to variance-degeneracy; these tests fix that.
- **Key findings:**
  - Nested-model DM is NON-STANDARD: limit distribution depends on Brownian-motion functionals.
  - MSE-F has well-tabulated critical values for nested settings.
  - ENC-NEW tests whether the larger model adds info beyond the smaller — directly meaningful for "does feature X help".
- **Relevance to GTOS:** Critical when comparing K54 (richer, regime-aware) to AI baseline if K54 nests AI features. Naive DM critical values would be wrong; we need MSE-F or ENC-NEW.
- **Hypothesis implied:** *Recomputing K54-vs-AI comparison with MSE-F critical values (rather than naive DM critical values) will widen confidence intervals; the naive DM-style p < 0.001 may become p < 0.10.*
- **Cross-domain links:** 19.

### Asymptotics for Out of Sample Tests of Causality
- **Authors / Year:** McCracken, M. W., 2007
- **Source / URL:** Journal of Econometrics, 140(2), 719-752. https://users.nber.org/~confer/2000/si2000/mccracken.pdf
- **Abstract:** Provides asymptotic null distributions for the MSE-F-statistic under nested-model out-of-sample comparisons. Shows the limit is non-standard (functional of Brownian motion). Tabulates critical values.
- **Key findings:**
  - Critical values depend on sample-split fraction π = R/T.
  - Power increases with π but so does estimation uncertainty.
  - Provides clean inference for the "does adding regime add forecast power" question.
- **Relevance to GTOS:** Companion to Clark-McCracken 2001; gives the actual critical values to use. Direct citation for any K54 nested-comparison.
- **Hypothesis implied:** *Optimal sample-split π for K54 OOS evaluation is approximately 0.5 per McCracken's tables — implying we should hold back ~50% of available trades for OOS, not the conventional 70/30 split.*
- **Cross-domain links:** 19.

### Comparing Possibly Misspecified Forecasts
- **Authors / Year:** Patton, A. J., 2020
- **Source / URL:** Journal of Business & Economic Statistics, 38(4), 796-809. https://www.tandfonline.com/doi/full/10.1080/07350015.2019.1585256 ; PDF: https://public.econ.duke.edu/~ap172/Patton_bregman_comparison_22dec16.pdf
- **Abstract:** Investigates how forecast comparison rankings change under loss-function choice when models may be misspecified. Shows ranking is loss-function-invariant only under correct specification + nested information sets — generally NOT robust.
- **Key findings:**
  - With misspecification, comparison ranking depends on chosen loss function.
  - Bregman-divergence consistent loss family: family-wide ranking holds, but choice within family matters.
  - Recommendation: explicitly specify the operative loss function (PnL, Sharpe, hit-rate, etc.) before comparison.
- **Relevance to GTOS:** Directly addresses the walk-level-vs-realized-R problem (memory `feedback_walk_level_evidence_not_predictive`): different loss functions (walk-AUC vs realized-R) can rank K54 differently, and the relevant loss is realized-R for trading purposes.
- **Hypothesis implied:** *The K54 model that is best under walk-AUC loss is NOT the same model that is best under realized-R loss; Patton's framework predicts ≥30% probability of ranking-flip if the candidate set has ≥5 hyperparameter variants.*
- **Cross-domain links:** 19, 21.

### What to Look for in a Backtest
- **Authors / Year:** Lopez de Prado, M., 2013
- **Source / URL:** SSRN: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2308682
- **Abstract:** Practitioner checklist of red flags in research backtests. Catalogs survivorship bias, look-ahead, data-mining, transaction-cost realism, and pseudo-stationarity assumptions. Sets a quality bar for vendor / counterparty backtest reports.
- **Key findings:**
  - Most published-paper backtests omit ≥3 of the canonical sins.
  - Sharpe + max-drawdown + Calmar are the minimum-required metrics.
  - PBO ≥ 0.5 → backtest results are random noise.
- **Relevance to GTOS:** Direct quality-bar reference for any internal research artifact (J/K/H series). Pre-flight checklist for "is this finding promotion-worthy?"
- **Hypothesis implied:** *Auditing the J46-J49 portfolio backtest under Lopez de Prado's checklist will reveal ≥1 silent sin (likely look-ahead in TP1 immediate-BE rule, or transaction-cost gap) — necessitating recompute.*
- **Cross-domain links:** none.

### The Sharpe Ratio Efficient Frontier (Probabilistic Sharpe Ratio)
- **Authors / Year:** Bailey, D. H., & Lopez de Prado, M., 2012
- **Source / URL:** Journal of Risk, 15(2), 3-44. SSRN: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1821643 ; PDF: https://www.davidhbailey.com/dhbpapers/sharpe-frontier.pdf
- **Abstract:** Introduces the Probabilistic Sharpe Ratio (PSR), the probability that the true SR exceeds a benchmark threshold given sample length and first four moments of returns. Defines Minimum Track Record Length (MinTRL): the months/years required to confidently reject a SR floor.
- **Key findings:**
  - PSR formula: Φ((SR̂ - SR*) × √(N-1) / sqrt(1 - γ̂₃ × SR̂ + (γ̂₄-1)/4 × SR̂²)).
  - Negative skewness + positive excess kurtosis dramatically inflate MinTRL.
  - For a typical high-Sharpe (1.5) trading strategy with skew = -1, kurt = 5, MinTRL > 5 years.
- **Relevance to GTOS:** Computing PSR + MinTRL on each instrument's live track record (XAUUSD, US30, USDJPY) tells us which "edge" claims are supported by the data and which need more time. Companion to deflated SR for single-strategy assessment.
- **Hypothesis implied:** *XAUUSD H2-2026 LONG performance computed under PSR with skewness/kurtosis adjustments will produce P(SR>0) < 0.50 — corroborating the SPRT halt rule's underlying trigger condition.*
- **Cross-domain links:** 21.

### Replicating Anomalies
- **Authors / Year:** Hou, K., Xue, C., & Zhang, L., 2020
- **Source / URL:** Review of Financial Studies, 33(5), 2019-2133. https://global-q.org/uploads/1/2/2/6/122679606/houxuezhang2020rfs.pdf ; SSRN: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2961979
- **Abstract:** Replicates 452 published cross-sectional anomalies under disciplined methodology (NYSE breakpoints, value-weighted returns). 65% fail at t > 1.96; 82% fail at multiple-testing-corrected t > 2.78. Microcaps drove much of the original "significance".
- **Key findings:**
  - 65% of anomalies fail single-test threshold.
  - 82% fail multiple-testing-corrected threshold.
  - Microcaps over-weighting was a methodological-not-real source of significance.
  - Trading-frictions category fares worst (96% fail).
- **Relevance to GTOS:** Empirical illustration of multiple-testing-correction-via-Harvey-Liu-Zhu in action. The pattern (small-stock-bias as silent inflator) parallels GTOS's small-bin-bias risk in regime-conditioned cells (e.g., F2 small-n trending_bull cells).
- **Hypothesis implied:** *The pattern of cross-sectional-anomaly-replication failure (≥80%) suggests our analogous regime-cell-significance claims will see similar failure rates if rigorous replication is applied — argues for Phase 2 emphasis on replication audits over new feature exploration.*
- **Cross-domain links:** 13, 22.

### Open Source Cross-Sectional Asset Pricing
- **Authors / Year:** Chen, A. Y., & Zimmermann, T., 2022
- **Source / URL:** Critical Finance Review, 27(2), 207-264. https://www.openassetpricing.com/ ; SSRN: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3604626 ; PDF: https://www.federalreserve.gov/econres/feds/files/2021-037pap.pdf
- **Abstract:** Reconciliation paper to Hou-Xue-Zhang (2020). Replicates 319 predictors with both stock-level signals and portfolio implementations. Of the 161 originally-significant signals, 98% replicate at t > 1.96 — much more optimistic than HXZ.
- **Key findings:**
  - Replication regression of reproduced t-stats on original t-stats: slope 0.88, R² 82% — most signals are real.
  - The discrepancy with HXZ is largely about microcap weighting and value-vs-equal weight conventions.
  - Open-source pipelines lower the cost of empirical replication audits.
- **Relevance to GTOS:** Suggests the "anomaly replication crisis" is partially methodological-disagreement, not pure noise. The methodological choice (e.g., regime cell filter, sample-size threshold) does substantively affect the reported significance rate.
- **Hypothesis implied:** *Methodological choices (cell-min-n, regime-classifier-version) explain ≥30% of variance in apparent decay-rate of GTOS edges across re-tests; documenting and standardizing methodology is a higher-leverage Phase 2 intervention than new-feature exploration.*
- **Cross-domain links:** 13, 22.

### A Note on the Validity of Cross-Validation for Evaluating Autoregressive Time Series Prediction
- **Authors / Year:** Bergmeir, C., Hyndman, R. J., & Koo, B., 2018
- **Source / URL:** Computational Statistics & Data Analysis, 120, 70-83. https://www.sciencedirect.com/science/article/abs/pii/S0167947317302384 ; PDF: https://robjhyndman.com/papers/cv-wp.pdf
- **Abstract:** Shows that, for purely-autoregressive models with uncorrelated residuals, standard k-fold CV is theoretically valid (contra widespread belief). Provides theoretical + simulation evidence and explains when k-fold breaks: when residuals are correlated.
- **Key findings:**
  - Pure AR models with white-noise residuals: k-fold CV is valid (mild conditions).
  - When models nest a more-appropriate model: k-fold appropriate.
  - When residuals are autocorrelated: must use purged-CV or walk-forward.
  - K-fold has higher power than non-dependent-CV in the valid setting.
- **Relevance to GTOS:** Counterweight to the "always use CPCV" heuristic. If K54 features are purely-historical (no overlap, no spilling labels), simpler k-fold may be valid AND more powerful. Test before defaulting to CPCV.
- **Hypothesis implied:** *Residual-autocorrelation diagnostic on K54 LightGBM training set will reveal pattern: low autocorr → k-fold valid (use it for power); high → CPCV mandatory.*
- **Cross-domain links:** 19.

### Rolling Window Selection for Out-of-Sample Forecasting with Time-Varying Parameters
- **Authors / Year:** Inoue, A., Jin, L., & Rossi, B., 2017
- **Source / URL:** Journal of Econometrics, 196(1), 55-67. https://www.sciencedirect.com/science/article/abs/pii/S0304407616301713 ; PDF: https://www.crei.cat/wp-content/uploads/users/working-papers/InoueLuRossi.pdf
- **Abstract:** Proposes a method for choosing the rolling-window size in out-of-sample forecasting under time-varying-parameter (TVP) data. Frames as a bias-variance tradeoff (analogous to bandwidth selection in nonparametric estimation).
- **Key findings:**
  - Optimal window minimizes asymptotic forecast MSE.
  - Under TVP, optimal window is finite (don't keep expanding).
  - Empirically improves output-growth forecasts vs naive split.
- **Relevance to GTOS:** Direct relevance to the "how much history should we use to fit K54?" question under regime decay (item #4). With v1 detector ≠ v2 detector + regime-conditioning, parameters are time-varying.
- **Hypothesis implied:** *Optimal rolling-window-size for K54 under regime decay is approximately 60-90 days (3-4 trading-months), not the 6+ months currently used — improving K54's ability to track H2-2026 dynamics.*
- **Cross-domain links:** 19.

### Evaluating Interval Forecasts (Christoffersen)
- **Authors / Year:** Christoffersen, P. F., 1998
- **Source / URL:** International Economic Review, 39(4), 841-862. https://users.ssc.wisc.edu/~behansen/718/Christoffersen1998.pdf
- **Abstract:** Develops likelihood-ratio tests for interval-forecast (and VaR) coverage. Decomposes "correct conditional coverage" into "unconditional coverage" + "independence-of-violations" — the canonical VaR-backtest framework.
- **Key findings:**
  - LRuc tests if hits/(N) ≈ α (unconditional coverage).
  - LRind tests if hits are independent across t.
  - Combined LRcc tests both jointly — this is the right test for VaR adequacy.
- **Relevance to GTOS:** Direct framework for backtesting GTOS's TP/SL coverage claims. If we claim "stop-loss hits at α=10% rate", LRuc + LRind on real trades gives the test. Generalizes to any interval-forecast made by Component 3A.
- **Hypothesis implied:** *Christoffersen LRcc on the empirical hit-rate of AI-emitted SL across closed trades will reject independence (LRind significant) under H2-2026 — implying SL violations are clustered (consecutive losing trades), which calls for time-stop or volatility-aware SL adjustments.*
- **Cross-domain links:** 16 (VaR-as-volatility-trading), 21 (SL-sizing).

### The Probabilistic Sharpe Ratio for the Difference of Sharpe Ratios
- **Authors / Year:** Wright, J., Yam, S. C. P., & Yung, S. P., 2014 (extension); Bailey-Lopez de Prado original 2012/2014
- **Source / URL:** PortfolioOptimizer blog summary: https://portfoliooptimizer.io/blog/the-probabilistic-sharpe-ratio-hypothesis-testing-and-minimum-track-record-length-for-the-difference-of-sharpe-ratios/ ; closely related paper: Wright et al. (2014) https://arxiv.org/abs/1407.7253
- **Abstract:** Generalizes PSR to the question "is strategy A's Sharpe statistically higher than strategy B's?" Critical when comparing competing trading strategies under non-normal returns.
- **Key findings:**
  - Difference-of-Sharpe distribution depends on covariance of strategies' returns.
  - MinTRL for difference is typically much longer than for level.
  - Can incorporate higher-moment differences in returns.
- **Relevance to GTOS:** Right test for "is K54 Sharpe higher than current AI gate Sharpe?" — accounts for paired structure of returns.
- **Hypothesis implied:** *MinTRL for K54-vs-AI Sharpe difference will exceed 12 months at the 95% confidence level — implying current K54 baseline (n=321 trades) is below MinTRL and the verdict MARGINAL_WITH_PRACTICAL_LIFT is appropriate.*
- **Cross-domain links:** 21.

---

## Section 4 — Methodological tools

### Robust Performance Hypothesis Testing with the Sharpe Ratio (HAC + Bootstrap)
- **Authors / Year:** Ledoit, O., & Wolf, M., 2008
- **Source / URL:** Journal of Empirical Finance, 15(5), 850-859. https://www.sciencedirect.com/science/article/abs/pii/S0927539808000182 ; PDF: https://www.econ.uzh.ch/apps/workingpapers/wp/iewwp320.pdf
- **Abstract:** Proposes studentized circular-block-bootstrap inference for Sharpe-ratio differences when returns are non-iid. Robust to serial correlation, fat tails, conditional heteroskedasticity. Strict improvement over Lo (2002) HAC asymptotic-only.
- **Key findings:**
  - Studentized bootstrap captures finite-sample distribution of paired-Sharpe-difference test.
  - HAC asymptotic CIs systematically under-cover under realistic dependence.
  - Bootstrap CIs cover at nominal rate even at moderate n.
- **Relevance to GTOS:** Right test for paired-Sharpe-difference comparison (e.g., portfolio with vs without K54 gate; XAUUSD H1 vs H2 Sharpe). Trade-by-trade dependence in GTOS PnL violates iid; this method handles it.
- **Hypothesis implied:** *Ledoit-Wolf studentized-bootstrap test on H1-2026 vs H2-2026 XAUUSD Sharpe difference will yield wider CI than naive HAC — possibly removing significance of the implied decay magnitude (corroborates F11's finding that decay is not universal).*
- **Cross-domain links:** 21.

### A Forecast Comparison of Volatility Models: Does Anything Beat a GARCH(1,1)?
- **Authors / Year:** Hansen, P. R., & Lunde, A., 2005
- **Source / URL:** Journal of Applied Econometrics, 20(7), 873-889. https://onlinelibrary.wiley.com/doi/abs/10.1002/jae.800 ; SSRN: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=264571
- **Abstract:** Compares 330 ARCH-type volatility models on DM/$ exchange rate and IBM returns using SPA test. Finds nothing significantly beats GARCH(1,1) for FX vol; for equities, leverage-effect models beat GARCH(1,1).
- **Key findings:**
  - Multiple-testing-corrected Sharpe-of-vol-forecast: GARCH(1,1) holds its own remarkably well.
  - Leverage matters for equities, less so for FX.
  - Empirical demonstration of SPA test in vol-forecasting context.
- **Relevance to GTOS:** Methodological example of large-N model comparison done correctly. Also directly relevant: GARCH(1,1) is the workhorse for any GTOS volatility-aware sizing or stop-distance calibration.
- **Hypothesis implied:** *Comparing GTOS H25 session-volatility-monitor metrics against GARCH(1,1) baseline using SPA over the 6 instruments will reveal at most 1-2 instruments where H25 dominates — suggesting GARCH should remain default, with H25 as a flag-not-gate.*
- **Cross-domain links:** 03 (vol-forecast content), 16 (vol-trading), 19.

### Realized GARCH: A Joint Model for Returns and Realized Measures of Volatility
- **Authors / Year:** Hansen, P. R., Huang, Z., & Shek, H. H., 2012
- **Source / URL:** Journal of Applied Econometrics, 27(6), 877-906. https://onlinelibrary.wiley.com/doi/abs/10.1002/jae.1234
- **Abstract:** Joint model that incorporates realized-volatility measures (intraday-based) into the GARCH conditional-variance equation. Substantially improves vol-forecast accuracy over standard GARCH(1,1).
- **Key findings:**
  - Realized measure constrains the conditional-variance update, reducing forecast error.
  - Better empirical fit on equity returns; consistent OOS gains.
  - Bridges low-frequency-GARCH and high-frequency-realized-volatility literatures.
- **Relevance to GTOS:** Methodology for incorporating intraday tick data (already captured in `data/ticks/{SYMBOL}/*.parquet`) into volatility-aware sizing or SL-distance gates.
- **Hypothesis implied:** *Realized-GARCH conditional-variance from M1 ticks will improve next-bar realized-vol forecasts by ≥20% MSE-reduction vs GARCH(1,1) on M15 close — useful as a vol-floor for the SL_buffer_atr_multiplier.*
- **Cross-domain links:** 03, 16.

### Recent Developments in Bootstrap Methods for Dependent Data
- **Authors / Year:** Cavaliere, G., 2015
- **Source / URL:** Journal of Time Series Analysis, 36(2), 154-201. https://onlinelibrary.wiley.com/doi/10.1111/jtsa.12128
- **Abstract:** Comprehensive review of bootstrap methods for dependent data: block bootstrap, stationary bootstrap, sieve bootstrap, frequency-domain bootstrap, dependent wild bootstrap. Decision tree for which method fits which dependence structure.
- **Key findings:**
  - For weakly-dependent stationary data: stationary bootstrap (Politis-Romano) is workhorse.
  - For long-memory or unit-root data: subsampling or frequency-domain.
  - Dependent wild bootstrap (Shao 2010) easy to implement, broad applicability.
- **Relevance to GTOS:** Methodological handbook for choosing bootstrap method for any backtest CI. Don't blindly apply iid; pick the right method.
- **Hypothesis implied:** *Stationary bootstrap is the right method for GTOS trade-by-trade PnL bootstrap; for OB-touch-event clustered analysis, dependent wild bootstrap (Shao 2010) handles within-cluster correlation.*
- **Cross-domain links:** 19.

### Sequential Change-Point Detection: Computation versus Statistical Performance
- **Authors / Year:** Wang, T., 2024
- **Source / URL:** WIREs Computational Statistics. https://wires.onlinelibrary.wiley.com/doi/abs/10.1002/wics.1628 ; arXiv: https://arxiv.org/pdf/2210.05181
- **Abstract:** Modern review of online change-point detection (CPD) methods. Compares CUSUM, GLR, Bayesian online CPD, e-detectors. Survey of computational vs statistical-performance tradeoffs.
- **Key findings:**
  - For low-latency requirements: CUSUM with optimal-stopping rule.
  - For unknown change-point distribution: e-detectors (Vovk-Wang) provably valid under arbitrary dependence.
  - Bayesian online CPD provides uncertainty quantification at higher computational cost.
- **Relevance to GTOS:** Modern menu of CPD methods for the live decay-monitor. Currently using rolling-50 + threshold; could upgrade to e-detector for stronger guarantees.
- **Hypothesis implied:** *E-detector replacement of the rolling-50 OB-continuation alarm will provide validity under arbitrary serial dependence and may reduce false-alarm rate by ≥30%.*
- **Cross-domain links:** 05.

### Empirical Properties of Asset Returns: Stylized Facts and Statistical Issues
- **Authors / Year:** Cont, R., 2001
- **Source / URL:** Quantitative Finance, 1(2), 223-236. https://www.tandfonline.com/doi/abs/10.1080/713665670 ; PDF: http://rama.cont.perso.math.cnrs.fr/pdf/empirical.pdf
- **Abstract:** Catalogs ~11 universal stylized facts of asset returns: heavy tails, no autocorrelation in returns, slow decay of |returns| autocorrelation (volatility clustering), aggregational Gaussianity, leverage effect, etc. Sets methodological constraints for any candidate model.
- **Key findings:**
  - Return distribution: power-law tails (α ~ 3-5).
  - Returns ACF: indistinguishable from zero except for very-short lags.
  - |Returns|² and |Returns| ACF: slow polynomial decay (long memory).
  - Volatility clustering universal.
- **Relevance to GTOS:** Methodology constraint: any GTOS forecast / backtest / simulation must respect these stylized facts. Cont's list is the validation checklist for synthetic-environment designs (e.g., for CPCV evaluation).
- **Hypothesis implied:** *Synthetic-environment used in K54 CPCV evaluation should be tested against Cont's 11 stylized facts; if it fails ≥3, the synthetic results may not generalize to live (e.g., heavy-tail Sharpe deflation may be under-stated).*
- **Cross-domain links:** 03 (canonical 03), but methodology angle keeps cross-link here.

### Evidence on Structural Instability in Macroeconomic Time Series Relations
- **Authors / Year:** Stock, J. H., & Watson, M. W., 1996
- **Source / URL:** Journal of Business & Economic Statistics, 14(1), 11-30. https://www.princeton.edu/~mwatson/papers/Stock_Watson_JBES_1996.pdf
- **Abstract:** Empirical examination of structural-stability tests on 76 US macro series, 8 categories. Substantial fraction of univariate AR and bivariate models exhibit parameter instability; adaptive methods (TVP, regime-switching) recover some lost forecasting power.
- **Key findings:**
  - Most macro relationships are unstable over time at multi-decade horizons.
  - TVP / regime-switching models capture significant share of instability.
  - Out-of-sample forecasting power is bounded by parameter instability — one of the few mechanisms behind real-world OOS-IS gap.
- **Relevance to GTOS:** Empirical foundation for our edge-decay framing. The H1→H2 GTOS shift is exactly the parameter-instability they document. Their adaptive-methods recommendation = our regime-aware K54 pipeline.
- **Hypothesis implied:** *Applying Stock-Watson stability tests on the 25 monthly Sharpe figures of XAUUSD's GTOS strategy will detect a structural break at 2026-Q1 — formalizing what F11/F15 found qualitatively.*
- **Cross-domain links:** 05 (regime-shift / structural break).

### Predictive Likelihood Comparisons with DSGE Models (Bayesian Predictive Checks)
- **Authors / Year:** Herbst, E. P., & Schorfheide, F., 2012 (reference paper); Lopes (2014) https://www.ecb.europa.eu/pub/pdf/scpwps/ecbwp1536.pdf for predictive-likelihood discussion
- **Source / URL:** Working paper / book (Bayesian Estimation of DSGE Models, 2016): https://www.philadelphiafed.org/-/media/frbp/assets/working-papers/2012/wp12-4.pdf ; companion: https://web.sas.upenn.edu/schorf/companion-web-site-bayesian-estimation-of-dsge-models/
- **Abstract:** Develops Bayesian predictive-check methodology for DSGE models. Predictive likelihood used to compare nested + non-nested forecasting models with rigorous accounting for parameter uncertainty.
- **Key findings:**
  - Predictive likelihood naturally handles parameter uncertainty (unlike point-estimate-based DM).
  - Marginal likelihood ratio = full posterior model probability ratio.
  - Predictive checks: simulate forecasts from posterior, compare distribution to observed.
- **Relevance to GTOS:** Bayesian alternative for K54 vs AI comparison. Posterior-predictive checks are the right diagnostic for "is the AI's forecast distribution adequate?" — directly addresses the F8 finding (decay in calibration, not perception).
- **Hypothesis implied:** *Posterior-predictive check on AI's emitted-TP-price distribution (vs realized TP) will fail conditional-coverage at H2-2026 — quantifying the calibration-decay mechanism.*
- **Cross-domain links:** 19, 18.

### Data-Snooping, Technical Trading Rule Performance, and the Bootstrap
- **Authors / Year:** Sullivan, R., Timmermann, A., & White, H., 1999
- **Source / URL:** Journal of Finance, 54(5), 1647-1691. https://onlinelibrary.wiley.com/doi/abs/10.1111/0022-1082.00163 ; SSRN: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=160330
- **Abstract:** Re-evaluation of Brock-Lakonishok-LeBaron (1992) under White's Reality Check across 7,846 trading rules on 100 years of DJIA data. Finds the BLL "trading rules profitable" claim is sensitive to data-snooping but partially survives.
- **Key findings:**
  - Best rule passed Reality Check pre-1986; failed for post-1986 OOS data.
  - Rules sensitive to subsample selection.
  - 7,846-rule universe → required Reality Check, single-rule-test would have grossly overstated significance.
- **Relevance to GTOS:** Empirical analogue of GTOS edge-decay over time, with proper multiple-testing discipline. Provides historical precedent for "edges that survive in-sample but fade after publication / OOS."
- **Hypothesis implied:** *GTOS-edge OOS H2-2026 will fail Reality Check at p < 0.10 against the 75-canary-fixture multiverse — suggesting the H2 collapse is large-enough that even properly-corrected pre-2026 in-sample edge cannot rescue it.*
- **Cross-domain links:** 14, 22.

### Simple Technical Trading Rules and the Stochastic Properties of Stock Returns
- **Authors / Year:** Brock, W., Lakonishok, J., & LeBaron, B., 1992
- **Source / URL:** Journal of Finance, 47(5), 1731-1764. https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.1992.tb04681.x ; PDF: https://finance.martinsewell.com/stylized-facts/distribution/BrockLakonishokLeBaron1992.pdf
- **Abstract:** Pioneering paper applying bootstrap methodology to evaluate technical trading rules. Tests MA + trading-range-break rules on Dow Jones 1897-1986. Returns inconsistent with random-walk, AR(1), GARCH-M, and EGARCH null models.
- **Key findings:**
  - Bootstrap confirms statistical significance of technical-trading-rule returns above random-walk null.
  - Used parametric residual-resampling bootstrap.
  - Did NOT correct for data-snooping across rules — Sullivan-Timmermann-White (1999) addressed this and found significance fragile.
- **Relevance to GTOS:** Cited as methodological precedent for "bootstrap-based trading-rule evaluation." Failure mode (no multiple-testing) is a cautionary tale.
- **Hypothesis implied:** *Re-running BLL-style bootstrap-trading-rule evaluation on a 4-rule subset (BLL's preferred set) WITH multiple-testing correction (Reality Check / SPA) will reduce significance from BLL's headline-positive to ambiguous — replicating the Sullivan-Timmermann-White result and reinforcing the methodology lesson.*
- **Cross-domain links:** 14.

### Consistent Ranking of Volatility Models
- **Authors / Year:** Hansen, P. R., & Lunde, A., 2006
- **Source / URL:** Journal of Econometrics, 131(1-2), 97-121. https://www.sciencedirect.com/science/article/abs/pii/S0304407605000072
- **Abstract:** Establishes necessary + sufficient conditions on the loss function for vol-forecast ranking to be robust to noise in the volatility proxy. Distortions vary greatly with loss-function choice; the "robust" family is infinite but constrained.
- **Key findings:**
  - Naive RMSE-on-realized-vol can flip the ranking due to proxy noise — sometimes severely.
  - Robust loss family includes MSE-on-log-vol and the Patton-2011 robust loss family.
  - Practical guidance: use MSE-of-log-RV or QLIKE.
- **Relevance to GTOS:** Direct applicability when comparing vol-forecasts (GARCH vs realized-GARCH vs naive lagged-vol) for sizing or SL-distance calibration. The wrong loss function can mis-rank our candidates.
- **Hypothesis implied:** *Comparing GARCH(1,1) vs Realized-GARCH on M15-vol for the 7 instruments under MSE-of-log-RV (robust) vs naive RMSE will produce different rankings for at least 2 instruments — informing the loss-function choice for any future vol-forecast experiments.*
- **Cross-domain links:** 03, 16.

### Volatility Forecast Comparison Using Imperfect Volatility Proxies
- **Authors / Year:** Patton, A. J., 2011
- **Source / URL:** Journal of Econometrics, 160(1), 246-256. https://www.sciencedirect.com/science/article/abs/pii/S030440761000076X ; PDF: https://public.econ.duke.edu/~ap172/Patton_robust_forecast_eval_11dec08.pdf
- **Abstract:** Constructs robust loss functions for forecast comparison when volatility is observed only with noise. Proves that QLIKE is asymptotically robust, MSE-on-log is robust under specific conditions, and most other loss functions are not.
- **Key findings:**
  - QLIKE (= log(σ̂²/σ²) + σ²/σ̂² - 1) is robust to proxy noise.
  - MSE on log-volatility is robust under finite-sample-corrections.
  - Heteroskedasticity-robust DM with QLIKE is the right framework.
- **Relevance to GTOS:** Same as Hansen-Lunde 2006 above; cited as the canonical guide for vol-forecast loss function choice in GTOS.
- **Hypothesis implied:** *QLIKE-based DM-test on H25 session-volatility-monitor vs naive lagged-volatility will yield decisive ranking even for low-N M15 samples; should be standard test in any future vol-comparison work.*
- **Cross-domain links:** 03, 16.

### The False Strategy Theorem
- **Authors / Year:** Lopez de Prado, M., & Bailey, D. H., 2018
- **Source / URL:** SSRN: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3221798 ; American Mathematical Monthly via X post: https://x.com/lopezdeprado/status/1456938378423844866
- **Abstract:** Formalizes the result that with enough trials, any in-sample Sharpe is achievable on noise. Provides the analytic upper bound E[max IS-Sharpe over N trials | true SR=0] = √(2 ln N). Companion to Bailey-Lopez de Prado-Borwein-Zhu (2014).
- **Key findings:**
  - Theorem: with N independent trials, expected max IS-Sharpe under noise grows like √(2 ln N).
  - Practical: 1000 trials → expected max IS-Sharpe ≈ 3.7 — even on pure noise.
  - Without N reporting, IS-Sharpe alone is meaningless.
- **Relevance to GTOS:** Citation backbone for "always report N alongside any best-of-trial Sharpe / R-multiple lift." Applies to canary-fixture-best, prompt-cascade-best, K54-best-hyperparameter.
- **Hypothesis implied:** *Cumulative GTOS prompt + config trial count is approximately N=200; theoretical noise ceiling for IS-Sharpe is √(2 ln 200) ≈ 3.27 — any apparent IS-Sharpe-of-best-strategy below this is statistically attributable to chance alone.*
- **Cross-domain links:** none.

### Detection of False Investment Strategies Using Unsupervised Learning
- **Authors / Year:** Lopez de Prado, M., & Lewis, M. J., 2018
- **Source / URL:** SSRN: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3167017 ; PDF: https://codemacher.com/wp-content/uploads/2021/02/Detection-of-false-investment-strategies-using-unsupervised-learning-methods_M.LopezDePrado_and_M.Lewis_2018.pdf
- **Abstract:** Uses Optimal Number of Clusters (ONC) clustering to identify highly-similar strategies in a backtest population. Reduces effective N for multiple-testing correction by clustering near-duplicates. Critical when many "different" strategy variants are in fact correlated.
- **Key findings:**
  - Naive N-correction (DSR with N = trial count) over-deflates when strategies are correlated.
  - ONC clustering yields effective-N typically 0.3-0.5 × literal N.
  - Correlation-aware DSR is much more powerful.
- **Relevance to GTOS:** Direct method for measuring effective-N across the GTOS prompt-cascade and K54-hyperparameter populations. Likely current literal N (≥100) collapses to effective N (≈30-40) under correlation analysis.
- **Hypothesis implied:** *Clustering the 6 prompt-cascade variants by their cosine-similarity on canary-fixture-output will reveal effective N ≈ 3-4 (not 6) — making DSR less brutal but still binding.*
- **Cross-domain links:** 19.

### Lucky Factors
- **Authors / Year:** Harvey, C. R., & Liu, Y., 2021 (JFE; SSRN 2015 working paper)
- **Source / URL:** Journal of Financial Economics, 141(2), 413-435. https://www.sciencedirect.com/science/article/abs/pii/S0304405X21001410 ; SSRN: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2528780 ; PDF: https://people.duke.edu/~charvey/Research/Published_Papers/P146_Lucky_factors.pdf
- **Abstract:** Develops a multiple-testing framework for factor selection that explicitly accounts for cross-correlation among test statistics. Bootstrap-based; controls FWER and FDR. Quantifies the "luck" component in apparent factor significance.
- **Key findings:**
  - Naive Bonferroni is over-conservative when factors are correlated.
  - Bootstrap-based correlation-aware correction is much more powerful.
  - Many published factors fail under proper correction; new t-thresholds for each cumulative-trial-count.
- **Relevance to GTOS:** The methodologically-rigorous companion to Harvey-Liu-Zhu 2016. Right method for the K-series feature-importance tests, which have correlated test statistics.
- **Hypothesis implied:** *Applying Lucky-Factors method to the 12 K-series features (with full pairwise-correlation matrix) will yield ≥3 features that are "lucky" (would clear naive threshold but fail correlation-aware correction) — informing K54 feature selection.*
- **Cross-domain links:** 13, 19.

### False (and Missed) Discoveries in Financial Economics
- **Authors / Year:** Harvey, C. R., & Liu, Y., 2020
- **Source / URL:** SSRN: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3073799
- **Abstract:** Quantifies both Type I errors (false discoveries) AND Type II errors (missed discoveries) in factor research. Argues research has been overly focused on Type I (publishing false factors) and neglecting Type II (missing real factors due to over-conservative thresholds).
- **Key findings:**
  - Optimal-power-correction approaches give different threshold tradeoffs than pure-FWER.
  - Many "rejected" factors are likely real but underpowered.
  - The optimal multiple-testing correction depends on prior over true-factor-distribution.
- **Relevance to GTOS:** Direct relevance to F11 / F15 framework: a "decay" detection that fails Bonferroni-corrected p < 0.05 might still be a real signal we're missing. We should track Type II decisions, not just Type I.
- **Hypothesis implied:** *Computing Type-II error rate alongside Type-I for the K-series tests will reveal that ~30% of "decay-not-significant" findings are likely real but under-powered — calling for either larger samples or pre-registered combinations.*
- **Cross-domain links:** 13, 22.

### Does Academic Research Destroy Stock Return Predictability?
- **Authors / Year:** McLean, R. D., & Pontiff, J., 2016
- **Source / URL:** Journal of Finance, 71(1), 5-32. https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.12365 ; SSRN: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2156623
- **Abstract:** Quantifies post-publication decay in 97 cross-sectional return predictors. Out-of-sample returns are 26% lower; post-publication returns are 58% lower. Decomposes 26% into "data-mining bias" and 32% additional into "investor learning / arb."
- **Key findings:**
  - Predictability decays by ~58% after publication.
  - 26% is data-snooping bias (would happen even without publication).
  - 32% is publication / arbitrage effect.
  - Statistical-decay literature foundational reference.
- **Relevance to GTOS:** Empirical analogue / pace-setter for our edge-decay observations. Suggests we should track "post-deployment-decay" as a metric. Also: frames the "32% publication-effect" as a specific mechanism that doesn't apply to private signals.
- **Hypothesis implied:** *GTOS XAUUSD H1→H2 decay (~38pp drop in WR) is much larger than the McLean-Pontiff industry-norm 58% relative decay — implying our decay has a regime-specific component on top of generic "edge-publication" decay.*
- **Cross-domain links:** 13, 22, 17.

### Engle 1982 — Autoregressive Conditional Heteroskedasticity
- **Authors / Year:** Engle, R. F., 1982
- **Source / URL:** Econometrica, 50(4), 987-1007. https://www.econometricsociety.org/publications/econometrica/1982/07/01/autoregressive-conditional-heteroscedasticity-estimates
- **Abstract:** Foundational paper introducing ARCH model and the LM-test for ARCH effects (squared-residuals serial autocorrelation). Cornerstone of the volatility-modeling literature, with downstream impact on backtest realism.
- **Key findings:**
  - LM(q): regress squared-residuals on q lags; T × R² ~ χ²(q) under no-ARCH null.
  - Returns are conditionally heteroskedastic; OLS-based forecasts under-state vol-forecast-error.
  - Methodologically: any "stationarity" assumption in finance backtests must consider ARCH effects.
- **Relevance to GTOS:** Pre-flight diagnostic for any GTOS time-series modeling. ARCH effects in PnL invalidate the iid bootstrap; signals stationary-bootstrap or block-bootstrap.
- **Hypothesis implied:** *LM-test on GTOS daily-PnL squared-residuals will be highly significant — confirming ARCH effects in our PnL stream, and necessitating ARCH-aware bootstrap for any CI.*
- **Cross-domain links:** 03, 16.

---

## Section 5 — Contrarian / under-cited findings

### Empirical Asset Pricing via Machine Learning
- **Authors / Year:** Gu, S., Kelly, B., & Xiu, D., 2020
- **Source / URL:** Review of Financial Studies, 33(5), 2223-2273. https://academic.oup.com/rfs/article/33/5/2223/5758276 ; SSRN: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3159577 ; NBER: https://www.nber.org/papers/w25398
- **Abstract:** Comparative ML asset-pricing study using 60 years of US stock data + 94 firm characteristics. Trees + neural networks dominate linear methods; double the OOS Sharpe of leading regressions. Methodology: rigorous walk-forward validation with strict OOS protocols.
- **Key findings:**
  - Trees + NNs capture nonlinear interactions linear methods cannot.
  - All methods agree on dominant signals: momentum, liquidity, volatility.
  - Strict walk-forward with parameter retraining is the right benchmark.
  - "ML doubles regression performance" — but methodologically because of nonlinearity, not magic.
- **Relevance to GTOS:** Cited as direct precedent for K54 LightGBM (a tree-method) — same methodology family. Provides validated walk-forward protocol GTOS can adopt. Contrarian aspect: the 60% of variance-explained is mostly liquidity / momentum / vol — not exotic features. Argues for keeping K54 feature set lean.
- **Hypothesis implied:** *K54's strongest predictive features should align with Gu-Kelly-Xiu's "momentum + liquidity + volatility" trinity, not exotic ICT-specific features. If our K-series highlights instead structural features like OB-touch, that's a finding worth scrutinizing for confirmation bias.*
- **Cross-domain links:** 13, 19.

### Family-wise Error Rate Control with E-values
- **Authors / Year:** Wang, R., & Ramdas, A., 2025 (arXiv 2025); plus prior Vovk-Wang 2021-2024
- **Source / URL:** arXiv: https://arxiv.org/pdf/2501.09015 ; review by Wang: https://sas.uwaterloo.ca/~wang/files/e-review.pdf ; Vovk 2024: https://onlinelibrary.wiley.com/doi/full/10.1002/cjs.11833
- **Abstract:** Develops e-values + e-processes as a non-classical alternative to p-values for sequential / multiple testing. E-values are anytime-valid: combinable across time without inflated Type I. Critical for online monitoring without prespecified stopping.
- **Key findings:**
  - E-process: any-time-valid sequence; product of independent/sequential e-values is an e-value.
  - E-Holm and similar procedures provide FWER control with no fixed-α requirement.
  - Practical: monitoring stream of evidence without pre-specified n.
- **Relevance to GTOS:** The right framework for live SPRT-like halt rules without pre-specifying when to stop. Currently our SPRT halt rules require fixed-α; e-process variants would let us continue monitoring beyond initial stopping decision.
- **Hypothesis implied:** *Replacing the SPRT halt rule for XAUUSD LONG with an e-process detector will allow continued evidence accrual without alpha-inflation, providing finer-grained live decision support.*
- **Cross-domain links:** 05.

### Bootstrap Methods for Out-of-Sample Predictions in Cross-Validation
- **Authors / Year:** Jiang, W., & Simon, R., 2007 (PMC); Bates et al. 2024 (CV uncertainty)
- **Source / URL:** PMC bootstrapping cross-validation: https://pmc.ncbi.nlm.nih.gov/articles/PMC6191021/ ; Springer: https://link.springer.com/article/10.1007/s10994-018-5714-4
- **Abstract:** Develops bootstrap-CI on cross-validation predictions. Decomposes CV-MSE uncertainty into prediction-noise + train-set-randomness components. Provides better-calibrated CIs for CV metrics.
- **Key findings:**
  - Naive CV-Sharpe / CV-MSE has wider CI than typically reported.
  - Bootstrap on the OOS predictions captures both sources.
  - Practical: full-bootstrap-CV is expensive but well-calibrated.
- **Relevance to GTOS:** Right method for K54 hyperparameter-search CI. Avoids the "best-CV-Sharpe" headline problem (which is a max-of-N draw, severely biased upward).
- **Hypothesis implied:** *Bootstrap-CI on K54 best-CV-Sharpe will overlap zero ≥30% of the time across the hyperparameter grid — severely qualifying any "best CV Sharpe = X" headline.*
- **Cross-domain links:** 19.

### Factor Investing: A Bayesian Hierarchical Approach
- **Authors / Year:** Feng, G., & He, J., 2022
- **Source / URL:** Journal of Econometrics. https://www.sciencedirect.com/science/article/abs/pii/S030440762100258X ; SSRN: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3326617 ; arXiv: https://arxiv.org/pdf/1902.01015
- **Abstract:** Bayesian hierarchical model for factor investing across multiple assets, with heterogeneous time-varying coefficients driven by lagged fundamentals. Borrows information across assets while preserving heterogeneity. Improves on naive separate-time-series and pooled-stack alternatives.
- **Key findings:**
  - Hierarchical pool sharing improves estimation efficiency for any single asset.
  - Time-varying coefficients capture regime-conditioned predictability.
  - Beats both pure-pooled and pure-individual approaches in OOS forecasts.
- **Relevance to GTOS:** Directly relevant: GTOS has 7 instruments with related-but-not-identical signals; hierarchical Bayesian K54-variant would borrow info from XAUUSD/XAGUSD pair, FX cross-rates, etc., while preserving instrument heterogeneity.
- **Hypothesis implied:** *A hierarchical-Bayesian K54-variant pooling across XAUUSD + XAGUSD (correlated) + USDJPY + GBPJPY + GBPUSD (correlated) + US30 + NAS100 (correlated) will outperform the per-instrument K54 baseline by ≥0.05R/trade on the most data-poor instruments (NAS100).*
- **Cross-domain links:** 19, 13.

### A Survey of Methods for Time Series Change Point Detection
- **Authors / Year:** Aminikhanghahi, S., & Cook, D. J., 2017
- **Source / URL:** Knowledge and Information Systems, 51(2), 339-367. https://link.springer.com/article/10.1007/s10115-016-0987-z ; PDF: https://pmc.ncbi.nlm.nih.gov/articles/PMC5464762/
- **Abstract:** Comprehensive survey of time-series CPD methods. Covers parametric (CUSUM, GLR), non-parametric (kernel-based, Bayesian), and ML-based (HMM, change-finder). Application areas: medical, climate, financial.
- **Key findings:**
  - Parametric methods most powerful when assumptions match.
  - Non-parametric kernel methods more robust but lower power.
  - Bayesian-online-CPD provides UQ at higher computational cost.
  - Decision-tree for method selection by application context.
- **Relevance to GTOS:** Methodology survey for CPD across S1 monthly-decay, OB-continuation, BE-rate, hallucination-rate, etc. Helps select optimal CPD per signal characteristics.
- **Hypothesis implied:** *For OB-continuation rate (slow-changing target with known α), CUSUM-with-known-mean is optimal; for hallucination rate (unknown α, sudden shifts), Bayesian-online-CPD better. Different signals warrant different methods.*
- **Cross-domain links:** 05.

### Hannan-Quinn Information Criterion (HQIC)
- **Authors / Year:** Hannan, E. J., & Quinn, B. G., 1979
- **Source / URL:** Journal of the Royal Statistical Society Series B, 41, 190-195. Wikipedia summary: https://en.wikipedia.org/wiki/Hannan%E2%80%93Quinn_information_criterion ; HQ original: search RSS-B.
- **Abstract:** Proposes the HQ-IC: 2 × ln(ln(n)) × k penalty, intermediate between AIC's 2k and BIC's ln(n) × k. Strongly consistent for AR-order selection but less penalizing than BIC for large n.
- **Key findings:**
  - HQIC is strongly consistent (asymptotically picks the true model order with probability 1).
  - Penalty grows like ln(ln(n)) — slower than BIC's ln(n) — yielding richer models in large samples.
  - Smaller penalty than BIC, larger than AIC.
- **Relevance to GTOS:** Choice between AIC / BIC / HQ for K54 hyperparameter and AR-component selection. Under-cited despite its strong-consistency property; many GTOS researchers default to BIC without checking.
- **Hypothesis implied:** *HQIC-based selection of K54 ML hyperparameters will give a richer (but still consistent) model than BIC-based selection on the same data — likely improving live OOS performance modestly.*
- **Cross-domain links:** 19.

### Bias-Corrected Bootstrap and Model Uncertainty
- **Authors / Year:** Steck, H., & Jaakkola, T., 2003 (NeurIPS); plus broader bias-correction literature
- **Source / URL:** https://people.csail.mit.edu/tommi/papers/SteJaa-nips03.pdf ; review: https://arxiv.org/pdf/1709.06183
- **Abstract:** Combines bootstrap-bias-correction with explicit model-uncertainty representation. Improves prediction-CI calibration when underlying model class is uncertain.
- **Key findings:**
  - Plain bootstrap CIs are systematically biased low for finite samples.
  - Bias-corrected bootstrap (BCa) corrects with skew + bias adjustment.
  - Model-uncertainty Bayesian-bootstrap further widens CIs to reflect class uncertainty.
- **Relevance to GTOS:** Right method for K54 lift-CI when the model class itself is uncertain. We have fundamental uncertainty about whether K54 should be LightGBM, neural net, or hierarchical Bayesian — model-uncertainty-aware CIs would honestly reflect this.
- **Hypothesis implied:** *Properly model-uncertainty-aware K54 lift CI (BCa + Bayesian-bootstrap-over-model-class) will be approximately 2× wider than the naive CI — substantially weakening current "MARGINAL_WITH_PRACTICAL_LIFT" verdict.*
- **Cross-domain links:** 19.

### Bayesian Backtesting for Counterparty Risk Models
- **Authors / Year:** Arnsdorf, M., & Zelvyte, M., 2022
- **Source / URL:** SSRN: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4026491
- **Abstract:** Develops Bayesian backtesting framework for counterparty risk that tests individual model parameters and identifies which aspects are misspecified. Outperforms classical backtests on diagnostic-power.
- **Key findings:**
  - Bayesian backtest separates calibration error from prediction error.
  - Pinpoints which parameter is misspecified, not just whether overall model fails.
  - Posterior predictive checks decompose miscalibration.
- **Relevance to GTOS:** Methodologically relevant for any "the AI is making bad TP predictions" diagnosis — Bayesian backtest tells us if the issue is the prior, the likelihood, or the data. F8 found the calibration is the issue; this method would pinpoint which calibration component.
- **Hypothesis implied:** *Bayesian-backtest-decomposition on AI's TP predictions will localize the calibration error to the "expected reach" component (over-optimistic) rather than the "direction" component — directing prompt-engineering effort.*
- **Cross-domain links:** 19, 18.

### Probabilistic Forecasts, Calibration and Sharpness
- **Authors / Year:** Gneiting, T., Balabdaoui, F., & Raftery, A. E., 2007
- **Source / URL:** Journal of the Royal Statistical Society Series B, 69(2), 243-268. https://rss.onlinelibrary.wiley.com/doi/abs/10.1111/j.1467-9868.2007.00587.x ; PDF: https://sites.stat.washington.edu/raftery/Research/PDF/Gneiting2007jrssb.pdf
- **Abstract:** Foundational framework for evaluating probabilistic forecasts via calibration (statistical consistency between distributional forecasts and outcomes) + sharpness (concentration of forecast distribution). Prescribes "maximize sharpness subject to calibration."
- **Key findings:**
  - PIT (probability integral transform) histograms diagnose calibration.
  - Marginal calibration plots + sharpness diagrams as visual checks.
  - Proper scoring rules (CRPS, log-score) align ranking with theoretical optimality.
- **Relevance to GTOS:** GTOS edge is implicitly a probabilistic forecast (probability of TP-hit before SL-hit). PIT-histogram on AI's emitted "confidence in TP" vs realized would diagnose calibration failure. Right test for F8's "calibration drift, not perception drift" finding.
- **Hypothesis implied:** *PIT histogram of AI-emitted-probability-of-TP-hit (when explicitly elicited) vs realized TP-hits will be uniform under correct calibration; under H2-2026, will show systematic bias toward low-quantile (over-confidence) — quantifying decision-calibration decay.*
- **Cross-domain links:** 18, 19.

### Forecast Evaluation and Combination
- **Authors / Year:** Diebold, F. X., & Lopez, J. A., 1996
- **Source / URL:** Handbook of Statistics, Vol. 14, Ch. 8, 241-268. NBER: https://www.nber.org/papers/t0192 ; PDF: https://www.sas.upenn.edu/~fdiebold/papers/paper111/Diebold-Lopez%20(1996).pdf ; SSRN: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=225136
- **Abstract:** Foundational handbook chapter covering forecast evaluation (point + interval + density) and combination methods. Key reference for ensemble / pooling decisions; covers both unconditional and conditional combination weights.
- **Key findings:**
  - Combined forecasts (simple-average) often beat individual forecasts via diversification.
  - Optimal combination weights depend on covariance of forecast errors.
  - Interval-forecast evaluation requires LR tests (Christoffersen 1998).
- **Relevance to GTOS:** Methodology reference for combining K54-AI ensemble forecasts. Naive simple-average may already improve over either alone.
- **Hypothesis implied:** *Simple-average ensemble of K54 + AI on the same trade-eligibility decision will outperform either alone in OOS Sharpe by ≥0.05 — exploiting forecast-error decorrelation per Diebold-Lopez framework.*
- **Cross-domain links:** 19.

### Causal Factor Investing: Can Factor Investing Become Scientific?
- **Authors / Year:** Lopez de Prado, M., 2022
- **Source / URL:** SSRN: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4205613 ; Cambridge Element: https://www.cambridge.org/core/elements/causal-factor-investing/9AFE270D7099B787B8FD4F4CBADE0C6E ; PDF: https://www.quantresearch.org/QF_Causal_Factor_Investing.pdf
- **Abstract:** Polemic + methodology paper arguing factor investing has been built on associational claims that fail under stress. Proposes causal-inference (DAG-based) framework as the path to scientifically defensible factor research. Discusses Type-A vs Type-B spurious claims.
- **Key findings:**
  - Most factor research is correlation-based; causal claims rare.
  - Without causal theory, factor research over-fits and degrades quickly OOS.
  - DAG-based causal-inference can ground variable selection and counterfactual analysis.
- **Relevance to GTOS:** Conceptual foundation for asking "WHY does the OB-edge work?" rather than "DOES it work?" The mechanism-grounded edge claim (impulse-leg + stop-cascade-mean-reversion in `.context/01_knowledge_base/edge_mechanism.md`) is exactly the causal framing Lopez de Prado advocates.
- **Hypothesis implied:** *Building a DAG model of GTOS's edge (causes: impulse → stop-cascade → mean-reversion → OB-touch retracement) will reveal that the edge requires regime-conditioning (trending vs ranging) — confirming F15's regime-as-load-bearing finding from a causal-inference perspective.*
- **Cross-domain links:** 13, 22.

---

## Section 6 — Top 10 most-relevant-to-GTOS

Ranked by direct applicability to current GTOS subsystem decisions (K54 ML pipeline, SPRT halt rules, CUSUM monitor, multiple-testing discipline, edge-decay diagnosis). Numbers in parentheses = paper id from the CSV.

1. **Advances in Financial Machine Learning, Ch. 7-12** (#9) — Lopez de Prado 2018. CPCV + meta-labeling + triple-barrier are mandated for K54 v2; this is THE methodology reference. The single highest-leverage paper for Phase 2.

2. **The Deflated Sharpe Ratio** (#10) — Bailey, Lopez de Prado 2014. Directly applicable to K54 baseline lift evaluation (n=321 trades, +0.164R lift @ thr≥0.60). Without DSR, our headline AUC and lift figures are inflated — adopting DSR is mandatory before any production-gate decision.

3. **...and the Cross-Section of Expected Returns** (#11) — Harvey, Liu, Zhu 2016. Sets the discipline for our Validated Numbers regime under cumulative-test-count. As we keep running K-series and F-series tests, the Harvey-Liu-Zhu running threshold says we should continue ratcheting our t-cutoff up — likely already past 3.0.

4. **Triple-Barrier Method and Meta-Labeling** (#15) — Lopez de Prado 2018. GTOS's TP/SL/time-out labels ARE triple-barrier labels; meta-labeling is the natural architecture for K54 (filter signals, don't replace them). This is the prescriptive architecture.

5. **The Three Types of Backtests** (#23) — Joubert, Sestovic, Barziy, Distaso, Lopez de Prado 2024. Mandates that K54 evaluation should include walk-forward + CPCV + Monte-Carlo simulation under regime stress. Currently we report only CPCV — incomplete.

6. **Sequential Tests of Statistical Hypotheses (SPRT)** (#5) — Wald 1945. Theoretical foundation for the XAUUSD LONG-WR-watch SPRT halt rule. Direct applicability to the active live-monitoring infrastructure.

7. **Stepwise Multiple Testing as Formalized Data Snooping (Romano-Wolf StepM)** (#16) — Romano, Wolf 2005. Right method for the 47 instrument×side×regime cell tests. Spec §7 explicitly references Romano-Wolf as a "concrete pre-registrable check"; this paper is the canonical reference.

8. **Tests of Conditional Predictive Ability** (#17) — Giacomini, White 2006. Relevant given F15's regime-conditioned decay finding: forecast comparison must be conditional on regime, not unconditional. Frames how K54-vs-Sonnet 4.6 should actually be compared.

9. **Probabilistic Forecasts, Calibration and Sharpness** (#68) — Gneiting et al. 2007. Direct framework for diagnosing F8's "calibration drift, not perception drift" finding. PIT-histogram on AI-confidence is the right test.

10. **Backtest Overfitting in the Machine Learning Era** (#25) — Arian, Norouzi, Seco 2024. Modern empirical study confirming CPCV beats walk-forward and naive k-fold for ML-style backtests. Direct precedent for K54 v2 design choice.

**Honorable mentions** (in slot 11-15 for any expanded shortlist):
- **The False Strategy Theorem** (#54) — Lopez de Prado, Bailey 2018. Numerical bound on noise-Sharpe-from-N for sanity-checking any "best-of-N" claim.
- **The Sharpe Ratio Efficient Frontier (PSR)** (#35) — Bailey, Lopez de Prado 2012. Direct test of "is XAUUSD's track record long enough to support its current Sharpe claim?"
- **Continuous Inspection Schemes (CUSUM)** (#4) — Page 1954. Method foundation for `shadow_logs/cusum_candidate_rate_daily.csv` and OB-continuation monitor.
- **Does Academic Research Destroy Stock Return Predictability?** (#58) — McLean, Pontiff 2016. Empirical pace-setter for our edge-decay observations.
- **Lucky Factors** (#56) — Harvey, Liu 2021. Right method for K-series feature-importance tests with correlated test statistics.

---

## Section 7 — Cross-domain handoffs

Ten papers in this corpus are properly multi-domain. Routing recommendations for Phase 2 synthesis:

**Volatility / GARCH-related → Domain 03 + 16**
- (#43) Hansen, Lunde 2005 — A Forecast Comparison of Volatility Models (canonical 02 due to SPA-application; 03 owns vol-as-stylized-fact; 16 owns vol-trading)
- (#44) Hansen, Huang, Shek 2012 — Realized GARCH (canonical 02; 03 owns realized-vol stylized fact; 16 owns vol-trading)
- (#52) Hansen, Lunde 2006 — Consistent Ranking of Vol Models (canonical 02; 03 + 16 cross-link)
- (#53) Patton 2011 — Volatility Forecast Comparison Using Imperfect Volatility Proxies (canonical 02; 03 + 16 cross-link)
- (#47) Cont 2001 — Stylized Facts (cross-link from 02; CANONICAL OWNER is 03 — flagged for re-routing)
- (#59) Engle 1982 — ARCH (canonical 02 due to LM-test methodology; 03 + 16 cross-link)

**Distributional inference / bootstrap → Domain 03**
- (#19) Politis, Romano 1994 — Stationary Bootstrap (canonical 02 due to inference; 03 cross-link for fat-tail bootstrap discussion)

**Change-point / regime-switching → Domain 05**
- (#4) Page 1954 — CUSUM (canonical 02; 05 cross-link)
- (#46) Wang 2024 — Sequential Change-Point Detection (canonical 02 since survey covers methodology broadly; 05 owns specifically-financial-regime-CPD)
- (#61) Wang, Ramdas 2025 — FWER with E-values (canonical 02; 05 cross-link for sequential detection)
- (#48) Stock, Watson 1996 — Structural Instability (canonical 02 since methodology paper; 05 owns regime-application)
- (#64) Aminikhanghahi, Cook 2017 — CPD Survey (canonical 02 since broad methodology; 05 cross-link for specifically-financial)

**ML methodology → Domain 19**
- (#9) Lopez de Prado AFML (canonical 02 because prescription is methodological discipline; 19 cross-link); (#14) Combinatorial Purged CV; (#15) Triple-Barrier; (#25) Arian et al. 2024 ML Backtest; (#38) Bergmeir-Hyndman-Koo 2018; (#62) Bootstrap CV Predictions

**Multiple testing applied to factors / cross-section → Domain 13**
- (#11) Harvey, Liu, Zhu 2016 — ...and the Cross-Section (canonical 02 due to t-stat-haircut methodology; 13 owns factor-zoo content)
- (#36) Hou, Xue, Zhang 2020 — Replicating Anomalies (canonical 02 since replication-discipline; 13 cross-link)
- (#37) Chen, Zimmermann 2022 — Open Source Cross-Sectional Asset Pricing (similar)
- (#56) Harvey, Liu 2021 — Lucky Factors (canonical 02; 13 cross-link)
- (#57) Harvey, Liu 2020 — False (and Missed) Discoveries
- (#60) Gu, Kelly, Xiu 2020 — Empirical Asset Pricing via Machine Learning (canonical 02 since walk-forward methodology; 13 cross-link)
- (#70) Lopez de Prado 2022 — Causal Factor Investing (canonical 02; 13 + 22 cross-link)

**Sizing / risk → Domain 21**
- (#10) Bailey, Lopez de Prado 2014 — Deflated Sharpe (canonical 02 due to multiple-testing focus; 21 owns Sharpe-as-sizing-input)
- (#21) Lo 2002 — Statistics of Sharpe Ratios (canonical 02; 21 cross-link)
- (#35) Bailey, Lopez de Prado 2012 — Sharpe Ratio Efficient Frontier / PSR (canonical 02; 21 cross-link)
- (#42) Ledoit, Wolf 2008 — Robust Performance Hypothesis Testing (canonical 02; 21 cross-link)
- (#41) Wright et al. / Bailey, Lopez de Prado — PSR for Difference of Sharpe (canonical 02; 21 cross-link)

**VaR / interval-coverage / vol regime → Domain 16 + 21**
- (#40) Christoffersen 1998 — Evaluating Interval Forecasts (canonical 02; 16 + 21 cross-link)
- (#67) Arnsdorf, Zelvyte 2022 — Bayesian Backtesting (canonical 02; 19 cross-link primary)

**Behavioral / psychology calibration → Domain 18**
- (#20) Mincer, Zarnowitz 1969 — Forecast Evaluation Regression (canonical 02; 18 cross-link for decision-calibration angle)
- (#68) Gneiting et al. 2007 — Probabilistic Forecasts (canonical 02; 18 + 19 cross-link)
- (#28) Witzany 2017 — Bayesian Approach to Backtest Overfitting (canonical 02; 19 + 21 cross-link)

**Behavioral / replication-crisis-style → Domain 17 + 22**
- (#22) Goyal, Welch, Zafirov 2024 (canonical 02 due to OOS-protocol methodology; 14 + 19 + 22 cross-link)
- (#58) McLean, Pontiff 2016 (canonical 02 due to methodology decomposition; 13 + 17 + 22 cross-link)
- (#50) Sullivan, Timmermann, White 1999 (canonical 02; 14 + 22 cross-link)

**Trend / momentum / technical-trading content** → Domain 14
- (#29) Hsu, Hsu, Kuan 2010 — Stepwise SPA for Technical Trading (canonical 02; 14 cross-link)
- (#51) Brock, Lakonishok, LeBaron 1992 (canonical 02 due to bootstrap-methodology pioneering; 14 cross-link)
- (#6) Lo, MacKinlay 1988 — Variance Ratio (canonical 02; 14 + 03 cross-link)

---

## Section 8 — Synthesis caveats and gaps

**Coverage gaps:**
- **Pure SPRT applications in finance** — surprisingly thin academic literature; most practitioner SPRT use is industrial. Wald 1945 + practitioner blogs dominate. Phase 2 may need to commission first-principles re-derivation.
- **Anytime-valid sequential testing** — emerging field (Vovk, Wang, Ramdas 2021-2025), still pre-canonical. Could be high-leverage for live monitoring but not yet standard.
- **CPCV finance-specific empirical evaluation** — only one major recent study (Arian-Norouzi-Seco 2024); limited cross-validation of the "CPCV is best" claim.
- **Bayesian backtesting with practitioner adoption** — promising methodology, but practitioner literature is thin. Witzany 2017 + Arnsdorf-Zelvyte 2022 are the few SSRN treatments.

**Methodology bias awareness:**
- Lopez de Prado authored or co-authored ~15 of 70 papers. He's the dominant figure in modern backtest-methodology, but his prescriptive style means "Lopez de Prado canon" can crowd out alternatives. Recommend Phase 2 synthesis explicitly seek non-Lopez-de-Prado methodological alternatives where they exist (e.g., Hansen-Lunde for multiple-testing in vol-forecasting; Romano-Wolf for stepwise; Harvey-Liu for factor-multiple-testing; Bayesian-Bayesian for posterior-based).

**Decision-relevance ranking:**
- For K54 v2 production gate: papers #9, #10, #14, #15, #23, #25 (CPCV + DSR + meta-labeling + ML-era backtests).
- For SPRT halt-rule design: #5, #46, #61 (Wald + e-detectors + e-process FWER).
- For multiple-testing discipline: #11, #16, #29, #56, #57 (Harvey-Liu-Zhu + Romano-Wolf + Stepwise SPA + Lucky Factors + False/Missed).
- For edge-decay diagnosis: #4, #58, #50, #22, #48 (CUSUM + McLean-Pontiff + Sullivan-Timmermann-White + Goyal-Welch-Zafirov + Stock-Watson).
- For calibration-drift diagnosis (F8 finding): #20, #40, #68 (Mincer-Zarnowitz + Christoffersen + Gneiting).

---

*Last updated: 2026-04-28. Worker: Phase 1 Literature Agent #2. 70 papers cataloged across 7 sections.*


