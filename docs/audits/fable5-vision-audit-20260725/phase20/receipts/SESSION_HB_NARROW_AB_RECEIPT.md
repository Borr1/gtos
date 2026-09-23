# Session HB narrow failure-set A/B

**0 bad → 0 bad · 0 fixed · 0 regressed. No regressions.**

Compared by **failure set**, not by count — counts are not portable across worktrees.

| | before | after |
|---|---|---|
| commit | `ba3c18ddf` | `bab74dc7f` |
| captured (UTC) | 2026-08-01T13:36:48Z | 2026-08-01T13:38:15Z |
| working tree | clean | clean |
| failed | 0 | 0 |
| errored | 0 | 0 |
| **bad** | **0** | **0** |
| passed | 16 | 42 |
| skipped | 0 | 0 |

## Embedded captures

Embedded, not referenced. A receipt that points at a scratchpad path is as unverifiable as
no receipt at all, because that file is gone by the time anyone reads this.

```json
{
 "schema": "gtos-ab-receipt-v1",
 "scope": [
  "tests/research_infra/test_wave19_sol_decision_semantics.py"
 ],
 "before": {
  "commit": "ba3c18ddf268294813545501f84b635ccc0f25bb",
  "commit_subject": "phase19: close Sol repair integration and synthesis",
  "captured_utc": "2026-08-01T13:36:48Z",
  "dirty": false,
  "totals": {
   "passed": 16
  }
 },
 "after": {
  "commit": "bab74dc7f43bdf3e21fa34f5bad982011050b83f",
  "commit_subject": "fix(train): fail closed on incomplete cost components",
  "captured_utc": "2026-08-01T13:38:15Z",
  "dirty": false,
  "totals": {
   "passed": 42
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
