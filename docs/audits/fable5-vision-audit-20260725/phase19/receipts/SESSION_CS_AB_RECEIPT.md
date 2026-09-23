# Session CS scoped A/B receipt

**1 bad → 1 bad · 0 fixed · 0 regressed. No regressions.**

Compared by **failure set**, not by count — counts are not portable across worktrees.

| | before | after |
|---|---|---|
| commit | `bca8c4466` | `6a42060e4` |
| captured (UTC) | 2026-07-31T23:43:36Z | 2026-08-01T04:22:10Z |
| working tree | dirty | dirty |
| failed | 1 | 1 |
| errored | 0 | 0 |
| **bad** | **1** | **1** |
| passed | 12705 | 583 |
| skipped | 120 | 1 |

## Scope difference — declared, not hidden

- before: `['tests/']`
- after : `['tests/costs/test_cost_artifact_absence_message.py', 'tests/research_infra/test_ao_candidate_family_v3.py', 'tests/research_infra/test_ao_p_floor_headroom.py', 'tests/research_infra/test_candidate_family.py', 'tests/research_infra/test_candidate_family_chain.py', 'tests/research_infra/test_candidate_family_v2_ratchet.py', 'tests/research_infra/test_era_population.py', 'tests/research_infra/test_fidelity_threshold_variant.py', 'tests/research_infra/test_gate_partial_universe_stamp.py', 'tests/research_infra/test_gate_wipeout_signal.py', 'tests/research_infra/test_lane_rematerialization.py', 'tests/research_infra/test_session_cs_breaker_folds.py', 'tests/research_infra/test_train_engine_cuts.py', 'tests/research_infra/test_train_engine_lane.py', 'tests/research_infra/test_trainer_folds.py', 'tests/research_infra/test_training_lane_protocol.py', 'tests/research_infra/test_walkforward_book_replay.py', 'tests/research_infra/test_walkforward_family.py', 'tests/research_infra/test_walkforward_gate.py', 'tests/research_infra/test_walkforward_supply.py', 'tests/research_infra/test_wf_diagnostics.py', 'tests/test_implementation_state_block_citations.py', 'tests/test_replay_acceleration_contract_split.py', 'tests/test_replay_acceleration_real_contract.py', 'tests/test_replay_acceleration_real_parity.py', 'tests/test_session_ck_mechanism_autopsy.py', 'tests/test_spread_composition.py']`

**Why this is still a comparison:** The committed before capture is the parse-complete suite-wide standing baseline at commissioned main; the after capture uses the tool-derived changed-path import closure plus the baseline's one failing nodeid, so every standing bad identity and the complete Session-CS blast radius are present while avoiding an unnecessary suite-wide rerun.

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
  "commit": "6a42060e41890b9f0ddbe8f0d45e454cf0fef457",
  "commit_subject": "evidence(phase19): decide ratified breaker gate",
  "captured_utc": "2026-08-01T04:22:10Z",
  "dirty": true,
  "totals": {
   "failed": 1,
   "passed": 583,
   "skipped": 1
  }
 },
 "bad_before": 1,
 "bad_after": 1,
 "unchanged": 1,
 "fixed": [],
 "regressed": [],
 "bad_before_nodeids": [
  "tests/research_infra/test_train_engine_cuts.py::test_exact_content_key_is_mapping_order_insensitive_and_type_strict"
 ],
 "bad_after_nodeids": [
  "tests/research_infra/test_train_engine_cuts.py::test_exact_content_key_is_mapping_order_insensitive_and_type_strict"
 ],
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
   "tests/research_infra/test_era_population.py",
   "tests/research_infra/test_fidelity_threshold_variant.py",
   "tests/research_infra/test_gate_partial_universe_stamp.py",
   "tests/research_infra/test_gate_wipeout_signal.py",
   "tests/research_infra/test_lane_rematerialization.py",
   "tests/research_infra/test_session_cs_breaker_folds.py",
   "tests/research_infra/test_train_engine_cuts.py",
   "tests/research_infra/test_train_engine_lane.py",
   "tests/research_infra/test_trainer_folds.py",
   "tests/research_infra/test_training_lane_protocol.py",
   "tests/research_infra/test_walkforward_book_replay.py",
   "tests/research_infra/test_walkforward_family.py",
   "tests/research_infra/test_walkforward_gate.py",
   "tests/research_infra/test_walkforward_supply.py",
   "tests/research_infra/test_wf_diagnostics.py",
   "tests/test_implementation_state_block_citations.py",
   "tests/test_replay_acceleration_contract_split.py",
   "tests/test_replay_acceleration_real_contract.py",
   "tests/test_replay_acceleration_real_parity.py",
   "tests/test_session_ck_mechanism_autopsy.py",
   "tests/test_spread_composition.py"
  ],
  "justification": "The committed before capture is the parse-complete suite-wide standing baseline at commissioned main; the after capture uses the tool-derived changed-path import closure plus the baseline's one failing nodeid, so every standing bad identity and the complete Session-CS blast radius are present while avoiding an unnecessary suite-wide rerun."
 }
}
```
