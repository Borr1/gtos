# NOFILL Source Expansion Parser Hash Repair Target Artifact Mutation Ledger

Route: `NOFILL_HISTORICAL_SOURCE_EXPANSION_PACKET_PARSER_HASH_REPAIR_REBUILD`
Terminal decision: `REPAIR_REBUILD_READY_FOR_G12_REAUDIT`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Summary

```json
{
  "artifact_family": "target_artifact_mutation_ledger",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "generated_at_utc": "2026-05-10T05:51:30Z",
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
  "packet_hash_mutation": {
    "after_packet_sha256": "5f3d2713a17393590fa85984a2c761403faa3d40c6ad018bfa1b32d3ddaf8341",
    "before_packet_sha256": "2c8dd8ff4b3e660bea7978a22a84e309ce98f3d95d9db0221fd13957481aa480",
    "packet_manifest_path": "research\\science_program_2026_05\\06_outcome_testing\\nofill_historical_source_expansion_builder_local_tick_shadow_packet\\NOFILL_HIST_SOURCE_EXPANSION_CANDIDATE_PACKET_MANIFEST_2026-05-10.json",
    "packet_path": "research\\science_program_2026_05\\06_outcome_testing\\nofill_historical_source_expansion_builder_local_tick_shadow_packet\\NOFILL_HIST_SOURCE_EXPANSION_SOURCE_BOUND_CANDIDATE_PACKET_2026-05-10.jsonl",
    "reason": "Packet row parser_code_hash/source_artifact_hash changed, so packet SHA changed."
  },
  "parser_asof_mutation": {
    "after": "0e637cddb98577de2951759c43288fafb251d70fbcb2457e9a029b1dab59ad3b",
    "before": "3bd0edb2d183283094f40d58e5889ddd116d3f8b3677853c2e2d75ea330df0d4",
    "changed": true,
    "path": "research\\science_program_2026_05\\06_outcome_testing\\nofill_historical_source_expansion_builder_local_tick_shadow_packet\\NOFILL_HIST_SOURCE_EXPANSION_PARSER_ASOF_MANIFEST_2026-05-10.json",
    "reason": "Bind parser_asof manifest to current target builder strict hash."
  },
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "route_id": "NOFILL_HISTORICAL_SOURCE_EXPANSION_PACKET_PARSER_HASH_REPAIR_REBUILD",
  "schema_version": "nofill_historical_source_expansion_packet_parser_hash_repair_rebuild_v1",
  "source_manifest_record_mutations": [
    {
      "after": {
        "mtime_utc": "2026-05-10T05:39:55Z",
        "sha256": "0e637cddb98577de2951759c43288fafb251d70fbcb2457e9a029b1dab59ad3b",
        "size_bytes": 75914
      },
      "before": {
        "mtime_utc": "2026-05-10T04:59:25Z",
        "sha256": "3bd0edb2d183283094f40d58e5889ddd116d3f8b3677853c2e2d75ea330df0d4",
        "size_bytes": 74299
      },
      "changed": true,
      "path": "research\\science_program_2026_05\\06_outcome_testing\\nofill_historical_source_expansion_builder_local_tick_shadow_packet\\build_nofill_historical_source_expansion_builder_local_tick_shadow_packet_2026_05_10.py",
      "reason": "Refresh strict parser/verifier code hash binding to current committed target file.",
      "role": "parser_or_verifier:builder"
    },
    {
      "after": {
        "mtime_utc": "2026-05-10T05:39:55Z",
        "sha256": "472dd4b2be228bac59017b4aabb5934dfe150819fdc8007bcd08a9fa38ab75e1",
        "size_bytes": 4814
      },
      "before": {
        "mtime_utc": "2026-05-10T05:00:31Z",
        "sha256": "209f51ac1400e2dcb3d9eb0528a2bbcec1c95dfa3749b867d379f8ab18455567",
        "size_bytes": 4705
      },
      "changed": true,
      "path": "research\\science_program_2026_05\\06_outcome_testing\\nofill_historical_source_expansion_builder_local_tick_shadow_packet\\test_nofill_historical_source_expansion_builder_local_tick_shadow_packet_2026_05_10.py",
      "reason": "Refresh strict parser/verifier code hash binding to current committed target file.",
      "role": "parser_or_verifier:focused_tests"
    },
    {
      "after": {
        "mtime_utc": "2026-05-10T05:39:55Z",
        "sha256": "ebeae4746221ff30a968a41ef8a938bb15d6f1a1f9fc346621ccae6dcfbf9ea5",
        "size_bytes": 14128
      },
      "before": {
        "mtime_utc": "2026-05-10T04:59:11Z",
        "sha256": "4a750bdf1fdb4c016c01fac04d69bbd40ee991275ad42bdb2ea1430ec5d333da",
        "size_bytes": 13785
      },
      "changed": true,
      "path": "research\\science_program_2026_05\\06_outcome_testing\\nofill_historical_source_expansion_builder_local_tick_shadow_packet\\verify_nofill_historical_source_expansion_builder_local_tick_shadow_packet_2026_05_10.py",
      "reason": "Refresh strict parser/verifier code hash binding to current committed target file.",
      "role": "parser_or_verifier:verifier"
    }
  ],
  "target_files_changed_or_refreshed": [
    "research\\science_program_2026_05\\06_outcome_testing\\nofill_historical_source_expansion_builder_local_tick_shadow_packet\\NOFILL_HIST_SOURCE_EXPANSION_SOURCE_BOUND_CANDIDATE_PACKET_2026-05-10.jsonl",
    "research\\science_program_2026_05\\06_outcome_testing\\nofill_historical_source_expansion_builder_local_tick_shadow_packet\\NOFILL_HIST_SOURCE_EXPANSION_CANDIDATE_PACKET_MANIFEST_2026-05-10.json",
    "research\\science_program_2026_05\\06_outcome_testing\\nofill_historical_source_expansion_builder_local_tick_shadow_packet\\NOFILL_HIST_SOURCE_EXPANSION_CANDIDATE_PACKET_MANIFEST_2026-05-10.md",
    "research\\science_program_2026_05\\06_outcome_testing\\nofill_historical_source_expansion_builder_local_tick_shadow_packet\\NOFILL_HIST_SOURCE_EXPANSION_SOURCE_HASH_MANIFEST_2026-05-10.json",
    "research\\science_program_2026_05\\06_outcome_testing\\nofill_historical_source_expansion_builder_local_tick_shadow_packet\\NOFILL_HIST_SOURCE_EXPANSION_SOURCE_HASH_MANIFEST_2026-05-10.md",
    "research\\science_program_2026_05\\06_outcome_testing\\nofill_historical_source_expansion_builder_local_tick_shadow_packet\\NOFILL_HIST_SOURCE_EXPANSION_PARSER_ASOF_MANIFEST_2026-05-10.json",
    "research\\science_program_2026_05\\06_outcome_testing\\nofill_historical_source_expansion_builder_local_tick_shadow_packet\\NOFILL_HIST_SOURCE_EXPANSION_PARSER_ASOF_MANIFEST_2026-05-10.md",
    "research\\science_program_2026_05\\06_outcome_testing\\nofill_historical_source_expansion_builder_local_tick_shadow_packet\\NOFILL_HIST_SOURCE_EXPANSION_VERIFICATION_RESULT_2026-05-10.json",
    "research\\science_program_2026_05\\06_outcome_testing\\nofill_historical_source_expansion_builder_local_tick_shadow_packet\\NOFILL_HIST_SOURCE_EXPANSION_COMPLETION_AUDIT_2026-05-10.json",
    "research\\science_program_2026_05\\06_outcome_testing\\nofill_historical_source_expansion_builder_local_tick_shadow_packet\\NOFILL_HIST_SOURCE_EXPANSION_COMPLETION_AUDIT_2026-05-10.md"
  ],
  "target_verifier_refresh_note": "Target verifier rerun refreshes target verification result and completion audit artifacts.",
  "terminal_decision": "REPAIR_REBUILD_READY_FOR_G12_REAUDIT",
  "validation_safe": false
}
```
