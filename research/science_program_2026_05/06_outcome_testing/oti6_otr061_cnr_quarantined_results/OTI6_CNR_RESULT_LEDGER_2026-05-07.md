# OTI6 CNR Result Ledger - 2026-05-07

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `false`  
**Outcome review opened:** `false`  
**Live effect:** `false`

- Terminal status: `RESULT_QUARANTINED_DISCOVERY_ONLY_CNR_E0_NOT_ELIGIBLE_TARGET_ALREADY_PASSED_AT_DECISION`
- Synthetic path-R was not computed because CNR_E0 failed preregistered geometry before path scoring.

```json
{
  "account_history_accessed": false,
  "api_calls": 0,
  "artifact_family": "OTI6_CNR_RESULT_LEDGER",
  "broker_actual_r_accessed": false,
  "canary_calls": 0,
  "databento_calls": 0,
  "date_stamp": "2026-05-07",
  "entry_model_id": "CNR_E0_DECISION_CLOSE_MARKET",
  "experiment_id": "G6-EXP-002-CONTINUATION-NO-RETRACE",
  "generated_at_utc": "2026-05-07T10:23:43Z",
  "git_head_at_build": "e8747e13f16045154d81e60503d7a12835314452",
  "label_family": "synthetic_path_r_quarantined_discovery_only_not_computed",
  "live_effect": false,
  "live_order_state_accessed": false,
  "mt5_order_calls": 0,
  "order_calls": 0,
  "ordered_path_summary": {
    "first_ask": 4648.31,
    "first_bid": 4647.67,
    "first_timestamp_utc": "2026-05-06T07:15:00.634000Z",
    "last_ask": 4680.18,
    "last_bid": 4679.63,
    "last_timestamp_utc": "2026-05-06T11:14:59.900000Z",
    "path_end_utc": "2026-05-06T11:15:00Z",
    "path_start_utc": "2026-05-06T07:15:00Z",
    "post_horizon_first_timestamp_utc": "2026-05-06T11:15:00.335000Z",
    "row_count": 88060
  },
  "outcome_review_opened": false,
  "packet_id": "OTG0-PKT-061",
  "paid_data_calls": 0,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "r_scoring_attempted": false,
  "r_scoring_blocked_before_path_scoring_reason": "LONG executable ask is above original TP1 before CNR_E0 can enter.",
  "record_count": 1,
  "result_row": {
    "base_r_price": 14.17,
    "candidate_id": "XAUUSD_2026-05-06T07:15:00+00:00",
    "cnr_e0_executable_entry": 4648.29,
    "decision_asof_utc": "2026-05-06T07:15:00Z",
    "decision_quote_timestamp_utc": "2026-05-06T07:14:59.889000Z",
    "original_entry_price": 4561.52,
    "original_stop_loss": 4547.35,
    "original_take_profit_1": 4582.77,
    "packet_id": "OTG0-PKT-061",
    "record_id": "OTG0-PKT-061|XAUUSD_2026-05-06T07:15:00+00:00",
    "result_status": "RESULT_QUARANTINED_DISCOVERY_ONLY_CNR_E0_NOT_ELIGIBLE_TARGET_ALREADY_PASSED_AT_DECISION",
    "side": "LONG",
    "synthetic_path_r": null,
    "synthetic_path_r_status": "NOT_COMPUTED_PREREGISTERED_GEOMETRY_NOT_ELIGIBLE",
    "target_already_passed_at_decision": true
  },
  "result_status": "RESULT_QUARANTINED_DISCOVERY_ONLY_CNR_E0_NOT_ELIGIBLE_TARGET_ALREADY_PASSED_AT_DECISION",
  "synthetic_path_r": null,
  "target_record_id": "OTG0-PKT-061|XAUUSD_2026-05-06T07:15:00+00:00",
  "terminal_status_counts": {
    "RESULT_QUARANTINED_DISCOVERY_ONLY_CNR_E0_NOT_ELIGIBLE_TARGET_ALREADY_PASSED_AT_DECISION": 1
  },
  "validation_safe": false
}
```
