# Session CO — scoped A/B vs the 12,600-pass ZERO baseline

**0 bad → 0 bad · 0 fixed · 0 regressed. No regressions.**

Compared by **failure set**, not by count — counts are not portable across worktrees.

| | before | after |
|---|---|---|
| commit | `6608eb969` | `cb9094477` |
| captured (UTC) | 2026-07-31T17:26:48Z | 2026-07-31T18:51:36Z |
| working tree | dirty | dirty |
| failed | 0 | 0 |
| errored | 0 | 0 |
| **bad** | **0** | **0** |
| passed | 12600 | 920 |
| skipped | 120 | 2 |

## Scope difference — declared, not hidden

- before: `['tests/']`
- after : `['tests/research_infra/test_ar_vol_level_tilt.py', 'tests/research_infra/test_av_timebase_per_file.py', 'tests/research_infra/test_ci_thirdparty_m1.py', 'tests/research_infra/test_regime_spine_conditions.py', 'tests/research_infra/test_walkforward_book_replay.py', 'tests/research_infra/test_wf_registry_surface_reconciliation.py', 'tests/safety/test_activation_token_attacks.py', 'tests/scripts/test_pytest_failset_parsing.py', 'tests/test_implementation_state_block_citations.py', 'tests/test_replay_policy_generation.py', 'tests/test_run_book_importable.py', 'tests/ultimate_book/test_activation_carry_vps_lineage.py', 'tests/ultimate_book/test_az_activation_carry_mx.py', 'tests/ultimate_book/test_ba_weekend_policy.py', 'tests/ultimate_book/test_bar_time_repair_and_safety_flags.py', 'tests/ultimate_book/test_book_engine.py', 'tests/ultimate_book/test_book_owner.py', 'tests/ultimate_book/test_book_sleeve_telemetry.py', 'tests/ultimate_book/test_breach_flatten.py', 'tests/ultimate_book/test_candidate_promotion_plumbing.py', 'tests/ultimate_book/test_ce_entry_hour_lever.py', 'tests/ultimate_book/test_convergence_replay_record.py', 'tests/ultimate_book/test_defect_register_repairs.py', 'tests/ultimate_book/test_frontier_exit_contracts.py', 'tests/ultimate_book/test_generator_contract.py', 'tests/ultimate_book/test_governor_baseline.py', 'tests/ultimate_book/test_lane_weights.py', 'tests/ultimate_book/test_market_expansion_runtime_generator.py', 'tests/ultimate_book/test_packet_carry_vps_lineage.py', 'tests/ultimate_book/test_packet_emit_on_change.py', 'tests/ultimate_book/test_packet_emitter_hardening.py', 'tests/ultimate_book/test_packet_modelled_cost.py', 'tests/ultimate_book/test_packet_unit_join_key.py', 'tests/ultimate_book/test_pre_gap_bar_wiring.py', 'tests/ultimate_book/test_running_conviction.py', 'tests/ultimate_book/test_runtime_learning_packet.py', 'tests/ultimate_book/test_spread_geometry_floor.py', 'tests/ultimate_book/test_stress_derisk.py', 'tests/ultimate_book/test_symbol_map.py', 'tests/ultimate_book/test_symbol_rename_adoption_gap.py', 'tests/ultimate_book/test_time_stop_rehydration.py', 'tests/ultimate_book/test_time_stop_window_coverage.py']`

