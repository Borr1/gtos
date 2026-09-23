# CNR Residual-R Field And Bin Spec - 2026-05-08

Promotion verdict: `NO_PROMOTION_VERDICT`
Validation safe: `false`
Outcome review opened: `false`
Live effect: `false`

Bins are mechanical/source-policy controls, not selected from OTI7 outcome performance.

```json
{
  "account_history_accessed": false,
  "api_calls": 0,
  "artifact_family": "CNR_RESIDUAL_R_FIELD_AND_BIN_SPEC",
  "blocked_packet_outcome_source_read": false,
  "broker_actual_r_accessed": false,
  "control_boundary": "These bins are preregistration controls only; they do not rescue or rescore OTI7.",
  "databento_calls": 0,
  "field_formulas": {
    "executable_quote_price": "LONG uses ask; SHORT uses bid",
    "executable_stop_distance_price": "LONG: executable_quote - original_stop_loss; SHORT: original_stop_loss - executable_quote",
    "original_base_r_price": "abs(original_entry_price - original_stop_loss)",
    "quote_displacement_from_original_entry_r": "signed favorable distance from original entry to executable quote / original_base_r_price",
    "quote_displacement_from_original_stop_r": "signed favorable distance from original stop to executable quote / original_base_r_price",
    "quote_displacement_from_original_tp1_r": "signed favorable distance from original TP1 to executable quote / original_base_r_price; positive means quote is already beyond TP1",
    "residual_target_price_from_executable_quote": "LONG: original_take_profit_1 - executable_quote; SHORT: executable_quote - original_take_profit_1",
    "residual_target_r_from_executable_quote": "residual_target_price_from_executable_quote / executable_stop_distance_price; null when stop distance <= 0",
    "stop_r_from_executable_quote": "executable_stop_distance_price / original_base_r_price"
  },
  "generated_at_utc": "2026-05-08T03:35:16Z",
  "live_effect": false,
  "live_trade_results_accessed": false,
  "matrix_bin_counts": {
    "residual_target_r": {
      "GT_0_25_TO_0_5_SMALL_RESIDUAL": 16,
      "GT_0_5_TO_1_0_SUB_ONE_R": 24,
      "GT_0_TO_0_25_TINY_RESIDUAL": 20,
      "GT_1_0_TO_LT_1_5_BELOW_GTOS_MIN_RR": 24,
      "MISSING_OR_STOP_INVALID": 18
    },
    "stop_r": {
      "GT_1_0_TO_1_5_EXPANDED_STOP_DISTANCE": 34,
      "GT_1_5_LARGE_STOP_DISTANCE_DECAY": 50,
      "LTE_0_INVALID_STOP_GEOMETRY": 18
    }
  },
  "mt5_order_calls": 0,
  "non_optimized_bin_sources": [
    "zero or sign eligibility",
    "mechanical quarter/half/one-R geometry fractions",
    "GTOS min_rr=1.5 as a policy boundary",
    "source presence / quote freshness status"
  ],
  "order_calls": 0,
  "outcome_review_opened": false,
  "paid_data_calls": 0,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "quote_age_policy": {
    "current_rows": "record quote_age_ms as input-only; do not retroactively invalidate accepted G12 rows",
    "future_gate": "future CNR result lanes must bind max_quote_age_ms before outcome opening; proposed default 5000ms is an operational freshness control, not an OTI7-fit threshold"
  },
  "residual_target_r_bins": [
    "MISSING_OR_STOP_INVALID",
    "LTE_0_TARGET_ALREADY_PASSED_OR_ZERO",
    "GT_0_TO_0_25_TINY_RESIDUAL",
    "GT_0_25_TO_0_5_SMALL_RESIDUAL",
    "GT_0_5_TO_1_0_SUB_ONE_R",
    "GT_1_0_TO_LT_1_5_BELOW_GTOS_MIN_RR",
    "GTE_1_5_MEETS_GTOS_MIN_RR_GEOMETRY_ONLY"
  ],
  "stop_r_bins": [
    "LTE_0_INVALID_STOP_GEOMETRY",
    "GT_0_TO_0_5_COMPRESSED_STOP_DISTANCE",
    "GT_0_5_TO_1_0_WITHIN_ORIGINAL_R",
    "GT_1_0_TO_1_5_EXPANDED_STOP_DISTANCE",
    "GT_1_5_LARGE_STOP_DISTANCE_DECAY"
  ],
  "validation_safe": false
}
```
