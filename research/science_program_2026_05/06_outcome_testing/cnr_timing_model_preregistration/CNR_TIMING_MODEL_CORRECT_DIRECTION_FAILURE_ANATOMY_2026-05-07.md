# CNR Timing Model Correct Direction Failure Anatomy - 2026-05-07

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `false`  
**Outcome review opened:** `false`  
**Live effect:** `false`

The recovered path moved upward after the decision quote, but the baseline CNR_E0 original TP1 target was already passed before eligible entry.
No earlier-entry or alternate-target result is opened here.

```json
{
  "account_history_accessed": false,
  "anatomy_verdict": "CORRECT_DIRECTION_MOVE_STUDIED_WITHOUT_SCORING_OR_RESCUE",
  "api_calls": 0,
  "artifact_family": "CNR_TIMING_MODEL_CORRECT_DIRECTION_FAILURE_ANATOMY",
  "blocked_packet_outcome_source_read": false,
  "broker_actual_r_accessed": false,
  "canary_calls": 0,
  "databento_calls": 0,
  "date_stamp": "2026-05-07",
  "earliest_future_entry_routes": [
    {
      "oti6_current_status": "not scoreable as rescue",
      "route": "candidate_close_quote",
      "status": "provable_only_if_candidate_close_quote_source_exists_before_outcome_opening"
    },
    {
      "oti6_current_status": "cannot infer from upward recovered path",
      "route": "signal_emit_first_tick",
      "status": "blocked_current_artifacts_need signal_emitted_utc and quote stream binding"
    },
    {
      "oti6_current_status": "forbidden if derived from known target-already-passed path",
      "route": "pretouch_continuation_trigger",
      "status": "blocked_until pre-entry trigger logger/parser exists"
    }
  ],
  "failure_type": "ENTRY_CLOCK_TOO_LATE_FOR_ORIGINAL_TARGET_GEOMETRY",
  "generated_at_utc": "2026-05-07T11:29:43Z",
  "git_branch_at_build": "cnr-timing-model-preregistration",
  "git_head_at_build": "6aa3d07a docs: refresh research state after cnr small-n mandate",
  "lane_id": "CNR_TIMING_MODEL_PREREGISTRATION",
  "live_effect": false,
  "live_order_state_accessed": false,
  "live_trade_results_accessed": false,
  "mt5_order_calls": 0,
  "order_calls": 0,
  "outcome_review_opened": false,
  "packet_id": "OTG0-PKT-061",
  "paid_data_calls": 0,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "target_eligibility": {
    "continuation_target": "future-only if preregistered before outcomes; rejected as OTI6 rescue",
    "original_tp1": "invalid_for_CNR_E0_on_OTI6_record_because_target_already_passed",
    "timebox_target": "future-only if preregistered before outcomes; rejected as OTI6 rescue"
  },
  "target_record_id": "OTG0-PKT-061|XAUUSD_2026-05-06T07:15:00+00:00",
  "timeline": [
    {
      "event": "original_candidate_geometry_source",
      "evidence": {
        "line_no": 50,
        "row_key": "97a72dd896b0b4fb88a0b9aadb9295e6",
        "source_file": "shadow_logs/continuation_no_retrace_candidates.jsonl",
        "source_file_sha256": "30ae312b24db1a0808928d5c025aa0cb4c6fb626a239657e179512c45b2cdd76",
        "source_line_sha256": "27d379d158972f568f3c854aeaabae6604183f0283d988d11889380c140b3691"
      },
      "interpretation": "Original GTOS geometry existed before this lane; entry 4561.52, SL 4547.35, TP1 4582.77.",
      "timestamp_utc": "2026-05-06T07:15:00+00:00"
    },
    {
      "event": "decision_close_asof",
      "evidence": "OTR061 packet proposal decision_asof_utc",
      "interpretation": "CNR_E0 trigger clock for the failed baseline model.",
      "timestamp_utc": "2026-05-06T07:15:00+00:00"
    },
    {
      "event": "decision_quote",
      "evidence": {
        "ask": 4648.29,
        "bid": 4647.65,
        "decision_rows_lte_071500": 875,
        "executable_decision_price_long_ask": 4648.29,
        "quote_timestamp_utc": "2026-05-06T07:14:59.889000Z"
      },
      "interpretation": "LONG executable ask 4648.29 was already beyond original TP1 4582.77.",
      "timestamp_utc": "2026-05-06T07:14:59.889000Z"
    },
    {
      "event": "first_ordered_tick_after_decision",
      "evidence": {
        "first_ask": 4648.31,
        "first_bid": 4647.67
      },
      "interpretation": "Path ordering exists but is context-only in this preregistration lane.",
      "timestamp_utc": "2026-05-06T07:15:00.634000Z"
    },
    {
      "event": "post_horizon_tick",
      "evidence": {
        "last_ask_before_horizon": 4680.18,
        "last_bid_before_horizon": 4679.63
      },
      "interpretation": "The path continued upward, but no R score or alternate target is opened here.",
      "timestamp_utc": "2026-05-06T11:15:00.335000Z"
    }
  ],
  "validation_safe": false,
  "what_cnr_e0_missed": "The no-retrace move had already traversed original TP1 before decision-close market entry could legally enter."
}
```
