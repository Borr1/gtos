# Searched Root Source Saturation Ledger

- Route: `FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR`
- Evidence class: `FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR_ONLY`
- Promotion verdict: `NO_PROMOTION_VERDICT`
- validation_safe: `False`
- outcome_review_opened: `False`
- live_effect: `False`

## Summary

```json
{
  "all_required_sources_seen": true,
  "searched_root_count": 4
}
```
## Payload

```json
{
  "all_required_sources_seen": true,
  "artifact_family": "searched_root_source_saturation_ledger",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "evidence_class": "FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR_ONLY",
  "generated_at_utc": "2026-05-11T10:22:32Z",
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
  "required_source_names": [
    "6BM26-CME.scid",
    "6EM26-CME.scid",
    "6JM26-CME.scid",
    "GCM26-COMEX.scid",
    "MGCM26-COMEX.scid",
    "MYMM26-CBOT.scid",
    "NQM26-CME.scid",
    "SIM26-COMEX.scid",
    "YMM26-CBOT.scid"
  ],
  "resolved_source_names": [
    "6BM26-CME.scid",
    "6EM26-CME.scid",
    "6JM26-CME.scid",
    "GCM26-COMEX.scid",
    "MGCM26-COMEX.scid",
    "MYMM26-CBOT.scid",
    "NQM26-CME.scid",
    "SIM26-COMEX.scid",
    "YMM26-CBOT.scid"
  ],
  "route_id": "FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR",
  "schema_version": "fpb_sealed_source_pool_immutable_scid_hash_freeze_repair_v1",
  "searched_roots": [
    {
      "finding": "exact 9 append-mutable SCID blockers",
      "path": "research/science_program_2026_05/06_outcome_testing/g12_fpb_sealed_source_pool_materialization_audit/G12_FPB_SEALED_SOURCE_POOL_MATERIALIZATION_AUDIT_REPAIR_BLOCKER_LEDGER_2026-05-11.json",
      "root_id": "g12_repair_blocker_ledger"
    },
    {
      "finding": "accepted 9 native SCID sealed-source candidates and hard floors",
      "path": "research/science_program_2026_05/06_outcome_testing/fpb_source_expansion_and_sealed_pool_materialization/FPB_SOURCE_EXPANSION_NATIVE_SCID_SEALED_POOL_CANDIDATE_LEDGER_2026-05-11.json",
      "root_id": "source_expansion_native_scid_ledger"
    },
    {
      "finding": "read-only direct source for the 9 required files",
      "path": "C:/SierraChart/Data",
      "root_id": "local_sierra_native_data"
    },
    {
      "finding": "discovery-source exclusion and four-baseline preservation inputs",
      "path": "research/science_program_2026_05/06_outcome_testing/g0_fpb_sealed_partition_and_adversarial_baseline_packet",
      "root_id": "g0_partition_and_baseline_packet"
    }
  ],
  "source_saturation_decision": "ALL_REQUIRED_G12_REPAIR_BLOCKERS_PURSUED",
  "summary": {
    "all_required_sources_seen": true,
    "searched_root_count": 4
  },
  "validation_safe": false
}
```
