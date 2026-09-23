# Verifier Test And Scoped Dirty Audit

- route_id: `G12_SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION_AUDIT`
- evidence_class: `G12_SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION_AUDIT_ONLY`
- terminal_decision: `n/a`
- status: `PASS`

```json
{
  "artifact_family": "verifier_test_scoped_dirty_audit",
  "dirty_state_policy": "Only the G12 audit route, the controlling prompt if edited by the builder route, mandatory preflight LIVE_STATE dirt, and research_current_state context refresh are in scope. Runtime or sibling-worktree dirt is informational unless it touches a forbidden surface.",
  "evidence_class": "G12_SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION_AUDIT_ONLY",
  "failures": [],
  "forbidden_scoped_dirty_rows": [],
  "generated_at_utc": "2026-05-12T07:34:34Z",
  "git_status_short": "M .context/LIVE_STATE.md\n M research/science_program_2026_05/06_outcome_testing/scid_forward_capture_readonly_monitoring_alignment_expansion/SCID_FORWARD_CAPTURE_READONLY_ALIGNMENT_EXPANSION_VERIFICATION_RESULT_2026-05-12.json\n?? research/science_program_2026_05/06_outcome_testing/g12_scid_forward_capture_readonly_monitoring_alignment_expansion_audit/\nwarning: unable to access 'C:\\Users\\MSI/.config/git/ignore': Permission denied\nwarning: unable to access 'C:\\Users\\MSI/.config/git/ignore': Permission denied",
  "input_route_command_results": [
    {
      "command": "python C:\\tmp\\gtos_otb\\SCID_READONLY_ALIGN\\research\\science_program_2026_05\\06_outcome_testing\\scid_forward_capture_readonly_monitoring_alignment_expansion\\verify_scid_forward_capture_readonly_monitoring_alignment_expansion_2026_05_12.py",
      "passed": true,
      "returncode": 0,
      "stderr_tail": "",
      "stdout_tail": "pens_live_restart\": false,\n        \"opens_live_trading_behavior\": false,\n        \"opens_paid_or_vendor_access\": false,\n        \"opens_prompt_config_risk_safety_execution_canary_selector_edit\": false,\n        \"opens_raw_market_data_blob_commit\": false,\n        \"opens_registry_edit\": false,\n        \"opens_remote_push\": false,\n        \"opens_result_scoring\": false,\n        \"opens_strategy_edge_claims\": false,\n        \"opens_validation\": false,\n        \"outcome_review_opened\": false,\n        \"promotion_verdict\": \"NO_PROMOTION_VERDICT\",\n        \"route_id\": \"SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION\",\n        \"schema_version\": \"scid_forward_capture_readonly_alignment_expansion_v1\",\n        \"static_excluded_roots\": [\n          {\n            \"exists\": true,\n            \"path\": \"data\",\n            \"reason\": \"raw market/history/tick blobs excluded by route boundary\"\n          },\n          {\n            \"exists\": true,\n            \"path\": \"data/ticks\",\n            \"reason\": \"raw tick parquet/blob content excluded\"\n          },\n          {\n            \"exists\": true,\n            \"path\": \"knowledge_base/trade_records\",\n            \"reason\": \"trade/broker record evidence excluded\"\n          },\n          {\n            \"exists\": true,\n            \"path\": \"prompts\",\n            \"reason\": \"production prompt surface excluded from changes and not needed for shape map\"\n          },\n          {\n            \"exists\": true,\n            \"path\": \"config\",\n            \"reason\": \"risk/config/live behavior surface excluded\"\n          },\n          {\n            \"exists\": true,\n            \"path\": \"src/components/execution.py\",\n            \"reason\": \"execution/live behavior surface excluded\"\n          },\n          {\n            \"exists\": true,\n            \"path\": \"src/components/permissions.py\",\n            \"reason\": \"safety/live decision surface excluded\"\n          },\n          {\n            \"exists\": true,\n            \"path\": \"scripts/canary_test.py\",\n            \"reason\": \"canary selector/evaluation surface excluded\"\n          }\n        ],\n        \"validation_safe\": false\n      },\n      \"status\": \"PASS\"\n    },\n    {\n      \"check\": \"fingerprint_manifest_count_positive\",\n      \"detail\": 2551,\n      \"status\": \"PASS\"\n    },\n    {\n      \"check\": \"fingerprint_manifest_no_raw_blob_rows\",\n      \"detail\": [],\n      \"status\": \"PASS\"\n    },\n    {\n      \"check\": \"g12_prompt_contains_required_boundaries_and_decisions\",\n      \"detail\": [],\n      \"status\": \"PASS\"\n    },\n    {\n      \"check\": \"output_manifest_includes_g12_prompt\",\n      \"detail\": \"research/science_program_2026_05/04_goal_prompts/G12_SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION_AUDIT_GOAL_PROMPT_2026-05-12.md\",\n      \"status\": \"PASS\"\n    },\n    {\n      \"check\": \"output_manifest_no_raw_market_blobs\",\n      \"detail\": [],\n      \"status\": \"PASS\"\n    },\n    {\n      \"check\": \"json_md_pairs_match\",\n      \"detail\": [],\n      \"status\": \"PASS\"\n    },\n    {\n      \"check\": \"scoped_git_surface_only_route_prompt_context\",\n      \"detail\": {\n        \"forbidden_scoped\": [],\n        \"scoped_entries\": [\n          {\n            \"path\": \".context/LIVE_STATE.md\",\n            \"status\": \"M\"\n          },\n          {\n            \"path\": \"research/science_program_2026_05/06_outcome_testing/scid_forward_capture_readonly_monitoring_alignment_expansion/SCID_FORWARD_CAPTURE_READONLY_ALIGNMENT_EXPANSION_VERIFICATION_RESULT_2026-05-12.json\",\n            \"status\": \"M\"\n          }\n        ]\n      },\n      \"status\": \"PASS\"\n    }\n  ],\n  \"evidence_class\": \"SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION_ONLY\",\n  \"failed_check_count\": 0,\n  \"failed_checks\": [],\n  \"live_effect\": false,\n  \"ok\": true,\n  \"outcome_review_opened\": false,\n  \"promotion_verdict\": \"NO_PROMOTION_VERDICT\",\n  \"route_id\": \"SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION\",\n  \"terminal_decision\": \"VERIFIED_SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION_READY_FOR_G12_AUDIT\",\n  \"validation_safe\": false\n}\n"
    },
    {
      "command": "python -m pytest C:\\tmp\\gtos_otb\\SCID_READONLY_ALIGN\\research\\science_program_2026_05\\06_outcome_testing\\scid_forward_capture_readonly_monitoring_alignment_expansion\\test_scid_forward_capture_readonly_monitoring_alignment_expansion_2026_05_12.py -q",
      "passed": true,
      "returncode": 0,
      "stderr_tail": "",
      "stdout_tail": ".....                                                                    [100%]\n5 passed in 0.15s\n"
    }
  ],
  "live_effect": false,
  "opens_ai_api": false,
  "opens_broker_account_order_history_deal_position_evidence": false,
  "opens_live_trading_behavior": false,
  "opens_paid_or_vendor_access": false,
  "opens_prompt_config_risk_safety_execution_canary_selector_edit": false,
  "opens_raw_market_data_blob_commit": false,
  "opens_result_scoring": false,
  "opens_strategy_edge_claims": false,
  "opens_validation": false,
  "outcome_review_opened": false,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "route_id": "G12_SCID_FORWARD_CAPTURE_READONLY_MONITORING_ALIGNMENT_EXPANSION_AUDIT",
  "scoped_dirty_rows": [
    {
      "path": "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_readonly_monitoring_alignment_expansion/SCID_FORWARD_CAPTURE_READONLY_ALIGNMENT_EXPANSION_VERIFICATION_RESULT_2026-05-12.json",
      "status": " M"
    },
    {
      "path": "research/science_program_2026_05/06_outcome_testing/g12_scid_forward_capture_readonly_monitoring_alignment_expansion_audit/",
      "status": "??"
    }
  ],
  "status": "PASS",
  "unscoped_dirty_rows_informational": [
    {
      "path": "context/LIVE_STATE.md",
      "status": "M "
    }
  ],
  "validation_safe": false
}
```
