# Source-Field Readiness Synthesis

- **route_id:** `G0_SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_SYNTHESIS`
- **evidence_class:** `G0_SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_SYNTHESIS_CONTROL_ONLY`
- **promotion_verdict:** `NO_PROMOTION_VERDICT`
- **validation_safe:** `false`
- **outcome_review_opened:** `false`
- **live_effect:** `false`

```json
{
  "accepted_packet_row_count": 3014,
  "artifact_family": "source_field_readiness_synthesis",
  "changes_live_trading_behavior": false,
  "closed_field_families": [
    "canonical_candidate_and_denominator",
    "source_symbol_session_partition",
    "source_control_coverage_not_computable_reasons"
  ],
  "constructive_interpretation": "The packet is accepted as a precise source-control map that tells the program what to search or capture next; it is not a dead end.",
  "credentials_touched": false,
  "direction_aware_result_design_blockers": [
    "intended_side_direction",
    "intended_entry_reference",
    "intended_stop_reference",
    "intended_target_reference",
    "poi_type_bounds_source",
    "framework_setup_family",
    "lifecycle_fill_cancel_expiry_source_status"
  ],
  "evidence_class": "G0_SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_SYNTHESIS_CONTROL_ONLY",
  "fail_closed_field_families": [
    "intended_side_direction",
    "intended_entry_reference",
    "intended_stop_reference",
    "intended_target_reference",
    "poi_type_bounds_source",
    "framework_setup_family",
    "lifecycle_fill_cancel_expiry_source_status"
  ],
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
  "forbidden_field_families": [
    "broker_account_order_history_deal_position_evidence"
  ],
  "forbidden_until_new_evidence_class": [
    "broker_account_order_history_deal_position_evidence"
  ],
  "generated_at_utc": "2026-05-12T00:19:24Z",
  "live_effect": false,
  "neutral_chain_context": {
    "g0_neutral_rank_1_route": "SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET",
    "g0_neutral_terminal_decision": "ACCEPT_AS_G0_NEUTRAL_TARGET_SYNTHESIS_WITH_RANKED_NEXT_ROUTE",
    "neutral_packet_candidate_rows": 3014,
    "neutral_packet_terminal_status_count": 24112
  },
  "non_generatable_historical_truth_fields": [
    "intended_side_direction",
    "intended_entry_reference",
    "intended_stop_reference",
    "intended_target_reference",
    "poi_type_bounds_source",
    "framework_setup_family",
    "lifecycle_fill_cancel_expiry_source_status"
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
  "prospective_capture_field_families": [
    "lower_timeframe_asof_path_availability",
    "future_orderflow_depth_proxy_requirements"
  ],
  "recoverable_market_source_fields": [
    "lower_timeframe_asof_path_availability",
    "future_orderflow_depth_proxy_requirements"
  ],
  "representative_closure_row_count": 3014,
  "representative_closure_rows": [
    {
      "candidate_input_row_id": "candidate_input:EURUSD_FUTURES_6E_PROXY:2026-05-10T22:15:00.000Z",
      "decision_asof_utc": "2026-05-10T22:15:00.000Z",
      "field_statuses": {
        "broker_account_order_history_deal_position_evidence": "FORBIDDEN_IN_THIS_EVIDENCE_CLASS",
        "canonical_candidate_and_denominator": "CLOSED_FROM_SOURCE",
        "framework_setup_family": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
        "future_orderflow_depth_proxy_requirements": "PROSPECTIVE_CAPTURE_REQUIRED",
        "intended_entry_reference": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
        "intended_side_direction": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
        "intended_stop_reference": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
        "intended_target_reference": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
        "lifecycle_fill_cancel_expiry_source_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
        "lower_timeframe_asof_path_availability": "PROSPECTIVE_CAPTURE_REQUIRED",
        "poi_type_bounds_source": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
        "source_control_coverage_not_computable_reasons": "CLOSED_FROM_SOURCE",
        "source_symbol_session_partition": "CLOSED_FROM_SOURCE"
      },
      "safe_flags": {
        "live_effect": false,
        "outcome_review_opened": false,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": false
      },
      "source_proxy_group": "EURUSD_FUTURES_6E_PROXY::6EM26-CME.scid",
      "symbol": "EURUSD"
    },
    {
      "candidate_input_row_id": "candidate_input:EURUSD_FUTURES_6E_PROXY:2026-05-10T22:30:00.000Z",
      "decision_asof_utc": "2026-05-10T22:30:00.000Z",
      "field_statuses": {
        "broker_account_order_history_deal_position_evidence": "FORBIDDEN_IN_THIS_EVIDENCE_CLASS",
        "canonical_candidate_and_denominator": "CLOSED_FROM_SOURCE",
        "framework_setup_family": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
        "future_orderflow_depth_proxy_requirements": "PROSPECTIVE_CAPTURE_REQUIRED",
        "intended_entry_reference": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
        "intended_side_direction": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
        "intended_stop_reference": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
        "intended_target_reference": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
        "lifecycle_fill_cancel_expiry_source_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
        "lower_timeframe_asof_path_availability": "PROSPECTIVE_CAPTURE_REQUIRED",
        "poi_type_bounds_source": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
        "source_control_coverage_not_computable_reasons": "CLOSED_FROM_SOURCE",
        "source_symbol_session_partition": "CLOSED_FROM_SOURCE"
      },
      "safe_flags": {
        "live_effect": false,
        "outcome_review_opened": false,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": false
      },
      "source_proxy_group": "EURUSD_FUTURES_6E_PROXY::6EM26-CME.scid",
      "symbol": "EURUSD"
    },
    {
      "candidate_input_row_id": "candidate_input:EURUSD_FUTURES_6E_PROXY:2026-05-10T22:45:00.000Z",
      "decision_asof_utc": "2026-05-10T22:45:00.000Z",
      "field_statuses": {
        "broker_account_order_history_deal_position_evidence": "FORBIDDEN_IN_THIS_EVIDENCE_CLASS",
        "canonical_candidate_and_denominator": "CLOSED_FROM_SOURCE",
        "framework_setup_family": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
        "future_orderflow_depth_proxy_requirements": "PROSPECTIVE_CAPTURE_REQUIRED",
        "intended_entry_reference": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
        "intended_side_direction": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
        "intended_stop_reference": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
        "intended_target_reference": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
        "lifecycle_fill_cancel_expiry_source_status": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
        "lower_timeframe_asof_path_availability": "PROSPECTIVE_CAPTURE_REQUIRED",
        "poi_type_bounds_source": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
        "source_control_coverage_not_computable_reasons": "CLOSED_FROM_SOURCE",
        "source_symbol_session_partition": "CLOSED_FROM_SOURCE"
      },
      "safe_flags": {
        "live_effect": false,
        "outcome_review_opened": false,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": false
      },
      "source_proxy_group": "EURUSD_FUTURES_6E_PROXY::6EM26-CME.scid",
      "symbol": "EURUSD"
    }
  ],
  "result_design_ready": false,
  "route_id": "G0_SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_SYNTHESIS",
  "schema_version": "g0_scid_strategy_field_packet_synthesis_v1",
  "validation_safe": false,
  "why_result_design_not_ready": "All seven historical strategy-intent/source-state families are fail-closed for all 3,014 rows; side, entry, stop, target, POI, setup family, and lifecycle cannot be inferred from neutral price behavior."
}
```
