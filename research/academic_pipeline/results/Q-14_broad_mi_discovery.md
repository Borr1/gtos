# Q-14 Broad Mutual-Information Edge Discovery

Generated: 2026-04-17 (from JSON run 02:39:14 UTC)
Script: `research/academic_pipeline/scripts/q_14_broad_mi.py`
Cost: $0 (local only). 500 permutations × 26 features × 4 horizons × 5 symbols.

## Covers

- Q-14.13 Information-theoretic broad MI feature discovery
- Q-14.8  Trade-flow imbalance from OHLCV (VPIN / BVC / tick rule)
- Q-14.2  Institutional algo footprints in OHLCV (TWAP / iceberg patterns)

## Pre-registered hypotheses (stated BEFORE inspecting results)

Read `q_14_broad_mi.py` docstring lines 15-50 for the full pre-registration.

- **H-14.8-1**  VPIN_t (BVC-based, bucket=50 M15) carries non-zero MI with sign(return_{t+k}) for k in {1,3,6,12}. Prior: weak.
- **H-14.8-2**  At OB-trigger candles, trades in the high-VPIN tercile win more often than low-VPIN. Prior: unknown.
- **H-14.2-1**  Equal-close streak features correlate positively with mean reversion at k=3..12. Prior: weak.
- **H-14.2-2**  Close-location-in-range asymmetry carries MI with sign(return_{t+1}). Prior: null in random walk.
- **H-14.13-1** At least one of ~25 candle-shape features clears Bonferroni 99.83rd-pct null (alpha=0.05/30 tests).
- **H-14.13-2** The top-MI feature will be a volatility-regime variable (rv/atr), NOT a microstructure feature. Volatility clusters; regime variables routinely show spurious MI.

Honest null expectation: on M15 retail-broker OHLCV (no true order flow, no level-II), all three questions will return weak or null results.

## Data

- XAUUSD, US30, USDJPY, GBPJPY, GBPUSD M15 CSVs from `data/historical_2026/` — 6,300-6,400 bars each, Jan 2 - Apr 10 2026.
- VPIN subgroup: XAUUSD batch trades from `unified_trades_v2_20260331.json` intersected with 2026 M15 window (n=29).

## Method

For each (symbol, feature, horizon k), compute mutual information between feature at time t and outcome at t+k:

- **dir_mi**: MI(feature_t, sign(return_{t+k}))  — direction predictability
- **ret_mi**: MI(feature_t, return_{t+k})        — magnitude predictability

Compare observed MI vs 500 random-shuffle permutations of the outcome. A feature "passes" if:

1. permutation p < 0.00167 (Bonferroni: 0.05 / 30)
2. ESS-adjusted permutation also passes (Bartlett correction, to account for serial correlation in features)

Cross-symbol ranking takes the top 30 dir_mi and top 30 ret_mi across all 520 tests (26 features × 4 horizons × 5 symbols).

## Results

### Headline: Bonferroni passers are all vol-regime, not microstructure

Top-30 **dir_mi** feature composition:

| Feature family | Count in top 30 | Example MI (bits) |
|---|---|---|
| Volatility regime (rv20, rv50, atr14, vol_ratio) | **21** | 0.003 - 0.007 |
| Flow / imbalance (vpin, tick_imbalance, volume, signed_tick_vol) | **8** | 0.003 - 0.007 |
| Candle shape (body, wicks, close_loc, wick_asym, eq_close, signed_body, gap) | **0** | n/a |
| Other (range_compression) | 1 | 0.003 |

Top-30 **ret_mi** (magnitude) feature composition:

| Feature family | Count in top 30 | Example MI (bits) |
|---|---|---|
| Volume / range (volume, range, signed_tick_vol) | **18** | 0.08 - 0.15 |
| Volatility regime (atr14, rv20, rv50) | **12** | 0.07 - 0.10 |
| Candle shape | **0** | n/a |

**H-14.13-2 is confirmed exactly as pre-registered.** Every single top-30 passer is a vol/range/flow/regime feature. Zero candle-shape features (body_over_range, wick_asymmetry, close_loc_in_range, eq_close_streak, abs_close_off_mid, signed_body, gap_from_prior_close) cleared Bonferroni on any symbol at any horizon.

### XAUUSD-specific passers (primary instrument)

**dir_mi top passers:**

| feature | k | MI | mean null | max null | perm_p | ESS_pass |
|---|---|---|---|---|---|---|
| vpin | 12 | 0.00339 | 0.00135 | 0.00167 | 0.000 | true |
| rv50 | 12 | 0.00288 | 0.00131 | 0.00169 | 0.000 | true |
| vpin | 3 | 0.00270 | 0.00146 | 0.00185 | 0.002 | true |
| rv20 | 12 | 0.00270 | 0.00133 | 0.00173 | 0.000 | true |

**ret_mi top passers:**

| feature | k | MI |
|---|---|---|
| range | 1 | 0.0937 |
| atr14 | 1 | 0.0851 |
| range | 3 | 0.0837 |
| atr14 | 3 | 0.0835 |
| volume | 1 | 0.0827 |
| signed_tick_vol | 1 | 0.0801 |
| rv20 | 3 | 0.0781 |
| rv20 | 1 | 0.0775 |
| rv50 | 6 | 0.0761 |
| rv50 | 3 | 0.0755 |

Interpretation: dir_mi magnitudes (0.003 bits) are effectively noise-level — they reach statistical significance only because n≈6,300 and 500 permutations give narrow nulls. The MI is detecting vol clustering, not direction. ret_mi is higher (0.07-0.09 bits) because volume/range autocorrelate in a vol-clustering regime, so present volume predicts future magnitude. This is textbook GARCH structure, not alpha.

### Q-14.8-2 VPIN tercile at OB-trigger candles (XAUUSD 2026 batch, n=29)

