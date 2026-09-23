# NOFILL Historical Source Expansion Contamination Purge Ledger

Route: `NOFILL_HISTORICAL_SOURCE_EXPANSION_BUILDER_LOCAL_TICK_SHADOW_PACKET`
Terminal decision: `ACCEPT_SOURCE_HASHED_INPUT_PACKET_READY_FOR_G12_SOURCE_CONTROL_AUDIT`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Summary

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
  "admitted_packet_row_count": 2,
  "admitted_source_dates": [
    "2026-05-08"
  ],
  "artifact_family": "contamination_purge_ledger",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "embargo_policy": "Strict one-calendar-day purge around parent contaminated source dates before row admission.",
  "generated_at_utc": "2026-05-10T05:02:02Z",
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
  "parent_contaminated_row_count": 298,
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
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "purge_rules": [
    "Purge packet row ID, source row ID, source inventory ID, nofill duplicate key, and duplicate group overlap.",
    "Globally contaminated source dates from accepted G12: ['2026-04-17', '2026-04-20', '2026-04-30', '2026-05-01', '2026-05-03', '2026-05-04', '2026-05-05', '2026-05-06'].",
    "Apply at least one-day same-symbol/source-lane embargo around contaminated source dates before source expansion.",
    "G12 may tighten the embargo if source-lane timestamps show same-event leakage."
  ],
  "route_id": "NOFILL_HISTORICAL_SOURCE_EXPANSION_BUILDER_LOCAL_TICK_SHADOW_PACKET",
  "schema_version": "nofill_historical_source_expansion_builder_local_tick_shadow_packet_v1",
  "validation_safe": false
}
```
