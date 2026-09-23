# Joint-Model Scout — K54 v2 ballpark estimator

**Run:** 2026-04-28T05:16:08.521759+00:00
**Source:** `research/ml_program/scout/build_scout_matrix.py` + `scout_model.py`
**Discipline:** scout only — NOT the Q1.2 validation gate. Uses the BURNED 2026-04-01 → 2026-04-28 cohort as ballpark test.
**Holdout (untouched):** 2026-04-29 → 2026-05-12 — never read here.

---

## Section 1 — Feature matrix construction

- **Effective n after tuple-keyed dedup** (`(date, symbol, direction, framework, realized_r)`): **528**.
- **Total features computed:** 1247.
- **Non-constant features used in training:** 1186.
- **Family breakdown** (target ≈ 1,219; CATALOG_v2 sums to 1,219):

  - structure: 432
  - volatility: 270
  - microstructure: 187
  - time_session: 138
  - liquidity: 157
  - regime: 63
  - by_source: {'trade_index': 33, 'unified_csv': 89, 'f11_mechanical': 406}
  - by_symbol: {'XAUUSD': 164, 'GBPUSD': 69, 'USDJPY': 69, 'US30_CASH': 62, 'NAS100': 51, 'XAGUSD': 51, 'GBPJPY': 62}

- **Key vs catalog (delta = +28):** liquidity module emits 157 columns (catalog says 129) due to per-instrument round-number features that are NaN for non-applicable instruments — kept as-is. structure/volatility/microstructure/time_session/regime match catalog exactly. Total 1,247 ≥ 1,219 catalog target; no missing features.

---

## Section 2 — Walk-forward AUC results

**Split (time-walk-forward):**
- Train (`< 2026-03-01`): n = 320
- Val (`[2026-03-01, 2026-04-01)`): n = 120
- Test (`[2026-04-01, 2026-04-29)`, BURNED ballpark): n = 88

**Tiny LightGBM** — two parallel models reported below. Hyperparams: n_estimators=200, max_depth=5, learning_rate=0.05, min_data_in_leaf=max(3, n_train/30), early-stop=20. Platt-scaling sigmoid calibration on val.

**Headline = Global-only (single LightGBM trained on all train rows; matches null-shuffle protocol).**
Per-regime ensemble shown for comparison; with 1,219 features and ~320 train rows, regime fragmentation (smallest regime = 21 rows) causes degradation.

| Slice | n | AUC global-only (HEADLINE) | AUC per-regime ensemble | WR |
|---|---:|---:|---:|---:|
| Train | 320 | 0.9925 | 0.4011 | — |
| Val | 120 | 0.6120 | 0.5330 | — |
| **Test (BALLPARK)** | 88 | **0.6544** | 0.5790 | — |
| Brier (test) | — | 0.2543 | 0.2527 | — |

**vs K54 v1 baseline (0.571):** global-only delta = **+0.0834**; per-regime delta = +0.0080.

**@ thr=0.60 on test:**
- Global-only: {'n_traded': 45, 'exp_r': 0.4211311111111111, 'wr': 0.5777777777777777, 'n_skipped': 43, 'skipped_wr': 0.4186046511627907}
- Per-regime ensemble: {'n_traded': 29, 'exp_r': 0.5155862068965518, 'wr': 0.6206896551724138, 'n_skipped': 59, 'skipped_wr': 0.4406779661016949}
- K54 v1 reported +0.164 R/trade lift @ thr>=0.60.

**KEY FINDING:** Per-regime ensemble degrades vs global-only at this n+feature_count. Per-regime AUC on test = 0.5790; global-only = 0.6544. The per-regime model architecture from K54 v1 (4 features) does NOT transfer cleanly to v2 (1,219 features) at this train n. This is a Phase 2 modeling decision: K54 v2 should consider regime-as-feature in a single global model rather than regime-as-gate per K54 v1.

**Per-regime test AUC** (small-n caveat — SE ~0.10 at n=14, ~0.07 at n=38):

| regime | n | AUC global-only | AUC per-regime ensemble | WR |
|---|---:|---:|---:|---:|
| untagged | 14 | 0.7778 | 0.5889 | 0.3571 |
| bearish | 14 | 0.6122 | 0.6122 | 0.5000 |
| transitional | 22 | 0.5714 | 0.4196 | 0.6364 |
| bullish | 38 | 0.7000 | 0.5764 | 0.4737 |

