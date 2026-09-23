# Ambiguities + Open Questions — K54 v2 Q1.3 Verdict Interrogation

**Author:** ML Program Orchestrator (post-Q1.3 deep read, 2026-04-28)
**Scope:** Personal interrogation of the Q1.3 deliverables. Goal: surface every question / inconsistency / counterfactual the verdict raises so the Q1.4 / Q1-close decision is fully informed.

**Inputs read:** `report.md`, `meta.json`, `cpcv_paired_results.json` (header), `pbo_results.json`, `null_distribution.json`, `cross_instrument_results.json`, `top_features.json`, `feature_prune_list.json`, plus all 5 audits + scout report.

---

## Critical findings the Q1.3 summary undersold

These are findings that change the verdict's meaning, not just its magnitude. I want to flag them up front because they drive the Q1.4 design.

### CF-1. The 95% CI on the paired diff INCLUDES ZERO

`cpcv_paired_results.json` (and report §6) shows:

- mean(diff) = **+0.0309**
- std(diff across 15 paths) = **0.0794**
- 95% CI = **[−0.0093, +0.0711]**

The interval CROSSES ZERO. So at the 95% confidence level, the lift is **not statistically distinguishable from no lift at all** — even before applying any independence correction. The Stouffer combined p=0.0015 is doing a lot of work here that the per-path SE doesn't support.

### CF-2. Stouffer's combined p assumes independent paths; CPCV paths share data

K=6, N=2 → 15 paths. Each path uses 4 train groups + 2 test groups. Any two paths share at least 2-4 train groups in common (highly correlated). Stouffer's combined p of 0.0015 assumes independence; the methodology critic explicitly warned this is optimistic.

**Realistic SE under CPCV-honest accounting:** 0.0794 / sqrt(3-4) ≈ 0.040-0.046 (vs the naive 0.0794/sqrt(15) = 0.0205). With SE=0.04, t-stat = 0.0309/0.04 = **0.77, p ≈ 0.44** — NOT significant.

**The +0.0309 lift may not even be statistically distinct from zero under proper CPCV-corrected SE.** This is a stronger negative finding than "fails the 0.04 threshold." The current Stouffer p=0.0015 is an artifact of treating dependent paths as independent.

### CF-3. K54 v1's published AUC 0.571 does NOT reproduce under CPCV

`report.md` reports K54 v1 paired baseline at **CPCV mean AUC 0.5120**. K54 v1's published number was **0.571** on a single time-walk-forward test slice (n=94, 2026-04 only).

Under proper CPCV, K54 v1 is at 0.512 — **0.06 lower than published, just barely above random**. The published 0.571 was on the most recent slice (2026-04), which captured FA-2-fix-era patterns; the rest of the timeline 2024-04 → 2026-03 doesn't generalize that well.

**Implication:** the +0.04 lift target was set against an inflated baseline. The "real" K54 v1 baseline at CPCV is 0.512, so K54 v2's effective lift over a robust K54 v1 is +0.031. **K54 v2 isn't underperforming a strong baseline; both K54 v1 and K54 v2 are weak under CPCV.**

### CF-4. K54 v1 underperforms RANDOM (AUC < 0.5) on 3 of 4 instrument groups

`cross_instrument_results.json`:

- GBPJPY v1 = 0.4590 (below random)
- NAS_US30 v1 = 0.4323 (below random by 0.07)
- XAU_XAG v1 = 0.4780 (below random)
- GBPUSD_USDJPY v1 = 0.5436 (only positive-lift cohort for v1)

**K54 v1 is actively counter-predictive on 3 of 4 cohorts.** The +0.0740 v2-vs-v1 lift on NAS_US30 isn't because v2 has positive signal (v2 = 0.5063, near random) — it's because v2 is "less wrong" than v1's anti-prediction. The narrative "v2 lifts over v1" hides "v1 is broken; v2 is mediocre."

### CF-5. EVERY per-group AUC_v2 is below 0.55

| Group | n | AUC_v2 | Distance above random |
|---|---:|---:|---:|
| GBPJPY | 62 | 0.4433 | **−0.057 (below random)** |
| GBPUSD_USDJPY | 138 | 0.5156 | +0.016 |
| NAS_US30 | 113 | 0.5063 | +0.006 |
| XAU_XAG | 215 | 0.5145 | +0.015 |

The model is not strong on any group. The 0.5429 aggregate AUC is mostly cohort-mix averaging. **No instrument group has a model worth shipping in production at the per-group level.**

