# Killed Hypotheses — Graveyard

Why-it-failed memos for hypotheses that reached terminal `FAIL` status (per `PRE_REGISTERED_HYPOTHESES.md`).

**This graveyard is more valuable than survivor write-ups.** It is the accumulated organizational knowledge of what doesn't work in this market.

Each entry has:

- The pre-registered hypothesis (verbatim).
- The actual result (numbers, dates, what was tested).
- Diagnosis: WHY did it fail? (overfitting, regime change, feature staleness, methodology bug, etc.)
- What we'd try differently next time.

Entries that are `INVALIDATED_PRE_TEST` (couldn't be tested as written) are NOT in this file — they remain in the registry with audit-trail links instead. This file is for hypotheses that were genuinely tested and the data said no.

---

## Q1.3 — K54 v2 expanded feature catalog (FAIL, 2026-04-28)

**Pre-registered hypothesis (verbatim, from `PRE_REGISTERED_HYPOTHESES.md` Q1.3):** *"An expanded 1,219-feature catalog (vs K54 v1's 17) lifts a global LightGBM (regime-as-feature) AUC by ≥0.04, from K54 v1's baseline of 0.571 to ≥0.61, when validated via combinatorial-purged CV (K=6, N=2; 15 paths) with explicit purge gaps ≥1 week and embargo ≥1 day, on training data from 2024-02-20 → 2026-04-28. AUC measurement is paired (v2 vs v1 on identical CPCV folds), with PBO < 0.5 to confirm non-overfitting. A 14-day prospective holdout window 2026-04-29 → 2026-05-12 serves as a directional-discipline check (sign of lift, calibration retention, no per-instrument sign-flip), NOT as a numeric AUC gate."*

### Actual result (2026-04-28)

| Gate | Threshold | Realized | Verdict |
|---|---|---:|:---:|
| (a) CPCV paired effect-size | mean(AUC_v2-AUC_v1) ≥ 0.04 | +0.0309 | FAIL |
| (a) CPCV paired significance | DeLong combined p < 0.01 | 0.001546 | PASS |
| (b) PBO | < 0.5 | 0.4667 | PASS (borderline) |
| (d) Cross-instrument | ≥3 of 5 groups positive lift | 2 of 4 (only 4 effective groups exist for our 7-symbol set) | FAIL |
| (e) White-noise null (B=1000) | obs ≥ p99 AND p_emp < 0.01 | 0.5429 ≥ 0.5365, p=0.003 | PASS |
| (c) Holdout discipline | DEFERRED | gate (c) opens at end-of-Q1 | DEFERRED |

**Final verdict:** FAIL on (a) effect-size + (d) cross-instrument; PASS on (b) overfitting + (e) signal vs noise.

### Diagnosis

The 1,234-feature catalog (post-Patch-1 prune) DOES carry a non-zero edge over K54 v1's 17 features:

- The lift IS detectable above white-noise (gate e: obs=0.5429 vs null p99=0.5365, p_emp=0.003).
- The lift IS statistically distinguishable from zero (gate a: combined DeLong p=0.001546 < 0.01).

But the lift is too small and too cohort-dependent:

- **Effect-size gap.** The pre-registered ≥0.04 AUC threshold reflects a "decision-grade" bar — what's needed to make K54 v2 a defensible AI-gate replacement in K55. The realized +0.0309 falls below that, even though it's statistically real. A model with a +3pp AUC lift cannot anchor a K55 shadow → live promotion.
- **Cross-instrument inconsistency.** Out of 4 effective-independent groups (XAU+XAG, NAS+US30, GBPJPY, GBPUSD+USDJPY), 2 had POSITIVE lift (XAU+XAG +0.036, NAS+US30 +0.074) and 2 had NEGATIVE lift (GBPJPY -0.016, GBPUSD+USDJPY -0.028). This is the classic "marginal global signal averaging over real per-instrument heterogeneity" pattern. K54 v2 helps for the metals + indices basket but actively hurts on the FX-pair basket.

### Likely root causes

1. **n=528 with 1,234 features is rows-per-feature ≈ 0.43** — well below the 5-10 rule-of-thumb for stable LightGBM training even with strong regularization. The methodology critic flagged this risk explicitly; the fixed-HP best (n_estimators=100, max_depth=5, lr=0.1) is the most-regularized of the 27-combo grid, suggesting the optimizer is correctly throttling to avoid overfit. But the implied effective-feature-count is much smaller than 1,234. Further pruning + per-instrument feature selection could matter.
2. **Cohort imbalance: XAUUSD 164 / FX 138 (combined GBPUSD+USDJPY) / GBPJPY 62 / Indices 113 / XAU+XAG 215** — XAUUSD trends dominate the global model. The XAU+XAG basket helps; FX-pairs hurt because the model picks up XAU-style features as predictive but they don't transfer.
3. **Per-path HP selection bias was real.** The original train_k54_v2.py reported diff_mean=+0.0652 (per-path-best HP); the CPCV-honest fixed-HP variant drops to +0.0309. This 2× shrinkage is exactly what the methodology critic predicted; it confirms the brief's PBO + paired-fixed-HP discipline was necessary.
4. **F11 mechanical OB-retest cohort dominates** (n=406 of 528 = 77%). The 110 unified_csv + 33 trade_index rows that contain AI-gated trades are too few to measurably differentiate K54 v2 from K54 v1's mechanical-feature surrogate (`ob_distance_atr`, `ob_age_candles`, `displacement_quality_score`).

### What we'd try differently in Q1.4

1. **Per-instrument-group LightGBM ensemble (re-test).** Joint-model scout found per-regime drag −0.075pp at n=528. But per-INSTRUMENT (not per-regime) might help: the 4-group cross-instrument result shows 2 strongly positive groups and 2 negative — a per-group model would let the negative-lift groups simply not contribute, instead of pulling down the global average.
2. **Tighter feature selection inside CPCV.** Per the methodology critic recommendation 2: per-fold screening LightGBM → top-50-150 features by gain → retrain final per-regime model on those. This is the "feature importance with bagging" pattern (de Prado AFML §8.5) applied PER FOLD, not on full data (which would leak).
3. **Cross-period replication.** Defer the +0.04 effect-size threshold for "global cohort" and instead test the SAME 1,234 features on a 2024-2025-only training cohort vs 2026-only test cohort. This is the cross-period robustness test the K54 v1 audit specifically called for.
4. **K55 shadow harness becomes secondary.** With marginal lift, the strategic question is no longer "shall we replace AI with ML" — it's "can ML add a small consistent overlay where AI is uncalibrated". Run K55 in shadow with a thr ≥ 0.55 (low-confidence floor), not as a hard gate.

### Code revisions

- Final K54 v2 model + report: `research/ml_program/models/k54_v2/`
- CPCV-honest paired comparison: `cpcv_paired_results.json` (`summary_fixed_hp_recommended`)
- B=1000 null distribution: `null_distribution.json`
- PBO computation: `pbo_results.json`
- Cross-instrument detail: `cross_instrument_results.json`
- Top-30 features: `top_features.json`

### Audit trail

- Methodology critique: `research/ml_program/audit/methodology_critique.md`
- Pre-week-4 synthesis: `research/ml_program/audit/PRE_WEEK4_SYNTHESIS.md`
- K54 v1 commit: `af5d97e`

---

## C-1 / H-15 — Coval-Shumway second-half-of-session OB-retest A/B (FAIL, 2026-04-29)

**Pre-registered hypothesis (verbatim):** *"OB-retest entries in the second half of a kill-zone (split at the kill-zone midpoint per CLAUDE.md kill-zone schedule) achieve realized-R mean ≥ +0.05R higher than first-half entries on the post-2022-2023-backfill cohort (n ≈ 2,326), with stationary block bootstrap p < 0.05 (DSR-corrected for ≈10 stratifications). Sign of the difference must be positive on ≥3 of 4 effective instrument groups (XAU+XAG, NAS+US30, GBPJPY, GBPUSD+USDJPY)."*

### Actual result (2026-04-29)

| Gate | Threshold | Realized | Verdict |
|---|---|---:|:---:|
| (a) Aggregate Δ ≥ +0.05R | ≥ +0.05R | +0.0605R | PASS |
| (b) Aggregate stationary-bootstrap p | < 0.05 | 0.4220 | FAIL |
| (c) DSR-corrected p (Bonferroni proxy, n_trials=10) | < 0.05 | 1.0000 | FAIL |
| (d) Sign-count gate | ≥3 of 4 instrument groups positive | 3 of 4 (XAU/INDEX/USD_FX +; GBPJPY −) | PASS |

**Final verdict:** FAIL — point estimate is in the predicted direction but bootstrap p far above the 0.05 bar; DSR-corrected p saturates at 1.0.

### Diagnosis

The directional signal is present (3 of 4 instrument groups positive; NY KZ Δ = +0.184R p = 0.090 borderline-suggestive; transitional regime Δ = +0.146R) but underpowered:

1. **Statistical power is the binding constraint.** With per-trade R standard deviation ≈ 1.0R and n = 1,185 split (754 first-half, 431 second-half), the implied SE on Δ is ≈ 0.07R. The observed +0.0605R sits at ~0.86 SE — well below the ~1.96 SE needed for p < 0.05. Detecting a ≥+0.05R promotion-grade effect at this n would require the population effect to be ≥+0.10R — which would have been clearly visible if it existed.
2. **Hour granularity (HH:00) coarsens the midpoint split.** Cohort entries are at integer-hour resolution; midpoints at :30/:45 had to be assigned to integer-hour bins; in 4 of 12 (sym × KZ) cells the second-half collapses to a single integer hour. This produces a 754/431 split (much larger first-half) and degrades sub-cell power.
3. **The transmission mechanism may not be time-of-session.** Coval-Shumway 2005's distressed-flow channel is fundamentally *stress*-driven, not *clock*-driven; the time-of-session axis is a noisy proxy. Realized-vol-percentile or intraday DD percentile would be the cleaner stress proxy (deferred to V-1 / H-E16).

### Likely root cause

**Primary:** the effect, if it exists, is too small (bounded above at ~+0.04R based on the failed-to-clear-significance point estimate) to justify a binary feature in K54 v3 at the dispatch's promotion gate. The Coval-Shumway prediction is *qualitatively* validated (sign agrees) but *quantitatively* below decision-grade.

### What we'd try differently next time

1. **C-1b — NY-only at finer precision.** The NY KZ p = 0.090 is borderline. Re-run with M15 / M1 timestamps (rebuild from `live_evaluations/h1_reconstructed/` + Component 2 entry-time stamps) — the integer-hour coarsening biases AGAINST the hypothesis on NY (mid 15:00 puts hour 15 trades into "second half" en bloc rather than splitting them at the actual minute mark).
2. **C-1c / V-1 / H-E16 — high-RV-conditioned variant.** Replace "second-half-of-KZ" with "current-day-realized-vol decile 9-10 vs decile 1-2." Same data, single rolling-RV computation. Coval-Shumway's mechanism is stress-driven; this is the cleaner test.
3. **Continuous "time-since-KZ-open" feature, not binary.** A continuous feature (minutes since KZ open, rolling sum since session start) preserves the within-bin information the binary midpoint discards. Fold into K54 v3 catalog as one of many candidate features (let SHAP gate inclusion).

### Code + reproducibility

- Audit script: `scripts/research/c1_coval_shumway_audit.py`
- Result JSON: `research/ml_program/experiments/c1_coval_shumway_results.json`
- Pre-registered + result writeup: `research/ml_program/experiments/c1_coval_shumway_second_half.md`
- Random seed: 42; B = 1,000 stationary block bootstrap replicates.
- Cohort: 2,380-row deduped combined (1,798-row 2022-2023 backfill + 582-row K54 v1 modeler dataset); within-KZ-window OB-retest filter → n = 1,185.

### Audit trail

- Master backlog item: `research/ml_program/MASTER_BACKLOG.md` C-1.
- Hypothesis backlog item: `research/ml_program/literature/HYPOTHESIS_BACKLOG.md` H-15.
- Literature evidence anchors: Coval-Shumway 2005 (Group D Section 1, Group E F-2 / H-E1 / Section 3); Group B §2.1.

---

## K-4 / P-4 — Stoikov 2018 micro-price feature on MT5 retail tick data (FAIL, 2026-04-29)

**Pre-registered hypothesis (verbatim, from `research/ml_program/experiments/k4_stoikov_micro_price.md` §1):** *"Stoikov micro-price reduces 1-step-ahead RMSE by ≥10% over naive midprice on both NAS100 + US30_cash tick captures. Verdict gate: PASS if reduction ≥10%, FAIL otherwise."*

### Actual result (2026-04-29, on tick captures from 2026-04-27 + 2026-04-28)

| Instrument | n_ticks | best_window | RMSE_naive | RMSE_stoikov | reduction_% | dir_acc_% | verdict |
|---|---:|---:|---:|---:|---:|---:|:---:|
| NAS100 | 1,752,649 | 200 | 0.32634 | 0.33442 | **-2.47%** | 47.19% | FAIL |
| US30_cash | 385,824 | 200 | 0.90839 | 0.91613 | **-0.85%** | 47.12% | FAIL |

**Sign-inverted diagnostic:** -2.47% (NAS100), -0.84% (US30_cash) — sign flip does NOT recover edge.
**M15-aggregated form:** -0.0003% (NAS100, n_bars=169), -0.010% (US30_cash, n_bars=168).

### Diagnosis (the substitution did not transmit)

Stoikov 2018 §2.1's formula `mp = p_bid * V_ask/(V_bid+V_ask) + p_ask * V_bid/(V_bid+V_ask)` requires **bid + ask queue volumes**. MT5 retail-broker spot CFD ticks have `volume = 0` on 100% of NAS100 + US30_cash captures and `last = 0` on 100% (no trade events). The reference impl substituted **rolling tick-flow imbalance from `inferred_aggressor`** as a queue-imbalance proxy. The substitution does not transmit the published mechanism, for three convergent reasons:

1. **`inferred_aggressor` is mechanically derived from mid changes.** Per `src/components/tick_capture.py` `classify_aggressor`, on spot CFDs the aggressor is determined by the tick test on `mid` vs prior `mid` (since `last = 0`). So our flow imbalance is essentially a **rolling momentum signal on mid changes**. At sub-second timescales midprice has Roll-model bid-ask-bounce — recent up-tick predicts a *down*-tick. Our momentum-direction proxy carries the wrong sign in a mean-reverting regime.

2. **Sign-inverted control rules out pure-bid-ask-bounce.** The diagnostic re-ran the benchmark with `mp_inverted = mid - (mp - mid)` and got -2.47% / -0.84% — virtually identical FAILs. So it's not "right magnitude wrong direction" but rather "noise of similar magnitude in either sign". The Stoikov correction `(I - 0.5) * spread` is bounded by half-spread (~$0.88 on NAS100), and per-tick mid jumps are typically larger (1-3 ticks); the correction is dominated by noise.

3. **Per-tick mid jumps dominate signal-to-noise.** NAS100 spread median 1.76 (1-tick = $0.01); US30_cash spread median 2.30 (1-tick = $0.05). Even a "perfectly informed" Stoikov correction at half-spread would be smaller than typical t→t+1 noise.

This refines the prior `project_microstructure_archived_2026-04-27` E24/E26 NULL_VERDICT: it's NOT just M15 aggregation that destroys the signal — at the proper microstructure timescale (per-tick) the volume-proxy substitution itself destroys it. A correctly-tested Stoikov micro-price on MT5 retail data **requires LOB depth** (Databento or similar).

### What we'd try differently

1. **Don't bother re-doing the flow-proxy variant.** The post-mortem is conclusive on the substitution path.
2. **Pivot to H-A (volume/dollar bar resampling)** in `group_b_microstructure.md` §6.2. The literature's strongest hypothesis is sampling-clock change, not feature substitution; the H-A path doesn't depend on LOB depth.
3. **Re-run with real LOB depth IF Databento or similar is sourced** for MT5 instruments. The reference impl's `stoikov_canonical_micro_price` is paper-faithful and ready (passes 5 synthetic + 1 published Stoikov 2018 §2.1 AAPL example unit tests).
4. **Consider as a non-load-bearing K54 v3 interaction feature** (not a primary): TEST its SHAP contribution after main features lock; retain only if interaction-AUC lift ≥0.005 over baseline. Default: drop.

### Code + artifacts

- Reference impl: `research/ml_program/experiments/k4_stoikov_micro_price.py`
- Design + verdict: `research/ml_program/experiments/k4_stoikov_micro_price.md`
- Machine-readable benchmark: `research/ml_program/experiments/k4_benchmark_results.json`
- Unit tests: 12/12 PASS (5 synthetic + 1 Stoikov 2018 AAPL example + 4 edge cases + 3 flow-proxy synthetic-tick checks)

### Audit trail

- Master backlog: `research/ml_program/MASTER_BACKLOG.md` K-4, P-4, U-3, B-8
- Hypothesis: `research/ml_program/literature/HYPOTHESIS_BACKLOG.md` H-4
- Literature synthesis: `research/ml_program/literature/synthesis/group_b_microstructure.md` §3 H2 + §6.1
- Paper: Stoikov, S. (2018). "The Micro-Price: A High Frequency Estimator of Future Prices." *Journal of Financial Markets*, 39, 1-19.

---

## Q1.4 — K54 v3 master bundle (FAIL, 2026-04-29)

**Pre-registered hypothesis (verbatim, from `PRE_REGISTERED_HYPOTHESES.md` Q1.4):** *"A K54 v3 model architected as (i) global LightGBM with per-fold top-100 feature screening, (ii) Lopez-de-Prado meta-labeling secondary classifier on triple-barrier outcome labels feeding sizing in {0, 0.5, 1.0} × `risk_per_trade_pct`, (iii) Kyle-Obizhaeva W-unit pooled training across 7 instruments with one-hot instrument-id, and (iv) NAS_US30 specialist routing layer activated when `symbol ∈ {NAS100, US30_cash}` will achieve, on the post-2022-2023-backfill cohort (n ≈ 2,326), all gates (a-g) below."*

### Actual result (2026-04-29)

| Gate | Threshold | Realized | Verdict |
|---|---|---:|:---:|
| (a) | CPCV-honest mean AUC ≥ 0.55 | 0.5770 | PASS |
| (b) | Lift ≥ 0.04 + DSR-p < 0.01 + PBO < 0.4 + null p ≥ 0.99 | lift=+0.0484, DSR-p=0.321, PBO=0.20, null p=1.0 | **FAIL on DSR-p** |
| (c.i) | Train 2022-2023 → Test 2024-2026 (v1-schema only) | lift +0.0481, 4/4 groups positive | PASS (v1-schema sanity) |
| (c.ii) | Train <2026-01-01 → Test 2026-01-01+ (v3 features) | lift -0.0225, 1/4 groups positive | FAIL |
| (d) | All 4 groups AUC ≥ 0.50 + NAS specialist delta ≥ +0.05 | 2/4 groups (NAS+GBPJPY <0.50); specialist +0.103 | FAIL |
| (e) | Realized-R lift ≥ +0.05R, bootstrap p < 0.01 | -0.108R, p=0.999 | FAIL |
| (f) | ≥30 stable features in top-50 across ≥80% paths, Jaccard ≥ 0.6 | 2 stable features, Jaccard 0.169 | FAIL |
| (g) | Christoffersen interval-coverage on holdout 2026-04-29→2026-05-12 | DEFERRED to 2026-05-13+ | DEFERRED |

**Final verdict:** 1/6 testable gates PASS (a only); 5/6 FAIL. **FAIL.**

### Diagnosis

The K54 v3 architecture is empirically **a regression from Architecture A** (the Q1.3 audit's strongest result) once the W-unit pooling element is included. Three convergent failure modes:

1. **W-unit dollar-volume pooling catastrophically underperforms.** Pre-registered spec used Kyle-Obizhaeva `W = dollar_volume × realized_vol × time` per row. The cross-instrument dollar-volume scale spans 5 orders of magnitude (GBPUSD ~100,000 vs NAS100 ~1). Even with [0.1, 10] clipping, the screening pass becomes dominated by FX cohorts, warping which features get selected. Diagnostic ablation (`diagnostic_w_unit_ablation.json`):
   - K54 v3 features + dollar-volume W-unit ON: AUC **0.5076**
   - K54 v3 features + W-unit OFF: AUC **0.5640**
   - Arch A reproduction (Q1.3) AUC **0.5605**
   The dispatch was re-run with a balanced intra-instrument-volatility-rank W-unit (clip [0.5, 2.0]) which recovered AUC to 0.5770. **Even the corrected W-unit form contributes only +0.0035 AUC over Arch A** (0.5605 → 0.5640 in ablation), well within noise. The K-7..K-10 closed-form additions (Osler stop-cluster proxy, power-law OB-age, regime-aligned interactions, round-number direction) do NOT lift the architecture meaningfully — they add 6 features to a 1,234-feature catalog whose underlying signal ceiling is already determined by the n=528 cohort size.

2. **DSR with N=200 deflates the lift below significance, same pattern as Q1.3 K54 v2.** Paired-trade SR = 1.27, sigma_SR = 0.36; expected max-SR under null at N=200 trial budget is `0.36 × 3.08 = 1.11`. Observed SR is 0.16 above the noise ceiling — DSR-p = 0.32. The lift IS real (B=1000 null p_emp = 0.000 — no random shuffle exceeded the observed AUC), but the cumulative GTOS Phase 1 trial budget puts the deflated p well above 0.01. This is the same statistical fate that K54 v2 met (B-8 DSR audit row M-2: dsr_p = 0.965); K54 v3 is closer (0.32) but does not survive.

3. **Realized-R lift is NEGATIVE on the cohort.** The K54 v3 thresholding decision (trade when p > 0.5) actively REMOVES winning trades on average — observed delta(realized R | v3 trades) - (uniform always trades) = **-0.108R per trade** (95% CI [-0.18, -0.04]). This is not an AUC-vs-realized-R disconnect (memory `feedback_walk_level_evidence_not_predictive`) — it is the model picking the wrong edge of its score distribution. Even a reasonably-calibrated AUC 0.577 model produces this artifact when the cohort's win-rate (0.580) is close to the threshold's positive-density.

4. **Per-instrument-group floor fails on NAS_US30 + GBPJPY.** Both groups have AUC < 0.50 from the global K54 v3 model. The NAS_US30 specialist (Architecture B at AUC 0.601, delta +0.103 over global) is the program's strongest single finding and reproduces Q1.3's signal — but it does NOT rescue the global model's per-cohort floor.

5. **Feature stability is statistically incompatible with the gate.** Mean pairwise Jaccard 0.169, only 2 features in top-50 across ≥80% of CPCV paths. Same overfit signature as Q1.3 K54 v2 (Jaccard 0.072). At 528/100 = 5.28 effective rows per feature post-screening, the model is structurally above the safe zone (per de Prado AFML §8.5), but per-fold screening still finds different "best 100 features" each fold — meaning the screening identifies a different model on every fold. The architecture cannot satisfy the f-gate at this n.

### Likely root causes

1. **Cohort scale ceiling.** n=528 with 1,234 features = 0.43 rows-per-feature pre-screening, 5.28 post-screening. Even Architecture A's PBO 0.20 is achieved by extreme regularization at this scale; the additional architectural complexity in K54 v3 (meta-label head + W-unit pooling + per-cohort routing) demands more rows than this cohort provides. The 2022-2023 backfill (n=1,798) cannot be joined to the v2 catalog because feature engineering for those 1,798 rows was not performed; only v1-schema cross-period verification is feasible.

2. **The DSR trial-budget penalty is decisive.** With N=200 cumulative GTOS Phase 1 trial population (per B-8 audit), the noise ceiling on paired SR is 1.11. Any architecture whose per-trial paired SR < 1.5 cannot pass DSR-p < 0.01. K54 v3's SR_paired = 1.27 is below this — the architecture would need ~+0.07 paired AUC lift (vs the realized +0.0484) to cross the DSR threshold. **No K54 family architecture has produced a +0.07+ paired AUC lift at this n on this catalog.**

3. **The K-7..K-10 closed-form additions are below noise.** Per ablation, the 6 new features add at most +0.0035 AUC over Arch A — negligible. Group F §3 / Group B §6.1 / Bhattacharya 2012 / Zhang 2024 predictions of +0.02-0.04 AUC for these features were under different cohort assumptions. At n=528 with 1,234 feature-screening competition, the 6 new features simply do not survive the per-fold screening selection.

4. **Architecture B (NAS_US30 specialist) is the only deployable component.** Specialist delta +0.103 over global on its 113-row cohort. PBO from Q1.3 was 0.53 (above threshold 0.4) but per-cohort lift is robust. **Recommendation: ship the NAS_US30 specialist as a K55-shadow signal candidate; do NOT ship the K54 v3 global model.**

### What we'd try differently in Q1.5 (or close Q1)

**Reframe K54 v3 to K55-shadow signal candidate (per Q1.3 KILLED memo §"What we'd try differently" item #4):**

1. **Shelve the global K54 v3 architecture for now.** Focus K55-shadow on the **NAS_US30 specialist** + the **v1-schema cross-period model** (which passed gate c.i with +0.0481 lift, 4/4 groups positive cross-period). These are the only two components with statistically-defensible lift.

2. **Cohort-expansion before further architectural work.** Compute the full v2 catalog (1,234 features) on the 2022-2023 backfill cohort (1,798 rows). This would 4× the rows-per-feature ratio (0.43 → 1.88 pre-screening, 5.28 → 23.3 post-screening), and would make all gates a-d feasibly testable on a true cross-period split. **This is the audit-recommended path** (per `audit/Q1_3_POSTMORTEM_SYNTHESIS.md` §3.2). 4-6 weeks of data engineering before Q1.5 would re-spec.

3. **Drop the dollar-volume Kyle-Obizhaeva pooling form.** Use balanced intra-instrument-vol-rank weights (this dispatch's diagnostic-corrected form) OR pure equal weighting. The diagnostic finding is now in `diagnostic_w_unit_ablation.json` for forward methodology.

4. **Drop the meta-labeling head as a primary architectural component.** It is testable but at n=528 the secondary classifier is operating on ~250 primary-positive rows, where its discriminating power is statistically weak. Re-introduce when the cohort > 5,000.

5. **Forward methodology: every primary lift claim must clear DSR-p < 0.01 with N=200 trial budget**, NOT just Stouffer / DeLong p < 0.01. The DSR penalty is the binding constraint at this trial budget; Stouffer/DeLong are systematically optimistic.

### Code revisions

- Final K54 v3 model + report: `research/ml_program/models/k54_v3/`
- Per-path detail: `cpcv_paired_results.json` (15-path AUC + DeLong p)
- DSR per-gate: `dsr_per_gate.json` + appended row in `audit/dsr_diagnostics.json`
- Cross-period: `cross_period_results.json` (gate c.i PASS, c.ii FAIL)
- Specialist (Architecture B replication): `specialist_results.json` (delta +0.103, n=113)
- Realized-R: `realized_r_holdout.json`
- Feature stability: `feature_stability.json`
- Calibration: `conformal_calibration.json` (gate g DEFERRED to 2026-05-13+)
- Top features: `top_features.json` (per-path top-100 + aggregated top-200)
- Diagnostic W-unit ablation: `diagnostic_w_unit_ablation.json` (variant comparison showing dollar-volume W-unit was the dominant cause of the un-corrected pipeline's failure)

### Audit trail

- Pre-registered hypothesis: `PRE_REGISTERED_HYPOTHESES.md` Q1.4
- Architectural spec: `research/ml_program/literature/HYPOTHESIS_BACKLOG.md` §8 H-1
- Q1.3 post-mortem (foundation): `research/ml_program/audit/Q1_3_POSTMORTEM_SYNTHESIS.md`
- Architecture A/B audit: `research/ml_program/audit/architecture_ab.md`
- Canonical K54 v1 baseline: `research/ml_program/audit/canonical_v1_rerun.md`
- DSR retroactive sweep (gate b methodology anchor): `research/ml_program/audit/dsr_retroactive_sweep.md`
- 2022-2023 backfill: `research/ml_program/audit/data_backfill_2022_2023.md`
- Statistical re-evaluation (CPCV-honest SE methodology): `research/ml_program/audit/statistical_reevaluation.md`
- NA8 Babu decomposition (Q1.4 priority verdict): `research/ml_program/experiments/na8_babu_decomposition.md`
- K-4 Stoikov KILLED memo (above)

### Top-1 surprise

**The Kyle-Obizhaeva W-unit pooling element of the master bundle was empirically harmful in its raw dollar-volume form** (AUC dropped from Arch A's 0.561 to 0.508). The literature anchor (Group B §2.4: Sirignano-Cont 2019 universal LSTM cross-stock generalization + Kyle-Obizhaeva 2016 W-unit invariance) operates on equity LOB depth, not retail FX/CFD with multi-decade dollar-volume scale ranges. This is a **scope-of-applicability** failure of the literature transplant — Kyle-Obizhaeva's W-unit invariance assumes you can MEASURE per-trade dollar volume from genuine LOB data, which retail MT5 brokers do not provide (volume=0 ceiling). The diagnostic-corrected balanced form (intra-instrument vol-rank, [0.5, 2.0] clip) recovers most of the architecture's potential but still adds essentially nothing over Arch A. **The pooling element should be dropped entirely from K54 vN+ scope until LOB depth is sourced** — same operational gap that killed K-4 Stoikov.

### Failure protocol decision

Per CLAUDE.md "Failure protocol: pass → ship; fail → KILLED memo + re-spec or close":

- **Recommendation:** CLOSE Q1 with K54 v3 reframed as **K55-shadow signal candidate** (per Q1.3 post-mortem §3.3 Alternative B). Open Q1.5 only after 2022-2023 v2-catalog feature engineering (4-6 weeks data work) — re-spec K54 v4 against a 2,326-row v2-feature cohort + 23-rows-per-feature ratio.
- **Ship in K55 shadow:** the **NAS_US30 specialist** (`k54_v3_nas_us30_specialist.lgb`, AUC 0.601 on its 113-row cohort) — strongest single finding of the program, replicates Q1.3 Arch B independently.
- **Forward methodology gate:** every K54-family lift claim must report DSR-corrected p alongside raw / Stouffer / DeLong p, and must use the discipline gate `dsr_p < 0.01 AND PBO < 0.4 AND null_p ≥ 0.99 AND lift ≥ 0.04` per B-8 audit's gate proposal.

---

*Append new entries below this line as Q1+ hypotheses close.*
