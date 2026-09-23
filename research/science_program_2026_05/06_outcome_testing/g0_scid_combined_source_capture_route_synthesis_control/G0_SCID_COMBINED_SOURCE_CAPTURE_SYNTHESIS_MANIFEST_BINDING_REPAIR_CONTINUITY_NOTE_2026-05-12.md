# Manifest-Binding Repair Continuity Note

- **route_id:** `G0_SCID_COMBINED_SOURCE_CAPTURE_ROUTE_SYNTHESIS_CONTROL`
- **evidence_class:** `G0_SCID_COMBINED_SOURCE_CAPTURE_ROUTE_SYNTHESIS_CONTROL_ONLY`
- **promotion_verdict:** `NO_PROMOTION_VERDICT`
- **validation_safe:** `false`
- **outcome_review_opened:** `false`
- **live_effect:** `false`

```json
{
  "accepted_repair": "The G12 prompt was intentionally hardened after the builder route and is rebound here to its current hash. The builder manifest self-hash is self-referential and is not used as a blocking source binding. All other artifact/input hash mismatches are blockers.",
  "artifact_family": "manifest_binding_repair_continuity_note",
  "blocking_unrepaired_hash_mismatches": [],
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "evidence_class": "G0_SCID_COMBINED_SOURCE_CAPTURE_ROUTE_SYNTHESIS_CONTROL_ONLY",
  "future_verifier_policy": [
    "The current G12 prompt hash supersedes the stale pre-hardening prompt hash.",
    "The builder output manifest self-hash remains non-blocking because it is self-referential: SELF_REFERENTIAL_MANIFEST_HASH_NOT_USED_AS_BLOCKING_BINDING.",
    "All other source/input/artifact hash mismatches are strict blockers.",
    "Future prompt packs must cite this repair note before comparing G12/builder manifest hashes."
  ],
  "generated_at_utc": "2026-05-12T02:35:23Z",
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
  "repair_preserved_in_prompt_packs": [
    "research/science_program_2026_05/04_goal_prompts/SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_GOAL_PROMPT_2026-05-12.md",
    "research/science_program_2026_05/04_goal_prompts/SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_CAPTURE_AUDIT_GOAL_PROMPT_2026-05-12.md",
    "research/science_program_2026_05/04_goal_prompts/SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_ACCEPTED_DESCRIPTORS_GOAL_PROMPT_2026-05-12.md",
    "research/science_program_2026_05/04_goal_prompts/SCID_DIRECTION_AWARE_RESULT_DESIGN_PREREGISTRATION_FROM_CAPTURE_AUDIT_GOAL_PROMPT_2026-05-12.md"
  ],
  "repaired_hash_binding_mismatches": [
    "research/science_program_2026_05/04_goal_prompts/G12_SCID_COMBINED_SOURCE_SEARCH_AND_FORWARD_CAPTURE_ROUTE_AUDIT_GOAL_PROMPT_2026-05-12.md",
    "research/science_program_2026_05/06_outcome_testing/scid_combined_source_search_and_forward_capture_route/SCID_COMBINED_SOURCE_CAPTURE_OUTPUT_MANIFEST_2026-05-12.json"
  ],
  "route_id": "G0_SCID_COMBINED_SOURCE_CAPTURE_ROUTE_SYNTHESIS_CONTROL",
  "schema_version": "g0_scid_combined_source_capture_synthesis_v1",
  "validation_safe": false
}
```
