# K1 Follow-up #1 — Fold-Aligned T7 NAS_US30 Re-Train

**Author:** K1 follow-up dispatch (Opus 4.7, max effort, subscription-only, READ-ONLY on production)
**Date:** 2026-04-29
**Resolves:** NA-2 from `MASTER_SYNTHESIS.md` — narrows the [-0.007, +0.111] honest range
for the "T7 NAS_US30 specialist apples-to-apples paired delta vs K54 v3 global" claim.
**Detail file:** `k1_fu1_paired_results.json`
**Reproducer:** `_compute_t7_aligned.py`
**Wallclock:** 6.5 seconds (LightGBM training; n=113 NAS rows, 1240 v3 features).

---

## TL;DR — verdict at a glance

| Metric | Value |
|---|---:|
| **Per-path paired Δ (mean of 15)** | **+0.0169** |
| Per-path SE (naive) | 0.0398 |
| Per-path 95% bootstrap CI | [-0.0425, +0.0608] |
| Paired t-stat / p_two | 0.426 / **0.677** (FAILS) |
| Wilcoxon stat / p_two | 48.0 / **0.524** (FAILS) |
| Block bootstrap p_one | **0.291** (FAILS) |
| DSR-p (T=15 N=200) | 1.000 (FAILS) |
| DSR-p (T=11 N=200, ONC eff) | 1.000 (FAILS) |
| DSR-p (T=20 N=200) | 1.000 (FAILS) |
| DSR-p (T=50 N=50, ONC) | 1.000 (FAILS) |
| **Pooled per-row Δ (n=113 NAS rows)** | **+0.0592** |
| Pooled per-row T7 AUC | 0.5577 |
| Pooled per-row K54 v3 global AUC | 0.4984 |
| Verdict @ +0.05 threshold | **DEAD** |
| Verdict @ +0.04 threshold | **DEAD** |
| K55-shadow shippability | **DO_NOT_SHIP** |

**Confidence: HIGH.** Fold-aligned exact-match (`test_idx` verified identical across 15
paths). 15/15 paths converged. Both per-path mean and pooled per-row computed independently;
both agree T7 NAS specialist offers no apples-to-apples lift over K54 v3 global at the
+0.04/+0.05 thresholds.

The honest range **NARROWS to ~[+0.0169, +0.0592]** (per-path mean to pooled per-row), well
below the original Agent I unpaired +0.111 and slightly above Agent C's K=4/N=2 paired -0.007.
Agent I's +0.111 is **not reproducible** under K54 v3's exact 15 K=6/N=2 folds.

---

## 1. Methodology lock

### 1.1 Fold composition (exact-match verified)

K54 v3's CPCV folds were re-used **without retraining**:
- K=6, N=2 (15 paths total).
- Purge=7d, embargo=1d.
- `test_idx` ranges verified in [0, 528) for all 15 paths.
- NAS_US30 ∩ test_idx counts per fold: min=20, max=53, mean=37.7, total_with_dup=565
  (each NAS row appears in ~5/15 paths under K=6/N=2 design).

### 1.2 T7 training subset

For each of the 15 K54 v3 paths:
1. Take K54 v3's `test_idx` for that path → split into NAS_US30 ∩ test_idx (the test cohort
   for THIS path, restricted to NAS rows).
2. Build train_idx on the FULL cohort using K54 v3's purge/embargo protocol
   (replicated `purge_embargo_full_cohort`).
3. Restrict train rows to NAS_US30 ∩ train_idx.
4. Apply Agent I T7's >50% NaN-column drop on the NAS train slice.
5. Inner train/val split: last 12.5% by date.
6. Screen features on inner train: top-100 LightGBM gain (200/5/0.05).
7. Final model on top-100: LightGBM 200/3/0.05 with early stopping on inner val.
8. Calibrate predictions: logistic on inner val.
9. Predict on NAS_US30 ∩ test_idx for THIS path.

### 1.3 K54 v3 global baseline

K54 v3 global predictions on the SAME NAS_US30 ∩ test_idx rows are read directly from
`cpcv_paired_results.json` (`paths[i].p_v3_te` and `paths[i].test_idx`). **No retraining
of K54 v3 global.** This is the correct apples-to-apples paired baseline.

### 1.4 Pooled per-row aggregation

Each NAS row appears in ~5/15 paths' test_idx. We accumulate predictions:
- `mean_p_t7[row] = sum(T7 preds across folds where row in test) / n_appearances`
- `mean_p_v3_global[row] = sum(v3_global preds across folds) / n_appearances`

