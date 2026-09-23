# OTI6 CNR Method Freeze - 2026-05-07

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `false`  
**Outcome review opened:** `false`  
**Live effect:** `false`

```json
{
  "account_history_accessed": false,
  "api_calls": 0,
  "artifact_family": "OTI6_CNR_METHOD_FREEZE",
  "broker_actual_r_accessed": false,
  "canary_calls": 0,
  "cohort": {
    "packet_id": "OTG0-PKT-061",
    "record_count": 1,
    "record_id": "OTG0-PKT-061|XAUUSD_2026-05-06T07:15:00+00:00"
  },
  "databento_calls": 0,
  "date_stamp": "2026-05-07",
  "entry_model": {
    "entry_model_id": "CNR_E0_DECISION_CLOSE_MARKET",
    "executable_price_rule": "LONG uses ask at decision quote; SHORT uses bid at decision quote.",
    "quote_timestamp_rule": "last source-hashed tick at or before decision_asof_utc"
  },
  "experiment_id": "G6-EXP-002-CONTINUATION-NO-RETRACE",
  "generated_at_utc": "2026-05-07T10:23:43Z",
  "geometry_gate_before_r_scoring": {
    "long_valid_ordering": "stop_loss < executable_entry < original_take_profit_1",
    "short_valid_ordering": "original_take_profit_1 < executable_entry < stop_loss",
    "target_already_passed_policy": "If executable entry is already beyond original TP1, do not score as positive R."
  },
  "git_head_at_build": "e8747e13f16045154d81e60503d7a12835314452",
  "live_effect": false,
  "live_order_state_accessed": false,
  "metric_freeze": {
    "primary_status": "RESULT_QUARANTINED_DISCOVERY_ONLY_CNR_E0_NOT_ELIGIBLE_TARGET_ALREADY_PASSED_AT_DECISION",
    "r_metric": "quarantined synthetic path-R only if geometry is valid and ordered path reaches TP1/SL unambiguously",
    "this_record_r_metric_status": "NOT_COMPUTED_PREREGISTERED_GEOMETRY_NOT_ELIGIBLE"
  },
  "mt5_order_calls": 0,
  "order_calls": 0,
  "outcome_review_opened": false,
  "packet_id": "OTG0-PKT-061",
  "paid_data_calls": 0,
  "preregistration_sources": [
    "research/program_control/CONTINUATION_NO_RETRACE_PREREGISTRATION_2026-05-06.md",
    "research/science_program_2026_05/01_domain_syntheses/G6_MOMENTUM_REVERSION_ROWS_2026-05-06.json"
  ],
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "target_record_id": "OTG0-PKT-061|XAUUSD_2026-05-06T07:15:00+00:00",
  "validation_safe": false
}
```
