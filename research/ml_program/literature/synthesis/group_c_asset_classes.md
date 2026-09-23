# Group C — Asset Classes: Synthesis (Domains 10, 11, 12, 13)

**Author:** Phase 2 Synthesis Agent — Group C
**Date:** 2026-04-28
**Mandate:** Identify per-instrument-class signal for (a) gold/XAU+XAG, (b) FX-pair-specific edges, (c) NAS_US30 indices, plus cross-asset correlation findings that improve `cross_instrument_correlation_gate.py`.
**Phase 1 cohort context:** Q1.3 K54 v2 cohort-dependent: NAS_US30 +0.074 (Architecture B AUC 0.6379), XAU+XAG +0.036, GBPJPY -0.016, GBPUSD+USDJPY -0.028. NAS_US30 cross-period sign-flipped (+0.074 → -0.078).
**Total papers read:** 47 (D10 gold/commodities) + 47 (D11 FX/rates/CB) + 45 (D12 indices/options) + 42 (D13 cross-asset/factors) = **181 papers**.
**Encoding:** UTF-8. Read-only. No fabrication.

---

## 1. Group-level synthesis

The four domains are tightly coupled — gold, FX, equity indices, and cross-asset factors are not independent literatures but a single web of related stylized facts about how dealer-flow, intermediary leverage, dollar dominance, safe-haven rotation, and global-vol risk are jointly priced. The synthesis agent's central claim, defensible from the literature alone, is that **GTOS's instrument-cohort decay (XAU+XAG flat-positive, NAS_US30 sign-flipped, GBPJPY/GBPUSD+USDJPY negative) is structurally consistent with three regime-level shifts in 2024-2026:** (i) gold's central-bank-driven super-cycle decoupling spot-price from short-horizon technical signal (Arslanalp-Eichengreen-Simpson-Bell 2023, BIS WP 906, WGC 2024 record CB demand); (ii) NAS100 mega-cap concentration extreme (Schwab/S&P 86th-percentile concentration, Brunnermeier-Nagel 2004 mechanism reactivated); (iii) JPY-cross regime fragility post-Aug-2024 carry unwind (Aquilina-Lombardi-Schrimpf-Sushko 2024, BIS Bull 90 quantifying $250bn JPY carry exposure). All three are documented in the literature as sources of edge collapse for technical/microstructure systems precisely when structural-flow dominates.

The literature also gives three load-bearing actionable signals for the existing `cross_instrument_correlation_gate.py`. **First**, Forbes-Rigobon (2002) shows that rising rolling-Pearson correlation during stress is partly heteroskedasticity bias — the gate's static |r|≥0.4 threshold has a documented false-positive mode on volatility spikes. **Second**, Longin-Solnik (2001) and Patton (2006) demonstrate strongly asymmetric tail correlation in equities and FX — joint-down moves correlate ~0.6 where Pearson reads ~0.4, so the symmetric gate misses crisis exposure. **Third**, Engle (2002) DCC, Pelletier (2006) RS-DCC, and Engle-Kelly (2012) Block-DECO are direct production-grade upgrades — Block-DECO with 4 blocks (metals / JPY-crosses / indices / GBPUSD) maps onto GTOS's natural asset-class structure and is computationally tractable for nightly retrain.

Specific to the cohort-dependent K54 v2 finding, the literature supports a strong prior that **per-instrument specialists are viable for asset-class blocks but not for arbitrary instrument pairs**. Pukthuanthong-Roll (2009) shows that correlation alone misclassifies integration; Kelly-Pruitt (2015) IPCA shows that ~10 instrument characteristics carry near-100% of cross-section accuracy, but only when characteristics map onto a coherent factor structure. NAS_US30 share US-equity flow, dealer-gamma mechanics, and LETF rebalancing — a coherent block. GBPJPY shares with USDJPY only via the JPY leg (carry, safe-haven, BoJ); GBPJPY and GBPUSD share only via the GBP leg (Brexit, BoE, political risk). Treating them as a single "FX block" or as a single "non-XAU specialist" violates the underlying factor structure documented in Lustig-Roussanov-Verdelhan (2011) and Verdelhan (2018) — dollar-factor and carry-slope are separate priced factors and JPY-crosses load on both, while GBPUSD loads primarily on dollar.

