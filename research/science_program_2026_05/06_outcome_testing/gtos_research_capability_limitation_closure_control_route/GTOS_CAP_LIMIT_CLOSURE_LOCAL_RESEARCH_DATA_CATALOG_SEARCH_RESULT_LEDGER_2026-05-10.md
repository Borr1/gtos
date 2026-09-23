# GTOS Local Research Data Catalog Search Result Ledger

Route: `GTOS_RESEARCH_CAPABILITY_LIMITATION_CLOSURE_CONTROL_ROUTE`
Terminal decision: `ACCEPT_AS_RESEARCH_CAPABILITY_LIMITATION_CLOSURE_CONTROL_ROUTE`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Summary

```json
{
  "artifact_family": "local_research_data_catalog_search_result_ledger",
  "catalog_row_count": 198,
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "forbidden_filename_tokens_excluded": [
    "account",
    "broker_actual_r",
    "deal",
    "history",
    "order",
    "position",
    "pnl",
    "slippage",
    "trade_record"
  ],
  "generated_at_utc": "2026-05-10T06:33:15Z",
  "hash_size_limit_bytes": 16777216,
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
  "root_ledgers": [
    {
      "exists": true,
      "file_count_indexed": 0,
      "max_files_per_root": 60,
      "root_id": "current_worktree_tick_root",
      "root_path": "C:\\tmp\\gtos_otb\\GTOSLIMITCLOSE\\data\\ticks",
      "source_type": "mt5_tick_parquet"
    },
    {
      "exists": true,
      "file_count_indexed": 60,
      "max_files_per_root": 60,
      "root_id": "absolute_main_tick_root",
      "root_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks",
      "source_type": "mt5_tick_parquet"
    },
    {
      "exists": true,
      "file_count_indexed": 18,
      "max_files_per_root": 60,
      "root_id": "current_worktree_external_data_root",
      "root_path": "C:\\tmp\\gtos_otb\\GTOSLIMITCLOSE\\data\\external",
      "source_type": "local_external_cache"
    },
    {
      "exists": true,
      "file_count_indexed": 60,
      "max_files_per_root": 60,
      "root_id": "sierra_chart_data_root",
      "root_path": "C:\\SierraChart\\Data",
      "source_type": "sierra_chart_cache"
    },
    {
      "exists": true,
      "file_count_indexed": 60,
      "max_files_per_root": 60,
      "root_id": "sierra_chart_depth_root",
      "root_path": "C:\\SierraChart\\Data\\MarketDepthData",
      "source_type": "sierra_chart_depth_cache"
    }
  ],
  "route_id": "GTOS_RESEARCH_CAPABILITY_LIMITATION_CLOSURE_CONTROL_ROUTE",
  "scanner_scope": "read_only_metadata_plus_hash_for_small_allowed_source_files",
  "schema_version": "gtos_research_capability_limitation_closure_control_route_v1",
  "terminal_decision": "ACCEPT_AS_RESEARCH_CAPABILITY_LIMITATION_CLOSURE_CONTROL_ROUTE",
  "validation_safe": false
}
```
