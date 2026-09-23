# OTI6 CNR Geometry And Eligibility Audit - 2026-05-07

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `false`  
**Outcome review opened:** `false`  
**Live effect:** `false`

```json
{
  "account_history_accessed": false,
  "api_calls": 0,
  "artifact_family": "OTI6_CNR_GEOMETRY_AND_ELIGIBILITY_AUDIT",
  "broker_actual_r_accessed": false,
  "canary_calls": 0,
  "candidate_geometry_source": {
    "line_no": 50,
    "row_key": "97a72dd896b0b4fb88a0b9aadb9295e6",
    "source_file": "shadow_logs/continuation_no_retrace_candidates.jsonl",
    "source_file_sha256": "30ae312b24db1a0808928d5c025aa0cb4c6fb626a239657e179512c45b2cdd76",
    "source_line_sha256": "27d379d158972f568f3c854aeaabae6604183f0283d988d11889380c140b3691"
  },
  "cnr_e0_geometry_rule": {
    "entry_model_id": "CNR_E0_DECISION_CLOSE_MARKET",
    "long_entry": "use executable decision ask",
    "score_only_after_geometry_valid": true,
    "short_entry": "use executable decision bid",
    "stop_model": "original_gtos_structural_stop_loss",
    "target_model": "original_gtos_take_profit_1"
  },
  "databento_calls": 0,
  "date_stamp": "2026-05-07",
  "decision_quote_reconstructed_from_parquet": {
    "ask": 4648.29,
    "bid": 4647.65,
    "decision_rows_lte_071500": 875,
    "executable_decision_price_long_ask": 4648.29,
    "quote_timestamp_utc": "2026-05-06T07:14:59.889000Z"
  },
  "distance_diagnostics": {
    "executable_entry_minus_original_entry_price": 86.77,
    "executable_entry_minus_original_entry_r": 6.12350035,
    "executable_entry_minus_tp1_price": 65.52,
    "executable_entry_minus_tp1_r": 4.62385321,
    "tp1_minus_original_entry_price": 21.25,
    "tp1_minus_original_entry_r": 1.49964714
  },
  "eligibility_status": {
    "eligible": false,
    "reason": "LONG executable ask is above original TP1 before CNR_E0 can enter.",
    "terminal_result_status": "RESULT_QUARANTINED_DISCOVERY_ONLY_CNR_E0_NOT_ELIGIBLE_TARGET_ALREADY_PASSED_AT_DECISION"
  },
  "experiment_id": "G6-EXP-002-CONTINUATION-NO-RETRACE",
  "generated_at_utc": "2026-05-07T10:23:43Z",
  "git_head_at_build": "e8747e13f16045154d81e60503d7a12835314452",
  "live_effect": false,
  "live_order_state_accessed": false,
  "mt5_order_calls": 0,
  "order_calls": 0,
  "original_gtos_geometry": {
    "base_r_price": 14.17,
    "entry_price": 4561.52,
    "geometry_valid": true,
    "side": "LONG",
    "stop_loss": 4547.35,
    "take_profit_1": 4582.77
  },
  "outcome_review_opened": false,
  "packet_id": "OTG0-PKT-061",
  "paid_data_calls": 0,
  "preregistered_original_geometry_valid": true,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "target_already_passed_at_decision": true,
  "target_record_id": "OTG0-PKT-061|XAUUSD_2026-05-06T07:15:00+00:00",
  "validation_safe": false
}
```
