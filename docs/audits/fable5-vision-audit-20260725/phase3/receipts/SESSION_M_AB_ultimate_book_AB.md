# Session M batch 1 A/B — ultimate_book defect register (D3–D11) + B41 vacuous tests

**60 bad → 59 bad · 1 fixed · 0 regressed. No regressions.**

Compared by **failure set**, not by count — counts are not portable across worktrees.

| | before | after |
|---|---|---|
| commit | `8ed443982` | `8ed443982` |
| captured (UTC) | 2026-07-26T21:27:03Z | 2026-07-26T21:28:02Z |
| working tree | dirty | dirty |
| failed | 60 | 59 |
| errored | 0 | 0 |
| **bad** | **60** | **59** |
| passed | 539 | 571 |
| skipped | 0 | 0 |

## Fixed (1)

- `tests/ultimate_book/test_book_engine.py::test_engine_gates_on_produces_realized_units_for_crypto`

## Embedded captures

Embedded, not referenced. A receipt that points at a scratchpad path is as unverifiable as
no receipt at all, because that file is gone by the time anyone reads this.

```json
{
 "schema": "gtos-ab-receipt-v1",
 "scope": [
  "tests/ultimate_book",
  "tests/test_replay_policy_sleeve_book.py"
 ],
 "before": {
  "commit": "8ed4439824f7ccd1fd5ce249509b8a24f9ea5a9d",
  "commit_subject": "Cleanup: retire twelve merged worktrees; preserve the unique .hermes campaign evidence",
  "captured_utc": "2026-07-26T21:27:03Z",
  "dirty": true,
  "totals": {
   "failed": 60,
   "passed": 539
  }
 },
 "after": {
  "commit": "8ed4439824f7ccd1fd5ce249509b8a24f9ea5a9d",
  "commit_subject": "Cleanup: retire twelve merged worktrees; preserve the unique .hermes campaign evidence",
  "captured_utc": "2026-07-26T21:28:02Z",
  "dirty": true,
  "totals": {
   "failed": 59,
   "passed": 571
  }
 },
 "bad_before": 60,
 "bad_after": 59,
 "unchanged": 59,
 "fixed": [
  "tests/ultimate_book/test_book_engine.py::test_engine_gates_on_produces_realized_units_for_crypto"
 ],
 "regressed": [],
 "bad_before_nodeids": [
  "tests/ultimate_book/test_a8_live_activation_config.py::test_active_live_config_arms_a8_gate_with_smooth_ceiling_profile",
  "tests/ultimate_book/test_book_engine.py::test_engine_gates_on_produces_realized_units_for_crypto",
  "tests/ultimate_book/test_candidate_activation_readiness_artifacts.py::test_candidate_activation_readiness_artifact_boundary",
  "tests/ultimate_book/test_candidate_activation_readiness_artifacts.py::test_candidate_activation_readiness_preserves_repair_lanes",
  "tests/ultimate_book/test_candidate_bridge_spec_ltf_work_artifacts.py::test_candidate_bridge_route_closes_ltf_gap_without_mutation",
  "tests/ultimate_book/test_candidate_bridge_spec_ltf_work_artifacts.py::test_candidate_bridge_route_preserves_broker_specific_work_split",
  "tests/ultimate_book/test_candidate_enabled_replay_mc_artifacts.py::test_candidate_enabled_route_core_numbers_and_boundaries",
  "tests/ultimate_book/test_candidate_enabled_replay_mc_artifacts.py::test_candidate_enabled_route_ledgers_preserve_unfinished_and_ready_ideas",
  "tests/ultimate_book/test_candidate_full_book_live_activation_artifacts.py::test_full_candidate_book_live_activation_bridge_and_successor_lanes",
  "tests/ultimate_book/test_candidate_full_book_live_activation_artifacts.py::test_full_candidate_book_live_activation_result_and_numbers",
  "tests/ultimate_book/test_candidate_natgas_decomposition_artifacts.py::test_natgas_decomposition_preserves_ex_natgas_sleeve",
  "tests/ultimate_book/test_candidate_natgas_decomposition_artifacts.py::test_natgas_decomposition_writes_bridge_and_daily_artifacts",
  "tests/ultimate_book/test_candidate_subset_routing_dossier_artifacts.py::test_candidate_subset_routing_dossier_result_and_boundaries",
  "tests/ultimate_book/test_candidate_subset_routing_dossier_artifacts.py::test_candidate_subset_routing_ledger_preserves_full_book_work",
  "tests/ultimate_book/test_market_expansion_activation_candidate_package_artifacts.py::test_activation_candidate_package_counts_and_boundaries",
  "tests/ultimate_book/test_market_expansion_activation_candidate_package_artifacts.py::test_activation_candidate_package_row_controls_and_generator_contracts",
  "tests/ultimate_book/test_market_expansion_activation_readiness_synthesis_artifacts.py::test_activation_readiness_synthesis_authority_detail_preserved",
  "tests/ultimate_book/test_market_expansion_activation_readiness_synthesis_artifacts.py::test_activation_readiness_synthesis_boundary_and_counts",
  "tests/ultimate_book/test_market_expansion_broker_authority_probe_artifacts.py::test_broker_authority_probe_default_off_and_verifier_clean",
  "tests/ultimate_book/test_market_expansion_broker_authority_probe_artifacts.py::test_broker_authority_probe_readonly_evidence_counts",
  "tests/ultimate_book/test_market_expansion_commission_family_transfer_artifacts.py::test_commission_family_transfer_counts_and_no_schedule_overclaim",
  "tests/ultimate_book/test_market_expansion_commission_family_transfer_artifacts.py::test_commission_family_transfer_default_off_and_verifier_clean",
  "tests/ultimate_book/test_market_expansion_conditioned_sizing_refinement_artifacts.py::test_conditioned_sizing_boundary_and_counts",
  "tests/ultimate_book/test_market_expansion_conditioned_sizing_refinement_artifacts.py::test_conditioned_sizing_improves_but_remains_default_off",
  "tests/ultimate_book/test_market_expansion_data_availability_artifacts.py::test_market_expansion_gap_commands_and_inspire_not_kill_rows",
  "tests/ultimate_book/test_market_expansion_data_availability_artifacts.py::test_market_expansion_inventory_and_boundaries",
  "tests/ultimate_book/test_market_expansion_default_off_design_artifacts.py::test_default_off_design_denominator_and_boundaries",
  "tests/ultimate_book/test_market_expansion_default_off_design_artifacts.py::test_default_off_design_risk_budget_and_repair_gates",
  "tests/ultimate_book/test_market_expansion_default_off_registry_artifacts.py::test_default_off_registry_artifacts_match_design_ledger_fields",
  "tests/ultimate_book/test_market_expansion_default_off_registry_artifacts.py::test_default_off_registry_artifacts_preserve_design_and_boundaries",
  "tests/ultimate_book/test_market_expansion_fill_session_probe_artifacts.py::test_fill_session_probe_aggregate_fill_and_session_counts",
  "tests/ultimate_book/test_market_expansion_fill_session_probe_artifacts.py::test_fill_session_probe_default_off_and_verifier_clean",
  "tests/ultimate_book/test_market_expansion_followup_replay_artifacts.py::test_followup_replay_denominator_and_boundaries",
  "tests/ultimate_book/test_market_expansion_followup_replay_artifacts.py::test_followup_replay_path_evidence_and_interaction_ledgers",
  "tests/ultimate_book/test_market_expansion_g12_review_artifacts.py::test_g12_review_acceptance_gates_concentration_and_handoff",
  "tests/ultimate_book/test_market_expansion_g12_review_artifacts.py::test_g12_review_denominator_decisions_and_boundaries",
  "tests/ultimate_book/test_market_expansion_live_authority_dossier_artifacts.py::test_live_authority_dossier_cost_session_and_fill_statuses",
  "tests/ultimate_book/test_market_expansion_live_authority_dossier_artifacts.py::test_live_authority_dossier_counts_boundaries_and_replay",
  "tests/ultimate_book/test_market_expansion_observed_session_fillability_repair_artifacts.py::test_observed_session_fillability_boundary_and_counts",
  "tests/ultimate_book/test_market_expansion_observed_session_fillability_repair_artifacts.py::test_observed_session_fillability_proxy_preserves_gaps",
  "tests/ultimate_book/test_market_expansion_promotion_boundary_artifacts.py::test_promotion_boundary_default_off_not_promoted",
  "tests/ultimate_book/test_market_expansion_promotion_boundary_artifacts.py::test_promotion_boundary_pretrade_packets_and_bridge_limits",
  "tests/ultimate_book/test_market_expansion_proxy_m1_repair_artifacts.py::test_proxy_m1_repair_candidate_decisions_are_row_level",
  "tests/ultimate_book/test_market_expansion_proxy_m1_repair_artifacts.py::test_proxy_m1_repair_result_boundaries_and_counts",
  "tests/ultimate_book/test_market_expansion_repaired_registry_integration_artifacts.py::test_repaired_registry_integration_counts_and_boundaries",
  "tests/ultimate_book/test_market_expansion_repaired_registry_integration_artifacts.py::test_repaired_registry_integration_preserves_row_level_repair_decisions",
  "tests/ultimate_book/test_market_expansion_runtime_generator.py::test_active_market_expansion_bridge_telemetry_exposes_reload_parity_flags",
  "tests/ultimate_book/test_market_expansion_runtime_generator_implementation_artifacts.py::test_runtime_generator_implementation_counts_and_boundaries",
  "tests/ultimate_book/test_market_expansion_runtime_generator_implementation_artifacts.py::test_runtime_generator_implementation_event_parity_and_execution_packets",
  "tests/ultimate_book/test_market_expansion_swap_adjusted_activation_rescore_artifacts.py::test_swap_adjusted_activation_boundary_and_counts",
  "tests/ultimate_book/test_market_expansion_swap_adjusted_activation_rescore_artifacts.py::test_swap_adjusted_activation_positive_but_not_overstated",
  "tests/ultimate_book/test_market_expansion_swap_mode5_holding_repair_artifacts.py::test_swap_mode5_holding_boundary_counts_and_sources",
  "tests/ultimate_book/test_market_expansion_swap_mode5_holding_repair_artifacts.py::test_swap_mode5_holding_proxy_preserves_live_gaps",
  "tests/ultimate_book/test_market_expansion_validation_scoring_artifacts.py::test_market_expansion_scoring_denominator_and_boundaries",
  "tests/ultimate_book/test_market_expansion_validation_scoring_artifacts.py::test_market_expansion_scoring_ledgers_and_promotion_gates",
  "tests/ultimate_book/test_rolling_stress_manifest_shadow_boundary.py::test_foundation_boundary_is_shadow_only_and_raw_payloads_are_cold",
  "tests/ultimate_book/test_rolling_stress_manifest_shadow_boundary.py::test_rolling_stress_manifest_seals_canonical_inputs",
  "tests/ultimate_book/test_wave_c_manifest_ohlcv_source.py::test_wave_c_manifest_source_get_candles_streams_bounded_window",
  "tests/ultimate_book/test_wave_c_manifest_ohlcv_source.py::test_wave_c_manifest_source_get_candles_streams_tail_without_full_materialization",
  "tests/ultimate_book/test_wave_c_manifest_ohlcv_source.py::test_wave_c_manifest_source_indexes_all_timeframes_and_aliases"
 ],
 "bad_after_nodeids": [
  "tests/ultimate_book/test_a8_live_activation_config.py::test_active_live_config_arms_a8_gate_with_smooth_ceiling_profile",
  "tests/ultimate_book/test_candidate_activation_readiness_artifacts.py::test_candidate_activation_readiness_artifact_boundary",
  "tests/ultimate_book/test_candidate_activation_readiness_artifacts.py::test_candidate_activation_readiness_preserves_repair_lanes",
  "tests/ultimate_book/test_candidate_bridge_spec_ltf_work_artifacts.py::test_candidate_bridge_route_closes_ltf_gap_without_mutation",
  "tests/ultimate_book/test_candidate_bridge_spec_ltf_work_artifacts.py::test_candidate_bridge_route_preserves_broker_specific_work_split",
  "tests/ultimate_book/test_candidate_enabled_replay_mc_artifacts.py::test_candidate_enabled_route_core_numbers_and_boundaries",
  "tests/ultimate_book/test_candidate_enabled_replay_mc_artifacts.py::test_candidate_enabled_route_ledgers_preserve_unfinished_and_ready_ideas",
  "tests/ultimate_book/test_candidate_full_book_live_activation_artifacts.py::test_full_candidate_book_live_activation_bridge_and_successor_lanes",
  "tests/ultimate_book/test_candidate_full_book_live_activation_artifacts.py::test_full_candidate_book_live_activation_result_and_numbers",
  "tests/ultimate_book/test_candidate_natgas_decomposition_artifacts.py::test_natgas_decomposition_preserves_ex_natgas_sleeve",
  "tests/ultimate_book/test_candidate_natgas_decomposition_artifacts.py::test_natgas_decomposition_writes_bridge_and_daily_artifacts",
  "tests/ultimate_book/test_candidate_subset_routing_dossier_artifacts.py::test_candidate_subset_routing_dossier_result_and_boundaries",
  "tests/ultimate_book/test_candidate_subset_routing_dossier_artifacts.py::test_candidate_subset_routing_ledger_preserves_full_book_work",
  "tests/ultimate_book/test_market_expansion_activation_candidate_package_artifacts.py::test_activation_candidate_package_counts_and_boundaries",
  "tests/ultimate_book/test_market_expansion_activation_candidate_package_artifacts.py::test_activation_candidate_package_row_controls_and_generator_contracts",
  "tests/ultimate_book/test_market_expansion_activation_readiness_synthesis_artifacts.py::test_activation_readiness_synthesis_authority_detail_preserved",
  "tests/ultimate_book/test_market_expansion_activation_readiness_synthesis_artifacts.py::test_activation_readiness_synthesis_boundary_and_counts",
  "tests/ultimate_book/test_market_expansion_broker_authority_probe_artifacts.py::test_broker_authority_probe_default_off_and_verifier_clean",
  "tests/ultimate_book/test_market_expansion_broker_authority_probe_artifacts.py::test_broker_authority_probe_readonly_evidence_counts",
  "tests/ultimate_book/test_market_expansion_commission_family_transfer_artifacts.py::test_commission_family_transfer_counts_and_no_schedule_overclaim",
  "tests/ultimate_book/test_market_expansion_commission_family_transfer_artifacts.py::test_commission_family_transfer_default_off_and_verifier_clean",
  "tests/ultimate_book/test_market_expansion_conditioned_sizing_refinement_artifacts.py::test_conditioned_sizing_boundary_and_counts",
  "tests/ultimate_book/test_market_expansion_conditioned_sizing_refinement_artifacts.py::test_conditioned_sizing_improves_but_remains_default_off",
  "tests/ultimate_book/test_market_expansion_data_availability_artifacts.py::test_market_expansion_gap_commands_and_inspire_not_kill_rows",
  "tests/ultimate_book/test_market_expansion_data_availability_artifacts.py::test_market_expansion_inventory_and_boundaries",
  "tests/ultimate_book/test_market_expansion_default_off_design_artifacts.py::test_default_off_design_denominator_and_boundaries",
  "tests/ultimate_book/test_market_expansion_default_off_design_artifacts.py::test_default_off_design_risk_budget_and_repair_gates",
  "tests/ultimate_book/test_market_expansion_default_off_registry_artifacts.py::test_default_off_registry_artifacts_match_design_ledger_fields",
  "tests/ultimate_book/test_market_expansion_default_off_registry_artifacts.py::test_default_off_registry_artifacts_preserve_design_and_boundaries",
  "tests/ultimate_book/test_market_expansion_fill_session_probe_artifacts.py::test_fill_session_probe_aggregate_fill_and_session_counts",
  "tests/ultimate_book/test_market_expansion_fill_session_probe_artifacts.py::test_fill_session_probe_default_off_and_verifier_clean",
  "tests/ultimate_book/test_market_expansion_followup_replay_artifacts.py::test_followup_replay_denominator_and_boundaries",
  "tests/ultimate_book/test_market_expansion_followup_replay_artifacts.py::test_followup_replay_path_evidence_and_interaction_ledgers",
  "tests/ultimate_book/test_market_expansion_g12_review_artifacts.py::test_g12_review_acceptance_gates_concentration_and_handoff",
  "tests/ultimate_book/test_market_expansion_g12_review_artifacts.py::test_g12_review_denominator_decisions_and_boundaries",
  "tests/ultimate_book/test_market_expansion_live_authority_dossier_artifacts.py::test_live_authority_dossier_cost_session_and_fill_statuses",
  "tests/ultimate_book/test_market_expansion_live_authority_dossier_artifacts.py::test_live_authority_dossier_counts_boundaries_and_replay",
  "tests/ultimate_book/test_market_expansion_observed_session_fillability_repair_artifacts.py::test_observed_session_fillability_boundary_and_counts",
  "tests/ultimate_book/test_market_expansion_observed_session_fillability_repair_artifacts.py::test_observed_session_fillability_proxy_preserves_gaps",
  "tests/ultimate_book/test_market_expansion_promotion_boundary_artifacts.py::test_promotion_boundary_default_off_not_promoted",
  "tests/ultimate_book/test_market_expansion_promotion_boundary_artifacts.py::test_promotion_boundary_pretrade_packets_and_bridge_limits",
  "tests/ultimate_book/test_market_expansion_proxy_m1_repair_artifacts.py::test_proxy_m1_repair_candidate_decisions_are_row_level",
  "tests/ultimate_book/test_market_expansion_proxy_m1_repair_artifacts.py::test_proxy_m1_repair_result_boundaries_and_counts",
  "tests/ultimate_book/test_market_expansion_repaired_registry_integration_artifacts.py::test_repaired_registry_integration_counts_and_boundaries",
  "tests/ultimate_book/test_market_expansion_repaired_registry_integration_artifacts.py::test_repaired_registry_integration_preserves_row_level_repair_decisions",
  "tests/ultimate_book/test_market_expansion_runtime_generator.py::test_active_market_expansion_bridge_telemetry_exposes_reload_parity_flags",
  "tests/ultimate_book/test_market_expansion_runtime_generator_implementation_artifacts.py::test_runtime_generator_implementation_counts_and_boundaries",
  "tests/ultimate_book/test_market_expansion_runtime_generator_implementation_artifacts.py::test_runtime_generator_implementation_event_parity_and_execution_packets",
  "tests/ultimate_book/test_market_expansion_swap_adjusted_activation_rescore_artifacts.py::test_swap_adjusted_activation_boundary_and_counts",
  "tests/ultimate_book/test_market_expansion_swap_adjusted_activation_rescore_artifacts.py::test_swap_adjusted_activation_positive_but_not_overstated",
  "tests/ultimate_book/test_market_expansion_swap_mode5_holding_repair_artifacts.py::test_swap_mode5_holding_boundary_counts_and_sources",
  "tests/ultimate_book/test_market_expansion_swap_mode5_holding_repair_artifacts.py::test_swap_mode5_holding_proxy_preserves_live_gaps",
  "tests/ultimate_book/test_market_expansion_validation_scoring_artifacts.py::test_market_expansion_scoring_denominator_and_boundaries",
  "tests/ultimate_book/test_market_expansion_validation_scoring_artifacts.py::test_market_expansion_scoring_ledgers_and_promotion_gates",
  "tests/ultimate_book/test_rolling_stress_manifest_shadow_boundary.py::test_foundation_boundary_is_shadow_only_and_raw_payloads_are_cold",
  "tests/ultimate_book/test_rolling_stress_manifest_shadow_boundary.py::test_rolling_stress_manifest_seals_canonical_inputs",
  "tests/ultimate_book/test_wave_c_manifest_ohlcv_source.py::test_wave_c_manifest_source_get_candles_streams_bounded_window",
  "tests/ultimate_book/test_wave_c_manifest_ohlcv_source.py::test_wave_c_manifest_source_get_candles_streams_tail_without_full_materialization",
  "tests/ultimate_book/test_wave_c_manifest_ohlcv_source.py::test_wave_c_manifest_source_indexes_all_timeframes_and_aliases"
 ]
}
```
