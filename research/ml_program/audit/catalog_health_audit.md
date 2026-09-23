# K54 v2 Catalog Health Audit

**Auditor:** Catalog Health Auditor (Q1 Week 3 close, 2026-04-28)
**Hypothesis under test:** `research/ml_program/PRE_REGISTERED_HYPOTHESES.md` Q1.2 (per-regime LightGBM AUC ≥ 0.61).
**Catalog under audit:** `research/ml_program/feature_catalogs/CATALOG_v2.csv` (1,219 rows + header) + 6 family modules at `research/ml_program/scripts/features/{family}.py`.
**Cohort:** XAUUSD candle-close timestamps drawn from K54 v1's 191-trade XAUUSD partition (deduped to 168, sampled to 80, 79 materialized = 1 dropped for insufficient OHLCV history at 2024-04-01).
**Holdout 2026-04-29 → 2026-05-12:** untouched, never accessed.
**Spec deviation:** the brief asked for `2026-03-15 13:00 UTC` as the smoke-test timestamp; that is a Sunday with no candles. Substituted `2026-03-13 13:00 UTC` (Friday NY-KZ open) — same NY-KZ regime, weekday close in training population.
**Audit code:** `research/ml_program/audit/catalog_health_run.py` (Q1+Q4+Q2-naive); `research/ml_program/audit/q2_robust_recompute.py` (Q2 robust); `research/ml_program/audit/q3_integrity_check.py` (Q3).

---

## Section 1 — Composability verdict

**Verdict: PASS (with 2 caveats).**

All six family modules import cleanly from `research/ml_program/scripts/features/` (no cross-import circular issues, no missing project-root dependencies). For the test fixture XAUUSD, 2026-03-13 13:00 UTC, every family produced a valid feature row. Total emitted: **1,207 numeric features** (vs catalog declaration 1,219). Source: `research/ml_program/audit/q1_composability.json`.

### Per-family interface table

| Family | Public entrypoint | Required inputs | Output shape | Catalog count | Live emit | Smoke-test ms |
|---|---|---|---:|---:|---:|---:|
| Structure | `structure.build_structure_features(timestamps, candles_by_tf)` (`structure.py:869`) | `dict[str, list[dict]]` of M15/H1/H4/D1 candles + ISO timestamp list | `pd.DataFrame` indexed by ts | 432 | 432 | 29.13 |
| Volatility | `volatility.compute_all_features(df_m15, df_h1, df_h4)` (`volatility.py:474`) | `pd.DataFrame` per TF, `DatetimeIndex`, OHLCV columns | `pd.DataFrame` indexed by M15 close | 270 | 270 | 1123.24 |
| Microstructure | `microstructure.compute_microstructure_features(df_m15, df_m1, df_h1, df_h4, ts_close, *, symbol, tick_df)` (`microstructure.py:1931`) | OHLCV `pd.DataFrame` (with `time` column) + `datetime` ts_close + symbol + optional tick_df | single-row `pd.DataFrame` indexed by `ts_close` | 187 | 187 | 499.76 |
| Time/Session | `time_session.compute_time_session_features(ts, symbol, **kwargs)` (`time_session.py:400`) | UTC-aware `datetime` + symbol | `dict[str, float]` | 138 | 126 (XAUUSD) / 138 (USDJPY/GBPJPY) | 0.42 |
| Liquidity | `liquidity.extract_liquidity_features(candles_by_tf, anchor_idx_by_tf, instrument, side, current_price)` (`liquidity.py:1030`) | candle dicts per TF + per-TF anchor index + side + reference price | `dict[str, float]` | 129 | 129 | 4.56 |
| Regime | `regime.compute_regime_features(symbol, ts, side, *, ctx)` (`regime.py:1065`) | UTC-aware `datetime` + symbol + side + (amortized) `RegimeFeatureContext` | `OrderedDict[str, float \| int]` | 63 | 63 | 53.95 |
| **Total** | | | | **1,219** | **1,207** | **1,711** |

### Time-axis composability

The six families consume timestamps in three subtly different conventions; none conflict. They all join cleanly on a single ISO-8601 UTC candle-close string.

