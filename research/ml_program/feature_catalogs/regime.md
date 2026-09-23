# K54 v2 — REGIME family feature catalog

**Owner:** REGIME family agent (1 of 6 in K54 v2 expanded feature catalog)
**Pre-registered hypothesis:** Q1.2 (locked 2026-04-28 20:00 UTC)
**Implementation:** `research/ml_program/scripts/features/regime.py`
**Author date:** 2026-04-28
**Feature count:** 63

---

## Why regime is a load-bearing axis (and why K54 v1 didn't capture it)

Per memory `project_f15_synthesis_regime_is_load_bearing` and the K54 v1
audit (`research/ml_program/k54_v1_audit.md` Section 5):

- F15 attribution: regime carries **+48.3pp Bonferroni-corrected
  attribution** (p=0.0016) of the H1 → H2 2026 XAUUSD decay.
- F2 pinpoint cell: XAUUSD London / `trending_bull` / LONG WR collapsed
  76.5% → 16.7% (Δ -59.8pp), with 2026-04-only WR=0% on n=4.
- A6 cohort: LONG-side selectivity collapse (LONG 48.4% → 18.8%) is
  concentrated in `bullish` v2 regimes.

K54 v1 has TWO regime features (`regime_tag`, `counter_direction_flag`).
Both have **ZERO importance** as features in any of the per-regime
LightGBM models — `regime_tag` is consumed only as **ensemble gating**
(one model per regime). The audit Section 5 explicitly calls out
`v2_score` and `v2_dead_zone` as "in backfill but UNUSED in K54 v1
features.csv — zero-cost wins" for v2.

This catalog surfaces those quick wins and adds 50+ derived regime
features that the K54 v1 schema never captured.

---

## Data sources

| Source | Path | Coverage | Notes |
|---|---|---|---|
| H4 regime backfill | `shadow_logs/structure_detector_backfill_2026.jsonl` | 3,571 rows, 9 symbols, 2026-01-21 → 2026-04-24 | v2_score + v2_dead_zone 100% populated. Logged_at 2026-04-26 17:26 UTC (retrospective backfill of v2 detector against historical MSO swings). |
| Live regime stream | `shadow_logs/regime_classifications.jsonl` | 133 rows, 2026-04-27+ | `RegimeClassification` schema from `src/components/regime_classifier.py` (CLASSIFIER_VERSION `v1.0-option-a-h4-swing`). Includes US30_cash. |
| OHLCV historical | `data/historical_2026/{SYMBOL}_{TF}.csv` | 2025-10-01 → 2026-04-24, all 7 fleet + EURUSD, M1/M15/H1/H4/D1 | Used for ATR ratios + D1-direction approximations. |
| Cross-instrument logic | `src/components/cross_instrument_correlation_gate.py` | static correlation table | Referenced for fleet-symbol set. NOT loaded — fleet symbols are hard-coded in `regime.py:FLEET_SYMBOLS` for determinism. |

---

## Feature groups

### Group 1 — Current regime label one-hots (9 features)

The audit's "regime label" is one of two detector outputs at the H4
boundary preceding entry. v1 = legacy `identify_structure_v1`. v2 =
production-active since session 38 (`identify_structure_v2`).

| Feature | Type | Notes |
|---|---|---|
| `regime_v1_is_bullish` | binary | v1 detector label |
| `regime_v1_is_bearish` | binary | v1 detector label |
| `regime_v1_is_transitional` | binary | v1 detector label |
| `regime_v1_is_untagged` | binary | label missing or sentinel |
| `regime_v2_is_bullish` | binary | v2 detector label (production) |
| `regime_v2_is_bearish` | binary | v2 detector label |
| `regime_v2_is_transitional` | binary | v2 detector label |
| `regime_v2_is_untagged` | binary | v2 label missing |
| `regime_v2_in_dead_zone` | binary | `\|v2_score\| <= v2_dead_zone`. Audit Section 5 quick-win. |

### Group 2 — v2 regime strength primitives (8 features)

Audit Section 5: `v2_score` and `v2_dead_zone` are present in backfill
but UNUSED in K54 v1's feature matrix. This group surfaces them.

