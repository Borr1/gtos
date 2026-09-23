# Decision Ledger

```json
{
  "acceptance_criteria": {
    "manifest_hashes_ok_after_repair": true,
    "mechanisms_present": [
      "canonical_row_ambiguity",
      "cross_card_duplication",
      "denominator_drift",
      "group_membership_instability",
      "row_hash_eol_friction",
      "session_symbol_timeframe_collision"
    ],
    "safe_flags_ok": true,
    "source_requirements_present": [
      "candidate id",
      "collision policy",
      "duplicate key",
      "group membership version",
      "source hash"
    ],
    "target_focused_tests_ok": true,
    "target_verifier_ok": true
  },
  "accepted_g12_control_evidence_only": true,
  "accepted_live_effect": false,
  "accepted_results_or_performance": false,
  "accepted_validation": false,
  "artifact_family": "decision_ledger",
  "changes_trading_risk_safety_prompt_decision_behavior": false,
  "credentials_touched": false,
  "evidence_class": "G12_ADV002_SOURCE_CONTROL_AUDIT_OR_SYNTHESIS_ONLY",
  "fairness_clause": "ADV-002 is accepted or rejected only on duplicate/collision source-control evidence. Novelty, anti-boxing framing, non-OB scope, and adversarial placebo/control purpose are not blockers.",
  "generated_at_utc": "2026-05-13T04:47:27Z",
  "live_effect": false,
  "may_open_outcomes_or_results_in_this_route": false,
  "nonblocking_future_requirements": [
    "future denominator-entry packet must bind group_membership_version and group_membership_manifest_sha256",
    "future result-opening packet must include canonical_counting_row_id before labels open",
    "future G0/result routes must reject rows with missing candidate id, duplicate key, source hash, as-of fields, or collision policy"
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
  "route_id": "G12_SCID_ANTI_BOXING_R11_ADV_002_SOURCE_CONTROL_AUDIT",
  "terminal_blockers": [],
  "terminal_decision": "ACCEPT_AS_G12_ADV002_DUPLICATE_COLLISION_SOURCE_CONTROL_DESIGN_EVIDENCE_ONLY",
  "validation_safe": false
}
```
