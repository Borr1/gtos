# Session HA Fidelity Authority A/B Receipt

**0 bad → 0 bad · 0 fixed · 0 regressed. No regressions.**

Compared by **failure set**, not by count — counts are not portable across worktrees.

| | before | after |
|---|---|---|
| commit | `ba3c18ddf` | `3cf333865` |
| captured (UTC) | 2026-08-01T13:37:32Z | 2026-08-01T13:37:41Z |
| working tree | clean | clean |
| failed | 0 | 0 |
| errored | 0 | 0 |
| **bad** | **0** | **0** |
| passed | 154 | 167 |
| skipped | 0 | 0 |

## Embedded captures

Embedded, not referenced. A receipt that points at a scratchpad path is as unverifiable as
no receipt at all, because that file is gone by the time anyone reads this.

```json
{
 "schema": "gtos-ab-receipt-v1",
 "scope": [
  "tests/research_infra/test_direct_fidelity_measurement.py",
  "tests/research_infra/test_walkforward_gate.py",
  "tests/research_infra/test_fidelity_register_matches_receipt.py",
  "tests/research_infra/test_fidelity_threshold_variant.py",
  "tests/research_infra/test_gate_wipeout_signal.py",
  "tests/research_infra/test_cr_ny_metals_capture.py",
  "tests/research_infra/test_candidate_family.py",
  "tests/research_infra/test_published_seals_pinned_by_value.py"
 ],
 "before": {
  "commit": "ba3c18ddf268294813545501f84b635ccc0f25bb",
  "commit_subject": "phase19: close Sol repair integration and synthesis",
  "captured_utc": "2026-08-01T13:37:32Z",
  "dirty": false,
  "totals": {
   "passed": 154
  }
 },
 "after": {
  "commit": "3cf33386558e8ae279296069d3a72137b07794c3",
  "commit_subject": "fix(walkforward): harden fidelity reference authority",
  "captured_utc": "2026-08-01T13:37:41Z",
  "dirty": false,
  "totals": {
   "passed": 167
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
