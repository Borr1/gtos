# G0 NOFILL Historical Source Expansion Duplicate Denominator Contamination Review

- `NO_PROMOTION_VERDICT`
- `validation_safe=false`
- `outcome_review_opened=false`
- `live_effect=false`

## Summary

Duplicate denominators remain 2/2/2 and contaminated or embargoed rows remain out of clean denominators.

## Machine Payload

```json
{
  "admitted_overlap_counts": {
    "contaminated_or_embargo_date": 0,
    "duplicate_group_id": 0,
    "nofill_duplicate_key": 0,
    "packet_row_id": 0,
    "source_inventory_id": 0,
    "source_row_id": 0
  },
  "admitted_source_dates": [
    "2026-05-08"
  ],
  "artifact_family": "duplicate_denominator_contamination_embargo_review",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "duplicate_denominators": "2/2/2",
  "embargo_policy": "Strict one-calendar-day purge around parent contaminated source dates before row admission.",
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
  "parent_contaminated_source_dates": [
    "2026-04-17",
    "2026-04-20",
    "2026-04-30",
    "2026-05-01",
    "2026-05-03",
    "2026-05-04",
    "2026-05-05",
    "2026-05-06"
  ],
  "primary_duplicate_denominator_unique_count": 2,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "reject_policy": "Rejects never add to or subtract from accepted denominators; they remain exclusion proof only.",
  "route_id": "G0_NOFILL_HISTORICAL_SOURCE_EXPANSION_PACKET_SYNTHESIS_CONTROL_REVIEW",
  "row_level_count": 2,
  "schema_version": "g0_nofill_historical_source_expansion_packet_synthesis_control_review_v1",
  "secondary_duplicate_denominator_unique_count": 2,
  "summary": "Duplicate denominators remain 2/2/2 and contaminated or embargoed rows remain out of clean denominators.",
  "validation_safe": false
}
```
