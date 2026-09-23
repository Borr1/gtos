# Session FB scoped failure-set A/B

**0 bad → 0 bad · 0 fixed · 0 regressed. No regressions.**

Compared by **failure set**, not by count — counts are not portable across worktrees.

| | before | after |
|---|---|---|
| commit | `d194d9f1f` | `ad1ab0e7c` |
| captured (UTC) | 2026-08-01T02:21:07Z | 2026-08-01T02:34:18Z |
| working tree | dirty | dirty |
| failed | 0 | 0 |
| errored | 0 | 0 |
| **bad** | **0** | **0** |
| passed | 10 | 10 |
| skipped | 0 | 0 |

## Embedded captures

Embedded, not referenced. A receipt that points at a scratchpad path is as unverifiable as
no receipt at all, because that file is gone by the time anyone reads this.

```json
{
 "schema": "gtos-ab-receipt-v1",
 "scope": [
  "tests/research_infra/test_cq_path_pool_grid.py"
 ],
 "before": {
  "commit": "d194d9f1f8270586ca6c2d916c7333e051a54439",
  "commit_subject": "audit(phase19): preregister Sol family geometry",
  "captured_utc": "2026-08-01T02:21:07Z",
  "dirty": true,
  "totals": {
   "passed": 10
  }
 },
 "after": {
  "commit": "ad1ab0e7c253a2deaf850d8eb43890719c9ad3b8",
  "commit_subject": "feat(phase19): add default-off OB-retest geometry candidate",
  "captured_utc": "2026-08-01T02:34:18Z",
  "dirty": true,
  "totals": {
   "passed": 10
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
