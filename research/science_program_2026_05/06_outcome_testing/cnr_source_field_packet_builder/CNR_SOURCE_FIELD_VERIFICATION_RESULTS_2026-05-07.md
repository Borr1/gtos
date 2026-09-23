# CNR Source Field Verification Results - 2026-05-07

Promotion verdict: `NO_PROMOTION_VERDICT`  
Validation safe: `false`  
Outcome review opened: `false`  
Live effect: `false`

## Verification

```json
{
  "account_history_accessed": false,
  "api_calls": 0,
  "artifact_family": "CNR_SOURCE_FIELD_VERIFICATION_RESULTS",
  "blocked_packet_outcome_source_read": false,
  "broker_actual_r_accessed": false,
  "commands": [
    {
      "command": "python -m py_compile build/verify/test scripts",
      "status": "PASS"
    },
    {
      "blocked_rows": 6098,
      "command": "python build_cnr_source_field_packet_builder_2026_05_07.py",
      "forbidden_scan_status": "PASS",
      "ready_rows": 102,
      "row_count": 6200,
      "status": "PASS"
    },
    {
      "command": "python verify_cnr_source_field_packet_builder_2026_05_07.py",
      "quote_rows": 2368,
      "ready_rows": 102,
      "row_count": 6200,
      "status": "PASS"
    },
    {
      "command": "python -m pytest test_cnr_source_field_packet_builder_2026_05_07.py -q",
      "status": "PASS",
      "tests": 4,
      "warnings": [
        "Pytest cache path creation denied under workspace; no test failure."
      ]
    },
    {
      "artifact_flag_issues": [],
      "command": "custom artifact flag and forbidden row-key scan",
      "row_forbidden_key_issue_count": 0,
      "status": "PASS"
    },
    {
      "command": "git diff/status scope inspection",
      "evidence": "Tracked diff before commit was .context/LIVE_STATE.md from mandatory preflight; untracked deliverables are under cnr_source_field_packet_builder; no src/prompts/config/risk/execution/safety/canary/credential/remote/order-path files were edited.",
      "status": "PASS_WITH_ENV_WARNING"
    }
  ],
  "databento_calls": 0,
  "environment_warnings": [
    {
      "impact": "git status emits a warning for this untracked temp directory; it is not a committed artifact and not used by the lane.",
      "path": "pytest-cache-files-rdqwx32e",
      "status": "UNREMOVABLE_BY_CURRENT_USER_AFTER_SANDBOX_AND_ESCALATED_ATTEMPTS"
    }
  ],
  "generated_at_utc": "2026-05-07T14:54:30Z",
  "live_effect": false,
  "live_order_state_accessed": false,
  "live_trade_results_accessed": false,
  "mt5_order_calls": 0,
  "order_calls": 0,
  "outcome_review_opened": false,
  "paid_data_calls": 0,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "validation_safe": false,
  "verification_status": "PASS_WITH_ENVIRONMENT_WARNING"
}
```
