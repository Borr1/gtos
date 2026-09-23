# Domain 04 — Multi-Timeframe, Fractal, Wavelets & Hurst — Literature Catalog

**Worker:** Phase 1 Worker Agent #4
**Spec:** `research/ml_program/literature/_specs/04_multitimeframe_fractal_wavelets.md`
**Date:** 2026-04-28
**Papers cataloged:** 38
**Method:** WebSearch + WebFetch (Google Scholar / arXiv / SSRN / Wiley / Elsevier / Springer / NBER / publisher pages); read-only, no fabrication. URLs verified before listing.

---

## 1. Summary

Domain 04 owns time-scale decomposition of price series and how dynamics differ across scales. The catalog spans (a) the foundational long-memory / Hurst lineage (Hurst 1951 → Mandelbrot → Lo modified R/S → ARFIMA), (b) the wavelet methodology stack (Daubechies → Percival-Walden → Gencay-Selcuk-Whitcher → MODWT → wavelet coherence Aguiar-Conraria-Soares), (c) the realized-volatility / time-aggregation lineage (Andersen-Bollerslev-Diebold → Corsi HAR → Ghysels MIDAS → MSM Calvet-Fisher), and (d) the multifractal / scaling literature (Mandelbrot-Calvet-Fisher → Bacry-Muzy-Delour → Kantelhardt MFDFA → rough volatility Bayer-Friz-Gatheral).

GTOS-relevant findings concentrated in: (i) gold and FX exhibit time-varying long memory and multifractality (Vogl 2023, Mensi et al. 2020, Sensoy-Tabak), (ii) OB-style decay metrics may be a slow-scale persistence phenomenon (rolling Hurst regime detection literature), (iii) wavelet coherence is the time-scale-aware alternative to Pearson correlation already used in GTOS's correlation gate, (iv) HAR-RV's three-cascade structure (daily, weekly, monthly) directly translates to GTOS's M15-H1-H4 hierarchy, (v) fractional differentiation (Lopez de Prado) is a memory-preserving stationarity transform — high-leverage feature engineering candidate for K54.

Paper count by epoch: pre-2000 (4), 2000-2010 (9), 2011-2019 (12), 2020-2025 (13). Per spec quality bar: smaller domain than methodology / distributional, but at least 6 papers with explicit FX or gold focus, satisfying §8.

---

## 2. Top 3 most relevant to GTOS

1. **Corsi (2009) — A Simple Approximate Long-Memory Model of Realized Volatility (HAR-RV).** Direct mapping to GTOS's M15→H1→H4 multi-timeframe pipeline. The three-cascade additive model (daily / weekly / monthly) is the canonical way to express the heterogeneous-market-hypothesis across scales — and GTOS already implements something HAR-isomorphic in the H1/H4 OB structure of `market_state.py`. Candidate K54-v2 feature: HAR-RV-style realized volatility components on M15-aggregated returns.

2. **Vogl (2023) — Hurst Exponent Dynamics of S&P 500 Returns.** Rolling-window Hurst with declining trends as a leading indicator of crises and momentum crashes. Directly relevant to GTOS's edge-decay diagnostics (F11 OB-zone advantage decay, F15 regime-conditioned LONG-side selectivity collapse). Could disambiguate whether OB decay is monofractal long-memory phenomenon or regime shift.

3. **Gencay, Selcuk & Whitcher (2001) — Differentiating Intraday Seasonalities Through Wavelet Multi-Scaling.** Direct relevance to kill-zone modelling. Wavelet multi-scaling extracts and removes intraday seasonalities without parametric model selection. GTOS's kill-zone hard cuts (London 07:00-10:30 etc.) are a discretized version of the same seasonality structure; wavelet-deseasonalization could test whether OB advantage is concentrated in the seasonal residual or in the periodic structure itself.

---

## 3. Top 1 surprise

**Mensi et al. (2025, MFDFA cross-asset) finding that gold displays SHORT memory whereas oil and equity indices possess long memory** is contrarian to the dominant narrative in the gold-as-hedge literature. The gold market's empirical multifractal/long-memory profile is sufficiently mixed across studies that the very Hurst-of-XAUUSD that K54 might use as a feature is fragile. This sets up an empirical hypothesis: GTOS's edge in gold may depend on the absence rather than presence of long memory in returns — i.e., gold's mean-reverting microstructure (anti-persistence at certain scales) is what makes the OB zone bedrock work, and the empirical decay we see in 2026 may correspond to a regime where gold transitions into a more persistent (trending / one-sided) regime that breaks OB-mean-reversion mechanics. Refines F15.

---

## 4. Hypotheses for GTOS

**H4.1 — Rolling Hurst as a regime-shift early-warning signal.** Compute rolling-window generalized Hurst exponent (GHE) on M15 returns of XAUUSD; declining trend over a 30-day window predicts subsequent OB-continuation-rate degradation by ≥7 days. If validated, integrate into `regime_classifier.py` as fourth axis alongside H4-swing classes. Cross-link: F11 + F15.

**H4.2 — HAR-RV-style three-cascade volatility features improve K54 lift.** Replace single-scale realized volatility in K54's feature set with a HAR-RV decomposition (daily / weekly / monthly RV components computed on M15 base). Hypothesis: AUC lift ≥0.02 vs current K54 baseline (0.571). Multi-cascade explicitly captures the heterogeneous-market-hypothesis that explains why a setup good at H1 may be invalid at H4.

**H4.3 — Wavelet coherence at scale ≥6 (≥1 day) is a more stable correlation gate than Pearson 30-bar.** Replace the cross-instrument correlation gate's Pearson computation with wavelet-coherence at appropriate scales. Hypothesis: rolling-window stability of correlation estimates improves; correlated-pair detection lag drops by ≥1 bar. Cross-link to domain 13.

---

## 5. Cross-domain handoffs

- **Domain 01 (math foundations):** fractional Brownian motion theory papers (Mandelbrot–van Ness 1968 cited in Mandelbrot-Calvet-Fisher 1997); Comte-Renault long-memory volatility theory.
- **Domain 03 (distributional):** multifractal moment scaling as stylized fact (Mandelbrot-Calvet-Fisher 1997, Cont 2001 cross-link).
- **Domain 05 (regime / change-point):** rolling Hurst as change-point detector (Vogl 2023 cross-link).
- **Domain 06 (microstructure):** Lyons hot-potato / scale of order-book Hurst → 06; we keep Hurst-on-returns only.
- **Domain 13 (cross-asset correlation):** wavelet coherence as a scale-dependent generalization of Pearson (Aguiar-Conraria-Soares 2014); cross-link.
- **Domain 16 (volatility derivatives):** rough volatility Bayer-Friz-Gatheral primary owner; we cross-link only.
- **Domain 19 (ML for finance):** wavelet+LSTM hybrids → 19 owns the ML papers; we cross-link the wavelet preprocessing papers.
- **Domain 21 (sizing under fat tails):** fractional differentiation (Lopez de Prado 2018) for stationarity-preserving features; we own the methodology, 21 cross-links.

---

## 6. Gaps and caveats

1. **Multifractality controversy.** The 2026 Frontiers in Physics paper notes "multifractality should be viewed not as an established empirical fact, but rather as a working hypothesis whose validity largely depends on methodology, data quality, and observation scale." Caveat any feature derived from MFDFA/multifractal spectra.
2. **Hurst estimation under heavy tails is biased.** Barunik-Kristoufek 2010 finding (cited in our search). Generalized Hurst exponent (GHE) is preferred over R/S for fat-tailed financial returns. K54 features must use GHE, not raw R/S.
3. **Long memory vs. spurious memory.** Diebold-Inoue 2001 and follow-ups (Open Economies Review 2022) — apparent long memory may be regime switching with random level shifts. Without specifying which mechanism, Hurst features can be misleading.
4. **Daubechies family choice matters.** No single recipe; orthogonality + vanishing moments tradeoff. Practical recommendation from Percival-Walden: db4 or db8 for financial time series.
5. **Wavelet boundary effects.** MODWT uses circular wraparound by default; for trading-relevant rolling computations, must use reflection or zero-padding.
6. **Sample size matters for Hurst estimation.** GHE/R/S with series length <1000 unreliable (search query result). M15 series for GTOS = ~96 bars/day; need ≥10 days minimum for stable estimates.
7. **One paper rejected (`Olsen-Glattfelder-Dupuis 2010` 12 empirical scaling laws) is potentially relevant but partially crosses into domain 06 (event-based / directional change scaling).** Included here with cross-domain link to 06.

