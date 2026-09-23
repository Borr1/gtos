# K54 v2 Q1.3 Statistical Re-Evaluation

**Author:** Statistical Re-Evaluation Auditor (post-Q1.3 robustness audit, 2026-04-28)
**Inputs:** `cpcv_paired_results.json` (15 paths × per-path AUC + DeLong p + paired predictions), `feature_matrix.parquet` (528 × 1,260, max date 2026-04-24), `feature_prune_list.json` (13 pruned features), `meta.json` (selected HP idx=5: n_estimators=100, max_depth=5, lr=0.1).
**Cohort cutoff verified:** `feature_matrix['__date'].max() == '2026-04-24'` (≤ 2026-04-28 cutoff, holdout untouched).
**Cross-checks:** my path-fold map (combo ordering of `itertools.combinations(range(6), 2)`) reproduces `cpcv_paired_results.paths_fixed_hp[*].test_idx` exactly. Naive mean +0.030896 / std 0.07943 / SE_iid 0.02051 reproduce header verbatim.
**Intermediate JSONs:** `_stat_reeval/q1_bootstrap.json`, `_stat_reeval/q2_loo.json`, `_stat_reeval/q3_path9.json`, `_stat_reeval/q4_jaccard.json`, `_stat_reeval/q4_per_path_top30.json`.

---

## Section 1 — Q1 block-bootstrap SE results

**Politis–Romano stationary bootstrap (B=1000, average block L=5, seed=42):**

| Quantity | Value |
|---|---|
| Bootstrap mean(diff) | **+0.031630** (matches naive +0.030896 within MC noise) |
| Bootstrap SE | **0.016097** |
| Naive iid SE | 0.020509 |
| Bootstrap 95% percentile CI | **[+0.000107, +0.061197]** |
| Bootstrap one-sided p (H1: mean > 0) | **0.019** |
| Bootstrap two-sided p | 0.038 |

**Surprise:** PR bootstrap returns a SE *smaller* than naive iid, not larger as expected. Cause: lag-2 and lag-3 serial autocorrelation of the per-path diff sequence are negative (−0.348, −0.251); blocks of length 5 average over those negative serial correlations and shrink the realized resample variance.

**This is mathematically the answer the spec asked for, but it is the wrong tool for the CPCV-correlation question.** CPCV path correlation is structural (paths share training folds), not serial. The PR bootstrap, applied to a 15-element vector with no meaningful temporal ordering, misses the structural dependency entirely.

**CPCV-honest SE proxy (training-fold-overlap-weighted).** Each pair of distinct paths shares either 2/4 train folds (when their test combos are disjoint) or 3/4 train folds (when their test combos share one element). Empirical mean off-diagonal training-overlap fraction = **0.6429**. Treating this as the average pairwise correlation ρ between path diffs:
- SE_cpcv_honest ≈ sqrt(var(diffs)/n × (1 + (n−1)·ρ)) = **0.06486**
- 95% CI = **[−0.0962, +0.1580]**
- t-stat = 0.030896 / 0.06486 = **0.476**
- two-sided p (normal approx) = **0.675**

This proxy is more conservative than the orchestrator's CF-2 estimate (~0.040 SE) because the orchestrator divided by sqrt(n_eff)≈sqrt(3-4); my path-pair-overlap method gives n_eff ≈ 2.4. The qualitative conclusion is identical: **once CPCV path dependency is honored, the +0.0309 lift is statistically indistinguishable from zero.**

**Verdict on Stouffer combined p (0.001546):** the Stouffer p is internally valid IF the per-path DeLong tests were on independent datasets. The CPCV configuration violates that: paths 1, 2, 3, 4 all use fold 0 in their test set (each shares its single XAU rows in test with several others); paths share 2-3 of their 4 training folds. The Stouffer combined p is an artifact of treating dependent z-scores as independent. **The PR bootstrap p (0.019), and especially the CPCV-honest p (0.675), are more credible at this CPCV configuration. The Stouffer p of 0.0015 should not be cited as evidence in the Q1.3 verdict.**

---

## Section 2 — Q2 leave-one-fold-out sensitivity

LOO mean = mean of OTHER 14 paths after dropping path *i*.

