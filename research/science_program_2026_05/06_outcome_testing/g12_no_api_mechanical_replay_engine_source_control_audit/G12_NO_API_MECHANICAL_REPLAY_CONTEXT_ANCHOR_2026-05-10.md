# Context Anchor

- status=recorded
- promotion_verdict=NO_PROMOTION_VERDICT
- validation_safe=false outcome_review_opened=false live_effect=false

```json
{
  "artifact_family": "context_anchor",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "evidence_class": "G12_SOURCE_CONTROL_AUDIT_ONLY",
  "expected_counts": {
    "candidate_inventory_row_count": 13540033,
    "candidate_rows_written": 120000,
    "excluded_source_slice_count": 3135,
    "large_file_hash_resolution_count": 18,
    "opened_family_count": 11,
    "path_label_row_count": 12852758,
    "path_label_rows_written": 120000,
    "selected_source_count": 365,
    "source_universe_rows_consumed": 3500
  },
  "g12_route_path": "research\\science_program_2026_05\\06_outcome_testing\\g12_no_api_mechanical_replay_engine_source_control_audit",
  "generated_at_utc": "2026-05-10T21:10:29+00:00",
  "head_at_audit": "46326250 docs: refresh state after mechanical replay dirty-state hardening",
  "live_effect": false,
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
  "prompt_path": "research\\science_program_2026_05\\04_goal_prompts\\G12_NO_API_MECHANICAL_REPLAY_ENGINE_SOURCE_CONTROL_AUDIT_GOAL_PROMPT_2026-05-10.md",
  "route_id": "G12_NO_API_MECHANICAL_REPLAY_ENGINE_SOURCE_CONTROL_AUDIT",
  "schema_version": "g12_no_api_mechanical_replay_source_control_audit_v1",
  "target_code_and_artifact_hashes": [
    {
      "path": "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\NO_API_MECHANICAL_REPLAY_CANDIDATE_INVENTORY_2026-05-10.json",
      "sha256": "cabed0e8ff0a691d8e29510364b3c3da5039813d0a57e4c3e73ac4aa8ed519a9",
      "size_bytes": 3959
    },
    {
      "path": "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\NO_API_MECHANICAL_REPLAY_COMPLETION_AUDIT_2026-05-10.json",
      "sha256": "dd0c592ecface8c2c334eaaa500ee1adbcca54d1d493330e3159a2b84a8a6e41",
      "size_bytes": 7378
    },
    {
      "path": "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\NO_API_MECHANICAL_REPLAY_CONTEXT_ANCHOR_2026-05-10.json",
      "sha256": "829e21f2e614237096a0c34d476652d5a9637a7b34325ec10f70ade12198445f",
      "size_bytes": 2705
    },
    {
      "path": "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\NO_API_MECHANICAL_REPLAY_DISCOVERY_PATH_LABEL_INVENTORY_2026-05-10.json",
      "sha256": "0c0c358f222f6a3c242901780e6f102faf392519535ce2ae6ef2f11d9c3118f1",
      "size_bytes": 2481
    },
    {
      "path": "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\NO_API_MECHANICAL_REPLAY_EXCLUDED_SLICE_LEDGER_2026-05-10.json",
      "sha256": "fb2e435eb484d8980fb3b0d64979a6abfe3d665073dbaf6c051d95b9b6e3f0ad",
      "size_bytes": 2204048
    },
    {
      "path": "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\NO_API_MECHANICAL_REPLAY_FAMILY_TERMINAL_STATUS_LEDGER_2026-05-10.json",
      "sha256": "b17ac914a248ab74e50635c03aeec28ec12b30e91175271e647d29a6e81569a3",
      "size_bytes": 7701
    },
    {
      "path": "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\NO_API_MECHANICAL_REPLAY_FROZEN_REPLAY_SCHEMA_AND_POLICY_2026-05-10.json",
      "sha256": "2465e0f73f57beb48dd0cd3c82d4c4e4f76d06444aba74f00a40a1f693ad62e6",
      "size_bytes": 2726
    },
    {
      "path": "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\NO_API_MECHANICAL_REPLAY_MECHANICAL_FAMILY_REGISTRY_2026-05-10.json",
      "sha256": "9ff9deb262e602a79c9d4508594a9f67df2658186d4e454cb325afeda25f73a2",
      "size_bytes": 8281
    },
    {
      "path": "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\NO_API_MECHANICAL_REPLAY_NEXT_PROMPT_PACK_2026-05-10.json",
      "sha256": "c5f5ccc38d4ec90cc31c46718ef185882d6ae4f09e6acd6d5e2c9d5f7c20e11c",
      "size_bytes": 2829
    },
    {
      "path": "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\NO_API_MECHANICAL_REPLAY_NOLEAK_AUDIT_2026-05-10.json",
      "sha256": "ef400e827f7f83c9882e8a263496bdc0cf359208d412711b2a745ec8c9a1729d",
      "size_bytes": 1280
    },
    {
      "path": "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\NO_API_MECHANICAL_REPLAY_OUTPUT_MANIFEST_2026-05-10.json",
      "sha256": "5adc913997e2fefe2131966b4c4fa8e785bc2142c70206e9320be3897d20d220",
      "size_bytes": 8405
    },
    {
      "path": "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\NO_API_MECHANICAL_REPLAY_SAME_EVIDENCE_CLASS_CONTINUATION_LEDGER_2026-05-10.json",
      "sha256": "087277da0a06f544f33be5e53ddc81d35807ebf96e88122d5f6f2c333b64c8aa",
      "size_bytes": 2165
    },
    {
      "path": "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\NO_API_MECHANICAL_REPLAY_SATURATION_SELF_REDTEAM_PASS_2026-05-10.json",
      "sha256": "1439b934248fe41891635e16bc4839ede5552e3312997d27ca47badaa04a89a7",
      "size_bytes": 2438
    },
    {
      "path": "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\NO_API_MECHANICAL_REPLAY_SEARCHED_ROOT_LEDGER_2026-05-10.json",
      "sha256": "3882dd7e2a360c239e4b58010c6f0466868d28b1e99a56bd2a19ebbc1dc05570",
      "size_bytes": 6213
    },
    {
      "path": "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\NO_API_MECHANICAL_REPLAY_SOURCE_SELECTION_AND_HASH_LEDGER_2026-05-10.json",
      "sha256": "b342981c867a1ab7aaea3e912417bd7bb05eb6b7c366728f0f2b63cd0033162c",
      "size_bytes": 174254
    },
    {
      "path": "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\NO_API_MECHANICAL_REPLAY_VERIFICATION_RESULT_2026-05-10.json",
      "sha256": "4633d802674f13dd8f4485bc4972711a38697c20b70a627ecbea834aacf62290",
      "size_bytes": 948
    },
    {
      "path": "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\NO_API_MECHANICAL_REPLAY_CANDIDATE_INVENTORY_ROWS_2026-05-10.jsonl",
      "sha256": "48442dd5db7aa00e6a48770548ded751227aeec3a22481f6a203d52c153a96b6",
      "size_bytes": 205437302
    },
    {
      "path": "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\NO_API_MECHANICAL_REPLAY_DISCOVERY_PATH_LABEL_ROWS_2026-05-10.jsonl",
      "sha256": "78bca50ebb33a0eb5845494e8e2bc4b12196d198d0027aedb9966c0b74673e7a",
      "size_bytes": 170589802
    },
    {
      "path": "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\NO_API_MECHANICAL_REPLAY_SOURCE_PROGRESS_2026-05-10.jsonl",
      "sha256": "2a9196a0c24c669aaeb7b94bff60a5b0393540edc3045c63a531b890a4f49772",
      "size_bytes": 180302
    }
  ],
  "target_prompt_path": "research\\science_program_2026_05\\04_goal_prompts\\NO_API_MECHANICAL_REPLAY_ENGINE_FROM_SOURCE_UNIVERSE_GOAL_PROMPT_2026-05-10.md",
  "target_required_artifacts": [
    "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\NO_API_MECHANICAL_REPLAY_CONTEXT_ANCHOR_2026-05-10.json",
    "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\NO_API_MECHANICAL_REPLAY_FROZEN_REPLAY_SCHEMA_AND_POLICY_2026-05-10.json",
    "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\NO_API_MECHANICAL_REPLAY_MECHANICAL_FAMILY_REGISTRY_2026-05-10.json",
    "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\NO_API_MECHANICAL_REPLAY_SOURCE_SELECTION_AND_HASH_LEDGER_2026-05-10.json",
    "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\NO_API_MECHANICAL_REPLAY_CANDIDATE_INVENTORY_2026-05-10.json",
    "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\NO_API_MECHANICAL_REPLAY_CANDIDATE_INVENTORY_ROWS_2026-05-10.jsonl",
    "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\NO_API_MECHANICAL_REPLAY_DISCOVERY_PATH_LABEL_INVENTORY_2026-05-10.json",
    "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\NO_API_MECHANICAL_REPLAY_DISCOVERY_PATH_LABEL_ROWS_2026-05-10.jsonl",
    "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\NO_API_MECHANICAL_REPLAY_FAMILY_TERMINAL_STATUS_LEDGER_2026-05-10.json",
    "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\NO_API_MECHANICAL_REPLAY_SEARCHED_ROOT_LEDGER_2026-05-10.json",
    "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\NO_API_MECHANICAL_REPLAY_SAME_EVIDENCE_CLASS_CONTINUATION_LEDGER_2026-05-10.json",
    "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\NO_API_MECHANICAL_REPLAY_EXCLUDED_SLICE_LEDGER_2026-05-10.json",
    "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\NO_API_MECHANICAL_REPLAY_NOLEAK_AUDIT_2026-05-10.json",
    "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\NO_API_MECHANICAL_REPLAY_SATURATION_SELF_REDTEAM_PASS_2026-05-10.json",
    "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\NO_API_MECHANICAL_REPLAY_NEXT_PROMPT_PACK_2026-05-10.json",
    "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\NO_API_MECHANICAL_REPLAY_COMPLETION_AUDIT_2026-05-10.json",
    "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\NO_API_MECHANICAL_REPLAY_OUTPUT_MANIFEST_2026-05-10.json",
    "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\NO_API_MECHANICAL_REPLAY_SOURCE_PROGRESS_2026-05-10.jsonl",
    "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\NO_API_MECHANICAL_REPLAY_VERIFICATION_RESULT_2026-05-10.json",
    "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\build_no_api_mechanical_replay_engine_from_source_universe_2026_05_10.py",
    "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\verify_no_api_mechanical_replay_engine_from_source_universe_2026_05_10.py",
    "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe\\test_no_api_mechanical_replay_engine_from_source_universe_2026_05_10.py"
  ],
  "target_route_path": "research\\science_program_2026_05\\06_outcome_testing\\no_api_mechanical_replay_engine_from_source_universe",
  "validation_safe": false
}
```
