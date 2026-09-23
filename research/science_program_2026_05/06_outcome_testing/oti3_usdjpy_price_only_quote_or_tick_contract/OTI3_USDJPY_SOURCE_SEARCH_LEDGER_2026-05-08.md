# OTI3 USDJPY Source Search Ledger - 2026-05-08

Promotion verdict: `NO_PROMOTION_VERDICT`
Validation safe: `false`
Outcome review opened: `false`
Live effect: `false`

- Local heavy-data search checked worktree, absolute main repo tick cache, C:\tmp worktrees, and C:\Users\MSI\Documents parquet candidates.

```json
{
  "access_request_row_ids": [
    "NOFILL-CLOSE-ROW-0129",
    "NOFILL-CLOSE-ROW-0130",
    "NOFILL-CLOSE-ROW-0131",
    "NOFILL-CLOSE-ROW-0163",
    "NOFILL-CLOSE-ROW-0164",
    "NOFILL-CLOSE-ROW-0165",
    "NOFILL-CLOSE-ROW-0166"
  ],
  "approved_extraction_dates": [
    "2026-04-17",
    "2026-04-20"
  ],
  "artifact_family": "OTI3_USDJPY_SOURCE_SEARCH_LEDGER",
  "final_tick_source_by_date": {
    "2026-04-17": "C:\\tmp\\gtos_otb\\OTI3USDJPY\\research\\science_program_2026_05\\06_outcome_testing\\oti3_usdjpy_price_only_quote_or_tick_contract\\OTI3_MT5_READ_ONLY_USDJPY_TICKS_2026-04-17.parquet",
    "2026-04-20": "C:\\tmp\\gtos_otb\\OTI3USDJPY\\research\\science_program_2026_05\\06_outcome_testing\\oti3_usdjpy_price_only_quote_or_tick_contract\\OTI3_MT5_READ_ONLY_USDJPY_TICKS_2026-04-20.parquet",
    "2026-04-30": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\USDJPY\\2026-04-30.parquet",
    "2026-05-01": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\USDJPY\\2026-05-01.parquet"
  },
  "final_tick_source_inspection_by_date": {
    "2026-04-17": {
      "coverage_status": "COVERS_REQUESTED_DECISION_DATE",
      "date_row_count": 138040,
      "decision_coverage": {
        "2026-04-17T00:15:00Z": true
      },
      "exists": true,
      "last_write_utc": "2026-05-08T14:57:04.341702+00:00",
      "max_ts_utc": "2026-04-17T23:59:35.086000Z",
      "min_ts_utc": "2026-04-17T00:00:09.858000Z",
      "path": "C:\\tmp\\gtos_otb\\OTI3USDJPY\\research\\science_program_2026_05\\06_outcome_testing\\oti3_usdjpy_price_only_quote_or_tick_contract\\OTI3_MT5_READ_ONLY_USDJPY_TICKS_2026-04-17.parquet",
      "row_count": 138040,
      "schema_columns": [
        "ts_utc",
        "ts_msc",
        "bid",
        "ask",
        "last",
        "volume",
        "flags",
        "mt5_symbol",
        "timestamp_mode"
      ],
      "sha256": "ff7db8dc50f7f7083557f54fc539aff951583f35ffab9f711ecb7af85aa27622",
      "size_bytes": 2209369
    },
    "2026-04-20": {
      "coverage_status": "COVERS_REQUESTED_DECISION_DATE",
      "date_row_count": 129746,
      "decision_coverage": {
        "2026-04-20T00:15:00Z": true,
        "2026-04-20T02:15:00Z": true
      },
      "exists": true,
      "last_write_utc": "2026-05-08T14:57:04.493546+00:00",
      "max_ts_utc": "2026-04-20T23:59:56.531000Z",
      "min_ts_utc": "2026-04-20T00:00:07.518000Z",
      "path": "C:\\tmp\\gtos_otb\\OTI3USDJPY\\research\\science_program_2026_05\\06_outcome_testing\\oti3_usdjpy_price_only_quote_or_tick_contract\\OTI3_MT5_READ_ONLY_USDJPY_TICKS_2026-04-20.parquet",
      "row_count": 129746,
      "schema_columns": [
        "ts_utc",
        "ts_msc",
        "bid",
        "ask",
        "last",
        "volume",
        "flags",
        "mt5_symbol",
        "timestamp_mode"
      ],
      "sha256": "13951dcfc7a0dd14783cadd18782bb2caec1573601c6b6e49d53da8f261d2fb9",
      "size_bytes": 2045401
    },
    "2026-04-30": {
      "coverage_status": "COVERS_REQUESTED_DECISION_DATE",
      "date_row_count": 244837,
      "decision_coverage": {
        "2026-04-30T00:15:00Z": true,
        "2026-04-30T00:30:00Z": true,
        "2026-04-30T13:45:00Z": true,
        "2026-04-30T14:00:00Z": true,
        "2026-04-30T14:15:00Z": true,
        "2026-04-30T14:30:00Z": true,
        "2026-04-30T14:45:00Z": true,
        "2026-04-30T15:00:00Z": true,
        "2026-04-30T15:15:00Z": true,
        "2026-04-30T15:30:00Z": true
      },
      "exists": true,
      "last_write_utc": "2026-05-01T00:00:01.123979+00:00",
      "max_ts_utc": "2026-04-30T23:59:56.312000Z",
      "min_ts_utc": "2026-04-30T00:00:00.402000Z",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\USDJPY\\2026-04-30.parquet",
      "row_count": 244837,
      "schema_columns": [
        "ts_utc",
        "ts_msc",
        "bid",
        "ask",
        "last",
        "volume",
        "flags",
        "inferred_aggressor"
      ],
      "sha256": "a48099563df87d2b2654ccae9c235917024dbbf32817eed5997880d15c544bce",
      "size_bytes": 3908592
    },
    "2026-05-01": {
      "coverage_status": "COVERS_REQUESTED_DECISION_DATE",
      "date_row_count": 163765,
      "decision_coverage": {
        "2026-05-01T00:15:00Z": true,
        "2026-05-01T00:30:00Z": true,
        "2026-05-01T00:45:00Z": true,
        "2026-05-01T01:00:00Z": true,
        "2026-05-01T01:15:00Z": true,
        "2026-05-01T01:45:00Z": true,
        "2026-05-01T02:00:00Z": true,
        "2026-05-01T02:15:00Z": true,
        "2026-05-01T02:30:00Z": true,
        "2026-05-01T02:45:00Z": true,
        "2026-05-01T03:00:00Z": true,
        "2026-05-01T08:15:00Z": true,
        "2026-05-01T09:15:00Z": true,
        "2026-05-01T09:30:00Z": true,
        "2026-05-01T13:15:00Z": true,
        "2026-05-01T14:00:00Z": true,
        "2026-05-01T14:15:00Z": true,
        "2026-05-01T14:45:00Z": true,
        "2026-05-01T15:00:00Z": true,
        "2026-05-01T15:15:00Z": true,
        "2026-05-01T15:30:00Z": true
      },
      "exists": true,
      "last_write_utc": "2026-05-03T23:46:11.814101+00:00",
      "max_ts_utc": "2026-05-01T20:59:01.601000Z",
      "min_ts_utc": "2026-05-01T00:00:00.335000Z",
      "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\USDJPY\\2026-05-01.parquet",
      "row_count": 163765,
      "schema_columns": [
        "ts_utc",
        "ts_msc",
        "bid",
        "ask",
        "last",
        "volume",
        "flags",
        "inferred_aggressor"
      ],
      "sha256": "7d13dd73d30a2fb5964b14e688d9aa9a4425828f6901067c1f04e36321430456",
      "size_bytes": 2768379
    }
  },
  "forbidden_surfaces": {
    "account_history_accessed": false,
    "broker_actual_r_accessed": false,
    "live_trade_result_accessed": false,
    "mt5_account_calls": 0,
    "mt5_history_calls": 0,
    "mt5_order_calls": 0,
    "mt5_position_calls": 0,
    "order_send_calls": 0,
    "paid_api_or_databento_calls": 0
  },
  "generated_at_utc": "2026-05-08T14:57:27Z",
  "initial_tick_source_probe_by_date": {
    "2026-04-17": {
      "all_exact_candidates": [
        "C:\\tmp\\gtos_otb\\OTI3USDJPY\\data\\ticks\\USDJPY\\2026-04-17.parquet",
        "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\USDJPY\\2026-04-17.parquet"
      ],
      "selected_existing_source": null,
      "selected_existing_source_inspection": null
    },
    "2026-04-20": {
      "all_exact_candidates": [
        "C:\\tmp\\gtos_otb\\OTI3USDJPY\\data\\ticks\\USDJPY\\2026-04-20.parquet",
        "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\USDJPY\\2026-04-20.parquet"
      ],
      "selected_existing_source": null,
      "selected_existing_source_inspection": null
    },
    "2026-04-30": {
      "all_exact_candidates": [
        "C:\\tmp\\gtos_otb\\OTI3USDJPY\\data\\ticks\\USDJPY\\2026-04-30.parquet",
        "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\USDJPY\\2026-04-30.parquet"
      ],
      "selected_existing_source": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\USDJPY\\2026-04-30.parquet",
      "selected_existing_source_inspection": {
        "coverage_status": "COVERS_REQUESTED_DECISION_DATE",
        "date_row_count": 244837,
        "decision_coverage": {
          "2026-04-30T00:15:00Z": true,
          "2026-04-30T00:30:00Z": true,
          "2026-04-30T13:45:00Z": true,
          "2026-04-30T14:00:00Z": true,
          "2026-04-30T14:15:00Z": true,
          "2026-04-30T14:30:00Z": true,
          "2026-04-30T14:45:00Z": true,
          "2026-04-30T15:00:00Z": true,
          "2026-04-30T15:15:00Z": true,
          "2026-04-30T15:30:00Z": true
        },
        "exists": true,
        "last_write_utc": "2026-05-01T00:00:01.123979+00:00",
        "max_ts_utc": "2026-04-30T23:59:56.312000Z",
        "min_ts_utc": "2026-04-30T00:00:00.402000Z",
        "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\USDJPY\\2026-04-30.parquet",
        "row_count": 244837,
        "schema_columns": [
          "ts_utc",
          "ts_msc",
          "bid",
          "ask",
          "last",
          "volume",
          "flags",
          "inferred_aggressor"
        ],
        "sha256": "a48099563df87d2b2654ccae9c235917024dbbf32817eed5997880d15c544bce",
        "size_bytes": 3908592
      }
    },
    "2026-05-01": {
      "all_exact_candidates": [
        "C:\\tmp\\gtos_otb\\OTI3USDJPY\\data\\ticks\\USDJPY\\2026-05-01.parquet",
        "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\USDJPY\\2026-05-01.parquet"
      ],
      "selected_existing_source": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\USDJPY\\2026-05-01.parquet",
      "selected_existing_source_inspection": {
        "coverage_status": "COVERS_REQUESTED_DECISION_DATE",
        "date_row_count": 163765,
        "decision_coverage": {
          "2026-05-01T00:15:00Z": true,
          "2026-05-01T00:30:00Z": true,
          "2026-05-01T00:45:00Z": true,
          "2026-05-01T01:00:00Z": true,
          "2026-05-01T01:15:00Z": true,
          "2026-05-01T01:45:00Z": true,
          "2026-05-01T02:00:00Z": true,
          "2026-05-01T02:15:00Z": true,
          "2026-05-01T02:30:00Z": true,
          "2026-05-01T02:45:00Z": true,
          "2026-05-01T03:00:00Z": true,
          "2026-05-01T08:15:00Z": true,
          "2026-05-01T09:15:00Z": true,
          "2026-05-01T09:30:00Z": true,
          "2026-05-01T13:15:00Z": true,
          "2026-05-01T14:00:00Z": true,
          "2026-05-01T14:15:00Z": true,
          "2026-05-01T14:45:00Z": true,
          "2026-05-01T15:00:00Z": true,
          "2026-05-01T15:15:00Z": true,
          "2026-05-01T15:30:00Z": true
        },
        "exists": true,
        "last_write_utc": "2026-05-03T23:46:11.814101+00:00",
        "max_ts_utc": "2026-05-01T20:59:01.601000Z",
        "min_ts_utc": "2026-05-01T00:00:00.335000Z",
        "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\USDJPY\\2026-05-01.parquet",
        "row_count": 163765,
        "schema_columns": [
          "ts_utc",
          "ts_msc",
          "bid",
          "ask",
          "last",
          "volume",
          "flags",
          "inferred_aggressor"
        ],
        "sha256": "7d13dd73d30a2fb5964b14e688d9aa9a4425828f6901067c1f04e36321430456",
        "size_bytes": 2768379
      }
    }
  },
  "lane_id": "OTI3_USDJPY_PRICE_ONLY_QUOTE_OR_TICK_CONTRACT",
  "live_effect": false,
  "mt5_read_only_extraction_attempts": [
    {
      "account_info_called": false,
      "allowed_by_owner_prompt": true,
      "attempted": true,
      "coverage_status": "RECOVERED_ROWS_FROM_READ_ONLY_MT5_COPY_TICKS_RANGE",
      "date": "2026-04-17",
      "history_deals_get_called": false,
      "history_orders_get_called": false,
      "initialize_returned": true,
      "last_error_after_copy_ticks_range": "(1, 'Success')",
      "last_error_after_initialize": "(1, 'Success')",
      "order_send_called": false,
      "orders_get_called": false,
      "output_path": "C:\\tmp\\gtos_otb\\OTI3USDJPY\\research\\science_program_2026_05\\06_outcome_testing\\oti3_usdjpy_price_only_quote_or_tick_contract\\OTI3_MT5_READ_ONLY_USDJPY_TICKS_2026-04-17.parquet",
      "output_sha256": "ff7db8dc50f7f7083557f54fc539aff951583f35ffab9f711ecb7af85aa27622",
      "output_size_bytes": 2209369,
      "paid_api_or_databento_called": false,
      "positions_get_called": false,
      "query_end_utc": "2026-04-18T00:00:00+00:00",
      "query_start_utc": "2026-04-17T00:00:00+00:00",
      "requested_date_row_count": 138040,
      "route": "MetaTrader5.copy_ticks_range",
      "rows": 138040,
      "source_first_ts_utc": "2026-04-17T00:00:09.858000Z",
      "source_last_ts_utc": "2026-04-17T23:59:35.086000Z",
      "symbol": "USDJPY",
      "timestamp_policy": "copy_ticks_range_time_msc_used_as_utc_when_returned_ticks_align_with_requested_utc_window"
    },
    {
      "account_info_called": false,
      "allowed_by_owner_prompt": true,
      "attempted": true,
      "coverage_status": "RECOVERED_ROWS_FROM_READ_ONLY_MT5_COPY_TICKS_RANGE",
      "date": "2026-04-20",
      "history_deals_get_called": false,
      "history_orders_get_called": false,
      "initialize_returned": true,
      "last_error_after_copy_ticks_range": "(1, 'Success')",
      "last_error_after_initialize": "(1, 'Success')",
      "order_send_called": false,
      "orders_get_called": false,
      "output_path": "C:\\tmp\\gtos_otb\\OTI3USDJPY\\research\\science_program_2026_05\\06_outcome_testing\\oti3_usdjpy_price_only_quote_or_tick_contract\\OTI3_MT5_READ_ONLY_USDJPY_TICKS_2026-04-20.parquet",
      "output_sha256": "13951dcfc7a0dd14783cadd18782bb2caec1573601c6b6e49d53da8f261d2fb9",
      "output_size_bytes": 2045401,
      "paid_api_or_databento_called": false,
      "positions_get_called": false,
      "query_end_utc": "2026-04-21T00:00:00+00:00",
      "query_start_utc": "2026-04-20T00:00:00+00:00",
      "requested_date_row_count": 129746,
      "route": "MetaTrader5.copy_ticks_range",
      "rows": 129746,
      "source_first_ts_utc": "2026-04-20T00:00:07.518000Z",
      "source_last_ts_utc": "2026-04-20T23:59:56.531000Z",
      "symbol": "USDJPY",
      "timestamp_policy": "copy_ticks_range_time_msc_used_as_utc_when_returned_ticks_align_with_requested_utc_window"
    }
  ],
  "needed_dates": [
    "2026-04-17",
    "2026-04-20",
    "2026-04-30",
    "2026-05-01"
  ],
  "no_r_performance_scoring": true,
  "outcome_review_opened": false,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "repo_head": "9cad99c83bc12bf84a569ac82d579aa6ee978dc9",
  "row_count": 69,
  "schema_version": "oti3_usdjpy_price_only_quote_or_tick_contract_v1",
  "scope": "source_correction_or_contract_revision_only",
  "search_conclusion": "quote_tick_sources_present_for_all_needed_dates",
  "targeted_recursive_searches": [
    {
      "errors": [
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos-pytest"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos_pytest_limit"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos_pytest_limit2"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos_pytest_live"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos_pytest_live2"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos_pytest_pending_lifecycle_20260504_1435"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos_pytest_pending_lifecycle_20260504_1436"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos_pytest_pending_lifecycle_20260504_1440"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos_pytest_remaining_fixes_20260502a"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos_pytest_remaining_fixes_20260502b"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos_pytest_shadow_health_20260504_1359_escalated"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos_pytest_shadow_health_20260504_1410"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos_pytest_shadow_integrity_pending_join"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos_pytest_sierra_enrich"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos_pytest_sierra_enrich_final"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos_pytest_watchdog_canary_skip"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos_pytest_xau_incident2"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos_pytest_xau_incident_full"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-basetemp"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-codex-l4-debate"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-codex-sierra-scid"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-databento-live-smoke"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto007"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto008"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto009"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto010"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto010-unit"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto011"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto012"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto012-013-final"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto013"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto014"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto014-final"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto015"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto015-2"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto015-export"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto015-final"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto015-time"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto016"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto017"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto018"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto019-initial"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto019-verify"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto020-initial"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto020-verify"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto021"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto022"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto025"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto026"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto030"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto033"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto036"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto037-final"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto037-initial"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto038-final"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto038-initial"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-mbo"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-of-MSI"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-orderflow-plan"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-sierra-fix"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-sierra-symbol"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest_g0_oti_merge"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest_g12_otb_reaudit_merge"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest_g12_oti_post_test_merge"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest_otb2g10_merge"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest_otb_packet_merge"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest_otb_rebuild_merge"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest_oti1_covariate"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest_oti_result_merge"
        }
      ],
      "exists": true,
      "match_count": 1,
      "matches": [
        {
          "exists": true,
          "last_write_utc": "2026-05-08T14:57:04.341702+00:00",
          "path": "C:\\tmp\\gtos_otb\\OTI3USDJPY\\research\\science_program_2026_05\\06_outcome_testing\\oti3_usdjpy_price_only_quote_or_tick_contract\\OTI3_MT5_READ_ONLY_USDJPY_TICKS_2026-04-17.parquet",
          "sha256": "ff7db8dc50f7f7083557f54fc539aff951583f35ffab9f711ecb7af85aa27622",
          "size_bytes": 2209369
        }
      ],
      "root": "C:\\tmp",
      "tokens": [
        "USDJPY",
        "2026-04-17",
        "parquet"
      ],
      "truncated": false
    },
    {
      "errors": [
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos-pytest"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos_pytest_limit"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos_pytest_limit2"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos_pytest_live"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos_pytest_live2"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos_pytest_pending_lifecycle_20260504_1435"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos_pytest_pending_lifecycle_20260504_1436"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos_pytest_pending_lifecycle_20260504_1440"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos_pytest_remaining_fixes_20260502a"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos_pytest_remaining_fixes_20260502b"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos_pytest_shadow_health_20260504_1359_escalated"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos_pytest_shadow_health_20260504_1410"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos_pytest_shadow_integrity_pending_join"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos_pytest_sierra_enrich"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos_pytest_sierra_enrich_final"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos_pytest_watchdog_canary_skip"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos_pytest_xau_incident2"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos_pytest_xau_incident_full"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-basetemp"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-codex-l4-debate"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-codex-sierra-scid"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-databento-live-smoke"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto007"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto008"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto009"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto010"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto010-unit"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto011"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto012"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto012-013-final"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto013"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto014"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto014-final"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto015"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto015-2"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto015-export"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto015-final"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto015-time"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto016"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto017"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto018"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto019-initial"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto019-verify"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto020-initial"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto020-verify"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto021"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto022"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto025"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto026"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto030"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto033"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto036"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto037-final"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto037-initial"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto038-final"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto038-initial"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-mbo"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-of-MSI"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-orderflow-plan"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-sierra-fix"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-sierra-symbol"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest_g0_oti_merge"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest_g12_otb_reaudit_merge"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest_g12_oti_post_test_merge"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest_otb2g10_merge"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest_otb_packet_merge"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest_otb_rebuild_merge"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest_oti1_covariate"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest_oti_result_merge"
        }
      ],
      "exists": true,
      "match_count": 1,
      "matches": [
        {
          "exists": true,
          "last_write_utc": "2026-05-08T14:57:04.493546+00:00",
          "path": "C:\\tmp\\gtos_otb\\OTI3USDJPY\\research\\science_program_2026_05\\06_outcome_testing\\oti3_usdjpy_price_only_quote_or_tick_contract\\OTI3_MT5_READ_ONLY_USDJPY_TICKS_2026-04-20.parquet",
          "sha256": "13951dcfc7a0dd14783cadd18782bb2caec1573601c6b6e49d53da8f261d2fb9",
          "size_bytes": 2045401
        }
      ],
      "root": "C:\\tmp",
      "tokens": [
        "USDJPY",
        "2026-04-20",
        "parquet"
      ],
      "truncated": false
    },
    {
      "errors": [
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos-pytest"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos_pytest_limit"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos_pytest_limit2"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos_pytest_live"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos_pytest_live2"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos_pytest_pending_lifecycle_20260504_1435"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos_pytest_pending_lifecycle_20260504_1436"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos_pytest_pending_lifecycle_20260504_1440"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos_pytest_remaining_fixes_20260502a"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos_pytest_remaining_fixes_20260502b"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos_pytest_shadow_health_20260504_1359_escalated"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos_pytest_shadow_health_20260504_1410"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos_pytest_shadow_integrity_pending_join"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos_pytest_sierra_enrich"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos_pytest_sierra_enrich_final"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos_pytest_watchdog_canary_skip"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos_pytest_xau_incident2"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos_pytest_xau_incident_full"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-basetemp"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-codex-l4-debate"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-codex-sierra-scid"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-databento-live-smoke"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto007"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto008"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto009"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto010"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto010-unit"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto011"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto012"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto012-013-final"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto013"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto014"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto014-final"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto015"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto015-2"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto015-export"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto015-final"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto015-time"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto016"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto017"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto018"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto019-initial"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto019-verify"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto020-initial"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto020-verify"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto021"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto022"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto025"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto026"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto030"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto033"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto036"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto037-final"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto037-initial"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto038-final"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto038-initial"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-mbo"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-of-MSI"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-orderflow-plan"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-sierra-fix"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-sierra-symbol"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest_g0_oti_merge"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest_g12_otb_reaudit_merge"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest_g12_oti_post_test_merge"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest_otb2g10_merge"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest_otb_packet_merge"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest_otb_rebuild_merge"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest_oti1_covariate"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest_oti_result_merge"
        }
      ],
      "exists": true,
      "match_count": 0,
      "matches": [],
      "root": "C:\\tmp",
      "tokens": [
        "USDJPY",
        "2026-04-30",
        "parquet"
      ],
      "truncated": false
    },
    {
      "errors": [
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos-pytest"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos_pytest_limit"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos_pytest_limit2"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos_pytest_live"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos_pytest_live2"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos_pytest_pending_lifecycle_20260504_1435"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos_pytest_pending_lifecycle_20260504_1436"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos_pytest_pending_lifecycle_20260504_1440"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos_pytest_remaining_fixes_20260502a"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos_pytest_remaining_fixes_20260502b"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos_pytest_shadow_health_20260504_1359_escalated"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos_pytest_shadow_health_20260504_1410"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos_pytest_shadow_integrity_pending_join"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos_pytest_sierra_enrich"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos_pytest_sierra_enrich_final"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos_pytest_watchdog_canary_skip"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos_pytest_xau_incident2"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\gtos_pytest_xau_incident_full"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-basetemp"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-codex-l4-debate"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-codex-sierra-scid"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-databento-live-smoke"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto007"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto008"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto009"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto010"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto010-unit"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto011"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto012"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto012-013-final"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto013"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto014"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto014-final"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto015"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto015-2"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto015-export"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto015-final"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto015-time"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto016"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto017"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto018"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto019-initial"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto019-verify"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto020-initial"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto020-verify"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto021"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto022"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto025"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto026"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto030"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto033"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto036"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto037-final"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto037-initial"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto038-final"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-lto038-initial"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-mbo"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-of-MSI"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-orderflow-plan"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-sierra-fix"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest-sierra-symbol"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest_g0_oti_merge"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest_g12_otb_reaudit_merge"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest_g12_oti_post_test_merge"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest_otb2g10_merge"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest_otb_packet_merge"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest_otb_rebuild_merge"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest_oti1_covariate"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\tmp\\pytest_oti_result_merge"
        }
      ],
      "exists": true,
      "match_count": 0,
      "matches": [],
      "root": "C:\\tmp",
      "tokens": [
        "USDJPY",
        "2026-05-01",
        "parquet"
      ],
      "truncated": false
    },
    {
      "errors": [
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.codex_tmp_watchdog_tests\\basetemp2"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.codex_tmp_watchdog_tests\\basetemp3"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\_codex_pytest_trade_record_backfill_1325_escalated"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\Users\\MSI\\Documents\\My Music"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\Users\\MSI\\Documents\\My Pictures"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\Users\\MSI\\Documents\\My Videos"
        }
      ],
      "exists": true,
      "match_count": 0,
      "matches": [],
      "root": "C:\\Users\\MSI\\Documents",
      "tokens": [
        "USDJPY",
        "2026-04-17",
        "parquet"
      ],
      "truncated": false
    },
    {
      "errors": [
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.codex_tmp_watchdog_tests\\basetemp2"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\.codex_tmp_watchdog_tests\\basetemp3"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\_codex_pytest_trade_record_backfill_1325_escalated"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\Users\\MSI\\Documents\\My Music"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\Users\\MSI\\Documents\\My Pictures"
        },
        {
          "error": "PermissionError(13, 'Access is denied')",
          "filename": "C:\\Users\\MSI\\Documents\\My Videos"
        }
      ],
      "exists": true,
      "match_count": 0,
      "matches": [],
      "root": "C:\\Users\\MSI\\Documents",
      "tokens": [
        "USDJPY",
        "2026-04-20",
        "parquet"
      ],
      "truncated": false
    }
  ],
  "usdjpy_m1_context_source": {
    "exists": true,
    "last_write_utc": "2026-05-02T07:28:22.591448+00:00",
    "path": "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\mt5_research_exports\\phase3_v2b_forward_20260401_20260502_readonly\\USDJPY_M1.csv",
    "sha256": "9a16ad55351131b0675bbc83390059deeb3ee6b669b42f848219cee7b47b5519",
    "size_bytes": 1832342
  },
  "validation_safe": false
}
```
