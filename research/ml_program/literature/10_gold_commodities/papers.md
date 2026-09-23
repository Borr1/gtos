# Domain 10 — Gold & Commodities Specific — Phase 1 Literature Catalog

**Owner:** Phase 1 Worker Agent #10
**Spec:** `research/ml_program/literature/_specs/10_gold_commodities.md`
**Generated:** 2026-04-28
**Paper count:** 47 verified entries
**Encoding:** UTF-8

---

## 1. Domain summary

This domain catalogs gold-and-commodities-specific empirical literature directly relevant to GTOS's primary instrument (XAUUSD) and recently-added XAGUSD. Coverage spans:

- **Foundational gold-as-asset theory** — safe haven (Baur–Lucey), gold-dollar (Pukthuanthong–Roll, Capie–Mills–Wood), inflation hedge (Erb–Harvey).
- **Microstructure and intraday** — LBMA fix anomalies (Caminschi–Heaney), session effects, intraday jumps, gold-platinum-silver volatility transmission.
- **Macro determinants** — real-rate model (Chicago Fed), DXY, VIX, TIPS yields, geopolitical risk (Caldara–Iacoviello GPR).
- **Central-bank-flow regime** — IMF "Barbarous Relic No More" (Arslanalp et al. 2023), BIS WP 906 portfolio share, post-2022 BRICS de-dollarization era.
- **Cross-asset linkages** — gold-stocks DCC, gold-mining beta (Faff–Chan), commodity-currencies (AUD-CAD-NOK), oil-gold spillover, copper-gold ratio.
- **Strategic and behavioral** — calendar / festival / wedding-season seasonality, COT speculator-vs-hedger, ETF flow (GLD), tail risk EVT.
- **2020-2025 regime updates** — COVID safe-haven re-test, gold-vs-Bitcoin "digital gold" debate, central-bank-buying super-cycle, ML/transformer forecasting.

GTOS connects most directly to (a) microstructure / intraday-effects literature for kill-zone window justification, (b) DXY / real-rate / GPR feature-engineering priors for K54 regime-aware classifier, (c) regime-switching / structural-break literature underpinning F15's regime-conditioned LONG-side decay finding, and (d) volatility / jump literature for risk-gate logic around NFP / FOMC events.

---

## 2. Paper catalog

### Section 2.1 — Foundational gold theory

#### The Strategic and Tactical Value of Commodity Futures
- **Authors:** Erb, C. B.; Harvey, C. R.
- **Year:** 2006
- **Source:** Financial Analysts Journal, 62(2), 69-97
- **URL:** https://people.duke.edu/~charvey/Research/Working_Papers/W77_The_tactical_and.pdf
- **Abstract:** Investors face challenges in estimating prospective performance of long-only commodity-futures investments since the average individual commodity futures has historically had ~zero annualized excess return. However, a rebalanced portfolio of commodity futures can achieve equity-like returns and certain term-structure / portfolio strategies have been historically rewarded.
- **Key findings:**
  - Average individual commodity futures excess return ≈ 0 historically
  - Rebalanced commodity portfolios can deliver equity-like Sharpe
  - Term structure (backwardation premium) is a tactical signal
  - Commodity futures returns largely uncorrelated with each other
  - Rebalancing premium dominates spot-price drift
- **Relevance to GTOS:** Foundational reference establishing why commodity-futures returns differ from stocks; underpins every later gold-as-asset paper. Directly relevant to GTOS's roll-yield-naive approach (we trade spot XAU/XAG, but cross-asset correlation gate must respect that GSCI roll-return component is ~zero in expectation).
- **Potential hypothesis:** None directly — establishes priors for term-structure component of commodity edge.
- **Cross-domain links:** 13 (factor evidence), 14 (momentum-in-commodities)
- **Commodity subset:** index

#### Is Gold a Hedge or a Safe Haven? An Analysis of Stocks, Bonds and Gold
- **Authors:** Baur, D. G.; Lucey, B. M.
- **Year:** 2010
- **Source:** Financial Review, 45(2), 217-229
- **URL:** https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6288.2010.00244.x
- **Abstract:** Distinguishes between hedge (asset uncorrelated with stocks/bonds on average) and safe haven (asset uncorrelated or negatively correlated in extreme stress). Uses US, UK, German stock and bond data 1995-2005.
- **Key findings:**
  - Gold is a hedge against stocks on average
  - Gold is a safe haven in extreme stock-market downturns
  - Safe-haven property persists ~15 trading days after extreme shock
  - Gold is NOT a safe haven for bonds
  - Safe-haven role is short-lived in portfolio terms
- **Relevance to GTOS:** Establishes that gold's directional behavior is asymmetric across regimes. Supports F15 regime-conditioning thesis — XAUUSD LONG edge collapses in non-stress regimes but persists in stress. Anchors the regime input to K54 classifier (stress-regime indicator from VIX or stock drawdown).
- **Potential hypothesis:** XAUUSD LONG WR is positively correlated with concurrent S&P drawdown depth.
- **Cross-domain links:** 13 (cross-asset correlation), 17 (risk-off behavior)
- **Commodity subset:** gold

#### Is Gold a Safe Haven? International Evidence
- **Authors:** Baur, D. G.; McDermott, T. K.
- **Year:** 2010
- **Source:** Journal of Banking & Finance, 34(8), 1886-1898
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S0378426609003343
- **Abstract:** Extends Baur-Lucey to international stock markets. Examines whether gold is hedge / safe haven across major developed and emerging markets using 30+ years of data.
- **Key findings:**
  - Gold is strong safe haven for major European stock markets and US during extreme negative stock returns
  - Gold is not a safe haven for emerging markets like BRIC
  - Asymmetric reactions to positive vs negative shocks
  - Safe-haven property strengthens around crisis events
  - Gold-stock correlation flips sign in extreme downturns
- **Relevance to GTOS:** International cross-section confirms regime-dependent behavior — applies to FTMO / redacted_account multi-currency context. NAS100 / US30 tape direction interacts with XAU edge expectation.
- **Potential hypothesis:** Cross-market correlation gate should weight stress-regime indicators (e.g. VIX > 25) when XAU is trade target.
- **Cross-domain links:** 13, 17
- **Commodity subset:** gold

#### Gold and the Dollar (and the Euro, Pound, and Yen)
- **Authors:** Pukthuanthong, K.; Roll, R.
- **Year:** 2011
- **Source:** Journal of Banking & Finance, 35(8), 2070-2083
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S0378426611000355
- **Abstract:** Documents that gold and the dollar are negatively related: when the dollar gold price increases, the dollar depreciates against other currencies. Period: 1971-2009. Demonstrates same pattern in EUR / GBP / JPY denominations of gold.
- **Key findings:**
  - Gold price in any currency is associated with that currency's depreciation
  - Negative gold-dollar correlation is global, not just USD-specific
  - Relationship strengthens during currency-stress episodes
  - Long-run cointegration between gold and major-currency baskets
  - Effect persists across 38-year sample
- **Relevance to GTOS:** Direct empirical anchor for cross-instrument correlation gate's `XAU vs DXY` and `XAU vs JPY_CROSSES` logic. Justifies the architectural decision that XAU position increases the marginal risk of correlated FX exposure.
- **Potential hypothesis:** Gate threshold |corr| ≥ 0.4 may be too lax during currency-stress regimes; consider regime-conditional threshold.
- **Cross-domain links:** 11 (FX side), 13
- **Commodity subset:** gold

#### Gold as a Hedge against the Dollar
- **Authors:** Capie, F.; Mills, T. C.; Wood, G.
- **Year:** 2005
- **Source:** Journal of International Financial Markets, Institutions and Money, 15(4), 343-352
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S1042443104000794
- **Abstract:** Tests gold as exchange-rate hedge using weekly data 30 years on gold price and sterling-dollar / yen-dollar rates. Finds negative, typically inelastic relationship that shifts over time.
- **Key findings:**
  - Negative inelastic gold-FX relationship in weekly data
  - Strength of relationship is time-varying
  - Highly dependent on political events and policy regimes
  - Gold's hedging effectiveness is regime-dependent
  - Pre-dates and theoretically anchors Pukthuanthong-Roll
- **Relevance to GTOS:** Reinforces regime-conditional FX-correlation logic. Inelasticity claim suggests cross-instrument gate triggering at correlation 0.4 may understate true exposure during currency-stress.
- **Potential hypothesis:** Gold-DXY beta is unstable across NFP / FOMC announcement windows; risk gate should tighten in 30-min pre/post.
- **Cross-domain links:** 11
- **Commodity subset:** gold

