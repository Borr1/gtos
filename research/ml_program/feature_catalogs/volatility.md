# Volatility Family — Feature Catalog
**Family:** Volatility (greenfield — K54 v1 had ZERO volatility features per audit Section 5).
**Author:** K54 v2 Volatility feature engineer (2026-04-28).
**Feature count:** 270 (target 100-300).
**Data cutoff:** ≤2026-04-28 23:59 UTC. Stability scoring on records pre-2026-04-01.

## Why this family
XAUUSD's documented distributional anomalies — fat-tail GPD index ξ=0.350, GARCH persistence α+β=0.9906 (half-life 73 H1 bars), 6.2× more 3σ events than Gaussian — make volatility regime conditioning a high-leverage axis. K54 v1's ATR is hidden inside `ob_distance_atr` and not exposed as a standalone feature; this family fills the gap.
Reference: `research/diagnostics/distributional_characterization_20260411_012816.json`, `memory/project_distributional_findings.md`.

## Feature blocks (high level)
| Block | Function | Rough count | Notes |
|---|---|---:|---|
| ATR + percentile + ratios | `atr_features` | 12/TF | Wilder ATR over 14/50/200; percentile rank within 100/500-bar window; cross-period ratios. |
| Realized vol + transitions | `realized_vol_features` | 8-15/TF | Rolling stddev of log-returns at 20/50/200; vol-of-vol; regime-transition counts; above-median binary. |
| Vol clustering (GARCH proxy) | `vol_clustering_features` | 8/TF | Rolling autocorr of squared returns at lags 1/5/20 over 50/200-bar windows. |
| Range expansion | `range_expansion_features` | 15/TF | Bar range vs rolling mean/stddev; expansion/contraction binary flags; True Range variants. |
| Bollinger squeeze/expansion | `bollinger_features` | 12/TF | BB-width over 20/50/200, percentile rank, squeeze (≤10th pct) and expansion (≥90th pct) flags. |
| Fat-tail proxies | `fat_tail_features` | 21/TF | Empirical 95th/99th percentile of \|return\|, count of 2σ/3σ events, rolling skew/kurt, tail ratio. |
| Parkinson/Garman-Klass | `hilo_estimators` | 12/TF | Lower-variance vol estimators using OHLC; normalized TR. |
| Intraday hour-of-day profile | `intraday_vol_profile_features` | 3 (M15 only) | Same-hour rolling mean/percentile-rank vol over last 30 days. |

## Top 5 features by absolute stability rho
| Rank | Feature | rho | n | p |
|---:|---|---:|---:|---:|
| 1 | `m15_sq_return_autocorr_lag1_w50` | 0.172 | 406 | 0.000501 |
| 2 | `h1_range_over_mean_20` | 0.1438 | 406 | 0.003681 |
| 3 | `h1_range_over_mean_50` | 0.1357 | 406 | 0.00618 |
| 4 | `h1_tr_over_mean_20` | 0.1356 | 406 | 0.006216 |
| 5 | `h4_range_expansion_flag_50` | 0.1316 | 406 | 0.007926 |

Stability = univariate Spearman correlation of feature value at trade-entry candle close vs realized R, on F11 BOS records + trade index pre-2026-04. Low |rho| does NOT mean unusable — model can still extract signal jointly with other features.

## Multi-timeframe / multi-instrument coverage
- TFs computed: M15 (full feature set incl. intraday profile), H1 (no intraday), H4 (no intraday).
- Instruments: 7 (XAUUSD, GBPUSD, USDJPY, GBPJPY, US30_cash, XAGUSD, NAS100). H4 data for some FX symbols ends 2026-04-03; M15 + H1 cover through 2026-04-17. NAS100/XAGUSD only have data from 2025-10-01 (data/historical_2026/) — flagged as a coverage gap; features that need 200+ bars of warmup will be NaN before ~2025-10-21 for these two.

## Inference cost
- Full multi-TF feature compute: ~1.0s on XAUUSD M15 (48k bars) + H1 (15k) + H4 (4.6k).
- Per-bar evaluation cost is bounded by O(N_max), N_max=500 (longest pct window). Vectorized; ~20μs/bar in steady state. Live evaluation cost negligible vs API call.
- Features flagged `expensive_flag=yes`: rolling autocorr, percentile-rank-w500, realized_kurt — these are O(N log N) at worst (sort within window) but pandas C-level; not blockers.

