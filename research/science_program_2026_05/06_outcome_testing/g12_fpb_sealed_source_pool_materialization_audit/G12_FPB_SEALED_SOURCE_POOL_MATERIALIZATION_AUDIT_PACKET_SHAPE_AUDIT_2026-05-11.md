# Packet Shape Audit

- Route: `G12_FPB_SEALED_SOURCE_POOL_MATERIALIZATION_AUDIT`
- Artifact family: `packet_shape_audit`
- Evidence class: `G12_FPB_SEALED_SOURCE_POOL_SOURCE_CONTROL_AUDIT_ONLY`
- Promotion posture: `NO_PROMOTION_VERDICT`
- Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

```json
{
  "artifact_family": "packet_shape_audit",
  "changes_live_trading_behavior": false,
  "completion_terminal_decision": "MATERIALIZED_NATIVE_SCID_SEALED_SOURCE_POOL_CANDIDATES_G12_AUDIT_REQUIRED",
  "credentials_touched": false,
  "csv_candidate_count": 0,
  "evidence_class": "G12_FPB_SEALED_SOURCE_POOL_SOURCE_CONTROL_AUDIT_ONLY",
  "generated_at_utc": "2026-05-11T09:43:01Z",
  "live_effect": false,
  "native_candidate_count": 9,
  "native_candidate_symbols": [
    "GBPUSD_6B",
    "EURUSD",
    "USDJPY_6J",
    "XAUUSD_GC",
    "XAUUSD_MGC",
    "US30_MYM",
    "NAS100_NQ",
    "XAGUSD_SI",
    "US30_YM"
  ],
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
  "route_id": "G12_FPB_SEALED_SOURCE_POOL_MATERIALIZATION_AUDIT",
  "schema_version": "g12_fpb_sealed_source_pool_materialization_audit_v1",
  "selected_source_count": 365,
  "shape_checks": {
    "csv_candidate_count_is_0": true,
    "native_candidate_count_is_9": true,
    "native_symbols_match_expected_order": true,
    "selected_source_count_is_365": true,
    "source_pool_audit_prompt_emitted": true,
    "validation_prompt_not_emitted": true
  },
  "validation_safe": false
}
```
