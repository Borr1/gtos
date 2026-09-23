# CNR XAGUSD Residual Target Forensics - 2026-05-08

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `false`  
**Outcome review opened:** `false`  
**Live effect:** `false`

```json
{
  "account_history_accessed": false,
  "api_calls": 0,
  "artifact_family": "CNR_XAGUSD_RESIDUAL_TARGET_FORENSICS",
  "bin_source": "non-optimized bins from CNR_RESIDUAL_R_FIELD_AND_BIN_SPEC; no new thresholds selected from outcomes",
  "blocked_packet_outcome_source_read": false,
  "broker_actual_r_accessed": false,
  "canary_calls": 0,
  "databento_calls": 0,
  "date_stamp": "2026-05-08",
  "future_preregistered_hypotheses": [
    "CNR_T1_FIXED_R_FROM_EXECUTABLE_QUOTE can test whether original TP1 residual-decay is the failure source without using outcome-fit target thresholds.",
    "CNR_T2_SOURCE_HASHED_STRUCTURAL_LEVEL can test whether source-ranked structural targets avoid tiny original-TP1 residual wins.",
    "CNR_T3_TERMINAL_TIMEBOX_OR_LIFECYCLE can separate late stop/target lifecycle from four-hour no-terminal labels before R scoring.",
    "CNR_E2/E3/E4 can test whether source emission, latency-aware quotes, or pre-touch triggers remove late-entry geometry artifacts."
  ],
  "generated_at_utc": "2026-05-08T06:01:14Z",
  "live_effect": false,
  "live_order_state_accessed": false,
  "live_trade_results_accessed": false,
  "mechanism_answers": [
    "OTI8's two target-before-stop rows are tiny residual-target wins from executable quote and remain learning evidence only.",
    "The six OTI8 no-terminal rows cluster in one May 5 NY XAGUSD duplicate group with deeper residual target geometry than the May 4 tiny rows.",
    "CNR_E0/E1 plus CNR_T0 original TP1 should be treated as a narrow geometry/timing failure mode until E2/E3/E4 and T1/T2/T3 are preregistered and tested.",
    "No live gate, rescue threshold, selector change, or promotion claim is supported by this forensics artifact."
  ],
  "mt5_account_calls": 0,
  "mt5_order_calls": 0,
  "order_calls": 0,
  "oti7_xagusd_summary": {
    "residual_bin_by_status": {
      "GT_0_TO_0_25_TINY_RESIDUAL": {
        "SCORED_TARGET_FIRST": 6
      },
      "GT_1_0_TO_LT_1_5_BELOW_GTOS_MIN_RR": {
        "SCORED_STOP_FIRST": 18
      },
      "MISSING_OR_STOP_INVALID": {
        "UNSCOREABLE_MISSING_SOURCE_GEOMETRY": 8,
        "UNSCOREABLE_STOP_INVALID_AT_EXECUTABLE_ENTRY": 18
      }
    },
    "row_count": 50,
    "session_counts": {
      "london": 26,
      "ny": 24
    },
    "timing_family_counts": {
      "CNR_E0_DECISION_CLOSE_MARKET": 25,
      "CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE": 25
    },
    "tiny_residual_rows": 6,
    "unique_duplicate_groups": 11
  },
  "oti8_no_terminal_cluster": {
    "duplicate_groups": {
      "G6_CNR|XAGUSD|2026-05-05|ny|SHORT|73.222": 6
    },
    "lifecycle_extension_labels": {
      "stop_after_original_horizon": 6
    },
    "row_count": 6,
    "sessions": {
      "ny": 6
    },
    "timing_families": {
      "CNR_E0_DECISION_CLOSE_MARKET": 3,
      "CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE": 3
    }
  },
  "oti8_xagusd_summary": {
    "residual_bin_by_status": {
      "GT_0_TO_0_25_TINY_RESIDUAL": {
        "TARGET_REACHED_BEFORE_STOP": 2
      },
      "GT_1_0_TO_LT_1_5_BELOW_GTOS_MIN_RR": {
        "NO_TERMINAL_WITHIN_ORDERED_HORIZON": 6
      }
    },
    "row_count": 8,
    "session_counts": {
      "london": 2,
      "ny": 6
    },
    "timing_family_counts": {
      "CNR_E0_DECISION_CLOSE_MARKET": 4,
      "CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE": 4
    },
    "tiny_residual_rows": 2,
    "unique_duplicate_groups": 2
  },
  "outcome_review_opened": false,
  "paid_data_calls": 0,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "schema_version": "cnr_next_model_control_pack_v1",
  "source_artifacts": {
    "matrix": "research/science_program_2026_05/06_outcome_testing/cnr_geometry_decay_residual_control/CNR_GEOMETRY_DECAY_INPUT_ROW_MATRIX_2026-05-08.jsonl",
    "oti7": "research/science_program_2026_05/06_outcome_testing/oti7_cnr_accepted_quarantined_results/OTI7_CNR_RESULT_LEDGER_2026-05-08.jsonl",
    "oti8": "research/science_program_2026_05/06_outcome_testing/oti8_cnr061_quarantined_results/OTI8_CNR061_RESULT_LEDGER_2026-05-08_ROWS.jsonl",
    "residual_bin_spec": "research/science_program_2026_05/06_outcome_testing/cnr_geometry_decay_residual_control/CNR_RESIDUAL_R_FIELD_AND_BIN_SPEC_2026-05-08.json"
  },
  "status": "DISCOVERY_ONLY_MECHANISM_FORENSICS_NO_RESCUE_NO_GATE",
  "validation_boundary": "descriptive discovery only; validation_safe=false and outcome_review_opened=false remain preserved",
  "validation_safe": false,
  "xagusd_matrix_input_only_residual_bin_counts": {
    "GT_0_TO_0_25_TINY_RESIDUAL": 8,
    "GT_1_0_TO_LT_1_5_BELOW_GTOS_MIN_RR": 24,
    "MISSING_OR_STOP_INVALID": 18
  }
}
```
