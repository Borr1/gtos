# Target Verifier Test Rerun Ledger

```json
{
  "artifact_family": "target_verifier_test_rerun_ledger",
  "changes_trading_risk_safety_prompt_decision_behavior": false,
  "credentials_touched": false,
  "evidence_class": "G12_SCID_FUTURE_CAPTURE_BLOCKED15_SOURCE_STATE_AUDIT_ONLY",
  "failures": [],
  "generated_at_utc": "2026-05-12T18:13:14Z",
  "live_effect": false,
  "ok": true,
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
  "route_id": "G12_SCID_FUTURE_CAPTURE_BLOCKED15_SOURCE_STATE_MATERIALIZATION_AUDIT",
  "target_evidence_class": "SCID_FUTURE_CAPTURE_FIELD_SOURCE_STATE_MATERIALIZATION_ONLY",
  "target_focused_pytest_command": {
    "command": [
      "python",
      "-m",
      "pytest",
      "research\\science_program_2026_05\\06_outcome_testing\\scid_future_capture_field_source_state_materialization_for_blocked15\\test_scid_future_capture_blocked15_materialization_2026_05_12.py",
      "-q"
    ],
    "ok": true,
    "returncode": 0,
    "stderr": [],
    "stdout": [
      ".....                                                                    [100%]",
      "5 passed in 0.45s"
    ]
  },
  "target_focused_tests_ok": true,
  "target_pytest_stdout_summary": [
    ".....                                                                    [100%]",
    "5 passed in 0.45s"
  ],
  "target_route_id": "SCID_FUTURE_CAPTURE_FIELD_SOURCE_STATE_MATERIALIZATION_FOR_BLOCKED15",
  "target_verifier_command": {
    "command": [
      "python",
      "research\\science_program_2026_05\\06_outcome_testing\\scid_future_capture_field_source_state_materialization_for_blocked15\\verify_scid_future_capture_blocked15_materialization_2026_05_12.py",
      "--json"
    ],
    "ok": true,
    "returncode": 0,
    "stderr": [],
    "stdout": [
      "{",
      "  \"can_mark_goal_complete\": true,",
      "  \"evidence_class\": \"SCID_FUTURE_CAPTURE_FIELD_SOURCE_STATE_MATERIALIZATION_ONLY\",",
      "  \"failure_count\": 0,",
      "  \"failures\": [],",
      "  \"live_effect\": false,",
      "  \"ok\": true,",
      "  \"opens_ai_api\": false,",
      "  \"opens_broker_account_order_history_deal_position_evidence\": false,",
      "  \"opens_live_restart\": false,",
      "  \"opens_live_trading_behavior\": false,",
      "  \"opens_paid_or_vendor_access\": false,",
      "  \"opens_prompt_config_risk_safety_execution_canary_selector_edit\": false,",
      "  \"opens_raw_market_data_blob_commit\": false,",
      "  \"opens_result_scoring\": false,",
      "  \"opens_strategy_edge_claims\": false,",
      "  \"opens_validation\": false,",
      "  \"outcome_review_opened\": false,",
      "  \"promotion_verdict\": \"NO_PROMOTION_VERDICT\",",
      "  \"recovered_row_validation\": {",
      "    \"failure_count\": 0,",
      "    \"failures\": [],",
      "    \"ok\": true,",
      "    \"row_count\": 1213",
      "  },",
      "  \"route_id\": \"SCID_FUTURE_CAPTURE_FIELD_SOURCE_STATE_MATERIALIZATION_FOR_BLOCKED15\",",
      "  \"validation_safe\": false",
      "}"
    ]
  },
  "target_verifier_ok": true,
  "target_verifier_stdout_summary": [
    "{",
    "  \"can_mark_goal_complete\": true,",
    "  \"evidence_class\": \"SCID_FUTURE_CAPTURE_FIELD_SOURCE_STATE_MATERIALIZATION_ONLY\",",
    "  \"failure_count\": 0,",
    "  \"failures\": [],",
    "  \"live_effect\": false,",
    "  \"ok\": true,",
    "  \"opens_ai_api\": false,",
    "  \"opens_broker_account_order_history_deal_position_evidence\": false,",
    "  \"opens_live_restart\": false,",
    "  \"opens_live_trading_behavior\": false,",
    "  \"opens_paid_or_vendor_access\": false,",
    "  \"opens_prompt_config_risk_safety_execution_canary_selector_edit\": false,",
    "  \"opens_raw_market_data_blob_commit\": false,",
    "  \"opens_result_scoring\": false,",
    "  \"opens_strategy_edge_claims\": false,",
    "  \"opens_validation\": false,",
    "  \"outcome_review_opened\": false,",
    "  \"promotion_verdict\": \"NO_PROMOTION_VERDICT\",",
    "  \"recovered_row_validation\": {"
  ],
  "validation_safe": false
}
```
