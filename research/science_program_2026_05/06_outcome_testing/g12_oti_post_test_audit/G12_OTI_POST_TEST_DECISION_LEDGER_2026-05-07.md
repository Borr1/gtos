# G12 OTI Post-Test Decision Ledger - 2026-05-07

**Promotion verdict:** `NO_PROMOTION_VERDICT`
**Validation safe:** `False`
**Outcome review opened:** `False`
**Generated:** `2026-05-07T01:17:05Z`

## Objective

Audit OTI1 lifecycle quarantined results and OTI2 risk-bank quarantined results against G12 accepted rebuilt packets, OTG0 controls, prior G12 audits, master registry constraints, research doctrine, and research_current_state. Decide each lane as accept, reject, or blocked without promoting or opening validation.

## Decisions

| Lane | Result lane | Decision | Packets | Reason | Next exact question |
| --- | --- | --- | --- | --- | --- |
| OTI1 | lifecycle_no_fill_existing_data_audit | ACCEPT_AS_QUARANTINED_DISCOVERY_EVIDENCE | ['OTG0-PKT-011', 'OTG0-PKT-016', 'OTG0-PKT-025', 'OTG0-PKT-029', 'OTG0-PKT-045', 'OTG0-PKT-055', 'OTG0-PKT-059', 'OTG0-PKT-071', 'OTG0-PKT-079'] | Metric was frozen, packet scope matches the 9 G12-accepted OTB1R lifecycle packets, blocked packet OTG0-PKT-017 is excluded, denominator/label/leakage audits are clean, and validation statistics are correctly marked not_computable. | Before any covariate-conditioned claim, which packet-bound source/as-of proofs clear the OTI1 covariate source-complete blockers while keeping lifecycle_no_fill separate from synthetic_path_r and broker_actual_r? |
| OTI2 | riskbank_synthetic_path_r_existing_data_audit | ACCEPT_AS_QUARANTINED_DISCOVERY_EVIDENCE | ['OTG0-PKT-013'] | Method was frozen before synthetic path label opening, packet scope is the single G12-accepted OTB2R risk-bank packet, source/hash/coverage and duplicate denominators pass, broker actual-R and blocked packets are not inspected, and the unscoreable risk-bank metric is correctly reported as not_computable rather than promoted. | Which future frozen input packet provides leg-level reentry state, risk_bank_before_action_r, risk_bank_after_action_r, realized_closed_leg_r, open_leg_stop_if_hit_r, and numeric estimated_remaining_cost_r for G10-EXP-RISKBANK-005 without broker actual-R or blocked-packet outcome pooling? |

## Evidence

### OTI1

- OTI1 metric froze before lifecycle label inspection and excluded OTG0-PKT-017. Evidence: `research/science_program_2026_05/06_outcome_testing/oti1_lifecycle_quarantined_results/OTI1_METRIC_FREEZE_2026-05-07.json` keys `frozen_before_lifecycle_label_inspection=true, allowed_packet_ids, excluded_packet_ids=['OTG0-PKT-017']`.
- OTI1 used only accepted OTB1R packets and did not inspect blocked/broker/synthetic results. Evidence: `research/science_program_2026_05/06_outcome_testing/oti1_lifecycle_quarantined_results/OTI1_RESULT_LEDGER_2026-05-07.json` keys `allowed_packet_count=9, blocked_packet_outcomes_inspected=false, broker_actual_r_values_inspected=false, synthetic_path_r_values_inspected=false`.
- OTI1 denominator and label-family audits have no concrete failure. Evidence: `research/science_program_2026_05/06_outcome_testing/oti1_lifecycle_quarantined_results/OTI1_DUPLICATE_DENOMINATOR_REPORT_2026-05-07.json` keys `denominator_mismatches=[], duplicate_group_label_conflicts=[]`.
- OTI1 label family is lifecycle_no_fill with forbidden fields absent. Evidence: `research/science_program_2026_05/06_outcome_testing/oti1_lifecycle_quarantined_results/OTI1_LABEL_FAMILY_SEPARATION_REPORT_2026-05-07.json` keys `primary_label_family=lifecycle_no_fill, forbidden_primary_field_hits=[], source_projection_forbidden_issue_count=0`.

### OTI2

