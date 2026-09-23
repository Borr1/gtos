# Domain 12 — Equity Indices, Options, Gamma Flow

**Worker:** Phase 1 Worker Agent #12
**Date:** 2026-04-28
**Spec:** `research/ml_program/literature/_specs/12_equity_indices_options_gamma.md`
**Index_studied special field:** SPX / NDX / DJI / RUT / VIX / multi
**Paper count:** 45 (target 35-50; quality bar dominates)

---

## 1. Domain framing

This domain catalogs research relevant to GTOS's equity-index instruments — **NAS100 (NDX) and US30 (DJI)** in production, with SPX literature serving as the deep base because (a) virtually all dealer-gamma / OPEX-pinning / 0DTE work targets SPX, and (b) the dealer-flow mechanics that drive intraday SPX behavior also drive NDX (via QQQ + NDX options and futures) and DJI (via DIA + futures, with thinner option flow). Cross-domain handoffs respected per `_INDEX.md` §6:
- VIX as **trading instrument / vol regime classifier** → 16; VIX as **descriptive volatility stylized fact** → 03 (here we keep VIX papers that pertain to *index price action* — leverage effect, post-FOMC, fear-gauge predictability).
- Generic OPEX VWAP / volume → 08; we keep **dealer-gamma-driven pinning + index-specific OPEX**.
- Round-number levels generally → 09; OPEX-strike magnetism specifically here.
- Cross-section equity factor anomalies → 13; we keep **index-level** factor research.
- Macro central-bank surprise framing → 11; we keep the **index-side reaction** to FOMC / CPI.

**Key gaps documented in §7:**
- NAS100-specific gamma / 0DTE empirical work is sparse — most papers study SPX. NDX-specific divergence research is mostly grey/practitioner literature.
- US30 / DJI-specific research is the thinnest sub-segment — DJI options have far less academic attention than SPX. F9 hallucination decomposition is supported by general index-microstructure literature, not DJI-specific work.

---

## 2. Foundational papers (1990s-2010s)

### Does Net Buying Pressure Affect the Shape of Implied Volatility Functions?
- **Authors:** Nicolas P. B. Bollen, Robert E. Whaley
- **Year:** 2004
- **Source:** Journal of Finance, Vol. 59, pp. 711-753
- **URL:** https://onlinelibrary.wiley.com/doi/10.1111/j.1540-6261.2004.00647.x
- **Abstract:** Examines the relation between net buying pressure and the shape of the implied volatility function (IVF) for index and individual stock options. Finds that changes in implied volatility are directly related to net buying pressure from public order flow. SPX index options dominated by put buying pressure; individual stock options dominated by call demand.
- **Key findings:**
  - Index put buying pressure shapes the SPX IVF (steepening the skew during stress)
  - Stock options dominated by call demand
  - Delta-neutral short-option strategies generate abnormal returns matching IVF deviations from historical vol
  - Demand pressure on options is not arbitraged away
  - Strong evidence against pure no-arbitrage IVF dynamics
- **Relevance to GTOS:** Foundational for understanding why SPX (and by extension NDX) put-side of vol surface is structurally bid. NAS100 dealer hedging in puts has same mechanics. K54 v2 candidate feature: index put-call IV skew as a regime classifier.
- **Potential hypothesis:** When NDX put-side IV is anomalously high relative to call-side (>1σ skew), short setups face headwind because dealer-hedging buy-flow supports the index.
- **Cross-domain links:** 16 (IVF as pricing input)
- **index_studied:** SPX (extends to NDX)

### Demand-Based Option Pricing
- **Authors:** Nicolae Gârleanu, Lasse Heje Pedersen, Allen M. Poteshman
- **Year:** 2009
- **Source:** Review of Financial Studies, Vol. 22(10), pp. 4259-4299
- **URL:** https://academic.oup.com/rfs/article-abstract/22/10/4259/1590158
- **Abstract:** Models demand-pressure effects on option prices. Demand pressure in one option contract increases its price by an amount proportional to the variance of the unhedgeable part of the option, plus a portion of the covariance with other contracts. Identifies aggregate dealer vs end-user positions; explains pricing puzzles for index options.
- **Key findings:**
  - Demand pressure → option price impact proportional to unhedgeable variance
  - Index options structurally expensive due to end-user net long demand
  - Cross-sectional demand pressure also drives single-stock option expensiveness
  - Dealer aggregate positions persistently short premium (writers of insurance)
  - Quantifies "expensiveness" puzzle on SPX options
- **Relevance to GTOS:** Mechanism explaining why dealers carry net short gamma and consequently drive intraday flows through their hedging. Foundational for K54 features that use dealer-positioning proxies.
- **Potential hypothesis:** Days when end-user option demand is anomalously elevated (proxy: open interest growth × IV skew) precede regime where dealer hedging dampens NDX intraday breakouts.
- **Cross-domain links:** 16, 13
- **index_studied:** SPX

### Stock Price Clustering on Option Expiration Dates
- **Authors:** Sophie Xiaoyan Ni, Neil D. Pearson, Allen M. Poteshman
- **Year:** 2005
- **Source:** Journal of Financial Economics, Vol. 78(1), pp. 49-87
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S0304405X05000577
- **Abstract:** Documents that on expiration dates, closing prices of optionable stocks cluster at strike prices. The effect is large enough to alter expiration-date returns by ≥16.5 bp, equating to $9B of aggregate market-cap shifts. Hedge rebalancing and proprietary-trader manipulation are shown as mechanisms.
- **Key findings:**
  - Statistically significant pinning at high open-interest strikes
  - Mechanism: market-maker delta-hedging force-pins price toward strike
  - Manipulation by firm proprietary traders also detected
  - >19% of optionable stocks close within $0.25 of a strike on OPEX vs <18% on non-OPEX Fridays
  - Pinning is conditional, not deterministic
- **Relevance to GTOS:** **Direct relevance to F9 US30 hallucination decomposition** — dense-strike index pinning could explain residual real-grounding-failure cohort behaviors. NDX OPEX strike magnetism affects round-number-tier setups.
- **Potential hypothesis:** On OPEX days (3rd Friday + 3rd Wednesday for SPXW), NDX/US30 setups that have high-OI strikes within 1 ATR experience reduced trend-continuation; flag as low-quality.
- **Cross-domain links:** 09 (round-number magnetism), 08 (OPEX session)
- **index_studied:** multi (single-stock + extends to indices)

### The Investor Fear Gauge
- **Authors:** Robert E. Whaley
- **Year:** 2000
- **Source:** Journal of Portfolio Management, Vol. 26(3), pp. 12-17
- **URL:** https://jpm.pm-research.com/content/26/3/12
- **Abstract:** Introduces the VIX index as a forward-looking implied-volatility measure constructed from S&P 100 OEX option prices. Establishes the VIX as a barometer of market sentiment ("fear gauge"). Lays the foundation for subsequent VIX-as-trading-instrument literature.
- **Key findings:**
  - VIX inversely correlates with S&P 500 returns
  - Asymmetric: VIX spikes more on down moves than rallies
  - Useful sentiment proxy beyond fundamentals
  - Constructed from 8 near-the-money OEX option series
  - Institutional investor "fear gauge" naming originated here
- **Relevance to GTOS:** VIX is a candidate K54 feature for risk-on/risk-off regime classification. NDX has its own VXN; correlation of VIX-VXN provides cross-index signal.
- **Potential hypothesis:** When VIX > 25 and trending up, NAS100 LONG setups underperform their backtest baseline by ≥5pp WR (consistent with regime-conditioned LONG-side decay observed in F2/F15).
- **Cross-domain links:** 16, 03
- **index_studied:** SPX/VIX

### Hedge Funds and the Technology Bubble
- **Authors:** Markus K. Brunnermeier, Stefan Nagel
- **Year:** 2004
- **Source:** Journal of Finance, Vol. 59(5), pp. 2013-2040
- **URL:** https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.2004.00690.x
- **Abstract:** Documents that hedge funds did not act as a stabilizing force during the 1998-2000 tech bubble; instead, they rode it heavily tilted toward overvalued tech stocks. Reduced exposure before the crash, capturing upside but avoiding much downside. Refutes EMH-style "rational arbitrageurs always stabilize."
- **Key findings:**
  - Hedge funds heavily long tech 1998-2000
  - Predictable investor sentiment + limits to arbitrage make riding bubbles rational
  - Smart money exits before crash, not at peak
  - Crowded trades unwind faster than they form
  - NDX-relevant: NAS100 is structurally tech-tilted
- **Relevance to GTOS:** NAS100 mega-cap concentration creates similar regime risk. Cross-instrument correlation gate may need NDX-specific volatility-regime conditioning during bubble-like regimes.
- **Potential hypothesis:** When NDX 30-day RV exceeds SPX 30-day RV by ≥1.5×, NAS100 LONG-side setups experience higher tail-loss frequency (regime characterized by speculative excess + limits-to-arbitrage breakdown).
- **Cross-domain links:** 17, 22
- **index_studied:** NDX (tech bubble concentration)

### A Closed-Form Solution for Options with Stochastic Volatility
- **Authors:** Steven L. Heston
- **Year:** 1993
- **Source:** Review of Financial Studies, Vol. 6(2), pp. 327-343
- **URL:** https://www.jstor.org/stable/2962057
- **Abstract:** Introduces the Heston stochastic-volatility option-pricing model with closed-form European call solution. Volatility follows a mean-reverting CIR process with possible correlation to the spot. Becomes the practitioner workhorse for SPX option pricing.
- **Key findings:**
  - Closed-form European option price under stochastic vol
  - Mean-reverting variance (CIR process)
  - Correlation between spot and vol drives skew
  - Captures volatility clustering
  - Widely calibrated to SPX options