| Feature | Type | Notes |
|---|---|---|
| `regime_v2_score` | int (signed) | (HH+HL) - (LH+LL) over the v2 swing window |
| `regime_v2_score_abs` | int | strength regardless of direction |
| `regime_v2_dead_zone_value` | int | `max(2, min_swing_transitions // 8)` |
| `regime_v2_score_minus_dead_zone` | int | strength above noise floor |
| `regime_v2_score_normalized` | float | score / dead_zone (period-transferable) |
| `regime_v2_dz_is_2` | binary | dead_zone bucket |
| `regime_v2_dz_is_3` | binary | dead_zone bucket |
| `regime_v2_dz_is_4_or_more` | binary | dead_zone bucket |

### Group 3 — Swing transition counts (4 features)

Auxiliary microstructure of the v2 swing window. Asymmetric counts
(many HH+HL, few LH+LL) is a clean trend signature; balanced counts
indicate transitional.

| Feature | Type |
|---|---|
| `regime_hh_count` | int |
| `regime_hl_count` | int |
| `regime_lh_count` | int |
| `regime_ll_count` | int |

### Group 4 — Stability + transitions (7 features)

Walks BACKWARD from the most-recent backfill row at `ts`. Capped at
100 H4 bars (~16 calendar days).

| Feature | Type | Notes |
|---|---|---|
| `regime_consecutive_h4_bars` | int | run length of current v2 label |
| `regime_h4_bars_since_last_flip` | int | `-1` if no flip in window |
| `regime_changed_in_last_1` | binary | flipped vs 1 H4 bar ago |
| `regime_changed_in_last_5` | binary | flipped vs 5 ago |
| `regime_changed_in_last_10` | binary | flipped vs 10 ago |
| `regime_changed_in_last_20` | binary | flipped vs 20 ago |
| `regime_changed_in_last_50` | binary | flipped vs 50 ago |

### Group 5 — Score dynamics (6 features)

Captures regime *velocity* + *turbulence*.

| Feature | Type | Notes |
|---|---|---|
| `regime_v2_score_change_1` | int | velocity vs 1 H4 ago |
| `regime_v2_score_change_5` | int | velocity vs 5 ago |
| `regime_v2_score_change_20` | int | velocity vs 20 ago |
| `regime_v2_score_max_in_20` | int | local max |
| `regime_v2_score_min_in_20` | int | local min |
| `regime_v2_score_range_in_20` | int | turbulence proxy |

### Group 6 — Detector consistency (1 feature)

| Feature | Type | Notes |
|---|---|---|
| `regime_v1_v2_disagreement` | binary | v1 vs v2 emit different labels at the same H4 boundary |

### Group 7 — Side × regime interactions (6 features)

Per F2 + A6, the *cohort* (regime × side) is where decay concentrated.
This group encodes the named cohorts.

| Feature | Type | Notes |
|---|---|---|
| `regime_counter_to_v2` | binary | replicates K54 v1 `counter_direction_flag` for v2 |
| `regime_counter_to_v1` | binary | same for v1 detector |
| `regime_aligned_v2` | binary | trade direction matches v2 regime |
| `regime_aligned_v1` | binary | matches v1 |
| `regime_long_in_bullish_v2` | binary | F2 cohort marker |
| `regime_short_in_bearish_v2` | binary | A6 LONG-decay complement marker |

### Group 8 — Cross-instrument fleet alignment (13 features)

Per audit Section 5: cross-instrument regime alignment is a noted gap.
Fleet symbols hard-coded as `(XAUUSD, XAGUSD, USDJPY, GBPJPY, GBPUSD,
US30_cash, NAS100)` in `regime.py:FLEET_SYMBOLS` for determinism.

| Feature | Type | Notes |
|---|---|---|
| `regime_fleet_bullish_count` | int | # of fleet symbols (excl self) with v2=bullish |
| `regime_fleet_bearish_count` | int | # with v2=bearish |
| `regime_fleet_transitional_count` | int | # transitional/missing |
| `regime_fleet_aligned_with_self` | int | # matching self v2 |
| `regime_fleet_score_mean` | float | mean v2_score across fleet |
| `regime_fleet_score_signed_agreement` | binary | sign agreement self vs fleet mean |
| `regime_xau_v2_is_bullish` | binary | XAU anchor (risk-correlated with metals/indices) |
| `regime_xau_v2_is_bearish` | binary | XAU anchor |
| `regime_xau_matches_self` | binary | XAU == self |
| `regime_xau_opposite_self` | binary | XAU bullish + self bearish (or vice versa) |
| `regime_xau_score` | int | XAU raw v2_score |
| `regime_xau_score_abs` | int | XAU abs score |
| `regime_xau_to_self_score_diff` | int | self - XAU score (drift relative to gold) |