### CF-6. Gate (d) threshold mismatch — "5 effective groups" but only 4 exist

The methodology critic specced gate (d) as "≥3 of 5 effective-independent groups." Q1.3 inherited this verbatim. But the production-fleet 7 instruments map exhaustively into 4 groups (XAU+XAG, NAS+US30, GBPJPY, GBPUSD+USDJPY) with **no residual cohort**. The "5th group" doesn't exist.

**The gate threshold was statistically impossible from inception.** Even with all 4 effective groups passing, we'd have 4 of "5" (which doesn't exist) — the critic's spec contained an error in group-counting.

If Q1.3 had been "≥2 of 4 effective groups" (50% threshold, matching the spirit), the result (2 of 4 PASS) would have been **borderline PASS**. If "≥3 of 4" (75%, stricter than 60%), it would have FAILED — but for a different reason than the spec implies.

This isn't a re-spec to bend the rule; it's noting the original gate was wrong.

### CF-7. Single-path fragility — path 9 carries 30% of the mean lift

Looking at the per-path table (report §6):

- 10 of 15 paths have positive diff; 5 negative.
- Path 9: AUC_v2 = 0.6465, AUC_v1 = 0.5010, diff = **+0.1454**, DeLong p=0.0092 (the ONLY path with p<0.01).
- Without path 9: mean diff = (15×0.0309 − 0.1454) / 14 = **+0.0227**.

**Path 9 contributes 30% of the mean lift. The result is fragile under leave-one-fold-out.** What's special about path 9's test groups? Without reading the 454KB cpcv_paired_results.json, I don't know — but if path 9's test fold was XAU-heavy, the lift may just be the XAU+XAG group's signal repackaged.

### CF-8. The scout-to-modeler AUC gap is enormous (0.6544 → 0.5429)

Scout single-split test AUC (n=88, 2026-04 burned slice): **0.6544**. Modeler CPCV-honest mean AUC: **0.5429**. **Gap = −0.1115.**

Standard CPCV-vs-single-split shrinkage is 0.01-0.03. A 0.11 gap means **the scout's test slice was unrepresentative of the broader timeline** — likely the 2026-04 cohort had patterns the model could fit that don't generalize backward to 2024-2025.

This is also a warning signal for the scout's "AUC ≥0.61 already exceeded" framing I relayed earlier. The scout was directional (signal exists) but quantitatively misleading. If we accept scout's pattern of "single-recent-slice inflation," then ANY future "scout-style" estimation needs to be discounted by ~0.10 AUC before quoting.

### CF-9. Null max (0.5494) is GREATER than observed (0.5429)

`null_distribution.json`:

- B=1000 shuffles, null mean 0.4994, **null max 0.5494**.
- Observed AUC_v2 = 0.5429.
- **Random shuffles produced an AUC HIGHER than our observed signal.**

The gate (e) PASS hinges on the 99th-percentile boundary (0.5365 < 0.5429 = PASS, margin 0.6pp). p_empirical = 3/1000 = 0.003. So 3 random shuffles beat observed. The signal IS there, but it's **at the edge of what randomness alone can produce on this cohort + this CV split structure**.

### CF-10. Per-group top features are completely different — no shared structure

`top_features.json` per-group top-10:

- GBPJPY: dominated by VOLATILITY (h4_sq_return_autocorr_lag20 gain 76; h4_garch_persistence_lag1 gain 75; h1_realized_vol_200 gain 66) + microstructure last_bar_upper_wick_ratio_h4 gain 67.
- GBPUSD_USDJPY: dominated by STRUCTURE (M15 nearest_fvg_dist gain 30; M15 nearest_ob_dist gain 28; M15 nearest_bb_depth gain 28).
- NAS_US30: dominated by STRUCTURE + VOL (M15 dist_to_nearest_swing_low gain 98; h1_range_over_mean_200 gain 73).
- XAU_XAG: **DOMINATED BY TIME/SESSION** (days_to_OPEX gain 44; day_of_year_cos gain 40; days_to_holiday gain 35; day_of_year_sin gain 28).

**Each group's "best features" are nearly disjoint from the others.** The features that work for one group don't transfer. There IS no "shared signal" across groups — only per-group cohort patterns.

The XAU_XAG signal coming from CALENDAR features (day-of-year + holiday/OPEX proximity) is particularly suspicious — it suggests the model is memorizing specific high-impact dates, not learning market structure.

### CF-11. High-gain features in FAILING groups

