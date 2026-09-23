# Packet Hash Manifest Reaudit

Route: `G12_NOFILL_HISTORICAL_SOURCE_EXPANSION_HASH_REPAIR_REAUDIT`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

## Summary

```json
{
  "artifact_family": "packet_hash_manifest_reaudit",
  "audit_passed": true,
  "changes_live_trading_behavior": false,
  "checks": {
    "manifest_keeps_g12_gate_closed": true,
    "packet_row_count_is_2": true,
    "packet_sha_matches_expected_repaired_sha": true,
    "packet_sha_matches_repair_packet_ledger": true,
    "packet_sha_matches_target_manifest": true
  },
  "credentials_touched": false,
  "expected_repaired_packet_sha256": "5f3d2713a17393590fa85984a2c761403faa3d40c6ad018bfa1b32d3ddaf8341",
  "generated_at_utc": "2026-05-10T06:17:01Z",
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
  "packet_row_count": 2,
  "packet_sha256_manifest": "5f3d2713a17393590fa85984a2c761403faa3d40c6ad018bfa1b32d3ddaf8341",
  "packet_sha256_recomputed": "5f3d2713a17393590fa85984a2c761403faa3d40c6ad018bfa1b32d3ddaf8341",
  "packet_sha256_repair_ledger": "5f3d2713a17393590fa85984a2c761403faa3d40c6ad018bfa1b32d3ddaf8341",
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "remaining_blockers": [],
  "target_packet_manifest_path": "research\\science_program_2026_05\\06_outcome_testing\\nofill_historical_source_expansion_builder_local_tick_shadow_packet\\NOFILL_HIST_SOURCE_EXPANSION_CANDIDATE_PACKET_MANIFEST_2026-05-10.json",
  "target_packet_path": "research\\science_program_2026_05\\06_outcome_testing\\nofill_historical_source_expansion_builder_local_tick_shadow_packet\\NOFILL_HIST_SOURCE_EXPANSION_SOURCE_BOUND_CANDIDATE_PACKET_2026-05-10.jsonl",
  "validation_safe": false
}
```
