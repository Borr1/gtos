# Session FG Sol repair integration A/B

**1 bad → 0 bad · 1 fixed · 0 regressed. No regressions.**

Compared by **failure set**, not by count — counts are not portable across worktrees.

| | before | after |
|---|---|---|
| commit | `bca8c4466` | `fcc9782e3` |
| captured (UTC) | 2026-07-31T23:43:36Z | 2026-08-01T05:23:52Z |
| working tree | dirty | dirty |
| failed | 1 | 0 |
| errored | 0 | 0 |
| **bad** | **1** | **0** |
| passed | 12705 | 736 |
| skipped | 120 | 1 |

## Fixed (1)

- `tests/research_infra/test_train_engine_cuts.py::test_exact_content_key_is_mapping_order_insensitive_and_type_strict`

## Scope difference — declared, not hidden

- before: `['tests/']`
- after : `['tests/costs/test_cost_artifact_absence_message.py', 'tests/research_infra/test_ao_candidate_family_v3.py', 'tests/research_infra/test_ao_p_floor_headroom.py', 'tests/research_infra/test_candidate_family.py', 'tests/research_infra/test_candidate_family_chain.py', 'tests/research_infra/test_candidate_family_v2_ratchet.py', 'tests/research_infra/test_cq_path_pool_grid.py', 'tests/research_infra/test_cr_ny_metals_capture.py', 'tests/research_infra/test_current_ob_retest_geometry_candidate.py', 'tests/research_infra/test_direct_fidelity_measurement.py', 'tests/research_infra/test_era_population.py', 'tests/research_infra/test_exit_overlay.py', 'tests/research_infra/test_fidelity_register_matches_receipt.py', 'tests/research_infra/test_fidelity_threshold_variant.py', 'tests/research_infra/test_gate_partial_universe_stamp.py', 'tests/research_infra/test_gate_wipeout_signal.py', 'tests/research_infra/test_lane_rematerialization.py', 'tests/research_infra/test_session_cs_breaker_folds.py', 'tests/research_infra/test_session_fb_sol_grid.py', 'tests/research_infra/test_session_fc_exit_overlay.py', 'tests/research_infra/test_session_fg_integration.py', 'tests/research_infra/test_sol_condition_instrumentation.py', 'tests/research_infra/test_sol_conditions.py', 'tests/research_infra/test_train_engine_cuts.py', 'tests/research_infra/test_train_engine_footprint.py', 'tests/research_infra/test_train_engine_lane.py', 'tests/research_infra/test_train_engine_resident_event_sink.py', 'tests/research_infra/test_trainer_folds.py', 'tests/research_infra/test_training_lane_protocol.py', 'tests/research_infra/test_walkforward_book_replay.py', 'tests/research_infra/test_walkforward_family.py', 'tests/research_infra/test_walkforward_gate.py', 'tests/research_infra/test_walkforward_supply.py', 'tests/research_infra/test_wave19_sol_decision_semantics.py', 'tests/research_infra/test_wf_diagnostics.py', 'tests/test_implementation_state_block_citations.py', 'tests/test_replay_acceleration_contract_split.py', 'tests/test_replay_acceleration_real_contract.py', 'tests/test_replay_acceleration_real_parity.py', 'tests/test_session_ck_mechanism_autopsy.py', 'tests/test_spread_composition.py', 'tests/ultimate_book/test_packet_carry_vps_lineage.py']`

