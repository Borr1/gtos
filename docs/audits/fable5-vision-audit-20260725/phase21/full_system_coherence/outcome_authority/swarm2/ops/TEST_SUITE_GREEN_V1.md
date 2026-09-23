# TEST_SUITE_GREEN_V1 — the suite reports the code again

**2026-08-12.** Owner policy change, in his words: *"for the tests, dont do ab testing anymore,
basically make sure all the tests pass, and maybe some failed tests are just stale or dont make
sense anymore, in that case they can be simply removed if the vision and the idea dont make sense
anymore or if it's an environment thing comparing mac and google and different paths then maybe we
can fix those too so that we dont have to do the full a/b each time we can just run the tests once
in the end when merging everything."*

This supersedes `CLAUDE.md` §6's A/B-against-parent ritual and H2's standing-red framing.

---

## 0. Counts

| | before | after |
|---|---:|---:|
| failed | 50 | 0 |
| errored (collection) | 1 | 0 |
| **bad** | **51** | **0** |
| passed | 13,909 | 14,022 |
| skipped | 124 | 124 |
| xfailed | 32 | 31 |

Baseline captured at `3da95f915` (dirty — see §4), full suite, `scripts/pytest_failset.py capture`.
The +113 passing delta is the 15 tests the sparse profile was hiding (§2.1), the newly-runnable
sealed-arm and R2 binding tests, and three tests added by this work.

`xfailed` drops by one because a KEEP-REAL row was **closed by fixing its defect**, which is the
alarm working as `tests/conftest.py` designed it.

---

## 1. The category-1 findings — read these first

Six. Four are in code and are fixed; two are reported rather than changed.

### C1-1 · The broker-mutation census had not run in any session that read it
`tests/safety/test_activation_token.py::test_the_mutating_surface_has_not_widened` is the check
that guarantees nothing mutates broker state outside `RealMT5.order_send`, where the
activation-token gate lives. It ran `subprocess.run(["rg", ...])`. **On this machine `rg` is a
shell function, not an executable**, so the call raised `FileNotFoundError` before the first
assertion. The census was inert while displaying as one filed red line — the worst failure mode a
safety check has, and **both accounts are armed and trading real money.**

Rewritten as `git ls-files` + a pure-Python scan (same corpus, same three excluded prefixes, both
original assertions unchanged) with a positive control that fails if the census finds no
`.order_send(` at all. Running it again surfaced the defect the KEEP-REAL row had originally
filed: two committed `.order_send(` sites under `docs/` were undeclared — the phase5
activation-carry staging copy of `execution.py` (bytes intended for the VPS) and swarm2's
`b8_paired_shadow/controls.py`. Both are now in `_DECLARED_MUTATION_SITES` with an argument each.
A `-g '!docs/**'` would have been one line and was refused deliberately: `docs/` holds the carry
tree that reaches the host.

Same defect, same fix, in `tests/test_opus5_architecture_audit_hardening.py::test_every_create_mt5_caller_uses_a_known_mode`
— now an AST walk, which is also strictly stronger: the old regex could only see a mode that was
first inside the parentheses and double-quoted, so `create_mt5(balance=1, mode='live')` was
invisible to it.

### C1-2 · The live entrypoint imports the broad-origin generator family
`run_book` pulls in `src.components.broader_origin_generators` and
`src.components.broad_origin_emission_contract`. That family has never traded live and must not be
reachable from the armed book. Chain:

```
run_book → … → src/components/selector_v4.py:41
            → src/research/moonshot_scheduler_v4_best_trade_allocator.py (module scope)
            → src/components/broader_origin_generators
```

Introduced by `d90da611b` ("wave21: bind scheduler collisions to producer occurrences") for three
pure key/ordinal helpers. Deferred into `_occurrence_identity()`, called at each of the two use
sites — both already inside functions — so no behaviour moves.