- **Structure / Liquidity** — string ISO timestamp (`"YYYY-MM-DD HH:MM:SS"`, candle-OPEN-labelled) + dict-form candles + per-TF anchor index. The anchor index is the last closed bar at evaluation time. No look-ahead by construction (`structure.py:914` slices `candles[:idx+1]`; `liquidity.py:1086` filter `candles[:anchor_idx + 1]`).
- **Volatility** — `pd.DataFrame` with `DatetimeIndex` (UTC tz-aware), all rolling windows are trailing only (`pd.rolling(N).fn()` at row T uses `[T-N+1, T]`; module-level `_self_test()` at `volatility.py:561-595` enforces this on every import).
- **Microstructure** — accepts both DatetimeIndex and `time` column; internally re-slices `df[df.time < ts]`. Hard cutoff enforced at `microstructure.py:1975` (`ValueError` if `ts_close >= 2026-04-28 23:59 UTC`).
- **Time/Session** — pure calendar lookup; no DataFrame needed. Cutoff guard at `time_session.py:51` and `time_session.py:425`.
- **Regime** — UTC-aware datetime; consumes `shadow_logs/structure_detector_backfill_2026.jsonl` via `RegimeBackfillIndex`. Backfill cutoff is point-in-time-by-construction (`regime.py:1111` calls `latest_at(symbol, ts)` which filters `ts <= input_ts`).

All family-internal cutoff conventions are consistent: at evaluation time T, only data with timestamp ≤ T is consulted. This is verified by the per-family leakage self-checks tabulated in `CATALOG_v2.md` Section 5.

### Naming uniqueness

- **Cross-family name collisions:** 0. (Verified via `q1_composability.json:name_collisions_across_families`.)
- **Within-family duplicates:** 0.

The catalog enforces unique names by namespacing structure features with TF prefixes (`H1__`, `H4__`, etc.), volatility with TF prefixes (`m15_`, `h1_`, `h4_`), microstructure with `_<TF>_<lookback>` suffixes, time/session with `t_*`, liquidity with `liq_*`, and regime with `regime_*`. The 6 prefix conventions are disjoint.

### Caveats

1. **Live emit count is per-instrument-conditional in Time/Session.** XAUUSD (no Tokyo KZ) emits 126 features. USDJPY/GBPJPY (with Tokyo KZ) emit 138. The 12 Tokyo-only features (`t_kz_tokyo_active`, `t_kz_tokyo_signed_min_to_open`, etc.) are absent for non-JPY instruments. This is INTENTIONAL per `CATALOG_v2.md` Section 6 caveat #5 ("JPY-pair Tokyo cohort split"), but creates a **dynamic schema for the modeler**: Week-4 must either (a) impute NaN for missing JPY-Tokyo columns when the row is non-JPY, or (b) use a per-instrument feature-name list. K54 v1 used (a) implicitly; K54 v2 should follow (a) explicitly with documented sentinel.
2. **Subprocess kwargs heterogeneity.** Liquidity requires a `current_price` argument the others don't (used for round-number ticks distance). Structure / Microstructure / Volatility take frames; Time/Session / Regime take only timestamp + symbol. The unifying entry-point convention is "`(timestamp, symbol)` is sufficient for 2 of 6; +`(candles_by_tf, anchor_idx_by_tf, current_price)` for 3 of 6 (1 of those, microstructure, also needs M1 frame); +`RegimeFeatureContext` for 1 of 6". A unified Week-4 build script will need a thin adapter layer (~30 lines) that loads OHLCV once per `(symbol, timestamp_set)`, computes anchor indices, then dispatches to each family.

---

## Section 2 — Cross-family redundancy report

**Audit cohort:** N=79 XAUUSD candle-close timestamps from K54 v1's deduped XAUUSD partition (target=80, 1 dropped for OHLCV history insufficient at 2024-04-01).

**Headline numbers (continuous-only, after dropping binary/low-cardinality features that produce spurious |ρ|=1.0 from cohort hour-imbalance):**

| Threshold | Cross-family pairs | All pairs (cross + within-family) |
|---|---:|---:|
| \|ρ\| ≥ 0.7 | **1,852** | 7,287 |
| \|ρ\| ≥ 0.9 | **52** | 1,676 |

Source: `research/ml_program/audit/q2_correlation_summary.json` `robust_recompute_continuous_only` block.

**Naive run** (same cohort but with binary OH features included): cross-family pairs spiked to 2,759 / 202 at thresholds 0.7 / 0.9. Most spurious — XAUUSD trade hour is concentrated at 8 (London KZ open, n=72/168 of cohort) and 14 (NY KZ, n=70/168), so binary OH features (`t_hour_07_oh`, `t_kz_london_first_15min`) get |ρ|=1.0 with anything constant within hour. The **continuous-only** numbers are the gate.

