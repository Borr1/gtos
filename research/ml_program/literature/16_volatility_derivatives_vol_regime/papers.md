# Domain 16 — Volatility Trading, Derivatives, Vol Regime

**Worker:** Phase 1 Literature Research Agent #16
**Status:** Complete
**Compiled:** 2026-04-28
**Paper count:** 50 (target 35-50)
**Encoding:** UTF-8

---

## 1. Domain summary

This domain catalogs the literature on volatility as a tradable / forecastable asset and on derivative pricing as it interacts with cash-market dynamics. The core research families covered:

- **Foundational option-pricing models** (Black-Scholes-Merton, Heston, SABR, Dupire local volatility)
- **Jump-diffusion** (Merton 1976, Kou 2002, Bates 1996/2000, Pan 2002)
- **Stochastic volatility extensions** (Heston-Nandi GARCH options, Bakshi-Cao-Chen, Christoffersen-Heston-Jacobs multifactor)
- **Rough volatility** (Gatheral-Jaisson-Rosenbaum, Bayer-Friz-Gatheral, El Euch-Rosenbaum, Bergomi rBergomi, microstructural foundations)
- **Realized volatility, HAR, range estimators** (Andersen-Bollerslev-Diebold-Labys, Corsi HAR, Garman-Klass, Parkinson, Yang-Zhang, Andersen-Bollerslev-Diebold "Roughing It Up")
- **Volatility risk premium / VIX** (Carr-Wu, Bollerslev-Tauchen-Zhou, Drechsler-Yaron, Bekaert-Hoerova, Whaley, Bollerslev-Todorov tails)
- **Implied vs realized + skew** (Britten-Jones-Neuberger, Christensen-Prabhala, Bakshi-Kapadia-Madan, Demeterfi-Derman-Kamal-Zou variance swaps)
- **GARCH families with option-pricing implication** (Engle 1982, Bollerslev 1986, Nelson 1991 EGARCH, GJR-GARCH, Hansen-Lunde, Heston-Nandi)
- **Microstructure noise, leverage effect, Carr-Madan FFT** (Bandi-Russell, Black 1976, Schwert 1989, El Euch-Rosenbaum-Fukasawa microstructure, Andersen-Bollerslev 1998)
- **0DTE options + 2020-2025 frontier** (Dim-Eraker-Vilkov, Adams-Fontaine-Ornthanalai, Vasquez et al, Vilkov 0DTE rules)
- **Path-dependent volatility** (Guyon-Lekeufack 2023, deep-learning calibration)
- **FX & commodity volatility** (Carr-Wu stochastic skew, Bates 1996 Deutsche Mark, Lipton 2002 FX smile, gold/oil VRP)
- **Macro announcement / event vol** (Andersen-Bollerslev-Diebold-Vega 2003, jump activity around news)

The literature is mature, with strong empirical consensus on vol clustering, leverage effect, and the existence of a negative variance risk premium. Open questions remain on (i) correct functional form for short-dated skew (rough-vol vs path-dependent), (ii) state-dependence of the variance risk premium (Drechsler-Yaron vs more recent regime-switching evidence), and (iii) whether 0DTE flows have added a new dealer-gamma feedback loop to S&P realized vol.

## 2. GTOS subsystem connections (the "why this matters")

| GTOS subsystem | Cross-link |
|---|---|
| `risk.sl_buffer_atr_multiplier` (ATR-based SL buffer) | The implicit volatility model is GARCH-of-ATR. Heston/SABR/rough-vol literature offers calibrated alternatives during regime shifts. Garman-Klass / Parkinson / Yang-Zhang range estimators offer cheaper-than-realized-vol alternatives for tick-light symbols. |
| K54 v2 lag-1 squared-return autocorrelation feature | Direct GARCH/HAR ancestor — see Engle 1982, Bollerslev 1986, Corsi 2009 HAR, Andersen et al. realized vol. F15 says regime is load-bearing — HMM regime literature (vol clustering) is the right substrate. |
| H29 drawdown position reduction (8% trigger) | Volatility-clustering literature (Engle Nobel lecture, Schwert 1989) supports vol-aware sizing. Yang-Zhang, ABDL realized vol → forecasts drawdown probability. |
| Heartbeat-flatten kill switch (catastrophe protection) | Bollerslev-Todorov "Tails, Fears, Risk Premia" + Pan 2002 + Bates 2000 directly inform threshold-setting for jump-tail catastrophe events. |
| F15 regime is load-bearing decay axis | Vol-regime detection literature (HMM, change-point), variance risk premium regime-switching (Bekaert-Hoerova) — direct hypothesis lift for K54 regime-aware classifier. |
| A4 trending_bull replay (XAUUSD H2 LONG selectivity collapse) | Rough-vol fast mean-reversion of vol-of-vol (rBergomi, El Euch-Rosenbaum) explains regime breakdowns where calm precedes regime flip. Path-dependent vol (Guyon-Lekeufack 2023) suggests "memory" of past vol drives current selectivity. |
| NFP / FOMC event windowing (kill-zone gates) | Andersen-Bollerslev-Diebold-Vega 2003 + Andersen et al. "Roughing It Up" jump-decomposition directly inform event-window logic. |
| Cross-instrument correlation gate (DCC-style) | Engle 2002 DCC GARCH (cross-link to domain 13) is the canonical multivariate-vol substrate. |
| Tick-feature engineering (microstructure) | Microstructural foundations of rough vol (El Euch-Rosenbaum 2018) suggests Hawkes-process-style intensity features. |

## 3. Critical takeaways for K54 and Phase 2

1. **Volatility is rough; ATR-based heuristics are first-order wrong.** Hurst H≈0.1 means vol moves are anti-persistent at high frequency. ATR exponential moving-average underestimates short-term vol of vol. Rough-Bergomi or path-dependent vol (Guyon-Lekeufack 2023) would be a meaningful upgrade.

2. **A negative variance risk premium is one of the most robust findings.** Carr-Wu 2009, Bollerslev-Tauchen-Zhou 2009, Drechsler-Yaron 2011, Bollerslev-Todorov 2011 all confirm. For GTOS this implies: implied vol > realized vol on average; selling vol earns premium; vol-buying tail-hedges are expensive. Relevance to GTOS is indirect (we are not vol-traders), but strong: when VIX is high, selling-side carry strategies beat trend-following, and our edge mechanism (OB stop-cascade reversion) should be stratified by VRP regime.

3. **0DTE may have changed equity-index intraday vol dynamics post-2022.** Dim-Eraker-Vilkov 2023, Adams et al. 2024 — the literature is split but converging on "0DTE attenuates rather than amplifies on average, but creates very-short-window vol spikes." For US30/NAS100, this is highly relevant; existing kill-zone schedule may need modification post-OPEX.

4. **HAR + Lasso outperforms more complex ML in many panels** (Audrino-Knaus 2016, Hansen-Lunde 2005 "does anything beat GARCH(1,1)?"). Phase 2 should hold a parsimonious HAR baseline against any deep-learning K54 v3.

5. **Regime-conditional VRP** (Bekaert-Hoerova 2014, Bardgett-Gourier-Leippold 2019). The variance premium has high-vol vs low-vol regimes; predictive power is highly state-dependent. For F15 regime-conditioned decay this is a direct analog.

## 4. Methodology / search log

- WebSearch + WebFetch on Google Scholar / arXiv / SSRN / NBER / journal repositories.
- All URLs verified by following at least one search result; no fabricated citations.
- 9 foundational papers from spec §3 (Black-Scholes 1973, Heston 1993, SABR Hagan 2002, Volatility is Rough Gatheral 2018, Engle-Patton 2001, Engle 2004 Nobel, ABDL 2003, Carr-Wu 2009 VRP, Bakshi-Cao-Chen 1997).
- Filled out: GARCH families (Engle 1982, Bollerslev 1986, GJR, EGARCH, Heston-Nandi), realized vol (Corsi HAR, range estimators, ABDL), variance risk premium, jump-diffusion (Merton, Kou, Bates, Pan), rough volatility track (rBergomi, microstructural foundations, El Euch-Rosenbaum, deep-calibration), 0DTE (5 recent papers), implied-vs-realized, skew/kurtosis (BKM), FX vol, macroeconomic event vol, and recent ML for vol.
- Known gap: Indian / Chinese / emerging-market vol literature minimal coverage; deemed not load-bearing for GTOS (XAUUSD, US30, GBPJPY, USDJPY, GBPUSD, XAGUSD, NAS100 all major-market instruments).

## 5. Cross-domain handoffs

| Paper / topic | Cross-link to domain |
|---|---|
| Engle 1982, Bollerslev 1986, EGARCH, GJR, Hansen-Lunde 2005 | 03 (descriptive distributional fit) — we keep option-pricing-implication side |
| Andersen-Bollerslev-Diebold-Labys 2003, Corsi HAR, Garman-Klass, Parkinson, Yang-Zhang | 04 (multifractal / wavelets / Hurst long-memory) — we keep tradable-vol side |
| Engle 2002 DCC | 13 (cross-asset correlation factors) |
| Andersen-Bollerslev 1998 (Deutschemark intraday) | 06 (microstructure) |
| Bandi-Russell 2008 microstructure noise | 06 |
| HMM vol-regime detection | 05 (change-point regime switching) — we cite trading-implication side |
| Drechsler-Yaron, Bollerslev-Todorov tail risk premia | 03 (descriptive) + 21 (sizing under tail risk) |
| Burnside-Eichenbaum-Rebelo carry / FX vol | 11 (FX content) |
| Microstructural foundations of rough vol | 06 |
| Andersen-Bollerslev-Diebold-Vega macro announcements | 11 (FX), 12 (equity) |
| Guyon-Lekeufack PDV | hybrid: keep here for trading implication; cross-link 04 long-memory |
| 0DTE (Dim-Eraker-Vilkov, Adams et al.) | 12 (equity-index gamma) |

