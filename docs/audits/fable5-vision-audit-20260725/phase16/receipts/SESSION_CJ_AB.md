# Session CJ scoped A/B

**0 bad → 0 bad · 0 fixed · 0 regressed. No regressions.**

Compared by **failure set**, not by count — counts are not portable across worktrees.

| | before | after |
|---|---|---|
| commit | `dbdead310` | `f298d7aac` |
| captured (UTC) | 2026-07-31T12:31:50Z | 2026-07-31T18:54:01Z |
| working tree | dirty | dirty |
| failed | 0 | 0 |
| errored | 0 | 0 |
| **bad** | **0** | **0** |
| passed | 1914 | 1933 |
| skipped | 7 | 7 |

## Embedded captures

Embedded, not referenced. A receipt that points at a scratchpad path is as unverifiable as
no receipt at all, because that file is gone by the time anyone reads this.

```json
{
 "schema": "gtos-ab-receipt-v1",
 "scope": [
  "tests/research_infra"
 ],
 "before": {
  "commit": "dbdead310bd514c68e9841745362477e52aea68e",
  "commit_subject": "Wave-14b train: zero -> zero, 12,522 (+46) \u2014 and wave 16 commissioned on the owner's seal break (CJ re-materialization, CK mechanism autopsy)",
  "captured_utc": "2026-07-31T12:31:50Z",
  "dirty": true,
  "totals": {
   "passed": 1914,
   "skipped": 7
  }
 },
 "after": {
  "commit": "f298d7aac644fc4826d5c5bb3446002849cc70af",
  "commit_subject": "phase16: measure true-UTC January economics",
  "captured_utc": "2026-07-31T18:54:01Z",
  "dirty": true,
  "totals": {
   "passed": 1933,
   "skipped": 7
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
