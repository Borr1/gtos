# Session AT — the tests that protect nothing, retired; the ones that protect something, named

**Wave 6.** Branch `phase6/test-triage`, from `main` at `eaafe085e`. Blocks **B900–B949**.

---

## 0. What Borhen asked for, and whether he was right

> can we just get rid of the tests that dont matter, as most of these 600 something issues arent
> real anyway, i dont want to keep doing this A/B i think it's silly and has no value

He was right, and the measurement is worse than the complaint. Of the 639 standing failures at `9fa65182c` (the same set the waves have been calling
"660-ish"; §6 explains the 25 that two data repairs had already removed):

| what it actually is | n | share |
|---|---:|---:|
| **absence of data** — a file that is not on disk | **419** | 65.6 % |
| **absence of a Python package** — three uninstalled dependencies | **46** | 7.2 % |
| code-shaped failure with no live symbol behind it | 138 | 21.6 % |
| **code-shaped failure on a path the live book reaches** | **36** | **5.6 %** |

**36 of 639.** Everything else was the suite reporting the state of a laptop's disk.

### The prior partition was wrong, and wrong in the direction that made the problem look smaller

`IMPLEMENTATION_STATE.md` **B372** partitioned the same set by exception class and put **197 under
"code-shaped — AssertionError"**. That over-counts code-shaped failures by **85** —
`absent_data_as_assertion` (58) plus `absent_data_as_stopiteration` (27) — because a large share of
those assertions are data absence in costume:

```
assert 0 == 386
  + where 0 = GTOSVNextEvidenceIndex(rows=(), scopes=(), rows_loaded_by_path={},
      missing_paths=('research\\science_program_2026_05\\...\\..._LEDGER_2026-05-16.jsonl',)).row_count
```

A loader returned nothing because the file is absent, and the test says `AssertionError`. Bare
`StopIteration` from `next(r for r in rows if ...)` over that same empty load is the same failure
a third time. Bucketing by **cause** rather than exception class moves 85 rows from "code-shaped" to
"absent data" and is the difference between "a third of the suite is broken" and "two thirds of it is
looking for files that are not there".

---

## 1. The measurement the deletions rest on

`CLAUDE.md` §8 permits deleting stale pollution **after proof**. The proof is reachability, and
getting it right took three attempts. All three are in `receipts/AT_TRIAL_LEDGER.jsonl`.

### 1.1 Module-level reachability is useless here

`run_book.py` imports `src/utils/config.py`, which imports `src/components/gtos_vnext_runtime.py`.
At module granularity that 18,090-line file is "live", and so are the ~300 tests that drive it.

At **symbol** granularity it is not. `src/utils/config.py:12` imports exactly two names:

```python
from src.components.gtos_vnext_runtime import (
    normalize_vnext_symbol_key,
    resolve_vnext_symbol_family,
)
```

Closure over (module, symbol) pairs: **the live book reaches 8 symbols of that module**, all of them
symbol-key normalisation. The legacy agent reaches **478**.

### 1.2 The entrypoint set was assumed, and the assumption was wrong

The first symbol closure was rooted at `run_book.py` and `run_agent.py`, which is what the
documentation implies. The VPS runtime snapshot says otherwise —
`vps-export-20260725/extracted/27_runtime_snapshot/processes_full.json`, 17 python processes
[MEASURED]:

| process | count |
|---|---:|
| `run_book.py` (two per account) | 4 |
| `.tools/monitor_books.py --loop 300` | 2 |
| `scripts/run_ai_companion_supervisor.py` | 2 |
| `scripts/build_runtime_learning_daily_advisory.py` | 2 |
| **`run_agent.py`** | **0** |

Two corrections fell out of that:

- **`run_agent.py` is not running.** It is launched by `start_all.bat`, per symbol, and no such
  process exists on the host. Every test whose only reachability runs through the legacy agent is
  therefore protecting a lineage nothing executes. This is what makes the `gtos_vnext_runtime.py`
  deletions safe: the failing tests drive `evaluate_vnext_route_event` and the CP281/moonshot rule
  enrichers, whose only caller is `src/components/orchestrator.py:2196,2413,8581,8777`, reachable
  only from `run_agent.py`.
