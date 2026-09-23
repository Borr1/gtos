# T1 — Entry Engineering Empirical Tests (Q-4.1 to Q-4.4)
## For: Claude Code execution agent (Sonnet, max effort)
## Date: April 11, 2026
## Written by: Strategic Research Advisor
## Basis: phase1_entry_engineering_papers_v1.md (51 papers, 4 tests identified)

---

## Overview

Run 4 empirical tests on GTOS batch trade data to answer the entry engineering questions identified by the literature search. All 4 tests share the same data — load once, analyze four ways.

**Bonferroni correction applies:** 4 simultaneous tests, so significance threshold is p < 0.0125 (not 0.05).

**Practical significance threshold:** Effects smaller than 0.05R per trade or 2pp WR are "statistically detectable but practically negligible" — document them but do not recommend changes.

---

## Phase 0: Data Discovery and Extraction

Before running any test, build the unified dataset. This is the most important phase — get the data right.

### Step 0.1: Find the batch trade population

The trade index is at `knowledge_base/index/_trade_index.json`. It contains ~129 trades with:
- trade_id, date, symbol, direction, kill_zone
- outcome (WIN/LOSS), r_multiple, mfe_r, mae_r, hold_time_candles
- displacement_quality, setup_grade, framework, day_of_week

It does NOT contain: entry_price, stop_loss, take_profit, OB zone boundaries.

### Step 0.2: Extract trade parameters from session files

Session files are in `knowledge_base/sessions/{SYMBOL}/YYYY-MM-DD_session.json` for:
- GBPUSD (~201 files)
- US30_cash (~121 files)
- USDJPY (~114 files)

XAUUSD batch sessions are NOT in this directory. Check `knowledge_base/live_sessions/XAUUSD/` and `knowledge_base/live_evaluations/XAUUSD/` for live data (only ~5 days, Apr 6-10).

For each trade in the trade index:
1. Parse the trade_id to get date, kill_zone, symbol
2. Find the corresponding session file
3. In the session file, find the candle_evaluation where `decision == "CANDIDATE"` and `trade_id` matches
4. Extract: entry_price, stop_loss, take_profit_1 (these may be nested inside the evaluation or in a `trade_result` block)

If entry_price is not in the session file, check `knowledge_base/trade_records/{SYMBOL}/` for detailed trade records with verification data including OB zone boundaries.

### Step 0.3: Extract OB zone boundaries

For each CANDIDATE trade, the OB zone used is documented in either:
- The AI evaluation's `h1_setup` fields (poi_price_level, poi_type)
- The verification checks in trade_records (e.g., "H1 OB found at 159.59-159.72")
- The session file's evaluation details

Search for these fields in the data:
```
grep -r "ob_zone\|poi_price_level\|order_block.*high\|order_block.*low" knowledge_base/sessions/ | head -20
```

If OB zone boundaries (zone_high, zone_low) cannot be extracted for a trade, mark it as `zone_data_missing=True`. Tests 1 and 4 only run on trades with zone data. Tests 2 and 3 may use entry_price and M15 OHLC.

### Step 0.4: Build unified DataFrame

Create a pandas DataFrame with one row per trade:

```python
columns = [
    'trade_id', 'date', 'symbol', 'direction', 'kill_zone',
    'outcome', 'r_multiple', 'mfe_r', 'mae_r', 'hold_time_candles',
    'displacement_quality', 'setup_grade',
    'entry_price', 'stop_loss', 'take_profit_1',
    'ob_zone_high', 'ob_zone_low',          # OB zone boundaries
    'ob_zone_width',                          # abs(zone_high - zone_low)
    'entry_depth_pct',                        # how deep into zone (0% = edge, 100% = far end)
    'candle_open', 'candle_high', 'candle_low', 'candle_close',  # M15 CANDIDATE candle OHLC
    'zone_data_available', 'candle_data_available'
]
```

**Compute derived fields:**
- `ob_zone_width = abs(ob_zone_high - ob_zone_low)`
- For LONG trades: `entry_depth_pct = (entry_price - ob_zone_low) / ob_zone_width * 100` (0% = entered at zone bottom/edge, 100% = entered at zone top/far end)
- For SHORT trades: `entry_depth_pct = (ob_zone_high - entry_price) / ob_zone_width * 100` (0% = entered at zone top/edge, 100% = entered at zone bottom/far end)
- Note: "edge" means the side where price enters from; "far end" is where the SL sits

Save the unified dataset as `research/academic_pipeline/data/entry_engineering_dataset.csv`

### Step 0.5: Report data availability

Before running tests, report:
- Total trades in index
- Trades with entry_price extracted
- Trades with OB zone boundaries extracted
- Trades with M15 candle OHLC extracted
- Breakdown by instrument
- Any instruments completely missing (e.g., XAUUSD batch sessions)

If fewer than 50 trades have zone data, Tests 1 and 4 will have low power. Document this limitation. Do NOT fabricate data to fill gaps.

---

