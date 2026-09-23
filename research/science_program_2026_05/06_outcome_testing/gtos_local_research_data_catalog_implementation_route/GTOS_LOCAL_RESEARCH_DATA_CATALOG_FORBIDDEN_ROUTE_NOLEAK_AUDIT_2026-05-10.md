# Forbidden Route Noleak Audit

Route: `GTOS_LOCAL_RESEARCH_DATA_CATALOG_IMPLEMENTATION_ROUTE`
Terminal decision: `ACCEPT_AS_LOCAL_RESEARCH_DATA_CATALOG_TOOLING`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Summary

```json
{
  "artifact_family": "forbidden_route_noleak_audit",
  "audit_passed": true,
  "broker_account_order_history_values_read": false,
  "broker_actual_r_read": false,
  "changes_live_trading_behavior": false,
  "credential_paths_opened": false,
  "credentials_touched": false,
  "diff_scope": {
    "changed_or_untracked_paths": [
      ".context/LIVE_STATE.md"
    ],
    "forbidden_live_surface_paths": [],
    "git_diff_returncode": 0,
    "git_untracked_returncode": 0,
    "ok": true
  },
  "forbidden_catalog_row_count": 0,
  "generated_at_utc": "2026-05-10T09:31:31Z",
  "large_files_copied_or_modified": false,
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
  "read_only_scan_actions": [
    "directory_listing",
    "stat",
    "sha256_small_safe_files",
    "large_file_hash_deferral"
  ],
  "result_cost_r_win_rate_expectancy_scoring_opened": false,
  "root_resolution_summary": [
    {
      "exists": true,
      "file_count_indexed": 120,
      "file_count_skipped_sensitive": 1,
      "max_depth": 6,
      "max_files": 120,
      "permission_status": "readable",
      "root_id": "current_worktree_data_root",
      "root_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data",
      "root_role": "worktree_data",
      "scan_enabled": true,
      "scan_status": "indexed"
    },
    {
      "exists": true,
      "file_count_indexed": 1,
      "file_count_skipped_sensitive": 0,
      "max_depth": 5,
      "max_files": 160,
      "permission_status": "readable",
      "root_id": "current_worktree_tick_root",
      "root_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\ticks",
      "root_role": "ticks",
      "scan_enabled": true,
      "scan_status": "indexed"
    },
    {
      "exists": true,
      "file_count_indexed": 104,
      "file_count_skipped_sensitive": 5,
      "max_depth": 2,
      "max_files": 120,
      "permission_status": "readable",
      "root_id": "current_worktree_shadow_logs",
      "root_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs",
      "root_role": "shadow_logs",
      "scan_enabled": true,
      "scan_status": "indexed"
    },
    {
      "exists": true,
      "file_count_indexed": 80,
      "file_count_skipped_sensitive": 0,
      "max_depth": 4,
      "max_files": 80,
      "permission_status": "readable",
      "root_id": "current_worktree_exports",
      "root_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\exports",
      "root_role": "exports",
      "scan_enabled": true,
      "scan_status": "indexed"
    },
    {
      "exists": true,
      "file_count_indexed": 18,
      "file_count_skipped_sensitive": 0,
      "max_depth": 6,
      "max_files": 140,
      "permission_status": "readable",
      "root_id": "current_worktree_external_data",
      "root_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\external",
      "root_role": "external_data",
      "scan_enabled": true,
      "scan_status": "indexed"
    },
    {
      "exists": true,
      "file_count_indexed": 160,
      "file_count_skipped_sensitive": 0,
      "max_depth": 4,
      "max_files": 160,
      "permission_status": "readable",
      "root_id": "current_worktree_science_routes",
      "root_path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\research\\science_program_2026_05\\06_outcome_testing",
      "root_role": "research_routes",
      "scan_enabled": true,
      "scan_status": "indexed"
    },
    {
      "exists": true,
      "file_count_indexed": 150,
      "file_count_skipped_sensitive": 1,
      "max_depth": 6,
      "max_files": 150,
      "permission_status": "readable",
      "root_id": "absolute_main_data_root",
      "root_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data",
      "root_role": "absolute_main_data",
      "scan_enabled": true,
      "scan_status": "indexed"
    },
    {
      "exists": true,
      "file_count_indexed": 80,
      "file_count_skipped_sensitive": 0,
      "max_depth": 5,
      "max_files": 220,
      "permission_status": "readable",
      "root_id": "absolute_main_tick_root",
      "root_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks",
      "root_role": "ticks",
      "scan_enabled": true,
      "scan_status": "indexed"
    },
    {
      "exists": true,
      "file_count_indexed": 116,
      "file_count_skipped_sensitive": 5,
      "max_depth": 2,
      "max_files": 140,
      "permission_status": "readable",
      "root_id": "absolute_main_shadow_logs",
      "root_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs",
      "root_role": "shadow_logs",
      "scan_enabled": true,
      "scan_status": "indexed"
    },
    {
      "exists": true,
      "file_count_indexed": 80,
      "file_count_skipped_sensitive": 0,
      "max_depth": 4,
      "max_files": 80,
      "permission_status": "readable",
      "root_id": "absolute_main_exports",
      "root_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\exports",
      "root_role": "exports",
      "scan_enabled": true,
      "scan_status": "indexed"
    },
    {
      "exists": true,
      "file_count_indexed": 160,
      "file_count_skipped_sensitive": 0,
      "max_depth": 6,
      "max_files": 160,
      "permission_status": "readable",
      "root_id": "absolute_main_external_data",
      "root_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\external",
      "root_role": "external_data",
      "scan_enabled": true,
      "scan_status": "indexed"
    },
    {
      "exists": true,
      "file_count_indexed": 160,
      "file_count_skipped_sensitive": 1,
      "max_depth": 4,
      "max_files": 160,
      "permission_status": "readable",
      "root_id": "prior_worktree_root",
      "root_path": "C:\\tmp\\gtos_otb",
      "root_role": "prior_worktree",
      "scan_enabled": true,
      "scan_status": "indexed"
    },
    {
      "exists": true,
      "file_count_indexed": 80,
      "file_count_skipped_sensitive": 0,
      "max_depth": 3,
      "max_files": 80,
      "permission_status": "readable",
      "root_id": "sierra_chart_root",
      "root_path": "C:\\SierraChart",
      "root_role": "sierra_root",
      "scan_enabled": true,
      "scan_status": "indexed"
    },
    {
      "exists": true,
      "file_count_indexed": 140,
      "file_count_skipped_sensitive": 0,
      "max_depth": 4,
      "max_files": 180,
      "permission_status": "readable",
      "root_id": "sierra_chart_data_root",
      "root_path": "C:\\SierraChart\\Data",
      "root_role": "sierra_data",
      "scan_enabled": true,
      "scan_status": "indexed"
    },
    {
      "exists": true,
      "file_count_indexed": 105,
      "file_count_skipped_sensitive": 0,
      "max_depth": 4,
      "max_files": 180,
      "permission_status": "readable",
      "root_id": "sierra_chart_depth_root",
      "root_path": "C:\\SierraChart\\Data\\MarketDepthData",
      "root_role": "sierra_depth",
      "scan_enabled": true,
      "scan_status": "indexed"
    },
    {
      "exists": true,
      "file_count_indexed": 0,
      "file_count_skipped_sensitive": 0,
      "max_depth": 1,
      "max_files": 0,
      "permission_status": "readable",
      "root_id": "owner_documents_candidate_root",
      "root_path": "C:\\Users\\MSI\\Documents",
      "root_role": "owner_documents",
      "scan_enabled": false,
      "scan_status": "resolved_not_indexed_by_config"
    }
  ],
  "route_id": "GTOS_LOCAL_RESEARCH_DATA_CATALOG_IMPLEMENTATION_ROUTE",
  "schema_version": "gtos_local_research_data_catalog_implementation_route_v1",
  "sensitive_path_not_opened_count": 13,
  "sensitive_path_not_opened_samples": [
    {
      "path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\data\\account_history\\mt5_deals_2026-04-27_2026-05-05.jsonl",
      "read_action": "not_opened",
      "root_id": "current_worktree_data_root",
      "skip_reason": "sensitive_path_fragment:account_history"
    },
    {
      "path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\account_pnl_truth_reconciliation.jsonl",
      "read_action": "not_opened",
      "root_id": "current_worktree_shadow_logs",
      "skip_reason": "sensitive_path_fragment:account_pnl"
    },
    {
      "path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\account_truth_reconciliation_status.jsonl",
      "read_action": "not_opened",
      "root_id": "current_worktree_shadow_logs",
      "skip_reason": "sensitive_path_fragment:account_truth"
    },
    {
      "path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\broker_actual_r_audit.jsonl",
      "read_action": "not_opened",
      "root_id": "current_worktree_shadow_logs",
      "skip_reason": "sensitive_path_fragment:broker_actual_r"
    },
    {
      "path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\daily_pnl.json",
      "read_action": "not_opened",
      "root_id": "current_worktree_shadow_logs",
      "skip_reason": "sensitive_path_fragment:daily_pnl"
    },
    {
      "path": "C:\\tmp\\gtos_otb\\NOFILLTICKRECOVERY\\shadow_logs\\daily_pnl_history.jsonl",
      "read_action": "not_opened",
      "root_id": "current_worktree_shadow_logs",
      "skip_reason": "sensitive_path_fragment:daily_pnl"
    },
    {
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\account_history\\mt5_deals_2026-04-27_2026-05-05.jsonl",
      "read_action": "not_opened",
      "root_id": "absolute_main_data_root",
      "skip_reason": "sensitive_path_fragment:account_history"
    },
    {
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\account_pnl_truth_reconciliation.jsonl",
      "read_action": "not_opened",
      "root_id": "absolute_main_shadow_logs",
      "skip_reason": "sensitive_path_fragment:account_pnl"
    },
    {
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\account_truth_reconciliation_status.jsonl",
      "read_action": "not_opened",
      "root_id": "absolute_main_shadow_logs",
      "skip_reason": "sensitive_path_fragment:account_truth"
    },
    {
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\broker_actual_r_audit.jsonl",
      "read_action": "not_opened",
      "root_id": "absolute_main_shadow_logs",
      "skip_reason": "sensitive_path_fragment:broker_actual_r"
    },
    {
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\daily_pnl.json",
      "read_action": "not_opened",
      "root_id": "absolute_main_shadow_logs",
      "skip_reason": "sensitive_path_fragment:daily_pnl"
    },
    {
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\daily_pnl_history.jsonl",
      "read_action": "not_opened",
      "root_id": "absolute_main_shadow_logs",
      "skip_reason": "sensitive_path_fragment:daily_pnl"
    },
    {
      "path": "C:\\tmp\\gtos_otb\\G0FWDCAPREADY\\data\\account_history\\mt5_deals_2026-04-27_2026-05-05.jsonl",
      "read_action": "not_opened",
      "root_id": "prior_worktree_root",
      "skip_reason": "sensitive_path_fragment:account_history"
    }
  ],
  "terminal_decision": "ACCEPT_AS_LOCAL_RESEARCH_DATA_CATALOG_TOOLING",
  "validation_execution_opened": false,
  "validation_safe": false
}
```
