# Domain 05 — Change-Point Detection and Regime Switching

**Phase 1 worker:** Literature Research Agent — Change-Point Detection + Regime Switching
**Date compiled:** 2026-04-28
**Papers cataloged:** 75
**Coverage:** Foundational (Hamilton, Bai-Perron, Andrews, BOCPD, CUSUM) + recent advances 2018-2026 (deep-learning CPD, BOCPD-AR with score-driven dynamics, jump models, panel MSGARCH, TDA-based detection, clustering with Wasserstein) + critical/contrarian voices.

---

## 1. Section overview

This domain is the load-bearing literature anchor for the GTOS regime-classifier upgrade (`src/components/regime_classifier.py`), the K54 ML classifier (Phase 2 rank #1), the S1 monthly-decay shadow monitor, and the production CUSUM-candidate-rate-daily monitor. The F15 finding — XAUUSD H1 (78% bullish regime) → H2 (4.8% bullish regime) — is itself a regime *shift* and falls squarely within this domain's ambit.

The literature splits cleanly into four buckets, matching the §8 quality-bar request:

| Category | Count | Anchor papers |
|----------|-------|---------------|
| (a) Detection methods (CUSUM, BOCPD, kernel-CP, deep-CP) | 18 | 05-02 Page; 05-05 Adams-MacKay; 05-43 Aue-Kirch; 05-49 Li-Fearnhead-Fryzlewicz-Wang |
| (b) Regime-switching models (HMM, MSGARCH, MSAR) | 21 | 05-01 Hamilton 1989; 05-17 Haas-Mittnik-Paolella; 05-32 Ardia-Bluteau-Boudt-Catania |
| (c) Structural-break inference (Andrews, Bai-Perron, Quandt-Chow) | 9 | 05-03 Andrews 1993; 05-04 Bai-Perron 1998 |
| (d) Financial regime evidence | 17 | 05-22 Engel-Hamilton; 05-10 Guidolin-Timmermann; 05-71 Maheu-McCurdy-Song; 05-68 SP500 MS-vol 2025 |
| Surveys / methodology | 10 | 05-34 Aminikhanghahi-Cook; 05-35 Truong-Oudre-Vayatis; 05-57 Hamilton handbook |

Per-paper detail in §3-§7. CSV with all annotation fields at `papers.csv`.

---

## 2. Sections 1-7 — per-paper catalog

(papers ordered by category; full schema in `papers.csv`. Below shows id, title, authors-year, URL, key relevance, and online/offline annotation.)

### Section 1 — Foundational regime-switching models

#### 05-01 A New Approach to the Economic Analysis of Nonstationary Time Series and the Business Cycle
- **Authors / year:** Hamilton J.D., 1989
- **Source:** Econometrica 57(2) 357-384
- **URL:** https://users.ssc.wisc.edu/~behansen/718/Hamilton1989.pdf
- **Abstract (paraphrase):** Proposes a tractable approach to modeling regime changes where AR parameters are the outcome of a discrete-state Markov process; presents a recursive filter analogous to Kalman filter to infer unobserved regimes and estimate parameters by maximum likelihood.
- **Key findings:** Foundational two-state Markov-switching framework; recursive Hamilton filter for posterior regime probabilities; ML estimation; demonstrated on US GNP cyclical regimes; analytic identification conditions for two-regime separability.
- **Relevance to GTOS:** Direct anchor for the regime-classifier upgrade. Current v1 H4-swing classifier is observational only; Hamilton-style 2-state MS-AR on H4 returns offers a probabilistic regime label that can replace ad-hoc swing rules and provide regime confidence as an additional feature for K54.
- **Hypothesis (H1):** A 2-state Hamilton MS-AR on XAUUSD H4 log-returns produces regime probabilities with higher H1→H2 forecast separation than v1 swing classifier (test on F15 regime-shift period).
- **Cross-domain:** 01 (Markov chain theory); 02 (likelihood inference); 19 (ML for finance: regime as ML feature).
- **Online/offline:** Offline-fitted, online-filtering (Hamilton filter is recursive).

#### 05-06 Analysis of Time Series Subject to Changes in Regime
- **Authors / year:** Hamilton J.D., 1990
- **Source:** Journal of Econometrics 45(1-2) 39-70
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/0304407690900939
- **Abstract:** Introduces an EM algorithm for ML estimation of MS-AR processes with discrete shifts in autoregressive parameters governed by a discrete-valued Markov chain; extends 1989 paper to vector systems.
- **Key findings:** EM algorithm for MS-AR estimation; smoothed regime probabilities (forward-backward); generalization to vector systems; foundation for MS-VAR.
- **Relevance to GTOS:** Operational-grade fitting recipe for the K54 regime-classifier successor. Smoothed probabilities give per-bar regime confidence usable as a feature.
- **Hypothesis (H6):** Per-bar smoothed regime probability from MS-AR(2) on XAUUSD H4 returns predicts next-bar realized R with regression-coefficient |t|>2 (n≥200).
- **Cross-domain:** 01 (HMM theory); 19 (regime as feature in K54).
- **Online/offline:** Offline-fitted, online-filtering.

#### 05-07 Autoregressive Conditional Heteroskedasticity and Changes in Regime (SWARCH)
- **Authors / year:** Hamilton J.D. & Susmel R., 1994
- **Source:** Journal of Econometrics 64(1-2) 307-333
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/0304407694900671
- **Key findings:** Switching-ARCH (SWARCH) addresses ARCH overstatement of volatility persistence; 2-3 regime models fit weekly equity returns; lower implied persistence than single-regime ARCH; better forecasts after large shocks.
- **Relevance to GTOS:** XAUUSD has highly persistent volatility plus regime shifts (F15). SWARCH or MSGARCH on M15/H1 returns gives a vol-state label; combined with v1-regime gives a 2D regime cell — direct K54 input.
- **Hypothesis (H7):** A 2-regime SWARCH on XAUUSD H1 returns produces vol-state labels that improve K53-style classifier OOS AUC by ≥0.04.
- **Cross-domain:** 03 (GARCH descriptive); 16 (vol-regime trading).
- **Online/offline:** Offline-fitted, online-filtering.

#### 05-08 Markov-Switching Vector Autoregressions (Krolzig monograph)
- **Authors / year:** Krolzig H.-M., 1997
- **Source:** Springer Lecture Notes in Economics 454 (book)
- **URL:** https://link.springer.com/book/10.1007/978-3-642-51684-9
- **Key findings:** Systematic taxonomy of MS-VAR variants (MSI / MSM / MSH); complete EM-based ML estimation theory; forecasting recipes; business-cycle applications; cointegration with regime.
- **Relevance to GTOS:** Multi-instrument MS-VAR is the natural extension when regime states should be cross-instrument-coherent (a single risk-on/risk-off regime governing XAU + USDJPY + US30 jointly). Connects to GTOS cross-instrument correlation gate.
- **Hypothesis (H8):** A 2-regime MS-VAR on (XAU, US30, USDJPY, GBPJPY) returns yields regime states whose risk-off label correlates with realized DXY r≥0.4.
- **Cross-domain:** 13 (cross-asset correlation); 11 (FX safe-haven).
- **Online/offline:** Offline.

#### 05-18 State-Space Models with Regime Switching (Kim-Nelson)
- **Authors / year:** Kim C.-J. & Nelson C.R., 1999
- **Source:** MIT Press monograph
- **URL:** https://direct.mit.edu/books/monograph/3265/State-Space-Models-with-Regime-SwitchingClassical
- **Key findings:** Kim filter handles state-space with regime switching; Gibbs sampler enables Bayesian inference; canonical reference for combining latent factor + regime models.
- **Relevance to GTOS:** If GTOS wants to combine a continuous latent factor (e.g., vol-of-vol or stress index) with discrete regime, Kim-Nelson is the architecture. Bridges deterministic v1 swing classifier with probabilistic alternatives.
- **Hypothesis (H18):** A Kim filter on (returns, realized vol) with regime-switching mean and variance produces regime labels coherent with v1 swing classifier ARI≥0.5.
- **Cross-domain:** 01 (state-space); 19 (Bayesian models).
- **Online/offline:** Offline-fitted, online-filtering.

#### 05-19 Regime Switching with Time-Varying Transition Probabilities
- **Authors / year:** Diebold F.X., Lee J.-H., Weinbach G.C., 1994
- **Source:** Hargreaves (ed.), Nonstationary Time Series Analysis and Cointegration, OUP
- **URL:** https://www.sas.upenn.edu/~fdiebold/papers/paper69/pa.dlw.pdf
- **Key findings:** TVTP MS lets regime persistence depend on fundamentals; richer than constant-transition MS; identifiable when covariates have predictive power for transitions.
- **Relevance to GTOS:** If macro covariates (DXY, VIX, gold-real-yield correlation) predict regime transitions, TVTP MS captures it. Connects to GTOS pre-AI gates that already use macro context.
- **Hypothesis (H19):** TVTP MS where transition probs depend on (DXY change, VIX level) outperforms constant-transition MS on XAU in-sample AIC and OOS regime classification.
- **Cross-domain:** 11 (FX/macro); 16 (vol context).
- **Online/offline:** Offline-fitted, online-filtering.

#### 05-20 Business-Cycle Phases and Their Transitional Dynamics
- **Authors / year:** Filardo A.J., 1994
- **Source:** Journal of Business and Economic Statistics 12(3) 299-308
- **URL:** https://www.tandfonline.com/doi/abs/10.1080/07350015.1994.10524545
- **Key findings:** TVTP business-cycle MS; leading indicators improve regime classification; foundation for macro-conditioned regime models.
- **Relevance to GTOS:** Empirical demonstration that TVTP MS works in a macro setting. Operational template for a GTOS macro-conditioned regime classifier.
- **Cross-domain:** 11 (macro); 17 (cycle effects).
- **Online/offline:** Offline-fitted, online-filtering.

#### 05-21 Modeling the Conditional Distribution of Interest Rates as a Regime-Switching Process
- **Authors / year:** Gray S., 1996
- **Source:** Journal of Financial Economics 42(1) 27-62
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/0304405X96008756
- **Key findings:** GRS = regime-switching with embedded GARCH and mean-reversion; first MS-GARCH with rigorous likelihood; outperforms single-regime in-sample and OOS for US short rate.
- **Relevance to GTOS:** Direct precedent for combining Markov regimes with conditional heteroskedasticity in returns. Architecture template for an MSGARCH-on-returns layer in K54.
- **Hypothesis (H20):** A Gray-style MSGARCH on XAU H4 returns reduces VaR violation rate by ≥20% vs single-regime GARCH.
- **Cross-domain:** 16 (vol); 11 (rates).
- **Online/offline:** Offline-fitted, online-filtering.

#### 05-29 Markov Switching in GARCH Processes and Mean-Reverting Stock-Market Volatility (Dueker)
- **Authors / year:** Dueker M.J., 1997
- **Source:** Journal of Business and Economic Statistics 15(1) 26-34
- **URL:** https://files.stlouisfed.org/files/htdocs/wp/1994/94-015.pdf
- **Key findings:** Switching-df Student-t gives time-varying tail thickness; superior multi-period vol forecast vs implied vols.
- **Relevance to GTOS:** Tail behavior shifts across regimes — directly relevant for fat-tail-aware sizing (`distributional_findings`). Dueker offers a parsimonious recipe.
- **Hypothesis (H28):** Adding switching-df Student-t to XAU H1 GARCH improves left-tail VaR coverage by ≥2pp at 1% level.
- **Cross-domain:** 03 (fat tails); 16 (vol).
- **Online/offline:** Offline-fitted, online-filtering.

#### 05-31 The Sticky HDP-HMM
- **Authors / year:** Fox E.B., Sudderth E.B., Jordan M.I., Willsky A.S., 2008-2011
- **Source:** Annals of Applied Statistics / NIPS
- **URL:** https://people.eecs.berkeley.edu/~jordan/papers/AOAS395.pdf
- **Key findings:** HDP-HMM is nonparametric (no need to fix K); but unmodified version overfits with rapid switching; sticky HDP-HMM enforces realistic state persistence; learnable dwell-time.
- **Relevance to GTOS:** Solves the "spurious regime" overfitting problem flagged by practitioner literature. If GTOS regime classifier is to be data-driven about K (number of regimes), sticky HDP-HMM is the architecture.
- **Hypothesis (H29):** Sticky HDP-HMM on XAU H4 returns selects K=3-5 regimes (vs current v1 hard-coded 4) without rapid-switching pathology; OOS regime-stability metric beats parametric K-fixed MS.
- **Cross-domain:** 19 (Bayesian nonparametric ML).
- **Online/offline:** Offline-fitted, online-filtering.

#### 05-71 Components of Bull and Bear Markets: Bull Corrections and Bear Rallies
- **Authors / year:** Maheu J.M., McCurdy T.H., Song Y., 2012
- **Source:** Journal of Business and Economic Statistics 30(3) 391-403
- **URL:** https://www.researchgate.net/publication/228179096_Components_of_Bull_and_Bear_Markets_Bull_Corrections_and_Bear_Rallies
- **Key findings:** Hierarchical regime structure: major bull/bear with embedded mini-states; better fit to drawdown dynamics; identifies within-bull pullbacks vs trend reversals.
- **Relevance to GTOS:** Direct relevance: GTOS often experiences within-bull pullbacks vs genuine reversals — same problem 4-state MS solves. Could refine ob_retest framework's regime-conditioning.
- **Hypothesis (H49):** A 4-state MS on XAU H1 returns identifies within-bull pullbacks (where ob_retest LONG should trade) vs bear-onset (where it should not) — improving LONG-side WR by ≥5pp.
- **Cross-domain:** 17 (bull/bear); 14 (trend).
- **Online/offline:** Offline-fitted, online-filtering.

(See `papers.csv` for entries 05-09 Ang-Bekaert; 05-10 Guidolin-Timmermann 2008; 05-15 Tong TAR; 05-16 Granger-Terasvirta STAR; 05-17 Haas-Mittnik-Paolella MSGARCH; 05-25 Klaassen MSGARCH; 05-30 Bauwens MSGARCH; 05-32 Ardia-Bluteau-Boudt-Catania MSGARCH performance study; 05-33 MSGARCH R package; 05-63 Bayesian nonparametric panel MSGARCH; 05-67 Giudici crypto HMM.)

---

### Section 2 — Detection methods (CUSUM, BOCPD, kernel, deep)

#### 05-02 Continuous Inspection Schemes (CUSUM)
- **Authors / year:** Page E.S., 1954
- **Source:** Biometrika 41(1-2) 100-115
- **URL:** https://academic.oup.com/biomet/article-abstract/41/1-2/100/456627
- **Key findings:** CUSUM is the seminal sequential change detector; uses full process history rather than fixed window; optimal under Lorden minimax criterion against constant-step shifts.
- **Relevance to GTOS:** GTOS already runs CUSUM-candidate-rate-daily and OB-continuation rolling-50 monitors; this is the literature anchor. Critical for S1 monthly-decay shadow monitor calibration.
- **Hypothesis (H2):** A multi-statistic CUSUM ensemble (per-instrument WR, CR, OB-continuation) lowers S1 false-alarm rate vs single-statistic baseline at matched detection latency.
- **Cross-domain:** 02 (sequential testing inference); 21 (CUSUM-triggered sizing reduction).
- **Online/offline:** Online.

#### 05-05 Bayesian Online Changepoint Detection (BOCPD)
- **Authors / year:** Adams R.P. & MacKay D.J.C., 2007
- **Source:** arXiv 0710.3742
- **URL:** https://arxiv.org/abs/0710.3742
- **Key findings:** BOCPD is the canonical online change-point detector; recursion over run-length probability; conjugate prior families admit tractable update; suitable for streaming data.
- **Relevance to GTOS:** Direct candidate for promoting GTOS regime-detection from observation-only to actionable. BOCPD on rolling features (vol, return autocorr, skew) can produce real-time regime probability that feeds the cross-instrument correlation gate or K54.
- **Hypothesis (H5):** A BOCPD pipeline on XAUUSD M15 returns + realized-vol + RV-skew triggers run-length resets that align with F15 regime change date within ±7 trading days.
- **Cross-domain:** 02 (Bayesian sequential inference); 19 (ML for finance: regime label).
- **Online/offline:** Online.

#### 05-43 The State of Cumulative Sum Sequential Changepoint Testing 70 Years After Page
- **Authors / year:** Aue A. & Kirch C., 2024
- **Source:** Biometrika 111(2) 367-391
- **URL:** https://academic.oup.com/biomet/article-abstract/111/2/367/7486557
- **Key findings:** Modern CUSUM has matured: self-normalization removes nuisance parameters; high-dim CUSUM with growing p; sequential testing under streaming covariates; tight theoretical guarantees.
- **Relevance to GTOS:** Authoritative anchor for upgrading GTOS CUSUM-candidate-rate-daily monitor with self-normalized variants and multivariate generalization (per-instrument joint CUSUM).
- **Hypothesis (H36):** Self-normalized CUSUM on (XAU, US30, USDJPY) joint daily CR vector reduces false-alarm rate by ≥30% at matched detection delay.
- **Cross-domain:** 02 (sequential inference).
- **Online/offline:** Online (review covers both).

#### 05-44 Learning from Time-Changing Data with Adaptive Windowing (ADWIN)
- **Authors / year:** Bifet A. & Gavalda R., 2007
- **Source:** SDM 2007
- **URL:** https://epubs.siam.org/doi/10.1137/1.9781611972771.42
- **Key findings:** ADWIN auto-adjusts window size; provable bounds on FP/FN; ADWIN2 is memory-efficient; popular in concept-drift / streaming-ML literature.
- **Relevance to GTOS:** Concept-drift literature parallel to BOCPD/CUSUM; ADWIN integrates well with online ML where window-size decisions matter (rolling-50 vs adaptive).
- **Hypothesis (H37):** An ADWIN-windowed XAU WR statistic detects F15 regime shift faster than fixed rolling-50 by ≥15 bars at matched FAR.
- **Cross-domain:** 19 (online ML); 02 (sequential testing).
- **Online/offline:** Online.

#### 05-45 Gaussian Process Change Point Models
- **Authors / year:** Saatci Y., Turner R., Rasmussen C.E., 2010
- **Source:** ICML 2010
- **URL:** https://mlg.eng.cam.ac.uk/pub/pdf/SaaTurRas10.pdf
- **Key findings:** GP-BOCPD: uses GP within each segment; correlated-data-aware; multiple computational variants.
- **Relevance to GTOS:** Specific upgrade path for BOCPD-with-correlation. If F11/F15 reveal that within-regime correlation matters, GP-BOCPD is the architecture.
- **Cross-domain:** 02 (Bayesian); 19 (GP ML).
- **Online/offline:** Online.

#### 05-46 Adaptive Sequential Bayesian Change Point Detection
- **Authors / year:** Turner R., Saatci Y., Rasmussen C.E., 2009
- **Source:** NIPS Temporal Segmentation Workshop
- **URL:** https://mlg.eng.cam.ac.uk/pub/pdf/TurSaaRas09.pdf
- **Key findings:** Adaptive hazard learning; useful when true change rate is unknown; Bayesian nonparametric on hazard.
- **Relevance to GTOS:** Practical refinement: GTOS doesn't know the true regime-change frequency. Adaptive hazard-rate estimation reduces hyperparameter sensitivity.
- **Cross-domain:** 02 (Bayesian sequential).
- **Online/offline:** Online.

#### 05-47 Kernel Change-point Analysis
- **Authors / year:** Harchaoui Z., Bach F., Moulines E., 2008-2009
- **Source:** NIPS 2008
- **URL:** https://papers.nips.cc/paper/3556-kernel-change-point-analysis
- **Key findings:** Kernel-CPD captures distributional shifts beyond mean/variance; MMD-based; useful for detecting changes in higher-order moments.
- **Relevance to GTOS:** If GTOS regime shifts are detectable in higher moments (skew, kurt) but not mean, kernel-CPD captures that. Connects to fat-tail-aware regime detection.
- **Hypothesis (H38):** Kernel-CPD on XAU H1 returns (with RBF kernel on 30-bar windows) detects F15 shift via 3rd-moment change before mean-CPD signal.
- **Cross-domain:** 02 (kernel testing); 03 (higher moments).
- **Online/offline:** Offline or sliding-online.

#### 05-48 NEWMA: A New Method for Scalable Model-Free Online Change-Point Detection
- **Authors / year:** Keriven N., Garreau D., Poli I., 2018
- **Source:** IEEE T-SP / arXiv 1805.08061
- **URL:** https://arxiv.org/pdf/1805.08061
- **Key findings:** Two EWMAs with different forgetting factors; flag change when gap exceeds threshold; sublinear in dimension; model-free.
- **Relevance to GTOS:** Lowest-overhead online detector; could be deployed alongside heavier BOCPD as a fast first-stage filter for live system.
- **Hypothesis (H39):** A NEWMA-on-XAU-H1-returns first-stage filter reduces BOCPD compute by ≥80% with negligible loss of detection power.
- **Cross-domain:** 02 (computation).
- **Online/offline:** Online.

#### 05-49 Automatic Change-Point Detection in Time Series via Deep Learning
- **Authors / year:** Li J., Fearnhead P., Fryzlewicz P., Wang T., 2024
- **Source:** Journal of the Royal Statistical Society Series B 86(2) 273-
- **URL:** https://academic.oup.com/jrsssb/article/86/2/273/7517020
- **Key findings:** Deep-learning CPD; scaling to many regimes via simulation-trained classifier; achieves SOTA on standard benchmarks; transfers across data types.
- **Relevance to GTOS:** Cutting-edge reference for ML-based CPD. May outperform BOCPD on irregular non-AR distributions. K54 ML synergy: classifier could be trained jointly for CPD + regime-class.
- **Hypothesis (H40):** A DL-CPD trained on simulated MS-GARCH DGPs detects F15 regime change earlier than BOCPD-AR by ≥N bars at matched FAR.
- **Cross-domain:** 19 (DL for finance); 02 (testing).
- **Online/offline:** Offline-fitted, online inference.

#### 05-41 Bayesian Autoregressive Online Change-Point Detection with Time-Varying Parameters
- **Authors / year:** Tsaknaki I.-Y., Lillo F., Mazzarisi P., 2024
- **Source:** arXiv 2407.16376
- **URL:** https://arxiv.org/html/2407.16376v1
- **Key findings:** BOCPD-AR(p)-score-driven extension; better fit when temporal correlation persists within regimes (i.e., not iid within regime); empirical advantage on financial data.
- **Relevance to GTOS:** Major upgrade for BOCPD's iid-within-regime assumption — which clearly fails for trading-edge data with autocorrelated returns. Closer to operational reality.
- **Hypothesis (H34):** BOCPD-AR(p)-score-driven on XAU H1 returns has lower false-alarm rate than vanilla-BOCPD by ≥30% at matched detection delay.
- **Cross-domain:** 02 (Bayesian sequential).
- **Online/offline:** Online.

#### 05-42 Online Learning of Order Flow and Market Impact with Bayesian Change-Point Detection Methods
- **Authors / year:** Tsaknaki I.-Y., Lillo F., Mazzarisi P., 2024
- **Source:** Quantitative Finance 25(2) 307-322
- **URL:** https://www.tandfonline.com/doi/full/10.1080/14697688.2024.2337300
- **Key findings:** Extended BOCPD on real LOB data; identifies persistent + transient regimes in order-flow imbalance; useful for anticipating short-horizon liquidity shifts.
- **Relevance to GTOS:** Most directly applicable contemporary paper to GTOS architecture: streaming detection + integration with execution-side proxies. Suggests value of detecting microstructure regimes alongside macro regimes.
- **Hypothesis (H35):** A short-horizon BOCPD on order-flow proxies (tick-feature memory) flags microstructure-regime change concurrent with E24-style microstructure-shift events.
- **Cross-domain:** 06 (microstructure); 02 (Bayesian sequential).
- **Online/offline:** Online.

(See `papers.csv` for entries 05-39 RuLSIF, 05-40 BOCPD-finance-2021, 05-50 DNN-multivariate, 05-51 HK stock BOCPD 2025.)

---

### Section 3 — Structural-break inference (offline, classical)

#### 05-03 Tests for Parameter Instability and Structural Change with Unknown Change Point
- **Authors / year:** Andrews D.W.K., 1993
- **Source:** Econometrica 61(4) 821-856
- **URL:** https://users.ssc.wisc.edu/~behansen/718/Andrews1993.pdf
- **Key findings:** Sup-Wald, sup-LM, sup-LR tests for unknown break in GMM models; nonstandard asymptotic distributions; tied-down Bessel-process critical values; trimming parameter for break-search region.
- **Relevance to GTOS:** Anchor for offline structural-break testing of GTOS edge metrics. Was the H1→H2 WR shift a true break or finite-sample noise? Andrews sup-LR with regression of WR on time gives an honest p-value adjusted for the unknown-break-date search.
- **Hypothesis (H3):** A sup-LR test on monthly XAUUSD WR series rejects parameter stability with bonf-corrected p<0.05 over 2024-2026, formally confirming F15 regime shift was structural not noise.
- **Cross-domain:** 02 (structural-break inference).
- **Online/offline:** Offline.

#### 05-04 Estimating and Testing Linear Models with Multiple Structural Changes
- **Authors / year:** Bai J. & Perron P., 1998
- **Source:** Econometrica 66(1) 47-78
- **URL:** http://www.columbia.edu/~jb3064/papers/1998_Estimating_and_testing_linear_models_with_multiple_structural_changes.pdf
- **Key findings:** Multiple-break detection via dynamic programming; sequential and global F-tests for k vs k+1 breaks; partial structural-change models; widely used Bai-Perron test.
- **Relevance to GTOS:** If GTOS edge has multiple regime shifts (e.g., 2024→2025→2026), single-break tests miss them. Bai-Perron is a one-shot offline diagnostic to date all WR/expectancy breaks for the trade history.
- **Hypothesis (H4):** Bai-Perron with up to 3 breaks on full XAUUSD trade-by-trade R series identifies F15 (Q4-2025) as one of ≥2 breaks, suggesting multiple distinct decay regimes.
- **Cross-domain:** 02 (structural-break inference).
- **Online/offline:** Offline.

#### 05-11 Tests of Equality Between Sets of Coefficients (Chow Test)
- **Authors / year:** Chow G.C., 1960
- **Source:** Econometrica 28(3) 591-605
- **URL:** https://www.semanticscholar.org/paper/Tests-of-equality-between-sets-of-coefficients-in-Chow/0f70219160c8ad2f9db02e226d3f7d7320e729b8
- **Key findings:** First formal structural-break test; F-statistic comparing pooled vs split SSR; restricted to known break dates; foundation for subsequent unknown-break-date extensions.
- **Relevance to GTOS:** Useful for hypothesis-driven testing where the candidate break date is announced. For F15 unknown-date case, prefer Andrews 1993.
- **Cross-domain:** 02.
- **Online/offline:** Offline.

#### 05-12 The Estimation of the Parameters of a Linear Regression System Obeying Two Separate Regimes
- **Authors / year:** Quandt R.E., 1958
- **Source:** JASA 53(284) 873-880
- **URL:** https://www.semanticscholar.org/paper/The-Estimation-of-the-Parameters-of-a-Linear-System-Quandt/5808b306a17547589374752d82568ac693a3cc28
- **Key findings:** Initiating paper for switching-regression literature; max-LR test for unknown break.
- **Relevance to GTOS:** Historical foundation; useful as a "minimum baseline" before adopting Hamilton-style probabilistic switching.
- **Cross-domain:** 02.
- **Online/offline:** Offline.

#### 05-13 Estimating Multiple Breaks One at a Time
- **Authors / year:** Bai J., 1997
- **Source:** Econometric Theory 13 315-352
- **URL:** http://www.columbia.edu/~jb3064/papers/1997_Estimating_multiple_breaks_one_at_a_time.pdf
- **Key findings:** Sequential break detection: estimate one break, split sample, recurse; consistent and asymptotically equivalent to global method under conditions; computationally cheaper for many breaks.
- **Relevance to GTOS:** If trading-edge decay has many small breaks rather than one big one, this gives a tractable diagnostic.
- **Hypothesis (H13):** Bai-1997 sequential estimation on monthly OB-continuation series identifies 2-4 breaks aligned with prior diagnosed regime shifts (F11 + F15).
- **Cross-domain:** 02.
- **Online/offline:** Offline.

#### 05-14 Sample Splitting and Threshold Estimation
- **Authors / year:** Hansen B.E., 2000
- **Source:** Econometrica 68(3) 575-604
- **URL:** https://www.ssc.wisc.edu/~bhansen/papers/ecnmt_00.pdf
- **Key findings:** Threshold estimates super-consistent at rate n; LR-based confidence intervals via Bessel-process critical values; useful for empirical sample-splitting on continuous variables.
- **Relevance to GTOS:** Could threshold-detect regime by a continuous proxy (e.g., realized vol level); Hansen confidence intervals tell whether the threshold is sharp or uncertain.
- **Hypothesis (H14):** A Hansen threshold model with realized-vol as threshold variable yields a sharp split (CI<width-of-1-bin) on XAUUSD trade R, supporting a single-cutoff vol-regime view.
- **Cross-domain:** 02; 16 (vol regime).
- **Online/offline:** Offline.

#### 05-23 An Analysis of the Real Interest Rate Under Regime Shifts
- **Authors / year:** Garcia R. & Perron P., 1996
- **Source:** Review of Economics and Statistics 78(1) 111-125
- **URL:** https://www.jstor.org/stable/2109851
- **Key findings:** Real-rate regime shifts in 1973 and 1981; conventional unit-root tests are misleading when shifts are present; structural-break framework is necessary.
- **Relevance to GTOS:** Cautionary tale: stationarity / unit-root inference is sensitive to undetected regime shifts. GTOS validation pipeline (e.g., XAUUSD trend tests) should use regime-aware tests.
- **Hypothesis (H22):** Standard ADF/KPSS on XAU returns is sensitive to F15 regime shift; structural-break-aware unit root (Zivot-Andrews) gives different verdict.
- **Cross-domain:** 02; 11 (rates).
- **Online/offline:** Offline.

#### 05-36 PELT — Optimal Detection of Changepoints with a Linear Computational Cost
- **Authors / year:** Killick R., Fearnhead P., Eckley I.A., 2012
- **Source:** JASA 107(500) 1590-1598
- **URL:** https://arxiv.org/abs/1101.1438
- **Key findings:** PELT exact and linear-time under mild conditions; orders of magnitude faster than dynamic programming; available in `changepoint` R package and `ruptures` Python.
- **Relevance to GTOS:** Operational fast path for offline CPD on long GTOS time series.
- **Hypothesis (H31):** PELT on monthly OB-continuation series identifies the same set of breaks as Bai-Perron at 1/100th the wall-clock time.
- **Cross-domain:** 02.
- **Online/offline:** Offline.

#### 05-37 Wild Binary Segmentation
- **Authors / year:** Fryzlewicz P., 2014
- **Source:** Annals of Statistics 42(6) 2243-2281
- **URL:** https://stats.lse.ac.uk/fryzlewicz/wbs/wbs.pdf
- **Key findings:** WBS handles short spacings + small jumps; no window-size hyperparameter; sBIC stopping rule.
- **Relevance to GTOS:** Useful when GTOS has many small but real regime nudges (monthly vol shifts). WBS may detect what PELT misses.
- **Hypothesis (H32):** WBS on XAU monthly WR series detects more breaks than PELT (with default penalty), and the additional breaks improve OOS forecast RMSE.
- **Cross-domain:** 02.
- **Online/offline:** Offline.

(See `papers.csv` for 05-26 Pesaran-Pettenuzzo-Timmermann; 05-27 Pesaran-Pick-Pranovich; 05-28 Maheu-McCurdy 2009.)

---

### Section 4 — Financial-regime evidence (gold, FX, equity, crypto)

#### 05-22 Long Swings in the Dollar
- **Authors / year:** Engel C. & Hamilton J.D., 1990
- **Source:** American Economic Review 80(4) 689-713
- **URL:** https://ideas.repec.org/a/aea/aecrev/v80y1990i4p689-713.html
- **Key findings:** FX exhibits multi-year regime swings (appreciation vs depreciation regimes); deviation from random walk is statistically significant; markets don't fully price regime info.
- **Relevance to GTOS:** Empirical foundation for regime-based FX trading. Directly relevant to USDJPY, GBPJPY, GBPUSD orchestrators.
- **Hypothesis (H21):** USDJPY orchestrator H1→H2 WR shifts align with a long-swing regime change; regime label improves USDJPY R discrimination.
- **Cross-domain:** 11 (FX); 17 (adaptive markets).
- **Online/offline:** Offline.

#### 05-09 Regime Switches in Interest Rates
- **Authors / year:** Ang A. & Bekaert G., 2002
- **Source:** Journal of Business and Economic Statistics 20(2) 163-182
- **URL:** https://business.columbia.edu/sites/default/files-efs/citation_file_upload/Journal%20of%20Business%20and%20Economic%20Statistics%2020%2C%20April%202002%2C%20163.pdf
- **Key findings:** Multivariate beats univariate MS for rate forecasting; regimes align with business-cycle phases; OOS improvement is real but moment-matching is imperfect.
- **Relevance to GTOS:** Cautionary note for K54: multivariate (multi-instrument) regime info improves classification, but moment-matching can fail. Validate K54 on realized R OOS (per `walk_level_evidence_not_predictive`), not on moments alone.
- **Hypothesis (H9):** A multi-instrument MS classifier (XAU+US30+USDJPY) outperforms a univariate XAU MS classifier on H1→H2 OOS realized-R discrimination by ≥0.05 AUC.
- **Cross-domain:** 11 (FX); 13 (cross-asset).
- **Online/offline:** Offline-fitted, online-filtering.

#### 05-10 International Asset Allocation under Regime Switching, Skew, and Kurtosis Preferences
- **Authors / year:** Guidolin M. & Timmermann A., 2008
- **Source:** Review of Financial Studies 21(2) 889-935
- **URL:** https://academic.oup.com/rfs/article-abstract/21/2/889/1610338
- **Key findings:** Bull/bear regimes are real and detectable in international equity returns; ignoring them produces misallocation; co-skewness and co-kurtosis matter; regime-conditional Sharpe is informative.
- **Relevance to GTOS:** Validates the regime-aware sizing hypothesis behind side-aware sizing memory and S79. Regime-conditional sizing has academic precedent.
- **Hypothesis (H10):** Regime-conditional position sizing on XAUUSD outperforms uniform sizing on Sharpe over 30+ live trades.
- **Cross-domain:** 13 (factor models); 21 (sizing); 17 (adaptive markets).
- **Online/offline:** Offline-fitted, online-filtering.

#### 05-24 Identifying Bull and Bear Markets in Stock Returns
- **Authors / year:** Maheu J.M. & McCurdy T.H., 2000
- **Source:** Journal of Business and Economic Statistics 18(1) 100-112
- **URL:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=146531
- **Key findings:** Duration-dependent MS for bull/bear; declining hazards (longer-state stickier); identifies all major US downturns 1834-1996; returns clustered at start of bull markets.
- **Relevance to GTOS:** Duration-dependent MS captures regime-stickiness which simple MS misses. Edge decay may be a stickiness function — once in "decay" regime, expect persistence.
- **Hypothesis (H23):** Duration-dependent MS on XAU monthly WR identifies declining hazard for the H2-2026 decay regime, predicting persistence of suppressed WR for n more months.
- **Cross-domain:** 17 (bull/bear); 14 (regime-conditional momentum).
- **Online/offline:** Offline-fitted, online-filtering.

#### 05-52 Forecasting Volatility of Gold Price Using Markov Regime Switching and Trading Strategy
- **Authors / year:** Yip & Tsang or similar (verify before use)
- **Source:** Journal of Mathematical Finance 2(2)
- **URL:** https://www.scirp.org/journal/paperinformation?paperid=17610
- **Note:** Author names approximated from the source page; weaker peer-review status than RFS / JFE. Mark as `seed candidate — verify before use`.
- **Key findings:** Two-regime gold-vol model; trading-rule overlay; gold-specific empirical evidence for regime switching.
- **Relevance to GTOS:** Direct gold-empirical evidence. Useful prior for K54 design choice (XAU is regime-switching).
- **Hypothesis (H42):** MS-GARCH on XAU daily log-returns identifies a high-vol regime aligning with GTOS realized-R drawdown periods.
- **Cross-domain:** 10 (gold).
- **Online/offline:** Offline-fitted, online-filtering.

#### 05-53 Regime-Switching Factor Investing with Hidden Markov Models
- **Authors / year:** Wang M., Lin Y.-H., Mikhelson I., 2020
- **Source:** Journal of Risk and Financial Management 13(12) 311
- **URL:** https://www.mdpi.com/1911-8074/13/12/311
- **Key findings:** HMM regime-detection on equity indices; regime-conditional factor allocation; OOS Sharpe improvement; risk-management filter.
- **Relevance to GTOS:** Empirical template for regime-conditional strategy switching. Directly informs side-aware-sizing memory and regime-conditional-sizing hypothesis.
- **Cross-domain:** 13 (factors); 17 (regime-conditional).
- **Online/offline:** Offline-fitted, online-filtering.

#### 05-54 Downside Risk Reduction Using Regime-Switching Signals: A Statistical Jump Model Approach
- **Authors / year:** Shu Y., Yu C.-H., Mulvey J.M., 2024
- **Source:** Journal of Asset Management
- **URL:** https://link.springer.com/article/10.1057/s41260-024-00376-x
- **Key findings:** JM = HMM with explicit jump-penalty; mitigates rapid switching pathology; better OOS persistence; downside-risk reduction without sacrificing upside on equities.
- **Relevance to GTOS:** JM is a competitor to sticky-HDP-HMM (05-31) for solving the same problem (overfit to spurious regimes). Simpler / interpretable; could be operationalized faster.
- **Hypothesis (H43):** A jump-model regime classifier on XAU H1-features produces more stable regime labels (lower transition rate) than vanilla HMM at matched OOS realized-R AUC.
- **Cross-domain:** 13 (allocation); 21 (sizing).
- **Online/offline:** Offline-fitted, online-filtering.

#### 05-66 Regime Switching Forecasting for Cryptocurrencies
- **Authors / year:** various, 2024
- **Source:** Digital Finance
- **URL:** https://link.springer.com/article/10.1007/s42521-024-00123-2
- **Key findings:** Crypto exhibits strong regime structure (low/high vol); MS forecast OOS-advantage exists but is sample-dependent; regime detection is easier than regime-conditioned forecasting.
- **Relevance to GTOS:** Cautionary note: detecting regimes in markets is easier than profiting from the detection. Relevant warning for K54 success criteria — beat benchmarks on realized R, not just regime-classification metrics.
- **Cross-domain:** 17 (adaptive markets).
- **Online/offline:** Offline-fitted, online-filtering.

#### 05-68 Improving S&P 500 Volatility Forecasting Through Regime-Switching Methods (2025)
- **Authors / year:** various, 2025
- **Source:** arXiv 2510.03236
- **URL:** https://arxiv.org/html/2510.03236v1
- **Key findings:** Recent data (post-COVID) favors MS-vol forecasting; HAR baselines beaten with regime-aware extensions; benchmarking matters.
- **Relevance to GTOS:** Recent empirical confirmation that MS-vol still wins post-2020. Supports MSGARCH-on-XAU layer for K54.
- **Cross-domain:** 16 (vol forecasting).
- **Online/offline:** Offline-fitted, online-filtering.

(See `papers.csv` for entries 05-32 Ardia-Bluteau-Boudt-Catania large-scale MSGARCH; 05-33 MSGARCH R package; 05-67 crypto HMM; 05-69 RV-MS forecasting; 05-72 / 05-73 directional change Tsang.)

---

### Section 5 — Time-varying parameter and continuous-drift alternatives

#### 05-59 Time-Varying Structural Vector Autoregressions and Monetary Policy
- **Authors / year:** Primiceri G.E., 2005
- **Source:** Review of Economic Studies 72(3) 821-852
- **URL:** https://faculty.wcas.northwestern.edu/gep575/tvsvar_final_july_04.pdf
- **Key findings:** TVP-VAR with SV captures continuous evolution rather than discrete regimes; alternative to MS for slowly-evolving relationships; Bayesian computation.
- **Relevance to GTOS:** Smooth-drift alternative to discrete regime models; applicable when GTOS believes edge erodes continuously rather than via abrupt breaks.
- **Hypothesis (H45):** A TVP-VAR on XAU returns with SV detects gradual edge decay better than discrete MS on AIC and OOS realized-R prediction.
- **Cross-domain:** 11 (macro); 19 (Bayesian).
- **Online/offline:** Offline.

#### 05-60 Drifts and Volatilities: Monetary Policies and Outcomes in the Post WWII US
- **Authors / year:** Cogley T. & Sargent T.J., 2005
- **Source:** Review of Economic Dynamics 8(2) 528-563
- **URL:** http://www.tomsargent.com/research/sims14.pdf
- **Key findings:** TVP-VAR with SV; Gibbs MCMC; identifies evolution of post-WWII US inflation persistence and policy.
- **Relevance to GTOS:** Companion paper to Primiceri 2005; together they form the TVP-VAR-SV canon. Use for inspiration on continuous-drift modeling.
- **Cross-domain:** 11 (macro).
- **Online/offline:** Offline.

#### 05-15 Threshold Autoregression / SETAR — Tong
- **Authors / year:** Tong H., 1990
- **Source:** Oxford University Press monograph
- **URL:** https://global.oup.com/academic/product/non-linear-time-series-9780198523000
- **Key findings:** TAR/SETAR captures asymmetric persistence and regime-dependent dynamics; deterministic threshold rather than probabilistic; more interpretable than MS but less flexible.
- **Relevance to GTOS:** Asymmetric AR dynamics across regimes is a known feature of trending markets. SETAR could be a lightweight alternative to MS-AR for regime classification when threshold variable is observable.
- **Hypothesis (H15):** SETAR on XAUUSD H4 returns with threshold = lagged 5-bar realized vol distinguishes vol-states with >2pp R difference (n≥200).
- **Cross-domain:** 14 (trend); 03 (nonlinear dynamics).
- **Online/offline:** Offline-fitted, online-filtering.

#### 05-16 Smooth Transition Autoregressive Models — Granger-Terasvirta
- **Authors / year:** Granger C.W.J. & Terasvirta T., 1993
- **Source:** Oxford University Press monograph
- **URL:** https://global.oup.com/academic/product/modelling-nonlinear-economic-relationships-9780198773207
- **Key findings:** STAR generalizes TAR with a continuous transition function; logistic STAR for monotone transitions, exponential STAR for symmetric.
- **Relevance to GTOS:** Trading regimes are rarely instantaneous; STAR matches the empirical observation of gradual edge decay. May fit GTOS edge-decay better than discrete regime models.
- **Hypothesis (H16):** A logistic STAR on XAU monthly WR-vs-time has lower AIC than a discrete two-state MS, indicating smooth (not abrupt) regime transition.
- **Cross-domain:** 14 (smooth trend); 03 (nonlinear dynamics).
- **Online/offline:** Offline-fitted, online-filtering.

---

### Section 6 — Critical / contrarian and methodology

#### 05-64 A Closer Look at the Regime-Switching Evidence of Bull and Bear Markets
- **Authors / year:** Kirby C., 2023
- **Source:** Finance Research Letters 52
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S1544612322005463
- **Key findings:** Critique: bull/bear MS estimates may be artifacts of return-distribution mixture properties; questions interpretation of regime parameters; methodological warning.
- **Relevance to GTOS:** Important contrarian voice. Reminds GTOS team that regime parameters are not directly observable and can be misinterpreted. Implies need for OOS validation of any regime label.
- **Hypothesis (H48):** A null-test that simulates returns from a fat-tailed mixture distribution (no regime structure) reproduces observed bull/bear-MS parameter estimates on XAU; reject regime interpretation if so.
- **Cross-domain:** 17 (behavioral); 03 (mixture distributions).
- **Online/offline:** Methodological critique.

#### 05-65 Practical Markov Regime-Switching for Finance and Energy: Mitigating the Risk of Spurious Regimes
- **Authors / year:** Levi J., 2024
- **Source:** Medium / industry whitepaper
- **URL:** https://medium.com/@jlevi.nyc/practical-markov-regime-switching-for-finance-and-energy-mitigating-the-risk-of-spurious-regimes-61fb955c240b
- **Key findings:** Spurious regimes are common when K is over-specified or outliers present; AIC/BIC discipline; OOS validation is essential; gray-literature complement to academic critiques.
- **Relevance to GTOS:** Practitioner-facing checklist. Validates the conservative-K approach (start with K=2-3, not K=5).
- **Cross-domain:** Methodological.
- **Online/offline:** Best-practice methodology.

#### 05-26 Forecasting Time Series Subject to Multiple Structural Breaks (Pesaran-Pettenuzzo-Timmermann)
- **Authors / year:** Pesaran M.H., Pettenuzzo D., Timmermann A., 2006
- **Source:** Review of Economic Studies 73(4) 1057-1084
- **URL:** https://academic.oup.com/restud/article-abstract/73/4/1057/1573279
- **Key findings:** Hierarchical Bayesian breaks; meta-distribution over break sizes and durations; OOS-better than methods that ignore breaks.
- **Relevance to GTOS:** Highly relevant: GTOS edge has experienced multiple breaks (item #4 in CLAUDE.md). Pesaran-Pettenuzzo-Timmermann gives a forecast model that *expects* future breaks rather than assuming stability.
- **Hypothesis (H25):** Pesaran-Pettenuzzo-Timmermann hierarchical-break forecast on XAU monthly WR outperforms a single-break or no-break forecast over 6-month OOS by RMSE ≥20%.
- **Cross-domain:** 02 (Bayesian inference); 14 (forecasting under breaks).
- **Online/offline:** Offline-fitted, online-filtering.

#### 05-27 Optimal Forecasts in the Presence of Structural Breaks
- **Authors / year:** Pesaran M.H., Pick A., Pranovich M., 2013
- **Source:** Journal of Econometrics 177(2) 134-152
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S0304407613000687
- **Key findings:** Optimal observation weights under MSE; continuous-break case yields exponential smoothing; discrete-break weights have closed forms.
- **Relevance to GTOS:** Operational bridge: GTOS already weights recent OB-continuation more (rolling-50). Pesaran-Pick-Pranovich gives the *optimal* weighting given assumed break-rate. Could replace ad-hoc rolling windows.
- **Hypothesis (H26):** Pesaran-Pick-Pranovich optimal weights on XAU WR series outperform fixed-rolling-50 on H2-2026 RMSE by ≥10%.
- **Cross-domain:** 02 (forecasting under breaks); 21 (sizing inputs).
- **Online/offline:** Offline-fitted, online-filtering.

#### 05-28 How Useful Are Historical Data for Forecasting the Long-Run Equity Return Distribution?
- **Authors / year:** Maheu J.M. & McCurdy T.H., 2009
- **Source:** Journal of Business and Economic Statistics 27(1) 95-112
- **URL:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=996696
- **Key findings:** Probability-weighted ensemble of submodels (each fit to a different post-break window); empirical Bayes factor for break vs no-break is exp(167); breaks affect tails not just means.
- **Relevance to GTOS:** Tail-risk inference is regime-dependent; this affects S79 risk-policy and Kelly sizing. Methodological template for tail-aware regime-conditioned sizing.
- **Hypothesis (H27):** Bayesian model-averaging across XAU windows post-2024-Q4-break provides Sharpe and CVaR estimates that differ materially from full-history estimates.
- **Cross-domain:** 21 (sizing under fat tails); 03 (tail behavior).
- **Online/offline:** Offline.

---

### Section 7 — Surveys, software, alternative methods (TDA / clustering / DC)

#### 05-34 A Survey of Methods for Time Series Change Point Detection
- **Authors / year:** Aminikhanghahi S. & Cook D.J., 2017
- **Source:** Knowledge and Information Systems 51(2) 339-367
- **URL:** https://eecs.wsu.edu/~cook/pubs/kais16.2.pdf
- **Key findings:** Taxonomy of CPD methods; key axes are supervision, parametric/nonparametric, online/offline; benchmarks on labeled datasets; gaps include real-time multivariate CPD.
- **Relevance to GTOS:** Anchor survey for navigating CPD method space. Read this before committing to a single method.
- **Online/offline:** Survey.

#### 05-35 Selective Review of Offline Change Point Detection Methods
- **Authors / year:** Truong C., Oudre L., Vayatis N., 2020
- **Source:** Signal Processing 167 107299
- **URL:** https://arxiv.org/abs/1801.00718
- **Key findings:** Three-block taxonomy (cost / search / constraint); ruptures Python package implements major algorithms; >140 papers reviewed.
- **Relevance to GTOS:** Essential reference for offline CPD on GTOS historical trade data. ruptures gives fast Python path to PELT, BinSeg, BottomUp, WBS implementations.
- **Online/offline:** Offline survey.

#### 05-38 Multiple Change-Point Detection: A Selective Overview
- **Authors / year:** Niu Y.S., Hao N., Zhang H.Y., 2016
- **Source:** Statistical Science 31(4) 611-623
- **URL:** https://projecteuclid.org/euclid.ss/1484816589
- **Key findings:** Selective overview of multiple-CP detection: regression, hypothesis testing, consistency, inference; coverage of normal-mean change-point model in depth.
- **Online/offline:** Survey.

#### 05-57 Macroeconomic Regimes and Regime Shifts (Hamilton handbook chapter)
- **Authors / year:** Hamilton J.D., 2016
- **Source:** Handbook of Macroeconomics Vol 2 163-201
- **URL:** https://www.nber.org/system/files/working_papers/w21863/w21863.pdf
- **Key findings:** Definitive review by founder of MS literature; covers identification, estimation, model selection, forecasting; gives modern best-practice template.
- **Relevance to GTOS:** Authoritative reference text. Read before designing GTOS regime classifier upgrade.
- **Online/offline:** Survey chapter.

#### 05-58 Regime Switching Models (Palgrave Encyclopedia)
- **Authors / year:** Hamilton J.D., 2008
- **Source:** New Palgrave Dictionary of Economics 2nd ed.
- **URL:** https://econweb.ucsd.edu/~jhamilto/palgrav1.pdf
- **Key findings:** Concise reference to regime-switching framework; classical+Bayesian inference; application examples.
- **Online/offline:** Survey entry.

#### 05-55 Change Point Detection in Financial Market Using Topological Data Analysis
- **Authors / year:** various, 2025
- **Source:** Systems 13(10) 875 (MDPI)
- **URL:** https://www.mdpi.com/2079-8954/13/10/875
- **Key findings:** TDA + persistent homology gives a regime-detection signal orthogonal to vol/return; rising spectral-density-at-low-frequencies precedes major crashes.
- **Relevance to GTOS:** Orthogonal signal class to traditional CPD; potentially fingerprints regime shifts that BOCPD/CUSUM miss. Worth piloting on XAU during F15 period to compare lead time.
- **Hypothesis (H44):** A TDA-persistence-landscape signal computed daily on XAU (with 26-stock companion universe) gives regime-shift early warning ≥14 days ahead of OB-continuation alarm.
- **Cross-domain:** 04 (TDA); 19 (alternative ML).
- **Online/offline:** Offline or sliding-online.

#### 05-56 Topological Data Analysis of Financial Time Series: Landscapes of Crashes
- **Authors / year:** Gidea M. & Katz Y., 2017-2018
- **Source:** Physica A 491 820-834
- **URL:** https://arxiv.org/abs/1703.04385
- **Key findings:** Lp-norm of persistence landscapes is leading indicator of crashes (dotcom + Lehman); computationally tractable on rolling windows.
- **Relevance to GTOS:** Foundational TDA-finance paper; provides validated empirical pattern (rising Lp pre-crash) that GTOS can replicate on XAU.
- **Cross-domain:** 04 (TDA).
- **Online/offline:** Offline with rolling-online.

#### 05-70 Topological Machine Learning for Financial Crisis Detection
- **Authors / year:** various, 2025
- **Source:** Computers 14(10) 408 (MDPI)
- **URL:** https://www.mdpi.com/2073-431X/14/10/408
- **Key findings:** TDA + ML combination; lead time ~1 month for major crises; signals persist across multiple market regimes.
- **Relevance to GTOS:** Empirical validation that TDA + ML can give actionable advance warning. Operational template for GTOS edge-decay early warning.
- **Cross-domain:** 04 (TDA); 19 (ML).
- **Online/offline:** Offline with rolling-online.

#### 05-61 Detecting Multivariate Market Regimes via Clustering Algorithms
- **Authors / year:** Mc Greevy J. et al., 2024
- **Source:** SSRN 4758243
- **URL:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4758243
- **Key findings:** Wasserstein-based regime clustering; explicit unsupervised regime identification; matches or beats HMM on benchmarks.
- **Relevance to GTOS:** Unsupervised alternative when HMM is hard to fit (small data). Could give GTOS a baseline before committing to MS-architecture.
- **Hypothesis (H46):** Wasserstein-k-means with k=3-4 on XAU multi-feature daily vector produces regime labels that align with v1 swing classifier (ARI≥0.4) at lower fitting cost.
- **Cross-domain:** 19 (unsupervised ML).
- **Online/offline:** Offline-fitted, online-filtering.

#### 05-62 Sliced Wasserstein K-Means
- **Authors / year:** Luan Q. & Hamp J., 2023
- **Source:** SSRN 4587877
- **URL:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4587877
- **Key findings:** Sliced Wasserstein is tractable in high dim; k-means on slice-distance gives regime labels; competitive vs HMM in tested datasets.
- **Relevance to GTOS:** Operational regime-detection method that scales to many features (e.g., GTOS 50+ feature vector).
- **Online/offline:** Offline-fitted, online-filtering.

#### 05-72 A Directional-Change Event Approach for Studying Financial Time Series
- **Authors / year:** Aloud M. & Tsang E.P.K. (and successors), 2012-2017
- **Source:** Economics: The Open-Access Journal
- **URL:** https://www.degruyterbrill.com/document/doi/10.5018/economics-ejournal.ja.2012-36/html?lang=en
- **Key findings:** DC-events define regime alternation by price-move magnitude rather than time; noise filter; identifies regime shifts via DC-event statistics.
- **Relevance to GTOS:** Alternative regime-detection lens that aligns naturally with ICT/SMC market-structure thinking (BOS = directional change). Could complement v1 swing classifier.
- **Hypothesis (H50):** DC-event statistics on XAU at threshold delta=15 ticks identifies regime-shift signals coherent with v1 swing classifier (precision≥0.7).
- **Cross-domain:** 07 (ICT/SMC); 06 (microstructure).
- **Online/offline:** Offline with online extension.

#### 05-73 Profiling High-Frequency Equity Price Movements in Directional Changes
- **Authors / year:** Tsang E., Tao R., Serguieva A., Ma S., 2017
- **Source:** Quantitative Finance 17(2) 217-225
- **URL:** https://www.tandfonline.com/doi/full/10.1080/14697688.2016.1164887
- **Key findings:** DC + overshoot statistics characterize regimes; normal vs abnormal regime profiles separable; HF empirical validation.
- **Cross-domain:** 06 (microstructure).
- **Online/offline:** Offline with online extension.

#### 05-74 Regime-Aware Adaptive Forecasting Framework for Bitcoin Prices Using Probabilistic Generative Models
- **Authors / year:** various, 2026
- **Source:** Computational Economics
- **URL:** https://link.springer.com/article/10.1007/s10614-026-11338-3
- **Key findings:** GMM-VAR vs HMM for crypto regime detection; GMM offers improvements over time-dependent HMM transition probs in HF data with overlapping regime shifts.
- **Relevance to GTOS:** Cautionary note: HMM may be too rigid for HF data with fast-evolving regimes. May affect K54 architecture choice for M15 data on XAU.
- **Hypothesis (H51):** A GMM-VAR regime model on XAU M15 outperforms a 2-state HMM on regime-classification AUC by ≥0.05.
- **Cross-domain:** 19 (generative ML).
- **Online/offline:** Offline-fitted, online-filtering.

#### 05-75 The Gerber Statistic
- **Authors / year:** Gerber S., Markowitz H.M., Ernst P., Miao Y., Javid B., Sargen P., 2022
- **Source:** Journal of Portfolio Management 48(2) 87-102
- **URL:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3880054
- **Key findings:** Gerber statistic = thresholded concordance count; robust to fat tails; useful for cross-asset correlation under regime-shift conditions.
- **Relevance to GTOS:** Cross-instrument correlation gate (currently 0.4 threshold) uses standard Pearson; Gerber is a robust alternative when regime-shift outliers distort Pearson.
- **Hypothesis (H52):** Replacing Pearson with Gerber-correlation in GTOS cross-instrument gate reduces false-trigger rate by ≥20% during F15 regime-shift period.
- **Cross-domain:** 13 (cross-asset); 21 (sizing).
- **Online/offline:** Offline with online rolling.

(See `papers.csv` for full set including 05-39 RuLSIF, 05-40 BOCPD-finance-2021, 05-50 DNN-multivariate-CPD, 05-51 HK 2025 BOCPD application, 05-67 Giudici crypto HMM.)

---

## 3. Top 3 most-relevant-to-GTOS papers (synthesis)

### #1 — 05-31 Sticky HDP-HMM (Fox et al. 2008-2011)
The strongest single architectural recommendation for the K54 regime-aware ML classifier. Solves the "how many regimes?" question without committing to a hard K, while explicitly avoiding the rapid-switching pathology that plagues vanilla HDP-HMM and naive multi-regime HMM. Directly addresses the spurious-regime risk that the contrarian literature (05-64, 05-65) flags as the biggest barrier to MS deployment in finance. Operational complement: can ship as a K54 v2 alongside the current LightGBM baseline, with model-comparison via OOS realized-R discrimination.

### #2 — 05-42 Online Learning of Order Flow and Market Impact with Bayesian Change-Point Detection (Tsaknaki, Lillo, Mazzarisi 2024)
Most directly applicable contemporary paper to GTOS architecture. Combines (i) a streaming detector (BOCPD), (ii) within-regime non-iid dynamics (Markovian + score-driven), and (iii) integration with execution-side proxies — exactly the integration shape GTOS needs for adding a microstructure-regime layer to the existing v1 H4-swing macro-regime classifier. The within-regime AR/score-driven extension addresses the chief technical objection to vanilla BOCPD on financial data (returns are not iid within a regime).

### #3 — 05-43 Aue-Kirch CUSUM Review (Biometrika 2024)
Authoritative anchor for the production CUSUM-candidate-rate-daily monitor and S1 monthly-decay shadow monitor. Self-normalized CUSUM removes nuisance-parameter calibration that's currently done ad hoc; high-dimensional / multivariate CUSUM unlocks joint cross-instrument detection (XAU + US30 + USDJPY simultaneously) — a direct upgrade path that requires zero new ML infra and aligns with the cross-instrument correlation gate's existing data flow.

---

## 4. Top 1 surprise

**05-64 Kirby (2023) — "A Closer Look at the Regime-Switching Evidence of Bull and Bear Markets" (Finance Research Letters).**

The methodologically sharpest contrarian voice in the modern literature. Argues that observed bull/bear regime parameters in MS estimates may be statistical artifacts of fat-tailed return distributions, not evidence of two distinct generating regimes. The implication for GTOS: a 2-state Hamilton MS fit on XAUUSD H1→H2 data could produce "regime-shift" parameters even if the true DGP is a stationary fat-tailed process with occasional outliers. This is a real epistemological brake on naive deployment of MS-based regime classifiers.

The corollary is a methodological discipline: any regime-classifier shipped to GTOS production should pass a null-test where simulated returns from a fat-tailed mixture (no regime structure) are run through the same fitting pipeline; if the fitted MS parameters look qualitatively similar to the live-data MS parameters, the regime interpretation is unsafe. Concretely connects to the existing GTOS memory `walk_level_evidence_not_predictive` — same class of statistical fragility, different model.

---

## 5. Hypotheses (3 highest-leverage for GTOS Phase 2 / experimentation)

### H-A: BOCPD-AR(p)-score-driven beats vanilla BOCPD on F15 detection (combination of 05-05 + 05-41 + 05-43)
A Bayesian online change-point detector with AR(p) within-regime dynamics and score-driven parameter updates, applied to XAUUSD M15/H1 returns + realized-vol + RV-skew, will detect the F15 regime change with lower false-alarm rate (≥30%) than vanilla iid-within-regime BOCPD at matched detection delay. Implementation cost: moderate (no new ML infra; BOCPD-style Python); experimental cost: low (replay on existing data); impact: a real-time regime-shift alarm with calibrated false-positive rate, suitable for feeding the K54 classifier or the cross-instrument gate.

### H-B: Sticky HDP-HMM produces a stable, parsimonious regime label that v1 misses (05-31, 05-54, 05-71)
A sticky HDP-HMM fit on XAU H4 returns + realized vol + RV-skew + DXY change will (i) select K=3-5 regimes data-drivenly, (ii) produce regime labels with lower transition-rate than vanilla HMM (avoiding rapid switching), and (iii) achieve OOS realized-R AUC ≥0.05 better than v1 swing classifier on H1→H2 OOS test set. Combined with bull/bear-sub-state hierarchy (05-71), this is the natural successor to v1 — and the architectural anchor for K54 v2.

### H-C: Self-normalized multivariate CUSUM on (XAU, US30, USDJPY) joint daily CR vector reduces S1 false-alarm rate by ≥30% (05-43)
A self-normalized CUSUM applied to a joint vector of per-instrument CR / WR / OB-continuation statistics, with weights chosen to maximize Lorden-criterion detection of joint regime shifts, will (i) detect regime shifts that single-asset univariate CUSUM misses (cross-asset contagion regime), (ii) reduce false-alarm rate at matched delay, and (iii) provide a single-knob upgrade to the existing CUSUM-candidate-rate-daily monitor without changing any production-trading code paths.

---

## 6. Cross-domain handoffs

| Topic | Handed off to | Rationale |
|-------|---------------|-----------|
| **Sequential-test machinery / inference theory** (sup-Wald, Wald, Robbins-Siegmund) | **02 statistical methodology** | Andrews 1993 sup-LR is foundational sequential inference; theory of sequential tests under unknown change point belongs in 02. |
| **Theoretical Markov chains** (HDP, Dirichlet processes, ergodic theory) | **01 math foundations** | Sticky HDP-HMM theory is Bayesian nonparametric; ergodicity / mixing of Markov chains is 01. |
| **Distribution-fit by regime** (fat tails, stylized facts) | **03 distributional characteristics** | If regime labels reveal regime-conditional fat-tail parameters, it's an empirical fact about distributions. |
| **Trading rules conditioned on detected regime** | **17 adaptive markets** or **14 trend / momentum** | A paper that *trades on* a regime detection is in 17/14, not 05. |
| **Multi-asset / portfolio regime-dependent allocation** | **13 cross-asset correlation / factors** or **21 risk management / Kelly** | Guidolin-Timmermann 2008 cross-listed; sticky-HDP-HMM allocation-applied → 13/21. |
| **Vol regime change-point** (between 05 and 16) | **16 vol regime trading** — but only when method's purpose is trading | Klaassen 2002 is on the cusp; we own the methodology, 16 owns the trade. |
| **Microstructure-regime BOCPD** (Tsaknaki-Lillo-Mazzarisi 2024) | **06 microstructure** cross-link | We own the detection, 06 owns the LOB-impact application. |
| **TDA-as-regime-detector** (Gidea-Katz; 05-70) | **04 multitimeframe / fractal / wavelets** cross-link | TDA features are fractal/topological decompositions; 04 owns the methodology, 05 owns the regime-detection use case. |
| **DCC + correlation-aware sizing** (05-75 Gerber) | **13 cross-asset correlation** owns; 05 cross-link only | Gerber statistic is correlation methodology; we cross-link because regime-conditioning is one robustness rationale. |
| **HMM in cryptocurrency** (05-67 Giudici; 05-74 GMM-VAR) | **20 RL/LLMs in trading** cross-link if used as RL state | If crypto HMM regime label feeds an RL agent, agent ownership goes to 20. |

**Worker rule applied:** "Detection method" → 05; "trades on detection" → 14/17/21. "MS-GARCH for vol forecasting" → 05 (ours: it's a MS detection method); "MS-GARCH calibrated for option pricing" → 16. "Order-flow CPD" → 05 if detection is the contribution, 06 if impact prediction is the contribution; in 05-42 both are contributions, so it goes to 05 with 06 cross-link.

---

## 7. Gaps and caveats

1. **Gold-specific regime literature is thin in top journals.** The most directly applicable empirical paper (05-52) is in a lower-tier journal with author identification I could not fully verify; treated as `seed candidate — verify before use`. The bulk of empirical regime-switching evidence is on equity (05-71, 05-68, 05-32, 05-24) or FX (05-22, 05-09). Gold-volatility MS papers exist but are scattered. Recommendation: run K52-style replication on gold daily/H1 data with the Hamilton 1989 / Klaassen 2002 / Haas-Mittnik-Paolella 2004 stack on GTOS data directly, rather than rely on second-hand empirical claims.

2. **Within-regime non-iid is a known weakness of vanilla BOCPD.** All financial returns within a regime are autocorrelated (volatility clustering, momentum effects). Adams-MacKay 2007 assumes iid within regime. The 2024 Tsaknaki-Lillo-Mazzarisi extension (05-41, 05-42) addresses this with score-driven within-regime dynamics — but the extension is recent and not yet widely adopted. Recommendation: if BOCPD is shipped, use the 05-41 score-driven extension, not vanilla.

3. **Spurious-regime risk is empirically real.** Kirby 2023 (05-64) gives a methodologically rigorous reason to suspect that 2-state MS fits on returns may be artifacts of fat tails, not evidence of regimes. K54 success criteria should include the null-test described above.

4. **Online deep-learning CPD is bleeding-edge and unvalidated on finance.** The 2024 JRSSB paper (05-49) is methodologically strong but applied predominantly to non-financial benchmarks. Caution: don't ship a DL-CPD into production on the strength of a JRSSB paper alone; require a 30-day shadow run on XAU first.

5. **HMM rigidity in HF / fast-moving regimes.** GMM-VAR (05-74) and crypto HF research suggest HMM transition-probability rigidity may underperform when regimes shift faster than the smoothed Hamilton filter assumes. For XAUUSD M15 (where regimes can shift within hours), this is a non-trivial caveat for the K54 architecture.

6. **No paper in this corpus directly tests OB-zone decay or trading-edge-decay on a per-instrument basis.** The literature gives the *methods* (CUSUM, BOCPD, Bai-Perron, Hansen threshold), not the *empirical fit* to GTOS data. The Phase 2 experiments (per-pair) are the GTOS-specific application of this domain literature.

7. **Topological data analysis (TDA) crosses domain 04 and 05.** The TDA-finance papers (05-55, 05-56, 05-70) are listed here because their *purpose* is regime/crash detection; the *methodology* (persistent homology, persistence landscapes) belongs in 04. Synthesis agents should route accordingly.

---

*Compiled 2026-04-28 by Phase 1 Worker #5 — Change-Point Detection + Regime Switching. Sources verified individually via WebSearch + WebFetch; non-verified entries flagged. UTF-8 encoded.*
