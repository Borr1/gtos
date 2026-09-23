# GTOS Local Research Data Catalog Schema

Route: `GTOS_RESEARCH_CAPABILITY_LIMITATION_CLOSURE_CONTROL_ROUTE`
Terminal decision: `ACCEPT_AS_RESEARCH_CAPABILITY_LIMITATION_CLOSURE_CONTROL_ROUTE`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Summary

```json
{
  "acquisition_request_manifest_format": [
    "request_id",
    "source_family",
    "symbol",
    "window_start_utc",
    "window_end_utc",
    "fields",
    "cost_cap_usd",
    "approval_reference",
    "no_leak_constraints",
    "output_path",
    "hash_policy"
  ],
  "artifact_family": "local_research_data_catalog_schema",
  "catalog_schema_fields": [
    "catalog_row_id",
    "root_id",
    "root_path",
    "source_type",
    "symbol",
    "source_date",
    "timeframe",
    "window_utc",
    "source_file",
    "size_bytes",
    "file_hash_sha256",
    "hash_status",
    "lineage",
    "as_of_policy",
    "allowed_evidence_class",
    "scanner_version"
  ],
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "generated_at_utc": "2026-05-10T06:33:15Z",
  "live_effect": false,
  "missing_window_ledger_format": [
    "symbol",
    "source_date",
    "window_utc",
    "missing_source",
    "blocker_class",
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
  "prototype_scanner_output": "GTOS_CAP_LIMIT_CLOSURE_LOCAL_RESEARCH_DATA_CATALOG_PROTOTYPE_2026-05-10.jsonl",
  "route_id": "GTOS_RESEARCH_CAPABILITY_LIMITATION_CLOSURE_CONTROL_ROUTE",
  "schema_version": "gtos_research_capability_limitation_closure_control_route_v1",
  "search_result_ledger_format": [
    "root_id",
    "root_path",
    "exists",
    "permission_status",
    "file_count_indexed",
    "max_files_per_root",
    "exclusion_tokens"
  ],
  "source_hash_policy": {
    "binary_files": "raw_sha256_only",
    "large_files": "dedicated_hash_manifest_required_before_consumption",
    "small_files": "raw_sha256_required",
    "text_files": "raw_sha256_plus_lf_normalized_sha256_when_used_as_parser_or_policy"
  },
  "terminal_decision": "ACCEPT_AS_RESEARCH_CAPABILITY_LIMITATION_CLOSURE_CONTROL_ROUTE",
  "validation_safe": false
}
```
