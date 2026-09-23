# Decision Ledger

```json
{
  "accepted_g12_control_evidence_only": true,
  "accepted_promotion": false,
  "accepted_strategy_performance": false,
  "accepted_validation_execution": false,
  "artifact_family": "decision_ledger",
  "changes_trading_risk_safety_prompt_decision_behavior": false,
  "check_map": {
    "blocked15_recomputation_and_capture_groups": true,
    "context_and_inputs": true,
    "denominator_quarantine_and_safe_flags": true,
    "prospective_contract_exactness": true,
    "recovered_row_schema_redaction": true,
    "source_search_saturation": true,
    "target_verifier_and_focused_tests": true
  },
  "credentials_touched": false,
  "decision_rationale": "The target route is accepted only as source/control evidence if all recomputed counts, source-search saturation, recovered-row schema/redaction validation, contract exactness, denominator quarantine, safe flags, and target verifier/tests pass. Recovered rows are source-state examples and do not close accepted-40 result denominators.",
  "evidence_class": "G12_SCID_FUTURE_CAPTURE_BLOCKED15_SOURCE_STATE_AUDIT_ONLY",
  "generated_at_utc": "2026-05-12T18:13:14Z",
  "live_effect": false,
  "next_g0_synthesis_prompt_required": true,
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
  "repair_prompt_required": false,
  "route_id": "G12_SCID_FUTURE_CAPTURE_BLOCKED15_SOURCE_STATE_MATERIALIZATION_AUDIT",
  "target_evidence_class": "SCID_FUTURE_CAPTURE_FIELD_SOURCE_STATE_MATERIALIZATION_ONLY",
  "target_route_id": "SCID_FUTURE_CAPTURE_FIELD_SOURCE_STATE_MATERIALIZATION_FOR_BLOCKED15",
  "terminal_blockers": [],
  "terminal_decision": "ACCEPT_AS_G12_SCID_FUTURE_CAPTURE_BLOCKED15_SOURCE_STATE_MATERIALIZATION_CONTROL_EVIDENCE_ONLY",
  "validation_safe": false,
  "verified_counts": {
    "blocked15_card_count": 15,
    "capture_group_count": 10,
    "contract_count": 10,
    "r3_quarantined_observations": 3,
    "recovered_source_state_rows": 1213,
    "upstream_quarantined_expansion_candidates": 12
  }
}
```
