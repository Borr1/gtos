# K54 v2 — Microstructure feature family

**Family:** `microstructure`
**Owner:** Microstructure feature-engineering agent (Q1 Week 2-3)
**Source module:** `research/ml_program/scripts/features/microstructure.py`
**Source CSV:** `research/ml_program/feature_catalogs/microstructure.csv`
**Stability data window:** F11 BOS events with realized R, BOS time strictly before 2026-04-01 UTC
**Stability sample size (per family):** n = 345 trades across 7 instruments
**Data cutoff (hard rule):** 2026-04-28 23:59 UTC — enforced inside `compute_microstructure_features` by `ValueError` on any `ts_close` at or after that timestamp
**Generation timestamp (UTC):** 2026-04-28 (Q1 Week 2-3)

This document is the canonical per-feature reference for the Microstructure
family. Sibling families (Structure, Volatility, Liquidity, Regime,
Time/Session) own their own catalog files. Names are deterministic; any
change here requires re-running `_run_microstructure_stability.py` to
regenerate `microstructure.csv` in lock-step.

---

## Scope

The K54 v1 audit (`research/ml_program/k54_v1_audit.md` Section 5)
identified microstructure as the single most under-served family. v1 had
exactly one microstructure feature (`displacement_quality_score`), and that
feature was hard-coded to `0.5` for 76% of the dataset (the F11 mechanical
slice) — making it effectively absent.

The K54 v2 microstructure catalog goes beyond the simple `cumulative_delta /
footprint_imbalance / micro_reversal_count` triad that E24 / E26 dispatched
NULL_VERDICT_CONFIRMED on (memory `project_microstructure_archived_2026-04-27`),
by:

1. **Multi-lookback expansion** (5 / 20 / 50 / 200 bars per primitive) to
   capture short-term vs swing-scale behavior on the same axis.
2. **Multi-timeframe replication** (M15 / H1 / H4) on Component-2-style
   primitives (OB count, FVG count / unfilled ratio).
3. **Per-bar distributional features** (z-score, percentile rank,
   compression / expansion counts, longest streaks) that simple-statistic
   summaries discard.
4. **Tick-data-required features** (cumulative delta, footprint imbalance,
   trade arrival rate, spread mean / max / volatility) gated on tick
   coverage. Sentinel `NaN` is emitted for instruments without tick
   coverage; never silently zero.
5. **Volume profile** (VPOC distance / value-area position) on M15 bars
   across 50 / 100 / 200 bar lookbacks.

Total feature count: **187** (target was 150-300).

| Subgroup | Count |
|---|---:|
| Component-2-derived (OB count) | 12 |
| Component-2-derived (FVG bull/bear count + unfilled ratio) | 36 |
| Mini-swing count | 6 |
| Body / wick ratios (last bar + percentile rank) | 12 |
| Tick-count z-score (volume proxy) | 3 |
| Range / expansion / compression / large-body | 30 |
| Streak / reversal-rate features | 8 |
| Synthetic-tick (M1 Lee-Ready) cum-delta + footprint + z-score + percentile | 14 |
| Tick-data-required (cum-delta + footprint + spread + trade-rate) | 24 |
| Volume profile (VPOC + value area) | 6 |
| Volume momentum / range-expansion ratio / vol-of-vol / FVG skew / close-in-range / last-bar-return-ATR / upper-lower body | 36 |
| **Total** | **187** |

24 features are flagged `EXPENSIVE_TICK` (require iterating tick rows;
> 1 ms / candle when tick volume > 50 000). 13 additional features are
flagged `EXPENSIVE` (large-lookback OHLCV scans, M1 21-window z-scores).

---

## Per-feature documentation

The full per-feature row is in `microstructure.csv`. Below is a grouped
narrative summary with the logic per group and the top observed
stability rho. **Stability rho** = Spearman rank correlation between the
feature value at the BOS / candle-close time and the realized R-multiple
of the corresponding F11 ob_retest trade, on pre-2026-04 data only
(n = 345 trades). **Stability p** = two-sided asymptotic p (Student-t
approximation, scipy.special.betainc fallback to Wilson approximation).
Bonferroni at family-size 187 means a single-test p must be below
0.05 / 187 ≈ 2.7e-4 to survive — none do at this n. Several features
clear raw p < 0.05 and merit follow-up at larger n.

