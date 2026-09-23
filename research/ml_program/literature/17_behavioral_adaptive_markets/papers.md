# Domain 17 — Behavioral Finance & Adaptive Markets — Paper Catalog

**Owner:** Phase 1 Worker Agent #17
**Compilation date:** 2026-04-28
**Paper count:** 42

This catalog covers behavioral models of price formation at the **market level** (limits to arbitrage, noise traders, sentiment indices, adaptive markets, Tetlock-style media sentiment, herding, social-media retail-flow regime, LLM-as-sentiment-source). Individual-trader cognitive biases sit in domain 18; LLM-extracted sentiment infrastructure cross-links to domains 19-20.

GTOS context: edge mechanism is stop-cascade mean reversion at OB retest — directly anchored in noise-trader / limits-of-arbitrage theory. Edge-decay (CEO's #1 concern, item #4 in CLAUDE.md) is exactly what Lo's Adaptive Markets Hypothesis predicts. K54 v2 features candidates listed in spec section 5 explicitly include sentiment indices, FEARS, news flow.

---

## Section 1 — Foundational behavioral asset pricing (BSV / Hong-Stein / DHS / Daniel-Hirshleifer-Subrahmanyam)

### A Model of Investor Sentiment
- **Authors:** Nicholas Barberis, Andrei Shleifer, Robert Vishny
- **Year:** 1998
- **Source:** Journal of Financial Economics, vol. 49(3), pages 307-343
- **URL:** https://nicholasbarberis.github.io/bsv_jnl.pdf
- **Mechanism:** underreaction / overreaction
- **Abstract:** Empirical findings show both underreaction and overreaction of stock prices to news. The authors present a parsimonious model of investor sentiment based on psychological evidence (representativeness heuristic + conservatism bias) that produces both phenomena across a wide range of parameter values.
- **Key findings:**
  1. Conservatism bias generates underreaction to news (drift continues in news direction).
  2. Representativeness heuristic generates overreaction at longer horizons (reversal).
  3. Single-regime-switching model parsimoniously captures both.
  4. Predicts post-earnings-announcement drift + long-run reversal in same framework.
- **Relevance to GTOS (esp. edge decay + sentiment FE):** GTOS's OB retest captures the *moment* underreaction-to-CHoCH transitions to overreaction-back-to-zone — BSV is the textbook anchor for why retests have edge. Sentiment regime variable in K54 v2 should map to BSV-style switching.
- **Potential hypothesis:** OB-retest edge magnitude is a function of *which BSV regime* the market is in; trending_bull cohort collapse (F2/F15) may correspond to regime-shift away from representativeness-driven overreaction.
- **Cross-domain:** 14 (momentum), 18 (cognitive biases at individual level)

### A Unified Theory of Underreaction, Momentum Trading, and Overreaction in Asset Markets
- **Authors:** Harrison Hong, Jeremy Stein
- **Year:** 1999
- **Source:** Journal of Finance, vol. 54(6), pages 2143-2184
- **URL:** http://www.columbia.edu/~hh2679/jf-mom.pdf
- **Mechanism:** underreaction / overreaction
- **Abstract:** Two boundedly rational agent classes — newswatchers and momentum traders. Newswatchers underreact because information diffuses gradually; momentum traders chase trends but use simple univariate rules, leading to overreaction at long horizons.
- **Key findings:**
  1. Gradual information diffusion → short-horizon underreaction → momentum profits.
  2. Momentum trader entry → overshoot → long-horizon reversal.
  3. Predicts that smaller / less-analyst-followed stocks have stronger momentum (slower diffusion).
  4. Provides micro-foundation for both Jegadeesh-Titman momentum and DeBondt-Thaler reversal.
- **Relevance to GTOS:** GTOS H1→M15 OB retest uses partial information (institutional zone + impulse) before broad market sees it. Edge decay = newswatcher population shrinking (as Lo predicts). The H1 OB advantage decay (+16.8pp → +4.6pp per F11) is exactly what Hong-Stein gradual-diffusion-erosion predicts.
- **Potential hypothesis:** As more retail platforms surface OB/SMC concepts (TradingView screeners, FX education), the "newswatcher" pool that allows OB precedence expands → overreaction-driven reversal at retest fails more often.
- **Cross-domain:** 14 (momentum), 02 (gradual-diffusion stat tests)

### Investor Psychology and Security Market Under- and Overreactions
- **Authors:** Kent Daniel, David Hirshleifer, Avanidhar Subrahmanyam
- **Year:** 1998
- **Source:** Journal of Finance, vol. 53(6), pages 1839-1885
- **URL:** https://www.ivey.uwo.ca/media/3775509/investor_psychology_and_security_market_under-and_overreactions.pdf
- **Mechanism:** overreaction / sentiment
- **Abstract:** Builds price-formation theory on two psychological biases: (i) overconfidence about precision of private information, and (ii) biased self-attribution (asymmetric confidence shifts based on outcomes).
- **Key findings:**
  1. Overconfidence → negative long-lag autocorrelations + excess volatility.
  2. Biased self-attribution → positive short-lag autocorrelations (momentum).
  3. Same model produces short-run drift + long-run reversal.
  4. Predicts public-event-based predictability when managerial actions correlate with mispricing.
- **Relevance to GTOS:** A6 LONG-side selectivity collapse (project_a6) mirrors Daniel-Hirshleifer-Subrahmanyam biased self-attribution: prior LONG winners → AI/system over-confident on next LONG → calibration drifts (F8 confirms decision-rationale rather than perception is decayed axis).
- **Potential hypothesis:** AI primary analyzer exhibits a Daniel-Hirshleifer-Subrahmanyam-like overconfidence cycle on LONG-side after prior winners; side-aware sizing (per project_side_aware_sizing_findings) is the mitigation.
- **Cross-domain:** 18 (overconfidence at individual level)

### Investor Psychology and Asset Pricing (survey)
- **Authors:** David Hirshleifer
- **Year:** 2001
- **Source:** Journal of Finance, vol. 56(4), pages 1533-1597
- **URL:** https://onlinelibrary.wiley.com/doi/abs/10.1111/0022-1082.00379
- **Mechanism:** sentiment / overreaction
- **Abstract:** Survey written for AFA 2001. Argues purely-rational asset pricing is being subsumed by behavioral approach where expected returns reflect *both* risk and misvaluation. Reviews biases, evidence, and models.
- **Key findings:**
  1. Frame for distinguishing rational-risk premia from misvaluation premia.
  2. Reviews herding / cascades / overconfidence / representativeness models.
  3. Connects time-varying-risk-premium models to behavioral predictions.
- **Relevance to GTOS:** Authoritative survey for K54 v2 feature engineering; provides taxonomy of behavioral premia that may be extractable via prompts/sentiment indices.
- **Potential hypothesis:** Per-regime LightGBM (K54) should encode at minimum: representativeness (recent-trend strength), conservatism (information-lag features), and overconfidence (volume-vs-volatility imbalance).
- **Cross-domain:** 14, 16, 18

### Psychology-Based Models of Asset Prices and Trading Volume
- **Authors:** Nicholas Barberis
- **Year:** 2018
- **Source:** Handbook of Behavioral Economics, Vol. 1, pages 79-175 (Elsevier)
- **URL:** https://nicholasbarberis.github.io/bdl17b.pdf
- **Mechanism:** sentiment / extrapolation / overreaction
- **Abstract:** Reviews three canonical psychology-based asset pricing model classes: extrapolation models, overconfidence models, gain-loss utility models inspired by prospect theory.
- **Key findings:**
  1. Each class captures a different empirical pattern (extrapolation → bubbles, overconfidence → trading volume, prospect theory → premia).
  2. Path-toward unified psychology-based model laid out.
  3. Extrapolation models match Greenwood-Shleifer survey-expectation evidence directly.
- **Relevance to GTOS:** Most current authoritative behavioral asset-pricing review. K54 should sample features from all three classes — not just extrapolation (existing momentum) or sentiment (single-feature). Connects directly to S79 sharpe_weighted Phase 2 risk policy via gain-loss utility.
- **Potential hypothesis:** Per-instrument feature weights in K54 should differ by which behavioral channel dominates that asset (e.g., gold = gain-loss utility because of safe-haven framing; NAS100 = extrapolation because growth-narrative).
- **Cross-domain:** 14, 18, 16

### Prospect Theory: An Analysis of Decision under Risk
- **Authors:** Daniel Kahneman, Amos Tversky
- **Year:** 1979
- **Source:** Econometrica, vol. 47(2), pages 263-292
- **URL:** https://web.mit.edu/curhan/www/docs/Articles/15341_Readings/Behavioral_Decision_Theory/Kahneman_Tversky_1979_Prospect_theory.pdf
- **Mechanism:** prospect-theory / loss aversion
- **Abstract:** Critique of expected utility theory as a descriptive model of decision under risk. Presents prospect theory: value function concave for gains, convex (and steeper) for losses; probabilities replaced by decision weights.
- **Key findings:**
  1. Certainty effect → risk aversion in gains, risk seeking in losses.
  2. Loss aversion (λ ≈ 2.25) → asymmetric reaction to gains vs. losses.
  3. Reflection effect → preference reversal across gain/loss frames.
- **Relevance to GTOS:** Direct anchor for sl_buffer / partial-close design (J46-J49 portfolio). The "immediate-on-TP1 BE" finding aligns with loss-aversion: removing tail risk dominates expected-value optimization. Touch-count gate (A19 LOOSEN_TO_3 rejection) is consistent with prospect-theory: agents avoid framing context where second touch creates clear "double-loss" reference point.
- **Potential hypothesis:** Per-instrument optimal sizing reflects population's loss-aversion asymmetry on that asset (gold > stocks in crisis; FX low). S79 + side-aware bundle is an empirical realization.
- **Cross-domain:** 18, all behavioral domains

### Prospect Theory and Asset Prices
- **Authors:** Nicholas Barberis, Ming Huang, Tano Santos
- **Year:** 2001
- **Source:** Quarterly Journal of Economics, vol. 116(1), pages 1-53
- **URL:** https://business.columbia.edu/sites/default/files-efs/pubfiles/555/prospect.pdf
- **Mechanism:** prospect-theory / loss aversion
- **Abstract:** Formal model where investors derive utility from wealth fluctuations; loss aversion + path-dependent risk aversion (house-money effect: prior gains buffer subsequent losses).
- **Key findings:**
  1. Equity premium can be high because of loss aversion (no risk premium puzzle).
  2. Excess volatility from path-dependent risk aversion.
  3. Predictability of returns on price-dividend ratio + low return-consumption correlation.
- **Relevance to GTOS:** Provides theory for why per-asset risk premia / expectancy differ across regimes. House-money effect → after winning streak, GTOS may be biased to over-size (mitigation: H29 8% DD reduction).
- **Potential hypothesis:** S79 sharpe_weighted should vary by recent realized R streak (house-money regime) — Phase 2 follow-up.
- **Cross-domain:** 18, 13

---

## Section 2 — Limits of Arbitrage

### The Limits of Arbitrage
- **Authors:** Andrei Shleifer, Robert Vishny
- **Year:** 1997
- **Source:** Journal of Finance, vol. 52(1), pages 35-55
- **URL:** https://www.nber.org/system/files/working_papers/w5167/w5167.pdf
- **Mechanism:** limits-of-arbitrage
- **Abstract:** Real-world arbitrage requires capital and risk-bearing; specialized arbitrageurs use other people's money. Performance-based arbitrage is *least effective* in extreme circumstances when capital is most needed.
- **Key findings:**
  1. Arbitrageurs may bail at the worst time (capital withdrawals correlate with mispricing extremes).
  2. Mispricings can deepen rather than self-correct in extreme regimes.
  3. Provides micro-foundation for sustained inefficiency.
- **Relevance to GTOS:** Direct theoretical anchor for edge mechanism. Stop-cascade events at OB are precisely the moments arbitrage capital is most withdrawn (forced unwinding of leveraged positions). GTOS is operating *as* the limits-of-arbitrage refilling agent on a small scale.
- **Potential hypothesis:** OB continuation rate is highest when funding/risk regime is stressed (vol expansion regimes); edge weakens in calm-regime periods → connects to F11 + F15 regime-conditioned decay.
- **Cross-domain:** 22 (hedge fund), 16 (vol regime)

### Noise Trader Risk in Financial Markets
- **Authors:** J. Bradford De Long, Andrei Shleifer, Lawrence Summers, Robert Waldmann
- **Year:** 1990
- **Source:** Journal of Political Economy, vol. 98(4), pages 703-738
- **URL:** https://ms.mcmaster.ca/~grasselli/DeLongShleiferSummersWaldmann90.pdf
- **Mechanism:** noise-trader / limits-of-arbitrage
- **Abstract:** OLG model where noise traders with stochastic erroneous beliefs both affect prices and earn higher expected returns. Unpredictability of noise-trader beliefs creates risk that deters arbitrageurs.
- **Key findings:**
  1. Noise-trader risk is a separate, priced risk factor.
  2. Explains excess volatility, mean reversion, closed-end fund discounts, equity premium puzzle.
  3. Noise traders survive (and earn premia) because rational agents cannot bet aggressively against them.
- **Relevance to GTOS:** Stop-cascade events ARE noise-trader risk realized — concentrated forced selling at zone breaks. GTOS edge captures the predictable component of noise-trader unwinding. Edge-decay thesis = noise-trader risk premium being eroded as more retail systematized.
- **Potential hypothesis:** Edge magnitude correlates with retail-vs-institutional flow balance per instrument; instruments with rising algorithmic-retail share (NAS100) decay faster than slower-moving (gold).
- **Cross-domain:** 06, 11, 22

### Limits of Arbitrage: The State of the Theory
- **Authors:** Denis Gromb, Dimitri Vayanos
- **Year:** 2010
- **Source:** Annual Review of Financial Economics, vol. 2, pages 251-275
- **URL:** https://personal.lse.ac.uk/vayanos/Papers/LOAST_ARFE10.pdf
- **Mechanism:** limits-of-arbitrage
- **Abstract:** Survey of theoretical developments. Costs faced by arbitrageurs: (a) fundamental + nonfundamental risk, (b) short-selling costs, (c) leverage / margin constraints, (d) equity-capital constraints.
- **Key findings:**
  1. Capital-constrained arbitrageurs cannot fully eliminate mispricing.
  2. Frictions amplify when correlated across arbitrageurs (firesale dynamics).
  3. Welfare and policy implications.
- **Relevance to GTOS:** Structural reading list for why GTOS edge persists; informs which regimes (high-vol, leverage stress) likely show *larger* edge.
- **Potential hypothesis:** OB continuation > 70% conditional on broker-margin-stress proxy (SOFR-OIS, equity-vol breakouts).
- **Cross-domain:** 22, 16

### Hedge Funds and the Technology Bubble
- **Authors:** Markus Brunnermeier, Stefan Nagel
- **Year:** 2004
- **Source:** Journal of Finance, vol. 59(5), pages 2013-2040
- **URL:** https://www.princeton.edu/~markus/research/papers/hedgefunds_bubble.pdf
- **Mechanism:** limits-of-arbitrage / herding
- **Abstract:** Hedge funds did NOT correct tech-bubble prices — they rode the bubble, reducing exposure stock-by-stock just before crashes.
- **Key findings:**
  1. Hedge fund tech holdings outperformed characteristics-matched benchmarks.
  2. Suggests informed investors rationally ride bubbles instead of arbitraging.
  3. Refutes simple short-sales-constraint explanations alone.
- **Relevance to GTOS:** "Smart money" can amplify rather than dampen mispricings. NAS100 retail-flow regime (post-2020) may follow same pattern; HALLUC-1 NAS100 93% precision bug emerging in same retail-tech-narrative environment is non-coincidence.
- **Potential hypothesis:** Edge in indices (NAS100 / US30) may be *anti-correlated* with bubble-regime indicator (high P/E + retail-flow surge).
- **Cross-domain:** 12, 22

### Liquidity and Risk Management
- **Authors:** Nicolae Garleanu, Lasse Heje Pedersen
- **Year:** 2007
- **Source:** American Economic Review, vol. 97(2), pages 193-197
- **URL:** https://nbgarleanu.github.io/LiquidityRiskManagementWP.pdf
- **Mechanism:** limits-of-arbitrage / funding
- **Abstract:** Tighter risk management → smaller maximum positions → less liquidity → more volatility → tighter risk management. Self-reinforcing destabilization spiral.
- **Key findings:**
  1. Risk-management feedback loop amplifies vol shocks.
  2. Sudden liquidity drops emerge endogenously without information shocks.
  3. Connects funding-side constraints to asset-pricing.
- **Relevance to GTOS:** Per-instrument-spread microstructure spikes (covered in domain 06) interact with this mechanism. Stop cascades = forced de-risking.
- **Potential hypothesis:** OB continuation rate spikes immediately *after* a vol-induced de-risking event (post-shock mean-reversion premium).
- **Cross-domain:** 06, 16, 22

---

## Section 3 — Adaptive Markets Hypothesis (Lo + Lim & Brooks + AMH applications)

### The Adaptive Markets Hypothesis: Market Efficiency from an Evolutionary Perspective
- **Authors:** Andrew W. Lo
- **Year:** 2004
- **Source:** Journal of Portfolio Management, vol. 30(5), pages 15-29
- **URL:** https://web.mit.edu/Alo/www/Papers/JPM2004_Pub.pdf
- **Mechanism:** adaptive
- **Abstract:** Reconciles efficient markets with behavioral alternatives via evolutionary principles (competition, adaptation, natural selection). Behavioral biases are evolved heuristics for adapting to changing environments.
- **Key findings:**
  1. Market efficiency is *not* binary — varies with market ecology (number of competitors, profit opportunities, adaptability).
  2. Behavioral "violations" of rationality are evolutionarily rational under shifted-environment.
  3. Predicts that any quantifiable edge will decay as competitors discover and arbitrage it.
  4. Risk premia are time-varying as investor populations + preferences change.
- **Relevance to GTOS (CRITICAL — direct edge-decay anchor):** This is the central theoretical anchor for CEO's #1 concern. F11 OB-zone-decay-velocity (+16.8pp → +4.6pp) IS Lo's predicted ecology shift. GTOS must continuously adapt or be selected out. Per-regime LightGBM (K54) and regime-aware sizing are operationalizations of AMH.
- **Potential hypothesis:** Edge half-life is inversely proportional to retail/institutional capital following the strategy publicly. NAS100 + GBPJPY (high retail FX education attention) decay faster than gold (lower retail attention but higher institutional flow).
- **Cross-domain:** 14, 02 (decay measurement)

### Reconciling Efficient Markets with Behavioral Finance: The Adaptive Markets Hypothesis
- **Authors:** Andrew W. Lo
- **Year:** 2005
- **Source:** Journal of Investment Consulting, vol. 7(2), pages 21-44
- **URL:** http://web.mit.edu/Alo/www/Papers/JIC2005.html
- **Mechanism:** adaptive
- **Abstract:** Extended treatment of AMH for practitioners. Loss aversion, overconfidence, overreaction, mental accounting all consistent with evolutionary heuristic-adaptation under changing environment.
- **Key findings:**
  1. Provides concrete investment-management implications: dynamic asset allocation > static.
  2. Risk-reward relations not stable — driven by population sizes / preferences.
  3. Investor-population shifts in ecology → factor-strategy decay.
- **Relevance to GTOS:** Directly connects to CEO's edge-decay concern. Operational guidance for adaptive position sizing.
- **Potential hypothesis:** S79 sharpe_weighted sizing should be re-calibrated quarterly using recent realized expectancy (rolling-90d), not anchored to historical SR.
- **Cross-domain:** 14

### The Adaptive Markets Hypothesis: An Evolutionary Approach to Understanding Financial System Dynamics
- **Authors:** Andrew W. Lo, Ruixun Zhang
- **Year:** 2024 (Clarendon Lectures, OUP)
- **Source:** Oxford University Press, Clarendon Lectures in Finance
- **URL:** https://global.oup.com/academic/product/the-adaptive-markets-hypothesis-9780199681143
- **Mechanism:** adaptive
- **Abstract:** Mathematical foundations of AMH. Evolutionary models showing how fundamental economic behaviors (risk preferences, loss aversion) emerge solely through natural selection.
- **Key findings:**
  1. Loss aversion is evolutionarily optimal in non-stationary environments.
  2. Risk-preferences are state-dependent; "rational" preferences emerge from adaptation, not axiom.
  3. Risk-reward relations evolve with population composition.
- **Relevance to GTOS:** Latest formal AMH reference. Loss-aversion + adaptation → S79 + side-aware sizing have evolutionary justification.
- **Potential hypothesis:** As AI participation rises, the adaptive equilibrium tilts toward populations that exploit AI's predictable biases — meta-edge available for human supervision.
- **Cross-domain:** 18, 14

### Adaptive Markets Hypothesis: Insights into Small Stock Market Efficiency (Finland)
- **Authors:** Various (Aalto / Tandfonline 2024)
- **Year:** 2024
- **Source:** Applied Economics, doi:10.1080/00036846.2024.2326039
- **URL:** https://www.tandfonline.com/doi/full/10.1080/00036846.2024.2326039
- **Mechanism:** adaptive
- **Abstract:** Tests AMH vs EMH on Finnish stock market. Examines whether small-market size impacts efficiency, role of liberalization, time-varying vol-return relation.
- **Key findings:**
  1. Strongly supports AMH over EMH; market goes through six efficiency phases.
  2. Market size alone does not impair efficiency.
  3. Foreign-investor opening improves efficiency *with delay*.
  4. Vol-return correlation varies in sign over time.
- **Relevance to GTOS:** Empirical AMH support on a smaller, less-liquid market — analogue to GBPJPY / XAGUSD positioning. Foreign-investor-opening lag → relevant for redacted_account / FTMO retail-prop populations entering markets.
- **Potential hypothesis:** GTOS edge in "lower-attention" pairs (XAGUSD, GBPJPY) more durable than in mega-cap retail-attention (NAS100).
- **Cross-domain:** 11

### Cryptocurrencies, Gold, and WTI Crude Oil Market Efficiency: A Dynamic Analysis Based on the Adaptive Market Hypothesis
- **Authors:** Various (Springer Financial Innovation 2021)
- **Year:** 2021
- **Source:** Financial Innovation
- **URL:** https://link.springer.com/article/10.1186/s40854-021-00246-0
- **Mechanism:** adaptive
- **Abstract:** Time-varying market efficiency in BTC, gold, oil under AMH. Returns predictability shifts across economic + political regimes.
- **Key findings:**
  1. All three commodities show time-varying efficiency.
  2. Gold + silver trend toward efficiency over time (mean-reversion in efficiency itself).
  3. Crypto remains less efficient than gold / oil through 2021.
- **Relevance to GTOS:** Confirms gold-market AMH applies — directly relevant to edge-decay framing on XAUUSD. Provides empirical method (rolling Hurst, automatic variance ratio) re-usable for monthly-decay-monitor (S1).
- **Potential hypothesis:** XAUUSD edge will continue decaying toward zero on multi-year horizon; intra-year reversal episodes (e.g. F15 regime shifts) provide windows of inefficiency.
- **Cross-domain:** 10 (gold)

### Predictability of Precious Metals and Adaptive Market Hypothesis
- **Authors:** Various
- **Year:** 2020
- **Source:** International Journal of Emerging Markets, doi:10.1108/ijoem-07-2018-0404
- **URL:** https://www.emerald.com/insight/content/doi/10.1108/ijoem-07-2018-0404/full/html
- **Mechanism:** adaptive
- **Abstract:** Tests AMH on gold + silver + platinum. Predictability changes over time across economic / political conditions.
- **Key findings:**
  1. Precious metals are adaptive markets — efficiency is not constant.
  2. Predictability cycles align with macro-event regimes.
  3. Refutes constant-efficiency assumption for gold.
- **Relevance to GTOS (gold-specific):** Most direct AMH evidence for XAUUSD. Provides time-series of predictability one can backtest GTOS expectancy against.
- **Potential hypothesis:** GTOS XAUUSD expectancy should correlate with periods identified as "predictable regime" in Auer / Caraiani-style precious-metal studies.
- **Cross-domain:** 10

### COVID-19 and Adaptive Behavior of Returns: Evidence from Commodity Markets
- **Authors:** Various (Nature Humanities and Social Sciences Communications 2022)
- **Year:** 2022
- **Source:** Nature HSSC, https://www.nature.com/articles/s41599-022-01332-z
- **URL:** https://www.nature.com/articles/s41599-022-01332-z
- **Mechanism:** adaptive
- **Abstract:** Linear + non-linear AMH tests on commodities through COVID-19 disruption.
- **Key findings:**
  1. AMH best explains COVID-19 commodity-market behavior.
  2. Strong adaptive-behavior signal under structural-break stress.
  3. Outperforms EMH in pandemic regime.
- **Relevance to GTOS:** Validates AMH framing for commodities under regime breaks. Suggests GTOS should expect *changes* in OB-continuation rate during macro regime shifts (geopolitical, central-bank-pivot).
- **Potential hypothesis:** OB continuation rate increases during initial-shock phase of regime breaks (when limits-of-arbitrage bind tightest).
- **Cross-domain:** 10, 16

---

## Section 4 — Sentiment indices, media, FEARS

### Investor Sentiment and the Cross-Section of Stock Returns
- **Authors:** Malcolm Baker, Jeffrey Wurgler
- **Year:** 2006
- **Source:** Journal of Finance, vol. 61(4), pages 1645-1680
- **URL:** https://onlinelibrary.wiley.com/doi/10.1111/j.1540-6261.2006.00885.x
- **Mechanism:** sentiment
- **Abstract:** Constructs composite sentiment index from six proxies (closed-end fund discount, NYSE turnover, IPO volume, IPO first-day returns, dividend premium, equity share). Tests cross-sectional asset-pricing implications.
- **Key findings:**
  1. Low-sentiment periods → small / young / volatile / unprofitable / non-dividend / extreme-growth stocks earn high subsequent returns.
  2. High sentiment → these categories earn low subsequent returns.
  3. Sentiment effects strongest where valuation is subjective + arbitrage costs high.
- **Relevance to GTOS (K54 v2 features):** Baker-Wurgler index is the canonical sentiment factor — directly listable in K54 feature set. Sentiment level may help disentangle when AI's LONG-side calibration drift occurs (high-sentiment regime → trending-bull cohort → F2 LONG decay).
- **Potential hypothesis:** Live LONG-WR-watch SPRT halts more frequently during high-sentiment periods (Baker-Wurgler index in top quintile).
- **Cross-domain:** 12, 13

### Giving Content to Investor Sentiment: The Role of Media in the Stock Market
- **Authors:** Paul Tetlock
- **Year:** 2007
- **Source:** Journal of Finance, vol. 62(3), pages 1139-1168
- **URL:** https://business.columbia.edu/sites/default/files-efs/pubfiles/3097/Tetlock_Media_Sentiment_JF.pdf
- **Mechanism:** sentiment
- **Abstract:** Quantifies media pessimism via WSJ "Abreast of the Market" column. Tests effects on prices + volume.
- **Key findings:**
  1. High pessimism → short-term price decline + reversion to fundamentals.
  2. Extreme pessimism (high or low) → high trading volume.
  3. Consistent with noise-trader liquidity models; rejects "media as proxy for fundamentals."
- **Relevance to GTOS:** Foundational paper for K54 v2 sentiment-feature engineering. Reversion-to-fundamentals after pessimism shock = OB-retest mean-reversion mechanism in macro form.
- **Potential hypothesis:** GTOS XAUUSD entries timed within 1-3 sessions after WSJ-pessimism extreme show higher expectancy.
- **Cross-domain:** 19, 20

### More Than Words: Quantifying Language to Measure Firms' Fundamentals
- **Authors:** Paul Tetlock, Maytal Saar-Tsechansky, Sofus Macskassy
- **Year:** 2008
- **Source:** Journal of Finance, vol. 63(3), pages 1437-1467
- **URL:** https://business.columbia.edu/sites/default/files-efs/pubfiles/3096/More_Than_Words_tetlock.pdf
- **Mechanism:** sentiment / underreaction
- **Abstract:** Firm-level news textual analysis. Negative-word fraction predicts low earnings; brief stock underreaction; predictability strongest when stories focus on fundamentals.
- **Key findings:**
  1. Negative words forecast low future earnings.
  2. Stock prices underreact briefly — drift continues.
  3. Effect concentrated in fundamental-focus stories vs. attention/peripheral news.
- **Relevance to GTOS:** Shows news-sentiment is real, sub-day predictive feature. Cross-link to K54 v2 (LLM-extracted firm/instrument-news features) and to spec section "LLM-as-sentiment."
- **Potential hypothesis:** Pre-news-event candidates with sentiment-aligned bias have higher expectancy than against-bias trades.
- **Cross-domain:** 19, 20

### The Sum of All FEARS: Investor Sentiment and Asset Prices
- **Authors:** Zhi Da, Joseph Engelberg, Pengjie Gao
- **Year:** 2015
- **Source:** Review of Financial Studies, vol. 28(1), pages 1-32
- **URL:** https://rady.ucsd.edu/faculty/directory/engelberg/pub/portfolios/FEARS.pdf
- **Mechanism:** sentiment
- **Abstract:** Constructs FEARS index from Google search volume on household-financial-anxiety terms ("recession," "unemployment," "bankruptcy"). Tests asset-price predictability 2004-2011.
- **Key findings:**
  1. FEARS predicts short-term return reversals.
  2. FEARS predicts temporary vol increases.
  3. FEARS predicts mutual-fund flows (out of equity, into bonds).
- **Relevance to GTOS (CRITICAL for K54 v2 sentiment features):** Search-volume indices are the highest-frequency, lowest-cost sentiment proxy — directly composable into K54 v2 feature set. Cross-instrument: gold queries spike at same FEARS extremes.
- **Potential hypothesis:** Gold (XAUUSD / XAGUSD) LONG expectancy positively correlated with concurrent FEARS index spikes; FX cross expectancy negatively correlated.
- **Cross-domain:** 19, 10, 11

### Sentiment During Recessions
- **Authors:** Diego Garcia
- **Year:** 2013
- **Source:** Journal of Finance, vol. 68(3), pages 1267-1300
- **URL:** https://leeds-faculty.colorado.edu/garcia/media_v33.pdf
- **Mechanism:** sentiment / overreaction
- **Abstract:** NYT financial-news sentiment 1905-2005. News content predictability is *concentrated in recessions*.
- **Key findings:**
  1. 1-σ pessimism shock in recession → 12 bps DJIA next day; in expansion → only 3.5 bps.
  2. Stronger on Mondays + post-holiday (more reading time).
  3. Effect persists into trading day.
- **Relevance to GTOS:** State-conditioned sentiment effect — direct match to F15's "regime is load-bearing" framing. Sentiment features should be regime-conditioned.
- **Potential hypothesis:** K54 v2 should include sentiment × regime interaction features (sentiment effect 3-4× stronger in stressed/recession regimes).
- **Cross-domain:** 19, F15 link

### When Is a Liability Not a Liability? Textual Analysis, Dictionaries, and 10-Ks
- **Authors:** Tim Loughran, Bill McDonald
- **Year:** 2011
- **Source:** Journal of Finance, vol. 66(1), pages 35-65
- **URL:** https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.2010.01625.x
- **Mechanism:** sentiment
- **Abstract:** Standard sentiment dictionaries (Harvard) misclassify ~75% of "negative" words in financial context. Builds finance-domain dictionary.
- **Key findings:**
  1. General-purpose sentiment dictionaries fail in finance text.
  2. Finance-specific Loughran-McDonald dictionary correlates with 10-K returns, volume, fraud, weakness, earnings.
  3. Now standard for finance NLP.
- **Relevance to GTOS:** Lesson for K54 v2 LLM-extracted sentiment: domain-specific framing critical. ChatGPT/LLM may inherit this misclassification problem unless prompted with finance context.
- **Potential hypothesis:** Domain-aligned LLM prompts (finance lexicon priming) outperform raw zero-shot sentiment by ≥10 percentage points in classification accuracy.
- **Cross-domain:** 19, 20

### Twitter Mood Predicts the Stock Market
- **Authors:** Johan Bollen, Huina Mao, Xiaojun Zeng
- **Year:** 2011
- **Source:** Journal of Computational Science, vol. 2(1), pages 1-8
- **URL:** https://arxiv.org/abs/1010.3003
- **Mechanism:** sentiment
- **Abstract:** Twitter mood (OpinionFinder + GPOMS 6-dimension) Granger-causes DJIA. Reports 87.6% directional accuracy.
- **Key findings:**
  1. Public mood (esp. "Calm") leads market by ~3 days.
  2. Self-organizing fuzzy NN improves MAPE by 6%.
  3. Caveat: subsequent replication failed out-of-sample (data-snooping concern); Derwent Capital fund based on it closed 2012.
- **Relevance to GTOS:** Cautionary tale for K54 v2 sentiment features — single-asset, single-source sentiment features should require Bonferroni-corrected, walk-forward, OOS validation.
- **Potential hypothesis:** Multi-source sentiment-composites (Twitter + FEARS + news) more robust than single-source.
- **Cross-domain:** 19, 20

### Social Mood and Financial Economics
- **Authors:** John Nofsinger
- **Year:** 2005
- **Source:** Journal of Behavioral Finance, vol. 6(3), pages 144-160
- **URL:** https://www.tandfonline.com/doi/abs/10.1207/s15427579jpfm0603_4
- **Mechanism:** sentiment
- **Abstract:** Social mood drives correlated decisions across consumers, investors, managers. Stock market itself = direct social-mood gauge.
- **Key findings:**
  1. Mood extremes → correlated optimism/pessimism in IPOs, M&A, capex, leverage.
  2. Market trends *follow* social mood (causality direction matters).
  3. Predicts vol + volume cycles.
- **Relevance to GTOS:** Theoretical anchor for why retail-flow-driven instruments (NAS100, GBPJPY) have decay tied to social-mood cycles.
- **Potential hypothesis:** Social-mood proxy (e.g., CSI, AAII bull-bear) can serve as regime feature in K54.
- **Cross-domain:** 13, 16

### Good Day Sunshine: Stock Returns and the Weather
- **Authors:** David Hirshleifer, Tyler Shumway
- **Year:** 2003
- **Source:** Journal of Finance, vol. 58(3), pages 1009-1032
- **URL:** https://www.jstor.org/stable/3094570
- **Mechanism:** sentiment / mood
- **Abstract:** Morning sunshine at exchange-city positively correlates with daily returns (26 countries 1982-1997).
- **Key findings:**
  1. Sunshine predicts returns; rain/snow do not (after controlling for sunshine).
  2. Difficult to reconcile with rational pricing.
  3. Mood-based investor decision evidence.
- **Relevance to GTOS:** Mood effects are real but small — supports inclusion of *time-of-day / day-of-week* features in K54 (already implicitly in kill-zone schedule).
- **Potential hypothesis:** Per-instrument expectancy modulated by exchange-city weather is small (≤5 bps daily) but composable into ensemble.
- **Cross-domain:** 02

---

## Section 5 — Behavioral asset-pricing anomalies (sentiment-anomaly, momentum, reversal, Stambaugh-Yu-Yuan)

### The Short of It: Investor Sentiment and Anomalies
- **Authors:** Robert Stambaugh, Jianfeng Yu, Yu Yuan
- **Year:** 2012
- **Source:** Journal of Financial Economics, vol. 104(2), pages 288-302
- **URL:** https://www.aqr.com/-/media/AQR/Documents/AQR-Insight-Award/2012/The-Short-of-It.pdf
- **Mechanism:** sentiment / limits-of-arbitrage
- **Abstract:** Investor-sentiment combined with short-sale impediments → asymmetric mispricing. Anomalies' long-short profitability concentrated post-high-sentiment periods.
- **Key findings:**
  1. Each tested anomaly is stronger after high sentiment.
  2. The short leg drives the result; long leg unrelated to sentiment.
  3. High sentiment → overpricing concentrated, with shorting blocked.
- **Relevance to GTOS:** Theoretical anchor for asymmetric LONG-vs-SHORT effects. F2/A6 LONG-side decay during high-sentiment trending_bull cohorts is exactly Stambaugh-Yu-Yuan symmetric prediction.
- **Potential hypothesis:** GTOS expectancy on SHORT side should be *more stable* than LONG side as decay unfolds — consistent with H29 + side-aware sizing finding.
- **Cross-domain:** 22, 14, 15

### Arbitrage Asymmetry and the Idiosyncratic Volatility Puzzle
- **Authors:** Robert Stambaugh, Jianfeng Yu, Yu Yuan
- **Year:** 2015
- **Source:** Journal of Finance, vol. 70(5), pages 1903-1948
- **URL:** https://www.nber.org/system/files/working_papers/w18560/w18560.pdf
- **Mechanism:** sentiment / limits-of-arbitrage
- **Abstract:** Arbitrage asymmetry (long-only friendly) + idiosyncratic vol → negative IVOL-return relation explained.
- **Key findings:**
  1. IVOL-return negative among overpriced stocks.
  2. IVOL-return positive among underpriced stocks.
  3. High sentiment strengthens asymmetry.
- **Relevance to GTOS:** Connects vol regime to behavioral premia. Reinforces side-aware sizing logic at the instrument level.
- **Potential hypothesis:** XAUUSD high-IVOL periods + LONG-side bias → expectancy collapse (matches A6 finding).
- **Cross-domain:** 16, 22

### Returns to Buying Winners and Selling Losers (Momentum)
- **Authors:** Narasimhan Jegadeesh, Sheridan Titman
- **Year:** 1993
- **Source:** Journal of Finance, vol. 48(1), pages 65-91
- **URL:** https://www.bauer.uh.edu/rsusmel/phd/jegadeesh-titman93.pdf
- **Mechanism:** underreaction / overreaction
- **Abstract:** 3-12 month momentum strategy generates significant returns. ~1.49% monthly, not explained by systematic risk.
- **Key findings:**
  1. Past 3-12 month winners outperform losers next 3-12 months.
  2. Returns dissipate in years 2-3 (long-horizon reversal).
  3. Founder of momentum literature.
- **Relevance to GTOS:** Edge mechanism for trend-trading at H1+ timeframes; underpins continuation post-OB-retest. F11 OB-decay velocity may have momentum-decay parallels.
- **Potential hypothesis:** Trend-following overlay (only enter OB-retest aligned with H4 momentum) preserves expectancy as edge decays.
- **Cross-domain:** 14

### Does the Stock Market Overreact?
- **Authors:** Werner DeBondt, Richard Thaler
- **Year:** 1985
- **Source:** Journal of Finance, vol. 40(3), pages 793-808
- **URL:** https://onlinelibrary.wiley.com/doi/full/10.1111/j.1540-6261.1985.tb05004.x
- **Mechanism:** overreaction
- **Abstract:** Loser portfolios outperform winners by ~24.6pp 36 months after formation. Asymmetric (losers > winners). January concentration.
- **Key findings:**
  1. Long-horizon mean reversion in extremes.
  2. Asymmetric: losers' rebound > winners' fade.
  3. Most excess returns realized in January.
- **Relevance to GTOS:** OB-retest is short-horizon analog of DeBondt-Thaler reversal. Asymmetric (loss-side stronger) parallels GTOS H29 8% DD reduction logic.
- **Potential hypothesis:** Post-loss expectancy on next OB-retest entry is higher than post-win entry (mean reversion of trader-state).
- **Cross-domain:** 14, 15

### Post-Earnings-Announcement Drift: Delayed Price Response or Risk Premium?
- **Authors:** Victor Bernard, Jacob Thomas
- **Year:** 1989
- **Source:** Journal of Accounting Research, vol. 27, pages 1-36
- **URL:** https://www.jstor.org/stable/2491062
- **Mechanism:** underreaction
- **Abstract:** Documents PEAD: top-vs-bottom SUE decile spread positive 41/48 quarters. Rejects risk-premium explanation.
- **Key findings:**
  1. Investors fail to fully incorporate current earnings into future expectations.
  2. Drift continues for ~60 trading days post-announcement.
  3. Persistent across decades.
- **Relevance to GTOS:** Classical underreaction evidence. Pre-news-event filtering for K54 v2 should weight upcoming-earnings/data-release calendar.
- **Potential hypothesis:** OB-retest entries 1-3 days post-major-news show different expectancy than typical bars (delayed-reaction premium / discount).
- **Cross-domain:** 14

### Forecasting Crashes: Trading Volume, Past Returns, and Conditional Skewness in Stock Prices
- **Authors:** Joseph Chen, Harrison Hong, Jeremy Stein
- **Year:** 2001
- **Source:** Journal of Financial Economics, vol. 61(3), pages 345-381
- **URL:** http://www.columbia.edu/~hh2679/jfe-forcrash.pdf
- **Mechanism:** overreaction / limits-of-arbitrage
- **Abstract:** Negative skewness most pronounced in stocks with: (i) volume increase relative to trend, (ii) positive 36-month returns. Hong-Stein differences-of-opinion + short-sales constraints model.
- **Key findings:**
  1. Volume + past returns predict crash risk.
  2. Mechanism: hidden bear opinions accumulate behind short-sales-constraints.
  3. Short-sale-blocked + bull-trend → crash setup.
- **Relevance to GTOS:** Index trading (NAS100/US30) — crash risk after sustained rally + volume expansion. Connects to GTOS Bull/Bear/Judge debate (research-door-wired N62).
- **Potential hypothesis:** SHORT-side OB retests on indices are *better* than baseline after high-volume bull-trend periods (crash-tail loading).
- **Cross-domain:** 12, 16

### Economic Links and Predictable Returns
- **Authors:** Lauren Cohen, Andrea Frazzini
- **Year:** 2008
- **Source:** Journal of Finance, vol. 63(4), pages 1977-2011
- **URL:** http://www.econ.yale.edu/~shiller/behfin/2006-04/cohen-frazzini.pdf
- **Mechanism:** underreaction
- **Abstract:** Stock prices fail to incorporate news of economically-related firms (customers/suppliers). Long-short customer-momentum strategy yields >150bps monthly.
- **Key findings:**
  1. Attention-constrained investors → cross-asset news diffusion is gradual.
  2. Generates predictable returns at portfolio horizon.
  3. Smith Breeden Prize 2008.
- **Relevance to GTOS:** Cross-asset correlation gate (additive HALVE/REJECT) is GTOS's analog. Currency-pair attention constraints likely produce similar lag in GBPJPY off USD news.
- **Potential hypothesis:** Cross-asset feature in K54 v2 capturing leading-instrument move (e.g., EURUSD H1 move 30 min before GBPUSD M15 entry) provides incremental edge.
- **Cross-domain:** 13, 14

---

## Section 6 — Adaptive markets / decay literature; recent retail-flow + LLM regime

### Does Academic Research Destroy Stock Return Predictability?
- **Authors:** R. David McLean, Jeffrey Pontiff
- **Year:** 2016
- **Source:** Journal of Finance, vol. 71(1), pages 5-32
- **URL:** https://www.fmg.ac.uk/sites/default/files/2020-08/Jeffrey-Pontiff.pdf
- **Mechanism:** adaptive (decay)
- **Abstract:** 82 characteristics, 68 studies. Out-of-sample returns 26% lower; post-publication returns 58% lower. 32% decay attributable to publication-induced arbitrage.
- **Key findings:**
  1. Anomalies decay post-publication (price-pressure / arbitrageur-learning effect).
  2. Out-of-sample-only decay = data-mining contribution (~26%).
  3. Publication-effect (~32%) is real, separable.
- **Relevance to GTOS (CRITICAL for edge-decay):** Direct empirical evidence supporting Lo's AMH + CEO's #1 concern. F11 OB-zone decay velocity (+16.8 → +4.6 over ~3-4 years) consistent with McLean-Pontiff publication-decay magnitude. The OB / SMC concept is now very widely "published" (TradingView templates, retail education).
- **Potential hypothesis:** GTOS's monthly-decay-monitor (S1) baseline should target McLean-Pontiff-style ~3-5%/year decay; sharp deviation (>10%/year) = signal of distinctly accelerating arbitrage.
- **Cross-domain:** 02, all factor domains

### Bubbles for Fama
- **Authors:** Robin Greenwood, Andrei Shleifer, Yang You
- **Year:** 2019
- **Source:** Journal of Financial Economics, vol. 131(1), pages 20-43
- **URL:** https://shleifer.scholars.harvard.edu/publications/bubbles-fama
- **Mechanism:** sentiment / extrapolation
- **Abstract:** Sharp price increases on industry portfolios → don't predict low average returns (Fama right) but DO predict heightened *crash probability*. Run-up attributes (vol, turnover, issuance, path) help forecast crashes + future returns.
- **Key findings:**
  1. Bubbles are conditionally identifiable (≥40% crash probability when in red zone).
  2. Run-up characteristics matter beyond level.
  3. Reconciles Fama (mean-zero) with bubbles (skewness).
- **Relevance to GTOS:** Crash-conditional risk relevant for index instruments (NAS100/US30) post-sustained-rally regimes. Risk-management overlay candidate.
- **Potential hypothesis:** S79 + side-aware sizing should reduce LONG-side risk when concurrent industry-bubble characteristics are flashing red zone.
- **Cross-domain:** 12, 16

### Predictable Financial Crises
- **Authors:** Robin Greenwood, Samuel Hanson, Andrei Shleifer, Jakob Sørensen
- **Year:** 2022 (NBER w27396)
- **Source:** NBER Working Paper 27396
- **URL:** https://www.nber.org/papers/w27396
- **Mechanism:** sentiment / extrapolation
- **Abstract:** "R-zone" indicator: rapid 3-year credit + asset-price growth → ~40% probability of crisis within 3 years vs ~7% normal.
- **Key findings:**
  1. Crises are substantially predictable from credit + asset-price warning signs.
  2. Slow-developing → policy-actionable lead time.
  3. Sentiment sustains credit-market overheating.
- **Relevance to GTOS:** Macro-regime risk overlay. GTOS multi-instrument exposure should dial down during R-zone periods (correlated downside risk).
- **Potential hypothesis:** Edge in correlated trades (e.g., commodity + commodity-currency) correlates with R-zone state.
- **Cross-domain:** 16, 22

### Expectations of Returns and Expected Returns
- **Authors:** Robin Greenwood, Andrei Shleifer
- **Year:** 2014
- **Source:** Review of Financial Studies, vol. 27(3), pages 714-746
- **URL:** https://scholar.harvard.edu/files/shleifer/files/expectations_of_returns_public._feb_2014_print.pdf
- **Mechanism:** extrapolation
- **Abstract:** 6 measures of investor return-expectations 1963-2011. Highly correlated with each other + past returns; *negatively* correlated with model-based expected returns.
- **Key findings:**
  1. Investors extrapolate past trends linearly.
  2. Extrapolation is wrong on average (mean-reversion in returns).
  3. Calibrates simple behavioral model where fundamentals require premium to absorb extrapolative shocks.
- **Relevance to GTOS:** Extrapolation is empirically primary belief-formation mechanism. K54 v2 should include explicit "extrapolation feature" (recent-trend persistence).
- **Potential hypothesis:** Expectancy is highest when GTOS signal CONTRADICTS the extrapolative-belief consensus (LONG OB after extended sell-off, SHORT OB after extended rally).
- **Cross-domain:** 14

### In Search of the Origins of Financial Fluctuations: The Inelastic Markets Hypothesis
- **Authors:** Xavier Gabaix, Ralph Koijen
- **Year:** 2021 (NBER w28967)
- **Source:** NBER Working Paper 28967
- **URL:** https://www.nber.org/system/files/working_papers/w28967/w28967.pdf
- **Mechanism:** limits-of-arbitrage / flow
- **Abstract:** Aggregate stock market is inelastic; institutions are constrained. $1 → ~$5 aggregate market value increase. Flow-driven price impact long-lasting.
- **Key findings:**
  1. Demand elasticity ≈ 0.2 (highly inelastic).
  2. Flows not information drive a meaningful share of price variance.
  3. Reframes general-equilibrium asset-pricing.
- **Relevance to GTOS:** Reinforces edge mechanism — small flow imbalances (stop cascades) generate disproportionate price moves; that's the precondition for OB retest's mean reversion. M5 of inelasticity = M5 microstructure to which GTOS already responds.
- **Potential hypothesis:** Edge magnitude correlates with inelasticity proxy (per-instrument bid-ask depth + low retail-day-volume environment).
- **Cross-domain:** 06, 12, 22

### A Theory of Fads, Fashion, Custom, and Cultural Change as Informational Cascades
- **Authors:** Sushil Bikhchandani, David Hirshleifer, Ivo Welch
- **Year:** 1992
- **Source:** Journal of Political Economy, vol. 100(5), pages 992-1026
- **URL:** https://snap.stanford.edu/class/cs224w-readings/bikhchandani92fads.pdf
- **Mechanism:** herding
- **Abstract:** Information cascade: rational agents follow predecessors when own-signal weighted less than crowd-signal. Cascades fragile but pervasive.
- **Key findings:**
  1. Rational herding (cascades) explains seemingly irrational mass behavior.
  2. Cascades can be wrong; correction requires public-signal shock.
  3. Mathematical foundation for fads / fashion / market panics.
- **Relevance to GTOS:** Stop-cascade events are *quintessential* informational cascades. Edge captures the moment cascades self-terminate (price exhausts, retests OB).
- **Potential hypothesis:** Cascade-strength proxy (volume + speed) at the breaking of structure → predicts retest probability + magnitude.
- **Cross-domain:** 06, 09

### Rational Herding in Financial Economics
- **Authors:** Andrea Devenow, Ivo Welch
- **Year:** 1996
- **Source:** European Economic Review, vol. 40(3-5), pages 603-615
- **URL:** https://www.ivo-welch.info/research/journalcopy/1996-eer.pdf
- **Mechanism:** herding
- **Abstract:** Survey: rational herding from (a) payoff externalities, (b) principal-agent / reputation, (c) informational cascades.
- **Key findings:**
  1. Multiple distinct mechanisms produce herding (not all behavioral-bias-driven).
  2. Rational and irrational herding coexist; identification is hard.
  3. Equilibrium herding can be efficient or destructively distortive.
- **Relevance to GTOS:** Theoretical taxonomy — relevant for separating retail-driven (irrational, A2 dumb-baseline cohort) from institutional-driven (rational, RR-driven) herding in instrument-specific edge analysis.
- **Potential hypothesis:** Edge is highest when rational + irrational herding align in same direction (rare); decays when they diverge.
- **Cross-domain:** 06, 09

### All That Glitters: The Effect of Attention and News on the Buying Behavior of Individual and Institutional Investors
- **Authors:** Brad Barber, Terrance Odean
- **Year:** 2008
- **Source:** Review of Financial Studies, vol. 21(2), pages 785-818
- **URL:** https://faculty.haas.berkeley.edu/odean/papers/Attention/All%20that%20Glitters.pdf
- **Mechanism:** sentiment / attention
- **Abstract:** Individual investors are net buyers of attention-grabbing stocks (news, abnormal volume, extreme returns). Asymmetry: only buy attention-grabbers, not sell.
- **Key findings:**
  1. Attention-asymmetric retail demand.
  2. Search-cost mechanism: too many stocks to monitor; news cuts the choice set.
  3. Persistent across brokerages.
- **Relevance to GTOS:** Retail-attention spike = predictable buying-pressure = potentially predictable mean-reversion fade (Tetlock-style overreaction). NAS100 / GBPJPY are the GTOS instruments most subject to retail attention.
- **Potential hypothesis:** Post-attention-spike SHORT setups (next 1-3 sessions) on retail-favorite instruments have positive expectancy.
- **Cross-domain:** 12, 18

### Peer Pressure: Social Interaction and the Disposition Effect
- **Authors:** Rawley Heimer
- **Year:** 2016
- **Source:** Review of Financial Studies, vol. 29(11), pages 3177-3209
- **URL:** https://academic.oup.com/rfs/article-abstract/29/11/3177/2583763
- **Mechanism:** sentiment / herding
- **Abstract:** Social-network access nearly doubles disposition effect. Causal identification via staggered brokerage-network entry.
- **Key findings:**
  1. Peer-effects amplify disposition effect.
  2. Connected traders converge on shared bias.
  3. Implications for retail-broker UI design.
- **Relevance to GTOS:** Underpins retail-flow-driven edge in social-trading-popular instruments. Connects to Reddit/WSB era (next paper).
- **Potential hypothesis:** Instruments with high copy-trading prevalence (FX majors) have stronger correlated stop-cascades → better OB-retest setups.
- **Cross-domain:** 18

### Hedge Fund Treasury Trading and Funding Fragility (LTCM Redux)
- **Authors:** OFR / Kruttli et al.
- **Year:** 2021
- **Source:** Federal Reserve Working Paper FEDS 2021-038
- **URL:** https://www.federalreserve.gov/econres/feds/files/2021038pap.pdf
- **Mechanism:** limits-of-arbitrage / funding
- **Abstract:** March 2020 Treasury basis-trade unwind. Hedge funds sold $173B Treasuries; basis jumped 100bps; repo costs spiked.
- **Key findings:**
  1. COVID-March 2020 = textbook funding-liquidity-crisis-triggered limits-of-arbitrage event.
  2. Dealer balance-sheet constraints + risk-limits forced unwinding.
  3. Dealer-of-last-resort role for Fed.
- **Relevance to GTOS:** Direct case study of edge-creating regime (forced unwinding → mean-reversion premium). Even Treasury markets — most liquid — see arbitrage limits.
- **Potential hypothesis:** GTOS expectancy in commodity + FX during funding-stress periods (TED spread > 60 bps) is higher than baseline.
- **Cross-domain:** 22, 16

### Do Stock Prices Move Too Much to be Justified by Subsequent Changes in Dividends?
- **Authors:** Robert Shiller
- **Year:** 1981
- **Source:** American Economic Review, vol. 71(3), pages 421-436
- **URL:** https://www.aeaweb.org/aer/top20/71.3.421-436.pdf
- **Mechanism:** sentiment / overreaction
- **Abstract:** Excess-volatility puzzle: actual stock-price std-dev exceeds bound implied by efficient-markets / rational-dividend-discount.
- **Key findings:**
  1. Founding evidence for excess volatility.
  2. Cited in Shiller's 2013 Nobel.
  3. Frame for rejecting strict EMH at long horizons.
- **Relevance to GTOS:** Foundational rejection of constant-efficiency assumption. Anchors AMH theoretical motivation.
- **Potential hypothesis:** Excess-volatility-conditional features (realized-vol vs. implied-vol gap) can serve as regime indicator in K54.
- **Cross-domain:** 16, 12

### A Survey of Behavioral Finance
- **Authors:** Nicholas Barberis, Richard Thaler
- **Year:** 2003 (Handbook of the Economics of Finance, ch. 18)
- **Source:** Elsevier Handbook
- **URL:** https://nicholasbarberis.github.io/ch18_6.pdf
- **Mechanism:** overview
- **Abstract:** Comprehensive survey: limits of arbitrage + investor psychology → asset pricing applications.
- **Key findings:**
  1. Two pillars of behavioral finance.
  2. Maps biases to anomalies (overconfidence → trading volume, loss aversion → equity premium).
  3. Authoritative pre-2010 reference.
- **Relevance to GTOS:** Comprehensive theory anchor; aging but still a primary reading-list source for K54 feature theory.
- **Potential hypothesis:** N/A (survey).
- **Cross-domain:** All behavioral domains

### Foundations of Technical Analysis: Computational Algorithms, Statistical Inference, and Empirical Implementation
- **Authors:** Andrew Lo, Harry Mamaysky, Jiang Wang
- **Year:** 2000
- **Source:** Journal of Finance, vol. 55(4), pages 1705-1765
- **URL:** https://www.cis.upenn.edu/~mkearns/teaching/cis700/lo.pdf
- **Mechanism:** sentiment / pattern
- **Abstract:** Kernel-regression-based automated chart pattern recognition (head-shoulders, double-bottom, etc.). Tests 1962-1996 US stocks.
- **Key findings:**
  1. Several patterns provide statistically significant incremental information.
  2. Smaller-cap stocks show stronger pattern-conditional return distributions.
  3. Establishes that visual / qualitative TA has measurable signal.
- **Relevance to GTOS:** Direct legitimization of pattern-based trading at academic level. OB / FVG patterns can be tested with same kernel-regression methodology.
- **Potential hypothesis:** Lo-Mamaysky-Wang methodology applied to OB-retest patterns yields decade-spanning expectancy panel — empirical-decay characterization.
- **Cross-domain:** 14, 02

---

## Section 7 — LLM-as-sentiment / GameStop / WallStreetBets / 2020-2025 retail regime

### Can ChatGPT Forecast Stock Price Movements? Return Predictability and Large Language Models
- **Authors:** Alejandro Lopez-Lira, Yuehua Tang
- **Year:** 2023-2024 (latest revision)
- **Source:** SSRN 4412788, arXiv 2304.07619
- **URL:** https://arxiv.org/abs/2304.07619
- **Mechanism:** sentiment / adaptive (LLM)
- **Abstract:** ChatGPT predicts stock-market reactions from news headlines without finance-specific training. Tests post-knowledge-cutoff data.
- **Key findings:**
  1. GPT-4 hits ~90% portfolio-day directional accuracy on initial reaction.
  2. Sharpe drops 6.54 (Q4-2021) → 3.68 (2022) → 2.33 (2023) → 1.22 (Jan-May 2024) — *real-time adaptive-decay observed*.
  3. Strategy returns decline as LLM-adoption rises → AMH-consistent.
  4. Forecast quality scales with model size.
- **Relevance to GTOS (HIGHEST PHASE 2 RELEVANCE):** Tri-junction paper (17/19/20). Direct empirical AMH demonstration on LLM-sentiment alpha: real-time live-decay from 6.54 → 1.22 Sharpe in 30 months. K54 + LLM-as-sentiment must factor in this fast-decaying alpha. Validates GTOS Sonnet-4.6-as-MSO-gate vs. raw-news-LLM positioning (gate is stable; news-sentiment alpha decays).
- **Potential hypothesis:** LLM-news-sentiment alpha will continue toward zero by 2027; GTOS edge needs to depend on infrastructure (OB precision + safety stack) rather than LLM-feature alpha alone.
- **Cross-domain:** 19, 20, 02 (decay measurement)

### FinBERT: A Large Language Model for Extracting Information from Financial Text
- **Authors:** Allen Huang et al.
- **Year:** 2023
- **Source:** Contemporary Accounting Research, vol. 40
- **URL:** https://onlinelibrary.wiley.com/doi/10.1111/1911-3846.12832
- **Mechanism:** sentiment (LLM)
- **Abstract:** Domain-specific BERT fine-tuned on finance corpus (10-Ks, analyst reports, earnings calls). 88.2% out-of-sample classification accuracy vs. 62.1-73.6% for lexicon-based / NB / SVM methods.
- **Key findings:**
  1. Domain-pretraining boosts accuracy 15-25 pp over general-purpose BERT.
  2. Words used for classification are concentrated in finance vocabulary.
  3. Reduces Loughran-McDonald-style misclassification.
- **Relevance to GTOS:** Engineering reference for K54 v2 sentiment features; FinBERT-style fine-tune is a viable path before LLM-API. FinBERT at zero marginal cost contrasts to API-based LLM ($).
- **Potential hypothesis:** FinBERT-derived per-instrument sentiment is sufficient for K54 v2; expensive zero-shot LLM gives marginal additional accuracy.
- **Cross-domain:** 19, 20

### A Note on GameStop, Short Squeezes, and Autodidactic Herding
- **Authors:** Tony Klein
- **Year:** 2022
- **Source:** Finance Research Letters
- **URL:** https://papers.ssrn.com/sol3/Delivery.cfm/SSRN_ID3857594_code2369410.pdf?abstractid=3845722
- **Mechanism:** herding / sentiment
- **Abstract:** Examines January 2021 GameStop short-squeeze as test case for retail-investor-coordination via Reddit. Frames as autodidactic herding (collective self-education + signal sharing).
- **Key findings:**
  1. Reddit-coordinated retail action moves prices on >$1B-mcap stock.
  2. Information cascades amplified by social media at unprecedented speed.
  3. Hedge funds (Melvin Capital) blew up despite institutional sophistication.
- **Relevance to GTOS:** Documents 2021-onward retail-flow regime change. NAS100 component dynamics post-2020 changed. Raises question whether OB/SMC-themed retail education is creating analogous coordinated stop-hunt behavior.
- **Potential hypothesis:** GTOS edge changes as retail education on SMC/OB concepts compounds; instruments most-discussed on retail-trading social media decay first.
- **Cross-domain:** 12

### The Meme Stock Frenzy: Origins and Implications
- **Authors:** Dhruv Aggarwal, Albert Choi, Yoon-Ho Alex Lee
- **Year:** 2024
- **Source:** SSRN 4432824
- **URL:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4432824
- **Mechanism:** herding / sentiment
- **Abstract:** Comprehensive treatment of GME/AMC/meme-stock phenomenon. Distinguishes social-coordination mechanism from prior retail-mania episodes.
- **Key findings:**
  1. Meme-stock phenomenon is structurally different from prior retail manias (zero-commission + Reddit + retail options).
  2. Asymmetric impact on smaller-cap names; spillover to indices indirect.
  3. Regulatory implications for market-structure reform.
- **Relevance to GTOS:** Background for why post-2020 NAS100 dynamics differ. Retail-options-flow gamma squeeze is a new mechanism; OB-retest behavior on tech-mega-cap may have meme-flow contamination.
- **Potential hypothesis:** Index-OB expectancy is degraded on meme-favorite-component-heavy days; mitigation via cross-instrument correlation gate (already operational).
- **Cross-domain:** 12, 16

### Sentiment, Social Media and Meme Stock Return Predictability
- **Authors:** Jingrui Li, Zijian Li
- **Year:** 2024
- **Source:** SSRN 4947010
- **URL:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4947010
- **Mechanism:** sentiment / herding
- **Abstract:** Tests 3-7 day return predictability from Google search vs. Bloomberg Twitter sentiment for meme stocks.
- **Key findings:**
  1. Google search sentiment predicts meme stocks at 3-7 day horizon.
  2. Bloomberg Twitter only predicts 1-day returns.
  3. Sentiment-source matters for horizon match.
- **Relevance to GTOS:** Multi-source sentiment matters; aligns with FEARS / Twitter / news-flow ensemble for K54 v2.
- **Potential hypothesis:** Composite sentiment (search + social + news) is more durable than single-source.
- **Cross-domain:** 19, 20

### Retail Trader Sophistication and Stock Market Quality: Evidence from Brokerage Outages
- **Authors:** Brad Barber, Xing Huang, Philippe Jorion, Terrance Odean, Christopher Schwarz (Eaton et al. variants)
- **Year:** 2022
- **Source:** Journal of Financial Economics
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S0304405X22001726
- **Mechanism:** herding / sentiment
- **Abstract:** Robinhood outages → reduced retail participation → reduced liquidity stress + lower vol on high-retail-interest stocks. Traditional broker outages have opposite effect.
- **Key findings:**
  1. Inexperienced retail traders herd more — create inventory risk for liquidity providers.
  2. Effect causal (outages = exogenous shocks).
  3. Different retail platforms contribute differently to market quality.
- **Relevance to GTOS:** Per-platform retail-flow has measurable price-discovery footprint. Supports GTOS treating different instruments (NAS100 vs XAUUSD) differently for retail-flow contamination.
- **Potential hypothesis:** OB-retest edge on stocks/indices with high Robinhood-flow share (NAS100 components) is more volatile than on lower-retail instruments (XAGUSD).
- **Cross-domain:** 12

### Will the Reddit Rebellion Take You to the Moon? Evidence from WallStreetBets
- **Authors:** Bradford Jordan + co-authors (FinMarkets Portfolio Management 2023)
- **Year:** 2023
- **Source:** Financial Markets and Portfolio Management, vol. 37(1)
- **URL:** https://link.springer.com/article/10.1007/s11408-022-00415-w
- **Mechanism:** herding / sentiment
- **Abstract:** Tests profitability of WSB-recommended portfolios. Mixed: not risk-adjusted profitable buy-and-hold; but tops investment-bank analysts on best-stock detection.
- **Key findings:**
  1. WSB-following portfolio yields no alpha 2017-2022.
  2. Post-GME, WSB report quality declined; price-pressure-strategy fraction rose 165%.
  3. WSB-attention trades correlate with negative returns.
- **Relevance to GTOS:** Retail-attention proxies (WSB mentions, Reddit volume) are noisy alpha-source — expectations should be modest. Directionally helpful for filtering.
- **Potential hypothesis:** WSB-mention surge on a tradeable equity / index → next-week SHORT-skew.
- **Cross-domain:** 12, 18

### Investor Sentiment, Beta, and the Cost of Equity Capital (Stambaugh-Yuan extension)
- **Authors:** Antoniou, Doukas, Subrahmanyam (related)
- **Year:** 2016 (cross-link)
- **Source:** Multiple
- **URL:** N/A (survey reference)
- **Mechanism:** sentiment / asset pricing
- **Abstract:** Sentiment-state interaction with risk factors; high sentiment → flatter security-market-line; low sentiment → steeper.
- **Key findings:**
  1. Beta-return relation depends on sentiment regime.
  2. CAPM "fails" in high-sentiment, holds in low-sentiment.
- **Relevance to GTOS:** Reinforces regime-conditioned expectancy framing in K54 v2.
- **Potential hypothesis:** Risk-on regime degrades GTOS LONG-side expectancy by similar mechanism.
- **Cross-domain:** 13

### Adaptive Market Hypothesis: Empirical Analysis of Time-Varying Market Efficiency of Cryptocurrencies
- **Authors:** Various (Cogent Economics & Finance 2020)
- **Year:** 2020
- **Source:** Cogent Economics & Finance, vol. 8(1), 1719574
- **URL:** https://www.tandfonline.com/doi/full/10.1080/23322039.2020.1719574
- **Mechanism:** adaptive
- **Abstract:** Time-varying efficiency on top cryptos. Bitcoin most efficient over time; periods of efficiency interspersed with inefficiency.
- **Key findings:**
  1. AMH framework outperforms EMH for cryptos.
  2. Bitcoin trends toward efficiency over time.
  3. Method: rolling automatic variance ratio test.
- **Relevance to GTOS:** Cross-asset AMH evidence; methodology applicable for monthly-decay-monitor.
- **Potential hypothesis:** GTOS XAUUSD efficiency-state correlates inversely with crypto-market-stress (alternative-asset rotation).
- **Cross-domain:** 02

### High-Frequency Investor Sentiment and Stock Returns Prediction (MIDAS models)
- **Authors:** Various (China Finance Review International 2024)
- **Year:** 2024
- **Source:** China Finance Review International
- **URL:** https://www.emerald.com/cfri/article/doi/10.1108/CFRI-12-2023-0344
- **Mechanism:** sentiment
- **Abstract:** Sentiment from forum posts at 5-min interval predicts near-term returns. MIDAS-based mixed-frequency forecasting.
- **Key findings:**
  1. High-frequency sentiment outperforms daily aggregation for daily forecasts.
  2. Non-trading-hours sentiment has stronger signal than trading-hours sentiment.
  3. MIDAS regression captures lead-lag structure.
- **Relevance to GTOS:** Direct method for K54 v2 intraday sentiment features; supports GTOS M15 cadence with sub-15-min sentiment input.
- **Potential hypothesis:** Pre-market-open sentiment (00-06 UTC for XAUUSD) predicts London-session OB-retest expectancy.
- **Cross-domain:** 19, 20, 02

---

## Cross-domain handoff registry

| Outbound topic | Cross-link to domain | Reason |
|----------------|----------------------|--------|
| Individual-trader cognitive biases (overconfidence at trader-level) | 18 | DHS, prospect theory at individual level |
| Pattern-based / TA / momentum quant strategies | 14 | Lo-Mamaysky-Wang, Jegadeesh-Titman, Cohen-Frazzini |
| Mean-reversion / contrarian portfolios | 15 | DeBondt-Thaler |
| LLM-extracted sentiment infrastructure | 19, 20 | Lopez-Lira-Tang, FinBERT, Tetlock-MTW, Loughran-McDonald |
| Sentiment-driven volatility (VIX, fear) | 16 | Stambaugh-Yu-Yuan, Greenwood-Shleifer-You |
| Round-number anchoring | 09 | Bikhchandani-Hirshleifer-Welch cascades at price levels |
| Order-flow microstructure / cascades | 06 | DeLong-Shleifer-Summers-Waldmann, Garleanu-Pedersen |
| Hedge-fund / arbitrageur capital constraints | 22 | Shleifer-Vishny, Brunnermeier-Nagel, Gromb-Vayanos, OFR-Treasury |
| Cross-asset behavioral spillover | 13 | Cohen-Frazzini, Greenwood-Shleifer (sentiment) |
| Gold-specific commodity behavior | 10 | Auer-Caraiani, Anghel, COVID-commodity AMH |
| FX-specific behavioral evidence | 11 | Indonesian FX AMH study (cross-link only) |

---

## Top 3 most-relevant-to-GTOS (esp. supporting Lo's AMH framing)

1. **Lo (2004) — Adaptive Markets Hypothesis** — direct theoretical anchor for CEO's #1 concern (edge decay). Predicts exactly the F11 OB-zone-decay pattern observed.
2. **Lopez-Lira & Tang (2024) — ChatGPT Forecast Stock Price Movements** — empirical AMH demonstration in real-time on LLM-news-sentiment: Sharpe collapsed 6.54 → 1.22 in 30 months as adoption rose. Tri-junction paper (17/19/20). Directly relevant to S79 + K54 + future LLM-as-sentiment design.
3. **McLean & Pontiff (2016) — Does Academic Research Destroy Stock Return Predictability** — empirical decay magnitudes (32% post-publication). Provides quantitative baseline for GTOS's monthly-decay-monitor (S1) targets and Phase 2 K54 expectations.

## Top 1 surprise

**Brunnermeier & Nagel (2004)** — Hedge funds RODE the tech bubble; did not arbitrage it. Refutes "smart money corrects mispricings" baseline assumption. Suggests GTOS in retail-heavy instruments (NAS100, GBPJPY) may face an inverse-arbitrage regime where institutional + retail flows align rather than offset. Connects to HALLUC-1 NAS100 93% precision-bug context (post-2020 retail-tech-narrative regime).

## 2-3 hypotheses for downstream synthesis / Phase 2

H1. **Regime-conditioned sentiment features outperform unconditional sentiment in K54 v2.** Rationale: Garcia (2013) shows pessimism effect 3-4× stronger in recessions; Stambaugh-Yu-Yuan show anomalies stronger post-high-sentiment. Composite (sentiment × regime) feature should beat sentiment alone.

H2. **Edge half-life is inversely proportional to retail social-media attention.** Rationale: McLean-Pontiff show post-publication arbitrage decay; Heimer (2016) shows social-network amplifies bias; WSB / Robinhood / OB-education make retail attention highly trackable. Test: rank GTOS instruments by retail-mention frequency; expect inverse correlation with realized expectancy decay velocity.

H3. **LLM-news-sentiment alpha will continue decaying toward zero by 2027.** Rationale: Lopez-Lira-Tang real-time observation 6.54 → 1.22 Sharpe in 30 months. GTOS should NOT bet edge on LLM-news-sentiment alpha specifically; should bet on infrastructure (OB precision + safety stack + tick microstructure features that are NOT publishable / democratized).

## Cross-domain handoffs (immediate)

- **Domain 18 (cognitive biases):** Daniel-Hirshleifer-Subrahmanyam overconfidence, Kahneman-Tversky prospect theory, Barber-Odean attention.
- **Domain 19 / 20 (LLM sentiment):** Lopez-Lira-Tang, FinBERT, Loughran-McDonald, Bollen, Tetlock-MTW.
- **Domain 14 (momentum):** Jegadeesh-Titman, Hong-Stein, Cohen-Frazzini, Lo-Mamaysky-Wang.
- **Domain 22 (hedge fund / limits-of-arbitrage):** Shleifer-Vishny, Brunnermeier-Nagel, Gromb-Vayanos, Garleanu-Pedersen, OFR Treasury 2021.
- **Domain 16 (vol regime):** Chen-Hong-Stein, Stambaugh-Yu-Yuan-2015, Greenwood-Shleifer-You, Garleanu-Pedersen.
- **Domain 10 (gold):** Predictability of Precious Metals AMH, COVID-commodity AMH, Cryptocurrencies-Gold-WTI.
- **Domain 12 (equity indices / options gamma):** All retail-flow / GameStop / WSB / index-bubble papers.
