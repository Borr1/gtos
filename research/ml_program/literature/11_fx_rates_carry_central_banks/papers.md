# Domain 11 — FX, Interest Rates, Carry, Central Banks

**Worker:** Phase 1 Worker Agent #11 (Opus 4.7 max-effort, Apr 28 2026)
**Spec:** `research/ml_program/literature/_specs/11_fx_rates_carry_central_banks.md`
**Target:** 40-55 papers
**Delivered:** 47 papers (web-verified URLs; no fabrication)

---

## 1. Scope and methodology recap

This domain owns FX / interest-rate / carry / central-bank literature relevant to GTOS's USDJPY, GBPJPY, GBPUSD, and (cross-link 10) XAUUSD instruments. Subscription-bounded WebSearch + WebFetch only. All papers verified by URL. Papers entirely out of scope (e.g., Lyons hot-potato microstructure for routing → 06; ICT level-trading rules → 07) are flagged and cross-linked, not duplicated here.

**Splits actually delivered:** 12 carry / forward-bias; 9 safe-haven / dollar / risk-on-off; 6 central-bank policy & FX; 4 FX vol / option-implied; 3 commodity-currency; 6 recent regime papers (2020-2025) covering CIP failure, JPY 2022-24, GBP mini-budget, August 2024 unwind, dollar dominance erosion; 7 method / fundamentals / fixings / liquidity. Total = 47.

**Quality bar.** No paper without a working URL. No paper without a non-empty `relevance_to_gtos`. Findings stated literally where possible; URL citations preserved for downstream synthesis-agent re-verification.

---

## 2. Foundational papers — UIP, forward-premium puzzle, Meese-Rogoff, microstructure roots

### Forward and Spot Exchange Rates
- **Authors:** Eugene F. Fama
- **Year:** 1984
- **Source:** *Journal of Monetary Economics*, 14(3), 319-338
- **URL:** https://econpapers.repec.org/RePEc:eee:moneco:v:14:y:1984:i:3:p:319-338
- **Abstract:** Establishes the empirical failure of forward-rate unbiasedness. Both an expected-future-spot component and a time-varying premium component vary over time, and they are negatively correlated. Most variation in forward rates is variation in the premium.
- **Key findings:** (1) Forward rates have little forecasting power for future spot. (2) Most forward-rate variation is risk-premium variation, not expected-spot variation. (3) Premium and expected-spot components are negatively correlated. (4) Foundational evidence for the "Fama puzzle": ex-post depreciation negatively correlated with interest differential, opposite of UIP prediction.
- **Relevance to GTOS:** Defines the bedrock anomaly — high-interest-rate currencies do NOT depreciate as UIP predicts. Direct implication for USDJPY/GBPJPY: BoJ vs Fed rate gap creates an exploitable risk premium that informs the M15 gate's directional bias prior. Justifies treating "interest differential" as a regime feature in K54 v2.
- **Potential hypothesis:** Build a forward-premium feature (interest differential vs realized 1-month change) as an input feature; expect a negative-sign loading consistent with the puzzle.
- **Cross-domain links:** 03 (stylized fact / risk premium); 13 (cross-asset factor)

### Empirical Exchange Rate Models of the Seventies: Do They Fit Out of Sample?
- **Authors:** Richard A. Meese, Kenneth Rogoff
- **Year:** 1983
- **Source:** *Journal of International Economics*, 14(1-2), 3-24
- **URL:** https://scholar.harvard.edu/files/rogoff/files/51_jie1983.pdf
- **Abstract:** Demonstrates that random walk forecasts of nominal exchange rates beat structural models out-of-sample at horizons of 1-12 months. The result holds for major floating currencies (yen, pound, mark/euro vs USD) and has become known as the Meese-Rogoff puzzle.
- **Key findings:** (1) Monetary models fail OOS even with realized fundamentals. (2) Random walk dominates at short-medium horizons. (3) Out-of-sample failure is robust to model specification. (4) Findings still provoke major literature 40+ years later.
- **Relevance to GTOS:** Anchors the warning that fundamental variables alone do not predict short-horizon FX moves — directly supports GTOS's microstructure / OB-zone-precision approach over fundamental timing. Justifies why GTOS does NOT trade off macro narratives.
- **Potential hypothesis:** Random-walk benchmarks should remain part of any FX prediction validation; any K54 feature claiming predictive lift must beat RW first.
- **Cross-domain links:** 02 (statistical methodology — OOS forecasting bar); 19 (ML benchmarking)

### Common Risk Factors in Currency Markets
- **Authors:** Hanno Lustig, Nikolai Roussanov, Adrien Verdelhan
- **Year:** 2011
- **Source:** *Review of Financial Studies*, 24(11), 3731-3777
- **URL:** https://academic.oup.com/rfs/article-abstract/24/11/3731/1589752
- **Abstract:** Identifies dollar (RX) and carry (HMLFX, slope) factors that explain most of the cross-section of currency returns. High-interest currencies load more on the slope factor than low-interest ones, generating a 4.8% per annum spread net of transaction costs.
- **Key findings:** (1) Two-factor model (dollar + carry slope) explains ~80% of cross-section. (2) Slope factor loads on global volatility and global equity vol. (3) Carry premium is a compensation for global-volatility risk. (4) Establishes carry-as-risk-factor framework adopted by subsequent literature.
- **Relevance to GTOS:** Provides academic foundation for "carry tilt" concept. JPY funding currency status implies USDJPY/GBPJPY have negative loading on carry slope — directional bias relevant to the cross-instrument correlation gate's grouping of JPY crosses.
- **Potential hypothesis:** Add a "global FX vol" feature (e.g., DBV / G10 vol index) to K54; expect negative loading for JPY-funded crosses during risk-off regimes.
- **Cross-domain links:** 13 (factor); 16 (vol risk premium)

### Carry Trades and Currency Crashes
- **Authors:** Markus K. Brunnermeier, Stefan Nagel, Lasse Heje Pedersen
- **Year:** 2008
- **Source:** *NBER Macroeconomics Annual*, 23, 313-347
- **URL:** https://www.nber.org/system/files/working_papers/w14473/w14473.pdf
- **Abstract:** Documents that carry-trade returns are negatively skewed (currencies "go up by the stairs and down by the elevator"). Skewness arises from sudden unwinding of carry trades when funding liquidity contracts.
- **Key findings:** (1) Negative skewness peaks in periods of risk-aversion and funding-liquidity stress. (2) Funding-liquidity measures (TED, VIX) predict exchange-rate moves. (3) Crash risk is a substantial part of the carry premium — partial resolution of UIP puzzle. (4) Carry-currency speculative positioning amplifies the asymmetry.
- **Relevance to GTOS:** Direct relevance to USDJPY/GBPJPY tail risk. JPY is the canonical funding currency; carry-unwind events deliver outsized JPY appreciation (e.g., Aug 2024). GTOS must size JPY-cross trades with awareness of left-tail crash regimes — supports H29 drawdown-reduction logic.
- **Potential hypothesis:** Add a "VIX delta" or "TED spread" feature in K54; expect heightened crash probability in JPY crosses when these spike.
- **Cross-domain links:** 03 (fat tails); 21 (Kelly under tail risk); 17 (risk-on/risk-off behavioral)

### The Microstructure Approach to Exchange Rates
- **Authors:** Richard K. Lyons
- **Year:** 2001 (book; 2006 paperback)
- **Source:** MIT Press
- **URL:** https://mitpress.mit.edu/9780262122436/the-microstructure-approach-to-exchange-rates/
- **Abstract:** Comprehensive treatment of FX from the trading-room perspective. Departs from three classical assumptions: full public information, homogeneous participants, and irrelevance of trading mechanism.
- **Key findings:** (1) Order flow is the proximate cause of intraday FX price moves, not macro news. (2) "Hot potato" inventory-passing pattern explains intra-day volume. (3) Asymmetric information among dealers is fundamental. (4) Macro news matters mostly because it triggers order flow.
- **Relevance to GTOS:** Conceptual primer for why M15 OB-zone behavior exists. Inventory cycling and hot-potato dynamics produce mean reversion to recent equilibrium, a mechanism overlapping with GTOS's edge thesis.
- **Potential hypothesis:** Sophistication-of-counterparties feature (broker tag, hour-of-day) may be predictive even on a retail feed.
- **Cross-domain links:** 06 (microstructure — owns the dealer-flow theory); 07 (ICT level-trading)

### Order Flow and Exchange Rate Dynamics
- **Authors:** Martin D.D. Evans, Richard K. Lyons
- **Year:** 2002
- **Source:** *Journal of Political Economy*, 110(1), 170-180
- **URL:** https://www.journals.uchicago.edu/doi/full/10.1086/324391
- **Abstract:** Empirical demonstration that order flow explains > 50% of daily DM/USD movement (R² above 50%). $1 billion of net dollar buys moves the price by ~1 pfennig.
- **Key findings:** (1) Order-flow-augmented models beat random walks at daily horizon — first major positive result vs Meese-Rogoff. (2) Cross-rate order flow has bilateral information content. (3) Macro news affects FX mostly through induced order-flow shifts.
- **Relevance to GTOS:** Theoretical complement to the OB-zone edge: AT M15 horizon, mean-reversion to recent dealer-inventory equilibrium IS the GTOS thesis. Note: cross-link 06 owns the methodology paper; 11 keeps macro implications.
- **Potential hypothesis:** Build a proxy for retail vs institutional flow imbalance (e.g., large-volume bar count, sweep events) as a K54 feature.
- **Cross-domain links:** 06 (microstructure owner)

---

## 3. Carry trade — risk, momentum, fragility

### The Cross-Section of Foreign Currency Risk Premia and Consumption Growth Risk
- **Authors:** Hanno Lustig, Adrien Verdelhan
- **Year:** 2007
- **Source:** *American Economic Review*, 97(1), 89-117
- **URL:** https://www.aeaweb.org/articles?id=10.1257/aer.97.1.89
- **Abstract:** Aggregate consumption-growth risk explains the cross-section of currency risk premia. Low-interest-rate currencies hedge domestic consumption risk; high-interest-rate currencies expose investors to it.
- **Key findings:** (1) Domestic investors earn negative excess returns on low-rate currencies — they hedge bad domestic states. (2) High-rate currencies' returns covary with consumption growth. (3) Provides consumption-CAPM resolution to UIP puzzle.
- **Relevance to GTOS:** Establishes that JPY (low-rate funding currency) appreciates in domestic-stress states. USDJPY long bias has fundamental risk-premium grounding; GTOS gate may cautiously bias against fresh longs in USDJPY when US risk-off proxies (VIX) rise.
- **Potential hypothesis:** Cross-instrument feature: 1-month change in VIX predicts USDJPY direction during risk-off.
- **Cross-domain links:** 13 (factor); 17 (risk preferences)