**Why this is still a comparison:** The committed before is the parse-complete suite-wide wave-19 baseline. The after is the tool-derived 42-file closure of all 66 integrated source commits plus FG worktree changes; its closure already contains the registered intermittent failure carrier. Raw pass totals are not compared, and the baseline node passing after is not attributed to FG.

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
  "commit": "bca8c44667ff30f1b12ed46d207255db085977d8",
  "commit_subject": "Wave 19 commissioned: CR closes CP's capture contract, CS supplies CQ's two folds",
  "captured_utc": "2026-07-31T23:43:36Z",
  "dirty": true,
  "totals": {
   "failed": 1,
   "passed": 12705,
   "skipped": 120,
   "xfailed": 32
  }
 },
 "after": {
  "commit": "fcc9782e3e7af05a90174c8a367c5b5f77223195",
  "commit_subject": "FF: record Sol composition completion",
  "captured_utc": "2026-08-01T05:23:52Z",
  "dirty": true,
  "totals": {
   "passed": 736,
   "skipped": 1
  }
 },
 "bad_before": 1,
 "bad_after": 0,
 "unchanged": 0,
 "fixed": [
  "tests/research_infra/test_train_engine_cuts.py::test_exact_content_key_is_mapping_order_insensitive_and_type_strict"
 ],
 "regressed": [],
 "bad_before_nodeids": [
  "tests/research_infra/test_train_engine_cuts.py::test_exact_content_key_is_mapping_order_insensitive_and_type_strict"
 ],
 "bad_after_nodeids": [],
 "scope_difference": {
  "before": [
   "tests/"
  ],
  "after": [
   "tests/costs/test_cost_artifact_absence_message.py",
   "tests/research_infra/test_ao_candidate_family_v3.py",
   "tests/research_infra/test_ao_p_floor_headroom.py",
   "tests/research_infra/test_candidate_family.py",
   "tests/research_infra/test_candidate_family_chain.py",
   "tests/research_infra/test_candidate_family_v2_ratchet.py",
   "tests/research_infra/test_cq_path_pool_grid.py",
   "tests/research_infra/test_cr_ny_metals_capture.py",
   "tests/research_infra/test_current_ob_retest_geometry_candidate.py",
   "tests/research_infra/test_direct_fidelity_measurement.py",
   "tests/research_infra/test_era_population.py",
   "tests/research_infra/test_exit_overlay.py",
   "tests/research_infra/test_fidelity_register_matches_receipt.py",
   "tests/research_infra/test_fidelity_threshold_variant.py",
   "tests/research_infra/test_gate_partial_universe_stamp.py",
   "tests/research_infra/test_gate_wipeout_signal.py",
   "tests/research_infra/test_lane_rematerialization.py",
   "tests/research_infra/test_session_cs_breaker_folds.py",
   "tests/research_infra/test_session_fb_sol_grid.py",
   "tests/research_infra/test_session_fc_exit_overlay.py",
   "tests/research_infra/test_session_fg_integration.py",
   "tests/research_infra/test_sol_condition_instrumentation.py",
   "tests/research_infra/test_sol_conditions.py",
   "tests/research_infra/test_train_engine_cuts.py",
   "tests/research_infra/test_train_engine_footprint.py",
   "tests/research_infra/test_train_engine_lane.py",
   "tests/research_infra/test_train_engine_resident_event_sink.py",
   "tests/research_infra/test_trainer_folds.py",
   "tests/research_infra/test_training_lane_protocol.py",
   "tests/research_infra/test_walkforward_book_replay.py",
   "tests/research_infra/test_walkforward_family.py",
   "tests/research_infra/test_walkforward_gate.py",
   "tests/research_infra/test_walkforward_supply.py",
   "tests/research_infra/test_wave19_sol_decision_semantics.py",
   "tests/research_infra/test_wf_diagnostics.py",
   "tests/test_implementation_state_block_citations.py",
   "tests/test_replay_acceleration_contract_split.py",
   "tests/test_replay_acceleration_real_contract.py",
   "tests/test_replay_acceleration_real_parity.py",
   "tests/test_session_ck_mechanism_autopsy.py",
   "tests/test_spread_composition.py",
   "tests/ultimate_book/test_packet_carry_vps_lineage.py"
  ],
  "justification": "The committed before is the parse-complete suite-wide wave-19 baseline. The after is the tool-derived 42-file closure of all 66 integrated source commits plus FG worktree changes; its closure already contains the registered intermittent failure carrier. Raw pass totals are not compared, and the baseline node passing after is not attributed to FG."
 }
}
```
