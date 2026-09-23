# Decision Ledger

```json
{
  "accepted_evidence_class_only": true,
  "artifact_family": "DECISION_LEDGER",
  "broker_native_cfd_truth_claims": 0,
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "decision_checks": [
    {
      "check": "denominator",
      "ok": true
    },
    {
      "check": "artifact_hash",
      "ok": true
    },
    {
      "check": "source_family",
      "ok": true
    },
    {
      "check": "equivalence",
      "ok": true
    },
    {
      "check": "blocker",
      "ok": true
    },
    {
      "check": "noleak",
      "ok": true
    }
  ],
  "eol_equivalence_summary": {
    "strict_failure_count": 0,
    "text_eol_equivalent_row_count": 5
  },
  "evidence_class": "G12_SCID_BLOCKED17_ORDERFLOW_PROXY_CONTRACT_AUDIT_ONLY",
  "fair_audit_policy": "Context-only proxy evidence is acceptable when contract-bound and non-equivalent. Rejection is limited to exact source-family, equivalence, as-of, hash, redaction, no-leak, verifier, or manifest failures.",
  "generated_at_utc": "2026-05-13T04:50:06Z",
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
  "route_id": "G12_SCID_BLOCKED17_ORDERFLOW_PROXY_CONTRACT_AUDIT",
  "same_g12_repair_summary": [
    {
      "current_sha256": "4affec0b8cabf9bd28698295d6fa5e081853fb0600372390ffdac2694e9f5cb4",
      "current_size_bytes": 4528,
      "old_manifest_sha256": "f68bd35ebcac1bf606dea114f3ba3353acf853e45306e1e1aa4aa0382374df91",
      "old_manifest_size_bytes": 3155,
      "path": "research/science_program_2026_05/04_goal_prompts/G12_SCID_BLOCKED17_ORDERFLOW_PROXY_CONTRACT_AUDIT_GOAL_PROMPT_2026-05-13.md",
      "repair_status": "CLOSED_IN_G12_AUDIT_REHASH_PROJECTION"
    }
  ],
  "schema_version": "g12_scid_blocked17_orderflow_proxy_contract_audit_v1",
  "terminal_blockers": [],
  "terminal_decision": "ACCEPT_AS_G12_SCID_BLOCKED17_ORDERFLOW_PROXY_CONTRACT_CONTROL_EVIDENCE_ONLY_WITH_PROMPT_MANIFEST_REPAIR",
  "validation_safe": false
}
```
