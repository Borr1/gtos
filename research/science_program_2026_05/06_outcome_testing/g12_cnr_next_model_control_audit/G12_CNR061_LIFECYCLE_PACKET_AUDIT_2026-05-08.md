# G12 CNR061 Lifecycle Packet Audit - 2026-05-08

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `false`  
**Outcome review opened:** `false`  
**Live effect:** `false`

```json
{
  "account_history_accessed": false,
  "api_calls": 0,
  "artifact_family": "G12_CNR061_LIFECYCLE_PACKET_AUDIT",
  "blocked_packet_outcome_source_read": false,
  "broker_actual_r_accessed": false,
  "canary_calls": 0,
  "databento_calls": 0,
  "date_stamp": "2026-05-08",
  "decision": "ACCEPT_LIFECYCLE_EVIDENCE_ONLY",
  "generated_at_utc": "2026-05-08T06:23:47Z",
  "independent_lifecycle_recompute": {
    "forbidden_lifecycle_key_hits": [],
    "label_counts": {
      "stop_after_original_horizon": 6
    },
    "oti8_no_terminal_row_count": 6,
    "oti8_no_terminal_sidecar_hashes": [
      "2d82227ec0dfd01b140471932701e4885dd065fca5c618d5dc2bf0e9c9da76ab",
      "41da6796ddb651413f558333ae52db302fc76a2863f00c204bee6ef37d10a23e",
      "4e76395873c48a3b9f20114c20d0247c92ef80846b170ee9b2f2d52919fa8d04",
      "5a7146782dc6564ac7a04ba163bd3d262ab731c2e1c3b6706ea14aeed979c7bb",
      "5ee22ed74a3eb5c16b1f7857d29346b2713ddbdb8b9a61de9f57c8414889959c",
      "63d08012951489781b7f892fe2d22a968e88101ded2429354aac16e68d3d93c8"
    ],
    "packet_sidecar_hashes": [
      "2d82227ec0dfd01b140471932701e4885dd065fca5c618d5dc2bf0e9c9da76ab",
      "41da6796ddb651413f558333ae52db302fc76a2863f00c204bee6ef37d10a23e",
      "4e76395873c48a3b9f20114c20d0247c92ef80846b170ee9b2f2d52919fa8d04",
      "5a7146782dc6564ac7a04ba163bd3d262ab731c2e1c3b6706ea14aeed979c7bb",
      "5ee22ed74a3eb5c16b1f7857d29346b2713ddbdb8b9a61de9f57c8414889959c",
      "63d08012951489781b7f892fe2d22a968e88101ded2429354aac16e68d3d93c8"
    ],
    "recomputed_rows": [
      {
        "candidate_close_utc": "2026-05-05T16:30:00+00:00",
        "countable_denominator_row": true,
        "matches_packet": true,
        "packet_label": "stop_after_original_horizon",
        "packet_row_sha256": "5aac013795111ad6962ac72309d2c452929906947c1c6c79d42b1b5ceae68423",
        "recomputed_label": "stop_after_original_horizon",
        "sidecar_row_sha256": "4e76395873c48a3b9f20114c20d0247c92ef80846b170ee9b2f2d52919fa8d04",
        "source_file_hash_failures": [],
        "source_first_tick_utc": "2026-05-05T20:30:00.120000Z",
        "source_last_tick_utc": "2026-05-06T16:29:59.984000Z",
        "source_rows_scanned": 208008,
        "terminal_ask": 74.122,
        "terminal_bid": 74.037,
        "terminal_event_utc": "2026-05-05T23:22:34.677000Z",
        "terminal_price_side": "ask",
        "timing_model_family": "CNR_E0_DECISION_CLOSE_MARKET"
      },
      {
        "candidate_close_utc": "2026-05-05T16:30:00+00:00",
        "countable_denominator_row": true,
        "matches_packet": true,
        "packet_label": "stop_after_original_horizon",
        "packet_row_sha256": "edc35423370a019ec857e057b17da57d678bdc0ba888048ee6808ad850d8a588",
        "recomputed_label": "stop_after_original_horizon",
        "sidecar_row_sha256": "41da6796ddb651413f558333ae52db302fc76a2863f00c204bee6ef37d10a23e",
        "source_file_hash_failures": [],
        "source_first_tick_utc": "2026-05-05T20:30:00.120000Z",
        "source_last_tick_utc": "2026-05-06T16:29:59.984000Z",
        "source_rows_scanned": 208008,
        "terminal_ask": 74.122,
        "terminal_bid": 74.037,
        "terminal_event_utc": "2026-05-05T23:22:34.677000Z",
        "terminal_price_side": "ask",
        "timing_model_family": "CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE"
      },
      {
        "candidate_close_utc": "2026-05-05T16:45:00+00:00",
        "countable_denominator_row": false,
        "matches_packet": true,
        "packet_label": "stop_after_original_horizon",
        "packet_row_sha256": "ce231b55138a2e55dd83b0359f38069a61874f0ca96baa1a342e61feed210ead",
        "recomputed_label": "stop_after_original_horizon",
        "sidecar_row_sha256": "5a7146782dc6564ac7a04ba163bd3d262ab731c2e1c3b6706ea14aeed979c7bb",
        "source_file_hash_failures": [],
        "source_first_tick_utc": "2026-05-05T20:45:00.084000Z",
        "source_last_tick_utc": "2026-05-06T16:44:59.529000Z",
        "source_rows_scanned": 209579,
        "terminal_ask": 74.358,
        "terminal_bid": 74.283,
        "terminal_event_utc": "2026-05-06T00:55:10.729000Z",
        "terminal_price_side": "ask",
        "timing_model_family": "CNR_E0_DECISION_CLOSE_MARKET"
      },
      {
        "candidate_close_utc": "2026-05-05T16:45:00+00:00",
        "countable_denominator_row": false,
        "matches_packet": true,
        "packet_label": "stop_after_original_horizon",
        "packet_row_sha256": "77d82cd9724e56efac6e7774b30c66e4bd9d8cb444de9cd144fa97e1c43d0b1f",
        "recomputed_label": "stop_after_original_horizon",
        "sidecar_row_sha256": "2d82227ec0dfd01b140471932701e4885dd065fca5c618d5dc2bf0e9c9da76ab",
        "source_file_hash_failures": [],
        "source_first_tick_utc": "2026-05-05T20:45:00.084000Z",
        "source_last_tick_utc": "2026-05-06T16:44:59.529000Z",
        "source_rows_scanned": 209579,
        "terminal_ask": 74.358,
        "terminal_bid": 74.283,
        "terminal_event_utc": "2026-05-06T00:55:10.729000Z",
        "terminal_price_side": "ask",
        "timing_model_family": "CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE"
      },
      {
        "candidate_close_utc": "2026-05-05T17:00:00+00:00",
        "countable_denominator_row": false,
        "matches_packet": true,
        "packet_label": "stop_after_original_horizon",
        "packet_row_sha256": "82bc07ec8b0c4cbb7c7e1a82b898fc72a90807250fe23d495634a5355334b0c3",
        "recomputed_label": "stop_after_original_horizon",
        "sidecar_row_sha256": "63d08012951489781b7f892fe2d22a968e88101ded2429354aac16e68d3d93c8",
        "source_file_hash_failures": [],
        "source_first_tick_utc": "2026-05-05T22:00:02.086000Z",
        "source_last_tick_utc": "2026-05-06T16:59:59.994000Z",
        "source_rows_scanned": 211833,
        "terminal_ask": 74.104,
        "terminal_bid": 74.019,
        "terminal_event_utc": "2026-05-05T23:22:30.264000Z",
        "terminal_price_side": "ask",
        "timing_model_family": "CNR_E0_DECISION_CLOSE_MARKET"
      },
      {
        "candidate_close_utc": "2026-05-05T17:00:00+00:00",
        "countable_denominator_row": false,
        "matches_packet": true,
        "packet_label": "stop_after_original_horizon",
        "packet_row_sha256": "fd78bccfb4eb4f6376befb960d39f01ea66d8aadda560fb27edee93c6cb97b45",
        "recomputed_label": "stop_after_original_horizon",
        "sidecar_row_sha256": "5ee22ed74a3eb5c16b1f7857d29346b2713ddbdb8b9a61de9f57c8414889959c",
        "source_file_hash_failures": [],
        "source_first_tick_utc": "2026-05-05T22:00:02.086000Z",
        "source_last_tick_utc": "2026-05-06T16:59:59.994000Z",
        "source_rows_scanned": 211833,
        "terminal_ask": 74.104,
        "terminal_bid": 74.019,
        "terminal_event_utc": "2026-05-05T23:22:30.264000Z",
        "terminal_price_side": "ask",
        "timing_model_family": "CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE"
      }
    ],
    "row_count": 6,
    "source_hash_failures": [],
    "status": "PASS"
  },
  "label_contract": {
    "allowed_labels": [
      "target_after_original_horizon",
      "stop_after_original_horizon",
      "ambiguous_target_stop_after_original_horizon",
      "still_no_terminal_after_extended_horizon",
      "source_horizon_insufficient"
    ],
    "contract_id": "CNR_T3_LIFECYCLE_NO_TERMINAL_EXTENSION_V1",
    "contract_sha256": "f36b44a84d982e0b2e5db6d10001a039821167a4c2ec911f85993454c5b728b3",
    "duplicate_policy": "Retain all six row-level rows; countable denominator uses the upstream OTI8 countable flag and duplicate_denominator_key.",
    "extended_horizon_policy": "Scan source-hashed XAGUSD ticks after original path_end_utc until the first terminal label or path_start_utc+24h, using contiguous local tick files already present.",
    "forbidden_outputs": [
      "synthetic_r",
      "broker_actual_r",
      "account_history",
      "live_trade_result",
      "live_order_state",
      "hidden_path_label",
      "promotion_statistic"
    ],
    "freeze_order": "This contract is built before reading any extended beyond-original-horizon tick path.",
    "price_side_rule": "For SHORT rows, ask reaching take_profit_1 is target and ask reaching stop_loss is stop; for LONG rows, bid is used.",
    "row_scope": "Exactly the six OTI8 rows with terminal_status=NO_TERMINAL_WITHIN_ORDERED_HORIZON.",
    "validation_boundary": "Lifecycle labels are discovery/input packet state only; no R, DSR/PBO, promotion, or live rule is computed."
  },
  "live_effect": false,
  "live_order_state_accessed": false,
  "live_trade_results_accessed": false,
  "mt5_account_calls": 0,
  "mt5_order_calls": 0,
  "order_calls": 0,
  "outcome_review_opened": false,
  "packet_status": "SOURCE_SAFE_LIFECYCLE_PACKET_BUILT_NO_R_SCORING",
  "paid_data_calls": 0,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "schema_version": "g12_cnr_next_model_control_audit_v1",
  "scope_check": {
    "all_rows_original_no_terminal": true,
    "all_rows_xagusd": true,
    "control_packet_rows": 6,
    "oti8_no_terminal_rows": 6,
    "oti8_no_terminal_sidecar_hashes": [
      "2d82227ec0dfd01b140471932701e4885dd065fca5c618d5dc2bf0e9c9da76ab",
      "41da6796ddb651413f558333ae52db302fc76a2863f00c204bee6ef37d10a23e",
      "4e76395873c48a3b9f20114c20d0247c92ef80846b170ee9b2f2d52919fa8d04",
      "5a7146782dc6564ac7a04ba163bd3d262ab731c2e1c3b6706ea14aeed979c7bb",
      "5ee22ed74a3eb5c16b1f7857d29346b2713ddbdb8b9a61de9f57c8414889959c",
      "63d08012951489781b7f892fe2d22a968e88101ded2429354aac16e68d3d93c8"
    ],
    "packet_sidecar_hashes": [
      "2d82227ec0dfd01b140471932701e4885dd065fca5c618d5dc2bf0e9c9da76ab",
      "41da6796ddb651413f558333ae52db302fc76a2863f00c204bee6ef37d10a23e",
      "4e76395873c48a3b9f20114c20d0247c92ef80846b170ee9b2f2d52919fa8d04",
      "5a7146782dc6564ac7a04ba163bd3d262ab731c2e1c3b6706ea14aeed979c7bb",
      "5ee22ed74a3eb5c16b1f7857d29346b2713ddbdb8b9a61de9f57c8414889959c",
      "63d08012951489781b7f892fe2d22a968e88101ded2429354aac16e68d3d93c8"
    ],
    "status": "PASS"
  },
  "six_row_lifecycle_summary": {
    "candidate_closes_utc": [
      "2026-05-05T16:30:00+00:00",
      "2026-05-05T16:45:00+00:00",
      "2026-05-05T17:00:00+00:00"
    ],
    "duplicate_groups": {
      "G6_CNR|XAGUSD|2026-05-05|ny|SHORT|73.222": 6
    },
    "lifecycle_label_counts": {
      "stop_after_original_horizon": 6
    },
    "source_files": [
      "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAGUSD\\2026-05-05.parquet",
      "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\XAGUSD\\2026-05-06.parquet"
    ],
    "timing_families": {
      "CNR_E0_DECISION_CLOSE_MARKET": 3,
      "CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE": 3
    }
  },
  "validation_safe": false,
  "what_this_does_not_prove": [
    "It does not compute or validate R/performance for the six lifecycle rows.",
    "It does not use or prove broker actual-R, account history, live trade results, live order state, or real fill/PnL behavior.",
    "It does not score, rescue, or reclassify the 94 G12-blocked rows.",
    "It does not meet sample-floor, DSR, PBO, effective-N, concentration, validation, promotion, or live-gate requirements.",
    "It does not prove E2/E3/E4 timing fields, T1 fixed-R targets, or T2 structural targets improve outcomes.",
    "It does not justify a new threshold, selector, risk change, prompt change, execution change, or live rule."
  ],
  "what_this_proves": [
    "The exact six OTI8 no-terminal rows can be re-identified by sidecar hashes and are the only rows in the lifecycle packet.",
    "The XAGUSD May 5/6 local tick extension files exist and their source hashes match the packet references.",
    "Under the frozen CNR_T3_LIFECYCLE_NO_TERMINAL_EXTENSION_V1 contract and SHORT ask-side terminal rule, all six rows first hit the original stop after the original ordered horizon.",
    "The earlier OTI8 no-terminal label was horizon-limited, not proof that the setup never reached a terminal state later.",
    "The six rows are useful failure-anatomy evidence for a late adverse XAGUSD May 5 NY duplicate group."
  ]
}
```
