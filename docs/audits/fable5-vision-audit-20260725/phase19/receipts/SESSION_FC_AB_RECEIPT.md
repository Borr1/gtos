# Session FC scoped A/B receipt

**1 bad → 0 bad · 1 fixed · 0 regressed. No regressions.**

The reported “fixed” node is the registered pre-existing mapping-order test
carried into the scope from the standing baseline. FC did not modify that test
or its implementation, and the same node failed in an earlier FC scoped run;
its pass here is a known intermittent outcome, not an FC repair claim. The
material A/B conclusion is **0 regressed failure IDs** across every FC-reachable
test plus the standing-failure carrier.

Compared by **failure set**, not by count — counts are not portable across worktrees.

| | before | after |
|---|---|---|
| commit | `bca8c4466` | `e5f995744` |
| captured (UTC) | 2026-07-31T23:43:36Z | 2026-08-01T04:40:24Z |
| working tree | dirty | dirty |
| failed | 1 | 0 |
| errored | 0 | 0 |
| **bad** | **1** | **0** |
| passed | 12705 | 78 |
| skipped | 120 | 0 |

## Fixed (1)

- `tests/research_infra/test_train_engine_cuts.py::test_exact_content_key_is_mapping_order_insensitive_and_type_strict`

## Scope difference — declared, not hidden

- before: `['tests/']`
- after : `['tests/research_infra/test_exit_overlay.py', 'tests/research_infra/test_session_fc_exit_overlay.py', 'tests/research_infra/test_train_engine_cuts.py', 'tests/test_implementation_state_block_citations.py']`

**Why this is still a comparison:** The before capture is the committed suite-wide standing baseline at bca8c4466 (an ancestor of FC's parent f8c05d0ac) and the after capture is the pytest_failset-derived FC blast radius from that parent through HEAD, unioned with the exact standing-failure carrier. Every FC-reachable test and the only registered baseline failure ID are therefore observed after the change; unrelated passing tests omitted from the after scope cannot hide a new failure-set regression.

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
  "commit": "e5f995744afbc71e71bb7d164cd5a9094938fdb5",
  "commit_subject": "docs: close FC verification record",
  "captured_utc": "2026-08-01T04:40:24Z",
  "dirty": true,
  "totals": {
   "passed": 78
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
   "tests/research_infra/test_exit_overlay.py",
   "tests/research_infra/test_session_fc_exit_overlay.py",
   "tests/research_infra/test_train_engine_cuts.py",
   "tests/test_implementation_state_block_citations.py"
  ],
  "justification": "The before capture is the committed suite-wide standing baseline at bca8c4466 (an ancestor of FC's parent f8c05d0ac) and the after capture is the pytest_failset-derived FC blast radius from that parent through HEAD, unioned with the exact standing-failure carrier. Every FC-reachable test and the only registered baseline failure ID are therefore observed after the change; unrelated passing tests omitted from the after scope cannot hide a new failure-set regression."
 }
}
```
