# Session CN — scoped A/B vs the committed ZERO baseline

**0 bad → 0 bad · 0 fixed · 0 regressed. No regressions.**

Compared by **failure set**, not by count — counts are not portable across worktrees.

| | before | after |
|---|---|---|
| commit | `6608eb969` | `b5a76fed4` |
| captured (UTC) | 2026-07-31T17:26:48Z | 2026-07-31T19:04:15Z |
| working tree | dirty | dirty |
| failed | 0 | 0 |
| errored | 0 | 0 |
| **bad** | **0** | **0** |
| passed | 12600 | 4100 |
| skipped | 120 | 19 |

## Scope difference — declared, not hidden

- before: `['tests/']`
- after : `['tests/costs/test_cost_artifact_absence_message.py', 'tests/replay/test_decision_invariance.py', 'tests/research_infra/test_cn_live_cost_carry.py', 'tests/research_infra/test_cn_live_cost_truth.py', 'tests/research_infra/test_fast_engine_accel.py', 'tests/research_infra/test_fast_engine_sealed_inputs.py', 'tests/research_infra/test_train_engine_lane.py', 'tests/safety/test_activation_token.py', 'tests/test_ai_call_policy.py', 'tests/test_ai_supervisor.py', 'tests/test_autocorrelation_risk.py', 'tests/test_b7_5_neutral_selection_factorial.py', 'tests/test_b7_5_selection_sizing_factorial_runtime.py', 'tests/test_broad_replay_repair_config.py', 'tests/test_broker_net_cost_engine.py', 'tests/test_broker_profile_namespace.py', 'tests/test_bugfixes_0.py', 'tests/test_build_source_bound_execution_parity.py', 'tests/test_concurrent_cap.py', 'tests/test_cross_instrument_correlation_gate.py', 'tests/test_daily_loss_stop.py', 'tests/test_deployment_prep.py', 'tests/test_divergence_matrix.py', 'tests/test_dual_broker_execution_follower.py', 'tests/test_equity_guard.py', 'tests/test_execution.py', 'tests/test_execution_manager_v4.py', 'tests/test_execution_volume_normalization.py', 'tests/test_exit_wiring.py', 'tests/test_exit_wiring_short_r.py', 'tests/test_gbpusd_context_strip.py', 'tests/test_gtos_vnext_runtime.py', 'tests/test_implementation_state_block_citations.py', 'tests/test_integration_live.py', 'tests/test_j46_j49_policy.py', 'tests/test_limit_order_flow.py', 'tests/test_live_config_truth.py', 'tests/test_m5_refinement.py', 'tests/test_market_whiteboard_v2.py', 'tests/test_mfe_mae_m5.py', 'tests/test_opus5_architecture_audit_hardening.py', 'tests/test_orchestrator.py', 'tests/test_pending_limit_lifecycle_logger.py', 'tests/test_permissions.py', 'tests/test_prelaunch_audit.py', 'tests/test_probability_debate_v4.py', 'tests/test_replay_acceleration_attempt5_typed_sparse_runner.py', 'tests/test_replay_acceleration_campaign_exact_cache.py', 'tests/test_replay_acceleration_candidate_boundary.py', 'tests/test_replay_acceleration_integrated_source.py', 'tests/test_replay_acceleration_isolated_reducers.py', 'tests/test_replay_acceleration_progressive_benchmark.py', 'tests/test_replay_acceleration_resume.py', 'tests/test_replay_acceleration_source_batch.py', 'tests/test_replay_acceleration_task6_prepared_pack_acceptance.py', 'tests/test_replay_acceleration_task7_isolated_runner.py', 'tests/test_replay_acceleration_task8_profile_runner.py', 'tests/test_replay_acceleration_task9_final_validation.py', 'tests/test_replay_columnar_source.py', 'tests/test_replay_prepared_day_pack.py', 'tests/test_replay_prepared_day_pack_integration.py', 'tests/test_replay_semantic_parity.py', 'tests/test_runtime_control_atomic_halt.py', 'tests/test_same_symbol_lifecycle_v4.py', 'tests/test_shadow_data_collection.py', 'tests/test_side_aware_sizing.py', 'tests/test_simulation_fixes.py', 'tests/test_sizing_profile_overlay_and_currency.py', 'tests/test_skip_ny_open.py', 'tests/test_slippage_shadow_logger.py', 'tests/test_sprt_class_halt_runtime.py', 'tests/test_structural_c_gate.py', 'tests/test_t7_deployment.py', 'tests/test_time_in_trade_shadow_logger.py', 'tests/test_timewarp_order_fillability_policy.py', 'tests/test_timewarp_profit_harvest_policy.py', 'tests/test_timewarp_scheduler_materialization.py', 'tests/test_timewarp_trade_params_live_shape.py', 'tests/test_touch_count_shadow_logger.py', 'tests/test_trade_capture.py', 'tests/test_trade_management_cascade_fix.py', 'tests/test_trailing_stop_shadow_logger.py', 'tests/test_v4_kia_parity_tick_first_runtime_repair.py', 'tests/test_v4_know_it_all_live_replay_runtime.py', 'tests/test_v4_timewarp_simulated_live_research_loop.py', 'tests/test_verification.py', 'tests/test_vnext_broader_origin_orchestrator.py', 'tests/test_vnext_lane05_portfolio_scheduler.py', 'tests/ultimate_book/test_activation_carry_vps_lineage.py', 'tests/ultimate_book/test_az_activation_carry_mx.py', 'tests/ultimate_book/test_ba_weekend_policy.py', 'tests/ultimate_book/test_book_owner.py', 'tests/ultimate_book/test_book_sleeve_telemetry.py', 'tests/ultimate_book/test_breach_flatten.py', 'tests/ultimate_book/test_ce_entry_hour_lever.py', 'tests/ultimate_book/test_frontier_exit_contracts.py', 'tests/ultimate_book/test_market_expansion_runtime_generator.py', 'tests/ultimate_book/test_order_route.py', 'tests/ultimate_book/test_packet_carry_vps_lineage.py', 'tests/ultimate_book/test_packet_emit_on_change.py', 'tests/ultimate_book/test_packet_emitter_hardening.py', 'tests/ultimate_book/test_packet_modelled_cost.py', 'tests/ultimate_book/test_packet_unit_join_key.py', 'tests/ultimate_book/test_pre_gap_bar_wiring.py', 'tests/ultimate_book/test_runtime_learning_packet.py', 'tests/ultimate_book/test_symbol_rename_adoption_gap.py', 'tests/ultimate_book/test_time_stop_rehydration.py', 'tests/ultimate_book/test_time_stop_units.py', 'tests/ultimate_book/test_time_stop_window_coverage.py']`

