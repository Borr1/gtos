# Context Anchor

- `NO_PROMOTION_VERDICT`
- `validation_safe=false`
- `outcome_review_opened=false`
- `live_effect=false`

## Machine Payload

```json
{
  "accepted_g12_artifacts_read": [
    "C:\\tmp\\gtos_otb\\G0_LTF_PROXY_SYNTH\\research\\science_program_2026_05\\06_outcome_testing\\g12_scid_ltf_proxy_blocked17_source_status_audit\\G12_SCID_LTF_PROXY_BLOCKED17_AUDIT_DECISION_LEDGER_2026-05-12.json",
    "C:\\tmp\\gtos_otb\\G0_LTF_PROXY_SYNTH\\research\\science_program_2026_05\\06_outcome_testing\\g12_scid_ltf_proxy_blocked17_source_status_audit\\G12_SCID_LTF_PROXY_BLOCKED17_AUDIT_DENOMINATOR_RECOMPUTATION_2026-05-12.json",
    "C:\\tmp\\gtos_otb\\G0_LTF_PROXY_SYNTH\\research\\science_program_2026_05\\06_outcome_testing\\g12_scid_ltf_proxy_blocked17_source_status_audit\\G12_SCID_LTF_PROXY_BLOCKED17_AUDIT_SOURCE_STATUS_RECOMPUTATION_AUDIT_2026-05-12.json",
    "C:\\tmp\\gtos_otb\\G0_LTF_PROXY_SYNTH\\research\\science_program_2026_05\\06_outcome_testing\\g12_scid_ltf_proxy_blocked17_source_status_audit\\G12_SCID_LTF_PROXY_BLOCKED17_AUDIT_SEARCH_ROOT_SOURCE_INVENTORY_AUDIT_2026-05-12.json",
    "C:\\tmp\\gtos_otb\\G0_LTF_PROXY_SYNTH\\research\\science_program_2026_05\\06_outcome_testing\\g12_scid_ltf_proxy_blocked17_source_status_audit\\G12_SCID_LTF_PROXY_BLOCKED17_AUDIT_PROXY_HASH_ASOF_AUDIT_2026-05-12.json",
    "C:\\tmp\\gtos_otb\\G0_LTF_PROXY_SYNTH\\research\\science_program_2026_05\\06_outcome_testing\\g12_scid_ltf_proxy_blocked17_source_status_audit\\G12_SCID_LTF_PROXY_BLOCKED17_AUDIT_NOLEAK_FORBIDDEN_SURFACE_AUDIT_2026-05-12.json",
    "C:\\tmp\\gtos_otb\\G0_LTF_PROXY_SYNTH\\research\\science_program_2026_05\\06_outcome_testing\\g12_scid_ltf_proxy_blocked17_source_status_audit\\G12_SCID_LTF_PROXY_BLOCKED17_AUDIT_COMPLETION_AUDIT_2026-05-12.json",
    "C:\\tmp\\gtos_otb\\G0_LTF_PROXY_SYNTH\\research\\science_program_2026_05\\06_outcome_testing\\g12_scid_ltf_proxy_blocked17_source_status_audit\\G12_SCID_LTF_PROXY_BLOCKED17_AUDIT_VERIFICATION_RESULT_2026-05-12.json"
  ],
  "artifact_family": "CONTEXT_ANCHOR",
  "card_ids": [
    "ADV-002",
    "EXE-001",
    "EXE-003",
    "EXE-005",
    "GEO-002",
    "GEO-003",
    "GEO-004",
    "HAZ-003",
    "HAZ-004",
    "MAC-003",
    "MIC-001",
    "MIC-002",
    "MIC-003",
    "MIC-004",
    "MIC-005",
    "UNC-001",
    "UNC-005"
  ],
  "changes_live_trading_behavior": false,
  "completion_standard": "All 17 cards reconciled, every same-evidence-class blocker mapped to cleared/proven-impossible/exact runnable prompt, route bundle broad enough to avoid OB/current-GTOS boxing, verifier/focused tests pass, scoped commits made.",
  "context_files_read_after_live_state_regeneration": [
    ".context/LIVE_STATE.md",
    ".context/00_core/goal_session_research_discipline.md",
    ".context/00_core/research_operating_doctrine.md",
    ".context/00_core/research_current_state.md",
    ".context/00_core/local_heavy_data_inventory.md",
    ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
    "research/science_program_2026_05/04_goal_prompts/G0_SCID_LTF_PROXY_BLOCKED17_UNBLOCKING_SYNTHESIS_GOAL_PROMPT_2026-05-12.md"
  ],
  "credentials_touched": false,
  "evidence_class": "G0_SCID_LTF_PROXY_BLOCKED17_UNBLOCKING_SYNTHESIS_ONLY",
  "generated_at_utc": "2026-05-13T01:20:09Z",
  "git_head": "ab9f1a14492123960e6b01ab4cc9bd631a847710",
  "input_hashes": {
    "controlling_prompt": "8d3814edbf1ffc08f9a584ef426fd214a37c27fd85b12c1b4d0ecad5a1b213dd",
    "g12_completion_audit": "28ea55df0d8fad7cc2a0a43cf3c8d4c20257060390314adae032267f1265eccd",
    "g12_decision_ledger": "7f3ac65b5869a30f5fb03e6d1277aacb912959ee7950463642b3099f0ecb2949",
    "g12_denominator_audit": "b954b2bc135f11d30d235475052853b3fdb775740b00377d0216ed237315f3c5",
    "g12_noleak_audit": "24acbf85661f2069b699e3a3c935fe3cce74de2d326fb64b498297d6453b95ac",
    "g12_proxy_hash_asof_audit": "6d778e64d716cd29f24c7dde3e0c5d9b3a97f41e054b5e5716e839e9c643f672",
    "g12_search_inventory_audit": "2eef12ac5698e275bec5fd68094c834181fa74f970ca63c9c4087cd18d1d44ae",
    "g12_source_status_recomputation": "33cbb0e1768d51fedf06cd8894c18717998d1efc2681a2769861c7da9cee5928",
    "g12_verification_result": "0c59dcb2086747d6e6da0b59e3063eeee1d564f0ed7ec2b9b6769413aa4a564a",
    "goal_session_research_discipline": "61b02d954ee8cabb393ea4d3976b587834f7fe3d458588aabc7dea62f0588a3f",
    "latest_handoff": "0662139cbae0ef3ee6a0282af14136b02a9e5c49d5e462b62fd16243a4645235",
    "live_state": "29561191b398be8da785dc7d2da31b3265b4254798db5f5f5b148a4bf01af51a",
    "local_heavy_data_inventory": "b9941a0891ac3afd1ac42f41f59de594e974e928f2ddf08bccf9c237554a26fc",
    "research_current_state": "fa42e3111caceac34718fdb7b3faf44155b68ac0e4930fe1980889b79f451df7",
    "research_operating_doctrine": "0114d5a0b7855a6a24a71154a2d5254f35a766208effb9e4ac4270c547104c3d",
    "target_card_set": "343ffe517c5e257d8b13b53ced6f331b6d384dff7bcc25dae4fce244c4057cdd",
    "target_completion_audit": "4f092cea4fee5ca6278482883cbb73a195efa7700fbc5501d307fca1660bd59a",
    "target_noleak_audit": "2f3169ac0855eb90f8ecc84f110b3bd34104b1e55a6cde015d36c1d7729c1264",
    "target_parser_hash_asof_requirements": "32529927a73a96935f773ccbaf853f0ba2f4558af9dfaed132a251ed56ad878a",
    "target_proxy_validity_matrix": "ef7777b5a08f0449c59665fbca688c22d82303f558e97ea1d49138e8a654facd",
    "target_recoverable_vs_nongeneratable": "e65a5fefa6c9a2f7e854e013502099cca4ced40b4c3ff58d8c92db359fd13483",
    "target_search_root_ledger": "5a7113a28ae1926b6cb158e58c4d20340358b877fdb6ece1610f0e9b9a07e3bb",
    "target_source_inventory": "4193bb61c605649cc4c9bc5dd5bdd08378c381f2c87e20986e7a04e4a4d110d7",
    "target_source_status_matrix": "7af530505a3b2553e8e09a78bdd72a49e28be19780fb92900954f7a350104fb9"
  },
  "lane_classification": "G0 source-control unblocking synthesis, not validation, scoring, promotion, or live behavior.",
  "live_effect": false,
  "mandatory_preflight_completed": true,
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
  "route_id": "G0_SCID_LTF_PROXY_BLOCKED17_UNBLOCKING_SYNTHESIS",
  "schema_version": "g0_scid_ltf_proxy_blocked17_unblocking_synthesis_v1",
  "target_artifacts_read": [
    "C:\\tmp\\gtos_otb\\G0_LTF_PROXY_SYNTH\\research\\science_program_2026_05\\06_outcome_testing\\scid_ltf_orderflow_proxy_source_status_expansion_for_blocked17\\SCID_LTF_PROXY_BLOCKED17_CARD_SET_2026-05-12.json",
    "C:\\tmp\\gtos_otb\\G0_LTF_PROXY_SYNTH\\research\\science_program_2026_05\\06_outcome_testing\\scid_ltf_orderflow_proxy_source_status_expansion_for_blocked17\\SCID_LTF_PROXY_SOURCE_STATUS_MATRIX_2026-05-12.json",
    "C:\\tmp\\gtos_otb\\G0_LTF_PROXY_SYNTH\\research\\science_program_2026_05\\06_outcome_testing\\scid_ltf_orderflow_proxy_source_status_expansion_for_blocked17\\SCID_LTF_PROXY_SOURCE_INVENTORY_2026-05-12.json",
    "C:\\tmp\\gtos_otb\\G0_LTF_PROXY_SYNTH\\research\\science_program_2026_05\\06_outcome_testing\\scid_ltf_orderflow_proxy_source_status_expansion_for_blocked17\\SCID_LTF_PROXY_VALIDITY_AND_EQUIVALENCE_MATRIX_2026-05-12.json",
    "C:\\tmp\\gtos_otb\\G0_LTF_PROXY_SYNTH\\research\\science_program_2026_05\\06_outcome_testing\\scid_ltf_orderflow_proxy_source_status_expansion_for_blocked17\\SCID_LTF_PROXY_PARSER_HASH_ASOF_REQUIREMENTS_2026-05-12.json",
    "C:\\tmp\\gtos_otb\\G0_LTF_PROXY_SYNTH\\research\\science_program_2026_05\\06_outcome_testing\\scid_ltf_orderflow_proxy_source_status_expansion_for_blocked17\\SCID_LTF_PROXY_RECOVERABLE_VS_NONGENERATABLE_LEDGER_2026-05-12.json",
    "C:\\tmp\\gtos_otb\\G0_LTF_PROXY_SYNTH\\research\\science_program_2026_05\\06_outcome_testing\\scid_ltf_orderflow_proxy_source_status_expansion_for_blocked17\\SCID_LTF_PROXY_SEARCH_ROOT_LEDGER_2026-05-12.json",
    "C:\\tmp\\gtos_otb\\G0_LTF_PROXY_SYNTH\\research\\science_program_2026_05\\06_outcome_testing\\scid_ltf_orderflow_proxy_source_status_expansion_for_blocked17\\SCID_LTF_PROXY_NO_LEAK_AND_FORBIDDEN_SURFACE_AUDIT_2026-05-12.json",
    "C:\\tmp\\gtos_otb\\G0_LTF_PROXY_SYNTH\\research\\science_program_2026_05\\06_outcome_testing\\scid_ltf_orderflow_proxy_source_status_expansion_for_blocked17\\SCID_LTF_PROXY_COMPLETION_AUDIT_2026-05-12.json"
  ],
  "validation_safe": false
}
```
