# OTI7 CNR Negative Result Learning Ledger - 2026-05-08

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `False`  
**Outcome review opened:** `False`  
**Live effect:** `False`

```json
{
  "account_history_accessed": false,
  "api_calls": 0,
  "artifact_family": "OTI7_CNR_ACCEPTED_QUARANTINED_RESULTS",
  "artifact_type": "negative_result_learning_ledger",
  "blocked_packet_outcome_source_read": false,
  "broker_actual_r_accessed": false,
  "databento_calls": 0,
  "generated_at_utc": "2026-05-08T01:56:25Z",
  "headline": "CNR_T0 original TP1 with decision/candidate-close market entry is strongly negative in this accepted-row quarantine audit.",
  "learning_entries": [
    {
      "evidence": {
        "r_summary": {
          "mean_r": -0.829271,
          "median_r": -1.0,
          "scored_rows": 76,
          "stop_first": 64,
          "target_first": 12,
          "total_r": -63.024622
        },
        "scored_rows": 76,
        "stop_first_rows": 64,
        "target_first_rows": 12
      },
      "finding": "Most eligible rows stopped first.",
      "interpretation": "Late market-entry CNR over original TP1 does not rescue these rows as a broad T0 rule.",
      "next_hypothesis": "Future timing work needs a separate pre-bound trigger or target model; do not reuse this result as validation."
    },
    {
      "evidence": {
        "target_first_r_values": [
          0.054478,
          0.054478,
          0.054478,
          0.054478,
          0.108085,
          0.108085,
          0.054478,
          0.054478,
          0.108085,
          0.108085,
          0.108085,
          0.108085
        ]
      },
      "finding": "Target-first rows have small realized R from the executable quote.",
      "interpretation": "When entry is late but not target-already-passed, residual TP1 distance can be too small to offset stop distance.",
      "next_hypothesis": "A future fixed-R or structural target needs its own source-bound preregistration before any outcome opening."
    },
    {
      "evidence": {
        "stop_invalid_rows": 18
      },
      "finding": "Some source geometries are invalid at executable market entry.",
      "interpretation": "A market-entry timing family can make original pending-order stop geometry unusable.",
      "next_hypothesis": "Future packets should add an explicit market-entry geometry invalidity gate before scoring."
    },
    {
      "evidence": {
        "missing_geometry_rows": 8
      },
      "finding": "OTG0-PKT-061 remains non-scoreable from approved inputs.",
      "interpretation": "Continuation-no-retrace accepted rows need source-bound entry/SL/TP geometry and a path horizon before result scoring.",
      "next_hypothesis": "Build an input-only CNR packet variant with geometry and horizon fields frozen before outcome opening."
    }
  ],
  "live_effect": false,
  "live_trade_results_accessed": false,
  "mt5_order_calls": 0,
  "order_calls": 0,
  "outcome_review_opened": false,
  "paid_data_calls": 0,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "result_status": "RESULT_QUARANTINED_DISCOVERY_ONLY",
  "validation_safe": false
}
```
