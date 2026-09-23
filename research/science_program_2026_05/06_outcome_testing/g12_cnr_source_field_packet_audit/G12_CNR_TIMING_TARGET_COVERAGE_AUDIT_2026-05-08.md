# G12 CNR Timing Target Coverage Audit - 2026-05-08

Promotion verdict: `NO_PROMOTION_VERDICT`  
Validation safe: `false`  
Outcome review opened: `false`  
Live effect: `false`

## Coverage Status

PASS

## Families

```json
{
  "packet_ids": [
    "OTG0-PKT-060",
    "OTG0-PKT-061",
    "OTG0-PKT-062",
    "OTG0-PKT-063",
    "OTG0-PKT-066"
  ],
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
  ]
}
```

## Matrix

```json
{
  "CNR_E0_DECISION_CLOSE_MARKET|CNR_T0_ORIGINAL_TP1": {
    "accepted_rows": 51,
    "blocked_rows": 259,
    "context_only_rows": 0,
    "rejected_rows": 0,
    "row_count": 310,
    "target_model_family": "CNR_T0_ORIGINAL_TP1",
    "timing_model_family": "CNR_E0_DECISION_CLOSE_MARKET"
  },
  "CNR_E0_DECISION_CLOSE_MARKET|CNR_T1_FIXED_R_FROM_EXECUTABLE_ENTRY": {
    "accepted_rows": 0,
    "blocked_rows": 310,
    "context_only_rows": 0,
    "rejected_rows": 0,
    "row_count": 310,
    "target_model_family": "CNR_T1_FIXED_R_FROM_EXECUTABLE_ENTRY",
    "timing_model_family": "CNR_E0_DECISION_CLOSE_MARKET"
  },
  "CNR_E0_DECISION_CLOSE_MARKET|CNR_T2_ASOF_STRUCTURAL_LEVEL": {
    "accepted_rows": 0,
    "blocked_rows": 310,
    "context_only_rows": 0,
    "rejected_rows": 0,
    "row_count": 310,
    "target_model_family": "CNR_T2_ASOF_STRUCTURAL_LEVEL",
    "timing_model_family": "CNR_E0_DECISION_CLOSE_MARKET"
  },
  "CNR_E0_DECISION_CLOSE_MARKET|CNR_T3_TIMEBOX_TERMINAL": {
    "accepted_rows": 0,
    "blocked_rows": 310,
    "context_only_rows": 0,
    "rejected_rows": 0,
    "row_count": 310,
    "target_model_family": "CNR_T3_TIMEBOX_TERMINAL",
    "timing_model_family": "CNR_E0_DECISION_CLOSE_MARKET"
  },
  "CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE|CNR_T0_ORIGINAL_TP1": {
    "accepted_rows": 51,
    "blocked_rows": 259,
    "context_only_rows": 0,
    "rejected_rows": 0,
    "row_count": 310,
    "target_model_family": "CNR_T0_ORIGINAL_TP1",
    "timing_model_family": "CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE"
  },
  "CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE|CNR_T1_FIXED_R_FROM_EXECUTABLE_ENTRY": {
    "accepted_rows": 0,
    "blocked_rows": 310,
    "context_only_rows": 0,
    "rejected_rows": 0,
    "row_count": 310,
    "target_model_family": "CNR_T1_FIXED_R_FROM_EXECUTABLE_ENTRY",
    "timing_model_family": "CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE"
  },
  "CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE|CNR_T2_ASOF_STRUCTURAL_LEVEL": {
    "accepted_rows": 0,
    "blocked_rows": 310,
    "context_only_rows": 0,
    "rejected_rows": 0,
    "row_count": 310,
    "target_model_family": "CNR_T2_ASOF_STRUCTURAL_LEVEL",
    "timing_model_family": "CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE"
  },
  "CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE|CNR_T3_TIMEBOX_TERMINAL": {
    "accepted_rows": 0,
    "blocked_rows": 310,
    "context_only_rows": 0,
    "rejected_rows": 0,
    "row_count": 310,
    "target_model_family": "CNR_T3_TIMEBOX_TERMINAL",
    "timing_model_family": "CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE"
  },
  "CNR_E2_SIGNAL_EMIT_FIRST_VALID_TICK|CNR_T0_ORIGINAL_TP1": {
    "accepted_rows": 0,
    "blocked_rows": 310,
    "context_only_rows": 0,
    "rejected_rows": 0,
    "row_count": 310,
    "target_model_family": "CNR_T0_ORIGINAL_TP1",
    "timing_model_family": "CNR_E2_SIGNAL_EMIT_FIRST_VALID_TICK"
  },
  "CNR_E2_SIGNAL_EMIT_FIRST_VALID_TICK|CNR_T1_FIXED_R_FROM_EXECUTABLE_ENTRY": {
    "accepted_rows": 0,
    "blocked_rows": 310,
    "context_only_rows": 0,
    "rejected_rows": 0,
    "row_count": 310,
    "target_model_family": "CNR_T1_FIXED_R_FROM_EXECUTABLE_ENTRY",
    "timing_model_family": "CNR_E2_SIGNAL_EMIT_FIRST_VALID_TICK"
  },
  "CNR_E2_SIGNAL_EMIT_FIRST_VALID_TICK|CNR_T2_ASOF_STRUCTURAL_LEVEL": {
    "accepted_rows": 0,
    "blocked_rows": 310,
    "context_only_rows": 0,
    "rejected_rows": 0,
    "row_count": 310,
    "target_model_family": "CNR_T2_ASOF_STRUCTURAL_LEVEL",
    "timing_model_family": "CNR_E2_SIGNAL_EMIT_FIRST_VALID_TICK"
  },
  "CNR_E2_SIGNAL_EMIT_FIRST_VALID_TICK|CNR_T3_TIMEBOX_TERMINAL": {
    "accepted_rows": 0,
    "blocked_rows": 310,
    "context_only_rows": 0,
    "rejected_rows": 0,
    "row_count": 310,
    "target_model_family": "CNR_T3_TIMEBOX_TERMINAL",
    "timing_model_family": "CNR_E2_SIGNAL_EMIT_FIRST_VALID_TICK"
  },
  "CNR_E3_LATENCY_BOUNDED_DECISION_WINDOW|CNR_T0_ORIGINAL_TP1": {
    "accepted_rows": 0,
    "blocked_rows": 310,
    "context_only_rows": 0,
    "rejected_rows": 0,
    "row_count": 310,
    "target_model_family": "CNR_T0_ORIGINAL_TP1",
    "timing_model_family": "CNR_E3_LATENCY_BOUNDED_DECISION_WINDOW"
  },
  "CNR_E3_LATENCY_BOUNDED_DECISION_WINDOW|CNR_T1_FIXED_R_FROM_EXECUTABLE_ENTRY": {
    "accepted_rows": 0,
    "blocked_rows": 310,
    "context_only_rows": 0,
    "rejected_rows": 0,
    "row_count": 310,
    "target_model_family": "CNR_T1_FIXED_R_FROM_EXECUTABLE_ENTRY",
    "timing_model_family": "CNR_E3_LATENCY_BOUNDED_DECISION_WINDOW"
  },
  "CNR_E3_LATENCY_BOUNDED_DECISION_WINDOW|CNR_T2_ASOF_STRUCTURAL_LEVEL": {
    "accepted_rows": 0,
    "blocked_rows": 310,
    "context_only_rows": 0,
    "rejected_rows": 0,
    "row_count": 310,
    "target_model_family": "CNR_T2_ASOF_STRUCTURAL_LEVEL",
    "timing_model_family": "CNR_E3_LATENCY_BOUNDED_DECISION_WINDOW"
  },
  "CNR_E3_LATENCY_BOUNDED_DECISION_WINDOW|CNR_T3_TIMEBOX_TERMINAL": {
    "accepted_rows": 0,
    "blocked_rows": 310,
    "context_only_rows": 0,
    "rejected_rows": 0,
    "row_count": 310,
    "target_model_family": "CNR_T3_TIMEBOX_TERMINAL",
    "timing_model_family": "CNR_E3_LATENCY_BOUNDED_DECISION_WINDOW"
  },
  "CNR_E4_PRETOUCH_CONTINUATION_TRIGGER|CNR_T0_ORIGINAL_TP1": {
    "accepted_rows": 0,
    "blocked_rows": 310,
    "context_only_rows": 0,
    "rejected_rows": 0,
    "row_count": 310,
    "target_model_family": "CNR_T0_ORIGINAL_TP1",
    "timing_model_family": "CNR_E4_PRETOUCH_CONTINUATION_TRIGGER"
  },
  "CNR_E4_PRETOUCH_CONTINUATION_TRIGGER|CNR_T1_FIXED_R_FROM_EXECUTABLE_ENTRY": {
    "accepted_rows": 0,
    "blocked_rows": 310,
    "context_only_rows": 0,
    "rejected_rows": 0,
    "row_count": 310,
    "target_model_family": "CNR_T1_FIXED_R_FROM_EXECUTABLE_ENTRY",
    "timing_model_family": "CNR_E4_PRETOUCH_CONTINUATION_TRIGGER"
  },
  "CNR_E4_PRETOUCH_CONTINUATION_TRIGGER|CNR_T2_ASOF_STRUCTURAL_LEVEL": {
    "accepted_rows": 0,
    "blocked_rows": 310,
    "context_only_rows": 0,
    "rejected_rows": 0,
    "row_count": 310,
    "target_model_family": "CNR_T2_ASOF_STRUCTURAL_LEVEL",
    "timing_model_family": "CNR_E4_PRETOUCH_CONTINUATION_TRIGGER"
  },
  "CNR_E4_PRETOUCH_CONTINUATION_TRIGGER|CNR_T3_TIMEBOX_TERMINAL": {
    "accepted_rows": 0,
    "blocked_rows": 310,
    "context_only_rows": 0,
    "rejected_rows": 0,
    "row_count": 310,
    "target_model_family": "CNR_T3_TIMEBOX_TERMINAL",
    "timing_model_family": "CNR_E4_PRETOUCH_CONTINUATION_TRIGGER"
  }
}
```