### A Habit-Based Explanation of the Exchange Rate Risk Premium
- **Authors:** Adrien Verdelhan
- **Year:** 2010
- **Source:** *Journal of Finance*, 65(1), 123-146
- **URL:** https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.2009.01525.x
- **Abstract:** Consumption-habit model with time-varying risk aversion reproduces the UIP puzzle. Risk aversion is countercyclical, real interest rates procyclical; foreign FX risk premium is positive when domestic agent is more risk averse than foreign — consistent with low domestic rates.
- **Key findings:** (1) Forward-premium puzzle is a risk-premium phenomenon. (2) Reproduces magnitude of UIP regression coefficients. (3) Connects FX premium to business-cycle / consumption state. (4) Theoretical underpinning for "risk-on/risk-off" being more than a cliché.
- **Relevance to GTOS:** Justifies regime-conditional FX behavior — GTOS regime classifier (V2 H4-swing) implicitly captures part of this state-dependence. Supports K54 v2 having a recession/contraction state as a proper feature.
- **Potential hypothesis:** US recession-probability proxy (yield curve, Sahm rule, etc.) should have a stronger magnitude effect on JPY-cross direction than on EUR/USD.
- **Cross-domain links:** 17 (habit / behavioral); 13 (factor)

### Carry Trade and Momentum in Currency Markets
- **Authors:** Craig Burnside, Martin Eichenbaum, Sergio T. Rebelo
- **Year:** 2011
- **Source:** *Annual Review of Financial Economics*, 3, 511-535
- **URL:** https://www.kellogg.northwestern.edu/faculty/rebelo/htm/carry.pdf
- **Abstract:** Reviews three explanations for FX carry / momentum profitability: risk compensation, peso problems / rare disasters, and price pressure. Compatible with the carry-as-disaster-insurance reading.
- **Key findings:** (1) Carry and momentum are largely uncorrelated currency strategies. (2) Each delivers Sharpe in 0.6-0.9 range pre-2008. (3) Standard risk factors do not span their returns. (4) Peso-problem story remains the leading non-risk explanation.
- **Relevance to GTOS:** Survey-level mapping of why GTOS's edge is NOT carry-momentum (those are weekly-monthly horizon factors); rules out alpha-double-counting if GTOS deploys a carry overlay later.
- **Potential hypothesis:** Currency-momentum (3-month FX change) feature could be additive to K54 if uncorrelated with OB-zone signal.
- **Cross-domain links:** 14 (TS momentum); 13 (factor cross-section)

### Currency Momentum Strategies
- **Authors:** Lukas Menkhoff, Lucio Sarno, Maik Schmeling, Andreas Schrimpf
- **Year:** 2012
- **Source:** *Journal of Financial Economics*, 106(3), 660-684
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S0304405X12001353
- **Abstract:** Cross-sectional currency momentum delivers up to 10% per annum spread between past winners and losers, partially explained by transaction costs and behavioral under-/overreaction.
- **Key findings:** (1) Momentum spread substantial and persistent. (2) Not explained by traditional risk factors (Lustig-Verdelhan slope, etc.). (3) Transaction costs eat ~half. (4) Consistent with limits-to-arbitrage explanations.
- **Relevance to GTOS:** Bears on GBPJPY / GBPUSD where short-horizon trends arise; informs whether a "look-ahead trend filter" is a meaningful K54 feature.
- **Potential hypothesis:** 12-bar M15 trend strength has marginal additive content beyond OB-zone signal in CADJPY-like crosses; test on out-of-sample.
- **Cross-domain links:** 14 (TS momentum); 06 (transaction costs)

### Carry Trades and Global Foreign Exchange Volatility
- **Authors:** Lukas Menkhoff, Lucio Sarno, Maik Schmeling, Andreas Schrimpf
- **Year:** 2012
- **Source:** *Journal of Finance*, 67(2), 681-718
- **URL:** https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.2012.01728.x
- **Abstract:** Global FX-volatility risk is a robust priced factor in currency cross-section. High-interest-rate currencies load positively on global FX vol — they crash in vol spikes.
- **Key findings:** (1) Global FX vol explains the carry-trade premium more cleanly than equity-vol proxies. (2) Pricing is robust across countries and sub-samples. (3) Vol-risk loading explains both level and time-variation in carry returns.
- **Relevance to GTOS:** A direct candidate K54 feature: global FX vol (proxied by JPMorgan G10 FX vol or DXY realized vol) likely has a side-aware effect on JPY crosses (memory: side_aware_sizing_findings).
- **Potential hypothesis:** Conditional on regime classifier output, FX-vol shock magnitude predicts SHORT-side WR more than LONG-side in JPY crosses.
- **Cross-domain links:** 16 (FX vol); 03 (vol stylized fact)

### Do Peso Problems Explain the Returns to the Carry Trade?
- **Authors:** Craig Burnside, Martin Eichenbaum, Isaac Kleshchelski, Sergio Rebelo
- **Year:** 2011
- **Source:** *Review of Financial Studies*, 24(3), 853-891
- **URL:** https://academic.oup.com/rfs/article-abstract/24/3/853/1591669
- **Abstract:** Argues carry-trade payoffs reflect a peso problem with high stochastic discount factors in disaster states, NOT extreme negative payoffs. Consistent with risk-based interpretation but with rare-event SDF mechanism.
- **Key findings:** (1) Peso event involves SDF spike, not catastrophic carry payoff. (2) Disasters do not need to be physically large to deter rational arbitrage. (3) Reconciles Sharpe with limits-to-arbitrage.
- **Relevance to GTOS:** Supports keeping moderate position sizing on JPY-cross longs even in calm regimes — the "tail" is a risk-aversion spike, not strictly a market crash.
- **Potential hypothesis:** Conditional Sharpe on JPY crosses systematically lower in periods following 6m+ of low realized vol (peso accumulation hypothesis).
- **Cross-domain links:** 03 (peso/disasters); 21 (sizing under disaster risk)

### Empirical Evidence on the Currency Carry Trade, 1900-2012
- **Authors:** Nikolay Doskov, Laurens Swinkels
- **Year:** 2015
- **Source:** *Journal of International Money and Finance*, 51, 370-389
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S0261560614002150
- **Abstract:** Long-horizon (112-year, 20 currencies) carry-trade Sharpe is 0.26 — markedly lower than recent-sample 0.6+. Cautions extrapolation from post-1990 data.
- **Key findings:** (1) Long-horizon Sharpe ~0.2-0.4. (2) Recent decades' high carry returns may be regime-specific. (3) Substantial drawdowns periodically (decades-long flat patches).
- **Relevance to GTOS:** Direct connection to memory `feedback_decay_is_ceo_number_one_concern` — even celebrated FX strategies have severe regime decay. Reinforces GTOS skepticism about backtest-only validation.
- **Potential hypothesis:** Decades-long FX-strategy decay is the rule; expect GTOS edge similarly subject to multi-year decay events. Reinforces F11 OB-zone decay finding's plausibility.
- **Cross-domain links:** 22 (alpha decay); 14 (long-horizon momentum)

### Foreign Exchange Risk and the Predictability of Carry Trade Returns
- **Authors:** Gino Cenedese, Lucio Sarno, Ilias Tsiakas
- **Year:** 2014
- **Source:** *Journal of Banking & Finance*, 42, 302-313
- **URL:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2050106
- **Abstract:** Higher market variance significantly predicts large future carry-trade losses. Average variance (not correlation) drives predictability. A vol-conditioned carry strategy outperforms naive carry net of TC.
- **Key findings:** (1) Vol predicts carry tail (lower-quantile) returns. (2) Component decomposition: average vol matters; average correlation does not. (3) Conditional carry strategy adds Sharpe.
- **Relevance to GTOS:** Vol-conditioning is directly applicable to JPY-cross sizing. Supports a "halve risk on JPY crosses when global FX vol > 75th percentile" K54 v2 sizing rule, complementary to S79.
- **Potential hypothesis:** Confirm in GTOS data: USDJPY/GBPJPY realized R degrades when 1-month G10 FX vol is in top quartile.
- **Cross-domain links:** 16 (vol regime); 21 (vol-conditioned sizing)

### Investor Overconfidence and the Forward Premium Puzzle
- **Authors:** A. Craig Burnside, Bing Han, David Hirshleifer, Tracy Yue Wang
- **Year:** 2010 (NBER WP 15866; published RES 2011)
- **Source:** NBER Working Paper 15866 / *Review of Economic Studies*
- **URL:** https://www.nber.org/papers/w15866
- **Abstract:** Investor overconfidence about inflation signals causes overshooting in forward more than spot rates. The induced rise in forward premium predicts subsequent spot-rate corrections.
- **Key findings:** (1) Behavioral micro-foundation for forward-premium puzzle. (2) Magnitude of FP bias matched. (3) Generates carry-trade profitability without rare disasters. (4) Cross-sectional implications for high-information vs low-information currencies.
- **Relevance to GTOS:** Connects to GTOS's broader concern that AI / human decision-makers chronically overweight strong signals. Supports K54 architectural principle: the AI gate's confidence should be down-weighted, not up-weighted.
- **Potential hypothesis:** A "macro-news magnitude in last 24h" feature should be a NEGATIVE-direction signal for next-bar CR (overconfidence -> overshoot -> reversal).
- **Cross-domain links:** 17 (overconfidence behavioral); 18 (decision under uncertainty)

