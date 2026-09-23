# Session CK scoped ZERO-to-HEAD A/B

**0 bad → 0 bad · 0 fixed · 0 regressed. No regressions.**

Compared by **failure set**, not by count — counts are not portable across worktrees.

| | before | after |
|---|---|---|
| commit | `cb3854c08` | `cb3854c08` |
| captured (UTC) | 2026-07-31T15:40:04Z | 2026-07-31T15:40:10Z |
| working tree | dirty | dirty |
| failed | 0 | 0 |
| errored | 0 | 0 |
| **bad** | **0** | **0** |
| passed | 169 | 169 |
| skipped | 0 | 0 |

## Embedded captures

Embedded, not referenced. A receipt that points at a scratchpad path is as unverifiable as
no receipt at all, because that file is gone by the time anyone reads this.

```json
{
 "schema": "gtos-ab-receipt-v1",
 "scope": [
  "tests/research_infra/test_fast_engine_accel.py",
  "tests/research_infra/test_train_engine_lane.py",
  "tests/test_implementation_state_block_citations.py",
  "tests/test_replay_acceleration_contract_split.py",
  "tests/test_replay_acceleration_real_contract.py",
  "tests/test_replay_acceleration_real_parity.py"
 ],
 "before": {
  "commit": "cb3854c08d429ec29c7fc41e1c94506e033a8318",
  "commit_subject": "test: retire landed CK block exemption",
  "captured_utc": "2026-07-31T15:40:04Z",
  "dirty": true,
  "totals": {
   "passed": 169
  }
 },
 "after": {
  "commit": "cb3854c08d429ec29c7fc41e1c94506e033a8318",
  "commit_subject": "test: retire landed CK block exemption",
  "captured_utc": "2026-07-31T15:40:10Z",
  "dirty": true,
  "totals": {
   "passed": 169
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
