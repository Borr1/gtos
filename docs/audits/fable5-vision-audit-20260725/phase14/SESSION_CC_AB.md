# Session CC — scoped A/B (training-lane protocol machinery, B2200–B2231)

**1 bad → 1 bad · 0 fixed · 0 regressed. No regressions.**

Compared by **failure set**, not by count — counts are not portable across worktrees.

| | before | after |
|---|---|---|
| commit | `046c29b10` | `046c29b10` |
| captured (UTC) | 2026-07-31T03:30:49Z | 2026-07-31T03:30:31Z |
| working tree | dirty | clean |
| failed | 0 | 0 |
| errored | 1 | 1 |
| **bad** | **1** | **1** |
| passed | 551 | 552 |
| skipped | 1 | 1 |

## Embedded captures

Embedded, not referenced. A receipt that points at a scratchpad path is as unverifiable as
no receipt at all, because that file is gone by the time anyone reads this.

```json
{
 "schema": "gtos-ab-receipt-v1",
 "scope": [
  "tests/research_infra/test_ao_candidate_family_v3.py",
  "tests/research_infra/test_ao_p_floor_headroom.py",
  "tests/research_infra/test_builder_partition_safety.py",
  "tests/research_infra/test_candidate_family.py",
  "tests/research_infra/test_candidate_family_chain.py",
  "tests/research_infra/test_candidate_family_v2_ratchet.py",
  "tests/research_infra/test_era_population.py",
  "tests/research_infra/test_fast_engine_accel.py",
  "tests/research_infra/test_fidelity_register_matches_receipt.py",
  "tests/research_infra/test_fidelity_threshold_variant.py",
  "tests/research_infra/test_gate_partial_universe_stamp.py",
  "tests/research_infra/test_gate_wipeout_signal.py",
  "tests/research_infra/test_learned_edge_dataset_builder.py",
  "tests/research_infra/test_learned_edge_walkforward_gate.py",
  "tests/research_infra/test_moonshot_unified_execution_scorer.py",
  "tests/research_infra/test_population_rule_ratified.py",
  "tests/research_infra/test_published_seals_pinned_by_value.py",
  "tests/research_infra/test_trainer_folds.py",
  "tests/research_infra/test_trainer_partitions.py",
  "tests/research_infra/test_vig_regime_inflation_sign.py",
  "tests/research_infra/test_vig_walk_forward.py",
  "tests/research_infra/test_walkforward_book_replay.py",
  "tests/research_infra/test_walkforward_diversifier.py",
  "tests/research_infra/test_walkforward_family.py",
  "tests/research_infra/test_walkforward_gate.py",
  "tests/research_infra/test_walkforward_supply.py",
  "tests/research_infra/test_wf_diagnostics.py",
  "tests/research_infra/test_wf_exits_parity.py",
  "tests/research_infra/test_wf_registry_surface_reconciliation.py",
  "tests/test_implementation_state_block_citations.py",
  "tests/test_spread_composition.py",
  "tests/ultimate_book/test_running_conviction.py"
 ],
 "before": {
  "commit": "046c29b102c9bc8c2151b7f8d2818742cbfba4fa",
  "commit_subject": "B2231: the mandated copy-back A/B has a landmine, repaired at the test",
  "captured_utc": "2026-07-31T03:30:49Z",
  "dirty": true,
  "totals": {
   "passed": 551,
   "skipped": 1,
   "error": 1
  }
 },
 "after": {
  "commit": "046c29b102c9bc8c2151b7f8d2818742cbfba4fa",
  "commit_subject": "B2231: the mandated copy-back A/B has a landmine, repaired at the test",
  "captured_utc": "2026-07-31T03:30:31Z",
  "dirty": false,
  "totals": {
   "passed": 552,
   "skipped": 1,
   "error": 1
  }
 },
 "bad_before": 1,
 "bad_after": 1,
 "unchanged": 1,
 "fixed": [],
 "regressed": [],
 "bad_before_nodeids": [
  "tests/research_infra/test_moonshot_unified_execution_scorer.py"
 ],
 "bad_after_nodeids": [
  "tests/research_infra/test_moonshot_unified_execution_scorer.py"
 ]
}
```

---

## Annex — the four things the numbers above need said out loud

**1. The scope, and why it is these 32 files.** Everything under `tests/` that imports a module
this session changed (`trainer_partitions`, `candidate_family`, `training_lane`, and the
`walkforward` package that reads the family declaration), plus the block-citation guard whose
input this session edited, plus `test_fast_engine_accel.py` which this session repaired (B2231).
Derived mechanically by `rg -l`, not chosen.

**2. The one `bad` on BOTH sides is pre-existing, filed, and not mine.**
`tests/research_infra/test_moonshot_unified_execution_scorer.py` fails at COLLECTION with
`ImportError: cannot import name 'aggregate_reduction_rows' from
src.research_infra.moonshot_expanded_market_leakage_reduction`. Byte-identical on both sides.
Session AT triaged it in wave 6 (`phase6/receipts/at_triage.py` → `ID_OVERRIDES`, verdict
**KEEP-REAL**): *"223 tests that have never once collected… that name has never existed there in
ANY revision — `git log -S` finds it only in the commit that added this test file (f3e0dc3a1).
The sibling import `aggregate_execution_rows` is missing from its module too, so this is an
unwritten API surface, not a rename."* AT deliberately did not delete it and specified the
repair as a next task. Not absorbed here: writing two unwritten API functions blind, then
discovering what 223 hidden tests assert, is a session, not a footnote in one. **Handed off.**

So the honest phrasing of the headline is: **0 → 0 by failure set, with one pre-existing
collection error unchanged on both sides.** It is not a regression and it is not zero.

**3. The `+1 passed` is an existing guard applying itself to a new artifact.** Identified by
node id rather than inferred: `test_candidate_family_v2_ratchet.py::
test_a_successor_is_a_superset_of_what_it_supersedes[CANDIDATE_FAMILY_V12.json]`. That test
discovers declarations on disk and asserts each is a superset of what it supersedes; V12 adds
one parametrization and it passes. Nothing was made to pass by weakening anything.

**4. Both captures name the same commit, and here that is CORRECT rather than the fake-A/B
shape.** Session BD's B2075 warns that identical commits on both sides can mean HEAD never
moved and nothing was compared. Under copy-back, HEAD *deliberately* never moves — the WORKING
TREE is moved instead — so the honest tell is the `dirty` flag plus the verification below,
not the commit hash. 19 changed paths were written from `7b5cbf8d8`'s bytes (5 restored, 14
deleted as absent at BASE) and every one verified by sha256 against `git show BASE:<path>`
BEFORE the capture; afterwards all 19 were restored from a held copy and verified again against
their HEAD sha256 (0 mismatches, `git status` clean, 0 files). Driven from Python, not shell
word-splitting — BD's B2075 is that `zsh` word-splitting produced a fake A/B that reported the
answer its author wanted.

**The new test file is reported separately, not folded in.**
`tests/research_infra/test_training_lane_protocol.py` does not exist at BASE, so including it in
the shared scope would have compared against an absent file (Session BD's B2073: passing new
files to both sides made the baseline unusable and only the tool's own refusal caught it).
Captured alone at HEAD: **62 passed, 0 failed, 0 errored.**

**Wider sanity, outside the receipt.** `tests/research_infra/` + `tests/scripts/` at HEAD:
**2096 passed, 7 skipped, 0 failed.** That sweep is what surfaced B2231.
