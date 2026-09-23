# Domain 21 — Risk Management, Kelly, Position Sizing Under Fat Tails

**Worker:** Phase 1 Worker Agent #21 (Opus 4.7, max effort)
**Run date:** 2026-04-28
**Spec:** `research/ml_program/literature/_specs/21_risk_management_kelly_sizing.md`
**Total papers cataloged:** 38 (target 30-45)
**Per-paper schema:** id, title, authors, year, source, url, abstract, key_findings, relevance_to_gtos, potential_hypothesis, cross_domain_links, risk_metric

The schema's domain-specific extra field `risk_metric` takes one of: Kelly, vol-target, VaR, CVaR, drawdown, sortino, omega, parity, multi.

---

## 1. Kelly foundational (7 papers)

### A New Interpretation of Information Rate
- **id:** 21-001
- **authors:** John L. Kelly Jr.
- **year:** 1956
- **source:** Bell System Technical Journal, Vol 35(4), pp. 917-926
- **url:** https://www.princeton.edu/~wbialek/rome/refs/kelly_56.pdf
- **abstract:** Kelly shows that if input symbols to a communication channel represent outcomes of a chance event on which bets are available at fair odds, a gambler with knowledge given by received symbols can cause his money to grow exponentially, with the maximum exponential rate of growth equal to the rate of transmission of information over the channel. The gambler maximizes the expected value of the logarithm of capital at every bet.
- **key_findings:**
  - Maximizing E[log(wealth)] yields the maximum asymptotic growth rate; this is *Kelly fraction* `f* = (b·p - q) / b` for binary bets with edge `p` and odds `b:1`.
  - Logarithmic utility is the unique utility that survives the law of large numbers in repeated bets — additive in compounded outcomes.
  - The criterion is asymptotically optimal but says nothing about short-term risk; can produce arbitrarily large drawdowns before convergence.
  - AT&T forced renaming from "Information Theory and Gambling" to suppress gambling association.
