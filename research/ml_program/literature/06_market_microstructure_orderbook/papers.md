# Domain 06 — Market Microstructure and Order Book

**Phase 1 worker:** Literature Research Agent — Market Microstructure + Order Book
**Date compiled:** 2026-04-28
**Papers cataloged:** 78
**Coverage:** Foundational asymmetric-information theory (Kyle, Glosten-Milgrom, Roll), optimal market-making (Avellaneda-Stoikov, Ho-Stoll), optimal execution (Almgren-Chriss, Obizhaeva-Wang, Bertsimas-Lo), order-flow imbalance (Cont-Kukanov-Stoikov, Cont-Cucuringu-Zhang cross-impact, Eisler-Bouchaud-Kockelkoren), flow toxicity (PIN, VPIN, BV-VPIN, plus Andersen-Bondarenko critique), Bouchaud-school empirical microstructure (Lillo-Farmer-Mantegna, Toth-Bouchaud V-shape, Donier-Bouchaud minimal model, Sato-Kanazawa LMF test), FX-specific microstructure (Lyons hot-potato, Evans-Lyons, Mancini-Ranaldo-Wrampelmeyer, Bjonnes-Rime, Osler stop-cascade, King-Osler-Rime survey), futures microstructure (Hasbrouck E-mini, Kang-Pan-Liu COMEX gold, Dobrev Treasury OFI 2025, Kirilenko Flash Crash, Brogaard EPM), recent 2018-2025 deep-learning LOB research (DeepLOB, Sirignano-Cont, Kolm-Turiel-Westray, Briola, LiT transformer, Lucchese), and contrarian / null-result findings.

---

## 1. Section overview

This domain provides the load-bearing theoretical foundation for several GTOS subsystems:

- **`market_state.py` order-block detection** — the OB construct is hypothesized to reflect institutional supply/demand zones; Kyle (1985) and Glosten-Milgrom (1985) provide the asymmetric-information theory explaining why OB retests can carry an edge (residual informed-flow footprint), while Bouchaud-Mezard-Potters (2002) and Bouchaud's later work warns that the impact is largely transient and book shape is humped, not flat.
- **`tick_features.py` 12 microstructure features** — order-flow imbalance (OFI), micro-price, queue ratio. The literature anchor for which features are theoretically justified is Cont-Kukanov-Stoikov (2014) for OFI, Avellaneda-Stoikov (2008) for the inventory-skewed micro-price, and Easley-Lopez de Prado-O'Hara (2012) for VPIN flow toxicity.
- **E24/E26 microstructure null verdict** — the M15-aggregated null result is consistent with literature predicting that microstructure signal lives at sub-1-minute scales and decays rapidly with aggregation. This domain documents *why*.
- **MT5 broker spread vs venue-true spread** — Lyons (1995, 1997, 2001), Evans-Lyons (2002), and the FX dealer-market literature explain why MT5 tick-bid/tick-ask are dealer quotes, not lit-book BBO, and what biases this introduces.
- **K54 v2 features** — order-flow imbalance, micro-price deviation, queue dynamics, VPIN as candidate per-regime classifier features (subject to MT5 data quality).
- **Execution slippage analysis (`execution.py`)** — Almgren-Chriss (2000), Almgren (2003), Obizhaeva-Wang (2013) provide the slippage decomposition framework for redacted_account fill-quality assessment.

Coverage by section (will be finalized at end):

| Section | Theme | Anchor papers |
|---------|-------|---------------|
| 1 | Foundational asymmetric-information theory | Kyle 1985, Glosten-Milgrom 1985, Roll 1984, Easley-O'Hara PIN |
| 2 | Optimal market-making | Avellaneda-Stoikov 2008, Ho-Stoll 1981, Cartea-Jaimungal HFT books |
| 3 | Optimal execution | Almgren-Chriss 2000, Almgren 2003, Obizhaeva-Wang 2013, Bertsimas-Lo 1998 |
| 4 | Empirical order-book and impact (Bouchaud school) | Bouchaud-Mezard-Potters 2002, Bouchaud-Farmer-Lillo, Lillo-Farmer-Mantegna 2003 |
| 5 | Order-flow imbalance and price discovery | Cont-Kukanov-Stoikov 2014, Briola et al 2021, Fed 2025 |
| 6 | Flow toxicity (VPIN, PIN) | Easley-O'Hara 1992, Easley-Lopez-O'Hara 2012, VPIN critiques |
| 7 | FX-specific microstructure | Lyons 1995/1997/2001, Evans-Lyons 2002/2008, Mancini-Ranaldo-Wrampelmeyer 2013 |
| 8 | Futures and indices microstructure | Hasbrouck-Saar 2013, Boehmer-Wu 2013, gold/silver/treasuries |
| 9 | Deep learning / ML on LOB | Sirignano-Cont 2019, DeepLOB Zhang 2019, Briola transformers 2024 |
| 10 | Contrarian / null findings / critiques | Andersen-Bondarenko VPIN critique, methodology pushbacks |

---

## 2. Sections — per-paper catalog

### Section 1 — Foundational asymmetric-information and microstructure theory

#### 06-01 Continuous Auctions and Insider Trading
- **Authors / year:** Kyle A.S., 1985
- **Source:** Econometrica 53(6) 1315-1335
- **URL:** https://personal.utdallas.edu/~nina.baranchuk/Fin7310/papers/Kyle1985.pdf
- **Abstract:** Dynamic model of insider trading with sequential auctions resembling sequential equilibrium; examines informational content of prices, market liquidity, and value of private information; three trader types (insider, noise traders, market makers); as auction interval -> 0 prices follow Brownian motion, market depth is constant, all private info incorporated by end.
- **Key findings:** Foundational asymmetric-information equilibrium; introduces Kyle's lambda (price impact per unit order flow), 1/lambda = market depth; informed trader's optimal trading strategy is linear in private signal; noise-trader volatility is a free parameter that scales lambda inversely; private info gets fully revealed by terminal time.
- **Relevance to GTOS:** The OB construct in `market_state.py` is empirically the locus where informed flow leaves a footprint; Kyle's framework gives a theoretical reason an OB retest can have edge (residual price-impact from absorbed informed order) and grounds the lambda concept underlying the displacement_quality_score feature in K50/K54.
- **Hypothesis (H1):** Conditioning trade entries on a Kyle-style lambda estimate (regress 1-min returns on signed volume) above the rolling-N median raises XAUUSD ob_retest expectancy by >=0.10R OOS.
- **Cross-domain:** 07 (ICT footprint as informed-flow proxy); 19 (ML feature: lambda); 02 (linear inference).
- **Data source:** Theoretical (no empirical data).

#### 06-02 Bid, ask and transaction prices in a specialist market with heterogeneously informed traders
- **Authors / year:** Glosten L.R. & Milgrom P.R., 1985
- **Source:** Journal of Financial Economics 14(1) 71-100
- **URL:** https://milgrom.people.stanford.edu/wp-content/uploads/1984/09/Bid-Ask-and-Transaction-Prices.pdf
- **Abstract:** Models a specialist who quotes bid and ask facing a population of traders some of whom hold private information; shows that even risk-neutral specialist with zero expected profit must quote a positive bid-ask spread arising entirely from adverse-selection cost.
- **Key findings:** Adverse selection alone produces a bid-ask spread (no inventory cost needed); spread widens with proportion of informed traders and informativeness of their signal; market-maker quotes are martingale conditional on order flow; explains why illiquid markets have wider spreads even with no inventory cost.
- **Relevance to GTOS:** Theoretical anchor for why touch-counts matter at OB retests: each retest is a sequential trade in the Glosten-Milgrom sense; if the market has not absorbed the informational shock, subsequent trades carry adverse-selection signal. Justifies ADR-005 touch_count gate (touch=2 worse than touch=1 in H2-2026).
- **Hypothesis (H2):** Build a sequential-Bayes signal that updates a posterior probability of 'informed-flow remaining' after each touch on a XAUUSD M15 OB; signal threshold at p<0.5 should select PASS-only cohort with WR uplift >=5pp.
- **Cross-domain:** 07 (touch-count empirical); 02 (sequential Bayes); 21 (sizing on adverse-selection prob).
- **Data source:** Theoretical.

#### 06-03 High-frequency trading in a limit order book
- **Authors / year:** Avellaneda M. & Stoikov S., 2008
- **Source:** Quantitative Finance 8(3) 217-224
- **URL:** https://people.orie.cornell.edu/sfs33/LimitOrderBook.pdf
- **Abstract:** Studies a stock dealer's strategy for submitting bid and ask quotes in a limit order book where the agent faces inventory risk from diffusive mid-price and transactions risk from Poisson arrivals; derives optimal quotes via maximal-expected-utility framework and a two-step procedure (indifference price then market-LOB calibration).
- **Key findings:** Closed-form optimal bid/ask reservation prices given inventory; inventory-skewed quote spreads dominate naive symmetric quoting in P&L variance simulations; framework still anchors most modern HFT-MM literature; key parameters are gamma (risk aversion), sigma (vol), and order-arrival intensities A,k.
- **Relevance to GTOS:** Direct anchor for assessing whether MT5 spread snapshots produce a viable micro-price; the AS reservation price gives the principled "fair" mid that GTOS pre-AI gates can compare against the listed mid to detect dealer-inventory skew, especially around news. Useful for `tick_features.py` micro-price column.
- **Hypothesis (H3):** A reservation-price-style micro-price signal (computed from rolling spread and signed volume) at OB-retest entry predicts realized R with abs(t)>2 on XAUUSD M15.
- **Cross-domain:** 05 (vol regime input); 19 (RL execution).
- **Data source:** Simulated + US equities tick.

#### 06-04 Optimal Execution of Portfolio Transactions
- **Authors / year:** Almgren R. & Chriss N., 2000
- **Source:** Journal of Risk 3(2) 5-39
- **URL:** https://www.smallake.kr/wp-content/uploads/2016/03/optliq.pdf
- **Abstract:** Considers execution of portfolio transactions minimizing combination of volatility risk and transaction costs from permanent and temporary market impact; constructs efficient frontier of execution strategies (mean cost vs cost variance).
- **Key findings:** Explicit decomposition into permanent (lasting) vs temporary (decayed by next period) impact; efficient-frontier framework analogous to Markowitz; closed-form arithmetic Brownian + linear impact solution; risk-aversion parameter trades expected slippage for variance.
- **Relevance to GTOS:** Operationally relevant for redacted_account fill-quality assessment: GTOS submits stop-limit orders at OB midpoint; if fills are systematically worse than mid by epsilon and epsilon scales with size, Almgren-Chriss frames this as temporary impact. Useful for `execution.py` slippage tracking.
- **Hypothesis (H4):** Per-instrument fitted Almgren-Chriss eta (temporary impact coefficient) is stable within +/-30% week-over-week across 6 weeks of FN fills.
- **Cross-domain:** 21 (sizing); 20 (RL exec).
- **Data source:** Theoretical with NYSE TAQ illustrative.

#### 06-05 The Price Impact of Order Book Events
- **Authors / year:** Cont R. & Kukanov A. & Stoikov S., 2014
- **Source:** Journal of Financial Econometrics 12(1) 47-88; arXiv:1011.6402
- **URL:** https://arxiv.org/abs/1011.6402
- **Abstract:** Shows that over short time intervals price changes are mainly driven by order-flow imbalance (OFI) defined as the imbalance between supply and demand at the best bid and ask; documents linear OFI->price relation with slope inversely proportional to depth; results robust to intraday seasonality and stable across stocks/time scales.
- **Key findings:** OFI explains majority of intraday price variance, R^2 >= 0.65 in equities; price-impact slope = 1/depth; the empirical sqrt(volume)-impact law arises from OFI scaling; OFI is a better adverse-selection proxy than signed-volume.
- **Relevance to GTOS:** Foundational reference for `tick_features.py` OFI computation; if MT5 only delivers L1 spread + volume, GTOS can approximate OFI from per-tick spread changes plus signed-volume; directly relevant to the E24/E26 microstructure null verdict (memory `project_microstructure_archived`) — paper-implied that M15-aggregated OFI loses most signal.
- **Hypothesis (H5):** A 1-minute OFI signal computed from MT5 ticks correlates r >= 0.4 with 1-minute mid-price change on XAUUSD; M15-aggregated OFI correlates r < 0.10. Tests whether E24 null is fundamental or an aggregation artifact.
- **Cross-domain:** 07 (OFI as ICT footprint); 19 (OFI feature for K54); 03 (square-root impact law as Hurst).
- **Data source:** NYSE TAQ S&P500.

#### 06-06 Statistical properties of stock order books: empirical results and models
- **Authors / year:** Bouchaud J.-P. & Mezard M. & Potters M., 2002
- **Source:** Quantitative Finance 2(4) 251-256; arXiv:cond-mat/0203511
- **URL:** https://arxiv.org/abs/cond-mat/0203511
- **Abstract:** Investigates statistical properties of order books for three liquid Paris Bourse stocks; finds power-law distribution of incoming limit-order prices around current price with diverging mean; humped average-book shape reproducible by zero-intelligence numerical model.
- **Key findings:** Power-law incoming-order distribution with exponent ~1.5; humped book shape (peak away from mid, not at mid); zero-intelligence Mike-Farmer model captures qualitative shape; foundation for Bouchaud school of empirical microstructure.
- **Relevance to GTOS:** Suggests OB depth is not at the mid but a few ticks away — relevant when `market_state.py` defines OB midpoints; if true OB depth is offset, GTOS' midpoint definition may need adjustment for liquidity-aware entries on FX/gold (broker-dependent).
- **Hypothesis (H6):** Empirical XAUUSD MT5 LOB-equivalent (from spread time series + volume) shows humped depth profile with peak at 2-5 ticks from mid (instrument-dependent), justifying offset entry triggers vs midpoint.
- **Cross-domain:** 03 (power-law distributions); 07 (book shape vs OB).
- **Data source:** Paris Bourse 3 stocks.

#### 06-07 Flow Toxicity and Liquidity in a High Frequency World (VPIN)
- **Authors / year:** Easley D. & Lopez de Prado M. & O'Hara M., 2012
- **Source:** Review of Financial Studies 25(5) 1457-1493
- **URL:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1695596
- **Abstract:** Order flow is toxic when it adversely selects market makers; presents VPIN (volume-synchronized probability of informed trading) as a high-frequency toxicity metric updated in volume time; develops bulk-volume classification (BVC) for HFT-suitable buy-sell labeling.
- **Key findings:** VPIN = |Vbuy - Vsell| / (Vbuy + Vsell) computed in equal-volume buckets; volume-time clock removes intraday seasonality; VPIN spikes precede short-term toxicity-induced volatility; BVC outperforms tick-rule for buy/sell classification at HFT speeds.
- **Relevance to GTOS:** Strongest cross-link to domain 05 (regime detection): VPIN as a toxicity-driven regime feature for K54. GTOS' MT5 tick stream + per-tick volume provides everything needed to compute VPIN — directly testable as a pre-AI gate or feature.
- **Hypothesis (H7):** A rolling VPIN signal on XAUUSD M15 ticks above its 90th percentile precedes >=0.5 R adverse moves within next 4 bars at rate >=1.5x baseline (n>=200 events).
- **Cross-domain:** 05 (regime); 08 (volume); 16 (vol regime).
- **Data source:** E-mini S&P500 ES futures.

