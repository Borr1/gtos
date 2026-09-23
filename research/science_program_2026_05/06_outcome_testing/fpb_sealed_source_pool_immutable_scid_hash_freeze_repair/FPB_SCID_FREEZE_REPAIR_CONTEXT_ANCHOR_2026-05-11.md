# Context Anchor

- Route: `FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR`
- Evidence class: `FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR_ONLY`
- Promotion verdict: `NO_PROMOTION_VERDICT`
- validation_safe: `False`
- outcome_review_opened: `False`
- live_effect: `False`

## Payload

```json
{
  "artifact_family": "context_anchor",
  "changes_live_trading_behavior": false,
  "chosen_policy": "BOUNDED_ELIGIBLE_SEGMENT",
  "controlling_prompt": "research/science_program_2026_05/04_goal_prompts/FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR_GOAL_PROMPT_2026-05-11.md",
  "credentials_touched": false,
  "current_head": "68304d63",
  "evidence_class": "FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR_ONLY",
  "forbidden_surfaces": [
    "validation_execution",
    "replay_or_path_label_generation",
    "result_scoring",
    "R_PnL_win_rate_expectancy_performance_claims",
    "promotion",
    "live_behavior",
    "AI_or_API_calls",
    "paid_or_vendor_access",
    "credentials",
    "remote_push",
    "broker_account_order_history_deal_position_data",
    "prompt_config_risk_safety_execution_canary_selector_changes"
  ],
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
  "policy_reason": "Full native Sierra files are append-mutable and large. The repair freezes the eligible segment as byte and record boundaries plus segment hashes, so later appends fall beyond the accepted byte range.",
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "repair_lane_boundary": "source-control repair only; no SCID-to-asof bar derivation or validation execution",
  "required_inputs": [
    "research/science_program_2026_05/06_outcome_testing/g12_fpb_sealed_source_pool_materialization_audit/G12_FPB_SEALED_SOURCE_POOL_MATERIALIZATION_AUDIT_REPAIR_BLOCKER_LEDGER_2026-05-11.json",
    "research/science_program_2026_05/06_outcome_testing/fpb_source_expansion_and_sealed_pool_materialization/FPB_SOURCE_EXPANSION_NATIVE_SCID_SEALED_POOL_CANDIDATE_LEDGER_2026-05-11.json",
    "research/science_program_2026_05/06_outcome_testing/fpb_source_expansion_and_sealed_pool_materialization/FPB_SOURCE_EXPANSION_SELECTED_SOURCE_COVERAGE_LEDGER_2026-05-11.json",
    "research/science_program_2026_05/06_outcome_testing/fpb_source_expansion_and_sealed_pool_materialization/FPB_SOURCE_EXPANSION_SOURCE_ASOF_NOLEAK_LEDGER_2026-05-11.json",
    "research/science_program_2026_05/06_outcome_testing/g0_fpb_sealed_partition_and_adversarial_baseline_packet/G0_FPB_SEALED_PARTITION_ADVERSARIAL_BASELINE_PACKET_2026-05-11.json",
    "research/science_program_2026_05/06_outcome_testing/g0_fpb_sealed_partition_and_adversarial_baseline_packet/G0_FPB_SEALED_PARTITION_PARTITION_LEDGER_2026-05-11.json",
    "research/science_program_2026_05/06_outcome_testing/g0_fpb_sealed_partition_and_adversarial_baseline_packet/G0_FPB_SEALED_PARTITION_DISCOVERY_EXPOSURE_LEDGER_2026-05-11.json",
    "research/science_program_2026_05/06_outcome_testing/g0_fpb_sealed_partition_and_adversarial_baseline_packet/G0_FPB_SEALED_PARTITION_SOURCE_ASOF_NOLEAK_CONTRACT_2026-05-11.json"
  ],
  "route_id": "FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR",
  "schema_version": "fpb_sealed_source_pool_immutable_scid_hash_freeze_repair_v1",
  "validation_safe": false
}
```
