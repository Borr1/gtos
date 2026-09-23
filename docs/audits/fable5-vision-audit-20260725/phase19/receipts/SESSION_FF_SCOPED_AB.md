# Session FF hard-eligibility observability scoped A/B

**0 bad → 0 bad · 0 fixed · 0 regressed. No regressions.**

Compared by **failure set**, not by count — counts are not portable across worktrees.

| | before | after |
|---|---|---|
| commit | `96659451b` | `d52e48b2d` |
| captured (UTC) | 2026-08-01T02:25:57Z | 2026-08-01T02:25:58Z |
| working tree | clean | clean |
| failed | 0 | 0 |
| errored | 0 | 0 |
| **bad** | **0** | **0** |
| passed | 102 | 110 |
| skipped | 0 | 0 |

## Embedded captures

Embedded, not referenced. A receipt that points at a scratchpad path is as unverifiable as
no receipt at all, because that file is gone by the time anyone reads this.

```json
{
 "schema": "gtos-ab-receipt-v1",
 "scope": [
  "tests/research_infra/test_train_engine_cuts.py",
  "tests/research_infra/test_train_engine_footprint.py",
  "tests/research_infra/test_train_engine_lane.py",
  "tests/research_infra/test_train_engine_resident_event_sink.py"
 ],
 "before": {
  "commit": "96659451be725912bf7f7d709271a3190df65ddc",
  "commit_subject": "FF: close Sol composition attribution",
  "captured_utc": "2026-08-01T02:25:57Z",
  "dirty": false,
  "totals": {
   "passed": 102
  }
 },
 "after": {
  "commit": "d52e48b2d0093dc0d9e42a4e3d6d774029fc0095",
  "commit_subject": "FF: preserve exact hard-eligibility observability",
  "captured_utc": "2026-08-01T02:25:58Z",
  "dirty": false,
  "totals": {
   "passed": 110
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
