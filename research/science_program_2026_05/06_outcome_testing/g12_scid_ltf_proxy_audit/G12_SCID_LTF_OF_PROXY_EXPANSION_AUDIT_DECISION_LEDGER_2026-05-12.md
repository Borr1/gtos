# Decision Ledger

```json
{
  "accepted_evidence_class_only": true,
  "artifact_family": "decision_ledger",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "decision_checks": [
    {
      "check": "candidate_boundary_capture_groups_ok",
      "passed": true
    },
    {
      "check": "source_inventory_hash_deferral_ok",
      "passed": true
    },
    {
      "check": "acquisition_ladder_saturation_ok",
      "passed": true
    },
    {
      "check": "coverage_matrices_ok",
      "passed": true
    },
    {
      "check": "proxy_validity_approval_asof_ok",
      "passed": true
    },
    {
      "check": "noleak_forbidden_surface_ok",
      "passed": true
    }
  ],
  "evidence_class": "G12_SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_AUDIT_ONLY",
  "fair_audit_policy": "No blocker was created for absence of performance validation, R/PnL/win-rate, OB-only conclusion, or correctly labeled proxy/context evidence. Blockers are limited to exact recomputation, source, hash, label, no-leak, scoped-diff, verifier, or evidence-class failures.",
  "generated_at_utc": "2026-05-12T07:45:57Z",
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
  "route_id": "G12_SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_AUDIT",
  "schema_version": "g12_scid_ltf_orderflow_proxy_source_expansion_audit_v1",
  "terminal_blockers": [],
  "terminal_decision": "ACCEPT_AS_G12_SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_CONTROL_EVIDENCE_ONLY",
  "validation_safe": false
}
```
