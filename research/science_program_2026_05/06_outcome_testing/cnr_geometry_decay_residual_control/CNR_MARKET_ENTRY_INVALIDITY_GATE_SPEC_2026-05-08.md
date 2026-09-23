# CNR Market Entry Invalidity Gate Spec - 2026-05-08

Promotion verdict: `NO_PROMOTION_VERDICT`
Validation safe: `false`
Outcome review opened: `false`
Live effect: `false`

The gate runs before any future R scoring.

```json
{
  "account_history_accessed": false,
  "api_calls": 0,
  "artifact_family": "CNR_MARKET_ENTRY_INVALIDITY_GATE_SPEC",
  "blocked_packet_outcome_source_read": false,
  "broker_actual_r_accessed": false,
  "current_matrix_gate_counts": {
    "STOP_INVALID_AT_EXECUTABLE_QUOTE": 18,
    "VALID_FOR_FUTURE_RESULT_LANE_AFTER_SAMPLE_AND_DUPLICATE_AUDIT": 84
  },
  "databento_calls": 0,
  "gate_order": [
    {
      "gate": "G0_SCOPE_ACCEPTED_INPUT_ROW",
      "rule": "row must be accepted by G12 CNR source-field packet audit for the timing/target family under test",
      "terminal_state": "BLOCKED_ROW_EXCLUDED"
    },
    {
      "gate": "G1_SOURCE_HASH_PRESENT_AND_RECOMPUTED",
      "rule": "source_file_paths and source_sha256_hashes must exist and recompute before any scoring",
      "terminal_state": "MISSING_SOURCE_HASH"
    },
    {
      "gate": "G2_QUOTE_SIDE_AND_EXECUTABLE_QUOTE_PRESENT",
      "rule": "LONG uses ask and SHORT uses bid; bid/ask/spread/quote_timestamp_utc must be source-bound",
      "terminal_state": "MISSING_QUOTE_SIDE_OR_EXECUTABLE_QUOTE"
    },
    {
      "gate": "G3_STALE_QUOTE",
      "rule": "future lanes must predeclare max_quote_age_ms; current control records quote_age_ms and proposes 5000ms operational default before outcomes",
      "terminal_state": "STALE_QUOTE"
    },
    {
      "gate": "G4_GEOMETRY_PRESENT",
      "rule": "original entry, original stop, original TP1, side, and original_base_r_price > 0 are required",
      "terminal_state": "MISSING_GEOMETRY"
    },
    {
      "gate": "G5_TARGET_ALREADY_PASSED",
      "rule": "LONG executable quote >= TP1 or SHORT executable quote <= TP1 blocks original TP1 scoring",
      "terminal_state": "TARGET_ALREADY_PASSED_AT_EXECUTABLE_QUOTE"
    },
    {
      "gate": "G6_STOP_INVALID",
      "rule": "LONG executable quote <= original SL or SHORT executable quote >= original SL blocks market-entry scoring",
      "terminal_state": "STOP_INVALID_AT_EXECUTABLE_QUOTE"
    },
    {
      "gate": "G7_DUPLICATE_CONTEXT",
      "rule": "countable_denominator_row=false rows may be context only and cannot add independent denominator",
      "terminal_state": "DUPLICATE_CONTEXT_ROW"
    },
    {
      "gate": "G8_SAMPLE_FLOOR",
      "rule": "no aggregate claim until >=30 unique duplicate groups per frozen timing/target family; validation requires a separate dossier",
      "terminal_state": "SAMPLE_FLOOR_BLOCKED"
    },
    {
      "gate": "G9_FUTURE_RESULT_LANE_ALLOWED",
      "rule": "only after all gates pass may a quarantined result lane open; still no promotion or live effect",
      "terminal_state": "FUTURE_OUTCOME_TEST_ELIGIBLE_ONLY_AFTER_G12_G0_AUDIT"
    }
  ],
  "generated_at_utc": "2026-05-08T03:35:16Z",
  "live_effect": false,
  "live_trade_results_accessed": false,
  "mt5_order_calls": 0,
  "order_calls": 0,
  "outcome_review_opened": false,
  "paid_data_calls": 0,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "validation_safe": false
}
```
