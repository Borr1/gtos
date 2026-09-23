# Red-suite classification — every failure assigned to a named cause

**Session C, Phase 1, 2026-07-26.** Branch `phase1/red-suite-deletion`, worktree
`/Users/borr/GTOSActive/worktrees/phase1-red-suite-20260726`, HEAD `acad79826`.
Evidence tags: **[MEASURED]** ran/observed here · **[VERIFIED]** read directly in code or sealed
artifacts · **[INFERRED]**.

This closes **Q4** — *"is the baseline mostly environment-bound or genuine?"* — the largest open
measurement question in the programme. The answer is **overwhelmingly environment-bound**, and the
mechanism is not the one two prior sessions assumed.

---

## 0. Baseline, and the phantom regression that is a method finding

| | failed | passed | skipped | errors |
|---|---:|---:|---:|---:|
| committed receipt @ `212ad7e6d` | 650 | 9,747 | 27 | 33 |
| **re-captured here @ `acad79826`** | **651** | **9,747** | **27** | **33** |

Set diff via `scripts/pytest_failset.py`: unchanged 683 · fixed 0 · **regressed 1** [MEASURED].

**The one regression is not a code regression, and the reason matters more than the test.**
`tests/test_permissions.py::test_scheduler_v4_terminal_gate_carries_ultimate_candidate_package_shadow_packet`
fails with `IndexError: list index out of range` at `tests/test_permissions.py:317`
(`package["selector_packets"][0]`). Its input,
`research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/ULTIMATE_CANDIDATE_PACKAGE_SLEEVE_REGISTRY_LEDGER.jsonl`,
is a **131-byte git-LFS pointer in this worktree** and 205,754 bytes in `/Users/borr/GTOSActive/repo`
[MEASURED]. The committed baseline was captured in a worktree where that pointer had been **hydrated
by hand** — `CLAUDE.md` H2 records the hydration as a side note.

> **`receipts/baseline_full_suite.json` is not reproducible from git alone: it encodes uncommitted
> working-tree LFS hydration state.** Any A/B run in a fresh worktree reports this as a phantom
> regression. Both LFS objects (`a5bcc0f8…`, `64fd1014…`) *are* in the local store, so
> `git lfs checkout` on those two paths repairs it — but the receipt should say so.

A second run captured per-failure reasons; it recorded **652** failed, i.e. one test in the suite is
non-deterministic beyond the known `test_high_load_integration`. Treated as noise, named in §6.

---

## 1. The environment, measured before any hypothesis

Every number here is from `git ls-files` / `git cat-file`, never from the filesystem — this worktree
materialises **5,500 of 29,822 tracked files** and `rg` cannot see the rest (F24 is exactly that
mistake) [MEASURED].

- **`/Users/borr/GTOSActive/repo` is ALSO sparse and also excludes `research/science_program_2026_05/`.**
  These failures are a property of *the machine*, not of this worktree.
- `filter.lfs.smudge` = `git-lfs smudge --skip`. Materialising an LFS-tracked path writes the
  **133-byte pointer**, never content.
- HEAD carries **4,142 LFS pointers, 67.65 GB declared**. The local store holds **1,031 objects /
  59.44 GB**. **3,295 objects (40.32 GB) referenced at HEAD are absent locally.**
- In the two directories the dominant tests read: `gtos_vnext_research_to_runtime_builder` **83 of 181
  tracked files are LFS pointers, 0 objects present**; `weekend_mechanical_edge_factory_moonshot_2026_05_15`
  **2,182 of 3,369, 0 present**; `main_orchestrator_24h_…` **0 of 1,156**.

That third bullet is the whole story of the 299, and it is why the prior materialisation experiments
failed to explain them.

**There are two LFS failure modes, not one, and conflating them would misread the deletion question.**
A reviewer refuted my first single-cause version, and reconciling the two measurements shows both are
right about different populations [MEASURED]:

| | pointer stubs | objects present locally | repair |
|---|---:|---:|---|
| **materialised** in this worktree (the smudge-skip left stubs at checkout) | **97** | **97 / 97** | `git lfs checkout` — free, offline |
| **sparse-masked** under `research/science_program_2026_05/**` | 2,265 in the two dominant dirs | **0** | 2.05 GB fetch from GitHub |

