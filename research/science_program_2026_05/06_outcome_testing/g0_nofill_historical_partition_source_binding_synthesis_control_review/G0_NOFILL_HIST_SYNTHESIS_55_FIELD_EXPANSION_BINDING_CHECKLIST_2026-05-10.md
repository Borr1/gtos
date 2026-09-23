# 55 Field Expansion Binding Checklist

Route: `G0_NOFILL_HISTORICAL_PARTITION_SOURCE_BINDING_SYNTHESIS_CONTROL_REVIEW`
Terminal decision: `ACCEPT_AS_G0_SOURCE_CONTROL_SYNTHESIS_FOR_NEXT_SEALED_SOURCE_EXPANSION`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Summary

```json
{
  "artifact_family": "fifty_five_field_expansion_binding_checklist",
  "binding_class_counts": {
    "FORBIDDEN_REDACTED_STATUS_ONLY": 7,
    "FUTURE_LOGGER_BOUND_REQUIRED_FOR_FULL_COVERAGE": 20,
    "SCHEMA_ONLY_CONTROL": 11,
    "SOURCE_BOUND_HISTORICAL_OR_FAIL_CLOSED": 17
  },
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "design_terminal_status_counts": {
    "EXISTING_SOURCE_SAFE_CAPTURE_READY": 17,
    "FORBIDDEN_OR_REDACTED_SOURCE_ONLY": 7,
    "FUTURE_LOGGER_FIELD_REQUIRED": 20,
    "SCHEMA_ONLY_CONTROL_FIELD": 11
  },
  "field_count": 55,
  "fields": [
    {
      "binding_class": "SOURCE_BOUND_HISTORICAL_OR_FAIL_CLOSED",
      "design_terminal_status": "EXISTING_SOURCE_SAFE_CAPTURE_READY",
      "exact_requirement_before_validation": "No owner action for existing source-safe binding; future extraction must preserve source hashes.",
      "expansion_binding_action": "preserve existing source-safe binding and source hash; fail closed if missing",
      "fail_closed_missing_status": "SOURCE_FIELD_MISSING_FAIL_CLOSED",
      "field_name": "capture_observed_at_utc",
      "future_logger_field": false
    },
    {
      "binding_class": "FUTURE_LOGGER_BOUND_REQUIRED_FOR_FULL_COVERAGE",
      "design_terminal_status": "FUTURE_LOGGER_FIELD_REQUIRED",
      "exact_requirement_before_validation": "Owner approval for source-capture logger wiring plus G12 source/control acceptance",
      "expansion_binding_action": "derive from tick/source extractor or wait for forward logger; fail closed if unavailable",
      "fail_closed_missing_status": "WRITE_CLOCK_MISSING_FAIL_CLOSED",
      "field_name": "capture_write_started_at_utc",
      "future_logger_field": true
    },
    {
      "binding_class": "FUTURE_LOGGER_BOUND_REQUIRED_FOR_FULL_COVERAGE",
      "design_terminal_status": "FUTURE_LOGGER_FIELD_REQUIRED",
      "exact_requirement_before_validation": "Owner approval for source-capture logger wiring plus G12 source/control acceptance",
      "expansion_binding_action": "derive from tick/source extractor or wait for forward logger; fail closed if unavailable",
      "fail_closed_missing_status": "WRITE_CLOCK_MISSING_FAIL_CLOSED",
      "field_name": "capture_write_completed_at_utc",
      "future_logger_field": true
    },
    {
      "binding_class": "FUTURE_LOGGER_BOUND_REQUIRED_FOR_FULL_COVERAGE",
      "design_terminal_status": "FUTURE_LOGGER_FIELD_REQUIRED",
      "exact_requirement_before_validation": "Owner approval for source-capture logger wiring plus G12 source/control acceptance",
      "expansion_binding_action": "derive from tick/source extractor or wait for forward logger; fail closed if unavailable",
      "fail_closed_missing_status": "WRITE_CLOCK_MISSING_FAIL_CLOSED",
      "field_name": "capture_latency_ms",
      "future_logger_field": true
    },
    {
      "binding_class": "FUTURE_LOGGER_BOUND_REQUIRED_FOR_FULL_COVERAGE",
      "design_terminal_status": "FUTURE_LOGGER_FIELD_REQUIRED",
      "exact_requirement_before_validation": "Owner approval for source-capture logger wiring plus G12 source/control acceptance",
      "expansion_binding_action": "derive from tick/source extractor or wait for forward logger; fail closed if unavailable",
      "fail_closed_missing_status": "CLOCK_SOURCE_MISSING_FAIL_CLOSED",
      "field_name": "capture_clock_source_status",
      "future_logger_field": true
    },
    {
      "binding_class": "FUTURE_LOGGER_BOUND_REQUIRED_FOR_FULL_COVERAGE",
      "design_terminal_status": "FUTURE_LOGGER_FIELD_REQUIRED",
      "exact_requirement_before_validation": "Owner approval for source-capture logger wiring plus G12 source/control acceptance",
      "expansion_binding_action": "derive from tick/source extractor or wait for forward logger; fail closed if unavailable",
      "fail_closed_missing_status": "CLOCK_SOURCE_MISSING_FAIL_CLOSED",
      "field_name": "capture_clock_skew_ms",
      "future_logger_field": true
    },
    {
      "binding_class": "FUTURE_LOGGER_BOUND_REQUIRED_FOR_FULL_COVERAGE",
      "design_terminal_status": "FUTURE_LOGGER_FIELD_REQUIRED",
      "exact_requirement_before_validation": "Owner approval for source-capture logger wiring plus G12 source/control acceptance",
      "expansion_binding_action": "derive from tick/source extractor or wait for forward logger; fail closed if unavailable",
      "fail_closed_missing_status": "CLOCK_SOURCE_MISSING_FAIL_CLOSED",
      "field_name": "capture_clock_skew_status",
      "future_logger_field": true
    },
    {
      "binding_class": "SOURCE_BOUND_HISTORICAL_OR_FAIL_CLOSED",
      "design_terminal_status": "EXISTING_SOURCE_SAFE_CAPTURE_READY",
      "exact_requirement_before_validation": "No owner action for existing source-safe binding; future extraction must preserve source hashes.",
      "expansion_binding_action": "preserve existing source-safe binding and source hash; fail closed if missing",
      "fail_closed_missing_status": "SOURCE_FIELD_MISSING_FAIL_CLOSED",
      "field_name": "capture_timestamp_derivation_rule",
      "future_logger_field": false
    },
    {
      "binding_class": "SOURCE_BOUND_HISTORICAL_OR_FAIL_CLOSED",
      "design_terminal_status": "EXISTING_SOURCE_SAFE_CAPTURE_READY",
      "exact_requirement_before_validation": "No owner action for existing source-safe binding; future extraction must preserve source hashes.",
      "expansion_binding_action": "preserve existing source-safe binding and source hash; fail closed if missing",
      "fail_closed_missing_status": "SOURCE_FIELD_MISSING_FAIL_CLOSED",
      "field_name": "pending_order_mode_source_safe",
      "future_logger_field": false
    },
    {
      "binding_class": "SOURCE_BOUND_HISTORICAL_OR_FAIL_CLOSED",
      "design_terminal_status": "EXISTING_SOURCE_SAFE_CAPTURE_READY",
      "exact_requirement_before_validation": "No owner action for existing source-safe binding; future extraction must preserve source hashes.",
      "expansion_binding_action": "preserve existing source-safe binding and source hash; fail closed if missing",
      "fail_closed_missing_status": "SOURCE_FIELD_MISSING_FAIL_CLOSED",
      "field_name": "pending_order_mode_status",
      "future_logger_field": false
    },
    {
      "binding_class": "SOURCE_BOUND_HISTORICAL_OR_FAIL_CLOSED",
      "design_terminal_status": "EXISTING_SOURCE_SAFE_CAPTURE_READY",
      "exact_requirement_before_validation": "No owner action for existing source-safe binding; future extraction must preserve source hashes.",
      "expansion_binding_action": "preserve existing source-safe binding and source hash; fail closed if missing",
      "fail_closed_missing_status": "SOURCE_FIELD_MISSING_FAIL_CLOSED",
      "field_name": "broker_pending_order_created_status",
      "future_logger_field": false
    },
    {
      "binding_class": "FUTURE_LOGGER_BOUND_REQUIRED_FOR_FULL_COVERAGE",
      "design_terminal_status": "FUTURE_LOGGER_FIELD_REQUIRED",
      "exact_requirement_before_validation": "Owner approval for source-capture logger wiring plus G12 source/control acceptance",
      "expansion_binding_action": "derive from tick/source extractor or wait for forward logger; fail closed if unavailable",
      "fail_closed_missing_status": "SOURCE_FIELD_MISSING_FAIL_CLOSED",
      "field_name": "native_pending_order_type_source_safe",
      "future_logger_field": true
    },
    {
      "binding_class": "FUTURE_LOGGER_BOUND_REQUIRED_FOR_FULL_COVERAGE",
      "design_terminal_status": "FUTURE_LOGGER_FIELD_REQUIRED",
      "exact_requirement_before_validation": "Owner approval for source-capture logger wiring plus G12 source/control acceptance",
      "expansion_binding_action": "derive from tick/source extractor or wait for forward logger; fail closed if unavailable",
      "fail_closed_missing_status": "SOURCE_FIELD_MISSING_FAIL_CLOSED",
      "field_name": "native_pending_order_type_status",
      "future_logger_field": true
    },
    {
      "binding_class": "FORBIDDEN_REDACTED_STATUS_ONLY",
      "design_terminal_status": "FORBIDDEN_OR_REDACTED_SOURCE_ONLY",
      "exact_requirement_before_validation": "Keep raw values redacted/closed; opening them requires a separate approved label/cost evidence lane.",
      "expansion_binding_action": "emit status/redaction only; never include raw broker/account/order/result/cost value",
      "fail_closed_missing_status": "FORBIDDEN_FIELD_PRESENT_FAIL_CLOSED",
      "field_name": "raw_ticket_field_present_status",
      "future_logger_field": false
    },
    {
      "binding_class": "FORBIDDEN_REDACTED_STATUS_ONLY",
      "design_terminal_status": "FORBIDDEN_OR_REDACTED_SOURCE_ONLY",
      "exact_requirement_before_validation": "Keep raw values redacted/closed; opening them requires a separate approved label/cost evidence lane.",
      "expansion_binding_action": "emit status/redaction only; never include raw broker/account/order/result/cost value",
      "fail_closed_missing_status": "FORBIDDEN_FIELD_PRESENT_FAIL_CLOSED",
      "field_name": "mt5_order_ticket_redaction_status",
      "future_logger_field": false
    },
    {
      "binding_class": "FUTURE_LOGGER_BOUND_REQUIRED_FOR_FULL_COVERAGE",
      "design_terminal_status": "FUTURE_LOGGER_FIELD_REQUIRED",
      "exact_requirement_before_validation": "Owner approval for source-capture logger wiring plus G12 source/control acceptance",
      "expansion_binding_action": "derive from tick/source extractor or wait for forward logger; fail closed if unavailable",
      "fail_closed_missing_status": "QUOTE_SNAPSHOT_MISSING_FAIL_CLOSED",
      "field_name": "decision_spread_status",
      "future_logger_field": true
    },
    {
      "binding_class": "FUTURE_LOGGER_BOUND_REQUIRED_FOR_FULL_COVERAGE",
      "design_terminal_status": "FUTURE_LOGGER_FIELD_REQUIRED",
      "exact_requirement_before_validation": "Owner approval for source-capture logger wiring plus G12 source/control acceptance",
      "expansion_binding_action": "derive from tick/source extractor or wait for forward logger; fail closed if unavailable",
      "fail_closed_missing_status": "QUOTE_SNAPSHOT_MISSING_FAIL_CLOSED",
      "field_name": "decision_spread_value_source_safe",
      "future_logger_field": true
    },
    {
      "binding_class": "FUTURE_LOGGER_BOUND_REQUIRED_FOR_FULL_COVERAGE",
      "design_terminal_status": "FUTURE_LOGGER_FIELD_REQUIRED",
      "exact_requirement_before_validation": "Owner approval for source-capture logger wiring plus G12 source/control acceptance",
      "expansion_binding_action": "derive from tick/source extractor or wait for forward logger; fail closed if unavailable",
      "fail_closed_missing_status": "QUOTE_SNAPSHOT_MISSING_FAIL_CLOSED",
      "field_name": "decision_spread_unit",
      "future_logger_field": true
    },
    {
      "binding_class": "FUTURE_LOGGER_BOUND_REQUIRED_FOR_FULL_COVERAGE",
      "design_terminal_status": "FUTURE_LOGGER_FIELD_REQUIRED",
      "exact_requirement_before_validation": "Owner approval for source-capture logger wiring plus G12 source/control acceptance",
      "expansion_binding_action": "derive from tick/source extractor or wait for forward logger; fail closed if unavailable",
      "fail_closed_missing_status": "QUOTE_SNAPSHOT_MISSING_FAIL_CLOSED",
      "field_name": "entry_touch_spread_status",
      "future_logger_field": true
    },
    {
      "binding_class": "FUTURE_LOGGER_BOUND_REQUIRED_FOR_FULL_COVERAGE",
      "design_terminal_status": "FUTURE_LOGGER_FIELD_REQUIRED",
      "exact_requirement_before_validation": "Owner approval for source-capture logger wiring plus G12 source/control acceptance",
      "expansion_binding_action": "derive from tick/source extractor or wait for forward logger; fail closed if unavailable",
      "fail_closed_missing_status": "QUOTE_SNAPSHOT_MISSING_FAIL_CLOSED",
      "field_name": "entry_touch_spread_value_source_safe",
      "future_logger_field": true
    },
    {
      "binding_class": "FUTURE_LOGGER_BOUND_REQUIRED_FOR_FULL_COVERAGE",
      "design_terminal_status": "FUTURE_LOGGER_FIELD_REQUIRED",
      "exact_requirement_before_validation": "Owner approval for source-capture logger wiring plus G12 source/control acceptance",
      "expansion_binding_action": "derive from tick/source extractor or wait for forward logger; fail closed if unavailable",
      "fail_closed_missing_status": "QUOTE_SNAPSHOT_MISSING_FAIL_CLOSED",
      "field_name": "spread_source_hash",
      "future_logger_field": true
    },
    {
      "binding_class": "FORBIDDEN_REDACTED_STATUS_ONLY",
      "design_terminal_status": "FORBIDDEN_OR_REDACTED_SOURCE_ONLY",
      "exact_requirement_before_validation": "Keep raw values redacted/closed; opening them requires a separate approved label/cost evidence lane.",
      "expansion_binding_action": "emit status/redaction only; never include raw broker/account/order/result/cost value",
      "fail_closed_missing_status": "FORBIDDEN_FIELD_PRESENT_FAIL_CLOSED",
      "field_name": "slippage_label_status",
      "future_logger_field": false
    },
    {
      "binding_class": "FORBIDDEN_REDACTED_STATUS_ONLY",
      "design_terminal_status": "FORBIDDEN_OR_REDACTED_SOURCE_ONLY",
      "exact_requirement_before_validation": "Keep raw values redacted/closed; opening them requires a separate approved label/cost evidence lane.",
      "expansion_binding_action": "emit status/redaction only; never include raw broker/account/order/result/cost value",
      "fail_closed_missing_status": "FORBIDDEN_FIELD_PRESENT_FAIL_CLOSED",
      "field_name": "slippage_value_redaction_status",
      "future_logger_field": false
    },
    {
      "binding_class": "FORBIDDEN_REDACTED_STATUS_ONLY",
      "design_terminal_status": "FORBIDDEN_OR_REDACTED_SOURCE_ONLY",
      "exact_requirement_before_validation": "Keep raw values redacted/closed; opening them requires a separate approved label/cost evidence lane.",
      "expansion_binding_action": "emit status/redaction only; never include raw broker/account/order/result/cost value",
      "fail_closed_missing_status": "FORBIDDEN_FIELD_PRESENT_FAIL_CLOSED",
      "field_name": "execution_quality_label_status",
      "future_logger_field": false
    },
    {
      "binding_class": "FORBIDDEN_REDACTED_STATUS_ONLY",
      "design_terminal_status": "FORBIDDEN_OR_REDACTED_SOURCE_ONLY",
      "exact_requirement_before_validation": "Keep raw values redacted/closed; opening them requires a separate approved label/cost evidence lane.",
      "expansion_binding_action": "emit status/redaction only; never include raw broker/account/order/result/cost value",
      "fail_closed_missing_status": "FORBIDDEN_FIELD_PRESENT_FAIL_CLOSED",
      "field_name": "execution_quality_value_redaction_status",
      "future_logger_field": false
    },
    {
      "binding_class": "FORBIDDEN_REDACTED_STATUS_ONLY",
      "design_terminal_status": "FORBIDDEN_OR_REDACTED_SOURCE_ONLY",
      "exact_requirement_before_validation": "Keep raw values redacted/closed; opening them requires a separate approved label/cost evidence lane.",
      "expansion_binding_action": "emit status/redaction only; never include raw broker/account/order/result/cost value",
      "fail_closed_missing_status": "FORBIDDEN_FIELD_PRESENT_FAIL_CLOSED",
      "field_name": "cost_testing_gate_status",
      "future_logger_field": false
    },
    {
      "binding_class": "SOURCE_BOUND_HISTORICAL_OR_FAIL_CLOSED",
      "design_terminal_status": "EXISTING_SOURCE_SAFE_CAPTURE_READY",
      "exact_requirement_before_validation": "No owner action for existing source-safe binding; future extraction must preserve source hashes.",
      "expansion_binding_action": "preserve existing source-safe binding and source hash; fail closed if missing",
      "fail_closed_missing_status": "LIFECYCLE_PATH_SOURCE_MISSING_FAIL_CLOSED",
      "field_name": "pending_intent_created_utc",
      "future_logger_field": false
    },
    {
      "binding_class": "FUTURE_LOGGER_BOUND_REQUIRED_FOR_FULL_COVERAGE",
      "design_terminal_status": "FUTURE_LOGGER_FIELD_REQUIRED",
      "exact_requirement_before_validation": "Owner approval for source-capture logger wiring plus G12 source/control acceptance",
      "expansion_binding_action": "derive from tick/source extractor or wait for forward logger; fail closed if unavailable",
      "fail_closed_missing_status": "LIFECYCLE_PATH_SOURCE_MISSING_FAIL_CLOSED",
      "field_name": "pending_horizon_start_utc",
      "future_logger_field": true
    },
    {
      "binding_class": "FUTURE_LOGGER_BOUND_REQUIRED_FOR_FULL_COVERAGE",
      "design_terminal_status": "FUTURE_LOGGER_FIELD_REQUIRED",
      "exact_requirement_before_validation": "Owner approval for source-capture logger wiring plus G12 source/control acceptance",
      "expansion_binding_action": "derive from tick/source extractor or wait for forward logger; fail closed if unavailable",
      "fail_closed_missing_status": "LIFECYCLE_PATH_SOURCE_MISSING_FAIL_CLOSED",
      "field_name": "pending_horizon_end_utc",
      "future_logger_field": true
    },
    {
      "binding_class": "SOURCE_BOUND_HISTORICAL_OR_FAIL_CLOSED",
      "design_terminal_status": "EXISTING_SOURCE_SAFE_CAPTURE_READY",
      "exact_requirement_before_validation": "No owner action for existing source-safe binding; future extraction must preserve source hashes.",
      "expansion_binding_action": "preserve existing source-safe binding and source hash; fail closed if missing",
      "fail_closed_missing_status": "LIFECYCLE_PATH_SOURCE_MISSING_FAIL_CLOSED",
      "field_name": "cancel_expiry_utc",
      "future_logger_field": false
    },
    {
      "binding_class": "SOURCE_BOUND_HISTORICAL_OR_FAIL_CLOSED",
      "design_terminal_status": "EXISTING_SOURCE_SAFE_CAPTURE_READY",
      "exact_requirement_before_validation": "No owner action for existing source-safe binding; future extraction must preserve source hashes.",
      "expansion_binding_action": "preserve existing source-safe binding and source hash; fail closed if missing",
      "fail_closed_missing_status": "LIFECYCLE_PATH_SOURCE_MISSING_FAIL_CLOSED",
      "field_name": "cancel_expiry_reason_status",
      "future_logger_field": false
    },
    {
      "binding_class": "SOURCE_BOUND_HISTORICAL_OR_FAIL_CLOSED",
      "design_terminal_status": "EXISTING_SOURCE_SAFE_CAPTURE_READY",
      "exact_requirement_before_validation": "No owner action for existing source-safe binding; future extraction must preserve source hashes.",
      "expansion_binding_action": "preserve existing source-safe binding and source hash; fail closed if missing",
      "fail_closed_missing_status": "LIFECYCLE_PATH_SOURCE_MISSING_FAIL_CLOSED",
      "field_name": "entry_touch_first_utc",
      "future_logger_field": false
    },
    {
      "binding_class": "SOURCE_BOUND_HISTORICAL_OR_FAIL_CLOSED",
      "design_terminal_status": "EXISTING_SOURCE_SAFE_CAPTURE_READY",
      "exact_requirement_before_validation": "No owner action for existing source-safe binding; future extraction must preserve source hashes.",
      "expansion_binding_action": "preserve existing source-safe binding and source hash; fail closed if missing",
      "fail_closed_missing_status": "LIFECYCLE_PATH_SOURCE_MISSING_FAIL_CLOSED",
      "field_name": "side_aware_entry_touch_status",
      "future_logger_field": false
    },
    {
      "binding_class": "FUTURE_LOGGER_BOUND_REQUIRED_FOR_FULL_COVERAGE",
      "design_terminal_status": "FUTURE_LOGGER_FIELD_REQUIRED",
      "exact_requirement_before_validation": "Owner approval for source-capture logger wiring plus G12 source/control acceptance",
      "expansion_binding_action": "derive from tick/source extractor or wait for forward logger; fail closed if unavailable",
      "fail_closed_missing_status": "LIFECYCLE_PATH_SOURCE_MISSING_FAIL_CLOSED",
      "field_name": "terminal_area_touch_status",
      "future_logger_field": true
    },
    {
      "binding_class": "FUTURE_LOGGER_BOUND_REQUIRED_FOR_FULL_COVERAGE",
      "design_terminal_status": "FUTURE_LOGGER_FIELD_REQUIRED",
      "exact_requirement_before_validation": "Owner approval for source-capture logger wiring plus G12 source/control acceptance",
      "expansion_binding_action": "derive from tick/source extractor or wait for forward logger; fail closed if unavailable",
      "fail_closed_missing_status": "LIFECYCLE_PATH_SOURCE_MISSING_FAIL_CLOSED",
      "field_name": "terminal_area_first_touch_utc",
      "future_logger_field": true
    },
    {
      "binding_class": "FUTURE_LOGGER_BOUND_REQUIRED_FOR_FULL_COVERAGE",
      "design_terminal_status": "FUTURE_LOGGER_FIELD_REQUIRED",
      "exact_requirement_before_validation": "Owner approval for source-capture logger wiring plus G12 source/control acceptance",
      "expansion_binding_action": "derive from tick/source extractor or wait for forward logger; fail closed if unavailable",
      "fail_closed_missing_status": "LIFECYCLE_PATH_SOURCE_MISSING_FAIL_CLOSED",
      "field_name": "protective_area_touch_status",
      "future_logger_field": true
    },
    {
      "binding_class": "FUTURE_LOGGER_BOUND_REQUIRED_FOR_FULL_COVERAGE",
      "design_terminal_status": "FUTURE_LOGGER_FIELD_REQUIRED",
      "exact_requirement_before_validation": "Owner approval for source-capture logger wiring plus G12 source/control acceptance",
      "expansion_binding_action": "derive from tick/source extractor or wait for forward logger; fail closed if unavailable",
      "fail_closed_missing_status": "LIFECYCLE_PATH_SOURCE_MISSING_FAIL_CLOSED",
      "field_name": "protective_area_first_touch_utc",
      "future_logger_field": true
    },
    {
      "binding_class": "SOURCE_BOUND_HISTORICAL_OR_FAIL_CLOSED",
      "design_terminal_status": "EXISTING_SOURCE_SAFE_CAPTURE_READY",
      "exact_requirement_before_validation": "No owner action for existing source-safe binding; future extraction must preserve source hashes.",
      "expansion_binding_action": "preserve existing source-safe binding and source hash; fail closed if missing",
      "fail_closed_missing_status": "EVENT_ORDER_METHOD_MISSING_FAIL_CLOSED",
      "field_name": "event_order_resolution_method",
      "future_logger_field": false
    },
    {
      "binding_class": "SOURCE_BOUND_HISTORICAL_OR_FAIL_CLOSED",
      "design_terminal_status": "EXISTING_SOURCE_SAFE_CAPTURE_READY",
      "exact_requirement_before_validation": "No owner action for existing source-safe binding; future extraction must preserve source hashes.",
      "expansion_binding_action": "preserve existing source-safe binding and source hash; fail closed if missing",
      "fail_closed_missing_status": "EVENT_ORDER_METHOD_MISSING_FAIL_CLOSED",
      "field_name": "same_tick_same_bar_ambiguity_status",
      "future_logger_field": false
    },
    {
      "binding_class": "SOURCE_BOUND_HISTORICAL_OR_FAIL_CLOSED",
      "design_terminal_status": "EXISTING_SOURCE_SAFE_CAPTURE_READY",
      "exact_requirement_before_validation": "No owner action for existing source-safe binding; future extraction must preserve source hashes.",
      "expansion_binding_action": "preserve existing source-safe binding and source hash; fail closed if missing",
      "fail_closed_missing_status": "LOWER_TF_COVERAGE_MISSING_FAIL_CLOSED",
      "field_name": "lower_tf_coverage_window_start_utc",
      "future_logger_field": false
    },
    {
      "binding_class": "SOURCE_BOUND_HISTORICAL_OR_FAIL_CLOSED",
      "design_terminal_status": "EXISTING_SOURCE_SAFE_CAPTURE_READY",
      "exact_requirement_before_validation": "No owner action for existing source-safe binding; future extraction must preserve source hashes.",
      "expansion_binding_action": "preserve existing source-safe binding and source hash; fail closed if missing",
      "fail_closed_missing_status": "LOWER_TF_COVERAGE_MISSING_FAIL_CLOSED",
      "field_name": "lower_tf_coverage_window_end_utc",
      "future_logger_field": false
    },
    {
      "binding_class": "SOURCE_BOUND_HISTORICAL_OR_FAIL_CLOSED",
      "design_terminal_status": "EXISTING_SOURCE_SAFE_CAPTURE_READY",
      "exact_requirement_before_validation": "No owner action for existing source-safe binding; future extraction must preserve source hashes.",
      "expansion_binding_action": "preserve existing source-safe binding and source hash; fail closed if missing",
      "fail_closed_missing_status": "LOWER_TF_COVERAGE_MISSING_FAIL_CLOSED",
      "field_name": "missing_coverage_intervals",
      "future_logger_field": false
    },
    {
      "binding_class": "SCHEMA_ONLY_CONTROL",
      "design_terminal_status": "SCHEMA_ONLY_CONTROL_FIELD",
      "exact_requirement_before_validation": "Parser/verifier must recompute and hash the control field before validation execution.",
      "expansion_binding_action": "emit deterministic schema/control value from builder, not from outcomes",
      "fail_closed_missing_status": "CONTROL_FIELD_MISSING_FAIL_CLOSED",
      "field_name": "row_level_denominator_member",
      "future_logger_field": false
    },
    {
      "binding_class": "SCHEMA_ONLY_CONTROL",
      "design_terminal_status": "SCHEMA_ONLY_CONTROL_FIELD",
      "exact_requirement_before_validation": "Parser/verifier must recompute and hash the control field before validation execution.",
      "expansion_binding_action": "emit deterministic schema/control value from builder, not from outcomes",
      "fail_closed_missing_status": "CONTROL_FIELD_MISSING_FAIL_CLOSED",
      "field_name": "nofill_duplicate_key_count_member",
      "future_logger_field": false
    },
    {
      "binding_class": "SCHEMA_ONLY_CONTROL",
      "design_terminal_status": "SCHEMA_ONLY_CONTROL_FIELD",
      "exact_requirement_before_validation": "Parser/verifier must recompute and hash the control field before validation execution.",
      "expansion_binding_action": "emit deterministic schema/control value from builder, not from outcomes",
      "fail_closed_missing_status": "CONTROL_FIELD_MISSING_FAIL_CLOSED",
      "field_name": "duplicate_group_id_count_member",
      "future_logger_field": false
    },
    {
      "binding_class": "SCHEMA_ONLY_CONTROL",
      "design_terminal_status": "SCHEMA_ONLY_CONTROL_FIELD",
      "exact_requirement_before_validation": "Parser/verifier must recompute and hash the control field before validation execution.",
      "expansion_binding_action": "emit deterministic schema/control value from builder, not from outcomes",
      "fail_closed_missing_status": "CONTROL_FIELD_MISSING_FAIL_CLOSED",
      "field_name": "nofill_duplicate_key_sha256",
      "future_logger_field": false
    },
    {
      "binding_class": "SCHEMA_ONLY_CONTROL",
      "design_terminal_status": "SCHEMA_ONLY_CONTROL_FIELD",
      "exact_requirement_before_validation": "Parser/verifier must recompute and hash the control field before validation execution.",
      "expansion_binding_action": "emit deterministic schema/control value from builder, not from outcomes",
      "fail_closed_missing_status": "CONTROL_FIELD_MISSING_FAIL_CLOSED",
      "field_name": "duplicate_group_id_sha256",
      "future_logger_field": false
    },
    {
      "binding_class": "SOURCE_BOUND_HISTORICAL_OR_FAIL_CLOSED",
      "design_terminal_status": "EXISTING_SOURCE_SAFE_CAPTURE_READY",
      "exact_requirement_before_validation": "No owner action for existing source-safe binding; future extraction must preserve source hashes.",
      "expansion_binding_action": "preserve existing source-safe binding and source hash; fail closed if missing",
      "fail_closed_missing_status": "SOURCE_FIELD_MISSING_FAIL_CLOSED",
      "field_name": "session_tag",
      "future_logger_field": false
    },
    {
      "binding_class": "SOURCE_BOUND_HISTORICAL_OR_FAIL_CLOSED",
      "design_terminal_status": "EXISTING_SOURCE_SAFE_CAPTURE_READY",
      "exact_requirement_before_validation": "No owner action for existing source-safe binding; future extraction must preserve source hashes.",
      "expansion_binding_action": "preserve existing source-safe binding and source hash; fail closed if missing",
      "fail_closed_missing_status": "SOURCE_FIELD_MISSING_FAIL_CLOSED",
      "field_name": "regime_context_status",
      "future_logger_field": false
    },
    {
      "binding_class": "SCHEMA_ONLY_CONTROL",
      "design_terminal_status": "SCHEMA_ONLY_CONTROL_FIELD",
      "exact_requirement_before_validation": "Parser/verifier must recompute and hash the control field before validation execution.",
      "expansion_binding_action": "emit deterministic schema/control value from builder, not from outcomes",
      "fail_closed_missing_status": "CONTROL_FIELD_MISSING_FAIL_CLOSED",
      "field_name": "sample_floor_policy_id",
      "future_logger_field": false
    },
    {
      "binding_class": "SCHEMA_ONLY_CONTROL",
      "design_terminal_status": "SCHEMA_ONLY_CONTROL_FIELD",
      "exact_requirement_before_validation": "Parser/verifier must recompute and hash the control field before validation execution.",
      "expansion_binding_action": "emit deterministic schema/control value from builder, not from outcomes",
      "fail_closed_missing_status": "CONTROL_FIELD_MISSING_FAIL_CLOSED",
      "field_name": "perturbation_ready_bucket",
      "future_logger_field": false
    },
    {
      "binding_class": "SCHEMA_ONLY_CONTROL",
      "design_terminal_status": "SCHEMA_ONLY_CONTROL_FIELD",
      "exact_requirement_before_validation": "Parser/verifier must recompute and hash the control field before validation execution.",
      "expansion_binding_action": "emit deterministic schema/control value from builder, not from outcomes",
      "fail_closed_missing_status": "CONTROL_FIELD_MISSING_FAIL_CLOSED",
      "field_name": "kill_switch_observability_status",
      "future_logger_field": false
    },
    {
      "binding_class": "SCHEMA_ONLY_CONTROL",
      "design_terminal_status": "SCHEMA_ONLY_CONTROL_FIELD",
      "exact_requirement_before_validation": "Parser/verifier must recompute and hash the control field before validation execution.",
      "expansion_binding_action": "emit deterministic schema/control value from builder, not from outcomes",
      "fail_closed_missing_status": "CONTROL_FIELD_MISSING_FAIL_CLOSED",
      "field_name": "source_artifact_hash",
      "future_logger_field": false
    },
    {
      "binding_class": "SCHEMA_ONLY_CONTROL",
      "design_terminal_status": "SCHEMA_ONLY_CONTROL_FIELD",
      "exact_requirement_before_validation": "Parser/verifier must recompute and hash the control field before validation execution.",
      "expansion_binding_action": "emit deterministic schema/control value from builder, not from outcomes",
      "fail_closed_missing_status": "CONTROL_FIELD_MISSING_FAIL_CLOSED",
      "field_name": "parser_code_hash",
      "future_logger_field": false
    },
    {
      "binding_class": "SCHEMA_ONLY_CONTROL",
      "design_terminal_status": "SCHEMA_ONLY_CONTROL_FIELD",
      "exact_requirement_before_validation": "Parser/verifier must recompute and hash the control field before validation execution.",
      "expansion_binding_action": "emit deterministic schema/control value from builder, not from outcomes",
      "fail_closed_missing_status": "CONTROL_FIELD_MISSING_FAIL_CLOSED",
      "field_name": "forbidden_field_scan_status",
      "future_logger_field": false
    }
  ],
  "future_logger_field_count": 20,
  "generated_at_utc": "2026-05-10T04:31:04Z",
  "live_effect": false,
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
  "route_id": "G0_NOFILL_HISTORICAL_PARTITION_SOURCE_BINDING_SYNTHESIS_CONTROL_REVIEW",
  "runtime_field_count": 55,
  "schema_version": "g0_nofill_historical_partition_source_binding_synthesis_control_review_v1",
  "validation_safe": false
}
```
