# Session CQ — scoped A/B vs the committed ZERO baseline

**0 bad → 0 bad · 0 fixed · 0 regressed. No regressions.**

Compared by **failure set**, not by count — counts are not portable across worktrees.

| | before | after |
|---|---|---|
| commit | `79d34a8d5` | `15375e936` |
| captured (UTC) | 2026-07-31T20:15:59Z | 2026-07-31T21:28:09Z |
| working tree | dirty | dirty |
| failed | 0 | 0 |
| errored | 0 | 0 |
| **bad** | **0** | **0** |
| passed | 12671 | 3327 |
| skipped | 120 | 13 |

## Scope difference — declared, not hidden

- before: `['tests/']`
- after : `['tests/research_infra/test_ao_candidate_family_v3.py', 'tests/research_infra/test_ao_p_floor_headroom.py', 'tests/research_infra/test_candidate_family.py', 'tests/research_infra/test_candidate_family_chain.py', 'tests/research_infra/test_candidate_family_v2_ratchet.py', 'tests/research_infra/test_cq_path_pool_grid.py', 'tests/research_infra/test_era_population.py', 'tests/research_infra/test_fast_engine_accel.py', 'tests/research_infra/test_fast_engine_sealed_inputs.py', 'tests/research_infra/test_fidelity_register_matches_receipt.py', 'tests/research_infra/test_fidelity_threshold_variant.py', 'tests/research_infra/test_gate_partial_universe_stamp.py', 'tests/research_infra/test_gate_wipeout_signal.py', 'tests/research_infra/test_lane_rematerialization.py', 'tests/research_infra/test_train_engine_lane.py', 'tests/research_infra/test_trainer_folds.py', 'tests/research_infra/test_training_lane_protocol.py', 'tests/research_infra/test_walkforward_book_replay.py', 'tests/research_infra/test_walkforward_family.py', 'tests/research_infra/test_walkforward_gate.py', 'tests/research_infra/test_walkforward_supply.py', 'tests/research_infra/test_wf_diagnostics.py', 'tests/test_ai_call_policy.py', 'tests/test_ai_supervisor.py', 'tests/test_autocorrelation_risk.py', 'tests/test_b7_5_neutral_selection_factorial.py', 'tests/test_b7_5_selection_sizing_factorial_runtime.py', 'tests/test_broad_replay_repair_config.py', 'tests/test_broader_origin_generators.py', 'tests/test_broader_origin_predecision_features.py', 'tests/test_broker_clock_truth.py', 'tests/test_broker_profile_namespace.py', 'tests/test_bugfixes_0.py', 'tests/test_build_source_bound_execution_parity.py', 'tests/test_daily_loss_stop.py', 'tests/test_data_ingestion.py', 'tests/test_deployment_prep.py', 'tests/test_divergence_matrix.py', 'tests/test_equity_guard.py', 'tests/test_exit_wiring.py', 'tests/test_exit_wiring_short_r.py', 'tests/test_gbpusd_context_strip.py', 'tests/test_gtos_vnext_runtime.py', 'tests/test_integration_live.py', 'tests/test_mfe_mae_m5.py', 'tests/test_opus5_architecture_audit_hardening.py', 'tests/test_orchestrator.py', 'tests/test_probability_debate_v4.py', 'tests/test_replay_acceleration_attempt5_typed_sparse_runner.py', 'tests/test_replay_acceleration_campaign_exact_cache.py', 'tests/test_replay_acceleration_candidate_boundary.py', 'tests/test_replay_acceleration_integrated_source.py', 'tests/test_replay_acceleration_isolated_reducers.py', 'tests/test_replay_acceleration_progressive_benchmark.py', 'tests/test_replay_acceleration_resume.py', 'tests/test_replay_acceleration_source_batch.py', 'tests/test_replay_acceleration_task6_prepared_pack_acceptance.py', 'tests/test_replay_acceleration_task7_isolated_runner.py', 'tests/test_replay_acceleration_task8_profile_runner.py', 'tests/test_replay_acceleration_task9_final_validation.py', 'tests/test_replay_columnar_source.py', 'tests/test_replay_prepared_day_pack.py', 'tests/test_replay_prepared_day_pack_integration.py', 'tests/test_replay_semantic_parity.py', 'tests/test_runtime_control_atomic_halt.py', 'tests/test_shadow_data_collection.py', 'tests/test_side_aware_sizing.py', 'tests/test_simulation_fixes.py', 'tests/test_skip_ny_open.py', 'tests/test_spread_composition.py', 'tests/test_sprt_class_halt_runtime.py', 'tests/test_structural_c_gate.py', 'tests/test_t7_deployment.py', 'tests/test_time_in_trade_shadow_logger.py', 'tests/test_timewarp_order_fillability_policy.py', 'tests/test_timewarp_profit_harvest_policy.py', 'tests/test_timewarp_scheduler_materialization.py', 'tests/test_timewarp_trade_params_live_shape.py', 'tests/test_trade_management_cascade_fix.py', 'tests/test_trailing_stop_shadow_logger.py', 'tests/test_v4_kia_parity_tick_first_runtime_repair.py', 'tests/test_v4_know_it_all_live_replay_runtime.py', 'tests/test_v4_timewarp_simulated_live_research_loop.py', 'tests/test_verification.py', 'tests/test_vnext_broader_origin_orchestrator.py', 'tests/test_vnext_production_wiring.py']`

