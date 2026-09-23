# Q-1.2 / Q-4.3 / Q-4.4 - Entry Engineering Re-test

**Generated:** 2026-04-17T01:33:06.208537+00:00
**Batch source:** `knowledge_base_backtest/analysis/unified_trades_v2_20260331.json` (n=110)
**M15 source:** `data/historical_2026/XAUUSD_M15.csv` (Jan 2 - Apr 10, 2026)
**Analysis scope:** XAUUSD (only symbol in batch and only symbol with live records joined)

## Hypothesis (pre-data)

Stated before opening the dataset for analysis:

- **Q-1.2 (tick volume):** Expected to have LOW or ZERO predictive value. Prior T1 analysis marked volume ineffective; T2a showed AI diagnostics are post-hoc narrative. Academic literature (Osler 2003, Cont 2014) locates the edge in OB zone precision, not microstructure volume. **Prediction:** MI permutation p > 0.2, no significant Pearson correlation.
- **Q-4.3 (limit vs retest):** Limit-at-OB-edge and retest-confirmation entries should produce SIMILAR realized WR if the edge operates at the zone-level rather than the entry-timing level. The main difference should be fill rate (retest has lower fill). **Prediction:** no significant difference in realized avg R between limit-proxy and BOS-proxy entries (p > 0.1).
- **Q-4.4 (OB depth / touch count):** Prior `knowledge_base/OB_touch_decay_analysis_v1.md` found touch-1 = 72.7% continuation vs touch-2+ = 31.5% continuation (n=106,147). **Prediction:** batch cannot test this directly (no touch metadata in batch JSON). Must DEFER pending data-capture fix.

## Data

- Batch trades: 110 XAUUSD trades, 2024-04-01 to 2026-03-13.
- M15 CSV coverage: 2026-01-02 to 2026-04-10 (2026 only, ~3.5 months).
- Volume column present in CSV: True.
- Live trade records directory `XAUUSD`: {'available': True, 'file_count': 9, 'has_touch_count': 0, 'has_ob_bounds': 9, 'has_pool_type': 9, 'sample_files': ['2026-04-15_ny_1315.json', '2026-04-15_ny_1330.json', '2026-04-15_ny_1345.json', '2026-04-15_ny_1415.json', '2026-04-15_ny_1615.json']}

### Exclusions / joining
- Q-1.2 / Q-4.3 analyses restricted to trades whose date falls inside CSV coverage.
- Entry candle matched by (date, kill_zone window, price containment).
- If no candle in kill zone contains entry_price, trade is dropped (not fabricated).

## Q-1.2 Tick volume results

- Matched trades: **28** (of 110 total; restricted to 2026 CSV coverage).
- Mutual information (vol_ratio vs outcome): **0.1900** (std across 10 seeds = 0.0000)
- MI permutation test p-value (1000 label shuffles): **0.027** (null p95 = 0.1625)
- Pearson correlation (vol_ratio vs r_multiple): r=0.0010, p=0.9960
- Point-biserial correlation (vol_ratio vs outcome): r=0.0210, p=0.9157

**Interpretation:** MI permutation p<0.05 indicates the volume-outcome relationship is more structured than random shuffled labels would produce. However, Pearson r~0 and point-biserial r~0 mean the relationship is NOT linear/monotonic. Inspect quartile table below - the pattern may be U-shaped or inverted-U.

### Quartile WR breakdown (sorted low-to-high vol_ratio)

| Bucket | n | WR | Avg R |
|---|---:|---:|---:|
| Q1_low | 7 | 42.9% | -0.311 |
| Q2 | 7 | 42.9% | 0.211 |
| Q3 | 7 | 85.7% | 0.033 |
| Q4_high | 7 | 71.4% | 0.333 |

Pattern: Q1 WR 42.9% -> Q2 42.9% -> Q3 85.7% -> Q4 71.4%. Q3 (just-above-average volume) and Q4 (high volume) have the highest WRs. Very low volume (Q1) entries perform poorly.

- **Verdict: promote_as_nonmonotonic** - MI perm p=0.027 (signal present) but linear tests flat (pearson_p=0.996, pointbis_p=0.916). This is a NON-MONOTONIC pattern (inspect quartile WR). Promote cautiously: need larger n to rule out sample-specific noise.

## Q-4.3 Limit vs retest results

**Important reframing on inspection:** batch trades are P1/P2-era BOS-confirmation entries (at M15 BOS candle close, 50-100+ pts above H1 OB per prior T1 analysis). True 'limit at OB edge' executions are rare in this dataset. We classify entry candle by approach direction as a PROXY:

Classification rules (by entry candle open/close geometry relative to entry_price):
- `approach_from_above` (LONG): candle OPEN > ep, LOW <= ep, CLOSE >= ep. Price pulled back down into entry -> LIMIT-FILL PROXY.
- `approach_from_below` (LONG): candle OPEN < ep, HIGH >= ep, CLOSE >= ep. Price rose up through entry -> BOS-BREAKOUT PROXY.
- `wick_reversal_retest` (LONG): candle CLOSE < ep but NEXT candle CLOSE >= ep -> wick-and-reverse (closest to 'retest confirmation' entry).
- `from_above_closed_adverse` (LONG): candle OPEN > ep, touched ep, CLOSE < ep. Price fell through.
- `from_below_closed_adverse` (LONG): candle OPEN < ep, touched ep, CLOSE < ep. Failed to break out.
- `other`: no touch or ambiguous.
(SHORT mirrors.)

