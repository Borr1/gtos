# Context Anchor

```json
{
  "artifact_family": "CONTEXT_ANCHOR",
  "changes_trading_risk_safety_prompt_decision_behavior": false,
  "controlling_prompt": {
    "exists": true,
    "path": "research/science_program_2026_05/04_goal_prompts/G12_SCID_BLOCKED17_LTF_ASOF_PATH_ATTACHMENT_REPAIR_AUDIT_GOAL_PROMPT_2026-05-13.md",
    "sha256": "4426ef15d2381643ca629f4c1bb439968a2f5454222e2eb023a95c301167afcf",
    "size_bytes": 4855
  },
  "credentials_touched": false,
  "current_head": "fce52bec docs: refresh state after g12 prompt hardening",
  "evidence_class": "G12_SCID_BLOCKED17_LTF_ASOF_PATH_ATTACHMENT_REPAIR_AUDIT_ONLY",
  "generated_at_utc": "2026-05-13T04:46:17Z",
  "git_status_at_audit_start": "M .context/LIVE_STATE.md\n?? research/science_program_2026_05/06_outcome_testing/g12_scid_blocked17_ltf_asof_path_attachment_repair_audit/",
  "lane_posture": "Strict G12 audit; fair to broad/non-OB LTF path evidence; blockers require exact parser/source/hash/as-of/access/capture evidence.",
  "live_effect": false,
  "mandatory_context_read_from_disk": [
    ".context/LIVE_STATE.md",
    ".context/00_core/goal_session_research_discipline.md",
    ".context/00_core/research_operating_doctrine.md",
    ".context/00_core/research_current_state.md",
    ".context/00_core/local_heavy_data_inventory.md",
    ".context/00_core/ai_in_loop_cost_control_research_plan.md",
    ".context/00_core/quick_reference_card.md",
    ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md"
  ],
  "objective_restatement": "Independently audit the Blocked17 LTF parser/source-hash/as-of candidate attachment packet from disk evidence only.",
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
  "required_packet_inputs": {
    "candidate_manifest": {
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_blocked17_ltf_asof_path_parser_and_candidate_attachment/SCID_BLOCKED17_LTF_ASOF_CANDIDATE_DECISION_WINDOW_ASOF_MANIFEST_2026-05-13.json",
      "sha256": "0036d0195a74b0f97013b5bacf56c35fb0060c97aff3f3b2f2f54353f466e88d",
      "size_bytes": 7858
    },
    "completion": {
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_blocked17_ltf_asof_path_parser_and_candidate_attachment/SCID_BLOCKED17_LTF_ASOF_COMPLETION_AUDIT_2026-05-13.json",
      "sha256": "5932a36feaa68879efba42f938c64f78d88eb8fd11b00cd6bb1c82fa59492584",
      "size_bytes": 4150
    },
    "denominator_noleak": {
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_blocked17_ltf_asof_path_parser_and_candidate_attachment/SCID_BLOCKED17_LTF_ASOF_DENOMINATOR_NOLEAK_AUDIT_2026-05-13.json",
      "sha256": "d8924de7aa5b18d040c3ea137cb40704fa482694c5316f8092c6410af2e1b04c",
      "size_bytes": 2735
    },
    "matrix": {
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_blocked17_ltf_asof_path_parser_and_candidate_attachment/SCID_BLOCKED17_LTF_ASOF_PARSER_SOURCE_HASH_ATTACHMENT_MATRIX_2026-05-13.json",
      "sha256": "e8cf612113f14ebb0bf11a6ca4f0d8e8531cb772754195f40d165f18241c0fad",
      "size_bytes": 609791
    },
    "missing_ledger": {
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_blocked17_ltf_asof_path_parser_and_candidate_attachment/SCID_BLOCKED17_LTF_ASOF_MISSING_PARSER_ACCESS_LEDGER_2026-05-13.json",
      "sha256": "dc9d60c3efc6639788b25a9fa68a2cf42475c308731c5b6d8e9bb5535bbccc81",
      "size_bytes": 4332
    },
    "packet_focused_test": {
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_blocked17_ltf_asof_path_parser_and_candidate_attachment/SCID_BLOCKED17_LTF_ASOF_FOCUSED_TEST_RESULT_2026-05-13.json",
      "sha256": "71e0adfe59d5ee35d9a778b9d77df59217343e0405ccca363a9bd8e9fced1ae2",
      "size_bytes": 1383
    },
    "packet_verification": {
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_blocked17_ltf_asof_path_parser_and_candidate_attachment/SCID_BLOCKED17_LTF_ASOF_VERIFICATION_RESULT_2026-05-13.json",
      "sha256": "64439a7849b5bc303665329d910fade53b932374130fe31d58e32ab178179a19",
      "size_bytes": 1602
    },
    "route_decision": {
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_blocked17_ltf_asof_path_parser_and_candidate_attachment/SCID_BLOCKED17_LTF_ASOF_ROUTE_DECISION_LEDGER_2026-05-13.json",
      "sha256": "b567039b6eeb3d1858c53403293985e91df6ad59e501427a3851c4c002419c79",
      "size_bytes": 1949
    },
    "saturation": {
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_blocked17_ltf_asof_path_parser_and_candidate_attachment/SCID_BLOCKED17_LTF_ASOF_SATURATION_SELF_REDTEAM_LEDGER_2026-05-13.json",
      "sha256": "4fd8523468084d27f626e7d077ce6fd923178f18e061335ad1dddc01047500dc",
      "size_bytes": 4276
    }
  },
  "route_id": "G12_SCID_BLOCKED17_LTF_ASOF_PATH_ATTACHMENT_REPAIR_AUDIT",
  "schema_version": "g12_scid_blocked17_ltf_asof_path_attachment_repair_audit_v1",
  "supporting_upstream_inputs": {
    "g12_denominator_recompute": {
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/g12_scid_ltf_proxy_blocked17_source_status_audit/G12_SCID_LTF_PROXY_BLOCKED17_AUDIT_DENOMINATOR_RECOMPUTATION_2026-05-12.json",
      "sha256": "b954b2bc135f11d30d235475052853b3fdb775740b00377d0216ed237315f3c5",
      "size_bytes": 3444
    },
    "g12_source_status_recompute": {
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/g12_scid_ltf_proxy_blocked17_source_status_audit/G12_SCID_LTF_PROXY_BLOCKED17_AUDIT_SOURCE_STATUS_RECOMPUTATION_AUDIT_2026-05-12.json",
      "sha256": "33cbb0e1768d51fedf06cd8894c18717998d1efc2681a2769861c7da9cee5928",
      "size_bytes": 10133
    },
    "source_status_matrix": {
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_ltf_orderflow_proxy_source_status_expansion_for_blocked17/SCID_LTF_PROXY_SOURCE_STATUS_MATRIX_2026-05-12.json",
      "sha256": "7af530505a3b2553e8e09a78bdd72a49e28be19780fb92900954f7a350104fb9",
      "size_bytes": 311414
    }
  },
  "validation_safe": false
}
```
