# Closeout Verification

- **route_id:** `G0_SCID_COMBINED_SOURCE_CAPTURE_ROUTE_SYNTHESIS_CONTROL`
- **evidence_class:** `G0_SCID_COMBINED_SOURCE_CAPTURE_ROUTE_SYNTHESIS_CONTROL_ONLY`
- **promotion_verdict:** `NO_PROMOTION_VERDICT`
- **validation_safe:** `false`
- **outcome_review_opened:** `false`
- **live_effect:** `false`

```json
{
  "artifact_family": "closeout_verification",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "evidence_class": "G0_SCID_COMBINED_SOURCE_CAPTURE_ROUTE_SYNTHESIS_CONTROL_ONLY",
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
  "planned_commands": [
    "python research/science_program_2026_05/06_outcome_testing/g0_scid_combined_source_capture_route_synthesis_control/build_g0_scid_combined_source_capture_route_synthesis_control_2026_05_12.py",
    "python research/science_program_2026_05/06_outcome_testing/g0_scid_combined_source_capture_route_synthesis_control/verify_g0_scid_combined_source_capture_route_synthesis_control_2026_05_12.py",
    "python -m pytest -q -p no:cacheprovider research/science_program_2026_05/06_outcome_testing/g0_scid_combined_source_capture_route_synthesis_control/test_g0_scid_combined_source_capture_route_synthesis_control_2026_05_12.py",
    "python scripts/generate_live_state.py"
  ],
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "prompt_pack_paths": {
    "SCID_DIRECTION_AWARE_RESULT_DESIGN_PREREGISTRATION_FROM_CAPTURE_AUDIT_GOAL_PROMPT_2026-05-12.md": "research/science_program_2026_05/04_goal_prompts/SCID_DIRECTION_AWARE_RESULT_DESIGN_PREREGISTRATION_FROM_CAPTURE_AUDIT_GOAL_PROMPT_2026-05-12.md",
    "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_GOAL_PROMPT_2026-05-12.md": "research/science_program_2026_05/04_goal_prompts/SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_GOAL_PROMPT_2026-05-12.md",
    "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_CAPTURE_AUDIT_GOAL_PROMPT_2026-05-12.md": "research/science_program_2026_05/04_goal_prompts/SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_CAPTURE_AUDIT_GOAL_PROMPT_2026-05-12.md",
    "SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_ACCEPTED_DESCRIPTORS_GOAL_PROMPT_2026-05-12.md": "research/science_program_2026_05/04_goal_prompts/SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_ACCEPTED_DESCRIPTORS_GOAL_PROMPT_2026-05-12.md"
  },
  "route_artifact_dir": "research/science_program_2026_05/06_outcome_testing/g0_scid_combined_source_capture_route_synthesis_control",
  "route_id": "G0_SCID_COMBINED_SOURCE_CAPTURE_ROUTE_SYNTHESIS_CONTROL",
  "schema_version": "g0_scid_combined_source_capture_synthesis_v1",
  "status": "READY_FOR_STANDALONE_VERIFIER_FOCUSED_TESTS_SCOPED_COMMIT_AND_FINAL_LIVE_STATE_REFRESH",
  "terminal_decision": "ACCEPT_AS_G0_SCID_COMBINED_SOURCE_CAPTURE_SYNTHESIS_WITH_RANKED_ROUTE_BUNDLE",
  "validation_safe": false
}
```
