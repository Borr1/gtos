# Accepted G12 Audit Reconciliation

- **route_id:** `G0_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PACKAGE_SYNTHESIS_CONTROL`
- **evidence_class:** `G0_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PACKAGE_SYNTHESIS_CONTROL_ONLY`
- **promotion_verdict:** `NO_PROMOTION_VERDICT`
- **validation_safe:** `false`
- **outcome_review_opened:** `false`
- **live_effect:** `false`

```json
{
  "accepted_g12_terminal_decision": "ACCEPT_AS_G12_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_CONTROL_EVIDENCE_ONLY",
  "accepted_upstream_g0_rank_1_route": "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE",
  "accepted_upstream_source_capture_g12_terminal_decision": "ACCEPT_AS_G12_SCID_COMBINED_SOURCE_CAPTURE_ROUTE_CONTROL_EVIDENCE_ONLY_WITH_MANIFEST_BINDING_REPAIR",
  "artifact_family": "accepted_g12_audit_reconciliation",
  "boundary_statement": "Accepted offline package is source/control evidence only. It does not validate, score, promote, or wire live capture.",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "evidence_class": "G0_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PACKAGE_SYNTHESIS_CONTROL_ONLY",
  "exact_reconciliation_checks": [
    {
      "actual": "ACCEPT_AS_G12_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_CONTROL_EVIDENCE_ONLY",
      "check_id": "accepted_g12_terminal_decision",
      "expected": "ACCEPT_AS_G12_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_CONTROL_EVIDENCE_ONLY",
      "status": "PASS"
    },
    {
      "actual": 3014,
      "check_id": "candidate_rows_coverage_expectation",
      "expected": 3014,
      "status": "PASS"
    },
    {
      "actual": 3014,
      "check_id": "duplicate_proxy_denominator_key_coverage_expectation",
      "expected": 3014,
      "status": "PASS"
    },
    {
      "actual": [
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
      "check_id": "ten_capture_groups",
      "expected": [
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
      "status": "PASS"
    },
    {
      "actual": true,
      "check_id": "schema_contract_audit_ok",
      "expected": true,
      "status": "PASS"
    },
    {
      "actual": true,
      "check_id": "fixture_validator_recomputation_ok",
      "expected": true,
      "status": "PASS"
    },
    {
      "actual": true,
      "check_id": "manifest_readonly_noleak_audit_ok",
      "expected": true,
      "status": "PASS"
    },
    {
      "actual": true,
      "check_id": "live_wiring_absent_required",
      "expected": true,
      "status": "PASS"
    },
    {
      "actual": true,
      "check_id": "verifier_ok",
      "expected": true,
      "status": "PASS"
    },
    {
      "actual": true,
      "check_id": "g12_completion_can_mark_goal_complete",
      "expected": true,
      "status": "PASS"
    }
  ],
  "generated_at_utc": "2026-05-12T04:18:03Z",
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
  "route_id": "G0_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PACKAGE_SYNTHESIS_CONTROL",
  "schema_version": "g0_scid_forward_capture_offline_schema_synthesis_v1",
  "validation_safe": false
}
```
