# CNR Timing Model Preregistration - 2026-05-07

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `false`  
**Outcome review opened:** `false`  
**Live effect:** `false`

This is a control/preregistration artifact only. It freezes future CNR timing and target model families before any new outcome opening.
The OTI6 correct-direction path is treated as failure anatomy, not as a scoreable rescue.

```json
{
  "account_history_accessed": false,
  "api_calls": 0,
  "artifact_family": "CNR_TIMING_MODEL_PREREGISTRATION",
  "blocked_packet_outcome_source_read": false,
  "broker_actual_r_accessed": false,
  "canary_calls": 0,
  "control_lane_status": "FROZEN_PREREGISTRATION_CONTROL_PACKAGE_NO_OUTCOME_OPENING",
  "databento_calls": 0,
  "date_stamp": "2026-05-07",
  "evidence_summary": {
    "accepted_g12_decision": "ACCEPT_AS_QUARANTINED_TARGET_ALREADY_PASSED_DISCOVERY_EVIDENCE",
    "candidate_geometry_source": {
      "line_no": 50,
      "row_key": "97a72dd896b0b4fb88a0b9aadb9295e6",
      "source_file": "shadow_logs/continuation_no_retrace_candidates.jsonl",
      "source_file_sha256": "30ae312b24db1a0808928d5c025aa0cb4c6fb626a239657e179512c45b2cdd76",
      "source_line_sha256": "27d379d158972f568f3c854aeaabae6604183f0283d988d11889380c140b3691"
    },
    "decision_asof_utc": "2026-05-06T07:15:00+00:00",
    "decision_quote": {
      "ask": 4648.29,
      "bid": 4647.65,
      "decision_rows_lte_071500": 875,
      "executable_decision_price_long_ask": 4648.29,
      "quote_timestamp_utc": "2026-05-06T07:14:59.889000Z"
    },
    "distance_diagnostics": {
      "executable_entry_minus_original_entry_price": 86.77,
      "executable_entry_minus_original_entry_r": 6.12350035,
      "executable_entry_minus_tp1_price": 65.52,
      "executable_entry_minus_tp1_r": 4.62385321,
      "tp1_minus_original_entry_price": 21.25,
      "tp1_minus_original_entry_r": 1.49964714
    },
    "duplicate_group_id": "G6_CNR|XAUUSD|2026-05-06|london|LONG|4561.52",
    "g12_mechanism_interpretation": "CNR_MECHANISM_NOT_DEAD_CNR_E0_DECISION_CLOSE_MARKET_MODEL_TOO_LATE_FOR_THIS_ROW",
    "label_family": "synthetic_path_r_quarantined_discovery_only_not_computed",
    "ordered_path_context_only": {
      "context_only_not_scored": true,
      "first_ask": 4648.31,
      "first_bid": 4647.67,
      "first_timestamp_utc": "2026-05-06T07:15:00.634000Z",
      "last_ask": 4680.18,
      "last_bid": 4679.63,
      "last_timestamp_utc": "2026-05-06T11:14:59.900000Z",
      "not_scored_reason": "LONG executable ask is above original TP1 before CNR_E0 can enter.",
      "path_end_utc": "2026-05-06T11:15:00Z",
      "path_start_utc": "2026-05-06T07:15:00Z",
      "post_horizon_first_timestamp_utc": "2026-05-06T11:15:00.335000Z",
      "row_count": 88060
    },
    "original_gtos_geometry": {
      "base_r_price": 14.17,
      "entry_price": 4561.52,
      "geometry_valid": true,
      "side": "LONG",
      "stop_loss": 4547.35,
      "take_profit_1": 4582.77
    },
    "packet_record_count": 1,
    "parquet_hash": "6f7e7e7e19635275916c78bb98678edf5f0cd80bebf2babd9f73017c740398ff",
    "r_scoring_attempted": false,
    "result_status": "RESULT_QUARANTINED_DISCOVERY_ONLY_CNR_E0_NOT_ELIGIBLE_TARGET_ALREADY_PASSED_AT_DECISION",
    "synthetic_path_r": null,
    "target_already_passed_at_decision": true,
    "terminal_status": "RESULT_QUARANTINED_DISCOVERY_ONLY_CNR_E0_NOT_ELIGIBLE_TARGET_ALREADY_PASSED_AT_DECISION"
  },
  "future_model_families": [
    {
      "context_timeframes": [
        "M1",
        "M5",
        "M15",
        "H1",
        "H4",
        "D1",
        "session"
      ],
      "duplicate_denominator": "G6_CNR|symbol|trade_date|session|side|original_entry_price",
      "executable_quote_source_and_side": "source-hashed quote at or immediately before decision_asof_utc; LONG uses ask, SHORT uses bid",
      "execution_timeframe": "tick_or_quote",
      "forbidden_fields": [
        "synthetic_path_r",
        "broker_actual_r",
        "account_history",
        "live_trade_result",
        "post_entry_path_extremes_for_model_definition",
        "target_hit_timestamp",
        "stop_hit_timestamp",
        "result_status"
      ],
      "model_family_id": "CNR_E0_DECISION_CLOSE_MARKET",
      "oti6_record_status": "target_already_passed_before_eligible_executable_entry",
      "readiness": "FROZEN_BASELINE_FAILED_FOR_OTI6_RECORD_READY_AS_CONTROL",
      "sample_floor": "single-row result-or-impossibility allowed after G12/G0 packet audit; no aggregate claim until >=30 unique duplicate groups and no validation claim until validation dossier floor passes",
      "source_whitelist": [
        "packet_id",
        "record_id",
        "symbol",
        "side",
        "session",
        "decision_asof_utc",
        "candidate_close_utc",
        "signal_emitted_utc",
        "original_entry_price",
        "original_stop_loss",
        "original_take_profit_1",
        "duplicate_group_id",
        "source_sha256",
        "quote_timestamp_utc",
        "bid",
        "ask",
        "spread",
        "predecision_context_fields"
      ],
      "stop_or_invalidity_rule": "original GTOS stop/invalidity geometry unless another stop model is preregistered before outcomes",
      "target_geometry_rule": "default CNR_T0_ORIGINAL_TP1 unless a future packet explicitly binds another target model before outcomes",
      "terminal_states": [
        "TARGET_ALREADY_PASSED_BEFORE_ELIGIBLE_EXECUTABLE_ENTRY",
        "NO_ELIGIBLE_EXECUTABLE_QUOTE_AS_OF",
        "INSUFFICIENT_PRE_ENTRY_PATH_EVIDENCE",
        "SAME_BAR_OR_TERMINAL_ORDER_AMBIGUITY",
        "MISSING_SOURCE_HASH",
        "MISSING_QUOTE_SIDE",
        "DUPLICATE_DENOMINATOR_EXCLUSION",
        "CONTEXT_ONLY_ROW",
        "FUTURE_OUTCOME_TEST_ELIGIBLE_ONLY_AFTER_G12_G0_AUDIT"
      ],
      "trigger_timeframe": "M15 decision close",
      "trigger_timestamp_rule": "decision_asof_utc from frozen packet"
    },
    {
      "context_timeframes": [
        "M1",
        "M5",
        "M15",
        "H1",
        "H4",
        "D1",
        "session"
      ],
      "duplicate_denominator": "G6_CNR|symbol|trade_date|session|side|original_entry_price",
      "executable_quote_source_and_side": "last source-hashed executable quote <= candidate_close_utc; LONG uses ask, SHORT uses bid; max quote age declared in packet",
      "execution_timeframe": "tick_or_quote",
      "forbidden_fields": [
        "synthetic_path_r",
        "broker_actual_r",
        "account_history",
        "live_trade_result",
        "post_entry_path_extremes_for_model_definition",
        "target_hit_timestamp",
        "stop_hit_timestamp",
        "result_status"
      ],
      "model_family_id": "CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE",
      "oti6_record_status": "not_retroactively_scoreable; candidate_close_quote cannot be used to rescue OTI6 after seeing target-already-passed state",
      "readiness": "FROZEN_FOR_FUTURE_PACKET_AUDIT_BLOCKED_WHEN_CANDIDATE_CLOSE_QUOTE_MISSING",
      "sample_floor": "same as CNR_E0; one row can be impossibility evidence only",
      "source_whitelist": [
        "packet_id",
        "record_id",
        "symbol",
        "side",
        "session",
        "decision_asof_utc",
        "candidate_close_utc",
        "signal_emitted_utc",
        "original_entry_price",
        "original_stop_loss",
        "original_take_profit_1",
        "duplicate_group_id",
        "source_sha256",
        "quote_timestamp_utc",
        "bid",
        "ask",
        "spread",
        "predecision_context_fields",
        "candidate_close_source_line",
        "candidate_close_source_sha256"
      ],
      "stop_or_invalidity_rule": "original GTOS SL for T0 or preregistered invalidity for T1/T2/T3",
      "target_geometry_rule": "CNR_T0_ORIGINAL_TP1 by default; CNR_T1/T2/T3 only if registered in packet before outcomes",
      "terminal_states": [
        "TARGET_ALREADY_PASSED_BEFORE_ELIGIBLE_EXECUTABLE_ENTRY",
        "NO_ELIGIBLE_EXECUTABLE_QUOTE_AS_OF",
        "INSUFFICIENT_PRE_ENTRY_PATH_EVIDENCE",
        "SAME_BAR_OR_TERMINAL_ORDER_AMBIGUITY",
        "MISSING_SOURCE_HASH",
        "MISSING_QUOTE_SIDE",
        "DUPLICATE_DENOMINATOR_EXCLUSION",
        "CONTEXT_ONLY_ROW",
        "FUTURE_OUTCOME_TEST_ELIGIBLE_ONLY_AFTER_G12_G0_AUDIT"
      ],
      "trigger_timeframe": "M15 candidate close or explicit signal close",
      "trigger_timestamp_rule": "candidate_close_utc from source-hashed candidate log, not reconstructed from later path"
    },
    {
      "context_timeframes": [
        "M1",
        "M5",
        "M15",
        "H1",
        "H4",
        "D1",
        "session"
      ],
      "duplicate_denominator": "G6_CNR|symbol|trade_date|session|side|original_entry_price",
      "executable_quote_source_and_side": "first source-hashed tick/quote >= signal_emitted_utc and <= signal_emitted_utc + declared latency cap; LONG uses ask, SHORT uses bid",
      "execution_timeframe": "tick_or_quote",
      "forbidden_fields": [
        "synthetic_path_r",
        "broker_actual_r",
        "account_history",
        "live_trade_result",
        "post_entry_path_extremes_for_model_definition",
        "target_hit_timestamp",
        "stop_hit_timestamp",
        "result_status"
      ],
      "model_family_id": "CNR_E2_SIGNAL_EMIT_FIRST_VALID_TICK",
      "oti6_record_status": "blocked_current_artifacts_do_not_prove_signal_emit_timestamp_before_target_passage",
      "readiness": "BLOCKED_UNTIL_SIGNAL_EMITTED_UTC_AND_TICK_QUOTE_SOURCE_ARE_PACKET_FIELDS",
      "sample_floor": "requires >=30 unique duplicate groups before aggregate result summary; not computable otherwise",
      "source_whitelist": [
        "packet_id",
        "record_id",
        "symbol",
        "side",
        "session",
        "decision_asof_utc",
        "candidate_close_utc",
        "signal_emitted_utc",
        "original_entry_price",
        "original_stop_loss",
        "original_take_profit_1",
        "duplicate_group_id",
        "source_sha256",
        "quote_timestamp_utc",
        "bid",
        "ask",
        "spread",
        "predecision_context_fields",
        "signal_emitted_utc",
        "signal_logger_schema",
        "latency_cap_ms"
      ],
      "stop_or_invalidity_rule": "must bind original stop or preregistered timing invalidity before outcomes",
      "target_geometry_rule": "must bind CNR_T0/T1/T2/T3 in the packet before outcomes",
      "terminal_states": [
        "TARGET_ALREADY_PASSED_BEFORE_ELIGIBLE_EXECUTABLE_ENTRY",
        "NO_ELIGIBLE_EXECUTABLE_QUOTE_AS_OF",
        "INSUFFICIENT_PRE_ENTRY_PATH_EVIDENCE",
        "SAME_BAR_OR_TERMINAL_ORDER_AMBIGUITY",
        "MISSING_SOURCE_HASH",
        "MISSING_QUOTE_SIDE",
        "DUPLICATE_DENOMINATOR_EXCLUSION",
        "CONTEXT_ONLY_ROW",
        "FUTURE_OUTCOME_TEST_ELIGIBLE_ONLY_AFTER_G12_G0_AUDIT"
      ],
      "trigger_timeframe": "event timestamp from logger",
      "trigger_timestamp_rule": "first system signal_emitted_utc from source-hashed logger before AI/decision latency, if such field exists"
    },
    {
      "context_timeframes": [
        "M1",
        "M5",
        "M15",
        "H1",
        "H4",
        "D1",
        "session"
      ],
      "duplicate_denominator": "G6_CNR|symbol|trade_date|session|side|original_entry_price",
      "executable_quote_source_and_side": "first or last quote in the declared window, explicitly selected in packet; LONG ask, SHORT bid",
      "execution_timeframe": "tick_or_quote",
      "forbidden_fields": [
        "synthetic_path_r",
        "broker_actual_r",
        "account_history",
        "live_trade_result",
        "post_entry_path_extremes_for_model_definition",
        "target_hit_timestamp",
        "stop_hit_timestamp",
        "result_status"
      ],
      "model_family_id": "CNR_E3_LATENCY_BOUNDED_DECISION_WINDOW",
      "oti6_record_status": "conceptually_available_future_model; not valid rescue because OTI6 latency rule was not pre-bound",
      "readiness": "FROZEN_AS_FUTURE_LATENCY_MODEL_REQUIRES_CAPTURE_FIELDS",
      "sample_floor": "requires latency-source coverage report plus >=30 unique duplicate groups before aggregate result summary",
      "source_whitelist": [
        "packet_id",
        "record_id",
        "symbol",
        "side",
        "session",
        "decision_asof_utc",
        "candidate_close_utc",
        "signal_emitted_utc",
        "original_entry_price",
        "original_stop_loss",
        "original_take_profit_1",
        "duplicate_group_id",
        "source_sha256",
        "quote_timestamp_utc",
        "bid",
        "ask",
        "spread",
        "predecision_context_fields",
        "decision_request_sent_utc",
        "decision_response_received_utc",
        "latency_policy_id"
      ],
      "stop_or_invalidity_rule": "pre-bound stop or invalidity; missing stop blocks result",
      "target_geometry_rule": "target model pre-bound; target-already-passed gate checked before scoring",
      "terminal_states": [
        "TARGET_ALREADY_PASSED_BEFORE_ELIGIBLE_EXECUTABLE_ENTRY",
        "NO_ELIGIBLE_EXECUTABLE_QUOTE_AS_OF",
        "INSUFFICIENT_PRE_ENTRY_PATH_EVIDENCE",
        "SAME_BAR_OR_TERMINAL_ORDER_AMBIGUITY",
        "MISSING_SOURCE_HASH",
        "MISSING_QUOTE_SIDE",
        "DUPLICATE_DENOMINATOR_EXCLUSION",
        "CONTEXT_ONLY_ROW",
        "FUTURE_OUTCOME_TEST_ELIGIBLE_ONLY_AFTER_G12_G0_AUDIT"
      ],
      "trigger_timeframe": "event timestamp plus M15 decision context",
      "trigger_timestamp_rule": "decision_request_sent_utc or decision_asof_utc plus predeclared latency window, not chosen after path inspection"
    },
    {
      "context_timeframes": [
        "H1",
        "H4",
        "D1",
        "session"
      ],
      "duplicate_denominator": "G6_CNR|symbol|trade_date|session|side|original_entry_price|pretouch_trigger_id",
      "executable_quote_source_and_side": "first eligible quote after the pretouch trigger within declared latency cap; LONG ask, SHORT bid",
      "execution_timeframe": "tick_or_quote",
      "forbidden_fields": [
        "synthetic_path_r",
        "broker_actual_r",
        "account_history",
        "live_trade_result",
        "post_entry_path_extremes_for_model_definition",
        "target_hit_timestamp",
        "stop_hit_timestamp",
        "result_status"
      ],
      "model_family_id": "CNR_E4_PRETOUCH_CONTINUATION_TRIGGER",
      "oti6_record_status": "blocked_without_predecision_pretouch_trigger_logger; cannot be inferred from recovered successful path",
      "readiness": "BLOCKED_PENDING_PREFILL_OR_PRETOUCH_ASOF_STRUCTURE_LOGGER",
      "sample_floor": "requires separate denominator audit because multiple pretouch triggers may exist inside one original opportunity",
      "source_whitelist": [
        "packet_id",
        "record_id",
        "symbol",
        "side",
        "session",
        "decision_asof_utc",
        "candidate_close_utc",
        "signal_emitted_utc",
        "original_entry_price",
        "original_stop_loss",
        "original_take_profit_1",
        "duplicate_group_id",
        "source_sha256",
        "quote_timestamp_utc",
        "bid",
        "ask",
        "spread",
        "predecision_context_fields",
        "pretouch_trigger_id",
        "pretouch_trigger_utc",
        "pretouch_source_sha256"
      ],
      "stop_or_invalidity_rule": "predeclared invalidation such as impulse origin, original SL, or structure level",
      "target_geometry_rule": "must bind target model before outcomes; original TP1 can only be used if not already passed",
      "terminal_states": [
        "TARGET_ALREADY_PASSED_BEFORE_ELIGIBLE_EXECUTABLE_ENTRY",
        "NO_ELIGIBLE_EXECUTABLE_QUOTE_AS_OF",
        "INSUFFICIENT_PRE_ENTRY_PATH_EVIDENCE",
        "SAME_BAR_OR_TERMINAL_ORDER_AMBIGUITY",
        "MISSING_SOURCE_HASH",
        "MISSING_QUOTE_SIDE",
        "DUPLICATE_DENOMINATOR_EXCLUSION",
        "CONTEXT_ONLY_ROW",
        "FUTURE_OUTCOME_TEST_ELIGIBLE_ONLY_AFTER_G12_G0_AUDIT"
      ],
      "trigger_timeframe": "M1/M5/M15 source-safe pre-entry path",
      "trigger_timestamp_rule": "predefined no-retrace/impulse state before target passage, sourced from M1/M5/M15 as-of rows"
    }
  ],
  "generated_at_utc": "2026-05-07T11:29:43Z",
  "git_branch_at_build": "cnr-timing-model-preregistration",
  "git_head_at_build": "6aa3d07a docs: refresh research state after cnr small-n mandate",
  "lane_id": "CNR_TIMING_MODEL_PREREGISTRATION",
  "live_effect": false,
  "live_order_state_accessed": false,
  "live_trade_results_accessed": false,
  "mt5_order_calls": 0,
  "not_scored_or_rescued": [
    "No earlier entry was scored.",
    "No alternate target was scored.",
    "The post-decision upward path is context-only failure anatomy.",
    "No validation or promotion claim is made."
  ],
  "order_calls": 0,
  "outcome_review_opened": false,
  "packet_id": "OTG0-PKT-061",
  "paid_data_calls": 0,
  "primary_answer": "CNR_E0 failed for OTG0-PKT-061 because the eligible decision-close market quote was already beyond original TP1; future CNR timing may only test separately frozen entry/target models with source-hashed quote-side and target-already-passed gates.",
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "target_models": [
    {
      "definition": "Use original GTOS TP1 from the candidate geometry frozen before the timing-model outcome opening.",
      "eligibility_rule": "Eligible only if the executable entry is not already beyond TP1 in the favorable direction and original entry/SL/TP geometry is valid.",
      "status_for_oti6_record": "NOT_ELIGIBLE_TARGET_ALREADY_PASSED_AT_DECISION",
      "target_model_id": "CNR_T0_ORIGINAL_TP1"
    },
    {
      "definition": "A predeclared fixed-R target measured from the timing model's executable quote using a predeclared stop or invalidity distance.",
      "eligibility_rule": "Requires a frozen R multiple, stop model, quote-side rule, and source-hashed executable quote before outcome opening.",
      "status_for_oti6_record": "FUTURE_ONLY_REJECTED_AS_OTI6_RESCUE",
      "target_model_id": "CNR_T1_FIXED_R_FROM_EXECUTABLE_ENTRY"
    },
    {
      "definition": "A target from an as-of H1/H4/M15 structure source such as next liquidity, swing, OB boundary, or FVG edge.",
      "eligibility_rule": "Requires structured level id, timestamp, parser, source hash, and level selected before any post-entry path is opened.",
      "status_for_oti6_record": "BLOCKED_PENDING_STRUCTURED_ASOF_LEVEL_SOURCE",
      "target_model_id": "CNR_T2_ASOF_STRUCTURAL_LEVEL"
    },
    {
      "definition": "A predeclared time horizon terminal state such as fixed 4h close or session close without tuning to path extremes.",
      "eligibility_rule": "Requires quote-side terminal pricing, cost rule, and same-bar/tick ordering policy before outcome opening.",
      "status_for_oti6_record": "FUTURE_ONLY_REJECTED_AS_OTI6_RESCUE",
      "target_model_id": "CNR_T3_TIMEBOX_TERMINAL"
    }
  ],
  "target_record_id": "OTG0-PKT-061|XAUUSD_2026-05-06T07:15:00+00:00",
  "terminal_states": [
    {
      "meaning": "For LONG, eligible executable ask is at or beyond target before entry. For SHORT, eligible executable bid is at or beyond target before entry.",
      "result_handling": "not_scoreable_for_that_target_model",
      "terminal_state": "TARGET_ALREADY_PASSED_BEFORE_ELIGIBLE_EXECUTABLE_ENTRY"
    },
    {
      "meaning": "No source-hashed quote exists at or before the trigger timestamp or inside the predeclared latency window.",
      "result_handling": "blocked_missing_quote_source",
      "terminal_state": "NO_ELIGIBLE_EXECUTABLE_QUOTE_AS_OF"
    },
    {
      "meaning": "The candidate trigger exists, but source-hashed tick/M1/M5 evidence needed to prove timing eligibility before entry is absent.",
      "result_handling": "blocked_missing_pre_entry_path",
      "terminal_state": "INSUFFICIENT_PRE_ENTRY_PATH_EVIDENCE"
    },
    {
      "meaning": "Entry, stop, target, invalidity, or terminal state order cannot be proved with ordered tick/M1 evidence.",
      "result_handling": "ambiguous_or_bounded_not_guessed",
      "terminal_state": "SAME_BAR_OR_TERMINAL_ORDER_AMBIGUITY"
    },
    {
      "meaning": "A referenced source file lacks a recorded SHA256 or reproducible lineage row.",
      "result_handling": "blocked_source_hash",
      "terminal_state": "MISSING_SOURCE_HASH"
    },
    {
      "meaning": "The source lacks bid/ask or a declared executable side rule.",
      "result_handling": "blocked_quote_side",
      "terminal_state": "MISSING_QUOTE_SIDE"
    },
    {
      "meaning": "A row is a duplicate within the same opportunity denominator and must not add an independent sample.",
      "result_handling": "excluded_from_primary_denominator",
      "terminal_state": "DUPLICATE_DENOMINATOR_EXCLUSION"
    },
    {
      "meaning": "A row can explain failure anatomy or source coverage but cannot enter a future result denominator.",
      "result_handling": "context_only_no_result_claim",
      "terminal_state": "CONTEXT_ONLY_ROW"
    },
    {
      "meaning": "All source, no-leak, duplicate, timing, target, and sample-floor controls pass packet audit before any outcome opening.",
      "result_handling": "eligible_for_future_quarantined_result_lane_not_promotion",
      "terminal_state": "FUTURE_OUTCOME_TEST_ELIGIBLE_ONLY_AFTER_G12_G0_AUDIT"
    }
  ],
  "validation_safe": false
}
```
