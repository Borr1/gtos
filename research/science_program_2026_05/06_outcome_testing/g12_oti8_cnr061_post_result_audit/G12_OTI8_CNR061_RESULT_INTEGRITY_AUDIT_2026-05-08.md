# G12 OTI8 CNR061 Result Integrity Audit - 2026-05-08

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `false`  
**Outcome review opened:** `false`  
**Live effect:** `false`

- `integrity_status`: `PASS_TERMINAL_SCORING_INTERNALLY_CONSISTENT`
- `verdict`: `The two wins are real within OTI8's ordered tick path evidence, but they are tiny residual-TP1 wins; the six null rows are unresolved inside the frozen four-hour horizon, not hidden failures.`

```json
{
  "account_history_accessed": false,
  "api_calls": 0,
  "artifact_family": "G12_OTI8_CNR061_RESULT_INTEGRITY_AUDIT",
  "blocked_packet_outcome_source_read": false,
  "broker_actual_r_accessed": false,
  "canary_calls": 0,
  "countable_summary": {
    "mean_r_all_rows_null_as_zero": 0.0272391505,
    "mean_r_all_rows_null_excluded": 0.054478301,
    "no_terminal_count": 2,
    "null_unresolved_count": 2,
    "resolved_r_count": 2,
    "row_count": 4,
    "status_counts": {
      "NO_TERMINAL_WITHIN_ORDERED_HORIZON": 2,
      "TARGET_REACHED_BEFORE_STOP": 2
    },
    "stop_before_target_count": 0,
    "sum_r_resolved_only": 0.108956602,
    "target_before_stop_count": 2
  },
  "databento_calls": 0,
  "date_stamp": "2026-05-08",
  "generated_at_utc": "2026-05-08T05:43:40Z",
  "integrity_status": "PASS_TERMINAL_SCORING_INTERNALLY_CONSISTENT",
  "jsonl_vs_ledger_consistency": {
    "countable_duplicate_policy_summary_matches": true,
    "jsonl_row_hashes_match_ledger_rows": true,
    "row_level_all_eight_summary_matches": true
  },
  "live_effect": false,
  "live_order_state_accessed": false,
  "live_trade_results_accessed": false,
  "mt5_account_calls": 0,
  "mt5_order_calls": 0,
  "order_calls": 0,
  "outcome_review_opened": false,
  "packet_id": "OTG0-PKT-061",
  "paid_data_calls": 0,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "row_level_summary": {
    "mean_r_all_rows_null_as_zero": 0.0136195752,
    "mean_r_all_rows_null_excluded": 0.054478301,
    "no_terminal_count": 6,
    "null_unresolved_count": 6,
    "resolved_r_count": 2,
    "row_count": 8,
    "status_counts": {
      "NO_TERMINAL_WITHIN_ORDERED_HORIZON": 6,
      "TARGET_REACHED_BEFORE_STOP": 2
    },
    "stop_before_target_count": 0,
    "sum_r_resolved_only": 0.108956602,
    "target_before_stop_count": 2
  },
  "schema_version": "g12_oti8_cnr061_post_result_audit_v1",
  "terminal_target_rows": [
    {
      "record_id": "OTG0-PKT-061|XAGUSD_2026-05-04T07:15:00+00:00",
      "sidecar_row_sha256": "95480e429f7beb460e31f4c65c0351eef65e46db4dca6557e4bb2a1f7afc998a",
      "stop_gap_at_worst_price": 0.961,
      "stop_loss": 75.928,
      "stop_not_reached_before_target_proxy": true,
      "synthetic_r": 0.054478301,
      "target_condition_pass": true,
      "terminal_event_utc": "2026-05-04T07:24:03.832000Z",
      "terminal_price": 74.784,
      "terminal_price_side": "ask",
      "terminal_status": "TARGET_REACHED_BEFORE_STOP",
      "timing_model_family": "CNR_E0_DECISION_CLOSE_MARKET",
      "tiny_residual_r": true,
      "tp1": 74.786
    },
    {
      "record_id": "OTG0-PKT-061|XAGUSD_2026-05-04T07:15:00+00:00",
      "sidecar_row_sha256": "6b12bdca36eedc8c689617982be0f5fce05e5be3d16f84794c9ea30d87e36016",
      "stop_gap_at_worst_price": 0.961,
      "stop_loss": 75.928,
      "stop_not_reached_before_target_proxy": true,
      "synthetic_r": 0.054478301,
      "target_condition_pass": true,
      "terminal_event_utc": "2026-05-04T07:24:03.832000Z",
      "terminal_price": 74.784,
      "terminal_price_side": "ask",
      "terminal_status": "TARGET_REACHED_BEFORE_STOP",
      "timing_model_family": "CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE",
      "tiny_residual_r": true,
      "tp1": 74.786
    }
  ],
  "unresolved_no_terminal_rows": [
    {
      "max_adverse_r_within_horizon": 0.3058387396,
      "max_favorable_r_within_horizon": 0.1668211307,
      "record_id": "OTG0-PKT-061|XAGUSD_2026-05-05T16:30:00+00:00",
      "residual_target_r_from_executable_quote": 1.062094532,
      "sidecar_row_sha256": "4e76395873c48a3b9f20114c20d0247c92ef80846b170ee9b2f2d52919fa8d04",
      "stop_gap_at_worst_price": 0.749,
      "target_gap_at_best_price": 0.966,
      "terminal_event_utc": null,
      "terminal_status": "NO_TERMINAL_WITHIN_ORDERED_HORIZON",
      "timing_model_family": "CNR_E0_DECISION_CLOSE_MARKET",
      "unresolved_condition_pass": true
    },
    {
      "max_adverse_r_within_horizon": 0.3058387396,
      "max_favorable_r_within_horizon": 0.1668211307,
      "record_id": "OTG0-PKT-061|XAGUSD_2026-05-05T16:30:00+00:00",
      "residual_target_r_from_executable_quote": 1.062094532,
      "sidecar_row_sha256": "41da6796ddb651413f558333ae52db302fc76a2863f00c204bee6ef37d10a23e",
      "stop_gap_at_worst_price": 0.749,
      "target_gap_at_best_price": 0.966,
      "terminal_event_utc": null,
      "terminal_status": "NO_TERMINAL_WITHIN_ORDERED_HORIZON",
      "timing_model_family": "CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE",
      "unresolved_condition_pass": true
    },
    {
      "max_adverse_r_within_horizon": 0.21552436,
      "max_favorable_r_within_horizon": 0.2056151941,
      "record_id": "OTG0-PKT-061|XAGUSD_2026-05-05T16:45:00+00:00",
      "residual_target_r_from_executable_quote": 1.2518579686,
      "sidecar_row_sha256": "5a7146782dc6564ac7a04ba163bd3d262ab731c2e1c3b6706ea14aeed979c7bb",
      "stop_gap_at_worst_price": 0.95,
      "target_gap_at_best_price": 1.267,
      "terminal_event_utc": null,
      "terminal_status": "NO_TERMINAL_WITHIN_ORDERED_HORIZON",
      "timing_model_family": "CNR_E0_DECISION_CLOSE_MARKET",
      "unresolved_condition_pass": true
    },
    {
      "max_adverse_r_within_horizon": 0.21552436,
      "max_favorable_r_within_horizon": 0.2056151941,
      "record_id": "OTG0-PKT-061|XAGUSD_2026-05-05T16:45:00+00:00",
      "residual_target_r_from_executable_quote": 1.2518579686,
      "sidecar_row_sha256": "2d82227ec0dfd01b140471932701e4885dd065fca5c618d5dc2bf0e9c9da76ab",
      "stop_gap_at_worst_price": 0.95,
      "target_gap_at_best_price": 1.267,
      "terminal_event_utc": null,
      "terminal_status": "NO_TERMINAL_WITHIN_ORDERED_HORIZON",
      "timing_model_family": "CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE",
      "unresolved_condition_pass": true
    },
    {
      "max_adverse_r_within_horizon": 0.2677865613,
      "max_favorable_r_within_horizon": 0.2450592885,
      "record_id": "OTG0-PKT-061|XAGUSD_2026-05-05T17:00:00+00:00",
      "residual_target_r_from_executable_quote": 1.1798418972,
      "sidecar_row_sha256": "63d08012951489781b7f892fe2d22a968e88101ded2429354aac16e68d3d93c8",
      "stop_gap_at_worst_price": 0.741,
      "target_gap_at_best_price": 0.946,
      "terminal_event_utc": null,
      "terminal_status": "NO_TERMINAL_WITHIN_ORDERED_HORIZON",
      "timing_model_family": "CNR_E0_DECISION_CLOSE_MARKET",
      "unresolved_condition_pass": true
    },
    {
      "max_adverse_r_within_horizon": 0.2677865613,
      "max_favorable_r_within_horizon": 0.2450592885,
      "record_id": "OTG0-PKT-061|XAGUSD_2026-05-05T17:00:00+00:00",
      "residual_target_r_from_executable_quote": 1.1798418972,
      "sidecar_row_sha256": "5ee22ed74a3eb5c16b1f7857d29346b2713ddbdb8b9a61de9f57c8414889959c",
      "stop_gap_at_worst_price": 0.741,
      "target_gap_at_best_price": 0.946,
      "terminal_event_utc": null,
      "terminal_status": "NO_TERMINAL_WITHIN_ORDERED_HORIZON",
      "timing_model_family": "CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE",
      "unresolved_condition_pass": true
    }
  ],
  "validation_safe": false,
  "verdict": "The two wins are real within OTI8's ordered tick path evidence, but they are tiny residual-TP1 wins; the six null rows are unresolved inside the frozen four-hour horizon, not hidden failures."
}
```