### Group A — Component-2-derived OB count (12)

`ob_count_{tf}_lb{N}` for tf ∈ {m15, h1, h4} × lookback ∈ {5, 20, 50, 200}.

For each window, count OB-like patterns: a bearish (resp. bullish)
candle immediately preceding a >= 1-ATR bullish (resp. bearish) flip.
This is a lightweight proxy for `src/components/market_state.identify_order_blocks`
(see Leakage self-check below). It does NOT require the full Component-2
detector; therefore it is isolation-safe for parallel feature-family
agents and runs in O(N) per window.

Top stability:
- `ob_count_h1_lb50`: rho = +0.033, n = 345, p = 0.55
- `ob_count_h4_lb20`: rho = +0.033, n = 345, p = 0.54

Both NO_SIGNAL on this sample. The hypothesis was that "rich OB
neighborhoods" might predict continuation strength; this is unsupported
at the F11 mechanical-only sample. Keep all 12 for K54 v2 — model can
prune; the cost is one tree split worth of memory each.

### Group B — Component-2-derived FVG count + unfilled ratio (36)

`fvg_bull_count_{tf}_lb{N}`, `fvg_bear_count_{tf}_lb{N}`,
`fvg_unfilled_ratio_{tf}_lb{N}` × tf {m15, h1, h4} × lb {5, 20, 50, 200}.

The 3-candle FVG check uses a 5%-of-14-bar-ATR minimum gap threshold
(matches the production `FVGFinder` floor). `unfilled` = the gap region
has not been re-traversed by any subsequent bar's high/low.

Top stability:
- `fvg_unfilled_ratio_m15_lb50`: rho = -0.095, n = 345, p = 0.078
- `fvg_unfilled_ratio_h1_lb20`: rho = -0.092, n = 345, p = 0.087
- `fvg_bull_count_h4_lb200`: rho = +0.067, n = 345, p = 0.21

Two unfilled-ratio features at raw p < 0.10 with NEGATIVE rho —
suggesting that more-unfilled-FVG environments correlate with weaker
realized R for ob_retest trades (an "obstacle to follow-through"
interpretation). Worth retaining; revisit at K54 v2 train-time AUC
contribution.

### Group C — Mini-swing count (6)

`swing_count_{m15,h1}_lb{5,20,50}`. Counts alternating local-extrema
swings (min 2-bar streak) on the close-diff sign. Crude proxy for the
production swing detector; correlation with the real swing count is
~0.7 on noisy series.

Top stability: **`swing_count_h1_lb5`: rho = +0.118, n = 345, p = 0.029** —
RAW SIG, does NOT survive Bonferroni. Possible reading: more-swingy H1
recent past = better continuation post-BOS. Marginal; keep.

### Group D — Body / wick ratios (12)

Last-bar `body_ratio` = `|close-open| / range`; upper / lower wick
ratios; percentile rank of body ratio against prior 50 same-TF bars.

Top stability: **`last_bar_lower_wick_ratio_m15`: rho = +0.124, n = 345,
p = 0.021**. Larger lower-wick on the last M15 bar (= rejection at
lows) correlates with better realized R for ob_retest trades. Aligns
with ICT "rejection candle precedes continuation" intuition. Keep.

### Group E — Tick-count z-score on bar volume (3)

`tick_count_zscore_{m15,h1,h4}_lb20`. MT5 `volume` field on OHLCV CSVs
is tick count, not currency volume. Z-score against prior 20 bars'
volume identifies "abnormal recent activity".

Top: `tick_count_zscore_h4_lb20`: rho = -0.054, n = 345, p = 0.32.
NO_SIGNAL.

### Group F — Range / expansion / compression / large-body (30)

`range_pctile_{tf}_lb{N}`, `compression_count_{tf}_lb{N}`,
`expansion_count_{tf}_lb{N}`, `large_body_count_{tf}_lb{N}`,
`avg_body_range_ratio_{tf}_lb{N}`, `volume_zscore_{tf}_lb{N}`.

Top stability:
- **`range_pctile_h4_lb20`: rho = +0.139, n = 345, p = 0.0095** (RAW SIG)
- **`range_pctile_h4_lb50`: rho = +0.133, n = 345, p = 0.014** (RAW SIG)
- **`range_pctile_h4_lb5`: rho = +0.113, n = 345, p = 0.036** (RAW SIG)

