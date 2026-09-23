# OTR061 Continuation No-Retrace Packet Proposal

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `false`  
**Outcome review opened:** `false`  
**Live effect:** `false`

```json
{
  "account_history_accessed": false,
  "api_calls": 0,
  "artifact_family": "OTR061_CONTINUATION_NO_RETRACE_PACKET_PROPOSAL",
  "broker_actual_r_accessed": false,
  "databento_calls": 0,
  "date_stamp": "2026-05-07",
  "experiment_id": "G6-EXP-002-CONTINUATION-NO-RETRACE",
  "generated_at_utc": "2026-05-07T09:15:22Z",
  "live_effect": false,
  "live_order_state_accessed": false,
  "mt5_order_calls": 0,
  "order_calls": 0,
  "outcome_review_opened": false,
  "packet_id": "OTG0-PKT-061",
  "paid_data_calls": 0,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "record_count": 1,
  "records": [
    {
      "continuation_no_retrace_decision_price_path_packet": {
        "decision_price_fields_status": "DECISION_QUOTE_FOUND_FROM_SOURCE_HASHED_MT5_EXPORT",
        "entry_model_id": "CNR_E0_DECISION_CLOSE_MARKET",
        "external_g12_reaudit_required": true,
        "no_result_fields_assertion": true,
        "ordered_path_fields_status": "ORDERED_TICK_PATH_FOUND_FROM_SOURCE_HASHED_MT5_EXPORT",
        "path_horizon_source": "otx_fixed_4h_path_horizon_for_reaudit_only",
        "schema_id": "continuation_no_retrace_decision_price_path_v1"
      },
      "decision_asof_utc": "2026-05-06T07:15:00+00:00",
      "decision_price_path_contract": {
        "no_result_fields_assertion": true,
        "ordered_path_materialization": "source_ref_only_pending_G12_reaudit_parser",
        "schema": "continuation_no_retrace_decision_price_path_v1",
        "source_hashed_tick_or_quote_path_refs": [
          {
            "inspection_summary": {
              "coverage_status": "RECOVERED_ROWS_FROM_READ_ONLY_MT5",
              "rows": 89391
            },
            "path": "C:\\tmp\\gtos_otb\\OTR061TICK\\research\\science_program_2026_05\\06_outcome_testing\\otr061_xau_tick_recovery\\OTR061_MT5_READ_ONLY_XAUUSD_TICKS_2026-05-06_0710_1115.parquet",
            "sha256": "6f7e7e7e19635275916c78bb98678edf5f0cd80bebf2babd9f73017c740398ff",
            "source_id": "mt5_read_only_recovered_tick_export"
          }
        ],
        "window_end_utc": "2026-05-06T11:15:00+00:00",
        "window_start_utc": "2026-05-06T07:10:00+00:00"
      },
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
      "packet_id": "OTG0-PKT-061",
      "prior_otx_input_record_for_traceability": {
        "candidate_id": "XAUUSD_2026-05-06T07:15:00+00:00",
        "continuation_no_retrace_decision_price_path_packet": {
          "decision_price_fields_status": "DECISION_QUOTE_NOT_FOUND_WITHIN_5M",
          "entry_model_id": "CNR_E0_DECISION_CLOSE_MARKET",
          "external_g12_reaudit_required": true,
          "ordered_path_fields_status": "ORDERED_TICK_PATH_EMPTY_OR_MISSING",
          "path_horizon_source": "otx_fixed_4h_path_horizon_for_reaudit_only",
          "schema_id": "continuation_no_retrace_decision_price_path_v1_otx_proposal"
        },
        "decision_asof_utc": "2026-05-06T07:15:00+00:00",
        "decision_quote_packet": {
          "decision_asof_utc": "2026-05-06T07:15:00Z",
          "missing_tick_files": [],
          "quote_status": "DECISION_QUOTE_NOT_FOUND_WITHIN_5M",
          "tick_source_files": [
            "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAUUSD\\2026-05-06.parquet"
          ]
        },
        "duplicate_group_id": "G6_CNR|XAUUSD|2026-05-06|london|LONG|4561.52",
        "experiment_id": "G6-EXP-002-CONTINUATION-NO-RETRACE",
        "label_family": "input_only_features_no_labels",
        "no_result_fields_assertion": true,
        "ordered_tick_path_packet": {
          "missing_tick_files": [],
          "ordered_path_source_id": "61d9086fe8a5a85e9a265e819e51c226",
          "path_end_utc": "2026-05-06T11:15:00Z",
          "path_first_timestamp_utc": null,
          "path_horizon_source": "otx_fixed_4h_path_horizon_for_reaudit_only",
          "path_last_timestamp_utc": null,
          "path_row_count": 0,
          "path_row_count_status": "EXACT_FILTERED_TICK_COUNT",
          "path_source_files": [
            "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAUUSD\\2026-05-06.parquet"
          ],
          "path_source_sha256": {
            "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAUUSD\\2026-05-06.parquet": "fdec881196886808c90aa25d6a91d99c5f1105274ecbd435e442f63bcac59439"
          },
          "path_source_type": "tick_parquet_quote_stream",
          "path_start_utc": "2026-05-06T07:15:00Z",
          "path_status": "ORDERED_TICK_PATH_EMPTY_OR_MISSING"
        },
        "outcome_review_opened": false,
        "packet_id": "OTG0-PKT-061",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "proposal_source_hash": "cdb0caa6d81f5687888174729413605f7c952c4b869bcc347a1b2764b94dbeaa",
        "record_id": "OTG0-PKT-061|XAUUSD_2026-05-06T07:15:00+00:00",
        "session": "london",
        "side": "LONG",
        "symbol": "XAUUSD",
        "validation_safe": false
      },
      "record_id": "OTG0-PKT-061|XAUUSD_2026-05-06T07:15:00+00:00",
      "side": "LONG",
      "symbol": "XAUUSD"
    }
  ],
  "repo_head": "ee34bc50c8f1326ccbf697c9bee4e96171b1e433",
  "required_window_utc": {
    "decision_asof": "2026-05-06T07:15:00+00:00",
    "end": "2026-05-06T11:15:00+00:00",
    "start": "2026-05-06T07:10:00+00:00"
  },
  "schema": "continuation_no_retrace_decision_price_path_v1",
  "target_record_id": "OTG0-PKT-061|XAUUSD_2026-05-06T07:15:00+00:00",
  "target_symbol": "XAUUSD",
  "terminal_state": "RECOVERY_PACKET_READY_FOR_G12_REAUDIT",
  "validation_safe": false
}
```
