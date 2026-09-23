# G12 Nofill Source State Gap Closure Target Artifact Inventory Source Hash Audit 2026-05-10

- Route: `G12_NOFILL_SOURCE_STATE_GAP_CLOSURE_AND_TICK_EXPORT_MANIFEST_AUDIT`
- Generated: `2026-05-10T09:13:22Z`
- Promotion posture: `NO_PROMOTION_VERDICT`
- Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

- audit_status: `PASS`

```json
{
  "artifact_family": "target_artifact_inventory_and_source_hash_audit",
  "audit_status": "PASS",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "generated_at_utc": "2026-05-10T09:13:22Z",
  "live_effect": false,
  "missing_target_artifacts": [],
  "mutable_context_hash_drifts": [
    {
      "current_sha256": "4b28326c15b25fa26e9c7e3f32bfabe50289dc8cf9882b205ef4f369a7e1047c",
      "generated_catalog_support": false,
      "input_key": "live_state",
      "mutable_context": true,
      "path": ".context/LIVE_STATE.md",
      "recorded_sha256": "6da97bd9e3b321f6b338f5e258d8259fc53eb13db63449d18ee971f730a79acf",
      "status": "MUTABLE_CONTEXT_DRIFT_ALLOWED"
    },
    {
      "current_sha256": "b1ad4be00992991b99f9f68713d692a517e3381272f9721ef4bc1c62f615985e",
      "generated_catalog_support": false,
      "input_key": "research_current_state",
      "mutable_context": true,
      "path": ".context/00_core/research_current_state.md",
      "recorded_sha256": "c354dc1aa8803bd20eed7dfc2e21787b5578ecaf6d76026d4ce250e1f6ca1f21",
      "status": "MUTABLE_CONTEXT_DRIFT_ALLOWED"
    },
    {
      "current_sha256": "bd8c1621452000376e6b6521b364c57e56473e69de3f9689bbc98140199e6cfc",
      "generated_catalog_support": false,
      "input_key": "research_doctrine",
      "mutable_context": true,
      "path": ".context/00_core/research_operating_doctrine.md",
      "recorded_sha256": "bed0ae8b92a000a28e4e4a3f07563abbc4913b37bc9ec3ad5cc71d07263dda6d",
      "status": "MUTABLE_CONTEXT_DRIFT_ALLOWED"
    }
  ],
  "opens_live_restart": false,
  "opens_live_trading_behavior": false,
  "opens_mt5_order_account_history_behavior": false,
  "opens_paid_api_or_databento_route": false,
  "opens_promotion": false,
  "opens_registry_edit": false,
  "opens_remote_push": false,
  "opens_result_scoring": false,
  "opens_validation": false,
  "outcome_review_opened": false,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "route_id": "G12_NOFILL_SOURCE_STATE_GAP_CLOSURE_AND_TICK_EXPORT_MANIFEST_AUDIT",
  "schema_version": "g12_nofill_source_state_gap_closure_and_tick_export_manifest_audit_v1",
  "strict_source_hash_mismatches": [],
  "target_artifact_count": 24,
  "target_artifact_hashes": [
    {
      "artifact_name": "NOFILL_SOURCE_STATE_GAP_CLOSURE_55_FIELD_CLOSURE_LEDGER_2026-05-10.json",
      "exists": true,
      "relative_path": "research/science_program_2026_05/06_outcome_testing/nofill_source_state_capture_gap_closure_and_tick_export_manifest_route/NOFILL_SOURCE_STATE_GAP_CLOSURE_55_FIELD_CLOSURE_LEDGER_2026-05-10.json",
      "sha256": "88eef5aadfa6ea3b9d3b674bfd737557cee29971ef5f38bd7f120c12a4e950d9",
      "size_bytes": 35894,
      "strict_source_artifact": true
    },
    {
      "artifact_name": "NOFILL_SOURCE_STATE_GAP_CLOSURE_ACTIVE_CATALOG_REFRESH_SEARCH_LEDGER_2026-05-10.json",
      "exists": true,
      "relative_path": "research/science_program_2026_05/06_outcome_testing/nofill_source_state_capture_gap_closure_and_tick_export_manifest_route/NOFILL_SOURCE_STATE_GAP_CLOSURE_ACTIVE_CATALOG_REFRESH_SEARCH_LEDGER_2026-05-10.json",
      "sha256": "288bccfed88617579d3c155e0c5a62c87e938d4184a4373120b0720af6303471",
      "size_bytes": 3670,
      "strict_source_artifact": true
    },
    {
      "artifact_name": "NOFILL_SOURCE_STATE_GAP_CLOSURE_ACTIVE_PURSUIT_LADDER_LEDGER_2026-05-10.json",
      "exists": true,
      "relative_path": "research/science_program_2026_05/06_outcome_testing/nofill_source_state_capture_gap_closure_and_tick_export_manifest_route/NOFILL_SOURCE_STATE_GAP_CLOSURE_ACTIVE_PURSUIT_LADDER_LEDGER_2026-05-10.json",
      "sha256": "15f05e88f43c37016ac40d01c531c83e47102a6cbfbca82e18a4a89d56504f9c",
      "size_bytes": 421435,
      "strict_source_artifact": true
    },
    {
      "artifact_name": "NOFILL_SOURCE_STATE_GAP_CLOSURE_ACTIVE_PURSUIT_LADDER_LEDGER_2026-05-10.md",
      "exists": true,
      "relative_path": "research/science_program_2026_05/06_outcome_testing/nofill_source_state_capture_gap_closure_and_tick_export_manifest_route/NOFILL_SOURCE_STATE_GAP_CLOSURE_ACTIVE_PURSUIT_LADDER_LEDGER_2026-05-10.md",
      "sha256": "85de8d93a6d07a40bf8a29fa066b355099e233ad63f9cbb34f5ced73951416f1",
      "size_bytes": 37531,
      "strict_source_artifact": true
    },
    {
      "artifact_name": "NOFILL_SOURCE_STATE_GAP_CLOSURE_COMPLETION_AUDIT_2026-05-10.json",
      "exists": true,
      "relative_path": "research/science_program_2026_05/06_outcome_testing/nofill_source_state_capture_gap_closure_and_tick_export_manifest_route/NOFILL_SOURCE_STATE_GAP_CLOSURE_COMPLETION_AUDIT_2026-05-10.json",
      "sha256": "33f6b942d5ad6202d173f6e2901ae6c6aba9d07577e747ef5f199bbb7cbcca40",
      "size_bytes": 8305,
      "strict_source_artifact": true
    },
    {
      "artifact_name": "NOFILL_SOURCE_STATE_GAP_CLOSURE_COMPLETION_AUDIT_2026-05-10.md",
      "exists": true,
      "relative_path": "research/science_program_2026_05/06_outcome_testing/nofill_source_state_capture_gap_closure_and_tick_export_manifest_route/NOFILL_SOURCE_STATE_GAP_CLOSURE_COMPLETION_AUDIT_2026-05-10.md",
      "sha256": "ba8c165a50ae4943e996dd1f2f64b6f7c87f0624d5db99b791cdedcdd7387e4e",
      "size_bytes": 3756,
      "strict_source_artifact": true
    },
    {
      "artifact_name": "NOFILL_SOURCE_STATE_GAP_CLOSURE_CONTAMINATION_EMBARGO_HANDLING_LEDGER_2026-05-10.json",
      "exists": true,
      "relative_path": "research/science_program_2026_05/06_outcome_testing/nofill_source_state_capture_gap_closure_and_tick_export_manifest_route/NOFILL_SOURCE_STATE_GAP_CLOSURE_CONTAMINATION_EMBARGO_HANDLING_LEDGER_2026-05-10.json",
      "sha256": "668600b9cb8314819507528b20597e4c29d862710829836c8c5faa5e753b5abd",
      "size_bytes": 19611,
      "strict_source_artifact": true
    },
    {
      "artifact_name": "NOFILL_SOURCE_STATE_GAP_CLOSURE_CONTEXT_ANCHOR_2026-05-10.json",
      "exists": true,
      "relative_path": "research/science_program_2026_05/06_outcome_testing/nofill_source_state_capture_gap_closure_and_tick_export_manifest_route/NOFILL_SOURCE_STATE_GAP_CLOSURE_CONTEXT_ANCHOR_2026-05-10.json",
      "sha256": "2ae34ac025f1e9ac3000814b7ded6016259fd90e80efb911175f38d0fc6a9f26",
      "size_bytes": 12810,
      "strict_source_artifact": true
    },
    {
      "artifact_name": "NOFILL_SOURCE_STATE_GAP_CLOSURE_DECISION_LEDGER_2026-05-10.json",
      "exists": true,
      "relative_path": "research/science_program_2026_05/06_outcome_testing/nofill_source_state_capture_gap_closure_and_tick_export_manifest_route/NOFILL_SOURCE_STATE_GAP_CLOSURE_DECISION_LEDGER_2026-05-10.json",
      "sha256": "5390ff5ae425ce50d3bcfb4c78aa95eb177c4a6dd8b9ee4672179a0046138ad3",
      "size_bytes": 2297,
      "strict_source_artifact": true
    },
    {
      "artifact_name": "NOFILL_SOURCE_STATE_GAP_CLOSURE_FORWARD_CAPTURE_REQUIREMENT_MATRIX_2026-05-10.json",
      "exists": true,
      "relative_path": "research/science_program_2026_05/06_outcome_testing/nofill_source_state_capture_gap_closure_and_tick_export_manifest_route/NOFILL_SOURCE_STATE_GAP_CLOSURE_FORWARD_CAPTURE_REQUIREMENT_MATRIX_2026-05-10.json",
      "sha256": "02f017507df743a0939074a74fb7454788f36209013f32ab942160980bf37627",
      "size_bytes": 41802,
      "strict_source_artifact": true
    },
    {
      "artifact_name": "NOFILL_SOURCE_STATE_GAP_CLOSURE_G0_BLOCKER_INGESTION_RECONCILIATION_2026-05-10.json",
      "exists": true,
      "relative_path": "research/science_program_2026_05/06_outcome_testing/nofill_source_state_capture_gap_closure_and_tick_export_manifest_route/NOFILL_SOURCE_STATE_GAP_CLOSURE_G0_BLOCKER_INGESTION_RECONCILIATION_2026-05-10.json",
      "sha256": "79fec4f952a02c71931a9d53c5c54f074d57f5b2f47a463be52f046cd9962d5f",
      "size_bytes": 4100,
      "strict_source_artifact": true
    },
    {
      "artifact_name": "NOFILL_SOURCE_STATE_GAP_CLOSURE_NOLEAK_FORBIDDEN_ROUTE_AUDIT_2026-05-10.json",
      "exists": true,
      "relative_path": "research/science_program_2026_05/06_outcome_testing/nofill_source_state_capture_gap_closure_and_tick_export_manifest_route/NOFILL_SOURCE_STATE_GAP_CLOSURE_NOLEAK_FORBIDDEN_ROUTE_AUDIT_2026-05-10.json",
      "sha256": "de54c64313914a92015f9f4d571755a622ef842510a575efa1b85407ea3d368c",
      "size_bytes": 17198,
      "strict_source_artifact": true
    },
    {
      "artifact_name": "NOFILL_SOURCE_STATE_GAP_CLOSURE_NOLEAK_FORBIDDEN_ROUTE_AUDIT_2026-05-10.md",
      "exists": true,
      "relative_path": "research/science_program_2026_05/06_outcome_testing/nofill_source_state_capture_gap_closure_and_tick_export_manifest_route/NOFILL_SOURCE_STATE_GAP_CLOSURE_NOLEAK_FORBIDDEN_ROUTE_AUDIT_2026-05-10.md",
      "sha256": "905b51bc3f5919f7917bcd1994b015107405e5d607acb5160560c644670842e1",
      "size_bytes": 17524,
      "strict_source_artifact": true
    },
    {
      "artifact_name": "NOFILL_SOURCE_STATE_GAP_CLOSURE_NON_GENERATABLE_TRUTH_PROOF_LEDGER_2026-05-10.json",
      "exists": true,
      "relative_path": "research/science_program_2026_05/06_outcome_testing/nofill_source_state_capture_gap_closure_and_tick_export_manifest_route/NOFILL_SOURCE_STATE_GAP_CLOSURE_NON_GENERATABLE_TRUTH_PROOF_LEDGER_2026-05-10.json",
      "sha256": "dce4ec52ce2c2184aa1e145b3e00749aa35ec575382decd51d680d2d040a08a0",
      "size_bytes": 148103,
      "strict_source_artifact": true
    },
    {
      "artifact_name": "NOFILL_SOURCE_STATE_GAP_CLOSURE_OWNER_ACTION_MANIFEST_2026-05-10.json",
      "exists": true,
      "relative_path": "research/science_program_2026_05/06_outcome_testing/nofill_source_state_capture_gap_closure_and_tick_export_manifest_route/NOFILL_SOURCE_STATE_GAP_CLOSURE_OWNER_ACTION_MANIFEST_2026-05-10.json",
      "sha256": "66b7b34a0697415449dec14a1b51b7069d4191e5d3015f7c199974e225bd263f",
      "size_bytes": 26503,
      "strict_source_artifact": true
    },
    {
      "artifact_name": "NOFILL_SOURCE_STATE_GAP_CLOSURE_OWNER_ACTION_MANIFEST_2026-05-10.md",
      "exists": true,
      "relative_path": "research/science_program_2026_05/06_outcome_testing/nofill_source_state_capture_gap_closure_and_tick_export_manifest_route/NOFILL_SOURCE_STATE_GAP_CLOSURE_OWNER_ACTION_MANIFEST_2026-05-10.md",
      "sha256": "a107cac84ae80fd32d7c57a07ff1272b63974951600417a004c5aa8507aa279b",
      "size_bytes": 26865,
      "strict_source_artifact": true
    },
    {
      "artifact_name": "NOFILL_SOURCE_STATE_GAP_CLOSURE_RECOVERED_SOURCE_STATE_MANIFEST_2026-05-10.json",
      "exists": true,
      "relative_path": "research/science_program_2026_05/06_outcome_testing/nofill_source_state_capture_gap_closure_and_tick_export_manifest_route/NOFILL_SOURCE_STATE_GAP_CLOSURE_RECOVERED_SOURCE_STATE_MANIFEST_2026-05-10.json",
      "sha256": "6ca4feaedfd5c0aca85419e9d39ff645da3ae88e22d54225b8ac2ea5cc1df279",
      "size_bytes": 22522,
      "strict_source_artifact": true
    },
    {
      "artifact_name": "NOFILL_SOURCE_STATE_GAP_CLOSURE_SOURCE_STATE_GAP_TAXONOMY_LEDGER_2026-05-10.json",
      "exists": true,
      "relative_path": "research/science_program_2026_05/06_outcome_testing/nofill_source_state_capture_gap_closure_and_tick_export_manifest_route/NOFILL_SOURCE_STATE_GAP_CLOSURE_SOURCE_STATE_GAP_TAXONOMY_LEDGER_2026-05-10.json",
      "sha256": "7c71ec22c041b8f71a028efb0475afae0f909111f0f911bbbd84834b3ac3a6e3",
      "size_bytes": 88312,
      "strict_source_artifact": true
    },
    {
      "artifact_name": "NOFILL_SOURCE_STATE_GAP_CLOSURE_TICK_EXPORT_EXTRACTION_MANIFEST_2026-05-10.json",
      "exists": true,
      "relative_path": "research/science_program_2026_05/06_outcome_testing/nofill_source_state_capture_gap_closure_and_tick_export_manifest_route/NOFILL_SOURCE_STATE_GAP_CLOSURE_TICK_EXPORT_EXTRACTION_MANIFEST_2026-05-10.json",
      "sha256": "0a6691b12471f8500d02305bb3ca657f109ecedecfd6f747e3159f4dc26d4096",
      "size_bytes": 66157,
      "strict_source_artifact": true
    },
    {
      "artifact_name": "NOFILL_SOURCE_STATE_GAP_CLOSURE_TICK_EXPORT_EXTRACTION_MANIFEST_2026-05-10.md",
      "exists": true,
      "relative_path": "research/science_program_2026_05/06_outcome_testing/nofill_source_state_capture_gap_closure_and_tick_export_manifest_route/NOFILL_SOURCE_STATE_GAP_CLOSURE_TICK_EXPORT_EXTRACTION_MANIFEST_2026-05-10.md",
      "sha256": "16776693f116254d07d59039be51dbf0155373f800f0a383be1bedc6890f9a88",
      "size_bytes": 28647,
      "strict_source_artifact": true
    },
    {
      "artifact_name": "NOFILL_SOURCE_STATE_GAP_CLOSURE_VERIFICATION_RESULT_2026-05-10.json",
      "exists": true,
      "relative_path": "research/science_program_2026_05/06_outcome_testing/nofill_source_state_capture_gap_closure_and_tick_export_manifest_route/NOFILL_SOURCE_STATE_GAP_CLOSURE_VERIFICATION_RESULT_2026-05-10.json",
      "sha256": "0247397e3fc37b5e42613228a5ece0ab43f428dc3fb48fb2d526112a18f5e114",
      "size_bytes": 1303,
      "strict_source_artifact": true
    },
    {
      "artifact_name": "build_nofill_source_state_capture_gap_closure_and_tick_export_manifest_route_2026_05_10.py",
      "exists": true,
      "relative_path": "research/science_program_2026_05/06_outcome_testing/nofill_source_state_capture_gap_closure_and_tick_export_manifest_route/build_nofill_source_state_capture_gap_closure_and_tick_export_manifest_route_2026_05_10.py",
      "sha256": "3f368b114aa54db8ae12aaa67f8d357e887f5bd8d1e658fef226ea8eed11f7dc",
      "size_bytes": 66494,
      "strict_source_artifact": true
    },
    {
      "artifact_name": "test_nofill_source_state_capture_gap_closure_and_tick_export_manifest_route_2026_05_10.py",
      "exists": true,
      "relative_path": "research/science_program_2026_05/06_outcome_testing/nofill_source_state_capture_gap_closure_and_tick_export_manifest_route/test_nofill_source_state_capture_gap_closure_and_tick_export_manifest_route_2026_05_10.py",
      "sha256": "a1ca37b8bf638ef471e14a4cb9e7845d4cc29ad9434e46ac971bb34643d5a71e",
      "size_bytes": 4212,
      "strict_source_artifact": true
    },
    {
      "artifact_name": "verify_nofill_source_state_capture_gap_closure_and_tick_export_manifest_route_2026_05_10.py",
      "exists": true,
      "relative_path": "research/science_program_2026_05/06_outcome_testing/nofill_source_state_capture_gap_closure_and_tick_export_manifest_route/verify_nofill_source_state_capture_gap_closure_and_tick_export_manifest_route_2026_05_10.py",
      "sha256": "e5a5d797797125896be9c3eb3f217eda86fbf13a7aa3a33115037c7c5a7f25b8",
      "size_bytes": 16443,
      "strict_source_artifact": true
    }
  ],
  "target_context_input_hash_drift_rows": [
    {
      "current_sha256": "28940ddfb90900c5832ba0b7583fb7a966c1f57c1caec0e89cfd77b08fbeeea2",
      "generated_catalog_support": true,
      "input_key": "catalog_completion",
      "mutable_context": false,
      "path": "C:/tmp/gtos_otb/NOFILLSTATEGAP/research/science_program_2026_05/06_outcome_testing/gtos_local_research_data_catalog_implementation_route/GTOS_LOCAL_RESEARCH_DATA_CATALOG_COMPLETION_AUDIT_2026-05-10.json",
      "recorded_sha256": "25bd6bed2434f0b16019fe5af10f68eca85f174e4846a0eb739e21cd2a75321a",
      "status": "GENERATED_CATALOG_SUPPORT_DRIFT_RECOMPUTED"
    },
    {
      "current_sha256": "0785e13dc522efa10a0afd991f22aa999636445ad335d7fa8371d4dd1c4a533a",
      "generated_catalog_support": true,
      "input_key": "catalog_hash_deferral",
      "mutable_context": false,
      "path": "C:/tmp/gtos_otb/NOFILLSTATEGAP/research/science_program_2026_05/06_outcome_testing/gtos_local_research_data_catalog_implementation_route/GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_HASH_DEFERRAL_MANIFEST_2026-05-10.json",
      "recorded_sha256": "112e099bd3e5e84f64a450650ac383b55338d8b6062c18d4b4cc351f9e9c4105",
      "status": "GENERATED_CATALOG_SUPPORT_DRIFT_RECOMPUTED"
    },
    {
      "current_sha256": "0586dfdd65623a606a5b65022784be13c118052dd558489509abc8efc7d882b8",
      "generated_catalog_support": true,
      "input_key": "catalog_missing_window",
      "mutable_context": false,
      "path": "C:/tmp/gtos_otb/NOFILLSTATEGAP/research/science_program_2026_05/06_outcome_testing/gtos_local_research_data_catalog_implementation_route/GTOS_LOCAL_RESEARCH_DATA_CATALOG_MISSING_WINDOW_LEDGER_2026-05-10.json",
      "recorded_sha256": "8055c98afa67001a50a26b3cede510a0a22f4693ffdc62a6e73a1e3d15266d4b",
      "status": "GENERATED_CATALOG_SUPPORT_DRIFT_RECOMPUTED"
    },
    {
      "current_sha256": "a11d2293b76a00c1d1ca2950ace12e946ff94b1b7ec3b4f6016c5476f938996c",
      "generated_catalog_support": true,
      "input_key": "catalog_output_manifest",
      "mutable_context": false,
      "path": "C:/tmp/gtos_otb/NOFILLSTATEGAP/research/science_program_2026_05/06_outcome_testing/gtos_local_research_data_catalog_implementation_route/GTOS_LOCAL_RESEARCH_DATA_CATALOG_OUTPUT_MANIFEST_2026-05-10.json",
      "recorded_sha256": "5d3e5f5d61252e87182b7f72801b56cecf1c6da77d08acddab87a84e459b3d06",
      "status": "GENERATED_CATALOG_SUPPORT_DRIFT_RECOMPUTED"
    },
    {
      "current_sha256": "e5424f0c2d39321409f7dc5c9927ab5305e29772c545e371ba886678eca57793",
      "generated_catalog_support": true,
      "input_key": "catalog_search",
      "mutable_context": false,
      "path": "C:/tmp/gtos_otb/NOFILLSTATEGAP/research/science_program_2026_05/06_outcome_testing/gtos_local_research_data_catalog_implementation_route/GTOS_LOCAL_RESEARCH_DATA_CATALOG_SEARCH_RESULT_LEDGER_2026-05-10.json",
      "recorded_sha256": "478a89040df92ab1135cd3d566a070b88e20912f41ab9e93bd17330e2df55833",
      "status": "GENERATED_CATALOG_SUPPORT_DRIFT_RECOMPUTED"
    },
    {
      "current_sha256": "4342d835657ebc1f1568a56b8f1b2ded647f3801002d9925fa7818038a530071",
      "generated_catalog_support": false,
      "input_key": "controlling_prompt",
      "mutable_context": false,
      "path": "research/science_program_2026_05/04_goal_prompts/NOFILL_SOURCE_STATE_CAPTURE_GAP_CLOSURE_AND_TICK_EXPORT_MANIFEST_ROUTE_GOAL_PROMPT_2026-05-10.md",
      "recorded_sha256": "4342d835657ebc1f1568a56b8f1b2ded647f3801002d9925fa7818038a530071",
      "status": "MATCH"
    },
    {
      "current_sha256": "7456e6fc368517a635990baa0d914bdeed010a2b3094caf8c0cfc15cc79c1d99",
      "generated_catalog_support": false,
      "input_key": "forward_capture_source",
      "mutable_context": false,
      "path": "src/research_infra/forward_capture.py",
      "recorded_sha256": "7456e6fc368517a635990baa0d914bdeed010a2b3094caf8c0cfc15cc79c1d99",
      "status": "MATCH"
    },
    {
      "current_sha256": "cbb1c4671c54bd78e988cc9380cb8cd6efe5554ce3437d3a12dda0bb4348d66f",
      "generated_catalog_support": false,
      "input_key": "forward_contract_map",
      "mutable_context": false,
      "path": "C:/tmp/gtos_otb/NOFILLSTATEGAP/research/science_program_2026_05/06_outcome_testing/nofill_forward_source_capture_implementation_design_plan/NOFILL_FORWARD_SOURCE_CONTRACT_IMPLEMENTATION_MAP_2026-05-10.json",
      "recorded_sha256": "cbb1c4671c54bd78e988cc9380cb8cd6efe5554ce3437d3a12dda0bb4348d66f",
      "status": "MATCH"
    },
    {
      "current_sha256": "8e727f33420f8fc55a1532f2579333dcea5cc31aa316a0232868bf46ff8a2248",
      "generated_catalog_support": false,
      "input_key": "forward_impl_completion",
      "mutable_context": false,
      "path": "C:/tmp/gtos_otb/NOFILLSTATEGAP/research/science_program_2026_05/06_outcome_testing/nofill_forward_source_capture_additive_logger_implementation/NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_COMPLETION_AUDIT_2026-05-10.json",
      "recorded_sha256": "8e727f33420f8fc55a1532f2579333dcea5cc31aa316a0232868bf46ff8a2248",
      "status": "MATCH"
    },
    {
      "current_sha256": "d7fb754bde9b6eaa09fc01bb7e2ba098dbc5e0007459b1f305b9f013ad3e544d",
      "generated_catalog_support": false,
      "input_key": "forward_impl_coverage",
      "mutable_context": false,
      "path": "C:/tmp/gtos_otb/NOFILLSTATEGAP/research/science_program_2026_05/06_outcome_testing/nofill_forward_source_capture_additive_logger_implementation/NOFILL_FORWARD_SOURCE_CAPTURE_55_FIELD_IMPLEMENTATION_COVERAGE_LEDGER_2026-05-10.json",
      "recorded_sha256": "d7fb754bde9b6eaa09fc01bb7e2ba098dbc5e0007459b1f305b9f013ad3e544d",
      "status": "MATCH"
    },
    {
      "current_sha256": "2db43cd81a2dde1b41ee4a50ffc73d89cdde94ab4c0e1431eecdfe32e23660cd",
      "generated_catalog_support": false,
      "input_key": "forward_parser_schema",
      "mutable_context": false,
      "path": "C:/tmp/gtos_otb/NOFILLSTATEGAP/research/science_program_2026_05/06_outcome_testing/nofill_forward_source_capture_implementation_design_plan/NOFILL_FORWARD_SOURCE_CAPTURE_PARSER_PROJECTION_SCHEMA_2026-05-10.json",
      "recorded_sha256": "2db43cd81a2dde1b41ee4a50ffc73d89cdde94ab4c0e1431eecdfe32e23660cd",
      "status": "MATCH"
    },
    {
      "current_sha256": "b029180c6fcf92327c947d703dbdb2538697d304227fa3eea123e1fb52a497b5",
      "generated_catalog_support": false,
      "input_key": "g0_blocker_ledger",
      "mutable_context": false,
      "path": "C:/tmp/gtos_otb/NOFILLSTATEGAP/research/science_program_2026_05/06_outcome_testing/g0_nofill_historical_source_expansion_packet_synthesis_control_review/G0_NOFILL_HIST_SRCEXP_SYNTHESIS_BLOCKER_ROUTE_LEDGER_2026-05-10.json",
      "recorded_sha256": "b029180c6fcf92327c947d703dbdb2538697d304227fa3eea123e1fb52a497b5",
      "status": "MATCH"
    },
    {
      "current_sha256": "7396733acf44c4435609c0808647675171369a30de94ec0e00e264d10d35c030",
      "generated_catalog_support": false,
      "input_key": "g0_catalog_refresh",
      "mutable_context": false,
      "path": "C:/tmp/gtos_otb/NOFILLSTATEGAP/research/science_program_2026_05/06_outcome_testing/g0_nofill_historical_source_expansion_packet_synthesis_control_review/G0_NOFILL_HIST_SRCEXP_SYNTHESIS_CATALOG_REFRESH_LEDGER_2026-05-10.json",
      "recorded_sha256": "7396733acf44c4435609c0808647675171369a30de94ec0e00e264d10d35c030",
      "status": "MATCH"
    },
    {
      "current_sha256": "d0f44eae45984c7e406fe25238d28d03515afa56572d9f9da6838d29c8fb260f",
      "generated_catalog_support": false,
      "input_key": "g0_completion_audit",
      "mutable_context": false,
      "path": "C:/tmp/gtos_otb/NOFILLSTATEGAP/research/science_program_2026_05/06_outcome_testing/g0_nofill_historical_source_expansion_packet_synthesis_control_review/G0_NOFILL_HIST_SRCEXP_SYNTHESIS_COMPLETION_AUDIT_2026-05-10.json",
      "recorded_sha256": "d0f44eae45984c7e406fe25238d28d03515afa56572d9f9da6838d29c8fb260f",
      "status": "MATCH"
    },
    {
      "current_sha256": "e5c89962d5aa92a8efbbc8307d74cbfffe93a40521f0a70f4f5cfc7225b639c6",
      "generated_catalog_support": false,
      "input_key": "g0_decision",
      "mutable_context": false,
      "path": "C:/tmp/gtos_otb/NOFILLSTATEGAP/research/science_program_2026_05/06_outcome_testing/g0_nofill_historical_source_expansion_packet_synthesis_control_review/G0_NOFILL_HIST_SRCEXP_SYNTHESIS_DECISION_LEDGER_2026-05-10.json",
      "recorded_sha256": "e5c89962d5aa92a8efbbc8307d74cbfffe93a40521f0a70f4f5cfc7225b639c6",
      "status": "MATCH"
    },
    {
      "current_sha256": "92ab779675c47551d9b08b8ce7e009053ecc19a909dfce2531df354fb42d875d",
      "generated_catalog_support": false,
      "input_key": "g0_next_prompt",
      "mutable_context": false,
      "path": "C:/tmp/gtos_otb/NOFILLSTATEGAP/research/science_program_2026_05/06_outcome_testing/g0_nofill_historical_source_expansion_packet_synthesis_control_review/G0_NOFILL_HIST_SRCEXP_SYNTHESIS_NEXT_ROUTE_PROMPT_PACK_2026-05-10.md",
      "recorded_sha256": "92ab779675c47551d9b08b8ce7e009053ecc19a909dfce2531df354fb42d875d",
      "status": "MATCH"
    },
    {
      "current_sha256": "0bae31e27b6b871fa994476dc1f26f540df6970590faf8bcb2c7d1ce1b1e524c",
      "generated_catalog_support": false,
      "input_key": "g0_opportunity_ranking",
      "mutable_context": false,
      "path": "C:/tmp/gtos_otb/NOFILLSTATEGAP/research/science_program_2026_05/06_outcome_testing/g0_nofill_historical_source_expansion_packet_synthesis_control_review/G0_NOFILL_HIST_SRCEXP_SYNTHESIS_SOURCE_EXPANSION_OPPORTUNITY_RANKING_2026-05-10.json",
      "recorded_sha256": "0bae31e27b6b871fa994476dc1f26f540df6970590faf8bcb2c7d1ce1b1e524c",
      "status": "MATCH"
    },
    {
      "current_sha256": "0883ac8977e99a48e0485fb376e9795346c65e82401aa16162c4351d70f9c209",
      "generated_catalog_support": false,
      "input_key": "g0_parallelization",
      "mutable_context": false,
      "path": "C:/tmp/gtos_otb/NOFILLSTATEGAP/research/science_program_2026_05/06_outcome_testing/g0_nofill_historical_source_expansion_packet_synthesis_control_review/G0_NOFILL_HIST_SRCEXP_SYNTHESIS_PARALLELIZATION_DECISION_LEDGER_2026-05-10.json",
      "recorded_sha256": "0883ac8977e99a48e0485fb376e9795346c65e82401aa16162c4351d70f9c209",
      "status": "MATCH"
    },
    {
      "current_sha256": "6c4fad6b8d278f8b56d94e3da3b5e647b21280cfaa07b712f57c1e09991e33fb",
      "generated_catalog_support": false,
      "input_key": "g0_reject_ledger",
      "mutable_context": false,
      "path": "C:/tmp/gtos_otb/NOFILLSTATEGAP/research/science_program_2026_05/06_outcome_testing/g0_nofill_historical_source_expansion_packet_synthesis_control_review/G0_NOFILL_HIST_SRCEXP_SYNTHESIS_REJECT_LEARNING_LEDGER_2026-05-10.json",
      "recorded_sha256": "6c4fad6b8d278f8b56d94e3da3b5e647b21280cfaa07b712f57c1e09991e33fb",
      "status": "MATCH"
    },
    {
      "current_sha256": "a09e6501efd30062a475b57c617aa9987866ae7fd6296410d8b5d0a15931c9c3",
      "generated_catalog_support": false,
      "input_key": "g0_two_admitted_rows",
      "mutable_context": false,
      "path": "C:/tmp/gtos_otb/NOFILLSTATEGAP/research/science_program_2026_05/06_outcome_testing/g0_nofill_historical_source_expansion_packet_synthesis_control_review/G0_NOFILL_HIST_SRCEXP_SYNTHESIS_TWO_ADMITTED_ROW_SYNTHESIS_2026-05-10.json",
      "recorded_sha256": "a09e6501efd30062a475b57c617aa9987866ae7fd6296410d8b5d0a15931c9c3",
      "status": "MATCH"
    },
    {
      "current_sha256": "23341263f349ace629d8b9d09f229441ad5e8b5f03c497508214ba4748421c17",
      "generated_catalog_support": false,
      "input_key": "g12_hash_repair_packet_hash",
      "mutable_context": false,
      "path": "C:/tmp/gtos_otb/NOFILLSTATEGAP/research/science_program_2026_05/06_outcome_testing/g12_nofill_historical_source_expansion_hash_repair_reaudit/G12_NOFILL_HIST_SRCEXP_HASH_REPAIR_REAUDIT_PACKET_HASH_MANIFEST_REAUDIT_2026-05-10.json",
      "recorded_sha256": "23341263f349ace629d8b9d09f229441ad5e8b5f03c497508214ba4748421c17",
      "status": "MATCH"
    },
    {
      "current_sha256": "2598a90a8bb2b5a8dd04c117324d6775f8ec7697e4f0abaeb19513af2baebc6c",
      "generated_catalog_support": false,
      "input_key": "goal_session_research_discipline",
      "mutable_context": true,
      "path": ".context/00_core/goal_session_research_discipline.md",
      "recorded_sha256": "2598a90a8bb2b5a8dd04c117324d6775f8ec7697e4f0abaeb19513af2baebc6c",
      "status": "MATCH"
    },
    {
      "current_sha256": "0662139cbae0ef3ee6a0282af14136b02a9e5c49d5e462b62fd16243a4645235",
      "generated_catalog_support": false,
      "input_key": "latest_handoff",
      "mutable_context": true,
      "path": ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
      "recorded_sha256": "0662139cbae0ef3ee6a0282af14136b02a9e5c49d5e462b62fd16243a4645235",
      "status": "MATCH"
    },
    {
      "current_sha256": "4b28326c15b25fa26e9c7e3f32bfabe50289dc8cf9882b205ef4f369a7e1047c",
      "generated_catalog_support": false,
      "input_key": "live_state",
      "mutable_context": true,
      "path": ".context/LIVE_STATE.md",
      "recorded_sha256": "6da97bd9e3b321f6b338f5e258d8259fc53eb13db63449d18ee971f730a79acf",
      "status": "MUTABLE_CONTEXT_DRIFT_ALLOWED"
    },
    {
      "current_sha256": "b9941a0891ac3afd1ac42f41f59de594e974e928f2ddf08bccf9c237554a26fc",
      "generated_catalog_support": false,
      "input_key": "local_heavy_data_inventory",
      "mutable_context": true,
      "path": ".context/00_core/local_heavy_data_inventory.md",
      "recorded_sha256": "b9941a0891ac3afd1ac42f41f59de594e974e928f2ddf08bccf9c237554a26fc",
      "status": "MATCH"
    },
    {
      "current_sha256": "a639889d645a232f032fe40adca6f114b48b3a23df9e487fbb7901c456ce6c13",
      "generated_catalog_support": false,
      "input_key": "pending_lifecycle_audit",
      "mutable_context": false,
      "path": "shadow_logs/pending_limit_lifecycle_audit.jsonl",
      "recorded_sha256": "a639889d645a232f032fe40adca6f114b48b3a23df9e487fbb7901c456ce6c13",
      "status": "MATCH"
    },
    {
      "current_sha256": "e09d71390f6862a97fe7d40223e1acd1a7914f5350ea6f954e4a84521f6d9ffd",
      "generated_catalog_support": false,
      "input_key": "quick_reference",
      "mutable_context": true,
      "path": ".context/00_core/quick_reference_card.md",
      "recorded_sha256": "e09d71390f6862a97fe7d40223e1acd1a7914f5350ea6f954e4a84521f6d9ffd",
      "status": "MATCH"
    },
    {
      "current_sha256": "b1ad4be00992991b99f9f68713d692a517e3381272f9721ef4bc1c62f615985e",
      "generated_catalog_support": false,
      "input_key": "research_current_state",
      "mutable_context": true,
      "path": ".context/00_core/research_current_state.md",
      "recorded_sha256": "c354dc1aa8803bd20eed7dfc2e21787b5578ecaf6d76026d4ce250e1f6ca1f21",
      "status": "MUTABLE_CONTEXT_DRIFT_ALLOWED"
    },
    {
      "current_sha256": "bd8c1621452000376e6b6521b364c57e56473e69de3f9689bbc98140199e6cfc",
      "generated_catalog_support": false,
      "input_key": "research_doctrine",
      "mutable_context": true,
      "path": ".context/00_core/research_operating_doctrine.md",
      "recorded_sha256": "bed0ae8b92a000a28e4e4a3f07563abbc4913b37bc9ec3ad5cc71d07263dda6d",
      "status": "MUTABLE_CONTEXT_DRIFT_ALLOWED"
    },
    {
      "current_sha256": "de2642202ecaea7376ff6a44fa024d4e9b0216e3c280b3ab2901aeb24797cefb",
      "generated_catalog_support": false,
      "input_key": "upstream_packet_manifest",
      "mutable_context": false,
      "path": "C:/tmp/gtos_otb/NOFILLSTATEGAP/research/science_program_2026_05/06_outcome_testing/nofill_historical_source_expansion_builder_local_tick_shadow_packet/NOFILL_HIST_SOURCE_EXPANSION_CANDIDATE_PACKET_MANIFEST_2026-05-10.json",
      "recorded_sha256": "de2642202ecaea7376ff6a44fa024d4e9b0216e3c280b3ab2901aeb24797cefb",
      "status": "MATCH"
    }
  ],
  "validation_safe": false
}
```