**Why this is still a comparison:** The committed before capture is the suite-wide ZERO baseline; CQ's after capture is the tool-derived 86-file import/path-literal closure for all 18 implementation-commit paths, with zero standing-failure files to union. Comparing bad-ID sets is valid because the before set is empty and the after scope contains every test reached by CQ's changed code, tests, ledgers, and receipts.

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
  "commit": "79d34a8d50d171d4165e3d886702fcb161686df0",
  "commit_subject": "R2 rebuild test now asserts the break is exactly CN's authorized one",
  "captured_utc": "2026-07-31T20:15:59Z",
  "dirty": true,
  "totals": {
   "passed": 12671,
   "skipped": 120,
   "xfailed": 32
  }
 },
 "after": {
  "commit": "15375e93646a2f38fc8e83639692fcc0ece0e8de",
  "commit_subject": "feat(phase18): build path-complete breaker repair",
  "captured_utc": "2026-07-31T21:28:09Z",
  "dirty": true,
  "totals": {
   "passed": 3327,
   "skipped": 13,
   "xfailed": 9
  }
 },
 "bad_before": 0,
 "bad_after": 0,
 "unchanged": 0,
 "fixed": [],
 "regressed": [],
 "bad_before_nodeids": [],
 "bad_after_nodeids": [],
 "scope_difference": {
  "before": [
   "tests/"
  ],
  "after": [
   "tests/research_infra/test_ao_candidate_family_v3.py",
   "tests/research_infra/test_ao_p_floor_headroom.py",
   "tests/research_infra/test_candidate_family.py",
   "tests/research_infra/test_candidate_family_chain.py",
   "tests/research_infra/test_candidate_family_v2_ratchet.py",
   "tests/research_infra/test_cq_path_pool_grid.py",
   "tests/research_infra/test_era_population.py",
   "tests/research_infra/test_fast_engine_accel.py",
   "tests/research_infra/test_fast_engine_sealed_inputs.py",
   "tests/research_infra/test_fidelity_register_matches_receipt.py",
   "tests/research_infra/test_fidelity_threshold_variant.py",
   "tests/research_infra/test_gate_partial_universe_stamp.py",
   "tests/research_infra/test_gate_wipeout_signal.py",
   "tests/research_infra/test_lane_rematerialization.py",
   "tests/research_infra/test_train_engine_lane.py",
   "tests/research_infra/test_trainer_folds.py",
   "tests/research_infra/test_training_lane_protocol.py",
   "tests/research_infra/test_walkforward_book_replay.py",
   "tests/research_infra/test_walkforward_family.py",
   "tests/research_infra/test_walkforward_gate.py",
   "tests/research_infra/test_walkforward_supply.py",
   "tests/research_infra/test_wf_diagnostics.py",
   "tests/test_ai_call_policy.py",
   "tests/test_ai_supervisor.py",
   "tests/test_autocorrelation_risk.py",
   "tests/test_b7_5_neutral_selection_factorial.py",
   "tests/test_b7_5_selection_sizing_factorial_runtime.py",
   "tests/test_broad_replay_repair_config.py",
   "tests/test_broader_origin_generators.py",
   "tests/test_broader_origin_predecision_features.py",
   "tests/test_broker_clock_truth.py",
   "tests/test_broker_profile_namespace.py",
   "tests/test_bugfixes_0.py",
   "tests/test_build_source_bound_execution_parity.py",
   "tests/test_daily_loss_stop.py",
   "tests/test_data_ingestion.py",
   "tests/test_deployment_prep.py",
   "tests/test_divergence_matrix.py",
   "tests/test_equity_guard.py",
   "tests/test_exit_wiring.py",
   "tests/test_exit_wiring_short_r.py",
   "tests/test_gbpusd_context_strip.py",
   "tests/test_gtos_vnext_runtime.py",
   "tests/test_integration_live.py",
   "tests/test_mfe_mae_m5.py",
   "tests/test_opus5_architecture_audit_hardening.py",
   "tests/test_orchestrator.py",
   "tests/test_probability_debate_v4.py",
   "tests/test_replay_acceleration_attempt5_typed_sparse_runner.py",
   "tests/test_replay_acceleration_campaign_exact_cache.py",
   "tests/test_replay_acceleration_candidate_boundary.py",
   "tests/test_replay_acceleration_integrated_source.py",
   "tests/test_replay_acceleration_isolated_reducers.py",
   "tests/test_replay_acceleration_progressive_benchmark.py",
   "tests/test_replay_acceleration_resume.py",
   "tests/test_replay_acceleration_source_batch.py",
   "tests/test_replay_acceleration_task6_prepared_pack_acceptance.py",
   "tests/test_replay_acceleration_task7_isolated_runner.py",
   "tests/test_replay_acceleration_task8_profile_runner.py",
   "tests/test_replay_acceleration_task9_final_validation.py",
   "tests/test_replay_columnar_source.py",
   "tests/test_replay_prepared_day_pack.py",
   "tests/test_replay_prepared_day_pack_integration.py",
   "tests/test_replay_semantic_parity.py",
   "tests/test_runtime_control_atomic_halt.py",
   "tests/test_shadow_data_collection.py",
   "tests/test_side_aware_sizing.py",
   "tests/test_simulation_fixes.py",
   "tests/test_skip_ny_open.py",
   "tests/test_spread_composition.py",
   "tests/test_sprt_class_halt_runtime.py",
   "tests/test_structural_c_gate.py",
   "tests/test_t7_deployment.py",
   "tests/test_time_in_trade_shadow_logger.py",
   "tests/test_timewarp_order_fillability_policy.py",
   "tests/test_timewarp_profit_harvest_policy.py",
   "tests/test_timewarp_scheduler_materialization.py",
   "tests/test_timewarp_trade_params_live_shape.py",
   "tests/test_trade_management_cascade_fix.py",
   "tests/test_trailing_stop_shadow_logger.py",
   "tests/test_v4_kia_parity_tick_first_runtime_repair.py",
   "tests/test_v4_know_it_all_live_replay_runtime.py",
   "tests/test_v4_timewarp_simulated_live_research_loop.py",
   "tests/test_verification.py",
   "tests/test_vnext_broader_origin_orchestrator.py",
   "tests/test_vnext_production_wiring.py"
  ],
  "justification": "The committed before capture is the suite-wide ZERO baseline; CQ's after capture is the tool-derived 86-file import/path-literal closure for all 18 implementation-commit paths, with zero standing-failure files to union. Comparing bad-ID sets is valid because the before set is empty and the after scope contains every test reached by CQ's changed code, tests, ledgers, and receipts."
 }
}
```
