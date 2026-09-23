# LTO-019 Decision-Layer Diagnostics Join - 2026-05-05

**Schema:** `lto019_decision_layer_diagnostics_join_report_v1`
**Generated:** `2026-06-01T23:37:36.837366+00:00`
**Status:** `ACTION_REQUIRED`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

## Counts

- Rows computed: `538`
- Status rows available: `745`
- Status rows appended this run: `21`
- Complete joined rows: `0`
- Partial documented rows: `207`
- Action-required rows: `331`
- Candidate-features joined rows: `207`
- Direction-emission joined rows: `203`
- SL-beyond-OB joined rows: `179`
- Touch-count joined rows: `53`
- Cross-instrument correlation joined rows: `282`
- D1-bias-lag joined rows: `4`
- Action required: `331`

## Source Counts

`{'candidate_rows': 538, 'candidate_feature_rows': 1180, 'd1_bias_lag_rows': 549, 'direction_emission_rows': 320, 'sl_beyond_ob_rows': 274, 'touch_count_rows': 78, 'cross_instrument_correlation_rows': 696}`

## Status Breakdown

- Status counts: `{'DECISION_DIAGNOSTICS_ACTION_REQUIRED': 331, 'DECISION_DIAGNOSTICS_PARTIAL_JOIN_DOCUMENTED': 207}`
- Symbol counts: `{'AUDJPY': 8, 'BTCUSD': 24, 'CHFJPY': 21, 'ETHUSD': 23, 'EURGBP': 27, 'EURJPY': 19, 'GBPJPY': 50, 'GBPUSD': 57, 'JP225': 20, 'NAS100': 76, 'NZDUSD': 3, 'UK100': 1, 'UKOIL_cash': 26, 'US30': 40, 'USDCAD': 25, 'USDJPY': 4, 'USOIL_cash': 24, 'XAGUSD': 60, 'XAUUSD': 30}`
- Framework counts: `{'origin_displacement_continuation': 91, 'origin_liquidity_sweep_reclaim': 108, 'origin_session_open_range_break': 14, 'origin_cross_asset_lead_lag': 48, 'origin_structural_distance_extreme': 59, 'origin_regime_transition_break': 2, 'origin_volatility_compression_expansion': 9, 'ob_retest': 195, 'breaker_re_entry': 12}`
- Final outcome counts: `{'SKIPPED_GTOS_VNEXT_BROADER_ORIGIN_DYNAMIC': 260, 'LIMIT_FILLED_GTOS_VNEXT_BROADER_ORIGIN': 13, 'REJECTED_GATE3_CIRCUIT_BREAKER': 59, 'LIMIT_CANCELLED_GTOS_VNEXT_LTF_SL_TOO_CLOSE': 1, 'REJECTED_L2': 125, 'LIMIT_PLACED': 17, 'REJECTED_GATE0_5_TRADING_ENABLED': 21, 'REJECTED_GATE1_SAFETY': 42}`
- Diagnostic join counts: `{'candidate_features': {'DIAGNOSTIC_JOIN_MISSING_WITHIN_TIME_WINDOW': 331, 'DIAGNOSTIC_NEAR_TIME_JOINED': 207}, 'cross_instrument_correlation': {'DIAGNOSTIC_NEAR_TIME_JOINED': 282, 'DIAGNOSTIC_JOIN_MISSING_WITHIN_TIME_WINDOW': 256}, 'd1_bias_lag': {'DIAGNOSTIC_JOIN_MISSING_WITHIN_TIME_WINDOW': 534, 'DIAGNOSTIC_NEAR_TIME_JOINED': 4}, 'direction_emission': {'DIAGNOSTIC_JOIN_MISSING_WITHIN_TIME_WINDOW': 335, 'DIAGNOSTIC_NEAR_TIME_JOINED': 203}, 'sl_beyond_ob': {'DIAGNOSTIC_JOIN_MISSING_WITHIN_TIME_WINDOW': 359, 'DIAGNOSTIC_NEAR_TIME_JOINED': 179}, 'touch_count': {'DIAGNOSTIC_JOIN_MISSING_WITHIN_TIME_WINDOW': 485, 'DIAGNOSTIC_NEAR_TIME_JOINED': 53}}`
- Action-required codes: `{'CANDIDATE_FEATURES_MISSING_FOR_CANDIDATE': 331}`
- Mismatch codes: `{}`
- Documented limitations: `{'D1_BIAS_LAG_DIAGNOSTIC_MISSING_WITHIN_TIME_WINDOW': 534, 'DIRECTION_EMISSION_DIAGNOSTIC_MISSING_WITHIN_TIME_WINDOW': 335, 'SL_BEYOND_OB_DIAGNOSTIC_MISSING_WITHIN_TIME_WINDOW': 359, 'CROSS_INSTRUMENT_CORRELATION_DIAGNOSTIC_OPTIONAL_MISSING_WITHIN_TIME_WINDOW': 256, 'TOUCH_COUNT_GATE_DIAGNOSTIC_MISSING_FOR_OB_RETEST': 139}`

