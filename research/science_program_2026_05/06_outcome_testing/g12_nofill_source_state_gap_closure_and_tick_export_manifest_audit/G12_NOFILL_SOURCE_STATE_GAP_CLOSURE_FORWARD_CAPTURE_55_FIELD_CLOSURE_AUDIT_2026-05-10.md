# G12 Nofill Source State Gap Closure Forward Capture 55 Field Closure Audit 2026-05-10

- Route: `G12_NOFILL_SOURCE_STATE_GAP_CLOSURE_AND_TICK_EXPORT_MANIFEST_AUDIT`
- Generated: `2026-05-10T09:13:22Z`
- Promotion posture: `NO_PROMOTION_VERDICT`
- Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

- audit_status: `PASS`
- field_count: `55`

```json
{
  "artifact_family": "forward_capture_55_field_closure_audit",
  "audit_status": "PASS",
  "changes_live_trading_behavior": false,
  "closure_class_counts": {
    "already_source_bound_or_source_safe_projection": 17,
    "exact_forward_capture_requirement": 20,
    "forbidden_redacted_status_only": 7,
    "schema_only_control": 11
  },
  "credentials_touched": false,
  "field_count": 55,
  "field_names_match_runtime_contract": true,
  "forward_matrix_counts": {
    "accepted_contract_field_count": 55,
    "future_logger_field_count": 20,
    "implementation_field_count": 55
  },
  "generated_at_utc": "2026-05-10T09:13:22Z",
  "live_effect": false,
  "missing_from_runtime": [],
  "missing_from_target_closure": [],
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
  "route_id": "G12_NOFILL_SOURCE_STATE_GAP_CLOSURE_AND_TICK_EXPORT_MANIFEST_AUDIT",
  "rows": [
    {
      "contract_terminal_status": "EXISTING_SOURCE_SAFE_CAPTURE_READY",
      "fail_closed_missing_status": "SOURCE_FIELD_MISSING_FAIL_CLOSED",
      "field_closure_class": "already_source_bound_or_source_safe_projection",
      "field_family": "from_parser_schema",
      "field_name": "capture_observed_at_utc",
      "historical_gap_resolution": "Closed by source-safe projection, schema control, or redacted status-only rule.",
      "market_data_role": "not_market_data_export_primary",
      "owner_or_source_requirement": "Use accepted forward-capture contract requirement."
    },
    {
      "contract_terminal_status": "FUTURE_LOGGER_FIELD_REQUIRED",
      "fail_closed_missing_status": "WRITE_CLOCK_MISSING_FAIL_CLOSED",
      "field_closure_class": "exact_forward_capture_requirement",
      "field_family": "from_parser_schema",
      "field_name": "capture_write_started_at_utc",
      "historical_gap_resolution": "Cannot repair absent historical GTOS source-state unless an existing source-safe log is found; future rows must emit or fail closed under this field.",
      "market_data_role": "not_market_data_export_primary",
      "owner_or_source_requirement": "Use accepted forward-capture contract requirement."
    },
    {
      "contract_terminal_status": "FUTURE_LOGGER_FIELD_REQUIRED",
      "fail_closed_missing_status": "WRITE_CLOCK_MISSING_FAIL_CLOSED",
      "field_closure_class": "exact_forward_capture_requirement",
      "field_family": "from_parser_schema",
      "field_name": "capture_write_completed_at_utc",
      "historical_gap_resolution": "Cannot repair absent historical GTOS source-state unless an existing source-safe log is found; future rows must emit or fail closed under this field.",
      "market_data_role": "not_market_data_export_primary",
      "owner_or_source_requirement": "Use accepted forward-capture contract requirement."
    },
    {
      "contract_terminal_status": "FUTURE_LOGGER_FIELD_REQUIRED",
      "fail_closed_missing_status": "WRITE_CLOCK_MISSING_FAIL_CLOSED",
      "field_closure_class": "exact_forward_capture_requirement",
      "field_family": "from_parser_schema",
      "field_name": "capture_latency_ms",
      "historical_gap_resolution": "Cannot repair absent historical GTOS source-state unless an existing source-safe log is found; future rows must emit or fail closed under this field.",
      "market_data_role": "not_market_data_export_primary",
      "owner_or_source_requirement": "Use accepted forward-capture contract requirement."
    },
    {
      "contract_terminal_status": "FUTURE_LOGGER_FIELD_REQUIRED",
      "fail_closed_missing_status": "CLOCK_SOURCE_MISSING_FAIL_CLOSED",
      "field_closure_class": "exact_forward_capture_requirement",
      "field_family": "from_parser_schema",
      "field_name": "capture_clock_source_status",
      "historical_gap_resolution": "Cannot repair absent historical GTOS source-state unless an existing source-safe log is found; future rows must emit or fail closed under this field.",
      "market_data_role": "not_market_data_export_primary",
      "owner_or_source_requirement": "Use accepted forward-capture contract requirement."
    },
    {
      "contract_terminal_status": "FUTURE_LOGGER_FIELD_REQUIRED",
      "fail_closed_missing_status": "CLOCK_SOURCE_MISSING_FAIL_CLOSED",
      "field_closure_class": "exact_forward_capture_requirement",
      "field_family": "from_parser_schema",
      "field_name": "capture_clock_skew_ms",
      "historical_gap_resolution": "Cannot repair absent historical GTOS source-state unless an existing source-safe log is found; future rows must emit or fail closed under this field.",
      "market_data_role": "not_market_data_export_primary",
      "owner_or_source_requirement": "Use accepted forward-capture contract requirement."
    },
    {
      "contract_terminal_status": "FUTURE_LOGGER_FIELD_REQUIRED",
      "fail_closed_missing_status": "CLOCK_SOURCE_MISSING_FAIL_CLOSED",
      "field_closure_class": "exact_forward_capture_requirement",
      "field_family": "from_parser_schema",
      "field_name": "capture_clock_skew_status",
      "historical_gap_resolution": "Cannot repair absent historical GTOS source-state unless an existing source-safe log is found; future rows must emit or fail closed under this field.",
      "market_data_role": "not_market_data_export_primary",
      "owner_or_source_requirement": "Use accepted forward-capture contract requirement."
    },
    {
      "contract_terminal_status": "EXISTING_SOURCE_SAFE_CAPTURE_READY",
      "fail_closed_missing_status": "SOURCE_FIELD_MISSING_FAIL_CLOSED",
      "field_closure_class": "already_source_bound_or_source_safe_projection",
      "field_family": "from_parser_schema",
      "field_name": "capture_timestamp_derivation_rule",
      "historical_gap_resolution": "Closed by source-safe projection, schema control, or redacted status-only rule.",
      "market_data_role": "not_market_data_export_primary",
      "owner_or_source_requirement": "Use accepted forward-capture contract requirement."
    },
    {
      "contract_terminal_status": "EXISTING_SOURCE_SAFE_CAPTURE_READY",
      "fail_closed_missing_status": "SOURCE_FIELD_MISSING_FAIL_CLOSED",
      "field_closure_class": "already_source_bound_or_source_safe_projection",
      "field_family": "from_parser_schema",
      "field_name": "pending_order_mode_source_safe",
      "historical_gap_resolution": "Closed by source-safe projection, schema control, or redacted status-only rule.",
      "market_data_role": "not_market_data_export_primary",
      "owner_or_source_requirement": "Use accepted forward-capture contract requirement."
    },
    {
      "contract_terminal_status": "EXISTING_SOURCE_SAFE_CAPTURE_READY",
      "fail_closed_missing_status": "SOURCE_FIELD_MISSING_FAIL_CLOSED",
      "field_closure_class": "already_source_bound_or_source_safe_projection",
      "field_family": "from_parser_schema",
      "field_name": "pending_order_mode_status",
      "historical_gap_resolution": "Closed by source-safe projection, schema control, or redacted status-only rule.",
      "market_data_role": "not_market_data_export_primary",
      "owner_or_source_requirement": "Use accepted forward-capture contract requirement."
    },
    {
      "contract_terminal_status": "EXISTING_SOURCE_SAFE_CAPTURE_READY",
      "fail_closed_missing_status": "SOURCE_FIELD_MISSING_FAIL_CLOSED",
      "field_closure_class": "already_source_bound_or_source_safe_projection",
      "field_family": "from_parser_schema",
      "field_name": "broker_pending_order_created_status",
      "historical_gap_resolution": "Closed by source-safe projection, schema control, or redacted status-only rule.",
      "market_data_role": "not_market_data_export_primary",
      "owner_or_source_requirement": "Use accepted forward-capture contract requirement."
    },
    {
      "contract_terminal_status": "FUTURE_LOGGER_FIELD_REQUIRED",
      "fail_closed_missing_status": "SOURCE_FIELD_MISSING_FAIL_CLOSED",
      "field_closure_class": "exact_forward_capture_requirement",
      "field_family": "from_parser_schema",
      "field_name": "native_pending_order_type_source_safe",
      "historical_gap_resolution": "Cannot repair absent historical GTOS source-state unless an existing source-safe log is found; future rows must emit or fail closed under this field.",
      "market_data_role": "not_market_data_export_primary",
      "owner_or_source_requirement": "Use accepted forward-capture contract requirement."
    },
    {
      "contract_terminal_status": "FUTURE_LOGGER_FIELD_REQUIRED",
      "fail_closed_missing_status": "SOURCE_FIELD_MISSING_FAIL_CLOSED",
      "field_closure_class": "exact_forward_capture_requirement",
      "field_family": "from_parser_schema",
      "field_name": "native_pending_order_type_status",
      "historical_gap_resolution": "Cannot repair absent historical GTOS source-state unless an existing source-safe log is found; future rows must emit or fail closed under this field.",
      "market_data_role": "not_market_data_export_primary",
      "owner_or_source_requirement": "Use accepted forward-capture contract requirement."
    },
    {
      "contract_terminal_status": "FORBIDDEN_OR_REDACTED_SOURCE_ONLY",
      "fail_closed_missing_status": "FORBIDDEN_FIELD_PRESENT_FAIL_CLOSED",
      "field_closure_class": "forbidden_redacted_status_only",
      "field_family": "from_parser_schema",
      "field_name": "raw_ticket_field_present_status",
      "historical_gap_resolution": "Closed by source-safe projection, schema control, or redacted status-only rule.",
      "market_data_role": "not_market_data_export_primary",
      "owner_or_source_requirement": "Use accepted forward-capture contract requirement."
    },
    {
      "contract_terminal_status": "FORBIDDEN_OR_REDACTED_SOURCE_ONLY",
      "fail_closed_missing_status": "FORBIDDEN_FIELD_PRESENT_FAIL_CLOSED",
      "field_closure_class": "forbidden_redacted_status_only",
      "field_family": "from_parser_schema",
      "field_name": "mt5_order_ticket_redaction_status",
      "historical_gap_resolution": "Closed by source-safe projection, schema control, or redacted status-only rule.",
      "market_data_role": "not_market_data_export_primary",
      "owner_or_source_requirement": "Use accepted forward-capture contract requirement."
    },
    {
      "contract_terminal_status": "FUTURE_LOGGER_FIELD_REQUIRED",
      "fail_closed_missing_status": "QUOTE_SNAPSHOT_MISSING_FAIL_CLOSED",
      "field_closure_class": "exact_forward_capture_requirement",
      "field_family": "from_parser_schema",
      "field_name": "decision_spread_status",
      "historical_gap_resolution": "Cannot repair absent historical GTOS source-state unless an existing source-safe log is found; future rows must emit or fail closed under this field.",
      "market_data_role": "tick_or_lower_tf_export_supports_field_when_source_state_exists",
      "owner_or_source_requirement": "Use accepted forward-capture contract requirement."
    },
    {
      "contract_terminal_status": "FUTURE_LOGGER_FIELD_REQUIRED",
      "fail_closed_missing_status": "QUOTE_SNAPSHOT_MISSING_FAIL_CLOSED",
      "field_closure_class": "exact_forward_capture_requirement",
      "field_family": "from_parser_schema",
      "field_name": "decision_spread_value_source_safe",
      "historical_gap_resolution": "Cannot repair absent historical GTOS source-state unless an existing source-safe log is found; future rows must emit or fail closed under this field.",
      "market_data_role": "tick_or_lower_tf_export_supports_field_when_source_state_exists",
      "owner_or_source_requirement": "Use accepted forward-capture contract requirement."
    },
    {
      "contract_terminal_status": "FUTURE_LOGGER_FIELD_REQUIRED",
      "fail_closed_missing_status": "QUOTE_SNAPSHOT_MISSING_FAIL_CLOSED",
      "field_closure_class": "exact_forward_capture_requirement",
      "field_family": "from_parser_schema",
      "field_name": "decision_spread_unit",
      "historical_gap_resolution": "Cannot repair absent historical GTOS source-state unless an existing source-safe log is found; future rows must emit or fail closed under this field.",
      "market_data_role": "tick_or_lower_tf_export_supports_field_when_source_state_exists",
      "owner_or_source_requirement": "Use accepted forward-capture contract requirement."
    },
    {
      "contract_terminal_status": "FUTURE_LOGGER_FIELD_REQUIRED",
      "fail_closed_missing_status": "QUOTE_SNAPSHOT_MISSING_FAIL_CLOSED",
      "field_closure_class": "exact_forward_capture_requirement",
      "field_family": "from_parser_schema",
      "field_name": "entry_touch_spread_status",
      "historical_gap_resolution": "Cannot repair absent historical GTOS source-state unless an existing source-safe log is found; future rows must emit or fail closed under this field.",
      "market_data_role": "tick_or_lower_tf_export_supports_field_when_source_state_exists",
      "owner_or_source_requirement": "Use accepted forward-capture contract requirement."
    },
    {
      "contract_terminal_status": "FUTURE_LOGGER_FIELD_REQUIRED",
      "fail_closed_missing_status": "QUOTE_SNAPSHOT_MISSING_FAIL_CLOSED",
      "field_closure_class": "exact_forward_capture_requirement",
      "field_family": "from_parser_schema",
      "field_name": "entry_touch_spread_value_source_safe",
      "historical_gap_resolution": "Cannot repair absent historical GTOS source-state unless an existing source-safe log is found; future rows must emit or fail closed under this field.",
      "market_data_role": "tick_or_lower_tf_export_supports_field_when_source_state_exists",
      "owner_or_source_requirement": "Use accepted forward-capture contract requirement."
    },
    {
      "contract_terminal_status": "FUTURE_LOGGER_FIELD_REQUIRED",
      "fail_closed_missing_status": "QUOTE_SNAPSHOT_MISSING_FAIL_CLOSED",
      "field_closure_class": "exact_forward_capture_requirement",
      "field_family": "from_parser_schema",
      "field_name": "spread_source_hash",
      "historical_gap_resolution": "Cannot repair absent historical GTOS source-state unless an existing source-safe log is found; future rows must emit or fail closed under this field.",
      "market_data_role": "tick_or_lower_tf_export_supports_field_when_source_state_exists",
      "owner_or_source_requirement": "Use accepted forward-capture contract requirement."
    },
    {
      "contract_terminal_status": "FORBIDDEN_OR_REDACTED_SOURCE_ONLY",
      "fail_closed_missing_status": "FORBIDDEN_FIELD_PRESENT_FAIL_CLOSED",
      "field_closure_class": "forbidden_redacted_status_only",
      "field_family": "from_parser_schema",
      "field_name": "slippage_label_status",
      "historical_gap_resolution": "Closed by source-safe projection, schema control, or redacted status-only rule.",
      "market_data_role": "not_market_data_export_primary",
      "owner_or_source_requirement": "Use accepted forward-capture contract requirement."
    },
    {
      "contract_terminal_status": "FORBIDDEN_OR_REDACTED_SOURCE_ONLY",
      "fail_closed_missing_status": "FORBIDDEN_FIELD_PRESENT_FAIL_CLOSED",
      "field_closure_class": "forbidden_redacted_status_only",
      "field_family": "from_parser_schema",
      "field_name": "slippage_value_redaction_status",
      "historical_gap_resolution": "Closed by source-safe projection, schema control, or redacted status-only rule.",
      "market_data_role": "not_market_data_export_primary",
      "owner_or_source_requirement": "Use accepted forward-capture contract requirement."
    },
    {
      "contract_terminal_status": "FORBIDDEN_OR_REDACTED_SOURCE_ONLY",
      "fail_closed_missing_status": "FORBIDDEN_FIELD_PRESENT_FAIL_CLOSED",
      "field_closure_class": "forbidden_redacted_status_only",
      "field_family": "from_parser_schema",
      "field_name": "execution_quality_label_status",
      "historical_gap_resolution": "Closed by source-safe projection, schema control, or redacted status-only rule.",
      "market_data_role": "not_market_data_export_primary",
      "owner_or_source_requirement": "Use accepted forward-capture contract requirement."
    },
    {
      "contract_terminal_status": "FORBIDDEN_OR_REDACTED_SOURCE_ONLY",
      "fail_closed_missing_status": "FORBIDDEN_FIELD_PRESENT_FAIL_CLOSED",
      "field_closure_class": "forbidden_redacted_status_only",
      "field_family": "from_parser_schema",
      "field_name": "execution_quality_value_redaction_status",
      "historical_gap_resolution": "Closed by source-safe projection, schema control, or redacted status-only rule.",
      "market_data_role": "not_market_data_export_primary",
      "owner_or_source_requirement": "Use accepted forward-capture contract requirement."
    },
    {
      "contract_terminal_status": "FORBIDDEN_OR_REDACTED_SOURCE_ONLY",
      "fail_closed_missing_status": "FORBIDDEN_FIELD_PRESENT_FAIL_CLOSED",
      "field_closure_class": "forbidden_redacted_status_only",
      "field_family": "from_parser_schema",
      "field_name": "cost_testing_gate_status",
      "historical_gap_resolution": "Closed by source-safe projection, schema control, or redacted status-only rule.",
      "market_data_role": "not_market_data_export_primary",
      "owner_or_source_requirement": "Use accepted forward-capture contract requirement."
    },
    {
      "contract_terminal_status": "EXISTING_SOURCE_SAFE_CAPTURE_READY",
      "fail_closed_missing_status": "LIFECYCLE_PATH_SOURCE_MISSING_FAIL_CLOSED",
      "field_closure_class": "already_source_bound_or_source_safe_projection",
      "field_family": "from_parser_schema",
      "field_name": "pending_intent_created_utc",
      "historical_gap_resolution": "Closed by source-safe projection, schema control, or redacted status-only rule.",
      "market_data_role": "not_market_data_export_primary",
      "owner_or_source_requirement": "Use accepted forward-capture contract requirement."
    },
    {
      "contract_terminal_status": "FUTURE_LOGGER_FIELD_REQUIRED",
      "fail_closed_missing_status": "LIFECYCLE_PATH_SOURCE_MISSING_FAIL_CLOSED",
      "field_closure_class": "exact_forward_capture_requirement",
      "field_family": "from_parser_schema",
      "field_name": "pending_horizon_start_utc",
      "historical_gap_resolution": "Cannot repair absent historical GTOS source-state unless an existing source-safe log is found; future rows must emit or fail closed under this field.",
      "market_data_role": "not_market_data_export_primary",
      "owner_or_source_requirement": "Use accepted forward-capture contract requirement."
    },
    {
      "contract_terminal_status": "FUTURE_LOGGER_FIELD_REQUIRED",
      "fail_closed_missing_status": "LIFECYCLE_PATH_SOURCE_MISSING_FAIL_CLOSED",
      "field_closure_class": "exact_forward_capture_requirement",
      "field_family": "from_parser_schema",
      "field_name": "pending_horizon_end_utc",
      "historical_gap_resolution": "Cannot repair absent historical GTOS source-state unless an existing source-safe log is found; future rows must emit or fail closed under this field.",
      "market_data_role": "not_market_data_export_primary",
      "owner_or_source_requirement": "Use accepted forward-capture contract requirement."
    },
    {
      "contract_terminal_status": "EXISTING_SOURCE_SAFE_CAPTURE_READY",
      "fail_closed_missing_status": "LIFECYCLE_PATH_SOURCE_MISSING_FAIL_CLOSED",
      "field_closure_class": "already_source_bound_or_source_safe_projection",
      "field_family": "from_parser_schema",
      "field_name": "cancel_expiry_utc",
      "historical_gap_resolution": "Closed by source-safe projection, schema control, or redacted status-only rule.",
      "market_data_role": "not_market_data_export_primary",
      "owner_or_source_requirement": "Use accepted forward-capture contract requirement."
    },
    {
      "contract_terminal_status": "EXISTING_SOURCE_SAFE_CAPTURE_READY",
      "fail_closed_missing_status": "LIFECYCLE_PATH_SOURCE_MISSING_FAIL_CLOSED",
      "field_closure_class": "already_source_bound_or_source_safe_projection",
      "field_family": "from_parser_schema",
      "field_name": "cancel_expiry_reason_status",
      "historical_gap_resolution": "Closed by source-safe projection, schema control, or redacted status-only rule.",
      "market_data_role": "not_market_data_export_primary",
      "owner_or_source_requirement": "Use accepted forward-capture contract requirement."
    },
    {
      "contract_terminal_status": "EXISTING_SOURCE_SAFE_CAPTURE_READY",
      "fail_closed_missing_status": "LIFECYCLE_PATH_SOURCE_MISSING_FAIL_CLOSED",
      "field_closure_class": "already_source_bound_or_source_safe_projection",
      "field_family": "from_parser_schema",
      "field_name": "entry_touch_first_utc",
      "historical_gap_resolution": "Closed by source-safe projection, schema control, or redacted status-only rule.",
      "market_data_role": "not_market_data_export_primary",
      "owner_or_source_requirement": "Use accepted forward-capture contract requirement."
    },
    {
      "contract_terminal_status": "EXISTING_SOURCE_SAFE_CAPTURE_READY",
      "fail_closed_missing_status": "LIFECYCLE_PATH_SOURCE_MISSING_FAIL_CLOSED",
      "field_closure_class": "already_source_bound_or_source_safe_projection",
      "field_family": "from_parser_schema",
      "field_name": "side_aware_entry_touch_status",
      "historical_gap_resolution": "Closed by source-safe projection, schema control, or redacted status-only rule.",
      "market_data_role": "not_market_data_export_primary",
      "owner_or_source_requirement": "Use accepted forward-capture contract requirement."
    },
    {
      "contract_terminal_status": "FUTURE_LOGGER_FIELD_REQUIRED",
      "fail_closed_missing_status": "LIFECYCLE_PATH_SOURCE_MISSING_FAIL_CLOSED",
      "field_closure_class": "exact_forward_capture_requirement",
      "field_family": "from_parser_schema",
      "field_name": "terminal_area_touch_status",
      "historical_gap_resolution": "Cannot repair absent historical GTOS source-state unless an existing source-safe log is found; future rows must emit or fail closed under this field.",
      "market_data_role": "not_market_data_export_primary",
      "owner_or_source_requirement": "Use accepted forward-capture contract requirement."
    },
    {
      "contract_terminal_status": "FUTURE_LOGGER_FIELD_REQUIRED",
      "fail_closed_missing_status": "LIFECYCLE_PATH_SOURCE_MISSING_FAIL_CLOSED",
      "field_closure_class": "exact_forward_capture_requirement",
      "field_family": "from_parser_schema",
      "field_name": "terminal_area_first_touch_utc",
      "historical_gap_resolution": "Cannot repair absent historical GTOS source-state unless an existing source-safe log is found; future rows must emit or fail closed under this field.",
      "market_data_role": "not_market_data_export_primary",
      "owner_or_source_requirement": "Use accepted forward-capture contract requirement."
    },
    {
      "contract_terminal_status": "FUTURE_LOGGER_FIELD_REQUIRED",
      "fail_closed_missing_status": "LIFECYCLE_PATH_SOURCE_MISSING_FAIL_CLOSED",
      "field_closure_class": "exact_forward_capture_requirement",
      "field_family": "from_parser_schema",
      "field_name": "protective_area_touch_status",
      "historical_gap_resolution": "Cannot repair absent historical GTOS source-state unless an existing source-safe log is found; future rows must emit or fail closed under this field.",
      "market_data_role": "not_market_data_export_primary",
      "owner_or_source_requirement": "Use accepted forward-capture contract requirement."
    },
    {
      "contract_terminal_status": "FUTURE_LOGGER_FIELD_REQUIRED",
      "fail_closed_missing_status": "LIFECYCLE_PATH_SOURCE_MISSING_FAIL_CLOSED",
      "field_closure_class": "exact_forward_capture_requirement",
      "field_family": "from_parser_schema",
      "field_name": "protective_area_first_touch_utc",
      "historical_gap_resolution": "Cannot repair absent historical GTOS source-state unless an existing source-safe log is found; future rows must emit or fail closed under this field.",
      "market_data_role": "not_market_data_export_primary",
      "owner_or_source_requirement": "Use accepted forward-capture contract requirement."
    },
    {
      "contract_terminal_status": "EXISTING_SOURCE_SAFE_CAPTURE_READY",
      "fail_closed_missing_status": "EVENT_ORDER_METHOD_MISSING_FAIL_CLOSED",
      "field_closure_class": "already_source_bound_or_source_safe_projection",
      "field_family": "from_parser_schema",
      "field_name": "event_order_resolution_method",
      "historical_gap_resolution": "Closed by source-safe projection, schema control, or redacted status-only rule.",
      "market_data_role": "not_market_data_export_primary",
      "owner_or_source_requirement": "Use accepted forward-capture contract requirement."
    },
    {
      "contract_terminal_status": "EXISTING_SOURCE_SAFE_CAPTURE_READY",
      "fail_closed_missing_status": "EVENT_ORDER_METHOD_MISSING_FAIL_CLOSED",
      "field_closure_class": "already_source_bound_or_source_safe_projection",
      "field_family": "from_parser_schema",
      "field_name": "same_tick_same_bar_ambiguity_status",
      "historical_gap_resolution": "Closed by source-safe projection, schema control, or redacted status-only rule.",
      "market_data_role": "not_market_data_export_primary",
      "owner_or_source_requirement": "Use accepted forward-capture contract requirement."
    },
    {
      "contract_terminal_status": "EXISTING_SOURCE_SAFE_CAPTURE_READY",
      "fail_closed_missing_status": "LOWER_TF_COVERAGE_MISSING_FAIL_CLOSED",
      "field_closure_class": "already_source_bound_or_source_safe_projection",
      "field_family": "from_parser_schema",
      "field_name": "lower_tf_coverage_window_start_utc",
      "historical_gap_resolution": "Closed by source-safe projection, schema control, or redacted status-only rule.",
      "market_data_role": "tick_or_lower_tf_export_supports_field_when_source_state_exists",
      "owner_or_source_requirement": "Use accepted forward-capture contract requirement."
    },
    {
      "contract_terminal_status": "EXISTING_SOURCE_SAFE_CAPTURE_READY",
      "fail_closed_missing_status": "LOWER_TF_COVERAGE_MISSING_FAIL_CLOSED",
      "field_closure_class": "already_source_bound_or_source_safe_projection",
      "field_family": "from_parser_schema",
      "field_name": "lower_tf_coverage_window_end_utc",
      "historical_gap_resolution": "Closed by source-safe projection, schema control, or redacted status-only rule.",
      "market_data_role": "tick_or_lower_tf_export_supports_field_when_source_state_exists",
      "owner_or_source_requirement": "Use accepted forward-capture contract requirement."
    },
    {
      "contract_terminal_status": "EXISTING_SOURCE_SAFE_CAPTURE_READY",
      "fail_closed_missing_status": "LOWER_TF_COVERAGE_MISSING_FAIL_CLOSED",
      "field_closure_class": "already_source_bound_or_source_safe_projection",
      "field_family": "from_parser_schema",
      "field_name": "missing_coverage_intervals",
      "historical_gap_resolution": "Closed by source-safe projection, schema control, or redacted status-only rule.",
      "market_data_role": "tick_or_lower_tf_export_supports_field_when_source_state_exists",
      "owner_or_source_requirement": "Use accepted forward-capture contract requirement."
    },
    {
      "contract_terminal_status": "SCHEMA_ONLY_CONTROL_FIELD",
      "fail_closed_missing_status": "CONTROL_FIELD_MISSING_FAIL_CLOSED",
      "field_closure_class": "schema_only_control",
      "field_family": "from_parser_schema",
      "field_name": "row_level_denominator_member",
      "historical_gap_resolution": "Closed by source-safe projection, schema control, or redacted status-only rule.",
      "market_data_role": "not_market_data_export_primary",
      "owner_or_source_requirement": "Use accepted forward-capture contract requirement."
    },
    {
      "contract_terminal_status": "SCHEMA_ONLY_CONTROL_FIELD",
      "fail_closed_missing_status": "CONTROL_FIELD_MISSING_FAIL_CLOSED",
      "field_closure_class": "schema_only_control",
      "field_family": "from_parser_schema",
      "field_name": "nofill_duplicate_key_count_member",
      "historical_gap_resolution": "Closed by source-safe projection, schema control, or redacted status-only rule.",
      "market_data_role": "not_market_data_export_primary",
      "owner_or_source_requirement": "Use accepted forward-capture contract requirement."
    },
    {
      "contract_terminal_status": "SCHEMA_ONLY_CONTROL_FIELD",
      "fail_closed_missing_status": "CONTROL_FIELD_MISSING_FAIL_CLOSED",
      "field_closure_class": "schema_only_control",
      "field_family": "from_parser_schema",
      "field_name": "duplicate_group_id_count_member",
      "historical_gap_resolution": "Closed by source-safe projection, schema control, or redacted status-only rule.",
      "market_data_role": "not_market_data_export_primary",
      "owner_or_source_requirement": "Use accepted forward-capture contract requirement."
    },
    {
      "contract_terminal_status": "SCHEMA_ONLY_CONTROL_FIELD",
      "fail_closed_missing_status": "CONTROL_FIELD_MISSING_FAIL_CLOSED",
      "field_closure_class": "schema_only_control",
      "field_family": "from_parser_schema",
      "field_name": "nofill_duplicate_key_sha256",
      "historical_gap_resolution": "Closed by source-safe projection, schema control, or redacted status-only rule.",
      "market_data_role": "not_market_data_export_primary",
      "owner_or_source_requirement": "Use accepted forward-capture contract requirement."
    },
    {
      "contract_terminal_status": "SCHEMA_ONLY_CONTROL_FIELD",
      "fail_closed_missing_status": "CONTROL_FIELD_MISSING_FAIL_CLOSED",
      "field_closure_class": "schema_only_control",
      "field_family": "from_parser_schema",
      "field_name": "duplicate_group_id_sha256",
      "historical_gap_resolution": "Closed by source-safe projection, schema control, or redacted status-only rule.",
      "market_data_role": "not_market_data_export_primary",
      "owner_or_source_requirement": "Use accepted forward-capture contract requirement."
    },
    {
      "contract_terminal_status": "EXISTING_SOURCE_SAFE_CAPTURE_READY",
      "fail_closed_missing_status": "SOURCE_FIELD_MISSING_FAIL_CLOSED",
      "field_closure_class": "already_source_bound_or_source_safe_projection",
      "field_family": "from_parser_schema",
      "field_name": "session_tag",
      "historical_gap_resolution": "Closed by source-safe projection, schema control, or redacted status-only rule.",
      "market_data_role": "not_market_data_export_primary",
      "owner_or_source_requirement": "Use accepted forward-capture contract requirement."
    },
    {
      "contract_terminal_status": "EXISTING_SOURCE_SAFE_CAPTURE_READY",
      "fail_closed_missing_status": "SOURCE_FIELD_MISSING_FAIL_CLOSED",
      "field_closure_class": "already_source_bound_or_source_safe_projection",
      "field_family": "from_parser_schema",
      "field_name": "regime_context_status",
      "historical_gap_resolution": "Closed by source-safe projection, schema control, or redacted status-only rule.",
      "market_data_role": "not_market_data_export_primary",
      "owner_or_source_requirement": "Use accepted forward-capture contract requirement."
    },
    {
      "contract_terminal_status": "SCHEMA_ONLY_CONTROL_FIELD",
      "fail_closed_missing_status": "CONTROL_FIELD_MISSING_FAIL_CLOSED",
      "field_closure_class": "schema_only_control",
      "field_family": "from_parser_schema",
      "field_name": "sample_floor_policy_id",
      "historical_gap_resolution": "Closed by source-safe projection, schema control, or redacted status-only rule.",
      "market_data_role": "not_market_data_export_primary",
      "owner_or_source_requirement": "Use accepted forward-capture contract requirement."
    },
    {
      "contract_terminal_status": "SCHEMA_ONLY_CONTROL_FIELD",
      "fail_closed_missing_status": "CONTROL_FIELD_MISSING_FAIL_CLOSED",
      "field_closure_class": "schema_only_control",
      "field_family": "from_parser_schema",
      "field_name": "perturbation_ready_bucket",
      "historical_gap_resolution": "Closed by source-safe projection, schema control, or redacted status-only rule.",
      "market_data_role": "not_market_data_export_primary",
      "owner_or_source_requirement": "Use accepted forward-capture contract requirement."
    },
    {
      "contract_terminal_status": "SCHEMA_ONLY_CONTROL_FIELD",
      "fail_closed_missing_status": "CONTROL_FIELD_MISSING_FAIL_CLOSED",
      "field_closure_class": "schema_only_control",
      "field_family": "from_parser_schema",
      "field_name": "kill_switch_observability_status",
      "historical_gap_resolution": "Closed by source-safe projection, schema control, or redacted status-only rule.",
      "market_data_role": "not_market_data_export_primary",
      "owner_or_source_requirement": "Use accepted forward-capture contract requirement."
    },
    {
      "contract_terminal_status": "SCHEMA_ONLY_CONTROL_FIELD",
      "fail_closed_missing_status": "CONTROL_FIELD_MISSING_FAIL_CLOSED",
      "field_closure_class": "schema_only_control",
      "field_family": "from_parser_schema",
      "field_name": "source_artifact_hash",
      "historical_gap_resolution": "Closed by source-safe projection, schema control, or redacted status-only rule.",
      "market_data_role": "not_market_data_export_primary",
      "owner_or_source_requirement": "Use accepted forward-capture contract requirement."
    },
    {
      "contract_terminal_status": "SCHEMA_ONLY_CONTROL_FIELD",
      "fail_closed_missing_status": "CONTROL_FIELD_MISSING_FAIL_CLOSED",
      "field_closure_class": "schema_only_control",
      "field_family": "from_parser_schema",
      "field_name": "parser_code_hash",
      "historical_gap_resolution": "Closed by source-safe projection, schema control, or redacted status-only rule.",
      "market_data_role": "not_market_data_export_primary",
      "owner_or_source_requirement": "Use accepted forward-capture contract requirement."
    },
    {
      "contract_terminal_status": "SCHEMA_ONLY_CONTROL_FIELD",
      "fail_closed_missing_status": "CONTROL_FIELD_MISSING_FAIL_CLOSED",
      "field_closure_class": "schema_only_control",
      "field_family": "from_parser_schema",
      "field_name": "forbidden_field_scan_status",
      "historical_gap_resolution": "Closed by source-safe projection, schema control, or redacted status-only rule.",
      "market_data_role": "not_market_data_export_primary",
      "owner_or_source_requirement": "Use accepted forward-capture contract requirement."
    }
  ],
  "runtime_forward_capture_field_count": 55,
  "schema_version": "g12_nofill_source_state_gap_closure_and_tick_export_manifest_audit_v1",
  "target_all_fields_closed": true,
  "target_required_field_count": 55,
  "validation_safe": false
}
```
