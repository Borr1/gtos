# G12 CNR Next Decision Ledger - 2026-05-08

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `false`  
**Outcome review opened:** `false`  
**Live effect:** `false`

```json
{
  "account_history_accessed": false,
  "api_calls": 0,
  "artifact_family": "G12_CNR_NEXT_DECISION_LEDGER",
  "audit_question_answers": [
    {
      "answer": "Yes, with a minor context note: the control pack anchor is from its source worktree/head, while this G12 audit rehashes the current merged artifacts in the G12 branch.",
      "evidence": "G12 context anchor and control pack context anchor",
      "question": 1
    },
    {
      "answer": "Yes for preregistration; E2/E3/E4 are blocked for current-row scoring because source-hashed signal, latency, and pretouch fields do not exist.",
      "evidence": [
        {
          "audit_reason": "The family is frozen as a future input contract, but current OTI8 rows do not contain the source-hashed fields needed to score it.",
          "decision": "ACCEPT_AS_RESEARCH_PREREGISTRATION_BLOCK_CURRENT_ROWS",
          "exact_blocker": "No committed source-hashed signal emission logger exists for these rows; preregister field only.",
          "family_id": "CNR_E2_SIGNAL_EMITTED_AT_SOURCE",
          "family_type": "timing",
          "forbidden_fields": [
            "terminal_event",
            "synthetic_path_r",
            "broker_actual_r",
            "account_history",
            "live_order_state",
            "hidden_path_label"
          ],
          "required_fields": [
            "signal_emitted_utc",
            "source_id",
            "source_hash",
            "emission_rule_id",
            "source_record_id"
          ],
          "source_state": "BLOCKED_FOR_CURRENT_OTI8_ROWS; current CNR matrix has signal_emitted_utc null."
        },
        {
          "audit_reason": "The family is frozen as a future input contract, but current OTI8 rows do not contain the source-hashed fields needed to score it.",
          "decision": "ACCEPT_AS_RESEARCH_PREREGISTRATION_BLOCK_CURRENT_ROWS",
          "exact_blocker": "Current OTI8/G12 artifacts have executable quote timestamps but not request/response timestamps or timeout policy ids.",
          "family_id": "CNR_E3_DECISION_LATENCY_AWARE",
          "family_type": "timing",
          "forbidden_fields": [
            "terminal_event",
            "synthetic_path_r",
            "broker_actual_r",
            "account_history",
            "live_order_state",
            "hidden_path_label"
          ],
          "required_fields": [
            "decision_request_sent_utc",
            "decision_response_received_utc",
            "latency_ms",
            "latency_policy_id",
            "quote_lookup_policy_id",
            "timeout_behavior"
          ],
          "source_state": "BLOCKED_FOR_CURRENT_OTI8_ROWS; request/response latency timestamps are not present in accepted packets."
        },
        {
          "audit_reason": "The family is frozen as a future input contract, but current OTI8 rows do not contain the source-hashed fields needed to score it.",
          "decision": "ACCEPT_AS_RESEARCH_PREREGISTRATION_BLOCK_CURRENT_ROWS",
          "exact_blocker": "No source-hashed pretouch trigger id, trigger type, distance-to-level rule, or cancellation source is present.",
          "family_id": "CNR_E4_PRETOUCH_TRIGGER",
          "family_type": "timing",
          "forbidden_fields": [
            "terminal_event",
            "synthetic_path_r",
            "broker_actual_r",
            "account_history",
            "live_order_state",
            "hidden_path_label"
          ],
          "required_fields": [
            "pretouch_trigger_id",
            "pretouch_trigger_utc",
            "trigger_type",
            "distance_to_level_rule_id",
            "cancellation_rule_id",
            "source_hash"
          ],
          "source_state": "BLOCKED_FOR_CURRENT_OTI8_ROWS; pretouch trigger source does not exist."
        },
        {
          "audit_reason": "The contract avoids outcome-fit rescue thresholds, but no result lane may score T1 until fixed_r_multiple and stop source are frozen in a packet.",
          "decision": "ACCEPT_AS_RESEARCH_PREREGISTRATION_BLOCK_RESULT_SCORING_UNTIL_FIXED_R_PACKET",
          "exact_blocker": "No result lane may score T1 until fixed_r_multiple and stop source are frozen in a packet.",
          "family_id": "CNR_T1_FIXED_R_FROM_EXECUTABLE_QUOTE",
          "family_type": "target",
          "price_side_rule": "LONG entry quote uses ask and terminal target/stop uses bid; SHORT entry quote uses bid and terminal target/stop uses ask.",
          "source_asof_fields": [
            "executable_quote_price",
            "executable_quote_side",
            "quote_timestamp_utc",
            "stop_loss",
            "stop_source_hash",
            "fixed_r_multiple",
            "target_price"
          ]
        },
        {
          "audit_reason": "The contract is source-safe, but current CNR rows do not have source-hashed structural-level snapshots or hierarchy/rank fields.",
          "decision": "ACCEPT_AS_RESEARCH_PREREGISTRATION_BLOCK_SOURCE_READINESS",
          "exact_blocker": "Current CNR rows bind original TP1 only; no source-hashed structural-level rank/source snapshot is available for CNR_T2.",
          "family_id": "CNR_T2_SOURCE_HASHED_STRUCTURAL_LEVEL",
          "family_type": "target",
          "price_side_rule": "same executable/terminal quote-side rule as T1.",
          "source_asof_fields": [
            "structural_level_id",
            "level_price",
            "level_timestamp_utc",
            "level_source_hash",
            "hierarchy_rank",
            "selection_rule_id"
          ]
        },
        {
          "audit_reason": "T3 categorical lifecycle labels were built for the six no-terminal rows without R scoring; validation and promotion remain blocked.",
          "decision": "ACCEPT_RESEARCH_PREREGISTRATION_AND_ACCEPT_SIX_ROW_LIFECYCLE_EVIDENCE_ONLY",
          "exact_blocker": "Promotion/result scoring remains blocked; Workstream C builds only source-hashed labels for the six no-terminal rows.",
          "family_id": "CNR_T3_TERMINAL_TIMEBOX_OR_LIFECYCLE",
          "family_type": "target",
          "price_side_rule": "same terminal quote-side rule as T1 for detecting target/stop event order; labels do not compute R.",
          "source_asof_fields": [
            "timebox_policy_id",
            "path_start_utc",
            "original_horizon_end_utc",
            "extended_horizon_end_utc",
            "path_source_files",
            "path_source_sha256"
          ]
        }
      ],
      "question": 2
    },
    {
      "answer": "Yes for T1/T2/T3 preregistration; T1/T2 result scoring remains blocked and no post-hoc residual rescue threshold was introduced.",
      "evidence": {
        "expected": [
          "CNR_T1_FIXED_R_FROM_EXECUTABLE_QUOTE",
          "CNR_T2_SOURCE_HASHED_STRUCTURAL_LEVEL",
          "CNR_T3_TERMINAL_TIMEBOX_OR_LIFECYCLE"
        ],
        "observed": [
          "CNR_T1_FIXED_R_FROM_EXECUTABLE_QUOTE",
          "CNR_T2_SOURCE_HASHED_STRUCTURAL_LEVEL",
          "CNR_T3_TERMINAL_TIMEBOX_OR_LIFECYCLE"
        ],
        "status": "PASS"
      },
      "question": 3
    },
    {
      "answer": "Yes as research contracts only; validation_safe remains false and source readiness is explicitly blocked where fields are absent.",
      "evidence": {
        "allowed_parsers": [
          "pyarrow parquet reader for ts_utc/bid/ask",
          "json/jsonl source-hash parser",
          "future preregistered source-specific parser"
        ],
        "allowed_source_roots": [
          "C:\\Users\\MSI\\Documents\\ai-trading-agent\\data\\ticks\\{SYMBOL}\\YYYY-MM-DD.parquet",
          "research/science_program_2026_05/06_outcome_testing/* source-hashed JSON/JSONL artifacts",
          "future source-hashed shadow logger files explicitly registered by G12/G0"
        ],
        "forbidden_sources": [
          "broker actual-R",
          "account history",
          "live trade results",
          "live order state",
          "hidden path labels",
          "94 G12-blocked CNR061 rows as scored evidence"
        ],
        "legal_source_state": {
          "E2_E3_E4": "preregistered but current rows blocked by missing source fields",
          "T1_T2_T3": "preregistered; T3 lifecycle packet built for six no-terminal rows without R scoring"
        },
        "source_artifact_inventory_files": 309
      },
      "question": 4
    },
    {
      "answer": "Yes for generated control-pack and lifecycle packet scope; forbidden broker/account/live/hidden labels are absent and all boundary flags stay false/zero.",
      "evidence": {
        "failures": [],
        "status": "PASS"
      },
      "question": 5
    },
    {
      "answer": "Yes; six row-level entries collapse to one duplicate group and two countable timing-target denominator rows, below validation floor.",
      "evidence": {
        "control_pack_sample_floor": {
          "countable_rows": 2,
          "packet_row_count": 6,
          "reason": "n=6 row-level and one duplicate group is an input packet only; validation/promotion sample floor is not met.",
          "sample_floor_for_validation_met": false,
          "unique_duplicate_groups": 1
        },
        "countable_rows": 2,
        "decision": "PASS_REPEATED_ROWS_VISIBLE_NOT_FALSE_INDEPENDENT_EVIDENCE",
        "duplicate_denominator_key_counts": {
          "OTG0-PKT-061|G6_CNR|XAGUSD|2026-05-05|ny|SHORT|73.222|CNR_E0_DECISION_CLOSE_MARKET|CNR_T0_ORIGINAL_TP1": 3,
          "OTG0-PKT-061|G6_CNR|XAGUSD|2026-05-05|ny|SHORT|73.222|CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE|CNR_T0_ORIGINAL_TP1": 3
        },
        "duplicate_group_counts": {
          "G6_CNR|XAGUSD|2026-05-05|ny|SHORT|73.222": 6
        },
        "row_count": 6,
        "unique_duplicate_groups": 1
      },
      "question": 6
    },
    {
      "answer": "Yes; the lifecycle packet sidecar hashes exactly equal the six OTI8 rows with terminal_status=NO_TERMINAL_WITHIN_ORDERED_HORIZON.",
      "evidence": {
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
      "question": 7
    },
    {
      "answer": "Yes; G12 independently recomputed all six labels as stop_after_original_horizon from source-hashed XAGUSD tick files.",
      "evidence": {
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
      "question": 8
    },
    {
      "answer": "Mechanistically, the OTI8 no-terminal state was horizon-limited; under the frozen T3 lifecycle contract, the May 5 NY XAGUSD duplicate group later hit the original stop.",
      "evidence": [
        "The exact six OTI8 no-terminal rows can be re-identified by sidecar hashes and are the only rows in the lifecycle packet.",
        "The XAGUSD May 5/6 local tick extension files exist and their source hashes match the packet references.",
        "Under the frozen CNR_T3_LIFECYCLE_NO_TERMINAL_EXTENSION_V1 contract and SHORT ask-side terminal rule, all six rows first hit the original stop after the original ordered horizon.",
        "The earlier OTI8 no-terminal label was horizon-limited, not proof that the setup never reached a terminal state later.",
        "The six rows are useful failure-anatomy evidence for a late adverse XAGUSD May 5 NY duplicate group."
      ],
      "question": 9
    },
    {
      "answer": "It does not prove R/performance, broker/account realized outcomes, validation, live gating, or promotion.",
      "evidence": [
        "It does not compute or validate R/performance for the six lifecycle rows.",
        "It does not use or prove broker actual-R, account history, live trade results, live order state, or real fill/PnL behavior.",
        "It does not score, rescue, or reclassify the 94 G12-blocked rows.",
        "It does not meet sample-floor, DSR, PBO, effective-N, concentration, validation, promotion, or live-gate requirements.",
        "It does not prove E2/E3/E4 timing fields, T1 fixed-R targets, or T2 structural targets improve outcomes.",
        "It does not justify a new threshold, selector, risk change, prompt change, execution change, or live rule."
      ],
      "question": 10
    },
    {
      "answer": "Yes; the 94 G12-blocked rows remain excluded and G12 did not compute labels or performance for them.",
      "evidence": {
        "blocked_audit_status": "PASS_EXACT_94_BLOCKED_ROWS_EXCLUDED",
        "blocked_overlap_with_accepted": [],
        "blocked_rows": 94,
        "note": "The 94 blocked rows are verified only as excluded; no blocked-row terminal labels or performance were computed by G12.",
        "packet_hashes_from_accepted_manifest": [
          "2d82227ec0dfd01b140471932701e4885dd065fca5c618d5dc2bf0e9c9da76ab",
          "41da6796ddb651413f558333ae52db302fc76a2863f00c204bee6ef37d10a23e",
          "4e76395873c48a3b9f20114c20d0247c92ef80846b170ee9b2f2d52919fa8d04",
          "5a7146782dc6564ac7a04ba163bd3d262ab731c2e1c3b6706ea14aeed979c7bb",
          "5ee22ed74a3eb5c16b1f7857d29346b2713ddbdb8b9a61de9f57c8414889959c",
          "63d08012951489781b7f892fe2d22a968e88101ded2429354aac16e68d3d93c8"
        ],
        "packet_rows_from_blocked_set": [],
        "status": "PASS"
      },
      "question": 11
    },
    {
      "answer": "Yes; residual forensics uses upstream predeclared residual bins and remains discovery-only.",
      "evidence": "non-optimized bins from CNR_RESIDUAL_R_FIELD_AND_BIN_SPEC; no new thresholds selected from outcomes",
      "question": 12
    },
    {
      "answer": "Run the T3 lifecycle expansion/source packet lane first because it is the most source-unblocked way to convert unresolved horizons into categorical evidence without R scoring.",
      "evidence": "G12_CNR_NEXT_BLOCKER_AND_NEXT_ROUTE_LEDGER",
      "question": 13
    }
  ],
  "blocked_packet_outcome_source_read": false,
  "broker_actual_r_accessed": false,
  "canary_calls": 0,
  "control_pack_verification_observed": {
    "completion_can_mark_goal_complete": true,
    "completion_verification_status": "PASS"
  },
  "databento_calls": 0,
  "date_stamp": "2026-05-08",
  "generated_at_utc": "2026-05-08T06:23:47Z",
  "live_effect": false,
  "live_order_state_accessed": false,
  "live_trade_results_accessed": false,
  "mt5_account_calls": 0,
  "mt5_order_calls": 0,
  "order_calls": 0,
  "outcome_review_opened": false,
  "overall_decision": "ACCEPT_AS_RESEARCH_CONTROL_PACK_WITH_BLOCKED_RESULT_AND_PROMOTION_LANES",
  "paid_data_calls": 0,
  "promotion_boundary": {
    "NO_PROMOTION_VERDICT": true,
    "live_effect": false,
    "no_live_surface_changes_authorized": true,
    "outcome_review_opened": false,
    "validation_safe": false
  },
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "schema_version": "g12_cnr_next_model_control_audit_v1",
  "subpart_decisions": [
    {
      "decision": "ACCEPT_AS_RESEARCH_CONTROL_PREREGISTRATION_BLOCK_CURRENT_ROWS",
      "evidence": "G12_CNR_TIMING_TARGET_PREREG_AUDIT",
      "subpart": "E2_E3_E4_timing_preregistration"
    },
    {
      "decision": "ACCEPT_AS_RESEARCH_CONTROL_PREREGISTRATION_WITH_T1_T2_RESULT_BLOCKERS_AND_T3_LIFECYCLE_ONLY",
      "evidence": "G12_CNR_TIMING_TARGET_PREREG_AUDIT",
      "subpart": "T1_T2_T3_target_preregistration"
    },
    {
      "decision": "ACCEPT_AS_RESEARCH_CONTRACTS_KEEP_VALIDATION_SAFE_FALSE",
      "evidence": "G12_CNR_SOURCE_NOLEAK_DUPLICATE_AUDIT",
      "subpart": "source_contracts"
    },
    {
      "decision": "ACCEPT_AS_RESEARCH_CONTROL_NOLEAK_DUPLICATE_SAMPLE_BOUNDARY",
      "evidence": "G12_CNR_SOURCE_NOLEAK_DUPLICATE_AUDIT",
      "subpart": "no_leak_duplicate_samplefloor_controls"
    },
    {
      "decision": "ACCEPT_LIFECYCLE_EVIDENCE_ONLY",
      "evidence": "G12_CNR061_LIFECYCLE_PACKET_AUDIT",
      "subpart": "six_row_lifecycle_packet"
    },
    {
      "decision": "ACCEPT_DISCOVERY_FORENSICS_ONLY",
      "evidence": "G12_CNR_XAGUSD_STOP_AFTER_HORIZON_FORENSICS",
      "subpart": "xagusd_stop_after_horizon_forensics"
    },
    {
      "decision": "ACCEPT_AFTER_G12_VERIFIER_PASS",
      "evidence": "G12_CNR_NEXT_COMPLETION_AUDIT and verify_g12_cnr_next_model_control_audit_2026_05_08.py",
      "subpart": "completion_audit_verifier_tests"
    }
  ],
  "validation_safe": false
}
```
