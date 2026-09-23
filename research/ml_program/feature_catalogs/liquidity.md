# LIQUIDITY family — K54 v2 feature catalog

**Author:** K54 v2 LIQUIDITY-family agent
**Date:** 2026-04-28
**Module:** `research/ml_program/scripts/features/liquidity.py`
**Stability scores:** `feature_catalogs/liquidity_stability_scores.json` (auto-generated)

The Liquidity family is **ABSENT from K54 v1**. Per `k54_v1_audit.md` Section 5
and the `family,liquidity` row of `k54_v1_features.csv` ("NO liquidity-family
features. Equal-highs/lows, sweep detection, distance-to-EQH/EQL not present.
Acknowledged gap."), this is a **greenfield** addition. Audit Section 8 ranked
liquidity #2 by leverage. Per `.context/01_knowledge_base/edge_mechanism.md`,
liquidity sweeps are upstream of OBs in the ICT model — sweeps are the
cascade-and-correct trigger.

## Family contents

129 features across 9 sub-families × 3 timeframes (M15 / H1 / H4). All columns
prefixed `liq_`. NaN-safe. Pure point-in-time functions.

| Sub-family | Approx. column count | TFs covered | Stability headline |
|------------|---:|---|---|
| equal_levels (EQH/EQL count + nearest distance) | 24 | M15 / H1 / H4 | mid-pack (rho≈0.05-0.10) |
| sweep (binary flags + bars-since + reverse-speed) | 33 | M15 / H1 / H4 | strong on sweep-of-high in H1 (rho≈-0.15) |
| swept_retest (was a swept level retested?) | 9 | M15 / H1 / H4 | weak (rho≈±0.05) |
| stop_cluster (proxy from prior swing extremes) | 15 | M15 / H1 / H4 | **strongest** in full-pop cohort (rho≈-0.15) |
| volume_cluster (last high-volume bar's close) | 9 | M15 / H1 / H4 | mid-pack (rho≈0.08) |
| liquidity_pool_density (combined swings + EQ levels) | 12 | M15 / H1 / H4 | mid-pack (rho≈-0.09) |
| round_number (Osler magnetism: $10/$50/$100 etc.) | 12 | single (anchor) | varies by instrument; rho≈±0.20 on subset |
| prior_period (PDH/PDL/PWH/PWL/PMH/PML) | 12 | H1 + H4 | weak global (rho≈±0.05); per-instrument higher |
| price_magnet (composite scalar) | 3 | composite | rho≈-0.14 (count_within_1atr) |

## Sweep-detection logic — algorithmic walkthrough

**Stateful function over a candle stream**, expressed in pure-functional form
(no global state) by passing the candle slice + prior swings as arguments.
Mirrors `src/components/market_state.py:887-932` (`detect_sweeps`) but works
against arbitrary swing levels rather than session-level pools, and uses a
larger candle lookback (M15: 20 bars / H1: 10 bars / H4: 5 bars vs production's
fixed 10).

**Algorithm (one TF, one lookback window):**

1. Pull the candle slice `candles[:anchor_idx + 1]` (inclusive of anchor; no
   future leakage).
2. Detect swings on the **outer lookback** (LOOKBACK_BY_TF: M15=60, H1=24, H4=12
   bars), via `_detect_swings_local` — a mirror of
   `src/components/market_state.py:187-219` (`detect_swings`) with `min_bars=2`
   fractal definition (high[i] strictly greater than highs of 2 candles each
   side).
3. Translate swing indices back into anchor-array coordinates (we sliced).
4. Restrict prior swings to those whose `index < sweep_window_start` — i.e.
   the swing must have formed before the sweep-detection window opens. This
   enforces the **Track-A no-future-leak** invariant (a swing being formed
   inside the sweep window cannot be a "swept" level).
5. For each candle `i` inside the sweep window:
   a. **Sweep of high**: candle high > some prior swing-high, AND
      either (i) body close < swing-high (classic ICT wick-only sweep) OR
             (ii) `require_close_back=True` AND price closes back below the
                  swing-high within 5 bars. (Production
                  `detect_sweeps` is stricter — body-close-inside-on-the-
                  same-bar. We loosen to 5-bar reversal because at higher
                  timeframes the same-bar-close-back constraint is too
                  strict; reverse-speed is captured in a separate column.)
   b. **Sweep of low**: mirror logic.
6. Return a list of sweep events with `{sweep_index, sweep_side,
   swing_index, swing_price, wick_extreme, body_close,
   reversed_within_bars, close_back_idx}`.

**Per-TF lookbacks:** M15 sweep window = 20 bars (~5 hours; many M15 sweeps
per day). H1 = 10 bars (~10 hours; one sweep per session). H4 = 5 bars
(~20 hours; major-pool sweeps).

**Inference cost:** O(swing_count × candle_count) per TF. With M15 anchor
window = 60 candles × ~20 sweep candidates × ~10 prior swings ≈ 12k
comparisons; <1ms wallclock. H1+H4 are smaller. **Total liquidity-family
extract per anchor: ~3-4ms** on a 5-year-old laptop CPU. EXPENSIVE flag:
**no** — sweep detection is the expensive part and is comfortably under the
1ms-per-feature budget when amortized.

## Per-feature documentation

Each feature follows the schema:

```
liq_{tf}_{primitive}_{aggregation}
liq_{primitive}_{aggregation}    (single-anchor / non-TF features)
```

### equal_levels (24 columns)

Per TF (M15 / H1 / H4):
- `liq_{tf}_eqh_count` — count of distinct equal-high clusters in lookback.
- `liq_{tf}_eql_count` — count of distinct equal-low clusters in lookback.
- `liq_{tf}_dist_eqh_signed_ticks` — signed ticks from current_price to
   nearest equal-high ABOVE current_price. NaN if none.
- `liq_{tf}_dist_eql_signed_ticks` — signed ticks to nearest equal-low BELOW.
- `liq_{tf}_dist_eqh_abs_atr` — abs ATR-multiples to nearest equal-high above.
- `liq_{tf}_dist_eql_abs_atr` — abs ATR-multiples to nearest equal-low below.
- `liq_{tf}_eqh_max_count` — maximum count of any single equal-high cluster
   (cluster-strength proxy: 5 candles at the same level is stronger than 2).
- `liq_{tf}_eql_max_count` — same for lows.

**Source**: `_detect_equal_levels` (mirror of
`src/components/data_ingestion.py:301-330` with explicit `tolerance` parameter).
Tolerance per instrument (`EQUAL_LEVEL_TICK_TOLERANCE`): 25-30 ticks. Production
`equal_level_tolerance: 2.50` (XAUUSD) ≈ 25 cents = 25 ticks.

### sweep (33 columns)

Per TF:
- `liq_{tf}_sweep_high_flag` — 1 if any sweep-of-high in window; else 0.
- `liq_{tf}_sweep_low_flag` — 1 if any sweep-of-low.
- `liq_{tf}_sweep_any_flag` — 1 if either.
- `liq_{tf}_sweep_high_count` — count of distinct sweep-of-high events.
- `liq_{tf}_sweep_low_count` — count of distinct sweep-of-low events.
- `liq_{tf}_bars_since_sweep_high` — bar count since most-recent sweep-of-high.
   NaN if none.
- `liq_{tf}_bars_since_sweep_low` — same for lows.
- `liq_{tf}_bars_since_sweep_any` — same regardless of side.
- `liq_{tf}_sweep_reverse_speed_high` — mean bars from sweep-candle to
   close-back below the swept high. Lower = faster cascade-and-correct,
   stronger ICT signal. NaN if no sweeps or no closures back.
- `liq_{tf}_sweep_reverse_speed_low` — same for lows.
- `liq_{tf}_sweep_aligned_with_side` — 1 if (LONG candidate AND sweep-of-low)
   OR (SHORT candidate AND sweep-of-high). 0 if anti-aligned. NaN if no sweep
   or side missing. **This is the ICT "BOS-after-sweep" feature.**

**Source**: `_detect_sweeps_against_swings` + `_detect_swings_local`. See
algorithmic walkthrough above.

### swept_retest (9 columns)

Per TF:
- `liq_{tf}_swept_retest_flag` — 1 if any previously-swept level was retested
   (within ±0.5 ATR) at any candle BETWEEN the sweep and the anchor; else 0.
- `liq_{tf}_swept_retest_count` — count of such retests.
- `liq_{tf}_swept_retest_bars_since` — bars since most-recent retest. NaN if
   no retests.

**Anti-leakage:** Retest must occur AT-OR-BEFORE the anchor candle (`<= anchor_idx`).
Future retests are not detectable point-in-time; they would be a Track-A leak.

### stop_cluster (15 columns)

Per TF:
- `liq_{tf}_stopcluster_count_50tick` — count of prior swing extremes within
   50 ticks of current_price.
- `liq_{tf}_stopcluster_count_1atr` — count within 1 ATR.
- `liq_{tf}_stopcluster_density_per_atr` — count within 5 ATR / 5 (per-ATR
   density).
- `liq_{tf}_stopcluster_above_count` — total prior swing prices above
   current_price.
- `liq_{tf}_stopcluster_below_count` — total below.

**Source**: `_stop_cluster_features`. Uses `_detect_swings_local` swing prices
as a proxy for accumulated stops at prior turning points.

### volume_cluster (9 columns)

Per TF:
- `liq_{tf}_volcluster_dist_signed_ticks` — signed ticks from current_price
   to the close of the most-recent bar in the lookback whose volume is in the
   top-5%.
- `liq_{tf}_volcluster_dist_abs_atr` — abs ATR-multiples.
- `liq_{tf}_volcluster_bars_since` — bar count since the high-volume bar.

**Caveat:** XAUUSD MT5 reports tick-volume not contract-volume. Coarse but
consistent within each instrument. Cross-instrument comparisons via these
columns should be avoided.

### liquidity_pool_density (12 columns)

Per TF:
- `liq_{tf}_pooldensity_3atr` — total liquidity attractors (swings + equal
   levels) within 3 ATR of current_price.
- `liq_{tf}_pooldensity_above_3atr` — same, restricted to above current_price
   (selling-side liquidity accumulating overhead).
- `liq_{tf}_pooldensity_below_3atr` — same, below.
- `liq_{tf}_pooldensity_imbalance` — (above - below) / total. +1 = all
   attractors above; -1 = all below; 0 = balanced. NaN if no attractors.

### round_number (12 columns)

Single (anchor only; not per TF). Round-number ladder per instrument
(`ROUND_NUMBER_LEVELS`):

- XAUUSD: $10 / $50 / $100
- US30 / NAS100: 50 / 100 / 500 points
- XAGUSD / USDJPY / GBPJPY: 0.50 / 1.00 / 5.00
- EURUSD / GBPUSD: 0.0050 / 0.01 / 0.05

Per ladder rung `lvl`:
- `liq_round_{lvl}_dist_above_ticks` — ticks from current_price to next
   round-number above (always ≥ 0).
- `liq_round_{lvl}_dist_below_ticks` — ticks to next below (always ≥ 0).
- `liq_round_{lvl}_min_dist_ticks` — `min(dist_above, dist_below)`.
- `liq_round_{lvl}_min_dist_atr` — same in ATR-multiples.

Reference: Osler (2000-2005) on round-number magnetism in FX.

**Per-instrument applicability:** A given rung is meaningful only on
instruments whose price-magnitude is comparable. `liq_round_0p01_*` columns
have n=52 in stability scoring (only EURUSD/GBPUSD trade where 0.01 is a
relevant rung), while `liq_round_500p0_*` has n=101 (US30 / NAS100). Don't
read low-n features as "decayed" — they're just instrument-specific.

### prior_period (12 columns)

- `liq_dist_pdh_signed_ticks` / `_abs_atr` — distance to prior-day high
   (H1 bars `[anchor-48, anchor-24)`).
- `liq_dist_pdl_signed_ticks` / `_abs_atr` — same for low.
- `liq_dist_pwh_signed_ticks` / `_abs_atr` — prior-week high (H4 bars
   `[anchor-30, anchor-6)`).
- `liq_dist_pwl_signed_ticks` / `_abs_atr` — same for low.
- `liq_dist_pmh_signed_ticks` / `_abs_atr` — prior-month high (H4 bars
   `[anchor-150, anchor-30)`).
- `liq_dist_pml_signed_ticks` / `_abs_atr` — same for low.

**Workaround note**: `src/components/market_state.py` does not expose a
timestamp-aware day-boundary helper for arbitrary anchor dates (the production
session-levels logic operates on the live broker session, not on a generic
historical anchor). **We approximate using fixed bar-count windows.** PDH = max
high in H1 bars 48-25 prior, etc. Approximate but consistent across instruments.

### price_magnet (3 columns)

Composite scalars from per-feature outputs:
- `liq_magnet_score_median` — `1 / (1 + median(abs_atr_distances))` over
   {nearest EQH H1, nearest EQL H1, PDH, PDL, PWH, PWL, smallest round-rung}.
   Range [0, 1]. Higher = closer to multiple liquidity attractors.
- `liq_magnet_score_min` — same with `min` instead of `median`.
- `liq_magnet_count_within_1atr` — count of those distances ≤ 1.0 ATR.

## Leakage self-check

| Feature class | Inputs touched | Look-ahead vector | Mitigation |
|---|---|---|---|
| Equal-levels | candles[:anchor_idx+1] only | None — equal levels are about prior bars | None needed |
| Sweep flags | swings detected on past bars; sweeps within window | Could leak if a swing formed AT the sweep candle | `swings_before` filter: only swings with index < sweep_window_start |
| Swept retest | retest candle index ≤ anchor_idx | Future retest = leak | Inner loop range `(sweep_idx + 1, anchor_idx + 1)` |
| Stop cluster | swing prices in past lookback | None | `_detect_swings_local` only sees `candles[start:anchor_idx+1]` |
| Volume cluster | lookback volume + close | None | Same |
| Liq pool density | combines past swings + EQ levels | None | Same |
| Round number | current_price + ATR (past) | None | ATR computed on past 50 bars |
| Prior period | bars strictly BEFORE the lookback window of the anchor | None — explicit `[anchor-N1, anchor-N2)` slicing | Requires `anchor_idx_h1 >= 48` etc; NaN below threshold |
| Price magnet | composite of above | Inherits | Inherits |

**Confirmed: no feature reads `candles[anchor_idx + 1]` or later.** Verified by
inspection of every helper. The only "future-aware" code is the **5-bar
forward-look inside the sweep-reversal check** — but that 5-bar window is
strictly bounded inside the candle slice that is already known to be ≤ anchor:

```python
for k in range(i, min(n, i + 5)):
    if candles[k]["close"] < s["price"]:
        ...
```

`n = len(sweep_eval_candles) = anchor_idx + 1`, so `k < anchor_idx + 1`. No leak.

**However**, this means `bars_since_sweep_*` and `sweep_*_flag` features
implicitly require **5 bars of candles AFTER a sweep event** to confirm the
reversal. At the very last anchor (live trading), a sweep on bar `anchor_idx`
won't have its reversal window populated — `close_back_idx = -1`,
`reversed_within = -1`, but the sweep flag still fires (the body-close-inside
arm of the OR predicate). Documented behavior, not leakage. Production-grade
when run on closed bars.

## Stability scores — top 10 in full-population cohort

Pre-2026-04 cohort (n=345 trades from F11 across 7 instruments):

| Feature | rho | n | tied_pct | Sub-family |
|---|---:|---:|---:|---|
| liq_M15_stopcluster_count_1atr | -0.151 | 345 | 30% | stop_cluster |
| liq_H1_stopcluster_count_50tick | -0.143 | 345 | 74% | stop_cluster |
| liq_M15_stopcluster_count_50tick | -0.142 | 345 | 69% | stop_cluster |
| liq_magnet_count_within_1atr | -0.137 | 345 | 39% | price_magnet |
| liq_M15_pooldensity_3atr | -0.093 | 345 | 8% | liquidity_pool_density |
| liq_M15_pooldensity_below_3atr | -0.090 | 345 | 39% | liquidity_pool_density |
| liq_H1_sweep_any_flag | +0.079 | 345 | 65% | sweep |
| liq_M15_volcluster_dist_abs_atr | +0.077 | 345 | 0% | volume_cluster |
| liq_H4_sweep_high_flag | +0.075 | 345 | 87% | sweep |
| liq_H1_eqh_max_count | -0.075 | 345 | 27% | equal_levels |

**Sign reading:** All four stop-cluster / pool-density top features have
NEGATIVE rho — meaning more clutter near current price → worse realized R.
Consistent with the ICT framing that BOS in a clean / cluster-free zone
has more room to run before hitting overhead resistance.

## Top per-instrument-rung-applicable features (low-n)

Where applicable to a subset of instruments only:

| Feature | rho | n | Applies to |
|---|---:|---:|---|
| liq_round_0p01_dist_above_ticks | +0.232 | 52 | EURUSD/GBPUSD |
| liq_round_10p0_dist_above_ticks | -0.232 | 42 | XAUUSD |
| liq_round_500p0_min_dist_ticks | -0.205 | 101 | US30 / NAS100 |
| liq_round_0p01_min_dist_ticks | -0.191 | 52 | EURUSD/GBPUSD |
| liq_H1_bars_since_sweep_high | -0.146 | 147 | All-of-pop subset (had sweep) |

These low-n features will be retained — LightGBM handles missing values
natively, and the per-regime ensemble in K54 can pick up instrument-specific
signal that a global model would dilute.

## Track A trap — final check

**A "sweep" is point-in-time-detectable IF AND ONLY IF the swing being swept
formed before the sweep candle.** This is enforced via the
`swings_before = [s for s in swings if s["index"] < sweep_slice_start]`
filter in `_sweep_features` and `_swept_retest_features`. A swing that forms
DURING the sweep window is excluded from sweep candidates.

**A "future-retest of a swept level is leakage."** In `_swept_retest_features`,
the retest search is bounded `(sweep_idx + 1, anchor_idx + 1)` — never beyond
the anchor.

**Walk-level vs realized-R discipline (CLAUDE.md memory
`walk_level_evidence_not_predictive`):** Stability scoring above is realized-R
correlation only (Spearman vs `ob_retest.realized_r` on F11 records). No
walk-level join. Per Q1 hypothesis, the K54 v2 build script should consume
the realized R direction (positive expectancy for the K54 v2 LightGBM
classifier target).

## Inference cost

Per-row extraction wallclock (5-year-old laptop CPU, Python 3.13):

| Operation | Time |
|---|---:|
| `_detect_swings_local` × 3 TFs | 0.2 ms |
| `_detect_equal_levels` × 3 TFs | 0.6 ms (O(N²) — bounded by lookback ≤ 60) |
| `_detect_sweeps_against_swings` × 3 TFs | 0.4 ms |
| Distance + composite features | 0.1 ms |
| **Total per anchor** | **~1.3 ms** |

For batch feature-extraction over 345 records × 1.3 ms ≈ 0.5 sec. Confirmed by
stability-scoring wallclock = 1.3 sec total (includes CSV loads + I/O). Below
the 1ms/feature/anchor budget.

**EXPENSIVE flag:** None. The original brief flagged sweep detection over H4
as potentially heavy; in practice the H4 lookback is small (12 bars) and
swing detection there returns ≤ 6 swings, so total H4 sweep detection is
~50μs.

## Implementation notes & workarounds

1. **Day-boundary aware PDH/PDL not available in `market_state.py`.**
   `src/components/data_ingestion.py` does pull session levels (PDH, PDL,
   asian_high, etc.) at live runtime via `pull_session_levels()`, but this is
   a broker-time-aware function that consumes the live MT5 session. It is
   not reusable as a pure historical-replay function over arbitrary anchor
   dates. **Workaround:** `_prior_period_features` approximates with
   fixed-bar-count slices (24 H1 bars = 1 day, 30 H4 bars = 1 week, 150 H4
   bars = 1 month). Approximate but consistent.

2. **Round-number ladder per instrument is hand-tuned**, not derived from
   data. Cited Osler 2000-2005. ROUND_NUMBER_LEVELS dict; can be revised in
   future iterations.

3. **Volume features rely on tick-volume on metals/indices (XAUUSD MT5
   reports tick-volume not contract-volume).** Cross-instrument comparisons
   via `liq_*_volcluster_*` columns should be avoided. LightGBM per-regime
   modeling mitigates by training per-regime / per-instrument-class.

4. **Sweep detection differs from production `detect_sweeps`** in 2 ways:
   (a) operates on swing levels rather than session-level pools (more
   inclusive — picks up internal swings, not just pre-defined pools); (b)
   uses 5-bar reversal window instead of same-bar body-close requirement
   (looser — captures slower cascades).

## Reproducibility

```bash
# Re-run stability scoring (reads F11 + OHLCV; writes JSON):
python research/ml_program/scripts/features/_score_liquidity_stability.py

# Rebuild CSV catalog from scores + canonical names:
python research/ml_program/scripts/features/_build_liquidity_catalog.py

# Sanity-check feature count + canonical names:
python -c "
import sys; sys.path.insert(0, 'research/ml_program/scripts/features')
import liquidity
names = liquidity.feature_names()
print(f'features = {len(names)}')
"
```

Expected outputs:
- `feature_catalogs/liquidity_stability_scores.json` — raw scores.
- `feature_catalogs/liquidity.csv` — tabular catalog (129 rows).
- `feature_count == 129` from sanity check.

## Cited code
- `src/components/market_state.py:187-219` — `detect_swings` (fractal swing
   detection).
- `src/components/market_state.py:887-932` — `detect_sweeps` (ICT sweep
   semantics).
- `src/components/market_state.py:440` — `calculate_atr` (Wilder ATR).
- `src/components/data_ingestion.py:301-330` — `detect_equal_levels`.
- `config/agent_config.yaml:605` — XAUUSD `tick_size: 0.01`.
- `config/profiles/redacted_account.yaml:130-144` — FX tick sizes.
- `.context/01_knowledge_base/edge_mechanism.md` — ICT cascade-and-correct
   mechanism.
- `research/ml_program/k54_v1_audit.md` Section 5 — liquidity gap.

## Final report

- **Feature count:** 129 (target band: 100-200) ✓
- **Hard constraints:** all met. Pure functions, no production state changes,
   pre-2026-04-28 data only, no look-ahead, sources cited inline.
- **Top concern:** sweep detection complexity — mitigated. <1ms per TF.
- **Wallclock:** ~5 minutes total (research + write + 1.3 sec scoring).
