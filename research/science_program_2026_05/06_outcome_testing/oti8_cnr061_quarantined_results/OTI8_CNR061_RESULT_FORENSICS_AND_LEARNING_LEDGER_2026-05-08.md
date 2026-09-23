# OTI8 CNR061 Result Forensics And Learning Ledger - 2026-05-08

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `false`  
**Outcome review opened:** `false`  
**Live effect:** `false`

- The resolved May 4 rows had tiny residual target distance; the May 5 rows did not reach target or stop inside the fixed horizon.

```json
{
  "account_history_accessed": false,
  "api_calls": 0,
  "artifact_family": "OTI8_CNR061_RESULT_FORENSICS_AND_LEARNING_LEDGER",
  "blocked_packet_outcome_source_read": false,
  "broker_actual_r_accessed": false,
  "canary_calls": 0,
  "databento_calls": 0,
  "date_stamp": "2026-05-08",
  "failure_anatomy": {
    "target_reached_rows": [
      {
        "record_id": "OTG0-PKT-061|XAGUSD_2026-05-04T07:15:00+00:00",
        "residual_target_r": 0.054478301,
        "terminal_event_utc": "2026-05-04T07:24:03.832000Z",
        "timing_model_family": "CNR_E0_DECISION_CLOSE_MARKET"
      },
      {
        "record_id": "OTG0-PKT-061|XAGUSD_2026-05-04T07:15:00+00:00",
        "residual_target_r": 0.054478301,
        "terminal_event_utc": "2026-05-04T07:24:03.832000Z",
        "timing_model_family": "CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE"
      }
    ],
    "unresolved_rows": [
      {
        "max_adverse_r": 0.3058387396,
        "max_favorable_r": 0.1668211307,
        "record_id": "OTG0-PKT-061|XAGUSD_2026-05-05T16:30:00+00:00",
        "residual_target_r": 1.062094532,
        "target_gap_at_best_price": 0.966,
        "timing_model_family": "CNR_E0_DECISION_CLOSE_MARKET"
      },
      {
        "max_adverse_r": 0.3058387396,
        "max_favorable_r": 0.1668211307,
        "record_id": "OTG0-PKT-061|XAGUSD_2026-05-05T16:30:00+00:00",
        "residual_target_r": 1.062094532,
        "target_gap_at_best_price": 0.966,
        "timing_model_family": "CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE"
      },
      {
        "max_adverse_r": 0.21552436,
        "max_favorable_r": 0.2056151941,
        "record_id": "OTG0-PKT-061|XAGUSD_2026-05-05T16:45:00+00:00",
        "residual_target_r": 1.2518579686,
        "target_gap_at_best_price": 1.267,
        "timing_model_family": "CNR_E0_DECISION_CLOSE_MARKET"
      },
      {
        "max_adverse_r": 0.21552436,
        "max_favorable_r": 0.2056151941,
        "record_id": "OTG0-PKT-061|XAGUSD_2026-05-05T16:45:00+00:00",
        "residual_target_r": 1.2518579686,
        "target_gap_at_best_price": 1.267,
        "timing_model_family": "CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE"
      },
      {
        "max_adverse_r": 0.2677865613,
        "max_favorable_r": 0.2450592885,
        "record_id": "OTG0-PKT-061|XAGUSD_2026-05-05T17:00:00+00:00",
        "residual_target_r": 1.1798418972,
        "target_gap_at_best_price": 0.946,
        "timing_model_family": "CNR_E0_DECISION_CLOSE_MARKET"
      },
      {
        "max_adverse_r": 0.2677865613,
        "max_favorable_r": 0.2450592885,
        "record_id": "OTG0-PKT-061|XAGUSD_2026-05-05T17:00:00+00:00",
        "residual_target_r": 1.1798418972,
        "target_gap_at_best_price": 0.946,
        "timing_model_family": "CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE"
      }
    ]
  },
  "generated_at_utc": "2026-05-08T05:11:01Z",
  "learning_summary": [
    "The only resolved duplicate group was the May 4 London XAGUSD short, and it required only about 0.054R residual movement to original TP1.",
    "All six May 5 NY rows stayed inside the fixed four-hour path horizon: no target and no stop, with max favorable movement only about 0.17R to 0.25R against targets requiring about 1.06R to 1.25R.",
    "E0 and E1 are identical for the accepted rows because the source-hashed executable quote was the same for each paired timing family.",
    "The packet is dominated by duplicate concentration: eight row-level rows collapse to four countable timing-family rows and two duplicate groups."
  ],
  "live_effect": false,
  "live_order_state_accessed": false,
  "live_trade_results_accessed": false,
  "mt5_account_calls": 0,
  "mt5_order_calls": 0,
  "next_hypotheses": [
    "Register a CNR target family that is not mechanically tied to original TP1 after large favorable displacement.",
    "Capture pre-touch/latency timing fields prospectively so E0/E1/E2/E3/E4 can differ without post-hoc inference.",
    "Treat unresolved four-hour horizons as their own lifecycle label rather than imputing zero or a win/loss."
  ],
  "order_calls": 0,
  "outcome_review_opened": false,
  "packet_id": "OTG0-PKT-061",
  "paid_data_calls": 0,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "status": "NEGATIVE_OR_TINY_N_LEARNING_RECORDED_NO_RESCUE",
  "validation_safe": false
}
```
