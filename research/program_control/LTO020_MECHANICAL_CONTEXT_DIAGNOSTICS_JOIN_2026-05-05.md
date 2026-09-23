# LTO-020 Mechanical Context Diagnostics Join - 2026-05-05

**Schema:** `lto020_mechanical_context_diagnostics_join_report_v1`
**Generated:** `2026-06-01T23:38:13.662856+00:00`
**Status:** `OK_MECHANICAL_CONTEXT_DIAGNOSTICS_JOIN_DOCUMENTED`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Counts

- Rows computed: `538`
- Status rows available: `7089`
- Status rows appended this run: `281`
- Complete joined rows: `0`
- Partial documented rows: `538`
- Action-required rows: `0`
- Path joined rows: `488`
- Actual-R claim allowed rows: `0`
- Action required: `0`

## Source Counts

`{'candidate_rows': 538, 'path_rows': 8903, 'broker_audit_rows': 284, 'dumb_baseline_rows': 22, 'proximity_rows': 386, 'liquidity_distance_rows': 65, 'displacement_rows': 157, 'structure_divergence_rows': 4209}`

## Status Breakdown

- Status counts: `{'MECHANICAL_CONTEXT_DIAGNOSTICS_PARTIAL_JOIN_DOCUMENTED': 538}`
- Symbol counts: `{'AUDJPY': 8, 'BTCUSD': 24, 'CHFJPY': 21, 'ETHUSD': 23, 'EURGBP': 27, 'EURJPY': 19, 'GBPJPY': 50, 'GBPUSD': 57, 'JP225': 20, 'NAS100': 76, 'NZDUSD': 3, 'UK100': 1, 'UKOIL_cash': 26, 'US30': 40, 'USDCAD': 25, 'USDJPY': 4, 'USOIL_cash': 24, 'XAGUSD': 60, 'XAUUSD': 30}`
- Framework counts: `{'origin_displacement_continuation': 91, 'origin_liquidity_sweep_reclaim': 108, 'origin_session_open_range_break': 14, 'origin_cross_asset_lead_lag': 48, 'origin_structural_distance_extreme': 59, 'origin_regime_transition_break': 2, 'origin_volatility_compression_expansion': 9, 'ob_retest': 195, 'breaker_re_entry': 12}`
- Final outcome counts: `{'SKIPPED_GTOS_VNEXT_BROADER_ORIGIN_DYNAMIC': 260, 'LIMIT_FILLED_GTOS_VNEXT_BROADER_ORIGIN': 13, 'REJECTED_GATE3_CIRCUIT_BREAKER': 59, 'LIMIT_CANCELLED_GTOS_VNEXT_LTF_SL_TOO_CLOSE': 1, 'REJECTED_L2': 125, 'LIMIT_PLACED': 17, 'REJECTED_GATE0_5_TRADING_ENABLED': 21, 'REJECTED_GATE1_SAFETY': 42}`
- ML label eligibility counts: `{'SYNTHETIC_PATH_LABEL_WITH_MECHANICAL_CONTEXT_NOT_ACCOUNT_HISTORY': 488, 'FEATURE_CONTEXT_ONLY_LABEL_NOT_AVAILABLE': 50}`
- Mechanical context join counts: `{'displacement': {'DISPLACEMENT_ASOF_JOINED': 39, 'DISPLACEMENT_JOIN_MISSING_WITHIN_ASOF_WINDOW': 499}, 'dumb_baseline': {'CONTEXT_JOIN_MISSING_WITHIN_TIME_WINDOW': 537, 'CONTEXT_NEAR_TIME_JOINED': 1}, 'liquidity_distance': {'CONTEXT_JOIN_MISSING_WITHIN_TIME_WINDOW': 508, 'CONTEXT_NEAR_TIME_GEOMETRY_JOINED': 30}, 'proximity': {'CONTEXT_JOIN_MISSING_WITHIN_TIME_WINDOW': 335, 'CONTEXT_NEAR_TIME_JOINED': 203}, 'structure_divergence': {'STRUCTURE_DIVERGENCE_TIMEFRAME_ROWS_JOINED': 231, 'STRUCTURE_DIVERGENCE_JOIN_MISSING_WITHIN_TIME_WINDOW': 307}}`
- Action-required codes: `{}`
- Mismatch codes: `{'DISPLACEMENT_DIRECTION_DIFFERS_FROM_SIDE_CONTEXT': 19}`
- Documented limitations: `{'DUMB_BASELINE_CONTEXT_MISSING_WITHIN_ASOF_WINDOW': 537, 'LIQUIDITY_DISTANCE_CONTEXT_MISSING_WITHIN_ASOF_WINDOW': 508, 'PROXIMITY_CONTEXT_MISSING_WITHIN_ASOF_WINDOW': 335, 'DISPLACEMENT_CONTEXT_MISSING_WITHIN_ASOF_WINDOW': 499, 'STRUCTURE_DIVERGENCE_CONTEXT_MISSING_WITHIN_ASOF_WINDOW': 307}`

## Discovery-Only Correlations

- Proximity by path label: `{'continued_without_entry_touch_to_tp_area': {'inside': 33, 'approaching': 36, 'far': 6, 'unknown': 1}, 'entry_touched_then_reached_tp1': {'inside': 37, 'far': 3, 'approaching': 4}, 'entry_touched_tp_and_sl_m15_ambiguous': {'approaching': 44, 'unknown': 5, 'inside': 10, 'far': 6, 'none': 2}, 'went_through_entry_and_continued_to_sl': {'unknown': 5, 'approaching': 4, 'inside': 3, 'none': 4}}`
- Dumb-baseline realized R by path label: `{'entry_touched_tp_and_sl_m15_ambiguous': {'n': 1, 'mean_r': -1.0, 'sum_r': -1.0}}`

## Boundary

This report joins existing mechanical/context diagnostics to candidate rows. It is ML/research substrate only and does not alter prompts, safety gates, risk, execution, or orders.

## Discovery Boundary

Path labels, broker actual-R, and dumb-baseline outcomes are correlation/comparator labels only. They are not decision-time features and remain NO_PROMOTION_VERDICT.

## ML Goal Contribution

The lane turns dumb-baseline comparators, OB proximity, liquidity-distance geometry, displacement state, structure-detector divergence, path labels, and account-history label status into one K55-ready feature/provenance/sample-eligibility surface.

## Safety Counters

- ai_calls: `0`
- canary_calls: `0`
- order_calls: `0`
- paid_data_calls: `0`
