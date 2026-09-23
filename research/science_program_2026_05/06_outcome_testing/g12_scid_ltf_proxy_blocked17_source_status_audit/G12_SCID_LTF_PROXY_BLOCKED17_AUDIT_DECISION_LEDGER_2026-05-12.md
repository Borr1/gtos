# Decision Ledger

```json
{
  "accepted_evidence_class_only": true,
  "artifact_family": "DECISION_LEDGER",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "decision_checks": [
    {
      "check": "denominator",
      "passed": true
    },
    {
      "check": "artifacts",
      "passed": true
    },
    {
      "check": "source_status",
      "passed": true
    },
    {
      "check": "search_inventory",
      "passed": true
    },
    {
      "check": "proxy_hash_asof",
      "passed": true
    },
    {
      "check": "noleak",
      "passed": true
    }
  ],
  "evidence_class": "G12_SCID_LTF_PROXY_BLOCKED17_SOURCE_STATUS_EXPANSION_AUDIT_ONLY",
  "fair_audit_policy": "Absence of validation/results/performance is not a blocker in this source-status lane. Blockers are limited to denominator, source, status, proxy, hash/as-of, no-leak, verifier, or forbidden-surface failures.",
  "generated_at_utc": "2026-05-12T18:00:40Z",
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
  "route_id": "G12_SCID_LTF_PROXY_BLOCKED17_SOURCE_STATUS_EXPANSION_AUDIT",
  "schema_version": "g12_scid_ltf_proxy_blocked17_source_status_audit_v1",
  "terminal_blockers": [],
  "terminal_decision": "ACCEPT_AS_G12_SCID_LTF_PROXY_BLOCKED17_SOURCE_STATUS_CONTROL_EVIDENCE_ONLY",
  "validation_safe": false
}
```
