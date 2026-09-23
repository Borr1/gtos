# 55 Field Binding Audit

Route: `G12_NOFILL_HISTORICAL_SOURCE_EXPANSION_PACKET_AUDIT`
Target route: `NOFILL_HISTORICAL_SOURCE_EXPANSION_BUILDER_LOCAL_TICK_SHADOW_PACKET`
Promotion posture: `NO_PROMOTION_VERDICT`
Safe flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

## Summary

```json
{
  "artifact_family": "field_55_binding_audit",
  "audit_passed": true,
  "binding_class_counts": {
    "FORBIDDEN_REDACTED_STATUS_ONLY": 7,
    "FUTURE_LOGGER_BOUND_REQUIRED_FOR_FULL_COVERAGE": 20,
    "SCHEMA_ONLY_CONTROL": 11,
    "SOURCE_BOUND_HISTORICAL_OR_FAIL_CLOSED": 17
  },
  "binding_rows_per_packet_row": {
    "NOFILL-HIST-SRCEXP-ROW-0001": 55,
    "NOFILL-HIST-SRCEXP-ROW-0002": 55
  },
  "changes_live_trading_behavior": false,
  "checks": {
    "all_binding_values_present": true,
    "binding_class_counts_match": true,
    "binding_row_count_is_110": true,
    "each_packet_row_has_55_binding_rows": true,
    "packet_rows_missing_no_runtime_fields": true,
    "runtime_field_count_is_55": true
  },
  "credentials_touched": false,
  "generated_at_utc": "2026-05-10T05:28:55Z",
  "live_effect": false,
  "missing_or_forbidden_by_row": [],
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
  "runtime_field_count": 55,
  "target_binding_row_count": 110,
  "validation_safe": false
}
```