### C1-3 · A sleeve with NO cost coverage was published UNCONDITIONAL
Wave 21 (`7d6bbca7a`, `src/costs/model.py:1233-1240`) made the cost layer refuse a
JPY-denominated cash-per-lot commission arriving with no `entry_utc`: converting it needs a
date-indexed USD-per-price-unit rate and the 2026 symbol-spec snapshot is not a historical
default. It says NOT_EVALUABLE and fails **closed**. Correct.

`recost_w7_validation.sleeve_table` then turned that refusal into a **number**. An `unpriced` row
is imputed at `class_medians.get(sleeve, 0.0)` ex-swap with a **zero** swap rate — reasonable
while some row in the class is priced and supplies the median, a fail-**open** when the whole
class refuses, because both fall back to `0.0`. Measured:

| sleeve | rows | ex-swap R | swap/night | tier |
|---|---:|---:|---:|---|
| `fx_jpy` | 530 | 0.0 | 0.0 | **UNCONDITIONAL** |
| `fx_jpy_ny` | 197 | 0.0 | 0.0 | **UNCONDITIONAL** |

UNCONDITIONAL is the most permissive survivor tier there is, and both earned it *because their
cost is unknown*. Worse: `mc_firm_rules.build_cells` selects `SURVIVORS_ONLY` on
`survives_at_max_carry` (net at max carry > 0 — plain gross when cost is zero), so both uncosted
sleeves were **selected into the survivor book and priced by the Monte Carlo as if they were
free** (`book_days` 246 → 623).

Fixed at the source: no priced and no transferred row ⇒ `cost_evaluable False`, tier
`NOT_EVALUABLE_NO_COST_COVERAGE`, and `survives_to_horizon` / `survives_at_max_carry` both False.

Survivor sets after the repair — Q's sealed four on each account **plus `sub_mid_dn_revert`**,
which now survives at max carry on both:

* FTMO — `crypto, energy_agri, metals_core, sub_mid_dn_revert, sub_xvol_pullback`
* redacted_account — `crypto, energy_agri, sub_mid_dn_revert, sub_xvol_pullback, vp_euidx_pocgrav`

### C1-4 · A compression made sealed evidence invisible to its own comparator
`replay_differential_harness.storage_mode` knew two forms — flat `.jsonl` and sharded
`.jsonl.cold/`. The 2026-08-12 storage-reclamation pass created a third by compressing sealed arm
ledgers in place; its own manifest records
`PHASE_D_JANUARY_S0R0_R2_…/…_ORDER_LEDGER.jsonl.zst` at 2,013,145 bytes. The harness reported that
role **absent**, `compare_arms` returned UNAVAILABLE for it, and the verdict degraded EQUIVALENT →
**INCOMPLETE**. 182 rows of sealed order evidence, present on disk, invisible to the comparator,
and answered with a softer verdict rather than a refusal.

`zst` is now a storage mode, streamed through the `zstd` **binary** (what the cold reader beside it
already does via `shutil.which`; no Python zstd binding is installed here). `storage_mode` still
returns `ambiguous` when more than one form is present, so a half-finished compression cannot pick
a side silently.

### C1-5 · A fifth artifact wrote the armed set down — with the disarmed sleeve in it
`tests/ultimate_book/test_lane_weights.py::test_supervisor_binds_current_account_scopes_and_contracts_to_external_files`
asserted three literal strings pinning the FTMO row as it stood **before 2026-08-05**, including
`mx_btcusd_d1_donchian_20_breakout` and its `--frontier-exits` — the sleeve the owner disarmed.
`CLAUDE.md` §4: *"Do not write the set down again anywhere — four artifacts did, and all four were
wrong."* This was the fifth. Now derived from `src.safety.armed_set`: reconcile clean, no worker
fail-open, spread floor equal to the declaration.

### C1-6 · Two open items, reported not changed

