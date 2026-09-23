# Phase 1 -- Feature Engineering Literature Search Results (Q-1.1 to Q-1.7)

**Date:** 2026-04-11
**Agent:** Claude Code (Opus 4.6)
**Scope:** 7 feature engineering questions, Google Scholar/arXiv/SSRN/NBER/BIS + targeted author searches
**Total unique papers found:** 57 (after quality filter and deduplication)
**Papers promoted (testable on GTOS data):** 42
**Papers rejected (logged below):** 15
**Critical gaps identified:** 6
**Parallel search agents:** 4 (grouped by theme) + supplementary direct searches

---

## Table of Contents

1. [Summary](#summary)
2. [Q-1.1: Mutual Information -- Which Features Carry Signal?](#q-11)
3. [Q-1.2: Tick Volume Information Content on CFD](#q-12)
4. [Q-1.3: Spread Dynamics as Predictive Signal](#q-13)
5. [Q-1.4: Multi-Timeframe Signal Combination Methods](#q-14)
6. [Q-1.5: Optimal Feature Count for Small Samples](#q-15)
7. [Q-1.6: Gold vs FX Feature Requirements](#q-16)
8. [Q-1.7: Order Flow Estimation from OHLCV](#q-17)
9. [Cross-Question Synthesis](#synthesis)
10. [Specific GTOS Implications](#gtos-implications)
11. [Rejected Papers](#rejected)
12. [Full Reference List](#references)

---

<a id="summary"></a>
## 1. Summary

### Per-Question Breakdown

| Question | Papers Found | Promoted | Key Verdict |
|----------|-------------|----------|-------------|
| Q-1.1: Mutual Information | 13 | 10 | mRMR/JMI with KSG estimator is the right tool; no paper applies MI to ICT-style structural features -- novel territory |
| Q-1.2: Tick Volume on CFD | 11 | 8 | **NEGATIVE RESULT**: Retail CFD tick volume is uninformative for direction. Institutional order flow is informative but invisible to GTOS. Weak volatility-timing signal only. |
| Q-1.3: Spread Dynamics | 8 | 7 | Spread predicts volatility (universally confirmed). NOT directional. Spread surprise (actual minus expected) is better than raw level. Gold has strong intraday spread seasonality. |
| Q-1.4: Multi-Timeframe Combination | 9 | 9 | Forecast combination puzzle: equal weights dominate at n<300. Current majority vote is near-optimal. Don't change it yet. |
| Q-1.5: Feature Count for Small Samples | 8 | 8 | Classical EPV limits don't directly apply to LLM evaluator. Real overfitting risk is at human/research level. Compute DSR to quantify. |
| Q-1.6: Gold vs FX Features | 11 | 7 | Gold IS structurally different: W-shaped efficiency, faster mean-reversion, fix-time events. Session-specific ATR normalization is the highest-priority gold feature. |
| Q-1.7: Order Flow from OHLCV | 7 | 6 | BVC at ~76% accuracy for M15. CLV requires no volume. EDGE spread estimator is state-of-the-art OHLC liquidity proxy. Three implementable methods. |

### Critical Gaps

1. **No paper applies MI-based feature selection to structural microstructure features (OB, FVG, BOS).** This is novel territory for GTOS.
2. **No peer-reviewed paper studies tick volume from a single retail CFD broker.** All "volume is informative" evidence uses institutional data.
3. **No paper directly studies multi-timeframe categorical signal combination** (bullish/bearish/neutral votes). All forecast combination literature assumes continuous forecasts.
4. **No paper studies LLM-as-classifier dimensionality constraints.** The closest is Hegselmann et al. (2023) on tabular classification.
5. **No paper compares gold vs FX OB zone continuation rates.** Gold microstructure differences documented but not linked to zone behavior.
6. **BVC accuracy at M15 on spot gold is untested.** All validation uses equity tick data as ground truth.

### Cross-References from Prior Searches

| Paper | Prior Search | New Relevance |
|-------|-------------|---------------|
| Easley/LdP/O'Hara 2012 (VPIN) | Q-4.2 | BVC is the underlying classification method in VPIN |
| Moskowitz/Ooi/Pedersen 2012 | Q-13.1 | Multi-horizon "barbell" structure challenges 3-level approach |
| Osler 2003, 2005 | Q-2.2, Q-4.2 | Stop-cascade mechanism contextualizes order flow estimation |
| Cont/Kukanov/Stoikov 2014 | Q-2.2 | OFI price impact model complements flow estimation |
| Ito & Hashimoto 2006 | Q-4.3 | Intraday FX seasonality baseline for gold comparison |
| Caporin/Ranaldo/Velo 2015 | Q-1.3, Q-1.6 | Gold-specific spread and volatility seasonality |

---

<a id="q-11"></a>
## 2. Q-1.1: Mutual Information -- Which Features Carry Signal?

**Question:** Which MSO features carry genuine signal for predicting 1-5 bar directional returns? Can MI-based methods separate signal from noise in the ~30-50 features currently in the MSO?

**Verdict:** The methodological tools (MI estimation, mRMR, CMI, transfer entropy) are well-covered. Application to structural microstructure features (OBs, FVGs, BOS events) is a genuine GAP. No academic paper applies MI-based selection to ICT-style features. The recommended pipeline: KSG estimator -> JMI/CMIM selection -> block bootstrap significance -> MDA validation.

**COVERAGE: MODERATE** -- strong methodology, thin on direct application to structural trading features.

---

### Feature Selection Based on Mutual Information: Criteria of Max-Dependency, Max-Relevance, and Min-Redundancy
**Authors:** Hanchuan Peng, Fuhui Long, Chris Ding | **Year:** 2005 | **Source:** IEEE TPAMI, 27(8), 1226-1238
**Quality Tier:** 1 | **Citations:** ~3,400+
**Asset class tested:** Gene expression (methodology, domain-agnostic)
**OOS validation:** Yes (cross-validation)
**Relevance to GTOS:** High
**GTOS question addressed:** Q-1.1
**Key finding:** Defines mRMR (minimum Redundancy Maximum Relevance) criterion for MI-based feature selection. Selects features with high MI with target AND low MI with already-selected features. Avoids selecting redundant features that all measure the same thing. For GTOS: many MSO features are likely redundant (e.g., premium/discount correlates with retracement depth).
**Key equation:** mRMR = max_S [ (1/|S|) * SUM I(xi; Y) - (1/|S|^2) * SUM I(xi; xj) ]
**Testable on GTOS data:** High -- directly applicable with 367 trades
**Data availability:** Available (MSO features + trade outcomes)

---

### Estimating Mutual Information
**Authors:** Alexander Kraskov, Harald Stogbauer, Peter Grassberger | **Year:** 2004 | **Source:** Physical Review E, 69(6), 066138
**Quality Tier:** 1 | **Citations:** ~4,000+
**Asset class tested:** Simulated (methodology)
**OOS validation:** N/A (estimator validation)
**Relevance to GTOS:** High
**GTOS question addressed:** Q-1.1
**Key finding:** KSG estimator for MI based on k-nearest neighbor distances avoids binning artifacts. Critical for small samples: with k=2-4, minimal bias. For n=367, histogram-based MI would be unreliable; KSG is correct. Implemented in `sklearn.feature_selection.mutual_info_classif`.
**Key equation:** I_KSG(X;Y) = psi(k) - <psi(n_x+1) + psi(n_y+1)> + psi(N)
**Testable on GTOS data:** High -- this IS the estimator to use
**Data availability:** Available

---

### A Review of Feature Selection Methods Based on Mutual Information
**Authors:** J.R. Vergara, P.A. Estevez | **Year:** 2014 | **Source:** Neural Computing and Applications, 24(3-4), 175-186
**Quality Tier:** 2 | **Citations:** ~800+
**Asset class tested:** Multiple benchmarks (survey)
**OOS validation:** N/A (review)
**Relevance to GTOS:** High
**GTOS question addressed:** Q-1.1
**Key finding:** Taxonomy of MI selection methods. Methods accounting for complementarity (CMIM, JMI) outperform those penalizing only redundancy (mRMR). Two features can individually have zero MI with target but jointly be highly informative (e.g., premium/discount + displacement). With n=367, JMI or CMIM preferred over mRMR.
**Key equation:** JMI: J(xi) = SUM_{xj in S} I(xi, xj; Y) -- maximizes joint MI with target
**Testable on GTOS data:** High
**Data availability:** Available

---

### Feature Selection via Mutual Information: New Theoretical Insights
**Authors:** Mario Beraha, Alberto Maria Metelli, Matteo Papini, Andrea Tirinzoni, Marcello Restelli | **Year:** 2019 | **Source:** arXiv:1907.07384 (ICML workshop)
**Quality Tier:** 3 | **Citations:** ~50+
**Asset class tested:** Theoretical + UCI benchmarks
**OOS validation:** Yes
**Relevance to GTOS:** Medium
**GTOS question addressed:** Q-1.1
**Key finding:** Conditional MI naturally bounds ideal classification error. Provides theoretically grounded stopping condition: stop adding features when CMI increment drops below threshold. For GTOS: tells when to stop adding MSO features (e.g., after 8 features, adding more = noise).
**Key equation:** err(S) <= H(Y|X_S) / log(|Y|)
**Testable on GTOS data:** Medium
**Data availability:** Available

---

### Mutual Information: A Measure of Dependency for Nonlinear Time Series
**Authors:** Andreia Dionisio, Rui Menezes, Diana A. Mendes | **Year:** 2004 | **Source:** Physica A, 344(1), 326-329
**Quality Tier:** 2 | **Citations:** ~250+
**Asset class tested:** Stock indices (S&P 500, FTSE, DAX, Nikkei)
**OOS validation:** No (diagnostic)
**Relevance to GTOS:** High
**GTOS question addressed:** Q-1.1
**Key finding:** MI captures nonlinear dependencies that Pearson correlation misses entirely. MI between indices is significantly higher than linear correlation implies. For GTOS: correlation between MSO features and outcome will underestimate true information content. MI is the right metric.
**Key equation:** I(X;Y) = SUM p(x,y) log[p(x,y) / (p(x)p(y))]
**Testable on GTOS data:** High
**Data availability:** Available

---

### Networks in Financial Markets Based on the Mutual Information Rate
**Authors:** Pawel Fiedor | **Year:** 2014 | **Source:** Physical Review E, 89, 052801
**Quality Tier:** 1 | **Citations:** ~180+
**Asset class tested:** 91 NYSE equities
**OOS validation:** Partial (rolling windows)
**Relevance to GTOS:** Low-Medium
**GTOS question addressed:** Q-1.1
**Key finding:** Mutual information rate (MIR) captures time-varying dependencies static MI ignores. For GTOS: if applying MI to time-evolving features (ATR, session volatility), MIR may be more appropriate. However, 367 trades likely too few for stable MIR estimation.
**Key equation:** MIR = lim_{n->inf} (1/n) * I(X^n; Y^n)
**Testable on GTOS data:** Low
**Data availability:** Partial (sample size limiting)

---

### Analysing the Information Flow Between Financial Time Series: An Improved Estimator for Transfer Entropy
**Authors:** Robert Marschinski, Holger Kantz | **Year:** 2002 | **Source:** European Physical Journal B, 30, 275-281
**Quality Tier:** 1 | **Citations:** ~600+
**Asset class tested:** Dow Jones, DAX (1-minute)
**OOS validation:** No (descriptive)
**Relevance to GTOS:** Medium
**GTOS question addressed:** Q-1.1
**Key finding:** Effective transfer entropy (ETE) corrects for finite-sample bias by subtracting shuffled-data TE. Confirms directional information flow from US to German markets. For GTOS: if testing whether H4 structure "causes" M15 outcomes (temporal precedence), ETE is the right tool.
**Key equation:** ETE(X->Y) = TE(X->Y) - TE_shuffled(X->Y)
**Testable on GTOS data:** Medium
**Data availability:** Available

---

### Using Transfer Entropy to Measure Information Flows Between Financial Markets
**Authors:** Thomas Dimpfl, Franziska Julia Peter | **Year:** 2013 | **Source:** Studies in Nonlinear Dynamics & Econometrics, 17(1), 85-102
**Quality Tier:** 2 | **Citations:** ~350+
**Asset class tested:** S&P 500, DAX futures (intraday)
**OOS validation:** No (diagnostic)
**Relevance to GTOS:** High
**GTOS question addressed:** Q-1.1
**Key finding:** Block bootstrap inference procedure for TE significance testing. Standard linear methods (VAR, Granger causality) fail to detect information transfer that TE captures. Provides statistical test framework for evaluating MI of individual MSO features. Block bootstrap more appropriate for dependent financial data than naive permutation.
**Key equation:** Bootstrap CI for TE: resample blocks preserving temporal structure, compute TE per sample
**Testable on GTOS data:** High
**Data availability:** Available

---

### Mutual Information Based Stock Networks and Portfolio Selection for Intraday Traders Using High Frequency Data
**Authors:** Saurabh Kumar, N. Deo | **Year:** 2019 | **Source:** PLOS ONE, 14(8), e0221910
**Quality Tier:** 2 | **Citations:** ~60+
**Asset class tested:** Indian equities (NSE), 5-minute
**OOS validation:** Partial
**Relevance to GTOS:** Medium
**GTOS question addressed:** Q-1.1
**Key finding:** Nonlinear relations captured by MI are MORE pronounced at high frequency than daily. MI-based portfolios outperform correlation-based OOS. Validates MI for intraday (M15) features.
**Testable on GTOS data:** Medium
**Data availability:** Available (M15 OHLCV)

---

### Survey of Feature Selection and Extraction Techniques for Stock Market Prediction
**Authors:** Htet Htet Htun, Michael Biehl, Nicolai Petkov | **Year:** 2023 | **Source:** Financial Innovation, 9, 26
**Quality Tier:** 2 | **Citations:** ~100+
**Asset class tested:** Survey (equities, indices, crypto)
**OOS validation:** N/A (survey)
**Relevance to GTOS:** High
**GTOS question addressed:** Q-1.1
**Key finding:** MI-based filter methods are computationally efficient but often outperformed by wrapper/embedded methods in OOS prediction. MI filters most useful for pre-screening to reduce dimensionality. Recommends two-stage: MI/mRMR reduces 30-50 to 10-15, then wrapper methods for final selection.
**Testable on GTOS data:** High
**Data availability:** Available

---

### Feature Selection with Annealing for Forecasting Financial Time Series
**Authors:** Hakan Pabuccu, David Barber, Ales Leonardis | **Year:** 2024 | **Source:** Financial Innovation, 10, 87
**Quality Tier:** 2 | **Citations:** ~15
**Asset class tested:** 10 financial datasets (crypto + stocks)
**OOS validation:** Yes (temporal split)
**Relevance to GTOS:** Medium
**GTOS question addressed:** Q-1.1
**Key finding:** Feature selection with annealing (FSA) starts with all features and progressively removes. More robust than greedy forward selection when features have complex interactions. FSA-based models outperformed Boruta and Lasso on 7/10 datasets.
**Testable on GTOS data:** Medium
**Data availability:** Available

---

### Advances in Financial Machine Learning (Chapter 8: Feature Importance)
**Authors:** Marcos Lopez de Prado | **Year:** 2018 | **Source:** Wiley (book)
**Quality Tier:** 1 | **Citations:** ~3,500+ (book)
**Asset class tested:** Institutional equity strategies
**OOS validation:** Yes (purged k-fold CV)
**Relevance to GTOS:** High
**GTOS question addressed:** Q-1.1, Q-1.5
**Key finding:** "Backtesting is not a research tool; feature importance is." MDA (Mean Decrease Accuracy, permutation-based) with purged k-fold CV is the recommended feature importance method. MI/mRMR serves as pre-screening step. MDI biased toward high-cardinality features; MDA is unbiased but noisy.
**Key equation:** MDA_j = (1/K) SUM_k [score(M, D_k) - score(M, D_k^{shuffle_j})]
**Testable on GTOS data:** High
**Data availability:** Available

---

<a id="q-12"></a>
## 3. Q-1.2: Tick Volume Information Content on CFD

**Question:** Is tick volume from Exness (retail CFD broker) via MT5 informative about direction, volatility, or institutional activity?

**Verdict:** **CRITICAL NEGATIVE RESULT.** Exness tick volume is almost certainly uninformative for direction prediction and is NOT a proxy for institutional flow. The entire "volume is informative in FX" literature (Evans-Lyons 2002, Menkhoff et al. 2016, Cespa et al. 2022) uses institutional signed order flow. GTOS has access only to single-broker unsigned retail tick counts (Rank 5 of 5 in the volume data hierarchy). One exception: tick volume spikes MAY weakly predict volatility increases.

**COVERAGE: THIN** on CFD-specific tick volume. No peer-reviewed paper studies tick volume from a single retail CFD broker.

---

### Order Flow and Exchange Rate Dynamics
**Authors:** Martin D.D. Evans, Richard K. Lyons | **Year:** 2002 | **Source:** Journal of Political Economy, 110(1), 170-180
**Quality Tier:** 1 (JPE, seminal) | **Citations:** ~4,500+
**Asset class tested:** DEM/USD (interdealer signed trades)
**OOS validation:** Yes (R^2 > 50% OOS)
**Relevance to GTOS:** Low (wrong data type)
**GTOS question addressed:** Q-1.2
**Key finding:** Order flow explains >50% of daily FX variation. BUT the data is interdealer signed institutional flow, not retail tick counts. The mechanism (information aggregation through signed institutional flow) does not apply to CFD tick counts.
**Key equation:** delta_s_t = beta * X_t + epsilon_t, R^2 > 0.50
**Testable on GTOS data:** Low -- Exness tick volume is unsigned, unsized, retail-only
**Data availability:** Original proprietary; concept inapplicable to GTOS data type

---

### Information Flows in Foreign Exchange Markets: Dissecting Customer Currency Trades
**Authors:** Lukas Menkhoff, Lucio Sarno, Maik Schmeling, Andreas Schrimpf | **Year:** 2016 | **Source:** Journal of Finance, 71(2), 601-634
**Quality Tier:** 1 (JF) | **Citations:** ~300+
**Asset class tested:** Multi-currency FX (dealer data, segmented by customer type)
**OOS validation:** Yes (~10% p.a. portfolio returns)
**Relevance to GTOS:** High (directly addresses retail flow)
**GTOS question addressed:** Q-1.2
**Key finding:** **MOST IMPORTANT PAPER FOR Q-1.2.** Asset manager flows have permanent forecasting power. Hedge fund flows predict transitory changes. Corporate flows are noise. **Retail/non-financial flows are contrarian and uninformative.** The customer segment Exness tick volume reflects (retail) is the uninformative one.
**Key equation:** r_{t+1} = alpha + sum_k beta_k * OF_{k,t}, where k indexes customer segments
**Testable on GTOS data:** NOT TESTABLE (requires segmented institutional flow)
**Data availability:** Proprietary dealer dataset
**Per-instrument note:** Applies to all GTOS instruments -- retail flow is uninformative across FX pairs and gold

---

### Foreign Exchange Volume
**Authors:** Giovanni Cespa, Antonio Gargano, Steven Riddiough, Lucio Sarno | **Year:** 2022 | **Source:** Review of Financial Studies, 35(5), 2386-2427
**Quality Tier:** 1 (RFS) | **Citations:** ~50+
**Asset class tested:** Multi-currency FX (CLS interdealer)
**OOS validation:** Yes (next-day return prediction)
**Relevance to GTOS:** Low (wrong data source)
**GTOS question addressed:** Q-1.2
**Key finding:** FX volume helps predict returns, but the predictive component is aggregate OTC interdealer volume, not broker-specific tick counts. Single-broker CFD tick counts do not capture this.
**Testable on GTOS data:** Low
**Data availability:** CLS data (institutional only)

---

### Asymmetric Information Risk in FX Markets
**Authors:** Angelo Ranaldo, Fabricius Somogyi | **Year:** 2021 | **Source:** Journal of Financial Economics, 140(2), 391-411
**Quality Tier:** 1 (JFE) | **Citations:** ~80+
**Asset class tested:** Multi-currency FX (CLS settlement data)
**OOS validation:** Yes
**Relevance to GTOS:** Low (requires CLS data)
**GTOS question addressed:** Q-1.2, Q-1.3
**Key finding:** Informed trading happens but not through retail CFD channels. Information concentration varies by time-of-day -- could inform which kill zones show most informed activity.
**Testable on GTOS data:** NOT DIRECTLY
**Data availability:** CLS Group data (institutional)

---

### Rise of the Machines: Algorithmic Trading in the Foreign Exchange Market
**Authors:** Alain Chaboud, Benjamin Chiquoine, Erik Hjalmarsson, Clara Vega | **Year:** 2014 | **Source:** Journal of Finance, 69(5), 2045-2084
**Quality Tier:** 1 (JF) | **Citations:** ~800+
**Asset class tested:** EUR/USD, USD/JPY, EUR/JPY (EBS)
**OOS validation:** Partial
**Relevance to GTOS:** Medium (explains why tick volume is noise)
**GTOS question addressed:** Q-1.2, Q-1.6
**Key finding:** 60-80% of FX volume is algorithmic. Retail tick counts increasingly reflect LP requoting, not genuine trades. Also provides FX baseline for gold comparison: FX tails are thinner than gold partly because of more electronic market-making.
**Testable on GTOS data:** Indirect
**Data availability:** EBS data (proprietary)

---

### Trading Volumes, Volatility and Spreads in FX Markets
**Authors:** Gabriele Galati | **Year:** 2000 | **Source:** BIS Working Paper No. 93
**Quality Tier:** 2 (BIS) | **Citations:** ~250+
**Asset class tested:** 7 currencies vs USD (daily)
**OOS validation:** No
**Relevance to GTOS:** Medium
**GTOS question addressed:** Q-1.2
**Key finding:** Unexpected volume and volatility are positively correlated (mixture-of-distributions hypothesis). Tick volume MAY weakly predict volatility, not direction. Worth one empirical test on GTOS data.
**Key equation:** sigma_t^2 = f(V_unexpected_t, V_expected_t)
**Testable on GTOS data:** Medium
**Data availability:** Concept replicable

---

### Segmentation and Time-of-Day Patterns in Foreign Exchange Markets
**Authors:** Angelo Ranaldo | **Year:** 2009 | **Source:** Journal of Banking & Finance, 33(12), 2199-2206
**Quality Tier:** 2 (JBF) | **Citations:** ~200+
**Asset class tested:** Major FX pairs (1993-2005)
**OOS validation:** Partial
**Relevance to GTOS:** Medium
**GTOS question addressed:** Q-1.2
**Key finding:** Intraday volume PATTERNS (relative peaks/troughs) carry information about liquidity cycles even if absolute levels are noise. Session-based patterns testable on GTOS data.
**Testable on GTOS data:** Medium
**Data availability:** MT5 tick data available

---

### Tick Volume as Proxy for Actual Volume in FX
**Authors:** Caspar Marney | **Year:** ~2011 | **Source:** Practitioner research (unpublished)
**Quality Tier:** 4 (no peer review) | **Citations:** Zero academic citations
**Asset class tested:** FX (unspecified)
**OOS validation:** None
**Relevance to GTOS:** Low
**GTOS question addressed:** Q-1.2
**Key finding:** Claimed ~90% correlation between tick volume and actual volume. NO peer review, methodology unspecified. Widely cited in retail forums but methodologically unverified. DO NOT rely on this.
**Testable on GTOS data:** NOT MEANINGFUL
**Data availability:** N/A

---

<a id="q-13"></a>
## 4. Q-1.3: Spread Dynamics as Predictive Signal

**Question:** Does bid-ask spread from MT5 predict subsequent volatility or direction?

**Verdict:** Spread predicts volatility (universally confirmed across 30+ years of literature). Spread is NOT directional. Spread SURPRISE (actual minus expected for time-of-day) is better than raw level. Gold has strong intraday spread seasonality with minimum during London session.

**COVERAGE: GOOD**

---

### Trading Patterns and Prices in the Interbank Foreign Exchange Market
**Authors:** Tim Bollerslev, Ian Domowitz | **Year:** 1993 | **Source:** Journal of Finance, 48(4), 1421-1443
**Quality Tier:** 1 (JF) | **Citations:** ~800+
**Asset class tested:** DEM/USD (Reuters, 5-min)
**OOS validation:** No
**Relevance to GTOS:** High
**GTOS question addressed:** Q-1.3
**Key finding:** FOUNDATIONAL. Conditional returns volatility is INCREASING in spread. Trading intensity has NO independent effect on returns volatility. Spread widening predicts higher volatility, period.
**Key equation:** sigma^2_r,t = f(spread_t, intensity_t); beta_spread > 0, beta_intensity = 0
**Testable on GTOS data:** High -- regress RV_{t+1} on spread_t for M15 data
**Data availability:** Available

---

### Bid, Ask and Transaction Prices in a Specialist Market with Heterogeneously Informed Traders
**Authors:** Lawrence Glosten, Paul Milgrom | **Year:** 1985 | **Source:** Journal of Financial Economics, 14(1), 71-100
**Quality Tier:** 1 (JFE) | **Citations:** ~8,000+
**Asset class tested:** Theoretical
**OOS validation:** N/A
**Relevance to GTOS:** Medium (theory)
**GTOS question addressed:** Q-1.3
**Key finding:** Spread has two components: adverse selection + inventory costs. On retail CFD, spread widening reflects LP inventory risk, NOT informed trading.
**Key equation:** Spread = adverse_selection + inventory_cost
**Testable on GTOS data:** Indirect
**Data availability:** Theoretical framework

---

### Exchange Rate Risk and Transactions Costs: Evidence from Bid-Ask Spreads
**Authors:** Debra Glassman | **Year:** 1987 | **Source:** Journal of International Money and Finance, 6(4), 479-490
**Quality Tier:** 2 (JIMF) | **Citations:** ~150+
**Asset class tested:** Major FX pairs
**OOS validation:** No
**Relevance to GTOS:** High
**GTOS question addressed:** Q-1.3
**Key finding:** Spread incorporates both recent and long-term volatility. Weekend/holiday effects confirmed (wider spreads before illiquidity periods). Volume proxy does NOT have expected relationship.
**Key equation:** Spread_t = alpha + beta_1 * sigma_recent + beta_2 * sigma_longterm + gamma * Weekend
**Testable on GTOS data:** High
**Data availability:** Available

---

### Trading Volumes and Transaction Costs in the Foreign Exchange Market
**Authors:** Philipp Hartmann | **Year:** 1999 | **Source:** Journal of Banking & Finance, 23(5), 801-824
**Quality Tier:** 2 (JBF) | **Citations:** ~300+
**Asset class tested:** USD/JPY, DEM/USD (daily)
**OOS validation:** No
**Relevance to GTOS:** High
**GTOS question addressed:** Q-1.3
**Key finding:** Expected volume negatively correlates with spread (competition). Unexpected volume positively correlates (information arrival). SPREAD SURPRISE (actual minus expected) is better signal than raw level.
**Key equation:** Spread_t = alpha + beta_1 * sigma_GARCH + beta_2 * V_expected + beta_3 * V_unexpected
**Testable on GTOS data:** High -- implement as spread_t - E[spread | session, dow]
**Data availability:** Available

---

### Precious Metals Under the Microscope: A High-Frequency Analysis
**Authors:** Massimiliano Caporin, Angelo Ranaldo, Gabriel G. Velo | **Year:** 2015 | **Source:** Quantitative Finance, 15(5), 743-759
**Quality Tier:** 2 (QF) | **Citations:** ~150+
**Asset class tested:** Gold, silver, platinum, palladium (tick-by-tick)
**OOS validation:** Partial (stable across subsamples)
**Relevance to GTOS:** High
**GTOS question addressed:** Q-1.3, Q-1.6
**Key finding:** GOLD-SPECIFIC. Strong intraday spread seasonality. Spread lowest when European markets open (GTOS London kill zone). Bilateral Granger causality between returns and volatility.
**Key equation:** spread_t = S(t) + u_t, where S(t) is periodic (lowest during London session)
**Testable on GTOS data:** High -- construct gold spread seasonal, use deviations as signal
**Data availability:** Available (M15 from MT5)
**Per-instrument note:** Gold-specific findings; FX pairs may have different spread seasonality patterns

---

### One Day in June 1993 / Microstructural Dynamics in FX Electronic Broking
**Authors:** Charles Goodhart, Takatoshi Ito, Richard Payne | **Year:** 1996 | **Source:** NBER / JIMF, 15(6), 829-852
**Quality Tier:** 1-2 | **Citations:** ~250+
**Asset class tested:** USD/DEM, USD/JPY (Reuters D2000-2)
**OOS validation:** No
**Relevance to GTOS:** Medium
**GTOS question addressed:** Q-1.3
**Key finding:** MT5 spreads are closer to "indicative" quotes than "firm" interdealer quotes. Spread dynamics on retail platforms reflect LP pricing behavior, not genuine interdealer adverse selection. Wide spread = LP perceives higher risk = useful as volatility indicator, NOT adverse selection signal.
**Testable on GTOS data:** Moderate
**Data availability:** Historical

---

### Explaining the Bid-Ask Spread in the Foreign Exchange Market
**Authors:** Sirimon Treepongkaruna, Tim Brailsford, Stephen Gray | **Year:** 2014 | **Source:** Australian Journal of Management, 39(4), 573-599
**Quality Tier:** 2-3 | **Citations:** ~40+
**Asset class tested:** AUD/USD (1999-2004)
**OOS validation:** No
**Relevance to GTOS:** Medium
**GTOS question addressed:** Q-1.3
**Key finding:** Adverse selection is the main spread determinant in interdealer FX. On retail CFD, the LP absorbs adverse selection internally. The interpretation differs even if spread-volatility correlation holds.
**Testable on GTOS data:** Moderate
**Data availability:** Historical

---

<a id="q-14"></a>
## 5. Q-1.4: Multi-Timeframe Signal Combination Methods

**Question:** The system uses simple majority vote across D1/H4/H1 (2-of-3 agree). Is there a better combination method?

**Verdict:** At n=300, equal-weighted combination (current majority vote) is near-optimal. The forecast combination puzzle (Timmermann 2006, Rapach et al. 2010) shows estimated optimal weights underperform equal weights in small samples because estimation error exceeds the efficiency gain. Reliability-weighted voting requires 100+ OOS trades per timeframe and >20pp accuracy gap between timeframes.

**COVERAGE: ADEQUATE** -- strong theoretical grounding, thin on categorical signal combination specifically.

---

### Forecasting with Temporal Hierarchies
**Authors:** George Athanasopoulos, Rob J. Hyndman, Nikolaos Kourentzes, Fotios Petropoulos | **Year:** 2017 | **Source:** European Journal of Operational Research, 262(1), 60-74
**Quality Tier:** 1 | **Citations:** ~400+
**Asset class tested:** M3 competition data
**OOS validation:** Yes
**Relevance to GTOS:** High (concept, not direct application)
**GTOS question addressed:** Q-1.4
**Key finding:** Temporal hierarchies from non-overlapping aggregation can be reconciled to produce coherent forecasts that outperform any single level. 5-15% RMSE improvement. But designed for continuous series, not categorical votes.
**Key equation:** Reconciled: y_tilde = S(S'W^{-1}S)^{-1}S'W^{-1} * y_hat_base
**Testable on GTOS data:** Medium -- requires converting categorical signals to probability scores
**Data availability:** R packages `thief` and `hts`

---

### Forecast Combinations (Handbook Chapter)
**Authors:** Allan Timmermann | **Year:** 2006 | **Source:** Handbook of Economic Forecasting, Vol. 1, Ch. 4
**Quality Tier:** 1 | **Citations:** ~1,500+
**Asset class tested:** Survey (equities, macro, FX)
**OOS validation:** N/A (review)
**Relevance to GTOS:** High
**GTOS question addressed:** Q-1.4
**Key finding:** **MOST IMPORTANT FOR GTOS.** Simple combinations (equal weights) that ignore correlations between forecast errors often dominate refined schemes. Three reasons: model misspecification, non-stationarity, estimation error. Directly supports GTOS's majority vote at n=300.
**Key equation:** Optimal weights w* = argmin E[(y - sum w_i f_i)^2] require estimating Sigma, which is unstable in small samples
**Testable on GTOS data:** High -- compare equal vs reliability-weighted using OOS accuracy logs
**Data availability:** Theoretical framework

---

### Out-of-Sample Equity Premium Prediction: Combination Forecasts and Links to the Real Economy
**Authors:** David E. Rapach, Jack K. Strauss, Guofu Zhou | **Year:** 2010 | **Source:** Review of Financial Studies, 23(2), 821-862
**Quality Tier:** 1 (RFS) | **Citations:** ~1,200+
**Asset class tested:** US equities (S&P 500)
**OOS validation:** Yes (1965-2005)
**Relevance to GTOS:** High
**GTOS question addressed:** Q-1.4
**Key finding:** Individual predictors fail OOS due to model uncertainty. Equal-weighted mean combination delivers consistent OOS gains. Mean combination outperforms best individual predictor.
**Key equation:** f_c = (1/N) * sum f_i; R^2_OOS = 1 - sum(y-f_c)^2 / sum(y-f_bar)^2
**Testable on GTOS data:** High
**Data availability:** Methodology transferable

---

### Multiresolution Forecasting for Futures Trading Using Wavelet Decompositions
**Authors:** B.L. Zhang, R. Coggins, M.A. Jabri, D. Dersch, B. Flower | **Year:** 2001 | **Source:** IEEE Trans. Neural Networks, 12(4), 765-775
**Quality Tier:** 2 | **Citations:** ~200+
**Asset class tested:** Futures (ASX SPI, US T-Bond)
**OOS validation:** Yes (1-2 years)
**Relevance to GTOS:** Medium
**GTOS question addressed:** Q-1.4
**Key finding:** Each temporal scale uses its own model with its own feature set. Scale-specific forecasts recombined via inverse wavelet transform. 15-30% OOS improvement. Validates multi-timeframe approach.
**Testable on GTOS data:** Medium
**Data availability:** PyWavelets available

---

### Time Series Momentum
**Authors:** Tobias J. Moskowitz, Yao Hua Ooi, Lasse Heje Pedersen | **Year:** 2012 | **Source:** Journal of Financial Economics, 104(2), 228-250
**Quality Tier:** 1 (JFE) | **Citations:** ~3,000+
**Asset class tested:** 58 liquid futures (gold included)
**OOS validation:** Yes (1965-2009)
**Relevance to GTOS:** Medium
**GTOS question addressed:** Q-1.4
**Key finding:** "Barbell" structure (short + long lookback, dropping medium) captures most trend information. Challenges GTOS's 3-level approach: does H4 add information beyond D1 and H1?
**Key equation:** TSMOM = sign(r_{t-h,t}) * r_{t,t+1}
**Testable on GTOS data:** High -- compare D1+H1 vs D1+H4+H1
**Data availability:** Available

**CROSS-REFERENCE:** Already in Priority A search (Q-13.1).

---

### Forecast Reconciliation: A Review
**Authors:** George Athanasopoulos, Rob J. Hyndman, Nikolaos Kourentzes, Anastasios Panagiotelis | **Year:** 2024 | **Source:** International Journal of Forecasting, 40(2), 430-456
**Quality Tier:** 1 | **Citations:** ~100+
**Asset class tested:** Review
**OOS validation:** N/A
**Relevance to GTOS:** Medium
**GTOS question addressed:** Q-1.4
**Key finding:** Bottom-up approach (aggregate from finest level) is surprisingly competitive with complex reconciliation. For GTOS: building signal from M15 upward may be as good as starting from D1.
**Testable on GTOS data:** Medium
**Data availability:** R/Python packages available

---

### Forecasting Based on Decomposed Financial Return Series: A Wavelet Analysis
**Authors:** Theo Berger | **Year:** 2016 | **Source:** Journal of Forecasting, 35(5), 419-433
**Quality Tier:** 2 | **Citations:** ~50+
**Asset class tested:** S&P 500, DAX, FTSE
**OOS validation:** Yes (rolling window VaR)
**Relevance to GTOS:** Medium
**GTOS question addressed:** Q-1.4
**Key finding:** Short-run information (1-2 wavelet scales) drives 95% VaR forecasts. Not all scales contribute equally. Most granular timeframes may dominate.
**Testable on GTOS data:** Medium
**Data availability:** PyWavelets available

---

### Improving Forecasting via Multiple Temporal Aggregation
**Authors:** Nikolaos Kourentzes, Fotios Petropoulos, Juan R. Trapero | **Year:** 2014 | **Source:** Foresight, 34, 12-17
**Quality Tier:** 2 | **Citations:** ~150+
**Asset class tested:** M3 competition data
**OOS validation:** Yes
**Relevance to GTOS:** Low-Medium
**GTOS question addressed:** Q-1.4
**Key finding:** MAPA estimates trend from coarse scale, seasonality from fine scale. Could inspire analogous approach: estimate trend from D1, momentum from H4, entry timing from H1.
**Testable on GTOS data:** Low
**Data availability:** R package `MAPA`

---

<a id="q-15"></a>
## 6. Q-1.5: Optimal Feature Count for Small Samples

**Question:** With ~300 trades and ~30-50 features, are we overfitting? Does the curse of dimensionality apply to an LLM evaluator?

**Verdict:** For a traditional classifier, 300 samples with 30-50 features is dangerous (EPV 6-10). But GTOS's LLM does NOT fit coefficients to the 300 trades -- it uses pre-trained knowledge. The classical dimensionality curse is sidestepped. **The real overfitting risk is at the human/research level:** feature selection, prompt engineering, and threshold calibration each constitute "trials." The Deflated Sharpe Ratio (Bailey & LdP 2014) quantifies this.

**COVERAGE: THIN for LLM-specific angle** -- no paper studies LLM-as-classifier dimensionality constraints directly.

---

### The Probability of Backtest Overfitting
**Authors:** David H. Bailey, Jonathan M. Borwein, Marcos Lopez de Prado, Qiji Jim Zhu | **Year:** 2014 | **Source:** Notices of the AMS / Journal of Computational Finance
**Quality Tier:** 1 | **Citations:** ~400+
**Asset class tested:** Simulated + real strategies
**OOS validation:** Yes (CSCV framework)
**Relevance to GTOS:** High
**GTOS question addressed:** Q-1.5
**Key finding:** PBO metric via Combinatorially Symmetric Cross-Validation. Even with N~20 variations, PBO can exceed 50% if sample size is small. If MSO features were selected from a larger pool by examining in-sample performance, PBO is non-trivial.
**Key equation:** PBO = P(R_bar_OOS < 0 | CSCV)
**Testable on GTOS data:** High -- can compute PBO on 367-trade dataset
**Data availability:** Python `pypbo` on GitHub

---

### The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest Overfitting, and Non-Normality
**Authors:** David H. Bailey, Marcos Lopez de Prado | **Year:** 2014 | **Source:** Journal of Portfolio Management, 40(5), 94-107
**Quality Tier:** 1 | **Citations:** ~300+
**Asset class tested:** Simulated + hedge fund strategies
**OOS validation:** Yes
**Relevance to GTOS:** High
**GTOS question addressed:** Q-1.5
**Key finding:** DSR corrects observed Sharpe for: number of strategies tested N, non-normality, sample length. At n=300, if N=50 feature combinations examined, DSR correction is modest; at N=500, it becomes severe.
**Key equation:** DSR = (SR_hat - SR_0) / sqrt[(1 - gamma_3*SR + (gamma_4-1)/4 * SR^2) / T]
**Testable on GTOS data:** High -- compute DSR for 367-trade batch
**Data availability:** Formula self-contained

---

### A Reality Check for Data Snooping
**Authors:** Halbert White | **Year:** 2000 | **Source:** Econometrica, 68(5), 1097-1126
**Quality Tier:** 1 (Econometrica) | **Citations:** ~2,000+
**Asset class tested:** Simulated + equity trading rules
**OOS validation:** Yes (bootstrap)
**Relevance to GTOS:** High
**GTOS question addressed:** Q-1.5
**Key finding:** Bootstrap procedure for testing whether best model from specification search has genuine superiority. Controls family-wise error rate across all tested specifications.
**Key equation:** V_bar = max_k {N^{1/2} * f_bar_k}; p-value from bootstrap
**Testable on GTOS data:** High
**Data availability:** Bootstrap self-contained

---

### Empirical Asset Pricing via Machine Learning
**Authors:** Shihao Gu, Bryan T. Kelly, Dacheng Xiu | **Year:** 2020 | **Source:** Review of Financial Studies, 33(5), 2223-2273
**Quality Tier:** 1 (RFS) | **Citations:** ~2,500+
**Asset class tested:** US equities (30,000+ stocks, 94 features)
**OOS validation:** Yes (1987-2016)
**Relevance to GTOS:** Medium-High
**GTOS question addressed:** Q-1.5
**Key finding:** All ML methods converge on the same small set of dominant features from 94 candidates. Sample splitting MUST be time-aware (rolling window), not random CV.
**Key equation:** R^2_OOS ~ 0.5% monthly for best ML method
**Testable on GTOS data:** Medium -- feature importance methodology (SHAP) applicable
**Data availability:** Methodology transferable

---

### An Introduction to Variable and Feature Selection
**Authors:** Isabelle Guyon, Andre Elisseeff | **Year:** 2003 | **Source:** Journal of Machine Learning Research, 3, 1157-1182
**Quality Tier:** 1 | **Citations:** ~15,000+
**Asset class tested:** Multiple domains (review)
**OOS validation:** N/A
**Relevance to GTOS:** Medium-High
**GTOS question addressed:** Q-1.5
**Key finding:** Feature selection itself is a form of model fitting subject to overfitting. Must use nested cross-validation. Start with filters (univariate), then wrappers (RFE), then embedded (L1).
**Testable on GTOS data:** High
**Data availability:** Methodology

---

### On Over-fitting in Model Selection and Subsequent Selection Bias
**Authors:** Gavin C. Cawley, Nicola L.C. Talbot | **Year:** 2010 | **Source:** JMLR, 11(70), 2079-2107
**Quality Tier:** 1 | **Citations:** ~1,500+
**Asset class tested:** UCI benchmarks
**OOS validation:** Yes (Monte Carlo)
**Relevance to GTOS:** Medium-High
**GTOS question addressed:** Q-1.5
**Key finding:** Over-fitting in model selection is of comparable magnitude to differences between algorithms. Nested CV is the minimum requirement. If features were added based on observed correlation with outcomes in the same dataset, performance estimate is inflated.
**Key equation:** Bias = E[L_selected] - E[L_true]
**Testable on GTOS data:** High -- audit feature selection history
**Data availability:** Methodology

---

### Regression Modeling Strategies (EPV Framework)
**Authors:** Frank E. Harrell Jr. | **Year:** 2015 | **Source:** Springer (book, 2nd ed.)
**Quality Tier:** 1 | **Citations:** ~10,000+
**Asset class tested:** Clinical prediction (biostatistics)
**OOS validation:** Yes
**Relevance to GTOS:** Medium
**GTOS question addressed:** Q-1.5
**Key finding:** EPV rule: need 10-20 events per predictor. At 300 trades, 62% WR: ~114 losses = events. EPV=10: max 11 features. EPV=20: max 5-6. **BUT this applies to coefficient-fitting models, NOT LLM evaluation.** The EPV constraint applies only if building a traditional classifier as benchmark.
**Key equation:** EPV = min(events, non-events) / p; require EPV >= 10-20
**Testable on GTOS data:** High (for traditional classifier benchmark)
**Data availability:** Formulas self-contained

---

### TabLLM: Few-shot Classification of Tabular Data with Large Language Models
**Authors:** Stefan Hegselmann, Alejandro Buendia, Hunter Lang, Monica Agrawal, Xiaoyi Jiang, David Sontag | **Year:** 2023 | **Source:** AISTATS 2023
**Quality Tier:** 2 | **Citations:** ~200+
**Asset class tested:** UCI benchmarks (healthcare, census, financial)
**OOS validation:** Yes
**Relevance to GTOS:** Medium
**GTOS question addressed:** Q-1.5
**Key finding:** LLMs classify tabular data competitively in 0-8 shot settings via in-context learning. Descriptive feature names enhance performance. Validates GTOS's approach of providing structured MSO to Claude for qualitative evaluation. The LLM leverages pre-trained knowledge, not coefficient fitting.
**Key equation:** GPT-3 AUC with 0-8 shots ~ XGBoost AUC with 100+ samples
**Testable on GTOS data:** Medium -- test whether reducing MSO to ~15 features changes accuracy
**Data availability:** Code/data available

---

<a id="q-16"></a>
## 7. Q-1.6: Gold vs FX Feature Requirements

**Question:** Should the MSO have gold-specific features not needed for FX? Gold has unique properties: xi=0.35 (vs FX 0.16-0.22), GARCH 0.99, kurtosis 34.85.

**Verdict:** Gold IS structurally different from FX in at least five measurable ways. Session-specific ATR normalization is the highest-priority gold feature. DXY intraday correlation is too thin in the literature. COMEX delivery and central bank effects have no academic evidence at intraday level.

**COVERAGE: MODERATE** -- smaller literature than FX but high-quality empirical work.

---

### The Financial Economics of Gold: A Survey
**Authors:** Fergal A. O'Connor, Brian M. Lucey, Jonathan A. Batten, Dirk G. Baur | **Year:** 2015 | **Source:** International Review of Financial Analysis, 41, 186-205
**Quality Tier:** 2 | **Citations:** ~500+
**Asset class tested:** Gold (all instruments)
**OOS validation:** Survey
**Relevance to GTOS:** Medium
**GTOS question addressed:** Q-1.6
**Key finding:** Gold operates simultaneously as commodity, currency, and safe haven. Market microstructure differs fundamentally from FX: physical delivery constraints, London/COMEX price discovery split, central bank demand.
**Testable on GTOS data:** Indirect
**Data availability:** Available

---

### Who Sets the Price of Gold? London or New York
**Authors:** Martin Hauptfleisch, Talis J. Putnins, Brian M. Lucey | **Year:** 2016 | **Source:** Journal of Futures Markets, 36(12), 1127-1156
**Quality Tier:** 2 (JFM) | **Citations:** ~100+
**Asset class tested:** Gold (London spot vs COMEX futures, 17 years)
**OOS validation:** No
**Relevance to GTOS:** Medium
**GTOS question addressed:** Q-1.6
**Key finding:** Both London and NY contribute to gold price discovery, but NY futures play a larger role ON AVERAGE despite lower volume. Price discovery share varies intraday and across years. No analogue in FX.
**Key equation:** Information share (Hasbrouck 1995): IS_j = (psi_j * sigma_eta)^2 / total
**Testable on GTOS data:** Partially -- compare relative session volatility for gold vs FX
**Data availability:** Partial (need futures data for full replication)
**Per-instrument note:** Gold-specific. FX pairs have more continuously distributed price discovery.

---

### Fixing a Leaky Fixing: Short-Term Market Reactions to the London PM Gold Price Fixing
**Authors:** Andrew Caminschi, Richard Heaney | **Year:** 2014 | **Source:** Journal of Futures Markets, 34(11), 1003-1039
**Quality Tier:** 2 (JFM) | **Citations:** ~200+
**Asset class tested:** Gold (COMEX futures, GLD ETF, around London PM fix)
**OOS validation:** No (event study 2007-2013)
**Relevance to GTOS:** Medium
**GTOS question addressed:** Q-1.6
**Key finding:** Information from the London fix leaked into markets pre-2015. Post-reform (March 2015), the fix STILL creates a liquidity event at known times. The fix aggregates large institutional orders, creating potential OB zone formation opportunities unique to gold.
**Testable on GTOS data:** Yes -- test M15 bars around 10:30 AM and 3:00 PM London time for elevated volatility
**Data availability:** Available (fix times public, M15 OHLCV from MT5)
**Per-instrument note:** Gold-only. No FX analogue.

---

### Intraday Seasonality in Efficiency, Liquidity, Volatility and Volume: Platinum and Gold Futures
**Authors:** Gbenga Ibikunle, Frank McGroarty, Owain ap Gwilym | **Year:** 2018 | **Source:** Journal of Commodity Markets, 11, 59-71
**Quality Tier:** 3 | **Citations:** ~50+
**Asset class tested:** Gold and platinum futures (TOCOM, COMEX)
**OOS validation:** No
**Relevance to GTOS:** High
**GTOS question addressed:** Q-1.6
**Key finding:** Gold has W-shaped efficiency pattern vs FX bimodal. Tokyo and London open show highest inefficiency. Informed trading evidence in NY, not Tokyo. Session identity matters MORE for gold than FX.
**Key equation:** VR_k = Var(k-period) / (k * Var(1-period)); deviations from 1.0 = inefficiency
**Testable on GTOS data:** Yes -- compute M15 variance ratios by session for gold vs FX
**Data availability:** Available
**Per-instrument note:** Gold has W-shape; expect FX to show bimodal pattern.

---

### Stylized Facts of Intraday Precious Metals
**Authors:** Jonathan Batten, Brian Lucey, Frank McGroarty, Maurice Peat, Andrew Urquhart | **Year:** 2017 | **Source:** PLOS ONE, 12(4), e0174232
**Quality Tier:** 3 | **Citations:** ~80+
**Asset class tested:** Gold, silver, platinum, palladium (5-min, 2000-2015)
**OOS validation:** No
**Relevance to GTOS:** High
**GTOS question addressed:** Q-1.6
**Key finding:** Gold has stronger negative autocorrelation at short horizons than FX (rho_1 ~ -0.05 vs ~-0.02), indicating faster mean-reversion. Tightest spreads and most symmetric returns among precious metals. Session-dependent autocorrelation patterns.
**Key equation:** rho_1(gold) ~ -0.05 vs rho_1(FX) ~ -0.02
**Testable on GTOS data:** Yes -- compute M15 autocorrelation for gold vs FX
**Data availability:** Available
**Per-instrument note:** Gold-specific: tighter TP targets or faster trailing stop activation may be warranted.

---

### Market Making in Spot Precious Metals
**Authors:** Alexander Barzykin, Philippe Bergault, Olivier Gueant | **Year:** 2024 | **Source:** arXiv:2404.15478
**Quality Tier:** 3 | **Citations:** Early stage
**Asset class tested:** Gold spot (EFP spread)
**OOS validation:** Yes (calibrated to real data)
**Relevance to GTOS:** Medium
**GTOS question addressed:** Q-1.6
**Key finding:** Gold's EFP spread follows nested OU with multiple relaxation times (hours and days). This dual-timescale mean-reversion is gold-specific and may explain different OB zone lifetimes for gold vs FX.
**Key equation:** dS = kappa_1(mu-S)dt + sigma_1*dW_1; dmu = kappa_2(theta-mu)dt + sigma_2*dW_2
**Testable on GTOS data:** Partially (need gold futures for full replication)
**Data availability:** Partial

---

### Are Gold and Silver Prices Being Fixed?
**Authors:** Rosa M. Abrantes-Metz, Albert D. Metz | **Year:** 2015 | **Source:** Working Paper (NYU Stern)
**Quality Tier:** 3 | **Citations:** ~100+
**Asset class tested:** Gold (London PM fix, 2001-2013)
**OOS validation:** No
**Relevance to GTOS:** Low-Medium
**GTOS question addressed:** Q-1.6
**Key finding:** Pre-reform anomalies documented. Post-reform period has not been equivalently analyzed. Fix STILL aggregates large orders at known times.
**Testable on GTOS data:** Partially -- test post-reform fix-time patterns
**Data availability:** Available

---

### Weekday Effects on Gold: Tokyo, London, and New York Markets
**Authors:** Hao-Chang Yang, Chung-Li Yu | **Year:** 2016 | **Source:** Investment Management and Financial Innovations, 13(2)
**Quality Tier:** 3 | **Citations:** ~30+
**Asset class tested:** Gold spot (2009-2015)
**OOS validation:** No
**Relevance to GTOS:** Low-Medium
**GTOS question addressed:** Q-1.6
**Key finding:** Monday returns in Tokyo significantly negative; Wednesday returns in London significantly positive. Weekday effects vary by session, unlike FX.
**Key equation:** r_{d,s} = alpha + sum beta_d * D_d (day-of-week dummies by session)
**Testable on GTOS data:** Yes
**Data availability:** Available
**Per-instrument note:** Day-of-week effect is gold-specific.

---

### Gold Markets Around the World: Who, Where, Why
**Authors:** Brian Lucey, Charles Larkin, Fergal O'Connor | **Year:** 2013 | **Source:** SSRN / handbook chapter
**Quality Tier:** 3 | **Citations:** ~60+
**Asset class tested:** Gold (global structure)
**OOS validation:** N/A
**Relevance to GTOS:** Medium
**GTOS question addressed:** Q-1.6
**Key finding:** Gold has multi-layered structure (LBMA -> COMEX -> ETFs -> retail CFD). Price flows top-down with variable lag. Gold OHLCV from retail broker may reflect price discovery with more lag than FX.
**Testable on GTOS data:** Partially
**Data availability:** Available

---

<a id="q-17"></a>
## 8. Q-1.7: Order Flow Estimation from OHLCV

**Question:** Can we approximate institutional order flow from OHLCV without Level 2 access? Beyond VPIN (already found), what methods exist?

**Verdict:** Three implementable approaches exist: (1) CLV from OHLC alone, (2) BVC at ~76% accuracy for M15, (3) EDGE spread estimator for liquidity. Recommended implementation order: CLV first (trivial), BVC second (needs sigma), EDGE third (R package available).

**COVERAGE: MODERATE-TO-GOOD** -- multiple peer-reviewed methods exist, but validation on FX/gold specifically is thin.

---

### Discerning Information from Trade Data
**Authors:** David Easley, Marcos Lopez de Prado, Maureen O'Hara | **Year:** 2016 | **Source:** Journal of Financial Economics, 120(2), 269-285
**Quality Tier:** 1 (JFE) | **Citations:** ~200+
**Asset class tested:** S&P 500 E-mini futures (CME)
**OOS validation:** Yes
**Relevance to GTOS:** High
**GTOS question addressed:** Q-1.7
**Key finding:** **THE FORMAL BVC PAPER.** BVC classifies volume as buy/sell using standardized price change within a bar. BVC better linked to information-based trading proxies than tick rules when applied to bar data. Primary OHLCV-to-flow method.
**Key equation:** V_buy = V_total * Phi((Close - Open) / (sigma * sqrt(dt)))
**Testable on GTOS data:** Yes -- directly implementable on M15 OHLCV + tick volume
**Data availability:** Available

---

### Evaluating Trade Classification Algorithms: BVC vs Tick Rule vs Lee-Ready
**Authors:** Bidisha Chakrabarty, Roberto Pascual, Andriy Shkilko | **Year:** 2015 | **Source:** Journal of Financial Markets, 25, 52-79
**Quality Tier:** 2 (JFM) | **Citations:** ~200+
**Asset class tested:** US equities (NASDAQ)
**OOS validation:** Yes (signed trades as ground truth)
**Relevance to GTOS:** High (CRITICAL CAUTION)
**GTOS question addressed:** Q-1.7
**Key finding:** **CAUTION PAPER.** When ground-truth signed trades available: tick rule 77-94%, Lee-Ready 80-95%, BVC only 64-80%. BVC accuracy depends on bar length: 1-second=64%, 1-hour=80%. At M15: ~76% (interpolated). BVC is noisy -- better than random but worse than tick-level methods. Use as supplementary feature, not primary signal.
**Key equation:** Accuracy = correctly classified volume / total volume. BVC at M15: ~76%
**Testable on GTOS data:** Yes (implement BVC, test predictive value)
**Data availability:** Available (OHLCV from MT5)

---

### Estimating Order Imbalance Using Low Frequency Data
**Authors:** JinGi Ha, Jianfeng Hu | **Year:** 2017 | **Source:** EFMA 2017 Conference
**Quality Tier:** 3 | **Citations:** ~30+
**Asset class tested:** US equities (daily/hourly)
**OOS validation:** Yes (predicts future returns OOS)
**Relevance to GTOS:** High
**GTOS question addressed:** Q-1.7
**Key finding:** Low Frequency Order Imbalance (LFOI) proxies: CLV = (2C-H-L)/(H-L), range [-1,1]. Positive = buying pressure. Requires NO volume data. Combined with BVC, gives two independent flow signals.
**Key equation:** CLV = (2*Close - High - Low) / (High - Low)
**Testable on GTOS data:** Yes -- trivially computable from M15 OHLCV
**Data availability:** Available

---

### A Simple Way to Estimate Bid-Ask Spreads from Daily High and Low Prices
**Authors:** Shane A. Corwin, Paul H. Schultz | **Year:** 2012 | **Source:** Journal of Finance, 67(2), 719-760
**Quality Tier:** 1 (JF) | **Citations:** ~1,500+
**Asset class tested:** US equities (NYSE/AMEX, 1993-2006)
**OOS validation:** Yes (vs TAQ effective spreads)
**Relevance to GTOS:** High
**GTOS question addressed:** Q-1.7
**Key finding:** Spread estimator from daily high/low only. Daily highs are almost always buy trades, lows sell trades. Separates variance (proportional to time) from spread (not proportional). Applicable to M15 bars.
**Key equation:** S = 2(e^alpha - 1)/(1 + e^alpha); alpha = sqrt(2*beta) - sqrt(beta)
**Testable on GTOS data:** Yes
**Data availability:** Available

---

### A Simple Estimation of Bid-Ask Spreads from Daily Close, High, and Low Prices
**Authors:** Farshid Abdi, Angelo Ranaldo | **Year:** 2017 | **Source:** Review of Financial Studies, 30(12), 4437-4480
**Quality Tier:** 1 (RFS) | **Citations:** ~500+
**Asset class tested:** US equities (1926-2015)
**OOS validation:** Yes (vs TAQ)
**Relevance to GTOS:** High
**GTOS question addressed:** Q-1.7
**Key finding:** Improves on Corwin-Schultz by using close price. More robust for FX/gold where spread dynamics differ from equities. Independent of trade direction.
**Key equation:** S^2 = 4 * E[(C-(H+L)/2)^2] - E[(H-L)^2] / k
**Testable on GTOS data:** Yes
**Data availability:** Available

---

### Efficient Estimation of Bid-Ask Spreads from Open, High, Low, and Close Prices
**Authors:** David Ardia, Emanuele Guidotti, Tim A. Kroencke | **Year:** 2024 | **Source:** Journal of Financial Economics, 161, 103916
**Quality Tier:** 1 (JFE, state-of-the-art) | **Citations:** ~50+
**Asset class tested:** US equities (full cross-section)
**OOS validation:** Yes (Monte Carlo + empirical vs TAQ)
**Relevance to GTOS:** High
**GTOS question addressed:** Q-1.7
**Key finding:** **STATE-OF-THE-ART.** EDGE estimator optimally uses ALL four OHLC prices simultaneously, achieving lowest variance. Corwin-Schultz and Abdi-Ranaldo are special cases using incomplete OHLC subsets. Open-source R package `bidask`.
**Key equation:** EDGE = optimal GMM combination of all pairwise OHLC differences
**Testable on GTOS data:** Yes -- directly computable from M15 OHLC
**Data availability:** Available (R package `bidask` on CRAN)

---

### Analysis of Stock Market Volatility: Adjusted VPIN with High-Frequency Data
**Authors:** Various | **Year:** 2021 | **Source:** International Review of Economics & Finance, 75
**Quality Tier:** 3 | **Citations:** ~40+
**Asset class tested:** Chinese A-shares
**OOS validation:** Yes (OOS volatility prediction)
**Relevance to GTOS:** Medium
**GTOS question addressed:** Q-1.7
**Key finding:** Adjusted VPIN (A-VPIN) incorporates price trend into BVC. 37.86% higher correlation with price change than standard VPIN. Trend-adjusted BVC is implementable on M15.
**Key equation:** A-VPIN = |V_buy - V_sell| / (V_buy + V_sell), with trend-adjusted BVC
**Testable on GTOS data:** Yes
**Data availability:** Available

---

<a id="synthesis"></a>
## 9. Cross-Question Synthesis

### What the Papers Collectively Say About GTOS Feature Engineering

**1. Kill tick volume as a directional feature immediately.** The hierarchy of volume data quality is clear: institutional signed order flow (Rank 1) -> aggregate interdealer (Rank 2) -> interdealer tick counts (Rank 3) -> aggregate retail sentiment (Rank 4) -> single-broker CFD tick counts (Rank 5). GTOS has only Rank 5 data. All "volume is informative" evidence uses Rank 1-3 data. (Evans-Lyons 2002, Menkhoff et al. 2016, Cespa et al. 2022)

**2. Replace tick volume with order flow proxies from OHLCV.** CLV = (2C-H-L)/(H-L) requires zero volume data and measures closing position within the bar. BVC at ~76% accuracy gives buy/sell classification from (C-O)/sigma. Together they provide two independent flow signals from price data alone, avoiding the tick volume quality problem entirely. (Ha & Hu 2017, Easley et al. 2016)

**3. Spread is a valid feature -- but for volatility, not direction.** Spread surprise (actual minus session expectation) is the right formulation. Implement as shadow feature in WF-1. (Bollerslev & Domowitz 1993, Hartmann 1999, Caporin et al. 2015)

**4. Keep the majority vote; don't optimize weights yet.** The forecast combination puzzle strongly supports equal-weighted combination at n<300. Moving to reliability-weighted voting would require 100+ OOS trades per timeframe and evidence of >20pp accuracy gap. (Timmermann 2006, Rapach et al. 2010)

**5. Gold DOES need different features than FX.** Five measurable differences documented: heavier tails (structural, not just distributional), W-shaped efficiency pattern, faster short-horizon mean-reversion, London/NY price discovery splits, and fix-time liquidity events. Session-specific ATR normalization is the highest-priority implementable feature. (Ibikunle 2018, Batten et al. 2017, Hauptfleisch 2016, Caminschi 2014)

**6. The LLM sidesteps classical dimensionality curse, but human overfitting is the real risk.** The LLM doesn't fit coefficients to 300 trades -- it uses pre-trained knowledge. The EPV constraint doesn't apply. But every time the researcher examined the 367-trade dataset to decide which features to include, they consumed a "trial." The DSR (Bailey & LdP 2014) quantifies this cumulative overfitting risk. (Harrell 2015, Bailey et al. 2014, Cawley & Talbot 2010, Hegselmann et al. 2023)

**7. Use MI-based selection to audit the current MSO.** mRMR/JMI with KSG estimator can identify which of the ~30-50 features are signal vs noise. The key methodological requirements: KSG estimator (not histogram), block bootstrap for significance, nested CV for validation. (Peng et al. 2005, Kraskov et al. 2004, Vergara & Estevez 2014, Dimpfl & Peter 2013)

### The Volume Data Hierarchy

| Rank | Data Type | Info Content | Available? | Papers |
|------|-----------|-------------|------------|--------|
| 1 | Signed institutional order flow | HIGH | NO | Evans-Lyons 2002, Menkhoff 2016 |
| 2 | Aggregate interdealer volume | MODERATE | NO | Cespa et al. 2022 |
| 3 | Interdealer tick frequency | LOW-MOD | NO | Ito-Hashimoto 2006 |
| 4 | Aggregate retail sentiment | LOW | Partial | OANDA, IG |
| 5 | Single-broker CFD tick count | VERY LOW | YES | None (no academic study) |
| ALT | OHLCV-derived flow proxies | MODERATE | YES | Easley 2016, Ha-Hu 2017, Ardia 2024 |

---

<a id="gtos-implications"></a>
## 10. Specific GTOS Implications -- What to Test

### Priority 1: MI-Based Feature Audit (from Q-1.1)

**Test:** Apply mRMR/JMI with KSG estimator to the ~30-50 MSO features vs binary trade outcome (win/loss).

**Method:**
1. Extract MSO features from historical trade data: OB body ratio, displacement quality, zone width, premium/discount position, H4 alignment, D1 alignment, FVG presence, ATR, etc.
2. Compute pairwise MI using sklearn's `mutual_info_classif` (uses KSG internally)
3. Apply JMI selection to rank features by joint information with target
4. Use block bootstrap (Dimpfl & Peter 2013) for significance testing
5. Stop adding features when CMI increment drops below threshold (Beraha et al. 2019)

**Prediction:** The top 5-8 features will capture >80% of the total MI. Many MSO features are likely redundant (premium/discount correlates with retracement depth).

**Required data:** Historical trade log + MSO feature values from pipeline_state/ files.

### Priority 2: OHLCV Flow Proxies (from Q-1.7)

**Test:** Implement CLV and BVC as new MSO features; evaluate predictive value for OB zone continuation.

**Method:**
1. CLV = (2C - H - L) / (H - L) per M15 bar (trivial, no volume needed)
2. BVC = tick_volume * Phi((C - O) / (ATR_14 * sqrt(15/60))) per M15 bar
3. Compute cumulative flow (sum of BVC over recent bars) as net order flow proxy
4. Correlate with subsequent OB zone continuation rate
5. Compare CLV-only vs BVC-only vs CLV+BVC

**Prediction:** CLV and BVC will show modest but measurable correlation (~0.1-0.2) with next-bar direction. The flow signal should be strongest during kill zones and weakest outside.

**Required data:** M15 OHLCV + tick volume from MT5. Shadow logging only.

### Priority 3: Spread Surprise Filter (from Q-1.3)

**Test:** Compute spread surprise (actual minus session expectation) as volatility regime indicator.

**Method:**
1. Build 30-day rolling expected spread per (session, day-of-week, instrument) from MT5 spread data
2. Compute spread_surprise = actual_spread / expected_spread
3. Flag bars where spread_surprise > 1.5x as "elevated uncertainty"
4. Shadow-log whether trades during elevated-spread periods have different WR/expectancy

**Prediction:** Trades taken during elevated-spread periods will have lower WR (Bollerslev-Domowitz 1993).

**Required data:** MT5 spread data (available from tick history).

### Priority 4: Gold Session-Specific ATR (from Q-1.6)

**Test:** Compute separate ATR for London, NY, and overlap sessions for gold. Compare to uniform ATR.

**Method:**
1. Compute ATR_London, ATR_NY, ATR_overlap from M15 candles within each session
2. Compare whether OB zone sizing using session-specific ATR improves SL/TP placement
3. Test whether gold's W-shaped volatility pattern (Ibikunle 2018) affects OB continuation by session

**Prediction:** London session ATR will be higher than overlap for gold; FX pairs will show different patterns. Session-specific ATR will improve SL calibration.

**Required data:** M15 OHLCV by session.

### Priority 5: Compute Deflated Sharpe Ratio (from Q-1.5)

**Test:** Quantify overfitting risk from the number of "trials" during system development.

**Method:**
1. Count the number of feature/rule variations examined during GTOS development (N)
2. Compute observed Sharpe from 367-trade batch
3. Compute DSR using Bailey & LdP 2014 formula with skewness, kurtosis from trade returns
4. Assess whether observed edge survives DSR correction

**Prediction:** If N < 100, DSR correction will be modest (~10-20% reduction). If N > 500, DSR may show the edge is not significant after correction.

**Required data:** Trade returns + development history audit.

### Priority 6: Barbell Test -- D1+H1 vs D1+H4+H1 (from Q-1.4)

**Test:** Does H4 add information beyond D1 and H1 for directional alignment?

**Method:**
1. For each historical trade, extract D1, H4, H1 directional signals
2. Compare: accuracy of (D1+H1 agree) vs (2-of-3 D1/H4/H1 agree)
3. If no significant difference, H4 may be redundant

**Prediction:** Based on the barbell hypothesis (Moskowitz et al. 2012), D1+H1 may capture most directional information. H4 adds little beyond redundancy.

**Required data:** Historical trade log with per-timeframe signals. Post-WF-1 analysis only.

### NOT Recommended (Insufficient Evidence)

| Feature Idea | Evidence Status | Decision |
|-------------|----------------|----------|
| Tick volume for direction | NEGATIVE (Menkhoff 2016) | KILL |
| DXY intraday correlation | THIN (no academic evidence at M15) | DEFER |
| COMEX delivery effects | THIN (no evidence at intraday level) | DEFER |
| Central bank reserve dates | Too infrequent for M15 features | REJECT |
| Reliability-weighted timeframe voting | Requires >100 OOS trades per TF | DEFER to post-WF-1 |

---

<a id="rejected"></a>
## 11. Rejected Papers (considered but did not pass quality filter)

| Paper | Reason for Rejection |
|-------|---------------------|
| Various MQL5/ForexFactory forum posts on tick volume | Not peer-reviewed, practitioner opinion |
| Marney ~2011 (tick volume 90% correlation claim) | Tier 4, no methodology, no peer review |
| Various MDPI papers on forex volume indicators | MDPI special issues, excluded per protocol |
| Multiple MDPI papers on gold prediction | MDPI/Hindawi, excluded per protocol |
| "Predictive modeling of FX trading signals using ML" (ScienceDirect 2025) | Pure DL black box |
| Cogent Economics paper on FX spread + macro (2022) | Tier 4 open-access, weak methodology |
| TIC-FusionNet (PLOS One 2025) | Pure DL multimodal fusion, no feature analysis |
| MSTAN (Information Sciences 2025) | Pure DL attention network, no OOS on trading data |
| Stock Movement Prediction with MSGCA (2025) | Requires sentiment data, no small-sample analysis |
| WaveLSFormer (arXiv 2025) | Requires large training data, no transferability to n=300 |
| Baur, Lucey (2010) "Is Gold a Hedge or Safe Haven?" | Daily/weekly frequency, not intraday MSO features |
| Various RSI/MACD gold trading papers | Excluded per protocol -- indicator optimization |
| Wang et al. (2023) "Gold forecast with DL" | Pure DL black box |
| Aizenman (2012) "Central Banks and Gold Puzzles" | Macro-level, not intraday features |
| Multiple TradingView/Medium articles | Non-academic, no empirical validation |

---

<a id="references"></a>
## 12. Full Reference List (alphabetical)

1. Abdi, F. & Ranaldo, A. (2017). A Simple Estimation of Bid-Ask Spreads from Daily Close, High, and Low Prices. Review of Financial Studies, 30(12), 4437-4480.
2. Abrantes-Metz, R.M. & Metz, A.D. (2015). Are Gold and Silver Prices Being Fixed? NYU Stern Working Paper.
3. Ardia, D., Guidotti, E. & Kroencke, T.A. (2024). Efficient Estimation of Bid-Ask Spreads from OHLC Prices. Journal of Financial Economics, 161, 103916.
4. Athanasopoulos, G., Hyndman, R.J., Kourentzes, N. & Panagiotelis, A. (2024). Forecast Reconciliation: A Review. International Journal of Forecasting, 40(2), 430-456.
5. Athanasopoulos, G., Hyndman, R.J., Kourentzes, N. & Petropoulos, F. (2017). Forecasting with Temporal Hierarchies. European Journal of Operational Research, 262(1), 60-74.
6. Bailey, D.H., Borwein, J.M., Lopez de Prado, M. & Zhu, Q.J. (2014). The Probability of Backtest Overfitting. Notices of the AMS / J. Computational Finance.
7. Bailey, D.H. & Lopez de Prado, M. (2014). The Deflated Sharpe Ratio. Journal of Portfolio Management, 40(5), 94-107.
8. Barzykin, A., Bergault, P. & Gueant, O. (2024). Market Making in Spot Precious Metals. arXiv:2404.15478.
9. Batten, J.A., Lucey, B.M., McGroarty, F., Peat, M. & Urquhart, A. (2017). Stylized Facts of Intraday Precious Metals. PLOS ONE, 12(4), e0174232.
10. Beraha, M., Metelli, A.M., Papini, M., Tirinzoni, A. & Restelli, M. (2019). Feature Selection via Mutual Information: New Theoretical Insights. arXiv:1907.07384.
11. Berger, T. (2016). Forecasting Based on Decomposed Financial Return Series. Journal of Forecasting, 35(5), 419-433.
12. Bollerslev, T. & Domowitz, I. (1993). Trading Patterns and Prices in the Interbank FX Market. Journal of Finance, 48(4), 1421-1443.
13. Caminschi, A. & Heaney, R. (2014). Fixing a Leaky Fixing. Journal of Futures Markets, 34(11), 1003-1039.
14. Caporin, M., Ranaldo, A. & Velo, G.G. (2015). Precious Metals Under the Microscope. Quantitative Finance, 15(5), 743-759.
15. Cawley, G.C. & Talbot, N.L.C. (2010). On Over-fitting in Model Selection. JMLR, 11(70), 2079-2107.
16. Cespa, G., Gargano, A., Riddiough, S. & Sarno, L. (2022). Foreign Exchange Volume. Review of Financial Studies, 35(5), 2386-2427.
17. Chaboud, A., Chiquoine, B., Hjalmarsson, E. & Vega, C. (2014). Rise of the Machines. Journal of Finance, 69(5), 2045-2084.
18. Chakrabarty, B., Pascual, R. & Shkilko, A. (2015). Evaluating Trade Classification Algorithms. Journal of Financial Markets, 25, 52-79.
19. Corwin, S.A. & Schultz, P.H. (2012). A Simple Way to Estimate Bid-Ask Spreads. Journal of Finance, 67(2), 719-760.
20. Dimpfl, T. & Peter, F.J. (2013). Using Transfer Entropy to Measure Information Flows. Studies in Nonlinear Dynamics & Econometrics, 17(1), 85-102.
21. Dionisio, A., Menezes, R. & Mendes, D.A. (2004). Mutual Information: A Measure of Dependency for Nonlinear Time Series. Physica A, 344(1), 326-329.
22. Easley, D., Lopez de Prado, M. & O'Hara, M. (2016). Discerning Information from Trade Data. Journal of Financial Economics, 120(2), 269-285.
23. Evans, M.D.D. & Lyons, R.K. (2002). Order Flow and Exchange Rate Dynamics. Journal of Political Economy, 110(1), 170-180.
24. Fiedor, P. (2014). Networks in Financial Markets Based on the Mutual Information Rate. Physical Review E, 89, 052801.
25. Galati, G. (2000). Trading Volumes, Volatility and Spreads in FX Markets. BIS WP No. 93.
26. Glassman, D. (1987). Exchange Rate Risk and Transactions Costs. JIMF, 6(4), 479-490.
27. Glosten, L. & Milgrom, P. (1985). Bid, Ask and Transaction Prices. JFE, 14(1), 71-100.
28. Goodhart, C., Ito, T. & Payne, R. (1996). Microstructural Dynamics in FX. JIMF, 15(6), 829-852.
29. Gu, S., Kelly, B.T. & Xiu, D. (2020). Empirical Asset Pricing via Machine Learning. RFS, 33(5), 2223-2273.
30. Guyon, I. & Elisseeff, A. (2003). An Introduction to Variable and Feature Selection. JMLR, 3, 1157-1182.
31. Ha, J. & Hu, J. (2017). Estimating Order Imbalance Using Low Frequency Data. EFMA Conference.
32. Harrell, F.E. Jr. (2015). Regression Modeling Strategies. Springer (2nd ed.).
33. Hartmann, P. (1999). Trading Volumes and Transaction Costs. JBF, 23(5), 801-824.
34. Hauptfleisch, M., Putnins, T.J. & Lucey, B.M. (2016). Who Sets the Price of Gold? JFM, 36(12), 1127-1156.
35. Hegselmann, S. et al. (2023). TabLLM: Few-shot Classification of Tabular Data. AISTATS 2023.
36. Htun, H.H., Biehl, M. & Petkov, N. (2023). Survey of Feature Selection and Extraction for Stock Prediction. Financial Innovation, 9, 26.
37. Ibikunle, G., McGroarty, F. & ap Gwilym, O. (2018). Intraday Seasonality in Efficiency: Gold Futures. J. Commodity Markets, 11, 59-71.
38. Kourentzes, N., Petropoulos, F. & Trapero, J.R. (2014). Improving Forecasting via Multiple Temporal Aggregation. Foresight, 34, 12-17.
39. Kraskov, A., Stogbauer, H. & Grassberger, P. (2004). Estimating Mutual Information. Physical Review E, 69(6), 066138.
40. Kumar, S. & Deo, N. (2019). Mutual Information Based Stock Networks. PLOS ONE, 14(8), e0221910.
41. Lopez de Prado, M. (2018). Advances in Financial Machine Learning. Wiley (Ch. 8, 11-12).
42. Lucey, B., Larkin, C. & O'Connor, F. (2013). Gold Markets Around the World. SSRN.
43. Marney, C. (~2011). Tick Volume as Proxy for Actual Volume. Unpublished.
44. Marschinski, R. & Kantz, H. (2002). Analysing Information Flow: Improved Transfer Entropy. EPJ B, 30, 275-281.
45. Menkhoff, L., Sarno, L., Schmeling, M. & Schrimpf, A. (2016). Information Flows in FX Markets. Journal of Finance, 71(2), 601-634.
46. Moskowitz, T.J., Ooi, Y.H. & Pedersen, L.H. (2012). Time Series Momentum. JFE, 104(2), 228-250.
47. O'Connor, F.A., Lucey, B.M., Batten, J.A. & Baur, D.G. (2015). Financial Economics of Gold: A Survey. IRFA, 41, 186-205.
48. Pabuccu, H., Barber, D. & Leonardis, A. (2024). Feature Selection with Annealing. Financial Innovation, 10, 87.
49. Peng, H., Long, F. & Ding, C. (2005). Feature Selection Based on Mutual Information. IEEE TPAMI, 27(8), 1226-1238.
50. Ranaldo, A. (2009). Segmentation and Time-of-Day Patterns in FX. JBF, 33(12), 2199-2206.
51. Ranaldo, A. & Somogyi, F. (2021). Asymmetric Information Risk in FX Markets. JFE, 140(2), 391-411.
52. Rapach, D.E., Strauss, J.K. & Zhou, G. (2010). OOS Equity Premium Prediction: Combination Forecasts. RFS, 23(2), 821-862.
53. Rime, D., Sarno, L. & Sojli, E. (2010). Exchange Rate Forecasting, Order Flow and Macro Information. JIE, 80(1), 72-88.
54. Timmermann, A. (2006). Forecast Combinations. Handbook of Economic Forecasting, Vol. 1, Ch. 4.
55. Treepongkaruna, S., Brailsford, T. & Gray, S. (2014). Explaining the Bid-Ask Spread in FX. AJM, 39(4), 573-599.
56. Vergara, J.R. & Estevez, P.A. (2014). A Review of Feature Selection Methods Based on MI. NCA, 24(3-4), 175-186.
57. Wang et al. (2021). Adjusted VPIN with High-Frequency Data. IREF, 75, 210-222.
58. White, H. (2000). A Reality Check for Data Snooping. Econometrica, 68(5), 1097-1126.
59. Yang, H.-C. & Yu, C.-L. (2016). Weekday Effects on Gold. IMFI, 13(2), 8-19.
60. Zhang, B.L. et al. (2001). Multiresolution Forecasting for Futures Trading Using Wavelet Decompositions. IEEE Trans. NN, 12(4), 765-775.

---

*This search was conducted on April 11, 2026. Total search queries: ~55 across 4 parallel agents. Papers reviewed: ~90+. After quality filter: 57 unique papers documented (42 promoted, 15 rejected). Six critical gaps identified requiring direct empirical testing on GTOS data. Cross-referenced against 120 existing papers in phase1_priority_a_papers.md (69) and phase1_entry_engineering_papers_v1.md (51) to avoid duplication.*
