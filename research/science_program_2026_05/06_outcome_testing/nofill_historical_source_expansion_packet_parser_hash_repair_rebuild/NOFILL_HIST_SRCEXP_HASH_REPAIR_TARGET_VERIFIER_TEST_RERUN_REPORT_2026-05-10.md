# NOFILL Source Expansion Parser Hash Repair Target Verifier Test Rerun Report

Route: `NOFILL_HISTORICAL_SOURCE_EXPANSION_PACKET_PARSER_HASH_REPAIR_REBUILD`
Terminal decision: `REPAIR_REBUILD_READY_FOR_G12_REAUDIT`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Summary

```json
{
  "artifact_family": "target_verifier_test_rerun_report",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
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
  "route_id": "NOFILL_HISTORICAL_SOURCE_EXPANSION_PACKET_PARSER_HASH_REPAIR_REBUILD",
  "schema_version": "nofill_historical_source_expansion_packet_parser_hash_repair_rebuild_v1",
  "status": "TARGET_VERIFIER_AND_FOCUSED_TESTS_PASSED",
  "target_focused_pytest_passed": true,
  "target_focused_pytest_run": {
    "command": [
      "C:\\Python313\\python.exe",
      "-m",
      "pytest",
      "C:\\tmp\\gtos_otb\\G12NOFILLHASHREPAIR\\research\\science_program_2026_05\\06_outcome_testing\\nofill_historical_source_expansion_builder_local_tick_shadow_packet\\test_nofill_historical_source_expansion_builder_local_tick_shadow_packet_2026_05_10.py",
      "-q",
      "-p",
      "no:cacheprovider"
    ],
    "returncode": 0,
    "stderr_tail": "",
    "stdout_tail": "......                                                                   [100%]\n6 passed in 0.46s\n"
  },
  "target_focused_pytest_was_run": true,
  "target_verifier_passed": true,
  "target_verifier_run": {
    "command": [
      "C:\\Python313\\python.exe",
      "C:\\tmp\\gtos_otb\\G12NOFILLHASHREPAIR\\research\\science_program_2026_05\\06_outcome_testing\\nofill_historical_source_expansion_builder_local_tick_shadow_packet\\verify_nofill_historical_source_expansion_builder_local_tick_shadow_packet_2026_05_10.py"
    ],
    "returncode": 0,
    "stderr_tail": "",
    "stdout_tail": "{\n  \"can_mark_goal_complete\": true,\n  \"diff_scope\": {\n    \"changed_or_untracked_paths\": [\n      \".context/LIVE_STATE.md\",\n      \"research/science_program_2026_05/06_outcome_testing/g12_nofill_historical_source_expansion_hash_repair_reaudit/G12_NOFILL_HIST_SRCEXP_HASH_REPAIR_REAUDIT_CONTEXT_ANCHOR_2026-05-10.json\",\n      \"research/science_program_2026_05/06_outcome_testing/g12_nofill_historical_source_expansion_hash_repair_reaudit/G12_NOFILL_HIST_SRCEXP_HASH_REPAIR_REAUDIT_CONTEXT_ANCHOR_2026-05-10.md\",\n      \"research/science_program_2026_05/06_outcome_testing/g12_nofill_historical_source_expansion_hash_repair_reaudit/G12_NOFILL_HIST_SRCEXP_HASH_REPAIR_REAUDIT_EXACT_BLOCKER_CLOSURE_REAUDIT_2026-05-10.json\",\n      \"research/science_program_2026_05/06_outcome_testing/g12_nofill_historical_source_expansion_hash_repair_reaudit/G12_NOFILL_HIST_SRCEXP_HASH_REPAIR_REAUDIT_EXACT_BLOCKER_CLOSURE_REAUDIT_2026-05-10.md\",\n      \"research/science_program_2026_05/06_outcome_testing/g12_nofill_historical_source_expansion_hash_repair_reaudit/G12_NOFILL_HIST_SRCEXP_HASH_REPAIR_REAUDIT_PACKET_HASH_MANIFEST_REAUDIT_2026-05-10.json\",\n      \"research/science_program_2026_05/06_outcome_testing/g12_nofill_historical_source_expansion_hash_repair_reaudit/G12_NOFILL_HIST_SRCEXP_HASH_REPAIR_REAUDIT_PACKET_HASH_MANIFEST_REAUDIT_2026-05-10.md\",\n      \"research/science_program_2026_05/06_outcome_testing/g12_nofill_historical_source_expansion_hash_repair_reaudit/G12_NOFILL_HIST_SRCEXP_HASH_REPAIR_REAUDIT_SEMANTIC_NO_ROW_CHANGE_REAUDIT_2026-05-10.json\",\n      \"research/science_program_2026_05/06_outcome_testing/g12_nofill_historical_source_expansion_hash_repair_reaudit/G12_NOFILL_HIST_SRCEXP_HASH_REPAIR_REAUDIT_SEMANTIC_NO_ROW_CHANGE_REAUDIT_2026-05-10.md\",\n      \"research/science_program_2026_05/06_outcome_testing/g12_nofill_historical_source_expansion_hash_repair_reaudit/G12_NOFILL_HIST_SRCEXP_HASH_REPAIR_REAUDIT_SOURCE_HASH_PARSER_HASH_RECOMPUTATION_AUDIT_2026-05-10.json\",\n      \"research/science_program_2026_05/06_outcome_testing/g12_nofill_historical_source_expansion_hash_repair_reaudit/G12_NOFILL_HIST_SRCEXP_HASH_REPAIR_REAUDIT_SOURCE_HASH_PARSER_HASH_RECOMPUTATION_AUDIT_2026-05-10.md\",\n      \"research/science_program_2026_05/06_outcome_testing/g12_nofill_historical_source_expansion_hash_repair_reaudit/G12_NOFILL_HIST_SRCEXP_HASH_REPAIR_REAUDIT_TARGET_VERIFIER_TEST_RERUN_AUDIT_2026-05-10.json\",\n      \"research/science_program_2026_05/06_outcome_testing/g12_nofill_historical_source_expansion_hash_repair_reaudit/G12_NOFILL_HIST_SRCEXP_HASH_REPAIR_REAUDIT_TARGET_VERIFIER_TEST_RERUN_AUDIT_2026-05-10.md\",\n      \"research/science_program_2026_05/06_outcome_testing/g12_nofill_historical_source_expansion_hash_repair_reaudit/build_g12_nofill_historical_source_expansion_hash_repair_reaudit_2026_05_10.py\",\n      \"research/science_program_2026_05/06_outcome_testing/g12_nofill_historical_source_expansion_hash_repair_reaudit/test_g12_nofill_historical_source_expansion_hash_repair_reaudit_2026_05_10.py\",\n      \"research/science_program_2026_05/06_outcome_testing/g12_nofill_historical_source_expansion_hash_repair_reaudit/verify_g12_nofill_historical_source_expansion_hash_repair_reaudit_2026_05_10.py\",\n      \"research/science_program_2026_05/06_outcome_testing/nofill_historical_source_expansion_builder_local_tick_shadow_packet/NOFILL_HIST_SOURCE_EXPANSION_COMPLETION_AUDIT_2026-05-10.json\",\n      \"research/science_program_2026_05/06_outcome_testing/nofill_historical_source_expansion_builder_local_tick_shadow_packet/NOFILL_HIST_SOURCE_EXPANSION_COMPLETION_AUDIT_2026-05-10.md\",\n      \"research/science_program_2026_05/06_outcome_testing/nofill_historical_source_expansion_builder_local_tick_shadow_packet/NOFILL_HIST_SOURCE_EXPANSION_VERIFICATION_RESULT_2026-05-10.json\",\n      \"research/science_program_2026_05/06_outcome_testing/nofill_historical_source_expansion_packet_parser_hash_repair_rebuild/NOFILL_HIST_SRCEXP_HASH_REPAIR_COMPLETION_AUDIT_2026-05-10.json\",\n      \"research/science_program_2026_05/06_outcome_testing/nofill_historical_source_expansion_packet_parser_hash_repair_rebuild/NOFILL_HIST_SRCEXP_HASH_REPAIR_COMPLETION_AUDIT_2026-05-10.md\",\n      \"research/science_program_2026_05/06_outcome_testing/nofill_historical_source_expansion_packet_parser_hash_repair_rebuild/NOFILL_HIST_SRCEXP_HASH_REPAIR_TARGET_VERIFIER_TEST_RERUN_REPORT_2026-05-10.json\",\n      \"research/science_program_2026_05/06_outcome_testing/nofill_historical_source_expansion_packet_parser_hash_repair_rebuild/NOFILL_HIST_SRCEXP_HASH_REPAIR_TARGET_VERIFIER_TEST_RERUN_REPORT_2026-05-10.md\",\n      \"research/science_program_2026_05/06_outcome_testing/nofill_historical_source_expansion_packet_parser_hash_repair_rebuild/NOFILL_HIST_SRCEXP_HASH_REPAIR_VERIFICATION_RESULT_2026-05-10.json\"\n    ],\n    \"forbidden_live_surface_paths\": [],\n    \"ok\": true\n  },\n  \"failures\": [],\n  \"field_count\": 55,\n  \"future20_field_count\": 20,\n  \"live_effect\": false,\n  \"ok\": true,\n  \"outcome_review_opened\": false,\n  \"packet_row_count\": 2,\n  \"promotion_verdict\": \"NO_PROMOTION_VERDICT\",\n  \"route_id\": \"NOFILL_HISTORICAL_SOURCE_EXPANSION_BUILDER_LOCAL_TICK_SHADOW_PACKET\",\n  \"schema_version\": \"nofill_historical_source_expansion_builder_local_tick_shadow_packet_v1_verifier_v1\",\n  \"terminal_decision\": \"ACCEPT_SOURCE_HASHED_INPUT_PACKET_READY_FOR_G12_SOURCE_CONTROL_AUDIT\",\n  \"validation_safe\": false\n}\n"
  },
  "target_verifier_was_run": true,
  "terminal_decision": "REPAIR_REBUILD_READY_FOR_G12_REAUDIT",
  "validation_safe": false
}
```
