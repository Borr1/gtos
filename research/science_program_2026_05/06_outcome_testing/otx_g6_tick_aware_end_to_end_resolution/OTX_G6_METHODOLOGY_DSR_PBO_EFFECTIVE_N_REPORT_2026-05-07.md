# OTX G6 Methodology DSR PBO Effective N Report

- Generated at UTC: `2026-05-07T07:50:26Z`
- Promotion verdict: `NO_PROMOTION_VERDICT`
- Validation safe: `false`
- Outcome review opened: `false`

```json
{
  "artifact_family": "OTX_G6_METHODOLOGY_DSR_PBO_EFFECTIVE_N_REPORT",
  "dsr": {
    "reason": "OTI4b is a tick-aware discovery quarantine, not validation; countable rows are below the 200 breakout-row floor.",
    "status": "NOT_COMPUTABLE_DISCOVERY_ONLY_AND_BELOW_SAMPLE_FLOOR"
  },
  "effective_n": {
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
  "generated_at_utc": "2026-05-07T07:50:26Z",
  "oti4b_countable_discovery_rows": 9,
  "oti4b_mean_synthetic_r_resolved_only": -0.5,
  "oti4b_raw_rows": 86,
  "oti4b_resolved_synthetic_r_rows": 5,
  "outcome_review_opened": false,
  "pbo": {
    "reason": "No variant selection or train/test matrix was run in this lane.",
    "status": "NOT_COMPUTABLE_NO_TRAIN_TEST_VARIANT_MATRIX"
  },
  "promotion_language_allowed": false,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "result_status": "RESULT_QUARANTINED_DISCOVERY_ONLY",
  "validation_safe": false
}
```