- **Relevance to GTOS:** Foundational for any K54 feature based on option-implied moments. Indirect for trading-side, but essential for understanding what "expected volatility" means.
- **Potential hypothesis:** Heston-implied variance over realized variance ratio (signed proxy for VRP) predicts NDX 1-day forward returns positively at the 80th percentile.
- **Cross-domain links:** 01, 16
- **index_studied:** SPX (model class)

### A Closed-Form GARCH Option Valuation Model
- **Authors:** Steven L. Heston, Saikat Nandi
- **Year:** 2000
- **Source:** Review of Financial Studies, Vol. 13(3), pp. 585-625
- **URL:** https://academic.oup.com/rfs/article-abstract/13/3/585/1576522
- **Abstract:** Develops a closed-form option-pricing formula with a GARCH(p,q) variance process correlated with returns. Substantially outperforms Black-Scholes for SPX even when BS is updated each period and GARCH is held fixed. Captures negative skew via leverage effect.
- **Key findings:**
  - Closed-form European option under GARCH variance
  - Outperforms BS on SPX index options
  - Captures skew through leverage correlation
  - Continuous-time limit is Heston (1993)
  - Negative correlation between vol and returns is the key
- **Relevance to GTOS:** Background — informs the "asymmetric vol" feature class. Useful for understanding why NDX puts are persistently expensive.
- **Potential hypothesis:** N/A (foundational pricing-model paper, not a trading hypothesis)
- **Cross-domain links:** 01, 16
- **index_studied:** SPX

### The Limits of Arbitrage
- **Authors:** Andrei Shleifer, Robert W. Vishny
- **Year:** 1997
- **Source:** Journal of Finance, Vol. 52(1), pp. 35-55
- **URL:** https://onlinelibrary.wiley.com/doi/10.1111/j.1540-6261.1997.tb03807.x
- **Abstract:** Argues that real-world arbitrage requires capital and is risky, and is conducted by a small number of specialists using OPM. When prices diverge from fundamentals, arbitrageurs can become MORE constrained, not less. Mispricings can persist.
- **Key findings:**
  - Arbitrage is not free / riskless in practice
  - Performance-based capital flows out exactly when needed
  - Mispricings amplify during stress
  - Institutional setup creates "wrong-way" capital dynamics
  - Foundational for behavioral asset-pricing
- **Relevance to GTOS:** Theoretical underpinning for why dealer-flow mispricings (gamma-driven NDX moves) can persist and even amplify intraday — arbitrageurs can't always reverse them. Connects to F15 regime-conditioned decay.
- **Potential hypothesis:** When equity put protection is concentrated and dealer short-gamma exposure is large, NDX intraday momentum (last-30-min following first-30-min) is amplified.
- **Cross-domain links:** 17, 22
- **index_studied:** multi

### Information in Option Volume for Future Stock Prices
- **Authors:** Jun Pan, Allen M. Poteshman
- **Year:** 2006
- **Source:** Review of Financial Studies, Vol. 19(3), pp. 871-908
- **URL:** https://academic.oup.com/rfs/article-abstract/19/3/871/1646711
- **Abstract:** Constructs put-call ratios from option volume initiated by buyers to open new positions, using CBOE data. Stocks with low put-call ratios outperform stocks with high put-call ratios by ≥40 bp the next day and ≥1% over a week. Source is non-public information held by option traders.
- **Key findings:**
  - Initiated put-call ratio is highly predictive
  - 40 bp next-day, 100 bp next-week
  - Predictability sourced from informed-trader signal
  - Public option volume far less predictive than initiated volume
  - Effect persists over multi-week horizons
- **Relevance to GTOS:** Suggests option-volume-based features could be valuable. Limitation: GTOS does not have buyer-initiated option-flow data; only public option volume. K54 v2 may use OI changes as a coarse proxy.
- **Potential hypothesis:** Days where NDX index option PCR (open-interest-weighted) is in the lowest decile precede positive NAS100 returns the next day with WR > 55%.
- **Cross-domain links:** 13, 16
- **index_studied:** multi (extends to indices)

### Deviations from Put-Call Parity and Stock Return Predictability
- **Authors:** Martijn Cremers, David Weinbaum
- **Year:** 2010
- **Source:** Journal of Financial and Quantitative Analysis, Vol. 45(2), pp. 335-367
- **URL:** https://www.cambridge.org/core/journals/journal-of-financial-and-quantitative-analysis/article/abs/deviations-from-putcall-parity-and-stock-return-predictability/D9BA8F97580328AAFD7988B092FE5D50
- **Abstract:** Difference in implied vol between matched call/put pairs predicts future stock returns. Stocks with relatively expensive calls outperform those with relatively expensive puts by 50 bp/week. Effect amplifies under high option liquidity + low stock liquidity, asymmetric information, weak analyst coverage.
- **Key findings:**
  - 50 bp/week long-short return on call-put IV spread
  - Effect strongest in asymmetric-info environments
  - Decreases over sample period (mispricing arb-ed away)
  - Informed traders prefer options before stock incorporates info
  - Robust to standard factor models
- **Relevance to GTOS:** Sets a microstructure prior — option-implied direction-pressure leaks into spot returns. Could inform K54 feature: ATM call-put IV difference for NDX as a 1-day predictor.
- **Potential hypothesis:** Daily NDX ATM (50Δ) call IV minus put IV in the top quintile predicts a positive next-day NAS100 return with statistical significance (replication on indices, not single names).
- **Cross-domain links:** 13, 16
- **index_studied:** multi

### Expected Stock Returns and Variance Risk Premia
- **Authors:** Tim Bollerslev, George Tauchen, Hao Zhou
- **Year:** 2009
- **Source:** Review of Financial Studies, Vol. 22(11), pp. 4463-4492
- **URL:** https://academic.oup.com/rfs/article-abstract/22/11/4463/1565787
- **Abstract:** The variance risk premium (VRP) — implied minus realized variance — predicts a non-trivial fraction of post-1990 aggregate stock returns. Strong predictability at the quarterly horizon, dominating P/E, default spread, CAY. Theoretical basis: Epstein-Zin agent + stochastic volatility + vol-of-vol.
- **Key findings:**
  - VRP explains 15%+ of quarterly excess return variation
  - Strongest at intermediate (1-3 month) horizons
  - Model-free implied volatility critical (not Black-Scholes IV)
  - High-frequency realized variance critical
  - Dominates traditional predictors (P/E, default spread, CAY)
- **Relevance to GTOS:** Establishes VRP as a strong index-return predictor. **K54 candidate feature:** VRP of S&P (and analogous for NDX/DJI from VXN/VXD if available).
- **Potential hypothesis:** When daily VRP (proxy: VIX² minus realized variance forecast) is in top quintile, NAS100 LONG setups in following 5 days achieve higher WR than baseline.
- **Cross-domain links:** 16, 03
- **index_studied:** SPX

### Stock Return Predictability and Variance Risk Premia: Statistical Inference and International Evidence
- **Authors:** Tim Bollerslev, James Marrone, Lai Xu, Hao Zhou
- **Year:** 2014
- **Source:** Journal of Financial and Quantitative Analysis, Vol. 49(3), pp. 633-661
- **URL:** https://www.federalreserve.gov/econres/feds/stock-return-predictability-and-variance-risk-premia-statistical-inference-and-international-evidence.htm
- **Abstract:** Confirms VRP predictability via finite-sample-corrected statistical inference and extends to seven additional countries (DE, FR, JP, CH, NL, BE, UK). Country-specific results parallel US; a "global" VRP delivers even stronger predictability via panel regressions.
- **Key findings:**
  - VRP predictability not a finite-sample artifact
  - Country-specific VRPs all predictive
  - Global VRP outperforms country-specific
  - 2-4 month horizons strongest
  - Robust to multiple test corrections
- **Relevance to GTOS:** Validates international export of VRP signal. Useful as a backbone of K54 cross-asset risk-regime classification.
- **Potential hypothesis:** Global VRP combined with US VRP predicts NAS100 short-horizon returns better than US VRP alone.
- **Cross-domain links:** 16, 13
- **index_studied:** multi (international)

### Tails, Fears and Risk Premia
- **Authors:** Tim Bollerslev, Viktor Todorov
- **Year:** 2011
- **Source:** Journal of Finance, Vol. 66(6), pp. 2165-2211
- **URL:** https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.2011.01695.x
- **Abstract:** Decomposes the variance risk premium into a "diffusive" part and a "jump-tail" part using high-frequency intraday returns and short-maturity OTM SPX options. Jump-tail component is the locus of compensation for crash fears. Constructs an "Investor Fears Index" capturing time-varying disaster premium.
- **Key findings:**
  - Most of equity / variance risk premium attributable to jump-tail
  - "Fears Index" strongly time-varying
  - Identifies regimes of heightened crash anticipation
  - Realized vol of vol, jump tail well-separated
  - Strong predictability of returns from jump-tail premium
- **Relevance to GTOS:** Crash-premium signals can flag regimes where SHORT setups on NAS100 are more rewarded; LONG setups face skew tail risk.
- **Potential hypothesis:** When Investor Fears Index (or proxy: SKEW index above 145) is elevated, NAS100 SHORT setups outperform their backtest WR by ≥5pp.
- **Cross-domain links:** 16, 03, 17
- **index_studied:** SPX

### Tail Risk Premia and Return Predictability
- **Authors:** Tim Bollerslev, Viktor Todorov, Lai Xu
- **Year:** 2015
- **Source:** Journal of Financial Economics, Vol. 118(1), pp. 113-134
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S0304405X15001269
- **Abstract:** Extends Bollerslev-Todorov 2011 by demonstrating that the jump-tail risk premium predicts aggregate market returns better than the total VRP, especially at short horizons. Most of the original VRP predictability is concentrated in the jump-tail piece.
- **Key findings:**
  - Jump-tail premium → strong return predictor
  - Diffusive premium → weak predictor
  - Short-horizon predictability stronger than full VRP
  - Linked to investor fears
  - Robust across alternative tail estimators
