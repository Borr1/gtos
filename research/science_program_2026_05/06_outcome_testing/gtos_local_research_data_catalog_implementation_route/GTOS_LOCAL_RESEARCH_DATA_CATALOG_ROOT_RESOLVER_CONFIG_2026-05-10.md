# Root Resolver Config

Route: `GTOS_LOCAL_RESEARCH_DATA_CATALOG_IMPLEMENTATION_ROUTE`
Terminal decision: `ACCEPT_AS_LOCAL_RESEARCH_DATA_CATALOG_TOOLING`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Summary

```json
{
  "artifact_family": "root_resolver_config",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "generated_at_utc": "2026-05-10T09:31:26Z",
  "hash_size_limit_bytes": 8388608,
  "ignore_directory_names": [
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "node_modules",
    "site-packages",
    "venv"
  ],
  "live_effect": false,
  "max_total_catalog_rows": 1200,
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
  "roots": [
    {
      "include_extensions": [
        ".csv",
        ".depth",
        ".dly",
        ".feather",
        ".json",
        ".jsonl",
        ".md",
        ".parquet",
        ".py",
        ".scid",
        ".txt",
        ".yaml",
        ".yml"
      ],
      "max_depth": 6,
      "max_files": 120,
      "read_policy": "stat_and_hash_small_safe_files_only",
      "root_id": "current_worktree_data_root",
      "root_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data",
      "root_role": "worktree_data",
      "scan_enabled": true,
      "source_family_hint": "local_research_data"
    },
    {
      "include_extensions": [
        ".csv",
        ".depth",
        ".dly",
        ".feather",
        ".json",
        ".jsonl",
        ".md",
        ".parquet",
        ".py",
        ".scid",
        ".txt",
        ".yaml",
        ".yml"
      ],
      "max_depth": 5,
      "max_files": 160,
      "read_policy": "stat_and_hash_small_safe_files_only",
      "root_id": "current_worktree_tick_root",
      "root_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\ticks",
      "root_role": "ticks",
      "scan_enabled": true,
      "source_family_hint": "mt5_tick_parquet"
    },
    {
      "include_extensions": [
        ".csv",
        ".depth",
        ".dly",
        ".feather",
        ".json",
        ".jsonl",
        ".md",
        ".parquet",
        ".py",
        ".scid",
        ".txt",
        ".yaml",
        ".yml"
      ],
      "max_depth": 2,
      "max_files": 120,
      "read_policy": "stat_and_hash_small_safe_files_only",
      "root_id": "current_worktree_shadow_logs",
      "root_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs",
      "root_role": "shadow_logs",
      "scan_enabled": true,
      "source_family_hint": "shadow_log_source_control"
    },
    {
      "include_extensions": [
        ".csv",
        ".depth",
        ".dly",
        ".feather",
        ".json",
        ".jsonl",
        ".md",
        ".parquet",
        ".py",
        ".scid",
        ".txt",
        ".yaml",
        ".yml"
      ],
      "max_depth": 4,
      "max_files": 80,
      "read_policy": "stat_and_hash_small_safe_files_only",
      "root_id": "current_worktree_exports",
      "root_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports",
      "root_role": "exports",
      "scan_enabled": true,
      "source_family_hint": "exported_source_control"
    },
    {
      "include_extensions": [
        ".csv",
        ".depth",
        ".dly",
        ".feather",
        ".json",
        ".jsonl",
        ".md",
        ".parquet",
        ".py",
        ".scid",
        ".txt",
        ".yaml",
        ".yml"
      ],
      "max_depth": 6,
      "max_files": 140,
      "read_policy": "stat_and_hash_small_safe_files_only",
      "root_id": "current_worktree_external_data",
      "root_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\external",
      "root_role": "external_data",
      "scan_enabled": true,
      "source_family_hint": "local_external_cache"
    },
    {
      "include_extensions": [
        ".csv",
        ".depth",
        ".dly",
        ".feather",
        ".json",
        ".jsonl",
        ".md",
        ".parquet",
        ".py",
        ".scid",
        ".txt",
        ".yaml",
        ".yml"
      ],
      "max_depth": 4,
      "max_files": 160,
      "read_policy": "stat_and_hash_small_safe_files_only",
      "root_id": "current_worktree_science_routes",
      "root_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing",
      "root_role": "research_routes",
      "scan_enabled": true,
      "source_family_hint": "research_route_artifact"
    },
    {
      "include_extensions": [
        ".csv",
        ".depth",
        ".dly",
        ".feather",
        ".json",
        ".jsonl",
        ".md",
        ".parquet",
        ".py",
        ".scid",
        ".txt",
        ".yaml",
        ".yml"
      ],
      "max_depth": 6,
      "max_files": 150,
      "read_policy": "stat_and_hash_small_safe_files_only",
      "root_id": "absolute_main_data_root",
      "root_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data",
      "root_role": "absolute_main_data",
      "scan_enabled": true,
      "source_family_hint": "local_research_data"
    },
    {
      "include_extensions": [
        ".csv",
        ".depth",
        ".dly",
        ".feather",
        ".json",
        ".jsonl",
        ".md",
        ".parquet",
        ".py",
        ".scid",
        ".txt",
        ".yaml",
        ".yml"
      ],
      "max_depth": 5,
      "max_files": 220,
      "read_policy": "stat_and_hash_small_safe_files_only",
      "root_id": "absolute_main_tick_root",
      "root_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks",
      "root_role": "ticks",
      "scan_enabled": true,
      "source_family_hint": "mt5_tick_parquet"
    },
    {
      "include_extensions": [
        ".csv",
        ".depth",
        ".dly",
        ".feather",
        ".json",
        ".jsonl",
        ".md",
        ".parquet",
        ".py",
        ".scid",
        ".txt",
        ".yaml",
        ".yml"
      ],
      "max_depth": 2,
      "max_files": 140,
      "read_policy": "stat_and_hash_small_safe_files_only",
      "root_id": "absolute_main_shadow_logs",
      "root_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs",
      "root_role": "shadow_logs",
      "scan_enabled": true,
      "source_family_hint": "shadow_log_source_control"
    },
    {
      "include_extensions": [
        ".csv",
        ".depth",
        ".dly",
        ".feather",
        ".json",
        ".jsonl",
        ".md",
        ".parquet",
        ".py",
        ".scid",
        ".txt",
        ".yaml",
        ".yml"
      ],
      "max_depth": 4,
      "max_files": 80,
      "read_policy": "stat_and_hash_small_safe_files_only",
      "root_id": "absolute_main_exports",
      "root_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports",
      "root_role": "exports",
      "scan_enabled": true,
      "source_family_hint": "exported_source_control"
    },
    {
      "include_extensions": [
        ".csv",
        ".depth",
        ".dly",
        ".feather",
        ".json",
        ".jsonl",
        ".md",
        ".parquet",
        ".py",
        ".scid",
        ".txt",
        ".yaml",
        ".yml"
      ],
      "max_depth": 6,
      "max_files": 160,
      "read_policy": "stat_and_hash_small_safe_files_only",
      "root_id": "absolute_main_external_data",
      "root_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external",
      "root_role": "external_data",
      "scan_enabled": true,
      "source_family_hint": "local_external_cache"
    },
    {
      "include_extensions": [
        ".csv",
        ".depth",
        ".dly",
        ".feather",
        ".json",
        ".jsonl",
        ".md",
        ".parquet",
        ".py",
        ".scid",
        ".txt",
        ".yaml",
        ".yml"
      ],
      "max_depth": 4,
      "max_files": 160,
      "read_policy": "stat_and_hash_small_safe_files_only",
      "root_id": "prior_worktree_root",
      "root_path": "C:\\tmp\\gtos_otb",
      "root_role": "prior_worktree",
      "scan_enabled": true,
      "source_family_hint": "prior_worktree_lead"
    },
    {
      "include_extensions": [
        ".csv",
        ".depth",
        ".dly",
        ".feather",
        ".json",
        ".jsonl",
        ".md",
        ".parquet",
        ".py",
        ".scid",
        ".txt",
        ".yaml",
        ".yml"
      ],
      "max_depth": 3,
      "max_files": 80,
      "read_policy": "stat_and_hash_small_safe_files_only",
      "root_id": "sierra_chart_root",
      "root_path": "C:\\SierraChart",
      "root_role": "sierra_root",
      "scan_enabled": true,
      "source_family_hint": "sierra_chart_cache"
    },
    {
      "include_extensions": [
        ".csv",
        ".depth",
        ".dly",
        ".feather",
        ".json",
        ".jsonl",
        ".md",
        ".parquet",
        ".py",
        ".scid",
        ".txt",
        ".yaml",
        ".yml"
      ],
      "max_depth": 4,
      "max_files": 180,
      "read_policy": "stat_and_hash_small_safe_files_only",
      "root_id": "sierra_chart_data_root",
      "root_path": "C:\\SierraChart\\Data",
      "root_role": "sierra_data",
      "scan_enabled": true,
      "source_family_hint": "sierra_chart_cache"
    },
    {
      "include_extensions": [
        ".csv",
        ".depth",
        ".dly",
        ".feather",
        ".json",
        ".jsonl",
        ".md",
        ".parquet",
        ".py",
        ".scid",
        ".txt",
        ".yaml",
        ".yml"
      ],
      "max_depth": 4,
      "max_files": 180,
      "read_policy": "stat_and_hash_small_safe_files_only",
      "root_id": "sierra_chart_depth_root",
      "root_path": "C:\\SierraChart\\Data\\MarketDepthData",
      "root_role": "sierra_depth",
      "scan_enabled": true,
      "source_family_hint": "sierra_chart_depth_cache"
    },
    {
      "include_extensions": [
        ".csv",
        ".depth",
        ".dly",
        ".feather",
        ".json",
        ".jsonl",
        ".md",
        ".parquet",
        ".py",
        ".scid",
        ".txt",
        ".yaml",
        ".yml"
      ],
      "max_depth": 1,
      "max_files": 0,
      "read_policy": "stat_and_hash_small_safe_files_only",
      "root_id": "owner_documents_candidate_root",
      "root_path": "C:\\Users\\MSI\\Documents",
      "root_role": "owner_documents",
      "scan_enabled": false,
      "source_family_hint": "owner_export_candidate"
    }
  ],
  "route_id": "GTOS_LOCAL_RESEARCH_DATA_CATALOG_IMPLEMENTATION_ROUTE",
  "schema_version": "gtos_local_research_data_catalog_implementation_route_v1",
  "search_queries": [
    {
      "extensions": [
        ".parquet"
      ],
      "purpose": "NOFILL source-expansion fixture tick file search",
      "query_id": "accepted_fixture_nas100_tick_2026_05_08",
      "source_date": "2026-05-08",
      "source_family_contains": "tick",
      "symbol": "NAS100"
    },
    {
      "extensions": [
        ".parquet"
      ],
      "purpose": "NOFILL source-expansion fixture tick file search",
      "query_id": "accepted_fixture_us30_cash_tick_2026_05_08",
      "source_date": "2026-05-08",
      "source_family_contains": "tick",
      "symbol": "US30_cash"
    },
    {
      "extensions": [
        ".parquet"
      ],
      "purpose": "recoverable market-data absence example",
      "query_id": "upstream_missing_gbpjpy_tick_2026_04_14",
      "source_date": "2026-04-14",
      "source_family_contains": "tick",
      "symbol": "GBPJPY"
    },
    {
      "extensions": [
        ".json",
        ".md",
        ".py"
      ],
      "path_contains": "g12_nofill_historical_source_expansion_hash_repair_reaudit",
      "purpose": "current acceptance-fixture G12 source-control route artifact search",
      "query_id": "g12_hash_repair_reaudit_manifest"
    },
    {
      "extensions": [
        ".jsonl"
      ],
      "path_contains": "GTOS_CAP_LIMIT_CLOSURE_LOCAL_RESEARCH_DATA_CATALOG_PROTOTYPE",
      "purpose": "upstream 198-row prototype catalog source search",
      "query_id": "cap_limit_catalog_prototype"
    },
    {
      "extensions": [
        ".scid",
        ".depth"
      ],
      "purpose": "Sierra local cache source discovery",
      "query_id": "sierra_nq_or_nqm26_depth_or_scid",
      "symbol_any": [
        "NQ",
        "NQM26"
      ]
    }
  ],
  "sensitive_path_fragments": [
    ".env",
    "api_key",
    "apikey",
    "secret",
    "password",
    "credential",
    "login",
    "broker_actual_r",
    "account_history",
    "account_pnl",
    "account_truth",
    "daily_pnl",
    "deal_history",
    "deals",
    "positions",
    "orders",
    "trade_records",
    "ticket"
  ],
  "terminal_decision": "ACCEPT_AS_LOCAL_RESEARCH_DATA_CATALOG_TOOLING",
  "validation_safe": false
}
```