* **`registry.active_specs` opt-in branches are asymmetric** (`registry.py:128-141`): with
  `include_candidate_book=True` an empty `candidate_book_sleeves` means **all** candidates; with
  `include_market_expansion_book=True` an empty `market_expansion_sleeves` means **none** — `if
  allowed:` guards the whole update. A two-flag call therefore resolves **zero** `mx_*` sleeves. It
  did not matter while the armed union was four clean/candidate names; it matters now that the two
  F5 workers declare 32 names including twelve `mx_*`. **Worth confirming the host's
  `ultimate_book_market_expansion_sleeves` actually admits every name the F5 declaration lists** —
  `registry.py:144` drops an unresolvable tag with no fallback and no error, so the difference is a
  silent stand-down, not an error.
* **Provenance is lost between the fixture and the replay runner's probe row.** Three probe rows in
  the B7.5 factorial refuse at `predecision_limit_fillability_source_boundary_missing` on
  `row.predecision_limit_fillability_probability` and `row.execution_fill_probability`. This is
  **not** the known fixture-provenance defect: `_candidate_bundle`'s candidate, option and packets
  all carry the complete tuple (boundary `asof_candidate_fields_only_no_postdecision_path`, source
  time 09:45), verified by direct read. Something between them drops it. Replay machinery, parked
  campaign, no live path — filed here rather than guessed at.

---

## 2. Every failure, with its category and disposition

Category key: **1** real code defect · **2** environment / path / platform · **3** stale decision ·
**4** wrong fixture.

**No test was deleted.** Where a test encoded a decision that had genuinely expired, the
*assertion* was replaced by the strongest claim that is still true, with the reason in the file.
That is recorded as category 3 below.

### 2.1 Sparse checkout — the route was tracked but not materialised (15) · category 2

| tests | disposition |
|---|---|
| `research_infra/test_sol_conditions.py` (5), `test_session_fc_exit_overlay.py` (4), `test_session_hdf_exit_capture_falsifier2.py` (2), `test_exit_overlay.py` (1), `test_wave19_sol_decision_semantics.py` (1), `test_session_fb_sol_grid.py` (**collection error**) | `research/operations/wave19_sol_repair_2026_08_01` added to `scripts/gtos_hydrate_test_data.py`'s `EXTRA_HYDRATIONS` |

The route landed 2026-08-01, after the triage pass that built that list, so nothing carried it and
every fresh worktree manufactured 15 red tests out of a clean tree. 52 files, 13.7 MiB. All 135
tests in those six files pass once hydrated. `test_session_fb_sol_grid.py` loads
`grid/session_fb_sol_grid.py` **by path**, which is why its absence was a collection error rather
than a failure. Running the hydration script also pulled in `broker_truth_layer_2026_07_27`, which
its own list already named, and that fixed `tests/test_replay_columnar_source.py` (3).

### 2.2 Absolute paths into deleted worktrees (2) · category 2

| test | what it pointed at | disposition |
|---|---|---|
| `research_infra/test_session_fg_integration.py` | `FG_PHASE1_SOURCE_MANIFEST.json` binds an absolute path into `worktrees/wave19-broad-forensic-20260801`, removed after the integration landed — all 76 file checks read `b""` and `git -C <dead path> rev-parse` exited 128 | resolve the recorded path first, fall back to the in-repo route of the same name (the 76 files are **tracked** and all reproduce byte-exact; canonical manifest `5f846600…` unchanged), and check the recorded source commit is still an object here rather than asking a deleted worktree for its HEAD |
| `research_infra/test_p1_offline_complete_path_runner.py::test_preexisting_output_parent_refuses_in_preflight` | `preflight` checks `SOURCE_ROOT` (`:1754`) — `worktrees/wave16-rematerialization-20260731/.hermes/…` — before reaching the refusal under test, so it failed on `path_component_missing` from its own setup | `SOURCE_ROOT` monkeypatched to a real directory; subject unchanged |

### 2.3 `rg` is not a binary on this machine (2) · category 2, one of them safety

