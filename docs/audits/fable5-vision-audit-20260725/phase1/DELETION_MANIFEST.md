# Deletion manifest — a reviewed list, with the sweep evidence behind it

**Session C, Phase 1, 2026-07-26.** HEAD `acad79826`. Companion to `RED_SUITE_CLASSIFICATION.md`,
which had to come first: you cannot decide what to delete while a third of the red suite is
unexplained, and ~330 of the failures belong to code this manifest is deciding about.

**Nothing in this file has been executed.** Per F23 the audits' own tier would have deleted the live
trading surface; a manifest that is right and unexecuted beats a deletion that is fast and wrong. The
one exception is §5, which the session brief explicitly ordered and which is measured.

---

## 0. The headline correction: deleting Python does not reclaim disk

The brief frames disk headroom as a live constraint (91 % full, ~40 GiB free, and Phase 5 wants tick
backfill in tens of GB). It is — but **the Python half of this manifest reclaims essentially zero
bytes**, and so does deleting tracked evidence, because git history keeps every blob. Measured on this
machine [MEASURED]:

| store | size | what it is |
|---|---:|---|
| `/Users/borr/GTOSActive/repo` **total** | **132 GB** | |
| — `.git` | **57 GB** | of which `.git/lfs` is **55 GB** and `.git/objects` is **907 MB** |
| — working tree | ~75 GB | of which **69 GB is ONE directory** (below) |
| four `replay-accel-*` worktrees | **~24 GB** | 16 + 6.7 + 1.2 + 0.04 |
| this worktree | 410 MB | |

`.git/lfs` being 96.5 % of the git store mirrors the VPS exactly (V6: 60.0 GB `.git/lfs` vs 845 MB of
real objects). **It is the same pathology on both hosts.**

### The tempting wrong recommendation, killed by measurement

The obvious move is `git lfs prune`. My own census said **184 local objects totalling 32.10 GB are not
referenced by any pointer at HEAD**, which reads like a 32 GB win. It is not:

```
$ git lfs prune --dry-run --verbose
1031 local objects, 4198 retained, done.
 * 6376fd59… (18 MB), done.
```

**`git lfs prune` would reclaim 18 MB.** LFS retains against all refs and recent commits, not just
HEAD, and those 184 objects are held by other refs. Recommending a prune on the strength of the
HEAD-only census would have been a confident wrong answer. [MEASURED]

### Where the disk actually is

| # | target | size | risk | mechanism |
|---|---|---:|---|---|
| **D1** | Untracked raw replay ledgers under `/Users/borr/GTOSActive/repo/research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/` | **69 GB** | **low, with the repo's own tool** | Individual `BROAD_LIVE_AS_IF_REPLAY_*` JSONL files of 6.0, 6.0, 3.8, 3.8, 3.4, 3.4 GB… from the January and April campaigns. Only 2,395 files of that directory are tracked (129 MB). The repo already ships `research/operations/final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16/archive_b7_5_cold_evidence.py`, with a receipted contract (`per_shard_compressed_and_uncompressed_hashes_required`, `raw_and_cold_simultaneous_representation_forbidden`, `minimum_free_reserve_bytes`) — and `.hermes/receipts/phase-d/JANUARY_*_COLD_DEMOTION.json` proves it has already been used on the January arms. This is `repo_cleanup_and_staleness_policy.md` §"Large Evidence" exactly: *demote raw shards to cold reproducibility evidence*. |
| **D2** | `worktrees/replay-accel-slice-safe-20260718` | 1.2 GB | **low** | **0** `.hermes` references |
| **D3** | `worktrees/replay-accel-attempt3-20260719` | 39 MB | **low** | **0** `.hermes` references |
| **D4** | `worktrees/replay-accel-attempt5-20260719` | 6.7 GB | **medium** | **20** `.hermes` references — needs a per-receipt read first |
| **—** | `worktrees/replay-accel-engine-20260719` | 16 GB | **DO NOT TOUCH** | **558** `.hermes` references; it is the `allowed_root` of the January cold-evidence archive (`JANUARY_S0R0_R2_COLD_DEMOTION.json`) and the producing worktree H4 binds |

D1+D2+D3 is **~70 GB** — larger than every other line in this manifest combined, and it touches no
tracked file, no test, and no contract.