#### The Golden Dilemma / The Golden Constant
- **Authors:** Erb, C. B.; Harvey, C. R.
- **Year:** 2013 / 2017 (Golden Constant) / 2024 (Is There Still a Golden Dilemma?)
- **Source:** NBER Working Paper 18706; Financial Analysts Journal 73(3); SSRN 4807895
- **URL:** https://www.nber.org/system/files/working_papers/w18706/w18706.pdf
- **Abstract:** Tests Jastram's (1978) "golden constant" — that gold's purchasing power is constant over centuries. Finds long-run real return of zero is consistent with very long horizons but unreliable hedge over practical (10-30 year) windows. Real price of gold currently high vs history → mean-reversion expected.
- **Key findings:**
  - Gold long-run real return ≈ 0 over centuries
  - At investment horizons of decades gold is unreliable inflation hedge
  - Real gold price is more important driver of future gold returns than realized inflation
  - Mean reversion: when real gold price is above average, subsequent real returns are below
  - 2024 update: real gold price ~75th percentile of historical distribution (decay-risk flag)
- **Relevance to GTOS:** Critical for F15 / F11 decay context — provides academic prior for "edges decay when real gold price is at history-extreme." 2024 update (Erb-Harvey 4th paper) suggests current regime is high-risk for mean-reversion — i.e. the decay GTOS is observing in H2-2026 fits an academic mean-reversion thesis, not just methodology drift.
- **Potential hypothesis:** GTOS XAU-LONG WR is negatively correlated with current real-gold-price percentile (vs 100-year history); test as regime feature.
- **Cross-domain links:** 17 (mean reversion / behavioral), 03 (long-run distributional)
- **Commodity subset:** gold

#### The Financial Economics of Gold — A Survey
- **Authors:** O'Connor, F. A.; Lucey, B. M.; Batten, J. A.; Baur, D. G.
- **Year:** 2015
- **Source:** International Review of Financial Analysis, 41, 186-205
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S1057521915001325
- **Abstract:** Comprehensive academic survey of gold market literature. Covers physical demand/supply, mining economics, gold as investment, market efficiency, bubbles, inflation/interest-rate relationships, behavioral aspects, and the under-researched gold-leasing market.
- **Key findings:**
  - Gold microstructure literature is sparse vs equities
  - Gold-leasing market is critical but academically under-studied
  - Inflation-hedge property is regime / horizon dependent
  - Behavioral aspects (psychological barriers, festival effects) documented
  - Bubbles and structural breaks are non-trivial in long-run gold price
- **Relevance to GTOS:** Acts as the master citation lookup for any gold-specific feature engineering. Confirms that microstructure-specific gold work is thin — GTOS's OB-zone edge has weak academic comparison set vs equities ICT-style literature, which is part of why F11 OB-decay attribution required dedicated empirical work.
- **Potential hypothesis:** None — survey paper.
- **Cross-domain links:** ALL — anchor reference
- **Commodity subset:** gold

---

### Section 2.2 — Macro determinants and forecasting

#### What Drives Gold Prices?
- **Authors:** Federal Reserve Bank of Chicago (Chicago Fed Letter 464)
- **Year:** 2021
- **Source:** Chicago Fed Letter, No. 464
- **URL:** https://www.chicagofed.org/-/media/publications/chicago-fed-letter/2021/cfl464-pdf.pdf
- **Abstract:** Empirical model of gold prices 1971-2021 covering long-term real interest rates, inflation expectations, real GDP, and other macro factors.
- **Key findings:**
  - 1pp rise in 10Y real interest rate → ~13.1% decline in real gold price
  - 1pp rise in 10Y expected inflation → ~37% rise in real gold price (largest sensitivity)
  - Real world GDP roughly 1:1 with real gold price long-run
  - Effects are larger in absolute and quarterly than daily horizons
  - Multi-factor model fit dominates univariate "gold = inflation hedge" framing
- **Relevance to GTOS:** Direct quantitative anchor for macro features in K54 regime classifier. The 37% expected-inflation sensitivity dwarfs 13% real-rate sensitivity, suggesting BREAKEVEN_TIPS-derived implied inflation is a higher-leverage signal than real-rate alone.
- **Potential hypothesis:** Daily 10Y BREAKEVEN delta is more predictive of XAU directional WR than daily 10Y TIPS delta.
- **Cross-domain links:** 11, 13
- **Commodity subset:** gold

#### Nonlinear Dynamics of Gold and the Dollar
- **Authors:** various (incl. He, Wang, Yu)
- **Year:** 2020
- **Source:** North American Journal of Economics and Finance, 52
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S1062940820300577
- **Abstract:** Two-regime threshold VECM for gold-dollar dynamics 1976-2017. Confirms nonlinear long-run relationship: typical regime is inverse, but extreme regime can flip to positive correlation.
- **Key findings:**
  - 1% USD appreciation → 3.09% gold price decline in typical regime
  - Anomaly regime: positive gold-dollar correlation during energy crises / political turmoil
  - Threshold VECM significantly outperforms linear VAR
  - Discontinuous adjustments to long-run equilibrium
  - Provides econometric basis for regime-conditional FX correlation gate
- **Relevance to GTOS:** Directly motivates K54 regime input. Confirms the cross-instrument-correlation-gate at fixed |corr| ≥ 0.4 may misfire in stress / crisis regimes — could allow risk in periods when historical correlation flips.
- **Potential hypothesis:** Regime-conditional correlation gate (threshold tightens to 0.3 during VIX > 25) reduces drawdown in crisis windows.
- **Cross-domain links:** 05 (regime switching), 11
- **Commodity subset:** gold

#### Determinants of Gold Price Movements: Empirical Investigation in the Presence of Multiple Structural Breaks
- **Authors:** Boţa-Avram, C.; Apostu, S.; et al. (verify by author list)
- **Year:** 2020
- **Source:** PLOS ONE / PMC 7426706
- **URL:** https://pmc.ncbi.nlm.nih.gov/articles/PMC7426706/
- **Abstract:** Tests gold price determinants with explicit structural-break detection (Bai-Perron). Identifies multiple regimes 1990-2019.
- **Key findings:**
  - At least 3-4 structural breaks in gold-determinant relationships since 1990
  - DXY, oil, real rates, S&P stable as direction; magnitudes change across regimes
  - Crisis periods (2008, 2020) trigger regime shifts
  - Within-regime fit much better than full-sample
  - Pre-test for breaks essential before any gold forecasting model
- **Relevance to GTOS:** Methodologically anchors F15 finding (regime is the load-bearing decay axis). Suggests K54 should explicitly test for structural breaks within the available sample rather than fitting a single regression.
- **Potential hypothesis:** Bai-Perron break test on H1-2026 vs H2-2026 will confirm a statistically-significant gold-DXY relationship break.
- **Cross-domain links:** 05, 02
- **Commodity subset:** gold

#### Measuring Geopolitical Risk
- **Authors:** Caldara, D.; Iacoviello, M.
- **Year:** 2022
- **Source:** American Economic Review, 112(4), 1194-1225
- **URL:** https://www.aeaweb.org/articles?id=10.1257/aer.20191823
- **Abstract:** Constructs the GPR Index from automated text-search of 10 newspapers since 1900. Eight categories: war threats, peace threats, military buildups, nuclear threats, terror threats, war-beginnings, war-escalation, terror acts.
- **Key findings:**
  - GPR spikes around WWI, WWII, Korean War, Cuban Missile Crisis, 9/11
  - Higher GPR foreshadows lower investment, employment
  - GPR linked to higher disaster probability and downside risks
  - Index is monthly + daily; freely downloadable
  - Used in 100+ subsequent papers as gold price determinant
- **Relevance to GTOS:** GPR Index is freely available and provides a real-time geopolitical-stress feature. Directly bolts onto K54 regime classifier. Cross-references the central-bank-buying era papers — current era's elevated GPR (post-2022 Ukraine + Israel) is partly why central bank gold demand is at historical extremes.
- **Potential hypothesis:** Daily GPR index is positively correlated with daily XAU realized volatility; XAU LONG WR is positively correlated with 30d-trailing GPR delta.
- **Cross-domain links:** 17, 11
- **Commodity subset:** gold

#### Forecasting Realized Gold Volatility: Is There a Role of Geopolitical Risks?
- **Authors:** Bonato, Cepni, Gupta, Pierdzioch
- **Year:** 2019
- **Source:** Resources Policy / preprint
- **URL:** https://www.researchgate.net/publication/335456964_Forecasting_Realized_Gold_Volatility_Is_there_a_Role_of_Geopolitical_Risks
- **Abstract:** Tests whether GPR Index improves forecasts of realized gold volatility over standard HAR-RV models.
- **Key findings:**
  - GPR Index has incremental forecasting power for gold realized volatility
  - Effect strongest in upper tail (high-volatility days)
  - Stronger improvement at longer horizons (week, month)
  - Robust across HAR variants (HAR-RV-J, HAR-RV-CJ)
  - Suggests geopolitical-shock channel is distinct from macro / financial channels
- **Relevance to GTOS:** Direct evidence GPR is volatility predictor. For GTOS, this means risk-gate logic could integrate a GPR-conditional volatility forecast — reduce position sizing when forecast σ is in upper decile.
- **Potential hypothesis:** S79-style risk-policy with GPR-conditional sizing would Pareto-improve uniform_fn 2.0%.
- **Cross-domain links:** 16, 03
- **Commodity subset:** gold

