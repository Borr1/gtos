# Hardening Coverage Ledger

- Route: `FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR`
- Evidence class: `FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR_ONLY`
- Promotion verdict: `NO_PROMOTION_VERDICT`
- validation_safe: `False`
- outcome_review_opened: `False`
- live_effect: `False`

## Summary

```json
{
  "all_hardening_controls_covered": true,
  "control_count": 8
}
```
## Payload

```json
{
  "all_hardening_controls_covered": true,
  "artifact_family": "hardening_coverage_ledger",
  "changes_live_trading_behavior": false,
  "controls": [
    {
      "control": "append_mutable_full_file_not_accepted",
      "coverage": "full-file hash is reference-only; segment hash is accepted evidence",
      "status": "COVERED"
    },
    {
      "control": "segment_boundaries_frozen",
      "coverage": "record and byte start/end boundaries emitted for each source",
      "status": "COVERED"
    },
    {
      "control": "immediate_rehash",
      "coverage": "builder rehashes each frozen byte range immediately",
      "status": "COVERED"
    },
    {
      "control": "future_rehash_verifier",
      "coverage": "verifier rehashes each frozen byte range from the manifest",
      "status": "COVERED"
    },
    {
      "control": "discovery_exclusion_preserved",
      "coverage": "365 selected source rows/hashes remain excluded and disjoint from repaired segment hashes",
      "status": "COVERED"
    },
    {
      "control": "eligible_hard_floor",
      "coverage": "first segment record is required to be >= eligible_segment_start_utc",
      "status": "COVERED"
    },
    {
      "control": "raw_blob_commit_prevention",
      "coverage": "no raw SCID/snapshot bytes are written; committed manifests only",
      "status": "COVERED"
    },
    {
      "control": "future_validation_gate",
      "coverage": "SCID-to-asof-bar derivation and separate validation prompt remain required",
      "status": "COVERED"
    }
  ],
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
  "route_id": "FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR",
  "schema_version": "fpb_sealed_source_pool_immutable_scid_hash_freeze_repair_v1",
  "summary": {
    "all_hardening_controls_covered": true,
    "control_count": 8
  },
  "validation_safe": false
}
```