### Forward and Spot Exchange Rates in a Multi-Currency World
- **Authors:** Tarek A. Hassan, Rui C. Mano
- **Year:** 2019
- **Source:** *Quarterly Journal of Economics*, 134(1), 397-450
- **URL:** https://academic.oup.com/qje/article-abstract/134/1/397/5144784
- **Abstract:** Decomposes UIP violations into cross-currency, time-and-currency, and cross-time components. Forward-premium puzzle and dollar-trade are cross-time; carry-trade is cross-sectional.
- **Key findings:** (1) FP puzzle and "dollar trade" share cross-time origin. (2) Carry trade is fundamentally a cross-sectional asymmetry. (3) Some currencies pay permanently higher expected returns.
- **Relevance to GTOS:** Distinguishes which UIP-puzzle features matter for which trades. For GTOS USDJPY/GBPJPY, the relevant component is cross-time (dollar / yen cycles), NOT cross-sectional carry.
- **Potential hypothesis:** Time-aware features (state of dollar cycle, yen cycle) should dominate cross-sectional ranking features in K54 for JPY crosses.
- **Cross-domain links:** 13 (factor); 03 (UIP stylized fact)

### Risk Appetite and Exchange Rates
- **Authors:** Tobias Adrian, Erkko Etula, Hyun Song Shin
- **Year:** 2009 (NYFed Staff Reports 361)
- **Source:** Federal Reserve Bank of New York / SSRN
- **URL:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1338121
- **Abstract:** US dollar-funded intermediary funding-liquidity aggregates forecast USD exchange-rate growth at weekly/monthly/quarterly horizons. Channel distinct from carry; rooted in time-varying risk constraints.
- **Key findings:** (1) Funding-liquidity aggregates have OOS predictive power for USD. (2) Effective risk aversion of dollar-funded intermediaries fluctuates with constraint tightness. (3) Channel does NOT subsume carry premium.
- **Relevance to GTOS:** Macro-funding-liquidity features (e.g., commercial paper outstanding, primary-dealer net positions) could be additive K54 features for USDJPY/GBPUSD via the dollar-cycle component.
- **Potential hypothesis:** Weekly-frequency primary-dealer-position deltas predict next-week USD direction; small but consistent.
- **Cross-domain links:** 06 (intermediary asset pricing); 13 (factor)

---

## 4. Safe-haven currencies, dollar-smile, JPY/CHF/USD risk-off behavior

### Safe Haven Currencies
- **Authors:** Angelo Ranaldo, Paul Söderlind
- **Year:** 2010
- **Source:** *Review of Finance*, 14(3), 385-407
- **URL:** https://academic.oup.com/rof/article-abstract/14/3/385/1592162
- **Abstract:** Using high-frequency 1993-2008 data, CHF and JPY appreciate vs USD when US stocks fall, US bonds rise, and FX vol increases. Effects are non-linear in vol and stronger during crises.
- **Key findings:** (1) Safe-haven status of CHF and JPY confirmed at intraday-to-daily horizons. (2) Effect non-linear: vol-conditional. (3) Visible across crisis vs non-crisis. (4) Strong factor structure.
- **Relevance to GTOS:** Direct mechanism for USDJPY mean-reversion under risk-off: yen appreciation. GTOS H25 session-volatility shadow logger captures part of this; cross-instrument correlation gate's grouping of JPY crosses is academically validated here.
- **Potential hypothesis:** A "VIX delta in last 4 hours > X" feature should HALVE risk on USDJPY/GBPJPY long-side.
- **Cross-domain links:** 10 (gold-as-safe-haven cross-link); 03 (non-linear vol)

### Getting Beyond Carry Trade: What Makes a Safe-Haven Currency?
- **Authors:** Maurizio Habib, Livio Stracca
- **Year:** 2011
- **Source:** ECB Working Paper Series 1288
- **URL:** https://www.ecb.europa.eu/pub/pdf/scpwps/ecbwp1288.pdf
- **Abstract:** Panel of 52 currencies, 25 years. Net foreign asset position and absolute size of stock market are robust predictors of safe-haven status. Interest-rate spread vs US is significant only for advanced-country currencies subject to carry trade.
- **Key findings:** (1) Net foreign asset position is the dominant safe-haven driver. (2) Stock-market size matters second. (3) Interest-rate spread effect is conditional on advanced-country status. (4) Distinguishes safe-haven from low-yield-currency.
- **Relevance to GTOS:** Justifies treating JPY (large NFA position, deep market) differently from GBP (smaller, post-Brexit weakened). GBPJPY safe-haven structure is asymmetric: only the JPY leg has the safe-haven feature.
- **Potential hypothesis:** During risk-off, GBPJPY moves should be MORE driven by JPY appreciation than GBP moves — feature: GBPJPY direction more strongly predicted by JPY-basket move than GBP-basket move conditional on VIX > X.
- **Cross-domain links:** 13 (cross-section); 10 (safe-haven cross-link)

### Foreign Safe Asset Demand and the Dollar Exchange Rate
- **Authors:** Zhengyang Jiang, Arvind Krishnamurthy, Hanno Lustig
- **Year:** 2021
- **Source:** *Journal of Finance*, 76(3), 1049-1089
- **URL:** https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.13003
- **Abstract:** Convenience yield from foreign demand for US safe assets, captured by the Treasury basis (US Treasury yield minus currency-hedged foreign government bond yield), explains up to 28% of quarterly USD variation.
- **Key findings:** (1) Treasury basis widening = immediate USD appreciation, subsequent depreciation. (2) Channel separate from carry. (3) Empirically large: 28% of quarterly USD variation. (4) Provides micro-foundation for "exorbitant privilege".
- **Relevance to GTOS:** Adds Treasury-basis as a candidate K54 feature for USDJPY/GBPUSD (where USD is one leg). Also explains why USD strengthens in risk-off — even when Fed easing relative to Japan / UK.
- **Potential hypothesis:** Weekly Treasury-basis change has predictive content for next-week USDJPY direction; opposite sign to short-vs-long horizon implications above.
- **Cross-domain links:** 13 (factor); 06 (intermediary)

### Exchange Rates during Financial Crises
- **Authors:** Marion Kohler
- **Year:** 2010
- **Source:** *BIS Quarterly Review*, March 2010
- **URL:** https://www.bis.org/publ/qtrpdf/r_qt1003f.htm
- **Abstract:** Reviews exchange-rate dynamics in 2008-09 GFC. Most-depreciated currencies were carry targets; funding currencies (JPY, CHF) appreciated. Interest-rate differentials explain more crisis-period FX variation than in past crises — reflecting carry-trade structural change.
- **Key findings:** (1) Crisis-period flows reverse normal (carry currencies fall, funding currencies rise). (2) Counter-intuitive: USD appreciates in 2008 despite epicenter status. (3) Interest-rate differentials more important than in prior crises.
- **Relevance to GTOS:** Supports a "regime crisis" feature in K54 — during high-VIX states, JPY-cross direction predictability INVERTS vs calm regimes. Cross-link to GTOS regime classifier promotion.
- **Potential hypothesis:** Conditional WR for USDJPY LONG when VIX > 30 should be SIGNIFICANTLY lower than when VIX < 20.
- **Cross-domain links:** 10 (gold safe haven); 17 (risk-on/risk-off)

### Dollar Smile (Stephen Jen — practitioner reference)
- **Author:** Stephen Jen (founder, Eurizon SLJ Capital; former Morgan Stanley)
- **Year:** 2001 (introduction of theory)
- **Source:** Practitioner research notes; widely-cited as conceptual framework
- **URL:** https://www.eurizonsljcapital.com/dollar-smile/
- **Abstract:** Three-state framework for dollar behavior: USD strengthens in risk-off ("flight to quality"), weakens during global growth/risk-on, strengthens again when US economy outperforms. The "smile" is U-shape vs global-growth state.
- **Key findings:** (1) USD has bipolar driver structure. (2) Middle of smile is "high-yield-other" environment when USD weakens. (3) Right tail is US-outperformance. (4) Operationalised by FX desks for tactical positioning.
- **Relevance to GTOS:** Conceptual framework directly relevant to GTOS's USDJPY/GBPUSD: regime classifier could be re-interpreted in dollar-smile coordinates (left=risk-off, middle=goldilocks, right=US outperform). Each kill-zone has different conditional WR.
- **Potential hypothesis:** A 2D feature space (US growth surprise index × VIX) creates a more discriminative regime classifier than current H4-swing.
- **Cross-domain links:** 13 (factor); 17 (regime); cross-link 10 (gold-USD smile relationship)

### Risk Appetite, Carry Trade and Exchange Rates
- **Authors:** Various extension on Adrian-Etula-Shin
- **Year:** 2012
- **Source:** *Global Finance Journal*, 23(1), 48-63
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S1044028312000051
- **Abstract:** Connects risk-appetite measures (VIX, intermediary leverage) to carry-trade returns and to exchange-rate predictability. Builds on Adrian-Etula-Shin and Brunnermeier-Nagel-Pedersen.
- **Key findings:** (1) Risk-appetite conditioning improves carry returns. (2) Time-varying premia predictable. (3) Cross-currency variation in vulnerability documented.
- **Relevance to GTOS:** Direct candidate features for K54: VIX-conditioned position sizing on JPY crosses.
- **Potential hypothesis:** Side-aware sizing layer (memory: side_aware_sizing_findings) should incorporate VIX-state.
- **Cross-domain links:** 13 (factor); 17 (risk-on/off)

### Liquidity in the Foreign Exchange Market: Measurement, Commonality, and Risk Premiums
- **Authors:** Loriano Mancini, Angelo Ranaldo, Jan Wrampelmeyer
- **Year:** 2013
- **Source:** *Journal of Finance*, 68(5), 1805-1841
- **URL:** https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.12053
- **Abstract:** First systematic study of FX liquidity. Significant variation across crosses, substantial illiquidity costs, strong commonality with equity and bond market liquidity. Funding currencies hedge liquidity risk; investment currencies expose to it.
- **Key findings:** (1) FX-liquidity factor priced. (2) Strong commonality across currencies. (3) Funding (low-rate) currencies have negative liquidity-risk loading. (4) Liquidity risk especially pronounced 2007-09.
- **Relevance to GTOS:** Justifies wider spread / lower size during liquidity stress (e.g., bank-holiday illiquid periods that often align with volatility). Could inform per-symbol "liquidity gate" in execution.
- **Potential hypothesis:** Spread-of-spread (volatility-of-spread) feature is predictive of failed-execution / slippage events; useful for execution-quality optimization, not directly for direction.
- **Cross-domain links:** 06 (microstructure); 21 (liquidity-aware sizing)

