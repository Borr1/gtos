# Closeout Verification

- **route_id:** `SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_OFFLINE_SCHEMA_SYNTHESIS`
- **evidence_class:** `SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_OFFLINE_SCHEMA_SYNTHESIS_ONLY`
- **promotion_verdict:** `NO_PROMOTION_VERDICT`
- **validation_safe:** `false`
- **outcome_review_opened:** `false`
- **live_effect:** `false`

```json
{
  "artifact_family": "closeout_verification",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "evidence_class": "SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_OFFLINE_SCHEMA_SYNTHESIS_ONLY",
  "final_live_state_refresh_complete": true,
  "focused_pytest": {
    "command": "python -m pytest -q -p no:cacheprovider research/science_program_2026_05/06_outcome_testing/scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis/test_scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis_2026_05_12.py",
    "observed_result": "6 passed",
    "status": "PASSED"
  },
  "generated_at_utc": "2026-05-12T05:31:11Z",
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
  "planned_commands": [
    "python research/science_program_2026_05/06_outcome_testing/scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis/build_scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis_2026_05_12.py",
    "python research/science_program_2026_05/06_outcome_testing/scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis/verify_scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis_2026_05_12.py",
    "python -m pytest -q -p no:cacheprovider research/science_program_2026_05/06_outcome_testing/scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis/test_scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis_2026_05_12.py",
    "python scripts/generate_live_state.py"
  ],
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "route_id": "SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_FROM_OFFLINE_SCHEMA_SYNTHESIS",
  "schema_version": "scid_no_api_mechanical_hypothesis_factory_offline_schema_v1",
  "scoped_git_status": {
    "forbidden_scoped_entries": [],
    "no_scoped_forbidden_live_surface": true,
    "no_scoped_raw_market_blob": true,
    "returncode": 0,
    "scoped_entry_count": 36,
    "stderr": [
      "warning: unable to access 'C:\\Users\\MSI/.config/git/ignore': Permission denied",
      "warning: unable to access 'C:\\Users\\MSI/.config/git/ignore': Permission denied"
    ]
  },
  "scoped_git_status_at_build": {
    "no_scoped_forbidden_live_surface": true,
    "no_scoped_raw_market_blob": true,
    "returncode": 0,
    "scoped_entries": [
      {
        "path": ".context/LIVE_STATE.md",
        "scoped": true,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/science_program_2026_05/06_outcome_testing/scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis/SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_ACCEPTED_AUDIT_RECONCILIATION_2026-05-12.json",
        "scoped": true,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/science_program_2026_05/06_outcome_testing/scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis/SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_ACCEPTED_AUDIT_RECONCILIATION_2026-05-12.md",
        "scoped": true,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/science_program_2026_05/06_outcome_testing/scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis/SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_ADVERSARIAL_BASELINE_PLACEBO_MATRIX_2026-05-12.json",
        "scoped": true,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/science_program_2026_05/06_outcome_testing/scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis/SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_ADVERSARIAL_BASELINE_PLACEBO_MATRIX_2026-05-12.md",
        "scoped": true,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/science_program_2026_05/06_outcome_testing/scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis/SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_CLOSEOUT_VERIFICATION_2026-05-12.json",
        "scoped": true,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/science_program_2026_05/06_outcome_testing/scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis/SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_CLOSEOUT_VERIFICATION_2026-05-12.md",
        "scoped": true,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/science_program_2026_05/06_outcome_testing/scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis/SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_COMPLETION_AUDIT_2026-05-12.json",
        "scoped": true,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/science_program_2026_05/06_outcome_testing/scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis/SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_COMPLETION_AUDIT_2026-05-12.md",
        "scoped": true,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/science_program_2026_05/06_outcome_testing/scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis/SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_CONTEXT_ANCHOR_2026-05-12.json",
        "scoped": true,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/science_program_2026_05/06_outcome_testing/scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis/SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_CONTEXT_ANCHOR_2026-05-12.md",
        "scoped": true,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/science_program_2026_05/06_outcome_testing/scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis/SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_DECISION_LEDGER_2026-05-12.json",
        "scoped": true,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/science_program_2026_05/06_outcome_testing/scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis/SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_DECISION_LEDGER_2026-05-12.md",
        "scoped": true,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/science_program_2026_05/06_outcome_testing/scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis/SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_FUTURE_NO_API_REPLAY_ROUTE_BUNDLE_2026-05-12.json",
        "scoped": true,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/science_program_2026_05/06_outcome_testing/scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis/SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_FUTURE_NO_API_REPLAY_ROUTE_BUNDLE_2026-05-12.md",
        "scoped": true,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/science_program_2026_05/06_outcome_testing/scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis/SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_FUTURE_RESULT_DESIGN_GATE_LEDGER_2026-05-12.json",
        "scoped": true,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/science_program_2026_05/06_outcome_testing/scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis/SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_FUTURE_RESULT_DESIGN_GATE_LEDGER_2026-05-12.md",
        "scoped": true,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/science_program_2026_05/06_outcome_testing/scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis/SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_G12_G0_AUDIT_PROMPT_PACK_2026-05-12.json",
        "scoped": true,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/science_program_2026_05/06_outcome_testing/scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis/SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_G12_G0_AUDIT_PROMPT_PACK_2026-05-12.md",
        "scoped": true,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/science_program_2026_05/06_outcome_testing/scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis/SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_GENERIC_IDEA_LIST_SATURATION_PROOF_2026-05-12.json",
        "scoped": true,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/science_program_2026_05/06_outcome_testing/scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis/SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_GENERIC_IDEA_LIST_SATURATION_PROOF_2026-05-12.md",
        "scoped": true,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/science_program_2026_05/06_outcome_testing/scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis/SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_HYPOTHESIS_CARD_LEDGER_SUMMARY_2026-05-12.json",
        "scoped": true,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/science_program_2026_05/06_outcome_testing/scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis/SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_HYPOTHESIS_CARD_LEDGER_SUMMARY_2026-05-12.md",
        "scoped": true,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/science_program_2026_05/06_outcome_testing/scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis/SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_MECHANISM_FAMILY_HYPOTHESIS_CATALOG_2026-05-12.json",
        "scoped": true,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/science_program_2026_05/06_outcome_testing/scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis/SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_MECHANISM_FAMILY_HYPOTHESIS_CATALOG_2026-05-12.md",
        "scoped": true,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/science_program_2026_05/06_outcome_testing/scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis/SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_OUTPUT_MANIFEST_2026-05-12.json",
        "scoped": true,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/science_program_2026_05/06_outcome_testing/scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis/SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_OUTPUT_MANIFEST_2026-05-12.md",
        "scoped": true,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/science_program_2026_05/06_outcome_testing/scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis/SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_PREREGISTRATION_READINESS_MATRIX_2026-05-12.json",
        "scoped": true,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/science_program_2026_05/06_outcome_testing/scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis/SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_PREREGISTRATION_READINESS_MATRIX_2026-05-12.md",
        "scoped": true,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/science_program_2026_05/06_outcome_testing/scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis/SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_SCIENCE_DOMAIN_COVERAGE_MATRIX_2026-05-12.json",
        "scoped": true,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/science_program_2026_05/06_outcome_testing/scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis/SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_SCIENCE_DOMAIN_COVERAGE_MATRIX_2026-05-12.md",
        "scoped": true,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/science_program_2026_05/06_outcome_testing/scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis/SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_SOURCE_FIELD_CHECKLIST_2026-05-12.json",
        "scoped": true,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/science_program_2026_05/06_outcome_testing/scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis/SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_SOURCE_FIELD_CHECKLIST_2026-05-12.md",
        "scoped": true,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/science_program_2026_05/06_outcome_testing/scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis/SCID_NO_API_MECH_HYP_FACTORY_OFFLINE_SCHEMA_VERIFICATION_RESULT_2026-05-12.json",
        "scoped": true,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      },
      {
        "path": "research/science_program_2026_05/06_outcome_testing/scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis/verify_scid_no_api_mechanical_hypothesis_factory_from_offline_schema_synthesis_2026_05_12.py",
        "scoped": true,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false,
        "status": " M"
      }
    ],
    "stderr": [
      "warning: unable to access 'C:\\Users\\MSI/.config/git/ignore': Permission denied",
      "warning: unable to access 'C:\\Users\\MSI/.config/git/ignore': Permission denied"
    ],
    "unrelated_dirty_entry_count": 1
  },
  "scoped_research_commit": "539d7764 research: build scid no-api hypothesis factory",
  "standalone_verifier": {
    "failure_count": 0,
    "ok": true,
    "status": "PASSED"
  },
  "status": "COMPLETE_SCOPED_RESEARCH_COMMIT_AND_CONTEXT_REFRESH_READY_FOR_G12_AUDIT",
  "syntax_parse": {
    "failures": [],
    "method": "ast_parse_no_bytecode",
    "ok": true
  },
  "terminal_decision": "BUILT_SCID_NO_API_MECHANICAL_HYPOTHESIS_FACTORY_G12_AUDIT_REQUIRED",
  "validation_safe": false
}
```