Three features at raw p < 0.05 — all H4 range-percentile features with
positive rho. Reading: BOS events that occur on H4 candles in expanded-
range regimes (vs compressed) tend to have better realized R. Consistent
with vol-clustering / fat-tail observations in
`project_distributional_findings.md` (gold ξ=0.35 fat tail). H4 range
appears load-bearing on stability sample — strongest single subgroup
for K54 v2.

### Group G — Streak features (8)

`longest_green_streak_{m15,h1}_lb50`, `longest_red_streak_{m15,h1}_lb50`,
`micro_reversal_rate_{m15,h1}_lb{20,50}`.

Top stability: **`micro_reversal_rate_m15_lb50`: rho = -0.144, n = 345,
p = 0.0073** (RAW SIG, top-1 microstructure feature). Higher reversal
rate (= choppier price action) correlates with WORSE realized R.
Intuitive: choppy environments make ICT-style continuation trades more
prone to whipsaw. Top of the watch list.

Also: **`longest_red_streak_m15_lb50`: rho = +0.122, n = 345,
p = 0.023** (RAW SIG). Longer recent red streaks before a (mostly LONG)
BOS = better realized R; might be the F2-known "deeper-pullback-leads-
to-better-LONG-fill" effect surfacing at microstructure scale.

### Group H — Synthetic-tick features (M1 Lee-Ready) (14)

`synthetic_cum_delta_m1_last_{15,60,240,480}min`,
`synthetic_footprint_imb_m1_last_{15,60,240,480}min`,
`synthetic_cum_delta_zscore_m1_{15,60,240,480}min_vs_lb20`,
`synthetic_delta_pctile_m1_{60,240}min_lb20`.

These rely on the Lee-Ready candle-direction proxy (`close > open` →
buyer-initiated; `close < open` → seller-initiated; `close == open` →
neutral). Inherits the ~85% accuracy ceiling of Lee-Ready 1991 on real
market microstructure (per the existing E24 implementation in
`src/research_infra/synthetic_tick_reconstructor.py`).

Top stability:
- `synthetic_delta_pctile_m1_240min_lb20`: rho = -0.120, n = 125, p = 0.18
- `synthetic_cum_delta_zscore_m1_240min_vs_lb20`: rho = -0.106, n = 125, p = 0.24

Both NO_SIGNAL at small n; neither contradicts E24 / E26 NULL_VERDICT.
The 240-min and 480-min variants have lower n (125-287) because the
lookback requires 21 × 240 min = 84 hours or 21 × 480 min = 168 hours of
prior M1 history, which excludes early-2026-01 trades.

Recommendation: keep but flag low-priority. K54 v2 ablation should
report what these contribute; if 0.0 importance, drop in K54 v3.

### Group I — Tick-data-required features (24)

`real_cum_delta_last_{30,60,300,900}s`,
`real_footprint_imb_last_{30,60,300,900}s`,
`trades_per_sec_last_{30,60,300,900}s`,
`avg_spread_last_{30,60,300,900}s`,
`max_spread_last_{30,60,300,900}s`,
`spread_volatility_last_{30,60,300,900}s`.

These consume captured tick parquets at `data/ticks/{symbol}/{date}.parquet`.
Stability **CANNOT BE COMPUTED** on the pre-2026-04 sample because the tick
daemon was deployed only on 2026-04-25 onward, AND only on NAS100 +
US30_cash. All 24 features have `stability_n = 0` in the catalog.
**This is the dominant tick-coverage gap.**

These features will be re-evaluated when tick coverage accumulates. K54
v2 trains them with `NaN` for any (symbol, candle) tuple lacking tick
data — LightGBM handles NaN natively as a missing-value branch decision.

Recommendation for the orchestrator: keep these in the catalog as
forward-looking schema slots; they will become useful for K54 v3 once
tick coverage hits all 7 instruments × at least one full month.

### Group J — Volume profile (6)

`vpoc_dist_atr_m15_lb{50,100,200}`, `value_area_pos_m15_lb{50,100,200}`.