### Tracked-tree shape, for the record [MEASURED]

29,822 tracked files, **6.84 GB** of blob bytes at HEAD.

- `research/science_program_2026_05/06_outcome_testing`: **12,387 files / 4.22 GB — 62 % of the tracked
  tree**, and `CLAUDE.md` §10 classes the programme historical.
- **289 blobs > 5 MB = 5.24 GB.** Largest are 91.9 / 90.9 / 90.7 / 88.4 MB single JSONL ledgers.
- `knowledge_base_backtest/batch_api/`: ~400 MB of raw LLM prompt dumps in 8 files.

Deleting these at HEAD costs nothing in disk until a history rewrite, so they are listed as a
**context-pollution** decision (they are what the sparse cone already excludes), not a disk decision.

---

## 1. Reachability, re-derived at this HEAD [MEASURED]

Own census over `git ls-files`, blobs read via `git cat-file --batch` (never the filesystem — this
worktree materialises 18 % of the tree, and F24 is that mistake):

**4,101 tracked `.py`, 2,423,314 lines, 0 parse errors, 14 UTF-8 BOMs.**
(The second audit's 3,814 / 2,347,200 was before Phase 0 vendored `run_book.py` and the 661-file
evidence route.)

| class | files | lines | % |
|---|---:|---:|---:|
| **operationally reachable** — closure from the named entrypoints below | **229** | **314,710** | **13.0 %** |
| policy-exempt (§2) | 654 | 558,696 | 23.1 % |
| candidate pool | 3,218 | 1,549,908 | 64.0 % |

E9 **holds and is slightly stronger than the second audit's ~14.8 %**: 87 % of tracked Python is
operationally unreachable.

The entrypoint set is named rather than heuristic, because an entrypoint set assembled from "has
`__main__`" is what produced F23:

- **LIVE** — `run_book.py` (started by `scripts/run_book_supervisor.ps1:86-108`), `run_agent.py`
  (24 × from `start_all.bat:121-167`), `.tools/monitor_books.py`,
  `scripts/dual_broker_execution_follower.py`, `scripts/fn_smoke_trade.py`, `scripts/mt5_preflight.py`,
  `scripts/emergency_close_and_stop_redacted_account.py`, `scripts/flatten_all_positions.py`,
  `scripts/gtos_activation_token.py`
- **CAMPAIGN** — `src/research_infra/b7_5_post_acceleration_runner.py`,
  `…/replay_acceleration_attempt5_typed_sparse_runner.py`,
  `…/v4_timewarp_simulated_live_research_loop.py`
- **TOOLING** — `scripts/generate_live_state.py`, `scripts/gtos_context.py`, `scripts/pytest_failset.py`

---

## 2. Exemptions — policy, not measurement

| exemption | files | why |
|---|---:|---|
| `src/components/ultimate_book/**`, `tests/ultimate_book/**` | — | SECOND_AUDIT §5.4 precondition |
| `src/safety/**`, `tests/safety/**` | — | the activation token is now the primary brake (`CLAUDE.md` §4) |
| `src/mt5/**` | — | carries the `order_send` choke point the token guards |
| `run_book.py` | 1 | the live entrypoint |
| **`scripts/flatten_all_positions.py`, `scripts/emergency_close_and_stop_redacted_account.py`** | 2 | **B21, 2026-07-26 owner decision.** Gate-unaware BY DESIGN — zero references to `live_broker_authority` or `ultimate_book`, driving raw `MetaTrader5`. Since revoking broker authority also revokes the book's ability to close, these are the operator's **only gate-independent exit**. They score DEAD on every static heuristic. They are load-bearing. |
| learning family — `learned_edge_layer_v4.py`, `learned_edge_dataset_builder.py`, `learned_edge_trainer.py`, `learned_edge_walkforward_gate.py` | 4 | SECOND_AUDIT §5.4; F23 names the walk-forward gate explicitly |
| `src/research_infra/moonshot_expanded_market_reduced_surface_execution.py` | 1 | named in active config, **`config/agent_config.yaml:2715`** (the audit says `:2716`; it is `:2715`). It also has a real importer at `scripts/backfill_ai_narrowing_policy_shadow_evaluations.py:25` and a string reference at `src/components/gtos_vnext_runtime.py:13055` — so "one subprocess hop" understates it |
| R2 `input_bindings` | 45 | deleting a bound file is a contract event, not a cleanup (H1) |
| `code_authority_paths` — the **second** SHA gate, `replay_acceleration_attempt5_typed_sparse_runner.py:1405-1431`, root-compared at `b7_5_post_acceleration_runner.py:1615` | 18 | B25: bound a second time from inside an executing file; OD-2 cannot free them and neither can a tier |
| **ACTIVE research routes** — any `research/operations/*` directory holding an R2-bound path | — | `final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16` and `final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20`. Their `build_*`/`verify_*` are CLI-invoked campaign machinery that nothing imports |
| **all of `tests/**`** | 537 | see §3 |
| `docs/audits/**/*.py` | — | an audit's own reproduction receipts |

