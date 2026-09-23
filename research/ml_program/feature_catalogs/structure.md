# STRUCTURE feature family — K54 v2

**Owner:** Q1 Week 2-3 feature engineer (structure family).
**Module:** `research/ml_program/scripts/features/structure.py`.
**Catalog CSV:** `research/ml_program/feature_catalogs/structure.csv`
(machine-readable; one row per feature).
**Stability scores:** `research/ml_program/feature_catalogs/structure_stability.csv`
(Spearman ρ vs realized R, computed on the K54 v1 train+val cohort).

## 1. What this family covers

ICT-style market-structure primitives derived from `src/components/market_state.py`
(Component 2). Built layer by layer:

* **Active Order Block geometry** — count, depth, age, retest count,
  nearest-OB signed distance, type. Per-TF and per-lookback.
* **Active Fair Value Gap geometry** — count, size, age, fill ratio,
  retest count, nearest-FVG signed distance. Per-TF and per-lookback.
* **Breaker Block geometry** — depth, distance, age, retest flag,
  original-OB direction. Per-TF.
* **Swing magnitudes** — last swing leg range/velocity, swing counts,
  max consecutive up/down legs, swing dispersion, age of last
  high/low. Per-TF and per-lookback.
* **BOS / CHoCH events** — counts, displacement-present count, mean
  displacement ratio, age of last event, last-event-was-BOS flag.
  Per-TF and per-lookback.
* **Distance-to-internal-swing** — distance to nearest swing high
  and low (ATR units) and the enclosing swing-band width. Per-TF.
* **Pre-BOS impulse-leg geometry** — impulse range / ATR, bar count,
  ratio of impulse range to OB depth, bullish-candle ratio, max
  displacement ratio across the leg, pre-impulse consolidation bar
  count. M15 + H1 only (these are where the BOS event actually fires
  in the production pipeline).
* **Multi-timeframe alignment** — direction encoded as +1/0/-1 per
  TF, all 6 pairwise agreement flags, total agreement count, signed
  4-TF score, all-aligned-bull and all-aligned-bear flags.

Total feature count: **432**. Family-level breakdown:

| Sub-family | Count |
|---|---:|
| `structure_ob` (Order Blocks) | 105 |
| `structure_fvg` (Fair Value Gaps) | 91 |
| `structure_swing` (Swings) | 84 |
| `structure_event` (BOS / CHoCH) | 70 |
| `structure_bb` (Breaker Blocks) | 44 |
| `structure_mtf_alignment` | 14 |
| `structure_distance_to_swing` | 12 |
| `structure_impulse` | 12 |

Lookback grid:

| TF | Lookback windows (candles) |
|---|---|
| M15 | 20, 100 |
| H1 | 20, 100 |
| H4 | 20, 50 |
| D1 | 50 |

Breaker-block primitives are emitted only at lookbacks ≥ 50 (BBs are
inherently rarer than OBs; small lookbacks return empty too often to
be useful).

## 2. Feature naming convention

Features use one of three name shapes:

```
<TF>__<primitive>__lb<N>          # per-TF, per-lookback
<TF>__<primitive>                  # per-TF, no lookback (e.g. distance-to-swing, impulse leg)
<primitive>                        # top-level (MTF alignment vector)
```

Examples: `H1__nearest_ob_signed_atr__lb100`,
`M15__impulse_range_atr`, `mtf_agreement_count`.

## 3. Source data + computation rules

All features derive from OHLCV CSVs in `data/historical_2026/` —
one CSV per symbol-TF pair, columns `time, open, high, low, close,
volume`. Time is candle-OPEN, UTC-naive (function localises to UTC).

For each candle close to be featurized:

1. Slice each TF's history at `candles[time <= ts]`. **No future
   candles ever enter the computation.**
2. Cap context to ≤250 bars per TF (D1 is capped at 80) to bound
   detector runtime.
3. Run `Component 2` primitives on the slice:
   `detect_swings → identify_structure → detect_structure_breaks →
   identify_order_blocks → identify_breaker_blocks → identify_fvgs`,
   then call `_count_touches` on every OB to populate `touch_count`
   point-in-time.
4. Extract aggregate features from the cached state at each
   lookback window.

## 4. Per-feature documentation

Detailed per-feature documentation is in `structure.csv` (column
`computation_summary`). The table below lists primitives once;
multiply by the lookback grid for the full CSV row count.

### 4.1 Order Block primitives (per `<TF>__<primitive>__lb<N>`)