**Why this is still a comparison:** Before is the committed whole-suite ZERO baseline: 12,600 passed and 0 bad at 6608eb969. After is the tool-derived 109-file import/path closure of the exact Session CN diff from commission base 83867e65f through committed fixture repair b5a76fed4: 4,100 passed and 0 bad. Because the before side has zero failures and zero collection errors suite-wide, any bad test in the after scope would be a regression. The after dirty flag contains only mandatory preflight-generated .context/LIVE_STATE.md and the untracked SCOPE/AFTER receipt artifacts; every CN source, test, result, measurement and carry byte under comparison was committed before capture. Sparse/LFS hydration changed no tracked byte.

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
  "commit": "6608eb969297ed8cbe218662f3987344a576bc6c",
  "commit_subject": "Merge Session CI: the vp time-depth blockade is solved; the comparability gate honestly refuses",
  "captured_utc": "2026-07-31T17:26:48Z",
  "dirty": true,
  "totals": {
   "passed": 12600,
   "skipped": 120,
   "xfailed": 32
  }
 },
 "after": {
  "commit": "b5a76fed499592ff90404380ceb5bd29cf66d5d8",
  "commit_subject": "test: model broker identity in live cost fixtures",
  "captured_utc": "2026-07-31T19:04:15Z",
  "dirty": true,
  "totals": {
   "passed": 4100,
   "skipped": 19,
   "xfailed": 11
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
   "tests/costs/test_cost_artifact_absence_message.py",
   "tests/replay/test_decision_invariance.py",
   "tests/research_infra/test_cn_live_cost_carry.py",
   "tests/research_infra/test_cn_live_cost_truth.py",
   "tests/research_infra/test_fast_engine_accel.py",
   "tests/research_infra/test_fast_engine_sealed_inputs.py",
   "tests/research_infra/test_train_engine_lane.py",
   "tests/safety/test_activation_token.py",
   "tests/test_ai_call_policy.py",
   "tests/test_ai_supervisor.py",
   "tests/test_autocorrelation_risk.py",
   "tests/test_b7_5_neutral_selection_factorial.py",
   "tests/test_b7_5_selection_sizing_factorial_runtime.py",
   "tests/test_broad_replay_repair_config.py",
   "tests/test_broker_net_cost_engine.py",
   "tests/test_broker_profile_namespace.py",
   "tests/test_bugfixes_0.py",
   "tests/test_build_source_bound_execution_parity.py",
   "tests/test_concurrent_cap.py",
   "tests/test_cross_instrument_correlation_gate.py",
   "tests/test_daily_loss_stop.py",
   "tests/test_deployment_prep.py",
   "tests/test_divergence_matrix.py",
   "tests/test_dual_broker_execution_follower.py",
   "tests/test_equity_guard.py",
   "tests/test_execution.py",
   "tests/test_execution_manager_v4.py",
   "tests/test_execution_volume_normalization.py",
   "tests/test_exit_wiring.py",
   "tests/test_exit_wiring_short_r.py",
   "tests/test_gbpusd_context_strip.py",
   "tests/test_gtos_vnext_runtime.py",
   "tests/test_implementation_state_block_citations.py",
   "tests/test_integration_live.py",
   "tests/test_j46_j49_policy.py",
   "tests/test_limit_order_flow.py",
   "tests/test_live_config_truth.py",
   "tests/test_m5_refinement.py",
   "tests/test_market_whiteboard_v2.py",
   "tests/test_mfe_mae_m5.py",
   "tests/test_opus5_architecture_audit_hardening.py",
   "tests/test_orchestrator.py",
   "tests/test_pending_limit_lifecycle_logger.py",
   "tests/test_permissions.py",
   "tests/test_prelaunch_audit.py",
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
   "tests/test_same_symbol_lifecycle_v4.py",
   "tests/test_shadow_data_collection.py",
   "tests/test_side_aware_sizing.py",
   "tests/test_simulation_fixes.py",
   "tests/test_sizing_profile_overlay_and_currency.py",
   "tests/test_skip_ny_open.py",
   "tests/test_slippage_shadow_logger.py",
   "tests/test_sprt_class_halt_runtime.py",
   "tests/test_structural_c_gate.py",
   "tests/test_t7_deployment.py",
   "tests/test_time_in_trade_shadow_logger.py",
   "tests/test_timewarp_order_fillability_policy.py",
   "tests/test_timewarp_profit_harvest_policy.py",
   "tests/test_timewarp_scheduler_materialization.py",
   "tests/test_timewarp_trade_params_live_shape.py",
   "tests/test_touch_count_shadow_logger.py",
   "tests/test_trade_capture.py",
   "tests/test_trade_management_cascade_fix.py",
   "tests/test_trailing_stop_shadow_logger.py",
   "tests/test_v4_kia_parity_tick_first_runtime_repair.py",
   "tests/test_v4_know_it_all_live_replay_runtime.py",
   "tests/test_v4_timewarp_simulated_live_research_loop.py",
   "tests/test_verification.py",
   "tests/test_vnext_broader_origin_orchestrator.py",
   "tests/test_vnext_lane05_portfolio_scheduler.py",
   "tests/ultimate_book/test_activation_carry_vps_lineage.py",
   "tests/ultimate_book/test_az_activation_carry_mx.py",
   "tests/ultimate_book/test_ba_weekend_policy.py",
   "tests/ultimate_book/test_book_owner.py",
   "tests/ultimate_book/test_book_sleeve_telemetry.py",
   "tests/ultimate_book/test_breach_flatten.py",
   "tests/ultimate_book/test_ce_entry_hour_lever.py",
   "tests/ultimate_book/test_frontier_exit_contracts.py",
   "tests/ultimate_book/test_market_expansion_runtime_generator.py",
   "tests/ultimate_book/test_order_route.py",
   "tests/ultimate_book/test_packet_carry_vps_lineage.py",
   "tests/ultimate_book/test_packet_emit_on_change.py",
   "tests/ultimate_book/test_packet_emitter_hardening.py",
   "tests/ultimate_book/test_packet_modelled_cost.py",
   "tests/ultimate_book/test_packet_unit_join_key.py",
   "tests/ultimate_book/test_pre_gap_bar_wiring.py",
   "tests/ultimate_book/test_runtime_learning_packet.py",
   "tests/ultimate_book/test_symbol_rename_adoption_gap.py",
   "tests/ultimate_book/test_time_stop_rehydration.py",
   "tests/ultimate_book/test_time_stop_units.py",
   "tests/ultimate_book/test_time_stop_window_coverage.py"
  ],
  "justification": "Before is the committed whole-suite ZERO baseline: 12,600 passed and 0 bad at 6608eb969. After is the tool-derived 109-file import/path closure of the exact Session CN diff from commission base 83867e65f through committed fixture repair b5a76fed4: 4,100 passed and 0 bad. Because the before side has zero failures and zero collection errors suite-wide, any bad test in the after scope would be a regression. The after dirty flag contains only mandatory preflight-generated .context/LIVE_STATE.md and the untracked SCOPE/AFTER receipt artifacts; every CN source, test, result, measurement and carry byte under comparison was committed before capture. Sparse/LFS hydration changed no tracked byte."
 }
}
```
