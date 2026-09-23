# Session FE scoped A/B: committed baseline to Sol condition repair

**1 bad → 0 bad · 1 fixed · 0 regressed. No regressions.**

Compared by **failure set**, not by count — counts are not portable across worktrees.

| | before | after |
|---|---|---|
| commit | `bca8c4466` | `a86976b14` |
| captured (UTC) | 2026-07-31T23:43:36Z | 2026-08-01T02:09:02Z |
| working tree | dirty | dirty |
| failed | 1 | 0 |
| errored | 0 | 0 |
| **bad** | **1** | **0** |
| passed | 12705 | 129 |
| skipped | 120 | 0 |

## Fixed (1)

- `tests/research_infra/test_train_engine_cuts.py::test_exact_content_key_is_mapping_order_insensitive_and_type_strict`

## Scope difference — declared, not hidden

- before: `['tests/']`
- after : `['tests/research_infra/test_sol_condition_instrumentation.py', 'tests/research_infra/test_sol_conditions.py', 'tests/research_infra/test_train_engine_cuts.py', 'tests/research_infra/test_train_engine_footprint.py', 'tests/research_infra/test_train_engine_lane.py', 'tests/research_infra/test_train_engine_resident_event_sink.py', 'tests/test_implementation_state_block_citations.py']`

**Why this is still a comparison:** The before capture is the mandated committed repository-wide baseline; the after capture is the tool-computed changed-path import closure from f8c05d0ac through HEAD plus FE's uncommitted final documentation and receipt paths. The baseline has no errored tests and only the registered order-sensitive load flake, while every test reached by FE's final diff is in the after scope.

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
  "commit": "a86976b148451d882b45ae4f77ebffcd7778cd1e",
  "commit_subject": "phase19: add default-off Sol condition telemetry",
  "captured_utc": "2026-08-01T02:09:02Z",
  "dirty": true,
  "totals": {
   "passed": 129
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
   "tests/research_infra/test_sol_condition_instrumentation.py",
   "tests/research_infra/test_sol_conditions.py",
   "tests/research_infra/test_train_engine_cuts.py",
   "tests/research_infra/test_train_engine_footprint.py",
   "tests/research_infra/test_train_engine_lane.py",
   "tests/research_infra/test_train_engine_resident_event_sink.py",
   "tests/test_implementation_state_block_citations.py"
  ],
  "justification": "The before capture is the mandated committed repository-wide baseline; the after capture is the tool-computed changed-path import closure from f8c05d0ac through HEAD plus FE's uncommitted final documentation and receipt paths. The baseline has no errored tests and only the registered order-sensitive load flake, while every test reached by FE's final diff is in the after scope."
 }
}
```
