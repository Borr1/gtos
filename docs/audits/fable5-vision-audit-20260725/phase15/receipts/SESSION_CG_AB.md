# Session CG — scoped copy-back A/B against ZERO

The before side is `83aa913fd`, reconstructed by copying its bytes over all 13
changed paths and moving the nine new paths aside; no checkout was used. The
same tool-generated scope reached four test files. Two exist on both sides and
form the embedded A/B below. The other two are new this session and were counted
separately: `test_train_engine_footprint.py` plus
`test_train_engine_resident_event_sink.py`, **13 passed / 0 failed**. After the
before capture, all 13 HEAD copies were restored and byte-compared; `git diff
--exit-code` was clean.

**0 bad → 0 bad · 0 fixed · 0 regressed. No regressions.**

Compared by **failure set**, not by count — counts are not portable across worktrees.

| | before | after |
|---|---|---|
| commit | `6d398ebc8` | `6d398ebc8` |
| captured (UTC) | 2026-07-31T12:25:24Z | 2026-07-31T12:24:52Z |
| working tree | dirty | dirty |
| failed | 0 | 0 |
| errored | 0 | 0 |
| **bad** | **0** | **0** |
| passed | 36 | 52 |
| skipped | 0 | 0 |

## Embedded captures

Embedded, not referenced. A receipt that points at a scratchpad path is as unverifiable as
no receipt at all, because that file is gone by the time anyone reads this.

```json
{
 "schema": "gtos-ab-receipt-v1",
 "scope": [
  "tests/research_infra/test_train_engine_cuts.py",
  "tests/test_implementation_state_block_citations.py"
 ],
 "before": {
  "commit": "6d398ebc84e59918e503495f0547a2cdcf3ccae9",
  "commit_subject": "CG: publish findings and handoff",
  "captured_utc": "2026-07-31T12:25:24Z",
  "dirty": true,
  "totals": {
   "passed": 36
  }
 },
 "after": {
  "commit": "6d398ebc84e59918e503495f0547a2cdcf3ccae9",
  "commit_subject": "CG: publish findings and handoff",
  "captured_utc": "2026-07-31T12:24:52Z",
  "dirty": true,
  "totals": {
   "passed": 52
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
