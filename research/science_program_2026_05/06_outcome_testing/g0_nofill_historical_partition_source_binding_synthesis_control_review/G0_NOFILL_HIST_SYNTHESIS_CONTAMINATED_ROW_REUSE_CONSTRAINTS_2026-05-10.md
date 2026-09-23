# Contaminated Row Reuse Constraints

Route: `G0_NOFILL_HISTORICAL_PARTITION_SOURCE_BINDING_SYNTHESIS_CONTROL_REVIEW`
Terminal decision: `ACCEPT_AS_G0_SOURCE_CONTROL_SYNTHESIS_FOR_NEXT_SEALED_SOURCE_EXPANSION`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Summary

```json
{
  "allowed_uses": [
    "source/control lineage explanation",
    "duplicate and concentration stress design",
    "exclusion-proof stress tests",
    "field binding and parser-design examples",
    "future robustness design that does not score the contaminated rows as validation"
  ],
  "artifact_family": "contaminated_row_reuse_constraints",
  "changes_live_trading_behavior": false,
  "contaminated_row_count": 298,
  "contaminated_source_dates": [
    "2026-04-17",
    "2026-04-20",
    "2026-04-30",
    "2026-05-01",
    "2026-05-03",
    "2026-05-04",
    "2026-05-05",
    "2026-05-06"
  ],
  "contamination_counts_by_terminal_family": {
    "accepted": 225,
    "reject": 65,
    "source_control": 4,
    "source_impossible": 4
  },
  "credentials_touched": false,
  "forbidden_uses": [
    "sealed historical validation denominator",
    "result/cost scoring",
    "promotion claim support",
    "sample-floor inflation",
    "source-date laundering through regenerated packet IDs",
    "broker actual-R/account-history review in this lane"
  ],
  "generated_at_utc": "2026-05-10T04:31:04Z",
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
  "primary_duplicate_key_members": 182,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "reuse_rule": "A future row must be excluded if it shares packet row ID, source row ID, source inventory ID, nofill duplicate key, duplicate group ID, source date, or one-day same-symbol/source-lane embargo overlap with this contaminated ledger unless a future G12 explicitly proves independent source generation.",
  "route_id": "G0_NOFILL_HISTORICAL_PARTITION_SOURCE_BINDING_SYNTHESIS_CONTROL_REVIEW",
  "schema_version": "g0_nofill_historical_partition_source_binding_synthesis_control_review_v1",
  "secondary_duplicate_group_members": 139,
  "validation_safe": false
}
```
