# CNR Timing Model Latency Capture Spec - 2026-05-07

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `false`  
**Outcome review opened:** `false`  
**Live effect:** `false`

```json
{
  "account_history_accessed": false,
  "api_calls": 0,
  "artifact_family": "CNR_TIMING_MODEL_LATENCY_CAPTURE_SPEC",
  "blocked_packet_outcome_source_read": false,
  "broker_actual_r_accessed": false,
  "canary_calls": 0,
  "capture_status": "FROZEN_SPEC_REQUIRES_FUTURE_SHADOW_OR_PACKET_FIELDS_FOR_SIGNAL_EMIT_AND_LATENCY",
  "databento_calls": 0,
  "date_stamp": "2026-05-07",
  "generated_at_utc": "2026-05-07T11:29:43Z",
  "git_branch_at_build": "cnr-timing-model-preregistration",
  "git_head_at_build": "6aa3d07a docs: refresh research state after cnr small-n mandate",
  "lane_id": "CNR_TIMING_MODEL_PREREGISTRATION",
  "latency_clock_chain": [
    "source_bar_close_utc",
    "candidate_detected_utc",
    "signal_emitted_utc",
    "packet_decision_asof_utc",
    "analysis_request_started_utc",
    "analysis_response_received_utc",
    "entry_model_selected_utc",
    "entry_eligible_utc",
    "quote_timestamp_utc",
    "order_intent_created_utc_for_future_shadow_only"
  ],
  "latency_window_policies": [
    {
      "entry_quote_rule": "last quote <= trigger_utc",
      "policy_id": "LATENCY_W0_ASOF_LAST_QUOTE",
      "terminal_if_missing": "NO_ELIGIBLE_EXECUTABLE_QUOTE_AS_OF"
    },
    {
      "entry_quote_rule": "first quote >= trigger_utc and <= trigger_utc+1000ms",
      "policy_id": "LATENCY_W1_FIRST_TICK_AFTER_TRIGGER_0_1000MS",
      "terminal_if_missing": "NO_ELIGIBLE_EXECUTABLE_QUOTE_AS_OF"
    },
    {
      "entry_quote_rule": "first quote >= trigger_utc and <= trigger_utc+15000ms",
      "policy_id": "LATENCY_W2_FIRST_TICK_AFTER_TRIGGER_0_15000MS",
      "terminal_if_missing": "NO_ELIGIBLE_EXECUTABLE_QUOTE_AS_OF"
    }
  ],
  "live_effect": false,
  "live_order_state_accessed": false,
  "live_trade_results_accessed": false,
  "mt5_order_calls": 0,
  "order_calls": 0,
  "outcome_review_opened": false,
  "packet_id": "OTG0-PKT-061",
  "paid_data_calls": 0,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "required_metrics": [
    "candidate_detection_lag_ms",
    "analysis_latency_ms",
    "decision_to_quote_age_ms",
    "entry_eligible_to_quote_age_ms",
    "source_clock_skew_ms",
    "max_allowed_quote_age_ms",
    "latency_bucket_id"
  ],
  "target_record_id": "OTG0-PKT-061|XAUUSD_2026-05-06T07:15:00+00:00",
  "validation_safe": false
}
```
