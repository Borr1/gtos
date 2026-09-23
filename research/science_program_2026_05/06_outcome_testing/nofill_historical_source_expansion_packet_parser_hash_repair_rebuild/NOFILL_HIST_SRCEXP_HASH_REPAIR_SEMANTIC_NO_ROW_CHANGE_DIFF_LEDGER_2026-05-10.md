# NOFILL Source Expansion Parser Hash Repair Semantic No-Row-Change Diff Ledger

Route: `NOFILL_HISTORICAL_SOURCE_EXPANSION_PACKET_PARSER_HASH_REPAIR_REBUILD`
Terminal decision: `REPAIR_REBUILD_READY_FOR_G12_REAUDIT`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Summary

```json
{
  "admitted_blocked_rejected_counts_required": {
    "admitted_packet_row_count": 2,
    "blocked_candidate_count": 37,
    "rejected_candidate_count": 9
  },
  "after_hash_fields": [
    {
      "packet_row_id": "NOFILL-HIST-SRCEXP-ROW-0001",
      "parser_code_hash": "0e637cddb98577de2951759c43288fafb251d70fbcb2457e9a029b1dab59ad3b",
      "source_artifact_hash": "53a5b700c2044a9c424259e3aa44f7b350837a1efd9ccc7b2ad16b5eecc74358"
    },
    {
      "packet_row_id": "NOFILL-HIST-SRCEXP-ROW-0002",
      "parser_code_hash": "0e637cddb98577de2951759c43288fafb251d70fbcb2457e9a029b1dab59ad3b",
      "source_artifact_hash": "dd55c753d9c544558741795303ccdb5a54a0e1cda8177a22d61f952ef8d0a698"
    }
  ],
  "after_packet_sha256": "5f3d2713a17393590fa85984a2c761403faa3d40c6ad018bfa1b32d3ddaf8341",
  "after_row_identities": [
    {
      "candidate_id": "NAS100_2026-05-08T15:45:00+00:00",
      "decision_time_utc": "2026-05-08T15:45:00+00:00",
      "packet_row_id": "NOFILL-HIST-SRCEXP-ROW-0001",
      "symbol": "NAS100"
    },
    {
      "candidate_id": "US30_cash_2026-05-08T13:45:00+00:00",
      "decision_time_utc": "2026-05-08T13:45:00+00:00",
      "packet_row_id": "NOFILL-HIST-SRCEXP-ROW-0002",
      "symbol": "US30_cash"
    }
  ],
  "artifact_family": "semantic_no_row_change_diff_ledger",
  "before_hash_fields": [
    {
      "packet_row_id": "NOFILL-HIST-SRCEXP-ROW-0001",
      "parser_code_hash": "3bd0edb2d183283094f40d58e5889ddd116d3f8b3677853c2e2d75ea330df0d4",
      "source_artifact_hash": "3bf7f8cdfbbb7cc065b00480116624b2a1acf7c37dd3f4e8bbdf741687a15c0b"
    },
    {
      "packet_row_id": "NOFILL-HIST-SRCEXP-ROW-0002",
      "parser_code_hash": "3bd0edb2d183283094f40d58e5889ddd116d3f8b3677853c2e2d75ea330df0d4",
      "source_artifact_hash": "425d7ff263decec8f4205f2abb5c7a73d394dc1484a7bb7c544591dd894924bb"
    }
  ],
  "before_packet_sha256": "2c8dd8ff4b3e660bea7978a22a84e309ce98f3d95d9db0221fd13957481aa480",
  "before_row_identities": [
    {
      "candidate_id": "NAS100_2026-05-08T15:45:00+00:00",
      "decision_time_utc": "2026-05-08T15:45:00+00:00",
      "packet_row_id": "NOFILL-HIST-SRCEXP-ROW-0001",
      "symbol": "NAS100"
    },
    {
      "candidate_id": "US30_cash_2026-05-08T13:45:00+00:00",
      "decision_time_utc": "2026-05-08T13:45:00+00:00",
      "packet_row_id": "NOFILL-HIST-SRCEXP-ROW-0002",
      "symbol": "US30_cash"
    }
  ],
  "candidate_packet_manifest_after_sha256": "5f3d2713a17393590fa85984a2c761403faa3d40c6ad018bfa1b32d3ddaf8341",
  "candidate_packet_manifest_before_sha256": "2c8dd8ff4b3e660bea7978a22a84e309ce98f3d95d9db0221fd13957481aa480",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "expected_row_identities_match_after": true,
  "expected_row_identities_match_before": true,
  "generated_at_utc": "2026-05-10T05:51:30Z",
  "hash_fields_changed_only": true,
  "live_effect": false,
  "only_hash_derived_fields_changed": true,
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
  "paths_changed": [
    "research\\science_program_2026_05\\06_outcome_testing\\nofill_historical_source_expansion_builder_local_tick_shadow_packet\\NOFILL_HIST_SOURCE_EXPANSION_SOURCE_BOUND_CANDIDATE_PACKET_2026-05-10.jsonl",
    "research\\science_program_2026_05\\06_outcome_testing\\nofill_historical_source_expansion_builder_local_tick_shadow_packet\\NOFILL_HIST_SOURCE_EXPANSION_CANDIDATE_PACKET_MANIFEST_2026-05-10.json",
    "research\\science_program_2026_05\\06_outcome_testing\\nofill_historical_source_expansion_builder_local_tick_shadow_packet\\NOFILL_HIST_SOURCE_EXPANSION_CANDIDATE_PACKET_MANIFEST_2026-05-10.md"
  ],
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "route_id": "NOFILL_HISTORICAL_SOURCE_EXPANSION_PACKET_PARSER_HASH_REPAIR_REBUILD",
  "row_count_after": 2,
  "row_count_before": 2,
  "schema_version": "nofill_historical_source_expansion_packet_parser_hash_repair_rebuild_v1",
  "semantic_counts_unchanged": true,
  "semantic_guard_after": {
    "admitted_packet_row_count": 2,
    "blocked_candidate_count": 37,
    "rejected_candidate_count": 9
  },
  "semantic_guard_before": {
    "admitted_packet_row_count": 2,
    "blocked_candidate_count": 37,
    "rejected_candidate_count": 9
  },
  "semantic_rows_unchanged_excluding_hash_fields": true,
  "terminal_decision": "REPAIR_REBUILD_READY_FOR_G12_REAUDIT",
  "validation_safe": false
}
```

## Notes

- Only `parser_code_hash` and parser-derived `source_artifact_hash` changed in packet rows.
