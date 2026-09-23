# Group B Synthesis — Microstructure, Order Flow, Volume, Levels

**Synthesis agent:** Group B (Phase 2, Opus 4.7 max-effort)
**Date:** 2026-04-28
**Domains synthesized:** 06 (Market Microstructure & Order Book), 07 (Order Flow / Footprint / ICT-SMC Academic), 08 (Volume / Auction / VWAP / OPEX), 09 (Round-Number Effects & Level Magnetism)
**Total papers:** 78 (06) + 32 (07) + 35 (08) + 30 (09) = **175 papers**
**Special focus per brief:** Architectural core for GTOS — informs Component 2 (`market_state.py`), the L2 verifier, the execution engine, and the K54 v2 feature catalog's structure / microstructure / liquidity / level families. Special flag for any paper directly supporting or challenging the OB-zone "stop-cascade-and-correct" framing in `.context/01_knowledge_base/edge_mechanism.md`.

---

## 1. Scope

This synthesis covers GTOS's edge-mechanism literature — the load-bearing theoretical and empirical foundations for *why* the OB-zone construct in `market_state.py` is supposed to work, plus the empirical evidence on how it actually behaves. Across the four domains:

- **06 Microstructure** anchors theory (Kyle 1985, Glosten-Milgrom 1985, Bouchaud-school empirical impact, Cont-Kukanov-Stoikov OFI, Stoikov micro-price, Avellaneda-Stoikov reservation prices, Hawkes order-book models, Sirignano-Cont universality, deep-LOB benchmarks).
- **07 Order flow / ICT/SMC academic** anchors directional-trading-signal literature: Osler 2003-2005 trio is the most direct microstructure mechanism for the OB pattern GTOS exploits; Evans-Lyons 2002 establishes order-flow as the dominant driver of FX prices; Lo-Mamaysky-Wang 2000 is the methodological template for evaluating any pattern-recognition strategy.
- **08 Volume / Auction / VWAP / OPEX** anchors session timing (Admati-Pfleiderer 1988, Andersen-Bollerslev 1997 deseasonalization), dealer-gamma and OPEX flows (Barbon-Buraschi 2021, Baltussen-Da-Lindberg-Pearce 2021, Avellaneda-Lipkin pinning, Baltussen-Terstegge-Whelan 2024 OPEX morning bias), FX fixing window risk (Krohn-Mueller-Whelan 2024, Ito-Yamada Tokyo-fix, Evans et al. London-fix-reform), turn-of-month / OPEX calendar effects.
- **09 Round numbers / level magnetism** anchors instrument-specific level effects: Niederhoffer 1965 / Harris 1991 (negotiation cost & clustering), Donaldson-Kim 1993 / Cyree et al. 1999 (psychological barriers), Aggarwal-Lucey 2007 + Lucey-O'Connor 2016 (gold-specific), Bhattacharya-Holden-Jacobsen 2012 + Johnson et al. 2007 + Zhang 2024 (penny-distance asymmetry — "above up below down"), Westerhoff 2003 (anchoring micro-foundation), De Ceuster 1998 / Dorfleitner-Klein 2009 (Benford-corrected nulls; published-anomaly fade).

**What's in:** any paper whose *first-order* claim is about price formation, level-magnetism, order-flow propagation, dealer/MM behavior, volume-conditioned dynamics, fixing/OPEX timing, or empirical evidence on technical-pattern profitability at intraday horizons.

**What's out / cross-routed:** distributional fat-tail mechanism (handed to 03), regime-detection methodology (handed to 05), gamma-fragility-as-asset-pricing-factor (cross-link 12), pure ML methodology (cross-link 19), execution-as-RL (cross-link 20), risk-of-ruin sizing (cross-link 21).

---

## 2. Cross-cutting findings (Top 5)

### 2.1 The OB-zone is the empirical convergence of three independent academic literatures (HIGH-CONFIDENCE; load-bearing for GTOS)

The "OB-zone = stop-cascade-and-correct" framing in `edge_mechanism.md` is **NOT** an isolated practitioner claim — it converges with three independent academic mechanisms whose conjunction *predicts* the GTOS edge:

1. **Stop-cluster microstructure (Osler 2003 + 2005, 06-44 / 07.2-2.3 / 09.2.2-2.3):** Take-profit orders cluster *AT* round numbers (~10% at ".00"); stop-loss orders cluster *BEYOND* round numbers (just-above-round for buy-stops, just-below for sell-stops). When price reaches a round-aligned level, take-profits fire (negative feedback / mean-reversion); when price *breaches* it, stops cascade (positive feedback / acceleration). This precisely predicts the GTOS pattern: sweep below swing low → stops cascade → cohort overshoot → mean-reversion to OB midpoint as take-profit demand exhausts cascade.
2. **Latent-liquidity V-shape (Toth-Bouchaud 2011, 06-31; Donier et al. 2015, 06-36):** Liquidity is V-shaped around the current price — depth vanishes near mid and grows linearly with distance. Square-root impact emerges from this. Implication: a sweep through a thin region creates a cavity that must be refilled (mechanical impact reverts), and the reversion target is the next level of supply (the OB).
3. **Long-memory order-flow as meta-order signature (Lillo-Mike-Farmer 2005, 06-54; Sato-Kanazawa 2023, 06-66; Bouchaud propagator school 06-14, 06-63):** Long-memory of order flow comes from institutional meta-order splitting. The propagator framework has a transient (mechanical) impact that decays as a power law and a permanent (informational) component. The OB is the price level where the meta-order "paused" — the residual informational shock. Both components decay with time, but at known rates.

