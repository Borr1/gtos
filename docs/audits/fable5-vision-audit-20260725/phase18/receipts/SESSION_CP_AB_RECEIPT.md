# Session CP true-UTC factory scoped A/B

**0 bad → 0 bad · 0 fixed · 0 regressed. No regressions.**

Compared by **failure set**, not by count — counts are not portable across worktrees.

| | before | after |
|---|---|---|
| commit | `79d34a8d5` | `86b643be2` |
| captured (UTC) | 2026-07-31T20:15:59Z | 2026-07-31T22:53:20Z |
| working tree | dirty | dirty |
| failed | 0 | 0 |
| errored | 0 | 0 |
| **bad** | **0** | **0** |
| passed | 12671 | 142 |
| skipped | 120 | 0 |

## Scope difference — declared, not hidden

- before: `['tests/']`
- after : `['tests/research_infra/test_cp_b_time_regeneration.py', 'tests/research_infra/test_cp_february_first_read.py', 'tests/research_infra/test_cp_true_utc_candidate_factory.py', 'tests/research_infra/test_cp_true_utc_recorded_gate.py', 'tests/research_infra/test_lane_rematerialization.py', 'tests/research_infra/test_train_engine_lane.py', 'tests/test_implementation_state_block_citations.py', 'tests/test_replay_acceleration_contract_split.py', 'tests/test_replay_acceleration_real_contract.py', 'tests/test_replay_acceleration_real_parity.py']`

**Why this is still a comparison:** The committed baseline is the orchestrator-owned whole-suite ZERO capture; CP after is the tool-derived exact 30-path/10-test closure from the wave-18 merge base, as required by the commission. The orchestrator owns the next whole-suite train capture.

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
  "commit": "86b643be260af9dc39dc3a9762bb5a10ffe86f73",
  "commit_subject": "phase18: close true UTC factory findings",
  "captured_utc": "2026-07-31T22:53:20Z",
  "dirty": true,
  "totals": {
   "passed": 142
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
   "tests/research_infra/test_cp_b_time_regeneration.py",
   "tests/research_infra/test_cp_february_first_read.py",
   "tests/research_infra/test_cp_true_utc_candidate_factory.py",
   "tests/research_infra/test_cp_true_utc_recorded_gate.py",
   "tests/research_infra/test_lane_rematerialization.py",
   "tests/research_infra/test_train_engine_lane.py",
   "tests/test_implementation_state_block_citations.py",
   "tests/test_replay_acceleration_contract_split.py",
   "tests/test_replay_acceleration_real_contract.py",
   "tests/test_replay_acceleration_real_parity.py"
  ],
  "justification": "The committed baseline is the orchestrator-owned whole-suite ZERO capture; CP after is the tool-derived exact 30-path/10-test closure from the wave-18 merge base, as required by the commission. The orchestrator owns the next whole-suite train capture."
 }
}
```
