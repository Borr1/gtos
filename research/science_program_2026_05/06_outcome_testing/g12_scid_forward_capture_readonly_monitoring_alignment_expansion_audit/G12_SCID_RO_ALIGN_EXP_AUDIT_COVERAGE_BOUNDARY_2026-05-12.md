# Coverage Boundary And Group Matrix Audit

- route_id: `G12_SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION_AUDIT`
- evidence_class: `G12_SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION_AUDIT_ONLY`
- terminal_decision: `n/a`
- status: `PASS`

```json
{
  "artifact_family": "coverage_boundary_and_group_matrix_audit",
  "boundary_is_source_control_expectation_only": true,
  "candidate_rows_boundary": 3014,
  "coverage_group_count": 10,
  "coverage_groups": [
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
  "duplicate_proxy_denominator_key_boundary": 3014,
  "evidence_class": "G12_SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION_AUDIT_ONLY",
  "failures": [],
  "gate_groups": [
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
  "generated_at_utc": "2026-05-12T07:34:30Z",
  "groups_requiring_exact_additive_capture_fields": [
    "intended_target_reference",
    "poi_type_bounds_source",
    "lifecycle_fill_cancel_expiry_source_status",
    "lower_timeframe_asof_path_availability",
    "future_orderflow_depth_proxy_requirements"
  ],
  "groups_with_no_shape_coverage": [],
  "live_effect": false,
  "missing_exact_schema_fields_by_group": {
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
  "offline_schema_groups": [
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
  "opens_live_trading_behavior": false,
  "opens_paid_or_vendor_access": false,
  "opens_prompt_config_risk_safety_execution_canary_selector_edit": false,
  "opens_raw_market_data_blob_commit": false,
  "opens_result_scoring": false,
  "opens_strategy_edge_claims": false,
  "opens_validation": false,
  "outcome_review_opened": false,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "route_id": "G12_SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION_AUDIT",
  "status": "PASS",
  "status_by_group": {
    "baseline_control_fields": {
      "coverage_status": "SHAPE_COVERAGE_PRESENT_EXACT_CAPTURE_FIELDS_PRESENT_IN_INSPECTED_SHAPES",
      "existing_shape_artifact_count": 1399,
      "historical_status": "CONTROL_CONTRACT_FROZEN_FROM_CLOSED_DESCRIPTOR_FIELDS"
    },
    "framework_setup_family": {
      "coverage_status": "SHAPE_COVERAGE_PRESENT_EXACT_CAPTURE_FIELDS_PRESENT_IN_INSPECTED_SHAPES",
      "existing_shape_artifact_count": 351,
      "historical_status": "NON_GENERATABLE_HISTORICAL_SOURCE_TRUTH_CAPTURE_REQUIRED"
    },
    "future_orderflow_depth_proxy_requirements": {
      "coverage_status": "SHAPE_COVERAGE_PRESENT_EXACT_CAPTURE_FIELDS_INCOMPLETE",
      "existing_shape_artifact_count": 1867,
      "historical_status": "RECOVERABLE_OR_REQUESTABLE_MARKET_CONTEXT_WITH_PROXY_CONTRACT_CAPTURE_REQUIRED"
    },
    "intended_entry_reference": {
      "coverage_status": "SHAPE_COVERAGE_PRESENT_EXACT_CAPTURE_FIELDS_PRESENT_IN_INSPECTED_SHAPES",
      "existing_shape_artifact_count": 612,
      "historical_status": "NON_GENERATABLE_HISTORICAL_SOURCE_TRUTH_CAPTURE_REQUIRED"
    },
    "intended_side_direction": {
      "coverage_status": "SHAPE_COVERAGE_PRESENT_EXACT_CAPTURE_FIELDS_PRESENT_IN_INSPECTED_SHAPES",
      "existing_shape_artifact_count": 685,
      "historical_status": "NON_GENERATABLE_HISTORICAL_SOURCE_TRUTH_CAPTURE_REQUIRED"
    },
    "intended_stop_reference": {
      "coverage_status": "SHAPE_COVERAGE_PRESENT_EXACT_CAPTURE_FIELDS_PRESENT_IN_INSPECTED_SHAPES",
      "existing_shape_artifact_count": 458,
      "historical_status": "NON_GENERATABLE_HISTORICAL_SOURCE_TRUTH_CAPTURE_REQUIRED"
    },
    "intended_target_reference": {
      "coverage_status": "SHAPE_COVERAGE_PRESENT_EXACT_CAPTURE_FIELDS_INCOMPLETE",
      "existing_shape_artifact_count": 709,
      "historical_status": "NON_GENERATABLE_HISTORICAL_SOURCE_TRUTH_CAPTURE_REQUIRED"
    },
    "lifecycle_fill_cancel_expiry_source_status": {
      "coverage_status": "SHAPE_COVERAGE_PRESENT_EXACT_CAPTURE_FIELDS_INCOMPLETE",
      "existing_shape_artifact_count": 513,
      "historical_status": "NON_GENERATABLE_HISTORICAL_LIFECYCLE_SOURCE_TRUTH_CAPTURE_REQUIRED"
    },
    "lower_timeframe_asof_path_availability": {
      "coverage_status": "SHAPE_COVERAGE_PRESENT_EXACT_CAPTURE_FIELDS_INCOMPLETE",
      "existing_shape_artifact_count": 489,
      "historical_status": "RECOVERABLE_MARKET_CONTEXT_BUT_NOT_ATTACHED_TO_ACCEPTED_CANDIDATES_CAPTURE_REQUIRED"
    },
    "poi_type_bounds_source": {
      "coverage_status": "SHAPE_COVERAGE_PRESENT_EXACT_CAPTURE_FIELDS_INCOMPLETE",
      "existing_shape_artifact_count": 1824,
      "historical_status": "NON_GENERATABLE_HISTORICAL_STRUCTURE_SOURCE_STATE_CAPTURE_REQUIRED"
    }
  },
  "terminal_decision_from_upstream_offline_g12": "ACCEPT_AS_G12_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_CONTROL_EVIDENCE_ONLY",
  "validation_safe": false
}
```