- **Relevance to GTOS:** Refines K54 feature design — use jump-tail-decomposed VRP rather than total VRP.
- **Potential hypothesis:** Short-horizon NAS100 reversals during quiet regimes are best timed using jump-tail premium thresholds, not VIX or total VRP.
- **Cross-domain links:** 16, 03
- **index_studied:** SPX

### Noise as Information for Illiquidity
- **Authors:** Grace Xing Hu, Jun Pan, Jiang Wang
- **Year:** 2013
- **Source:** Journal of Finance, Vol. 68(6), pp. 2341-2382
- **URL:** https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.12083
- **Abstract:** Constructs a market-wide liquidity measure from yield-curve "noise" in U.S. Treasuries — when arb capital is scarce, deviations grow. Strongly correlated with VIX (R²≈12%). Captures flight-to-quality + liquidity-crisis episodes.
- **Key findings:**
  - Noise measure proxies arbitrage-capital scarcity
  - Strongly correlated with VIX, especially in crises
  - Predicts hedge-fund + carry-trade returns
  - Extends to JGB market in follow-up work
  - Captures liquidity beyond traditional proxies
- **Relevance to GTOS:** Cross-asset liquidity risk regime → flag for index trades. K54 v2 feature: HPW noise measure (or simpler proxy: TED spread, MOVE index) as risk-on/off classifier.
- **Potential hypothesis:** Days when HPW noise > 90th percentile coincide with NAS100 LONG-side WR collapse (similar mechanism to F2/F15 LONG decay).
- **Cross-domain links:** 11, 13, 21
- **index_studied:** multi (cross-asset)

### Modeling and Forecasting Realized Volatility
- **Authors:** Torben G. Andersen, Tim Bollerslev, Francis X. Diebold, Paul Labys
- **Year:** 2003
- **Source:** Econometrica, Vol. 71(2), pp. 579-625
- **URL:** https://onlinelibrary.wiley.com/doi/abs/10.1111/1468-0262.00418
- **Abstract:** Develops the framework for using high-frequency intraday returns to construct unbiased realized-volatility estimators. Demonstrates that returns standardized by RV are approximately Gaussian, log-RV is approximately Gaussian, and long-memory dynamics are well-captured by ARFIMA.
- **Key findings:**
  - RV is asymptotically free of measurement error
  - log-RV approximately Gaussian
  - Long-memory in volatility is robust
  - ARMA-based forecasts compete with sophisticated GARCH
  - 5-min sampling frequency optimal trade-off
- **Relevance to GTOS:** Direct relevance to any K54 feature using realized vol from M15/H1 data; provides theoretical basis for vol-feature engineering.
- **Potential hypothesis:** N/A (foundational methodology paper)
- **Cross-domain links:** 01, 03
- **index_studied:** SPX (and FX in companion work)

---

## 3. Dealer-gamma / pinning / OPEX

### Gamma Fragility
- **Authors:** Andrea Barbon, Andrea Buraschi
- **Year:** 2021 (revised; first posted 2020)
- **Source:** SSRN working paper / academic web (Univ. St. Gallen)
- **URL:** https://www.abarbon.com/assets/Barbon_Buraschi_2021_Gamma_Fragility.pdf
- **Abstract:** Documents that aggregate dealer gamma imbalances drive intraday momentum (when negative gamma) or mean-reversion (when positive gamma) in equity returns through delta-hedging feedback. Distinct from information / funding-liquidity frictions; depends on underlying-market liquidity.
- **Key findings:**
  - Negative dealer gamma + low liquidity → intraday momentum
  - Positive dealer gamma → mean-reversion
  - Mechanism is delta-hedging feedback
  - Dataset: equity options 2010-May 2020
  - Effect economically + statistically significant
- **Relevance to GTOS:** **Most directly cited GTOS-edge-relevant paper for NDX/SPX dealer-flow.** Directly motivates regime-aware K54: positive vs negative gamma regime classifier.
- **Potential hypothesis:** When proxy for NDX dealer gamma is negative (proxy: GEX < 0 from public estimators), NAS100 intraday breakouts continue at higher WR; when positive, breakouts mean-revert.
- **Cross-domain links:** 06, 16
- **index_studied:** multi (single-stock + extends to indices)

### Hedging Demand and Market Intraday Momentum
- **Authors:** Guido Baltussen, Zhi Da, Sten Lammers, Martin Martens
- **Year:** 2021
- **Source:** Journal of Financial Economics, Vol. 142(1), pp. 377-403
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S0304405X21001598
- **Abstract:** Documents persistent intraday momentum in last-30-min returns predicted by rest-of-day returns across 60+ futures (equities, bonds, commodities, currencies, 1974-2020). Mechanism: gamma hedging by option market makers + leveraged-ETF rebalancers. Effect economically significant; reverts over subsequent days.
- **Key findings:**
  - Last-30-min momentum present in 60+ futures, not just SPX
  - Gamma-hedging mechanism via dealers + LETFs
  - Reverts over subsequent days (not free lunch)
  - Robust 1974-2020 (45+ years)
  - Stronger when dealer net gamma is more negative
- **Relevance to GTOS:** **Direct evidence that NAS100 + US30 should exhibit last-30-min intraday momentum.** Critical for kill-zone calibration: NY close (16:00 ET = 20:00/21:00 UTC) is outside current US30 NY KZ but exactly the gamma-driven time. Consider extending US30 NY KZ end to 16:00 ET in observe mode.
- **Potential hypothesis:** Adding a 15:30-16:00 ET kill-zone for US30 / NAS100 with intraday-momentum filter (extends current 13:30-16:00 US30 NY KZ to capture last-30-min) yields incremental setups with WR comparable to current NY KZ.
- **Cross-domain links:** 14, 16, 06
- **index_studied:** multi (60+ futures)

### Where does gamma hedge drive the intraday market move?
- **Authors:** (AFA 2024 paper, multi-author)
- **Year:** 2024
- **Source:** AFA Annual Meeting 2024
- **URL:** https://afajof.org/management/viewp.php?n=129472
- **Abstract:** Recent AFA paper analyzing where in intraday SPX trading dealer gamma hedging dominates; refines Barbon-Buraschi by intra-day timing. Sequence of position-rebalancing windows mapped against price impact.
- **Key findings:**
  - Gamma-hedging impact concentrated in last-90-min
  - Magnitude conditional on dealer-gamma sign
  - Effect strongest on high-OI strikes
  - 0DTE growth amplifies intraday flows
  - Pinning intensifies in last hour
- **Relevance to GTOS:** Supplements Baltussen et al. with intra-day timing detail; informs NY KZ end-time tuning.
- **Potential hypothesis:** Confirmed dealer-gamma-impact concentrated in last-90-min suggests US30/NAS100 NY KZ end at 16:00 ET (not 16:30/17:00) captures the highest-edge window.
- **Cross-domain links:** 14, 16, 08
- **index_studied:** SPX

### 0DTEs: Trading, Gamma Risk and Volatility Propagation
- **Authors:** Chukwuma Dim, Bjorn Eraker, Grigory Vilkov
- **Year:** 2023
- **Source:** SSRN working paper
- **URL:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4692190
- **Abstract:** Studies the explosion in trading of zero-day-to-expiry (0DTE) SPX options. Market makers' net gamma is on average positive (i.e., end-users are net long 0DTEs). Positive net gamma → intraday reversal; negative → momentum. No unconditional propagation of 0DTE gamma into underlying volatility.
- **Key findings:**
  - 0DTE MM net gamma typically positive
  - Positive gamma → SPX intraday reversal
  - Negative gamma → SPX intraday momentum
  - No "0DTEs cause volatility" effect unconditionally
  - Conditional impact present in extreme regimes
- **Relevance to GTOS:** Sets boundary for NDX 0DTE worry. SPX-specific finding: 0DTEs do not increase volatility unconditionally. **Note:** NDX has weekly 0DTE-equivalent options (Mon/Wed/Fri NDX weeklies); literature is sparser.
- **Potential hypothesis:** When SPX 0DTE MM net gamma is in extreme negative quintile, NDX intraday momentum is amplified (correlation hypothesis).
- **Cross-domain links:** 16, 06
- **index_studied:** SPX

### 0DTE Index Options and Market Volatility: How Large is Their Impact?
- **Authors:** Diego Amaya, Pedro A. Garcia-Ares, Neil D. Pearson, Aurelio Vasquez
- **Year:** 2023-24
- **Source:** Cboe research publication
- **URL:** https://cdn.cboe.com/resources/education/research_publications/gammasqueezes.pdf
- **Abstract:** Estimates upper-bound impact of options market makers' (OMM) gamma on SPX index volatility using proprietary trade data + simulation. Average net gamma across all 0DTE expiries ranges 0.04%-0.17% of SPX futures daily liquidity — small relative to market depth.
- **Key findings:**
  - 0DTE OMM net gamma is small relative to liquidity
  - No discernible market impact under normal conditions
  - Tail-event impact possible but contained
  - SPX intraday vol patterns consistent with pre-0DTE era
  - Consistent with Dim-Eraker-Vilkov findings
- **Relevance to GTOS:** Tempers the "0DTE drives intraday" practitioner narrative for SPX; should also temper NDX worry.
- **Potential hypothesis:** No additive impact of 0DTE positioning beyond standard GEX → no NDX-specific 0DTE feature needed in K54 v1.
- **Cross-domain links:** 16, 06
- **index_studied:** SPX

