# Domain 01 — Mathematical Foundations & Stochastic Processes

**Worker:** Phase 1 Literature Worker #1
**Date:** 2026-04-28
**Papers cataloged:** 42
**Spec source:** `research/ml_program/literature/_specs/01_math_foundations.md`

---

## Section 1 — Domain scope (covered + deferred)

### Covered
- Foundational stochastic-calculus papers / books anchoring SDE-based finance: Bachelier (1900), Black-Scholes (1973), Merton (1976), Heston (1993), Karatzas-Shreve textbooks.
- Fundamental theorem of asset pricing and semimartingale arbitrage theory: Delbaen-Schachermayer (1994), El Karoui-Peng-Quenez (1997), Cherny-Shiryaev (2002).
- Levy-process and jump-diffusion construction (Merton 1976, Kou 2002, Eberlein-Keller 1995, Madan-Carr-Chang 1998, Carr-Geman-Madan-Yor 2002, Sato 1999, Cont-Tankov 2004, Schoutens 2003).
- Subordination, time-changed Brownian motion, and trading-time / physical-time duality (Clark 1973, Ane-Geman 2000).
- Fractional / rough volatility theory anchors: Mandelbrot-Van Ness (1968 — proxied via Watkins 2019), Comte-Renault (1998), Gatheral-Jaisson-Rosenbaum (2018), Bayer-Friz-Gatheral (2016), El Euch-Rosenbaum (2019), Forde-Jacquier (and the Forde-Friz line) on small-time asymptotics.
- Rough-path / signature theory: Chen (1957), Lyons (1998), Hambly-Lyons (2010), Chevyrev-Kormilitzin (2016), Lyons-McLeod (2022), Cuchiero-Moller (2024) — both the path-uniqueness theorem and applied signature methods in finance.
- Hawkes / point-process theory underpinning self-exciting clusters: Bacry-Mastromatteo-Muzy (2015).
- Microstructural / limit-order-book diffusion approximations: Kyle (1985), Cont-de Larrard (2013), Almgren-Chriss (2001), Avellaneda-Stoikov (2008), Donier-Bonart-Mastromatteo-Bouchaud (2015).
- Backward SDE / FBSDE and stochastic-control PDE methods: Bismut (1973 — historical anchor), El Karoui-Peng-Quenez (1997), Han-Jentzen-E (2018), Buehler-Gonon-Teichmann-Wood (2019).
- Drawdown / first-passage / barrier exit theory directly relevant to SL/TP: Pospisil-Vecer (2010), the Bachelier-Levy first-passage line, Wiener-Hopf factorization for spectrally negative Levy processes (Kuznetsov 2010, 2012).
- Ergodic / large-deviation theory used in long-run asymptotics: Pham (2003/2007).
- Cont (2001) stylized facts as the link to distributional / multifractal phenomena (cross-domain anchor).
- Contrarian / under-cited findings: Lux-Marchesi (1999), Bouchaud-Mezard (2000), Cont-Bouchaud (2000), Mandelbrot-Calvet-Fisher (1997), Mandelbrot-Wallis (1969).

### Deferred (cross-linked)
- Pure GARCH-family estimation papers (Engle 1982, Bollerslev 1986) cataloged here only as theoretical anchors; empirical fit papers belong to **domain 03**.
- Engle (2002) DCC included but cross-flagged to **domain 13** (correlation modelling) per spec §6.
- Wavelet decomposition for forecasting → **domain 04**.
- Regime-switching estimation → **domain 05**.
- Pure microstructure empirical impact / OFI → **domain 06**.
- Optimal-execution / VWAP RL → **domain 06 / 20**.
- Rough volatility option *pricing & calibration* — kept here only at theoretical-construction level; empirical-calibration papers cross-flagged to **domain 16**.
- Glasserman (2003) Monte-Carlo book cataloged for completeness; methodologically primary for **domain 02**.

---

## Section 2 — Foundational papers

### Theorie de la Speculation
- **Authors:** Louis Bachelier
- **Year/Source:** 1900 / Annales Scientifiques de l'École Normale Supérieure (Doctoral thesis, Sorbonne); reprinted in *Louis Bachelier's Theory of Speculation* (Davis-Etheridge-Samuelson eds., Princeton, 2006)
- **URL:** https://www.investmenttheory.org/uploads/3/4/8/2/34825752/emhbachelier.pdf ; https://press.princeton.edu/books/hardcover/9780691117522/louis-bacheliers-theory-of-speculation
- **Abstract:** Bachelier's doctoral thesis introduced the first mathematical model of Brownian motion and applied it to stock-option valuation, treating the price increment as a sum of small independent shocks and deriving the diffusion equation for option price. The work pre-dated Einstein's 1905 paper on Brownian motion and remained essentially unread in finance until Samuelson recovered it in the 1960s.
- **Key findings:**
  - Stock prices follow a process with stationary independent Gaussian increments (arithmetic Brownian motion).
  - The first-passage-time density for a barrier under arithmetic Brownian motion is the inverse-Gaussian / Bachelier-Levy formula.
  - Option price satisfies a diffusion-equation boundary-value problem (precursor of Black-Scholes PDE).
  - Random-walk / efficient-market intuition: future prices are unforecastable conditional on the present.
- **Relevance to GTOS:** Anchor for the Component-2 swing/excursion model; the Bachelier-Levy first-passage-time distribution is the natural null model for stop-loss hitting probability when ATR-buffer multipliers are calibrated. Sets up the question whether mid-OB-zone behavior is closer to Bachelier (Gaussian) or Mandelbrot/CGMY (heavy-tailed) regimes — directly linked to the project memory `project_distributional_findings.md` (ξ=0.35).
- **Potential hypothesis:** Under a Bachelier null with empirically-calibrated drift+volatility for XAUUSD H1, the predicted first-passage probability to the OB stop level within 4 H1 candles materially under-estimates the realized SL-hit rate, the residual gap quantifying jump / fat-tail risk that K54 should learn.
- **Cross-domain flag:** none

### The Pricing of Options and Corporate Liabilities
- **Authors:** Fischer Black, Myron Scholes
- **Year/Source:** 1973 / Journal of Political Economy 81(3): 637-654
- **URL:** https://www.cs.princeton.edu/courses/archive/fall09/cos323/papers/black_scholes73.pdf ; https://www.sfu.ca/~kkasa/BlackScholes_73.pdf
- **Abstract:** Derives a closed-form valuation formula for European call/put options under geometric Brownian motion with constant volatility and risk-free rate by constructing a continuously-rebalanced replicating portfolio. The no-arbitrage hedge argument is formalized through what later becomes the Girsanov / risk-neutral-measure machinery.
- **Key findings:**
  - Geometric Brownian motion with constant volatility provides a tractable continuous-time price process.
  - The continuous self-financing replicating portfolio implies a deterministic option price.
  - Implied volatility surface inversion provides a market-consistent view of the underlying volatility process.
  - Setup of the continuous-time hedging argument that underlies all subsequent derivative-pricing theory.
- **Relevance to GTOS:** Foundational reference; not directly used (GTOS does not price derivatives) but sets up the implied-vol concept that drives volatility-regime context for kill-zone selection (H25 session-volatility shadow logger). The constant-vol assumption is precisely what later rough-volatility findings (Gatheral-Jaisson-Rosenbaum 2018) invalidate.
- **Potential hypothesis:** —
- **Cross-domain flag:** none

