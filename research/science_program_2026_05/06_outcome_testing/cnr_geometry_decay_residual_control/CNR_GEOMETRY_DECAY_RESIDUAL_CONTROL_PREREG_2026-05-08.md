# CNR Geometry Decay Residual Control Prereg - 2026-05-08

Promotion verdict: `NO_PROMOTION_VERDICT`
Validation safe: `false`
Outcome review opened: `false`
Live effect: `false`

This is an input-only control/preregistration artifact. It does not score outcomes or rescue OTI7.

```json
{
  "account_history_accessed": false,
  "api_calls": 0,
  "artifact_family": "CNR_GEOMETRY_DECAY_RESIDUAL_CONTROL_PREREG",
  "blocked_packet_outcome_source_read": false,
  "broker_actual_r_accessed": false,
  "control_lane_status": "FROZEN_INPUT_ONLY_GEOMETRY_DECAY_RESIDUAL_CONTROL_NO_OUTCOME_OPENING",
  "databento_calls": 0,
  "evidence_chain": [
    "CNR_TIMING_MODEL_PREREGISTRATION freezes CNR_E0-E4 and CNR_T0-T3 families.",
    "CNR_SOURCE_FIELD_PACKET_BUILDER emits 6200 input-only rows with exact blockers.",
    "G12_CNR_SOURCE_FIELD_PACKET_AUDIT accepts 102 input-only E0/E1 + T0 rows and blocks 6098 rows.",
    "OTI7 scores only the accepted rows in quarantine and returns negative discovery evidence.",
    "G12_OTI7 accepts OTI7 as clean negative discovery evidence and requests this input-only control package."
  ],
  "forbidden_actions_confirmed": [
    "no OTI7 rescoring",
    "no blocked-row scoring",
    "no CNR_E2/E3/E4 outcome opening",
    "no CNR_T1/T2/T3 outcome opening",
    "no broker actual-R/account history/live trade result use",
    "no live trading surface changes",
    "no source-safe or outcome-review flips"
  ],
  "frozen_controls": [
    "residual_target_r_from_executable_quote",
    "stop_r_from_executable_quote",
    "quote_displacement_from_original_entry_r",
    "quote_displacement_from_original_stop_r",
    "quote_displacement_from_original_tp1_r",
    "target_already_passed_at_executable_quote",
    "stop_invalid_at_executable_quote",
    "market_entry_geometry_valid_for_original_tp1",
    "duplicate/sample-floor/no-leak/source-hash gates"
  ],
  "generated_at_utc": "2026-05-08T03:35:16Z",
  "input_matrix_summary": {
    "aggregate_sample_floor_status": "BLOCKED_BELOW_30_UNIQUE_GROUPS_PER_TIMING_TARGET_FAMILY",
    "aggregate_sample_floor_unique_groups": 30,
    "by_market_entry_geometry_gate_state": {
      "STOP_INVALID_AT_EXECUTABLE_QUOTE": 18,
      "VALID_FOR_FUTURE_RESULT_LANE_AFTER_SAMPLE_AND_DUPLICATE_AUDIT": 84
    },
    "by_packet": {
      "OTG0-PKT-060": 26,
      "OTG0-PKT-061": 8,
      "OTG0-PKT-062": 32,
      "OTG0-PKT-063": 32,
      "OTG0-PKT-066": 4
    },
    "by_residual_target_r_bin": {
      "GT_0_25_TO_0_5_SMALL_RESIDUAL": 16,
      "GT_0_5_TO_1_0_SUB_ONE_R": 24,
      "GT_0_TO_0_25_TINY_RESIDUAL": 20,
      "GT_1_0_TO_LT_1_5_BELOW_GTOS_MIN_RR": 24,
      "MISSING_OR_STOP_INVALID": 18
    },
    "by_stop_r_bin": {
      "GT_1_0_TO_1_5_EXPANDED_STOP_DISTANCE": 34,
      "GT_1_5_LARGE_STOP_DISTANCE_DECAY": 50,
      "LTE_0_INVALID_STOP_GEOMETRY": 18
    },
    "by_symbol": {
      "GBPJPY": 32,
      "NAS100": 6,
      "XAGUSD": 50,
      "XAUUSD": 14
    },
    "by_timing_target": {
      "CNR_E0_DECISION_CLOSE_MARKET|CNR_T0_ORIGINAL_TP1": 51,
      "CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE|CNR_T0_ORIGINAL_TP1": 51
    },
    "countable_rows": 54,
    "duplicate_context_rows": 48,
    "per_family_countable_unique_duplicate_groups": {
      "CNR_E0_DECISION_CLOSE_MARKET|CNR_T0_ORIGINAL_TP1": 27,
      "CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE|CNR_T0_ORIGINAL_TP1": 27
    },
    "quote_age_ms_range": {
      "max": 2957,
      "min": 4
    },
    "residual_target_r_from_executable_quote_range": {
      "max": 1.2518579686,
      "min": 0.054478301
    },
    "row_count": 102,
    "stop_r_from_executable_quote_range": {
      "max": 2.3698030635,
      "min": -6.2697841727
    },
    "unique_countable_duplicate_groups": 27,
    "unique_duplicate_groups": 30
  },
  "live_effect": false,
  "live_trade_results_accessed": false,
  "mt5_order_calls": 0,
  "negative_result_anchor_not_rescued": {
    "g12_oti7_decision": "ACCEPT_AS_QUARANTINED_NEGATIVE_DISCOVERY_EVIDENCE",
    "negative_result_learning_anchor": "CNR E0/E1 market-entry with original TP1 is accepted as a clean quarantined negative discovery result, not rescued or promoted.",
    "oti7_failure_summary": {
      "all_scored_mean_r": null,
      "status": "OTI7 outcomes are not used to choose thresholds in this package."
    }
  },
  "objective": "Freeze input-only residual target-R, quote displacement, invalidity gates, duplicate/sample-floor, no-leak, source-hash, and next-route blockers before any future CNR timing/target outcome lane.",
  "order_calls": 0,
  "outcome_review_opened": false,
  "paid_data_calls": 0,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "validation_safe": false
}
```
