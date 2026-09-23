# Wave-14b train A/B — Session CD: the regeneration lands

**0 bad → 0 bad · 0 fixed · 0 regressed. No regressions.**

Compared by **failure set**, not by count — counts are not portable across worktrees.

| | before | after |
|---|---|---|
| commit | `d312e06e3` | `ce40cd566` |
| captured (UTC) | 2026-07-31T10:22:21Z | 2026-07-31T12:08:02Z |
| working tree | dirty | dirty |
| failed | 0 | 0 |
| errored | 0 | 0 |
| **bad** | **0** | **0** |
| passed | 12476 | 12522 |
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
 "after": {
  "commit": "ce40cd566f80cd4c4845b8d48b3cb27cc2f14ec7",
  "commit_subject": "Merge Session CD: the regeneration lands \u2014 the repairs make the family worse, and the deficit was never the cost model",
  "captured_utc": "2026-07-31T12:08:02Z",
  "dirty": true,
  "totals": {
   "passed": 12522,
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
