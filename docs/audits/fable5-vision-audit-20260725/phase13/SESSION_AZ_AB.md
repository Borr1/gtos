# Failure-set A/B — Session AZ (wave 13, B1850–B1899)

**0 bad → 0 bad · 0 fixed · 0 regressed. No regressions.**
**+39 net new passing tests in one new file** (`tests/ultimate_book/test_az_activation_carry_mx.py`),
outside the shared scope below and therefore reported separately rather than folded into a
count that would not be an A/B.

`scripts/pytest_failset.py scope --base HEAD --include-worktree` returned **18** files. The new
test file does not exist at HEAD, so the A/B is run over the **17 shared** files — an A/B across
different scopes is not a comparison, and the tool refuses one. The 18-file run at HEAD+work is
**470 passed / 0 failed / 0 errored**, i.e. 431 shared + 39 new.

Changed under test: `run_book.py` (the B1852 launch-banner repair) and
`src/components/ultimate_book/execution_packets.py` (`describe_frontier_contract`). Everything
else this session added is under `docs/audits/.../phase13/activation_carry_mx/` and is not on
any import path.

Compared by **failure set**, not by count — counts are not portable across worktrees.

| | before | after |
|---|---|---|
| commit | `46a0d21be` | `46a0d21be` |
| captured (UTC) | 2026-07-30T16:52:36Z | 2026-07-30T16:54:27Z |
| working tree | clean | dirty |
| failed | 0 | 0 |
| errored | 0 | 0 |
| **bad** | **0** | **0** |
| passed | 431 | 431 |
| skipped | 0 | 0 |

## Embedded captures

Embedded, not referenced. A receipt that points at a scratchpad path is as unverifiable as
no receipt at all, because that file is gone by the time anyone reads this.

```json
{
 "schema": "gtos-ab-receipt-v1",
 "scope": [
  "tests/research_infra/test_av_metalabel_leakfree.py",
  "tests/research_infra/test_walkforward_supply.py",
  "tests/safety/test_activation_token_attacks.py",
  "tests/scripts/test_pytest_failset_parsing.py",
  "tests/test_run_book_importable.py",
  "tests/ultimate_book/test_activation_carry_vps_lineage.py",
  "tests/ultimate_book/test_book_owner.py",
  "tests/ultimate_book/test_book_sleeve_telemetry.py",
  "tests/ultimate_book/test_candidate_promotion_plumbing.py",
  "tests/ultimate_book/test_exit_contract_activation.py",
  "tests/ultimate_book/test_frontier_exit_contracts.py",
  "tests/ultimate_book/test_market_expansion_runtime_generator.py",
  "tests/ultimate_book/test_order_route.py",
  "tests/ultimate_book/test_packet_carry_vps_lineage.py",
  "tests/ultimate_book/test_pre_gap_bar_wiring.py",
  "tests/ultimate_book/test_time_stop_rehydration.py",
  "tests/ultimate_book/test_time_stop_units.py"
 ],
 "before": {
  "commit": "46a0d21bec6e06ac7a4b80d493adc7e15913f3a6",
  "commit_subject": "Commission AZ: the mx_btcusd activation carry (B1850-B1899) \u2014 the surface moves",
  "captured_utc": "2026-07-30T16:52:36Z",
  "dirty": false,
  "totals": {
   "passed": 431,
   "xfailed": 1
  }
 },
 "after": {
  "commit": "46a0d21bec6e06ac7a4b80d493adc7e15913f3a6",
  "commit_subject": "Commission AZ: the mx_btcusd activation carry (B1850-B1899) \u2014 the surface moves",
  "captured_utc": "2026-07-30T16:54:27Z",
  "dirty": true,
  "totals": {
   "passed": 431,
   "xfailed": 1
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
