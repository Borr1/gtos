# Decision Ledger

```json
{
  "accepted_g12_control_evidence_only": true,
  "accepted_promotion": false,
  "accepted_strategy_performance": false,
  "accepted_validation_execution": false,
  "artifact_family": "decision_ledger",
  "changes_live_trading_behavior": false,
  "check_results": [
    {
      "check": "row_coverage_denominator_recomputation_ok",
      "passed": true
    },
    {
      "check": "field_status_recomputation_ok",
      "passed": true
    },
    {
      "check": "source_search_saturation_ok",
      "passed": true
    },
    {
      "check": "source_hash_manifest_binding_ok_after_repair",
      "passed": true
    },
    {
      "check": "capture_contract_exactness_ok",
      "passed": true
    },
    {
      "check": "noleak_forbidden_surface_ok",
      "passed": true
    }
  ],
  "credentials_touched": false,
  "evidence_class": "G12_SCID_COMBINED_SOURCE_CAPTURE_ROUTE_AUDIT_ONLY",
  "generated_at_utc": "2026-05-12T02:04:09Z",
  "live_effect": false,
  "next_prompt_path": "research/science_program_2026_05/04_goal_prompts/G0_SCID_COMBINED_SOURCE_CAPTURE_ROUTE_SYNTHESIS_CONTROL_PROMPT_2026-05-12.md",
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
  "route_id": "G12_SCID_COMBINED_SOURCE_SEARCH_AND_FORWARD_CAPTURE_ROUTE_AUDIT",
  "schema_version": "g12_scid_combined_source_capture_route_audit_v1",
  "terminal_blockers": [],
  "terminal_decision": "ACCEPT_AS_G12_SCID_COMBINED_SOURCE_CAPTURE_ROUTE_CONTROL_EVIDENCE_ONLY_WITH_MANIFEST_BINDING_REPAIR",
  "terminal_evidence_boundary": "CONTROL_EVIDENCE_ONLY_NOT_VALIDATION_NOT_STRATEGY_PERFORMANCE",
  "terminal_repairs_applied": [
    "current G12 prompt hash rebound in source-hash audit after post-build prompt hardening",
    "builder output manifest self-hash excluded as self-referential and rebound through current audit manifest"
  ],
  "validation_safe": false
}
```