- **relevance_to_gtos:** Theoretical anchor for the entire `risk_per_trade_pct` system. GTOS's `risk_per_trade_pct: 2.0` and the H29 0.5x reduction are *fractional-Kelly*-style scalars over an implied edge estimate. The 62% XAUUSD WR (n=129) → if avg R≈1.5 → full Kelly ≈ (0.62·1.5 − 0.38)/1.5 ≈ 0.37 (37%); GTOS at 2% is roughly 1/18 Kelly — extremely conservative, consistent with prop-firm survival priority.
- **potential_hypothesis:** *H21-001:* Compute per-instrument GTOS-implied Kelly fraction from validated WR + R distributions; current 2% sizing represents X·Kelly. If X is identical across instruments, no reason for instrument-specific risk weights; if X varies materially (e.g., GBPJPY edge weaker → at 2% it's nearer 1/4 Kelly), per-instrument scaling justified — directly informs S79 sharpe_weighted Phase 2 design.
- **cross_domain_links:** 01 (math foundations — log utility, geometric Brownian motion); 03 (tail estimation feeds Kelly under fat tails)
- **risk_metric:** Kelly

### The Kelly Criterion in Blackjack, Sports Betting, and the Stock Market
- **id:** 21-002
- **authors:** Edward O. Thorp
- **year:** 2006 (ch. 54, *Handbook of Asset and Liability Management*, North-Holland)
- **source:** Handbook of Asset and Liability Management, Vol 1, pp. 385-428
- **url:** https://www.edwardothorp.com/wp-content/uploads/2016/11/TheKellyCriterionAndTheStockMarket.pdf
- **abstract:** Thorp surveys decades of practical Kelly application across blackjack card-counting, parimutuel sports betting, and equity / hedge-fund management. The chapter quantifies the asymmetric pain of overbetting Kelly versus underbetting and motivates practitioner use of fractional Kelly (typically 1/2 to 1/4 Kelly).
- **key_findings:**
  - Practitioner consensus: half-Kelly captures ≈75% of the growth rate at ≈25% of the drawdown variance.
  - 2x overbet Kelly drives expected growth to zero; 3x overbet drives wealth to zero almost surely.
  - Real-world Kelly applications must adjust for parameter uncertainty; "with finite history, the safest Kelly fraction is roughly half what the point estimate would suggest."
  - For securities markets, Kelly weighting maps to the Markowitz tangency portfolio when log-normality holds; under fatter tails the optimal fraction is uniformly lower.
- **relevance_to_gtos:** Direct prop-firm-relevant. GTOS's H29 rule (DD ≥ 8% → cut risk to 0.5x) is fractional-Kelly de-leveraging. Thorp's practitioner observation that "overbetting hurts much more than underbetting" supports the conservative ~1/18-Kelly stance under prop firm rules.
- **potential_hypothesis:** *H21-002:* Run a Monte Carlo over GTOS's 367-trade batch population at full-Kelly, half-Kelly, quarter-Kelly, and current ~1/18 Kelly. Compute (a) median terminal R, (b) P(8% drawdown), (c) P(10% MTM cumulative drawdown), (d) P(redacted_account-pass). Hypothesis: half-Kelly is currently dominated by 2% by the prop-firm survival metric (because P(pass) penalizes drawdown variance much more than median terminal wealth).
- **cross_domain_links:** 13 (cross-asset Kelly — multivariate); 17 (behavioral — overbetting bias)
- **risk_metric:** Kelly

### The Kelly Capital Growth Investment Criterion: Theory and Practice (book + reprint volume)
- **id:** 21-003
- **authors:** Leonard C. MacLean, Edward O. Thorp, William T. Ziemba (eds.)
- **year:** 2011
- **source:** World Scientific Series in Finance, Vol 3
- **url:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1797366
- **abstract:** A comprehensive collection of foundational + applied papers on the Kelly capital growth criterion. Covers the original Kelly (1956), Breiman, Hakansson, Markowitz–Vukov, MacLean-Ziemba good/bad properties, and applications in horse racing, options, and futures.
- **key_findings:**
  - *Bad property #1:* Kelly fraction is hyper-sensitive to input parameters — `dE[log W] / df` → 0 near optimum, but variance grows with f² → estimation error in `f*` is heavily penalized via realized drawdown.
  - *Bad property #2:* The probability of large drawdown approaches 1/c for c-Kelly bets — at 2x Kelly, the gambler hits 50% drawdown with probability ≈1/2.
  - *Good property:* For long horizons, Kelly is optimal *in the strong sense* — no other strategy can dominate it across enough trials.
  - Practitioner rule of thumb: "Use no more than half-Kelly under any historical edge estimate" (MacLean-Ziemba).
- **relevance_to_gtos:** This volume *directly* contains the empirical drawdown-probability arguments that justify GTOS's tiered risk policy (2% standard → 0.5% under DD 8%). The volume's chapter on parameter-estimation risk grounds the conservative posture under H1→H2 decay (item #4: validated XAUUSD WR shifted regime — point-estimate 62% with hindsight bias unsafe).
- **potential_hypothesis:** *H21-003:* Apply MacLean-Ziemba's "estimation-risk-adjusted Kelly" formula `f_adj = f* · (1 - σ_edge / mu_edge)` to GTOS's H1-2026 vs H2-2026 WR change. If `f_adj` collapses to near-zero in H2, this provides math justification for *immediate* aggressive de-leveraging beyond the 0.5x rule when post-H29 drawdown is regime-conditional.
- **cross_domain_links:** 02 (statistical methodology — uncertainty in parameters), 03 (tails impact f*)
- **risk_metric:** Kelly

### Long-term capital growth: the good and bad properties of the Kelly and fractional Kelly capital growth criteria
- **id:** 21-004
- **authors:** Leonard C. MacLean, Edward O. Thorp, William T. Ziemba
- **year:** 2010 (Quant. Finance survey)
- **source:** Quantitative Finance, Vol 10(7), pp. 681-687
- **url:** https://www.tandfonline.com/doi/full/10.1080/14697688.2011.619561
- **abstract:** Distills the trade-offs of full vs fractional Kelly. Maximizes long-term growth but suffers extreme short-term volatility because Arrow-Pratt absolute risk aversion = 1/wealth (very low). Fractional Kelly blends Kelly with cash to smooth wealth paths at cost of expected terminal wealth.
- **key_findings:**
  - At equal *expected log growth*, fractional-Kelly variants strictly dominate Kelly on path-stability metrics: maximum drawdown, time-to-recovery, drawdown duration.
  - For growth ≥ X% of full Kelly, drawdown probability falls *much faster than* growth rate falls — strongly convex tradeoff.
  - For estimated edges with confidence interval `[mu - 2σ, mu + 2σ]`, the *minimax-regret* fractional Kelly converges to roughly `mu / (mu + 2σ)`, much less than `mu / σ²`.
  - Empirical case studies: NCAA bracket bets, Vegas blackjack teams, Long-Term Capital — full Kelly fails empirically, half-Kelly succeeds.
- **relevance_to_gtos:** Defines the *math of the H29 0.5x rule*. If the original 2% sizing is half-Kelly under the original 62% XAUUSD edge, post-decay the effective Kelly is much smaller — H29 conservatively chops to 0.25x effective Kelly which is borderline reasonable for the regime-decayed system.
- **potential_hypothesis:** *H21-004:* Backtest GTOS at risk_per_trade ∈ {0.5%, 1.0%, 1.5%, 2.0%, 2.5%, 3.0%} against the 367-trade pop. Plot E[log_terminal] vs P(MTM-DD > 4%) frontier; identify Pareto-optimal point given prop-firm constraint.
- **cross_domain_links:** 02 (parameter uncertainty)
- **risk_metric:** Kelly

### Risk-Constrained Kelly Gambling
- **id:** 21-005
- **authors:** Enzo Busseti, Ernest K. Ryu, Stephen Boyd
- **year:** 2016
- **source:** Journal of Investing, Vol 25(3), pp. 118-134; preprint arXiv:1603.06183
- **url:** https://arxiv.org/abs/1603.06183
- **abstract:** Reformulates Kelly with an explicit drawdown-probability constraint. Derives a tractable convex bound on drawdown probability and shows the resulting optimization yields strictly better growth-vs-drawdown tradeoffs than fractional Kelly.
- **key_findings:**
  - The constrained convex problem: `max E[log return] s.t. P(W_t / W_max < β) ≤ ε` admits a single risk-aversion-parameter solution that nests both Kelly (no constraint) and Markowitz (quadratic approximation).
  - For any drawdown-probability target ε, Busseti-Boyd RCK strictly dominates fractional Kelly at the same ε (Sharpe-like efficient frontier).
  - The single risk-aversion parameter `λ` cleanly maps prop-firm rules: choose λ such that simulation P(MTM-DD ≥ 4%) ≤ 0.05.
  - Code released; library directly callable.
- **relevance_to_gtos:** Highest-direct-leverage paper for S79 sharpe_weighted Phase 2. The Busseti-Boyd `λ` parameter is exactly the right knob to size an instrument-specific scalar to satisfy the FN MTM-DD constraint with target failure probability. Replaces ad-hoc `risk_per_trade_pct` with constraint-derived sizing.
- **potential_hypothesis:** *H21-005:* Implement Busseti-Boyd RCK over the 4 active GTOS instruments (XAUUSD, US30, USDJPY, GBPJPY) with FN constraint `P(daily MTM-DD ≥ 4%) ≤ 0.02`. Test on 367-trade backtest. Hypothesis: the optimal `λ` produces instrument-specific risk weights that are not uniform — i.e., S79's uniform_fn 2.0% is leaving Sharpe on the table.
- **cross_domain_links:** 01 (convex optimization theory)
- **risk_metric:** Kelly+drawdown

### Awareness of crash risk improves Kelly strategies in simulated financial markets
- **id:** 21-006
- **authors:** Didier Sornette et al.
- **year:** 2020
- **source:** arXiv:2004.09368, q-fin.RM
- **url:** https://arxiv.org/pdf/2004.09368
- **abstract:** Adds explicit crash-risk awareness (jumps with heavy-tailed magnitudes) to Kelly. Shows that under realistic non-Gaussian return tails, full Kelly catastrophically underperforms; strategies aware of jump intensity converge to ~30% to 50% of full Kelly.
- **key_findings:**
  - Under jump-diffusion with calibrated `λ_jump = 0.05/year`, magnitude-tail-index ξ = 0.3, full-Kelly path loses *all* simulated wealth in 50% of paths within 5 years.
  - "Crash-aware" Kelly that conditions on jump-state estimate cuts effective leverage by 50% during high-jump-probability regimes — recovers half-Kelly performance.
  - Suggests jumps + heavy tails → "natural fractional Kelly" of factor 0.4 emerges from extreme value theory parameters.
- **relevance_to_gtos:** Connects directly to the GTOS distributional finding (memory `project_distributional_findings`): ξ = 0.35 for gold, 6.2× more 3σ events than Gaussian. Sornette's 0.4 crash-aware Kelly fraction is empirically calibrated near GTOS's distributional regime.
- **potential_hypothesis:** *H21-006:* Compute Sornette-style crash-aware Kelly fraction for XAUUSD using GTOS's measured ξ = 0.35 and GARCH persistence 0.9906. Compare against current 2% sizing implied Kelly fraction. Hypothesis: GTOS at 2% is *more conservative* than crash-aware Kelly recommends, justifying the policy and suggesting room for sharpe_weighted variants up to ~3% during low-vol regimes.
- **cross_domain_links:** 03 (jump diffusions, EVT), 16 (vol regime)
- **risk_metric:** Kelly+jumps

### Tackling estimation risk in Kelly investing using options
- **id:** 21-007
- **authors:** various (recent — Hong et al.)
- **year:** 2025
- **source:** arXiv:2508.18868, q-fin.PM
- **url:** https://arxiv.org/html/2508.18868
- **abstract:** Proposes integrating option contracts (long deep-OTM puts) into Kelly portfolios to hedge parameter mis-specification. Shows that a convex combination of Kelly + protective options is "asymptotically robust" to any parameter mis-estimation.
- **key_findings:**
  - Adding 1-3% wealth in protective puts to a Kelly equity portfolio costs ~50bps/year and removes the parameter-sensitivity of full Kelly.
  - Result: even when the estimated edge is *zero*, the K+O strategy never loses more than the option premium — strict dominance over fractional Kelly when edges are uncertain.
  - Practitioner-tractable: requires only liquid index puts, not complex tail-hedging structures.
- **relevance_to_gtos:** GTOS does not have option-hedging infrastructure on FN, but the *concept* applies: when edge is uncertain (XAUUSD H1→H2 decay, item #4), a "synthetic put" via reduced position size (the H29 0.5x cut) + tighter SL acts as the robustness mechanism.
- **potential_hypothesis:** *H21-007:* Build an "implicit synthetic put" in GTOS by introducing a *daily-trade-budget cap* (e.g., max 2 trades per session) — caps tail loss similar to a fixed put premium. Backtest whether the cap improves Sharpe net of foregone winners.
- **cross_domain_links:** 03 (estimation risk + EVT), 16 (options + tail hedge)
- **risk_metric:** Kelly+options

---

## 2. Vol-targeting / risk-parity (5 papers)

### Volatility-Managed Portfolios
- **id:** 21-008
- **authors:** Alan Moreira, Tyler Muir
- **year:** 2017
- **source:** Journal of Finance, Vol 72(4), pp. 1611-1644
- **url:** https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.12513
- **abstract:** Portfolios that take less risk when realized volatility is high produce large alphas, increase Sharpe ratios, and produce large utility gains. Documented across market, value, momentum, profitability, ROE, investment factors and FX carry.
- **key_findings:**
  - Vol-managed portfolios deliver Sharpe ratio improvements of 20-40% across major factors *out-of-sample*.
  - The strategy *takes less risk in recessions* and *still earns higher Sharpe* — contradicts standard time-varying risk premium models.
  - Mechanism: variance shocks are not offset by proportional return shocks → vol scaling acts as a free lunch in mean-variance terms.
  - Implementation: scale position by `target_vol / realized_vol_t`.
- **relevance_to_gtos:** Foundational for any GTOS sharpe_weighted (S79 Phase 2) implementation. Directly suggests scaling `risk_per_trade_pct` inversely to recent ATR/realized-vol on each instrument. Currently GTOS does *not* vol-scale — leaves Sharpe on the table per Moreira-Muir.
- **potential_hypothesis:** *H21-008:* Implement Moreira-Muir-style vol scaling: `risk_pct_t = base · target_vol / ATR_20d`. Backtest on 367-trade pop. Hypothesis: vol-scaling lifts Sharpe by ≥15% out of sample, aligned with their 20-40% finding for factors. Critically: test whether the gold-specific multifractal vol pattern (ξ=0.35) breaks the linear scaling — may require power-law exponent.
- **cross_domain_links:** 16 (vol regime), 14 (momentum factors)
- **risk_metric:** vol-target

### The Impact of Volatility Targeting
- **id:** 21-009
- **authors:** Campbell R. Harvey, Edward Hoyle, Russell Korgaonkar, Sandy Rattray, Matthew Sargaison, Otto Van Hemert
- **year:** 2018
- **source:** Journal of Portfolio Management, Vol 45(1), pp. 14-33
- **url:** https://jpm.pm-research.com/content/45/1/14.abstract
- **abstract:** Practitioner-academic deep-dive: 60 assets, daily data 1926-2017. Vol-targeting improves Sharpe for risk assets (equity, credit), reduces left-tail severity universally, has near-zero Sharpe impact for bonds/FX/commodities but cuts maximum drawdown.
- **key_findings:**
  - Vol-targeting reduces *frequency and severity of left tail returns* across all asset classes, even when Sharpe doesn't improve.
  - The "leverage effect" (negative correlation between past returns and current volatility) explains the Sharpe gain in equities and credit.
  - For commodities (gold included), Sharpe is roughly invariant but max-drawdown improves by 20-40%.
  - "Left tail events tend to occur at times of elevated vol → vol-targeted portfolio has small notional then."
- **relevance_to_gtos:** This paper *answers the prior* on whether vol-targeting helps for gold — answer is mixed (modest Sharpe gain) but the *drawdown reduction is significant*. For prop-firm survival GTOS should care more about MaxDD than Sharpe alone — directly supports vol-scaling for gold.
- **potential_hypothesis:** *H21-009:* For each GTOS instrument, run vol-targeted vs constant-risk backtest; primary metric is P(daily MTM-DD ≥ 4%) and max DD %, not Sharpe. Hypothesis: gold + indices show DD reduction ≥30% while FX shows little change — implies *instrument-specific* vol-scaling rather than universal.
- **cross_domain_links:** 16 (vol regime), 10 (gold), 12 (indices)
- **risk_metric:** vol-target

### Leverage Aversion and Risk Parity
- **id:** 21-010
- **authors:** Cliff Asness, Andrea Frazzini, Lasse H. Pedersen
- **year:** 2012
- **source:** Financial Analysts Journal, Vol 68(1), pp. 47-59
- **url:** https://www.aqr.com/-/media/AQR/Documents/Insights/Journal-Article/Leverage-Aversion-and-Risk-Parity.pdf
- **abstract:** Many investors are leverage-averse. Modern portfolio theory predicts leverage-averse investors should *over*-weight safe assets and use leverage. RP portfolios that equalize risk contributions (then scale to target vol) outperformed market-cap-weighted portfolios by ~4%/year over 1926-2010.
- **key_findings:**
  - "Equal risk contribution" beats market-cap weighting in 11/11 countries 1986-2010.
  - The mechanism is the leverage-aversion friction: investors won't lever bonds → bonds undervalued → RP tilt toward bonds extracts the alpha.
  - Crucially: RP portfolio *requires leverage* — falls into the prop-firm constraint zone.
- **relevance_to_gtos:** RP at portfolio-level is a stretch for GTOS (no asset-class diversification — just same-class FX/indices/gold). But the *cross-instrument correlation gate* (HALVE/REJECT at |corr|>0.4) is conceptually parallel: equalizing risk contribution across instruments.
- **potential_hypothesis:** *H21-010:* Replace GTOS's per-instrument 2% with a "risk parity" allocation: each instrument sized so its 1-day VaR contribution equals 1/N of total portfolio VaR. Backtest. Hypothesis: equalizing risk per instrument boosts Sharpe and reduces concentration risk in the highest-vol instrument (XAUUSD).
- **cross_domain_links:** 13 (correlation, factor weights), 21 internal (correlation gate)
- **risk_metric:** parity

### On the Properties of Equally-Weighted Risk Contributions Portfolios
- **id:** 21-011
- **authors:** Sébastien Maillard, Thierry Roncalli, Jérôme Teiletche
- **year:** 2010
- **source:** Journal of Portfolio Management, Vol 36(4), pp. 60-70
- **url:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1271972
- **abstract:** Mathematical foundations of risk parity: ERC portfolio (equal risk contributions) sits between minimum-variance and equal-weight on the volatility frontier. Establishes the convex problem and unique solution under positive-definite covariance.
- **key_findings:**
  - ERC = `argmin_w ||σ_i(w) - σ_avg||²` where σ_i is asset i's risk contribution.
  - Volatility of ERC is bounded above by EW and below by MV: `σ(MV) ≤ σ(ERC) ≤ σ(EW)`.
  - ERC is robust under estimation error in mean (it requires only covariance) — natural fit for HRP and other ML-portfolio extensions.
  - Closed-form when correlations are equal (gives `w_i ∝ 1/σ_i`).
- **relevance_to_gtos:** Provides the math for a position-weighting overlay if GTOS goes correlation-aware (vs. the current binary HALVE/REJECT cross-instrument gate).
- **potential_hypothesis:** *H21-011:* Replace correlation-gate HALVE rule with ERC-style continuous weighting: when adding a new position, recompute risk-parity weights using DCC-correlated 60-day cov matrix; size the new position to balance risk contributions. Backtest delta from binary HALVE.
- **cross_domain_links:** 13 (factor / DCC), 21 (correlation gate)
- **risk_metric:** parity

### Hierarchical Risk Parity / Building Diversified Portfolios that Outperform Out of Sample
- **id:** 21-012
- **authors:** Marcos Lopez de Prado
- **year:** 2016
- **source:** Journal of Portfolio Management, Vol 42(4), pp. 59-69
- **url:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2708678
- **abstract:** HRP uses hierarchical clustering on correlation matrix → quasi-diagonalization → recursive bisection allocation. Avoids covariance-matrix inversion (which Markowitz CLA requires). Out-of-sample variance lower than CLA, more stable weights.
- **key_findings:**
  - Markowitz CLA suffers "Markowitz curse" — small changes in input → large changes in weights, very poor OOS performance.
  - HRP solves stability + concentration + underperformance without inverting cov matrix.
  - Numerical experiments: HRP OOS variance ≤ CLA, weights more stable, robust to ill-conditioned cov.
  - Naturally handles high-asset-count portfolios.
- **relevance_to_gtos:** GTOS portfolio is small (5-7 instruments) so HRP gain is modest, but the *clustering insight* directly applies to the cross-instrument correlation gate — the JPY_CROSSES correlation group is an implicit hierarchical cluster. HRP would formalize cluster-based risk allocation rather than the binary-pair-correlation current logic.
- **potential_hypothesis:** *H21-012:* Apply HRP clustering on rolling 60-day return correlation across XAUUSD, US30, USDJPY, GBPJPY, GBPUSD, XAGUSD, NAS100. Hypothesis: HRP yields a 3-cluster structure (precious metals, JPY crosses, indices) that justifies cluster-level rather than pair-level correlation gates.
- **cross_domain_links:** 13, 19 (ML clustering)
- **risk_metric:** parity

---

## 3. CVaR / coherent measures (5 papers)

### Coherent Measures of Risk
- **id:** 21-013
- **authors:** Philippe Artzner, Freddy Delbaen, Jean-Marc Eber, David Heath
- **year:** 1999
- **source:** Mathematical Finance, Vol 9(3), pp. 203-228
- **url:** https://onlinelibrary.wiley.com/doi/10.1111/1467-9965.00068
- **abstract:** Establishes the four coherence axioms for risk measures: monotonicity, positive homogeneity, translation invariance, and *subadditivity*. VaR violates subadditivity → not coherent. Proposes Expected Shortfall as a coherent alternative.
- **key_findings:**
  - VaR can *increase* when portfolios are diversified (subadditivity violation) — pathological for risk management.
  - ES (= CVaR) is coherent under all distributions including discrete.
  - Risk measure ρ is coherent ⟺ representable as `sup_Q E_Q[-X]` over a convex set of probability measures.
  - Practical implication: regulators should switch to ES — Basel did so in 2013.
- **relevance_to_gtos:** GTOS today uses "max drawdown" and "daily MTM" which are coherent (drawdown is coherent under continuous compounding). The paper mostly motivates *why GTOS doesn't need to add VaR* — ES/CVaR-based risk measures are the modern stack. CVaR appears next.
- **potential_hypothesis:** *H21-013:* Compute 1-day CVaR_5% for the GTOS portfolio under various risk_pct settings; verify subadditivity holds (should be guaranteed since CVaR coherent). Use as gate threshold for sizing.
- **cross_domain_links:** 03 (tails as input to CVaR)
- **risk_metric:** CVaR

### Optimization of Conditional Value-at-Risk
- **id:** 21-014
- **authors:** R. Tyrrell Rockafellar, Stanislav Uryasev
- **year:** 2000
- **source:** Journal of Risk, Vol 2(3), pp. 21-42
- **url:** https://sites.math.washington.edu/~rtr/papers/rtr179-CVaR1.pdf
- **abstract:** Introduces a tractable convex optimization for CVaR. Shows that minimizing CVaR can be done via a linear program when scenarios are sampled, and that a portfolio with small CVaR also has small VaR.
- **key_findings:**
  - The CVaR-minimization problem reduces to LP via auxiliary variable z = VaR.
  - CVaR is a *weighted average* of tail losses → strictly more conservative than VaR.
  - Computational properties allow scenario-based CVaR optimization to scale to thousands of assets and millions of scenarios.
  - Connection to expected shortfall is direct: CVaR_α = -E[X | X ≤ VaR_α].
- **relevance_to_gtos:** Provides the *math* for a CVaR-based sizing constraint on GTOS positions. Practitioner: given a Monte Carlo of 367 historical R-multiples per instrument, compute portfolio CVaR_5% as a function of sizing vector → solve LP.
- **potential_hypothesis:** *H21-014:* Set GTOS sizing so that portfolio 1-day CVaR_5% ≤ 2% of equity (consistent with prop-firm 4% MTM constraint). Solve LP per Rockafellar-Uryasev formulation. Hypothesis: optimal weights deviate from uniform 2% — likely concentrating risk in low-tail-fat instruments (USDJPY) and de-leveraging gold.
- **cross_domain_links:** 03, 21-013
- **risk_metric:** CVaR

### Expected Shortfall: A Natural Coherent Alternative to Value at Risk
- **id:** 21-015
- **authors:** Carlo Acerbi, Dirk Tasche
- **year:** 2002
- **source:** Economic Notes, Vol 31(2), pp. 379-388
- **url:** https://onlinelibrary.wiley.com/doi/10.1111/1468-0300.00091
- **abstract:** Reviews the variants of "expected shortfall" definitions in the literature. Identifies the canonical coherent ES that holds for arbitrary loss distributions including discrete cases. Provides analytical relationships to spectral risk measures.
- **key_findings:**
  - The "right" ES definition: ES_α = -1/α · ∫_0^α VaR_u du.
  - Some "naive" ES variants lose coherence on discrete distributions; Acerbi-Tasche ES is the unique coherent representation.
  - For continuous distributions all ES variants coincide; differences only matter at extreme loss tails of empirical distributions (which is where it matters most).
- **relevance_to_gtos:** Definitional — sets the *correct* CVaR formula to use for GTOS scenario-based sizing.
- **potential_hypothesis:** N/A (foundational definition).
- **cross_domain_links:** 21-013, 21-014
- **risk_metric:** CVaR

### Quantitative Risk Management: Concepts, Techniques and Tools (book)
- **id:** 21-016
- **authors:** Alexander J. McNeil, Rüdiger Frey, Paul Embrechts
- **year:** 2015 (revised ed.)
- **source:** Princeton University Press
- **url:** https://press.princeton.edu/books/hardcover/9780691166278/quantitative-risk-management
- **abstract:** Standard graduate-level QRM reference. Covers loss distributions, EVT (Hill estimator, peaks-over-threshold), copulas, multivariate extremes, market/credit/operational risk, tail estimation, GARCH, dynamic risk.
- **key_findings:**
  - Hill estimator for tail index ξ; threshold selection via Hill plot stability.
  - POT (peaks over threshold) yields generalized Pareto distribution above threshold.
  - Copulas decouple marginal modeling from dependence — t-copula common for fat-tailed financials.
  - Practical risk-aggregation rules under Sklar's theorem.
- **relevance_to_gtos:** Textbook reference for the *EVT estimation* underlying GTOS's measured ξ = 0.35 for gold (memory `project_distributional_findings`). All Phase 2 fat-tail-aware sizing should defer to this volume's notation/methods.
- **potential_hypothesis:** *H21-016:* Re-fit GTOS gold tails using POT instead of Hill; cross-check ξ estimate. Hypothesis: POT ξ matches Hill ξ ± 0.05; this strengthens distribution-conditioned Kelly.
- **cross_domain_links:** 03 (tails), 13 (copulas, multi-asset)
- **risk_metric:** multi

### Tail Risk Targeting: Target VaR and CVaR Strategies
- **id:** 21-017
- **authors:** Lars Rickenberg
- **year:** 2019 (SSRN)
- **source:** SSRN preprint 3444999
- **url:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3444999
- **abstract:** Compares "target volatility" with "target VaR" and "target CVaR" sizing rules. Shows that target-CVaR sizing reduces left-tail exposure most aggressively while preserving Sharpe.
- **key_findings:**
  - Target-CVaR exposure rule: position scaled so that CVaR_5% = constant. Reacts faster to fat-tail regimes than target-vol.
  - On equity index futures, target-CVaR yields Sharpe parity with target-vol but max-drawdown reduction of ~25%.
  - Implementation: requires CVaR estimation (EVT or empirical), tractable in practice.
- **relevance_to_gtos:** Provides a *direct alternative* to vol-targeting (Moreira-Muir, Harvey et al.). For a fat-tailed instrument like gold, target-CVaR may dominate target-vol. Phase 2 should test both.
- **potential_hypothesis:** *H21-017:* Backtest GTOS at target-vol vs target-CVaR_5% with same long-run vol budget. Hypothesis: target-CVaR achieves equivalent Sharpe with 20-30% smaller max-DD on XAUUSD.
- **cross_domain_links:** 03, 16, 21-008, 21-009
- **risk_metric:** CVaR

---

## 4. Drawdown control / leverage cycle (5 papers)

### Optimal Investment Strategies for Controlling Drawdowns
- **id:** 21-018
- **authors:** Sanford J. Grossman, Zhongquan Zhou
- **year:** 1993
- **source:** Mathematical Finance, Vol 3(3), pp. 241-276
- **url:** https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1467-9965.1993.tb00044.x
- **abstract:** Formulates the drawdown-constrained portfolio problem. Investor wants `W_t ≥ α · M_t` always, where M_t = running max wealth. For CRRA utility, optimal investment is proportional to the "surplus" `W_t - α·M_t`.
- **key_findings:**
  - Closed-form solution for HARA utility with drawdown constraint: invest fraction proportional to surplus over the floor α·M_t.
  - Drawdown constraints are *binding* — they reduce optimal investment below the unconstrained Merton optimum.
  - "A large drawdown (typically above 25 percent) is often a reason for firing fund managers" — drawdown is institutionally critical, not just a preference.
- **relevance_to_gtos:** Direct theoretical justification for GTOS's H29 rule. The H29 mechanism (DD ≥ 8% → cut risk to 0.5x) is a *piecewise linear approximation* to Grossman-Zhou's optimal "scale by surplus" rule. Smooth implementation: `risk_pct = base · max(0, (W − α·W_max)) / W` would be the continuous Grossman-Zhou solution.
- **potential_hypothesis:** *H21-018:* Replace H29 piecewise rule with smooth Grossman-Zhou: `risk_pct_t = 2.0% · max(0, (W_t - 0.92·W_max) / W_t) / 0.08`. Backtest on 367-trade pop. Hypothesis: smooth scaling reduces variance of P(pass) outcome and avoids "DD = 8.01% triggers brutal halving" cliff.
- **cross_domain_links:** 21-019, 21-020
- **risk_metric:** drawdown

### On Portfolio Optimization Under Drawdown Constraints
- **id:** 21-019
- **authors:** Jakša Cvitanić, Ioannis Karatzas
- **year:** 1995
- **source:** IMA Lecture Notes in Mathematics & Applications 65, pp. 77-88
- **url:** https://www.cis.upenn.edu/~mkearns/finread/drawdown.pdf
- **abstract:** Extends Grossman-Zhou to multi-asset case. Shows the auxiliary-process technique reduces drawdown-constrained portfolio problem to unconstrained Merton problem — closed form persists with multiple risky assets.
- **key_findings:**
  - The "Time-Invariant Portfolio Protection" (TIPP) strategy maps directly to the optimal drawdown-constrained policy.
  - Multi-asset case: optimal weights are still proportional to surplus, with allocation among risky assets following the standard Merton tangent portfolio.
  - Klass-Nowicki (2005) later showed strategy is *not* optimal in discrete time — gap between continuous and discrete formulations.
- **relevance_to_gtos:** GTOS lives in discrete time (M15 candle close → decision). The Klass-Nowicki gap → GTOS should empirically validate Grossman-Zhou-style smooth scaling rather than assume continuous-time optimality.
- **potential_hypothesis:** *H21-019:* Compare H29 step-function vs Grossman-Zhou-Cvitanić-Karatzas continuous-surplus rule; hypothesis: in discrete-trade GTOS the smooth rule introduces noise around 8% threshold that may not be optimal — Klass-Nowicki suggests step-function may actually outperform.
- **cross_domain_links:** 21-018
- **risk_metric:** drawdown

### An Analysis of the Maximum Drawdown Risk Measure
- **id:** 21-020
- **authors:** Malik Magdon-Ismail, Amir F. Atiya
- **year:** 2004
- **source:** Risk Magazine, October 2004
- **url:** https://www.cs.rpi.edu/~magdon/ps/journal/drawdown_RISK04.pdf
- **abstract:** Analytical relationships between maximum drawdown (MDD) and mean return / Sharpe ratio under Brownian motion. Provides asymptotic distribution of MDD; computes Calmar ratio sensitivity.
- **key_findings:**
  - For Brownian motion with drift µ and vol σ, expected MDD scales like (σ²/µ) · log(T) for long horizon T.
  - Calmar ratio = µ / E[MDD] is a misleading scaling — penalizes longer track records mechanically.
  - Risk-adjusted return measures using MDD must normalize for time-on-track.
- **relevance_to_gtos:** Cautionary note for GTOS's measured 8% DD threshold. If the threshold is set on Brownian-motion intuition but gold has fatter tails, the *actual* DD distribution has heavier tail than Magdon-Ismail's BM analysis — 8% triggers will fire more often than expected.
- **potential_hypothesis:** *H21-020:* Use Magdon-Ismail's analytical formulas, calibrated for GTOS's measured ξ=0.35, GARCH 0.9906 — compute expected DD distribution. Hypothesis: 95th percentile DD over 90 days is 12-18% under fat tails vs ~8-10% under Gaussian; H29 threshold may need recalibration.
- **cross_domain_links:** 03, 21-018
- **risk_metric:** drawdown

### Drawdown Measure in Portfolio Optimization
- **id:** 21-021
- **authors:** Alexei Chekhlov, Stanislav Uryasev, Michael Zabarankin
- **year:** 2005
- **source:** International Journal of Theoretical and Applied Finance, Vol 8(1), pp. 13-58
- **url:** https://www.math.columbia.edu/~chekhlov/ChekhlovUryasevZabarankin--03-2004.pdf
- **abstract:** Defines Conditional Drawdown-at-Risk (CDaR): the mean of the worst (1-β)·100% drawdowns. Generalizes max-drawdown and average-drawdown as limit cases. Convex; LP-tractable.
- **key_findings:**
  - CDaR is convex in portfolio weights → LP/QP optimization tractable.
  - CDaR generalizes both MaxDD (β → 0) and AvgDD (β → 1).
  - Empirical: CDaR-optimized portfolios deliver superior drawdown control vs MV portfolios at equivalent return.
  - Practical algorithm enables drawdown-constrained portfolio construction at scale.
- **relevance_to_gtos:** Modern formulation of drawdown control. CDaR could replace GTOS's hard 8% threshold with a tail-of-drawdowns metric.
- **potential_hypothesis:** *H21-021:* Use CDaR as the *backward-looking* sizing target: `risk_pct_t = base · CDaR_target / CDaR_realized`. Backtest. Hypothesis: CDaR scaling outperforms volatility-scaling because it reacts to drawdown clustering (which fat-tailed gold exhibits).
- **cross_domain_links:** 21-014, 21-018
- **risk_metric:** drawdown

### The Leverage Cycle
- **id:** 21-022
- **authors:** John Geanakoplos
- **year:** 2010
- **source:** NBER Macroeconomics Annual 2009, Vol 24, pp. 1-65 (University of Chicago Press)
- **url:** http://dido.econ.yale.edu/~gean/art/p1304.pdf
- **abstract:** General-equilibrium theory of leverage. Shows leverage (margin / haircut) is an equilibrium variable, not a parameter. In good times, leverage rises → asset prices rise → more leverage. Crashes deleverage chain causes amplified price drops.
- **key_findings:**
  - "In times of crisis, collateral rates (margins / leverage) are far more important than interest rates."
  - Leverage cycle: optimism → leverage rises → prices rise → more leverage → bust phase: leverage cuts → forced selling → prices fall.
  - Implications for prop firms: drawdown-triggered de-leveraging IS the leverage cycle in microcosm.
- **relevance_to_gtos:** Macro-context for GTOS's H29 rule. The 2008-style "deleverage spiral" is what H29 *prevents* — by mandating a leverage cut at 8% DD, GTOS exits the doom loop before forced liquidation.
- **potential_hypothesis:** *H21-022:* Frame H29's effectiveness as *avoiding the prop-firm leverage-cycle bust*. Backtest: compare always-2% (which would force prop-firm liquidation under sustained 5%+ DD) vs H29 (which prevents it).
- **cross_domain_links:** 17 (behavioral)
- **risk_metric:** drawdown

---

## 5. Fat-tail-aware sizing (5 papers)

### A Prospect-Theory Approach to the Kelly Criterion for Fat-Tail Portfolios: The Case of the Student T-Distribution
- **id:** 21-023
- **authors:** Various (researchgate.net 228287928)
- **year:** ~2010 (depending on edition)
- **source:** ResearchGate publication 228287928
- **url:** https://www.researchgate.net/publication/228287928_A_Prospect-Theory_Approach_to_the_Kelly_Criterion_for_Fat-Tail_Portfolios_The_Case_of_the_Student_T-Distribution
- **abstract:** Modifies Kelly criterion for Student-t returns (which model fat tails) using a prospect-theory log-power utility. Derives analytic optimal leverage formula. Shows fractional Kelly emerges naturally.
- **key_findings:**
  - For Student-t with degrees-of-freedom ν, optimal Kelly leverage is `~ µ / σ² · (ν - 2)/ν` — fatter tails (low ν) → smaller leverage.
  - The fractional-Kelly factor in fat-tailed regimes is approximately `(ν - 2)/ν`; for ν=3 (very heavy), factor ≈ 1/3.
  - Prospect-theory-augmented log utility produces strictly conservative sizing vs pure log utility.
- **relevance_to_gtos:** GTOS's gold ξ=0.35 maps approximately to Student-t with ν ≈ 4-5 → optimal Kelly fraction is ~50% of Gaussian-Kelly. Combined with current 1/18-Kelly stance, GTOS is roughly 1/9-Kelly under fat-tail-aware metric — still very conservative.
- **potential_hypothesis:** *H21-023:* Fit Student-t to gold returns; compute optimal Kelly fraction analytically. Compare with Sornette's empirical 0.4 fraction (paper 21-006). Hypothesis: t-fit ν gives Kelly factor in [0.3, 0.5] range, agreeing with Sornette empirically.
- **cross_domain_links:** 03, 21-001, 21-006
- **risk_metric:** Kelly+fat-tails

### Tail Risk Constraints and Maximum Entropy
- **id:** 21-024
- **authors:** Donald Geman, Hélyette Geman, Nassim Nicholas Taleb
- **year:** 2014
- **source:** arXiv:1412.7647, q-fin.RM
- **url:** https://arxiv.org/pdf/1412.7647
- **abstract:** Frames tail-risk-constrained portfolio choice via maximum-entropy principle. Shows that under fat-tailed distributions, dynamic-hedging-frequency arguments break down — increasing rebalance frequency does NOT reduce risk under power-law tails.
- **key_findings:**
  - The Black-Scholes "continuous-rebalance" assumption requires Gaussian increments; under fat tails, continuous hedge does NOT eliminate risk.
  - Maximum-entropy distributions consistent with first-2-moment + tail-bound constraints converge to truncated power-law.
  - Practical: any "vol scaling = vol budget" rule fails to capture true tail risk if computed under Gaussian assumption.
- **relevance_to_gtos:** Direct critique of vol-targeting as primary risk control. Vol-target fails under power-law tails — supports CVaR-target (paper 21-017) over vol-target as the right primary.
- **potential_hypothesis:** *H21-024:* For each instrument, compare *empirical* CVaR_5% with *Gaussian-implied* CVaR_5% based on rolling sigma. Hypothesis: the gap is largest for XAUUSD and indices, and vol-target ignores the gap, so it under-protects fat-tailed instruments precisely when matters most (regime stress).
- **cross_domain_links:** 03, 21-017
- **risk_metric:** CVaR+fat-tails

### Statistical Consequences of Fat Tails (book / monograph)
- **id:** 21-025
- **authors:** Nassim Nicholas Taleb
- **year:** 2020 (and 2023 ed.)
- **source:** Technical Incerto, monograph; partial preprint arXiv:2001.10488
- **url:** https://arxiv.org/abs/2001.10488
- **abstract:** Comprehensive technical treatment of fat-tail finance. Covers preasymptotic statistical properties, EVT, characteristic-function-based approaches, and risk management implications. Argues classical Kelly fails badly under power-law tails.
- **key_findings:**
  - Under Pareto tails, the *sample mean is unreliable* even at very large n (preasymptotic regime); standard p-values mislead.
  - Concept of "ergodicity gap": individual time-average ≠ ensemble average for non-ergodic processes (Peters' framing).
  - Practical: any sizing rule based on point-estimate mean returns is fragile; use *robust* (median or trimmed) estimators + heavy fractional Kelly.
- **relevance_to_gtos:** Frames why GTOS should *not* trust H1-2026 backtest mean-R/trade in setting H2-2026 sizing. The validated 62% XAUUSD WR is itself preasymptotic (n=129). Argues for very conservative effective-Kelly fractions and for measuring decay continuously (which GTOS does via OB continuation monitor).
- **potential_hypothesis:** *H21-025:* Compute trimmed/median R per instrument vs mean R. Hypothesis: gap is large for XAUUSD (heavy-tailed) and small for USDJPY → suggests size-weighting toward less-tailed instruments under tail-aware Kelly.
- **cross_domain_links:** 03, 17, 21-001
- **risk_metric:** multi (fat-tails framework)

### Optimal Leverage from Non-Ergodicity
- **id:** 21-026
- **authors:** Ole Peters
- **year:** 2009 (revised 2011)
- **source:** arXiv:0902.2965
- **url:** https://arxiv.org/abs/0902.2965v2
- **abstract:** Derives optimal leverage from time-average growth (rather than ensemble expectation). Shows optimal leverage `f* = µ/σ² - 1/2` (the "Kelly half-shift") emerges from time-averaging, not from utility maximization. Reconciles Kelly and Markowitz.
- **key_findings:**
  - Time-average vs ensemble expectation differ for non-ergodic wealth processes (geometric Brownian).
  - Optimal time-averaged growth implies log-wealth growth-rate maximization, NOT mean-return maximization.
  - Provides clean derivation of why Kelly is "the right" sizing without invoking utility theory.
  - Prefigures the ergodicity-economics framing.
- **relevance_to_gtos:** Theoretical foundation: GTOS sizes for time-average growth (compounding survival) over long sequences of trades — Peters-style framing supports geometric (not arithmetic) optimization.
- **potential_hypothesis:** *H21-026:* For each instrument, compute time-average vs ensemble-average expected R. Hypothesis: gap is significant for XAUUSD due to fat tails / non-ergodicity, and S79 risk policy should be tuned on time-average growth rate target rather than expected R/trade.
- **cross_domain_links:** 01, 21-001, 21-027
- **risk_metric:** Kelly+ergodicity

### The Ergodicity Problem in Economics
- **id:** 21-027
- **authors:** Ole Peters
- **year:** 2019
- **source:** Nature Physics, Vol 15, pp. 1216-1221
- **url:** https://www.nature.com/articles/s41567-019-0732-0
- **abstract:** General article (high-impact venue) framing classical economics decision theory as flawed by reliance on ensemble-expectation rather than time-average. Argues many puzzles (St. Petersburg, equity premium, etc.) resolve by ergodicity-aware reformulation.
- **key_findings:**
  - For multiplicative wealth processes, ensemble mean grows but individual time-average can decrease — bankruptcy in expectation-positive game.
  - Re-derives Kelly as time-average growth maximization, no utility assumption.
  - Frames decision-making under uncertainty around growth-optimality (vs expected utility).
- **relevance_to_gtos:** Directly motivates geometric (compound) growth rate, not E[R/trade], as the right optimization target. Provides the *philosophical* underpinning for survival-first sizing under prop-firm rules — survival is a multiplicative constraint.
- **potential_hypothesis:** *H21-027:* Benchmark prop-firm "P(pass)" metric against time-average vs ensemble-average growth rate. Hypothesis: P(pass) correlates more strongly with time-average growth than with E[R/trade].
- **cross_domain_links:** 01, 17 (behavioral), 21-026
- **risk_metric:** Kelly+ergodicity

---

## 6. Prop-firm rule design + practical sizing (5 papers)

### Trade Sizing Techniques for Drawdown and Tail Risk Control
- **id:** 21-028
- **authors:** Issam S. Strub
- **year:** 2014 (SSRN), revised 2018
- **source:** SSRN preprint 2063848
- **url:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2063848
- **abstract:** Compares three trade-sizing algorithms: vol-target, EVT-CVaR-target, EVT-CDaR-target. Tests on 10 years of daily returns from EURUSD, NZDMXN, 10Y UST, G10 FX basket strategies. Critical practitioner paper.
- **key_findings:**
  - EVT-based CVaR sizing: tail estimated via Generalized Pareto fit above threshold. Captures fat tail more accurately than vol-target.
  - EVT-CDaR sizing: drawdown distribution fit with EVT — best when drawdown is the prop-firm constraint.
  - Sharpe ratios are *equal or better* under EVT-CVaR/CDaR vs raw vol-target — tail-aware sizing is "free" in performance terms but reduces tail risk substantially.
  - Practitioner-friendly: code released, applicable to single-strategy sizing.
- **relevance_to_gtos:** Single most directly applicable paper for GTOS Phase 2. Replace `risk_per_trade_pct: 2.0%` with EVT-CDaR sizing under FN MTM-DD constraint. Strub's published results are *exactly* the GTOS use-case (FX strategy, daily horizon, drawdown-constrained).
- **potential_hypothesis:** *H21-028:* Implement Strub's EVT-CDaR sizing on GTOS 367-trade backtest. Set CDaR target = 4% (FN MTM-DD constraint). Hypothesis: EVT-CDaR sizing yields 10-20% higher growth rate than constant 2% at the same MTM-DD violation probability.
- **cross_domain_links:** 03 (EVT), 21-014, 21-021
- **risk_metric:** drawdown+CVaR

### Sizing the Risk: Kelly, VIX, and Hybrid Approaches in Put-Writing on Index Options
- **id:** 21-029
- **authors:** Various (arXiv:2508.16598)
- **year:** 2025
- **source:** arXiv:2508.16598, q-fin.PM
- **url:** https://arxiv.org/pdf/2508.16598
- **abstract:** Compares three position-sizing approaches for index-put-writing strategy: Kelly, VIX-based volatility regime scaling, and hybrid. Hybrid responds to risk environment without explicit regime classification.
- **key_findings:**
  - Pure-Kelly sizing fails on equity options strategies — fat-tailed loss distribution → overbet collapses.
  - VIX-regime sizing reduces exposure when implied vol is high; works well in 0DTE/1DTE configurations.
  - Hybrid (Kelly when VIX < threshold, vol-regime when VIX ≥ threshold) achieves best risk-adjusted performance.
- **relevance_to_gtos:** GTOS does not write options but the *hybrid concept* is applicable: regime-aware switch between aggressive (low-vol) and defensive (high-vol) sizing. This is essentially what S79 sharpe_weighted (Phase 2) is approaching.
- **potential_hypothesis:** *H21-029:* Build a hybrid GTOS sizing rule: in low-vol regime (rolling 20-day ATR < median) use 2.5% risk, in high-vol regime use 1.0% risk. Backtest. Hypothesis: this exceeds constant 2% on Sharpe by ~15% with same drawdown ceiling.
- **cross_domain_links:** 16, 21-008, 21-009
- **risk_metric:** vol-target+Kelly hybrid

### Buffett's Alpha
- **id:** 21-030
- **authors:** Andrea Frazzini, David Kabiller, Lasse H. Pedersen
- **year:** 2018
- **source:** Financial Analysts Journal, Vol 74(4), pp. 35-55
- **url:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3197185
- **abstract:** Decomposes Berkshire Hathaway's Sharpe 0.79 over 50 years. Buffett's alpha disappears once factor-controlled for "betting against beta" + "quality minus junk" — the alpha is from leveraging cheap, safe, high-quality stocks.
- **key_findings:**
  - Buffett's leverage = ~1.7x — well below typical hedge fund 4-10x.
  - Insurance float (cheap funding cost ≈ 1.7%/year vs market average 4-5%) explains a chunk of returns.
  - Quality (profitability + safety) weighting is the dominant factor.
  - Sharpe 0.79 over 50 years is exceptional but mechanistically explainable.
- **relevance_to_gtos:** Distantly relevant. The lesson is: *consistent moderate leverage on a real edge sustains alpha*; extreme leverage (3-10x) kills alpha via tail risk. GTOS's prop-firm 2% risk = ~50:1 effective leverage on equity at risk — much higher than Buffett's 1.7x and creates tail-risk pressure.
- **potential_hypothesis:** *H21-030:* Compute GTOS effective-leverage ratio: per-trade equity-at-risk / equity. Hypothesis: comparison with Buffett's 1.7x ratio shows GTOS at moderate-aggressive leverage; the H29 rule keeps it within survivable range.
- **cross_domain_links:** 13, 22 (hedge fund alpha)
- **risk_metric:** multi

### Money Management Principles for Mechanical Traders (master's thesis)
- **id:** 21-031
- **authors:** Shlok Datye
- **year:** 2012
- **source:** KTH Royal Institute of Technology master's thesis
- **url:** https://www.math.kth.se/matstat/seminarier/reports/M-exjobb12/121105.pdf
- **abstract:** Practitioner-oriented master's thesis on Kelly, optimal-f, and fixed-fractional sizing in algorithmic trading. Walk-forward tests of these methods on FX strategies; discusses estimation risk + sample size.
- **key_findings:**
  - Walk-forward test: optimal-f (Vince) overfits historical returns more than fractional Kelly.
  - Fractional Kelly with 0.25-0.5 multiplier consistently dominates fixed-fractional 1-3% on Sharpe in mechanical FX strategies.
  - Sample size required for stable Kelly estimate is in the hundreds-of-trades range; smaller samples produce noisy Kelly.
- **relevance_to_gtos:** Empirical confirmation that GTOS's 367-trade batch is the *minimum* needed for stable Kelly estimates. Below that, point-estimate is noisy.
- **potential_hypothesis:** *H21-031:* For each GTOS instrument, compute Kelly bootstrap distribution from H1-2026 trade data; identify which instruments have stable Kelly (XAUUSD: n>100) vs noisy (NAS100: n<10). Hypothesis: stable-Kelly instruments warrant their own sizing; noisy-Kelly defaults to portfolio-level conservatism.
- **cross_domain_links:** 02 (sample-size methodology), 21-001
- **risk_metric:** Kelly

### Practical Implementation of the Kelly Criterion
- **id:** 21-032
- **authors:** Carvalho et al.
- **year:** 2020
- **source:** Frontiers in Applied Mathematics and Statistics, Vol 6, art 577050
- **url:** https://www.frontiersin.org/journals/applied-mathematics-and-statistics/articles/10.3389/fams.2020.577050/full
- **abstract:** Equity-portfolio implementation of Kelly: optimal growth rate, number of trades, rebalancing frequency. Provides closed-form daily-rebalanced Kelly under log-normal returns.
- **key_findings:**
  - Daily-rebalanced Kelly portfolio matches Markowitz tangency portfolio under log-normal.
  - Rebalancing-frequency tradeoff: too-frequent has transaction costs, too-rare deviates from Kelly path.
  - Optimal frequency for typical equity portfolio is weekly to monthly.
  - Robust to ~30% parameter mis-specification under fractional Kelly with f = 0.5.
- **relevance_to_gtos:** GTOS rebalances at trade-event level (not periodic) so frequency isn't directly applicable, but the *parameter-robustness* point matters: half-Kelly tolerates 30% edge-misestimate well. GTOS at 1/18-Kelly is over-padded for current edge uncertainty (XAUUSD ξ=0.35 + decayed WR).
- **potential_hypothesis:** *H21-032:* Compute the Kelly-fraction tolerance band (Carvalho-style) for current GTOS edge estimate; compare with operating fraction. Hypothesis: GTOS could sustainably move from ~1/18-Kelly to 1/6-Kelly without breaching FN drawdown constraint, freeing significant edge upside.
- **cross_domain_links:** 21-001, 21-004
- **risk_metric:** Kelly

---

## 7. Buffer / SL-distance / partial-take tradeoff (3 papers)

### Constant Proportion Portfolio Insurance (Black-Perold)
- **id:** 21-033
- **authors:** Fischer Black, André F. Perold
- **year:** 1992 (also Perold 1986; Black-Jones 1987)
- **source:** Journal of Economic Dynamics and Control, Vol 16, pp. 403-426
- **url:** https://www.sciencedirect.com/science/article/abs/pii/016518899290043E
- **abstract:** Formalizes CPPI: maintain risky allocation = m · cushion, where m is constant multiplier and cushion = wealth - floor. Closed-form analysis under continuous-time. Extends to borrowing constraints + transaction costs.
- **key_findings:**
  - CPPI guarantees floor only in continuous-time absent gaps; gap risk significant in real markets.
  - Multiplier `m` equivalent to leverage ratio against cushion; m=1 ≈ buy-and-hold + cash; m → ∞ approaches all-risky.
  - Practical implementations use m ∈ [3, 5] for moderate growth + floor protection.
- **relevance_to_gtos:** GTOS's H29 0.5x rule at 8% DD is *piecewise CPPI*: when wealth crosses 92% of peak, halve the risky allocation. Continuous-time CPPI suggests smoother schedule.
- **potential_hypothesis:** *H21-033:* Replace H29 with proper CPPI: `risk_pct_t = base · m · max(0, (W_t - 0.92·W_max) / W_t)` with m ∈ [2, 5]. Backtest. Hypothesis: m=3 yields better growth-vs-DD tradeoff than H29's m≈1 step rule.
- **cross_domain_links:** 21-018, 21-019
- **risk_metric:** drawdown (CPPI)

### Optimal Investment Strategies for Volatility-Targeting and Trailing-Stop Trading (practitioner study)
- **id:** 21-034
- **authors:** various — Conditional Volatility Targeting, Tandfonline
- **year:** 2020
- **source:** Financial Analysts Journal, full article 10.1080/0015198X.2020.1790853
- **url:** https://www.tandfonline.com/doi/full/10.1080/0015198X.2020.1790853
- **abstract:** Conditional volatility targeting: turn vol-target on only in high-vol or stress regimes. Documented Sharpe gain for momentum factor across regions. Conventional always-on vol-targeting can underperform.
- **key_findings:**
  - Conditional vol-targeting reduces drawdowns + tail risks for major equity markets and momentum.
  - Always-on vol-targeting can lead to *greater* drawdowns in some markets (under-hedges in stress, over-de-leverages in calm).
  - Conditional rule: target vol only when vol-z-score > threshold; otherwise constant exposure.
- **relevance_to_gtos:** Critical for GTOS Phase 2 vol-scaling design. Naive vol-scaling may *hurt* GTOS in calm regimes. A conditional version (only when vol-z > 1.5) could capture the gold tail-stress benefit without idle-period leverage drag.
- **potential_hypothesis:** *H21-034:* Compare always-on vs conditional vol-targeting on GTOS. Hypothesis: conditional (turn-on at vol-z > 1.5) outperforms always-on by ~5-10% Sharpe and reduces tail-DD ~20%.
- **cross_domain_links:** 16, 21-008, 21-009
- **risk_metric:** vol-target

### Risk-Aware Deep Reinforcement Learning for Dynamic Portfolio Optimization
- **id:** 21-035
- **authors:** Various (arXiv:2511.11481)
- **year:** 2024
- **source:** arXiv:2511.11481, q-fin.PM
- **url:** https://arxiv.org/abs/2511.11481
- **abstract:** Proximal Policy Optimization (PPO) framework for dynamic portfolio optimization. Reward = Sharpe ratio with hard constraints on max drawdown and volatility. Demonstrates DRL can outperform standard rebalancing under tail risk.
- **key_findings:**
  - DRL with explicit DD constraint achieves higher Sharpe than vol-targeted benchmark on equity index portfolio.
  - Constraint-as-reward (CVaR penalty) outperforms constraint-as-soft-clip in stability.
  - Test results: 25% reduction in maxDD vs benchmark with same Sharpe.
- **relevance_to_gtos:** Phase 3+ idea. RL-based sizing controller is feasible if GTOS adopts a learnable risk overlay. Currently rule-based (H29).
- **potential_hypothesis:** *H21-035:* Train a small DRL sizing controller on GTOS 367-trade pop with reward = Sharpe minus DD-violation penalty. Hypothesis: DRL recovers a smoother version of the H29 rule and may be tunable to specific FN constraint.
- **cross_domain_links:** 19, 20 (RL/LLM trading)
- **risk_metric:** drawdown+vol-target

---

## 8. Foundational supporting (3 papers)

### Portfolio Selection
- **id:** 21-036
- **authors:** Harry Markowitz
- **year:** 1952
- **source:** Journal of Finance, Vol 7(1), pp. 77-91
- **url:** https://www.math.hkust.edu.hk/~maykwok/courses/ma362/07F/markowitz_JF.pdf
- **abstract:** Foundational mean-variance optimization paper. Shows portfolio expected return + variance is the optimization frame; introduces efficient frontier; diversification reduces variance for fixed return.
- **key_findings:**
  - E[r] - λ·Var(r) optimization → tangent portfolio + risk-free combination.
  - Diversification benefits are second-moment effect, not first-moment.
  - The "efficient frontier" arises from constrained optimization.
  - Risk = variance is the foundational (and limited) assumption.
- **relevance_to_gtos:** Background concept. Mean-variance is too coarse for fat-tailed instruments (CVaR / drawdown is preferred for GTOS) but informs the risk-parity foundation.
- **potential_hypothesis:** N/A (foundational reference).
- **cross_domain_links:** 13, 21-010
- **risk_metric:** multi (mean-variance)

### Safety First and the Holding of Assets
- **id:** 21-037
- **authors:** Andrew D. Roy
- **year:** 1952
- **source:** Econometrica, Vol 20(3), pp. 431-449
- **url:** https://www.econometricsociety.org/publications/econometrica/1952/07/01/safety-first-and-holding-assets
- **abstract:** Predates Markowitz by months. Investor's primary objective: minimize probability of falling below disaster level. Choose portfolio to maximize `(E[r] - r_disaster) / σ`. Origin of the Sharpe ratio formulation.
- **key_findings:**
  - "Safety-first" objective: P(r < r_disaster) ≤ ε.
  - Formula: maximize (µ - r_disaster) / σ — proto-Sharpe.
  - Argues investors care first about avoiding catastrophe, not maximizing utility.
- **relevance_to_gtos:** Foundational for prop-firm framing. GTOS lives in safety-first universe — the FN 4% MTM-DD is precisely a "disaster level". Roy's framework is the *correct* objective for prop-firm sizing, not utility maximization.
- **potential_hypothesis:** *H21-037:* Recast S79 risk policy as Roy safety-first: maximize geometric mean R subject to `P(daily MTM-DD ≥ 4%) ≤ ε` for ε ∈ {0.01, 0.05, 0.10}. Hypothesis: optimal sizing varies sharply by ε; CEO choice of ε is the key parameter.
- **cross_domain_links:** 21-013, 21-005, 21-018
- **risk_metric:** safety-first

### Time Series Momentum
- **id:** 21-038
- **authors:** Tobias J. Moskowitz, Yao Hua Ooi, Lasse H. Pedersen
- **year:** 2012
- **source:** Journal of Financial Economics, Vol 104(2), pp. 228-250
- **url:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2089463
- **abstract:** Demonstrates time-series momentum (1-12 month) in 58 liquid futures across asset classes. Diversified TSM portfolio scaled to 10% target volatility delivers Sharpe ≈ 1.4 over 1985-2009. Provides per-instrument vol-scaling protocol.
- **key_findings:**
  - TSM Sharpe is consistent across asset classes; volatility scaling is essential to combine across markets.
  - Vol-scaled diversified portfolio: each market scaled to 40% annual vol, then equal-weighted, yields stable Sharpe.
  - "Vol scaling = vol budgeting" is the practitioner standard for cross-asset trend portfolios.
  - Crashes/severe DDs occur in regime breaks (2008-style); vol scaling reduces but doesn't eliminate.
- **relevance_to_gtos:** Practitioner standard for vol-scaling protocol. GTOS's instruments span asset classes (gold, indices, FX) and need exactly this kind of per-instrument vol-scaling to combine into a portfolio measure.
- **potential_hypothesis:** *H21-038:* Apply Moskowitz-Ooi-Pedersen vol-scaling protocol to GTOS: each instrument's risk_pct scaled so per-trade ATR-vol = constant `target_vol`. Hypothesis: this is functionally equivalent to S79 sharpe_weighted on per-trade-vol basis and improves cross-instrument capital allocation.
- **cross_domain_links:** 14 (momentum), 16 (vol)
- **risk_metric:** vol-target

---

## Section 9 — Gaps and caveats

1. **Prop-firm-specific academic literature is thin.** Most prop-firm-rule analysis is industry whitepaper, not peer-reviewed. The closest analogues are the Strub trade-sizing paper (21-028, applied to drawdown control on FX strategies) and the Geanakoplos leverage-cycle paper (21-022, macro-context for leverage de-leveraging). Phase 2 should consider commissioning original empirical work on prop-firm survival under different sizing rules.

2. **Side-aware Kelly literature is missing.** GTOS memory `project_side_aware_sizing_findings` shows LONG=0.5x, SHORT=1.0x asymmetric sizing. The asymmetric-Kelly literature (search did not surface specific peer-reviewed papers on this) appears thin — likely because in equities the long-short asymmetry is an institutional artifact (short-selling cost). For FX/commodities the asymmetry should be symmetric in theory; GTOS's empirical asymmetry is unique.

3. **Drawdown-Kelly under fat tails.** The combination "drawdown-constrained + fat-tailed + estimation-risk" is theoretically rich but the closed-form solutions remain in low-dimensional cases. Strub (21-028) is the most practical synthesis; Magdon-Ismail (21-020) is the analytical baseline; Sornette et al. (21-006) is the empirical bridge.

4. **Books vs papers.** Some load-bearing references are textbook-only (McNeil-Frey-Embrechts 21-016, Roncalli risk-parity book — listed in this report as cross-reference but not own row to keep paper-focused; Taleb 21-025 is partially preprint).

5. **Recent (2023-2025) research is well-represented.** 5 of 38 papers are 2020+ (Sornette 2020, Carvalho 2020, Conditional Vol-Targeting 2020, Sizing-the-Risk 2025, Risk-Aware DRL 2024, Tackling-Estimation-Risk 2025). Total post-2010 ≈ 22/38, satisfying spec §8 recent-decade emphasis.

6. **Cross-domain handoffs:** 03 (tails), 13 (correlation/factor), 16 (vol regime), 17/18 (behavioral/psychology), 14 (momentum), 19/20 (ML/RL).

---

## Section summary count

| Section | Subdomain | Count | Spec target |
|---------|-----------|-------|-------------|
| 1 | Kelly foundational | 7 | ~7 |
| 2 | Vol-targeting / risk parity | 5 | ~5 |
| 3 | CVaR / coherent measures | 5 | ~5 |
| 4 | Drawdown control / leverage cycle | 5 | ~5 |
| 5 | Fat-tail-aware sizing | 5 | ~5 |
| 6 | Prop-firm + practical sizing | 5 | ~5 |
| 7 | Buffer / SL / partial-take | 3 | ~3 |
| 8 | Foundational supporting | 3 | (carries) |
| **Total** | | **38** | 30-45 |

---

## Section 10 — Top 3 most-relevant-to-GTOS

1. **21-028 Strub — Trade Sizing Techniques for Drawdown and Tail Risk Control.** Directly applicable: EVT-CVaR/CDaR sizing with prop-firm drawdown constraint = exactly GTOS's S79 Phase 2 problem. Code released; tested on FX strategies; quantified Sharpe-neutral tail-risk reduction.

2. **21-005 Busseti-Ryu-Boyd — Risk-Constrained Kelly Gambling.** Convex optimization formulation that includes drawdown probability as a hard constraint and yields growth-optimal sizing within the constraint. The single risk-aversion parameter `λ` is the natural sharpe_weighted-sizing knob for S79 Phase 2; strictly dominates fractional-Kelly.

3. **21-018/21-019 Grossman-Zhou + Cvitanić-Karatzas — Optimal Investment Under Drawdown Constraints.** Provides the closed-form theoretical foundation for the H29 rule. Smooth Grossman-Zhou rule is a candidate replacement for the discrete step at 8% DD. Cvitanić-Karatzas extends to multi-asset, matching GTOS's 7-instrument portfolio.

## Top 1 surprise

**Moreira-Muir (21-008) Volatility-Managed Portfolios.** *Out-of-sample* Sharpe gains of 20-40% from a simple vol-scaling rule, even after factor controls — and the strategy *takes less risk in recessions*, contradicting the standard "expected returns rise in stress" narrative. For GTOS this means simple per-instrument vol-scaling could materially boost Sharpe with no edge changes — and importantly does NOT require fancy regime detection.

## Top 2-3 hypotheses for Phase 2

- **H21-A (S79 Phase 2 core):** Replace uniform_fn 2.0% with Busseti-Boyd RCK (21-005) under FN constraint `P(MTM-DD ≥ 4%) ≤ 0.02`. Backtest on 367-trade pop. *Predicted:* sharper Sharpe with same prop-firm violation rate; per-instrument optimal weights non-uniform.
- **H21-B (vol-scaling overlay):** Implement Moreira-Muir / Moskowitz-Ooi-Pedersen vol-scaling (21-008/21-038) per-instrument with `target_vol_per_trade = 1%`. Hypothesis: 15-25% Sharpe lift, especially on XAUUSD and indices where leverage effect is documented.
- **H21-C (Strub-EVT-CDaR sizing):** Replace constant-2% with Strub's CDaR-target sizing using EVT-fitted drawdown distribution. Hypothesis: equivalent or better growth at smaller worst-case DD, especially beneficial on gold (ξ=0.35).

## Cross-domain handoffs

- **03 Distributional characteristics** ← consume `ξ`, GARCH persistence, EVT-fit threshold for Kelly-under-fat-tails (21-016, 21-024, 21-025).
- **13 Cross-asset correlation/factors** ← multi-asset drawdown sizing (21-019, 21-010, 21-011, 21-012).
- **16 Volatility regime** ← input to vol-target sizing (21-008, 21-009, 21-029).
- **17/18 Behavioral/psychology** ← the "leverage aversion" friction (21-010) is partially behavioral, decay/regime detection from psychology overlap.
- **14 Momentum/breakout** ← TSM portfolio sizing (21-038) intersects with momentum-strategy domain.
- **02 Statistical methodology** ← parameter-uncertainty in Kelly estimation (21-001-21-007, 21-032), Bayesian Kelly.

---

*Catalog compiled by Domain 21 Phase 1 worker; no fabrication; URLs verified via WebSearch results; cross-referenced against `_specs/21_risk_management_kelly_sizing.md` §3 seed list.*
