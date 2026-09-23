# OTI8 CNR061 Methodology DSR PBO Effective-N Report - 2026-05-08

**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Validation safe:** `false`  
**Outcome review opened:** `false`  
**Live effect:** `false`

```json
{
  "account_history_accessed": false,
  "api_calls": 0,
  "artifact_family": "OTI8_CNR061_METHODOLOGY_DSR_PBO_EFFECTIVE_N_REPORT",
  "blocked_packet_outcome_source_read": false,
  "broker_actual_r_accessed": false,
  "canary_calls": 0,
  "databento_calls": 0,
  "date_stamp": "2026-05-08",
  "dsr": {
    "reason": "Eight row-level discovery-only rows collapse to four countable timing-family rows and two duplicate groups; no validation vector or promotion test exists.",
    "status": "not_computable"
  },
  "effective_n": {
    "countable_rows": 4,
    "duplicate_groups": 2,
    "resolved_countable_rows": 2,
    "row_level_rows": 8,
    "status": "tiny_n_discovery_only_not_validation"
  },
  "generated_at_utc": "2026-05-08T05:11:01Z",
  "live_effect": false,
  "live_order_state_accessed": false,
  "live_trade_results_accessed": false,
  "mt5_account_calls": 0,
  "mt5_order_calls": 0,
  "order_calls": 0,
  "outcome_review_opened": false,
  "packet_id": "OTG0-PKT-061",
  "paid_data_calls": 0,
  "pbo": {
    "reason": "No model family selection or train/test split is being evaluated; this is one frozen quarantined packet.",
    "status": "not_computable"
  },
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "sample_floor": {
    "current_duplicate_groups": 2,
    "current_row_level_n": 8,
    "required_future_floor": "future CNR target/timing validation needs a separately preregistered sample floor; this packet cannot validate.",
    "sample_floor_pass": false
  },
  "statistical_verdict": "NOT_VALIDATION_NOT_PROMOTION_DSR_PBO_NOT_COMPUTABLE",
  "validation_safe": false
}
```
