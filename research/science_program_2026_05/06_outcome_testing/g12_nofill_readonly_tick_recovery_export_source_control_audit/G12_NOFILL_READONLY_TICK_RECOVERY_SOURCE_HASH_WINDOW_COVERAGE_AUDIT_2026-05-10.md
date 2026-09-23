# G12 NOFILL Readonly Tick Recovery Source Hash Window Coverage Audit

Route: `G12_NOFILL_READONLY_TICK_RECOVERY_EXPORT_SOURCE_CONTROL_AUDIT`
Terminal decision: `ACCEPT_AS_G12_READONLY_TICK_RECOVERY_SOURCE_CONTROL_AUDIT_WITH_NONPASSIVE_NEXT_ROUTE`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

```json
{
  "all_recovered_sources_pass": true,
  "artifact_family": "source_hash_window_coverage_audit",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "generated_at_utc": "2026-05-10T10:17:17Z",
  "hash_mismatch_count": 0,
  "live_effect": false,
  "manifest_only_source_file_count": 0,
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
  "recovered_source_file_count": 20,
  "rehashed_local_source_file_count": 20,
  "route_id": "G12_NOFILL_READONLY_TICK_RECOVERY_EXPORT_SOURCE_CONTROL_AUDIT",
  "rows": [
    {
      "actual_broker_symbol_values": [
        "GBPJPY"
      ],
      "actual_in_requested_window_row_count": 222024,
      "actual_max_timestamp_utc": "2026-04-14T23:59:58.740000Z",
      "actual_min_timestamp_utc": "2026-04-14T00:00:02.941000Z",
      "actual_required_field_missing": [],
      "actual_row_count": 222024,
      "actual_sha256": "5bd866e1fc74b8d2f3c0f1e8ba53ffef2d1a399e07c19f1acd970e1c1fe0a4e2",
      "actual_size_bytes": 3691827,
      "actual_source_symbol_values": [
        "GBPJPY"
      ],
      "actual_symbol_alias_compatible": true,
      "audit_status": "PASS",
      "candidate_ids": [
        "GBPJPY_2026-04-14T01:15:05.006410+00:00",
        "GBPJPY_2026-04-14T15:30:05.012815+00:00"
      ],
      "candidate_window_checks": [
        {
          "candidate_id": "GBPJPY_2026-04-14T01:15:05.006410+00:00",
          "candidate_utc": "2026-04-14T01:15:05.006410Z",
          "inside_actual_file_span": true,
          "inside_requested_utc_window": true
        },
        {
          "candidate_id": "GBPJPY_2026-04-14T15:30:05.012815+00:00",
          "candidate_utc": "2026-04-14T15:30:05.012815Z",
          "inside_actual_file_span": true,
          "inside_requested_utc_window": true
        }
      ],
      "exists_in_active_worktree": true,
      "field_availability_manifest": {
        "ask": true,
        "bid": true,
        "broker_symbol": true,
        "flags": true,
        "last": true,
        "source_symbol": true,
        "time_msc": true,
        "time_utc": true,
        "volume": true
      },
      "manifest_max_timestamp_utc": "2026-04-14T23:59:58.740000Z",
      "manifest_min_timestamp_utc": "2026-04-14T00:00:02.941000Z",
      "manifest_row_count": 222024,
      "manifest_sha256": "5bd866e1fc74b8d2f3c0f1e8ba53ffef2d1a399e07c19f1acd970e1c1fe0a4e2",
      "manifest_size_bytes": 3691827,
      "max_timestamp_matches_manifest": true,
      "min_timestamp_matches_manifest": true,
      "owner_request_id": "OWNER-TICK-0001",
      "parquet_schema_fields": [
        "time_utc",
        "time",
        "time_msc",
        "bid",
        "ask",
        "last",
        "volume",
        "flags",
        "volume_real",
        "source_symbol",
        "broker_symbol"
      ],
      "rehash_status": "REHASHED_LOCAL_SOURCE_FILE",
      "requested_window_end_utc": "2026-04-14T23:59:59.999999Z",
      "requested_window_start_utc": "2026-04-14T00:00:00Z",
      "row_count_matches_manifest": true,
      "sha256_matches_manifest": true,
      "size_matches_manifest": true,
      "source_date": "2026-04-14",
      "source_path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/GBPJPY/2026-04-14.parquet",
      "symbol": "GBPJPY",
      "symbol_compatibility": {
        "broker_symbol": "GBPJPY",
        "requested_symbol": "GBPJPY",
        "status": "exact_symbol_match"
      },
      "terminal_status": "RECOVERED_READONLY_MT5_SOURCE_HASHED",
      "window_coverage_status": "PASS_REHASHED_SOURCE_COVERS_REQUESTED_UTC_WINDOW_AND_CANDIDATES"
    },
    {
      "actual_broker_symbol_values": [
        "GBPJPY"
      ],
      "actual_in_requested_window_row_count": 239538,
      "actual_max_timestamp_utc": "2026-04-15T23:59:58.060000Z",
      "actual_min_timestamp_utc": "2026-04-15T00:00:03.841000Z",
      "actual_required_field_missing": [],
      "actual_row_count": 239538,
      "actual_sha256": "183795c2900e538726a1ea2fbad4146cd200591dbc572bf3f9853df6e456e66d",
      "actual_size_bytes": 3923919,
      "actual_source_symbol_values": [
        "GBPJPY"
      ],
      "actual_symbol_alias_compatible": true,
      "audit_status": "PASS",
      "candidate_ids": [
        "GBPJPY_2026-04-15T00:30:05.011237+00:00",
        "GBPJPY_2026-04-15T13:15:57.164919+00:00"
      ],
      "candidate_window_checks": [
        {
          "candidate_id": "GBPJPY_2026-04-15T00:30:05.011237+00:00",
          "candidate_utc": "2026-04-15T00:30:05.011237Z",
          "inside_actual_file_span": true,
          "inside_requested_utc_window": true
        },
        {
          "candidate_id": "GBPJPY_2026-04-15T13:15:57.164919+00:00",
          "candidate_utc": "2026-04-15T13:15:57.164919Z",
          "inside_actual_file_span": true,
          "inside_requested_utc_window": true
        }
      ],
      "exists_in_active_worktree": true,
      "field_availability_manifest": {
        "ask": true,
        "bid": true,
        "broker_symbol": true,
        "flags": true,
        "last": true,
        "source_symbol": true,
        "time_msc": true,
        "time_utc": true,
        "volume": true
      },
      "manifest_max_timestamp_utc": "2026-04-15T23:59:58.060000Z",
      "manifest_min_timestamp_utc": "2026-04-15T00:00:03.841000Z",
      "manifest_row_count": 239538,
      "manifest_sha256": "183795c2900e538726a1ea2fbad4146cd200591dbc572bf3f9853df6e456e66d",
      "manifest_size_bytes": 3923919,
      "max_timestamp_matches_manifest": true,
      "min_timestamp_matches_manifest": true,
      "owner_request_id": "OWNER-TICK-0002",
      "parquet_schema_fields": [
        "time_utc",
        "time",
        "time_msc",
        "bid",
        "ask",
        "last",
        "volume",
        "flags",
        "volume_real",
        "source_symbol",
        "broker_symbol"
      ],
      "rehash_status": "REHASHED_LOCAL_SOURCE_FILE",
      "requested_window_end_utc": "2026-04-15T23:59:59.999999Z",
      "requested_window_start_utc": "2026-04-15T00:00:00Z",
      "row_count_matches_manifest": true,
      "sha256_matches_manifest": true,
      "size_matches_manifest": true,
      "source_date": "2026-04-15",
      "source_path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/GBPJPY/2026-04-15.parquet",
      "symbol": "GBPJPY",
      "symbol_compatibility": {
        "broker_symbol": "GBPJPY",
        "requested_symbol": "GBPJPY",
        "status": "exact_symbol_match"
      },
      "terminal_status": "RECOVERED_READONLY_MT5_SOURCE_HASHED",
      "window_coverage_status": "PASS_REHASHED_SOURCE_COVERS_REQUESTED_UTC_WINDOW_AND_CANDIDATES"
    },
    {
      "actual_broker_symbol_values": [
        "GBPJPY"
      ],
      "actual_in_requested_window_row_count": 236959,
      "actual_max_timestamp_utc": "2026-04-16T23:59:58.496000Z",
      "actual_min_timestamp_utc": "2026-04-16T00:00:01.347000Z",
      "actual_required_field_missing": [],
      "actual_row_count": 236959,
      "actual_sha256": "19152faa2713eff446d6ced13694c1ba206e6035496480237b4dbf2708f727f7",
      "actual_size_bytes": 3851820,
      "actual_source_symbol_values": [
        "GBPJPY"
      ],
      "actual_symbol_alias_compatible": true,
      "audit_status": "PASS",
      "candidate_ids": [
        "GBPJPY_2026-04-16T00:16:00.503237+00:00"
      ],
      "candidate_window_checks": [
        {
          "candidate_id": "GBPJPY_2026-04-16T00:16:00.503237+00:00",
          "candidate_utc": "2026-04-16T00:16:00.503237Z",
          "inside_actual_file_span": true,
          "inside_requested_utc_window": true
        }
      ],
      "exists_in_active_worktree": true,
      "field_availability_manifest": {
        "ask": true,
        "bid": true,
        "broker_symbol": true,
        "flags": true,
        "last": true,
        "source_symbol": true,
        "time_msc": true,
        "time_utc": true,
        "volume": true
      },
      "manifest_max_timestamp_utc": "2026-04-16T23:59:58.496000Z",
      "manifest_min_timestamp_utc": "2026-04-16T00:00:01.347000Z",
      "manifest_row_count": 236959,
      "manifest_sha256": "19152faa2713eff446d6ced13694c1ba206e6035496480237b4dbf2708f727f7",
      "manifest_size_bytes": 3851820,
      "max_timestamp_matches_manifest": true,
      "min_timestamp_matches_manifest": true,
      "owner_request_id": "OWNER-TICK-0003",
      "parquet_schema_fields": [
        "time_utc",
        "time",
        "time_msc",
        "bid",
        "ask",
        "last",
        "volume",
        "flags",
        "volume_real",
        "source_symbol",
        "broker_symbol"
      ],
      "rehash_status": "REHASHED_LOCAL_SOURCE_FILE",
      "requested_window_end_utc": "2026-04-16T23:59:59.999999Z",
      "requested_window_start_utc": "2026-04-16T00:00:00Z",
      "row_count_matches_manifest": true,
      "sha256_matches_manifest": true,
      "size_matches_manifest": true,
      "source_date": "2026-04-16",
      "source_path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/GBPJPY/2026-04-16.parquet",
      "symbol": "GBPJPY",
      "symbol_compatibility": {
        "broker_symbol": "GBPJPY",
        "requested_symbol": "GBPJPY",
        "status": "exact_symbol_match"
      },
      "terminal_status": "RECOVERED_READONLY_MT5_SOURCE_HASHED",
      "window_coverage_status": "PASS_REHASHED_SOURCE_COVERS_REQUESTED_UTC_WINDOW_AND_CANDIDATES"
    },
    {
      "actual_broker_symbol_values": [
        "GBPJPY"
      ],
      "actual_in_requested_window_row_count": 250615,
      "actual_max_timestamp_utc": "2026-04-22T23:59:58.514000Z",
      "actual_min_timestamp_utc": "2026-04-22T00:00:09.411000Z",
      "actual_required_field_missing": [],
      "actual_row_count": 250615,
      "actual_sha256": "69080040b37c652eefec2ffded50239c0cb608225eab23029d23f94b3fc2b379",
      "actual_size_bytes": 4019231,
      "actual_source_symbol_values": [
        "GBPJPY"
      ],
      "actual_symbol_alias_compatible": true,
      "audit_status": "PASS",
      "candidate_ids": [
        "GBPJPY_2026-04-22T08:00:05.028587+00:00"
      ],
      "candidate_window_checks": [
        {
          "candidate_id": "GBPJPY_2026-04-22T08:00:05.028587+00:00",
          "candidate_utc": "2026-04-22T08:00:05.028587Z",
          "inside_actual_file_span": true,
          "inside_requested_utc_window": true
        }
      ],
      "exists_in_active_worktree": true,
      "field_availability_manifest": {
        "ask": true,
        "bid": true,
        "broker_symbol": true,
        "flags": true,
        "last": true,
        "source_symbol": true,
        "time_msc": true,
        "time_utc": true,
        "volume": true
      },
      "manifest_max_timestamp_utc": "2026-04-22T23:59:58.514000Z",
      "manifest_min_timestamp_utc": "2026-04-22T00:00:09.411000Z",
      "manifest_row_count": 250615,
      "manifest_sha256": "69080040b37c652eefec2ffded50239c0cb608225eab23029d23f94b3fc2b379",
      "manifest_size_bytes": 4019231,
      "max_timestamp_matches_manifest": true,
      "min_timestamp_matches_manifest": true,
      "owner_request_id": "OWNER-TICK-0004",
      "parquet_schema_fields": [
        "time_utc",
        "time",
        "time_msc",
        "bid",
        "ask",
        "last",
        "volume",
        "flags",
        "volume_real",
        "source_symbol",
        "broker_symbol"
      ],
      "rehash_status": "REHASHED_LOCAL_SOURCE_FILE",
      "requested_window_end_utc": "2026-04-22T23:59:59.999999Z",
      "requested_window_start_utc": "2026-04-22T00:00:00Z",
      "row_count_matches_manifest": true,
      "sha256_matches_manifest": true,
      "size_matches_manifest": true,
      "source_date": "2026-04-22",
      "source_path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/GBPJPY/2026-04-22.parquet",
      "symbol": "GBPJPY",
      "symbol_compatibility": {
        "broker_symbol": "GBPJPY",
        "requested_symbol": "GBPJPY",
        "status": "exact_symbol_match"
      },
      "terminal_status": "RECOVERED_READONLY_MT5_SOURCE_HASHED",
      "window_coverage_status": "PASS_REHASHED_SOURCE_COVERS_REQUESTED_UTC_WINDOW_AND_CANDIDATES"
    },
    {
      "actual_broker_symbol_values": [
        "GBPJPY"
      ],
      "actual_in_requested_window_row_count": 305039,
      "actual_max_timestamp_utc": "2026-04-23T23:59:58.735000Z",
      "actual_min_timestamp_utc": "2026-04-23T00:00:04.798000Z",
      "actual_required_field_missing": [],
      "actual_row_count": 305039,
      "actual_sha256": "8fb92e5674382c0265062249b073b7e36805a53a9fc07bedd4d6ee83c0d9784a",
      "actual_size_bytes": 4684456,
      "actual_source_symbol_values": [
        "GBPJPY"
      ],
      "actual_symbol_alias_compatible": true,
      "audit_status": "PASS",
      "candidate_ids": [
        "GBPJPY_2026-04-23T07:16:14.138817+00:00"
      ],
      "candidate_window_checks": [
        {
          "candidate_id": "GBPJPY_2026-04-23T07:16:14.138817+00:00",
          "candidate_utc": "2026-04-23T07:16:14.138817Z",
          "inside_actual_file_span": true,
          "inside_requested_utc_window": true
        }
      ],
      "exists_in_active_worktree": true,
      "field_availability_manifest": {
        "ask": true,
        "bid": true,
        "broker_symbol": true,
        "flags": true,
        "last": true,
        "source_symbol": true,
        "time_msc": true,
        "time_utc": true,
        "volume": true
      },
      "manifest_max_timestamp_utc": "2026-04-23T23:59:58.735000Z",
      "manifest_min_timestamp_utc": "2026-04-23T00:00:04.798000Z",
      "manifest_row_count": 305039,
      "manifest_sha256": "8fb92e5674382c0265062249b073b7e36805a53a9fc07bedd4d6ee83c0d9784a",
      "manifest_size_bytes": 4684456,
      "max_timestamp_matches_manifest": true,
      "min_timestamp_matches_manifest": true,
      "owner_request_id": "OWNER-TICK-0005",
      "parquet_schema_fields": [
        "time_utc",
        "time",
        "time_msc",
        "bid",
        "ask",
        "last",
        "volume",
        "flags",
        "volume_real",
        "source_symbol",
        "broker_symbol"
      ],
      "rehash_status": "REHASHED_LOCAL_SOURCE_FILE",
      "requested_window_end_utc": "2026-04-23T23:59:59.999999Z",
      "requested_window_start_utc": "2026-04-23T00:00:00Z",
      "row_count_matches_manifest": true,
      "sha256_matches_manifest": true,
      "size_matches_manifest": true,
      "source_date": "2026-04-23",
      "source_path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/GBPJPY/2026-04-23.parquet",
      "symbol": "GBPJPY",
      "symbol_compatibility": {
        "broker_symbol": "GBPJPY",
        "requested_symbol": "GBPJPY",
        "status": "exact_symbol_match"
      },
      "terminal_status": "RECOVERED_READONLY_MT5_SOURCE_HASHED",
      "window_coverage_status": "PASS_REHASHED_SOURCE_COVERS_REQUESTED_UTC_WINDOW_AND_CANDIDATES"
    },
    {
      "actual_broker_symbol_values": [
        "GBPUSD"
      ],
      "actual_in_requested_window_row_count": 140383,
      "actual_max_timestamp_utc": "2026-04-14T23:59:58.289000Z",
      "actual_min_timestamp_utc": "2026-04-14T00:00:02.878000Z",
      "actual_required_field_missing": [],
      "actual_row_count": 140383,
      "actual_sha256": "0f917392030134ca9fa443abdec1207e5d80542b5e0b9d6b3a3ba59aa191e412",
      "actual_size_bytes": 2566997,
      "actual_source_symbol_values": [
        "GBPUSD"
      ],
      "actual_symbol_alias_compatible": true,
      "audit_status": "PASS",
      "candidate_ids": [
        "GBPUSD_2026-04-14T07:30:05.011677+00:00",
        "GBPUSD_2026-04-14T14:00:57.743957+00:00"
      ],
      "candidate_window_checks": [
        {
          "candidate_id": "GBPUSD_2026-04-14T07:30:05.011677+00:00",
          "candidate_utc": "2026-04-14T07:30:05.011677Z",
          "inside_actual_file_span": true,
          "inside_requested_utc_window": true
        },
        {
          "candidate_id": "GBPUSD_2026-04-14T14:00:57.743957+00:00",
          "candidate_utc": "2026-04-14T14:00:57.743957Z",
          "inside_actual_file_span": true,
          "inside_requested_utc_window": true
        }
      ],
      "exists_in_active_worktree": true,
      "field_availability_manifest": {
        "ask": true,
        "bid": true,
        "broker_symbol": true,
        "flags": true,
        "last": true,
        "source_symbol": true,
        "time_msc": true,
        "time_utc": true,
        "volume": true
      },
      "manifest_max_timestamp_utc": "2026-04-14T23:59:58.289000Z",
      "manifest_min_timestamp_utc": "2026-04-14T00:00:02.878000Z",
      "manifest_row_count": 140383,
      "manifest_sha256": "0f917392030134ca9fa443abdec1207e5d80542b5e0b9d6b3a3ba59aa191e412",
      "manifest_size_bytes": 2566997,
      "max_timestamp_matches_manifest": true,
      "min_timestamp_matches_manifest": true,
      "owner_request_id": "OWNER-TICK-0006",
      "parquet_schema_fields": [
        "time_utc",
        "time",
        "time_msc",
        "bid",
        "ask",
        "last",
        "volume",
        "flags",
        "volume_real",
        "source_symbol",
        "broker_symbol"
      ],
      "rehash_status": "REHASHED_LOCAL_SOURCE_FILE",
      "requested_window_end_utc": "2026-04-14T23:59:59.999999Z",
      "requested_window_start_utc": "2026-04-14T00:00:00Z",
      "row_count_matches_manifest": true,
      "sha256_matches_manifest": true,
      "size_matches_manifest": true,
      "source_date": "2026-04-14",
      "source_path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/GBPUSD/2026-04-14.parquet",
      "symbol": "GBPUSD",
      "symbol_compatibility": {
        "broker_symbol": "GBPUSD",
        "requested_symbol": "GBPUSD",
        "status": "exact_symbol_match"
      },
      "terminal_status": "RECOVERED_READONLY_MT5_SOURCE_HASHED",
      "window_coverage_status": "PASS_REHASHED_SOURCE_COVERS_REQUESTED_UTC_WINDOW_AND_CANDIDATES"
    },
    {
      "actual_broker_symbol_values": [
        "GBPUSD"
      ],
      "actual_in_requested_window_row_count": 152421,
      "actual_max_timestamp_utc": "2026-04-15T23:59:57.944000Z",
      "actual_min_timestamp_utc": "2026-04-15T00:00:03.761000Z",
      "actual_required_field_missing": [],
      "actual_row_count": 152421,
      "actual_sha256": "7b4df6cc830b0f94d1c80c32782a19d176d96c2a5f9a2b4d280899746e8d8dfb",
      "actual_size_bytes": 2722667,
      "actual_source_symbol_values": [
        "GBPUSD"
      ],
      "actual_symbol_alias_compatible": true,
      "audit_status": "PASS",
      "candidate_ids": [
        "GBPUSD_2026-04-15T07:30:05.010905+00:00",
        "GBPUSD_2026-04-15T13:16:01.327115+00:00"
      ],
      "candidate_window_checks": [
        {
          "candidate_id": "GBPUSD_2026-04-15T07:30:05.010905+00:00",
          "candidate_utc": "2026-04-15T07:30:05.010905Z",
          "inside_actual_file_span": true,
          "inside_requested_utc_window": true
        },
        {
          "candidate_id": "GBPUSD_2026-04-15T13:16:01.327115+00:00",
          "candidate_utc": "2026-04-15T13:16:01.327115Z",
          "inside_actual_file_span": true,
          "inside_requested_utc_window": true
        }
      ],
      "exists_in_active_worktree": true,
      "field_availability_manifest": {
        "ask": true,
        "bid": true,
        "broker_symbol": true,
        "flags": true,
        "last": true,
        "source_symbol": true,
        "time_msc": true,
        "time_utc": true,
        "volume": true
      },
      "manifest_max_timestamp_utc": "2026-04-15T23:59:57.944000Z",
      "manifest_min_timestamp_utc": "2026-04-15T00:00:03.761000Z",
      "manifest_row_count": 152421,
      "manifest_sha256": "7b4df6cc830b0f94d1c80c32782a19d176d96c2a5f9a2b4d280899746e8d8dfb",
      "manifest_size_bytes": 2722667,
      "max_timestamp_matches_manifest": true,
      "min_timestamp_matches_manifest": true,
      "owner_request_id": "OWNER-TICK-0007",
      "parquet_schema_fields": [
        "time_utc",
        "time",
        "time_msc",
        "bid",
        "ask",
        "last",
        "volume",
        "flags",
        "volume_real",
        "source_symbol",
        "broker_symbol"
      ],
      "rehash_status": "REHASHED_LOCAL_SOURCE_FILE",
      "requested_window_end_utc": "2026-04-15T23:59:59.999999Z",
      "requested_window_start_utc": "2026-04-15T00:00:00Z",
      "row_count_matches_manifest": true,
      "sha256_matches_manifest": true,
      "size_matches_manifest": true,
      "source_date": "2026-04-15",
      "source_path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/GBPUSD/2026-04-15.parquet",
      "symbol": "GBPUSD",
      "symbol_compatibility": {
        "broker_symbol": "GBPUSD",
        "requested_symbol": "GBPUSD",
        "status": "exact_symbol_match"
      },
      "terminal_status": "RECOVERED_READONLY_MT5_SOURCE_HASHED",
      "window_coverage_status": "PASS_REHASHED_SOURCE_COVERS_REQUESTED_UTC_WINDOW_AND_CANDIDATES"
    },
    {
      "actual_broker_symbol_values": [
        "GBPUSD"
      ],
      "actual_in_requested_window_row_count": 178942,
      "actual_max_timestamp_utc": "2026-04-17T23:59:41.473000Z",
      "actual_min_timestamp_utc": "2026-04-17T00:00:09.834000Z",
      "actual_required_field_missing": [],
      "actual_row_count": 178942,
      "actual_sha256": "a0dbedf4f42333595f614b9eacaabf1d24b0f1d55c790d971fc50adcfc3d8d12",
      "actual_size_bytes": 3049533,
      "actual_source_symbol_values": [
        "GBPUSD"
      ],
      "actual_symbol_alias_compatible": true,
      "audit_status": "PASS",
      "candidate_ids": [
        "GBPUSD_2026-04-17T08:00:59.541491+00:00",
        "GBPUSD_2026-04-17T14:15:05.012317+00:00"
      ],
      "candidate_window_checks": [
        {
          "candidate_id": "GBPUSD_2026-04-17T08:00:59.541491+00:00",
          "candidate_utc": "2026-04-17T08:00:59.541491Z",
          "inside_actual_file_span": true,
          "inside_requested_utc_window": true
        },
        {
          "candidate_id": "GBPUSD_2026-04-17T14:15:05.012317+00:00",
          "candidate_utc": "2026-04-17T14:15:05.012317Z",
          "inside_actual_file_span": true,
          "inside_requested_utc_window": true
        }
      ],
      "exists_in_active_worktree": true,
      "field_availability_manifest": {
        "ask": true,
        "bid": true,
        "broker_symbol": true,
        "flags": true,
        "last": true,
        "source_symbol": true,
        "time_msc": true,
        "time_utc": true,
        "volume": true
      },
      "manifest_max_timestamp_utc": "2026-04-17T23:59:41.473000Z",
      "manifest_min_timestamp_utc": "2026-04-17T00:00:09.834000Z",
      "manifest_row_count": 178942,
      "manifest_sha256": "a0dbedf4f42333595f614b9eacaabf1d24b0f1d55c790d971fc50adcfc3d8d12",
      "manifest_size_bytes": 3049533,
      "max_timestamp_matches_manifest": true,
      "min_timestamp_matches_manifest": true,
      "owner_request_id": "OWNER-TICK-0008",
      "parquet_schema_fields": [
        "time_utc",
        "time",
        "time_msc",
        "bid",
        "ask",
        "last",
        "volume",
        "flags",
        "volume_real",
        "source_symbol",
        "broker_symbol"
      ],
      "rehash_status": "REHASHED_LOCAL_SOURCE_FILE",
      "requested_window_end_utc": "2026-04-17T23:59:59.999999Z",
      "requested_window_start_utc": "2026-04-17T00:00:00Z",
      "row_count_matches_manifest": true,
      "sha256_matches_manifest": true,
      "size_matches_manifest": true,
      "source_date": "2026-04-17",
      "source_path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/GBPUSD/2026-04-17.parquet",
      "symbol": "GBPUSD",
      "symbol_compatibility": {
        "broker_symbol": "GBPUSD",
        "requested_symbol": "GBPUSD",
        "status": "exact_symbol_match"
      },
      "terminal_status": "RECOVERED_READONLY_MT5_SOURCE_HASHED",
      "window_coverage_status": "PASS_REHASHED_SOURCE_COVERS_REQUESTED_UTC_WINDOW_AND_CANDIDATES"
    },
    {
      "actual_broker_symbol_values": [
        "GBPUSD"
      ],
      "actual_in_requested_window_row_count": 179015,
      "actual_max_timestamp_utc": "2026-04-20T23:59:58.559000Z",
      "actual_min_timestamp_utc": "2026-04-20T00:00:07.487000Z",
      "actual_required_field_missing": [],
      "actual_row_count": 179015,
      "actual_sha256": "2dcf9ea0d4d33f5f09a7bd8427251fc9f5282fbca52861bb9a808be1c4328f8a",
      "actual_size_bytes": 3059435,
      "actual_source_symbol_values": [
        "GBPUSD"
      ],
      "actual_symbol_alias_compatible": true,
      "audit_status": "PASS",
      "candidate_ids": [
        "GBPUSD_2026-04-20T07:45:05.020140+00:00",
        "GBPUSD_2026-04-20T15:31:14.730975+00:00"
      ],
      "candidate_window_checks": [
        {
          "candidate_id": "GBPUSD_2026-04-20T07:45:05.020140+00:00",
          "candidate_utc": "2026-04-20T07:45:05.020140Z",
          "inside_actual_file_span": true,
          "inside_requested_utc_window": true
        },
        {
          "candidate_id": "GBPUSD_2026-04-20T15:31:14.730975+00:00",
          "candidate_utc": "2026-04-20T15:31:14.730975Z",
          "inside_actual_file_span": true,
          "inside_requested_utc_window": true
        }
      ],
      "exists_in_active_worktree": true,
      "field_availability_manifest": {
        "ask": true,
        "bid": true,
        "broker_symbol": true,
        "flags": true,
        "last": true,
        "source_symbol": true,
        "time_msc": true,
        "time_utc": true,
        "volume": true
      },
      "manifest_max_timestamp_utc": "2026-04-20T23:59:58.559000Z",
      "manifest_min_timestamp_utc": "2026-04-20T00:00:07.487000Z",
      "manifest_row_count": 179015,
      "manifest_sha256": "2dcf9ea0d4d33f5f09a7bd8427251fc9f5282fbca52861bb9a808be1c4328f8a",
      "manifest_size_bytes": 3059435,
      "max_timestamp_matches_manifest": true,
      "min_timestamp_matches_manifest": true,
      "owner_request_id": "OWNER-TICK-0009",
      "parquet_schema_fields": [
        "time_utc",
        "time",
        "time_msc",
        "bid",
        "ask",
        "last",
        "volume",
        "flags",
        "volume_real",
        "source_symbol",
        "broker_symbol"
      ],
      "rehash_status": "REHASHED_LOCAL_SOURCE_FILE",
      "requested_window_end_utc": "2026-04-20T23:59:59.999999Z",
      "requested_window_start_utc": "2026-04-20T00:00:00Z",
      "row_count_matches_manifest": true,
      "sha256_matches_manifest": true,
      "size_matches_manifest": true,
      "source_date": "2026-04-20",
      "source_path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/GBPUSD/2026-04-20.parquet",
      "symbol": "GBPUSD",
      "symbol_compatibility": {
        "broker_symbol": "GBPUSD",
        "requested_symbol": "GBPUSD",
        "status": "exact_symbol_match"
      },
      "terminal_status": "RECOVERED_READONLY_MT5_SOURCE_HASHED",
      "window_coverage_status": "PASS_REHASHED_SOURCE_COVERS_REQUESTED_UTC_WINDOW_AND_CANDIDATES"
    },
    {
      "actual_broker_symbol_values": [
        "GBPUSD"
      ],
      "actual_in_requested_window_row_count": 184174,
      "actual_max_timestamp_utc": "2026-04-21T23:59:58.549000Z",
      "actual_min_timestamp_utc": "2026-04-21T00:00:06.807000Z",
      "actual_required_field_missing": [],
      "actual_row_count": 184174,
      "actual_sha256": "b3b9349ae45bbf63669ab6957f08608b41dbc5e79901586a4f2635439cdd3822",
      "actual_size_bytes": 3104581,
      "actual_source_symbol_values": [
        "GBPUSD"
      ],
      "actual_symbol_alias_compatible": true,
      "audit_status": "PASS",
      "candidate_ids": [
        "GBPUSD_2026-04-21T11:30:05.011826+00:00"
      ],
      "candidate_window_checks": [
        {
          "candidate_id": "GBPUSD_2026-04-21T11:30:05.011826+00:00",
          "candidate_utc": "2026-04-21T11:30:05.011826Z",
          "inside_actual_file_span": true,
          "inside_requested_utc_window": true
        }
      ],
      "exists_in_active_worktree": true,
      "field_availability_manifest": {
        "ask": true,
        "bid": true,
        "broker_symbol": true,
        "flags": true,
        "last": true,
        "source_symbol": true,
        "time_msc": true,
        "time_utc": true,
        "volume": true
      },
      "manifest_max_timestamp_utc": "2026-04-21T23:59:58.549000Z",
      "manifest_min_timestamp_utc": "2026-04-21T00:00:06.807000Z",
      "manifest_row_count": 184174,
      "manifest_sha256": "b3b9349ae45bbf63669ab6957f08608b41dbc5e79901586a4f2635439cdd3822",
      "manifest_size_bytes": 3104581,
      "max_timestamp_matches_manifest": true,
      "min_timestamp_matches_manifest": true,
      "owner_request_id": "OWNER-TICK-0010",
      "parquet_schema_fields": [
        "time_utc",
        "time",
        "time_msc",
        "bid",
        "ask",
        "last",
        "volume",
        "flags",
        "volume_real",
        "source_symbol",
        "broker_symbol"
      ],
      "rehash_status": "REHASHED_LOCAL_SOURCE_FILE",
      "requested_window_end_utc": "2026-04-21T23:59:59.999999Z",
      "requested_window_start_utc": "2026-04-21T00:00:00Z",
      "row_count_matches_manifest": true,
      "sha256_matches_manifest": true,
      "size_matches_manifest": true,
      "source_date": "2026-04-21",
      "source_path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/GBPUSD/2026-04-21.parquet",
      "symbol": "GBPUSD",
      "symbol_compatibility": {
        "broker_symbol": "GBPUSD",
        "requested_symbol": "GBPUSD",
        "status": "exact_symbol_match"
      },
      "terminal_status": "RECOVERED_READONLY_MT5_SOURCE_HASHED",
      "window_coverage_status": "PASS_REHASHED_SOURCE_COVERS_REQUESTED_UTC_WINDOW_AND_CANDIDATES"
    },
    {
      "actual_broker_symbol_values": [
        "GBPUSD"
      ],
      "actual_in_requested_window_row_count": 163415,
      "actual_max_timestamp_utc": "2026-04-22T23:59:58.269000Z",
      "actual_min_timestamp_utc": "2026-04-22T00:00:09.344000Z",
      "actual_required_field_missing": [],
      "actual_row_count": 163415,
      "actual_sha256": "c28e753536fd2ef40fec68ec70f8024176985ab34b4202dd962059df81f696d2",
      "actual_size_bytes": 2869040,
      "actual_source_symbol_values": [
        "GBPUSD"
      ],
      "actual_symbol_alias_compatible": true,
      "audit_status": "PASS",
      "candidate_ids": [
        "GBPUSD_2026-04-22T07:16:12.155934+00:00"
      ],
      "candidate_window_checks": [
        {
          "candidate_id": "GBPUSD_2026-04-22T07:16:12.155934+00:00",
          "candidate_utc": "2026-04-22T07:16:12.155934Z",
          "inside_actual_file_span": true,
          "inside_requested_utc_window": true
        }
      ],
      "exists_in_active_worktree": true,
      "field_availability_manifest": {
        "ask": true,
        "bid": true,
        "broker_symbol": true,
        "flags": true,
        "last": true,
        "source_symbol": true,
        "time_msc": true,
        "time_utc": true,
        "volume": true
      },
      "manifest_max_timestamp_utc": "2026-04-22T23:59:58.269000Z",
      "manifest_min_timestamp_utc": "2026-04-22T00:00:09.344000Z",
      "manifest_row_count": 163415,
      "manifest_sha256": "c28e753536fd2ef40fec68ec70f8024176985ab34b4202dd962059df81f696d2",
      "manifest_size_bytes": 2869040,
      "max_timestamp_matches_manifest": true,
      "min_timestamp_matches_manifest": true,
      "owner_request_id": "OWNER-TICK-0011",
      "parquet_schema_fields": [
        "time_utc",
        "time",
        "time_msc",
        "bid",
        "ask",
        "last",
        "volume",
        "flags",
        "volume_real",
        "source_symbol",
        "broker_symbol"
      ],
      "rehash_status": "REHASHED_LOCAL_SOURCE_FILE",
      "requested_window_end_utc": "2026-04-22T23:59:59.999999Z",
      "requested_window_start_utc": "2026-04-22T00:00:00Z",
      "row_count_matches_manifest": true,
      "sha256_matches_manifest": true,
      "size_matches_manifest": true,
      "source_date": "2026-04-22",
      "source_path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/GBPUSD/2026-04-22.parquet",
      "symbol": "GBPUSD",
      "symbol_compatibility": {
        "broker_symbol": "GBPUSD",
        "requested_symbol": "GBPUSD",
        "status": "exact_symbol_match"
      },
      "terminal_status": "RECOVERED_READONLY_MT5_SOURCE_HASHED",
      "window_coverage_status": "PASS_REHASHED_SOURCE_COVERS_REQUESTED_UTC_WINDOW_AND_CANDIDATES"
    },
    {
      "actual_broker_symbol_values": [
        "US30"
      ],
      "actual_in_requested_window_row_count": 189608,
      "actual_max_timestamp_utc": "2026-04-14T23:57:49.824000Z",
      "actual_min_timestamp_utc": "2026-04-14T01:01:00.262000Z",
      "actual_required_field_missing": [],
      "actual_row_count": 189608,
      "actual_sha256": "89231640fafef98b7e6e01a8c7e76413986b4874b5de8d64bdf0b553f7941588",
      "actual_size_bytes": 3363965,
      "actual_source_symbol_values": [
        "US30"
      ],
      "actual_symbol_alias_compatible": true,
      "audit_status": "PASS",
      "candidate_ids": [
        "US30_cash_2026-04-14T08:16:00.983581+00:00"
      ],
      "candidate_window_checks": [
        {
          "candidate_id": "US30_cash_2026-04-14T08:16:00.983581+00:00",
          "candidate_utc": "2026-04-14T08:16:00.983581Z",
          "inside_actual_file_span": true,
          "inside_requested_utc_window": true
        }
      ],
      "exists_in_active_worktree": true,
      "field_availability_manifest": {
        "ask": true,
        "bid": true,
        "broker_symbol": true,
        "flags": true,
        "last": true,
        "source_symbol": true,
        "time_msc": true,
        "time_utc": true,
        "volume": true
      },
      "manifest_max_timestamp_utc": "2026-04-14T23:57:49.824000Z",
      "manifest_min_timestamp_utc": "2026-04-14T01:01:00.262000Z",
      "manifest_row_count": 189608,
      "manifest_sha256": "89231640fafef98b7e6e01a8c7e76413986b4874b5de8d64bdf0b553f7941588",
      "manifest_size_bytes": 3363965,
      "max_timestamp_matches_manifest": true,
      "min_timestamp_matches_manifest": true,
      "owner_request_id": "OWNER-TICK-0012",
      "parquet_schema_fields": [
        "time_utc",
        "time",
        "time_msc",
        "bid",
        "ask",
        "last",
        "volume",
        "flags",
        "volume_real",
        "source_symbol",
        "broker_symbol"
      ],
      "rehash_status": "REHASHED_LOCAL_SOURCE_FILE",
      "requested_window_end_utc": "2026-04-14T23:59:59.999999Z",
      "requested_window_start_utc": "2026-04-14T00:00:00Z",
      "row_count_matches_manifest": true,
      "sha256_matches_manifest": true,
      "size_matches_manifest": true,
      "source_date": "2026-04-14",
      "source_path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/US30_cash/2026-04-14.parquet",
      "symbol": "US30_cash",
      "symbol_compatibility": {
        "basis": "existing repo MT5 research export mapping uses US30_cash:US30",
        "broker_symbol": "US30",
        "requested_symbol": "US30_cash",
        "status": "compatible_broker_alias_for_market_data_only"
      },
      "terminal_status": "RECOVERED_READONLY_MT5_SOURCE_HASHED",
      "window_coverage_status": "PASS_REHASHED_SOURCE_COVERS_REQUESTED_UTC_WINDOW_AND_CANDIDATES"
    },
    {
      "actual_broker_symbol_values": [
        "US30"
      ],
      "actual_in_requested_window_row_count": 181824,
      "actual_max_timestamp_utc": "2026-04-16T23:57:54.481000Z",
      "actual_min_timestamp_utc": "2026-04-16T01:01:00.265000Z",
      "actual_required_field_missing": [],
      "actual_row_count": 181824,
      "actual_sha256": "205c20d976f85a2031cfcd62db900295d2a665f021c48cdb9c8c140761d70c39",
      "actual_size_bytes": 3227975,
      "actual_source_symbol_values": [
        "US30"
      ],
      "actual_symbol_alias_compatible": true,
      "audit_status": "PASS",
      "candidate_ids": [
        "US30_cash_2026-04-16T13:45:56.810509+00:00"
      ],
      "candidate_window_checks": [
        {
          "candidate_id": "US30_cash_2026-04-16T13:45:56.810509+00:00",
          "candidate_utc": "2026-04-16T13:45:56.810509Z",
          "inside_actual_file_span": true,
          "inside_requested_utc_window": true
        }
      ],
      "exists_in_active_worktree": true,
      "field_availability_manifest": {
        "ask": true,
        "bid": true,
        "broker_symbol": true,
        "flags": true,
        "last": true,
        "source_symbol": true,
        "time_msc": true,
        "time_utc": true,
        "volume": true
      },
      "manifest_max_timestamp_utc": "2026-04-16T23:57:54.481000Z",
      "manifest_min_timestamp_utc": "2026-04-16T01:01:00.265000Z",
      "manifest_row_count": 181824,
      "manifest_sha256": "205c20d976f85a2031cfcd62db900295d2a665f021c48cdb9c8c140761d70c39",
      "manifest_size_bytes": 3227975,
      "max_timestamp_matches_manifest": true,
      "min_timestamp_matches_manifest": true,
      "owner_request_id": "OWNER-TICK-0013",
      "parquet_schema_fields": [
        "time_utc",
        "time",
        "time_msc",
        "bid",
        "ask",
        "last",
        "volume",
        "flags",
        "volume_real",
        "source_symbol",
        "broker_symbol"
      ],
      "rehash_status": "REHASHED_LOCAL_SOURCE_FILE",
      "requested_window_end_utc": "2026-04-16T23:59:59.999999Z",
      "requested_window_start_utc": "2026-04-16T00:00:00Z",
      "row_count_matches_manifest": true,
      "sha256_matches_manifest": true,
      "size_matches_manifest": true,
      "source_date": "2026-04-16",
      "source_path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/US30_cash/2026-04-16.parquet",
      "symbol": "US30_cash",
      "symbol_compatibility": {
        "basis": "existing repo MT5 research export mapping uses US30_cash:US30",
        "broker_symbol": "US30",
        "requested_symbol": "US30_cash",
        "status": "compatible_broker_alias_for_market_data_only"
      },
      "terminal_status": "RECOVERED_READONLY_MT5_SOURCE_HASHED",
      "window_coverage_status": "PASS_REHASHED_SOURCE_COVERS_REQUESTED_UTC_WINDOW_AND_CANDIDATES"
    },
    {
      "actual_broker_symbol_values": [
        "USDJPY"
      ],
      "actual_in_requested_window_row_count": 117046,
      "actual_max_timestamp_utc": "2026-04-15T23:59:58.041000Z",
      "actual_min_timestamp_utc": "2026-04-15T00:00:03.797000Z",
      "actual_required_field_missing": [],
      "actual_row_count": 117046,
      "actual_sha256": "bf6196c9332e94adf576becb743e77848844b59ebf4ba1126029232224df8e30",
      "actual_size_bytes": 2243297,
      "actual_source_symbol_values": [
        "USDJPY"
      ],
      "actual_symbol_alias_compatible": true,
      "audit_status": "PASS",
      "candidate_ids": [
        "USDJPY_2026-04-15T02:45:05.009485+00:00",
        "USDJPY_2026-04-15T13:15:57.398922+00:00"
      ],
      "candidate_window_checks": [
        {
          "candidate_id": "USDJPY_2026-04-15T02:45:05.009485+00:00",
          "candidate_utc": "2026-04-15T02:45:05.009485Z",
          "inside_actual_file_span": true,
          "inside_requested_utc_window": true
        },
        {
          "candidate_id": "USDJPY_2026-04-15T13:15:57.398922+00:00",
          "candidate_utc": "2026-04-15T13:15:57.398922Z",
          "inside_actual_file_span": true,
          "inside_requested_utc_window": true
        }
      ],
      "exists_in_active_worktree": true,
      "field_availability_manifest": {
        "ask": true,
        "bid": true,
        "broker_symbol": true,
        "flags": true,
        "last": true,
        "source_symbol": true,
        "time_msc": true,
        "time_utc": true,
        "volume": true
      },
      "manifest_max_timestamp_utc": "2026-04-15T23:59:58.041000Z",
      "manifest_min_timestamp_utc": "2026-04-15T00:00:03.797000Z",
      "manifest_row_count": 117046,
      "manifest_sha256": "bf6196c9332e94adf576becb743e77848844b59ebf4ba1126029232224df8e30",
      "manifest_size_bytes": 2243297,
      "max_timestamp_matches_manifest": true,
      "min_timestamp_matches_manifest": true,
      "owner_request_id": "OWNER-TICK-0014",
      "parquet_schema_fields": [
        "time_utc",
        "time",
        "time_msc",
        "bid",
        "ask",
        "last",
        "volume",
        "flags",
        "volume_real",
        "source_symbol",
        "broker_symbol"
      ],
      "rehash_status": "REHASHED_LOCAL_SOURCE_FILE",
      "requested_window_end_utc": "2026-04-15T23:59:59.999999Z",
      "requested_window_start_utc": "2026-04-15T00:00:00Z",
      "row_count_matches_manifest": true,
      "sha256_matches_manifest": true,
      "size_matches_manifest": true,
      "source_date": "2026-04-15",
      "source_path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/USDJPY/2026-04-15.parquet",
      "symbol": "USDJPY",
      "symbol_compatibility": {
        "broker_symbol": "USDJPY",
        "requested_symbol": "USDJPY",
        "status": "exact_symbol_match"
      },
      "terminal_status": "RECOVERED_READONLY_MT5_SOURCE_HASHED",
      "window_coverage_status": "PASS_REHASHED_SOURCE_COVERS_REQUESTED_UTC_WINDOW_AND_CANDIDATES"
    },
    {
      "actual_broker_symbol_values": [
        "USDJPY"
      ],
      "actual_in_requested_window_row_count": 114833,
      "actual_max_timestamp_utc": "2026-04-16T23:59:57.446000Z",
      "actual_min_timestamp_utc": "2026-04-16T00:00:01.335000Z",
      "actual_required_field_missing": [],
      "actual_row_count": 114833,
      "actual_sha256": "3dcadb200e61a1f486303a49716eccb3446f91503e27e42cf681ad62853b407d",
      "actual_size_bytes": 2203620,
      "actual_source_symbol_values": [
        "USDJPY"
      ],
      "actual_symbol_alias_compatible": true,
      "audit_status": "PASS",
      "candidate_ids": [
        "USDJPY_2026-04-16T15:00:05.011292+00:00"
      ],
      "candidate_window_checks": [
        {
          "candidate_id": "USDJPY_2026-04-16T15:00:05.011292+00:00",
          "candidate_utc": "2026-04-16T15:00:05.011292Z",
          "inside_actual_file_span": true,
          "inside_requested_utc_window": true
        }
      ],
      "exists_in_active_worktree": true,
      "field_availability_manifest": {
        "ask": true,
        "bid": true,
        "broker_symbol": true,
        "flags": true,
        "last": true,
        "source_symbol": true,
        "time_msc": true,
        "time_utc": true,
        "volume": true
      },
      "manifest_max_timestamp_utc": "2026-04-16T23:59:57.446000Z",
      "manifest_min_timestamp_utc": "2026-04-16T00:00:01.335000Z",
      "manifest_row_count": 114833,
      "manifest_sha256": "3dcadb200e61a1f486303a49716eccb3446f91503e27e42cf681ad62853b407d",
      "manifest_size_bytes": 2203620,
      "max_timestamp_matches_manifest": true,
      "min_timestamp_matches_manifest": true,
      "owner_request_id": "OWNER-TICK-0015",
      "parquet_schema_fields": [
        "time_utc",
        "time",
        "time_msc",
        "bid",
        "ask",
        "last",
        "volume",
        "flags",
        "volume_real",
        "source_symbol",
        "broker_symbol"
      ],
      "rehash_status": "REHASHED_LOCAL_SOURCE_FILE",
      "requested_window_end_utc": "2026-04-16T23:59:59.999999Z",
      "requested_window_start_utc": "2026-04-16T00:00:00Z",
      "row_count_matches_manifest": true,
      "sha256_matches_manifest": true,
      "size_matches_manifest": true,
      "source_date": "2026-04-16",
      "source_path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/USDJPY/2026-04-16.parquet",
      "symbol": "USDJPY",
      "symbol_compatibility": {
        "broker_symbol": "USDJPY",
        "requested_symbol": "USDJPY",
        "status": "exact_symbol_match"
      },
      "terminal_status": "RECOVERED_READONLY_MT5_SOURCE_HASHED",
      "window_coverage_status": "PASS_REHASHED_SOURCE_COVERS_REQUESTED_UTC_WINDOW_AND_CANDIDATES"
    },
    {
      "actual_broker_symbol_values": [
        "USDJPY"
      ],
      "actual_in_requested_window_row_count": 126514,
      "actual_max_timestamp_utc": "2026-04-21T23:59:57.778000Z",
      "actual_min_timestamp_utc": "2026-04-21T00:00:07.055000Z",
      "actual_required_field_missing": [],
      "actual_row_count": 126514,
      "actual_sha256": "98493eaa5b2ef1f1d5b15c1296770b7c2979f48ac44896764d0ea4fbc9eabb9e",
      "actual_size_bytes": 2367705,
      "actual_source_symbol_values": [
        "USDJPY"
      ],
      "actual_symbol_alias_compatible": true,
      "audit_status": "PASS",
      "candidate_ids": [
        "USDJPY_2026-04-21T13:45:05.018194+00:00"
      ],
      "candidate_window_checks": [
        {
          "candidate_id": "USDJPY_2026-04-21T13:45:05.018194+00:00",
          "candidate_utc": "2026-04-21T13:45:05.018194Z",
          "inside_actual_file_span": true,
          "inside_requested_utc_window": true
        }
      ],
      "exists_in_active_worktree": true,
      "field_availability_manifest": {
        "ask": true,
        "bid": true,
        "broker_symbol": true,
        "flags": true,
        "last": true,
        "source_symbol": true,
        "time_msc": true,
        "time_utc": true,
        "volume": true
      },
      "manifest_max_timestamp_utc": "2026-04-21T23:59:57.778000Z",
      "manifest_min_timestamp_utc": "2026-04-21T00:00:07.055000Z",
      "manifest_row_count": 126514,
      "manifest_sha256": "98493eaa5b2ef1f1d5b15c1296770b7c2979f48ac44896764d0ea4fbc9eabb9e",
      "manifest_size_bytes": 2367705,
      "max_timestamp_matches_manifest": true,
      "min_timestamp_matches_manifest": true,
      "owner_request_id": "OWNER-TICK-0016",
      "parquet_schema_fields": [
        "time_utc",
        "time",
        "time_msc",
        "bid",
        "ask",
        "last",
        "volume",
        "flags",
        "volume_real",
        "source_symbol",
        "broker_symbol"
      ],
      "rehash_status": "REHASHED_LOCAL_SOURCE_FILE",
      "requested_window_end_utc": "2026-04-21T23:59:59.999999Z",
      "requested_window_start_utc": "2026-04-21T00:00:00Z",
      "row_count_matches_manifest": true,
      "sha256_matches_manifest": true,
      "size_matches_manifest": true,
      "source_date": "2026-04-21",
      "source_path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/USDJPY/2026-04-21.parquet",
      "symbol": "USDJPY",
      "symbol_compatibility": {
        "broker_symbol": "USDJPY",
        "requested_symbol": "USDJPY",
        "status": "exact_symbol_match"
      },
      "terminal_status": "RECOVERED_READONLY_MT5_SOURCE_HASHED",
      "window_coverage_status": "PASS_REHASHED_SOURCE_COVERS_REQUESTED_UTC_WINDOW_AND_CANDIDATES"
    },
    {
      "actual_broker_symbol_values": [
        "USDJPY"
      ],
      "actual_in_requested_window_row_count": 115085,
      "actual_max_timestamp_utc": "2026-04-22T23:59:58.465000Z",
      "actual_min_timestamp_utc": "2026-04-22T00:00:09.373000Z",
      "actual_required_field_missing": [],
      "actual_row_count": 115085,
      "actual_sha256": "a5a839f79272c505c3fc87f2a10ff08d48e82f5d6519dea4cc9efb2ec119508d",
      "actual_size_bytes": 2175673,
      "actual_source_symbol_values": [
        "USDJPY"
      ],
      "actual_symbol_alias_compatible": true,
      "audit_status": "PASS",
      "candidate_ids": [
        "USDJPY_2026-04-22T00:30:05.018068+00:00",
        "USDJPY_2026-04-22T15:15:05.016051+00:00"
      ],
      "candidate_window_checks": [
        {
          "candidate_id": "USDJPY_2026-04-22T00:30:05.018068+00:00",
          "candidate_utc": "2026-04-22T00:30:05.018068Z",
          "inside_actual_file_span": true,
          "inside_requested_utc_window": true
        },
        {
          "candidate_id": "USDJPY_2026-04-22T15:15:05.016051+00:00",
          "candidate_utc": "2026-04-22T15:15:05.016051Z",
          "inside_actual_file_span": true,
          "inside_requested_utc_window": true
        }
      ],
      "exists_in_active_worktree": true,
      "field_availability_manifest": {
        "ask": true,
        "bid": true,
        "broker_symbol": true,
        "flags": true,
        "last": true,
        "source_symbol": true,
        "time_msc": true,
        "time_utc": true,
        "volume": true
      },
      "manifest_max_timestamp_utc": "2026-04-22T23:59:58.465000Z",
      "manifest_min_timestamp_utc": "2026-04-22T00:00:09.373000Z",
      "manifest_row_count": 115085,
      "manifest_sha256": "a5a839f79272c505c3fc87f2a10ff08d48e82f5d6519dea4cc9efb2ec119508d",
      "manifest_size_bytes": 2175673,
      "max_timestamp_matches_manifest": true,
      "min_timestamp_matches_manifest": true,
      "owner_request_id": "OWNER-TICK-0017",
      "parquet_schema_fields": [
        "time_utc",
        "time",
        "time_msc",
        "bid",
        "ask",
        "last",
        "volume",
        "flags",
        "volume_real",
        "source_symbol",
        "broker_symbol"
      ],
      "rehash_status": "REHASHED_LOCAL_SOURCE_FILE",
      "requested_window_end_utc": "2026-04-22T23:59:59.999999Z",
      "requested_window_start_utc": "2026-04-22T00:00:00Z",
      "row_count_matches_manifest": true,
      "sha256_matches_manifest": true,
      "size_matches_manifest": true,
      "source_date": "2026-04-22",
      "source_path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/USDJPY/2026-04-22.parquet",
      "symbol": "USDJPY",
      "symbol_compatibility": {
        "broker_symbol": "USDJPY",
        "requested_symbol": "USDJPY",
        "status": "exact_symbol_match"
      },
      "terminal_status": "RECOVERED_READONLY_MT5_SOURCE_HASHED",
      "window_coverage_status": "PASS_REHASHED_SOURCE_COVERS_REQUESTED_UTC_WINDOW_AND_CANDIDATES"
    },
    {
      "actual_broker_symbol_values": [
        "USDJPY"
      ],
      "actual_in_requested_window_row_count": 150006,
      "actual_max_timestamp_utc": "2026-04-23T23:59:58.374000Z",
      "actual_min_timestamp_utc": "2026-04-23T00:00:04.775000Z",
      "actual_required_field_missing": [],
      "actual_row_count": 150006,
      "actual_sha256": "4c1b7ee014d33eb4d6a5f886b68e44224080fa433bf278be1e7b2d9852e67010",
      "actual_size_bytes": 2711362,
      "actual_source_symbol_values": [
        "USDJPY"
      ],
      "actual_symbol_alias_compatible": true,
      "audit_status": "PASS",
      "candidate_ids": [
        "USDJPY_2026-04-23T08:45:05.012266+00:00"
      ],
      "candidate_window_checks": [
        {
          "candidate_id": "USDJPY_2026-04-23T08:45:05.012266+00:00",
          "candidate_utc": "2026-04-23T08:45:05.012266Z",
          "inside_actual_file_span": true,
          "inside_requested_utc_window": true
        }
      ],
      "exists_in_active_worktree": true,
      "field_availability_manifest": {
        "ask": true,
        "bid": true,
        "broker_symbol": true,
        "flags": true,
        "last": true,
        "source_symbol": true,
        "time_msc": true,
        "time_utc": true,
        "volume": true
      },
      "manifest_max_timestamp_utc": "2026-04-23T23:59:58.374000Z",
      "manifest_min_timestamp_utc": "2026-04-23T00:00:04.775000Z",
      "manifest_row_count": 150006,
      "manifest_sha256": "4c1b7ee014d33eb4d6a5f886b68e44224080fa433bf278be1e7b2d9852e67010",
      "manifest_size_bytes": 2711362,
      "max_timestamp_matches_manifest": true,
      "min_timestamp_matches_manifest": true,
      "owner_request_id": "OWNER-TICK-0018",
      "parquet_schema_fields": [
        "time_utc",
        "time",
        "time_msc",
        "bid",
        "ask",
        "last",
        "volume",
        "flags",
        "volume_real",
        "source_symbol",
        "broker_symbol"
      ],
      "rehash_status": "REHASHED_LOCAL_SOURCE_FILE",
      "requested_window_end_utc": "2026-04-23T23:59:59.999999Z",
      "requested_window_start_utc": "2026-04-23T00:00:00Z",
      "row_count_matches_manifest": true,
      "sha256_matches_manifest": true,
      "size_matches_manifest": true,
      "source_date": "2026-04-23",
      "source_path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/USDJPY/2026-04-23.parquet",
      "symbol": "USDJPY",
      "symbol_compatibility": {
        "broker_symbol": "USDJPY",
        "requested_symbol": "USDJPY",
        "status": "exact_symbol_match"
      },
      "terminal_status": "RECOVERED_READONLY_MT5_SOURCE_HASHED",
      "window_coverage_status": "PASS_REHASHED_SOURCE_COVERS_REQUESTED_UTC_WINDOW_AND_CANDIDATES"
    },
    {
      "actual_broker_symbol_values": [
        "USDJPY"
      ],
      "actual_in_requested_window_row_count": 125100,
      "actual_max_timestamp_utc": "2026-04-24T23:59:43.751000Z",
      "actual_min_timestamp_utc": "2026-04-24T00:00:06.045000Z",
      "actual_required_field_missing": [],
      "actual_row_count": 125100,
      "actual_sha256": "96ee076771334c44ea29560d2ddd2cb02563750147be045b58b96d71ae827479",
      "actual_size_bytes": 2345690,
      "actual_source_symbol_values": [
        "USDJPY"
      ],
      "actual_symbol_alias_compatible": true,
      "audit_status": "PASS",
      "candidate_ids": [
        "USDJPY_2026-04-24T00:16:10.771453+00:00"
      ],
      "candidate_window_checks": [
        {
          "candidate_id": "USDJPY_2026-04-24T00:16:10.771453+00:00",
          "candidate_utc": "2026-04-24T00:16:10.771453Z",
          "inside_actual_file_span": true,
          "inside_requested_utc_window": true
        }
      ],
      "exists_in_active_worktree": true,
      "field_availability_manifest": {
        "ask": true,
        "bid": true,
        "broker_symbol": true,
        "flags": true,
        "last": true,
        "source_symbol": true,
        "time_msc": true,
        "time_utc": true,
        "volume": true
      },
      "manifest_max_timestamp_utc": "2026-04-24T23:59:43.751000Z",
      "manifest_min_timestamp_utc": "2026-04-24T00:00:06.045000Z",
      "manifest_row_count": 125100,
      "manifest_sha256": "96ee076771334c44ea29560d2ddd2cb02563750147be045b58b96d71ae827479",
      "manifest_size_bytes": 2345690,
      "max_timestamp_matches_manifest": true,
      "min_timestamp_matches_manifest": true,
      "owner_request_id": "OWNER-TICK-0019",
      "parquet_schema_fields": [
        "time_utc",
        "time",
        "time_msc",
        "bid",
        "ask",
        "last",
        "volume",
        "flags",
        "volume_real",
        "source_symbol",
        "broker_symbol"
      ],
      "rehash_status": "REHASHED_LOCAL_SOURCE_FILE",
      "requested_window_end_utc": "2026-04-24T23:59:59.999999Z",
      "requested_window_start_utc": "2026-04-24T00:00:00Z",
      "row_count_matches_manifest": true,
      "sha256_matches_manifest": true,
      "size_matches_manifest": true,
      "source_date": "2026-04-24",
      "source_path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/USDJPY/2026-04-24.parquet",
      "symbol": "USDJPY",
      "symbol_compatibility": {
        "broker_symbol": "USDJPY",
        "requested_symbol": "USDJPY",
        "status": "exact_symbol_match"
      },
      "terminal_status": "RECOVERED_READONLY_MT5_SOURCE_HASHED",
      "window_coverage_status": "PASS_REHASHED_SOURCE_COVERS_REQUESTED_UTC_WINDOW_AND_CANDIDATES"
    },
    {
      "actual_broker_symbol_values": [
        "XAUUSD"
      ],
      "actual_in_requested_window_row_count": 602353,
      "actual_max_timestamp_utc": "2026-04-17T23:59:58.919000Z",
      "actual_min_timestamp_utc": "2026-04-17T01:00:00.749000Z",
      "actual_required_field_missing": [],
      "actual_row_count": 602353,
      "actual_sha256": "8c5ffc921bb811f78bdd16e43553d7a7650a6b1c862a70f18d23eebc42f9b0db",
      "actual_size_bytes": 8603256,
      "actual_source_symbol_values": [
        "XAUUSD"
      ],
      "actual_symbol_alias_compatible": true,
      "audit_status": "PASS",
      "candidate_ids": [
        "XAUUSD_2026-04-17T13:30:05.007149+00:00"
      ],
      "candidate_window_checks": [
        {
          "candidate_id": "XAUUSD_2026-04-17T13:30:05.007149+00:00",
          "candidate_utc": "2026-04-17T13:30:05.007149Z",
          "inside_actual_file_span": true,
          "inside_requested_utc_window": true
        }
      ],
      "exists_in_active_worktree": true,
      "field_availability_manifest": {
        "ask": true,
        "bid": true,
        "broker_symbol": true,
        "flags": true,
        "last": true,
        "source_symbol": true,
        "time_msc": true,
        "time_utc": true,
        "volume": true
      },
      "manifest_max_timestamp_utc": "2026-04-17T23:59:58.919000Z",
      "manifest_min_timestamp_utc": "2026-04-17T01:00:00.749000Z",
      "manifest_row_count": 602353,
      "manifest_sha256": "8c5ffc921bb811f78bdd16e43553d7a7650a6b1c862a70f18d23eebc42f9b0db",
      "manifest_size_bytes": 8603256,
      "max_timestamp_matches_manifest": true,
      "min_timestamp_matches_manifest": true,
      "owner_request_id": "OWNER-TICK-0022",
      "parquet_schema_fields": [
        "time_utc",
        "time",
        "time_msc",
        "bid",
        "ask",
        "last",
        "volume",
        "flags",
        "volume_real",
        "source_symbol",
        "broker_symbol"
      ],
      "rehash_status": "REHASHED_LOCAL_SOURCE_FILE",
      "requested_window_end_utc": "2026-04-17T23:59:59.999999Z",
      "requested_window_start_utc": "2026-04-17T00:00:00Z",
      "row_count_matches_manifest": true,
      "sha256_matches_manifest": true,
      "size_matches_manifest": true,
      "source_date": "2026-04-17",
      "source_path": "data/mt5_research_exports/nofill_readonly_tick_recovery_export_source_control_route/ticks/XAUUSD/2026-04-17.parquet",
      "symbol": "XAUUSD",
      "symbol_compatibility": {
        "broker_symbol": "XAUUSD",
        "requested_symbol": "XAUUSD",
        "status": "exact_symbol_match"
      },
      "terminal_status": "RECOVERED_READONLY_MT5_SOURCE_HASHED",
      "window_coverage_status": "PASS_REHASHED_SOURCE_COVERS_REQUESTED_UTC_WINDOW_AND_CANDIDATES"
    }
  ],
  "schema_version": "g12_nofill_readonly_tick_recovery_export_source_control_audit_v1",
  "target_source_manifest": "research/science_program_2026_05/06_outcome_testing/nofill_readonly_tick_recovery_export_source_control_route/NOFILL_READONLY_TICK_RECOVERY_SOURCE_HASH_MANIFEST_2026-05-10.json",
  "terminal_decision": "ACCEPT_AS_G12_READONLY_TICK_RECOVERY_SOURCE_CONTROL_AUDIT_WITH_NONPASSIVE_NEXT_ROUTE",
  "validation_safe": false,
  "window_or_schema_failure_count": 0
}
```
