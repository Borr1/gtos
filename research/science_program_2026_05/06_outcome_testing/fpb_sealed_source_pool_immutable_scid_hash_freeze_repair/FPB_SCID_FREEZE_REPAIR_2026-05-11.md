# FPB Immutable SCID Hash Freeze Repair Packet

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
  "repaired_source_count": 9,
  "selected_source_rows_preserved": 365,
  "terminal_decision": "REPAIRED_ALL_9_SCID_SOURCES_G12_REAUDIT_REQUIRED"
}
```
## Payload

```json
{
  "all_four_baselines_preserved": true,
  "all_hard_floors_preserved": true,
  "artifact_family": "repair_packet",
  "baseline_controls": [
    "baseline_random_session_control",
    "baseline_shifted_entry_control",
    "baseline_momentum_continuation",
    "baseline_mean_reversion"
  ],
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "evidence_class": "FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR_ONLY",
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
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "remaining_non_repair_gates_before_validation": [
    "G12 repair reaudit acceptance",
    "SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AND_CANDIDATE_GENERATOR_CONSTRAINT",
    "separate validation-execution prompt after source-control contract acceptance"
  ],
  "repaired_source_count": 9,
  "route_id": "FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR",
  "schema_version": "fpb_sealed_source_pool_immutable_scid_hash_freeze_repair_v1",
  "scid_to_asof_bar_derivation_contract_gate": "SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AND_CANDIDATE_GENERATOR_CONSTRAINT_REQUIRED_BEFORE_ANY_REPLAY_OR_CANDIDATE_GENERATION",
  "selected_source_rows_preserved": 365,
  "separate_validation_execution_prompt_gate": "REQUIRED_AFTER_SOURCE_CONTROL_CONTRACT_ACCEPTANCE",
  "source_access_blocker_count": 0,
  "source_pool_status_after_repair": "G12_REAUDIT_REQUIRED",
  "summary": {
    "all_four_baselines_preserved": true,
    "repaired_source_count": 9,
    "selected_source_rows_preserved": 365,
    "terminal_decision": "REPAIRED_ALL_9_SCID_SOURCES_G12_REAUDIT_REQUIRED"
  },
  "terminal_decision": "REPAIRED_ALL_9_SCID_SOURCES_G12_REAUDIT_REQUIRED",
  "validation_execution_prompt_emitted": false,
  "validation_safe": false
}
```