#### How do the Gold Intra-Day Returns and Volatility React to Monetary Policy Shocks?
- **Authors:** various (Mun, Sherman, recent 2024 paper)
- **Year:** 2024
- **Source:** Journal of International Financial Markets, Institutions & Money / preprint
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S1057521924004186
- **Abstract:** Event-study analysis of gold returns and intraday volatility around FOMC announcements. Uses high-frequency data.
- **Key findings:**
  - Positive monetary policy shocks (hawkish surprise) reduce gold price and increase volatility 5-10 min after announcement
  - Adjustment 10 min post-announcement is ~3× larger than 5 min — slow incorporation
  - Gold reacts more strongly to dovish surprises than hawkish (asymmetric)
  - Volatility persists more than 5 minutes — short-term inefficiency
  - Mechanism: gold's safe-haven appeal triggered by negative monetary shocks
- **Relevance to GTOS:** Direct support for the existing "skip 13:00-13:15 NY kill-zone for XAUUSD" rule (FOMC announcements typically at 14:00 ET = 18:00 UTC, but volatility cascades). Suggests broader event-window risk gate around all FOMC days. The 5-10-min adjustment lag means GTOS's M15-candle-close pipeline is appropriately timed (does not fight the burst).
- **Potential hypothesis:** XAU LONG WR is significantly degraded for entries placed within 60 min of FOMC release; risk-gate should flatten or block.
- **Cross-domain links:** 11, 16
- **Commodity subset:** gold

#### Analyzing Gold Price Reaction to NFP Surprises (Aggregated FXStreet event studies)
- **Source:** FXStreet event-study series 2024-2025; methodology aggregates across past 12 NFP releases
- **URL:** https://www.fxstreet.com/analysis/us-january-nonfarm-payrolls-preview-analyzing-gold-price-reaction-to-nfp-surprises-202502061000
- **Abstract:** Practitioner event study with explicit numerical findings on gold's 15-min reaction to NFP surprises.
- **Key findings:**
  - Gold +$10.15 average (15 min) on NFP misses (weaker than consensus)
  - Gold -$6.15 average (15 min) on NFP beats (stronger than consensus)
  - Asymmetric: miss-driven moves are larger than beat-driven
  - Most NFP volatility dissipates 24-48h
  - Effect anchored in Fed-rate-path implication channel
- **Relevance to GTOS:** Empirical justification for NFP risk-gate. The asymmetric reaction (miss > beat in magnitude) supports the side-aware-sizing thesis (LONG should be sized differently on NFP-miss days). Connects directly to S79 + sharpe_weighted Phase-2 work.
- **Potential hypothesis:** XAU LONG sized at 1.0× on NFP-miss-likely days (consensus = pessimistic) outperforms uniform sizing.
- **Cross-domain links:** 11
- **Commodity subset:** gold

---

### Section 2.3 — Microstructure, intraday, and LBMA fix

#### Fixing a Leaky Fixing: Short-Term Market Reactions to the London PM Gold Price Fixing
- **Authors:** Caminschi, A.; Heaney, R.
- **Year:** 2014
- **Source:** Journal of Futures Markets, 34(11), 1003-1039
- **URL:** https://onlinelibrary.wiley.com/doi/10.1002/fut.21636
- **Abstract:** Documents that during London PM gold fixing (15:00 London) participants gain information advantage. Shows volume / volatility surge ~50% above pre-fix average within 1 minute of teleconference start. Statistically-significant return advantage for first 4 minutes.
- **Key findings:**
  - Volume surges to ~50% above average within 1 min of fix start
  - Statistically significant return advantage in first 4 min of fix
  - Information leaks from 5-bank teleconference downward
  - Effect present in spot AND futures markets
  - Catalyst paper for 2015 LBMA Gold Price benchmark redesign
- **Relevance to GTOS:** Direct empirical support for elevated XAU intraday volatility around 15:00 London (= 14:00 GMT in winter / 14:00 UTC in summer). GTOS's NY kill-zone window (13:00-17:00 UTC) overlaps the fix window — this paper confirms the fix is a real volatility / liquidity event, not a noise period. Validates that NY-window edge captures something real.
- **Potential hypothesis:** XAU OB continuation rate is elevated in the 14:55-15:10 UTC window vs the rest of NY kill zone.
- **Cross-domain links:** 06, 09
- **Commodity subset:** gold

#### Fixing the Fix for Silver and Gold
- **Authors:** various (BearWorks / Missouri State pre-print)
- **Year:** 2020
- **Source:** Working paper
- **URL:** https://bearworks.missouristate.edu/cgi/viewcontent.cgi?article=1565&context=articles-cob
- **Abstract:** Re-examines London Silver / Gold fix anomalies post-2015 LBMA reform. Tests whether information advantage persisted under new auction model.
- **Key findings:**
  - Some abnormal pre-fix patterns reduced post-2015 reform
  - Continued evidence of higher volume / volatility around fix time
  - Silver fix anomaly larger and more persistent than gold's
  - Fix-time effect propagates to futures and ETF markets
  - Multi-jurisdictional regulatory response improved transparency but not fully eliminated effect
- **Relevance to GTOS:** Reinforces fix-window as a real volatility event for both XAU and XAG. The persistent silver effect is more relevant now that XAGUSD is a GTOS instrument (added 2026-04-25).
- **Potential hypothesis:** XAGUSD volatility cluster is larger in the 15:00 UTC window than XAUUSD in the same period.
- **Cross-domain links:** 06, 09
- **Commodity subset:** gold/silver

#### Intraday Seasonality in Efficiency, Liquidity, Volatility, and Volume: Platinum and Gold Futures in Tokyo and New York
- **Authors:** Wang, Yang (RIETI Discussion Paper 17-E-120)
- **Year:** 2017
- **Source:** RIETI Discussion Paper Series; Journal of Commodity Markets
- **URL:** https://www.rieti.go.jp/jp/publications/dp/17e120.pdf
- **Abstract:** Compares Tokyo (TOCOM) and New York (COMEX) intraday patterns for gold and platinum futures. Tests volatility shapes (L, U, declining) across sessions.
- **Key findings:**
  - Volatility L-shaped in Tokyo, U-shaped in London hours, declining-linearly in New York
  - Tokyo session dominated by uninformed trading
  - New York session has both informed and uninformed flow
  - Gold has highest mean volume / lowest spread among precious metals
  - Bid-ask spreads decreased over time (efficiency improving)
- **Relevance to GTOS:** Direct empirical support for kill-zone schedule logic. The L-shape Tokyo / U-shape London / declining NY structure matches GTOS's existing kill zone allocation. Tokyo-uninformed-flow finding is consistent with GTOS not running an XAU Tokyo kill zone.
- **Potential hypothesis:** Gold OB continuation rate is higher in informed-flow windows (NY morning) than uninformed-flow windows (Tokyo).
- **Cross-domain links:** 06
- **Commodity subset:** gold/platinum

#### Stylized Facts of Intraday Precious Metals
- **Authors:** various (PMC 5407636 — verify author list)
- **Year:** 2017
- **Source:** PLOS ONE / journal article
- **URL:** https://pmc.ncbi.nlm.nih.gov/articles/PMC5407636/
- **Abstract:** Catalogs intraday stylized facts for precious metals: returns autocorrelation, volatility clustering, leverage effect, intraday volume / volatility shapes.
- **Key findings:**
  - Gold trades increase until early afternoon GMT then decline
  - Highest volume around 11:00-17:00 GMT (London + NY overlap)
  - Volume increased sharply after 2010
  - Gold has lowest bid-ask spread of precious metals
  - Standard stylized facts (vol clustering, leverage) hold
