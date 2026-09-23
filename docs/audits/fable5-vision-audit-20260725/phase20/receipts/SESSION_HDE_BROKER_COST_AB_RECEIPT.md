# HDE Extended Broker-Cost Closure A/B

**0 bad → 0 bad · 0 fixed · 0 regressed. No regressions.**

Compared by **failure set**, not by count — counts are not portable across worktrees.

| | before | after |
|---|---|---|
| commit | `e101fa2b1` | `cf70fd7e3` |
| captured (UTC) | 2026-08-01T14:32:55Z | 2026-08-01T14:49:29Z |
| working tree | dirty | dirty |
| failed | 0 | 0 |
| errored | 0 | 0 |
| **bad** | **0** | **0** |
| passed | 46 | 46 |
| skipped | 0 | 0 |

## Embedded captures

Embedded, not referenced. A receipt that points at a scratchpad path is as unverifiable as
no receipt at all, because that file is gone by the time anyone reads this.

```json
{
 "schema": "gtos-ab-receipt-v1",
 "scope": [
  "tests/test_broker_truth_cost_capture_v2.py",
  "tests/research_infra/test_cn_live_cost_truth.py",
  "tests/research_infra/test_cn_live_cost_carry.py",
  "tests/test_repair_broad_replay_terminal_cost_aliases.py",
  "tests/test_costs_layer.py",
  "tests/test_cost_slippage_exit_coverage.py",
  "tests/test_v4_timewarp_simulated_live_research_loop.py::test_marketable_limit_rebased_cost_authority_overrides_original_geometry_cost"
 ],
 "before": {
  "commit": "e101fa2b1e0b9399fba4ad1745d639176e06c3e5",
  "commit_subject": "audit(phase20): close HDB cost falsifier",
  "captured_utc": "2026-08-01T14:32:55Z",
  "dirty": true,
  "totals": {
   "passed": 46
  }
 },
 "after": {
  "commit": "cf70fd7e36eaaab8d5d04e04db8c85a7685b0a83",
  "commit_subject": "refactor(train): minimize cost authority closure",
  "captured_utc": "2026-08-01T14:49:29Z",
  "dirty": true,
  "totals": {
   "passed": 46
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