- **Two live processes have no source in this repository.** `run_ai_companion_supervisor.py` and
  `build_runtime_learning_daily_advisory.py` exist only in the VPS export at `21_scripts/`. That is
  the live-lineage fork the second audit recorded, still open. Their first-party imports were read
  from the export and seeded into the closure; the closure then continues through **this** repo's
  `src/`, which is an approximation — Session S measured 25 of 519 shared `src/` files differ by
  sha256 between the trees (B292). **Declared, not hidden:** this is the one hole in the
  reachability model.

### 1.3 The keep side is deliberately coarser than the delete side

The first fallback rule scored each test by the symbols its **body** names, and proposed deleting
`tests/test_sl_beyond_ob_precision_aware.py` — four tests about NAS100 stop-loss floor precision —
because the bodies never name `apply_instrument_overrides`, which the file imports at module level.

Symbol-level reachability is an under-approximation: `getattr`, dynamic dispatch and fixtures are
invisible to it. So the final rule is asymmetric on purpose:

- **DELETE** requires zero live symbols **and** zero live modules **and** a named superseding authority.
- **KEEP** is triggered by either signal alone.

Erring on the keep side costs a line in a report. Erring the other way removes coverage from a module
the armed book imports.

---

## 2. What was done, per test, never per file

| disposition | n | what happened | still red after |
|---|---:|---|---:|
| **DELETE** | 504 | 504 test functions removed by AST span across 73 files; 45 files removed whole because the triage marked every test they define | **0** |
| **SKIP-WITH-REASON** | 93 | skipped by a `tests/conftest.py` hook, **only while the named input is absent**, with the restoring command in the reason | 25 |
| **KEEP-REAL** | 36 | left failing on purpose and filed below with `file:line` | 36 |
| **HYDRATE** | 6 | collection errors behind committed-but-unhydrated modules | 6 |

`67 = 36 + 25 + 6`, and every one of the 504 deletions left the failure set. The 25 are the
hook declining to act: their skip precondition is `.hermes/` being absent, and `.hermes/` is
present in this worktree, so the B7.5 campaign harness fails on specific missing evidence
inside it rather than on the tree being missing. **The hook refused to skip a test whose stated
precondition it could not verify**, which is the behaviour I want from it even though it leaves
25 red lines I would rather not have.

### 2.1 The two files carrying 43 % of the noise kept their live coverage

The instruction was not to delete a file wholesale to clear its failures. Measured outcome:

| file | failing, removed | **kept** |
|---|---:|---:|
| `tests/test_gtos_vnext_master_conversion_ledger.py` | 188 | **34** |
| `tests/test_gtos_vnext_runtime.py` | 111 | **192** |
| `tests/test_wave4r_v4_vs_v3_frozen_replay_results_gate.py` | 31 | 26 |

The trap was real and it is worth stating what it would have cost. `tests/test_gtos_vnext_runtime.py`
contains **15 prop-safe-selector tests** and **all 15 pass**. Not one of the 111 failures touches the
prop-safe selector, and not one touches either of the two symbol-normalisation functions the live book
actually calls. Deleting the file to clear 111 red lines would have removed 192 passing tests,
including the entire prop-safe selector suite, while FTMO is trading real money.

### 2.2 Hydration beat deletion where it was cheap

Seventeen failures in `tests/test_vnext_production_wiring.py` — all on the live symbol
`src/utils/config.py::apply_instrument_overrides` — were one absent 77.5 KB file. Hydrating its
directory (**4.1 MB, 138 files**) turned 17 failures into **15 passes and 2 real findings**. That is
the whole exercise in miniature: the noise cleared and signal appeared underneath it.

Hydration is **worktree-local** and does not survive into a fresh worktree — `.git/worktrees/<n>/info/sparse-checkout`
is not committed, and there is no bootstrap script in the tree that would re-apply it. The command is
recorded in `TEST_TRIAGE_V1.json` and the conftest hook names it in every skip reason, which is the
durable half.

### 2.3 Two repairs that were not deletions

