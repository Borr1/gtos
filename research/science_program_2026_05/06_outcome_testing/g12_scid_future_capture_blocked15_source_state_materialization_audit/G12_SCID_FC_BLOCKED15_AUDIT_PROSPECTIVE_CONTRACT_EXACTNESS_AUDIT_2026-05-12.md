# Prospective Contract Exactness Audit

```json
{
  "all_cards_remain_blocked_for_results": true,
  "artifact_family": "prospective_contract_exactness_audit",
  "changes_trading_risk_safety_prompt_decision_behavior": false,
  "contract_count": 10,
  "contract_groups": [
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
  "contract_rows": [
    {
      "accepted_40_denominator_unblocked": false,
      "fail_closed_missing_status": "SCID_FORWARD_CAPTURE_MISSING_FIELDS_FAIL_CLOSED_V1",
      "field_group": "baseline_control_fields",
      "materialization_status": "RECOVERED_SOURCE_SAFE_FORWARD_SHADOW_ROWS_PRESENT",
      "recovered_row_count": 190,
      "source_logger": "offline_baseline_control_assignment_manifest"
    },
    {
      "accepted_40_denominator_unblocked": false,
      "fail_closed_missing_status": "SCID_FORWARD_CAPTURE_MISSING_FIELDS_FAIL_CLOSED_V1",
      "field_group": "framework_setup_family",
      "materialization_status": "RECOVERED_SOURCE_SAFE_FORWARD_SHADOW_ROWS_PRESENT",
      "recovered_row_count": 190,
      "source_logger": "source_safe_strategy_decision_packet_logger"
    },
    {
      "accepted_40_denominator_unblocked": false,
      "fail_closed_missing_status": "SCID_FORWARD_CAPTURE_MISSING_FIELDS_FAIL_CLOSED_V1",
      "field_group": "future_orderflow_depth_proxy_requirements",
      "materialization_status": "ROUTED_TO_R2_LTF_ORDERFLOW_PROXY_SOURCE_STATUS_EXPANSION",
      "recovered_row_count": 0,
      "source_logger": "orderflow_depth_proxy_context_capture"
    },
    {
      "accepted_40_denominator_unblocked": false,
      "fail_closed_missing_status": "SCID_FORWARD_CAPTURE_MISSING_FIELDS_FAIL_CLOSED_V1",
      "field_group": "intended_entry_reference",
      "materialization_status": "RECOVERED_SOURCE_SAFE_FORWARD_SHADOW_ROWS_PRESENT",
      "recovered_row_count": 190,
      "source_logger": "source_safe_strategy_decision_packet_logger"
    },
    {
      "accepted_40_denominator_unblocked": false,
      "fail_closed_missing_status": "SCID_FORWARD_CAPTURE_MISSING_FIELDS_FAIL_CLOSED_V1",
      "field_group": "intended_side_direction",
      "materialization_status": "RECOVERED_SOURCE_SAFE_FORWARD_SHADOW_ROWS_PRESENT",
      "recovered_row_count": 190,
      "source_logger": "source_safe_strategy_decision_packet_logger"
    },
    {
      "accepted_40_denominator_unblocked": false,
      "fail_closed_missing_status": "SCID_FORWARD_CAPTURE_MISSING_FIELDS_FAIL_CLOSED_V1",
      "field_group": "intended_stop_reference",
      "materialization_status": "RECOVERED_SOURCE_SAFE_FORWARD_SHADOW_ROWS_PRESENT",
      "recovered_row_count": 190,
      "source_logger": "source_safe_strategy_decision_packet_logger"
    },
    {
      "accepted_40_denominator_unblocked": false,
      "fail_closed_missing_status": "SCID_FORWARD_CAPTURE_MISSING_FIELDS_FAIL_CLOSED_V1",
      "field_group": "intended_target_reference",
      "materialization_status": "RECOVERED_SOURCE_SAFE_FORWARD_SHADOW_ROWS_PRESENT",
      "recovered_row_count": 190,
      "source_logger": "source_safe_strategy_decision_packet_logger"
    },
    {
      "accepted_40_denominator_unblocked": false,
      "fail_closed_missing_status": "SCID_FORWARD_CAPTURE_MISSING_FIELDS_FAIL_CLOSED_V1",
      "field_group": "lifecycle_fill_cancel_expiry_source_status",
      "materialization_status": "RECOVERED_SOURCE_SAFE_FORWARD_SHADOW_ROWS_PRESENT",
      "recovered_row_count": 73,
      "source_logger": "nonbroker_pending_intent_lifecycle_event_logger"
    },
    {
      "accepted_40_denominator_unblocked": false,
      "fail_closed_missing_status": "SCID_FORWARD_CAPTURE_MISSING_FIELDS_FAIL_CLOSED_V1",
      "field_group": "lower_timeframe_asof_path_availability",
      "materialization_status": "ROUTED_TO_R2_LTF_ORDERFLOW_PROXY_SOURCE_STATUS_EXPANSION",
      "recovered_row_count": 0,
      "source_logger": "ltf_source_availability_and_path_descriptor_capture"
    },
    {
      "accepted_40_denominator_unblocked": false,
      "fail_closed_missing_status": "SCID_FORWARD_CAPTURE_MISSING_FIELDS_FAIL_CLOSED_V1",
      "field_group": "poi_type_bounds_source",
      "materialization_status": "NO_RECOVERABLE_STRUCTURED_SOURCE_ROWS_FOUND_FOR_ACCEPTED_40_DENOMINATOR",
      "recovered_row_count": 0,
      "source_logger": "source_safe_mso_snapshot_and_poi_logger"
    }
  ],
  "credentials_touched": false,
  "evidence_class": "G12_SCID_FUTURE_CAPTURE_BLOCKED15_SOURCE_STATE_AUDIT_ONLY",
  "failures": [],
  "generated_at_utc": "2026-05-12T18:13:11Z",
  "live_effect": false,
  "matrix_capture_group_summaries_count": 10,
  "ok": true,
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
  "required_contract_keys": [
    "source_logger",
    "as_of_clock",
    "redaction",
    "fail_closed_missing_status",
    "parser_hash_requirement",
    "owner_or_restart_gate",
    "tests_required",
    "g12_acceptance_criteria",
    "accepted_40_result_gate"
  ],
  "route_id": "G12_SCID_FUTURE_CAPTURE_BLOCKED15_SOURCE_STATE_MATERIALIZATION_AUDIT",
  "target_evidence_class": "SCID_FUTURE_CAPTURE_FIELD_SOURCE_STATE_MATERIALIZATION_ONLY",
  "target_route_id": "SCID_FUTURE_CAPTURE_FIELD_SOURCE_STATE_MATERIALIZATION_FOR_BLOCKED15",
  "unblocking_card_count": 15,
  "validation_safe": false
}
```