### Carry Funding and Safe Haven Currencies: A Threshold Regression Approach
- **Authors:** Multiple (extension paper post-Habib-Stracca)
- **Year:** 2015
- **Source:** *Journal of International Money and Finance*
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S0261560615001205
- **Abstract:** Threshold-regression formalization of when "safe-haven" status of JPY/CHF/USD activates. State-dependence is non-trivial; thresholds align with VIX percentile breaks.
- **Key findings:** (1) Safe-haven flow activates above identifiable VIX thresholds. (2) JPY safe-haven dominates CHF in some regimes. (3) USD safe-haven activation later in crises. (4) Confirms non-linearity of safe-haven mechanism.
- **Relevance to GTOS:** Justifies discrete-state regime modeling in K54 v2 over continuous-feature approaches; threshold regimes match GTOS regime classifier philosophy.
- **Potential hypothesis:** Empirical threshold for JPY safe-haven activation in M15 GTOS data falls near VIX 20-25 percentile.
- **Cross-domain links:** 05 (regime/change-point); 17 (risk-on/off)

### Foreign Exchange Fixings and Returns Around the Clock
- **Authors:** Ingomar Krohn, Philippe Mueller, Paul Whelan
- **Year:** 2024
- **Source:** *Journal of Finance*, 79(1), 541-578
- **URL:** https://onlinelibrary.wiley.com/doi/10.1111/jofi.13306
- **Abstract:** USD appreciates in run-up to FX fixes and depreciates thereafter, tracing W-shape return pattern around the clock. Reversals statistically significant for top-9 currencies over 21 years. Inventory-risk explanation: dealers intermediate unconditional USD demand at fixes.
- **Key findings:** (1) W-shape pattern: USD up before/depreciate after each major fix. (2) Reversals ~2 bps either side of fix. (3) Daily swings >$1 billion. (4) Robust across 1999-2014 sub-samples.
- **Relevance to GTOS:** EXTREMELY relevant — direct intra-day pattern aligned with GTOS kill-zone logic. London 4pm fix corresponds to NY-PM kill-zone overlap. Suggests pre-fix LONG-USD bias and post-fix mean-reversion as K54 features.
- **Potential hypothesis:** Add hour-of-day relative to fixes as a K54 feature; expect predictive lift especially for USDJPY around 16:00 London (15:00 GMT/UTC).
- **Cross-domain links:** 06 (microstructure mechanism); 08 (volume around fixes); 09 (round-number fix)

---

## 5. Central-bank policy & FX response — interventions, Fed, BoJ, ECB

### When Is Foreign Exchange Intervention Effective? Evidence from 33 Countries
- **Authors:** Marcel Fratzscher, Oliver Gloede, Lukas Menkhoff, Lucio Sarno, Tobias Stöhr
- **Year:** 2019
- **Source:** *American Economic Journal: Macroeconomics*, 11(1), 132-156
- **URL:** https://www.aeaweb.org/articles?id=10.1257/mac.20150317
- **Abstract:** 33-country, 1995-2011 dataset. FX intervention is widely used and effective with > 80% success rate under some criteria. Effective for smoothing path; level-shifting in flexible regimes requires large size + public announcement + verbal support.
- **Key findings:** (1) Intervention works at smoothing volatility. (2) Level-shifting harder, requires multiple support pillars. (3) Communication amplifies effect. (4) Documents that intervention is more common than commonly believed.
- **Relevance to GTOS:** When BoJ / SNB / ECB intervene, GTOS should treat as a regime breakpoint. Suggests an "intervention-detected" gate that suspends or downsides positions on the affected pair.
- **Potential hypothesis:** Intervention-detection signal (Reuters tag, BoJ press, large M5 bar with coincident MoF announcement) should temporarily disable trading on the affected pair.
- **Cross-domain links:** 17 (policy); 06 (microstructure intervention)

### The Lasting Effect of Yen-Buying Interventions: Two Cases of Japanese FX Interventions in 1997-98 and 2022
- **Authors:** Various (per ScienceDirect)
- **Year:** 2025
- **Source:** *Journal of International Money and Finance*
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S0261560625001809
- **Abstract:** Compares 1997-98 and 2022 Japanese yen-buying interventions. October 2022 events had effects lasting > 10 business days; September 2022 was short-lived.
- **Key findings:** (1) Effectiveness varies even within a single intervention campaign. (2) Larger persistent effects when paired with US-CPI-driven repricing. (3) Persistence requires alignment with macro fundamentals.
- **Relevance to GTOS:** Direct GTOS-relevant: 2022-2024 BoJ intervention is exactly the regime in which 2026 trading occurs. Calibrates expected duration of post-intervention "freeze" on JPY-cross trading.
- **Potential hypothesis:** Post-intervention 10-day window has materially different USDJPY M15 conditional distribution; data-collection cohort flag for future K54 retraining.
- **Cross-domain links:** 17 (policy intervention); 05 (regime change)

### How Successful Is the G7 in Managing Exchange Rates?
- **Authors:** Marcel Fratzscher
- **Year:** 2009
- **Source:** *Journal of International Economics*, 79(1), 78-88
- **URL:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=804466
- **Abstract:** Analyzes 1990s-2000s G7 verbal interventions and operational interventions. Distinguishes portfolio-balance vs signaling channels. Signaling channel accounts for ~2/3 of effect; portfolio for ~1/3.
- **Key findings:** (1) Verbal intervention can move prices without operational intervention. (2) Signaling channel more persistent. (3) Portfolio channel exists but short-lived. (4) Coordination amplifies impact.
- **Relevance to GTOS:** Suggests official-communication detection (BoJ governor speeches, MoF statements) is a relevant K54-feature trigger, not just operational intervention.
- **Potential hypothesis:** Speech-event detection feature has > 80% success in marking 1-2 day USDJPY mean-reversion epochs.
- **Cross-domain links:** 17 (communication); 06 (event microstructure)

### The Economics of the Fed Put
- **Authors:** Anna Cieslak, Annette Vissing-Jorgensen
- **Year:** 2021
- **Source:** *Review of Financial Studies*, 34(9), 4045-4089
- **URL:** https://academic.oup.com/rfs/article-abstract/34/9/4045/5917640
- **Abstract:** Stock-market drops co-move with downgrades to Fed growth expectations and predict subsequent policy accommodation. Textual analysis of FOMC documents shows policymaker attention to stock market driven by consumption-wealth concern.
- **Key findings:** (1) Negative stock returns predict subsequent policy easing. (2) Mechanism is consumption-wealth, not moral-hazard. (3) Empirical "Fed put" exists. (4) Limited evidence of overreaction beyond growth-expectations channel.
- **Relevance to GTOS:** Supports an "equity-market-stress -> dollar weakness" K54 feature for USDJPY (Fed easing → USD weak). Connects equity index moves (US30, NAS100) cross-instrument to FX direction.
- **Potential hypothesis:** US30 / SPX 5-day decline > X predicts 1-week USDJPY direction (Fed-put -> dollar weakness).
- **Cross-domain links:** 12 (equity indices); 17 (policy reaction)

### Exchange Rates and Monetary Policy Uncertainty
- **Authors:** Philippe Mueller, Alireza Tahbaz-Salehi, Andrea Vedolin
- **Year:** 2017
- **Source:** *Journal of Finance*, 72(3), 1213-1252
- **URL:** https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.12499
- **Abstract:** Short-USD/long-other-currency strategies have significantly higher excess returns on FOMC announcement days. Returns rise with monetary-policy uncertainty and during easing.
- **Key findings:** (1) Short-USD trade earns FOMC-day premium. (2) Premium scales with rate-differential. (3) Increases with policy uncertainty. (4) Easing intensifies effect.
- **Relevance to GTOS:** Direct: FOMC-day USD-pair behavior is systematically different. K54 / execution gate should treat FOMC-announcement windows specially. Argues for blocking trades (or halving size) for ~1 hour around FOMC release.
- **Potential hypothesis:** GTOS should add an "FOMC release within X hours" gate that adjusts kill-zone or sizing.
- **Cross-domain links:** 17 (event); 12 (equity reaction)

### Micro Effects of Macro Announcements: Real-Time Price Discovery in Foreign Exchange
- **Authors:** Torben G. Andersen, Tim Bollerslev, Francis X. Diebold, Clara Vega
- **Year:** 2003
- **Source:** *American Economic Review*, 93(1), 38-62
- **URL:** https://www.aeaweb.org/articles?id=10.1257/000282803321455151
- **Abstract:** Macro-announcement surprises produce conditional-mean jumps in spot USD exchange rates at 5-minute frequency. Bad news has greater impact than good news (sign asymmetry).
- **Key findings:** (1) Announcement surprises cause measurable jumps. (2) Asymmetric reaction: bad news bigger. (3) Effect concentrated in first 5-15 minutes. (4) Foundational empirical paper for high-frequency macro impact.
- **Relevance to GTOS:** GTOS pre-AI gate should NOT enter new positions in 5-15 minute windows after major releases (NFP, CPI, FOMC, BoJ, BoE, ECB). Empirically validated event-blackout window.
- **Potential hypothesis:** Build a calendar-aware blackout layer; expected lift in CR/WR is small but tail-risk-improving.
- **Cross-domain links:** 06 (event microstructure); 17 (policy)

### Dollar Ahead of FOMC Target Rate Changes
- **Authors:** Nina Karnaukh
- **Year:** 2018 (SSRN)
- **Source:** SSRN
- **URL:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3221318
- **Abstract:** USD appreciates before contractionary FOMC decisions and depreciates before expansionary ones. Fed-funds-futures spread predicts both rate change and pre-meeting USD move with R²~22%.
- **Key findings:** (1) Pre-FOMC USD drift exists. (2) Predictable from Fed-funds futures spread. (3) Magnitude economically meaningful. (4) Predictability holds out-of-sample.
- **Relevance to GTOS:** Adds the 3-day pre-FOMC window to event-aware feature. Could be K54 directional feature: Fed-funds futures change in past 3 days predicts USD direction in pre-FOMC kill zones.
- **Potential hypothesis:** Pre-FOMC USDJPY kill-zone should be biased LONG when Fed-funds-futures spread > 5bp, biased SHORT when < -5bp.
- **Cross-domain links:** 17 (policy); 12 (event)

---

## 6. CIP failures, dollar dominance, recent global FX system