- **An un-hydrated LFS pointer.** `SLEEVE_MEMBER_EXACT_JOIN_LEDGER.jsonl` was a 132-byte pointer;
  `json.loads` was reading `version https://git-lfs.github.com/spec/v1` and raising. `git lfs checkout`
  on that one path — **not** `git checkout`, that route is load-bearing by absence — fixed **10 of 11**
  failures in `tests/test_b7_5_neutral_selection_factorial.py`. Exactly the B185 case `CLAUDE.md`
  documents.
- **46 failures are three uninstalled packages.** `pytest-asyncio` (23), `fastapi` (12),
  `sentence_transformers` (11). Nothing is wrong with those tests. pytest itself has been warning
  about it the whole time — `PytestConfigWarning: Unknown config option: asyncio_mode` — because
  `pytest.ini` configures a plugin that is not installed. They are skipped with the `pip install`
  line in the reason rather than deleted, and **not installed by this session**: three other sessions
  were running full suites against the same interpreter, and adding a collection-time plugin to shared
  site-packages mid-flight would have altered their A/Bs.

---

## 3. KEEP — REAL: the 33 that protect something, and what they are saying

Filed rather than fixed where the fix is an owner call. These are the return on clearing the noise.

| finding | where | what it means |
|---|---|---|
| **A new broker-mutating call site is in the tree** | `tests/safety/test_activation_token.py:589` | The guard is working. The offender is a *snapshot copy* of `execution.py` vendored under `docs/audits/.../phase5/activation_carry/files/execution.py:9636`, not a live path. Repair is to exclude vendored snapshots from the scan, or drop the copy — but it should be a deliberate decision, because narrowing a safety scan is how the next real one gets missed. |
| **Mainline config is not armed, and a committed test asserts that it is** | `tests/ultimate_book/test_a8_live_activation_config.py:76` asserts `ultimate_book_live_activation_allowed is True`; `config/agent_config.yaml:1250` is `false` | The FTMO arming lives in the VPS's own config, not this repo's. Note for `CLAUDE.md` §4: its citation of "three gates at `agent_config.yaml:1161-1163`" refers to the **exported VPS** file; in this repository `:1161-1163` are `validation_anti_overfit_v4_*` keys and the ultimate_book gates are at `:1248-1250`. |
| **The redacted_account profile has outgrown the Stage-03 universe** | `tests/test_vnext_production_wiring.py:321` | 8 symbols carry risk overlays with no Stage-03 eligibility: `CADJPY, EU50_cash, FRA40_cash, LTCUSD, NZDJPY, US2000_cash, XPTUSD, XRPUSD` — the market-expansion families. Either the 2026-05 activation map needs superseding or the overlays are unbacked. Sleeve composition is Borhen's call. |
| **The live monitor universe no longer matches Stage-03** | `tests/test_vnext_production_wiring.py:429` | Same root cause. |
| **Armed-set MC control fails its own identity check** | `tests/test_armed_set_mc.py` → `mc_firm_rules.py:666` | `eff_risk_pct 1.453 vs 1.45`, `vol_scale 0.7264 vs 0.7248`, `mean_r_per_book_day 0.122 vs 0.12334`. Small, but it is a **control** — it is supposed to reproduce exactly. |
| **A live admission decision reports no runtime effect** | `tests/ultimate_book/test_market_expansion_runtime_generator.py:285`, `dec.runtime_effect_now is True` fails | On the `admission`/`bridge`/`book_owner` path the armed book uses. |
| **SPRT halt classes pin a set the config has outgrown** | `tests/test_sprt_class_halt_check.py:314,347` | Test expects `{metals, indices, jpy_pairs}`; config has `crypto`, `energy`, `tight_fx` too, and `GBPUSD` now appears in a list the test asserts it is absent from. |
| **A scheduler denial reason changed** | `tests/test_vnext_lane05_portfolio_scheduler.py:79` | `same_symbol_lifecycle_v4_hedge_conflict_rejected` → `..._source_required_fail_closed`. |
| NAS100 stop-loss floor | `tests/test_sl_beyond_ob_precision_aware.py` | `NAS100 resolved floor 0.01 < expected_min 0.1; tick_size pin removed?` — 4 tests, live symbol surface. |
| the rest (structure detector shadow, jsonl rotation, permissions, dual-broker follower, integration-live record) | see `TEST_TRIAGE_V1.json` | each has `file:line` and its live symbol recorded |