A simplified TPO-like volume profile: bin the typical price `(h+l+c)/3`
across 30 bins, accumulate `volume` (= MT5 tick count) per bin. VPOC =
bin with highest accumulated volume. Value area = expanding range
around VPOC capturing >= 70% of total volume.

`vpoc_dist_atr_m15_lb{N}` = (last_close − VPOC) / 14-bar ATR.
`value_area_pos_m15_lb{N}` ∈ {-1 (below VAL), 0 (inside), +1 (above VAH)}.

Top stability: `vpoc_dist_atr_m15_lb50`: rho = +0.045, n = 345, p = 0.41.
NO_SIGNAL. This is potentially because the F11 dataset is dominated by
fresh BOS events where price has not yet had time to accumulate
volume-profile structure. May surface signal in continuation-trade
holdouts; keep.

### Group K — Misc (vol momentum, vol-of-vol, FVG skew, close-in-range, last-bar-return-ATR, upper-lower body) (36)

Various single-purpose features — see CSV for individual descriptions.

Top stability inside this group: `lower_body_lb20_m15`: rho = +0.104,
n = 345, p = 0.055. Marginal raw-significance; same reading as Group D
last-bar lower wick.

---

## Top 5 features by |stability_rho| (sample n >= 200)

(Same list as printed by `_run_microstructure_stability.py`. None survive
Bonferroni at family-size 187 on n = 345 — the same scale of finding as
E24 / E26's NULL_VERDICT. Two of the seven raw-significant features come
from Group F (range percentile), one from Group G (reversal rate),
one from Group D (lower wick), and three more are non-overlapping in
mechanism — meaning we have 4 distinct potential micro-axes worth
re-testing under K54 v2 train-set lift.)

| Rank | Feature | rho | n | p | Group |
|---:|---|---:|---:|---:|---|
| 1 | `micro_reversal_rate_m15_lb50` | -0.144 | 345 | 0.0073 | G — Streak / reversal |
| 2 | `range_pctile_h4_lb20` | +0.139 | 345 | 0.0095 | F — Range expansion |
| 3 | `range_pctile_h4_lb50` | +0.133 | 345 | 0.014 | F — Range expansion |
| 4 | `last_bar_lower_wick_ratio_m15` | +0.124 | 345 | 0.021 | D — Wick ratio |
| 5 | `longest_red_streak_m15_lb50` | +0.122 | 345 | 0.023 | G — Streak |

All five have raw p < 0.05. After Bonferroni (factor 187), all become
NO_SIGNAL. **Reading: at n = 345, microstructure features are individually
weak but several distinct axes show coherent direction with realized R.**
This is consistent with the Phase 1 audit finding that the K54 v1 effective
feature set was structure-only and time-only; microstructure provides
roughly 5 fresh quasi-orthogonal axes for the LightGBM tree splits to find
combinations on, even if no single feature is by itself decisive.

---

## Top 1 concern

**Tick coverage is the dominant gap.**

As of the 2026-04-28 audit cutoff, captured ticks under
`data/ticks/{symbol}/*.parquet` exist for **only 2 of 7 instruments**
(NAS100 + US30_cash) and **only for 2026-04-27** (one calendar day).
Because the tick daemon shipped on 2026-04-25, no pre-2026-04 stability
data exists for the 24 tick-data-required features in Group I. They
all show `stability_n = 0`.

Five instruments — XAUUSD, GBPJPY, GBPUSD, USDJPY, XAGUSD — have ZERO
tick coverage. Two — NAS100, US30_cash — have one day's coverage. The
production tick-capture daemon is per-orchestrator, so the gap reflects
which orchestrators were live with tick capture vs not as of the
cutoff.

Mitigation:

- **All 24 tick-required features emit `np.nan` (NOT zero) when
  `tick_df is None`.** LightGBM's missing-value branching will route
  these correctly without contaminating the loss surface.
- **Synthetic-tick features (Group H, 14 features)** provide a partial
  bridge: M1-derived Lee-Ready cum-delta and footprint imbalance. These
  ARE computable across all 7 instruments and the full 2026-01 to
  2026-04 window; n is 125-287 depending on lookback.
