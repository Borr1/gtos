# CNR No-Leak Duplicate Sample Audit - 2026-05-08

Promotion verdict: `NO_PROMOTION_VERDICT`
Validation safe: `false`
Outcome review opened: `false`
Live effect: `false`

The input row matrix is label-free and denominator-controlled.

```json
{
  "account_history_accessed": false,
  "api_calls": 0,
  "artifact_family": "CNR_NOLEAK_DUPLICATE_SAMPLE_AUDIT",
  "blocked_packet_outcome_source_read": false,
  "broker_actual_r_accessed": false,
  "countable_rows": 54,
  "databento_calls": 0,
  "duplicate_context_rows": 48,
  "duplicate_denominator_key_collision_count": 24,
  "duplicate_denominator_key_collision_examples": {
    "OTG0-PKT-060|G6_OB_GENERIC|GBPJPY|2026-05-04|tokyo|LONG|213.257|CNR_E0_DECISION_CLOSE_MARKET|CNR_T0_ORIGINAL_TP1": 2,
    "OTG0-PKT-060|G6_OB_GENERIC|GBPJPY|2026-05-04|tokyo|LONG|213.257|CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE|CNR_T0_ORIGINAL_TP1": 2,
    "OTG0-PKT-060|G6_OB_GENERIC|XAGUSD|2026-05-05|ny|SHORT|73.597|CNR_E0_DECISION_CLOSE_MARKET|CNR_T0_ORIGINAL_TP1": 3,
    "OTG0-PKT-060|G6_OB_GENERIC|XAGUSD|2026-05-05|ny|SHORT|73.597|CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE|CNR_T0_ORIGINAL_TP1": 3,
    "OTG0-PKT-060|G6_OB_GENERIC|XAGUSD|2026-05-06|london|SHORT|73.597|CNR_E0_DECISION_CLOSE_MARKET|CNR_T0_ORIGINAL_TP1": 3,
    "OTG0-PKT-060|G6_OB_GENERIC|XAGUSD|2026-05-06|london|SHORT|73.597|CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE|CNR_T0_ORIGINAL_TP1": 3,
    "OTG0-PKT-061|G6_CNR|XAGUSD|2026-05-05|ny|SHORT|73.222|CNR_E0_DECISION_CLOSE_MARKET|CNR_T0_ORIGINAL_TP1": 3,
    "OTG0-PKT-061|G6_CNR|XAGUSD|2026-05-05|ny|SHORT|73.222|CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE|CNR_T0_ORIGINAL_TP1": 3,
    "OTG0-PKT-062|G6_OPENING_DRIVE|GBPJPY|2026-05-04|tokyo|NO_BREAKOUT_ASOF|CNR_E0_DECISION_CLOSE_MARKET|CNR_T0_ORIGINAL_TP1": 3,
    "OTG0-PKT-062|G6_OPENING_DRIVE|GBPJPY|2026-05-04|tokyo|NO_BREAKOUT_ASOF|CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE|CNR_T0_ORIGINAL_TP1": 3
  },
  "duplicate_policy": "Rows marked countable_denominator_row=false remain context only. E0 and E1 are separate timing-family rows but not independent opportunity proof when they share the same quote timestamp.",
  "forbidden_input_row_key_hits": [],
  "forbidden_input_row_keys": [
    "account_history",
    "broker_actual_r",
    "label_family",
    "live_trade_result",
    "path_coverage",
    "quarantined_result_status",
    "result_status",
    "stop_first_touch_utc",
    "stop_hit_timestamp",
    "synthetic_path_r",
    "target_first_touch_utc",
    "target_hit_timestamp",
    "terminal_ask",
    "terminal_bid",
    "terminal_event",
    "terminal_quote_side",
    "terminal_timestamp_utc"
  ],
  "forbidden_input_row_scan_status": "PASS_INPUT_MATRIX_HAS_NO_FORBIDDEN_OUTCOME_KEYS",
  "generated_at_utc": "2026-05-08T03:35:19Z",
  "input_row_count": 102,
  "label_family_policy": "input_only_control_fields; no broker_actual_r/account_history/live_result/synthetic_path_r labels in matrix",
  "live_effect": false,
  "live_trade_results_accessed": false,
  "mt5_order_calls": 0,
  "order_calls": 0,
  "outcome_review_opened": false,
  "paid_data_calls": 0,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "sample_floor_status": "BLOCKED_BELOW_30_UNIQUE_GROUPS_PER_TIMING_TARGET_FAMILY",
  "sample_floor_unique_groups_per_family": 30,
  "timing_target_countable_rows": {
    "CNR_E0_DECISION_CLOSE_MARKET|CNR_T0_ORIGINAL_TP1": 27,
    "CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE|CNR_T0_ORIGINAL_TP1": 27
  },
  "timing_target_unique_duplicate_groups": {
    "CNR_E0_DECISION_CLOSE_MARKET|CNR_T0_ORIGINAL_TP1": 27,
    "CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE|CNR_T0_ORIGINAL_TP1": 27
  },
  "unique_countable_duplicate_groups": 27,
  "unique_duplicate_groups": 30,
  "validation_safe": false
}
```
