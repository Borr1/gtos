# G12 G0EXP R1 Verifier And Focused Test Evidence

- **route_id:** `G12_G0EXP_R1_LOCAL_HEAVY_ROOT_PARSER_HASH_LINEAGE_SOURCE_CONTROL_AUDIT`
- **evidence_class:** `G12_G0EXP_R1_LOCAL_HEAVY_ROOT_PARSER_HASH_LINEAGE_SOURCE_CONTROL_AUDIT_ONLY`
- **promotion_verdict:** `NO_PROMOTION_VERDICT`
- **validation_safe:** `false`
- **outcome_review_opened:** `false`
- **live_effect:** `false`

- R1 verifier ok: `true`.
- Focused tests ok: `true`.

```json
{
  "artifact_family": "verifier_test_evidence",
  "changes_trading_risk_safety_prompt_decision_behavior": false,
  "credentials_touched": false,
  "evidence_class": "G12_G0EXP_R1_LOCAL_HEAVY_ROOT_PARSER_HASH_LINEAGE_SOURCE_CONTROL_AUDIT_ONLY",
  "focused_tests_ok": true,
  "generated_at_utc": "2026-05-13T04:47:59Z",
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
  "r1_final_verification_result": {
    "accepted_40_count_verified": 40,
    "adjacent_overflow_count_verified": 6,
    "artifact_count_verified": 11,
    "assigned_family_count_verified": 4,
    "can_mark_goal_complete": true,
    "evidence_class": "G0EXP_R1_LOCAL_HEAVY_ROOT_PARSER_HASH_LINEAGE_SOURCE_CONTROL_ONLY",
    "failures": [],
    "focused_tests_marked_ok": true,
    "live_effect": false,
    "ok": true,
    "outcome_review_opened": false,
    "parser_file_count_verified": 120,
    "present_root_count_verified": 19,
    "promotion_verdict": "NO_PROMOTION_VERDICT",
    "r1_new_denominator_rows_added": 0,
    "route_id": "G0EXP_R1_LOCAL_HEAVY_ROOT_PARSER_HASH_LINEAGE_SOURCE_CONTROL",
    "schema_shape_file_count_verified": 120,
    "schema_version": "g0exp_r1_verification_result_v1",
    "scoped_status_has_forbidden_live_surface": false,
    "scoped_status_has_raw_market_blob": false,
    "syntax_parse": {
      "failures": [],
      "method": "ast_parse_no_bytecode",
      "ok": true
    },
    "validation_safe": false
  },
  "r1_focused_tests": {
    "command": "python -m pytest research/science_program_2026_05/06_outcome_testing/g0exp_r1_local_heavy_root_parser_hash_lineage_source_control/test_g0exp_r1_local_heavy_root_parser_hash_lineage_source_control_2026_05_13.py -q",
    "returncode": 0,
    "stderr_tail": "",
    "stdout_tail": ".......                                                                  [100%]\n7 passed in 0.47s\n"
  },
  "r1_verifier_after_focused_tests": {
    "command": "python research/science_program_2026_05/06_outcome_testing/g0exp_r1_local_heavy_root_parser_hash_lineage_source_control/verify_g0exp_r1_local_heavy_root_parser_hash_lineage_source_control_2026_05_13.py --mark-focused-tests-ok",
    "returncode": 0,
    "stderr_tail": "",
    "stdout_tail": "{\n  \"ok\": true,\n  \"failure_count\": 0,\n  \"failures\": []\n}\n"
  },
  "r1_verifier_before_focused_tests": {
    "command": "python research/science_program_2026_05/06_outcome_testing/g0exp_r1_local_heavy_root_parser_hash_lineage_source_control/verify_g0exp_r1_local_heavy_root_parser_hash_lineage_source_control_2026_05_13.py",
    "returncode": 0,
    "stderr_tail": "",
    "stdout_tail": "{\n  \"ok\": true,\n  \"failure_count\": 0,\n  \"failures\": []\n}\n"
  },
  "r1_verifier_ok": true,
  "route_id": "G12_G0EXP_R1_LOCAL_HEAVY_ROOT_PARSER_HASH_LINEAGE_SOURCE_CONTROL_AUDIT",
  "schema_version": "g12_g0exp_r1_local_heavy_root_parser_hash_lineage_source_control_audit_v1",
  "validation_safe": false
}
```