GBPJPY's group AUC_v2 = 0.4433 (below random by 0.057) but its TOP features have gain 67-76 (very high). **High split-gain doesn't mean correct direction.** The model is splitting often on these features but the splits don't generalize to the test fold. This is overfit pattern in its purest form.

This is unmistakable fingerprint of "1,234 features × 528 rows × 4-fold-train ≈ 0.4 rows-per-feature" pathology.

---

## Open questions (categorized, ranked by Q1.4 impact)

### Category A — Statistical interpretation (high impact)

**A1.** What is the CPCV-honest paired SE accounting for path correlation? If true SE is 0.04 (not 0.02), then the Stouffer p=0.0015 → real p ≈ 0.4 (not significant). **Block bootstrap or the Politis-Romano stationary bootstrap would give a defensible confidence interval.** Q1.4 should compute this.

**A2.** Why does path 9 carry 30% of the lift? Reading `cpcv_paired_results.json` to identify path 9's test-fold composition will tell us whether the result is XAU-driven or genuinely cross-cohort.

**A3.** Is the +0.0309 lift survivable under leave-one-fold-out? If excluding any single path drops the mean below +0.02, the result is fragile. Easy compute: 15 leave-one-out means.

**A4.** PBO 0.4667 is borderline (threshold 0.5). At α=0.4 threshold (more conservative), Q1.3 fails gate (b) too. What threshold is defensible? Bailey & López de Prado discuss [0.3, 0.5] as the gray zone.

**A5.** Per-path IS-best HP varies between 3 different combinations (idx 1, 8, 14). The optimizer picks different HPs on different paths — meaning HP choice is itself unstable. Is this captured in PBO, or is PBO reporting an under-estimate of overfitting risk?

**A6.** Does the null distribution's max (0.5494) > observed (0.5429) tell us anything specific? Max-null is one realization of an extreme-value distribution; with B=1000 the expected max is around 0.54-0.55 even under a null with std 0.015. This suggests our observation falls into the upper tail of "what random looks like" but not as far into it as we'd want.

### Category B — K54 v1 baseline integrity (high impact)

**B1.** Why does K54 v1 perform at AUC 0.512 in CPCV vs published 0.571? The published 0.571 was on a single 2026-04 slice (n=94). Was K54 v1 ever validated under CPCV? **If not, the published baseline is the fluky test-slice number, and our +0.04 lift target was set against an inflated baseline.**

**B2.** The modeler dropped 3 features from K54 v1 (framework + cross_instrument_xau_dir + walk_level_signal) and ADDED `symbol`. This is non-canonical. The original K54 v1 used `instrument_class` (4-class), not `symbol` (7-class). **Adding `symbol` likely STRENGTHENS K54 v1, narrowing the v2-vs-v1 gap.**

**B3.** What if we re-evaluate with the canonical K54 v1 17-feature set (no symbol; include framework + 2 schema-slot features)? Would K54 v1's AUC drop further, making the v2-vs-v1 lift LARGER and possibly passing +0.04? This is a 1-day Q1.4 sub-task.

**B4.** Did the modeler use the same hyperparameters for K54 v1 (trained on 15 features) as for K54 v2 (1,234 features)? With v1's small feature space, the same HP (n_estimators=100, max_depth=5, lr=0.1) may underfit v1 — making v1 look weaker than its true potential. Conversely, K54 v1's original grid was selected for its 17-feature space. A fair v1 baseline should grid-search v1's HPs separately.

**B5.** K54 v1's per-regime ensemble was disabled in the paired comparison (the modeler ran v1 as global single model to match v2's global architecture). This means K54 v1 lost its "+0.032 lift over global per K54 v1 audit." The fair-but-fundamentally-different "per-regime ensemble v1" baseline would be at AUC ≈ 0.512 + 0.032 ≈ 0.544 — much closer to v2's 0.5429! At that point K54 v2 has roughly ZERO lift over a properly-architected K54 v1.

### Category C — Cross-instrument heterogeneity (high impact)

**C1.** Should Q1.4 use per-instrument-group LightGBM ensembles? The 4 effective groups have wildly different top features. Letting each group train its own model (gating XAU_XAG + NAS_US30 ON, GBPJPY + GBPUSD_USDJPY OFF) might preserve the 2 winning groups while not dragging the global on the 2 losing groups.

**C2.** Per-group n: GBPJPY 62, GBPUSD_USDJPY 138, NAS_US30 113, XAU_XAG 215. Per-group LightGBM at n=62 is dangerous (~50 features at 1.2 rows/feature). Need either: (a) heavy feature selection per group, or (b) ensemble of single-group models with majority-vote prediction.