---

## 4. A hazard found on the way, which is not about tests at all

**The R2 decision contract's expected hash for one bound path matches an *uncommitted* file.**
[MEASURED]

`ULTIMATE_CANDIDATE_PACKAGE_SLEEVE_REGISTRY_LEDGER.jsonl` is LFS-tracked and bound by R2.

| | sha256 |
|---|---|
| pointer `oid` at HEAD (both trees) | `a5bcc0f8…` |
| this worktree after `git lfs checkout` | `a5bcc0f8…` |
| **R2 contract expects** | `19365f60…` |
| `/Users/borr/GTOSActive/repo` working copy — **`git status` reports it MODIFIED** | `19365f60…` |

The seal is satisfied only because the runner's `binding_roots` fallback chain ends at
`MAIN_REPO_ROOT = /Users/borr/GTOSActive/repo` and finds the dirty file there. **If that working tree
is ever cleaned or re-checked-out, the contract can no longer be satisfied from git**, and the parked
campaign's ~36-machine-hour option dies with it. Both files are the same length (205,754 bytes), which
is why nothing noticed.

This also **corrects `CLAUDE.md` H1's LFS caveat**, which says: *"The pointer's own `oid sha256:` line
is the contract's expected hash, so a pointer is positive evidence the content is intact."* For this
path that is false — pointer `a5bcc0f8…`, contract `19365f60…`. A reader following the caveat would
conclude "no drift" and be wrong.

Nothing was touched. The main repo was not modified; the contract was not regenerated.

---

## 5. Making the A/B cheap

`scripts/pytest_failset.py` gains `scope` and `capture --scope`, extending the existing instrument
rather than adding a second one.

`scope` maps a diff to the tests that can observe it, through two indices built in **1.9 s**: a
transitive first-party import closure per test file (786 modules), and a path/basename literal index
(2,565 entries) so a test that asserts on `research/.../LEDGER.jsonl` still runs when that ledger
changes even though nothing imports it.

It is **fail-safe by construction**. A `conftest.py`, a config file, a deleted test file, or any path
that resolves to neither a module nor a literal escalates the whole run to `tests/`. Under-scoping is
a silent false "no regressions"; over-scoping costs seconds. The scope and its justification are
written into the capture and surface in the receipt, so the next reader judges the scope instead of
inheriting it.

**Measured on this session's own instrument commit:** a diff touching `scripts/pytest_failset.py` and
one new file under `docs/` scopes to **1 test file** instead of 11,400 tests.

A second, larger saving fell out of the triage: **re-running only the standing failure set takes 94
seconds** (665 ids, reproduced exactly: 634 failed + 31 errors) against ~10.5 minutes for the suite.
`scope --standing <capture.json>` unions those files in, so a scoped A/B still sees a change that
fixes or breaks a pre-existing failure.

**Two cases still need the full suite, and the tool says so itself rather than letting you find out
later:** a branch that deletes tests (a deleted path cannot be passed to pytest on the after side, so
removals under-report), and anything on the escape list. This session is the first case, which is why
its own A/B below is full-suite.

### `KNOWN_LOAD_FLAKES`

See §6. Entries are added only on the evidence the docstring requires — failing at the base commit
too, or passing in isolation at the commit that "broke" it.

---

## 6. The A/B

Full-suite, by failure set, both sides. Receipt with embedded captures:
`receipts/SESSION_AT_AB.md`.

| | before `9fa65182c` | after `bbc6baccc` |
|---|---:|---:|
| failed | 608 | 58 |
| errored | 31 | 9 |
| **bad** | **639** | **67** |
| passed | 10,993 | **11,004** |
| skipped | 57 | 125 |

**639 bad → 67 bad · 572 fixed · 0 REGRESSED.**

Two things in that table matter more than the headline:

