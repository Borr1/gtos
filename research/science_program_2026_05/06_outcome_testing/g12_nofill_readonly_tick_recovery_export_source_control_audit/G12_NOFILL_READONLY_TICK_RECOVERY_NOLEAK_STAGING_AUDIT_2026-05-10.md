# G12 NOFILL Readonly Tick Recovery No-Leak Staging Audit

Route: `G12_NOFILL_READONLY_TICK_RECOVERY_EXPORT_SOURCE_CONTROL_AUDIT`
Terminal decision: `ACCEPT_AS_G12_READONLY_TICK_RECOVERY_SOURCE_CONTROL_AUDIT_WITH_NONPASSIVE_NEXT_ROUTE`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

```json
{
  "artifact_family": "noleak_staging_audit",
  "audit_status": "PASS",
  "changed_or_untracked_paths": [
    ".context/LIVE_STATE.md",
    "research/science_program_2026_05/06_outcome_testing/g12_nofill_readonly_tick_recovery_export_source_control_audit/G12_NOFILL_READONLY_TICK_RECOVERY_AUDIT_REPORT_2026-05-10.json",
    "research/science_program_2026_05/06_outcome_testing/g12_nofill_readonly_tick_recovery_export_source_control_audit/G12_NOFILL_READONLY_TICK_RECOVERY_AUDIT_REPORT_2026-05-10.md",
    "research/science_program_2026_05/06_outcome_testing/g12_nofill_readonly_tick_recovery_export_source_control_audit/G12_NOFILL_READONLY_TICK_RECOVERY_COMPLETION_AUDIT_2026-05-10.json",
    "research/science_program_2026_05/06_outcome_testing/g12_nofill_readonly_tick_recovery_export_source_control_audit/G12_NOFILL_READONLY_TICK_RECOVERY_COMPLETION_AUDIT_2026-05-10.md",
    "research/science_program_2026_05/06_outcome_testing/g12_nofill_readonly_tick_recovery_export_source_control_audit/G12_NOFILL_READONLY_TICK_RECOVERY_CONTEXT_ANCHOR_2026-05-10.json",
    "research/science_program_2026_05/06_outcome_testing/g12_nofill_readonly_tick_recovery_export_source_control_audit/G12_NOFILL_READONLY_TICK_RECOVERY_CONTEXT_ANCHOR_2026-05-10.md",
    "research/science_program_2026_05/06_outcome_testing/g12_nofill_readonly_tick_recovery_export_source_control_audit/G12_NOFILL_READONLY_TICK_RECOVERY_MACHINE_LEDGER_2026-05-10.json",
    "research/science_program_2026_05/06_outcome_testing/g12_nofill_readonly_tick_recovery_export_source_control_audit/G12_NOFILL_READONLY_TICK_RECOVERY_NEXT_ROUTE_RECOMMENDATION_2026-05-10.json",
    "research/science_program_2026_05/06_outcome_testing/g12_nofill_readonly_tick_recovery_export_source_control_audit/G12_NOFILL_READONLY_TICK_RECOVERY_NEXT_ROUTE_RECOMMENDATION_2026-05-10.md",
    "research/science_program_2026_05/06_outcome_testing/g12_nofill_readonly_tick_recovery_export_source_control_audit/G12_NOFILL_READONLY_TICK_RECOVERY_NOLEAK_STAGING_AUDIT_2026-05-10.json",
    "research/science_program_2026_05/06_outcome_testing/g12_nofill_readonly_tick_recovery_export_source_control_audit/G12_NOFILL_READONLY_TICK_RECOVERY_NOLEAK_STAGING_AUDIT_2026-05-10.md",
    "research/science_program_2026_05/06_outcome_testing/g12_nofill_readonly_tick_recovery_export_source_control_audit/G12_NOFILL_READONLY_TICK_RECOVERY_REMAINING_REQUEST_EXHAUSTION_AUDIT_2026-05-10.json",
    "research/science_program_2026_05/06_outcome_testing/g12_nofill_readonly_tick_recovery_export_source_control_audit/G12_NOFILL_READONLY_TICK_RECOVERY_REMAINING_REQUEST_EXHAUSTION_AUDIT_2026-05-10.md",
    "research/science_program_2026_05/06_outcome_testing/g12_nofill_readonly_tick_recovery_export_source_control_audit/G12_NOFILL_READONLY_TICK_RECOVERY_SOURCE_HASH_WINDOW_COVERAGE_AUDIT_2026-05-10.json",
    "research/science_program_2026_05/06_outcome_testing/g12_nofill_readonly_tick_recovery_export_source_control_audit/G12_NOFILL_READONLY_TICK_RECOVERY_SOURCE_HASH_WINDOW_COVERAGE_AUDIT_2026-05-10.md",
    "research/science_program_2026_05/06_outcome_testing/g12_nofill_readonly_tick_recovery_export_source_control_audit/build_g12_nofill_readonly_tick_recovery_export_source_control_audit_2026_05_10.py",
    "research/science_program_2026_05/06_outcome_testing/g12_nofill_readonly_tick_recovery_export_source_control_audit/test_g12_nofill_readonly_tick_recovery_export_source_control_audit_2026_05_10.py",
    "research/science_program_2026_05/06_outcome_testing/g12_nofill_readonly_tick_recovery_export_source_control_audit/verify_g12_nofill_readonly_tick_recovery_export_source_control_audit_2026_05_10.py",
    "research/science_program_2026_05/06_outcome_testing/nofill_readonly_tick_recovery_export_source_control_route/NOFILL_READONLY_TICK_RECOVERY_VERIFICATION_RESULT_2026-05-10.json"
  ],
  "changes_live_trading_behavior": false,
  "copied_ignored_market_data_file_count": 22,
  "copied_ignored_market_data_files": [
    {
      "path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/NOFILL_READONLY_TICK_RECOVERY_MT5_MARKET_DATA_ONLY_EXTRACTION_2026-05-10.json",
      "size_bytes": 32135
    },
    {
      "path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/NOFILL_READONLY_TICK_RECOVERY_MT5_MARKET_DATA_ONLY_PROBE_2026-05-10.json",
      "size_bytes": 23419
    },
    {
      "path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/GBPJPY/2026-04-14.parquet",
      "size_bytes": 3691827
    },
    {
      "path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/GBPJPY/2026-04-15.parquet",
      "size_bytes": 3923919
    },
    {
      "path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/GBPJPY/2026-04-16.parquet",
      "size_bytes": 3851820
    },
    {
      "path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/GBPJPY/2026-04-22.parquet",
      "size_bytes": 4019231
    },
    {
      "path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/GBPJPY/2026-04-23.parquet",
      "size_bytes": 4684456
    },
    {
      "path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/GBPUSD/2026-04-14.parquet",
      "size_bytes": 2566997
    },
    {
      "path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/GBPUSD/2026-04-15.parquet",
      "size_bytes": 2722667
    },
    {
      "path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/GBPUSD/2026-04-17.parquet",
      "size_bytes": 3049533
    },
    {
      "path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/GBPUSD/2026-04-20.parquet",
      "size_bytes": 3059435
    },
    {
      "path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/GBPUSD/2026-04-21.parquet",
      "size_bytes": 3104581
    },
    {
      "path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/GBPUSD/2026-04-22.parquet",
      "size_bytes": 2869040
    },
    {
      "path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/US30_cash/2026-04-14.parquet",
      "size_bytes": 3363965
    },
    {
      "path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/US30_cash/2026-04-16.parquet",
      "size_bytes": 3227975
    },
    {
      "path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/USDJPY/2026-04-15.parquet",
      "size_bytes": 2243297
    },
    {
      "path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/USDJPY/2026-04-16.parquet",
      "size_bytes": 2203620
    },
    {
      "path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/USDJPY/2026-04-21.parquet",
      "size_bytes": 2367705
    },
    {
      "path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/USDJPY/2026-04-22.parquet",
      "size_bytes": 2175673
    },
    {
      "path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/USDJPY/2026-04-23.parquet",
      "size_bytes": 2711362
    },
    {
      "path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/USDJPY/2026-04-24.parquet",
      "size_bytes": 2345690
    },
    {
      "path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/XAUUSD/2026-04-17.parquet",
      "size_bytes": 8603256
    }
  ],
  "copied_ignored_market_data_total_size_bytes": 66841603,
  "credentials_touched": false,
  "diff_scope_ok": true,
  "forbidden_live_surface_paths": [],
  "forbidden_surface_statement": "No validation execution, outcome review, result scoring, broker actual-R, MT5 account/order/history/deal/position values, paid/API/Databento route, registry edit, remote push, live restart, prompt/config/risk/permissions/safety/selector/canary change, or live trading behavior was opened by this audit.",
  "generated_at_utc": "2026-05-10T10:17:25Z",
  "live_effect": false,
  "non_raw_data_tree_tracked_files_ignored_for_raw_check": [
    "data/ticks/README.md"
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
  "outside_allowed_scope_paths": [],
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "raw_tick_or_csv_files_not_tracked_or_staged": true,
  "raw_tick_or_csv_files_staged": [],
  "raw_tick_or_csv_files_tracked": [],
  "raw_tick_or_csv_files_visible_untracked": [],
  "route_id": "G12_NOFILL_READONLY_TICK_RECOVERY_EXPORT_SOURCE_CONTROL_AUDIT",
  "schema_version": "g12_nofill_readonly_tick_recovery_export_source_control_audit_v1",
  "target_forbidden_api_calls_omitted": [
    "account_info",
    "history_deals_get",
    "history_orders_get",
    "orders_get",
    "positions_get"
  ],
  "target_forbidden_api_used_any": false,
  "target_noleak_audit_status": "PASS",
  "target_staging_policy_status": "PASS",
  "terminal_decision": "ACCEPT_AS_G12_READONLY_TICK_RECOVERY_SOURCE_CONTROL_AUDIT_WITH_NONPASSIVE_NEXT_ROUTE",
  "validation_safe": false
}
```