**Why this is still a comparison:** Before is the committed whole-suite ZERO baseline: 12,600 passed and 0 bad at 6608eb969. After is the tool-derived 42-file import/path closure of the exact Session CO diff from base 83867e65f through findings and range-retirement commit cb9094477: 920 passed, 2 skipped, 1 xfailed, and 0 bad. Because the before side has zero failures and zero collection errors suite-wide, any bad test in the after scope is a regression. The after dirty flag comprises only the tool-emitted SCOPE capture already present before pytest and the AFTER output path itself; all Session CO source, tests, runtime receipts, signed carry, findings, implementation blocks, and range retirement under comparison were committed before capture.

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
  "commit": "cb90944772a006c7e3827745035baafe846344e6",
  "commit_subject": "phase17 CO: record bounded lane findings",
  "captured_utc": "2026-07-31T18:51:36Z",
  "dirty": true,
  "totals": {
   "passed": 920,
   "skipped": 2,
   "xfailed": 1
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
   "tests/research_infra/test_ar_vol_level_tilt.py",
   "tests/research_infra/test_av_timebase_per_file.py",
   "tests/research_infra/test_ci_thirdparty_m1.py",
   "tests/research_infra/test_regime_spine_conditions.py",
   "tests/research_infra/test_walkforward_book_replay.py",
   "tests/research_infra/test_wf_registry_surface_reconciliation.py",
   "tests/safety/test_activation_token_attacks.py",
   "tests/scripts/test_pytest_failset_parsing.py",
   "tests/test_implementation_state_block_citations.py",
   "tests/test_replay_policy_generation.py",
   "tests/test_run_book_importable.py",
   "tests/ultimate_book/test_activation_carry_vps_lineage.py",
   "tests/ultimate_book/test_az_activation_carry_mx.py",
   "tests/ultimate_book/test_ba_weekend_policy.py",
   "tests/ultimate_book/test_bar_time_repair_and_safety_flags.py",
   "tests/ultimate_book/test_book_engine.py",
   "tests/ultimate_book/test_book_owner.py",
   "tests/ultimate_book/test_book_sleeve_telemetry.py",
   "tests/ultimate_book/test_breach_flatten.py",
   "tests/ultimate_book/test_candidate_promotion_plumbing.py",
   "tests/ultimate_book/test_ce_entry_hour_lever.py",
   "tests/ultimate_book/test_convergence_replay_record.py",
   "tests/ultimate_book/test_defect_register_repairs.py",
   "tests/ultimate_book/test_frontier_exit_contracts.py",
   "tests/ultimate_book/test_generator_contract.py",
   "tests/ultimate_book/test_governor_baseline.py",
   "tests/ultimate_book/test_lane_weights.py",
   "tests/ultimate_book/test_market_expansion_runtime_generator.py",
   "tests/ultimate_book/test_packet_carry_vps_lineage.py",
   "tests/ultimate_book/test_packet_emit_on_change.py",
   "tests/ultimate_book/test_packet_emitter_hardening.py",
   "tests/ultimate_book/test_packet_modelled_cost.py",
   "tests/ultimate_book/test_packet_unit_join_key.py",
   "tests/ultimate_book/test_pre_gap_bar_wiring.py",
   "tests/ultimate_book/test_running_conviction.py",
   "tests/ultimate_book/test_runtime_learning_packet.py",
   "tests/ultimate_book/test_spread_geometry_floor.py",
   "tests/ultimate_book/test_stress_derisk.py",
   "tests/ultimate_book/test_symbol_map.py",
   "tests/ultimate_book/test_symbol_rename_adoption_gap.py",
   "tests/ultimate_book/test_time_stop_rehydration.py",
   "tests/ultimate_book/test_time_stop_window_coverage.py"
  ],
  "justification": "Before is the committed whole-suite ZERO baseline: 12,600 passed and 0 bad at 6608eb969. After is the tool-derived 42-file import/path closure of the exact Session CO diff from base 83867e65f through findings and range-retirement commit cb9094477: 920 passed, 2 skipped, 1 xfailed, and 0 bad. Because the before side has zero failures and zero collection errors suite-wide, any bad test in the after scope is a regression. The after dirty flag comprises only the tool-emitted SCOPE capture already present before pytest and the AFTER output path itself; all Session CO source, tests, runtime receipts, signed carry, findings, implementation blocks, and range retirement under comparison were committed before capture."
 }
}
```