**C3.** XAU_XAG's signal is concentrated in TIME/SESSION features (days_to_OPEX, day_of_year_cos/sin). This is suspicious — calendar features with this much weight suggest memorization of specific high-impact dates. Is this signal genuine or is it overfitting to OPEX-week or year-of-2026 anomalies? **Cross-period replication would either confirm (signal persists) or destroy (signal is 2026-specific) this.**

**C4.** GBPJPY at n=62 + AUC_v2=0.443 is below random by 0.057. Is GBPJPY uniquely hard, or is this a sample-size artifact (n=62 has SE ~0.07)? At n=62 the 95% CI on AUC includes 0.30-0.59. **GBPJPY may be no worse than the others; the "below random" is statistically indistinguishable from random.**

**C5.** Could we drop GBPJPY + GBPUSD_USDJPY from training entirely and train only on XAU+XAG + NAS+US30? The training-population n drops from 528 to 328. But then the model is XAU+indices-only by construction and all per-instrument heterogeneity is bypassed. Strategic question: does this match production? FN trades all 7 — so dropping FX would mean the model can't decision FX trades.

### Category D — Feature catalog properties (medium impact)

**D1.** Only 13 features pruned at |ρ|≥0.95. Audit found 1,852 cross-family pairs at |ρ|≥0.7. **What if we prune at |ρ|≥0.7 or |ρ|≥0.8?** Could reduce the feature space by 500-800 features → better rows-per-feature ratio.

**D2.** With 528 rows × 1,234 features = 0.43 rows-per-feature, we're well below the 5-10 rule of thumb. Even the most-regularized HP (n_estimators=100, max_depth=5, lr=0.1) is over-parameterized. **What's the per-fold feature-screening number that would land us at 5-10 rows-per-feature?** At 528 rows / 5 = 100 features per fold; / 10 = 50 features per fold. This is the de Prado AFML §8.5 recommendation.

**D3.** Feature stability across CPCV paths: how stable is the top-30? If only 5-10 features appear in EVERY path's top-30 and the rest rotate, that's a strong sign of overfit. **Easy compute on the existing model artifacts.** Q1.4 ask.

**D4.** The catalog has 1,219 features but the K54 v2 model uses 1,234 (catalog + 28 liquidity per-instrument variants from scout - 13 prunes = 1,234). Some features are inherently per-instrument (XAU-only round-numbers, JPY-only Tokyo KZ). On the FX cohort, those features are NaN. **NaN-handling in LightGBM may be giving accidental signal — what fraction of the model's split-gain comes from "feature is NaN" branches?**

**D5.** The XAU_XAG group's TIME/SESSION dominance (days_to_OPEX gain 44) is calendar-based. Over 2024-2026 we have ~18 quarterly OPEX dates. The model could be memorizing "trades around OPEX on 2024-09-20 / 2024-12-20 / etc." rather than learning a generalizable "OPEX-week behavior" pattern. **Cross-period replication is the test.**

### Category E — Methodology gaps (medium impact)

**E1.** The modeler's gate (d) was "≥3 of 5 effective groups" but only 4 effective groups exist. Methodology critic erred. **Q1.4 must spec gate (d) against actual instrument grouping (4 groups, not 5).**

**E2.** Brier score is not in the modeler's outputs. Gate (c) (deferred) requires Brier. The modeler will need to compute it at end-of-Q1 holdout opening — but the CPCV Brier as the comparison anchor isn't in the JSONs. Need to verify before holdout opening.

**E3.** The modeler's "per_path_hp_overoptimistic" variant gives AUC 0.5843 with z=5.54 vs null. This wasn't reported in the official Q1.3 verdict but is in the null_distribution.json. The 2× shrinkage (0.0652 → 0.0309) is real — but how much of that shrinkage is HP-instability vs path-data correlation? A pure HP-instability test would compute the same AUC across 27 HP combinations on the SAME fold — if AUC varies by 0.05+ across HP for the same fold, HP choice is the dominant variance source.

**E4.** Was K54 v1 also subject to per-path HP selection bias in the agent's pipeline? `pbo_results.json` shows IS-best-HP varies (idx 1, 8, 14 across paths). If K54 v1's HP was also per-path-best, its AUC may also be inflated. The fair comparison is K54 v1 with fixed HP too (selected by mean OOS).

**E5.** Cross-period replication WAS NOT RUN. This is the audit's actual open test (per A4 GREEN context — the temporal robustness question is the strategic one). **Q1.4 MUST run this.**