## 6. Gaps and caveats

- **Gold-specific vol literature thin.** GARCH-MIDAS gold paper exists but no major Heston-style stochastic-vol calibration paper for XAUUSD options. Cross-link to domain 10 (gold/commodities).
- **FX 0DTE literature absent.** All 0DTE work is S&P 500 index. For GBPJPY/USDJPY/GBPUSD this is uncovered terrain.
- **Tick-data microstructure overlap with domain 06.** Some included here as foundations of rough vol; the trading-rule side stays in 06.
- **Most VRP papers are S&P 500.** Commodity / FX VRP coverage is thinner; one paper (Prokopczuk et al. variance risk premia in commodity markets) included to bridge.
- **No paper directly validates GTOS-style "OB precision after stop-cascade" thesis** — the closest analog is Bollerslev-Todorov 2011 "Tails, Fears, Risk Premia" describing fear-driven jumps; the stop-cascade reversion mechanism is GTOS's empirical claim, not a published mechanism.

---

## 7. Papers

### 1. The Pricing of Options and Corporate Liabilities

- **Authors:** Fischer Black, Myron Scholes
- **Year:** 1973
- **Source:** Journal of Political Economy 81(3): 637-654
- **URL:** https://www.cs.princeton.edu/courses/archive/fall09/cos323/papers/black_scholes73.pdf
- **Model type:** Black-Scholes (geometric Brownian motion, constant vol)
- **Abstract:** First successful options pricing formula. Derives the no-arbitrage value of a European call option under geometric Brownian motion of the underlying with constant volatility, riskless rate, and continuous trading. Launches the field of financial engineering.
- **Key findings:**
  - Option price depends on five inputs: spot, strike, time-to-expiry, riskless rate, volatility (constant)
  - Hedge portfolio (delta hedge) eliminates risk locally; valuation by replication
  - Implies single "Black-Scholes implied volatility" for any option, providing a benchmark even where the model fails
- **Relevance to GTOS:** Foundational reference; defines the constant-volatility null model that GARCH/Heston/rough-vol all reject. Implies the implicit-vol assumption baked into GTOS's ATR-based SL buffer multipliers (`risk.sl_buffer_atr_multiplier`) — i.e., the system assumes Brownian-motion-like vol over the 1-2 hour holding window, which fat-tail empirical evidence (memory: project_distributional_findings ξ=0.35) directly contradicts.
- **Potential hypothesis:** None directly tradable; serves as null model.
- **Cross-domain links:** 03 (distributional null)

### 2. A Closed-Form Solution for Options with Stochastic Volatility with Applications to Bond and Currency Options

- **Authors:** Steven L. Heston
- **Year:** 1993
- **Source:** Review of Financial Studies 6(2): 327-343
- **URL:** https://www.ma.imperial.ac.uk/~ajacquie/IC_Num_Methods/IC_Num_Methods_Docs/Literature/Heston.pdf
- **Model type:** Heston-stochastic
- **Abstract:** Closed-form European option pricing under square-root stochastic volatility (CIR process for variance) using characteristic-function methods. Allows arbitrary correlation between volatility and asset returns and stochastic interest rates with applications to bond and currency options.
- **Key findings:**
  - Variance follows CIR / square-root process: dv = κ(θ-v)dt + σ√v dW
  - Negative correlation between vol and price reproduces the equity volatility skew
  - Characteristic function admits FFT-friendly numerical inversion
  - Five parameters: long-run vol θ, mean-reversion κ, vol of vol σ, correlation ρ, initial vol v_0
- **Relevance to GTOS:** The canonical stochastic-vol benchmark. For XAUUSD, FX pairs, US30 — Heston with negative correlation is the simplest model that captures both vol clustering AND leverage effect. Direct calibration target if GTOS adds option-data ingestion. Even without options, Heston-implied ATR dynamics give principled vol-of-vol forecasts for sizing (H29 DD reduction).
- **Potential hypothesis:** Heston-calibrated v_t (filtered from realized vol + asymmetric M15 returns) is a stronger K54 vol feature than ATR-of-ATR.
- **Cross-domain links:** 03, 11

### 3. Managing Smile Risk

- **Authors:** Patrick S. Hagan, Deep Kumar, Andrew S. Lesniewski, Diana E. Woodward
- **Year:** 2002
- **Source:** Wilmott Magazine, September 2002, 84-108
- **URL:** https://www.next-finance.net/IMG/pdf/pdf_SABR.pdf
- **Model type:** SABR (stochastic alpha, beta, rho — stochastic local-vol)
- **Abstract:** Identifies that local-vol smile dynamics move opposite to observed market behavior, leading to unstable Black-Scholes-derived hedges. Develops the SABR model — stochastic vol with correlated forward — and uses singular perturbation to derive closed-form algebraic implied-vol formula.
- **Key findings:**
  - SABR has 4 parameters: α (initial vol), β (CEV exponent), ρ (correlation), ν (vol of vol)
  - Closed-form approximation for implied vol as function of forward and strike
  - When β=1: lognormal SABR; β=0: normal SABR
  - Becomes industry standard for swaption/IR-options markets