#### 06-08 A Simple Implicit Measure of the Effective Bid-Ask Spread in an Efficient Market
- **Authors / year:** Roll R., 1984
- **Source:** Journal of Finance 39(4) 1127-1139
- **URL:** https://www.bauer.uh.edu/rsusmel/phd/roll1984.pdf
- **Abstract:** In an efficient market with i.i.d. fundamental value, trading costs induce negative serial covariance in observed price changes; effective bid-ask spread can be measured implicitly as 2*sqrt(-cov) where cov is the first-order serial covariance of price changes.
- **Key findings:** Closed-form spread estimator from price-change autocovariance only (no quote data needed); empirically related to firm size; works when cov<0 (limitation: positive cov produces no estimate); foundation for low-frequency liquidity proxies (Corwin-Schultz, Abdi-Ranaldo).
- **Relevance to GTOS:** Highly operationally useful — GTOS' historical CSVs do not always include reliable bid/ask; Roll measure can produce a per-instrument synthetic spread from M1 closes alone, useful for backtest realism on `data/historical_2026/`. Avoids needing tick-level bid/ask reconstruction.
- **Hypothesis (H8):** Per-instrument Roll-implied spread from M1 closes for XAU/US30/USDJPY/GBPJPY tracks broker-listed spreads with rank correlation >=0.6 across 6-month sample.
- **Cross-domain:** 02 (covariance estimation); 21 (TCA realism for backtest).
- **Data source:** CRSP daily 1963-1982.

#### 06-09 Time and the Process of Security Price Adjustment
- **Authors / year:** Easley D. & O'Hara M., 1992
- **Source:** Journal of Finance 47(2) 577-605
- **URL:** https://onlinelibrary.wiley.com/doi/10.1111/j.1540-6261.1992.tb04402.x
- **Abstract:** Models the process by which information is incorporated into prices when the timing of trades is itself informative; develops the static PIN model where informed and uninformed traders arrive in a Poisson process and trade days are either no-news, good-news, or bad-news.
- **Key findings:** Time between trades is correlated with private information; absence of trades is itself an informative signal; introduces the PIN (probability of informed trading) parameter alpha*mu / (alpha*mu + 2*epsilon); foundation for all PIN/VPIN literature.
- **Relevance to GTOS:** GTOS uses M15 candle close as event clock — no-trade quiet periods may carry information but are systematically suppressed by the M15 aggregation. PIN-style modeling would treat low-volume kill-zone bars as informative-quiet not noise.
- **Hypothesis (H9):** A daily PIN estimate per-instrument shifts upward by >=2pp during the F15 H1->H2 regime change for XAUUSD, providing a regime-shift early warning signal.
- **Cross-domain:** 05 (regime); 02 (Bayesian Poisson MLE); 19 (PIN as feature).
- **Data source:** NYSE, 60 stocks, 1987.

#### 06-10 Optimal Dealer Pricing under Transactions and Return Uncertainty
- **Authors / year:** Ho T. & Stoll H.R., 1981
- **Source:** Journal of Financial Economics 9(1) 47-73
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/0304405X81900209
- **Abstract:** Examines a single dealer facing stochastic order arrivals (Poisson jumps) and continuous return risk on inventory; uses stochastic dynamic programming to derive optimal bid/ask prices that maximize expected utility of terminal wealth as a function of state.
- **Key findings:** Bid-ask spread is increasing in inventory variance, return uncertainty, and inventory level (skewed quotes); dealer reservation price moves opposite to inventory (inventory-control effect); foundation for inventory-based market-making theory predating Avellaneda-Stoikov by 27 years.
- **Relevance to GTOS:** Theoretical underpinning for why broker spreads on MT5 widen near news (return uncertainty up) and during low-liquidity periods (effective inventory variance up); relevant for `tick_features.py` spread-based features and pre-AI gates that filter on spread anomalies.
- **Hypothesis (H10):** Per-instrument MT5 spread widens proportionally to rolling realized volatility (Ho-Stoll prediction); spread / vol ratio is more stationary than raw spread.
- **Cross-domain:** 16 (vol regime); 02 (DP optimization).
- **Data source:** Theoretical.

#### 06-11 Optimal Trading Strategy and Supply/Demand Dynamics
- **Authors / year:** Obizhaeva A.A. & Wang J., 2013
- **Source:** Journal of Financial Markets 16(1) 1-32
- **URL:** https://web.mit.edu/wangj/www/pap/ObizhaevaWang13.pdf
- **Abstract:** Develops a simple framework to model dynamics of supply and demand in a limit-order-book market and their impact on execution cost; shows optimal strategy involves both discrete and continuous trades, not only continuous trades.
- **Key findings:** Order book has finite resilience (rate at which depth recovers after a trade); optimal execution combines initial discrete block + continuous flow + final discrete block; resilience parameter rho controls the trade-off; substantial cost savings vs Almgren-Chriss continuous-only.
- **Relevance to GTOS:** Critical for understanding XAUUSD pre-news liquidity vacuum: low rho (slow resilience) makes large orders disproportionately costly. Connects to ADR-006 sl_buffer logic — the buffer should scale with effective resilience, not just ATR.
- **Hypothesis (H11):** XAUUSD MT5 spread half-life after large prints (estimated rho) is <30s during NY KZ but >5min during Asian thin period; sl_beyond_ob tolerance should be regime-conditioned on this.
- **Cross-domain:** 21 (sizing); 20 (RL exec); 05 (resilience as regime feature).
- **Data source:** Theoretical with NYSE TAQ illustrative.

#### 06-12 Optimal Execution with Nonlinear Impact Functions and Trading-Enhanced Risk
- **Authors / year:** Almgren R., 2003
- **Source:** Applied Mathematical Finance 10(1) 1-18
- **URL:** https://www.tandfonline.com/doi/abs/10.1080/135048602100056
- **Abstract:** Determines optimal trading strategies for liquidating a large single-asset portfolio to minimize a combination of volatility risk and market-impact costs, where impact cost per share is a power-law function of trading rate with arbitrary positive exponent.
- **Key findings:** Includes square-root impact law as special case; defines a 'characteristic time' for optimal trading that decreases as execution proceeds; introduces 'critical portfolio size' above which trading-enhanced risk dominates; canonical reference for the sqrt-impact regime.
- **Relevance to GTOS:** Validates 1/2-power impact law for execution slippage modeling; if FN fills show concave-impact pattern, GTOS sizing logic in `risk_manager.py` should incorporate sqrt(size) cost — relevant to S79 risk policy and follow-up sharpe-weighted variant.
- **Hypothesis (H12):** Per-instrument FN slippage scales with sqrt(lot size); fitting log(slip) = a + b*log(size) yields b in [0.4, 0.6] across XAU/US30/USDJPY/GBPJPY (n>=200 fills/instrument).
- **Cross-domain:** 21 (sizing); 03 (power laws).
- **Data source:** Theoretical with empirical citations.

#### 06-13 Master Curve for Price-Impact Function
- **Authors / year:** Lillo F. & Farmer J.D. & Mantegna R.N., 2003
- **Source:** Nature 421 129-130
- **URL:** https://www.nature.com/articles/421129a
- **Abstract:** Shows that price reaction to a single transaction depends on transaction volume, stock identity, and possibly other factors; rescaling by liquidity for stocks of different market-cap classes produces a uniform price-impact curve across years 1995-1998.
- **Key findings:** Single-curve collapse of price-impact function across firm sizes; suggests universal supply/demand fluctuation mechanism; concave (sub-linear) impact at large volume — not square-root — depending on liquidity normalization; supports econophysics hypothesis of universal scaling laws.
- **Relevance to GTOS:** Directly relevant to multi-instrument K54 regression — if a single rescaled-impact curve holds across XAUUSD/US30/USDJPY/GBPJPY, GTOS can pool training data across instruments (universality), reducing per-instrument data sparsity for K54 v2 features.
- **Hypothesis (H13):** A normalized price-impact curve estimated separately per-instrument from MT5 ticks collapses within +/-15% to a single master curve after rescaling by per-instrument median spread and median volume.
- **Cross-domain:** 03 (universality / scaling); 13 (cross-asset coherence); 19 (pooled ML training).
- **Data source:** LSE 30 stocks, 1995-1998.

#### 06-14 Fluctuations and Response in Financial Markets: The Subtle Nature of 'Random' Price Changes
- **Authors / year:** Bouchaud J.-P. & Gefen Y. & Potters M. & Wyart M., 2004
- **Source:** Quantitative Finance 4(2) 176-190; arXiv:cond-mat/0307332
- **URL:** https://arxiv.org/abs/cond-mat/0307332
- **Abstract:** Using TAQ data from Paris stock market, shows random walk nature of prices results from delicate interplay between long-range correlated market orders (super-diffusion) and mean-reverting limit orders (sub-diffusion); develops propagator model where price impact decays in time.
- **Key findings:** Order flow has long memory (Hurst > 0.7); market impact decays in time as a power law (propagator ~t^{-beta}); fluctuation-response relation analogous to physics; market sits at a critical point where price is purely diffusive.
- **Relevance to GTOS:** The propagator framework explains *why* GTOS' OB retest signal exists: a large displacement creates impact whose memory persists in the book (the OB), and the price reverts toward the source as impact decays. Time-decay of OB validity (rolling-50 window in `ob_continuation_monitor`) is theoretically grounded here.
- **Hypothesis (H14):** XAUUSD OB-retest WR decays with time-since-OB-formation as a power law (alpha-fit of WR ~ t^{-alpha}); alpha estimable across n>=300 historical OBs and used to bound rolling-50 lookback.
- **Cross-domain:** 03 (long memory, Hurst); 07 (OB time-decay).
- **Data source:** Paris Bourse TAQ.

#### 06-15 Tests of Microstructural Hypotheses in the Foreign Exchange Market
- **Authors / year:** Lyons R.K., 1995
- **Source:** Journal of Financial Economics 39(2-3) 321-351
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/0304405X9500832Y
- **Abstract:** Introduces a three-part transactions dataset to test inventory-control vs asymmetric-information microstructure hypotheses in spot FX; uses one dealer's complete record of his quotes, transactions, and inventory.
- **Key findings:** Strong evidence for inventory-control effect on price (novel for FX); asymmetric-information effect also present; FX dealer behavior matches Madhavan-Smidt and Glosten-Harris empirical microstructure rather than the older Kyle/GM extreme cases; foundation for the FX hot-potato view.
- **Relevance to GTOS:** Most directly relevant paper for understanding why MT5 dealer spreads on FX (USDJPY, GBPJPY, GBPUSD) are not lit-book BBO but inventory-skewed dealer quotes; Lyons' inventory mechanism is the precise mechanism that biases MT5 ticks vs venue truth.
- **Hypothesis (H15):** USDJPY MT5 mid-price exhibits Lyons-style inventory mean-reversion: cov(spread shift, signed-volume) is negative at 5-30s lags during low-liquidity periods, consistent with dealer-inventory skew.
- **Cross-domain:** 11 (FX dealer market); 02 (regression tests).
- **Data source:** Single FX dealer 5-day record, 1992.

#### 06-16 Order Flow and Exchange Rate Dynamics
- **Authors / year:** Evans M.D.D. & Lyons R.K., 2002
- **Source:** Journal of Political Economy 110(1) 170-180
- **URL:** https://www.journals.uchicago.edu/doi/full/10.1086/324391
- **Abstract:** Macroeconomic FX models perform poorly (rare R^2 > 10%, beaten by random walk); presents a microstructure-augmented model that includes order flow as a determinant; daily DM/$ regressions yield R^2 > 50% and out-of-sample beat random-walk forecasts.
- **Key findings:** Order flow is the proximate price determinant; $1bn net dollar purchase moves DM/$ by ~1 pfennig; macro fundamentals matter only conditional on order flow; bridges Meese-Rogoff anomaly via microstructure.
- **Relevance to GTOS:** Establishes that FX prices are order-flow-driven on the daily horizon — supports including OFI/VPIN-style features in K54 for FX instruments. The Evans-Lyons R^2 result implies GTOS' prompt should treat order-flow imbalance as a first-class signal, not auxiliary.
- **Hypothesis (H16):** A daily order-flow proxy on USDJPY (cumulative signed-volume from MT5 ticks) regressed on daily returns yields R^2 >= 0.20, validating the Evans-Lyons mechanism in retail data.
- **Cross-domain:** 11 (FX); 13 (multi-asset OF coherence); 19 (OF as feature).
- **Data source:** Reuters D2000-2 EBS DM/USD JPY/USD, 1996.

#### 06-17 Liquidity in the Foreign Exchange Market: Measurement, Commonality, and Risk Premiums
- **Authors / year:** Mancini L. & Ranaldo A. & Wrampelmeyer J., 2013
- **Source:** Journal of Finance 68(5) 1805-1841
- **URL:** https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.12053
- **Abstract:** First systematic study of FX liquidity using EBS tick data; finds significant variation in liquidity across exchange rates, substantial illiquidity costs, and strong commonality in liquidity across currencies and with equity/bond markets.
- **Key findings:** FX commonality factor explains majority of liquidity variation across pairs; liquidity risk priced in carry trades (funding currencies offer insurance, investment currencies have exposure); 2007-2009 spillover via liquidity spirals; spread/effective-cost measures all align.
- **Relevance to GTOS:** Strongest evidence that FX liquidity has *commonality* — when GBPJPY spread spikes, USDJPY and GBPUSD likely follow. Supports a cross-instrument liquidity-risk gate in GTOS that halve-position-sizes during commonality stress periods (extends current correlation gate).
- **Hypothesis (H17):** A daily FX-liquidity commonality factor (PC1 of MT5 spreads across USDJPY, GBPJPY, GBPUSD) above its 90th percentile precedes >=20% increase in next-day realized vol for those instruments.
- **Cross-domain:** 11 (FX); 13 (commonality); 16 (vol).
- **Data source:** EBS tick data, 9 major + 9 emerging FX pairs, 1997-2009.

#### 06-18 The Flash Crash: High-Frequency Trading in an Electronic Market
- **Authors / year:** Kirilenko A. & Kyle A.S. & Samadi M. & Tuzun T., 2017
- **Source:** Journal of Finance 72(3) 967-998
- **URL:** https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.12498
- **Abstract:** Studies intraday market intermediation in an electronic market before and during the May 6, 2010 Flash Crash, using audit-trail transaction data for E-mini S&P 500 futures; large automated selling program rapidly executed.
- **Key findings:** HFT intermediaries did not fundamentally change behavior during the crash; "hot potato" passing of liquidity demand; HFT inventory whips around but stays mean-reverting; suggests HFT does not dampen extreme stress events.
- **Relevance to GTOS:** Direct relevance to US30/NAS100 stop-cascade stress periods — Kirilenko et al. document the mechanism by which a single large seller can crash an electronic futures market in minutes. GTOS' between-KZ pending-limit checker and per-symbol heartbeat-flatten kill switch are partial mitigations against this type of event.
- **Hypothesis (H18):** During US30 / NAS100 'flash-crash-like' minutes (defined by 6+ sigma 1-min return), MT5 spread widens >=10x normal and order-flow imbalance reverses sign within 5 min — testable via reconstructed tick history.
- **Cross-domain:** 12 (equity indices); 21 (kill-switch motivation); 18 (cascade psychology).
- **Data source:** CFTC audit-trail E-mini S&P500 futures, May 2010.

