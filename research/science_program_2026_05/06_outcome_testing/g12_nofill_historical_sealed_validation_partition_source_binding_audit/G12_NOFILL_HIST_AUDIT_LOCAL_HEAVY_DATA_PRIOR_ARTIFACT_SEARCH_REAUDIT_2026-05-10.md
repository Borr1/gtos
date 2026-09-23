# Local Heavy Data Prior Artifact Search Reaudit

Route: `G12_NOFILL_HISTORICAL_SEALED_VALIDATION_PARTITION_SOURCE_BINDING_AUDIT`
Target route: `NOFILL_HISTORICAL_SEALED_VALIDATION_PARTITION_AND_SOURCE_BINDING`
Promotion posture: `NO_PROMOTION_VERDICT`
Safe flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

## Summary

```json
{
  "absolute_main_exists": true,
  "absolute_main_nofill_route_dir_count_recomputed": 40,
  "artifact_family": "local_heavy_data_prior_artifact_search_reaudit",
  "audit_passed": true,
  "changes_live_trading_behavior": false,
  "checks": {
    "absolute_main_metadata_reaudit_completed_or_absence_recorded": true,
    "current_worktree_reaudit_completed": true,
    "nofill_forward_capture_log_absence_rechecked": true,
    "prior_artifact_search_not_zero": true,
    "target_search_recorded_roots": true,
    "tick_root_metadata_reaudit_completed_or_absence_recorded": true,
    "tick_windows_kept_source_only": true
  },
  "credentials_touched": false,
  "current_worktree_nofill_route_dir_count_recomputed": 41,
  "current_worktree_root": "C:\\tmp\\gtos_otb\\G12NOFILLHISTPART",
  "live_effect": false,
  "nofill_forward_source_capture_log_hits_rechecked": [],
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
  "prior_tmp_exact_target_route_hits": [
    "C:\\tmp\\gtos_otb\\G12NOFILLHISTPART\\research\\science_program_2026_05\\06_outcome_testing\\nofill_historical_sealed_validation_partition_and_source_binding",
    "C:\\tmp\\gtos_otb\\NOFILLHISTPART\\research\\science_program_2026_05\\06_outcome_testing\\nofill_historical_sealed_validation_partition_and_source_binding"
  ],
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "reaudit_conclusion": "Current worktree and absolute/local-heavy metadata do not contradict zero committed sealed-validation rows; tick/Sierra files remain source-only inputs requiring future hashed extraction and prior-use audit.",
  "sierra_depth_metadata_reaudit": {
    "count_seen": 105,
    "exists": true,
    "pattern": "*.depth",
    "sample": [
      "C:\\SierraChart\\Data\\MarketDepthData\\6BM26-CME.2026-05-03.depth",
      "C:\\SierraChart\\Data\\MarketDepthData\\6BM26-CME.2026-05-04.depth",
      "C:\\SierraChart\\Data\\MarketDepthData\\6BM26-CME.2026-05-05.depth",
      "C:\\SierraChart\\Data\\MarketDepthData\\6BM26-CME.2026-05-06.depth",
      "C:\\SierraChart\\Data\\MarketDepthData\\6BM26-CME.2026-05-07.depth",
      "C:\\SierraChart\\Data\\MarketDepthData\\6BM26-CME.2026-05-08.depth",
      "C:\\SierraChart\\Data\\MarketDepthData\\6BM26-CME.2026-05-09.depth",
      "C:\\SierraChart\\Data\\MarketDepthData\\6EM26-CME.2026-05-03.depth"
    ],
    "truncated": false
  },
  "sierra_scid_metadata_reaudit": {
    "count_seen": 33,
    "exists": true,
    "pattern": "*.scid",
    "sample": [
      "C:\\SierraChart\\Data\\6AM26-CME.scid",
      "C:\\SierraChart\\Data\\6BM26-CME.scid",
      "C:\\SierraChart\\Data\\6CM26-CME.scid",
      "C:\\SierraChart\\Data\\6EM26-CME.scid",
      "C:\\SierraChart\\Data\\6JM26-CME.scid",
      "C:\\SierraChart\\Data\\6SM26-CME.scid",
      "C:\\SierraChart\\Data\\AAPL.scid",
      "C:\\SierraChart\\Data\\AMZN-NQTV.scid"
    ],
    "truncated": false
  },
  "target_route_id": "NOFILL_HISTORICAL_SEALED_VALIDATION_PARTITION_AND_SOURCE_BINDING",
  "target_search_root_literals": [
    "C:\\tmp\\gtos_otb\\NOFILLHISTPART",
    "C:\\Users\\MSI\\Documents\\ai-trading-agent",
    "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks",
    "C:\\SierraChart\\Data",
    "C:\\tmp\\gtos_otb"
  ],
  "target_tick_source_only_candidate_window_count": 7,
  "target_worktree_root_literal_matches_current_worktree": false,
  "tick_parquet_metadata_reaudit": {
    "count_seen": 72,
    "exists": true,
    "pattern": "*.parquet",
    "sample": [
      "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-04-28.parquet",
      "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-04-29.parquet",
      "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-04-30.parquet",
      "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-01.parquet",
      "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-03.parquet",
      "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-04.parquet",
      "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-05.parquet",
      "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-06.parquet"
    ],
    "truncated": false
  },
  "validation_safe": false
}
```
