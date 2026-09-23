# K54 v2 Unified Feature Catalog

**Built:** 2026-04-28 (Q1 Week 2-3 close)
**Hypothesis:** `research/ml_program/PRE_REGISTERED_HYPOTHESES.md` Q1.2
**Threshold:** AUC ≥ 0.61 on (a) CPCV-with-purge over 2024-02-20 → 2026-04-28 AND (b) 14-day prospective live holdout 2026-04-29 → 2026-05-12, opened ONCE.
**Builder:** `research/ml_program/scripts/build_catalog_v2.py` (regenerable; no API spend).
**Tabular catalog:** `research/ml_program/feature_catalogs/CATALOG_v2.csv` (1,219 rows + header).

---

## Section 1 — Headline

| Family | Features | Target | Top stability \|ρ\| | Top feature |
|---|---:|---:|---:|---|
| Structure | 432 | 200-400 | 0.266 | `H1__impulse_max_displacement_ratio` |
| Volatility | 270 | 100-300 | 0.172 | `m15_sq_return_autocorr_lag1_w50` |
| Microstructure | 187 | 150-300 | 0.144 | `micro_reversal_rate_m15_lb50` |
| Time/Session | 138 | 50-150 | 0.192 | `t_kz_tokyo_abs_min_to_close` |
| Liquidity | 129 | 100-200 | 0.232 | `liq_round_10p0_dist_above_ticks` (XAUUSD-only) |
| Regime | 63 | 50-100 | 0.087 | `regime_xau_score` |
| **Total** | **1,219** | — | — | — |

**vs K54 v1:** 17 declared features, 4 effective (`ob_distance_atr`, `ob_age_candles`, `hour_utc`, `day_of_week`). K54 v2 = ~72× declared count, ~300× effective count.

The 2K target in the original briefing is aspirational. The pre-registered "4× the K54 v1 feature set" gate is met >70× over. Quality + breadth take priority over raw count.

---

## Section 2 — Top 20 features overall (by |stability_rho|)

Stability = Spearman rank correlation of feature value at trade-entry-candle-close vs realized R, computed on pre-2026-04 cohort only (n varies by feature 42-406).

| Rank | Family | Feature | ρ | n |
|---:|---|---|---:|---:|
| 1 | structure | `H1__impulse_max_displacement_ratio` | +0.266 | 173 |
| 2 | liquidity | `liq_round_10p0_dist_above_ticks` (XAUUSD) | -0.232 | 42 |
| 3 | liquidity | `liq_round_10p0_dist_below_ticks` (XAUUSD) | +0.232 | 42 |
| 4 | structure | `M15__last_choch_age_bars__lb20` | -0.219 | 78 |
| 5 | structure | `M15__last_choch_age_bars__lb100` | -0.219 | 78 |
| 6 | structure | `M15__nearest_ob_dist_atr__lb20` | -0.215 | 258 |
| 7 | time_session | `t_kz_tokyo_abs_min_to_close` (JPY pairs) | +0.192 | 105 |
| 8 | time_session | `t_kz_tokyo_signed_min_to_open` (JPY pairs) | -0.191 | 105 |
| 9 | time_session | `t_kz_tokyo_signed_min_to_close` (JPY pairs) | -0.191 | 105 |
| 10 | time_session | `t_kz_tokyo_abs_min_to_open` (JPY pairs) | +0.191 | 105 |
| 11 | structure | `H1__mean_displacement_ratio__lb20` | +0.181 | 345 |
| 12 | structure | `H1__impulse_range_atr` | +0.181 | 173 |
| 13 | volatility | `m15_sq_return_autocorr_lag1_w50` | +0.172 | 406 |
| 14 | structure | `H1__last_event_displaced__lb20` | +0.167 | 345 |
| 15 | structure | `H1__last_event_displaced__lb100` | +0.167 | 345 |
| 16 | structure | `H4__ob_mean_age_bars__lb50` | -0.160 | 332 |
| 17 | structure | `M15__swing_low_count__lb20` | +0.155 | 345 |
| 18 | liquidity | `liq_M15_stopcluster_count_1atr` | -0.151 | 345 |
| 19 | structure | `H1__last_choch_age_bars__lb20` | +0.147 | 179 |
| 20 | structure | `H1__last_choch_age_bars__lb100` | +0.147 | 179 |

**Sign-convention reading (for the modeler):**