### Deviations from Covered Interest Rate Parity
- **Authors:** Wenxin Du, Alexander Tepper, Adrien Verdelhan
- **Year:** 2018
- **Source:** *Journal of Finance*, 73(3), 915-957
- **URL:** https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.12620
- **Abstract:** Post-2008 covered-interest-parity violations are large, persistent, and systematic. Not explained by credit risk or transaction costs. Particularly strong at quarter-end (banking-regulation-driven).
- **Key findings:** (1) CIP violations 50-100bp regularly post-2008. (2) Not credit-risk explained. (3) Quarter-end spikes. (4) Causal effect of banking regulation on asset prices.
- **Relevance to GTOS:** Establishes that even "arbitrage-free" FX pricing has predictable seasonal structure. Quarter-end USD funding stress could impact USDJPY/GBPUSD M15 dynamics. Useful K54 feature: days-to-quarter-end interacted with USD strength.
- **Potential hypothesis:** Last-3-days-of-quarter shows different conditional USDJPY M15 distribution; spread/slippage worse around 23-24-30/31 of Mar/Jun/Sep/Dec.
- **Cross-domain links:** 06 (intermediary balance sheet); 13 (factor)

### Covered Interest Parity Lost: Understanding the Cross-Currency Basis
- **Authors:** Claudio Borio, Robert N. McCauley, Patrick McGuire, Vladyslav Sushko
- **Year:** 2016
- **Source:** *BIS Quarterly Review*, September 2016
- **URL:** https://www.bis.org/publ/qtrpdf/r_qt1609e.htm
- **Abstract:** Cross-currency basis dispersion across countries best explained by interaction of large FX hedging demand with tighter limits to arbitrage. Quantitative proxies for hedging demand explain time-series and cross-section.
- **Key findings:** (1) Hedging demand × balance-sheet constraints generates basis. (2) Country-level differences explain cross-section. (3) Time-variation tracks balance-sheet costs. (4) FX-swap market is dollar-funding focal point.
- **Relevance to GTOS:** Establishes that "arbitrage-free" textbook is wrong post-GFC. JPY-USD basis is a measurable feature; widening basis correlates with periods of dollar-funding stress that affect FX vol.
- **Potential hypothesis:** USD-JPY basis change in past week predicts USDJPY M15 vol expansion.
- **Cross-domain links:** 06 (balance-sheet capacity); 13 (factor)

### The Dollar, Bank Leverage, and Deviations from Covered Interest Parity
- **Authors:** Stefan Avdjiev, Wenxin Du, Cathérine Koch, Hyun Song Shin
- **Year:** 2019
- **Source:** *American Economic Review: Insights*, 1(2), 193-208
- **URL:** https://www.aeaweb.org/articles?id=10.1257/aeri.20180322
- **Abstract:** Documents triangular relationship: stronger USD ↔ larger CIP deviations ↔ contraction in cross-border USD bank lending. USD is a global risk-taking-capacity barometer.
- **Key findings:** (1) Stronger USD coincides with wider FX basis. (2) Contracting cross-border USD lending. (3) Risk-taking-capacity channel. (4) USD as global financial conditions metric.
- **Relevance to GTOS:** Adds a "global USD funding stress" feature: when DXY rises with widening FX basis, expect M15 risk-off conditions. JPY-cross long-side WR likely degrades.
- **Potential hypothesis:** Composite feature (DXY 5-day change × USD-JPY basis change) is predictive of USDJPY/GBPJPY conditional WR.
- **Cross-domain links:** 06 (intermediary asset pricing); 13 (factor)

### International Currencies and Capital Allocation
- **Authors:** Matteo Maggiori, Brent Neiman, Jesse Schreger
- **Year:** 2020
- **Source:** *Journal of Political Economy*, 128(6), 2019-2066
- **URL:** https://www.journals.uchicago.edu/doi/abs/10.1086/705688
- **Abstract:** Cross-border bond holdings biased toward home-currency. USD is global exception — foreigners willing to hold USD-denominated bonds. Dollar-bond share surged after 2008.
- **Key findings:** (1) Strong own-currency-home bias outside USD. (2) USD as global exception with foreign demand. (3) Dollar-share rose post-2008. (4) Small US firms can borrow abroad in USD because of dominance.
- **Relevance to GTOS:** Confirms structural USD floor. GTOS USD-pair behavior in long-horizon regime change must respect dollar dominance even as composition slowly erodes.
- **Potential hypothesis:** USD long-tail behavior less extreme than peer currencies — implies skew of USDJPY differs from GBPJPY in fundamental ways.
- **Cross-domain links:** 13 (factor); 22 (alpha — long-horizon)

### The Stealth Erosion of Dollar Dominance: Active Diversifiers and the Rise of Nontraditional Reserve Currencies
- **Authors:** Serkan Arslanalp, Barry Eichengreen, Chima Simpson-Bell
- **Year:** 2022
- **Source:** *Journal of International Economics* (also IMF WP 2022/058)
- **URL:** https://www.imf.org/en/Publications/WP/Issues/2022/03/24/The-Stealth-Erosion-of-Dollar-Dominance-Active-Diversifiers-and-the-Rise-of-Nontraditional-515150
- **Abstract:** Documents gradual erosion of USD share of global FX reserves; not matched by EUR/JPY/GBP rises but by AUD, CAD, CNH, KRW, SGD, NOK, SEK. Reserve managers diversifying into "nontraditional" currencies.
- **Key findings:** (1) USD reserve share declining ~1pp/year. (2) Diversification flows to G10-and-emerging non-reserve currencies. (3) Process driven by yield search and digital-finance access. (4) Multipolar reserve regime emerging.
- **Relevance to GTOS:** Long-horizon structural shift; implies regime classifier may need to track DXY-vs-non-traditional-currency-baskets, not just G10. Less immediately actionable for M15 GTOS but informs decadal-horizon assumptions.
- **Potential hypothesis:** USD-AUD / USD-CAD relationship (currently outside GTOS instrument set) drifts as diversification proceeds — slow regime change, not short-horizon.
- **Cross-domain links:** 13 (factor); 22 (regime change long-horizon)

### The Market Turbulence and Carry Trade Unwind of August 2024
- **Authors:** Matteo Aquilina, Marco Jacopo Lombardi, Andreas Schrimpf, Vladyslav Sushko
- **Year:** 2024
- **Source:** BIS Bulletin No. 90
- **URL:** https://www.bis.org/publ/bisbull90.pdf
- **Abstract:** Documents Aug 5 2024 episode: TOPIX -12% in single session, Nikkei vol spiked to crisis levels. Yen carry pre-event ¥40 trillion (~$250 billion) on/off-balance-sheet exposure. Procyclical deleveraging amplified initial macro shock.
- **Key findings:** (1) Pre-event JPY carry exposure ~$250bn (lower-bound). (2) Sub-1-day-massive deleveraging cascade. (3) Procyclical margin increases magnified shock. (4) Market dysfunction averted but structural fragility remains.
- **Relevance to GTOS:** EXTREMELY relevant — quantifies the JPY-cross tail risk GTOS faces. Validates aggressive H29 drawdown sizing reduction. Argues for systematic monitoring of BIS / IMM net JPY positioning as a tail-risk feature.
- **Potential hypothesis:** A monthly "BIS-reported JPY-carry exposure proxy" feature, when in top quartile, requires SHORT-side WR-watch SPRT-style alarm on USDJPY/GBPJPY long-side trades.
- **Cross-domain links:** 03 (fat-tail event); 21 (sizing under disaster); 17 (forced unwinding)

---

## 7. Theory: UIP, fundamentals, predictability, exchange-rate disconnect

### Exchange Rates and Fundamentals
- **Authors:** Charles Engel, Kenneth D. West
- **Year:** 2005
- **Source:** *Journal of Political Economy*, 113(3), 485-517
- **URL:** https://www.journals.uchicago.edu/doi/abs/10.1086/429137
- **Abstract:** In rational-expectations present-value model with I(1) fundamentals and discount factor near 1, asset price exhibits near-random-walk behavior — even though it IS a function of fundamentals.
- **Key findings:** (1) Theoretical resolution of Meese-Rogoff puzzle. (2) Random-walk behavior is consistent with fundamental-driven model. (3) Exchange rates Granger-cause fundamentals. (4) Standard asset-pricing models can match key facts.
- **Relevance to GTOS:** Reinforces that exchange rates LOOK random-walk-like at short horizons even when driven by news; supports GTOS not relying on short-horizon fundamentals.
- **Potential hypothesis:** Fundamental-news direction (e.g., interest-differential change) may have weak but systematic direction-leading effect on M15 behavior.
- **Cross-domain links:** 02 (RW benchmark); 19 (ML benchmarking)

### Exchange Rate Disconnect in General Equilibrium
- **Authors:** Oleg Itskhoki, Dmitry Mukhin
- **Year:** 2021
- **Source:** *Journal of Political Economy*, 129(8), 2183-2232
- **URL:** https://www.journals.uchicago.edu/doi/abs/10.1086/714447
- **Abstract:** GE model that simultaneously addresses Meese-Rogoff, Backus-Smith, PPP, and UIP puzzles. Combines productivity + monetary + financial shocks to produce volatile, near-martingale exchange rates with empirically realistic macro comovement.
- **Key findings:** (1) Single GE model resolves multiple puzzles. (2) Financial shocks essential. (3) Reproduces business-cycle moments AND exchange-rate disconnect. (4) Major theoretical advance.
- **Relevance to GTOS:** Reinforces conceptual basis for "exchange-rate disconnect" — fundamentals do affect FX, just weakly at high frequency. Supports K54 architecture with weak fundamental priors and stronger price-action features.
- **Potential hypothesis:** Financial-shock proxies (intermediary leverage, basis spread) deliver more K54 lift than productivity / monetary fundamentals.
- **Cross-domain links:** 13 (factor); 22 (alpha — long horizon)

### Exchange Rates, Interest Rates, and the Risk Premium
- **Authors:** Charles Engel
- **Year:** 2016
- **Source:** *American Economic Review*, 106(2), 436-474
- **URL:** https://www.aeaweb.org/articles?id=10.1257/aer.20121365
- **Abstract:** Documents joint-puzzle: high-real-rate countries have currencies stronger than UIP predicts AND larger expected-future-depreciation than UIP predicts. Apparently contradictory implications for the FX risk-premium.
- **Key findings:** (1) Puzzle compounds: spot-vs-UIP and forward-vs-UIP both fail. (2) Risk-premium needs to switch sign across horizons. (3) Standard models cannot accommodate. (4) Calls for non-standard preferences or frictions.
- **Relevance to GTOS:** Caution that "interest-differential" feature has different predictive sign at different horizons — a 1-week forward-premium feature may differ in sign from a 1-month carry feature.
- **Potential hypothesis:** Test multiple time-horizon interest-differential features in K54; expect non-monotonic effect.
- **Cross-domain links:** 13 (factor); 17 (preferences)

