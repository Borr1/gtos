# Parallelization Ledger

```json
{
  "artifact_family": "parallelization_ledger",
  "can_run_in_parallel_after_current_g0_acceptance": [
    "SCID_BLOCKED15_POI_BOUNDS_SOURCE_CAPTURE_CONTRACT_REPAIR",
    "SCID_BLOCKED17_LTF_ASOF_PATH_PARSER_AND_CANDIDATE_ATTACHMENT",
    "SCID_BLOCKED17_ORDERFLOW_PROXY_CONTRACT_AND_SOURCE_STATUS_ATTACH",
    "SCID_BLOCKED_BASELINE_LIFECYCLE_SOURCE_STATE_MATERIALIZATION",
    "SCID_BLOCKED_FAILURE_ANATOMY_NEGATIVE_EVIDENCE_CONTROL_PACKET",
    "SCID_BLOCKED_CROSS_DOMAIN_NON_OB_ROUTE_EXPANSION_GATE"
  ],
  "changes_trading_risk_safety_prompt_decision_behavior": false,
  "credentials_touched": false,
  "disjoint_write_scopes_for_parallel_children": {
    "BASELINE_LIFECYCLE": "baseline/lifecycle source-state fixtures",
    "CROSS_DOMAIN_EXPANSION": "quarantined expansion/anti-boxing denominator gate",
    "FAILURE_ANATOMY": "negative-evidence/source-gap control packet",
    "LTF_ASOF": "LTF parser/source-hash/as-of attachment matrix",
    "ORDERFLOW_PROXY": "proxy/source contract and access ledger",
    "POI_BOUNDS": "prospective source logger contract and synthetic fixtures"
  },
  "do_not_parallelize": [
    "Any result scoring or validation route with source-control children.",
    "Any route requiring paid/API/vendor or broker account/order/history/deal/position access."
  ],
  "evidence_class": "G0_SCID_BLOCKED_CARD_UNBLOCKING_SYNTHESIS_AFTER_G12_FUTURE_CAPTURE_SOURCE_AUDIT_ONLY",
  "generated_at_utc": "2026-05-13T01:18:09Z",
  "live_effect": false,
  "must_wait_for_child_outputs": [
    "SCID_BLOCKED32_PARALLEL_SOURCE_CONTROL_REPAIR_WAVE",
    "SCID_BLOCKED_RESULT_GATE_DORMANT_UNTIL_SOURCE_CONTROL_ACCEPTED"
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
  "requires_prior_g12_or_g0_acceptance_before_result_opening": [
    "all routes in this bundle"
  ],
  "route_id": "G0_SCID_BLOCKED_CARD_UNBLOCKING_SYNTHESIS_AFTER_G12_FUTURE_CAPTURE_SOURCE_AUDIT",
  "schema_version": "g0_scid_blocked_unblocking_synthesis_v1",
  "validation_safe": false
}
```
