# Repair Ledger

```json
{
  "artifact_family": "repair_ledger",
  "changes_trading_risk_safety_prompt_decision_behavior": false,
  "credentials_touched": false,
  "evidence_class": "G12_ADV002_SOURCE_CONTROL_AUDIT_OR_SYNTHESIS_ONLY",
  "generated_at_utc": "2026-05-13T04:47:27Z",
  "live_effect": false,
  "may_open_outcomes_or_results_in_this_route": false,
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
  "post_repair_manifest_mismatch_count": 0,
  "post_repair_target_focused_tests_ok": true,
  "post_repair_target_verifier_ok": true,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "repairs": [
    {
      "action": "patched target verifier write order so verification result is written before manifest refresh",
      "class": "hash/manifest",
      "evidence": "research/science_program_2026_05/06_outcome_testing/scid_anti_boxing_r11_adv_002/SCID_ANTI_BOXING_R11_ADV_002_OUTPUT_MANIFEST_2026-05-13.json",
      "issue": "target verifier refreshed output manifest before writing the current verification result, leaving the verification-result hash stale on rerun",
      "repair_id": "ADV002-G12-REPAIR-MANIFEST-HASH-ORDER",
      "status": "CLOSED"
    },
    {
      "action": "patched target builder/verifier to set manifest self-row sha256=null with explicit self_hash_policy",
      "class": "hash/manifest",
      "evidence": "research/science_program_2026_05/06_outcome_testing/scid_anti_boxing_r11_adv_002/SCID_ANTI_BOXING_R11_ADV_002_OUTPUT_MANIFEST_2026-05-13.json",
      "issue": "target manifest attempted to carry a self-referential sha256 row",
      "repair_id": "ADV002-G12-REPAIR-MANIFEST-SELF-HASH",
      "status": "CLOSED"
    }
  ],
  "route_id": "G12_SCID_ANTI_BOXING_R11_ADV_002_SOURCE_CONTROL_AUDIT",
  "validation_safe": false
}
```