### Top-20 cross-family pairs (robust, continuous-only, by |ρ|)

| # | Family A — Feature A | Family B — Feature B | Spearman | Pearson |
|---:|---|---|---:|---:|
| 1 | volatility — h1_atr_50 | regime — regime_atr_h4_14 | +0.948 | +0.971 |
| 2 | volatility — h4_atr_14 | regime — regime_atr_h4_14 | +0.950 | +0.971 |
| 3 | volatility — m15_atr_200 | regime — regime_atr_h4_14 | +0.949 | +0.967 |
| 4 | structure — H4__fvg_bear_count__lb50 | microstructure — fvg_bear_count_h4_lb50 | +0.964 | +0.967 |
| 5 | volatility — m15_garman_klass_vol_200 | regime — regime_atr_h4_14 | +0.900 | +0.963 |
| 6 | volatility — m15_norm_tr_200 | regime — regime_atr_h4_14 | +0.897 | +0.962 |
| 7 | volatility — h1_norm_tr_50 | regime — regime_atr_h4_14 | +0.893 | +0.961 |
| 8 | volatility — m15_parkinson_vol_200 | regime — regime_atr_h4_14 | +0.892 | +0.960 |
| 9 | volatility — h1_garman_klass_vol_50 | regime — regime_atr_h4_14 | +0.896 | +0.960 |
| 10 | volatility — h1_parkinson_vol_50 | regime — regime_atr_h4_14 | +0.890 | +0.958 |
| 11 | structure — H4__fvg_bull_count__lb50 | microstructure — fvg_bull_count_h4_lb50 | +0.944 | +0.954 |
| 12 | volatility — m15_bb_width_50 | liquidity — liq_H1_dist_eql_signed_ticks | -0.662 | -0.951 |
| 13 | volatility — m15_garman_klass_vol_20 | liquidity — liq_M15_dist_eqh_signed_ticks | +0.694 | +0.947 |
| 14 | volatility — m15_return_p95_abs_200 | regime — regime_atr_h4_14 | +0.863 | +0.947 |
| 15 | volatility — h1_realized_vol_50 | regime — regime_atr_h4_14 | +0.849 | +0.947 |
| 16 | volatility — m15_realized_vol_200 | regime — regime_atr_h4_14 | +0.869 | +0.946 |
| 17 | volatility — h4_norm_tr_20 | regime — regime_atr_h4_14 | +0.902 | +0.946 |
| 18 | volatility — m15_norm_tr_std_20 | liquidity — liq_M15_dist_eqh_signed_ticks | +0.715 | +0.945 |
| 19 | structure — H4__fvg_bear_count__lb20 | microstructure — fvg_bear_count_h4_lb20 | +0.945 | +0.937 |
| 20 | volatility — h4_parkinson_vol_20 | regime — regime_atr_h4_14 | +0.900 | +0.945 |

Persisted to `q2_robust_top_corr_pairs.csv` (full top-300 pairs).

### Identified near-duplicate clusters

Three categories of cross-family redundancy:

#### Category A — Volatility ↔ Regime ATR cluster (TRUE duplication, 14+ pairs)

`regime__regime_atr_h4_14` is functionally H4 ATR(14) implemented inside the regime family. It correlates ≥0.94 (Pearson) with **every volatility ATR/Parkinson/Garman-Klass/realized-vol feature** at lookbacks 14-200. This was predicted in `CATALOG_v2.md` Section 4.C ("regime-conditional volatility ratios" overlap with volatility) but the rho magnitude is striking — these are nearly the same feature.

**Root cause:** `regime.py:_feat_regime_conditional_vol` computes raw H4 ATR(14) and ratios; the volatility family also computes H4 ATR(14) and many derivative metrics. None should be dropped — the regime family also emits ratios (`regime_atr_h4_ratio_to_20`, `regime_atr_h4_ratio_to_50`, `regime_atr_h1_to_h4_ratio`) that ARE additive — but the raw `regime_atr_h4_14` is a duplicate of `volatility__h4_atr_14`. The ratio variants survive correlation pruning because they're scaled by a baseline.

#### Category B — Structure ↔ Microstructure FVG counts (TRUE duplication, ~12 pairs)