### Liquidity Provision to Leveraged ETFs and Equity Options Rebalancing Flows: Evidence from End-of-Day Stock Prices
- **Authors:** Andrea Barbon, Heiner Beckmeyer, Andrea Buraschi, Mathis Moerke
- **Year:** 2022 (working paper)
- **Source:** SSRN working paper
- **URL:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3925725
- **Abstract:** Disentangles two distinct end-of-day rebalancing flows: leveraged-ETF rebalancing and option-dealer delta hedging. Both produce statistically significant end-of-day momentum / mean-reversion in returns. A 1σ increase in LETF rebalancing flow → 430% of mean last-30-min return.
- **Key findings:**
  - LETFs + option dealers BOTH source intraday momentum
  - Effects economically large at the margin
  - Mechanism mechanically distinct from information flow
  - Most pronounced last 30 min
  - Distinguishable LETF-flow from gamma-flow at end of day
- **Relevance to GTOS:** Reinforces last-30-min timing for NAS100/US30. Suggests LETF NDX (TQQQ, SQQQ) rebalancing flow should be modeled as a feature.
- **Potential hypothesis:** Adding a LETF-rebalancing-flow proxy (TQQQ AUM × NDX % daily change) improves K54 NAS100 last-30-min trade-quality classification.
- **Cross-domain links:** 14, 16, 13
- **index_studied:** multi

### No Max Pain, No Max Gain: A Case of Predictable Reversal
- **Authors:** Ilias Filippou, Pedro Angel Garcia-Ares, Fernando Zapatero
- **Year:** 2022 (revised 2024)
- **Source:** SSRN working paper
- **URL:** https://papers.ssrn.com/abstract=4140487
- **Abstract:** Tests Max Pain theory using U.S. equity options data. Finds strong empirical support: long-short portfolio strategies reversing toward Max Pain strike ahead of expiration generate significant excess risk-adjusted returns.
- **Key findings:**
  - Max Pain theory has empirical support post-controls
  - Excess returns from reversal strategy
  - Effect strongest in high-OI underlyings
  - Mechanism: dealer-hedging incentives align toward MP
  - Robust to standard factor models
- **Relevance to GTOS:** Direct support for using max-pain as a NAS100/SPX day-trading filter. K54 candidate feature: distance-to-max-pain on OPEX days.
- **Potential hypothesis:** When NAS100 spot is >2 ATR away from max-pain strike on OPEX day, mean-reversion-toward-MP is detectable in last 4 hours of trading.
- **Cross-domain links:** 09, 08
- **index_studied:** multi

### Program Trading and Individual Stock Returns: Ingredients of the Triple-Witching Brew
- **Authors:** Hans R. Stoll, Robert E. Whaley
- **Year:** 1987 (and 1991 update)
- **Source:** Journal of Financial Economics
- **URL:** https://www.researchgate.net/publication/24103078_Program_Trading_and_Individual_Stock_Returns_Ingredients_of_the_Triple-Witching_Brew
- **Abstract:** Foundational paper documenting expiration-day effects on US equity-index futures and individual stocks. Demonstrates "triple witching hour" abnormal volume + price-pressure effects driven by program trading + index arbitrage. Settlement-time changes (close vs open) alter volatility patterns.
- **Key findings:**
  - Triple-witching hour: significant abnormal volume + volatility
  - Program trading + index arb dominate flow
  - Settlement-time methodology matters for effect size
  - Effect partially dissipates with regulatory + structural changes
  - Foundational reference for OPEX-day microstructure
- **Relevance to GTOS:** Historical foundation for OPEX-day NAS100/US30 caution. Effect attenuated but not eliminated.
- **Potential hypothesis:** OPEX 3rd-Friday last-hour NDX setups (≥25% of monthly options volume) should be observed-only or risk-halved (similar to NAS100 3-day observe mode).
- **Cross-domain links:** 08, 09, 06
- **index_studied:** multi (S&P + DJIA + NYSE)

### The Derivative Payoff Bias
- **Authors:** Guido Baltussen, Julian Terstegge, Paul Whelan
- **Year:** 2024 (AFA paper)
- **Source:** AFA Annual Meeting 2024
- **URL:** https://afajof.org/management/viewp.php?n=98196
- **Abstract:** Documents a "derivative payoff bias" in OPEX-week returns: payoff structure of options creates systematic price pressure on expiration days that is not arbitraged away. Updates classic OPEX literature to post-0DTE era.
- **Key findings:**
  - OPEX-week + day systematic returns
  - Driven by payoff-structure of expiring options
  - Modern markets (post-2020) still exhibit effect
  - Predictable timing window
  - Robust to typical confounders
- **Relevance to GTOS:** Confirms OPEX-day filter is still warranted post-0DTE. Validates conservative treatment of OPEX days for NAS100/US30 trading.
- **Potential hypothesis:** OPEX-day setups (3rd Friday) on NAS100/US30 underperform mid-month-Friday setups by ≥10pp WR.
- **Cross-domain links:** 08, 09, 16
- **index_studied:** SPX (extends to NDX/DJI)

### Liquidity Provision to Leveraged ETFs and Equity Options Rebalancing Flows
- **Authors:** Andrea Barbon, Heiner Beckmeyer, Andrea Buraschi, Mathis Moerke
- **Year:** 2024 (extended version)
- **Source:** Swiss Finance Institute Research Paper Series RP 22-40
- **URL:** https://ideas.repec.org/p/chf/rpseri/rp2240.html
- **Abstract:** Extended treatment establishing that two distinct flows — leveraged ETF rebalancing and option-dealer delta hedging — are economically significant sources of end-of-day liquidity demand and induce both end-of-day momentum and mean-reversion patterns.
- **Key findings:**
  - Distinct LETF + option-dealer flows
  - Both economically large
  - Drive last-30-min predictability
  - Stable mechanism over multi-decade sample
  - Quantifies cumulative price impact
- **Relevance to GTOS:** Companion to the prior entry; confirms LETF-flow + dealer-flow as separable drivers. K54 should encode both.
- **Potential hypothesis:** Days with high LETF-rebalancing-needs in NDX (large NDX move + large TQQQ/SQQQ AUM) precede NAS100 last-30-min momentum-extension above baseline.
- **Cross-domain links:** 14, 16, 13
- **index_studied:** multi

---

## 4. VIX / vol risk premium / fear

### VIX Term Structure Forecasting: New Evidence Based on the Realized Semi-Variances
- **Authors:** Gaoxiu Qiao, Gongyue Jiang, Jiyu Yang
- **Year:** 2022
- **Source:** International Review of Financial Analysis, Vol. 82
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S1057521922001600
- **Abstract:** Proposes a discrete-time RV-ud-GARCH model that decomposes realized variance into upside and downside semi-variances and uses both to forecast the VIX term structure. Improves forecasting accuracy across short-, medium-, and long-end of the curve.
- **Key findings:**
  - Asymmetric realized semi-variances improve VIX TS forecasts
  - Downside semi-variance dominant in stress regimes
  - Forecasts beat single-RV benchmarks
  - Applies to multiple maturities simultaneously
  - High-frequency data essential
- **Relevance to GTOS:** K54 feature: VIX term-structure slope (M1 - M3) as a regime classifier; can be backfilled cheaply.
- **Potential hypothesis:** When VIX term structure is in deep backwardation (M1>M3), NAS100/US30 LONG setups underperform vs contango regime by ≥8pp WR.
- **Cross-domain links:** 16, 03
- **index_studied:** VIX

### Forecasting VIX Using Two-Component Realized EGARCH Model
- **Authors:** Xinyu Wu, An Zhao, Li Liu
- **Year:** 2023
- **Source:** North American Journal of Economics and Finance, Vol. 67
- **URL:** https://ideas.repec.org/a/eee/ecofin/v67y2023ics1062940823000578.html
- **Abstract:** Two-component realized EGARCH model accommodating high-frequency information + long-memory through component-volatility structure. Derives the model-implied VIX. Improves on standard realized-EGARCH forecasts in out-of-sample tests.
- **Key findings:**
  - Long-memory + asymmetry both matter
  - Component vol structure key
  - Best for short-horizon VIX forecasts
  - Outperforms HAR-RV-VIX
  - Robust to sample partitioning
- **Relevance to GTOS:** Methodological background for any VIX-feature engineering. Operational use limited (model complex), but informs feature selection (use both fast + slow vol components).
- **Potential hypothesis:** N/A (methodology paper)
- **Cross-domain links:** 16, 03
- **index_studied:** VIX

### VIX and Stock Market Volatility Predictability: A New Approach
- **Authors:** (per ScienceDirect indexing)
- **Year:** 2022
- **Source:** Finance Research Letters, Vol. 50
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S1544612322001696
- **Abstract:** Develops a new prediction approach combining VIX with realized volatility for S&P 500 volatility forecasting. Demonstrates that VIX-conditioning improves out-of-sample volatility forecasts particularly during regime shifts.
- **Key findings:**
  - VIX-conditioned RV forecasts beat univariate
  - Most useful in regime-change periods
  - Performs well during 2020 COVID stress
  - Cross-validation across decades
  - Practical implementation for backtesting
- **Relevance to GTOS:** Strong support for using VIX as a regime-conditioning input rather than predicting raw volatility from history alone.
- **Potential hypothesis:** Conditioning K54 NAS100 trading on (VIX level, VIX delta-1d, RV-30d) jointly improves trade-quality classification beyond using any single one.
- **Cross-domain links:** 16, 19
- **index_studied:** SPX/VIX

### A New Star Is Born: Does the VIX1D Render Common Volatility Forecasting Models for the US Equity Market Obsolete?
- **Authors:** Albers et al.
- **Year:** 2025
- **Source:** Journal of Futures Markets
- **URL:** https://onlinelibrary.wiley.com/doi/full/10.1002/fut.70023
- **Abstract:** Evaluates whether VIX1D (CBOE 1-day VIX) renders longer-horizon vol forecasting models obsolete. Finds VIX1D adds short-horizon forecasting power particularly for 1-day-ahead, but predictive content decays faster than longer-horizon VIX.
- **Key findings:**
  - VIX1D improves 1-day forecasts
  - Decay faster than VIX, VIX9D
  - Overnight bias in raw VIX1D
  - HAR-RV-VIX1D dominates HAR-RV-VIX at 1-day horizon
  - Methodology adjustments needed for raw VIX1D
