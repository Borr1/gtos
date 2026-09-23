# CNR Source Field Duplicate Denominator Report - 2026-05-07

Promotion verdict: `NO_PROMOTION_VERDICT`  
Validation safe: `false`  
Outcome review opened: `false`  
Live effect: `false`

```json
{
  "account_history_accessed": false,
  "api_calls": 0,
  "artifact_family": "CNR_SOURCE_FIELD_DUPLICATE_DENOMINATOR_REPORT",
  "blocked_packet_outcome_source_read": false,
  "broker_actual_r_accessed": false,
  "by_packet": {
    "OTG0-PKT-060": {
      "countable_rows": 400,
      "rows": 1600,
      "unique_denominator_keys": 400,
      "unique_primary_duplicate_groups": 20
    },
    "OTG0-PKT-061": {
      "countable_rows": 160,
      "rows": 1020,
      "unique_denominator_keys": 160,
      "unique_primary_duplicate_groups": 8
    },
    "OTG0-PKT-062": {
      "countable_rows": 380,
      "rows": 1720,
      "unique_denominator_keys": 380,
      "unique_primary_duplicate_groups": 19
    },
    "OTG0-PKT-063": {
      "countable_rows": 420,
      "rows": 1720,
      "unique_denominator_keys": 420,
      "unique_primary_duplicate_groups": 21
    },
    "OTG0-PKT-066": {
      "countable_rows": 120,
      "rows": 140,
      "unique_denominator_keys": 120,
      "unique_primary_duplicate_groups": 6
    }
  },
  "canary_calls": 0,
  "databento_calls": 0,
  "duplicate_context_rows": 4720,
  "duplicate_policy": "one countable row per duplicate_group_id per packet/timing_model_family/target_model_family",
  "generated_at_utc": "2026-05-07T16:38:18Z",
  "live_effect": false,
  "live_order_state_accessed": false,
  "live_trade_results_accessed": false,
  "mt5_order_calls": 0,
  "order_calls": 0,
  "outcome_review_opened": false,
  "paid_data_calls": 0,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "stability_status": "PASS_DUPLICATE_DENOMINATOR_STABLE",
  "total_rows": 6200,
  "unique_denominator_keys": 1480,
  "validation_safe": false
}
```
