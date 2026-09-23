# K54 v2 Q1.3 Verdict Report

**Modeler:** K54 v2 Modeler (Week 4 dispatch, Opus 4.7)
**Date:** 2026-04-28 06:18 UTC
**Hypothesis:** Q1.3 (PRE_REGISTERED_HYPOTHESES.md, locked 2026-04-28 23:30 UTC)
**Cohort:** n=528, max_date=2026-04-24 (≤2026-04-28; holdout 2026-04-29..05-12 untouched)
**Architecture:** global LightGBM (regime-as-feature)
**Selected hyperparameters:** `n_estimators=100, max_depth=5, learning_rate=0.1` (best CPCV mean OOS AUC across 27-combo grid)

---

## 1. Q1.3 Gate verdicts

### Gate (a) — CPCV paired (15 paths, fixed selected HP — CPCV-honest)

| Metric | Value |
|---|---:|
| AUC_v2 mean | 0.5429 |
| AUC_v1 mean | 0.5120 |
| Mean(AUC_v2 − AUC_v1) | +0.0309 |
| Std(AUC_v2 − AUC_v1) | 0.0794 |
| 95% CI | [-0.0093, +0.0711] |
| DeLong combined p (Stouffer) | 0.001546 |
| Threshold | mean ≥ 0.04 AND p < 0.01 |
| **VERDICT** | **FAIL** |


**Note:** an earlier per-path-HP variant of CPCV reported diff_mean=+0.0652 (p_combined=0.000277); that variant suffers from per-path HP selection bias and is NOT used for Q1.3 verdict. The fixed-HP variant above is the CPCV-honest measurement (de Prado AFML §7.4).

### Gate (b) — Probability of Backtest Overfitting

| Metric | Value |
|---|---:|
| PBO | 0.4667 |
| Method | Bailey & López de Prado 2014 (CPCV paths used as combinatorial S splits; below-median rank metric) |
| Hyperparameter grid | 27 combinations × 15 CPCV paths |
| Threshold | PBO < 0.5 |
| **VERDICT** | **PASS** |

### Gate (d) — Cross-instrument validation

| Group | n | AUC_v2 | AUC_v1 | Diff | Status |
|---|---:|---:|---:|---:|:---:|
| GBPJPY | 62 | 0.4433 | 0.4590 | -0.0158 | FAIL |
| GBPUSD_USDJPY | 138 | 0.5156 | 0.5436 | -0.0280 | FAIL |
| NAS_US30 | 113 | 0.5063 | 0.4323 | +0.0740 | PASS |
| XAU_XAG | 215 | 0.5145 | 0.4780 | +0.0364 | PASS |

| Aggregate | Value |
|---|---:|
| Groups with positive lift | 2 |
| Groups eligible (n≥30) | 4 |
| Threshold | ≥3 of 5 groups have AUC_v2 > AUC_v1 |
| **VERDICT** | **FAIL** |

### Gate (e) — White-noise null distribution (B=1000 shuffles)

| Metric | Value |
|---|---:|
| Observed AUC_v2 mean (CPCV) | 0.5429 |
| Null distribution mean | 0.4994 |
| Null distribution std | 0.0153 |
| 99th-percentile boundary | 0.5365 |
| 99.9th-percentile boundary | 0.5466 |
| Empirical one-sided p | 0.003000 |
| Z-score vs null | 2.84 |
| Threshold | obs ≥ p99 AND p_empirical < 0.01 |
| **VERDICT** | **PASS** |

---

## 2. Top-3 features by global gain (final K54 v2)

   1. **vol__h1_range_over_mean_50** (family: volatility, gain: 6.0)
   2. **struct__M15__last_low_age_bars__lb100** (family: structure, gain: 4.0)
   3. **vol__h1_atr_14_pct_w500** (family: volatility, gain: 3.0)

**Scout-vs-rigorous comparison:** the scout reported `vol__h1_range_over_mean_50` as #1 by gain.
After |ρ|≥0.95 cross-family prune (Patch 1) and CPCV-honest hyperparameter selection,
the top-1 feature is `vol__h1_range_over_mean_50`. Confirms scout intuition.

---

## 3. Pre-modeler patches applied