- **Relevance to GTOS:** VIX1D could be a same-day NAS100/US30 risk-regime feature for K54. Operational complication: VIX1D needs overnight-bias correction.
- **Potential hypothesis:** VIX1D-VIX9D spread (1d minus 9d implied vol) is a contemporaneous regime classifier — large spreads (>3σ from average) correspond to acute crisis regimes where NDX directional setups are degraded.
- **Cross-domain links:** 16
- **index_studied:** VIX

### The Daily Rise and Fall of the VIX1D: Causes and Solutions of Its Overnight Bias
- **Authors:** (per ScienceDirect indexing)
- **Year:** 2024
- **Source:** Finance Research Letters, Vol. 62
- **URL:** https://www.sciencedirect.com/science/article/pii/S1544612324002162
- **Abstract:** Decomposes the systematic intraday rise + overnight fall pattern in VIX1D. Shows that "business-time" vs "calendar-time" methodology + dynamic weighting of next-term options causes overnight-variance-premium bias. Proposes corrections.
- **Key findings:**
  - VIX1D has predictable intraday + day-of-week pattern
  - Bias mechanically tied to construction methodology
  - Overnight VRP embedded in raw VIX1D
  - Corrected VIX1D more useful for forecasting
  - Day-of-week effect substantial
- **Relevance to GTOS:** Operational caveat — raw VIX1D should not be used as feature without bias correction.
- **Potential hypothesis:** Raw VIX1D feature (uncorrected) introduces systematic bias into K54 day-of-week model; corrected version eliminates this.
- **Cross-domain links:** 16
- **index_studied:** VIX

### Volatility Forecasting with Machine Learning and Intraday Commonality
- **Authors:** (Journal of Financial Econometrics 2024)
- **Year:** 2024
- **Source:** Journal of Financial Econometrics, Vol. 22(2), pp. 492+
- **URL:** https://academic.oup.com/jfec/article/22/2/492/7081291
- **Abstract:** Uses ML methods (random forest, neural nets) to forecast intraday volatility for cross-section of stocks. Documents commonality in intraday volatility patterns. Identifies time-of-day and volume effects as the dominant ML features.
- **Key findings:**
  - ML beats HAR-RV out-of-sample
  - Intraday volatility commonality high cross-section
  - Volume + time-of-day dominate features
  - U-shape diurnal pattern persistent
  - Random forest > neural net for this problem
- **Relevance to GTOS:** Methodology for K54 feature engineering. Validates using time-of-day + volume as feature; volume features are mostly absent from current GTOS feature set.
- **Potential hypothesis:** Adding intraday-time-of-day-bucket × volume feature to K54 lifts AUC by ≥0.02.
- **Cross-domain links:** 19, 03, 14
- **index_studied:** multi

### Volmageddon and the Failure of Short Volatility Products
- **Authors:** Patrick Augustin, Ing-Haw Cheng, Ludovic Van den Bergen
- **Year:** 2021
- **Source:** Financial Analysts Journal, Vol. 77(3), pp. 35-51
- **URL:** https://rpc.cfainstitute.org/research/financial-analysts-journal/2021/volmageddon-failure-short-volatility-products
- **Abstract:** Analyzes the February 5, 2018 short-volatility blowup that destroyed XIV/SVXY. Mechanism: short-vol ETPs forced to cover via VIX futures purchases, creating a feedback loop. Volume spike to 115k VIX futures contracts in single minute at 16:08.
- **Key findings:**
  - XIV/SVXY net short ~280k VIX futures pre-event
  - Mechanical rebalancing → feedback loop
  - 115k contracts in 1 min at 16:08 ET
  - Short-vol products structurally fragile
  - Lessons for systematic short-vol strategies
- **Relevance to GTOS:** Tail-risk-regime warning — when VIX trades up rapidly (>50%/day), expect feedback flow that magnifies SPX/NDX move beyond fundamental information. Risk-gate trigger.
- **Potential hypothesis:** Days with VIX up >25% (intraday) → halve risk on directional NAS100 setups due to feedback loops potentially still active.
- **Cross-domain links:** 16, 21
- **index_studied:** VIX

---

## 5. Intraday momentum / mean reversion / overnight-vs-intraday

### Intraday Momentum: The First Half-Hour Return Predicts the Last Half-Hour Return
- **Authors:** Lei Gao, Yufeng Han, Sophia Zhengzi Li, Guofu Zhou
- **Year:** 2018 (originally 2015 working paper)
- **Source:** Journal of Financial Economics, Vol. 129(2), pp. 394-414
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S0304405X18301351
- **Abstract:** Documents that the first 30-min return on SPY (and 10 other actively-traded ETFs) predicts the last 30-min return. Stronger on volatile, high-volume, recession, and macro-news days. Simple long/short market-timing yields 6.67%/year, beating buy-and-hold (6.04%) on a Sharpe basis.
- **Key findings:**
  - First-30-min ⇒ last-30-min predictive
  - Effect across SPY, DIA, QQQ, IWM, etc.
  - Stronger on macro-news days (FOMC, CPI)
  - Mechanism: daytraders + informed traders
  - 6.67% annual return on simple timing strategy
- **Relevance to GTOS:** **Direct evidence that NAS100, US30 should exhibit first-30-min/last-30-min predictability.** First 30 min after London open + first 30 min after NY open = key predictive windows. Connects to GTOS kill-zone design.
- **Potential hypothesis:** First 30-min NAS100 return after NY open predicts last 30-min direction with WR ≥55% (replicate Gao et al. on NAS100 specifically).
- **Cross-domain links:** 14, 06, 17
- **index_studied:** multi (SPY + 10 ETFs)

### A Tug of War: Overnight Versus Intraday Expected Returns
- **Authors:** Dong Lou, Christopher Polk, Spyros Skouras
- **Year:** 2019
- **Source:** Journal of Financial Economics, Vol. 134(1), pp. 192-213
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S0304405X19300650
- **Abstract:** Documents strong firm-level return continuation overnight + intraday separately, with offsetting cross-period reversal. Profits on momentum/reversal strategies are entirely overnight or entirely intraday — typically opposite signs across periods.
- **Key findings:**
  - Overnight + intraday returns highly distinct
  - Cross-period reversal strong
  - Strategies separate cleanly into overnight vs intraday
  - Effect pervasive across strategies
  - Suggests separate liquidity / investor pools at each session
- **Relevance to GTOS:** GTOS trades intraday only; the overnight component is missed. Suggests carry-cost-adjusted overnight gap should be a feature for K54 (NDX last-night close - this morning open as a regime input).
- **Potential hypothesis:** Days with large overnight NAS100 gaps (|gap| > 0.5%) precede directional intraday following the overnight (continuation), while gaps are mean-reverted on the next overnight.
- **Cross-domain links:** 14, 17, 13
- **index_studied:** multi (cross-section equity + ETFs)

### Beat the Market: An Effective Intraday Momentum Strategy for S&P 500 ETF (SPY)
- **Authors:** Carlo Zarattini, Andrew Aziz, Andrea Barbon
- **Year:** 2024
- **Source:** SSRN working paper
- **URL:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4824172
- **Abstract:** Develops a SPY-specific intraday-momentum strategy using opening-range breakout + dynamic position sizing. Backtests show Sharpe 2.396 vs SPY buy-and-hold 0.836. Authors provide concrete trade rules.
- **Key findings:**
  - SPY ORB + dynamic sizing outperforms buy-and-hold
  - Sharpe 2.396 vs 0.836
  - Pre-2020 data primarily; post-2020 effect attenuated
  - Practical implementation rules disclosed
  - Robust across various filters
- **Relevance to GTOS:** Concrete practitioner-academic strategy template that could inform NAS100/US30 first-30-min entry rules.
- **Potential hypothesis:** Adapting Zarattini et al.'s SPY ORB to NAS100 with regime-conditioning (VIX, time-of-day) yields incremental positive expectancy.
- **Cross-domain links:** 14, 06
- **index_studied:** SPX

### A Profitable Day Trading Strategy For The U.S. Equity Market
- **Authors:** Carlo Zarattini, Andrea Barbon, Andrew Aziz
- **Year:** 2024
- **Source:** SSRN working paper
- **URL:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4729284
- **Abstract:** Cross-section "Stocks in Play" 5-min ORB strategy; long short across top-20 high-activity stocks. 1,600% total net return; Sharpe 2.81; 36% annualized alpha. 2016-2023 sample.
- **Key findings:**
  - 5-min ORB on selected high-activity stocks works
  - Sharpe 2.81; alpha 36%
  - Stocks-in-Play filter critical
  - Post-cost robust
  - Authors disclose all rules
- **Relevance to GTOS:** Cross-validation of opening-range concept. NAS100/US30 are passive-flow-driven indices — adapt rules differently.
- **Potential hypothesis:** Index-level ORB on NAS100 in NY session yields positive (lower magnitude) edge after costs.
- **Cross-domain links:** 14, 06, 13
- **index_studied:** multi

### Assessing the Profitability of Timely Opening Range Breakout on Index Futures Markets
- **Authors:** (per IEEE indexing)
- **Year:** 2019
- **Source:** IEEE Access
- **URL:** https://ieeexplore.ieee.org/document/8641124
- **Abstract:** Tests Timely Opening Range Breakout (TORB) strategies on DJIA, S&P 500, NASDAQ, HSI, TAIEX index futures using 1-min intraday data 2003-2013. >8% annual return, p-value <3% in all five markets. Robust to commission costs.
- **Key findings:**
  - TORB profitable in 5/5 indices including DJIA, NDX
  - >8% annual return, p<0.03
  - Robust to commission
  - 1-min granularity matters
  - Effect attenuates over decade