## Cadence Mix

- Daily status mix: `{'2026-05-03': {'DECISION_DIAGNOSTICS_PARTIAL_JOIN_DOCUMENTED': 3}, '2026-05-04': {'DECISION_DIAGNOSTICS_PARTIAL_JOIN_DOCUMENTED': 48}, '2026-05-05': {'DECISION_DIAGNOSTICS_PARTIAL_JOIN_DOCUMENTED': 25}, '2026-05-06': {'DECISION_DIAGNOSTICS_PARTIAL_JOIN_DOCUMENTED': 10}, '2026-05-07': {'DECISION_DIAGNOSTICS_PARTIAL_JOIN_DOCUMENTED': 40}, '2026-05-08': {'DECISION_DIAGNOSTICS_PARTIAL_JOIN_DOCUMENTED': 64}, '2026-05-10': {'DECISION_DIAGNOSTICS_PARTIAL_JOIN_DOCUMENTED': 1}, '2026-05-11': {'DECISION_DIAGNOSTICS_PARTIAL_JOIN_DOCUMENTED': 7}, '2026-05-12': {'DECISION_DIAGNOSTICS_PARTIAL_JOIN_DOCUMENTED': 9}, '2026-05-31': {'DECISION_DIAGNOSTICS_ACTION_REQUIRED': 9}, '2026-06-01': {'DECISION_DIAGNOSTICS_ACTION_REQUIRED': 322}}`
- Weekly status mix: `{'2026-W18': {'DECISION_DIAGNOSTICS_PARTIAL_JOIN_DOCUMENTED': 3}, '2026-W19': {'DECISION_DIAGNOSTICS_PARTIAL_JOIN_DOCUMENTED': 188}, '2026-W20': {'DECISION_DIAGNOSTICS_PARTIAL_JOIN_DOCUMENTED': 16}, '2026-W22': {'DECISION_DIAGNOSTICS_ACTION_REQUIRED': 9}, '2026-W23': {'DECISION_DIAGNOSTICS_ACTION_REQUIRED': 322}}`

## Boundary

This report joins existing decision-time diagnostics to live candidate rows. It is ML/research substrate only and does not alter prompts, safety gates, risk, execution, or orders.

## ML Goal Contribution

The lane converts AI direction, candidate features, L2 gate state, touch-count state, D1/H4/H1 lag context, and direction-emission audit rows into one K55-ready feature/provenance surface with mismatch codes for target refresh and inference QA.

## Safety Counters

- ai_calls: `0`
- canary_calls: `0`
- order_calls: `0`
- paid_data_calls: `0`

## Action Required Examples

