# SCID Combined Historical Source-State Recovery Attempt Ledger

- **route_id:** `SCID_COMBINED_SOURCE_SEARCH_AND_FORWARD_CAPTURE_ROUTE`
- **evidence_class:** `SCID_COMBINED_SOURCE_SEARCH_AND_FORWARD_CAPTURE_ROUTE_ONLY`
- **promotion_verdict:** `NO_PROMOTION_VERDICT`
- **validation_safe:** `false`
- **outcome_review_opened:** `false`
- **live_effect:** `false`

```json
{
  "artifact_family": "historical_source_state_recovery_attempt_ledger",
  "candidate_rows": 3014,
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "evidence_class": "SCID_COMBINED_SOURCE_SEARCH_AND_FORWARD_CAPTURE_ROUTE_ONLY",
  "explicit_new_strategy_intent_recoveries": 0,
  "field_recovery_results": [
    {
      "candidate_rows": 3014,
      "combined_route_status": "RECOVERED_FROM_ACCEPTED_EXPLICIT_SOURCE",
      "field_family": "canonical_candidate_and_denominator",
      "rows_recovered_from_explicit_source": 3014,
      "rows_requiring_capture_contract": 0,
      "terminal_interpretation": "accepted source-control descriptor already closed"
    },
    {
      "candidate_rows": 3014,
      "combined_route_status": "RECOVERED_FROM_ACCEPTED_EXPLICIT_SOURCE",
      "field_family": "source_symbol_session_partition",
      "rows_recovered_from_explicit_source": 3014,
      "rows_requiring_capture_contract": 0,
      "terminal_interpretation": "accepted source-control descriptor already closed"
    },
    {
      "candidate_rows": 3014,
      "combined_route_status": "RECOVERED_FROM_ACCEPTED_EXPLICIT_SOURCE",
      "field_family": "source_control_coverage_not_computable_reasons",
      "rows_recovered_from_explicit_source": 3014,
      "rows_requiring_capture_contract": 0,
      "terminal_interpretation": "accepted source-control descriptor already closed"
    },
    {
      "candidate_rows": 3014,
      "combined_route_status": "NON_GENERATABLE_HISTORICAL_SOURCE_TRUTH_CAPTURE_CONTRACT_FROZEN",
      "field_family": "intended_side_direction",
      "rows_recovered_from_explicit_source": 0,
      "rows_requiring_capture_contract": 3014,
      "terminal_interpretation": "historical strategy/source-state truth is non-generatable unless explicitly logged"
    },
    {
      "candidate_rows": 3014,
      "combined_route_status": "NON_GENERATABLE_HISTORICAL_SOURCE_TRUTH_CAPTURE_CONTRACT_FROZEN",
      "field_family": "intended_entry_reference",
      "rows_recovered_from_explicit_source": 0,
      "rows_requiring_capture_contract": 3014,
      "terminal_interpretation": "historical strategy/source-state truth is non-generatable unless explicitly logged"
    },
    {
      "candidate_rows": 3014,
      "combined_route_status": "NON_GENERATABLE_HISTORICAL_SOURCE_TRUTH_CAPTURE_CONTRACT_FROZEN",
      "field_family": "intended_stop_reference",
      "rows_recovered_from_explicit_source": 0,
      "rows_requiring_capture_contract": 3014,
      "terminal_interpretation": "historical strategy/source-state truth is non-generatable unless explicitly logged"
    },
    {
      "candidate_rows": 3014,
      "combined_route_status": "NON_GENERATABLE_HISTORICAL_SOURCE_TRUTH_CAPTURE_CONTRACT_FROZEN",
      "field_family": "intended_target_reference",
      "rows_recovered_from_explicit_source": 0,
      "rows_requiring_capture_contract": 3014,
      "terminal_interpretation": "historical strategy/source-state truth is non-generatable unless explicitly logged"
    },
    {
      "candidate_rows": 3014,
      "combined_route_status": "NON_GENERATABLE_HISTORICAL_SOURCE_TRUTH_CAPTURE_CONTRACT_FROZEN",
      "field_family": "poi_type_bounds_source",
      "rows_recovered_from_explicit_source": 0,
      "rows_requiring_capture_contract": 3014,
      "terminal_interpretation": "historical strategy/source-state truth is non-generatable unless explicitly logged"
    },
    {
      "candidate_rows": 3014,
      "combined_route_status": "NON_GENERATABLE_HISTORICAL_SOURCE_TRUTH_CAPTURE_CONTRACT_FROZEN",
      "field_family": "framework_setup_family",
      "rows_recovered_from_explicit_source": 0,
      "rows_requiring_capture_contract": 3014,
      "terminal_interpretation": "historical strategy/source-state truth is non-generatable unless explicitly logged"
    },
    {
      "candidate_rows": 3014,
      "combined_route_status": "NON_GENERATABLE_HISTORICAL_SOURCE_TRUTH_CAPTURE_CONTRACT_FROZEN",
      "field_family": "lifecycle_fill_cancel_expiry_source_status",
      "rows_recovered_from_explicit_source": 0,
      "rows_requiring_capture_contract": 3014,
      "terminal_interpretation": "historical strategy/source-state truth is non-generatable unless explicitly logged"
    },
    {
      "candidate_rows": 3014,
      "combined_route_status": "RECOVERABLE_MARKET_CONTEXT_CAPTURE_CONTRACT_FROZEN",
      "field_family": "lower_timeframe_asof_path_availability",
      "rows_recovered_from_explicit_source": 0,
      "rows_requiring_capture_contract": 3014,
      "terminal_interpretation": "market/proxy context may be recoverable prospectively but is not source-attached to accepted candidates"
    },
    {
      "candidate_rows": 3014,
      "combined_route_status": "RECOVERABLE_MARKET_CONTEXT_CAPTURE_CONTRACT_FROZEN",
      "field_family": "future_orderflow_depth_proxy_requirements",
      "rows_recovered_from_explicit_source": 0,
      "rows_requiring_capture_contract": 3014,
      "terminal_interpretation": "market/proxy context may be recoverable prospectively but is not source-attached to accepted candidates"
    },
    {
      "candidate_rows": 3014,
      "combined_route_status": "CONTROL_CONTRACT_FROZEN_FROM_CLOSED_SOURCE_DESCRIPTORS",
      "field_family": "baseline_control_fields",
      "rows_recovered_from_explicit_source": 0,
      "rows_requiring_capture_contract": 3014,
      "terminal_interpretation": "baseline contract can be frozen from closed descriptors without scoring"
    },
    {
      "candidate_rows": 3014,
      "combined_route_status": "FORBIDDEN_IN_THIS_EVIDENCE_CLASS",
      "field_family": "broker_account_order_history_deal_position_evidence",
      "rows_recovered_from_explicit_source": 0,
      "rows_requiring_capture_contract": 0,
      "terminal_interpretation": "forbidden in this evidence class"
    }
  ],
  "generated_at_utc": "2026-05-12T01:06:39Z",
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
  "route_id": "SCID_COMBINED_SOURCE_SEARCH_AND_FORWARD_CAPTURE_ROUTE",
  "schema_version": "scid_combined_source_capture_route_v1",
  "validation_safe": false,
  "weak_join_policy": "timestamp/symbol-only overlaps are leads, not recovered source truth; exact candidate id or duplicate denominator binding is required"
}
```
