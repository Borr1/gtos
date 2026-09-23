# Accepted G12/G0 Handoff Reconciliation

- **route_id:** `SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE`
- **evidence_class:** `SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_ONLY`
- **promotion_verdict:** `NO_PROMOTION_VERDICT`
- **validation_safe:** `false`
- **outcome_review_opened:** `false`
- **live_effect:** `false`

```json
{
  "accepted_g0_terminal_decision": "ACCEPT_AS_G0_SCID_COMBINED_SOURCE_CAPTURE_SYNTHESIS_WITH_RANKED_ROUTE_BUNDLE",
  "accepted_g12_terminal_decision": "ACCEPT_AS_G12_SCID_COMBINED_SOURCE_CAPTURE_ROUTE_CONTROL_EVIDENCE_ONLY_WITH_MANIFEST_BINDING_REPAIR",
  "artifact_family": "accepted_g12_g0_handoff_reconciliation",
  "candidate_rows": 3014,
  "changes_live_trading_behavior": false,
  "control_boundary": "control evidence only; no validation, result scoring, performance, or live behavior",
  "credentials_touched": false,
  "evidence_class": "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_ONLY",
  "generated_at_utc": "2026-05-12T03:20:54Z",
  "live_effect": false,
  "manifest_binding_repair_carried_forward": true,
  "observed_capture_groups": [
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
  "required_capture_groups": [
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
  "route_id": "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE",
  "schema_version": "scid_forward_capture_offline_schema_package_v1",
  "strategy_field_fail_closed_families": [
    "intended_side_direction",
    "intended_entry_reference",
    "intended_stop_reference",
    "intended_target_reference",
    "poi_type_bounds_source",
    "framework_setup_family",
    "lifecycle_fill_cancel_expiry_source_status"
  ],
  "strategy_field_prospective_capture_families": [
    "lower_timeframe_asof_path_availability",
    "future_orderflow_depth_proxy_requirements"
  ],
  "unique_candidate_input_row_ids": 3014,
  "unique_duplicate_proxy_denominator_keys": 3014,
  "validation_safe": false
}
```
