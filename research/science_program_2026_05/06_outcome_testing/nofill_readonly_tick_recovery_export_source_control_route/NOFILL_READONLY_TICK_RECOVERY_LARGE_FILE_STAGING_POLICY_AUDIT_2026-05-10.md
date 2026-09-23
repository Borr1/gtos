# NOFILL Read-Only Tick Recovery Large File And Staging Policy Audit

Route: `NOFILL_READONLY_TICK_RECOVERY_EXPORT_SOURCE_CONTROL_ROUTE`
Terminal decision: `ACCEPT_WITH_EXACT_REMAINING_EXPORT_OR_ACCESS_REQUESTS`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Summary

## Machine Payload

```json
{
  "artifact_family": "large_file_staging_policy_audit",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "generated_at_utc": "2026-05-10T09:46:58Z",
  "large_file_hash_deferral_count": 0,
  "large_unhashed_files": [],
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
  "policy_status": "PASS",
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "raw_market_data_file_count": 20,
  "raw_market_data_files": [
    {
      "git_ignored": true,
      "git_tracked": false,
      "path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/GBPJPY/2026-04-14.parquet",
      "sha256_recorded": true,
      "size_bytes": 3691827
    },
    {
      "git_ignored": true,
      "git_tracked": false,
      "path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/GBPJPY/2026-04-15.parquet",
      "sha256_recorded": true,
      "size_bytes": 3923919
    },
    {
      "git_ignored": true,
      "git_tracked": false,
      "path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/GBPJPY/2026-04-16.parquet",
      "sha256_recorded": true,
      "size_bytes": 3851820
    },
    {
      "git_ignored": true,
      "git_tracked": false,
      "path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/GBPJPY/2026-04-22.parquet",
      "sha256_recorded": true,
      "size_bytes": 4019231
    },
    {
      "git_ignored": true,
      "git_tracked": false,
      "path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/GBPJPY/2026-04-23.parquet",
      "sha256_recorded": true,
      "size_bytes": 4684456
    },
    {
      "git_ignored": true,
      "git_tracked": false,
      "path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/GBPUSD/2026-04-14.parquet",
      "sha256_recorded": true,
      "size_bytes": 2566997
    },
    {
      "git_ignored": true,
      "git_tracked": false,
      "path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/GBPUSD/2026-04-15.parquet",
      "sha256_recorded": true,
      "size_bytes": 2722667
    },
    {
      "git_ignored": true,
      "git_tracked": false,
      "path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/GBPUSD/2026-04-17.parquet",
      "sha256_recorded": true,
      "size_bytes": 3049533
    },
    {
      "git_ignored": true,
      "git_tracked": false,
      "path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/GBPUSD/2026-04-20.parquet",
      "sha256_recorded": true,
      "size_bytes": 3059435
    },
    {
      "git_ignored": true,
      "git_tracked": false,
      "path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/GBPUSD/2026-04-21.parquet",
      "sha256_recorded": true,
      "size_bytes": 3104581
    },
    {
      "git_ignored": true,
      "git_tracked": false,
      "path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/GBPUSD/2026-04-22.parquet",
      "sha256_recorded": true,
      "size_bytes": 2869040
    },
    {
      "git_ignored": true,
      "git_tracked": false,
      "path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/US30_cash/2026-04-14.parquet",
      "sha256_recorded": true,
      "size_bytes": 3363965
    },
    {
      "git_ignored": true,
      "git_tracked": false,
      "path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/US30_cash/2026-04-16.parquet",
      "sha256_recorded": true,
      "size_bytes": 3227975
    },
    {
      "git_ignored": true,
      "git_tracked": false,
      "path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/USDJPY/2026-04-15.parquet",
      "sha256_recorded": true,
      "size_bytes": 2243297
    },
    {
      "git_ignored": true,
      "git_tracked": false,
      "path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/USDJPY/2026-04-16.parquet",
      "sha256_recorded": true,
      "size_bytes": 2203620
    },
    {
      "git_ignored": true,
      "git_tracked": false,
      "path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/USDJPY/2026-04-21.parquet",
      "sha256_recorded": true,
      "size_bytes": 2367705
    },
    {
      "git_ignored": true,
      "git_tracked": false,
      "path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/USDJPY/2026-04-22.parquet",
      "sha256_recorded": true,
      "size_bytes": 2175673
    },
    {
      "git_ignored": true,
      "git_tracked": false,
      "path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/USDJPY/2026-04-23.parquet",
      "sha256_recorded": true,
      "size_bytes": 2711362
    },
    {
      "git_ignored": true,
      "git_tracked": false,
      "path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/USDJPY/2026-04-24.parquet",
      "sha256_recorded": true,
      "size_bytes": 2345690
    },
    {
      "git_ignored": true,
      "git_tracked": false,
      "path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/XAUUSD/2026-04-17.parquet",
      "sha256_recorded": true,
      "size_bytes": 8603256
    }
  ],
  "raw_market_data_files_changed_or_untracked_visible_to_git": [],
  "raw_market_data_files_gitignored": true,
  "raw_market_data_files_not_tracked": true,
  "route_id": "NOFILL_READONLY_TICK_RECOVERY_EXPORT_SOURCE_CONTROL_ROUTE",
  "schema_version": "nofill_readonly_tick_recovery_export_source_control_route_v1",
  "terminal_decision": "ACCEPT_WITH_EXACT_REMAINING_EXPORT_OR_ACCESS_REQUESTS",
  "validation_safe": false
}
```
