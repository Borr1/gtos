# Phase 2 Synthesis — Group D: Trading Strategies

**Author:** Phase 2 Synthesis Agent — Group D (Opus 4.7, max effort)
**Date:** 2026-04-28
**Domains synthesized:** 14 (trend / momentum / breakout) · 15 (mean reversion / cointegration / stat-arb) · 16 (volatility / derivatives / vol regime)
**Source paper count:** 38 + 38 + 50 = **126** (see per-domain `papers.md` + `papers.csv` for citations)
**Output schema:** 6 sections per Group A template + a final closing report (≤350 words).
**Pre-existing context (not re-derived):**
- F11 (OB-zone advantage decay velocity, +16.8pp pre-2026 → +12.1pp H1-2026 → +4.6pp H2-2026, decay-dominant ~78%, methodology ~22%).
- F15 (regime is the load-bearing decay axis; A6 LONG-side selectivity collapse 48.4% → 18.8%; H1 78% bullish-cohort → H2 4.8%; bonf p=0.0016).
- A1 (mechanical OB +0.036R H2 vs AI -0.131R H2 → SYSTEM_DECAY).
- F2 (XAUUSD London/trending_bull/LONG -59.8pp; Apr-only WR=0% n=4).
- Q1.3 K54 v2 CPCV-honest **FAILED**; top single feature was `vol__h1_range_over_mean_50` (volatility expansion from Group D's domain 16 substrate); the joint-model scout *did* find +0.083 over K54 v1 baseline — modest signal exists but it's small and dominated by volatility-family features.
- J46-J49 portfolio policy +0.742R/trade vs baseline (n=321 p=3.3e-20).
- S79 risk policy uniform_fn 2.0% shipped (+25.8pp P(pass FN)); sharpe_weighted is Phase 2 follow-up.

---

## 1. Cross-cutting findings (5 themes)

### Theme 1 — Mean-reversion and momentum are the SAME phenomenon at different time-scales, conditioned by regime

**Evidence (cross-domain consensus):**
- Lehmann 1990 (D15): weekly winners reverse, weekly losers reverse; mechanism = liquidity provision, not "fad".
- Jegadeesh-Titman 1993 + Moskowitz-Ooi-Pedersen 2012 (D14): 1-12 month past returns predict future returns positively (momentum).
- DeBondt-Thaler 1985, 1987 (D15): 3-5 year extreme winners revert to losers and vice-versa (long-run reversal).
- Jegadeesh 1990 (D15) is the canonical bridge: short-horizon (1-month) **negative** autocorrelation co-exists with long-horizon (12-month) **positive** autocorrelation.
- Hong-Stein 1999 + Barberis-Shleifer-Vishny 1998 (D14): underreaction → mid-horizon momentum; overreaction → long-horizon reversal — *generated jointly by one belief-updating mechanism*.
- Wood-Roberts-Zohren 2022 (D14): explicitly hybridizes "slow momentum" with "fast reversion" via online change-point detection; +33% Sharpe full-sample, +67% in 2015-2020.

**GTOS implication.** GTOS lives in the *intersection* — its "stop-cascade reversion to OB" (mean-reversion at sub-hour) is anchored by the prevailing structural trend (momentum at H1-H4). The F15 finding (regime-conditioned LONG-side decay) is the mechanism: when the regime is mid-bull (trending_bull), the multi-TF momentum and the local mean-reversion are *aligned*; the OB-retest is a continuation entry. When the regime *transitions* (the cohort that collapsed in H2), the local-reversion is now *against* the new trend, and the entry becomes a counter-trend trade in disguise. Wood-Roberts-Zohren's "fast reversion when trends die" architecture is the literal Phase 2 K54 v3 recipe.

### Theme 2 — Strategy returns are state-dependent; the binding constraint is regime-conditional Sharpe, not gross alpha

**Evidence:**
- Cooper-Gutierrez-Hameed 2004 (D14): momentum profits +0.93%/mo after positive market state, **−0.37%/mo after negative state**.
- Daniel-Moskowitz 2016 (D14) "Momentum Crashes": momentum's losses concentrate in panic-state-then-rebound; dynamic Sharpe ~2× static.
- Lewellen 2002 (D14) + Avramov-Cheng-Hameed 2016 (D14): liquidity and factor-state both gate the momentum payoff.
- Nagel 2012 (D15) "Evaporating Liquidity": short-term equity reversal returns are *liquidity-provision compensation*, **VIX-conditional** with R²>0.3 for some horizons; 2008-2009 reversal Sharpe ~5.
- Bekaert-Hoerova 2014 + Bardgett-Gourier-Leippold 2019 (D16): Variance Risk Premium (VRP) regime-switches between high-vol and low-vol; predictive power is highly state-dependent.
- Hutchinson-O'Brien 2014 (D14): trend-following <50% normal returns for 4 years post-financial-crisis as autocorrelation breaks down.

**GTOS implication.** The CEO's intuition ("decay is real") is empirically supported but *over-broad*. The literature uniformly says: *the edge is conditional, and the conditioning is in volatility / liquidity / regime.* The F15 finding aligns precisely with Cooper-Gutierrez-Hameed and Daniel-Moskowitz at the strategy level. **GTOS does not need to "fix" the OB-edge; it needs to *gate* it on the right regime / vol state.** This is a much smaller engineering problem than "rebuild K54 from scratch".

### Theme 3 — Volatility is rough, path-dependent, and predictable enough to size on

**Evidence:**
- Gatheral-Jaisson-Rosenbaum 2018 + Bayer-Friz-Gatheral 2016 (D16): log-vol behaves as fractional Brownian motion with H≈0.1 across 21 indices — anti-persistent at high frequency.
- Engle 1982, Bollerslev 1986, Hansen-Lunde 2005 (D16): GARCH(1,1) is the workhorse; nothing beats GARCH(1,1) for FX vol forecasting.
- Andersen-Bollerslev-Diebold-Labys 2003 + Corsi 2009 (D16): realized vol is predictable; HAR-RV with lags (1, 5, 22) wins.
- Guyon-Lekeufack 2023 (D16): 4-factor *path-dependent volatility* explains **65% of realized vol variance** and **90% of implied vol variance** from past returns alone — no latent SV factor.
- Yang-Zhang 2000, Garman-Klass 1980, Parkinson 1980 (D16): range-based estimators are strictly better than ATR for single-bar vol.
- Bollerslev-Tauchen-Zhou 2009 + Drechsler-Yaron 2011 + Bollerslev-Todorov 2011 (D16): VRP is a robust quarterly-horizon return predictor; near-tail VRP is the strongest known.
- Barroso-Santa-Clara 2015 (D14) "Momentum Has Its Moments": volatility-scaled momentum **almost doubles Sharpe** (0.53 → 0.97) by eliminating crashes.

**GTOS implication.** GTOS's `risk.sl_buffer_atr_multiplier` is 1980s technology applied to a 2020s problem. Five concrete upgrades supported by ≥3 papers each:
1. Replace ATR-EMA with HAR-RV(1,5,22) on log-realized-vol — Andersen-Bollerslev-Diebold-Labys + Corsi.
2. Add PDV-style power-law-weighted past-return aggregations as K54 features — Guyon-Lekeufack.
3. Add range-based estimators (Yang-Zhang) as cheap-and-strong vol features — Yang-Zhang.
4. Make S79 sharpe_weighted explicit Barroso-Santa-Clara: position size ∝ 1/realized-vol-of-realized-R, clip to [0.5, 2.0].
5. Make SL-buffer multiplier vol-of-vol-aware via rough-vol scaling, not just ATR scaling.

### Theme 4 — Decay is real, gradual, and survivable — but ONLY if the strategy is multi-component

**Evidence:**
- Avellaneda-Lee 2010 (D15): PCA-stat-arb Sharpe fell **1.44 (1997-2007) → 0.9 (2003-2007)** — visible alpha decay.
- Do-Faff 2010 (D15): pairs-trading profitability **roughly halved** 1989-2008 vs 1962-1988, **but concentrated in turbulent periods**.
- Khandani-Lo 2007/2011 (D15): August 2007 quant meltdown — crowded trade unwind, NOT pure information loss.
- McLean-Pontiff 2016 (D14): 97 published anomalies decline **26% OOS, 58% post-publication**. Magnitude is unprecedented but **not extinction**.
- Babu-Hoffman-Levine et al. 2020 (D14) "You Can't Always Trend When You Want": 2010-2018 trend-following underperformance is **fully attributable to muted market moves**, not signal-translation decay.
- Hurst-Ooi-Pedersen 2017 + Lempérière et al. 2014 (D14): trend-following is positive every decade since 1880 / 1800.

**GTOS implication.** The decay narrative needs *quantitative attribution*, not narrative. The Babu et al. decomposition (move-magnitude × signal-translation × diversification) is the exact framework F11/F15 should be re-cast in. Pre-registered prediction: a Babu decomposition on H1 vs H2 2026 will show that XAU's H2 LONG decay is split ~40% market-move-magnitude (smaller realized vol in trending_bull regime) / ~60% signal-translation (LONG-side selectivity collapse). If true, **a substantial fraction of decay reverses with vol regime change**, lowering urgency for prompt-overhaul actions and pointing toward S79 sharpe_weighted as the highest-yield investment.

### Theme 5 — Stop-cascade reversion is published mechanism, not folk-theorem

**Evidence:**
- **Osler 2003, 2005** (D15) "Stop-Loss Orders and Price Cascades in Currency Markets" — the literal published precedent for GTOS's edge mechanism. Documents (a) stops cluster just below round numbers, (b) clusters generate self-reinforcing cascades when triggered, (c) prices reverse at predictable round-number levels post-cascade. *Stronger than take-profit responses, persists longer, stronger in low-liquidity periods.*
- Stübinger-Endres 2018 (D15) "Pairs Trading with Mean-Reverting Jump-Diffusion": the displacement-then-mean-reversion pattern is best modeled as *jump-diffusion* (jump for displacement, OU for retest), not pure-OU.
- Stübinger-Bredthauer 2019 (D15): overnight S&P 500 gaps mean-revert intraday — direct analog of GTOS's displacement-then-OB-retest, different time-scale.
- Lo-Mamaysky-Wang 2000 (D15): visually-defined chart patterns DO have measurable predictive power; technical-analysis is not pseudoscience when made objective.
- Lehmann 1990 (D15) + Nagel 2012 (D15): the mechanism *is* liquidity-provision compensation, not behavioral fad.

**GTOS implication.** The OB-retest edge is **academically supported, not folk-theoretic.** Phase 2 should:
1. Add `distance-to-nearest-round-number` × `OB-zone` as a *multiplicative* K54 feature (Osler additivity hypothesis H15-2).
2. Model displacement as *jump* and retest as *OU* (Stübinger-Endres) — better generative model for K54 features.
3. Re-position GTOS publicly (research-internal) as "round-number-and-OB-reinforced liquidity-provision compensation" not "ICT/SMC continuation play." This sharpens the mechanism story and clarifies what to instrument.

---

## 2. Top 5 actionable hypotheses

Numbered for cross-reference; pre-registerable.

**H-D1 (Vol-regime-conditional edge, Nagel-style; HIGHEST CONFIDENCE).** GTOS expectancy is a **positive function** of contemporaneous realized-vol percentile / VIX regime / VRP regime. Stratify J46-J49 portfolio findings by realized-vol-decile per instrument; predict that the top 30% vol regimes show >2× the realized R/trade of the bottom 30%. **Evidence:** Nagel 2012 (R²>0.3 VIX→reversal-Sharpe), Bollerslev-Tauchen-Zhou 2009, Bekaert-Hoerova 2014, Do-Faff 2010 (pairs concentrated in turbulent periods).

**H-D2 (Regime-conditioned LONG-sizing modifier — Daniel-Moskowitz port).** A K54 LONG-side sizing modifier of form `0.5x if regime ∈ {trending_bull, transitional} AND realized_vol_z > +1; 1.0x otherwise` will deliver +20-40% improvement in LONG-side realized R/trade vs uniform sizing. **Evidence:** Daniel-Moskowitz 2016 (momentum crashes in panic+rebound); Cooper-Gutierrez-Hameed 2004 (post-state asymmetry); F2 (London/trending_bull/LONG -59.8pp); F15. **Bundles directly with S79 sharpe_weighted Phase 2.** This is the single highest-leverage, lowest-effort change available.

**H-D3 (Path-dependent vol features — Guyon-Lekeufack port).** Replacing K54 v2's `vol__h1_range_over_mean_50` (top single feature, but inconclusive on CPCV-honest) with PDV-style power-law-weighted aggregations of past M15 returns and squared-returns (4 features × 2-3 decay rates = 8-12 features) will (a) reduce K54 redundancy, (b) match or exceed `vol__h1_range_over_mean_50` predictive power, (c) survive CPCV-honest accounting. **Evidence:** Guyon-Lekeufack 2023 (PDV explains 65% of realized vol variance from past returns alone, beats rough-vol AND classical SV).

**H-D4 (Sharpe-objective training — Lim-Zohren-Roberts port).** Training K54 v3 with a **Sharpe-objective** rather than cross-entropy / log-loss will improve OOS Sharpe by 20-40% for the same feature set. The Q1.3 K54 v2 CPCV failure may be partly an *objective-mismatch* failure: classifier accuracy ≠ trade-Sharpe. **Evidence:** Lim-Zohren-Roberts 2019 (Deep Momentum Networks with Sharpe-objective training >2× Sharpe vs static TSMOM); Wood-Roberts-Zohren 2022.

**H-D5 (Continuous-sized OB entries vs binary CANDIDATE/NO-CANDIDATE — Cartea-Jaimungal port).** A continuous K54 score → continuous risk size (function of OB-distance and predicted R-quantile) will outperform the current binary CANDIDATE/NO-CANDIDATE logic by 15-30% portfolio realized-R. **Evidence:** Cartea-Jaimungal 2016 (analytic optimal size is *linear in cointegration residual*); Bertram 2010 (Sharpe-optimal vs return-optimal threshold split). Crucially, this re-frames K54's job from "is this a trade?" to "how much exposure does this signal warrant?" — directly addressing the AUC-vs-realized-R disconnect.

---

## 3. Top 1 strategy archetype GTOS isn't currently exploiting

**The "Volatility-Conditioning Overlay" archetype** — also called **vol-managed momentum** in the literature.

The GTOS pipeline currently has two layers (structure detection → AI evaluation) and *no* explicit vol-regime conditioning layer above them. The literature unanimously supports adding a **vol-regime gate / sizing layer** between the AI evaluation and the execution engine:

- **Barroso-Santa-Clara 2015**: vol-managed momentum nearly doubles Sharpe (0.53 → 0.97) via inverse-realized-vol scaling.
- **Daniel-Moskowitz 2016**: dynamic momentum forecastable from market state + lagged vol; Sharpe ~2× static.
- **Wood-Roberts-Zohren 2022**: hybrid slow-momentum + fast-reversion via online change-point detection; +33-67% Sharpe over base DMN.
- **Geczy-Samonov 2016**: dynamic-beta hedging (200 years of evidence) — reduce LONG size on regime-transition flag.
- **Nagel 2012**: liquidity-provision returns scale with VIX; conditional Sharpe up to 5.
- **Bardgett-Gourier-Leippold 2019**: VVIX (vol-of-vol) > VIX as regime classifier.

**Concrete shape for GTOS.** Insert a "vol-conditioning" component between Component 3A (AI Primary Analyzer) and Component 4 (Execution Engine):

```
Component 3A (AI evaluation, CANDIDATE/NO) →
  [NEW] Component 3C (Vol-regime sizer):
    - Realized-vol percentile (per-instrument, rolling 30 days)
    - VRP estimate (where VIX/GVZ available)
    - Regime persistence score (rolling autocorr of regime)
    - Sigma multiplier output ∈ [0.5, 2.0]  →
Component 4 (Execution at sigma-adjusted size)
```

This is a *small* engineering increment (one new component, all features computable from existing OHLCV + minimal external data) but addresses Themes 1, 2, 3, 4 simultaneously. **It is the single highest-EV / lowest-cost addition the literature unambiguously endorses.**

---

## 4. Top 1 vol-regime finding for S79-style risk policy

**Finding: vol-managed sizing is the most-replicated, highest-Sharpe-impact intervention in the entire trend/mean-reversion/vol literature.** It is supported by ≥6 papers in this synthesis (Barroso-Santa-Clara 2015; Daniel-Moskowitz 2016; Hurst-Ooi-Pedersen 2013; Babu et al. 2020; Geczy-Samonov 2016; Cartea-Jaimungal 2016) and the empirical effect size (Sharpe roughly doubles) is the largest reported single intervention.

**Concrete S79 Phase 2 specification (sharpe_weighted, Barroso-Santa-Clara port).**

```
position_size_R = base_R × clip(target_vol / realized_R_vol_30d, 0.5, 2.0)

where:
  base_R = 2.0% (current S79 uniform_fn)
  target_vol = pre-registered constant (e.g., median realized_R_vol over 2024-2025 backtest)
  realized_R_vol_30d = rolling-30-trade std of realized R per instrument
```

**Pre-registered prediction.** This rule will:
1. Deliver **+30-50% Sharpe improvement** vs uniform_fn 2.0% in OOS evaluation (Barroso-Santa-Clara magnitude).
2. **Materially reduce drawdown depth** by halving position size precisely in the high-realized-R-vol regimes that produce GTOS's worst losing streaks (Daniel-Moskowitz mechanism).
3. **Bundle naturally with H-D2** (Daniel-Moskowitz LONG-side modifier) — they multiply: vol-managed AND regime-conditional.

**Caveat (Babu et al. discipline).** Before shipping, perform the Babu-decomposition on GTOS H1 vs H2 2026: separate move-magnitude × signal-translation × diversification components. If H2 underperformance is >50% move-magnitude (small realized vol in trending_bull regime), then *S79 sharpe_weighted will partially reverse the underperformance automatically* by raising position size in the next high-vol regime — a significant fraction of "decay" recovers without any prompt-overhaul work.

---

## 5. Cross-domain handoffs (notes for adjacent groups)

| Receiving group / domain | Reason | Key papers |
|--------------------------|--------|------------|
| **Group A (Foundations) — Domain 02 (Stat methodology)** | Sullivan-Timmermann-White Reality Check + Lo-MacKinlay variance-ratio test directly relevant to K54 hyperparameter discipline | Sullivan-Timmermann-White 1999; Lo-MacKinlay 1988 |
| **Group A — Domain 03 (Distributional)** | GARCH families, Hurst H≈0.1 rough-vol, fat-tail ξ=0.35 evidence | Engle 1982; Bollerslev 1986; Gatheral-Jaisson-Rosenbaum 2018 |
| **Group A — Domain 04 (Multi-TF / fractal)** | Long-memory in vol (d≈0.4 ABDL); rough-vol Hurst H≈0.1 (anti-persistent log-vol) | Andersen-Bollerslev-Diebold-Labys 2003; Gatheral-Jaisson-Rosenbaum 2018 |
| **Group A — Domain 05 (Regime / change-point)** | Wood-Roberts-Zohren CPD module is direct port; Daniel-Moskowitz forecastable crashes are a regime detection problem | Wood-Roberts-Zohren 2022; Daniel-Moskowitz 2016; Bekaert-Hoerova 2014 |
| **Group B (Microstructure) — Domain 06** | Osler 2005 (stop-cascade + round-number clustering), El Euch-Rosenbaum (Hawkes microstructure → rough vol), Andersen-Bollerslev 1998 (intraday FX vol) | Osler 2005; El Euch-Rosenbaum 2018; Andersen-Bollerslev 1998 |
| **Group B — Domain 07 (Order Flow / ICT-SMC)** | Lo-Mamaysky-Wang 2000 (objective TA pattern detection); Stübinger-Endres jump-then-revert is the formal SMC-displacement story | Lo-Mamaysky-Wang 2000; Stübinger-Endres 2018 |
| **Group B — Domain 09 (Round numbers)** | **Osler 2005 is the cross-link of the synthesis** — round-number ∩ OB ∩ stop-cascade ∩ liquidity-provision-compensation. Highest-priority handoff in the entire program. | Osler 2003; Osler 2005 |
| **Group C (Asset class) — Domain 10 (Gold)** | Erb-Harvey 2006 commodity rebalancing premium; XAUUSD-XAGUSD cointegration | Erb-Harvey 2006; Leung-Nguyen 2019 |
| **Group C — Domain 11 (FX)** | Menkhoff et al. 2012 currency momentum; Carr-Wu 2007 stochastic skew; Bates 1996 SVJ DM/USD; ABDV 2003 macro announcements | Menkhoff-Sarno-Schmeling-Schrimpf 2012; Carr-Wu 2007; Andersen-Bollerslev-Diebold-Vega 2003 |
| **Group C — Domain 12 (Equity index / gamma)** | 0DTE (Dim-Eraker-Vilkov 2023; Adams et al. 2024); CBOE SKEW (BKM 2003); VIX construction (Whaley 2009) | Dim-Eraker-Vilkov 2023; Bakshi-Kapadia-Madan 2003; Whaley 2009 |
| **Group C — Domain 13 (Cross-asset / factor)** | Asness-Moskowitz-Pedersen "Value and Momentum Everywhere"; Engle DCC for cross-instrument correlation | Asness-Moskowitz-Pedersen 2013; Engle 2002 |
| **Group E (Behavioral / RL/ML) — Domain 17 (Behavioral)** | Hong-Stein, BSV, Daniel-Hirshleifer-Subrahmanyam underreaction/overreaction mechanisms | Hong-Stein 1999; BSV 1998 |
| **Group E — Domain 19 (AI/ML)** | Lim-Zohren-Roberts Deep Momentum Networks; Krauss-Do-Huck 2017 GBT/RAF/DNN comparison; Guijarro-Pelger-Zanotti conv-transformer stat-arb | Lim-Zohren-Roberts 2019; Krauss-Do-Huck 2017; Guijarro-Pelger-Zanotti 2024 |
| **Group E — Domain 20 (RL / LLM)** | Sharpe-objective training; Hybrid DRL pairs trading (Kim et al. 2022) | Lim-Zohren-Roberts 2019; Kim et al. 2022 |
| **Group F (Risk / Hedge fund) — Domain 21 (Sizing)** | **Barroso-Santa-Clara vol-managed momentum is the canonical S79 sharpe_weighted reference.** Daniel-Moskowitz dynamic; Cartea-Jaimungal continuous sizing; Jurek-Yang divergence-aware reduction | Barroso-Santa-Clara 2015; Daniel-Moskowitz 2016; Cartea-Jaimungal 2016 |
| **Group F — Domain 22 (Hedge fund alpha)** | Hutchinson-O'Brien crisis-shadow; McLean-Pontiff anomaly decay magnitudes; Babu et al. CTA decomposition | Hutchinson-O'Brien 2014; McLean-Pontiff 2016; Babu et al. 2020 |

---

## 6. Coverage / gaps / caveats

### Strong coverage
- Trend-following century-of-evidence (Hurst-Ooi-Pedersen 2017; Lempérière et al. 2014).
- Cross-sectional + time-series momentum from canonical (J-T 1993, MOP 2012) through modern (Ehsani-Linnainmaa 2022 factor momentum).
- Pairs / cointegration foundations (Engle-Granger 1987; Johansen 1991; Gatev-Goetzmann-Rouwenhorst 2006).
- Avellaneda-Lee 2010 PCA stat-arb (canonical modern stat-arb).
- Liquidity-provision mechanism (Lehmann 1990; Nagel 2012; Khandani-Lo 2007).
- Stop-cascade-FX literature (Osler 2003, 2005).
- GARCH / realized vol / range estimators (Engle 1982; Bollerslev 1986; Corsi 2009; ABDL 2003; Yang-Zhang 2000).
- Jump-diffusion (Merton 1976; Kou 2002; Bates 1996/2000; Pan 2002).
- Rough volatility (Gatheral-Jaisson-Rosenbaum 2018; Bayer-Friz-Gatheral 2016; El Euch-Rosenbaum 2018; Guyon-Lekeufack 2023).
- VRP / VIX (Carr-Wu 2009; BTZ 2009; Drechsler-Yaron 2011; Bollerslev-Todorov 2011; Bekaert-Hoerova 2014; Bardgett-Gourier-Leippold 2019).
- 0DTE frontier (Dim-Eraker-Vilkov 2023).
- ML for vol / stat-arb (Krauss-Do-Huck 2017; Guijarro-Pelger-Zanotti 2024; Lim-Zohren-Roberts 2019; Wood-Roberts-Zohren 2022).
- Behavioral mechanism (Hong-Stein 1999; BSV 1998; Daniel-Hirshleifer-Subrahmanyam 1998).

### Partial coverage
- **Intraday momentum at sub-hour horizon:** the academic horizon mismatch with GTOS's M15 cadence is a real gap. Gao-Han-Li-Zhou 2018 (first 30-min predicts last 30-min) is the closest analog; Heston-Korajczyk-Sadka 2010 supports kill-zone-conditioned modeling but at half-hour granularity.
- **FX 0DTE / FX vol regime:** essentially absent from the literature; GBPJPY/USDJPY/GBPUSD have no 0DTE-equivalent paper.
- **Gold-specific stochastic vol calibration:** GARCH-MIDAS gold paper exists, but no Heston-style XAUUSD options-calibrated SV paper.
- **Crowding diagnostic for GTOS-style retail-AI strategies:** Khandani-Lo 2007 quant-meltdown framework is qualitatively the right diagnostic, but GTOS's exact-strategy-crowding cannot be measured from public data.

### Caveats / disciplinary cautions
- **Walk-level evidence is not predictive of realized R** (per memory `feedback_walk_level_evidence_not_predictive`). All hypotheses above must be tested on per-stratum **realized R**, not on AUC / Sharpe-of-classifier.
- **Sullivan-Timmermann-White 1999 Reality Check / Bailey-Lopez-de-Prado Deflated Sharpe is mandatory** for any K54 v3 selection given the multi-feature hyperparameter universe.
- **Goyal-Wahal 2015**: Novy-Marx 2012 echo-decomposition does NOT replicate internationally; do not over-invest in the 12-7 vs 6-1 distinction at the GTOS scale.
- **Heterogeneous time-scales**: most cited papers operate at monthly (J-T-style) or daily (Avellaneda-Lee, pairs) or 30-minute (Gao-Han-Li-Zhou) horizons. GTOS at M15 is *below* most of the literature's horizon. Translation from monthly-momentum to M15-OB-retest requires a leap-of-faith that *needs* per-paper validation in K54 v3 ablation tests.
- **Ockham discipline**: HAR + Lasso (Audrino-Knaus 2016) is hard to beat; Hansen-Lunde 2005 "nothing beats GARCH(1,1)" for FX vol; Krauss-Do-Huck 2017 GBT > DNN at lagged-return inputs. K54 v3 should not skip the simple baseline.
- **Linear-correlation gate is wrong in tails** (Liew-Wu 2013 copula approach; Stübinger-Mangold-Krauss 2018 vine copulas). The current GTOS cross-instrument correlation gate (Pearson ρ ≥ 0.4) is structurally biased; tail-conditional dependence is the right substrate during stress.

### Subscription-bounded research limits
- All paper verification was done via WebSearch / WebFetch and the 126 source-domain `papers.md` files; no Anthropic API calls beyond this synthesis dispatch.
- 100% URL-verified per source domain (all three Phase 1 workers maintained zero-fabrication discipline).
- No retrospective adjustment of priors based on Q1.3 K54 v2 failure — synthesis takes Q1.3 as a given baseline and looks forward.

---

## Final report (≤350 words)

**1. Total papers read.** 126 (38 trend/momentum + 38 mean-reversion + 50 vol).

**2. Top 5 cross-cutting findings.**
1. **Mean-reversion and momentum are one phenomenon at different scales, conditioned by regime.** GTOS's stop-cascade-revert-to-OB lives at the intersection (Hong-Stein 1999, Wood-Roberts-Zohren 2022, Lehmann 1990, Jegadeesh 1990). When trend and local-revert align → continuation works; when regime transitions → counter-trend disguise (F15 mechanism).
2. **State-dependence dominates gross alpha.** Cooper-Gutierrez-Hameed 2004, Daniel-Moskowitz 2016, Nagel 2012, Bekaert-Hoerova 2014: edge is conditional on vol / liquidity / regime — F15 is the canonical realization, NOT an outlier.
3. **Vol is rough, path-dependent, and predictable enough to size on.** Gatheral-Jaisson-Rosenbaum 2018, Guyon-Lekeufack 2023, Barroso-Santa-Clara 2015. ATR is 1980s tech; PDV/HAR-RV/Yang-Zhang are strict upgrades.
4. **Decay is real but survivable with multi-component design.** Avellaneda-Lee 2010, Do-Faff 2010, Hurst-Ooi-Pedersen 2017, Babu et al. 2020 — F11 magnitude (4.6pp residual) is consistent with literature decay rates, not extinction.
5. **Stop-cascade reversion is published mechanism, not folk-theorem.** Osler 2005 documents it for FX with round-number-clustered stops — the academic precedent for GTOS's edge.

**3. Top 5 actionable hypotheses.** H-D1 (vol-regime-conditional edge — Nagel-port); H-D2 (Daniel-Moskowitz LONG-sizing modifier; HIGHEST EV); H-D3 (Guyon-Lekeufack PDV K54 features); H-D4 (Lim-Zohren-Roberts Sharpe-objective training); H-D5 (Cartea-Jaimungal continuous-sized entries). Pre-registerable; bundle with S79 sharpe_weighted Phase 2.

**4. Top archetype GTOS isn't currently exploiting.** **Volatility-Conditioning Overlay (vol-managed momentum).** Insert a Component 3C between AI evaluator and Execution Engine: realized-vol-percentile + VRP + regime-persistence → sigma multiplier ∈ [0.5, 2.0]. Single highest-EV / lowest-engineering-cost addition; supported by ≥6 papers; addresses Themes 1-4 simultaneously.

**5. Top vol-regime finding for S79.** **Barroso-Santa-Clara 2015 vol-managed momentum.** Sharpe 0.53 → 0.97 via inverse-realized-vol scaling; +30-50% Sharpe lift expected for S79 sharpe_weighted port. Bundles with H-D2 multiplicatively. Babu et al. 2020 attribution discipline first: a substantial fraction of the F11/F15 decay may auto-recover under vol-managed sizing without any prompt overhaul.

---

*End of group_d_strategies.md.*
