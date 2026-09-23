# Wave-15 train A/B — CE (activation package) + CF (the refuted rename, the real watchdog)

**0 bad → 0 bad · 0 fixed · 0 regressed. No regressions.**

Compared by **failure set**, not by count — counts are not portable across worktrees.

| | before | after |
|---|---|---|
| commit | `02edf909a` | `d312e06e3` |
| captured (UTC) | 2026-07-31T05:31:16Z | 2026-07-31T10:22:21Z |
| working tree | dirty | dirty |
| failed | 0 | 0 |
| errored | 0 | 0 |
| **bad** | **0** | **0** |
| passed | 12403 | 12476 |
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
 "after": {
  "commit": "d312e06e3cbfbc676ea654ef2464725f0d87188d",
  "commit_subject": "Merge Session CF: there was no rename \u2014 the orchestrator's event refuted with the broker's own tree, and the real silence gets a watchdog",
  "captured_utc": "2026-07-31T10:22:21Z",
  "dirty": true,
  "totals": {
   "passed": 12476,
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
