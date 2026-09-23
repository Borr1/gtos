# Phase 1 Track A — XAUUSD Reverse-Engineering RECON

Branch: `research/phase1-track-a-xauusd-reverse`  Worktree: `.claude/worktrees/agent-a7c39cbfec5fec7b2/`  Date: 2026-04-24

## Entry points confirmed

| Hook | File:line | Notes |
|---|---|---|
| `compute_market_state(raw_data, config)` | `src/components/market_state.py:1088` | Main MSO builder. Returns `MarketStateObject`. Honors `config['market_state']['detector_version']` via `resolve_detector_mode` (F2.3). Forcing `'v1'` keeps behaviour on pre-F2.3 path — no v2 logging, no dual-compute. |
| `build_raw_data(all_candles, target_date, candle_time, session_levels, symbol=...)` | `scripts/historical_data_loader.py:410` | Produces the exact `raw_data` dict `compute_market_state` expects. Slices `all_candles` dict to lookback ending at `candle_time`. Canonical symbol threaded through to keep session-ATR + shadow logger paths consistent with production (post–2026-04-24 Wave 2.5 empty-symbol fix). |
| `compute_session_levels(m15_all, target_date)` | same file | Asian H/L + PDH/PDL from full M15 history (not sliced). |
| `parse_tradingview_csv(path)` | same file | CSV → list[{time, open, high, low, close, volume}]. |

### MSO shape (from `src/models/market_state_models.py`)

`MarketStateObject` exposes:
- `.timeframes[tf].structure.direction ∈ {bullish, bearish, transitional, insufficient_data}`
- `.timeframes[tf].order_blocks: list[OrderBlock]` — each has `type, high, low, formation_time, mitigated, touch_count, causing_event_type`
- `.timeframes[tf].breaker_blocks: list[BreakerBlock]`
- `.timeframes[tf].fair_value_gaps: list[FairValueGap]`
- `.timeframes[tf].premium_discount: PremiumDiscount` (equilibrium_50 etc.)
- `.timeframes[tf].atr_14` + `atr_session` + `session_vol_ratio` (M15 XAUUSD only)
- `.timeframes[tf].clv_current, clv_avg_5, bvc_buy_fraction, net_flow_5`
- `.session_levels` (asian/pdh/pdl/session/london H+L)
- `.liquidity_pools, .detected_sweeps`

### Detector version

`config['market_state']['detector_version'] = 'v1'` forces v1 single-compute. Verified by smoke test at a real 2026-01-13T15:00:00Z candle:
- D1 `insufficient_data` (expected — 13 days of D1 = below swing detection threshold for D1)
- H4 `transitional`, H1 `bullish`, M15 `bullish`
- H1 OB count = 10, M15 ATR(14) = 7.125
- No exceptions, no v2 shadow row emitted.

This is the SAME `compute_market_state` path that runs in production for Component 3A's prompt — AI sees exactly these fields via `build_prompt` → `primary_analyzer_prompt.build_static_context + build_user_message`.

## Data provenance

| File | Bars | First → Last |
|---|---|---|
| `data/historical_2026/XAUUSD_M15.csv` | 6,880 | 2026-01-02T01:00Z → 2026-04-17T23:45Z |
| `data/historical_2026/XAUUSD_H1.csv` | 1,721 | 2026-01-02T01:00Z → 2026-04-17T23:00Z |
| `data/historical_2026/XAUUSD_H4.csv` | 450 | — |
| `data/historical_2026/XAUUSD_D1.csv` | 75 | — |

**Note — dataset ends 2026-04-17, not 2026-04-13 as spec stated.** I will walk to 2026-04-13 per the LOCKED split (test ends Mar 1-Apr 13). The extra 4 days (Apr 14-17) remain in the CSV but are outside the defined test window and will NOT be evaluated.

### Label horizon data gap

Primary label horizon is 12 H1 candles (~12 hours). For M15 close candles near the dataset end (Apr 13 21:00-23:45), we don't have 12 subsequent H1 candles in-file. These candles will be labeled `unlabeled` and excluded. Rough estimate: last ~12-16 M15 rows of Apr 13 lose the Primary / Premium labels but may still have Sub-lens-1 labels (4 H1).

## Production feature schema (for mapping to hits/misses)

`shadow_logs/candidate_features_log.jsonl` (169 lines, fleet-wide — XAUUSD is a subset). Key fields on each row (parsed from tail):
- `timestamp_utc, symbol, evaluation_id, kill_zone, session_tag, day_of_week, hour_utc`
- `decision ∈ {CANDIDATE, NO_TRADE, …}`, `framework, setup_grade, c_gate_result`
- `daily_bias_direction, daily_bias_confidence, h4_aligned, m15_choch_detected`
- `trade_parameters` (populated only when CANDIDATE)
- `mso_{d1,h1,m15}_structure_direction`, `mso_h1_unmitigated_ob_count, mso_h1_ob_touch_counts`
- `mso_h1_nearest_ob_distance_atr, mso_h1_fvg_count, mso_m15_fvg_count`
- `mso_pool_count_by_type, mso_nearest_same_side_pool_distance_atr, mso_nearest_opposite_side_pool_distance_atr`
- `mso_{h1,m15,d1}_atr_14, mso_pd_equilibrium_50, mso_pd_current_zone`
- `mso_m15_clv_current, clv_avg_5, bvc_buy_fraction, net_flow_5, session_vol_ratio`
- `mso_detected_sweeps_count, mso_detected_sweeps_types[]`

Hit-mapping plan: every shadow-log row has `timestamp_utc` → candle timestamp; join on that against our walked feature rows by rounding to M15 close. XAUUSD subset filter: `symbol == "XAUUSD"` (symbol backfill shipped 2026-04-24 Wave 2.5).

