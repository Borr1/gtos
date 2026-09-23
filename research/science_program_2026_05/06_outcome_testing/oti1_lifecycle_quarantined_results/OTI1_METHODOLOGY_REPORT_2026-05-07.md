# OTI1 Methodology Report - 2026-05-07

**Lane:** `OTI1`  
**Artifact type:** `methodology_report`  
**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Result status:** `RESULT_QUARANTINED_DISCOVERY_ONLY`

## Frozen Method

| Field | Value |
| --- | --- |
| Metric freeze | research/science_program_2026_05/06_outcome_testing/oti1_lifecycle_quarantined_results/OTI1_METRIC_FREEZE_2026-05-07.json |
| Metric | unique duplicate_group_id count by normalized lifecycle_state and fill_or_no_fill_state |
| Denominator | unique_duplicate_group_id_not_raw_rows |
| Label family | lifecycle_no_fill |
| Lifecycle labels inspected after freeze | True |
| Discovery quarantine only | True |

## Not-Computable Criteria

- `effective_n_below_sample_floor`
- `missing_lifecycle_rate_null_or_alternative`
- `duplicate_group_denominator_unproven`
- `duplicate_group_label_conflict`
- `covariate_source_asof_proof_absent`
- `no_validation_target_registered_for_quarantined_lane`
- `pbo_requires_registered_variants_or_folds`
- `dsr_requires_return_or_sharpe_series_not_lifecycle_labels`

## Controlling Inputs

- `.context/LIVE_STATE.md`
- `.context/02_session_handoffs/SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md`
- `.context/00_core/quick_reference_card.md`
- `.context/00_core/research_operating_doctrine.md`
- `.context/00_core/research_current_state.md`
- `.context/00_READING_ORDER.md`
- `research/science_program_2026_05/05_synthesis/SCIENCE_PROGRAM_MASTER_REGISTRY_2026-05-06.json`
- `research/science_program_2026_05/03_experiment_specs/EXPERIMENT_PREREGISTRY_2026-05-06.json`
- `research/science_program_2026_05/06_outcome_testing/OTG0_OUTCOME_TESTING_CONTROL_RULES_2026-05-07.md`
- `research/science_program_2026_05/06_outcome_testing/OTG0_FROZEN_COHORT_PACKET_MANIFEST_2026-05-07.json`
- `research/science_program_2026_05/06_outcome_testing/OTL1_LIFECYCLE_NO_FILL_PACKET_AUDIT_2026-05-07.md`
- `research/science_program_2026_05/06_outcome_testing/otb0_blocker_clearing_governor/OTB0_PACKET_BUILDER_REQUIREMENTS_2026-05-07.md`
- `research/science_program_2026_05/06_outcome_testing/otb0_blocker_clearing_governor/OTB0_COMPLETION_AUDIT_2026-05-07.md`
- `research/science_program_2026_05/06_outcome_testing/g12_blocker_clearing_audit/G12_BLOCKER_CLEARING_DECISION_LEDGER_2026-05-07.md`
- `research/science_program_2026_05/06_outcome_testing/g12_blocker_clearing_audit/G12_DUPLICATE_DENOMINATOR_REVIEW_2026-05-07.md`
- `research/science_program_2026_05/06_outcome_testing/g12_blocker_clearing_audit/G12_LABEL_FAMILY_REVIEW_2026-05-07.md`
- `research/science_program_2026_05/06_outcome_testing/g12_blocker_clearing_audit/G12_SOURCE_ASOF_SOURCE_HASH_REVIEW_2026-05-07.md`
- `research/science_program_2026_05/06_outcome_testing/otb1r_input_only_lifecycle_rebuild/OTB1R_INPUT_ONLY_LIFECYCLE_REBUILD_LEDGER_2026-05-07.md`
- `research/science_program_2026_05/06_outcome_testing/otb1r_input_only_lifecycle_rebuild/OTB1R_SCHEMA_NOLEAK_VALIDATION_REPORT_2026-05-07.md`
- `research/science_program_2026_05/06_outcome_testing/otb1r_input_only_lifecycle_rebuild/OTB1R_DUPLICATE_DENOMINATOR_REPORT_2026-05-07.md`
- `research/science_program_2026_05/06_outcome_testing/otb1r_input_only_lifecycle_rebuild/OTB1R_AMBIGUITY_LEDGER_2026-05-07.md`
- `research/science_program_2026_05/06_outcome_testing/otb1r_input_only_lifecycle_rebuild/source_projections/OTB1R_SANITIZED_LIFECYCLE_SOURCE_PROJECTIONS_2026-05-07.jsonl`
- `research/science_program_2026_05/06_outcome_testing/g12_otb_rebuild_reaudit/G12_OTB_REBUILD_REAUDIT_DECISION_LEDGER_2026-05-07.md`
- `research/science_program_2026_05/06_outcome_testing/g12_otb_rebuild_reaudit/G12_OTB_REBUILD_ACCEPTED_PACKET_SHORTLIST_2026-05-07.json`
- `research/science_program_2026_05/06_outcome_testing/g12_otb_rebuild_reaudit/G12_OTB_REBUILD_DUPLICATE_DENOMINATOR_REVIEW_2026-05-07.md`
- `research/science_program_2026_05/06_outcome_testing/g12_otb_rebuild_reaudit/G12_OTB_REBUILD_LABEL_FAMILY_REVIEW_2026-05-07.md`
- `research/science_program_2026_05/06_outcome_testing/g12_otb_rebuild_reaudit/G12_OTB_REBUILD_SOURCE_HASH_REVIEW_2026-05-07.md`
- `research/science_program_2026_05/06_outcome_testing/g12_otb_rebuild_reaudit/G12_OTB_REBUILD_BLOCKED_QUESTION_LEDGER_2026-05-07.md`
- `shadow_logs/pending_limit_lifecycle.jsonl`
- `shadow_logs/pending_limit_lifecycle_audit.jsonl`
- `shadow_logs/opportunity_lifecycle_audit.jsonl`
- `research/science_program_2026_05/06_outcome_testing/oti1_lifecycle_quarantined_results/OTI1_METRIC_FREEZE_2026-05-07.json`
- `research/science_program_2026_05/06_outcome_testing/g12_otb_rebuild_reaudit/G12_OTB_REBUILD_ACCEPTED_PACKET_SHORTLIST_2026-05-07.json`
- `research/science_program_2026_05/03_experiment_specs/EXPERIMENT_PREREGISTRY_2026-05-06.json`

## Source Evidence Exhausted

| Evidence | Value |
| --- | --- |
| Source projection file | research/science_program_2026_05/06_outcome_testing/otb1r_input_only_lifecycle_rebuild/source_projections/OTB1R_SANITIZED_LIFECYCLE_SOURCE_PROJECTIONS_2026-05-07.jsonl |
| Source projection rows | 8 |
| Source hash resolution issues | 0 |
| Lifecycle logs hashed | 3 |
