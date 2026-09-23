# OTI8 CNR061 Method Freeze - 2026-05-08

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `false`  
**Outcome review opened:** `false`  
**Live effect:** `false`

```json
{
  "accepted_sidecar_row_sha256": [
    "2d82227ec0dfd01b140471932701e4885dd065fca5c618d5dc2bf0e9c9da76ab",
    "41da6796ddb651413f558333ae52db302fc76a2863f00c204bee6ef37d10a23e",
    "4e76395873c48a3b9f20114c20d0247c92ef80846b170ee9b2f2d52919fa8d04",
    "5a7146782dc6564ac7a04ba163bd3d262ab731c2e1c3b6706ea14aeed979c7bb",
    "5ee22ed74a3eb5c16b1f7857d29346b2713ddbdb8b9a61de9f57c8414889959c",
    "63d08012951489781b7f892fe2d22a968e88101ded2429354aac16e68d3d93c8",
    "6b12bdca36eedc8c689617982be0f5fce05e5be3d16f84794c9ea30d87e36016",
    "95480e429f7beb460e31f4c65c0351eef65e46db4dca6557e4bb2a1f7afc998a"
  ],
  "account_history_accessed": false,
  "api_calls": 0,
  "artifact_family": "OTI8_CNR061_METHOD_FREEZE",
  "blocked_packet_outcome_source_read": false,
  "broker_actual_r_accessed": false,
  "canary_calls": 0,
  "cohort_freeze_status": "FROZEN_BEFORE_TERMINAL_TICK_PATH_SCORING",
  "databento_calls": 0,
  "date_stamp": "2026-05-08",
  "duplicate_aggregation_policy": {
    "countable_blocked_overlap": {
      "duplicate_denominator_key_overlap": [],
      "duplicate_group_id_overlap": [],
      "record_id_overlap": [],
      "source_row_hash_overlap": []
    },
    "countable_overlap_status": "PASS_ZERO_COUNTABLE_BLOCKED_OVERLAP",
    "countable_policy": "Use CNR/G12 countable_denominator_row from source rows: one countable primary row per packet/duplicate_group/timing_model/target_model; duplicate-context rows are retained row-level but excluded from countable aggregate.",
    "do_not_join_on_duplicate_group_alone": true,
    "raw_duplicate_overlap_disclosure": {
      "duplicate_denominator_key_overlap": [
        "OTG0-PKT-061|G6_CNR|XAGUSD|2026-05-04|london|SHORT|75.471|CNR_E0_DECISION_CLOSE_MARKET|CNR_T0_ORIGINAL_TP1",
        "OTG0-PKT-061|G6_CNR|XAGUSD|2026-05-04|london|SHORT|75.471|CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE|CNR_T0_ORIGINAL_TP1"
      ],
      "duplicate_group_id_overlap": [
        "G6_CNR|XAGUSD|2026-05-04|london|SHORT|75.471"
      ],
      "record_id_overlap": [],
      "source_row_hash_overlap": []
    },
    "row_level_all_eight_reported": true
  },
  "exclusion_gates": [
    "Exclude any sidecar_row_sha256 not accepted by G12_CNR061_SIDECAR_REAUDIT.",
    "Exclude the 94 source rows not matching accepted source row hashes.",
    "Null/exclude any accepted row with missing executable quote, missing ordered path, invalid stop geometry, target already passed at quote, or ambiguous same-tick target/stop."
  ],
  "generated_at_utc": "2026-05-08T05:11:01Z",
  "live_effect": false,
  "live_order_state_accessed": false,
  "live_trade_results_accessed": false,
  "metric_policy": {
    "path_horizon": "Use source sidecar ordered_path_packet path_start_utc/path_end_utc only.",
    "r_scoring": "Target before stop receives residual_target_r_from_executable_quote; stop before target receives -1.0R; unresolved horizon remains null.",
    "same_tick_policy": "If target and stop are both touched on the same ordered tick, classify ambiguous and do not impute R.",
    "target_model_family": "CNR_T0_ORIGINAL_TP1",
    "target_stop_fields": "entry_sl_tp_or_level_packet.take_profit_1 and stop_loss",
    "terminal_order_source": "source-hashed ordered tick path bid/ask rows, not OHLC ordering or hidden path labels"
  },
  "mt5_account_calls": 0,
  "mt5_order_calls": 0,
  "order_calls": 0,
  "outcome_review_opened": false,
  "packet_id": "OTG0-PKT-061",
  "paid_data_calls": 0,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "quote_side_policy": {
    "market_entry": "LONG uses ask, SHORT uses bid at source-hashed executable quote.",
    "terminal_exit": "LONG target/stop evaluated on bid; SHORT target/stop evaluated on ask."
  },
  "status": "PASS_METHOD_FROZEN",
  "validation_safe": false
}
```