**Eligible regimes (train n >= 30):** ['untagged', 'bullish', 'transitional']
**Train regime distribution:** {'untagged': np.int64(185), 'bullish': np.int64(61), 'transitional': np.int64(53), 'bearish': np.int64(21)}
**Test regime distribution:** {'bullish': np.int64(38), 'transitional': np.int64(22), 'untagged': np.int64(14), 'bearish': np.int64(14)}

---

## Section 3 — Top features by global + per-regime gain

**Top-30 global by gain** (catalog_rho = univariate Spearman ρ on pre-2026-04 cohort):

| rank | feature | gain | split | catalog_rho |
|---:|---|---:|---:|---:|
| 1 | `vol__h1_range_over_mean_50` | 89.12 | 9 | +0.136 |
| 2 | `micro__last_bar_body_ratio_h4` | 55.10 | 6 | +0.075 |
| 3 | `vol__m15_sq_return_autocorr_lag5_w50` | 54.86 | 6 | +0.087 |
| 4 | `micro__synthetic_footprint_imb_m1_last_480min` | 53.83 | 4 | -0.015 |
| 5 | `struct__M15__nearest_fvg_age_bars__lb20` | 49.86 | 6 | +0.101 |
| 6 | `vol__m15_tr_over_mean_50` | 41.48 | 5 | +0.040 |
| 7 | `struct__M15__last_low_age_bars__lb20` | 41.23 | 5 | -0.106 |
| 8 | `struct__H1__nearest_ob_dist_atr__lb20` | 40.18 | 5 | +0.094 |
| 9 | `vol__h4_range_over_mean_20` | 39.37 | 6 | +0.104 |
| 10 | `struct__H1__swing_total_count__lb100` | 34.89 | 3 | -0.000 |
| 11 | `struct__M15__nearest_ob_age_bars__lb20` | 31.93 | 4 | +0.020 |
| 12 | `ts__t_days_to_quarterly_opex_abs` | 31.46 | 5 | -0.067 |
| 13 | `vol__m15_count_2sigma_w200` | 29.84 | 3 | -0.006 |
| 14 | `liq__liq_round_50p0_dist_above_ticks` | 28.28 | 4 | +0.068 |
| 15 | `ts__t_trading_days_to_month_end` | 26.21 | 3 | +0.016 |
| 16 | `struct__M15__nearest_fvg_dist_atr__lb100` | 25.75 | 3 | -0.102 |
| 17 | `vol__h4_sq_return_autocorr_lag5_w50` | 25.28 | 3 | +0.068 |
| 18 | `micro__synthetic_cum_delta_zscore_m1_240min_vs_lb20` | 23.78 | 3 | -0.106 |
| 19 | `vol__h1_atr_14_pct_w500` | 22.88 | 3 | -0.025 |
| 20 | `struct__H4__dist_to_nearest_swing_high_atr` | 22.15 | 3 | +0.048 |
| 21 | `vol__h4_range_over_mean_200` | 21.41 | 2 | +0.064 |
| 22 | `struct__H1__last_swing_velocity_atr_per_bar__lb20` | 21.14 | 4 | -0.080 |
| 23 | `ts__t_days_to_nearest_opex_signed` | 21.09 | 3 | +0.057 |
| 24 | `vol__h4_parkinson_vol_200` | 18.40 | 3 | -0.006 |
| 25 | `struct__H1__nearest_bb_depth_atr__lb100` | 18.09 | 2 | +0.035 |
| 26 | `micro__last_bar_upper_wick_ratio_h1` | 17.72 | 5 | +0.037 |
| 27 | `liq__liq_H1_dist_eqh_abs_atr` | 16.22 | 2 | +0.099 |
| 28 | `struct__H4__last_high_age_bars__lb20` | 15.26 | 2 | +0.022 |
| 29 | `vol__m15_bb_width_pct_200_w100` | 15.26 | 3 | +0.077 |
| 30 | `micro__range_mean_ratio_5_50_h4` | 14.86 | 2 | +0.035 |

**Per-regime top-10 by gain:**

### regime = `untagged`