## Leakage self-check
**1. Rolling computations.** All rolling stats use pandas `rolling(N).fn()`, which at row T uses rows in [T-N+1, T] (current included). The candle that closes at time T is COMPLETE at T (full OHLC known). No `.shift(-k)` and no future-window aggregation appears anywhere in `volatility.py` (verified by `grep -n 'shift(-' volatility.py` returning empty).
**2. Multi-TF stitching.** Multi-TF features are stitched via `pd.merge_asof(..., direction='backward')` so that at M15 candle T, only H1/H4 candles with close_time ≤ T are joined. The most recent H1 candle at M15 13:15 is the H1 candle that closed at 13:00 — correct.
**3. Intraday profile.** Same-hour rolling mean is `.shift(1)` AFTER aggregation, so the current bar's |return| is NOT used to forecast itself. The percentile-rank version is one place where the current bar IS included in its own ranking distribution; this is deliberate (rank within history including self) but documented here.
**4. Sigma-count features.** `count_2sigma` / `count_3sigma` use `std_w` over the SAME rolling window as the |return| comparison, so each row's flag uses sigma derived from past bars only. No future sigma leakage.
**5. Module-level self-test.** `_self_test()` runs on import; verifies that ATR(14) and realized_vol(20) at row 200 match between full-data and truncated-data computations to <1e-9. If these assertions fail, the module fails to import.
**6. F11 BOS-time stability.** Stability scoring uses BOS times from F11 records. These are the M15 candle close times of the BOS event — i.e., the candle is closed at that exact timestamp. Features at that timestamp use rolling stats over PRIOR bars, including the BOS bar itself (which has fully materialized OHLC). No look-ahead beyond the BOS bar.

## Coverage gaps and caveats
- **NAS100 + XAGUSD M15/H1/H4** only available from 2025-10-01 (`data/historical_2026/`). Features needing 200+ bars warmup are NaN before ~2025-10-21 for these. Stability test tolerated this (NaN-masked).
- **H4 USDJPY/GBPJPY/GBPUSD** ends 2026-04-03 (data/historical/). M15 + H1 cover to 2026-04-17, so the H4 stability test for those instruments uses the H4 candle that contains the BOS time, which may be up to 4h stale on the latest BOS.
- **Trade index timestamps** are date-only — snapped to kill-zone hour (london=08, ny=14, tokyo=01). For F11 the bos_time is precise; trade-index/unified records are approximate. Stability rho should be reweighted toward F11 if this matters.
- **Sample size for stability.** Capped at 80 records per symbol → ~520 effective records. Spearman p-values reported are asymptotic; with n=500 and family-wide ~270 features, Bonferroni threshold for α=0.05 is p<1.85e-4. **Treat any single feature's p-value as screening signal only**; CPCV at K54 v2 train time is the real validation.

## How K54 v2 should consume these
- All features are float-valued and bounded (or NaN-masked); no further encoding needed.
- Recommend: feed all features to LightGBM with `is_unbalance=True` and let split-gain select. Bonferroni-significant features should be retained even if low-rho; univariate-zero features may still split well jointly (e.g., `bb_squeeze_flag` × regime).
- Per-regime training (per `project_f15_synthesis_regime_is_load_bearing`): vol features are likely to interact strongly with regime — bullish vs trending vs ranging cells should see different importance rankings.
- Decay watch: re-run stability scoring quarterly. The `count_3sigma` features in particular may have time-varying baselines (regime-conditioned tail incidence).

## Full feature table