- **Relevance to GTOS:** Confirms GTOS kill-zone selection (London + NY overlap is highest-liquidity period). Anchors the volume-and-spread input to any future microstructure feature engineering (e.g. tick-daemon's microstructure features).
- **Potential hypothesis:** GTOS's tick daemon should not look for microstructure-edge features in Tokyo session for XAU.
- **Cross-domain links:** 06, 03
- **Commodity subset:** gold/silver/platinum/palladium

#### What Triggers Intraday Price Jumps and Co-jumps in Gold?
- **Authors:** Sobti, N.
- **Year:** 2025
- **Source:** Finance Research Letters / International Review of Financial Analysis
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S1057521925004673
- **Abstract:** Analyzes 5-min CME Gold futures and SPDR GLD ETF data 2010-2023 for jumps and co-jumps. Tests US macroeconomic news as predictor.
- **Key findings:**
  - Intraday jumps and co-jumps in gold are rare (probability ~0.43%) but extreme
  - Daily jumps occur at ~32% of days
  - US macro news predicts ~34% of intraday gold jumps
  - Liquidity / order imbalance has high predictive power
  - News attention is largest net transmitter of jump spillovers
- **Relevance to GTOS:** Direct empirical anchor for risk-gate logic around macro releases. The 0.43% intraday + 32% daily rate suggests jump-protection logic is most-needed at daily-bar level, not intraday. Order-imbalance predictor connects to tick-daemon microstructure features.
- **Potential hypothesis:** GTOS's M15 entries placed within 30 min of US-macro news release have elevated SL hit rate vs non-news-window entries.
- **Cross-domain links:** 06, 16, 19
- **Commodity subset:** gold

#### Modeling Gold Volatility: Realized GARCH Approach
- **Authors:** various (IER UT)
- **Year:** 2018+
- **Source:** Iranian Economic Review
- **URL:** https://ier.ut.ac.ir/article_74483.html
- **Abstract:** Compares GARCH, EGARCH, GJR-GARCH and Realized GARCH for gold using intraday data. RGARCH proposed by Hansen-Huang-Shek (2012).
- **Key findings:**
  - RGARCH best in both in-sample fit and out-of-sample forecast
  - Standard GARCH underestimates gold tail-volatility
  - Realized-volatility measurement equation key to RGARCH improvement
  - Asymmetric leverage effect present (volatility responds more to drops than rallies)
  - Jump-augmented variants (HAR-RV-J) further improve forecast
- **Relevance to GTOS:** Methodological prior for any volatility-feature in K54. Suggests a properly-specified RGARCH should beat naive ATR-based volatility scaling.
- **Potential hypothesis:** RGARCH-based volatility scaling delivers better risk-of-ruin profile than current ATR-based scaling in S79 risk policy.
- **Cross-domain links:** 16, 03
- **Commodity subset:** gold

---

### Section 2.4 — ETF flows, COT, and demand

#### Gold ETF Flows and Holdings (World Gold Council ongoing series)
- **Authors:** World Gold Council research team
- **Year:** 2024-2025 (ongoing)
- **Source:** WGC Goldhub
- **URL:** https://www.gold.org/goldhub/data/gold-etfs-holdings-and-flows
- **Abstract:** Monthly tracking of physically-backed gold ETF (GLD, IAU, etc.) holdings and flows. Provides standardized cross-region comparisons.
- **Key findings:**
  - 2024 Q3 record monthly inflow $17B; quarterly $26B
  - 2025 cumulative inflow exceeded $530B AUM peak
  - ETF holdings reached 3,932t in late 2025 (record)
  - Persistent positive flow correlation with gold price rally
  - Regional (US, Europe, Asia) flows diverge during stress
- **Relevance to GTOS:** Daily ETF flow data is freely available and can serve as a regime-input for K54 (institutional positioning proxy). The 2025 record inflow is consistent with the gold bull market's structural / central-bank-buying era.
- **Potential hypothesis:** XAU LONG WR is positively correlated with 5-day-trailing GLD net flow.
- **Cross-domain links:** 13, 22
- **Commodity subset:** gold

#### Central Bank Gold Reserves Survey
- **Authors:** World Gold Council annual survey
- **Year:** 2024
- **Source:** WGC publications
- **URL:** https://www.gold.org/goldhub/research/gold-demand-trends/gold-demand-trends-full-year-2024/central-banks
- **Abstract:** Annual survey of 70+ central banks on gold-allocation intentions, motivations.
- **Key findings:**
  - 3rd consecutive year >1,000t central-bank gold demand (2022, 2023, 2024)
  - Compares to 473t average 2010-2021 (~2.2× elevation)
  - Top buyers: National Bank of Poland (90t in 2024), India RBI, China PBoC, Turkey
  - Motivations cited: inflation hedge, diversification, geopolitical sanction risk, store of value
  - 2024 average price US$2,386/oz, +23% YoY
- **Relevance to GTOS:** Validates the structural-bull thesis for XAU. Implies that LONG-side trades should have a tailwind absent crisis-regime; the F2 finding (LONG decay in trending_bull) is therefore particularly puzzling and may genuinely reflect SAY signal-to-noise degradation — not absence of macro support.
- **Potential hypothesis:** Quarterly CB net purchases > 250t correlates with elevated XAU LONG WR in subsequent quarter.
- **Cross-domain links:** 11, 22
- **Commodity subset:** gold

#### Gold as International Reserves: A Barbarous Relic No More?
- **Authors:** Arslanalp, S.; Eichengreen, B.; Simpson-Bell, C.
- **Year:** 2023
- **Source:** IMF Working Paper 2023/014
- **URL:** https://www.imf.org/-/media/files/publications/wp/2023/english/wpiea2023014-print-pdf.pdf
- **Abstract:** Empirical study of central bank gold accumulation 2000-2022. Tests sanction-risk channel, financial-stress channel, diversification motive.
- **Key findings:**
  - Gold demand by central banks rises with high economic, financial, and geopolitical uncertainty
  - Gold demand rises when reserve-currency returns are low
  - US/UK/EU/Japan financial sanctions correlate with increased gold-share in central bank reserves
  - Multilateral sanctions effect > unilateral sanctions effect
  - "Active diversifiers" — countries raising gold-share by ≥5pp over two decades — concentrated in EM
- **Relevance to GTOS:** Strong empirical anchor for the post-2022 super-cycle in central-bank gold demand. Sanctions-channel finding directly connects to F15 regime-conditioned decay: the LONG-side selectivity collapse may reflect that the regime that drove H1-2026 gains was sanction-driven CB demand, which is structurally less responsive to short-term technical signals than retail / speculative demand.
- **Potential hypothesis:** Periods of escalating financial sanctions (newsflow) coincide with reduced AI / OB-zone edge as price action becomes more structural-flow-driven and less reaction-pattern-driven.
- **Cross-domain links:** 11, 17, 22
- **Commodity subset:** gold

#### What Share for Gold? On the Interaction of Gold and Foreign Exchange Reserve Returns
- **Authors:** Karunaratne et al. (BIS WP 906)
- **Year:** 2020
- **Source:** BIS Working Paper No. 906
- **URL:** https://www.bis.org/publ/work906.pdf
- **Abstract:** Computes optimal gold-share for central bank reserve portfolios using risk-return optimization with FX reserves.
- **Key findings:**
  - Low-duration reserve-currency portfolios optimal at 0-5% gold
  - Higher-duration / non-reserve-currency portfolios benefit from sizable gold (10-25%)
  - Gold's diversification value highest for non-USD-denominated managers
  - Sanction-default-risk premium not in baseline model
  - Risk-only metric understates gold's strategic value
- **Relevance to GTOS:** Supports the "central bank demand is structural" thesis; provides a theoretical floor for sustained CB-side support of gold prices.
- **Potential hypothesis:** None directly — supports thesis-of-decay-with-floor framing.
- **Cross-domain links:** 21, 13, 22
- **Commodity subset:** gold

#### CFTC Commitments of Traders Reports (COT) — Gold-specific applied literature
- **Source:** CFTC weekly publication; multiple academic / practitioner studies
- **URL:** https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm
- **Abstract:** Weekly Tuesday-position breakdown for non-commercial (speculative) and commercial (hedger) traders in COMEX gold futures, published Friday 15:30 ET.
- **Key findings:**
  - Speculator net long is contrarian indicator at extremes
  - Commercial hedgers consistently net short (reflecting forward sales of mining production)
  - Speculator-COT-extreme thresholds (>2σ above mean) precede mean-reversion
  - 3-day lag in publication limits intraday usefulness
  - Empirical predictability strongest at 4-12 week horizon
- **Relevance to GTOS:** COT is freely-available weekly feature. Could feed K54 as positioning-extreme regime input. Combined with WGC ETF flow and CB demand, gives a 3-axis "demand pressure" feature set.
- **Potential hypothesis:** XAU SHORT WR is elevated in weeks immediately following speculator-COT crossing >2σ above 5-year mean.
- **Cross-domain links:** 14, 17, 22
- **Commodity subset:** gold

---

### Section 2.5 — Gold-stocks and gold-mining

#### Variables Explaining the Price of Gold Mining Stocks
- **Authors:** various (WTAMU SWER paper)
- **Year:** 2010s
- **Source:** Southwestern Economic Review
- **URL:** https://swer.wtamu.edu/sites/default/files/Data/81-88-279-1040-1-PB.pdf
- **Abstract:** Faff-Chan-style regression of gold mining stock returns on gold price, market index, FX, interest rates.
- **Key findings:**
  - Gold mining stock beta to gold price ≈ 1.5-2.0 (typical historical)
  - Operational leverage drives super-elasticity
  - Gold-leverage-effect: mining stocks amplify gold moves (10% gold → 30%+ profit move)
  - Decoupling during equity-market crises (mining tracks equity, not gold)
  - 2025 ETF performance: gold miner ETFs returned 96-110% vs 30% for physical gold
- **Relevance to GTOS:** GTOS does not directly trade mining stocks but the 2× beta finding is relevant context — when gold price moves, mining stocks (HUI / GDX / GDXJ) move ~2× and these are sometimes gateway-instruments for systemic gold flow. Cross-asset correlation gate could integrate GDX/GDXJ as a forward indicator.
- **Potential hypothesis:** Daily GDX-vs-XAU spread (deviation from 2× beta) is a contrarian signal for next-day XAU direction.
- **Cross-domain links:** 13, 14
- **Commodity subset:** gold

#### Re-examining the Real Option Characteristics of Gold for Gold Mining Companies
- **Authors:** various (Resources Policy)
- **Year:** 2020
- **Source:** Resources Policy
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S0301420720309211
- **Abstract:** Tests whether the embedded real option in mining firm valuation is empirically time-varying.
- **Key findings:**
  - Real option value time-varying, occurs over very short-run
  - Strongest during gold-price uptrends with high volatility
  - Mean-reverts at multi-year horizon
  - Connects mining-stock beta variability to gold-volatility regime
- **Relevance to GTOS:** Connects to gold-volatility regime. The time-varying real option suggests cross-asset hedge ratios for mining vs. physical gold are unstable.
- **Potential hypothesis:** None directly.
- **Cross-domain links:** 16, 13
- **Commodity subset:** gold

#### Gold Stocks, the Gold Price and Market Timing
- **Authors:** ap Gwilym, O.; Clare, A.
- **Year:** 2014 (CASS Business School working paper)
- **Source:** Bayes Business School / CASS WP
- **URL:** https://www.bayes.citystgeorges.ac.uk/__data/assets/pdf_file/0005/69935/Gold-Stocks,-The-Gold-Price-and-Market-Timing.pdf
- **Abstract:** Tests whether gold-stock vs gold-spot signals predict each other.
- **Key findings:**
  - Bidirectional Granger causality between gold and gold-stocks
  - Gold-stock signal modestly improves market-timing of physical gold
  - Lead-lag time ~1-3 weeks, regime-dependent
- **Relevance to GTOS:** Supports including GDX/HUI as a gold-side regime input.
- **Potential hypothesis:** None directly.
- **Cross-domain links:** 13, 14
- **Commodity subset:** gold

---

### Section 2.6 — Silver, platinum, palladium

#### Empirical Study on the Volatility Spillover Effect of Gold, Silver and Platinum Prices
- **Authors:** various (Enpress Publisher)
- **Year:** 2024
- **Source:** Financial Studies Journal
- **URL:** https://systems.enpress-publisher.com/index.php/FSJ/article/view/9514
- **Abstract:** GARCH / VAR analysis of volatility spillover among gold, silver, platinum.
- **Key findings:**
  - Gold-volatility transmission to silver is unidirectional
  - Gold and silver volatilities both transmit to platinum
  - Silver-to-platinum effect persistent
  - Platinum is volatility-receiver only
  - Asymmetric responses: gold and platinum are more sensitive to positive shocks; silver is more sensitive to negative shocks
- **Relevance to GTOS:** Direct empirical anchor for XAGUSD risk management. The asymmetric-response finding (silver: negative-shock-sensitive) is a side-aware risk parameter — silver SHORT trades may have different size scaling than LONG.
- **Potential hypothesis:** XAGUSD SHORT size should be reduced (vs LONG) on days when XAU realizes a large negative shock.
- **Cross-domain links:** 16, 03
- **Commodity subset:** silver/gold/platinum

#### On Volatility Transmission between Gold and Silver Markets: Evidence from a Long-Term Historical Period
- **Authors:** various (MDPI Computation 11(2))
- **Year:** 2023
- **Source:** Computation, MDPI
- **URL:** https://www.mdpi.com/2079-3197/11/2/25
- **Abstract:** Long-history study of gold-silver volatility spillover; spans 1970s-2020s.
- **Key findings:**
  - Gold-to-silver spillover stable across decades
  - Silver-to-gold spillover sometimes detected in commodity-stress periods
  - Spillover strength regime-dependent (stronger in crisis)
  - Implied vol (GVZ → VXSLV) effect ~10 month duration
- **Relevance to GTOS:** Justifies treating XAU shocks as exogenous input for XAG risk. Supports XAGUSD inheriting cross-instrument-correlation gate logic from XAUUSD.
- **Potential hypothesis:** None directly.
- **Cross-domain links:** 16
- **Commodity subset:** silver/gold

#### Gold Silver Pair Trading — Mean Reversion Strategy Using Machine Learning
- **Authors:** Mittal, V. K.; Mittal, R.
- **Year:** 2025
- **Source:** SSRN 5710242
- **URL:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5710242
- **Abstract:** Hybrid Kalman / cointegration / ML mean-reversion strategy for gold-silver ratio. Backtests 2015-2025.
- **Key findings:**
  - ML-filtered mean-reversion outperforms static cointegration
  - Sharpe improvement biggest during high-volatility regimes (2020 COVID, 2022 inflation, 2024 commodity rally)
  - Z-score normalization + regime-filter is the value-add layer
  - Long-term gold-silver ratio mean ~65-70:1
  - Outside historical range (often >100 or <40) signals high-probability reversion
- **Relevance to GTOS:** Direct empirical support for gold-silver ratio as XAGUSD regime input. The 65-70:1 historical mean is a useful benchmark; current ratio (often >85:1 in 2023-2025) suggests silver is structurally underpriced — implies a side-aware bias for XAG LONG.
- **Potential hypothesis:** XAGUSD LONG WR is elevated when gold-silver ratio is in upper decile of 5-year history.
- **Cross-domain links:** 15, 19
- **Commodity subset:** silver/gold

#### A Macroeconomic Viewpoint Using a Structural VAR Analysis of Silver Price Behaviour
- **Authors:** various
- **Year:** 2023
- **Source:** Mineral Economics, Springer
- **URL:** https://link.springer.com/article/10.1007/s13563-023-00386-y
- **Abstract:** SVAR analysis of silver price drivers — supply, demand, monetary, industrial.
- **Key findings:**
  - Industrial demand explains ~45-50% of silver price variation
  - Solar PV demand growing share over 2015-2023
  - Monetary / safe-haven channel weaker than for gold
  - Gold-silver ratio regime-driven (industrial-cycle vs monetary-cycle)
  - Silver Institute 2024 report: 1,306Moz demand vs 1,034Moz supply (272Moz deficit, record)
- **Relevance to GTOS:** Supports silver = industrial-tilted exposure. XAGUSD edge mechanism may differ from XAUUSD: less monetary, more industrial-cycle. Implies different feature set in K54 for XAG vs XAU.
- **Potential hypothesis:** XAGUSD edge has higher correlation with copper price than with DXY, while XAUUSD is opposite.
- **Cross-domain links:** 11, 16
- **Commodity subset:** silver

#### Silver Price Forecasting Using Extreme Gradient Boosting (XGBoost)
- **Authors:** various (MDPI Mathematics 11(18))
- **Year:** 2023
- **Source:** Mathematics, MDPI
- **URL:** https://www.mdpi.com/2227-7390/11/18/3813
- **Abstract:** XGBoost forecasting model for silver price using 80+ features.
- **Key findings:**
  - XGBoost beats linear / ARIMA on out-of-sample silver
  - Most important features: gold price, oil, USDX, copper
  - Silver-specific industrial-demand features add modest improvement
  - Macro / economic uncertainty indices have nonzero importance
- **Relevance to GTOS:** Empirical reference for K54 silver feature set. Confirms gold price as #1 silver feature — corroborates the cross-instrument correlation gate logic.
- **Potential hypothesis:** None directly.
- **Cross-domain links:** 19
- **Commodity subset:** silver

---

### Section 2.7 — Cross-asset correlation, oil, copper, currencies

#### Tail Risk Spillover Effects in Commodity Markets: A Comparative Study of Crisis Periods
- **Authors:** various
- **Year:** 2023
- **Source:** Journal of Commodity Markets
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S2405851323000600
- **Abstract:** Tests gold tail-risk spillover with stocks, oil, FX during crisis vs tranquil periods.
- **Key findings:**
  - Gold acts as safe-haven (reduces extreme downside risk) during GFC; same not confirmed for COVID
  - Connectedness is higher for gold/silver/oil during stress
  - Crisis-period spillover increases dramatically
  - COVID-19 + Russia-Ukraine: cross-shock spillovers elevated
  - Gold's safe-haven property is crisis-type-specific
- **Relevance to GTOS:** Caveats the safe-haven thesis. For 2026 / current era, gold's safe-haven role may be partial / type-specific. Cross-instrument correlation gate should not assume gold-uncorrelated-with-stocks during all stress.
- **Potential hypothesis:** None directly.
- **Cross-domain links:** 13, 03
- **Commodity subset:** gold

#### Volatility Modeling and Tail Risk Estimation of Financial Assets: Evidence from Gold, Oil, Bitcoin, and Stocks
- **Authors:** various (MDPI Risks 13(7))
- **Year:** 2025
- **Source:** Risks, MDPI
- **URL:** https://www.mdpi.com/2227-9091/13/7/138
- **Abstract:** Cross-asset comparison of GARCH / EVT for tail-risk; gold included.
- **Key findings:**
  - Gold has lowest volatility of compared assets (gold, oil, BTC, stocks)
  - All assets have non-zero skew + excess kurtosis (fat-tailed)
  - GPD-based VaR superior to normal-based VaR for gold
  - Gold tail behavior more "stable" than other risk assets
  - 95% / 99% VaR ratios consistent with EVT theory
- **Relevance to GTOS:** Supports applying EVT-based size-of-extreme-loss for XAU position sizing. Particularly for the 1% risk per trade × max 1.5R loss rule — EVT estimates of XAU 1d 99.5% loss anchors what "1.5R worst case" actually means.
- **Potential hypothesis:** None directly.
- **Cross-domain links:** 03, 21
- **Commodity subset:** gold/silver

#### Are Spillover Effects Between Oil and Gold Prices Asymmetric? Evidence from the COVID-19 Pandemic
- **Authors:** various (Energy Research Letters)
- **Year:** 2021
- **Source:** Energy Research Letters
- **URL:** https://erl.scholasticahq.com/article/28127
- **Abstract:** Asymmetric spillover analysis between oil and gold markets during COVID era.
- **Key findings:**
  - Oil-to-gold spillover stronger than gold-to-oil
  - Tranquil regime: positive dependence; crisis regime: negative dependence
  - 5.22% of gold-market variance attributable to oil shocks
  - 4.62% return transmission from gold to oil
  - Asymmetric magnitudes between positive and negative shocks
- **Relevance to GTOS:** Supports oil-XAU as a regime feature (oil shock → XAU drift). Asymmetric dependence aligns with regime-conditional approach.
- **Potential hypothesis:** XAU LONG WR is asymmetric across days where oil >2% gain vs >2% loss.
- **Cross-domain links:** 13
- **Commodity subset:** gold/oil

#### When Gold Meets Copper: A Comprehensive Look at the Informative Role of the Relative Value of Gold on Global Stock Markets
- **Authors:** Roh, T.-Y.; Kim, D.; Yoon, S.-J.; You, Y.
- **Year:** 2024
- **Source:** SSRN 5677761
- **URL:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5677761
- **Abstract:** Tests gold-to-copper ratio (and copper-to-gold) as forecasting variable for global stock returns.
- **Key findings:**
  - Gold-to-copper ratio has predictive power for short-term (3-12mo) stock returns
  - Predictability stronger during recessions
  - Copper-to-gold ratio leads 10Y Treasury yield (1pp ratio increase → ~30bp yield rise within 12wk)
  - Robust across developed and emerging markets
  - Channel: gold = risk-off proxy; copper = risk-on / cycle proxy
- **Relevance to GTOS:** Provides macro feature for K54 (copper-gold ratio as risk-cycle indicator). Could differentiate "gold rallying because risk-off" vs "gold rallying because dollar-weakness" — these regimes likely require different LONG-side selectivity.
- **Potential hypothesis:** XAU LONG WR is positively correlated with falling copper-gold ratio (risk-off signal), negatively when ratio is rising.
- **Cross-domain links:** 13, 11
- **Commodity subset:** gold/copper

#### Relationship Between the Gold Price and the Australian Dollar / US Dollar Exchange Rate
- **Authors:** various (Curtin University; Mineral Economics 28)
- **Year:** 2015
- **Source:** Mineral Economics, Springer
- **URL:** https://link.springer.com/article/10.1007/s13563-015-0067-y
- **Abstract:** Empirical bidirectional analysis of XAU-AUDUSD with VAR / Granger causality.
- **Key findings:**
  - Bidirectional Granger causality between gold and AUDUSD
  - 1% gold price increase → ~0.5% AUDUSD appreciation
  - Correlation coefficient ~0.77 in long-run
  - Australia is major gold exporter; AUD is "commodity currency"
  - Relationship sensitive to other-commodity prices (iron ore, coal)
- **Relevance to GTOS:** Strong empirical anchor for cross-instrument correlation gate's AUD inclusion. The bidirectionality means the gate works in both directions of the trade.
- **Potential hypothesis:** None directly.
- **Cross-domain links:** 11, 13
- **Commodity subset:** gold

#### Dynamic Correlations of Gold and S&P 500 Returns (DCC-GARCH)
- **Authors:** various (multiple papers in 2010s-2020s)
- **Year:** 2018-2022
- **Source:** various
- **URL:** https://www.researchgate.net/figure/Dynamic-correlations-of-Gold-and-S-P-500-returns-obtained-with-the-BEKK-GARCH-between_fig5_323935694
- **Abstract:** DCC-GARCH and BEKK-GARCH analyses of time-varying gold-stock correlations.
- **Key findings:**
  - Gold-stock correlation switches sign over time
  - Pre-2020: typically slightly negative (safe haven)
  - 2020+: more frequent positive episodes (correlation +0.945 Sept 2024 — extreme)
  - Crisis periods reverse pattern but in unpredictable directions
  - DCC-GARCH well-suited for regime-aware sizing
- **Relevance to GTOS:** Direct support for time-varying / regime-conditional correlation gate. The Sept-2024 +0.945 correlation event is a regime-anomaly that could justify a regime-detector-driven correlation gate threshold.
- **Potential hypothesis:** Cross-instrument correlation gate threshold should be regime-conditional (tighter when DCC > 0.5 between XAU and SPX).
- **Cross-domain links:** 13, 16
- **Commodity subset:** gold

---

### Section 2.8 — Bubbles, structural breaks, and regime detection

#### Do Bubbles Occur in the Gold Price? Investigation of Gold Lease Rates and Markov-Switching Models
- **Authors:** various
- **Year:** 2013
- **Source:** Journal of Commodity Markets
- **URL:** https://www.sciencedirect.com/science/article/pii/S2214845013000136
- **Abstract:** Tests whether gold price contains rational speculative bubbles using lease-rate as fundamental measure.
- **Key findings:**
  - Standard ADF + cointegration tests indicate bubbles
  - Markov-Switching ADF gives mixed evidence
  - Variance-switching specifications: no bubble
  - 2002-2008 period was super-exponential growth
  - 2002-2012: explosive process
- **Relevance to GTOS:** Methodologically anchors structural-break / regime-detection logic. The mixed-evidence finding cautions against confident "bubble = mean-revert soon" narrative.
- **Potential hypothesis:** None directly.
- **Cross-domain links:** 05, 17
- **Commodity subset:** gold

#### Speculative Trading in the Gold Market
- **Authors:** various (Journal of International Financial Markets, Institutions & Money)
- **Year:** 2015
- **Source:** International Review of Financial Analysis
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S1057521915000344
- **Abstract:** Decomposes gold price into speculative and fundamental components.
- **Key findings:**
  - 2002-2012 period had significant speculative-driven component
  - Speculative pressure correlates with COT large-spec net long
  - Speculative episodes precede mean-reversion at multi-month horizon
  - Fundamental (real-rate / DXY-driven) component dominates long-run
  - Identifies regimes where speculation > fundamentals
- **Relevance to GTOS:** Connects to COT positioning as regime feature. Multi-month-mean-reversion finding may explain part of H2-2026 H1 → H2 LONG decay (speculative-positioning unwinding).
- **Potential hypothesis:** None directly.
- **Cross-domain links:** 17, 22
- **Commodity subset:** gold

#### A Power GARCH Examination of the Gold Market
- **Authors:** Tully, E.; Lucey, B. M.
- **Year:** 2007
- **Source:** Research in International Business and Finance, 21(2), 316-325
- **URL:** https://brianmlucey.wordpress.com/wp-content/uploads/2011/05/power_garchgold.pdf
- **Abstract:** APGARCH analysis of gold market volatility 1980s-2000s. Identifies main influences on conditional variance.
- **Key findings:**
  - APGARCH(1,1) outperforms GARCH(1,1) on gold
  - Asymmetric leverage effect present
  - DXY and S&P shocks transmit to gold-volatility
  - Long-memory parameter d > 0.4 (strong persistence)
  - Predates RGARCH but pioneered asymmetric-vol modeling for gold
- **Relevance to GTOS:** Methodological prior for any volatility-based regime feature in K54.
- **Potential hypothesis:** None directly.
- **Cross-domain links:** 16, 03
- **Commodity subset:** gold

#### Psychological Barriers in Gold Prices?
- **Authors:** Aggarwal, R.; Lucey, B. M.
- **Year:** 2007
- **Source:** Review of Financial Economics, 16(2), 217-230
- **URL:** https://onlinelibrary.wiley.com/doi/10.1016/j.rfe.2006.04.001
- **Abstract:** Tests for psychological round-number barriers in daily and intraday gold prices.
- **Key findings:**
  - Statistically significant psychological barriers at $50 / $100 / $1000 levels
  - Effect persists in intraday data
  - Mean-reversion magnitude elevated within ±2% of barriers
  - Behavioral / mass-attention channel
- **Relevance to GTOS:** Strong theoretical anchor for round-number magnetism logic in M15-OB-detection. Suggests OB / FVG / liquidity-pool levels coinciding with $X000 figures should have elevated significance.
- **Potential hypothesis:** GTOS XAU OB-zone continuation rate is elevated when OB midpoint is within ±0.5% of nearest $50 / $100 round figure.
- **Cross-domain links:** 09, 17
- **Commodity subset:** gold

---

### Section 2.9 — Calendar / seasonality / event effects

#### The Impact of Festivities on Gold Price Expectation and Volatility
- **Authors:** Roesch, A.; Schmidbauer, H.
- **Year:** 2018
- **Source:** Journal of International Financial Markets, Institutions & Money
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S1057521918301753
- **Abstract:** Tests global gold price effects around major Asian festivals 1991-2012.
- **Key findings:**
  - Akshaya Tritiya, Chinese New Year, Christmas, Dussehra, Ramadan Eid all impact gold price distribution
  - Diwali NOT statistically significant in global prices (only local Indian)
  - September and November are seasonally elevated months (Indian wedding season)
  - Effect mostly volatility-channel, less directional
  - Local-market effects strong; global-market effect weaker
- **Relevance to GTOS:** Direct support for date-aware regime features — Akshaya Tritiya, Chinese New Year, Indian wedding season are all known volatility-elevation events. Could enhance K54 by adding event-window regime indicator.
- **Potential hypothesis:** XAU intraday volatility is elevated on Akshaya Tritiya and CNY days; risk-gate may flatten or scale down sizing.
- **Cross-domain links:** 17, 09
- **Commodity subset:** gold

#### Calendar Anomalies in Commodity Markets for Natural Resources: Evidence from India
- **Authors:** various
- **Year:** 2022
- **Source:** Resources Policy
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S0301420722004627
- **Abstract:** Tests calendar effects (day-of-week, month-of-year, turn-of-year) for Indian commodity markets including gold.
- **Key findings:**
  - January-effect / turn-of-year effect NOT found in Indian commodity markets
  - Some day-of-week and month-of-year effects detected
  - Gold-specific effects weaker than equity-specific
  - Holiday effect present around major festivals
- **Relevance to GTOS:** Adds caveats: turn-of-year doesn't apply universally for gold. Useful negative finding for K54 (don't add a January-effect feature without testing).
- **Potential hypothesis:** None — negative finding.
- **Cross-domain links:** 09, 17
- **Commodity subset:** gold

