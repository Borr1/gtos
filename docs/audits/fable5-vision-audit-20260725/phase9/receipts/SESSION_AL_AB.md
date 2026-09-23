# Failure-set A/B

**1 bad → 0 bad · 1 fixed · 0 regressed. No regressions.**

Compared by **failure set**, not by count — counts are not portable across worktrees.

| | before | after |
|---|---|---|
| commit | `f83ea9fc2` | `f83ea9fc2` |
| captured (UTC) | 2026-07-30T03:16:30Z | 2026-07-30T03:17:13Z |
| working tree | dirty | dirty |
| failed | 1 | 0 |
| errored | 0 | 0 |
| **bad** | **1** | **0** |
| passed | 274 | 275 |
| skipped | 0 | 0 |

## Fixed (1)

- `tests/test_implementation_state_block_citations.py::test_the_in_flight_wave_range_is_declared_and_shrinking`

## Embedded captures

Embedded, not referenced. A receipt that points at a scratchpad path is as unverifiable as
no receipt at all, because that file is gone by the time anyone reads this.

```json
{
 "schema": "gtos-ab-receipt-v1",
 "scope": [
  "tests/research_infra/test_ak_receipt_drivers.py",
  "tests/research_infra/test_candidate_family.py",
  "tests/research_infra/test_fidelity_register_matches_receipt.py",
  "tests/research_infra/test_trainer_folds.py",
  "tests/research_infra/test_vig_trial_ledger_prospective.py",
  "tests/research_infra/test_walkforward_book_replay.py",
  "tests/research_infra/test_walkforward_family.py",
  "tests/research_infra/test_walkforward_gate.py",
  "tests/research_infra/test_walkforward_supply.py",
  "tests/research_infra/test_wf_diagnostics.py",
  "tests/test_implementation_state_block_citations.py",
  "tests/test_spread_composition.py"
 ],
 "before": {
  "commit": "f83ea9fc27f00f8477e8d99a8264ec4a7e972a9e",
  "commit_subject": "AL: the drivers \u2014 regeneration through the production port, the four populations, and the ratcheted family",
  "captured_utc": "2026-07-30T03:16:30Z",
  "dirty": true,
  "totals": {
   "failed": 1,
   "passed": 274
  }
 },
 "after": {
  "commit": "f83ea9fc27f00f8477e8d99a8264ec4a7e972a9e",
  "commit_subject": "AL: the drivers \u2014 regeneration through the production port, the four populations, and the ratcheted family",
  "captured_utc": "2026-07-30T03:17:13Z",
  "dirty": true,
  "totals": {
   "passed": 275
  }
 },
 "bad_before": 1,
 "bad_after": 0,
 "unchanged": 0,
 "fixed": [
  "tests/test_implementation_state_block_citations.py::test_the_in_flight_wave_range_is_declared_and_shrinking"
 ],
 "regressed": [],
 "bad_before_nodeids": [
  "tests/test_implementation_state_block_citations.py::test_the_in_flight_wave_range_is_declared_and_shrinking"
 ],
 "bad_after_nodeids": []
}
```