So "the input is an LFS pointer" is *not* evidence that a test's input is gone. Where the object is in
the shared store (`git rev-parse --git-common-dir` is the primary repo's `.git`), the failure is
worktree-local and one command from repaired. Only the masked science-programme tree is genuinely
unavailable on this machine.

---

## 2. The 299 — what two prior sessions could not close, closed by experiment [MEASURED]

B10 materialised two directories and compared **counts** (wrong method). B11 materialised all
`SCAN_ROOTS` (5.3 GiB, 20,985 files) and compared **sets**: 299 → 271, i.e. **29 fixed**. Nobody could
explain the other 270.

**The missing variable is git-LFS, not sparse-checkout.** A surgical experiment settles it without
materialising anything, in three steps, on
`test_batch_wave_converts_ready8_context_risk_rules` — the test the prior sessions named as their open
probe. Its wave has exactly five member artifacts.

| state | `len(wave_units)` | result |
|---|---:|---|
| as shipped (all 5 masked) | **0** | `assert 0 == 5` |
| + the 2 **inline** members written from their HEAD blobs | **2** | `assert 2 == 5` |
| + the 3 **LFS-pointer** members written exactly as `git sparse-checkout` would write them | **5** | passes the count, then fails **further down** on a different assertion |

Three findings fall out, and the third is the one that mattered:

1. **One artifact → one ledger row.** The causal link between artifact absence and the failure is now a
   measurement, not an inference.
2. **The three LFS members cannot be hydrated on this machine.** They are 131/131/129-byte pointers
   whose objects are absent from the local store. Fetching them means 2.05 GB from GitHub for these two
   directories alone.
3. **Materialising makes it worse, not better.** The builder never raises on a pointer — it *silently
   lies*. `_read_json_object` swallows `JSONDecodeError` and returns `{}`
   (`scripts/build_gtos_vnext_master_conversion_ledger.py:3837-3841`); `_count_nonempty_lines` counts the
   pointer's three lines. So a pointer-backed artifact yields `row_count: 3` where the test wants 143.
   **That is why B11's full materialisation fixed only 29:** it converted `FileNotFoundError` into
   wrong-number assertion failures across the pointer-backed majority.

The sparse-checkout config was restored byte-for-byte; SHA
`d2a9676ba216caa74794b5b803b9615e37ace12f46e69b066acc726edac60c1c` before and after, `git status` clean
apart from the preflight's own `.context/LIVE_STATE.md` [MEASURED].

**This is why the full materialisation experiment was NOT re-run.** Its outcome is now predictable per
artifact, it costs 5.6 GB on a disk at 92 %, and B11 already paid for the generic version. What was
missing was never scale — it was the LFS variable.

---

## 3. Cause register — all 652 failures and 33 errors

### 3.1 `tests/test_gtos_vnext_master_conversion_ledger.py` — 188 [MEASURED]

Reproduced exactly: 188 failed / 33 passed. Every one is the same root cause — *the artifact the row
depends on is tracked but not in the checkout* — surfacing in four shapes:

| n | shape | mechanism |
|---:|---|---|
| 90 | `FileNotFoundError` | test opens a masked artifact directly. **100 % of the 90 paths are tracked-but-absent**; 13 of them are LFS-pointer-backed |
| 70 | `assert 0 == N`, `assert []`, `KeyError` | asserts over `build_rows()` output whose source is masked; drop site `…:30250-30251` |
| 27 | **`StopIteration`** | `test_batch_wave_converts_*` does a bare `next(item for item in waves if …)`, so a missing wave never mentions a file |
| 1 | `KeyError: 'row_count'` | **genuine defect** — `iter_current_wave_long_path_source_files` (`…:30282`) yields a row with **no `exists()` guard**, so `classify_artifact` cannot count lines |

**Both named suspects are exonerated by measurement, and this corrects the prior art:**

- `_is_non_material_handoff_source_name` (`…:30236`) filters **exactly 0 files** — of all 29,822 tracked
  paths, **zero** match its regex.
- The `MOONSHOT_REPO`/`MOONSHOT_ROUTE` Windows-path defect (`…:40-43`) removes **zero rows**. `Path("")`
  is `PosixPath('.')` and *does* exist, `MOONSHOT_ROUTE` with literal backslashes does not, and
  `_git_ls_files_with_blob_hash` (`…:30215`) normalises `\`→`/` at the git boundary. Net effect: the
  block at `…:30260` is dead, and `…:30286-30288` re-adds 24 hollow rows for files not on disk. Dead
  and, when the tree is materialised, harmless.

**Probe 3's premise is falsified.** `NON_MATERIAL_HANDOFF_SOURCE_PATTERNS` (`…:60-62`) is *not* what
made `test_non_material_resume_handoff_is_not_added_to_execution_denominator` fail when files exist.
The eight files it was written for were deleted in `c680e99bc` (2026-05-20); zero tracked paths match
it; `excluded_names` is always empty and the test passes. The real "fails only when files exist" cause
was the pre-fix `_long_path_text` reached through `build_rows` (`…:33789-33791`): **58 of 67
`MANUAL_UNITS` resolve to ≥240 characters from this worktree**, so materialising them made
`sha256_path` hand `open()` a `\\?\/Users/...` string and the whole module died. `d2bb4448e` already
fixed it.

Two side findings, both the same half-done Windows→POSIX conversion: `build_rows()` is cwd-dependent and
raises `CalledProcessError` outside a git repo; and `tests/…:1199` asserts
`unit["source_artifact_path"].startswith("")` — **vacuously true**, because the argument used to be
`MOONSHOT_REPO`.

**Label: environment-bound in cause, stale in consequence.** 187 environment-bound, 1 genuine
(the missing `exists()` guard) — and all of it dies with the 2026-05 route it measures.

### 3.2 `tests/test_gtos_vnext_runtime.py` — 111 [MEASURED]

**Verdict: ZERO routing regressions in `src/components/gtos_vnext_runtime.py`.** By the probe's own
partition, 109 of the 111 present as artifact-absence — but 36 of those are a POSIX-unresolvable path
literal that no amount of hydration fixes, so the honest split is **73 environment-bound / 38 genuine
defect, all 38 test-side with production verified correct**.

The framing premise — "many fail with `assert 'LEGACY' == 'FOLLOW'`" — is false: **exactly one** does,
and four fail on a LEGACY outcome at all. The decider is a counterfactual through the identical code
path: `tests/test_gtos_vnext_runtime.py:6054` builds its rows **in-line**, runs `evaluate_vnext_event`,
asserts `FOLLOW`, and **passes at HEAD**. Re-running the one `'LEGACY' == 'FOLLOW'` scenario against a
synthetic ledger at a tmp path returns `FOLLOW` (r=4.5, n=12) and `AVOID` (r=−4.5, stress=−3.0) with
`reason=matched_vnext_scope`, satisfying every assertion. Only file existence changed.

| n | sub-cause | label |
|---:|---|---|
| **71** | POSIX artifact-path constants, masked (67 `FileNotFoundError` before any runtime call, 2 `AssertionError`, 2 `KeyError`) | environment-bound |
| **36** | **Windows-backslash path literals** `Path(r"research\science_program_2026_05\…")`. `_local_path_exists` (`src/components/gtos_vnext_runtime.py:171-179`) does no separator translation and returns `False` on POSIX. **These stay red on macOS no matter what is hydrated** | **genuine defect (test-side), unfixable by hydration** |
| **2** | loads real `config/agent_config.yaml` `artifact_paths`: 162 configured, 0 loaded | environment-bound |
| **2** | fixture drift; production correct — a `partial_be_runner` fixture takes the exact-match branch (`…:16848-16849`) instead of the bridge branch the assertions expect, while the **production allowlist has 1,302 of 1,302 rows on the branch that works**; and a diagnostic list that faithfully reports a 2-element session-candidate set the assertion under-reports | genuine defect (test-side) |

**The mechanism is a designed fail-closed guard, not a bug.** Under the real config, `config/agent_config.yaml:3196`
sets `min_loaded_evidence_rows: 50000` and the comment at `:3193-3195` names this exact scenario —
*"prevents Git-LFS pointer files, missing heavy local artifacts, or truncated ledgers from producing
FOLLOW/AVOID decisions from partial evidence."* With 0 rows loaded the runtime returns
`decision="LEGACY", reason="vnext_evidence_index_below_min_loaded_rows"` (`…:9048-9061`).

**One live-adjacent observation to carry forward, and it is not a defect.** On any host without the
evidence tree, the vNext runtime returns LEGACY for *every* event under production config, and
`legacy_blocks_execution: false` (`config/agent_config.yaml:3188`) means LEGACY = "no vNext opinion,
fall through to legacy". `src/components/orchestrator.py:952/:1057/:5495` does reach these paths and
`config/agent_config.yaml:611-620,634` has them enabled. So the orchestrator's entire vNext routing
influence evaporates silently on a host with no evidence tree, and the only signal is the `reason`
string in `shadow_logs/gtos_vnext_runtime_decisions.jsonl`. **Worth checking on the VPS** — the
follow-up export can answer it in one grep.

### 3.3 `tests/ultimate_book/` — 60, and this block is the actionable one [MEASURED]

27 files × 2 + `test_wave_c_manifest_ohlcv_source.py` × 3 + three singletons = 60.

| n | named cause | label |
|---:|---|---|
| **56** | The route the test asserts against has **0 files tracked at HEAD** — it exists only on the live-lineage refs. `git ls-files research/operations/ \| grep -c 2026_06_18` = **0**; the same 27 routes exist on `origin/vps/ultimate-conditioned-expansion-minimal-2026-06-18` as **497 files / 48.5 MB** | environment-bound — **vendorable** |
| **3** | `final_moonshot_wave_b_…` and `final_moonshot_wave_c_…` exist on **no ref at all** | stale / unrecoverable |
| 1 | `test_book_engine.py` — see §6 | see §6 |
| 1 | `test_a8_live_activation_config.py` — see §6 | see §6 |
| 1 | `test_market_expansion_runtime_generator.py` — see §6 | see §6 |

This is the same shape as B15 (`test_vendor_parity`, fixed by Phase 0 item 0.2 vendoring 661 files) and
it is the **cheapest live-surface win in the whole baseline**: 48.5 MB of evidence turns 56 failures on
the *declared live decision surface* green. Recorded as a recommendation, not executed — it is a
vendoring decision, not a red-suite repair.

### 3.4 `tests/test_wave4r_v4_vs_v3_frozen_replay_results_gate.py` — 31 [MEASURED]

**Not missing artifacts.** All 31 observe exactly one selector verdict:
`action=reject, reason=broker_net_cost_authority_not_executable:missing`. The module hands the selector
a synthetic proxy cost model (`wave4r_…gate.py:3880-3886`, `expected_total_cost_r: 0.03`) and never sets
`cost_authority`; `src/components/selector_v4.py:1966-1970` requires
`cost_authority == "broker_calibrated_replay_cost"` and hard-rejects otherwise.

Neutralising *only* the selector reject still left 31 failing — the allocator vetoes independently with
`broker_cost_packet_status_missing_not_executable`. Two enforcement points, one root gap.

**Label: stale, dies with its code.** `src/research_infra/wave4r_v4_vs_v3_frozen_replay_results_gate.py`
has exactly one importer in the whole tree — its own test. Two caveats stated precisely: the sibling
`wave4r_replay_microstructure.py` **is** live research code
(`src/research_infra/v4_timewarp_simulated_live_research_loop.py:180`,
`src/research_infra/v4u_ordered_path_hydration.py:24`), so the `waveN*` family is **not** uniformly
dead; and `src/components/ultimate_book/convergence_replay_matcher.py:24-25` points at wave4r route
outputs that are **absent from the index** — a dangling pointer worth its own line in the manifest.

This is the selector **correctly failing closed** on a proxy cost model, not a selector defect.

### 3.5 `tests/test_vnext_production_wiring.py` — 17 [MEASURED]

17/17 identical: `FileNotFoundError` on the sparse-masked
`…/vnext_moonshot_production_replacement_activation_2026_05_26/VNEXT_REPLACEMENT_MARKET_SOURCE_ACTIVATION_MAP_2026-05-26.json`
at `tests/test_vnext_production_wiring.py:40`. `git ls-files -v` returns `S`; the blob is 79,357 bytes of
real JSON; `git check-attr filter` is `unspecified` — **not LFS**. Hydrating it: **15 of 17 pass**.

The 2 that remain are stale assertions, not defects: a profile-overlay superset check
(`tests/…:321`) that the profile has since outgrown, and an **order-sensitive list compare**
(`tests/…:429`) whose sets are equal.

**The prior audit classified these 17 as "live surface". That is wrong, and the evidence is specific:**

- `scripts/run_book_supervisor.ps1:86-108` launches exactly two `run_book.py` processes and nothing else.
- Grepping the live book (`src/components/ultimate_book/*`, `run_book.py`,
  `ultimate_book_live_package.py`) for the asserted config sections: `kill_zones` 0, `correlation_group`
  0, `sprt` 0, `economic_calendar` 0, `news_filter` 0, `session_windows` 0, `trading_enabled` 0. Only
  `mt5_symbol` is consumed, via `src/components/ultimate_book/symbol_map.py:33-40`.
- **The asserted universe is the wrong universe.** Stage08 eligible = 24 symbols; the live W7 book
  (`ultimate_book_live_package.py:214-239` minus `drop_w7_symbols`) = 25. **Overlap 16.** The tests
  enforce coverage of 8 symbols the live book never trades and never check 9 it does.

**Label: environment-bound (15) + stale (2). Nominal, not live surface.**

Two live-relevant findings this file structurally cannot see, recorded for whoever owns the profile work:
6 live W7 symbols have **no `instruments[]` block** in `redacted_account.yaml` (`CORN_c, COTTON_c, XAGAUD,
XAGEUR, XAUAUD, XAUEUR`), so `book_engine.py:430-431` silently skips them with
`profile_missing_instrument_config`; and `scripts/_live_monitor_iter.py:28` hardcodes
`Path(r"C:\Users\MSI\Documents\ai-trading-agent")`, so on this laptop `load_monitor_universe()` returns
`FALLBACK_INSTRUMENTS` and the assertion named "…is_config_derived…" passes off a hardcoded constant.

### 3.6 `tests/test_master_research_queue_state.py` — 13 [MEASURED]

13/13 identical: `FileNotFoundError: 'research/ml_program/MASTER_BACKLOG.md'` at
`scripts/build_master_research_queue_state.py:72`. `git ls-files -v` → `S`; blob is 62,158 bytes of real
markdown; not LFS. Hydrating it plus the also-masked
`research/phase_3_external_feed_validation/PHASE3_DEFERRED_TASKS_AND_NEXT_STEPS_LEDGER_2026-05-02.md`:
**16/16 pass**. **Label: environment-bound, no defect whatsoever.**

### 3.7 The 33 collection errors — classified for the first time [MEASURED]

| n | named cause | label |
|---:|---|---|
| 10 | `TestVectorDB` class fixture `tests/test_knowledge_base.py:523-524` imports `sentence_transformers` — declared at `requirements.txt:10`, not installed | environment-bound |
| 12 | `TestDashboardEndpoints` fixture `tests/test_monitoring.py:201-203` → `src/components/dashboard.py:12` imports `fastapi` — `requirements.txt:17`, not installed | environment-bound |
| 1 | `tests/test_chart_renderer.py:7` → `src/utils/chart_renderer.py:15` imports `plotly` — `requirements.txt:13`, not installed | environment-bound |
| 5 | sparse-masked route module (`test_vnext_absolute_moonshot_lane16…`, `…scheduler_v3`, `…ftmo_local_profile…`, `…lane10_portfolio_scheduler_v2`, `…lane10b…`) | environment-bound |
| 2 | **`src/research/__init__.py` shadows the top-level `research` namespace package** | **genuine defect** |
| 1 | `tests/research_infra/test_moonshot_unified_execution_scorer.py:725,730,758` imports 11 names that **never existed** in the `src/` modules — the test was written against a route script's API | genuine defect |
| 2 | April-2026 ADR programmes with null results and no consumer (`test_a1_analyze.py` → ADR-005, `test_retest_geometry_study.py` → ADR-003) | stale, dies with its code |

**Correction to prior art: C11's "~23 failures attributable to missing `pytest-asyncio`" does not touch
the error list at all.** Zero of the 33 are pytest-asyncio; none of the 13 implicated files contains a
single `async def`. The 23 are `sentence_transformers` + `fastapi` + `plotly`, three packages declared
in `requirements.txt` and blocked by the same PEP-668 constraint. C11 belongs entirely to the `failed`
list, and its attribution there is still unverified.

**The finding worth acting on — `src/research/__init__.py`.** [MEASURED, verified independently]
That file (87 bytes) makes `src/research` a **regular** package. Four test modules insert `<repo>/src`
at `sys.path[0]` at import time (`tests/research_infra/test_vig_regime_inflation.py:23`,
`test_validation_integrity_gauntlet.py:36`, `test_vig_perm_null.py:20`, `test_vig_trial_budget.py:17`)
and they all pass, so nothing points at them. From then on `import research` resolves to
`src/research/__init__.py` and `research.operations` is unreachable for the rest of the process.

Blast radius, measured: `tests/test_b7_5_post_acceleration_contract.py` is **1 failed / 26 passed**
standalone and **5 failed / 30 passed** when preceded by one poisoner. That is the decision-contract
test for the **current** B7.5 programme. Total cost: 2 errors + 4 failures.

**The fix is one deletion and it is validated.** Removing `src/research/__init__.py` makes `research` a
namespace package with both portions; a sandbox reproduction confirms `research.operations.*` and
`src.research.*` both keep importing. `src/research/__init__.py` is **not** R2-bound (only
`src/research/moonshot_scheduler_v4_best_trade_allocator.py` is). Recorded, not landed — see §7.

### 3.8 The remainder — 232 records, and the three genuine defects inside it

453 of the 685 records were attributed mechanically from their own reason string (a path that is
tracked-but-absent is an environment fact, not an opinion). The remaining 232 went to probes: 140 to the
two dominant-file investigations above, and 92 to three finder agents given the cause register and told
to add keys only where nothing fitted. **Seven new keys came back**, and every one of them names a
failure mode the register did not have:

| key | label | meaning |
|---|---|---|
| **C19 — lfs-smudge-skipped-worktree** | environment-bound, **worktree-local** | the on-disk file is a ~132-byte stub because this worktree was checked out with `filter.lfs.smudge = git-lfs smudge --skip` — but the object **is** in the shared store and the primary checkout has it hydrated. `git lfs checkout` repairs it offline. Distinct from C2, where the object is genuinely absent |
| **C20 — tombstoned module API** | stale, dies with its code | the dependency still exists at HEAD but was deliberately reduced to a no-compatibility stub by owner override, and its API moved. `run_broad_live_as_if_replay_harness.py:2-7`: *"This path intentionally has no import or execution compatibility surface."* The importing builder and its tests were never retired with it |
| **C21 — py3.14 argparse `%` in help** | **genuine defect** | an unescaped `%` in an argparse `help=` string. CPython 3.14 validates help strings inside `add_argument`, so the parser cannot be constructed and **every** invocation dies, not just `--help` |
| **C22 — wall-clock-aged fixture** | stale (time-bound) | a synthetic fixture pinned to an absolute start date ages out of a production freshness window as the calendar advances. Deterministic at any given date — **not** C15 — but permanently red after a computable threshold. Two instances, one of which is L1 in §4.1 |
| **C23 — py3.14 no implicit event loop** | environment-bound | a **synchronous** test calls `asyncio.get_event_loop()` with no running loop; 3.12 deprecated implicit creation and 3.14 raises. Distinct from C5, which is the missing plugin refusing `async def` test functions. One line (`asyncio.run`) |
| **C24 — never-green assertion** | genuine defect (test-side) | the assertion has never matched production — verified red at its own introducing commit by reading the source there. No drift, no regression: it encodes an intended contract that was never implemented. `tests/test_shadow_observer.py:157` asserts `promotion_verdict` on a JSONL row that only ever carried it in the *status* payload (`shadow_observer.py:191` vs `:428-444`) |
| **C25 — dead-PID assertion** | stale | the assertion binds a hardcoded OS process id captured during one live observation session. `PROTECTED_LEGACY_PID = 34389` (`replay_acceleration_final_route_decision.py:27`) is probed with `ps -p` at `:209-224`; that process is long gone, so the branch is hardwired false. Unreproducible by construction |

### 3.9 Genuine defects on code that is NOT queued for deletion — verified independently

These are the highest-value output of half one. All three were reported by a probe and then re-checked
by me directly, because a session that takes agent reports at face value is how this programme has
produced its wrong answers.

**D1 — `scripts/research/run_k51_decayed_components.py` cannot run at all on this interpreter.**
`:114` has `help="Bootstrap resamples per window for the 95% CI. 0 disables."`. Reproduced:
`python3 scripts/research/run_k51_decayed_components.py --help` → `ValueError: badly formed help string`
from `argparse.py:1750 _check_help`. `_build_arg_parser()` raises before `main()` parses anything, so
**every** invocation is fatal, not just `--help`. One character (`95%%`). [MEASURED]

**D2 — the BUG #28 regression guard for live stop-loss handling has never actually executed.**
`tests/test_trade_management_cascade_fix.py:282` injects broker rejection on
`request.get("action") == 2`, but the SLTP request is built with `TRADE_ACTION_SLTP = 6`
(`src/mt5/mt5_interface.py:64`, sent at `src/components/execution.py:9680`). Verified by reading both
constants. The probe demonstrated the consequence by mutation: with `2` the stub never fires, MockMT5
succeeds and the retry-and-leave path is never entered; with `6`, six `order_send` calls are all
rejected `10011`, the stop stays at `214.89` and the position stays open — i.e. **production
`_move_sl_to_breakeven` (`execution.py:9543-9634`) is correct and honours the documented contract**, and
the only thing wrong is that the guard protecting live execution code is inert. This test covers
`src/components/execution.py`; it is not queued for deletion. One line (`2` → `6`) converts a dead test
into a real regression guard. [VERIFIED]

**D3 — `src/research/__init__.py`, §3.7.** 2 errors + 4 failures, on the current programme's contract test.

**None of the three is landed here.** Each needs a whole-suite A/B to claim no regressions, and each
would move the failure set this document is measuring. They are recorded with their exact fix so a
follow-up session can land them cheaply.

### 3.10 One thing the owner should see, which is not a defect

`tests/ultimate_book/test_a8_live_activation_config.py:76` asserts
`ultimate_book_live_activation_allowed is True`. **That test only goes green when the live broker gate
is open.** `config/agent_config.yaml:1250` currently has it `false`, which is why it is red.

Given B26 — no halt flag exists anywhere on the VPS, the supervisor task is Running, both terminals are
connected and `trade_allowed` is true, so **one YAML boolean is the entire brake** — a test suite that
treats "gate armed" as the expected state is a hazard of its own. It is a standing invitation for a
future session to "fix the failing test" by flipping the gate. Worth an owner decision independent of
anything in this document.

---

## 4. Roll-up — all 685 records

453 attributed mechanically from the reason string, 92 by finder agents over the residue, 140 by the two
dominant-file probes. **Nothing is unattributed.**

| group | records | environment-bound | genuine defect | stale, dies with its code |
|---|---:|---:|---:|---:|
| `test_gtos_vnext_master_conversion_ledger.py` | 188 | 187 | 1 | 0 |
| `test_gtos_vnext_runtime.py` | 111 | 73 | 38 | 0 |
| `tests/ultimate_book/**` | 60 | 54 | 1 | 5 |
| `test_wave4r_v4_vs_v3_frozen_replay_results_gate.py` | 31 | 0 | 0 | 31 |
| `test_vnext_production_wiring.py` | 17 | 15 | 0 | 2 |
| `test_master_research_queue_state.py` | 13 | 13 | 0 | 0 |
| all other files (232 failures + 33 errors) | 265 | 188 | 28 | 49 |
| **total** | **685** | **530 (77.4 %)** | **68 (9.9 %)** | **87 (12.7 %)** |

**Q4's answer: the baseline is 77 % environment-bound, 13 % stale, and the genuine 10 % is almost
entirely test-side.** Of the 68 genuine defects, **36 are one defect** — the Windows-backslash path
literals in a single test module — and the rest are fixtures that drifted from a production path this
investigation then verified correct. The count of genuine defects found **in the live decision path is
zero**. The four real repo defects are §3.9's D1 (a research script's argparse string), D2 (an inert test
guard), D3 (`src/research/__init__.py`, a packaging file) and one missing `exists()` guard in a research
builder.

That is the honest headline, and it is the opposite of what a 652-failure suite looks like from outside.

### 4.1 The live-surface findings, which are worth more than the counts

Three came out of the classification and none of them is a failing test's own subject:

**L1 — the live book's only non-vacuous engine test has been dead since 2026-07-14T20:00Z.**
`tests/ultimate_book/test_book_engine.py::test_engine_gates_on_produces_realized_units_for_crypto` is the
sole test in that file asserting a **non-zero** intent (`:72`, `:77`). Its fixture is pinned to
`t0 = datetime(2026, 6, 1, …)` with 4 h bars (`:15,:23`); 261 bars put the last close at
2026-07-14T12:00Z, and the decision-bar recency guard at
`src/components/ultimate_book/book_engine.py:485` (`> 2 * ivl * 60`) then drops every symbol slot. Proved
by pinning `now_utc` to last-bar-close + 1 min: **2 intents appear** (`crypto`/`BTCUSD`,
`stop_dist=703.16`).

The consequence is worse than one red test: **the other 12 tests in the file pass, and two of them assert
`n_intents == 0`** (`:94`, `:105`) — which they now satisfy vacuously. **Any regression in `ultimate_book`
intent generation after mid-July is invisible to this suite**, and `ultimate_book` is the declared live
decision surface (`config/agent_config.yaml:1246-1394`). This is B13's time-bomb, in a file B13 did not
check.

A second breakage is stacked behind it: with the clock pinned, the test still fails because `_cfg()`
(`:41-56`) never sets `ultimate_book_live_broker_authority`, so the engine returns
`decision_status="shadow_live_broker_authority_false"` with `realized_units == []` while still computing
the shadow projection correctly (`would_total_risk_pct = 0.0079475`). **That is an independent,
runtime-side confirmation of B26**: one YAML boolean is the sole gate on realized units.

**L2 — Gate 3's vNext same-symbol lifecycle has no working coverage on the live permissions path.**
All three `tests/test_concurrent_cap.py::TestGate3Integration` tests short-circuit at
`same_symbol_lifecycle_v4_source_required_fail_closed` (`src/components/same_symbol_lifecycle_v4.py:1172-1176`
→ `src/components/permissions.py:1321-1324`) before reaching the behaviour each exists to prove:
count-cap bypass, duplicate rejection, and broker-alias-aware hedge conflict. The production fail-closed
is correct. The consequence is that **duplicate / hedge / alias handling on the live execution path is
currently unexercised.** The gap is four fixture fields: `candidate.candidate_id`, `.ev_r`,
`.probability`, `.thesis_id`.

**L3 — three tests only go green when a live gate is OPEN.**
`tests/ultimate_book/test_a8_live_activation_config.py:76` asserts
`ultimate_book_live_activation_allowed is True`; `tests/test_wave3_5_v4_authority_activation.py:20`
asserts `selector_v4_apply_to_execution is True`; and
`tests/ultimate_book/test_market_expansion_runtime_generator.py:285` requires `runtime_effect_now is True`.
All three are red **because the gates are correctly closed**. Given B26 — no halt flag exists anywhere on
the VPS, the supervisor is Running, both terminals connected, `trade_allowed` true, so one YAML boolean
is the entire brake — a suite that encodes "gate armed" as the expected state is a standing invitation
for a future session to "fix the failing test" by flipping the gate. **Owner decision, independent of
anything else in this document.**

### 4.2 Two more divergences the classification surfaced

- `scripts/dual_broker_execution_follower.py:2496-2509` maps **42** instruments from the current profile,
  against the declared 24-symbol `GTOS_24_SYMBOL_SURFACE`; 18 extra, **0 missing**. Latent (the script is
  on the never-execute list, H6) but a real declared-surface divergence.
- 6 live W7 symbols have **no `instruments[]` block** in `config/profiles/redacted_account.yaml`
  (`CORN_c, COTTON_c, XAGAUD, XAGEUR, XAUAUD, XAUEUR`), so
  `src/components/ultimate_book/book_engine.py:430-431` skips them with
  `reason: "profile_missing_instrument_config"` — silently.

---

## 5. What "environment-bound" actually costs

The label is not "harmless". Three distinct remedies with very different prices:

| remedy | fixes | price |
|---|---:|---|
| Vendor the 27 `*_2026_06_18` routes from the VPS lineage | **56** on the declared live surface | 48.5 MB, 497 files |
| Widen the sparse cone for 3 non-LFS artifacts (`VNEXT_REPLACEMENT_MARKET_SOURCE_ACTIVATION_MAP`, `MASTER_BACKLOG.md`, `PHASE3_DEFERRED_…_LEDGER`) | **28** (15 + 13) | < 1 MB |
| Widen the cone for `research/science_program_2026_05` **and** fetch 2.05 GB of LFS objects from GitHub | part of the 299 — and per §2 the pointer-backed majority gets *worse* before it gets better | 4.25 GB + 2.05 GB network, on a disk at 92 % |
| `pip install sentence-transformers fastapi plotly` | 23 errors | blocked — PEP-668 (C11) |
| Delete `src/research/__init__.py` | 2 errors + 4 failures | one line |

---

## 6. Declared gaps — required output, not an admission

- **The three `tests/ultimate_book/` singletons** (`test_book_engine.py`, `test_a8_live_activation_config.py`,
  `test_market_expansion_runtime_generator.py`) are in the tail table, not individually root-caused here.
- **A second non-deterministic test exists.** Two whole-suite runs 25 minutes apart at the same commit
  gave 651 and 652 failures. `test_high_load_integration` is the known one; the second is not isolated.
- **No full-materialisation A/B was run.** §2 explains why, and states the prediction it declines to
  test: hydrating everything turns the ~57 % non-pointer artifacts green and turns the pointer-backed
  remainder from `FileNotFoundError` into wrong-number assertions.
- **Whether the 36 Windows-backslash tests ever passed on any machine** is unknown; the history is a
  single squashed snapshot (`95105914f`) so bisection is impossible.
- **C11's ~23 pytest-asyncio attribution inside the 650 `failed`** is still unverified. It was checked
  against the *errors* and refuted there; nobody has checked it against the failures.