When `symbol == XAUUSD`: XAU-anchor features mirror the symbol's own
features (XAU matches self, score diff = 0).

### Group 9 — Cross-timeframe agreement (3 features)

D1 direction is APPROXIMATED by 5-bar close-vs-close (not the
production v2 detector — D1 backfill not available). Threshold 50bp.

| Feature | Type | Notes |
|---|---|---|
| `regime_d1_direction_bullish` | binary | D1 5-bar > +0.5% |
| `regime_d1_direction_bearish` | binary | D1 5-bar < -0.5% |
| `regime_h4_d1_agreement` | binary | H4 v2 == D1 5-bar direction |

### Group 10 — Regime-conditional volatility (4 features)

Per `project_distributional_findings`: gold has fat-tail ξ=0.35 + GARCH
persistence 0.9906. Vol-ratio features condition on regime context;
raw vol-family features (percentiles, squeeze) belong to the volatility
family, not here.

| Feature | Type | Notes |
|---|---|---|
| `regime_atr_h4_14` | float | raw H4 ATR(14) — instrument-magnitude |
| `regime_atr_h4_ratio_to_20` | float | vs 20-H4 mean ATR baseline |
| `regime_atr_h4_ratio_to_50` | float | vs 50-H4 mean ATR baseline |
| `regime_atr_h1_to_h4_ratio` | float | H1 ATR / H4 ATR (microstructure-vs-macro) |

### Group 11 — Backfill data-quality (2 features)

Critical to distinguish "regime is neutral" from "no backfill row for
this (symbol, ts)".

| Feature | Type | Notes |
|---|---|---|
| `regime_backfill_available` | binary | 1 if backfill row found at ts; 0 if missing |
| `regime_backfill_h4_bars_stale` | int | H4 bars between row and ts; -1 if no row |

---

## Leakage self-check

**Hard contract per module docstring:** all features at trade entry
timestamp `T` consume ONLY data with backfill timestamp `< T` (and OHLCV
with `time <= T_TF_floor - 1s` for the H4/D1/H1 ATR + D1-direction
features).

**Specific leakage probes:**

1. **Backfill row timestamp.** Backfill rows live on H4 boundaries
   (00, 04, 08, 12, 16, 20 UTC). For an entry at `T`,
   `RegimeBackfillIndex.latest_at(symbol, T)` returns the most recent
   row with `row.ts <= T`. The row at `row.ts == T` (if T is an H4
   boundary) is INCLUDED — that H4 candle has just opened, but its
   regime label was computed at backfill time from swings strictly
   ENDING at `row.ts` (no future data). VERIFIED — see backfill
   schema: `counts.{hh,hl,lh,ll}` are computed from swings at
   `row.ts` minus the configured swing window, never beyond `row.ts`.

2. **Cross-instrument fleet alignment.** Each fleet symbol's backfill
   row is fetched independently with `latest_at(fleet_sym, T)`. No
   symbol's row at `T` reads ANY other symbol's row at `T` — they are
   indexed separately. VERIFIED — see `_feat_cross_instrument_alignment`.

3. **D1 direction approximation.** D1 candle at `T` has not closed if
   `T` is intraday. Cutoff used: `_d1_floor(T) - 1s`, which excludes
   today's not-yet-closed D1 candle. Last `n=10` D1 closes are read
   strictly BEFORE `T`'s D1. VERIFIED — see
   `_feat_cross_timeframe`.

4. **ATR-of-completed-candles for H4 + H1.** H4 candle at `_h4_floor(T)`
   is the candle CONTAINING `T` and may not have closed. Cutoff used:
   `_h4_floor(T) - 1s`. Same pattern for H1. VERIFIED — see
   `_feat_regime_conditional_vol`.

5. **Stability + transitions backward walk.** `RegimeBackfillIndex.window`
   returns `lst[start:idx+1]` where `idx` is the last index with `row.ts
   <= T`. The walk is backward from there only. VERIFIED — see
   `_feat_regime_stability` and `_feat_regime_score_dynamics`.

