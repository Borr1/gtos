# Wave-7 train A/B — merged main vs Session AT's after-capture

**Verdict: 0 REGRESSED.** No test that passed at AT's after-commit fails on merged main.

The composition moved for exactly one non-code reason — hydration — and both directions are
explained by it:

- **Fixed: 4.** Collection errors behind committed-but-sparse-excluded inputs
  (AT's HYDRATE disposition); `scripts/gtos_hydrate_test_data.py` (built at this merge) hydrates
  them in any worktree, so they now collect and pass.
- **`regressed` in the embedded block lists 18 ids because the schema defines it as the raw
  set difference — read this before treating them as damage.** All 18 were SKIPPED at the before-capture (the
  conftest hook skips only while a named input is absent). Hydration supplied those named inputs,
  the tests now RUN, and they fail one layer deeper: on machine-local campaign evidence
  (`.hermes/`-class replay-acceleration verification state) that is deliberately not in git.
  Same class as the 25 red lines AT's own receipt documents; skipped→failing is not
  passing→failing.
- The un-hydrated intermediate capture (82 bad, +15 in `test_vnext_production_wiring.py` alone)
  measured the worktree, not the code — it is superseded by this hydrated capture and kept only
  in the session scratchpad.

**This after-capture is committed as `FAILSET_BASELINE_MAIN.json` — the committed baseline.**
Diff against it with `python3 scripts/pytest_failset.py diff baseline <after.json>`; never
re-capture the before side. Full captures remain the orchestrator's, once per merge train, in a
hydrated worktree (`python3 scripts/gtos_hydrate_test_data.py` first).

Train merged: AT `b34c796e7`, AD `6e07cd94c`, AF `98413c6f7`, AE `6f78f108d`.

## Embedded captures

```json
{
 "schema": "gtos-ab-receipt-v1",
 "scope": [
  "tests/"
 ],
 "before": {
  "commit": "bbc6baccc60627bb1c1dbd90480b102726d55a04",
  "commit_subject": "Wave 6: retire the 504 tests that protect nothing (Session AT's after-capture, ITS worktree, hydrated)",
  "captured_utc": "2026-07-29T23:25:26Z",
  "dirty": false,
  "totals": {
   "failed": 58,
   "passed": 11004,
   "skipped": 125,
   "xfailed": 1,
   "error": 9
  }
 },
 "after": {
  "commit": "94a212abc1830cbf27e74663a117f0019b0f703d",
  "commit_subject": "gtos_hydrate_test_data: AT's twenty-line gap, built \u2014 hydration now survives a fresh worktree",
  "captured_utc": "2026-07-30T00:37:35Z",
  "dirty": true,
  "totals": {
   "failed": 75,
   "passed": 11169,
   "skipped": 79,
   "xfailed": 1,
   "error": 6
  }
 },
 "bad_before": 67,
 "bad_after": 81,
 "unchanged": 63,
 "fixed": [
  "tests/test_a1_analyze.py",
  "tests/test_pending_nofill_lifecycle_v4.py::test_wave2_877_pending_rows_project_to_v4_fixture_shape",
  "tests/test_vnext_absolute_moonshot_lane16_historical_microscope_scale.py",
  "tests/test_vnext_moonshot_lane10b_scheduler_conflict_anatomy_multiticket_design.py"
 ],
 "regressed": [
  "tests/test_analyze_b7_5_extended_history_behavior.py::test_canonical_verifier_accepts_current_cross_window_proof",
  "tests/test_replay_acceleration_candidate_boundary.py::test_independent_verifier_consumes_persisted_bytes",
  "tests/test_replay_acceleration_final_route_decision.py::test_prospective_amendment_remains_non_authoritative",
  "tests/test_replay_acceleration_progressive_benchmark.py::test_independent_verifier_measures_its_persisted_byte_pass",
  "tests/test_replay_acceleration_progressive_benchmark.py::test_persisted_progressive_result_is_verified_independently",
  "tests/test_replay_acceleration_resource_architecture.py::test_compression_and_hash_measurements_are_narrow_and_honest",
  "tests/test_replay_acceleration_resource_architecture.py::test_independent_resource_verifier_consumes_persisted_result",
  "tests/test_replay_acceleration_resource_architecture.py::test_resource_inventory_preserves_evidence_and_bounds_each_slice",
  "tests/test_replay_acceleration_resume.py::test_checkpoint_contains_full_canonical_arm_state",
  "tests/test_replay_acceleration_resume.py::test_independent_resume_verifier_consumes_persisted_checkpoints",
  "tests/test_replay_acceleration_resume.py::test_resume_route_root_is_deterministic",
  "tests/test_replay_acceleration_resume.py::test_resume_scenarios_converge_and_bound_unsealed_loss",
  "tests/test_replay_acceleration_resume.py::test_stale_wrong_and_interruption_failure_matrix",
  "tests/test_replay_acceleration_typed_proofs.py::test_typed_campaign_roots_are_deterministic_across_fresh_writes",
  "tests/test_replay_acceleration_typed_proofs.py::test_typed_day_shards_round_trip_exact_legacy_projections",
  "tests/test_replay_acceleration_typed_proofs.py::test_typed_failure_injection_matrix_rejects_all_mutations",
  "tests/test_replay_columnar_source.py::test_verification_retains_no_rows",
  "tests/test_vnext_absolute_moonshot_lane16_historical_microscope_scale.py::test_lane16_written_route_outputs_verify_without_rebuild"
 ],
 "bad_before_nodeids": [
  "tests/research_infra/test_moonshot_unified_execution_scorer.py",
  "tests/safety/test_activation_token.py::test_the_mutating_surface_has_not_widened",
  "tests/test_a1_analyze.py",
  "tests/test_adaptive_review.py::TestWeeklyInsights::test_generate_weekly_insights",
  "tests/test_analyze_b7_5_extended_history_behavior.py::test_aggregate_rows_keeps_terminal_unscoreable_trade_out_of_wlf_and_r",
  "tests/test_analyze_b7_5_extended_history_behavior.py::test_cross_window_execution_digest_mismatch_fails_truth",
  "tests/test_analyze_b7_5_extended_history_behavior.py::test_cross_window_truth_can_pass_while_economic_generalization_fails",
  "tests/test_analyze_b7_5_extended_history_behavior.py::test_non_additive_signal_is_not_reported_as_executable_r_percentage",
  "tests/test_analyze_b7_5_extended_history_behavior.py::test_window_report_rejects_loaded_trade_count_mismatch",
  "tests/test_armed_set_mc.py::test_sealed_defaults_write_no_sizing_convention_block_and_non_sealed_does",
  "tests/test_b7_5_extended_history_source_window_contract.py::test_b7_5_harness_requires_both_contract_hashes_before_source_resolution",
  "tests/test_b7_5_extended_history_source_window_contract.py::test_behavioral_execution_digest_ignores_only_postrun_proof_consumer_drift",
  "tests/test_b7_5_extended_history_source_window_contract.py::test_capacity_projection_uses_v258_bytes_and_preserves_reserve",
  "tests/test_b7_5_extended_history_source_window_contract.py::test_contract_is_deterministic_replay_free_and_fails_on_unmatched_axis",
  "tests/test_b7_5_extended_history_source_window_contract.py::test_selector_dispositions_cover_every_axis_and_keep_absence_explicit",
  "tests/test_b7_5_neutral_selection_factorial.py::test_unbound_packet_shape_and_s1r1_runtime_behavior_are_preserved",
  "tests/test_b7_5_post_acceleration_contract.py::test_attempt5_runtime_accepts_successor_and_rejects_predecessor_chain_tamper",
  "tests/test_bugfixes_0.py::TestCandidateFeaturesLoggedOnPreAiGate::test_pre_ai_gate_skip_writes_candidate_features_row",
  "tests/test_chart_renderer.py",
  "tests/test_deployment_prep.py::TestTradeParameterRecording::test_existing_sessions_parseable",
  "tests/test_dual_broker_execution_follower.py::test_ftmo_follower_profile_covers_live_symbols_and_broker_geometry",
  "tests/test_integration_live.py::TestLimitFillExitDataCaptured::test_limit_fill_promotes_pending_record_to_active",
  "tests/test_jsonl_rotation.py::test_cleanup_pending_compresses_leftovers",
  "tests/test_jsonl_rotation.py::test_time_trigger_rotates_at_utc_midnight_cross",
  "tests/test_mc_firm_rules.py::test_the_published_grid_reconstructs_and_the_two_survivor_sets_differ",
  "tests/test_mc_firm_rules.py::test_this_engine_reproduces_every_published_mc_field_exactly",
  "tests/test_pending_nofill_lifecycle_v4.py::test_wave2_877_pending_rows_project_to_v4_fixture_shape",
  "tests/test_replay_acceleration_final_route_decision.py::test_all_bounded_layers_are_accepted_before_final_decision",
  "tests/test_replay_acceleration_final_route_decision.py::test_golden_availability_probe_is_structural_only",
  "tests/test_replay_acceleration_partial_golden.py::test_structural_successor_is_accepted_as_latest_exact_golden",
  "tests/test_replay_acceleration_physical_reference_runner.py::test_physical_reference_args_are_exact_and_cache_free",
  "tests/test_replay_acceleration_progressive_benchmark.py::test_prospective_two_day_receipt_is_allowlisted_and_outcome_blind",
  "tests/test_replay_acceleration_source_rebind_successor.py::test_successor_run_and_verifier_envelope_are_self_authenticated",
  "tests/test_replay_acceleration_task2_semantic_acceptance.py::test_existing_semantic_manifest_authenticates_complete_inventory",
  "tests/test_replay_acceleration_task2_semantic_acceptance.py::test_summary_authority_rejects_nested_execution_option_change",
  "tests/test_replay_acceleration_task2_semantic_acceptance.py::test_summary_authority_rejects_unknown_nested_field",
  "tests/test_replay_acceleration_task2_semantic_slice_runner.py::test_direct_semantic_manifest_binds_every_evidence_file",
  "tests/test_replay_acceleration_task7_isolated_runner.py::test_task7_authenticates_task6_and_corrected_no_event_pack",
  "tests/test_replay_acceleration_task7_isolated_runner.py::test_task7_independent_verifier_recomputes_review_repaired_gate",
  "tests/test_retest_geometry_study.py",
  "tests/test_side_aware_sizing.py::TestContextualSideRisk::test_ready8_context_rule_artifact_adds_haz001_branch_support",
  "tests/test_side_aware_sizing.py::TestContextualSideRisk::test_ready8_context_rule_artifact_requires_descriptor_anchors",
  "tests/test_side_aware_sizing.py::TestContextualSideRisk::test_ready8_discriminative_context_artifact_adds_support_and_inverse_risk",
  "tests/test_side_aware_sizing.py::TestContextualSideRisk::test_ready8_failure_context_adjustment_artifact_zeroes_control_explained_support",
  "tests/test_sl_beyond_ob_precision_aware.py::TestSlBeyondObTickSizeProductionConfig::test_resolved_floor_exceeds_expected_minimum[NAS100-0.1]",
  "tests/test_sl_beyond_ob_precision_aware.py::TestSlBeyondObTickSizeProductionConfig::test_resolved_floor_exceeds_expected_minimum[US30-0.1]",
  "tests/test_sl_beyond_ob_precision_aware.py::TestSlBeyondObTickSizeProductionConfig::test_resolved_floor_exceeds_expected_minimum[US30_cash-0.1]",
  "tests/test_sl_beyond_ob_precision_aware.py::TestSlBeyondObTickSizeProductionConfig::test_resolved_nas100_tick_size_in_config",
  "tests/test_sprt_class_halt_check.py::test_production_config_has_sprt_halt_block",
  "tests/test_sprt_class_halt_check.py::test_production_config_smoke_via_check",
  "tests/test_sprt_class_halt_check.py::test_production_config_tight_fx_excluded",
  "tests/test_structure_detector_shadow.py::TestBuildTimeframeStateWiring::test_logger_crash_inside_logger_does_not_break_production",
  "tests/test_structure_detector_shadow.py::TestBuildTimeframeStateWiring::test_v2_mode_logs_divergence_and_uses_v2_for_production",
  "tests/test_structure_detector_shadow.py::TestBuildTimeframeStateWiring::test_v2_shadow_mode_logs_divergence",
  "tests/test_structure_detector_shadow.py::TestSymbolPropagationEndToEnd::test_every_instrument_reaches_shadow_log",
  "tests/test_structure_detector_shadow.py::TestSymbolPropagationEndToEnd::test_us30_cash_canonical_reaches_shadow_log",
  "tests/test_structure_detector_shadow.py::TestSymbolPropagationEndToEnd::test_xauusd_symbol_reaches_shadow_log",
  "tests/test_vnext_absolute_moonshot_lane16_historical_microscope_scale.py",
  "tests/test_vnext_absolute_moonshot_scheduler_v3.py",
  "tests/test_vnext_ftmo_local_profile_and_vps_dual_prod_prep.py",
  "tests/test_vnext_lane05_portfolio_scheduler.py::test_governed_vnext_same_symbol_position_conflict_is_explicit_ticket_guard",
  "tests/test_vnext_moonshot_lane10_portfolio_scheduler_v2.py",
  "tests/test_vnext_moonshot_lane10b_scheduler_conflict_anatomy_multiticket_design.py",
  "tests/test_vnext_production_wiring.py::test_current_profile_overlay_matches_current_stage03_resolvable_symbols",
  "tests/test_vnext_production_wiring.py::test_live_monitor_runtime_universe_is_config_derived_and_matches_stage03_surface",
  "tests/ultimate_book/test_a8_live_activation_config.py::test_active_live_config_arms_a8_gate_with_smooth_ceiling_profile",
  "tests/ultimate_book/test_market_expansion_runtime_generator.py::test_active_market_expansion_bridge_telemetry_exposes_reload_parity_flags"
 ],
 "bad_after_nodeids": [
  "tests/research_infra/test_moonshot_unified_execution_scorer.py",
  "tests/safety/test_activation_token.py::test_the_mutating_surface_has_not_widened",
  "tests/test_adaptive_review.py::TestWeeklyInsights::test_generate_weekly_insights",
  "tests/test_analyze_b7_5_extended_history_behavior.py::test_aggregate_rows_keeps_terminal_unscoreable_trade_out_of_wlf_and_r",
  "tests/test_analyze_b7_5_extended_history_behavior.py::test_canonical_verifier_accepts_current_cross_window_proof",
  "tests/test_analyze_b7_5_extended_history_behavior.py::test_cross_window_execution_digest_mismatch_fails_truth",
  "tests/test_analyze_b7_5_extended_history_behavior.py::test_cross_window_truth_can_pass_while_economic_generalization_fails",
  "tests/test_analyze_b7_5_extended_history_behavior.py::test_non_additive_signal_is_not_reported_as_executable_r_percentage",
  "tests/test_analyze_b7_5_extended_history_behavior.py::test_window_report_rejects_loaded_trade_count_mismatch",
  "tests/test_armed_set_mc.py::test_sealed_defaults_write_no_sizing_convention_block_and_non_sealed_does",
  "tests/test_b7_5_extended_history_source_window_contract.py::test_b7_5_harness_requires_both_contract_hashes_before_source_resolution",
  "tests/test_b7_5_extended_history_source_window_contract.py::test_behavioral_execution_digest_ignores_only_postrun_proof_consumer_drift",
  "tests/test_b7_5_extended_history_source_window_contract.py::test_capacity_projection_uses_v258_bytes_and_preserves_reserve",
  "tests/test_b7_5_extended_history_source_window_contract.py::test_contract_is_deterministic_replay_free_and_fails_on_unmatched_axis",
  "tests/test_b7_5_extended_history_source_window_contract.py::test_selector_dispositions_cover_every_axis_and_keep_absence_explicit",
  "tests/test_b7_5_neutral_selection_factorial.py::test_unbound_packet_shape_and_s1r1_runtime_behavior_are_preserved",
  "tests/test_b7_5_post_acceleration_contract.py::test_attempt5_runtime_accepts_successor_and_rejects_predecessor_chain_tamper",
  "tests/test_bugfixes_0.py::TestCandidateFeaturesLoggedOnPreAiGate::test_pre_ai_gate_skip_writes_candidate_features_row",
  "tests/test_chart_renderer.py",
  "tests/test_deployment_prep.py::TestTradeParameterRecording::test_existing_sessions_parseable",
  "tests/test_dual_broker_execution_follower.py::test_ftmo_follower_profile_covers_live_symbols_and_broker_geometry",
  "tests/test_integration_live.py::TestLimitFillExitDataCaptured::test_limit_fill_promotes_pending_record_to_active",
  "tests/test_jsonl_rotation.py::test_cleanup_pending_compresses_leftovers",
  "tests/test_jsonl_rotation.py::test_time_trigger_rotates_at_utc_midnight_cross",
  "tests/test_mc_firm_rules.py::test_the_published_grid_reconstructs_and_the_two_survivor_sets_differ",
  "tests/test_mc_firm_rules.py::test_this_engine_reproduces_every_published_mc_field_exactly",
  "tests/test_replay_acceleration_candidate_boundary.py::test_independent_verifier_consumes_persisted_bytes",
  "tests/test_replay_acceleration_final_route_decision.py::test_all_bounded_layers_are_accepted_before_final_decision",
  "tests/test_replay_acceleration_final_route_decision.py::test_golden_availability_probe_is_structural_only",
  "tests/test_replay_acceleration_final_route_decision.py::test_prospective_amendment_remains_non_authoritative",
  "tests/test_replay_acceleration_partial_golden.py::test_structural_successor_is_accepted_as_latest_exact_golden",
  "tests/test_replay_acceleration_physical_reference_runner.py::test_physical_reference_args_are_exact_and_cache_free",
  "tests/test_replay_acceleration_progressive_benchmark.py::test_independent_verifier_measures_its_persisted_byte_pass",
  "tests/test_replay_acceleration_progressive_benchmark.py::test_persisted_progressive_result_is_verified_independently",
  "tests/test_replay_acceleration_progressive_benchmark.py::test_prospective_two_day_receipt_is_allowlisted_and_outcome_blind",
  "tests/test_replay_acceleration_resource_architecture.py::test_compression_and_hash_measurements_are_narrow_and_honest",
  "tests/test_replay_acceleration_resource_architecture.py::test_independent_resource_verifier_consumes_persisted_result",
  "tests/test_replay_acceleration_resource_architecture.py::test_resource_inventory_preserves_evidence_and_bounds_each_slice",
  "tests/test_replay_acceleration_resume.py::test_checkpoint_contains_full_canonical_arm_state",
  "tests/test_replay_acceleration_resume.py::test_independent_resume_verifier_consumes_persisted_checkpoints",
  "tests/test_replay_acceleration_resume.py::test_resume_route_root_is_deterministic",
  "tests/test_replay_acceleration_resume.py::test_resume_scenarios_converge_and_bound_unsealed_loss",
  "tests/test_replay_acceleration_resume.py::test_stale_wrong_and_interruption_failure_matrix",
  "tests/test_replay_acceleration_source_rebind_successor.py::test_successor_run_and_verifier_envelope_are_self_authenticated",
  "tests/test_replay_acceleration_task2_semantic_acceptance.py::test_existing_semantic_manifest_authenticates_complete_inventory",
  "tests/test_replay_acceleration_task2_semantic_acceptance.py::test_summary_authority_rejects_nested_execution_option_change",
  "tests/test_replay_acceleration_task2_semantic_acceptance.py::test_summary_authority_rejects_unknown_nested_field",
  "tests/test_replay_acceleration_task2_semantic_slice_runner.py::test_direct_semantic_manifest_binds_every_evidence_file",
  "tests/test_replay_acceleration_task7_isolated_runner.py::test_task7_authenticates_task6_and_corrected_no_event_pack",
  "tests/test_replay_acceleration_task7_isolated_runner.py::test_task7_independent_verifier_recomputes_review_repaired_gate",
  "tests/test_replay_acceleration_typed_proofs.py::test_typed_campaign_roots_are_deterministic_across_fresh_writes",
  "tests/test_replay_acceleration_typed_proofs.py::test_typed_day_shards_round_trip_exact_legacy_projections",
  "tests/test_replay_acceleration_typed_proofs.py::test_typed_failure_injection_matrix_rejects_all_mutations",
  "tests/test_replay_columnar_source.py::test_verification_retains_no_rows",
  "tests/test_retest_geometry_study.py",
  "tests/test_side_aware_sizing.py::TestContextualSideRisk::test_ready8_context_rule_artifact_adds_haz001_branch_support",
  "tests/test_side_aware_sizing.py::TestContextualSideRisk::test_ready8_context_rule_artifact_requires_descriptor_anchors",
  "tests/test_side_aware_sizing.py::TestContextualSideRisk::test_ready8_discriminative_context_artifact_adds_support_and_inverse_risk",
  "tests/test_side_aware_sizing.py::TestContextualSideRisk::test_ready8_failure_context_adjustment_artifact_zeroes_control_explained_support",
  "tests/test_sl_beyond_ob_precision_aware.py::TestSlBeyondObTickSizeProductionConfig::test_resolved_floor_exceeds_expected_minimum[NAS100-0.1]",
  "tests/test_sl_beyond_ob_precision_aware.py::TestSlBeyondObTickSizeProductionConfig::test_resolved_floor_exceeds_expected_minimum[US30-0.1]",
  "tests/test_sl_beyond_ob_precision_aware.py::TestSlBeyondObTickSizeProductionConfig::test_resolved_floor_exceeds_expected_minimum[US30_cash-0.1]",
  "tests/test_sl_beyond_ob_precision_aware.py::TestSlBeyondObTickSizeProductionConfig::test_resolved_nas100_tick_size_in_config",
  "tests/test_sprt_class_halt_check.py::test_production_config_has_sprt_halt_block",
  "tests/test_sprt_class_halt_check.py::test_production_config_smoke_via_check",
  "tests/test_sprt_class_halt_check.py::test_production_config_tight_fx_excluded",
  "tests/test_structure_detector_shadow.py::TestBuildTimeframeStateWiring::test_logger_crash_inside_logger_does_not_break_production",
  "tests/test_structure_detector_shadow.py::TestBuildTimeframeStateWiring::test_v2_mode_logs_divergence_and_uses_v2_for_production",
  "tests/test_structure_detector_shadow.py::TestBuildTimeframeStateWiring::test_v2_shadow_mode_logs_divergence",
  "tests/test_structure_detector_shadow.py::TestSymbolPropagationEndToEnd::test_every_instrument_reaches_shadow_log",
  "tests/test_structure_detector_shadow.py::TestSymbolPropagationEndToEnd::test_us30_cash_canonical_reaches_shadow_log",
  "tests/test_structure_detector_shadow.py::TestSymbolPropagationEndToEnd::test_xauusd_symbol_reaches_shadow_log",
  "tests/test_vnext_absolute_moonshot_lane16_historical_microscope_scale.py::test_lane16_written_route_outputs_verify_without_rebuild",
  "tests/test_vnext_absolute_moonshot_scheduler_v3.py",
  "tests/test_vnext_ftmo_local_profile_and_vps_dual_prod_prep.py",
  "tests/test_vnext_lane05_portfolio_scheduler.py::test_governed_vnext_same_symbol_position_conflict_is_explicit_ticket_guard",
  "tests/test_vnext_moonshot_lane10_portfolio_scheduler_v2.py",
  "tests/test_vnext_production_wiring.py::test_current_profile_overlay_matches_current_stage03_resolvable_symbols",
  "tests/test_vnext_production_wiring.py::test_live_monitor_runtime_universe_is_config_derived_and_matches_stage03_surface",
  "tests/ultimate_book/test_a8_live_activation_config.py::test_active_live_config_arms_a8_gate_with_smooth_ceiling_profile",
  "tests/ultimate_book/test_market_expansion_runtime_generator.py::test_active_market_expansion_bridge_telemetry_exposes_reload_parity_flags"
 ]
}
```