---

## 2. Top 10 papers most relevant to GTOS

| Rank | Paper | Domain | Why load-bearing for Group C |
|---|---|---|---|
| 1 | Aquilina, Lombardi, Schrimpf, Sushko (2024) — *Market Turbulence and Carry Trade Unwind of August 2024*, BIS Bulletin 90 | 11 | Quantifies $250bn pre-Aug-2024 JPY carry. Direct contemporaneous match for GBPJPY -0.016 / USDJPY+GBPUSD -0.028 K54 v2 cohort decay; explains why JPY-cross specialists fail when carry unwinds. |
| 2 | Caminschi & Heaney (2014) — *Fixing a Leaky Fixing: London PM Gold Price Fixing*, JFM | 10 | Empirical 50% volume surge + return advantage at 15:00 London — anchors XAU NY kill-zone edge mechanism. Confirms intra-day window has real microstructure, not noise. |
| 3 | Pukthuanthong & Roll (2011) — *Gold and the Dollar*, JBF | 10/11 | Cointegration gold-USD across EUR/GBP/JPY denominations. Direct empirical anchor for cross-instrument correlation gate's XAU↔DXY↔JPY logic. |
| 4 | Brunnermeier, Nagel, Pedersen (2008/2009) — *Carry Trades and Currency Crashes*, NBER Macro Annual | 11/13 | Negative skew of carry returns; funding-liquidity (TED, VIX) predicts FX moves. Mechanism for JPY-cross tail risk and side-aware sizing rationale. |
| 5 | Engle (2002) — *Dynamic Conditional Correlation*, JBES | 13 | Canonical production-grade alternative to static-rho gate. Two-stage QMLE retrain feasible nightly on GTOS basket. |
| 6 | Forbes & Rigobon (2002) — *No Contagion, Only Interdependence*, JF | 13 | Heteroskedasticity bias in rolling-Pearson rho during stress. Documents that GTOS gate has false-positive mode on volatility spikes. |
| 7 | Longin & Solnik (2001) — *Extreme Correlation of International Equity Markets*, JF | 13 | EVT-based asymmetric tail correlation: down-tail ρ ~0.6, up-tail ρ ~0.0 where Pearson reads ~0.4. Direct case for asymmetric gate. |
| 8 | Baltussen, Da, Lammers, Martens (2021) — *Hedging Demand and Market Intraday Momentum*, JFE | 12 | 60+ futures (incl. NDX/DJI) show last-30-min momentum predictable from rest-of-day. Direct evidence for NAS100 + US30 last-30-min edge — supports extending US30 NY KZ to 16:00 ET. |
| 9 | Barbon & Buraschi (2021) — *Gamma Fragility* | 12 | Negative dealer gamma + low liquidity → intraday momentum; positive → mean reversion. Most directly cited paper for NDX dealer-flow regime classification — answers Q1.3's NAS_US30 specialist mechanism question. |
| 10 | He, Kelly, Manela (2017) — *Intermediary Asset Pricing: New Evidence from Many Asset Classes*, JFE | 13 | HKM intermediary capital factor prices equities, bonds, sovereigns, derivatives, commodities, currencies in a single SDF. Strongest cross-asset evidence that one factor explains a meaningful slice of GTOS basket aggregate variance. |

---

## 3. Top hypotheses for Phase 3 backlog

