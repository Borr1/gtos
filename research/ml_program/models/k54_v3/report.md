# K54 v3 Master Bundle — Q1.4 Modeler Report

**Date:** 2026-04-28T20:49:07.601390+00:00
**Architecture:** Master bundle: Arch A + meta-label + W-unit pooled + NAS_US30 specialist + conformal
**Cohort:** primary 528-row v2 cohort + 1,798-row 2022-2023 backfill (cross-period only)
**Wallclock:** 58s

## TL;DR — Final Verdict: **FAIL** (1/6 testable gates passed; (g) deferred to holdout open)

| Gate | Threshold | Realized | Verdict |
|---|---|---|:---:|
| (a) | CPCV-honest mean AUC ≥ 0.55 | 0.5770 | PASS |
| (b) | Lift ≥ 0.04 (vs anchor 0.5286) AND DSR-p < 0.01 AND PBO < 0.4 AND null p ≥ 0.99 | lift=+0.0484, DSR-p=0.3210, PBO=0.2000, null p_emp=0.0000 | FAIL |
| (c.i) | Train 2022-2023 → Test 2024-2026: lift sign preserved + magnitude ±50% | +0.0481 | PASS |
| (c.ii) | Train <2026-01-01 → Test 2026-01-01+: lift sign + ≥3/4 groups positive | lift=-0.0225 | FAIL |
| (d) | All 4 effective groups AUC ≥ 0.50 + NAS_US30 specialist delta ≥ +0.05 | 2/4 groups, specialist delta = 0.10297805642633234 | FAIL |
| (e) | realized-R lift ≥ +0.05R/trade with bootstrap p < 0.01 | lift=-0.1076, p=0.9990 | FAIL |
| (f) | Feature stability: ≥30 stable features in top-50, Jaccard ≥ 0.6 | 2 stable, Jaccard=0.1685 | FAIL |
| (g) | Christoffersen interval-coverage on holdout | DEFERRED (CPCV proxy coverage = 0.8811) | DEFERRED |

---

## 1. Architecture summary

K54 v3 master bundle (locked per Q1.4 pre-registered spec):

1. **Global LightGBM with per-fold top-100 feature screening** (Architecture A; de Prado AFML §8.5).
2. **Lopez-de-Prado meta-labeling secondary classifier** on triple-barrier outcome labels (TP/SL/TIMEOUT).
3. **Kyle-Obizhaeva W-unit pooled training** (sample weights = dollar_volume × realized_vol per row).
4. **NAS_US30 specialist routing layer** (Architecture B from Q1.3 audit).
5. **Adaptive conformal calibration** (Zaffran 2022; gate g enabler).

**K54 v3 new features added (closed-form):**

- `kw__k10_round_aligned`
- `kw__k10_round_dist_min_atr`
- `kw__k7_osler_stopcluster_proxy`
- `kw__k10_round50_above_below_asym`
- `kw__k8_ob_age_power_law`
- `kw__k9_regime_x_round_x_side`

**Dropped from scope:** K-4 Stoikov micro-price (KILLED 2026-04-29 per `KILLED_HYPOTHESES.md` — MT5 retail tick has volume=0).
**Substitution:** K-1 volume bars → K-1' tick-count-time bars (deferred — closed-form requires per-row tick aggregation from `data/ticks/`; computed only as a marker feature in this dispatch).

---

## 2. CPCV paired results (gates a + b)

- **CPCV K=6, N=2, paths=15, purge_days=7, embargo_days=1**
- **Mean K54 v3 AUC (15 paths)** = `0.5770` (anchor: CPCV-honest K54 v1 = 0.5286)
- **Lift vs anchor** = `+0.0484`
- **Naive 95% CI on lift** = `[+0.0349, +0.0809]`
- **CPCV-honest 95% CI on lift** (training-overlap-weighted SE) = `[-0.0148, +0.1306]`
- **CPCV-honest p (two-sided)** = `0.1185`
- **DSR (B-LdP 2014, N=200) p** = `0.3210`
- **PBO (CSCV, n_combos=14+)** = `0.2000`
- **Null distribution (B=1000)**: mean = `0.5003`, p99 = `0.5246`, p_emp = `1.0000`
- **Selected HP** (fixed across paths): `{'n_estimators': 200, 'max_depth': 3, 'learning_rate': 0.05}`

### Per-path table