| Primitive | Description | Range / Units |
|---|---|---|
| `ob_count` | Active OBs in window. | int ≥ 0 |
| `ob_bull_count` / `ob_bear_count` | Active OBs by type. | int ≥ 0 |
| `ob_unmitigated_count` / `ob_mitigated_count` | Component-2 mitigation flag breakdown. | int ≥ 0 |
| `ob_breaker_count_in_window` | Breaker blocks formed in window. | int ≥ 0 |
| `ob_mean_depth_atr` | Mean (high-low)/ATR across active OBs. | float, ATR-units |
| `ob_mean_age_bars` | Mean (last_idx - formation_index). | float, bars |
| `ob_max_touch_count` | Max retest count among active OBs. | int ≥ 0 |
| `nearest_ob_dist_atr` | \|close - mid\| / ATR for nearest OB. | float, ATR-units |
| `nearest_ob_signed_atr` | (close - mid) / ATR. | float, ATR-units (signed) |
| `nearest_ob_depth_atr` | (high-low)/ATR for nearest OB. | float, ATR-units |
| `nearest_ob_age_bars` | Bars since formation. | int ≥ 0 |
| `nearest_ob_touch_count` | Retests of nearest OB up to current candle. | int ≥ 0 |
| `nearest_ob_is_bullish` | 1 if bullish, 0 if bearish. | binary |

### 4.2 FVG primitives

| Primitive | Description | Range / Units |
|---|---|---|
| `fvg_count`, `fvg_bull_count`, `fvg_bear_count` | Counts in window. | int ≥ 0 |
| `fvg_filled_count` / `fvg_unfilled_count` | Fill-status breakdown. | int ≥ 0 |
| `fvg_mean_size_atr` | Mean (top-bottom)/ATR. | float |
| `nearest_fvg_dist_atr` | \|close - midpoint\| / ATR. | float |
| `nearest_fvg_size_atr` | Size in ATR-units. | float |
| `nearest_fvg_age_bars` | Bars since formation. | int ≥ 0 |
| `nearest_fvg_fill_ratio` | Fraction of FVG range consumed by post candles. | [0, 1] |
| `nearest_fvg_retest_count` | Bars overlapping FVG zone after formation. | int ≥ 0 |
| `nearest_fvg_is_bullish` / `nearest_fvg_is_filled` | Boolean flags. | binary |

### 4.3 Breaker Block primitives (LB ≥ 50 only)

| Primitive | Description |
|---|---|
| `bb_count`, `bb_bull_count`, `bb_bear_count`, `bb_retested_count` | Counts. |
| `nearest_bb_dist_atr` / `nearest_bb_signed_atr` | Distance to nearest BB (unsigned & signed, ATR-units). |
| `nearest_bb_depth_atr` | (zone_high - zone_low) / ATR. |
| `nearest_bb_age_bars` | Bars since formation. |
| `nearest_bb_is_retested` / `nearest_bb_orig_was_bullish` / `nearest_bb_is_bullish` | Booleans. |

### 4.4 Event primitives (BOS / CHoCH)

| Primitive | Description |
|---|---|
| `bos_count`, `choch_count`, `bos_bull_count`, `bos_bear_count` | Counts. |
| `displacement_present_count` | Events with body/avg_body ≥ 1.5. |
| `mean_displacement_ratio` | Mean event.displacement_ratio. |
| `last_bos_age_bars` / `last_choch_age_bars` | Bars since most recent event. |
| `last_event_was_bos` / `last_event_displaced` | Booleans of latest event. |

### 4.5 Swing primitives

| Primitive | Description |
|---|---|
| `swing_high_count`, `swing_low_count`, `swing_total_count` | Counts. |
| `swing_high_ratio` | high / total. |
| `last_swing_range_atr` | abs(last_high.price - last_low.price) / ATR. |
| `last_swing_leg_bars` | abs(last_high.index - last_low.index). |
| `last_swing_velocity_atr_per_bar` | Range / leg_bars normalised by ATR. |
| `max_up_leg_atr` / `max_down_leg_atr` | Max consecutive same-type swing diff, ATR units. |
| `last_high_age_bars` / `last_low_age_bars` | Bars since latest extreme. |
| `swing_dispersion_atr` | (max - min swing prices) / ATR. |

### 4.6 Distance-to-internal-swing (no lookback)

| Primitive | Description |
|---|---|
| `dist_to_nearest_swing_high_atr` / `dist_to_nearest_swing_low_atr` | min(\|close - swing.price\|) / ATR. |
| `dist_to_swing_band_atr` | \|nearest_high - nearest_low\| / ATR. |

### 4.7 Pre-BOS impulse-leg geometry (M15 + H1 only, no lookback)

Computed only when at least one OB and one BOS event are visible in
the candle slice. The "leg" is `candles[ob.formation_index ..
bos.candle_index]`.