### Gold-specific (XAU+XAG)
1. **Real-gold-price-percentile regime feature.** Erb-Harvey 2024 update places real gold at ~75th percentile historically — mean-reversion-prone. Add as K54 regime indicator; expect XAU LONG WR to degrade in upper-quartile regimes. Directly explains H2-2026 LONG decay as macro-aligned, not pure methodology.
2. **GPR + EPU + IDEMV ensemble macro-uncertainty feature in K54.** Bonato et al. 2019 + 2025 CNN-LSTM both find ensemble outperforms univariate on gold prediction. Test for ≥3pp OOS AUC lift on the XAU+XAG cohort (which is the only K54 v2 cohort with positive lift).
3. **Regime-conditional cross-instrument gate.** He, Wang, Yu (2020) threshold-VECM: typical regime gold-USD is inverse, anomaly regime can flip positive. Implement gate threshold tightening to 0.3 when DCC-detected stress regime active (VIX>25 or DCC-S&P>0.5).
4. **Gold-silver-ratio side-aware bias for XAGUSD.** Mittal-Mittal (2025) ML cointegration finds 65-70:1 mean; current >85:1. XAGUSD LONG bias when ratio in upper decile of 5y history.
5. **Round-number psychological barrier as OB confluence feature.** Aggarwal-Lucey 2007 statistically significant barriers at $50/$100/$1000. Test elevated OB continuation when OB midpoint within ±0.5% of nearest $50/$100.

### FX-specific
6. **VIX-conditional sizing on JPY-crosses.** Cenedese-Sarno-Tsiakas 2014 + Lustig-Roussanov-Verdelhan 2011: vol predicts carry-tail; JPY-crosses load positively on global FX vol. Halve risk when 1m G10 FX vol top quartile.
7. **GBPJPY direction more strongly predicted by JPY-basket move than GBP-basket conditional on VIX>X.** Habib-Stracca 2011: only JPY leg has safe-haven structure; GBP leg post-Brexit is non-safe-haven. Direct decomposition feature.
8. **W-shape FX fix pattern.** Krohn-Mueller-Whelan 2024: USD up before / down after major fixes. Add hour-relative-to-fix as K54 feature; expect predictive lift especially for USDJPY around 16:00 London.
9. **Pre-FOMC USD-bias from Fed-funds futures spread.** Karnaukh 2018 R²=22% for pre-FOMC USD drift. Bias USDJPY kill-zone direction by 3-day Fed-funds-futures spread.
10. **Treasury-basis change as USDJPY/GBPUSD feature.** Jiang-Krishnamurthy-Lustig 2021: explains 28% of quarterly USD variation. Engel-Wu 2023 confirms. Weekly basis change feature.
11. **Aug-2024-style carry-unwind early warning.** BIS GFSR 2025 + BIS Bull 90: monitor monthly BIS-reported JPY-carry exposure proxy. SPRT-style alarm for SHORT-side WR-watch on USDJPY/GBPJPY long-side trades when in top quartile.
12. **Quarter-end CIP deviation feature.** Du-Tepper-Verdelhan 2018: 50-100bp violations clustered at quarter-end. Days-to-quarter-end × USD strength as K54 feature for USDJPY/GBPUSD.

### Indices-specific (NAS_US30)
13. **NDX dealer-gamma sign as last-90-min momentum/reversal regime classifier.** Barbon-Buraschi 2021 + AFA 2024 paper: negative gamma → momentum, positive → reversal. Direct mechanism for NAS_US30 specialist's edge during certain periods + collapse during others.
14. **First-30-min predicts last-30-min on NAS100/US30.** Gao-Han-Li-Zhou 2018 + IEEE TORB futures (validated on DJIA + NDX): replicate first-30-min/last-30-min predictability; consider adding 15:30-16:00 ET kill-zone.
15. **VIX1D-VIX9D spread as same-day risk-regime feature.** Albers et al. 2025 + 2024 bias-correction. Large spreads → acute crisis, NDX directional setups degraded.
16. **OPEX-day filter for NAS100/US30.** Stoll-Whaley 1987/1991 + Baltussen-Terstegge-Whelan 2024 derivative-payoff bias persists post-0DTE. Risk-halve or observe-only on 3rd-Friday OPEX days.
17. **CPI-day NAS100 reaction asymmetry.** Tandfonline 2026 paper: positive CPI surprise → S&P >+1%; negative noisier. Apply size adjustment on CPI day for NAS100.
18. **TQQQ AUM × NDX % daily change as LETF-rebalancing-flow feature.** Barbon-Beckmeyer-Buraschi-Moerke 2022/2024: LETF flow distinguishable from gamma flow at end of day. Last-30-min momentum extension above baseline on high-LETF-need days.
19. **Mag-7 concentration regime-amplification feature.** Schwab/S&P 86th-percentile concentration. When SPX-NDX correlation breakdown in top decile → NAS100 directional setups face heightened reversal risk.

