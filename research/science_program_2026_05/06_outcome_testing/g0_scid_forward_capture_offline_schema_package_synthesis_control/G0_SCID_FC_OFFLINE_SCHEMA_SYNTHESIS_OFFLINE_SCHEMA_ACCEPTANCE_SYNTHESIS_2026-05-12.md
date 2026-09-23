# Offline Schema Acceptance Synthesis

- **route_id:** `G0_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PACKAGE_SYNTHESIS_CONTROL`
- **evidence_class:** `G0_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PACKAGE_SYNTHESIS_CONTROL_ONLY`
- **promotion_verdict:** `NO_PROMOTION_VERDICT`
- **validation_safe:** `false`
- **outcome_review_opened:** `false`
- **live_effect:** `false`

```json
{
  "accepted_capture_groups": [
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
  "accepted_package_boundary": "OFFLINE_SCHEMA_PARSER_FIXTURE_VALIDATOR_READONLY_ALIGNMENT_ONLY",
  "artifact_family": "offline_schema_acceptance_synthesis",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "evidence_class": "G0_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PACKAGE_SYNTHESIS_CONTROL_ONLY",
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
  "generated_at_utc": "2026-05-12T04:18:03Z",
  "invalid_fixture_fail_closed_count": 13,
  "live_effect": false,
  "live_wiring_absence_required_boundary": true,
  "live_wiring_added": false,
  "non_result_denominator_boundary": {
    "candidate_input_row_ids": 3014,
    "duplicate_proxy_denominator_keys": 3014,
    "use": "source/control coverage expectation only, not result denominator"
  },
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
  "parser_contract_keys": [
    "candidate_key_policy",
    "duplicate_policy",
    "fail_closed_policy",
    "input_format",
    "schema_version_check",
    "source_hash_policy"
  ],
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "read_only_alignment_target_count": 12,
  "redaction_policy_id": "SCID_FORWARD_CAPTURE_NO_BROKER_ACCOUNT_ORDER_DEAL_POSITION_IDS_V1",
  "route_id": "G0_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PACKAGE_SYNTHESIS_CONTROL",
  "schema_file_count": 11,
  "schema_version": "g0_scid_forward_capture_offline_schema_synthesis_v1",
  "terminal_decision": "ACCEPT_AS_G12_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_CONTROL_EVIDENCE_ONLY",
  "valid_fixture_pass_count": 5,
  "validation_safe": false
}
```
