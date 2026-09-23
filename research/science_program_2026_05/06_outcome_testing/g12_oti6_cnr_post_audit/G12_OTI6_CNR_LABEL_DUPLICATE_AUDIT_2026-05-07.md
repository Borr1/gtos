# G12 OTI6 CNR Label Duplicate Audit - 2026-05-07

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `false`  
**Outcome review opened:** `false`  
**Live effect:** `false`

```json
{
  "accepted_packet_record_count": 1,
  "account_history_accessed": false,
  "api_calls": 0,
  "artifact_family": "G12_OTI6_CNR_LABEL_DUPLICATE_AUDIT",
  "audit_verdict": "PASS_DUPLICATE_DENOMINATOR_AND_LABEL_FAMILY_CONTROLS",
  "blocked_packet_outcome_source_read": false,
  "broker_actual_r_accessed": false,
  "canary_calls": 0,
  "databento_calls": 0,
  "date_stamp": "2026-05-07",
  "duplicate_group_id": "G6_CNR|XAUUSD|2026-05-06|london|LONG|4561.52",
  "duplicate_group_source": "G12_OTR061_PACKET_RECOVERY_AUDIT.prior_duplicate_group_id_for_future_denominator and candidate geometry",
  "duplicate_policy": "One primary countable opportunity; duplicate context rows are not summed as independent opportunities.",
  "generated_at_utc": "2026-05-07T10:47:40Z",
  "git_head_at_build": "16713c77 docs: refresh research state for g12 oti6 prompt",
  "label_boundary_verdict": "PASS_SYNTHETIC_PATH_R_NULL_NOT_POOLED_WITH_BROKER_OR_LIFECYCLE_LABELS",
  "label_family_separation": {
    "input_packet_label_family": "input_only_features_no_labels",
    "lifecycle_context_label_family": "lifecycle_no_fill_context_only",
    "result_label_family": "synthetic_path_r_quarantined_discovery_only_not_computed",
    "validation_label_family": null
  },
  "live_effect": false,
  "live_order_state_accessed": false,
  "live_trade_results_accessed": false,
  "mt5_order_calls": 0,
  "opportunity_counting_context": {
    "candidate_duplicate_counting_rule": "AGGREGATE_ONLY_COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY",
    "latest_resolution_rows_inspected": 7,
    "permitted_resolution_context": [
      {
        "asof_latest_candle_utc": "2026-05-06T09:15:00+00:00",
        "first_touch_times": {
          "entry_first_touch_utc": null,
          "sl_first_touch_utc": null,
          "tp1_first_touch_utc": "2026-05-06T07:15:00+00:00"
        },
        "later_path_outcome_status": "NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH",
        "line_no": 163,
        "row_key": "d9edec644a107c6424ed990a40904f08",
        "score_status": "PATH_CONTEXT_ONLY_NO_PROMOTION_GRADE_R",
        "synthetic_r_status": "NOT_COMPUTED_SOURCE_BLOCKED",
        "touched_original_limit_entry": false
      },
      {
        "asof_latest_candle_utc": "2026-05-06T09:30:00+00:00",
        "first_touch_times": {
          "entry_first_touch_utc": null,
          "sl_first_touch_utc": null,
          "tp1_first_touch_utc": "2026-05-06T07:15:00+00:00"
        },
        "later_path_outcome_status": "NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH",
        "line_no": 165,
        "row_key": "5887c1083f9f1fc569f699e3d26d42f5",
        "score_status": "PATH_CONTEXT_ONLY_NO_PROMOTION_GRADE_R",
        "synthetic_r_status": "NOT_COMPUTED_SOURCE_BLOCKED",
        "touched_original_limit_entry": false
      },
      {
        "asof_latest_candle_utc": "2026-05-06T10:30:00+00:00",
        "first_touch_times": {
          "entry_first_touch_utc": null,
          "sl_first_touch_utc": null,
          "tp1_first_touch_utc": "2026-05-06T07:15:00+00:00"
        },
        "later_path_outcome_status": "NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH",
        "line_no": 167,
        "row_key": "4b1ca70c464e491c03078a88ed316831",
        "score_status": "PATH_CONTEXT_ONLY_NO_PROMOTION_GRADE_R",
        "synthetic_r_status": "NOT_COMPUTED_SOURCE_BLOCKED",
        "touched_original_limit_entry": false
      },
      {
        "asof_latest_candle_utc": "2026-05-06T10:45:00+00:00",
        "first_touch_times": {
          "entry_first_touch_utc": null,
          "sl_first_touch_utc": null,
          "tp1_first_touch_utc": "2026-05-06T07:15:00+00:00"
        },
        "later_path_outcome_status": "NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH",
        "line_no": 169,
        "row_key": "e54d2f116f91182e584514dedf0a87d8",
        "score_status": "PATH_CONTEXT_ONLY_NO_PROMOTION_GRADE_R",
        "synthetic_r_status": "NOT_COMPUTED_SOURCE_BLOCKED",
        "touched_original_limit_entry": false
      },
      {
        "asof_latest_candle_utc": "2026-05-06T11:15:00+00:00",
        "first_touch_times": {
          "entry_first_touch_utc": null,
          "sl_first_touch_utc": null,
          "tp1_first_touch_utc": "2026-05-06T07:15:00+00:00"
        },
        "later_path_outcome_status": "NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH",
        "line_no": 171,
        "row_key": "b4523ff9c4d96a7c3c77f6ea11f38191",
        "score_status": "PATH_CONTEXT_ONLY_NO_PROMOTION_GRADE_R",
        "synthetic_r_status": "NOT_COMPUTED_SOURCE_BLOCKED",
        "touched_original_limit_entry": false
      },
      {
        "asof_latest_candle_utc": "2026-05-06T11:30:00+00:00",
        "first_touch_times": {
          "entry_first_touch_utc": null,
          "sl_first_touch_utc": null,
          "tp1_first_touch_utc": "2026-05-06T07:15:00+00:00"
        },
        "later_path_outcome_status": "NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH",
        "line_no": 173,
        "row_key": "8aa935a7ced5cb323b05756ef33118ca",
        "score_status": "PATH_CONTEXT_ONLY_NO_PROMOTION_GRADE_R",
        "synthetic_r_status": "NOT_COMPUTED_SOURCE_BLOCKED",
        "touched_original_limit_entry": false
      },
      {
        "asof_latest_candle_utc": "2026-05-06T16:15:00+00:00",
        "first_touch_times": {
          "entry_first_touch_utc": null,
          "sl_first_touch_utc": null,
          "tp1_first_touch_utc": "2026-05-06T07:15:00+00:00"
        },
        "later_path_outcome_status": "NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH",
        "line_no": 175,
        "row_key": "d0930547f715a7a0976580fe0c76f805",
        "score_status": "PATH_CONTEXT_ONLY_NO_PROMOTION_GRADE_R",
        "synthetic_r_status": "NOT_COMPUTED_SOURCE_BLOCKED",
        "touched_original_limit_entry": false
      }
    ]
  },
  "order_calls": 0,
  "outcome_review_opened": false,
  "packet_id": "OTG0-PKT-061",
  "paid_data_calls": 0,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "source_label_controls": {
    "input_packet_label_family": "input_only_features_no_labels",
    "lifecycle_context_label_family": "lifecycle_no_fill_context_only",
    "post_decision_context_not_used_for_cnr_e0_scoring": true,
    "result_label_family": "synthetic_path_r_quarantined_discovery_only_not_computed",
    "validation_label_family": null
  },
  "target_record_id": "OTG0-PKT-061|XAUUSD_2026-05-06T07:15:00+00:00",
  "validation_safe": false
}
```
