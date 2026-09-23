# Session P — A/B by failure set

**Scope: `tests/ultimate_book` (588 tests collected). NOT repo-wide.**

Two other sessions were live (O integrating six branches, N finishing the Stage 1.2 re-cost) and
memory is the binding constraint on this machine — five concurrent full suites last wave left
108 MB free of 16 GB and silently killed captures. Scoping to the directory this carry touches was
the deliberate trade. **No repo-wide "no regressions" claim is made.**

| | commit | bad |
|---|---|---|
| before | `df2baf060` (worktree base, stashed) | **60** |
| after | `HEAD` (post-refuter) | **60** |

```
unchanged: 60   fixed: 0   REGRESSED: 0
No regressions.
```

**Passing: 481 → 536 (+55).** Sets, not counts — see `session_p_ab/diff.txt`.

## The first A/B was not clean, and that is the point of running it

The initial capture showed **2 REGRESSED**, both genuine and both mine:

1. `test_runtime_learning_batch_preserves_valid_packets_when_one_packet_is_invalid` — I had
   renamed the cycle-summary key `packet_write_error_count`. It has a **live consumer** at
   `src/components/ai_companion/supervisor.py:517,539-540`, so the rename would have silently
   degraded the AI companion's view of packet health without failing anything. Both keys restored.
2. `test_runtime_learning_fallback_dedupe_retries_duplicate_after_transient_append_failure` — the
   guard was built in `__init__`, so tooling that replaces `owner._runtime_learning_writer` no
   longer governed where packets landed. Guard is now built per call. Fixing this also surfaced two
   real defects in my fallback: it did not tolerate a writer returning `None` on success, and it did
   not deduplicate by packet hash — so a transient batch failure would have **doubled every packet
   in the cycle**.

One test was then **deliberately amended**, and the reason is recorded in the test body:
`test_runtime_learning_batch_preserves_valid_packets_when_one_packet_is_invalid` asserted that a
refused packet leaves **no trace** in the main log. That is the false-green behaviour this session
exists to remove. It now asserts the `packet_rejected` marker and the quarantine sidecar instead.

## Known-flaky

None observed. The 60 unchanged failures are the pre-existing set at the worktree base.

---

*Embedded block added post-hoc by the orchestrator. The prose above is Session P's and is
unchanged — including its honest statement that this run is scoped, not repo-wide. The block
below is regenerated from P's own committed captures in `session_p_ab/` and reproduces its
claim exactly (60 → 60 bad, 0 regressed). A repo-wide A/B now also exists:
`SESSION_P_REPOWIDE_AB.md`.*

## Embedded captures

Embedded, not referenced. A receipt that points at a scratchpad path is as unverifiable as
no receipt at all, because that file is gone by the time anyone reads this.

```json
{
 "schema": "gtos-ab-receipt-v1",
 "scope": [
  "tests/ultimate_book"
 ],
 "before": {
  "commit": "df2baf0606c8c379a3a7aae4fddb3e22c48dd035",
  "commit_subject": "Wave 3 / Session N prompt: record the sparse-checkout trap",
  "captured_utc": "2026-07-28T14:53:07Z",
  "dirty": false,
  "totals": {
   "failed": 60,
   "passed": 481
  }
 },
 "after": {
  "commit": "5ffef1a7fff02b1cb1451a858b315374accd045a",
  "commit_subject": "Stage 3: refresh the A/B after the hour-snap change -- 60 bad -> 60 bad, 0 regressed, +50 passing",
  "captured_utc": "2026-07-28T15:33:41Z",
  "dirty": true,
  "totals": {
   "failed": 60,
   "passed": 536
  }
 },
 "bad_before": 60,
 "bad_after": 60,
 "unchanged": 60,
 "fixed": [],
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
 ]
}
```

