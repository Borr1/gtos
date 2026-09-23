# Fixture Manifest

- **route_id:** `SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE`
- **evidence_class:** `SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_ONLY`
- **promotion_verdict:** `NO_PROMOTION_VERDICT`
- **validation_safe:** `false`
- **outcome_review_opened:** `false`
- **live_effect:** `false`

```json
{
  "artifact_family": "fixture_manifest",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "evidence_class": "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_ONLY",
  "field_groups_with_missing_fixture": [
    "baseline_control_fields",
    "framework_setup_family",
    "future_orderflow_depth_proxy_requirements",
    "intended_entry_reference",
    "intended_side_direction",
    "intended_stop_reference",
    "intended_target_reference",
    "lifecycle_fill_cancel_expiry_source_status",
    "lower_timeframe_asof_path_availability",
    "poi_type_bounds_source"
  ],
  "fixture_count": 18,
  "fixtures": [
    {
      "category": "valid_pass",
      "expected_valid": true,
      "fixture_id": "fully_populated_synthetic_source_safe_rowset",
      "path": "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/fixtures/fully_populated_synthetic_source_safe_rowset.jsonl"
    },
    {
      "category": "missing_field_fail_closed",
      "expected_valid": false,
      "field_group": "intended_side_direction",
      "fixture_id": "missing_required_intended_side_direction",
      "missing_field": "strategy_side_enum_LONG_SHORT_NEUTRAL_NO_STRATEGY",
      "path": "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/fixtures/missing_required_intended_side_direction.json"
    },
    {
      "category": "missing_field_fail_closed",
      "expected_valid": false,
      "field_group": "intended_entry_reference",
      "fixture_id": "missing_required_intended_entry_reference",
      "missing_field": "entry_reference_type_market_limit_zone_midpoint_other",
      "path": "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/fixtures/missing_required_intended_entry_reference.json"
    },
    {
      "category": "missing_field_fail_closed",
      "expected_valid": false,
      "field_group": "intended_stop_reference",
      "fixture_id": "missing_required_intended_stop_reference",
      "missing_field": "stop_reference_price",
      "path": "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/fixtures/missing_required_intended_stop_reference.json"
    },
    {
      "category": "missing_field_fail_closed",
      "expected_valid": false,
      "field_group": "intended_target_reference",
      "fixture_id": "missing_required_intended_target_reference",
      "missing_field": "target_reference_price",
      "path": "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/fixtures/missing_required_intended_target_reference.json"
    },
    {
      "category": "missing_field_fail_closed",
      "expected_valid": false,
      "field_group": "poi_type_bounds_source",
      "fixture_id": "missing_required_poi_type_bounds_source",
      "missing_field": "poi_type_enum_ob_fvg_breaker_swing_other_none",
      "path": "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/fixtures/missing_required_poi_type_bounds_source.json"
    },
    {
      "category": "missing_field_fail_closed",
      "expected_valid": false,
      "field_group": "framework_setup_family",
      "fixture_id": "missing_required_framework_setup_family",
      "missing_field": "frameworks_evaluated",
      "path": "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/fixtures/missing_required_framework_setup_family.json"
    },
    {
      "category": "missing_field_fail_closed",
      "expected_valid": false,
      "field_group": "lifecycle_fill_cancel_expiry_source_status",
      "fixture_id": "missing_required_lifecycle_fill_cancel_expiry_source_status",
      "missing_field": "pending_intent_id",
      "path": "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/fixtures/missing_required_lifecycle_fill_cancel_expiry_source_status.json"
    },
    {
      "category": "missing_field_fail_closed",
      "expected_valid": false,
      "field_group": "lower_timeframe_asof_path_availability",
      "fixture_id": "missing_required_lower_timeframe_asof_path_availability",
      "missing_field": "ltf_timeframes_available",
      "path": "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/fixtures/missing_required_lower_timeframe_asof_path_availability.json"
    },
    {
      "category": "missing_field_fail_closed",
      "expected_valid": false,
      "field_group": "future_orderflow_depth_proxy_requirements",
      "fixture_id": "missing_required_future_orderflow_depth_proxy_requirements",
      "missing_field": "proxy_instrument",
      "path": "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/fixtures/missing_required_future_orderflow_depth_proxy_requirements.json"
    },
    {
      "category": "missing_field_fail_closed",
      "expected_valid": false,
      "field_group": "baseline_control_fields",
      "fixture_id": "missing_required_baseline_control_fields",
      "missing_field": "partition_assignment",
      "path": "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/fixtures/missing_required_baseline_control_fields.json"
    },
    {
      "category": "ltf_unavailable",
      "expected_valid": true,
      "fixture_id": "ltf_unavailable_fail_closed_valid",
      "path": "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/fixtures/ltf_unavailable_fail_closed_valid.json"
    },
    {
      "category": "orderflow_proxy_unavailable",
      "expected_valid": true,
      "fixture_id": "orderflow_proxy_unavailable_fail_closed_valid",
      "path": "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/fixtures/orderflow_proxy_unavailable_fail_closed_valid.json"
    },
    {
      "category": "forbidden_broker_identifier",
      "expected_valid": false,
      "fixture_id": "forbidden_broker_identifier_fail_closed",
      "path": "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/fixtures/forbidden_broker_identifier_fail_closed.json"
    },
    {
      "category": "stale_asof_violation",
      "expected_valid": false,
      "fixture_id": "stale_asof_violation_fail_closed",
      "path": "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/fixtures/stale_asof_violation_fail_closed.json"
    },
    {
      "category": "duplicate_denominator_consistency",
      "expected_valid": true,
      "fixture_id": "duplicate_denominator_consistency_valid",
      "path": "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/fixtures/duplicate_denominator_consistency_valid.jsonl"
    },
    {
      "category": "duplicate_denominator_consistency",
      "expected_valid": false,
      "fixture_id": "duplicate_denominator_mismatch_fail_closed",
      "path": "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/fixtures/duplicate_denominator_mismatch_fail_closed.jsonl"
    },
    {
      "category": "manifest_binding_repair_continuity",
      "expected_valid": true,
      "fixture_id": "manifest_binding_repair_continuity",
      "path": "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/fixtures/manifest_binding_repair_continuity.json"
    }
  ],
  "generated_at_utc": "2026-05-12T03:20:54Z",
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
  "required_fixture_categories": [
    "valid_pass",
    "missing_field_fail_closed",
    "ltf_unavailable",
    "orderflow_proxy_unavailable",
    "forbidden_broker_identifier",
    "stale_asof_violation",
    "duplicate_denominator_consistency",
    "manifest_binding_repair_continuity"
  ],
  "route_id": "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE",
  "schema_version": "scid_forward_capture_offline_schema_package_v1",
  "validation_safe": false
}
```