---

## 3. F23 reproduced — in my own tier, twice, before any agent saw it

This is the most useful thing in the manifest, because it says the failure mode is **structural**, not
a slip the first audit made.

**Version 1** put every test file in the candidate pool. Nothing imports a test, so *every* test scored
"unreferenced" and TIER LOW contained:

- `tests/test_run_book_importable.py` — **Gate G0 criterion 1**
- `tests/test_b7_5_post_acceleration_contract_r2_verification_split.py` — the R2 contract test this
  programme wrote three days ago
- `tests/scripts/test_pytest_failset_parsing.py` — the A/B tool's own test, i.e. the thing that makes
  every "no regressions" claim in this programme checkable
- `tests/test_opus5_architecture_audit_hardening.py` — the first audit's 97 hardening tests

**Version 2** exempted tests but still had
`research/operations/final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16/build_b7_5_selection_sizing_decision_contract.py`
in TIER LOW — **the R2 contract's own construction authority**, which is B25's
"rejected on inspection" case repeating itself one route over.

Two rules follow, and they are the manifest's actual product:

> **R1. A test is never a standalone deletion candidate.** It enters only as the paired half of a module
> deletion, when *every* non-test import target of that test is itself in the tier. This is the plan's
> "tests and the code they cover go as one reviewed pair, never tests first", made mechanical.
>
> **R2. A research route that holds a contract-bound path is ACTIVE**, and its CLI-invoked `build_*` /
> `verify_*` tooling is not deletable, no matter what the import graph says.

---

## 4. The sweep, and TIER LOW

Every candidate had to survive **five independent consumer checks**, because the import graph alone is
what F23 defeats:

1. **import** — an importer inside the reachable closure
2. **string** — any tracked file mentions its stem. Built by streaming **every tracked blob, 6.80 GB in
   one pass** via `git cat-file --batch`, extracting identifier tokens and intersecting with the set of
   tracked `.py` stems. 3,900 stems are referenced somewhere.
3. **hermes** — an untracked `.hermes/**` accepted-evidence receipt names it (86 stems do)
4. **config** — `config/**` names it
5. **VPS-branch** — a file that exists **only** on a live-lineage ref (`origin/vps/*`,
   `origin/live-handoff-2026-06-15`, `origin/deploy-live`) and **not at HEAD** names it. 1,488 VPS-only
   files scanned across the five refs; they name **595** stems.

Note on check 5: the naive version — "is the file present on a VPS ref" — marked 3,607 of 3,786
candidates as blocked, because those branches carry the whole repo. *Presence is not consumption.*
Only VPS-**only** files can be hidden consumers, and that is exactly the `run_book.py` → `book_owner.py`
shape F23 describes.

That first pass produced **90 files / 37,110 lines**. It was wrong, and the adversarial review is what
proved it.

### 4.1 The adversarial review, and the two defects it exposed

Three agents, one per 30-file batch, briefed to **refute with `file:line`** and told that a batch with
no refutations is a suspicious result. One batch came back **12 UNSAFE, 2 UNCERTAIN, 16 SAFE** — and
the value was not the twelve files. It was this sentence:

> *"The implemented rule is not the stated rule. You state 'no consumer of any kind,' but what the
> classifier enforces is 'no consumer inside the 229-file reachable closure.' A reference from a
> surviving-but-unreachable file scores zero. **An unreachable file that imports a deleted file is
> still a broken file.**"*

That is correct, and it is the same class of error as F23 wearing different clothes. Concretely:

- `src/research_infra/validation_integrity/gauntlet.py:51-56` imports `perm_null`,
  `regime_inflation` and `walk_forward_oos`, calls them at `:207/:212/:217`, and is **not** in the tier.
  Deleting those three leaves a `NameError`-on-import module and breaks
  `tests/research_infra/test_validation_integrity_gauntlet.py`, which passes today.
- `src/research_infra/replay_acceleration_task6_prepared_pack_acceptance.py:32` and
  `…task6_prepared_pack_runner.py:22` import the `task5` modules, and `task4` hangs off `task5`. `task6`
  is the fail-closed acceptance for the **prepared day packs every remaining campaign arm consumes**
  (`b7_5_post_acceleration_runner.py:476-626`; `CLAUDE.md` §9 lists the pack root as a launch input).
- `scripts/build_wave3_hard_halt_causal_microscope_continuation.py:10` is the **only** tracked caller of
  `build_route` in `src/research_infra/wave3_hard_halt_causal_microscope.py`, whose own
  `if __name__ == "__main__"` blocks at `:867,:882` are **string templates the builder writes**, not
  entrypoints. Two 15-line shims, load-bearing precisely because they are trivial.

**Repair 1 — score to a fixpoint.** A reference from any file that does not *itself* end up in the tier
is a blocker, and an **import** edge is stronger than a textual mention (a surviving importer of a
deleted module is a guaranteed `ImportError`, not a maybe). Re-scoring until the tier stops changing
converged in **3 rounds: 3,218 → 80 → 77**.

**Repair 2 — the index is blind to numeric-prefixed stems.** The reference index tokenises with
`[A-Za-z_][A-Za-z0-9_]{2,}`, so a file named `10_live_l2_corrected.py` is invisible to it — the index
only ever saw `live_l2_corrected`. Every numeric-prefixed research script was therefore **unswept**,
and `.context/02_session_handoffs/40_apr26_DEFERRED_CHANGES_MASTER.md:89` names two of them as required
reading for an **open** decision. All such stems are now held out by construction, not by luck.

**Both repairs were validated against the review rather than asserted:** all **12 UNSAFE files and both
UNCERTAIN files are removed automatically** by the two rules, with no per-file special-casing.

### 4.2 The second review round, and the finding that changes the answer

The other two batches came back **12 UNSAFE / 2 UNCERTAIN / 16 SAFE** and **12 UNSAFE / 17 UNCERTAIN /
1 SAFE**. The fixpoint had already removed the first batch's twelve. It removed almost none of the
second's, because that batch exposed a different blind spot entirely:

> *"Producer-side edges are invisible to a consumer-only index. Roughly half this batch has no consumer
> **of the file** and is nonetheless load-bearing because it is the **sole writer** of an artifact that
> config, `src/`, tests, or preflight authority binds by path. Your classifier asks 'who imports X?'; it
> never asks '**what does X write, and who binds that?**'. For research routes, which are write-once
> evidence factories, the second question is the only one that matters."*

That is correct and it is the crux of the whole exercise. Three concrete proofs from that batch:

- **`build_wave_f_fillability_label_repair.py:690`** is the only writer of
  `WAVE_F_ROW_BOUND_FILLABILITY_LABEL_REPAIR_LEDGER.jsonl`.
  `src/research_infra/replay_acceleration_attempt5_typed_sparse_runner.py:366-400` binds it as
  `fillability_labels`, lists it in `required_inputs`, and **raises
  `runtime_evidence_input_missing:fillability_labels`** without it. **Every remaining April/May/March
  arm consumes it**, and it was on my delete list.
- **`build_ultimate_system_repair_analysis.py:37`** is the only writer of
  `ULTIMATE_WEAK_ACCEPTED_FILTER_LEDGER.jsonl`, which `config/agent_config.yaml:781` binds as
  `selector_v4_admission_quality_guard_source` and `src/components/selector_v4.py:2800` reads. A
  **live-config-bound** artifact with a delete-listed producer.
- **`verify_wave1b_v3_live_authority_gap.py:229-236`** — a **surviving** script — `subprocess`-executes
  `build_wave1b_v3_live_authority_gap.py` by path and gates on `py_compile_ok`.

Plus two structural rules I had missed:

