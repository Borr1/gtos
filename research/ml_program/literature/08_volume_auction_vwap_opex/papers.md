# Domain 08 — Volume, Auction Theory, VWAP, OPEX

**Worker:** Phase 1 Literature Research Agent #8
**Date:** 2026-04-28
**Spec:** `research/ml_program/literature/_specs/08_volume_auction_vwap_opex.md`
**Output schema fields:** `id, title, authors, year, source, url, abstract, key_findings, relevance_to_gtos, potential_hypothesis, cross_domain_links, intraday_window`

This domain catalogs literature on (1) volume as information signal, (2) market-profile / auction-theoretic frameworks, (3) VWAP-anchored execution, (4) options-expiration / dealer-gamma effects on cash markets, and (5) end-of-day, opening, and FX-fix mechanical flows. The Phase-2 synthesis hooks are: `tick_features.py` volume-imbalance features, the kill-zone window definitions (esp. NAS100/US30 13:30/14:30 UTC), the cross-instrument correlation gate (calendar-fix flow distortions), and the L2 sl_buffer-0.0 cluster which appears empirically near round-number / fixing clusters.

---

## 1. Foundational volume-volatility & market-microstructure-volume

### The Relation between Price Changes and Trading Volume: A Survey
- **Authors:** Jonathan M. Karpoff
- **Year:** 1987
- **Source:** Journal of Financial and Quantitative Analysis 22(1): 109-126
- **URL:** https://www.cambridge.org/core/services/aop-cambridge-core/content/view/DBE2C70FA41E390EB8FA418BBFFD76C8/S0022109000012473a.pdf/div-class-title-the-relation-between-price-changes-and-trading-volume-a-survey-div.pdf
- **Abstract:** Reviews previous and current research on the relation between price changes and trading volume. Establishes two empirical regularities: volume is positively correlated with the magnitude of price change, and (in equity markets) with the price change per se. Synthesizes theoretical models attempting to explain these regularities.
- **Key findings:**
  - Volume is positively related to |Δp| in essentially every asset class examined.
  - Volume is positively related to Δp itself (i.e., asymmetric) in equity markets but not consistently in futures.
  - The "Mixture of Distributions Hypothesis" (Clark 1973, Tauchen-Pitts 1983) provides one consistent framework.
  - Sequential information arrival (Copeland 1976) is an alternative competing model.
  - Karpoff proposes a cost-of-information-asymmetry model that reconciles seemingly contradictory observations.
- **Relevance to GTOS:** Foundational justification for any volume-derived feature in `tick_features.py`. The asymmetric volume-return relation in equities (vs. symmetric in commodities) is directly relevant to comparing XAUUSD/US30/NAS100 (where volume should track |Δp|) to FX (USDJPY/GBPJPY/EURUSD/GBPUSD where volume is harder to interpret because there is no consolidated tape).
- **Potential hypothesis:** A regime-conditioned volume-imbalance feature should add lift in equity-index regimes (US30, NAS100) but be near-noise in FX. Test by stratifying realized R by quartile of `vol_imbalance` per instrument.
- **Cross-domain links:** 03 (volume as Hurst-of-order-flow stylized fact); 06 (Kyle-lambda is the price-impact cousin)
- **Intraday window:** Daily (foundational survey covers all windows)

### Trading Volume: Definitions, Data Analysis, and Implications of Portfolio Theory
- **Authors:** Andrew W. Lo, Jiang Wang
- **Year:** 2000
- **Source:** Review of Financial Studies 13(2): 257-300
- **URL:** https://web.mit.edu/wangj/www/pap/LoWang00.pdf
- **Abstract:** Examines the implications of portfolio theory for cross-sectional behavior of equity volume. Two-fund separation theorems suggest a natural definition of trading activity: share turnover. Documents stylized facts of volume.
- **Key findings:**
  - Share turnover (rather than dollar volume) is the theoretically-cleanest volume measure under multi-fund-separation models.
  - Cross-sectional volume is highly heteroscedastic and clustered.
  - Aggregate turnover follows long-memory dynamics distinct from return long-memory.
  - There is no single "volume" — different definitions reveal different facts.
  - Day-of-week and intraday seasonality dominate raw volume series.
- **Relevance to GTOS:** The instrument-comparability question for volume features. Comparing XAUUSD-tick-volume to US30-futures-volume is not apples-to-apples; turnover-style normalization (volume/open-interest or volume/free-float) is the academically-correct cross-instrument harmonizer.
- **Potential hypothesis:** Replace raw tick-volume in `tick_features.py` with turnover-normalized volume per instrument; expect tighter cross-instrument feature distribution and stable importance ranking in K54.
- **Cross-domain links:** 03 (long-memory of volume); 13 (cross-section turnover as a factor)
- **Intraday window:** Daily / cross-sectional

### Mixture of Distributions Hypothesis: Empirical Tests in GARCH Frameworks
- **Authors:** various (Andersen 1996; Lamoureux & Lastrapes 1990; Tauchen & Pitts 1983)
- **Year:** 1983-1996 (foundational)
- **Source:** Journal of Finance / Journal of Business / Econometrica
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S0304407617301665 (modern review)
- **Abstract:** The MDH posits that observed return-and-volume series are subordinated to a latent information-arrival process. Volume is a conditioning variable for return variance: when volume is included in GARCH conditional variance equations, persistence (β) typically falls dramatically.
- **Key findings:**
  - Lamoureux-Lastrapes (1990): including contemporaneous volume in GARCH(1,1) volatility eliminates persistence in many stocks.
  - Result is fragile — Andersen (1996) shows it doesn't survive when volume is treated endogenously.
  - The latent information-flow interpretation survives empirically in most markets.
  - Cross-asset, the relationship is strongest in equities, weaker in FX, ambiguous in commodities.
- **Relevance to GTOS:** Justifies including volume as a state-conditioning variable for our volatility-regime classifier (K54). If MDH holds even partially, volume-conditional volatility forecasts should beat unconditional GARCH in shadow.
- **Potential hypothesis:** Add a `volume_conditional_volatility` feature to K54 — expected positive importance for indices, near-zero for FX.
- **Cross-domain links:** 03 (GARCH in vol modeling); 16 (vol regime trading)
- **Intraday window:** Daily / contemporaneous

### A Theory of Intraday Patterns: Volume and Price Variability
- **Authors:** Anat R. Admati, Paul Pfleiderer
- **Year:** 1988
- **Source:** Review of Financial Studies 1(1): 3-40
- **URL:** https://pages.stern.nyu.edu/~lpederse/courses/LAP/papers/Information,Fundamental/AdmatiPfleiderer88.pdf
- **Abstract:** Provides an information-theoretic explanation for the U-shaped intraday volume and volatility pattern. Discretionary liquidity traders prefer to trade when other liquidity traders are trading (lower adverse-selection cost), creating endogenous concentration of activity at predictable times.
- **Key findings:**
  - U-shape in volume and volatility emerges as Nash equilibrium of strategic liquidity-trader timing.
  - Informed traders pool with liquidity traders, intensifying both volume and price variability.
  - The model explains why "everyone trades when everyone trades."
  - High volume periods are simultaneously highest-info and highest-noise.
  - Predictable seasonality is a feature of strategic equilibrium, not a bug.
- **Relevance to GTOS:** Theoretical underpinning for the kill-zone framework: London/NY opens and closes are not just historical convention; they are equilibrium outcomes. Implies that quality-of-signal at 13:30 UTC NAS100 open is a mixture, not pure-noise.
- **Potential hypothesis:** Within a single kill-zone window, the *first 5-10 minutes* are dominated by liquidity-trader pooling (noise); the next 30-60 minutes are higher-quality signal. Test by stratifying realized R by minute-bucket within kill zones.
- **Cross-domain links:** 06 (microstructure equilibrium); 09 (round-number clustering as another equilibrium)
- **Intraday window:** Open / close / mid (full intraday)

### Are Intraday Volume and Volatility U-Shaped After Accounting for Public Information?
- **Authors:** Tian, Pan, Sefton (and predecessors)
- **Year:** ~2008-2014
- **Source:** various working papers; ResearchGate
- **URL:** https://www.researchgate.net/publication/46511595_Are_Intraday_Volume_and_Volatility_U-Shaped_After_Accounting_for_Public_Information
- **Abstract:** Tests whether the U-shape in volume/volatility persists after explicitly conditioning on public-information arrival (macro releases). Finds the pattern weakens but does not disappear.
- **Key findings:**
  - U-shape is partly explained by macro release clustering (early morning news, mid-day announcements).
  - Even after orthogonalizing on news, opening 30 minutes have ~40% higher volume than mid-day.
  - Pre-close last-30-minutes spike is largely *not* news-driven — consistent with mechanical / rebalancing flow.
  - Volatility U-shape is more news-driven than volume U-shape.
- **Relevance to GTOS:** Supports a refinement of kill-zone definitions: the morning kill zone is *partly* news-driven (FOMC, NFP, ECB) while the close kill zone is *more* mechanical. Our risk gates should treat these differently.
- **Potential hypothesis:** Spread of the kill-zone WR distribution should be larger near opens (news heterogeneity) and smaller near closes (mechanical homogeneity). Test on existing batch.
- **Cross-domain links:** 17 (calendar effects); 11 (FX news and macro)
- **Intraday window:** Open / mid / close

### Intraday Periodicity and Volatility Persistence in Financial Markets
- **Authors:** Torben G. Andersen, Tim Bollerslev
- **Year:** 1997
- **Source:** Journal of Empirical Finance 4(2-3): 115-158
- **URL:** https://finance.martinsewell.com/stylized-facts/volatility/AndersenBollerslev1997b.pdf
- **Abstract:** Documents that intraday volatility has both a strong deterministic seasonality and long-memory persistence. The seasonality must be filtered before estimating persistence.
- **Key findings:**
  - Intraday FX volatility shows U-shape with double-peak (London open + NY open).
  - Long-memory parameter d ≈ 0.4-0.5 after deseasonalization.
  - Failing to deseasonalize causes biased GARCH estimates of persistence.
  - Two-component decomposition: deterministic seasonality × stochastic long-memory.
  - Macroeconomic announcements add jump-like spikes on top of the seasonal pattern.
- **Relevance to GTOS:** Methodologically critical for any volatility regime classifier (K54): don't fit GARCH on raw 5-min volatility, deseasonalize first using a kill-zone-aware filter. Otherwise persistence is overestimated and regime boundaries are spurious.
- **Potential hypothesis:** Recompute K54 features with kill-zone-deseasonalized volatility; expect cleaner regime separation in clusters than current implementation.
- **Cross-domain links:** 03 (long-memory); 04 (multifractal decomposition); 16 (vol regime)
- **Intraday window:** Full intraday

