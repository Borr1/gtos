# G12 FPB SCID Freeze Repair Reaudit Output Manifest

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
    "artifact_count": 6,
    "terminal_decision": "ACCEPT_AS_SOURCE_CONTROL_IMMUTABLE_SCID_SEGMENT_REPAIR_EVIDENCE_ONLY"
  }
}
```
## Payload

```json
{
  "artifact_family": "output_manifest",
  "artifacts": {
    "blocker_ledger": {
      "json": "research/science_program_2026_05/06_outcome_testing/g12_fpb_sealed_source_pool_immutable_scid_hash_freeze_repair_reaudit/G12_FPB_SCID_FREEZE_REPAIR_REAUDIT_BLOCKER_LEDGER_2026-05-11.json",
      "md": "research/science_program_2026_05/06_outcome_testing/g12_fpb_sealed_source_pool_immutable_scid_hash_freeze_repair_reaudit/G12_FPB_SCID_FREEZE_REPAIR_REAUDIT_BLOCKER_LEDGER_2026-05-11.md"
    },
    "completion_audit": {
      "json": "research/science_program_2026_05/06_outcome_testing/g12_fpb_sealed_source_pool_immutable_scid_hash_freeze_repair_reaudit/G12_FPB_SCID_FREEZE_REPAIR_REAUDIT_COMPLETION_AUDIT_2026-05-11.json",
      "md": "research/science_program_2026_05/06_outcome_testing/g12_fpb_sealed_source_pool_immutable_scid_hash_freeze_repair_reaudit/G12_FPB_SCID_FREEZE_REPAIR_REAUDIT_COMPLETION_AUDIT_2026-05-11.md"
    },
    "decision_ledger": {
      "json": "research/science_program_2026_05/06_outcome_testing/g12_fpb_sealed_source_pool_immutable_scid_hash_freeze_repair_reaudit/G12_FPB_SCID_FREEZE_REPAIR_REAUDIT_DECISION_LEDGER_2026-05-11.json",
      "md": "research/science_program_2026_05/06_outcome_testing/g12_fpb_sealed_source_pool_immutable_scid_hash_freeze_repair_reaudit/G12_FPB_SCID_FREEZE_REPAIR_REAUDIT_DECISION_LEDGER_2026-05-11.md"
    },
    "dirty_path_audit": {
      "json": "research/science_program_2026_05/06_outcome_testing/g12_fpb_sealed_source_pool_immutable_scid_hash_freeze_repair_reaudit/G12_FPB_SCID_FREEZE_REPAIR_REAUDIT_DIRTY_PATH_AUDIT_2026-05-11.json",
      "md": "research/science_program_2026_05/06_outcome_testing/g12_fpb_sealed_source_pool_immutable_scid_hash_freeze_repair_reaudit/G12_FPB_SCID_FREEZE_REPAIR_REAUDIT_DIRTY_PATH_AUDIT_2026-05-11.md"
    },
    "noleak_partition_audit": {
      "json": "research/science_program_2026_05/06_outcome_testing/g12_fpb_sealed_source_pool_immutable_scid_hash_freeze_repair_reaudit/G12_FPB_SCID_FREEZE_REPAIR_REAUDIT_NOLEAK_PARTITION_AUDIT_2026-05-11.json",
      "md": "research/science_program_2026_05/06_outcome_testing/g12_fpb_sealed_source_pool_immutable_scid_hash_freeze_repair_reaudit/G12_FPB_SCID_FREEZE_REPAIR_REAUDIT_NOLEAK_PARTITION_AUDIT_2026-05-11.md"
    },
    "source_rehash_audit": {
      "json": "research/science_program_2026_05/06_outcome_testing/g12_fpb_sealed_source_pool_immutable_scid_hash_freeze_repair_reaudit/G12_FPB_SCID_FREEZE_REPAIR_REAUDIT_SOURCE_REHASH_AUDIT_2026-05-11.json",
      "md": "research/science_program_2026_05/06_outcome_testing/g12_fpb_sealed_source_pool_immutable_scid_hash_freeze_repair_reaudit/G12_FPB_SCID_FREEZE_REPAIR_REAUDIT_SOURCE_REHASH_AUDIT_2026-05-11.md"
    }
  },
  "builder": "research/science_program_2026_05/06_outcome_testing/g12_fpb_sealed_source_pool_immutable_scid_hash_freeze_repair_reaudit/build_g12_fpb_scid_freeze_repair_reaudit_2026_05_11.py",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
  "evidence_class": "G12_FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR_REAUDIT_ONLY",
  "focused_tests": "research/science_program_2026_05/06_outcome_testing/g12_fpb_sealed_source_pool_immutable_scid_hash_freeze_repair_reaudit/test_g12_fpb_scid_freeze_repair_reaudit_2026_05_11.py",
  "generated_at_utc": "2026-05-11T11:11:44Z",
  "live_effect": false,
  "next_prompt_record": {
    "artifact_family": "next_prompt_record",
    "changes_live_trading_behavior": false,
    "credentials_touched": false,
    "evidence_class": "G12_FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR_REAUDIT_ONLY",
    "generated_at_utc": "2026-05-11T11:11:44Z",
    "live_effect": false,
    "next_prompt_exists": true,
    "next_prompt_path": "research/science_program_2026_05/04_goal_prompts/SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AND_CANDIDATE_GENERATOR_CONSTRAINT_GOAL_PROMPT_2026-05-11.md",
    "next_prompt_required": true,
    "next_route_id": "SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AND_CANDIDATE_GENERATOR_CONSTRAINT",
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
    "route_id": "G12_FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR_REAUDIT",
    "schema_version": "g12_fpb_scid_freeze_repair_reaudit_v1",
    "summary": {
      "next_prompt_exists": true,
      "next_prompt_required": true
    },
    "validation_safe": false
  },
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
  "route_id": "G12_FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR_REAUDIT",
  "schema_version": "g12_fpb_scid_freeze_repair_reaudit_v1",
  "summary": {
    "artifact_count": 6,
    "terminal_decision": "ACCEPT_AS_SOURCE_CONTROL_IMMUTABLE_SCID_SEGMENT_REPAIR_EVIDENCE_ONLY"
  },
  "terminal_decision": "ACCEPT_AS_SOURCE_CONTROL_IMMUTABLE_SCID_SEGMENT_REPAIR_EVIDENCE_ONLY",
  "validation_safe": false,
  "verifier": "research/science_program_2026_05/06_outcome_testing/g12_fpb_sealed_source_pool_immutable_scid_hash_freeze_repair_reaudit/verify_g12_fpb_scid_freeze_repair_reaudit_2026_05_11.py"
}
```