| Primitive | Description |
|---|---|
| `impulse_range_atr` | (leg_high - leg_low) / ATR. |
| `impulse_bar_count` | Length of leg in bars. |
| `impulse_to_ob_depth_ratio` | impulse_range / ob_depth. |
| `impulse_bull_candle_ratio` | Fraction of leg candles with close>open. |
| `impulse_max_displacement_ratio` | max(\|c.close-c.open\| / avg_body) across leg. |
| `impulse_pre_consolidation_bars` | Walk back from OB; count consecutive bars with TR/ATR < 0.7. Cap=50. |

### 4.8 Multi-timeframe alignment vector (top-level, no TF prefix)

| Feature | Range |
|---|---|
| `dir_M15`, `dir_H1`, `dir_H4`, `dir_D1` | +1 / 0 / -1 |
| `agree_M15_H1`, `agree_M15_H4`, `agree_M15_D1`, `agree_H1_H4`, `agree_H1_D1`, `agree_H4_D1` | 0 / 1 |
| `mtf_agreement_count` | [0, 6] |
| `mtf_signed_score` | [-4, +4] |
| `mtf_all_aligned_bull` / `mtf_all_aligned_bear` | 0 / 1 |

## 5. Stability scores

Spearman rank correlation of feature value at trade-entry candle
close vs realized R, computed on **F11 mechanical OB-retest
population pre-2026-04** (n=345 filled trades across 7 instruments).

This cohort is the K54 v1 train+val (data ≤2026-03-31) — disjoint
from the locked Q1.2 holdout (2026-04-29 → 2026-05-12).

Top 10 features by |ρ|:

| Feature | ρ | n | p (large-sample) |
|---|---:|---:|---:|
| `H1__impulse_max_displacement_ratio` | +0.266 | 173 | 3e-04 |
| `M15__last_choch_age_bars__lb100` | -0.219 | 78 | 0.050 |
| `M15__last_choch_age_bars__lb20` | -0.219 | 78 | 0.050 |
| `M15__nearest_ob_dist_atr__lb20` | -0.215 | 258 | 4e-04 |
| `H1__mean_displacement_ratio__lb20` | +0.181 | 345 | 6e-04 |
| `H1__impulse_range_atr` | +0.181 | 173 | 0.016 |
| `H1__last_event_displaced__lb20` | +0.167 | 345 | 0.002 |
| `H1__last_event_displaced__lb100` | +0.167 | 345 | 0.002 |
| `H4__ob_mean_age_bars__lb50` | -0.160 | 332 | 0.003 |
| `M15__swing_low_count__lb20` | +0.155 | 345 | 0.004 |

Reading: H1 displacement strength (impulse + recent BOS) and M15
recent CHoCH proximity dominate. Most ρ values fall in the [-0.05,
+0.05] band — typical for high-dimensional feature catalogs at this
sample size. **NaN ρ for a column means: insufficient n (<30 valid),
or variance was zero across the cohort.** Per the brief, NaN-ρ
features are **not dropped**; the modeler decides.

Statistical caveats:

* p-values use a large-sample normal approximation, not a permutation
  test. Treat as approximate.
* No multiple-testing correction (Bonferroni / BH-FDR) is applied at
  the catalog level — this is feature engineering, not hypothesis
  testing. The Week-4 modeler applies discipline.
* Some features have heavy mass at zero (`ob_count` etc.). Spearman
  on ties is conservative but doesn't fully control for the discrete
  nature.
* H1 impulse stability of ρ=0.266 looks promising but n=173 — that's
  the subset of records where a paired (OB, BOS) was found in the H1
  slice. The remainder return NaN, treated as "feature missing."

## 6. Inference cost

Single-row featurization cost on M15/H1/H4/D1 with 250-bar context
caps: **~15 ms per (symbol, candle close)** on the dev box (Windows
11, Python 3.12). Dominant cost is the four `_build_tf_state` calls
(detector pipeline). Per-candle cost is acceptable for batch
training but not sub-millisecond — flag for production: **all
features inherit `expensive_flag=false` in `structure.csv` (none
individually dominates), but the full row-build is non-trivial and
benefits from caching the per-TF detector outputs across rows
sharing the same M15 candle close.**

For online inference, reuse `pipeline_state/02_market_state.json`
which already contains the same Component-2 outputs computed by the
production pipeline; bypass the per-row recomputation.

## 7. Missing data / coverage gaps

* **D1 lookback=50** requires ≥50 D1 candles of history at the
  featurized timestamp. The OHLCV files start 2025-10-01, so any
  timestamp before ~2025-12-20 will return NaN for `D1__*__lb50`
  features. All F11 records are in 2026, so this is benign for the
  K54 v1 train+val cohort.
* **Impulse-leg features** require both an OB and a BOS in the H1
  (or M15) slice. Approximately half of records hit this at H1 (n=173
  for `impulse_*`). For records with no OB-BOS pair on the slice,
  these features are NaN — by design, not a bug.