### Volume, Volatility, and Public News Announcements
- **Authors:** Tim Bollerslev, Jia Li, Yuan Xue
- **Year:** 2018
- **Source:** Review of Economic Studies 85(4): 2005-2041
- **URL:** https://public.econ.duke.edu/~boller/Published_Papers/restud_18.pdf
- **Abstract:** Develops a high-frequency identification of jumps in volume and volatility at scheduled macro announcement times, using non-parametric tests. Documents the differential response of volume vs. volatility to news.
- **Key findings:**
  - 7 of 25 largest absolute returns directly tied to news release in same / preceding interval.
  - Humphrey-Hawkins testimony causes ~2100% jump in volatility, ~93% jump in cumulative |return|.
  - Volume jumps on news are larger than volatility jumps; they decay slower.
  - Pre-announcement volatility *drops* significantly before scheduled announcements (calm-before-storm).
  - Bond markets respond more strongly than equities to macro news per unit announcement-importance.
- **Relevance to GTOS:** Direct support for the existing pre-AI H1 POI gate behavior on FOMC/NFP days, and for treating macro release windows as a separate evaluation regime. Volume's signal-to-noise improves around announcements but only post-release.
- **Potential hypothesis:** A 5-minute pre-NFP / pre-FOMC blackout (no new entries) would reduce sl_buffer 0.0 cluster on NAS100/US30. Test against existing trade record.
- **Cross-domain links:** 11 (macro / central banks); 17 (announcement effects)
- **Intraday window:** Specific (announcement-time)

### Liquidity and Volatility
- **Authors:** Itamar Drechsler, Alan Moreira, Alexi Savov
- **Year:** 2024
- **Source:** Review of Financial Studies (forthcoming) / NBER WP
- **URL:** https://pages.stern.nyu.edu/~asavov/alexisavov/Alexi_Savov_files/DMS_Liquidity_and_Volatility.pdf
- **Abstract:** Theoretical and empirical paper showing that liquidity provision is the residual after market-makers absorb order-flow imbalance, and that volatility, liquidity, and volume are jointly determined. The U-shape in spread / depth complements the U-shape in volume.
- **Key findings:**
  - Liquidity (depth) is U-shaped intraday but *inversely* — deepest at open and close, shallowest mid-day.
  - Spread is *not* U-shaped — wide at open, tightens to mid-day, slightly widens at close.
  - The "volume-volatility-liquidity" trinity has time-varying correlations across regimes.
  - Recent paper (2025) extends to show ∪-shape in Kyle-lambda is a calendar-time aggregation artifact; in trade-time the pattern is much weaker.
- **Relevance to GTOS:** Refines kill-zone risk profile. Open-of-London and NY are simultaneously "high-volume / deep-book" — meaning slippage *should* be lower there than mid-day, contradicting the naive "high-volatility = high-slippage" assumption. Important for execution.py decisions.
- **Potential hypothesis:** Slippage in execution.py is *lower* in the first 30 minutes of London / NY kill zones than the last 30 minutes, despite higher volatility. Test by joining slippage to kill-zone-bucket.
- **Cross-domain links:** 06 (microstructure liquidity); 16 (vol-liquidity)
- **Intraday window:** Open / mid / close

### Order Imbalance, Liquidity, and Market Returns
- **Authors:** Tarun Chordia, Richard Roll, Avanidhar Subrahmanyam
- **Year:** 2002
- **Source:** Journal of Financial Economics 65(1): 111-130
- **URL:** https://www.cis.upenn.edu/~mkearns/finread/Chordia_buy-sell_orders.pdf
- **Abstract:** Documents the daily-frequency relation between aggregate order imbalance (buy-initiated minus sell-initiated trades), market returns, and liquidity. Order imbalance is a powerful contemporaneous and (weakly) predictive variable.
- **Key findings:**
  - Order imbalance in either direction reduces liquidity (depth decreases when |OI| rises).
  - Sell-side imbalance impacts volatility ~4× more than buy-side imbalance (asymmetric).
  - Market returns reverse after large negative-imbalance / large negative-return days.
  - At weekly frequency, lagged order imbalance has weak but significant predictive power for returns.
  - Daily aggregate OI is highly persistent (long-memory).
- **Relevance to GTOS:** Directly motivates a `daily_order_imbalance_proxy` from tick volume + tick rule. Given the asymmetry, sell-side imbalance is potentially a stronger feature than buy-side.
- **Potential hypothesis:** A signed `tick_imbalance_5min` feature should have higher absolute SHAP for SHORT trades than LONG trades in K54, given the empirical asymmetry. This connects to GTOS's known LONG-side selectivity collapse (project F2).
- **Cross-domain links:** 06 (order-flow / Kyle-lambda); 13 (signed order flow as factor)
- **Intraday window:** Daily

---

## 2. VWAP and execution literature

### Optimal Execution of Portfolio Transactions
- **Authors:** Robert Almgren, Neil Chriss
- **Year:** 2000
- **Source:** Journal of Risk 3(2): 5-39
- **URL:** https://www.smallake.kr/wp-content/uploads/2016/03/optliq.pdf
- **Abstract:** The seminal optimal-execution paper. Constructs the efficient frontier in the space of time-dependent liquidation strategies trading off market-impact costs against volatility risk over the execution window. Introduces the concept of liquidity-adjusted VAR (L-VaR).
- **Key findings:**
  - Optimal liquidation strategy is a function of three quantities: total quantity, time horizon, and risk-aversion.
  - Linear permanent impact + quadratic transient impact gives a closed-form solution.
  - Risk-neutral execution is uniform-rate (TWAP); risk-averse is front-loaded.
  - VWAP-style is approximately optimal under flat-information / passive-impact assumptions.
  - The framework underpins essentially all modern algo execution.
- **Relevance to GTOS:** Academic baseline for the question "is a market order or a limit order better at the kill-zone open?" Currently `execution.py` uses limit orders by default; Almgren-Chriss says the choice depends on temporary impact estimate.
- **Potential hypothesis:** For setups in the first 5 minutes of London open (high impact, high volatility), a small split-order would beat single-shot limit. Out-of-scope for current size but a research candidate.
- **Cross-domain links:** 06 (Almgren-Chriss is the canonical microstructure execution paper); 20 (RL-for-execution variants)
- **Intraday window:** Mid / general

### VWAP Strategies
- **Authors:** Ananth Madhavan
- **Year:** 2002
- **Source:** Trading 2002(1): 32-39 (PMR Trading Journal)
- **URL:** https://www.smallake.kr/wp-content/uploads/2016/03/TP_Spring_2002_Madhavan.pdf
- **Abstract:** Practitioner-academic synthesis of VWAP execution. Documents the rise of VWAP as the institutional execution benchmark, discusses three components: pre-trade analysis, schedule determination, and execution monitoring. Acknowledges VWAP is conceptually simple but operationally complex.
- **Key findings:**
  - VWAP became dominant institutional benchmark in late 1990s / early 2000s.
  - Pre-trade analysis filters orders; some orders are not VWAP candidates.
  - Schedule generation must adapt to time-of-day volume seasonality (U-shape).
  - Naive VWAP underperforms when volume profile shifts intraday (event days).
  - Adaptive volume-tracking is the practical innovation.
- **Relevance to GTOS:** GTOS does not currently use VWAP execution but does benchmark fills against simulated mid-prices. Madhavan's pre-trade-analysis framing maps onto our pre-AI H1 POI gate — both are "is this a setup we should even attempt?" filters.
- **Potential hypothesis:** Adopting Madhavan-style pre-trade fill-cost estimation could front-load the rejection of high-impact-cost setups (likely the same setups that produce sl_buffer 0.0 patterns).
- **Cross-domain links:** 06 (execution); 20 (RL agents implementing VWAP)
- **Intraday window:** Full day

### Improving VWAP Strategies: A Dynamic Volume Approach
- **Authors:** Jędrzej Białkowski, Serge Darolles, Gaëlle Le Fol
- **Year:** 2008
- **Source:** Journal of Banking and Finance 32(9): 1709-1722
- **URL:** https://www.fbv.kit.edu/symposium/10th/papers/Bialkowski_Darolles_LeFol%20-%20Decomposing%20volume%20for%20VWAP%20strategies.pdf
- **Abstract:** Decomposes intraday volume into a *seasonal common component* (extracted via PCA across stocks in CAC40) and a *stock-specific dynamic component* (modeled as ARMA(1,1) or SETAR). Reduces VWAP execution risk substantially.
- **Key findings:**
  - Seasonal volume component is highly cross-sectionally synchronized — true "market-wide" pattern.
  - Stock-specific component is short-memory / mean-reverting.
  - Two-component decomposition reduces VWAP slippage by 5-30bps depending on stock.
  - PCA-extracted common factor explains 60-80% of intraday volume variance.
  - SETAR (regime-switching) outperforms ARMA on event days.
- **Relevance to GTOS:** Methodologically important for any cross-instrument volume normalization in `tick_features.py`. Suggests a 2-component model: extract a "market-wide kill-zone seasonality" factor across XAUUSD/US30/NAS100 and treat residual as instrument-specific signal.
- **Potential hypothesis:** Cross-asset residual volume (after removing kill-zone common factor) is the actually-informative volume signal. Test as feature in K54.
- **Cross-domain links:** 13 (cross-section common factors); 06 (execution)
- **Intraday window:** Full day

### Competitive Algorithms for VWAP and Limit Order Trading
- **Authors:** Sham M. Kakade, Michael Kearns, Yishay Mansour, Luis Ortiz
- **Year:** 2004
- **Source:** Proceedings of the 5th ACM Conference on Electronic Commerce: 189-198
- **URL:** https://www.cis.upenn.edu/~mkearns/papers/vwap.pdf
- **Abstract:** Provides the first online / competitive-ratio analysis of VWAP and limit-order trading. Derives algorithm classes whose worst-case performance ratio against optimal-in-hindsight is bounded.
- **Key findings:**
  - VWAP can be approximated to within a constant factor of optimal under realistic order-book models.
  - Limit-order placement under adversarial price dynamics has logarithmic regret bounds.
  - Algorithms exploit the structure of total-volume revelation (post-trade) to improve performance.
  - Theoretical bounds match empirical algorithm performance in 2003-2004 NYSE data.
  - Bridges machine-learning online-algorithms with finance execution.
- **Relevance to GTOS:** Theoretical foundation for the case "deterministic limit-order schedule beats market-order" used implicitly in `execution.py`. The competitive-ratio framing motivates worst-case analysis of slippage.
- **Potential hypothesis:** Adding bounded-regret execution analysis to GTOS would expose execution-quality decay (analogous to the OB-continuation decay) — a metric we don't currently track.
- **Cross-domain links:** 06 (LOB algorithms); 20 (online learning)
- **Intraday window:** Full day