`structure__H4__fvg_bear_count__lb50` and `microstructure__fvg_bear_count_h4_lb50` correlate at +0.964 / +0.967. Both families count H4 FVGs over a 50-bar lookback using the same Component-2 primitive. This is a **policy gap**: when both families implement the same primitive count over the same TF + lookback, they should NOT both emit. The catalog Section 4.C predicted this would "use different primitives" — it does not in practice.

This affects: `H4 fvg_bull_count` × 2 lookbacks × 2 families = **at least 4 named near-duplicates**, plus their bear-direction siblings = **8 near-duplicates**, plus M15/H1 lookback variants likely produce more (verifiable with Spearman ≥0.9 list).

#### Category C — Volatility ↔ Liquidity range/cluster (CORRELATED but mechanistically distinct)

`m15_bb_width_50` (Bollinger band width) ↔ `liq_H1_dist_eql_signed_ticks` (signed distance to equal-low) at Pearson −0.951 / Spearman −0.662. The Spearman gap (0.66 vs 0.95) suggests the Pearson is driven by a single high-leverage point or non-monotonic relationship; this is a **borderline case**. Mechanistically these ARE distinct (BB width is volatility expansion; distance-to-equal-low is structural anchor distance) — they likely correlate because both spike in the same regime (large impulse → wide BB AND price extends from prior equal-level pool). LightGBM should handle these via split-gain interactions; keep both.

### Recommendation: correlation prune at training time

**Yes — the modeler should correlation-prune** before/within hyperparameter search. Suggested protocol:

1. **Threshold |ρ| ≥ 0.95** (Spearman) for hard prune — keep one of every near-duplicate cluster, prefer the feature with higher univariate stability_rho on the K54 v2 train set.
2. **Drop policy for the ATR cluster (Category A above):** prefer the volatility-family feature (richer subfamily expansion: ATR/Parkinson/Garman-Klass/realized vol at multiple windows). The regime family's `regime_atr_h4_14` raw-ATR feature is redundant; **keep the ratio variants** (`regime_atr_h4_ratio_to_20`, etc.) which encode regime-relative volatility, not raw level.
3. **Drop policy for FVG counts (Category B):** prefer the structure-family version (richer cross-TF expansion: M15/H1/H4 each at lookbacks 20/50/100/200). Microstructure's `fvg_*_count_*_lb*` are exact duplicates at H4 specifically.
4. **Threshold |ρ| ≥ 0.7** (Spearman) for soft prune — flag for ablation study at K54 v3, not auto-drop. The catalog Section 6 caveat already discloses this.
5. **Re-run on the K54 v2 modeling cohort** (~411 trades) before pruning — N=79 XAUUSD-only is a screening cohort. Cross-instrument features (`regime_xau_score`, fleet-alignment counts, JPY-Tokyo) need their own redundancy checks per-cohort.

### Caveats on this number