#### Examination of the Existence of Month of the Year, Day of the Week, and Seasonal Anomalies in Gold Futures Contracts (Turkey)
- **Authors:** various
- **Year:** 2023
- **Source:** ResearchGate / Turkish journal
- **URL:** https://www.researchgate.net/publication/372718966
- **Abstract:** Tests calendar anomalies in Turkish gold futures.
- **Key findings:**
  - Positive returns in January and March
  - Some weekday effects detected (Tuesday-effect-like)
  - Effects weaker post-2010
  - Local market specifics interact with global gold trends
- **Relevance to GTOS:** Modest support for January-effect (in some markets). Not generalizable to global XAUUSD.
- **Potential hypothesis:** None directly.
- **Cross-domain links:** 09
- **Commodity subset:** gold

---

### Section 2.10 — Recent regime: COVID, Bitcoin, central bank super-cycle

#### Hedge and Safe Haven Properties During COVID-19: Evidence from Bitcoin and Gold
- **Authors:** Akhtaruzzaman, Boubaker, Lucey, Sensoy
- **Year:** 2021
- **Source:** Economic Modelling
- **URL:** https://pmc.ncbi.nlm.nih.gov/articles/PMC8648322/
- **Abstract:** Tests gold and Bitcoin as hedge / safe haven during COVID phases.
- **Key findings:**
  - Gold safe-haven for stocks in Phase I (Dec 2019 - Mar 16, 2020)
  - Gold lost safe-haven role in Phase II (Mar 17 - Apr 24, 2020) — equity-correlated drop
  - Bitcoin not consistent safe-haven during COVID
  - Phase-dependent / regime-dependent safe-haven property
  - Liquidity-stress dominates safe-haven properties at extreme stress
