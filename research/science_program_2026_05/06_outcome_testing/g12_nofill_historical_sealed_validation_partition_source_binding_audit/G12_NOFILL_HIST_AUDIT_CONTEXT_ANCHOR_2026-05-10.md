# Context Anchor

Route: `G12_NOFILL_HISTORICAL_SEALED_VALIDATION_PARTITION_SOURCE_BINDING_AUDIT`
Target route: `NOFILL_HISTORICAL_SEALED_VALIDATION_PARTITION_AND_SOURCE_BINDING`
Promotion posture: `NO_PROMOTION_VERDICT`
Safe flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

## Summary

```json
{
  "artifact_family": "context_anchor",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "forbidden_scope": [
    "validation execution",
    "result/cost scoring",
    "promotion",
    "registry edit",
    "paid/API route",
    "remote push",
    "live restart",
    "prompt/config/risk/permissions/safety/selector/canary change",
    "MT5 order/account/history/deal/position behavior",
    "credentials",
    "live trading behavior"
  ],
  "generated_at_utc": "2026-05-10T03:55:15Z",
  "git_head": "813b810ebe4c869247d01cd6d245d3d596aed104",
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
  "prompt_path": "research/science_program_2026_05/04_goal_prompts/G12_NOFILL_HISTORICAL_SEALED_VALIDATION_PARTITION_SOURCE_BINDING_AUDIT_GOAL_PROMPT_2026-05-10.md",
  "required_context_files_read": [
    ".context/LIVE_STATE.md",
    ".context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md",
    ".context/00_core/quick_reference_card.md",
    ".context/00_core/research_operating_doctrine.md",
    ".context/00_core/research_current_state.md",
    ".context/00_core/goal_session_research_discipline.md",
    ".context/00_core/local_heavy_data_inventory.md",
    ".context/00_READING_ORDER.md",
    "CLAUDE.md"
  ],
  "route_id": "G12_NOFILL_HISTORICAL_SEALED_VALIDATION_PARTITION_SOURCE_BINDING_AUDIT",
  "scope": "G12 source/control audit only",
  "source_manifest": [
    {
      "exists": true,
      "path": "research/science_program_2026_05/04_goal_prompts/G12_NOFILL_HISTORICAL_SEALED_VALIDATION_PARTITION_SOURCE_BINDING_AUDIT_GOAL_PROMPT_2026-05-10.md",
      "role": "controlling_prompt",
      "sha256": "89a97566eed6e958fe8e3fbb11666b256587f7b52d486e5f0453fbe35733e5f4",
      "size_bytes": 11516
    },
    {
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/nofill_historical_sealed_validation_partition_and_source_binding/NOFILL_HISTORICAL_SEALED_VALIDATION_DECISION_LEDGER_2026-05-10.json",
      "role": "target_decision_ledger",
      "sha256": "14e8ebf1514aa1158bcc1c0a1c0012a77942b3d55223ff559f01a4d94c28c76c",
      "size_bytes": 1252
    },
    {
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/nofill_historical_sealed_validation_partition_and_source_binding/NOFILL_HISTORICAL_SEALED_VALIDATION_PARTITION_LEDGER_2026-05-10.json",
      "role": "target_partition_ledger",
      "sha256": "668fee761d354564e91ce179cb4f080ae2a19f0bcc9e580903ffb574449eaa7f",
      "size_bytes": 3591
    },
    {
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/nofill_historical_sealed_validation_partition_and_source_binding/NOFILL_HISTORICAL_SEALED_VALIDATION_PARTITION_ROW_LEDGER_2026-05-10.jsonl",
      "role": "target_partition_rows",
      "sha256": "996280d53cf552bc0d6845e0dd6018755ce5c488ec649d2a9398acb3d64d2c27",
      "size_bytes": 379621
    },
    {
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/nofill_historical_sealed_validation_partition_and_source_binding/NOFILL_HISTORICAL_SEALED_VALIDATION_CONTAMINATION_PROOF_LEDGER_2026-05-10.json",
      "role": "target_contamination_proof",
      "sha256": "f25503f254a88226647d27cf832eef3a304ae5490966253e57de06b5388b0921",
      "size_bytes": 1651
    },
    {
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/nofill_historical_sealed_validation_partition_and_source_binding/NOFILL_HISTORICAL_SEALED_VALIDATION_55_FIELD_SOURCE_BINDING_MATRIX_2026-05-10.json",
      "role": "target_field_matrix",
      "sha256": "21bd926b504e3f6e9214c0dc4289d2f135642da2799df2c80f1927cd497b2508",
      "size_bytes": 69866
    },
    {
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/nofill_historical_sealed_validation_partition_and_source_binding/NOFILL_HISTORICAL_SEALED_VALIDATION_FIELD_BLOCKERS_OWNER_REQUIREMENTS_LEDGER_2026-05-10.json",
      "role": "target_field_blockers",
      "sha256": "d11d1ef93ce6c3913b1960c1de0af596f451ca5b4ed5f841d06995999a80b032",
      "size_bytes": 9010
    },
    {
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/nofill_historical_sealed_validation_partition_and_source_binding/NOFILL_HISTORICAL_SEALED_VALIDATION_DUPLICATE_DENOMINATOR_PURGE_EMBARGO_POLICY_2026-05-10.json",
      "role": "target_duplicate_policy",
      "sha256": "307c1c41ccfc75a31758e7da93809d07adb8569ee16ae71db239243f5082b91d",
      "size_bytes": 2152
    },
    {
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/nofill_historical_sealed_validation_partition_and_source_binding/NOFILL_HISTORICAL_SEALED_VALIDATION_SYMBOL_SESSION_REGIME_SPLIT_READINESS_LEDGER_2026-05-10.json",
      "role": "target_split_readiness",
      "sha256": "0e19c2a6e54ea6ad20d25f588285052ad8d21132e7e5e517c1cd07143daaf056",
      "size_bytes": 2162
    },
    {
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/nofill_historical_sealed_validation_partition_and_source_binding/NOFILL_HISTORICAL_SEALED_VALIDATION_LOCAL_HEAVY_DATA_PRIOR_ARTIFACT_SEARCH_LEDGER_2026-05-10.json",
      "role": "target_local_heavy_search",
      "sha256": "bf1554190d85be52c496e41813a95f30a3266c639cf2685a44ea5d876f1e820a",
      "size_bytes": 11909
    },
    {
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/nofill_historical_sealed_validation_partition_and_source_binding/NOFILL_HISTORICAL_SEALED_VALIDATION_FUTURE_VALIDATION_EXECUTION_PREREQUISITES_2026-05-10.json",
      "role": "target_future_prereqs",
      "sha256": "ab88b375ae1d72ba04d94b49eca0ebde5d20372c18cf6e61c896600fb4b82740",
      "size_bytes": 1775
    },
    {
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/nofill_historical_sealed_validation_partition_and_source_binding/NOFILL_HISTORICAL_SEALED_VALIDATION_COMPLETION_AUDIT_2026-05-10.json",
      "role": "target_completion_audit",
      "sha256": "236a64e5997d0a68551a85f183b7e3b8c2d55e9a4f8c0041db4bfc01bd4ea687",
      "size_bytes": 2435
    },
    {
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/nofill_cat_v3_source_control_rebuild/NOFILL_CAT_V3_ACCEPTED_OR_SOURCE_CONTROL_PACKET_2026-05-09.json",
      "role": "upstream_cat_packet",
      "sha256": "af1b24ac585638b542a1385538312dfa9e708278711e8006e6ee85bb5d8b8464",
      "size_bytes": 359796
    },
    {
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/nofill_cat_v3_source_control_rebuild/NOFILL_CAT_V3_REJECT_LEDGER_2026-05-09.json",
      "role": "upstream_cat_rejects",
      "sha256": "00437e8bf297851cae8922119c5f58c7ad232bb59f76f7992bcd2ab527a6ae74",
      "size_bytes": 110674
    },
    {
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/nofill_cat_v3_source_control_rebuild/NOFILL_CAT_V3_BLOCKER_IMPOSSIBILITY_LEDGER_2026-05-09.json",
      "role": "upstream_cat_source_impossible",
      "sha256": "f91d994cdc707db854ab6af46e07318c2a0a7666b9934dce838bdfedfb65cbc1",
      "size_bytes": 10164
    },
    {
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/nofill_cat_v3_quarantined_categorical_count_packet/NOFILL_CAT_V3_COUNT_ACCEPTED_INPUT_ROWS_2026-05-09.jsonl",
      "role": "upstream_cat_count_rows",
      "sha256": "fece899f3db5a4cce4e9b750ec089d0653eae8bef3dba0b79da8dce2f105e043",
      "size_bytes": 310915
    },
    {
      "exists": true,
      "path": "research/science_program_2026_05/06_outcome_testing/nofill_cat_v3_quarantined_categorical_count_packet/NOFILL_CAT_V3_CATEGORICAL_COUNT_LEDGER_2026-05-09.json",
      "role": "upstream_cat_count_ledger",
      "sha256": "7e79779720d383354f28677e156fa3408db522c6ee61ddeb9f9917d5bdd4b6b7",
      "size_bytes": 32388
    }
  ],
  "target_route_id": "NOFILL_HISTORICAL_SEALED_VALIDATION_PARTITION_AND_SOURCE_BINDING",
  "target_route_path": "research/science_program_2026_05/06_outcome_testing/nofill_historical_sealed_validation_partition_and_source_binding",
  "validation_safe": false
}
```