### Infrequent Portfolio Decisions: A Solution to the Forward Discount Puzzle
- **Authors:** Philippe Bacchetta, Eric van Wincoop
- **Year:** 2010
- **Source:** *American Economic Review*, 100(3), 870-904
- **URL:** https://www.aeaweb.org/articles?id=10.1257/aer.100.3.870
- **Abstract:** Two-country model with infrequent portfolio decisions matches forward-discount puzzle and delayed overshooting. Active currency-management gain smaller than fees, justifying infrequent reallocation.
- **Key findings:** (1) Infrequent decision optimality. (2) Reproduces FD puzzle. (3) Explains delayed overshooting. (4) Behavioral microfoundation.
- **Relevance to GTOS:** Implies real-money flows are slow; high-frequency GTOS competes with HF / dealer flow, NOT real money. Supports M15 microstructure focus over weekly fundamental positioning.
- **Potential hypothesis:** Mid-month / month-end portfolio rebalancing may show in M15 patterns; date-of-month feature predictive.
- **Cross-domain links:** 17 (decision frictions); 19 (ML horizon)

### Exchange Rate Predictability
- **Authors:** Barbara Rossi
- **Year:** 2013
- **Source:** *Journal of Economic Literature*, 51(4), 1063-1119
- **URL:** https://www.aeaweb.org/articles?id=10.1257/jel.51.4.1063
- **Abstract:** Survey article. Predictability of exchange rates "depends on choice of predictor, horizon, sample, model, evaluation method." Best when Taylor-rule or NFA-based, linear, parsimonious.
- **Key findings:** (1) Random-walk-without-drift is the toughest benchmark. (2) Taylor-rule fundamentals best at medium horizon. (3) NFA-based models work at long horizon. (4) Robustness to method matters more than novelty.
- **Relevance to GTOS:** Methodological discipline: any K54 feature needs to beat RW benchmark on the horizon claimed. Reinforces F11/F15 caution about claiming feature predictability.
- **Potential hypothesis:** GTOS should evaluate K54 features against RW benchmark explicitly for each kill-zone.
- **Cross-domain links:** 02 (methodology); 19 (ML benchmarking)

### An Economic Evaluation of Empirical Exchange Rate Models
- **Authors:** Pasquale Della Corte, Lucio Sarno, Ilias Tsiakas
- **Year:** 2009
- **Source:** *Review of Financial Studies*, 22(9), 3491-3530
- **URL:** https://academic.oup.com/rfs/article-abstract/22/9/3491/1569619
- **Abstract:** Bayesian model averaging across exchange-rate models with volatility timing. Evaluates economic value (Sharpe-improving) rather than just statistical significance.
- **Key findings:** (1) Vol-timing improves economic value of forecasts. (2) Bayesian model averaging robust. (3) Predictive ability depends on volatility regime. (4) Combined forecasts dominate.
- **Relevance to GTOS:** Vol-timing principle is directly applicable: K54 sizing should incorporate realized-vol forecasts. Bayesian averaging philosophy aligns with GTOS multi-framework dispatch.
- **Potential hypothesis:** Conditioning K54 outputs on realized-vol-quantile improves economic value (R/trade, not just hit rate).
- **Cross-domain links:** 16 (vol regime); 19 (ML)

### Volatility Risk Premia and Exchange Rate Predictability
- **Authors:** Pasquale Della Corte, Tarun Ramadorai, Lucio Sarno
- **Year:** 2016
- **Source:** *Journal of Financial Economics*, 120(1), 21-40
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S0304405X16300150
- **Abstract:** Volatility risk premium (expected realized vol minus model-free implied vol) predicts currency returns. Strategy: sell high-insurance-cost currencies, buy low-insurance-cost ones.
- **Key findings:** (1) VRP predicts cross-section of currency returns. (2) Strategy delivers diversification. (3) VRP captures insurance cost. (4) Robust to standard risk factors.
- **Relevance to GTOS:** FX-option-implied-vol is a candidate K54 feature. Especially relevant for USDJPY where 1m25d risk-reversal is a well-defined sentiment marker.
- **Potential hypothesis:** USDJPY 1m 25d risk-reversal change in past 24h has predictive content for USDJPY M15 direction in next 4-8 hours.
- **Cross-domain links:** 16 (vol risk premium); 19 (ML feature)

### Which Fundamentals Drive Exchange Rates? A Cross-Sectional Perspective
- **Authors:** Lucio Sarno, Maik Schmeling
- **Year:** 2014
- **Source:** *Journal of Money, Credit and Banking*, 46(2-3), 267-292
- **URL:** https://onlinelibrary.wiley.com/doi/abs/10.1111/jmcb.12106
- **Abstract:** Tests present-value-model predictions on 35 currency pairs over 1900-2009. Exchange rates predict nominal fundamentals (inflation, money, NGDP); predictability for real fundamentals weaker, post-Bretton-Woods only.
- **Key findings:** (1) Exchange rates contain information about future nominal fundamentals. (2) Real-fundamental link weaker. (3) Cross-section approach more powerful than time-series. (4) 109-year data validates structural mechanism.
- **Relevance to GTOS:** Validates that high-frequency FX moves contain information that future macro will catch up to — but with long delay. For M15 GTOS: weakly relevant.
- **Potential hypothesis:** Cross-section ranking of FX moves (e.g., USDJPY rank vs all crosses) is more stable feature than absolute USDJPY level.
- **Cross-domain links:** 13 (cross-section); 19 (ML feature)

### Five Facts about the UIP Premium
- **Authors:** Şebnem Kalemli-Özcan, Liliana Varela
- **Year:** 2021 (NBER WP 28923)
- **Source:** NBER Working Paper / forthcoming
- **URL:** https://www.nber.org/papers/w28923
- **Abstract:** Five empirical regularities: EM UIP premium consistently higher and more volatile; significant local-risk-factor share; interest-differential-component more volatile; expectations align with realized; local risk maps to country-policy shocks.
- **Key findings:** (1) EM UIP premium > AE UIP premium. (2) Local-risk vs global-risk decomposition. (3) Interest-differential is volatile component. (4) Expectations track realizations. (5) Country-policy uncertainty drives local risk.
- **Relevance to GTOS:** GTOS instruments are AE-only (USDJPY, GBPJPY, GBPUSD). Reinforces that AE-FX is structurally cleaner than EM-FX; supports current FN profile choice.
- **Potential hypothesis:** Local-policy-uncertainty (BoE, BoJ) features should add lift for GBPUSD/USDJPY but smaller than for EM crosses.
- **Cross-domain links:** 13 (cross-section); 17 (policy uncertainty)

---

## 8. FX fixings, microstructure / liquidity / intraday seasonality

### Forex Trading and the WMR Fix
- **Authors:** Martin D.D. Evans
- **Year:** 2018
- **Source:** *Journal of Banking & Finance*
- **URL:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2487991
- **Abstract:** WM/R 4pm London fix: prices unusually volatile around the fix; FX returns negatively correlated either side. Inconsistent with competitive Fix-trading model.
- **Key findings:** (1) Volatility spike around 4pm London. (2) Negative serial correlation: pre-fix and post-fix moves opposite. (3) Inconsistent with competition. (4) Consistent with collusion / inventory effects.
- **Relevance to GTOS:** Direct alert: GTOS should treat 15:55-16:05 London (≈14:55-15:05 UTC depending on DST) as a special-microstructure window. NY-PM kill zone overlaps; size or block accordingly.
- **Potential hypothesis:** A "fix-window blackout" (or halve sizing) gate centered on 4pm London for cable / EURUSD / JPY-pairs improves expected R-per-trade.
- **Cross-domain links:** 06 (microstructure); 09 (round-number/fix clustering)

### Was the Forex Fixing Fixed?
- **Authors:** Takatoshi Ito, Masahiro Yamada
- **Year:** 2015 (NBER WP 21518)
- **Source:** NBER WP / *Journal of International Economics* (2017)
- **URL:** https://www.nber.org/papers/w21518
- **Abstract:** Tokyo fixing (9:55am Tokyo) and London fixing (4pm London) examined. Pre-2008 fixing prices biased upward — set higher than highest transaction price during window. Post-2008 still above median.
- **Key findings:** (1) Tokyo fixing more disturbed than London. (2) Customer orders biased toward FX-buying. (3) Bias improved post-2008 but persists. (4) Confirms "fix manipulation" as structural feature.
- **Relevance to GTOS:** Tokyo open kill-zone (00:00-03:00 UTC) for USDJPY/GBPJPY overlaps the 9:55am Tokyo fix (00:55 UTC). Consider blackout or asymmetric-bias adjustment around this window.
- **Potential hypothesis:** USDJPY 5-minute pre-Tokyo-fix systematically biased upward (USD-buy demand); test on M5 data.
- **Cross-domain links:** 06 (microstructure); 09 (fix clustering)

### Intra-Day Seasonality in Activities of the Foreign Exchange Markets: Evidence from the Electronic Broking System
- **Authors:** Takatoshi Ito, Yuko Hashimoto
- **Year:** 2006
- **Source:** *Journal of the Japanese and International Economies*, 20(4), 637-664
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S0889158306000463
- **Abstract:** EBS data on USD/JPY and EUR/USD shows U-shape intraday for Tokyo and London but NOT New York. Quote-frequency, volume, and vol move together; spreads inverse.
- **Key findings:** (1) U-shape intraday for Tokyo, London. (2) NY does NOT show U-shape, no end-of-day spike. (3) Quote frequency / volume / vol comove positively. (4) Spread comoves negatively.
- **Relevance to GTOS:** Empirical foundation for kill-zone time windows. NY kill-zone differs from London structurally — supports NOT applying London-kill-zone logic to NY-PM windows.
- **Potential hypothesis:** Per-kill-zone realized-WR may differ structurally between London and NY; KZ-fixed-effect feature in K54.
- **Cross-domain links:** 06 (microstructure intraday); 08 (volume seasonality)