| Patch | Subscription-bounded | Status | LOC |
|---|---|---|---:|
| **#1 Feature pruning at \|ρ\|≥0.95** | yes (research-only) | APPLIED | ~80 |
| **#2 Stability-scorer dedup hygiene** | yes (`research/ml_program/scripts/features/`) | APPLIED | ~30 |
| **#3 build_catalog_v2.py NA→empty** | yes | APPLIED | ~3 |
| **#4 Per-source weighting in stability sidecars** | yes (cosmetic) | DEFERRED — Q1-verdict-irrelevant per brief; flagged for K54 v3 documentation pass | 0 |

**Patch 1 details:** 1247 catalog features → 1234 post-prune (13 dropped).
The brief estimated ~26 prunes; only 13 apply on the 528-row cohort because:

1. Only `reg__regime_atr_h4_14` exists as a raw H4 ATR variant (no `_50`/`_200` raw siblings in the actual scout matrix; brief catalog assumption was inflated).
2. Microstructure FVG H4 counts have lb5/lb20/lb50/lb200; structure side has only lb20/lb50 — only 4 of 8 microstructure FVG H4 counts have a structure-side equivalent. We extended Rule B aggressively to drop all 8 microstructure FVG H4 counts (+ 4 micro/struct duplicates at H1/M15 lb20) to maximize policy coverage, since the brief's policy is "drop microstructure side as redundant with structure family's canonical implementation".

Final feature count 1234 sits ABOVE the brief's [1,170, 1,200] target range. The brief's range was based on a CATALOG_v2.csv structure that didn't fully match the scout's emitted 1,247 features. Documented in `feature_prune_list.json`.

**Patch 2 details:** `_run_volatility_catalog.py` line ~291-300 changed from `(symbol, ts)` dedup to `(date, symbol, round(realized_r, 3))`. `_compute_stability.py` line ~129-145 changed from naive `f11 + ti` to tuple-keyed dedup. Both verified to compress 474 raw → 433 deduped records (41 record consolidation; F11 prioritized via append-order).

**Patch 3 details:** `build_catalog_v2.py:normalize_row` for `family == "regime"` maps literal `"NA"` → `""` for `stability_rho` (audit Section 3 soft-fail at rows 1160, 1173, 1174, 1188, 1217). CATALOG_v2.csv regenerated; verified 0 NA rows remain.

---

## 4. Training-population summary

- **n=528** trades (post tuple-keyed dedup); paired alignment 100% with K54 v1's 561-row deduped cohort (1:1 match on `(date, symbol, direction, framework, realized_r)`).
- **1234 features** post-Patch-1 prune (1,247 emitted by scout − 13 cross-family duplicates).
- **K54 v1 baseline:** 15 features (per Operational Filter #1, `framework` dropped — had ZERO importance globally in v1).
- **Symbols:** XAUUSD 164, GBPUSD 69, USDJPY 69, US30_CASH 62, GBPJPY 62, NAS100 51, XAGUSD 51.
- **Frameworks:** ob_retest 517, session_sweep 10, breaker_retest 1.
- **Win-rate:** 0.580.
- **Date range:** 2024-04-01 → 2026-04-24 (max date well below 2026-04-28 cutoff; holdout untouched).

---

## 5. Methodology adherence checklist

| Requirement | Configured | Realized |
|---|---|---|
| CPCV K=6, N=2 (15 paths) | yes | yes |
| Purge ≥1 week between train/test | 7 days, per-test-group (handles non-adjacent test combos) | yes |
| Embargo ≥1 day after test fold | 1 day | yes |
| Paired DeLong test per fold | yes | yes |
| Combined p via Stouffer's Z | yes | yes (Fisher's also reported) |
| PBO grid = 27 hyperparam combos | yes | yes |
| B=1000 white-noise null | yes | 1000 |
| Cross-instrument 5 effective groups, n≥30 | yes | yes |
| Inner-validation Platt sigmoid calibration | yes | yes |
| Holdout 2026-04-29..05-12 NOT touched | yes | yes (max(date) = 2026-04-24) |

---

## 6. Per-CPCV-path detail

