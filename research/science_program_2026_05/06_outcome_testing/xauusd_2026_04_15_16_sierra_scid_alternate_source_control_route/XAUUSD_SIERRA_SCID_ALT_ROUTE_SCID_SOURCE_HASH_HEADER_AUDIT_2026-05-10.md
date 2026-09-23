# SCID Source Hash Header Audit

Route: `XAUUSD_2026_04_15_16_SIERRA_SCID_ALTERNATE_SOURCE_CONTROL_ROUTE`
Terminal posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

```json
{
  "artifact_family": "scid_source_hash_header_audit",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
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
  "generated_at_utc": "2026-05-10T10:47:39Z",
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
    "existing_convert_sierra_scid_to_ohlcv_sha256": "de7c109e6998e9f50051c377c37a71c0a68e7283d133b2ff2e446c6ca82714a6",
    "existing_inspect_sierra_scid_sha256": "e439e1975c0e4ca43c57b373fe5ede167f5b0dc59a0bb32eff7236752c0d23d9",
    "route_builder_sha256": "01ca9d48055f07346b736be89c88d1478cd99caf756d14a258a24ac342146c84"
  },
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "raw_source": {
    "hash_algorithm": "SHA256",
    "raw_source_not_committed": true,
    "raw_source_not_copied": true,
    "size_bytes": 378542496,
    "source_path": "C:\\SierraChart\\Data\\XAUUSD.scid",
    "source_sha256": "c10de3e8863cf6a9240abefa3f6293b86cae97835acd96d71d202ef6d40f494b"
  },
  "route_id": "XAUUSD_2026_04_15_16_SIERRA_SCID_ALTERNATE_SOURCE_CONTROL_ROUTE",
  "schema_version": "xauusd_2026_04_15_16_sierra_scid_alternate_source_control_route_v1",
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
  "source_access_status": "SOURCE_HASHED_AND_HEADER_PARSED",
  "source_location_search": {
    "exact_source_exists": true,
    "required_source_path": "C:\\SierraChart\\Data\\XAUUSD.scid",
    "search_rows": [
      {
        "exists": true,
        "match_count": 1,
        "matches": [
          "C:\\SierraChart\\Data\\XAUUSD.scid"
        ],
        "root_id": "exact_required_path",
        "root_path": "C:\\SierraChart\\Data\\XAUUSD.scid",
        "search_policy": "exact_required_source_path_first"
      }
    ],
    "selected_source_path": "C:\\SierraChart\\Data\\XAUUSD.scid",
    "source_access_status": "EXACT_SOURCE_READABLE"
  },
  "validation_safe": false
}
```