### Optimal Liquidity-Based Trading Tactics
- **Authors:** Charles-Albert Lehalle, Othmane Mounjid, Mathieu Rosenbaum
- **Year:** 2018
- **Source:** arXiv 1803.05690
- **URL:** https://arxiv.org/abs/1803.05690
- **Abstract:** Models a trading agent that buys/sells a small quantity over a short window via a mix of limit orders, market orders, and cancellations. Uses dynamic-programming on a stylized order-book model.
- **Key findings:**
  - Optimal mix depends on current bid-ask imbalance and queue position.
  - Limit-order optimal in low-volatility / low-imbalance states; market-order optimal in high-imbalance states.
  - Cancellation policy is governed by adverse-selection probability.
  - Out-of-sample on Euronext data: 5-15bps savings vs. naive limit-only.
  - Generalizes Almgren-Chriss with explicit LOB modeling.
- **Relevance to GTOS:** Most directly relevant to a Phase-2 execution upgrade. Currently we treat market vs. limit as a static config flag; Lehalle et al. show the choice should be state-conditional.
- **Potential hypothesis:** A simple imbalance-conditioned execution-mode flag (limit if `bid_size/ask_size` ratio in [0.5, 2.0], market otherwise) would reduce slippage with no other change. Test in shadow.
- **Cross-domain links:** 06 (LOB-based execution); 20 (RL execution agents)
- **Intraday window:** Mid / general

---

## 3. Auction theory and Market Profile

### Markets, Profile, and Method: A Trader's Theory (Steidlmayer Series)
- **Authors:** J. Peter Steidlmayer (with Steven B. Hawkins)
- **Year:** 1984+ (multi-volume); definitive 2003 edition Wiley
- **Source:** Wiley (Steidlmayer on Markets) and CBOT publications 1984-1986
- **URL:** Reference: https://en.wikipedia.org/wiki/Market_profile (Wikipedia overview); https://atas.net/market-theory/the-auction-market-theory/ (introductory summary). Original CBOT publications not freely online — practitioner classic.
- **Abstract:** The original framework distinguishing "price advertising opportunity," "time regulating price opportunity," and "volume measuring success of the auction." Defines TPO (Time-Price-Opportunity), Value Area (typically 70% of volume / 1σ), and Point of Control (POC).
- **Key findings (as documented in Steidlmayer-derived literature):**
  - Markets oscillate between balance (Value-Area-bound) and imbalance (initiative move) states.
  - The previous-day Value Area Low (VAL) and Value Area High (VAH) act as magnets / barriers in the next session.
  - POC = price level with highest TPO count = market's "fair value" assessment.
  - Single-prints (TPO=1 levels) often act as resistance / support on retest.
  - Auction terminates when a price stops attracting time / volume — operational rotation rule.
- **Relevance to GTOS:** The auction-theoretic concepts of "balance" vs. "trend" map onto GTOS's regime classifier (`regime_classifier.py`). Specifically, the "trending_bull / trending_bear" state corresponds to Steidlmayer's "initiative move," and "balanced_chop" corresponds to "responsive / mean-reverting" auction state.
- **Potential hypothesis:** Augmenting `regime_classifier.py` with a daily-VAL/VAH/POC feature should give measurable lift in F2 cells (LONG decay in trending_bull) since it provides a non-redundant view on the same regime axis.
- **Cross-domain links:** 07 (ICT/SMC also uses POI / order-block concepts derived from same auction intuitions); 14 (trend / momentum)
- **Intraday window:** Full day (the Profile is by-construction a daily aggregate)

### Auction Market Theory: Foundational Synthesis
- **Authors:** Mark Fisher, Jim Dalton, Robert Dalton (and others extending Steidlmayer)
- **Year:** 1990s-2000s
- **Source:** "Mind Over Markets" (Dalton), "Markets in Profile"
- **URL:** Practitioner-classic; reviewed in https://atas.net/market-theory/the-auction-market-theory/ ; academic overview at https://blog.tradingriot.com/p/auction-market-theory
- **Abstract:** Extends Steidlmayer's framework into practical trading rules. Codifies "responsive" vs. "initiative" trading, the role of Initial Balance (first hour), and overnight inventory effects on the cash-session opening type.
- **Key findings:**
  - Initial Balance (IB) — first 60 minutes — defines the day's "opening type" (open-drive, open-test-drive, open-rejection-reverse, open-auction).
  - Open-drive days have ~80% directional follow-through (anecdotal — limited academic confirmation).
  - Overnight inventory longs/shorts predict cash-session reversal probability.
  - The Profile rotation hypothesis is essentially a regime-conditional mean-reversion vs. trend prediction.
  - Value migration (today's VA shifting from yesterday's VA) signals trend continuation.
- **Relevance to GTOS:** Operational kill-zone work and Initial-Balance concepts overlap with GTOS's existing "first hour after London open" emphasis. Would benefit GTOS to formalize Initial-Balance-style features in `tick_features.py`.
- **Potential hypothesis:** Days where price breaks the IB high/low *within the first 30 minutes of NY kill zone* are high-conviction setups; quantify in shadow.
- **Cross-domain links:** 07 (ICT/SMC POI rules are auction-theory derivatives); 14 (trend continuation)
- **Intraday window:** Open / IB-specific

### Volume Profile Empirical Literature (composite — Quantpedia, RainmakerTrade, others)
- **Authors:** various practitioner-academic
- **Year:** 2018-2025
- **Source:** Quantpedia.com, RainmakerTrade Substack, journalled volume-profile backtests
- **URL:** https://www.quantifiedstrategies.com/value-area-trading-strategy/ ; https://atas.net/market-theory/the-auction-market-theory/
- **Abstract:** Practitioner backtests of Value Area / POC / Single-Print mean-reversion and breakout rules on equity index futures and FX. Generally find weak but positive Sharpe in some subsamples.
- **Key findings:**
  - "Fade outside Value Area / target POC" rule earns positive Sharpe (~0.4-0.7) on ES futures 2010-2020 in some specifications.
  - Effect weakens substantially in instruments with continuous 24h sessions (FX) where the Profile is less well-defined.
  - Single-print retests succeed ~55-60% of the time on liquid futures (small edge).
  - Value Area Low support during bull regimes is stronger than Value Area High resistance — asymmetric.
  - Most "rules" are essentially regime-conditional mean-reversion in disguise.
- **Relevance to GTOS:** Mostly negative (low Sharpe, weak effects) but informative — Volume Profile rules are *not* a replacement for OB/FVG zones. Confirms our edge mechanism (zone + impulse) sits closer to ICT than to pure-Profile.
- **Potential hypothesis:** Adding a "POC-distance" continuous feature to K54 may capture small residual signal not in OB-zone detection. Modest expected lift.
- **Cross-domain links:** 07 (ICT/SMC); 09 (level magnetism); 14 (mean reversion)
- **Intraday window:** Daily

---

## 4. OPEX, dealer-gamma, and option-induced flows on cash markets

### Stock Price Clustering on Option Expiration Dates
- **Authors:** Sophie X. Ni, Neil D. Pearson, Allen M. Poteshman
- **Year:** 2005
- **Source:** Journal of Financial Economics 78(1): 49-87
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S0304405X05000577
- **Abstract:** Documents that on option-expiration Fridays, closing prices of optionable stocks cluster at strike prices to a statistically and economically significant degree. Provides decomposition into market-maker hedging vs. firm-proprietary manipulation.
- **Key findings:**
  - Closing prices of optionable stocks cluster within $0.125 of strike on expiration Fridays at significantly higher frequency than non-expiration Fridays.
  - On each expiration date, returns of optionable stocks are altered by ≥16.5bps on average.
  - Aggregate market-cap movement attributable to pinning ≈ $9 billion per expiration.
  - Hedge-rebalancing by market-makers contributes ~50% of the effect.
  - Firm proprietary traders contribute the residual via potentially-manipulative strategies.
- **Relevance to GTOS:** Direct evidence that the third Friday of each month is a special regime for optionable underlyings. NAS100 and US30 (index futures with options) are subject to derivative-style pinning effects from SPX/NDX option pinning even though they are not themselves "options."
- **Potential hypothesis:** Restrict NAS100/US30 trading to non-OPEX-Fridays for the next 6 months as a shadow A/B test of OPEX-day decay.
- **Cross-domain links:** 12 (equity-index gamma flow specifically); 09 (round-number / strike clustering)
- **Intraday window:** Daily / OPEX-Friday-specific

### Pinning in the S&P 500 Futures
- **Authors:** Benjamin Golez, Jens Carsten Jackwerth
- **Year:** 2012
- **Source:** Journal of Financial Economics 106(3): 566-585
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S0304405X12001365
- **Abstract:** Extends pinning evidence to S&P 500 futures (the most liquid equity-index instrument). Documents that ES futures are pulled toward the at-the-money strike on serial-option expiration days.
- **Key findings:**
  - ES futures pinning occurs on serial (monthly, non-quarterly) option-on-future expiration days.
  - Effect magnitude is ~5-10bps over the morning of expiration day.
  - ATM-option volume on expiration day is positively correlated with pinning probability.
  - Market-makers in ES options are net-short → delta-hedge by selling on rallies / buying on dips.
  - Cash-settled (e.g., quarterly SPX) expirations have weaker pinning than physically-settled.
- **Relevance to GTOS:** Most directly applicable paper for US30 cash and NAS100 cash, which are linked to ES / NQ futures and SPX / NDX option flow. Predicts that GTOS edge in those instruments will be *weakest* on serial-option-expiration mornings.
- **Potential hypothesis:** Stratify NAS100 / US30 historical realized R by serial-OPEX-Friday vs. all other days; expect lower expected R on OPEX (matches HALLUC-1 pattern).
- **Cross-domain links:** 12 (gamma flow specifically); 09 (round-number magnetism)
- **Intraday window:** OPEX-day morning

### Does Net Buying Pressure Affect the Shape of Implied Volatility Functions?
- **Authors:** Nicolas P. B. Bollen, Robert E. Whaley
- **Year:** 2004
- **Source:** Journal of Finance 59(2): 711-753
- **URL:** https://onlinelibrary.wiley.com/doi/10.1111/j.1540-6261.2004.00647.x
- **Abstract:** Documents that net buying pressure from public order flow (proxy: signed option volume) directly shifts the shape of the implied volatility function. Index-option IV is most affected by put-buying pressure; stock-option IV by call demand.
- **Key findings:**
  - Index put net-buying pressure → IV skew steepens; effect is contemporaneous and short-lived.
  - Stock call net-buying pressure → ATM IV rises; cross-sectional dispersion in IV widens.
  - Limits-of-arbitrage hypothesis explains persistence of IV deviations from theoretical no-arbitrage.
  - Demand-pressure effects accumulate over the trading day, peak near close.
  - Smile shape responds asymmetrically to call vs put pressure → fundamental violation of B-S.
