# GTOS ML Research Program — HYPOTHESIS BACKLOG (Phase 3 polished view)

**Author:** Phase 3 Hypothesis Generation Agent (Opus 4.7, max effort)
**Date:** 2026-04-29
**Inputs:** `research/ml_program/MASTER_BACKLOG.md` (178 raw items, stable IDs); 6 Phase-2 syntheses (`literature/synthesis/group_a..f`) covering 22 domains / ~1,100+ papers; Q1.3 audit pack (`audit/Q1_3_POSTMORTEM_SYNTHESIS.md`, `AMBIGUITIES_AND_OPEN_QUESTIONS.md`, `architecture_ab.md`, `cross_period_replication.md`, `statistical_reevaluation.md`, `data_backfill_2022_2023.md`).
**Output discipline:** UTF-8, no fabrication, every hypothesis cites ≥3 evidence sources, references MASTER_BACKLOG.md IDs throughout.

---

## Section 1 — Methodology

### Composite scoring

Every hypothesis is scored on four 1-5 axes; **composite = feasibility × expected_impact × evidence_strength × decay_velocity_priority** (max 625, min 1). Multiplicative deliberately: a hypothesis must be strong on ALL four to rank high. A 1 on any axis collapses the score, which is the right Bayesian behaviour for the Q1.4 funding decision.

| Axis | 1 | 3 | 5 |
|------|---|---|---|
| **Feasibility** (engineering + data realism) | New infra + new data feed + multi-month build | Tractable on current GTOS infra in 1-2 weeks | Closed-form, deterministic, drop-in |
| **Expected impact** (under 50% literature-realization haircut per `MASTER_BACKLOG.md` planning rule) | <0.005 AUC or <0.02R/trade | +0.02 AUC or +0.05R/trade | +0.05 AUC or +0.15R/trade or kill-switch class |
| **Evidence strength** (citation depth + cross-domain corroboration + mechanism clarity) | 1 paper, single domain | ≥3 papers, 1-2 domains | ≥5 papers, ≥3 domains, mechanism-grounded |
| **Decay-velocity priority** (CEO-explicit per memory `feedback_decay_is_ceo_number_one_concern`) | Long-cycle research (Q3+) | Q2 prep | Decay-defending edge or new-edge-discovery vehicle |

### Tie-breakers (when composites equal)

1. **Composability** with other top-N hypotheses (a hypothesis that bundles cleanly with three siblings beats an equally-scored standalone).
2. **Q1.3 failure-mode reversibility** — does this hypothesis directly attack a documented Q1.3 K54 v2 failure mode (CF-1..CF-11 in `AMBIGUITIES_AND_OPEN_QUESTIONS.md`)?
3. **Subscription-bounded execution** (no Anthropic API consumption beyond research dispatches).
4. **Cross-period robustness viability** — feasibly testable under the new 7-of-7 cross-period regime opened by `data_backfill_2022_2023.md`.

### Discipline gates inherited from MASTER_BACKLOG.md (apply to every Q1.4 candidate)

- Pre-registration in `PRE_REGISTERED_HYPOTHESES.md` for primary hypotheses.
- Paired-fixed-HP CPCV with K=6/N=2 + 7-day purge / 1-day embargo.
- **CPCV-honest training-overlap-weighted SE** (NOT Stouffer naive — `audit/statistical_reevaluation.md` showed Stouffer p=0.0015 was an artifact at CPCV-honest p=0.675).
- DSR + PBO < 0.40 + effective-N (Lopez-de-Prado-Bailey) per Group A M1.
- B=1000 null-shuffle empirical p ≥ 0.99.
- Cross-period robustness gate: lift sign preserved on 2026-Q1+ test split AND on 2022-2023 → 2024-2026 split (now feasible per backfill).
- Stationary block bootstrap (Politis-Romano) for trade PnL CIs (per Group A M5).
- Failure protocol: pass → ship; fail → KILLED memo + re-spec or close.

### Cohort baseline (post-backfill)

