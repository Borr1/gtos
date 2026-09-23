# Manifest Hash Policy Ledger

- **route_id:** `SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE`
- **evidence_class:** `SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_ONLY`
- **promotion_verdict:** `NO_PROMOTION_VERDICT`
- **validation_safe:** `false`
- **outcome_review_opened:** `false`
- **live_effect:** `false`

```json
{
  "accepted_g12_repair_note": "The G12 prompt was intentionally hardened after the builder route and is rebound here to its current hash. The builder manifest self-hash is self-referential and is not used as a blocking source binding. All other artifact/input hash mismatches are blockers.",
  "artifact_family": "manifest_hash_policy_ledger",
  "blocking_unrepaired_hash_mismatches": [],
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "evidence_class": "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_ONLY",
  "g0_repair_policy": [
    "The current G12 prompt hash supersedes the stale pre-hardening prompt hash.",
    "The builder output manifest self-hash remains non-blocking because it is self-referential: SELF_REFERENTIAL_MANIFEST_HASH_NOT_USED_AS_BLOCKING_BINDING.",
    "All other source/input/artifact hash mismatches are strict blockers.",
    "Future prompt packs must cite this repair note before comparing G12/builder manifest hashes."
  ],
  "generated_at_utc": "2026-05-12T03:20:55Z",
  "input_hash_rows": [
    {
      "exists": true,
      "input_name": "controlling_prompt",
      "path": "research/science_program_2026_05/04_goal_prompts/SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_GOAL_PROMPT_2026-05-12.md",
      "raw_market_blob": false,
      "sha256": "f47c322b373b07b63c6109eb6073e397b65f4c78e28f9d23ea78f666574ebfa7",
      "strict_hash_policy": true
    },
    {
      "exists": true,
      "input_name": "live_state",
      "path": ".context/LIVE_STATE.md",
      "raw_market_blob": false,
      "sha256": "d4a7b0e6124ac14d3fddcaeb451b56d7ea17d1753a92d1ccf2a36b1aeaf26037",
      "strict_hash_policy": false
    },
    {
      "exists": true,
      "input_name": "quick_reference",
      "path": ".context/00_core/quick_reference_card.md",
      "raw_market_blob": false,
      "sha256": "a0b24baf2d9829f79f48563172f327a7f23bac867db6e8e7df60f2af26658812",
      "strict_hash_policy": true
    },
    {
      "exists": true,
      "input_name": "research_doctrine",
      "path": ".context/00_core/research_operating_doctrine.md",
      "raw_market_blob": false,
      "sha256": "6b47da2ec47955381430bfa67aa78a11763fd10ff432118dbe1f18a7622a423c",
      "strict_hash_policy": true
    },
    {
      "exists": true,
      "input_name": "goal_session_discipline",
      "path": ".context/00_core/goal_session_research_discipline.md",
      "raw_market_blob": false,
      "sha256": "509fa5f901cf7df49a89582edd9d4064992e9af4c17a6b82bda283f7255611e8",
      "strict_hash_policy": true
    },
    {
      "exists": true,
      "input_name": "research_current_state",
      "path": ".context/00_core/research_current_state.md",
      "raw_market_blob": false,
      "sha256": "bc537c66f96ef5406bbf0fd7a187d2ccd2ffc74395a8a1308ddc35684efe64a5",
      "strict_hash_policy": false
    },
    {
      "exists": true,
      "input_name": "latest_handoff",
      "path": ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
      "raw_market_blob": false,
      "sha256": "1bc8223169e150ed2d64dcc74c6656c5db469a86eb53943ac199a633a407b670",
      "strict_hash_policy": true
    },
    {
      "exists": true,
      "input_name": "g12_decision",
      "path": "research/science_program_2026_05/06_outcome_testing/g12_scid_combined_source_search_and_forward_capture_route_audit/G12_SCID_COMBINED_SOURCE_CAPTURE_AUDIT_DECISION_LEDGER_2026-05-12.json",
      "raw_market_blob": false,
      "sha256": "4fb1d1cf53dfd280726ede40efaf85b7d5d40e912b68bd8b643b747b6a466aa0",
      "strict_hash_policy": true
    },
    {
      "exists": true,
      "input_name": "g12_row_coverage",
      "path": "research/science_program_2026_05/06_outcome_testing/g12_scid_combined_source_search_and_forward_capture_route_audit/G12_SCID_COMBINED_SOURCE_CAPTURE_AUDIT_ROW_COVERAGE_DENOMINATOR_RECOMPUTATION_AUDIT_2026-05-12.json",
      "raw_market_blob": false,
      "sha256": "0693abf8ef18747f30d5450e578b0566e5b3871690a0d0df805b0a0d49eeda78",
      "strict_hash_policy": true
    },
    {
      "exists": true,
      "input_name": "g12_field_status",
      "path": "research/science_program_2026_05/06_outcome_testing/g12_scid_combined_source_search_and_forward_capture_route_audit/G12_SCID_COMBINED_SOURCE_CAPTURE_AUDIT_FIELD_STATUS_RECOMPUTATION_AUDIT_2026-05-12.json",
      "raw_market_blob": false,
      "sha256": "eb2424693ecf4aca1674380545c5c083078e01e16d789279ac429198213e1c27",
      "strict_hash_policy": true
    },
    {
      "exists": true,
      "input_name": "g12_source_saturation",
      "path": "research/science_program_2026_05/06_outcome_testing/g12_scid_combined_source_search_and_forward_capture_route_audit/G12_SCID_COMBINED_SOURCE_CAPTURE_AUDIT_SOURCE_SEARCH_SATURATION_AUDIT_2026-05-12.json",
      "raw_market_blob": false,
      "sha256": "79f029c033328f4a64ad53f004c824868a0b1676888c73a8e9559b298032809a",
      "strict_hash_policy": true
    },
    {
      "exists": true,
      "input_name": "g12_hash_binding",
      "path": "research/science_program_2026_05/06_outcome_testing/g12_scid_combined_source_search_and_forward_capture_route_audit/G12_SCID_COMBINED_SOURCE_CAPTURE_AUDIT_SOURCE_HASH_MANIFEST_BINDING_AUDIT_2026-05-12.json",
      "raw_market_blob": false,
      "sha256": "f5a7a9494a568d642e96fa05429b8b71eece8665982d533cb8c19e2d8aaa308e",
      "strict_hash_policy": true
    },
    {
      "exists": true,
      "input_name": "g12_capture_exactness",
      "path": "research/science_program_2026_05/06_outcome_testing/g12_scid_combined_source_search_and_forward_capture_route_audit/G12_SCID_COMBINED_SOURCE_CAPTURE_AUDIT_CAPTURE_CONTRACT_EXACTNESS_AUDIT_2026-05-12.json",
      "raw_market_blob": false,
      "sha256": "20c48531fbef2f3b012265b2874e7f9b3ff302a06c982d92522f72404fa3e82e",
      "strict_hash_policy": true
    },
    {
      "exists": true,
      "input_name": "g12_noleak",
      "path": "research/science_program_2026_05/06_outcome_testing/g12_scid_combined_source_search_and_forward_capture_route_audit/G12_SCID_COMBINED_SOURCE_CAPTURE_AUDIT_NOLEAK_FORBIDDEN_SURFACE_AUDIT_2026-05-12.json",
      "raw_market_blob": false,
      "sha256": "8f359ac75f86d0856bfdf8b279f5bbb8c2f70960d27bedc462beca89c49b8e54",
      "strict_hash_policy": true
    },
    {
      "exists": true,
      "input_name": "g12_output_manifest",
      "path": "research/science_program_2026_05/06_outcome_testing/g12_scid_combined_source_search_and_forward_capture_route_audit/G12_SCID_COMBINED_SOURCE_CAPTURE_AUDIT_OUTPUT_MANIFEST_2026-05-12.json",
      "raw_market_blob": false,
      "sha256": "bc974bf333ecac1821743543d8d18b2d04deb36a2e55fe4d5d97e9c51b69b507",
      "strict_hash_policy": true
    },
    {
      "exists": true,
      "input_name": "g12_verification_result",
      "path": "research/science_program_2026_05/06_outcome_testing/g12_scid_combined_source_search_and_forward_capture_route_audit/G12_SCID_COMBINED_SOURCE_CAPTURE_AUDIT_VERIFICATION_RESULT_2026-05-12.json",
      "raw_market_blob": false,
      "sha256": "bcbbe15aa91728948ccac34d230b712f0bab66ac4fb979ce7120d6d0000b9457",
      "strict_hash_policy": true
    },
    {
      "exists": true,
      "input_name": "g12_completion_audit",
      "path": "research/science_program_2026_05/06_outcome_testing/g12_scid_combined_source_search_and_forward_capture_route_audit/G12_SCID_COMBINED_SOURCE_CAPTURE_AUDIT_COMPLETION_AUDIT_2026-05-12.json",
      "raw_market_blob": false,
      "sha256": "85b4f685e3c84c3b355f125e0c9f8b6f68183ea110ab02aaeebe632689da4271",
      "strict_hash_policy": true
    },
    {
      "exists": true,
      "input_name": "g12_closeout",
      "path": "research/science_program_2026_05/06_outcome_testing/g12_scid_combined_source_search_and_forward_capture_route_audit/G12_SCID_COMBINED_SOURCE_CAPTURE_AUDIT_CLOSEOUT_VERIFICATION_2026-05-12.json",
      "raw_market_blob": false,
      "sha256": "03e762b595d7d56b7e4248031ecce2879ec116dbe49467eac16ab9d0d018efaf",
      "strict_hash_policy": true
    },
    {
      "exists": true,
      "input_name": "g0_reconciliation",
      "path": "research/science_program_2026_05/06_outcome_testing/g0_scid_combined_source_capture_route_synthesis_control/G0_SCID_COMBINED_SOURCE_CAPTURE_SYNTHESIS_ACCEPTED_G12_AUDIT_RECONCILIATION_2026-05-12.json",
      "raw_market_blob": false,
      "sha256": "43fbcfc5d866d87db94498db9db22d578fb2e1d37c22cecefb31f6c3bf4bcb2f",
      "strict_hash_policy": true
    },
    {
      "exists": true,
      "input_name": "g0_ranking",
      "path": "research/science_program_2026_05/06_outcome_testing/g0_scid_combined_source_capture_route_synthesis_control/G0_SCID_COMBINED_SOURCE_CAPTURE_SYNTHESIS_ROUTE_OPTION_RANKING_2026-05-12.json",
      "raw_market_blob": false,
      "sha256": "d5db8bdf30abaa64bedf22072fd5bf9f0ef7cf60e15c03c9243b4f25f24747c4",
      "strict_hash_policy": true
    },
    {
      "exists": true,
      "input_name": "g0_carry_forward_contract",
      "path": "research/science_program_2026_05/06_outcome_testing/g0_scid_combined_source_capture_route_synthesis_control/G0_SCID_COMBINED_SOURCE_CAPTURE_SYNTHESIS_CARRY_FORWARD_CAPTURE_CONTRACT_LEDGER_2026-05-12.json",
      "raw_market_blob": false,
      "sha256": "d75809787015cfe398aed6118b64a691e8522d6fe0be7651ee64263b28d5ee5d",
      "strict_hash_policy": true
    },
    {
      "exists": true,
      "input_name": "g0_manifest_repair",
      "path": "research/science_program_2026_05/06_outcome_testing/g0_scid_combined_source_capture_route_synthesis_control/G0_SCID_COMBINED_SOURCE_CAPTURE_SYNTHESIS_MANIFEST_BINDING_REPAIR_CONTINUITY_NOTE_2026-05-12.json",
      "raw_market_blob": false,
      "sha256": "f7b95163f426d3d62bb5f792fa570ad3e452fe58de9db66f41aae462d293715a",
      "strict_hash_policy": true
    },
    {
      "exists": true,
      "input_name": "g0_boundary",
      "path": "research/science_program_2026_05/06_outcome_testing/g0_scid_combined_source_capture_route_synthesis_control/G0_SCID_COMBINED_SOURCE_CAPTURE_SYNTHESIS_IMPLEMENTATION_READINESS_BOUNDARY_LEDGER_2026-05-12.json",
      "raw_market_blob": false,
      "sha256": "3cb9a69c787599bc88b23324be7a9e067f3d8fe2a551ecb5bbf1e1ca11a6c118",
      "strict_hash_policy": true
    },
    {
      "exists": true,
      "input_name": "g0_forbidden_surface",
      "path": "research/science_program_2026_05/06_outcome_testing/g0_scid_combined_source_capture_route_synthesis_control/G0_SCID_COMBINED_SOURCE_CAPTURE_SYNTHESIS_FORBIDDEN_SURFACE_NOLEAK_CONTINUITY_AUDIT_2026-05-12.json",
      "raw_market_blob": false,
      "sha256": "c316830272c3e05c6ae6f695c09a2c064fae9b55d1dd64200bd8cb8f9e060ed5",
      "strict_hash_policy": true
    },
    {
      "exists": true,
      "input_name": "g0_prompt_pack",
      "path": "research/science_program_2026_05/06_outcome_testing/g0_scid_combined_source_capture_route_synthesis_control/G0_SCID_COMBINED_SOURCE_CAPTURE_SYNTHESIS_SELECTED_ROUTE_PROMPT_PACK_LEDGER_2026-05-12.json",
      "raw_market_blob": false,
      "sha256": "95e660983b868a3f6d95e808beea43009f50220834359a26adb43c2214ba3c96",
      "strict_hash_policy": true
    },
    {
      "exists": true,
      "input_name": "g0_decision",
      "path": "research/science_program_2026_05/06_outcome_testing/g0_scid_combined_source_capture_route_synthesis_control/G0_SCID_COMBINED_SOURCE_CAPTURE_SYNTHESIS_DECISION_LEDGER_2026-05-12.json",
      "raw_market_blob": false,
      "sha256": "4728b42f17c4edcccc6d8d0d4fe7fe4f7ec65e060caff9c229f05f91d147d950",
      "strict_hash_policy": true
    },
    {
      "exists": true,
      "input_name": "g0_completion_audit",
      "path": "research/science_program_2026_05/06_outcome_testing/g0_scid_combined_source_capture_route_synthesis_control/G0_SCID_COMBINED_SOURCE_CAPTURE_SYNTHESIS_COMPLETION_AUDIT_2026-05-12.json",
      "raw_market_blob": false,
      "sha256": "ad3480458ab271050c8ddc629c2fb93e69c3ecd93f15f6b1870664a046fa8e4d",
      "strict_hash_policy": true
    },
    {
      "exists": true,
      "input_name": "g0_closeout",
      "path": "research/science_program_2026_05/06_outcome_testing/g0_scid_combined_source_capture_route_synthesis_control/G0_SCID_COMBINED_SOURCE_CAPTURE_SYNTHESIS_CLOSEOUT_VERIFICATION_2026-05-12.json",
      "raw_market_blob": false,
      "sha256": "63b40100a32cf524c62d6e42c70553e493521ad77e8837907c1bc6aac3c8dea1",
      "strict_hash_policy": true
    },
    {
      "exists": true,
      "input_name": "builder_forward_contract",
      "path": "research/science_program_2026_05/06_outcome_testing/scid_combined_source_search_and_forward_capture_route/SCID_COMBINED_SOURCE_CAPTURE_FORWARD_CAPTURE_CONTRACT_2026-05-12.json",
      "raw_market_blob": false,
      "sha256": "21383a8839c7559247fd647253c400e459614b23498e2152b99381d2de82e223",
      "strict_hash_policy": true
    },
    {
      "exists": true,
      "input_name": "builder_schema_spec",
      "path": "research/science_program_2026_05/06_outcome_testing/scid_combined_source_search_and_forward_capture_route/SCID_COMBINED_SOURCE_CAPTURE_SCHEMA_REDACTION_ASOF_NOLEAK_SPECIFICATION_2026-05-12.json",
      "raw_market_blob": false,
      "sha256": "31f848144cfcc3b4f7e6207c7e92c47378f05b7d70f05b6908e096eb577c0acb",
      "strict_hash_policy": true
    },
    {
      "exists": true,
      "input_name": "strategy_field_summary",
      "path": "research/science_program_2026_05/06_outcome_testing/scid_strategy_field_source_expansion_packet/SCID_STRATEGY_FIELD_STATUS_SUMMARY_2026-05-12.json",
      "raw_market_blob": false,
      "sha256": "b55ca178042701de3200ba1938eccb58adb9217cf27d32c0ad1535ce28012cf9",
      "strict_hash_policy": true
    },
    {
      "exists": true,
      "input_name": "strategy_field_closure_rows",
      "path": "research/science_program_2026_05/06_outcome_testing/scid_strategy_field_source_expansion_packet/SCID_STRATEGY_FIELD_CANDIDATE_FIELD_CLOSURE_LEDGER_2026-05-12.jsonl",
      "raw_market_blob": false,
      "sha256": "fed6afa123d75e17dad8414f216400c2cab8a2f78e66ebe626c2daa1f2d69190",
      "strict_hash_policy": true
    },
    {
      "exists": true,
      "input_name": "g0_strategy_capture_spec",
      "path": "research/science_program_2026_05/06_outcome_testing/g0_scid_strategy_field_source_expansion_packet_synthesis/G0_SCID_STRATEGY_FIELD_PACKET_SYNTHESIS_CAPTURE_ONLY_IMPLEMENTATION_ROUTE_SPECIFICATION_2026-05-12.json",
      "raw_market_blob": false,
      "sha256": "a71198cc7feba672df36917815e2db5593f5cfe2c156d9fb5e4712911e26b76e",
      "strict_hash_policy": true
    },
    {
      "exists": true,
      "input_name": "g0_strategy_readiness",
      "path": "research/science_program_2026_05/06_outcome_testing/g0_scid_strategy_field_source_expansion_packet_synthesis/G0_SCID_STRATEGY_FIELD_PACKET_SYNTHESIS_SOURCE_FIELD_READINESS_SYNTHESIS_2026-05-12.json",
      "raw_market_blob": false,
      "sha256": "14120388bae835cc2d4d2d53dfd691cf88bbad770e2cb12749f74fb0a7d32b06",
      "strict_hash_policy": true
    },
    {
      "exists": true,
      "input_name": "g12_strategy_decision",
      "path": "research/science_program_2026_05/06_outcome_testing/g12_scid_strategy_field_source_expansion_packet_audit/G12_SCID_STRATEGY_FIELD_PACKET_AUDIT_DECISION_LEDGER_2026-05-12.json",
      "raw_market_blob": false,
      "sha256": "0ea3d42236ca6bc5d59dbe0d07b1f727878c0b3c820eb7ac21c2c06150bad6a2",
      "strict_hash_policy": true
    },
    {
      "exists": true,
      "input_name": "g12_strategy_field_status",
      "path": "research/science_program_2026_05/06_outcome_testing/g12_scid_strategy_field_source_expansion_packet_audit/G12_SCID_STRATEGY_FIELD_PACKET_AUDIT_FIELD_STATUS_RECOMPUTATION_AUDIT_2026-05-12.json",
      "raw_market_blob": false,
      "sha256": "c818bd90bc815c9c72035875d7f093b456dd5e35733e99180e7dc591f3336a6a",
      "strict_hash_policy": true
    }
  ],
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
  "raw_market_blob_inputs_committed_by_this_route": [],
  "repair_policy": {
    "all_other_source_input_hash_mismatches_are_strict_blockers": true,
    "builder_output_manifest_self_hash_is_non_blocking": true,
    "current_g12_prompt_hash_supersedes_stale_pre_hardening_hash": true
  },
  "route_id": "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE",
  "schema_version": "scid_forward_capture_offline_schema_package_v1",
  "validation_safe": false
}
```
