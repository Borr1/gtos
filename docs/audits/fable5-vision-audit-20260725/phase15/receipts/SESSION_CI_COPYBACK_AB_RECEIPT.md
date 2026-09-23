# Session CI — shared-surface copy-back A/B

**Method:** all 14 CI paths in `be9b5ed4c..7fcb4400c` were copied to a temporary recovery
directory; added paths were moved out of the tree and the two modified paths were replaced with
their `be9b5ed4c` bytes. No `git checkout` was used. The shared pre-existing citation test was
captured, every final byte was copied back, the restored paths were byte-compared to the saved
finals, and the same test was captured again. The commit id is intentionally the same on both rows:
copy-back changes the worktree being tested, not git history.

**0 bad → 0 bad · 0 fixed · 0 regressed. No regressions.**

Compared by **failure set**, not by count — counts are not portable across worktrees.

| | before | after |
|---|---|---|
| commit | `7fcb4400c` | `7fcb4400c` |
| captured (UTC) | 2026-07-31T11:55:56Z | 2026-07-31T11:55:59Z |
| working tree | dirty | dirty |
| failed | 0 | 0 |
| errored | 0 | 0 |
| **bad** | **0** | **0** |
| passed | 9 | 9 |
| skipped | 0 | 0 |

## Embedded captures

Embedded, not referenced. A receipt that points at a scratchpad path is as unverifiable as
no receipt at all, because that file is gone by the time anyone reads this.

```json
{
 "schema": "gtos-ab-receipt-v1",
 "scope": [
  "tests/test_implementation_state_block_citations.py"
 ],
 "before": {
  "commit": "7fcb4400ca9b7ebf18fb23e1979f85434b74ccf0",
  "commit_subject": "Close Session CI with verified structural stop",
  "captured_utc": "2026-07-31T11:55:56Z",
  "dirty": true,
  "totals": {
   "passed": 9
  }
 },
 "after": {
  "commit": "7fcb4400ca9b7ebf18fb23e1979f85434b74ccf0",
  "commit_subject": "Close Session CI with verified structural stop",
  "captured_utc": "2026-07-31T11:55:59Z",
  "dirty": true,
  "totals": {
   "passed": 9
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
