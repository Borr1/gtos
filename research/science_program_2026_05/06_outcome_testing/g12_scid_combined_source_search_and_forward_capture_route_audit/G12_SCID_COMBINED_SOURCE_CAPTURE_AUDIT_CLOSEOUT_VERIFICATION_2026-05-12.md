# Closeout Verification

```json
{
  "artifact_family": "closeout_verification",
  "builder_result": {
    "blockers": [],
    "candidate_rows": 3014,
    "ok": true,
    "terminal_decision": "ACCEPT_AS_G12_SCID_COMBINED_SOURCE_CAPTURE_ROUTE_CONTROL_EVIDENCE_ONLY_WITH_MANIFEST_BINDING_REPAIR"
  },
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "evidence_class": "G12_SCID_COMBINED_SOURCE_CAPTURE_ROUTE_AUDIT_ONLY",
  "focused_pytest": {
    "args": [
      "C:\\Python313\\python.exe",
      "-m",
      "pytest",
      "-q",
      "research/science_program_2026_05/06_outcome_testing/g12_scid_combined_source_search_and_forward_capture_route_audit/test_g12_scid_combined_source_search_and_forward_capture_route_audit_2026_05_12.py",
      "--basetemp=tmp_codex_probe/pytest_g12_scid_combined_source_capture_audit"
    ],
    "returncode": 0,
    "status": "PASSED",
    "stderr_tail": "",
    "stdout_tail": ".....                                                                    [100%]\n============================== warnings summary ===============================\n..\\..\\AppData\\Roaming\\Python\\Python313\\site-packages\\_pytest\\cacheprovider.py:475\n  C:\\Users\\MSI\\AppData\\Roaming\\Python\\Python313\\site-packages\\_pytest\\cacheprovider.py:475: PytestCacheWarning: could not create cache path C:\\Users\\MSI\\Documents\\ai-trading-agent\\.pytest_cache\\v\\cache\\nodeids: [WinError 5] Access is denied: 'C:\\\\Users\\\\MSI\\\\Documents\\\\ai-trading-agent\\\\.pytest_cache\\\\v\\\\cache'\n    config.cache.set(\"cache/nodeids\", sorted(self.cached_nodeids))\n\n-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html\n5 passed, 1 warning in 0.30s\n"
  },
  "generated_at_utc": "2026-05-12T02:04:12Z",
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
  "py_compile": {
    "args": [
      "C:\\Python313\\python.exe",
      "-c",
      "import pathlib, py_compile; out=pathlib.Path('tmp_codex_probe/pyc_g12_scid_combined_source_capture_audit'); out.mkdir(parents=True, exist_ok=True); files=['research/science_program_2026_05/06_outcome_testing/g12_scid_combined_source_search_and_forward_capture_route_audit/build_g12_scid_combined_source_search_and_forward_capture_route_audit_2026_05_12.py', 'research/science_program_2026_05/06_outcome_testing/g12_scid_combined_source_search_and_forward_capture_route_audit/verify_g12_scid_combined_source_search_and_forward_capture_route_audit_2026_05_12.py', 'research/science_program_2026_05/06_outcome_testing/g12_scid_combined_source_search_and_forward_capture_route_audit/test_g12_scid_combined_source_search_and_forward_capture_route_audit_2026_05_12.py']; [py_compile.compile(f, cfile=str(out/(pathlib.Path(f).stem+'.pyc')), doraise=True) for f in files]; print('custom py_compile ok')"
    ],
    "returncode": 0,
    "status": "PASSED",
    "stderr_tail": "",
    "stdout_tail": "custom py_compile ok\n"
  },
  "route_id": "G12_SCID_COMBINED_SOURCE_SEARCH_AND_FORWARD_CAPTURE_ROUTE_AUDIT",
  "safe_flags": {
    "NO_PROMOTION_VERDICT": true,
    "live_effect": false,
    "outcome_review_opened": false,
    "validation_safe": false
  },
  "schema_version": "g12_scid_combined_source_capture_route_audit_v1",
  "scoped_commit": "f67e807e research: accept g12 scid combined source capture audit",
  "standalone_verifier": {
    "args": [
      "C:\\Python313\\python.exe",
      "research/science_program_2026_05/06_outcome_testing/g12_scid_combined_source_search_and_forward_capture_route_audit/verify_g12_scid_combined_source_search_and_forward_capture_route_audit_2026_05_12.py"
    ],
    "returncode": 0,
    "status": "PASSED",
    "stderr_tail": "",
    "stdout_tail": "     \"scoped\": false,\n        \"scoped_forbidden_live_surface\": false,\n        \"scoped_raw_market_blob\": false,\n        \"status\": \"??\"\n      },\n      {\n        \"path\": \"research/program_control/LTO019_DERIVED_LOG_REPAIR_20260512_073108.json\",\n        \"scoped\": false,\n        \"scoped_forbidden_live_surface\": false,\n        \"scoped_raw_market_blob\": false,\n        \"status\": \"??\"\n      },\n      {\n        \"path\": \"research/program_control/LTO019_decision_layer_diagnostics_join_pre_repair_20260512_073108.jsonl\",\n        \"scoped\": false,\n        \"scoped_forbidden_live_surface\": false,\n        \"scoped_raw_market_blob\": false,\n        \"status\": \"??\"\n      },\n      {\n        \"path\": \"research/program_control/ML_SHADOW_PREDICTIONS_POINTER_HEADER_PRE_REPAIR_20260512_073616.jsonl\",\n        \"scoped\": false,\n        \"scoped_forbidden_live_surface\": false,\n        \"scoped_raw_market_blob\": false,\n        \"status\": \"??\"\n      },\n      {\n        \"path\": \"research/program_control/ML_SHADOW_PREDICTIONS_POINTER_HEADER_REPAIR_20260512_073616.json\",\n        \"scoped\": false,\n        \"scoped_forbidden_live_surface\": false,\n        \"scoped_raw_market_blob\": false,\n        \"status\": \"??\"\n      },\n      {\n        \"path\": \"research/science_program_2026_05/04_goal_prompts/G0_SCID_COMBINED_SOURCE_CAPTURE_ROUTE_SYNTHESIS_CONTROL_PROMPT_2026-05-12.md\",\n        \"scoped\": true,\n        \"scoped_forbidden_live_surface\": false,\n        \"scoped_raw_market_blob\": false,\n        \"status\": \"??\"\n      },\n      {\n        \"path\": \"research/science_program_2026_05/06_outcome_testing/g12_scid_combined_source_search_and_forward_capture_route_audit/\",\n        \"scoped\": true,\n        \"scoped_forbidden_live_surface\": false,\n        \"scoped_raw_market_blob\": false,\n        \"status\": \"??\"\n      },\n      {\n        \"path\": \"shadow_logs/nofill_forward_source_capture.jsonl\",\n        \"scoped\": false,\n        \"scoped_forbidden_live_surface\": false,\n        \"scoped_raw_market_blob\": false,\n        \"status\": \"??\"\n      },\n      {\n        \"path\": \"shadow_logs/operator_market_intelligence.jsonl\",\n        \"scoped\": false,\n        \"scoped_forbidden_live_surface\": false,\n        \"scoped_raw_market_blob\": false,\n        \"status\": \"??\"\n      },\n      {\n        \"path\": \"shadow_logs/source_diagnostic_intelligence.jsonl\",\n        \"scoped\": false,\n        \"scoped_forbidden_live_surface\": false,\n        \"scoped_raw_market_blob\": false,\n        \"status\": \"??\"\n      },\n      {\n        \"path\": \"shadow_logs/time_in_trade.jsonl\",\n        \"scoped\": false,\n        \"scoped_forbidden_live_surface\": false,\n        \"scoped_raw_market_blob\": false,\n        \"status\": \"??\"\n      }\n    ],\n    \"no_scoped_forbidden_live_surface\": true,\n    \"no_scoped_raw_market_blob\": true,\n    \"returncode\": 0,\n    \"scoped_entries\": [\n      {\n        \"path\": \".context/LIVE_STATE.md\",\n        \"scoped\": true,\n        \"scoped_forbidden_live_surface\": false,\n        \"scoped_raw_market_blob\": false,\n        \"status\": \" M\"\n      },\n      {\n        \"path\": \"research/science_program_2026_05/04_goal_prompts/G0_SCID_COMBINED_SOURCE_CAPTURE_ROUTE_SYNTHESIS_CONTROL_PROMPT_2026-05-12.md\",\n        \"scoped\": true,\n        \"scoped_forbidden_live_surface\": false,\n        \"scoped_raw_market_blob\": false,\n        \"status\": \"??\"\n      },\n      {\n        \"path\": \"research/science_program_2026_05/06_outcome_testing/g12_scid_combined_source_search_and_forward_capture_route_audit/\",\n        \"scoped\": true,\n        \"scoped_forbidden_live_surface\": false,\n        \"scoped_raw_market_blob\": false,\n        \"status\": \"??\"\n      }\n    ],\n    \"stderr\": [\n      \"warning: unable to access 'C:\\\\Users\\\\MSI/.config/git/ignore': Permission denied\",\n      \"warning: unable to access 'C:\\\\Users\\\\MSI/.config/git/ignore': Permission denied\"\n    ]\n  },\n  \"syntax_parse\": {\n    \"failures\": [],\n    \"method\": \"ast_parse_no_bytecode\",\n    \"ok\": true\n  },\n  \"terminal_decision\": \"ACCEPT_AS_G12_SCID_COMBINED_SOURCE_CAPTURE_ROUTE_CONTROL_EVIDENCE_ONLY_WITH_MANIFEST_BINDING_REPAIR\"\n}\n"
  },
  "terminal_decision": "ACCEPT_AS_G12_SCID_COMBINED_SOURCE_CAPTURE_ROUTE_CONTROL_EVIDENCE_ONLY_WITH_MANIFEST_BINDING_REPAIR",
  "validation_safe": false
}
```
