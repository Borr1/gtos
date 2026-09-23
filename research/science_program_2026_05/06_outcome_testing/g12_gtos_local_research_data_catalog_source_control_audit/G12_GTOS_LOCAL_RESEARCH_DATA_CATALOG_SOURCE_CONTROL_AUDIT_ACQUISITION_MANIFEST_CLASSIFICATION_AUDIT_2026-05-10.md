# Acquisition Manifest Classification Audit

Route: `G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT`
Terminal decision: `ACCEPT_WITH_EXACT_IMPLEMENTATION_FOLLOWUPS`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Summary

```json
{
  "artifact_family": "acquisition_manifest_classification_audit",
  "audit_passed": true,
  "changes_live_trading_behavior": false,
  "classification_classes": [
    "forbidden_evidence_class",
    "non_generatable_historical_gtos_source_state",
    "recoverable_by_source_contract",
    "recoverable_market_data"
  ],
  "credentials_touched": false,
  "forbidden_request_route_count": 0,
  "forbidden_request_route_ids": [],
  "generated_at_utc": "2026-05-10T07:24:26Z",
  "live_effect": false,
  "non_generatable_can_price_backfill": false,
  "non_manifest_execution_count": 0,
  "non_manifest_execution_request_ids": [],
  "nonzero_cost_cap_count": 0,
  "nonzero_cost_cap_request_ids": [],
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
  "recoverable_can_catalog_recover": true,
  "request_count": 42,
  "request_type_counts": {
    "non_generatable_historical_gtos_source_state": 20,
    "recoverable_market_data": 22
  },
  "required_classification_classes_missing": [],
  "route_id": "G12_GTOS_LOCAL_RESEARCH_DATA_CATALOG_SOURCE_CONTROL_AUDIT",
  "schema_version": "g12_gtos_local_research_data_catalog_source_control_audit_v1",
  "terminal_decision": "ACCEPT_WITH_EXACT_IMPLEMENTATION_FOLLOWUPS",
  "validation_safe": false
}
```
