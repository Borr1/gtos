# Session CL scoped copy-back A/B

**0 bad → 0 bad · 0 fixed · 0 regressed. No regressions.**

Compared by **failure set**, not by count — counts are not portable across worktrees.

| | before | after |
|---|---|---|
| commit | `c13322ceb` | `c13322ceb` |
| captured (UTC) | 2026-07-31T18:29:15Z | 2026-07-31T18:29:34Z |
| working tree | dirty | dirty |
| failed | 0 | 0 |
| errored | 0 | 0 |
| **bad** | **0** | **0** |
| passed | 215 | 215 |
| skipped | 0 | 0 |

## Embedded captures

Embedded, not referenced. A receipt that points at a scratchpad path is as unverifiable as
no receipt at all, because that file is gone by the time anyone reads this.

```json
{
 "schema": "gtos-ab-receipt-v1",
 "scope": [
  "tests/research_infra/test_ce_rule_amendment.py",
  "tests/research_infra/test_train_engine_lane.py",
  "tests/research_infra/test_training_lane_protocol.py",
  "tests/test_implementation_state_block_citations.py",
  "tests/ultimate_book/test_activation_carry_vps_lineage.py",
  "tests/ultimate_book/test_az_activation_carry_mx.py",
  "tests/ultimate_book/test_packet_carry_vps_lineage.py"
 ],
 "before": {
  "commit": "c13322ceb0cb52135a48a839de5dcdbeb860fdab",
  "commit_subject": "docs: hand off Session CL pass-surface result",
  "captured_utc": "2026-07-31T18:29:15Z",
  "dirty": true,
  "totals": {
   "passed": 215
  }
 },
 "after": {
  "commit": "c13322ceb0cb52135a48a839de5dcdbeb860fdab",
  "commit_subject": "docs: hand off Session CL pass-surface result",
  "captured_utc": "2026-07-31T18:29:34Z",
  "dirty": true,
  "totals": {
   "passed": 215
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