- **Relevance to GTOS:** Establishes the channel through which dealer-gamma exposure builds intraday. The IV-skew dynamics directly feed back into delta-hedging requirements that affect cash-market price action — the chain Bollen-Whaley → Garleanu-Pedersen → Barbon-Buraschi.
- **Potential hypothesis:** A daily skew-pressure proxy (put-call vol ratio extreme) should predict NAS100 next-day intraday momentum / reversal regime, useful as a K54 feature.
- **Cross-domain links:** 12 (IV-skew driver); 16 (vol regime)
- **Intraday window:** Daily / contemporaneous

### Demand-Based Option Pricing
- **Authors:** Nicolae Gârleanu, Lasse Heje Pedersen, Allen M. Poteshman
- **Year:** 2009
- **Source:** Review of Financial Studies 22(10): 4259-4299
- **URL:** http://docs.lhpedersen.com/DBOP.pdf
- **Abstract:** Builds equilibrium model in which option market-makers cannot perfectly hedge inventory; consequently, end-user demand pressure feeds through into option prices. Proves the impact is proportional to the variance of the unhedgeable risk.
- **Key findings:**
  - Demand pressure for option contract i raises its price by an amount ∝ unhedgeable variance of i.
  - Cross-effect: demand for i raises prices of j by ∝ covariance of unhedgeable parts.
  - Empirically, demand explains the index-option expensive-puts puzzle and the skew shape.
  - Single-stock options also exhibit demand-pressure-driven cross-section in expensiveness.
  - Foundational paper for "dealer-positioning matters" theme that drives modern OPEX/GEX literature.
- **Relevance to GTOS:** Establishes the academic legitimacy of dealer-positioning being a *first-order* driver of cash-market and derivative-market dynamics. NAS100/US30 dealer positioning therefore matters for our trading on those instruments even though we don't trade options.
- **Potential hypothesis:** A simple GEX-sign feature (positive vs negative aggregate dealer gamma) should partition NAS100 intraday R distribution. Test on existing trades.
- **Cross-domain links:** 12 (option pricing under demand); 16 (vol risk premium)
- **Intraday window:** Daily

### Gamma Fragility
- **Authors:** Andrea Barbon, Andrea Buraschi
- **Year:** 2021
- **Source:** SSRN 3725454 (working paper, presented at multiple top conferences)
- **URL:** https://www.abarbon.com/assets/Barbon_Buraschi_2021_Gamma_Fragility.pdf
- **Abstract:** Documents a novel link between aggregate dealer gamma imbalances and intraday momentum / reversal in stock returns. The mechanism is feedback from delta-hedging in the option market into the underlying market.
- **Key findings:**
  - Negative aggregate gamma → intraday momentum (stock moves get amplified by hedging).
  - Positive aggregate gamma → intraday reversal (stock moves are dampened by hedging).
  - Effect strongest in less-liquid stocks (illiquidity is the friction that lets hedging move price).
  - Distinct from information-frictions and funding-liquidity-frictions channels.
  - Validates the gamma-positioning channel as an empirical regularity, not just a theoretical possibility.
- **Relevance to GTOS:** Most directly relevant theoretical paper for the question "should GTOS be afraid of NAS100 OPEX days more than non-OPEX days?" Answer is yes: dealer gamma typically peaks near OPEX with mid-month dynamics potentially flipping reversal-vs-momentum regime.
- **Potential hypothesis:** Compute a poor-man's GEX proxy (using publicly-available SpotGamma / SqueezeMetrics free data) and bucket NAS100 trades by gamma sign; expect H2 LONG decay to concentrate on negative-gamma days.
- **Cross-domain links:** 12 (gamma flow); 16 (vol regime); 17 (intraday momentum / behavior)
- **Intraday window:** Full intraday

### Where Does Gamma Hedge Drive the Intraday Market Move?
- **Authors:** AFA-PhD-job-market candidate (~2024 paper, awaiting top-journal publication)
- **Year:** 2024
- **Source:** AFA 2024 paper presentation
- **URL:** https://afajof.org/management/viewp.php?n=129472
- **Abstract:** Identifies the *Gamma-Theta Breakeven Range* (GTBR) — the price range within which dealers' gamma + theta P&L is balanced. Beyond GTBR, dealers must rebalance, creating inelastic demand for the underlying.
- **Key findings:**
  - GTBR boundaries serve as inflection points for nonlinear intraday momentum.
  - Within GTBR, dealers do not rebalance → cash market behaves "normally."
  - Outside GTBR, hedging accelerates → trend extension.
  - Inelastic demand is amplified by professional-investor option demand (not just retail).
  - Empirical tests on SPX confirm GTBR boundaries are predictable from open-interest data.
- **Relevance to GTOS:** Quantifies the conditions under which dealer-gamma flow becomes load-bearing (vs. background noise). Most days, gamma is *not* the dominant driver; the question is identifying when it is.
- **Potential hypothesis:** GTOS should add a daily "GTBR-boundary-distance" feature for NAS100 and US30; trade outside GTBR is high-momentum-amplification regime.
- **Cross-domain links:** 12 (gamma flow); 16 (intraday vol regime)
- **Intraday window:** Full intraday

### Hedging Demand and Market Intraday Momentum
- **Authors:** Guido Baltussen, Zhi Da, Sten Lindberg, Anders Pearce
- **Year:** 2021
- **Source:** Journal of Financial Economics (2021)
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S0304405X21001598 ; https://www3.nd.edu/~zda/intramom.pdf
- **Abstract:** Connects intraday-momentum (Gao-Han-Li-Zhou 2018) directly to option-market-maker negative-gamma exposure. Shows that intraday momentum strengthens when net-MM-gamma is more negative.
- **Key findings:**
  - Sign of MM-gamma is a strong moderator of the intraday-momentum strategy.
  - When MM-gamma negative: first-30-min return predicts last-30-min return with strong R² (~5-8%).
  - When MM-gamma positive: predictability collapses to near-zero.
  - Effect is robust across 2007-2018 and across SPY, QQQ, IWM.
  - Provides clean identification: gamma-positioning is the missing variable in older intraday-momentum literature.
- **Relevance to GTOS:** Direct application to NAS100. If MM-gamma is publicly inferable on a given day, GTOS should down-weight afternoon entries on positive-gamma days (mean-reversion regime) and possibly up-weight on negative-gamma days.
- **Potential hypothesis:** Bucket NAS100 historical realized R by tertile of inferred MM-gamma; expect monotonic increase in afternoon kill-zone realized R from positive → negative gamma.
- **Cross-domain links:** 12 (gamma); 14 (intraday momentum)
- **Intraday window:** Full day, especially close

### A Market-Induced Mechanism for Stock Pinning
- **Authors:** Marco Avellaneda, Mike Lipkin
- **Year:** 2003
- **Source:** Quantitative Finance 3(6): 417-425
- **URL:** https://math.nyu.edu/inmemoriam/avellaneda//qf3601.pdf
- **Abstract:** Mathematical model deriving stock pinning as the equilibrium of delta-hedging by floor market-makers. Shows pinning probability increases with open interest, decreases with volatility, and increases with proximity to expiration.
- **Key findings:**
  - Stochastic-DE for stock price has singular drift toward strike, scaled by open interest.
  - Pinning probability: P(pin) = function(σ, OI, T, price-elasticity).
  - High-OI strikes near expiration → P(pin) approaches 1 for low-volatility stocks.
  - Mechanism: market-makers selling rallies / buying dips around strike.
  - Numerical results match Ni-Pearson-Poteshman empirical magnitudes.
- **Relevance to GTOS:** Theoretical basis for why kill-zone-bound trading near round-number levels (which often coincide with high-OI strikes) is structurally disadvantaged on OPEX-Fridays. Connects directly to A4 trending_bull replay finding (sl_buffer 0.0 patterns near round numbers).
- **Potential hypothesis:** GTOS-rejected trades on OPEX-Fridays where the SL is set within $5-$10 of a round-number / strike will systematically have worse realized-R than non-OPEX equivalents.
- **Cross-domain links:** 09 (round-numbers); 12 (gamma flow); 16 (vol-regime)
- **Intraday window:** Daily / OPEX-day-specific

### Mathematical Models for Stock Pinning near Option Expiration Dates
- **Authors:** Marco Avellaneda, Gennady Kasyan, Mike Lipkin
- **Year:** 2012
- **Source:** Communications on Pure and Applied Mathematics 65(7): 949-976
- **URL:** https://www.researchgate.net/publication/260742282_Mathematical_Models_for_Stock_Pinning_near_Option_Expiration_Dates
- **Abstract:** Extends Avellaneda-Lipkin (2003) with multi-strike pinning, time-dependent gamma, and improved numerical methods. Refines the price-elasticity calibration.
- **Key findings:**
  - Multi-strike interaction: pinning at strike A is suppressed by high OI at adjacent strikes.
  - Time-dependent gamma: pinning probability accelerates in the last 4 hours before expiration.
  - Calibration on US large-cap stocks: price-elasticity ≈ 1.5-3 / billion-dollar-OI.
  - Pinning probability sensitivity to volatility: dP/dσ < 0 (pinning kills in high-vol regimes).
  - Out-of-sample test 2008-2010: model-predicted pin rate matches realized within 15%.
- **Relevance to GTOS:** Refinement of pinning theory to multi-strike, time-dependent setting — closer to actual NAS100/US30 OPEX dynamics with multiple strikes alive.
- **Potential hypothesis:** Restrict NAS100 trading to before noon UTC on OPEX-Fridays, since pinning probability accelerates in the last 4 hours.
- **Cross-domain links:** 12 (gamma flow); 09 (multi-strike clustering)
- **Intraday window:** OPEX-day, last 4 hours

### Does Option Trading Have a Pervasive Impact on Underlying Stock Prices?
- **Authors:** Sophie X. Ni, Neil D. Pearson, Allen M. Poteshman, Joshua S. White
- **Year:** 2021
- **Source:** Review of Financial Studies 34(4): 1952-1986
- **URL:** https://academic.oup.com/rfs/article-abstract/34/4/1952/5873587
- **Abstract:** The "everyday" gamma-pinning paper. Shows that option-market-maker hedging has a measurable, statistically-significant impact on underlying stock prices on *every* trading day, not just expiration. Decomposes into informational and noninformational channels.
- **Key findings:**
  - Negative relation between stock return volatility and net purchased option positions of likely-hedgers.
  - The effect is "first evidence for substantial and pervasive influence of option trading on stock prices" (every-day, not just OPEX).
  - Informational channel: option-market info gets impounded into underlying via hedging trades.
  - Noninformational channel: hedge rebalancing creates mean-reverting / amplification flow.
  - Decomposition is approximately 50:50 between channels.
