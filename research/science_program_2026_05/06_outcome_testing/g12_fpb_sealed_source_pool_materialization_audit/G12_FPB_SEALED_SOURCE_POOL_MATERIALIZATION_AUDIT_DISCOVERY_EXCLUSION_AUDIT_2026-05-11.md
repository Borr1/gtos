# Discovery Exclusion Audit

- Route: `G12_FPB_SEALED_SOURCE_POOL_MATERIALIZATION_AUDIT`
- Artifact family: `discovery_exclusion_audit`
- Evidence class: `G12_FPB_SEALED_SOURCE_POOL_SOURCE_CONTROL_AUDIT_ONLY`
- Promotion posture: `NO_PROMOTION_VERDICT`
- Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

```json
{
  "accepted_fpb_path_label_rows_excluded": 12852758,
  "artifact_family": "discovery_exclusion_audit",
  "candidate_hash_count": 9,
  "changes_live_trading_behavior": false,
  "checks": {
    "accepted_path_labels_forbidden": true,
    "all_365_selected_hashes_present": true,
    "all_selected_coverage_rows_excluded": true,
    "g0_partition_blocks_validation_execution": true,
    "g0_sealed_pool_was_zero_before_expansion": true,
    "selected_coverage_has_at_least_365_rows_for_365_hashes": true,
    "selected_hashes_disjoint_from_candidates": true
  },
  "credentials_touched": false,
  "evidence_class": "G12_FPB_SEALED_SOURCE_POOL_SOURCE_CONTROL_AUDIT_ONLY",
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
  "partition_status": "CURRENT_ACCEPTED_FPB_UNIVERSE_IS_DISCOVERY_EXPOSED_NO_VALIDATION_EXECUTION",
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "route_id": "G12_FPB_SEALED_SOURCE_POOL_MATERIALIZATION_AUDIT",
  "schema_version": "g12_fpb_sealed_source_pool_materialization_audit_v1",
  "sealed_historical_validation_source_rows_before_source_expansion": 0,
  "selected_candidate_hash_overlap": [],
  "selected_hash_count": 365,
  "selected_source_coverage_rows": 551,
  "selected_source_rows_in_source_selection": 365,
  "validation_safe": false
}
```
