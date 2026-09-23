# SCID Combined Source-State Join Recovery Candidate Ledger

- **route_id:** `SCID_COMBINED_SOURCE_SEARCH_AND_FORWARD_CAPTURE_ROUTE`
- **evidence_class:** `SCID_COMBINED_SOURCE_SEARCH_AND_FORWARD_CAPTURE_ROUTE_ONLY`
- **promotion_verdict:** `NO_PROMOTION_VERDICT`
- **validation_safe:** `false`
- **outcome_review_opened:** `false`
- **live_effect:** `false`

```json
{
  "artifact_family": "source_state_join_recovery_candidate_ledger",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "evidence_class": "SCID_COMBINED_SOURCE_SEARCH_AND_FORWARD_CAPTURE_ROUTE_ONLY",
  "generated_at_utc": "2026-05-12T01:06:39Z",
  "join_candidates": [
    {
      "decision": "USE_FOR_DESCRIPTOR_RECOVERY_ONLY",
      "join_key": "candidate_input_row_id and duplicate_proxy_denominator_key",
      "join_route": "accepted_strategy_field_packet_exact_candidate_id",
      "not_recovered_field_families": [
        "framework_setup_family",
        "intended_entry_reference",
        "intended_side_direction",
        "intended_stop_reference",
        "intended_target_reference",
        "lifecycle_fill_cancel_expiry_source_status",
        "poi_type_bounds_source"
      ],
      "recovered_field_families": [
        "canonical_candidate_and_denominator",
        "source_control_coverage_not_computable_reasons",
        "source_symbol_session_partition"
      ],
      "rows_with_explicit_binding": 3014
    },
    {
      "decision": "NO_RECOVERY",
      "join_key": "candidate_input_row_id or duplicate_proxy_denominator_key",
      "join_route": "shadow_logs_explicit_candidate_or_duplicate_key",
      "rows_with_explicit_binding": 0
    },
    {
      "decision": "NOT_ACCEPTED_WITHOUT_EXPLICIT_SCID_BINDING",
      "join_key": "symbol plus decision_asof_utc",
      "join_route": "shadow_logs_symbol_time_candidate_lead",
      "rows_with_explicit_binding": 0
    },
    {
      "decision": "NOT_SCID_SOURCE_STATE_AND_NO_CANDIDATE_BINDING",
      "join_key": "symbol/time/log reconstruction fields",
      "join_route": "knowledge_base_live_evaluations_or_reconstructions",
      "rows_with_explicit_binding": 0
    },
    {
      "decision": "FORBIDDEN_OR_INSUFFICIENT_FOR_STRATEGY_INTENT; MAY_SUPPORT_FUTURE_MARKET_CONTEXT_CONTRACT_ONLY",
      "join_key": "market timestamp/source file",
      "join_route": "raw_scid_or_market_blob_reparse",
      "rows_with_explicit_binding": 0
    },
    {
      "decision": "NO_EXPLICIT_SOURCE_STATE_MATCH_FOUND",
      "join_key": "candidate ids, duplicate keys, source candidate ids",
      "join_route": "prior_worktree_cache_roots",
      "rows_with_explicit_binding": 0
    }
  ],
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
  "row_level_status_path": "research/science_program_2026_05/06_outcome_testing/scid_combined_source_search_and_forward_capture_route/SCID_COMBINED_SOURCE_CAPTURE_CANDIDATE_SOURCE_CAPTURE_STATUS_2026-05-12.jsonl",
  "schema_version": "scid_combined_source_capture_route_v1",
  "validation_safe": false
}
```
