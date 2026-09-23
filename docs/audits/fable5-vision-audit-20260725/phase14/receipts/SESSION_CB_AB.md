# Session CB — scoped A/B against the parent commit

`CLAUDE.md` §6: no "no regressions" claim without an A/B. **0 bad → 0 bad, 0 regressed**,
on the scope this session's change actually reaches. The tool-emitted receipt with both
embedded captures is below; this header records what a reader needs to check it.

## Base

`4f92c90a6` — *"The train lane exists: outcome identity, a content-addressed cut, and a gate
that refuses March"* — is this session's own commit; the **before** side is its parent
`7b5cbf8d8` (the ratification commit), reconstructed by **copy-back, never `git checkout`**
(wave-11 §2). Both captures therefore report the same git HEAD and a dirty tree; that is the
copy-back signature, not an error.

The restore is sha256-verified: `src/research_infra/fast_engine/bench.py` came back at
`32de7ad1b1ca6416e521e8527b57c18a035b710b6bafa3af9c8bb89771bf9959`, byte-identical to the
copy taken before the swap.

## Scope

`python3 scripts/pytest_failset.py scope --base HEAD~1 --include-worktree` — 19 paths
changed, **10 test files** reached by import closure or path literal. Four of them are new
this session and do not exist on the before side, so the A/B is over the **6 shared files**
and the new ones are counted separately — the same treatment AW's, AQ's and AV's receipts
gave the same situation, and the reason `pytest_failset diff` refuses a mismatched scope.

```
# A/B'd (shared)                                        # new this session (counted separately)
tests/research_infra/test_fast_engine_accel.py          tests/research_infra/test_train_engine_accept.py
tests/test_gtos_context_os.py                           tests/research_infra/test_train_engine_cuts.py
tests/test_replay_acceleration_contract_split.py        tests/research_infra/test_train_engine_guard.py
tests/test_replay_acceleration_real_contract.py         tests/research_infra/test_train_engine_identity.py
tests/test_replay_acceleration_real_parity.py
tests/ultimate_book/test_packet_carry_vps_lineage.py
```

**New this session: 81 tests, 81 passed, 0 failed.**

## What changed

**No frozen or bound file was modified.** Every source change is an addition, plus three
additive edits to one unbound file:

| path | status |
|---|---|
| `src/research_infra/train_engine/{__init__,identity,cuts,guard,runner,accept}.py` | **new** |
| `src/research_infra/train_engine/README.md` | **new** |
| `src/research_infra/fast_engine/bench.py` | modified — two optional parameters (`installer_factory`, `extra_report`) and one added report field; all three additive, no existing behaviour changed |
| `tests/research_infra/test_train_engine_*.py` | **new** (4 files, 81 tests) |
| `docs/.../phase14/SESSION_CB_TRAIN_ENGINE_RESULT.md`, `phase14/receipts/*` | **new** |

**H1 (CLAUDE.md §3):** checked at session start and before each commit — 43 bound paths,
**2 non-matching, both the known unhydrated LFS pointers this worktree carries**
(`ULTIMATE_CANDIDATE_PACKAGE_SLEEVE_REGISTRY_LEDGER.jsonl`,
`SLEEVE_MEMBER_EXACT_JOIN_LEDGER.jsonl`), neither touched by this session. Unchanged across
the session. `bench.py` is **not** a bound path.

## The full-suite number, and the trap that fired for the third time

A **full-suite** capture in this worktree first reported **11 failed / 12,313 passed**,
against the committed ZERO baseline's 0 failed / 12,246 passed
(`docs/audits/fable5-vision-audit-20260725/receipts/FAILSET_BASELINE_MAIN.json`, commit
`6a0932acf`). The 11 were:

```
tests/test_b7_5_neutral_selection_factorial.py   (10)
tests/test_permissions.py::test_scheduler_v4_terminal_gate_carries_ultimate_candidate_package_shadow_packet  (1)
```

**None of them was reachable from this change, and that was measured before it was
explained.** The same 11 fail at the parent commit's tree by the same copy-back
(`11 → 11 bad, 0 regressed, 0 fixed`, byte-identical failure sets —
`CB_PREEXISTING_FAILURES.json`), they fail identically when the two files are run in
isolation, and neither file imports anything this session added.

**The cause was an unhydrated LFS pointer, and the estate had already recorded both the
trap and its repair — `IMPLEMENTATION_STATE.md` B2074**, where Session BD briefly attributed
18 failures to its own changes and found the same pointer. Applying B2074's documented repair
(object store is local, no network):

```bash
git lfs checkout research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/SLEEVE_MEMBER_EXACT_JOIN_LEDGER.jsonl
```