| Feature | TF | Lookback | Stability rho | n | p | Expensive |
|---|---|---|---:|---:|---:|---|
| `h1_atr_14` | h1 | 14 | -0.0529 | 406 | 0.287277 | no |
| `h1_atr_14_pct_w100` | h1 | 100 | 0.0273 | 406 | 0.582815 | no |
| `h1_atr_14_pct_w500` | h1 | 500 | -0.0248 | 406 | 0.61876 | yes |
| `h1_atr_200` | h1 | 200 | -0.0563 | 406 | 0.258075 | no |
| `h1_atr_200_pct_w100` | h1 | 100 | -0.0386 | 406 | 0.43779 | no |
| `h1_atr_200_pct_w500` | h1 | 500 | -0.0755 | 406 | 0.129071 | yes |
| `h1_atr_50` | h1 | 50 | -0.0552 | 406 | 0.267244 | no |
| `h1_atr_50_pct_w100` | h1 | 100 | 0.0018 | 406 | 0.970428 | no |
| `h1_atr_50_pct_w500` | h1 | 500 | -0.0642 | 406 | 0.196766 | yes |
| `h1_atr_ratio_14_over_200` | h1 | 200 | -0.0214 | 406 | 0.666732 | no |
| `h1_atr_ratio_14_over_50` | h1 | 50 | 0.017 | 406 | 0.732861 | no |
| `h1_atr_ratio_50_over_200` | h1 | 200 | -0.0507 | 406 | 0.307771 | no |
| `h1_bb_expansion_flag_200_w100` | h1 | 100 | -0.0584 | 406 | 0.240183 | no |
| `h1_bb_expansion_flag_20_w100` | h1 | 100 | 0.0444 | 406 | 0.372021 | no |
| `h1_bb_expansion_flag_50_w100` | h1 | 100 | 0.0468 | 406 | 0.346678 | no |
| `h1_bb_squeeze_flag_200_w100` | h1 | 100 | 0.097 | 406 | 0.050836 | no |
| `h1_bb_squeeze_flag_20_w100` | h1 | 100 | -0.1088 | 406 | 0.02841 | no |
| `h1_bb_squeeze_flag_50_w100` | h1 | 100 | -0.0017 | 406 | 0.972958 | no |
| `h1_bb_width_20` | h1 | 20 | 0.0424 | 406 | 0.394425 | no |
| `h1_bb_width_200` | h1 | 200 | -0.0305 | 406 | 0.539677 | no |
| `h1_bb_width_50` | h1 | 50 | 0.0205 | 406 | 0.680754 | no |
| `h1_bb_width_pct_200_w100` | h1 | 100 | -0.0993 | 406 | 0.045439 | no |
| `h1_bb_width_pct_20_w100` | h1 | 100 | 0.0936 | 406 | 0.059606 | no |
| `h1_bb_width_pct_50_w100` | h1 | 100 | 0.0693 | 406 | 0.163436 | no |
| `h1_count_2sigma_w200` | h1 | 200 | -0.0477 | 406 | 0.33726 | yes |
| `h1_count_2sigma_w50` | h1 | 50 | 0.0431 | 406 | 0.386523 | no |
| `h1_count_2sigma_w500` | h1 | 500 | -0.0621 | 406 | 0.211956 | no |
| `h1_count_3sigma_w200` | h1 | 200 | -0.0098 | 406 | 0.843858 | yes |
| `h1_count_3sigma_w50` | h1 | 50 | 0.023 | 406 | 0.644255 | no |
| `h1_count_3sigma_w500` | h1 | 500 | -0.0676 | 406 | 0.173876 | no |
| `h1_garch_persistence_lag1_w100` | h1 | 100 | -0.0103 | 406 | 0.836459 | no |
| `h1_garch_persistence_lag1_w20` | h1 | 20 | 0.0046 | 406 | 0.92674 | no |
| `h1_garman_klass_vol_20` | h1 | 20 | -0.0075 | 406 | 0.879714 | no |
| `h1_garman_klass_vol_200` | h1 | 200 | -0.0034 | 406 | 0.945071 | no |
| `h1_garman_klass_vol_50` | h1 | 50 | -0.004 | 406 | 0.935913 | no |
| `h1_norm_tr_20` | h1 | 20 | -0.0043 | 406 | 0.93047 | no |
| `h1_norm_tr_200` | h1 | 200 | -0.0056 | 406 | 0.910538 | no |
| `h1_norm_tr_50` | h1 | 50 | -0.0024 | 406 | 0.961709 | no |
| `h1_norm_tr_std_20` | h1 | 20 | 0.0206 | 406 | 0.679725 | no |
| `h1_norm_tr_std_200` | h1 | 200 | -0.009 | 406 | 0.856122 | no |
| `h1_norm_tr_std_50` | h1 | 50 | 0.0043 | 406 | 0.931101 | no |
| `h1_parkinson_vol_20` | h1 | 20 | 0.0002 | 406 | 0.997433 | no |
| `h1_parkinson_vol_200` | h1 | 200 | -0.0067 | 406 | 0.892675 | no |
| `h1_parkinson_vol_50` | h1 | 50 | 0.0015 | 406 | 0.976172 | no |
| `h1_range_contraction_flag_20` | h1 | 20 | -0.0665 | 406 | 0.18089 | no |
| `h1_range_contraction_flag_200` | h1 | 200 | -0.0015 | 406 | 0.976187 | no |
| `h1_range_contraction_flag_50` | h1 | 50 | -0.0068 | 406 | 0.890865 | no |
| `h1_range_expansion_flag_20` | h1 | 20 | 0.0906 | 406 | 0.068215 | no |
| `h1_range_expansion_flag_200` | h1 | 200 | 0.0221 | 406 | 0.657363 | no |
| `h1_range_expansion_flag_50` | h1 | 50 | 0.0747 | 406 | 0.133104 | no |
| `h1_range_over_mean_20` | h1 | 20 | 0.1438 | 406 | 0.003681 | no |
| `h1_range_over_mean_200` | h1 | 200 | 0.1232 | 406 | 0.012992 | no |
| `h1_range_over_mean_50` | h1 | 50 | 0.1357 | 406 | 0.00618 | no |
| `h1_realized_kurt_200` | h1 | 200 | -0.0265 | 406 | 0.594354 | yes |
| `h1_realized_kurt_50` | h1 | 50 | 0.0497 | 406 | 0.31744 | yes |
| `h1_realized_kurt_500` | h1 | 500 | -0.0157 | 406 | 0.753048 | yes |
| `h1_realized_skew_200` | h1 | 200 | -0.001 | 406 | 0.984036 | yes |
| `h1_realized_skew_50` | h1 | 50 | 0.0098 | 406 | 0.844684 | yes |
| `h1_realized_skew_500` | h1 | 500 | -0.0308 | 406 | 0.53638 | yes |
| `h1_realized_vol_20` | h1 | 20 | 0.0146 | 406 | 0.769364 | no |
| `h1_realized_vol_200` | h1 | 200 | -0.0098 | 406 | 0.843862 | no |
| `h1_realized_vol_50` | h1 | 50 | 0.0096 | 406 | 0.847788 | no |
| `h1_return_p95_abs_200` | h1 | 200 | -0.0187 | 406 | 0.707682 | no |
| `h1_return_p95_abs_50` | h1 | 50 | 0.0029 | 406 | 0.953504 | no |
| `h1_return_p95_abs_500` | h1 | 500 | -0.0097 | 406 | 0.844959 | no |
| `h1_return_p99_abs_200` | h1 | 200 | -0.016 | 406 | 0.747914 | no |
| `h1_return_p99_abs_50` | h1 | 50 | 0.0157 | 406 | 0.752699 | no |
| `h1_return_p99_abs_500` | h1 | 500 | -0.0083 | 406 | 0.86774 | no |
| `h1_sq_return_autocorr_lag1_w200` | h1 | 200 | 0.0185 | 406 | 0.710119 | yes |
| `h1_sq_return_autocorr_lag1_w50` | h1 | 50 | -0.0498 | 406 | 0.316617 | yes |
| `h1_sq_return_autocorr_lag20_w200` | h1 | 200 | -0.0007 | 406 | 0.989044 | yes |
| `h1_sq_return_autocorr_lag20_w50` | h1 | 50 | -0.0142 | 406 | 0.775239 | yes |
| `h1_sq_return_autocorr_lag5_w200` | h1 | 200 | 0.0025 | 406 | 0.960657 | yes |
| `h1_sq_return_autocorr_lag5_w50` | h1 | 50 | -0.0262 | 406 | 0.5989 | yes |
| `h1_tail_ratio_99_50_200` | h1 | 200 | -0.0081 | 406 | 0.870951 | no |
| `h1_tail_ratio_99_50_50` | h1 | 50 | 0.0405 | 406 | 0.415279 | no |
| `h1_tail_ratio_99_50_500` | h1 | 500 | -0.0129 | 406 | 0.79496 | no |
| `h1_tr_over_mean_20` | h1 | 20 | 0.1356 | 406 | 0.006216 | no |
| `h1_tr_over_mean_200` | h1 | 200 | 0.1141 | 406 | 0.021442 | no |
| `h1_tr_over_mean_50` | h1 | 50 | 0.1293 | 406 | 0.009083 | no |
| `h1_vol_above_median_200` | h1 | 200 | 0.0509 | 406 | 0.306233 | no |
| `h1_vol_of_range_ratio_20` | h1 | 20 | 0.0641 | 406 | 0.197735 | no |
| `h1_vol_of_range_ratio_200` | h1 | 200 | -0.0271 | 406 | 0.585698 | no |
| `h1_vol_of_range_ratio_50` | h1 | 50 | -0.0384 | 406 | 0.44066 | no |
| `h1_vol_of_vol_20_w200` | h1 | 200 | -0.01 | 406 | 0.840204 | yes |
| `h1_vol_of_vol_20_w50` | h1 | 50 | 0.0342 | 406 | 0.491651 | no |
| `h1_vol_regime_transitions_k20` | h1 | — | 0.0345 | 406 | 0.487927 | no |
| `h1_vol_regime_transitions_k5` | h1 | — | 0.0498 | 406 | 0.316898 | no |
| `h1_vol_regime_transitions_k50` | h1 | — | 0.0316 | 406 | 0.525604 | no |
| `h4_atr_14` | h4 | 14 | -0.0539 | 406 | 0.278539 | no |
| `h4_atr_14_pct_w100` | h4 | 100 | -0.032 | 406 | 0.520239 | no |
| `h4_atr_14_pct_w500` | h4 | 500 | -0.0287 | 406 | 0.564398 | yes |
| `h4_atr_200` | h4 | 200 | -0.0514 | 406 | 0.301609 | no |
| `h4_atr_200_pct_w100` | h4 | 100 | -0.0657 | 406 | 0.186298 | no |
| `h4_atr_200_pct_w500` | h4 | 500 | -0.0154 | 406 | 0.756628 | yes |
| `h4_atr_50` | h4 | 50 | -0.0569 | 406 | 0.252541 | no |
| `h4_atr_50_pct_w100` | h4 | 100 | -0.059 | 406 | 0.235671 | no |
| `h4_atr_50_pct_w500` | h4 | 500 | -0.0355 | 406 | 0.475327 | yes |
| `h4_atr_ratio_14_over_200` | h4 | 200 | -0.0464 | 406 | 0.350536 | no |
| `h4_atr_ratio_14_over_50` | h4 | 50 | -0.0283 | 406 | 0.569983 | no |
| `h4_atr_ratio_50_over_200` | h4 | 200 | -0.041 | 406 | 0.409425 | no |
| `h4_bb_expansion_flag_200_w100` | h4 | 100 | -0.045 | 406 | 0.365747 | no |
| `h4_bb_expansion_flag_20_w100` | h4 | 100 | -0.0356 | 406 | 0.473943 | no |
| `h4_bb_expansion_flag_50_w100` | h4 | 100 | -0.0364 | 406 | 0.464036 | no |
| `h4_bb_squeeze_flag_200_w100` | h4 | 100 | 0.0815 | 406 | 0.101052 | no |
| `h4_bb_squeeze_flag_20_w100` | h4 | 100 | -0.0377 | 406 | 0.448396 | no |
| `h4_bb_squeeze_flag_50_w100` | h4 | 100 | 0.0003 | 406 | 0.995449 | no |
| `h4_bb_width_20` | h4 | 20 | 0.0096 | 406 | 0.84779 | no |
| `h4_bb_width_200` | h4 | 200 | -0.0053 | 406 | 0.915946 | no |
| `h4_bb_width_50` | h4 | 50 | -0.0301 | 406 | 0.545081 | no |
| `h4_bb_width_pct_200_w100` | h4 | 100 | -0.0831 | 406 | 0.094429 | no |
| `h4_bb_width_pct_20_w100` | h4 | 100 | 0.0284 | 406 | 0.568892 | no |
| `h4_bb_width_pct_50_w100` | h4 | 100 | -0.0533 | 406 | 0.283547 | no |
| `h4_count_2sigma_w200` | h4 | 200 | -0.0414 | 406 | 0.405473 | yes |
| `h4_count_2sigma_w50` | h4 | 50 | 0.0148 | 406 | 0.766236 | no |
| `h4_count_2sigma_w500` | h4 | 500 | 0.0407 | 406 | 0.413391 | no |
| `h4_count_3sigma_w200` | h4 | 200 | -0.012 | 406 | 0.809768 | yes |
| `h4_count_3sigma_w50` | h4 | 50 | 0.0131 | 406 | 0.792139 | no |
| `h4_count_3sigma_w500` | h4 | 500 | 0.0361 | 406 | 0.468525 | no |
| `h4_garch_persistence_lag1_w100` | h4 | 100 | 0.0233 | 406 | 0.639566 | no |
| `h4_garch_persistence_lag1_w20` | h4 | 20 | 0.0269 | 406 | 0.589364 | no |
| `h4_garman_klass_vol_20` | h4 | 20 | -0.0029 | 406 | 0.952755 | no |
| `h4_garman_klass_vol_200` | h4 | 200 | -0.0089 | 406 | 0.858829 | no |
| `h4_garman_klass_vol_50` | h4 | 50 | -0.0103 | 406 | 0.836815 | no |
| `h4_norm_tr_20` | h4 | 20 | -0.0007 | 406 | 0.988813 | no |
| `h4_norm_tr_200` | h4 | 200 | -0.0091 | 406 | 0.855453 | no |
| `h4_norm_tr_50` | h4 | 50 | -0.0078 | 406 | 0.875192 | no |
| `h4_norm_tr_std_20` | h4 | 20 | 0.0186 | 406 | 0.70877 | no |
| `h4_norm_tr_std_200` | h4 | 200 | 0.0038 | 406 | 0.939191 | no |
| `h4_norm_tr_std_50` | h4 | 50 | -0.006 | 406 | 0.903618 | no |
| `h4_parkinson_vol_20` | h4 | 20 | 0.0042 | 406 | 0.932873 | no |
| `h4_parkinson_vol_200` | h4 | 200 | -0.006 | 406 | 0.904483 | no |
| `h4_parkinson_vol_50` | h4 | 50 | -0.0091 | 406 | 0.855488 | no |
| `h4_range_contraction_flag_20` | h4 | 20 | -0.1084 | 406 | 0.029038 | no |
| `h4_range_contraction_flag_200` | h4 | 200 | -0.0898 | 406 | 0.070735 | no |
| `h4_range_contraction_flag_50` | h4 | 50 | -0.1004 | 406 | 0.043239 | no |
| `h4_range_expansion_flag_20` | h4 | 20 | 0.0705 | 406 | 0.155946 | no |
| `h4_range_expansion_flag_200` | h4 | 200 | 0.1136 | 406 | 0.02203 | no |
| `h4_range_expansion_flag_50` | h4 | 50 | 0.1316 | 406 | 0.007926 | no |
| `h4_range_over_mean_20` | h4 | 20 | 0.1042 | 406 | 0.035795 | no |
| `h4_range_over_mean_200` | h4 | 200 | 0.0642 | 406 | 0.197014 | no |
| `h4_range_over_mean_50` | h4 | 50 | 0.1019 | 406 | 0.040154 | no |
| `h4_realized_kurt_200` | h4 | 200 | 0.0883 | 406 | 0.075676 | yes |
| `h4_realized_kurt_50` | h4 | 50 | -0.0218 | 406 | 0.660819 | yes |
| `h4_realized_kurt_500` | h4 | 500 | 0.0029 | 406 | 0.95425 | yes |
| `h4_realized_skew_200` | h4 | 200 | -0.0259 | 406 | 0.602195 | yes |
| `h4_realized_skew_50` | h4 | 50 | 0.0819 | 406 | 0.099336 | yes |
| `h4_realized_skew_500` | h4 | 500 | 0.0138 | 406 | 0.780911 | yes |
| `h4_realized_vol_20` | h4 | 20 | 0.0212 | 406 | 0.670773 | no |
| `h4_realized_vol_200` | h4 | 200 | 0.002 | 406 | 0.968179 | no |
| `h4_realized_vol_50` | h4 | 50 | -0.0058 | 406 | 0.907699 | no |
| `h4_return_p95_abs_200` | h4 | 200 | -0.0151 | 406 | 0.761541 | no |
| `h4_return_p95_abs_50` | h4 | 50 | -0.0034 | 406 | 0.945713 | no |
| `h4_return_p95_abs_500` | h4 | 500 | 0.0041 | 406 | 0.933793 | no |
| `h4_return_p99_abs_200` | h4 | 200 | 0.0202 | 406 | 0.684489 | no |
| `h4_return_p99_abs_50` | h4 | 50 | -0.0036 | 406 | 0.942624 | no |
| `h4_return_p99_abs_500` | h4 | 500 | 0.0132 | 406 | 0.790957 | no |
| `h4_sq_return_autocorr_lag1_w200` | h4 | 200 | 0.0744 | 406 | 0.134467 | yes |
| `h4_sq_return_autocorr_lag1_w50` | h4 | 50 | 0.0151 | 406 | 0.762219 | yes |
| `h4_sq_return_autocorr_lag20_w200` | h4 | 200 | 0.0616 | 406 | 0.21538 | yes |
| `h4_sq_return_autocorr_lag20_w50` | h4 | 50 | -0.0363 | 406 | 0.465171 | yes |
| `h4_sq_return_autocorr_lag5_w200` | h4 | 200 | 0.0673 | 406 | 0.175949 | yes |
| `h4_sq_return_autocorr_lag5_w50` | h4 | 50 | 0.0682 | 406 | 0.170167 | yes |
| `h4_tail_ratio_99_50_200` | h4 | 200 | 0.0247 | 406 | 0.620039 | no |
| `h4_tail_ratio_99_50_50` | h4 | 50 | -0.0056 | 406 | 0.911135 | no |
| `h4_tail_ratio_99_50_500` | h4 | 500 | 0.0207 | 406 | 0.676824 | no |
| `h4_tr_over_mean_20` | h4 | 20 | 0.0977 | 406 | 0.049232 | no |
| `h4_tr_over_mean_200` | h4 | 200 | 0.0605 | 406 | 0.223584 | no |
| `h4_tr_over_mean_50` | h4 | 50 | 0.0952 | 406 | 0.055301 | no |
| `h4_vol_above_median_200` | h4 | 200 | 0.0559 | 406 | 0.261111 | no |
| `h4_vol_of_range_ratio_20` | h4 | 20 | 0.03 | 406 | 0.54603 | no |
| `h4_vol_of_range_ratio_200` | h4 | 200 | -0.0096 | 406 | 0.847765 | no |
| `h4_vol_of_range_ratio_50` | h4 | 50 | -0.0275 | 406 | 0.580057 | no |
| `h4_vol_of_vol_20_w200` | h4 | 200 | 0.0398 | 406 | 0.424354 | yes |
| `h4_vol_of_vol_20_w50` | h4 | 50 | 0.0146 | 406 | 0.768606 | no |
| `h4_vol_regime_transitions_k20` | h4 | — | -0.0055 | 406 | 0.911865 | no |
| `h4_vol_regime_transitions_k5` | h4 | — | -0.021 | 406 | 0.673108 | no |
| `h4_vol_regime_transitions_k50` | h4 | — | 0.0438 | 406 | 0.379268 | no |
| `m15_atr_14` | m15 | 14 | -0.0533 | 406 | 0.284319 | no |
| `m15_atr_14_pct_w100` | m15 | 100 | 0.0264 | 406 | 0.595314 | no |
| `m15_atr_14_pct_w500` | m15 | 500 | 0.0244 | 406 | 0.624099 | yes |
| `m15_atr_200` | m15 | 200 | -0.055 | 406 | 0.268819 | no |
| `m15_atr_200_pct_w100` | m15 | 100 | -0.0019 | 406 | 0.969542 | no |
| `m15_atr_200_pct_w500` | m15 | 500 | -0.017 | 406 | 0.732622 | yes |
| `m15_atr_50` | m15 | 50 | -0.0551 | 406 | 0.268245 | no |
| `m15_atr_50_pct_w100` | m15 | 100 | 0.0049 | 406 | 0.92194 | no |
| `m15_atr_50_pct_w500` | m15 | 500 | -0.011 | 406 | 0.824537 | yes |
| `m15_atr_ratio_14_over_200` | m15 | 200 | 0.0094 | 406 | 0.849458 | no |
| `m15_atr_ratio_14_over_50` | m15 | 50 | 0.0343 | 406 | 0.490571 | no |
| `m15_atr_ratio_50_over_200` | m15 | 200 | -0.0177 | 406 | 0.722215 | no |
| `m15_bb_expansion_flag_200_w100` | m15 | 100 | 0.0705 | 406 | 0.156017 | no |
| `m15_bb_expansion_flag_20_w100` | m15 | 100 | 0.0642 | 406 | 0.196703 | no |
| `m15_bb_expansion_flag_50_w100` | m15 | 100 | -0.0359 | 406 | 0.470409 | no |
| `m15_bb_squeeze_flag_200_w100` | m15 | 100 | -0.0483 | 406 | 0.331639 | no |
| `m15_bb_squeeze_flag_20_w100` | m15 | 100 | -0.0035 | 406 | 0.944047 | no |
| `m15_bb_squeeze_flag_50_w100` | m15 | 100 | -0.0291 | 406 | 0.559143 | no |
| `m15_bb_width_20` | m15 | 20 | 0.0521 | 406 | 0.294998 | no |
| `m15_bb_width_200` | m15 | 200 | 0.0186 | 406 | 0.708863 | no |
| `m15_bb_width_50` | m15 | 50 | 0.039 | 406 | 0.433472 | no |
| `m15_bb_width_pct_200_w100` | m15 | 100 | 0.077 | 406 | 0.121269 | no |
| `m15_bb_width_pct_20_w100` | m15 | 100 | 0.0437 | 406 | 0.379969 | no |
| `m15_bb_width_pct_50_w100` | m15 | 100 | 0.0113 | 406 | 0.820515 | no |
| `m15_count_2sigma_w200` | m15 | 200 | -0.006 | 406 | 0.90461 | yes |
| `m15_count_2sigma_w50` | m15 | 50 | 0.0321 | 406 | 0.519005 | no |
| `m15_count_2sigma_w500` | m15 | 500 | -0.0116 | 406 | 0.815031 | no |
| `m15_count_3sigma_w200` | m15 | 200 | 0.016 | 406 | 0.747778 | yes |
| `m15_count_3sigma_w50` | m15 | 50 | 0.0188 | 406 | 0.70627 | no |
| `m15_count_3sigma_w500` | m15 | 500 | -0.0085 | 406 | 0.864789 | no |
| `m15_garch_persistence_lag1_w100` | m15 | 100 | 0.0127 | 406 | 0.798113 | no |
| `m15_garch_persistence_lag1_w20` | m15 | 20 | 0.1034 | 406 | 0.037286 | no |
| `m15_garman_klass_vol_20` | m15 | 20 | 0.0083 | 406 | 0.867885 | no |
| `m15_garman_klass_vol_200` | m15 | 200 | -0.0077 | 406 | 0.877328 | no |
| `m15_garman_klass_vol_50` | m15 | 50 | 0.0137 | 406 | 0.783502 | no |
| `m15_intraday_vol_hour_avg_d30` | m15 | — | 0.05 | 406 | 0.315163 | no |
| `m15_intraday_vol_pct_d30` | m15 | — | -0.0109 | 406 | 0.826756 | no |
| `m15_intraday_vol_ratio_d30` | m15 | — | -0.0134 | 406 | 0.787852 | no |
| `m15_norm_tr_20` | m15 | 20 | -0.0009 | 406 | 0.986313 | no |
| `m15_norm_tr_200` | m15 | 200 | 0.0001 | 406 | 0.998888 | no |
| `m15_norm_tr_50` | m15 | 50 | 0.0057 | 406 | 0.909006 | no |
| `m15_norm_tr_std_20` | m15 | 20 | 0.0257 | 406 | 0.605075 | no |
| `m15_norm_tr_std_200` | m15 | 200 | -0.0008 | 406 | 0.9874 | no |
| `m15_norm_tr_std_50` | m15 | 50 | 0.0373 | 406 | 0.453943 | no |
| `m15_parkinson_vol_20` | m15 | 20 | 0.0087 | 406 | 0.860807 | no |
| `m15_parkinson_vol_200` | m15 | 200 | -0.0003 | 406 | 0.995262 | no |
| `m15_parkinson_vol_50` | m15 | 50 | 0.0163 | 406 | 0.743884 | no |
| `m15_range_contraction_flag_20` | m15 | 20 | -0.0528 | 406 | 0.288129 | no |
| `m15_range_contraction_flag_200` | m15 | 200 | -0.0523 | 406 | 0.292873 | no |
| `m15_range_contraction_flag_50` | m15 | 50 | -0.1245 | 406 | 0.012036 | no |
| `m15_range_expansion_flag_20` | m15 | 20 | -0.0217 | 406 | 0.6635 | no |
| `m15_range_expansion_flag_200` | m15 | 200 | -0.0115 | 406 | 0.817439 | no |
| `m15_range_expansion_flag_50` | m15 | 50 | 0.0632 | 406 | 0.204045 | no |
| `m15_range_over_mean_20` | m15 | 20 | 0.0601 | 406 | 0.227113 | no |
| `m15_range_over_mean_200` | m15 | 200 | 0.0646 | 406 | 0.193913 | no |
| `m15_range_over_mean_50` | m15 | 50 | 0.044 | 406 | 0.376014 | no |
| `m15_realized_kurt_200` | m15 | 200 | 0.069 | 406 | 0.165003 | yes |
| `m15_realized_kurt_50` | m15 | 50 | 0.0362 | 406 | 0.466491 | yes |
| `m15_realized_kurt_500` | m15 | 500 | 0.0135 | 406 | 0.785984 | yes |
| `m15_realized_skew_200` | m15 | 200 | 0.0039 | 406 | 0.936906 | yes |
| `m15_realized_skew_50` | m15 | 50 | 0.0307 | 406 | 0.537031 | yes |
| `m15_realized_skew_500` | m15 | 500 | 0.0473 | 406 | 0.342067 | yes |
| `m15_realized_vol_20` | m15 | 20 | -0.0026 | 406 | 0.958476 | no |
| `m15_realized_vol_200` | m15 | 200 | 0.0111 | 406 | 0.82404 | no |
| `m15_realized_vol_50` | m15 | 50 | 0.0137 | 406 | 0.78263 | no |
| `m15_return_p95_abs_200` | m15 | 200 | -0.0047 | 406 | 0.924706 | no |
| `m15_return_p95_abs_50` | m15 | 50 | 0.0231 | 406 | 0.642735 | no |
| `m15_return_p95_abs_500` | m15 | 500 | -0.0013 | 406 | 0.979017 | no |
| `m15_return_p99_abs_200` | m15 | 200 | 0.0218 | 406 | 0.661716 | no |
| `m15_return_p99_abs_50` | m15 | 50 | 0.0263 | 406 | 0.59759 | no |
| `m15_return_p99_abs_500` | m15 | 500 | 0.0128 | 406 | 0.797066 | no |
| `m15_sq_return_autocorr_lag1_w200` | m15 | 200 | -0.018 | 406 | 0.718165 | yes |
| `m15_sq_return_autocorr_lag1_w50` | m15 | 50 | 0.172 | 406 | 0.000501 | yes |
| `m15_sq_return_autocorr_lag20_w200` | m15 | 200 | -0.0081 | 406 | 0.870701 | yes |
| `m15_sq_return_autocorr_lag20_w50` | m15 | 50 | -0.0127 | 406 | 0.799127 | yes |
| `m15_sq_return_autocorr_lag5_w200` | m15 | 200 | -0.0256 | 406 | 0.607693 | yes |
| `m15_sq_return_autocorr_lag5_w50` | m15 | 50 | 0.0867 | 406 | 0.081182 | yes |
| `m15_tail_ratio_99_50_200` | m15 | 200 | -0.0011 | 406 | 0.982957 | no |
| `m15_tail_ratio_99_50_50` | m15 | 50 | 0.0614 | 406 | 0.216765 | no |
| `m15_tail_ratio_99_50_500` | m15 | 500 | -0.0241 | 406 | 0.627584 | no |
| `m15_tr_over_mean_20` | m15 | 20 | 0.0582 | 406 | 0.241819 | no |
| `m15_tr_over_mean_200` | m15 | 200 | 0.0623 | 406 | 0.210072 | no |
| `m15_tr_over_mean_50` | m15 | 50 | 0.04 | 406 | 0.421928 | no |
| `m15_vol_above_median_200` | m15 | 200 | -0.0109 | 406 | 0.827342 | no |
| `m15_vol_of_range_ratio_20` | m15 | 20 | 0.1106 | 406 | 0.025883 | no |
| `m15_vol_of_range_ratio_200` | m15 | 200 | -0.0484 | 406 | 0.330459 | no |
| `m15_vol_of_range_ratio_50` | m15 | 50 | 0.0931 | 406 | 0.060896 | no |
| `m15_vol_of_vol_20_w200` | m15 | 200 | 0.0115 | 406 | 0.816799 | yes |
| `m15_vol_of_vol_20_w50` | m15 | 50 | 0.0056 | 406 | 0.910576 | no |
| `m15_vol_regime_transitions_k20` | m15 | — | 0.108 | 406 | 0.029524 | no |
| `m15_vol_regime_transitions_k5` | m15 | — | -0.0288 | 406 | 0.562207 | no |
| `m15_vol_regime_transitions_k50` | m15 | — | 0.0623 | 406 | 0.210178 | no |
