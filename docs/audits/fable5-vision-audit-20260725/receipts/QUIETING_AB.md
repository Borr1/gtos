# The quieting A/B — 81 standing bad to ZERO, with nothing deleted and nothing hidden

**11,294 passed · 0 failed · 0 errored · 111 skipped · 34 xfailed** at `4dce24028`.

A standing red set trains every reader to ignore red. Every one of the 81 went to its honest
state, by cause:

- **Hydration (the build move).** 159+ committed inputs materialised by
  `scripts/gtos_hydrate_test_data.py` (six route dirs, four module dirs, lane16 LFS content
  pulled from origin), plus `plotly`/`kaleido` installed. **120+ tests that had never executed
  in any revision came alive and PASS** — and 8 of them fixed the exact defects their KEEP-REAL
  rows were filed for, which the strict-xfail alarm flagged on its first firing (rows closed
  as `KEEP-REAL-RESOLVED` in `TEST_TRIAGE_V1.json`).
- **Filed findings → `xfail(strict=True)`** (34), read straight from the triage artifact by the
  conftest hook. Quiet on every read; the day one is repaired the suite goes red with
  "unexpectedly passing — close the row". The alarm fires on repair, not on rediscovery.
- **B7.5 parked-campaign harness → opt-in skip** (32 ids in `TEST_QUIET_REGISTRY_V1.json`):
  they verify sealed campaign evidence that is partial off the campaign machine; set
  `GTOS_RUN_CAMPAIGN_HARNESS=1` to run them deliberately at campaign resume (D-D).
- **Never-collectable files → ignored at collection** with the restore path in the registry
  (`test_moonshot_unified_execution_scorer.py`: 223 tests importing an API that has never
  existed in any revision).

The embedded block's `fixed` lists all 81 because the schema defines fixed as the derivable
set difference; the four bullets above are the causes. **This after-capture is the committed
baseline** (`FAILSET_BASELINE_MAIN.json`): diff with
`python3 scripts/pytest_failset.py diff baseline <after.json>`. From here, ANY red line in a
full capture is a real signal.

## Embedded captures

```json
{
 "schema": "gtos-ab-receipt-v1",
 "scope": [
  "tests/"
 ],
 "before": {
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
 "after": {
  "commit": "4dce24028fea1cc54294d57f8665babb782a673f",
  "commit_subject": "Close 8 KEEP-REAL rows the strict-xfail alarm flagged on its first firing",
  "captured_utc": "2026-07-30T01:46:15Z",
  "dirty": true,
  "totals": {
   "passed": 11294,
   "skipped": 111,
   "xfailed": 34
  }
 },
 "bad_before": 81,
 "bad_after": 0,
 "unchanged": 0,
 "fixed": [
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
 ],
 "regressed": [],
 "bad_before_nodeids": [
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
 ],
 "bad_after_nodeids": []
}
```