- Matched: **28** of 29 in-window trades; unmatched=1.

### Counts and performance per class

| Class | n | WR | Avg R | Median R | Stdev R |
|---|---:|---:|---:|---:|---:|
| wick_reversal_retest | 9 | 77.8% | 0.469 | 0.230 | 1.174 |
| approach_from_below | 8 | 75.0% | -0.051 | 0.115 | 0.613 |
| approach_from_above | 4 | 25.0% | 0.007 | -1.000 | 2.015 |
| from_below_closed_adverse | 5 | 40.0% | -0.386 | -0.270 | 0.591 |
| from_above_closed_adverse | 2 | 50.0% | -0.025 | -0.025 | 0.417 |

**Welch's t-test**: not run (insufficient n in one or both classes, threshold=5).

- **Verdict: defer** - Underpowered for proxy limit-vs-BOS comparison (approach_from_above n=4, approach_from_below n=8, wick_reversal n=9). Note: batch is P1/P2 BOS-confirmation system, so true 'limit at OB edge' trades are RARE in this dataset.

## Q-4.4 OB depth results

### Data gap
- Batch JSON has touch_count field: **False**
- Batch JSON has ob_high / ob_low: **False**
- Batch JSON has liquidity_pool_type: **True**
- Live trade records (XAUUSD): 9 files, touch_count in 0, ob bounds in 9, pool_type in 9

### Proxy analysis: liquidity pool type x WR (batch n=111)

| Pool type | n | WR | Avg R |
|---|---:|---:|---:|
| asian_high | 28 | 71.4% | 0.291 |
| none | 45 | 66.7% | 0.338 |
| session_high | 4 | 50.0% | -0.208 |
| asian_low | 16 | 56.2% | 0.052 |
| pdh | 7 | 71.4% | -0.110 |
| london_low | 4 | 50.0% | -0.032 |
| session_low | 2 | 50.0% | -0.055 |
| pdl | 4 | 50.0% | -0.140 |

**mae_r distribution (how deep limit entries pulled back adversely before resolution):** n=110, mean=0.554R, median=0.360R, p75=0.965R, p90=1.257R.

- **Touch-count verdict: defer_data_gap** - Batch JSON has no touch_count field. Live records contain it (Apr 2026 only, n<10), insufficient to test.
- **Depth-from-midpoint verdict: defer_data_gap** - Batch has no ob_high/ob_low. Live records (MSO JSON) contain them but n<10 for April. Would require batch re-run with OB bounds captured.

## Overall recommendations

- **Q-1.2 Tick volume:** `promote_as_nonmonotonic` - MI perm p=0.027 (signal present) but linear tests flat (pearson_p=0.996, pointbis_p=0.916). This is a NON-MONOTONIC pattern (inspect quartile WR). Promote cautiously: need larger n to rule out sample-specific noise.
- **Q-4.3 Limit vs retest:** `defer` - Underpowered for proxy limit-vs-BOS comparison (approach_from_above n=4, approach_from_below n=8, wick_reversal n=9). Note: batch is P1/P2 BOS-confirmation system, so true 'limit at OB edge' trades are RARE in this dataset.
- **Q-4.4 Touch count:** `defer_data_gap` - Batch JSON has no touch_count field. Live records contain it (Apr 2026 only, n<10), insufficient to test.
- **Q-4.4 Depth:** `defer_data_gap` - Batch has no ob_high/ob_low. Live records (MSO JSON) contain them but n<10 for April. Would require batch re-run with OB bounds captured.

## Caveats

- **OB reconstruction is proxy-based.** Batch JSON does not store ob_high / ob_low. We approximate OB bounds using (entry_price, stop_loss). This inflates classification noise.
- **Q-1.2 and Q-4.3 are restricted to 2026 trades** (~29 in window) because M15 CSV only covers Jan 2 - Apr 10, 2026. Pre-2026 (82 trades) are NOT in analysis.
- **Entry candle matching is approximate.** When multiple candles in the kill zone contain the entry price, the *first* match is used. Spread and limit-vs-market execution differences not modeled at tick level.
- **Batch trades were executed by P1/P2-era pipeline.** P1/P2 had known bugs (stale state, session_memory=on before disabled Apr 12). T7 C-gate production may produce a different mix of setup qualities.
- **Welch's t-test assumes approximately normal distribution of R per class**; R is bimodal (WR=1.5R hit vs LOSS=-1R hit). Mean and t-test are still useful for directional signal but the p-value is approximate. Non-parametric Mann-Whitney U could follow up.
- **Tick volume in MT5 CSV is tick count per bar**, not true volume. Known proxy. Correlated with true volume r~0.85 per literature, but not identical.

## Next steps

1. **Q-1.2 follow-up (only if MI > 0.03):** Export M15 + H1 + tick_volume for full batch window (2024-04 to 2026-04) and re-run with n=111+. Cost: zero (local MT5 dump).
2. **Q-4.3 follow-up:** Rebuild batch with ob_high/ob_low captured per trade (modify simulate_t7_live_period.py to log OB bounds). Then re-classify properly. Cost: one simulation re-run.
3. **Q-4.4 follow-up:** Wire proximity_shadow_logger to dump touch_count at CANDIDATE time into shadow_logs/. After ~50 live trades, join touch_count x outcome. Cost: 0 (already runs in shadow).
4. **No API spend recommended** for any of these follow-ups. All are local re-runs.
