# Negative Failure Anatomy Ledger

- Route: `FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR`
- Evidence class: `FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR_ONLY`
- Promotion verdict: `NO_PROMOTION_VERDICT`
- validation_safe: `False`
- outcome_review_opened: `False`
- live_effect: `False`

## Summary

```json
{
  "root_cause": "append-mutable full file evidence"
}
```
## Payload

```json
{
  "artifact_family": "negative_failure_anatomy_ledger",
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
  "prior_failure": {
    "failed_fields": [
      "sha256",
      "size_bytes",
      "record_count",
      "coverage_end_utc"
    ],
    "failure": "G12 rejected the source pool because full native SCID files kept appending after materialization.",
    "root_cause": "mutable EOF on live Sierra native files, not market-result evidence"
  },
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "repair": {
    "method": "bounded eligible segment hashes",
    "what_it_does_not_repair": [
      "SCID-to-asof-bar derivation contract",
      "candidate generation",
      "validation execution",
      "promotion or live behavior"
    ],
    "why_it_repairs": "later appended records are beyond the frozen byte_end_exclusive and cannot alter the segment hash"
  },
  "route_id": "FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR",
  "schema_version": "fpb_sealed_source_pool_immutable_scid_hash_freeze_repair_v1",
  "summary": {
    "root_cause": "append-mutable full file evidence"
  },
  "validation_safe": false
}
```