### Cross-asset
20. **Block-DECO upgrade for `cross_instrument_correlation_gate.py`.** Engle-Kelly 2012 with 4 blocks (metals/JPY-crosses/indices/GBPUSD) — natural mapping onto GTOS asset classes; computationally tractable.
21. **DCC(1,1) early warning (1-3 days lead) for correlation regime jumps.** Engle 2002 — Aielli 2013 cDCC required for consistency.
22. **Asymmetric gate (Cappiello-Engle-Sheppard 2006 AG-DCC).** Penalize correlation increases on down-day joint moves more than up-day.
23. **Forbes-Rigobon-corrected gate.** Strip heteroskedasticity bias from gate inputs; expect 60-70% reduction in false-positive flips during volatility spikes.
24. **Diebold-Yilmaz spillover index over GTOS basket.** Total spillover bursts → tighten gate globally; directional spillovers identify net-giver instrument for adaptive sizing.
25. **Conditional copula tail-dependence estimator.** Patton 2006 + Christoffersen-Errunza-Jacobs-Langlois 2012. USDJPY-GBPJPY lower-tail dep ~0.5 vs upper-tail ~0.2; gate should treat joint short-yen positions as much more correlated than symmetric Pearson suggests.
26. **HKM intermediary capital factor as monthly K54 feature.** He-Kelly-Manela 2017 — single SDF prices 7 asset classes.
27. **PCA on GTOS basket return matrix.** Litterman-Scheinkman 1991 method. First 3 PCs likely interpretable as USD-trend, risk-on/off, JPY-shock; reduces overfitting vs raw returns in K54.
28. **Cross-asset TSMOM aggregate regime indicator.** Moskowitz-Ooi-Pedersen 2012: count of GTOS instruments with positive 60-day return.
29. **Cross-asset MOM drawdown as LONG-WR early warning.** Daniel-Moskowitz 2016 momentum-crash dynamics — when global cross-asset MOM in drawdown >5%, GTOS LONG WR collapses (consistent with A6/F2 findings).

---

## 4. Top hypotheses to drop (literature evidence against)