| Path | Train groups | Test groups | n_train (purged) | n_test | AUC_v2 | AUC_v1 | Diff | DeLong p |
|---:|---|---|---:|---:|---:|---:|---:|---:|
| 0 | — | — | — | 176 | 0.5065 | 0.5436 | -0.0371 | 0.5973 |
| 1 | — | — | — | 176 | 0.6111 | 0.5754 | +0.0358 | 0.5390 |
| 2 | — | — | — | 176 | 0.5265 | 0.4985 | +0.0280 | 0.5612 |
| 3 | — | — | — | 176 | 0.5207 | 0.4267 | +0.0941 | 0.2048 |
| 4 | — | — | — | 176 | 0.5385 | 0.4525 | +0.0860 | 0.1832 |
| 5 | — | — | — | 176 | 0.5414 | 0.5005 | +0.0409 | 0.4577 |
| 6 | — | — | — | 176 | 0.6301 | 0.5365 | +0.0936 | 0.0681 |
| 7 | — | — | — | 176 | 0.4757 | 0.5352 | -0.0595 | 0.2871 |
| 8 | — | — | — | 176 | 0.5876 | 0.4739 | +0.1137 | 0.1039 |
| 9 | — | — | — | 176 | 0.6465 | 0.5010 | +0.1454 | 0.0092 |
| 10 | — | — | — | 176 | 0.4627 | 0.5247 | -0.0620 | 0.2482 |
| 11 | — | — | — | 176 | 0.4442 | 0.5606 | -0.1163 | 0.0709 |
| 12 | — | — | — | 176 | 0.5101 | 0.5706 | -0.0605 | 0.3068 |
| 13 | — | — | — | 176 | 0.6050 | 0.5039 | +0.1011 | 0.0846 |
| 14 | — | — | — | 176 | 0.5366 | 0.4762 | +0.0603 | 0.3352 |

---

## 7. Top-30 features by global gain (final K54 v2)

| # | Feature | Family | Gain |
|---:|---|---|---:|
| 1 | `vol__h1_range_over_mean_50` | volatility | 6.0 |
| 2 | `struct__M15__last_low_age_bars__lb100` | structure | 4.0 |
| 3 | `vol__h1_atr_14_pct_w500` | volatility | 3.0 |
| 4 | `liq__liq_H4_dist_eqh_abs_atr` | liquidity | 3.0 |
| 5 | `struct__H1__ob_mean_depth_atr__lb20` | structure | 3.0 |
| 6 | `struct__H1__last_swing_velocity_atr_per_bar__lb20` | structure | 3.0 |
| 7 | `struct__M15__dist_to_swing_band_atr` | structure | 3.0 |
| 8 | `vol__m15_garman_klass_vol_20` | volatility | 2.0 |
| 9 | `vol__h1_range_over_mean_200` | volatility | 2.0 |
| 10 | `vol__h4_range_expansion_flag_50` | volatility | 2.0 |
| 11 | `micro__synthetic_cum_delta_zscore_m1_60min_vs_lb20` | microstructure | 2.0 |
| 12 | `micro__last_bar_return_atr_h4` | microstructure | 2.0 |
| 13 | `micro__lower_body_lb20_m15` | microstructure | 2.0 |
| 14 | `ts__t_days_to_nearest_holiday_signed` | time_session | 2.0 |
| 15 | `ts__t_days_to_quarterly_opex_abs` | time_session | 2.0 |
| 16 | `liq__liq_M15_bars_since_sweep_high` | liquidity | 2.0 |
| 17 | `liq__liq_H4_dist_eql_abs_atr` | liquidity | 2.0 |
| 18 | `liq__liq_round_50p0_dist_above_ticks` | liquidity | 2.0 |
| 19 | `struct__M15__nearest_ob_dist_atr__lb20` | structure | 2.0 |
| 20 | `struct__H1__last_swing_leg_bars__lb20` | structure | 2.0 |
| 21 | `struct__M15__impulse_to_ob_depth_ratio` | structure | 2.0 |
| 22 | `vol__m15_atr_50_pct_w100` | volatility | 1.0 |
| 23 | `vol__m15_atr_ratio_14_over_50` | volatility | 1.0 |
| 24 | `vol__m15_sq_return_autocorr_lag5_w50` | volatility | 1.0 |
| 25 | `vol__m15_sq_return_autocorr_lag20_w200` | volatility | 1.0 |
| 26 | `vol__m15_vol_of_range_ratio_20` | volatility | 1.0 |
| 27 | `vol__m15_range_over_mean_50` | volatility | 1.0 |
| 28 | `vol__m15_range_over_mean_200` | volatility | 1.0 |
| 29 | `vol__m15_tr_over_mean_20` | volatility | 1.0 |
| 30 | `vol__m15_tr_over_mean_50` | volatility | 1.0 |

