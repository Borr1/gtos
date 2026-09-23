# Failure-set A/B

**0 bad → 0 bad · 0 fixed · 0 regressed. No regressions.**

Compared by **failure set**, not by count — counts are not portable across worktrees.

| | before | after |
|---|---|---|
| commit | `681153ed5` | `6a0932acf` |
| captured (UTC) | 2026-07-30T16:49:25Z | 2026-07-31T02:00:31Z |
| working tree | dirty | dirty |
| failed | 0 | 0 |
| errored | 0 | 0 |
| **bad** | **0** | **0** |
| passed | 11930 | 12246 |
| skipped | 121 | 121 |

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
  "commit": "681153ed56386fa14f97e4a94adbc94767af08af",
  "commit_subject": "The carry-conditional fetch DONE \u2014 three sleeves' data blockade broken (receipt)",
  "captured_utc": "2026-07-30T16:49:25Z",
  "dirty": true,
  "totals": {
   "passed": 11930,
   "skipped": 121,
   "xfailed": 32
  }
 },
 "after": {
  "commit": "6a0932acf60fb3c7fa2646624dfb990de95ebb69",
  "commit_subject": "Fix the red train: one real regression, one leak, one order-dependence, three stale assertions",
  "captured_utc": "2026-07-31T02:00:31Z",
  "dirty": true,
  "totals": {
   "passed": 12246,
   "skipped": 121,
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
