# Recovered Row Schema Redaction Audit

```json
{
  "accepted_40_result_denominator_closure_from_recovered_rows": false,
  "artifact_family": "recovered_row_schema_redaction_audit",
  "asof_failure_count": 0,
  "changes_trading_risk_safety_prompt_decision_behavior": false,
  "counts_by_group": {
    "baseline_control_fields": 190,
    "framework_setup_family": 190,
    "intended_entry_reference": 190,
    "intended_side_direction": 190,
    "intended_stop_reference": 190,
    "intended_target_reference": 190,
    "lifecycle_fill_cancel_expiry_source_status": 73
  },
  "credentials_touched": false,
  "evidence_class": "G12_SCID_FUTURE_CAPTURE_BLOCKED15_SOURCE_STATE_AUDIT_ONLY",
  "failures": [],
  "forbidden_row_key_hits": [],
  "generated_at_utc": "2026-05-12T18:13:11Z",
  "live_effect": false,
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
  "recovered_row_count": 1213,
  "route_id": "G12_SCID_FUTURE_CAPTURE_BLOCKED15_SOURCE_STATE_MATERIALIZATION_AUDIT",
  "rows_are_source_state_examples_only": true,
  "sample_source_identifiers": [
    "shadow_logs/pending_limit_lifecycle_audit.jsonl#L1",
    "shadow_logs/pending_limit_lifecycle_audit.jsonl#L10",
    "shadow_logs/pending_limit_lifecycle_audit.jsonl#L11",
    "shadow_logs/pending_limit_lifecycle_audit.jsonl#L12",
    "shadow_logs/pending_limit_lifecycle_audit.jsonl#L13",
    "shadow_logs/pending_limit_lifecycle_audit.jsonl#L14",
    "shadow_logs/pending_limit_lifecycle_audit.jsonl#L15",
    "shadow_logs/pending_limit_lifecycle_audit.jsonl#L16",
    "shadow_logs/pending_limit_lifecycle_audit.jsonl#L17",
    "shadow_logs/pending_limit_lifecycle_audit.jsonl#L18"
  ],
  "schema_versions": {
    "scid_forward_source_capture_v1": 1213
  },
  "target_evidence_class": "SCID_FUTURE_CAPTURE_FIELD_SOURCE_STATE_MATERIALIZATION_ONLY",
  "target_route_id": "SCID_FUTURE_CAPTURE_FIELD_SOURCE_STATE_MATERIALIZATION_FOR_BLOCKED15",
  "unique_source_hash_count": 977,
  "validation_safe": false,
  "validator_failure_count": 0,
  "validator_used": "src.research_infra.forward_capture.validate_scid_forward_source_capture_row"
}
```
