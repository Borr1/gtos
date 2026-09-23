# OTI5 G6 CUSUM Method Freeze

- Generated at UTC: `2026-05-07T09:16:17Z`
- Promotion verdict: `NO_PROMOTION_VERDICT`
- Validation safe: `false`
- Outcome review opened: `false`

```json
{
  "artifact_family": "OTI5_G6_CUSUM_METHOD_FREEZE",
  "decision_time_feature_rule": {
    "feature_asof_required": "feature_asof_utc_lte_decision_asof_utc == true",
    "feature_status_required": "PREREGISTERED_TICK_CUSUM_FEATURE_READY",
    "model_id_required": "g6_tick_cusum_changepoint_v1",
    "threshold_freeze_id_required": "tick_m1_120bar_cusum_mad8_v1"
  },
  "duplicate_denominator_policy": "Sort by decision_asof_utc, then record_id; keep rank 1 as countable primary.",
  "experiment_id": "G6-EXP-004-EXHAUSTION-CHANGEPOINT",
  "generated_at_utc": "2026-05-07T09:16:17Z",
  "input_subset": {
    "excluded_record_ids": [
      "OTG0-PKT-063|NAS100_2026-05-03T16:15:00+00:00",
      "OTG0-PKT-063|XAUUSD_2026-05-03T16:15:00+00:00",
      "OTG0-PKT-063|XAUUSD_2026-05-03T16:30:00+00:00",
      "OTG0-PKT-063|XAUUSD_2026-05-06T07:15:00+00:00",
      "OTG0-PKT-063|XAUUSD_2026-05-06T08:00:00+00:00"
    ],
    "packet_id": "OTG0-PKT-063",
    "raw_rows": 86,
    "source_ready_rows": 81
  },
  "live_effect": false,
  "metric_freeze": {
    "continuation_failure_rate": "ENTRY_TOUCHED_THEN_SL / (ENTRY_TOUCHED_THEN_SL + ENTRY_TOUCHED_THEN_TP1) on duplicate-primary rows only",
    "descriptive_cusum_partition": "changepoint_count > 0 versus changepoint_count == 0; no threshold selected after outcomes",
    "expectancy_r": "mean synthetic_r over resolved TP/SL rows only; no-entry rows reported separately"
  },
  "outcome_review_opened": false,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "scoring_gate": "compute result only if subset/source/no-leak/duplicate/label checks pass",
  "synthetic_path_scoring_rule": {
    "long_entry": "ask <= entry_price",
    "long_sl": "bid <= stop_loss after entry",
    "long_tp": "bid >= take_profit_1 after entry",
    "same_tick_policy": "TP and SL on same tick is ambiguous; synthetic_r null",
    "short_entry": "bid >= entry_price",
    "short_sl": "ask >= stop_loss after entry",
    "short_tp": "ask <= take_profit_1 after entry"
  },
  "validation_safe": false
}
```