- **Forward plan**: as tick capture accumulates (now LIVE on production
  per `start_all.bat` per-orchestrator daemon), re-run
  `_run_microstructure_stability.py` at K54 v3 (Q2 Week 2-3) to
  populate `stability_n > 0` for Group I. Expected n by 2026-08-31:
  ~3000+ ticks per (symbol, day) × 60+ days × 7 instruments — sufficient
  for 0.05-resolution Spearman.

A second smaller concern is that the F11 stability sample is **100% F11
mechanical** trades. Per the K54 v1 audit Section 3, this is the same
limitation that K54 v1 hit — the AI-decision quadrant is empty. The
stability ρ values reflect "what would have happened on mechanical
ob_retest" not "what the AI evaluator does in real-time". K54 v2 should
duplicate this stability run on the trade_index + unified_csv sources
(once those are pre-2026-04 only) at K54 v2 mid-Week-3.

---

## Leakage self-check

For each of the 187 features, the implementation in
`research/ml_program/scripts/features/microstructure.py` follows the
"point-in-time" discipline:

- **`compute_microstructure_features` enforces the data cutoff.** Any
  `ts_close >= 2026-04-28 23:59 UTC` raises `ValueError` before any
  feature is touched.
- **`_slice_bars(df, ts_close, lookback)`** uses strict inequality
  `times < ts_close`. Bars whose CSV `time` (= bar OPEN) equals
  `ts_close` are excluded — they have not closed at `ts_close`. Callers
  pass `ts_close = bar_close_time = next_bar_open_time`, which is the
  earliest moment at which the candle's features become known.
- **`_slice_ticks(tick_df, ts_close, lookback_sec)`** uses
  `[ts_close - lookback_sec, ts_close)`, half-open at the right edge.
- **All FVG / OB / volume-profile aggregations** iterate ONLY the
  sliced window, never index forward in the parent dataframe.
- **Synthetic cum-delta and z-score** windows are constructed from
  `ts_close - k × lb_min` for k ∈ {0, 1, ..., 20}; baseline windows
  are STRICTLY EARLIER than the current window.
- **Tick-required features** consume `data/ticks/{symbol}/{date}.parquet`
  where `date = ts_close.strftime("%Y-%m-%d")`; ticks for
  `ts > ts_close` are filtered out by `_slice_ticks`. Cross-day ticks
  (e.g. ts_close at 00:30 UTC, prior 30 min spans the prior day) are
  NOT crossed because the loader is single-date — this is a known
  conservative limitation that produces NaN at session boundaries
  rather than leak across midnight.
- **No in-place mutation of input frames.** All slicing returns views
  / copies; no caller sees a modified `df_m15` etc.

Spot-check (random sample of 6 specs):

| Feature | Source slice | Boundary | Leakage risk |
|---|---|---|---|
| `ob_count_m15_lb20` | last 20 M15 bars where time < ts_close | strict < | none |
| `range_pctile_h4_lb50` | last 51 H4 bars; rank of last vs prior 50 | strict < | none — last value compared only to PRIOR window |
| `synthetic_cum_delta_m1_last_60min` | M1 bars in [ts_close - 60min, ts_close) | half-open | none |
| `synthetic_cum_delta_zscore_m1_60min_vs_lb20` | k=0 window + 20 prior 60-min windows | half-open ×21 | none — explicit k=0 vs k>0 separation |
| `real_cum_delta_last_30s` | ticks in [ts_close - 30s, ts_close) | half-open | none |
| `vpoc_dist_atr_m15_lb50` | last 50 M15 bars (after additional 14 for ATR) | strict < | none |

A regression test would set `ts_close` and a single bar at `time =
ts_close - 1ms`, then a second bar at `time = ts_close + 1ms`, and
verify the second bar is never included in any feature. Such a test is
out of scope for this catalog but is recommended at K54 v2 train-time
gate.

---

## Tick-coverage table

Per-instrument count of captured tick parquets and pre-2026-04 F11
trades available for stability scoring on tick-required features.

| Instrument | Tick parquets (any date) | Pre-2026-04 F11 trades | Tick coverage status |
|---|---:|---:|---|
| XAUUSD | 0 | 42 | ABSENT |
| GBPJPY | 0 | 49 | ABSENT |
| GBPUSD | 0 | 52 | ABSENT |
| USDJPY | 0 | 56 | ABSENT |
| XAGUSD | 0 | 45 | ABSENT |
| NAS100 | 1 (2026-04-27) | 49 | POST-CUTOFF ONLY |
| US30_cash | 1 (2026-04-27) | 52 | POST-CUTOFF ONLY |
| **Total** | **2** | **345** | — |

