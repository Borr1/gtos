# Owner Manual Export Fallback Manifest

Route: `XAUUSD_2026_04_15_16_SIERRA_SCID_ALTERNATE_SOURCE_CONTROL_ROUTE`
Terminal posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

```json
{
  "artifact_family": "owner_manual_export_fallback_manifest",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "generated_at_utc": "2026-05-10T10:47:40Z",
  "live_effect": false,
  "market_data_export_requests": [
    {
      "candidate_ids": [
        "XAUUSD_2026-04-15T14:15:05.007998+00:00"
      ],
      "format": "parquet_preferred_csv_acceptable_with_schema",
      "hash_requirement": "SHA256, size, schema, min/max timestamp, source symbol, broker symbol, and candidate-window row counts",
      "no_leak_constraints": [
        "market_data_only",
        "no MT5 account/order/history/deal/position values",
        "no broker outcome labels",
        "no result/cost/R/win-rate/expectancy scoring"
      ],
      "owner_request_id": "OWNER-TICK-0020",
      "remaining_owner_action": "provide_or_authorize_source_safe_mt5_bid_ask_tick_export",
      "required_fields": [
        "time_utc",
        "time_msc",
        "bid",
        "ask",
        "last",
        "volume",
        "flags",
        "source_symbol",
        "broker_symbol",
        "source_file_sha256"
      ],
      "source_date": "2026-04-15",
      "source_symbol": "XAUUSD",
      "symbol": "XAUUSD",
      "target_path_template": "data/ticks/XAUUSD/2026-04-15.parquet",
      "window_end_utc": "2026-04-15T23:59:59.999999Z",
      "window_start_utc": "2026-04-15T00:00:00Z"
    },
    {
      "candidate_ids": [
        "XAUUSD_2026-04-16T09:30:05.013547+00:00",
        "XAUUSD_2026-04-16T13:16:01.126537+00:00"
      ],
      "format": "parquet_preferred_csv_acceptable_with_schema",
      "hash_requirement": "SHA256, size, schema, min/max timestamp, source symbol, broker symbol, and candidate-window row counts",
      "no_leak_constraints": [
        "market_data_only",
        "no MT5 account/order/history/deal/position values",
        "no broker outcome labels",
        "no result/cost/R/win-rate/expectancy scoring"
      ],
      "owner_request_id": "OWNER-TICK-0021",
      "remaining_owner_action": "provide_or_authorize_source_safe_mt5_bid_ask_tick_export",
      "required_fields": [
        "time_utc",
        "time_msc",
        "bid",
        "ask",
        "last",
        "volume",
        "flags",
        "source_symbol",
        "broker_symbol",
        "source_file_sha256"
      ],
      "source_date": "2026-04-16",
      "source_symbol": "XAUUSD",
      "symbol": "XAUUSD",
      "target_path_template": "data/ticks/XAUUSD/2026-04-16.parquet",
      "window_end_utc": "2026-04-16T23:59:59.999999Z",
      "window_start_utc": "2026-04-16T00:00:00Z"
    }
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
  "reason": "SCID cannot satisfy the MT5 bid/ask tick parquet contract.",
  "remaining_market_data_export_request_count": 2,
  "route_id": "XAUUSD_2026_04_15_16_SIERRA_SCID_ALTERNATE_SOURCE_CONTROL_ROUTE",
  "schema_version": "xauusd_2026_04_15_16_sierra_scid_alternate_source_control_route_v1",
  "validation_safe": false
}
```