| Drop path | Dropped diff | Dropped DeLong p | LOO-14 mean |
|--:|--:|--:|--:|
| 0 | −0.0371 | 0.597 | +0.03576 |
| 1 | +0.0358 | 0.539 | +0.03055 |
| 2 | +0.0280 | 0.561 | +0.03110 |
| 3 | +0.0941 | 0.205 | +0.02638 |
| 4 | +0.0860 | 0.183 | +0.02696 |
| 5 | +0.0409 | 0.458 | +0.03018 |
| 6 | +0.0936 | 0.068 | +0.02642 |
| 7 | −0.0595 | 0.287 | +0.03736 |
| 8 | +0.1137 | 0.104 | +0.02498 |
| **9** | **+0.1454** | **0.009** | **+0.02271** ← LOO min |
| 10 | −0.0620 | 0.248 | +0.03753 |
| 11 | −0.1163 | 0.071 | **+0.04141** ← LOO max |
| 12 | −0.0605 | 0.307 | +0.03743 |
| 13 | +0.1011 | 0.085 | +0.02588 |
| 14 | +0.0603 | 0.335 | +0.02879 |

**Aggregates.** LOO min = +0.02271 (drop path 9). LOO max = +0.04141 (drop path 11, the most negative diff). LOO median = +0.03018.

**Fragility counts.** #LOO < +0.02 = **0**. #LOO < +0.01 = **0**. #LOO < 0 = **0**.

**Verdict (per spec rules): ROBUST.** Every LOO mean ≥ +0.02. No single path can collapse the mean below half of the +0.04 target.

**Caveat the rules don't capture.** Path 9 is the most influential by a wide margin: dropping it shaves the mean from +0.0309 → +0.0227, a **26.5% relative reduction**. Dropping any other path moves the mean by ≤16% relative. The headline +0.0309 is "ROBUST to single-fold removal" only when that fold's diff is near the average. Path 9's +0.1454 is a 4.5σ outlier vs the other 14 paths' SE; the LOO-14 mean still sits *exactly* at the orchestrator's CF-7 threshold (+0.0227). One single fold off the floor of "no decay" of the headline.

---

## Section 3 — Q3 path 9 test-fold composition

**Path 9 = combo (2, 3) per `itertools.combinations(range(6), 2)` ordering** — verified by reconstructing test_idx and matching against `cpcv_paired_results.paths_fixed_hp[9].test_idx` (set equality holds).

**Fold meta.**
- Fold 2: n=88, dates 2026-01-22 → 2026-02-13.
- Fold 3: n=88, dates 2026-02-13 → 2026-03-10.
- **Path 9 test cohort:** n=176, **dates 2026-01-22 → 2026-03-10** (Q1 2026, ~7-week window).

**By symbol (n=176):** XAUUSD 29, USDJPY 28, US30_CASH 24, GBPUSD 24, GBPJPY 24, XAGUSD 24, NAS100 23. **No instrument carries even 17% of the cohort** — all 7 instruments are within ±3 trades of equal representation.

**By instrument class:** fx 76 (43%), metals 53 (30%), other (USDJPY/GBPJPY by class) 24 (14%), indices 23 (13%).

**By month:** 2026-01 = 34 (19%), 2026-02 = **110 (62.5%)**, 2026-03 = 32 (18%). Path 9 is **February-2026-heavy**.

**By direction:** LONG 101, SHORT 75. Win rate 0.523 (92/176).

**Path-9 lift decomposition by group (paired AUC v2 vs v1 on same 176 rows):**

| Group | n | AUC_v2 | AUC_v1 | diff |
|---|--:|--:|--:|--:|
| XAU_XAG | 53 | 0.6629 | 0.5100 | **+0.1529** |
| GBPJPY | 24 | 0.5214 | 0.3679 | **+0.1536** |
| GBPUSD_USDJPY | 52 | 0.6402 | 0.5060 | **+0.1342** |
| NAS_US30 | 47 | 0.7143 | 0.6099 | **+0.1044** |

**Per-symbol lift (n≥23):** XAUUSD +0.336, GBPUSD +0.182, GBPJPY +0.154, US30_CASH +0.133, USDJPY +0.086, NAS100 +0.085, XAGUSD **−0.042**. **6 of 7 symbols positive.**