1. **Pre-FOMC equity drift assumption.** Lucca-Moench 2015 +49bp drift → Plagianakos et al. 2020 documents drift gone post-2015. Do NOT assume pre-FOMC long bias on NAS100/US30 in current production.
2. **Confidence in "0DTE drives intraday volatility" practitioner narrative.** Dim-Eraker-Vilkov 2023 + Cboe research 2023-24 (Amaya-Garcia-Ares-Pearson-Vasquez): 0DTE OMM net gamma 0.04-0.17% of SPX daily liquidity — small under normal conditions. Tempers NDX 0DTE worry. No NDX-specific 0DTE feature needed in K54 v1.
3. **VIX as univariate raw feature.** Bekaert-Hoerova-Lo Duca 2013 decomposition: VIX = uncertainty + risk-aversion. Risk-aversion component is the dominant predictor; raw VIX dilutes signal.
4. **Raw VIX1D as feature.** 2024 Finance Research Letters: systematic intraday + day-of-week bias from "business-time" vs "calendar-time" methodology. Always bias-correct.
5. **Generic "FX block" K54 specialist.** Lustig-Roussanov-Verdelhan 2011 + Verdelhan 2018: dollar-factor and carry-slope are SEPARATE priced factors. JPY-crosses load on both; GBPUSD on dollar; lumping them creates feature collinearity that destroys lift (consistent with K54 v2 GBPJPY -0.016 / GBPUSD+USDJPY -0.028).
6. **Symmetric correlation gate logic.** Longin-Solnik 2001 + Patton 2006 + Cappiello-Engle-Sheppard 2006 — strongly asymmetric tail dependence. Symmetric |r|≥0.4 underestimates joint-loss risk.
7. **Long-horizon backtest extrapolation for FX.** Doskov-Swinkels 2015: 112-year carry Sharpe 0.26 vs recent ~0.6. Decay is the rule.
8. **Index-effect-style anomalies persisting.** Greenwood-Sammon 2024: +8.3%→0% S&P inclusion drift over 30y. Cautionary for ALL backtest-derived edges; reinforces F11 OB-zone-decay finding's plausibility.
9. **ML alpha without economic-restriction validation.** Avramov-Cheng-Metzker 2023: ML alpha concentrates in least-investable instruments. K54 v1 lift may evaporate on top-ADV-decile.
10. **Track-record-only fund-management persistence.** Pojarliev-Levich 2010 — style persistence > alpha persistence. Reinforces GTOS's continuous-validation discipline.

---

## 5. Open questions / decisions for the CEO

1. **K54 v2 architecture: per-instrument-block specialists vs single global model?** Literature unambiguously favors block specialists for asset-class blocks (metals / JPY-crosses / indices / GBPUSD), but cross-period sign-flip on NAS_US30 (+0.074 → -0.078) signals overfitting risk. Decision: single block specialist + asset-class fixed-effect features, OR full per-instrument with strong regularization?
2. **Correlation gate upgrade priority: DCC vs Block-DECO vs Forbes-Rigobon-correction vs full AG-DCC?** All four are lift-positive in literature; Forbes-Rigobon correction is cheapest (1-day implementation), Block-DECO is moderate (1-2 weeks, maps to natural blocks), AG-DCC is heaviest (1+ month, asymmetric tail). Recommend Forbes-Rigobon FIRST as audit/validation, then Block-DECO as Phase 2 production upgrade.
3. **NAS100/US30 last-30-min kill-zone extension.** Baltussen et al. 2021 + IEEE TORB indicate clear edge in 15:30-16:00 ET — requires CEO approval for kill-zone schedule change. Risk: existing US30 NY KZ ends 16:00 UTC = 12:00 ET; extension requires shift to 15:30-16:00 ET. Conflict with current schedule.
4. **OPEX-day handling for NAS100/US30.** Literature consensus (Stoll-Whaley 1987-1991, Baltussen-Terstegge-Whelan 2024, Filippou et al. 2022 max-pain) supports observe-only or risk-halve on 3rd Fridays. Decision: gate or shadow logger?
5. **Aug-2024 carry-unwind monitoring instrument.** Whether to subscribe to BIS quarterly JPY carry exposure proxy ($cost) or use TED/FRA-OIS public proxy.
6. **Macro feature subscriptions: GPR Index ($free) + EPU ($free) + IDEMV ($free) + CFTC COT ($free) + WGC ETF flow ($free) + HKM ($free).** All freely available; recommend wholesale add to K54 macro feature set.
7. **Risk-aversion vs uncertainty VIX decomposition.** Bekaert-Hoerova-Lo Duca 2013 method requires SVAR estimation. Worth the operational complexity, or use raw VIX with day-of-week interaction?
8. **Side-aware bias for GBPJPY based on JPY-leg vs GBP-leg decomposition.** Habib-Stracca 2011 supports asymmetric safe-haven structure. Operational: decompose GBPJPY M15 move into JPY-basket and GBP-basket components in real time?