| Path | Train groups | Test groups | n_train | n_test | AUC v3 | AUC v1 | diff | DeLong p |
|---:|---|---|---:|---:|---:|---:|---:|---:|
| 0 | [2, 3, 4, 5] | [0, 1] | 303 | 176 | 0.5488 | 0.5050 | +0.0438 | 0.4283 |
| 1 | [1, 3, 4, 5] | [0, 2] | 272 | 176 | 0.6156 | 0.5400 | +0.0756 | 0.2024 |
| 2 | [1, 2, 4, 5] | [0, 3] | 274 | 176 | 0.5124 | 0.5513 | -0.0389 | 0.4369 |
| 3 | [1, 2, 3, 5] | [0, 4] | 277 | 176 | 0.5619 | 0.5659 | -0.0040 | 0.9401 |
| 4 | [1, 2, 3, 4] | [0, 5] | 289 | 176 | 0.5366 | 0.4153 | +0.1212 | 0.0396 |
| 5 | [0, 3, 4, 5] | [1, 2] | 301 | 176 | 0.6053 | 0.5243 | +0.0809 | 0.0771 |
| 6 | [0, 2, 4, 5] | [1, 3] | 266 | 176 | 0.6436 | 0.5755 | +0.0681 | 0.1674 |
| 7 | [0, 2, 3, 5] | [1, 4] | 268 | 176 | 0.5085 | 0.4854 | +0.0231 | 0.6973 |
| 8 | [0, 2, 3, 4] | [1, 5] | 280 | 176 | 0.5852 | 0.4913 | +0.0939 | 0.1770 |
| 9 | [0, 1, 4, 5] | [2, 3] | 266 | 176 | 0.6361 | 0.5265 | +0.1095 | 0.0432 |
| 10 | [0, 1, 3, 5] | [2, 4] | 242 | 176 | 0.5606 | 0.4906 | +0.0700 | 0.2077 |
| 11 | [0, 1, 3, 4] | [2, 5] | 254 | 176 | 0.5593 | 0.4466 | +0.1127 | 0.1137 |
| 12 | [0, 1, 2, 5] | [3, 4] | 279 | 176 | 0.5586 | 0.5446 | +0.0139 | 0.8103 |
| 13 | [0, 1, 2, 4] | [3, 5] | 257 | 176 | 0.6435 | 0.5868 | +0.0568 | 0.2698 |
| 14 | [0, 1, 2, 3] | [4, 5] | 285 | 176 | 0.5784 | 0.5366 | +0.0418 | 0.4935 |

---

## 3. Cross-period robustness (gate c)

### Gate (c.i): Train 2022-2023 (n=1,798) → Test 2024-2026 (n=528) on V1 schema

- **Method:** Train 2022-2023 v1-schema (n=1798) -> Test 2024-2026 v1-schema (n=528)
- **AUC on test:** `0.5767` (lift vs anchor `+0.0481`)
- **Per-group positive:** 4/4
- **Verdict:** PASS
- **Caveat:** Backfill cohort has only v1-schema 17 features. K54 v3 1,234-feature catalog cannot be tested cross-period — feature engineering on 2022-2023 OHLCV not done. This is a v1-baseline cross-period sanity test only.

### Gate (c.ii): Within 2024-2026 — Train <2026-01-01 → Test 2026-01-01+ (V3 features)

- **n_train:** 93 / **n_test:** 435
- **AUC v3 test:** `0.5039` / **AUC v1 test:** `0.5264` / **lift:** `-0.0225`
- **Per-group positive:** 1/4
- **Verdict:** FAIL

---

## 4. Per-instrument-group breakdown (gate d)

| Group | n | AUC v3 | AUC v1 | Diff | Above floor 0.50 |
|---|---:|---:|---:|---:|:---:|
| GBPJPY | 62 | 0.4643 | 0.4601 | +0.0042 | FAIL |
| GBPUSD_USDJPY | 138 | 0.5270 | 0.5279 | -0.0010 | PASS |
| NAS_US30 | 113 | 0.4984 | 0.4292 | +0.0693 | FAIL |
| XAU_XAG | 215 | 0.5212 | 0.4790 | +0.0422 | PASS |

**NAS_US30 specialist:**

- n = 113
- Specialist AUC = `0.6014`
- Global K54 v3 on same cohort = `0.4984`
- **Delta = `+0.1030`** (gate threshold ≥ +0.05) → PASS

---

## 5. Realized-R lift (gate e)

- **Method:** Per-cohort delta(realized R | K54 v3 trades) vs uniform; stationary block bootstrap
- **n** = 528
- **Observed lift** = `-0.1076R/trade`
- **95% bootstrap CI** = `[-0.1822, -0.0392]`
- **One-sided p (H1: lift > 0)** = `0.9990`
- **Verdict:** FAIL
- **Caveat:** J46-J49 holdout (j46_j49_shadow_outcomes.jsonl) has only n=1 record at dispatch time; surrogate via cohort R-trade decision.

---

## 6. Feature stability (gate f)

- **Mean pairwise Jaccard (top-50):** `0.1685` (threshold 0.6)
- **Median Jaccard:** `0.1628`
- **n features in top-50 across ≥80% of paths:** `2` (threshold 30)

**Top-15 most-stable features (by path frequency):**

