# OTI7 CNR Target-Already-Passed And Null Forensics - 2026-05-08

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `False`  
**Outcome review opened:** `False`  
**Live effect:** `False`

```json
{
  "account_history_accessed": false,
  "api_calls": 0,
  "artifact_family": "OTI7_CNR_ACCEPTED_QUARANTINED_RESULTS",
  "artifact_type": "target_already_passed_and_null_forensics",
  "blocked_packet_outcome_source_read": false,
  "broker_actual_r_accessed": false,
  "databento_calls": 0,
  "forensic_summary": [
    "No accepted row was target-already-passed under the recomputed side-aware executable quote gate.",
    "No accepted row ended as null-R after ordered tick scoring; terminal target/stop was found for every eligible geometry row.",
    "Eighteen rows were unscoreable because original stop geometry was invalid relative to the executable market quote.",
    "Eight OTG0-PKT-061 rows were unscoreable because the source packet has no entry/SL/TP geometry or path horizon."
  ],
  "generated_at_utc": "2026-05-08T01:56:25Z",
  "live_effect": false,
  "live_trade_results_accessed": false,
  "missing_geometry_count": 8,
  "mt5_order_calls": 0,
  "null_r_count": 0,
  "null_rows": [],
  "order_calls": 0,
  "outcome_review_opened": false,
  "paid_data_calls": 0,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "result_status": "RESULT_QUARANTINED_DISCOVERY_ONLY",
  "same_tick_ambiguity_count": 0,
  "stop_invalid_count": 18,
  "target_already_passed_count": 0,
  "target_already_passed_rows": [],
  "validation_safe": false
}
```
