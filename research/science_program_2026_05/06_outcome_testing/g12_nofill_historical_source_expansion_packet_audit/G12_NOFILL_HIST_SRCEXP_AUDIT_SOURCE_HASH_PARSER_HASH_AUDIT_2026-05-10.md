# Source Hash And Parser Hash Audit

Route: `G12_NOFILL_HISTORICAL_SOURCE_EXPANSION_PACKET_AUDIT`
Target route: `NOFILL_HISTORICAL_SOURCE_EXPANSION_BUILDER_LOCAL_TICK_SHADOW_PACKET`
Promotion posture: `NO_PROMOTION_VERDICT`
Safe flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

## Summary

```json
{
  "artifact_family": "source_hash_parser_hash_audit",
  "audit_completed": true,
  "audit_passed_clean_without_repair": false,
  "changes_live_trading_behavior": false,
  "checks": {
    "all_non_mutable_hashes_match": false,
    "packet_rows_bind_same_parser_hash": false,
    "parser_manifest_matches_current_target_builder": false,
    "target_builder_verifier_tests_committed": true
  },
  "credentials_touched": false,
  "current_target_builder_hash": "0e637cddb98577de2951759c43288fafb251d70fbcb2457e9a029b1dab59ad3b",
  "generated_at_utc": "2026-05-10T05:28:55Z",
  "live_effect": false,
  "mutable_context_drift_count": 0,
  "mutable_context_drift_records": [],
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
  "packet_row_parser_hashes": [
    "3bd0edb2d183283094f40d58e5889ddd116d3f8b3677853c2e2d75ea330df0d4"
  ],
  "parser_manifest_hash": "3bd0edb2d183283094f40d58e5889ddd116d3f8b3677853c2e2d75ea330df0d4",
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "records": [
    {
      "exists_now": true,
      "hash_matches_manifest": true,
      "manifest_sha256": "f61abba6441b2ff5aba59de365f0995820363b0936c5ee490cce8b1bf6dad73c",
      "mutable_context_classification": "STRICT_HASH_REQUIRED",
      "path": "research\\science_program_2026_05\\04_goal_prompts\\NOFILL_HISTORICAL_SOURCE_EXPANSION_BUILDER_LOCAL_TICK_SHADOW_PACKET_GOAL_PROMPT_2026-05-10.md",
      "recomputed_sha256": "f61abba6441b2ff5aba59de365f0995820363b0936c5ee490cce8b1bf6dad73c",
      "role": "parent_artifact:controlling_prompt",
      "source_contract_id": "accepted_parent_source_control"
    },
    {
      "exists_now": true,
      "hash_matches_manifest": true,
      "manifest_sha256": "3569f3046f249a87ae96378553614548a53f2358cb6e7857bc0e976e181560db",
      "mutable_context_classification": "STRICT_HASH_REQUIRED",
      "path": "research\\science_program_2026_05\\06_outcome_testing\\g0_nofill_historical_partition_source_binding_synthesis_control_review\\G0_NOFILL_HIST_SYNTHESIS_VALIDATION_EXECUTION_CLOSED_GATE_LEDGER_2026-05-10.json",
      "recomputed_sha256": "3569f3046f249a87ae96378553614548a53f2358cb6e7857bc0e976e181560db",
      "role": "parent_artifact:g0_closed_gates",
      "source_contract_id": "accepted_parent_source_control"
    },
    {
      "exists_now": true,
      "hash_matches_manifest": true,
      "manifest_sha256": "ccb6f1006f745f6cfcfc4d28ca4ba3d91f4e6f7deefb1330f22bf597c671b787",
      "mutable_context_classification": "STRICT_HASH_REQUIRED",
      "path": "research\\science_program_2026_05\\06_outcome_testing\\g0_nofill_historical_partition_source_binding_synthesis_control_review\\G0_NOFILL_HIST_SYNTHESIS_DECISION_LEDGER_2026-05-10.json",
      "recomputed_sha256": "ccb6f1006f745f6cfcfc4d28ca4ba3d91f4e6f7deefb1330f22bf597c671b787",
      "role": "parent_artifact:g0_decision",
      "source_contract_id": "accepted_parent_source_control"
    },
    {
      "exists_now": true,
      "hash_matches_manifest": true,
      "manifest_sha256": "82b69dbbedcc5a1b280c49d1d27af2d500b256dde8f3b9395637e56fcc20ddc7",
      "mutable_context_classification": "STRICT_HASH_REQUIRED",
      "path": "research\\science_program_2026_05\\06_outcome_testing\\g0_nofill_historical_partition_source_binding_synthesis_control_review\\G0_NOFILL_HIST_SYNTHESIS_55_FIELD_EXPANSION_BINDING_CHECKLIST_2026-05-10.json",
      "recomputed_sha256": "82b69dbbedcc5a1b280c49d1d27af2d500b256dde8f3b9395637e56fcc20ddc7",
      "role": "parent_artifact:g0_field_checklist",
      "source_contract_id": "accepted_parent_source_control"
    },
    {
      "exists_now": true,
      "hash_matches_manifest": true,
      "manifest_sha256": "1f5539637d384f5e4151d0584914b66f0f1d6fa59edb09077677cefd5b9006f2",
      "mutable_context_classification": "STRICT_HASH_REQUIRED",
      "path": "research\\science_program_2026_05\\06_outcome_testing\\g0_nofill_historical_partition_source_binding_synthesis_control_review\\G0_NOFILL_HIST_SYNTHESIS_LOCAL_HEAVY_PRIOR_ARTIFACT_SEARCH_PLAN_2026-05-10.json",
      "recomputed_sha256": "1f5539637d384f5e4151d0584914b66f0f1d6fa59edb09077677cefd5b9006f2",
      "role": "parent_artifact:g0_local_search",
      "source_contract_id": "accepted_parent_source_control"
    },
    {
      "exists_now": true,
      "hash_matches_manifest": true,
      "manifest_sha256": "8d7bd8b2d9b1d3a7b756a5f064709a628d06d92ea0ae4a5ed467ab4ba2be107e",
      "mutable_context_classification": "STRICT_HASH_REQUIRED",
      "path": "research\\science_program_2026_05\\06_outcome_testing\\g0_nofill_historical_partition_source_binding_synthesis_control_review\\G0_NOFILL_HIST_SYNTHESIS_OWNER_ACCESS_SOURCE_CAPTURE_REQUIREMENTS_LEDGER_2026-05-10.json",
      "recomputed_sha256": "8d7bd8b2d9b1d3a7b756a5f064709a628d06d92ea0ae4a5ed467ab4ba2be107e",
      "role": "parent_artifact:g0_owner_requirements",
      "source_contract_id": "accepted_parent_source_control"
    },
    {
      "exists_now": true,
      "hash_matches_manifest": true,
      "manifest_sha256": "0f22241ab3166f3f51c825b349fd0163a29d62a41a95a78507c50297899ec59a",
      "mutable_context_classification": "STRICT_HASH_REQUIRED",
      "path": "research\\science_program_2026_05\\06_outcome_testing\\g0_nofill_historical_partition_source_binding_synthesis_control_review\\G0_NOFILL_HIST_SYNTHESIS_EXACT_SOURCE_EXPANSION_REQUIREMENTS_MATRIX_2026-05-10.json",
      "recomputed_sha256": "0f22241ab3166f3f51c825b349fd0163a29d62a41a95a78507c50297899ec59a",
      "role": "parent_artifact:g0_requirements",
      "source_contract_id": "accepted_parent_source_control"
    },
    {
      "exists_now": true,
      "hash_matches_manifest": true,
      "manifest_sha256": "638c99da7fb5b197817794fb31f21cb2af0397656efa88ab4804bf1b353f8f86",
      "mutable_context_classification": "STRICT_HASH_REQUIRED",
      "path": "research\\science_program_2026_05\\06_outcome_testing\\g0_nofill_historical_partition_source_binding_synthesis_control_review\\G0_NOFILL_HIST_SYNTHESIS_NOLEAK_DUPLICATE_PURGE_EMBARGO_SOURCE_HASH_RULES_2026-05-10.json",
      "recomputed_sha256": "638c99da7fb5b197817794fb31f21cb2af0397656efa88ab4804bf1b353f8f86",
      "role": "parent_artifact:g0_rules",
      "source_contract_id": "accepted_parent_source_control"
    },
    {
      "exists_now": true,
      "hash_matches_manifest": true,
      "manifest_sha256": "b7d6c441ed7c9b7037490c4a7e9cd862abb098bf2d1632a7a10b2316e5386c93",
      "mutable_context_classification": "STRICT_HASH_REQUIRED",
      "path": "research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_historical_sealed_validation_partition_source_binding_audit\\G12_NOFILL_HIST_AUDIT_CONTAMINATION_PROOF_REAUDIT_2026-05-10.json",
      "recomputed_sha256": "b7d6c441ed7c9b7037490c4a7e9cd862abb098bf2d1632a7a10b2316e5386c93",
      "role": "parent_artifact:g12_contamination",
      "source_contract_id": "accepted_parent_source_control"
    },
    {
      "exists_now": true,
      "hash_matches_manifest": true,
      "manifest_sha256": "d54bfc9f85765ea77a22be396bb99fbe5a0a98a8dbfbd1ab48a3b73b8f7132a5",
      "mutable_context_classification": "STRICT_HASH_REQUIRED",
      "path": "research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_historical_sealed_validation_partition_source_binding_audit\\G12_NOFILL_HIST_AUDIT_DECISION_LEDGER_2026-05-10.json",
      "recomputed_sha256": "d54bfc9f85765ea77a22be396bb99fbe5a0a98a8dbfbd1ab48a3b73b8f7132a5",
      "role": "parent_artifact:g12_decision",
      "source_contract_id": "accepted_parent_source_control"
    },
    {
      "exists_now": true,
      "hash_matches_manifest": true,
      "manifest_sha256": "f25503f254a88226647d27cf832eef3a304ae5490966253e57de06b5388b0921",
      "mutable_context_classification": "STRICT_HASH_REQUIRED",
      "path": "research\\science_program_2026_05\\06_outcome_testing\\nofill_historical_sealed_validation_partition_and_source_binding\\NOFILL_HISTORICAL_SEALED_VALIDATION_CONTAMINATION_PROOF_LEDGER_2026-05-10.json",
      "recomputed_sha256": "f25503f254a88226647d27cf832eef3a304ae5490966253e57de06b5388b0921",
      "role": "parent_artifact:target_contamination",
      "source_contract_id": "accepted_parent_source_control"
    },
    {
      "exists_now": true,
      "hash_matches_manifest": true,
      "manifest_sha256": "307c1c41ccfc75a31758e7da93809d07adb8569ee16ae71db239243f5082b91d",
      "mutable_context_classification": "STRICT_HASH_REQUIRED",
      "path": "research\\science_program_2026_05\\06_outcome_testing\\nofill_historical_sealed_validation_partition_and_source_binding\\NOFILL_HISTORICAL_SEALED_VALIDATION_DUPLICATE_DENOMINATOR_PURGE_EMBARGO_POLICY_2026-05-10.json",
      "recomputed_sha256": "307c1c41ccfc75a31758e7da93809d07adb8569ee16ae71db239243f5082b91d",
      "role": "parent_artifact:target_duplicate_policy",
      "source_contract_id": "accepted_parent_source_control"
    },
    {
      "exists_now": true,
      "hash_matches_manifest": true,
      "manifest_sha256": "996280d53cf552bc0d6845e0dd6018755ce5c488ec649d2a9398acb3d64d2c27",
      "mutable_context_classification": "STRICT_HASH_REQUIRED",
      "path": "research\\science_program_2026_05\\06_outcome_testing\\nofill_historical_sealed_validation_partition_and_source_binding\\NOFILL_HISTORICAL_SEALED_VALIDATION_PARTITION_ROW_LEDGER_2026-05-10.jsonl",
      "recomputed_sha256": "996280d53cf552bc0d6845e0dd6018755ce5c488ec649d2a9398acb3d64d2c27",
      "role": "parent_artifact:target_partition_rows",
      "source_contract_id": "accepted_parent_source_control"
    },
    {
      "exists_now": true,
      "hash_matches_manifest": true,
      "manifest_sha256": "0ed23ea479b2a98a98021a67c838c7b27f9c0a2ee280193cefa25d8a01ed208f",
      "mutable_context_classification": "MUTABLE_SHADOW_LOG_CONTEXT_DRIFT_ALLOWED",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\candidate_ltf_path_order.jsonl",
      "recomputed_sha256": "0ed23ea479b2a98a98021a67c838c7b27f9c0a2ee280193cefa25d8a01ed208f",
      "role": "raw_shadow_log",
      "source_contract_id": "local_shadow_source"
    },
    {
      "exists_now": true,
      "hash_matches_manifest": true,
      "manifest_sha256": "624f58663c7f78e3aaccce0dc4d213b16ddd2983baf2cbf4c4ba5f1cb9140dbc",
      "mutable_context_classification": "MUTABLE_SHADOW_LOG_CONTEXT_DRIFT_ALLOWED",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\candidate_path_follow.jsonl",
      "recomputed_sha256": "624f58663c7f78e3aaccce0dc4d213b16ddd2983baf2cbf4c4ba5f1cb9140dbc",
      "role": "raw_shadow_log",
      "source_contract_id": "local_shadow_source"
    },
    {
      "exists_now": true,
      "hash_matches_manifest": true,
      "manifest_sha256": "1183d41f8af0914d1d398c1bda2d1cf6b9147f88c0c24e10a178a9697d78b5b0",
      "mutable_context_classification": "MUTABLE_SHADOW_LOG_CONTEXT_DRIFT_ALLOWED",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\candidate_registry_audit.jsonl",
      "recomputed_sha256": "1183d41f8af0914d1d398c1bda2d1cf6b9147f88c0c24e10a178a9697d78b5b0",
      "role": "raw_shadow_log",
      "source_contract_id": "local_shadow_source"
    },
    {
      "exists_now": true,
      "hash_matches_manifest": true,
      "manifest_sha256": "f0c45eb94d70b94e9e4eb6aebcb4943f3864a7f1cdb37c6003631337e8b9ad49",
      "mutable_context_classification": "MUTABLE_SHADOW_LOG_CONTEXT_DRIFT_ALLOWED",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\pending_limit_lifecycle.jsonl",
      "recomputed_sha256": "f0c45eb94d70b94e9e4eb6aebcb4943f3864a7f1cdb37c6003631337e8b9ad49",
      "role": "raw_shadow_log",
      "source_contract_id": "local_shadow_source"
    },
    {
      "exists_now": true,
      "hash_matches_manifest": true,
      "manifest_sha256": "a639889d645a232f032fe40adca6f114b48b3a23df9e487fbb7901c456ce6c13",
      "mutable_context_classification": "MUTABLE_SHADOW_LOG_CONTEXT_DRIFT_ALLOWED",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\pending_limit_lifecycle_audit.jsonl",
      "recomputed_sha256": "a639889d645a232f032fe40adca6f114b48b3a23df9e487fbb7901c456ce6c13",
      "role": "raw_shadow_log",
      "source_contract_id": "local_shadow_source"
    },
    {
      "exists_now": true,
      "hash_matches_manifest": true,
      "manifest_sha256": "5ba5af2f5b1a9561397ecd0adf397fd4eeba942fe9c218f066c74288436b9e31",
      "mutable_context_classification": "STRICT_HASH_REQUIRED",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\NAS100\\2026-05-08.parquet",
      "recomputed_sha256": "5ba5af2f5b1a9561397ecd0adf397fd4eeba942fe9c218f066c74288436b9e31",
      "role": "raw_tick_parquet_admitted_row_source",
      "source_contract_id": "local_mt5_tick_parquet"
    },
    {
      "exists_now": true,
      "hash_matches_manifest": true,
      "manifest_sha256": "bfed917d099ba990458319e4c607e405e3a53de458be13d9dc893be011fc4cd6",
      "mutable_context_classification": "STRICT_HASH_REQUIRED",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\US30_cash\\2026-05-08.parquet",
      "recomputed_sha256": "bfed917d099ba990458319e4c607e405e3a53de458be13d9dc893be011fc4cd6",
      "role": "raw_tick_parquet_admitted_row_source",
      "source_contract_id": "local_mt5_tick_parquet"
    },
    {
      "exists_now": true,
      "hash_matches_manifest": false,
      "manifest_sha256": "3bd0edb2d183283094f40d58e5889ddd116d3f8b3677853c2e2d75ea330df0d4",
      "mutable_context_classification": "STRICT_HASH_REQUIRED",
      "path": "research\\science_program_2026_05\\06_outcome_testing\\nofill_historical_source_expansion_builder_local_tick_shadow_packet\\build_nofill_historical_source_expansion_builder_local_tick_shadow_packet_2026_05_10.py",
      "recomputed_sha256": "0e637cddb98577de2951759c43288fafb251d70fbcb2457e9a029b1dab59ad3b",
      "role": "parser_or_verifier:builder",
      "source_contract_id": "route_parser_verifier_code"
    },
    {
      "exists_now": true,
      "hash_matches_manifest": false,
      "manifest_sha256": "209f51ac1400e2dcb3d9eb0528a2bbcec1c95dfa3749b867d379f8ab18455567",
      "mutable_context_classification": "STRICT_HASH_REQUIRED",
      "path": "research\\science_program_2026_05\\06_outcome_testing\\nofill_historical_source_expansion_builder_local_tick_shadow_packet\\test_nofill_historical_source_expansion_builder_local_tick_shadow_packet_2026_05_10.py",
      "recomputed_sha256": "472dd4b2be228bac59017b4aabb5934dfe150819fdc8007bcd08a9fa38ab75e1",
      "role": "parser_or_verifier:focused_tests",
      "source_contract_id": "route_parser_verifier_code"
    },
    {
      "exists_now": true,
      "hash_matches_manifest": true,
      "manifest_sha256": "7456e6fc368517a635990baa0d914bdeed010a2b3094caf8c0cfc15cc79c1d99",
      "mutable_context_classification": "STRICT_HASH_REQUIRED",
      "path": "src\\research_infra\\forward_capture.py",
      "recomputed_sha256": "7456e6fc368517a635990baa0d914bdeed010a2b3094caf8c0cfc15cc79c1d99",
      "role": "parser_or_verifier:forward_capture_contract",
      "source_contract_id": "route_parser_verifier_code"
    },
    {
      "exists_now": true,
      "hash_matches_manifest": false,
      "manifest_sha256": "4a750bdf1fdb4c016c01fac04d69bbd40ee991275ad42bdb2ea1430ec5d333da",
      "mutable_context_classification": "STRICT_HASH_REQUIRED",
      "path": "research\\science_program_2026_05\\06_outcome_testing\\nofill_historical_source_expansion_builder_local_tick_shadow_packet\\verify_nofill_historical_source_expansion_builder_local_tick_shadow_packet_2026_05_10.py",
      "recomputed_sha256": "ebeae4746221ff30a968a41ef8a938bb15d6f1a1f9fc346621ccae6dcfbf9ea5",
      "role": "parser_or_verifier:verifier",
      "source_contract_id": "route_parser_verifier_code"
    }
  ],
  "source_record_count": 24,
  "strict_hash_blocker_count": 3,
  "validation_safe": false
}
```

## Notes

- Mutable shadow-log drift is not used as a packet blocker; strict parser/tick/committed artifact mismatches are blockers.