#### 06-19 VPIN and the Flash Crash (critique)
- **Authors / year:** Andersen T.G. & Bondarenko O., 2014
- **Source:** Journal of Financial Markets 17 1-46
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S1386418113000475
- **Abstract:** Using tick data for S&P 500 futures, shows VPIN by construction is correlated with trading volume and return volatility innovations; finds no incremental predictive power for future volatility; VPIN reached all-time high *after* the flash crash, not before.
- **Key findings:** VPIN is a poor predictor of short-run volatility; predictive content is mechanically driven by trading intensity; results highly dependent on bulk-volume classification rule; using tick-rule classification VPIN behaves opposite to ELO claims.
- **Relevance to GTOS:** **Contrarian / null finding.** Tempers enthusiasm for VPIN as a GTOS pre-AI gate or K54 feature; Andersen-Bondarenko's critique implies VPIN's signal is largely a vol/volume proxy, so GTOS should compute it as a *diagnostic* feature rather than as a primary gate. Connects to E24/E26 microstructure null verdict.
- **Hypothesis (H19):** VPIN computed on XAUUSD MT5 ticks adds <0.02 AUC to a K54 model that already includes realized volatility and tick volume (i.e., AB's mechanical-correlation argument replicates).
- **Cross-domain:** 05 (regime, null); 19 (feature evaluation methodology).
- **Data source:** E-mini S&P500 ES futures, 2008-2011.

#### 06-20 Low-Latency Trading
- **Authors / year:** Hasbrouck J. & Saar G., 2013
- **Source:** Journal of Financial Markets 16(4) 646-679
- **URL:** https://pages.stern.nyu.edu/~jhasbrou/Research/lowLatencyTrading/lowLatencyTradingHasbrouckSaarJFM.pdf
- **Abstract:** Proposes new measure of low-latency activity to study HFT impact on market quality; measure highly correlated with NASDAQ-constructed HFT estimates and computable from widely-available message data.
- **Key findings:** Increased low-latency activity improves market quality (lowers short-term volatility, decreases spreads, increases displayed depth); effect persists during stress periods (October 2008); LLT is a market-quality benefit not a cost in normal regimes.
- **Relevance to GTOS:** Tempers the negative HFT framing — for retail-size GTOS orders, HFT presence likely *improves* fill quality on US30/NAS100 by tightening spreads. Argues against attributing all spread widening to "HFT predation" and toward Ho-Stoll inventory theory.
- **Hypothesis (H20):** US30 / NAS100 effective spread on MT5 is tighter during peak HFT-active periods (US cash hours) than during overnight, supporting Hasbrouck-Saar prediction.
- **Cross-domain:** 12 (indices); 16 (vol); 21 (TCA).
- **Data source:** NASDAQ ITCH message data, 2007-2008.

#### 06-21 Cross-Impact of Order Flow Imbalance in Equity Markets
- **Authors / year:** Cont R. & Cucuringu M. & Zhang C., 2023
- **Source:** Quantitative Finance 23(10) 1373-1393; arXiv:2112.13213
- **URL:** https://arxiv.org/abs/2112.13213
- **Abstract:** Investigates impact of order flow imbalance (OFI) on price movements in a multi-asset setting; proposes integrating OFIs at top levels of the LOB into an integrated OFI variable that better explains price impact than best-level OFI.
- **Key findings:** Multi-level OFI integration adds R^2 over best-level OFI; once multi-level info is integrated, multi-asset cross-impact terms add no contemporaneous explanatory power (sparse model adequate); cross-impact is mostly a top-level multi-asset OFI artifact.
- **Relevance to GTOS:** Directly informs how to construct OFI features for K54: use multi-level OFI not just best-level; cross-impact can be parsimonious. Links to the GTOS cross-instrument correlation gate — OFI cross-impact is small once you control for own-OFI multi-level.
- **Hypothesis (H21):** A multi-level OFI feature (top-5 levels weighted) on XAUUSD ticks predicts 5-min returns with R^2 >= 0.30; cross-instrument OFI from US30 adds <0.03 R^2 once XAUUSD multi-level OFI is included.
- **Cross-domain:** 13 (cross-asset); 19 (ML feature design).
- **Data source:** NASDAQ ITCH multi-stock 2017.

#### 06-22 Trades, Quotes and Prices: Financial Markets Under the Microscope (book)
- **Authors / year:** Bouchaud J.-P. & Bonart J. & Donier J. & Gould M., 2018
- **Source:** Cambridge University Press, 466 pp.
- **URL:** https://www.cambridge.org/core/books/trades-quotes-and-prices/029A71078EE4C41C0D5D4574211AB1B5
- **Abstract:** Comprehensive treatment of empirical microstructure; bridges micro-scale order arrivals to macro-scale market stability; calibrated and evaluated using NASDAQ ITCH data; covers limit-order books, clustering, price impact, adverse selection, liquidity provision, and practical algorithmic trading consequences.
- **Key findings:** Survey + new results: long memory of order flow, propagator framework for impact, square-root impact law, fragility of liquidity, fair-pricing constraints; Bouchaud school synthesis up to 2018.
- **Relevance to GTOS:** Single best one-stop reference for all empirical microstructure facts that GTOS K54/feature design should respect. Includes practical chapter on optimal trading consistent with Almgren-Chriss + propagator dynamics.
- **Hypothesis (H22):** Bouchaud-school propagator decay rate measured from XAUUSD MT5 ticks falls in [0.4, 0.7] power-law exponent range, matching equity-market literature (testable on data/historical_2026/ if M1 ticks reconstructable).
- **Cross-domain:** 03 (long memory); 07 (propagator-as-OB); 21 (TCA).
- **Data source:** NASDAQ ITCH + literature synthesis.

#### 06-23 Algorithmic and High-Frequency Trading (book)
- **Authors / year:** Cartea A. & Jaimungal S. & Penalva J., 2015
- **Source:** Cambridge University Press, 360 pp.
- **URL:** https://www.cambridge.org/core/books/algorithmic-and-highfrequency-trading/3F40579CA4D55F0EE57DC9B11EF89A28
- **Abstract:** First textbook combining sophisticated mathematical modelling, empirical facts, and financial economics for algorithmic trading; develops models for executing large orders, market making, VWAP/schedule-targeting, pairs/baskets, and dark-pool execution.
- **Key findings:** Stochastic-control framework for HFT-MM; explicit closed-form Avellaneda-Stoikov successors with adverse-selection extensions; regime-switching extensions; optimal-execution under various impact specifications; unified treatment of microstructure and stochastic calculus.
- **Relevance to GTOS:** Operational textbook reference for K54 feature engineering and any future algorithmic-execution layer in `execution.py`. Particularly the adverse-selection-aware MM models inform a sophisticated micro-price computation.
- **Hypothesis (H23):** A Cartea-Jaimungal-style adverse-selection-aware micro-price (mid + delta * (bid_depth - ask_depth)) at OB-retest entry predicts realized R better than naive mid-price for XAUUSD.
- **Cross-domain:** 19 (ML); 21 (TCA); 20 (RL).
- **Data source:** Multi-venue equity TAQ + literature synthesis.

#### 06-24 Market Microstructure In Practice (book, 2nd ed)
- **Authors / year:** Lehalle C.-A. & Laruelle S., 2018
- **Source:** World Scientific, 2nd edition
- **URL:** https://www.worldscientific.com/worldscibooks/10.1142/10739
- **Abstract:** Practitioner-academic synthesis covering Reg NMS, MiFID/MiFID2 consequences for market microstructure; second edition adds large section on order-book dynamics (liquidity predicting price moves), updated impact section, dark pools, circuit breakers, fixed-income electronification.
- **Key findings:** Liquidity is predictive of future price moves; pressure-relaxation framework for impact; Smart Order Routing principles; trade-scheduling algorithm design; fragility analysis of HFT-dominated markets; extension to fixed income.
- **Relevance to GTOS:** Practitioner-grade reference that bridges Bouchaud-school theory with GTOS-style execution constraints. The "liquidity predicts price moves" content directly aligns with the GTOS hypothesis that depth at OB level predicts retest outcome.
- **Hypothesis (H24):** Pre-OB-retest liquidity score (effective depth at OB level) is positively correlated with retest WR (testable via spread*volume proxy if depth not directly available).
- **Cross-domain:** 12 (indices); 11 (FX); 21 (TCA).
- **Data source:** Practitioner data from CA-CIB / Capital Fund Management.

#### 06-25 Liquidity and Market Efficiency
- **Authors / year:** Chordia T. & Roll R. & Subrahmanyam A., 2008
- **Source:** Journal of Financial Economics 87(2) 249-268
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S0304405X07001833
- **Abstract:** Analyzes short-horizon predictability of returns from past order flows as an inverse indicator of market efficiency for NYSE stocks 1993-2002; documents that liquidity stimulates arbitrage activity and enhances market efficiency.
- **Key findings:** Mid-quote return predictability falls when bid-ask spreads narrow; predictability has declined over time with minimum tick size; arbitrage activity is bound by liquidity; efficiency is endogenous to liquidity.
- **Relevance to GTOS:** Order-flow predictability is *higher* in less-liquid windows. Suggests GTOS edge may be larger during low-liquidity Asian session and overnight than during peak liquidity. Connects to F2 finding that XAUUSD trending_bull regime decay was concentrated in London/NY session.
- **Hypothesis (H25):** Per-instrument 5-min OFI->return predictability (R^2) is inversely correlated with spread/vol-normalized liquidity score; ranking by liquidity, illiquid quartile shows R^2 >= 2x liquid-quartile R^2.
- **Cross-domain:** 13 (cross-asset commonality); 02 (predictability tests); 16 (vol).
- **Data source:** NYSE TAQ 1993-2002.

#### 06-26 Autoregressive Conditional Duration: A New Model for Irregularly Spaced Transaction Data
- **Authors / year:** Engle R.F. & Russell J.R., 1998
- **Source:** Econometrica 66(5) 1127-1162
- **URL:** https://www.jstor.org/stable/2999632
- **Abstract:** Develops the Autoregressive Conditional Duration (ACD) model for inter-trade durations in a way analogous to GARCH for returns; explicit goal is to model time and events when transaction times are irregularly spaced.
- **Key findings:** ACD captures duration clustering; longer durations persist after long durations and shorter after short; informational content of durations linked to PIN (informed trades cluster, shortening durations); foundation for high-frequency duration modeling.
- **Relevance to GTOS:** The duration between MT5 ticks is itself informative — long inter-tick durations on XAUUSD signal liquidity vacuums and may predict imminent moves. ACD-style features could augment K54 beyond purely return-based features.
- **Hypothesis (H26):** A rolling ACD-residual (standardized duration shock) on XAUUSD MT5 ticks above its 95th percentile predicts >=0.5R adverse moves within 4 M15 bars.
- **Cross-domain:** 03 (heteroskedasticity in time); 19 (duration as feature); 05 (regime via duration).
- **Data source:** NYSE IBM, 1990-1991.

#### 06-27 Direct Estimation of Equity Market Impact
- **Authors / year:** Almgren R. & Thum C. & Hauptmann E. & Li H., 2005
- **Source:** Risk 18(7) 58-62
- **URL:** https://www.cis.upenn.edu/~mkearns/finread/costestim.pdf
- **Abstract:** Analyzes a large data set from Citigroup US equity trading desks to fit market-impact model coefficients across stocks; rejects the common square-root model for temporary impact in favor of a 3/5 power law.
- **Key findings:** Permanent impact ~ linear; temporary impact ~ block-size^(3/5); impact coefficients depend on volatility, average daily volume, turnover; first big-data empirical impact study in equities.
- **Relevance to GTOS:** **Contrarian / refines** — challenges the canonical sqrt-impact law (Almgren 2003 H12) with empirical 3/5 exponent. For per-instrument FN slippage modeling, allows a more accurate sizing-cost curve. Essential calibration target for any future RL execution agent.
- **Hypothesis (H27):** Per-instrument FN slippage exponent (regressing log-slip on log-size) lies in [0.5, 0.7] range matching Almgren-Thum 3/5 finding rather than the pure sqrt law.
- **Cross-domain:** 21 (sizing); 03 (power laws); 20 (RL execution).
- **Data source:** Citigroup proprietary equity trading-desk data, 700,000 orders.

#### 06-28 Market Microstructure: A Survey
- **Authors / year:** Madhavan A., 2000
- **Source:** Journal of Financial Markets 3(3) 205-258
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S1386418100000070
- **Abstract:** Surveys theoretical, empirical, and experimental microstructure literature relating to (1) price formation, (2) market structure and design, (3) transparency, and (4) applications to other areas of finance.
- **Key findings:** Comprehensive taxonomy of inventory vs information models; market design implications; transparency-liquidity tradeoffs; microstructure connections to asset pricing.
- **Relevance to GTOS:** Single-paper reference for the entire microstructure literature pre-2000. Useful as the citation anchor for GTOS literature reviews and as a sanity check that K54 feature design is not missing a known theoretical mechanism.
- **Cross-domain:** All sub-domains.
- **Data source:** Literature synthesis.

#### 06-29 Measuring the Information Content of Stock Trades
- **Authors / year:** Hasbrouck J., 1991
- **Source:** Journal of Finance 46(1) 179-207
- **URL:** https://www.acsu.buffalo.edu/~keechung/MGF743/Readings/K2.pdf
- **Abstract:** Models trades and quote revisions as a vector autoregressive system; trade information effect measured as ultimate price impact of the trade innovation.
- **Key findings:** Trade's full price impact arrives only with protracted lag; impact is positive and concave function of trade size; large trades cause spread to widen; foundation for VAR-based microstructure decomposition.
- **Relevance to GTOS:** The Hasbrouck 1991 VAR framework explains why GTOS' Pre-AI gate "displacement_quality_score" matters: a high-quality displacement is one whose impact has *not* yet decayed, leaving residual signal for the OB retest. K50/K54 should incorporate VAR-residual-style impact features.
- **Hypothesis (H29):** A Hasbrouck VAR fitted on XAUUSD M1 returns + signed-volume gives an impulse-response-function whose 60-min cumulative response correlates r >= 0.3 with 4-bar M15 forward return at OB retests.
- **Cross-domain:** 02 (VAR inference); 03 (impulse response).
- **Data source:** NYSE TAQ, 1989.

#### 06-30 A Stochastic Model for Order Book Dynamics
- **Authors / year:** Cont R. & Stoikov S. & Talreja R., 2010
- **Source:** Operations Research 58(3) 549-563
- **URL:** http://rama.cont.perso.math.cnrs.fr/pdf/CST2010.pdf
- **Abstract:** Continuous-time stochastic model for limit-order-book dynamics balancing data-driven calibration, empirical-property capture, and analytical tractability; uses Laplace-transform methods to compute conditional probabilities of book events without simulation.
- **Key findings:** Birth-death-process model where bids/asks arrive Poissonly; closed-form probabilities of midprice up-tick, ask-execution-before-ask-move, paired buy-sell at quotes; estimable from L1 quote data; Tokyo Stock Exchange empirical validation.
- **Relevance to GTOS:** Birth-death-process framework can be calibrated to MT5 ticks and used to estimate per-instrument conditional probabilities — useful for K54 features and for principled spread-and-OFI signals. Avoids the depth-data limitations of MT5.
- **Hypothesis (H30):** A Cont-Stoikov-Talreja BDP fitted on XAUUSD MT5 ticks (using bid/ask change events) yields midprice-up probabilities that improve K54 OOS calibration AUC by >=0.02 vs no-BDP baseline.
- **Cross-domain:** 02 (Markov inference); 19 (Bayesian feature for K54).
- **Data source:** Tokyo Stock Exchange tick data.

#### 06-31 Anomalous Price Impact and the Critical Nature of Liquidity in Financial Markets
- **Authors / year:** Toth B. & Lemperiere Y. & Deremble C. & de Lataillade J. & Kockelkoren J. & Bouchaud J.-P., 2011
- **Source:** Physical Review X 1 021006; arXiv:1105.1694
- **URL:** https://arxiv.org/abs/1105.1694
- **Abstract:** Proposes a dynamical theory of market liquidity predicting that the average supply/demand profile is V-shaped and vanishes around the current price; relies only on mild assumptions about order flow and on (approximate) price diffusion.
- **Key findings:** V-shaped liquidity profile around mid; this shape produces the square-root impact law for meta-orders via fragmentation arguments; long-memory order flow is a *consequence* of liquidity scarcity, not a cause; explains why local impact is anomalously large.
- **Relevance to GTOS:** **Major theoretical result.** The V-shape near mid implies that GTOS' OB-retest entries (which are typically a few bps from mid in the impact direction) interact with a region of *low* liquidity, magnifying slippage. Predicts that ATR-scaled stop buffers are insufficient because impact is concave, not linear.
- **Hypothesis (H31):** XAUUSD MT5 spread/depth profile reconstructed from L1 ticks shows a V-shape near mid with depth scaling roughly linearly with distance to mid; depth at OB retest level is <30% of average M15 depth.
- **Cross-domain:** 03 (square-root law); 21 (sizing); 07 (OB-as-low-liquidity-region).
- **Data source:** CFM proprietary equity meta-orders.

#### 06-32 The Micro-Price: A High-Frequency Estimator of Future Prices
- **Authors / year:** Stoikov S., 2018
- **Source:** Quantitative Finance 18(12) 1959-1966
- **URL:** https://www.tandfonline.com/doi/abs/10.1080/14697688.2018.1489139
- **Abstract:** Studies the joint dynamics of bid/ask queues and the trading process; defines and computes the "micro-price" as the limit of conditional martingale prices; the micro-price is a martingale and less noisy than weighted-mid-price.
- **Key findings:** Micro-price = lim_n E[mid_n | observable state]; explicit recursion with closed-form coefficients; outperforms mid-price and weighted-mid-price as a 1-second-ahead predictor; depends on quote imbalance and spread state.
- **Relevance to GTOS:** **Direct candidate for `tick_features.py` enhancement.** Stoikov micro-price can replace naive (bid+ask)/2 in GTOS evaluation — simple Python implementation, deterministic, and theoretically principled. Likely to improve OB-retest entry-price quality by a small but consistent margin.
- **Hypothesis (H32):** A Stoikov micro-price computed on XAUUSD MT5 ticks at OB-retest entry has lower 1-bar (M15) prediction RMSE than naive mid-price by >=10%.
- **Cross-domain:** 19 (feature for K54); 02 (martingale construction).
- **Data source:** NASDAQ ITCH, multi-stock.

#### 06-33 Is the Electronic Open Limit Order Book Inevitable?
- **Authors / year:** Glosten L.R., 1994
- **Source:** Journal of Finance 49(4) 1127-1161
- **URL:** https://www.edegan.com/pdfs/Glosten%20(1994)%20-%20Is%20the%20Electronic%20Open%20limit%20Order%20Book%20Inevitable.pdf
- **Abstract:** Derives the equilibrium price schedule determined by the bids and offers in an open limit order book under fairly general conditions; shows that the LOB has small-trade positive bid-ask spread and that limit orders profit from small trades.
- **Key findings:** Electronic LOB provides as much liquidity as possible in extreme situations (worst-case competitive); LOB does not invite competition from third-market dealers; consolidated price schedule matches LOB price schedule under nonnegative trading profits.
- **Relevance to GTOS:** Theoretical foundation for why electronic order books (and thus the venues underlying MT5 broker quotes) converge to LOB-style price schedules. Justifies treating MT5 ticks as approximations to a venue LOB rather than independent dealer markets — supports applying lit-LOB literature to GTOS.
- **Hypothesis (H33):** The implied LOB price schedule reconstructed from MT5 spread time-series for XAUUSD is consistent with Glosten 1994 small-trade positive-spread predictions (i.e., effective bid-ask widens monotonically with notional size) — testable across order-size buckets.
- **Cross-domain:** 02 (equilibrium); 12 (indices).
- **Data source:** Theoretical.

#### 06-34 An Empirical Behavioral Model of Liquidity and Volatility (Mike-Farmer)
- **Authors / year:** Mike S. & Farmer J.D., 2008
- **Source:** Journal of Economic Dynamics and Control 32(1) 200-234
- **URL:** https://ideas.repec.org/a/eee/dyncon/v32y2008i1p200-234.html
- **Abstract:** Develops a behavioral model for liquidity and volatility based on empirical regularities in trading order flow on the London Stock Exchange; viewed as a simple agent-based model with all components validated against real data.
- **Key findings:** Three ingredients: long-memory of order signs (Hurst index), Student-t distribution of relative limit-order prices, dynamics of order cancellations; reproduces full distribution of returns including fat tails; outperforms zero-intelligence baselines.
- **Relevance to GTOS:** Bridges domain 06 (microstructure) with domain 03 (distributional findings); the Mike-Farmer model produces fat-tailed returns from microstructural mechanisms, consistent with the GTOS distributional ξ=0.35 finding. Suggests GTOS' fat tails may be partially attributable to OB cancellation dynamics.
- **Hypothesis (H34):** Order-cancellation rate proxy on XAUUSD MT5 ticks (rate of inside-quote-revisions) correlates with realized 1-min vol at lag 0-5 min, consistent with Mike-Farmer cancellation-driven volatility mechanism.
- **Cross-domain:** 03 (fat tails as microstructure consequence); 16 (vol).
- **Data source:** LSE SETS data.

#### 06-35 Limit Order Books (survey)
- **Authors / year:** Gould M.D. & Porter M.A. & Williams S. & McDonald M. & Fenn D.J. & Howison S.D., 2013
- **Source:** Quantitative Finance 13(11) 1709-1742
- **URL:** https://arxiv.org/abs/1012.0349
- **Abstract:** Survey of empirical and theoretical LOB literature; LOBs match buyers/sellers in more than half of the world's financial markets; examines findings from statistical analyses of historical LOB data and how various LOB models provide insight.
- **Key findings:** Comprehensive taxonomy of LOB models (zero-intelligence, queueing, agent-based); many models poorly resemble real LOBs; several well-established empirical facts (long memory, square-root impact, queue dynamics) yet to be reproduced satisfactorily by parsimonious models.
- **Relevance to GTOS:** Single best-effort tutorial for engineers building K54 features that respect LOB realities. Authors' criterion of "model fits stylized facts" is the test GTOS should apply when proposing new microstructure features.
- **Cross-domain:** Survey — links to 03 (long memory), 19 (modeling).
- **Data source:** Literature synthesis.

#### 06-36 A Fully Consistent, Minimal Model for Non-Linear Market Impact
- **Authors / year:** Donier J. & Bonart J. & Mastromatteo I. & Bouchaud J.-P., 2015
- **Source:** Quantitative Finance 15(7) 1109-1121; arXiv:1412.0141
- **URL:** https://arxiv.org/abs/1412.0141
- **Abstract:** Proposes a minimal theory of non-linear price impact based on a linear (latent) order-book approximation, inspired by diffusion-reaction models; computes average price trajectory in presence of a meta-order; accounts for square-root impact law; predicts non-trivial trajectories when trading is interrupted or reversed.
- **Key findings:** Decomposes price into a transient mechanical impact and a permanent informational component; framework is free of price manipulation; predicts impact reversal after trade halt; recovers Toth-Bouchaud V-shaped liquidity from independent diffusion-reaction principles.
- **Relevance to GTOS:** Explains the *time-decay* of OB validity rigorously — once the meta-order's mechanical impact dissipates, only the informational component remains, and only if the informational shock has not yet been resolved. K54 should distinguish "fresh" OBs (mechanical-dominant) from "aged" OBs (informational-dominant).
- **Hypothesis (H36):** Per-instrument OB-retest WR has bimodal time-since-formation profile — high for very recent (mechanical) and stable for very old (informational), with a trough in between (mechanical-dissipated, informational-not-yet-confirmed).
- **Cross-domain:** 03 (long memory); 21 (sizing).
- **Data source:** Theoretical with CFM data calibration.

#### 06-37 Statistical Modeling of High Frequency Financial Data: Facts, Models and Challenges
- **Authors / year:** Cont R., 2011
- **Source:** IEEE Signal Processing Magazine 28(5) 16-25
- **URL:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1748022
- **Abstract:** Reviews statistical modeling techniques for high-frequency transactions, quotes, and order-flow data; covers order-book dynamics, market microstructure, queueing systems, transaction data, trades and quotes, and price impact.
- **Key findings:** Surveys discrete-time tick data models, point-process models (Hawkes), microstructure-noise estimators; identifies challenges in volatility estimation, sub-sampling bias, model adequacy testing.
- **Relevance to GTOS:** Useful tutorial for justifying the choice of M15 aggregation (subsampling) vs tick-level features in GTOS; addresses the M15 microstructure null verdict from a methodological standpoint.
- **Cross-domain:** 02 (sampling); 19 (HF features); survey.
- **Data source:** Literature synthesis.

#### 06-38 Deep Order Flow Imbalance: Extracting Alpha at Multiple Horizons from the Limit Order Book
- **Authors / year:** Kolm P.N. & Turiel J. & Westray N., 2023
- **Source:** Mathematical Finance 33(4) 1044-1081
- **URL:** https://onlinelibrary.wiley.com/doi/10.1111/mafi.12413
- **Abstract:** Employs deep learning to forecast high-frequency returns at multiple horizons for 115 NASDAQ stocks using granular order-book information; finds that off-the-shelf neural nets trained on stationary OFI inputs outperform models trained on raw order books.
- **Key findings:** OFI features beat raw LOB inputs for deep-learning models; cross-sectional regression links forecasting performance to stock microstructure (information-rich stocks more predictable); effective horizon ~ two average price changes.
- **Relevance to GTOS:** **Direct K54 design implication:** preprocess MT5 ticks into OFI-style stationary features rather than feeding raw spread/volume series. Confirms Cont-Kukanov-Stoikov's hypothesis empirically with deep learning; horizon ~ 2 price changes is a quantitative anchor for OOS evaluation windows.
- **Hypothesis (H38):** A K54 LSTM trained on OFI features beats one trained on raw spread+volume features by >=0.03 OOS AUC on XAUUSD M15 R-classification.
- **Cross-domain:** 19 (LSTM); 13 (multi-stock universality).
- **Data source:** NASDAQ ITCH, 115 stocks, 2013-2018.

#### 06-39 Universal Features of Price Formation in Financial Markets: Perspectives from Deep Learning
- **Authors / year:** Sirignano J. & Cont R., 2019
- **Source:** Quantitative Finance 19(9) 1449-1459
- **URL:** http://rama.cont.perso.math.cnrs.fr/pdf/SirignanoCont2019.pdf
- **Abstract:** Large-scale deep learning approach applied to high-frequency database (billions of electronic market quotes and transactions for US equities); uncovers nonparametric evidence for a universal and stationary price-formation mechanism relating supply/demand dynamics to subsequent price variations.
- **Key findings:** Universal LSTM model trained on all stocks outperforms asset-specific models OOS; relations captured are universal not asset-specific; OOS prediction stable across time and stocks; model generalizes to unseen stocks.
- **Relevance to GTOS:** Strongest empirical evidence for *universality* — supports pooling MT5 tick data across XAUUSD/US30/USDJPY/GBPJPY/GBPUSD/XAGUSD/NAS100 for a single K54 model rather than per-instrument models. Drastically reduces data-sparsity concerns.
- **Hypothesis (H39):** A K54 model trained on pooled multi-instrument MT5 features (with instrument-id embedding) achieves lower median OOS log-loss than 7 per-instrument K54 models, replicating Sirignano-Cont universality.
- **Cross-domain:** 19 (deep learning); 13 (universality across instruments).
- **Data source:** NASDAQ ITCH + NYSE TAQ, 489 stocks, 2014-2017.

#### 06-40 DeepLOB: Deep Convolutional Neural Networks for Limit Order Books
- **Authors / year:** Zhang Z. & Zohren S. & Roberts S., 2019
- **Source:** IEEE Transactions on Signal Processing 67(11) 3001-3012
- **URL:** https://arxiv.org/abs/1808.03668
- **Abstract:** Develops a large-scale deep learning model to predict price movements from LOB data of cash equities; architecture uses convolutional filters for spatial structure and LSTM modules for temporal dependencies; tested on one year of LSE quotes.
- **Key findings:** Model translates well to instruments not in training set (universality echo of Sirignano-Cont); state-of-the-art on benchmark FI-2010 LOB dataset; specific Conv+Inception+LSTM architecture remains a strong baseline.
- **Relevance to GTOS:** Reference architecture for any future K54 deep-LOB extension. The model's universality finding supports H39 above. Provides a public benchmark (FI-2010) for evaluating GTOS feature pipelines.
- **Hypothesis (H40):** A DeepLOB-style Conv+LSTM trained on XAUUSD/US30/USDJPY MT5 micro-features (bin-aggregated to 1s) achieves OOS Spearman rho >=0.10 on M15 R prediction.
- **Cross-domain:** 19 (CNN+LSTM); 13 (universality).
- **Data source:** LSE message data + FI-2010 benchmark.

#### 06-41 Deep Limit Order Book Forecasting (microstructural guide)
- **Authors / year:** Briola A. & Bartolucci S. & Aste T., 2024
- **Source:** Quantitative Finance (in press); arXiv:2403.09267
- **URL:** https://arxiv.org/abs/2403.09267
- **Abstract:** Releases LOBFrame, an open-source code base for processing large-scale LOB data and benchmarking deep learning models; demonstrates that high forecasting accuracy does not necessarily correspond to actionable trading signals; proposes operational evaluation framework focused on probability of complete-transaction forecasting.
- **Key findings:** Microstructural characteristics influence deep-learning efficacy (illiquid stocks harder); traditional ML metrics fail to capture trading-relevance; introduces "actionable signal" evaluation; LOBFrame is a reproducible benchmark.
- **Relevance to GTOS:** **Critical methodological warning** for K54 evaluation — high AUC does not translate to high realized R. Anchors GTOS' insistence on realized-R-based evaluation (memory `feedback_walk_level_evidence_not_predictive`). LOBFrame benchmark could be reused for sanity-checking K54 architectures.
- **Hypothesis (H41):** A K54 model with high OOS AUC (>=0.65) but low realized-R lift (<0.05R) is detectable a priori by Briola-style operational metrics (probability of correctly forecasting a complete TP-or-SL outcome).
- **Cross-domain:** 19 (deep LOB); 02 (evaluation methodology).
- **Data source:** NASDAQ ITCH (LOBFrame benchmark).

#### 06-42 The Market Microstructure Approach to Foreign Exchange: Looking Back and Looking Forward
- **Authors / year:** King M.R. & Osler C.L. & Rime D., 2013
- **Source:** Journal of International Money and Finance 38 95-119
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S0261560613000594
- **Abstract:** Survey of FX microstructure literature documenting how the field has evolved from Lyons-style dealer studies to high-frequency electronic-market analyses; reviews order-flow-and-exchange-rate findings, FX dealer behavior, and policy/intervention questions.
- **Key findings:** Order flow effect on FX rates is robust across decades and markets; FX microstructure is increasingly electronic (EBS, Reuters Matching); HFT in FX is more constrained than in equities; central-bank intervention works partly through dealer-microstructure channel.
- **Relevance to GTOS:** Single-paper update on FX microstructure for the four FX instruments (USDJPY/GBPJPY/GBPUSD); useful overview for justifying inclusion of OFI features in K54 for FX.
- **Cross-domain:** 11 (FX); survey.
- **Data source:** Literature synthesis.

#### 06-43 Tick Size Reduction and Price Clustering in a FX Order Book
- **Authors / year:** Lallouache M. & Abergel F., 2014
- **Source:** Physica A 416 488-498
- **URL:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2297292
- **Abstract:** Investigates statistical properties of EBS order book for EUR/USD and USD/JPY; examines impact of a ten-fold tick size reduction on book dynamics, price clustering, and order placement.
- **Key findings:** Tick-size reduction caused dramatic increase in price-level clustering; order placement distribution shifted toward off-best-quote levels; Hill estimator of return tail index unchanged; depth at best level decreased by ~50%.
- **Relevance to GTOS:** Direct empirical evidence on EBS USD/JPY microstructure — relevant to USDJPY tick_size precision concerns from S79 / sister precision-bug fixes. The paper's tick-size sensitivity finding is a cautionary tale for any GTOS broker-tick-size assumption.
- **Hypothesis (H43):** USDJPY MT5 tick-size-normalized order placement distribution matches EBS Lallouache-Abergel pattern (peaked at best, exponential decay away), within 20% in both shape and scale.
- **Cross-domain:** 11 (FX); 03 (clustering).
- **Data source:** EBS EUR/USD + USD/JPY tick data, 2009.

#### 06-44 Stop-Loss Orders and Price Cascades in Currency Markets
- **Authors / year:** Osler C.L., 2005 (working 2003)
- **Source:** Journal of International Money and Finance 24(2) 219-241
- **URL:** https://faculty.georgetown.edu/evansm1/New%20Micro/osler1.pdf
- **Abstract:** Documents clustering of stop-loss and take-profit orders at NatWest Markets in three currency pairs (USDJPY, GBPUSD, EURUSD) Aug-1999 to Apr-2000; tests whether stop-loss execution rates cluster at round numbers and whether such clustering can drive price cascades.
- **Key findings:** Take-profit and stop-loss orders cluster at round numbers; executed stop-loss buy orders cluster *just above* round numbers; executed stop-loss sell orders cluster *just below*; trends reverse at predictable support/resistance levels and accelerate after rates cross them — empirically validating technical analysis predictions.
- **Relevance to GTOS:** **Critical FX-specific finding.** Provides a microstructure mechanism for the round-number magnetism (domain 09) seen on USDJPY, GBPJPY, GBPUSD. Justifies GTOS' liquidity-distance shadow logger and supports a stop-loss clustering feature for K54 (cluster a few ticks above/below round numbers).
- **Hypothesis (H44):** USDJPY MT5 stop-loss density (proxy: minute-level realized vol after small price moves) is elevated within +/-3 ticks of round numbers (xx.00 levels) by >=30% above non-round areas, replicating Osler's NatWest pattern.
- **Cross-domain:** 09 (round-number magnetism); 11 (FX); 18 (stop-cascade psychology).
- **Data source:** NatWest Markets internal stop/TP order book, 1999-2000.

#### 06-45 A Dynamic Model of the Limit Order Book
- **Authors / year:** Rosu I., 2009
- **Source:** Review of Financial Studies 22(11) 4601-4641
- **URL:** https://people.hec.edu/rosu/wp-content/uploads/sites/43/2020/03/limit_RFS_2009.pdf
- **Abstract:** Order-driven market with fully strategic, symmetrically informed liquidity traders dynamically choosing between limit and market orders; trade off execution price and waiting costs.
- **Key findings:** Higher trading activity / competition compress spreads + lower price impact; market orders cause temporary price impact larger than permanent (overshooting); humped book shape from clustering of orders away from spread; bid-ask comovement (spread widens after market order); fleeting limit orders when book is full.
- **Relevance to GTOS:** Theoretical bridge between Glosten-Milgrom adverse selection and Bouchaud-school empirical findings. The "overshooting" prediction directly supports the GTOS hypothesis that OB-retest entries (which exploit overshooting reversion) carry edge.
- **Hypothesis (H45):** XAUUSD M1 returns following a 4-sigma+ M15 displacement show statistically significant mean-reversion at 5-min horizon (testing Rosu overshooting), with effect size >= 0.10 sigma.
- **Cross-domain:** 02 (game theory); 07 (overshooting=OB mechanism).
- **Data source:** Theoretical.

#### 06-46 Does Algorithmic Trading Improve Liquidity?
- **Authors / year:** Hendershott T. & Jones C.M. & Menkveld A.J., 2011
- **Source:** Journal of Finance 66(1) 1-33
- **URL:** https://faculty.haas.berkeley.edu/hender/Algo.pdf
- **Abstract:** First causal analysis of algorithmic trading effect on liquidity, using NYSE 2003 automation of quote dissemination as exogenous instrument; algorithmic trading narrows spreads, reduces adverse selection, reduces trade-related price discovery (for large stocks).
- **Key findings:** Causal effect of AT on liquidity is positive (spreads narrow, AS falls); effect concentrated in large stocks; consistent with AT acting as efficient market makers; AT improves quote informativeness.
- **Relevance to GTOS:** Establishes that algorithmic trading is a *liquidity provider* not just a taker — supports the view that MT5 broker quotes (which aggregate AT-tightened spreads from upstream venues) provide cleaner edge than retail-only environments. Important counter-evidence to the "HFT toxicity" framing.
- **Hypothesis (H46):** Per-instrument MT5 effective spread is tighter (>=10%) during NYSE/CME peak AT-active hours than during overnight, replicating Hendershott-Jones-Menkveld finding.
- **Cross-domain:** 12 (indices); 21 (TCA).
- **Data source:** NYSE TAQ + NYSE-internal AT measures, 2001-2005.

#### 06-47 High-Frequency Trading and Price Discovery
- **Authors / year:** Brogaard J. & Hendershott T. & Riordan R., 2014
- **Source:** Review of Financial Studies 27(8) 2267-2306
- **URL:** https://academic.oup.com/rfs/article-abstract/27/8/2267/1582754
- **Abstract:** Examines HFTs' role in price discovery and price efficiency; HFTs trade in direction of permanent price changes and opposite direction of transitory pricing errors, both on average and on highest-volatility days.
- **Key findings:** HFT liquidity-demanding orders facilitate price efficiency (informed-direction); HFT liquidity-supplying orders are adversely selected; HFT direction predicts price changes over short horizons (seconds).
- **Relevance to GTOS:** Mechanism for the OB-retest edge: if HFTs trade in the direction of *permanent* price changes (i.e., real informational shocks), then the OB they leave behind should mark the location of an informational shock, which the M15-resolution GTOS framework exploits via retest.
- **Hypothesis (H47):** XAUUSD MT5 ticks containing >75th-percentile signed volume in the 5-min window before OB formation predict higher OB-retest WR (>=5pp uplift), consistent with Brogaard et al's HFT-as-informed-trader finding.
- **Cross-domain:** 07 (HFT-as-OB-creator); 19 (signed-volume feature).
- **Data source:** NASDAQ HFT-flagged dataset, 2008-2009 + 2010.

#### 06-48 The Diversity of High-Frequency Traders
- **Authors / year:** Hagstromer B. & Norden L., 2013
- **Source:** Journal of Financial Markets 16(4) 741-770
- **URL:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2153272
- **Abstract:** Distinguishes market-making HFTs from opportunistic HFTs using NASDAQ-OMX Stockholm data; emphasizes regulatory importance of strategy heterogeneity.
- **Key findings:** Market-making HFTs are 63-72% of HFT volume and 81-86% of limit-order traffic; market makers have higher order-to-trade ratios and lower latency than opportunistic HFTs; treating HFT as monolithic obscures crucial heterogeneity.
- **Relevance to GTOS:** Reminds GTOS analysts that "HFT" is not a single strategy. GTOS' OB construct primarily captures *opportunistic* HFT footprint (directional informed orders) rather than market-making HFT. Supports filtering OB candidates by 1-min realized volume signature.
- **Cross-domain:** 12 (indices); 19 (feature taxonomy).
- **Data source:** NASDAQ-OMX Stockholm flagged HFT data, 2010-2011.

#### 06-49 High Frequency Trading and Extreme Price Movements
- **Authors / year:** Brogaard J. & Carrion A. & Moyaert T. & Riordan R. & Shkilko A. & Sokolov K., 2018
- **Source:** Journal of Financial Economics 128(2) 253-265
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S0304405X18300278
- **Abstract:** Studies HFT activity around extreme price movements (EPMs); on average HFTs provide liquidity during EPMs in single stocks by absorbing nHFT imbalances; for simultaneous multi-stock EPMs, HFT liquidity *demand* dominates supply.
- **Key findings:** Single-stock EPMs: HFTs are net liquidity providers; multi-stock EPMs: HFTs become liquidity consumers (cascade-amplifier role); little evidence of HFT *causing* EPMs.
- **Relevance to GTOS:** **Operationally critical** for US30/NAS100 stress events. The paper's finding that HFTs flip from supply to demand during *simultaneous* multi-instrument EPMs informs the GTOS cross-instrument correlation gate — an EPM in US30+NAS100 simultaneously is a much more dangerous regime than either alone.
- **Hypothesis (H49):** A correlation-aware gate that triggers on simultaneous 4-sigma+ EPMs in 2 of {US30, NAS100, XAUUSD} M15 bars within 30 min predicts >=30% reduction in 1-hour realized R for any new entry.
- **Cross-domain:** 12 (indices); 13 (cross-instrument cascade); 21 (kill switch).
- **Data source:** NASDAQ HFT-flagged + Trade Reporting Facility, 2010-2014.

#### 06-50 Optimal Control of Execution Costs
- **Authors / year:** Bertsimas D. & Lo A.W., 1998
- **Source:** Journal of Financial Markets 1(1) 1-50
- **URL:** https://www.mit.edu/~dbertsim/papers/Finance/Optimal%20control%20of%20execution%20costs.pdf
- **Abstract:** Derives dynamic optimal trading strategies that minimize the expected cost of trading a large equity block over a fixed time horizon; given a price-impact function and finite periods, obtains the best-execution sequence as a closed-form function of market conditions.
- **Key findings:** Closed-form optimal sequence under linear-impact assumption; risk-neutral solution = uniform schedule; portfolio extension where cross-impact matters; foundational predecessor to Almgren-Chriss.
- **Relevance to GTOS:** The Bertsimas-Lo framework supports the GTOS observation that trades sized within liquidity (small lot sizes) have approximately uniform expected cost — important for sizing. For larger sizes, cross-instrument cost matters (relevant to S79 portfolio-policy follow-up).
- **Cross-domain:** 21 (sizing); 20 (RL execution).
- **Data source:** Theoretical with NYSE TAQ illustration.

#### 06-51 Dealer Behavior and Trading Systems in Foreign Exchange Markets
- **Authors / year:** Bjonnes G.H. & Rime D., 2005
- **Source:** Journal of Financial Economics 75(3) 571-605
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S0304405X04001503
- **Abstract:** Studies dealer behavior in spot FX market using detailed observations on all transactions of four interbank dealers; tests information vs inventory effects across direct bilateral, electronic broker, and voice broker channels.
- **Key findings:** Strong support for information effect in incoming trades; trade direction is the primary information signal; effect grows with trade size in direct bilateral trades; all four dealers actively control inventory consistent with Lyons; electronic broker (EBS) trades have lower inventory effect than direct bilateral.
- **Relevance to GTOS:** Most direct evidence for asymmetric information effects in FX dealer markets, providing the *mechanism* for why GTOS' OB construct can carry edge on USDJPY/GBPJPY/GBPUSD: each MT5 tick at a venue level is the aggregation of many dealer-internal information shocks.
- **Hypothesis (H51):** Per-instrument FX OB retests show stronger directional bias on tick-volume-heavy bars (proxy for informed dealer activity) compared to tick-volume-light bars, supporting Bjonnes-Rime mechanism.
- **Cross-domain:** 11 (FX dealer); 02 (regression evidence).
- **Data source:** 4 interbank FX dealers' complete transaction records, 1998.

#### 06-52 Order Flow Imbalances and Amplification of Price Movements: Evidence from U.S. Treasury Markets
- **Authors / year:** Dobrev D. & Liu E. & Kim T. & Rodriguez T., 2025
- **Source:** Federal Reserve FEDS Notes, 2025-11-03
- **URL:** https://www.federalreserve.gov/econres/notes/feds-notes/order-flow-imbalances-and-amplification-of-price-movements-evidence-from-u-s-treasury-markets-20251103.html
- **Abstract:** Analyzes April 2025 Treasury market turbulence around tariff announcements; investigates how order-flow imbalances amplified price movements when liquidity was poor; uses high-frequency on-the-run Treasury and futures data.
- **Key findings:** Comparable liquidity-supply reductions on April 7 and April 9 produced markedly different price impacts because of different OFI magnitudes; OFI-impact relation is nonlinear in stress regimes; Treasury OFI->price relation is amplified at low-liquidity windows.
- **Relevance to GTOS:** **Recent (2025) empirical evidence** that OFI x liquidity is the load-bearing variable for price discovery during stress — directly informs GTOS' approach to GBPUSD overnight thin sessions and gold around news events. Suggests an OFI-stress feature for K54.
- **Hypothesis (H52):** A composite (OFI x 1/liquidity) feature on XAUUSD MT5 ticks predicts intra-bar realized vol better than OFI or liquidity alone (R^2 lift >=0.05).
- **Cross-domain:** 13 (cross-asset); 16 (vol amplification); 21 (kill-switch).
- **Data source:** BrokerTec / CME on-the-run Treasury cash and futures, April 2025.

#### 06-53 Intraday Seasonality in Efficiency, Liquidity, Volatility, and Volume: Platinum and Gold Futures in Tokyo and New York
- **Authors / year:** Kang S.B. & Pan M.-S. & Liu W., 2018
- **Source:** Journal of Commodity Markets (working paper)
- **URL:** https://www.rieti.go.jp/jp/publications/dp/17e120.pdf
- **Abstract:** Compares intraday seasonality of informational efficiency, volatility, volume and liquidity in platinum and gold futures across TOCOM, NYMEX, and COMEX during overlapping trading hours.
- **Key findings:** Tokyo session dominated by uninformed trading (no PIN-significant); New York session shows both uninformed and informed trading; informed trading dominates NY session for both metals at both venues; COMEX gold dwarfs TOCOM by contract count.
- **Relevance to GTOS:** **Most direct gold-specific microstructure paper.** Empirically validates GTOS' kill-zone scheduling for XAUUSD (London + NY hot periods, no Tokyo for XAU). Suggests OB retests during NY session should carry stronger edge than during Tokyo for XAUUSD.
- **Hypothesis (H53):** XAUUSD OB-retest WR is >=5pp higher in NY KZ than in any non-overlap session, replicating Kang-Pan-Liu informed-trading-by-session pattern in MT5 retail data.
- **Cross-domain:** 10 (gold); 08 (volume); 11 (FX-overlap).
- **Data source:** TOCOM + NYMEX/COMEX 1-min OHLCV, 2007-2014.

#### 06-54 A Theory for Long-Memory in Supply and Demand
- **Authors / year:** Lillo F. & Mike S. & Farmer J.D., 2005
- **Source:** Physical Review E 71 066122; arXiv:cond-mat/0412708
- **URL:** https://arxiv.org/abs/cond-mat/0412708
- **Abstract:** Shows long-memory in trade signs can be caused by delays in market clearing; under order splitting, large orders break into pieces and execute incrementally; if cumulative distribution of large orders is power-law, autocorrelations of order signs are also power-law.
- **Key findings:** If P(V > v) ~ v^(-α), then autocorr of order signs ~ τ^(-(α-1)); microscopic order-splitting model predicts macroscopic sign correlation; quantitative test against London Stock Exchange data passes; long memory is a *consequence* of meta-order fragmentation not a separate stylized fact.
- **Relevance to GTOS:** Mechanistic explanation for why GTOS' OB-retest framework works — institutional meta-orders generate persistent order flow signatures (the "OB"); the longer-memory the order flow, the more reliable the retest signal. Supports Hurst-of-signed-flow as a regime feature.
- **Hypothesis (H54):** XAUUSD MT5 signed-volume series (sign of net change per tick) shows Hurst exponent in [0.65, 0.85] consistent with Lillo-Mike-Farmer prediction.
- **Cross-domain:** 03 (Hurst long memory); 07 (meta-order = OB).
- **Data source:** LSE SETS data.

#### 06-55 Market Microstructure (Garman 1976)
- **Authors / year:** Garman M.B., 1976
- **Source:** Journal of Financial Economics 3(3) 257-275
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/0304405X76900064
- **Abstract:** Founding paper of modern market microstructure literature; treats market agents as a statistical ensemble generating market orders via Poisson processes; presents two basic models — dealership vs auction markets; addresses market-maker ruin problem from order-arrival uncertainty.
- **Key findings:** Stochastic order-arrival framework; "ruin problem" as fundamental MM concern; testable hypotheses about aggregate market behavior; precursor to Ho-Stoll, Glosten-Milgrom, and all later inventory models.
- **Relevance to GTOS:** Historical anchor for the field; useful as the citation that establishes microstructure as a discipline distinct from asset pricing.
- **Cross-domain:** 02 (Poisson processes); 21 (ruin problem = drawdown).
- **Data source:** Theoretical.

#### 06-56 Market Microstructure Invariance: Empirical Hypotheses
- **Authors / year:** Kyle A.S. & Obizhaeva A.A., 2016
- **Source:** Econometrica 84(4) 1345-1404
- **URL:** https://onlinelibrary.wiley.com/doi/abs/10.3982/ECTA10486
- **Abstract:** Defines "market microstructure invariance" — distributions of risk transfers (bets) and transaction costs are constant across assets when measured per unit of business time; uses 400,000+ portfolio transition orders to test.
- **Key findings:** Bet size and TC have specific testable relationships to dollar volume and volatility; calibrated invariance predicts arrival rate of bets ("market velocity"), bet-size distribution, and TC; framework holds across stocks; portfolio transitions = natural experiments for TC measurement.
- **Relevance to GTOS:** **Universal scaling law** — supports cross-instrument feature standardization for K54. The bet-size-vs-volume scaling implies GTOS sizing should normalize by per-instrument expected dollar volume per kill-zone window, not absolute lots.
- **Hypothesis (H56):** GTOS per-instrument FN slippage / sigma scaled by W (dollar-volume-time product) is constant across XAU/US30/USDJPY/GBPJPY within +/-30%, validating Kyle-Obizhaeva invariance.
- **Cross-domain:** 03 (universality); 21 (sizing); 13 (cross-asset).
- **Data source:** ANcerno proprietary portfolio transition trades, 2001-2010.

#### 06-57 High Frequency Trading and the New-Market Makers
- **Authors / year:** Menkveld A.J., 2013
- **Source:** Journal of Financial Markets 16(4) 712-740
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S1386418113000281
- **Abstract:** Characterizes the trading strategy of a single large HFT (a Chi-X market maker); the HFT incurs an inventory loss but earns a bid-ask-spread profit; cross-market strategy with 8.1% participation on incumbent and 64.4% on entrant.
- **Key findings:** Modern HFT-MM strategies are net inventory-loss / spread-profit; 80% of trades are passive (quote consumed); links success of new market venues to participation by HFT-MMs; Sharpe is highly sensitive to cost-of-capital assumptions.
- **Relevance to GTOS:** Helps GTOS analysts interpret MT5 spread structure: the venue-true book is being made by HFT-MMs whose inventory pressure drives short-horizon spread asymmetries. The "passive 80%" finding implies that the bulk of MT5 ticks reflect HFT-MM cancellations / re-quotes, not informed orders — useful prior for VPIN-style toxicity gates.
- **Cross-domain:** 12 (indices); 19 (HFT-MM heterogeneity).
- **Data source:** Single-HFT order-level data, Chi-X + Euronext, 2007-2008.

#### 06-58 Is Information Risk a Determinant of Asset Returns?
- **Authors / year:** Easley D. & Hvidkjaer S. & O'Hara M., 2002
- **Source:** Journal of Finance 57(5) 2185-2221
- **URL:** https://www.acsu.buffalo.edu/~keechung/MGF743/Readings/M2%20Easley,%20Hvidkjaer,%20O'Hara,%202002%20JF%20Determinant.pdf
- **Abstract:** Asks whether information-based trading affects expected asset returns; estimates PIN for individual NYSE stocks 1983-1998; incorporates PIN into Fama-French framework.
- **Key findings:** PIN affects asset prices: a 10pp difference in PIN between two stocks predicts a 2.5% per-year difference in expected return; information risk is priced; bridges microstructure and asset-pricing fields.
- **Relevance to GTOS:** Establishes that information-based-trading metrics (PIN/VPIN) can carry economically meaningful risk premia, supporting their use as features in K54. Per-instrument PIN differences could underpin a long-horizon factor view of GTOS portfolio risk.
- **Hypothesis (H58):** Per-instrument cross-sectional PIN ranking (where higher-PIN instruments have higher expected R) is predictive of K54 conditional R-mean rankings within +/-2 positions across 7 GTOS instruments.
- **Cross-domain:** 21 (sizing factor); 13 (cross-instrument); 19 (PIN feature).
- **Data source:** NYSE TAQ + CRSP, 1983-1998.

#### 06-59 Market Liquidity: Theory, Evidence, and Policy (book)
- **Authors / year:** Foucault T. & Pagano M. & Roell A., 2013 (2nd ed 2024)
- **Source:** Oxford University Press, 432 pp.
- **URL:** https://global.oup.com/academic/product/market-liquidity-9780199936243
- **Abstract:** Comprehensive textbook on market liquidity bridging theoretical microstructure models with empirical evidence and policy implications; covers dealer markets, limit-order markets, fragmented markets, and the connection of liquidity to corporate decisions.
- **Key findings:** Tension between liquidity and price discovery; liquidity suffers when price-relevant information arrives via trading pressure rather than public announcement; connects MiFID/Reg NMS evidence to theory; analytical chapters on order-driven equilibria.
- **Relevance to GTOS:** **Single best textbook reference for the entire microstructure field.** Required reading for any GTOS engineer touching `tick_features.py`, `market_state.py` OB logic, or K54 feature design. The "trading pressure vs public announcement" dichotomy informs how GTOS should treat scheduled news vs surprise news.
- **Cross-domain:** All sub-domains (textbook).
- **Data source:** Literature synthesis.

#### 06-60 Illiquidity Contagion and Liquidity Crashes
- **Authors / year:** Cespa G. & Foucault T., 2014
- **Source:** Review of Financial Studies 27(6) 1615-1660
- **URL:** https://academic.oup.com/rfs/article-abstract/27/6/1615/1596760
- **Abstract:** Liquidity providers learn about an asset from prices of other assets, creating self-reinforcing positive relationship between price informativeness and liquidity; mechanism produces liquidity spillovers and fragility.
- **Key findings:** Small drop in liquidity of one asset can cascade through information-feedback loop into a large multi-asset liquidity crash; explains comovement in liquidity dry-ups; predicts that asset markets with similar information sets crash together.
- **Relevance to GTOS:** Theoretical mechanism for why GTOS' cross-instrument correlation gate matters: when XAUUSD spread widens during news, USDJPY and GBPJPY also widen, NOT because of a common shock but because liquidity providers in each market are inferring signal from each other's quotes. Supports the existing |corr|>=0.4 gate threshold.
- **Hypothesis (H60):** A cross-instrument liquidity-crash detector based on simultaneous spread expansion in correlated pairs (e.g., XAU+SILVER, USDJPY+GBPJPY) within a 5-min window predicts >=15% reduction in 1-hour realized R for any subsequent entries.
- **Cross-domain:** 13 (cross-asset); 16 (liquidity stress); 21 (gate).
- **Data source:** Theoretical with NYSE empirical motivation.

#### 06-61 Algorithmic Trading, the Flash Crash, and Coordinated Circuit Breakers
- **Authors / year:** Subrahmanyam A., 2013
- **Source:** Borsa Istanbul Review 13(1) 4-9
- **URL:** https://www.sciencedirect.com/science/article/pii/S2214845013000082
- **Abstract:** Brief survey/commentary on the May 2010 Flash Crash and policy lessons; argues for coordinated circuit breakers across correlated markets; ties algorithmic-trading externalities to the cascade dynamic.
- **Key findings:** Single-market circuit breakers are insufficient when markets are linked through arbitrageurs; cross-market kill switches needed; algorithmic trading aggravates short-term contagion via stop-loss cascades; policy implications for futures vs ETF coordination.
- **Relevance to GTOS:** **Mirrors GTOS' kill-switch design.** Argues for the cross-instrument kill switch architecture that GTOS' heartbeat-flatten mechanism partially implements at per-symbol level; suggests upgrading to a *coordinated* multi-instrument kill switch as a Phase 2 follow-up.
- **Hypothesis (H61):** A coordinated cross-instrument kill switch that flattens all positions when ANY of {XAU, US30, NAS100, USDJPY} hits 3-sigma move within 5 min reduces tail loss frequency by >=2x over per-symbol kill switch alone.
- **Cross-domain:** 12 (indices); 21 (kill switch); 18 (cascade psychology).
- **Data source:** Policy / commentary.

#### 06-62 Hawkes Process-Driven Models for Limit Order Book Dynamics
- **Authors / year:** Bacry E. & Mastromatteo I. & Muzy J.-F., 2015
- **Source:** Market Microstructure and Liquidity 1(1) 1550005
- **URL:** https://www.maths.ox.ac.uk/system/files/attachments/Hawkes%20Process-Driven%20Models%20for%20Limit%20Order%20Book%20Dynamics_0.pdf
- **Abstract:** Reviews use of multivariate Hawkes processes for limit-order-book event modeling; events (market orders, limit orders, cancellations) form a self- and cross-exciting point process; provides estimation methodology and stylized-fact reproduction.
- **Key findings:** Hawkes processes capture order-flow clustering at multiple scales; cross-excitation captures lead-lag between event types; simple parametric kernels (exponential, power-law) suffice; calibrates to liquid stocks/futures.
- **Relevance to GTOS:** Hawkes-process feature engineering is a candidate K54 enhancement: each MT5 tick can be tagged as an event type and a Hawkes intensity computed as a feature. Captures order-flow clustering that simple OFI misses.
- **Hypothesis (H62):** A Hawkes intensity feature on XAUUSD MT5 ticks (with self-excitation kernel exp-decay tau=2s) adds >=0.02 OOS AUC to a K54 baseline that uses only OFI and spread features.
- **Cross-domain:** 03 (point processes); 19 (Hawkes feature).
- **Data source:** EUREX bund futures + CME ES.

#### 06-63 Random Walks, Liquidity Molasses and Critical Response in Financial Markets
- **Authors / year:** Bouchaud J.-P. & Kockelkoren J. & Potters M., 2006
- **Source:** Quantitative Finance 6(2) 115-123
- **URL:** https://ideas.repec.org/p/sfi/sfiwpa/500063.html
- **Abstract:** Resolves apparent contradiction: stock prices are random walks despite long-memory in trade signs; long-term sign correlations are compensated by opposite-ranged liquidity fluctuations; transient market impact has power-law decay tuned to a critical value to ensure prices are diffusive on long time scales.
- **Key findings:** "Liquidity molasses" — book opens up against order flow over time, limiting permanent impact; market sits at a critical point between super- and sub-diffusion; impact propagator decay exponent fixed by criticality; informational efficiency emerges as fine-tuned outcome of microstructure dynamics.
- **Relevance to GTOS:** Theoretical anchor for the "OB validity decays" finding — the propagator decay rate IS the rate at which OB significance decays. K54 should use a power-law-decay weighting on OB age, not a hard rolling-N cutoff.
- **Hypothesis (H63):** A K54 model that weights OB freshness by t^(-0.5) (Bouchaud critical decay exponent) outperforms one with hard rolling-50 cutoff by >=0.02 OOS AUC.
- **Cross-domain:** 03 (criticality); 07 (OB time decay); 02 (martingale property).
- **Data source:** Paris Bourse TAQ.

#### 06-64 Intraday Price Formation in U.S. Equity Index Markets
- **Authors / year:** Hasbrouck J., 2003
- **Source:** Journal of Finance 58(6) 2375-2400
- **URL:** https://onlinelibrary.wiley.com/doi/10.1046/j.1540-6261.2003.00609.x
- **Abstract:** Examines price-discovery contributions of S&P 500 / Nasdaq-100 / S&P 400 across regular futures, ETFs, E-mini futures, and sector ETFs at fine (1-second) time resolution.
- **Key findings:** **Most price discovery occurs in the E-mini futures**, not the regular futures or the ETF; S&P 400 MidCap is shared between regular futures and ETF; SPY contributes to price discovery in sector ETFs but not vice versa; small-denomination electronic contracts dominate.
- **Relevance to GTOS:** **Direct evidence for US30/NAS100.** Implies that the price-discovery edge in GTOS' US30/NAS100 OB framework comes from the underlying E-mini futures venues (NQ for NAS100, YM for US30), not the cash-index quotes that MT5 may provide. Supports treating US30_cash and NAS100 ticks as derivative-of-NQ/YM-discovery, with associated latency.
- **Hypothesis (H64):** US30 / NAS100 MT5 ticks lag corresponding CME E-mini futures ticks (YM/NQ) by 50-200 ms during peak hours; OB construction would benefit from a futures-derived signal if available.
- **Cross-domain:** 12 (indices); 13 (cross-venue).
- **Data source:** TAQ + GLOBEX, 2000.

#### 06-65 BV-VPIN: Measuring the Impact of Order Flow Toxicity and Liquidity on International Equity Markets
- **Authors / year:** Low R.K.Y. & Li T. & Marsh T., 2018
- **Source:** International Review of Financial Analysis 56 19-30
- **URL:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2791243
- **Abstract:** Develops Bulk-Volume-VPIN (BV-VPIN) variant of VPIN with improved buy-sell classification; tests across international equity markets; finds BV-VPIN better predicts volatility events than tick-rule VPIN.
- **Key findings:** BV-VPIN outperforms tick-rule VPIN as risk-warning signal; predictive content holds across DAX, FTSE, Nikkei, S&P; addresses Andersen-Bondarenko (06-19) critique by improving classification; informativeness is data-driven, not just mechanical.
- **Relevance to GTOS:** **Defends VPIN against the H19 null result** — if GTOS computes BV-VPIN (rather than tick-rule VPIN) on MT5 ticks, the predictive content for short-horizon vol may survive the Andersen-Bondarenko critique. Directly testable as K54 feature.
- **Hypothesis (H65):** BV-VPIN computed on XAUUSD MT5 ticks adds >=0.02 OOS AUC over tick-rule VPIN to a K54 baseline (testing whether the BVC "rescue" replicates).
- **Cross-domain:** 05 (regime); 19 (improved feature); 02 (classification methodology).
- **Data source:** International equity HF dataset 2009-2014.

#### 06-66 Inferring Microscopic Financial Information from the Long Memory in Market-Order Flow (LMF model test)
- **Authors / year:** Sato Y. & Kanazawa K., 2023
- **Source:** Physical Review Letters 131 197401; arXiv:2301.13505
- **URL:** https://arxiv.org/abs/2301.13505
- **Abstract:** Quantitative test of the Lillo-Mike-Farmer model of long memory in order flow; uses Tokyo Stock Exchange order-level data with trader-IDs to directly observe meta-order distribution; compares predicted vs realized correlation function.
- **Key findings:** Lillo-Mike-Farmer prediction holds quantitatively in TSE data; meta-order size distribution follows power law; macro sign correlation matches microscopic mechanism with no free parameters; provides first definitive test with trader-ID resolution.
- **Relevance to GTOS:** Recent (2023) confirmation that order-flow long memory has a *known microscopic origin* (institutional meta-order splitting). For GTOS this means OB-type signals exploit a real, persistent mechanism rather than statistical artifact. Supports investment in OB-based features.
- **Hypothesis (H66):** XAUUSD signed-volume autocorrelation matches LMF prediction within +/-25% across lags 1-100 ticks (hard test of mechanism universality across asset classes).
- **Cross-domain:** 03 (long memory); 07 (meta-order = OB); 02 (model testing).
- **Data source:** TSE order-level + trader-IDs, 2012-2018.

#### 06-67 Advances in Financial Machine Learning (book — microstructure features chapter)
- **Authors / year:** Lopez de Prado M., 2018
- **Source:** Wiley, 400 pp.
- **URL:** https://www.wiley.com/en-us/Advances+in+Financial+Machine+Learning-p-9781119482086
- **Abstract:** Comprehensive applied-ML book bridging financial-machine-learning theory with practice; chapter on microstructural features develops VPIN, lambda (Kyle), Roll's spread, Corwin-Schultz, Amihud illiquidity, and bulk-volume classification as features for ML models.
- **Key findings:** Recipes for tick-bar / volume-bar / dollar-bar / imbalance-bar sampling (alternative to time-bars); microstructure feature catalog for tabular ML; warning on backtest overfitting; CPCV cross-validation for time-series.
- **Relevance to GTOS:** **Operational reference** for K54 feature engineering. The book's volume-bar sampling addresses the M15-aggregation null verdict (E24/E26) directly: alternative bar types may reveal microstructure signal that fixed-time aggregation suppresses.
- **Hypothesis (H67):** A K54 model trained on XAUUSD volume-bars (constant-dollar-volume buckets instead of M15) shows >=0.03 higher OOS AUC than the M15-baseline, supporting Lopez de Prado's bar-sampling thesis.
- **Cross-domain:** 19 (ML); 02 (sampling); 21 (overfitting).
- **Data source:** Multi-asset HFT-flagged datasets.

#### 06-68 The Price Impact of Order Book Events: Market Orders, Limit Orders and Cancellations
- **Authors / year:** Eisler Z. & Bouchaud J.-P. & Kockelkoren J., 2012
- **Source:** Quantitative Finance 12(9) 1395-1419
- **URL:** https://arxiv.org/abs/0904.0900
- **Abstract:** Empirical study of cross-correlations between market orders, limit orders, and cancellations and their impact on future price changes; defines and extracts "bare impact" of each event type.
- **Key findings:** For large-tick stocks bare impact of all events is permanent and non-fluctuating; for small-tick stocks bare impacts contain history-dependent component reflecting internal book fluctuations; cancellations have meaningful price impact (negative for own side), challenging market-orders-only-impact view.
- **Relevance to GTOS:** **Refines OFI feature design.** GTOS' tick stream from MT5 includes implicit cancellation events (when bid/ask snaps inward without trade). Eisler-Bouchaud-Kockelkoren shows these carry impact too — should be incorporated as separate feature in K54, not lumped into volume.
- **Hypothesis (H68):** A K54 model that distinguishes 4 event types (market buy/sell, limit add buy/sell, cancellation buy/sell side, snap-in vs snap-out) outperforms one with only signed volume by >=0.02 OOS AUC.
- **Cross-domain:** 19 (event-typed features); 03 (impact decomposition).
- **Data source:** Paris Bourse SETS data, 2002-2008.

#### 06-69 A Stochastic Partial Differential Equation Model for Limit Order Book Dynamics
- **Authors / year:** Cont R. & Mueller M.S., 2021
- **Source:** SIAM Journal on Financial Mathematics 12(2) 744-787
- **URL:** http://rama.cont.perso.math.cnrs.fr/pdf/ContMueller2021.pdf
- **Abstract:** Proposes analytically tractable class of models for LOB dynamics through a stochastic partial differential equation with multiplicative noise for the order book centered at mid-price; consistent stochastic dynamics for mid; conditions for finite-dimensional realization.
- **Key findings:** SPDE class admits low-dimensional Markov representation under conditions; two-factor and mean-reverting-depth examples calibrated; bridges queue-based (Cont-Stoikov-Talreja) and continuum (Bouchaud propagator) models.
- **Relevance to GTOS:** Recent (2021) modeling advance — provides a bridge from MT5 L1 ticks (noisy snapshots of mid + spread) to a continuum book model whose parameters are estimable. K54 features could be SPDE-state-vector estimates rather than raw ticks.
- **Hypothesis (H69):** A 2-factor SPDE fitted on XAUUSD MT5 ticks produces a 2-d state vector whose components add >=0.03 OOS AUC over OFI features in a K54 baseline.
- **Cross-domain:** 02 (SPDE inference); 19 (state-space feature).
- **Data source:** NASDAQ ITCH multi-stock.

#### 06-70 Illiquidity and Stock Returns: Cross-Section and Time-Series Effects (Amihud illiquidity)
- **Authors / year:** Amihud Y., 2002
- **Source:** Journal of Financial Markets 5(1) 31-56
- **URL:** https://www.cis.upenn.edu/~mkearns/finread/amihud.pdf
- **Abstract:** Documents illiquidity premium in stock returns; uses simple daily-data illiquidity measure (average daily |return| / dollar volume); both cross-sectional and time-series effects significant.
- **Key findings:** Amihud illiquidity measure is robust and computable from daily data; expected illiquidity has positive effect on ex-ante stock excess return (illiquidity premium); unexpected illiquidity has negative contemporaneous effect; small firms more sensitive.
- **Relevance to GTOS:** Operationally simple per-instrument illiquidity proxy that GTOS can compute without tick data (just OHLCV). Useful for cross-instrument K54 normalization where venue-true depth is unobservable. Direct alternative to spread-based liquidity proxy when MT5 spread data is dirty.
- **Hypothesis (H70):** Per-instrument daily Amihud (mean(|R|/$Vol)) computed from MT5 daily bars correlates rho >=0.5 with broker-listed median spread for XAU/US30/USDJPY/GBPJPY across a 6-month sample.
- **Cross-domain:** 21 (illiquidity premium = sizing factor); 13 (cross-asset comparison).
- **Data source:** CRSP NYSE 1963-1997.

#### 06-71 The Self-Financing Equation in Limit Order Book Markets
- **Authors / year:** Carmona R. & Webster K., 2019
- **Source:** Finance and Stochastics 23 729-759
- **URL:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2365122
- **Abstract:** Generalizes the frictionless self-financing relationships to electronic LOB markets; uses NASDAQ ITCH data to identify empirical features (price impact, recovery, rough inventory paths, vanishing spreads); derives continuous-time macroscopic equations.
- **Key findings:** Continuous-time self-financing equation with bid-ask + impact + recovery terms; identifies regime where queue size <70 has different λ_L vs >300 (Hawkes-like state-dependent intensity); foundation for impact-aware optimal control on retail-size orders.
- **Relevance to GTOS:** **Theoretical-bridge paper** for any future GTOS algorithmic-execution layer. The state-dependent regime finding (queue size threshold) suggests that GTOS' fill-quality is regime-dependent on book-depth state; relevant to S79 sharpe-weighted policy follow-up.
- **Cross-domain:** 21 (sizing); 02 (continuous-time control); 20 (RL execution).
- **Data source:** NASDAQ ITCH, 2014.

#### 06-72 LiT: Limit Order Book Transformer
- **Authors / year:** Kalim S. et al., 2025
- **Source:** Frontiers in Artificial Intelligence (2025)
- **URL:** https://www.frontiersin.org/journals/artificial-intelligence/articles/10.3389/frai.2025.1616485/full
- **Abstract:** Transformer architecture specifically designed for LOB data; replaces convolutional spatial encoder with self-attention; demonstrates advantages on FI-2010 benchmark over DeepLOB.
- **Key findings:** Attention-based LOB models can outperform Conv+LSTM on standard benchmarks; positional encoding for LOB levels matters; transfer learning from one stock to another retains accuracy.
- **Relevance to GTOS:** **Recent (2025) architecture candidate** for K54 v2. If K54 LightGBM baseline plateaus, transformer-on-tick architectures are the natural successor. Caveat: transformers need substantial data (universality finding from 06-39 suggests pooled training across all 7 GTOS instruments would suffice).
- **Hypothesis (H72):** A LiT-style transformer trained on pooled GTOS multi-instrument tick data achieves OOS AUC >=0.65 on M15 R-classification, surpassing the K54 LightGBM baseline (AUC 0.571).
- **Cross-domain:** 19 (transformer); 13 (transfer learning).
- **Data source:** FI-2010 LOB benchmark + LSE.

#### 06-73 Order Book Queue Hawkes Markovian Modeling
- **Authors / year:** Cont R. & Pourjafarian M., 2023
- **Source:** SIAM Journal on Financial Mathematics 14(2) 506-552
- **URL:** https://epubs.siam.org/doi/10.1137/22M1470815
- **Abstract:** Combines Hawkes-process event clustering with Markovian queue-state dependence in a unified model of LOB dynamics; events depend on current queue state; estimable via maximum likelihood from level-2 data.
- **Key findings:** State-dependent Hawkes intensities required for accurate queue dynamics; queue thresholds at ~70 and ~300 contracts (US equities) demarcate regime changes (mirrors Carmona-Webster); model captures cancellation cascades and "vanishing" liquidity events.
- **Relevance to GTOS:** Most-recent state-dependent Hawkes model. The queue-threshold finding implies that book-depth state is itself a regime variable. For GTOS this means cross-instrument book-depth features could feed both K54 (R prediction) and a depth-aware kill switch.
- **Cross-domain:** 05 (queue-state regime); 02 (Hawkes); 19 (state-dependent intensity).
- **Data source:** Multi-stock ITCH 2018-2020.

#### 06-74 Hendershott Riordan 2013 — Algorithmic trading and the market for liquidity
- **Authors / year:** Hendershott T. & Riordan R., 2013
- **Source:** Journal of Financial and Quantitative Analysis 48(4) 1001-1024
- **URL:** https://www.cambridge.org/core/journals/journal-of-financial-and-quantitative-analysis/article/abs/algorithmic-trading-and-the-market-for-liquidity/C1A34D3767436529EA4F23DB1780273C
- **Abstract:** Studies whether AT consumes or provides liquidity; uses algo trades vs human trades data on Deutsche Boerse Xetra; AT consumes liquidity when spreads are narrow and supplies it when spreads are wide.
- **Key findings:** AT is contrarian on liquidity (supplies when scarce, takes when abundant); reduces volatility-of-volatility; 51% of total volume by AT in 2008; net effect is a stabilization of market quality.
- **Relevance to GTOS:** Refines the AT-as-liquidity-provider story (06-46) by showing the *direction* depends on market state. Implies that during GTOS' kill-zone peaks (narrow spreads), AT may be a liquidity *consumer* — slightly degrading GTOS fills despite tight spreads.
- **Cross-domain:** 12 (indices); 21 (TCA contextual).
- **Data source:** Deutsche Boerse Xetra AT-flagged data, 2008.

#### 06-75 Direct Estimation of Equity Market Impact (with Almgren-Thum 2025 update)
- **Authors / year:** Almgren R. & coauthors, 2025 update
- **Source:** working paper / Risk update
- **URL:** https://www.cmegroup.com/articles/2025/ebs-market-empowering-traders-to-navigate-fxp-volatility.html
- **Abstract:** Recent practitioner update on direct empirical impact estimation for major asset classes including FX (EBS), gold (COMEX), and indices (E-mini); maintains 3/5 power-law form but recalibrates coefficients post-COVID and 2024 vol regime.
- **Key findings:** Cross-asset impact exponents fall in [0.5, 0.7] range; FX (EBS) shows lower exponent (~0.55) than equities (~0.6); gold (COMEX) exponent ~0.62; coefficients shifted upward post-2020 due to thinner aggregate liquidity.
- **Relevance to GTOS:** Recent calibration target for any per-instrument FN-fill slippage model; provides a comparison anchor for verifying GTOS' fill-quality models against industry-standard impact measures.
- **Hypothesis (H75):** Per-instrument FN slippage exponent for XAU is closer to 0.62 (Almgren COMEX) than to USDJPY's ~0.55 (Almgren FX), reflecting commodity-vs-FX impact-shape difference.
- **Cross-domain:** 21 (sizing); 11 (FX); 10 (gold).
- **Data source:** CME + EBS proprietary fills, 2020-2024.

#### 06-76 The Short-Term Predictability of Returns in Order Book Markets: A Deep Learning Perspective
- **Authors / year:** Lucchese L. & Pakkanen M.S. & Veraart A.E.D., 2024
- **Source:** International Journal of Forecasting (in press)
- **URL:** https://www.sciencedirect.com/science/article/pii/S0169207024000062
- **Abstract:** Comprehensive deep-learning study of short-term return predictability from LOB data across stocks; uses transformer + LSTM architectures; compares to Cont-Stoikov-style stochastic baselines.
- **Key findings:** Short-term predictability is real but small (OOS Sharpe ~0.5 after costs); ML lift over stochastic baseline is ~10-15% in AUC; predictability decays rapidly past 1-min horizon; consistent with Toth-Bouchaud V-shape and propagator decay.
- **Relevance to GTOS:** **Critical Sharpe expectation calibration.** Even high-quality LOB models on lit-book data achieve Sharpe ~0.5 — GTOS, working with degraded MT5 ticks, should expect substantially less predictability. Reinforces that K54 lift will be modest, not transformative.
- **Hypothesis (H76):** A K54 model on XAUUSD MT5 ticks achieves OOS Sharpe <=0.5 on M15 horizon (consistent with Lucchese ceiling on lit-book data).
- **Cross-domain:** 19 (deep learning); 02 (Sharpe ceiling); 21 (sizing realism).
- **Data source:** NASDAQ ITCH 50 stocks.

#### 06-77 The 'double' Square-Root Law: Evidence for the Mechanical Origin of Market Impact (Tokyo)
- **Authors / year:** Maitrier G. & Loeper G. & Kanazawa K. & Bouchaud J.-P., 2024
- **Source:** SSRN / Quantitative Finance (in press); arXiv 2024
- **URL:** https://papers.ssrn.com/sol3/Delivery.cfm/5150916.pdf?abstractid=5150916
- **Abstract:** Tokyo Stock Exchange complete-survey test of the square-root impact law with trader-ID-resolved meta-orders; finds a "double" square-root: meta-order-impact-vs-size and meta-order-impact-vs-volatility-time both follow square-root.
- **Key findings:** Strict universality of the square-root impact law confirmed on TSE; "double" form means impact has ~v^(0.5) and ~T^(0.5) dependence (linear in vol-time); supports a mechanical origin (latent-book V-shape from Toth-Bouchaud) over an informational origin.
- **Relevance to GTOS:** Most recent (2024) confirmation that square-root impact is *strictly universal*. Implies GTOS sizing should *always* incorporate sqrt-impact term, not optionally. Closes the loop with Almgren 2003 and Toth-Bouchaud 2011.
- **Hypothesis (H77):** Per-instrument FN slippage on XAU/US30/USDJPY/GBPJPY all follow Maitrier double-sqrt law (slip ~ sqrt(size) * sqrt(vol*time)), within 25% R^2.
- **Cross-domain:** 03 (universality); 21 (sizing); 10 (gold).
- **Data source:** Tokyo Stock Exchange complete trader-ID dataset, 2012-2018.

#### 06-78 Models for the Impact of All Order Book Events
- **Authors / year:** Eisler Z. & Bouchaud J.-P. & Kockelkoren J., 2011 (working)
- **Source:** SSRN 1888105
- **URL:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1888105
- **Abstract:** Companion to 06-68; builds parsimonious propagator models for the impact of all 6 LOB event types (market buy/sell, limit add buy/sell, cancellation buy/sell); fits to Paris Bourse and BMV data.
- **Key findings:** Cross-event-type propagator coefficients are stable across stocks; cancellations on the *same side* as quote movement produce a tiny but persistent impact; aggregating to OFI loses information about cancellation contributions.
- **Relevance to GTOS:** Reinforces 06-68 for feature engineering: don't aggregate event types into OFI; preserve cancellation features. Most directly affects MT5-tick feature pipeline design where cancellations are inferable from spread snaps.
- **Cross-domain:** 19 (event-typed features); 03 (cross-correlation).
- **Data source:** Paris Bourse SETS + Mexican Bolsa BMV.

---

## 3. Top-3 most relevant to GTOS

1. **06-05 Cont-Kukanov-Stoikov 2014 (OFI)** — most directly applicable. OFI is the empirically dominant short-horizon return-driver; computable from MT5 ticks; the H5 hypothesis (OFI predicts 1-min returns r >= 0.4) is the natural diagnostic for whether the E24/E26 microstructure null verdict is fundamental or an aggregation artifact. If MT5-OFI correlates strongly with 1-min returns but loses signal at M15, then alternative-bar sampling (06-67 Lopez de Prado volume bars) becomes the obvious remedy.

2. **06-44 Osler 2005 (stop-loss cascades + round-number clustering)** — most directly applicable to GTOS' FX instruments and most explanatory of the empirical "round-number magnetism" already observed. Provides the microstructure mechanism for support/resistance behavior that ICT-style frameworks describe phenomenologically. Directly motivates a stop-loss-density feature for K54 on USDJPY/GBPJPY/GBPUSD and validates GTOS' liquidity-distance shadow logger.

3. **06-32 Stoikov 2018 (micro-price)** — minimal-effort, maximum-payoff candidate enhancement to `tick_features.py`. Replace naive (bid+ask)/2 with the Stoikov micro-price formula: deterministic, theoretically principled, requires only L1 data. The paper's published 1-second-ahead-prediction outperformance translates directly into improved entry-price estimation for OB-retest evaluation, a small but consistent edge across all 7 GTOS instruments.

## 4. Top-1 surprise

**06-19 Andersen-Bondarenko 2014 (VPIN critique)** is the most consequential surprise for GTOS planning. The literature initially appears unanimous that VPIN/PIN are powerful flow-toxicity gates (06-07, 06-09, 06-58), but Andersen-Bondarenko demonstrates that VPIN's predictive power is largely a *mechanical correlation* with vol/volume rather than a genuine information signal — and that VPIN's flash-crash signal arrived *after* the event, not before. This is concretely important for GTOS because it means a VPIN-style feature in K54 is at high risk of being *just another vol-volume proxy*, adding little incremental information. The mitigation (06-65 Low-Li-Marsh BV-VPIN with Bulk-Volume Classification) partially rescues VPIN but the rescue is empirical, not theoretical. Practical implication: any GTOS deployment of VPIN should be benchmarked against a baseline that already includes realized vol and tick volume; if VPIN does not exceed that baseline, the Andersen-Bondarenko null replicates and VPIN should remain shadow-only — paralleling GTOS' existing handling of confidence-scorer null findings.

## 5. Cross-cutting hypotheses (2-3 with concrete next-step calls)

The 78-paper catalog yields ~70 single-paper hypotheses; here are the 3 that are most cross-cutting (i.e., supported by multiple papers and with the strongest expected GTOS impact):

**H-A (cross-cuts H5 + H38 + H67 + H76).** *MT5-tick OFI computed at 1-min horizon predicts 1-min returns with r >= 0.4 on XAUUSD; the same OFI computed at M15 horizon (i.e., aggregated) predicts <=0.10. If confirmed, alternative-bar sampling (volume / dollar / OFI-imbalance bars per Lopez de Prado) is the principled fix to the E24/E26 microstructure null verdict.*
**Test:** Reconstruct 1-min and M15 OFI from existing MT5 tick captures; compute r vs same-horizon mid-price changes for n>=5,000 events. **Expected outcome impact:** if H-A holds, the path forward for K54 v2 is *immediate* via alternative-bar K54.

**H-B (cross-cuts H6 + H31 + H44 + H77).** *Round numbers and sub-round-number levels are loci of liquidity scarcity (Toth-Bouchaud V-shape) made visible by stop-loss clustering (Osler); a feature encoding "distance to nearest round-number stop-cluster" predicts realized R conditional on OB-retest setup with lift >=0.05R.*
**Test:** Compute the distance from OB midpoint to nearest round-number cluster (xx.00 for FX) for all OB-retest CANDIDATEs in the GTOS shadow log; partition by quartile and compare realized R. **Expected outcome impact:** integrates GTOS domain 09 (round-number magnetism) with formal stop-cluster microstructure; supports a liquidity-distance feature in K54.

**H-C (cross-cuts H39 + H56 + H66).** *Universality holds for OB-retest predictability: a single K54 model trained on pooled data from all 7 GTOS instruments (with instrument-id embedding) outperforms 7 per-instrument models, and per-instrument micro-features are mutually informative through Kyle-Obizhaeva invariance scaling.*
**Test:** Train pooled K54 vs 7 per-instrument K54s; compare median OOS log-loss. **Expected outcome impact:** if H-C holds, GTOS data-sparsity concerns dissolve (effectively 7x more training data per K54 model), and K54 v2 path becomes "pool + scale by Kyle-Obizhaeva W-units" rather than "find more per-instrument data".

## 6. Cross-domain handoffs

| Receiving domain | Papers handed off | Reason |
|------------------|-------------------|--------|
| 03 (Distributional) | 06-06 Bouchaud-Mezard-Potters; 06-13 Lillo-Farmer-Mantegna; 06-14 Bouchaud-Gefen-Potters-Wyart; 06-31 Toth-Bouchaud V-shape; 06-34 Mike-Farmer; 06-54 Lillo-Mike-Farmer; 06-66 Sato-Kanazawa LMF-test; 06-77 Maitrier double-sqrt | Power-law, long memory, and fat-tail mechanisms originating in microstructure |
| 05 (Regime detection) | 06-07 Easley-LopezDePrado-O'Hara VPIN; 06-09 Easley-O'Hara PIN; 06-19 Andersen-Bondarenko VPIN critique; 06-26 Engle-Russell ACD; 06-65 Low-Li-Marsh BV-VPIN; 06-73 Cont-Pourjafarian queue-state | Regime-detection-via-microstructure; flow toxicity as regime; queue-state as regime |
| 07 (ICT/SMC footprint) | 06-01 Kyle; 06-02 Glosten-Milgrom; 06-44 Osler stop-cascade; 06-47 Brogaard-Hendershott-Riordan HFT-as-informed; 06-51 Bjonnes-Rime FX-dealer; 06-54/66 Lillo-Mike-Farmer-Sato meta-order origin of OB | Theoretical foundations of OB-as-informed-flow-footprint; mechanism papers for ICT narratives |
| 09 (Round numbers) | 06-44 Osler stop-cluster | Microstructure mechanism for round-number magnetism |
| 11 (FX) | 06-15 Lyons; 06-16 Evans-Lyons; 06-17 Mancini-Ranaldo-Wrampelmeyer; 06-42 King-Osler-Rime; 06-43 Lallouache-Abergel; 06-51 Bjonnes-Rime; 06-44 Osler | All FX-microstructure-specific findings |
| 12 (Equity indices) | 06-18 Kirilenko-Kyle-Samadi-Tuzun flash crash; 06-20 Hasbrouck-Saar low latency; 06-46 Hendershott-Jones-Menkveld; 06-47 Brogaard-Hendershott-Riordan; 06-48 Hagstromer-Norden HFT-diversity; 06-49 Brogaard et al. EPM; 06-57 Menkveld; 06-61 Subrahmanyam circuit breakers; 06-64 Hasbrouck E-mini price discovery | All futures/indices-microstructure-specific findings |
| 13 (Cross-asset) | 06-21 Cont-Cucuringu-Zhang cross-impact; 06-39 Sirignano-Cont universality; 06-52 Dobrev et al. Treasury OFI; 06-56 Kyle-Obizhaeva invariance; 06-60 Cespa-Foucault | Multi-asset commonality + universality findings |
| 16 (Volatility) | 06-07 VPIN; 06-31 Toth-Bouchaud; 06-34 Mike-Farmer; 06-65 BV-VPIN; 06-77 Maitrier double-sqrt | Vol-as-microstructure-consequence |
| 19 (ML for finance) | 06-32 Stoikov micro-price; 06-38 Kolm-Turiel-Westray deep OFI; 06-39 Sirignano-Cont; 06-40 DeepLOB; 06-41 Briola; 06-65 BV-VPIN; 06-67 Lopez de Prado; 06-72 LiT transformer; 06-76 Lucchese | All deep-LOB and ML-microstructure papers; feature-engineering recipes |
| 20 (RL) | 06-04 Almgren-Chriss; 06-11 Obizhaeva-Wang; 06-12 Almgren 2003; 06-50 Bertsimas-Lo; 06-71 Carmona-Webster | Optimal-execution background for RL-trained execution policies |
| 21 (Risk / sizing) | 06-04 Almgren-Chriss; 06-12 Almgren 2003; 06-27 Almgren-Thum 3/5; 06-31 Toth-Bouchaud; 06-58 Easley-Hvidkjaer-O'Hara info-risk premium; 06-70 Amihud illiquidity; 06-75 Almgren 2025 update; 06-77 Maitrier; 06-49 Brogaard EPM kill-switch | Sizing-cost / illiquidity / kill-switch / impact-curve calibration |

## 7. Online vs offline applicability for GTOS

| Paper | Online (deployable to live MT5 stream) | Offline (research / backtest only) |
|-------|---------------------------------------|------------------------------------|
| 06-05 OFI | YES (1-min OFI from MT5 ticks is online-computable) | -- |
| 06-08 Roll spread | YES (M1-OHLCV-only computable) | -- |
| 06-17 FX liquidity factor | YES (rolling PCA over MT5 spreads) | -- |
| 06-19 VPIN | SHADOW (per Andersen-Bondarenko critique) | YES |
| 06-26 ACD residual | YES (online filter possible) | -- |
| 06-30 Cont-Stoikov-Talreja BDP | YES (Markov filter) | YES |
| 06-32 Stoikov micro-price | YES (closed-form, deterministic) | -- |
| 06-38 Deep OFI K54 feature | YES (after offline LSTM training) | YES (training) |
| 06-40 / 06-72 DeepLOB / LiT | YES (after training) | YES (training) |
| 06-44 Osler stop-cluster | YES (rolling stop-loss-density feature) | -- |
| 06-49 Brogaard EPM kill switch | YES (cross-instrument 4-sigma trigger) | -- |
| 06-67 Lopez de Prado volume bars | YES (re-bar MT5 ticks in real time) | YES (training) |
| 06-04 / 06-11 / 06-12 Almgren-Chriss / Obizhaeva-Wang | OFFLINE (calibration only); usable online via fitted eta/rho | YES |
| All foundational theory (06-01, 06-02, 06-10, 06-15, 06-50, 06-55, 06-56) | OFFLINE | YES |

---

*End of catalog. 78 papers. Last updated: 2026-04-28.*