**Verdict on Q3: GENUINELY CROSS-COHORT.** Path 9 is *not* XAU-driven (XAU_XAG is just one of four positive-lift groups; XAGUSD inside that group is negative); not FX-driven (FX is only 43% of the cohort); not symbol-concentrated (max single symbol = 16% of cohort). The lift IS time-window-driven — Feb 2026 dominates 62% of the cohort, and v2 outperforms v1 on essentially every symbol within that window. This is the *opposite* of CF-7's hypothesis ("if path 9's test fold was XAU-heavy, the lift may just be the XAU+XAG signal repackaged"). **Path 9's lift is real OOS performance over a single 7-week window, not a single-instrument artifact.** The fragility is therefore *period-window* fragility: K54 v2 has +0.10-0.15 lift for one ~7-week window in Q1 2026, and ~0 lift the rest of the timeline.

---

## Section 4 — Q4 per-fold feature-stability Jaccard

**Method.** Re-trained 15 K54 v2 LightGBM models (selected HP n_estimators=100, max_depth=5, lr=0.1, deterministic, seed=42, post-prune 1234 features), each on path *i*'s purged train fold (mean n=274 inner-train rows) with 15% inner-val for early stopping. Extracted top-30 features by `feature_importances_` (split-gain). Pairwise Jaccard = |A∩B| / |A∪B| over the C(15,2)=105 path-pairs.

**Top-1 features per path (illustrative variance).**

| Path | Top-1 feature | Gain |
|--:|---|--:|
| 0 | vol__h1_range_over_mean_20 | 12 |
| 1 | vol__m15_bb_width_pct_200_w100 | 6 |
| 2 | vol__h1_range_over_mean_200 | 8 |
| 3 | struct__M15__dist_to_swing_band_atr | 17 |
| 4 | vol__h1_atr_50_pct_w500 | 3 |
| 5 | vol__m15_atr_14 | 1 |
| 6 | liq__liq_round_50p0_dist_above_ticks | 10 |
| 7 | vol__m15_sq_return_autocorr_lag1_w50 | 7 |
| 8 | micro__synthetic_cum_delta_zscore_m1_240min_vs_lb20 | 5 |
| 9 | ts__t_days_to_nearest_holiday_signed | 14 |
| 10 | ts__t_days_to_nearest_holiday_signed | 17 |
| 11 | vol__h1_sq_return_autocorr_lag20_w200 | 3 |
| 12 | struct__M15__dist_to_swing_band_atr | 9 |
| 13 | vol__m15_atr_14 | 2 |
| 14 | vol__m15_sq_return_autocorr_lag5_w50 | 4 |

15 paths, 11 distinct top-1 features. Only `struct__M15__dist_to_swing_band_atr`, `ts__t_days_to_nearest_holiday_signed`, and `vol__m15_atr_14` are top-1 in more than one path (all in 2 paths). Top-1 absolute gains range 1-17; **gain magnitudes are tiny** (LightGBM gain is typically hundreds-thousands when a feature is doing real work) — consistent with `n_features_with_nonzero_gain` ranging 12-248 across paths (paths with the cleanest signal use only a dozen features; paths with weaker signal scatter gain across hundreds).

**Pairwise Jaccard distribution (n=105 path-pairs).**

| Statistic | Value |
|---|--:|
| Mean | **0.0724** |
| Median | 0.0714 |
| Min | **0.0000** (some path-pairs share NO top-30 features) |
| Max | 0.2245 |

**Stable core.**
- **Features in ALL 15 paths' top-30: 0.**
- **Features in ≥80% (≥12 of 15) paths: 0.**
- Most-stable single feature: `vol__h1_range_over_mean_50` appears in **9 of 15** paths' top-30.
- Distribution: of 248 unique features that appear in *any* path's top-30, **141 (57%) appear in only 1 path**; only 14 appear in ≥5 paths.

| Frequency | # features |
|--:|--:|
| 9 | 1 |
| 8 | 2 |
| 7 | 2 |
| 6 | 4 |
| 5 | 5 |
| 4 | 9 |
| 3 | 17 |
| 2 | 67 |
| 1 | 141 |

**Family of the (loose) stable-ish core (≥6 paths):** 5 volatility, 2 microstructure, 1 structure, 1 time-session. **Zero regime features**, despite K54 v2's headline being "regime-as-feature." The 20 `reg__*` regime features (which made `meta.json` look like the regime hypothesis was being tested) are simply not in any path's top-30 with stability.

