# Duplicate Discovery Exclusion Audit

- Route: `FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR`
- Evidence class: `FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR_ONLY`
- Promotion verdict: `NO_PROMOTION_VERDICT`
- validation_safe: `False`
- outcome_review_opened: `False`
- live_effect: `False`

## Summary

```json
{
  "all_four_baselines_preserved": true,
  "duplicate_decision": "ALL_SEGMENT_HASHES_UNIQUE_AND_DISJOINT_FROM_365_DISCOVERY_SELECTED_SOURCE_HASHES",
  "selected_source_rows_preserved": 365
}
```
## Payload

```json
{
  "accepted_fpb_path_label_rows_remain_excluded": 12852758,
  "all_four_baselines_preserved": true,
  "artifact_family": "duplicate_discovery_exclusion_audit",
  "baseline_controls_present": [
    "baseline_random_session_control",
    "baseline_shifted_entry_control",
    "baseline_momentum_continuation",
    "baseline_mean_reversion"
  ],
  "changes_live_trading_behavior": false,
  "checks": {
    "all_four_baselines_preserved": true,
    "g0_selected_source_count_is_365": true,
    "no_duplicate_segment_hashes": true,
    "no_selected_segment_hash_overlap": true,
    "partition_assignment_preserved": true,
    "selected_source_count_is_365": true
  },
  "credentials_touched": false,
  "duplicate_decision": "ALL_SEGMENT_HASHES_UNIQUE_AND_DISJOINT_FROM_365_DISCOVERY_SELECTED_SOURCE_HASHES",
  "duplicate_segment_hashes": [],
  "evidence_class": "FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR_ONLY",
  "expected_baselines": [
    "baseline_random_session_control",
    "baseline_shifted_entry_control",
    "baseline_momentum_continuation",
    "baseline_mean_reversion"
  ],
  "g0_selected_source_count": 365,
  "g0_selected_source_hash_count": 365,
  "generated_at_utc": "2026-05-11T10:22:32Z",
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
  "partition_assignment_preserved": true,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "repair_partition_assignment": "SEALED_HISTORICAL_SOURCE_POOL_CANDIDATE_G12_REAUDIT_REQUIRED",
  "route_id": "FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR",
  "schema_version": "fpb_sealed_source_pool_immutable_scid_hash_freeze_repair_v1",
  "selected_segment_hash_overlap": [],
  "selected_source_coverage_row_count": 551,
  "selected_source_hash_count": 350,
  "selected_source_rows_preserved": 365,
  "summary": {
    "all_four_baselines_preserved": true,
    "duplicate_decision": "ALL_SEGMENT_HASHES_UNIQUE_AND_DISJOINT_FROM_365_DISCOVERY_SELECTED_SOURCE_HASHES",
    "selected_source_rows_preserved": 365
  },
  "validation_safe": false
}
```
