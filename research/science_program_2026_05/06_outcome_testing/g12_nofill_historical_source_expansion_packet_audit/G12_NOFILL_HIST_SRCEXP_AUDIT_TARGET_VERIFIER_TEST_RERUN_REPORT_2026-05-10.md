# Target Verifier Test Rerun Report

Route: `G12_NOFILL_HISTORICAL_SOURCE_EXPANSION_PACKET_AUDIT`
Target route: `NOFILL_HISTORICAL_SOURCE_EXPANSION_BUILDER_LOCAL_TICK_SHADOW_PACKET`
Promotion posture: `NO_PROMOTION_VERDICT`
Safe flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

## Summary

```json
{
  "artifact_family": "target_verifier_test_rerun_report",
  "audit_passed": true,
  "changes_live_trading_behavior": false,
  "checks": {
    "target_failures_reduced_to_exact_context_or_repair_requirement_or_passed": true,
    "target_focused_pytest_was_run": true,
    "target_verifier_was_run": true
  },
  "credentials_touched": false,
  "generated_at_utc": "2026-05-10T05:28:57Z",
  "live_effect": false,
  "nonzero_run_classifications": [
    {
      "classification": "TARGET_PARSER_HASH_MISMATCH_REDUCED_TO_EXACT_REPAIR_REQUIREMENT",
      "command": [
        "C:\\Python313\\python.exe",
        "C:\\tmp\\gtos_otb\\G12NOFILLHISTSRCEXP\\research\\science_program_2026_05\\06_outcome_testing\\nofill_historical_source_expansion_builder_local_tick_shadow_packet\\verify_nofill_historical_source_expansion_builder_local_tick_shadow_packet_2026_05_10.py"
      ],
      "returncode": 1
    },
    {
      "classification": "TARGET_PYTEST_VERIFIER_FAILURE_REDUCED_TO_EXACT_PARSER_HASH_REPAIR_REQUIREMENT",
      "command": [
        "C:\\Python313\\python.exe",
        "-m",
        "pytest",
        "C:\\tmp\\gtos_otb\\G12NOFILLHISTSRCEXP\\research\\science_program_2026_05\\06_outcome_testing\\nofill_historical_source_expansion_builder_local_tick_shadow_packet\\test_nofill_historical_source_expansion_builder_local_tick_shadow_packet_2026_05_10.py",
        "-q",
        "-p",
        "no:cacheprovider"
      ],
      "returncode": 1
    }
  ],
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
  "target_focused_pytest_run": {
    "command": [
      "C:\\Python313\\python.exe",
      "-m",
      "pytest",
      "C:\\tmp\\gtos_otb\\G12NOFILLHISTSRCEXP\\research\\science_program_2026_05\\06_outcome_testing\\nofill_historical_source_expansion_builder_local_tick_shadow_packet\\test_nofill_historical_source_expansion_builder_local_tick_shadow_packet_2026_05_10.py",
      "-q",
      "-p",
      "no:cacheprovider"
    ],
    "completed_at_utc": "2026-05-10T05:28:57Z",
    "returncode": 1,
    "started_at_utc": "2026-05-10T05:28:56Z",
    "stderr_tail": "",
    "stdout_tail": ".....F                                                                   [100%]\n================================== FAILURES ===================================\n____________________ test_verifier_accepts_generated_route ____________________\n\n    def test_verifier_accepts_generated_route():\n        verifier = _load_module(VERIFIER_PATH, \"nofill_source_expansion_verifier\")\n        result = verifier.verify()\n>       assert result[\"ok\"] is True\nE       assert False is True\n\nresearch\\science_program_2026_05\\06_outcome_testing\\nofill_historical_source_expansion_builder_local_tick_shadow_packet\\test_nofill_historical_source_expansion_builder_local_tick_shadow_packet_2026_05_10.py:107: AssertionError\n=========================== short test summary info ===========================\nFAILED research/science_program_2026_05/06_outcome_testing/nofill_historical_source_expansion_builder_local_tick_shadow_packet/test_nofill_historical_source_expansion_builder_local_tick_shadow_packet_2026_05_10.py::test_verifier_accepts_generated_route\n1 failed, 5 passed in 0.51s\n"
  },
  "target_verifier_run": {
    "command": [
      "C:\\Python313\\python.exe",
      "C:\\tmp\\gtos_otb\\G12NOFILLHISTSRCEXP\\research\\science_program_2026_05\\06_outcome_testing\\nofill_historical_source_expansion_builder_local_tick_shadow_packet\\verify_nofill_historical_source_expansion_builder_local_tick_shadow_packet_2026_05_10.py"
    ],
    "completed_at_utc": "2026-05-10T05:28:56Z",
    "returncode": 1,
    "started_at_utc": "2026-05-10T05:28:55Z",
    "stderr_tail": "",
    "stdout_tail": "ome_testing/g12_nofill_historical_source_expansion_packet_audit/G12_NOFILL_HIST_SRCEXP_AUDIT_FORBIDDEN_REDACTED_NOLEAK_AUDIT_2026-05-10.json\",\n      \"research/science_program_2026_05/06_outcome_testing/g12_nofill_historical_source_expansion_packet_audit/G12_NOFILL_HIST_SRCEXP_AUDIT_FORBIDDEN_REDACTED_NOLEAK_AUDIT_2026-05-10.md\",\n      \"research/science_program_2026_05/06_outcome_testing/g12_nofill_historical_source_expansion_packet_audit/G12_NOFILL_HIST_SRCEXP_AUDIT_FUTURE20_EXTRACTION_FAIL_CLOSED_AUDIT_2026-05-10.json\",\n      \"research/science_program_2026_05/06_outcome_testing/g12_nofill_historical_source_expansion_packet_audit/G12_NOFILL_HIST_SRCEXP_AUDIT_FUTURE20_EXTRACTION_FAIL_CLOSED_AUDIT_2026-05-10.md\",\n      \"research/science_program_2026_05/06_outcome_testing/g12_nofill_historical_source_expansion_packet_audit/G12_NOFILL_HIST_SRCEXP_AUDIT_FUTURE_ROUTE_ELIGIBILITY_LEDGER_2026-05-10.json\",\n      \"research/science_program_2026_05/06_outcome_testing/g12_nofill_historical_source_expansion_packet_audit/G12_NOFILL_HIST_SRCEXP_AUDIT_FUTURE_ROUTE_ELIGIBILITY_LEDGER_2026-05-10.md\",\n      \"research/science_program_2026_05/06_outcome_testing/g12_nofill_historical_source_expansion_packet_audit/G12_NOFILL_HIST_SRCEXP_AUDIT_NEXT_ROUTE_PROMPT_PACK_2026-05-10.md\",\n      \"research/science_program_2026_05/06_outcome_testing/g12_nofill_historical_source_expansion_packet_audit/G12_NOFILL_HIST_SRCEXP_AUDIT_SATURATION_ADVERSARIAL_ISSUE_LEDGER_2026-05-10.json\",\n      \"research/science_program_2026_05/06_outcome_testing/g12_nofill_historical_source_expansion_packet_audit/G12_NOFILL_HIST_SRCEXP_AUDIT_SATURATION_ADVERSARIAL_ISSUE_LEDGER_2026-05-10.md\",\n      \"research/science_program_2026_05/06_outcome_testing/g12_nofill_historical_source_expansion_packet_audit/G12_NOFILL_HIST_SRCEXP_AUDIT_SOURCE_HASH_PARSER_HASH_AUDIT_2026-05-10.json\",\n      \"research/science_program_2026_05/06_outcome_testing/g12_nofill_historical_source_expansion_packet_audit/G12_NOFILL_HIST_SRCEXP_AUDIT_SOURCE_HASH_PARSER_HASH_AUDIT_2026-05-10.md\",\n      \"research/science_program_2026_05/06_outcome_testing/g12_nofill_historical_source_expansion_packet_audit/G12_NOFILL_HIST_SRCEXP_AUDIT_SOURCE_PACKET_ROW_RECOMPUTATION_AUDIT_2026-05-10.json\",\n      \"research/science_program_2026_05/06_outcome_testing/g12_nofill_historical_source_expansion_packet_audit/G12_NOFILL_HIST_SRCEXP_AUDIT_SOURCE_PACKET_ROW_RECOMPUTATION_AUDIT_2026-05-10.md\",\n      \"research/science_program_2026_05/06_outcome_testing/g12_nofill_historical_source_expansion_packet_audit/build_g12_nofill_historical_source_expansion_packet_audit_2026_05_10.py\"\n    ],\n    \"forbidden_live_surface_paths\": [],\n    \"ok\": true\n  },\n  \"failures\": [\n    \"hash mismatch: parser_or_verifier:builder research\\\\science_program_2026_05\\\\06_outcome_testing\\\\nofill_historical_source_expansion_builder_local_tick_shadow_packet\\\\build_nofill_historical_source_expansion_builder_local_tick_shadow_packet_2026_05_10.py\",\n    \"hash mismatch: parser_or_verifier:focused_tests research\\\\science_program_2026_05\\\\06_outcome_testing\\\\nofill_historical_source_expansion_builder_local_tick_shadow_packet\\\\test_nofill_historical_source_expansion_builder_local_tick_shadow_packet_2026_05_10.py\",\n    \"hash mismatch: parser_or_verifier:verifier research\\\\science_program_2026_05\\\\06_outcome_testing\\\\nofill_historical_source_expansion_builder_local_tick_shadow_packet\\\\verify_nofill_historical_source_expansion_builder_local_tick_shadow_packet_2026_05_10.py\"\n  ],\n  \"field_count\": 55,\n  \"future20_field_count\": 20,\n  \"live_effect\": false,\n  \"ok\": false,\n  \"outcome_review_opened\": false,\n  \"packet_row_count\": 2,\n  \"promotion_verdict\": \"NO_PROMOTION_VERDICT\",\n  \"route_id\": \"NOFILL_HISTORICAL_SOURCE_EXPANSION_BUILDER_LOCAL_TICK_SHADOW_PACKET\",\n  \"schema_version\": \"nofill_historical_source_expansion_builder_local_tick_shadow_packet_v1_verifier_v1\",\n  \"terminal_decision\": \"ACCEPT_SOURCE_HASHED_INPUT_PACKET_READY_FOR_G12_SOURCE_CONTROL_AUDIT\",\n  \"validation_safe\": false\n}\n"
  },
  "validation_safe": false
}
```
