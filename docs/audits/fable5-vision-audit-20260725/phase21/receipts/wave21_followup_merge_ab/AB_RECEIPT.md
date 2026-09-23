# Wave-21 follow-up merge A/B (origin/main 56d2e27d9 vs merged 8e7b98ee1)

**38 bad → 38 bad · 0 fixed · 0 regressed. No regressions.**

Compared by **failure set**, not by count — counts are not portable across worktrees.

| | before | after |
|---|---|---|
| commit | `56d2e27d9` | `8e7b98ee1` |
| captured (UTC) | 2026-08-10T21:10:56Z | 2026-08-10T21:40:40Z |
| working tree | clean | clean |
| failed | 38 | 38 |
| errored | 0 | 0 |
| **bad** | **38** | **38** |
| passed | 13786 | 13810 |
| skipped | 134 | 134 |

## Embedded captures

Embedded, not referenced. A receipt that points at a scratchpad path is as unverifiable as
no receipt at all, because that file is gone by the time anyone reads this.

```json
{
 "schema": "gtos-ab-receipt-v1",
 "scope": [
  "tests/"
 ],
 "before": {
  "commit": "56d2e27d986fb504db2a592d2f3461c4892d5835",
  "commit_subject": "April+May read REJECT: result + receipt (pooled -2.612R/67, April -7.742, May +5.130; discipline beats naive by +6.6R; family-specific liquidity_sweep_reclaim); CLAUDE.md plan note",
  "captured_utc": "2026-08-10T21:10:56Z",
  "dirty": false,
  "totals": {
   "failed": 38,
   "passed": 13786,
   "skipped": 134,
   "xfailed": 32
  }
 },
 "after": {
  "commit": "8e7b98ee1ac7a392ab739d667262cba15ba2f7d8",
  "commit_subject": "Merge wave21/post-integration-measurements: W7 post-integration receipt, verifier refusal-row repair, compose repair",
  "captured_utc": "2026-08-10T21:40:40Z",
  "dirty": false,
  "totals": {
   "failed": 38,
   "passed": 13810,
   "skipped": 134,
   "xfailed": 32
  }
 },
 "bad_before": 38,
 "bad_after": 38,
 "unchanged": 38,
 "fixed": [],
 "regressed": [],
 "bad_before_nodeids": [
  "tests/research_infra/test_cl_pass_surface_ceremony.py::test_real_package_is_hash_sealed_and_empty",
  "tests/research_infra/test_cn_live_cost_carry.py::test_carry_builder_reproduces_every_committed_payload_and_diff",
  "tests/research_infra/test_p1_offline_complete_path_runner.py::test_preexisting_output_parent_refuses_in_preflight",
  "tests/research_infra/test_session_fg_integration.py::test_session_fg_integrated_evidence_and_default_off_boundaries",
  "tests/scripts/test_ab_receipts_are_self_contained.py::test_every_ab_receipt_embeds_its_captures",
  "tests/test_armed_set_mc.py::test_a_named_set_equals_the_derived_variant_it_names",
  "tests/test_armed_set_mc.py::test_no_sleeve_set_leaves_the_published_grid_shape",
  "tests/test_b7_5_neutral_selection_factorial.py::test_compaction_retains_every_hard_eligible_option_when_probe_rows_drop",
  "tests/test_b7_5_neutral_selection_factorial.py::test_decision_window_and_canonical_identity_fail_closed",
  "tests/test_b7_5_neutral_selection_factorial.py::test_r0_selected_finalizer_probe_keeps_fixed_cash_binding",
  "tests/test_b7_5_neutral_selection_factorial.py::test_s0_and_s1_share_hard_pool_but_only_s0_bypasses_soft_quality",
  "tests/test_b7_5_neutral_selection_factorial.py::test_s0_neutral_rank_ignores_outcome_fields_and_input_order",
  "tests/test_b7_5_neutral_selection_factorial.py::test_s1_scheduler_counterfactual_carry_is_audit_only_and_parent_exact[R0-None]",
  "tests/test_b7_5_neutral_selection_factorial.py::test_s1_scheduler_counterfactual_carry_is_audit_only_and_parent_exact[R0-hard_scheduler_veto_present:cost_authority_missing]",
  "tests/test_b7_5_neutral_selection_factorial.py::test_s1_scheduler_counterfactual_carry_is_audit_only_and_parent_exact[R1-None]",
  "tests/test_b7_5_neutral_selection_factorial.py::test_s1_scheduler_counterfactual_carry_is_audit_only_and_parent_exact[R1-hard_scheduler_veto_present:cost_authority_missing]",
  "tests/test_b7_5_neutral_selection_factorial.py::test_unbound_finalizer_has_no_factorial_probe_shape_and_s1r1_only_adds_audit",
  "tests/test_b7_5_post_acceleration_contract.py::test_phase_c_hash_producer_binding_is_format_independent",
  "tests/test_b7_5_post_acceleration_contract_r2_verification_split.py::test_a_verifier_fix_breaks_r1_and_not_r2",
  "tests/test_b7_5_post_acceleration_contract_r2_verification_split.py::test_r1_binds_again_the_moment_the_sealed_bytes_are_restored",
  "tests/test_b7_5_post_acceleration_contract_r2_verification_split.py::test_r2_binds_through_the_real_enforcement_path[0]",
  "tests/test_b7_5_post_acceleration_contract_r2_verification_split.py::test_r2_binds_through_the_real_enforcement_path[1]",
  "tests/test_b7_5_post_acceleration_contract_r2_verification_split.py::test_r2_binds_through_the_real_enforcement_path[2]",
  "tests/test_b7_5_post_acceleration_contract_r2_verification_split.py::test_r2_binds_through_the_real_enforcement_path[3]",
  "tests/test_b7_5_post_acceleration_contract_r2_verification_split.py::test_r2_no_longer_rebuilds_and_the_break_is_exactly_the_authorized_one",
  "tests/test_broad_origin_emission_repairs.py::test_the_live_book_entrypoint_does_not_import_this_generator",
  "tests/test_mc_firm_rules.py::test_the_published_grid_reconstructs_and_the_two_survivor_sets_differ",
  "tests/test_mc_firm_rules.py::test_this_engine_reproduces_every_published_mc_field_exactly",
  "tests/test_opus5_architecture_audit_hardening.py::test_every_create_mt5_caller_uses_a_known_mode",
  "tests/test_permissions.py::test_scheduler_v4_terminal_gate_carries_ultimate_candidate_package_shadow_packet",
  "tests/test_replay_differential_harness.py::test_a_sealed_arm_compared_with_itself_is_equivalent",
  "tests/test_replay_differential_harness.py::test_the_cold_shard_roles_are_readable_on_a_sealed_arm",
  "tests/test_replay_differential_harness.py::test_two_different_sealed_arms_are_reported_as_differing",
  "tests/test_replay_policy_generation_lineage.py::test_deployed_lineage_claim_is_pinned_to_the_live_commit",
  "tests/test_w7_recost.py::test_commission_at_validation_stops_is_not_the_live_window_rate",
  "tests/test_w7_recost.py::test_night_ceilings_come_from_rollover_nights_not_a_weekday_fraction",
  "tests/test_w7_recost.py::test_only_a_structural_bound_promotes_a_sleeve_out_of_carry_conditional",
  "tests/ultimate_book/test_lane_weights.py::test_supervisor_binds_current_account_scopes_and_contracts_to_external_files"
 ],
 "bad_after_nodeids": [
  "tests/research_infra/test_cl_pass_surface_ceremony.py::test_real_package_is_hash_sealed_and_empty",
  "tests/research_infra/test_cn_live_cost_carry.py::test_carry_builder_reproduces_every_committed_payload_and_diff",
  "tests/research_infra/test_p1_offline_complete_path_runner.py::test_preexisting_output_parent_refuses_in_preflight",
  "tests/research_infra/test_session_fg_integration.py::test_session_fg_integrated_evidence_and_default_off_boundaries",
  "tests/scripts/test_ab_receipts_are_self_contained.py::test_every_ab_receipt_embeds_its_captures",
  "tests/test_armed_set_mc.py::test_a_named_set_equals_the_derived_variant_it_names",
  "tests/test_armed_set_mc.py::test_no_sleeve_set_leaves_the_published_grid_shape",
  "tests/test_b7_5_neutral_selection_factorial.py::test_compaction_retains_every_hard_eligible_option_when_probe_rows_drop",
  "tests/test_b7_5_neutral_selection_factorial.py::test_decision_window_and_canonical_identity_fail_closed",
  "tests/test_b7_5_neutral_selection_factorial.py::test_r0_selected_finalizer_probe_keeps_fixed_cash_binding",
  "tests/test_b7_5_neutral_selection_factorial.py::test_s0_and_s1_share_hard_pool_but_only_s0_bypasses_soft_quality",
  "tests/test_b7_5_neutral_selection_factorial.py::test_s0_neutral_rank_ignores_outcome_fields_and_input_order",
  "tests/test_b7_5_neutral_selection_factorial.py::test_s1_scheduler_counterfactual_carry_is_audit_only_and_parent_exact[R0-None]",
  "tests/test_b7_5_neutral_selection_factorial.py::test_s1_scheduler_counterfactual_carry_is_audit_only_and_parent_exact[R0-hard_scheduler_veto_present:cost_authority_missing]",
  "tests/test_b7_5_neutral_selection_factorial.py::test_s1_scheduler_counterfactual_carry_is_audit_only_and_parent_exact[R1-None]",
  "tests/test_b7_5_neutral_selection_factorial.py::test_s1_scheduler_counterfactual_carry_is_audit_only_and_parent_exact[R1-hard_scheduler_veto_present:cost_authority_missing]",
  "tests/test_b7_5_neutral_selection_factorial.py::test_unbound_finalizer_has_no_factorial_probe_shape_and_s1r1_only_adds_audit",
  "tests/test_b7_5_post_acceleration_contract.py::test_phase_c_hash_producer_binding_is_format_independent",
  "tests/test_b7_5_post_acceleration_contract_r2_verification_split.py::test_a_verifier_fix_breaks_r1_and_not_r2",
  "tests/test_b7_5_post_acceleration_contract_r2_verification_split.py::test_r1_binds_again_the_moment_the_sealed_bytes_are_restored",
  "tests/test_b7_5_post_acceleration_contract_r2_verification_split.py::test_r2_binds_through_the_real_enforcement_path[0]",
  "tests/test_b7_5_post_acceleration_contract_r2_verification_split.py::test_r2_binds_through_the_real_enforcement_path[1]",
  "tests/test_b7_5_post_acceleration_contract_r2_verification_split.py::test_r2_binds_through_the_real_enforcement_path[2]",
  "tests/test_b7_5_post_acceleration_contract_r2_verification_split.py::test_r2_binds_through_the_real_enforcement_path[3]",
  "tests/test_b7_5_post_acceleration_contract_r2_verification_split.py::test_r2_no_longer_rebuilds_and_the_break_is_exactly_the_authorized_one",
  "tests/test_broad_origin_emission_repairs.py::test_the_live_book_entrypoint_does_not_import_this_generator",
  "tests/test_mc_firm_rules.py::test_the_published_grid_reconstructs_and_the_two_survivor_sets_differ",
  "tests/test_mc_firm_rules.py::test_this_engine_reproduces_every_published_mc_field_exactly",
  "tests/test_opus5_architecture_audit_hardening.py::test_every_create_mt5_caller_uses_a_known_mode",
  "tests/test_permissions.py::test_scheduler_v4_terminal_gate_carries_ultimate_candidate_package_shadow_packet",
  "tests/test_replay_differential_harness.py::test_a_sealed_arm_compared_with_itself_is_equivalent",
  "tests/test_replay_differential_harness.py::test_the_cold_shard_roles_are_readable_on_a_sealed_arm",
  "tests/test_replay_differential_harness.py::test_two_different_sealed_arms_are_reported_as_differing",
  "tests/test_replay_policy_generation_lineage.py::test_deployed_lineage_claim_is_pinned_to_the_live_commit",
  "tests/test_w7_recost.py::test_commission_at_validation_stops_is_not_the_live_window_rate",
  "tests/test_w7_recost.py::test_night_ceilings_come_from_rollover_nights_not_a_weekday_fraction",
  "tests/test_w7_recost.py::test_only_a_structural_bound_promotes_a_sleeve_out_of_carry_conditional",
  "tests/ultimate_book/test_lane_weights.py::test_supervisor_binds_current_account_scopes_and_contracts_to_external_files"
 ]
}
```
