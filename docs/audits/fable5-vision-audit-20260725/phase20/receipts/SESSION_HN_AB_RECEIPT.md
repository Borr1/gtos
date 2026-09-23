# Session HN P1 upstream reconstruction A/B

`execution_authority: false`

`activation_authority: false`

`result_bearing_science_executed: false`

`result_use_status: SOURCE_CONTROL_ONLY_NO_OUTCOME_READ`

**1 bad → 0 bad · 1 fixed · 0 regressed. No regressions.**

Compared by **failure set**, not by count — counts are not portable across worktrees.

| | before | after |
|---|---|---|
| commit | `1c81f5cd3` | `f59fbb829` |
| captured (UTC) | 2026-08-01T22:03:33Z | 2026-08-01T22:03:34Z |
| working tree | dirty | dirty |
| failed | 0 | 0 |
| errored | 1 | 0 |
| **bad** | **1** | **0** |
| passed | 0 | 15 |
| skipped | 0 | 0 |

## Fixed (1)

- `tests/research_infra/test_p1_upstream_reconstruction.py`

## Embedded captures

Embedded, not referenced. A receipt that points at a scratchpad path is as unverifiable as
no receipt at all, because that file is gone by the time anyone reads this.

```json
{
 "schema": "gtos-ab-receipt-v1",
 "scope": [
  "--noconftest",
  "tests/research_infra/test_p1_upstream_reconstruction.py"
 ],
 "before": {
  "commit": "1c81f5cd384671a4a99ddcda49f9dfc6ef7bae51",
  "commit_subject": "phase20: harden P1 adapter under HM falsification",
  "captured_utc": "2026-08-01T22:03:33Z",
  "dirty": true,
  "totals": {
   "error": 1
  }
 },
 "after": {
  "commit": "f59fbb829a5561b7e7b78bed324d67a8c01d6e74",
  "commit_subject": "phase20: reconstruct P1 upstream source packet",
  "captured_utc": "2026-08-01T22:03:34Z",
  "dirty": true,
  "totals": {
   "passed": 15
  }
 },
 "bad_before": 1,
 "bad_after": 0,
 "unchanged": 0,
 "fixed": [
  "tests/research_infra/test_p1_upstream_reconstruction.py"
 ],
 "regressed": [],
 "bad_before_nodeids": [
  "tests/research_infra/test_p1_upstream_reconstruction.py"
 ],
 "bad_after_nodeids": []
}
```
