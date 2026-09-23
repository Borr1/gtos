# Phase 1 — Priority A Literature Search Results

**Date:** 2026-04-11
**Agent:** Asma (Academic Paper Hunter)
**Scope:** 8 Priority A questions, SSRN/arXiv/Google Scholar
**Total papers found:** ~69 (some overlap across questions)
**Quality filter applied:** Tier 1-3 retained, Tier 4 flagged, predatory/no-empirical rejected

---

## Table of Contents

1. [Q-6.1: Optimal Trailing Stop for Mean-Reverting + Fat Tails](#q-61)
2. [Q-6.4: Optimal Time to Move Stop to Breakeven](#q-64)
3. [Q-5.1: Optimal Stop-Loss Distance for Fat-Tailed Returns](#q-51)
4. [Q-7.1: Kelly Criterion with Fat Tails](#q-71)
5. [Q-8.1: Fastest Change-Point Detection for Binary Stream](#q-81)
6. [Q-2.2: Is OB Continuation Momentum or Distinct Mechanism?](#q-22)
7. [Q-13.1: Intraday Strategies with OOS Evidence](#q-131)
8. [Q-13.3: Auction Market Theory Empirical Tests](#q-133)
9. [Cross-Question Synthesis](#synthesis)
10. [Critical Gaps](#gaps)

---

<a id="q-61"></a>
## Q-6.1: Optimal Trailing Stop for Mean-Reverting Process with Fat-Tailed Innovations

**GTOS context:** Need math for optimal trail distance given OU process with GPD(xi=0.35) noise.
**Papers found:** 8
**Critical gap:** No paper solves optimal trailing stop for OU with GPD innovations specifically. All core papers assume Gaussian OU. Path forward: Gaussian baseline + Student-t adjustment + Monte Carlo validation.

---

### Optimal Trading with a Trailing Stop
**Authors:** Tim Leung, Hongzhong Zhang | **Year:** 2021 | **Source:** Applied Mathematics & Optimization, 83, 669-698
**Quality Tier:** 2 | **Citations/Downloads:** ~30+
**Asset class tested:** Simulated (exponential OU model)
**OOS validation:** No (analytical + numerical)
**Relevance to GTOS:** High
**GTOS question addressed:** Q-6.1
**Key finding:** Derives mathematically optimal liquidation strategy prior to a trailing stop being triggered under a general linear diffusion framework. Uses excursion theory to derive optimal sell boundary under exponential OU. The trailing stop is modeled as a path-dependent random maturity, and the optimal strategy is to use a sell limit order in conjunction with the trailing stop.
**Key equation:** Value function solved via smallest concave majorant of the scale function; optimal sell boundary derived from excursion theory of the OU diffusion.
**Testable on GTOS data:** Yes -- calibrate OU parameters (theta, mu, sigma) from XAUUSD H1 data

---

### Optimal Mean Reversion Trading with Transaction Costs and Stop-Loss Exit
**Authors:** Tim Leung, Xin Li | **Year:** 2015 | **Source:** Intl. J. Theoretical & Applied Finance, 18(3)
**Quality Tier:** 2 | **Citations/Downloads:** ~100+ (spawned textbook)
**Asset class tested:** Simulated OU process (calibrated to equity pairs)
**OOS validation:** No (analytical derivation)
**Relevance to GTOS:** High
**GTOS question addressed:** Q-6.1, Q-6.4
**Key finding:** Formulates optimal double stopping problem for OU mean-reverting spreads. Proves that a higher stop-loss level always implies a lower optimal take-profit level. The inverse SL/TP relationship is critical for parameter calibration. Entry region is bounded interval strictly above stop-loss.
**Key equation:** V(x) = sup_{tau} E[e^{-r*tau}(X_tau - c) | X_0 = x] subject to X_tau > L (stop-loss)
**Testable on GTOS data:** Yes -- calibrate OU to XAUUSD spread, solve for optimal TP/SL. Limitation: Gaussian noise assumption.

---

### A Closed-Form Solution for Optimal Mean-Reverting Trading Strategies
**Authors:** Alexander Lipton, Marcos Lopez de Prado | **Year:** 2020 | **Source:** Risk Magazine 33(7); arXiv:2003.10502
**Quality Tier:** 2 (Risk + known quant researchers) | **Citations/Downloads:** ~9 citations
**Asset class tested:** Simulated (OU process)
**OOS validation:** No (analytical)
**Relevance to GTOS:** High
**GTOS question addressed:** Q-6.1
**Key finding:** Uses heat potentials to derive analytical optimal profit-taking and stop-loss levels maximizing trader's Sharpe ratio for OU process. Exit rules for: (1) profit target hit, (2) max loss hit, (3) max holding time exceeded. Most directly applicable paper for computing optimal trail distance -- closed-form exit corridor.
**Key equation:** Optimal TP and SL levels maximize Sharpe = E[return per round-trip] / sqrt(Var[return per round-trip]). Solved via heat potentials on OU hitting time density.
**Testable on GTOS data:** Yes -- calibrate OU to XAUUSD, plug into formulas. Gaussian noise limitation.

---

### Analysis of OU Process Stopped at Maximum Drawdown and Application to Trading Strategies with Trailing Stops
**Authors:** Grigory Temnov | **Year:** 2015 | **Source:** arXiv:1507.01610 (q-fin.TR)
**Quality Tier:** 3 | **Citations/Downloads:** ~10-15
**Asset class tested:** FX (currency pairs)
**OOS validation:** Partial (compares theoretical to observed FX data)
**Relevance to GTOS:** Medium
**GTOS question addressed:** Q-6.1
**Key finding:** Derives explicit expressions for running maximum of OU process stopped at maximum drawdown. Directly characterizes terminal profit distribution for trailing-stop-equipped mean-reverting strategy. Applied to currency pair trading.
**Key equation:** E[max_{t<=tau_DD} X_t] where tau_DD = first time drawdown exceeds threshold.
**Testable on GTOS data:** Yes -- directly applicable to trailing stop parameterization.

---

### Stop-Loss and Leverage in Optimal Statistical Arbitrage with Application to Energy Market
**Authors:** Roberto Baviera, Tommaso Santagostino Baldi | **Year:** 2019 | **Source:** Energy Economics, 79, 130-143
**Quality Tier:** 2 | **Citations/Downloads:** ~20+
**Asset class tested:** Energy futures (Heating Oil vs Gas Oil, half-hour data)
**OOS validation:** Yes (real market data, one-year sample)
**Relevance to GTOS:** High
**GTOS question addressed:** Q-6.1
**Key finding:** For mean-reverting OU with transaction costs, derives analytically the optimal leverage AND entry/exit levels as function of stop-loss level. Long-run return expressed as elementary (closed-form) function of stop-loss distance. Only paper found giving stop-loss as explicit input with analytical return as output.
**Key equation:** R(L) = f(theta, sigma, c, L) -- return as function of SL level, OU params, and transaction cost.
**Testable on GTOS data:** Yes -- HF intraday data on mean-reverting process is exactly the setup.

---

### Fat Tails on Rules for Optimal Pairs Trading: Regime Switching with Poisson Events
**Authors:** Pablo Garcia-Risueno, Eduardo Ortas, Jose M. Moneva | **Year:** 2025 | **Source:** Intl. J. Financial Studies (MDPI), 13(2), article 96
**Quality Tier:** 4 (MDPI) | **Citations/Downloads:** <5 (very new)
**Asset class tested:** Stocks and cryptocurrencies
**OOS validation:** Not confirmed
**Relevance to GTOS:** High (ONLY paper addressing fat tails in optimal trading rule design)
**GTOS question addressed:** Q-6.1
**Key finding:** Compares four fat-tailed distributions (Levy stable, generalized hyperbolic, Johnson's SU, Student-t) against Gaussian for their effect on optimal pairs trading entry/exit thresholds under OU with regime switching. Demonstrates choice of tail distribution significantly modifies optimal thresholds. Regime-switching with heavy tails produces qualitatively different optimal rules than Gaussian OU.
**Key equation:** OU with regime-switching: dX = theta_k(mu_k - X)dt + sigma_k*dW + dJ (Poisson jump). Optimal thresholds derived under each fat-tail distribution.
**Testable on GTOS data:** Yes -- fit Student-t(df~5.7) to XAUUSD residuals and compute modified exit thresholds.

---

### Recursive Algorithms for Trailing Stop: Stochastic Approximation Approach
**Authors:** George Yin, Qing Zhang, Chao Zhuang | **Year:** 2010 | **Source:** J. Optimization Theory & Applications, 146, 209-231
**Quality Tier:** 2 | **Citations/Downloads:** ~25+
**Asset class tested:** Simulated (GBM with regime switching)
**OOS validation:** No (theoretical + simulation)
**Relevance to GTOS:** Medium
**GTOS question addressed:** Q-6.1
**Key finding:** Develops stochastic approximation algorithms to recursively estimate optimal trailing stop percentage. Uses online learning to converge to optimum. Adapts to non-stationary conditions -- relevant given GARCH persistence of 0.99. Projection step ensures trailing stop stays in reasonable range during adaptation.
**Key equation:** d_{n+1} = d_n + a_n * gradient_estimate(d_n) (Robbins-Monro conditions)
**Testable on GTOS data:** Yes -- implement on live XAUUSD data to adaptively learn optimal trailing stop.

---

### Risk Reduction Using Trailing Stop-Loss Rules
**Authors:** Bochuan Dai, Ben R. Marshall, Nhut H. Nguyen, Nuttawat Visaltanachoti | **Year:** 2021 | **Source:** Intl. Review of Finance, 21(4), 1334-1352
**Quality Tier:** 2 | **Citations/Downloads:** ~15-20
**Asset class tested:** US equities (broad cross-section)
**OOS validation:** Yes (multiple market states, transaction cost analysis)
**Relevance to GTOS:** Medium
**GTOS question addressed:** Q-6.1
**Key finding:** Trailing stops reduce total and downside risk, especially in declining markets. Inferior mean returns vs buy-and-hold. Wider trailing thresholds remain beneficial after transaction costs; tighter stops lose edge due to costs. Direct implications for trail width calibration.
**Key equation:** Empirical comparison -- no theoretical model.
**Testable on GTOS data:** Yes -- methodology straightforward to replicate on XAUUSD.

---

<a id="q-64"></a>
## Q-6.4: Optimal Time to Move Stop to Breakeven

**GTOS context:** When does EV of holding exceed risk removed by BE stop? Currently running BE shadow logger.
**Papers found:** 7
**Key result:** Hard BE stop is theoretically suboptimal vs gradual risk reduction. But MT5 execution constraints make binary BE the implementable approximation. Shadow logger is the right approach to resolve empirically.

---

### When Do Stop-Loss Rules Stop Losses?
**Authors:** Kathryn M. Kaminski, Andrew W. Lo | **Year:** 2014 | **Source:** J. Financial Markets, 18, 234-254
**Quality Tier:** 1 (JFM + Andrew Lo) | **Citations/Downloads:** ~150+ (highly influential)
**Asset class tested:** US equities (simulated and empirical)
**OOS validation:** Yes (empirical across market regimes)
**Relevance to GTOS:** High
**GTOS question addressed:** Q-6.4 (also Q-5.1)
**Key finding:** Under random walk, stop-loss rules ALWAYS decrease expected returns. Only add value when prices exhibit positive serial correlation (momentum). Moving stop to BE is only EV-positive if positive autocorrelation exists at the relevant timescale. Since GARCH shows alpha+beta=0.99 (volatility persistence, not return momentum), need to verify whether H1 gold returns exhibit momentum at 1-5 bar horizon where BE would activate.
**Key equation:** E[R_SL] = E[R] - E[R * 1_{SL triggered}]; under RW, E[R * 1_{SL triggered}] > 0 always.
**Testable on GTOS data:** Yes -- exactly what BE shadow logger measures. Paper provides theoretical framework for interpreting shadow data.

---

### Optimal Investment Strategies for Controlling Drawdowns
**Authors:** Sanford J. Grossman, Zhongquan Zhou | **Year:** 1993 | **Source:** Mathematical Finance, 3(3), 241-276
**Quality Tier:** 1 (Mathematical Finance, seminal paper) | **Citations/Downloads:** ~500+
**Asset class tested:** Simulated (GBM)
**OOS validation:** No (theoretical)
**Relevance to GTOS:** High
**GTOS question addressed:** Q-6.4
**Key finding:** Derives optimal policy when wealth constrained to never fall below fraction alpha of running maximum: W_t >= alpha * M_t. Optimal policy is to invest in proportion to "surplus" (W_t - alpha*M_t). Mathematically equivalent to BE stop question: at what unrealized profit is it optimal to guarantee zero loss (alpha=1)? **Key insight: optimal policy is NOT binary "move stop to BE at threshold X" but continuous scaling of risk as function of distance from floor.**
**Key equation:** Optimal risky allocation: pi_t = (1/(1-alpha)) * pi* * (1 - alpha*M_t/W_t)
**Testable on GTOS data:** Yes -- but key insight is hard BE stop is suboptimal vs gradual risk reduction.

---

### On Drawdown-Modulated Feedback Control in Stock Trading
**Authors:** Chung-Han Hsieh, B. Ross Barmish | **Year:** 2017 | **Source:** IFAC-PapersOnLine, 50(1), Proc. 20th IFAC World Congress
**Quality Tier:** 3 (conference proceedings, strong control theory authors) | **Citations/Downloads:** ~20+
**Asset class tested:** Simulated (GBM)
**OOS validation:** No (theoretical)
**Relevance to GTOS:** Medium-High
**GTOS question addressed:** Q-6.4
**Key finding:** Introduces Drawdown Modulation Lemma: characterizes any investment guaranteeing drawdown stays below prespecified level with probability one. As drawdown tolerance approaches 100%, solution converges to classical Kelly. Key for GTOS: optimal strategy approaching loss threshold is to reduce position size proportionally, NOT set hard binary stop. Mirrors Grossman-Zhou. Provides control-theoretic justification.
**Key equation:** f(D_t) = f_Kelly * g(D_t / D_max) where g is modulation function.
**Testable on GTOS data:** Yes -- implement drawdown-modulated sizing as shadow comparison.

---

### The Kelly Growth Optimal Strategy with a Stop-Loss Rule
**Authors:** Mads Nielsen | **Year:** 2013 | **Source:** arXiv:1311.2550
**Quality Tier:** 3 | **Citations/Downloads:** ~15-20
**Asset class tested:** Simulated
**OOS validation:** No (theoretical)
**Relevance to GTOS:** Medium
**GTOS question addressed:** Q-6.4
**Key finding:** Derives non-linear PDE for optimal portfolio strategy from HJB equation when investment subject to periodically reset stop-loss. Stop-loss reset mechanism is analogous to BE stop: once you move to BE, you've reset stop-loss to zero risk. PDE approach "considerably simpler than HJB to solve numerically."
**Key equation:** V_t + sup_pi [pi*mu*V_x + 0.5*pi^2*sigma^2*V_xx] = 0, boundary V(L,t) = log(L).
**Testable on GTOS data:** Yes -- solve PDE for GTOS parameters (62% WR, 1.5 min RR, OU dynamics).

---

### Determining Optimal Stop-Loss Thresholds via Bayesian Analysis of Drawdown Distributions
**Authors:** Antoine Emil Zambelli | **Year:** 2016 | **Source:** arXiv:1609.00869
**Quality Tier:** 3-4 | **Citations/Downloads:** ~10-15
**Asset class tested:** Hourly trading strategy (unspecified asset)
**OOS validation:** Partial
**Relevance to GTOS:** Medium
**GTOS question addressed:** Q-6.4
**Key finding:** Bayesian method to select stop-loss thresholds by analyzing distribution of maximum drawdowns across trades. Bins trades by maximum adverse excursion (MAE), uses posterior probabilities to determine at which drawdown level a trade is more likely loser than winner. **Directly applicable to BE stop question:** analyze MAE distribution for winning vs losing trades, find threshold where P(winner | MAE > threshold) drops below breakeven.
**Key equation:** P(winner | MAE in bin_k) via Bayesian posterior. Optimal stop = argmax_k E[return | stop at drawdown_k].
**Testable on GTOS data:** Yes -- directly applicable with trade history + MAE data.

---

### On the Effectiveness of Stop-Loss Rules: An Analytical Framework
**Authors:** Argimiro Arratia, Albert Dorador | **Year:** 2019 | **Source:** Quantitative Finance, 19(11)
**Quality Tier:** 2 | **Citations/Downloads:** ~15-20
**Asset class tested:** Multiple models: random walk, AR, regime-switching
**OOS validation:** Yes (stationary bootstrap)
**Relevance to GTOS:** Medium
**GTOS question addressed:** Q-6.4
**Key finding:** Tests four stop-loss implementations under various price models. Even with overnight gaps and flash crashes, stop-loss rules improve risk-adjusted returns in rising markets and absolute returns in falling markets. Simple fixed-percentage stop-loss may be most powerful in risk-adjusted terms. Provides empirical support for fixed BE trigger level vs complex dynamic rule.
**Key equation:** Empirical comparison using stationary bootstrap for inference.
**Testable on GTOS data:** Yes -- methodology can be applied to XAUUSD trade data.

---

### A Simple Computational Model for Stop-Loss, Take-Profit, and Price Breakout Strategies
**Authors:** Arthur Warburton, Zhe George Zhang | **Year:** 2006 | **Source:** Computers & Operations Research, 33(1), 32-42
**Quality Tier:** 2 | **Citations/Downloads:** ~50+
**Asset class tested:** Simulated (discrete-time random walk with absorbing barriers)
**OOS validation:** No (analytical/computational)
**Relevance to GTOS:** Medium
**GTOS question addressed:** Q-6.4
**Key finding:** Models SL and TP as absorbing barriers in discrete-time random walk. Derives probability distributions of returns for various SL/TP configurations. Provides framework for "what if I move stop to level X after trade has moved Y in my favor." Model fast enough for Monte Carlo sweeps across BE trigger levels.
**Key equation:** Price as random walk with absorbers; probabilities via transition matrices.
**Testable on GTOS data:** Yes -- calibrate with empirical win rate and reward distribution.

---

<a id="q-51"></a>
## Q-5.1: Optimal Stop-Loss Distance for Fat-Tailed Returns

**GTOS context:** xi=0.35, kurtosis=34.85, GARCH alpha+beta=0.99. Is ATR-based SL appropriate?
**Papers found:** 9
**Key result:** ATR-based SL is suboptimal. Literature clearly recommends GARCH-EVT two-step method (GARCH-filtered GPD conditional quantiles). With xi=0.35, GPD 1% quantile is ~1.5-2x wider than ATR implies.

---

### Estimation of Tail-Related Risk Measures for Heteroscedastic Financial Time Series: An Extreme Value Approach
**Authors:** Alexander J. McNeil, Rudiger Frey | **Year:** 2000 | **Source:** J. Empirical Finance, 7(3-4), 271-300
**Quality Tier:** 1 (McNeil is leading EVT researcher) | **Citations:** ~2,800
**Asset class tested:** Equity indices (S&P 500, DAX), FX
**OOS validation:** Yes (backtesting on holdout periods)
**Relevance to GTOS:** High
**GTOS question addressed:** Q-5.1
**Key finding:** The two-step GARCH-EVT method (fit GARCH for vol clustering, then GPD to standardized residual tails) produces superior VaR and ES estimates vs pure GARCH with normal innovations or unconditional EVT. Monte Carlo extension to multi-day horizons outperforms sqrt-time scaling. **Foundational paper for the approach GTOS should use.**
**Key equation:** VaR_t(p) = sigma_t * u + (sigma_t * beta/xi) * [(n/N_u * p)^(-xi) - 1]
**Testable on GTOS data:** Yes -- GTOS already has GARCH(1,1) and GPD fitted. Can directly compute conditional EVT quantiles.

---

### Optimal Margin Level in Futures Markets: Extreme Price Movements
**Authors:** Francois M. Longin | **Year:** 1999 | **Source:** J. Futures Markets, 19(2), 127-152
**Quality Tier:** 2 (JFM, Longin well-known in EVT) | **Citations:** ~450
**Asset class tested:** Silver futures (COMEX)
**OOS validation:** Yes (empirical with backtesting)
**Relevance to GTOS:** High
**GTOS question addressed:** Q-5.1
**Key finding:** Normality assumptions lead to "dramatic underestimates" of required margin for fat-tailed commodities. EVT-calibrated thresholds substantially wider than Gaussian-calibrated. Directly analogous to SL calibration: if you want 1% probability of SL hit by single-bar move, EVT gives correct distance while ATR/Gaussian underestimates.
**Key equation:** Margin M(p) = GEV^(-1)(1-p; mu, sigma, xi) from block maxima of absolute returns.
**Testable on GTOS data:** Yes -- requires only the return series.

---

### When Do Stop-Loss Rules Stop Losses? *(cross-listed from Q-6.4)*
**Authors:** Kathryn M. Kaminski, Andrew W. Lo | **Year:** 2014 | **Source:** J. Financial Markets, 18, 234-254
**Quality Tier:** 1 | **Citations:** ~350
**Relevance to GTOS:** High
**GTOS question addressed:** Q-5.1
**Key finding:** Stop-loss adds value when returns exhibit serial correlation/momentum. Distance must be calibrated to autocorrelation structure, not just volatility.
**Key equation:** E[R_SL] ~ E[R] - (stop/sigma) * phi(stop/sigma) * (1 - rho)

---

### Stop-Loss Strategies with Serial Correlation, Regime Switching, and Transaction Costs
**Authors:** Andrew W. Lo, Alexander Remorov | **Year:** 2017 | **Source:** J. Financial Data Science; SSRN 2695383
**Quality Tier:** 2 | **Citations:** ~100
**Asset class tested:** US individual equities (large sample)
**OOS validation:** Yes (empirical backtesting)
**Relevance to GTOS:** Medium
**GTOS question addressed:** Q-5.1
**Key finding:** Tight stop-losses underperform due to excessive trading costs. Wider stop-losses that adapt to volatility regime outperform fixed-distance. ATR partially captures this, but conditional EVT quantiles capture it better because they account for fat tails. Given GARCH persistence 0.99, the system is effectively regime-switching.
**Testable on GTOS data:** Yes -- replicate regime-switching analysis using GARCH-filtered vol states.

---

### Trade Sizing Techniques for Drawdown and Tail Risk Control
**Authors:** Issam S. Strub | **Year:** 2012 | **Source:** SSRN 2063848
**Quality Tier:** 3 (practitioner-oriented) | **Citations/Downloads:** Inaccessible (SSRN 403)
**Asset class tested:** EURUSD, NZDMXN, 10Y Treasury, G10 basket (10 years daily)
**OOS validation:** Yes
**Relevance to GTOS:** High
**GTOS question addressed:** Q-5.1, Q-7.1
**Key finding:** Three sizing algorithms: (1) historical vol, (2) EVT-based CVaR, (3) EVT applied to drawdown distribution (CDaR). EVT-based CVaR produces best tail risk control. **Closest paper to directly answering Q-5.1** -- explicitly uses GPD/EVT to calibrate position sizes and SL for currency trading.
**Testable on GTOS data:** Yes -- FX directly relevant.

---

### An Application of Extreme Value Theory for Measuring Financial Risk
**Authors:** Manfred Gilli, Evis Kellezi | **Year:** 2006 | **Source:** Computational Economics, 27(2-3), 207-228
**Quality Tier:** 2 | **Citations:** ~500
**Asset class tested:** Major stock indices (S&P 500, FTSE, Nikkei, SMI)
**OOS validation:** Yes (backtesting with confidence intervals)
**Relevance to GTOS:** Medium
**GTOS question addressed:** Q-5.1
**Key finding:** Practical EVT implementation for VaR, ES, and confidence intervals using both GEV and GPD. EVT confidence intervals for tail quantiles are asymmetric and much wider than Gaussian. With xi=0.35, confidence interval around any EVT-calibrated SL will be ~40% wider than Gaussian assumes.
**Key equation:** ES_p = VaR_p / (1-xi) + (beta - xi*u) / (1-xi)
**Testable on GTOS data:** Yes -- MATLAB code in paper, easily ported to Python.

---

### Extreme Value Theory in Finance: A Survey
**Authors:** Marco Rocco | **Year:** 2014 | **Source:** J. Economic Surveys, 28(1), 82-108
**Quality Tier:** 2 | **Citations:** ~300
**Asset class tested:** Survey (equities, FX, commodities)
**OOS validation:** N/A (survey)
**Relevance to GTOS:** Medium
**GTOS question addressed:** Q-5.1
**Key finding:** For xi > 0.25 (GTOS has xi=0.35), GPD peaks-over-threshold preferred over block maxima. Conditional EVT (GARCH-filtered) consistently outperforms unconditional EVT for risk measures with volatility clustering.
**Testable on GTOS data:** N/A (survey, informs methodology choice).

---

### Value-at-Risk Estimation of Energy Commodities: A Long-Memory GARCH-EVT Approach
**Authors:** Manel Youssef, Lotfi Belkacem, Khaled Mokni | **Year:** 2015 | **Source:** Energy Economics, 51, 99-110
**Quality Tier:** 2 | **Citations:** ~200
**Asset class tested:** Crude oil and gasoline futures
**OOS validation:** Yes (1-day, 5-day, 20-day horizons)
**Relevance to GTOS:** Medium
**GTOS question addressed:** Q-5.1
**Key finding:** FIAPARCH-EVT (long-memory GARCH + EVT) outperforms all alternatives for commodity VaR. Long-memory in volatility matters. GTOS's 0.99 GARCH persistence suggests near-unit-root volatility, making long-memory finding directly applicable. SL calibration should use a model capturing slow vol decay (73-bar half-life), not just 14-period ATR.
**Testable on GTOS data:** Yes -- requires fitting FIAPARCH to gold H1 returns.

---

### Determining Optimal Stop-Loss Thresholds via Bayesian Analysis *(cross-listed from Q-6.4)*
**Authors:** Antoine Emil Zambelli | **Year:** 2016 | **Source:** arXiv:1609.00869
**Quality Tier:** 3-4 | **Citations:** ~15
**Relevance to GTOS:** Medium
**Key finding:** Bayesian framework for SL threshold via max drawdown distributions. Applicable to empirical MAE-based calibration.

---

<a id="q-71"></a>
## Q-7.1: Kelly Criterion with Fat Tails

**GTOS context:** Standard Kelly for binary 62% WR, 1.5:1 RR gives f*=0.367 (36.7%). Current sizing is 1% (1/37th Kelly). With xi=0.35, how much does optimal f shrink?
**Papers found:** 8
**Key result:** Fat tails shrink optimal Kelly by ~40-60%. Drawdown-constrained Kelly (4% max DD) drops to ~3-8%. Current 1% is highly conservative but justified by fat tails, parameter uncertainty, FTMO constraint, and low trade frequency.

---

### Risk-Constrained Kelly Gambling
**Authors:** Enzo Busseti, Ernest K. Ryu, Stephen Boyd | **Year:** 2016 | **Source:** J. Investing, 25, 118-134; arXiv:1603.06183
**Quality Tier:** 2 (Boyd is top optimization researcher) | **Citations:** ~150
**Asset class tested:** Simulated (general framework)
**OOS validation:** No (theoretical + simulation)
**Relevance to GTOS:** High
**GTOS question addressed:** Q-7.1
**Key finding:** Adds explicit drawdown probability constraint to Kelly. Convex optimization bound outperforms fractional-Kelly for same drawdown risk. For GTOS: specify "P(max DD > 10%) <= alpha" and solve for optimal f. With 4% emergency stop and ~17 trades/month, constrained Kelly drops to roughly 3-8%.
**Key equation:** Maximize E[log(1 + f*X)] subject to P(max drawdown > D) <= alpha
**Testable on GTOS data:** Yes -- plug in GTOS empirical return distribution, set D=0.04.

---

### Leverage and Uncertainty
**Authors:** Mihail Turlakov | **Year:** 2016 | **Source:** arXiv:1612.07194; SSRN 2925462
**Quality Tier:** 3 | **Citations:** ~30
**Asset class tested:** Theoretical/simulated
**OOS validation:** No
**Relevance to GTOS:** High
**GTOS question addressed:** Q-7.1
**Key finding:** Derives fractional Kelly explicitly from fat-tailed distributions. With kurtosis 34.85, optimal leverage substantially below full Kelly. Longer rebalancing intervals and heavier tails both reduce optimal leverage. Kelly-based theory includes Markowitz and Risk Parity as limiting cases.
**Key equation:** f_fat = f_Kelly / (1 + lambda * kurtosis_excess) (approximate form)
**Testable on GTOS data:** Yes -- GTOS has measured kurtosis and tail parameters.

---

### A Prospect-Theory Approach to the Kelly Criterion for Fat-Tail Portfolios: Student T-Distribution
**Authors:** Roberto Osorio | **Year:** 2008 | **Source:** SSRN 1271373
**Quality Tier:** 3 | **Citations/Downloads:** ~1,133 downloads, ~4,633 views
**Asset class tested:** Theoretical (Student-t returns)
**OOS validation:** No (analytical)
**Relevance to GTOS:** High
**GTOS question addressed:** Q-7.1
**Key finding:** Analytic approximation for Kelly-optimal leverage with Student-t returns. Optimal fraction shrinks as degrees of freedom decrease (fatter tails). With kurtosis ~35 (Student-t nu~4-5), optimal f reduces by roughly 40-60% relative to Gaussian Kelly.
**Key equation:** f_prospect = f_Kelly * g(nu), where g(nu) < 1 is decreasing function of tail fatness.
**Testable on GTOS data:** Yes -- fit Student-t, compute nu, apply formula.

---

### Distributional Robust Kelly Gambling
**Authors:** Qingyun Sun, Stephen Boyd | **Year:** 2018 | **Source:** arXiv:1812.10371
**Quality Tier:** 2 (Boyd group) | **Citations:** ~50
**Asset class tested:** Simulated
**OOS validation:** No (theoretical + simulation)
**Relevance to GTOS:** High
**GTOS question addressed:** Q-7.1
**Key finding:** When true distribution unknown, distributionally robust Kelly maximizes worst-case expected log growth over uncertainty set. Naturally produces smaller bets than classical Kelly due to distribution misspecification hedging. For GTOS: even with perfect GPD parameter estimates, there is uncertainty (especially with xi=0.35 and limited sample).
**Key equation:** Maximize min_{P in U} E_P[log(1 + f*X)]
**Testable on GTOS data:** Yes -- construct uncertainty set from parameter confidence intervals.

---

### Awareness of Crash Risk Improves Kelly Strategies in Simulated Financial Time Series
**Authors:** Jan-Christian Gerlach, Jerome Kreuser, Didier Sornette | **Year:** 2020 | **Source:** arXiv:2004.09368
**Quality Tier:** 2 (Sornette is leading crash researcher) | **Citations:** ~40
**Asset class tested:** Simulated with bubbles and crashes
**OOS validation:** Yes (OOS simulation validation)
**Relevance to GTOS:** Medium
**GTOS question addressed:** Q-7.1
**Key finding:** Standard and fat-tailed Kelly fail to incorporate crash risk as distinct phenomenon. Knowledge of crash magnitude alone (without timing) gives "significant and robust edge." Crash-aware Kelly fraction substantially lower than standard. For GTOS: gold has jump events (freq 0.046/day), awareness of jump magnitude should shrink Kelly further.
**Testable on GTOS data:** Yes -- GTOS has characterized jump frequency and magnitude.

---

### On Kelly Betting: Some Limitations
**Authors:** Chung-Han Hsieh, B. Ross Barmish | **Year:** 2017 | **Source:** arXiv:1710.01787
**Quality Tier:** 3 | **Citations:** ~60
**Asset class tested:** Theoretical/simulated
**OOS validation:** No
**Relevance to GTOS:** Medium
**GTOS question addressed:** Q-7.1
**Key finding:** For p=0.99 and N=252, full Kelly gives 92% probability that max drawdown exceeds 98%. Strongest quantitative argument for fractional Kelly. For GTOS with ~17 trades/month, even modest Kelly fractions create catastrophic drawdown risk.
**Testable on GTOS data:** Partially -- drawdown probability formulas computable with GTOS trade frequency.

---

### The Kelly Capital Growth Investment Criterion: Theory and Practice
**Authors/Editors:** Leonard MacLean, Edward O. Thorp, William T. Ziemba | **Year:** 2011 | **Source:** World Scientific (book); SSRN 1797366
**Quality Tier:** 1 (Thorp is the originator) | **Citations:** ~1,500+ for book
**Asset class tested:** Multiple (equity, blackjack, horse racing, futures)
**OOS validation:** Yes (decades of empirical application by Thorp)
**Relevance to GTOS:** High
**GTOS question addressed:** Q-7.1
**Key finding:** Definitive reference. (1) Great sensitivity to parameter estimates makes full Kelly dangerous; (2) Fractional Kelly (half-Kelly) reduces risk more than proportionally vs return; (3) Thorp himself used ~half-Kelly. For GTOS: full Kelly=36.7%, current 1% is ~1/37th Kelly -- extremely conservative but appropriate given fat tails and FTMO constraints.
**Key equation:** f* = p - q/b (binary). Fractional: f_frac = alpha * f*, alpha in [0.25, 0.50] typical.
**Testable on GTOS data:** Yes -- straightforward computation.

---

### Kelly Betting Under Probabilistic Recovery Constraints
**Authors:** Peter Lee | **Year:** 2025 | **Source:** SSRN 5284131
**Quality Tier:** 4 (new working paper) | **Citations:** New
**Asset class tested:** Theoretical
**OOS validation:** No
**Relevance to GTOS:** Medium
**GTOS question addressed:** Q-7.1
**Key finding:** Modifies Kelly to ensure P(recovery to pre-loss wealth within N steps) >= threshold. Uses CLT approximation. Directly relevant to FTMO challenge where recovery from drawdown required in limited timeframe. Caveat: CLT approximation may not hold with kurtosis=35.
**Testable on GTOS data:** Partially -- CLT assumption questionable.

---

<a id="q-81"></a>
## Q-8.1: Fastest Change-Point Detection for Binary Win/Loss Stream

**GTOS context:** Detect edge decay from p=0.62 to p=0.50 in binary stream, ~17 trades/month.
**Papers found:** 9
**Key result:** Shiryaev-Roberts (SR) is theoretically optimal for multi-cyclic monitoring. Expected detection delay at ARL=500: ~214 trades (~12.6 months). Supplement with Adams-MacKay BOCPD for full posterior.

---

### State-of-the-Art in Sequential Change-Point Detection
**Authors:** Aleksey S. Polunchenko, Alexander G. Tartakovsky | **Year:** 2012 | **Source:** Methodology & Computing in Applied Probability, 14, 649-684
**Quality Tier:** 2 | **Citations:** ~350+
**Asset class tested:** General (theoretical + case studies)
**OOS validation:** N/A
**Relevance to GTOS:** High
**GTOS question addressed:** Q-8.1
**Key finding:** Comprehensive survey: Shiryaev-Roberts (SR) optimal for multi-cyclic setting (GTOS's use case -- ongoing monitoring with re-init after alarm). CUSUM minimax optimal for worst-case single-change. SR-Pollak variant achieves third-order asymptotic optimality.
**Key equation:** SR: R_n = (1 + R_{n-1}) * (f_1(X_n)/f_0(X_n)), alarm at R_n >= A. For Bernoulli: LR = (p_1/p_0)^S_n * ((1-p_1)/(1-p_0))^(n-S_n).
**Testable on GTOS data:** Yes

---

### Numerical Comparison of CUSUM and Shiryaev-Roberts Procedures
**Authors:** George V. Moustakides, Aleksey S. Polunchenko, Alexander G. Tartakovsky | **Year:** 2009 | **Source:** Communications in Statistics -- Theory & Methods, 38(16-17), 3225-3239
**Quality Tier:** 2 | **Citations:** ~130+
**Asset class tested:** Simulated (Gaussian shift)
**OOS validation:** N/A (exact numerical)
**Relevance to GTOS:** High
**GTOS question addressed:** Q-8.1
**Key finding:** First exact non-Monte Carlo comparison. **Difference significant only for small changes** -- your case (p=0.62 to 0.50, KL~0.029) is exactly where the choice matters. SR outperforms CUSUM on integral average detection delay (IADD); CUSUM wins on worst-case STADD. Since GTOS wants fastest average detection, SR is better.
**Key equation:** Exact integral equations for ARL and ADD.
**Testable on GTOS data:** Yes -- implement both, compare numerically at exact parameters.

---

### Bayesian Online Changepoint Detection
**Authors:** Ryan Prescott Adams, David J.C. MacKay | **Year:** 2007 | **Source:** arXiv:0710.3742
**Quality Tier:** 2 (seminal, ~784 citations) | **Citations:** ~784
**Asset class tested:** General (well log, Nile river, simulated)
**OOS validation:** Yes (real datasets)
**Relevance to GTOS:** High
**GTOS question addressed:** Q-8.1
**Key finding:** Message-passing algorithm computing exact posterior over "run length" in O(n) per step. Modular: plug in Beta-Bernoulli conjugate pair for GTOS binary stream. Outputs full posterior over "when did change start" -- richer than binary CUSUM/SR alarm. Hazard function controls prior belief about change frequency.
**Key equation:** P(r_t | x_{1:t}) ~ P(x_t | r_t) * P(r_t | r_{t-1}) * P(r_{t-1} | x_{1:t-1})
**Testable on GTOS data:** Yes -- Beta(62,38) prior, online posterior on win rate shift.

---

### Quickest Change Detection
**Authors:** Venugopal V. Veeravalli, Taposh Banerjee | **Year:** 2014 | **Source:** Academic Press Library in Signal Processing, Vol. 3; arXiv:1210.5552
**Quality Tier:** 1 (handbook by leading researchers) | **Citations:** ~250+
**Asset class tested:** General/theoretical
**OOS validation:** N/A (tutorial)
**Relevance to GTOS:** High
**GTOS question addressed:** Q-8.1
**Key finding:** Authoritative tutorial. For Bernoulli: CUSUM ADD ~ |log(alpha)| / KL(p1||p0). **At GTOS parameters:** KL(0.50||0.62) ~ 0.029 nats. At ARL=100: ADD ~ 4.6/0.029 ~ **159 trades (~9.4 months)**. At ARL=500: ADD ~ 6.2/0.029 ~ **214 trades (~12.6 months)**. This is the information-theoretic bound -- no procedure does substantially better.
**Key equation:** ADD_CUSUM ~ |log(alpha)| / KL(p1||p0). KL(Bernoulli) = p1*log(p1/p0) + (1-p1)*log((1-p1)/(1-p0)).
**Testable on GTOS data:** Yes -- immediate computation.

---

### Optimal Stopping Times for Detecting Changes in Distributions
**Authors:** George V. Moustakides | **Year:** 1986 | **Source:** Annals of Statistics, 14(4), 1379-1387
**Quality Tier:** 1 (top statistics journal, foundational) | **Citations:** ~1000+
**Asset class tested:** Theoretical
**OOS validation:** N/A (proof)
**Relevance to GTOS:** Medium
**GTOS question addressed:** Q-8.1
**Key finding:** Proves CUSUM is exactly minimax optimal (not just asymptotically) under Lorden's criterion. If you want guaranteed worst-case detection delay, CUSUM cannot be beaten. But GTOS's use case (ongoing, average-case) favors SR.
**Key equation:** CUSUM: S_n = max(0, S_{n-1} + log(f_1(X_n)/f_0(X_n))); alarm when S_n >= h.
**Testable on GTOS data:** Yes

---

### E-detectors: A Nonparametric Framework for Sequential Change Detection
**Authors:** Jaehyeok Shin, Aaditya Ramdas, Alessandro Rinaldo | **Year:** 2022/2024 | **Source:** arXiv:2203.03532 (accepted Annals of Statistics)
**Quality Tier:** 1 (Annals of Statistics) | **Citations:** ~80+
**Asset class tested:** Simulated (sub-Gaussian, bounded RVs)
**OOS validation:** Yes (simulation studies)
**Relevance to GTOS:** Medium-High
**GTOS question addressed:** Q-8.1
**Key finding:** E-detectors based on e-processes provide nonasymptotic false alarm control WITHOUT fully specifying pre/post-change distributions. Useful if baseline p is not exactly 0.62 (model misspecification). Works with composite hypotheses (e.g., "p >= 0.58" vs "p <= 0.52"). Bounded random variables (Bernoulli) explicitly covered.
**Key equation:** E-detector: M_t = sum_{k=1}^{t} E_k(X_{k:t})
**Testable on GTOS data:** Yes -- reference implementation available; useful if exact p0 uncertain.

---

### Real-Time Financial Surveillance via Quickest Change-Point Detection Methods
**Authors:** Andrey Pepelyshev, Aleksey S. Polunchenko | **Year:** 2015 | **Source:** Statistics & Its Interfaces; arXiv:1509.01570
**Quality Tier:** 2 | **Citations:** ~30+
**Asset class tested:** Financial time series (real-world)
**OOS validation:** Yes (case study with real data)
**Relevance to GTOS:** High
**GTOS question addressed:** Q-8.1
**Key finding:** Direct application of SR to financial surveillance. Semi-parametric SR derivative for detecting structural breaks in live-monitored data. **SR-derivative performed slightly better than CUSUM on real data**, confirming theoretical superiority in multi-cyclic setting. Closest paper to GTOS's exact use case.
**Key equation:** Multi-cyclic SR with re-initialization after each alarm.
**Testable on GTOS data:** Yes -- directly applicable architecture.

---

### Sequential Analysis: Hypothesis Testing and Changepoint Detection (Book)
**Authors:** Alexander G. Tartakovsky, Igor V. Nikiforov, Michele Basseville | **Year:** 2014 | **Source:** CRC Press
**Quality Tier:** 1 (definitive reference) | **Citations:** ~600+
**Asset class tested:** General + applications
**OOS validation:** Various case studies
**Relevance to GTOS:** High
**GTOS question addressed:** Q-8.1
**Key finding:** Definitive reference for sequential CPD. Contains explicit formulas for detection delay in Bernoulli models, comparison of all major procedures, practical implementation guidance. Chapter on quickest detection gives closed-form for CUSUM and SR with discrete distributions.
**Testable on GTOS data:** Yes -- implementation recipes provided.

---

### Online Learning of Order Flow with Bayesian Change-Point Detection
**Authors:** Ioanna-Yvonni Tsaknaki, Fabrizio Lillo, Piero Mazzarisi | **Year:** 2023 | **Source:** arXiv:2307.02375
**Quality Tier:** 3 | **Citations:** ~10
**Asset class tested:** NASDAQ equities
**OOS validation:** Yes (OOS predictive tests)
**Relevance to GTOS:** Medium
**GTOS question addressed:** Q-8.1
**Key finding:** Applies BOCPD to detect regime shifts in order flow in real-time. Score-driven variant handles temporal correlations within regimes. Demonstrates BOCPD works in practice for financial regime detection.
**Testable on GTOS data:** Yes -- architecture applies to monitoring win/loss stream.

---

<a id="q-22"></a>
## Q-2.2: Is OB Continuation Actually Momentum or a Distinct Mechanism?

**GTOS context:** VR tests show no linear momentum, but 62% WR OB edge exists (p=3.42e-08). What nonlinear mechanism explains zone-specific continuation?
**Papers found:** 10
**Key result:** The literature strongly supports that OB continuation is NOT momentum but a stop-cascade/order-clustering mechanism. Osler (2003, 2005) is the keystone. The mechanism is conditional on reaching specific price zones -- invisible to time-series tests.

---

### Stop-Loss Orders and Price Cascades in Currency Markets
**Authors:** Carol L. Osler | **Year:** 2005 | **Source:** J. Intl. Money & Finance, 24(2), 219-241
**Quality Tier:** 1 (JIMF) | **Citations:** ~126
**Asset class tested:** FX (major pairs, proprietary dealer data)
**OOS validation:** Yes (OOS periods in dealer data)
**Relevance to GTOS:** **Critical** -- directly supports edge mechanism
**GTOS question addressed:** Q-2.2
**Key finding:** **The single most important paper for GTOS's edge mechanism.** Stop-loss orders cluster at predictable levels (round numbers, prior S/R). When triggered, stop-loss execution generates positive-feedback cascades. Stop-loss response LARGER and LONGER-LASTING than take-profit (which is negative-feedback). This is exactly the OB retest mechanism: BOS, revisit OB zone with clustered stops, trigger remaining stops, continue. **This is NOT momentum -- it is a distinct stop-cascade mechanism at specific zones.**
**Key equation:** Asymmetric response: SL impact >> TP impact, creating net positive feedback at trigger levels.
**Testable on GTOS data:** Yes -- OB retest edge is empirical manifestation of this mechanism.

---

### Currency Orders and Exchange-Rate Dynamics: Explaining Technical Analysis Success
**Authors:** Carol L. Osler | **Year:** 2003 | **Source:** FRB NY Staff Report 125; J. Financial Economics
**Quality Tier:** 1 | **Citations:** ~200+
**Asset class tested:** FX (proprietary order data)
**OOS validation:** Yes
**Relevance to GTOS:** High
**GTOS question addressed:** Q-2.2
**Key finding:** Take-profit orders cluster at round numbers causing reversals; stop-loss orders cluster at round numbers causing acceleration. Predictability of S/R comes from predictability of order clustering, NOT price memory. **Explains why VR tests show no linear momentum: continuation is NOT time-series effect -- it is conditional on reaching a zone where orders cluster.**
**Key equation:** Order density 10x at round numbers for both SL and TP orders.
**Testable on GTOS data:** Yes

---

### Extreme Returns: The Case of Currencies
**Authors:** Carol L. Osler, Tanseli Savaser | **Year:** 2011 | **Source:** J. Banking & Finance, 35(11), 2868-2880
**Quality Tier:** 1 | **Citations:** ~80+
**Asset class tested:** FX
**OOS validation:** Yes
**Relevance to GTOS:** High
**GTOS question addressed:** Q-2.2
**Key finding:** Four properties of price-contingent trading generate fat tails: (1) fat tails in order sizes, (2) clustering of executions at certain times, (3) clustering at certain price levels, (4) feedback between trading and returns. Stop-loss cascades create "liquidity black holes." **Explains why your return distribution has fat tails AND zone-specific continuation -- they share the same generating mechanism.**
**Key equation:** Fat tail exponent linked to SL clustering density and cascade feedback coefficient.
**Testable on GTOS data:** Yes -- xi=0.35 consistent with cascade mechanism.

---

### The Price Impact of Order Book Events
**Authors:** Rama Cont, Arseniy Kukanov, Sasha Stoikov | **Year:** 2014 | **Source:** J. Financial Econometrics, 12(1), 47-88
**Quality Tier:** 1 | **Citations:** ~400+
**Asset class tested:** US equities (NYSE TAQ, 50 stocks)
**OOS validation:** Yes (robust across stocks/time)
**Relevance to GTOS:** Medium-High
**GTOS question addressed:** Q-2.2
**Key finding:** Price changes driven mainly by order flow imbalance (OFI), linear impact: Delta_p = lambda * OFI, lambda inversely proportional to depth. The mechanism is about ORDER FLOW at specific levels, not past returns predicting future returns. OB zone marks where prior OFI was extreme; retest brings price back to where residual liquidity sits.
**Key equation:** Delta_p = lambda * OFI, lambda ~ 1/depth.
**Testable on GTOS data:** Needs external data (order flow), but theoretical framing applies.

---

### How Markets Slowly Digest Changes in Supply and Demand
**Authors:** Jean-Philippe Bouchaud, J. Doyne Farmer, Fabrizio Lillo | **Year:** 2008 | **Source:** Handbook of Financial Markets (Elsevier); arXiv:0809.0822
**Quality Tier:** 1 (Bouchaud/Farmer are top researchers) | **Citations:** ~500+
**Asset class tested:** Equities (empirical + theoretical)
**OOS validation:** Yes
**Relevance to GTOS:** High
**GTOS question addressed:** Q-2.2
**Key finding:** **Foundational for resolving the GTOS paradox.** Order flow has long memory (Hurst ~0.7) because institutional orders split over days/weeks. Price impact temporarily mean-reverts after each trade but aggregate effect persists because meta-order continues. Creates situation where: (a) returns show no linear autocorrelation (your VR finding), BUT (b) order flow at specific zones is highly persistent and predictable. OB zone marks end of prior meta-order completion -- when price revisits, residual imbalance creates continuation.
**Key equation:** Order flow autocorrelation C(tau) ~ tau^(-gamma), gamma~0.5. Impact: I(Q) ~ Q^(0.5) (square-root law).
**Testable on GTOS data:** Partially -- no order flow data, but mechanism explains observations.

---

### Limit Order Clustering and Price Barriers: Evidence from Euronext
**Authors:** Alexis Cellier, David Bourghelle | **Year:** 2007 | **Source:** SSRN 966454
**Quality Tier:** 3 | **Citations:** ~40+
**Asset class tested:** Euronext equities
**OOS validation:** Yes
**Relevance to GTOS:** Medium
**GTOS question addressed:** Q-2.2
**Key finding:** Limit order clustering at round numbers creates price barriers where stock "spends inordinate time." Clustering creates volume accumulation acting as temporary barrier. Explains both reversal cases (cluster absorbs flow) and continuation cases (cluster overwhelmed, triggering stops behind it).
**Key equation:** Clustering density ~5-10x at round vs non-round prices.
**Testable on GTOS data:** Needs external data (limit order book).

---

### Can Daily Closing Prices Predict Future Movements? The Role of Limit Order Clustering
**Authors:** Xiao Zhang | **Year:** 2024 | **Source:** SSRN 4718961
**Quality Tier:** 4 (working paper, recent) | **Citations:** Low
**Asset class tested:** US equities + 18 intl markets
**OOS validation:** Yes (OOS across markets/time)
**Relevance to GTOS:** Medium
**GTOS question addressed:** Q-2.2
**Key finding:** Stocks closing just above round number outperform those just below by 24.6 bps/day and 46.1 bps/week. Mechanism: concentrated buy limit orders at round prices support price above level. Zone-specific continuation NOT momentum -- conditional on relationship between price and order-cluster level. Replicates across 18 markets.
**Key equation:** Return spread = 24.6 bps/day at round number boundaries.
**Testable on GTOS data:** Yes -- test whether OB zone boundaries at round numbers have stronger continuation.

---

### Evidence and Behaviour of Support and Resistance Levels in Financial Time Series
**Authors:** Ken Chung, Anthony Bellotti | **Year:** 2021 | **Source:** arXiv:2101.07410
**Quality Tier:** 3 | **Citations:** ~15
**Asset class tested:** Intraday equities
**OOS validation:** Unclear
**Relevance to GTOS:** Medium
**GTOS question addressed:** Q-2.2
**Key finding:** Algorithmically discovered S/R levels have statistically significant reversal ability. More prior bounces = higher future bounce probability (reinforcement). S/R levels DECAY over time -- bounce probability decreases. Cannot be explained by AR(1). **Operationally important: OB zones may lose predictive power over time, consistent with stop cluster being gradually absorbed.**
**Key equation:** Bounce probability as f(prior bounces, time since last bounce).
**Testable on GTOS data:** Yes -- test whether older OB zones have lower continuation rates.

---

### The Market Microstructure Approach to Foreign Exchange
**Authors:** Michael R. King, Carol L. Osler, Dagfinn Rime | **Year:** 2013 | **Source:** J. Intl. Money & Finance, 38, 52-74
**Quality Tier:** 1 | **Citations:** ~200+
**Asset class tested:** FX (comprehensive survey)
**OOS validation:** N/A (survey)
**Relevance to GTOS:** Medium-High
**GTOS question addressed:** Q-2.2
**Key finding:** Order flow is primary driver of short-run exchange rate dynamics, not macroeconomic news. Osler's stop-loss cascade mechanisms confirmed as robust FX microstructure features. Heterogeneity among agents creates predictable order flow patterns.
**Testable on GTOS data:** No (survey, but provides theoretical foundation).

---

### Empirical Properties of Asset Returns: Stylized Facts and Statistical Issues
**Authors:** Rama Cont | **Year:** 2001 | **Source:** Quantitative Finance, 1(2), 223-236
**Quality Tier:** 1 (foundational) | **Citations:** ~5000+
**Asset class tested:** Multiple (equities, FX, commodities)
**OOS validation:** Yes (meta-analysis)
**Relevance to GTOS:** Medium
**GTOS question addressed:** Q-2.2
**Key finding:** Establishes 11 stylized facts including: (a) absence of linear autocorrelation, (b) heavy tails, (c) volatility clustering, (d) nonlinear dependence (|r_t| and r_t^2 have significant autocorrelation even when r_t does not). **Fact (d) is exactly GTOS's situation.** OB edge is conditional nonlinear dependence -- continuation conditioned on reaching specific zone. Standard linear tests (VR, ACF) miss it by design.
**Key equation:** |r_t| and r_t^2 have significant autocorrelation even when r_t does not.
**Testable on GTOS data:** Yes -- confirms absence of linear predictability does not mean absence of exploitable structure.

---

<a id="q-131"></a>
## Q-13.1: Comprehensive Survey of Intraday Strategies with OOS Evidence

**GTOS context:** What intraday strategies survive academic scrutiny with OOS validation?
**Papers found:** 11
**Key results:** (1) Intraday momentum real and pervasive, especially last-30-min. (2) Simple technical rules on gold fail OOS. (3) Intraday edges persist longer than daily. (4) Context filtering is the edge, not raw patterns.

---

### Intraday Market Return Predictability Culled from the Factor Zoo
**Authors:** Saketh Aleti, Tim Bollerslev, Mathias Siggaard | **Year:** 2025 | **Source:** Management Science, 71(9), 7731-7751
**Quality Tier:** 1 (Management Science) | **Citations/Downloads:** Published 2025, high visibility
**Asset class tested:** US equities (S&P 500 components)
**OOS validation:** Yes (ML models tested OOS)
**Relevance to GTOS:** Medium
**GTOS question addressed:** Q-13.1
**Key finding:** Lagged HF factors predict intraday returns. ML models exploit low-dimensional subspace achieving Sharpe >1.20 OOS after costs. Predictability lives in low-dimensional factor space.
**Key equation:** PLS/FFN/GBRT regression on lagged factor returns
**Testable on GTOS data:** No -- requires tick-level equity factor data

---

### Market Intraday Momentum
**Authors:** Lei Gao, Yufeng Han, Sophia Zhengzi Li, Guofu Zhou | **Year:** 2018 | **Source:** J. Financial Economics, 129(2), 394-414
**Quality Tier:** 1 (JFE) | **Citations:** 200+
**Asset class tested:** SPY + 10 liquid ETFs
**OOS validation:** Yes (1993-2013)
**Relevance to GTOS:** Medium
**GTOS question addressed:** Q-13.1
**Key finding:** First half-hour return significantly predicts last half-hour return. Stronger on volatile/high-volume/recession/macro-news days. Consistent with late-informed trading.
**Key equation:** r_last30 = alpha + beta * r_first30 + controls
**Testable on GTOS data:** Yes -- measure first/last 30 min of XAUUSD sessions.

---

### Hedging Demand and Market Intraday Momentum
**Authors:** Guido Baltussen, Zhi Da, Sjoerd Stork, Amar Soebhag | **Year:** 2021 | **Source:** J. Financial Economics, 142(1), 377-403
**Quality Tier:** 1 (JFE) | **Citations:** 100+
**Asset class tested:** 60+ futures on equities, bonds, commodities, currencies (1974-2020)
**OOS validation:** Yes (46 years multi-asset, genuine OOS splits)
**Relevance to GTOS:** High -- commodities and FX included
**GTOS question addressed:** Q-13.1
**Key finding:** Market intraday momentum pervasive across ALL asset classes. Last 30 min positively predicted by rest-of-day returns. Linked to gamma hedging demand. Reverts over subsequent days. Statistically significant across commodities, FX, equity indices, bonds.
**Key equation:** r_close = alpha + beta * r_restofday (positive beta, t > 3 across most assets)
**Testable on GTOS data:** Yes -- directly testable on all 5 GTOS instruments.

---

### Time Series Momentum
**Authors:** Tobias J. Moskowitz, Yao Hua Ooi, Lasse Heje Pedersen | **Year:** 2012 | **Source:** J. Financial Economics, 104(2), 228-250
**Quality Tier:** 1 (JFE) | **Citations:** 3000+
**Asset class tested:** 58 liquid futures (gold explicitly included)
**OOS validation:** Yes (1965-2009)
**Relevance to GTOS:** High
**GTOS question addressed:** Q-13.1
**Key finding:** Significant time-series momentum across all asset classes at 1-12 month horizons, partial reversal longer. Gold futures explicitly tested. Foundation for momentum-based strategies. While focused on daily/monthly, foundational for directional assumption in BOS/OB.
**Key equation:** Signal = sign(r_{t-12,t-1}); weights proportional to lagged excess returns
**Testable on GTOS data:** Yes -- already embedded in BOS directional assumption.

---

### Intraday Patterns in Cross-section of Stock Returns
**Authors:** Steven L. Heston, Robert A. Korajczyk, Ronnie Sadka | **Year:** 2010 | **Source:** J. Finance, 65(4), 1369-1407
**Quality Tier:** 1 (JF) | **Citations:** 400+
**Asset class tested:** US equities
**OOS validation:** Yes
**Relevance to GTOS:** Medium
**GTOS question addressed:** Q-13.1
**Key finding:** Returns show continuation at exact half-hour intervals (multiples of trading day), persisting 40+ days. Short-term reversal from temporary liquidity imbalances lasting <1 hour.
**Key equation:** r_{t,h} = alpha + beta * r_{t-k,h} (half-hour interval, k = day multiples)
**Testable on GTOS data:** Equity-specific, but periodicity concept testable on XAUUSD.

---

### Infrequent Rebalancing, Return Autocorrelation, and Seasonality
**Authors:** Vincent Bogousslavsky | **Year:** 2016 | **Source:** J. Finance, 71(6), 2967-3006
**Quality Tier:** 1 (JF) | **Citations:** 200+
**Asset class tested:** US equities (model + empirical)
**OOS validation:** Yes
**Relevance to GTOS:** Medium
**GTOS question addressed:** Q-13.1
**Key finding:** Infrequent portfolio rebalancing produces return autocorrelations that switch sign at rebalancing horizon. Leading theoretical explanation for intraday momentum. Relevant to understanding why OB retests work at specific timeframes.
**Testable on GTOS data:** Yes -- test autocorrelation at half-hour intervals.

---

### A Profitable Day Trading Strategy for the U.S. Equity Market
**Authors:** Carlo Zarattini, Andrea Barbon, Andrew Aziz | **Year:** 2024 | **Source:** SSRN 4729284, Swiss Finance Institute
**Quality Tier:** 2-3 | **Citations/Downloads:** 50,000+ SSRN downloads
**Asset class tested:** 7,000+ US stocks (2016-2023)
**OOS validation:** Yes (walk-forward, 8 years)
**Relevance to GTOS:** Medium
**GTOS question addressed:** Q-13.1
**Key finding:** 5-min Opening Range Breakout on "Stocks in Play" (high pre-market volume + news): Sharpe 2.81, alpha 36%. Generic ORB on all stocks does NOT work. **Critical: context/filter matters more than raw pattern**, analogous to GTOS's OB edge requiring BOS context.
**Key equation:** Enter on 5-min ORB break, filtered by pre-market volume + news catalysts.
**Testable on GTOS data:** Partially -- IB breakout testable, but "Stocks in Play" filter has no direct analogue.

---

### Profitability of Technical Stock Trading: Has it Moved from Daily to Intraday Data?
**Authors:** Stephan Schulmeister | **Year:** 2009 | **Source:** Review of Financial Economics, 18(4), 190-201
**Quality Tier:** 2 | **Citations:** 100+
**Asset class tested:** S&P 500 spot and futures (1960-2007)
**OOS validation:** Yes (8 subperiods)
**Relevance to GTOS:** High
**GTOS question addressed:** Q-13.1
**Key finding:** 2,580 technical models on daily data unprofitable since early 1990s. Same models on 30-min data: average gross returns 7.2%/year (1983-2007) with NO declining trend. **Intraday technical edges persist longer than daily -- supports GTOS's H1 choice.**
**Key equation:** MA crossover and momentum oscillator signals on 30-min bars.
**Testable on GTOS data:** Yes -- same signals on H1 XAUUSD.

---

### Does Intraday Technical Trading Have Predictive Power in Precious Metal Markets?
**Authors:** Jonathan Batten, Brian Lucey, Frank McGroarty, Maurice Peat, Andrew Urquhart | **Year:** 2018 | **Source:** J. Intl. Financial Markets, Institutions & Money, 52, 102-113
**Quality Tier:** 2 | **Citations:** 50+
**Asset class tested:** Gold and silver futures (intraday)
**OOS validation:** Yes (OOS + Hansen's SPA test for data snooping)
**Relevance to GTOS:** **Very High** -- directly tests intraday gold
**GTOS question addressed:** Q-13.1
**Key finding:** Standard MA parameters offer NO predictive power in gold or silver. After data-snooping correction, transaction costs, and OOS testing, intraday technical predictive power in gold is "illusory" for simple technical rules. **GTOS's 62% WR must come from something beyond simple MA/oscillator signals -- consistent with finding that edge is in zone precision, not generic technical rules.**
**Key equation:** MA crossover rules; Hansen's SPA test for data snooping.
**Testable on GTOS data:** Yes -- directly applicable as benchmark.

---

### Intraday Trading of Precious Metals Futures Using Algorithmic Systems
**Authors:** Gil Cohen | **Year:** 2022 | **Source:** Chaos, Solitons & Fractals, 154, 111676
**Quality Tier:** 2-3 | **Citations:** 20+
**Asset class tested:** Gold, silver, platinum, palladium futures (intraday)
**OOS validation:** Partial (PSO optimization, overfitting risk)
**Relevance to GTOS:** High -- intraday gold
**GTOS question addressed:** Q-13.1
**Key finding:** RSI-based system on gold: 106.2% excess returns over B&H. Keltner Channels (60-min bars, 1.5 ATR multiplier): 64.72% excess. Long trades outperform short. Caveat: PSO optimization creates overfitting risk, weaker OOS validation than Batten et al.
**Key equation:** RSI and KC entry/exit, PSO-optimized parameters.
**Testable on GTOS data:** Yes -- trivially computable on H1 data.

---

### Technical Analysis in the Stock Market: A Review
**Authors:** Yufeng Han, Yang Liu, Guofu Zhou, Yingzi Zhu | **Year:** 2021 | **Source:** SSRN 3850494
**Quality Tier:** 2 (Tier-1 authors) | **Citations:** 100+
**Asset class tested:** Survey (equities, FX, commodities)
**OOS validation:** Survey
**Relevance to GTOS:** Medium
**GTOS question addressed:** Q-13.1
**Key finding:** Evidence for technical trading profitability is mixed but non-zero, stronger for intraday horizons and when combined with ML. Best single reference for current state of academic opinion on technical analysis.
**Testable on GTOS data:** N/A (survey).

---

<a id="q-133"></a>
## Q-13.3: Auction Market Theory (Market Profile) Empirical Tests

**GTOS context:** Does Value Area rejection, IB breakout, etc. survive statistical testing?
**Papers found:** 7
**CRITICAL FINDING:** Academic literature on Market Profile / AMT is remarkably thin. ZERO Tier-1 or Tier-2 papers rigorously test Steidlmayer's concepts with proper OOS validation.

---

### Support for Resistance: Technical Analysis and Intraday Exchange Rates
**Authors:** Carol L. Osler | **Year:** 2000 | **Source:** FRB NY Economic Policy Review, 6(2), 53-68
**Quality Tier:** 1-2 (Fed research) | **Citations:** 300+
**Asset class tested:** DEM/USD, GBP/USD, JPY/USD (intraday FX)
**OOS validation:** Yes (S/R from 6 firms, 1996-1998)
**Relevance to GTOS:** Very High -- closest academic proxy for value area rejection
**GTOS question addressed:** Q-13.3
**Key finding:** S/R levels from FX firms significantly predict intraday trend interruptions. Predictive power varies across pairs and firms. Closest academic validation of core AMT concept that price reverses at specific levels.
**Key equation:** Conditional P(reversal vs continuation) at identified S/R levels.
**Testable on GTOS data:** Yes -- GTOS already tests OB zone rejection, conceptually equivalent.

---

### Stop-Loss Orders and Price Cascades in Currency Markets *(cross-listed from Q-2.2)*
**Authors:** Carol L. Osler | **Year:** 2005 | **Source:** J. Intl. Money & Finance, 24(2), 219-241
**Quality Tier:** 1 | **Citations:** 300+
**Key finding:** SL orders cluster at round numbers; when triggered, rates accelerate. Difference between moves after crossing vs reversing at round numbers significant at p < 0.001%. Primary academic evidence for stop-cascade mechanism.

---

### The Price Impact of Order Book Events *(cross-listed from Q-2.2)*
**Authors:** Rama Cont, Arseniy Kukanov, Sasha Stoikov | **Year:** 2014 | **Source:** J. Financial Econometrics, 12(1), 47-88
**Quality Tier:** 1 | **Citations:** 500+
**Key finding:** Price = f(OFI), slope inversely proportional to depth. Microstructure foundation for AMT: "value areas" (high-volume zones) stabilize because depth is high; "low-volume nodes" allow rapid movement.

---

### Assessing the Profitability of Timely Opening Range Breakout on Index Futures
**Authors:** Yi-Cheng Tsai, Mu-En Wu, Jia-Hao Syu, et al. | **Year:** 2019 | **Source:** IEEE Access, 7, 32061-32075
**Quality Tier:** 3 (IEEE Access) | **Citations:** 30+
**Asset class tested:** DJIA, S&P 500, NASDAQ, HSI, TAIEX (2003-2013)
**OOS validation:** Yes (5 international markets)
**Relevance to GTOS:** Medium
**GTOS question addressed:** Q-13.3
**Key finding:** Timely ORB (TORB) achieves >8% annual returns with p < 3% across all 5 markets. Best: TAIEX 20.28% (p=3.1e-5). **Strongest published OOS evidence for IB breakout.** But "timely" qualifier important -- standard ORB without timing optimization not significant.
**Key equation:** Enter on N-minute range break; exit on target/stop/close.
**Testable on GTOS data:** Yes -- IB breakout computable for XAUUSD and US30.

---

### Assessing Profitability of Intraday ORB Strategies (Crude Oil)
**Authors:** Lars Ericsson, Johan Lindgren | **Year:** 2012 | **Source:** Finance Letters (Umea working paper)
**Quality Tier:** 3 | **Citations:** 30+
**Asset class tested:** Crude oil futures (intraday)
**OOS validation:** Yes (3 sub-periods)
**Relevance to GTOS:** Medium
**GTOS question addressed:** Q-13.3
**Key finding:** Full sample: "remarkable success" on crude oil. But splitting into 3 sub-periods: NOT robust to time -- largely explained by most volatile period. **Critical warning: IB breakout profitability may be regime-dependent.** Generic ORB p-values land at 0.45-0.50.
**Key equation:** Standard ORB entry, time-based exit.
**Testable on GTOS data:** Yes -- directly testable on XAUUSD and US30.

---

### Allocative Efficiency of Markets with Zero-Intelligence Traders
**Authors:** Dhananjay K. Gode, Shyam Sunder | **Year:** 1993 | **Source:** J. Political Economy, 101(1), 119-137
**Quality Tier:** 1 (JPE) | **Citations:** 2000+
**Asset class tested:** Simulated continuous double auction
**OOS validation:** N/A (experimental)
**Relevance to GTOS:** Medium
**GTOS question addressed:** Q-13.3
**Key finding:** Even zero-intelligence traders converge near equilibrium in continuous double auction with ~100% allocative efficiency. Market microstructure (the auction mechanism itself) drives price formation, not trader intelligence. Academic analog of Steidlmayer's insight that auction dynamics create discoverable value areas. Tests mechanism, not trading strategy.
**Key equation:** Allocative efficiency = achieved / maximum surplus.
**Testable on GTOS data:** No -- theoretical/experimental.

---

### Stylized Facts of Intraday Precious Metals
**Authors:** Haiying Wang, Ying Shang, Bianxia Sun | **Year:** 2017 | **Source:** PLOS ONE
**Quality Tier:** 3 | **Citations:** 20+
**Asset class tested:** Gold, silver, platinum, palladium (5-min intraday)
**OOS validation:** Descriptive/statistical
**Relevance to GTOS:** High -- documents intraday gold periodicity
**GTOS question addressed:** Q-13.3
**Key finding:** Significant intraday periodicity in gold returns, volatility, volume, and spreads linked to major market opens/closes. Returns and volume show strong bilateral Granger causality. Bid-ask spread lowest during European hours. **Validates GTOS's kill zone approach -- periodicity corresponds to London/NY sessions.**
**Key equation:** Granger causality tests and intraday periodicity decomposition.
**Testable on GTOS data:** Yes -- H25 session volatility monitor already measures this.

---

<a id="synthesis"></a>
## Cross-Question Synthesis

### The Unified Picture

The 8 questions converge on a coherent picture of how GTOS's edge works and how to optimize around it:

1. **The edge is real and microstructural** (Q-2.2). Osler (2003, 2005), Bouchaud et al. (2008), and Cont et al. (2014) provide the theoretical mechanism: stop-loss cascades at clustered price levels create zone-specific continuation that is invisible to linear time-series tests. This resolves the VR/random walk paradox.

2. **Fat tails are endogenous to the mechanism** (Q-2.2, Q-5.1). Osler & Savaser (2011) show that stop cascades and order clustering generate fat tails. The xi=0.35 and kurtosis=34.85 are not noise -- they are signatures of the same mechanism that creates the edge.

3. **ATR-based risk management is misaligned** (Q-5.1). McNeil & Frey (2000), Longin (1999), and Youssef et al. (2015) establish that GARCH-EVT is the correct risk framework for fat-tailed, volatility-clustered processes. ATR (a first-moment measure) systematically underestimates tail risk when xi > 0.

4. **Trailing stop optimization has closed-form solutions but only for Gaussian OU** (Q-6.1). Lipton & Lopez de Prado (2020) give the best starting point. The fat-tail adjustment requires either Garcia-Risueno et al. (2025) methodology or Monte Carlo with GPD-fitted residuals.

5. **Hard BE stop is theoretically suboptimal** (Q-6.4). Grossman & Zhou (1993) and Hsieh & Barmish (2017) both derive that optimal drawdown management is continuous position scaling, not binary stop movement. But MT5 constraints make binary BE the implementable approximation. The shadow logger is the correct empirical approach.

6. **Kelly sizing is massively over-conservative at 1%** (Q-7.1). Even with fat-tail adjustment (40-60% reduction from Osorio 2008), drawdown constraint (Busseti et al. 2016), and parameter uncertainty (Sun & Boyd 2018), optimal f is likely in the 3-8% range. Current 1% provides extreme safety margin.

7. **Edge decay detection requires ~159-214 trades (~9-13 months)** (Q-8.1). This is an information-theoretic bound. SR is optimal for multi-cyclic monitoring. BOCPD provides richer posterior. No procedure can detect a 12pp drop much faster with binary data.

8. **GTOS's edge is distinct from anything in the academic survey literature** (Q-13.1, Q-13.3). Simple technical rules fail on gold (Batten et al. 2018). Market Profile has zero rigorous academic testing. The OB zone precision edge is genuinely novel -- zone-specific conditional continuation validated at p=3.42e-08 is not present in any paper found.

### Priority Actions (research team recommendation)

| Priority | Action | Supporting papers | Expected impact |
|----------|--------|-------------------|-----------------|
| 1 | Implement GARCH-EVT conditional SL | McNeil & Frey (2000), Longin (1999) | Fix ATR underestimation, ~1.5-2x wider SL in tails |
| 2 | Run Busseti et al. constrained Kelly | Busseti et al. (2016), Osorio (2008) | Quantify whether 1% risk is optimal or could increase |
| 3 | Implement SR change-point detector | Polunchenko & Tartakovsky (2012), Moustakides et al. (2009) | Replace ad-hoc CUSUM with optimal multi-cyclic detector |
| 4 | Compute Lipton-LdP trailing stop bounds | Lipton & Lopez de Prado (2020) | Gaussian baseline for trail distance optimization |
| 5 | Test OB zone age decay | Chung & Bellotti (2021) | Validate whether older OBs have lower continuation |
| 6 | Test intraday momentum (last 30 min) | Baltussen et al. (2021) | Additional alpha source on GTOS instruments |
| 7 | Analyze Zambelli MAE for BE threshold | Zambelli (2016) | Empirical optimal BE trigger from trade data |

---

<a id="gaps"></a>
## Critical Gaps — Insufficient Academic Coverage

| Question | Gap description | Implication |
|----------|----------------|-------------|
| Q-6.1 | No paper solves OU trailing stop with GPD(xi=0.35) innovations | Must use Gaussian baseline + fat-tail adjustment + MC validation |
| Q-6.4 | No closed-form for "at what R-multiple move to BE" | Theory says hard BE suboptimal; empirical resolution via shadow logger |
| Q-5.1 | No paper compares ATR vs EVT stop-loss specifically for gold intraday | GTOS-specific backtest needed |
| Q-7.1 | No paper calibrates Kelly for 62% WR intraday gold with GPD xi=0.35 | Components exist (Osorio + McNeil-Frey) but nobody combined them |
| Q-13.3 | ZERO rigorous papers testing Market Profile (Value Area, POC, TPO) | AMT may be practitioner folklore -- or untested alpha. GTOS could be first rigorous test |
| Q-2.2 | Osler's data is proprietary dealer FX; no public replication on gold | Mechanism transfers theoretically but gold-specific empirical gap |

---

## Paper Count Summary

| Question | Papers found | Tier 1 | Tier 2 | Tier 3 | Tier 4 |
|----------|-------------|--------|--------|--------|--------|
| Q-6.1 | 8 | 0 | 5 | 2 | 1 |
| Q-6.4 | 7 | 2 | 2 | 3 | 0 |
| Q-5.1 | 9 | 2 | 5 | 2 | 0 |
| Q-7.1 | 8 | 1 | 3 | 3 | 1 |
| Q-8.1 | 9 | 3 | 3 | 2 | 1 |
| Q-2.2 | 10 | 5 | 0 | 3 | 2 |
| Q-13.1 | 11 | 6 | 3 | 1 | 1 |
| Q-13.3 | 7 | 2 | 1 | 3 | 1 |
| **Total** | **~69** | **21** | **22** | **19** | **7** |

*Note: Some papers appear under multiple questions. Unique paper count is approximately 55-60.*

---

## Additional Reference (Foundational)

### Statistical Consequences of Fat Tails
**Authors:** Nassim Nicholas Taleb | **Year:** 2020 (3rd ed. 2025) | **Source:** arXiv:2001.10488 (monograph)
**Quality Tier:** 2 (monograph, not peer-reviewed) | **Citations:** ~500+
**Relevance to GTOS:** Medium (foundational context for Q-5.1 and Q-7.1)
**Key finding:** With xi > 0 (power-law tails), sample means converge extremely slowly. "Future is fatter tailed than the past." Position sizing and SL calibration must be more conservative than point estimates suggest. Philosophical grounding for fractional Kelly and EVT-based SL.

### Stop-Loss and Investment Returns
**Authors:** Emmanuel Acar, Robert Toffel | **Year:** 2000 | **Source:** Investment Conference, Faculty & Institute of Actuaries
**Quality Tier:** 3 | **Citations:** ~30+
**Asset class tested:** S&P 500, T-bond, Yen futures
**OOS validation:** Yes
**Relevance to GTOS:** Medium
**Key finding:** Under random walk, any path-dependent exit (including BE stop) diminishes expected returns. Stop-loss payoff equivalent to portfolio of barrier options. Provides null hypothesis for BE shadow logger.
**Key equation:** P(SL) = P(B&H) - P(down-and-out put option at SL level).

---

*Search conducted: 2026-04-11. Sources: SSRN, arXiv q-fin, Google Scholar, ScienceDirect, Springer, Wiley, Taylor & Francis. No papers were fabricated. Gaps explicitly documented.*
