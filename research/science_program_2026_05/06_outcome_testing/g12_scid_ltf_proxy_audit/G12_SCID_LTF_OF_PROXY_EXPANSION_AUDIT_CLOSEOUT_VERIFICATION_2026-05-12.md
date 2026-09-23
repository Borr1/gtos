# Closeout Verification

```json
{
  "artifact_family": "closeout_verification",
  "changes_live_trading_behavior": false,
  "closeout_ok": true,
  "credentials_touched": false,
  "evidence_class": "G12_SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_AUDIT_ONLY",
  "g12_audit_focused_pytest": {
    "returncode": 0,
    "status": "passed_after_focused_pytest_command",
    "test_path": "research/science_program_2026_05/06_outcome_testing/g12_scid_ltf_proxy_audit/test_g12_ltf_proxy_audit_2026_05_12.py"
  },
  "g12_audit_focused_tests_ok": true,
  "g12_audit_verifier": {
    "failures": [],
    "result_path": "research/science_program_2026_05/06_outcome_testing/g12_scid_ltf_proxy_audit/G12_SCID_LTF_OF_PROXY_EXPANSION_AUDIT_VERIFICATION_RESULT_2026-05-12.json",
    "returncode": 0,
    "status": "passed"
  },
  "g12_audit_verifier_ok": true,
  "generated_at_utc": "2026-05-12T07:45:57Z",
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
  "route_id": "G12_SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_AUDIT",
  "schema_version": "g12_scid_ltf_orderflow_proxy_source_expansion_audit_v1",
  "source_route_focused_pytest": {
    "args": [
      "python",
      "-m",
      "pytest",
      "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/test_scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis_2026_05_12.py",
      "-q",
      "-p",
      "no:cacheprovider",
      "--basetemp=tmp_codex_probe/pytest_scid_ltf_proxy_source_route_g12_audit"
    ],
    "returncode": 0,
    "stderr_tail": "",
    "stdout_tail": "......                                                                   [100%]\n6 passed in 0.23s\n"
  },
  "source_route_focused_tests_ok": true,
  "source_route_verifier": {
    "args": [
      "python",
      "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/verify_scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis_2026_05_12.py"
    ],
    "returncode": 0,
    "stderr_tail": "",
    "stdout_tail": "OXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json\",\n    \"research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.md\",\n    \"research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_CANDIDATE_COVERAGE_MATRIX_2026-05-12.json\",\n    \"research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_CANDIDATE_COVERAGE_MATRIX_2026-05-12.md\",\n    \"research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json\",\n    \"research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.md\",\n    \"research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ASOF_NOLEAK_DUPLICATE_POLICY_2026-05-12.json\",\n    \"research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ASOF_NOLEAK_DUPLICATE_POLICY_2026-05-12.md\",\n    \"research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_APPROVAL_GATE_LEDGER_2026-05-12.json\",\n    \"research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_APPROVAL_GATE_LEDGER_2026-05-12.md\",\n    \"research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_SATURATION_REDTEAM_LEDGER_2026-05-12.json\",\n    \"research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_SATURATION_REDTEAM_LEDGER_2026-05-12.md\",\n    \"research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_DECISION_LEDGER_2026-05-12.json\",\n    \"research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_DECISION_LEDGER_2026-05-12.md\",\n    \"research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_OUTPUT_MANIFEST_2026-05-12.json\",\n    \"research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_OUTPUT_MANIFEST_2026-05-12.md\",\n    \"research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_COMPLETION_AUDIT_2026-05-12.json\",\n    \"research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_COMPLETION_AUDIT_2026-05-12.md\",\n    \"research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_CLOSEOUT_VERIFICATION_2026-05-12.json\",\n    \"research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_CLOSEOUT_VERIFICATION_2026-05-12.md\"\n  ],\n  \"route_id\": \"SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS\",\n  \"scoped_git_status\": {\n    \"no_scoped_forbidden_live_surface\": true,\n    \"no_scoped_raw_market_blob\": true,\n    \"returncode\": 0,\n    \"scoped_entries\": [\n      {\n        \"path\": \"research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_VERIFICATION_RESULT_2026-05-12.json\",\n        \"scoped\": true,\n        \"scoped_forbidden_live_surface\": false,\n        \"scoped_raw_market_blob\": false,\n        \"status\": \" M\"\n      }\n    ],\n    \"stderr\": [\n      \"warning: unable to access 'C:\\\\Users\\\\MSI/.config/git/ignore': Permission denied\",\n      \"warning: unable to access 'C:\\\\Users\\\\MSI/.config/git/ignore': Permission denied\"\n    ],\n    \"unrelated_dirty_entry_count\": 2\n  },\n  \"source_category_count\": 12,\n  \"source_inventory_count\": 844,\n  \"syntax\": {\n    \"failures\": [],\n    \"method\": \"ast_parse_no_bytecode\",\n    \"ok\": true\n  },\n  \"terminal_decision\": \"BUILT_SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_G12_AUDIT_REQUIRED\",\n  \"verification_note\": \"Focused pytest must also pass; this verifier does not open validation or raw/live surfaces.\"\n}\n"
  },
  "source_route_verifier_ok": true,
  "terminal_decision": "ACCEPT_AS_G12_SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_CONTROL_EVIDENCE_ONLY",
  "validation_safe": false
}
```
