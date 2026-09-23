# Duplicate Purge Embargo Split Reaudit

Route: `G12_NOFILL_HISTORICAL_SEALED_VALIDATION_PARTITION_SOURCE_BINDING_AUDIT`
Target route: `NOFILL_HISTORICAL_SEALED_VALIDATION_PARTITION_AND_SOURCE_BINDING`
Promotion posture: `NO_PROMOTION_VERDICT`
Safe flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

## Summary

```json
{
  "accepted_row_count_recomputed": 225,
  "artifact_family": "duplicate_purge_embargo_split_reaudit",
  "audit_passed": true,
  "changes_live_trading_behavior": false,
  "checks": {
    "accepted_row_count_matches_policy": true,
    "contaminated_dates_match_rows": true,
    "embargo_rules_present": true,
    "primary_duplicate_key_count_matches_policy": true,
    "purge_rules_present": true,
    "regime_split_is_blocked_until_asof_binding": true,
    "secondary_duplicate_group_count_matches_policy": true,
    "session_counts_match_rows": true,
    "side_counts_match_rows": true,
    "symbol_counts_match_rows": true
  },
  "contaminated_source_dates_recomputed": [
    "2026-04-17",
    "2026-04-20",
    "2026-04-30",
    "2026-05-01",
    "2026-05-03",
    "2026-05-04",
    "2026-05-05",
    "2026-05-06"
  ],
  "credentials_touched": false,
  "effective_n_control_conclusion": "Future validation must use duplicate-key as primary denominator, duplicate-group as concentration denominator, and one-day same-symbol embargo around contaminated source dates before outcome opening.",
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
  "primary_duplicate_key_unique_count_recomputed": 182,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "secondary_duplicate_group_unique_count_recomputed": 139,
  "session_counts_recomputed": {
    "london": 90,
    "ny": 154,
    "tokyo": 54
  },
  "side_counts_recomputed": {
    "LONG": 107,
    "SHORT": 191
  },
  "symbol_counts_recomputed": {
    "GBPJPY": 18,
    "NAS100": 78,
    "US30_cash": 3,
    "USDJPY": 72,
    "XAGUSD": 106,
    "XAUUSD": 21
  },
  "symbol_session_counts_recomputed": {
    "GBPJPY|tokyo": 18,
    "NAS100|london": 24,
    "NAS100|ny": 54,
    "US30_cash|london": 3,
    "USDJPY|london": 6,
    "USDJPY|ny": 30,
    "USDJPY|tokyo": 36,
    "XAGUSD|london": 48,
    "XAGUSD|ny": 58,
    "XAUUSD|london": 9,
    "XAUUSD|ny": 12
  },
  "target_route_id": "NOFILL_HISTORICAL_SEALED_VALIDATION_PARTITION_AND_SOURCE_BINDING",
  "validation_safe": false
}
```
