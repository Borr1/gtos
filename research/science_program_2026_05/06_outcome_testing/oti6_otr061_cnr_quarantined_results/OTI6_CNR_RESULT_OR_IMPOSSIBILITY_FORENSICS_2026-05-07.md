# OTI6 CNR Result Or Impossibility Forensics - 2026-05-07

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `false`  
**Outcome review opened:** `false`  
**Live effect:** `false`

- This is a result-or-impossibility forensic artifact, not a promotion or validation result.
- The row is useful evidence about decision latency and target-already-passed states.

```json
{
  "account_history_accessed": false,
  "api_calls": 0,
  "artifact_family": "OTI6_CNR_RESULT_OR_IMPOSSIBILITY_FORENSICS",
  "broker_actual_r_accessed": false,
  "canary_calls": 0,
  "databento_calls": 0,
  "date_stamp": "2026-05-07",
  "evidence": {
    "cnr_e0_entry_ask": 4648.29,
    "decision_quote_timestamp_utc": "2026-05-06T07:14:59.889000Z",
    "first_ordered_path_bid": 4647.67,
    "first_ordered_path_timestamp_utc": "2026-05-06T07:15:00.634000Z",
    "original_tp1": 4582.77,
    "source_file_line": "shadow_logs/continuation_no_retrace_candidates.jsonl:50",
    "target_already_passed_by_price": 65.52,
    "target_already_passed_by_r": 4.62385321
  },
  "experiment_id": "G6-EXP-002-CONTINUATION-NO-RETRACE",
  "future_preregistered_capture_needed": [
    "Capture executable quotes before or during the decision candle if testing an earlier-entry CNR model.",
    "Register a distinct target model if testing continuation beyond original TP1; do not reuse this CNR_E0 target.",
    "Log exact decision latency and quote-side marketability prospectively so target-passed states are explicit."
  ],
  "generated_at_utc": "2026-05-07T10:23:43Z",
  "git_head_at_build": "e8747e13f16045154d81e60503d7a12835314452",
  "impossibility_type": "PREREGISTERED_GEOMETRY_INVALID_TARGET_ALREADY_PASSED_AT_DECISION",
  "live_effect": false,
  "live_order_state_accessed": false,
  "mt5_order_calls": 0,
  "not_a_forced_win_loss": true,
  "order_calls": 0,
  "outcome_review_opened": false,
  "packet_id": "OTG0-PKT-061",
  "paid_data_calls": 0,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "row_teaches": [
    "The original GTOS structural idea had already delivered through TP1 before the CNR_E0 market-entry quote was available.",
    "A no-retrace continuation did occur in lifecycle context, but not in a way that the preregistered decision-close market-entry model can score.",
    "Using CNR_E0 at 4648.29 against original TP1 4582.77 would be an impossible long target geometry, not a profitable R result."
  ],
  "target_record_id": "OTG0-PKT-061|XAUUSD_2026-05-06T07:15:00+00:00",
  "terminal_status": "RESULT_QUARANTINED_DISCOVERY_ONLY_CNR_E0_NOT_ELIGIBLE_TARGET_ALREADY_PASSED_AT_DECISION",
  "validation_safe": false
}
```
