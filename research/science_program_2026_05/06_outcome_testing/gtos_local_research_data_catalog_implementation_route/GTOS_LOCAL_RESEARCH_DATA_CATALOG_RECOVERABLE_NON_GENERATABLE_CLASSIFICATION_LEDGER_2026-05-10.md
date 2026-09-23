# Recoverable Non Generatable Classification Ledger

Route: `GTOS_LOCAL_RESEARCH_DATA_CATALOG_IMPLEMENTATION_ROUTE`
Terminal decision: `ACCEPT_AS_LOCAL_RESEARCH_DATA_CATALOG_TOOLING`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Summary

```json
{
  "artifact_family": "recoverable_vs_non_generatable_classification_ledger",
  "changes_live_trading_behavior": false,
  "classification_rows": [
    {
      "can_catalog_recover": true,
      "can_price_backfill": false,
      "class": "recoverable_market_data",
      "examples": [
        "ticks",
        "bars",
        "quotes",
        "spreads",
        "Sierra cache",
        "vendor cache"
      ],
      "route": "local_catalog_search_then_read_only_extraction_or_owner_export"
    },
    {
      "can_catalog_recover": true,
      "can_price_backfill": false,
      "class": "recoverable_by_source_contract",
      "examples": [
        "public source cache",
        "vendor cache",
        "Sierra export"
      ],
      "route": "pre_call_or_source_contract_manifest_before_network_vendor_api_action"
    },
    {
      "can_catalog_recover": false,
      "can_price_backfill": false,
      "class": "non_generatable_historical_gtos_source_state",
      "examples": [
        "pending intent id",
        "pending lifecycle group",
        "write-clock event",
        "source-safe order observability",
        "logger-emitted final lifecycle state"
      ],
      "route": "existing_source_safe_logs_or_forward_capture_requirement_only"
    },
    {
      "can_catalog_recover": false,
      "can_price_backfill": false,
      "class": "forbidden_evidence_class",
      "examples": [
        "broker account history",
        "broker actual R",
        "live order state",
        "credential source"
      ],
      "route": "reject_or_split_to_owner_approved_prompt"
    }
  ],
  "credentials_touched": false,
  "generated_at_utc": "2026-05-10T09:31:31Z",
  "live_effect": false,
  "missing_window_counts": {
    "non_generatable_historical_gtos_source_state": 20,
    "recoverable_market_data": 22,
    "recovered_local_market_data": 0
  },
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
  "price_movement_backfill_rule": "Price movement cannot backfill historical GTOS source-state truth.",
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "route_id": "GTOS_LOCAL_RESEARCH_DATA_CATALOG_IMPLEMENTATION_ROUTE",
  "schema_version": "gtos_local_research_data_catalog_implementation_route_v1",
  "terminal_decision": "ACCEPT_AS_LOCAL_RESEARCH_DATA_CATALOG_TOOLING",
  "validation_safe": false
}
```
