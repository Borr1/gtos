# CNR Source Field Capture Ledger - 2026-05-07

Promotion verdict: `NO_PROMOTION_VERDICT`  
Validation safe: `false`  
Outcome review opened: `false`  
Live effect: `false`

```json
{
  "account_history_accessed": false,
  "api_calls": 0,
  "artifact_family": "CNR_SOURCE_FIELD_CAPTURE_LEDGER",
  "blocked_packet_outcome_source_read": false,
  "broker_actual_r_accessed": false,
  "canary_calls": 0,
  "capture_summary": {
    "blocked_rows": 6098,
    "packet_blocker_counts": {
      "OTG0-PKT-060": {
        "BLOCKED_WITH_EXACT_SOURCE_FIELD_REQUIREMENTS": 1574,
        "READY_INPUT_ONLY_FOR_G12_G0_AUDIT": 26
      },
      "OTG0-PKT-061": {
        "BLOCKED_WITH_EXACT_SOURCE_FIELD_REQUIREMENTS": 1012,
        "READY_INPUT_ONLY_FOR_G12_G0_AUDIT": 8
      },
      "OTG0-PKT-062": {
        "BLOCKED_WITH_EXACT_SOURCE_FIELD_REQUIREMENTS": 1688,
        "READY_INPUT_ONLY_FOR_G12_G0_AUDIT": 32
      },
      "OTG0-PKT-063": {
        "BLOCKED_WITH_EXACT_SOURCE_FIELD_REQUIREMENTS": 1688,
        "READY_INPUT_ONLY_FOR_G12_G0_AUDIT": 32
      },
      "OTG0-PKT-066": {
        "BLOCKED_WITH_EXACT_SOURCE_FIELD_REQUIREMENTS": 136,
        "READY_INPUT_ONLY_FOR_G12_G0_AUDIT": 4
      }
    },
    "quote_extracted_rows": 2368,
    "ready_input_only_rows": 102,
    "ready_scope_note": "Rows are input-only source-field packets. Ready means source fields are present for G12/G0 audit, not outcome scoring or validation.",
    "row_count": 6200,
    "target_status_counts": {
      "CNR_T0_ORIGINAL_TP1": {
        "BOUND_INPUT_ONLY_ORIGINAL_TP1": 1550
      },
      "CNR_T1_FIXED_R_FROM_EXECUTABLE_ENTRY": {
        "BLOCKED_TARGET_MODEL_NOT_PREBOUND_FOR_THIS_PACKET": 1550
      },
      "CNR_T2_ASOF_STRUCTURAL_LEVEL": {
        "BLOCKED_STRUCTURED_ASOF_LEVEL_SOURCE_NOT_BOUND": 1550
      },
      "CNR_T3_TIMEBOX_TERMINAL": {
        "BLOCKED_TERMINAL_TIMEBOX_POLICY_NOT_BOUND": 1550
      }
    },
    "timing_status_counts": {
      "CNR_E0_DECISION_CLOSE_MARKET": {
        "BLOCKED_NO_SOURCE_HASHED_EXECUTABLE_QUOTE": 56,
        "QUOTE_EXTRACTED_SOURCE_HASHED": 1184
      },
      "CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE": {
        "BLOCKED_NO_SOURCE_HASHED_EXECUTABLE_QUOTE": 56,
        "QUOTE_EXTRACTED_SOURCE_HASHED": 1184
      },
      "CNR_E2_SIGNAL_EMIT_FIRST_VALID_TICK": {
        "BLOCKED_TIMING_TRIGGER_NOT_MATERIALIZED": 1240
      },
      "CNR_E3_LATENCY_BOUNDED_DECISION_WINDOW": {
        "BLOCKED_TIMING_TRIGGER_NOT_MATERIALIZED": 1240
      },
      "CNR_E4_PRETOUCH_CONTINUATION_TRIGGER": {
        "BLOCKED_TIMING_TRIGGER_NOT_MATERIALIZED": 1240
      }
    }
  },
  "databento_calls": 0,
  "exact_remaining_blockers": {
    "latency_clock_chain": "required for CNR_E3; decision request/response timestamps absent",
    "pretouch_trigger": "required for CNR_E4; pretouch trigger id/utc absent",
    "quote_gaps": "where local tick parquet lacks a quote at or before decision_asof_utc, read-only extraction manifest is recorded",
    "signal_emitted_utc": "required for CNR_E2; absent from approved source packet/log fields",
    "target_T1_T2_T3_bindings": "future target models are frozen options but not bound per row before outcome opening"
  },
  "generated_at_utc": "2026-05-07T16:38:18Z",
  "live_effect": false,
  "live_order_state_accessed": false,
  "live_trade_results_accessed": false,
  "mt5_order_calls": 0,
  "order_calls": 0,
  "outcome_review_opened": false,
  "paid_data_calls": 0,
  "parser_version": "cnr_source_field_packet_builder_v1",
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "source_packet_count": 5,
  "source_record_count": 310,
  "target_families": [
    "CNR_T0_ORIGINAL_TP1",
    "CNR_T1_FIXED_R_FROM_EXECUTABLE_ENTRY",
    "CNR_T2_ASOF_STRUCTURAL_LEVEL",
    "CNR_T3_TIMEBOX_TERMINAL"
  ],
  "timing_families": [
    "CNR_E0_DECISION_CLOSE_MARKET",
    "CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE",
    "CNR_E2_SIGNAL_EMIT_FIRST_VALID_TICK",
    "CNR_E3_LATENCY_BOUNDED_DECISION_WINDOW",
    "CNR_E4_PRETOUCH_CONTINUATION_TRIGGER"
  ],
  "validation_safe": false
}
```
