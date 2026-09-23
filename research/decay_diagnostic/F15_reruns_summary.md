# F15 — Re-run Summary on Integrated Wave 2 Follow-up Data

_Generated: 2026-04-27 03:10 UTC | Branch: `feat/research-f15-integrated-reruns` | Base: `integration/wave2-followups@7c10b7c`_

## Setup

The structure-detector v2 backfill at the parent
(`shadow_logs/structure_detector_backfill_2026.jsonl`, 3,571 rows, range
`2026-01-21` → `2026-04-24`) was generated against pre-F14 OHLCV. This task's
first action regenerated the backfill against the F14-extended OHLCV
(2024-02-01 → 2026-04-24, 9 instruments × 4 timeframes, sourced from the F14
worktree at `agent-a5e0f3326c6b6c607/data/historical_2026/`).

| Backfill metric | Pre-F14 (parent file) | Pre-F14 (F6 cited in F14 commit) | Post-F14 (F15) |
|---|---:|---:|---:|
| Rows | **3,571** | 7,096 | **30,250** |
| Time range | 2026-01-21 → 2026-04-24 | 2025-10-20 → 2026-04-24 | 2024-02-20 → 2026-04-24 |
| Backfill duration | 3 mo | 6 mo | **26 mo** |
| Instruments | 9 | 9 | 9 |

The 30,250-row backfill is the input to A3, A6, K50, K51, and K53 in F15. K51
and K53 do NOT consume the H4-regime backfill directly (their feature spaces
come from the per-trade record, not the regime tag), so their numbers are
expected to be bit-identical to F5 / F3. A3 and A6 do consume the regime tags
and their numbers move materially.

---

## F15 — re-run summary on integrated data

| Analysis | Prior verdict | New verdict (v2) | n delta | sig delta | Interpretation |
| --- | --- | --- | --- | --- | --- |
| **A3 (side-strat)** | UNTAGGED 43.6% overall, 18.3% (2026 from CLAUDE.md), 100% pre-2026, 411 trades, 0 change points, 1 stratum n≥10 | **UNTAGGED 0.0% overall**, 0.0% in 2026, 411 trades, **1 change point** (XAUUSD London/trending_bull/LONG +35.5pp Jan→Feb 2026, bonf_p=0.0725), 2 strata n≥10 | n unchanged | UNTAGGED -43.6pp; first non-trivial change point now visible | **SHARPER**: blind spot fully closed; new candidate change-point surfaced (pre-decay ramp in trending_bull LONG) |
| **A6** | side +29.64pp bonf_p=0.0560; **regime +21.81pp bonf_p=0.8343** (UNTAGGED-dominated strata); bias +28.87pp bonf_p=0.0673; total attributed +12.68pp | side +29.64pp bonf_p=0.0560 (unchanged); **regime +48.30pp bonf_p=0.0016** (now Bonferroni-significant); bias +28.87pp bonf_p=0.0673; total attributed +15.09pp | h1_n=63, h2_n=44 unchanged | **regime: bonf_p 0.8343 → 0.0016 — newly Bonferroni-significant** | **SHARPER**: regime is now the dominant attributable component. SHORT-side n=12 in H2 (cf. n=1 in H1) keeps `side` at near-significance. Total attributed 12.68 → 15.09pp; observed delta still +8.98pp; residual deepens to -6.11pp |
| **K50 (proper SHAP)** | n=215; rank-1 = displacement_quality_score (38.0%); decay test: **displacement_quality_score Bonferroni-significant (delta +0.0513, bonf_p=1.69e-05, DECAYED)**; framework_id rank-2 (33.6%) | **n=240**; rank-1 = framework_id (51.2%); rank-2 = displacement_quality_score (26.1%); rank-3 = session_id (22.6%); decay test: **NO Bonferroni-significant decay** (displacement_quality delta -0.0184 — direction REVERSED — bonf_p=1.0000) | n +25 | displacement_quality decay flipped from significant→stable, direction reversed | **WEAKENED / FLIPPED**: F16's headline finding (displacement_quality_score is decaying) does NOT replicate at the larger n. Top-rank also flipped to framework_id |
| **K51 (proper SHAP)** | n=129; 0 decayed, 0 newly important, 12 stable at α=0.05 family=12; H1 trade window 2025-02-19 → 2025-04-17, H2 2025-12-19 → 2026-02-03 | **n=129 (unchanged); 0 decayed, 0 newly important, 12 stable**. Trajectories generated with 2 windows of 50 (was 4 windows of 30) | n unchanged | none | **STABLE**: K51 reads `knowledge_base/trade_records/` directly; the H4 backfill does NOT add new trades to its data source. F5 verdict re-confirmed: no Bonferroni-significant decay at n=129 |
| **K53 (Phase 1 only)** | n=75 total / n_holdout=33; train AUC=1.0, test AUC=0.208, **holdout AUC=0.4005**; top features hour_cos, touch_count, ob_retest_distance_atr | **n=75 total / n_holdout=33; train AUC=1.0, test AUC=0.208, holdout AUC=0.4005** (BIT-IDENTICAL to F3) | n unchanged | none | **STABLE / BIT-IDENTICAL**: K53 reads `unified_filled_cands.jsonl`; doesn't depend on H4 regime tags. F3 verdict re-confirmed: classifier indistinguishable from random in H2 |