| test | disposition |
|---|---|
| `tests/safety/test_activation_token.py::test_the_mutating_surface_has_not_widened` | **C1-1** — `git ls-files` + Python scan, positive control added, two docs/ sites declared, KEEP-REAL row closed |
| `tests/test_opus5_architecture_audit_hardening.py::test_every_create_mt5_caller_uses_a_known_mode` | AST walk over tracked `*.py` |

### 2.4 Point-in-time claims asserted as standing ones (14) · category 3

Each of these was true when written and can only go false as the repository moves. None was
deleted; each was rebound to the thing it was actually claiming.

| test | what it used to assert | why that is dead | what it asserts now |
|---|---|---|---|
| `test_session_fg_integration` → `safety.no_forbidden_changed_path` | no `config/`, `run_book*`, activation-token or raw-broker path changed in `BASE..HEAD` **plus** the working tree **plus** every untracked file | that is a property of the future, not of FG; it went false the first time a later session legitimately edited a live config | the same forbidden-prefix check over FG's own **closed** range `integration_base..integration_head_before_synthesis`, both from the committed ledger. Still zero |
| `test_session_fg_integration` → `safety.r2_drift_inherited_exact` | the working tree's R2 drift set is exactly two paths | CLAUDE.md §3 records that count is a property of the tree's LFS/resolution state and is not portable between worktrees; §4 records CN's break as authorized | no R2-bound path appears in FG's own integration range |
| `test_session_fg_integration` → `docs.fa_six_axes` | seven verbatim prose strings | `42c7c863a` re-authored the document in the session's own voice; not one string survived while all six axes are present and closed | structural: axes numbered 1–6, plus a "What I got wrong" section |
| `test_b7_5_post_acceleration_contract_r2_verification_split` (7) | the R2 contract binds this tree; the cost engine is at CN's exact after-bytes | **six** R2-bound paths are drifted at `origin/main` itself — the authorized forward break plus wave-21 replay work — and pinning one revision of a file expected to keep moving made every later authorized cost commit report itself as "an unrecorded edit" | a session fixture recovers each drifted path's **sealed blob from git history into a temp tree** and hands it to the runner as `runtime_evidence_root` (it returns on first *hash match*), so the four arm bindings and the OD-2 measurement run against genuinely sealed bytes with **zero repo mutation**. Plus a new test: every drifted bound path must be named in `AUTHORIZED_FORWARD_BREAKS` with who authorized it and why |
| `test_b7_5_post_acceleration_contract::test_phase_c_hash_producer_binding_is_format_independent` | the Phase-C contract binds | its producer (`v4_timewarp_…`) is one of those authorized breaks | keeps its seven AST predicates; asserts bound when sealed, failing **closed** with `historical_hash_producer_contract_changed` when not, plus that the producer still carries its three structural clauses |
| `test_cl_pass_surface_ceremony::test_real_package_is_hash_sealed_and_empty` | `config/agent_config.yaml` unchanged in this worktree | a precondition CL checked before executing on 2026-08-01; every arming decision since edits that file | package properties asserted alone; the guard is split into `restricted_config_drift()`, still run, still refusing a *missing* guarded file, with drift required to be explained — and `config/profiles/redacted_account.yaml` (inside the token digest) asserted unchanged |
| `test_cn_live_cost_carry::test_carry_builder_reproduces_every_committed_payload_and_diff` | the carry reproduces from today's working tree | its four `NEW_FILES` were read from the working tree while every `HOST_BASES` entry is pinned; wave 21 rewrote two of them, and rebuilding would have silently redefined what CN carried on 2026-08-06 | pinned to `870d4cb53` — the commit that reproduces **all six** recorded manifest values at once (three payload copies, two `not_carried` config hashes, `mainline_sha256_after_CN` at `f599f25f…`), found by search, not assumed |
| `test_scripts/test_ab_receipts_are_self_contained::test_every_ab_receipt_embeds_its_captures` | every A/B receipt embeds a machine capture | `phase20/receipts/r1/R1_AB.md` is one the tool **could not** have produced and says so: the capture at `8dd9b07c0` returned `parse_complete: false` / `usable_as_baseline: false` ("recovered 0 ids but pytest reported 94") and the branch had concurrent writers | admitted to the exemption list, and a **new** test makes the reason mandatory so the exemption cannot become a way back in for prose |
| `test_replay_policy_generation_lineage::test_deployed_lineage_claim_is_pinned_to_the_live_commit` | every module that differs from `redacted_host` under `sleeves/` is lineage-classified | that is not the register's invariant — the module states it as `DEPLOYED_HELPERS \| NO_DEPLOYED_LINEAGE == clock_dependent_sleeves()`, asserted seven lines earlier and passing. Five modules diverged for reasons unrelated to a clock (`ce3be027a` stop-floor centralisation across `_stop_floor`/`metals`/`metals_ob_micro`, `eeb73b090` STAGE13 in `candidate_registry`, `f2fdd99de` ETHUSD in `crypto`) and none owns a clock at either lineage | narrowed to clock owners at **either** lineage, so a sleeve that had a clock and lost it still needs classifying |
| `test_mc_firm_rules::test_the_published_grid_reconstructs_and_the_two_survivor_sets_differ` | `book_days` reproduces on every cell ("a cost re-pricing cannot change the trade set") | true of a variant whose membership is cost-independent, false of `SURVIVORS_ONLY`, which is *selected* on cost | `book_days` stays **hard** for fixed-membership variants; for cost-derived ones a change must be accounted for by a named membership difference |
| `test_mc_firm_rules::test_this_engine_reproduces_every_published_mc_field_exactly` | all 48 redacted_account MC fields reproduce exactly | no cost-independent field is left — `med_days_pass` moves on `ALL_11_BOOK_OF_RECORD` too. **`MC_FIRM_TRUE_V1.json` needs an owner re-seal**; until then no exact-reproduction control over it can be green | structural completeness (all 24 published cells, every published key) **and determinism** (same seed base twice, identical) — which a broken engine fails and an authorized cost change cannot |
| `test_armed_set_mc::test_no_sleeve_set_leaves_the_published_grid_shape` | the FTMO survivor list is exactly Q's four | a second place the survivor set was written down, and the membership is cost-derived | grid shape hard; every sleeve Q sealed is still a survivor (a **disappearance** still fails); subset of the book of record |
| `test_armed_set_mc::test_a_named_set_equals_the_derived_variant_it_names` | the literal `ARMED_4` equals the derived `SURVIVORS_ONLY` | compared a four-sleeve book to a five-sleeve one | names FTMO's own **derived** survivors, which is what the test says it does |
| `test_b7_5_neutral_selection_factorial` (5) | `risk_decision_reason == probe["status"]`; all six probe rows read `candidate_instance_identity_not_materialized` | the first pinned the **fallback** arm of `first_present(probe["risk_decision_reason"], probe["status"], …)` — the probe now carries its own reason and `status` is that reason namespaced; the second covered rows that materialize and refuse one stage later | the contract plus "both name the same veto"; and the identity claim stated over the **conflicted** rows, with nothing hard-eligible anywhere. Residual filed at **C1-6** |