- **`scripts/audit_goal_route_artifacts.py:32-40,283-287`** requires one `verify_*`/`*verifier*` script
  per route under its default `standard` profile. Deleting a route's only verifier silently flips it
  from `ok=true` to `missing_required`. Seven routes in my tier would have.
- **A route's own `OUTPUT_MANIFEST.json` / `FOCUSED_TEST_RESULT.json` pins its scripts by name** —
  two routes record their verifier as the literal `tests` entry. Self-evidence, detectable mechanically.

### 4.3 The producer-side sweep, and what it does to the tier

Implemented all three as mechanical rules: **P1** any artifact filename the candidate emits that a
surviving file under `config/`, `src/`, `tests/`, `.context/` or `scripts/` references; **P2** sole
route verifier; **P3** named in a surviving route manifest.

**TIER LOW collapses from 47 files to 2** — and one of those two is the batch-2 reviewer's own
UNCERTAIN (`build_wave1a_hard_halt_forensic_matrix.py:19` is the only CLI driver for `build_route()` in
the surviving, test-covered `src/research_infra/wave1a_hard_halt_forensics.py` — an *inverse* import
edge a consumer index cannot see). Removing that leaves:

| lines | file |
|---:|---|
| **8** | `research/operations/final_moonshot_wave2_final_master_after_hard_halt_2026_06_04/build_wave2_wave3_prompt_pack.py` |

An eight-line shim (`from build_wave2_semantic_launch_architecture_repair import main`) whose only
import target is itself blocked. That is the entire honest LOW tier.

**P1 over-blocks, deliberately.** "Emits `COMPLETION_AUDIT.json`, bound by
`.context/00_core/research_current_state.md`" is a weak binding — the filename is generic and the
reference is a doc mention. Over-blocking is the correct direction for a deletion manifest, and the
result is not sensitive to it: the three named proofs above are exact bindings to the running replay
engine and to live config.

### 4.3b Two more method defects the review named, both confirmed

**"Zero hits" was being read as evidence of absence when it was often absence of evidence.** The
admission rule is a disjunction of six positive signals and a candidate passes when all six come back
empty — but an empty result from a *broken probe* is indistinguishable from a genuine empty. The
digit-initial-stem bug is the proof: `refindex.json` holds 3,900 stems and **not one begins with a
digit**, and 28 of the 90 v1 candidates had digit-initial basenames. None had ever been tested.

The repair generalises past that one bug: **a liveness assertion per candidate** — before trusting a
zero, confirm the probe can see the candidate at all. Run against the final tier: both surviving stems
are visible to the index in 2 and 5 files respectively, so their zeros are real zeros.

**Basename-keyed dispatch tables are invisible to any identifier index.**
`scripts/build_gtos_vnext_master_conversion_ledger.py:6484` lists
`"07_market_state_algo_verify.py"` literally in `EXPANDED_MARKET_SOURCE_GEOMETRY_SPECIAL_NAMES`,
dispatched at `:6747`, and `tests/…:3139` asserts the resulting family count is exactly **96**. Three
`instrument_expansion` scripts are likewise bound by `sha256` **and** `support_line_count` in
`scripts/build_gtos_vnext_instrument_expansion_market_session_runtime_rows.py:1088-1091`, with
`SystemExit("generated instrument-expansion runtime rows are stale")` at `:1185-1189` and a live config
declaration at `config/agent_config.yaml:1615,3263`. And `research/instrument_expansion_2026-04-25/02_decay_analysis.py`
is loaded by `spec_from_file_location` from **two surviving siblings** (`_run_parallel.py:18-24`,
`_run_subset.py:12-18`) — whose own comment says the file is deliberately named so it can never be an
identifier.

Cheap mechanical repair, now part of the rule set: **extract every string literal ending in `.py` from
tracked code and diff it against the manifest.** Run against the final tier: **0 hits.**

### 4.4 The conclusion this forces

> **Per-file deletion of research-route Python does not survive a producer-side sweep. The unit is
> wrong.** The first audit's LOW tier — 607 files / 219,469 lines "with no reachable consumer and no
> surviving test" — is not a deletable set. Its own definition never asked what those files *write*, and
> in a tree that is 97 % generated evidence, that is the only question that decides anything.

