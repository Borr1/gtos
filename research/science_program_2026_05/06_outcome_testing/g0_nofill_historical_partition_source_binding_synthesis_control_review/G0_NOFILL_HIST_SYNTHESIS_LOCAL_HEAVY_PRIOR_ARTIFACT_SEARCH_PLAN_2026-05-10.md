# Local Heavy And Prior Artifact Search Plan

Route: `G0_NOFILL_HISTORICAL_PARTITION_SOURCE_BINDING_SYNTHESIS_CONTROL_REVIEW`
Terminal decision: `ACCEPT_AS_G0_SOURCE_CONTROL_SYNTHESIS_FOR_NEXT_SEALED_SOURCE_EXPANSION`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Summary

```json
{
  "artifact_family": "local_heavy_prior_artifact_metadata",
  "changes_live_trading_behavior": false,
  "contaminated_source_dates_from_g12": [
    "2026-04-17",
    "2026-04-20",
    "2026-04-30",
    "2026-05-01",
    "2026-05-03",
    "2026-05-04",
    "2026-05-05",
    "2026-05-06"
  ],
  "credentials_touched": false,
  "generated_at_utc": "2026-05-10T04:31:04Z",
  "global_one_day_embargo_clear_tick_dates_by_symbol": {
    "GBPJPY": [
      "2026-04-28",
      "2026-05-08"
    ],
    "GBPUSD": [
      "2026-04-28",
      "2026-05-08"
    ],
    "NAS100": [
      "2026-04-27",
      "2026-04-28",
      "2026-05-08"
    ],
    "US30_cash": [
      "2026-04-27",
      "2026-04-28",
      "2026-05-08"
    ],
    "USDJPY": [
      "2026-04-28",
      "2026-05-08"
    ],
    "XAGUSD": [
      "2026-04-28",
      "2026-05-08"
    ],
    "XAUUSD": [
      "2026-04-28",
      "2026-05-08"
    ]
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
  "prior_exact_route_hits": [
    "C:\\tmp\\gtos_otb\\G0NOFILLHISTSYNTH\\research\\science_program_2026_05\\06_outcome_testing\\g0_nofill_historical_partition_source_binding_synthesis_control_review",
    "C:\\tmp\\gtos_otb\\G0NOFILLHISTSYNTH\\research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_historical_sealed_validation_partition_source_binding_audit",
    "C:\\tmp\\gtos_otb\\G0NOFILLHISTSYNTH\\research\\science_program_2026_05\\06_outcome_testing\\nofill_historical_sealed_validation_partition_and_source_binding",
    "C:\\tmp\\gtos_otb\\G12NOFILLHISTPART\\research\\science_program_2026_05\\06_outcome_testing\\g12_nofill_historical_sealed_validation_partition_source_binding_audit",
    "C:\\tmp\\gtos_otb\\G12NOFILLHISTPART\\research\\science_program_2026_05\\06_outcome_testing\\nofill_historical_sealed_validation_partition_and_source_binding",
    "C:\\tmp\\gtos_otb\\NOFILLHISTPART\\research\\science_program_2026_05\\06_outcome_testing\\nofill_historical_sealed_validation_partition_and_source_binding"
  ],
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "route_conclusion": "Local heavy roots contain source-only candidate material, especially tick parquet and Sierra files. No file is validation-safe from metadata alone; a future source expansion builder must hash inputs, purge contaminated dates/keys/groups, bind all 55 fields, and pass G12 before any validation execution.",
  "route_id": "G0_NOFILL_HISTORICAL_PARTITION_SOURCE_BINDING_SYNTHESIS_CONTROL_REVIEW",
  "schema_version": "g0_nofill_historical_partition_source_binding_synthesis_control_review_v1",
  "searches_performed_this_route": [
    "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\*\\*.parquet",
    "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs selected candidate/pending/nofill logs",
    "C:\\SierraChart\\Data\\*.scid",
    "C:\\SierraChart\\Data\\MarketDepthData\\*.depth",
    "C:\\tmp\\gtos_otb prior NOFILL route directories"
  ],
  "shadow_log_metadata": [
    {
      "exists": true,
      "line_count": 6914,
      "name": "candidate_ltf_path_order.jsonl",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\candidate_ltf_path_order.jsonl",
      "size_bytes": 10146567
    },
    {
      "exists": true,
      "line_count": 66,
      "name": "candidate_mso_snapshot_joins.jsonl",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\candidate_mso_snapshot_joins.jsonl",
      "size_bytes": 250212
    },
    {
      "exists": true,
      "line_count": 3183,
      "name": "candidate_path_contract_audit.jsonl",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\candidate_path_contract_audit.jsonl",
      "size_bytes": 5172490
    },
    {
      "exists": true,
      "line_count": 4088,
      "name": "candidate_path_follow.jsonl",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\candidate_path_follow.jsonl",
      "size_bytes": 15356876
    },
    {
      "exists": true,
      "line_count": 190,
      "name": "candidate_registry_audit.jsonl",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\candidate_registry_audit.jsonl",
      "size_bytes": 439794
    },
    {
      "exists": false,
      "line_count": null,
      "name": "nofill_forward_source_capture.jsonl",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\nofill_forward_source_capture.jsonl",
      "size_bytes": null
    },
    {
      "exists": true,
      "line_count": 237,
      "name": "pending_limit_lifecycle.jsonl",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\pending_limit_lifecycle.jsonl",
      "size_bytes": 461124
    },
    {
      "exists": true,
      "line_count": 89,
      "name": "pending_limit_lifecycle_audit.jsonl",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\pending_limit_lifecycle_audit.jsonl",
      "size_bytes": 261922
    },
    {
      "exists": true,
      "line_count": 285,
      "name": "pending_limit_lifecycle_join_backfill.jsonl",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\shadow_logs\\pending_limit_lifecycle_join_backfill.jsonl",
      "size_bytes": 528146
    }
  ],
  "sierra_depth_metadata": {
    "count_seen_sample_limited": 105,
    "exists": true,
    "pattern": "*.depth",
    "root": "C:\\SierraChart\\Data\\MarketDepthData",
    "sample": [
      "C:\\SierraChart\\Data\\MarketDepthData\\6BM26-CME.2026-05-03.depth",
      "C:\\SierraChart\\Data\\MarketDepthData\\6BM26-CME.2026-05-04.depth",
      "C:\\SierraChart\\Data\\MarketDepthData\\6BM26-CME.2026-05-05.depth",
      "C:\\SierraChart\\Data\\MarketDepthData\\6BM26-CME.2026-05-06.depth",
      "C:\\SierraChart\\Data\\MarketDepthData\\6BM26-CME.2026-05-07.depth",
      "C:\\SierraChart\\Data\\MarketDepthData\\6BM26-CME.2026-05-08.depth",
      "C:\\SierraChart\\Data\\MarketDepthData\\6BM26-CME.2026-05-09.depth",
      "C:\\SierraChart\\Data\\MarketDepthData\\6EM26-CME.2026-05-03.depth",
      "C:\\SierraChart\\Data\\MarketDepthData\\6EM26-CME.2026-05-04.depth",
      "C:\\SierraChart\\Data\\MarketDepthData\\6EM26-CME.2026-05-05.depth",
      "C:\\SierraChart\\Data\\MarketDepthData\\6EM26-CME.2026-05-06.depth",
      "C:\\SierraChart\\Data\\MarketDepthData\\6EM26-CME.2026-05-07.depth",
      "C:\\SierraChart\\Data\\MarketDepthData\\6EM26-CME.2026-05-08.depth",
      "C:\\SierraChart\\Data\\MarketDepthData\\6EM26-CME.2026-05-09.depth",
      "C:\\SierraChart\\Data\\MarketDepthData\\6JM26-CME.2026-05-03.depth",
      "C:\\SierraChart\\Data\\MarketDepthData\\6JM26-CME.2026-05-04.depth"
    ],
    "truncated": false
  },
  "sierra_scid_metadata": {
    "count_seen_sample_limited": 33,
    "exists": true,
    "pattern": "*.scid",
    "root": "C:\\SierraChart\\Data",
    "sample": [
      "C:\\SierraChart\\Data\\6AM26-CME.scid",
      "C:\\SierraChart\\Data\\6BM26-CME.scid",
      "C:\\SierraChart\\Data\\6CM26-CME.scid",
      "C:\\SierraChart\\Data\\6EM26-CME.scid",
      "C:\\SierraChart\\Data\\6JM26-CME.scid",
      "C:\\SierraChart\\Data\\6SM26-CME.scid",
      "C:\\SierraChart\\Data\\AAPL.scid",
      "C:\\SierraChart\\Data\\AMZN-NQTV.scid",
      "C:\\SierraChart\\Data\\BTCUSDT_PERP_BINANCE.scid",
      "C:\\SierraChart\\Data\\CLM26-NYMEX.scid",
      "C:\\SierraChart\\Data\\ESM26-CME.scid",
      "C:\\SierraChart\\Data\\EURUSD.scid",
      "C:\\SierraChart\\Data\\GCM26-COMEX.scid",
      "C:\\SierraChart\\Data\\M2KM26-CME.scid",
      "C:\\SierraChart\\Data\\MCLM26-NYMEX.scid",
      "C:\\SierraChart\\Data\\MESM26-CME.scid"
    ],
    "truncated": false
  },
  "tick_dates_by_symbol": {
    "GBPJPY": [
      "2026-04-28",
      "2026-04-29",
      "2026-04-30",
      "2026-05-01",
      "2026-05-03",
      "2026-05-04",
      "2026-05-05",
      "2026-05-06",
      "2026-05-07",
      "2026-05-08"
    ],
    "GBPUSD": [
      "2026-04-28",
      "2026-04-29",
      "2026-04-30",
      "2026-05-01",
      "2026-05-03",
      "2026-05-04",
      "2026-05-05",
      "2026-05-06",
      "2026-05-07",
      "2026-05-08"
    ],
    "NAS100": [
      "2026-04-27",
      "2026-04-28",
      "2026-04-29",
      "2026-04-30",
      "2026-05-01",
      "2026-05-03",
      "2026-05-04",
      "2026-05-05",
      "2026-05-06",
      "2026-05-07",
      "2026-05-08"
    ],
    "US30_cash": [
      "2026-04-27",
      "2026-04-28",
      "2026-04-29",
      "2026-04-30",
      "2026-05-01",
      "2026-05-03",
      "2026-05-04",
      "2026-05-05",
      "2026-05-06",
      "2026-05-07",
      "2026-05-08"
    ],
    "USDJPY": [
      "2026-04-28",
      "2026-04-29",
      "2026-04-30",
      "2026-05-01",
      "2026-05-03",
      "2026-05-04",
      "2026-05-05",
      "2026-05-06",
      "2026-05-07",
      "2026-05-08"
    ],
    "XAGUSD": [
      "2026-04-28",
      "2026-04-29",
      "2026-04-30",
      "2026-05-01",
      "2026-05-03",
      "2026-05-04",
      "2026-05-05",
      "2026-05-06",
      "2026-05-07",
      "2026-05-08"
    ],
    "XAUUSD": [
      "2026-04-28",
      "2026-04-29",
      "2026-04-30",
      "2026-05-01",
      "2026-05-03",
      "2026-05-04",
      "2026-05-05",
      "2026-05-06",
      "2026-05-07",
      "2026-05-08"
    ]
  },
  "tick_parquet_metadata": {
    "count_seen_sample_limited": 72,
    "exists": true,
    "pattern": "*.parquet",
    "root": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks",
    "sample": [
      "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-04-28.parquet",
      "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-04-29.parquet",
      "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-04-30.parquet",
      "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-01.parquet",
      "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-03.parquet",
      "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-04.parquet",
      "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-05.parquet",
      "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-06.parquet",
      "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-07.parquet",
      "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPJPY\\2026-05-08.parquet",
      "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPUSD\\2026-04-28.parquet",
      "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPUSD\\2026-04-29.parquet",
      "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPUSD\\2026-04-30.parquet",
      "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPUSD\\2026-05-01.parquet",
      "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPUSD\\2026-05-03.parquet",
      "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\GBPUSD\\2026-05-04.parquet"
    ],
    "truncated": false
  },
  "validation_safe": false
}
```