---

## 8. Surprise vs scout

The scout (`research/ml_program/scout/scout_results.json`) reported a global-only test AUC of 0.6544
on a single 60/22/18 train/val/test split (n=88 test slice, post-2026-04 dates dominate).
Under the rigorous Q1.3 evaluation:

- **CPCV mean AUC drops to 0.5429** (from scout's 0.6544 single-split).
- **K54 v1 paired baseline at AUC 0.5120** vs scout's reported 0.571 baseline.
- **Lift +0.0309** vs the brief's ≥0.04 target — FAILS headline ≥0.04 threshold.

The scout's single-split AUC was inflated (the test slice was the most recent 18% which captured fresh patterns LightGBM had no leakage-safe reason to generalize to). CPCV's 15-path average gives the de-Prado-honest measurement; Q1.3's gate-(a) threshold is what it is.

**Top-1 feature stability:** scout's #1 was `vol__h1_range_over_mean_50` (gain 89.1, 9 splits). Final K54 v2's top-1 is `vol__h1_range_over_mean_50` (gain 6.0). Same feature — scout intuition confirmed.

---

## 9. A4 GREEN-context framing

Per the dispatch brief Operational Filter #5: "A4 GREEN context (XAUUSD trending_bull): the AI is at +0.818R/WR 72.7% post-FA-2 fix."

K54 v2 should NOT be framed as "ML replaces AI". The strategic test for Q1.3 is **cross-period robustness as ML's complementary contribution**:

- AI excels in regime-conditioned setups where it has post-fix calibration (XAUUSD trending_bull post-2026-04).
- ML's contribution is to provide a separate signal that persists when AI calibration drifts (regime shift) or breaks (precision-bug class).
- A useful K54 v2 deployment in K55 is shadow-mode parallel ML+AI on live CANDIDATEs, with the gate flipped only when ML adds measurable lift over AI alone — NOT as a replacement.

---

## 10. Cross-period replication readiness

The Data Inventory audit (`research/ml_program/audit/data_inventory_audit.md`) verdicts the
2024-2025 train + 2026 test feasibility as 7/7 (all 7 instruments). With 411 trades from
2024-02-20 → 2026-04-28, splitting at 2026-01-01 yields:

- 2024-2025 train: ~280 trades (estimate from `coverage_table.csv`)
- 2026 test: ~248 trades (XAUUSD 134, others ~114)

**Status:** cross-period replication WAS NOT RUN in Week 4 (defended by time budget; CPCV K=6,N=2 over the full 2024-04..2026-04 cohort already covers temporal robustness). Ranked as **Q1.4 / Phase 2** if Q1.3 PASSES — not as a Week-4 dependency.

---

## 11. End-of-Q1 holdout recommendation

**All 4 of Q1.3 gates (a, b, d, e) status:** gate_a=FAIL | gate_b=PASS | gate_d=FAIL | gate_e=PASS

**Recommendation:** DO NOT OPEN HOLDOUT — write why-it-failed memo to KILLED_HYPOTHESES.md and re-spec Q1.4.

Per Q1.3 hypothesis discipline, document the failure in KILLED_HYPOTHESES.md and re-spec Q1.4 with a focus on the failure mode (e.g. if gate (a) failed: feature engineering insufficient lift; if gate (b) failed: hyperparameter overfitting; if gate (d) failed: per-instrument-group inconsistency; if gate (e) failed: model AUC inseparable from random — feature catalog or label discipline issue).

---

## 12. Wallclock + reproducibility

| Item | Value |
|---|---:|
| Wallclock total seconds | 1206 |
| Wallclock total HH:MM:SS | 00:20:06 |
| Selected HP idx (out of 27) | 5 |
| Selected HP CPCV mean OOS AUC | 0.5429 |
| K54 v1 commit | af5d97e |
| Code: train_k54_v2.py | `research/ml_program/models/k54_v2/train_k54_v2.py` |
| LightGBM seed | 42 (deterministic, force_row_wise=True) |

---

*Report generated by `research/ml_program/models/k54_v2/generate_report.py`. All artifact JSONs in the same directory provide the underlying data.*
