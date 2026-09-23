# G12 Otx G6 Method Stats Audit

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `false`  
**Outcome review opened:** `false`

```json
{
  "artifact_family": "G12_OTX_G6_METHOD_STATS_AUDIT",
  "dsr_status": {
    "reason": "OTI4b is a tick-aware discovery quarantine, not validation; countable rows are below the 200 breakout-row floor.",
    "status": "NOT_COMPUTABLE_DISCOVERY_ONLY_AND_BELOW_SAMPLE_FLOOR"
  },
  "effective_n_status": {
    "raw_countable_n": 9,
    "sample_floor": 200,
    "session_concentration": {
      "london": 4,
      "ny": 3,
      "tokyo": 2
    },
    "status": "NOT_COMPUTABLE_BELOW_PREREG_SAMPLE_FLOOR",
    "symbol_concentration": {
      "GBPJPY": 3,
      "NAS100": 2,
      "US30_cash": 1,
      "XAGUSD": 3
    }
  },
  "generated_at_utc": "2026-05-07T08:33:45Z",
  "live_effect": false,
  "oti4b_countable_discovery_rows": 9,
  "oti4b_mean_synthetic_r_resolved_only": -0.5,
  "oti4b_resolved_synthetic_r_rows": 5,
  "oti4b_synthetic_r_values_resolved_only": [
    -1.0,
    1.5,
    -1.0,
    -1.0,
    -1.0
  ],
  "outcome_review_opened": false,
  "packet_063_stats_status": "NOT_RUN_INPUT_ONLY_FUTURE_QUARANTINE_SUBSET_ACCEPTED",
  "packet_066_stats_status": "NOT_RUN_INPUT_ONLY_FUTURE_QUARANTINE_SUBSET_ACCEPTED_SAMPLE_FLOOR_150_NOT_MET",
  "pbo_status": {
    "reason": "No variant selection or train/test matrix was run in this lane.",
    "status": "NOT_COMPUTABLE_NO_TRAIN_TEST_VARIANT_MATRIX"
  },
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "statistical_verdict": "NOT_VALIDATION_NOT_COMPUTABLE_BELOW_SAMPLE_FLOOR",
  "validation_safe": false
}
```