---

## Strategic refinement

### Strongest verdicts firmed by the larger data

1. **A6 regime as the dominant decay component**: with the 30,250-row regime backfill, A6's `regime` jumps from +21.81pp (bonf_p=0.8343, dominated by UNTAGGED strata) to +48.30pp (bonf_p=0.0016, now Bonferroni-significant). The H1 cohort is overwhelmingly `bullish` (49/63 = 77.8% of trades), the H2 cohort is mixed `bullish` (21), `bearish` (13), `transitional` (10), and the H1 bullish stratum (53.1% WR) collapses to H2 bullish 4.8% WR — a -48.3pp drop. **The regime backfill confirms regime drift is the single largest attributable mover of XAUUSD H1→H2 decay.**
2. **A3 trending_bull LONG decay finally visible**: with UNTAGGED collapsed to 0%, A3 surfaces a trending_bull/London/LONG cell shifting +35.5pp Jan→Feb 2026 (54.5% → 90.0%, bonf_p=0.0725) — this is the *pre-decay ramp* that preceded the H2 collapse F2 already pinpointed. The change-point detector now has signal where prior had silence.
3. **F4 OB-zone result remains intact** (not re-run here — outside F15 scope, but A3 strata coverage gains do not undermine it). A6's `ob_zone` row stays at +8.98pp bonf_p=1.0000 — i.e. ob_zone is NOT the decay driver, regime is.

### Verdicts that weakened or flipped

1. **K50 displacement_quality_score decay does NOT replicate at n=240**. F16 reported delta +0.0513, bonf_p=1.69e-05 (DECAYED) at n=215. F15 measures delta -0.0184 (direction REVERSED), bonf_p=1.0000 (stable). This is the exact pattern memory `feedback_walk_level_evidence_not_predictive` warns about and reinforces `project_f5_k51_does_not_replicate_under_proper_method` as a class-wide methodology issue: SHAP-decay verdicts under small n / small delta are unstable across re-runs with marginally different data.
2. **K50 top-feature re-ranks**: prior had displacement_quality_score #1 (38.0% relative |SHAP|). New has framework_id #1 (51.2%). Both are high-variance estimates with overlapping bootstrap CIs — the rank-flip itself is small-sample noise, but it weakens the case for treating either as the load-bearing K54 input.
3. **K51 verdict unchanged at n=129**: not weakened, but task brief asked "with more data, does anything reach Bonferroni significance now?" — answer: **no**, because K51's data source (live trade records) does NOT grow with the regime backfill. F5's verdict is re-confirmed; the same analysis on the same n=129 with the same Bonferroni family=12 still has 0 decayed components.