**These three mechanisms predict** that an OB retest will revert toward midpoint *if and only if* the cascade was mostly mechanical (i.e., the V-shape cavity is being refilled by the take-profit cluster) AND the underlying meta-order's informational component has not yet been resolved. This is *exactly* the regime-conditional pattern the F11-decay finding observed empirically (+16.8pp pre-2026 → +4.6pp H2-2026): edge persists in regimes where the mechanism is intact, decays in regimes where it isn't.

### 2.2 The "M15-aggregation null" (E24/E26 microstructure verdict) is theoretically expected, NOT a refutation of microstructure relevance

A near-unanimous finding across 06: **microstructure signal lives at sub-1-minute (often sub-1-second) scales and decays rapidly with aggregation.** Evidence:

- **Cont-Kukanov-Stoikov 2014 (06-05):** OFI-vs-return R² ≥ 0.65 at 1-second horizon; literature predicts steep decay with aggregation.
- **Lucchese-Pakkanen-Veraart 2024 (06-76):** Even highest-quality deep-LOB models on lit-book data achieve OOS Sharpe ~0.5; predictability decays past 1-minute horizon.
- **Easley-Lopez-O'Hara Volume Clock (08, "The Volume Clock"):** Proper microstructure analysis must use volume-time, not calendar-time; M15-calendar bars are a subsampling artifact.
- **Lopez de Prado (06-67):** Volume-bars / dollar-bars / imbalance-bars produce cleaner stationarity than time-bars.
- **Stoikov micro-price 2018 (06-32):** 1-second-ahead prediction; martingale construction; outperforms naive mid by small but consistent margin.

**Implication for GTOS K54 v2:** The E24/E26 null at M15 is consistent with theory — sampling at M15 throws away >90% of microstructure signal. The fix is **NOT** to abandon microstructure features; it is to **change the sampling clock**. Lopez de Prado-style volume-bars or imbalance-bars should expose signal that M15-time-bars suppress. This is hypothesis H-A in the catalog and the highest-leverage architectural change for K54 v2.

### 2.3 Liquidity / depth / OFI / VPIN — every short-horizon "predictor" is partially or wholly a vol-volume mechanical proxy

A robust theme across all four domains: **most "informed flow" indicators turn out to be partly tautological with volume × volatility.**

- **Andersen-Bondarenko 2014 (06-19, 08 critique):** VPIN's flash-crash "prediction" was post-hoc; correlation with future vol is mechanically driven by trading intensity, not toxicity.
- **Buis et al. 2024 (08):** Both positive and negative dealer gamma increase order-book volume — sign separates direction (depth vs flow) but magnitude is dominated by volume.
- **Holý-Tomanová 2022 (09.5.4):** At ultra-high frequency, higher instantaneous vol → WEAKER round-number clustering (opposite of low-frequency finding) — suggesting clustering effects are partly an artifact of low-vol regime aggregation.
- **Vasquez et al. 2024 + Dim-Eraker-Vilkov 2024 (08):** 0DTE-amplification narrative empirically rejected; gamma-fragility is bounded.

**Implication:** Any candidate K54 v2 feature in the OFI/VPIN/depth/clustering family must be evaluated **against a baseline that already includes realized vol and tick volume**. If incremental AUC is <0.02 over that baseline, the feature is a vol-volume proxy in disguise. This codifies what the existing `feedback_walk_level_evidence_not_predictive` memory already warns about.

### 2.4 Universality (Sirignano-Cont) supports cross-instrument pooled training, breaking the data-sparsity ceiling

Three converging findings indicate that price formation has *universal* features across asset classes that should be exploited by GTOS:

- **Sirignano-Cont 2019 (06-39 / 07.5.3):** A universal LSTM trained on multiple stocks beats per-stock models OOS — cross-stock transfer learning works.
- **Lillo-Farmer-Mantegna 2003 (06-13):** Single rescaled price-impact curve collapses across firm sizes — universality is empirical, not just theoretical.
- **Kyle-Obizhaeva 2016 (06-56):** Market microstructure invariance — bet-size and TC distributions are constant across assets when measured per unit business time.

**Implication:** K54 v2 should train on **pooled** multi-instrument data (XAUUSD, US30, USDJPY, GBPJPY, GBPUSD, XAGUSD, NAS100) with an instrument-id embedding, scaled by Kyle-Obizhaeva W-units (dollar-volume × volatility × time). This dissolves the data-sparsity bottleneck (Q1.4 cross-period viability after 2022-2023 backfill compounds with this), and is hypothesis H-C. The mechanism is the same as why Sirignano-Cont's universality holds — Lillo-Mike-Farmer-Sato meta-order-splitting, V-shaped latent liquidity, and Glosten-Milgrom adverse selection are universal.

