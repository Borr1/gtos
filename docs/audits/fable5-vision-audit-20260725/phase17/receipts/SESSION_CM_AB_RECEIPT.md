# Session CM armed-fidelity A/B receipt

**0 bad → 0 bad · 0 fixed · 0 regressed. No regressions.**

Compared by **failure set**, not by count — counts are not portable across worktrees.

| | before | after |
|---|---|---|
| commit | `6608eb969` | `d82883992` |
| captured (UTC) | 2026-07-31T17:26:48Z | 2026-07-31T18:43:08Z |
| working tree | dirty | dirty |
| failed | 0 | 0 |
| errored | 0 | 0 |
| **bad** | **0** | **0** |
| passed | 12600 | 503 |
| skipped | 120 | 0 |

## Scope difference — declared, not hidden

- before: `['tests/']`
- after : `['tests/research_infra/test_av_metalabel_leakfree.py', 'tests/research_infra/test_cm_armed_fidelity.py', 'tests/research_infra/test_walkforward_supply.py', 'tests/test_implementation_state_block_citations.py', 'tests/ultimate_book/test_activation_carry_vps_lineage.py', 'tests/ultimate_book/test_az_activation_carry_mx.py', 'tests/ultimate_book/test_ba_weekend_policy.py', 'tests/ultimate_book/test_book_owner.py', 'tests/ultimate_book/test_candidate_promotion_plumbing.py', 'tests/ultimate_book/test_ce_entry_hour_lever.py', 'tests/ultimate_book/test_exit_contract_activation.py', 'tests/ultimate_book/test_frontier_exit_contracts.py', 'tests/ultimate_book/test_market_expansion_runtime_generator.py', 'tests/ultimate_book/test_order_route.py', 'tests/ultimate_book/test_packet_carry_vps_lineage.py', 'tests/ultimate_book/test_time_stop_rehydration.py', 'tests/ultimate_book/test_time_stop_units.py']`

**Why this is still a comparison:** Before is the committed whole-suite ZERO baseline at 12,600 tests. After is the tool-derived 17-file dependency/path-literal closure of the exact Session CM diff from 83867e65f6abe317411cbef48bf44414acf28111 through d82883992, including in-worktree CM receipt/capture artifacts: 503 passed, 1 xfailed, 0 failed, 0 errored. The only unrelated dirty path is generated .context/LIVE_STATE.md; every substantive Session CM source, test, finding, activation package, block, range retirement, and Wave-16a receipt repair was committed before capture.

## Embedded captures

Embedded, not referenced. A receipt that points at a scratchpad path is as unverifiable as
no receipt at all, because that file is gone by the time anyone reads this.

```json
{
 "schema": "gtos-ab-receipt-v1",
 "scope": [
  "tests/"
 ],
 "before": {
  "commit": "6608eb969297ed8cbe218662f3987344a576bc6c",
  "commit_subject": "Merge Session CI: the vp time-depth blockade is solved; the comparability gate honestly refuses",
  "captured_utc": "2026-07-31T17:26:48Z",
  "dirty": true,
  "totals": {
   "passed": 12600,
   "skipped": 120,
   "xfailed": 32
  }
 },
 "after": {
  "commit": "d8288399201e5bc118210674a8922b1aed75b78d",
  "commit_subject": "audit: make Wave-16a A/B self-contained",
  "captured_utc": "2026-07-31T18:43:08Z",
  "dirty": true,
  "totals": {
   "passed": 503,
   "xfailed": 1
  }
 },
 "bad_before": 0,
 "bad_after": 0,
 "unchanged": 0,
 "fixed": [],
 "regressed": [],
 "bad_before_nodeids": [],
 "bad_after_nodeids": [],
 "scope_difference": {
  "before": [
   "tests/"
  ],
  "after": [
   "tests/research_infra/test_av_metalabel_leakfree.py",
   "tests/research_infra/test_cm_armed_fidelity.py",
   "tests/research_infra/test_walkforward_supply.py",
   "tests/test_implementation_state_block_citations.py",
   "tests/ultimate_book/test_activation_carry_vps_lineage.py",
   "tests/ultimate_book/test_az_activation_carry_mx.py",
   "tests/ultimate_book/test_ba_weekend_policy.py",
   "tests/ultimate_book/test_book_owner.py",
   "tests/ultimate_book/test_candidate_promotion_plumbing.py",
   "tests/ultimate_book/test_ce_entry_hour_lever.py",
   "tests/ultimate_book/test_exit_contract_activation.py",
   "tests/ultimate_book/test_frontier_exit_contracts.py",
   "tests/ultimate_book/test_market_expansion_runtime_generator.py",
   "tests/ultimate_book/test_order_route.py",
   "tests/ultimate_book/test_packet_carry_vps_lineage.py",
   "tests/ultimate_book/test_time_stop_rehydration.py",
   "tests/ultimate_book/test_time_stop_units.py"
  ],
  "justification": "Before is the committed whole-suite ZERO baseline at 12,600 tests. After is the tool-derived 17-file dependency/path-literal closure of the exact Session CM diff from 83867e65f6abe317411cbef48bf44414acf28111 through d82883992, including in-worktree CM receipt/capture artifacts: 503 passed, 1 xfailed, 0 failed, 0 errored. The only unrelated dirty path is generated .context/LIVE_STATE.md; every substantive Session CM source, test, finding, activation package, block, range retirement, and Wave-16a receipt repair was committed before capture."
 }
}
```
