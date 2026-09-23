# No-Leak Forbidden Surface Audit

```json
{
  "artifact_family": "noleak_forbidden_surface_audit",
  "builder_manifest_raw_market_blob_paths": [],
  "changes_live_trading_behavior": false,
  "control_prompt_required_phrase_gaps": [],
  "credentials_touched": false,
  "evidence_class": "G12_SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_AUDIT_ONLY",
  "generated_at_utc": "2026-05-12T07:45:57Z",
  "live_effect": false,
  "noleak_forbidden_surface_ok": true,
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
  "related_commit_forbidden_surface_violations": [],
  "related_commits": [
    {
      "commit": "f8bbb4dce883af7aa8c88c1013794cdf75a006a3",
      "forbidden_live_surface_paths": [],
      "paths": [
        "research/science_program_2026_05/04_goal_prompts/G12_SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_AUDIT_GOAL_PROMPT_2026-05-12.md"
      ],
      "raw_market_blob_paths": [],
      "subject": "research: finalize scid ltf orderflow audit prompt hardening"
    },
    {
      "commit": "ad7361c19a0f1383b8b4b5d318c26afbd6cad765",
      "forbidden_live_surface_paths": [],
      "paths": [
        "research/science_program_2026_05/04_goal_prompts/G12_SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_AUDIT_GOAL_PROMPT_2026-05-12.md"
      ],
      "raw_market_blob_paths": [],
      "subject": "research: harden scid ltf orderflow g12 prompt"
    },
    {
      "commit": "67441ae89e72576523fb4325b08c55d2d3f1f178",
      "forbidden_live_surface_paths": [],
      "paths": [
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_CLOSEOUT_VERIFICATION_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_CLOSEOUT_VERIFICATION_2026-05-12.md"
      ],
      "raw_market_blob_paths": [],
      "subject": "research: normalize scid ltf proxy closeout status"
    },
    {
      "commit": "bcab89868812f37aacdf2ad039127cdff6a70ff0",
      "forbidden_live_surface_paths": [],
      "paths": [
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_VERIFICATION_RESULT_2026-05-12.json"
      ],
      "raw_market_blob_paths": [],
      "subject": "research: refresh scid ltf proxy verification result"
    },
    {
      "commit": "2b5b899d9250891cb94f283fe931b5105a4622b9",
      "forbidden_live_surface_paths": [],
      "paths": [
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_CLOSEOUT_VERIFICATION_2026-05-12.md",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_COMPLETION_AUDIT_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_COMPLETION_AUDIT_2026-05-12.md"
      ],
      "raw_market_blob_paths": [],
      "subject": "research: finalize scid ltf proxy closeout"
    },
    {
      "commit": "add9401e66c8f553b792a280a062c27a3c7e2415",
      "forbidden_live_surface_paths": [],
      "paths": [
        "research/science_program_2026_05/04_goal_prompts/G12_SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_AUDIT_GOAL_PROMPT_2026-05-12.md",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ACCEPTED_AUDIT_RECONCILIATION_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ACCEPTED_AUDIT_RECONCILIATION_2026-05-12.md",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ACQUISITION_LADDER_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ACQUISITION_LADDER_2026-05-12.md",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_APPROVAL_GATE_LEDGER_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_APPROVAL_GATE_LEDGER_2026-05-12.md",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ASOF_NOLEAK_DUPLICATE_POLICY_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ASOF_NOLEAK_DUPLICATE_POLICY_2026-05-12.md",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_CANDIDATE_COVERAGE_MATRIX_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_CANDIDATE_COVERAGE_MATRIX_2026-05-12.md",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_CLOSEOUT_VERIFICATION_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_CLOSEOUT_VERIFICATION_2026-05-12.md",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_COMPLETION_AUDIT_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_COMPLETION_AUDIT_2026-05-12.md",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_CONTEXT_ANCHOR_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_CONTEXT_ANCHOR_2026-05-12.md",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_DECISION_LEDGER_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_DECISION_LEDGER_2026-05-12.md",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_LTF_SOURCE_MATRIX_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_LTF_SOURCE_MATRIX_2026-05-12.md",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_ORDERFLOW_PROXY_MATRIX_2026-05-12.md",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_OUTPUT_MANIFEST_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_OUTPUT_MANIFEST_2026-05-12.md",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_PROXY_VALIDITY_LEDGER_2026-05-12.md",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_SATURATION_REDTEAM_LEDGER_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_SATURATION_REDTEAM_LEDGER_2026-05-12.md",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_SOURCE_INVENTORY_HASH_MANIFEST_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_SOURCE_INVENTORY_HASH_MANIFEST_2026-05-12.md",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_VERIFICATION_RESULT_2026-05-12.json",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/build_scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis_2026_05_12.py",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/test_scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis_2026_05_12.py",
        "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/verify_scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis_2026_05_12.py"
      ],
      "raw_market_blob_paths": [],
      "subject": "research: build scid ltf orderflow proxy expansion"
    }
  ],
  "route_id": "G12_SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_FROM_OFFLINE_SCHEMA_SYNTHESIS_AUDIT",
  "safe_flag_violations": [],
  "schema_version": "g12_scid_ltf_orderflow_proxy_source_expansion_audit_v1",
  "scoped_git_status": {
    "entries": [
      {
        "path": ".context/LIVE_STATE.md",
        "raw": " M .context/LIVE_STATE.md",
        "scoped": true,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false
      },
      {
        "path": "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_VERIFICATION_RESULT_2026-05-12.json",
        "raw": " M research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_VERIFICATION_RESULT_2026-05-12.json",
        "scoped": true,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false
      },
      {
        "path": "research/science_program_2026_05/06_outcome_testing/g12_scid_ltf_proxy_audit/",
        "raw": "?? research/science_program_2026_05/06_outcome_testing/g12_scid_ltf_proxy_audit/",
        "scoped": true,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false
      }
    ],
    "no_scoped_forbidden_live_surface": true,
    "no_scoped_raw_market_blob": true,
    "scoped_entries": [
      {
        "path": ".context/LIVE_STATE.md",
        "raw": " M .context/LIVE_STATE.md",
        "scoped": true,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false
      },
      {
        "path": "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_VERIFICATION_RESULT_2026-05-12.json",
        "raw": " M research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_expansion_from_offline_schema_synthesis/SCID_LTF_OF_PROXY_EXPANSION_VERIFICATION_RESULT_2026-05-12.json",
        "scoped": true,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false
      },
      {
        "path": "research/science_program_2026_05/06_outcome_testing/g12_scid_ltf_proxy_audit/",
        "raw": "?? research/science_program_2026_05/06_outcome_testing/g12_scid_ltf_proxy_audit/",
        "scoped": true,
        "scoped_forbidden_live_surface": false,
        "scoped_raw_market_blob": false
      }
    ],
    "unrelated_dirty_entry_count": 0
  },
  "validation_safe": false
}
```
