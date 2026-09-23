# Context And Target Input Inventory

```json
{
  "all_required_inputs_disk_backed": true,
  "artifact_family": "context_and_target_input_inventory",
  "audit_lane": "G12 fair-adversarial acceptance audit",
  "changes_trading_risk_safety_prompt_decision_behavior": false,
  "credentials_touched": false,
  "evidence_class": "G12_SCID_EXPANSION_CANDIDATE_ACCEPTANCE_DESIGN_AUDIT_ONLY",
  "generated_at_utc": "2026-05-12T18:06:35Z",
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
  "parseable_json_target_inputs": [
    "accepted_source_mapping",
    "accepted_terminal_status",
    "g0_expansion_ledger",
    "g12_noapi_expansion_quarantine",
    "target_completion",
    "target_criteria",
    "target_inventory",
    "target_manifest",
    "target_negative",
    "target_quarantine",
    "target_ranking",
    "target_source_matrix",
    "target_verification"
  ],
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "required_context_files": [
    {
      "bytes": 13281,
      "exists": true,
      "path": ".context/LIVE_STATE.md",
      "sha256": "930a60633a6a0f1adc8cef7e4cae9fd57d69bcfbfc395352af59bad54ef836ca"
    },
    {
      "bytes": 38422,
      "exists": true,
      "path": ".context/00_core/goal_session_research_discipline.md",
      "sha256": "61b02d954ee8cabb393ea4d3976b587834f7fe3d458588aabc7dea62f0588a3f"
    },
    {
      "bytes": 18642,
      "exists": true,
      "path": ".context/00_core/research_operating_doctrine.md",
      "sha256": "0114d5a0b7855a6a24a71154a2d5254f35a766208effb9e4ac4270c547104c3d"
    },
    {
      "bytes": 922819,
      "exists": true,
      "path": ".context/00_core/research_current_state.md",
      "sha256": "93fb328878325c0a22a6bff06c80afb43cdad4c5c3c4ee22201d6887bda626c0"
    },
    {
      "bytes": 7418,
      "exists": true,
      "path": ".context/00_core/local_heavy_data_inventory.md",
      "sha256": "b9941a0891ac3afd1ac42f41f59de594e974e928f2ddf08bccf9c237554a26fc"
    },
    {
      "bytes": 5863,
      "exists": true,
      "path": "research/science_program_2026_05/04_goal_prompts/G0NAPI_R4_EXPANSION_DESIGN_GOAL_PROMPT_2026-05-12.md",
      "sha256": "1b97871d4828fdedc472934458ebc77d79dba1c0472172f7bef14ae58fdccc8c"
    },
    {
      "bytes": 3029,
      "exists": true,
      "path": "research/science_program_2026_05/04_goal_prompts/G12_SCID_EXPANSION_CANDIDATE_ACCEPTANCE_DESIGN_AUDIT_GOAL_PROMPT_2026-05-12.md",
      "sha256": "64aef898f3eb53466fbf3af33cf3fe0fe460078272bde1b53abb437f51d65c21"
    }
  ],
  "route_id": "G12_SCID_EXPANSION_CANDIDATE_ACCEPTANCE_DESIGN_AUDIT",
  "schema_version": "g12_scid_expansion_audit_v1",
  "target_and_upstream_artifact_hashes": {
    "accepted_source_mapping": {
      "bytes": 181236,
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_noapi_40card_prereg_input_design/SCID_NO_API_40_CARD_8_DOMAIN_PREREG_REPLAY_INPUT_DESIGN_SOURCE_FIELD_MAPPING_MATRIX_2026-05-12.json",
      "sha256": "bf1216dbd969d3239c187a1f5d335e00a4fadbd967b46760e50ea38a57288e33"
    },
    "accepted_terminal_status": {
      "bytes": 31330,
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_noapi_40card_prereg_input_design/SCID_NO_API_40_CARD_8_DOMAIN_PREREG_REPLAY_INPUT_DESIGN_PER_CARD_TERMINAL_STATUS_LEDGER_2026-05-12.json",
      "sha256": "8919cb7a1d747d98fc0bd17c238f0fb5b9bca65f0b00015c574276254c2b53b0"
    },
    "g0_expansion_ledger": {
      "bytes": 8061,
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/g0_scid_noapi_40card_prereg_replay_input_design_synthesis/G0_SCID_NOAPI_PREREG_SYNTHESIS_EXPANSION_CANDIDATE_LEDGER_2026-05-12.json",
      "sha256": "a0e5cbb4f537f3b5c4d04ce29e2a427bcefb8b7246503d2dcfbf738ae203637e"
    },
    "g12_noapi_expansion_quarantine": {
      "bytes": 4499,
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/g12_scid_noapi_40card_prereg_replay_input_design_audit/G12_SCID_NOAPI_PREREG_AUDIT_EXPANSION_CANDIDATE_QUARANTINE_AUDIT_2026-05-12.json",
      "sha256": "5331117c89ca03d33a3a33b1c13295f90e4ffce4af85a91860b29bf6568bc5cb"
    },
    "target_builder": {
      "bytes": 61206,
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_expansion_candidate_acceptance_and_design_route/build_scid_expansion_candidate_acceptance_and_design_route_2026_05_12.py",
      "sha256": "9db2047e3246b92d29a593fdeb1fcb24e9ed726dd5406e9e7c4704115e4c0103"
    },
    "target_completion": {
      "bytes": 3761,
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_expansion_candidate_acceptance_and_design_route/SCID_EXPANSION_COMPLETION_AUDIT_2026-05-12.json",
      "sha256": "8d462c79b69c1583a6f2cf2aa5cdfe8d7a60677c7918b4ec2dbc8ab2aaf4df36"
    },
    "target_criteria": {
      "bytes": 47813,
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_expansion_candidate_acceptance_and_design_route/SCID_EXPANSION_ACCEPTANCE_REJECTION_CRITERIA_2026-05-12.json",
      "sha256": "603940d925e3173e52502daf215eac0142284cedf3a48bc4dc47fd5cc43b006e"
    },
    "target_inventory": {
      "bytes": 171994,
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_expansion_candidate_acceptance_and_design_route/SCID_EXPANSION_CANDIDATE_INVENTORY_2026-05-12.json",
      "sha256": "7c1fdb4b1ac4b7f1e419400f060f137347480f9e031a97cd4ad68a1c68b07dd6"
    },
    "target_manifest": {
      "bytes": 3799,
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_expansion_candidate_acceptance_and_design_route/SCID_EXPANSION_OUTPUT_MANIFEST_2026-05-12.json",
      "sha256": "8608bb1187fe2aef5f94bdf7b066283f98508c7ccc283a539581f92e4930bd3a"
    },
    "target_negative": {
      "bytes": 70872,
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_expansion_candidate_acceptance_and_design_route/SCID_EXPANSION_NEGATIVE_EVIDENCE_AND_BOXING_AUDIT_2026-05-12.json",
      "sha256": "5120a57e5353512645d460d74383a08f455e66c43cf20b437b76dbc8156470f8"
    },
    "target_quarantine": {
      "bytes": 2809,
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_expansion_candidate_acceptance_and_design_route/SCID_EXPANSION_DENOMINATOR_QUARANTINE_PROOF_2026-05-12.json",
      "sha256": "b1cee255e38ff8a89a1a5fdd207d1cdc1e7706b18ae00edc3cc004c7fe3e7d48"
    },
    "target_ranking": {
      "bytes": 20853,
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_expansion_candidate_acceptance_and_design_route/SCID_EXPANSION_ROUTE_RANKING_MATRIX_2026-05-12.json",
      "sha256": "f27fa6b7a5b6dc902b6f170443ca123902507b7bf28b7607f332e66d343c38cd"
    },
    "target_saturation": {
      "bytes": 2097,
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_expansion_candidate_acceptance_and_design_route/SCID_EXPANSION_SATURATION_SELF_RED_TEAM_2026-05-12.md",
      "sha256": "b4fb6dee1990867d60b2bececc9ffc79a8a2c296154c7d85cb493f5fa801b357"
    },
    "target_source_matrix": {
      "bytes": 49407,
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_expansion_candidate_acceptance_and_design_route/SCID_EXPANSION_SOURCE_FIELD_DESIGN_MATRIX_2026-05-12.json",
      "sha256": "6675e206568fa43cb82fb42d018528ce48580d19b9de1a8e8a6dc2f59bd8bd0c"
    },
    "target_tests": {
      "bytes": 4904,
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_expansion_candidate_acceptance_and_design_route/test_scid_expansion_candidate_acceptance_and_design_route_2026_05_12.py",
      "sha256": "2dcc49b2ad123d9cca7cc53339c87345176cc284d76c076f01429c329765a832"
    },
    "target_verification": {
      "bytes": 809,
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_expansion_candidate_acceptance_and_design_route/SCID_EXPANSION_VERIFICATION_RESULT_2026-05-12.json",
      "sha256": "f05ee3d9c9c8562623712dee7a533920a50de693d8ae5e90b4153ea41be70887"
    },
    "target_verifier": {
      "bytes": 12458,
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/scid_expansion_candidate_acceptance_and_design_route/verify_scid_expansion_candidate_acceptance_and_design_route_2026_05_12.py",
      "sha256": "630689e623dec3c26cf4d8b58d6a13fa2633a58b924051b6e32255e128eb9288"
    }
  },
  "target_route_dir": "research/science_program_2026_05/06_outcome_testing/scid_expansion_candidate_acceptance_and_design_route",
  "validation_safe": false
}
```