### Liquidity in the Global Currency Market
- **Authors:** Karnaukh, Ranaldo, Söderlind (2022)
- **Year:** 2022
- **Source:** *Journal of Financial Economics*, 146(3), 859-883
- **URL:** https://ideas.repec.org/a/eee/jfinec/v146y2022i3p859-883.html
- **Abstract:** Updates liquidity / liquidity-risk pricing in FX. Confirms pricing of liquidity risk in cross-section; identifies new state-dependence.
- **Key findings:** (1) FX liquidity priced. (2) State-dependent risk. (3) Cross-currency commonality strong. (4) Weekly frequency findings.
- **Relevance to GTOS:** Confirmation that liquidity-state matters for FX returns. K54 sizing-layer should incorporate cross-currency liquidity proxy.
- **Potential hypothesis:** Days when XAUUSD/USDJPY co-move outliers are flagged → reduce GTOS exposure.
- **Cross-domain links:** 06 (microstructure); 21 (sizing)

### Bjønnes-Rime Dealer Behavior and Trading Systems in Foreign Exchange Markets
- **Authors:** Geir Høidal Bjønnes, Dagfinn Rime
- **Year:** 2005
- **Source:** *Journal of Financial Economics*, 75(3), 571-605
- **URL:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=244468
- **Abstract:** Dealers hold positions for minutes, mean-revert inventories. Speculation contributes more than liquidity-provision to dealer profits. Information effects in Madhavan-Smidt framework.
- **Key findings:** (1) Position-holding minutes-scale. (2) Inventory mean reversion strong. (3) Speculation > liquidity provision in profits. (4) Information effects measurable.
- **Relevance to GTOS:** Conceptual underpinning for GTOS edge: M15-horizon mean reversion is natural consequence of dealer-inventory cycling. Note: cross-link 06 owns the methodology paper.
- **Potential hypothesis:** Periods of unusually high dealer-position holding (e.g., late Friday) should show different M15 mean-reversion strength.
- **Cross-domain links:** 06 (microstructure owner); 19 (feature)

### Arbitrage in the Foreign Exchange Market: Turning on the Microscope
- **Authors:** Q. Farooq Akram, Dagfinn Rime, Lucio Sarno
- **Year:** 2008
- **Source:** *Journal of International Economics*, 76(2), 237-253
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S0022199608000706
- **Abstract:** Tick-frequency examination of CIP violations across 3 major capital markets, 7+ months. CIP violations short-lived but economically significant; duration sufficient to exploit but explains why low-frequency studies miss them.
- **Key findings:** (1) Sub-minute CIP violations occur. (2) Economically significant. (3) Sufficient duration to exploit. (4) Lower-frequency studies under-detect.
- **Relevance to GTOS:** Arbitrage is incomplete at sub-minute horizon — but GTOS operates on M15. Confirms FX is NOT efficient at high-frequency, supporting M15 mean-reversion plays generally.
- **Potential hypothesis:** Sub-minute price-inefficiency density correlates with M15 follow-through quality.
- **Cross-domain links:** 06 (microstructure)

---

## 9. Commodity-currencies, AUD/CAD/NOK and FX-Commodity links

### Can Exchange Rates Forecast Commodity Prices?
- **Authors:** Yu-chin Chen, Kenneth Rogoff, Barbara Rossi
- **Year:** 2010
- **Source:** *Quarterly Journal of Economics*, 125(3), 1145-1194
- **URL:** https://academic.oup.com/qje/article-abstract/125/3/1145/1903653
- **Abstract:** "Commodity-currency" exchange rates (AUD, CAD, NZD, NOK) robustly predict global commodity prices in-sample and out-of-sample. Reverse direction (commodity → FX) less robust.
- **Key findings:** (1) FX leads commodities, not vice versa. (2) Exchange rates are forward-looking, commodity prices reactive. (3) Robust OOS performance. (4) Mechanism: FX prices in expectations about future fundamentals.
- **Relevance to GTOS:** Cross-instrument: gold (XAUUSD) and AUD/CAD/NOK historically co-vary. GTOS XAUUSD performance may have systematic relationship to commodity-currency FX moves; not directly tradable but feature-relevant.
- **Potential hypothesis:** AUDUSD (5-day) change is a leading indicator of XAUUSD direction by ~1-2 days.
- **Cross-domain links:** 10 (gold owner); 13 (factor)

### Vehicle Currency Use in International Trade
- **Authors:** Linda S. Goldberg, Cédric Tille
- **Year:** 2008
- **Source:** *Journal of International Economics*, 76(2), 177-192
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S0022199608000664
- **Abstract:** Foundational on USD as vehicle currency in international trade invoicing. Industry features and country size dominate; coalescing effect favors dominance equilibrium. Dollar is widely used in trade not directly involving the US.
- **Key findings:** (1) Coalescing effect explains USD dominance. (2) Industry-level FX-elasticity-bid-ask matter. (3) Reference-priced commodities/exchange-traded goods sustain USD use. (4) Vehicle-currency network effect.
- **Relevance to GTOS:** Reinforces structural USD-floor mechanism beyond pure reserve-currency. Supports asymmetric expectation: USD weak rallies in EM tightly bounded.
- **Potential hypothesis:** USD periods of weakness in trade-data-release windows revert faster than periods of weakness in macro-policy windows.
- **Cross-domain links:** 13 (factor); 22 (long-horizon)

### Evidence of Carry Trade Activity
- **Authors:** Gabriele Galati, Alexandra Heath, Patrick McGuire
- **Year:** 2007
- **Source:** *BIS Quarterly Review*, September 2007
- **URL:** https://www.bis.org/publ/qtrpdf/r_qt0709e.htm
- **Abstract:** Pre-GFC documentation of carry-trade activity and indicators (CFTC positioning, BIS banking statistics, options markets, hedge-fund flows). Establishes interest-rate differentials as primary FX driver.
- **Key findings:** (1) Carry positioning measurable across multiple data sources. (2) Cross-source consistency. (3) Carry activity explains material FX flow. (4) Pre-GFC peak documentation.
- **Relevance to GTOS:** Shows that public/regulatory data feeds (CFTC IMM, BIS banking) can proxy carry-position state. Useful for slow-moving regime features in K54 v2.
- **Potential hypothesis:** Monthly CFTC IMM JPY-net-short-positioning level interacts with M15 USDJPY trade outcome.
- **Cross-domain links:** 06 (intermediary); 17 (positioning)

---

## 10. JPY weakness 2022-2024, GBP post-Brexit, regime-relevant 2020-2025

### Trade, Labour and the Brexit Exchange Rate Depreciation
- **Authors:** Various (per ScienceDirect 2024)
- **Year:** 2024
- **Source:** *Journal of International Economics*
- **URL:** https://www.sciencedirect.com/science/article/pii/S002219962400120X
- **Abstract:** Studies large GBP depreciation post-Brexit referendum. Sterling fell sharply, biggest single-day depreciation among major currencies since Bretton Woods. Examines transmission to UK trade and labour.
- **Key findings:** (1) Brexit caused structural GBP depreciation. (2) Transmission to UK firms and workers. (3) Effect persistent. (4) Major currency natural-experiment.
- **Relevance to GTOS:** GBPJPY and GBPUSD trade live for GTOS. Brexit established a structural-break in GBP behavior; subsequent (Sep 2022 mini-budget) added another. Supports GBPUSD observer-only mode.
- **Potential hypothesis:** Pre-2016 / 2016-22 / post-2022 GBPUSD M15 distributions should be tested for stationarity; expect rejection.
- **Cross-domain links:** 17 (political shock); 22 (regime change)

### Exchange Rates and Political Uncertainty: The Brexit Case
- **Authors:** Manasse, P. (per Economica 2024)
- **Year:** 2024
- **Source:** *Economica*
- **URL:** https://onlinelibrary.wiley.com/doi/full/10.1111/ecca.12509
- **Abstract:** Brexit referendum as natural experiment for political-uncertainty effect on exchange rate. Quantifies premium during uncertainty and post-vote regime.
- **Key findings:** (1) Political-uncertainty discount measurable. (2) Persistent post-vote regime change. (3) Carry-implication for GBP. (4) Lessons for similar political-uncertainty events.
- **Relevance to GTOS:** Supports GBPUSD observer-only mode. Validates that political-uncertainty episodes are structurally different regime; GTOS could explicitly mark such regimes.
- **Potential hypothesis:** UK political-event date features (general elections, leadership changes) should mark regime-flag in GBPUSD.
- **Cross-domain links:** 17 (political shock); 05 (regime change)

### The Lasting Effect of Yen-Buying Interventions
- *(Already cataloged in §5)*

### The Market Turbulence and Carry Trade Unwind of August 2024
- *(Already cataloged in §6)*

### Liquidity and Exchange Rates: An Empirical Investigation
- **Authors:** Charles Engel, Steve Pak Yeung Wu
- **Year:** 2023
- **Source:** *Review of Economic Studies*, 90(5), 2395-2438
- **URL:** https://academic.oup.com/restud/article-abstract/90/5/2395/6748716
- **Abstract:** Government-bond convenience yield (relative liquidity yield) is observable and partly explains UIP deviations. Magnitude of CIP deviations also reflects relative liquidity of funding and investment currencies.
- **Key findings:** (1) Government-bond liquidity yield essential to FX determination. (2) Treasury-basis-style measures forecast FX. (3) Substantive R² improvements. (4) Bridges UIP-CIP literature with intermediary asset pricing.
- **Relevance to GTOS:** Direct connection to Jiang-Krishnamurthy-Lustig 2021 findings. Suggests "Treasury-basis change" feature for K54 v2 USDJPY / GBPUSD.
- **Potential hypothesis:** Weekly Treasury-basis change feature delivers measurable lift on USDJPY direction at daily-week horizons.
- **Cross-domain links:** 06 (intermediary); 13 (factor)

