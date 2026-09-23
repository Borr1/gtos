# Context Instruction Coverage Ledger

- Route: `NO_API_MECHANICAL_REPLAY_FAMILY_PATH_BEHAVIOR_DISCOVERY_RESULT_SCREEN`
- Evidence class: `NO_API_DISCOVERY_RESULT_QUARANTINED_ONLY`
- Generated: `2026-05-11T04:20:56+00:00`
- Promotion posture: `NO_PROMOTION_VERDICT`
- Boundary: discovery path-behavior only; no validation, promotion, R, PnL, win-rate, expectancy, broker/account/order/history/deal/position evidence, AI/API, paid/vendor access, or live behavior.

```json
{
  "all_requirements_covered": true,
  "artifact_family": "context_instruction_coverage_ledger",
  "changes_live_trading_behavior": false,
  "checks": [
    {
      "evidence": "Mandatory preflight executed before route build",
      "requirement_id": "preflight_context_refreshed",
      "status": "PASS"
    },
    {
      "evidence": "research/science_program_2026_05/06_outcome_testing/no_api_mechanical_replay_family_path_behavior_discovery_result_screen/FPB_DENOMINATOR_DUPLICATE_POLICY_2026-05-10.json",
      "requirement_id": "denominator_duplicate_policy_frozen",
      "status": "PASS"
    },
    {
      "evidence": "research/science_program_2026_05/06_outcome_testing/no_api_mechanical_replay_family_path_behavior_discovery_result_screen/FPB_LFS_MATERIALIZATION_AUDIT_2026-05-10.json",
      "requirement_id": "lfs_materialization_checked",
      "status": "PASS"
    },
    {
      "evidence": "research/science_program_2026_05/06_outcome_testing/no_api_mechanical_replay_family_path_behavior_discovery_result_screen/FPB_FULL_POPULATION_AGGREGATE_MATRIX_2026-05-10.json",
      "requirement_id": "full_population_aggregate_matrix",
      "status": "PASS"
    },
    {
      "evidence": "11 opened families",
      "requirement_id": "all_11_families_included",
      "status": "PASS"
    },
    {
      "evidence": "research/science_program_2026_05/06_outcome_testing/no_api_mechanical_replay_family_path_behavior_discovery_result_screen/FPB_BASELINE_CONTROL_LEDGER_2026-05-10.json",
      "requirement_id": "all_4_baseline_controls_included",
      "status": "PASS"
    },
    {
      "evidence": "ONE_ATR_CONTINUATION_CONTEXT_TOUCH, PROTECTIVE_BOUNDARY_CLOSE_CONTEXT_TOUCH, MIDPOINT_RETRACE_BEFORE_EXTENSION, ONE_ATR_EXTENSION_WITHOUT_MIDPOINT_RETRACE, SAME_BAR_CONTEXT_AMBIGUOUS, UNRESOLVED_BY_WINDOW, UNRESOLVED_AT_SOURCE_END",
      "requirement_id": "label_vocabulary_exact",
      "status": "PASS"
    },
    {
      "evidence": "family_rows include ambiguity_unresolved_count separately",
      "requirement_id": "ambiguity_unresolved_separated",
      "status": "PASS"
    },
    {
      "evidence": "research/science_program_2026_05/06_outcome_testing/no_api_mechanical_replay_family_path_behavior_discovery_result_screen/FPB_COMPACT_CAP_DIAGNOSTICS_2026-05-10.json",
      "requirement_id": "compact_cap_explicit",
      "status": "PASS"
    },
    {
      "evidence": "research/science_program_2026_05/06_outcome_testing/no_api_mechanical_replay_family_path_behavior_discovery_result_screen/FPB_SELECTION_BIAS_MULTIPLE_TESTING_LEDGER_2026-05-10.json",
      "requirement_id": "selection_bias_multiple_testing_recorded",
      "status": "PASS"
    },
    {
      "evidence": "research/science_program_2026_05/06_outcome_testing/no_api_mechanical_replay_family_path_behavior_discovery_result_screen/FPB_FAILURE_ANATOMY_NEXT_HYPOTHESIS_LEDGER_2026-05-10.json",
      "requirement_id": "failure_anatomy_next_hypothesis_discovery_only",
      "status": "PASS"
    },
    {
      "evidence": "research/science_program_2026_05/06_outcome_testing/no_api_mechanical_replay_family_path_behavior_discovery_result_screen/FPB_CONTEXT_ANCHOR_2026-05-10.json",
      "requirement_id": "context_anchor_exists",
      "status": "PASS"
    },
    {
      "evidence": "research/science_program_2026_05/04_goal_prompts/G12_NO_API_MECHANICAL_REPLAY_FAMILY_PATH_BEHAVIOR_DISCOVERY_RESULT_AUDIT_GOAL_PROMPT_2026-05-10.md",
      "requirement_id": "post_result_g12_prompt_exists",
      "status": "PASS"
    },
    {
      "evidence": "builder/verifier/test files in route directory",
      "requirement_id": "builder_verifier_focused_tests_present",
      "status": "PASS"
    },
    {
      "evidence": "research/science_program_2026_05/06_outcome_testing/no_api_mechanical_replay_family_path_behavior_discovery_result_screen/FPB_NOLEAK_DIRTY_STATE_AUDIT_2026-05-10.json",
      "requirement_id": "no_forbidden_surfaces_opened",
      "status": "PASS"
    }
  ],
  "credentials_touched": false,
  "evidence_class": "NO_API_DISCOVERY_RESULT_QUARANTINED_ONLY",
  "generated_at_utc": "2026-05-11T04:20:56+00:00",
  "live_effect": false,
  "opens_live_restart": false,
  "opens_live_trading_behavior": false,
  "opens_mt5_order_account_history_behavior": false,
  "opens_paid_api_or_databento_route": false,
  "opens_promotion": false,
  "opens_registry_edit": false,
  "opens_remote_push": false,
  "opens_result_scoring": false,
  "opens_validation": false,
  "outcome_review_opened": false,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "resume_context_policy": "On resume or compaction, regenerate LIVE_STATE and re-read this ledger plus the context anchor before continuing.",
  "route_id": "NO_API_MECHANICAL_REPLAY_FAMILY_PATH_BEHAVIOR_DISCOVERY_RESULT_SCREEN",
  "schema_version": "family_path_behavior_discovery_result_screen_v1",
  "validation_safe": false
}
```
