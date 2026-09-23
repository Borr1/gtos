# Capture Requirement And Source Saturation Audit

- route_id: `G12_SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION_AUDIT`
- evidence_class: `G12_SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION_AUDIT_ONLY`
- terminal_decision: `n/a`
- status: `PASS`

```json
{
  "artifact_family": "capture_requirement_and_source_saturation_audit",
  "capture_requirements_include_required_controls": true,
  "capture_requirements_name_every_missing_field": true,
  "evidence_class": "G12_SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION_AUDIT_ONLY",
  "failures": [],
  "gate_row_count": 10,
  "generated_at_utc": "2026-05-12T07:34:32Z",
  "historical_truth_inference_allowed_rows": [],
  "live_effect": false,
  "missing_exact_fields_by_group": {
    "future_orderflow_depth_proxy_requirements": [
      "derived_feature_schema_version",
      "publication_or_capture_asof_utc",
      "source_file_pointer_or_vendor_cache_id"
    ],
    "intended_target_reference": [
      "risk_reward_reference"
    ],
    "lifecycle_fill_cancel_expiry_source_status": [
      "redacted_order_bridge_hash_optional",
      "source_event_clock_basis",
      "source_event_utc"
    ],
    "lower_timeframe_asof_path_availability": [
      "asof_path_descriptor_version",
      "decision_minus_window_start_utc"
    ],
    "poi_type_bounds_source": [
      "mso_snapshot_hash"
    ]
  },
  "missing_producer_field_group_count": 5,
  "opens_ai_api": false,
  "opens_broker_account_order_history_deal_position_evidence": false,
  "opens_live_trading_behavior": false,
  "opens_paid_or_vendor_access": false,
  "opens_prompt_config_risk_safety_execution_canary_selector_edit": false,
  "opens_raw_market_data_blob_commit": false,
  "opens_result_scoring": false,
  "opens_strategy_edge_claims": false,
  "opens_validation": false,
  "outcome_review_opened": false,
  "producer_files_modified": [],
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "route_id": "G12_SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION_AUDIT",
  "source_saturation_summary": {
    "external_or_prior_local_roots_searched": 12,
    "first_twelve_alignment_target_boundary_exceeded_by": 2539,
    "groups_with_no_shape_coverage": [],
    "parsed_shape_artifact_count": 2551,
    "same_evidence_class_gaps_remaining": [],
    "searched_root_count": 18
  },
  "status": "PASS",
  "validation_safe": false
}
```
