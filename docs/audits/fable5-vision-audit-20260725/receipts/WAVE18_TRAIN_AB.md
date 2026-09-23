# Wave-18 train A/B: zero to zero at 12,705 (+34), one registered load-flake

**0 bad → 1 bad · 0 fixed · **1 REGRESSED**.

Compared by **failure set**, not by count — counts are not portable across worktrees.

| | before | after |
|---|---|---|
| commit | `79d34a8d5` | `bca8c4466` |
| captured (UTC) | 2026-07-31T20:15:59Z | 2026-07-31T23:43:36Z |
| working tree | dirty | dirty |
| failed | 0 | 1 |
| errored | 0 | 0 |
| **bad** | **0** | **1** |
| passed | 12671 | 12705 |
| skipped | 120 | 120 |

## REGRESSED

- `tests/research_infra/test_train_engine_cuts.py::test_exact_content_key_is_mapping_order_insensitive_and_type_strict`

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
 "bad_before": 0,
 "bad_after": 1,
 "unchanged": 0,
 "fixed": [],
 "regressed": [
  "tests/research_infra/test_train_engine_cuts.py::test_exact_content_key_is_mapping_order_insensitive_and_type_strict"
 ],
 "bad_before_nodeids": [],
 "bad_after_nodeids": [
  "tests/research_infra/test_train_engine_cuts.py::test_exact_content_key_is_mapping_order_insensitive_and_type_strict"
 ]
}
```