- **Relevance to GTOS:** Important caveat: gold's safe-haven property failed at peak-stress. Cross-instrument correlation gate should not assume gold protects when liquidity-stress is extreme.
- **Potential hypothesis:** None directly.
- **Cross-domain links:** 17, 13
- **Commodity subset:** gold

#### Assessing Bitcoin and Gold as Safe Havens Amid Global Uncertainties: A Rolling Window DCC-GARCH Analysis
- **Authors:** Kumar, Mohan, Niveditha
- **Year:** 2025
- **Source:** Margin: Journal of Applied Economic Research, 19(2)
- **URL:** https://journals.sagepub.com/doi/10.1177/09711023251322578
- **Abstract:** Rolling DCC-GARCH analysis of gold vs Bitcoin during 2020-2024 multi-stress era.
- **Key findings:**
  - Gold remains primary safe-haven across most stress events
  - Bitcoin partial safe-haven for emerging-market currencies
  - Rolling-window correlations switch sign in stress
  - Gold-BTC competition increases by 2024-2025
  - Future scenario: 50/50 reserve allocation discussed in DB / institutional research
- **Relevance to GTOS:** Recent regime literature supports "gold = primary safe haven." Bitcoin's partial-safe-haven for EM-currency may be irrelevant to GTOS but bears watching.
- **Potential hypothesis:** None directly.
- **Cross-domain links:** 17, 22
- **Commodity subset:** gold