## Trade record schema

`knowledge_base/trade_records/XAUUSD/2026-04-15_ny_1330.json` — verified. Structure:
- `metadata.candle_time` + `metadata.system_version`
- `decision_pipeline.final_outcome ∈ {FILLED, REJECTED_L2, REJECTED_L1, …, TIMEOUT, CANCELLED, …}`
- `decision_pipeline.ai_decision, ai_direction, ai_framework, ai_grade, ai_confidence`
- `decision_pipeline.level2_verification.{passed, blocked_by, checks[]}`
- `mso` — the full MSO snapshot at decision
- (when filled) additional blocks for `outcome.{exit_reason, pnl_r, mfe_r, mae_r, …}` — will confirm on-the-fly

Only 12 XAUUSD trade records to date (Apr 15-20). Limited ground truth for hit/miss mapping on the TEST window (Mar 1 – Apr 13) — only 12 candles' worth. This is a real limitation. The candidate_features log is broader.

## Environment

- Python: sklearn 1.8.0 ✅ (GradientBoostingClassifier), pandas 3.0.1, numpy 2.4.4, pyarrow 23.0.1
- lightgbm: NOT available → fall back to `sklearn.ensemble.GradientBoostingClassifier` (spec explicitly permits this fallback). Permutation importance available via `sklearn.inspection.permutation_importance`. SHAP may not be installed — will verify; if absent, use tree-path leaf-clustering as cluster proxy.

## Plan for candle walk

No Task/Agent tool is available in this environment (verified via `ToolSearch select:Task` → "No matching deferred tools found"). Per memory `feedback_parallelize_aggressively_tier4.md` I will still parallelize: dispatch the per-slice feature extraction as 8 background bash processes (`run_in_background: true`), each invoking a self-contained Python module that loads CSVs, walks its slice, writes `slice_<N>/features.parquet`, and prints a summary JSON to stdout. This is pure-CPU ($0 API — pins the mission's hard budget constraint).

Slice plan (8 slices, ~13 calendar days each, split by M15-close timestamp):

| Slice | Range | Split |
|---|---|---|
| 1 | 2026-01-02 → 2026-01-14 | train |
| 2 | 2026-01-15 → 2026-01-28 | train |
| 3 | 2026-01-29 → 2026-02-10 | train |
| 4 | 2026-02-11 → 2026-02-23 | train |
| 5 | 2026-02-24 → 2026-02-28 + 2026-03-01 → 2026-03-09 | **boundary — walked together then split on date** |
| 6 | 2026-03-10 → 2026-03-22 | test |
| 7 | 2026-03-23 → 2026-04-04 | test |
| 8 | 2026-04-05 → 2026-04-13 | test |

Train/test cut is enforced POST-walk by filtering on `candle_time < 2026-03-01T00:00Z` (train) vs `>=` (test). Slice 5 straddles the boundary but doesn't violate IRON rule because walking ≠ training — it's pure label extraction. Classifier fit uses only candles in the correct split.

## Feature list (for extraction)

Per candle, per direction (LONG, SHORT), we'll emit a row with:

**Structure**
- `d1_dir, h4_dir, h1_dir, m15_dir` (one-hot or categorical)
- `d1_h4_aligned, h4_h1_aligned, h1_m15_aligned` (booleans)
- `mtf_alignment_score` (count of aligned adjacent TF pairs)

**Order blocks**
- `h1_unmitigated_ob_count, h1_ob_min_touch, h1_ob_max_touch`
- `h1_nearest_opposing_ob_distance_pips, _atr` (opposing = counter-direction; this is the OB GTOS would retest)
- `h4_nmitigated_ob_count`
- `m15_unmitigated_ob_count`

**FVGs**
- `h1_fvg_count, m15_fvg_count, h1_fvg_within_1atr` (nearest FVG distance under 1 ATR)

**Volatility / sessions**
- `m15_atr_14, h1_atr_14, d1_atr_14, session_vol_ratio` (when defined)
- `kill_zone ∈ {london, ny, tokyo, deadzone}`, `hour_utc`, `day_of_week`
- `atr_rolling_20d` (normalize to compare to current)
- `range_pct_last_20` — (highest high - lowest low) / mean close over last 20 M15

**PD zone**
- `pd_current_zone ∈ {premium, equilibrium, discount}`, `pd_midpoint_distance_atr`

**Order flow proxies (L1 Q-1.7)**
- `clv_current, clv_avg_5, bvc_buy_fraction, net_flow_5`

**Liquidity**
- `sweeps_count_last_20`, `nearest_same_side_pool_distance_atr`, `nearest_opposite_side_pool_distance_atr`
- `equal_highs_count, equal_lows_count`

**Swings**
- `hh_count_h1, hl_count_h1, lh_count_h1, ll_count_h1` per TF (×3 TFs)

**Direction of trial**
- `direction ∈ {LONG, SHORT}` (explicit feature so classifier can distinguish)

**Target labels**
- `label_primary, label_quick, label_premium, label_anti` — computed via forward-simulation over next 24 H1 candles

**Bookkeeping**
- `candle_time, split ∈ {train, test}, sl_source ∈ {ob, atr_fallback}, sl_distance, r_denom`

## Go/no-go checks

- [x] `compute_market_state` runs end-to-end on historical candle with detector_version=v1
- [x] sklearn + pandas + numpy + pyarrow available
- [x] Trade record schema readable, candidate_features log readable
- [x] Branch `research/phase1-track-a-xauusd-reverse` created in worktree
- [ ] 8 slice workers dispatched → see `slice_<N>/` outputs
- [ ] Synthesis: classifiers fit on TRAIN, evaluated on TEST, clusters exported, SYNTHESIS.md written

GO.