- **Relevance to GTOS:** Important rebalancing of OPEX-only thinking. Dealer-gamma effects are present *every day*, not just on OPEX. The OPEX-day effect is a magnitude amplification, not a regime change.
- **Potential hypothesis:** Adding a continuous daily-gamma-magnitude feature should add lift across all NAS100/US30 trades, with an interaction effect on OPEX-Friday.
- **Cross-domain links:** 12 (gamma flow); 06 (info channel)
- **Intraday window:** Daily

### 0DTE Index Options and Market Volatility: How Large is Their Impact?
- **Authors:** Aurelio Vasquez, Diego Amaya, Neil D. Pearson, Pedro A. Garcia-Ares (Cboe-supported)
- **Year:** 2024
- **Source:** Cboe research / SSRN 5113405
- **URL:** https://cdn.cboe.com/resources/education/research_publications/gammasqueezes.pdf
- **Abstract:** Estimates the maximum impact of options market-maker gamma on SPX index volatility, using proprietary trade data to determine aggregate OMM positions.
- **Key findings:**
  - Customer 0DTE flow is much more balanced (puts vs calls, longs vs shorts) than narrative suggests.
  - Net MM gamma hedging is at most ~0.2% of SPX daily liquidity.
  - 0DTEs *do not* materially destabilize SPX volatility through hedging.
  - 0DTE flow is dominated by short-vol selling (covered puts/calls) — gamma exposure is moderate.
  - Estimated upper bound on volatility impact: ~5% of realized vol.
- **Relevance to GTOS:** Tempers the apocalyptic 0DTE-narrative. NAS100 / US30 are influenced by SPX dynamics, but 0DTE-specific gamma flow is bounded above. The L2 sl_buffer 0.0 pattern is unlikely to be primarily 0DTE-driven.
- **Potential hypothesis:** No specific GTOS hypothesis derived; this paper is a *negative* result tempering an otherwise compelling narrative.
- **Cross-domain links:** 12 (gamma); 16 (vol)
- **Intraday window:** Full intraday

### 0DTEs: Trading, Gamma Risk, and Volatility Propagation
- **Authors:** Chukwuma Dim, Bjørn Eraker, Grigory Vilkov
- **Year:** 2024
- **Source:** SSRN 4692190
- **URL:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4692190
- **Abstract:** Tests whether high-OI 0DTE positions propagate intraday volatility shocks. Result: no, they do not amplify recent index returns despite the popular narrative.
- **Key findings:**
  - 0DTE OI gamma does *not* propagate past volatility into future intraday returns.
  - 0DTE-underlying integration has increased over time (positive correlation rising).
  - Intraday 0DTE volume shocks do *not* amplify recent index returns.
  - Result is *inconsistent* with view that 0DTE growth intensifies fragility.
  - Possibly because customer flow is two-sided / dealers' net gamma is contained.
- **Relevance to GTOS:** Reinforces Vasquez et al. negative result. Empirical gamma-fragility *for 0DTEs specifically* is weaker than feared. NAS100/US30 risk profile should not be aggressively shifted on perceived 0DTE risk alone.
- **Potential hypothesis:** Same as 0DTE-Cboe paper — no major hypothesis change beyond "don't over-react to 0DTE narrative."
- **Cross-domain links:** 12 (gamma); 16 (vol)
- **Intraday window:** Full intraday

### Gamma Positioning and Market Quality
- **Authors:** Buis, Pieterse-Bloem, Verschoor, Zwinkels
- **Year:** 2024
- **Source:** Journal of Economic Dynamics and Control
- **URL:** https://www.sciencedirect.com/science/article/pii/S0165188924000721
- **Abstract:** Studies how dealer gamma positioning affects market-quality measures (depth, spread, intraday volatility). Uses simulation to identify mechanism.
- **Key findings:**
  - Both positive *and* negative dealer gamma positions increase order book volume.
  - Effect is asymmetric: positive gamma → more depth; negative gamma → more flow.
  - Distributions of intraday returns shift with gamma sign (heavier left tails for negative gamma).
  - Empirical literature scarcity due to proprietary data — simulation is a feasible workaround.
  - Provides a falsifiable model that can be calibrated to public data (open-interest based).
- **Relevance to GTOS:** Reinforces dealer-gamma as a state variable that should enter K54 (regime classifier). The empirical-data-scarcity caveat is honest and methodologically important — practitioner-data approximations (SqueezeMetrics, SpotGamma) are necessary substitutes.
- **Potential hypothesis:** Use public-data dealer-gamma proxy as K54 feature; expected interaction with intraday-momentum sign.
- **Cross-domain links:** 12 (gamma); 06 (market quality / depth)
- **Intraday window:** Daily / aggregate

### The Equity Derivative Payoff Bias
- **Authors:** Guido Baltussen, Julian Terstegge, Paul Whelan
- **Year:** 2024 (presented AFA 2025)
- **Source:** SSRN 4562800
- **URL:** https://afajof.org/management/viewp.php?n=98196
- **Abstract:** Documents that the third-Friday-of-the-month market-open ("AM settlement") for SPX index options shows a statistically significant abnormal return pattern, with concentrated 18.2bps gap on expiry-Fridays vs 1.3bps on non-expiry days post-2003.
- **Key findings:**
  - Post-2003: ~17bps abnormal positive open-gap on expiration Fridays vs non-expiration.
  - Effect is concentrated specifically in the AM settlement (Special Opening Quotation) window.
  - Two competing explanations: (a) dealer hedging into the SOQ; (b) deliberate manipulation by holders of large option positions.
  - Authors lean toward "manipulator" interpretation given gap reverses post-settlement.
  - Effect is robust to controls; cross-sectional pattern indicates targeted manipulation.
- **Relevance to GTOS:** Direct evidence that NAS100/US30 cash open on third Fridays is *not* a fair-value signal. GTOS's pre-AI POI evaluation in this window is at structurally elevated risk.
- **Potential hypothesis:** Skip first 30 minutes of NAS100/US30 sessions on OPEX-Fridays. Test as additive shadow gate.
- **Cross-domain links:** 12 (gamma flow); 17 (manipulation / behavioral); 09 (round-number/strike)
- **Intraday window:** Open / OPEX-Friday-specific

### Liquidity Provision to Leveraged ETFs and Equity Options Rebalancing Flows
- **Authors:** Andrea Barbon, Heiner Beckmeyer, Andrea Buraschi, Mathis Moerke
- **Year:** 2022
- **Source:** SSRN 3925725 / Swiss Finance Institute Research Paper
- **URL:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3925725
- **Abstract:** Joint analysis of leveraged ETF rebalancing and equity-option-dealer hedging flows in the closing-auction period. Both are mechanically driven by the day's intraday move and concentrate in the last 30 minutes.
- **Key findings:**
  - 1σ increase in gamma-hedging-pressure → -113% of average last-30-min return (depresses).
  - 1σ increase in LETF rebalancing flow → +430% of average last-30-min return (amplifies).
  - LETF flows tend to attract more competitive liquidity provision (shorter-lived effects).
  - During Feb-Mar 2020 Covid sell-off, the effects compounded — last-30-min was a key vol generator.
  - Combined model has R² ~10% on last-30-min equity-index returns.
- **Relevance to GTOS:** US30 / NAS100 last-30-minute behavior is mechanically driven by these flows. GTOS does not currently restrict trading near close, but academic evidence is strong that this window has different statistical properties.
- **Potential hypothesis:** Restricting NAS100/US30 to *not* enter new trades after 19:30 UTC (last 30 min of NY) would reduce sl_buffer 0.0 cluster.
- **Cross-domain links:** 12 (gamma); 13 (passive flows / cross-section)
- **Intraday window:** Close (last 30 minutes)

---

## 5. FX fixings and end-of-day mechanical flows

### Foreign Exchange Fixings and Returns Around the Clock
- **Authors:** Ingomar Krohn, Philippe Mueller, Paul Whelan
- **Year:** 2024
- **Source:** Journal of Finance 79(1): 479-526
- **URL:** https://onlinelibrary.wiley.com/doi/10.1111/jofi.13306
- **Abstract:** Documents a "W-shaped" pattern in USD returns around the clock, with the USD appreciating in the run-up to FX fixes (Tokyo 9:55 / London 4pm / NY 5pm) and depreciating thereafter. Pattern is statistically significant over 21-year sample.
- **Key findings:**
  - W-shaped intraday return pattern with reversal points at major fixes.
  - For top-9 currencies, return reversals at fixes are pervasive and economically large (~$1B daily swings on $9.5T notional).
  - Mechanism: FX dealers intermediate unconditional USD demand at fixes, building inventory positions that reverse afterwards.
  - Natural-experiment identification (timing changes around methodology revisions) confirms the causal channel.
  - Effect persists post-2015 reform (window extended from 1min to 5min), although magnitude reduced.
- **Relevance to GTOS:** Direct, important paper for USDJPY and GBPJPY (both quote-USD pairs and yen-cross pairs sit near Tokyo 9:55 fix). Confirms that the 30-minute windows around 9:55 / 16:00 / 17:00 UTC are NOT random walks. Currently GTOS treats these uniformly with non-fix windows.
- **Potential hypothesis:** Adding a "minutes-to-nearest-fix" continuous feature to K54 should partition USDJPY / GBPJPY realized R, especially for trades opened within ±15 min of a fix.
- **Cross-domain links:** 11 (FX fixing macro); 06 (microstructure inventory channel)
- **Intraday window:** Tokyo 9:55 / London 16:00 / NY 17:00 UTC

### Equity Hedging and Exchange Rates at the London 4pm Fix
- **Authors:** Michael Melvin, John Prins
- **Year:** 2014
- **Source:** Journal of International Financial Markets, Institutions and Money
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S1386418114000779
- **Abstract:** Mechanism paper for the London 4pm fix: equity-portfolio managers who hedge currency exposure on a monthly/quarterly cycle generate large, predictable FX flows concentrated at the WM/R fix.
- **Key findings:**
  - Equity-hedging FX flow is strongly correlated with month-end USD-equity returns (signed).
  - Flow magnitude largest on month-end / quarter-end days (vs mid-month).
  - Effect pre-fix: USD trends in direction of expected demand.
  - Effect post-fix: partial reversal as flow exhausts.
  - Provides natural experiment around WM/R methodology change in 2015.