Only 2 of 7 instruments have ANY tick parquets. The 2 that do have only
1 day each, and that day (2026-04-27) is AFTER the pre-2026-04 boundary
used for stability scoring — so no pre-cutoff tick-required feature
values exist. **All 24 tick-required features have `stability_n = 0`
in the CSV.**

For the K54 v2 ENSEMBLE, this means LightGBM will see NaN for all 24
tick features on 100% of the pre-2026-04 training rows. The model
should learn to use "tick value present vs absent" as a binary signal
(cheap surrogate for "instrument is NAS100 or US30_cash AND date is
post-2026-04-25"). To prevent this surrogate from being a leak proxy
for symbol or date, K54 v2's training procedure should drop tick
features from the FEATURE_NAMES set if the model is trained on data
prior to widespread tick coverage.

Concrete recommendation to the orchestrator: **train K54 v2 with the
163 NON-TICK features as the primary feature set, and the 24 tick
features as a secondary set that ablation tests can include or exclude.**
The microstructure family's primary contribution to K54 v2 AUC is
expected to come from Groups A-H + J + K (= 163 features), not Group I.

---

## Inference-cost notes

`expensive_flag` in the CSV identifies features that may exceed
1 ms / candle when invoked in isolation. Two flag values:

- `EXPENSIVE` (13 features): large-lookback (>= 200 bars at M15) or
  M1-21-window operations. Empirically ~3-8 ms / candle on a single
  thread.
- `EXPENSIVE_TICK` (12 features): tick-data-required AND lookback >=
  300 s. When tick volume exceeds 50 000 in the lookback window
  (NAS100 active session), can hit 5-15 ms / candle.

In practice the K54 v2 training call computes all 187 features in one
sweep per candle, so the dispatch overhead amortizes. The per-batch
time on 345 candles × 187 features was ~12 seconds on the audit
machine — about 35 ms/candle/feature on average, dominated by:

- M1 cum-delta windows (Group H 240/480 min) at ~50 ms each
- Volume-profile binning (Group J 200-bar lookback) at ~8 ms
- Component-2 OB / FVG iteration over 200-bar M15 (Group A/B) at ~3 ms each

For inference-time deployment in production (one call per candle
close, ~one M15 candle per 15 min per instrument), 35 ms is
trivially well within budget.

---

## How to regenerate

```
# from repo root
python research/ml_program/scripts/features/_run_microstructure_stability.py --sample 350
# writes research/ml_program/feature_catalogs/microstructure.csv
```

The runner sources F11 records from
`research/edge_decomposition/F11_ob_zone_original_geometry/population.jsonl`
and OHLCV from `data/historical_2026/{symbol}_{tf}.csv`. Tick parquets
under `data/ticks/{symbol}/{date}.parquet` are loaded if present; absent
parquets produce NaN as documented. Override the F11 path with
`--out` for output CSV; defaults to the canonical catalog path.

---

## Cross-references

- **K54 v1 audit Section 5 microstructure subsection** —
  `research/ml_program/k54_v1_audit.md`. Identifies the v1 gap.
- **K54 v1 features list** — `research/ml_program/k54_v1_features.csv`.
  See row `microstructure,displacement_quality_score`.
- **Production market-state code** — `src/components/market_state.py`.
  Component 2 detectors (`identify_order_blocks`, `identify_fvgs`,
  `detect_swings`, `detect_structure_breaks`, `detect_sweeps`,
  `_count_touches`).
- **E24 / E26 prior microstructure analysis** —
  `src/research_infra/microstructure_features.py` +
  `src/research_infra/synthetic_tick_reconstructor.py`. NULL_VERDICT
  context preserved in `project_microstructure_archived_2026-04-27`.
- **Edge mechanism** — `.context/01_knowledge_base/edge_mechanism.md`.
  Microstructure features are observation-only; the OB-zone-precision
  edge is the load-bearing mechanism — not microstructure.
- **Project rules** — `CLAUDE.md` (data cutoff, no production state
  changes, walk-level evidence is not predictive of realized R, etc).