```json
[
  {
    "action_required_codes": [
      "CANDIDATE_FEATURES_MISSING_FOR_CANDIDATE"
    ],
    "candidate_final_outcome_at_log": "SKIPPED_GTOS_VNEXT_BROADER_ORIGIN_DYNAMIC",
    "candidate_id": "AUDJPY_2026-06-01T00:15:00Z",
    "decision_time_utc": "2026-06-01T00:15:00Z",
    "framework": "origin_displacement_continuation",
    "mismatch_codes": [],
    "row_key": "23baadf8027f379b8a55bae16de91bb2",
    "symbol": "AUDJPY"
  },
  {
    "action_required_codes": [
      "CANDIDATE_FEATURES_MISSING_FOR_CANDIDATE"
    ],
    "candidate_final_outcome_at_log": "SKIPPED_GTOS_VNEXT_BROADER_ORIGIN_DYNAMIC",
    "candidate_id": "AUDJPY_2026-06-01T00:30:00Z",
    "decision_time_utc": "2026-06-01T00:30:00Z",
    "framework": "origin_liquidity_sweep_reclaim",
    "mismatch_codes": [],
    "row_key": "bc7aba2c3b0ef57f4b495dc681765bba",
    "symbol": "AUDJPY"
  },
  {
    "action_required_codes": [
      "CANDIDATE_FEATURES_MISSING_FOR_CANDIDATE"
    ],
    "candidate_final_outcome_at_log": "SKIPPED_GTOS_VNEXT_BROADER_ORIGIN_DYNAMIC",
    "candidate_id": "AUDJPY_2026-06-01T01:00:00Z",
    "decision_time_utc": "2026-06-01T01:00:00Z",
    "framework": "origin_session_open_range_break",
    "mismatch_codes": [],
    "row_key": "3e0630342b9bec0d0c50c6bd22500ba1",
    "symbol": "AUDJPY"
  },
  {
    "action_required_codes": [
      "CANDIDATE_FEATURES_MISSING_FOR_CANDIDATE"
    ],
    "candidate_final_outcome_at_log": "SKIPPED_GTOS_VNEXT_BROADER_ORIGIN_DYNAMIC",
    "candidate_id": "AUDJPY_2026-06-01T01:15:00Z",
    "decision_time_utc": "2026-06-01T01:15:00Z",
    "framework": "origin_liquidity_sweep_reclaim",
    "mismatch_codes": [],
    "row_key": "18f4438736de5db4ab8c8f42df913bed",
    "symbol": "AUDJPY"
  },
  {
    "action_required_codes": [
      "CANDIDATE_FEATURES_MISSING_FOR_CANDIDATE"
    ],
    "candidate_final_outcome_at_log": "SKIPPED_GTOS_VNEXT_BROADER_ORIGIN_DYNAMIC",
    "candidate_id": "AUDJPY_2026-06-01T01:45:00Z",
    "decision_time_utc": "2026-06-01T01:45:00Z",
    "framework": "origin_liquidity_sweep_reclaim",
    "mismatch_codes": [],
    "row_key": "5cd0e6df6ec535a80c34012f2fdca457",
    "symbol": "AUDJPY"
  },
  {
    "action_required_codes": [
      "CANDIDATE_FEATURES_MISSING_FOR_CANDIDATE"
    ],
    "candidate_final_outcome_at_log": "SKIPPED_GTOS_VNEXT_BROADER_ORIGIN_DYNAMIC",
    "candidate_id": "AUDJPY_2026-06-01T02:00:00Z",
    "decision_time_utc": "2026-06-01T02:00:00Z",
    "framework": "origin_liquidity_sweep_reclaim",
    "mismatch_codes": [],
    "row_key": "7ddc11a84d90eef468dc243934acb72e",
    "symbol": "AUDJPY"
  },
  {
    "action_required_codes": [
      "CANDIDATE_FEATURES_MISSING_FOR_CANDIDATE"
    ],
    "candidate_final_outcome_at_log": "SKIPPED_GTOS_VNEXT_BROADER_ORIGIN_DYNAMIC",
    "candidate_id": "AUDJPY_2026-06-01T02:15:00Z",
    "decision_time_utc": "2026-06-01T02:15:00Z",
    "framework": "origin_liquidity_sweep_reclaim",
    "mismatch_codes": [],
    "row_key": "5d88baaa747fb43e1b51e9a55fbb61b5",
    "symbol": "AUDJPY"
  },
  {
    "action_required_codes": [
      "CANDIDATE_FEATURES_MISSING_FOR_CANDIDATE"
    ],
    "candidate_final_outcome_at_log": "SKIPPED_GTOS_VNEXT_BROADER_ORIGIN_DYNAMIC",
    "candidate_id": "AUDJPY_2026-06-01T03:45:00Z",
    "decision_time_utc": "2026-06-01T03:45:00Z",
    "framework": "origin_displacement_continuation",
    "mismatch_codes": [],
    "row_key": "68a6e69e2ebb237e95d5caffc5ac3b52",
    "symbol": "AUDJPY"
  },
  {
    "action_required_codes": [
      "CANDIDATE_FEATURES_MISSING_FOR_CANDIDATE"
    ],
    "candidate_final_outcome_at_log": "SKIPPED_GTOS_VNEXT_BROADER_ORIGIN_DYNAMIC",
    "candidate_id": "BTCUSD_2026-05-31T23:15:00Z",
    "decision_time_utc": "2026-05-31T23:15:00Z",
    "framework": "origin_liquidity_sweep_reclaim",
    "mismatch_codes": [],
    "row_key": "b23a71212872d6ec2d77bef1643f950a",
    "symbol": "BTCUSD"
  },
  {
    "action_required_codes": [
      "CANDIDATE_FEATURES_MISSING_FOR_CANDIDATE"
    ],
    "candidate_final_outcome_at_log": "SKIPPED_GTOS_VNEXT_BROADER_ORIGIN_DYNAMIC",
    "candidate_id": "BTCUSD_2026-05-31T23:45:00Z",
    "decision_time_utc": "2026-05-31T23:45:00Z",
    "framework": "origin_displacement_continuation",
    "mismatch_codes": [],
    "row_key": "c5061a9ed8aeef61fa809437532bf001",
    "symbol": "BTCUSD"
  },
  {
    "action_required_codes": [
      "CANDIDATE_FEATURES_MISSING_FOR_CANDIDATE"
    ],
    "candidate_final_outcome_at_log": "SKIPPED_GTOS_VNEXT_BROADER_ORIGIN_DYNAMIC",
    "candidate_id": "BTCUSD_2026-06-01T01:15:00Z",
    "decision_time_utc": "2026-06-01T01:15:00Z",
    "framework": "origin_displacement_continuation",
    "mismatch_codes": [],
    "row_key": "c4a7239c8ae3a903da59daf25b672969",
    "symbol": "BTCUSD"
  },
  {
    "action_required_codes": [
      "CANDIDATE_FEATURES_MISSING_FOR_CANDIDATE"
    ],
    "candidate_final_outcome_at_log": "SKIPPED_GTOS_VNEXT_BROADER_ORIGIN_DYNAMIC",
    "candidate_id": "BTCUSD_2026-06-01T01:30:00Z",
    "decision_time_utc": "2026-06-01T01:30:00Z",
    "framework": "origin_cross_asset_lead_lag",
    "mismatch_codes": [],
    "row_key": "5fcc73b6b911abbee45fec542a6a04bb",
    "symbol": "BTCUSD"
  },
  {
    "action_required_codes": [
      "CANDIDATE_FEATURES_MISSING_FOR_CANDIDATE"
    ],
    "candidate_final_outcome_at_log": "SKIPPED_GTOS_VNEXT_BROADER_ORIGIN_DYNAMIC",
    "candidate_id": "BTCUSD_2026-06-01T02:15:00Z",
    "decision_time_utc": "2026-06-01T02:15:00Z",
    "framework": "origin_displacement_continuation",
    "mismatch_codes": [],
    "row_key": "4fc18d2faa9d10c7ff0263b8e621f41d",
    "symbol": "BTCUSD"
  },
  {
    "action_required_codes": [
      "CANDIDATE_FEATURES_MISSING_FOR_CANDIDATE"
    ],
    "candidate_final_outcome_at_log": "SKIPPED_GTOS_VNEXT_BROADER_ORIGIN_DYNAMIC",
    "candidate_id": "BTCUSD_2026-06-01T02:30:00Z",
    "decision_time_utc": "2026-06-01T02:30:00Z",
    "framework": "origin_cross_asset_lead_lag",
    "mismatch_codes": [],
    "row_key": "7fe2b1d05540029d6c4861136cb2ed16",
    "symbol": "BTCUSD"
  },
  {
    "action_required_codes": [
      "CANDIDATE_FEATURES_MISSING_FOR_CANDIDATE"
    ],
    "candidate_final_outcome_at_log": "SKIPPED_GTOS_VNEXT_BROADER_ORIGIN_DYNAMIC",
    "candidate_id": "BTCUSD_2026-06-01T02:45:00Z",
    "decision_time_utc": "2026-06-01T02:45:00Z",
    "framework": "origin_displacement_continuation",
    "mismatch_codes": [],
    "row_key": "29447b76020fe72ce109009e110388b0",
    "symbol": "BTCUSD"
  },
  {
    "action_required_codes": [
      "CANDIDATE_FEATURES_MISSING_FOR_CANDIDATE"
    ],
    "candidate_final_outcome_at_log": "SKIPPED_GTOS_VNEXT_BROADER_ORIGIN_DYNAMIC",
    "candidate_id": "BTCUSD_2026-06-01T06:45:00Z",
    "decision_time_utc": "2026-06-01T06:45:00Z",
    "framework": "origin_structural_distance_extreme",
    "mismatch_codes": [],
    "row_key": "d4c2148109c23308f47ff56c2872e2ec",
    "symbol": "BTCUSD"
  },
  {
    "action_required_codes": [
      "CANDIDATE_FEATURES_MISSING_FOR_CANDIDATE"
    ],
    "candidate_final_outcome_at_log": "SKIPPED_GTOS_VNEXT_BROADER_ORIGIN_DYNAMIC",
    "candidate_id": "BTCUSD_2026-06-01T07:00:00Z",
    "decision_time_utc": "2026-06-01T07:00:00Z",
    "framework": "origin_liquidity_sweep_reclaim",
    "mismatch_codes": [],
    "row_key": "d778c81d6eadaaf5feb258d73d5fe54e",
    "symbol": "BTCUSD"
  },
  {
    "action_required_codes": [
      "CANDIDATE_FEATURES_MISSING_FOR_CANDIDATE"
    ],
    "candidate_final_outcome_at_log": "SKIPPED_GTOS_VNEXT_BROADER_ORIGIN_DYNAMIC",
    "candidate_id": "BTCUSD_2026-06-01T07:30:00Z",
    "decision_time_utc": "2026-06-01T07:30:00Z",
    "framework": "origin_structural_distance_extreme",
    "mismatch_codes": [],
    "row_key": "9a28ecd683dad929a3687be8b5724814",
    "symbol": "BTCUSD"
  },
  {
    "action_required_codes": [
      "CANDIDATE_FEATURES_MISSING_FOR_CANDIDATE"
    ],
    "candidate_final_outcome_at_log": "SKIPPED_GTOS_VNEXT_BROADER_ORIGIN_DYNAMIC",
    "candidate_id": "BTCUSD_2026-06-01T07:45:00Z",
    "decision_time_utc": "2026-06-01T07:45:00Z",
    "framework": "origin_liquidity_sweep_reclaim",
    "mismatch_codes": [],
    "row_key": "e24551e62bc16f583b93997b9458c32b",
    "symbol": "BTCUSD"
  },
  {
    "action_required_codes": [
      "CANDIDATE_FEATURES_MISSING_FOR_CANDIDATE"
    ],
    "candidate_final_outcome_at_log": "SKIPPED_GTOS_VNEXT_BROADER_ORIGIN_DYNAMIC",
    "candidate_id": "BTCUSD_2026-06-01T08:30:00Z",
    "decision_time_utc": "2026-06-01T08:30:00Z",
    "framework": "origin_liquidity_sweep_reclaim",
    "mismatch_codes": [],
    "row_key": "401421caf1fb29173efc49edfb97ada4",
    "symbol": "BTCUSD"
  },
  {
    "action_required_codes": [
      "CANDIDATE_FEATURES_MISSING_FOR_CANDIDATE"
    ],
    "candidate_final_outcome_at_log": "SKIPPED_GTOS_VNEXT_BROADER_ORIGIN_DYNAMIC",
    "candidate_id": "BTCUSD_2026-06-01T08:45:00Z",
    "decision_time_utc": "2026-06-01T08:45:00Z",
    "framework": "origin_liquidity_sweep_reclaim",
    "mismatch_codes": [],
    "row_key": "e400e9d5f4aa49777fdecdd8033e58cb",
    "symbol": "BTCUSD"
  },
  {
    "action_required_codes": [
      "CANDIDATE_FEATURES_MISSING_FOR_CANDIDATE"
    ],
    "candidate_final_outcome_at_log": "SKIPPED_GTOS_VNEXT_BROADER_ORIGIN_DYNAMIC",
    "candidate_id": "BTCUSD_2026-06-01T10:45:00Z",
    "decision_time_utc": "2026-06-01T10:45:00Z",
    "framework": "origin_liquidity_sweep_reclaim",
    "mismatch_codes": [],
    "row_key": "095851c9dc3b813bcd96b6e72e84cede",
    "symbol": "BTCUSD"
  },
  {
    "action_required_codes": [
      "CANDIDATE_FEATURES_MISSING_FOR_CANDIDATE"
    ],
    "candidate_final_outcome_at_log": "LIMIT_FILLED_GTOS_VNEXT_BROADER_ORIGIN",
    "candidate_id": "BTCUSD_2026-06-01T12:00:00Z",
    "decision_time_utc": "2026-06-01T12:00:00Z",
    "framework": "origin_displacement_continuation",
    "mismatch_codes": [],
    "row_key": "0bdbb34b8dd4e48b88276c5a7a89f056",
    "symbol": "BTCUSD"
  },
  {
    "action_required_codes": [
      "CANDIDATE_FEATURES_MISSING_FOR_CANDIDATE"
    ],
    "candidate_final_outcome_at_log": "SKIPPED_GTOS_VNEXT_BROADER_ORIGIN_DYNAMIC",
    "candidate_id": "BTCUSD_2026-06-01T12:45:00Z",
    "decision_time_utc": "2026-06-01T12:45:00Z",
    "framework": "origin_cross_asset_lead_lag",
    "mismatch_codes": [],
    "row_key": "8f2beba54e8c494b15c1bc41031f9374",
    "symbol": "BTCUSD"
  },
  {
    "action_required_codes": [
      "CANDIDATE_FEATURES_MISSING_FOR_CANDIDATE"
    ],
    "candidate_final_outcome_at_log": "REJECTED_GATE3_CIRCUIT_BREAKER",
    "candidate_id": "BTCUSD_2026-06-01T13:15:00Z",
    "decision_time_utc": "2026-06-01T13:15:00Z",
    "framework": "origin_displacement_continuation",
    "mismatch_codes": [],
    "row_key": "feb02315ae8d49999758897eaa2f2f95",
    "symbol": "BTCUSD"
  }
]
```