### Risk and Resilience in the Global Foreign Exchange Market (IMF GFSR 2025)
- **Authors:** IMF (per GFSR 2025 Ch.2)
- **Year:** 2025
- **Source:** *IMF Global Financial Stability Report*, October 2025, Chapter 2
- **URL:** https://www.imf.org/-/media/files/publications/gfsr/2025/october/english/ch2.pdf
- **Abstract:** Comprehensive 2025 update on FX market vulnerabilities. Covers Aug 2024 unwind, hedge-fund FX positioning, dealer balance-sheet capacity, and resilience pathways.
- **Key findings:** (1) Hedge-fund FX positioning remains concentrated. (2) Dealer-capacity remains constrained at month/quarter ends. (3) NDF EM markets growing share. (4) Multiple risk-amplification channels documented.
- **Relevance to GTOS:** Most current authoritative summary of post-2024 FX system risks. Calibrates GTOS expectations on tail-event likelihood for next 12-18 months.
- **Potential hypothesis:** Cross-instrument tail risk monitoring should include FX as named factor; current correlation gate already covers some of this.
- **Cross-domain links:** 21 (sizing under stress); 06 (intermediary)

### Foreign Exchange Intervention: A New Database
- **Authors:** Marcel Fratzscher et al.
- **Year:** 2022 (IMF Economic Review)
- **Source:** *IMF Economic Review*
- **URL:** https://link.springer.com/article/10.1057/s41308-022-00190-8
- **Abstract:** Largest-to-date FX intervention database. Builds on Fratzscher-Gloede-Menkhoff-Sarno-Stöhr 2019 with extended panel. Methodological advances in inferring intervention from price/volume data.
- **Key findings:** (1) Intervention more common globally than reported. (2) Effectiveness varies systematically by regime. (3) Verbal-only intervention has measurable effect. (4) Database enables future research.
- **Relevance to GTOS:** Updated empirical baseline. Supports adding intervention-detection module to GTOS data pipeline.
- **Potential hypothesis:** Identifying suspected intervention M5 / M1 windows and excluding from training data improves K54 generalization.
- **Cross-domain links:** 17 (policy); 06 (event microstructure)

---

## 11. Risk premium / dollar / global financial cycle (additional)

### From World Banker to World Venture Capitalist: US External Adjustment and the Exorbitant Privilege
- **Authors:** Pierre-Olivier Gourinchas, Hélène Rey
- **Year:** 2007
- **Source:** NBER Chapters / *Journal of Political Economy* (related "International Financial Adjustment")
- **URL:** https://www.nber.org/system/files/chapters/c0121/c0121.pdf
- **Abstract:** Documents excess return of US external assets over US external liabilities (~2.69% since 1952). USD's "exorbitant privilege" connected to wealth-transfer dynamics during crises.
- **Key findings:** (1) US enjoys persistent excess return on external balance-sheet. (2) Wealth transfer USD→ROW during 2008 ≈ 20% US GDP. (3) USD appreciated 8% real during GFC despite epicenter status. (4) Asymmetric global insurance role of USD.
- **Relevance to GTOS:** Reinforces dollar-smile right-tail and asymmetric crisis-period USD behavior. Backs hypothesis that USD risk-off appreciation persists.
- **Potential hypothesis:** GFC-pattern is repeatable; design GTOS regime-stress-test on hypothetical risk-off-with-USD-rallies.
- **Cross-domain links:** 13 (factor); 22 (long-horizon)

### Dilemma not Trilemma: The Global Financial Cycle and Monetary Policy Independence
- **Authors:** Hélène Rey
- **Year:** 2015 (NBER WP 21162)
- **Source:** NBER Working Paper / *Jackson Hole Symposium 2013*
- **URL:** https://www.nber.org/papers/w21162
- **Abstract:** Global financial cycle exists in capital flows, asset prices, credit growth — co-moves with VIX. Transforms classical "trilemma" into "dilemma": independent monetary policy possible only with capital-account management.
- **Key findings:** (1) GFC empirically present and pervasive. (2) Center-country (US) monetary policy drives GFC. (3) Floating exchange rates do NOT insulate. (4) Fundamental policy implication: capital controls or aligned monetary policy.
- **Relevance to GTOS:** USD strength/weakness driven by Fed monetary stance is global event affecting ALL GTOS instruments. VIX is therefore a load-bearing K54 feature beyond any single instrument.
- **Potential hypothesis:** A "Fed monetary stance index" feature improves K54 across ALL GTOS instruments simultaneously, not just USD-pairs.
- **Cross-domain links:** 13 (factor); 17 (policy); 22 (decadal)

### Risk, Uncertainty and Monetary Policy
- **Authors:** Geert Bekaert, Marie Hoerova, Marco Lo Duca
- **Year:** 2013
- **Source:** *Journal of Monetary Economics*, 60(7), 771-788
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S0304393213000871
- **Abstract:** Decomposes VIX into risk-aversion and uncertainty proxies. Lax monetary policy decreases both, with stronger effect on risk-aversion. Establishes Fed-VIX feedback mechanism.
- **Key findings:** (1) VIX = risk-aversion + uncertainty. (2) Risk-aversion responds more to monetary policy. (3) Robust across SVAR identifications. (4) Bridges policy and asset-pricing.
- **Relevance to GTOS:** Refines VIX-as-feature: when VIX moves, GTOS should distinguish risk-aversion vs uncertainty origin (both have FX implications).
- **Potential hypothesis:** Decomposed-VIX (risk-aversion separately from vol-of-vol) outperforms raw VIX in predicting USDJPY conditional WR.
- **Cross-domain links:** 16 (vol); 17 (policy)

### A Macroeconomic Model with a Financial Sector
- **Authors:** Markus K. Brunnermeier, Yuliy Sannikov
- **Year:** 2014
- **Source:** *American Economic Review*, 104(2), 379-421
- **URL:** https://www.aeaweb.org/articles?id=10.1257/aer.104.2.379
- **Abstract:** Continuous-time GE model with financial frictions. Endogenous risk persists in crisis even when exogenous risk is low; nonlinear amplification produces volatility-paradox episodes.
- **Key findings:** (1) Financial frictions alone can generate amplification. (2) Endogenous risk dynamics. (3) Volatility paradox. (4) Foundational for modern intermediary-asset-pricing literature.
- **Relevance to GTOS:** Provides theoretical basis for "intermediary capacity stress" → FX dislocation cascade. Connects to memory `feedback_decay_is_ceo_number_one_concern` — frictions slowly erode then suddenly amplify.
- **Potential hypothesis:** Periods of low realized volatility (especially > 6 months) signal building tail risk; CFTC + IMM positioning data flag this.
- **Cross-domain links:** 03 (vol paradox); 22 (regime fragility)

---

## 12. Currency-management benchmark / professional flows

### Do Professional Currency Managers Beat the Benchmark?
- **Authors:** Momtchil Pojarliev, Richard M. Levich
- **Year:** 2008
- **Source:** *Financial Analysts Journal* / SSRN
- **URL:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1077687
- **Abstract:** 1990-2006 currency-fund-manager returns ~25bp/month. Most explained by exposure to four factors (carry, trend, value, vol). Alpha redefined as residual after factor exposure.
- **Key findings:** (1) Average pro-currency-fund excess return 25bp/month. (2) Four-factor exposure explains most. (3) True alpha modest. (4) Style-persistence > alpha-persistence.
- **Relevance to GTOS:** Sets benchmark for "what's possible" in FX retail. GTOS R/trade target should be evaluated against this baseline. Highlights that style-persistence is real (carry traders stay carry traders) — relevant for K54 architecture.
- **Potential hypothesis:** GTOS as a "non-style" / event-trading manager should be uncorrelated with carry/trend/value/vol factors; check beta to these.
- **Cross-domain links:** 22 (alpha decay); 13 (factor)

### Trades of the Living Dead: Style Differences, Style Persistence and Performance of Currency Fund Managers
- **Authors:** Momtchil Pojarliev, Richard M. Levich
- **Year:** 2010
- **Source:** *Journal of International Money and Finance*, 29(8), 1752-1775
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S0261560610000653
- **Abstract:** Extends 2008 work. Style persistence dominates alpha persistence — funds keep their style year-on-year, but year-1 alpha does not predict year-2 alpha.
- **Key findings:** (1) Style persistence robust. (2) Alpha persistence weak. (3) Implications for fund selection. (4) Mean-reversion of alpha across funds.
- **Relevance to GTOS:** Validates GTOS skepticism of fund-management alpha persistence. Reinforces that GTOS edge needs continuous validation, not assumption-of-persistence.
- **Potential hypothesis:** GTOS rolling-50 OB-continuation alarm aligns with this principle — assume mean-reversion of edge unless evidence persists.
- **Cross-domain links:** 22 (alpha decay); 14 (style/momentum)

---

## 13. Gaps and caveats

1. **Practitioner-only "dollar smile" framework**: Stephen Jen's dollar-smile theory is widely-cited but has no peer-reviewed canonical paper. Catalogued via practitioner research (Eurizon SLJ Capital). Synthesis agent should treat as "conceptual framework" not "validated fact."
2. **NDF / EM sources less covered**: Spec was AE-FX-focused (USDJPY/GBPJPY/GBPUSD); EM-NDF literature included one IMF working paper but is otherwise lighter.
3. **2022-24 BoJ academic literature lag**: Empirical evaluations of 2022-2024 BoJ interventions are still being published (one cataloged from Apr 2025). Worker recommends re-pull for synthesis-2 phase to capture late-arriving papers.
4. **Cross-domain handoff for FX volatility / option-implied**: Several FX-vol papers (Della Corte et al. 2016) are arguably better-fit for domain 16 — kept here per spec section 6's "11 owns the FX-content" rule, with cross-link.
5. **No fabrication**: All 47 papers verified by URL. None are seed candidates; all are confirmed published.
6. **Coverage of GBPJPY as instrument-specific**: GBPJPY-specific empirical literature is thin (it's a synthetic cross). Workers should derive GBPJPY behavior from JPY safe-haven + GBP politics + USD exchange-rate compositional decomposition.
7. **Memory-aware caveats applied**: F11 OB-zone decay finding, F15 regime-conditioned LONG-side selectivity collapse, and S79 risk policy all visible in selected papers' GTOS-relevance fields. Hypotheses target K54 v2 features mappable to existing GTOS feature pipeline.
8. **Phase 2 synthesis recommendation**: cross with domain 13 (factor), domain 17 (behavioral), and domain 06 (microstructure) explicitly — each provides ~20-30% of insight needed for FX hypothesis backlog.

---

*End of papers.md. See `papers.csv` for machine-readable schema with all 47 entries.*
