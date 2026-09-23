# CNR061 Noleak Duplicate Audit - 2026-05-08

Promotion verdict: `NO_PROMOTION_VERDICT`
Validation safe: `false`
Outcome review opened: `false`
Live effect: `false`

- `forbidden_sidecar_key_status`: `PASS`
- `sidecar_row_count`: `8`
- `unique_duplicate_group_count`: `2`

```json
{
  "account_history_accessed": false,
  "api_calls": 0,
  "artifact_family": "CNR061_NOLEAK_DUPLICATE_AUDIT",
  "blocked_packet_outcome_source_read": false,
  "broker_actual_r_accessed": false,
  "databento_calls": 0,
  "duplicate_denominator_key_counts": {
    "OTG0-PKT-061|G6_CNR|XAGUSD|2026-05-04|london|SHORT|75.471|CNR_E0_DECISION_CLOSE_MARKET|CNR_T0_ORIGINAL_TP1": 1,
    "OTG0-PKT-061|G6_CNR|XAGUSD|2026-05-04|london|SHORT|75.471|CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE|CNR_T0_ORIGINAL_TP1": 1,
    "OTG0-PKT-061|G6_CNR|XAGUSD|2026-05-05|ny|SHORT|73.222|CNR_E0_DECISION_CLOSE_MARKET|CNR_T0_ORIGINAL_TP1": 3,
    "OTG0-PKT-061|G6_CNR|XAGUSD|2026-05-05|ny|SHORT|73.222|CNR_E1_CANDIDATE_CLOSE_EXECUTABLE_QUOTE|CNR_T0_ORIGINAL_TP1": 3
  },
  "duplicate_group_counts": {
    "G6_CNR|XAGUSD|2026-05-04|london|SHORT|75.471": 2,
    "G6_CNR|XAGUSD|2026-05-05|ny|SHORT|73.222": 6
  },
  "duplicate_policy": "Rows preserve timing-model denominator keys; duplicate_group_id exposes same-setup grouping for G12 denominator decisions. No outcome denominator is accepted here.",
  "forbidden_sidecar_key_hits": [],
  "forbidden_sidecar_key_status": "PASS",
  "generated_at_utc": "2026-05-08T04:11:39Z",
  "live_effect": false,
  "live_trade_results_accessed": false,
  "metadata_flag_status": {
    "live_effect": false,
    "outcome_review_opened": false,
    "promotion_verdict": "NO_PROMOTION_VERDICT",
    "validation_safe": false
  },
  "mt5_order_calls": 0,
  "order_calls": 0,
  "outcome_review_opened": false,
  "paid_data_calls": 0,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "schema_version": "cnr061_geometry_horizon_sidecar_v1",
  "sidecar_row_count": 8,
  "unique_duplicate_group_count": 2,
  "unique_sidecar_row_hashes": 8,
  "validation_safe": false
}
```