### 2.5 Real code defects (11 failures across 4 files) · category 1

`test_broad_origin_emission_repairs` (2) · `test_w7_recost` (3) · `test_replay_differential_harness`
(3) · `test_lane_weights` (1) · `test_activation_token` (1, was xfail) ·
`test_opus5_architecture_audit_hardening` (1). See §1.

### 2.6 Category 4 — wrong fixture

**None confirmed.** The one candidate (`predecision_limit_fillability_source_boundary_missing`) was
traced to the runner rather than the fixture and is filed at **C1-6**.

The 10 `tests/test_selector_v4.py` failures named in the brief (bare `{"fill_probability": X}` with
no provenance tuple, `IMPLEMENTATION_STATE.md` B8) **are already fixed** — that file does not
appear in the 2026-08-12 baseline at all and passes clean. Nothing was done to it, and
`selector_v4.py` was not touched.

---

## 3. Decision-contract membership — what was touched under `src/`

Checked against R2 per `CLAUDE.md` §3 H1 before editing. Two bound files were edited:

| file | bound? | already drifted before this work? |
|---|---|---|
| `src/research/moonshot_scheduler_v4_best_trade_allocator.py` | **yes** (`common_behavior_inputs`) | **yes** — drifted at `origin/main`, verified by `git show origin/main:<path>` |
| `src/research_infra/replay_differential_harness.py` | no | — |
| `scripts/recost_w7_validation.py` | no | — |

