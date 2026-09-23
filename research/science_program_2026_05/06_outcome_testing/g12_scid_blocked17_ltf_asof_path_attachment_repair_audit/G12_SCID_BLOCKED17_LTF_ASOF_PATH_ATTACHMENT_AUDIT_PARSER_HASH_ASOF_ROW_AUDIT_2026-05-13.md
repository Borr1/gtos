# Parser Hash Asof Row Audit

```json
{
  "all_rows_parser_bound_hash_asof_and_fail_closed": true,
  "artifact_family": "PARSER_HASH_ASOF_ROW_AUDIT",
  "attachment_row_count": 78,
  "candidate_rowset_recompute": {
    "candidate_rows_ref": "research/science_program_2026_05/06_outcome_testing/scid_asof_bar_builder_and_candidate_input_packet_source_control/SCID_ASOF_CANDIDATE_INPUT_ROWS_2026-05-11.jsonl",
    "crlf_normalized_sha256_matches_manifest": false,
    "duplicate_key_collision_count": 0,
    "first_decision_asof_utc": "2026-05-01T21:00:00.000Z",
    "forbidden_field_names": [],
    "hash_policy_repair_applied": "TEXT_EOL_EQUIVALENCE_ACCEPTED_FOR_JSONL_SOURCE_HASH",
    "last_decision_asof_utc": "2026-05-11T10:00:00.000Z",
    "lf_normalized_sha256_matches_manifest": true,
    "manifest_row_count": 3014,
    "manifest_sha256": "a692db4032a945f588d2cb4232600262e4f7eaa2f39a0725f13f5a5e3cab5eb2",
    "raw_sha256_matches_manifest": false,
    "recomputed_crlf_normalized_sha256": "11d2c2e13b107231af756b3dc4a07f9a0d696a55770ee3bc492921d8ff7ed634",
    "recomputed_lf_normalized_sha256": "a692db4032a945f588d2cb4232600262e4f7eaa2f39a0725f13f5a5e3cab5eb2",
    "recomputed_raw_sha256": "11d2c2e13b107231af756b3dc4a07f9a0d696a55770ee3bc492921d8ff7ed634",
    "row_count": 3014,
    "row_count_matches_manifest": true,
    "sample_row_ids": [
      "candidate_input:EURUSD_FUTURES_6E_PROXY:2026-05-10T22:15:00.000Z",
      "candidate_input:EURUSD_FUTURES_6E_PROXY:2026-05-10T22:30:00.000Z",
      "candidate_input:EURUSD_FUTURES_6E_PROXY:2026-05-10T22:45:00.000Z",
      "candidate_input:EURUSD_FUTURES_6E_PROXY:2026-05-10T23:00:00.000Z",
      "candidate_input:EURUSD_FUTURES_6E_PROXY:2026-05-10T23:15:00.000Z"
    ],
    "sha256_matches_manifest": true,
    "unique_duplicate_key_count": 3014
  },
  "changes_trading_risk_safety_prompt_decision_behavior": false,
  "closure_status_counts": {
    "PARSER_BOUND_HASH_OR_EXACT_NO_COMMIT_HASH_REQUIREMENT_ATTACHED": 13,
    "PARSER_BOUND_SOURCE_HASH_ASOF_REQUIREMENTS_ATTACHED": 65
  },
  "credentials_touched": false,
  "decision_window_asof_rules": [
    "decision_asof_utc is the hard upper bound for every LTF bar/tick source row",
    "decision_minus_window_start_utc must be present in any card-level packet before LTF materialization; if absent, the row fails closed",
    "M15 source-control rows already carry bar_window_start_utc/bar_window_end_utc and row hashes; LTF M1/M5/tick rows must bind the same candidate_input_row_id or duplicate_key before use",
    "No result, target-hit, stop-hit, R/PnL, win-rate, expectancy, broker account/order/history/deal/position, or post-outcome fields may be used as source selectors"
  ],
  "evidence_class": "G12_SCID_BLOCKED17_LTF_ASOF_PATH_ATTACHMENT_REPAIR_AUDIT_ONLY",
  "failures": [],
  "field_counts": {
    "asof_path_descriptor_version": 13,
    "bars_present_by_timeframe": 13,
    "decision_minus_window_start_utc": 13,
    "ltf_source_file_pointer_or_cache_id": 13,
    "ltf_source_hash": 13,
    "ltf_timeframes_available": 13
  },
  "generated_at_utc": "2026-05-13T04:46:17Z",
  "live_effect": false,
  "ok": true,
  "opens_ai_api": false,
  "opens_broker_account_order_history_deal_position_evidence": false,
  "opens_live_restart": false,
  "opens_live_trading_behavior": false,
  "opens_paid_or_vendor_access": false,
  "opens_prompt_config_risk_safety_execution_canary_selector_edit": false,
  "opens_raw_market_data_blob_commit": false,
  "opens_registry_edit": false,
  "opens_remote_push": false,
  "opens_result_scoring": false,
  "opens_strategy_edge_claims": false,
  "opens_validation": false,
  "outcome_review_opened": false,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "required_parser_binding_families": [
    "accepted_scid_m15_source_control_bars",
    "forward_capture_ltf_availability_schema",
    "prior_production_mt5_tick_parquet_market_context",
    "sierra_converted_m1_m5_m15_ohlcv_roots"
  ],
  "route_id": "G12_SCID_BLOCKED17_LTF_ASOF_PATH_ATTACHMENT_REPAIR_AUDIT",
  "sample_attachment_rows": [
    {
      "card_id": "ADV-002",
      "closure_status": "PARSER_BOUND_SOURCE_HASH_ASOF_REQUIREMENTS_ATTACHED",
      "field": "asof_path_descriptor_version",
      "parser_families": [
        "accepted_scid_m15_source_control_bars",
        "sierra_converted_m1_m5_m15_ohlcv_roots",
        "prior_production_mt5_tick_parquet_market_context",
        "forward_capture_ltf_availability_schema"
      ]
    },
    {
      "card_id": "ADV-002",
      "closure_status": "PARSER_BOUND_SOURCE_HASH_ASOF_REQUIREMENTS_ATTACHED",
      "field": "bars_present_by_timeframe",
      "parser_families": [
        "accepted_scid_m15_source_control_bars",
        "sierra_converted_m1_m5_m15_ohlcv_roots",
        "prior_production_mt5_tick_parquet_market_context",
        "forward_capture_ltf_availability_schema"
      ]
    },
    {
      "card_id": "ADV-002",
      "closure_status": "PARSER_BOUND_SOURCE_HASH_ASOF_REQUIREMENTS_ATTACHED",
      "field": "decision_minus_window_start_utc",
      "parser_families": [
        "accepted_scid_m15_source_control_bars",
        "sierra_converted_m1_m5_m15_ohlcv_roots",
        "prior_production_mt5_tick_parquet_market_context",
        "forward_capture_ltf_availability_schema"
      ]
    },
    {
      "card_id": "ADV-002",
      "closure_status": "PARSER_BOUND_SOURCE_HASH_ASOF_REQUIREMENTS_ATTACHED",
      "field": "ltf_source_file_pointer_or_cache_id",
      "parser_families": [
        "accepted_scid_m15_source_control_bars",
        "sierra_converted_m1_m5_m15_ohlcv_roots",
        "prior_production_mt5_tick_parquet_market_context",
        "forward_capture_ltf_availability_schema"
      ]
    },
    {
      "card_id": "ADV-002",
      "closure_status": "PARSER_BOUND_HASH_OR_EXACT_NO_COMMIT_HASH_REQUIREMENT_ATTACHED",
      "field": "ltf_source_hash",
      "parser_families": [
        "accepted_scid_m15_source_control_bars",
        "sierra_converted_m1_m5_m15_ohlcv_roots",
        "prior_production_mt5_tick_parquet_market_context",
        "forward_capture_ltf_availability_schema"
      ]
    },
    {
      "card_id": "ADV-002",
      "closure_status": "PARSER_BOUND_SOURCE_HASH_ASOF_REQUIREMENTS_ATTACHED",
      "field": "ltf_timeframes_available",
      "parser_families": [
        "accepted_scid_m15_source_control_bars",
        "sierra_converted_m1_m5_m15_ohlcv_roots",
        "prior_production_mt5_tick_parquet_market_context",
        "forward_capture_ltf_availability_schema"
      ]
    },
    {
      "card_id": "EXE-001",
      "closure_status": "PARSER_BOUND_SOURCE_HASH_ASOF_REQUIREMENTS_ATTACHED",
      "field": "asof_path_descriptor_version",
      "parser_families": [
        "accepted_scid_m15_source_control_bars",
        "sierra_converted_m1_m5_m15_ohlcv_roots",
        "prior_production_mt5_tick_parquet_market_context",
        "forward_capture_ltf_availability_schema"
      ]
    },
    {
      "card_id": "EXE-001",
      "closure_status": "PARSER_BOUND_SOURCE_HASH_ASOF_REQUIREMENTS_ATTACHED",
      "field": "bars_present_by_timeframe",
      "parser_families": [
        "accepted_scid_m15_source_control_bars",
        "sierra_converted_m1_m5_m15_ohlcv_roots",
        "prior_production_mt5_tick_parquet_market_context",
        "forward_capture_ltf_availability_schema"
      ]
    }
  ],
  "schema_version": "g12_scid_blocked17_ltf_asof_path_attachment_repair_audit_v1",
  "source_exists_card_count": 13,
  "source_family_coverage": {
    "accepted_scid_m15_source_control_bars": {
      "asof_field": "decision_asof_utc",
      "row_count": 3014,
      "source_hash": "a692db4032a945f588d2cb4232600262e4f7eaa2f39a0725f13f5a5e3cab5eb2",
      "status": "HASH_ASOF_ATTACHED"
    },
    "prior_production_mt5_tick_parquet_market_context": {
      "source_file_count": 93,
      "status": "PARSER_BOUND_HASH_OR_EXACT_REQUIREMENT_ATTACHED",
      "symbol_counts": {
        "GBPJPY": 13,
        "GBPUSD": 13,
        "NAS100": 14,
        "US30_cash": 14,
        "USDJPY": 13,
        "XAGUSD": 13,
        "XAUUSD": 13
      }
    },
    "sierra_converted_m1_m5_m15_ohlcv_roots": {
      "source_file_count": 150,
      "status": "PARSER_BOUND_HASH_OR_EXACT_REQUIREMENT_ATTACHED",
      "timeframe_counts": {
        "M1": 50,
        "M15": 50,
        "M5": 50
      }
    }
  },
  "validation_safe": false
}
```
