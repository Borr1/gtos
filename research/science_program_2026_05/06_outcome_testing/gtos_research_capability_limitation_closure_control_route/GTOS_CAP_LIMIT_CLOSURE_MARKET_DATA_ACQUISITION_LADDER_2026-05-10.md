# GTOS Market Data Acquisition Ladder

Route: `GTOS_RESEARCH_CAPABILITY_LIMITATION_CLOSURE_CONTROL_ROUTE`
Terminal decision: `ACCEPT_AS_RESEARCH_CAPABILITY_LIMITATION_CLOSURE_CONTROL_ROUTE`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Summary

```json
{
  "artifact_family": "market_data_acquisition_ladder",
  "blocker_vocabulary": [
    {
      "blocker_code": "RECOVERED_LOCAL_SOURCE",
      "meaning": "Source file exists in current worktree or approved absolute local root and is hashable for the lane.",
      "terminal_action": "Record source hash, as-of convention, lineage, and allowed evidence class."
    },
    {
      "blocker_code": "RECOVERABLE_BY_APPROVED_EXTRACTION",
      "meaning": "Market ticks, bars, quotes, or spreads can be exported read-only from an approved local tool or broker terminal.",
      "terminal_action": "Create extraction manifest with symbol, window, fields, no-leak guard, output path, and hash plan."
    },
    {
      "blocker_code": "RECOVERABLE_BY_OWNER_EXPORT",
      "meaning": "Owner can export the market source or cache file, but this session cannot access it directly.",
      "terminal_action": "Write owner action manifest naming source root, symbol, window, file type, and redaction rule."
    },
    {
      "blocker_code": "RECOVERABLE_BY_SOURCE_CONTRACT",
      "meaning": "Public, vendor, Sierra, or cached source can provide data after a source contract is registered.",
      "terminal_action": "Write pre-call or source-contract manifest before any network, vendor, or API action."
    },
    {
      "blocker_code": "NON_GENERATABLE_SOURCE_STATE",
      "meaning": "Historical GTOS intent, pending lifecycle, order observability, or write-clock truth was not captured in source-safe logs.",
      "terminal_action": "Do not infer from price; write forward capture requirement."
    },
    {
      "blocker_code": "FORBIDDEN_EVIDENCE_CLASS",
      "meaning": "Requested action crosses into validation, result scoring, live trading, broker account/order history, credentials, paid route, or promotion.",
      "terminal_action": "Reject route or split to owner-approved prompt."
    }
  ],
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "exact_local_root_search_policy": [
    "Search current worktree source directories and committed manifests first.",
    "Search absolute main repo roots such as C:\\Users\\MSI\\Documents\\ai-trading-agent\\data and data\\ticks.",
    "Search prior worktrees under C:\\tmp\\gtos_otb as leads, then require source hashes before use.",
    "Search Sierra roots such as C:\\SierraChart\\Data and C:\\SierraChart\\Data\\MarketDepthData for cache presence.",
    "Record every positive and negative root result in a search ledger."
  ],
  "generated_at_utc": "2026-05-10T06:33:15Z",
  "live_effect": false,
  "network_api_vendor_pre_call_manifest_schema": {
    "approval_required": true,
    "fields": [
      "source_id",
      "vendor_or_public_url",
      "dataset",
      "symbols",
      "windows_utc",
      "requested_fields",
      "evidence_class",
      "cost_usd_cap",
      "free_credit_evidence_path",
      "owner_approval_reference",
      "no_leak_constraints",
      "forbidden_fields",
      "raw_capture_output_path",
      "source_index_output_path",
      "raw_sha256_policy"
    ]
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
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "prototype_scan_summary": {
    "catalog_row_count": 198,
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
    ]
  },
  "read_only_mt5_extraction_templates": [
    {
      "allowed_fields": [
        "symbol",
        "from_utc",
        "to_utc",
        "bid",
        "ask",
        "last",
        "volume",
        "flags",
        "time_msc"
      ],
      "execution_status_for_this_route": "not_executed_control_template_only",
      "forbidden_fields": [
        "account",
        "order",
        "deal",
        "position",
        "profit",
        "ticket",
        "broker_actual_r"
      ],
      "required_manifest_fields": [
        "symbol",
        "window_start_utc",
        "window_end_utc",
        "terminal_source",
        "output_path",
        "raw_sha256",
        "as_of_rule",
        "owner_approval_reference_if_needed"
      ],
      "template_id": "MT5_COPY_TICKS_RANGE_READ_ONLY_SOURCE_PACKET"
    },
    {
      "allowed_fields": [
        "symbol",
        "timeframe",
        "time",
        "open",
        "high",
        "low",
        "close",
        "tick_volume",
        "spread",
        "real_volume"
      ],
      "execution_status_for_this_route": "not_executed_control_template_only",
      "forbidden_fields": [
        "account",
        "order",
        "deal",
        "position",
        "profit",
        "ticket",
        "broker_actual_r"
      ],
      "required_manifest_fields": [
        "symbol",
        "timeframe",
        "window_start_utc",
        "window_end_utc",
        "output_path",
        "raw_sha256",
        "as_of_rule"
      ],
      "template_id": "MT5_COPY_RATES_RANGE_READ_ONLY_BAR_SOURCE_PACKET"
    }
  ],
  "route_id": "GTOS_RESEARCH_CAPABILITY_LIMITATION_CLOSURE_CONTROL_ROUTE",
  "schema_version": "gtos_research_capability_limitation_closure_control_route_v1",
  "sierra_vendor_cache_search_policy": [
    "Search Sierra cache directories by symbol contract, source date, and extension before requesting fresh vendor data.",
    "Treat futures proxy files as source candidates only until proxy validity and CFD transfer rules are separately bound.",
    "Hash small files in the catalog prototype and route large files to a dedicated hash manifest."
  ],
  "terminal_decision": "ACCEPT_AS_RESEARCH_CAPABILITY_LIMITATION_CLOSURE_CONTROL_ROUTE",
  "validation_safe": false
}
```