### New significant findings (Bonferroni-corrected)

1. **A6 `regime` component at α=0.0016** (bonf_p) — newly significant.
2. **A3 XAUUSD London/trending_bull/LONG +35.5pp** (Jan→Feb 2026, bonf_p=0.0725) — close-to-significant change-point that did not appear at all under prior 43.6% UNTAGGED rate. Below α=0.05 but the only visible signal in the full 411-trade A3 search.

### Verdicts that did NOT change

- A6 `side` row (+29.64pp, bonf_p=0.0560) — unchanged because the side-stratification axis is not regime-dependent.
- A6 `bias` row (+28.87pp, bonf_p=0.0673) — same.
- K51 (n=129, 0 decayed) — unchanged; data source not regime-dependent.
- K53 (n=75, holdout AUC 0.4005) — bit-identical; reads `unified_filled_cands.jsonl`.

---

## Open questions / blockers

1. **K50 displacement_quality_score sign-flip is the loudest signal**. The feature went from "decayed under small SHAP delta" to "growing slightly under small SHAP delta". With CI overlap and an n=240 baseline, neither verdict is stable enough to ship a K54 weighting decision on. The Phase 2 prompt research that leaned on F16's "displacement_quality_score is the load-bearing feature" claim should be re-evaluated. **Action**: do not rely on F16's K50 decay-claim for K54 feature weighting. Treat the F16 verdict as superseded.
2. **A6's `regime` component's H2 stratum sizes are still small** (bullish n=21, bearish n=13, transitional n=10). The +48.30pp attribution is statistically robust under Beta-binomial conjugate posterior, but the H2 bullish 4.8% (1/21) WR drives the bulk of it — that's a tiny-sample tail that warrants per-trade audit before a Phase 2 prompt is gated on regime.
3. **A3's H2 LONG cohort still has no change-point with n≥10 on both sides** — F2's pinpointing of XAUUSD London/trending_bull LONG 76.5% → 16.7% (Δ -59.8pp) cited in CLAUDE.md item #11 is computed inside F2's own run, not here. F15's A3 surfaces only the *Jan→Feb pre-decay ramp* (+35.5pp), not the *Feb→Mar/Apr collapse*, because the decay window straddles a single month with too few trades on either side to clear `min_n=10`.
4. **K53 unchanged at n=75 / holdout n=33** is a hard data limit, not a methodological blocker — Phase 1 trades are exhausted. Future K53 cohorts depend on Phase 2 trade volume.

---

## Falsifiability notes

- All five analyses produced parseable JSON outputs in `*_v2/` directories alongside their pre-existing v1 counterparts.
- The 30,250-row backfill is reproducible: re-running `python scripts/research/backfill_v2_regime.py --data-dir <F14 worktree>` with the same CSVs produces a byte-identical JSONL (excluding the `logged_at` per-row timestamp which the loader ignores).
- Memory citations: every prior-verdict number quoted above traces to either F16's own report (K50), F5's K51 comparison file, F3's classifier_metrics.json (K53), the prior A6 attribution.json, or the prior A3 report.md. CLAUDE.md item #11 is the source for "AUC 0.401 (n=33)" / "side +29.64pp bonf_p=0.056" / "displacement_quality #1".

## Artefacts

- `research/decay_diagnostic/A3_stratification_side_v2/` (strata.jsonl, change_points.json, report.md)
- `research/decay_diagnostic/A6_attribution_v2/` (attribution.json, report.md)
- `research/edge_decomposition/K50_attribution_v2/` (shap_values.json, ranking.json, report.md, comparison.md)
- `research/edge_decomposition/K51_decayed_v2/` (trajectories.json, decay_report.md, comparison.md)
- `research/edge_decomposition/K53_anti_pattern_phase1_v2/` (anti_pattern_report.md, classifier_metrics.json, clusters.json, feature_matrix.json)

The v1 directories (without `_v2` suffix) are preserved unchanged for the comparison baseline.