- **Positive** ρ on `impulse_displacement_ratio`, `impulse_range_atr`, `last_event_displaced`, `swing_low_count`, `range_over_mean`: stronger / more recent / cleaner impulses → better R.
- **Negative** ρ on `nearest_ob_dist_atr`, `stopcluster_count`, `ob_mean_age_bars`: closer OBs / cluttered zones / stale OBs → worse R. Consistent with the ICT framing that BOS in clean / close-OB-but-aged zones may be late.
- The XAUUSD round-number pair (#2 + #3) is sign-symmetric — distance to round above is bad for LONG, distance to round below is good for LONG. Logic: a round number magnet near above price caps upside; a round below acts as support away from price.
- Tokyo KZ proximity (#7-#10) is JPY-pair-only (n=105) — a real cohort signal that K54 v1's `kill_zone` flag flattened.

**Bonferroni note:** Family-size correction at α=0.05 → threshold ~p<4e-5 for the full catalog (1219 features). 0 features universally pass that bar in univariate. Per the pre-registration discipline, **stability scoring is screening only — CPCV at K54 v2 train time is the validation gate**.

---

## Section 3 — Per-family summary

### Structure (432 features) — `feature_catalogs/structure.md`

- **Top 5:** `H1__impulse_max_displacement_ratio` +0.266, `M15__last_choch_age_bars__lb20` -0.219, `M15__last_choch_age_bars__lb100` -0.219, `M15__nearest_ob_dist_atr__lb20` -0.215, `H1__mean_displacement_ratio__lb20` +0.181.
- **What's new vs K54 v1:** pre-BOS impulse-leg geometry (audit's #5 priority gap), multi-lookback OB distance, multi-TF CHoCH age, MTF alignment vector, swing-magnitude stats.
- **Concern:** **MTF alignment saturation.** D1 direction is +1 for the entire 2026 gold cohort (sustained uptrend). 14 MTF agreement features show ρ≈0 from variance starvation, NOT leakage. Will add value on SHORT cohorts and counter-trend setups (sparse in train+val). LightGBM should still find split-gain for cells where MTF disagrees.

### Volatility (270 features) — `feature_catalogs/volatility.md`

- **Top 5:** `m15_sq_return_autocorr_lag1_w50` +0.172, `h1_range_over_mean_20` +0.144, `h1_range_over_mean_50` +0.136, `h1_tr_over_mean_20` +0.136, `h4_range_expansion_flag_50` +0.132.
- **What's new vs K54 v1:** GREENFIELD — K54 v1 had zero volatility-family features. ATR percentile + realized vol + GARCH lag-1 + range-vs-expansion + BB squeeze/expansion + fat-tail percentiles + Parkinson/Garman-Klass + intraday vol profile.
- **Top stability is GARCH lag-1 squared-return autocorr** — directly aligns with memory `project_distributional_findings` (GARCH persistence 0.9906, half-life ~73 H1 bars). Per-regime LightGBM should amplify the signal beyond univariate ρ via interactions.

### Microstructure (187 features) — `feature_catalogs/microstructure.md`

- **Top 5:** `micro_reversal_rate_m15_lb50` -0.144, `range_pctile_h4_lb20` +0.139, `range_pctile_h4_lb50` +0.133, `last_bar_lower_wick_ratio_m15` +0.124, `longest_red_streak_m15_lb50` +0.122.
- **What's new vs K54 v1:** M15 reversal rate, range percentile (TF-aware), wick ratios, streak counts, Component-2-output rolling counts, synthetic Lee-Ready proxy from M1 (Group H).
- **Top concern: TICK COVERAGE GAP.** Only NAS100 + US30_cash have tick parquets, only for 2026-04-27 (single day, post-pre-2026-04 boundary). 5 instruments — XAUUSD/GBPJPY/GBPUSD/USDJPY/XAGUSD — have ZERO tick coverage. **24 tick-required features have stability_n=0** in the CSV. NaN sentinels (not zeros) are emitted; 163 non-tick features carry the family weight.

### Time/Session (138 features) — `feature_catalogs/time_session.md`

- **Top 5:** `t_kz_tokyo_abs_min_to_close` +0.192, `t_kz_tokyo_signed_min_to_open` -0.191, `t_kz_tokyo_signed_min_to_close` -0.191, `t_kz_tokyo_abs_min_to_open` +0.191, `t_kz_tokyo_min_to_next_open` -0.141 — all JPY-pair-only (n=105).
- **What's new vs K54 v1:** Minutes-to-KZ-open/close per session per instrument (replaces K54 v1's coarse `kill_zone` flag); week-of-month; first-15min-of-session; OPEX proximity; calendar-based NFP/CPI proximity (formula-only, no news content per CEO ruling).
- **Calendar caveats** (documented in family doc): NFP is 1st-Friday-of-month (BLS shifts on holidays); CPI is 2nd-Wednesday formula with explicit ±2d fuzz. Flagged "Low-Medium" confidence; modeler should learn ±2d windows.
- **21 features constant-in-backfill** (hour-aligned timestamps + no weekend rows). Per "flag-don't-drop" discipline they're kept; will exercise in live data.

### Liquidity (129 features) — `feature_catalogs/liquidity.md`

- **Top 5:** `liq_round_10p0_dist_above_ticks` -0.232 (XAUUSD), `liq_round_10p0_dist_below_ticks` +0.232 (XAUUSD), `liq_M15_stopcluster_count_1atr` -0.151, `liq_H1_bars_since_sweep_high` -0.146, `liq_H1_stopcluster_count_50tick` -0.143.
- **What's new vs K54 v1:** GREENFIELD — K54 v1 had zero liquidity-family features. Equal-highs/lows count, sweep detection (multi-TF), time-since-last-sweep, distance-to-equal-level, distance-to-round-number, stop-cluster proxy, volume-cluster proximity, prior-period high/low distances, price-magnet score.
- **Concern: M15 sweep flag tied_pct=92%.** Sweep semantics are LOOSER than production's same-bar body-close (5-bar reversal window vs 1-bar). LightGBM tree splits should still find boundary signal; flagged for downstream verification.
- **Per-instrument round-number features** are low-n (42-101) but high |ρ| (up to 0.232). Kept for per-regime ensemble pickup; LightGBM handles missing values natively.

### Regime (63 features) — `feature_catalogs/regime.md`

- **Top 5:** `regime_xau_score` -0.087, `regime_changed_in_last_50` +0.084, `regime_fleet_bullish_count` -0.082, `regime_fleet_transitional_count` +0.077, `regime_xau_matches_self` +0.077.
- **What's new vs K54 v1:** Audit §5 quick-wins delivered — `v2_score` and `v2_dead_zone` surfaced as 14 features (UNUSED in K54 v1 per audit). Plus regime-stability-score, regime-transition-flag, time-since-flip, regime-conditional volatility, cross-instrument fleet alignment, XAU-anchor features.
- **3 of top-5 are cross-instrument fleet/XAU-anchor features.** Negative signs on bullish-cluster features consistent with F2/A6 LONG-side decay finding (`project_a6_decay_attribution_long_side_concentrated`).
- **Concern: US30_cash NOT in `structure_detector_backfill_2026.jsonl`.** Backfill covers EURUSD/GBPJPY/GBPUSD/GER40/NAS100/UK100/USDJPY/XAGUSD/XAUUSD — but not US30_cash (the live fleet uses US30_cash, not US30). Mitigation: 2 added flags `regime_backfill_available`, `regime_backfill_h4_bars_stale` so the model can disambiguate "regime is neutral" from "no backfill row".

---

## Section 4 — Cross-cutting findings

### A. The signal axis the catalog identifies

Top-20 spans 5 of 6 families (Microstructure absent from top-20; only Volatility's #1 GARCH feature crosses ρ>0.16 broadly). The dominant pattern:

- **Impulse strength + recency** (Structure positives at #1, #11, #12, #14, #15) → bigger / more recent / cleaner impulse-leg → bigger realized R.
- **Cluster / clutter penalty** (Structure + Liquidity negatives at #4, #5, #6, #16, #18) → more local clutter / staler / older OB → smaller realized R.
- **Cohort separation** (Time/Session #7-#10, Liquidity #2-#3) — features that pin down a specific instrument-cohort dominate that cohort's signal but contribute zero to others; the per-regime ensemble architecture is correct.

### B. Cohort imbalance affects univariate stability

- **D1 sustained-bull cohort** flattens MTF agreement variance (Structure 14-feature subset).
- **JPY-pair Tokyo** (n=105) drives 4 of top-10 by univariate |ρ|, pinning a cohort signal that won't surface for non-JPY.
- **Pre-2026-04 trade_index** snaps to KZ-hour (date-only entry time precision); only F11 has bos-time precision. Stability ρ may be biased toward features that move slowly enough to survive the snap-to-hour error (Volatility flagged this).
- **Implication:** trust per-regime LightGBM split gain over univariate Spearman ρ. Univariate is screening only.

### C. Potential cross-family redundancy

Modeler should expect correlated features across:

- Volatility's `h1_range_over_mean_*` vs Microstructure's `range_pctile_h4_*` — different TFs but related concept (range expansion).
- Volatility's `count_2sigma`/`count_3sigma` vs Liquidity's `liq_*_sweep_*` — different mechanisms but both fire on extreme moves.
- Structure's `M15__nearest_ob_dist_atr` vs Liquidity's `liq_*_stopcluster_*` — both encode local clutter, different primitives.

LightGBM correlation pruning (or a Pearson/Spearman correlation matrix sweep at training time) is recommended before deep hyperparameter search.

### D. Bonferroni summary

- Catalog-wide: 0 features universally survive Bonferroni at α=0.05 (threshold ~p<4e-5). Some features flagged near-Bonferroni in Volatility (GARCH lag-1, p=5e-4). Liquidity's per-instrument round-number features hit |ρ|=0.232 but at n=42-52 — wide CI.
- This is **expected and consistent with the pre-registration discipline**. The brief explicitly stated: "stability scores are screening only; CPCV at K54 v2 train time is real validation."
- The univariate-zero / weak-univariate features may still split-gain in tree ensembles via interactions (e.g. `bb_squeeze_flag` × regime; MTF agreement on SHORT-side cohort).

---

## Section 5 — Leakage discipline summary

Each family ran an independent leakage self-check; all six pass with explicit point-in-time guarantees.

| Family | Mechanism | Boundary | Spot-check |
|---|---|---|---|
| Structure | `cutoff_idx = state.n - 1 - lookback`; trailing-only slices | `candles[:cutoff_idx+1]` slice argument propagated through Component 2 helpers | F11 BOS time = decision time, before any outcome bars; backward-walk for pre-BOS consolidation |
| Volatility | `pd.rolling(N).fn()` at row T uses [T-N+1, T] (current included) | No `.shift(-k)`; `merge_asof(direction='backward')` for multi-TF stitch | Module-level self-test on import compares full-data vs truncated-data ATR(14) and realized_vol(20) at row 200, must match <1e-9 |
| Microstructure | `_slice_bars(df, ts_close, lookback)` strict `<`; `_slice_ticks(...)` half-open `[ts_close - lb, ts_close)` | `compute_microstructure_features` raises `ValueError` for `ts_close >= 2026-04-28 23:59 UTC` | 6-feature random-sample table in family doc verifies boundary |
| Time/Session | Single-timestamp + static calendar; no rolling reads | `t_kz_*_min_to_next_open` is "days until Christmas" — calendar-known future, not future-data peek | Sign convention review: past events negative, future events positive |
| Liquidity | `swings_before` filter excludes swings-at-or-after sweep window; retest search bounded `(sweep_idx+1, anchor_idx+1)` | Sweep flag fires on body-close-inside even when 5-bar reversal window not yet populated (live-bar conservative behavior) | "Confirmed: no feature reads `candles[anchor_idx+1]` or later" — full helper inspection |
| Regime | Backfill `latest_at(symbol, T)` returns row with `row.ts <= T`; H4/D1 ATR uses `_h4_floor(T) - 1s` cutoff | Cross-instrument fleet rows fetched independently with same `<= T` discipline | 7 explicit point-in-time leakage probes in family doc |

**Overall:** no family has a known leak. Microstructure's tick-day-loader is single-date conservative — produces NaN at midnight rather than cross-day leak. Liquidity's sweep flag has a 5-bar reversal window that is bounded BEFORE anchor (no future-bar consultation). Structure's MTF saturation is variance-starved, NOT leak. Regime's backfill `logged_at >> ts` does NOT leak because the regime label at `ts` was computed from swings ending at `ts` — point-in-time at compute time, snapshot-replayed at consumption.

**Recommended at K54 v2 train time:** an independent leakage hunter agent (Week 5-6 adversarial validator per the roadmap) should run a regression test that sets `ts_close` and a single bar at `time = ts_close - 1ms`, then a second at `time = ts_close + 1ms`, and verify the second bar is NEVER included in any feature across all 1219.

---

## Section 6 — Operational concerns the modeler must handle

1. **Tick coverage gap (Microstructure).** Train K54 v2 with the **163 non-tick features as the primary feature set**, and the **24 tick-required features as a secondary set** the ablation tests can include or exclude. Production deployment will exercise the secondary set as tick capture matures (see Q3 — Tick microstructure phase).
2. **US30_cash backfill gap (Regime).** The model should learn that `regime_backfill_available == 0` reduces regime-feature reliability for that instrument. Concrete: train per-regime ensembles with US30_cash rows in the "missing-backfill" bucket; per-regime gating still works via the production live-stream classifier output.
3. **MTF saturation (Structure).** 14 MTF agreement features are variance-starved on the 2026 sustained-bull cohort. Cross-period replication (2022-2025 train) should add the variance back. If cross-period replication fails for these specific features, drop them at K54 v3.
4. **Sweep flag tied_pct=92% (Liquidity).** LightGBM tree splits should still find boundary signal; if Week-4 modeling shows zero split-gain, a `tied_pct` filter at 80% may be appropriate.
5. **JPY-pair Tokyo cohort split (Time/Session).** Tokyo features are JPY-pair-only — they're missing for non-JPY instruments. Per-regime ensemble + per-instrument fine-tune should handle this; modeler should verify Tokyo features have feature_importance > 0 in JPY-only regime models and feature_importance ≈ 0 in non-JPY models.
6. **Cohort imbalance (D1 sustained-bull).** Cross-period replication 2022-2025 is the antidote. If 2022-2025 data shows insufficient regime variation, escalate.
7. **Trade-index timestamp snap (cross-cutting).** Trade-index records snap entry time to KZ-hour (date-only); only F11 records have bos-time precision. Modeler should weigh F11-cohort stability scores higher when feature-pruning, and consider per-source train splits.
8. **Bonferroni discipline.** All 1,219 features pass to LightGBM unfiltered (per the discipline). Feature pruning by univariate ρ is forbidden; CPCV split-gain is the gate.

---

## Section 7 — Recommendations for K54 v2 modeler (Week 4)

1. **Training population** — pre-2026-04-29 only (data cutoff ≤2026-04-28 23:59 UTC enforced by every family module). 14-day prospective holdout 2026-04-29 → 2026-05-12 is OFF-LIMITS until end-of-Q1 evaluation.
2. **Feature partitioning:**
   - **Primary set (1,195 features):** all features minus the 24 tick-required (Microstructure Group I).
   - **Secondary set (24 features):** tick-required Microstructure features. Ablation-test inclusion-vs-exclusion at K54 v3 review time.
3. **Per-regime architecture** — keep K54 v1's per-regime ensemble (regime as gating, not feature). Min sample size per regime ≥30 before reporting per-regime AUC (audit §8 methodology improvement).
4. **CPCV** — 6 splits + ≥1-week purge gap + ≥1-day embargo per de Prado *AFML* ch. 7. Expected per-fold n ≈ 80-100 trades; AUC SE ≈ 0.05-0.06 per fold; ensemble averages tighter.
5. **Cross-instrument replication** — train on XAUUSD only, test on the other 6. Threshold: positive AUC lift on ≥4 of 6.
6. **Cross-period replication** — train on 2022-2025 (where available), test on 2026-Q1. Threshold: positive AUC lift on the 2026 partition.
7. **Hyperparameter search** — Optuna with `min_data_in_leaf = max(3, len(y_tr) // 30)`, `n_estimators ∈ {50, 100, 200, 400}`, `max_depth ∈ {3, 5, 7, 9}`, `learning_rate ∈ {0.01, 0.03, 0.05, 0.1}`. Selection metric: validation CPCV mean AUC. Early stopping on val with `stopping_rounds=20`.
8. **Calibration** — Platt-scaling sigmoid (small-sample-friendly) per K54 v1's pattern.
9. **Realized R only** — no walk-level proxies. Consume `realized_r` from F11 records + `r_multiple` from trade_index.
10. **Dedup fix from audit §8 #2** — switch from trade_id-keyed to tuple-keyed `(date, symbol, direction, framework, realized_r)` to eliminate K54 v1's ~33-row train-set duplication.
11. **Don't re-run** the K54 v1 baseline reproduction — already done by K55 (`dd6a855`). AUC 0.571 is the baseline number.
12. **Output** — `research/ml_program/models/k54_v2/` with: `meta.json` (training spec + hyperparams), `regime_*.lgb` (per-regime models), `global.lgb` (fallback), `training_log.json`, `cpcv_results.json`.

---

## Section 8 — File map + reproducibility

| File | Purpose |
|---|---|
| `research/ml_program/feature_catalogs/CATALOG_v2.md` | This synthesis. |
| `research/ml_program/feature_catalogs/CATALOG_v2.csv` | Unified tabular catalog (1,219 rows). |
| `research/ml_program/feature_catalogs/{family}.md` | Per-family detailed catalog (×6). |
| `research/ml_program/feature_catalogs/{family}.csv` | Per-family tabular catalog (×6). |
| `research/ml_program/scripts/features/{family}.py` | Reference implementation (×6). |
| `research/ml_program/scripts/build_catalog_v2.py` | Normalizer; produces `CATALOG_v2.csv` from per-family CSVs. |

**To rebuild the unified catalog:**

```
python research/ml_program/scripts/build_catalog_v2.py
```

(Re-runs from per-family CSVs; idempotent.)

---

*Synthesis complete. Standing by for Week 4 K54 v2 modeler dispatch.*