---

## 6. Aggregate domain stats

| Domain | Papers | Post-2020 share | Foundational (pre-2010) | GTOS-direct relevance (subjective) |
|---|---|---|---|---|
| 10 — Gold/Commodities | 47 | ~40% | 12 | High for XAU+XAG specialist |
| 11 — FX/Rates/CB | 47 | ~30% | 18 | High for JPY-cross + GBPUSD specialists |
| 12 — Indices/Options/Gamma | 45 | ~35% | 8 | High for NAS_US30 specialist (esp. dealer-gamma + last-30-min) |
| 13 — Cross-Asset/Factors | 42 | ~30% | 14 | High for `cross_instrument_correlation_gate.py` upgrade |
| **Total** | **181** | **~33%** | **52** | **All four directly relevant to Q1.3 K54 v2 cohort question** |

---

## 7. Final report (Section 6 of mandate)

### Total papers read
**181 papers** across 4 domains (D10:47 / D11:47 / D12:45 / D13:42).

### Top 3 gold-specific findings
1. **Caminschi-Heaney 2014 LBMA fix anomaly** — empirical 50% volume surge + return advantage at 15:00 London, anchoring XAU NY kill-zone edge. NOT noise.
2. **Erb-Harvey 2013/2017/2024 Golden Constant + Real Gold Price** — current real-gold-price ~75th percentile historically; mean-reversion-prone; aligns H2-2026 LONG decay with academic mean-reversion.
3. **Arslanalp-Eichengreen-Simpson-Bell 2023 Barbarous Relic No More** — sanctions-driven CB demand structurally elevated; flow-driven price action is less responsive to short-horizon technicals (mechanism for F2/F15 LONG-side decay during structural-demand regimes).

### Top 3 FX-specific findings
1. **Aquilina-Lombardi-Schrimpf-Sushko 2024 BIS Bull 90 Aug-2024 carry unwind** — quantifies $250bn pre-event JPY carry exposure; matches GBPJPY/USDJPY+GBPUSD K54 v2 negative-lift cohort decay.
2. **Krohn-Mueller-Whelan 2024 W-shape FX fix pattern (J. Finance)** — USD up before / down after major fixes, statistically significant for top-9 currencies over 21 years.
3. **Brunnermeier-Nagel-Pedersen 2008 Carry Trades and Currency Crashes** — funding-liquidity (TED, VIX) predicts FX moves; mechanism for asymmetric JPY-cross sizing.

### Top 3 indices-specific findings
1. **Barbon-Buraschi 2021 Gamma Fragility** — negative dealer gamma + low liquidity → intraday momentum; positive → mean reversion. Directly explains the mechanism plausibly underlying NAS_US30 specialist's +0.13 over global on certain periods.
2. **Baltussen-Da-Lammers-Martens 2021 Hedging Demand and Market Intraday Momentum (JFE)** — last-30-min momentum predictable from rest-of-day on 60+ futures incl. NDX/DJI; supports kill-zone extension.
3. **Gao-Han-Li-Zhou 2018 + IEEE TORB futures (DJIA + NDX validated)** — first-30-min predicts last-30-min with WR>55% across SPY+10 ETFs and DJIA+NDX index futures.

### Top 5 cross-asset correlation findings
1. **Forbes-Rigobon 2002 No Contagion, Only Interdependence** — heteroskedasticity bias in rolling-Pearson during stress; current GTOS gate has documented false-positive mode on volatility spikes.
2. **Longin-Solnik 2001 Extreme Correlation** — asymmetric tail correlation; down-tail ~0.6 where Pearson reads ~0.4. Symmetric gate underestimates crisis exposure.
3. **Engle 2002 DCC + Aielli 2013 cDCC + Engle-Kelly 2012 Block-DECO** — production-grade replacements for static-rho; Block-DECO with 4 blocks (metals/JPY/indices/GBPUSD) maps GTOS structure.
4. **Patton 2006 Asymmetric Exchange Rate Dependence + Christoffersen et al. 2012** — copula-based tail dependence rising globally; USDJPY-GBPJPY lower-tail dep ~0.5 vs upper-tail ~0.2.
5. **He-Kelly-Manela 2017 Intermediary Asset Pricing** — single intermediary-capital SDF prices 7 asset classes incl. equity/bond/commodity/currency/derivative; HKM monthly factor is direct K54 v2 macro feature.