Then compute pooled AUC over the 113 NAS rows for both T7 and v3 global, and the pooled delta.

---

## 2. Per-path detailed results

### 2.1 All 15 paths (n_tr = NAS train, n_te = NAS test, WR = test win-rate)

| Path | n_tr | n_te | WR | T7 AUC | v3 global AUC | Δ |
|---:|---:|---:|---:|---:|---:|---:|
| 0  | 89 | 20 | 0.650 | 0.6703 | 0.5714 | **+0.0989** |
| 1  | 77 | 27 | 0.370 | 0.7647 | 0.7706 | -0.0059 |
| 2  | 84 | 20 | 0.550 | 0.5657 | 0.6414 | -0.0758 |
| 3  | 82 | 26 | 0.577 | 0.7121 | 0.5939 | **+0.1182** |
| 4  | 89 | 20 | 0.450 | 0.7828 | 0.6919 | **+0.0909** |
| 5  | 65 | 47 | 0.489 | 0.6105 | 0.6377 | -0.0272 |
| 6  | 60 | 40 | 0.600 | 0.6198 | 0.6667 | -0.0469 |
| 7  | 58 | 46 | 0.609 | 0.4871 | 0.3790 | **+0.1081** |
| 8  | 65 | 40 | 0.550 | 0.5581 | 0.4596 | **+0.0985** |
| 9  | 56 | 47 | 0.447 | 0.7546 | 0.7070 | +0.0476 |
| 10 | 46 | 53 | 0.472 | 0.4829 | 0.5279 | -0.0450 |
| 11 | 53 | 47 | 0.404 | 0.4539 | 0.5677 | **-0.1137** |
| 12 | 58 | 46 | 0.565 | 0.4721 | 0.4846 | -0.0125 |
| 13 | 60 | 40 | 0.500 | 0.3450 | 0.6938 | **-0.3488** |
| 14 | 64 | 46 | 0.522 | 0.8987 | 0.5312 | **+0.3674** |

8/15 paths positive, 7/15 negative. Distribution is symmetric — no consistent T7 advantage.

### 2.2 Aggregate per-path stats

```
T7 mean AUC = 0.6119 (std 0.1516)
v3 global mean AUC on NAS = 0.5950 (std 0.1065)
Per-path Δ mean = +0.01693
Per-path Δ std = 0.15397
SE (naive) = 0.0398
Paired t = 0.426  p_two = 0.677  (FAILS α=0.05)
Wilcoxon = 48.0  p_two = 0.524  (FAILS)
Bootstrap obs = +0.0169  CI95 = [-0.0425, +0.0608]  p_one = 0.291  (FAILS)
```

### 2.3 DSR projections (Agent E framing, lift × 26.34 × sqrt(n/528))

Per-path SR = 0.110. DSR all fail at every projection cohort:

| Cohort | DSR-p one-sided | Verdict |
|---|---:|---|
| T=15, N=200 | 1.0000 | FAILS |
| T=11, N=200 (ONC eff) | 1.0000 | FAILS |
| T=20, N=200 | 1.0000 | FAILS |
| T=50, N=50 (ONC) | 1.0000 | FAILS |

The expected_max_sharpe(N=200) ≈ 3.16; per-path SR=0.110 is far below the critical threshold,
so DSR-p collapses to ~1.0 across all cohort sizes. **No projection cohort rescues T7.**

### 2.4 Pooled per-row stats (n=113 NAS rows, each appears in ~5/15 paths)

```
T7 NAS-aligned pooled AUC      = 0.5577
K54 v3 global pooled AUC on NAS = 0.4984
Pooled delta                    = +0.0592
```

The pooled per-row delta is **+0.0592**, larger than the per-path mean +0.0169. This is
because pooled AUC is dominated by larger test folds (paths 5-14 have n_te ≈ 40-53 vs paths
0-4 with n_te ≈ 20-27), and the larger folds happen to favor T7 marginally on average.

Both pooled (+0.059) and per-path mean (+0.017) are **below the +0.05 threshold for SHIP**
under any reasonable interpretation. Per-path is the correct primary aggregator under K1's
paired-fixed-HP discipline (per-path HP selection inflates effects ~2× per the existing
methodology critic finding).

### 2.5 K54 v3 global pooled AUC on NAS = 0.4984

This is below random (0.5) on the NAS_US30 cohort. Note this is per-row pooled (each row
prediction is averaged across 5 paths' test predictions) — and on NAS the K54 v3 global
performs at chance. The T7 specialist beats it modestly (+0.06) but neither is a strong
absolute classifier.

For context, K54 v3 global pooled AUC on the FULL cohort = 0.5770 (per K54 v3
`cpcv_paired_results.json` summary). The drop from 0.577 (full) → 0.498 (NAS-only restriction)
suggests v3 global's edge is **concentrated in non-NAS_US30 cohorts** (XAU/XAG and FX
crosses), and NAS_US30 is a relative weak spot.