The right unit is the **whole route**: its code, its evidence, and its tests, retired together on an
owner decision that the route's evidence is no longer authority — not on an import graph. Two routes
qualify for that conversation today on the classification's own evidence (`RED_SUITE_CLASSIFICATION.md`
§3.3): `final_moonshot_wave_b_…` and `final_moonshot_wave_c_…_2026_06_18`, whose evidence exists on **no
ref at all**, so nothing can regenerate or verify them.

### 4.5 The superseded 47-file tier, kept for the record

Before the producer-side sweep, the tier stood at **47 files / 24,506 lines**, every one a one-shot
`build_*` / `verify_*` route script under `research/operations/`, surviving all five consumer checks
*and* the fixpoint. It is listed in `RED_SUITE_DELETION_TIER_LOW.txt` **as a review artifact, not as a
deletion instruction** — 27 of its 30 reviewed files were subsequently refuted.

| files | route family |
|---:|---|
| 10 | `final_moonshot_wave2_final_master_after_hard_halt_2026_06_04` |
| 22 | eleven `final_moonshot_ultimate_system_*_2026_06_19` build/verify pairs |
| 4 | `final_moonshot_ultimate_convergence_*_2026_06_19` |
| 3 | `vnext_vps_local_v3_ftmo_production_integration_2026_06_02` |
| 3 | `final_moonshot_wave1*_2026_06_04` |
| 2 | `final_moonshot_v4_kiap_ultimate_system_repair_2026_06_07` |
| 1 | `vnext_root_context_cleanup_closure_2026_05_31` |

Full list with line counts: `RED_SUITE_DELETION_TIER_LOW.txt` beside this file.

**Paired tests: zero.** After the fixpoint, no TIER LOW module has a covering test at all, so the
"tests and code go as one pair" rule has nothing to pair — which is the right outcome, not a gap.

**Not deletable but worth recording:** each of these routes keeps its evidence (`OUTPUT_MANIFEST.json`,
`VERIFICATION_RESULT.json`) while its producer goes. Several manifests record the producer's own
`sha256` and `size_bytes`; one (`VERIFY_POST_SEAL_NAMESPACE_AMENDMENT.json`) records a
`verifier_source_sha256` that has **already drifted** from the file it names. Git history is the archive
per `repo_cleanup_and_staleness_policy.md`, so this is survivable — but it should be a deliberate
decision, not a side effect of a tier that only ever scores `.py` files.

**Scale, honestly stated — four numbers, each smaller than the last, each for a named reason.**

| tier | files | lines | what removed the difference |
|---|---:|---:|---|
| first audit's LOW | 607 | 219,469 | — |
| my v1 | 90 | 37,110 | exemptions, the five-way consumer sweep, tests removed from the pool |
| my v2 | 47 | 24,506 | fixpoint scoring + the index-blind rule (adversarial round 1) |
| **final** | **1** | **8** | the producer-side sweep (adversarial round 2) |

That is not four better searches. It is one search corrected four times by evidence, and the last
correction is the one that says the *unit* was wrong, not the threshold.

---

## 5. The three Tier-A context files — deleted, with the measured effect

Ordered by the session brief: *"Delete them as part of your manifest once the 299 are classified, and
say what it did to the failure set."*

`.context/00_core/architecture.md` (141,996 B, 3,337 lines of XAUUSD-only Model A, status line "Design
Complete"), `.context/00_core/master_roadmap.md` (17,009 B, April edge claims the live system
falsified), `.context/00_core/pre_lock_final_review.md` (19,142 B, an expired WF-1 gate). All three
already carry a `HISTORICAL — NOT CURRENT AUTHORITY` banner whose closing line reads *"Retained only
until the red-suite investigation completes"* — that is this session. All three are hardcoded by path in
`scripts/build_gtos_vnext_master_conversion_ledger.py:31724`, `:31816`, `:31909`, which is why they
survived the Tier-A pass.

**Extract-first, per `repo_cleanup_and_staleness_policy.md` §8: already done, and the banners are the
record.** The one piece of live intelligence in `pre_lock_final_review.md` — that **the AI adds ~0pp to
entry win rate**, the measurement that drove the de-LLM-ing of GTOS — is extracted into
`SECOND_AUDIT.md` §3.6. `master_roadmap.md`'s April edge claim (*"101 trades, 69.3 % WR, +0.235R,
p=0.014"*) survives as the falsified comparand against the hard-halt reconciliation's **77 trades,
−$859.69, 31 W / 46 L**, which its own banner records. `architecture.md` is the Model-A design;
its successor authority is `GTOS_ULTRA_GOAL.md` + `live_system_of_record.md`.

