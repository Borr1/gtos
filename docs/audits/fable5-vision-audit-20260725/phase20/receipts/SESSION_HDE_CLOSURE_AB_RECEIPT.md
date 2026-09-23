# HDE Equal-Scope Cost Closure A/B

**0 bad → 0 bad · 0 fixed · 0 regressed. No regressions.**

Compared by **failure set**, not by count — counts are not portable across worktrees.

| | before | after |
|---|---|---|
| commit | `e101fa2b1` | `cf70fd7e3` |
| captured (UTC) | 2026-08-01T14:32:54Z | 2026-08-01T14:49:28Z |
| working tree | dirty | dirty |
| failed | 0 | 0 |
| errored | 0 | 0 |
| **bad** | **0** | **0** |
| passed | 355 | 355 |
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
  "tests/research_infra/test_wave20_cost_completeness_falsifier.py",
  "tests/test_broker_net_cost_engine.py"
 ],
 "before": {
  "commit": "e101fa2b1e0b9399fba4ad1745d639176e06c3e5",
  "commit_subject": "audit(phase20): close HDB cost falsifier",
  "captured_utc": "2026-08-01T14:32:54Z",
  "dirty": true,
  "totals": {
   "passed": 355
  }
 },
 "after": {
  "commit": "cf70fd7e36eaaab8d5d04e04db8c85a7685b0a83",
  "commit_subject": "refactor(train): minimize cost authority closure",
  "captured_utc": "2026-08-01T14:49:28Z",
  "dirty": true,
  "totals": {
   "passed": 355
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