- **Relevance to GTOS:** Specific predictive variable for GBPUSD / EURUSD month-end behavior. GTOS's cross-instrument correlation gate may misfire on these days.
- **Potential hypothesis:** Add "is-month-end" and "is-quarter-end" boolean to K54 and the correlation gate; expect re-alignment of correlation regime on these specific days.
- **Cross-domain links:** 11 (FX); 13 (cross-asset rebalancing); 17 (calendar effect)
- **Intraday window:** London 16:00 fix; month-end concentration

### Did the Reform Fix the London Fix Problem?
- **Authors:** Martin D.D. Evans, Peter O'Neill, Dagfinn Rime, Jo Saakvitne
- **Year:** 2018
- **Source:** NBER Working Paper 23327
- **URL:** https://www.nber.org/system/files/working_papers/w23327/w23327.pdf
- **Abstract:** Tests whether the 2015 reform of the WM/Reuters 4pm fix (extending window from 1 to 5 minutes) reduced manipulation. Finds that abnormal volatility around the fix decreased materially but did not vanish.
- **Key findings:**
  - Pre-2015: ~80% of abnormal volatility around fix could be attributed to suspected collusion/manipulation.
  - Post-2015: reform reduced abnormal volatility by ~40-50% (not eliminated).
  - Persistent post-fix reversal pattern remains, consistent with inventory-rebalancing rather than manipulation.
  - Implication: even with reform, the fix is NOT a fair-value reference for risk management at minute-frequency.
  - Provides a clean before/after natural experiment for fix mechanics.
- **Relevance to GTOS:** Confirms even after reform, GBPUSD / EURUSD / USDJPY behavior at London 16:00 is structurally biased. Important for execution-window decisions.
- **Potential hypothesis:** Restricting USDJPY / GBPUSD entries to outside ±15 min of London fix should reduce slippage variance.
- **Cross-domain links:** 11 (FX manipulation); 06 (microstructure)
- **Intraday window:** London 16:00 ±15min

### Puzzles in the Forex Tokyo "Fixing": Order Imbalances and Biased Pricing by Banks
- **Authors:** Takatoshi Ito, Masahiro Yamada
- **Year:** 2017
- **Source:** Journal of International Economics 109: 214-234 (NBER WP 22820)
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S0022199617301204
- **Abstract:** Documents that the Tokyo 9:55 ("仲値" / chuugai) fix shows abnormal volume and pricing biases, with banks systematically setting fixing rates above the median transaction price.
- **Key findings:**
  - "Spike" frequency around Tokyo fix exceeds London-fix frequency by ~30%.
  - Pre-2008: banks announced fixing rates often higher than highest-observed transaction price (skewing).
  - Post-2008 (greater scrutiny): bias reduced but persisted (still above median).
  - Effect translates to consistent profit margin for banks at customer expense.
  - Annualized USD-index pre-fix appreciation ~5.3% / post-fix depreciation ~5.5% (round-trip).
- **Relevance to GTOS:** Direct, important paper for USDJPY at the 00:00-03:00 UTC kill zone. The 00:55 UTC fix behavior is non-trivial — Tokyo price action is biased relative to fair value. GTOS should NOT enter trades within ±15 min of 00:55 UTC.
- **Potential hypothesis:** Stratifying USDJPY trades by "within-±15-min-of-Tokyo-fix" vs not, expect lower realized R in the fix-window.
- **Cross-domain links:** 11 (FX); 06 (price discovery / dealer biased pricing)
- **Intraday window:** Tokyo 00:55 UTC ±15min

### Foreign Exchange Market Microstructure and the WM/Reuters 4pm Fix
- **Authors:** Ian Marsh, Panayiotis Andreou, others
- **Year:** 2017
- **Source:** Working paper, ResearchGate
- **URL:** https://www.researchgate.net/publication/271710273_Foreign_Exchange_Market_Microstructure_and_the_WMReuters_4pm_Fix
- **Abstract:** Detailed microstructure analysis of WM/R fix: order-flow patterns, dealer behavior, and post-fix reversals.
- **Key findings:**
  - Inter-dealer order flow is sharply skewed in the 5-minute window pre-fix.
  - Post-fix reversal pattern is more pronounced for "fill-at-fix" customer orders.
  - Volume during the fix window is 5-10× normal volume on month-ends.
  - Coordinated dealer behavior (allowed pre-2015) contributed to magnitude.
  - Provides empirical support for both inventory-channel and (residual) collusion-channel.
- **Relevance to GTOS:** Reinforces Krohn-Mueller-Whelan and Evans et al. — the fix windows are predictably noisy. Dealer-flow asymmetry quantitatively documented.
- **Potential hypothesis:** GTOS-rejected trades within fix-windows should have *much-greater* slippage than median; quantify in shadow.
- **Cross-domain links:** 11 (FX); 06 (microstructure)
- **Intraday window:** London 16:00 fix

### To Fix or Not to Fix: Representativeness of WM/R Methodology
- **Authors:** various (pre-registered report)
- **Year:** 2024
- **Source:** Pacific-Basin Finance Journal 84
- **URL:** https://www.sciencedirect.com/science/article/pii/S0927538X24000623
- **Abstract:** Pre-registered evaluation of post-reform WM/R methodology: representativeness, attainability, and robustness. Comprehensive 5-minute-window vs 1-minute-window comparison.
- **Key findings:**
  - 5-minute window better tracks order-book median than 1-minute window.
  - Robustness to single-trade manipulation improved substantially.
  - Representativeness for non-major-pair currencies still problematic.
  - "Window-end" boundary effects remain: prices accelerate at the closing bound.
  - Recommendation: further extend window to 10 minutes for cross-pair fixes.
- **Relevance to GTOS:** Methodological paper documenting the *evolution* of fix mechanics. Confirms that even a "fixed" fix is not fair-value at sub-minute frequency.
- **Potential hypothesis:** Aside from the fix itself, the *boundary* (3:57 / 4:02 UTC) shows price-acceleration. Intra-window exits may benefit from this but new entries should avoid it.
- **Cross-domain links:** 11 (FX); 06 (benchmark methodology)
- **Intraday window:** London 16:00 fix ±5min

---

## 6. End-of-day, opening, and order-flow

### Market Intraday Momentum
- **Authors:** Lei Gao, Yufeng Han, Sophia Zhengzi Li, Guofu Zhou
- **Year:** 2018
- **Source:** Journal of Financial Economics 129(2): 394-414
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S0304405X18301351
- **Abstract:** Documents a robust intraday-momentum pattern in S&P 500 ETF (SPY) from 1993-2013: the first half-hour return predicts the last half-hour return. Effect is strong, statistically significant, economically tradable.
- **Key findings:**
  - First-30min return predicts last-30min return with R² ~3-5%.
  - Effect strongest on volatile days, high-volume days, recession days, news days.
  - Strategy Sharpe ~1.0 in-sample (~0.7 out-of-sample post-publication).
  - Time-of-day asymmetry: closer to close, predictability strengthens.
  - Effect consistent with Baltussen-Da-Lindberg-Pearce (2021) gamma-hedging mechanism.
- **Relevance to GTOS:** Documents a baseline intraday-momentum effect that GTOS may be partially exploiting (via late-NY-kill-zone entries) but not consciously. Worth comparing GTOS expected-R to the intraday-momentum baseline as a benchmark.
- **Potential hypothesis:** GTOS late-NY trades on negative-MM-gamma days should beat first-30min-momentum-baseline (i.e., not redundant with it). Test on existing data.
- **Cross-domain links:** 14 (momentum); 12 (gamma channel)
- **Intraday window:** First-30min / last-30min

### Intraday Momentum: The First Half-Hour Return Predicts the Last Half-Hour Return
- **Authors:** Lei Gao, Yufeng Han, Sophia Zhengzi Li, Guofu Zhou
- **Year:** 2015 (initial SSRN)
- **Source:** SSRN 2552752 (working version of JFE 2018)
- **URL:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2552752
- **Abstract:** Working-paper version of the JFE 2018 paper. Same core finding; this is the most-cited / most-accessible early version.
- **Key findings:** Same as above; included for completeness with original-version reference.
- **Relevance to GTOS:** Same as above.
- **Potential hypothesis:** Same as above.
- **Cross-domain links:** 14, 12
- **Intraday window:** First-30min / last-30min

### Order Flow and Exchange Rate Dynamics
- **Authors:** Martin D.D. Evans, Richard K. Lyons
- **Year:** 2002
- **Source:** Journal of Political Economy 110(1): 170-180
- **URL:** https://faculty.georgetown.edu/evansm1/wpapers_files/orderflow.pdf
- **Abstract:** Seminal paper bridging FX market-microstructure and macro. Combines order-flow data with macro fundamentals to explain ~50%+ of daily exchange-rate variation in DEM/USD and JPY/USD.
- **Key findings:**
  - $1B net dollar purchases → +0.5% DEM-per-USD price move (large).
  - Order flow accounts for 40-80% of daily exchange-rate variation across major pairs.
  - Out-of-sample, the order-flow-augmented model beats random walk for short-horizon FX forecasting.
  - Two-component decomposition: portfolio shifts (private info) + macro innovations.
  - Foundational paper for "FX is microstructure-driven, not pure-macro."
- **Relevance to GTOS:** Although GTOS does not see consolidated FX order flow directly, the principle that order-flow imbalance is a major driver of FX is foundational. Tick-volume in `tick_features.py` is a (weak) proxy.
- **Potential hypothesis:** A daily aggregate signed-tick-volume feature for USDJPY/GBPUSD/EURUSD/GBPJPY should have measurable predictive power on next-day mid-price direction. Test on backfill.
- **Cross-domain links:** 11 (FX macro); 06 (microstructure foundation)
- **Intraday window:** Daily

### The Long Memory of Order Flow in the Foreign Exchange Spot Market
- **Authors:** Martin D. Gould, Mason A. Porter, Sam D. Howison
- **Year:** 2016
- **Source:** Market Microstructure and Liquidity 2(2): 1650001
- **URL:** https://people.maths.ox.ac.uk/porterm/papers/long-memory-published.pdf
- **Abstract:** Empirical study of order-flow autocorrelation in three major FX pairs on a large electronic platform. Documents Hurst H ≈ 0.7 — strong long-memory, persistent over days.
- **Key findings:**
  - H ≈ 0.7 for each of 3 major FX pairs (EUR/USD, USD/JPY, GBP/USD).
  - Long-memory is a robust property; persists across daily boundaries.
  - Two competing explanations: (a) traders herding on common info, (b) order-splitting metaorders over multiple days.
  - Long-memory survives intraday-pattern controls.
  - Implications for impact-cost modeling — single-day analysis underestimates persistence.
