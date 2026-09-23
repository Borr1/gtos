# Root Resolver Config Schema

Route: `GTOS_LOCAL_RESEARCH_DATA_CATALOG_IMPLEMENTATION_ROUTE`
Terminal decision: `ACCEPT_AS_LOCAL_RESEARCH_DATA_CATALOG_TOOLING`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Summary

```json
{
  "artifact_family": "root_resolver_config_schema",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "generated_at_utc": "2026-05-10T09:31:31Z",
  "hash_policy": {
    "large_safe_files": "deferred_large_file_requires_dedicated_hash_manifest",
    "sensitive_paths": "not_opened_recorded_in_noleak_audit",
    "small_safe_files": "raw_sha256"
  },
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
    "root_id",
    "root_path",
    "root_role",
    "source_family_hint",
    "max_depth",
    "max_files",
    "include_extensions",
    "read_policy",
    "scan_enabled"
  ],
  "root_status_fields": [
    "exists",
    "permission_status",
    "file_count_indexed",
    "file_count_skipped_sensitive"
  ],
  "route_id": "GTOS_LOCAL_RESEARCH_DATA_CATALOG_IMPLEMENTATION_ROUTE",
  "schema_version": "gtos_local_research_data_catalog_implementation_route_v1",
  "terminal_decision": "ACCEPT_AS_LOCAL_RESEARCH_DATA_CATALOG_TOOLING",
  "validation_safe": false
}
```