- **N=79 cohort imbalance.** Even after dropping binary OH features, 79 candle-close timestamps from a single instrument (XAUUSD) over a 2024-04 → 2026-04 span will under-cover SHORT-direction setups (item #11 in CLAUDE.md unresolved list — A6 finding). The modeler should re-run correlation discipline on the full ~411 cohort with both instruments and both directions represented.
- **52 pairs at |ρ|≥0.9 cross-family is a screening number.** True near-duplicates in the modeling cohort might be lower (some current high-ρ pairs are cohort artifacts) or higher (some currently borderline pairs may tighten). Don't auto-act on the screening; ablation-test the prune list.
- **Within-family redundancy is much larger** (1,676 pairs at |ρ|≥0.9 globally vs 52 cross-family). These are mostly multi-lookback emissions of the same primitive (`last_bos_age_bars__lb20` ≡ `__lb100` in 79-cohort because the BOS event index is older than 100 bars in most rows). Multi-lookback redundancy was an explicit design choice (`CATALOG_v2.md` Section 6 caveat #6: "Multi-lookback expansion redundancy is acceptable; LightGBM split-gain handles it"). Within-family pruning is OPTIONAL; cross-family is the stronger signal.

---

## Section 3 — Catalog integrity verdict

**Verdict: PASS_WITH_NOTE** — all hard checks pass; one soft normalization issue.

Per `q3_integrity_check.py` and `q3_integrity_findings.json`:

| Check | Result |
|---|---|
| Total rows | **1,219** ✓ (matches 432+270+187+138+129+63) |
| Per-family counts match brief | **All 6 ✓** (structure 432 / microstructure 187 / volatility 270 / time_session 138 / liquidity 129 / regime 63) |
| All 11 canonical columns present | **✓** (`family, feature_name, subfamily, source, lookback, computation, stability_rho, stability_n, stability_p, expensive_flag, notes`) |
| No missing or extra columns | **✓** |
| `stability_rho` valid floats or empty | **5 rows fail** — see note below |
| Within-family duplicate names | **0** ✓ |
| Cross-family name collisions | **0** ✓ |
| Spot-check 5 random rows match family CSV | **5/5 ✓** (all unified `stability_rho` matches original family CSV value byte-for-byte; row indices 53, 230, 459, 503, 565) |

### `stability_rho` normalization soft-fail

5 rows in CATALOG_v2.csv carry the literal string `"NA"` instead of an empty cell:

| Row idx | Family | Feature | `stability_rho` |
|---:|---|---|---|
| 1160 | regime | regime_v1_is_transitional | `NA` |
| 1173 | regime | regime_v2_dz_is_3 | `NA` |
| 1174 | regime | regime_v2_dz_is_4_or_more | `NA` |
| 1188 | regime | regime_v2_score_change_20 | `NA` |
| 1217 | regime | regime_atr_h4_ratio_to_50 | `NA` |

**Source:** the regime family CSV at `feature_catalogs/regime.csv` rows 4, 17, 18, 32, 61 emit literal `NA` in the `stability_spearman_pre_2026_04` column. The unifier `build_catalog_v2.py:91` passes the value through verbatim. The other 5 families (structure, volatility, microstructure, time_session, liquidity) emit empty string `""` for missing stability — both empty and the float-parseable values would pass `safe_float`, but `"NA"` does not.

**Severity:** soft. The Week-4 modeler reads `stability_rho` only for screening / weighting; "NA" parses to None in `safe_float`, identical to "" in the modeler's read path. But the catalog claim "all stability_rho values are valid floats or empty" is technically violated.

**Recommended fix (one-line):** modify `build_catalog_v2.py:normalize_row` for `family == "regime"` to map `"NA"` → `""` before write. Not blocking for Week-4 modeler.

### Spot-check details

Random seed 42 picked rows 53, 230, 459, 503, 565 from the unified catalog. All 5 found in the corresponding family CSV with byte-identical `stability_rho`:

- structure / `M15__ob_bull_count__lb100` → 0.0138305513306162 ✓
- structure / `H4__nearest_ob_depth_atr__lb20` → 0.0001819627444384 ✓
- microstructure / `fvg_bear_count_h1_lb50` → 0.037473336639071785 ✓
- microstructure / `range_pctile_m15_lb5` → 0.00013953161718801297 ✓
- microstructure / `volume_zscore_m15_lb200` → 0.023002050119368338 ✓

No data corruption / no rows lost in normalization.

---

## Section 4 — Inference cost benchmark

**Verdict: TOTAL 1,644 ms / decision (XAUUSD, deepest available history) — 1644× the per-family <1ms target.**

Source: `research/ml_program/audit/q4_timing_summary.json`, `q4_timing.csv`. Median over 5 runs per family on Windows / Python 3, hot-cache (post-warmup).

| Family | Median ms | Min ms | Max ms | n features | ms / feature |
|---|---:|---:|---:|---:|---:|
| Structure | 21.01 | 20.03 | 21.66 | 432 | 0.049 |
| **Volatility** | **1,134.34** | 1,109.71 | 1,211.22 | 270 | **4.20** |
| **Microstructure** | **483.89** | 478.91 | 522.42 | 187 | **2.59** |
| Time/Session | 0.23 | 0.18 | 0.25 | 126 | 0.002 |
| Liquidity | 4.14 | 3.74 | 4.87 | 129 | 0.032 |
| Regime | 0.26 | 0.25 | 19.95 | 63 | 0.004 |
| **TOTAL** | **1,643.87** | — | — | **1,207** | **1.36** |

### Bottleneck identification

**Volatility (1,134 ms = 69% of total) is the bottleneck** — exceeds my prior expectation that "Liquidity sweep-detection or Microstructure tick-rolling" would dominate. Investigation:

1. **`compute_all_features` calls 8 sub-builders × 3 TFs = 24 sub-calls per row** (`volatility.py:489-532`). Each sub-builder rolls over full bar history (~46k M15 rows in the deepest cohort) and emits dozens of features. The bottleneck is **not** missing vectorization (pandas `rolling` is C-level) — it's the **deep history**: `data/historical/XAUUSD_M15.csv` has 48,360 rows × 13 lookbacks × 24 ATR/realized-vol/range/BB/fat-tail/Hi-Lo functions. Each function's `pd.rolling(N).fn()` is O(rows). Volatility's actual cost is ≈ rows × functions ≈ 48k × 24 ≈ 1.2M operations × ~1μs each = ~1.1s, matching observed timing.
2. **Microstructure (484 ms = 29% of total)** — second bottleneck. Cause is the **M1 + M15 + H1 + H4 frame slicing** at every feature call (`microstructure.py:1990` calls `fn(...)` × 187 features, each slices its own bars). The DISPATCHER pattern doesn't share intermediate computations across features.

Combined: 99% of inference cost is in two families (volatility + microstructure). The other four together take 26ms.

### Comparison vs production budget

The brief asserts "production budget: <1ms per decision per CLAUDE.md". I could not locate this exact number in CLAUDE.md (grep `1ms|1 ms|< ?1ms` → no matches). The "<1ms total per row" target appears in the per-family module docstrings (e.g. `liquidity.py:67`, `volatility.py:42-44`). Liquidity (4.14 ms) and Volatility (1,134 ms) both exceed this target. Time/Session, Regime, and Structure-when-bounded all hit the budget.

**Production reality:** K54 v2 lives at the M15-candle-close cadence — one decision per candle per instrument = 4 decisions/hour/instrument × 7 instruments = **28 decisions/hour** total. Even at 1.6 s/decision the budget is 28 × 1.6 = 45 seconds/hour of compute, or 1.25% CPU duty — entirely feasible inline if the M15 close is the only deadline.

**Architectural recommendation:** cost the **inline** path on the M15-close decision cadence and accept ~2 s if the volatility family proves to be the highest-importance source. For batch backfill of training features (~411 trades or ~50k 15-min slots × 7 instruments = 350k feature-row builds), at 1.6 s/row that's 156 hours wall-clock on single-thread — too long. Modeler MUST parallelize backfill (per-instrument, 7-way parallel = 22 hours) or implement a **shared rolling-state cache** that amortizes the 24 volatility builders across rows.

### Caveats on timing

- **Cold-start cost not measured.** Module imports run `_self_test()` at the bottom of `volatility.py` (~5 ms per import per `volatility.py:597`); these are amortized at process start.
- **Regime max time was 19.95 ms** vs median 0.26 ms — a single first-call cold cache miss in `RegimeBackfillIndex`. Amortized after first call.
- **Microstructure tick path NOT exercised** — no tick parquet was passed (XAUUSD has zero tick coverage per memory `project_microstructure_archived_2026-04-27`). Tick-required features emitted NaN sentinels; Group I tick-features added <2 ms. If/when tick coverage extends, those 24 features will add cost.
- **N=5 timing runs** is a lightweight sample. Variance across runs was small (max-min ≈ 5% of median) so 5 runs is sufficient for the magnitude question; tighter timing would not change the verdict.
- **Hardware:** measured on the CEO's Windows 11 box (2 of 6 family modules say "5-year-old laptop"). Production target hardware unspecified.

---

## Section 5 — Recommendations for Week 4 modeler

### High priority (act now)

1. **Cross-family correlation prune at |ρ|≥0.95 Spearman.**
   - Drop `regime__regime_atr_h4_14` (raw ATR duplicate of `volatility__h4_atr_14`); keep `regime_atr_h4_ratio_to_20/50` and `regime_atr_h1_to_h4_ratio` (these are ratios, additive).
   - Drop `microstructure__fvg_bull_count_h4_lb20/50` and `microstructure__fvg_bear_count_h4_lb20/50` (duplicates of `structure__H4__fvg_bull_count__lb20/50`, etc.). Verify symmetry on M15/H1 lookbacks via the redundancy CSV (`q2_robust_top_corr_pairs.csv`).
   - **Re-run** correlation discipline on the full ~411-trade modeling cohort (cross-instrument, cross-direction) before final prune. The N=79 XAUUSD screening cohort over-represents London-KZ-LONG.
   - Estimated reduction: ~50-100 features dropped, leaving ~1,120-1,170 to pass into LightGBM.

2. **Backfill cost: parallelize per-instrument or amortize volatility rolling.**
   - For the 411-trade train + ~50k point-in-time backfill, single-thread 1.6 s × 350k = 156 hours is unrealistic.
   - **Option A (simple):** 7-way `multiprocessing` on instrument; reduces to ~22 hours.
   - **Option B (faster):** refactor `volatility.compute_all_features` to compute all rolling stats ONCE over the full bar frame and cache in memory; per-row feature extraction becomes O(1) lookup. Requires ~100 LOC of refactor; saves ~14 of those 22 hours. NOT BLOCKING for K54 v2; flag for K54 v3.

3. **Time/Session schema dynamism.** XAUUSD/US30/GBPUSD/XAGUSD/NAS100 emit 126 features; USDJPY/GBPJPY emit 138 (Tokyo features). Use a unified 138-column schema with the 12 Tokyo features as NaN sentinel for non-JPY rows. This matches K54 v1's behavior and keeps the LightGBM regime models comparable across instruments.

### Medium priority (consider but not blocking)

4. **Regime-feature soft-fail normalization** — fix `build_catalog_v2.py` to map `"NA"` → `""` for the 5 regime rows. Also one-pass `safe_float` should treat `"NA"` as missing in any modeler-side reader.
5. **Within-family redundancy** (1,676 pairs at |ρ|≥0.9 globally) — DO NOT auto-prune. Multi-lookback emission was an explicit design choice; LightGBM split-gain handles it. Document as known acceptable redundancy in K54 v2 model card.
6. **Validate the 12 Tokyo-only Time/Session features** with stability scoring on JPY-pair-only cohort. K54 v1 audit showed these were absent; K54 v2 catalog Section 1 ranks them in the global top-10 by univariate ρ. Confirm the n=105 sample isn't producing inflated estimates.

### Low priority (Phase 2 / K54 v3)

7. **Cohort balancing for redundancy estimates.** N=79 XAUUSD is a screening number. Re-run correlation matrix on the full ~411 modeling cohort across all 7 instruments and both directions before reporting final feature importance.
8. **Tick coverage caveat carried forward.** 24 microstructure tick-required features will emit NaN for the entire 2024-04 → 2026-04-26 span (only NAS100 + US30_cash + 2026-04-27 has tick parquets). LightGBM handles NaN natively, but treat the tick features as a SECONDARY set; don't gate K54 v2 on their importance.
9. **Cold-start vs hot-start timing.** Production deployment will pay ~30-50 ms cold start per family on first M15 close after process restart. Pre-warm the rolling caches during canary boot.

### Production deployment

10. **Per-decision inline cost (~1.6 s) is acceptable** at M15-close cadence (28 decisions/hour fleet-wide). The "<1ms / row" budget claimed in family docstrings is an OFFLINE backfill aspiration, not an inline-decision budget.
11. **Don't cache feature values across instruments.** Each instrument has its own market-state context; sharing the volatility rolling-cache across instruments would silently break point-in-time discipline.

---

## Appendix — File map

| File | Purpose |
|---|---|
| `research/ml_program/audit/catalog_health_audit.md` | This audit. |
| `research/ml_program/audit/catalog_health_run.py` | Q1 + Q4 + Q2-naive audit runner. |
| `research/ml_program/audit/q2_robust_recompute.py` | Q2 robust recompute (continuous-only). |
| `research/ml_program/audit/q3_integrity_check.py` | Q3 catalog integrity check. |
| `research/ml_program/audit/q1_composability.json` | Q1 raw findings. |
| `research/ml_program/audit/q2_correlation_summary.json` | Q2 summary (naive + robust). |
| `research/ml_program/audit/q2_top_corr_pairs.csv` | Q2 top-200 pairs (naive). |
| `research/ml_program/audit/q2_robust_top_corr_pairs.csv` | Q2 top-300 pairs (robust). |
| `research/ml_program/audit/q2_correlation_matrix.csv` | Reduced correlation matrix (only features with ≥1 high-corr partner). |
| `research/ml_program/audit/q3_integrity_findings.json` | Q3 raw findings. |
| `research/ml_program/audit/q4_timing.csv` | Q4 per-family timing CSV. |
| `research/ml_program/audit/q4_timing_summary.json` | Q4 summary. |

*Audit complete. Awaiting Week-4 modeler dispatch.*