Pre-registered direction: HIGH-VPIN trades should win more than LOW-VPIN. Actual:

| VPIN tercile | n | WR |
|---|---|---|
| low (vpin < 0.450) | 10 | **0.80** |
| mid | 9 | 0.56 |
| high (vpin > 0.495) | 10 | 0.50 |

Fisher's exact (high vs low): odds 0.25, **p = 0.350** — underpowered.

The sign is INVERTED from pre-registration. Low VPIN (less "toxic" flow in Easley/O'Hara's framing) is associated with higher WR on OB-retests. This is directionally consistent with the fade-the-cascade mechanism already driving GTOS — OBs work best when flow is two-sided, not when one side dominates. But n=10 per tercile is far below any deployment gate.

Caveats (in addition to pre-reg):
- Tick-volume on gold CFD is a proxy, not true trade count.
- Only 29/111 batch trades fall inside the 2026 M15 window (same root cause as Q-crowding_retail — 2024-2025 M15 data gap).
- Bonferroni α for the VPIN tercile test alone = 0.05; with 4 other pre-registered hypotheses the joint α = 0.0125. p=0.35 fails both.

### Q-14.2 TWAP / iceberg proxies (eq_close_5, eq_close_streak, close_loc_in_range, abs_close_off_mid)

None of these features made the top-30 dir_mi for any symbol at any horizon. All permutation p-values > 0.05. **REJECT H-14.2-1 and H-14.2-2.** On this OHLCV data with tick-volume proxy, candle-shape patterns associated with algo execution do not carry predictive information for M15 direction.

### Per-symbol summary (passers in top 30 dir_mi)

| symbol | passers | note |
|---|---|---|
| US30 | 8 | Dominated by rv20/rv50 and range_compression |
| USDJPY | 7 | rv20 k=6/12, atr14 k=6/12 |
| GBPJPY | 6 | rv20/rv50 k=12, vol_ratio |
| GBPUSD | 5 | atr14 k=12, rv20 k=12 |
| XAUUSD | 4 | vpin k=3/12, rv20/rv50 k=12 |

XAUUSD has the fewest passers — gold is the hardest-to-predict-from-shape instrument in this panel, consistent with its reputation for micro-noise driven by macro narratives rather than flow imprints.

## Verdicts

- **H-14.13-1 (at least one Bonferroni passer):** TECHNICALLY PASSES (30 features clear perm p < 0.00167 and ESS gate). But every single passer is a vol-regime or flow-proxy feature, not an independent shape-based edge. In spirit, NULL.
- **H-14.13-2 (top feature is vol regime):** **CONFIRMED** exactly. rv20/rv50/atr14 own the ranking. Vol clustering re-validated; no hidden microstructure edge.
- **H-14.8-1 (VPIN→sign MI):** TECHNICAL PASS for XAUUSD vpin k=3/12 (perm p < 0.005) but MI=0.003 bits is not actionable signal.
- **H-14.8-2 (high-VPIN at OB wins):** **REJECTED** — sign inverted AND underpowered (Fisher p=0.35). LOW-VPIN wins more (WR 80% vs 50%), consistent with fade-the-cascade mechanism but not statistically conclusive.
- **H-14.2-1 (eq_close → mean-rev):** REJECTED. Not in top 30 for any symbol.
- **H-14.2-2 (CLV asymmetry → sign):** REJECTED. Not in top 30 for any symbol.

## Classification

**NULL discovery.** This broad sweep failed to find a candle-shape or microstructure feature that adds directional MI beyond what volatility regime already explains. The OHLCV proxy family is exhausted for direction prediction on M15 retail-broker data. Corroborates Q-14.14 (separate report: zero direction-prediction passers across 5 OHLCV microstructure proxies) and Q-13.5 (cross-asset lead-lag NULL) — three independent tests, three nulls in the same direction.

## What this means for GTOS

1. **Do not wire any shape/microstructure feature into entry gating.** The AI's C-gate (H1-bias, M15-non-opposing, direction-match) is already operating at the MI ceiling accessible from OHLCV.
2. **Vol-regime is the only MI-earning feature.** GTOS already implicitly uses ATR for SL sizing and regime filters. Do not add a redundant rv20 "predictor" — it would correlate with ATR-based gates already in place.
3. **LOW-VPIN directional flag is worth one monitor slot** if the pre-2026 M15 gap is ever closed. With 111+ batch trades matched to VPIN terciles, the low-VPIN=high-WR pattern could become significant. Until then: shadow-log only, no deployment.
4. **Candle-shape feature engineering is a dead end on this data source.** Future effort should target true tick-level order flow (broker API or Level II), not more OHLCV transformations.

## Caveats / data gaps

- **Tick-volume proxy** on CFD XAUUSD is not true trade count; dampens VPIN signal quality. Same limitation as Q-14.9/14.11 and Q-16.5.
- **2024-2025 M15 data gap:** only 29/111 batch trades available for VPIN-tercile test. Filling this gap is prerequisite for upgrading H-14.8-2 from underpowered to conclusive.
- **DST transition** (Mar 8 US, Mar 29 EU) introduces 1h session drift on kill-zone-aware features.
- **Broker timestamps** not strict UTC; same convention as other Q-14 / Q-crowding_retail scripts.
- **No out-of-sample check** — this is in-sample on 2026 Q1. Any "passer" would need 2024-2025 or post-Apr-10 OOS to earn shadow-logger status.

## Artifacts

- Script: `research/academic_pipeline/scripts/q_14_broad_mi.py`
- Raw JSON (all 520 tests): `research/academic_pipeline/results/Q-14_broad_mi_discovery.json`
- This report: `research/academic_pipeline/results/Q-14_broad_mi_discovery.md`

*End of report.*
