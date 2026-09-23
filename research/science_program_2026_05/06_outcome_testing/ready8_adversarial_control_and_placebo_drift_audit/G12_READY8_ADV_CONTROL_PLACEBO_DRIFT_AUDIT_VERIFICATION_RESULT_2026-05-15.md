# Verification Result

```json
{
  "artifact_family": "verification_result",
  "can_mark_goal_complete": true,
  "changes_trading_risk_safety_prompt_decision_behavior": false,
  "classification_counts_verified": {
    "FULLY_EXPLAINED_BY_ADV_CONTROL_DRIFT": 2608,
    "MATERIALLY_WEAKENED_BY_ADV_CONTROL_DRIFT": 14,
    "NOT_NUMERIC_NOT_ADJUSTABLE": 3622,
    "RESIDUAL_PRESERVED_AFTER_ADV_CONTROL_ENVELOPE": 1,
    "UNDERPOWERED_PRESERVED_NOT_DECISION": 4318
  },
  "evidence_class": "G12_READY8_ADV_CONTROL_PLACEBO_DRIFT_AUDIT_REVIEW_ONLY",
  "expected_counts_verified": {
    "adv001_placebo": 4288,
    "adv003_placebo": 12611,
    "baseline_drift": 3546,
    "comparison_mapping": 10563,
    "concentration": 79746,
    "duplicate_artifact": 3270,
    "explained_weakened": 2622,
    "residual": 1,
    "stress_vs_sealed": 45913,
    "underpower": 79746
  },
  "failure_count": 0,
  "failures": [],
  "focused_tests_marked_ok": true,
  "live_effect": false,
  "ok": true,
  "opens_ai_api": false,
  "opens_broker_account_order_history_deal_position_evidence": false,
  "opens_live_trading_behavior": false,
  "opens_paid_or_vendor_access": false,
  "opens_prompt_config_risk_safety_execution_canary_selector_edit": false,
  "opens_raw_market_data_blob_commit": false,
  "opens_registry_edit": false,
  "opens_remote_push": false,
  "outcome_review_opened": false,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "route_id": "G12_READY8_ADV_CONTROL_PLACEBO_DRIFT_AUDIT",
  "scoped_git_status": {
    "no_forbidden_live_surface": true,
    "no_raw_market_blob": true,
    "returncode": 0,
    "scoped_entries": [
      {
        "forbidden_live_surface": false,
        "path": "research/science_program_2026_05/06_outcome_testing/ready8_adversarial_control_and_placebo_drift_audit/G12_READY8_ADV_CONTROL_PLACEBO_DRIFT_AUDIT_OUTPUT_MANIFEST_2026-05-15.json",
        "raw_market_blob": false,
        "scoped": true,
        "status": " M"
      },
      {
        "forbidden_live_surface": false,
        "path": "research/science_program_2026_05/06_outcome_testing/ready8_adversarial_control_and_placebo_drift_audit/G12_READY8_ADV_CONTROL_PLACEBO_DRIFT_AUDIT_OUTPUT_MANIFEST_2026-05-15.md",
        "raw_market_blob": false,
        "scoped": true,
        "status": " M"
      },
      {
        "forbidden_live_surface": false,
        "path": "research/science_program_2026_05/06_outcome_testing/ready8_adversarial_control_and_placebo_drift_audit/G12_READY8_ADV_CONTROL_PLACEBO_DRIFT_AUDIT_VERIFICATION_RESULT_2026-05-15.json",
        "raw_market_blob": false,
        "scoped": true,
        "status": " M"
      },
      {
        "forbidden_live_surface": false,
        "path": "research/science_program_2026_05/06_outcome_testing/ready8_adversarial_control_and_placebo_drift_audit/G12_READY8_ADV_CONTROL_PLACEBO_DRIFT_AUDIT_VERIFICATION_RESULT_2026-05-15.md",
        "raw_market_blob": false,
        "scoped": true,
        "status": " M"
      }
    ],
    "stderr": [
      "warning: unable to access 'C:\\Users\\MSI/.config/git/ignore': Permission denied",
      "warning: unable to access 'C:\\Users\\MSI/.config/git/ignore': Permission denied"
    ],
    "unscoped_entry_count": 178
  },
  "syntax_parse": {
    "failures": [],
    "method": "ast_parse_no_bytecode",
    "ok": true
  },
  "terminal_decision": "ACCEPT_AS_G12_READY8_ADV_CONTROL_PLACEBO_DRIFT_AUDIT_CANONICAL_DOWNSTREAM_CONTROL_EVIDENCE_NO_PROMOTION",
  "validation_safe": false
}
```