### Category F — Things we didn't try (high impact for Q1.4 design)

**F1.** Per-instrument-group LightGBM ensemble (4 models, each with 50-150 features, gated by symbol-group at inference).

**F2.** Per-fold feature screening (de Prado AFML §8.5): inside each CPCV fold, use a screening LightGBM to identify top-50/100/150 features by gain → re-train final model on those.

**F3.** Different label encodings: binary at +0R (current), at +0.5R, at +1R. Or regression of realized R magnitude (not just sign).

**F4.** Different model classes: RandomForest (interpretable), XGBoost (different regularization), CatBoost (handles categoricals natively, no `symbol` encoding hack needed).

**F5.** Block bootstrap for honest SE (per Politis-Romano stationary bootstrap, 200-1000 resamples).

**F6.** Smaller catalogs: top-50 by importance from the current run; top-100; top-200. At 528/100 = 5.3 rows-per-feature, we're back in the safe zone.

**F7.** Bayesian hyperparameter optimization (Optuna) instead of grid search — may find better-regularized HPs in regions the 27-grid missed.

**F8.** Cross-period replication: train on 2024-04 → 2026-01-01 (~280 trades), test on 2026-01-01 → 2026-04-28 (~248 trades). Tests temporal robustness.

**F9.** Feature ablation by family: train K54 v2 with 5 of 6 families (drop one at a time), measure AUC change. If dropping `time_session` or `regime` doesn't move AUC, those families add no information.

### Category G — Things we likely can't test at this n (low Q1.4 priority)

**G1.** Per-(instrument × regime) cell modeling — 22 of 28 cells fail n≥30 per data inventory.

**G2.** Per-instrument fine-tuning at the symbol level — n=51 (NAS100) to 215 (XAU+XAG aggregated; per-symbol max ~164 XAUUSD).

**G3.** Sequence models (LSTM/Transformer) — n=528 is far below what sequence models need; plus this was deferred to Q2 anyway.

### Category H — Things to verify

**H1.** K54 v1 reproducibility at CPCV: re-run K54 v1's original 17-feature canonical setup under CPCV K=6/N=2 to confirm or refute the CPCV-AUC=0.512 number. If canonical v1 is at, say, 0.498 (lower than 0.512), then v2's lift is +0.045 which would PASS the threshold.

**H2.** Path 9 test-fold composition: read `cpcv_paired_results.json` to identify which 2 of 6 groups were in path 9's test. If they're XAU-dominated, path 9 is just per-group cross-instrument result with extra steps.

**H3.** Per-fold feature stability: compute Jaccard overlap of top-30 features across the 15 paths. If overlap < 50%, feature importance is path-specific (overfit signature).

**H4.** Brier score computation: confirm the modeler can compute Brier on holdout when gate (c) opens.

**H5.** Calibration plot quality: per-fold and pooled. Platt sigmoid was applied but we don't have calibration curves to confirm it produced well-calibrated probabilities (esp. in the 0.5-0.7 prediction band where K55 shadow gating would operate).

---

## Strategic recalibration

Putting CF-1 through CF-11 together:

**The Q1.3 result is more negative than "FAIL 2 of 4 gates" implies.**

- The +0.0309 lift may not be statistically real under CPCV-corrected SE (CF-1, CF-2).
- K54 v1 itself doesn't generalize under CPCV (CF-3, CF-4, B1).
- The v1-baseline framework was non-canonical (B2, B3, B5).
- Per-group AUC is mediocre everywhere (CF-5, CF-11).
- Gate (d) threshold was statistically impossible from inception (CF-6).
- Single-fold sensitivity is high (CF-7).
- The scout AUC was inflated by ~0.11 vs CPCV (CF-8).
- Null max > observed (CF-9).
- No shared cross-group signal (CF-10).

**But also more interesting than "K54 v2 is broken":**

- Gate (e) does PASS — the catalog has detectable signal above random (p=0.003).
- 2 of 4 instrument groups (XAU+XAG, NAS+US30) DO show positive lift, even with v1's pathological per-group AUC.
- The features that do work in those groups are interpretable and consistent with the documented edge mechanism (range expansion, OB depth, swing geometry).
- The methodology critic's discipline genuinely caught a 2× false PASS — without it we'd be celebrating a fragile model.

The honest strategic read is: **K54 v2 has a real but small signal that doesn't survive aggressive testing with the current architecture.** The lift is concentrated on metals + indices, with calendar features doing suspicious work on XAU_XAG. The catalog is also too large for the available n.

