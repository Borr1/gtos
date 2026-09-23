# G0 NOFILL Historical Source Expansion Evidence Chain Reconciliation

- `NO_PROMOTION_VERDICT`
- `validation_safe=false`
- `outcome_review_opened=false`
- `live_effect=false`

## Summary

Accepted packet chain, repair chain, counts, hashes, and closed gates reconciled.

## Machine Payload

```json
{
  "accepted_counts": {
    "admitted_packet_row_count": 2,
    "blocked_candidate_count": 37,
    "duplicate_denominators": "2/2/2",
    "packet_rows": 2,
    "rejected_candidate_count": 9,
    "status_counts": {
      "ADMITTED_SOURCE_PACKET_ROW": 2,
      "BLOCKED_WITH_EXACT_SOURCE_REQUIREMENT": 37,
      "REJECTED_ONE_DAY_EMBARGO_OVERLAP": 9
    }
  },
  "artifact_family": "evidence_chain_reconciliation",
  "changes_live_trading_behavior": false,
  "closed_validation_gates": {
    "g12_future_route_scoring_remains_closed": true,
    "g12_future_route_validation_execution_remains_closed": true,
    "g12_noleak_audit_passed": true,
    "g12_repair_terminal_decision": "ACCEPT_REPAIRED_SOURCE_CONTROL_PACKET_FOR_NEXT_EVIDENCE_CLASS_PROMPT"
  },
  "credentials_touched": false,
  "generated_at_utc": "2026-05-10T07:53:15Z",
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
  "packet_hash": {
    "audit_passed": true,
    "expected_repaired_packet_sha256": "5f3d2713a17393590fa85984a2c761403faa3d40c6ad018bfa1b32d3ddaf8341",
    "g12_packet_sha256_manifest": "5f3d2713a17393590fa85984a2c761403faa3d40c6ad018bfa1b32d3ddaf8341",
    "g12_packet_sha256_recomputed": "5f3d2713a17393590fa85984a2c761403faa3d40c6ad018bfa1b32d3ddaf8341"
  },
  "parser_hashes": {
    "g12_repair_parser_audit": {
      "audit_passed": true,
      "packet_parser_code_hashes": [
        "0e637cddb98577de2951759c43288fafb251d70fbcb2457e9a029b1dab59ad3b"
      ],
      "parser_asof_hash": "0e637cddb98577de2951759c43288fafb251d70fbcb2457e9a029b1dab59ad3b"
    },
    "packet_parser_code_hashes": [
      "0e637cddb98577de2951759c43288fafb251d70fbcb2457e9a029b1dab59ad3b"
    ],
    "parser_manifest_path": "research/science_program_2026_05/06_outcome_testing/nofill_historical_source_expansion_builder_local_tick_shadow_packet/NOFILL_HIST_SOURCE_EXPANSION_PARSER_ASOF_MANIFEST_2026-05-10.json",
    "parser_manifest_sha256": "81b9888b56b24d266d9322c6e9d3e2983c297f77f7be6d58f8cfdd9f2d3df606"
  },
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "route_id": "G0_NOFILL_HISTORICAL_SOURCE_EXPANSION_PACKET_SYNTHESIS_CONTROL_REVIEW",
  "schema_version": "g0_nofill_historical_source_expansion_packet_synthesis_control_review_v1",
  "source_hashes": {
    "admitted_row_source_files_sha256": [
      {
        "candidate_id": "NAS100_2026-05-08T15:45:00+00:00",
        "source_files_sha256": {
          "candidate_ltf_path_order": "0ed23ea479b2a98a98021a67c838c7b27f9c0a2ee280193cefa25d8a01ed208f",
          "candidate_registry_audit": "1183d41f8af0914d1d398c1bda2d1cf6b9147f88c0c24e10a178a9697d78b5b0",
          "pending_limit_lifecycle": "f0c45eb94d70b94e9e4eb6aebcb4943f3864a7f1cdb37c6003631337e8b9ad49",
          "pending_limit_lifecycle_audit": "a639889d645a232f032fe40adca6f114b48b3a23df9e487fbb7901c456ce6c13",
          "tick_parquet": "5ba5af2f5b1a9561397ecd0adf397fd4eeba942fe9c218f066c74288436b9e31"
        }
      },
      {
        "candidate_id": "US30_cash_2026-05-08T13:45:00+00:00",
        "source_files_sha256": {
          "candidate_ltf_path_order": "0ed23ea479b2a98a98021a67c838c7b27f9c0a2ee280193cefa25d8a01ed208f",
          "candidate_registry_audit": "1183d41f8af0914d1d398c1bda2d1cf6b9147f88c0c24e10a178a9697d78b5b0",
          "pending_limit_lifecycle": "f0c45eb94d70b94e9e4eb6aebcb4943f3864a7f1cdb37c6003631337e8b9ad49",
          "pending_limit_lifecycle_audit": "a639889d645a232f032fe40adca6f114b48b3a23df9e487fbb7901c456ce6c13",
          "tick_parquet": "bfed917d099ba990458319e4c607e405e3a53de458be13d9dc893be011fc4cd6"
        }
      }
    ],
    "packet_manifest_path": "research/science_program_2026_05/06_outcome_testing/nofill_historical_source_expansion_builder_local_tick_shadow_packet/NOFILL_HIST_SOURCE_EXPANSION_CANDIDATE_PACKET_MANIFEST_2026-05-10.json",
    "packet_manifest_sha256": "de2642202ecaea7376ff6a44fa024d4e9b0216e3c280b3ab2901aeb24797cefb",
    "source_hash_manifest_path": "research/science_program_2026_05/06_outcome_testing/nofill_historical_source_expansion_builder_local_tick_shadow_packet/NOFILL_HIST_SOURCE_EXPANSION_SOURCE_HASH_MANIFEST_2026-05-10.json",
    "source_hash_manifest_sha256": "812d706d253a62962e0761ab96ae514163cbaf14a2c1f00f6d24fe34168b5f17"
  },
  "summary": "Accepted packet chain, repair chain, counts, hashes, and closed gates reconciled.",
  "validation_safe": false,
  "what_repaired_packet_did_not_prove": [
    "No validation lane is open.",
    "No result, cost, R, win-rate, expectancy, DSR, PBO, broker outcome, or promotion claim is proven.",
    "The two admitted rows do not clear a sample floor.",
    "Historical missing source-state truth for the 37 blockers is not recoverable from price movement or catalog presence."
  ],
  "what_repaired_packet_proved": [
    "Two source-bound source/control rows exist for NAS100 2026-05-08T15:45:00Z and US30_cash 2026-05-08T13:45:00Z.",
    "Those two rows bind 55 packet fields and 20 future logger field statuses.",
    "The repaired packet hash, parser hashes, and semantic row counts survived independent G12 repair reaudit.",
    "Forbidden result/cost/live surfaces remained closed in the accepted G12 repair reaudit."
  ]
}
```
