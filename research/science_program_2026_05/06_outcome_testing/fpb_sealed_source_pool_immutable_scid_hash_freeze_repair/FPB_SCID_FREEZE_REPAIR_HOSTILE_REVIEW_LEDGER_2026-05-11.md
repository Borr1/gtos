# Hostile Source Review Ledger

- Route: `FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR`
- Evidence class: `FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR_ONLY`
- Promotion verdict: `NO_PROMOTION_VERDICT`
- validation_safe: `False`
- outcome_review_opened: `False`
- live_effect: `False`

## Summary

```json
{
  "all_attacks_preempted_or_blocked": true,
  "attack_count": 5
}
```
## Payload

```json
{
  "all_attacks_preempted_or_blocked": true,
  "artifact_family": "hostile_source_review_ledger",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "evidence_class": "FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR_ONLY",
  "generated_at_utc": "2026-05-11T10:22:32Z",
  "hostile_reviews": [
    {
      "attack": "Full-file hashes could drift after append and be mistaken as immutable.",
      "preemption": "accepted evidence is segment_records_sha256 with byte_end_exclusive frozen; full-file hash is reference-only",
      "status": "PREEMPTED"
    },
    {
      "attack": "Pre-eligible records could leak into the segment.",
      "preemption": "start index is lower_bound(timestamp >= eligible_segment_start_utc_hard_floor)",
      "status": "PREEMPTED"
    },
    {
      "attack": "Discovery-selected source could re-enter under a different hash family.",
      "preemption": "365 selected source hashes remain excluded; repaired segment hashes are checked disjoint",
      "status": "PREEMPTED"
    },
    {
      "attack": "Segment hashes could be unrehashable in the next audit.",
      "preemption": "manifest records path, byte range, record indexes, parser hash, and verifier rehashes the same range",
      "status": "PREEMPTED"
    },
    {
      "attack": "Source repair could silently become validation.",
      "preemption": "SCID-to-asof-bar and separate validation-execution gates remain explicit; no result fields are emitted",
      "status": "PREEMPTED"
    }
  ],
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
  "segment_rows_reviewed": 9,
  "summary": {
    "all_attacks_preempted_or_blocked": true,
    "attack_count": 5
  },
  "validation_safe": false
}
```