---

## Recommended Q1.4 design (informed by all of the above)

If we proceed with Q1.4, the spec should incorporate:

### Q1.4 hypothesis (proposed)

*"A reduced 50-150-feature subset of the 1,219-feature catalog (selected via per-fold screening LightGBM, de Prado AFML §8.5) achieves AUC ≥ 0.55 against random (NOT against K54 v1) AND > 0.50 on each of the 4 effective instrument groups, when validated via paired-fixed-HP CPCV (K=6, N=2; 15 paths) + block-bootstrap-corrected SE + cross-period replication (train on 2024-04 → 2026-01-01, test on 2026-01-01 → 2026-04-28). Holdout 2026-04-29 → 2026-05-12 is reserved for end-of-Q1 directional discipline check ONLY (no numeric AUC gate)."*

### Q1.4 thresholds (proposed)

- **(a) CPCV honest:** mean AUC_v2 ≥ 0.55 (NOT mean(v2 − v1); v1 is too unstable to be a useful anchor). Block-bootstrap p<0.01 vs null=0.50.
- **(b) PBO < 0.4** (tighter than 0.5).
- **(c) Per-instrument-group floor:** AUC_v2 > 0.50 on ALL 4 effective groups (not just majority). XAU+XAG, NAS+US30, GBPJPY, GBPUSD+USDJPY.
- **(d) Cross-period robustness:** AUC_v2 on 2026-01-01+ test slice ≥ 0.53 (allowing 0.02 shrinkage from full-CPCV).
- **(e) White-noise null B=1000:** observed ≥ p99.5.
- **(f) Feature stability:** ≥30 features in top-50 across ≥80% of CPCV paths (Jaccard overlap).

This spec is HARDER than Q1.3, not softer — it raises the bar on signal-existence (vs random, not vs flaky v1) while explicitly handling cohort heterogeneity and adding cross-period robustness.

### Q1.4 architecture

Two architectures to evaluate in parallel:

1. **Global LightGBM with regime-as-feature + per-fold feature screening** (de Prado AFML §8.5).
2. **Per-instrument-group ensemble** (4 LightGBMs, one per group; gate by symbol → group at inference; only deploy on groups where Q1.4 gate (c) PASSES).

If neither passes, Q1 closes with K54 v2 reframed as "supplementary signal layer for K55 shadow harness, not primary decision layer." The catalog is preserved for K55 + Q2 work.

### Q1.4 scope-out (don't do these)

- Don't try sequence models at n=528 (Q2 territory).
- Don't try per-(instrument × regime) cells (n insufficient).
- Don't add new features (catalog is already sized; the issue is too many features, not too few).

---

## What I (orchestrator) would do next

I'd spawn 3-4 parallel investigations in the same Opus 4.7 + max-effort pattern, each tightly scoped:

1. **Statistical re-evaluation agent** — block bootstrap SE, leave-one-fold-out sensitivity, path 9 composition, per-fold feature-stability Jaccard. Confirms or refutes whether the +0.0309 lift is real.
2. **K54 v1 baseline canonical re-run agent** — re-train K54 v1 with the canonical 17-feature set (no symbol, include framework + 2 schema-slots) under CPCV K=6/N=2 with grid-searched v1-specific HP. Gives us the true paired comparison anchor.
3. **Architecture A/B agent** — train both (i) global with per-fold screening (top 100 features) and (ii) 4-group per-instrument ensemble. Compare to current v2.
4. **Cross-period replication agent** — 2024-04 → 2026-01-01 train / 2026-01-01 → 2026-04-28 test. Single number: does the +0.0309 lift survive the temporal split?

Total ~3 hours wallclock parallel; subscription-only. Output informs the Q1.4 / Q1-close decision with actual data instead of hand-wringing.

---

## What I do NOT have answers to (and may never)

- Whether the catalog's "real" predictive power (under all biases stripped away) is closer to AUC 0.51 or 0.55. The honest range is wide.
- Whether the XAU_XAG calendar-feature signal is genuine or artefact of 2024-2026's specific high-impact-date sequence.
- Whether K54 v1's published 0.571 was ever a robust number, or whether it's been a fluky test-slice all along (this affects how much weight to put on it as a baseline anywhere).
- Whether 528 rows is fundamentally too small to support 1,200+ features regardless of any methodological discipline. (My intuition: yes, but a tighter catalog could still produce a useful model.)

---

*End of interrogation. Standing by for orchestrator/CEO direction on which of the 4 sub-investigations to launch.*