#### Gold's Role During Multi-Crisis Era: Russia-Ukraine + Sanctions
- **Source:** IMF / WGC / Federal Reserve research 2022-2024
- **URL:** https://www.federalreserve.gov/econres/ifdp/files/ifdp1420.pdf
- **Abstract:** Federal Reserve / IMF / WGC tracking of gold-allocation changes 2020-2024.
- **Key findings:**
  - Sanctions on Russia 2022 catalyzed CB gold demand
  - 2022 / 2023 / 2024 each >1,000t (vs 473t 2010-2021 average)
  - Sanctions-channel verified empirically (Arslanalp et al. 2023)
  - Geopolitical-risk channel + de-dollarization channel separable
  - Permanent / structural rather than transitional
- **Relevance to GTOS:** Validates multi-year-bull thesis. CB-driven flow is largely structural and price-insensitive — less reactive to short-term technicals → could explain F2 / F15 LONG decay (technicals matter less when flow is dominant).
- **Potential hypothesis:** None directly.
- **Cross-domain links:** 11, 22, 17
- **Commodity subset:** gold

---

### Section 2.11 — ML and forecasting

#### Forecasting Gold Price Using Machine Learning Methodologies
- **Authors:** various
- **Year:** 2023
- **Source:** Chaos, Solitons & Fractals
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S0960077923009803
- **Abstract:** Comparison of ML methods (XGBoost, RF, NN) for gold forecasting.
- **Key findings:**
  - XGBoost / random forest competitive with simple deep learning at 1d horizon
  - Feature importance: DXY > oil > S&P > silver > geopolitical risk
  - Performance degrades at multi-week horizons
  - Out-of-sample R² typically 5-15%
  - SHAP values reveal regime-shift in feature importance
- **Relevance to GTOS:** Methodological reference for K54 baseline. Confirms DXY top-feature ranking.
- **Potential hypothesis:** None directly.
- **Cross-domain links:** 19
- **Commodity subset:** gold

#### Gold Price Prediction by a CNN-Bi-LSTM Model
- **Authors:** various (PLOS ONE)
- **Year:** 2024
- **Source:** PLOS ONE
- **URL:** https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0298426
- **Abstract:** CNN + Bidirectional LSTM hybrid for gold price prediction with auto-tuning.
- **Key findings:**
  - CNN-Bi-LSTM beats LSTM / GRU / ARIMA
  - Auto-parameter tuning provides modest improvement
  - Sample period 2014-2023 includes regime shifts
  - Sensitive to feature normalization
- **Relevance to GTOS:** Methodological reference; suggests deep-sequence models add ~3-5pp accuracy over simpler methods at 1d horizon. Likely diminishing returns vs K54-LightGBM baseline complexity cost.
- **Potential hypothesis:** None directly.
- **Cross-domain links:** 19
- **Commodity subset:** gold

#### Which Uncertainty Measure Better Predicts Gold Prices? New Evidence from a CNN-LSTM Approach
- **Authors:** various
- **Year:** 2025
- **Source:** North American Journal of Economics and Finance
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S1062940825000154
- **Abstract:** Tests EPU, IDEMV, VIX, GPR, T10Y3M as gold-price predictors in CNN-LSTM.
- **Key findings:**
  - EPU (Economic Policy Uncertainty) outperforms VIX as gold predictor
  - IDEMV (Equity Market Volatility tracker) provides incremental value
  - GPR effect concentrated on high-stress days
  - Multi-uncertainty ensemble best
  - Macro-financial uncertainty channel dominant
- **Relevance to GTOS:** Direct empirical support for adding EPU + IDEMV + GPR as features in K54. The ensemble-best finding suggests multi-feature regime classifier outperforms univariate.
- **Potential hypothesis:** Adding EPU + IDEMV + GPR to K54 improves OOS AUC by ≥3pp.
- **Cross-domain links:** 19, 17
- **Commodity subset:** gold

---

### Section 2.12 — Long-memory, distributional, contrarian

#### Anything But Gold — The Golden Constant Revisited
- **Authors:** Bilgin, Gozgor, Lau, Sheng
- **Year:** 2021
- **Source:** Journal of Commodity Markets, 25
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S2405851321000040
- **Abstract:** Reanalysis of golden constant thesis with extended data; tests inflation-hedge with structural breaks.
- **Key findings:**
  - Even extended data reaffirms gold-as-inflation-hedge is regime-dependent
  - Real returns are unstable across decades
  - Modern monetary regime (post-1971) shows different patterns vs gold-standard era
  - Cross-country evidence: stronger in countries with looser monetary policy
  - Mean-reversion in real gold price confirmed
