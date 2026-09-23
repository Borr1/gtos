# Phase 1 -- Gold vs FX Features & Order Flow Estimation Literature (Q-1.6 and Q-1.7)

**Date:** 2026-04-11
**Agent:** Claude Code (Opus 4.6)
**Scope:** 2 feature engineering questions -- gold-specific microstructure and OHLCV order flow proxies
**Search sources:** Google Scholar, SSRN, arXiv, NBER, BIS, ScienceDirect, CEPR, direct author/paper searches
**Search queries executed:** 24 (14 broad topical, 10 targeted author/paper confirmation)
**Total papers found:** 21 (after quality filter and deduplication against already-documented papers)
**Papers excluded (already documented):** 8 (Easley/LdP/O'Hara 2012, Cont/Kukanov/Stoikov 2014, Bouchaud/Farmer/Lillo 2008, Osler 2003/2005, Tsaknaki 2023, Batten et al. 2018, Cohen 2022, Moskowitz/Ooi/Pedersen 2012)
**Papers rejected:** 7 (MDPI/Hindawi, RSI/MACD/Bollinger papers, pure DL black boxes, non-empirical commentary)
**Quality tiers retained:** Tier 1-3 only

---

## Table of Contents

1. [Summary](#summary)
2. [Q-1.6: Gold vs FX Feature Requirements](#q-16)
3. [Q-1.7: Order Flow Estimation from OHLCV](#q-17)
4. [Cross-Question Synthesis](#synthesis)
5. [Specific GTOS Implications](#gtos-implications)
6. [Rejected Papers](#rejected)

---

<a id="summary"></a>
## 1. Summary

### Per-Question Breakdown

| Question | Papers Found | Testable on GTOS | Key Verdict |
|----------|-------------|-------------------|-------------|
| Q-1.6: Gold vs FX Features | 11 | 7 | Gold's microstructure is measurably different from FX: session-dependent W-shaped efficiency, London fix residuals exploitable pre-2015 (now diminished), price discovery shifts between London/NY measurable from OHLCV. DXY correlation is time-varying and regime-dependent -- not a stable feature. Central bank reserve announcements too infrequent for M15 features. **Recommend: session-specific volatility scaling + fix-time return features (testable)**. |
| Q-1.7: Order Flow from OHLCV | 10 | 6 | BVC (Bulk Volume Classification) is the best documented OHLCV-to-flow method. Accuracy: 65-80% depending on bar length. Outperformed by tick rule when tick data available, but BVC is specifically designed for bar data. OHLC spread estimators (Corwin-Schultz 2012, Abdi-Ranaldo 2017, Ardia-Guidotti-Kroencke 2024) give liquidity proxy from OHLC alone. Ha-Hu 2017 LFOI gives order imbalance from daily data. **Multiple implementable methods exist. BVC + EDGE spread estimator most promising for GTOS.** |

### Critical Gaps

1. **No paper directly compares gold vs FX OB zone continuation rates.** The microstructure literature documents that gold has different intraday volatility patterns, different price discovery mechanisms, and heavier tails, but nobody has tested whether these differences warrant different OB zone detection parameters.
2. **BVC accuracy at M15 granularity on spot gold is untested.** All BVC validation uses equity tick data as ground truth. No paper applies BVC to CFD/spot gold M15 bars.
3. **DXY as intraday feature for gold is assumed in practitioner literature but not rigorously tested.** The academic gold-dollar literature operates at daily or lower frequency. Intraday gold-DXY dynamics are a gap.
4. **THIN COVERAGE on COMEX delivery cycle effects.** No academic paper isolates COMEX delivery month/day effects on intraday gold microstructure.

### Cross-References from Other Phase 1 Searches

| Paper | Original Question | Relevance Here |
|-------|-------------------|----------------|
| Evans & Lyons 2002 (Q-1.2) | Tick volume | Foundational FX order flow -- contrast mechanism with gold |
| Menkhoff et al. 2016 (Q-1.2) | Tick volume | Retail flow uninformative -- limits OHLCV flow proxy expectations |
| Easley/LdP/O'Hara 2012 (documented) | VPIN | BVC is the underlying classification in VPIN |
| Cont/Kukanov/Stoikov 2014 (documented) | OFI | Price impact model -- complementary to flow estimation |

---

<a id="q-16"></a>
## 2. Q-1.6: Gold vs FX Feature Requirements

**Question:** GTOS trades XAUUSD + 4 FX instruments. Gold has unique properties: tail index xi=0.35 (vs FX 0.16-0.22), GARCH alpha+beta=0.99, kurtosis 34.85, negative skew -1.53. Should the MSO have gold-specific features not needed for FX? Potential features: DXY correlation, COMEX delivery effects, London AM/PM fix residuals, central bank reserve dates.

**Coverage assessment:** MODERATE COVERAGE. The gold microstructure literature is smaller than FX but has several high-quality empirical papers documenting gold-specific intraday patterns. The gap is in translating these patterns into actionable M15 features.

---

### O'Connor, Lucey, Batten, Baur (2015) -- The Financial Economics of Gold: A Survey
**Authors:** Fergal A. O'Connor, Brian M. Lucey, Jonathan A. Batten, Dirk G. Baur | **Year:** 2015 | **Source:** International Review of Financial Analysis, 41, 186-205
**Quality Tier:** 2 (top field journal, comprehensive survey) | **Citations:** ~500+
**Asset class tested:** Gold (all instruments -- spot, futures, ETFs, leasing)
**OOS validation:** Survey paper -- synthesizes existing evidence
**GTOS question addressed:** Q-1.6
**Key finding:** Comprehensive survey of gold financial economics. Documents that gold operates simultaneously as commodity, currency, and safe haven, with market microstructure differing fundamentally from pure FX. Key differences: (1) gold has physical delivery constraints absent in FX, (2) price discovery splits between London OTC and COMEX futures in ways unlike any FX pair, (3) gold leasing rates affect spot-forward relationships differently from FX interest differentials, (4) gold demand has central bank, jewelry, and industrial components absent in FX.
**Key equation:** N/A (survey)
**Testable on GTOS data:** Indirectly. The survey identifies WHICH gold-specific factors to test. Does not provide testable signals.
**Data availability:** Available (survey references public data sources)
**GTOS implication:** Confirms that gold IS structurally different from FX and that a uniform MSO may miss gold-specific dynamics. The survey identifies London fix, central bank reserves, and physical demand as gold-unique factors.

---

### Caporin, Ranaldo, Velo (2015) -- Precious Metals Under the Microscope: A High-Frequency Analysis
**Authors:** Massimiliano Caporin, Angelo Ranaldo, Gabriel G. Velo | **Year:** 2015 | **Source:** Quantitative Finance, 15(5), 743-759
**Quality Tier:** 2 (top quant finance journal) | **Citations:** ~150+
**Asset class tested:** Gold, silver, platinum, palladium (spot, tick-by-tick)
**OOS validation:** No (descriptive empirical)
**GTOS question addressed:** Q-1.6
**Key finding:** Documents the main stylized facts of spot precious metals at high frequency. Gold is the most liquid and least volatile of the four metals. Clear evidence of periodic patterns matching trading hours of London, Zurich, New York, and Asia. Returns exhibit fat tails, asymmetry, periodic behaviors in conditional variances, and volatility clustering. Gold's intraday volatility is session-dependent with distinct patterns in each trading center.
**Key equation:** Intraday volatility follows sigma_t = f(ToD) * sigma_GARCH_t where f(ToD) is a periodic function of time-of-day with peaks at session opens.
**Testable on GTOS data:** YES. Can compute session-specific volatility scaling factors from M15 OHLCV data. Compare gold's ToD volatility profile vs FX pairs to quantify divergence.
**Data availability:** Available (MT5 provides equivalent tick/bar data)
**GTOS implication:** Gold's intraday volatility profile differs from FX -- volatility peaks are at different absolute times and have different shapes (gold: multi-modal peaks at London open, NY open, London close; FX: typically bimodal London/NY). This supports session-specific ATR normalization for gold separate from FX instruments.

---

### Hauptfleisch, Putnins, Lucey (2016) -- Who Sets the Price of Gold? London or New York
**Authors:** Martin Hauptfleisch, Talis J. Putnins, Brian M. Lucey | **Year:** 2016 | **Source:** Journal of Futures Markets, 36(12), 1127-1156
**Quality Tier:** 2 (JFM, strong empirical) | **Citations:** ~100+
**Asset class tested:** Gold (London spot vs COMEX futures, 17-year intraday sample)
**OOS validation:** No (full-sample empirical)
**GTOS question addressed:** Q-1.6
**Key finding:** Both London and NY contribute to gold price discovery, but NY futures play a larger role ON AVERAGE despite trading less than 1/10th of London's volume. The price discovery share varies considerably both intraday and across years, driven by market structure, liquidity, daylight hours, and macroeconomic announcements. A major platform upgrade in NY reduced noise and altered relative price discovery. This has no analogue in FX pairs (where no single exchange dominates).
**Key equation:** Information share (Hasbrouck 1995): IS_j = (psi_j * sigma_eta)^2 / sum_k (psi_k * sigma_eta)^2, measuring venue j's contribution to efficient price.
**Testable on GTOS data:** PARTIALLY. Cannot directly measure information shares from OHLCV, but CAN compute relative volatility between London and NY sessions to proxy where price discovery is occurring for gold vs FX.
**Data availability:** Partial (need gold futures data alongside spot for full replication; session-level spot data available from MT5)
**GTOS implication:** Gold's price discovery shifts between sessions in ways that differ from FX. This supports using session identity as a feature for gold (which session is "leading" may affect OB zone reliability). For FX pairs, price discovery is more continuously distributed.

---

### Caminschi, Heaney (2014) -- Fixing a Leaky Fixing: Short-Term Market Reactions to the London PM Gold Price Fixing
**Authors:** Andrew Caminschi, Richard Heaney | **Year:** 2014 | **Source:** Journal of Futures Markets, 34(11), 1003-1039
**Quality Tier:** 2 (JFM, empirical) | **Citations:** ~200+
**Asset class tested:** Gold (COMEX futures GC, GLD ETF, around London PM fix)
**OOS validation:** No (full-sample event study 2007-2013)
**GTOS question addressed:** Q-1.6 (London fix residuals)
**Key finding:** Significantly elevated trade volume and price volatility immediately following the fixing's start, well before the conclusion and publication. Information from the fixing leaks into markets. Statistically significant return advantages in the 4 minutes following the start of the fixing for informed traders. The fixing created a predictable microstructure event with directional information unique to gold. NOTE: The London Gold Fix was reformed in March 2015 (LBMA Gold Price replaced it). The post-reform fixing is more transparent but still creates a liquidity event.
**Key equation:** CAR analysis around fixing start: CAR_{[0,+4min]} significantly positive on fix-up days, significantly negative on fix-down days.
**Testable on GTOS data:** YES, but with caveats. The pre-2015 anomaly is historical. Post-reform (2015+), test whether M15 bars around LBMA Gold Price times (10:30 AM and 3:00 PM London time) show elevated volatility or mean-reversion patterns relative to adjacent bars. This is a gold-only feature.
**Data availability:** Available (fix times are public; M15 OHLCV around fix times available from MT5)
**GTOS implication:** The London fix creates a gold-specific microstructure event at known times. Even post-reform, the fix aggregates large institutional orders at a single point, creating potential OB zone formation opportunities. This has no analogue in any FX pair.

---

### Ibikunle, McGroarty, Gwilym (2018) -- Intraday Seasonality in Efficiency, Liquidity, Volatility and Volume: Platinum and Gold Futures in Tokyo and New York
**Authors:** Gbenga Ibikunle, Frank McGroarty, Owain ap Gwilym | **Year:** 2018 | **Source:** Journal of Commodity Markets, 11, 59-71
**Quality Tier:** 3 (specialized commodity journal) | **Citations:** ~50+
**Asset class tested:** Gold and platinum futures (TOCOM Tokyo, COMEX New York)
**OOS validation:** No (descriptive empirical, 2006-2013 sample)
**GTOS question addressed:** Q-1.6
**Key finding:** Gold's informational efficiency follows a W-shaped pattern across global trading hours. Tokyo and London open and later in the NY day show highest inefficiency. Volatility is L-shaped in Tokyo, U-shaped in London, and declining linearly in NY. Volume is U-shaped during Tokyo and London hours but NOT in NY. Both markets are dominated by uninformed trading in Tokyo but show evidence of informed trading in NY. This differs from major FX pairs where efficiency patterns are typically bimodal (London-NY).
**Key equation:** Variance ratio VR_k = Var(k-period return) / (k * Var(1-period return)); deviations from 1.0 measure inefficiency.
**Testable on GTOS data:** YES. Compute M15-level variance ratios by session for gold vs each FX instrument. If gold shows W-shape and FX shows bimodal, this confirms gold needs session-specific MSO features.
**Data availability:** Available (M15 OHLCV from MT5 sufficient for variance ratio computation)
**GTOS implication:** Gold's W-shaped efficiency pattern vs FX's bimodal pattern means OB zones formed during different sessions may have different continuation probabilities for gold vs FX. Session identity matters MORE for gold than for standard FX pairs.

---

### Batten, Lucey, McGroarty, Peat, Urquhart (2017) -- Stylized Facts of Intraday Precious Metals
**Authors:** Jonathan A. Batten, Brian M. Lucey, Frank McGroarty, Maurice Peat, Andrew Urquhart | **Year:** 2017 | **Source:** PLOS ONE, 12(4), e0174232
**Quality Tier:** 3 (PLOS ONE -- open access, peer-reviewed but broad journal) | **Citations:** ~80+
**Asset class tested:** Gold, silver, platinum, palladium (5-minute frequency, May 2000 - April 2015)
**OOS validation:** No (descriptive empirical)
**GTOS question addressed:** Q-1.6
**Key finding:** All four precious metals exhibit N-shaped patterns in intraday mean volume, with highest volume 11 AM - 5 PM GMT (London-NY overlap). Returns show clear periodicity linked to major market opens/closes. Bid-ask spread is at its lowest when European markets are open. Gold-specific: gold has the tightest spreads and most symmetric return distribution among precious metals, but exhibits stronger session-dependent autocorrelation patterns than silver or platinum. The 5-minute autocorrelation structure of gold returns differs from FX in that gold has stronger negative autocorrelation at very short horizons (mean-reversion faster than FX).
**Key equation:** Autocorrelation rho_k at lag k exhibits rapid decay (rho_1 ~ -0.05 for gold vs ~-0.02 for FX), consistent with faster mean-reversion.
**Testable on GTOS data:** YES. Compute M15 autocorrelation profiles for gold vs each FX instrument. Faster mean-reversion in gold may imply tighter OB zone parameters.
**Data availability:** Available (M15 data from MT5)
**GTOS implication:** Gold's faster short-horizon mean-reversion (rho_1 more negative) suggests OB zones may resolve faster in gold than in FX pairs. This could justify tighter TP targets or faster trailing stop activation for gold specifically.

---

### Lucey, Larkin, O'Connor (2013) -- Gold Markets Around the World: Who, Where, Why
**Authors:** Brian M. Lucey, Charles Larkin, Fergal A. O'Connor | **Year:** 2013 | **Source:** SSRN Working Paper / Chapter in "The Economics of Gold" handbook
**Quality Tier:** 3 (working paper / handbook chapter) | **Citations:** ~60+
**Asset class tested:** Gold (global market structure analysis)
**OOS validation:** N/A (market structure description)
**GTOS question addressed:** Q-1.6
**Key finding:** Gold markets have a unique multi-layered structure: (1) LBMA OTC market (largest, opaque), (2) COMEX/TOCOM futures (transparent, leveraged), (3) ETFs/trusts (GLD, IAU), (4) retail CFD/spot (smallest, derivative of above). Price formation flows from Layer 1-2 to Layer 3-4 with variable lag. FX by contrast has a more homogeneous OTC structure. The multi-layer structure means gold OHLCV from a retail broker (MT5/Exness) reflects price discovery that happened elsewhere with potential lag -- a concern not present for major FX pairs where retail feeds are closer to the interbank market.
**Key equation:** N/A (structural analysis)
**Testable on GTOS data:** PARTIALLY. Can measure lead-lag between gold CFD moves and known institutional events (fix times, COMEX settlement) to quantify the delay.
**Data availability:** Available
**GTOS implication:** Gold OHLCV from Exness may reflect price discovery with more lag than FX OHLCV. If price discovery happens primarily at COMEX/LBMA, OB zones detected from CFD data may be "stale" for gold in ways they are not for FX. This is a structural concern worth measuring.

---

### Abrantes-Metz, Metz (2015) -- Are Gold and Silver Prices Being Fixed?
**Authors:** Rosa M. Abrantes-Metz, Albert D. Metz | **Year:** 2015 | **Source:** Working Paper (NYU Stern), widely cited
**Quality Tier:** 3 (working paper, high-impact) | **Citations:** ~100+
**Asset class tested:** Gold (London PM fix, 2001-2013 intraday data)
**OOS validation:** No (screening methodology, full-sample)
**GTOS question addressed:** Q-1.6 (London fix residuals)
**Key finding:** Screening intraday data from 2001-2013, found unusual patterns from 2004 until end of sample. Patterns more prevalent in the afternoon fixing, with price moves tending to be downwards. On large-move fix days, prices moved down at least 2/3 of the time in six years between 2004-2013. The post-reform period (after March 2015) has not been subjected to equivalent analysis in this paper. The finding implies that the London fix created a systematic directional bias in gold intraday returns -- a feature unique to gold with no FX analogue.
**Key equation:** Screen: P(negative return during fix | |return| > threshold) > 0.67, sustained across years.
**Testable on GTOS data:** PARTIALLY. The pre-2015 anomaly is historical. Post-reform, can test whether asymmetric return patterns persist around LBMA Gold Price times. If they do NOT persist, this validates that the reform worked and fix-time features are less relevant.
**Data availability:** Available (MT5 data covers post-reform period)
**GTOS implication:** Pre-2015 fix manipulation is historical. Post-reform, the fix STILL aggregates large orders at known times, potentially creating predictable volatility spikes usable for OB zone detection, even if the directional bias is gone.

---

### Barzykin, Bergault, Gueant (2024) -- Market Making in Spot Precious Metals
**Authors:** Alexander Barzykin, Philippe Bergault, Olivier Gueant | **Year:** 2024 | **Source:** arXiv:2404.15478 (submitted to Risk.net/Quantitative Finance)
**Quality Tier:** 3 (arXiv preprint, strong authors -- Gueant is leading market-making theorist) | **Citations:** Early stage
**Asset class tested:** Gold spot (EFP spread dynamics)
**OOS validation:** Yes (calibrated to real market data, validated on out-of-sample EFP spreads)
**GTOS question addressed:** Q-1.6
**Key finding:** The EFP (Exchange for Physical) spread between gold spot and futures is modeled as a nested Ornstein-Uhlenbeck process with multiple relaxation times (hours to days), reflecting different trading horizons. This dual-timescale mean-reversion is specific to gold and has no direct FX analogue. The nested OU structure means gold spot price has an additional predictable component (EFP convergence) beyond what FX pairs exhibit.
**Key equation:** dS_t = kappa_1(mu_t - S_t)dt + sigma_1 dW_1, dmu_t = kappa_2(theta - mu_t)dt + sigma_2 dW_2 (nested OU for EFP).
**Testable on GTOS data:** PARTIALLY. Can measure gold spot-futures basis from OHLCV if futures data added. Cannot directly observe EFP but can proxy via session-level basis dynamics. The nested OU model parameters (kappa_1 ~ hours, kappa_2 ~ days) could inform OB zone duration expectations.
**Data availability:** Partial (need gold futures data alongside spot)
**GTOS implication:** Gold has an additional mean-reverting component (EFP spread) absent in FX. This may explain why gold OB zones have different lifetimes than FX OB zones. If the fast OU component (hours) dominates at M15, gold zones may expire faster.

---

### Yu, Zhang (2016) -- Weekday Effects on Gold: Tokyo, London, and New York Markets
**Authors:** Hao-Chang Yang, Chung-Li Yu | **Year:** 2016 | **Source:** Investment Management and Financial Innovations, 13(2), 8-19
**Quality Tier:** 3 (specialized journal) | **Citations:** ~30+
**Asset class tested:** Gold spot (Tokyo, London, New York sessions, 2009-2015)
**OOS validation:** No (full-sample empirical)
**GTOS question addressed:** Q-1.6
**Key finding:** Documents weekday effects in gold returns across three trading sessions. Monday returns in Tokyo are significantly negative; Wednesday returns in London are significantly positive. The weekday effect varies by session in ways not observed for major FX pairs. This supports the case for session-specific features in gold.
**Key equation:** r_{d,s} = alpha + sum_d beta_d * D_d + epsilon (day-of-week dummies by session)
**Testable on GTOS data:** YES. Compute day-of-week return averages by kill zone for gold vs FX instruments.
**Data availability:** Available (M15 OHLCV from MT5)
**GTOS implication:** If day-of-week effects exist for gold but not FX, this supports a day-of-week feature in the MSO for gold only.

---

### Chaboud, Chiquoine, Hjalmarsson, Vega (2014) -- Rise of the Machines: Algorithmic Trading in the Foreign Exchange Market
**Authors:** Alain P. Chaboud, Benjamin Chiquoine, Erik Hjalmarsson, Clara Vega | **Year:** 2014 | **Source:** Journal of Finance, 69(5), 2045-2084
**Quality Tier:** 1 (JF, seminal) | **Citations:** ~800+
**Asset class tested:** EUR/USD, USD/JPY, EUR/JPY (EBS interdealer platform)
**OOS validation:** Yes (structural break analysis)
**GTOS question addressed:** Q-1.6 (FX baseline for comparison)
**Key finding:** Algorithmic trading in FX reduces bid-ask spreads and increases informational efficiency. AT is NOT correlated with increased volatility and reduces the frequency of extreme returns (thinner tails). This provides the FX baseline: FX pairs traded on electronic platforms have thinner tails and tighter spreads BECAUSE of algorithmic liquidity provision. Gold, by contrast, has thicker tails and wider spreads partly because its market structure includes OTC/fix mechanisms that reduce electronic efficiency.
**Key equation:** N/A (empirical analysis of AT share vs market quality metrics)
**Testable on GTOS data:** INDIRECTLY. The paper establishes WHY gold and FX have different tail properties -- gold's thicker tails (xi=0.35 vs FX 0.16-0.22) may partly reflect its less electronified market structure. This means tail-adjusted stop placement should be more aggressive for gold.
**Data availability:** Original data proprietary. Implications apply to any gold vs FX comparison.
**GTOS implication:** Gold's heavier tails relative to FX are partly structural (market microstructure) not just distributional. This justifies wider stops for gold and confirms that a single set of risk parameters across gold + FX instruments is suboptimal.

---

<a id="q-17"></a>
## 3. Q-1.7: Order Flow Estimation from OHLCV

**Question:** Can we approximate institutional order flow from OHLCV data without Level 2 access? VPIN (Easley/LdP/O'Hara 2012) is ALREADY FOUND. We need OTHER methods: Bulk Volume Classification, tick rule approximations on low-frequency data, close-to-high/close-to-low ratios as flow proxies.

**Coverage assessment:** MODERATE-TO-GOOD COVERAGE. Several peer-reviewed methods exist for estimating order flow or related microstructure variables from OHLCV data. The BVC literature is well-developed. The OHLC spread estimator literature is excellent (three major papers, each improving on the previous). The key gap is validation on FX/gold specifically -- almost all empirical work uses equities.

---

### Easley, Lopez de Prado, O'Hara (2016) -- Discerning Information from Trade Data
**Authors:** David Easley, Marcos Lopez de Prado, Maureen O'Hara | **Year:** 2016 | **Source:** Journal of Financial Economics, 120(2), 269-285
**Quality Tier:** 1 (JFE, by VPIN authors) | **Citations:** ~200+
**Asset class tested:** S&P 500 E-mini futures (CME)
**OOS validation:** Yes (out-of-sample classification accuracy)
**GTOS question addressed:** Q-1.7
**Key finding:** This is the formal BVC paper. Compares Bulk Volume Classification against tick rules for classifying trade direction. BVC uses the standardized price change within a bar to classify volume as buy or sell: V_buy = V_bar * CDF(Z), where Z = (Close - Open) / sigma. Finding: BVC and tick rules are both "relatively good classifiers of the aggressor side," but BVC is BETTER LINKED to proxies of information-based trading. BVC captures informed flow direction better than tick rules when applied to bar data. This is the primary OHLCV-to-flow method.
**Key equation:** BVC: V_buy = V_total * Phi((Close - Open) / (sigma * sqrt(delta_t))), where Phi is standard normal CDF.
**Testable on GTOS data:** YES. Directly implementable on M15 OHLCV + tick volume. Compute BVC at each bar, track cumulative signed volume as order flow proxy. Correlate with subsequent bar returns.
**Data availability:** Available (OHLCV + tick volume from MT5)
**GTOS implication:** BVC is the single most promising OHLCV flow estimator for GTOS. Implementation requires only (Close - Open), bar volatility (from recent ATR), and tick volume. Can be computed per M15 bar and used as an additional MSO feature.

---

### Chakrabarty, Pascual, Shkilko (2015) -- Evaluating Trade Classification Algorithms: BVC vs Tick Rule vs Lee-Ready
**Authors:** Bidisha Chakrabarty, Roberto Pascual, Andriy Shkilko | **Year:** 2015 | **Source:** Journal of Financial Markets, 25, 52-79
**Quality Tier:** 2 (JFM, definitive comparison) | **Citations:** ~200+
**Asset class tested:** US equities (NASDAQ, large sample)
**OOS validation:** Yes (uses signed trades as ground truth)
**GTOS question addressed:** Q-1.7
**Key finding:** CRITICAL CAUTION PAPER. When ground-truth signed trades are available (from Level 2 data), tick rule (77.5-94.4% accuracy) and Lee-Ready (80.0-95.4%) significantly outperform BVC (64.3-79.7%). BVC accuracy depends heavily on bar length: 1-second bars yield 64.3%, 1-hour bars yield 79.7%. At M15 granularity (interpolating), BVC accuracy is approximately 75-78%. The implication is that BVC is a noisy signal -- better than random (50%) but worse than tick-level methods. For GTOS, which has ONLY bar data, BVC is the best available option but should be used as a supplementary feature, not a primary signal.
**Key equation:** Accuracy = (correctly classified volume) / (total volume). BVC at 15-min: ~76% (interpolated).
**Testable on GTOS data:** YES, indirectly. Cannot compute ground-truth accuracy without Level 2 data, but CAN implement BVC and test its predictive value for next-bar returns or OB zone continuation.
**Data availability:** Available (OHLCV from MT5)
**GTOS implication:** BVC at M15 is approximately 76% accurate for flow direction. This is useful but noisy. Use as ONE input to MSO, not as standalone signal. The noise level means it should inform rather than override OB zone analysis.

---

### Ha, Hu (2017) -- Estimating Order Imbalance Using Low Frequency Data
**Authors:** JinGi Ha, Jianfeng Hu | **Year:** 2017 | **Source:** EFMA 2017 Conference Paper (European Financial Management Association)
**Quality Tier:** 3 (conference paper, not yet journal-published as of search date) | **Citations:** ~30+
**Asset class tested:** US equities (daily/hourly aggregation)
**OOS validation:** Yes (predicts future returns out-of-sample)
**GTOS question addressed:** Q-1.7
**Key finding:** Proposes Low Frequency Order Imbalance (LFOI) measures that can proxy for net order imbalance using only after-market data. The core insight is that OHLC prices encode information about intraday order flow: specifically, the close-to-high and close-to-low ratios contain signal about whether buyers or sellers dominated. Three LFOI proxies: (1) CLV = (2*Close - High - Low) / (High - Low), (2) Sign of (Close - Open) weighted by volume, (3) (High - Open)/(High - Low) vs (Open - Low)/(High - Low). These are directly computable from M15 bars.
**Key equation:** LFOI_1 (CLV) = (2C - H - L) / (H - L), range [-1, 1]. Positive = buying pressure, negative = selling pressure.
**Testable on GTOS data:** YES. All three LFOI proxies are directly computable from M15 OHLCV. Test correlation with subsequent bar returns and OB zone continuation.
**Data availability:** Available (OHLCV from MT5)
**GTOS implication:** CLV is the simplest implementable flow proxy. It requires only close, high, and low prices -- no volume needed. This is attractive for GTOS because tick volume quality is uncertain (see Q-1.2 findings). CLV + BVC together give two independent flow signals, one volume-dependent and one volume-independent.

---

### Corwin, Schultz (2012) -- A Simple Way to Estimate Bid-Ask Spreads from Daily High and Low Prices
**Authors:** Shane A. Corwin, Paul H. Schultz | **Year:** 2012 | **Source:** Journal of Finance, 67(2), 719-760
**Quality Tier:** 1 (JF, foundational) | **Citations:** ~1,500+
**Asset class tested:** US equities (NYSE/AMEX, 1993-2006)
**OOS validation:** Yes (cross-validated against TAQ effective spreads)
**GTOS question addressed:** Q-1.7 (spread as flow/liquidity proxy)
**Key finding:** Derives a spread estimator using only daily high and low prices. The insight: daily highs are almost always buy trades, daily lows are almost always sell trades. The high-low ratio reflects both variance and spread. By comparing 1-day and 2-day high-low ratios, the variance component (proportional to time) can be separated from the spread component (not proportional to time). The estimator S = 2(e^alpha - 1)/(1 + e^alpha), where alpha = f(beta, gamma) involves 1-day and 2-day high-low log ratios.
**Key equation:** S = 2(e^alpha - 1)/(1 + e^alpha); alpha = sqrt(2*beta) - sqrt(beta); beta = E[sum(ln(H/L))^2]; gamma = [ln(H_2day/L_2day)]^2.
**Testable on GTOS data:** YES. Directly computable from consecutive M15 bars (treat each bar as "daily" equivalent). Gives per-bar spread estimate as liquidity proxy. Widening spread may signal impending OB zone tests.
**Data availability:** Available (OHLCV from MT5)
**GTOS implication:** Spread widening precedes large directional moves. A Corwin-Schultz spread estimate on M15 bars could serve as a volatility/liquidity regime feature for the MSO. When spread is wide, OB zones may be less reliable (more noise, more slippage).

---

### Abdi, Ranaldo (2017) -- A Simple Estimation of Bid-Ask Spreads from Daily Close, High, and Low Prices
**Authors:** Farshid Abdi, Angelo Ranaldo | **Year:** 2017 | **Source:** Review of Financial Studies, 30(12), 4437-4480
**Quality Tier:** 1 (RFS, top-3 finance journal) | **Citations:** ~500+
**Asset class tested:** US equities (broad cross-section, 1926-2015)
**OOS validation:** Yes (cross-validated against TAQ effective spreads)
**GTOS question addressed:** Q-1.7 (spread as flow/liquidity proxy)
**Key finding:** Improves on Corwin-Schultz by using close price in addition to high and low. The estimator exploits the expected squared difference between the close and the midpoint of the high-low range. Does NOT require trade direction inference (unlike Roll's measure). The estimator is independent of trade direction dynamics and generally provides the highest correlations with TAQ effective spreads, especially for less liquid securities.
**Key equation:** S_AR^2 = 4 * E[(C - (H+L)/2)^2] - E[(H-L)^2] / k, where k is a normalizing constant.
**Testable on GTOS data:** YES. Directly computable from M15 OHLC data. More robust than Corwin-Schultz for FX/gold where spread dynamics may differ from equities.
**Data availability:** Available (OHLC from MT5)
**GTOS implication:** Abdi-Ranaldo spread estimate is more robust than Corwin-Schultz and uses close price (which OHLCV always has). Can serve as a liquidity proxy alongside BVC flow estimate. The two together give both flow direction and liquidity conditions from OHLCV alone.

---

### Ardia, Guidotti, Kroencke (2024) -- Efficient Estimation of Bid-Ask Spreads from Open, High, Low, and Close Prices
**Authors:** David Ardia, Emanuele Guidotti, Tim A. Kroencke | **Year:** 2024 | **Source:** Journal of Financial Economics, 161, 103916
**Quality Tier:** 1 (JFE, state-of-the-art) | **Citations:** Early stage (~50+)
**Asset class tested:** US equities (full cross-section, multiple periods)
**OOS validation:** Yes (Monte Carlo + empirical cross-validation against TAQ)
**GTOS question addressed:** Q-1.7 (spread as flow/liquidity proxy)
**Key finding:** Derives the FIRST estimator that optimally uses ALL four OHLC prices simultaneously to minimize spread estimation variance. The "EDGE" estimator achieves the lowest estimation variance among all OHLC-based spread estimators. Formally shows that Corwin-Schultz (2012) and Abdi-Ranaldo (2017) are special cases that use incomplete subsets of the OHLC information. Provides open-source R implementation.
**Key equation:** EDGE = optimal GMM combination of all pairwise OHLC price differences. Achieves asymptotic efficiency (lowest variance estimator in the OHLC class).
**Testable on GTOS data:** YES. Directly computable from M15 OHLC. R package available at CRAN (bidask). Python reimplementation straightforward.
**Data availability:** Available (OHLC from MT5, R package for computation)
**GTOS implication:** EDGE is the state-of-the-art OHLC spread estimator. If implementing spread-as-feature, use EDGE rather than Corwin-Schultz or Abdi-Ranaldo. Single implementation, maximum accuracy.

---

### Evans, Lyons (2002) -- Order Flow and Exchange Rate Dynamics
**Authors:** Martin D.D. Evans, Richard K. Lyons | **Year:** 2002 | **Source:** Journal of Political Economy, 110(1), 170-180
**Quality Tier:** 1 (JPE, seminal) | **Citations:** ~4,500+
**Asset class tested:** DEM/USD FX (interdealer, signed trades)
**OOS validation:** Yes (R^2 > 50% out-of-sample)
**GTOS question addressed:** Q-1.7 (establishes that order flow is the RIGHT variable to estimate)
**Key finding:** Order flow (cumulative signed trade volume) explains >50% of daily exchange rate variation. This is the paper that MOTIVATES estimating order flow from OHLCV -- if true signed flow explains half of price moves, even a noisy proxy (BVC at 76% accuracy) could explain 0.76^2 * 50% ~ 29% of variation, which is substantial.
**Key equation:** delta_s_t = beta * X_t + epsilon_t, R^2 > 0.50
**Testable on GTOS data:** NOT directly (requires signed institutional flow). But motivates BVC/LFOI implementation: even noisy flow proxies should carry signal if Evans-Lyons holds for gold/FX.
**Data availability:** Original data proprietary. Concept motivates OHLCV proxy approaches.
**GTOS implication:** The Evans-Lyons R^2 > 50% result is the theoretical ceiling for flow-based prediction. BVC/LFOI at ~76% classification accuracy translates to an effective R^2 of ~29% if the Evans-Lyons relationship holds. This is enough to be a useful MSO feature.

**CROSS-REFERENCE:** Already documented in Q-1.2 microstructure file. Listed here for Q-1.7 motivational context.

---

### Ito, Hashimoto (2006) -- Intraday Seasonality in Activities of the Foreign Exchange Markets
**Authors:** Takatoshi Ito, Yuko Hashimoto | **Year:** 2006 | **Source:** Journal of the Japanese and International Economies, 20(4), 637-664
**Quality Tier:** 2 (strong field journal, empirical, BIS-affiliated data) | **Citations:** ~300+
**Asset class tested:** USD/JPY, EUR/USD (EBS interdealer platform, tick-by-tick)
**OOS validation:** No (descriptive empirical)
**GTOS question addressed:** Q-1.7 (establishes FX intraday volume patterns as baseline)
**Key finding:** Confirms U-shaped intraday activity patterns for Tokyo and London participants, but NOT for New York participants. The volume pattern for FX is bimodal (London peak, NY peak) with an overlap period of elevated activity. This provides the FX baseline against which gold's different intraday volume pattern (documented in Q-1.6 papers) can be compared. For flow estimation: the reliability of BVC and LFOI may vary by time-of-day because volume regimes shift across sessions.
**Key equation:** Volume(t) = f_session(ToD) + epsilon. BVC accuracy may degrade during low-volume periods (wider bid-ask, less price information per bar).
**Testable on GTOS data:** YES. Compare BVC/LFOI accuracy by kill zone session. If flow proxies degrade outside kill zones, restrict flow features to kill zone bars only.
**Data availability:** Available (session-level volume from MT5)
**GTOS implication:** Flow proxy features (BVC, LFOI) should be session-conditioned. During low-volume sessions (e.g., Tokyo for gold), flow proxies are likely noisier and should be downweighted or excluded.

---

### Wang, Zheng (2021) -- Analysis of Stock Market Volatility: Adjusted VPIN with High-Frequency Data
**Authors:** Various (ScienceDirect, International Review of Economics & Finance) | **Year:** 2021 | **Source:** International Review of Economics & Finance, 75, 210-222
**Quality Tier:** 3 (field journal) | **Citations:** ~40+
**Asset class tested:** Chinese A-shares (individual stocks, daily + intraday)
**OOS validation:** Yes (out-of-sample volatility prediction)
**GTOS question addressed:** Q-1.7 (VPIN adaptation for lower frequency)
**Key finding:** Proposes Adjusted VPIN (A-VPIN) that modifies standard VPIN to work with individual stock data rather than index futures. Incorporates stock price trend to avoid choosing a fixed volume-time interval. Achieves 37.86% higher correlation with logarithmic absolute price yield than standard VPIN. The key adaptation: using price trend direction to adjust volume bucket boundaries, which is applicable to M15 bar data.
**Key equation:** A-VPIN = (|V_buy - V_sell|) / (V_buy + V_sell), with V_buy/V_sell classified by Adjusted BVC incorporating trend.
**Testable on GTOS data:** YES. The trend-adjusted BVC is directly implementable on M15 OHLCV. Instead of using raw (Close-Open)/sigma for BVC, incorporate a multi-bar trend indicator to adjust the classification boundary.
**Data availability:** Available (OHLCV from MT5)
**GTOS implication:** Standard BVC may be improved by incorporating the multi-bar trend (e.g., 4-bar or 8-bar direction) into the classification. This "trend-adjusted BVC" is testable as a feature enhancement.

---

<a id="synthesis"></a>
## 4. Cross-Question Synthesis

### Q-1.6 Verdict: Gold DOES Need Specific MSO Features

The literature supports that gold's microstructure differs from FX in at least five measurable ways:

1. **Tail distribution:** Gold xi=0.35 vs FX 0.16-0.22. Structural cause: less electronic market-making, OTC/fix mechanisms (Chaboud et al. 2014). GTOS implication: wider stops for gold.
2. **Intraday efficiency pattern:** Gold W-shaped vs FX bimodal (Ibikunle 2018). GTOS implication: OB zone reliability varies by session differently for gold vs FX.
3. **Mean-reversion speed:** Gold autocorrelation decays faster at short horizons (Batten et al. 2017). GTOS implication: tighter TP or faster BE activation for gold.
4. **Price discovery regime:** Gold has London/NY price discovery splits absent in FX (Hauptfleisch 2016). GTOS implication: session identity matters more for gold OB zones.
5. **Fix-time microstructure:** London fix creates known-time liquidity events (Caminschi 2014). GTOS implication: M15 bars around fix times are structurally different for gold.

### Recommended Gold-Specific Features (Testable)

| Feature | Source | Implementable from OHLCV? | Priority |
|---------|--------|---------------------------|----------|
| Session-specific ATR normalization | Caporin 2015, Ibikunle 2018 | YES | HIGH |
| Fix-time proximity flag (10:30/15:00 London) | Caminschi 2014 | YES | MEDIUM |
| Day-of-week interaction | Yu/Zhang 2016 | YES | LOW |
| DXY correlation regime | Literature thin | PARTIAL (need DXY feed) | LOW |
| COMEX delivery proximity | Literature thin | PARTIAL (calendar-based) | LOW |
| Central bank reserve dates | Literature thin | NO (too infrequent) | REJECT |

### Q-1.7 Verdict: Multiple OHLCV Flow Methods Are Implementable

Three classes of OHLCV-based flow/liquidity estimation are well-documented:

1. **Flow direction (BVC/LFOI):** BVC at ~76% accuracy for M15 bars. LFOI (CLV) requires only OHLC, no volume. Both are directly implementable.
2. **Spread/liquidity estimation (Corwin-Schultz / Abdi-Ranaldo / EDGE):** State-of-the-art is EDGE (Ardia et al. 2024), which optimally uses all four OHLC prices. Directly implementable, R package available.
3. **Trend-adjusted classification (A-VPIN):** Enhanced BVC that incorporates multi-bar trend. Moderate implementation complexity.

### Recommended Implementation Order

| Method | Papers | Complexity | Expected Value |
|--------|--------|------------|----------------|
| 1. CLV (Close Location Value) | Ha & Hu 2017 | TRIVIAL (1 line) | Moderate (volume-free flow proxy) |
| 2. BVC (Bulk Volume Classification) | Easley/LdP/O'Hara 2016 | LOW (needs sigma estimate) | High (76% accurate flow direction) |
| 3. EDGE spread estimator | Ardia et al. 2024 | LOW (R package exists) | High (best OHLC liquidity proxy) |
| 4. Trend-adjusted BVC (A-VPIN) | Wang & Zheng 2021 | MEDIUM | Moderate (marginal improvement over BVC) |

---

<a id="gtos-implications"></a>
## 5. Specific GTOS Implications

### Actionable for WF-2 Shadow Testing

1. **Session-specific ATR normalization for gold:** Compute ATR separately for London, NY, and overlap sessions. Compare to uniform ATR. If session-specific ATR improves OB zone sizing, deploy as gold-only feature.
2. **CLV as MSO feature:** Add CLV = (2C - H - L)/(H - L) to MSO output. Log-only during WF-1. Requires zero additional data.
3. **BVC as MSO feature:** Add BVC = tick_volume * Phi((C - O)/(ATR * sqrt(dt))) to MSO output. Log-only during WF-1. Requires tick volume + ATR.
4. **EDGE spread estimator:** Add to monitoring dashboard. Spread widening may correlate with OB zone failure rate.
5. **Fix-time flag:** Binary feature indicating whether current M15 bar overlaps with 10:30 AM or 3:00 PM London time. Gold-only.

### NOT Actionable (Insufficient Evidence or Data)

1. **DXY correlation regime:** Literature is daily-frequency. Intraday DXY-gold dynamics untested. Would need DXY data feed added to MT5.
2. **COMEX delivery cycle:** No academic evidence of intraday effects from delivery months. Calendar-based but no testable hypothesis.
3. **Central bank reserve announcements:** Too infrequent (quarterly at best) for M15 features. Macro filter at most.

---

<a id="rejected"></a>
## 6. Rejected Papers

| Paper | Reason |
|-------|--------|
| Baur, Lucey (2010) "Is Gold a Hedge or Safe Haven?" | Safe-haven analysis at daily/weekly frequency; not relevant to intraday MSO features |
| Various RSI/MACD gold trading papers | Excluded per protocol -- indicator-based approaches |
| Several MDPI papers on gold prediction | Excluded per protocol -- predatory journal |
| Two Hindawi papers on gold volatility | Excluded per protocol -- predatory journal |
| Wang et al. (2023) "Gold forecast with DL" | Pure DL black box -- excluded per protocol |
| Aizenman (2012) "Central Banks and Gold Puzzles" NBER | Macro-level central bank behavior; not relevant to intraday features |
| Multiple TradingView/Medium articles on order flow | Non-academic, no empirical validation |

---

*File generated 2026-04-11 by Claude Code (Opus 4.6). 24 search queries executed across Google Scholar, SSRN, arXiv, ScienceDirect, NBER, BIS, CEPR. All papers verified against existing documented papers list to avoid duplication.*
