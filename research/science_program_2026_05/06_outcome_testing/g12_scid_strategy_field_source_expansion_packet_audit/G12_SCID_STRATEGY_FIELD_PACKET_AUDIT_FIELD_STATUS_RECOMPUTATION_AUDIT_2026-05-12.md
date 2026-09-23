# Field Status Recomposition Audit

```json
{
  "artifact_family": "field_status_enum_and_closed_field_recomputation_audit",
  "changes_live_trading_behavior": false,
  "closed_field_source_paths_checked": [
    "canonical_candidate_and_denominator",
    "source_control_coverage_not_computable_reasons",
    "source_symbol_session_partition"
  ],
  "closed_source_value_mismatch_count": 0,
  "closed_source_value_mismatch_examples": [],
  "credentials_touched": false,
  "evidence_class": "G12_SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_AUDIT_ONLY",
  "expected_status_profile": {
    "broker_account_order_history_deal_position_evidence": {
      "FORBIDDEN_IN_THIS_EVIDENCE_CLASS": 3014
    },
    "canonical_candidate_and_denominator": {
      "CLOSED_FROM_SOURCE": 3014
    },
    "framework_setup_family": {
      "FAIL_CLOSED_MISSING_SOURCE_FIELD": 3014
    },
    "future_orderflow_depth_proxy_requirements": {
      "PROSPECTIVE_CAPTURE_REQUIRED": 3014
    },
    "intended_entry_reference": {
      "FAIL_CLOSED_MISSING_SOURCE_FIELD": 3014
    },
    "intended_side_direction": {
      "FAIL_CLOSED_MISSING_SOURCE_FIELD": 3014
    },
    "intended_stop_reference": {
      "FAIL_CLOSED_MISSING_SOURCE_FIELD": 3014
    },
    "intended_target_reference": {
      "FAIL_CLOSED_MISSING_SOURCE_FIELD": 3014
    },
    "lifecycle_fill_cancel_expiry_source_status": {
      "FAIL_CLOSED_MISSING_SOURCE_FIELD": 3014
    },
    "lower_timeframe_asof_path_availability": {
      "PROSPECTIVE_CAPTURE_REQUIRED": 3014
    },
    "poi_type_bounds_source": {
      "FAIL_CLOSED_MISSING_SOURCE_FIELD": 3014
    },
    "source_control_coverage_not_computable_reasons": {
      "CLOSED_FROM_SOURCE": 3014
    },
    "source_symbol_session_partition": {
      "CLOSED_FROM_SOURCE": 3014
    }
  },
  "field_families_required": [
    "canonical_candidate_and_denominator",
    "source_symbol_session_partition",
    "intended_side_direction",
    "intended_entry_reference",
    "intended_stop_reference",
    "intended_target_reference",
    "poi_type_bounds_source",
    "framework_setup_family",
    "lifecycle_fill_cancel_expiry_source_status",
    "lower_timeframe_asof_path_availability",
    "source_control_coverage_not_computable_reasons",
    "future_orderflow_depth_proxy_requirements",
    "broker_account_order_history_deal_position_evidence"
  ],
  "field_status_audit_ok": true,
  "field_status_counts_by_field": {
    "broker_account_order_history_deal_position_evidence": {
      "FORBIDDEN_IN_THIS_EVIDENCE_CLASS": 3014
    },
    "canonical_candidate_and_denominator": {
      "CLOSED_FROM_SOURCE": 3014
    },
    "framework_setup_family": {
      "FAIL_CLOSED_MISSING_SOURCE_FIELD": 3014
    },
    "future_orderflow_depth_proxy_requirements": {
      "PROSPECTIVE_CAPTURE_REQUIRED": 3014
    },
    "intended_entry_reference": {
      "FAIL_CLOSED_MISSING_SOURCE_FIELD": 3014
    },
    "intended_side_direction": {
      "FAIL_CLOSED_MISSING_SOURCE_FIELD": 3014
    },
    "intended_stop_reference": {
      "FAIL_CLOSED_MISSING_SOURCE_FIELD": 3014
    },
    "intended_target_reference": {
      "FAIL_CLOSED_MISSING_SOURCE_FIELD": 3014
    },
    "lifecycle_fill_cancel_expiry_source_status": {
      "FAIL_CLOSED_MISSING_SOURCE_FIELD": 3014
    },
    "lower_timeframe_asof_path_availability": {
      "PROSPECTIVE_CAPTURE_REQUIRED": 3014
    },
    "poi_type_bounds_source": {
      "FAIL_CLOSED_MISSING_SOURCE_FIELD": 3014
    },
    "source_control_coverage_not_computable_reasons": {
      "CLOSED_FROM_SOURCE": 3014
    },
    "source_symbol_session_partition": {
      "CLOSED_FROM_SOURCE": 3014
    }
  },
  "generated_at_utc": "2026-05-11T23:49:46Z",
  "invalid_status_examples": [],
  "invalid_status_row_count": 0,
  "live_effect": false,
  "missing_family_examples": [],
  "missing_family_row_count": 0,
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
  "route_id": "G12_SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_AUDIT",
  "row_hash_mismatch_count": 0,
  "row_hash_mismatch_examples": [],
  "schema_version": "g12_scid_strategy_field_source_expansion_packet_audit_v1",
  "status_mismatches": {},
  "valid_status_enum": [
    "CLOSED_FROM_SOURCE",
    "FAIL_CLOSED_MISSING_SOURCE_FIELD",
    "FORBIDDEN_IN_THIS_EVIDENCE_CLASS",
    "PROSPECTIVE_CAPTURE_REQUIRED"
  ],
  "validation_safe": false
}
```
