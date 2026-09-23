# Session AU — scoped A/B (B1550–B1599)

**0 bad → 0 bad · 0 fixed · 0 regressed. No regressions.**

Compared by **failure set**, not by count — counts are not portable across worktrees.

| | before | after |
|---|---|---|
| commit | `f6b51dd07` | `f6b51dd07` |
| captured (UTC) | 2026-07-30T14:17:45Z | 2026-07-30T14:18:24Z |
| working tree | dirty | dirty |
| failed | 0 | 0 |
| errored | 0 | 0 |
| **bad** | **0** | **0** |
| passed | 689 | 694 |
| skipped | 3 | 3 |

## Embedded captures

Embedded, not referenced. A receipt that points at a scratchpad path is as unverifiable as
no receipt at all, because that file is gone by the time anyone reads this.

```json
{
 "schema": "gtos-ab-receipt-v1",
 "scope": [
  "tests/research_infra/test_ak_receipt_drivers.py",
  "tests/research_infra/test_ao_candidate_family_v3.py",
  "tests/research_infra/test_ao_p_floor_headroom.py",
  "tests/research_infra/test_candidate_family.py",
  "tests/research_infra/test_candidate_family_chain.py",
  "tests/research_infra/test_candidate_family_v2_ratchet.py",
  "tests/research_infra/test_era_population.py",
  "tests/research_infra/test_fidelity_threshold_variant.py",
  "tests/research_infra/test_gate_partial_universe_stamp.py",
  "tests/research_infra/test_gate_wipeout_signal.py",
  "tests/research_infra/test_trainer_folds.py",
  "tests/research_infra/test_vig_regime_inflation_sign.py",
  "tests/research_infra/test_vig_trial_ledger_prospective.py",
  "tests/research_infra/test_walkforward_book_replay.py",
  "tests/research_infra/test_walkforward_family.py",
  "tests/research_infra/test_walkforward_gate.py",
  "tests/research_infra/test_walkforward_supply.py",
  "tests/research_infra/test_wf_diagnostics.py",
  "tests/safety/test_activation_token_attacks.py",
  "tests/scripts/test_pytest_failset_parsing.py",
  "tests/test_run_book_importable.py",
  "tests/test_spread_composition.py",
  "tests/ultimate_book/test_activation_carry_vps_lineage.py",
  "tests/ultimate_book/test_book_owner.py",
  "tests/ultimate_book/test_breach_flatten.py",
  "tests/ultimate_book/test_candidate_promotion_plumbing.py",
  "tests/ultimate_book/test_learning_actuator_live.py",
  "tests/ultimate_book/test_market_expansion_runtime_generator.py",
  "tests/ultimate_book/test_order_route.py",
  "tests/ultimate_book/test_packet_carry_vps_lineage.py",
  "tests/ultimate_book/test_packet_emitter_hardening.py",
  "tests/ultimate_book/test_pre_gap_bar_wiring.py",
  "tests/ultimate_book/test_runtime_learning_packet.py",
  "tests/ultimate_book/test_time_stop_units.py"
 ],
 "before": {
  "commit": "f6b51dd07cada007bb236c84e846f95c1b1fdcb0",
  "commit_subject": "Wave 12: commission AU (contract wiring + estate restamp B1550-B1599) and AV (the sample engine B1600-B1649)",
  "captured_utc": "2026-07-30T14:17:45Z",
  "dirty": true,
  "totals": {
   "passed": 689,
   "skipped": 3,
   "xfailed": 1
  }
 },
 "after": {
  "commit": "f6b51dd07cada007bb236c84e846f95c1b1fdcb0",
  "commit_subject": "Wave 12: commission AU (contract wiring + estate restamp B1550-B1599) and AV (the sample engine B1600-B1649)",
  "captured_utc": "2026-07-30T14:18:24Z",
  "dirty": true,
  "totals": {
   "passed": 694,
   "skipped": 3,
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

---

## Scope, and the two things this receipt does not cover

**Why the scope is 34 files and not the tool's own answer.** `pytest_failset.py scope --base f6b51dd07
--include-worktree` escalates to the FULL suite, and its stated reason is one path:
`scripts/gtos_hydrate_test_data.py` resolves to no module and no test literal. That escalation is the
right default for an unknown consumer, and it is wrong here for a reason that is checkable rather than
asserted: the file is a standalone maintenance script, `rg gtos_hydrate_test_data tests/ src/` returns
nothing, and this session's change to it is one entry in a list of sparse-checkout paths. So the scope
was recomputed over the other 26 changed paths, which resolved cleanly to 36 test files. Per the
wave-11 agreement §2 the full-suite A/B is the orchestrator's, once per merge train.

**The two new test files are counted separately, not inside the diff.** They do not exist on the before
side, so including them would compare 36 files against 34 and the tool would (correctly) refuse. The
comparison above is over the **34 shared** files; the new files are:

| file | tests |
|---|---:|
| `tests/ultimate_book/test_frontier_exit_contracts.py` | 43 |
| `tests/ultimate_book/test_runtime_flag_defaults_complete.py` | 6 |

Run over the full 36-file scope at HEAD: **743 passed / 3 skipped / 1 xfailed / 0 failed / 0 errored.**
So the honest total is **0 bad → 0 bad, 0 regressed, +5 net new passing tests inside the shared scope
(3 in `test_vig_regime_inflation_sign.py`, 2 in `test_learning_actuator_live.py`) and +49 in the two
new files.**

**Copy-back, never `git checkout`.** The 12 modified tracked files were restored to `f6b51dd07`'s bytes
from `git show`, the 2 new test files were moved aside, and afterwards every one of the 12 was restored
from a held copy and **sha256-verified against the pre-A/B digest — 0 mismatches** — with `git status`
confirming the same 12 modified + 4 untracked paths as before the run. AR §8.9 recorded a confounded
A/B produced by zsh word-splitting inside a restore loop that agreed with the truth anyway; this one is
done in Python and the restore is verified by digest rather than by inspection.

**Two new tests failed on their first run and both were real.** The `regime_inflation` floor fixture
had an unrealistically clean equity curve (`sr_window` ~10 instead of ~0.04), so no injected variance
could reach the penalty floor and the test asserted a state it could not produce; and
`test_every_wired_override_is_a_sleeve_the_registry_knows` called `effective_registry` without the live
market-expansion policy, which fails closed to 20 sleeves and does not contain `mx_btcusd`. Both are
recorded in the result doc's §what-I-got-wrong.