- **`passed` went UP, by 11.** A deletion branch cannot manufacture passes, so this is not the
  deletions. It is load-flake recovery: the before capture ran with three concurrent full suites
  on this machine and the after with fewer. `test_high_load_integration`, already a registered
  `KNOWN_LOAD_FLAKES` entry, is in the FIXED list. If `passed` had gone *down* by even one, a
  deletion would have taken a passing test with it, and a count-only comparison would never have
  shown it. That is the whole reason this A/B is reported as sets.
- **The before side is 639, not the 660–665 quoted for six waves.** The gap is the two data
  repairs (§2.3), which were applied to the worktree *before* the before capture on purpose, so
  that the A/B measures the deletions alone and not deletions-plus-hydration. Their own effect is
  measured separately: **664 → 639, 25 fixed** (10 from `git lfs checkout`, 15 from 4.1 MB of
  sparse hydration).

### `KNOWN_LOAD_FLAKES` — no new entries earned

Zero regressions means nothing new qualified. The docstring's bar is specific — a name only lands
there after failing at the BASE commit too, or passing in isolation at the commit that "broke"
it — and no candidate arose. The one load-sensitive name that moved,
`test_high_load_integration`, moved in the *fixed* direction and is already registered. **An
entry added without that evidence would make the next receipt look cleaner and be worth less**,
so the list is unchanged.

---

## 7. What I got wrong, and withdrew

1. **The first baseline was contaminated and was thrown away.** I started a full-suite capture and
   then hydrated LFS objects and a sparse-checkout path *while it was running*, and later edited
   `tests/conftest.py` during a second one. Both were re-run from a clean tree. The A/B in §6 is the
   third attempt; the first two are not cited anywhere.
2. **`rg -r` misuse**, the exact trap `WAVE_6_WORKING_AGREEMENT.md` §4 lists. Searching for
   `evaluate_vnext_prop_safe_selector` with `-r` substituted the pattern instead of searching, and the
   output claimed the callers were named `n`. Caught immediately, but it is trap #2 on the list and I
   walked into it anyway.
3. **The reason-extraction probe was wrong on 69 % of rows** before a self-check caught it (§1 of the
   commit message). The self-check — "does each row's traceback file match its node id's file?" — is
   the only reason it was not silently believed.
4. **The prompt's premise about `tests/test_gtos_vnext_runtime.py` is not right, and it does not
   matter.** It states the file binds to `research/full_matrix.jsonl`, `gate.jsonl` and
   `frozen_ready_action_runtime_rule_ledger.jsonl`. Those three strings appear only as fixture values
   inside synthetic `tmp_path` records, and none of the three is committed anywhere. The file's real
   binding is `research/science_program_2026_05/`. The disposition is unchanged.
5. **A docs-only diff escalated `scope` to FULL** on first implementation, which is the headline case
   the prompt asked for. Fixed: an all-inert diff now reports that no test can observe the change
   rather than emitting an empty scope or the whole suite.

---

## 8. What is left, honestly

- **The standing set is 67, not 0, and it was never going to be 0.** 36 are KEEP-REAL and red on
  purpose; 25 are the skip hook declining to act because its precondition is unmet; 6 are
  collection errors behind committed-but-unhydrated modules. The number is now small enough that
  a reader can hold the whole list, which is the actual goal — **660 was not a number anyone read.**
- **The biggest single item left is not in the 67 at all.** `tests/research_infra/test_moonshot_unified_execution_scorer.py`
  is **223 tests that have never collected**, and it counts as ONE failure. It imports
  `aggregate_reduction_rows` from a module where that name has never existed in any revision
  (`git log -S`, all refs), and the sibling import `aggregate_execution_rows` is missing from its
  module too — an unwritten API surface, not a rename. Two more files hide **95** and **18** tests
  the same way. Roughly **340 tests in this repository have never executed once**, and the standing
  count showed them as 3.
- **46 skips are one `pip install` away** from being real coverage again. Someone should install
  `pytest-asyncio`, `fastapi` and `sentence-transformers` and re-run; the skips un-skip themselves.
- **Hydration does not survive a fresh worktree.** A `scripts/gtos_hydrate_test_data.py` reading the
  HYDRATE rows out of `TEST_TRIAGE_V1.json` would fix that in about twenty lines. Not built here.
- **The reachability model has a declared hole**: two live processes whose source is not in this
  repository (§1.2).