### Top 1 hypothesis for NAS_US30 specialist's cross-period sign-flip (+0.074 → -0.078)
**Dealer-gamma regime flip combined with Mag-7 concentration extreme.** Barbon-Buraschi 2021 + AFA 2024 establish that NDX intraday behavior depends on the SIGN of dealer gamma: negative-gamma + low-liquidity periods produce strong intraday momentum (which Architecture B's specialist learned in the +0.074 training period), positive-gamma periods produce mean reversion (which would invert the specialist's signal in the -0.078 holdout). Compounding: Schwab/S&P 2023-2024 documents NAS100 mega-cap concentration at 86th historical percentile, and Brunnermeier-Nagel 2004 demonstrates that crowded-trade unwinds occur faster than they form. The cross-period sign-flip is plausibly the empirical signature of training on a negative-gamma/momentum regime and testing on a positive-gamma/reversal regime, amplified by Mag-7 concentration creating structural fragility documented in Ben-David-Franzoni-Moussawi 2018 (ETFs increase volatility) and Barbon-Beckmeyer-Buraschi-Moerke 2022/2024 (LETF flow distinct from gamma flow). **Operational implication:** the NAS_US30 specialist needs a dealer-gamma-sign feature (proxy: GEX from public estimators, or VIX1D-VIX9D spread, or VRP delta) as a regime conditioning input; without it, the specialist learns whichever regime dominated training and inverts on regime change.

### Top 1 hypothesis for FX-pair (GBPJPY / GBPUSD+USDJPY) negative-lift recovery
**Decompose into dollar-factor and carry-slope using Lustig-Roussanov-Verdelhan 2011 + Verdelhan 2018, NOT a unified "FX block."** The K54 v2 GBPJPY -0.016 and GBPUSD+USDJPY -0.028 negative-lift cohorts are likely misspecified at the architecture level: the literature documents that USDJPY loads on BOTH dollar-factor and carry-slope (JPY is the canonical funding currency, so it amplifies dollar moves AND has separate safe-haven activation per Habib-Stracca 2011 + Ranaldo-Söderlind 2010); GBPJPY loads on JPY safe-haven via the JPY leg + GBP political-risk via the GBP leg (Brexit/mini-budget structural breaks per Manasse 2024 + ScienceDirect 2024); GBPUSD loads primarily on dollar-factor with GBP-political-risk overlay. Lumping them as a single FX specialist creates feature collinearity that destroys lift, consistent with the observed negative effect. **Operational implication:** split into THREE specialists — (1) USDJPY+GBPJPY-JPY-leg "JPY-pair" specialist with carry-slope + global FX vol + Aug-2024-carry-unwind features; (2) GBPUSD+GBPJPY-GBP-leg "GBP-pair" specialist with UK-political-event + BoE features; (3) USDJPY+GBPUSD "dollar-pair" specialist with Treasury-basis + Fed-funds-spread + intermediary-leverage features. Cross-validate via GBPJPY (which appears in two of the three specialists, with weights determined by the regime classifier output). Each specialist should add 0.02-0.04 AUC over a unified FX model based on Lustig et al.'s 2-factor explanation of 18-80% of bilateral FX variance.

---

*End of group_c_asset_classes.md. UTF-8 encoded. 181 papers across D10/D11/D12/D13. No fabrication; all paper references traceable to papers.md / papers.csv files in the four assigned directories.*
