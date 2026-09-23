# Nofill Source State Gap Closure Tick Export Extraction Manifest 2026-05-10

- Route: `NOFILL_SOURCE_STATE_CAPTURE_GAP_CLOSURE_AND_TICK_EXPORT_MANIFEST_ROUTE`
- Promotion posture: `NO_PROMOTION_VERDICT`
- `validation_safe=false`
- `outcome_review_opened=false`
- `live_effect=false`

- tick_export_dependent_blocker_count: `31`

## Machine Payload

```json
{
  "artifact_family": "tick_export_readonly_extraction_manifest",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "generated_at_utc": "2026-05-10T08:33:44Z",
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
  "read_only_extraction_policy": "This route specifies market-data-only tick extraction/export. It does not call MT5 account, order, history, deal, or position APIs and does not score results.",
  "route_id": "NOFILL_SOURCE_STATE_CAPTURE_GAP_CLOSURE_AND_TICK_EXPORT_MANIFEST_ROUTE",
  "rows_count": 31,
  "rows_sample": [
    {
      "candidate_id": "GBPJPY_2026-04-14T01:15:05.006410+00:00",
      "clean_packet_use_status": "still_blocked_until_source_state_capture_exists",
      "contamination_or_embargo_blocked": false,
      "export_request_id": "TICK-EXPORT-0001",
      "format": "parquet_preferred_csv_acceptable_with_schema",
      "no_leak_constraints": [
        "market_data_only",
        "no MT5 account/order/history/deal/position values",
        "no broker outcome labels",
        "no result/cost/R/win-rate/expectancy scoring"
      ],
      "owner_export_status": "owner_export_required_if_read_only_local_extraction_is_unavailable",
      "read_only_extraction_status": "specified_not_executed_in_source_control_route",
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
      "source_date": "2026-04-14",
      "source_symbol": "GBPJPY",
      "symbol": "GBPJPY",
      "target_hash": "sha256_required_before_consumption",
      "target_path_template": "data/ticks/GBPJPY/2026-04-14.parquet",
      "timeframe": "TICK",
      "window_end_utc": "2026-04-14T23:59:59.999999Z",
      "window_start_utc": "2026-04-14T00:00:00Z"
    },
    {
      "candidate_id": "GBPJPY_2026-04-14T15:30:05.012815+00:00",
      "clean_packet_use_status": "still_blocked_until_source_state_capture_exists",
      "contamination_or_embargo_blocked": false,
      "export_request_id": "TICK-EXPORT-0002",
      "format": "parquet_preferred_csv_acceptable_with_schema",
      "no_leak_constraints": [
        "market_data_only",
        "no MT5 account/order/history/deal/position values",
        "no broker outcome labels",
        "no result/cost/R/win-rate/expectancy scoring"
      ],
      "owner_export_status": "owner_export_required_if_read_only_local_extraction_is_unavailable",
      "read_only_extraction_status": "specified_not_executed_in_source_control_route",
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
      "source_date": "2026-04-14",
      "source_symbol": "GBPJPY",
      "symbol": "GBPJPY",
      "target_hash": "sha256_required_before_consumption",
      "target_path_template": "data/ticks/GBPJPY/2026-04-14.parquet",
      "timeframe": "TICK",
      "window_end_utc": "2026-04-14T23:59:59.999999Z",
      "window_start_utc": "2026-04-14T00:00:00Z"
    },
    {
      "candidate_id": "GBPJPY_2026-04-15T00:30:05.011237+00:00",
      "clean_packet_use_status": "still_blocked_until_source_state_capture_exists",
      "contamination_or_embargo_blocked": false,
      "export_request_id": "TICK-EXPORT-0003",
      "format": "parquet_preferred_csv_acceptable_with_schema",
      "no_leak_constraints": [
        "market_data_only",
        "no MT5 account/order/history/deal/position values",
        "no broker outcome labels",
        "no result/cost/R/win-rate/expectancy scoring"
      ],
      "owner_export_status": "owner_export_required_if_read_only_local_extraction_is_unavailable",
      "read_only_extraction_status": "specified_not_executed_in_source_control_route",
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
      "source_symbol": "GBPJPY",
      "symbol": "GBPJPY",
      "target_hash": "sha256_required_before_consumption",
      "target_path_template": "data/ticks/GBPJPY/2026-04-15.parquet",
      "timeframe": "TICK",
      "window_end_utc": "2026-04-15T23:59:59.999999Z",
      "window_start_utc": "2026-04-15T00:00:00Z"
    }
  ],
  "schema_version": "nofill_source_state_capture_gap_closure_and_tick_export_manifest_route_v1",
  "tick_export_dependent_blocker_count": 31,
  "unique_export_requests": [
    {
      "candidate_ids": [
        "GBPJPY_2026-04-14T01:15:05.006410+00:00",
        "GBPJPY_2026-04-14T15:30:05.012815+00:00"
      ],
      "format": "parquet_preferred_csv_acceptable_with_schema",
      "no_leak_constraints": [
        "market_data_only",
        "no MT5 account/order/history/deal/position values",
        "no broker outcome labels",
        "no result/cost/R/win-rate/expectancy scoring"
      ],
      "owner_request_id": "OWNER-TICK-0001",
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
      "source_date": "2026-04-14",
      "source_symbol": "GBPJPY",
      "symbol": "GBPJPY",
      "target_hash": "sha256_required_before_consumption",
      "target_path_template": "data/ticks/GBPJPY/2026-04-14.parquet",
      "window_end_utc": "2026-04-14T23:59:59.999999Z",
      "window_start_utc": "2026-04-14T00:00:00Z"
    },
    {
      "candidate_ids": [
        "GBPJPY_2026-04-15T00:30:05.011237+00:00",
        "GBPJPY_2026-04-15T13:15:57.164919+00:00"
      ],
      "format": "parquet_preferred_csv_acceptable_with_schema",
      "no_leak_constraints": [
        "market_data_only",
        "no MT5 account/order/history/deal/position values",
        "no broker outcome labels",
        "no result/cost/R/win-rate/expectancy scoring"
      ],
      "owner_request_id": "OWNER-TICK-0002",
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
      "source_symbol": "GBPJPY",
      "symbol": "GBPJPY",
      "target_hash": "sha256_required_before_consumption",
      "target_path_template": "data/ticks/GBPJPY/2026-04-15.parquet",
      "window_end_utc": "2026-04-15T23:59:59.999999Z",
      "window_start_utc": "2026-04-15T00:00:00Z"
    },
    {
      "candidate_ids": [
        "GBPJPY_2026-04-16T00:16:00.503237+00:00"
      ],
      "format": "parquet_preferred_csv_acceptable_with_schema",
      "no_leak_constraints": [
        "market_data_only",
        "no MT5 account/order/history/deal/position values",
        "no broker outcome labels",
        "no result/cost/R/win-rate/expectancy scoring"
      ],
      "owner_request_id": "OWNER-TICK-0003",
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
      "source_symbol": "GBPJPY",
      "symbol": "GBPJPY",
      "target_hash": "sha256_required_before_consumption",
      "target_path_template": "data/ticks/GBPJPY/2026-04-16.parquet",
      "window_end_utc": "2026-04-16T23:59:59.999999Z",
      "window_start_utc": "2026-04-16T00:00:00Z"
    },
    {
      "candidate_ids": [
        "GBPJPY_2026-04-22T08:00:05.028587+00:00"
      ],
      "format": "parquet_preferred_csv_acceptable_with_schema",
      "no_leak_constraints": [
        "market_data_only",
        "no MT5 account/order/history/deal/position values",
        "no broker outcome labels",
        "no result/cost/R/win-rate/expectancy scoring"
      ],
      "owner_request_id": "OWNER-TICK-0004",
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
      "source_date": "2026-04-22",
      "source_symbol": "GBPJPY",
      "symbol": "GBPJPY",
      "target_hash": "sha256_required_before_consumption",
      "target_path_template": "data/ticks/GBPJPY/2026-04-22.parquet",
      "window_end_utc": "2026-04-22T23:59:59.999999Z",
      "window_start_utc": "2026-04-22T00:00:00Z"
    },
    {
      "candidate_ids": [
        "GBPJPY_2026-04-23T07:16:14.138817+00:00"
      ],
      "format": "parquet_preferred_csv_acceptable_with_schema",
      "no_leak_constraints": [
        "market_data_only",
        "no MT5 account/order/history/deal/position values",
        "no broker outcome labels",
        "no result/cost/R/win-rate/expectancy scoring"
      ],
      "owner_request_id": "OWNER-TICK-0005",
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
      "source_date": "2026-04-23",
      "source_symbol": "GBPJPY",
      "symbol": "GBPJPY",
      "target_hash": "sha256_required_before_consumption",
      "target_path_template": "data/ticks/GBPJPY/2026-04-23.parquet",
      "window_end_utc": "2026-04-23T23:59:59.999999Z",
      "window_start_utc": "2026-04-23T00:00:00Z"
    },
    {
      "candidate_ids": [
        "GBPUSD_2026-04-14T07:30:05.011677+00:00",
        "GBPUSD_2026-04-14T14:00:57.743957+00:00"
      ],
      "format": "parquet_preferred_csv_acceptable_with_schema",
      "no_leak_constraints": [
        "market_data_only",
        "no MT5 account/order/history/deal/position values",
        "no broker outcome labels",
        "no result/cost/R/win-rate/expectancy scoring"
      ],
      "owner_request_id": "OWNER-TICK-0006",
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
      "source_date": "2026-04-14",
      "source_symbol": "GBPUSD",
      "symbol": "GBPUSD",
      "target_hash": "sha256_required_before_consumption",
      "target_path_template": "data/ticks/GBPUSD/2026-04-14.parquet",
      "window_end_utc": "2026-04-14T23:59:59.999999Z",
      "window_start_utc": "2026-04-14T00:00:00Z"
    },
    {
      "candidate_ids": [
        "GBPUSD_2026-04-15T07:30:05.010905+00:00",
        "GBPUSD_2026-04-15T13:16:01.327115+00:00"
      ],
      "format": "parquet_preferred_csv_acceptable_with_schema",
      "no_leak_constraints": [
        "market_data_only",
        "no MT5 account/order/history/deal/position values",
        "no broker outcome labels",
        "no result/cost/R/win-rate/expectancy scoring"
      ],
      "owner_request_id": "OWNER-TICK-0007",
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
      "source_symbol": "GBPUSD",
      "symbol": "GBPUSD",
      "target_hash": "sha256_required_before_consumption",
      "target_path_template": "data/ticks/GBPUSD/2026-04-15.parquet",
      "window_end_utc": "2026-04-15T23:59:59.999999Z",
      "window_start_utc": "2026-04-15T00:00:00Z"
    },
    {
      "candidate_ids": [
        "GBPUSD_2026-04-17T08:00:59.541491+00:00",
        "GBPUSD_2026-04-17T14:15:05.012317+00:00"
      ],
      "format": "parquet_preferred_csv_acceptable_with_schema",
      "no_leak_constraints": [
        "market_data_only",
        "no MT5 account/order/history/deal/position values",
        "no broker outcome labels",
        "no result/cost/R/win-rate/expectancy scoring"
      ],
      "owner_request_id": "OWNER-TICK-0008",
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
      "source_date": "2026-04-17",
      "source_symbol": "GBPUSD",
      "symbol": "GBPUSD",
      "target_hash": "sha256_required_before_consumption",
      "target_path_template": "data/ticks/GBPUSD/2026-04-17.parquet",
      "window_end_utc": "2026-04-17T23:59:59.999999Z",
      "window_start_utc": "2026-04-17T00:00:00Z"
    },
    {
      "candidate_ids": [
        "GBPUSD_2026-04-20T07:45:05.020140+00:00",
        "GBPUSD_2026-04-20T15:31:14.730975+00:00"
      ],
      "format": "parquet_preferred_csv_acceptable_with_schema",
      "no_leak_constraints": [
        "market_data_only",
        "no MT5 account/order/history/deal/position values",
        "no broker outcome labels",
        "no result/cost/R/win-rate/expectancy scoring"
      ],
      "owner_request_id": "OWNER-TICK-0009",
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
      "source_date": "2026-04-20",
      "source_symbol": "GBPUSD",
      "symbol": "GBPUSD",
      "target_hash": "sha256_required_before_consumption",
      "target_path_template": "data/ticks/GBPUSD/2026-04-20.parquet",
      "window_end_utc": "2026-04-20T23:59:59.999999Z",
      "window_start_utc": "2026-04-20T00:00:00Z"
    },
    {
      "candidate_ids": [
        "GBPUSD_2026-04-21T11:30:05.011826+00:00"
      ],
      "format": "parquet_preferred_csv_acceptable_with_schema",
      "no_leak_constraints": [
        "market_data_only",
        "no MT5 account/order/history/deal/position values",
        "no broker outcome labels",
        "no result/cost/R/win-rate/expectancy scoring"
      ],
      "owner_request_id": "OWNER-TICK-0010",
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
      "source_date": "2026-04-21",
      "source_symbol": "GBPUSD",
      "symbol": "GBPUSD",
      "target_hash": "sha256_required_before_consumption",
      "target_path_template": "data/ticks/GBPUSD/2026-04-21.parquet",
      "window_end_utc": "2026-04-21T23:59:59.999999Z",
      "window_start_utc": "2026-04-21T00:00:00Z"
    },
    {
      "candidate_ids": [
        "GBPUSD_2026-04-22T07:16:12.155934+00:00"
      ],
      "format": "parquet_preferred_csv_acceptable_with_schema",
      "no_leak_constraints": [
        "market_data_only",
        "no MT5 account/order/history/deal/position values",
        "no broker outcome labels",
        "no result/cost/R/win-rate/expectancy scoring"
      ],
      "owner_request_id": "OWNER-TICK-0011",
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
      "source_date": "2026-04-22",
      "source_symbol": "GBPUSD",
      "symbol": "GBPUSD",
      "target_hash": "sha256_required_before_consumption",
      "target_path_template": "data/ticks/GBPUSD/2026-04-22.parquet",
      "window_end_utc": "2026-04-22T23:59:59.999999Z",
      "window_start_utc": "2026-04-22T00:00:00Z"
    },
    {
      "candidate_ids": [
        "US30_cash_2026-04-14T08:16:00.983581+00:00"
      ],
      "format": "parquet_preferred_csv_acceptable_with_schema",
      "no_leak_constraints": [
        "market_data_only",
        "no MT5 account/order/history/deal/position values",
        "no broker outcome labels",
        "no result/cost/R/win-rate/expectancy scoring"
      ],
      "owner_request_id": "OWNER-TICK-0012",
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
      "source_date": "2026-04-14",
      "source_symbol": "US30_or_US30_cash_broker_alias",
      "symbol": "US30_cash",
      "target_hash": "sha256_required_before_consumption",
      "target_path_template": "data/ticks/US30_cash/2026-04-14.parquet",
      "window_end_utc": "2026-04-14T23:59:59.999999Z",
      "window_start_utc": "2026-04-14T00:00:00Z"
    },
    {
      "candidate_ids": [
        "US30_cash_2026-04-16T13:45:56.810509+00:00"
      ],
      "format": "parquet_preferred_csv_acceptable_with_schema",
      "no_leak_constraints": [
        "market_data_only",
        "no MT5 account/order/history/deal/position values",
        "no broker outcome labels",
        "no result/cost/R/win-rate/expectancy scoring"
      ],
      "owner_request_id": "OWNER-TICK-0013",
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
      "source_symbol": "US30_or_US30_cash_broker_alias",
      "symbol": "US30_cash",
      "target_hash": "sha256_required_before_consumption",
      "target_path_template": "data/ticks/US30_cash/2026-04-16.parquet",
      "window_end_utc": "2026-04-16T23:59:59.999999Z",
      "window_start_utc": "2026-04-16T00:00:00Z"
    },
    {
      "candidate_ids": [
        "USDJPY_2026-04-15T02:45:05.009485+00:00",
        "USDJPY_2026-04-15T13:15:57.398922+00:00"
      ],
      "format": "parquet_preferred_csv_acceptable_with_schema",
      "no_leak_constraints": [
        "market_data_only",
        "no MT5 account/order/history/deal/position values",
        "no broker outcome labels",
        "no result/cost/R/win-rate/expectancy scoring"
      ],
      "owner_request_id": "OWNER-TICK-0014",
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
      "source_symbol": "USDJPY",
      "symbol": "USDJPY",
      "target_hash": "sha256_required_before_consumption",
      "target_path_template": "data/ticks/USDJPY/2026-04-15.parquet",
      "window_end_utc": "2026-04-15T23:59:59.999999Z",
      "window_start_utc": "2026-04-15T00:00:00Z"
    },
    {
      "candidate_ids": [
        "USDJPY_2026-04-16T15:00:05.011292+00:00"
      ],
      "format": "parquet_preferred_csv_acceptable_with_schema",
      "no_leak_constraints": [
        "market_data_only",
        "no MT5 account/order/history/deal/position values",
        "no broker outcome labels",
        "no result/cost/R/win-rate/expectancy scoring"
      ],
      "owner_request_id": "OWNER-TICK-0015",
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
      "source_symbol": "USDJPY",
      "symbol": "USDJPY",
      "target_hash": "sha256_required_before_consumption",
      "target_path_template": "data/ticks/USDJPY/2026-04-16.parquet",
      "window_end_utc": "2026-04-16T23:59:59.999999Z",
      "window_start_utc": "2026-04-16T00:00:00Z"
    },
    {
      "candidate_ids": [
        "USDJPY_2026-04-21T13:45:05.018194+00:00"
      ],
      "format": "parquet_preferred_csv_acceptable_with_schema",
      "no_leak_constraints": [
        "market_data_only",
        "no MT5 account/order/history/deal/position values",
        "no broker outcome labels",
        "no result/cost/R/win-rate/expectancy scoring"
      ],
      "owner_request_id": "OWNER-TICK-0016",
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
      "source_date": "2026-04-21",
      "source_symbol": "USDJPY",
      "symbol": "USDJPY",
      "target_hash": "sha256_required_before_consumption",
      "target_path_template": "data/ticks/USDJPY/2026-04-21.parquet",
      "window_end_utc": "2026-04-21T23:59:59.999999Z",
      "window_start_utc": "2026-04-21T00:00:00Z"
    },
    {
      "candidate_ids": [
        "USDJPY_2026-04-22T00:30:05.018068+00:00",
        "USDJPY_2026-04-22T15:15:05.016051+00:00"
      ],
      "format": "parquet_preferred_csv_acceptable_with_schema",
      "no_leak_constraints": [
        "market_data_only",
        "no MT5 account/order/history/deal/position values",
        "no broker outcome labels",
        "no result/cost/R/win-rate/expectancy scoring"
      ],
      "owner_request_id": "OWNER-TICK-0017",
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
      "source_date": "2026-04-22",
      "source_symbol": "USDJPY",
      "symbol": "USDJPY",
      "target_hash": "sha256_required_before_consumption",
      "target_path_template": "data/ticks/USDJPY/2026-04-22.parquet",
      "window_end_utc": "2026-04-22T23:59:59.999999Z",
      "window_start_utc": "2026-04-22T00:00:00Z"
    },
    {
      "candidate_ids": [
        "USDJPY_2026-04-23T08:45:05.012266+00:00"
      ],
      "format": "parquet_preferred_csv_acceptable_with_schema",
      "no_leak_constraints": [
        "market_data_only",
        "no MT5 account/order/history/deal/position values",
        "no broker outcome labels",
        "no result/cost/R/win-rate/expectancy scoring"
      ],
      "owner_request_id": "OWNER-TICK-0018",
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
      "source_date": "2026-04-23",
      "source_symbol": "USDJPY",
      "symbol": "USDJPY",
      "target_hash": "sha256_required_before_consumption",
      "target_path_template": "data/ticks/USDJPY/2026-04-23.parquet",
      "window_end_utc": "2026-04-23T23:59:59.999999Z",
      "window_start_utc": "2026-04-23T00:00:00Z"
    },
    {
      "candidate_ids": [
        "USDJPY_2026-04-24T00:16:10.771453+00:00"
      ],
      "format": "parquet_preferred_csv_acceptable_with_schema",
      "no_leak_constraints": [
        "market_data_only",
        "no MT5 account/order/history/deal/position values",
        "no broker outcome labels",
        "no result/cost/R/win-rate/expectancy scoring"
      ],
      "owner_request_id": "OWNER-TICK-0019",
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
      "source_date": "2026-04-24",
      "source_symbol": "USDJPY",
      "symbol": "USDJPY",
      "target_hash": "sha256_required_before_consumption",
      "target_path_template": "data/ticks/USDJPY/2026-04-24.parquet",
      "window_end_utc": "2026-04-24T23:59:59.999999Z",
      "window_start_utc": "2026-04-24T00:00:00Z"
    },
    {
      "candidate_ids": [
        "XAUUSD_2026-04-15T14:15:05.007998+00:00"
      ],
      "format": "parquet_preferred_csv_acceptable_with_schema",
      "no_leak_constraints": [
        "market_data_only",
        "no MT5 account/order/history/deal/position values",
        "no broker outcome labels",
        "no result/cost/R/win-rate/expectancy scoring"
      ],
      "owner_request_id": "OWNER-TICK-0020",
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
      "target_hash": "sha256_required_before_consumption",
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
      "no_leak_constraints": [
        "market_data_only",
        "no MT5 account/order/history/deal/position values",
        "no broker outcome labels",
        "no result/cost/R/win-rate/expectancy scoring"
      ],
      "owner_request_id": "OWNER-TICK-0021",
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
      "target_hash": "sha256_required_before_consumption",
      "target_path_template": "data/ticks/XAUUSD/2026-04-16.parquet",
      "window_end_utc": "2026-04-16T23:59:59.999999Z",
      "window_start_utc": "2026-04-16T00:00:00Z"
    },
    {
      "candidate_ids": [
        "XAUUSD_2026-04-17T13:30:05.007149+00:00"
      ],
      "format": "parquet_preferred_csv_acceptable_with_schema",
      "no_leak_constraints": [
        "market_data_only",
        "no MT5 account/order/history/deal/position values",
        "no broker outcome labels",
        "no result/cost/R/win-rate/expectancy scoring"
      ],
      "owner_request_id": "OWNER-TICK-0022",
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
      "source_date": "2026-04-17",
      "source_symbol": "XAUUSD",
      "symbol": "XAUUSD",
      "target_hash": "sha256_required_before_consumption",
      "target_path_template": "data/ticks/XAUUSD/2026-04-17.parquet",
      "window_end_utc": "2026-04-17T23:59:59.999999Z",
      "window_start_utc": "2026-04-17T00:00:00Z"
    }
  ],
  "unique_tick_export_request_count": 22,
  "validation_safe": false
}
```