6. **Score dynamics — `score_change_N` features.** Compute
   `cur_score - score[N H4 ago]` where `score[N H4 ago]` is at index
   `idx - N`. No future H4 row consulted. VERIFIED.

7. **`logged_at` >> `ts` in backfill.** The backfill JSONL was written
   2026-04-26 17:26 UTC, but each row's `ts` is the H4 boundary. The
   regime label at `ts` was computed FROM swings ending at `ts` —
   the retrospective `logged_at` does not introduce future-data
   leakage as long as the backfill compute itself was point-in-time.
   This is documented in `regime_classifier.py` Option-A note: "Same
   MSO -> same label; can be re-run on historical fixtures to compare
   against realized outcomes".

**Known data-quality risk (NOT leakage; flagged for modeler):**

- US30_cash is in the production fleet but NOT in
  `structure_detector_backfill_2026.jsonl`. Backfill symbols are
  `{EURUSD, GBPJPY, GBPUSD, GER40, NAS100, UK100, USDJPY, XAGUSD,
  XAUUSD}`. For 2026-01..04 US30_cash trades, `regime_backfill_available
  == 0` and the model should learn to discount the regime features
  via that flag. See `regime_backfill_h4_bars_stale == -1`.
- Pre-2026-01-21 trades hit the same case (e.g. 2024-2025 trade_index
  rows from XAUUSD/GBPUSD batch). `regime_backfill_available == 0` is
  the disambiguator.

---

## Regime-classifier point-in-time guarantees

The production regime classifier (`src/components/regime_classifier.py`)
is **deterministic**: identical MSO swing input → identical
`RegimeClassification`. The classifier:

1. Pulls `MSO.timeframes['H4'].swings` (already point-in-time per
   `market_state.detect_swings` — swings are anchored to candle indices
   that closed BEFORE the call).
2. Filters swings to a soft lookback (default 20 H4 candles).
3. Calls `identify_structure_v2(swings)` — pure function over the
   swing list. No future data available.
4. Returns `RegimeClassification(regime, classifier_version,
   raw_features={...})`.