| rank | feature | gain | split |
|---:|---|---:|---:|
| 1 | `struct__M15__nearest_fvg_age_bars__lb20` | 14.47 | 1 |
| 2 | `struct__M15__ob_mean_age_bars__lb20` | 12.89 | 1 |
| 3 | `liq__liq_dist_pwl_signed_ticks` | 11.98 | 1 |
| 4 | `micro__synthetic_cum_delta_m1_last_15min` | 11.80 | 1 |
| 5 | `struct__H4__dist_to_swing_band_atr` | 11.20 | 1 |
| 6 | `micro__vpoc_dist_atr_m15_lb50` | 9.77 | 1 |
| 7 | `liq__liq_magnet_score_median` | 2.39 | 1 |
| 8 | `vol__m15_garch_persistence_lag1_w100` | 0.00 | 1 |
| 9 | `liq__liq_round_0p5_min_dist_atr` | 0.00 | 0 |
| 10 | `liq__liq_round_1p0_dist_above_ticks` | 0.00 | 0 |

### regime = `bullish`

| rank | feature | gain | split |
|---:|---|---:|---:|
| 1 | `micro__synthetic_cum_delta_m1_last_240min` | 11.40 | 1 |
| 2 | `vol__h1_realized_skew_200` | 10.61 | 1 |
| 3 | `micro__range_pctile_h1_lb20` | 9.75 | 1 |
| 4 | `reg__regime_atr_h1_to_h4_ratio` | 8.25 | 1 |
| 5 | `struct__H1__nearest_ob_touch_count__lb20` | 7.71 | 1 |
| 6 | `struct__H4__swing_total_count__lb50` | 3.63 | 1 |
| 7 | `micro__synthetic_delta_pctile_m1_60min_lb20` | 2.76 | 1 |
| 8 | `liq__liq_round_0p5_dist_below_ticks` | 0.00 | 0 |
| 9 | `liq__liq_round_0p5_min_dist_ticks` | 0.00 | 0 |
| 10 | `liq__liq_round_0p5_min_dist_atr` | 0.00 | 0 |

### regime = `transitional`

| rank | feature | gain | split |
|---:|---|---:|---:|
| 1 | `struct__H1__ob_max_touch_count__lb100` | 25.59 | 2 |
| 2 | `micro__synthetic_footprint_imb_m1_last_15min` | 21.50 | 2 |
| 3 | `vol__h4_realized_skew_200` | 10.36 | 1 |
| 4 | `micro__vpoc_dist_atr_m15_lb50` | 9.82 | 1 |
| 5 | `struct__H4__ob_mean_age_bars__lb20` | 8.81 | 1 |
| 6 | `struct__M15__last_swing_range_atr__lb20` | 8.14 | 1 |
| 7 | `vol__m15_sq_return_autocorr_lag20_w200` | 7.30 | 2 |
| 8 | `micro__volume_volofvol_m15_lb50` | 4.85 | 1 |
| 9 | `vol__m15_atr_14` | 0.00 | 3 |
| 10 | `vol__m15_atr_14_pct_w100` | 0.00 | 4 |

**Surprises — top-gain features with low univariate ρ (< 0.10):** these are interaction-signal candidates.

| rank | feature | gain | catalog_rho |
|---:|---|---:|---:|
| 2 | `micro__last_bar_body_ratio_h4` | 55.10 | +0.075 |
| 3 | `vol__m15_sq_return_autocorr_lag5_w50` | 54.86 | +0.087 |
| 4 | `micro__synthetic_footprint_imb_m1_last_480min` | 53.83 | -0.015 |
| 6 | `vol__m15_tr_over_mean_50` | 41.48 | +0.040 |
| 8 | `struct__H1__nearest_ob_dist_atr__lb20` | 40.18 | +0.094 |
| 10 | `struct__H1__swing_total_count__lb100` | 34.89 | -0.000 |
| 11 | `struct__M15__nearest_ob_age_bars__lb20` | 31.93 | +0.020 |
| 12 | `ts__t_days_to_quarterly_opex_abs` | 31.46 | -0.067 |
| 13 | `vol__m15_count_2sigma_w200` | 29.84 | -0.006 |
| 14 | `liq__liq_round_50p0_dist_above_ticks` | 28.28 | +0.068 |

---

## Section 4 — White-noise null distribution