- **Relevance to GTOS:** Direct empirical confirmation that FX order flow has long-memory, meaning daily-aggregate features carry information beyond contemporaneous return. Useful for K54.
- **Potential hypothesis:** Add a 5-day exponentially-weighted average of signed tick-volume to K54; expect positive coefficient.
- **Cross-domain links:** 03 (Hurst / long-memory); 06 (microstructure); 11 (FX)
- **Intraday window:** Daily aggregated

### Measuring the Information Content of Stock Trades
- **Authors:** Joel Hasbrouck
- **Year:** 1991
- **Source:** Journal of Finance 46(1): 179-207
- **URL:** https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.1991.tb03749.x
- **Abstract:** Methodological-foundational paper. Uses VAR (vector autoregression) on trade and quote data to identify the information content of individual trades. Establishes that trades have both transient and permanent price impact.
- **Key findings:**
  - VAR framework cleanly separates trade-induced price changes into transient (recoverable) and permanent (info-revealing) components.
  - Permanent component is the "information content."
  - Trade size and trade direction interact non-trivially.
  - Order-flow imbalance is information; trades themselves are signals.
  - Modern microstructure literature is built on this VAR foundation.
- **Relevance to GTOS:** Methodological foundation for any signed-volume feature with separation of transient vs permanent impact. Currently `tick_features.py` does not implement this decomposition.
- **Potential hypothesis:** Implementing Hasbrouck-VAR-style decomposition on `tick_features.py` and using only the *permanent* component as feature should improve K54 SHAP-importance for trades.
- **Cross-domain links:** 06 (microstructure foundation); 03 (econometric VAR)
- **Intraday window:** General

### High-Frequency Trading and Price Discovery
- **Authors:** Jonathan Brogaard, Terrence Hendershott, Ryan Riordan
- **Year:** 2014
- **Source:** Review of Financial Studies 27(8): 2267-2306
- **URL:** https://academic.oup.com/rfs/article-abstract/27/8/2267/1582754
- **Abstract:** Empirical study of HFT trading patterns using NASDAQ proprietary data. HFTs facilitate price efficiency by trading in direction of permanent price changes; their liquidity-supplying orders are adversely selected.
- **Key findings:**
  - HFTs' liquidity-demanding orders correlate positively with permanent price changes.
  - HFTs' liquidity-supplying orders are *negatively* correlated with permanent changes (adverse selection).
  - HFT direction predicts price changes over horizons measured in seconds.
  - On highest-volatility days, HFTs continue to make markets but with wider spreads.
  - Net contribution: HFTs contribute to price discovery, especially on news days.
- **Relevance to GTOS:** Mostly background context. HFT presence is part of the modern microstructure environment GTOS operates in. Implies that any sub-second feature engineering must contend with HFT noise.
- **Potential hypothesis:** None directly; this is contextual paper for execution-layer thinking.
- **Cross-domain links:** 06 (HFT microstructure); 03 (price discovery)
- **Intraday window:** Sub-second / second

### The Volume Clock: Insights into the High Frequency Paradigm
- **Authors:** David Easley, Marcos López de Prado, Maureen O'Hara
- **Year:** 2012
- **Source:** Journal of Portfolio Management 39(1): 19-29
- **URL:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2034858
- **Abstract:** Argues that algorithmic / HFT decisions are best modeled in *volume time* rather than calendar time. Volume buckets synchronize with information arrival; empirical patterns become cleaner.
- **Key findings:**
  - Volume-time stationarizes return distributions (less seasonality, more Gaussian-like).
  - Volume-time aggregation reveals patterns missed in calendar-time data.
  - Information arrival in HFT era is volume-paced, not clock-paced.
  - Volume-clock framework underlies VPIN methodology (separate paper).
  - Practical implication: design features in volume-time when possible.
- **Relevance to GTOS:** Methodological paper. Currently GTOS samples in calendar-time (M15 candles); volume-time alternatives could sharpen tick-feature signals.
- **Potential hypothesis:** Comparing M15-calendar features vs volume-bucket features in K54 should show volume-time has cleaner distributions per Easley-LopezdePrado-O'Hara.
- **Cross-domain links:** 06 (HFT); 03 (stationarity / time-change)
- **Intraday window:** Sub-minute

### VPIN: The Microstructure of the 'Flash Crash'
- **Authors:** David Easley, Marcos López de Prado, Maureen O'Hara
- **Year:** 2011
- **Source:** SSRN 1695041; later in Journal of Portfolio Management
- **URL:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1695041
- **Abstract:** Proposes VPIN (Volume-synchronized Probability of Informed Trading) as a real-time toxicity metric. Claims it would have provided 1+ hour warning before the Flash Crash.
- **Key findings:**
  - VPIN is computed in volume-time using equal-volume buckets.
  - VPIN spikes precede 2010 Flash Crash by >1 hour.
  - VPIN > some threshold → toxic flow → liquidity providers withdraw.
  - VPIN is correlated with future intraday volatility.
  - Implementable in real-time on streaming trade data.
- **Relevance to GTOS:** Useful as a *toxicity* feature in `tick_features.py` — when VPIN spikes, GTOS L2 rejection rates should increase.
- **Potential hypothesis:** VPIN > 80th-percentile should predict elevated L2 sl_buffer 0.0 cluster rate in subsequent 30 minutes.
- **Cross-domain links:** 06 (microstructure toxicity); 03 (information arrival)
- **Intraday window:** General / volume-time

### VPIN and the Flash Crash (Critique)
- **Authors:** Torben G. Andersen, Oleg Bondarenko
- **Year:** 2014
- **Source:** Journal of Financial Markets 17: 1-46
- **URL:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1881731
- **Abstract:** Critical evaluation of VPIN. Documents that VPIN's predictive content for short-run volatility is weak; that VPIN actually peaked *after* not before the Flash Crash; and that the BVC volume-classification scheme has systematic errors.
- **Key findings:**
  - VPIN's flash-crash prediction is artifact of post-crash data inclusion in cumulative-distribution.
  - Standard tick-rule outperforms BVC for trade classification.
  - VPIN's volatility-prediction is mechanically driven by trading intensity, not toxicity.
  - Andersen-Bondarenko argue VPIN is "unsuitable for capturing order-flow toxicity."
  - Easley-López-O'Hara dispute these claims; debate continues.
- **Relevance to GTOS:** Important *contrarian* finding. Tempers the case for VPIN as a feature. Suggests using only careful tick-rule-classified imbalance, not BVC.
- **Potential hypothesis:** If GTOS adds VPIN to `tick_features.py`, evaluate against tick-rule-imbalance as baseline; expect tick-rule wins for forecasting.
- **Cross-domain links:** 06 (microstructure debate); 02 (statistical methodology critique)
- **Intraday window:** General

### The Flash Crash: High-Frequency Trading in an Electronic Market
- **Authors:** Andrei A. Kirilenko, Albert S. Kyle, Mehrdad Samadi, Tugkan Tuzun
- **Year:** 2017
- **Source:** Journal of Finance 72(3): 967-998
- **URL:** https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.12498
- **Abstract:** Definitive academic study of the May 6, 2010 Flash Crash using CFTC audit-trail data. Documents the role of HFTs as inventory managers (not market-makers in the classic sense) during the event.
- **Key findings:**
  - HFTs did not cause the Flash Crash but *amplified* it via inventory-management.
  - The triggering trade was a 75,000-contract E-mini sell program (Waddell & Reed).
  - HFTs initially absorbed selling; then aggressively sold to manage exposure.
  - Combined HFT-fundamental selling pressure caused the rapid decline.
  - "Hot-potato" trading among HFTs amplified volatility without adding liquidity.
- **Relevance to GTOS:** Background paper for understanding modern E-mini liquidity profile. NAS100 / US30 cash GTOS trading is at the periphery of this dynamic.
- **Potential hypothesis:** Single large flow event → 30+min of impaired liquidity → elevated GTOS rejection rate. Hard to test without identifying flow events.
- **Cross-domain links:** 06 (HFT microstructure); 03 (extreme events / fat tails)
- **Intraday window:** Sub-second / event-specific

---

## 7. Calendar-effect / month-end / OPEX-day flows

### Equity Returns at the Turn of the Month
- **Authors:** Wei Xu, John J. McConnell
- **Year:** 2008
- **Source:** Financial Analysts Journal 64(2): 49-64
- **URL:** https://business.purdue.edu/faculty/mcconnell/publications/Equity-Returns-at-the-Turn-of-the-Month.pdf
- **Abstract:** Comprehensive analysis of the turn-of-the-month (TOM) effect: stock returns are systematically higher during the 4-day window from last trading day of month to first 3 trading days of next month.
- **Key findings:**
  - 1926-2005: TOM-window contained essentially all of the equity-risk-premium.
  - 1987-2005: same finding holds.
  - Effect not concentrated in small-caps, low-price stocks, year-ends, or US-only — found in 31/35 countries.
  - Not explained by trading volume or net flows to equity funds.
  - Interpretation: pension-fund inflows from monthly cashflow + window-dressing dominant explanation.
- **Relevance to GTOS:** Long-only US-equity finding; partially relevant for US30 and NAS100. The TOM-window has a stale-but-real bullish bias that GTOS LONG-side exposure on those instruments may benefit from / SHORT-side may be impaired by.
- **Potential hypothesis:** Stratifying NAS100 / US30 LONG vs SHORT realized R by TOM-window inclusion; expect LONG-bias on TOM-window days.
- **Cross-domain links:** 13 (rebalancing flows); 17 (calendar anomaly behavior)
- **Intraday window:** Daily / month-end-specific

### Turn-of-the-Month Anomaly: Re-examination
- **Authors:** various; Lakonishok-Smidt
- **Year:** 2017+ (modern reassessment)
- **Source:** Quantpedia / academic re-examinations
- **URL:** https://quantpedia.com/strategies/turn-of-the-month-in-equity-indexes
- **Abstract:** Reviews TOM-effect in light of post-2015 data. Finds TOM-effect has substantially weakened, possibly arbitraged away.
- **Key findings:**
  - 2015-2025: TOM effect statistically borderline; not significant in some specifications.
  - ETF-era trading reduces calendar-time predictability.
  - Effect persists in EM and small-caps; weakens in S&P 500.
  - Bid-ask-spread filters eliminate ~30% of nominal effect.
  - Practitioner interpretation: TOM is now a tail-risk hedge rather than a predictable edge.
- **Relevance to GTOS:** Confirms TOM-effect is decayed. GTOS does not need to specifically design around it for liquid majors (XAUUSD/US30/NAS100), although it remains a (small) tailwind for LONG bias.
- **Potential hypothesis:** None operational; this is a "now-decay-confirmed" finding.
- **Cross-domain links:** 22 (anomaly decay); 17 (calendar anomalies)
- **Intraday window:** Daily