* **F11 records have BOS times in UTC**; OHLCV CSV `time` is naive
  (interpreted as UTC). The catalog joins on prefix string match, so
  a small risk of off-by-15-minutes if any F11 timestamp doesn't fall
  on an exact M15 candle close. Spot-checks during stability
  computation showed no row-loss; if this changes for a future data
  source, the slice function will silently degrade to "use all
  candles up to ts" which may emit an extra candle. Not a correctness
  bug for trailing-slice features.
* **OHLCV M1 files exist** in the data dir but are NOT used here —
  the structure family operates on M15+. M1 belongs to the
  microstructure family.

## 8. Leakage self-check

Every feature in this family was reviewed for future-data
dependency. The findings:

* **Component-2 `_count_touches`** walks `candles[formation_index+1:
  ]`. We feed it only the slice `candles[:cutoff_idx+1]`, so the
  walk terminates at the featurized candle close. **Safe.**
* **Component-2 `OrderBlock.mitigated`** uses `for k in range(
  break_idx + 1, len(candles))`. Same slice argument; mitigation
  flag reflects only past mitigation visible at the candle close.
  **Safe.**
* **Component-2 `BreakerBlock.is_retested`** uses
  `for k in range(mitigation_idx + 1, len(candles))` on the same
  slice. **Safe.**
* **Component-2 `FairValueGap.filled`** uses `for k in range(i+2,
  len(candles))` on the slice. **Safe.**
* **Component-2 `detect_sweeps`** walks the last 10 candles of the
  slice only; we don't expose sweep features in this family
  (liquidity family owns sweeps), but the underlying call wouldn't
  leak even if we did. **Safe.**
* **`identify_breaker_blocks`** has an inner loop walking
  `candles[start_idx:]` for mitigation detection. With our slice
  argument, `start_idx = causing_bos_index + 1` and `len(candles) =
  cutoff_idx + 1`, so the walk cannot see beyond the featurized
  candle. **Safe.**
* **F11 BOS times are decision times, not exit times.** The
  realized R label comes from a trade that opens at the BOS event.
  We featurize at BOS time, before any of the trade's outcome bars
  enter the slice. **Safe.**
* **Pre-BOS consolidation walk** is a backward walk from
  `ob.formation_index - 1` toward earlier indices. By construction
  past-only. **Safe.**
* **MTF alignment** uses `identify_structure(swings)`, which has no
  forward dependency. **Safe.**

The lookback windows in this catalog are **trailing only** — every
`lookback` parameter sets `cutoff_idx = state.n - 1 - lookback`,
slicing from "lookback bars ago" to the latest candle. There is no
"lookahead window" mode in any primitive.

**Track A trap reminder:** Track A's `walk_level_signal` failure
(see CLAUDE.md item #7) was not look-ahead per se — it was a
walk-survivor proxy that didn't predict realized R. We avoid that
trap entirely here by computing every feature at the candle close
and joining only to realized R from F11 (no walk-level proxies).

## 9. Files

| Path | Purpose |
|---|---|
| `research/ml_program/scripts/features/structure.py` | Reference implementation (`build_structure_features` is the entry point). |
| `research/ml_program/scripts/features/_compute_structure_stability.py` | One-shot stability computer; writes `structure_stability.csv`. |
| `research/ml_program/scripts/features/_build_structure_catalog.py` | Generates `structure.csv` from the live module + stability CSV. |
| `research/ml_program/feature_catalogs/structure.csv` | Machine-readable feature catalog (one row per feature). |
| `research/ml_program/feature_catalogs/structure_stability.csv` | Per-feature Spearman ρ, n, p. |

## 10. Lane discipline

This family is **structure-only**. Features that overlap with
sibling families have NOT been included:

* Volatility — handled by the volatility family (ATR percentiles,
  squeeze flags, vol-of-vol, etc.). We expose ATR-normalised distance
  / depth features but not raw ATR statistics.
* Liquidity — equal-highs/lows, sweep flags, distance-to-pool
  belong to the liquidity family. We do NOT touch
  `LiquidityPool` / `LiquiditySweep` outputs.
* Regime — regime tags, regime-confidence scores, dead-zone flags
  are owned by the regime family.
* Time / session — kill-zone, hour, day-of-week, KZ-position
  features are owned by the time/session family.
* Microstructure — tick-derived order-flow proxies (CLV, BVC, net
  flow) belong to the microstructure family.

**No feature in this catalog reads from tick data, news feeds,
options data, or any external reference series.**

---

*End of structure-family catalog. Generated 2026-04-28. For changes,
update `structure.py` first, then re-run `_compute_structure_stability.py`
followed by `_build_structure_catalog.py`.*