- **Relevance to GTOS:** Reinforces F11 / F15 — empirical decay is consistent with academic mean-reversion expectation.
- **Potential hypothesis:** None directly.
- **Cross-domain links:** 03, 05, 17
- **Commodity subset:** gold

#### Extreme Value Theory and Gold Price Extremes 1975-2025
- **Authors:** various (MDPI Risks 4(4))
- **Year:** 2025
- **Source:** Risks, MDPI
- **URL:** https://www.mdpi.com/2813-2432/4/4/24
- **Abstract:** EVT analysis of 50-year gold-price extreme returns. Long-term VaR and ES.
- **Key findings:**
  - Gold returns clearly fat-tailed (Hill estimator confirms)
  - GPD better fit than GEV for left and right tails
  - 99.5% VaR ~3-4× normal-distribution-based estimate
  - Tail-index varies modestly by decade
  - 1980 / 2008 / 2020 are tail-extreme events
- **Relevance to GTOS:** Direct empirical anchor for risk-of-ruin / position-sizing logic. The 3-4× VaR ratio means a "1.5R worst case" assumption from normal-distribution thinking would understate true 99.5% loss by ~4×.
- **Potential hypothesis:** None directly.
- **Cross-domain links:** 03, 21
- **Commodity subset:** gold

#### Gold Demand Trends — Q4 / Full Year 2024 (WGC)
- **Authors:** World Gold Council
- **Year:** 2025
- **Source:** WGC publications
- **URL:** https://www.gold.org/goldhub/research/gold-demand-trends/gold-demand-trends-full-year-2024
- **Abstract:** Comprehensive demand decomposition by sector (jewelry, investment, industrial, central bank).
- **Key findings:**
  - 2024 LBMA Gold Price reached 40 new record highs
  - Q4 average price US$2,663/oz; annual US$2,386/oz (+23%)
  - Investment 1,180t (+25%) — 4-year high
  - Jewelry, industrial demand both robust
  - 2024 Central Bank Survey reaffirms multi-year gold-share rise
- **Relevance to GTOS:** Quantitative grounding for the structural-bull thesis. Useful for sanity-checking K54 features in context of base rates.
- **Potential hypothesis:** None directly.
- **Cross-domain links:** 22
- **Commodity subset:** gold

#### On the Lease Rate, the Convenience Yield and Speculative Effects in the Gold Futures Market
- **Authors:** Barone-Adesi, Hilliker (Swiss Finance Institute RP 0907)
- **Year:** 2009
- **Source:** Swiss Finance Institute Research Paper
- **URL:** https://ideas.repec.org/p/chf/rpseri/rp0907.html
- **Abstract:** Tests gold lease rate (GOFO-derived) as proxy for convenience yield + speculative pressure.
- **Key findings:**
  - Gold lease rate proxies convenience yield better than IAB
  - Lease rate has asymmetric relationship with discretionary inventory
  - Speculative-pressure component identifiable
  - Strong negative effect on inventory at 1/3/6mo tenors
  - Connects to both market-stress and basis-trading literature
- **Relevance to GTOS:** Lease rates publicly available; could enrich K54 with funding-stress regime feature.
- **Potential hypothesis:** Elevated lease rates correlate with reduced XAU LONG WR (funding-squeeze regime).
- **Cross-domain links:** 22, 16
- **Commodity subset:** gold

---

## 3. Domain summary statistics

- **Total entries:** 47
- **Gold-specific:** 35
- **Silver-specific:** 5 (within gold-silver dual)
- **Multi-metal:** 5
- **Cross-asset / commodity general:** 7
- **Post-2020 papers:** 19 (~40%)
- **Foundational pre-2015:** 12

---

## 4. Top relevance-to-GTOS rankings

Top 5 papers most directly relevant to GTOS XAUUSD edge:

1. **Caminschi & Heaney (2014) — LBMA Fix anomaly** — direct empirical justification for NY-kill-zone window edge.
2. **Pukthuanthong & Roll (2011) — Gold and the Dollar** — empirical anchor for cross-instrument correlation gate's USD/JPY/GBP/EUR threshold.
3. **Chicago Fed Letter 464 (2021) — What Drives Gold Prices?** — quantitative anchor for K54 macro-feature priors (real rate / inflation expectation / GDP).
4. **Sobti (2025) — Intraday Jumps in Gold** — empirical jump rates + macro-news predictability for risk-gate around event windows.
5. **Arslanalp, Eichengreen, Simpson-Bell (2023) — Gold as International Reserves: Barbarous Relic No More?** — anchors the structural-CB-buying era and explains why current regime differs from 2002-2012 speculative bubble era.

---

## 5. Top hypotheses for Phase 3 backlog

1. **Regime-conditional cross-instrument correlation gate.** Gate threshold |corr| ≥ 0.4 should tighten to 0.3 when DCC-detected stress regime active (VIX > 25 or DCC-S&P > 0.5). Baked from Pukthuanthong-Roll + nonlinear-dynamics + DCC-GARCH literature.

2. **GPR + EPU + IDEMV ensemble macro-uncertainty feature in K54.** Three-factor uncertainty index outperforms single-factor in gold-prediction (Bonato et al.; CNN-LSTM 2025 paper). Add as K54 feature and test ≥3pp OOS AUC lift.

3. **NFP / FOMC / fix-window event-flatten gate.** Direct empirical evidence for elevated volatility / asymmetric reactions. Test whether 60-min flat window around NFP / FOMC reduces drawdown without sacrificing edge.

4. **Side-aware bias on gold-silver-ratio extremes for XAGUSD.** Gold-silver ratio in upper decile predicts silver mean-reversion. Implement XAG LONG sizing bias in upper-decile regimes, XAG SHORT bias in lower-decile.

5. **Round-number psychological barrier as OB-zone-confluence feature.** Aggarwal-Lucey psychological barriers + ICT-style OB confluences should compound; predict elevated OB continuation rate when OB midpoint within ±0.5% of nearest $50/$100 round.

6. **Real-gold-price-percentile regime feature.** Erb-Harvey 2024 update suggests current real-gold-price is 75th-percentile historically — mean-reversion-prone. Add as regime indicator; test whether GTOS LONG edge degrades in upper-quartile regimes.

7. **GLD / WGC ETF flow as pseudo-real-time positioning feature.** 5-day GLD net flow correlates with momentum regime. Add as K54 feature.

---

## 6. Cross-domain handoffs (papers that may belong elsewhere)

- **Real-rate / TIPS macro modeling** → 11 may also claim. Owner: 10 keeps the gold-asset side; 11 keeps TIPS-as-rate-instrument.
- **Caminschi-Heaney LBMA fix as round-number / level-magnetism** → cross-link to 09; 10 retains.
- **DCC-GARCH gold-stocks** → cross-link to 13 (correlation models), 16 (DCC methodology). 10 retains as gold-context paper.
- **Gold mining stocks beta → real options** → cross-link to 13 (factor exposure) and 14 (operating leverage). 10 retains as commodity-beta paper.
- **Calendar / festival effects** → cross-link to 09 (level-magnetism), 17 (behavioral); 10 retains gold-specific empirical finding.
- **Speculative bubbles in gold** → cross-link to 17 (behavioral) and 22 (alpha decay narrative); 10 retains.

---

## 7. Gaps and caveats

1. **High-frequency gold microstructure / OFI literature is thin** — most academic gold-market work uses daily / intraday-aggregate. The kill-zone-specific OB-zone literature for gold does not exist academically; GTOS's edge mechanism (OB zones) has stronger empirical support from F11 / Phase 1 internal work than from peer-reviewed gold microstructure.
2. **Side-aware (LONG vs SHORT) gold edge literature is thin** — most papers test directional gold without distinguishing LONG-side vs SHORT-side specifically. F2 / F15 / A6 internal findings appear novel relative to academic literature.
3. **Decay-velocity literature for technical edges in gold is essentially nonexistent.** F11 OB-zone-decay-velocity and McLean-Pontiff (cross-asset alpha decay, domain 22) frame the question; no gold-specific replication study exists.
4. **2026-specific regime literature is too recent for peer-reviewed work** — most Russia-Ukraine / sanctions-era findings are 2022-2024 working papers. K52 / F15 / S79 internal work on the 2026 regime is at the academic frontier.
5. **Silver microstructure literature thinner than gold** — the gold-silver volatility-spillover literature is mature, but silver-specific microstructure / intraday work is sparse. Implications: XAGUSD regime classifier may need to inherit from XAU work more aggressively.
6. **Track record of published gold-prediction ML papers is mediocre** — typical OOS R² 5-15% suggests modest predictive power at 1d horizon. K54 marginal AUC 0.571 is in the literature distribution.

---

*Compiled by Phase 1 Worker Agent #10 — 2026-04-28. Subscription-bounded WebSearch + WebFetch only. UTF-8.*
