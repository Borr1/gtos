# Failure-set A/B

**0 bad → 0 bad · 0 fixed · 0 regressed. No regressions.**

Compared by **failure set**, not by count — counts are not portable across worktrees.

| | before | after |
|---|---|---|
| commit | `fcb4fe5e7` | `fcb4fe5e7` |
| captured (UTC) | 2026-07-31T07:54:38Z | 2026-07-31T07:56:54Z |
| working tree | dirty | clean |
| failed | 0 | 0 |
| errored | 0 | 0 |
| **bad** | **0** | **0** |
| passed | 846 | 846 |
| skipped | 0 | 0 |

## Embedded captures

Embedded, not referenced. A receipt that points at a scratchpad path is as unverifiable as
no receipt at all, because that file is gone by the time anyone reads this.

```json
{
 "schema": "gtos-ab-receipt-v1",
 "scope": [
  "tests/research_infra/test_ar_vol_level_tilt.py",
  "tests/research_infra/test_av_timebase_per_file.py",
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
  "tests/ultimate_book/test_defect_register_repairs.py",
  "tests/ultimate_book/test_frontier_exit_contracts.py",
  "tests/ultimate_book/test_generator_contract.py",
  "tests/ultimate_book/test_governor_baseline.py",
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
  "tests/ultimate_book/test_time_stop_rehydration.py",
  "tests/ultimate_book/test_time_stop_window_coverage.py"
 ],
 "before": {
  "commit": "fcb4fe5e7ea7d1944f43247ae8a8a95a61491875",
  "commit_subject": "CE blocks B2300-B2340 + the in-flight range table, corrected in place",
  "captured_utc": "2026-07-31T07:54:38Z",
  "dirty": true,
  "totals": {
   "passed": 846,
   "xfailed": 1
  }
 },
 "after": {
  "commit": "fcb4fe5e7ea7d1944f43247ae8a8a95a61491875",
  "commit_subject": "CE blocks B2300-B2340 + the in-flight range table, corrected in place",
  "captured_utc": "2026-07-31T07:56:54Z",
  "dirty": false,
  "totals": {
   "passed": 846,
   "xfailed": 1
  }
 },
 "bad_before": 0,
 "bad_after": 0,
 "unchanged": 0,
 "fixed": [],
 "regressed": [],
 "bad_before_nodeids": [],
 "bad_after_nodeids": []
}
```