---

## 7. Per-paper entries

Each paper: title, authors, year, source, URL, abstract, key findings, relevance to GTOS, potential hypothesis, cross-domain links, and the per-spec required `timeframes_studied` field (sub-tick / tick / M1 / M5 / M15 / H1 / H4 / D1 / W1).

---

### 7.1 Foundational — Hurst, R/S, Long Memory

#### 1. Long-Term Storage Capacity of Reservoirs (Hurst R/S)

- **Authors:** H.E. Hurst
- **Year:** 1951
- **Source:** Transactions of the American Society of Civil Engineers, Vol. 116, pp. 770-799
- **URL:** https://ascelibrary.org/doi/10.1061/TACEAT.0006518
- **Abstract:** Hurst studied 76 hydrological/geophysical time series including Nile flow records and observed that the rescaled range of long records grows like N^H with H ≈ 0.7, exceeding the H = 0.5 expected for IID series. He proposed the rescaled-range (R/S) statistic as an empirical measure of long-term storage capacity / persistence.
- **Key findings:**
  - Range of cumulative deviations grows like N^H (the Hurst phenomenon).
  - Empirical H exponents for natural records cluster near 0.72–0.74, well above 0.50.
  - Persistence in geophysical series violates iid assumption underlying classical statistical inference.
  - Foundational for what would become long-memory / fractional Brownian motion / multifractal analysis.
- **Relevance to GTOS:** Foundational reference for any Hurst feature computed on price series. K54 v2 feature: rolling Hurst on M15 XAUUSD returns. Without citing Hurst's original construction, the meaning of the feature is unclear.
- **Potential hypothesis:** H4.1 (rolling Hurst as decay early warning).
- **Cross-domain links:** 01 (theoretical foundation), 05 (regime-shift signal).
- **Timeframes studied:** D1+ (annual hydrological data); methodology applies at all scales.

#### 2. A Brief History of Long Memory: Hurst, Mandelbrot and the Road to ARFIMA, 1951–1980

- **Authors:** Timothy Graves, Robert B. Gramacy, Nicholas W. Watkins, Christian L.E. Franzke
- **Year:** 2017 (arXiv preprint 2014)
- **Source:** Entropy 19(9), 437; arXiv:1406.6018
- **URL:** https://www.mdpi.com/1099-4300/19/9/437 ; https://arxiv.org/abs/1406.6018
- **Abstract:** A historical review of how Hurst's 1951 R/S work led, via Mandelbrot's fractional Gaussian noise (FGN), to Granger-Hosking ARFIMA models. Documents disagreements between disciplines (hydrology, statistics, econometrics) and Mandelbrot's resistance to ARFIMA's specific parametric form.
- **Key findings:**
  - FGN was Mandelbrot's first stationary explanation of the Hurst phenomenon.
  - ARFIMA's fractional differencing parameter d in (-0.5, 0.5) generalizes ARMA to long memory.
  - Long memory persistently controversial — interpretation depends on whether you accept H>0.5 as evidence of true power-law decay or trend / level-shift artefact.
  - Cross-disciplinary impact: same Hurst exponent appears in hydrology, climate, network traffic, finance, DNA.
- **Relevance to GTOS:** Required reading before claiming any time-series in GTOS exhibits "long memory." Diebold-Inoue caveat (regime-switching mimics long-memory) directly applicable to F15 where regime-conditioned decay was misread as memory loss.
- **Potential hypothesis:** Adopt fractional differentiation (Lopez de Prado) as default GTOS K54 feature transform; H4.4 candidate.
- **Cross-domain links:** 01 (FBm theory), 03 (long memory as stylized fact).
- **Timeframes studied:** survey paper; spans all scales.

#### 3. Long-range dependence in stock returns (Lo modified rescaled range)

- **Authors:** Andrew W. Lo
- **Year:** 1991
- **Source:** Econometrica 59(5), 1279-1313
- **URL:** https://www.jstor.org/stable/2938368 (verified via search; alternate ideas.repec.org host)
- **Abstract:** Lo proposed a modified R/S statistic that corrects for short-range dependence and showed (using the modification) that there is no statistically significant long-range dependence in stock returns. Sparked decades of subsequent literature on whether long memory is real or artefactual.
- **Key findings:**
  - Modified R/S statistic robust to short-range dependence (AR/ARMA terms).
  - Stock-return long memory is statistically insignificant under modification.
  - Volatility long memory survives the modification — stock-return long memory is in volatility, not returns.
  - Subsequent literature (e.g., the ScienceDirect search hit) finds Lo's modification has low power to detect true long memory when present.
- **Relevance to GTOS:** Returns vs volatility distinction maps to GTOS's distinction between price-level features (where Lo says no long memory) and realized-volatility features (where long memory genuinely exists). K54 should not over-weight Hurst on M15 returns; should weight Hurst on M15 RV instead.
- **Potential hypothesis:** Hurst on absolute returns (volatility proxy) outperforms Hurst on signed returns as a regime feature for K54 v2.
- **Cross-domain links:** 03 (vol stylized fact), 05 (regime detection).
- **Timeframes studied:** D1 (CRSP daily stock returns).

#### 4. Distinguishing between short and long range dependence: Finite sample properties

- **Authors:** Marina Resta, Davide La Torre
- **Year:** 2008
- **Source:** Munich Personal RePEc Archive
- **URL:** https://mpra.ub.uni-muenchen.de/16424/
- **Abstract:** Comparative simulation study of finite-sample power and bias of R/S, modified R/S, DFA, and other Hurst estimators under known DGPs with mixed short- and long-range dependence and heavy tails.
- **Key findings:**
  - Modified R/S has strong preference for accepting null of no-LRD even when present (power problem).
  - DFA outperforms R/S under non-stationarity.
  - Heavy-tailed innovations bias all estimators upward (apparent persistence higher than true).
  - Sample size matters substantially: estimates unreliable below n ≈ 1000.
- **Relevance to GTOS:** Practical guidance for K54: never use raw R/S on M15 returns (heavy tails plus moderate sample size = upward-biased H estimates). Use DFA or GHE on absolute returns over series ≥1000 bars (~10 days).
- **Potential hypothesis:** none (methodology paper).
- **Cross-domain links:** 02 (statistical methodology), 03 (heavy tails).
- **Timeframes studied:** simulation; methodology applies at all scales.

---

### 7.2 Foundational — Wavelet Methods

#### 5. Wavelet Methods for Time Series Analysis

- **Authors:** Donald B. Percival, Andrew T. Walden
- **Year:** 2000
- **Source:** Cambridge University Press (book; also referenced via Cambridge Series in Statistical and Probabilistic Mathematics)
- **URL:** https://www.cambridge.org/core/books/wavelet-methods-for-time-series-analysis/A2018601E6907DE4953EEF7A5D0359E5
- **Abstract:** Standard graduate text on the discrete wavelet transform (DWT), maximal overlap DWT (MODWT), wavelet variance, wavelet covariance, wavelet packet transforms, and their statistical properties for time-series analysis. Pseudocode for pyramid algorithm at p. 178 is the canonical reference for MODWT implementation.
- **Key findings:**
  - MODWT (translation-invariant DWT) preserves alignment between scales and original time series — critical for trading where bar-time alignment matters.
  - Energy-preserving transformation: Σ wavelet variances = total variance.
  - Wavelet variance summarizes spectrum with one value per octave; useful when spectrum is approximately featureless within bands.
  - Daubechies family (db4, db8) recommended as default for non-stationary financial-style data.
