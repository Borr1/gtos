# Source Hash Header Coverage Reaudit

```json
{
  "artifact_family": "source_hash_header_coverage_reaudit",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "day_counts_match_expected": true,
  "day_coverage": [
    {
      "coverage_status": "SCID_ROWS_PRESENT",
      "first_record": {
        "ask_volume": 28,
        "bid_volume": 38,
        "close": 4837.52001953125,
        "high": 4837.669921875,
        "index": 8519586,
        "low": 4837.08984375,
        "num_trades": 66,
        "open": 4837.43994140625,
        "record_status_anomalies": [],
        "sierra_datetime_us": 3985372800016000,
        "timestamp_utc": "2026-04-15T00:00:00.016000Z",
        "total_volume": 66
      },
      "last_record": {
        "ask_volume": 1,
        "bid_volume": 2,
        "close": 4823.599609375,
        "high": 4823.6396484375,
        "index": 8591704,
        "low": 4823.599609375,
        "num_trades": 3,
        "open": 4823.6298828125,
        "record_status_anomalies": [],
        "sierra_datetime_us": 3985459199140000,
        "timestamp_utc": "2026-04-15T23:59:59.140000Z",
        "total_volume": 3
      },
      "max_close": 4870.91015625,
      "min_close": 4786.7998046875,
      "record_status_anomaly_counts": {},
      "row_count": 72119,
      "source_date": "2026-04-15",
      "timestamp_resolution": {
        "duplicate_timestamp_count": 0,
        "max_gap_seconds": 3661.002,
        "median_positive_delta_us": 1013000,
        "min_positive_delta_us": 1000,
        "non_monotonic_timestamp_count": 0
      },
      "volume_totals": {
        "ask_volume": 462143,
        "bid_volume": 459487,
        "num_trades": 921630,
        "total_volume": 921630
      },
      "window_end_utc": "2026-04-15T23:59:59.999999Z",
      "window_start_utc": "2026-04-15T00:00:00Z"
    },
    {
      "coverage_status": "SCID_ROWS_PRESENT",
      "first_record": {
        "ask_volume": 27,
        "bid_volume": 11,
        "close": 4824.1201171875,
        "high": 4824.14013671875,
        "index": 8591705,
        "low": 4823.4697265625,
        "num_trades": 38,
        "open": 4823.6103515625,
        "record_status_anomalies": [],
        "sierra_datetime_us": 3985459200016000,
        "timestamp_utc": "2026-04-16T00:00:00.016000Z",
        "total_volume": 38
      },
      "last_record": {
        "ask_volume": 1,
        "bid_volume": 8,
        "close": 4791.52001953125,
        "high": 4792.1650390625,
        "index": 8661752,
        "low": 4791.52001953125,
        "num_trades": 9,
        "open": 4791.97998046875,
        "record_status_anomalies": [],
        "sierra_datetime_us": 3985545599793000,
        "timestamp_utc": "2026-04-16T23:59:59.793000Z",
        "total_volume": 9
      },
      "max_close": 4838.580078125,
      "min_close": 4773.400390625,
      "record_status_anomaly_counts": {},
      "row_count": 70048,
      "source_date": "2026-04-16",
      "timestamp_resolution": {
        "duplicate_timestamp_count": 0,
        "max_gap_seconds": 3661.029,
        "median_positive_delta_us": 1015000,
        "min_positive_delta_us": 2000,
        "non_monotonic_timestamp_count": 0
      },
      "volume_totals": {
        "ask_volume": 436154,
        "bid_volume": 437162,
        "num_trades": 873316,
        "total_volume": 873316
      },
      "window_end_utc": "2026-04-16T23:59:59.999999Z",
      "window_start_utc": "2026-04-16T00:00:00Z"
    }
  ],
  "first_file_record": {
    "ask_volume": 12,
    "bid_volume": 7,
    "close": 3939.760009765625,
    "high": 3939.760009765625,
    "index": 0,
    "low": 3939.530029296875,
    "num_trades": 19,
    "open": 3939.530029296875,
    "record_status_anomalies": [],
    "sierra_datetime_us": 3970822749044000,
    "timestamp_utc": "2025-10-28T14:19:09.044000Z",
    "total_volume": 19
  },
  "generated_at_utc": "2026-05-10T11:13:20Z",
  "last_file_record": {
    "ask_volume": 0,
    "bid_volume": 1,
    "close": 4613.740234375,
    "high": 4614.18994140625,
    "index": 9463560,
    "low": 4613.2900390625,
    "num_trades": 1,
    "open": 0.0,
    "record_status_anomalies": [
      "INVALID_OR_SPECIAL_PRICE_FIELD"
    ],
    "sierra_datetime_us": 3986829898881000,
    "timestamp_utc": "2026-05-01T20:44:58.881000Z",
    "total_volume": 1
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
  "parser_code_hashes": {
    "g12_audit_builder_sha256": "acfea9f546ac3beee672a344ef0677ace49fa8d1cd59622f95f221113ed34c44",
    "scripts_inspect_sierra_scid_sha256": "e439e1975c0e4ca43c57b373fe5ede167f5b0dc59a0bb32eff7236752c0d23d9",
    "target_route_builder_sha256": "97f706b611aaf7750c2dad8977bd849b29aafcaea3375b4e54ce7ac1777bfac6"
  },
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "raw_source": {
    "expected_source_sha256": "c10de3e8863cf6a9240abefa3f6293b86cae97835acd96d71d202ef6d40f494b",
    "raw_source_not_committed": true,
    "raw_source_not_copied": true,
    "size_bytes": 378542496,
    "source_path": "C:\\SierraChart\\Data\\XAUUSD.scid",
    "source_sha256": "c10de3e8863cf6a9240abefa3f6293b86cae97835acd96d71d202ef6d40f494b",
    "source_sha256_matches_expected": true
  },
  "route_id": "G12_XAUUSD_2026_04_15_16_SIERRA_SCID_ALTERNATE_SOURCE_CONTROL_AUDIT",
  "schema_version": "g12_xauusd_2026_04_15_16_sierra_scid_alternate_source_control_audit_v1",
  "scid_header": {
    "exists": true,
    "header_size": 56,
    "magic": "SCID",
    "path": "C:\\SierraChart\\Data\\XAUUSD.scid",
    "record_count": 9463561,
    "record_size": 40,
    "remainder_bytes": 0,
    "size_bytes": 378542496,
    "utc_start_index": 0,
    "version": 1
  },
  "scid_header_validation_issues": [],
  "source_access_status": "SCID_REHASHED_AND_HEADER_REPARSED_READ_ONLY",
  "target_route_comparison": {
    "comparison_status": "MATCH",
    "mismatches": [],
    "target_day_candidate_coverage_artifact": "research/science_program_2026_05/06_outcome_testing/xauusd_2026_04_15_16_sierra_scid_alternate_source_control_route/XAUUSD_SIERRA_SCID_ALT_ROUTE_SCID_DAY_CANDIDATE_COVERAGE_LEDGER_2026-05-10.json",
    "target_source_hash_header_artifact": "research/science_program_2026_05/06_outcome_testing/xauusd_2026_04_15_16_sierra_scid_alternate_source_control_route/XAUUSD_SIERRA_SCID_ALT_ROUTE_SCID_SOURCE_HASH_HEADER_AUDIT_2026-05-10.json"
  },
  "target_route_id": "XAUUSD_2026_04_15_16_SIERRA_SCID_ALTERNATE_SOURCE_CONTROL_ROUTE",
  "validation_safe": false
}
```
