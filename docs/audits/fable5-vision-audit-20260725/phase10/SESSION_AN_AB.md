# Session AN — scoped verification receipt (agreement §2)

**Branch `phase10/population-rule`, merge-base `8db17b29c`.** Capture:
`phase10/receipts/SESSION_AN_HEAD_CAPTURE.json`.

## 1. Blast radius, named mechanically

```
python3 scripts/pytest_failset.py scope --base 8db17b29c --include-worktree
  -> 21 changed paths -> 23 test files by import closure and path literal
  escapes: []   unresolved: []   deleted_tests: []
```

Five `src/` files changed (`costs/spread_model.py`, `costs/model.py`,
`research_infra/walkforward/{spec,panel,era_population}.py`), three test files added or changed,
plus the audit tree, the repair queue and the trial ledger.

## 2. HEAD

| side | scope | result |
|---|---|---|
| **HEAD** | all 23 files | **478 passed / 2 skipped / 0 failed / 0 errored** |

**No merge-base capture is reported, and here is why that is the right answer rather than a gap.**
The agreement §2.2 says to name the blast radius, run it at HEAD, and *verify any suspicious
failure at the merge-base*. HEAD has **zero** failures and zero errors, so there is no suspicious
failure to verify: a merge-base capture could only show the same zero (the wave-9 baseline is
committed at `receipts/FAILSET_BASELINE_MAIN.json` as 0 failed / 0 errored) and could not change
any conclusion. Running it would also require a fresh worktree at the merge-base, which agreement §4
warns is not a usable A/B for tests reading sparse-excluded artifacts. The full-suite A/B is the
orchestrator's, once per merge train.

## 3. New and changed tests

| file | tests |
|---|---|
| `tests/test_spread_model.py` | **+5** (B1250 coverage repair), 1 strengthened (`test_recorded_era_on_a_tick_anchored_symbol_stays_measured` now asserts decidability explicitly), **1 rewritten** (`test_what_measured_coverage_exactly_means`, B1264) |
| `tests/research_infra/test_era_population.py` | **+16**, new file (14 + the 2 fail-open guards of B1267) |
| `tests/research_infra/test_published_seals_pinned_by_value.py` | **+7**, new file (B1253) |
| `tests/test_implementation_state_block_citations.py` | AN's `IN_FLIGHT_WAVE_RANGES` entry retired — B1250–B1266 are written, which makes the entry DEAD by the test's own definition; the test names that remedy in its own assertion message. AO's `(1300, 1349)` stays as a valid pre-declaration above the ceiling. |

## 4. The negative control that matters

**Every one of the five new B1250 tests was verified RED against the pre-repair logic.** Method: copy
`src/costs/spread_model.py` aside, restore the pre-repair `if fb is not None … / elif era_class …`
branch in place and delete the new one, run, then **restore by copy-back** — never `git checkout`,
which is how AL §9 silently lost an uncommitted edit.

```
at the OLD logic:   5 failed, 24 passed
at HEAD:            29 passed
```

The five: `test_the_204058x_band_no_longer_prices_as_measured`,
`test_no_undecidable_era_anywhere_reports_measured`,
`test_undecidable_never_strengthens_coverage`,
`test_measured_coverage_is_exactly_the_recorded_and_decidable_population` (since rewritten as
`test_what_measured_coverage_exactly_means`), `test_cost_r_carries_the_degradation_to_its_consumer`.

`tests/research_infra/test_published_seals_pinned_by_value.py` carries its own negative control
in-file (`test_a_substituted_seal_would_be_caught`), because the hole it closes is precisely a test
that passes against a substitution.

## 5. H1 and safety

- **H1 drift check: 2 UNHYDRATED-LFS / 0 DRIFTED.** Per `CLAUDE.md` §3's 2026-07-30 amendment that
  is a property of this worktree's LFS hydration state, not of any commit.
- **None of the five edited `src/` files is bound** by R2 — checked before editing, against the 43
  bound paths in `B7_5_POST_ACCELERATION_DECISION_CONTRACT_R2_VERIFICATION_SPLIT.json`.
- `config/agent_config.yaml`: **not written and not read for any live decision.** The research
  override `ultimate_book_include_clean3: True` reaches the generation port as a config *dict* via
  AA's own path, exactly as AL and AM used it.
- **No broker-capable script was run**; no broker module is imported by any receipt script; the VPS
  was never contacted; nothing was merged or pushed.