## Test 1: Entry Depth vs Trade Outcome (Q-4.1 + Q-4.4)

**Hypothesis:** Trades that enter deeper into the OB zone (closer to the SL end) have different R:R and WR than trades entering at the zone edge.

**Prediction from literature (Baviera 2019, Leung & Li 2015):** Optimal entry is at 40-60% depth. Entering at 0% (zone edge) wastes R:R potential. Entering near 100% (far end) has higher failure rate because you're closest to the invalidation level.

**Method:**
1. Filter to trades with `zone_data_available == True`
2. Compute entry_depth_pct (already derived in Step 0.4)
3. Bin into quartiles: Q1 (0-25%), Q2 (25-50%), Q3 (50-75%), Q4 (75-100%)
4. For each quartile, compute:
   - n (sample size)
   - Win rate with Wilson 95% CI
   - Mean r_multiple with 95% CI (bootstrap, 10000 iterations, seed=42)
   - Mean mfe_r (maximum favorable excursion)
   - Mean mae_r (maximum adverse excursion)
   - Expectancy = mean(r_multiple)
5. Test: Kruskal-Wallis across quartiles on r_multiple (non-parametric, appropriate for non-normal R distributions)
6. If Kruskal-Wallis significant at p < 0.0125: run pairwise Mann-Whitney with additional Bonferroni correction (6 pairs → p < 0.0125/6 = 0.002)
7. Compute Spearman rank correlation: entry_depth_pct vs r_multiple

**Per-instrument analysis:**
- Run the above for each instrument separately (if n >= 15 per instrument)
- For instruments with n < 15: report point estimates only, flag "low power"
- If only one instrument has sufficient data: note that findings may not generalize

**Output:**
- Summary table: quartile × {n, WR, WR_CI, mean_R, expectancy}
- Per-instrument table (same structure, if n sufficient)
- Spearman rho and p-value
- Kruskal-Wallis statistic and p-value
- Histogram: entry_depth_pct distribution (are entries clustered at a particular depth?)
- Scatter plot: entry_depth_pct vs r_multiple (if matplotlib available)

---

## Test 2: Market Order vs Limit Order Decision (Q-4.2)

**Hypothesis:** Placing a limit order at the 50% depth of the OB zone (instead of a market order at M15 close) would change expected outcome.

**Prediction from literature:** Limit orders save the spread (~$0.50 on XAUUSD, ~1-2 pips on FX) but face adverse selection (DeLise 2024) and non-fill risk. For a cascade strategy, market orders may be structurally better (Osler 2005).

**Data requirement:** This test needs both (a) entry_price and OB zone boundaries and (b) whether price actually reached the 50% zone depth AFTER the signal candle. Checking (b) requires subsequent M15 candle OHLC data.

**Feasibility check:**
- If M15 candle data is NOT available in the session files: use the `mfe_r` and `mae_r` fields as a proxy. If mae_r > 0 for a trade, price DID move adversely into the zone — meaning a deeper limit order would have filled. This is an imperfect proxy but better than nothing.
- If M15 candle data IS available: use the actual subsequent candles to check fill.

**Method (full version, if candle data available):**
1. For each CANDIDATE trade with zone data:
   a. Compute limit_order_price at 50% of OB zone
   b. Check subsequent M15 candles (same session): did price reach limit_order_price?
   c. If yes: compute hypothetical entry at limit_order_price, same SL/TP → hypothetical r_multiple
   d. If no: mark as MISSED_TRADE
2. Compare:
   - Fill rate: what % of trades would have filled at 50% depth?
   - For filled trades: mean r_multiple (market) vs mean r_multiple (limit)
   - Expected value: E[R_market] vs P(fill) × E[R_limit|fill]

**Method (proxy version, if candle data unavailable):**
1. Use mae_r as proxy for "did price go deeper into zone"
2. For trades where mae_r > threshold_R (meaning price pulled back significantly):
   - These would likely have filled a deeper limit order
   - Compute the R improvement from better entry price
3. Estimate fill rate from mae_r distribution
4. Report as "proxy analysis — requires candle data for definitive answer"

**Statistical test:** Paired Wilcoxon signed-rank test on r_multiple (market vs hypothetical limit) for filled trades only. Significance threshold: p < 0.0125.

**Output:**
- Fill rate at 25%, 50%, 75% zone depth
- R improvement per filled trade (mean, median)
- Net expected value comparison (accounting for missed trades)
- Recommendation: market, limit, or "insufficient data"

---

## Test 3: Alpha Decay Within M15 Candle (Q-4.3)

**Hypothesis:** The expected trade outcome differs if you enter at the M15 candle open vs close.

**Prediction from literature (Lehalle & Neuman 2019):** At zero market impact, optimal execution is immediate. At the M15 timescale, alpha decay is likely < 1 pip (< 0.05R). Effect should be negligible.

**Data requirement:** M15 candle open and close prices for each CANDIDATE candle.