- **Relevance to GTOS:** **Empirical validation of opening-range mechanics on US30 (DJIA) + NAS100 specifically**. K54 should consider time-since-NY-open as a feature.
- **Potential hypothesis:** Adapting TORB to GTOS NAS100 entry rules with appropriate filtering improves NAS100 setup quality.
- **Cross-domain links:** 14, 06
- **index_studied:** multi (DJIA + NDX)

---

## 6. Event days / FOMC / CPI / earnings

### The Pre-FOMC Announcement Drift
- **Authors:** David O. Lucca, Emanuel Moench
- **Year:** 2015 (Federal Reserve Staff Report 2011)
- **Source:** Journal of Finance, Vol. 70(1), pp. 329-371
- **URL:** https://www.newyorkfed.org/research/staff_reports/sr512.html
- **Abstract:** Documents that S&P 500 returns in 24-hour pre-FOMC window average +49 bp, accounting for ~half of total realized excess equity returns 1980-2011. Effect does not revert. Higher when yield curve flat, IV high, past pre-FOMC returns elevated.
- **Key findings:**
  - +49 bp/24-hour pre-FOMC drift
  - Half of total excess returns came from pre-FOMC days
  - Most concentrated in last few hours pre-announcement
  - Stronger when VIX is high
  - No reversal post-announcement
- **Relevance to GTOS:** **Strong directional bias on FOMC days affects NAS100/US30 trading.** GTOS should have an FOMC-day filter or risk-on bias. (Note: caveat below in "disappearing drift" paper.)
- **Potential hypothesis:** NAS100 LONG setups in 4-hour pre-FOMC window outperform baseline by ≥10pp WR.
- **Cross-domain links:** 11, 17
- **index_studied:** SPX

### The Disappearing Pre-FOMC Announcement Drift
- **Authors:** Vasiliki Plagianakos, et al.
- **Year:** 2020
- **Source:** Economics Letters, PMC NIH index
- **URL:** https://pmc.ncbi.nlm.nih.gov/articles/PMC7525326/
- **Abstract:** Documents that the pre-FOMC announcement drift originally identified by Lucca-Moench essentially disappeared after 2015. Holds whether or not the FOMC had a press conference scheduled.
- **Key findings:**
  - Pre-FOMC drift gone post-2015
  - Affects both press-conference and non-press FOMC days
  - Effect possibly arbitraged away
  - Or shifted to different timing window
  - Revisits Lucca-Moench
- **Relevance to GTOS:** **Caveat to prior paper.** Modern GTOS should NOT assume pre-FOMC drift; instead, treat FOMC as elevated-volatility risk event.
- **Potential hypothesis:** NAS100/US30 setups in any 24-hour FOMC window should be observed-only (or risk-halved) since drift gone but volatility elevated.
- **Cross-domain links:** 11, 17
- **index_studied:** SPX

### Asymmetric S&P 500 Reactions to CPI Surprises in a High-Inflation Environment
- **Authors:** (per Tandfonline indexing)
- **Year:** 2026 (forthcoming)
- **Source:** Applied Economics Letters
- **URL:** https://www.tandfonline.com/doi/full/10.1080/13504851.2026.2624038
- **Abstract:** Daily-frequency event study of S&P 500 reactions to CPI surprises in the 2021-2025 high-inflation regime. Positive surprises (CPI below expectations) generate +1%+ statistically significant abnormal returns; negative surprises produce similar-magnitude negative returns but lack statistical significance.
- **Key findings:**
  - Positive CPI surprise → strong S&P rally (>1%)
  - Negative surprise → directionally negative but noisy
  - Asymmetric reaction magnitudes
  - Strongest in 2021-2025 sample (high-inflation regime)
  - Event-study methodology validates causality
- **Relevance to GTOS:** **Direct relevance to NAS100/US30 CPI-day handling.** NAS100 reacts more strongly to CPI than US30 (consistent with practitioner observations). Risk gate at CPI release recommended.
- **Potential hypothesis:** CPI-day setups on NAS100 should be (a) observed-only in pre-release window or (b) risk-adjusted based on CPI surprise sign post-release.
- **Cross-domain links:** 11
- **index_studied:** SPX (extends to NDX)

### Volume Dynamics around FOMC Announcements
- **Authors:** (BIS Working Paper)
- **Year:** 2023
- **Source:** BIS Working Paper No. 1079
- **URL:** https://www.bis.org/publ/work1079.pdf
- **Abstract:** Documents systematic volume patterns around FOMC announcements: pre-event volume buildup, intra-event spike, post-event volume decay over 90 minutes. Mechanism: information absorption + position rebalancing.
- **Key findings:**
  - Pre-FOMC volume rises systematically
  - Intra-event spike sustained 90 min
  - Volume decay slow (hours)
  - Asset-class spillover (equities, bonds, FX)
  - Methodology useful for intraday volume engineering
- **Relevance to GTOS:** Operational guidance for FOMC-day execution; the 90-min absorption window is the high-vol period.
- **Potential hypothesis:** Trading NAS100/US30 in the 90 min post-FOMC release is unfavorable; setups should resume after this absorption window.
- **Cross-domain links:** 11, 08, 06
- **index_studied:** multi

### COVID-19 and the March 2020 Stock Market Crash. Evidence from S&P1500
- **Authors:** (per ScienceDirect / PMC indexing)
- **Year:** 2020
- **Source:** Finance Research Letters
- **URL:** https://www.sciencedirect.com/science/article/abs/pii/S1544612320306668
- **Abstract:** Analyzes S&P 1500 sector behavior in February-March 2020 COVID crash. Healthcare, software up; petroleum, real estate, entertainment, hospitality dramatically down. Loser stocks exhibit extreme asymmetric volatility negatively correlated with returns.
- **Key findings:**
  - Sector dispersion extreme during COVID crash
  - Software / healthcare resilience
  - Asymmetric volatility most pronounced in losers
  - VIX peaked at 83 (unprecedented)
  - Recovery uneven across sectors
- **Relevance to GTOS:** Crisis-regime case study; NAS100 (tech-heavy) exhibits different behavior from US30 (cyclical-heavy) in such regimes. Supports differential treatment.
- **Potential hypothesis:** When VIX > 50 and sector dispersion (proxy: TQQQ-DIA correlation) breaks down, NAS100 outperforms US30 by ≥15bp/day on average.
- **Cross-domain links:** 03, 17
- **index_studied:** SPX (extends to NDX/DJI)

---

## 7. Crashes / structural events / leverage effect

### The Microstructure of the 'Flash Crash': Flow Toxicity, Liquidity Crashes and the Probability of Informed Trading
- **Authors:** David Easley, Marcos M. López de Prado, Maureen O'Hara
- **Year:** 2011
- **Source:** Journal of Portfolio Management
- **URL:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1695041
- **Abstract:** Analyzes May 6, 2010 SPX/E-mini flash crash via VPIN (volume-synchronized probability of informed trading). Order-flow toxicity rose for hours/days before, predicting the liquidity crash. Provides early-warning measure.
- **Key findings:**
  - VPIN warned days in advance of flash crash
  - Order toxicity → liquidity crash mechanism
  - HFT withdrawal central
  - Asynchronous information critical
  - Generalizable to other flash events
- **Relevance to GTOS:** Crisis early-warning framework; VPIN-like measures could be K54 risk-regime classifier.
- **Potential hypothesis:** Days when SPX VPIN proxy is in 99th percentile precede NAS100 / US30 elevated tail-loss frequency.
- **Cross-domain links:** 06, 21
- **index_studied:** SPX

### The Flash Crash: High-Frequency Trading in an Electronic Market
- **Authors:** Andrei A. Kirilenko, Albert S. Kyle, Mehrdad Samadi, Tugkan Tuzun
- **Year:** 2017 (originally 2010)
- **Source:** Journal of Finance
- **URL:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1686004
- **Abstract:** Examines a large automated selling program in the E-mini SPX futures market that triggered the 2010 flash crash. HFT served as transient liquidity but withdrew when needed. Cross-market arbitrage propagated to cash equities.
- **Key findings:**
  - HFT central to mechanism
  - Large automated sell program triggered crash
  - HFT withdrew during stress
  - Cross-market propagation E-mini → cash → ETF
  - Liquidity essentially evaporated for 36 minutes
- **Relevance to GTOS:** Index futures (ES, NQ, YM) contain the propagation engine for flash crashes affecting cash NAS100/US30. Risk-of-ruin scenario.
- **Potential hypothesis:** Catastrophic-event detector (NAS100 or US30 -3% in <60 min) should automatically halt all directional setups for next 4 hours.
- **Cross-domain links:** 06, 21, 11
- **index_studied:** SPX (E-mini)

### Portfolio Insurance and Other Investor Fashions as Factors in the 1987 Stock Market Crash
- **Authors:** Robert Shiller
- **Year:** 1988
- **Source:** NBER Macroeconomics Annual, Vol. 3, pp. 287-297
- **URL:** https://www.nber.org/books-and-chapters/nber-macroeconomics-annual-1988-volume-3/portfolio-insurance-and-other-investor-fashions-factors-1987-stock-market-crash
- **Abstract:** Argues that portfolio insurance (delta-hedged equity protection) created a feedback loop in the October 1987 crash: initial price decline → portfolio insurer selling → further decline → further insurer selling. Foundational paper on systematic-strategy-induced crashes.
- **Key findings:**
  - Portfolio insurance mechanically pro-cyclical
  - Feedback loop: price ↓ → sell pressure ↑ → price ↓
  - Same mechanics as modern systematic vol-control / risk-parity strategies
  - 22.6% DJIA single-day drop
  - Foundational reference for systemic risk
