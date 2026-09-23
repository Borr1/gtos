# SCID As-Of Bar Derivation Contract

- Route: `SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AND_CANDIDATE_GENERATOR_CONSTRAINT`
- Evidence class: `SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AND_CANDIDATE_GENERATOR_CONSTRAINT_ONLY`
- Promotion verdict: `NO_PROMOTION_VERDICT`
- validation_safe: `False`
- outcome_review_opened: `False`
- live_effect: `False`

## Summary

```json
{
  "interval_policy": "left_closed_right_open",
  "parser": "<QffffIIII",
  "segment_reference_count": 9,
  "validation_safe": false
}
```

## Payload

```json
{
  "artifact_family": "bar_derivation_contract",
  "bar_derivation_rules": {
    "accepted_bar_intervals": [
      "M1",
      "M5",
      "M15",
      "H1",
      "H4"
    ],
    "bar_identity_fields": [
      "source_manifest_ref",
      "segment_records_sha256",
      "source_file_name",
      "symbol",
      "canonical_economic_group",
      "interval",
      "bar_start_utc",
      "bar_end_exclusive_utc",
      "source_record_start_index",
      "source_record_end_index"
    ],
    "default_interval_for_future_candidate_inputs": "M15 unless a future packet explicitly freezes another interval",
    "duplicate_timestamp_policy": {
      "exact_duplicate_values": "do not drop inside the source-control contract; future data-quality lane may flag but not alter without G12 approval",
      "same_millisecond_records": "retain raw source_timestamp_us for order; timestamp_utc_ms alone is not a tie key",
      "same_timestamp_records": "retain all records and aggregate in source_record_index order"
    },
    "empty_bar_policy": {
      "default_output": "sparse bars only; absence of records means no bar row unless dense continuity is explicitly requested",
      "dense_output_if_requested": {
        "ask_volume": 0,
        "bar_status": "EMPTY_NO_SOURCE_RECORDS",
        "bid_volume": 0,
        "candidate_eligible": false,
        "close": null,
        "high": null,
        "low": null,
        "num_trades": 0,
        "open": null,
        "total_volume": 0
      },
      "forbidden": "no forward-fill, backward-fill, midpoint-fill, session-average fill, or inferred OHLC"
    },
    "gap_session_policy": {
      "no_records_inside_calendar_open": "emit DATA_GAP_NO_SOURCE_RECORDS if dense output requested; candidate_eligible=false",
      "session_calendar_source": "future packet must freeze calendar/KZ definitions by value and hash; live config reads are forbidden",
      "session_closed_or_holiday": "emit SESSION_CLOSED_NO_MARKET_DATA if a frozen calendar proves closure; candidate_eligible=false",
      "unknown_calendar": "do not infer closure; mark SESSION_STATUS_UNKNOWN and fail closed for candidate eligibility if continuity is required"
    },
    "ohlcv_semantics": {
      "ask_volume": "sum ask_volume",
      "bid_volume": "sum bid_volume",
      "close": "close of last sorted source record in the interval",
      "high": "max high across sorted source records in the interval",
      "low": "min low across sorted source records in the interval",
      "num_trades": "sum num_trades",
      "open": "open of first sorted source record in the interval",
      "source_record_count": "count source records in interval",
      "total_volume": "sum total_volume"
    },
    "record_order_policy": "stable sort by (source_timestamp_us, source_record_index) after scanning the frozen segment",
    "record_scan_scope": "scan only segment_byte_start through segment_byte_end_exclusive from accepted manifest"
  },
  "changes_live_trading_behavior": false,
  "contract_decision": "FREEZE_CONTRACT_ONLY_G12_AUDIT_REQUIRED_BEFORE_BUILDER_USE",
  "credentials_touched": false,
  "evidence_class": "SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AND_CANDIDATE_GENERATOR_CONSTRAINT_ONLY",
  "forbidden_outputs": [
    "candidate rows for validation",
    "path-label rows",
    "result rows",
    "R/PnL/win-rate/expectancy/performance rows",
    "broker/account/order/deal/position fields",
    "cost/slippage scoring fields"
  ],
  "generated_at_utc": "2026-05-11T11:51:25Z",
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
  "parser_contract": {
    "accepted_record_identity": [
      "source_manifest_ref",
      "segment_records_sha256",
      "segment_byte_start",
      "segment_byte_end_exclusive",
      "source_record_index",
      "source_timestamp_us"
    ],
    "binary_header": {
      "byte_order": "little_endian",
      "expected_header_size_bytes": 56,
      "expected_magic": "SCID",
      "fields": [
        {
          "name": "magic",
          "required_value": "SCID",
          "type": "char[4]"
        },
        {
          "name": "header_size",
          "required_value": 56,
          "type": "uint32"
        },
        {
          "name": "record_size",
          "required_value": 40,
          "type": "uint32"
        },
        {
          "accepted_values": [
            1
          ],
          "name": "version",
          "type": "uint16"
        },
        {
          "accepted_values": [
            0
          ],
          "name": "utc_start_index",
          "type": "uint16"
        },
        {
          "accepted_values": [
            0
          ],
          "name": "unused",
          "type": "uint32"
        },
        {
          "name": "reserve",
          "policy": "hashed_as_header_bytes_not_interpreted",
          "type": "bytes[36]"
        }
      ],
      "struct": "<4sIIHHI36s"
    },
    "binary_record": {
      "fields": [
        {
          "name": "source_timestamp_us",
          "semantic": "Sierra DateTime microseconds",
          "type": "uint64"
        },
        {
          "name": "open",
          "semantic": "source record open price",
          "type": "float32"
        },
        {
          "name": "high",
          "semantic": "source record high price",
          "type": "float32"
        },
        {
          "name": "low",
          "semantic": "source record low price",
          "type": "float32"
        },
        {
          "name": "close",
          "semantic": "source record close price",
          "type": "float32"
        },
        {
          "name": "num_trades",
          "semantic": "source record trade count",
          "type": "uint32"
        },
        {
          "name": "total_volume",
          "semantic": "source record total volume",
          "type": "uint32"
        },
        {
          "name": "bid_volume",
          "semantic": "source record bid volume",
          "type": "uint32"
        },
        {
          "name": "ask_volume",
          "semantic": "source record ask volume",
          "type": "uint32"
        }
      ],
      "record_size_bytes": 40,
      "struct": "<QffffIIII"
    },
    "contract_status": "FROZEN_FOR_NEXT_G12_AUDIT_NOT_VALIDATION",
    "parser_fail_closed_rules": [
      "bad magic rejects source packet",
      "header_size not 56 rejects source packet",
      "record_size not 40 rejects source packet",
      "partial record remainder rejects source packet",
      "segment byte boundaries not record-aligned reject source packet",
      "segment raw-byte rehash mismatch rejects source packet"
    ]
  },
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "route_id": "SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AND_CANDIDATE_GENERATOR_CONSTRAINT",
  "schema_version": "scid_to_asof_bar_contract_v1",
  "source_inputs": [
    {
      "append_safety_rule": "hash only frozen record byte range; later EOF growth is outside segment_byte_end_exclusive",
      "eligible_segment_start_utc_hard_floor": "2026-05-01T20:59:01Z",
      "g12_rehash_audit_ref": "research/science_program_2026_05/06_outcome_testing/g12_fpb_sealed_source_pool_immutable_scid_hash_freeze_repair_reaudit/G12_FPB_SCID_FREEZE_REPAIR_REAUDIT_SOURCE_REHASH_AUDIT_2026-05-11.json",
      "raw_blob_committed": false,
      "rehash_matches": true,
      "segment_byte_end_exclusive": 61576176,
      "segment_byte_start": 54786536,
      "segment_descriptor_sha256": "78109494711d8ee2de98c7d0f411733c73f07af6bd2cd1a20006a3d1e26dab0a",
      "segment_first_record_utc": "2026-05-01T20:59:41Z",
      "segment_last_record_utc": "2026-05-11T10:12:19Z",
      "segment_record_count": 169741,
      "segment_record_end_index_inclusive": 1539402,
      "segment_record_start_index": 1369662,
      "segment_records_sha256": "91ae9eb8ca0493cd301ae7dd3be2c08d2f8529473ac049206187f3b805e2a263",
      "source_access_status": "OK",
      "source_file_name": "6BM26-CME.scid",
      "source_input_status": "G12_ACCEPTED_BOUNDED_SEGMENT_REFERENCE_ONLY",
      "source_manifest_ref": "research/science_program_2026_05/06_outcome_testing/fpb_sealed_source_pool_immutable_scid_hash_freeze_repair/FPB_SCID_FREEZE_REPAIR_SNAPSHOT_SEGMENT_MANIFEST_2026-05-11.json",
      "source_path_reference_only": "C:\\SierraChart\\Data\\6BM26-CME.scid",
      "symbol": "GBPUSD_6B",
      "timestamp_monotonic_non_decreasing": false,
      "timestamp_monotonicity_policy": "diagnostic_only_for_source_acceptance; future as-of bar derivation scans the frozen segment and stable-sorts records by (source_timestamp_us, source_record_index) before aggregation",
      "validation_safe": false
    },
    {
      "append_safety_rule": "hash only frozen record byte range; later EOF growth is outside segment_byte_end_exclusive",
      "eligible_segment_start_utc_hard_floor": "2026-05-08T23:45:01Z",
      "g12_rehash_audit_ref": "research/science_program_2026_05/06_outcome_testing/g12_fpb_sealed_source_pool_immutable_scid_hash_freeze_repair_reaudit/G12_FPB_SCID_FREEZE_REPAIR_REAUDIT_SOURCE_REHASH_AUDIT_2026-05-11.json",
      "raw_blob_committed": false,
      "rehash_matches": true,
      "segment_byte_end_exclusive": 155726296,
      "segment_byte_start": 154981376,
      "segment_descriptor_sha256": "e7f997ce783fd0ea15e0d48a0fb74b756698a8ea2b4b243ea8f56d1c8f4a2783",
      "segment_first_record_utc": "2026-05-10T22:00:00Z",
      "segment_last_record_utc": "2026-05-11T10:12:19Z",
      "segment_record_count": 18623,
      "segment_record_end_index_inclusive": 3893155,
      "segment_record_start_index": 3874533,
      "segment_records_sha256": "3e755a319b4f895c27203d63fd7ddb310b81066384f93f007943bddc94ca2053",
      "source_access_status": "OK",
      "source_file_name": "6EM26-CME.scid",
      "source_input_status": "G12_ACCEPTED_BOUNDED_SEGMENT_REFERENCE_ONLY",
      "source_manifest_ref": "research/science_program_2026_05/06_outcome_testing/fpb_sealed_source_pool_immutable_scid_hash_freeze_repair/FPB_SCID_FREEZE_REPAIR_SNAPSHOT_SEGMENT_MANIFEST_2026-05-11.json",
      "source_path_reference_only": "C:\\SierraChart\\Data\\6EM26-CME.scid",
      "symbol": "EURUSD",
      "timestamp_monotonic_non_decreasing": true,
      "timestamp_monotonicity_policy": "diagnostic_only_for_source_acceptance; future as-of bar derivation scans the frozen segment and stable-sorts records by (source_timestamp_us, source_record_index) before aggregation",
      "validation_safe": false
    },
    {
      "append_safety_rule": "hash only frozen record byte range; later EOF growth is outside segment_byte_end_exclusive",
      "eligible_segment_start_utc_hard_floor": "2026-05-01T20:59:01Z",
      "g12_rehash_audit_ref": "research/science_program_2026_05/06_outcome_testing/g12_fpb_sealed_source_pool_immutable_scid_hash_freeze_repair_reaudit/G12_FPB_SCID_FREEZE_REPAIR_REAUDIT_SOURCE_REHASH_AUDIT_2026-05-11.json",
      "raw_blob_committed": false,
      "rehash_matches": true,
      "segment_byte_end_exclusive": 119363656,
      "segment_byte_start": 102820496,
      "segment_descriptor_sha256": "cb1e18f67e507ccc4b37a362e2ac730c975c9847ef714eaf325ae95ee0b6ac09",
      "segment_first_record_utc": "2026-05-01T20:59:15Z",
      "segment_last_record_utc": "2026-05-11T10:12:12Z",
      "segment_record_count": 413579,
      "segment_record_end_index_inclusive": 2984089,
      "segment_record_start_index": 2570511,
      "segment_records_sha256": "c7bcc874ee594d78d51c1637c249372b59cf6e16194fb67fdea446a33b3832eb",
      "source_access_status": "OK",
      "source_file_name": "6JM26-CME.scid",
      "source_input_status": "G12_ACCEPTED_BOUNDED_SEGMENT_REFERENCE_ONLY",
      "source_manifest_ref": "research/scienc
... truncated in markdown; see matching JSON artifact ...
```