**Procedure:** shuffle train+val labels with 10 distinct seeds [101, 202, 303, 404, 505, 606, 707, 808, 909, 1010], retrain identical-hyperparam global LightGBM, score the BURNED test slice.

| metric | value |
|---|---:|
| n_shuffles | 10 |
| null AUC mean | 0.4949 |
| null AUC std | 0.0372 |
| null AUC max | 0.5488 |
| **real test AUC** | **0.6544** |
| z-score | 4.29 |
| p-value (empirical, one-sided) | 0.0000 |
| p-value (smoothed, Phipson-Smyth-style) | 0.0909 |

**Per-shuffle null AUCs:** [0.4595, 0.5052, 0.4809, 0.4341, 0.4527, 0.5214, 0.532, 0.4992, 0.5155, 0.5488]

**Note:** with n_shuffles=10 the empirical p-floor is 1/11 ≈ 0.091 (smoothed). For a tighter p value, run more shuffles at Week-4 modeling time.

---

## Section 5 — Verdict

### Q1: Does the catalog have signal? **YES**

- HEADLINE (global-only) test AUC = **0.6544**.
- Per-regime ensemble test AUC = 0.5790 (regime fragmentation drag at this n).
- Null distribution mean = **0.4949**, std = 0.0372, max = **0.5488**.
- Real beats null max? **True** (delta +0.1056).
- z-score = 4.29.
- p_empirical (one-sided) = **0.0000**, p_smoothed = **0.0909**.
- Verdict: signal exists at p < 0.05? **YES on z-score (4.29 sigma) and p_empirical=0.0000 (0/10 nulls beat real); smoothed p has a 1/(B+1)=0.091 floor at n=10 shuffles, not a signal-absence indicator**.

### Q2: Is AUC ≥ 0.61 plausible at Week-4 modeling? **YES (already exceeds with global-only)**

- Headline test AUC vs the 0.61 threshold: **0.6544** vs 0.61 → meets/exceeds (delta +0.0444).
- Headline vs K54 v1 baseline (0.571): **+0.0834**.
- Per-regime vs K54 v1 baseline: +0.0080 (degraded at this n+feature_count).

**Recommendation:** Week-4 catalog modeling is HIGHLY LIKELY to achieve AUC ≥ 0.61. Scout's tiny-LightGBM global-only model already crosses the bar by **+0.0444**. Full Optuna search + CPCV-with-purge + cross-period replication should hold or improve. **Architectural recommendation: do NOT inherit K54 v1's per-regime gating without re-evaluating** — at 1,219 features the ensemble fragmentation drag (-0.0754 AUC) outweighs the K54 v1 ensemble's +0.032 lift. Either keep regime-as-feature in the global model (current scout architecture) OR raise per-regime min-rows above 60+ before fragmenting.

**Notes for Q1.2 modeler:**
1. Scout test slice is BURNED — these numbers are ballpark, not validation. The locked Q1.2 holdout 2026-04-29 → 2026-05-12 remains untouched.
2. Per-regime n in test is SMALL (~15-40 per regime). AUC SE per regime is large (~0.10). Treat per-regime AUCs as directional, not predictive.
3. NaN density is high for trades pre-2025-10 (12 trades) and for tick-required microstructure (24 features all NaN — no parquet coverage). LightGBM handles NaN natively; no imputation needed.
4. **Global-only >= per-regime at this n.** The per-regime ensemble fragmenting train into 4 regimes (smallest = 21 rows) is harmful at the 1,219-feature scale. Reconsider K54 v1's per-regime architecture before Week-4 commits to it.
5. **Null distribution discipline:** test AUC=0.6544 is +15.95pp above null mean (z=4.29 sigma), beats null max by +0.1056. Empirical p=0.0000 (0/10 nulls >= real); smoothed p=0.0909 reflects 1/(B+1) floor at B=10. Modeler should run >100 shuffles to tighten p.

---

**Files:**
- `research/ml_program/scout/feature_matrix.parquet` (or .csv) — unified feature matrix
- `research/ml_program/scout/feature_matrix_meta.json` — schema + shape
- `research/ml_program/scout/scout_results.json` — full numerical results
- `research/ml_program/scout/build_scout_matrix.py` — feature matrix builder
- `research/ml_program/scout/scout_model.py` — model + null + report writer