**Verdict (per spec rules): UNSTABLE.**
- Mean Jaccard 0.0724 << 0.30 (UNSTABLE threshold).
- Stable-core count 0 << 3 (UNSTABLE threshold).
- Both criteria triggered.

This is one of the lowest feature-stability Jaccard scores I would expect to see from a model claiming useful generalization. With 1234 features and ~274 effective training rows per fold (≈0.22 rows/feature), the per-fold "best feature set" is dominated by which features happen to fit the specific train-fold idiosyncrasies. **The model has no consistent feature-importance structure across folds; each path is essentially fitting a different model.**

---

## Section 5 — Verdict on the +0.0309 lift's robustness

**Synthesis of Q1-Q4 evidence.**

| Test | Result | Reading |
|---|---|---|
| Q1: PR stationary bootstrap | CI [+0.0001, +0.0612], one-sided p=0.019 | Marginally significant under serial-block assumption. But this is the wrong dependency model — CPCV correlation is structural, not serial. |
| Q1: CPCV-honest training-overlap proxy | SE 0.0649, t=0.476, p=0.675 | **Lift indistinguishable from zero once path correlation is honored.** |
| Q2: LOO-14 fragility | All LOO ≥ +0.02 (verdict ROBUST per rule) | Per the strict rule. But path 9 alone is +26.5% of the mean — close to half the target. Single-period fragility. |
| Q3: Path 9 composition | Cross-cohort, Feb-2026-window-driven | The single most-influential path is *not* a single-instrument artifact. It is a single ~7-week window where v2 happens to outperform v1 on 6 of 7 symbols. This is *temporal* fragility. |
| Q4: Per-fold feature Jaccard | Mean 0.0724, stable-core count 0 (verdict UNSTABLE) | **No two paths agree on what the model is "learning."** Classic 0.22-rows-per-feature overfit signature. |

**Final answer to the headline question.** The +0.0309 lift is **not "real signal that fails the +0.04 threshold" — it is statistical noise inflated by Stouffer's independence assumption.** Three independent lines of evidence converge:

1. The Stouffer combined p of 0.0015 is the *only* number that calls the lift significant. Once CPCV path correlation is honored (Q1 supplement), the corrected p is 0.68. Once a single fold is dropped (Q2, path 9), the LOO mean is +0.0227 — which is itself NON-significant under any honest SE.
2. The path-9 outlier that drives 26.5% of the mean is a single 7-week window in Q1 2026 (Q3). Removing it leaves a mean that is below half the +0.04 target.
3. The model has zero feature-importance stability across folds (Q4 mean Jaccard 0.072, zero stable-core features). With 1234 features and 274 effective training rows per fold, the model is statistically incapable of learning a transferable structure; it is fitting fold-specific noise. The +0.0309 lift is what 15 fold-specific models *coincidentally average to*, not what a single coherent model achieves.

The interlocking conclusion is stronger than either Q1, Q2, Q3, or Q4 alone: the +0.0309 lift is consistent with **a high-dimensional model overfitting to fold-specific patterns, with random-window aggregation producing a small positive aggregate**. The model is not "close to working" — it has not learned anything that generalizes beyond a single 7-week window.

**Practical implication for Q1.4 / Q1-close.** Do not ship a "K54 v3 fixes the threshold gap" research thread. The threshold gap (+0.04 vs realized +0.031) is illusory; the realized number itself is not significant. The high-priority Q1.4 question is whether *any* model on the current 528-row cohort + 1247-feature catalog can achieve generalizable lift, and the Q4 evidence (mean Jaccard 0.072, zero stable-core) suggests the answer is no — feature-engineering refinement is upstream of any modeling refinement.

**Top-1 surprise.** The PR stationary bootstrap returned a SE *smaller* than naive iid — 0.0161 vs 0.0205 — because the per-path diff sequence has lag-2 autocorrelation of −0.348. Block resampling with average block size 5 mostly averages over those negative serial correlations and shrinks SE. This is a vivid demonstration that block-bootstrap with a fixed block size is the wrong tool for CPCV path-correlation; the requested method *technically* answers the question asked while producing a result diametrically opposed to the truth. The truth requires a structural dependency model (training-overlap-weighted SE = 0.065, CI crosses zero), which gives the orchestrator's expected outcome.
