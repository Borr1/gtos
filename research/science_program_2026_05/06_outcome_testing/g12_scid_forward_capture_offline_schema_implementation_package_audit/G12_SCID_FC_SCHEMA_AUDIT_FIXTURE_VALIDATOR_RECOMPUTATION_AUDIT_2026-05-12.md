# Fixture Validator Recompution Audit

```json
{
  "artifact_family": "fixture_validator_recomputation_audit",
  "builder_fixture_ledger_ok": true,
  "builder_invalid_fixture_fail_closed_count": 13,
  "builder_valid_fixture_pass_count": 5,
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "evidence_class": "G12_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_AUDIT_ONLY",
  "fixture_categories": [
    "duplicate_denominator_consistency",
    "forbidden_broker_identifier",
    "ltf_unavailable",
    "manifest_binding_repair_continuity",
    "missing_field_fail_closed",
    "orderflow_proxy_unavailable",
    "stale_asof_violation",
    "valid_pass"
  ],
  "fixture_count": 18,
  "fixture_validator_failures": [],
  "fixture_validator_recomputation_ok": true,
  "generated_at_utc": "2026-05-12T03:53:19Z",
  "independent_fixture_results": [
    {
      "category": "valid_pass",
      "errors": [],
      "expected_valid": true,
      "fixture_id": "fully_populated_synthetic_source_safe_rowset",
      "observed_valid": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/fixtures/fully_populated_synthetic_source_safe_rowset.jsonl"
    },
    {
      "category": "missing_field_fail_closed",
      "errors": [
        "missing_required:strategy_side_enum_LONG_SHORT_NEUTRAL_NO_STRATEGY"
      ],
      "expected_valid": false,
      "fixture_id": "missing_required_intended_side_direction",
      "observed_valid": false,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/fixtures/missing_required_intended_side_direction.json"
    },
    {
      "category": "missing_field_fail_closed",
      "errors": [
        "missing_required:entry_reference_type_market_limit_zone_midpoint_other"
      ],
      "expected_valid": false,
      "fixture_id": "missing_required_intended_entry_reference",
      "observed_valid": false,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/fixtures/missing_required_intended_entry_reference.json"
    },
    {
      "category": "missing_field_fail_closed",
      "errors": [
        "missing_required:stop_reference_price"
      ],
      "expected_valid": false,
      "fixture_id": "missing_required_intended_stop_reference",
      "observed_valid": false,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/fixtures/missing_required_intended_stop_reference.json"
    },
    {
      "category": "missing_field_fail_closed",
      "errors": [
        "missing_required:target_reference_price"
      ],
      "expected_valid": false,
      "fixture_id": "missing_required_intended_target_reference",
      "observed_valid": false,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/fixtures/missing_required_intended_target_reference.json"
    },
    {
      "category": "missing_field_fail_closed",
      "errors": [
        "missing_required:poi_type_enum_ob_fvg_breaker_swing_other_none"
      ],
      "expected_valid": false,
      "fixture_id": "missing_required_poi_type_bounds_source",
      "observed_valid": false,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/fixtures/missing_required_poi_type_bounds_source.json"
    },
    {
      "category": "missing_field_fail_closed",
      "errors": [
        "missing_required:frameworks_evaluated"
      ],
      "expected_valid": false,
      "fixture_id": "missing_required_framework_setup_family",
      "observed_valid": false,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/fixtures/missing_required_framework_setup_family.json"
    },
    {
      "category": "missing_field_fail_closed",
      "errors": [
        "missing_required:pending_intent_id"
      ],
      "expected_valid": false,
      "fixture_id": "missing_required_lifecycle_fill_cancel_expiry_source_status",
      "observed_valid": false,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/fixtures/missing_required_lifecycle_fill_cancel_expiry_source_status.json"
    },
    {
      "category": "missing_field_fail_closed",
      "errors": [
        "missing_required:ltf_timeframes_available"
      ],
      "expected_valid": false,
      "fixture_id": "missing_required_lower_timeframe_asof_path_availability",
      "observed_valid": false,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/fixtures/missing_required_lower_timeframe_asof_path_availability.json"
    },
    {
      "category": "missing_field_fail_closed",
      "errors": [
        "missing_required:proxy_instrument"
      ],
      "expected_valid": false,
      "fixture_id": "missing_required_future_orderflow_depth_proxy_requirements",
      "observed_valid": false,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/fixtures/missing_required_future_orderflow_depth_proxy_requirements.json"
    },
    {
      "category": "missing_field_fail_closed",
      "errors": [
        "missing_required:partition_assignment"
      ],
      "expected_valid": false,
      "fixture_id": "missing_required_baseline_control_fields",
      "observed_valid": false,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/fixtures/missing_required_baseline_control_fields.json"
    },
    {
      "category": "ltf_unavailable",
      "errors": [],
      "expected_valid": true,
      "fixture_id": "ltf_unavailable_fail_closed_valid",
      "observed_valid": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/fixtures/ltf_unavailable_fail_closed_valid.json"
    },
    {
      "category": "orderflow_proxy_unavailable",
      "errors": [],
      "expected_valid": true,
      "fixture_id": "orderflow_proxy_unavailable_fail_closed_valid",
      "observed_valid": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/fixtures/orderflow_proxy_unavailable_fail_closed_valid.json"
    },
    {
      "category": "forbidden_broker_identifier",
      "errors": [
        "unexpected_key:mt5_order_ticket",
        "forbidden_key:mt5_order_ticket",
        "forbidden_value_marker:09"
      ],
      "expected_valid": false,
      "fixture_id": "forbidden_broker_identifier_fail_closed",
      "observed_valid": false,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/fixtures/forbidden_broker_identifier_fail_closed.json"
    },
    {
      "category": "stale_asof_violation",
      "errors": [
        "asof_violation:source_observed_after_decision"
      ],
      "expected_valid": false,
      "fixture_id": "stale_asof_violation_fail_closed",
      "observed_valid": false,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/fixtures/stale_asof_violation_fail_closed.json"
    },
    {
      "category": "duplicate_denominator_consistency",
      "errors": [],
      "expected_valid": true,
      "fixture_id": "duplicate_denominator_consistency_valid",
      "observed_valid": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/fixtures/duplicate_denominator_consistency_valid.jsonl"
    },
    {
      "category": "duplicate_denominator_consistency",
      "errors": [
        "duplicate_key_mismatch:synthetic_candidate_input:DUPLICATE_MISMATCH:2026-05-12T11:00:00Z"
      ],
      "expected_valid": false,
      "fixture_id": "duplicate_denominator_mismatch_fail_closed",
      "observed_valid": false,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/fixtures/duplicate_denominator_mismatch_fail_closed.jsonl"
    },
    {
      "category": "manifest_binding_repair_continuity",
      "errors": [],
      "expected_valid": true,
      "fixture_id": "manifest_binding_repair_continuity",
      "observed_valid": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/fixtures/manifest_binding_repair_continuity.json"
    }
  ],
  "input_route_id": "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE",
  "invalid_fixture_fail_closed_count": 13,
  "live_effect": false,
  "opens_ai_api": false,
  "opens_broker_account_order_history_deal_position_evidence": false,
  "opens_live_restart": false,
  "opens_live_trading_behavior": false,
  "opens_paid_or_vendor_access": false,
  "opens_prompt_config_risk_safety_execution_canary_selector_edit": false,
  "opens_raw_market_data_blob_commit": false,
  "opens_registry_edit": false,
  "opens_remote_push": false,
  "opens_result_scoring": false,
  "opens_strategy_edge_claims": false,
  "opens_validation": false,
  "outcome_review_opened": false,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "route_id": "G12_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_AUDIT",
  "valid_fixture_pass_count": 5,
  "validation_safe": false
}
```
