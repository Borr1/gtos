# Wave-14 train A/B — the training-lane wave (CA, CB, CC merged; V13 resolution; incubation adoption)

**0 bad → 0 bad · 0 fixed · 0 regressed. No regressions.**

Compared by **failure set**, not by count — counts are not portable across worktrees.

| | before | after |
|---|---|---|
| commit | `6a0932acf` | `02edf909a` |
| captured (UTC) | 2026-07-31T02:00:31Z | 2026-07-31T05:31:16Z |
| working tree | dirty | dirty |
| failed | 0 | 0 |
| errored | 0 | 0 |
| **bad** | **0** | **0** |
| passed | 12246 | 12403 |
| skipped | 121 | 120 |

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
 "after": {
  "commit": "02edf909ad108615daa84568834246d6bdc0e8d8",
  "commit_subject": "H-CB-2 run: the trusted key is measured clean at 44.3M hits; three memos are measured dirty and CD is bound to the safe set",
  "captured_utc": "2026-07-31T05:31:16Z",
  "dirty": true,
  "totals": {
   "passed": 12403,
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
