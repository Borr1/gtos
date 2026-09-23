# G12 OTR061 Packet Recovery Audit - 2026-05-07

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `false`  
**Outcome review opened:** `false`  
**Live effect:** `false`

- Directly verifies the recovered XAUUSD parquet hash, row count, decision quote, and ordered path.
- Accepts the packet only for a future quarantined result audit.

```json
{
  "artifact_family": "G12_OTR061_PACKET_RECOVERY_AUDIT",
  "audit_verdict": "PASS_ACCEPT_INPUT_PACKET_FOR_FUTURE_QUARANTINED_RESULT_AUDIT",
  "forbidden_surface_review": {
    "account_history_accessed": false,
    "all_used_files_hashed": true,
    "api_calls": 0,
    "broker_actual_r_accessed": false,
    "databento_calls": 0,
    "live_order_state_accessed": false,
    "mt5_order_calls": 0,
    "paid_data_calls": 0
  },
  "generated_at_utc": "2026-05-07T09:59:44Z",
  "live_effect": false,
  "otr061_terminal_state": "RECOVERY_PACKET_READY_FOR_G12_REAUDIT",
  "outcome_review_opened": false,
  "packet_fields": {
    "decision_quote_packet": {
      "ask": 4648.29,
      "bid": 4647.65,
      "decision_asof_utc": "2026-05-06T07:15:00+00:00",
      "executable_decision_price": 4648.29,
      "executable_price_rule": "LONG_uses_ask_SHORT_uses_bid_market_entry",
      "mid": 4647.969999999999,
      "quote_status": "DECISION_QUOTE_FOUND_FROM_SOURCE_HASHED_MT5_EXPORT",
      "quote_timestamp_utc": "2026-05-06T07:14:59.889000+00:00",
      "schema_id": "decision_quote_asof_v1",
      "side": "LONG",
      "source_file": "C:\\tmp\\gtos_otb\\OTR061TICK\\research\\science_program_2026_05\\06_outcome_testing\\otr061_xau_tick_recovery\\OTR061_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_0710_1115.parquet",
      "source_sha256": "6f7e7e7e19635275916c78bb98678edf5f0cd80bebf2babd9f73017c740398ff",
      "spread": 0.6400000000003274
    },
    "label_family": "input_only_features_no_labels",
    "no_result_fields_assertion": true,
    "ordered_tick_path_packet": {
      "no_result_fields_assertion": true,
      "ordered_path_materialization": "source_file_filtered_by_ts_utc_between_path_start_and_path_end_inclusive",
      "path_end_utc": "2026-05-06T11:15:00+00:00",
      "path_first_timestamp_utc": "2026-05-06T07:15:00.634000+00:00",
      "path_last_timestamp_utc": "2026-05-06T11:14:59.900000+00:00",
      "path_row_count": 88060,
      "path_source_files": [
        "C:\\tmp\\gtos_otb\\OTR061TICK\\research\\science_program_2026_05\\06_outcome_testing\\otr061_xau_tick_recovery\\OTR061_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_0710_1115.parquet"
      ],
      "path_source_sha256": {
        "C:\\tmp\\gtos_otb\\OTR061TICK\\research\\science_program_2026_05\\06_outcome_testing\\otr061_xau_tick_recovery\\OTR061_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_0710_1115.parquet": "6f7e7e7e19635275916c78bb98678edf5f0cd80bebf2babd9f73017c740398ff"
      },
      "path_source_type": "mt5_copy_ticks_range_quote_stream",
      "path_start_utc": "2026-05-06T07:15:00+00:00",
      "path_status": "ORDERED_TICK_PATH_FOUND_FROM_SOURCE_HASHED_MT5_EXPORT",
      "post_horizon_first_timestamp_utc": "2026-05-06T11:15:00.335000+00:00",
      "row_order": "ts_utc_ascending_preserving_mt5_tick_order",
      "schema_id": "ordered_tick_path_asof_v1",
      "source_query_first_timestamp_utc": "2026-05-06T07:10:01.820000+00:00",
      "source_query_last_timestamp_utc": "2026-05-06T11:15:59.763000+00:00",
      "source_reaches_required_end": true
    },
    "prior_duplicate_group_id_for_future_denominator": "G6_CNR|XAUUSD|2026-05-06|london|LONG|4561.52",
    "record_count": 1,
    "record_id": "OTG0-PKT-061|XAUUSD_2026-05-06T07:15:00+00:00",
    "schema": "continuation_no_retrace_decision_price_path_v1"
  },
  "packet_id": "OTG0-PKT-061",
  "parquet_direct_verification": {
    "columns": [
      "ts_utc",
      "time",
      "bid",
      "ask",
      "last",
      "volume",
      "time_msc",
      "flags",
      "volume_real",
      "mt5_symbol"
    ],
    "decision_quote": {
      "ask": 4648.29,
      "bid": 4647.65,
      "decision_rows_lte_071500": 875,
      "executable_decision_price_long_ask": 4648.29,
      "quote_timestamp_utc": "2026-05-06T07:14:59.889000Z"
    },
    "exists": true,
    "first_ask": 4646.56,
    "first_bid": 4645.91,
    "first_tick_utc": "2026-05-06T07:10:01.820000Z",
    "last_ask": 4680.59,
    "last_bid": 4680.02,
    "last_tick_utc": "2026-05-06T11:15:59.763000Z",
    "ordered_path": {
      "first_timestamp_utc": "2026-05-06T07:15:00.634000Z",
      "last_timestamp_utc": "2026-05-06T11:14:59.900000Z",
      "post_horizon_first_timestamp_utc": "2026-05-06T11:15:00.335000Z",
      "row_count": 88060
    },
    "path": "C:\\tmp\\gtos_otb\\G12OTI5OTR061\\research\\science_program_2026_05\\06_outcome_testing\\otr061_xau_tick_recovery\\OTR061_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_0710_1115.parquet",
    "required_window": {
      "first_timestamp_utc": "2026-05-06T07:10:01.820000Z",
      "last_timestamp_utc": "2026-05-06T11:14:59.900000Z",
      "row_count": 88935
    },
    "row_count": 89391,
    "sha256": "6f7e7e7e19635275916c78bb98678edf5f0cd80bebf2babd9f73017c740398ff"
  },
  "path_relocation_note": {
    "current_worktree_parquet_path": "C:\\tmp\\gtos_otb\\G12OTI5OTR061\\research\\science_program_2026_05\\06_outcome_testing\\otr061_xau_tick_recovery\\OTR061_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_0710_1115.parquet",
    "same_sha256_in_current_worktree": true,
    "source_ledger_original_path": "C:\\tmp\\gtos_otb\\OTR061TICK\\research\\science_program_2026_05\\06_outcome_testing\\otr061_xau_tick_recovery\\OTR061_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_0710_1115.parquet"
  },
  "previous_blocker_answered": {
    "answer": "The prior OTG0-PKT-061 blocker for exact executable decision price plus ordered tick path is cleared for this one XAUUSD record by a source-hashed read-only MT5 tick export.",
    "remaining_boundary": "No result outcome is scored here; future continuation/no-retrace result lane must re-use the frozen packet, preserve label separation, and pass duplicate/source/no-leak checks before scoring.",
    "status": "YES_FOR_INPUT_PACKET_RECOVERY"
  },
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "source_search_review": {
    "absolute_xau_tick_file_rechecked": true,
    "absolute_xau_tick_window_rows": 0,
    "access_requests": [],
    "approved_search_roots_count": 9,
    "local_heavy_data_inventory_enforced": true,
    "mt5_read_only_rows": 89391,
    "sierra_same_market_xau_scid_window_rows": 0,
    "worktree_absence_not_treated_as_data_absence": true
  },
  "target_record_id": "OTG0-PKT-061|XAUUSD_2026-05-06T07:15:00+00:00",
  "terminal_g12_decision": "ACCEPT_PACKET_FOR_FUTURE_QUARANTINED_RESULT_AUDIT",
  "validation_safe": false,
  "verified_claims": [
    {
      "claim": "recovery_terminal_state",
      "expected": "RECOVERY_PACKET_READY_FOR_G12_REAUDIT",
      "observed": "RECOVERY_PACKET_READY_FOR_G12_REAUDIT",
      "status": "PASS"
    },
    {
      "claim": "parquet_sha256",
      "expected": "6f7e7e7e19635275916c78bb98678edf5f0cd80bebf2babd9f73017c740398ff",
      "observed": "6f7e7e7e19635275916c78bb98678edf5f0cd80bebf2babd9f73017c740398ff",
      "status": "PASS"
    },
    {
      "claim": "parquet_row_count",
      "expected": 89391,
      "observed": 89391,
      "status": "PASS"
    },
    {
      "claim": "first_tick_utc",
      "expected": "2026-05-06T07:10:01.820000Z",
      "observed": "2026-05-06T07:10:01.820000Z",
      "status": "PASS"
    },
    {
      "claim": "last_tick_utc",
      "expected": "2026-05-06T11:15:59.763000Z",
      "observed": "2026-05-06T11:15:59.763000Z",
      "status": "PASS"
    },
    {
      "claim": "decision_quote_timestamp_utc",
      "expected": "2026-05-06T07:14:59.889000Z",
      "observed": "2026-05-06T07:14:59.889000Z",
      "status": "PASS"
    },
    {
      "claim": "long_executable_ask",
      "expected": 4648.29,
      "observed": 4648.29,
      "status": "PASS"
    },
    {
      "claim": "ordered_path_first_timestamp_utc",
      "expected": "2026-05-06T07:15:00.634000Z",
      "observed": "2026-05-06T07:15:00.634000Z",
      "status": "PASS"
    },
    {
      "claim": "ordered_path_last_timestamp_utc",
      "expected": "2026-05-06T11:14:59.900000Z",
      "observed": "2026-05-06T11:14:59.900000Z",
      "status": "PASS"
    },
    {
      "claim": "post_horizon_first_timestamp_utc",
      "expected": "2026-05-06T11:15:00.335000Z",
      "observed": "2026-05-06T11:15:00.335000Z",
      "status": "PASS"
    }
  ]
}
```
