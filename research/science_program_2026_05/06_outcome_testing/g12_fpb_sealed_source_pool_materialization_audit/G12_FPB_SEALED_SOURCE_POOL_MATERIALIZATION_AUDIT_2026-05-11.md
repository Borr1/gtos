# G12 FPB Sealed Source Pool Materialization Audit

- Route: `G12_FPB_SEALED_SOURCE_POOL_MATERIALIZATION_AUDIT`
- Artifact family: `audit_verdict`
- Evidence class: `G12_FPB_SEALED_SOURCE_POOL_SOURCE_CONTROL_AUDIT_ONLY`
- Promotion posture: `NO_PROMOTION_VERDICT`
- Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

```json
{
  "accepted_scid_after_audit": 0,
  "accepted_source_pool_status": "REPAIR_BLOCKED",
  "artifact_family": "audit_verdict",
  "audit_decision": "REPAIR_BLOCKED_SOURCE_POOL_PACKET",
  "changes_live_trading_behavior": false,
  "command_audit": {
    "target_focused_pytest_first_attempt_observed_before_builder": {
      "args": [
        "C:\\Python313\\python.exe",
        "-m",
        "pytest",
        "-q",
        "research/science_program_2026_05/06_outcome_testing/fpb_source_expansion_and_sealed_pool_materialization/test_fpb_source_expansion_and_sealed_pool_materialization_2026_05_11.py",
        "--basetemp",
        "C:\\tmp\\pytest-g12-source-expansion-existing",
        "--cache-clear"
      ],
      "classification": "ENVIRONMENT_CACHE_PERMISSION_FAILURE_NOT_TEST_FAILURE",
      "ok": false,
      "returncode": 1,
      "stderr_summary": "PermissionError [WinError 5] Access is denied: .pytest_cache/v before tests executed"
    },
    "target_focused_pytest_nocache": {
      "args": [
        "C:\\Python313\\python.exe",
        "-m",
        "pytest",
        "-q",
        "research/science_program_2026_05/06_outcome_testing/fpb_source_expansion_and_sealed_pool_materialization/test_fpb_source_expansion_and_sealed_pool_materialization_2026_05_11.py",
        "-p",
        "no:cacheprovider",
        "--basetemp",
        "C:\\tmp\\pytest-g12-fpb-source-packet-existing"
      ],
      "ok": true,
      "returncode": 0,
      "stderr": "",
      "stdout": "....                                                                     [100%]\n4 passed in 0.13s\n"
    },
    "target_py_compile": {
      "args": [
        "C:\\Python313\\python.exe",
        "-m",
        "py_compile",
        "research/science_program_2026_05/06_outcome_testing/fpb_source_expansion_and_sealed_pool_materialization/build_fpb_source_expansion_and_sealed_pool_materialization_2026_05_11.py",
        "research/science_program_2026_05/06_outcome_testing/fpb_source_expansion_and_sealed_pool_materialization/verify_fpb_source_expansion_and_sealed_pool_materialization_2026_05_11.py",
        "research/science_program_2026_05/06_outcome_testing/fpb_source_expansion_and_sealed_pool_materialization/test_fpb_source_expansion_and_sealed_pool_materialization_2026_05_11.py"
      ],
      "ok": true,
      "returncode": 0,
      "stderr": "",
      "stdout": ""
    },
    "target_verifier": {
      "args": [
        "C:\\Python313\\python.exe",
        "research/science_program_2026_05/06_outcome_testing/fpb_source_expansion_and_sealed_pool_materialization/verify_fpb_source_expansion_and_sealed_pool_materialization_2026_05_11.py"
      ],
      "ok": true,
      "returncode": 0,
      "stderr": "",
      "stdout": "{\n  \"check_count\": 35,\n  \"verification_passed\": true\n}\n"
    }
  },
  "controlling_prompt": "research/science_program_2026_05/04_goal_prompts/G12_FPB_SEALED_SOURCE_POOL_MATERIALIZATION_AUDIT_GOAL_PROMPT_2026-05-11.md",
  "credentials_touched": false,
  "evidence_class": "G12_FPB_SEALED_SOURCE_POOL_SOURCE_CONTROL_AUDIT_ONLY",
  "generated_at_utc": "2026-05-11T09:43:01Z",
  "live_effect": false,
  "next_route": "FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR",
  "no_validation_execution_prompt_emitted": true,
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
  "packet_shape_summary": {
    "csv_candidate_count": 0,
    "native_candidate_count": 9,
    "selected_source_count": 365
  },
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "repair_blocker_count": 9,
  "route_id": "G12_FPB_SEALED_SOURCE_POOL_MATERIALIZATION_AUDIT",
  "safe_flags": {
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
    "validation_safe": false
  },
  "schema_version": "g12_fpb_sealed_source_pool_materialization_audit_v1",
  "scid_candidate_count": 9,
  "target_packet": "research/science_program_2026_05/06_outcome_testing/fpb_source_expansion_and_sealed_pool_materialization",
  "validation_remains_blocked": true,
  "validation_safe": false
}
```