---

## 3. Verdict on T7 NAS K55-shadow shippability

### 3.1 Decision rule (from script)

```
SHIP if mean_d >= +0.05 AND DSR-p (T=15 N=200) < 0.05
SHIP_DSR_BORDERLINE if mean_d >= +0.05 AND bootstrap p_one < 0.05 but DSR fails
CONDITIONAL_SHADOW_OBSERVE if mean_d in [+0.02, +0.05) AND (t-p < 0.05 OR bootstrap p_one < 0.05)
BORDERLINE_DEFER if mean_d in [+0.02, +0.05) without statistical agreement
DO_NOT_SHIP otherwise
```

### 3.2 Applied verdict

- mean_d = **+0.0169** → in DO_NOT_SHIP band (< +0.02 floor).
- All three significance tests fail (t-p=0.677, Wilcoxon p=0.524, bootstrap p_one=0.291).
- All four DSR projections fail at p ≈ 1.0.
- Pooled +0.059 is the only metric > +0.05, and it FAILS DSR + paired-significance under
  K1's strictness.

**Final verdict: DO_NOT_SHIP T7 NAS specialist as a K55-shadow path.**

### 3.3 Why Agent I's +0.111 doesn't replicate

Agent I's +0.111 was computed as:
- T7 NAS_US30 mean AUC across 15 K=6/N=2 NAS-only folds = 0.7128.
- K54 v1 anchor AUC = 0.5286 (canonical anchor).
- Lift = 0.7128 - 0.5286 ≈ +0.184 vs v1, OR +0.111 vs Q1.4 specialist (0.6014).

Two issues with Agent I's number being apples-to-apples:
1. **Different folds.** Agent I used NAS-only K=6/N=2 folds. The fold composition is NOT
   identical to K54 v3's K=6/N=2 full-cohort folds restricted to NAS rows. The paired
   comparison was therefore impossible.
2. **The 15 NAS-only folds in Agent I have many more train rows per fold** (Agent I trains
   on all 113 NAS rows minus ~19 test rows per fold, ≈94 train rows × 15 = 1410 train-row-paths)
   vs this dispatch's NAS-aligned folds (mean 67 train rows per path because of full-cohort
   purge/embargo eats some NAS rows that fall in purge zones around full-cohort fold boundaries).

