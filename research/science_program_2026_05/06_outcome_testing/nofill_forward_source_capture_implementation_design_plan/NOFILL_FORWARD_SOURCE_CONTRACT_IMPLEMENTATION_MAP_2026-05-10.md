# NOFILL Forward Source Contract Implementation Map

Promotion verdict: `NO_PROMOTION_VERDICT`

## Terminal Status Counts

| Status | Count |
|---|---:|
| `BLOCKED_WITH_EXACT_OWNER_APPROVAL_OR_SOURCE_REQUIREMENT` | 0 |
| `EXISTING_SOURCE_SAFE_CAPTURE_READY` | 17 |
| `FORBIDDEN_OR_REDACTED_SOURCE_ONLY` | 7 |
| `FUTURE_LOGGER_FIELD_REQUIRED` | 20 |
| `SCHEMA_ONLY_CONTROL_FIELD` | 11 |

## Field Closure Ledger

| Field | Family | Terminal status | Target source surface | Fail-closed status | Fixture |
|---|---|---|---|---|---|
| `capture_observed_at_utc` | `capture_latency_clock` | `EXISTING_SOURCE_SAFE_CAPTURE_READY` | future sanitized nofill_forward_source_capture writer wrapper | `SOURCE_FIELD_MISSING_FAIL_CLOSED` | `FIXTURE_EXISTING_SOURCE_SAFE_PROJECTION` |
| `capture_write_started_at_utc` | `capture_latency_clock` | `FUTURE_LOGGER_FIELD_REQUIRED` | future sanitized nofill_forward_source_capture writer wrapper | `WRITE_CLOCK_MISSING_FAIL_CLOSED` | `FIXTURE_WRITE_CLOCK_COMPLETE_AND_MISSING` |
| `capture_write_completed_at_utc` | `capture_latency_clock` | `FUTURE_LOGGER_FIELD_REQUIRED` | future sanitized nofill_forward_source_capture writer wrapper | `WRITE_CLOCK_MISSING_FAIL_CLOSED` | `FIXTURE_WRITE_CLOCK_COMPLETE_AND_MISSING` |
| `capture_latency_ms` | `capture_latency_clock` | `FUTURE_LOGGER_FIELD_REQUIRED` | future sanitized nofill_forward_source_capture writer wrapper | `WRITE_CLOCK_MISSING_FAIL_CLOSED` | `FIXTURE_WRITE_CLOCK_COMPLETE_AND_MISSING` |
| `capture_clock_source_status` | `capture_latency_clock` | `FUTURE_LOGGER_FIELD_REQUIRED` | future sanitized nofill_forward_source_capture writer wrapper | `CLOCK_SOURCE_MISSING_FAIL_CLOSED` | `FIXTURE_CLOCK_SOURCE_AND_SKEW_STATUS` |
| `capture_clock_skew_ms` | `capture_latency_clock` | `FUTURE_LOGGER_FIELD_REQUIRED` | future sanitized nofill_forward_source_capture writer wrapper | `CLOCK_SOURCE_MISSING_FAIL_CLOSED` | `FIXTURE_CLOCK_SOURCE_AND_SKEW_STATUS` |
| `capture_clock_skew_status` | `capture_latency_clock` | `FUTURE_LOGGER_FIELD_REQUIRED` | future sanitized nofill_forward_source_capture writer wrapper | `CLOCK_SOURCE_MISSING_FAIL_CLOSED` | `FIXTURE_CLOCK_SOURCE_AND_SKEW_STATUS` |
| `capture_timestamp_derivation_rule` | `capture_latency_clock` | `EXISTING_SOURCE_SAFE_CAPTURE_READY` | future sanitized nofill_forward_source_capture writer wrapper | `SOURCE_FIELD_MISSING_FAIL_CLOSED` | `FIXTURE_EXISTING_SOURCE_SAFE_PROJECTION` |
| `pending_order_mode_source_safe` | `pending_order_observability` | `EXISTING_SOURCE_SAFE_CAPTURE_READY` | strategy_follow_candidates and pending_limit_lifecycle projected through redaction | `SOURCE_FIELD_MISSING_FAIL_CLOSED` | `FIXTURE_PENDING_ORDER_OBSERVABILITY_REDACTED` |
| `pending_order_mode_status` | `pending_order_observability` | `EXISTING_SOURCE_SAFE_CAPTURE_READY` | strategy_follow_candidates and pending_limit_lifecycle projected through redaction | `SOURCE_FIELD_MISSING_FAIL_CLOSED` | `FIXTURE_PENDING_ORDER_OBSERVABILITY_REDACTED` |
| `broker_pending_order_created_status` | `pending_order_observability` | `EXISTING_SOURCE_SAFE_CAPTURE_READY` | strategy_follow_candidates and pending_limit_lifecycle projected through redaction | `SOURCE_FIELD_MISSING_FAIL_CLOSED` | `FIXTURE_PENDING_ORDER_OBSERVABILITY_REDACTED` |
| `native_pending_order_type_source_safe` | `pending_order_observability` | `FUTURE_LOGGER_FIELD_REQUIRED` | strategy_follow_candidates and pending_limit_lifecycle projected through redaction | `SOURCE_FIELD_MISSING_FAIL_CLOSED` | `FIXTURE_PENDING_ORDER_OBSERVABILITY_REDACTED` |
| `native_pending_order_type_status` | `pending_order_observability` | `FUTURE_LOGGER_FIELD_REQUIRED` | strategy_follow_candidates and pending_limit_lifecycle projected through redaction | `SOURCE_FIELD_MISSING_FAIL_CLOSED` | `FIXTURE_PENDING_ORDER_OBSERVABILITY_REDACTED` |
| `raw_ticket_field_present_status` | `pending_order_observability` | `FORBIDDEN_OR_REDACTED_SOURCE_ONLY` | redaction projection before any output row is accepted | `FORBIDDEN_FIELD_PRESENT_FAIL_CLOSED` | `FIXTURE_REDACTION_STATUS_ONLY_ROW` |
| `mt5_order_ticket_redaction_status` | `pending_order_observability` | `FORBIDDEN_OR_REDACTED_SOURCE_ONLY` | redaction projection before any output row is accepted | `FORBIDDEN_FIELD_PRESENT_FAIL_CLOSED` | `FIXTURE_REDACTION_STATUS_ONLY_ROW` |
| `decision_spread_status` | `spread_slippage_execution_quality_status` | `FUTURE_LOGGER_FIELD_REQUIRED` | future quote or tick snapshot join at decision and first-touch timestamps | `QUOTE_SNAPSHOT_MISSING_FAIL_CLOSED` | `FIXTURE_DECISION_AND_TOUCH_QUOTE_SNAPSHOT` |
| `decision_spread_value_source_safe` | `spread_slippage_execution_quality_status` | `FUTURE_LOGGER_FIELD_REQUIRED` | future quote or tick snapshot join at decision and first-touch timestamps | `QUOTE_SNAPSHOT_MISSING_FAIL_CLOSED` | `FIXTURE_DECISION_AND_TOUCH_QUOTE_SNAPSHOT` |
| `decision_spread_unit` | `spread_slippage_execution_quality_status` | `FUTURE_LOGGER_FIELD_REQUIRED` | future quote or tick snapshot join at decision and first-touch timestamps | `QUOTE_SNAPSHOT_MISSING_FAIL_CLOSED` | `FIXTURE_DECISION_AND_TOUCH_QUOTE_SNAPSHOT` |
| `entry_touch_spread_status` | `spread_slippage_execution_quality_status` | `FUTURE_LOGGER_FIELD_REQUIRED` | future quote or tick snapshot join at decision and first-touch timestamps | `QUOTE_SNAPSHOT_MISSING_FAIL_CLOSED` | `FIXTURE_DECISION_AND_TOUCH_QUOTE_SNAPSHOT` |
| `entry_touch_spread_value_source_safe` | `spread_slippage_execution_quality_status` | `FUTURE_LOGGER_FIELD_REQUIRED` | future quote or tick snapshot join at decision and first-touch timestamps | `QUOTE_SNAPSHOT_MISSING_FAIL_CLOSED` | `FIXTURE_DECISION_AND_TOUCH_QUOTE_SNAPSHOT` |
| `spread_source_hash` | `spread_slippage_execution_quality_status` | `FUTURE_LOGGER_FIELD_REQUIRED` | future quote or tick snapshot join at decision and first-touch timestamps | `QUOTE_SNAPSHOT_MISSING_FAIL_CLOSED` | `FIXTURE_DECISION_AND_TOUCH_QUOTE_SNAPSHOT` |
| `slippage_label_status` | `spread_slippage_execution_quality_status` | `FORBIDDEN_OR_REDACTED_SOURCE_ONLY` | redaction projection before any output row is accepted | `FORBIDDEN_FIELD_PRESENT_FAIL_CLOSED` | `FIXTURE_REDACTION_STATUS_ONLY_ROW` |
| `slippage_value_redaction_status` | `spread_slippage_execution_quality_status` | `FORBIDDEN_OR_REDACTED_SOURCE_ONLY` | redaction projection before any output row is accepted | `FORBIDDEN_FIELD_PRESENT_FAIL_CLOSED` | `FIXTURE_REDACTION_STATUS_ONLY_ROW` |
| `execution_quality_label_status` | `spread_slippage_execution_quality_status` | `FORBIDDEN_OR_REDACTED_SOURCE_ONLY` | redaction projection before any output row is accepted | `FORBIDDEN_FIELD_PRESENT_FAIL_CLOSED` | `FIXTURE_REDACTION_STATUS_ONLY_ROW` |
| `execution_quality_value_redaction_status` | `spread_slippage_execution_quality_status` | `FORBIDDEN_OR_REDACTED_SOURCE_ONLY` | redaction projection before any output row is accepted | `FORBIDDEN_FIELD_PRESENT_FAIL_CLOSED` | `FIXTURE_REDACTION_STATUS_ONLY_ROW` |
| `cost_testing_gate_status` | `spread_slippage_execution_quality_status` | `FORBIDDEN_OR_REDACTED_SOURCE_ONLY` | redaction projection before any output row is accepted | `FORBIDDEN_FIELD_PRESENT_FAIL_CLOSED` | `FIXTURE_REDACTION_STATUS_ONLY_ROW` |
| `pending_intent_created_utc` | `pending_lifecycle` | `EXISTING_SOURCE_SAFE_CAPTURE_READY` | pending_limit_lifecycle_audit plus candidate_ltf_path_order projection | `LIFECYCLE_PATH_SOURCE_MISSING_FAIL_CLOSED` | `FIXTURE_PENDING_LIFECYCLE_TOUCH_STATES` |
| `pending_horizon_start_utc` | `pending_lifecycle` | `FUTURE_LOGGER_FIELD_REQUIRED` | pending_limit_lifecycle_audit plus candidate_ltf_path_order projection | `LIFECYCLE_PATH_SOURCE_MISSING_FAIL_CLOSED` | `FIXTURE_PENDING_LIFECYCLE_TOUCH_STATES` |
| `pending_horizon_end_utc` | `pending_lifecycle` | `FUTURE_LOGGER_FIELD_REQUIRED` | pending_limit_lifecycle_audit plus candidate_ltf_path_order projection | `LIFECYCLE_PATH_SOURCE_MISSING_FAIL_CLOSED` | `FIXTURE_PENDING_LIFECYCLE_TOUCH_STATES` |
| `cancel_expiry_utc` | `pending_lifecycle` | `EXISTING_SOURCE_SAFE_CAPTURE_READY` | pending_limit_lifecycle_audit plus candidate_ltf_path_order projection | `LIFECYCLE_PATH_SOURCE_MISSING_FAIL_CLOSED` | `FIXTURE_PENDING_LIFECYCLE_TOUCH_STATES` |
| `cancel_expiry_reason_status` | `pending_lifecycle` | `EXISTING_SOURCE_SAFE_CAPTURE_READY` | pending_limit_lifecycle_audit plus candidate_ltf_path_order projection | `LIFECYCLE_PATH_SOURCE_MISSING_FAIL_CLOSED` | `FIXTURE_PENDING_LIFECYCLE_TOUCH_STATES` |
| `entry_touch_first_utc` | `entry_touch_observability` | `EXISTING_SOURCE_SAFE_CAPTURE_READY` | pending_limit_lifecycle_audit plus candidate_ltf_path_order projection | `LIFECYCLE_PATH_SOURCE_MISSING_FAIL_CLOSED` | `FIXTURE_PENDING_LIFECYCLE_TOUCH_STATES` |
| `side_aware_entry_touch_status` | `entry_touch_observability` | `EXISTING_SOURCE_SAFE_CAPTURE_READY` | pending_limit_lifecycle_audit plus candidate_ltf_path_order projection | `LIFECYCLE_PATH_SOURCE_MISSING_FAIL_CLOSED` | `FIXTURE_PENDING_LIFECYCLE_TOUCH_STATES` |
| `terminal_area_touch_status` | `terminal_area_observability` | `FUTURE_LOGGER_FIELD_REQUIRED` | pending_limit_lifecycle_audit plus candidate_ltf_path_order projection | `LIFECYCLE_PATH_SOURCE_MISSING_FAIL_CLOSED` | `FIXTURE_PENDING_LIFECYCLE_TOUCH_STATES` |
| `terminal_area_first_touch_utc` | `terminal_area_observability` | `FUTURE_LOGGER_FIELD_REQUIRED` | pending_limit_lifecycle_audit plus candidate_ltf_path_order projection | `LIFECYCLE_PATH_SOURCE_MISSING_FAIL_CLOSED` | `FIXTURE_PENDING_LIFECYCLE_TOUCH_STATES` |
| `protective_area_touch_status` | `terminal_area_observability` | `FUTURE_LOGGER_FIELD_REQUIRED` | pending_limit_lifecycle_audit plus candidate_ltf_path_order projection | `LIFECYCLE_PATH_SOURCE_MISSING_FAIL_CLOSED` | `FIXTURE_PENDING_LIFECYCLE_TOUCH_STATES` |
| `protective_area_first_touch_utc` | `terminal_area_observability` | `FUTURE_LOGGER_FIELD_REQUIRED` | pending_limit_lifecycle_audit plus candidate_ltf_path_order projection | `LIFECYCLE_PATH_SOURCE_MISSING_FAIL_CLOSED` | `FIXTURE_PENDING_LIFECYCLE_TOUCH_STATES` |
| `event_order_resolution_method` | `event_order_resolution` | `EXISTING_SOURCE_SAFE_CAPTURE_READY` | candidate_ltf_path_order source-safe path-order classifier | `EVENT_ORDER_METHOD_MISSING_FAIL_CLOSED` | `FIXTURE_EVENT_ORDER_AMBIGUITY` |
| `same_tick_same_bar_ambiguity_status` | `event_order_resolution` | `EXISTING_SOURCE_SAFE_CAPTURE_READY` | candidate_ltf_path_order source-safe path-order classifier | `EVENT_ORDER_METHOD_MISSING_FAIL_CLOSED` | `FIXTURE_EVENT_ORDER_AMBIGUITY` |
| `lower_tf_coverage_window_start_utc` | `source_coverage` | `EXISTING_SOURCE_SAFE_CAPTURE_READY` | candidate_ltf_path_order coverage window projection | `LOWER_TF_COVERAGE_MISSING_FAIL_CLOSED` | `FIXTURE_LOWER_TF_COVERAGE_GAP` |
| `lower_tf_coverage_window_end_utc` | `source_coverage` | `EXISTING_SOURCE_SAFE_CAPTURE_READY` | candidate_ltf_path_order coverage window projection | `LOWER_TF_COVERAGE_MISSING_FAIL_CLOSED` | `FIXTURE_LOWER_TF_COVERAGE_GAP` |
| `missing_coverage_intervals` | `source_coverage` | `EXISTING_SOURCE_SAFE_CAPTURE_READY` | candidate_ltf_path_order coverage window projection | `LOWER_TF_COVERAGE_MISSING_FAIL_CLOSED` | `FIXTURE_LOWER_TF_COVERAGE_GAP` |
| `row_level_denominator_member` | `duplicate_denominator` | `SCHEMA_ONLY_CONTROL_FIELD` | offline projection parser and source hash manifest | `CONTROL_FIELD_MISSING_FAIL_CLOSED` | `FIXTURE_CONTROL_AND_HASH_MANIFEST_ROW` |
| `nofill_duplicate_key_count_member` | `duplicate_denominator` | `SCHEMA_ONLY_CONTROL_FIELD` | offline projection parser and source hash manifest | `CONTROL_FIELD_MISSING_FAIL_CLOSED` | `FIXTURE_CONTROL_AND_HASH_MANIFEST_ROW` |
| `duplicate_group_id_count_member` | `duplicate_denominator` | `SCHEMA_ONLY_CONTROL_FIELD` | offline projection parser and source hash manifest | `CONTROL_FIELD_MISSING_FAIL_CLOSED` | `FIXTURE_CONTROL_AND_HASH_MANIFEST_ROW` |
| `nofill_duplicate_key_sha256` | `duplicate_denominator` | `SCHEMA_ONLY_CONTROL_FIELD` | offline projection parser and source hash manifest | `CONTROL_FIELD_MISSING_FAIL_CLOSED` | `FIXTURE_CONTROL_AND_HASH_MANIFEST_ROW` |
| `duplicate_group_id_sha256` | `duplicate_denominator` | `SCHEMA_ONLY_CONTROL_FIELD` | offline projection parser and source hash manifest | `CONTROL_FIELD_MISSING_FAIL_CLOSED` | `FIXTURE_CONTROL_AND_HASH_MANIFEST_ROW` |
| `session_tag` | `regime_session_review_control` | `EXISTING_SOURCE_SAFE_CAPTURE_READY` | strategy_follow_candidates session and regime source-safe metadata | `SOURCE_FIELD_MISSING_FAIL_CLOSED` | `FIXTURE_EXISTING_SOURCE_SAFE_PROJECTION` |
| `regime_context_status` | `regime_session_review_control` | `EXISTING_SOURCE_SAFE_CAPTURE_READY` | strategy_follow_candidates session and regime source-safe metadata | `SOURCE_FIELD_MISSING_FAIL_CLOSED` | `FIXTURE_EXISTING_SOURCE_SAFE_PROJECTION` |
| `sample_floor_policy_id` | `regime_session_review_control` | `SCHEMA_ONLY_CONTROL_FIELD` | offline projection parser and source hash manifest | `CONTROL_FIELD_MISSING_FAIL_CLOSED` | `FIXTURE_CONTROL_AND_HASH_MANIFEST_ROW` |
| `perturbation_ready_bucket` | `regime_session_review_control` | `SCHEMA_ONLY_CONTROL_FIELD` | offline projection parser and source hash manifest | `CONTROL_FIELD_MISSING_FAIL_CLOSED` | `FIXTURE_CONTROL_AND_HASH_MANIFEST_ROW` |
| `kill_switch_observability_status` | `regime_session_review_control` | `SCHEMA_ONLY_CONTROL_FIELD` | offline projection parser and source hash manifest | `CONTROL_FIELD_MISSING_FAIL_CLOSED` | `FIXTURE_CONTROL_AND_HASH_MANIFEST_ROW` |
| `source_artifact_hash` | `source_provenance` | `SCHEMA_ONLY_CONTROL_FIELD` | offline projection parser and source hash manifest | `CONTROL_FIELD_MISSING_FAIL_CLOSED` | `FIXTURE_CONTROL_AND_HASH_MANIFEST_ROW` |
| `parser_code_hash` | `source_provenance` | `SCHEMA_ONLY_CONTROL_FIELD` | offline projection parser and source hash manifest | `CONTROL_FIELD_MISSING_FAIL_CLOSED` | `FIXTURE_CONTROL_AND_HASH_MANIFEST_ROW` |
| `forbidden_field_scan_status` | `no_leak_control` | `SCHEMA_ONLY_CONTROL_FIELD` | offline projection parser and source hash manifest | `CONTROL_FIELD_MISSING_FAIL_CLOSED` | `FIXTURE_CONTROL_AND_HASH_MANIFEST_ROW` |
