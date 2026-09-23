# G12 NOFILL Readonly Tick Recovery Remaining Request Exhaustion Audit

Route: `G12_NOFILL_READONLY_TICK_RECOVERY_EXPORT_SOURCE_CONTROL_AUDIT`
Terminal decision: `ACCEPT_AS_G12_READONLY_TICK_RECOVERY_SOURCE_CONTROL_AUDIT_WITH_NONPASSIVE_NEXT_ROUTE`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

```json
{
  "artifact_family": "remaining_request_exhaustion_audit",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "exact_remaining_requests": [
    "XAUUSD|2026-04-15",
    "XAUUSD|2026-04-16"
  ],
  "exact_remaining_requests_match_expected": true,
  "generated_at_utc": "2026-05-10T10:17:24Z",
  "live_effect": false,
  "non_passive_next_route_required": true,
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
  "recovery_ladder_exhaustion_pass": true,
  "recovery_ladder_exhaustion_status": "ACCEPT_EXACT_REMAINING_MT5_TICK_REQUESTS_AFTER_SOURCE_SAFE_SEARCH_AND_READONLY_EXTRACTION",
  "remaining_candidate_row_count": 3,
  "remaining_owner_export_request_count": 2,
  "route_id": "G12_NOFILL_READONLY_TICK_RECOVERY_EXPORT_SOURCE_CONTROL_AUDIT",
  "schema_version": "g12_nofill_readonly_tick_recovery_export_source_control_audit_v1",
  "sierra_same_market_scid_audit": {
    "admitted_as_recovered_tick_source": false,
    "market_session_closure_explanation_ruled_out": true,
    "not_admitted_reason": "SCID rows prove same-market activity but do not satisfy the target MT5 bid/ask tick parquet field contract.",
    "scid_window_rows_present": true,
    "source_class": "SAME_MARKET_SIERRA_SCID_MARKET_DATA_NOT_MT5_BID_ASK_TICK_SCHEMA",
    "source_path": "C:\\SierraChart\\Data\\XAUUSD.scid",
    "windows": [
      {
        "end_utc": "2026-04-15T23:59:59.999999Z",
        "exists": true,
        "first_close": 4837.52001953125,
        "first_timestamp_utc": "2026-04-15T00:00:00.016000Z",
        "header": {
          "exists": true,
          "first_file_timestamp_utc": "2025-10-28T14:19:09.044000Z",
          "header_size": 56,
          "last_file_timestamp_utc": "2026-05-01T20:44:58.881000Z",
          "magic": "SCID",
          "path": "C:\\SierraChart\\Data\\XAUUSD.scid",
          "record_count": 9463561,
          "record_size": 40,
          "remainder_bytes": 0,
          "size_bytes": 378542496,
          "utc_start_index": 0,
          "version": 1
        },
        "last_close": 4823.599609375,
        "last_timestamp_utc": "2026-04-15T23:59:59.140000Z",
        "path": "C:\\SierraChart\\Data\\XAUUSD.scid",
        "rows": 72119,
        "start_utc": "2026-04-15T00:00:00Z",
        "status": "SCID_ROWS_PRESENT"
      },
      {
        "end_utc": "2026-04-16T23:59:59.999999Z",
        "exists": true,
        "first_close": 4824.1201171875,
        "first_timestamp_utc": "2026-04-16T00:00:00.016000Z",
        "header": {
          "exists": true,
          "first_file_timestamp_utc": "2025-10-28T14:19:09.044000Z",
          "header_size": 56,
          "last_file_timestamp_utc": "2026-05-01T20:44:58.881000Z",
          "magic": "SCID",
          "path": "C:\\SierraChart\\Data\\XAUUSD.scid",
          "record_count": 9463561,
          "record_size": 40,
          "remainder_bytes": 0,
          "size_bytes": 378542496,
          "utc_start_index": 0,
          "version": 1
        },
        "last_close": 4791.52001953125,
        "last_timestamp_utc": "2026-04-16T23:59:59.793000Z",
        "path": "C:\\SierraChart\\Data\\XAUUSD.scid",
        "rows": 70048,
        "start_utc": "2026-04-16T00:00:00Z",
        "status": "SCID_ROWS_PRESENT"
      }
    ]
  },
  "target_filename_search": {
    "all_targeted_raw_searches_clear": true,
    "raw_tick_or_csv_match_count": 0,
    "targeted_search_rows": [
      {
        "exists": true,
        "match_count": 0,
        "matches": [],
        "root_id": "active_worktree_data_root",
        "root_path": "C:\\tmp\\gtos_otb\\G12NOFILLTICKRECOVERY\\data",
        "search_policy": "targeted_xauusd_date_raw_parquet_csv_filename_search",
        "truncated": false
      },
      {
        "exists": true,
        "match_count": 0,
        "matches": [],
        "root_id": "active_worktree_tick_root",
        "root_path": "C:\\tmp\\gtos_otb\\G12NOFILLTICKRECOVERY\\data\\ticks",
        "search_policy": "targeted_xauusd_date_raw_parquet_csv_filename_search",
        "truncated": false
      },
      {
        "exists": true,
        "match_count": 0,
        "matches": [],
        "root_id": "active_worktree_ignored_extraction_root",
        "root_path": "C:\\tmp\\gtos_otb\\G12NOFILLTICKRECOVERY\\data\\mt5_research_exports\\nofill_readonly_tick_recovery_export_source_control_route",
        "search_policy": "targeted_xauusd_date_raw_parquet_csv_filename_search",
        "truncated": false
      },
      {
        "exists": true,
        "match_count": 0,
        "matches": [],
        "root_id": "absolute_main_data_root",
        "root_path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data",
        "search_policy": "targeted_xauusd_date_raw_parquet_csv_filename_search",
        "truncated": false
      },
      {
        "exists": true,
        "match_count": 0,
        "matches": [],
        "root_id": "prior_worktrees_root",
        "root_path": "C:\\tmp\\gtos_otb",
        "search_policy": "targeted_xauusd_date_raw_parquet_csv_filename_search",
        "truncated": false
      },
      {
        "exists": true,
        "match_count": 0,
        "matches": [],
        "root_id": "sierra_data_root",
        "root_path": "C:\\SierraChart\\Data",
        "search_policy": "targeted_xauusd_date_raw_parquet_csv_filename_search",
        "truncated": false
      }
    ]
  },
  "terminal_acceptance": "accepted_for_exact_mt5_tick_schema_only_with_sierra_alternate_source_next_route",
  "terminal_decision": "ACCEPT_AS_G12_READONLY_TICK_RECOVERY_SOURCE_CONTROL_AUDIT_WITH_NONPASSIVE_NEXT_ROUTE",
  "validation_safe": false,
  "zero_tick_rows": [
    {
      "absent_window_terminal_status": "OWNER_EXPORT_REQUIRED_AFTER_LOCAL_AND_READONLY_EXTRACTION",
      "broker_symbol": "XAUUSD",
      "candidate_boundary_checks": [
        {
          "candidate_id": "XAUUSD_2026-04-15T14:15:05.007998+00:00",
          "candidate_utc": "2026-04-15T14:15:05.007998Z",
          "contamination_or_embargo_blocked": false,
          "inside_requested_utc_day": true,
          "source_state_boundary_preserved": true
        }
      ],
      "candidate_ids": [
        "XAUUSD_2026-04-15T14:15:05.007998+00:00"
      ],
      "exact_remaining_key_ok": true,
      "extraction_api_call": "copy_ticks_range(COPY_TICKS_ALL)",
      "extraction_error_ruled_out": true,
      "extraction_rows": 0,
      "extraction_status": "NO_TICKS_EXPORTED",
      "last_error": "(1, 'Success')",
      "owner_request_id": "OWNER-TICK-0020",
      "probe_api_call": "copy_ticks_range(COPY_TICKS_ALL)",
      "probe_rows": 0,
      "probe_status": "NO_TICKS_RETURNED",
      "probe_symbol_select": true,
      "read_only_extraction_attempt_status": "NO_TICKS_EXPORTED",
      "requested_symbol": "XAUUSD",
      "source_date": "2026-04-15",
      "source_state_boundary_preserved": true,
      "source_symbol": "XAUUSD",
      "symbol": "XAUUSD",
      "symbol_select": true,
      "target_path_template": "data/ticks/XAUUSD/2026-04-15.parquet",
      "terminal_disconnected_ruled_out": true,
      "unavailable_symbol_ruled_out": true,
      "window_end_utc": "2026-04-15T23:59:59.999999Z",
      "window_start_utc": "2026-04-15T00:00:00Z",
      "wrong_symbol_ruled_out": true,
      "wrong_utc_day_ruled_out": true
    },
    {
      "absent_window_terminal_status": "OWNER_EXPORT_REQUIRED_AFTER_LOCAL_AND_READONLY_EXTRACTION",
      "broker_symbol": "XAUUSD",
      "candidate_boundary_checks": [
        {
          "candidate_id": "XAUUSD_2026-04-16T09:30:05.013547+00:00",
          "candidate_utc": "2026-04-16T09:30:05.013547Z",
          "contamination_or_embargo_blocked": true,
          "inside_requested_utc_day": true,
          "source_state_boundary_preserved": true
        },
        {
          "candidate_id": "XAUUSD_2026-04-16T13:16:01.126537+00:00",
          "candidate_utc": "2026-04-16T13:16:01.126537Z",
          "contamination_or_embargo_blocked": true,
          "inside_requested_utc_day": true,
          "source_state_boundary_preserved": true
        }
      ],
      "candidate_ids": [
        "XAUUSD_2026-04-16T09:30:05.013547+00:00",
        "XAUUSD_2026-04-16T13:16:01.126537+00:00"
      ],
      "exact_remaining_key_ok": true,
      "extraction_api_call": "copy_ticks_range(COPY_TICKS_ALL)",
      "extraction_error_ruled_out": true,
      "extraction_rows": 0,
      "extraction_status": "NO_TICKS_EXPORTED",
      "last_error": "(1, 'Success')",
      "owner_request_id": "OWNER-TICK-0021",
      "probe_api_call": "copy_ticks_range(COPY_TICKS_ALL)",
      "probe_rows": 0,
      "probe_status": "NO_TICKS_RETURNED",
      "probe_symbol_select": true,
      "read_only_extraction_attempt_status": "NO_TICKS_EXPORTED",
      "requested_symbol": "XAUUSD",
      "source_date": "2026-04-16",
      "source_state_boundary_preserved": true,
      "source_symbol": "XAUUSD",
      "symbol": "XAUUSD",
      "symbol_select": true,
      "target_path_template": "data/ticks/XAUUSD/2026-04-16.parquet",
      "terminal_disconnected_ruled_out": true,
      "unavailable_symbol_ruled_out": true,
      "window_end_utc": "2026-04-16T23:59:59.999999Z",
      "window_start_utc": "2026-04-16T00:00:00Z",
      "wrong_symbol_ruled_out": true,
      "wrong_utc_day_ruled_out": true
    }
  ]
}
```
