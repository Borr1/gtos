# NOFILL Read-Only Tick Recovery No-Leak Audit

Route: `NOFILL_READONLY_TICK_RECOVERY_EXPORT_SOURCE_CONTROL_ROUTE`
Terminal decision: `ACCEPT_WITH_EXACT_REMAINING_EXPORT_OR_ACCESS_REQUESTS`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Summary

## Machine Payload

```json
{
  "account_order_history_deal_position_api_used_any": false,
  "artifact_family": "noleak_audit",
  "audit_status": "PASS",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "extraction_runtime_status": "MT5_INITIALIZED_MARKET_DATA_ONLY",
  "forbidden_api_calls_covered": true,
  "forbidden_api_calls_omitted": [
    "account_info",
    "history_deals_get",
    "history_orders_get",
    "orders_get",
    "positions_get"
  ],
  "forbidden_text_hits": [],
  "generated_at_utc": "2026-05-10T09:46:58Z",
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
  "route_id": "NOFILL_READONLY_TICK_RECOVERY_EXPORT_SOURCE_CONTROL_ROUTE",
  "schema_version": "nofill_readonly_tick_recovery_export_source_control_route_v1",
  "source_state_boundary_preserved": true,
  "terminal_decision": "ACCEPT_WITH_EXACT_REMAINING_EXPORT_OR_ACCESS_REQUESTS",
  "validation_safe": false
}
```
