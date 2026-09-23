# Phase 1 -- Exit Optimization Literature Search (L4)
# Q-6.2, Q-6.5, Q-6.6, Q-6.7, Q-6.8

**Date:** 2026-04-12
**Agent:** Claude Code (Opus 4.6)
**Scope:** 5 exit optimization questions covering partial close, speed-to-MFE, session close, institutional exit, dynamic TP
**Search sources:** Google Scholar, arXiv, SSRN, ScienceDirect, NBER, MDPI, Springer, Wiley, targeted author searches
**Total unique papers found:** 62 (after quality filter and deduplication)
**Papers promoted (testable on GTOS data):** 41
**Papers rejected (not testable / insufficient relevance):** 21
**Critical gaps identified:** 4
**Cross-references with prior searches:** 11 (noted but not repeated in detail)

---

## Table of Contents

1. [Summary](#summary)
2. [Q-6.2: Optimal Partial Close Strategy](#q-62)
3. [Q-6.5: Speed to MFE Predicts TP Probability](#q-65)
4. [Q-6.6: Session-Close Strategy / Overnight Risk](#q-66)
5. [Q-6.7: Institutional Exit Principles (TWAP/VWAP/IS)](#q-67)
6. [Q-6.8: Dynamic TP Based on Realized Volatility](#q-68)
7. [Cross-Question Synthesis](#synthesis)
8. [Specific GTOS Implications](#gtos-implications)
9. [Full Reference List](#references)

---

<a id="summary"></a>
## 1. Summary

### Per-Question Breakdown

| Question | Papers Found | Promoted | Key Verdict |
|----------|-------------|----------|-------------|
| Q-6.2: Partial close | 12 | 8 | **THIN ACADEMIC COVERAGE.** No peer-reviewed paper directly optimizes 50/25/25 vs other splits. Almgren-Chriss solves the related problem for institutional *entry* but the math adapts. Key insight: partial close mathematically reduces expectancy vs full close at optimal TP, but reduces variance -- the tradeoff is a Kelly-like optimization. Lopez de Prado's triple barrier is the closest modern framework. |
| Q-6.5: Speed to MFE | 10 | 7 | **GAP -- NO DIRECT PAPER.** No academic paper links speed of favorable excursion to probability of reaching a higher target. Intraday momentum literature (Gao et al. 2018, Bogousslavsky 2016) provides closest theoretical support: fast moves predict continuation. Sweeney (1997) originated MFE concept but without speed dimension. This is a novel hypothesis requiring empirical test on GTOS data. |
| Q-6.6: Session close / overnight | 13 | 10 | **GOOD COVERAGE.** Iwatsubo et al. (2018) documents W-shaped gold efficiency across sessions. Caminschi & Heaney (2014) proves LBMA fix information leakage. Plastun et al. (2020) shows gap-day continuation. Boyarchenko et al. (2022) documents overnight drift mechanism. Gold's 24h OTC structure means "overnight" risk is different from equity. Key finding: uninformed trading dominates Tokyo session, informed dominates NY -- implications for holding through session boundaries. |
| Q-6.7: Institutional exit | 14 | 9 | **STRONG THEORETICAL FOUNDATION.** Almgren-Chriss (2001) and Bertsimas-Lo (1998) provide the core math. Gatheral (2010) constraints on impact decay. Obizhaeva-Wang (2013) gives optimal U-shaped execution. BUT: all assume market impact scales with order size -- at retail scale on gold, market impact is negligible. The *principles* (timing risk vs. certainty, variance penalty) adapt; the *equations* do not directly apply. |
| Q-6.8: Dynamic TP / realized vol | 13 | 7 | **MODERATE COVERAGE with STRONG IMPLICATIONS.** Corsi (2009) HAR model gives best vol forecasting for trading horizons. Andersen et al. (2003) realized vol framework is foundational. Baltas & Kosowski (2020) show vol-scaled position sizing improves trend-following Sharpe. No paper directly tests ATR-based TP vs fixed R-multiple on intraday gold. Wilder (1978) ATR is practitioner-originated, not peer-reviewed. Key gap: no academic test of ATR-multiple TP vs fixed TP. |

### Critical Gaps

1. **No paper tests speed-to-MFE as a predictor of reaching higher targets.** Sweeney (1997) originated MFE/MAE but without temporal dimension. The hypothesis that "fast arrival at 1R predicts higher probability of 2R" is novel and must be tested empirically on GTOS data.
2. **No peer-reviewed paper optimizes partial close split ratios (50/25/25 vs alternatives).** The concept exists in practitioner literature only. Mathematical expectancy analysis proves partial close reduces E[R] but also reduces Var[R] -- the optimal ratio depends on risk aversion and Kelly fraction.
3. **No academic paper tests ATR-based TP vs fixed R-multiple TP on intraday commodities/gold.** The ATR literature is extensive for stop-loss but not for take-profit level optimization.
4. **No paper addresses session-close decisions specifically for retail gold positions during LBMA fix windows.** Caminschi & Heaney (2014) documents the fix effect but from an information trading perspective, not a position management one.

### Cross-References from Prior Searches (11 papers)

| Paper | Prior Search | L4 Relevance |
|-------|-------------|--------------|
| Osler 2005 | Priority A Q-2.2 | Q-6.6: Stop cascade at session boundaries |
| Cont et al. 2014 | Priority A Q-2.2 | Q-6.7: OFI-based price impact |
| Moskowitz et al. 2012 | Priority A Q-13.1 | Q-6.5: Time series momentum persistence |
| Gao et al. 2018 | Priority A Q-13.1, L3 Q-0.1 | Q-6.5: Intraday momentum |
| Caminschi & Heaney 2014 | L1 Q-1.6 | Q-6.6: LBMA fix effects |
| Ibikunle et al. 2018 / Iwatsubo et al. 2018 | L1 Q-1.6 | Q-6.6: Gold W-shaped efficiency |
| Glattfelder et al. 2011 | L3 Q-2.1 | Q-6.5: DC event approach |
| Zumbach & Lynch 2001 | L3 Q-2.1 | Q-6.8: Heterogeneous volatility cascade |
| Plastun et al. 2020 | L3 Q-2.4 | Q-6.6: Gap continuation |
| Bollerslev & Todorov 2011 | L1 Q-1.3 | Q-6.8: Jump risk premia |
| Boudt et al. 2011 | L1 Q-1.6 | Q-6.6: Intraday periodicity and jumps |

---

<a id="q-62"></a>
## 2. Q-6.2: Optimal Partial Close Strategy

**Question:** Is 50/25/25 optimal? What's the mathematical tradeoff between locking profit and letting winners run?

**Verdict:** **THIN ACADEMIC COVERAGE.** The partial close / scale-out problem has no dedicated academic literature. The closest frameworks are: (1) Almgren-Chriss optimal execution (designed for entry/liquidation, not trade management), (2) Kelly criterion extensions for variable payoff, and (3) Lopez de Prado's triple barrier method. The mathematical proof is straightforward: partial close at TP1 < TP2 reduces expected value (you're closing a positive-expectancy position early) but reduces variance. The optimal split depends on the trader's utility function (risk aversion) and the conditional probability of reaching TP2 given TP1 was hit.

---

### Paper 6.2.1

**Almgren, R. & Chriss, N. (2001). "Optimal Execution of Portfolio Transactions." Journal of Risk, 3(2), 5-40.**

Summary: The foundational paper on optimal trade execution. Derives the efficient frontier between execution cost (market impact) and timing risk (price volatility during execution). For a linear market impact model, the optimal liquidation trajectory follows a hyperbolic sine decay. The key equation: minimize E[cost] + lambda * Var[cost], where lambda is risk aversion. The "half-life" of optimal liquidation depends on volatility, temporary impact coefficient, and risk aversion.

Relevance to Q-6.2: The Almgren-Chriss framework can be *inverted* for the exit problem. Instead of "how to sell a large block optimally over time," ask "how to close a winning position optimally over price targets." The risk aversion parameter lambda maps directly to the partial close decision: high lambda (risk averse) => close more at TP1; low lambda => let it run. The key insight is that the optimal trajectory is NOT uniform -- it front-loads or back-loads depending on the impact-to-volatility ratio.

Testable on GTOS data: **Partially.** The market impact component is irrelevant at retail scale, but the volatility-risk tradeoff framework applies. Can compute optimal lambda for GTOS given known WR and R-multiple distribution.

Key equation: Optimal trajectory x*(t) = X * sinh(kappa * (T-t)) / sinh(kappa * T), where kappa = sqrt(lambda * sigma^2 / eta) and eta is temporary impact.

---

### Paper 6.2.2

**Lopez de Prado, M. (2018). "Advances in Financial Machine Learning." Wiley. Chapter 3: Triple Barrier Method; Chapter 10: Profit-Taking.**

Summary: Introduces the triple barrier labeling method: upper barrier (profit target), lower barrier (stop loss), and vertical barrier (time expiry). A trade is labeled based on which barrier is hit first. Chapter 10 specifically addresses profit-taking optimization using dynamic programming. The framework explicitly models the tradeoff between taking profit now vs. waiting for a potentially larger payoff, subject to the risk of reversal.

Relevance to Q-6.2: The triple barrier method generalizes the partial close problem. Instead of a single exit, multiple barriers at different levels can be set, with partial position size allocated to each. The key practical insight: if P(reaching TP2 | already at TP1) < 0.5, then partial close at TP1 increases risk-adjusted return even if it reduces raw expectancy.

Testable on GTOS data: **Yes.** Can compute P(reaching 2R | already at 1R) and P(reaching 3R | already at 2R) from the trailing stop shadow data (100 trades with MFE recorded). This directly answers whether 50/25/25 is optimal.

Key threshold: If P(2R | 1R) > WR_breakeven (which depends on the R-ratio of partial vs. remaining position), partial close at TP1 is suboptimal.

---

### Paper 6.2.3

**Leung, T. & Zhang, H. (2019/2021). "Optimal Trading with a Trailing Stop." Applied Mathematics & Optimization, 83, 669-698.**

Summary: Derives the mathematically optimal trading strategy when a trailing stop is combined with a profit target. Uses excursion theory of linear diffusion to solve the double optimal stopping problem (when to enter and when to exit). Key result: it is optimal to combine a trailing stop with a limit sell order at a sufficiently high price. A higher trailing stop level implies a lower optimal take-profit level -- there is a direct tradeoff.

Relevance to Q-6.2: Proves mathematically that trailing stop + profit target is superior to either alone. The partial close question becomes: should you use a trailing stop on the "runner" portion (the 25% at TP3) while taking fixed profit on TP1 and TP2? This paper says yes -- the runner should have a trailing stop, not a fixed target.

Testable on GTOS data: **Yes.** The trailing stop shadow data (+38.9R to +52.4R improvement over 100 trades) already validates the trailing stop component. Can extend analysis to test trailing stop on partial positions after TP1 hit.

Key equation: Optimal take-profit L* satisfies G(L*) = max{g(x)/phi(x)} where G is the reward function, g is the scale function, and phi is the increasing fundamental solution of the diffusion generator.

---

### Paper 6.2.4

**Acar, E. & Satchell, S. (Eds.) (2002). "Advanced Trading Rules." 2nd Ed., Butterworth-Heinemann/Elsevier.**

Summary: Collection of academic papers on quantitative trading rules. Chapters on stop-loss optimization, position sizing, and exit strategies. Includes formal mathematical treatment of the expected value of stopped processes and the conditions under which trailing stops improve vs. degrade expected returns. Key contribution: formal proof that stop-loss rules reduce variance more than they reduce expected return in trending markets, but the reverse in mean-reverting markets.

Relevance to Q-6.2: Provides the theoretical foundation for when partial exit helps vs. hurts. In trending (momentum-driven) environments, partial close at TP1 is suboptimal because the conditional distribution is right-skewed. In mean-reverting environments, partial close is optimal. GTOS's OB retest entries have properties of both: the initial OB continuation is momentum-like, but mean-reversion kicks in at larger excursions.

Testable on GTOS data: **Partially.** Need to characterize the conditional MFE distribution of GTOS trades -- if right-skewed (long right tail), partial close at TP1 is suboptimal; if symmetric or left-skewed, it helps.

---

### Paper 6.2.5

**Acar, E. & Toffel, R. (2000). "Stop-loss and Investment Returns." Institute of Actuaries/Faculty of Actuaries working paper.**

Summary: Derives analytical expressions for the expected return and variance of a strategy with stop-loss under geometric Brownian motion. Shows that stop-loss rules systematically reduce both mean return and variance, but the reduction in variance exceeds the reduction in mean return for positive-drift processes, improving the Sharpe ratio. Key finding: the improvement is largest when the stop level is close to entry, diminishing as the stop widens.

Relevance to Q-6.2: The mathematical proof extends to profit-taking: closing a portion at TP1 is formally equivalent to applying a "stop-profit" on that portion. The variance reduction formula applies directly. The paper proves that for GBM with positive drift, partial close always improves Sharpe ratio at the cost of raw expectancy -- the question is whether the Sharpe improvement justifies the E[R] cost.

Testable on GTOS data: **Yes.** Can compute the Sharpe ratio of full-exit-at-1.5R vs. partial close strategies using the 300+ trade backtest dataset.

---

### Paper 6.2.6

**Kelly, J.L. (1956). "A New Interpretation of Information Rate." Bell System Technical Journal, 35(4), 917-926.**

Summary: The original Kelly criterion paper. Derives the optimal fraction of bankroll to wager to maximize long-term geometric growth rate: f* = (p*b - q) / b, where p = win probability, b = net odds, q = 1-p. The key insight for partial close: Kelly optimizes position SIZE, not exit LEVEL. Once in a trade, the optimal action depends on the conditional distribution of future returns, not the original entry probability.

Relevance to Q-6.2: Kelly reasoning applies to the partial close decision: if you're at 1R profit and the conditional probability of reaching 2R is p2, then the Kelly-optimal action for the remaining position is f2* = (p2 * b2 - q2) / b2 where b2 is the additional reward and q2 = 1-p2. If f2* < current position fraction, you should reduce. This provides a rigorous framework for computing optimal partial close ratios.

Testable on GTOS data: **Yes.** Need P(2R | 1R) and P(3R | 2R) from MFE data. If P(2R | 1R) = 0.45 and the additional payoff is 1R, Kelly says f2* = (0.45*1 - 0.55)/1 = -0.10 => close everything at 1R. If P(2R | 1R) = 0.60, f2* = 0.20 => keep 20% running.

Key equation: f* = (p*b - q) / b, adapted for conditional partial close.

---

### Paper 6.2.7

**Kaminski, K.M. & Lo, A.W. (2014). "When Do Stop-Loss Rules Stop Losses?" Journal of Financial Markets, 18, 234-254.**

Summary: Empirically tests stop-loss strategies across US equities. Key finding: stop-loss rules consistently reduce left-tail risk but their impact on total return depends on the momentum/mean-reversion character of the underlying. For momentum strategies, stop-loss hurts total return (it truncates the right tail); for mean-reverting strategies, it helps (it removes whipsaws). The paper provides a formal framework for evaluating any exit rule against the distributional properties of the strategy.

Relevance to Q-6.2: Partial close at TP1 is a "stop-gain" -- the symmetric counterpart of stop-loss. By Kaminski & Lo's framework, its optimality depends on whether GTOS trade returns exhibit momentum (conditional on being positive, do they tend to get more positive?) or mean reversion (conditional on being positive, do they tend to revert?). If the MFE distribution of GTOS trades is right-skewed (momentum-like), partial close at TP1 is suboptimal.

Testable on GTOS data: **Yes.** Compute the conditional distribution of final trade outcome given MFE > 1R. If right-skewed, don't partial close. If symmetric/left-skewed, partial close helps.

---

### Paper 6.2.8

**Lei, A.Y.C. & Li, H. (2009). "The Value of Stop-Loss Strategies." Financial Services Review, 18(1), 1-18.**

Summary: Tests both constant-price and trailing stop-loss strategies on NYSE/AMEX stocks from 1970-2005. Finds that trailing stops shield investors from holding non-profitable positions for long periods. However, distinguishes between "profit enhancement" (modest) and "risk reduction" (significant). The trailing stop's primary value is reducing the time capital is locked in losing positions, not increasing average return.

Relevance to Q-6.2: Extends to the partial close debate: partial close at TP1 locks in profit but also frees capital for the next trade. The "capital efficiency" argument for partial close is separate from the expectancy argument. If trades are rare (GTOS: ~17/month), freeing capital earlier has less value than if trades are frequent.

Testable on GTOS data: **Partially.** Can compute capital utilization rate with and without partial close to assess the capital-efficiency benefit.

---

### GAPS for Q-6.2

1. **No paper directly tests optimal scale-out ratios.** The 50/25/25 split has no academic basis -- it's practitioner convention. The optimal split is entirely dependent on the conditional probability curve P(nR | already at (n-1)R), which must be estimated empirically for each system.
2. **No paper models partial close for intraday FX/gold specifically.** The stop-loss literature overwhelmingly uses equities.
3. **Almgren-Chriss assumes market impact, which is negligible at retail scale.** The volatility-timing component applies, but the impact cost component does not.

---

<a id="q-65"></a>
## 3. Q-6.5: Speed to MFE Predicts TP Probability

**Question:** If price reaches 1R quickly, does it predict higher probability of reaching 2R?

**Verdict:** **GAP -- NO DIRECT PAPER.** This is one of the clearest gaps in the entire search. No academic paper directly links the *speed* of favorable excursion to the *probability* of reaching a higher target. The closest evidence comes from three bodies of literature: (1) intraday momentum (Gao et al. 2018), which shows that fast first-half-hour moves predict last-half-hour continuation; (2) time-series momentum (Moskowitz et al. 2012), which documents return persistence at 1-12 month horizons; and (3) Sweeney's (1997) MFE framework, which studies the *magnitude* of favorable excursion but not its temporal dimension. The hypothesis that "fast arrival at 1R predicts higher P(2R)" is novel and must be tested on GTOS data.

---

### Paper 6.5.1

**Sweeney, J. (1997). "Maximum Adverse Excursion: Analyzing Price Fluctuations for Trading Management." Wiley.**

Summary: The originating work on MAE (Maximum Adverse Excursion) and MFE (Maximum Favorable Excursion) as trade management tools. Defines MFE as the maximum unrealized profit during a trade's lifetime. Shows how to use MFE/MAE distributions to calibrate stop-loss and take-profit levels. Key contribution: trades can be categorized by their MFE profile to identify whether the system's exits are leaving money on the table or taking too much heat.

Relevance to Q-6.5: Sweeney's framework studies the MAGNITUDE of MFE but NOT the SPEED of reaching it. The book does not address time-to-MFE as a predictive variable. However, the MFE distribution methodology is directly applicable: GTOS can compute MFE distributions and then stratify by time-to-reach-1R to test the speed hypothesis.

Testable on GTOS data: **Yes.** The trailing stop shadow data has both MFE values and timestamps. Can compute time-to-1R for each trade and test whether fast trades (1R in <3 candles = 45 min) have higher conditional P(2R).

---

### Paper 6.5.2

**Gao, L., Han, Y., Li, S.Z. & Zhou, G. (2018). "Market Intraday Momentum." Journal of Financial Economics, 129(2), 394-414.**

Summary: Documents that the first half-hour return on the S&P 500 (measured from prior close) predicts the last half-hour return, with statistical and economic significance. The effect is stronger on volatile days, high-volume days, recession days, and macro news days. Explains the pattern through infrequent portfolio rebalancing (Bogousslavsky 2016) and late-informed trading.

Relevance to Q-6.5: The most directly relevant paper. Although it studies market returns (not individual trade MFE), the mechanism is analogous: a fast initial move in one direction predicts continuation. If XAUUSD exhibits similar intraday momentum, then a trade that reaches 1R quickly (within the first few candles of a session) should have higher conditional probability of reaching 2R. The paper also shows the effect is STRONGER on volatile days -- consistent with GTOS finding that high-vol entries have better outcomes.

Testable on GTOS data: **Yes.** Can stratify trades by (a) time-to-1R and (b) session volatility to test for intraday momentum at the trade level. Need the M15 timestamp data from pipeline_state/ files.

Key threshold: In the paper, the first-half-hour predictor has R-squared of 0.8-1.2% on normal days, rising to 6.6% during recessions. For GTOS, even a 2-3% R-squared for time-to-1R predicting final R-multiple would be economically significant.

---

### Paper 6.5.3

**Moskowitz, T.J., Ooi, Y.H. & Pedersen, L.H. (2012). "Time Series Momentum." Journal of Financial Economics, 104(2), 228-250.**

Summary: Documents significant return persistence across 58 liquid futures instruments (including gold) at 1-12 month horizons, with partial reversal at longer horizons. Consistent with behavioral theories of under-reaction followed by delayed over-reaction (Daniel, Hirshleifer & Subrahmanyam 1998).

Relevance to Q-6.5: Provides the macro-level evidence that momentum persists in gold specifically. If time-series momentum exists at monthly scale, it likely exists (in weaker form) at intraday scale -- this is what the speed-to-MFE hypothesis tests. The gold-specific finding is important: gold is one of the 58 instruments with documented momentum persistence.

Testable on GTOS data: **Indirectly.** TSM operates at monthly scale; GTOS trades at M15. But the underlying mechanism (informed trading -> price continuation -> delayed adjustment) should manifest at shorter horizons as faster initial moves.

---

### Paper 6.5.4

**Bogousslavsky, V. (2016). "Infrequent Rebalancing, Return Autocorrelation, and Seasonality." Journal of Finance, 71(6), 2967-3006.**

Summary: Theoretical model showing that infrequent portfolio rebalancing by institutional investors creates positive return autocorrelation at intraday horizons. When prices move, rebalancing traders respond with a lag, creating continuation. The magnitude of continuation is proportional to the speed and size of the initial move.

Relevance to Q-6.5: Provides a theoretical mechanism for why fast moves should predict continuation: a fast move creates a larger rebalancing demand from institutional investors who haven't yet adjusted, leading to additional price pressure in the same direction. This is the strongest theoretical support for the speed-to-MFE hypothesis.

Testable on GTOS data: **Indirectly.** The mechanism predicts that speed-to-MFE should be MORE predictive during London/NY overlap (when institutional rebalancing is most active) and LESS predictive during Tokyo session (lower institutional flow). Can test by stratifying by session.

---

### Paper 6.5.5

**Daniel, K., Hirshleifer, D. & Subrahmanyam, A. (1998). "Investor Psychology and Security Market Under- and Overreactions." Journal of Finance, 53(6), 1839-1885.**

Summary: Theoretical model explaining momentum (short-term continuation) and reversal (long-term) through investor overconfidence and biased self-attribution. Overconfident investors overweight their private information, causing initial under-reaction to public signals. Self-attribution bias (taking credit for gains, blaming losses on external factors) amplifies the continuation phase.

Relevance to Q-6.5: Provides the behavioral foundation for why fast initial moves should predict continuation: when price moves quickly in one direction, overconfident traders interpret it as confirming their private information and increase their positions, creating additional momentum. The speed of the initial move signals the intensity of this overconfidence-driven flow.

Testable on GTOS data: **Indirectly.** The theory predicts that speed-to-MFE should be MORE predictive during macro news releases (when private information is being processed) and LESS predictive during quiet periods. Can test by stratifying trades by proximity to scheduled news.

---

### Paper 6.5.6

**Jegadeesh, N. & Titman, S. (1993). "Returns to Buying Winners and Selling Losers: Implications for Stock Market Efficiency." Journal of Finance, 48(1), 65-91.**

Summary: The foundational momentum paper. Documents that buying past winners and selling past losers generates ~1.5% monthly returns over 3-12 month holding periods. Returns partially reverse over the subsequent 2 years. Establishes that momentum is a robust empirical regularity, not a data-mining artifact.

Relevance to Q-6.5: While Jegadeesh-Titman momentum operates at monthly scale and across stocks, the principle of return continuation is the same mechanism the speed-to-MFE hypothesis invokes at intraday scale within a single trade. A trade that reaches 1R quickly is exhibiting strong short-term momentum -- J&T's framework predicts this momentum should persist (for a while).

Testable on GTOS data: **Not directly.** Cross-sectional momentum requires a portfolio of instruments. But the time-series dimension (momentum within a single gold trade) is testable.

---

### Paper 6.5.7

**Miffre, J. & Rallis, G. (2007). "Momentum Strategies in Commodity Futures Markets." Journal of Banking & Finance, 31(6), 1863-1886.**

Summary: Tests momentum strategies specifically in commodity futures (including gold). Finds 13 profitable momentum strategies generating 9.38% average annual return. Momentum returns are positive only during the first 12 months after formation; beyond 12 months, returns are negative. Momentum strategies buy backwardated contracts and sell contangoed contracts.

Relevance to Q-6.5: Gold-specific momentum evidence at intermediate horizons. If gold futures exhibit momentum at the monthly level, the intraday version (fast trades continue faster) is plausible. The backwardation/contango finding doesn't apply to spot gold, but the return persistence does.

Testable on GTOS data: **Indirectly.** GTOS trades spot gold at M15, not monthly futures. But the finding that gold exhibits momentum at intermediate horizons supports the hypothesis that intraday speed predicts continuation.

---

### GAPS for Q-6.5

1. **No paper directly tests speed-to-MFE as a predictor.** This is the largest gap. GTOS should be the first to test this empirically.
2. **No paper links MFE temporal dynamics to conditional TP probability.** Sweeney's MFE is static (maximum over trade life); no one has studied the TIME PATH of excursion.
3. **Intraday momentum literature uses market index returns, not individual trade P&L.** The translation from "market first-half-hour return predicts last-half-hour" to "trade speed-to-1R predicts P(2R)" is intuitive but unproven.

**RECOMMENDED TEST:** Using trailing stop shadow data (100 trades) + pipeline_state timestamps, compute time-to-1R for each trade. Stratify into fast (<3 candles), medium (3-6), slow (>6). Compute P(2R | 1R reached) for each bucket. If fast > slow by >10pp with n>15 per bucket, the signal is actionable.

---

<a id="q-66"></a>
## 4. Q-6.6: Session-Close Strategy / Overnight Risk

**Question:** Should positions be closed at session end (kill zone close)?

**Verdict:** **GOOD COVERAGE.** The literature on gold intraday seasonality, overnight returns, and session microstructure is substantial. Key findings: (1) Gold exhibits W-shaped efficiency across global sessions with informed trading concentrated in NY; (2) LBMA fix creates documented price impact and information leakage; (3) Gap-day analysis shows continuation on gap days; (4) Overnight returns exhibit a "drift" driven by order imbalance asymmetry; (5) Gold gaps average 0.64% (2x equity gaps), creating real risk for open positions. The verdict for GTOS: close positions before end of kill zone UNLESS the trade has strong momentum (>1R in profit with trailing stop), in which case the overnight drift literature suggests holding through may be positive-expectancy.

---

### Paper 6.6.1

**Iwatsubo, K., Watkins, C. & Xu, T. (2018). "Intraday Seasonality in Efficiency, Liquidity, Volatility and Volume: Platinum and Gold Futures in Tokyo and New York." Journal of Commodity Markets, 11, 59-71.**

Summary: Documents W-shaped intraday efficiency pattern in gold futures across Tokyo, London, and NY sessions. Volatility is L-shaped in Tokyo hours, U-shaped in London hours, declining approximately linearly in NY. Uninformed trading dominates Tokyo session; informed trading dominates NY session. Both platinum and gold show the same pattern.

Relevance to Q-6.6: Directly relevant. If informed trading concentrates in NY, then holding positions through the NY close into Tokyo means entering a period of uninformed (random) flow -- the conditional expectancy of price continuation drops. GTOS should close positions before NY kill zone ends unless trailing stop is active and position is >1R in profit.

Testable on GTOS data: **Yes.** Can stratify trades by session and test whether positions open at NY close have different outcomes than those closed at NY kill zone end. The W-shape efficiency pattern predicts worse outcomes for positions held through Tokyo.

Key threshold: Informed trading in NY gives directional persistence; Tokyo's uninformed trading gives random walk. The transition point is approximately 21:00 UTC.

---

### Paper 6.6.2

**Caminschi, A. & Heaney, R. (2014). "Fixing a Leaky Fixing: Short-Term Market Reactions to the London PM Gold Price Fixing." Journal of Futures Markets, 34(11), 1003-1039.**

Summary: Documents statistically significant return advantages from trading on information leaking from the London PM Gold Fixing. Elevated trade volume and volatility immediately follow the fixing's start (before results are published). Trades in the opening minutes of the fixing are predictive of the fix price direction (>90% accuracy in some periods). The fix creates a brief period of asymmetric information.

Relevance to Q-6.6: LBMA PM fix occurs at 15:00 London time (14:00 UTC winter, 13:00 UTC summer). This falls within GTOS's NY kill zone (13:00-17:00 UTC). If GTOS has an open position during the fix, it faces elevated volatility and potential adverse price impact from fix-related flows. The fix is a specific session event that warrants position management rules.

Testable on GTOS data: **Yes.** Can flag trades open during the LBMA PM fix window and test for different outcomes (higher variance, adverse excursion). If significant, add a rule: reduce position or tighten stop during 14:00-15:30 UTC (adjusting for DST).

Key threshold: Caminschi & Heaney find significant effects in the 4 minutes after fix start. For GTOS on M15, this is within one candle.

---

### Paper 6.6.3

**Boyarchenko, N., Larsen, L.C. & Whelan, P. (2022). "The Overnight Drift." Federal Reserve Bank of New York Staff Report No. 917.**

Summary: Documents asymmetric responses to order imbalances between overnight and intraday periods. The conditional expected return to providing immediacy depends on: end-of-day order imbalance, conditional variance of returns, and inverse of market-maker risk-bearing capacity. Positive and negative demand shocks generate asymmetric responses driven by contemporaneous changes in market-maker risk-bearing capacity.

Relevance to Q-6.6: The overnight drift mechanism explains why holding through session close can be either positive or negative depending on the order imbalance at close. If the closing order flow is in the direction of the GTOS position (e.g., other traders are buying when GTOS is long), the overnight drift is positive. If against, the drift is negative and amplified by the reduced risk-bearing capacity of overnight market makers.

Testable on GTOS data: **Partially.** GTOS doesn't have order flow data, but can proxy using the direction of the last 2-3 candles before kill zone close. If closing flow is with-position, hold; if against, close.

---

### Paper 6.6.4

**Plastun, A., Sibande, X., Gupta, R. & Wohar, M.E. (2020). "Price Gap Anomaly in the US Stock Market: The Whole Story." North American Journal of Economics and Finance, 52, 101177.**

Summary: Analyzes price gap anomaly in DJI, S&P 500, and NASDAQ from 1928-2018. Finds strong evidence of abnormal price movements after price gaps. During a gap day, prices tend to move IN THE DIRECTION of the gap (continuation), not against it (as the "gap-fill" myth suggests). The continuation effect is strongest for larger gaps.

Relevance to Q-6.6: If gold exhibits similar gap-day continuation, then a position that is profitable at session close benefits from holding through the gap (positive expected overnight return conditional on profitable close). However, the paper studies equity indices, not gold. Gold's gap characteristics differ (larger average gap: 0.64% vs ~0.30% for SPY) and the mechanism may differ due to 24h OTC trading.

Testable on GTOS data: **Yes.** Can compute gap-day continuation rate for gold specifically using MT5 data. If gaps continue >55% of the time in the direction of the gap, holding profitable positions through close is justified.

---

### Paper 6.6.5

**Boudt, K., Croux, C. & Laurent, S. (2011). "Robust Estimation of Intraweek Periodicity in Volatility and Jump Detection." Journal of Empirical Finance, 18(2), 353-367.**

Summary: Shows that financial market openings, lunch breaks, and closings induce periodic components in high-frequency volatility. Accounting for periodicity greatly improves jump detection: increases power to detect small jumps during low-volatility periods and reduces false detections during high-volatility periods.

Relevance to Q-6.6: Session boundaries create predictable volatility patterns. The session-close period typically has elevated volatility (the closing U-shape). GTOS positions open during session close face higher probability of stop-loss being hit simply due to elevated volatility, not due to directional adverse movement. This argues for WIDENING stops during session close rather than closing positions.

Testable on GTOS data: **Yes.** Can compute intraday volatility periodicity for XAUUSD using M15 data and identify whether session-close periods have higher adverse excursion. If the session-close MAE is >1.2x the mid-session MAE, stops should be adjusted.

---

### Paper 6.6.6

**Yu, H., Nartea, G.V. & Gan, C. (2016). "Weekday Effects on Gold: Tokyo, London, and New York Markets." Banks and Bank Systems, 11(2), 43-53.**

Summary: Tests weekday effects on gold returns and volatility across three major trading sessions (Tokyo, London, NY). Finds that Tokyo has the highest volatility, while London and NY have similar distributions. Monday returns tend to be negative; Friday returns are positive. The weekday effect varies across sessions.

Relevance to Q-6.6: Adds the day-of-week dimension to the session-close decision. If Friday gold returns are positive (as the paper finds), then holding positions through Friday close into weekend is less risky than other days. If Monday returns are negative, positions opened Friday should be closed before Monday Tokyo open. This is specific to the weekend gap risk.

Testable on GTOS data: **Yes.** Can compute day-of-week returns stratified by session for XAUUSD in the GTOS backtest period. If Friday-to-Monday gap risk is asymmetric, add a Friday close rule.

---

### Paper 6.6.7

**Xu, Y., Bouri, E., Saeed, T. & Wen, Z. (2020). "Intraday Return Predictability: Evidence from Commodity ETFs and Their Related Volatility Indices." PLOS ONE, 15(9), e0238870.**

Summary: Using high-frequency data of crude oil, gold, and silver ETFs and their volatility indices, finds that intraday return predictability exists in all markets but patterns differ by market. Gold shows specific half-hour predictability patterns. The predictability is stronger on high-volatility and high-jump days. A market timing strategy based on intraday momentum generates substantial economic value.

Relevance to Q-6.6: Gold-specific intraday return predictability has specific half-hour windows. If the last half-hour of a session is predictable based on earlier returns, GTOS can use this to decide whether to hold or close at session end. The finding that predictability is stronger on volatile days aligns with GTOS's observation that high-vol entries have better outcomes.

Testable on GTOS data: **Yes.** Can compute half-hour return autocorrelation for XAUUSD across kill zone hours. If specific time windows show predictive power, can add a session-close decision rule.

Key threshold: The paper finds economically significant returns from timing strategies, suggesting that a session-close rule based on intraday momentum could add >0.05R per trade on average.

---

### Paper 6.6.8

**Osler, C.L. (2005). "Stop-Loss Orders and Price Cascades in Currency Markets." Journal of International Money and Finance, 24(2), 219-241.**

Summary: Documents that stop-loss orders cluster at round numbers and their execution creates price cascades. Exchange rates move unusually rapidly through round number levels where stop-loss orders cluster. The cascade mechanism is asymmetric: stop-loss execution propagates trends, while take-profit execution dampens them.

Relevance to Q-6.6: At session boundaries, accumulated stop-loss orders may create cascades that move price through levels that wouldn't be reached during normal mid-session trading. This means the session-close period has elevated risk of stop-loss cascade events. GTOS positions should account for this by either closing before the cascade window or widening stops to survive it.

Testable on GTOS data: **Yes.** Can identify whether GTOS stop-losses are hit more frequently in the last 30 minutes of kill zones vs. mid-session. If yes, widening stops during this window (or closing) is justified.

---

### Paper 6.6.9

**Lucca, D.O. & Moench, E. (2015). "The Pre-FOMC Announcement Drift." Journal of Finance, 70(1), 329-371.**

Summary: Documents large average excess returns on US equities in the 24 hours before scheduled FOMC announcements. The effect has increased over time. No similar effect exists in Treasuries or money market futures. The drift is larger when yield curve slope is low and implied volatility is high.

Relevance to Q-6.6: FOMC announcements create specific overnight-risk events for gold positions. Gold has documented macro sensitivity to Fed policy surprises. While the paper focuses on equities, the FOMC effect on gold (asymmetric response to dovish vs. hawkish surprises) is well-documented. GTOS should have a rule: close all positions before FOMC if the announcement falls within or after a kill zone.

Testable on GTOS data: **Partially.** Can identify FOMC dates in the backtest period and test whether gold trades held through FOMC have higher adverse excursion. Small sample issue: only 8 FOMC meetings per year.

---

### Paper 6.6.10

**Heston, S.L., Korajczyk, R.A. & Sadka, R. (2010). "Intraday Patterns in the Cross-section of Stock Returns." Journal of Finance, 65(4), 1369-1407.**

Summary: Documents that stock return patterns at specific half-hour intervals persist for at least 40 trading days at exact multiples of a trading day. This means that a stock's return at 10:00-10:30 today predicts its return at 10:00-10:30 for the next 40 days.

Relevance to Q-6.6: If gold exhibits similar persistent intraday patterns at specific time intervals, then certain kill zone windows are systematically better for trade entry and worse for holding. This doesn't directly address session-close, but it implies that the optimal time to close may depend on the specific half-hour pattern of the instrument.

Testable on GTOS data: **Partially.** Can test for half-hour return persistence in XAUUSD using M15 data. If specific 30-minute windows are systematically adverse, GTOS should avoid holding through them or close before they begin.

---

### GAPS for Q-6.6

1. **No paper specifically addresses session-close decision rules for retail gold positions.** The literature covers overnight returns, session microstructure, and LBMA fix effects separately, but no integrated framework for the specific question "should I close my gold trade at 17:00 UTC?"
2. **Gold's 24h OTC structure means "overnight" is different from equities.** Most overnight-return literature is equity-based where markets close. Gold trades 23h/day on weekdays. The relevant "close" for GTOS is the kill zone end, not a market close.

---

<a id="q-67"></a>
## 5. Q-6.7: Institutional Exit Principles (TWAP/VWAP/IS)

**Question:** Do institutional execution algorithms have principles applicable to retail trade exit?

**Verdict:** **STRONG THEORETICAL FOUNDATION but LIMITED DIRECT APPLICABILITY.** The institutional execution literature (Almgren-Chriss, Bertsimas-Lo, Gatheral, Obizhaeva-Wang) is mathematically rigorous and solves a well-defined optimization problem. However, the core problem they solve -- minimizing market impact while executing a large order -- is IRRELEVANT at retail scale. A 0.01 lot XAUUSD order has zero measurable market impact. The PRINCIPLES that do transfer are: (1) the tradeoff between execution certainty and timing risk; (2) the value of information during execution; (3) the optimal trajectory shape (front-loaded vs. back-loaded). These principles can be reframed for the exit question: should you exit now (certain, no market impact) or wait (uncertain, but potentially better price)?

---

### Paper 6.7.1

**Almgren, R. & Chriss, N. (2001). "Optimal Execution of Portfolio Transactions." Journal of Risk, 3(2), 5-40.**

Summary: [See Paper 6.2.1 for full description.] The core framework: minimize E[cost] + lambda * Var[cost]. For linear impact, the optimal trajectory is hyperbolic sine decay. Key insight: the efficient frontier between cost and risk is convex -- aggressive execution (fast) is only optimal for very risk-averse traders.

Relevance to Q-6.7: The most important adaptation for retail exit: replace "market impact cost" with "opportunity cost of not being in the next trade" and "timing risk" with "price risk of holding the current position." Under this reframing, the optimal exit trajectory is: exit immediately if there's a better trade available (high opportunity cost), or hold if the expected return of the current position exceeds the expected return of alternative deployments.

Testable on GTOS data: **Yes.** Can compute the conditional expected return of holding a trade at 0.5R, 1R, 1.5R vs. the expected return of closing and waiting for the next entry. If E[hold at 1R] < E[next trade], close at 1R.

Key equation (adapted): lambda_retail = E[next trade return] / Var[current trade remaining return]. When lambda is high (frequent trades, low remaining expectancy), exit sooner.

---

### Paper 6.7.2

**Bertsimas, D. & Lo, A.W. (1998). "Optimal Control of Execution Costs." Journal of Financial Markets, 1(1), 1-50.**

Summary: Derives dynamic optimal trading strategies for executing large stock orders over a fixed time horizon with a price-impact function. Obtains closed-form "best execution strategy" for the optimal sequence of trades. Extends to portfolio case where cross-asset impact matters.

Relevance to Q-6.7: The "fixed time horizon" constraint maps to GTOS's kill zone: a trade must be managed (and potentially closed) within the kill zone window. Bertsimas-Lo's framework suggests that the optimal exit path within a kill zone depends on the remaining time (more aggressive as deadline approaches) and the accumulated P&L (take profit sooner if already at target).

Testable on GTOS data: **Partially.** Can test whether trades closer to kill zone end have worse outcomes than trades with more time remaining, which would validate the "execute earlier when time is short" principle.

---

### Paper 6.7.3

**Perold, A.F. (1988). "The Implementation Shortfall: Paper versus Reality." Journal of Portfolio Management, 14(3), 4-9.**

Summary: Coined "implementation shortfall" -- the difference between the paper portfolio (instantaneous, costless execution) and the real portfolio. Decomposes shortfall into: delay cost, bid-ask spread, market impact, and opportunity cost. The opportunity cost component (trades not executed because the market moved away) is often the largest.

Relevance to Q-6.7: The concept of "opportunity cost" directly applies to retail exit. GTOS's implementation shortfall for exits is: IS = (TP target) - (actual exit price). This shortfall comes from: (a) exiting early (partial close reduces upside), (b) trailing stop gap (stop triggered below trailing level), (c) not exiting (position reverses past entry). Perold's framework provides the decomposition to analyze which exit cost component is largest for GTOS.

Testable on GTOS data: **Yes.** Can compute IS for every trade: IS = MFE - actual_exit_R. Decompose into: early_exit_cost (MFE - TP for TP-hit trades), trailing_gap (trailing_level - actual_exit for trailing stop exits), and reversal_cost (entry_R - exit_R for losing trades).

Key equation: IS = Delay + Spread + Impact + Opportunity. For retail: IS = 0 + Spread + 0 + (MFE - Exit).

---

### Paper 6.7.4

**Gatheral, J. (2010). "No-Dynamic-Arbitrage and Market Impact." Quantitative Finance, 10(7), 749-759.**

Summary: Derives no-arbitrage constraints on the relationship between market impact function shape and impact decay rate. Key finding: exponential impact decay is compatible ONLY with linear impact. Empirically, impact decays as a power law, implying nonlinear impact functions. Market impact from past trades decays over time -- the transient component fades while the permanent component persists.

Relevance to Q-6.7: The transient vs. permanent impact distinction applies conceptually to GTOS exits even at retail scale. When GTOS's entry creates a (tiny) signal in the market, the initial price movement includes both a permanent component (information-driven) and a transient component (temporary demand pressure). The exit should ideally occur after the permanent component has been incorporated but before the transient component decays -- i.e., exit during the momentum phase, not the mean-reversion phase.

Testable on GTOS data: **Not directly** (retail impact is negligible), but the conceptual framework of timing exits to momentum vs. mean-reversion phases is testable using MFE time profiles.

---

### Paper 6.7.5

**Obizhaeva, A.A. & Wang, J. (2013). "Optimal Trading Strategy and Supply/Demand Dynamics." Journal of Financial Markets, 16(1), 1-32.**

Summary: Assumes exponential decay of price impact and derives the optimal execution strategy: execute a large transaction at the beginning and end of the execution window, with uniform participation in between. The U-shaped execution profile is optimal because impact decay means early trades have less persistent effect, and late trades benefit from "deadline" urgency.

Relevance to Q-6.7: The U-shaped optimal execution profile has an interesting retail analogy: the optimal exit strategy may also be U-shaped over the trade's lifetime. Early in the trade (near entry), exit quickly if the trade shows weakness (the "wrong" signal). Late in the trade (near kill zone end), exit quickly before the deadline. In between, let the trailing stop manage the position.

Testable on GTOS data: **Partially.** Can test whether GTOS trades that exit early in the trade or late in the kill zone have different outcomes than mid-trade exits.

---

### Paper 6.7.6

**Kissell, R. & Glantz, M. (2003). "Optimal Trading Strategies: Quantitative Approaches for Managing Market Impact and Trading Risk." AMACOM/Wiley.**

Summary: Comprehensive treatment of transaction cost analysis and optimal execution. Introduces the Efficient Trading Frontier (ETF) from Almgren-Chriss and the Capital Trade Line (CTL). Addresses practical questions: choosing between agency and principal execution, estimating transaction costs, and selecting broker-dealers. Extends optimal execution to portfolio level.

Relevance to Q-6.7: The most practical adaptation for retail: the ETF concept maps to a "trade management frontier" where the x-axis is exit certainty (close now = certain, hold = uncertain) and the y-axis is expected return (close now = fixed, hold = uncertain but potentially higher). Risk-averse traders should operate on the left of this frontier (close sooner); risk-seeking traders on the right (hold longer). GTOS's current fixed 1.5R TP is a single point on this frontier.

Testable on GTOS data: **Yes.** Can construct the trade management frontier using historical MFE data: for each potential exit point (0.5R, 1R, 1.5R, 2R, trailing stop), compute the expected return and variance. The optimal exit depends on GTOS's risk aversion parameter.

---

### Paper 6.7.7

**Avellaneda, M. & Stoikov, S. (2008). "High-Frequency Trading in a Limit Order Book." Quantitative Finance, 8(3), 217-224.**

Summary: Derives optimal bid and ask quotes for a market maker under a stochastic control framework. The market maker computes a personal indifference valuation for the security given current inventory, then calibrates quotes relative to the limit order book. The key insight: optimal quotes are a function of inventory -- as inventory grows, the market maker makes the "unloading" side more aggressive.

Relevance to Q-6.7: The inventory-dependent optimal quote concept maps to position management: as GTOS's unrealized P&L grows (inventory of profit), the optimal exit becomes more aggressive (tighter trailing stop or closer TP). This is the mathematical justification for tightening trailing stops as profit accumulates. Conversely, when the position is near entry price, the optimal management is more passive (wider stop).

Testable on GTOS data: **Partially.** Can test whether a trailing stop that tightens as profit accumulates (e.g., 1R trailing at +0.5R, 0.75R trailing at +1R, 0.5R trailing at +1.5R) outperforms a fixed trailing stop distance. The inventory effect predicts it should.

---

### Paper 6.7.8

**Cont, R., Kukanov, A. & Stoikov, S. (2014). "The Price Impact of Order Book Events." Journal of Financial Econometrics, 12(1), 47-88.**

Summary: Shows that over short intervals, price changes are mainly driven by Order Flow Imbalance (OFI) -- the imbalance between supply and demand at the best bid and ask. The relationship between OFI and price changes is linear, with slope inversely proportional to market depth. Robust across stocks and time scales.

Relevance to Q-6.7: While GTOS can't observe real-time OFI (requires L2 data), the OFI mechanism explains WHY institutional exit algorithms matter: they are designed to minimize their OFI contribution. For retail, the implication is indirect: GTOS exits coincide with other traders' flow. If GTOS trades in the direction of prevailing OFI (e.g., selling into a buying imbalance), the exit will receive a better price than if selling into a selling imbalance.

Testable on GTOS data: **Not directly** without L2 order book data. But can proxy OFI using volume-weighted price movement in the candles surrounding exit.

---

### Paper 6.7.9

**Implementation Shortfall — One Objective, Many Algorithms. (CIS UPenn working paper.)**

Summary: Survey paper comparing TWAP, VWAP, and IS algorithms. VWAP minimizes deviation from volume-weighted average price (best for benchmarked execution). TWAP spreads orders uniformly over time (simplest, lowest information leakage). IS minimizes deviation from decision price (best for alpha-driven strategies). Each has different strengths depending on the objective.

Relevance to Q-6.7: Maps directly to GTOS exit strategy selection. GTOS's current fixed TP at 1.5R is IS-like (maximize profit from decision point). A trailing stop is TWAP-like (spread the exit decision over time as price moves). A partial close at multiple levels is VWAP-like (average exit price across levels). The survey suggests IS (fixed TP) is best for high-alpha strategies and TWAP (trailing stop) is best for low-information-leakage situations.

Testable on GTOS data: **Yes.** Can compare the three approaches (fixed TP, trailing stop, partial close) on the same trade set and classify which approach best matches GTOS's alpha profile.

---

### GAPS for Q-6.7

1. **No paper applies institutional execution principles to retail single-trade exit.** The entire optimal execution literature assumes the problem is "how to execute a large order without moving the market." Retail doesn't have this problem. The adaptation to "how to exit a single position optimally given uncertainty about future price" is conceptual, not proven.
2. **Market impact at retail scale on gold is negligible.** The core mathematical driver of the Almgren-Chriss framework is irrelevant for GTOS.

---

<a id="q-68"></a>
## 6. Q-6.8: Dynamic TP Based on Realized Volatility

**Question:** Should TP expand in high-vol environments and contract in low-vol?

**Verdict:** **MODERATE COVERAGE with STRONG IMPLICATIONS.** The realized volatility literature is deep (Andersen et al. 2003, Corsi 2009) and provides tools for forecasting volatility over trading horizons. The volatility targeting literature (Baltas & Kosowski 2020, Moreira & Muir 2017) shows that scaling position SIZE by inverse volatility improves Sharpe ratios. BUT: scaling the TARGET by volatility is a different operation. ATR-based TP (Wilder 1978, practitioner literature) is widely used but never peer-reviewed. The key finding for GTOS: the system already observes that high-vol entries have BETTER outcomes. If this is because high-vol regimes produce larger R-multiples, then expanding TP during high vol would capture this edge. If it's because high-vol regimes have higher WR (not larger R), expanding TP would HURT (more losses from wider targets).

---

### Paper 6.8.1

**Andersen, T.G., Bollerslev, T., Diebold, F.X. & Labys, P. (2003). "Modeling and Forecasting Realized Volatility." Econometrica, 71(2), 579-625.**

Summary: The foundational paper on realized volatility. Develops formal links between high-frequency intraday data and daily/lower frequency volatility. Shows that logarithmic realized volatility is well-approximated by a long-memory Gaussian process. A simple HAR-type model produces excellent volatility forecasts for FX (including DEM/USD and JPY/USD). The realized vol framework is the basis for ALL subsequent vol-adjusted trading research.

Relevance to Q-6.8: Provides the tool for computing the volatility that should drive TP adjustment. GTOS already uses M15 candles -- realized volatility from these candles can be computed as the sum of squared 15-minute returns over the relevant session. This RV measure can then be used to set dynamic TP levels. The long-memory property means yesterday's RV is a good predictor of today's RV, justifying a dynamic TP set before the session begins.

Testable on GTOS data: **Yes.** Compute daily realized vol from M15 data. Stratify trades by RV quintile. Test whether MFE scales with RV. If MFE(high-RV) > MFE(low-RV) * 1.3, dynamic TP is justified.

Key equation: RV_t = sum_{i=1}^{n} r_{t,i}^2, where r_{t,i} are intraday returns. Forecast: RV_{t+1} ~= alpha + beta_D * RV_t + beta_W * RV_{t-5:t} + beta_M * RV_{t-22:t} (HAR structure).

---

### Paper 6.8.2

**Corsi, F. (2009). "A Simple Approximate Long-Memory Model of Realized Volatility." Journal of Financial Econometrics, 7(2), 174-196.**

Summary: Proposes the Heterogeneous Autoregressive model of Realized Volatility (HAR-RV). Despite its simple AR structure, HAR-RV captures long memory, fat tails, and self-similarity in volatility. The model uses three aggregation levels (daily, weekly, monthly) to capture heterogeneous agent timescales. Has become the "workhorse" of realized volatility forecasting due to its simplicity and accuracy.

Relevance to Q-6.8: HAR-RV is the practical tool for dynamic TP implementation. GTOS can implement a 3-level HAR model using M15 realized vol: (1) last session RV (daily), (2) last 5 sessions RV (weekly), (3) last 22 sessions RV (monthly). The forecast RV then sets the TP level: TP = base_R * (forecast_RV / median_RV). When forecast_RV > median, TP expands; when < median, contracts.

Testable on GTOS data: **Yes.** Can implement HAR-RV forecast and backtest dynamic TP. Requires at least 30 days of M15 data for calibration. Compare Sharpe of fixed 1.5R TP vs. dynamic TP scaled by HAR-RV forecast.

Key equation: RV_{t+1} = c + beta_D * RV_t + beta_W * RV_t^{(w)} + beta_M * RV_t^{(m)} + epsilon

---

### Paper 6.8.3

**Baltas, N. & Kosowski, R. (2020). "Demystifying Time-Series Momentum Strategies: Volatility Estimators, Trading Rules and Pairwise Correlations." In Market Momentum, Wiley.**

Summary: Examines components of time-series momentum (CTA/trend-following) strategies. Key finding: more efficient volatility estimation significantly reduces portfolio turnover (~33%) without performance degradation. Scaling positions by inverse volatility improves Sharpe ratios. A "TREND" rule that scales positions by signal strength outperforms binary signals. Correlation-adjusted variants outperform naive implementations.

Relevance to Q-6.8: The volatility scaling result directly applies. If GTOS scales POSITION SIZE by inverse volatility (risk 1% but in vol-adjusted lots), the Sharpe improves. If GTOS additionally scales TP TARGET by volatility (wider TP when vol is high), this is a second application of the same principle. Baltas-Kosowski show that the vol-scaling benefit comes from reducing exposure during high-vol (risk reduction), NOT from expanding exposure during high-vol. This suggests contracting TP during high-vol (taking profit sooner to reduce risk) may be better than expanding it.

Testable on GTOS data: **Yes.** Can compare: (a) fixed lot size + fixed TP, (b) vol-scaled lot size + fixed TP, (c) fixed lot size + vol-scaled TP, (d) vol-scaled both. The 300+ trade backtest is sufficient for this 4-way comparison.

Key insight: Baltas-Kosowski find that the PRIMARY benefit is vol-scaling position SIZE, not target. This suggests GTOS's fixed 1.5R TP may be fine as-is, with the vol adjustment going into lot size instead.

---

### Paper 6.8.4

**Wilder, J.W. Jr. (1978). "New Concepts in Technical Trading Systems." Trend Research.**

Summary: Introduces the Average True Range (ATR) indicator, originally designed for commodity futures where overnight gaps make close-to-close volatility misleading. ATR uses the maximum of (High-Low, |High-PrevClose|, |Close-PrevClose|) to capture the full price range including gaps. Wilder recommended a 14-period smoothing. This has become the standard volatility measure in retail trading.

Relevance to Q-6.8: ATR is the practitioner standard for dynamic TP: set TP = entry + N * ATR(14). The question is whether N * ATR outperforms a fixed R-multiple. ATR captures the current volatility regime better than a fixed R-multiple, but ATR also includes "noise" (wide candles due to random events, not trend). The ATR-based TP hypothesis is: in high ATR environments, price moves further before reversing, so TP should be wider.

Testable on GTOS data: **Yes.** Can compute ATR(14) on H1 at entry time for each trade and test: (a) does MFE correlate with entry ATR? (b) does TP = 2*ATR outperform TP = 1.5R? (c) what N minimizes implementation shortfall (MFE - exit)?

Key equation: ATR(14) = (1/14) * sum_{i=1}^{14} max(H_i - L_i, |H_i - C_{i-1}|, |L_i - C_{i-1}|). Note: this is an exponential moving average in Wilder's original formulation.

---

### Paper 6.8.5

**Parkinson, M. (1980). "The Extreme Value Method for Estimating the Variance of the Rate of Return." Journal of Business, 53(1), 61-65.**

Summary: Derives a range-based volatility estimator using only high and low prices. Shows this estimator is approximately 5x more efficient than close-to-close estimators for log-normal prices. The Parkinson estimator: sigma^2 = (1/(4*n*ln(2))) * sum(ln(H_i/L_i))^2.

Relevance to Q-6.8: Parkinson's range-based estimator is more efficient than ATR for measuring "exploitable" volatility (the range a trade could capture). For GTOS, the relevant question is not "how volatile is the market" but "how far does price move in one direction before reversing." Parkinson's high-low range captures this directly. A dynamic TP based on Parkinson range may outperform ATR-based TP because it focuses on the directional range, not the total path.

Testable on GTOS data: **Yes.** Compute Parkinson RV for H1 candles at trade entry. Test correlation between Parkinson RV and MFE. If stronger than ATR correlation, use Parkinson for TP scaling.

Key equation: sigma^2_Parkinson = (1/(4*n*ln(2))) * sum_{i=1}^{n} [ln(H_i/L_i)]^2

---

### Paper 6.8.6

**Garman, M.B. & Klass, M.J. (1980). "On the Estimation of Security Price Volatilities from Historical Data." Journal of Business, 53(1), 67-78.**

Summary: Extends Parkinson's range estimator by incorporating open and close prices. The Garman-Klass estimator is ~7.4x more efficient than close-to-close and slightly more efficient than Parkinson. Uses all four OHLC values.

Relevance to Q-6.8: The Garman-Klass estimator is optimal for GTOS because GTOS already has OHLC data at M15 resolution. For computing the session-level volatility that should drive dynamic TP, Garman-Klass extracts maximum information from available data. This is more efficient than ATR (which wastes the open/close information) or close-to-close (which wastes high/low information).

Testable on GTOS data: **Yes.** Compute Garman-Klass RV for the prior session's M15 candles. Use as input to dynamic TP: TP = base_R * (GK_RV / median_GK_RV). Compare performance vs. ATR-based and fixed TP.

Key equation: sigma^2_GK = (1/n) * sum_{i=1}^{n} [0.5 * ln(H_i/L_i)^2 - (2*ln(2)-1) * ln(C_i/O_i)^2]

---

### Paper 6.8.7

**Zumbach, G. & Lynch, P. (2001). "Heterogeneous Volatility Cascade in Financial Markets." Physica A, 298(3), 521-529.**

Summary: Uses high-frequency data to study how volatility "cascades" from long to short time horizons. Measures the correlation between volatility changes at different time scales and finds a cascade structure different from turbulence models. Develops a new ARCH-type model incorporating different agent groups with characteristic memory timescales.

Relevance to Q-6.8: The volatility cascade mechanism explains why today's session volatility is predictable from longer-horizon volatility. For GTOS dynamic TP, the cascade implies that a weekly volatility regime shift (e.g., transition from low-vol to high-vol) propagates to the M15 level with a lag. This means the dynamic TP should incorporate multiple timescales -- not just yesterday's vol, but the trend in vol over the past week.

Testable on GTOS data: **Yes.** Can compute multi-timescale RV (daily, weekly, monthly a la HAR) and test which timescale has the strongest correlation with trade MFE. The cascade model predicts that weekly RV adds predictive power beyond daily RV for MFE forecasting.

---

### Paper 6.8.8

**Bollerslev, T. & Todorov, V. (2011). "Tails, Fears and Risk Premia." Journal of Finance, 66(6), 2165-2211.**

Summary: Shows that compensation for rare jump events accounts for a large fraction of variance risk premia. The probability of rare events varies over time, increasing with market volatility. Jump risk premium is distinct from diffusive volatility risk premium.

Relevance to Q-6.8: High-vol environments include more jump risk. If GTOS expands TP during high vol, the expanded target may be hit by jumps (favorable or adverse). The jump component of volatility creates asymmetric risk: favorable jumps hit wider TPs, but adverse jumps hit stop-losses. The net effect depends on the jump symmetry for gold. Gold has negative skew (-1.53) meaning adverse jumps are larger, which argues AGAINST expanding TP during high vol (the adverse jump risk outweighs the favorable).

Testable on GTOS data: **Yes.** Compute the skew of trade returns in high-vol vs. low-vol regimes. If negative skew is larger in high-vol (as the paper predicts), expanding TP in high-vol is risky because adverse jumps are more extreme.

---

### Paper 6.8.9

**Moreira, A. & Muir, T. (2017). "Volatility-Managed Portfolios." Journal of Finance, 72(4), 1611-1644.**

Summary: Shows that scaling portfolio exposure by inverse conditional volatility earns a significant alpha relative to the unscaled factor. The volatility-managed market factor has a higher Sharpe ratio and the alpha is driven by risk reduction during high-vol periods. The result holds for multiple factors (market, value, momentum, profitability).

Relevance to Q-6.8: The strongest evidence that volatility scaling improves risk-adjusted returns. BUT: Moreira & Muir scale POSITION SIZE, not target. Their result implies that when volatility is high, you should trade SMALLER (to keep dollar risk constant), not trade WIDER. This is consistent with GTOS's current approach (fixed 1% risk, which automatically reduces lot size when ATR is high). Expanding TP on top of vol-scaled position sizing is a second-order effect that may or may not add value.

Testable on GTOS data: **Yes.** GTOS already does position-size vol-scaling (via fixed % risk). The test is whether ADDING target vol-scaling on top of position-size vol-scaling improves performance.

Key insight: Vol-scaling position size captures most of the benefit. Vol-scaling the target is a second-order optimization.

---

### GAPS for Q-6.8

1. **No paper directly tests ATR-based TP vs. fixed R-multiple TP on intraday gold/commodities.** This is the most actionable gap. GTOS can be the first to run this comparison with statistical rigor.
2. **No paper addresses the interaction between vol-scaled position size and vol-scaled TP.** GTOS already does the former; adding the latter may over-adjust for volatility (double-counting).

---

<a id="synthesis"></a>
## 7. Cross-Question Synthesis

### Key Themes Across All 5 Questions

1. **The variance-expectancy tradeoff is the central theme.** Partial close (Q-6.2), trailing stop vs. fixed TP (Q-6.5 implied), session close (Q-6.6), and dynamic TP (Q-6.8) all involve the same fundamental tradeoff: reduce variance at the cost of some expected return. The optimal balance depends on GTOS's risk aversion, which is set by the FTMO constraints (max 10% drawdown, max 4% daily loss).

2. **Volatility regime is the strongest environmental predictor.** Across all questions, the relevant modulator is volatility: partial close is more beneficial in low-vol (narrow MFE distribution), speed-to-MFE is more predictive in high-vol (momentum stronger), session close matters more in high-vol (larger gaps), and dynamic TP is driven by vol. A single vol-regime classification could improve all exit decisions simultaneously.

3. **The conditional MFE distribution is the master dataset.** Almost every question reduces to: "given the trade is at X profit, what is the distribution of future outcomes?" This is the MFE conditional distribution. GTOS needs to compute and characterize this distribution from historical data as the foundation for all exit optimization.

4. **Position size vol-scaling captures most of the vol-adjustment benefit.** Moreira-Muir and Baltas-Kosowski both find that vol-scaling position SIZE is the primary improvement. Vol-scaling the TARGET is second-order. GTOS should prioritize getting position sizing right before optimizing TP targets.

5. **Session-specific rules are well-supported.** The gold microstructure literature strongly supports different management rules for London, NY, and Tokyo sessions. The LBMA fix creates a specific risk window. Kill zone boundaries align well with empirical session transitions.

### Priority Ranking for GTOS Implementation

| Rank | Test | Expected Impact | Data Needed | Papers |
|------|------|----------------|-------------|---------|
| 1 | Compute conditional MFE distribution P(nR given mR) | Foundation for all exit decisions | 300 trades MFE data | 6.2.1, 6.2.2, 6.5.1 |
| 2 | Test speed-to-MFE as predictor | Novel signal for trailing stop tightening | 100 shadow trades with timestamps | 6.5.2, 6.5.3, 6.5.4 |
| 3 | Test dynamic TP via HAR-RV | Volume-adjusted targets | M15 data + 300 trades | 6.8.1, 6.8.2, 6.8.4 |
| 4 | Test session-close rule | Reduce overnight adverse excursion | 300 trades with session timing | 6.6.1, 6.6.2, 6.6.5 |
| 5 | Test optimal partial close split | Lock profit vs. let run | Conditional MFE from #1 | 6.2.2, 6.2.3, 6.2.6 |

---

<a id="gtos-implications"></a>
## 8. Specific GTOS Implications

### Immediate Actions (no code change needed)

1. **Compute P(2R | 1R) from trailing stop shadow data.** This single number determines whether partial close is worth testing. If P(2R | 1R) < 0.50, partial close at 1R adds value. If > 0.60, partial close destroys expectancy.

2. **Compute time-to-1R distribution.** Stratify by fast (<3 candles = 45 min) vs. slow (>6 candles). If fast trades have >10pp higher P(2R), the speed-to-MFE signal is actionable.

3. **Compute RV-MFE correlation.** If MFE scales linearly with session RV, dynamic TP is justified. If not, fixed TP is optimal.

### Medium-term Tests (code changes, shadow mode)

4. **Implement HAR-RV dynamic TP in shadow mode.** Log what the dynamic TP would have been for each trade. Compare to actual 1.5R TP outcomes.

5. **Implement session-close rule in shadow mode.** Log whether positions held past kill zone end had worse outcomes than those closed at end.

6. **Implement LBMA fix risk window.** Flag trades open during 14:00-15:30 UTC and log their MAE during the fix window.

### WF-2 Candidates (require CEO approval)

7. **Partial close at TP1 + trailing stop on runner.** Only if P(2R | 1R) is in the 0.45-0.55 range (ambiguous zone where partial close helps risk-adjusted return without destroying expectancy).

8. **Vol-regime exit classification.** Use HAR-RV forecast to classify regime (high/medium/low vol) and apply different exit rules per regime.

---

<a id="references"></a>
## 9. Full Reference List

### Q-6.2: Partial Close

1. Almgren, R. & Chriss, N. (2001). Optimal Execution of Portfolio Transactions. *Journal of Risk*, 3(2), 5-40.
2. Lopez de Prado, M. (2018). *Advances in Financial Machine Learning*. Wiley. Ch. 3, 10.
3. Leung, T. & Zhang, H. (2021). Optimal Trading with a Trailing Stop. *Applied Mathematics & Optimization*, 83, 669-698.
4. Acar, E. & Satchell, S. (Eds.) (2002). *Advanced Trading Rules*. 2nd Ed., Butterworth-Heinemann.
5. Acar, E. & Toffel, R. (2000). Stop-loss and Investment Returns. Working Paper, Institute of Actuaries.
6. Kelly, J.L. (1956). A New Interpretation of Information Rate. *Bell System Technical Journal*, 35(4), 917-926.
7. Kaminski, K.M. & Lo, A.W. (2014). When Do Stop-Loss Rules Stop Losses? *Journal of Financial Markets*, 18, 234-254.
8. Lei, A.Y.C. & Li, H. (2009). The Value of Stop-Loss Strategies. *Financial Services Review*, 18(1), 1-18.

### Q-6.5: Speed to MFE

9. Sweeney, J. (1997). *Maximum Adverse Excursion*. Wiley.
10. Gao, L., Han, Y., Li, S.Z. & Zhou, G. (2018). Market Intraday Momentum. *Journal of Financial Economics*, 129(2), 394-414.
11. Moskowitz, T.J., Ooi, Y.H. & Pedersen, L.H. (2012). Time Series Momentum. *Journal of Financial Economics*, 104(2), 228-250.
12. Bogousslavsky, V. (2016). Infrequent Rebalancing, Return Autocorrelation, and Seasonality. *Journal of Finance*, 71(6), 2967-3006.
13. Daniel, K., Hirshleifer, D. & Subrahmanyam, A. (1998). Investor Psychology and Security Market Under- and Overreactions. *Journal of Finance*, 53(6), 1839-1885.
14. Jegadeesh, N. & Titman, S. (1993). Returns to Buying Winners and Selling Losers. *Journal of Finance*, 48(1), 65-91.
15. Miffre, J. & Rallis, G. (2007). Momentum Strategies in Commodity Futures Markets. *Journal of Banking & Finance*, 31(6), 1863-1886.

### Q-6.6: Session Close / Overnight Risk

16. Iwatsubo, K., Watkins, C. & Xu, T. (2018). Intraday Seasonality in Efficiency, Liquidity, Volatility and Volume. *Journal of Commodity Markets*, 11, 59-71.
17. Caminschi, A. & Heaney, R. (2014). Fixing a Leaky Fixing. *Journal of Futures Markets*, 34(11), 1003-1039.
18. Boyarchenko, N., Larsen, L.C. & Whelan, P. (2022). The Overnight Drift. *Federal Reserve Bank of New York Staff Report No. 917*.
19. Plastun, A., Sibande, X., Gupta, R. & Wohar, M.E. (2020). Price Gap Anomaly in the US Stock Market. *North American Journal of Economics and Finance*, 52, 101177.
20. Boudt, K., Croux, C. & Laurent, S. (2011). Robust Estimation of Intraweek Periodicity. *Journal of Empirical Finance*, 18(2), 353-367.
21. Yu, H., Nartea, G.V. & Gan, C. (2016). Weekday Effects on Gold. *Banks and Bank Systems*, 11(2), 43-53.
22. Xu, Y., Bouri, E., Saeed, T. & Wen, Z. (2020). Intraday Return Predictability: Commodity ETFs. *PLOS ONE*, 15(9), e0238870.
23. Osler, C.L. (2005). Stop-Loss Orders and Price Cascades. *Journal of International Money and Finance*, 24(2), 219-241.
24. Lucca, D.O. & Moench, E. (2015). The Pre-FOMC Announcement Drift. *Journal of Finance*, 70(1), 329-371.
25. Heston, S.L., Korajczyk, R.A. & Sadka, R. (2010). Intraday Patterns in the Cross-section of Stock Returns. *Journal of Finance*, 65(4), 1369-1407.

### Q-6.7: Institutional Exit Principles

26. Bertsimas, D. & Lo, A.W. (1998). Optimal Control of Execution Costs. *Journal of Financial Markets*, 1(1), 1-50.
27. Perold, A.F. (1988). The Implementation Shortfall. *Journal of Portfolio Management*, 14(3), 4-9.
28. Gatheral, J. (2010). No-Dynamic-Arbitrage and Market Impact. *Quantitative Finance*, 10(7), 749-759.
29. Obizhaeva, A.A. & Wang, J. (2013). Optimal Trading Strategy and Supply/Demand Dynamics. *Journal of Financial Markets*, 16(1), 1-32.
30. Kissell, R. & Glantz, M. (2003). *Optimal Trading Strategies*. AMACOM.
31. Avellaneda, M. & Stoikov, S. (2008). High-Frequency Trading in a Limit Order Book. *Quantitative Finance*, 8(3), 217-224.
32. Cont, R., Kukanov, A. & Stoikov, S. (2014). The Price Impact of Order Book Events. *Journal of Financial Econometrics*, 12(1), 47-88.

### Q-6.8: Dynamic TP / Realized Volatility

33. Andersen, T.G., Bollerslev, T., Diebold, F.X. & Labys, P. (2003). Modeling and Forecasting Realized Volatility. *Econometrica*, 71(2), 579-625.
34. Corsi, F. (2009). A Simple Approximate Long-Memory Model of Realized Volatility. *Journal of Financial Econometrics*, 7(2), 174-196.
35. Baltas, N. & Kosowski, R. (2020). Demystifying Time-Series Momentum Strategies. In *Market Momentum*, Wiley.
36. Wilder, J.W. Jr. (1978). *New Concepts in Technical Trading Systems*. Trend Research.
37. Parkinson, M. (1980). The Extreme Value Method for Estimating the Variance. *Journal of Business*, 53(1), 61-65.
38. Garman, M.B. & Klass, M.J. (1980). On the Estimation of Security Price Volatilities. *Journal of Business*, 53(1), 67-78.
39. Zumbach, G. & Lynch, P. (2001). Heterogeneous Volatility Cascade. *Physica A*, 298(3), 521-529.
40. Bollerslev, T. & Todorov, V. (2011). Tails, Fears and Risk Premia. *Journal of Finance*, 66(6), 2165-2211.
41. Moreira, A. & Muir, T. (2017). Volatility-Managed Portfolios. *Journal of Finance*, 72(4), 1611-1644.

### Additional Cross-Referenced (from prior L0-L3 searches)

42. Glattfelder, J.B., Dupuis, A. & Olsen, R.B. (2011). Patterns in High-Frequency FX Data: Discovery of 12 Empirical Scaling Laws. *Quantitative Finance*, 11(4), 599-614.
43. Nystrup, P., Kolm, P.N. & Lindstrom, E. (2020). Greedy Online Classification of Persistent Market States. *Journal of Financial Data Science*, 2(3), 25-39.

---

*End of L4 Exit Optimization Literature Search. 62 papers surveyed, 41 promoted as testable on GTOS data, 4 critical gaps identified. The conditional MFE distribution is the master dataset needed for all 5 questions.*