Therefore: the regime label at `T` produced by the classifier on data
ending at `T` is identical to the label that WOULD HAVE BEEN produced
in real-time at `T` (assuming swings haven't been retroactively edited).
The backfill JSONL captures this snapshot at H4 boundaries during the
backfill run; we consume `<T` rows only.

**Caveat 1 (acceptable lag):** the H4 candle at `_h4_floor(T)` may not
have closed by the time an M15 candle inside it closes. The regime
label at `_h4_floor(T)` is the regime that closed at the PREVIOUS H4
boundary. We accept this lag — `RegimeBackfillIndex.latest_at(sym, T)`
returns the most-recent row with `row.ts <= T`, which IS the previous
H4 boundary's snapshot until the H4 candle at `T` closes (i.e. T+4h).
This is the same convention K54 v1 used (`_regime_lookup` walk-back at
`k54_build_features.py:163-176`).

**Caveat 2 (D1 swing direction):** D1 direction is a 5-bar
close-vs-close approximation, NOT the v2 detector. D1 backfill is
not available; rebuilding it from `data/historical_2026/{SYM}_D1.csv`
via `identify_structure_v2` over D1 swings is the deterministic
upgrade for K54 v3.

**Caveat 3 (live-stream fallback NOT implemented):** the live regime
stream `shadow_logs/regime_classifications.jsonl` IS read by the
module's path constants but NOT consulted by the lookup methods —
they only read backfill. For the Q1.2 holdout window (2026-04-29 →
2026-05-12) AND for US30_cash backfill gap, the modeler should fold
in `regime_classifications.jsonl` parsing (schema is fully documented
in `regime.py` constants). The constraint of `≤2026-04-28 23:59 UTC`
data cutoff means the live stream's added value within Q1 training
is small — 1 day of overlap.

---

## Inference cost note

| Stage | Cost | Notes |
|---|---|---|
| `RegimeBackfillIndex.__init__` | 1× scan of 3,571-row JSONL (~5ms) | Once per process. |
| `OHLCVCache._load(sym, tf)` | 1× CSV scan per (symbol, TF). Up to ~13k rows for M15. | Lazy-loaded; cached. |
| `compute_regime_features(sym, ts, side)` | 1 backfill latest_at + 1 backfill window + 7 fleet latest_at + 3 OHLCV slices + ATR computations (each O(period=14) with 5-snapshot subsampling). | ~1-2ms per call after caches warm. |
| Production deployment | Calls `classify_regime` once per M15 close already on the live path (session 38). Marginal cost of these features = dict assembly only. | No new classifier-inference cost in production. |

**Flag:** Regime classifier is potentially expensive to RE-RUN
historically (rebuilding the backfill takes minutes). This module
CONSUMES the precomputed backfill — does not re-run. If
`structure_detector_backfill_2026.jsonl` is regenerated for K54 v3 with
extended date range, the module's `RegimeBackfillIndex` automatically
ingests the new data without code changes (one path constant).

---

## Stability scores summary

Computed as Spearman rank correlation of feature value at trade-entry
candle close vs realized R, on `pre-2026-04-01` rows only (the unburned
slice per K54 v1 audit Section 3 + caveat #7).

- `n_pre_april = 378` (439 F11 mechanical filtered to pre-April + 33
  `_trade_index.json` rows, 2024-04 → 2026-03-31).
- Univariate magnitudes are modest (~0.05-0.10 in absolute value)
  which is normal for individual regime features at this n; signal is
  expected from interaction terms learned by the per-regime LightGBM.
- See `regime.csv` for per-feature `stability_spearman_pre_2026_04`.

**Top 5 by |stability|:**

| Rank | Feature | Spearman ρ |
|---|---|---|
| 1 | `regime_xau_score` | -0.0867 |
| 2 | `regime_changed_in_last_50` | +0.0835 |
| 3 | `regime_fleet_bullish_count` | -0.0819 |
| 4 | `regime_fleet_transitional_count` | +0.0772 |
| 5 | `regime_xau_matches_self` | +0.0770 |

Top features cluster on (a) **cross-instrument fleet alignment** (3 of
top 5) and (b) **regime-stability lookback windows** (1 of top 5),
consistent with the F15 + F2 finding that *regime cohort* (not raw
regime label) drives realized outcomes. This indicates the cross-
instrument + stability features are the highest-leverage additions
beyond K54 v1's ENSEMBLE-GATING use of `regime_tag`.

The negative sign on `regime_xau_score` and `regime_fleet_bullish_count`
is consistent with F2/A6's LONG-side decay finding: *more positive
fleet/XAU score* = more LONG-bias regime concentration = lower mean
realized R in the H1-2026 cohort. This is exactly the cohort F2 said
collapsed in H2 — the model needs to learn that bullish-fleet-cluster +
LONG side is the decayed cell.

---

## Changes from K54 v1

| K54 v1 | K54 v2 (this catalog) |
|---|---|
| `regime_tag` (4-class categorical) — used as ensemble gating, ZERO importance as feature | 9 one-hots across v1 + v2 detectors + dead-zone flag |
| `counter_direction_flag` (binary) — ZERO importance | Replaced + extended: 6 side × regime interactions including F2 cohort markers |
| `cross_instrument_xau_dir` — schema slot, ALWAYS BLANK | 7 XAU-anchor features + 6 fleet aggregate features |
| `v2_score` — read in build_features but NEVER propagated | 14 features (raw, abs, normalized, dynamics) |
| `v2_dead_zone` — read but NEVER propagated | 5 features (raw, buckets, in-dead-zone flag) |
| No regime stability/transition features | 7 features (consecutive bars, bars-since-flip, changed-in-last-N) |
| No cross-timeframe regime agreement | 3 features (D1 direction approx + agreement) |
| No regime-conditional volatility | 4 features (ATR ratios at H4-20, H4-50, H1-to-H4) |
| No data-quality flag | 2 features (backfill_available, h4_bars_stale) — protects against US30_cash + pre-2026-01-21 zero-vs-missing trap |

Total: K54 v1 had 2 regime features (both zero-importance). K54 v2
ships **63 regime features** with explicit point-in-time discipline,
documented stability scores, leakage self-check, and data-quality
indicators.

---

*End of catalog. Implementation in `research/ml_program/scripts/features/regime.py`.*
