# G12 SCID FC Impl Design Audit Target Verifier And Focused Tests

```json
{
  "artifact_type": "target_verifier_and_focused_tests_audit",
  "evidence_class": "G12_SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE_AUDIT_ONLY",
  "generated_at_utc": "2026-05-12T08:02:20Z",
  "route_id": "G12_SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE_AUDIT",
  "safe_flags": {
    "live_effect": false,
    "opens_ai_api": false,
    "opens_broker_account_order_history_deal_position_evidence": false,
    "opens_live_behavior": false,
    "opens_live_restart": false,
    "opens_paid_vendor_access": false,
    "opens_prompt_config_risk_safety_execution_canary_selector_change": false,
    "opens_raw_market_data_blob_commit": false,
    "opens_registry_edit": false,
    "opens_remote_push": false,
    "opens_result_scoring": false,
    "opens_strategy_edge_review": false,
    "opens_validation": false,
    "outcome_review_opened": false,
    "promotion_verdict": "NO_PROMOTION_VERDICT",
    "validation_safe": false
  },
  "target_focused_pytest_command": "python -m pytest -q -p no:cacheprovider --junitxml=<audit-route>/G12_SCID_FC_IMPL_DESIGN_AUDIT_TARGET_PYTEST_RESULT_2026-05-12.xml research/science_program_2026_05/06_outcome_testing/scid_forward_capture_implementation_design_package_from_offline_schema_synthesis/test_scid_forward_capture_implementation_design_package_2026_05_12.py",
  "target_pytest_status": {
    "errors": 0,
    "failures": 0,
    "path": "G12_SCID_FC_IMPL_DESIGN_AUDIT_TARGET_PYTEST_RESULT_2026-05-12.xml",
    "skipped": 0,
    "status": "passed",
    "tests": 5
  },
  "target_route_restore_policy": "Target verifier/tests are allowed as recomputation evidence but they rewrite target-route generated artifacts; tracked target drift is restored to HEAD after command capture.",
  "target_verifier_command": "python research/science_program_2026_05/06_outcome_testing/scid_forward_capture_implementation_design_package_from_offline_schema_synthesis/verify_scid_forward_capture_implementation_design_package_2026_05_12.py",
  "target_verifier_status": {
    "path": "G12_SCID_FC_IMPL_DESIGN_AUDIT_TARGET_VERIFIER_STDOUT_2026-05-12.json",
    "payload": {
      "can_mark_goal_complete": true,
      "candidate_rows_verified": 3014,
      "capture_groups_verified": 10,
      "evidence_class": "SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE_FROM_OFFLINE_SCHEMA_SYNTHESIS_ONLY",
      "failures": [],
      "generated_at_utc": "2026-05-12T07:51:54Z",
      "git_scope": {
        "disallowed": [],
        "ignored_research": [
          "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_implementation_design_package/build_scid_forward_capture_implementation_design_package_2026_05_12.py",
          "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_implementation_design_package/test_scid_forward_capture_implementation_design_package_2026_05_12.py",
          "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_implementation_design_package/verify_scid_forward_capture_implementation_design_package_2026_05_12.py"
        ],
        "repo_root": "C:\\tmp\\gtos_otb\\SCID_IMPL_DESIGN",
        "status_lines": [
          " M .context/LIVE_STATE.md",
          "?? research/science_program_2026_05/06_outcome_testing/scid_forward_capture_implementation_design_package/build_scid_forward_capture_implementation_design_package_2026_05_12.py",
          "?? research/science_program_2026_05/06_outcome_testing/scid_forward_capture_implementation_design_package/test_scid_forward_capture_implementation_design_package_2026_05_12.py",
          "?? research/science_program_2026_05/06_outcome_testing/scid_forward_capture_implementation_design_package/verify_scid_forward_capture_implementation_design_package_2026_05_12.py"
        ]
      },
      "notes": [
        "Allowed generated context refresh present: .context/LIVE_STATE.md",
        "Ignored sibling research-only untracked files outside this package: research/science_program_2026_05/06_outcome_testing/scid_forward_capture_implementation_design_package/build_scid_forward_capture_implementation_design_package_2026_05_12.py, research/science_program_2026_05/06_outcome_testing/scid_forward_capture_implementation_design_package/test_scid_forward_capture_implementation_design_package_2026_05_12.py, research/science_program_2026_05/06_outcome_testing/scid_forward_capture_implementation_design_package/verify_scid_forward_capture_implementation_design_package_2026_05_12.py"
      ],
      "ok": true,
      "pytest_status": {
        "errors": 0,
        "failures": 0,
        "path": "SCID_FC_IMPL_DESIGN_PYTEST_RESULT_2026-05-12.xml",
        "skipped": 0,
        "status": "passed",
        "tests": 5
      },
      "route_id": "SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE_FROM_OFFLINE_SCHEMA_SYNTHESIS",
      "safe_flags": {
        "ai_api_call_opened": false,
        "broker_or_account_evidence_opened": false,
        "canary_or_selector_change_opened": false,
        "config_change_opened": false,
        "evidence_class": "SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE_FROM_OFFLINE_SCHEMA_SYNTHESIS_ONLY",
        "execution_logic_change_opened": false,
        "live_effect": false,
        "outcome_review_opened": false,
        "paid_vendor_call_opened": false,
        "performance_claim_opened": false,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "prompt_change_opened": false,
        "raw_blob_capture_opened": false,
        "result_scoring_opened": false,
        "risk_logic_change_opened": false,
        "validation_safe": false
      },
      "warnings": []
    },
    "status": "passed"
  }
}
```
