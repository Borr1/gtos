# Target Verifier Test Rerun Report

Route: `G12_NOFILL_HISTORICAL_SEALED_VALIDATION_PARTITION_SOURCE_BINDING_AUDIT`
Target route: `NOFILL_HISTORICAL_SEALED_VALIDATION_PARTITION_AND_SOURCE_BINDING`
Promotion posture: `NO_PROMOTION_VERDICT`
Safe flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

## Summary

```json
{
  "artifact_family": "target_verifier_test_rerun_report",
  "ast_syntax_fallback": {
    "checked_paths": [
      "research/science_program_2026_05/06_outcome_testing/nofill_historical_sealed_validation_partition_and_source_binding/verify_nofill_historical_sealed_validation_partition_and_source_binding_2026_05_10.py",
      "research/science_program_2026_05/06_outcome_testing/nofill_historical_sealed_validation_partition_and_source_binding/test_nofill_historical_sealed_validation_partition_and_source_binding_2026_05_10.py",
      "research/science_program_2026_05/06_outcome_testing/nofill_historical_sealed_validation_partition_and_source_binding/build_nofill_historical_sealed_validation_partition_and_source_binding_2026_05_10.py",
      "research/science_program_2026_05/06_outcome_testing/g12_nofill_historical_sealed_validation_partition_source_binding_audit/build_g12_nofill_historical_sealed_validation_partition_source_binding_audit_2026_05_10.py",
      "research/science_program_2026_05/06_outcome_testing/g12_nofill_historical_sealed_validation_partition_source_binding_audit/verify_g12_nofill_historical_sealed_validation_partition_source_binding_audit_2026_05_10.py",
      "research/science_program_2026_05/06_outcome_testing/g12_nofill_historical_sealed_validation_partition_source_binding_audit/test_g12_nofill_historical_sealed_validation_partition_source_binding_audit_2026_05_10.py"
    ],
    "errors": [],
    "passed": true
  },
  "audit_passed": true,
  "changes_live_trading_behavior": false,
  "checks": {
    "syntax_check_passed": true,
    "target_focused_tests_passed": true,
    "target_verifier_passed": true
  },
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
  "py_compile_rerun": {
    "command": "C:\\Python313\\python.exe -B -m py_compile C:\\tmp\\gtos_otb\\G12NOFILLHISTPART\\research\\science_program_2026_05\\06_outcome_testing\\nofill_historical_sealed_validation_partition_and_source_binding\\verify_nofill_historical_sealed_validation_partition_and_source_binding_2026_05_10.py C:\\tmp\\gtos_otb\\G12NOFILLHISTPART\\research\\science_program_2026_05\\06_outcome_testing\\nofill_historical_sealed_validation_partition_and_source_binding\\test_nofill_historical_sealed_validation_partition_and_source_binding_2026_05_10.py C:\\tmp\\gtos_otb\\G12NOFILLHISTPART\\research\\science_program_2026_05\\06_outcome_testing\\nofill_historical_sealed_validation_partition_and_source_binding\\build_nofill_historical_sealed_validation_partition_and_source_binding_2026_05_10.py C:\\tmp\\gtos_otb\\G12NOFILLHISTPART\\research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_historical_sealed_validation_partition_source_binding_audit\\build_g12_nofill_historical_sealed_validation_partition_source_binding_audit_2026_05_10.py C:\\tmp\\gtos_otb\\G12NOFILLHISTPART\\research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_historical_sealed_validation_partition_source_binding_audit\\verify_g12_nofill_historical_sealed_validation_partition_source_binding_audit_2026_05_10.py C:\\tmp\\gtos_otb\\G12NOFILLHISTPART\\research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_historical_sealed_validation_partition_source_binding_audit\\test_g12_nofill_historical_sealed_validation_partition_source_binding_audit_2026_05_10.py",
    "completed_at_utc": "2026-05-10T03:55:15Z",
    "passed": false,
    "returncode": 1,
    "started_at_utc": "2026-05-10T03:55:14Z",
    "stderr_tail": "[Errno 2] No such file or directory: 'C:\\\\tmp\\\\gtos_otb\\\\G12NOFILLHISTPART\\\\research\\\\science_program_2026_05\\\\06_outcome_testing\\\\nofill_historical_sealed_validation_partition_and_source_binding\\\\__pycache__\\\\verify_nofill_historical_sealed_validation_partition_and_source_binding_2026_05_10.cpython-313.pyc.2384267098416'",
    "stdout_tail": ""
  },
  "target_focused_tests_rerun": {
    "command": "C:\\Python313\\python.exe -m pytest C:\\tmp\\gtos_otb\\G12NOFILLHISTPART\\research\\science_program_2026_05\\06_outcome_testing\\nofill_historical_sealed_validation_partition_and_source_binding\\test_nofill_historical_sealed_validation_partition_and_source_binding_2026_05_10.py -q",
    "completed_at_utc": "2026-05-10T03:55:14Z",
    "passed": true,
    "returncode": 0,
    "started_at_utc": "2026-05-10T03:55:13Z",
    "stderr_tail": "",
    "stdout_tail": "....                                                                     [100%]\n4 passed in 0.13s\n"
  },
  "target_route_id": "NOFILL_HISTORICAL_SEALED_VALIDATION_PARTITION_AND_SOURCE_BINDING",
  "target_verifier_rerun": {
    "command": "C:\\Python313\\python.exe C:\\tmp\\gtos_otb\\G12NOFILLHISTPART\\research\\science_program_2026_05\\06_outcome_testing\\nofill_historical_sealed_validation_partition_and_source_binding\\verify_nofill_historical_sealed_validation_partition_and_source_binding_2026_05_10.py",
    "completed_at_utc": "2026-05-10T03:55:13Z",
    "passed": true,
    "returncode": 0,
    "started_at_utc": "2026-05-10T03:55:12Z",
    "stderr_tail": "",
    "stdout_tail": "{\n  \"can_mark_goal_complete\": true,\n  \"cat_v3_partition_rows\": 298,\n  \"field_blocker_count\": 20,\n  \"field_count\": 55,\n  \"issues\": [],\n  \"live_effect\": false,\n  \"ok\": true,\n  \"outcome_review_opened\": false,\n  \"promotion_verdict\": \"NO_PROMOTION_VERDICT\",\n  \"route_id\": \"NOFILL_HISTORICAL_SEALED_VALIDATION_PARTITION_AND_SOURCE_BINDING\",\n  \"schema_version\": \"nofill_historical_sealed_validation_partition_and_source_binding_verifier_v1\",\n  \"sealed_validation_current_committed_nofill_rows\": 0,\n  \"validation_safe\": false\n}\n"
  },
  "validation_safe": false
}
```