- **Relevance to GTOS:** Macro-theoretical foundation for why dealer-gamma feedback loops matter; modern GEX-driven NDX moves are a smaller-scale analog.
- **Potential hypothesis:** When NDX intraday GEX flips from positive to negative within 60 min, expect feedback flow → momentum continuation, not mean reversion.
- **Cross-domain links:** 21, 22, 17
- **index_studied:** SPX/DJIA

---

## 8. ETF / index inclusion / structural

### ETF Arbitrage and Return Predictability
- **Authors:** David C. Brown, et al.
- **Year:** 2017 / 2021 (Review of Finance)
- **Source:** Review of Finance
- **URL:** https://revfin.org/etf-arbitrage-non-fundamental-demand-and-return-predictability/
- **Abstract:** ETF creations / redemptions lead to monthly return predictability for both underlying assets and ETFs themselves. Long-stocks-of-extreme-outflow-ETFs / short-extreme-inflow-ETFs strategy generates ~61 bp/month. Suggests significant non-fundamental demand drives ETF flows + returns.
- **Key findings:**
  - 61 bp/month long-short return on ETF flow signal
  - Non-fundamental demand drives ETF returns
  - Predicts both ETF + underlying
  - Robust across factor controls
  - Practical implementation discussed
- **Relevance to GTOS:** SPY, QQQ, DIA, IWM flows could be a NAS100/US30 K54 feature. Practical: daily ETF AUM change as a regime input.
- **Potential hypothesis:** Days following extreme QQQ inflow (>1σ above avg) precede NAS100 underperformance (mean-reversion of nonfundamental demand) by 50bp.
- **Cross-domain links:** 13, 21
- **index_studied:** multi

### The Disappearing Index Effect
- **Authors:** Robin Greenwood, Marco Sammon
- **Year:** 2024 (NBER Working Paper)
- **Source:** NBER Working Paper No. w30748
- **URL:** https://www.nber.org/system/files/working_papers/w30748/w30748.pdf
- **Abstract:** Documents that the long-known +3-4% index-inclusion abnormal return has essentially disappeared over the past decade. Median excess returns of S&P 500 additions fell from +8.3% (1995-99) to -0.04% (2011-21). Driver: better market liquidity for index changes + S&P MidCap migration patterns.
- **Key findings:**
  - Index-effect went from +8.3% to ~0%
  - 2011-2021 effectively no abnormal return
  - Liquidity provision improved
  - Migration from MidCap dilutes effect
  - Implication: many "anomalies" decay
- **Relevance to GTOS:** Cautionary tale about anomaly decay (relevant to F11 OB-zone-decay finding). Validates that backtest-derived edges erode.
- **Potential hypothesis:** N/A (cautionary, not a trade hypothesis)
- **Cross-domain links:** 22, 13
- **index_studied:** SPX

### Do ETFs Increase Volatility?
- **Authors:** Itzhak Ben-David, Francesco Franzoni, Rabih Moussawi
- **Year:** 2018
- **Source:** Journal of Finance, Vol. 73(6), pp. 2471-2535
- **URL:** https://jacobslevycenter.wharton.upenn.edu/wp-content/uploads/2014/06/Moussawi_Paper.pdf
- **Abstract:** Documents that stocks with greater ETF ownership exhibit higher intraday and daily volatility. Mechanism: ETF arbitrage trades transmit non-fundamental shocks from ETF prices to underlying stocks. Effect economically significant.
- **Key findings:**
  - Higher ETF ownership → higher stock volatility
  - Non-fundamental shocks propagate
  - Mechanism: arbitrage flows
  - Significant cross-sectional differences
  - QQQ / IWM ownership particularly impactful
- **Relevance to GTOS:** NAS100 stocks (high QQQ ownership) should exhibit higher volatility than DJIA stocks (DIA ownership lower). Justifies higher position-size restraint on NAS100.
- **Potential hypothesis:** NAS100 intraday vol per ATR move is structurally higher than US30 due to QQQ-arb propagation; K54 should normalize moves by index-specific vol.
- **Cross-domain links:** 03, 13
- **index_studied:** multi (with QQQ/SPY focus)

---

## 9. Volatility surface / skew / cross-section

### Predictable Dynamics in the S&P 500 Index Options Implied Volatility Surface
- **Authors:** (per JSTOR indexing)
- **Year:** 2007
- **Source:** Journal of Business, Vol. 80(4)
- **URL:** https://www.jstor.org/stable/10.1086/500686
- **Abstract:** Documents predictable patterns in the SPX IVS over time. Levels, slopes, and curvatures of IV across strikes and maturities exhibit autoregressive + cross-sectional dynamics that can be modeled.
- **Key findings:**
  - SPX IVS is autoregressive
  - Cross-sectional dependencies persistent
  - Predictable factor dynamics
  - Useful for option-pricing forecasts
  - Operates on weekly/monthly frequency
- **Relevance to GTOS:** SPX IV-skew dynamics could inform NDX as a feature; SPX-skew leads NDX-skew empirically.
- **Potential hypothesis:** SPX skew (25Δ put - 25Δ call IV) at end of day leads NDX directional return next day.
- **Cross-domain links:** 16, 03
- **index_studied:** SPX

### Pricing S&P 500 Index Put Options: Smiles, Skews, and Leverage
- **Authors:** (UCLA Anderson 08-07)
- **Year:** 2008
- **Source:** UCLA Anderson Working Paper
- **URL:** https://www.anderson.ucla.edu/documents/areas/fac/finance/08-07.pdf
- **Abstract:** Develops pricing model that captures SPX put-side volatility smile, term-structure skew, and leverage effect. Demonstrates that volatility-leverage correlation is the key driver of put-side smile.
- **Key findings:**
  - Leverage effect drives skew
  - Captures both term + strike dimension
  - SPX put-side persistently expensive
  - Monte Carlo validation
  - Practitioner-relevant calibration
- **Relevance to GTOS:** Background — explains why SPX/NDX put hedging is structurally expensive and drives dealer hedging asymmetry.
- **Potential hypothesis:** N/A (pricing model)
- **Cross-domain links:** 16
- **index_studied:** SPX

### S&P 100 Index Option Volatility
- **Authors:** Campbell R. Harvey, Robert E. Whaley
- **Year:** 1991
- **Source:** Journal of Finance, Vol. 46(4), pp. 1251-1261
- **URL:** https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.1991.tb04631.x
- **Abstract:** Foundational paper on extracting implied volatility from S&P 100 index options. Identifies serial-correlation biases from non-simultaneous option / index observation. Uses American-style option algorithm.
- **Key findings:**
  - IV extraction prone to non-simultaneity bias
  - American-option algorithm essential
  - Bid/ask quote effects induce spurious correlation
  - Foundation for VXO / VIX construction
  - Methodologically rigorous
- **Relevance to GTOS:** Methodology background for any option-implied feature.
- **Potential hypothesis:** N/A (methodology)
- **Cross-domain links:** 16
- **index_studied:** SPX (OEX)

---

## 10. Index-level extras

### NDX vs SPX Mega-Cap Concentration / Magnificent 7
- **Authors:** Various practitioner + S&P research
- **Year:** 2023-2024
- **Source:** Charles Schwab / S&P research notes
- **URL:** https://www.schwab.com/learn/story/every-breadth-you-take-market-concentration-risks
- **Abstract:** Mega-cap crowding in S&P 500 reached 86th percentile vs history. Magnificent 7 weight share grew dramatically; Mag 7 returned 101% in 2023 vs broader S&P. NDX dominated by these mega-caps; outperformed SPX by 23+pp in 2020 + 2023.
- **Key findings:**
  - Mag 7 dominates 2023 returns
  - NDX = mega-cap-tech-concentrated
  - Concentration creates regime-amplification risk
  - 2020 + 2023 NDX outperformance >23pp vs SPX
  - Concentration cycles: 2020-2024 unusual
- **Relevance to GTOS:** **NAS100 is structurally more concentrated than US30 / SPX.** This affects volatility, regime sensitivity, and gamma-flow concentration.
- **Potential hypothesis:** When SPX-NDX correlation breakdown is in top decile (sector rotation event), NAS100 directional setups face heightened reversal risk.
- **Cross-domain links:** 13, 22
- **index_studied:** NDX/SPX

### Day of the Week and the Cross-Section of Returns
- **Authors:** Justin Birru
- **Year:** 2018
- **Source:** Journal of Financial Economics, Vol. 130(1), pp. 182-214
- **URL:** https://www.aeaweb.org/conference/2017/preliminary/paper/fNkhhEd6
- **Abstract:** Documents day-of-week (DoW) effects in US equity returns. Despite weakening over time, certain DoW patterns persist, particularly for small-cap (Russell 2000 / NASDAQ Composite). Mechanism: investor-attention + news-flow timing.
- **Key findings:**
  - DoW effects persist for small-cap
  - Mid-week vs Monday/Friday spread
  - Investor-attention mechanism
  - Effect attenuated post-2000s
  - News-flow timing partly explanatory
- **Relevance to GTOS:** Day-of-week feature for K54.
- **Potential hypothesis:** NAS100 / US30 setups have differential WR by day-of-week; controlling for this in K54 lifts AUC.
- **Cross-domain links:** 13, 17
- **index_studied:** multi

### Index Options Open Interest and Stock Market Returns
- **Authors:** Sang-Hyun Seo
- **Year:** 2020
- **Source:** Journal of Futures Markets
- **URL:** https://onlinelibrary.wiley.com/doi/abs/10.1002/fut.22095
- **Abstract:** Documents that growth in index option open interest is significantly related to future stock market returns. Suggests open-interest changes carry informational content beyond price.
- **Key findings:**
  - OI growth predictive of stock returns
  - Mechanism: informed trader positioning
  - Effect cross-sample-stable
  - Operationally tractable feature
  - Direction of effect documented
- **Relevance to GTOS:** **K54 candidate feature: NDX index option total OI change (daily).**
- **Potential hypothesis:** Days following large NDX index option OI growth (>1σ above 30d avg) precede NAS100 directional moves consistent with put-call OI imbalance direction.
- **Cross-domain links:** 13, 16
- **index_studied:** multi