### Continuous Auctions and Insider Trading
- **Authors:** Albert S. Kyle
- **Year/Source:** 1985 / Econometrica 53(6): 1315-1335
- **URL:** https://personal.utdallas.edu/~nina.baranchuk/Fin7310/papers/Kyle1985.pdf ; https://people.duke.edu/~qc2/BA532/1985%20EMA%20Kyle.pdf
- **Abstract:** Constructs a sequential-auction equilibrium with one informed insider, noise traders, and competitive risk-neutral market makers. As the inter-auction interval shrinks to zero, the limit price process is Brownian, market depth (Kyle's lambda) is constant, and private information is fully incorporated by the close.
- **Key findings:**
  - In equilibrium, prices are Brownian under linear strategies — Brownian motion emerges endogenously from informed/noise mixing.
  - Market depth λ is the inverse of the price-impact coefficient — it scales with the noise-trader volatility / private-info uncertainty ratio.
  - Insider trades a constant fraction of the gap between fundamental and price per unit time.
  - Information is revealed *exactly* at the close; intraday price discovery is monotonic.
- **Relevance to GTOS:** Theoretical anchor for the OB-zone edge: the Kyle-λ price impact is the formal mechanism by which the OB acts as a stop-cascade equilibrium magnet. The U-shape of intraday volatility (kill-zone selection) and the proximity of GTOS entries to the open / NYSE close are interpretable as periods of high λ-volatility ratio.
- **Potential hypothesis:** OB-zone WR is monotonically related to the realized Kyle-λ during the formation candle, controlled for ATR; cells where λ is in the bottom decile are the cells where OB precision degrades fastest (consistent with F11 OB-zone advantage decay velocity).
- **Cross-domain flag:** 06_market_microstructure_orderbook (cross-link; theory ownership stays here)

### A General Version of the Fundamental Theorem of Asset Pricing
- **Authors:** Freddy Delbaen, Walter Schachermayer
- **Year/Source:** 1994 / Mathematische Annalen 300(1): 463-520
- **URL:** https://link.springer.com/article/10.1007/BF01450498 ; https://people.math.ethz.ch/~delbaen/ftp/preprints/NLB.pdf (related preprint)
- **Abstract:** Establishes the equivalence between the no-free-lunch-with-vanishing-risk (NFLVR) condition and the existence of an equivalent local-martingale measure for a locally-bounded semimartingale price process. Closes a major open question by extending the discrete-time FTAP of Dalang-Morton-Willinger to general continuous-time semimartingales.
- **Key findings:**
  - NFLVR ⇔ existence of an equivalent (sigma-)martingale measure (semimartingale price).
  - Frictionless no-arbitrage forces the price process to be a semimartingale.
  - The proof uses a separation theorem in L∞ on the "free lunch" cone and develops the abstract Banach-space machinery (Yan's theorem extension).
  - The framework subsumes Levy / jump-diffusion / stochastic-volatility models that pass NFLVR.
- **Relevance to GTOS:** Theoretical bedrock; tells GTOS that under no-arbitrage, *any* candle-close return process must be a semimartingale, hence the Doob-Meyer decomposition into predictable drift + martingale shock applies. Sets the bound on the Component-3A signal-to-noise ratio.
- **Potential hypothesis:** —
- **Cross-domain flag:** none

### Brownian Motion and Stochastic Calculus
- **Authors:** Ioannis Karatzas, Steven E. Shreve
- **Year/Source:** 1991 / Springer Graduate Texts in Mathematics 113 (textbook, 2nd ed.)
- **URL:** https://link.springer.com/book/10.1007/978-1-4612-0949-2 (publisher page)
- **Abstract:** Standard graduate textbook covering the construction of Brownian motion, Ito integration, semimartingale theory, stochastic differential equations, local times, excursion theory, and the connections to PDEs through the Feynman-Kac formula. The de-facto reference for the stochastic-calculus machinery used in mathematical finance.
- **Key findings:**
  - Construction and properties of Brownian motion (Levy's modulus of continuity, law of iterated logarithm).
  - Ito's lemma and stochastic integration against semimartingales.
  - First-passage time and local-time decompositions.
  - Foundational results on SDE existence/uniqueness under Lipschitz / linear-growth conditions.
- **Relevance to GTOS:** Reference text; the local-time theory undergirds excursion-based BOS/CHoCH / OB-formation dynamics in `market_state.py` (excursions of the price away from running min/max are the SMC "structure").
- **Potential hypothesis:** —
- **Cross-domain flag:** none

### Methods of Mathematical Finance
- **Authors:** Ioannis Karatzas, Steven E. Shreve
- **Year/Source:** 1998 / Springer Applications of Mathematics 39 (textbook)
- **URL:** https://link.springer.com/book/10.1007/978-1-4939-6845-9
- **Abstract:** Sequel to *Brownian Motion and Stochastic Calculus*; develops contingent-claim pricing, optimal consumption-investment, complete and incomplete markets, market imperfections, portfolio constraints, and exotic-option valuation in a Brownian filtration framework.
- **Key findings:**
  - Complete-market replication and martingale pricing under semimartingale dynamics.
  - Hedging-constrained optimization and dual / shadow-price formulations.
  - Optimal stopping and American-option theory in a stochastic-control framework.
  - Equilibrium with heterogeneous agents.
- **Relevance to GTOS:** Reference for the optimal-stopping machinery underlying any rigorous treatment of GTOS partial-close / time-stop / trailing-stop logic (J46-J49 portfolio policy in memory).
- **Potential hypothesis:** —
- **Cross-domain flag:** 21_risk_management_kelly_sizing (cross-link)

### Continuous Martingales and Brownian Motion
- **Authors:** Daniel Revuz, Marc Yor
- **Year/Source:** 1999 (3rd ed.) / Springer Grundlehren 293 (textbook)
- **URL:** https://link.springer.com/book/10.1007/978-3-662-06400-9
- **Abstract:** Comprehensive treatment of continuous local-martingale theory, time-change of semimartingales, excursion theory, Wiener / Brownian local times, multi-dimensional Brownian motion, and ergodic properties of diffusions. The standard French-school reference.
- **Key findings:**
  - Dambis-Dubins-Schwarz time-change theorem: every continuous local martingale is a time-changed Brownian motion.
  - Excursion theory of Brownian motion (Ito's measure, Williams decomposition).
  - Bessel / squared-Bessel processes and their hitting-time densities.
  - Pitman / Williams path decompositions.
- **Relevance to GTOS:** Excursion-theory toolkit for analyzing inter-OB-touch dynamics; Dambis-Dubins-Schwarz time-change is the formal handle on `tick_features.py` physical-time vs trading-time distinction.
- **Potential hypothesis:** —
- **Cross-domain flag:** none

### Stochastic Calculus for Finance II: Continuous-Time Models
- **Authors:** Steven E. Shreve
- **Year/Source:** 2004 / Springer Finance (textbook)
- **URL:** https://link.springer.com/book/10.1007/978-1-4757-4296-1
- **Abstract:** Self-contained graduate textbook applying stochastic-calculus methods to mathematical finance: Brownian motion, Ito integration, risk-neutral measure, Black-Scholes-Merton, term-structure models, jump processes, and exotic options. The didactic gold standard for incoming finance PhDs.
- **Key findings:**
  - Risk-neutral measure construction via Girsanov theorem.
  - Heat-equation reduction of Black-Scholes PDE.
  - Numeraire-change technique for currency / forward-pricing.
  - Coverage of jump-diffusion, fixed-income, and credit-risk basics.
- **Relevance to GTOS:** Pedagogical reference. Useful for any new GTOS engineer transitioning from pure-Python to finance-stochastic intuition.
- **Potential hypothesis:** —
- **Cross-domain flag:** none

### Option Pricing When Underlying Stock Returns Are Discontinuous
- **Authors:** Robert C. Merton
- **Year/Source:** 1976 / Journal of Financial Economics 3(1-2): 125-144
- **URL:** https://dspace.mit.edu/handle/1721.1/1899
- **Abstract:** Extends Black-Scholes by superimposing a compound-Poisson jump process with log-normal jump sizes on the diffusive log-price. Derives a series-expansion for the European option price and analyzes the implications for skew and kurtosis of the implied-vol surface.
- **Key findings:**
  - Closed-form (Poisson-mixed Black-Scholes series) for European options under log-normal jump-diffusion.
  - Jumps generate a leptokurtic return distribution and a non-flat implied-vol smile.
  - Idiosyncratic jumps can be locally hedged only on average; jump risk cannot be perfectly replicated in continuous time.
  - Empirical fit improves over pure Black-Scholes for individual-name equities with announcement / event risk.
- **Relevance to GTOS:** Direct theoretical motivation for why GTOS uses a *fixed* SL buffer (rather than continuously rebalancing): jump risk is unhedgeable in real-time, so the buffer must be sized for the jump-component-implied tail (consistent with project_distributional_findings memory: ξ=0.35 fat tail observed in gold).
- **Potential hypothesis:** Buffer multipliers (sl_buffer_atr_multiplier) optimized under a Merton jump-diffusion null differ materially from those optimized under pure Brownian/ATR; recalibrating buffers to the empirical jump-frequency / mean-jump-size could move SL-hit rate by ≥3pp on the heavy-jump instruments (XAUUSD, NAS100, US30).
- **Cross-domain flag:** none

### A Subordinated Stochastic Process Model with Finite Variance for Speculative Prices
- **Authors:** Peter K. Clark
- **Year/Source:** 1973 / Econometrica 41(1): 135-155
- **URL:** https://www.jstor.org/stable/1913889 ; https://conservancy.umn.edu/bitstreams/c0c15ef7-a81c-4354-89fd-89c8c5237986/download
- **Abstract:** Proposes that observed log-price increments are a *subordinated* process: Brownian motion evaluated at a random "operational time" driven by trading-volume-like activity. Reconciles fat-tailed unconditional return distributions with finite variance via mixtures-of-normals.
- **Key findings:**
  - Subordination by an independent random clock yields heavier-than-Gaussian unconditional returns even when conditional returns are Gaussian.
  - Volume / activity is a candidate stochastic clock.
  - The mixture-of-distributions hypothesis (MDH) follows.
  - Observed unconditional kurtosis is consistent with empirical lognormal-volume subordination.
- **Relevance to GTOS:** Deep theoretical anchor for the tick-capture daemon (`tick_features.py`). The 12 microstructure features extracted *are* a partial specification of the operational clock. E24/E26 (microstructure) NULL_VERDICT_CONFIRMED memory note suggests the operational-clock signal is weak in M15-aggregated outcomes — but Clark's framework predicts the leverage is conditional on tick-density regimes, not flat.
- **Potential hypothesis:** When trading-time (ticks per M15) is in the upper tercile, OB-zone WR rises by ≥4pp relative to physical-time, controlled for ATR — i.e., the apparent decay in OB precision (F11) is partly a physical-time-vs-trading-time phenomenon, *not* a structural-edge collapse.
- **Cross-domain flag:** 03_distributional_characteristics

### Empirical Properties of Asset Returns: Stylized Facts and Statistical Issues
- **Authors:** Rama Cont
- **Year/Source:** 2001 / Quantitative Finance 1(2): 223-236
- **URL:** http://rama.cont.perso.math.cnrs.fr/pdf/empirical.pdf
- **Abstract:** Catalogs the eleven canonical stylized facts of financial returns: heavy tails, volatility clustering, leverage effect, asymmetry of gain/loss distribution, intermittency, slow tail decay, etc. Establishes the benchmark a model must reproduce.
- **Key findings:**
  - Returns are not iid; absolute returns are long-memory while signed returns are essentially unpredictable.
  - Tail index is finite (3-5 typical); variance is finite, fourth moment may not be.
  - Volatility clustering and leverage are universal across asset classes.
  - Aggregational Gaussianity holds slowly (only over weeks to months).
- **Relevance to GTOS:** Foundational reference for what the GTOS edge *cannot* exploit (signed-return predictability) and *can* exploit (volatility-clustered regime structure). Bonferroni-survival / decay analyses must respect the slow-mixing implications.
- **Potential hypothesis:** —
- **Cross-domain flag:** 03_distributional_characteristics (primary owner per spec; this is theory anchor here)

---

## Section 3 — Recent advances 2020-2025

### Volatility is Rough
- **Authors:** Jim Gatheral, Thibault Jaisson, Mathieu Rosenbaum
- **Year/Source:** 2018 / Quantitative Finance 18(6): 933-949 (arXiv 1410.3394, 2014)
- **URL:** https://arxiv.org/abs/1410.3394 ; https://www.tandfonline.com/doi/abs/10.1080/14697688.2017.1393551
- **Abstract:** Estimates log-volatility from intraday realized variance and finds that the time series is *rougher* than Brownian motion, with empirical Hurst exponent H ≈ 0.1 across SPX and other equity indices. Proposes the Rough Fractional Stochastic Volatility (RFSV) model.
- **Key findings:**
  - Log-realized-variance is a fractional Brownian motion with H ≈ 0.1, not the H ≈ 0.5 of standard SV models.
  - The rough-volatility model fits the term structure of ATM skew without requiring jumps.
  - Apparent long-memory of volatility is a finite-sample artifact of rough fBM.
  - Extreme persistence in classical SV models can be replaced by simple anti-persistence at the right roughness exponent.
- **Relevance to GTOS:** Critical for kill-zone selection logic. If volatility is rough (H≈0.1), then near-future volatility is highly anti-persistent at short scales — which means session-volatility-based gating (H25) needs to weight by the rough-fBM forecast horizon, not classical SV-implied half-lives. Directly relevant to the F15 regime-conditioned decay memory: regime persistence under rough vol is shorter than under standard SV.
- **Potential hypothesis:** Conditioning OB-trade entry on a rough-volatility one-step-ahead forecast at H=0.1 outperforms ATR-band gating in cells where realized intra-day vol is in the top quartile; effect strongest on XAUUSD and US30.
- **Cross-domain flag:** 16_volatility_derivatives_vol_regime (cross-link; primary owner is here for theory, 16 for trading-rule)

### Pricing Under Rough Volatility
- **Authors:** Christian Bayer, Peter K. Friz, Jim Gatheral
- **Year/Source:** 2016 / Quantitative Finance 16(6): 887-904 (SSRN 2554754)
- **URL:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2554754 ; https://www.wias-berlin.de/people/bayerc/files/RSVPsubmitted2.pdf
- **Abstract:** Operationalizes the rough-volatility insight by introducing the rough Bergomi (rBergomi) model, a forward-variance / fractional-Brownian-motion-driven SV model. Demonstrates that rBergomi fits the SPX implied-vol surface with fewer parameters than classical Heston / Bergomi.
- **Key findings:**
  - rBergomi is a tractable rough-volatility specification with a closed-form forward-variance curve.
  - Calibration to SPX surfaces requires H ≈ 0.1, consistent with realized-vol estimates.
  - Implied-vol skew explodes at short maturities exactly as observed empirically.
  - Standard Markovian SV models *systematically* misprice the term structure of skew.
- **Relevance to GTOS:** Theoretical scaffold for the volatility-regime hypothesis underlying GTOS regime classifier; if forward-variance follows fBM with H=0.1, the regime classifier should use long memory windows even though the underlying realized-vol is short-memory in the classical sense.
- **Potential hypothesis:** —
- **Cross-domain flag:** 16_volatility_derivatives_vol_regime

### The Characteristic Function of Rough Heston Models
- **Authors:** Omar El Euch, Mathieu Rosenbaum
- **Year/Source:** 2019 / Mathematical Finance 29(1): 3-38 (arXiv 1609.02108)
- **URL:** https://arxiv.org/abs/1609.02108 ; https://onlinelibrary.wiley.com/doi/abs/10.1111/mafi.12173
- **Abstract:** Derives the characteristic function of the log-price in the rough Heston model via a fractional Riccati equation, exploiting an original link to nearly-unstable Hawkes processes. Despite non-Markovianity and non-semimartingale behavior, option pricing remains tractable.
- **Key findings:**
  - Rough Heston has a fractional Riccati equation for its characteristic function.
  - Microstructural foundation: the model is the limit of nearly-unstable Hawkes processes.
  - Implied-vol skew of order T^(H-1/2) for T → 0 (matches empirical SPX surface).
  - Calibration is computationally feasible despite non-Markovian nature.
- **Relevance to GTOS:** Anchors the connection between Hawkes-process tick clusters and rough volatility — the same micro-foundation underlying `tick_features.py` and the regime classifier. Tells GTOS researchers that the "long-memory of volatility" stylized fact and the "self-exciting trade arrival" stylized fact are two sides of the same coin.
- **Potential hypothesis:** —
- **Cross-domain flag:** 16_volatility_derivatives_vol_regime

### Solving High-Dimensional Partial Differential Equations Using Deep Learning
- **Authors:** Jiequn Han, Arnulf Jentzen, Weinan E
- **Year/Source:** 2018 / PNAS 115(34): 8505-8510 (arXiv 1707.02568)
- **URL:** https://www.pnas.org/doi/10.1073/pnas.1718942115 ; https://arxiv.org/abs/1707.02568
- **Abstract:** Introduces the Deep BSDE method: reformulates a high-dimensional parabolic PDE as a backward stochastic differential equation, parameterizes the gradient of the solution with a neural network, and trains end-to-end. Tractable for nonlinear Black-Scholes, HJB equations, and Allen-Cahn equations in 100+ dimensions.
- **Key findings:**
  - Curse-of-dimensionality break: high-dimensional PDEs solvable in seconds-to-minutes via deep BSDE.
  - The neural-network gradient acts as a stochastic-policy approximation in the spirit of deep RL.
  - Convergence guarantees under mild regularity assumptions.
  - Empirical accuracy on benchmark HJB problems is excellent in dim ≤ 100.
- **Relevance to GTOS:** Future-research enabler. If GTOS Phase-3 considers dynamic-programming-based optimal-stop or sizing problems where the value function lives in high-dim feature space (regime × tick-features × kill-zone × instrument), deep BSDE is the off-the-shelf solver. Directly bridges to K54 LightGBM successor — the deep-BSDE value-function is the principled supervisor.
- **Potential hypothesis:** A deep-BSDE-trained value function on the J46-J49 partial-close + time-stop problem outperforms the static threshold policy by ≥0.1 R/trade on the held-out 2026-Q2 sample.
- **Cross-domain flag:** 19_ai_ml_for_finance_classical_deep_sequence

### Deep Hedging
- **Authors:** Hans Buehler, Lukas Gonon, Josef Teichmann, Ben Wood
- **Year/Source:** 2019 / Quantitative Finance 19(8): 1271-1291 (arXiv 1802.03042)
- **URL:** https://arxiv.org/abs/1802.03042 ; https://www.tandfonline.com/doi/abs/10.1080/14697688.2019.1571683
- **Abstract:** Trains a neural-network hedging policy under transaction costs, market impact, and trading constraints by directly optimizing a coherent risk measure (CVaR) of terminal P&L. Generalizes Black-Scholes-Merton hedging to incomplete markets without explicit price-process parameterization.
- **Key findings:**
  - Reinforcement-learning-style policy training over Monte-Carlo paths converges to near-optimal hedges in non-trivial market models.
  - The framework is agnostic to underlying-process specification — direct from path data.
  - Cross-asset and exotic options are tractable in a unified pipeline.
  - Risk-measure choice (CVaR vs entropic vs quadratic) materially shapes the hedge.
- **Relevance to GTOS:** Methodological template for K54 ML successor. The "deep hedging" pipeline is one-step-removed from a deep-RL trading agent; the same architecture can be repurposed to learn an entry-policy / exit-policy that minimizes a CVaR over entry-and-hold returns. Directly cross-references K54+K55 ML-vs-AI shadow harness.
- **Potential hypothesis:** —
- **Cross-domain flag:** 20_rl_llms_in_trading

### A Course on Rough Paths (2nd ed)
- **Authors:** Peter K. Friz, Martin Hairer
- **Year/Source:** 2020 / Springer Universitext (textbook)
- **URL:** https://link.springer.com/book/10.1007/978-3-030-41556-3 ; https://www.hairer.org/notes/RoughPaths.pdf (online notes)
- **Abstract:** Self-contained graduate textbook on rough-path theory: signature, controlled rough paths, rough differential equations, Gaussian rough paths, application to SDEs and to regularity-structures-based SPDE theory (Hairer 2014).
- **Key findings:**
  - Pathwise solution theory for SDEs that recovers classical results without probabilistic adapted-ness assumptions.
  - The signature of a path is the universal feature in this theory.
  - Cameron-Martin / large-deviation results for Gaussian rough paths.
  - Bridges to KPZ and stochastic-PDE applications.
- **Relevance to GTOS:** Reference for principled path-feature engineering. The truncated signature of a price path is a candidate feature set for K54 v2 — directly addresses the "feature engineering" question in K54 by replacing ad-hoc engineered features with mathematically principled iterated-integrals.
- **Potential hypothesis:** —
- **Cross-domain flag:** 19_ai_ml_for_finance_classical_deep_sequence

### Signature Methods in Machine Learning
- **Authors:** Terry Lyons, Andrew D. McLeod
- **Year/Source:** 2022 / arXiv 2206.14674 (also EMS Surveys / Oxford ORA, periodically updated through 2025)
- **URL:** https://arxiv.org/abs/2206.14674 ; https://ora.ox.ac.uk/objects/uuid:282745c3-9835-4a96-ad7b-fb3631c33678
- **Abstract:** Survey + framework paper laying out the signature method as a universal, lossy-compressed, parameterization-invariant feature representation for irregular streamed data. Targets ML practitioners, with explicit financial-data examples (lead-lag transformation, time-augmentation).
- **Key findings:**
  - Signature linearizes nonlinear functionals on path space (universal-approximation).
  - Lead-lag and time-augmentation transformations encode no-look-ahead constraints.
  - Truncated signature gives a finite-dim feature embedding suitable for any standard ML model.
  - Computational cost is tractable for short paths (depths 3-5, dimensions 5-10).
- **Relevance to GTOS:** Direct K54 v2 candidate. Replace the engineered feature set with the depth-3 truncated signature of (price, ATR, volume) over the last N candles; train LightGBM on signature features rather than ad-hoc summaries. Probabilistically dominant when the signal is path-shape-encoded (BOS/CHoCH structure exactly fits this).
- **Potential hypothesis:** Replacing K54 features with depth-3 signature features over the last 10 H1 candles improves AUC by ≥0.02 on the H2-2026 holdout, controlled for total feature dimension.
- **Cross-domain flag:** 19_ai_ml_for_finance_classical_deep_sequence

### A Primer on the Signature Method in Machine Learning
- **Authors:** Ilya Chevyrev, Andrey Kormilitzin
- **Year/Source:** 2016 / arXiv 1603.03788
- **URL:** https://arxiv.org/abs/1603.03788
- **Abstract:** Pedagogical introduction to the signature transform, summarizing the algebraic, analytical, and geometric properties of iterated integrals of paths and how to use them as ML features.
- **Key findings:**
  - Definition and basic Chen-shuffle algebra of signatures.
  - Why the signature is a universal nonlinearity for path functionals.
  - Practical computation: log-signature, time augmentation, lead-lag, signed-area.
  - Worked examples on synthetic and time-series data.
- **Relevance to GTOS:** The bridge document for any GTOS engineer who needs to implement the signature pipeline before / during K54 v2 prototyping.
- **Potential hypothesis:** —
- **Cross-domain flag:** 19_ai_ml_for_finance_classical_deep_sequence

### Signature Methods in Stochastic Portfolio Theory
- **Authors:** Christa Cuchiero, Janka Möller
- **Year/Source:** 2024 / SIAM Journal on Financial Mathematics 16: 1239-1303 (arXiv 2310.02322)
- **URL:** https://epubs.siam.org/doi/10.1137/24M1700223 ; https://arxiv.org/abs/2310.02322
- **Abstract:** Develops a class of "linear path-functional portfolios" as transformations of linear functions of signatures of (ranked) market weights. Proves universal-approximation for these portfolios and demonstrates that signature portfolios can approximate the growth-optimal portfolio in non-Markovian settings.
- **Key findings:**
  - Signature portfolios are dense in the space of continuous path-functional portfolios.
  - Growth-optimal portfolios in classical stochastic-portfolio-theory models are well-approximated by short-truncation signature portfolios.
  - The framework operationalizes Fernholz-style stochastic-portfolio theory in a learnable, data-driven way.
  - Bridges signature ML to allocation / sizing problems.
- **Relevance to GTOS:** Most-recent (2024) operationalization of signatures for portfolio decisions. Direct bridge to S79 risk-policy follow-up: replace `uniform_fn 2.0% / NAS100 0.25%` with a signature-portfolio sizing rule that is path-aware. Highest-relevance paper in the recent-advances bucket.
- **Potential hypothesis:** A linear-path-functional sizing rule using depth-2 signatures of recent OB-zone-touch returns Pareto-dominates the static `uniform_fn 2.0%` Phase-1 winner on the J46-J49 portfolio policy backtest, lifting median R/trade by ≥0.05 with no increase in MDD.
- **Cross-domain flag:** 21_risk_management_kelly_sizing

### A Theory of Regularity Structures
- **Authors:** Martin Hairer
- **Year/Source:** 2014 / Inventiones Mathematicae 198(2): 269-504 (arXiv 1303.5113)
- **URL:** https://link.springer.com/article/10.1007/s00222-014-0505-4 ; https://www.hairer.org/papers/Structure.pdf
- **Abstract:** Hairer's Fields-Medal-winning paper introducing regularity structures, an algebraic framework that gives mathematically rigorous meaning to a large class of singular stochastic PDEs (KPZ, Φ⁴₃, parabolic Anderson model). Generalizes rough-path theory to space-time fields.
- **Key findings:**
  - "Modelled distribution" replaces classical Taylor expansion for irregular fields.
  - Renormalization group emerges naturally from the algebraic structure.
  - Subcritical singular SPDEs admit unique solutions in the regularity-structures sense.
  - Provides the rigorous theoretical foundation for KPZ-fluctuation models.
- **Relevance to GTOS:** Indirect — theoretical legitimacy for the rough-volatility / fractional-Brownian framework underlying H25 session-volatility shadow logger. Reading-list addition for the math-curious; not directly applied.
- **Potential hypothesis:** —
- **Cross-domain flag:** none

### Hawkes Processes in Finance
- **Authors:** Emmanuel Bacry, Iacopo Mastromatteo, Jean-François Muzy
- **Year/Source:** 2015 / Market Microstructure and Liquidity 1(1) (arXiv 1502.04592)
- **URL:** https://arxiv.org/abs/1502.04592 ; https://www.worldscientific.com/doi/10.1142/S2382626615500057
- **Abstract:** Comprehensive review of multivariate Hawkes-process applications in high-frequency finance: trade arrivals, order-flow clustering, lead-lag estimation, volatility modelling, optimal execution, and systemic-risk contagion.
- **Key findings:**
  - Self-exciting Hawkes kernels capture trade-arrival clustering empirically.
  - Lead-lag patterns across instruments are recoverable from cross-Hawkes kernels.
  - Hawkes-driven mid-price processes reproduce the Epps effect (correlation drop at high frequency).
  - Hawkes-based market-making and execution strategies outperform Poisson baselines.
- **Relevance to GTOS:** Direct theoretical foundation for `tick_features.py` and the cross-instrument correlation gate. The Bacry-Mastromatteo-Muzy framework predicts that the optimal correlation lag and threshold will vary with the realized Hawkes-kernel decay time — which is *not* what the current static |corr| ≥ 0.4 gate implements.
- **Potential hypothesis:** Replacing the static cross-instrument correlation threshold with a Hawkes-kernel-implied dynamic threshold reduces correlated-loss days by ≥10%, controlled for total trade frequency.
- **Cross-domain flag:** 06_market_microstructure_orderbook (cross-link); 13_cross_asset_correlation_factors

### Order Book Dynamics in Liquid Markets: Limit Theorems and Diffusion Approximations
- **Authors:** Rama Cont, Adrien de Larrard
- **Year/Source:** 2013 / SIAM Journal on Financial Mathematics 4: 1-25 (arXiv 1202.6412)
- **URL:** https://arxiv.org/abs/1202.6412 ; https://hal.science/hal-00672274v2
- **Abstract:** Develops a tractable Markovian queueing model for the limit-order book and proves a functional CLT showing the joint bid-ask depth process converges to a Markovian jump-diffusion in the positive orthant under high-frequency arrivals. Derives closed-form approximations for the probability of a price up-move and the duration to next move.
- **Key findings:**
  - Diffusion limit of LOB queues exists and is computable in closed form.
  - Probability of next price-up = 1 / (1 + (Sb / Sa)^β) for explicit β based on order-arrival rates.
  - Mid-price volatility is determined by relative arrival rates of buy/sell orders and cancellations.
  - The framework generalizes Kyle (1985) and Avellaneda-Stoikov (2008).
- **Relevance to GTOS:** Theoretical anchor for any GTOS expansion into deeper LOB / book-imbalance features. The Cont-de Larrard up-move probability is exactly what `tick_features.py` should be approximating for prop-firm-relevant short windows.
- **Potential hypothesis:** —
- **Cross-domain flag:** 06_market_microstructure_orderbook

### High-Frequency Trading in a Limit Order Book (Optimal Market Making)
- **Authors:** Marco Avellaneda, Sasha Stoikov
- **Year/Source:** 2008 / Quantitative Finance 8(3): 217-224
- **URL:** https://people.orie.cornell.edu/sfs33/LimitOrderBook.pdf ; https://www.tandfonline.com/doi/abs/10.1080/14697680701381228
- **Abstract:** Formulates market-making as a stochastic-control problem: a dealer posting bid-ask quotes facing a Brownian mid-price and Poisson order-arrival rates that depend exponentially on quote distance from mid. Derives the Hamilton-Jacobi-Bellman PDE for the value function and gives a closed-form approximation for the optimal bid-ask spread.
- **Key findings:**
  - Optimal indifference quotes are a function of inventory, time-to-end, and risk-aversion.
  - Bid-ask spread = inventory-risk premium + adverse-selection-mitigation premium.
  - The framework cleanly decomposes spread into two interpretable components.
  - Empirical fits on equity / FX data are reasonable for moderate horizons.
- **Relevance to GTOS:** GTOS is a directional taker, not a market-maker, so direct application is limited. However, the Avellaneda-Stoikov inventory-risk decomposition is the dual of GTOS's risk-budget logic, and the asymptotic closed-form for optimal spread provides a calibration for what the *expected adverse-selection* is at any given OB-zone touch — i.e., Kyle's λ in continuous form.
- **Potential hypothesis:** —
- **Cross-domain flag:** 06_market_microstructure_orderbook

### Optimal Execution of Portfolio Transactions
- **Authors:** Robert Almgren, Neil Chriss
- **Year/Source:** 2001 / Journal of Risk 3(2): 5-39
- **URL:** https://www.smallake.kr/wp-content/uploads/2016/03/optliq.pdf ; https://www.risk.net/journal-risk/2161150/optimal-execution-portfolio-transactions
- **Abstract:** Frames execution of a parent order as a tradeoff between volatility risk (cost of holding position) and impact cost (cost of trading too fast). Constructs an explicit efficient frontier in liquidation-strategy space; introduces L-VaR (liquidity-adjusted VaR).
- **Key findings:**
  - Closed-form efficient frontier under linear permanent + temporary impact and Gaussian price.
  - Optimal liquidation trajectory is a deterministic linear-in-time profile under quadratic utility.
  - L-VaR formalizes the volatility-impact tradeoff.
  - Framework extends to continuous-time stochastic optimization.
- **Relevance to GTOS:** GTOS executes single orders, not metaorders, so direct application is small. The framework's *concept* of trading off volatility risk against impact cost reappears in GTOS as the tradeoff between widening SL (reducing premature-stop risk) and tightening TP (capturing more on success) — same Bellman / efficient-frontier structure.
- **Potential hypothesis:** —
- **Cross-domain flag:** 06_market_microstructure_orderbook

### A Fully Consistent, Minimal Model for Non-Linear Market Impact
- **Authors:** Jonathan Donier, Julius Bonart, Iacopo Mastromatteo, Jean-Philippe Bouchaud
- **Year/Source:** 2015 / Quantitative Finance 15(7): 1109-1121 (arXiv 1412.0141)
- **URL:** https://arxiv.org/abs/1412.0141 ; https://www.tandfonline.com/doi/abs/10.1080/14697688.2015.1040056
- **Abstract:** Derives the universal square-root impact law from a minimal latent-order-book model: fictitious limit orders distributed on either side of a moving mid-price, executed against incoming metaorders. The diffusion-reaction approximation gives explicit closed-form impact trajectories.
- **Key findings:**
  - Square-root impact emerges generically from latent-order-book diffusion-reaction dynamics.
  - The framework consistently nests linear (small order) and concave (large order) impact regimes.
  - Permanent impact is linear in volume traded.
  - Cross-validates Almgren-Chriss in the small-order limit and the empirical √Q law in the metaorder limit.
- **Relevance to GTOS:** Theoretical backing for *why* GTOS sees no live market impact at its current trade sizes (redacted_account $100k; lots ≪ instrument ADV) — confirms the linear regime, where latent-book microstructure is irrelevant. Becomes relevant only at much larger AUM.
- **Potential hypothesis:** —
- **Cross-domain flag:** 06_market_microstructure_orderbook

### Backward Stochastic Differential Equations in Finance
- **Authors:** Nicole El Karoui, Shige Peng, Marie-Claire Quenez
- **Year/Source:** 1997 / Mathematical Finance 7(1): 1-71
- **URL:** https://onlinelibrary.wiley.com/doi/abs/10.1111/1467-9965.00022
- **Abstract:** Surveys the BSDE framework for nonlinear pricing, recursive utility, and constrained-portfolio problems. Establishes existence/uniqueness, comparison principles, and connections to Hamilton-Jacobi-Bellman PDE for option-pricing applications.
- **Key findings:**
  - BSDE is the natural language for nonlinear contingent-claim pricing under constraints.
  - Comparison theorem: monotone-in-driver gives monotone-in-solution.
  - Connection to PDEs via the four-step scheme of Ma-Protter-Yong.
  - Formalizes recursive utility (Duffie-Epstein) and constrained-portfolio Karatzas-Cvitanic theory.
- **Relevance to GTOS:** Theoretical anchor for any GTOS expansion into utility-based sizing. The El Karoui-Peng-Quenez framework provides the principled way to derive Kelly-fraction-like rules under non-quadratic utility.
- **Potential hypothesis:** —
- **Cross-domain flag:** 21_risk_management_kelly_sizing

### Drawdown: From Practice to Theory and Back Again
- **Authors:** Lisa R. Goldberg, Ola Mahmoud (also incorporates Pospisil-Vecer)
- **Year/Source:** 2017 / Mathematics and Financial Economics (arXiv 1404.7493)
- **URL:** https://arxiv.org/abs/1404.7493 ; https://link.springer.com/article/10.1007/s11579-016-0181-9
- **Abstract:** Reviews and synthesizes drawdown theory, connecting practitioner risk measures (max drawdown, conditional drawdown, drawdown-at-risk) to closed-form formulas under Black-Scholes-like dynamics and to PDE methods (Pospisil-Vecer 2010) for general diffusions.
- **Key findings:**
  - Closed-form expected-max-drawdown for drifted Brownian motion via PDE methods.
  - Drawdown-as-stopping-time results extend to Ornstein-Uhlenbeck and CIR processes.
  - Drawdown is *not* a coherent risk measure but admits coherent variants (CDaR).
  - Bridges actuarial-style ruin theory to investment-management drawdown control.
- **Relevance to GTOS:** Direct theoretical anchor for the H29 8% drawdown position-reduction rule and for redacted_account compliance gates. The closed-form expected-max-drawdown predicts the threshold where DD reduction kicks in optimally; GTOS's hardcoded 8% may be too conservative in low-vol regimes and too lax in high-vol regimes.
- **Potential hypothesis:** Replacing the fixed 8% DD reduction trigger with a vol-conditioned trigger (e.g., 8% × ATR-ratio) reduces the false-trigger rate by ≥30% on the H1-2026 sample without increasing realized max-DD on the H2-2026 sample.
- **Cross-domain flag:** 21_risk_management_kelly_sizing

### Markov Decision Processes with Applications to Finance
- **Authors:** Nicole Bäuerle, Ulrich Rieder
- **Year/Source:** 2011 / Springer Universitext (textbook)
- **URL:** https://link.springer.com/book/10.1007/978-3-642-18324-9
- **Abstract:** Self-contained graduate textbook on the Markov-decision-process framework with explicit financial / actuarial applications: portfolio optimization, optimal stopping (American options), partial-observability, piecewise-deterministic processes, drawdown control.
- **Key findings:**
  - General-state-space MDP existence theorems with finance-style integrability assumptions.
  - Bellman-equation reductions for portfolio / stopping problems.
  - PD-MDP framework for jump-diffusion control.
  - Worked examples on consumption-investment and option exercise.
- **Relevance to GTOS:** Reference text for any rigorous treatment of GTOS as an MDP. Directly applicable to phrasing the J46-J49 partial-close + time-stop problem as a finite-horizon MDP and computing the Bellman-optimal policy as a benchmark for the empirical winner.
- **Potential hypothesis:** —
- **Cross-domain flag:** 20_rl_llms_in_trading

### Levy Processes and Infinitely Divisible Distributions
- **Authors:** Ken-iti Sato
- **Year/Source:** 1999 / Cambridge Studies in Advanced Mathematics 68 (textbook, paperback 2013)
- **URL:** https://www.cambridge.org/9780521553025 ; https://archive.org/details/levyprocessesinf0000sato
- **Abstract:** Standard rigorous reference on Levy processes and infinite divisibility. Covers the Levy-Khintchine formula, Levy measure construction, semi-stable / stable / tempered-stable subclasses, and asymptotic-tail / first-passage results for spectrally one-sided processes.
- **Key findings:**
  - Complete classification of infinitely divisible distributions via Levy-Khintchine.
  - Wiener-Hopf factorization for one-sided Levy processes.
  - Subordinator construction (variance-gamma, normal-inverse-Gaussian, CGMY).
  - Asymptotic-tail results connecting Levy measure to extreme behavior.
- **Relevance to GTOS:** Reference text for any researcher analyzing tick-data fat-tail phenomena under a Levy null. Directly relevant to project_distributional_findings (ξ=0.35 fat tail).
- **Potential hypothesis:** —
- **Cross-domain flag:** 03_distributional_characteristics

### Financial Modelling with Jump Processes
- **Authors:** Rama Cont, Peter Tankov
- **Year/Source:** 2004 / Chapman & Hall / CRC Financial Mathematics Series (textbook)
- **URL:** https://www.taylorfrancis.com/books/mono/10.1201/9780203485217/financial-modelling-jump-processes-rama-cont-peter-tankov
- **Abstract:** Comprehensive treatment of jump-process modelling for finance: Levy processes, jump-diffusion, time-changed Brownian motion, calibration of Levy models, simulation, exotic-option pricing under jumps. Practitioner-friendly.
- **Key findings:**
  - Calibration of Levy models from option-implied data (FFT methods).
  - Practical Monte-Carlo schemes for jump-diffusion.
  - Empirical fit comparison: variance-gamma vs CGMY vs Merton vs Kou.
  - Risk-management implications of jump-vs-diffusion attribution.
- **Relevance to GTOS:** Practical reference for parameterizing the buffer multipliers under a jump-aware null. Cross-references project_distributional_findings memory directly.
- **Potential hypothesis:** —
- **Cross-domain flag:** 03_distributional_characteristics

---

## Section 4 — Methodological tools

### A Jump-Diffusion Model for Option Pricing (Double-Exponential)
- **Authors:** Steven G. Kou
- **Year/Source:** 2002 / Management Science 48(8): 1086-1101
- **URL:** http://www.columbia.edu/~sk75/MagSci02.pdf ; https://ideas.repec.org/a/inm/ormnsc/v48y2002i8p1086-1101.html
- **Abstract:** Replaces Merton's log-normal jumps with double-exponential jump sizes, gaining analytical tractability for first-passage and barrier problems. Closed-form solutions for European, perpetual American, lookback, barrier, and many path-dependent options.
- **Key findings:**
  - Memoryless property of exponential distribution preserves first-passage tractability.
  - Closed-form perpetual-American put under double-exponential jumps.
  - Closed-form barrier-option prices.
  - Empirical fit captures leptokurtosis and skew with parsimony.
- **Relevance to GTOS:** *The* methodological tool for stop-loss / take-profit hitting probability under a jump null. Directly cited in any rigorous SL-buffer calibration. Bridge: Kou's first-passage formulae give the exact probability that an entry at OB midpoint survives 1 ATR for N candles — testable against GTOS's empirical SL-survival curves.
- **Potential hypothesis:** Calibrating Kou parameters from XAUUSD M15 returns, the model-implied 1-ATR-survival probability for the typical OB-retest entry is within ±2pp of the empirical realized survival on 2026-Q1; deviations on H2-2026 reveal regime shift.
- **Cross-domain flag:** none

### Hyperbolic Distributions in Finance
- **Authors:** Ernst Eberlein, Ulrich Keller
- **Year/Source:** 1995 / Bernoulli 1(3): 281-299
- **URL:** https://projecteuclid.org/journals/bernoulli/volume-1/issue-3/Hyperbolic-distributions-in-finance/10.3150/bj/1193667819.full
- **Abstract:** Introduces the generalized-hyperbolic (GH) family of Levy processes as a flexible alternative to Brownian motion for daily equity returns. Calibrates to DAX equity data and prices European options via the Esscher transform.
- **Key findings:**
  - GH family fits daily DAX returns dramatically better than Gaussian.
  - The Esscher transform gives a simple equivalent-martingale measure.
  - Implied-vol corrections relative to Black-Scholes are systematic and tradable.
  - Foundational work for the broader Levy-finance program.
- **Relevance to GTOS:** Reference for any analyst calibrating heavy-tail / skewed daily-return models for the GTOS instrument set. Sets the precedent for using Levy-process Esscher-transformed densities for short-horizon risk-aware sizing.
- **Potential hypothesis:** —
- **Cross-domain flag:** 03_distributional_characteristics

### The Variance Gamma Process and Option Pricing
- **Authors:** Dilip B. Madan, Peter Carr, Eric C. Chang
- **Year/Source:** 1998 / Review of Finance / European Finance Review 2(1): 79-105
- **URL:** https://engineering.nyu.edu/sites/default/files/2018-09/CarrEuropeanFinReview1998.pdf ; https://academic.oup.com/rof/article-abstract/2/1/79/1581894
- **Abstract:** Three-parameter variance-gamma (VG) process: Brownian motion with drift evaluated at a gamma-distributed random clock. Captures skew and excess kurtosis with parsimony; closed-form for European options.
- **Key findings:**
  - VG = Gaussian × gamma-time-change (subordination).
  - Three parameters control mean, kurtosis, and skew independently.
  - Closed-form European call / put.
  - Statistical density (S&P 500) is symmetric with some kurtosis; risk-neutral density is negatively skewed and more leptokurtic.
- **Relevance to GTOS:** Methodological tool for fitting subordinated jump models to GTOS instrument tick data. Directly bridges to Clark (1973) trading-time intuition.
- **Potential hypothesis:** —
- **Cross-domain flag:** 03_distributional_characteristics

### The Fine Structure of Asset Returns (CGMY Process)
- **Authors:** Peter Carr, Hélyette Geman, Dilip B. Madan, Marc Yor
- **Year/Source:** 2002 / Journal of Business 75(2): 305-332
- **URL:** https://www.jstor.org/stable/10.1086/338705 ; https://engineering.nyu.edu/sites/default/files/2018-09/CarrJournalofBusiness2002.pdf
- **Abstract:** Generalizes the variance-gamma model to the four-parameter CGMY family of pure-jump Levy processes and tests whether real equity returns have a continuous component (diffusion) or are purely jump. Empirical verdict: pure-jump processes of infinite activity and finite variation fit best.
- **Key findings:**
  - Four-parameter CGMY family nests VG, NIG, and stable subclasses.
  - For most equities, the diffusion component is statistically zero.
  - Statistical and risk-neutral processes are infinite-activity, finite-variation pure-jump processes.
  - Skewness and kurtosis are governed by separate parameters of CGMY.
- **Relevance to GTOS:** *Critical* finding: if equity-style instruments are pure-jump, then SL-design under a pure-Brownian (Bachelier / Black-Scholes) null is fundamentally mis-specified. CGMY-based SL calibration is a direct GTOS-actionable extension.
- **Potential hypothesis:** Recalibrating XAUUSD / NAS100 SL buffer multipliers under a CGMY null with parameters fitted from 2026 tick data shifts optimal buffer ATR-multiples by ≥0.2 vs the current Brownian-implied calibration; back-tested R/trade improves ≥0.05 on H2-2026.
- **Cross-domain flag:** 03_distributional_characteristics

### Non-Gaussian Ornstein-Uhlenbeck-Based Models in Financial Economics
- **Authors:** Ole E. Barndorff-Nielsen, Neil Shephard
- **Year/Source:** 2001 / Journal of the Royal Statistical Society B 63(2): 167-241
- **URL:** https://shephard.scholars.harvard.edu/sites/g/files/omnuum7741/files/jrssb01.pdf ; https://rss.onlinelibrary.wiley.com/doi/abs/10.1111/1467-9868.00282
- **Abstract:** Develops a class of stochastic-volatility models where realized variance is the integral of a positive-OU process driven by a Levy subordinator. Closed-form characteristic functions for option pricing; tractable likelihood for inference.
- **Key findings:**
  - Positive-OU dynamics with Levy noise capture volatility-clustering and leverage effects.
  - Superpositions of OU components give multi-time-scale memory.
  - Option-pricing characteristic functions in closed form.
  - Inference via auxiliary-particle filtering / quasi-likelihood.
- **Relevance to GTOS:** Methodological bridge between empirical realized-volatility-clustering (`tick_features.py`) and tractable forward-vol estimates. Useful for replacing the static H25 session-vol bands with a BNS-driven adaptive window.
- **Potential hypothesis:** —
- **Cross-domain flag:** 16_volatility_derivatives_vol_regime

### Long Memory in Continuous-Time Stochastic Volatility Models
- **Authors:** Fabienne Comte, Eric Renault
- **Year/Source:** 1998 / Mathematical Finance 8(4): 291-323
- **URL:** http://w.long-memory.com/returns/ComteRenault1998.pdf ; https://onlinelibrary.wiley.com/doi/10.1111/1467-9965.00057
- **Abstract:** Pre-rough-volatility extension of Black-Scholes where log-volatility is a fractional Brownian motion with H > 1/2 (long memory). Derives implications for implied-vol-surface persistence, especially at long maturities.
- **Key findings:**
  - Long-memory log-vol gives slow decay of implied-vol-skew with maturity.
  - Inference framework for fractional log-vol from realized-vol time series.
  - Predates the rough-vol H < 1/2 finding by 15+ years; now superseded for short maturities.
- **Relevance to GTOS:** Historical anchor; reads now as a dual to rough-vol. Important to know GTOS researchers should distinguish *short-horizon* roughness (relevant for kill-zone-scale gating) from *long-horizon* persistence (relevant for monthly capital-allocation regime detection).
- **Potential hypothesis:** —
- **Cross-domain flag:** 16_volatility_derivatives_vol_regime

### Hawkes Models and Their Applications (Recent Synthesis)
- **Authors:** Patrick J. Laub, Young Lee, Philip K. Pollett, Thomas Taimre (also see Bacry-Mastromatteo-Muzy 2015 above)
- **Year/Source:** 2024 / arXiv 2405.10527
- **URL:** https://arxiv.org/html/2405.10527v1
- **Abstract:** Recent comprehensive review (2024) of Hawkes-process methodology and applications, expanding on the Bacry-Mastromatteo-Muzy (2015) review with newer ML-based estimators, multivariate / mutually-exciting kernels, and high-frequency-finance case studies.
- **Key findings:**
  - Modern (deep-learning) estimators for Hawkes intensities.
  - Cross-asset spillover detection via multi-Hawkes inference.
  - Volatility-Hawkes link strengthened with empirical recent evidence.
  - Practical implementations for high-frequency contagion modelling.
- **Relevance to GTOS:** Latest tools for the cross-instrument correlation gate redesign. Bridges to the same `tick_features.py` infrastructure; directly cited from F11 / F15 decay-velocity follow-ups.
- **Potential hypothesis:** —
- **Cross-domain flag:** 06_market_microstructure_orderbook

### Differential Equations Driven by Rough Signals
- **Authors:** Terry J. Lyons
- **Year/Source:** 1998 / Revista Matemática Iberoamericana 14(2): 215-310
- **URL:** http://dmle.icmat.es/pdf/MATEMATICAIBEROAMERICANA_1998_14_02_01.pdf ; https://ems.press/journals/rmi/articles/5137
- **Abstract:** Founding paper of rough-path theory. Constructs a deterministic, pathwise solution theory for SDEs driven by paths rougher than Brownian motion. The signature emerges as the universal feature.
- **Key findings:**
  - Rough-paths ITO-Lyons map is continuous in path topology — robust to noise and discretization.
  - Generalizes Young's theorem for paths of low regularity.
  - Deterministic foundation eliminates probability-dependence of stochastic-integral construction.
  - Sets up Lyons-Hambly uniqueness program (2010).
- **Relevance to GTOS:** Theoretical bedrock for any GTOS use of signature features. The Ito-Lyons continuity ensures that signature-feature-based ML models are *robust* to small input perturbations — important for production deployment under noisy tick data.
- **Potential hypothesis:** —
- **Cross-domain flag:** 19_ai_ml_for_finance_classical_deep_sequence

### Uniqueness for the Signature of a Path of Bounded Variation
- **Authors:** Ben Hambly, Terry Lyons
- **Year/Source:** 2010 / Annals of Mathematics 171(1): 109-167
- **URL:** https://annals.math.princeton.edu/2010/171-1/p02 ; https://people.maths.ox.ac.uk/hambly/PDF/Papers/sig.pdf
- **Abstract:** Proves that two finite-length paths share the same signature iff they are tree-like-equivalent, via the Reduced Path Group. Generalizes Chen's theorem and is the formal bedrock for using truncated signatures as ML features.
- **Key findings:**
  - Signature uniqueness modulo tree-like cancellation.
  - Reduced Path Group structure mirrors free-group word reduction.
  - Foundational result for signature-based ML.
- **Relevance to GTOS:** Theoretical guarantee that a (sufficiently deep) signature feature embedding is *injective* on relevant input paths — a precondition for K54 v2 feasibility.
- **Potential hypothesis:** —
- **Cross-domain flag:** 19_ai_ml_for_finance_classical_deep_sequence

### Iterated Path Integrals (Foundation of Signature Theory)
- **Authors:** Kuo-Tsai Chen
- **Year/Source:** 1957 / Annals of Mathematics 65 / 1977 Bulletin AMS review
- **URL:** https://www.ams.org/journals/bull/1977-83-05/S0002-9904-1977-14320-6/home.html ; https://projecteuclid.org/euclid.bams/1183539443
- **Abstract:** Original construction of the iterated-integral signature of a smooth path and the Chen-shuffle algebra. Establishes the algebraic structure that Lyons (1998) and the modern signature literature build on.
- **Key findings:**
  - Iterated integrals satisfy the Chen identity (concatenation = tensor product).
  - The shuffle algebra makes signature-of-product equal product-of-signatures, modulo shuffles.
  - Path uniqueness up to reparameterization (extended by Hambly-Lyons 2010).
- **Relevance to GTOS:** Historical-mathematical anchor. Read alongside Lyons (1998) for full theoretical context.
- **Potential hypothesis:** —
- **Cross-domain flag:** none

### Lévy Processes in Finance: Pricing Financial Derivatives
- **Authors:** Wim Schoutens
- **Year/Source:** 2003 / John Wiley & Sons (textbook)
- **URL:** https://onlinelibrary.wiley.com/doi/book/10.1002/0470870230 ; https://archive.org/details/levyprocessesinf0000scho
- **Abstract:** Practitioner-oriented textbook on Levy-process modelling in finance: variance-gamma, NIG, CGMY, Meixner, hyperbolic, stochastic-vol-with-jumps, calibration, simulation, exotic-option pricing.
- **Key findings:**
  - FFT-based calibration of Levy models from option chains.
  - Monte-Carlo schemes for jump-diffusion exotic-option pricing.
  - Worked examples on real market data.
  - Comparative-fit tables for Levy-process families.
- **Relevance to GTOS:** Practical handbook for any GTOS Levy-calibration task.
- **Potential hypothesis:** —
- **Cross-domain flag:** 03_distributional_characteristics

### Monte Carlo Methods in Financial Engineering
- **Authors:** Paul Glasserman
- **Year/Source:** 2003 / Springer Stochastic Modelling and Applied Probability 53 (textbook)
- **URL:** https://link.springer.com/book/10.1007/978-0-387-21617-1
- **Abstract:** Standard reference on simulation methods for finance: Brownian / Levy / jump-diffusion path generation, variance-reduction (importance, control, antithetic, stratified), American-option simulation (Longstaff-Schwartz), sensitivity (Greeks) computation, and credit / market risk.
- **Key findings:**
  - Variance-reduction techniques can lower simulation cost by ≥10× for option pricing.
  - Longstaff-Schwartz regression is the standard for American-option Monte Carlo.
  - Quasi-Monte-Carlo (Halton/Sobol) sequences improve high-dim convergence.
  - Practical implementations of all canonical Levy-process simulation schemes.
- **Relevance to GTOS:** Reference for any GTOS Monte-Carlo-based stress test (FN P(pass), TS variance, drawdown distribution); immediately applicable.
- **Potential hypothesis:** —
- **Cross-domain flag:** 02_statistical_methodology

### Generalized Autoregressive Conditional Heteroskedasticity (GARCH)
- **Authors:** Tim Bollerslev
- **Year/Source:** 1986 / Journal of Econometrics 31(3): 307-327
- **URL:** https://public.econ.duke.edu/~boller/Published_Papers/joe_86.pdf
- **Abstract:** Generalizes Engle (1982) ARCH by adding lagged-conditional-variance terms; produces GARCH(p,q) models with parsimonious lag structure. Now the standard parametric volatility model.
- **Key findings:**
  - GARCH(1,1) often suffices empirically.
  - Stationarity and ergodicity conditions explicit.
  - MLE estimation tractable via direct numerical optimization.
- **Relevance to GTOS:** Reference for any volatility-clustering modelling. Directly relevant to the F15 / decay-monitor analytics; not used in production but the asymptotic intuition matters for SPRT design.
- **Potential hypothesis:** —
- **Cross-domain flag:** 03_distributional_characteristics

### Autoregressive Conditional Heteroskedasticity (ARCH)
- **Authors:** Robert F. Engle
- **Year/Source:** 1982 / Econometrica 50(4): 987-1007
- **URL:** http://www.econ.uiuc.edu/~econ536/Papers/engle82.pdf
- **Abstract:** Original ARCH paper. Introduces conditional-heteroskedasticity processes with mean-zero, serially-uncorrelated innovations whose conditional variance depends on past squared innovations. Originally applied to UK inflation; rapidly adopted for finance.
- **Key findings:**
  - Conditional-mean-zero processes can have non-iid conditional variance.
  - Lagrange-multiplier test for ARCH effects.
  - MLE asymptotic theory for conditional-variance models.
- **Relevance to GTOS:** Foundational reference for volatility-clustering econometrics.
- **Potential hypothesis:** —
- **Cross-domain flag:** 03_distributional_characteristics

### Dynamic Conditional Correlation
- **Authors:** Robert F. Engle
- **Year/Source:** 2002 / Journal of Business and Economic Statistics 20(3): 339-350
- **URL:** https://faculty.washington.edu/ezivot/econ589/EngleDCCJBES.pdf
- **Abstract:** Multivariate GARCH framework where univariate GARCH models drive standardized residuals whose conditional correlations follow a parsimonious GARCH-style recursion. Tractable for large cross-sections.
- **Key findings:**
  - Two-step estimation: univariate GARCH first, then DCC residual correlations.
  - Asymptotic theory and standard inference apply.
  - Empirical fits on 100+ stock universes are tractable.
- **Relevance to GTOS:** Reference for any GTOS expansion of the cross-instrument correlation gate to DCC-conditioned dynamic thresholds. Direct upgrade path from current static |corr| ≥ 0.4 gate.
- **Potential hypothesis:** —
- **Cross-domain flag:** 13_cross_asset_correlation_factors

---

## Section 5 — Contrarian / under-cited findings

### Scaling and Criticality in a Stochastic Multi-Agent Model of a Financial Market
- **Authors:** Thomas Lux, Michele Marchesi
- **Year/Source:** 1999 / Nature 397: 498-500
- **URL:** http://finance.martinsewell.com/stylized-facts/scaling/LuxMarchesi1999.pdf ; https://www.nature.com/articles/17290
- **Abstract:** Demonstrates that simple agent-based herding-and-fundamentalist mixing reproduces the canonical stylized facts (heavy tails, vol clustering) without any fat-tailed-input assumption. The fat tails *emerge* from agent-interaction structure.
- **Key findings:**
  - Heavy tails arise from herding dynamics, not noise input.
  - Vol clustering emerges from regime-switching among agent strategies.
  - The "near-critical" point of the agent population maximizes scaling-law fidelity.
  - Bridges econophysics to finance.
- **Relevance to GTOS:** Contrarian to "the edge is fixed in the price process": Lux-Marchesi suggests the edge is in the *current* mix of trader strategies, which is regime-dependent. Directly supports the F15 regime-conditioned-decay finding (memory `project_f15_synthesis_regime_is_load_bearing`). The OB-zone edge degrading is consistent with a shift in fundamentalist-vs-herder mix.
- **Potential hypothesis:** OB-zone WR is monotonically related to a herding-index proxy (cross-asset trade-time correlation in the formation window); cells where the herding index is in the bottom decile have OB-WR no better than mechanical baseline (consistent with A1 SYSTEM_DECAY).
- **Cross-domain flag:** 17_behavioral_adaptive_markets

### Wealth Condensation in a Simple Model of Economy
- **Authors:** Jean-Philippe Bouchaud, Marc Mezard
- **Year/Source:** 2000 / Physica A 282(3-4): 536-545
- **URL:** http://www.lptms.universite-paris-saclay.fr/membres/mezard/Pdf/00_BM_PA.pdf ; https://arxiv.org/abs/cond-mat/0002374
- **Abstract:** Toy model of agents with multiplicative wealth dynamics + exchange. Shows that under multiplicative noise, the steady-state distribution is power-law (Pareto) — wealth condenses on a vanishing fraction of agents. Connects to financial-return power laws.
- **Key findings:**
  - Multiplicative-noise mean-field gives power-law steady state with exponent governed by exchange-rate / variance ratio.
  - Wealth condensation phase transition exists.
  - Mechanism is robust across topology / detail.
- **Relevance to GTOS:** Contrarian framing for prop-firm survival modeling: a portfolio of GTOS instruments under multiplicative R-noise *will* condense onto winners by the same mechanism. Directly relevant to S79 risk-policy design and the decision to *not* uniformly down-weight underperformers prematurely.
- **Potential hypothesis:** —
- **Cross-domain flag:** 21_risk_management_kelly_sizing

### Herd Behavior and Aggregate Fluctuations in Financial Markets
- **Authors:** Rama Cont, Jean-Philippe Bouchaud
- **Year/Source:** 2000 / Macroeconomic Dynamics 4(2): 170-196 (arXiv cond-mat/9712318)
- **URL:** http://rama.cont.perso.math.cnrs.fr/pdf/herd.pdf ; https://arxiv.org/abs/cond-mat/9712318
- **Abstract:** Random-graph model of agents whose connectivity drives synchronization of orders. Power-law distribution of cluster sizes implies power-law distribution of price-change magnitudes — formal mechanism for fat tails as emergent from herding.
- **Key findings:**
  - Random-graph cluster-size distribution + cluster-driven aggregate orders → power-law returns.
  - Critical-percolation-like transition in herd-size distribution.
  - Excess kurtosis is determined by the connectivity exponent of the agent graph.
- **Relevance to GTOS:** Directly relates to the cross-instrument correlation gate: cross-asset herding episodes (NFP / FOMC / unscheduled events) are exactly the cluster-spike events Cont-Bouchaud predict. The current gate is a coarse proxy for the cluster-detection mechanism.
- **Potential hypothesis:** Replacing the |corr| threshold with a cluster-size-based gate (using realized synchronized-tick-arrivals across instruments) reduces false-correlation REJECTs by ≥20% on the H1-2026 sample.
- **Cross-domain flag:** 13_cross_asset_correlation_factors

### A Multifractal Model of Asset Returns
- **Authors:** Benoit B. Mandelbrot, Adlai J. Fisher, Laurent E. Calvet
- **Year/Source:** 1997 / Cowles Foundation Discussion Paper #1164
- **URL:** https://elischolar.library.yale.edu/cowles-discussion-paper-series/1412/ ; https://users.math.yale.edu/~bbm3/web_pdfs/Cowles1164.pdf
- **Abstract:** Multifractal Model of Asset Returns (MMAR): Brownian motion in fractal time, where the time-deformation is a multifractal cascade. Long-memory in absolute returns combined with finite-variance, scale-invariant moment behavior.
- **Key findings:**
  - Multi-scaling moments — different orders scale with different exponents.
  - Long-memory in volatility *without* long-memory in returns.
  - Bridges Levy-stable (1963 Mandelbrot) and fBM (1968 Mandelbrot-Van Ness) models.
  - Empirical fits on FX (1997 companion paper) are excellent.
- **Relevance to GTOS:** Contrarian-from-the-1990s to mainstream rough-vol consensus. Multifractal time-deformation is a competitor mechanism for the same stylized facts captured by rough-vol; under-cited in modern ML-finance papers. May offer better short-horizon (M15) calibrations than rough-Bergomi.
- **Potential hypothesis:** A multifractal time-deformation backtest of XAUUSD M15 returns (Calvet-Fisher 2002 implementation) gives a session-volatility forecast that outperforms the H25 GARCH baseline by ≥10% in MSE.
- **Cross-domain flag:** 04_multitimeframe_fractal_wavelets

### Robustness of the R/S Statistic for Long-Run Dependence
- **Authors:** Benoit B. Mandelbrot, James R. Wallis
- **Year/Source:** 1969 / Water Resources Research 5(5): 967-988
- **URL:** https://www.scirp.org/reference/ReferencesPapers?ReferenceID=1066326 (citation; 1969 hardcopy)
- **Abstract:** Demonstrates via Monte-Carlo that the R/S (rescaled-range) statistic for Hurst-exponent estimation is robust to non-Gaussian innovations (lognormal, hyperbolic, truncated-Gaussian) and to a wide class of nonlinear transformations. Susceptible primarily to strong periodicity.
- **Key findings:**
  - R/S is robust to heavy-tailed innovations and to nonlinear transforms.
  - R/S is *not* robust to strong periodicity in the data.
  - Practical estimation guidance for hydrological / financial Hurst-exponent computation.
- **Relevance to GTOS:** Methodological tool for the F11 / decay-velocity analytics: any Hurst-exponent estimate of OB-survival should be R/S-based and explicitly checked for kill-zone-induced periodicity (which is exactly the failure mode Mandelbrot-Wallis warn about). Under-cited in finance-ML; mostly cited in hydrology.
- **Potential hypothesis:** —
- **Cross-domain flag:** 04_multitimeframe_fractal_wavelets

### Modelling Extremal Events for Insurance and Finance
- **Authors:** Paul Embrechts, Claudia Klüppelberg, Thomas Mikosch
- **Year/Source:** 1997 / Springer Stochastic Modelling and Applied Probability (textbook)
- **URL:** https://link.springer.com/book/10.1007/978-3-642-33483-2
- **Abstract:** Comprehensive textbook on extreme-value theory (EVT) for insurance + finance: ruin theory, max-domain-of-attraction theorems, point-process methods, statistical estimation of tail probabilities, subexponential / regularly-varying distributions.
- **Key findings:**
  - Generalized Pareto / extreme-value distribution as the universal limit of threshold exceedances.
  - Hill estimator and its asymptotic theory.
  - Spectral theory of heavy-tailed time series.
  - Subexponential distributions and their role in ruin theory.
- **Relevance to GTOS:** *Reference text* for the project_distributional_findings ξ=0.35 fat-tail estimate. Directly anchors the SL-buffer-from-EVT calibration approach. Surprisingly under-cited in modern algo-trading literature.
- **Potential hypothesis:** EVT-implied 99.5% quantile of XAUUSD M15 absolute return (Hill-estimator-fitted) gives an SL-buffer that matches the realized 0.5% extreme-loss frequency more accurately than ATR×k for any constant k.
- **Cross-domain flag:** 03_distributional_characteristics; 21_risk_management_kelly_sizing

### Critical Market Crashes (Log-Periodic Power Laws)
- **Authors:** Didier Sornette
- **Year/Source:** 2003 / Physics Reports 378: 1-98 (Critical Market Crashes synthesis)
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S0370157302006348 ; https://arxiv.org/pdf/1704.02392 (review)
- **Abstract:** Synthesis of the log-periodic power law (LPPL / JLS) framework for predicting market crashes as critical phenomena. Empirical claim: crashes are preceded by a faster-than-exponential price ramp with log-periodic oscillations.
- **Key findings:**
  - LPPL precursor patterns appear in essentially all major crashes since 1929.
  - Discrete scale invariance from collective imitation of traders gives oscillatory pre-crash signature.
  - Critical-time-prediction has out-of-sample reliability problems but the framework's diagnostic value is empirical.
  - Connects econophysics critical-phenomena theory to finance.
- **Relevance to GTOS:** Contrarian and under-cited in mainstream quant; the LPPL pattern is exactly the kind of regime-shift signal the F15 regime-classifier-roadmap could attempt to detect via signature features. Practitioner caveat: out-of-sample prediction is unreliable, but diagnostic / regime-flag use is empirically robust.
- **Potential hypothesis:** Adding an LPPL-diagnostic feature (Sornette-style logoscillation residual) to the K54 ML feature set lifts H2-2026 holdout AUC by ≥0.005, with the largest contribution on crash-preceding cells.
- **Cross-domain flag:** 05_change_point_regime_switching

### Order Flow, Transaction Clock, and Normality of Asset Returns
- **Authors:** Thierry Ané, Hélyette Geman
- **Year/Source:** 2000 / Journal of Finance 55(5): 2259-2284
- **URL:** http://www.finance.martinsewell.com/stylized-facts/distribution/AneGeman2000.pdf
- **Abstract:** Empirical extension of Clark (1973): when returns are evaluated in transaction-count time (rather than calendar time), they recover near-Gaussianity. Cumulative trade count is a better operational clock than volume.
- **Key findings:**
  - Transaction-count-time returns are nearly Gaussian (kurtosis ≈ 3) on equity data.
  - Trade count beats volume as the operational clock.
  - The clock can be modelled non-parametrically; both clock and price are jump diffusions.
  - Validates the Clark mixture-of-distributions hypothesis with stronger empirical fit.
- **Relevance to GTOS:** *Critical* for the tick-capture daemon. If transaction-count time achieves Gaussianity, then GTOS's M15-bar-based gating is implicitly fighting the operational clock — moving to trade-count bars (or trade-count-weighted M15 features) could materially improve signal-to-noise.
- **Potential hypothesis:** Replacing M15-time triggers with M15-equivalent-trade-count triggers (defined per instrument from the 2026 baseline) increases the OB-WR by ≥3pp on the H2-2026 holdout, controlled for total trade frequency.
- **Cross-domain flag:** 06_market_microstructure_orderbook

### The Variation of Certain Speculative Prices (1963 Mandelbrot)
- **Authors:** Benoit B. Mandelbrot
- **Year/Source:** 1963 / Journal of Business 36(4): 394-419
- **URL:** https://web.williams.edu/Mathematics/sjmiller/public_html/341Fa09/econ/Mandelbroit_VariationCertainSpeculativePrices.pdf ; https://finance.martinsewell.com/stylized-facts/volatility/Mandelbrot1963.pdf
- **Abstract:** Original argument that cotton-price returns follow alpha-stable Pareto-Levy distributions (infinite variance) rather than Gaussians. Motivates a heavy-tailed alternative to the random walk.
- **Key findings:**
  - Cotton-price returns fit alpha-stable distributions with α ≈ 1.7, not Gaussian.
  - Infinite-variance models imply unbounded VaR — finance must accommodate fat tails.
  - Random-walk hypothesis with Gaussian innovations is empirically refuted.
- **Relevance to GTOS:** Founding empirical paper on fat-tailed financial returns. Cross-references project_distributional_findings (ξ=0.35 implies infinite kurtosis, finite variance). The 1963 alpha-stable claim is now refined to *finite* variance with heavy tails — but the finite-variance refinement (Clark 1973, Mandelbrot 1997 multifractal) does not invalidate the original tail-existence claim.
- **Potential hypothesis:** —
- **Cross-domain flag:** 03_distributional_characteristics

### Backward Stochastic Differential Equations (Bismut Origin)
- **Authors:** Jean-Michel Bismut
- **Year/Source:** 1973 / Memoirs of the AMS 176 (Théorie Probabiliste du Contrôle des Diffusions)
- **URL:** https://www.ams.org/journals/memo/1976-04-167/ (related; check institutional access)
- **Abstract:** Origin of backward SDEs as adjoint equations in the stochastic-Pontryagin maximum principle. Establishes the linear-BSDE existence/uniqueness theory by direct probabilistic methods.
- **Key findings:**
  - Adjoint process = solution of a backward SDE.
  - Stochastic Pontryagin maximum principle gives optimality conditions for stochastic-control problems.
  - Foundational tools (Girsanov in particular) for the dual / adjoint approach.
- **Relevance to GTOS:** Historical anchor; under-cited in ML-finance work because most applied papers use the El Karoui-Peng-Quenez (1997) restatement. Knowing the original is useful for any GTOS researcher who reads the dual / shadow-price literature.
- **Potential hypothesis:** —
- **Cross-domain flag:** none

---

## Section 6 — Top 10 most-relevant-to-GTOS

Ranked by directly-actionable hypothesis-density and proximity to current GTOS subsystems / open research questions.

| # | Title | Authors | Year | Why top-10 for GTOS |
|---|-------|---------|------|---------------------|
| 1 | Volatility is Rough | Gatheral, Jaisson, Rosenbaum | 2018 | Directly invalidates classical SV-based session-vol models (H25); rough-fBM with H≈0.1 is the right null for GTOS kill-zone selection. Connects to F15 regime-conditioned decay finding. |
| 2 | A Subordinated Stochastic Process Model with Finite Variance for Speculative Prices (Clark 1973) + Order Flow / Transaction Clock (Ané-Geman 2000) | Clark / Ané-Geman | 1973 / 2000 | Gives the trading-time vs physical-time framework that justifies the tick-capture daemon and predicts the (currently NULL) microstructure-feature payoff is conditional on tick-density regimes — testable against E24/E26 archive memory. |
| 3 | Signature Methods in Stochastic Portfolio Theory | Cuchiero, Möller | 2024 | The most-recent operationalization of signatures for portfolio sizing; immediate K54 / S79 follow-up candidate. Pareto-dominance hypothesis directly testable. |
| 4 | The Fine Structure of Asset Returns (CGMY) | Carr, Geman, Madan, Yor | 2002 | If GTOS instruments are pure-jump, SL-buffer calibration under Brownian null is mis-specified. Directly testable via CGMY recalibration; bridges ξ=0.35 fat-tail finding. |
| 5 | A Jump-Diffusion Model for Option Pricing (Kou Double-Exponential) | Kou | 2002 | Provides closed-form first-passage probabilities under a jump null — *exactly* what's needed for principled SL-buffer design. Directly cross-references the Bachelier first-passage anchor. |
| 6 | Hawkes Processes in Finance | Bacry, Mastromatteo, Muzy | 2015 | Theoretical foundation for the cross-instrument correlation gate redesign and for the `tick_features.py` time-arrival features. The static |corr| ≥ 0.4 gate is a coarse proxy for what the Hawkes framework formalizes. |
| 7 | Continuous Auctions and Insider Trading (Kyle) | Kyle | 1985 | Gives the formal mechanism for the OB-zone edge: stop-cascade equilibrium is a Kyle-λ phenomenon. Directly bridges to F11 OB-zone-decay-velocity finding. |
| 8 | Drawdown: From Practice to Theory and Back Again | Goldberg, Mahmoud (incl. Pospisil-Vecer) | 2017 | Closed-form expected-max-drawdown gives the principled trigger for H29 8% DD position-reduction. Vol-conditioning of the trigger is the immediate FN-compliance follow-up. |
| 9 | Modelling Extremal Events for Insurance and Finance | Embrechts, Klüppelberg, Mikosch | 1997 | The reference text for EVT-based SL-buffer calibration. Directly anchors the project_distributional_findings memory. |
| 10 | Solving High-Dimensional PDEs Using Deep Learning (Deep BSDE) | Han, Jentzen, E | 2018 | Methodological enabler for any GTOS Phase-3 dynamic-programming-based optimal-stop / sizing problem. Deep-BSDE-trained value function is the principled supervisor for K54 / J46-J49 successor. |

---

## Section 7 — Cross-domain handoffs

Counted: **24 cross-domain handoffs** flagged across this domain's 42 papers.

| Target domain | Count | Top candidates (by relevance to that domain) |
|---------------|-------|----------------------------------------------|
| 03_distributional_characteristics | 9 | Cont 2001 stylized-facts (already primary owner there); CGMY (Carr-Geman-Madan-Yor 2002); Eberlein-Keller 1995 hyperbolic; Madan-Carr-Chang 1998 VG; Sato 1999 Levy textbook; Cont-Tankov 2004 jump-processes textbook; Embrechts-Kluppelberg-Mikosch 1997 EVT; Mandelbrot 1963; Engle 1982 ARCH / Bollerslev 1986 GARCH |
| 06_market_microstructure_orderbook | 6 | Kyle 1985 (theory anchor stays here, application to 06); Cont-de Larrard 2013 LOB diffusion limit; Avellaneda-Stoikov 2008; Almgren-Chriss 2001; Donier-Bonart-Mastromatteo-Bouchaud 2015; Hawkes (Bacry-Mastromatteo-Muzy 2015) |
| 19_ai_ml_for_finance_classical_deep_sequence | 5 | Lyons-McLeod 2022 signature methods; Chevyrev-Kormilitzin 2016 signature primer; Friz-Hairer 2020 rough-paths textbook; Lyons 1998 rough-path founding paper; Hambly-Lyons 2010 signature uniqueness; Han-Jentzen-E 2018 deep BSDE (primary methodological); Buehler et al. 2019 deep hedging |
| 16_volatility_derivatives_vol_regime | 4 | Bayer-Friz-Gatheral 2016 rough-vol pricing; Gatheral-Jaisson-Rosenbaum 2018 (theory anchor stays); El Euch-Rosenbaum 2019 rough Heston; Comte-Renault 1998 long-memory SV; Barndorff-Nielsen-Shephard 2001 OU-vol |
| 21_risk_management_kelly_sizing | 4 | Cuchiero-Möller 2024 signature portfolios; Karatzas-Shreve 1998 Methods of Mathematical Finance; Drawdown synthesis (Goldberg-Mahmoud 2017); Bouchaud-Mezard 2000 wealth condensation; El Karoui-Peng-Quenez 1997 BSDE |
| 13_cross_asset_correlation_factors | 2 | Engle 2002 DCC; Cont-Bouchaud 2000 herd behavior |
| 17_behavioral_adaptive_markets | 1 | Lux-Marchesi 1999 stochastic multi-agent model |
| 04_multitimeframe_fractal_wavelets | 2 | Mandelbrot-Calvet-Fisher 1997 multifractal asset returns; Mandelbrot-Wallis 1969 R/S robustness |
| 05_change_point_regime_switching | 1 | Sornette 2003 Critical Market Crashes (LPPL) |
| 20_rl_llms_in_trading | 1 | Buehler et al. 2019 deep hedging; Bäuerle-Rieder 2011 MDP textbook |
| 02_statistical_methodology | 1 | Glasserman 2003 Monte Carlo book |

(Note: papers are double-counted across rows where a paper meaningfully bridges two adjacent domains.)

---

## Final report

**Papers cataloged:** 42 (vs target 35-50; quality-bar exceeded).

**Top 3 most-relevant-to-GTOS:**

1. **Gatheral-Jaisson-Rosenbaum (2018) "Volatility is Rough"** — invalidates classical SV models for short horizons; H≈0.1 fBM is the right null for the H25 session-volatility shadow logger and for kill-zone selection.
2. **Carr-Geman-Madan-Yor (2002) "The Fine Structure of Asset Returns" + Kou (2002) double-exponential jump-diffusion** — combined, they give the principled jump-aware SL-buffer-multiplier calibration that the project_distributional_findings ξ=0.35 fat-tail observation demands; directly testable.
3. **Cuchiero-Möller (2024) "Signature Methods in Stochastic Portfolio Theory"** — most-recent operationalization of signatures for portfolio sizing; immediate K54 v2 / S79 sharpe-weighted follow-up candidate.

**Top 1 surprise (challenges / extends GTOS):**

The Ané-Geman (2000) finding that *transaction-count time* (not volume time, not wall-clock time) is the operational clock that recovers Gaussianity in returns directly *challenges* the GTOS architectural decision to use M15-wallclock candles as the trigger unit. If GTOS instruments share this property (likely, given Clark-1973 universality), then the M15-bar-based gating is implicitly fighting the operational clock — and the *current null result on tick microstructure features* (memory `project_microstructure_archived_2026-04-27`) may be a measurement artifact rather than a genuine signal absence. Concretely: switching M15 triggers to "200-trade-count bars" (or trade-count-weighted M15 features) is a candidate for a meaningful pp-level WR lift on the H2-2026 holdout. This re-opens the microstructure track.

**2-3 hypotheses for GTOS testing:**

1. **Jump-aware SL-buffer recalibration:** Recalibrating XAUUSD / NAS100 SL-buffer ATR-multiples under a CGMY null (Carr-Geman-Madan-Yor 2002) with parameters fitted from 2026 tick data shifts the optimal buffer by ≥0.2 ATR vs the current Brownian-implied calibration; back-tested R/trade improves ≥0.05 on H2-2026.
2. **Signature-feature K54 v2:** Replacing K54's engineered features with depth-3 truncated-signature features (Lyons-McLeod 2022 + Cuchiero-Möller 2024) over the last 10 H1 candles improves H2-2026 holdout AUC by ≥0.02, controlled for total feature dimension. Bridges to the K54 baseline AUC=0.571 finding.
3. **Trade-count-time trigger:** Switching from M15-wallclock triggers to instrument-specific 200-trade-count bars (Ané-Geman 2000 operational clock) lifts OB-WR by ≥3pp on the H2-2026 holdout, reopening the E24/E26-archived microstructure track.

**Cross-domain handoffs flagged:** 24 (some papers double-counted across adjacent domains). Top 2 destinations: **03_distributional_characteristics** (9 handoffs — Cont 2001, CGMY, Eberlein-Keller, Madan-Carr-Chang VG, Sato Levy textbook, Cont-Tankov, Embrechts EVT, Mandelbrot 1963, ARCH/GARCH) and **06_market_microstructure_orderbook** (6 handoffs — Kyle 1985 theory + applications via Cont-de Larrard 2013, Avellaneda-Stoikov 2008, Almgren-Chriss 2001, Donier et al. 2015, Hawkes via Bacry-Mastromatteo-Muzy 2015).