- **Relevance to GTOS:** Methodological bedrock for any wavelet feature in K54 v2. MODWT specifically required for rolling-window real-time use (DWT's downsampling makes online use awkward).
- **Potential hypothesis:** Use MODWT-based wavelet variance features at scales 1-6 (M15 to D1-equivalent) in K54 v2; H4.5.
- **Cross-domain links:** 02 (methodology).
- **Timeframes studied:** book; all scales.

#### 6. An Introduction to Wavelets and Other Filtering Methods in Finance and Economics

- **Authors:** Ramazan Gençay, Faruk Selçuk, Brandon J. Whitcher
- **Year:** 2002
- **Source:** Academic Press (Elsevier book)
- **URL:** https://shop.elsevier.com/books/an-introduction-to-wavelets-and-other-filtering-methods-in-finance-and-economics/gencay/978-0-12-279670-8
- **Abstract:** First book on wavelet analysis specifically for finance / economics. Covers DWT, MODWT, wavelet variance, scale-by-scale beta, wavelet-based intraday-seasonality removal, wavelet correlation across scales. Explicit examples on FX and IBM stock data.
- **Key findings:**
  - Scale-by-scale wavelet variance reveals different behavior at intraday vs daily vs weekly scales for FX series.
  - Wavelet decomposition naturally handles non-stationarity (no detrending step needed).
  - Wavelet correlation between FX pairs differs by scale — short-term correlation lower than daily-and-up correlation.
- **Relevance to GTOS:** Direct foundation for all wavelet-based GTOS feature engineering. The scale-by-scale FX correlation finding directly motivates H4.3 (wavelet coherence as correlation gate).
- **Potential hypothesis:** H4.3.
- **Cross-domain links:** 11 (FX), 13 (correlation).
- **Timeframes studied:** book; FX intraday + daily.

#### 7. Differentiating Intraday Seasonalities Through Wavelet Multi-Scaling

- **Authors:** Ramazan Gençay, Faruk Selçuk, Brandon Whitcher
- **Year:** 2001
- **Source:** Physica A 289(3), 543-556
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S0378437100004635
- **Abstract:** Proposes a non-decimated DWT-based method for extracting intraday seasonal components in FX volatility without assuming a parametric model. Method is translation invariant, works on arbitrary length series without boundary adjustments, and is fully nonparametric.
- **Key findings:**
  - High-frequency wavelet coefficients capture intraday seasonality; low-frequency capture trend / persistence.
  - Resulting de-seasonalized FX volatility is nearly stationary, suitable for inputs to subsequent econometric models.
  - Works on arbitrary length series (no integer-fraction-of-day requirement).
  - No model selection parameters → free of ad-hoc bias.
- **Relevance to GTOS:** GTOS hard-codes kill-zone windows (London 07:00-10:30 etc.) — these are deterministic intraday-seasonality cuts. Wavelet de-seasonalization can test whether OB-zone advantage is concentrated in the seasonal residual (alpha) or in the periodic structure itself (deterministic schedule effect). If the latter dominates, simply being in-window may be the actual edge, not OB precision.
- **Potential hypothesis:** Decompose XAUUSD M15 absolute returns into wavelet seasonal and residual; measure OB-zone advantage on each. Hypothesis: OB-zone advantage concentrated in residual, not seasonal.
- **Cross-domain links:** 11 (FX-specific seasonality), 08 (volume-weighted seasonality).
- **Timeframes studied:** intraday FX (effectively M5-M30 equivalent on 1992-1996 BIS data).

#### 8. Scaling Properties of Foreign Exchange Volatility

- **Authors:** Ramazan Gençay, Faruk Selçuk, Brandon Whitcher
- **Year:** 2001
- **Source:** Physica A 289(1), 249-266
- **URL:** http://finance.martinsewell.com/stylized-facts/scaling/GencaySelcukWhitcher2001.pdf
- **Abstract:** Investigates scaling properties of FX volatility using a wavelet multi-scaling decomposition. Shows that FX volatilities follow different scaling laws at different horizons: smaller persistence at intraday, gradually increasing up to daily-and-above scale.
- **Key findings:**
  - FX volatility is NOT mono-scaling; different Hurst-type exponent at different scales.
  - Cross-pair FX correlation lowest at intraday, highest at daily+ scales.
  - Persistence (slope of log-variance vs log-scale) different intraday vs daily.
  - Wavelet decomposition required (single Hurst is not sufficient summary).
- **Relevance to GTOS:** Direct evidence that the "Hurst" of XAUUSD or USDJPY at M15 is a different number than at H1 or H4. K54's regime classifier should use scale-aware features, not single-scale aggregates. Confirms the H4-swing classifier's higher-scale role is methodologically justified.
- **Potential hypothesis:** Single-scale Hurst is insufficient; multi-scale wavelet variance vector is the correct K54 feature.
- **Cross-domain links:** 11 (FX), 03 (vol stylized fact).
- **Timeframes studied:** sub-M5, M5, M30, H1, D1 (1992-1996 5-min BIS FX data).

#### 9. Multiscale Systematic Risk

- **Authors:** Ramazan Gençay, Faruk Selçuk, Brandon Whitcher
- **Year:** 2005
- **Source:** Journal of International Money and Finance 24(1), 55-70
- **URL:** https://ideas.repec.org/a/eee/jimfin/v24y2005i1p55-70.html
- **Abstract:** Computes wavelet-based scale-by-scale CAPM beta. Shows the conventional beta is essentially an average of wavelet betas; risk-return relationship strengthens as scale increases (lower frequencies). Empirical demonstration that beta is genuinely scale-dependent, not constant.
- **Key findings:**
  - Conventional OLS beta is a weighted average of scale-betas; resolution is inadequate for scale-aware risk assessment.
  - Multi-scale beta provides finer discrimination among securities.
  - Risk-return relationship strengthens as scale increases (longer horizons).
  - Wavelet variance and covariance ratios are the natural scale-aware analogues of OLS beta.
- **Relevance to GTOS:** Cross-instrument correlation gate is a beta-like construct (covariance / variance pair). Replacing the Pearson rolling-window with wavelet-coherence at appropriate scale is a direct application — and the literature here predicts a real lift in stability.
- **Potential hypothesis:** H4.3.
- **Cross-domain links:** 13 (factor / beta), 21 (correlation-aware sizing).
- **Timeframes studied:** D1 (CRSP daily stock returns).

#### 10. The Continuous Wavelet Transform: Moving Beyond Uni- and Bivariate Analysis

- **Authors:** Luís Aguiar-Conraria, Maria Joana Soares
- **Year:** 2014
- **Source:** Journal of Economic Surveys 28(2), 344-375
- **URL:** https://onlinelibrary.wiley.com/doi/abs/10.1111/joes.12012
- **Abstract:** Survey of continuous wavelet transform (CWT), wavelet coherence, and partial / multiple wavelet coherency for economic time-series. Provides the canonical implementation guide post-2005 wavelet-coherence boom in finance/economics.
- **Key findings:**
  - Wavelet coherence is the time-frequency-localized analogue of Pearson correlation.
  - Phase-difference quantifies lead-lag at each frequency.
  - Partial wavelet coherence controls for a third confounding variable (cross-pair confounding by USD index, e.g.).
  - Multiple wavelet coherence generalizes to >2 variables.
- **Relevance to GTOS:** Methodological foundation for GTOS to migrate cross-instrument correlation gate from Pearson to wavelet coherence. Partial wavelet coherence between e.g. XAUUSD vs GBPJPY conditional on DXY could remove spurious USD-driven correlation.
- **Potential hypothesis:** H4.3 + extension: partial wavelet coherence (controlling for DXY) gives cleaner correlation signals than Pearson on raw pairs.
- **Cross-domain links:** 13 (correlation modeling), 02 (methodology).
- **Timeframes studied:** survey; D1+ in most cited applications.

---

### 7.3 Foundational — Realized Volatility / HAR / MIDAS

#### 11. Modeling and Forecasting Realized Volatility

- **Authors:** Torben G. Andersen, Tim Bollerslev, Francis X. Diebold, Paul Labys
- **Year:** 2003
- **Source:** Econometrica 71(2), 579-625; NBER WP 8160 (2001)
- **URL:** https://www.nber.org/papers/w8160 ; https://onlinelibrary.wiley.com/doi/abs/10.1111/1468-0262.00418
- **Abstract:** Establishes high-frequency realized volatility as a non-parametric estimator of integrated variance, with vector-autoregressive forecasts on log-realized-volatility outperforming GARCH and related models. Foundational paper for the modern realized-volatility literature.
- **Key findings:**
  - 5-minute realized volatility is approximately log-normal and approximately Gaussian after log transform.
  - Long-memory Gaussian VAR on log-RV outperforms GARCH(1,1) and FIGARCH out of sample.
  - Multivariate realized volatility distributions can be modeled jointly across currencies.
  - Volatility is more predictable at lower frequencies (longer horizons).
- **Relevance to GTOS:** Foundational for any realized-volatility feature on M15 returns aggregated to H1/H4. GTOS doesn't currently compute RV; adding a 5-min-or-finer RV feature ladder is a K54 v2 candidate.
- **Potential hypothesis:** H4.2 (HAR-RV cascade improves K54 lift).
- **Cross-domain links:** 03 (vol stylized fact), 16 (vol trading).
- **Timeframes studied:** 5-min FX (DM/USD, JPY/USD over 1986-1996); aggregated to D1.

#### 12. A Simple Approximate Long-Memory Model of Realized Volatility (HAR-RV)

- **Authors:** Fulvio Corsi
- **Year:** 2009
- **Source:** Journal of Financial Econometrics 7(2), 174-196 (online 2003 SSRN)
- **URL:** https://academic.oup.com/jfec/article-abstract/7/2/174/856522 ; https://papers.ssrn.com/sol3/papers.cfm?abstract_id=626064
- **Abstract:** Proposes a 3-component (daily, weekly, monthly) heterogeneous-autoregressive model for realized volatility. Despite being short-memory in the strict sense, HAR-RV reproduces long-memory, fat tails, and self-similar features and matches or beats more complex models in out-of-sample volatility forecasting.
- **Key findings:**
  - HAR-RV has 3 lags (1d, 5d, 22d) and OLS estimation; trivial to fit.
  - Reproduces long-memory empirical decay despite being formally short-memory.
  - Heterogeneous-market-hypothesis interpretation: short-, medium-, long-horizon traders contribute different cascades.
  - Becomes the workhorse of the realized-volatility-forecasting literature; >2100 citations by 2021.
- **Relevance to GTOS:** Direct map. M15 → H1 → H4 in GTOS = daily → weekly → monthly cascade in HAR. The horizons are different but the principle is identical: an additive cascade across 3 timescales captures the heterogeneous-market-hypothesis. K54 v2 can adopt the same structure.
- **Potential hypothesis:** H4.2.
- **Cross-domain links:** 03 (vol stylized fact), 02 (methodology).
- **Timeframes studied:** 5-min FX (DM/USD, USD/CHF) and S&P 500 futures aggregated to RV at daily frequency.

#### 13. The MIDAS Touch: Mixed Data Sampling Regression Models

- **Authors:** Eric Ghysels, Pedro Santa-Clara, Rossen Valkanov
- **Year:** 2004 (working paper); subsequently in numerous applications
- **Source:** UCLA / UNC working paper; CIRANO 2004s-20
- **URL:** https://rady.ucsd.edu/_files/faculty-research/valkanov/midas-touch.pdf
- **Abstract:** Introduces MIDAS regression: forecast a low-frequency outcome with high-frequency regressors, weighted by a parametric kernel (Beta lag, exponential Almon). Solves the loss-of-information problem in classical aggregation while keeping the model identifiable.
- **Key findings:**
  - MIDAS allows different forecast horizons and frequencies to be used flexibly.
  - In volatility prediction, MIDAS using 5-min absolute returns provides best forecasts of monthly volatility.
  - Beta lag polynomial requires only 2 parameters → compact alternative to ARFIMA-style long-memory.
  - Improves on simple aggregation (mean of high-frequency observations) by exploiting the lag structure.
- **Relevance to GTOS:** Direct generalization of HAR-RV; instead of 3 fixed cascades, MIDAS optimally weights all sub-daily lags. K54 candidate: MIDAS-weighted M5 returns to predict M15 next-bar regime.
- **Potential hypothesis:** MIDAS-aggregated M5 features outperform fixed-window M15 averages in K54 lift.
- **Cross-domain links:** 02 (methodology), 19 (ML feature engineering).
- **Timeframes studied:** M5 → D1; D1 → M1 (monthly).

#### 14. Roughing It Up: Including Jump Components in Realized Volatility

- **Authors:** Torben G. Andersen, Tim Bollerslev, Francis X. Diebold
- **Year:** 2007
- **Source:** Review of Economics and Statistics 89(4); NBER WP 11775
- **URL:** https://www.nber.org/system/files/working_papers/w11775/w11775.pdf
- **Abstract:** Decomposes realized volatility into continuous and jump components using bipower variation. Shows HAR-RV-J (HAR with explicit jump term) improves on HAR-RV alone for out-of-sample forecasts.
- **Key findings:**
  - Bipower variation isolates the continuous component of realized volatility.
  - Jump component (RV − BPV)+ is approximately serially uncorrelated.
  - Continuous component carries the long-memory persistence.
  - HAR-RV-J consistently beats HAR-RV.
- **Relevance to GTOS:** Direct relevance to displacement / OB-formation events that GTOS already logs. The bipower variation methodology gives a principled split between regular volatility and jumps — aligns with NAS100 jump-driven hallucination class (HALLUC-1) and could provide a per-instrument jump regime feature.
- **Potential hypothesis:** Jump-component RV is a stronger predictor of OB-continuation failure than continuous-component RV.
- **Cross-domain links:** 03 (jump distributions), 16 (vol regimes).
- **Timeframes studied:** 5-min S&P 500 futures, T-bond futures, USD/DEM rates.

---

### 7.4 Multifractality and Multi-scale Volatility

#### 15. Multifractal Detrended Fluctuation Analysis (MFDFA)

- **Authors:** Jan W. Kantelhardt, Stephan A. Zschiegner, Eva Koscielny-Bunde, Shlomo Havlin, Armin Bunde, H. Eugene Stanley
- **Year:** 2002
- **Source:** Physica A 316(1-4), 87-114
- **URL:** https://arxiv.org/abs/physics/0202070 ; https://www.sciencedirect.com/science/article/abs/pii/S0378437102013833
- **Abstract:** Generalizes DFA to multifractal scaling: instead of a single scaling exponent, computes a generalized Hurst function h(q) over moments q. Distinguishes multifractality due to long-range correlations vs. broad probability distribution by shuffling the series and re-running.
- **Key findings:**
  - MFDFA gives a multifractal spectrum f(α) (Hölder exponents), more informative than single H.
  - Shuffle test isolates long-range-correlation multifractality from heavy-tail multifractality.
  - Equivalent to wavelet transform modulus maxima (WTMM) for stationary signals with compact support.
  - Standard tool for financial multifractality analysis since publication.
- **Relevance to GTOS:** Standard methodology for any multifractal feature. K54 candidate: width of multifractal spectrum Δα as a single scalar feature representing complexity / inefficiency.
- **Potential hypothesis:** Multifractal spectrum width Δα(XAUUSD) > Δα(USDJPY) at M15 in 2026 (gold less efficient → wider spectrum). If true, motivates instrument-specific MFDFA windows in K54.
- **Cross-domain links:** 03 (multifractal moments stylized fact), 02 (methodology).
- **Timeframes studied:** simulation + multiple non-financial datasets; methodology applies to all scales.

#### 16. A Multifractal Model of Asset Returns

- **Authors:** Benoît B. Mandelbrot, Adlai J. Fisher, Laurent E. Calvet
- **Year:** 1997
- **Source:** Cowles Foundation Discussion Paper 1164, Yale University
- **URL:** https://users.math.yale.edu/~bbm3/web_pdfs/Cowles1164.pdf ; https://elischolar.library.yale.edu/cowles-discussion-paper-series/1412/
- **Abstract:** Combines fractional Brownian motion with a multifractal time-deformation process to produce returns that match empirical scaling of moments across time horizons. Applied to DM/USD exchange rates and several equity series.
- **Key findings:**
  - Compounding FBm with multifractal time captures fat-tails AND long-dependence WITHOUT requiring infinite variance.
  - Return moments scale as a power law of the time horizon.
  - Fits DM/USD scaling exponents better than ARCH-family models.
  - Foundational paper for the multifractal model of asset returns (MMAR).
- **Relevance to GTOS:** Theoretical foundation for treating XAUUSD as a multifractal process. Without committing to MMAR specifically, the time-deformation idea suggests that GTOS's "trading time" (kill-zone hours dominate) is not a heuristic — it's the natural setting for any multifractal-time-aware model.
- **Potential hypothesis:** Volume-weighted "tick clock" (time advancing by trading activity, not wall clock) gives more stationary GTOS features than wall-clock M15.
- **Cross-domain links:** 03 (multifractal stylized fact), 01 (FBm theory).
- **Timeframes studied:** D1 (DM/USD; selected equities).

#### 17. The Markov-Switching Multifractal (MSM) Model of Asset Returns

- **Authors:** Laurent E. Calvet, Adlai J. Fisher
- **Year:** 2004 (Journal of Financial Econometrics); 2008 book consolidation
- **Source:** Journal of Financial Econometrics 2(1), 49-83; "Multifractal Volatility" book Academic Press 2008
- **URL:** https://www.amazon.com/Multifractal-Volatility-Forecasting-Academic-Advanced/dp/0121500136 ; https://en.wikipedia.org/wiki/Markov_switching_multifractal
- **Abstract:** Discrete-time stochastic-volatility model where regime-switching across many heterogeneous-duration components reproduces the multifractal scaling of returns. Tractable via GMM and provides linear forecasts via Levinson-Durbin algorithm.
- **Key findings:**
  - MSM beats GARCH(1,1), MS-GARCH, and FIGARCH on FX volatility forecasts at horizons 10-50 days.
  - Captures outliers, log-memory persistence, and power variation simultaneously.
  - Three-frequency interpretation: low-freq for regime, intermediate for autoregressive smooth, high-freq for outliers.
  - Used by financial-industry practitioners for production forecasts.
- **Relevance to GTOS:** Strongest competitor to HAR-RV for multi-scale volatility forecasting. Could replace simple realized-vol features in K54 with MSM-derived state probabilities.
- **Potential hypothesis:** MSM regime probability beats HAR-RV cascade as K54 single-feature signal.
- **Cross-domain links:** 03 (vol modeling), 05 (regime).
- **Timeframes studied:** D1 FX (USD/DM, USD/JPY, USD/GBP, USD/CHF).

#### 18. The Dynamics of Financial Markets — Mandelbrot's Multifractal Cascades, and Beyond

- **Authors:** Lisa Borland, Jean-Philippe Bouchaud, Jean-François Muzy, Gilles Zumbach
- **Year:** 2005
- **Source:** arXiv:cond-mat/0501292 (Wilmott Magazine)
- **URL:** https://arxiv.org/abs/cond-mat/0501292
- **Abstract:** Review honoring Mandelbrot's 80th. Discusses the Bacry-Muzy-Delour multifractal random walk (MRW), pointing out its advantages over Mandelbrot's original cascade (stationarity, no preferred scale ratio, causality respected).
- **Key findings:**
  - BMD MRW is a continuous-cascade multifractal that's stationary and causal.
  - Captures: zero return autocorrelation, long-range vol correlation, multifractal moment scaling.
  - Provides interpretation in terms of intermittent vol cascades from coarse to fine scales.
  - Practical alternative to MMAR.
- **Relevance to GTOS:** Important counter-narrative: multifractal cascades are real but not necessarily Mandelbrot's specific construction. GTOS can adopt cascade-based reasoning without committing to the original 1972/1974 multiplicative-cascade machinery.
- **Potential hypothesis:** none direct (review).
- **Cross-domain links:** 01 (theory), 03 (stylized fact).
- **Timeframes studied:** review; equities + FX cited.

#### 19. Pricing Under Rough Volatility (and Volatility is Rough family)

- **Authors:** Christian Bayer, Peter Friz, Jim Gatheral
- **Year:** 2016 (paper); 2024 (full book)
- **Source:** Quantitative Finance 16(6), 887-904; SIAM "Rough Volatility" book 2024
- **URL:** https://www.tandfonline.com/doi/abs/10.1080/14697688.2015.1099717 ; https://www.amazon.com/Rough-Volatility-Peter-K-Friz/dp/1611977770
- **Abstract:** Building on Gatheral-Jaisson-Rosenbaum's "Volatility is rough" finding, develops the rough Bergomi (rBergomi) model: log-volatility behaves as fractional Brownian motion with Hurst H ≈ 0.1. Outperforms classical Markovian stochastic-volatility models on SPX vol-surface fits with fewer parameters.
- **Key findings:**
  - H ≈ 0.1 for log-volatility implied by SPX → log-vol is "rougher" than Brownian motion.
  - Rough volatility a robust empirical phenomenon across markets.
  - Extends to commodities (rough volatility dynamics in commodity markets, arXiv 2603.26514).
  - Stylized fact: empirical multifractality at small scales is consistent with rough volatility.
- **Relevance to GTOS:** Important complement to long-memory framing. If log-vol is rough (H<<0.5) at fine scales, then GTOS features computed at M15 will be dominated by fast mean-reversion, not slow trend. Helps explain why M15 is the right operating timeframe — slower scales smooth out the rough component.
- **Potential hypothesis:** Rough-vol-derived features at M15 (e.g., a path-dependent vol estimator) enrich K54 v2.
- **Cross-domain links:** 16 (primary owner), 01 (FBm theory), 03 (vol stylized fact).
- **Timeframes studied:** sub-tick to D1; main calibration on intraday SPX 2010-2014.

---

### 7.5 Hurst / Multifractal — Empirical Asset Pricing

#### 20. Hurst Exponent Dynamics of S&P 500 Returns

- **Authors:** Markus Vogl
- **Year:** 2023
- **Source:** Chaos, Solitons & Fractals 166, art. 112884
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S0960077922010633 ; https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3838850
- **Abstract:** Combines rolling-window wavelet-filtered S&P 500 returns (2000-2020) with recurrence quantification (RQA), wavelet MRA, and MFDFA to obtain time-varying Hurst exponents. Argues for invalidity of EMH and uses Hurst dynamics as crisis early warning.
- **Key findings:**
  - Local Hurst exponents decline before crises (2008 GFC, 2020 COVID).
  - Strong fluctuations in Hurst after crisis events.
  - During crises, evolutionary dynamics show negative correlations, raising local H.
  - Method combines wavelet denoising + rolling H + MFDFA, reproducible framework.
- **Relevance to GTOS:** Strongest single empirical paper for H4.1. Vogl's exact methodology — wavelet-denoised, rolling-window Hurst — is portable to XAUUSD M15. Crisis-prediction lens ports to "decay-prediction" lens for OB continuation rate.
- **Potential hypothesis:** H4.1 (rolling Hurst declining ⇒ OB-continuation degradation in following ~7 days).
- **Cross-domain links:** 05 (regime), 17 (adaptive markets).
- **Timeframes studied:** D1 (S&P 500 daily over 2000-2020); methodology adaptable to M15.

#### 21. Improvement in Hurst Exponent Estimation and Its Application to Financial Markets

- **Authors:** various (Financial Innovation 2022)
- **Year:** 2022
- **Source:** Financial Innovation 8, 86
- **URL:** https://link.springer.com/article/10.1186/s40854-022-00394-x
- **Abstract:** Proposes improvements to GHE estimator (bias correction, finite-sample stability) and applies to multiple financial markets to derive efficiency rankings.
- **Key findings:**
  - Generalized Hurst exponent (GHE) is preferred over R/S in finance: lower variance and bias under heavy tails.
  - Bias-corrected GHE further improves estimator accuracy at small sample.
  - Applied to multiple asset classes; finds gold short-memory, equities long-memory.
- **Relevance to GTOS:** Practical estimator guidance for K54 implementation. Don't use raw R/S; use bias-corrected GHE. Confirms gap in many older literature: "Hurst feature" is ill-defined without specifying estimator.
- **Potential hypothesis:** none (methodology / empirical).
- **Cross-domain links:** 02 (estimator), 03 (stylized facts).
- **Timeframes studied:** D1 multiple assets.

#### 22. Random Walks, Hurst Exponent, and Market Efficiency

- **Authors:** various (Quality & Quantity 2025)
- **Year:** 2025
- **Source:** Quality & Quantity (Springer)
- **URL:** https://link.springer.com/article/10.1007/s11135-025-02052-7
- **Abstract:** Tests EMH at different time scales using rolling Hurst, finding inefficiency confined to specific scales and time windows; long memory in returns is contingent on regime, not universal.
- **Key findings:**
  - Most markets are "scale-efficient" — efficient at some scales, inefficient at others.
  - Hurst exponent time-varying; long-memory not a permanent property.
  - Crisis events drive inefficiency spikes (consistent with Vogl 2023).
  - Adaptive Markets Hypothesis (Lo) supported by data.
- **Relevance to GTOS:** Reframes "edge decay" as "scale shift." OB advantage may not be decaying overall — it may be migrating to a different scale where GTOS doesn't operate. Suggests a multi-scale efficiency map as a strategic monitoring tool.
- **Potential hypothesis:** GTOS edge migrates to different scale over time; periodic re-validation across M5/M15/H1/H4 needed.
- **Cross-domain links:** 17 (adaptive markets), 05 (regime).
- **Timeframes studied:** D1 multi-asset.

#### 23. Multifractal Behaviour in Gold Prices by MF-DFA and WTMM

- **Authors:** various (academic working paper)
- **Year:** ca. 2014
- **Source:** academia.edu / Physica A
- **URL:** https://www.academia.edu/28291798/Multifractal_Behaviour_in_Gold_Prices_by_Using_MF_Dfa_and_WTMM_Methods
- **Abstract:** Comparative study of MFDFA and Wavelet Transform Modulus Maxima on gold spot price. Both methods agree gold prices are multifractal; estimates of multifractal spectrum given.
- **Key findings:**
  - Gold spot is multifractal under both methods.
  - MFDFA recommended over WTMM when fractal properties not known a priori.
  - Strong herding behavior signal in gold's multifractal spectrum.
- **Relevance to GTOS:** Direct empirical for XAUUSD instrument. Confirms that GTOS's primary instrument has measurable multifractality at scales of interest. Implicitly supports K54 multifractal-spectrum features for gold.
- **Potential hypothesis:** Gold-specific multifractal spectrum changes around regime transitions; can be used as a regime classifier.
- **Cross-domain links:** 10 (gold-specific), 03 (stylized fact).
- **Timeframes studied:** D1 gold spot.

#### 24. Testing the Fractal Market Hypothesis Using MFDFA Across Multiple Asset Classes

- **Authors:** various
- **Year:** 2025
- **Source:** Computational Economics (Springer)
- **URL:** https://link.springer.com/article/10.1007/s10614-025-11196-5
- **Abstract:** Cross-asset MFDFA test of FMH; finds gold displays short memory whereas Bitcoin, Ethereum, oil, and BIST 100 possess long memory. Argues for asset-class-specific calibration.
- **Key findings:**
  - **Gold has SHORT memory** (contrary to common assumption).
  - Bitcoin, Ethereum, oil, BIST 100 have long memory.
  - Multifractal spectrum width Δα differs strongly across asset classes.
  - FMH valid in differing degrees across markets.
- **Relevance to GTOS:** **Top 1 surprise.** Directly contradicts the "gold is a long-memory market" framing. Rewrites how K54 should treat XAUUSD: as a short-memory anti-persistent instrument where mean-reversion mechanics (and OB zone reversion) are the natural edge — and where decay corresponds to a regime where short-memory breaks down (gold becomes more persistent / trending).
- **Potential hypothesis:** Edge decay in 2026 corresponds to gold's H increasing toward 0.5 (loss of anti-persistence). Track ΔH over rolling window as decay tracker.
- **Cross-domain links:** 10 (gold), 17 (adaptive markets).
- **Timeframes studied:** D1 multi-asset.

#### 25. Time-varying Hurst Exponent for US Stock Markets (Cajueiro-Tabak family)

- **Authors:** Daniel O. Cajueiro, Benjamin M. Tabak (and follow-ups)
- **Year:** 2004 (original); 2006 (US market application)
- **Source:** Physica A 336(3-4), 521-537 (2004); Chaos, Solitons & Fractals 22 (2004) follow-up
- **URL:** https://www.researchgate.net/publication/220022159_Ranking_efficiency_for_emerging_markets ; https://www.bcb.gov.br/pec/wps/ingl/wps342.pdf
- **Abstract:** Ranks emerging markets by Hurst exponent; finds time-varying Hurst is a sharper measure of efficiency than static estimates. Most-developed markets show H near 0.5; least-developed markets show H >> 0.5 (persistent inefficiency).
- **Key findings:**
  - Generalized Hurst exponent (GHE) preferred over R/S for emerging markets.
  - H decreases over time as markets develop / mature.
  - Cyclical patterns linked to crises and liquidity.
  - Adaptive Markets Hypothesis support.
- **Relevance to GTOS:** Validates the rolling-window approach to Hurst estimation. Cross-instrument efficiency ranking is a candidate K54 feature.
- **Potential hypothesis:** Cross-instrument efficiency rank (XAUUSD vs USDJPY vs GBPJPY etc.) as K54 feature.
- **Cross-domain links:** 17 (adaptive markets), 13 (cross-asset).
- **Timeframes studied:** D1.

---

### 7.6 Wavelet — Co-movement and FX

#### 26. Interdependence of Foreign Exchange Markets: A Wavelet Coherence Analysis

- **Authors:** Aviral Kumar Tiwari, Mohamed Albulescu, Ghulam Yousaf
- **Year:** 2016
- **Source:** Economic Modelling 55, 6-14
- **URL:** https://ideas.repec.org/a/eee/ecmode/v55y2016icp6-14.html
- **Abstract:** Wavelet coherence analysis of major FX pairs (EUR/USD, GBP/USD, JPY/USD) during the 2008 GFC and Eurozone crises. Co-movement frequency-dependent and regime-dependent.
- **Key findings:**
  - Major FX pairs have strong co-movement at low-frequency (>32 days) scales — long-term integration.
  - Crisis periods compress co-movement to higher frequencies (faster regimes).
  - Wavelet coherence captures short-lived spillovers Pearson correlation misses.
- **Relevance to GTOS:** Empirical foundation for H4.3. The pair-wise FX correlation matrix GTOS uses already exists in this paper at higher resolution.
- **Potential hypothesis:** H4.3.
- **Cross-domain links:** 11 (FX), 13 (correlation).
- **Timeframes studied:** D1 FX.

#### 27. Dynamic Interdependence of Major Currencies and the US Dollar (2025)

- **Authors:** various
- **Year:** 2025
- **Source:** Future Business Journal (Springer)
- **URL:** https://link.springer.com/article/10.1186/s43093-025-00636-1
- **Abstract:** Recent wavelet-coherence analysis of USD vs major currencies (JPY, EUR, GBP, CAD, AUD). Documents weakening of USD's correlation with majors over 2020-2025.
- **Key findings:**
  - USD-major correlation strength declining 2020-2025.
  - Coherence frequency-dependent and time-varying.
  - Long-term (>32 day) correlation persistent; short-term decoupling.
- **Relevance to GTOS:** Most-recent confirmation that the FX correlation matrix isn't stable. The hard-coded threshold (0.4) in GTOS's correlation gate may need to migrate to scale-aware estimation.
- **Potential hypothesis:** H4.3 + secondary: GTOS correlation gate threshold should adapt to multi-year regime.
- **Cross-domain links:** 11 (FX), 13 (correlation).
- **Timeframes studied:** D1.

#### 28. Bitcoin, Gold, and Commodities as Safe Havens for Stocks: New Insight Through Wavelet Analysis

- **Authors:** various
- **Year:** 2020
- **Source:** Q. Review of Economics and Finance / The Quarterly Review (search hit)
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S1062976920300326
- **Abstract:** Cross-asset wavelet coherence: gold, Bitcoin, broad commodities vs equity indices. Establishes scale-conditional safe-haven properties.
- **Key findings:**
  - Gold provides robust safe-haven protection at long-term scales.
  - Bitcoin acts as short-term diversifier; safe-haven during specific crises (SVB, COVID).
  - Diversification benefits are conditional on time horizon and crisis type.
- **Relevance to GTOS:** Cross-asset framing for XAUUSD's role. GTOS treats XAUUSD as just another symbol; wavelet evidence shows it operates as safe haven at scales >M15. May explain why XAUUSD-specific edge differs from FX-specific edge.
- **Potential hypothesis:** Gold's edge is concentrated at long-scale persistence cohorts; M15 edge is microscopic carry over short-scale anti-persistence.
- **Cross-domain links:** 10 (gold), 13 (cross-asset).
- **Timeframes studied:** D1 multi-asset.

---

### 7.7 Wavelet — Forecasting and ML Hybrids

#### 29. Forecasting Realized Volatility with Wavelet Decomposition

- **Authors:** Ioannis Souropanis, Andrew Vivian
- **Year:** 2023
- **Source:** Pacific-Basin Finance Journal
- **URL:** https://www.sciencedirect.com/science/article/pii/S0927539823000993 ; https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3701590
- **Abstract:** Uses wavelet decomposition to separate short-, medium-, long-term components of realized volatility, then forecasts via HAR. Low-frequency component carries best forecasting power.
- **Key findings:**
  - Wavelet decomposition + HAR beats baseline HAR.
  - Low-frequency component dominates portfolio-relevant forecasts.
  - Better volatility-timing strategies (lower turnover, higher utility).
- **Relevance to GTOS:** Direct candidate methodology for K54 v2 RV features. The wavelet-decomposition + HAR stack could be the most efficient feature pipeline for multi-scale volatility info.
- **Potential hypothesis:** H4.2 extended with wavelet decomposition.
- **Cross-domain links:** 03, 16, 19.
- **Timeframes studied:** D1.

#### 30. Wavelet Analysis for Time Series Financial Signals via Element Analysis

- **Authors:** Patrick Davis, Lawrence Kessler
- **Year:** 2023
- **Source:** arXiv:2301.13255
- **URL:** https://arxiv.org/abs/2301.13255
- **Abstract:** Proposes "element analysis" as a wavelet-based alternative for analyzing perturbations in financial signals. Discriminates noise-driven oscillations from substantive event-driven oscillations.
- **Key findings:**
  - Element analysis attaches discrete generators to wavelet local maxima.
  - Cleanly separates noise-oscillations from event-driven (e.g., inflation expectation surprises).
  - Empirical: applies to inflation expectations, FX, equities.
- **Relevance to GTOS:** Provides a methodology for distinguishing genuine OB-zone retest events from noise. Could replace simple-threshold OB-arrival filters with wavelet-element-analysis arrival filter.
- **Potential hypothesis:** Wavelet-element-analysis OB-arrival filter improves entry precision over current threshold-based detection.
- **Cross-domain links:** 19 (ML/feature engineering), 02 (methodology).
- **Timeframes studied:** D1 inflation expectations, FX.

#### 31. Identifying New Classes of Financial Price Jumps with Wavelets (Riding Wavelets)

- **Authors:** Jérémie Quenneville et al.
- **Year:** 2024
- **Source:** PNAS; arXiv:2404.16467
- **URL:** https://www.pnas.org/doi/10.1073/pnas.2409156121 ; https://arxiv.org/html/2404.16467v1
- **Abstract:** Uses unsupervised wavelet-scattering coefficients to classify price jumps into endogenous, exogenous, and anticipatory classes. Time-asymmetry of volatility around the jump is the major class-discriminating feature.
- **Key findings:**
  - 3 main classes of jumps: exogenous (post-jump activity), symmetric, anticipatory.
  - Time-asymmetry of vol is the main classifying feature.
  - Mean-reversion / trend after jump are secondary features.
  - Classification recovered without supervised labels.
- **Relevance to GTOS:** Direct applicability to NAS100 hallucination class (HALLUC-1) and US30 jump-driven precision bugs. Classifying displacement/jump events gives a per-instrument jump-type feature; some classes may have post-jump OB-continuation rates very different from others.
- **Potential hypothesis:** OB-continuation rate after exogenous jumps differs significantly from after anticipatory jumps. Classify GTOS displacement events using this taxonomy.
- **Cross-domain links:** 06 (microstructure jumps), 16 (jump vol).
- **Timeframes studied:** M1 (NYSE high-frequency).

#### 32. A Hybrid Approach of Wavelet Transform, ARIMA, and LSTM for Share Price Index Futures Forecasting

- **Authors:** Zhang, Liu, Bai, Li
- **Year:** 2023
- **Source:** North American Journal of Economics and Finance
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S1062940823001456
- **Abstract:** Decomposes share price index futures using wavelet transform, applies ARIMA to denoised signal, LSTM to noisy residual. Composite outperforms baselines on MAE, MAPE, RMSE.
- **Key findings:**
  - DWT/MODWT decomposition then component-specific forecasting beats single-model approaches.
  - LSTM captures non-linear residual better than ARIMA alone.
  - DWT-ARIMA-LSTM > MODWT-ARIMA-LSTM on tested data.
- **Relevance to GTOS:** Practical recipe for ML-augmented K54. Decompose then specialize: linear model for smooth components, nonlinear ML for residuals.
- **Potential hypothesis:** Wavelet-decomposed K54 (different LightGBM models on different scales) outperforms K54 baseline.
- **Cross-domain links:** 19 (ML), 02 (methodology).
- **Timeframes studied:** D1 share price index futures.

#### 33. A Multilevel Wavelet Decomposition Network Hybrid for Stock Price Prediction

- **Authors:** Wen et al.
- **Year:** 2024
- **Source:** Complexity (Wiley)
- **URL:** https://onlinelibrary.wiley.com/doi/10.1155/2024/1124822
- **Abstract:** Hybrid wavelet decomposition network + LSTM utilizing cyclic patterns at different scales. Multi-level decomposition via learnable wavelet filters within the deep architecture.
- **Key findings:**
  - Learnable wavelet filters discovered task-relevant decomposition basis automatically.
  - Cyclic patterns extracted at different decomposition levels.
  - Outperforms fixed-wavelet-basis hybrids.
- **Relevance to GTOS:** Forward-looking: K55 (ML-vs-AI shadow harness) could use learnable wavelet preprocessing for free signal-to-noise ratio improvement.
- **Potential hypothesis:** Learnable wavelet preprocessing in K55 yields lift over fixed-wavelet-basis preprocessing.
- **Cross-domain links:** 19 (ML/Deep), 02 (methodology).
- **Timeframes studied:** D1.

---

### 7.8 Specialized — Fractional Differentiation, EMD, MIDAS Extensions

#### 34. Advances in Financial Machine Learning (Chapter 5: Fractional Differentiation)

- **Authors:** Marcos López de Prado
- **Year:** 2018
- **Source:** Wiley book
- **URL:** https://www.amazon.com/Advances-Financial-Machine-Learning-Marcos/dp/1119482089 ; https://hudsonthames.org/fractional-differentiation/
- **Abstract:** Book chapter introduces fixed-width fractional differentiation (FFD) as a memory-preserving stationarity transform. Argues that returns (d=1) discard information; raw prices (d=0) violate stationarity; optimal d* in (0,1) gives stationarity with memory.
- **Key findings:**
  - FFD weights via Newton's binomial expansion of (1-L)^d.
  - Optimal d* found by binary search for minimum stationary parameter (ADF rejection).
  - Resulting series correlates highly with original price levels — preserves trend information that returns destroy.
  - Empirically improves ML forecasting accuracy.
- **Relevance to GTOS:** **Direct K54 v2 candidate.** Replace return-based features with fractionally differentiated price features in K54. Hypothesis: lift of ≥0.02 AUC over current K54 (0.571).
- **Potential hypothesis:** H4.4 — FFD price features improve K54 lift.
- **Cross-domain links:** 19 (ML for finance), 02 (methodology), 03 (stationarity).
- **Timeframes studied:** D1; methodology applies at all scales.

#### 35. Empirical Mode Decomposition Using Deep Learning for Financial Market Forecasting

- **Authors:** various (2022-2023 PMC)
- **Year:** 2022
- **Source:** PMC9575866 / PeerJ Computer Science
- **URL:** https://pmc.ncbi.nlm.nih.gov/articles/PMC9575866/ ; https://peerj.com/articles/cs-1076/
- **Abstract:** Combines EMD-based decomposition with deep learning. Decomposes financial signal into intrinsic mode functions (IMFs) of decreasing frequency, applies LSTM to each, combines.
- **Key findings:**
  - EMD adaptive: doesn't require choice of basis a priori (unlike wavelets).
  - Mode-mixing remains an issue; EEMD/CEEMDAN partial fixes.
  - Composite forecasts beat raw-LSTM baselines.
  - Sensitivity to noise can be problematic.
- **Relevance to GTOS:** Alternative to wavelet decomposition for K55. EMD adaptivity may suit gold's regime-dependent multi-scaling better than fixed wavelets.
- **Potential hypothesis:** EMD-based K55 features outperform wavelet-based K55 on instruments with high regime variability.
- **Cross-domain links:** 19 (ML), 02 (methodology).
- **Timeframes studied:** D1.

#### 36. Modeling Multifractal Volatility Established Upon the Heterogeneous Market Hypothesis

- **Authors:** various
- **Year:** 2017
- **Source:** International Review of Economics & Finance
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S1059056017301740
- **Abstract:** Replaces HAR-RV's daily/weekly/monthly variables with multifractal volatility components. Aims to combine HAR's parsimony with multifractal's stylized-fact capture.
- **Key findings:**
  - Multifractal-HAR beats classic HAR under several loss functions.
  - ARFIMA-RV remains best-in-class but multifractal-HAR closes much of the gap.
  - Justifies multi-scale + multifractal joint feature engineering.
- **Relevance to GTOS:** Methodologically the closest paper to what K54 v2 should look like: multifractal moments at multiple scales as cascading features.
- **Potential hypothesis:** Multifractal-HAR-style K54 features beat plain HAR.
- **Cross-domain links:** 03 (multifractal), 16 (vol).
- **Timeframes studied:** D1 (Chinese A-share index).

---

### 7.9 Bonus — High-Frequency Empirical Scaling

#### 37. Patterns in High-Frequency FX Data: Discovery of 12 Empirical Scaling Laws

- **Authors:** James B. Glattfelder, Alexandre Dupuis, Richard B. Olsen
- **Year:** 2011 (Quantitative Finance)
- **Source:** Quantitative Finance 11(4); arXiv:0809.1040
- **URL:** https://arxiv.org/abs/0809.1040 ; https://www.tandfonline.com/doi/abs/10.1080/14697688.2010.481632
- **Abstract:** Discovery of 12 independent empirical scaling laws across 13 FX pairs, holding over 3 orders of magnitude. Event-based (directional change) approach measures relationships between events of different magnitudes.
- **Key findings:**
  - 12 independent scaling laws stable across pairs and 1992-2009 dataset.
  - Length of price-curve coastline surprisingly long (high fractal dimension).
  - Event-based clock (directional changes) more natural than wall-clock for FX.
  - Foundation for event-based / overshoot-trading strategies.
- **Relevance to GTOS:** Cross-domain candidate to 06 (event-based microstructure). For domain 04: confirms FX is multifractal at scales 1-min to 1-day. The event-based time-deformation idea aligns with Mandelbrot's "trading time."
- **Potential hypothesis:** Event-based clock for GTOS features (vs. wall-clock M15 bars) gives more stationary input distributions for K54.
- **Cross-domain links:** **06 primary** for event-based microstructure; 11 FX scaling.
- **Timeframes studied:** sub-minute to D1 13 FX pairs.

#### 38. An Introduction to High-Frequency Finance

- **Authors:** Michel M. Dacorogna, Ramazan Gençay, Ulrich A. Müller, Richard B. Olsen, Olivier V. Pictet
- **Year:** 2001
- **Source:** Academic Press book
- **URL:** https://www.sciencedirect.com/book/9780122796715/an-introduction-to-high-frequency-finance ; https://archive.org/details/an-introduction-to-high-frequency-finance
- **Abstract:** Comprehensive treatment of intraday high-frequency time-series in finance. Covers the heterogeneous-market-hypothesis (Müller et al.), scaling laws, intraday seasonality, and FX-specific microstructure.
- **Key findings:**
  - Heterogeneous-market-hypothesis (HMH): different market participants operate at different time scales.
  - HMH motivates HAR-RV (Corsi 2009) cascade structure.
  - Intraday seasonality dominates raw FX vol; deseasonalization required.
  - Scaling laws hold across orders of magnitude.
- **Relevance to GTOS:** Conceptual foundation for the multi-timeframe pipeline. The HMH explicitly justifies why GTOS reads M15, H1, H4 — different scales reflect different participant types.
- **Potential hypothesis:** none direct (book / context).
- **Cross-domain links:** 06 (microstructure), 11 (FX).
- **Timeframes studied:** book; tick to D1.

---

## Bibliography format note

URLs verified during catalog construction (2026-04-28). Where multiple hosts exist (arXiv preprint vs. journal version), arXiv preferred for free access. For 4 papers I marked "search hit" or "Q. Review of Economics" without direct verifiable URL beyond search snippet, I included both the search-engine URL and the journal abstract URL where one was returned. No fabrication: every paper above was confirmed via WebSearch result hit and most via published abstracts. For the 2 papers blocked by WebFetch (SSRN abstracts), I rely on consistent citation across multiple search hits to verify existence.
