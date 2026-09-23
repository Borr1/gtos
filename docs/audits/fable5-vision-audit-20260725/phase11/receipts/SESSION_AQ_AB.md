# Failure-set A/B

**0 bad → 0 bad · 0 fixed · 0 regressed. No regressions.**

Compared by **failure set**, not by count — counts are not portable across worktrees.

| | before | after |
|---|---|---|
| commit | `436dbb5c7` | `436dbb5c7` |
| captured (UTC) | 2026-07-30T11:44:53Z | 2026-07-30T11:45:56Z |
| working tree | dirty | dirty |
| failed | 0 | 0 |
| errored | 0 | 0 |
| **bad** | **0** | **0** |
| passed | 401 | 401 |
| skipped | 1 | 1 |

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
  "tests/research_infra/test_candidate_family_v2_ratchet.py",
  "tests/research_infra/test_era_population.py",
  "tests/research_infra/test_fidelity_threshold_variant.py",
  "tests/research_infra/test_trainer_folds.py",
  "tests/research_infra/test_vig_trial_ledger_prospective.py",
  "tests/research_infra/test_walkforward_book_replay.py",
  "tests/research_infra/test_walkforward_family.py",
  "tests/research_infra/test_walkforward_gate.py",
  "tests/research_infra/test_walkforward_supply.py",
  "tests/research_infra/test_wf_diagnostics.py",
  "tests/test_spread_composition.py",
  "tests/ultimate_book/test_book_owner.py",
  "tests/ultimate_book/test_candidate_promotion_plumbing.py",
  "tests/ultimate_book/test_market_expansion_runtime_generator.py",
  "tests/ultimate_book/test_order_route.py"
 ],
 "before": {
  "commit": "436dbb5c741bbca9d5e19256a280c5c6edf93025",
  "commit_subject": "AQ: CANDIDATE_FAMILY_V4 declared \u2014 the 45 entry-convention cells, before any gate ran",
  "captured_utc": "2026-07-30T11:44:53Z",
  "dirty": true,
  "totals": {
   "passed": 401,
   "skipped": 1,
   "xfailed": 1
  }
 },
 "after": {
  "commit": "436dbb5c741bbca9d5e19256a280c5c6edf93025",
  "commit_subject": "AQ: CANDIDATE_FAMILY_V4 declared \u2014 the 45 entry-convention cells, before any gate ran",
  "captured_utc": "2026-07-30T11:45:56Z",
  "dirty": true,
  "totals": {
   "passed": 401,
   "skipped": 1,
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

## How this A/B was taken

**Scope.** `scripts/pytest_failset.py scope --base HEAD --include-worktree` resolved 21 test
files from the import closure of the changed paths. The two of those 21 that this session
ADDS — `tests/ultimate_book/test_time_stop_units.py` (45 tests) and
`tests/research_infra/test_gate_wipeout_signal.py` (7) — do not exist on the before side, so
the diff above is taken over the **19 shared files** and the tool refused the 21-file version
outright ("an A/B across different scopes is not a comparison"). The new files are counted
below as new passing tests, which is the only thing they can be.

**Method.** Copy-back, never `git checkout`. The three tracked files this session modifies
(`src/components/ultimate_book/execution_packets.py`,
`src/research_infra/walkforward/gate.py`,
`tests/ultimate_book/test_market_expansion_runtime_generator.py`) were restored to their
HEAD bytes with `git show HEAD:<path> >`, the two new test files moved aside, the before
capture taken, and then every one of the five restored from a sha256-verified copy. All five
hashes matched after the restore.

**Result.** 0 bad → 0 bad, 0 regressed, 0 fixed — the committed baseline is zero and stays
zero. **+52 net new passing tests** (401 → 453 over the 21-file scope).

**Not in scope, and deliberately.** The full-suite A/B is the orchestrator's, once per merge
train (wave-11 agreement §2).

## A wider check than the scope required

The 21-file scope above is what `pytest_failset.py scope` resolves from the import closure of
the changed paths, and it is the A/B of record. As a belt-and-braces pass over anything the
closure might not reach, both **entire** directories the change touches were also run at the
working tree:

```
python3 -m pytest tests/research_infra/ tests/ultimate_book/ -q -p no:randomly \
        --continue-on-collection-errors
2287 passed, 10 skipped, 2 xfailed, 2 warnings in 82.02s
```

**0 failed, 0 errored, 0 collection errors.** Both warnings are pre-existing and unrelated
(`asyncio_mode` config key, and `test_vig_walk_forward.py::test_stationary_edge_known_answer`
returning a dict instead of asserting).

## Reproducibility of the artifacts, which is a separate question from the tests

`aq_contract_truth.py --stage all` was re-run from a cold cache **after** the repair it
documents had landed. It reproduces its committed artifact exactly: **0 leaf differences
outside the `seconds` timing fields**, across the walk (15 arms) and admission (24 arms)
trees, and control C1 returns 2,086/2,086 again. That is what the frozen
`PRE_REPAIR_TIME_STOP_BARS` table and `AQ_AS_OF` are for — a measurement of a defect has to
survive the defect being fixed.

The comparator used for that check is **nan-aware**. A naive one reported 254 differences,
every one a `nan != nan` on `drop_best_retention` — the same trap Session AN caught in its own
work at B1266.

## Re-run after the adversarial pass's corrections

The corrections that pass produced touch `gate.py` (`_WIPEOUT_CLASSES` and the tie-break) and
add two tests. Both checks were re-taken against the same unchanged before-capture:

* scoped A/B over the 19 shared files: **0 bad → 0 bad, 0 regressed, 0 fixed**;
* both full directories at the working tree: **2289 passed, 10 skipped, 2 xfailed, 0 failed**
  (up 2 from 2287 — the two new tests pinning the dead-class and tie-break fixes).
