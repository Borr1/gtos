# Session HB train-engine and cost closure A/B

**0 bad → 0 bad · 0 fixed · 0 regressed. No regressions.**

Compared by **failure set**, not by count — counts are not portable across worktrees.

| | before | after |
|---|---|---|
| commit | `ba3c18ddf` | `bab74dc7f` |
| captured (UTC) | 2026-08-01T13:36:41Z | 2026-08-01T13:38:16Z |
| working tree | clean | clean |
| failed | 0 | 0 |
| errored | 0 | 0 |
| **bad** | **0** | **0** |
| passed | 205 | 231 |
| skipped | 0 | 0 |

## Embedded captures

Embedded, not referenced. A receipt that points at a scratchpad path is as unverifiable as
no receipt at all, because that file is gone by the time anyone reads this.

```json
{
 "schema": "gtos-ab-receipt-v1",
 "scope": [
  "tests/research_infra/test_train_engine_accept.py",
  "tests/research_infra/test_train_engine_cuts.py",
  "tests/research_infra/test_train_engine_footprint.py",
  "tests/research_infra/test_train_engine_guard.py",
  "tests/research_infra/test_train_engine_identity.py",
  "tests/research_infra/test_train_engine_lane.py",
  "tests/research_infra/test_train_engine_resident_event_sink.py",
  "tests/research_infra/test_wave19_sol_decision_semantics.py",
  "tests/test_broker_net_cost_engine.py"
 ],
 "before": {
  "commit": "ba3c18ddf268294813545501f84b635ccc0f25bb",
  "commit_subject": "phase19: close Sol repair integration and synthesis",
  "captured_utc": "2026-08-01T13:36:41Z",
  "dirty": false,
  "totals": {
   "passed": 205
  }
 },
 "after": {
  "commit": "bab74dc7f43bdf3e21fa34f5bad982011050b83f",
  "commit_subject": "fix(train): fail closed on incomplete cost components",
  "captured_utc": "2026-08-01T13:38:16Z",
  "dirty": false,
  "totals": {
   "passed": 231
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