So the seal was **not newly broken** by this work: the allocator was already off its sealed bytes on
mainline, alongside five other bound paths, under the owner-authorized forward break recorded in
`CLAUDE.md` §4. All six are now enumerated with their authority in
`tests/test_b7_5_post_acceleration_contract_r2_verification_split.py :: AUTHORIZED_FORWARD_BREAKS`,
and a new test fails on any drifted bound path that is **not** named there.

No safety test was weakened, skipped or deleted. `tests/safety/` is 169 passing.

---

## 4. Conditions during the run

The baseline was captured while another agent landed the **F5 minimal-size experiment** in this same
worktree (`c40885d1f`, `56721dd5c`: two new decision surfaces on one funded account, broker identity
`0`, `--f5-minimal-size-usd`). That produced transient failures which are **not** in the table
above because their owner fixed them mid-run:

* four in `tests/safety/test_armed_set_single_source.py` — `armed_sleeves()` unioned across all
  accounts including the 32-sleeve $10 experiment surfaces, contradicting its own module docstring.
  Fixed by that session with `surface=SURFACE_PRODUCTION` and `production_arming()`.
* 22 `SymbolAuthorityError: profile symbol authority drift for redacted_account` from editing
  `config/profiles/redacted_account.yaml` — that file is inside the activation-token digest, and their
  follow-up commit `56721dd5c` ("the profile file is inside the token digest") addressed it.

One consequence reached this work and is fixed here: `tests/test_broad_origin_emission_repairs.py`
needs the union over **every** worker for an isolation proof, not just the production dial — a $10
order is still an order — so it now asks `armed_sleeves(surface=None)` deliberately.

---

## 5. Commits

| commit | scope |
|---|---|
| `78235d599` | hydrate wave-19's SOL route; unbind FG's verifier from a deleted worktree |
| `28d12bc21` | the broker-mutation census was inert — `rg` is not a binary here |
| `0e425e895` | live-entrypoint isolation; a fifth artifact wrote the armed set down |
| `363183158` | an unpriced sleeve was published UNCONDITIONAL |
| `a8daefb6e` | the R2 seal controls measure the authorized break instead of dying of it |
| `6dc9e7bbf` | a compression made sealed evidence invisible to its own comparator |
| `7c9db9543` | two ceremony packages measured today's mainline instead of their own moment |

Report is this file; no test or code change is in it.

---

## 6. What still needs an owner decision

1. **`MC_FIRM_TRUE_V1.json` needs a re-seal.** Every one of its 96 published Monte-Carlo fields is
   downstream of the cost layer, and the cost layer has moved three times under owner authority
   (CN's commission default; wave 21's dated-FX refusal; the 2026-08-12 rollover/barrier model).
   No exact-reproduction control over that artifact can be green until it is re-sealed. Determinism
   and structural completeness are asserted in the meantime.
2. **`SURVIVOR_BOOK_V1.json`'s tiers move** once the fail-open at C1-3 is priced: `fx_jpy` and
   `fx_jpy_ny` are NOT_EVALUABLE, and `sub_mid_dn_revert` now survives at max carry on both
   accounts. Nothing armed changes by itself; the published economics do.
3. **Confirm the F5 declaration resolves** (C1-6, first bullet) before treating the two experiment
   workers' 32 sleeves as a measurement of the full system.
