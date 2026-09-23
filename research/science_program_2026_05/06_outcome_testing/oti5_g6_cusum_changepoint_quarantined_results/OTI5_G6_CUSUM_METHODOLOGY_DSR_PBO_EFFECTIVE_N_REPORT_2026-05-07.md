# OTI5 G6 CUSUM Methodology DSR/PBO/Effective-N Report

- Generated at UTC: `2026-05-07T09:16:17Z`
- Promotion verdict: `NO_PROMOTION_VERDICT`
- Validation safe: `false`
- Outcome review opened: `false`

```json
{
  "artifact_family": "OTI5_G6_CUSUM_METHODOLOGY_DSR_PBO_EFFECTIVE_N_REPORT",
  "countable_primary_unique_duplicate_groups": 17,
  "dsr": {
    "reason": "No valid train/test variant matrix and only 17 duplicate-primary groups versus the preregistered 300 synthetic-row production-relevance floor.",
    "status": "not_computable"
  },
  "effective_n": {
    "observed_duplicate_primary_groups": 17,
    "reason": "Duplicate-collapsed N is observable, but validation-style effective-N is not computable at this sample size and without an independent validation design.",
    "status": "not_computable_for_validation"
  },
  "generated_at_utc": "2026-05-07T09:16:17Z",
  "live_effect": false,
  "outcome_review_opened": false,
  "pbo": {
    "reason": "No cross-validated variant or train/test matrix exists; this lane reports one quarantined descriptive partition only.",
    "status": "not_computable"
  },
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "sample_floor_review": {
    "broker_actual_r_floor": 100,
    "broker_actual_r_opened": false,
    "current_countable_synthetic_groups": 17,
    "status": "BELOW_SAMPLE_FLOOR_DISCOVERY_ONLY",
    "synthetic_row_floor": 300
  },
  "statistical_verdict": "NOT_VALIDATION_NOT_COMPUTABLE_BELOW_SAMPLE_FLOOR",
  "validation_safe": false
}
```
