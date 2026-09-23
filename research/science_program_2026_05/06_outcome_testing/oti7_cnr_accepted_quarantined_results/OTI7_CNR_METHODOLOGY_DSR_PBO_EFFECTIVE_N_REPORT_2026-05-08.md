# OTI7 CNR Methodology DSR PBO Effective-N Report - 2026-05-08

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `False`  
**Outcome review opened:** `False`  
**Live effect:** `False`

```json
{
  "account_history_accessed": false,
  "api_calls": 0,
  "artifact_family": "OTI7_CNR_ACCEPTED_QUARANTINED_RESULTS",
  "artifact_type": "methodology_dsr_pbo_effective_n_report",
  "blocked_packet_outcome_source_read": false,
  "broker_actual_r_accessed": false,
  "databento_calls": 0,
  "descriptive_result_only": true,
  "dsr": {
    "reasons": [
      "NO_PROMOTION_VERDICT",
      "validation_safe=false",
      "quarantined discovery result only",
      "no independent validation split",
      "no approved trial-count/return-series dossier for CNR timing family promotion"
    ],
    "status": "not_computable"
  },
  "effective_n": {
    "accepted_rows": 102,
    "countable_rows": 54,
    "ready_countable_unique_primary_duplicate_groups": 27,
    "ready_unique_primary_duplicate_groups": 30,
    "scored_countable_rows": 44,
    "scored_countable_unique_primary_duplicate_groups": 22,
    "scored_rows": 76,
    "status": "descriptive_only_not_validation"
  },
  "generated_at_utc": "2026-05-08T01:56:25Z",
  "live_effect": false,
  "live_trade_results_accessed": false,
  "mt5_order_calls": 0,
  "order_calls": 0,
  "outcome_review_opened": false,
  "paid_data_calls": 0,
  "pbo": {
    "reasons": [
      "no train/test or CPCV blocks",
      "no variant matrix",
      "E0 and E1 share packet as-of quotes in accepted rows",
      "blocked rows remain excluded and cannot be used for expansion"
    ],
    "status": "not_computable"
  },
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "raw_p": {
    "reason": "quarantined discovery lane, same accepted packet family, no validation dossier, and no preregistered null distribution for CNR_E0/E1 T0 market-entry tick scoring",
    "status": "not_computed_for_promotion"
  },
  "raw_result_summary_all_rows": {
    "mean_r": -0.829271,
    "median_r": -1.0,
    "scored_rows": 76,
    "stop_first": 64,
    "target_first": 12,
    "total_r": -63.024622
  },
  "raw_result_summary_countable_rows": {
    "mean_r": -0.755473,
    "median_r": -1.0,
    "scored_rows": 44,
    "stop_first": 34,
    "target_first": 10,
    "total_r": -33.240792
  },
  "result_status": "RESULT_QUARANTINED_DISCOVERY_ONLY",
  "validation_safe": false
}
```
