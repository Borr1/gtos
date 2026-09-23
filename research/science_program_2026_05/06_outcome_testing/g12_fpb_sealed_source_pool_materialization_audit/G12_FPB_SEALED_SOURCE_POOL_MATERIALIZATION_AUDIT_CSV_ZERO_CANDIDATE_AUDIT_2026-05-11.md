# CSV Zero Candidate Audit

- Route: `G12_FPB_SEALED_SOURCE_POOL_MATERIALIZATION_AUDIT`
- Artifact family: `csv_zero_candidate_audit`
- Evidence class: `G12_FPB_SEALED_SOURCE_POOL_SOURCE_CONTROL_AUDIT_ONLY`
- Promotion posture: `NO_PROMOTION_VERDICT`
- Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

```json
{
  "accepted_csv_candidate_count": 0,
  "artifact_family": "csv_zero_candidate_audit",
  "changes_live_trading_behavior": false,
  "checks": {
    "accepted_csv_candidates_empty": true,
    "accepted_csv_count_is_zero": true,
    "csv_rejections_are_explicit": true,
    "no_false_eurusd5_or_xauusd5_scid_m15_rows": true,
    "scid_named_csv_symbol_timeframe_inference_corrected": true
  },
  "credentials_touched": false,
  "duplicate_csv_count": 284,
  "evidence_class": "G12_FPB_SEALED_SOURCE_POOL_SOURCE_CONTROL_AUDIT_ONLY",
  "false_scid_m15_symbol_suffix_hits": [],
  "generated_at_utc": "2026-05-11T09:43:01Z",
  "live_effect": false,
  "opens_live_restart": false,
  "opens_live_trading_behavior": false,
  "opens_mt5_order_account_history_behavior": false,
  "opens_paid_api_or_databento_route": false,
  "opens_promotion": false,
  "opens_registry_edit": false,
  "opens_remote_push": false,
  "opens_result_scoring": false,
  "opens_validation": false,
  "outcome_review_opened": false,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "rejected_csv_count": 472,
  "rejected_reason_counts": {
    "REJECT_PURGE_EMBARGO_OR_MISSING_COVERAGE_FAIL_CLOSED": 8,
    "REJECT_SELECTED_SOURCE_HASH_DISCOVERY_EXPOSED": 365,
    "REJECT_UNSUPPORTED_SCHEMA_OR_TIMEFRAME_FOR_FPB_ENGINE": 99
  },
  "route_id": "G12_FPB_SEALED_SOURCE_POOL_MATERIALIZATION_AUDIT",
  "schema_version": "g12_fpb_sealed_source_pool_materialization_audit_v1",
  "scid_named_csv_inference_examples": [
    {
      "file": "EURUSD_SCID_M15.csv",
      "inferred_symbol": "EURUSD",
      "inferred_timeframe": "M15"
    },
    {
      "file": "XAUUSD_SCID_M15.csv",
      "inferred_symbol": "XAUUSD",
      "inferred_timeframe": "M15"
    },
    {
      "file": "EURUSD_SCID_M1.csv",
      "inferred_symbol": "EURUSD",
      "inferred_timeframe": "M1"
    }
  ],
  "validation_safe": false
}
```
