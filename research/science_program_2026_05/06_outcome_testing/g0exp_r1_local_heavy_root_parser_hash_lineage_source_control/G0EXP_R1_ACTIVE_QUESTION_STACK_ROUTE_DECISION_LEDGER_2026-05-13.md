# G0EXP R1 Active Question Stack And Route Decision Ledger

- **route_id:** `G0EXP_R1_LOCAL_HEAVY_ROOT_PARSER_HASH_LINEAGE_SOURCE_CONTROL`
- **evidence_class:** `G0EXP_R1_LOCAL_HEAVY_ROOT_PARSER_HASH_LINEAGE_SOURCE_CONTROL_ONLY`
- **promotion_verdict:** `NO_PROMOTION_VERDICT`
- **validation_safe:** `false`
- **outcome_review_opened:** `false`
- **live_effect:** `false`

- Adjacent overflow families preserved: `6`.

```json
{
  "active_question_stack": [
    {
      "answer_status": "ANSWERED_BY_SOURCE_ROOT_LEDGER",
      "evidence": "research/science_program_2026_05/06_outcome_testing/g0exp_r1_local_heavy_root_parser_hash_lineage_source_control/G0EXP_R1_SOURCE_ROOT_SEARCH_HASH_DEFERRAL_LEDGER_2026-05-13.json",
      "question": "Which local-heavy roots exist, and which are metadata-only versus exact absent/access blockers?",
      "question_id": "R1-Q1"
    },
    {
      "answer_status": "ANSWERED_BY_PARSER_MATRIX",
      "evidence": "research/science_program_2026_05/06_outcome_testing/g0exp_r1_local_heavy_root_parser_hash_lineage_source_control/G0EXP_R1_PARSER_VERSION_SHAPE_FINGERPRINT_MATRIX_2026-05-13.json",
      "question": "Which parser/control files need version and shape fingerprints before denominator entry?",
      "question_id": "R1-Q2"
    },
    {
      "answer_status": "ANSWERED_FAIL_CLOSED",
      "evidence": "research/science_program_2026_05/06_outcome_testing/g0exp_r1_local_heavy_root_parser_hash_lineage_source_control/G0EXP_R1_BLOCKER_PURSUIT_LEDGER_2026-05-13.json",
      "question": "Can missing hashes become control/placebo strata without opening outcomes?",
      "question_id": "R1-Q3"
    },
    {
      "answer_status": "ANSWERED_NO_MUTATION",
      "evidence": "research/science_program_2026_05/06_outcome_testing/g0exp_r1_local_heavy_root_parser_hash_lineage_source_control/G0EXP_R1_DENOMINATOR_QUARANTINE_PROOF_2026-05-13.json",
      "question": "Does this route mutate the accepted-40 denominator or expansion quarantines?",
      "question_id": "R1-Q4"
    },
    {
      "answer_status": "ANSWERED_BY_OVERFLOW_ROWS",
      "evidence": "adjacent_rows in this ledger",
      "question": "What adjacent source/control families surfaced beyond the assigned floor?",
      "question_id": "R1-Q5"
    }
  ],
  "adjacent_overflow_decisions": [
    {
      "accepted_40_card_denominator_inclusion": false,
      "candidate_family": "Duplicate-Key Collision Placebo Route",
      "candidate_id": "OVF-ANTI-ADV-002",
      "decision": "KEPT_QUARANTINED_OVERFLOW_SUPPORT",
      "next_owner": "G0EXP_R2 and future G12 audit",
      "why": "Duplicate-key collisions require parser/schema/keyset hashes before any placebo/control result route."
    },
    {
      "accepted_40_card_denominator_inclusion": false,
      "candidate_family": "Duplicate Denominator Drift Route",
      "candidate_id": "OVF-ANTI-MISS-002",
      "decision": "ROUTED_TO_DENOMINATOR_MISSINGNESS_SOURCE_CONTROL",
      "next_owner": "G0EXP_R2_DENOMINATOR_ROWSET_PARTITION_MISSINGNESS_SOURCE_CONTROL",
      "why": "Duplicate denominator drift is a denominator-entry control, not a result family."
    },
    {
      "accepted_40_card_denominator_inclusion": false,
      "candidate_family": "Schema Parser Clock Failure Taxonomy Route",
      "candidate_id": "OVF-ANTI-FAIL-003",
      "decision": "KEPT_AS_R1_R5_OVERFLOW_CLOCK_PARSER_FAILURE_CONTROL",
      "next_owner": "G0EXP_R1 plus G0EXP_R5",
      "why": "Parser clock failures need parser fingerprinting now and clock/as-of contract later."
    },
    {
      "accepted_40_card_denominator_inclusion": false,
      "candidate_family": "EOL and text-normalized hash equivalence control",
      "candidate_id": "R1-OVF-EOL-HASH-001",
      "decision": "ADDED_AS_DISK_DISCOVERED_OVERFLOW_SUPPORT",
      "next_owner": "Future G12/G0 source-hash audit",
      "why": "Recent Ready-8 G0 hardening proved CRLF/LF hash sensitivity can become a real source-control issue."
    },
    {
      "accepted_40_card_denominator_inclusion": false,
      "candidate_family": "Git LFS pointer and no-raw-blob boundary control",
      "candidate_id": "R1-OVF-LFS-POINTER-001",
      "decision": "ADDED_AS_DISK_DISCOVERED_OVERFLOW_SUPPORT",
      "next_owner": "Future source-control audit",
      "why": "Repository uses narrow LFS patterns; future routes need explicit pointer/raw-blob treatment before denominator entry."
    },
    {
      "accepted_40_card_denominator_inclusion": false,
      "candidate_family": "Prior worktree source divergence and stale artifact control",
      "candidate_id": "R1-OVF-PRIOR-WORKTREE-001",
      "decision": "ADDED_AS_DISK_DISCOVERED_OVERFLOW_SUPPORT",
      "next_owner": "Future local-heavy source search lane",
      "why": "C:\\tmp contains multiple GTOS worktrees; they are leads, not canonical truth, until hashes and git lineage bind them."
    }
  ],
  "artifact_family": "active_question_stack_and_route_decision_ledger",
  "assigned_family_decisions": [
    {
      "accepted_40_card_denominator_inclusion": false,
      "candidate_family": "local_heavy_data_root_coverage_and_hash_deferral_controls",
      "candidate_id": "R4-EXP-ROOT-001",
      "decision": "MATERIALIZED_IN_R1_SOURCE_CONTROL_PACKAGE",
      "may_open_results_now": false
    },
    {
      "accepted_40_card_denominator_inclusion": false,
      "candidate_family": "parser_version_shape_fingerprint_and_schema_drift_controls",
      "candidate_id": "R4-EXP-PARSER-001",
      "decision": "MATERIALIZED_IN_R1_SOURCE_CONTROL_PACKAGE",
      "may_open_results_now": false
    },
    {
      "accepted_40_card_denominator_inclusion": false,
      "candidate_family": "hash_integrity_placebo_controls",
      "candidate_id": "EXP-ADV-001",
      "decision": "MATERIALIZED_IN_R1_SOURCE_CONTROL_PACKAGE",
      "may_open_results_now": false
    },
    {
      "accepted_40_card_denominator_inclusion": false,
      "candidate_family": "source_control_commit_route_and_artifact_lineage_controls",
      "candidate_id": "R4-EXP-CODEHIST-001",
      "decision": "MATERIALIZED_IN_R1_SOURCE_CONTROL_PACKAGE",
      "may_open_results_now": false
    }
  ],
  "changes_trading_risk_safety_prompt_decision_behavior": false,
  "credentials_touched": false,
  "evidence_class": "G0EXP_R1_LOCAL_HEAVY_ROOT_PARSER_HASH_LINEAGE_SOURCE_CONTROL_ONLY",
  "generated_at_utc": "2026-05-13T02:51:58Z",
  "head_at_build": "3ab07d464082",
  "live_effect": false,
  "opens_ai_api": false,
  "opens_broker_account_order_history_deal_position_evidence": false,
  "opens_live_restart": false,
  "opens_live_trading_behavior": false,
  "opens_paid_or_vendor_access": false,
  "opens_prompt_config_risk_safety_execution_canary_selector_edit": false,
  "opens_raw_market_data_blob_commit": false,
  "opens_registry_edit": false,
  "opens_remote_push": false,
  "opens_result_scoring": false,
  "opens_strategy_edge_claims": false,
  "opens_validation": false,
  "outcome_review_opened": false,
  "promotion_verdict": "NO_PROMOTION_VERDICT",
  "route_id": "G0EXP_R1_LOCAL_HEAVY_ROOT_PARSER_HASH_LINEAGE_SOURCE_CONTROL",
  "route_posture": "DISCOVERY_ENABLING_SOURCE_CONTROL_BUILDER_NOT_RESULT_OR_VALIDATION_LANE",
  "schema_version": "g0exp_r1_local_heavy_root_parser_hash_lineage_source_control_v1",
  "terminal_decision": "BUILT_G0EXP_R1_SOURCE_CONTROL_PACKAGE_G12_AUDIT_REQUIRED",
  "validation_safe": false
}
```