### Program Trading and Individual Stock Returns: Ingredients of the Triple-Witching Brew
- **Authors:** Hans R. Stoll, Robert E. Whaley
- **Year:** 1987
- **Source:** Working paper / financial Analysts Journal
- **URL:** https://www.researchgate.net/publication/24103078_Program_Trading_and_Individual_Stock_Returns_Ingredients_of_the_Triple-Witching_Brew
- **Abstract:** Original Stoll-Whaley paper on triple-witching effect. Documents abnormal price/volume behavior on the third Friday of March/June/September/December when index futures, index options, and stock options all expire.
- **Key findings:**
  - Triple-witching Fridays show abnormal volatility ~7% higher daily range vs non-triple-witching Fridays.
  - Average return: -0.72% lower than typical.
  - Mostly concentrated in last hour of trading.
  - Reverses partially at next Monday open.
  - Foundational paper for "expiration effects on cash markets."
- **Relevance to GTOS:** Background paper; modern OPEX literature has refined this. The triple-witching pattern is *the* test bed for any OPEX-related GTOS gate.
- **Potential hypothesis:** Specific triple-witching Friday gate to be tested first as proof-of-concept before generalizing to all monthly OPEX.
- **Cross-domain links:** 12 (option expiration); 09 (round-number)
- **Intraday window:** Last hour of triple-witching Friday

### Market Profile and Volume Profile (FTMO / Educational Synthesis)
- **Authors:** various practitioner-educational
- **Year:** 2020-2025
- **Source:** FTMO blog, ATAS, Topstep blogs (industry-educational)
- **URL:** https://ftmo.com/en/blog/market-profile-volume-profile-and-auction-market-theory/
- **Abstract:** Educational synthesis of how Market Profile concepts (TPO chart) and Volume Profile concepts (VPVR/VPSR) interact in modern futures-and-equity-index trading. Includes practical application to gold and equity-index futures.
- **Key findings (educational):**
  - Volume Profile charts are widely used by prop-firm traders (FTMO context).
  - Value Area and POC concepts apply to gold (XAUUSD) intraday.
  - Practical rule: "fade VAH on responsive day, target POC."
  - Gold-specific: London 4pm fix often near POC of London session.
  - 24h-instrument issue: "session" definition is non-trivial for FX/gold.
- **Relevance to GTOS:** Operational reference for prop-firm-trader-style market context. Confirms Profile-style concepts are practitioner-mainstream and worth considering as features.
- **Potential hypothesis:** Adding session-VAL/VAH/POC as continuous features for XAUUSD; expect modest predictive lift.
- **Cross-domain links:** 07 (ICT/SMC); 09 (level magnetism)
- **Intraday window:** Session

---

## 8. Practitioner / dealer-flow research notes

### SqueezeMetrics: "Short Is Long" — Dealer Hedging Whitepaper
- **Authors:** SqueezeMetrics (anonymous practitioner)
- **Year:** ~2020
- **Source:** SqueezeMetrics whitepaper (private platform)
- **URL:** Referenced in https://spotgamma.com/gamma-exposure-gex/ ; whitepaper hosted at squeezemetrics platform
- **Abstract:** Practitioner whitepaper credited with popularizing the GEX (Gamma Exposure) framework and dealer-hedging-flow narrative in retail trading.
- **Key findings (practitioner):**
  - Net positive dealer gamma → mean-reverting market behavior, low volatility.
  - Net negative dealer gamma → trending / momentum-amplifying behavior, high volatility.
  - "Gamma flip" levels = inflection points where dealer behavior shifts.
  - Empirical SPX correlation between GEX sign and realized vol-of-vol.
  - Practitioner-popular but academically informal — corroborated by Barbon-Buraschi (Gamma Fragility).
- **Relevance to GTOS:** Practitioner reference enabling free-tier GEX data acquisition. Provides the "GEX" concept that academic literature (Barbon-Buraschi, Baltussen-Da-Lindberg) formalizes.
- **Potential hypothesis:** Free SpotGamma / SqueezeMetrics public-feed GEX data → daily K54 feature → expected lift on NAS100/US30.
- **Cross-domain links:** 12 (gamma flow); 22 (practitioner alpha)
- **Intraday window:** Daily / aggregate

### SpotGamma: GEX, Gamma Flip, Call Wall, Put Wall
- **Authors:** SpotGamma (Brent Kochuba)
- **Year:** 2020-present (continuing platform)
- **Source:** SpotGamma platform / blog
- **URL:** https://spotgamma.com/gamma-exposure-gex/
- **Abstract:** SpotGamma calculates and publishes daily GEX, gamma-flip levels, and "call wall" / "put wall" levels for SPX, SPY, QQQ, IWM. Industry-standard practitioner dealer-positioning data source.
- **Key findings (practitioner):**
  - "Call wall" = strike with maximum positive gamma → tends to act as resistance.
  - "Put wall" = strike with maximum negative gamma → tends to act as support.
  - Gamma flip level = price at which net dealer gamma changes sign.
  - Hedging flow predicts intraday range and end-of-day pinning.
  - 0DTE-era refinements: per-expiration gamma, intraday GEX updates.
- **Relevance to GTOS:** Practitioner reference. NAS100 (NDX/QQQ) and US30 (similar to DIA) have publicly-accessible Call/Put walls. These could serve as resistance/support reference levels distinct from OB/FVG.
- **Potential hypothesis:** GTOS POI levels that coincide with daily Call Wall / Put Wall are higher-conviction setups; quantify in shadow.
- **Cross-domain links:** 12 (gamma flow); 09 (round-number/strike); 07 (ICT/SMC POI alignment)
- **Intraday window:** Daily / aggregate

---

## 9. Gaps and caveats

1. **No explicit "kill-zone-feature-engineering" academic literature.** GTOS's kill-zone framework is practitioner-derived; the closest academic foundations are Admati-Pfleiderer (1988), Lo-Wang (2000), and Andersen-Bollerslev (1997). The intraday-momentum literature (Gao-Han-Li-Zhou 2018, Baltussen-Da-Lindberg 2021) provides the most-direct academic backing for opens/closes mattering, but does not endorse our specific "13:00-17:00 NY for XAUUSD" structure.

2. **Limited Steidlmayer / Market-Profile peer-review.** Steidlmayer's auction-market-theory framework is practitioner-classic but never received formal peer-review. The Quantpedia / RainmakerTrade backtests are the closest to academic validation.

3. **Dealer-gamma data scarcity.** Per Buis et al. (2024), the empirical literature is sparse because proprietary option-position data is limited. SpotGamma / SqueezeMetrics estimates are public-data approximations subject to model error — the literature is partly a *practitioner-academic hybrid*.

4. **0DTE narrative tempering.** Recent rigorous papers (Cboe Vasquez et al. 2024; Dim-Eraker-Vilkov 2024) *contradict* the popular 0DTE-amplification narrative. GTOS should not over-react to 0DTE narrative without verifying.

5. **OPEX-effect on FX is under-studied.** Most OPEX literature is equity-index-options-on-stocks. FX OPEX effects (currency-options-on-spot) are not well-documented in academic literature; FX literature focuses on the *fix* mechanism instead of *option expirations*.

6. **TOM effect decayed post-2015.** Modern re-examinations of the turn-of-the-month effect find it is either gone or much weaker. Don't ship a TOM-based gate without modern-data confirmation.

7. **GBPJPY / USDJPY Tokyo fix specificity.** The 9:55 Tokyo fix is documented in Ito-Yamada (2017), but the FX-fix literature is dominated by London-4pm. GTOS's USDJPY/GBPJPY Tokyo kill-zone (00:00-03:00 UTC) sits very close to the 00:55 UTC Tokyo fix. This is an under-utilized cross-reference.

8. **Cross-instrument-correlation-gate failure modes.** Krohn-Mueller-Whelan (2024) and Melvin-Prins (2014) document that month-end / fix-window FX flows can break normal correlations. GTOS's cross-instrument correlation gate is not currently calendar-aware; this is a known but not-yet-addressed weakness.

---

## 10. Top 3 most-relevant-to-GTOS

1. **Krohn-Mueller-Whelan (2024)** — "Foreign Exchange Fixings and Returns Around the Clock." Direct evidence that GTOS's USDJPY / GBPJPY trading near 9:55 UTC / 16:00 UTC is structurally biased. Adding a "minutes-to-fix" feature is a concrete, testable change.

2. **Baltussen-Terstegge-Whelan (2024)** — "The Equity Derivative Payoff Bias." Clean evidence of OPEX-Friday open mispricing in SPX (and by extension NAS100). Gives a sharp, falsifiable hypothesis: skip first 30 minutes of NAS100 / US30 on third Fridays.

3. **Baltussen-Da-Lindberg-Pearce (2021)** — "Hedging Demand and Market Intraday Momentum." Connects intraday momentum to dealer-gamma sign with strong empirical R². Most directly actionable: GTOS K54 should ingest a daily MM-gamma-sign feature (publicly inferable from SpotGamma).

## 11. Top surprise

**Vasquez-Amaya-Pearson-Garcia-Ares (2024) and Dim-Eraker-Vilkov (2024) jointly reject the 0DTE-amplification narrative.** The popular media story that 0DTE flows are a structural fragility-source is *not* supported by careful academic empirics — net dealer-gamma exposure from 0DTEs is bounded and customer flow is much more two-sided than feared. This means GTOS should *not* aggressively de-risk on 0DTE-related concerns alone; the bigger quantitative effects come from monthly OPEX (Baltussen-Terstegge-Whelan; Ni-Pearson-Poteshman) and FX fixes (Krohn et al.; Ito-Yamada).

## 12. Hypotheses (for Phase 3 backlog)

1. **Fix-window avoidance gate (USDJPY/GBPJPY/GBPUSD/EURUSD).** Skip new entries within ±15 min of (Tokyo 00:55, London 16:00, NY 17:00 UTC) fixes. Backed by Krohn-Mueller-Whelan + Ito-Yamada + Marsh et al. Test as additive shadow gate; expected reduction in slippage variance and L2 sl_buffer 0.0 cluster.

2. **OPEX-Friday morning gate (NAS100/US30).** Skip first 30 minutes of NAS100/US30 on third-Friday-of-month. Backed by Baltussen-Terstegge-Whelan + Avellaneda-Lipkin pinning theory + Ni-Pearson-Poteshman. Test as additive shadow gate; expected reduction in HALLUC-1-class issues.

3. **Dealer-gamma-sign K54 feature.** Add daily aggregate GEX-sign feature (using public SpotGamma data) to K54 regime classifier. Expect interaction with kill-zone realized R: positive-gamma days favor mean-reversion, negative-gamma days favor trend-following. Backed by Barbon-Buraschi + Baltussen-Da-Lindberg-Pearce.

---

*Last updated: 2026-04-28 by Phase 1 Worker Agent #8.*