- **Relevance to GTOS:** SABR formula gives a fast smile interpolation across strikes. For instruments where GTOS could ingest options data (USDJPY, GBPUSD, XAUUSD all liquid), SABR-implied skew is a candidate K54 feature for direction prediction (skew = market's expected jump asymmetry).
- **Potential hypothesis:** Risk-reversal (25-delta call IV − 25-delta put IV) is a K54 directional feature.
- **Cross-domain links:** 11 (FX skew)

### 4. Volatility is Rough

- **Authors:** Jim Gatheral, Thibault Jaisson, Mathieu Rosenbaum
- **Year:** 2018 (arXiv 2014)
- **Source:** Quantitative Finance 18(6): 933-949
- **URL:** https://arxiv.org/abs/1410.3394
- **Model type:** Rough Fractional Stochastic Volatility (RFSV) — H<1/2
- **Abstract:** Empirically demonstrates log-volatility behaves as fractional Brownian motion with Hurst exponent H≈0.1, at any reasonable timescale. Proposes the Rough FSV (RFSV) model, providing a microstructural justification via high-frequency endogeneity and order splitting.
- **Key findings:**
  - H≈0.07-0.14 across 21 indices and asset classes (incredible cross-asset robustness)
  - Standard SV models (Heston etc.) need H=0.5; market is much rougher
  - RFSV reproduces both stylized facts (vol clustering, leverage) AND short-term smile steepness
  - Forecasting RFSV outperforms HAR-RV out-of-sample
- **Relevance to GTOS:** Major framing shift. Vol is anti-persistent at high frequency, meaning ATR-EMA based risk gates (which assume mean-reversion timescale ~hours) systematically underestimate vol-of-vol on M15 → H1. Implies that within an M15 candle, vol can swing more than ATR(14) suggests.
- **Potential hypothesis:** Replace ATR-based SL buffer with rough-Heston-implied vol forecast (H≈0.1 fractional kernel applied to last N M15 squared returns). H29 drawdown threshold should also be informed by rough-vol scaling.
- **Cross-domain links:** 03 (long-memory; rejected for log-vol), 04 (fractal), 06 (microstructural origin)

### 5. What Good is a Volatility Model?

- **Authors:** Robert F. Engle, Andrew J. Patton
- **Year:** 2001
- **Source:** Quantitative Finance 1(2): 237-245
- **URL:** https://web-static.stern.nyu.edu/rengle/EnglePattonQF.pdf
- **Model type:** GARCH (review / methodological)
- **Abstract:** A volatility model must forecast volatility. Reviews stylized facts about volatility (persistence, mean-reversion, asymmetry, exogenous predictors) and outlines the requirements a useful model must meet, illustrated on the Dow Jones Industrial Index.
- **Key findings:**
  - Vol persistence: half-life of shocks ~weeks for daily; days for intraday
  - Asymmetry / leverage effect: negative shocks raise vol more than positive shocks
  - Mean reversion: long-run vol exists; recent vol pulls toward it
  - Pre-determined exogenous variables (volume, news) help
  - Forecast horizon matters: intraday vs daily vs monthly need different specifications
- **Relevance to GTOS:** Direct checklist for any K54 vol feature: does it embed persistence + leverage + mean-reversion + exogenous predictors? Lag-1 squared-return AR has only persistence. K54 v3 should add leverage + mean-reversion explicit terms.
- **Potential hypothesis:** Add EGARCH-style sign-asymmetric squared-return feature: `sign(r_{t-1}) * r_{t-1}^2`. May materially help XAUUSD LONG-side decay (F2/F15).
- **Cross-domain links:** 03

### 6. Risk and Volatility: Econometric Models and Financial Practice (Nobel Lecture)

- **Authors:** Robert F. Engle
- **Year:** 2004
- **Source:** American Economic Review 94(3): 405-420
- **URL:** https://www.aeaweb.org/articles?id=10.1257/0002828041464597
- **Model type:** GARCH (overview)
- **Abstract:** Engle's Nobel lecture surveying the development of ARCH/GARCH and its application to risk management. Discusses why time-varying volatility is critical to value-at-risk, derivative pricing, and asset allocation.
- **Key findings:**
  - GARCH(1,1) captures most of the persistence in equity-vol time series
  - Risk premia depend on conditional volatility (GARCH-in-mean)
  - Multivariate vol (DCC) is the natural extension
  - Long-memory volatility: components-GARCH or FIGARCH for ultra-low-frequency persistence
- **Relevance to GTOS:** Methodologically definitive. Reinforces that GARCH-of-returns is the right baseline; rough-vol and HAR are refinements not replacements.
- **Potential hypothesis:** GARCH(1,1) of M15 squared returns is a stronger K54 baseline than lag-1 squared-return autocorrelation.
- **Cross-domain links:** 03

### 7. Modeling and Forecasting Realized Volatility

- **Authors:** Torben G. Andersen, Tim Bollerslev, Francis X. Diebold, Paul Labys
- **Year:** 2003
- **Source:** Econometrica 71(2): 579-625
- **URL:** https://onlinelibrary.wiley.com/doi/abs/10.1111/1468-0262.00418
- **Model type:** Realized volatility (model-free)
- **Abstract:** Develops the framework for using high-frequency intraday returns to construct daily realized volatility. Shows that simple long-memory Gaussian VAR over log-realized-vol forecasts well, and combined with lognormal-normal mixture, gives well-calibrated density forecasts.
- **Key findings:**
  - Realized variance = sum of squared intraday returns; consistent for integrated variance
  - Log-realized-vol is approximately Gaussian (much more so than vol itself)
  - Long memory in vol (d≈0.4 in fractional integration) is highly robust
  - 5-minute sampling: optimal trade-off between noise and continuous-time approximation
- **Relevance to GTOS:** GTOS's tick-capture daemon builds the substrate for proper realized-vol features. Using log-realized-vol (rather than ATR) as a K54 input is a direct upgrade — Gaussian-distributed log-RV plays well with linear / tree models.
- **Potential hypothesis:** Replace `atr_14` with `log_realized_vol_M15` (sum of M1 squared returns) as a K54 feature. Expected lift from better-distributed input alone.
- **Cross-domain links:** 04 (long memory), 06 (microstructure-noise correction)

### 8. Variance Risk Premiums

- **Authors:** Peter Carr, Liuren Wu
- **Year:** 2009
- **Source:** Review of Financial Studies 22(3): 1311-1341
- **URL:** https://engineering.nyu.edu/sites/default/files/2019-01/CarrReviewofFinStudiesMarch2009-a.pdf
- **Model type:** Model-free variance swap
- **Abstract:** Quantifies the variance risk premium directly: VRP = realized variance − synthetic-variance-swap rate (built from option strip). Documents large negative VRP across S&P 500 and individual stocks; common stochastic variance risk factor commands negative risk premium.
- **Key findings:**
  - VRP is consistently negative for equity indices (mean ~-2% per month annualized)
  - VRP varies in cross-section: high-beta-to-aggregate-vol stocks have more negative VRP
  - Variance-swap rate dominates ATM Black-Scholes IV as a measure of risk-neutral expected vol
  - Model-free: no parametric SV / jump model required
- **Relevance to GTOS:** VIX itself is a model-free variance-swap rate. VIX − HAR-RV-forecast = VRP estimate; this is a direct candidate K54 feature for US30 and NAS100. For XAUUSD: GVZ is the analog; for USDJPY: JYVIX. VRP regime conditions edge: when |VRP| is high, risk-on / risk-off transitions are imminent.
- **Potential hypothesis:** VRP at trade-open is predictive of subsequent realized R. K54 should include VIX-implied-vol minus HAR-realized-vol as a regime indicator for US30/NAS100 trades.
- **Cross-domain links:** 03 (descriptive vol), 21 (risk premium for sizing)

### 9. Empirical Performance of Alternative Option Pricing Models

- **Authors:** Gurdip Bakshi, Charles Cao, Zhiwu Chen
- **Year:** 1997
- **Source:** Journal of Finance 52(5): 2003-2049
- **URL:** https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.1997.tb02749.x
- **Model type:** Heston-stochastic + jumps + stochastic interest rates
- **Abstract:** Compares alternative option pricing models nesting stochastic vol, stochastic interest rates, and jumps. Evaluates internal consistency (parameter stability), out-of-sample pricing, and hedging on S&P 500 options.
- **Key findings:**
  - Adding stochastic vol substantially improves pricing accuracy
  - Adding jumps improves short-term option pricing further (especially OTM puts)
  - For hedging, stochastic vol alone is best — adding jumps degrades hedge ratios
  - Stochastic interest rates: marginal at best for short-dated equity options
- **Relevance to GTOS:** When designing volatility-aware risk gates, the right model depends on use case. For short-horizon position sizing (1-2h holding period): stochastic vol matters most. Jumps matter for catastrophe protection (heartbeat-flatten). Don't conflate.
- **Potential hypothesis:** Heartbeat-flatten threshold should be calibrated to jump-frequency tail (Bates 2000, Pan 2002) not vol-of-vol.
- **Cross-domain links:** 03

### 10. Rough Volatility (book) and Pricing under Rough Volatility

- **Authors:** Christian Bayer, Peter Friz, Jim Gatheral (and book editors Fukasawa, Jacquier, Rosenbaum)
- **Year:** 2016 (paper); 2023 (SIAM book)
- **Source:** Quantitative Finance 16(6): 887-904 (paper); SIAM book Rough Volatility
- **URL:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2554754
- **Model type:** Rough-Bergomi (rBergomi) — three parameter rough stochastic vol
- **Abstract:** Builds on Gatheral-Jaisson-Rosenbaum 2014/2018 to derive the rough Bergomi model — a 3-parameter (H, η, ρ) forward-variance model. Demonstrates rBergomi fits SPX vol surface markedly better than conventional Markovian SV with fewer parameters; consistent with variance-swap curves around 2008 and Flash Crash.
- **Key findings:**
  - rBergomi = 3 parameters; nests Black-Scholes when H→0.5, η→0
  - Captures short-maturity skew steepness that Heston cannot
  - Forward-variance curve extracted from option prices encodes the past-volatility history
  - VIX futures pricing: rBergomi consistent with empirical term structure
- **Relevance to GTOS:** Complementary to paper #4. Provides the calibration recipe; the canonical reference if Phase 2 builds option-aware features for K54.
- **Potential hypothesis:** rBergomi-implied vol forecast (H≈0.1, calibrated weekly per instrument) is a stronger K54 feature than ATR.
- **Cross-domain links:** 04

### 11. The Heston Model and the Microstructural Foundations of Leverage Effect and Rough Volatility (El Euch-Rosenbaum mechanism)

- **Authors:** Omar El Euch, Mathieu Rosenbaum (with Hawkes-process foundations from Jaisson, Bacry, et al.)
- **Year:** 2018-2019
- **Source:** Mathematical Finance 29(1): 3-38 ("The characteristic function of rough Heston models"); Finance & Stochastics 22(2): 241-280 ("The microstructural foundations of leverage effect and rough volatility")
- **URL:** https://arxiv.org/abs/1609.02108 ; https://arxiv.org/abs/1609.05177
- **Model type:** Rough Heston / Hawkes-process foundations
- **Abstract:** Derives the characteristic function of the rough Heston model via fractional Riccati equation, enabling efficient option pricing. Companion paper shows rough vol + leverage effect emerge naturally from a microscopic Hawkes-process model encoding endogenous order flow + asymmetric metaorder execution.
- **Key findings:**
  - Rough Heston: Riccati becomes fractional; no closed form but efficient numerics
  - Microscopic origin: Hawkes processes with metaorder asymmetry → both rough vol AND leverage emerge as scaling limits
  - Empirical degree of endogeneity ~95% for major markets; matches data
  - Provides theoretical basis for H≈0.1 (not arbitrary fitted value)
- **Relevance to GTOS:** Cements that rough vol is real, not statistical artifact. The Hawkes-process foundation suggests microstructure features (order-flow imbalance, trade-arrival rate) drive vol in a structured way — directly relevant to GTOS's tick daemon (vision Layer 1).
- **Potential hypothesis:** Hawkes-process trade-arrival intensity λ_t (estimable from M1 trades) is a stronger contemporaneous-vol proxy than realized variance.
- **Cross-domain links:** 06 (microstructure)

### 12. A Simple Approximate Long-Memory Model of Realized Volatility (HAR-RV)

- **Authors:** Fulvio Corsi
- **Year:** 2009
- **Source:** Journal of Financial Econometrics 7(2): 174-196
- **URL:** https://statmath.wu.ac.at/~hauser/LVs/FinEtricsQF/References/Corsi2009JFinEtrics_LMmodelRealizedVola.pdf
- **Model type:** HAR (heterogeneous autoregressive)
- **Abstract:** Proposes additive cascade of vol components defined over different horizons (daily, weekly, monthly). HAR-RV is a simple AR model in realized vol with three lags (1-day, 5-day, 22-day averages). Reproduces long-memory, fat tails, and self-similarity without true long-memory parameters.
- **Key findings:**
  - HAR(1,5,22) fits log-RV nearly as well as ARFIMA / fractionally-integrated models
  - Forecasting performance: best-in-class out-of-sample for daily RV
  - Three-parameter parsimony; trivial to estimate (OLS on log-RV)
  - Theoretical foundation: heterogeneous market hypothesis (different agents with different horizons)
- **Relevance to GTOS:** HAR is the workhorse of academic vol forecasting. For K54: HAR-RV(1, 4, 16) on M15 returns would be a powerful additional feature stack. Trivial cost; large empirical evidence base.
- **Potential hypothesis:** HAR-RV-projected vol over the next 4 candles is a strong predictor of trade outcome variance.
- **Cross-domain links:** 04 (long memory), 03 (descriptive vol)

### 13. Stock Return Characteristics, Skew Laws, and the Differential Pricing of Individual Equity Options (BKM)

- **Authors:** Gurdip Bakshi, Nikunj Kapadia, Dilip Madan
- **Year:** 2003
- **Source:** Review of Financial Studies 16(1): 101-143
- **URL:** https://people.umass.edu/nkapadia/docs/Bakshi_Kapadia_Madan_2003_RFS.pdf
- **Model type:** Model-free risk-neutral moments
- **Abstract:** Derives model-free formulas for risk-neutral skewness and kurtosis from option prices (the BKM estimators). Documents that individual-stock risk-neutral distributions are far less negatively skewed than the market index — relating differential pricing to differential skewness.
- **Key findings:**
  - BKM estimators: model-free formulas for risk-neutral skewness and kurtosis
  - Individual stocks: less negative skewness than index; risk premium for index puts
  - CBOE SKEW index built on BKM methodology
  - Skew laws: aggregate skew driven by systematic component (correlations)
- **Relevance to GTOS:** Risk-neutral skew is directional information embedded in option prices. For instruments with liquid skew (XAUUSD, US30, NAS100) skew can be a K54 feature for LONG/SHORT bias prediction. CBOE SKEW index is publicly available.
- **Potential hypothesis:** CBOE SKEW level / change is a regime indicator for US30 LONG/SHORT bias.
- **Cross-domain links:** 12 (equity-index options)

### 14. A Closed-Form GARCH Option Valuation Model (Heston-Nandi)

- **Authors:** Steven L. Heston, Saikat Nandi
- **Year:** 2000
- **Source:** Review of Financial Studies 13(3): 585-625
- **URL:** https://academic.oup.com/rfs/article-abstract/13/3/585/1576522
- **Model type:** GARCH-affine (closed-form)
- **Abstract:** First readily-computed option formula for a discrete-time random-volatility model. Variance follows affine GARCH(p,q) correlated with returns; single-lag version converges to Heston 1993 in continuous time.
- **Key findings:**
  - Closed-form option valuation (FFT-friendly characteristic function)
  - Out-of-sample S&P 500 valuation errors substantially below ad-hoc Black-Scholes
  - Captures correlation of vol with spot AND path-dependence in vol simultaneously
  - Bridges the GARCH (econometrics) and stochastic-vol (mathematical-finance) traditions
- **Relevance to GTOS:** For systems that already have GARCH on returns (or could), this gives an option-pricing-consistent vol forecast. K54 feature: HN-implied conditional variance.
- **Potential hypothesis:** Heston-Nandi conditional variance estimated on M15 returns is a strictly better feature than ATR, with the same input cost.
- **Cross-domain links:** 03

### 15. Deutsche Mark-Dollar Volatility: Intraday Activity Patterns, Macroeconomic Announcements, and Longer Run Dependencies

- **Authors:** Torben G. Andersen, Tim Bollerslev
- **Year:** 1998
- **Source:** Journal of Finance 53(1): 219-265
- **URL:** https://onlinelibrary.wiley.com/doi/abs/10.1111/0022-1082.85732
- **Model type:** Realized volatility (intraday FX)
- **Abstract:** Foundational paper on intraday FX volatility. Documents intraday seasonality (U-shape), macro-announcement effects, and long-memory persistence using 5-minute DM/USD returns.
- **Key findings:**
  - U-shape in intraday vol: peaks at London open, NY open, NY close
  - Macro announcements (US NFP, FOMC) cause sharp vol spikes lasting 30-60 minutes
  - Long memory (FIGARCH d≈0.4) survives intraday seasonality removal
  - Spikes have asymmetric persistence: news vol decays faster than baseline shocks
- **Relevance to GTOS:** Validates GTOS's kill-zone model (London + NY). Provides empirical basis for "skip first NY candle" type rules and identifies macro-announcement windows as 30-60 min vol-elevated zones. Also directly relevant to USDJPY/GBPUSD/GBPJPY.
- **Potential hypothesis:** Intraday-vol-seasonality-adjusted ATR is a better risk gate than raw ATR; macro-announcement window flag should be a K54 hard-feature (binary or distance-to-event).
- **Cross-domain links:** 06 (microstructure), 11 (FX)

### 16. More Than You Ever Wanted to Know About Volatility Swaps (variance swap replication)

- **Authors:** Kresimir Demeterfi, Emanuel Derman, Michael Kamal, Joseph Zou
- **Year:** 1999
- **Source:** Journal of Derivatives 6(4): 9-32 (also Goldman Sachs Quantitative Strategies note March 1999)
- **URL:** https://emanuelderman.com/wp-content/uploads/1999/02/gs-volatility_swaps.pdf
- **Model type:** Model-free variance swap replication
- **Abstract:** Practitioner-quality derivation of variance swap replication via static portfolio of vanilla options. Shows that under continuous price diffusion, a variance swap can be exactly replicated by inverse-strike-squared-weighted strip of OTM puts and calls.
- **Key findings:**
  - Variance swap rate = risk-neutral expected variance, replicable from option prices
  - 2003 VIX redesign uses this exact methodology (Britten-Jones-Neuberger formulation)
  - Volatility swaps (square-root payoff): no exact static replication; require dynamic hedging
  - Dispersion trade: long index vol, short basket of single-name vols (or vice versa)
- **Relevance to GTOS:** Variance swap rate (= VIX² in the S&P case) is the "true" risk-neutral vol expectation — better than ATM-implied vol. For K54, VIX (and squared) is the right transformation, not raw VIX level.
- **Potential hypothesis:** VIX² (variance) features more linearly into return-prediction models than VIX (vol).
- **Cross-domain links:** 12

### 17. Option Pricing When Underlying Stock Returns Are Discontinuous (Merton jump-diffusion)

- **Authors:** Robert C. Merton
- **Year:** 1976
- **Source:** Journal of Financial Economics 3(1-2): 125-144
- **URL:** https://dspace.mit.edu/handle/1721.1/1899
- **Model type:** Merton jump-diffusion (lognormal jumps)
- **Abstract:** Adds Poisson jump component to Black-Scholes with lognormal jump sizes. Derives semi-closed-form pricing as Poisson-weighted sum of Black-Scholes prices conditional on jump count.
- **Key findings:**
  - Two new parameters: jump intensity λ, jump size distribution (lognormal: mean μ_J, vol σ_J)
  - Markets become incomplete (no perfect hedge of jump risk)
  - Captures kurtosis and short-term smile that pure-diffusion models cannot
  - Risk-neutral jump intensity may differ from physical-measure intensity (jump-risk premium)
- **Relevance to GTOS:** Jump-diffusion is the canonical model for catastrophe events (NFP, FOMC, geopolitical news). Heartbeat-flatten kill switch protects against the jump component, not the diffusion component. Calibrated jump intensity → expected jumps per session → expected stop-out frequency on extreme news.
- **Potential hypothesis:** Merton-jump-implied tail probability is a better catastrophe-protection trigger than rolling 99th percentile of bar size.
- **Cross-domain links:** 03 (tails), 21 (catastrophe sizing)

### 18. A Jump-Diffusion Model for Option Pricing (Kou double-exponential)

- **Authors:** Steven G. Kou
- **Year:** 2002
- **Source:** Management Science 48(8): 1086-1101
- **URL:** http://www.columbia.edu/~sk75/MagSci02.pdf
- **Model type:** Kou double-exponential jump-diffusion
- **Abstract:** Replaces Merton's lognormal jumps with double-exponential distribution (asymmetric Laplace), enabling closed-form solutions for path-dependent options including American and barrier.
- **Key findings:**
  - Asymmetric jumps: separate parameters for up-jumps (η_u) and down-jumps (η_d)
  - Closed-form pricing for lookback, barrier, perpetual American options
  - Better empirical fit than Merton for index returns
  - Memoryless property of exponential jumps simplifies first-passage computations
- **Relevance to GTOS:** Asymmetric jump intensity directly maps to LONG-side vs SHORT-side selectivity collapse (F2/F15 finding). XAUUSD H2 LONG underperformance could be modeled as asymmetric down-jumps (skewed event distribution).
- **Potential hypothesis:** Estimating asymmetric jump distributions per-instrument (using rolling-30-day M15 jump events) gives a directional risk feature.
- **Cross-domain links:** 03

### 19. Jumps and Stochastic Volatility: Exchange Rate Processes Implicit in Deutsche Mark Options (Bates 1996)

- **Authors:** David S. Bates
- **Year:** 1996
- **Source:** Review of Financial Studies 9(1): 69-107
- **URL:** http://deriscope.com/docs/Bates_1996.pdf
- **Model type:** Heston-stochastic + Merton-jumps (SVJ)
- **Abstract:** Combines Heston stochastic volatility and Merton jump-diffusion (SVJ model) and calibrates to DM/USD options 1984-1991. Shows pure stochastic vol cannot generate sufficient implied excess kurtosis without implausible parameters; jumps are required.
- **Key findings:**
  - SVJ = Heston SV + Merton jumps; characteristic function admits FFT
  - DM options: jumps account for ~half the smile curvature; SV accounts for the slope
  - Jump-risk premium is large and time-varying
  - Foreign exchange volatility smile is more symmetric than equity (no leverage effect of same magnitude)
- **Relevance to GTOS:** Direct evidence for FX instruments (USDJPY/GBPUSD/GBPJPY). FX vol is more symmetric → directional bias from skew is weaker than for equity indices.
- **Potential hypothesis:** For FX instruments, K54 should not heavily weight skew-derived features; for US30/NAS100/XAUUSD, skew matters more.
- **Cross-domain links:** 11 (FX)

### 20. Post-'87 Crash Fears in the S&P 500 Futures Option Market

- **Authors:** David S. Bates
- **Year:** 2000
- **Source:** Journal of Econometrics 94(1-2): 181-238
- **URL:** https://www.nber.org/system/files/working_papers/w5894/w5894.pdf
- **Model type:** SVJ with time-varying jump intensity
- **Abstract:** Documents persistent negative skewness in S&P 500 risk-neutral distributions post-1987 crash. Compares stochastic-vol-with-negative-correlation vs negative-mean jumps with time-varying frequency. Latter dominates.
- **Key findings:**
  - Risk-neutral distributions remain strongly negatively skewed years after 1987 crash
  - SV with negative correlation cannot fully replicate; jumps are required
  - Jump intensity itself is stochastic and time-varying — "fear" component
  - Implies persistent peso-problem effects in equity index markets
- **Relevance to GTOS:** "Fear" is persistent and asymmetric in equity indices. For US30/NAS100, OTM put skew is a K54 candidate feature for fear-regime detection.
- **Potential hypothesis:** US30 OTM put skew (e.g., 25-delta − 50-delta IV) is a fear-regime feature predicting LONG-side selectivity.
- **Cross-domain links:** 12

### 21. The Jump-Risk Premia Implicit in Options (Pan 2002)

- **Authors:** Jun Pan
- **Year:** 2002
- **Source:** Journal of Financial Economics 63(1): 3-50
- **URL:** https://pages.stern.nyu.edu/~dbackus/Disasters/Pan%20jump%20risk%20JFE%2002.PDF
- **Model type:** SVJ with jump-risk premium
- **Abstract:** Joint time-series estimation of S&P 500 + near-the-money short-dated options under SVJ model. Estimates a jump-risk premium that is volatility-dependent: high vol → high jump compensation.
- **Key findings:**
  - Risk-neutral mean jump size: -18%; physical mean jump size: -0.3% — premium of -17.6%
  - Jump-risk premium is positively correlated with market volatility
  - SV alone underprices OTM puts; jumps + jump premium close the gap
  - Joint estimation (returns + options) crucial for identification
- **Relevance to GTOS:** Vol-conditional jump premium = the markets price in MORE catastrophe-fear when vol is already high. For heartbeat-flatten and H29 DD-reduction, this implies vol-conditional thresholds are correct (which GTOS already does at 8%).
- **Potential hypothesis:** Heartbeat-flatten threshold should be vol-conditional (lower trigger when VIX is high).
- **Cross-domain links:** 21

### 22. Expected Stock Returns and Variance Risk Premia (Bollerslev-Tauchen-Zhou 2009)

- **Authors:** Tim Bollerslev, George Tauchen, Hao Zhou
- **Year:** 2009
- **Source:** Review of Financial Studies 22(11): 4463-4492
- **URL:** https://public.econ.duke.edu/~boller/Published_Papers/rfs_09.pdf
- **Model type:** VRP (model-free) vs return predictability
- **Abstract:** Variance risk premium (VIX² - realized variance) predicts S&P 500 returns at quarterly horizons. Predictability dominates classical predictors (P/E, default spread, consumption-wealth) at the quarterly horizon.
- **Key findings:**
  - VRP = model-free implied variance − realized variance
  - Quarterly-horizon return predictability: VRP best
  - Mechanism: time-varying economic uncertainty in general equilibrium
  - High VRP → high subsequent returns (consistent with risk premium for vol exposure)
- **Relevance to GTOS:** For multi-day position-holding, VRP is the strongest known predictor. GTOS holds 1-2h, so direct application is limited; BUT VRP regime conditioning of M15-edge expectancy is a hypothesis worth testing.
- **Potential hypothesis:** GTOS edge (R/trade) is non-stationary across VRP regimes; high-VRP days have different OB-precision than low-VRP days.
- **Cross-domain links:** 03

### 23. The VIX, the Variance Premium and Stock Market Volatility (Bekaert-Hoerova 2014)

- **Authors:** Geert Bekaert, Marie Hoerova
- **Year:** 2014
- **Source:** Journal of Econometrics 183(2): 181-192
- **URL:** https://www.ecb.europa.eu/pub/pdf/scpwps/ecbwp1675.pdf
- **Model type:** VIX decomposition
- **Abstract:** Decomposes squared VIX into conditional variance of stock returns + equity variance premium. Shows variance premium (= VIX² minus expected realized variance) tracks risk aversion; conditional variance tracks economic activity.
- **Key findings:**
  - Variance premium → predicts stock returns (consistent with BTZ 2009)
  - Conditional vol → predicts economic activity and financial instability
  - Two distinct channels: risk-aversion vs uncertainty
  - Variance premium more sensitive to monetary policy stance
- **Relevance to GTOS:** Two-component decomposition of VIX is more informative than VIX level. For K54: separately track variance-premium component and realized-vol forecast component.
- **Potential hypothesis:** Risk-aversion-component (variance premium) of VIX, not VIX level, drives F15 regime switches.
- **Cross-domain links:** 03, 17 (behavioral risk aversion)

### 24. What's Vol Got to Do with It (Drechsler-Yaron 2011)

- **Authors:** Itamar Drechsler, Amir Yaron
- **Year:** 2011
- **Source:** Review of Financial Studies 24(1): 1-45
- **URL:** https://repository.upenn.edu/fnce_papers/325/
- **Model type:** Long-run risk + variance premium GE model
- **Abstract:** Variance premium captures attitudes toward uncertainty. Calibrated long-run-risks model with non-Gaussian transient shocks reproduces variance premium time variation, return predictability, and matches market return + risk-free rate moments simultaneously.
- **Key findings:**
  - Variance premium is informative about uncertainty preferences (Epstein-Zin)
  - Non-Gaussian (jump-like) shocks essential for variance-premium dynamics
  - Calibrated GE matches both equity premium and variance premium
  - Implies both equity and variance premia have common driver
- **Relevance to GTOS:** General-equilibrium foundation — explains WHY variance premium predicts returns. For sizing literature (cross-link 21), this paper is key.
- **Potential hypothesis:** None directly tradable; provides interpretation framework.
- **Cross-domain links:** 17, 21

### 25. Tails, Fears, and Risk Premia (Bollerslev-Todorov 2011)

- **Authors:** Tim Bollerslev, Viktor Todorov
- **Year:** 2011
- **Source:** Journal of Finance 66(6): 2165-2211
- **URL:** https://www.kellogg.northwestern.edu/faculty/todorov/htm/papers/jrp.pdf
- **Model type:** Jump-tail risk premium estimation
- **Abstract:** Decomposes equity and variance risk premia into "rare event" component vs "diffusive" component. Develops "Investor Fears" index from short-maturity OTM options + extreme value theory on jump tails.
- **Key findings:**
  - Rare-event compensation = large fraction of equity + variance premia
  - Investor Fears index from OTM puts: large time-varying jump-tail premium
  - Jump tails are model-free identifiable from option-implied vs realized tail measures
  - Strongly time-varying compensation for disaster fears
- **Relevance to GTOS:** Catastrophe-protection calibration target. For heartbeat-flatten threshold setting, jump-tail-implied probability gives the correct measure.
- **Potential hypothesis:** Bollerslev-Todorov fear-index level conditions GTOS's edge (high-fear regimes have different OB outcomes).
- **Cross-domain links:** 03 (tails), 17 (behavioral)

### 26. Understanding the VIX (Whaley 2009)

- **Authors:** Robert E. Whaley
- **Year:** 2009
- **Source:** Journal of Portfolio Management 35(3): 98-105
- **URL:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1296743
- **Model type:** VIX (overview)
- **Abstract:** Practitioner overview of VIX construction, history, and "investor fear gauge" interpretation. Explains why VIX is asymmetric: dominated by put-buying hedger demand.
- **Key findings:**
  - VIX = forward-looking 30-day expected vol from option strip
  - VIX rises sharply in selloffs (asymmetric); reflects portfolio-insurance demand
  - Not symmetric vol measure: skewed up by put demand
  - VIX is less an "expected vol" forecast and more an "insurance price"
- **Relevance to GTOS:** For interpretation: VIX up does not just mean expected vol up; it also means more demand for insurance (and could reflect supply contraction). Don't take VIX literally as expected vol.
- **Potential hypothesis:** None directly; calibration cautionary.
- **Cross-domain links:** 12

### 27. Inferring Volatility Dynamics and Risk Premia from S&P 500 and VIX Markets (Bardgett-Gourier-Leippold 2019)

- **Authors:** Chris Bardgett, Elise Gourier, Markus Leippold
- **Year:** 2019
- **Source:** Journal of Financial Economics 131(3): 593-618
- **URL:** http://www.elisegourier.com/uploads/3/7/9/6/37964671/bardgett_gourier_leippold_vix_paper.pdf
- **Model type:** Three-factor stochastic-vol with jumps; joint S&P + VIX options
- **Abstract:** Jointly estimates affine three-factor SV+jump model on S&P 500 and VIX options panel. Shows VIX options contain information not spanned by S&P 500 alone — particularly about risk-neutral conditional distributions of vol at different horizons.
- **Key findings:**
  - VIX options span term-structure of vol uncertainty independently
  - Three-factor SV model: short-vol, long-vol, vol-of-vol — all priced separately
  - Variance risk premium decomposable across maturities
  - Standard model with single vol factor underprices VIX options consistently
- **Relevance to GTOS:** If GTOS adds option features, VIX options surface (not just VIX level) is the right input. Vol-of-vol (VVIX) is the cleanest standalone measure of uncertainty about vol.
- **Potential hypothesis:** VVIX is a stronger regime-classifier feature than VIX for K54.
- **Cross-domain links:** 12

### 28. Volatility is (Mostly) Path-Dependent (Guyon-Lekeufack 2023)

- **Authors:** Julien Guyon, Jordan Lekeufack
- **Year:** 2023
- **Source:** Quantitative Finance 23(9): 1221-1258
- **URL:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4174589
- **Model type:** Path-dependent volatility (PDV) — 4-factor extension
- **Abstract:** Up to 90% of implied vol variance and 65% of realized vol variance is explained by simple path-dependent function of past index returns: linear combination of weighted-sum-of-past-returns + sqrt-weighted-sum-of-squared-past-returns with power-law-decay weights.
- **Key findings:**
  - 4-factor PDV: 4 power-law-weighted-sums of past returns and squared returns
  - Outperforms rough-vol AND classical SV across train/test on equity indices
  - Same model fits both physical (realized vol) AND risk-neutral (implied vol)
  - Joint SPX + VIX smile fit competitive with state-of-art
- **Relevance to GTOS:** Most exciting recent paper for GTOS application. Pure path-dependent function of past returns (no latent SV factor) explains 65% of realized vol variance. For K54 v3: build M15 PDV features (power-law-weighted sum of past returns, with multiple decay rates).
- **Potential hypothesis:** PDV-style power-law-weighted past-return aggregations are feature-engineerable from M15 OHLC alone, no exogenous data, and would strongly outperform the current K54 v2 lag-1 squared-return autocorrelation.
- **Cross-domain links:** 04 (long memory)

### 29. The Relation Between Implied and Realized Volatility (Christensen-Prabhala 1998)

- **Authors:** Bent J. Christensen, Nagpurnanand R. Prabhala
- **Year:** 1998
- **Source:** Journal of Financial Economics 50(2): 125-150
- **URL:** https://www.sciencedirect.com/science/article/pii/S0304405X98000348
- **Model type:** Predictive regression
- **Abstract:** With longer time series and non-overlapping data, implied vol outperforms past vol in forecasting future vol; sometimes subsumes the information in past vol entirely. Refutes earlier claims that implied vol is biased.
- **Key findings:**
  - 1987 crash regime shift biased earlier studies
  - Non-overlapping monthly data: IV is unbiased and dominant
  - IV captures arrival of new information; past vol is backward-looking
  - Methodological: overlap creates spurious bias
- **Relevance to GTOS:** Whenever option-implied data is available, it dominates historical-vol forecasts. If GTOS K54 ingests VIX/GVZ for instruments, weight implied higher than ATR-derived past vol.
- **Potential hypothesis:** For US30/NAS100/XAUUSD: VIX/VXN/GVZ as vol forecast > rolling realized vol.
- **Cross-domain links:** 03

### 30. The Shape and Term Structure of the Index Option Smirk (Christoffersen-Heston-Jacobs 2009)

- **Authors:** Peter Christoffersen, Steven L. Heston, Kris Jacobs
- **Year:** 2009
- **Source:** Management Science 55(12): 1914-1932
- **URL:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=961037
- **Model type:** Two-factor stochastic vol
- **Abstract:** Single-factor SV models capture skew slope but not its time variation independent of level. Two-factor SV model with distinct factor correlations and time-varying weights — improves on Heston by 24% in/out-of-sample.
- **Key findings:**
  - Smirk slope and level fluctuate independently
  - Single Heston factor cannot generate this; two factors required
  - Stochastic correlation structure between vol and returns
  - Multifactor SV is the modern industry standard
- **Relevance to GTOS:** If multi-component vol is the right model, K54 features should reflect short-term vs long-term vol independently (not just one ATR window).
- **Potential hypothesis:** Add both short-window (5-bar) and long-window (24-bar) realized vol as separate features; let the classifier learn the interaction.
- **Cross-domain links:** 12

### 31. Roughing It Up: Including Jump Components in the Measurement, Modeling, and Forecasting of Return Volatility

- **Authors:** Torben G. Andersen, Tim Bollerslev, Francis X. Diebold
- **Year:** 2007
- **Source:** Review of Economics and Statistics 89(4): 701-720
- **URL:** https://www.nber.org/papers/w11775
- **Model type:** Realized volatility decomposition
- **Abstract:** Develops bipower variation + nonparametric jump tests to decompose realized variance into continuous and jump components. Empirically: jump component is highly important, less persistent than continuous; jump-aware models forecast better out-of-sample.
- **Key findings:**
  - RV = continuous variance + sum-of-squared-jumps
  - Bipower variation is jump-robust estimator of continuous component
  - Jumps cluster around macro news announcements
  - HAR-RV-CJ: HAR with separate continuous + jump terms; significant out-of-sample gain
- **Relevance to GTOS:** Jump-aware HAR is the modern best-practice realized-vol forecaster. K54 should distinguish jump-driven vs continuous vol, not aggregate.
- **Potential hypothesis:** HAR-RV-CJ-style features (separate continuous and jump RV) outperform aggregated realized-vol in K54 v3.
- **Cross-domain links:** 04, 03

### 32. The Investor Fear Gauge / Variance Risk Premia VIX-FUTURES research

- **Authors:** Robert E. Whaley
- **Year:** 2000 (original 1993 article); 2009 update
- **Source:** Journal of Portfolio Management 26(3): 12-17
- **URL:** https://www.researchgate.net/publication/247920760_The_Investor_Fear_Gauge
- **Model type:** VIX (interpretation)
- **Abstract:** Original 1993 derivation framing of VIX as "fear gauge" — measures market participants' anxiety about near-term equity declines.
- **Key findings:**
  - VIX rises asymmetrically in selloffs vs rallies
  - Hedger-driven put demand creates persistent positive skew in VIX dynamics
  - VIX leads VVIX in major selloffs but VVIX leads in tail-event aftermath
- **Relevance to GTOS:** Sentiment-style interpretation of VIX. If GTOS regime-classifier (K54) ingests VIX, treat it as fear sentiment, not pure expected vol.
- **Potential hypothesis:** None directly tradable.
- **Cross-domain links:** 12, 17

### 33. Volatility Dynamics for the S&P 500: Evidence from Realized Volatility, Daily Returns, and Option Prices (Christoffersen-Jacobs-Mimouni 2010)

- **Authors:** Peter Christoffersen, Kris Jacobs, Karim Mimouni
- **Year:** 2010
- **Source:** Review of Financial Studies 23(8): 3141-3189
- **URL:** https://academic.oup.com/rfs/article-abstract/23/8/3141/1589270
- **Model type:** Stochastic volatility model comparison
- **Abstract:** Triangulates 5 alternative SV models against three independent data sources: realized vol, S&P 500 returns, and large options panel. Best specification: linear (not square-root / CIR) diffusion for variance.
- **Key findings:**
  - Linear-diffusion-of-variance dominates square-root (Heston) in all three datasets
  - Multi-source consistency check is methodologically critical
  - Linear-vol model has lower IV mean-squared error in/out of sample
  - Stylized facts in realized vol point to linear (not CEV) variance dynamics
- **Relevance to GTOS:** Provides the empirical case for linear-vol-of-vol over square-root-vol-of-vol. Practical: variance-of-variance is approximately constant, not vol-dependent.
- **Potential hypothesis:** None directly.
- **Cross-domain links:** 03

### 34. A Forecast Comparison of Volatility Models: Does Anything Beat a GARCH(1,1)? (Hansen-Lunde 2005)

- **Authors:** Peter R. Hansen, Asger Lunde
- **Year:** 2005
- **Source:** Journal of Applied Econometrics 20(7): 873-889
- **URL:** https://onlinelibrary.wiley.com/doi/abs/10.1002/jae.800
- **Model type:** GARCH families comparison
- **Abstract:** Tournament of 330 ARCH-family models on DM/USD exchange rate and IBM equity returns, controlled for data-snooping (SPA test). For FX: nothing beats GARCH(1,1). For equity (IBM): GJR-GARCH wins (leverage effect critical).
- **Key findings:**
  - GARCH(1,1) is hard-to-beat baseline for FX volatility
  - For equity, asymmetric/leverage models (GJR, EGARCH) win
  - Data-snooping inflates many ML/complex-model claims
  - SPA + Reality Check methodology is the rigorous benchmark
- **Relevance to GTOS:** Strong statistical baseline for K54 vol features. For FX instruments (USDJPY, GBPUSD, GBPJPY), GARCH(1,1) is the right baseline; for index/gold, leverage-aware GARCH (GJR / EGARCH).
- **Potential hypothesis:** Per-instrument vol model: GJR-GARCH for XAUUSD/US30/NAS100; GARCH(1,1) for FX.
- **Cross-domain links:** 02 (statistical methodology — SPA test), 03

### 35. Generalized Autoregressive Conditional Heteroskedasticity (Bollerslev 1986)

- **Authors:** Tim Bollerslev
- **Year:** 1986
- **Source:** Journal of Econometrics 31(3): 307-327
- **URL:** https://public.econ.duke.edu/~boller/Published_Papers/joe_86.pdf
- **Model type:** GARCH (foundational)
- **Abstract:** Generalizes Engle 1982 ARCH by allowing past conditional variances in the conditional-variance equation. GARCH(p,q): more flexible lag structure, parsimonious.
- **Key findings:**
  - σ²_t = ω + α·ε²_{t-1} + β·σ²_{t-1} (GARCH(1,1))
  - Stationarity: α + β < 1
  - Maximum-likelihood estimation
  - Connects to ARMA framework for variance
- **Relevance to GTOS:** Bedrock vol-clustering model. Direct candidate K54 v3 baseline against more complex models.
- **Potential hypothesis:** GARCH(1,1) on M15 returns gives a strong vol-clustering K54 baseline.
- **Cross-domain links:** 03

### 36. Autoregressive Conditional Heteroscedasticity (Engle 1982)

- **Authors:** Robert F. Engle
- **Year:** 1982
- **Source:** Econometrica 50(4): 987-1007
- **URL:** http://www.econ.uiuc.edu/~econ536/Papers/engle82.pdf
- **Model type:** ARCH (foundational)
- **Abstract:** Introduces ARCH processes — mean-zero, serially uncorrelated, with non-constant conditional variance. Maximum-likelihood estimation; LM test for ARCH effects. Empirical: UK inflation has substantial ARCH effect, especially in chaotic 1970s.
- **Key findings:**
  - Conditional vs unconditional moments differ
  - ARCH(p): variance depends on past p squared innovations
  - Lagrange multiplier test for ARCH effects
  - Foundation for entire vol-clustering literature
- **Relevance to GTOS:** Original work. Vol-clustering is the most robust empirical fact in finance.
- **Potential hypothesis:** None novel; embedded in K54.
- **Cross-domain links:** 03

### 37. Conditional Heteroskedasticity in Asset Returns: A New Approach (Nelson 1991 EGARCH)

- **Authors:** Daniel B. Nelson
- **Year:** 1991
- **Source:** Econometrica 59(2): 347-370
- **URL:** Reference and overview at https://vlab.stern.nyu.edu/docs/volatility/EGARCH
- **Model type:** EGARCH (asymmetric)
- **Abstract:** Specifies log-conditional-variance directly (no positivity constraints). Allows explicit asymmetric response to positive vs negative shocks via signed function of standardized residuals.
- **Key findings:**
  - log(σ²_t) = ω + α·g(z_{t-1}) + β·log(σ²_{t-1})
  - g(z) embeds asymmetry: |z| − E|z| + γ·z
  - No parameter restrictions for positive vol
  - Captures leverage effect more cleanly than GJR
- **Relevance to GTOS:** Asymmetric vol response is mandatory for equity-style instruments. EGARCH is one of two standard choices (GJR is the other).
- **Potential hypothesis:** EGARCH-residual-z is itself a K54 feature (signed standardized return).
- **Cross-domain links:** 03

### 38. On the Relation Between the Expected Value and the Volatility of the Nominal Excess Return on Stocks (GJR-GARCH; Glosten-Jagannathan-Runkle 1993)

- **Authors:** Lawrence R. Glosten, Ravi Jagannathan, David E. Runkle
- **Year:** 1993
- **Source:** Journal of Finance 48(5): 1779-1801
- **URL:** https://faculty.washington.edu/ezivot/econ589/GJRJOF1993.pdf
- **Model type:** GJR-GARCH (asymmetric)
- **Abstract:** Modified GARCH-M with seasonal dummies, asymmetric news effect (positive vs negative innovation), and nominal interest-rate predictor. Finds weak negative relation between conditional variance and expected return; asymmetric volatility response is robust.
- **Key findings:**
  - σ²_t = ω + α·ε²_{t-1} + γ·I[ε_{t-1}<0]·ε²_{t-1} + β·σ²_{t-1}
  - Negative shocks raise vol much more than positive of same magnitude
  - Volatility is less persistent than first thought after seasonality + asymmetry adjustment
  - Industry-standard alternative to EGARCH
- **Relevance to GTOS:** Captures the "vol up on selloff" asymmetry pivotal for equity indices.
- **Potential hypothesis:** GJR-style asymmetric squared-return feature significantly improves K54 selectivity prediction.
- **Cross-domain links:** 03, 12

### 39. Microstructure Noise, Realized Variance, and Optimal Sampling (Bandi-Russell 2008)

- **Authors:** Federico M. Bandi, Jeffrey R. Russell
- **Year:** 2008
- **Source:** Review of Economic Studies 75(2): 339-369
- **URL:** https://academic.oup.com/restud/article-abstract/75/2/339/1620899
- **Model type:** Realized variance + microstructure noise
- **Abstract:** Quantifies microstructure-noise bias in realized variance; derives MSE-optimal sampling frequency that trades off noise-bias against high-frequency variance reduction. Shows traditional 5-min sampling is suboptimal; optimal frequency is asset-specific.
- **Key findings:**
  - Observed price = efficient price × multiplicative noise
  - Optimal sampling: trade off noise bias vs sampling variance
  - 5-min is fine for liquid equities; higher freq for less liquid; lower freq for very noisy
  - Subsampling + sparse-then-average estimators improve over naive RV
- **Relevance to GTOS:** GTOS tick daemon → must choose appropriate sampling frequency for realized-vol-derived K54 features. For low-volume instruments (during off-session hours), tick-level sampling could induce more noise than signal.
- **Potential hypothesis:** Per-instrument optimal sampling freq for realized-vol features in K54 v3.
- **Cross-domain links:** 06 (microstructure)

### 40. Drift-Independent Volatility Estimation Based on High, Low, Open, and Close Prices (Yang-Zhang 2000)

- **Authors:** Dennis Yang, Qiang Zhang
- **Year:** 2000
- **Source:** Journal of Business 73(3): 477-492
- **URL:** https://www.jstor.org/stable/10.1086/209650
- **Model type:** Range-based volatility estimator
- **Abstract:** Combines overnight, close-to-close, and intraday Rogers-Satchell estimators with optimal weight (k≈0.34). Drift-independent, unbiased in continuous limit, handles opening jumps; minimum variance among such estimators.
- **Key findings:**
  - σ_YZ² = σ_O² + k·σ_C² + (1-k)·σ_RS²
  - Drift-independent (handles non-zero return drift)
  - Handles opening price jumps cleanly
  - Smaller variance than Garman-Klass, Parkinson, or Rogers-Satchell alone
- **Relevance to GTOS:** Without tick data, Yang-Zhang gives the cleanest single-bar vol estimate. Across M15 / H1 candles, YZ is a strictly stronger ATR replacement.
- **Potential hypothesis:** YZ-vol over M15 candles is a strictly better K54 feature than ATR-14.
- **Cross-domain links:** 03, 06

### 41. The Extreme Value Method for Estimating the Variance of the Rate of Return (Parkinson 1980)

- **Authors:** Michael Parkinson
- **Year:** 1980
- **Source:** Journal of Business 53(1): 61-65
- **URL:** Reference at https://www.scirp.org/reference/referencespapers?referenceid=1728924
- **Model type:** Range-based volatility (high-low)
- **Abstract:** Uses high-low range to estimate volatility, exploiting that range is roughly 5x more efficient than close-to-close. Foundational; assumes lognormal price + zero drift.
- **Key findings:**
  - σ_P² = (high − low)² / (4·ln 2)
  - 5x more efficient than close-to-close
  - No drift adjustment; biased if drift is non-zero
  - First range-based estimator
- **Relevance to GTOS:** Cheap historical-vol estimator from OHLC. For instruments with thin tick data, range-based is more reliable than naive sum-of-squared-returns.
- **Potential hypothesis:** Parkinson is a fast lower-bound vol feature.
- **Cross-domain links:** 03

### 42. On the Estimation of Security Price Volatilities from Historical Data (Garman-Klass 1980)

- **Authors:** Mark B. Garman, Michael J. Klass
- **Year:** 1980
- **Source:** Journal of Business 53(1): 67-78
- **URL:** https://www-2.rotman.utoronto.ca/~kan/3032/pdf/FinancialAssetReturns/Garman_Klass_JB_1980.pdf
- **Model type:** Range + open-close volatility estimator
- **Abstract:** Uses all OHLC: high, low, open, close. 7.4x more efficient than close-to-close. Assumes Brownian motion with zero drift, no opening jumps.
- **Key findings:**
  - σ_GK² = 0.5·(ln(H/L))² − (2ln 2 − 1)·(ln(C/O))²
  - 7.4x more efficient than close-to-close
  - Assumes no drift, no opening jumps (limiting for FX)
  - Foundation for many subsequent estimators (Yang-Zhang generalization)
- **Relevance to GTOS:** Direct candidate K54 feature: GK-vol over M15 candles. Combine with Yang-Zhang for drift/jump robustness.
- **Potential hypothesis:** GK-vol is a strictly better feature than ATR-of-1-bar.
- **Cross-domain links:** 03

### 43. Stochastic Skew in Currency Options (Carr-Wu 2007)

- **Authors:** Peter Carr, Liuren Wu
- **Year:** 2007
- **Source:** Journal of Financial Economics 86(1): 213-247
- **URL:** https://engineering.nyu.edu/sites/default/files/2019-03/Carr-stochastic-skew-in-currency-options.pdf
- **Model type:** Time-changed Lévy processes (stochastic skew)
- **Abstract:** Documents stochastic skewness in currency options — risk reversals fluctuate widely in magnitude AND sign. Standard SVJ models (Bates 1996) cannot generate this. Time-changed Lévy processes with separate up/down jump components do.
- **Key findings:**
  - Risk reversal sign changes (FX skew is bidirectional, unlike equity)
  - Two-component Lévy: separate up-jump and down-jump time-changes
  - Captures stochastic vol AND stochastic skewness simultaneously
  - Relevant for emerging-market currencies and major-cross FX
- **Relevance to GTOS:** For USDJPY, GBPUSD, GBPJPY: skew is bidirectional and time-varying. F2/F15 LONG/SHORT asymmetry could partly reflect underlying currency-skew dynamics.
- **Potential hypothesis:** FX risk-reversal sign and magnitude predict realized R asymmetry across LONG/SHORT trades.
- **Cross-domain links:** 11

### 44. 0DTEs: Trading, Gamma Risk and Volatility Propagation (Dim-Eraker-Vilkov 2023)

- **Authors:** Chukwuma Dim, Bjorn Eraker, Grigory Vilkov
- **Year:** 2023
- **Source:** SSRN working paper (Northern Finance Association draft 2024)
- **URL:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4692190
- **Model type:** Empirical 0DTE microstructure
- **Abstract:** Studies the explosion in same-day-expiry (0DTE) options on S&P 500 since 2022. Tests whether 0DTE gamma destabilizes the index. Finds no evidence of destabilization; for >1 day options, open-interest gamma is associated with LOWER realized vol.
- **Key findings:**
  - 0DTE volume now exceeds 50% of all index option volume (2024)
  - Open-interest gamma in non-0DTE options dampens realized vol
  - Variance risk premium is U-shaped in maturity — extreme for 0DTE, decreasing through 1-week, then rising
  - 0DTE gamma effects cluster in last hour of trading
- **Relevance to GTOS:** Direct relevance for US30 / NAS100 last-NY-hour behavior. The "skip first NY candle" type rule has a literature analog: skip the OPEX/0DTE-driven last hour.
- **Potential hypothesis:** Last-NY-hour US30/NAS100 trades have different outcome distribution post-2022 due to 0DTE; calibrate kill-zone end-time.
- **Cross-domain links:** 12 (equity-index gamma)

### 45. Local Volatility / Pricing with a Smile (Dupire 1994)

- **Authors:** Bruno Dupire
- **Year:** 1994
- **Source:** Risk Magazine 7(1): 18-20
- **URL:** https://faculty.fordham.edu/rchen/Dupire.pdf
- **Model type:** Local volatility (deterministic function of S, t)
- **Abstract:** Given complete option prices for all strikes/maturities, derives unique risk-neutral diffusion coefficient σ(S,t). Provides arbitrage-free local-vol surface; matches market exactly.
- **Key findings:**
  - σ²_loc(K,T) closed-form from market option prices (Dupire formula)
  - Matches market exactly; suitable for path-dependent options
  - Local vol is smile-conditional; not the same as instantaneous vol
  - Critique: dynamics of local vol are unrealistic (smile shifts wrong way under spot moves) — motivates SABR
- **Relevance to GTOS:** Local-vol surface gives instrument-specific risk-neutral vol distribution by spot/time. Could inform per-instrument risk gating.
- **Potential hypothesis:** None directly.
- **Cross-domain links:** 12

### 46. Option Valuation Using the Fast Fourier Transform (Carr-Madan 1998)

- **Authors:** Peter Carr, Dilip B. Madan
- **Year:** 1998
- **Source:** Journal of Computational Finance 2(4): 61-73
- **URL:** https://engineering.nyu.edu/sites/default/files/2018-08/CarrMadan2_0.pdf
- **Model type:** FFT-based option pricing (numerical)
- **Abstract:** Closed-form FFT-based option pricing for any model whose log-price has known characteristic function. Massively accelerates Heston, Bates, VG, NIG, CGMY pricing.
- **Key findings:**
  - Damped option price → integrable; admits FFT
  - Vectorized strike grid evaluation in single FFT call
  - Standard tool for SV/jump model calibration
  - Generalizable to any characteristic-function-known model
- **Relevance to GTOS:** Computational tool. If GTOS calibrates SV models per instrument, FFT is the standard implementation method.
- **Potential hypothesis:** None (tool, not model).
- **Cross-domain links:** 02 (numerical methods)

### 47. Dynamic Conditional Correlation: A Simple Class of Multivariate GARCH Models (Engle 2002 DCC)

- **Authors:** Robert F. Engle
- **Year:** 2002
- **Source:** Journal of Business and Economic Statistics 20(3): 339-350
- **URL:** https://pages.stern.nyu.edu/~rengle/dccfinal.pdf
- **Model type:** DCC multivariate GARCH
- **Abstract:** Two-step multivariate GARCH: univariate GARCH for each marginal volatility; transformed standardized residuals fit time-varying conditional correlation.
- **Key findings:**
  - DCC(1,1): Q_t = (1-a-b)Q_bar + a·z_{t-1}z'_{t-1} + b·Q_{t-1}
  - Two-step estimation: parsimony + scalability
  - Captures time-varying correlation efficiently
  - Industry standard for multivariate vol
- **Relevance to GTOS:** GTOS cross-instrument correlation gate uses static rolling correlations; DCC is the dynamic upgrade. Relevant for hard cross-asset risk gates.
- **Potential hypothesis:** DCC-conditional correlation (XAUUSD ↔ DXY ↔ NAS100) is more reactive than rolling-N correlation; would tighten correlation-gate detection of regime breaks.
- **Cross-domain links:** 13

### 48. Lassoing the HAR Model (Audrino-Knaus 2016)

- **Authors:** Francesco Audrino, Simon D. Knaus
- **Year:** 2016
- **Source:** Econometric Reviews 35(8-10): 1485-1521
- **URL:** https://ideas.repec.org/a/taf/emetrv/v35y2016i8-10p1485-1521.html
- **Model type:** HAR + Lasso
- **Abstract:** Asymptotic theory shows Lasso recovers HAR's true lag structure when HAR is the DGP. Empirically: HAR's a-priori (1,5,22) lag structure does NOT match Lasso-selected lags on real data — and there are clear structural breaks.
- **Key findings:**
  - Lasso-recovered lag structure differs from HAR's defaults
  - Two clear regime breaks for most assets
  - Calls into question one-size-fits-all HAR specification
  - Recommends data-driven lag selection
- **Relevance to GTOS:** Critical methodological point: even simple-looking HAR has data-driven optimal lag structure. K54 should not pre-specify squared-return lag-1; let regularized regression select.
- **Potential hypothesis:** Lasso-selected past-return power-law features (multi-lag PDV-style; combining with paper #28 Guyon-Lekeufack) outperforms HAR(1,5,22).
- **Cross-domain links:** 02 (statistical methodology), 19 (ML)

### 49. Deep Learning Volatility (Horvath, Muguruza, Tomas 2021) and 2024 interpretability

- **Authors:** Blanka Horvath, Aitor Muguruza, Mehdi Tomas (and 2024 interpretability work by Friz, Hager, et al.)
- **Year:** 2021 (deep-learning calibration); 2024-2025 (interpretability)
- **Source:** Quantitative Finance 21(1): 11-27 (and arXiv 2411.19317 for interpretability)
- **URL:** https://arxiv.org/abs/1901.09647 ; https://arxiv.org/html/2411.19317v1
- **Model type:** Neural-network calibration of rough vol
- **Abstract:** Two-step: train neural network to learn pricing map (rBergomi parameters → option prices); then use classical calibration on the network. Brings rough-vol calibration within real-time tolerance (millisecond-scale).
- **Key findings:**
  - Calibration time: 10-100 milliseconds for full IV surface
  - Generalizable across SV/rough-vol families
  - Recent (2024) interpretability work links network-learned weights to known rough-vol features
- **Relevance to GTOS:** If GTOS adds rough-vol features in K54 v3, deep-NN calibration is the practical path (otherwise rBergomi is too slow per-candle).
- **Potential hypothesis:** Pre-calibrated rough-vol features are computationally feasible at the M15 cadence using NN-based pipelines.
- **Cross-domain links:** 19 (ML)

### 50. Micro Effects of Macro Announcements: Real-Time Price Discovery in Foreign Exchange (Andersen-Bollerslev-Diebold-Vega 2003)

- **Authors:** Torben G. Andersen, Tim Bollerslev, Francis X. Diebold, Clara Vega
- **Year:** 2003
- **Source:** American Economic Review 93(1): 38-62
- **URL:** https://www.aeaweb.org/articles?id=10.1257/000282803321455151
- **Model type:** Event-study + jump decomposition
- **Abstract:** Six years of real-time FX quotes + macro expectations + realizations. Documents that announcement surprises produce conditional-mean jumps; high-frequency exchange rate dynamics are linked to fundamentals; bad news has greater impact than good news.
- **Key findings:**
  - Announcement effect peaks at 5-15min post-release; persists 30-60min
  - Asymmetry: bad news > good news
  - News-driven jumps → identifiable in high-frequency data
  - Vol elevation is event-specific; clustering of news effects
- **Relevance to GTOS:** Direct relevance for FX kill-zone calibration (USDJPY, GBPUSD, GBPJPY) around US/UK/JP macro releases. Defines the announcement-window logic GTOS should use.
- **Potential hypothesis:** Distance-to-next-major-macro-release is a hard K54 feature; trades within 30 minutes of NFP / FOMC / BOE / BOJ releases have substantially different outcome distributions.
- **Cross-domain links:** 11 (FX), 06 (microstructure)

---

## End of papers.md
