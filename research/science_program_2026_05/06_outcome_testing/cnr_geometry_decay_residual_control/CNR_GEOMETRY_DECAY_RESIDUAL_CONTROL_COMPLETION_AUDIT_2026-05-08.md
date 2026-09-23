# CNR Geometry Decay Residual Control Completion Audit - 2026-05-08

Promotion verdict: `NO_PROMOTION_VERDICT`
Validation safe: `false`
Outcome review opened: `false`
Live effect: `false`

Completion is based on artifact evidence, not tests alone.

```json
{
  "account_history_accessed": false,
  "api_calls": 0,
  "artifact_family": "CNR_GEOMETRY_DECAY_RESIDUAL_CONTROL_COMPLETION_AUDIT",
  "blocked_packet_outcome_source_read": false,
  "broker_actual_r_accessed": false,
  "can_mark_goal_complete_after_verifier_and_scoped_commit": true,
  "databento_calls": 0,
  "generated_at_utc": "2026-05-08T03:35:19Z",
  "live_effect": false,
  "live_trade_results_accessed": false,
  "matrix_summary": {
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
  "mt5_order_calls": 0,
  "no_outcome_scoring_or_threshold_rescue_performed": true,
  "objective_restatement": "Create an input-only CNR geometry-decay/residual-control package from CNR timing, G12 CNR, OTI7, and G12 OTI7 evidence, without opening outcomes or claiming validation.",
  "order_calls": 0,
  "outcome_review_opened": false,
  "paid_data_calls": 0,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "prompt_to_artifact_checklist": [
    {
      "evidence": ".context/LIVE_STATE.md regenerated at session start and read during preflight",
      "requirement": "regenerate/read LIVE_STATE first",
      "status": "PASS"
    },
    {
      "evidence": "required CNR_GEOMETRY_* artifacts plus input row matrix generated under scoped directory",
      "requirement": "build input-only geometry-decay/residual-R/source-control artifacts",
      "status": "PASS"
    },
    {
      "evidence": "builder consumes source rows/G12 ready rows for matrix; OTI7 only appears as quarantined failure-anatomy summary",
      "requirement": "do not score outcomes or backfit thresholds",
      "status": "PASS"
    },
    {
      "evidence": "CNR_RESIDUAL_R_FIELD_AND_BIN_SPEC and CNR_GEOMETRY_DECAY_INPUT_ROW_MATRIX",
      "requirement": "freeze residual_target_r_from_executable_quote and quote displacement fields",
      "status": "PASS"
    },
    {
      "evidence": "CNR_MARKET_ENTRY_INVALIDITY_GATE_SPEC gate order G4-G6 and matrix gate counts",
      "requirement": "invalid stop/target geometry gates",
      "status": "PASS"
    },
    {
      "evidence": "CNR_NOLEAK_DUPLICATE_SAMPLE_AUDIT and CNR_SOURCE_SEARCH_AND_HASH_LEDGER",
      "requirement": "duplicate/sample-floor/no-leak/source-hash rules",
      "status": "PASS"
    },
    {
      "evidence": "CNR_NEXT_ROUTE_BLOCKER_DECISION_LEDGER",
      "requirement": "next-route blockers for CNR_E2/E3/E4 and CNR_T1/T2/T3",
      "status": "PASS"
    },
    {
      "evidence": "next-route ledger records source-field geometry exists for 8 ready rows, OTX quote/path sidecars exist, unified G12-ready geometry+horizon packet absent",
      "requirement": "OTG0-PKT-061 geometry/horizon blocker or sidecar finding",
      "status": "PASS"
    },
    {
      "evidence": "all generated artifacts carry control flags and verifier scans them",
      "requirement": "preserve NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false",
      "status": "PASS"
    },
    {
      "evidence": "scoped CNR geometry-control artifacts were committed, followed only by the permitted research-current-state refresh",
      "requirement": "commit only scoped artifacts",
      "status": "PASS"
    }
  ],
  "required_output_files": [
    "CNR_GEOMETRY_DECAY_RESIDUAL_CONTROL_PREREG_2026-05-08.md",
    "CNR_GEOMETRY_DECAY_RESIDUAL_CONTROL_PREREG_2026-05-08.json",
    "CNR_GEOMETRY_DECAY_INPUT_ROW_MATRIX_2026-05-08.jsonl",
    "CNR_RESIDUAL_R_FIELD_AND_BIN_SPEC_2026-05-08.md",
    "CNR_RESIDUAL_R_FIELD_AND_BIN_SPEC_2026-05-08.json",
    "CNR_MARKET_ENTRY_INVALIDITY_GATE_SPEC_2026-05-08.md",
    "CNR_MARKET_ENTRY_INVALIDITY_GATE_SPEC_2026-05-08.json",
    "CNR_SOURCE_SEARCH_AND_HASH_LEDGER_2026-05-08.md",
    "CNR_SOURCE_SEARCH_AND_HASH_LEDGER_2026-05-08.json",
    "CNR_NOLEAK_DUPLICATE_SAMPLE_AUDIT_2026-05-08.md",
    "CNR_NOLEAK_DUPLICATE_SAMPLE_AUDIT_2026-05-08.json",
    "CNR_NEXT_ROUTE_BLOCKER_DECISION_LEDGER_2026-05-08.md",
    "CNR_NEXT_ROUTE_BLOCKER_DECISION_LEDGER_2026-05-08.json",
    "CNR_CONTEXT_CONTINUITY_AND_INSTRUCTION_COVERAGE_2026-05-08.md",
    "CNR_CONTEXT_CONTINUITY_AND_INSTRUCTION_COVERAGE_2026-05-08.json",
    "CNR_GEOMETRY_DECAY_RESIDUAL_CONTROL_COMPLETION_AUDIT_2026-05-08.md",
    "CNR_GEOMETRY_DECAY_RESIDUAL_CONTROL_COMPLETION_AUDIT_2026-05-08.json"
  ],
  "validation_safe": false
}
```