fixes **10 of the 11** — every `test_b7_5_neutral_selection_factorial.py` failure — and
brings H1 to **43 bound, 1 non-matching**, which is exactly the `drifted=1` steady state
B2074 documents.

**The 11th is left, deliberately.** `test_permissions.py::…shadow_packet` is fixed by
hydrating the *other* pointer, `ULTIMATE_CANDIDATE_PACKAGE_SLEEVE_REGISTRY_LEDGER.jsonl`
(CLAUDE.md H2 records exactly that). B2074's repair stops at one pointer and reports
`drifted=1`, so that is where this session stops too — and the second pointer is the one
carrying CLAUDE.md's standing **B905** hazard, whose safe handling is an integrator decision
made at the integrator's baseline, not a side effect of a feature branch.

### The full-suite number after the repair, and the two failures that WERE mine

Re-captured on the hydrated worktree: **3 failed / 12,321 passed / 124 skipped**. Two of the
three were caused by this session and are fixed:

```
tests/test_implementation_state_block_citations.py::test_no_new_dangling_block_citations
tests/test_implementation_state_block_citations.py::test_the_in_flight_wave_range_is_declared_and_shrinking
```

Appending blocks B2150–B2164 moved the block ceiling from B2075 to B2164, which turned BD's
`B2086` and `B2094` — forward-allocated and exempt while they sat above the old ceiling —
into dangling citations, **without BD having done anything wrong and without this session
having touched them**. AU's B1593 exposure exactly; `WAVE_11_WORKING_AGREEMENT.md` §5 puts it
on whoever raises the ceiling. Resolved as `KNOWN_GHOSTS` entries (BD's own result doc
identifies them as commit-subject range names and repoints readers at B2050–B2075; `B2086`
also sits inside an embedded `gtos-ab-receipt-v1` fence that must not be edited — the `B1976`
case), and CB's own `(2150, 2199)` in-flight entry dropped per the test's own remedy. See
`IMPLEMENTATION_STATE.md` B2165. **Nine block-citation tests green.**

**Residual: 1** — `test_permissions.py::…shadow_packet`, the second LFS pointer, above.

## A note on the copy-back itself

The first attempt at this A/B produced two empty captures and `usable_as_baseline=false`.
The cause was **`zsh` not word-splitting an unquoted variable**, so the whole file list
reached pytest as one argument and it exited with a usage error — the identical failure
`IMPLEMENTATION_STATE.md` B2075 records against AR §8.9, where it "produced a fake A/B that
reported the answer its author wanted". It was caught here only because `pytest_failset.py`
refuses an unparseable capture instead of returning an empty failure set. The captures
embedded below were re-run with literal paths.

---

# Session CB — scoped A/B against the parent commit

**0 bad → 0 bad · 0 fixed · 0 regressed. No regressions.**

Compared by **failure set**, not by count — counts are not portable across worktrees.

| | before | after |
|---|---|---|
| commit | `4f92c90a6` | `4f92c90a6` |
| captured (UTC) | 2026-07-31T04:27:13Z | 2026-07-31T04:25:59Z |
| working tree | dirty | dirty |
| failed | 0 | 0 |
| errored | 0 | 0 |
| **bad** | **0** | **0** |
| passed | 149 | 149 |
| skipped | 0 | 0 |

## Embedded captures

Embedded, not referenced. A receipt that points at a scratchpad path is as unverifiable as
no receipt at all, because that file is gone by the time anyone reads this.

```json
{
 "schema": "gtos-ab-receipt-v1",
 "scope": [
  "tests/research_infra/test_fast_engine_accel.py",
  "tests/test_gtos_context_os.py",
  "tests/test_replay_acceleration_contract_split.py",
  "tests/test_replay_acceleration_real_contract.py",
  "tests/test_replay_acceleration_real_parity.py",
  "tests/ultimate_book/test_packet_carry_vps_lineage.py"
 ],
 "before": {
  "commit": "4f92c90a6a08a3650c03430ec318938e3bd444b7",
  "commit_subject": "The train lane exists: outcome identity, a content-addressed cut, and a gate that refuses March",
  "captured_utc": "2026-07-31T04:27:13Z",
  "dirty": true,
  "totals": {
   "passed": 149
  }
 },
 "after": {
  "commit": "4f92c90a6a08a3650c03430ec318938e3bd444b7",
  "commit_subject": "The train lane exists: outcome identity, a content-addressed cut, and a gate that refuses March",
  "captured_utc": "2026-07-31T04:25:59Z",
  "dirty": true,
  "totals": {
   "passed": 149
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
