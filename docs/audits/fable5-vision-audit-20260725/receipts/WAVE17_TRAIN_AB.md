# Wave-17+CJ train A/B: zero to zero at 12,671 (+71)

**0 bad → 0 bad · 0 fixed · 0 regressed. No regressions.**

Compared by **failure set**, not by count — counts are not portable across worktrees.

| | before | after |
|---|---|---|
| commit | `6608eb969` | `79d34a8d5` |
| captured (UTC) | 2026-07-31T17:26:48Z | 2026-07-31T20:15:59Z |
| working tree | dirty | dirty |
| failed | 0 | 0 |
| errored | 0 | 0 |
| **bad** | **0** | **0** |
| passed | 12600 | 12671 |
| skipped | 120 | 120 |

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
 "bad_before": 0,
 "bad_after": 0,
 "unchanged": 0,
 "fixed": [],
 "regressed": [],
 "bad_before_nodeids": [],
 "bad_after_nodeids": []
}
```
