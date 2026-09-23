# Contamination Purge Embargo Audit

Route: `G12_NOFILL_HISTORICAL_SOURCE_EXPANSION_PACKET_AUDIT`
Target route: `NOFILL_HISTORICAL_SOURCE_EXPANSION_BUILDER_LOCAL_TICK_SHADOW_PACKET`
Promotion posture: `NO_PROMOTION_VERDICT`
Safe flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

## Summary

```json
{
  "admitted_checks": [
    {
      "global_one_day_embargo_hits": [],
      "packet_row_id": "NOFILL-HIST-SRCEXP-ROW-0001",
      "same_symbol_source_lane_one_day_embargo_hits": [],
      "source_date": "2026-05-08",
      "source_date_contaminated": false,
      "source_lane": "LOCAL_TICK_SHADOW_PENDING_LIMIT_LIFECYCLE_AUDIT",
      "symbol": "NAS100"
    },
    {
      "global_one_day_embargo_hits": [],
      "packet_row_id": "NOFILL-HIST-SRCEXP-ROW-0002",
      "same_symbol_source_lane_one_day_embargo_hits": [],
      "source_date": "2026-05-08",
      "source_date_contaminated": false,
      "source_lane": "LOCAL_TICK_SHADOW_PENDING_LIMIT_LIFECYCLE_AUDIT",
      "symbol": "US30_cash"
    }
  ],
  "admitted_row_count": 2,
  "artifact_family": "contamination_purge_embargo_audit",
  "audit_passed": true,
  "changes_live_trading_behavior": false,
  "checks": {
    "admitted_overlap_counts_zero": true,
    "admitted_source_dates_only_may8": true,
    "no_admitted_global_embargo_hits": true,
    "no_admitted_same_symbol_source_lane_embargo_hits": true,
    "parent_contaminated_dates_match_expected": true
  },
  "credentials_touched": false,
  "generated_at_utc": "2026-05-10T05:28:55Z",
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
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "target_admitted_overlap_counts": {
    "contaminated_or_embargo_date": 0,
    "duplicate_group_id": 0,
    "nofill_duplicate_key": 0,
    "packet_row_id": 0,
    "source_inventory_id": 0,
    "source_row_id": 0
  },
  "validation_safe": false
}
```
