# Instruction Coverage Checklist

Route: `G0_NOFILL_HISTORICAL_PARTITION_SOURCE_BINDING_SYNTHESIS_CONTROL_REVIEW`
Terminal decision: `ACCEPT_AS_G0_SOURCE_CONTROL_SYNTHESIS_FOR_NEXT_SEALED_SOURCE_EXPANSION`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Summary

```json
{
  "all_requirements_done": true,
  "artifact_family": "instruction_coverage_checklist",
  "changes_live_trading_behavior": false,
  "credentials_touched": false,
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
  "requirements": [
    {
      "evidence": "research\\science_program_2026_05\\06_outcome_testing\\g0_nofill_historical_partition_source_binding_synthesis_control_review\\G0_NOFILL_HIST_SYNTHESIS_CONTEXT_ANCHOR_2026-05-10.json",
      "prompt_requirement": "context anchor",
      "requirement_id": "context_anchor",
      "status": "DONE"
    },
    {
      "evidence": "research\\science_program_2026_05\\06_outcome_testing\\g0_nofill_historical_partition_source_binding_synthesis_control_review\\G0_NOFILL_HIST_SYNTHESIS_DECISION_LEDGER_2026-05-10.json",
      "prompt_requirement": "G0 decision ledger",
      "requirement_id": "decision_ledger",
      "status": "DONE"
    },
    {
      "evidence": "research\\science_program_2026_05\\06_outcome_testing\\g0_nofill_historical_partition_source_binding_synthesis_control_review\\G0_NOFILL_HIST_SYNTHESIS_ACCEPTED_G12_TARGET_ROUTE_SYNTHESIS_2026-05-10.json",
      "prompt_requirement": "accepted G12 and target-route synthesis",
      "requirement_id": "accepted_synthesis",
      "status": "DONE"
    },
    {
      "evidence": "research\\science_program_2026_05\\06_outcome_testing\\g0_nofill_historical_partition_source_binding_synthesis_control_review\\G0_NOFILL_HIST_SYNTHESIS_ZERO_SEALED_ROW_IMPLICATION_LEDGER_2026-05-10.json",
      "prompt_requirement": "zero-sealed-row implication ledger",
      "requirement_id": "zero_sealed",
      "status": "DONE"
    },
    {
      "evidence": "research\\science_program_2026_05\\06_outcome_testing\\g0_nofill_historical_partition_source_binding_synthesis_control_review\\G0_NOFILL_HIST_SYNTHESIS_CONTAMINATED_ROW_REUSE_CONSTRAINTS_2026-05-10.json",
      "prompt_requirement": "allowed contaminated-row reuse ledger",
      "requirement_id": "contaminated_reuse",
      "status": "DONE"
    },
    {
      "evidence": "research\\science_program_2026_05\\06_outcome_testing\\g0_nofill_historical_partition_source_binding_synthesis_control_review\\G0_NOFILL_HIST_SYNTHESIS_NEXT_SOURCE_EXPANSION_ROUTE_RANKING_2026-05-10.json",
      "prompt_requirement": "next source expansion route ranking",
      "requirement_id": "route_ranking",
      "status": "DONE"
    },
    {
      "evidence": "research\\science_program_2026_05\\06_outcome_testing\\g0_nofill_historical_partition_source_binding_synthesis_control_review\\G0_NOFILL_HIST_SYNTHESIS_EXACT_SOURCE_EXPANSION_REQUIREMENTS_MATRIX_2026-05-10.json",
      "prompt_requirement": "exact source expansion requirements matrix",
      "requirement_id": "requirements_matrix",
      "status": "DONE"
    },
    {
      "evidence": "research\\science_program_2026_05\\06_outcome_testing\\g0_nofill_historical_partition_source_binding_synthesis_control_review\\G0_NOFILL_HIST_SYNTHESIS_55_FIELD_EXPANSION_BINDING_CHECKLIST_2026-05-10.json",
      "prompt_requirement": "55-field expansion binding checklist",
      "requirement_id": "field_checklist",
      "status": "DONE"
    },
    {
      "evidence": "research\\science_program_2026_05\\06_outcome_testing\\g0_nofill_historical_partition_source_binding_synthesis_control_review\\G0_NOFILL_HIST_SYNTHESIS_NOLEAK_DUPLICATE_PURGE_EMBARGO_SOURCE_HASH_RULES_2026-05-10.json",
      "prompt_requirement": "no-leak/duplicate/purge/embargo/source-hash rules",
      "requirement_id": "noleak_rules",
      "status": "DONE"
    },
    {
      "evidence": "research\\science_program_2026_05\\06_outcome_testing\\g0_nofill_historical_partition_source_binding_synthesis_control_review\\G0_NOFILL_HIST_SYNTHESIS_LOCAL_HEAVY_PRIOR_ARTIFACT_SEARCH_PLAN_2026-05-10.json",
      "prompt_requirement": "local-heavy-data and prior-artifact source search plan",
      "requirement_id": "search_plan",
      "status": "DONE"
    },
    {
      "evidence": "research\\science_program_2026_05\\06_outcome_testing\\g0_nofill_historical_partition_source_binding_synthesis_control_review\\G0_NOFILL_HIST_SYNTHESIS_OWNER_ACCESS_SOURCE_CAPTURE_REQUIREMENTS_LEDGER_2026-05-10.json",
      "prompt_requirement": "owner/access/source/capture requirements ledger",
      "requirement_id": "owner_requirements",
      "status": "DONE"
    },
    {
      "evidence": "research\\science_program_2026_05\\06_outcome_testing\\g0_nofill_historical_partition_source_binding_synthesis_control_review\\G0_NOFILL_HIST_SYNTHESIS_BROAD_SCIENCE_HORIZON_SEPARATION_NOTE_2026-05-10.json",
      "prompt_requirement": "broader science horizon separation note",
      "requirement_id": "broad_horizon",
      "status": "DONE"
    },
    {
      "evidence": "research\\science_program_2026_05\\06_outcome_testing\\g0_nofill_historical_partition_source_binding_synthesis_control_review\\G0_NOFILL_HIST_SYNTHESIS_VALIDATION_EXECUTION_CLOSED_GATE_LEDGER_2026-05-10.json",
      "prompt_requirement": "validation-execution closed-gate ledger",
      "requirement_id": "closed_gates",
      "status": "DONE"
    },
    {
      "evidence": "research\\science_program_2026_05\\06_outcome_testing\\g0_nofill_historical_partition_source_binding_synthesis_control_review\\G0_NOFILL_HIST_SYNTHESIS_SATURATION_SELF_REDTEAM_PASS_2026-05-10.json",
      "prompt_requirement": "saturation/self-red-team pass",
      "requirement_id": "saturation",
      "status": "DONE"
    },
    {
      "evidence": "python_files_or_manifest",
      "prompt_requirement": "instruction-coverage checklist",
      "requirement_id": "instruction_coverage",
      "status": "DONE"
    },
    {
      "evidence": "python_files_or_manifest",
      "prompt_requirement": "next prompt pack with one-line starter",
      "requirement_id": "next_prompt_pack",
      "status": "DONE"
    },
    {
      "evidence": "python_files_or_manifest",
      "prompt_requirement": "completion audit",
      "requirement_id": "completion_audit",
      "status": "DONE"
    },
    {
      "evidence": "python_files_or_manifest",
      "prompt_requirement": "builder, verifier, and focused tests",
      "requirement_id": "builder_verifier_tests",
      "status": "DONE"
    }
  ],
  "validation_safe": false
}
```