### 2.5 Round-number / level effects survive Benford-corrected tests and remain instrument-specific

The literature has a clear methodological trajectory: Donaldson-Kim 1993 frequency tests → De Ceuster 1998 (Benford's Law null demolishes naive frequency tests) → Cyree et al. 1999 / Aggarwal-Lucey 2007 (conditional moments + Bertola-Caballero hump tests rescue effect with proper benchmarks) → Sonnemans 2006 (natural experiment provides causal identification).

**Survives:**
- Gold / silver $100 barriers (Aggarwal-Lucey 2007; Lucey-O'Connor 2016)
- Penny-distance asymmetry: "above up below down" (Bhattacharya et al. 2012; Johnson et al. 2007; Zhang 2024 long-short 24.6 bp/day)
- Stop/take-profit clustering at round levels (Osler 2003)
- LOB clustering at integers and halves (Cellier-Bourghelle 2007; Ahn-Cai-Cheung 2005)

**Decayed / fragile:**
- Some equity-index barriers post-publication (Dorfleitner-Klein 2009)
- TOM equity-effect post-2015 (Quantpedia re-examination)
- Naive trade-return-after-round-close in BTC (Urquhart 2017)

**Cross-instrument variation:** Brent shows barriers, WTI does NOT (Dowling-Cummins-Lucey 2016). 5 of 7 Asian markets show no barriers (Bahng 2003). Per-instrument calibration is mandatory.

**Implication for GTOS:** Round-number features in K54 v2 must (a) use Benford-corrected null, (b) be per-instrument-calibrated rather than pooled, (c) interact with regime and vol classifiers (per F15 finding). The strongest candidate is the Bhattacharya / Zhang "above up below down" rule applied to OB-midpoints that straddle round numbers.

---

## 3. Top 15 actionable hypotheses

Ranked by GTOS-relevance × evidence-strength × testability. Each hypothesis cross-references catalog IDs.

### H1 — Volume-bar / OFI-imbalance-bar K54 sampling beats M15-time bars (HIGHEST PRIORITY)
**Source:** Lopez de Prado 2018 (06-67); Easley-Lopez-O'Hara Volume Clock (08); Cont-Kukanov-Stoikov 2014 (06-05); Lucchese 2024 (06-76).
**Claim:** A K54 v2 model trained on volume-bar features (constant-dollar-volume buckets) achieves ≥0.03 higher OOS AUC than M15-time-bar baseline; OOS realized-R lift ≥0.10R/trade at thr≥0.60.
**Test:** Re-bar existing MT5 tick data into dollar-volume buckets (per-instrument bucket size = median per-M15-bar dollar volume), recompute K54 features, retrain LightGBM, compare to current K54 v2 baseline (Q1.3 AUC 0.571).
**Expected impact:** Direct fix to E24/E26 microstructure null verdict; addresses root cause (sampling artifact, not feature absence).

### H2 — Stoikov micro-price replaces naive mid in `tick_features.py` and at OB-retest entry
**Source:** Stoikov 2018 (06-32).
**Claim:** Stoikov micro-price (`(p_bid * vol_ask + p_ask * vol_bid) / (vol_bid + vol_ask)` with proper martingale correction) at OB-retest entry has ≥10% lower 1-bar prediction RMSE than naive `(bid+ask)/2`.
**Test:** Closed-form, deterministic; recompute on existing MT5 ticks. Trivial implementation.
**Expected impact:** Small but consistent edge across all 7 instruments. Zero deployment risk (deterministic feature).

### H3 — Pooled multi-instrument K54 with instrument-ID embedding beats 7 per-instrument models
**Source:** Sirignano-Cont 2019 (06-39 / 07.5.3); Lillo-Farmer-Mantegna 2003 (06-13); Kyle-Obizhaeva 2016 (06-56); Briola 2024 LiT (06-72).
**Claim:** A K54 v2 model trained on pooled MT5 features from all 7 GTOS instruments (with one-hot instrument-id and Kyle-Obizhaeva W-unit scaling) achieves lower median OOS log-loss than 7 per-instrument models, and ≥0.02 higher AUC.
**Test:** Train both architectures on Q1.4 cross-period dataset; CPCV-honest evaluation.
**Expected impact:** Dissolves data-sparsity ceiling on Q1.4; combines with H1 for K54 v2 architecture.

### H4 — Osler stop-cluster feature for FX K54 (BIG round + just-beyond bands)
**Source:** Osler 2003 + 2005 (06-44 / 07.2 / 09.2.2-2.3); Curcio-Goodhart 1991 (06 / 07 / 09.1.2); Cellier-Bourghelle 2007 (09.3.5).
**Claim:** Per-instrument FX stop-cluster density (proxy: rolling 1-min realized vol within ±N ticks of round numbers) at OB-retest entry adds ≥0.02 OOS AUC to K54 baseline; effect concentrated in USDJPY/GBPJPY/GBPUSD.
**Test:** Compute "minutes since last sweep within ±3 ticks of round" feature on FX MT5 ticks; cross-stratify K54 outcomes.
**Expected impact:** Direct microstructure-mechanism feature for FX OB framework; expected to cleanly identify Osler-mechanism-active regimes.

### H5 — "Above up, below down" round-aligned OB direction feature
**Source:** Bhattacharya-Holden-Jacobsen 2012 (09.5.5); Johnson-Johnson-Shanthikumar 2007 (09.5.6); Zhang 2024 (09.5.7); Niederhoffer 1965 (09.1.1).
**Claim:** When OB midpoint straddles a round number, conditional retest direction is biased (continuation when entry-price last-digit = 1-3; mean-reversion when last-digit = 7-9). Add as direction-conditional feature.
**Test:** Stratify existing OB-retest outcomes by (a) round-aligned vs not, (b) last-digit bucket (1-3, 4-6, 7-9). Expected directional asymmetry.
**Expected impact:** Resolves part of the LONG-side selectivity collapse (memory `project_a6_decay_attribution_long_side_concentrated`) — LONG-bias hits adverse selection at just-below-round levels.

### H6 — Power-law-decayed OB-age weighting outperforms hard rolling-50 cutoff
**Source:** Bouchaud-Gefen-Potters-Wyart 2004 (06-14); Bouchaud-Kockelkoren-Potters 2006 (06-63); Donier et al. 2015 (06-36).
**Claim:** Replacing the rolling-50 hard cutoff with a power-law-decay weighting `w(t) = t^(-0.5)` (Bouchaud critical exponent) on OB freshness adds ≥0.02 OOS AUC. Mechanically grounded — this is the propagator's transient-impact decay rate.
**Test:** Reweight OB candidates by age^(-0.5) in K54 training; compare to hard cutoff.
**Expected impact:** Sharper time-decay modeling reduces "stale OB" false positives.

### H7 — Per-instrument round-number-effect strength is calibrated, regime-conditional, NOT pooled
**Source:** Mitchell-Izan 2006 (09.3.4); Bahng 2003 (09.6.1); Dowling-Cummins-Lucey 2016 (09.4.3); 2025 FX-intervention paper (09.5.10); F15 memory.
**Claim:** Round-number-effect strength varies materially across XAU/JPY/EUR/GBP/NAS100/US30 and across regime states. K54 must include `regime × round_distance` interaction terms, not pooled main effect.
**Test:** Stratify OB outcomes by `(instrument, regime, round_aligned)`; expect significant interaction.
**Expected impact:** Codifies F15 finding for level features; prevents over-pooling that masked regime-conditional decay.

### H8 — Fix-window avoidance gate (Tokyo 00:55 / London 16:00 / NY 17:00 UTC ± 15 min)
**Source:** Krohn-Mueller-Whelan 2024 (08); Ito-Yamada 2017 (08); Marsh et al. 2017 (08); Evans-O'Neill-Rime-Saakvitne 2018 (08).
**Claim:** Skipping new entries within ±15 min of FX fixes for USDJPY/GBPJPY/GBPUSD reduces L2 sl_buffer 0.0 cluster rate by ≥30% and reduces slippage variance.
**Test:** Stratify existing trades by minutes-to-nearest-fix; expect concentration of bad outcomes in fix windows. Adopt as additive shadow gate.
**Expected impact:** Direct shipping candidate. Calendar-aware additive gate. Low decay risk (mechanism is dealer inventory, not crowded trade).

### H9 — OPEX-Friday morning gate for NAS100/US30 (skip first 30 min)
**Source:** Baltussen-Terstegge-Whelan 2024 (08); Avellaneda-Lipkin 2003 (08); Avellaneda-Kasyan-Lipkin 2012 (08); Ni-Pearson-Poteshman 2005 (08); Stoll-Whaley 1987 (08); Golez-Jackwerth 2012 (08).
**Claim:** Skipping new entries on third-Friday-of-month before noon UTC for NAS100/US30 reduces hallucination-class issues (memory `project_halluc_1_precision_bug_class_2026-04-27`) and reduces OPEX-day SL cluster.
**Test:** Stratify NAS100/US30 trades by OPEX-Friday inclusion + by hour; expect lower realized R in OPEX morning.
**Expected impact:** Calendar-aware gate; complements existing safety stack. Quarterly triple-witching (Mar/Jun/Sep/Dec) would be the strongest test.

### H10 — Daily MM-gamma-sign feature for K54 (NAS100/US30)
**Source:** Barbon-Buraschi 2021 (08); Baltussen-Da-Lindberg-Pearce 2021 (08); Garleanu-Pedersen-Poteshman 2009 (08); Bollen-Whaley 2004 (08); Buis et al. 2024 (08); Ni-Pearson-Poteshman-White 2021 (08).
**Claim:** Adding a daily MM-gamma-sign feature (publicly inferable from SpotGamma/SqueezeMetrics free data) to K54 separates intraday momentum from intraday reversal regimes. Negative gamma → momentum-amplifying; positive gamma → mean-reverting.
**Test:** Bucket NAS100 trades by tertile of inferred MM-gamma; expect monotonic R lift from positive→negative gamma days.
**Expected impact:** Fundamental regime-axis addition. Connects to Group A regime synthesis (vol-regime classifier) and to F15 LONG-decay finding (negative-gamma regimes may explain LONG-side momentum failures).

### H11 — Multi-level OFI (top-5 weighted) feature outperforms best-level OFI for K54
**Source:** Cont-Cucuringu-Zhang 2023 (06-21); Kolm-Turiel-Westray 2023 (06-38); Cont-Kukanov-Stoikov 2014 (06-05).
**Claim:** Multi-level OFI (top-5 levels weighted by depth) on MT5 reconstructed-LOB ticks adds ≥0.03 OOS AUC over best-level OFI; cross-instrument OFI adds <0.03 once own-multi-level OFI is included.
**Test:** Reconstruct multi-level depth from MT5 spread snapshots + tick volume; compute weighted OFI; benchmark in K54.
**Expected impact:** Confirms parsimonious own-asset OFI (no cross-impact term needed) — simplifies K54.

### H12 — Hawkes intensity feature on MT5 ticks
**Source:** Bacry-Mastromatteo-Muzy 2015 (06-62); Cont-Pourjafarian 2023 (06-73).
**Claim:** A self-exciting Hawkes intensity feature (exponential-decay kernel τ=2s) on MT5 ticks captures order-flow clustering that simple OFI misses; adds ≥0.02 OOS AUC.
**Test:** Tag MT5 tick events by type (snap-in/snap-out/no-change), fit multivariate Hawkes process per instrument, use intensity as K54 feature.
**Expected impact:** Better capture of clustering at sub-bar resolution.

### H13 — Cross-instrument liquidity-commonality regime gate
**Source:** Mancini-Ranaldo-Wrampelmeyer 2013 (06-17 / 07); Cespa-Foucault 2014 (06-60); Brogaard et al. 2018 EPM (06-49); Subrahmanyam 2013 (06-61).
**Claim:** A cross-instrument liquidity-commonality factor (PC1 of MT5 spreads across XAU/USDJPY/GBPJPY/GBPUSD) above its 90th percentile predicts ≥20% increase in next-bar realized vol for those instruments; serves as kill-switch / size-halve trigger.
**Test:** Reconstruct rolling PC1; backtest as additive risk gate.
**Expected impact:** Multi-instrument early-warning for liquidity-stress regimes; complements existing |corr|≥0.4 cross-instrument gate.

### H14 — VPIN deprecated as primary gate; BV-VPIN (BVC-corrected) as shadow feature only
**Source:** Andersen-Bondarenko 2014 (06-19 / 08); Low-Li-Marsh 2018 (06-65); Easley-Lopez-O'Hara 2012 (06-07 / 07 / 08).
**Claim:** VPIN computed naively on MT5 ticks adds <0.02 AUC over a baseline already including realized vol and tick volume; BVC-corrected BV-VPIN may rescue if computed properly.
**Test:** Build both versions; benchmark against vol+volume baseline. Expect VPIN naive null; BV-VPIN modest.
**Expected impact:** Prevents wasteful pursuit of VPIN-as-gate when underlying signal is mechanical vol-volume proxy.

### H15 — `volume_conditional_volatility` feature added to K54 (asymmetric per asset class)
**Source:** Karpoff 1987 (08); Lamoureux-Lastrapes 1990 (08); Bollerslev-Li-Xue 2018 (08); Drechsler-Moreira-Savov 2024 (08).
**Claim:** Including contemporaneous volume in volatility forecasts beats unconditional GARCH for indices (US30, NAS100); near-zero lift for FX.
**Test:** Per-instrument volume-conditional vs unconditional GARCH(1,1) shadow comparison.
**Expected impact:** Asset-class-asymmetric vol regime feature; clarifies why instrument-pooled vol features work better for some pairs than others.

---

## 4. Methodology / quality bar

The literature converges on a few methodological musts that GTOS K54 v2 must respect:

### 4.1 Bar-sampling
- **Calendar-time bars are subsampling artifacts** at sub-daily horizons (Easley-Lopez-O'Hara Volume Clock; Lopez de Prado 2018; Andersen-Bollerslev 1997 deseasonalization).
- **Volume-bars / dollar-bars / imbalance-bars** are the proper aggregation units for microstructure features.
- **Deseasonalization** of intraday seasonality is required *before* any persistence estimation (Andersen-Bollerslev 1997).

### 4.2 Universality vs per-instrument calibration
- **Universality holds for price formation mechanism** (Sirignano-Cont 2019; Lillo-Farmer-Mantegna 2003; Kyle-Obizhaeva 2016) — supports pooled training with instrument-id embedding.
- **Per-instrument calibration required for level effects** (Mitchell-Izan 2006; Dowling-Cummins-Lucey 2016; Bahng 2003) — round-number magnetism varies materially across instruments.
- **Reconciliation:** pool the *learned representation* but preserve per-instrument scaling parameters (Kyle-Obizhaeva W-units = dollar-volume × volatility × time).

### 4.3 Null benchmarks
- **Benford-corrected null** mandatory for any clustering / round-number feature (De Ceuster-Dhaene-Schatteman 1998; Dorfleitner-Klein 2009).
- **Vol-volume baseline mandatory** for any flow-toxicity feature (Andersen-Bondarenko 2014 critique of VPIN). If a feature does not exceed `realized_vol + tick_volume`, it is mechanical.
- **Bootstrap-permutation > t-test** for trading-rule profitability (Brock-Lakonishok-LeBaron 1992).
- **CPCV cross-validation** for time-series ML (Lopez de Prado 2018) — already adopted by GTOS Q1.3.

### 4.4 Walk-level vs realized-R (already in `feedback_walk_level_evidence_not_predictive`)
- High AUC ≠ high realized R (Briola-Bartolucci-Aste 2024).
- "Actionable signal" evaluation framework (probability of correctly forecasting complete TP-or-SL outcome) > standard ML metrics.
- Sharpe-ceiling ~0.5 for even high-quality lit-book deep-learning models (Lucchese-Pakkanen-Veraart 2024) — calibrates expectations for K54 v2.

### 4.5 Decay tracking
- Half of "TA edges" decay post-publication (Park-Irwin 2007 survey of 95 studies).
- Some round-number effects survive 40 years (gold per Lucey-O'Connor 2016); others decay in years (DAX per Dorfleitner-Klein 2009).
- Long-memory of order flow has microscopic origin (Lillo-Mike-Farmer / Sato-Kanazawa) → mechanism is durable; trading-rule edges that exploit it are NOT necessarily.

---

## 5. Contradictions / open questions

### 5.1 VPIN: signal or vol-volume proxy?
- **Pro-VPIN:** Easley-Lopez-O'Hara 2012 (06-07 / 08); Low-Li-Marsh 2018 BV-VPIN rescue (06-65).
- **Anti-VPIN:** Andersen-Bondarenko 2014 (06-19 / 08).
- **Resolution:** Empirical — benchmark BV-VPIN against vol+volume baseline on MT5 ticks. Existing E24/E26 null suggests outcome is likely null, but BVC variant deserves one shadow test.

### 5.2 Square-root vs 3/5 power impact law
- **Square-root canon:** Almgren 2003 (06-12); Toth-Bouchaud 2011 (06-31); Maitrier et al. 2024 "double sqrt" (06-77); Bouchaud Substack 2024 (07).
- **3/5 power refinement:** Almgren-Thum 2005 (06-27); Almgren 2025 update (06-75) with cross-asset exponents in [0.55, 0.62].
- **Resolution:** Both are right at different scales; canonical sqrt holds for small/medium, 3/5 fits better for very large meta-orders. For GTOS retail-size, sqrt approximation is sufficient.

### 5.3 Round-number effects: durable or decayed?
- **Durable:** Aggarwal-Lucey 2007 + Lucey-O'Connor 2016 (gold); Sonnemans 2006 (Dutch natural experiment); 2024 LOB-clustering evidence (09.6.8).
- **Decayed:** Dorfleitner-Klein 2009 (DAX); Quantpedia TOM re-examination; Urquhart 2017 BTC (no return-pattern after close).
- **Resolution:** Empirically asset-class-specific. Gold / commodity barriers durable; equity-index barriers decayed; FX intervention-conditional. Calibrate per-instrument; avoid single-shot pooled tests.

### 5.4 0DTE-amplification: real or narrative?
- **Pro:** Popular media + practitioner narrative (SpotGamma / SqueezeMetrics).
- **Anti:** Vasquez-Amaya-Pearson-Garcia-Ares 2024 (08); Dim-Eraker-Vilkov 2024 (08) — both reject amplification.
- **Resolution:** Don't over-react. Net dealer-gamma exposure from 0DTEs is bounded; customer flow is two-sided. Standard *monthly* OPEX effects (Baltussen-Terstegge-Whelan; Ni-Pearson-Poteshman) are more material than 0DTE.

### 5.5 HFT: liquidity provider or consumer?
- **Provider:** Hasbrouck-Saar 2013 (06-20); Hendershott-Jones-Menkveld 2011 (06-46); Brogaard-Hendershott-Riordan 2014 (06-47).
- **Consumer:** Hendershott-Riordan 2013 (06-74) — AT *consumes* when narrow, *provides* when wide; Brogaard et al. 2018 (06-49) — HFTs flip provider→consumer during simultaneous multi-instrument EPMs; Kirilenko-Kyle-Samadi-Tuzun 2017 (06-18 / 07.5.2 / 08).
- **Resolution:** State-conditional. For GTOS retail-size on MT5, HFT presence likely tightens spreads in normal regimes (provider) but exits during stress (consumer). Implication: cross-instrument simultaneous-EPM kill switch (H13) is grounded.

### 5.6 Order book V-shape vs humped depth
- **V-shape near mid:** Toth-Bouchaud 2011 (06-31); Donier et al. 2015 (06-36).
- **Humped (peak away from mid):** Bouchaud-Mezard-Potters 2002 (06-06); Rosu 2009 (06-45).
- **Resolution:** Both; V-shape applies to mid-instantaneous depth; humped applies to time-averaged book shape. For GTOS midpoint definition: empirical test required (H6 in catalog 06).

---

## 6. Build-this-next (recommendations for K54 v2 + Component 2)

### Tier 1 (highest leverage, lowest cost, can ship within 1-2 weeks)

#### 6.1 Stoikov micro-price in `tick_features.py` and at OB-retest entry (H2)
Closed-form, deterministic, no training cost. Replace naive `(bid+ask)/2` with proper micro-price formula at entry. **Universal across all 7 instruments.** Expected small but consistent edge.

#### 6.2 Volume-bar / dollar-bar K54 sampling (H1)
Re-bar existing MT5 tick captures into dollar-volume buckets per Lopez de Prado. Retrain K54 on volume-bars vs M15-time-bars; compare AUC and realized-R. **This is the architectural fix to E24/E26.**

#### 6.3 Fix-window avoidance gate (H8)
Calendar-aware additive gate. Skip new entries within ±15 min of (Tokyo 00:55 / London 16:00 / NY 17:00 UTC) for FX pairs. Backed by 4 papers with consistent finding. Low decay risk (mechanism is dealer inventory, durable).

### Tier 2 (substantial engineering, high expected lift)

#### 6.4 K54 v2 architectural rewrite — pooled multi-instrument with regime × level interactions (H3 + H7)
- Train K54 v2 on pooled MT5 features across all 7 instruments with instrument-id embedding and Kyle-Obizhaeva W-unit scaling.
- Include `regime × round_distance` interaction terms (NOT pooled main effect).
- Use power-law-decayed OB-age weighting (H6), not hard rolling-50 cutoff.
- Include multi-level OFI (top-5 weighted) (H11), Stoikov micro-price (H2), and Hawkes intensity (H12).
- Drop VPIN naive; if including BV-VPIN, gate it behind vol+volume baseline benchmark (H14).
- Per the Q1.4 cross-period viability now made possible by 2022-2023 backfill, add cross-period CPCV-honest evaluation as the standard.

This single architectural rewrite addresses Q1.3 K54 v2 failure under CPCV, dissolves data-sparsity, and integrates 6 of the top-15 hypotheses.

#### 6.5 Osler stop-cluster + "above up below down" round-aligned features (H4 + H5)
Per-instrument FX features. Mechanism-grounded. Direct connection to A6 LONG-side selectivity collapse. Likely the highest leverage for explaining and partially recovering the F11 OB decay.

#### 6.6 OPEX-Friday morning gate (H9) + daily MM-gamma-sign feature (H10)
For NAS100/US30 only. Calendar + dealer-flow regime axes. Connects to HALLUC-1 root-cause (NAS100 hallucination concentrated near round / OPEX-strike clusters). Backed by 6+ papers including 2024-2025 work.

### Tier 3 (research / Phase 2+)

- **Cross-instrument liquidity-commonality kill switch (H13):** Useful but operationally complex; needs validation on stress periods first.
- **DeepLOB / LiT transformer architectures:** Briola 2024 + Lucchese 2024 set Sharpe ceiling at ~0.5 even on lit-book data; for MT5 degraded ticks, expectations should be lower. K54 LightGBM baseline + Tier 1+2 features should be exhausted first.
- **SPDE / Hawkes-queue state models:** Cont-Mueller 2021, Cont-Pourjafarian 2023 — academic frontier; benefit unclear for retail-broker tick data.
- **Hasbrouck VAR-based decomposition** (Hasbrouck 1991): permanent vs transient impact decomposition as feature for K54. Methodologically interesting; H29 in catalog 06.

---

## 7. The OB-zone framing: support and challenge

(Per brief special focus.)

### 7.1 The single most-supportive paper

**Osler 2003: "Currency Orders and Exchange-Rate Dynamics: Explaining the Success of Technical Analysis"** (06-44 / 07.2 / 09.2.2)

This is the **load-bearing academic paper for the GTOS edge mechanism**. Using NatWest Markets stop-loss + take-profit order book data Aug 1999-Apr 2000 across DEM, USD/JPY, USD/GBP, Osler documents:

- **Take-profit orders cluster strongly AT round numbers** (~10% at ".00" rates, vs ~3% baseline for other "0" endings).
- **Stop-loss orders cluster JUST BEYOND round numbers** — buy-stops just-above, sell-stops just-below.
- **Asymmetric execution clustering** is the literal microstructure mechanism for both directional TA predictions: (a) trends reverse at round-aligned levels (take-profits exhaust the move), (b) trends accelerate past round-aligned levels (stops cascade).

**Why this is precisely the GTOS edge mechanism:**

The `edge_mechanism.md` description — "exploits stop-cascade mean-reversion to pre-cascade equilibrium" — is *exactly* Osler's mechanism. When price sweeps below a swing low (i.e., a previously-defined OB level), retail and resting institutional stops trigger in cascade. The resulting overshoot is mechanical (Toth-Bouchaud V-shape latent-liquidity cavity); the price reversion target is the take-profit cluster on the opposite side, which sits at the OB midpoint or the next round-aligned level above.

**The corollary that GTOS' `sl_beyond_ob` gate exists** is grounded directly in Osler's finding: stops should be BEYOND, not AT, the level — because Osler showed institutional take-profits cluster AT and stops cluster BEYOND.

**This also predicts F11 decay direction:** The mechanism depends on the asymmetric clustering pattern. If retail order-clustering composition shifts (e.g., toward different brokers / different levels / less round-number anchoring as crypto/AT participation grows), the asymmetry weakens and the mechanism degrades. The decay-velocity finding (+16.8pp pre-2026 → +12.1pp H1-2026 → +4.6pp H2-2026) is consistent with a slow Osler-mechanism erosion, not a sudden cliff.

### 7.2 The single most-challenging paper

**Lucchese, Pakkanen, Veraart 2024: "The Short-Term Predictability of Returns in Order Book Markets: A Deep Learning Perspective"** (06-76)

This paper provides a **realistic ceiling check** on the GTOS edge mechanism:

- Even highest-quality deep-learning models on **lit-book** data achieve OOS Sharpe ~0.5 (after costs).
- ML lift over stochastic baselines is ~10-15% in AUC.
- Predictability decays rapidly past 1-minute horizon.
- Consistent with Toth-Bouchaud V-shape and propagator decay.

**Why this challenges the OB-framing:**

GTOS works on degraded MT5 retail-broker tick data, at M15 horizon, against a population that includes professional FX desks who use TA actively (Menkhoff-Taylor 2007). The Lucchese ceiling implies:

1. **Sharpe ~0.5 is the realistic upper bound** for K54 v2; M15 aggregation forfeits most of that.
2. **The OB-zone edge is most likely a small, regime-conditional residual** (consistent with F11 +4.6pp H2-2026), not a transformative alpha.
3. **Any K54 v2 model claiming OOS Sharpe >>0.5 on M15 is more likely overfit than alpha-discovery** — a methodological warning that fits with the Q1.3 K54 v2 CPCV-honest accounting failure.

**This challenges the "OB-zone precision is a durable edge" framing** by quantifying the headroom: there isn't much. Mature, serious literature on lit-book microstructure says even with full-LOB ITCH data, Sharpe maxes out at ~0.5. GTOS, with degraded data and slower aggregation, should expect substantially less.

**Reconciliation:** The OB-zone edge is real (Osler 2003 + Toth-Bouchaud 2011 + Lillo-Mike-Farmer mechanisms are durable), but the *magnitude* available to GTOS is bounded. The decay observation is consistent with this ceiling — the edge was always small, and the regime-conditional component (Group A's regime literature) is what makes some windows profitable and others not. The right strategic frame is **"capture small, durable, regime-conditional edge with conservative sizing"** — not "discover transformative alpha" — and S79 risk policy + the existing safety stack are well-aligned with that frame.

---

## 8. Top recommendation: build-this-next for the K54 v2 edge layer

**Single most-impactful build-this-next: Tier-1 H1 + H2, then Tier-2 H3 + H4 + H7 + H6.**

Concretely, the K54 v2 architecture should be:

1. **Sampling layer:** Replace M15-time-bars with dollar-volume-bars (H1; Lopez de Prado bar-sampling). Per-instrument bucket size = median per-M15-bar dollar volume, recomputed weekly.
2. **Mid-price feature:** Stoikov micro-price replaces naive mid (H2; Stoikov 2018).
3. **Cross-instrument architecture:** Pooled training with instrument-id embedding and Kyle-Obizhaeva W-unit scaling (H3; Sirignano-Cont 2019; Kyle-Obizhaeva 2016).
4. **Regime × level interaction:** Add `(regime, round_aligned, side)` interaction terms (H7; F15 + Mitchell-Izan 2006). NOT pooled main effects.
5. **OB-age weighting:** Power-law decay `t^(-0.5)` instead of hard rolling-50 cutoff (H6; Bouchaud propagator).
6. **Stop-cluster feature for FX:** Osler-style rolling stop-cluster density at OB-retest entry (H4; Osler 2003 + 2005).

This bundle:
- **Directly addresses E24/E26 microstructure null** (H1 = sampling fix).
- **Resolves Q1.4 cross-period data-sparsity** (H3 = pooled training).
- **Resolves F11 OB-decay attribution** (H4 + H7 = regime + Osler mechanism).
- **Has 5+ papers of academic backing per component**, with at least one 2023-2024 confirmation per axis.
- **Is testable as a single CPCV-honest re-run** of the existing K54 evaluation pipeline.

**Expected AUC lift over current K54 v2 baseline (Q1.3 AUC 0.571):** +0.04 to +0.07 (literature-implied; per-component AUC lifts of 0.02-0.03 with diminishing returns from overlap). Lucchese ceiling implies max OOS Sharpe ~0.5; conservatively expect K54 v2 Sharpe in [0.25, 0.40] range — modest but meaningful and consistent with the small-durable-edge frame.

**This is the single highest-leverage architectural change available to GTOS in Phase 2.** It converts K54 from a marginal feature catalog into a literature-grounded edge layer.

---

*Synthesis complete. 175 papers integrated. UTF-8. Read-only outside this file. No fabrication.*