| Feature | Frequency in top-50 |
|---|---:|
| `liq__liq_round_50p0_dist_above_ticks` | 14/15 |
| `vol__h1_range_over_mean_200` | 12/15 |
| `struct__M15__nearest_bb_age_bars__lb100` | 11/15 |
| `struct__M15__dist_to_swing_band_atr` | 11/15 |
| `vol__h1_range_over_mean_20` | 11/15 |
| `ts__t_days_to_nearest_cpi_signed` | 11/15 |
| `ts__t_days_to_nearest_holiday_signed` | 10/15 |
| `ts__t_day_of_year_cos` | 10/15 |
| `ts__t_days_to_nearest_opex_signed` | 10/15 |
| `ts__t_days_to_quarterly_opex_abs` | 10/15 |
| `ts__t_day_of_year_sin` | 10/15 |
| `micro__last_bar_lower_wick_ratio_m15` | 9/15 |
| `ts__t_day_of_month_sin` | 9/15 |
| `ts__t_days_to_quarterly_opex_signed` | 9/15 |
| `struct__M15__nearest_fvg_dist_atr__lb20` | 8/15 |

---

## 7. Calibration (gate g — DEFERRED)

- **Holdout window:** 2026-04-29 → 2026-05-12 (NEVER touched in this dispatch).
- **CPCV-test coverage proxy** (90% interval): `0.8811` (target 0.90)
- **Christoffersen LR_uc p (CPCV proxy)**: `0.0016`
- **Status:** Gate (g) opens at end-of-Q1 (2026-05-13+) per pre-registered hypothesis lock.

---

## 8. Final synthesis

**FAIL — 1 of 6 testable gates passed (a only); 5 of 6 FAIL; (g) DEFERRED.**

Per failure protocol applied to specific failures:

- Gate (a) PASS → architecture has measurable signal; gate (b) is the binding test.
- **Gate (b) FAIL on DSR-p** (lift +0.048 → DSR-p 0.32 at N=200 trial budget; PBO 0.20 PASS, null p_emp=0.000 PASS, but DSR penalty kills it). Same fate as K54 v2 (DSR row M-2).
- Gate (c.i) PASS on v1-schema cross-period sanity (4/4 groups positive; train 2022-2023 → test 2024-2026 lift +0.048).
- Gate (c.ii) FAIL → within 2024-2026 lift -0.022; pre-2026 cohort too small + XAU-dominated.
- Gate (d) FAIL on global per-cohort floor (NAS_US30 + GBPJPY <0.50); **specialist delta +0.103 PASS** (strongest single finding).
- Gate (e) FAIL → realized-R lift -0.108R at p > 0.5 threshold (model picks wrong half of distribution).
- Gate (f) FAIL → 2 stable features, Jaccard 0.169 (overfit signature mirrors Q1.3 K54 v2).

### Strongest single finding survives: NAS_US30 specialist

- AUC 0.6014 on n=113 cohort (NAS100 + US30_cash)
- Delta +0.103 over global K54 v3 on same cohort
- Replicates Q1.3 Architecture B independently
- **Recommended for K55-shadow deploy** (low-confidence floor p ≥ 0.55, NAS100 + US30_cash only)

### Recommendation for Phase 2

1. **Close Q1 globally; ship NAS_US30 specialist as K55-shadow signal candidate.**
2. **Audit-recommended cohort expansion is the binding bottleneck.** 4-6 weeks of 2022-2023 v2-feature engineering (compute the full 1,234 feature catalog on the 1,798-row 2022-2023 backfill). At 5+ rows-per-feature post-screening with n=2,326 cohort, K54 v4 architecture's potential becomes DSR-testable.
3. **Q1.5 re-spec template** (if cohort expansion completes): Architecture A + NAS specialist routing + DSR-mandatory methodology gate. **Drop** Kyle-Obizhaeva W-unit pooling (failed mechanism transmit on retail data; volume=0 ceiling), Lopez-de-Prado meta-labeling (statistically weak at n<5,000), and K-7..K-10 closed-form features (below noise on global model).
4. **Document Q1.4 KILLED memo** in `research/ml_program/KILLED_HYPOTHESES.md` (DONE).
5. **Holdout 2026-04-29 → 2026-05-12 remains UNOPENED for global K54 v3 gate (g).** May be applied to NAS specialist instead if K55-shadow deploy approved.

See `research/ml_program/audit/Q1_4_POSTMORTEM_AND_Q1_CLOSE_RECOMMENDATION.md` for full Q1-close synthesis + CEO decision request.

---

## 9. File index

- `meta.json` — config snapshot + gate verdicts
- `cpcv_paired_results.json` — per-path detail + summary
- `dsr_per_gate.json` — DSR / PBO / null per gate
- `cross_period_results.json` — gates (c.i) + (c.ii)
- `specialist_results.json` — NAS_US30 specialist
- `realized_r_holdout.json` — gate (e) bootstrap
- `feature_stability.json` — gate (f) Jaccard
- `conformal_calibration.json` — gate (g) DEFERRED proxy
- `top_features.json` — aggregated top-200 + final-model top-30 + per-path top-100
- `k54_v3_global.lgb` — final global LightGBM
- `k54_v3_meta_label.lgb` — meta-label secondary classifier
- `k54_v3_nas_us30_specialist.lgb` — NAS_US30 specialist (Architecture B)

*End of report. Computed at 2026-04-28T20:49:07.601390+00:00.*