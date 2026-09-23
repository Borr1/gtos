# r1 — A/B, per CLAUDE.md §6

**Change under test:** one optional kwarg (`entry_price`) on
`src/research_infra/walkforward/exits.py:replay`, plus two new files
(`walkforward/quote_side.py`, `tests/research_infra/test_quote_side.py`).

**Why scoped rather than full-suite.** Two reasons, both stated rather than assumed.

1. `scripts/pytest_failset.py` could not parse this run: the full-suite capture at
   `8dd9b07c0` returned `parse_complete: false`, *"recovered 0 ids but pytest reported 94
   (failed=50, error=44)"*, and stamped itself `usable_as_baseline: false`. A diff on it
   would have been a diff on nothing. The full-suite totals are recorded below as a
   snapshot, not used as a gate.
2. **This branch has concurrent writers.** HEAD moved from `937390d59` to `8dd9b07c0`
   mid-session and `src/components/broader_origin_generators.py` carries another lane's
   uncommitted edits. A ~11-minute full-suite A/B across that is not a controlled
   experiment; a 100-second one over the modules that can reach `exits.replay` is.

**Scope:** `tests/research_infra`, `tests/ultimate_book`, `tests/test_spread_composition.py`,
`tests/test_spread_model.py` — every test file that references `walkforward` (29 of them,
by `rg -l walkforward tests/`) plus the two spread-model suites the new module imports.

**Method:** BEFORE was produced by physically reverting the change
(`git checkout -- exits.py`, the two new files moved aside), not by reasoning about it.
Both arms ran the identical command; the restore was verified byte-identical afterwards.

```
python3 -m pytest -q --tb=no -rf -p no:cacheprovider --continue-on-collection-errors \
  tests/research_infra tests/ultimate_book tests/test_spread_composition.py tests/test_spread_model.py
```

| | failed | passed | skipped | xfailed | errors |
|---|---:|---:|---:|---:|---:|
| **BEFORE** (change reverted) | **11** | 3,367 | 28 | 2 | 2 |
| **AFTER** (change applied) | **11** | **3,394** | 28 | 2 | 2 |

**The two failure sets are byte-identical.** `diff` returns empty: **0 regressed, 0 fixed,
+27 net new passing tests** — exactly the 27 tests in `test_quote_side.py`.

The 11 standing failures are pre-existing and unrelated (8 × `FileNotFoundError` on
un-materialised sparse-checkout artifacts under `tests/ultimate_book/`, 2 ×
`test_trainer_partitions` / 1 × `test_builder_partition_safety` March-leak registry
assertions, 1 × a `gtos_command_center` import-shadowing test).

**Full-suite snapshot at the same tree (record only, not a gate):** 50 failed / 12,464
passed / 213 skipped / 31 xfailed / 44 errors, `/tmp/r1_after.json`.

**One environment change was made and it affects both arms equally:** two committed-but-
unmaterialised paths were hydrated into this worktree's sparse-checkout —
`research/operations/spread_model_2026_07_29` (dropped by a `git stash` earlier in the
session; the AG spread model this lane depends on) and
`research/operations/broker_truth_layer_2026_07_27` (never materialised; `costs.model`
refuses without it, which is what four `test_wf_diagnostics` failures were). No bytes were
regenerated; both are `git sparse-checkout add` of committed content.