- OTI2 method froze before synthetic path outcome inspection. Evidence: `research/science_program_2026_05/06_outcome_testing/oti2_riskbank_quarantined_results/OTI2_RISKBANK_METHOD_FREEZE_2026-05-07.json` keys `frozen_before_synthetic_path_outcome_inspection=true, allowed_packet_id=OTG0-PKT-013, label_family_boundary.primary_label_family=synthetic_path_r`.
- OTI2 result uses only OTG0-PKT-013 and avoids blocked/broker actual-R. Evidence: `research/science_program_2026_05/06_outcome_testing/oti2_riskbank_quarantined_results/OTI2_RISKBANK_RESULT_LEDGER_2026-05-07.json` keys `packet_id=OTG0-PKT-013, unique_duplicate_group_id_count=86, blocked_packet_outcomes_inspected=false, broker_actual_r_inspected=false`.
- OTI2 source hash and coverage pass for all 86 rows. Evidence: `research/science_program_2026_05/06_outcome_testing/oti2_riskbank_quarantined_results/OTI2_RISKBANK_SOURCE_HASH_COVERAGE_REPORT_2026-05-07.json` keys `packet_hash_match=true, row_source_hash_failure_count=0, coverage_failure_count=0`.
- OTI2 row ledger contains 86 quarantined synthetic path rows and no forbidden broker/live-result fields. Evidence: `research/science_program_2026_05/06_outcome_testing/oti2_riskbank_quarantined_results/OTI2_RISKBANK_RESULT_LEDGER_ROWS_2026-05-07.jsonl` keys `packet_id=OTG0-PKT-013, forbidden_field_hits=[]`.

## Controlling Inputs

- `research/science_program_2026_05/06_outcome_testing/g12_otb_rebuild_reaudit/G12_OTB_REBUILD_ACCEPTED_PACKET_SHORTLIST_2026-05-07.json`
- `research/science_program_2026_05/06_outcome_testing/g12_otb_rebuild_reaudit/G12_OTB_REBUILD_REAUDIT_DECISION_LEDGER_2026-05-07.json`
- `research/science_program_2026_05/06_outcome_testing/g12_otb_rebuild_reaudit/G12_OTB_REBUILD_LEAKAGE_REVIEW_2026-05-07.json`
- `research/science_program_2026_05/06_outcome_testing/g12_otb_rebuild_reaudit/G12_OTB_REBUILD_DUPLICATE_DENOMINATOR_REVIEW_2026-05-07.json`
- `research/science_program_2026_05/06_outcome_testing/g12_otb_rebuild_reaudit/G12_OTB_REBUILD_LABEL_FAMILY_REVIEW_2026-05-07.json`
- `research/science_program_2026_05/06_outcome_testing/g12_otb_rebuild_reaudit/G12_OTB_REBUILD_SOURCE_HASH_REVIEW_2026-05-07.json`
- `research/science_program_2026_05/06_outcome_testing/OTG0_OUTCOME_TESTING_CONTROL_RULES_2026-05-07.json`
- `research/science_program_2026_05/06_outcome_testing/OTG0_FROZEN_COHORT_PACKET_MANIFEST_2026-05-07.json`
- `research/science_program_2026_05/06_outcome_testing/OTG0_PREREG_CLASSIFICATION_LEDGER_2026-05-07.json`
- `research/science_program_2026_05/06_outcome_testing/OTL1_LIFECYCLE_NO_FILL_PACKET_AUDIT_2026-05-07.json`
- `research/science_program_2026_05/06_outcome_testing/otl2_synthetic_replay_packet_audit/OTL2_SYNTHETIC_REPLAY_PACKET_AUDIT_2026-05-07.json`
- `research/science_program_2026_05/06_outcome_testing/otb0_blocker_clearing_governor/OTB0_COMPLETION_AUDIT_2026-05-07.json`
- `research/science_program_2026_05/06_outcome_testing/otb1r_input_only_lifecycle_rebuild/OTB1R_SCHEMA_NOLEAK_VALIDATION_REPORT_2026-05-07.json`
- `research/science_program_2026_05/06_outcome_testing/otb1r_input_only_lifecycle_rebuild/OTB1R_DUPLICATE_DENOMINATOR_REPORT_2026-05-07.json`
- `research/science_program_2026_05/06_outcome_testing/otb2r_input_only_path_rebuild/OTB2R_SANITIZED_SOURCE_HASHES_2026-05-07.json`
- `research/science_program_2026_05/06_outcome_testing/otb2r_input_only_path_rebuild/OTB2R_FORBIDDEN_FIELD_SCAN_2026-05-07.json`
- `research/science_program_2026_05/06_outcome_testing/otb2r_input_only_path_rebuild/OTB2R_COVERAGE_AUDIT_2026-05-07.json`
- `research/science_program_2026_05/05_synthesis/SCIENCE_PROGRAM_MASTER_REGISTRY_2026-05-06.md`
- `.context/00_core/research_operating_doctrine.md`
- `.context/00_core/research_current_state.md`