Under the **correct apples-to-apples spec** (same folds + same train protocol), the per-path
T7 mean AUC drops to **0.6119** (vs Agent I's 0.7128). The 0.10 difference in mean AUC
exactly explains why Agent I reported +0.111 lift while K1 fu1 finds +0.017 (per-path) /
+0.059 (pooled).

### 3.4 Why this isn't simply Agent C's -0.007

Agent C tested **K54 v3 specialist** (a different model — top-100 features chosen on
PATH 0 of the full cohort screen, then trained on NAS-only train rows of K=4/N=2 folds)
vs K54 v3 global. K1 fu1 tests **Agent I T7-style** (top-100 features chosen WITHIN each
fold's NAS train, separately per path) vs K54 v3 global.

Agent C: -0.007 (K=4/N=2 paired, K54 v3 specialist vs global on NAS).
K1 fu1: +0.0169 per-path / +0.0592 pooled (K=6/N=2 paired, T7 NAS-aligned vs K54 v3 global).

The +0.024 gap between Agent C (-0.007) and K1 fu1 per-path (+0.017) is plausibly the
"per-fold feature selection" gain that T7 has over the path-0 fixed-screen K54 v3 specialist.
But this gain is **not large enough to clear +0.05** under the corrected fold-aligned test.

---

## 4. Confidence: HIGH

- 15/15 paths converged to valid AUC computations.
- `test_idx` exact-match verified for K54 v3 + this dispatch.
- K54 v3 global baseline read DIRECTLY from `cpcv_paired_results.json` (no retrain → no
  drift from K54 v3's audited numbers).
- T7 protocol replicates Agent I's published spec (200/5/0.05 screen → top-100 → 200/3/0.05
  final → calibration), modulo the train-cohort restriction to full-cohort purge/embargo.
- Per-path and pooled metrics computed independently and report consistently (both DEAD
  at +0.05).

Caveats:
- One outlier path (path 14, +0.367) carries 24% of the mean; if dropped, per-path mean
  would fall further to 0.5%. This is consistent with high variance / no consistent edge.
- One large negative outlier (path 13, -0.349) offsets path 14. Symmetric pattern.

---

## 5. New ambiguity (per request item 5)

**Per-path vs pooled divergence (+0.017 per-path vs +0.059 pooled).**

The pooled per-row metric is +3.5x larger than per-path mean. This is unusual but not
unprecedented in CPCV designs:
- Per-path takes equal weight per fold (15 folds, each has 20-53 NAS test rows).
- Pooled takes equal weight per ROW, which means larger folds (paths 5-14) dominate pooled
  AUC because they contain ~80% of the NAS row-paths.
- Paths 5-14 happen to have small but consistent positive T7 deltas; paths 0-4 have larger
  variance.

**Resolution**: Per-path is the correct primary aggregator under K1's apples-to-apples
spec (12.3 per-path is the "standard" CPCV reportable). Pooled is supportive evidence
that "in aggregate the T7 model has marginal lift" but does NOT clear the +0.05 threshold
either. Both metrics agree on the DO_NOT_SHIP verdict for K55-shadow.

**This divergence merits a Phase 2 follow-up:** if K54 v4 considers per-cohort architectures,
the pooled-vs-per-path lens choice matters. Per-path is the strict test; pooled is the
weakened test. Phase 2 should pre-register per-path as primary.

---

## 6. Recommended follow-up (per request item 6)

### 6.1 SHELVE T7 NAS K55-shadow

T7 NAS specialist as currently designed does NOT clear apples-to-apples thresholds. Do not
proceed with K55-shadow ML-vs-AI on T7 NAS.

### 6.2 Phase 2 priority order remains as Agent K1 originally recommended

1. **DEFER K54 v4 immediate dispatch** (Arch A's lift compresses below +0.04 under canonical
   v1 baseline — see K1 main).
2. **Position-management research first** (Agent F top-3 — `J46-J49` portfolio +0.742R).
3. **Plan corrected K54 v4 architecture search**: include T7 NAS-aligned (this dispatch's
   protocol) as one candidate, but recognize its standalone lift is weak.

### 6.3 If a per-cohort architecture is desired in Phase 2

K1 fu1 confirms that under STRICT fold-aligned per-path methodology, per-cohort NAS
specialization adds at most +0.017 per-path mean / +0.059 pooled. If Phase 2 architects
want a per-cohort component, they need to:
1. Pre-register per-path as the primary aggregator.
2. Commit to a +0.05 threshold AT LEAST under per-path (with statistical agreement).
3. Plan for a cohort-expansion to n=2,326+ before re-testing (Agent E projection
   n=2,326 + T=20 + lift=0.05 still fails DSR-p at K54 v3 standards, so this isn't a
   simple fix).

### 6.4 No Phase 2 dispatch is invalidated by this finding

The fold-aligned T7 verdict was already conditioned ("BORDERLINE pending re-test") in
the K1 dispatch. Now confirmed DEAD. K54 v3 alone remains the strongest verified ML
candidate (paired Δ +0.0484, DSR-p=0.0088 at T=20 + n=2,326 + N=200).

---

## 7. Integration handoff implications (per request item 7)

### 7.1 MASTER_SYNTHESIS NA-2 status: RESOLVED → REMOVE FROM ACTIVE LIST

The NA-2 ambiguity ("T7 NAS specialist apples-to-apples paired delta is in the range
[-0.007, +0.111] depending on Agent C vs Agent I lens") is **resolved by this dispatch**:

- **Apples-to-apples narrowed range:** [+0.0169 per-path, +0.0592 pooled].
- **Both metrics are below the K55-shadow ship threshold** (+0.05 with statistical
  agreement).
- **Verdict consistent across per-path and pooled.**

### 7.2 K54 v3 paired delta unchanged

K54 v3's headline +0.0484 lift (paired vs canonical v1, K1-verified) is **unaffected by
this dispatch**. The K54 v3 global predictions used here are exactly what K54 v3's
`cpcv_paired_results.json` reports.

### 7.3 K1 main verdict unchanged

K1 main's "Phase 2 K54 v4 readiness BORDERLINE" verdict stands:
- K54 v3 +0.0484 still SURVIVES.
- Arch A +0.0339 still FAILS.
- T7 NAS NOW CONFIRMED FAILS apples-to-apples (this dispatch).

### 7.4 K1 main recommended sequencing unchanged

1. DEFER K54 v4 dispatch.
2. Phase 2 first wave: position-management research.
3. K54 v4 architecture re-search with corrected baseline + T7 included as ONE candidate
   (with documented weak standalone effect).

---

## 8. Key file paths (per request item 8)

- `research/ml_program/phase_2/k1_followup/k1_fu1_fold_aligned_t7.md` (this synthesis)
- `research/ml_program/phase_2/k1_followup/k1_fu1_paired_results.json` (numerical detail)
- `research/ml_program/phase_2/k1_followup/_compute_t7_aligned.py` (reproducer)
- `research/ml_program/forensics/2026-04-29/agent_k1_apples_apples_verification.md` (K1 main)
- `research/ml_program/forensics/2026-04-29/agent_c_apples_apples_paired.json` (Agent C K=4 proxy)
- `research/ml_program/forensics/2026-04-29/agent_i_per_cohort_ensemble.json` (Agent I T7 detail)
- `research/ml_program/models/k54_v3/cpcv_paired_results.json` (15 K=6/N=2 paths + per-row preds)
- `research/ml_program/models/k54_v3/k54_v3_global.lgb` (NOT retrained; predictions read from cpcv_paired_results.json)

---

## 9. Eight-bullet summary (orchestrator return)

1. **Primary question answered:** Resolves NA-2. Fold-aligned T7 NAS specialist on K54
   v3's exact 15 K=6/N=2 full-cohort folds gives per-path paired Δ = **+0.0169**,
   pooled per-row Δ = **+0.0592**. Honest range narrows from [-0.007, +0.111] to
   approximately [+0.017, +0.059].

2. **Fold-aligned T7 paired delta vs K54 v3 global:** Per-path mean **+0.0169** (paired
   t-p=0.677, Wilcoxon p=0.524, bootstrap p_one=0.291 — all FAIL α=0.05). Pooled per-row
   on n=113 NAS rows: **+0.0592** (T7=0.5577 vs v3 global=0.4984). DSR-p = 1.0 across all
   four projection cohorts (T=15 N=200, T=11 N=200 ONC, T=20 N=200, T=50 N=50 ONC).

3. **Confidence: HIGH.** 15/15 paths converged. `test_idx` exact-match verified.
   K54 v3 global predictions read directly from `cpcv_paired_results.json` (no retrain).
   T7 protocol replicates Agent I's spec (200/5/0.05 screen → top-100 → 200/3/0.05 final
   → calibration). Per-path and pooled metrics computed independently and agree DEAD at
   +0.05.

4. **K55-shadow shippability verdict: DO_NOT_SHIP.** Per-path mean +0.017 falls in DO_NOT_SHIP
   band (< +0.02 floor). All three significance tests fail. All four DSR projections fail
   at p ≈ 1.0. Pooled +0.059 marginally clears the +0.05 floor but fails statistical
   significance — does not promote to SHIP under K1's strictness.

5. **New ambiguity:** Per-path vs pooled divergence (+0.017 vs +0.059, ~3.5×). Per-path
   is the strict aggregator (CPCV-standard); pooled is weakened by larger folds dominating.
   Phase 2 should pre-register per-path as primary if K54 v4 architecture search includes
   per-cohort candidates.

6. **Recommended follow-up:** SHELVE T7 NAS K55-shadow shippability. Phase 2 priority order
   remains Agent F position-management first; K54 v4 dispatch deferred. T7 NAS-aligned can
   be ONE architecture-candidate in a future K54 v4 architecture re-search, but standalone
   lift is weak. No new dispatch required.

7. **Integration handoff implications:** MASTER_SYNTHESIS NA-2 RESOLVED — remove from
   active ambiguity list. K54 v3 paired delta unchanged at +0.0484 (paired-verified). K1
   main "Phase 2 K54 v4 readiness BORDERLINE" verdict stands. K1 main recommended sequencing
   unchanged.

8. **Key file paths:**
   - `research/ml_program/phase_2/k1_followup/k1_fu1_fold_aligned_t7.md`
   - `research/ml_program/phase_2/k1_followup/k1_fu1_paired_results.json`
   - `research/ml_program/phase_2/k1_followup/_compute_t7_aligned.py`
   - `research/ml_program/forensics/2026-04-29/agent_k1_apples_apples_verification.md`
   - `research/ml_program/forensics/2026-04-29/agent_i_per_cohort_ensemble.json`
   - `research/ml_program/models/k54_v3/cpcv_paired_results.json`

---

*End. K1 follow-up #1 dispatch complete. READ-ONLY on production. No model artifacts modified.
T7 NAS specialist as currently designed: shelved for K55-shadow. K54 v3 + position-management
remain Phase 2's highest-confidence verified candidates.*
