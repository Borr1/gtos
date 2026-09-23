# Acquisition Manifest Schema

Route: `GTOS_LOCAL_RESEARCH_DATA_CATALOG_IMPLEMENTATION_ROUTE`
Terminal decision: `ACCEPT_AS_LOCAL_RESEARCH_DATA_CATALOG_TOOLING`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Summary

```json
{
  "allowed_blocker_codes": [
    "RECOVERABLE_BY_APPROVED_EXTRACTION",
    "RECOVERABLE_BY_OWNER_EXPORT",
    "RECOVERABLE_BY_SOURCE_CONTRACT",
    "NON_GENERATABLE_SOURCE_STATE",
    "FORBIDDEN_EVIDENCE_CLASS"
  ],
  "artifact_family": "acquisition_request_manifest_schema",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "execution_policy": "manifest_only_no_api_no_mt5_no_broker_account_no_paid_route_executed",
  "generated_at_utc": "2026-05-10T09:31:31Z",
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
  "required_fields": [
    "request_id",
    "source_requirement_type",
    "blocker_code",
    "symbol",
    "window_start_utc",
    "window_end_utc",
    "timeframe",
    "requested_fields",
    "approved_route",
    "cost_cap_usd",
    "approval_required",
    "owner_action_required",
    "no_leak_constraints",
    "forbidden_fields",
    "output_path",
    "hash_policy",
    "execution_status"
  ],
  "route_id": "GTOS_LOCAL_RESEARCH_DATA_CATALOG_IMPLEMENTATION_ROUTE",
  "schema_version": "gtos_local_research_data_catalog_implementation_route_v1",
  "terminal_decision": "ACCEPT_AS_LOCAL_RESEARCH_DATA_CATALOG_TOOLING",
  "validation_safe": false
}
```
