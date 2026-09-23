# Session AS — the scoped A/B receipt

Wave-11 agreement §2: *"A/B by copy-back, never `git checkout`; scoped `pytest_failset.py scope` at
HEAD; the committed baseline is ZERO — the full-suite A/B is the orchestrator's, once per train."*

> **Re-run after the adversarial pass.** The first version of this receipt covered 19 paths and 4
> test files, because nothing under `src/` had been touched. The pass then found a live
> `KeyError('trigger_r')` on the adopt path for four of the five armed sleeves, this session fixed
> it in `src/components/execution.py`, and the scope went from **4 test files to 52**. The figures
> below are the re-run.

## The change set

**21 paths: 18 new files, 1 modified source file, 2 append-only ledgers.**

| path | kind |
|---|---|
| `scripts/book_sleeve_telemetry.py` | new |
| `tests/ultimate_book/test_book_sleeve_telemetry.py` | new (28 tests) |
| `tests/ultimate_book/test_exit_contract_activation.py` | new (22 tests) |
| `phase11/FIVE_SLEEVE_OPERATOR_PAGE.md` · `phase11/EXIT_CONTRACT_ACTIVATION_DOSSIER.md` · `phase11/REPLAY_FLEET_MAP.md` | new, generated |
| `phase11/receipts/as_{live_basis,operator_page,exit_contract_activation,activation_dossier,fleet_map,repair_rows}.py` | new drivers |
| `phase11/receipts/{AS_LIVE_SLEEVE_BASIS_V1,FIVE_SLEEVE_STOP_CONDITIONS_V1,AS_EXIT_CONTRACT_ACTIVATION_V1,AS_FLEET_MAP_V1,AS_STAGES}.json` | new artifacts |
| `src/components/execution.py` | **modified** — the B1535 `KeyError('trigger_r')` fix, 1 read → 5 lines |
| `tests/ultimate_book/test_time_stop_rehydration.py` | new (14 tests) |
| `phase6/receipts/REPAIR_QUEUE_APPEND.jsonl` | append-only, 179 → 192 |
| `research/operations/trial_budget/TRIAL_LEDGER.jsonl` | append-only, +48 rows (session `AS`) |

**The two proposed exit-contract diffs are described and tested but NOT landed** — the tests apply
them in memory and restore, which is the only order in which `test_the_naive_mx_edit_is_a_noop` can
prove anything. The one `src/` change is the B1535 fix, which is a defect repair rather than a
proposal: `execution.py:3003` read `params["trigger_r"]` unconditionally against a
`_vnext_time_stop_params` that correctly returns no such key.

## The scope

```
python3 scripts/pytest_failset.py scope --base HEAD --include-worktree
  -> diff HEAD...WORKTREE: 17 path(s) changed
  -> scoped to 52 test file(s) reached by import closure or path literal
```

`execution.py` is what widens it: the closure now reaches `test_execution.py`,
`test_book_owner.py`, `test_exit_wiring.py`, `test_execution_manager_v4.py`,
`test_trade_management_cascade_fix.py`, `test_breach_flatten.py`, `test_order_route.py`,
`test_time_stop_units.py` and 41 others.

The comparison is over the **49 shared** files; this session's 3 new test files do not exist on the
before side and are counted separately — the same treatment AQ's receipt gave its two.

## Method

Copy-back, never `git checkout`:

1. every changed path copied to a hold directory with its sha256 recorded;
2. each tracked path restored to its HEAD bytes with `git show HEAD:<path>`, each untracked path
   removed — `git status` then reports a clean tree;
3. `capture` over the 49 shared files → the **before** side;
4. all 17 restored from the hold, **every one sha-verified against the pre-removal digest** (17/17
   `OK`);
5. `capture` again → the **after** side;
6. `diff`.

## Result

```
before c71297fa6: 0 bad
after  c71297fa6: 0 bad
unchanged: 0   fixed: 0   REGRESSED: 0

No regressions.
```

**0 bad → 0 bad, 0 regressed, 0 fixed.** Both sides: **1,474 passed / 10 xfailed / 0 failed /
0 errored**, byte-identical totals across a scope that includes every consumer of `execution.py`
the import closure reaches.

**+64 net new passing tests**, all green:

| file | tests |
|---|---:|
| `tests/ultimate_book/test_book_sleeve_telemetry.py` | 28 |
| `tests/ultimate_book/test_exit_contract_activation.py` | 22 |
| `tests/ultimate_book/test_time_stop_rehydration.py` | 14 |

And the B1535 fix is proved **both ways**: reverting it in place makes exactly the four `time_stop`
armed sleeves fail with `KeyError('trigger_r')` while `energy_agri` (`partial_be_runner`) keeps
passing — 5 failed / 9 passed — and the file restores byte-identical afterwards.

## H1 drift

**2 at session start, 2 at session end — unchanged.** Both are `UNHYDRATED-LFS`
(`ULTIMATE_CANDIDATE_PACKAGE_SLEEVE_REGISTRY_LEDGER.jsonl`, `SLEEVE_MEMBER_EXACT_JOIN_LEDGER.jsonl`),
which is the LFS hydration state of this worktree and not a seal break — CLAUDE.md H1's own caveat.
No bound file was touched. The session's `membership` stage measured that neither file either
proposed diff would touch is bound by R2, R1, `code_authority_paths`, or `config_file_hashes` — and
the same is true of `src/components/execution.py`, the one file this session did modify, so the
B1535 fix carries **no seal exposure**.

## One worktree change outside the change set

`git sparse-checkout add research/operations/broker_truth_layer_2026_07_29` — the route holding
`BROKER_TRUE_COSTS_V1_1.json` was absent from this worktree's sparse profile, so every cost-true
driver died on `CostTruthError`. This is AR's B1473 reproducing in a second worktree; it is filed as
a repair-queue row (`THE_SPARSE_CHECKOUT_GAP_REPRODUCED_IN_A_SECOND_WORKTREE`) with the fix being an
edit to the **committed** sparse profile so the next worktree does not pay for it again. Sparse-
checkout state is machine-local and not part of the diff.

## What this receipt does NOT claim

The full-suite A/B is the orchestrator's, once per merge train. This is the scoped comparison the
agreement asks each session for. It covers every test file the import closure of the change set
reaches, which for `execution.py` is substantial — but "no regressions in 52 files" is not "no
regressions in the suite", and the B1535 fix is a **live-path** change that the orchestrator should
see in a full-suite run before it is carried to a host.