**Consumer check before deleting** [MEASURED]: `git grep` over `tests/` for all three filenames returns
**zero** hits. They contribute exactly **3 of 1,354 ledger rows**
(`architecture.md` → `CONVERTED_AI_NARROWING_OR_AI_REMOVAL_RULE`, `master_roadmap.md` and
`pre_lock_final_review.md` → `CONVERTED_RISK_SIZING_RULE`), and no test asserts on those rows.

### 5.1 Effect on the failure set [MEASURED]

A/B by failure **set**, via `scripts/pytest_failset.py`. Scoped first, to the three test files that
consume `build_rows()`; then the **whole suite**, because the working rules require it and Phase 0 had
three regressions that passed in isolation:

```
scoped  before acad79826: 193 bad     after deletion: 193 bad
        unchanged: 193   fixed: 0   REGRESSED: 0

whole   before acad79826: 684 bad     after cb13a9bd3: 684 bad
suite   unchanged: 684   fixed: 0   REGRESSED: 0
        651 failed / 9,747 passed / 27 skipped / 33 errors — identical on both sides
```

**Deleting them changed nothing in the failure set.** The ledger drops from 1,354 to 1,351 rows and no
assertion moves. The fear that motivated retaining them — *"removing them would drop ledger rows
mid-investigation"* — was real in principle and null in fact, and now it is measured rather than
assumed. 178,147 bytes and 3,337 + ~400 lines of contradicted Model-A authority leave the working
surface; git history keeps them.

---

## 6. What this manifest actually recommends

Ranked by bytes reclaimed per unit of risk, which is the ranking the brief asked for:

| # | action | reclaims | risk | why it is safe |
|---|---|---:|---|---|
| **1** | Cold-demote the untracked raw replay ledgers in `/repo`'s denominator-to-deployment route with the repo's own `archive_b7_5_cold_evidence.py` | **~69 GB** | low | receipted contract, hash-verified, `raw_and_cold_simultaneous_representation_forbidden`, already used on the January arms |
| **2** | Remove `worktrees/replay-accel-slice-safe-20260718` and `…-attempt3-20260719` | **1.24 GB** | low | **0** `.hermes` references each |
| **3** | Review `worktrees/replay-accel-attempt5-20260719` receipt by receipt | 6.7 GB | medium | 20 `.hermes` references |
| **4** | Delete `build_wave2_wave3_prompt_pack.py` | 8 lines | low | the entire surviving TIER LOW |
| — | **Do not** run `git lfs prune` expecting space | 18 MB | — | measured; the 32 GB in the HEAD-only census is held by other refs |
| — | **Do not touch** `worktrees/replay-accel-engine-20260719` | — | — | 558 `.hermes` references; it is the January cold archive's `allowed_root` |

And one action that is not a deletion but is the best value in the whole exercise: **vendor the 27
`research/operations/*_2026_06_18` routes from the VPS lineage — 497 files, 48.5 MB — and 56 failures on
the declared live decision surface go green** (`RED_SUITE_CLASSIFICATION.md` §3.3).

## 7. What is NOT in the tier, and why

- **`research/science_program_2026_05/**` (12,387 files, 4.22 GB, 62 % of the tracked tree).** It is the
  single largest context-pollution target and `CLAUDE.md` calls the programme historical. It is not in
  TIER LOW because ~330 red tests still assert against it and because deleting it at HEAD reclaims no
  disk. It belongs in a **tests+code+evidence** tranche decided together, after the 56-failure
  vendoring question in `RED_SUITE_CLASSIFICATION.md` §3.3 is settled.
- **The 179-module `moonshot_*` layer** (MEDIUM tier in the first audit). Not swept here. One of them is
  named in active config and has a live importer; that alone means the family needs the per-file sweep
  before any bulk move.
- **`src/components/ultimate_book/convergence_replay_matcher.py:24-25`** points at wave4r route outputs
  that are absent from the index — a dangling pointer on the live surface. Recorded as a defect to fix,
  not a deletion.
