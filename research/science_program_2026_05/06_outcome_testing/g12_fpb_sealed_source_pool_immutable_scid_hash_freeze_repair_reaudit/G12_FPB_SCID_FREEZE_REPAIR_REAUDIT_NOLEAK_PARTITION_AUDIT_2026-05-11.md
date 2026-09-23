# G12 FPB SCID Freeze Repair Reaudit No-Leak Partition Audit

- Route: `G12_FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR_REAUDIT`
- Evidence class: `G12_FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR_REAUDIT_ONLY`
- Promotion verdict: `NO_PROMOTION_VERDICT`
- validation_safe: `False`
- outcome_review_opened: `False`
- live_effect: `False`

## Summary

```json
{
  "summary": {
    "all_four_adversarial_baselines_exact": true,
    "g0_selected_source_count": 365,
    "safe_flags_closed": true,
    "selected_source_count_declared": 365
  }
}
```
## Payload

```json
{
  "artifact_family": "noleak_partition_audit",
  "baseline_controls_present": [
    "baseline_random_session_control",
    "baseline_shifted_entry_control",
    "baseline_momentum_continuation",
    "baseline_mean_reversion"
  ],
  "changes_live_trading_behavior": false,
  "checks": {
    "all_four_adversarial_baselines_exact": true,
    "duplicate_denominator_controls_source_control_only": true,
    "g0_discovery_exposure_preserves_365": true,
    "g0_source_asof_safe_flags_closed": true,
    "hard_floors_preserved": true,
    "no_broker_order_account_result_fields_read": true,
    "parser_asof_gate_explicit": true,
    "parser_rows_all_ok": true,
    "safe_flags_closed_on_target_packet": true,
    "scid_to_asof_gate_unopened": true,
    "segment_hashes_disjoint_from_selected_source_hashes": true,
    "selected_source_count_is_365": true,
    "target_duplicate_audit_preserves_365": true,
    "target_duplicate_overlap_empty": true,
    "validation_execution_gate_unopened": true
  },
  "credentials_touched": false,
  "denominator_control_decision": "SOURCE_CONTROL_ONLY_NO_VALIDATION_ROW_COUNTING_OR_OUTCOME_DENOMINATOR_OPENED",
  "duplicate_decision": "SEGMENT_HASHES_UNIQUE_DISJOINT_FROM_DISCOVERY_SELECTED_HASHES_AND_NOT_VALIDATION_DENOMINATOR_ROWS",
  "evidence_class": "G12_FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR_REAUDIT_ONLY",
  "g0_selected_source_count": 365,
  "g0_selected_source_hash_count": 365,
  "generated_at_utc": "2026-05-11T11:11:44Z",
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
  "remaining_gates_before_validation": [
    "SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AND_CANDIDATE_GENERATOR_CONSTRAINT",
    "separate validation-execution prompt after source-control contract acceptance",
    "future G12/G0 audit of any derived as-of packet before result scoring"
  ],
  "route_id": "G12_FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR_REAUDIT",
  "schema_version": "g12_fpb_scid_freeze_repair_reaudit_v1",
  "segment_hash_count": 9,
  "segment_selected_source_hash_overlap": [],
  "selected_source_count_declared": 365,
  "selected_source_coverage_row_count": 551,
  "selected_source_hash_count_from_source_expansion_rows": 350,
  "summary": {
    "all_four_adversarial_baselines_exact": true,
    "g0_selected_source_count": 365,
    "safe_flags_closed": true,
    "selected_source_count_declared": 365
  },
  "validation_safe": false
}
```