- Q1.3 cohort: n=528 trades.
- Post-backfill (`audit/data_backfill_2022_2023.md`): +1,798 mechanical OB-retest trades (XAUUSD 394, XAGUSD 418, USDJPY 376, GBPUSD 400, NAS100 210), 99.1% regime-tagged, 7-of-7 cross-period feasible.
- **Q1.4 cohort target: n ≈ 2,326** (528 Q1.3 + 1,798 backfill). Rows-per-feature ratio at the 1,234-feature catalog: 1.88 (vs Q1.3's 0.43). Still in high-dim regime; still need feature-screening / pruning.
- This is the single highest-impact data shift since the program began. Every hypothesis below assumes Q1.4-cohort scale.

### Ranking selection rules

- **Top 10 (Section 2)** = Q1.4-candidate-ready. Composite ≥ 250 (4-axis geometric-mean ≥ ~4.0). Each must be a coherent dispatch unit (single agent or small parallel-agent team, not a quarter-long programme).
- **Tier 2 (Section 3, ranks 11-30)** = composite 100-249, Q2-Q3 candidates. Same 4-axis schema, tighter prose.
- **Architectural composites (Section 4)** = MASTER_BACKLOG.md Section B (B-1..B-8) bundles, validated / refined.

---

## Section 2 — TOP 10 Q1.4-candidate-ready hypotheses

Numbered H-1 through H-10. Each references MASTER_BACKLOG.md IDs and cites ≥3 evidence sources across syntheses + GTOS findings.

---

### H-1 — K54 v3 master bundle: Architecture A + meta-labeling head + per-fold screening + cohort pooling on n=2,326

**1-line description.** Replace K54 v2 with Arch-A global LightGBM (per-fold top-100 screening, de Prado AFML §8.5) + meta-labeling secondary classifier (Lopez-de-Prado triple-barrier) trained on the post-backfill 7-of-7 cross-period cohort with Kyle-Obizhaeva W-unit pooling.

**Master backlog IDs.** Bundles **K-11** (per-fold top-100 screening) + **K-12** (meta-labeling head over 3A) + **K-13** (triple-barrier labels) + **K-15** (TreeSHAP-stability pruning) + **K-5** + **K-6** (Kyle-Obizhaeva pooling + multi-instrument training) + **K-18** (master bundle reference) + **B-1** (composite) + **D-11** (backfill QA) + **M-7** (CPCV-honest training-overlap SE) + **M-12** (effective-N tracker) + **M-13** (PBO baked-in).

**Evidence sources.**
- Group F §2 Rank 1 — "Per-regime LightGBM with TreeSHAP-stability feature pruning + Lopez-de-Prado meta-labeling head" (5 anchor papers: Gu-Kelly-Xiu 2020 RFS, Lopez de Prado 2018 AFML, Lundberg-Lee 2017 SHAP, Friedman 2001 GBT, Hudson-Thames 2022 meta-label replication).
- Group A CC6 — "CPCV + triple-barrier + meta-labeling is the canonical ML pipeline for finance" (AFML Ch 7-12; Joubert et al. 2024 three-types-of-backtests; Arian-Norouzi-Seco 2024 ML backtest).
- Group B §2.4 — Sirignano-Cont 2019 universal LSTM cross-stock generalization + Kyle-Obizhaeva 2016 W-unit invariance + Lillo-Farmer-Mantegna 2003 universal price-impact: pooled-instrument K54 dissolves data-sparsity ceiling.
- `audit/architecture_ab.md` — Arch A AUC 0.5625, lift +0.0492, PBO 0.20, gate (a) PASS at Stouffer p=9.4e-5; cross-period concern primary.
- `audit/data_backfill_2022_2023.md` — 1,798 new trades unlocking 7-of-7 cross-period; Q1.4-cohort n=2,326.
- Group F §3 — meta-labeling concrete spec exactly matches J46-J49 triple-barrier outcomes (memory `project_j46_j49_position_mgmt_findings`).

**GTOS subsystem affected.** K54 v3 (replaces K54 v2); production architecture upgrade Component 3A → Component 3D (meta-label head) → Component 4 sizing; touches `src/research_infra/` modeller pipeline and (downstream) `risk_per_trade_pct` substitution at execution.

**Feasibility (5).** All-tree LightGBM stack already implemented; Arch A code shipped (`research/ml_program/models/k54_v2_arch_a/`); per-fold screening proven; meta-labeling is one additional secondary LightGBM; W-unit normalization is a dollar-vol × volatility scaling formula; 2022-2023 backfill DONE per `data_backfill_2022_2023.md`. Subscription-bounded; ~3-5 hours wallclock.

**Expected impact (5).** Composite of three lifts:
- Arch A → Arch A+screening on n=2,326 (vs n=528): expected +0.02-0.04 AUC over Arch A's 0.5625 (rows-per-feature 1.88 vs 0.43 closes the high-dim noise floor).
- Meta-labeling head: literature predicts +5-15% F1 lift on the binary skill classifier (Hudson-Thames 2022); GTOS-translation to realized-R: +0.05-0.10R/trade per Group F §3.
- Pooling under Kyle-Obizhaeva W-units: Group B §2.4 + Group F Rank 2 predict +0.02-0.05 AUC for data-poor cells (USDJPY/GBPJPY/GBPUSD/XAGUSD).
**Headline target after 50% realization haircut: K54 v3 mean AUC ≥ 0.58 on full Q1.4 cohort + lift ≥ +0.05R/trade vs S79-uniform sizing on H2-2026 holdout.** This single bundle closes the Q1.3 failure mode and lands K54 in production.

**Decay-velocity priority (5).** Direct CEO #1 concern. K54 v3 IS the regime-aware decay-defending architecture. Phase 2 rank #1 in CLAUDE.md. Explicitly displaces Q1.3's failed v2.

**Evidence strength (5).** 12+ papers across 3 syntheses (A/B/F) + 3 audit artifacts + 4 memories. Mechanism is fully grounded: Sirignano-Cont universality + Lopez-de-Prado meta-labeling + Lo-AMH decay frame + Kyle-Obizhaeva invariance.

**Composite score: 5 × 5 × 5 × 5 = 625.**

**Data requirements.**
- Cohort: 2,326 trades from `data/historical_2022_2023/trade_cohort.csv` (1,798) + Q1.3 cohort (528). Schema-aligned per backfill audit.
- Features: existing 1,234-feature scout matrix, recomputed across backfill window; Kyle-Obizhaeva W-units = `dollar_volume × realized_vol × time` per instrument.
- Triple-barrier labels: extract TP/SL/TIMEOUT outcome from `_trade_index.json` + `trades_unified.csv` per Group F §3 spec.
- New: Stoikov micro-price (K-4 / H-2 below) feature for instruments with tick coverage (NAS100, US30_cash) — drop-in if available, else flag NaN.

**Methodology.**
- Paired-fixed-HP CPCV (K=6, N=2) with 7-day purge / 1-day embargo (matches Q1.3).
- CPCV-honest training-overlap-weighted SE per Group A M7 + `audit/statistical_reevaluation.md`.
- Per-fold top-100 screening LightGBM → final fixed-HP LightGBM.
- Meta-labeling secondary: focal loss γ=2, α=0.25 (Group F §3 spec).
- Cross-period robustness gates (TWO splits): (i) train 2026 / test 2026-Q1+ (Q1.3 split); (ii) train 2022-2023 / test 2024-2026 (the new gate enabled by backfill).
- Promotion gate: DSR-corrected p < 0.01 + PBO < 0.40 + B=1000 null p ≥ 0.99 + lift sign preserved on BOTH cross-period splits.
- Stationary block bootstrap on lift CIs (Politis-Romano).

**Expected wallclock.** 4-6 hours for the modeller dispatch + 2-4 hours for the meta-labeling fit + 2-3 hours for cross-period validation = single-day Q1.4 deliverable. Subscription-only.

**Composability.** Bundles directly with H-3 (vol-conditioning overlay supplies sizing feature for meta-label head); H-4 (Stoikov micro-price drops in as additive feature); H-7 (regime classifier upgrade supplies regime-prob vector to K54 v3); H-9 (DSR-discipline gates this hypothesis). NOT compatible with stripping Component 3A (the AI primary direction is the meta-label PRIMARY signal).

---

### H-2 — Component 3C Vol-Conditioning Overlay (Barroso-Santa-Clara port)

**1-line description.** Insert a Component 3C between Component 3A (AI gate) and Component 4 (Execution): realized-vol-percentile + VRP + regime-persistence → sigma multiplier ∈ [0.5, 2.0] applied to S79 risk_per_trade_pct.

**Master backlog IDs.** Bundles **V-1** + **V-2** + **V-3** + **V-4** + **V-5** + **V-6** + **V-9** (composite reference) + **B-2** (architectural composite) + **R-7** (vol-scaled sizing across 7 instruments) + **P-1** (Component 3C implementation).

**Evidence sources.**
- Group D §3 + §4 — explicitly names "Volatility-Conditioning Overlay" as the highest-EV / lowest-cost addition; backed by ≥6 papers (Barroso-Santa-Clara 2015 vol-managed-momentum Sharpe 0.53→0.97; Daniel-Moskowitz 2016 forecastable momentum-crashes; Wood-Roberts-Zohren 2022; Geczy-Samonov 2016; Nagel 2012; Bardgett-Gourier-Leippold 2019 VVIX).
- Group E F-4 + H-E7 — Moreira-Muir 2017 vol-management 20-40% Sharpe gain OOS; explicit S79 Phase 2 spec recommendation.
- Group A Rank 1 + CC1 + CC4 — rough-vol H~0.1 + fat tails imply current ATR-based sizing is implicit-Gaussian-under-heavy-tailed-reality. McNeil-Frey GARCH-EVT prescription.
- Memory `project_distributional_findings` — gold ξ=0.35, GARCH 0.9906, 6.2× more 3σ events. S79 uniform_fn 2% IS the Moreira-Muir target.
- `audit/Q1_3_POSTMORTEM_SYNTHESIS.md` — Q1.3 K54 v2 top single feature was `vol__h1_range_over_mean_50` (volatility-family). Vol regime IS the load-bearing signal.

**GTOS subsystem affected.** New `src/components/vol_conditioning.py` Component 3C; touches S79 risk-policy substitution path; reads from `regime_classifier.py` + new realized-vol percentile computation; writes sigma multiplier to execution.

**Feasibility (5).** Zero new ML infra; all features computable from existing OHLCV; Component 3C is a deterministic sigma-rule first (later ML-trainable per H-1 meta-label head). 2-3 days eng for the rule-based version; A/B-testable in shadow mode immediately.

**Expected impact (5).** Literature-implied +30-50% Sharpe lift (Barroso-Santa-Clara). Apply 50% realization haircut → +15-25% Sharpe. Bundles multiplicatively with H-1 meta-label head (sigma is the head's output unit). On the J46-J49 +0.742R/trade baseline, expected +0.10-0.18R/trade additive after both interventions.

**Decay-velocity priority (5).** Vol-managed sizing is documented as the most-replicated, highest-Sharpe-impact single intervention in the trend/mean-reversion/vol literature. Direct AMH-decay defender (per Group E F-1: edge magnitude correlates positively with funding-stress / vol regimes — vol-conditioning lets GTOS up-size precisely in regimes where edge is strongest).

**Evidence strength (5).** ≥6 anchor papers across Groups A/D/E + memory `project_distributional_findings`. Cross-domain consensus (foundations + strategies + behavioral/risk all converge on this).

**Composite score: 5 × 5 × 5 × 5 = 625.**

**Data requirements.**
- Per-instrument realized-vol rolling-30-day percentile (existing OHLCV).
- VRP estimate: where MT5 surfaces implied-vol / where free public proxy works (VIX1D-VIX9D for indices via SpotGamma free; GVZ for gold; not available for FX — fall back to realized-vol-percentile only for FX).
- Regime-persistence score (rolling autocorr of regime label from `regime_classifier.py`).
- No new feeds in v1 (rule-based); H-7 sticky-HDP-HMM upgrade slots in once available.

**Methodology.**
- Pre-register sigma rule + clip range [0.5, 2.0] before testing.
- Backtest on Q1.4 cohort (n=2,326).
- Babu-Hoffman-Levine 2020 decomposition mandatory: separate move-magnitude × signal-translation × diversification components on H1-vs-H2 2026 (per Group D Theme 4) — pre-registered prediction that ~40% of H2 LONG-decay reverses under vol-managed sizing.
- A/B in shadow mode for ≥2 weeks before activating in production.
- Promotion gate: ≥+0.10R/trade vs uniform_fn 2.0% on Q1.4 cohort backtest at DSR p<0.01; OR ≥+15% Sharpe + DD-depth ≤ baseline.

**Expected wallclock.** 2-3 days engineering + 1 week shadow-mode + ~1 week shadow validation = 2-3 weeks to production (Q1.4-aligned).

**Composability.** Multiplicative with H-1 (meta-label sizing × vol-conditioning sigma); additive with H-3 (regime classifier feeds regime-persistence); replaces S79 uniform_fn 2% layer; DOES NOT compete with H-5 (side-aware sizing); they bundle multiplicatively.

---

### H-3 — Trade-count-time triggers + dollar-volume bar K54 sampling (open the E24/E26 microstructure track)

**1-line description.** Switch K54's data clock from M15-wallclock to instrument-specific dollar-volume bars (Lopez-de-Prado 2018) AND test the trade-count-time hypothesis (Ane-Geman 2000; Glattfelder-Dupuis-Olsen 2011) on existing tick captures.

**Master backlog IDs.** Bundles **K-1** (volume-bar resampling) + **K-2** (dollar-bar) + **K-3** (imbalance-bar) + **X-1** + **X-2** + **X-3** (E24/E26 re-test on each bar type) + **D-1** (re-bar-sampling infrastructure) + **P-9** (trade-count-time triggers in Component 1).

**Evidence sources.**
- Group A CC2 — "Trading-time / transaction-count time is the operational clock; M15 wallclock is fighting the operational clock" (Clark 1973 mixture-of-distributions; Ane-Geman 2000 transaction-count-time recovers Gaussianity; Glattfelder-Dupuis-Olsen 2011 12 empirical scaling laws).
- Group B §2.2 — explicitly names "M15-aggregation null is theoretically expected, NOT a refutation of microstructure relevance" with 5 papers (Cont-Kukanov-Stoikov 2014 OFI R²≥0.65 at 1s; Lucchese 2024 deep-LOB Sharpe ceiling 0.5; Easley-Lopez-O'Hara Volume Clock; Lopez de Prado 2018 bar sampling; Stoikov 2018 micro-price).
- Group B §6.2 explicitly recommends this as Tier-1 architectural fix to E24/E26.
- Memory `project_microstructure_archived_2026-04-27` — E24/E26 NULL_VERDICT on M15 wallclock; literature predicts SUBSAMPLING ARTIFACT.
- `audit/Q1_3_POSTMORTEM_SYNTHESIS.md` CF-10 — XAU_XAG signal concentrated in calendar/time features (likely overfit). Volume-bar sampling decouples calendar and microstructure.

**GTOS subsystem affected.** Component 1 data ingestion + tick-capture daemon; new `src/research_infra/bar_sampling.py`; downstream `tick_features.py` regime; potentially Component 2 OB detection (only if M15 → volume-bar transition is ratified for production).

**Feasibility (4).** Tick daemon already captures ticks; trade-count + dollar-volume aggregation is a simple groupby-cumsum on existing data. Per-instrument bucket size = median per-M15-bar dollar volume. Backtestable on 2024-2026 history without new infra. Imbalance bars need tick-direction tags (slightly heavier).

**Expected impact (4).** Two pathways:
- K54 v2 retraining on volume-bar features: Group B §2.4 predicts ≥0.03 AUC lift over M15-time-bar baseline; realized-R ≥0.10R/trade at thr≥0.60.
- E24/E26 microstructure non-null: opens an entire feature family currently archived. If verdict is non-null, expected K54 v3 lift +0.02 AUC for the new feature family.
**After 50% realization haircut:** +0.015 AUC + microstructure feature pathway opened.

**Decay-velocity priority (4).** Architectural intervention with long-horizon payoff (microstructure features are LESS likely to decay than published TA patterns per Group D Theme 5). Mid-term decay defender. Slightly lower than H-1/H-2 because it's a research-driven dispatch (verdict could be null again under proper bars).

**Evidence strength (5).** Group A + B both flag this as foundational; ≥5 anchor papers; mechanism (operational clock) is theoretically settled.

**Composite score: 4 × 4 × 5 × 4 = 320.**

**Data requirements.**
- Tick captures: existing `data/ticks/{SYMBOL}/*.parquet`.
- 2022-2023 OHLCV backfill (DONE).
- New: per-instrument bar-bucket size calibration (rolling weekly).
- Optional: tick-direction tags for imbalance bars (BVC-corrected per Andersen-Bondarenko 2014 critique).

**Methodology.**
- Re-bar existing MT5 tick captures into (i) volume bars, (ii) dollar bars, (iii) imbalance bars.
- Recompute K54 catalog on each bar type.
- Pair against M15-time-bar baseline under CPCV-honest accounting.
- Pre-registered prediction: dollar-volume bars + imbalance bars beat M15-time bars by ≥0.03 AUC; volume bars at ≥0.02 AUC.
- Open-question: trade-count-time triggers (200-trade-count bars) for Component 1 ingestion — separate gating from K54 features.
- Promotion gate: cross-period robustness on the 2022-2023 → 2024-2026 split (per H-1).

**Expected wallclock.** 1-2 weeks: 3-4 days re-bar sampling infra; 2-3 days K54 retrain × 3 bar types; 3-5 days CPCV validation. Subscription-only.

**Composability.** Provides cleaner sampling for H-1 K54 v3 features (drop-in once validated); independent of H-2 and H-5; supplies the proper-clock substrate for H-4 Stoikov micro-price effectiveness. Pre-condition for H-8 microstructure-feature catalog expansion.

---

### H-4 — Stoikov micro-price + Osler stop-cluster + power-law-decayed OB-age (microstructure feature trio)

**1-line description.** Add three microstructure-mechanism-grounded features to the K54 catalog: Stoikov 2018 micro-price (replaces naive mid), Osler 2003 stop-cluster density at OB-retest entry, and Bouchaud propagator power-law `t^(-0.5)` OB-age weighting.

**Master backlog IDs.** Bundles **K-4** (Stoikov micro-price) + **K-7** (Osler stop-cluster for FX K54) + **K-8** (power-law OB-age weighting) + **K-10** (above-up below-down round-aligned direction) + **P-4** (Stoikov in `tick_features.py`) + **E-1** (Osler stop-cluster validation on production data — gates this hypothesis's mechanism claim) + **C-2** (disposition-effect feature on counterparty stops).

**Evidence sources.**
- Group B §2.1 — "the OB-zone is the empirical convergence of three independent academic literatures" (Osler 2003-2005 stop-cluster microstructure; Toth-Bouchaud 2011 V-shape latent liquidity; Lillo-Mike-Farmer-Sato 2005-2023 long-memory order flow).
- Group B §6.1 + §7.1 — names Osler 2003 as the load-bearing GTOS edge-mechanism paper. Direct match for `edge_mechanism.md`.
- Group D Theme 5 + H-D5 — Stübinger-Endres 2018 jump-then-OU + Lo-Mamaysky-Wang 2000 + Lehmann 1990: stop-cascade mechanism is published, not folk-theorem.
- Group E F-2 + Section 3 — disposition effect overdetermined (Odean 1998, Coval-Shumway 2005, Locke-Mann 2005, Frydman-Barberis-Camerer-Bossaerts-Rangel 2014 fMRI realization-utility); IS the operative counterparty mechanism.
- Memory `project_f11_ob_zone_decay_velocity_pinned` — OB-zone advantage decay-dominant ~78%. Power-law-age weighting + stop-cluster context disentangles methodology vs decay drivers.

**GTOS subsystem affected.** `tick_features.py` + K54 catalog (`src/research_infra/k54_features.py` if exists / equivalent path); Component 2 OB-zone instantiation (age-weighting); per-instrument FX-specific feature path.

**Feasibility (5).** All three features are deterministic / closed-form:
- Stoikov micro-price: `(p_bid * vol_ask + p_ask * vol_bid) / (vol_bid + vol_ask)` with martingale correction; computed on existing tick data.
- Osler stop-cluster proxy: rolling 1-min realized-vol within ±N ticks of round numbers (no proprietary stop-book needed).
- Power-law OB-age: replace rolling-50 hard cutoff with `weight(t) = t^(-0.5)` on candidate-OB age list.
Drop-in features. ~1-2 days each.

**Expected impact (4).** Per-feature lift from Group B + Group D estimates:
- Stoikov micro-price: small but consistent edge across all 7 instruments (1-bar prediction RMSE ≥10% lower).
- Osler stop-cluster: ≥0.02 OOS AUC, concentrated in USDJPY/GBPJPY/GBPUSD.
- Power-law OB-age: ≥0.02 OOS AUC; mechanism-grounded sharper time-decay.
- Combined non-overlapping lift after diminishing-returns: +0.04 to +0.06 AUC.
**After 50% haircut: +0.02-0.03 AUC.**

**Decay-velocity priority (4).** Microstructure features are LESS arbitrage-decayed than published TA patterns (Group B §4.5; Group D Theme 5). Edge-mechanism-validating: if Osler stop-cluster correlates with OB-retest WR, it confirms the GTOS edge mechanism is what `edge_mechanism.md` claims.

**Evidence strength (5).** ≥10 papers across Groups B/D/E; Osler 2003 specifically named as load-bearing in Group B §7.1.

**Composite score: 5 × 4 × 5 × 4 = 400.**

**Data requirements.**
- Tick captures (existing).
- Round-number tables per instrument (XAU $1/$50/$100; FX ticks at 0.0001 / 0.01).
- OB candidate age list (existing in market_state.py).
- No new external feeds.

**Methodology.**
- Pre-register per-feature OOS AUC predictions (Stoikov small; Osler ≥0.02; OB-age ≥0.02).
- Add as additive features to K54 v3 catalog (drops into H-1 bundle).
- Test under CPCV-honest accounting on Q1.4 cohort.
- Stratify by instrument (Osler concentrated in FX per literature).
- Validate Osler mechanism: rolling stop-cluster density should correlate with OB-retest realized-R in FX cells.
- E-1 mechanism validation runs in parallel: take-profits cluster AT round; stops just BEYOND. Verify on production trade history before claiming Osler attribution.

**Expected wallclock.** ~1 week: 2 days Stoikov implementation + 2 days Osler proxy + 1 day OB-age weighting + 2-3 days CPCV validation.

**Composability.** Drops into H-1 K54 v3 master bundle as additive features. Independent of H-2, H-3, H-5. H-3 (volume-bar sampling) sharpens H-4 (microstructure features have higher signal at proper sampling clock). Cross-references H-7 (Osler-mechanism context informs round-number × side regime classifier interaction).

---

### H-5 — Risk-policy bundle: Busseti-Boyd RCK + Strub EVT-CDaR + side-aware sizing + smooth Grossman-Zhou

**1-line description.** Replace S79 uniform_fn 2.0% with a literature-grounded multi-component risk policy: Busseti-Boyd Risk-Constrained Kelly under FN constraint `P(MTM-DD ≥ 4%) ≤ 0.02` × Strub EVT-CDaR sizing × side-aware multiplier (LONG=0.5x, SHORT=1.0x) × smooth Grossman-Zhou variant of H29.

**Master backlog IDs.** Bundles **R-1** (Busseti-Boyd RCK) + **R-2** (lambda auto-calibration) + **R-3** (Strub EVT-CDaR) + **R-4** (smooth Grossman-Zhou) + **R-5** (per-instrument optimal weights) + **R-6** (side-aware sizing) + **R-7** (vol-scaled cross-7) + **R-9** (composite reference) + **B-3** (composite bundle).

**Evidence sources.**
- Group E §5 + Section 6 priorities 1-3 + final-report F-4 — explicitly names Busseti-Boyd RCK + Strub EVT-CDaR + Moreira-Muir vol-scaling + smooth Grossman-Zhou as the literature-grounded path from S79 uniform.
- Group D §4 + final-report — Barroso-Santa-Clara vol-managed (Sharpe 0.53→0.97); Daniel-Moskowitz LONG-sizing modifier; bundles multiplicatively.
- Group A Rank 1 + M7 — McNeil-Frey GARCH-EVT for VaR/heartbeat/DD threshold calibration; coherent ES > VaR for portfolio aggregation.
- Memory `project_s79_risk_policy_shipped_2026-04-27` — S79 +25.8pp P(pass FN) shipped; sharpe_weighted explicitly Phase 2 follow-up.
- Memory `project_side_aware_sizing_findings` — H37/H38 + side-aware (LONG=0.5x, SHORT=1.0x) Pareto-dominates; XAUUSD H2 +$8k recovery.
- Memory `project_distributional_findings` — gold ξ=0.35; calibrates Sornette crash-aware Kelly fraction at ~0.4 (consistent with GTOS conservative 1/9-Kelly stance).

**GTOS subsystem affected.** S79 risk-policy substitution; `risk_per_trade_pct` resolution layer; H29 drawdown manager; permissions gate; per-instrument profiles (`config/profiles/`).

**Feasibility (4).** Multi-component bundle; each piece is closed-form or convex-optimization tractable:
- Busseti-Boyd RCK: cvxpy convex-opt; single λ knob; nightly retrain feasible.
- Strub EVT-CDaR: McNeil-Frey GPD fit + CDaR formula; statsmodels/arch packages.
- Side-aware: trivial config flag + multiplier table.
- Smooth Grossman-Zhou: closed-form continuous variant of H29.
Implementation 1-2 weeks; backtest validation 1-2 weeks.

**Expected impact (5).** Composite of:
- Vol-scaling: +15-25% Sharpe (Moreira-Muir; haircut from 30-50%).
- Side-aware: per memory project_side_aware_sizing_findings, +$8k XAUUSD H2 recovery on 2024-2026 backtest.
- Busseti-Boyd: per-instrument optimal weights non-uniform; +10-20% growth at same MTM-DD violation prob.
- Smooth Grossman-Zhou: variance reduction on P(pass FN); not headline.
**After 50% haircut on Sharpe + side-aware: +20-35% Sharpe + +0.05-0.15R/trade.** Direct FN-survivability impact.

**Decay-velocity priority (5).** Risk-policy is decay-orthogonal: it doesn't decay. Bundles directly with the LONG-side selectivity collapse (memory `project_a6_decay_attribution_long_side_concentrated`) — side-aware sizing recovers the realized-R lost in H2 trending_bull cohorts.

**Evidence strength (5).** ≥10 papers across Groups A/D/E + 3 GTOS memories + S79 production track record.

**Composite score: 4 × 5 × 5 × 5 = 500.**

**Data requirements.**
- Per-instrument realized-R distribution (existing trade history).
- GARCH-EVT GPD fit parameters (computed offline, refresh quarterly).
- FN constraint `P(MTM-DD ≥ 4%) ≤ ε` for ε = 0.02 (CEO-fixed).
- No new feeds.

**Methodology.**
- Pre-register per-instrument optimal weights vs uniform_fn 2.0%.
- Backtest on Q1.4 cohort (n=2,326) under stationary block bootstrap.
- Babu-Hoffman-Levine 2020 attribution: separate move-magnitude vs sizing-policy effect.
- A/B in shadow mode for ≥30 days against current S79.
- Monte Carlo P(pass FN) under each variant (replicate S79 protocol).
- Promotion gate: ≥+15% Sharpe + DD-depth ≤ baseline + P(pass FN) ≥ S79's +25.8pp baseline.

**Expected wallclock.** 2-3 weeks: 1 week implementation + 1 week shadow + 1 week Monte Carlo + validation.

**Composability.** Bundles multiplicatively with H-2 (vol-conditioning sigma is the input to RCK λ); H-1 (meta-label sizing output × RCK risk allocation = production sizing). DOES NOT compete with side-aware path. Replaces S79 entirely once validated.

---

### H-6 — DSR + effective-N + PBO methodology bundle (retroactive + forward-gating)

**1-line description.** Apply DSR + effective-N + PBO + Romano-Wolf StepM retroactively to all "Validated Numbers" in CLAUDE.md (J46-J49, K54 v1, S79, XAUUSD WR 62%, USDJPY 75.8%, FVG-impulse, OB-zone advantage); make the same bundle a mandatory promotion gate for every Q1.4+ "lift" claim.

**Master backlog IDs.** Bundles **M-1** (DSR retroactive J46-J49) + **M-2** (DSR K54 v1) + **M-3** (DSR S79) + **M-4** (DSR audit Validated Numbers) + **M-6** (Romano-Wolf StepM cells) + **M-7** (CPCV-honest training-overlap SE — already adopted) + **M-12** (effective-N tracker) + **M-13** (PBO baked-in) + **M-16** (bias-variance bookkeeping) + **B-6** (composite) + **RR-2** (monthly tracker update).

**Evidence sources.**
- Group A CC7 + CC12 + Section 4 M1-M5 — multiple-testing discipline is the single largest threat to lift claims; Bailey-Lopez-de-Prado 2014 deflated SR; Lopez-de-Prado-Lewis 2018 ONC effective-N; Romano-Wolf 2005 StepM; Lucky Factors Harvey-Liu 2021; PBO Bailey-Lopez-de-Prado 2017.
- Group F Finding 2 + §6 — McLean-Pontiff 2016 26%/58% decay; F11's GTOS measurement squarely inside that distribution; methodology discipline is what catches false-strategy noise.
- `audit/statistical_reevaluation.md` — CPCV-honest p=0.675 (vs Stouffer naive 0.0015) on K54 v2; the methodology critic's discipline genuinely caught a 2× false PASS. This bundle is the formalization of that catch.
- Memory `feedback_walk_level_evidence_not_predictive` — walk-level p=5e-16 reversed to p=0.564 under realized-R. DSR closes this exact gap.
- Memory `project_k52_validated_numbers_status_2026-04-27` — 2/5 Validated Numbers survive under partial K52 retest. Full DSR sweep is the next step.

**GTOS subsystem affected.** Research-infra promotion gates; CLAUDE.md "Validated Numbers" table; every future "+0.X R/trade" claim.

**Feasibility (5).** Closed-form formulas; Lopez-de-Prado-Bailey papers have reference implementations; Python packages (mlfinlab, pyfolio) have baked-in DSR computation. <1 day eng.

**Expected impact (4).** Two directions:
- Retroactive: likely some "Validated Numbers" will fail DSR (per K52 partial retest 2/5 survives). This is INFORMATIONAL impact — eliminates false-confidence overhead on production decisions.
- Forward-gating: prevents the next K54-v2-style false PASS. Estimated saved ML push: 1-2 quarters × ~$5k research budget.

**Decay-velocity priority (5).** Direct CEO concern; without this discipline, the entire research program is exposed to false-strategy noise (Bailey-Lopez-de-Prado 2014: with cumulative trial count ~200, noise-only Sharpe ceiling ~3.27).

**Evidence strength (5).** ≥8 anchor papers + 3 GTOS audits + 4 memories.

**Composite score: 5 × 4 × 5 × 5 = 500.**

**Data requirements.**
- Cumulative trial count log (research-infra audit; estimate ~200 currently).
- Per-claim trade samples (already in `_trade_index.json` / `trades_unified.csv`).
- ONC clustering on trial population (per Lopez-de-Prado-Lewis 2018; sklearn).

**Methodology.**
- Build `dsr_diagnostics.json` schema: (i) cumulative trial count N, (ii) DSR-corrected p-value, (iii) PBO from CSCV, (iv) effective-N via ONC clustering.
- Apply retroactively to: J46-J49 +0.742R, K54 v1 0.571 + +0.164R, S79 +25.8pp, XAUUSD WR 62%, USDJPY 75.8%, US30 58.5%, FVG-impulse, OB-zone advantage.
- Document survivors in updated CLAUDE.md "Validated Numbers" table.
- Make `dsr_diagnostics.json` mandatory in every `research/` artifact with a Sharpe/R/AUC headline.
- Romano-Wolf StepM at α=0.05 over the 47 instrument×side×regime cells (per Group A M4) for any "F-series finding pinpoints cell X" claim.

**Expected wallclock.** 2-3 days: ~1 day for retroactive sweep on 8 claims + 1 day infra-build + 1 day documentation.

**Composability.** GATES every other hypothesis in this backlog. H-1 cannot ship without H-6 evaluation. DOES NOT compete with anything; pure infrastructure.

---

### H-7 — Sticky-HDP-HMM regime classifier with Kirby fat-tailed-mixture null-test

**1-line description.** Upgrade `regime_classifier.py` from V1 H4-swing (observational) to a sticky HDP-HMM (Fox 2008-11) on XAU H4 returns + RV + RV-skew + DXY change with Kirby-2023 fat-tailed-mixture null-test as mandatory pre-promotion gate.

**Master backlog IDs.** Bundles **P-8** (sticky HDP-HMM regime classifier) + **K-9** (regime × round_aligned × side interaction features in K54) + **U-16** (Kirby null-test calibration) + **A-14** (Aquilina BIS JPY-carry-unwind regime classifier; bundles for FX cells).

**Evidence sources.**
- Group A Rank 3 + CC3 + CC9 + M6 — explicit recommendation; sticky HDP-HMM gives probabilistic confidence + auto-K + realistic dwell time. Kirby 2023 (05-64) mandatory null-test before production.
- Group D Theme 1 + Theme 2 — regime conditions everything; Wood-Roberts-Zohren 2022 hybrid slow-momentum + fast-reversion via online change-point detection (+33-67% Sharpe).
- Group E F-1 — Lo's AMH frames regime-conditioned cohort failures as recurring; F15 + A6 + F2 explicitly need regime-aware re-architecture.
- Memory `project_f3_k53_source_stratified_indistinguishable_random` — K53 classifier failed at H2-2026 holdout (AUC 0.401). Demonstrates exactly why Kirby null-test is non-optional.
- Memory `project_f15_synthesis_regime_is_load_bearing` — regime is the load-bearing decay axis (bonf_p=0.0016 with proper backfill); v1 detector forced trending_bull cohort → cohort collapse.

**GTOS subsystem affected.** `src/components/regime_classifier.py` upgrade; `regime_shadow_logger.py`; downstream K54 v3 features (regime probability vector); strategic substrate for all regime-aware sizing.

**Feasibility (3).** Sticky HDP-HMM is computationally non-trivial; PyMC or pyhsmm has implementations but Bayesian inference layer is heavier than LightGBM. Kirby null-test requires fat-tailed mixture simulator. ~1-2 weeks engineering. NOT a same-day dispatch.

**Expected impact (4).** Group A Rank 3: realized-R AUC ≥0.05 better than v1 swing classifier on H1→H2 OOS test. Powers H-1 K54 v3's regime-prob feature. Predicted regime-aware K54 v3 lift: +0.02-0.04 AUC over non-regime-aware baseline.

**Decay-velocity priority (5).** Regime-aware ML is Phase 2 rank #1 in CLAUDE.md. Direct decay-defender (regimes shift faster than features).

**Evidence strength (4).** ≥6 anchor papers across Groups A/D/E + 2 memories. Kirby contrarian (1 paper) is the methodological brake.

**Composite score: 3 × 4 × 4 × 5 = 240.**

**Data requirements.**
- XAU H4 returns + realized vol + RV-skew (existing).
- DXY change (free MT5 surface; or DXY proxy via EUR + JPY + GBP + CAD + SEK + CHF basket).
- Fat-tailed mixture simulator (Group A M6 prescription): Student-t mixture calibrated to GTOS distributional findings (ξ=0.35).
- No new external feeds.

**Methodology.**
- Train sticky HDP-HMM on H4 returns + RV + RV-skew + DXY change; auto-K via the nonparametric prior.
- Kirby null-test: simulate fat-tailed mixture (no regime structure) calibrated to GTOS data; run classifier on simulated data; check whether parameter estimates / regime labels look qualitatively similar to live data. If yes, REJECT regime interpretation.
- Cross-period robustness on 2022-2023 → 2024-2026 split.
- Promotion gate: realized-R AUC ≥ +0.05 over v1 H4-swing on H1→H2 OOS + Kirby null-test PASS + ≥14d shadow data.

**Expected wallclock.** 2-3 weeks: 1 week implementation + 1 week Kirby null-test + 1 week shadow validation.

**Composability.** Feeds H-1 K54 v3 (regime-prob feature); supplies regime label for H-2 vol-conditioning's regime-persistence input; supplies the regime axis for H-5 risk-policy bundle's per-instrument-regime weight. Pre-condition for any regime-conditional sizing rule.

---

### H-8 — Asset-class-specialist bundle: NAS_US30 dealer-gamma + JPY-pair Aquilina + GBP-pair political + dollar-pair Treasury-basis

**1-line description.** Replace generic "FX block" K54 specialist with three asset-class-specialist models (JPY-pair / GBP-pair / dollar-pair) via Lustig-Roussanov-Verdelhan 2-factor decomposition, plus NAS_US30 specialist with dealer-gamma + VIX1D-VIX9D + LETF-flow features.

**Master backlog IDs.** Bundles **A-1** (gamma-sign feature for indices) + **A-2** (VIX1D-VIX9D) + **A-3** (VRP delta) + **A-4** (NAS_US30 specialist re-train) + **A-5** (JPY-pair specialist) + **A-6** (GBP-pair specialist) + **A-7** (dollar-pair specialist) + **A-8** (Erb-Harvey real-gold-price percentile) + **A-11** (LBMA fix anomaly) + **A-12** (Krohn-Mueller-Whelan FX-fix W-shape) + **A-14** (Aquilina BIS JPY-carry-unwind) + **B-4** (composite).

**Evidence sources.**
- Group C §1 + Sections 5/7 + final-report — central claim that NAS_US30 cross-period sign-flip is dealer-gamma-regime-flip + Mag-7 concentration; FX cohort negative-lift is mis-specified single FX block (must split per Lustig-Roussanov-Verdelhan 2-factor).
- Group C §3 + final-report — 22 hypotheses, ranks #1 (dealer-gamma + Mag-7 for NAS_US30) and "decompose into dollar-factor and carry-slope, NOT unified FX block" for the FX recovery.
- Group B §6.6 — OPEX-Friday morning + daily MM-gamma-sign feature for NAS100/US30 (10 anchor papers).
- `audit/architecture_ab.md` — NAS_US30 specialist AUC 0.6379 strongest single Q1.3 finding; cross-period sign-flipped (+0.074 → -0.078). Mechanism is exactly dealer-gamma per Group C.
- Memory `project_b7_hallucination_per_instrument_2026-04-27` — US30_cash 23.4% hallucination concentrated near round/OPEX-strike clusters (independent corroboration of dealer-gamma mechanism).

**GTOS subsystem affected.** Per-cohort K54 specialist routing; new feature feeds (VIX1D-VIX9D, GVZ, Erb-Harvey real-gold-price, FX-fix calendar); cross-instrument correlation gate (informed by Block-DECO upgrade).

**Feasibility (3).** Multi-component:
- NAS_US30 dealer-gamma: free-data via SpotGamma/SqueezeMetrics or VIX1D-VIX9D proxy. ~1 week.
- JPY-pair / GBP-pair / dollar-pair split: feature engineering on existing OHLCV + free public proxies. ~1 week.
- LBMA fix + Krohn-Mueller-Whelan: calendar features (closed-form). ~3 days.
- Erb-Harvey real-gold-price: WGC + FRED feeds (free). ~3 days.
Total: 3-4 weeks. Multiple specialists = multiple validations.

**Expected impact (5).** Group C estimates per-feature lifts:
- JPY-pair specialist: +0.02-0.04 AUC on USDJPY+GBPJPY-JPY-leg cohort.
- GBP-pair specialist: +0.02-0.04 AUC on GBPUSD+GBPJPY-GBP-leg cohort.
- Dollar-pair specialist: +0.02-0.04 AUC on USDJPY+GBPUSD cohort.
- NAS_US30 dealer-gamma: cures the cross-period sign-flip (+0.13 in-sample → preserve OOS).
**After 50% haircut + cross-period validation: +0.02-0.05 AUC on the 4 currently-decayed cohorts; potential to take K54 v3 from 0.58 to 0.62-0.65 on those cells.**

**Decay-velocity priority (4).** Asset-class specialists are decay-resistant (mechanism-grounded; carry / dealer-gamma / fix-window are durable structural flows per Group C). Direct attack on Q1.3 cohort sign-flip mode.

**Evidence strength (5).** ≥15 anchor papers across Group C + 4 from Group B + 2 from Group A + 3 audit refs.

**Composite score: 3 × 5 × 5 × 4 = 300.**

**Data requirements.**
- Free public feeds: VIX1D / VIX9D / GVZ (CBOE free); SpotGamma / SqueezeMetrics free tier; FRED macro (intermediary capital, TED spread); WGC ETF flow.
- LBMA fix + Krohn-Mueller-Whelan calendar: open-source.
- TQQQ AUM: Yahoo Finance.
- BIS Bull 90 JPY-carry-unwind metric: monthly proxy via TED + FRA-OIS public.
- ALL FREE.

**Methodology.**
- Per-specialist CPCV-honest validation on Q1.4 cohort.
- Cross-period robustness on 2022-2023 → 2024-2026 split (Q1.4 prerequisite).
- Romano-Wolf StepM over the 4 specialist cells (per Group A M4).
- Pre-register per-cohort lift predictions before testing.
- For NAS_US30: dealer-gamma feature must EXPLAIN the +0.13 → -0.078 cross-period sign-flip; otherwise it's correlation not mechanism.

**Expected wallclock.** 4-6 weeks: feeds setup 1 week, per-specialist build 1-2 weeks, validation + cross-period 1-2 weeks.

**Composability.** Drops specialists into H-1 K54 v3 master bundle (per-cohort routing layer P-6 in MASTER_BACKLOG.md). Bundles with H-7 regime classifier (regime × specialist interaction). Independent of H-2/H-5 risk-overlay. NAS_US30 specialist is an early-Q1.4 ship candidate; FX-3 specialists are mid-Q1.4.

---

### H-9 — Multivariate self-normalized CUSUM + BOCPD-AR-score-driven decay observability upgrade

**1-line description.** Replace S1 monthly-decay shadow monitor's rolling-50 + threshold heuristic with two principled streaming detectors: Aue-Kirch 2024 self-normalized multivariate CUSUM on (XAU, US30, USDJPY) joint daily WR/CR/OB-continuation vector + Tsaknaki-Lillo-Mazzarisi 2024 BOCPD-AR-score-driven on XAU M15 returns + RV.

**Master backlog IDs.** Bundles Group-A Rank 6 + Rank 12 (no specific MASTER_BACKLOG IDs yet — surface as new items after Phase 3) + **RR-3** (weekly McLean-Pontiff baseline alarm) + **U-14** (McLean-Pontiff publication-decay validation).

**Evidence sources.**
- Group A Rank 6 + CC9 + Rank 12 — Aue-Kirch 2024 self-normalized CUSUM (05-43); Tsaknaki-Lillo-Mazzarisi 2024 BOCPD-AR-score-driven; e-detectors (Wang-Ramdas 2025).
- Group E F-1 + Section 2 — McLean-Pontiff 26%/58% decay; ~5%/year residual decay is the alarm baseline; F11 GTOS measurement squarely inside this distribution.
- Group F §6 — edge decay is a property of publication-and-replication; continuous observability is the strategic response.
- Memory `feedback_decay_is_ceo_number_one_concern` — decay-velocity dominates compute cost; pre-register monitoring ahead of decay events.

**GTOS subsystem affected.** S1 monthly-decay shadow monitor; CUSUM-candidate-rate-daily monitor; `scripts/ob_continuation_monitor.py`.

**Feasibility (4).** Aue-Kirch self-normalized CUSUM has closed-form; Tsaknaki et al. 2024 has open-source code in some forks. Implementation 1-2 weeks; replacing rolling-50 heuristic is low-friction.

**Expected impact (3).** Operational improvement; ≥30% reduction in S1 false-alarm rate at matched detection delay (Group A Rank 6 prediction). Not a direct realized-R lift; observational.

**Decay-velocity priority (5).** This IS the decay observability infrastructure. CEO #1 concern.

**Evidence strength (4).** ≥4 anchor papers + 2 memories.

**Composite score: 4 × 3 × 4 × 5 = 240.**

**Data requirements.**
- Daily WR / CR / OB-continuation vectors (existing in `shadow_logs/`).
- M15 returns + RV (existing).
- Cross-instrument tick microstructure features (existing tick daemon).
- No new feeds.

**Methodology.**
- Implement Aue-Kirch self-normalized CUSUM on (XAU, US30, USDJPY) joint vector.
- Implement BOCPD-AR-score-driven on XAU M15 + RV + RV-skew.
- Calibrate FPR ≤ 5% on simulated null (fat-tailed mixture per H-7 Kirby spec).
- A/B against current rolling-50 + threshold for 30 days.
- Promotion gate: ≥30% lower false-alarm rate at matched detection delay.

**Expected wallclock.** 2-3 weeks: 1 week implementation + 1 week calibration + 1 week shadow A/B.

**Composability.** Independent of H-1 / H-2 / H-5; complements H-7 (regime classifier transitions feed CUSUM). Pre-condition for activating S1 watchdog cron hook (currently DISABLED per CLAUDE.md item #6).

---

### H-10 — Tool-grounded LLM Component 3A + Bull/Bear/Judge debate activation + Reflexion post-trade

**1-line description.** Wire QuantMCP/FinAgent-style tool-use grounding for Component 3A (predicted 70-80% reduction in HALLUC-class precision bugs); activate Bull/Bear/Judge debate (N62, currently default OFF) in shadow mode; add Reflexion-style post-trade reflection loop.

**Master backlog IDs.** Bundles **L-1** (QuantMCP tool-use) + **L-2** (FinAgent tool inventory) + **L-3** (Reflexion post-trade reflection) + **L-4** (Bull/Bear/Judge activation) + **L-5** (Y. Li 2023 ICAIF hybrid) + **L-6** (HALLUC-2 token-usage logger) + **L-7** (Q71 slippage logger) + **L-8** (LLM transfer test) + **B-5** (composite).

**Evidence sources.**
- Group F Finding 4 + Stream C — QuantMCP 2025 80% factual hallucination reduction; FAITH 2025 8-15% intrinsic frontier-model hallucination on finance tables (brackets GTOS pre-FA-2 rates); Deficiency study 2023.
- Group F Stream B — TradingAgents 2024 + AlphaAgents 2025 (BlackRock) + FinCon 2024 NeurIPS; Self-Reflection 2024 p<0.001 lift.
- Memory `project_halluc_1_precision_bug_class_2026-04-27` — NAS100 93% "hallucination" was deterministic precision bug; tool-grounding eliminates the class.
- Memory `project_a4_xauusd_trending_bull_replay_2026-04-28` — same compound bug class; safety stack catches via L2 sl_buffer 0.0 pattern; tool-grounding addresses root cause.
- Memory `project_b7_hallucination_per_instrument_2026-04-27` — US30_cash 23.4% / USDJPY <5%; OB-anchored fields 80-99% accurate; current_price + stop_loss are hallucination loci (exactly what tool-grounding fixes).

**GTOS subsystem affected.** Component 3A (`src/components/primary_analyzer.py`); Component 3B Bull/Bear/Judge debate (already wired, default OFF); new Reflexion post-trade module.

**Feasibility (4).** Anthropic MCP is supported; Component 3B is built-but-not-wired (research-door-wired N62 per CLAUDE.md unresolved item #10). Reflexion is a wrapper around closed trades. Implementation ≤2 weeks per L-track; A/B in shadow ≥4 weeks.

**Expected impact (4).** Per Group F:
- Tool-grounding: 70-80% HALLUC-class precision bug reduction → fewer L2 sl_beyond_ob rejections (memory `project_live_l2_rejection_per_instrument`: XAUUSD 85.7%, GBPUSD 78.6% pre-FA-2). Direct CR lift.
- Bull/Bear/Judge: TradingAgents-class lifts 5-15% (variable; 30d-3mo backtests).
- Reflexion: ≥0.05R expectancy lift at <$5/mo per L-3 spec.

**Decay-velocity priority (3).** Group F Stream A: LLM-news-sentiment alpha decays toward zero by 2027 (Lopez-Lira-Tang 6.54→1.22 in 30m). This bundle defends the AI-grounding quality but doesn't itself address structural edge-decay. Lower priority than risk-policy + K54 v3.

**Evidence strength (4).** ≥6 anchor papers + 5 memories. Strong on tool-grounding (consensus); softer on debate (smaller literature).

**Composite score: 4 × 4 × 4 × 3 = 192.** (Lower than H-1..H-9; surface as Q1.4-tail or Q2-early; included in top-10 because it's the only LLM-architecture lever in the top tier and its tool-grounding piece is high-leverage.)

**Data requirements.**
- MCP-compatible market-state query tools (build on top of `market_state.py`).
- Closed-trade outcome ledger (existing `_trade_index.json`).
- No new feeds.

**Methodology.**
- L-1 QuantMCP wiring: replace numeric-fact prompt embedding with MCP tool calls.
- A/B in shadow vs prompt-only baseline for ≥30 days.
- Bull/Bear/Judge: enable in shadow mode; track WR / CR / realized-R deltas.
- Reflexion: post-trade reflection writes to episodic-memory store; gated by ≥0.05R lift at <$5/mo.
- Promotion gate (per memory `feedback_avoid_conservative_default_defer`): default OFF protects production; ship in shadow with explicit kill-switch.

**Expected wallclock.** 4-6 weeks: 2 weeks tool-grounding + 2 weeks debate activation + 2 weeks Reflexion + ongoing shadow.

**Composability.** Independent of K54 v3 / risk-policy; pre-condition for K55 ML-vs-AI shadow harness (Section S in MASTER_BACKLOG.md). Replaces / complements Component 3A; does NOT replace K54 v3.

---

## Section 3 — Tier 2 hypotheses (ranks 11-30)

Tier-2 = composite 100-249, Q2-Q3 candidates. Same axes; tighter prose. Each cites ≥3 evidence sources and references MASTER_BACKLOG IDs.

### H-11 — Signature features + fractional differentiation + HAR-RV cascade for K54 v3 features
- **Master IDs:** Group A Rank 5 / 9 / 10 (no specific catalog ID — surface as new K-feature items).
- **Evidence:** Group A CC10 (Lyons 1998; Cuchiero-Möller 2024) + CC5 (Lo 1991; Lopez-de-Prado AFML Ch 5) + CC8 (Corsi 2009 HAR-RV) + Group D Theme 3 (Guyon-Lekeufack 2023 PDV).
- **Subsystem:** K54 v3 feature engineering.
- **Feasibility 4:** signatory / iisignature Python packages; fractional differentiation closed-form; HAR-RV is statsmodels.
- **Impact 4:** +0.02 AUC each, diminishing-returns combined +0.04-0.06.
- **Decay 3:** mid-term feature engineering; depends on K54 v3 architecture being in place.
- **Evidence 4:** ≥5 anchor papers Group A + Group D.
- **Composite: 4 × 4 × 4 × 3 = 192.**
- Composability: drops into H-1 K54 v3 master bundle as additive features.

### H-12 — Block-DECO + Forbes-Rigobon-corrected cross-instrument correlation gate
- **Master IDs:** **A-16** (Engle DCC / Aielli cDCC / Engle-Kelly Block-DECO) + **A-17** (Patton 2006 + Christoffersen 2012 copula) + **A-18** (Forbes-Rigobon 2002).
- **Evidence:** Group C §3 ranks #20-25 (Block-DECO with 4 blocks maps GTOS asset-class structure); Group A Rank 8 (wavelet-coherence alternative); Group E H-E18 (HRP cluster gate).
- **Subsystem:** `src/components/cross_instrument_correlation_gate.py`.
- **Feasibility 4:** Engle DCC has python implementations; Forbes-Rigobon is closed-form bias correction.
- **Impact 3:** ≥60-70% reduction in false-positive flips during volatility spikes; downstream additive risk gate.
- **Decay 3:** decay-orthogonal infrastructure.
- **Evidence 5:** ≥10 anchor papers Group C.
- **Composite: 4 × 3 × 5 × 3 = 180.**

### H-13 — Pre-FOMC + macro-announcement + LBMA-fix calendar features
- **Master IDs:** **A-11** (LBMA fix anomaly Caminschi-Heaney 2014) + **A-12** (Krohn-Mueller-Whelan FX-fix W-shape) + **A-13** (Brunnermeier-Nagel-Pedersen funding-liquidity).
- **Evidence:** Group C ranks #8/#9/#11 (W-shape FX fix; pre-FOMC USD-bias from Karnaukh 2018 R²=22%; quarter-end CIP Du-Tepper-Verdelhan 2018); Group B §6.3 (fix-window avoidance gate).
- **Feasibility 5:** calendar features; closed-form.
- **Impact 3:** per-feature ≤+0.02 AUC; bundles to +0.03-0.05.
- **Decay 3:** durable macro mechanism.
- **Evidence 4:** ≥6 anchor papers Group C + Group B.
- **Composite: 5 × 3 × 4 × 3 = 180.**

### H-14 — OPEX-Friday morning gate + dealer-gamma sign feature for NAS100/US30
- **Master IDs:** Subset of **A-1**+**A-2**+**A-3**+**A-4** (already in H-8); also Group B §6.6 (no MASTER ID).
- **Evidence:** Group B §6.6 + H8/H9/H10 (OPEX-Friday morning gate; daily MM-gamma-sign; 10 anchor papers); Group C §3 ranks #13/#15/#16 (NDX dealer-gamma; VIX1D-VIX9D; OPEX filter).
- **Feasibility 5:** calendar + free public proxies.
- **Impact 4:** explains NAS_US30 cross-period sign-flip (per Group C §7 final-report top hypothesis); cures HALLUC-1-class round/OPEX clusters.
- **Decay 3:** durable derivative-payoff mechanism.
- **Evidence 5:** ≥10 anchor papers Group B + Group C.
- **Composite: 5 × 4 × 5 × 3 = 300.** (Borderline top-10; included as standalone Tier-2 because the bundle is also in H-8; this is the standalone ship-fast version.)

### H-15 — Coval-Shumway second-half-of-session A/B test on existing GTOS data
- **Master IDs:** **C-1** (Coval-Shumway 2005 second-half OB-retest A/B) + **E-1** (Osler stop-cluster validation as pair).
- **Evidence:** Group D Section 1 + H-D1 (Coval-Shumway 2005); Group E F-2 + H-E1 (counterparty-stress mechanism); Group B §2.1 (OB-zone 3-mechanism convergence).
- **Feasibility 5:** existing data; trivial stratification.
- **Impact 3:** if H1 confirms, gives a free intraday-time feature for K54.
- **Decay 4:** validates the GTOS edge mechanism (high-info-density single test).
- **Evidence 4:** ≥4 anchor papers + canonical Coval-Shumway citation.
- **Composite: 5 × 3 × 4 × 4 = 240.**

### H-16 — VIX-conditional sizing + VRP feature + Bekaert-Hoerova decomposition
- **Master IDs:** **V-2** (VRP feature; subset of H-2) + **A-2** (VIX1D-VIX9D); decomposition new.
- **Evidence:** Group D Theme 3 + H-D1; Group C ranks #6/#7/#15; Group E H-E20 (sentiment-conditioned SPRT); Group A Section 4 M7 (McNeil-Frey GARCH-EVT).
- **Feasibility 4:** VIX free; Bekaert-Hoerova SVAR is moderate engineering.
- **Impact 3:** ≥+0.02 AUC; VRP outperforms raw VIX.
- **Decay 3:** macro-feature; less arbitrage-decayed.
- **Evidence 4:** ≥5 anchor papers across Groups A/C/D/E.
- **Composite: 4 × 3 × 4 × 3 = 144.**

### H-17 — Sharpe-objective training (Lim-Zohren-Roberts) for K54 v3 with continuous sizing (Cartea-Jaimungal)
- **Master IDs:** **C-5** (Lim-Zohren-Roberts Sharpe-objective) + **C-6** (Cartea-Jaimungal continuous-sized entries).
- **Evidence:** Group D H-D4 + H-D5 (Lim-Zohren-Roberts 2019 Deep Momentum >2× Sharpe; Cartea-Jaimungal 2016 analytic optimal size linear in cointegration residual); Group F Rank 1 (meta-labeling alternative).
- **Feasibility 3:** custom Sharpe-objective training is non-trivial in LightGBM (needs custom obj); GBT framework supports it.
- **Impact 4:** +20-40% OOS Sharpe per Lim-Zohren-Roberts.
- **Decay 3:** complementary to H-1 meta-labeling.
- **Evidence 4:** ≥4 anchor papers Group D + Group F.
- **Composite: 3 × 4 × 4 × 3 = 144.**

### H-18 — Per-instrument volume-conditional volatility feature for indices
- **Master IDs:** Group B H15 (no MASTER ID — surface as new K-feature).
- **Evidence:** Group B H15 (Karpoff 1987; Lamoureux-Lastrapes 1990; Bollerslev-Li-Xue 2018; Drechsler-Moreira-Savov 2024); Group A CC8 (HAR-RV multi-scale).
- **Feasibility 4:** GARCH(1,1) + volume conditioning; trivial.
- **Impact 3:** asymmetric across asset classes; near-zero for FX, modest for indices.
- **Decay 3:** infrastructure feature.
- **Evidence 4:** ≥4 anchor papers Group B.
- **Composite: 4 × 3 × 4 × 3 = 144.**

### H-19 — Multi-level OFI + Hawkes intensity feature on MT5 ticks
- **Master IDs:** Group B H11 + H12 (no specific MASTER IDs).
- **Evidence:** Group B H11 (Cont-Cucuringu-Zhang 2023; Kolm-Turiel-Westray 2023; Cont-Kukanov-Stoikov 2014); Group B H12 (Bacry-Mastromatteo-Muzy 2015; Cont-Pourjafarian 2023); Group A Rank 15 (multivariate Hawkes).
- **Feasibility 3:** multi-level depth reconstruction non-trivial; tick package available.
- **Impact 3:** ≥+0.03 AUC for top-5 weighted OFI; Hawkes adds ≥+0.02.
- **Decay 4:** microstructure features less decay-prone.
- **Evidence 4:** ≥6 anchor papers Group A + Group B.
- **Composite: 3 × 3 × 4 × 4 = 144.**

### H-20 — Real-gold-price-percentile + GPR + EPU + IDEMV macro ensemble for XAU+XAG
- **Master IDs:** **A-8** (Erb-Harvey real-gold-price percentile) + **A-9** (Gold COT positioning) + **A-10** (Gold central-bank-flow).
- **Evidence:** Group C ranks #1/#2/#3/#4 + Section 3 (Erb-Harvey 2024; Bonato et al. 2019/2025 CNN-LSTM; Arslanalp-Eichengreen-Simpson-Bell 2023; Mittal-Mittal 2025 gold-silver ratio).
- **Feasibility 4:** WGC + FRED feeds (free); CFTC COT (D-4).
- **Impact 4:** ≥+3pp OOS AUC on the XAU+XAG cohort (only K54 v2 cohort with positive lift).
- **Decay 3:** macro-anchored; durable.
- **Evidence 5:** ≥6 anchor papers Group C.
- **Composite: 4 × 4 × 5 × 3 = 240.**

### H-21 — Track A anti-pattern classifier reformulation as side-conditional skill filter
- **Master IDs:** Reframed from CLAUDE.md unresolved item #7 (Track A failed AUC 0.65 → 0.55 OOS).
- **Evidence:** Group D H-D2 (Daniel-Moskowitz LONG-sizing modifier); Group E H-E10 (LONG decay faster than SHORT); memory `project_a6_decay_attribution_long_side_concentrated`.
- **Feasibility 4:** existing Track A artifact; reformulation as side-conditional + meta-label task.
- **Impact 3:** modest; complements H-5 side-aware sizing.
- **Decay 3:** addresses LONG-side selectivity collapse.
- **Evidence 4:** ≥4 anchor papers + 2 memories.
- **Composite: 4 × 3 × 4 × 3 = 144.**

### H-22 — Hansen SPA + Diebold-Mariano per-fold paired AUC + Reality Check forecast comparison
- **Master IDs:** **M-10** (Hansen SPA on K54-class lifts) + **M-11** (DM per-fold paired AUC) + **M-8** (B=1000 — DONE).
- **Evidence:** Group A Section 4 M3 + M8 (Giacomini-White 2006; Patton 2020 misspecified forecasts; White 2000 Reality Check; Hansen-Lunde-Nason 2011 MCS; Stepwise SPA).
- **Feasibility 5:** statsmodels has DM; Hansen SPA python-implementable.
- **Impact 3:** methodology hardening; not direct lift.
- **Decay 5:** every forward "X beats Y" claim must use these.
- **Evidence 5:** ≥8 anchor papers Group A.
- **Composite: 5 × 3 × 5 × 5 = 375.** (Borderline top-10; relegated because it bundles into H-6 retroactively; surface as standalone Q1.4 ship if H-6 not adopted.)

### H-23 — Christoffersen interval-coverage test + adaptive conformal calibration on K54 v3 outputs
- **Master IDs:** **K-14** (adaptive conformal 90%-coverage) + **M-14** (Christoffersen interval-coverage) + **P-3** (conformal calibration module).
- **Evidence:** Group F §5 production-plane block (adaptive conformal Zaffran et al. 2022 → 90% CI); Group A M14.
- **Feasibility 4:** mapie / nonconformist Python packages.
- **Impact 3:** decision-quality (calibrated probabilities) not headline lift.
- **Decay 3:** infrastructure.
- **Evidence 4:** ≥4 anchor papers Group A + Group F.
- **Composite: 4 × 3 × 4 × 3 = 144.**

### H-24 — Babu-Hoffman-Levine 2020 decomposition on H1-vs-H2 2026 decay attribution
- **Master IDs:** No specific catalog ID; surface as new methodology task.
- **Evidence:** Group D Theme 4 + Section 4 (Babu et al. 2020 CTA decomposition: trend-following 2010-2018 underperformance fully attributable to muted market moves, NOT signal-translation decay).
- **Feasibility 5:** closed-form decomposition on existing trade history; ≤1 day eng.
- **Impact 4:** if ≥40% of H2 LONG-decay reverses under vol-managed sizing (H-2), the urgency-of-prompt-overhaul collapses; ranks H-2 above prompt-engineering work.
- **Decay 5:** strategic re-frame of CEO #1 concern.
- **Evidence 3:** 1 anchor paper Babu et al. (decomposition methodology), 2 corroborating Group D papers.
- **Composite: 5 × 4 × 3 × 5 = 300.** (Borderline top-10; relegated because it's a one-off analysis not an architectural ship; surface as Q1.4-pre-week deliverable.)

### H-25 — DLinear + zero-shot foundation-model baseline gate before any sequence model
- **Master IDs:** **Q-1** (DLinear baseline) + **Q-2** (Time-LLM) + **Q-3** (Chronos) + **Q-4** (iTransformer) + **Q-5** (PatchTST) + **Q-6** (TCN) + **Q-7** (LSTM) + **Q-8** (sequence model decision).
- **Evidence:** Group F §4 (Zeng et al. 2023 DLinear AAAI Oral; Carriero-Pettenuzzo 2024 macro forecasting LLMs; foundation-model zero-shot benchmarks).
- **Feasibility 4:** all tools open-source; benchmarks free.
- **Impact 3:** Occam-test discipline; saves Q2 from chasing a fragile transformer.
- **Decay 4:** Q2 prerequisite.
- **Evidence 5:** ≥6 anchor papers Group F.
- **Composite: 4 × 3 × 5 × 4 = 240.**

### H-26 — F11 OB-zone decay vs retail-flow share regression (operationalize AMH)
- **Master IDs:** **E-4** (F11 OB-zone decay regression vs retail-flow share) + **U-12** (F2/F15 LONG decay attribution under Erb-Harvey lens) + **U-14** (McLean-Pontiff publication-decay validation).
- **Evidence:** Group E F-1 + Section 2 (Lo's AMH; McLean-Pontiff 2016); Group F §6 (edge decay = publication-and-replication property); memory `project_f11_ob_zone_decay_velocity_pinned`.
- **Feasibility 4:** retail-flow proxies (CFTC COT, retail-broker estimates); ≤1 week.
- **Impact 3:** strategic-frame validation; not direct lift.
- **Decay 5:** operationalizes CEO #1 concern.
- **Evidence 4:** ≥4 anchor papers Group E + Group F.
- **Composite: 4 × 3 × 4 × 5 = 240.**

### H-27 — Saliency-debiased prompt redesign for HALLUC-class precision-anchoring
- **Master IDs:** Group E H-E13 (saliency-debiased prompts; reduce decimal precision); ties to **L-1** tool-grounding.
- **Evidence:** Group E §4 (Frydman-Rangel 2014 saliency debiasing; Northcraft-Neale 1987 anchoring; Heath-Tversky 1991 competence); Group F Finding 4 (tool-grounding); memories `project_halluc_1_precision_bug_class_2026-04-27` + `project_eurusd_sl_root_cause`.
- **Feasibility 4:** prompt A/B; CEO approval per WF-1.
- **Impact 3:** complements H-10 tool-grounding; smaller standalone lift.
- **Decay 3:** addresses HALLUC root cause.
- **Evidence 4:** ≥4 anchor papers + 3 memories.
- **Composite: 4 × 3 × 4 × 3 = 144.**

### H-28 — Path-9 Feb-2026 window deep-dive
- **Master IDs:** **C-7** (Path-9 Feb-2026 window deep-dive) + **U-17** (Path-9 anomaly investigation).
- **Evidence:** `audit/AMBIGUITIES_AND_OPEN_QUESTIONS.md` CF-7 (path 9 carries 30% of mean lift; the only path with p<0.01); `audit/statistical_reevaluation.md` (path 9 contributes 26.5% of mean; cross-cohort confirmed).
- **Feasibility 5:** 1-2 day inspection of Path 9 test-fold composition.
- **Impact 4:** if a replicable condition is identifiable, gives a regime-dependent K54 specialist signal.
- **Decay 3:** research-only.
- **Evidence 3:** 2 audit refs + Group F decay-baseline framing.
- **Composite: 5 × 4 × 3 × 3 = 180.**

### H-29 — Per-fold feature stability vs production deployment performance regression
- **Master IDs:** **C-8** (per-fold feature stability vs production performance; Jaccard 0.072 implies fold-specific features won't generalize).
- **Evidence:** `audit/AMBIGUITIES_AND_OPEN_QUESTIONS.md` D3 / H3 (top-30 Jaccard overlap as overfit signature); Group A CC12 (spurious-regime / lucky-factor); Group F Finding 1 (tree ensembles + small-n discipline).
- **Feasibility 5:** 1-day analysis.
- **Impact 3:** methodology hardening for K54 v3; not headline lift.
- **Decay 4:** Q1.4 prerequisite.
- **Evidence 3:** 2 audit refs + 1 anchor paper.
- **Composite: 5 × 3 × 3 × 4 = 180.**

### H-30 — K54 v1 published 0.571 vs CPCV-honest 0.512-0.529 reconciliation
- **Master IDs:** **X-6** (K54 v1 baseline reconciliation).
- **Evidence:** `audit/canonical_v1_rerun.md` (CPCV mean AUC 0.5286 vs published 0.571); `audit/AMBIGUITIES_AND_OPEN_QUESTIONS.md` B1-B5; Group A CC7 (multiple-testing discipline).
- **Feasibility 5:** ≤1 day.
- **Impact 3:** baseline-integrity; supports H-6 retroactive sweep.
- **Decay 4:** prevents future v1-baseline inflation.
- **Evidence 3:** 2 audit refs + 1 cross-cutting finding.
- **Composite: 5 × 3 × 3 × 4 = 180.**

---

## Section 4 — Architectural composites (multi-hypothesis bundles)

References MASTER_BACKLOG.md Section B (B-1..B-8). Each composite below is a **dispatchable unit** (single agent or small parallel-agent team) bundling 2-7 individual hypotheses. Bundles validated / refined and cross-referenced to Top-10 + Tier-2 IDs.

### Composite C1 — K54 v3 master bundle (= MASTER_BACKLOG B-1)

- **Source:** MASTER_BACKLOG **B-1** = **K-18** = K-1 + K-4 + K-5 + K-6 + K-7 + K-8 + K-9 + K-10 + K-11 + K-12 + K-13 + K-14 + K-15.
- **Hypothesis-backlog mapping:** H-1 (master) + H-3 (volume-bar sampling K-1) + H-4 (Stoikov K-4 + Osler K-7 + power-law-age K-8) + H-7 (regime classifier K-9) + H-11 (signature features) + H-23 (conformal calibration K-14) + H-29 (TreeSHAP-stability K-15).
- **Validated:** the bundle correctly composes the regime-aware K54 v3 architecture endorsed across Groups A/B/F. The literature predicts **+0.04-0.07 AUC over Q1.3 baseline 0.571** (MASTER_BACKLOG K-18 estimate); after 50% realization haircut and CPCV-honest accounting, we expect **K54 v3 mean CPCV AUC ≥ 0.58** on n=2,326 cohort.
- **Refinement:** Add H-8 NAS_US30 specialist as a per-cohort routing layer (P-6 in MASTER_BACKLOG.md) ON TOP of the global K54 v3. The global model handles XAU+XAG + FX cohorts; specialist handles indices.
- **Combined expected impact:** AUC +0.05-0.08 (post-haircut) + meta-label realized-R lift +0.05-0.10R/trade.
- **Dispatch shape:** single Q1.4 modeller agent with parallel sub-tasks (feature-engineering / pooling / meta-label / specialist).
- **Wallclock:** 1 week if subscription-only (per H-1 estimate × small overhead).

### Composite C2 — Component 3C Vol-Conditioning bundle (= MASTER_BACKLOG B-2)

- **Source:** MASTER_BACKLOG **B-2** = **V-9** = V-1 + V-2 + V-3 + V-4 + V-5 + V-6.
- **Hypothesis-backlog mapping:** H-2 (master) + H-16 (VIX-conditional sizing).
- **Validated:** highest-EV / lowest-cost addition per Group D Section 3; ≥6 anchor papers; Sharpe lift 30-50% literature, 15-25% post-haircut.
- **Refinement:** vol-conditioning sigma multiplier is the natural input to H-1 meta-label head (multiplies sizing) AND to H-5 RCK λ. Bundles MULTIPLICATIVELY with both. Babu-2020 decomposition (H-24) is a pre-requisite analysis to allocate effort between H-2 and H-1 prompt-overhaul work.
- **Combined expected impact:** +20-35% Sharpe + +0.10-0.18R/trade additive.
- **Dispatch shape:** rule-based v1 first (2 weeks), then ML-trained sigma in K54 v3 production track.
- **Wallclock:** 2-3 weeks v1; 1 quarter for ML upgrade.

### Composite C3 — Risk-policy bundle (= MASTER_BACKLOG B-3)

- **Source:** MASTER_BACKLOG **B-3** = **R-9** = R-1 + R-2 + R-5 + R-6 + R-7 + V-8.
- **Hypothesis-backlog mapping:** H-5 (master) + H-2 (vol-scaling V-8 overlap).
- **Validated:** Group E Section 5 endorses each component independently; bundle is the literature-grounded path from S79 uniform_fn 2.0% to per-instrument multi-component optimal sizing.
- **Refinement:** add Roy 1952 safety-first frame as the OBJECTIVE function (per Group E F-4): maximize geometric mean R subject to `P(daily MTM-DD ≥ 4%) ≤ ε` for ε ∈ {0.01, 0.05, 0.10}. CEO ε choice is the key parameter. Sornette crash-aware Kelly (memory `project_distributional_findings` calibrates at fraction 0.4) is empirical anchor.
- **Combined expected impact:** +20-35% Sharpe + +0.05-0.15R/trade + Higher P(pass FN).
- **Dispatch shape:** Q1.4 mid-track ship (2-3 weeks).

### Composite C4 — Asset-class-specialist bundle (= MASTER_BACKLOG B-4)

- **Source:** MASTER_BACKLOG **B-4** = A-1 + A-2 + A-3 + A-4 + A-5 + A-6 + A-7 + A-8 + A-11.
- **Hypothesis-backlog mapping:** H-8 (master) + H-13 (calendar features) + H-14 (NAS100/US30 OPEX + dealer-gamma) + H-20 (XAU+XAG macro ensemble).
- **Validated:** Group C §1 + final-report central claim — JPY-pair / GBP-pair / dollar-pair split is mandatory; NAS_US30 dealer-gamma cures cross-period sign-flip.
- **Refinement:** ADD A-14 (Aquilina BIS JPY-carry-unwind regime classifier) and A-12 (Krohn-Mueller-Whelan FX-fix W-shape) — both currently in Group C ranks but not in B-4 source. Drop A-11 (LBMA fix anomaly) into H-14 for consolidation.
- **Combined expected impact:** +0.02-0.05 AUC on the 4 currently-decayed cohorts; cures Q1.3 cohort sign-flip.
- **Dispatch shape:** parallel per-cohort modellers (4 specialists).
- **Wallclock:** 4-6 weeks (slowest top-10 hypothesis).

### Composite C5 — AI-grounding bundle (= MASTER_BACKLOG B-5)

- **Source:** MASTER_BACKLOG **B-5** = L-1 + L-2 + L-4 + L-6 + L-7 + L-8.
- **Hypothesis-backlog mapping:** H-10 (master) + H-27 (saliency-debiased prompts).
- **Validated:** Group F Stream C; QuantMCP 80% hallucination reduction; Bull/Bear/Judge already wired.
- **Refinement:** ADD L-3 (Reflexion post-trade reflection) as default-off shadow path. The bundle is structurally LLM-architecture; should ship after H-1 K54 v3 (the ML-primary path) is in production, not before.
- **Combined expected impact:** 70-80% HALLUC-class precision-bug reduction + ≥0.05R Reflexion expectancy lift.
- **Dispatch shape:** L-track engineering (4-6 weeks; Q1.4 tail or Q2 early).

### Composite C6 — Methodology-discipline bundle (= MASTER_BACKLOG B-6)

- **Source:** MASTER_BACKLOG **B-6** = M-1 + M-2 + M-3 + M-4 + M-7 + M-12 + M-13.
- **Hypothesis-backlog mapping:** H-6 (master) + H-22 (Hansen SPA + DM + Reality Check) + H-29 (per-fold feature stability) + H-30 (K54 v1 baseline reconciliation).
- **Validated:** Group A Section 4 + `audit/statistical_reevaluation.md` central role; M-7 + M-13 already adopted; M-1..M-4 + M-12 still pending.
- **Refinement:** ADD M-5 (Inoue-Kilian vs CPCV-honest doctrine resolution per-instrument) as a per-cohort decision; ADD M-15 (Bayesian-backtesting parallel track) as a long-term diversification (not Q1.4 critical).
- **Combined expected impact:** prevents next K54-v2-style false PASS; saves 1-2 quarters research budget.
- **Dispatch shape:** single methodology agent with retroactive sweep + forward-gating documentation.
- **Wallclock:** 2-3 days.

### Composite C7 — Edge-mechanism validation bundle (= MASTER_BACKLOG B-7)

- **Source:** MASTER_BACKLOG **B-7** = E-1 + E-2 + E-3 + E-4.
- **Hypothesis-backlog mapping:** H-15 (Coval-Shumway second-half-of-session) + H-26 (F11 OB-zone vs retail-flow regression) + standalone E-2 (Toth-Bouchaud V-shape latent liquidity test).
- **Validated:** Group B §2.1 (3-mechanism convergence); Group D Theme 5; Group E §3.
- **Refinement:** ADD E-5 (OB-precision feature uncorrelated-with-OB-precision discovery) — the Renaissance-Medallion-style aggregation principle (Group F §6). Without E-5, the bundle stays mechanistic; with E-5, it generates the next-generation feature catalog.
- **Combined expected impact:** validates GTOS edge mechanism + opens the next 5-10 uncorrelated features.
- **Dispatch shape:** 4 parallel mechanism-validation agents.
- **Wallclock:** 1-2 weeks.

### Composite C8 — Quick-win bundle (= MASTER_BACKLOG B-8)

- **Source:** MASTER_BACKLOG **B-8** = M-1 + M-7 + C-1 + C-2 + K-4 + E-1 + L-6 + L-7 + P-4 + Q-1.
- **Hypothesis-backlog mapping:** H-6 (M-1 + M-7) + H-15 (C-1 + E-1) + H-4 (K-4 + P-4) + H-25 (Q-1 DLinear baseline) + standalone C-2 (disposition-effect feature) + L-6 (HALLUC-2 logger) + L-7 (Q71 slippage logger).
- **Validated:** designed as do-this-week dispatch in MASTER_BACKLOG.md; each component <1-day eng.
- **Refinement:** REMOVE L-6 + L-7 (operational ops, not ML-research); ADD H-24 (Babu-2020 decomposition) as a 1-day strategic-re-frame analysis. The result is a coherent "1-week pre-Q1.4 sprint" deliverable.
- **Combined expected impact:** ships methodology + edge-validation infrastructure ahead of K54 v3 dispatch; reduces Q1.4 risk.
- **Dispatch shape:** 5-7 parallel agents (1-day each).
- **Wallclock:** 1 week.

### NEW Composite C9 — Cross-period robustness gate bundle (NEW; not in MASTER_BACKLOG)

- **Hypothesis-backlog mapping:** H-1 (uses backfill cohort) + H-30 (baseline reconciliation under cross-period) + H-26 (decay regression) + new gate: 2022-2023 → 2024-2026 train/test split as Q1.4 promotion gate addition.
- **Rationale:** `data_backfill_2022_2023.md` opened the cross-period robustness gate at 7-of-7 instruments. THIS IS THE SINGLE STRUCTURAL CHANGE THAT MAKES Q1.4 SUBSTANTIVELY DIFFERENT FROM Q1.3. The gate must be made formal across ALL Q1.4-candidate hypotheses, not just K54 v3.
- **Validation:** every primary Q1.4 hypothesis (H-1, H-2, H-5, H-7, H-8) must pass cross-period robustness on the new 2022-2023 → 2024-2026 split, not just the 2026-Q1+ split. Lift sign preserved + magnitude within ±50%.
- **Dispatch shape:** part of every Q1.4 modeller dispatch.
- **Wallclock:** integrated into each hypothesis; no incremental cost.

### NEW Composite C10 — Live-trade enrichment + closed-trade meta-label feedback (NEW)

- **Hypothesis-backlog mapping:** **O-8** (live_evaluations + trade_records enrichment gap) + **O-1** (`_trade_index.json` frozen-bug fix) + H-1 (meta-label triple-barrier labels feed from trade_records).
- **Rationale:** memory `project_trade_records_enrichment_gap` notes April 2026 records all `execution: null`. H-1 meta-labeling needs proper triple-barrier labels; the operational gap blocks the architectural ship.
- **Validation:** before H-1 ships, fix O-1 + O-8 to ensure trade_records enriched with execution outcome (TP / SL / TIMEOUT + realized R).
- **Dispatch shape:** main-thread O-1 fix + research-side schema validation.
- **Wallclock:** 2-3 days operational + 1 day validation.

---

## Section 5 — Reframings of existing GTOS findings

The literature changes how we INTERPRET prior GTOS findings. Each reframing cites the synthesis source + the prior GTOS finding it reframes.

### R1 — F11 OB-zone advantage decay reframed: McLean-Pontiff baseline + AMH publication-and-replication, NOT extinction

- **Prior GTOS finding:** F11 attribution: decay-dominant ~78%, methodology ~22%; +16.8pp pre-2026 → +12.1pp H1-2026 → +4.6pp H2-2026 (memory `project_f11_ob_zone_decay_velocity_pinned`).
- **Literature reframe (Group E §2 + Group F §6):** F11's measurement is **squarely inside McLean-Pontiff 2016's distribution** (26% OOS, 58% post-publication decay across 97 anomalies). This is industry-baseline edge-decay, NOT GTOS pathology and NOT "extinct edge". Lo's AMH says decay is property of publication-and-replication (TradingView OB/SMC templates, retail YouTube channels) — not mechanism failure. McLean-Pontiff baseline ~5%/year sets the alarm threshold; >10%/year sustained decay is the actionable signal.
- **Operational implication:** S1 monthly-decay shadow monitor's threshold should be ~5%/year baseline, not generic "decay alarm". H-9 BOCPD-AR-score-driven detector should calibrate FPR ≤ 5% against this baseline. Strategic narrative shifts from "fix the OB edge" to "aggregate uncorrelated edges" (Renaissance Medallion model per Group F §6 + Zuckerman 2019).

### R2 — F15 regime-conditioned LONG-side decay reframed: regime is universal not GTOS-specific

- **Prior GTOS finding:** F15 regime is the load-bearing decay axis (bonf_p=0.0016 with proper backfill, +48.3pp attribution); A6 LONG-side selectivity collapse 48.4% → 18.8%; F2 trending_bull cell -59.8pp (memory `project_f15_synthesis_regime_is_load_bearing`).
- **Literature reframe (Group A CC3 + CC11 + Group D Theme 1 + Group E F-1 + Group D Theme 2):** Regime-conditioned decay is the **canonical realization** of Cooper-Gutierrez-Hameed 2004 (momentum +0.93%/mo after positive market state, -0.37%/mo after negative) + Daniel-Moskowitz 2016 (forecastable momentum-crashes Sharpe 2× static) + Lo 2017 AMH (regime-conditioned cohort failures recur). It's NOT a GTOS-specific defect.
- **Operational implication:** H-7 sticky-HDP-HMM regime classifier + H-1 K54 v3 regime-prob feature ARE the literature-endorsed response. Wood-Roberts-Zohren 2022 hybrid slow-momentum + fast-reversion via online change-point is the Phase 2 K54 v3 recipe. Don't try to "eliminate" LONG-side decay; instrument and gate it. Bundles directly with H-5 side-aware sizing.

### R3 — Q1.3 K54 v2 CPCV-honest p=0.675 reframed: small-but-real signal at sample-size limit, NOT no-signal

- **Prior GTOS finding:** Q1.3 K54 v2 FAILED CPCV-honest gate (p=0.675); 95% CI [-0.0962, +0.1580] crosses zero (`audit/statistical_reevaluation.md`).
- **Literature reframe (Group F Finding 3 + Group A CC7 + Group B §7.2):** The **AUC-vs-realized-R gap is structural**, not GTOS pathology — universal across all proxy-based learning (cross-entropy / AUC / training reward), confirmed by Avramov-Cheng-Metzker 2023 + Israel-Kelly-Moskowitz 2020 + quantum RL (arXiv 2506.20930 2025). Lucchese-Pakkanen-Veraart 2024 sets **realistic Sharpe ceiling ~0.5** for high-quality lit-book data — GTOS at degraded MT5 retail-broker M15 should expect **substantially less, likely Sharpe 0.25-0.40**. Architecture A's PBO 0.20 + lift +0.0492 + 4-of-4 groups beating K54 v2 is the small-but-real signal Group F predicts.
- **Operational implication:** Don't aim for K54 v3 OOS Sharpe > 0.5; aim for the small-durable-edge frame. Meta-labeling (H-1) closes the AUC-vs-realized-R gap by separating "is direction right?" from "should we size up?" — the architectural pattern Lopez de Prado 2018 + Buffett's-Alpha (Frazzini-Kabiller-Pedersen 2018) endorse. Q1.4 thresholds should target AUC ≥ 0.55 + realized-R lift ≥ +0.05R/trade, not AUC ≥ 0.65.

### R4 — HALLUC-1 NAS100 93% reframed: precision-bug class with mechanistic root, NOT AI failure

- **Prior GTOS finding:** HALLUC-1 NAS100 93% live "hallucination" diagnosed as deterministic precision bug (memory `project_halluc_1_precision_bug_class_2026-04-27`); F12 confirmed H4 precision-rounding for 7-record cohort.
- **Literature reframe (Group F Finding 4 + Group B §6.6):** This is **exactly** the predicted outcome of NOT having tool-grounded numeric facts (FAITH 2025: 8-15% intrinsic frontier-model hallucination on finance tables). FinAgent 2024 + QuantMCP 2025 show 70-80% reduction via tool-grounding. Group B §6.6 + Group C ranks #13/#15/#16 connect NAS100 hallucination concentration to dealer-gamma + OPEX-strike clusters — there's a real microstructure pattern the LLM is poorly handling.
- **Operational implication:** H-10 tool-grounding directly attacks the bug class; H-14 OPEX/dealer-gamma feature engineering attacks the underlying microstructure pattern that the LLM misses. Bundles for NAS_US30 cohort recovery.

### R5 — Confidence scorer "rubber stamp" reframed: AUC measure was wrong; calibration should use Christoffersen + adaptive conformal

- **Prior GTOS finding:** Confidence scorer confirmed useless (98% get confidence=80) per CLAUDE.md.
- **Literature reframe (Group F §5 production-plane + Group A M14):** The "rubber-stamp" pathology is consistent with mis-calibrated probability (PAtton 2020 misspecified forecast comparison). The fix is **adaptive conformal calibration** (Zaffran et al. 2022 → 90% CI) + Christoffersen interval-coverage test (M14). The AI's confidence is one feature; the K54 v3 + meta-label head + adaptive conformal pipeline gives a calibrated probability that is operationally meaningful.
- **Operational implication:** H-23 Christoffersen + adaptive conformal directly fixes the rubber-stamp pathology in K54 v3 outputs. This was an unsolved CLAUDE.md item; the literature provides the closed solution.

### R6 — Track A anti-pattern AUC 0.65 → 0.55 OOS reframed: classic high-dim overfit at small-n, NOT failed mechanism

- **Prior GTOS finding:** Track A anti-pattern classifier does NOT replicate OOS (AUC 0.65 → 0.55, n=75, CLAUDE.md item #7).
- **Literature reframe (Group A CC12 + Group F Finding 1 + Q1.3 audit CF-11):** At n=75 with classifier-class features, AUC drop of 0.10 is the predicted high-dim overfit signature (Q1.3 audit CF-11: "high split-gain doesn't mean correct direction"). Group F Finding 1: tree ensembles need ≥10× labels at fixed S/N. Track A's failure is a sample-size-and-feature-count problem, not a mechanism problem.
- **Operational implication:** H-21 reformulates Track A as side-conditional skill filter on the Q1.4 cohort (n=2,326 vs n=75); 30× more data dissolves the high-dim noise. Bundles with H-5 side-aware sizing.

### R7 — V4 + LIRA shelved as cascade-prompt-recovery reframed: Q3+ research, NOT immediate priority

- **Prior GTOS finding:** V4 + LIRA SHELVED (V3 confirmed empirically-best); cascade prompt LOST-IRRECOVERABLE (recovered template at `research/prompt_cascade_ob_test/RECOVERED_v3_cascade_template.py.txt`); post-Phase-2 research candidate (CLAUDE.md item #8).
- **Literature reframe (Group F Stream A + Stream B):** Group F's hierarchy is: **Hybrid (LLM + traditional ML) beats pure-LLM in finance** (Y. Li 2023 ICAIF). PIXIU/FinMA: stock-prediction stays at chance even for fine-tuned domain models. The K54 v3 (H-1) production path is what closes the gap; cascade-prompt rebuild is a Q3+ secondary research track.
- **Operational implication:** Don't reopen V4/LIRA before H-1 K54 v3 ships. Cascade-prompt rebuild is X-7 in MASTER_BACKLOG.md (T3 tier); Q1.4 priority is K54 v3.

### R8 — Component 3B Bull/Bear/Judge default-OFF reframed: literature endorses; activation gating is correct discipline

- **Prior GTOS finding:** Component 3B Bull/Bear/Judge research-door-wired (N62, default OFF); 30-day shadow data + CEO DELETE/WIRE/LEAVE decision pending (CLAUDE.md item #10).
- **Literature reframe (Group F Stream B):** TradingAgents 2024 + AlphaAgents 2025 (BlackRock) + FinCon 2024 NeurIPS — structured Bull/Bear/Judge debate beats single-agent (5-15% lift in 30d-3mo backtests). BUT: long-horizon LLM-trading evaluation (arXiv 2505.07078, 2025) shows decay or inversion at 3+ years.
- **Operational implication:** Default-OFF is the correct discipline. H-10 enables shadow-mode activation and gates production by ≥+0.05R/trade lift over 30d. Pair with H-9 BOCPD-AR-score-driven decay observability so any debate-driven edge is monitored explicitly.

### R9 — XAUUSD WR 62% Validated Number reframed: survives K52 + DSR pending; FVG-impulse REVERSED

- **Prior GTOS finding:** XAUUSD WR vs breakeven 62% (n=129) survives K52 retest (p=0.0249, memory `project_k52_validated_numbers_status_2026-04-27`); FVG-in-impulse signal FAILS (direction REVERSED in H2-2026, FVG-WR 72.6% < non-FVG 75.4%).
- **Literature reframe (Group A M1 + Group F Finding 2):** XAUUSD WR 62% must still pass DSR + effective-N (H-6) before being treated as "validated". With cumulative trial count ~200, noise ceiling sqrt(2 ln 200) ~ 3.27 — needs to clear that. FVG-impulse REVERSAL is classic McLean-Pontiff post-publication arbitrage (Group E §2.3) — exactly what AMH predicts for over-published patterns.
- **Operational implication:** H-6 retroactive DSR sweep gates the entire "Validated Numbers" table. K54 v3 (H-1) should DROP FVG-impulse as a positive feature (memory `project_k52_validated_numbers_status_2026-04-27`).

---

## Section 6 — Closed questions (resolved by literature)

The following ambiguities from `audit/AMBIGUITIES_AND_OPEN_QUESTIONS.md` and CLAUDE.md unresolved items are RESOLVED by Phase 2 syntheses.

### Closed Q1 — Why does K54 v1 perform AUC 0.512 in CPCV vs published 0.571?

**Audit ambiguity B1.** Resolved by `audit/canonical_v1_rerun.md` (CPCV mean AUC 0.5286) + Group F Finding 1 (tree ensembles need ≥10× labels at fixed S/N; K54 v1 published 0.571 was a single-fluky-test-slice number on n=94, not robust under CPCV). H-30 formalizes the reconciliation.

### Closed Q2 — Should Q2 lead with DLinear baseline before sequence models?

**Master backlog Q-1.** Resolved by Group F §4 (YES, DLinear baseline must come first; sequence models follow only if they beat it). Group F §4 spec: DLinear → zero-shot foundation models (Time-MoE, Lag-Llama, Chronos, MOIRAI) → TCN → PatchTST/iTransformer → LSTM/Transformer (skip vanilla Transformer). H-25 captures.

### Closed Q3 — Hybrid vs pure-replacement vs pure-supplementation for AI architecture?

**Master backlog L-track.** Resolved by Group F §5 (Hybrid via meta-labeling, NOT replacement). Three converging streams: Y. Li 2023 ICAIF "Hybrid LLM + traditional beats pure-LLM in finance"; PIXIU/FinMA "stock-prediction stays at chance even for fine-tuned domain models"; Tool-grounded LLM > prompt-only LLM (QuantMCP 2025 80% reduction). Endorsed path: K54 v3 + meta-labeling + conformal calibration as primary local; LLM stays as Component 3A advisory; K55 shadow harness measures crossover.

### Closed Q4 — Is GTOS at $100k below capacity-decay band?

**Master backlog U-13 (Naik-Ramadorai-Stromqvist relevance).** Resolved by Group F §6 (YES, $100k is below the capacity-decay band; capacity binds at $250M+). Stein 2005: GTOS as closed-end-CEO-financed prop-trade is structurally redemption-immune. Don't optimize for capacity-decay before $1M AUM. Strategic frame: optimize for edge-discovery rate over edge-preservation.

### Closed Q5 — VPIN as primary gate or vol-volume proxy?

**Master backlog (no specific ID; surfaces in Group B H14).** Resolved by Group B §5.1 + H14 (Andersen-Bondarenko 2014 critique stands; VPIN naive is mechanical vol-volume proxy; BV-VPIN deserves one shadow test but is not headline). Don't ship VPIN as a gate.

### Closed Q6 — Does the "M15-aggregation null" refute microstructure relevance?

**Memory `project_microstructure_archived_2026-04-27` + master backlog X-1/X-2/X-3.** Resolved by Group A CC2 + Group B §2.2 (NO, M15 is the wrong clock; signal is at sub-1-min — sampling artifact). H-3 captures the architectural fix.

### Closed Q7 — Is loss aversion λ ≈ 2 a universal constant?

**Master backlog R-8 (Walasek 2025 λ-context-dependence audit).** Resolved by Group E F-3 (NO; λ ≈ 1.07 in symmetric/unordered subsets, λ ≈ 2 only in asymmetric/ordered conditions). Trading IS asymmetric and ordered → λ ≈ 2 still applies operationally for trading-context decisions. Inverted-TP gate justified. Cross-applying λ=2 to non-trading CEO decisions is questionable.

### Closed Q8 — Square-root vs 3/5 power impact law?

Resolved by Group B §5.2 (both are right at different scales; canonical sqrt holds for small/medium; 3/5 fits very large meta-orders). For GTOS retail-size, sqrt approximation is sufficient.

### Closed Q9 — 0DTE-amplification: real or narrative?

**Group C ranks #15/#16.** Resolved by Group B §5.4 + Group C drop-list #2 (NO 0DTE-amplification in NDX; Vasquez-Amaya-Pearson-Garcia-Ares 2024 + Dim-Eraker-Vilkov 2024 reject). Don't add NDX-specific 0DTE feature. Standard *monthly* OPEX effects (Baltussen-Terstegge-Whelan 2024; Stoll-Whaley 1987-1991) ARE material — H-14 captures.

### Closed Q10 — Should Q1.4 use per-instrument-group LightGBM ensembles?

**Audit ambiguity C1.** Resolved by Group C §1 + final-report (YES for asset-class blocks; NO for arbitrary instrument pairs). Specific blocks: metals / JPY-crosses / indices / GBPUSD; NOT a generic "FX block". H-8 captures.

---

## Section 7 — New ambiguities surfaced by literature

The Phase 2 syntheses surface new questions that were NOT in `AMBIGUITIES_AND_OPEN_QUESTIONS.md` or MASTER_BACKLOG.md.

### NA1 — Inoue-Kilian 2005 + Diebold 2015 vs Lopez de Prado AFML CPCV-honest doctrine: which is GTOS's correct paradigm?

**Source:** Group A Section 5 D1 — Inoue-Kilian 2005 (02-#30) + Diebold 2015 (02-#26) argue **IS tests with proper SE + multiple-testing correction often beat OOS tests**, directly contradicting Lopez-de-Prado AFML CPCV-honest doctrine. **Master backlog:** **M-5** + **U-1**. **Question for CEO:** does Q1.4 stick with CPCV-OOS for new feature exploration AND adopt full-sample IS for already-decided regime-cells (e.g., F2 trending_bull LONG)? Affects Q1.4 design choice. **Recommended dispatch:** parallel agents — CPCV vs full-sample-IS-with-Romano-Wolf StepM on the F2 cohort — under both methodologies.

### NA2 — Gamma-sign feature constructibility from MT5 alone vs needing CBOE feed?

**Source:** Group C ranks #13/#15 + Group B §6.6. **Master backlog:** **A-1** + **A-2** + **U-2** + **D-3**. **Question:** can GTOS reconstruct dealer-gamma sign sufficiently from VIX1D-VIX9D + VRP-delta on MT5 + free public proxies, or does it need a paid CBOE GEX feed? Group C ranks #13 implies free public proxies suffice. **Recommended dispatch:** scout agent comparing free-proxy vs reference GEX on a 30-day overlap window.

### NA3 — Stoikov micro-price benefit at M15 vs only at finer scales?

**Source:** Group B §6.1 + Master backlog **K-4** + **U-3**. **Question:** does Stoikov micro-price provide benefit at M15 timeframe, or only at sub-1-min where microstructure lives? Group B implies "small but consistent edge across all 7 instruments" but the explicit evaluation at M15 is unclear. **Recommended dispatch:** drop-in evaluation in K54 v3 ablation (part of H-1).

### NA4 — Pooled multi-instrument benefit per-instrument sweep — which instruments gain most?

**Source:** Group B §2.4 + Group F Rank 2. **Master backlog:** **K-5** + **K-6** + **U-4**. **Question:** Sirignano-Cont 2019 shows pooled training works for stocks; does it work for FX/commodities/indices in the same model? Group F Rank 2 predicts +0.03-0.05 AUC for data-poor cells. **Recommended dispatch:** part of H-1 ablation (per-cohort lift analysis).

### NA5 — Component 3C realization haircut — is 50% conservative?

**Source:** MASTER_BACKLOG.md discipline gate "Treat literature-derived predictions as upper bounds (50% realization in production is the planning baseline)" + **U-7**. **Question:** is 50% the right haircut for vol-conditioning? Some interventions (Sornette crash-aware Kelly) have stronger causal anchors than others (Heath-Tversky competence preference). **Recommended dispatch:** per-hypothesis realization-haircut estimate from Phase 1 worker confidence scores.

### NA6 — XAU_XAG calendar-feature signal: genuine OPEX-week mechanism vs date-memorization artifact?

**Source:** `audit/architecture_ab.md` §1.5 (top-30 dominated by calendar features `days_to_OPEX`, `day_of_year_cos/sin`); cross-period drop 97-100%. **Master backlog:** **C-3** (XAU_XAG calendar-feature attribution audit; not in current MASTER_BACKLOG; surface as new task). **Question:** is the XAU_XAG calendar dominance memorization or mechanism? Group B + Group C imply LBMA fix + macro-announcement calendar IS mechanism (durable Caminschi-Heaney 2014). H-13 + H-14 directly test. **Recommended dispatch:** post-H-1 ablation — drop calendar features and re-evaluate.

### NA7 — Per-instrument loss-aversion λ from order-flow asymmetry: feasible feature or research-only?

**Source:** Group E H-E12 (P29 Walasek-Mullett-Stewart 2025). **Question:** can per-instrument λ be derived from order-flow asymmetry around stop-out clusters and used as a K54 v3 feature? Group E H-E12 says yes; literature is thin on FX/commodity loss-aversion measurement. **Recommended dispatch:** Q2 research candidate; feasibility check on tick-data after H-1 ships.

### NA8 — Babu et al. 2020 decomposition results — what fraction of H2-2026 LONG-decay reverses under vol-managed sizing?

**Source:** Group D Theme 4 + final-report; H-24 in this backlog. **Question:** if Babu decomposition shows ~40-60% of H2 underperformance is move-magnitude (vol regime) rather than signal-translation, then S79 sharpe_weighted (H-2) auto-recovers significant fraction without prompt-overhaul. **Top newly-surfaced ambiguity** — directly answers "do we prioritize H-2 vol-conditioning over H-10 prompt-overhaul work?" **Recommended dispatch:** H-24 standalone 1-day analysis BEFORE Q1.4 K54 v3 dispatch (the decomposition number gates the Q1.4 priority order).

### NA9 — Renaissance Medallion edge-aggregation — feasible at GTOS scale or aspirational?

**Source:** Group F §6 (Cornell 2020; Zuckerman 2019). **Master backlog:** **U-15**. **Question:** how many uncorrelated edges does GTOS need to aggregate to match Medallion's no-down-year durability? Group F §6 implies the answer is "many small" but doesn't quantify. **Recommended dispatch:** Q3+ research; not Q1.4 critical.

### NA10 — Adaptive conformal calibration vs Christoffersen: which goes first?

**Source:** Group F §5 + Group A M14. **Master backlog:** **K-14** + **M-14**. **Question:** Group F endorses adaptive conformal directly; Group A endorses Christoffersen interval-coverage test. Are they competing or complementary? **Recommended:** Christoffersen first (closed-form test of any K54 v3 confidence-band feature); adaptive conformal is the SOLUTION when Christoffersen FAILS. Sequenced.

---

## Section 8 — Recommended Q1.4 spec

### Q1.4 hypothesis text (verbatim, ready for `PRE_REGISTERED_HYPOTHESES.md` append)

> **Q1.4 hypothesis (pre-registered).** A K54 v3 model architected as (i) global LightGBM with per-fold top-100 feature screening (de Prado AFML §8.5), (ii) Lopez-de-Prado meta-labeling secondary classifier on triple-barrier outcome labels (TP/SL/TIMEOUT) feeding sizing in {0, 0.5, 1.0} × `risk_per_trade_pct`, (iii) Kyle-Obizhaeva W-unit pooled training across 7 instruments with one-hot instrument-id, and (iv) NAS_US30 specialist routing layer activated when `symbol ∈ {NAS100, US30_cash}` will achieve, on the post-2022-2023-backfill cohort (n ≈ 2,326), all of the following:
>
> - (a) **Mean CPCV AUC ≥ 0.55** under CPCV-honest training-overlap-weighted SE.
> - (b) **Lift over canonical K54 v1 ≥ +0.04** with deflated-Sharpe-corrected combined p < 0.01 AND DSR + effective-N + B=1000 null-p ≥ 0.99 + PBO < 0.40.
> - (c) **Cross-period robustness on TWO splits:** (i) train 2022-2023 / test 2024-2026 lift sign preserved + magnitude within ±50%; (ii) train ≤ 2026-01-01 / test 2026-01-01+ lift sign preserved + per-cohort lift sign preserved on ≥3 of 4 effective groups.
> - (d) **Per-instrument-group floor:** AUC ≥ 0.50 on ALL 4 effective groups; NAS_US30 specialist beats global by ≥+0.05 on its cohort.
> - (e) **Realized-R lift on the J46-J49 portfolio policy holdout: ≥ +0.05R/trade** with stationary block bootstrap (Politis-Romano) p < 0.01.
> - (f) **Feature stability gate:** ≥30 features in top-50 across ≥80% of CPCV paths (Jaccard overlap ≥ 0.6).
> - (g) **Holdout 2026-04-29 → 2026-05-12 reserved** for end-of-Q1 directional discipline check ONLY (no numeric AUC gate). Calibration measured via Christoffersen interval-coverage test.

### Q1.4 thresholds (gates a-g with specific numeric values; copied above for clarity)

| Gate | Spec | Threshold |
|------|------|-----------|
| (a) CPCV-honest AUC | mean CPCV AUC | **≥ 0.55** |
| (b) Lift + DSR + PBO + null | lift ≥ +0.04 AND DSR-p < 0.01 AND null-p ≥ 0.99 AND PBO < 0.40 | **all 4 must hold** |
| (c) Cross-period robustness | lift sign preserved on (i) 2022-2023→2024-2026 AND (ii) 2026-Q1+ test | **both, magnitude within ±50%** |
| (d) Per-group floor | AUC ≥ 0.50 on 4-of-4 groups | **4-of-4** |
| (d') NAS_US30 specialist | Specialist AUC vs global delta on NAS+US30 cohort | **≥ +0.05** |
| (e) Realized-R lift | J46-J49-policy holdout | **≥ +0.05R/trade**, block bootstrap p<0.01 |
| (f) Feature stability | top-50 Jaccard overlap | **≥ 0.6** |
| (g) Calibration | Christoffersen interval-coverage on holdout | **PASS at α=0.05** |

### Q1.4 architecture (locked spec)

**K54 v3 = Hybrid architecture:**

1. **Global model:** LightGBM with per-fold top-100 feature screening (Architecture A from Q1.3 audit).
2. **Specialist routing:** symbol ∈ {NAS100, US30_cash} → NAS_US30 specialist (Architecture B winner from Q1.3 audit).
3. **Pooling:** all 7 instruments + Kyle-Obizhaeva W-unit normalization + one-hot instrument-id feature.
4. **Meta-labeling head:** secondary LightGBM on triple-barrier outcome labels; output sizing ∈ {0, 0.5, 1.0}.
5. **Adaptive conformal calibration:** Zaffran et al. 2022 → 90% CI on K54 v3 outputs (per Group F §5 production-plane spec).
6. **Cohort:** n ≈ 2,326 (Q1.3 528 + 2022-2023 backfill 1,798).
7. **Feature catalog:** 1,234 base + Stoikov micro-price (K-4, drop-in) + Osler stop-cluster (K-7, FX-only) + power-law OB-age (K-8) — total ≈ 1,237 candidates → screened to ≤100 per fold.
8. **Validation:** paired-fixed-HP CPCV K=6/N=2 (15 paths) + 7-day purge / 1-day embargo + CPCV-honest training-overlap-weighted SE (Group A M7) + cross-period TWO splits.

### Q1.4 dispatch shape (which agents, which order, which MASTER_BACKLOG IDs)

**Pre-week sprint (Composite C8 quick-win, parallel; ~1 week before Q1.4):**

1. H-6 retroactive DSR sweep agent (M-1 + M-2 + M-3 + M-4 + M-7 + M-12 + M-13). Output: updated CLAUDE.md "Validated Numbers" table + `dsr_diagnostics.json` schema.
2. H-24 Babu-2020 decomposition agent (1 day standalone). Output: H1-vs-H2 2026 decay attribution; gates Q1.4 priority order (vol-conditioning vs prompt-overhaul).
3. H-15 Coval-Shumway second-half-of-session A/B agent (C-1; ≤1 day). Output: free intraday-time feature for K54 v3.
4. H-30 K54 v1 baseline reconciliation agent (X-6; ≤1 day). Output: confirmed K54 v1 CPCV anchor at 0.512-0.529.
5. C10 trade_records enrichment fix (O-1 + O-8; main-thread 2-3 days). Output: triple-barrier labels available.

**Q1.4 main dispatch (parallel where independent, sequential where dependent; ~1-2 weeks):**

6. **H-1 K54 v3 modeller agent (master)** — Composite C1 = K-1 + K-4 + K-5 + K-6 + K-7 + K-8 + K-9 + K-10 + K-11 + K-12 + K-13 + K-14 + K-15 + B-1 + D-11. Single Opus-4.7-max-effort agent with sub-tasks (feature-engineering / pooling / meta-label / specialist). Wallclock 4-6 hours.
7. **H-7 sticky-HDP-HMM regime classifier agent (parallel)** — P-8 + Kirby null-test; 2-3 weeks. Output: regime probability vector for K54 v3 input feature.
8. **H-8 NAS_US30 dealer-gamma + JPY/GBP/dollar-pair specialist agent (parallel)** — Composite C4; 4-6 weeks. Output: per-cohort specialists.
9. **H-2 Component 3C Vol-Conditioning Overlay agent (parallel)** — Composite C2 = V-1..V-6 + V-9 + B-2; rule-based v1 in 2-3 weeks.
10. **H-5 Risk-policy bundle agent (parallel)** — Composite C3 = R-1 + R-2 + R-5 + R-6 + R-7 + V-8 + R-9 + B-3; 2-3 weeks.

**Q1.4 dependency graph:**

- H-6 + H-30 + C10 are pre-requisites for ALL downstream hypotheses (gate methodology + data quality).
- H-7 feeds H-1 (regime feature).
- H-1 feeds H-2 (meta-label probability is sigma-multiplier input).
- H-1 feeds H-5 (meta-label sizing × RCK risk allocation).
- H-8 specialist drops INTO H-1 routing layer.
- H-3 (volume-bar sampling) is research-track parallel; can run after H-1 ships.
- H-9 / H-10 / H-12-H-30 are Tier-2; sequence in Q2.

### Q1.4 wallclock estimate

- **Pre-week sprint:** 1 week (5-7 parallel 1-day agents).
- **Main Q1.4 dispatch:** 1-2 weeks for H-1 (the headline ship); 2-6 weeks for H-2/H-5/H-7/H-8 supporting tracks (parallel).
- **Total to first Q1.4 deliverable (H-1 K54 v3 ship):** **2-3 weeks**.
- **Total to full Q1.4 close (all top-10):** **6-8 weeks**.

### Q1.4 PASS / FAIL implications

**If H-1 PASSES all 7 gates (a-g):** ship K54 v3 + meta-label head + NAS_US30 specialist as the production primary-direction layer (Component 3D); LLM (Component 3A) becomes advisory; K55 ML-vs-AI shadow harness initialized.

**If H-1 FAILS gate (c) cross-period:** the most-likely failure mode. Reframe per `Q1_3_POSTMORTEM_SYNTHESIS.md` Alternative B — close Q1 with K54 reframed as "shadow-harness candidate, not Q1 deliverable". Move to Q2 sequence-models (H-25 DLinear baseline) + K55 shadow harness.

**If H-1 FAILS gate (a) CPCV AUC ≥ 0.55 but PASSES (b) lift + (c) cross-period:** the catalog has signal but the K54 v3 architecture under-extracts it. Re-spec with H-11 signature features + H-19 multi-level OFI as an additive feature push.

**If H-2 vol-conditioning overlay PASSES standalone (independent of H-1):** ship vol-conditioning regardless of H-1 outcome; this becomes the "Q1.4 minimum-viable deliverable" even if K54 v3 fails.

**If H-5 risk-policy bundle PASSES Monte-Carlo P(pass FN) ≥ S79 baseline:** ship as next-gen S79 replacement; bundles with (or replaces) S79 sharpe_weighted.

**Probability of Q1.4 PASS estimate (per `Q1_3_POSTMORTEM_SYNTHESIS.md` §3.1 calibration):** 50-65% (vs Q1.3's ~40-55% before the 2022-2023 backfill). The 7-of-7 cross-period feasibility raises probability materially. Strongest dependency: gate (c) cross-period + gate (e) realized-R lift.

---

## Section 9 — Strategic reframe

### Group F's headline reframe

Per Group F §6 + §7: **edge decay is a property of publication-and-replication, NOT mechanism failure.** GTOS at $100k AUM is **below the capacity-decay band** (Naik-Ramadorai-Stromqvist 2007 binds at $250M+); structurally redemption-immune (Stein 2005). The strategic optimization target shifts from edge-PRESERVATION to **edge-DISCOVERY-RATE**.

### Implications for the 4-quarter program shape

**Original framing (pre-Phase-2 syntheses):**
- Q1 = K54 v2 ML modelling (FAILED CPCV-honest).
- Q2 = sequence models (LSTM/Transformer).
- Q3 = K55 shadow harness + ML-vs-AI crossover.
- Q4 = K55 production gate + sovereignty doctrine.
- Implicit narrative: "build K54 to replace AI primary_analyzer" → driven by static-edge optimization.

**Phase-2-synthesis-informed reframe:**
- **Q1.4 = K54 v3 (Hybrid Arch A + meta-label + NAS_US30 specialist) + Vol-conditioning Overlay + Risk-Policy bundle.** Three ship-track parallel; 2-8 weeks. Optimize for FIRST production deployment of the meta-labeling pattern (Group F Rank 1).
- **Q2 = (a) DLinear + foundation-model baseline gate (Group F §4); (b) sticky-HDP-HMM regime classifier + Kirby null-test; (c) microstructure track reopened (volume-bars + Stoikov + Osler); (d) Asset-class specialist bundle for FX-3 cohorts.** Decay-defensive feature catalog expansion — NEW EDGES, not preserve OB-zone.
- **Q3 = K55 ML-vs-AI shadow harness + uncorrelated-edge aggregation (Renaissance-Medallion-style per Group F §6).** Group F §6 #2: "Aggregate small uncorrelated edges, don't rely on one large edge." K55 measures crossover; Q3 shifts the program from monolithic-K54 to portfolio-of-models.
- **Q4 = K55 production gate (only after shadow correlation ≥1.2× AI per Q4 spec) + sovereignty doctrine on partial fleet (per `Q1_3_POSTMORTEM_SYNTHESIS.md` §4.2 end-state).** Most-likely end-state: **ML primary on NAS_US30; ML advisory ensemble across the rest of the fleet.** NOT pure AI replacement.

### Operational shifts implied

1. **Drop edge-preservation-first thinking.** Stop trying to "fix" the OB-zone advantage decay (R1 reframe). Treat F11 measurement as inside-the-McLean-Pontiff-distribution baseline.

2. **Aggressively pursue uncorrelated edges.** Group F §6 #2: K54 v3 (H-1) should pursue features WEAKLY-CORRELATED with the OB-precision feature. F11 + F2 already identified regime-side conditioning as one such axis (H-1 + H-7). Continue identifying axes — microstructure (H-3 + H-4), dealer-gamma (H-8 + H-14), asset-class macro (H-13 + H-20), counterparty stress (H-15 + H-26).

3. **Continuous edge-evolution as the moat.** Lo's AMH + Bollen 2024: edge-discovery rate must exceed edge-decay rate. Phase 2 priority order should bias toward NEW EDGE DISCOVERY (regime-aware ML, microstructure, side-aware sizing, asset-class specialists) over EXISTING EDGE OPTIMIZATION (better OB detection thresholds).

4. **Buffett's Alpha decomposition as the institutional-credibility template.** Each K54 v3 prediction comes with feature-importance attribution. CEO can read the rationale; rationale is replicable; edge is institutional-grade.

5. **Methodology discipline as the program's true alpha.** H-6 + Group A Section 4 + `audit/statistical_reevaluation.md` central role. The methodology critic genuinely caught a 2× false PASS on K54 v2; without it, GTOS would be celebrating a fragile model. Methodology-discipline is the single discipline that compounds across all hypotheses.

### The single most-important new framing

**Optimize for edge-DISCOVERY-rate, not edge-PRESERVATION.** GTOS is below capacity-decay; redemption-immune; with subscription-bounded research budget. The constraints favor multi-edge aggregation (Renaissance Medallion model) over single-edge optimization (Long-Term Capital Management model). The 4-quarter program shape should reflect this — Q1.4 is the FIRST commit to the meta-labeling pattern that lets multi-edge aggregation work; Q2-Q4 are the portfolio-of-edges build-out.

### What this implies for the CEO's decay-velocity concern

Decay is real but survivable IF the program ships new edges faster than existing ones decay. McLean-Pontiff baseline ~5%/year decay (Group E F-1). At GTOS's measurement frequency (rolling-50 + monthly S1), this is detectable. Group F §6 #4: "Continuous edge-evolution is the real moat." The real risk is NOT that any individual edge decays (it will), but that the discovery rate stalls. Q1.4-Q2 priorities (H-1 + H-2 + H-5 + H-7 + H-8 + H-3 + H-4) are designed precisely to keep discovery > decay.

---

*End of HYPOTHESIS_BACKLOG.md. Phase 3 hypothesis generation complete. UTF-8. No fabrication. All 30 hypotheses cite ≥3 evidence sources; all reference MASTER_BACKLOG.md IDs throughout. Cross-references: 6 Phase-2 syntheses + 5 audits + MASTER_BACKLOG.md + 30+ memories.*

---

## Phase 4 B-8 Quick-Win Bundle results (post-2026-04-29 verdict updates)

The following edits to §8 spec come from the B-8 Quick-Win Bundle dispatches that closed 2026-04-29. Original §8 is preserved above for audit trail; this section overrides specific scope/priority items based on B-8 dispatch outcomes.

### Q1.4 priority lock (NA8 verdict): H-1 K54 v3 ships first

**NA8 Babu-Hoffman-Levine 2020 decomposition** on H1→H2 XAUUSD LONG cohort delivered: move-magnitude **3.0%** (CI [-6.9%, +14.8%]); signal-translation **71.4%** dominates. Vol-managed (Barroso-Santa-Clara 2015) recovery estimate -1.0% (point) — NEGATIVE because H2 vol_rank 0.67 < H1 vol_rank 0.77 (Barroso multiplier amplifies losing trades in below-median vol).

**Verdict:** **H-1 K54 v3 master bundle ships first** in Q1.4. **H-2 Component 3C Vol-Conditioning Overlay defers to Phase 5** as a multiplicative sizing-overlay-on-K54 follow-on.

**FA-2 caveat:** A6 canonical cohort ends 2026-04-10 (FA-2 fix `fa35cc0` shipped 2026-04-20). Pooled-H2 measurement is effectively pre-FA-2 only (n=32 pre / 0 post). Signal-translation 71% share will compress when post-FA-2 cohort reaches n≥20 (~3-4 weeks). Move-magnitude 3% is FA-2-independent → H-1-first verdict robust.

See: `research/ml_program/experiments/na8_babu_decomposition.md` + memory `project_na8_babu_decomposition_2026-04-29`.

### H-1 master bundle scope revisions (B-8 dispatch outcomes)

| Element | Original §8 spec | Post-B-8 status |
|---|---|---|
| K-4 Stoikov micro-price | INCLUDED in C1 / B-1 / H-1 | **DROPPED** — KILLED 2026-04-29. MT5 retail tick has `volume=0` + `last=0` on 100% rows. Reference impl preserved at `research/ml_program/experiments/k4_stoikov_micro_price.py` (paper-faithful, 12/12 unit tests pass) for re-evaluation if paid LOB feed sourced. See `KILLED_HYPOTHESES.md` K-4/P-4 entry + memory `project_mt5_retail_tick_lob_gap_2026-04-29`. |
| K-1 volume-bar resampling | INCLUDED | **REPLACED with K-1' tick-count-time bars** (Glattfelder-Dupuis-Olsen 2011) — same substrate gap. ~200-tick buckets per instrument; no volume needed. |
| K-2 / K-3 dollar/imbalance bars | NOT in H-1 (was Section X reopened) | DEFERRED in master backlog — same substrate gap. |
| K-5..K-15 + NAS_US30 specialist | INCLUDED | UNCHANGED — all in H-1 modeler dispatch (2026-04-29). |
| C-1 `is_second_half_of_kz` binary feature | C8 candidate | **NOT ADDED** — KILLED 2026-04-29 by C-1 dispatch. Aggregate Δ=+0.0605R passes magnitude but bootstrap p=0.42 / DSR p=1.0. Two follow-ups deferred to Phase 2: C-1b NY-only at M1 precision; C-1c high-RV-decile-conditioned (cleaner stress proxy than time-of-session). |

### Q1.4 gate (b) anchor revision (DSR sweep verdict)

**Original §8 gate (b):** "Lift over canonical K54 v1 ≥ +0.04 with deflated-Sharpe-corrected combined p < 0.01 AND DSR + effective-N + B=1000 null-p ≥ 0.99 + PBO < 0.40."

**Revised:** Same specs; **anchor changed from K54 v1 published 0.571 to CPCV-honest K54 v1 = 0.5286** (per `audit/canonical_v1_rerun.md`). The DSR sweep showed 0.571 fails DSR at p=0.965 — it was a single-fluky-test-slice number, not a robust baseline. CPCV-honest 0.5286 is the proper anchor for paired comparison.

See: `research/ml_program/audit/dsr_retroactive_sweep.md` + memory `project_dsr_retroactive_sweep_2026-04-29`.

### Q2 sequence-model phase shelved (Q-1 DLinear NO-GO)

**Q-1 DLinear** (Zeng et al. 2023 AAAI Oral) returned: CPCV mean AUC 0.5049, Δ vs K54 v1 anchor -0.0237, DSR p=1.0, PBO 0.795, cross-period 0.499 (random). All gates fail decisively.

**Verdict:** **Q-2 Time-LLM, Q-3 Chronos, Q-4 iTransformer, Q-5 PatchTST, Q-6 TCN, Q-7 LSTM, Q-8/Q-9 SHELVED** until cohort expansion to n ≥ 5,000 with regime-balanced labels. K54 v3 (H-1) is the entire Q1.4 ML primary path.

**Q2 calendar pivots** from sequence-models-and-cohort-expansion to:
- (a) Feature-engineering for K54 v4+ (post-Q1.4 increment).
- (b) Sticky-HDP-HMM regime classifier (H-7) with Kirby null-test.
- (c) Asset-class specialists (H-8 — JPY-pair / GBP-pair / dollar-pair / NAS_US30 dealer-gamma).
- (d) Decay observability infrastructure (H-9 self-normalized CUSUM + BOCPD-AR-score-driven).
- (e) Microstructure track at proper clock (K-1' tick-count-time bars; Osler stop-cluster K-7).

See: `research/ml_program/experiments/q1_dlinear_baseline.md` + memory `project_q1_dlinear_q2_nogo_2026-04-29`.

### Methodology gate hardened (DSR sweep)

Forward methodology gate for every Q1.4+ lift claim: `dsr_p < 0.01 AND PBO < 0.4 AND effective_N ≥ 3`. Audit trail row in `research/ml_program/audit/dsr_diagnostics.json` per claim. CLAUDE.md "Validated Numbers" table updated 2026-04-29 to reflect post-DSR survival (only J46-J49 + S79 survive at N=200). OB-zone mechanism survives separately at cross-period z=10.5; "+17pp" relative claim was overfit.

See: `research/ml_program/audit/dsr_retroactive_sweep.md` Section 7.

---

*Post-B-8 §8 update complete. Q1.4 dispatch (H-1 K54 v3 modeler, agent a7bffb43f7b4bb01b) running 2026-04-29. Spec lock formalized in `PRE_REGISTERED_HYPOTHESES.md` Q1.4 entry.*
