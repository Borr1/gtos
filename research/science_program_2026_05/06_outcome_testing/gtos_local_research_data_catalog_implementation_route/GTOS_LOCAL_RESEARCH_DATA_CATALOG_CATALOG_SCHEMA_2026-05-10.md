# Catalog Schema

Route: `GTOS_LOCAL_RESEARCH_DATA_CATALOG_IMPLEMENTATION_ROUTE`
Terminal decision: `ACCEPT_AS_LOCAL_RESEARCH_DATA_CATALOG_TOOLING`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Summary

```json
{
  "acquisition_manifest_schema_ref": "GTOS_LOCAL_RESEARCH_DATA_CATALOG_ACQUISITION_REQUEST_MANIFEST_SCHEMA_2026-05-10.json",
  "artifact_family": "catalog_schema",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "generated_at_utc": "2026-05-10T09:31:31Z",
  "live_effect": false,
  "missing_window_ledger_format": [
    "window_id",
    "source_requirement_type",
    "symbol",
    "source_date",
    "timeframe",
    "source_family",
    "local_catalog_status",
    "blocker_code",
    "exact_next_action"
  ],
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
  "required_catalog_row_fields": [
    "catalog_row_id",
    "root_id",
    "root_path",
    "absolute_path",
    "relative_path",
    "repo_relative_path",
    "source_family",
    "symbol",
    "source_date",
    "source_date_range",
    "timeframe",
    "file_extension",
    "size_bytes",
    "mtime_utc",
    "hash_policy",
    "sha256",
    "hash_status",
    "large_file_hash_deferral_id",
    "allowed_evidence_class",
    "forbidden_use_notes",
    "read_actions"
  ],
  "route_id": "GTOS_LOCAL_RESEARCH_DATA_CATALOG_IMPLEMENTATION_ROUTE",
  "schema_version": "gtos_local_research_data_catalog_implementation_route_v1",
  "search_result_ledger_format": [
    "query_id",
    "purpose",
    "match_count",
    "positive_evidence",
    "negative_evidence",
    "roots_searched"
  ],
  "terminal_decision": "ACCEPT_AS_LOCAL_RESEARCH_DATA_CATALOG_TOOLING",
  "validation_safe": false
}
```