**Feasibility check:**
- If candle OHLC is in the session files: use directly
- If NOT available: this test CANNOT be run with existing data. Document this as "DATA_UNAVAILABLE — requires M15 candle OHLC for CANDIDATE signals. Recommend adding candle_open/close to session file schema for future data collection."

**Method (if candle data available):**
1. For each CANDIDATE trade:
   - Record entry at candle_close (current behavior) and hypothetical entry at candle_open
   - Compute R-multiple for each entry price (same SL/TP)
   - Compute delta_R = R_close_entry - R_open_entry
2. Summary statistics: mean(delta_R), median(delta_R), std(delta_R)
3. Test: one-sample Wilcoxon signed-rank test (is delta_R significantly different from 0?)
4. If |mean(delta_R)| < 0.05R: conclude negligible regardless of p-value

**Output:**
- mean delta_R and 95% CI
- Wilcoxon p-value
- Conclusion: negligible / worth investigating / significant

---

## Test 4: OB Zone Width vs Trade Outcome (Q-4.4)

**Hypothesis:** OB zone width (in price units) predicts trade outcome.

**Prediction from literature (Tsinaslanidis 2022):** Wider zones have slightly higher bounce probability (more order accumulation) but lower R:R (SL must be wider). Net effect on expectancy is ambiguous.

**Method:**
1. Filter to trades with zone data available
2. Normalize zone width: for each instrument, compute zone_width_atr = ob_zone_width / ATR(14). This makes the measure comparable across instruments.
   - If ATR is not in the trade data, use zone_width in raw price units and analyze per-instrument only
3. Bin zone_width_atr into quartiles
4. For each quartile, compute:
   - n, WR (Wilson CI), mean r_multiple (bootstrap CI, seed=42), mean mfe_r, mean mae_r
   - Expectancy = mean(r_multiple)
5. Test: Spearman correlation between zone_width_atr and r_multiple
6. Test: Spearman correlation between zone_width_atr and WR (using binary 0/1 outcome)

**Per-instrument analysis:**
- Same as Test 1 — per-instrument if n >= 15, flag "low power" otherwise

**Output:**
- Summary table: quartile × {n, WR, WR_CI, mean_R, expectancy}
- Spearman rho and p-value (zone width vs r_multiple)
- Spearman rho and p-value (zone width vs WR)
- Scatter plot: zone_width_atr vs r_multiple
- Per-instrument table if sufficient data

---

## Phase 5: Synthesis

After running all 4 tests (or as many as data permits), write a synthesis section:

1. **What we can answer:** Which tests produced statistically significant results? Which are practically significant (> 0.05R or > 2pp WR)?

2. **What we can't answer:** Which tests were blocked by missing data? What data would be needed?

3. **Actionable recommendations:** For each test with a significant, practically meaningful result:
   - What specific change to the system would this imply?
   - Estimated impact (delta R per trade, delta WR)
   - Implementation complexity (trivial / moderate / complex)

4. **Null results:** For each test with no significant result: document clearly. "No evidence that X matters" is a valuable finding — it means we don't need to spend engineering effort optimizing X.

---

## Output File

Save the complete results to: `research/academic_pipeline/results/T1_entry_engineering_results_v1.md`

Include:
- Data availability summary (Phase 0.5)
- Results for each test (or DATA_UNAVAILABLE with explanation)
- All statistical tests with exact p-values
- Synthesis and recommendations
- Raw summary tables

Also save the unified dataset CSV to: `research/academic_pipeline/data/entry_engineering_dataset.csv`

---

## Constraints

- **Do NOT modify any files in src/ or prompts/**
- **Do NOT fabricate data.** If data is missing, say so. "Data unavailable" is always an acceptable result.
- **seed=42** for all bootstrap and randomization
- **Bonferroni threshold: p < 0.0125** for the 4 primary tests
- **Wilson confidence intervals** for all proportions (NOT Wald — Wald fails at extreme p or small n)
- **Per-instrument analysis is mandatory** where sample size permits (n >= 15)
- **Never overwrite existing files** — use _v1 suffix
- If any instrument has 0 trades with zone data, document it — do not omit it silently

---

## Pressure Test Log

**Issues found and fixed before delivery:**
1. Tests assumed OB zone data would be in trade index — it's NOT. Added data discovery phase with fallback sources.
2. Tests 2 and 3 need M15 candle OHLC which may not exist in repo — added feasibility check and proxy method for Test 2.
3. Zone width comparison across instruments is meaningless in raw units — added ATR normalization.
4. Original entry_depth_pct definition was ambiguous for LONG vs SHORT — clarified that "edge" = side where price enters from, "far end" = SL side.
5. Missing Bonferroni correction for 4 simultaneous tests — added p < 0.0125 threshold.
6. Missing practical significance threshold — added 0.05R / 2pp minimum for actionable findings.
7. Missing Wilson CI specification — Wald CIs fail at extreme proportions and small n.
8. No fallback for XAUUSD batch data (sessions not in expected directory) — added note about live_sessions/XAUUSD/ and live_evaluations/XAUUSD/ as alternatives.