### S&P 500 Index Inclusion and Implied Volatility Skew
- **Authors:** Asli Eksi, Saurabh Roy
- **Year:** 2022
- **Source:** EFMA 2022 Annual Meeting paper
- **URL:** http://www.efmaefm.org/0EFMAMEETINGS/EFMA%20ANNUAL%20MEETINGS/2022-Rome/papers/EFMA%202022_stage-3032_question-Full%20Paper_id-329.pdf
- **Abstract:** Documents that newly-added stocks to the S&P 500 exhibit changed put-call IV skew due to indexer + ETF demand for protection. Effect persistent across recent inclusions.
- **Key findings:**
  - Newly-added stocks' IV skew shifts
  - ETF / index protection drives put demand
  - Effect economically significant
  - Persistent over months
  - Connects to demand-based pricing literature
- **Relevance to GTOS:** Index inclusion effects on NDX components affect option-implied features; tertiary relevance.
- **Potential hypothesis:** N/A (less direct)
- **Cross-domain links:** 13, 16
- **index_studied:** SPX

---

## 11. Recent advances 2020-2025

### Where Heston Breaks: Stochastic Volatility Limits / Practitioner Heston GARCH
- **Authors:** Multiple (per ScienceDirect 2024 review)
- **Year:** 2024
- **Source:** Journal of Empirical Finance
- **URL:** https://www.sciencedirect.com/science/article/pii/S105752192400228X
- **Abstract:** Recent practitioner-Heston review that refines closed-form GARCH option pricing, expanding the Heston-Nandi framework for modern derivatives. Relevant for SPX option-pricing applications post-COVID volatility regime.
- **Key findings:**
  - Modern Heston-GARCH variants
  - SPX calibration improvements
  - Captures 2020+ regime shifts
  - Foundational refinement
  - Bridges classical + modern
- **Relevance to GTOS:** Background on modern option-pricing technology; non-immediate.
- **Potential hypothesis:** N/A (methodology refinement)
- **Cross-domain links:** 16
- **index_studied:** SPX

### Volatility Risk and Volatility-of-Volatility Risk: State-Dependent Correlations Between VIX and the S&P 500 Stock Index
- **Authors:** Li et al.
- **Year:** 2025
- **Source:** Journal of Futures Markets, Vol. 45
- **URL:** https://onlinelibrary.wiley.com/doi/full/10.1002/fut.70035
- **Abstract:** Examines state-dependent VIX-SPX correlations. The relationship between VIX changes + SPX returns is asymmetric and conditional — particularly extreme during left-tail SPX moves. Hedging effectiveness varies by state.
- **Key findings:**
  - VIX-SPX correlation state-dependent
  - Asymmetric in tails
  - Lower-5% SPX returns coincide with strongest VIX jump
  - Hedging effectiveness regime-conditional
  - Modern updated treatment
- **Relevance to GTOS:** Confirms regime-conditional VIX use. K54 should encode regime (level + delta + state).
- **Potential hypothesis:** When SPX in lower 5% intraday move, VIX-NDX correlation amplifies — directionally bad for NAS100 LONG setups.
- **Cross-domain links:** 16, 03
- **index_studied:** SPX/VIX

### Unveiling Bidirectional Forecasting Between Volatility of VIX and Stock Market: Insights From Asymmetric Jumps and Cojumps
- **Authors:** Jiang et al.
- **Year:** 2025
- **Source:** Journal of Futures Markets
- **URL:** https://onlinelibrary.wiley.com/doi/10.1002/fut.70015
- **Abstract:** Documents bidirectional forecasting between VIX volatility-of-volatility and stock market returns. Asymmetric jumps + cojumps drive most of the relationship. SPX cojumps with VIX vol-of-vol are tail-event indicators.
- **Key findings:**
  - Bidirectional VVOL-stock market forecasting
  - Asymmetric jumps central
  - Cojumps with VIX = tail-risk indicator
  - Modern empirical treatment
  - Cross-checks on various sub-periods
- **Relevance to GTOS:** VVIX could serve as tail-risk gate for NAS100 / US30 trading.
- **Potential hypothesis:** Days where VVIX > 90th percentile precede NAS100 / US30 stress regimes; reduce risk.
- **Cross-domain links:** 16, 03
- **index_studied:** SPX/VIX

### VIX Option-Implied Volatility Slope and VIX Futures Returns
- **Authors:** Ji-Hyun Yoon
- **Year:** 2022
- **Source:** Journal of Futures Markets, Vol. 42(8)
- **URL:** https://onlinelibrary.wiley.com/doi/full/10.1002/fut.22317
- **Abstract:** Documents that VIX option-implied volatility slope (across strikes) predicts VIX futures returns. Reveals expectations embedded in vol-of-vol surface. Practical for VIX-related trading.
- **Key findings:**
  - VIX option IV slope predictive
  - Mechanism: dealer + speculator positioning
  - Cross-section of VIX strike IV informative
  - Robust across recent decade
  - Practical features extractable
- **Relevance to GTOS:** Tertiary — VIX trading not core GTOS, but VIX option flow features could enrich K54.
- **Potential hypothesis:** N/A (less direct)
- **Cross-domain links:** 16
- **index_studied:** VIX

### Sizing the Risk: Kelly, VIX, and Hybrid Approaches in Put-Writing on Index Options
- **Authors:** (per arXiv indexing)
- **Year:** 2025
- **Source:** arXiv preprint 2508.16598
- **URL:** https://arxiv.org/html/2508.16598v1
- **Abstract:** Modern Kelly-criterion-based sizing for put-writing on index options. Combines VIX regime classification with hybrid Kelly approach. Demonstrates better drawdown control than fixed-fractional sizing.
- **Key findings:**
  - Kelly sizing on put-writes
  - VIX regime conditioning improves outcomes
  - Hybrid approach beats pure Kelly
  - Modern empirical treatment
  - Practitioner-relevant
- **Relevance to GTOS:** Indirect — put-writing is not GTOS strategy, but Kelly-VIX sizing methodology could inform K54 risk-engineering.
- **Potential hypothesis:** N/A (sizing methodology)
- **Cross-domain links:** 21, 16
- **index_studied:** SPX/VIX

### Improving S&P 500 Volatility Forecasting through Regime-Switching Methods
- **Authors:** (per arXiv indexing)
- **Year:** 2025
- **Source:** arXiv preprint 2510.03236
- **URL:** https://arxiv.org/html/2510.03236v1
- **Abstract:** Regime-switching volatility model for SPX outperforms standard HAR-RV / GARCH benchmarks. Identifies stable regime boundaries; conditional forecasts substantially improve in regime-shift periods.
- **Key findings:**
  - Regime switching beats single-regime
  - Boundaries identifiable via state-space methods
  - Out-of-sample improvements
  - Most useful in regime transitions
  - Methodology generalizable
- **Relevance to GTOS:** **Strongly relevant to K54 v2 regime-aware classification.** Directly applicable methodology.
- **Potential hypothesis:** Regime-switching VIX classification (low/normal/elevated/crisis) used as conditioning variable for K54 lifts NAS100 trade-quality classification meaningfully.
- **Cross-domain links:** 16, 19, 05
- **index_studied:** SPX

---

## 12. Gaps and caveats (synthesis support)

1. **NDX-specific empirical work is sparse.** Most academic literature targets SPX. Practitioner literature on NDX-specific gamma exists (SpotGamma, MenthorQ, FlashAlpha) but is not peer-reviewed. **Action:** treat NDX-specific findings as inferred from SPX literature unless explicitly tested.

2. **DJI / US30-specific work is the thinnest.** Stoll-Whaley 1987/1991 and TORB futures index paper are core; otherwise DJI is treated as a "generic large-cap index" in literature.

3. **0DTE literature is rapidly evolving.** Dim-Eraker-Vilkov + Cboe research suggest impact is small; Adams-Dim-Eraker 2025 follow-up "Do S&P500 Options Increase Market Volatility? Evidence from 0DTEs" examines this further.

4. **Pre-FOMC drift caveat.** Lucca-Moench 2015 finding has been refuted by the 2020 paper — drift disappeared post-2015. Operational implication: **do not assume pre-FOMC long bias** for current GTOS production.

5. **Index-effect decay caveat.** Greenwood-Sammon 2024 documents that the well-known 1990s S&P-500-inclusion effect is gone. Confirms F11 / OB-zone-decay-style erosion is general, not GTOS-specific.

6. **VIX1D as feature requires bias correction.** Raw VIX1D has systematic intraday + day-of-week bias; do not use uncorrected.

7. **Many "max pain"/"GEX" practitioner claims lack rigorous tests.** Filippou-Garcia-Ares-Zapatero 2022 provides academic support, but most GEX-related claims (SpotGamma, MenthorQ) are practitioner-only.

8. **VPIN-style flow-toxicity measures require trade-level data** GTOS does not currently have intraday tick-level NDX/US30 trade direction. Tick daemon stores data but quote-classification not implemented.

---

## 13. Cross-domain handoffs (per `_INDEX.md` §6)

- **VIX as descriptive vol stylized fact** (asymmetric vol, leverage effect) → 03
- **VIX as trading instrument / vol-arb strategy** → 16
- **OPEX VWAP / volume general framework** → 08
- **Round-number / level magnetism general** → 09
- **Sector / single-stock factor anomalies** → 13
- **FOMC / CPI macro framing (policy side)** → 11
- **Hedge-fund alpha / decay studies** → 22
- **Behavioral finance underpinning index reactions** → 17
- **RL / ML execution algorithms** → 19, 20

---

*End of papers.md. Total entries: 45 individual papers / sources in §2-11. UTF-8 encoded. Sources verified via WebSearch with URLs validated.*
