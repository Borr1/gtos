# 55 Field Source Binding Matrix Reaudit

Route: `G12_NOFILL_HISTORICAL_SEALED_VALIDATION_PARTITION_SOURCE_BINDING_AUDIT`
Target route: `NOFILL_HISTORICAL_SEALED_VALIDATION_PARTITION_AND_SOURCE_BINDING`
Promotion posture: `NO_PROMOTION_VERDICT`
Safe flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

## Summary

```json
{
  "artifact_family": "source_binding_matrix_reaudit",
  "audit_passed": true,
  "binding_class_counts_recomputed": {
    "FORBIDDEN_REDACTED_STATUS_ONLY": 7,
    "FUTURE_LOGGER_BOUND_REQUIRED_FOR_FULL_COVERAGE": 20,
    "SCHEMA_ONLY_CONTROL": 11,
    "SOURCE_BOUND_HISTORICAL_OR_FAIL_CLOSED": 17
  },
  "changes_live_trading_behavior": false,
  "checks": {
    "all_55_fields_closed": true,
    "all_rows_have_exact_requirement_source_asof_failclosed_and_redaction": true,
    "binding_class_counts_match_expected": true,
    "design_status_counts_match_expected": true,
    "field_count_is_55": true,
    "forbidden_rows_remain_status_only": true,
    "future_logger_field_count_is_20": true,
    "runtime_field_count_is_55": true,
    "target_matrix_field_names_match_runtime_contract": true,
    "target_matrix_has_no_duplicate_field_names": true
  },
  "credentials_touched": false,
  "design_terminal_status_counts_recomputed": {
    "EXISTING_SOURCE_SAFE_CAPTURE_READY": 17,
    "FORBIDDEN_OR_REDACTED_SOURCE_ONLY": 7,
    "FUTURE_LOGGER_FIELD_REQUIRED": 20,
    "SCHEMA_ONLY_CONTROL_FIELD": 11
  },
  "duplicate_field_names": [],
  "expected_binding_class_counts": {
    "FORBIDDEN_REDACTED_STATUS_ONLY": 7,
    "FUTURE_LOGGER_BOUND_REQUIRED_FOR_FULL_COVERAGE": 20,
    "SCHEMA_ONLY_CONTROL": 11,
    "SOURCE_BOUND_HISTORICAL_OR_FAIL_CLOSED": 17
  },
  "expected_design_terminal_status_counts": {
    "EXISTING_SOURCE_SAFE_CAPTURE_READY": 17,
    "FORBIDDEN_OR_REDACTED_SOURCE_ONLY": 7,
    "FUTURE_LOGGER_FIELD_REQUIRED": 20,
    "SCHEMA_ONLY_CONTROL_FIELD": 11
  },
  "extra_matrix_fields_not_runtime": [],
  "field_count_recomputed": 55,
  "forbidden_rows_with_raw_route": [],
  "forbidden_status_only_fields": [
    "cost_testing_gate_status",
    "execution_quality_label_status",
    "execution_quality_value_redaction_status",
    "mt5_order_ticket_redaction_status",
    "raw_ticket_field_present_status",
    "slippage_label_status",
    "slippage_value_redaction_status"
  ],
  "future_logger_fields_recomputed": [
    "capture_clock_skew_ms",
    "capture_clock_skew_status",
    "capture_clock_source_status",
    "capture_latency_ms",
    "capture_write_completed_at_utc",
    "capture_write_started_at_utc",
    "decision_spread_status",
    "decision_spread_unit",
    "decision_spread_value_source_safe",
    "entry_touch_spread_status",
    "entry_touch_spread_value_source_safe",
    "native_pending_order_type_source_safe",
    "native_pending_order_type_status",
    "pending_horizon_end_utc",
    "pending_horizon_start_utc",
    "protective_area_first_touch_utc",
    "protective_area_touch_status",
    "spread_source_hash",
    "terminal_area_first_touch_utc",
    "terminal_area_touch_status"
  ],
  "incomplete_source_binding_rows": [],
  "live_effect": false,
  "missing_runtime_fields_in_matrix": [],
  "opens_live_restart": false,
  "opens_live_trading_behavior": false,
  "opens_mt5_order_account_history_behavior": false,
  "opens_paid_api_or_databento_route": false,
  "opens_promotion": false,
  "opens_registry_edit": false,
  "opens_remote_push": false,
  "opens_result_scoring": false,
  "opens_validation": false,
  "outcome_review_opened": false,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "runtime_field_count_recomputed": 55,
  "runtime_future_logger_field_count_recomputed": 20,
  "target_route_id": "NOFILL_HISTORICAL_SEALED_VALIDATION_PARTITION_AND_SOURCE_BINDING",
  "validation_safe": false
}
```
