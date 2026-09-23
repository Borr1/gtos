# Phase 2 Session D receipt — the differential harness

**Assessed 2026-07-26** on branch `phase2/harness-revival`, worktree
`/Users/borr/GTOSActive/worktrees/phase2-harness-20260726`, from `acad79826`.
Evidence tags: **[MEASURED]** (ran/observed here), **[VERIFIED]** (read directly in code or sealed
artifacts).

`SESSION_D_HARNESS_REVIVAL.md` §7 states done as: *"The harness takes two arm outputs — start with two
of the four sealed January arms, which are known to differ — and reports **where** they differ at row
and field level, fails closed on a difference it does not understand, and proves on a known-identical
pair that it does not cry wolf."*

---

## 0. The premise moved, and that is the main finding

The prompt's table lists three modules totalling ~6,800 lines as "~80 % of the harness a rebuild
needs", to be revived in order. Read in parallel, one agent per module, the measured position is
different and it changes the shape of the work:

**One of the three is the harness. The other two are not comparators at all, and one of them cannot
become one.** The prompt anticipated this — *"If revival turns out to be the wrong call for one of the
three, say so with the evidence and move on. Two working comparators beat three half-revived ones."*
The evidence says it about two of them.

| Module | Lines | Verdict | Deciding evidence |
|---|---:|---|---|
| `replay_acceleration_task2_semantic_acceptance.py` | 3,433 | **REVIVED — and not edited** | Its `compare_role_rows` runs against the sealed arms today with zero modifications [MEASURED]. The row/field difference engine, the 38-entry volatility allowlist and the preimage validator are all present and correct |
| `replay_acceleration_partial_golden_verifier.py` | 2,008 | **NOT REVIVED** | Outcome-blind **by contract**: `verifier.py:1534-1542` hard-requires `semantic_result_values_emitted: False` and `persisted_result_files_hashed_as_opaque_bytes: True`. Its finest possible output is `ledger_hash_mismatch:{role}` (`:1694`) — *which* of eight ledgers, never where [VERIFIED] |
| `replay_acceleration_streaming_archive_verifier.py` | 1,353 | **NOT REVIVED** | Verifies one archive against its own manifest; it never accepts two archives. Its input format does not exist for any sealed arm, and producing it means editing `b7_5_post_acceleration_runner.py:825-826` — a **bound, executing** file — then re-running arms at ~16.5 h/window [VERIFIED] |

**What replaced the third.** The sealed arms' cold surfaces use a different format
(`gtos.b7_5.cold_jsonl_archive.v1`) with a reader already written and, decisively, **unbound by either
contract**: `research/operations/…_2026_07_16/b7_5_cold_evidence.py`. Verified against R2, R1 and
`code_authority_paths` — zero matches in all three [MEASURED]. Its `RawOrColdResolver` streams a 4 GB
logical ledger through the `zstd` binary and is seekable.

**Net effect on the prompt's cost model.** The deliverable needed no edit to any contract-bound file,
and no edit to `task2` either. `verification_tooling` freedom was necessary to *build on* it, not to
change it.

---

## 1. Criterion-by-criterion

| # | Criterion | Verdict | Evidence |
|---|---|---|---|
| 1 | Takes two arm outputs | **MET** | `ArmOutputs` discovers each arm's prefix from disk; four sealed January arms read, including the three cold-only roles [MEASURED] |
| 2 | Reports **where** they differ, at row and field | **MET** | §3. Cross-arm S0R0 vs S1R0 localises to `(row_key, field_path)`; unmatched rows named by key [MEASURED] |
| 3 | Fails closed on a difference it does not understand | **MET** | §4. Nine distinct fail-closed rules, each pinned by a behavioural test that fails against the pre-fix code [MEASURED] |
| 4 | Does not cry wolf on a known-identical pair | **MET** | §3. Five flat roles / 9,653 rows EQUIVALENT; 69,888 cold decision rows EQUIVALENT [MEASURED] |
| 5 | `IMPLEMENTATION_STATE.md` updated with evidence tags and declared gaps | **MET** | B27–B30 |
| 6 | Receipt in the shape of `GATE_G0_RECEIPT.md` | **MET** | this file |

---

## 2. What was built

`src/research_infra/replay_differential_harness.py` (~1,000 lines) and
`tests/test_replay_differential_harness.py` (**43 behavioural tests**, all green [MEASURED]).

It is a **driver**, not a new comparison semantics — the anti-drift rule in the prompt §5. The
difference engine (`task2._difference_paths`), the allowlist lookup (`task2._entry_for_path`), the
value-class rules and the preimage validator (`task2._validate_runtime_hash_preimages`) are imported
unchanged. The four things it adds are the four things `task2` does not have:

1. **Arm resolution not bound to one worktree or one arm.** `task2.PREFIX` (`task2:31-34`) is a module
   constant naming `S0R0`, and `_role_path` (`:2375-2376`) builds every path from it — so `task2` can
   address exactly one of the four arms [MEASURED]. `ArmOutputs` derives the prefix from the directory
   and validates nothing against a repo root, so H4's path binding is not inherited.
2. **Reading the cold archives.** `task2._role_rows` (`:2395-2400`) routes to an archive only when a
   *zero-byte* flat `.jsonl` sits beside a `streaming-proof-archive/CAMPAIGN_ARCHIVE_MANIFEST.json`.
   On the sealed arms neither exists, so it raises `FileNotFoundError` on `decision`, `scorecard` and
   `missed` — 15.6 GB logical per arm, the three biggest surfaces [MEASURED].
3. **Enumerating differences instead of raising on the first.** `compare_role_rows` raises at
   `task2:962-967`. Correct for an acceptance gate, useless for localisation.
4. **Identity alignment.** `compare_role_rows` zips positionally (`task2:943-948`) and raises
   `semantic_row_count_mismatch`. Positional stays the default — it is right for the Phase-2 case, the
   *same* arm on a new engine — but two different arms need a key join.

**The join key, measured rather than assumed.** `(canonical_replay_candidate_instance_key,
order_event_stage)` is unique across all four arms for `order` (182/176/156/148 rows, 0 duplicates);
`canonical_replay_candidate_instance_key` alone is unique for `trade` and `oracle` [MEASURED]. The
stage is required because each candidate instance emits an `accepted_pending` row and a terminal row.
Roles without a measured-unique key refuse identity alignment rather than guess, and a declared key
that turns out non-unique fails closed with `identity_key_not_unique`.

---

## 3. Discrimination evidence [MEASURED]

Committed receipts, produced by the CLI against the sealed arms in
`/Users/borr/GTOSActive/worktrees/replay-accel-engine-20260719/…/attempt_5_typed_sparse/`:

**It does not cry wolf** — `receipts/harness_self_comparison_all_roles_S0R0.json`, exit 0. A whole
sealed arm, **every one of the eight roles**, no role excluded:

| role | rows | storage | status | non-finite leaves |
|---|---:|---|---|---:|
| source | 867 | raw | EQUIVALENT | 0 |
| order | 182 | raw | EQUIVALENT | 0 |
| trade | 90 | raw | EQUIVALENT | 0 |
| oracle | 91 | raw | EQUIVALENT | 0 |
| bucket | 8,490 | raw | EQUIVALENT | 0 |
| decision | 69,888 | **cold** | EQUIVALENT | 0 |
| scorecard | 2,016 | **cold** | EQUIVALENT | **34,640** |
| missed | 154,299 | **cold** | EQUIVALENT | 0 |

**235,923 rows — ~15.6 GB logical across the three cold surfaces — in 782 s at 370 MB peak RSS**, zero
roles unavailable [MEASURED]. The three `cold` rows are the surfaces the prompt's third module was meant
to reach and could not.

**It finds what is there** — `receipts/harness_cross_arm_S0R0_vs_S1R0.json`, identity alignment, exit 1:

| role | left | right | matched | left-only | right-only | unknown diffs | allowlisted |
|---|---:|---:|---:|---:|---:|---:|---:|
| order | 182 | 156 | 142 | 40 | 14 | 8,269 | 690 |
| trade | 90 | 77 | 70 | 20 | 7 | 4,043 | 272 |

Each difference carries `row_key`, `left_row_index`, `right_row_index`, `field_path`, `classification`
and `reason`. Unmatched rows are named by key. The difference counts are **totals**, while the receipt
retains 25 per role under the recorded `max_differences_per_role` — before the adversarial pass those
same runs reported `unknown_difference_count: 24`, i.e. the cap rather than the finding.

**Day-bounded comparison works** — `receipts/harness_day_bounded_2026_01_02.json`, `--end-day
2026-01-02`: 10 order rows and 5 trade rows per side instead of 182/90. This is the cheapest available
answer to **H5**: `task2.rows_through` gives a day-bounded *prefix* without a sub-window replay. It is
a prefix, not an arbitrary window — stated plainly because `exact_scope_rows` (which takes a start day)
raises on out-of-scope rows rather than filtering, and was not wired.

**Memory is not the constraint here.** Peak RSS 369 MB on the largest workload run [MEASURED],
against H3's 8.61 GB/arm. Everything streams; nothing materialises a ledger.

---

## 4. Fail-closed rules, each pinned by a test

`EQUIVALENT` requires: at least one role compared, every role readable *and non-empty*, no unmatched
rows, no truncation, and zero unknown differences.

| Rule | Mirrors | Test |
|---|---|---|
| Unclassified difference → UNKNOWN | `task2:962-967` | `test_a_single_economic_field_change_is_located_by_row_and_field` |
| Exact roles admit no normalisation | `task2:958-959` | `test_exact_roles_admit_no_normalization_at_all` |
| Allowlisted clock slot must hold a real UTC stamp | `task2:970-977` | `test_an_allowlisted_clock_slot_holding_a_non_timestamp_is_unknown` |
| Allowlisted hash slot must hold a real SHA-256 | `task2:979-982` | `test_an_allowlisted_hash_slot_holding_a_non_hash_is_unknown` |
| Hash closure must be proven | `task2:1013-1021` | `test_an_allowlisted_hash_without_a_proven_closure_is_unknown` |
| The `risk_authority` alias needs the packet on both sides | `task2:990-991` | `test_the_risk_authority_alias_shortcut_requires_the_packet_on_both_sides` |
| A row's hashes must match their own preimages | `task2:951-952`, `:862-902` | `test_a_hash_that_contradicts_its_own_preimage_is_unknown` |
| Two NaNs are never silently equal | `replay_canonical_bytes` | `test_two_nans_are_never_silently_equal` |
| Zero rows on both sides is not equivalence | — | `test_zero_rows_on_both_sides_is_not_equivalence` |
| A zero-byte archive-role ledger is a demotion marker | `task2:2397` | `test_a_zero_byte_archive_role_is_a_demotion_marker_not_an_empty_ledger` |
| Truncation alone blocks equivalence | — | `test_truncation_alone_blocks_equivalence` |

The load-bearing one is `test_the_harness_and_task2_agree_on_what_is_equivalent`: it feeds the same
fixture to both comparators and asserts `task2` raises where the harness reports DIFFER. That is the
correctness property — the harness's `EQUIVALENT` is never weaker than `task2`'s.

---

## 5. The adversarial pass, and what it changed

Two agents briefed to **refute with `file:line`**, defaulting to "refuted" when uncertain, with write
access only to a scratchpad. They returned **22 findings, 20 confirmed by execution**, and the first
version of the harness was wrong in ways that matter. Everything below is fixed and pinned.

**The two that mattered most, both false greens:**

1. **`PREIMAGE` was asserted without ever checking a preimage.** `task2` earns that word: it runs
   `_validate_runtime_hash_preimages` on both rows before comparing anything (`task2:951-952`). The
   first version handed out `ALLOWLISTED_DERIVED_HASH_PROVEN` on a pattern-string match alone, so a row
   whose declared `risk_authority/packet_hash_sha256` contradicted its own material compared
   **EQUIVALENT** where `task2` raises `risk_packet_hash_invalid`. That is precisely the Phase-2 defect
   class — a rebuilt engine recomputing a packet hash over slightly different material — and it was the
   one class the harness waved through. The agent also observed that my own fixture *encoded the bug as
   correct*, using `"a"*64` (the hash of nothing) and asserting equivalence. Fixtures now seal every
   hash from its own preimage; three tests changed meaning as a result.

2. **The harness crashed on real sealed evidence, on the default invocation.** `scorecard` rows carry
   `Infinity` as a "no ceiling" sentinel — **26 of the first 40 rows in every one of the four arms**
   [MEASURED] — and `task2.canonical_bytes` refuses non-finite floats since P1 (`e5c7ce30a`). With no
   `--role`, `scorecard` is in the default intersection, so the run died with no report at all. The
   diff encoder is now total: non-finite floats are replaced by stable markers so `inf == inf`, `NaN`
   is reported UNKNOWN at its own path even when both sides carry one, and every non-finite leaf is
   counted in the receipt. Nothing non-finite is hashed into an authority digest.

**Also fixed:** unknown/allowlisted counts were summed over the already-capped list, so a receipt could
say `unknown_difference_count: 0` on a run that found two economic changes — counts are now totals, the
cap is recorded in the receipt, and an unknown displaces a benign entry rather than being dropped ·
identity pass two materialised *every* changed row, contradicting its own docstring and reaching ~19 GB
on the `missed` surface — now bounded by `max_detailed_rows`, with undetailed rows blocking equivalence
· identity decided equivalence from row digests, so it could never certify the wall-clock case it exists
for — now the same rule as positional · `UNAVAILABLE` outranked a proven `DIFFER` · a `Mapping` proof
class raised `TypeError` · four sibling exception classes aborted a multi-role run · `_discover_prefix`
counted AppleDouble `._NAME` sidecars, so any arm copied via exFAT/SMB read as ambiguous · raw and cold
present together reported `raw` where the resolver refuses · absence and a real value rendered
identically under `--expose-values` · a self-comparison was not flagged as one.

---

## 6. A guard that was passing vacuously [MEASURED — FIXED]

`test_the_freed_verifiers_are_genuinely_unreachable_from_the_arm_path` exists to prove the OD-2 split
is not a behaviour hole. It shelled out to
`rg '^\s*(import|from)\b.*\bMODULE\b' src scripts` and asserted the hits were within an allowlist of
five paths.

**That regex matched nothing.** Every importer in this repo writes
`from src.research_infra import (\n    module_name,\n)`, so the module name never shares a line with
the `from`. An AST census finds **eight** modules that reach a freed verifier. The test has been
passing since it was written, and its allowlist of five was never exercised.

Found because the new harness imports `task2` and the guard did not notice. Replaced with an AST census
stating the property that actually matters — **no chain of imports leads from a sealed arm entrypoint to
a freed verifier** — which is stronger than an allowlist of direct importers (an allowlisted importer
that is itself on the arm path would still be a hole) and cannot be evaded by import style.

**The property itself holds:** both `b7_5_post_acceleration_runner` and
`replay_acceleration_attempt5_typed_sparse_runner` are transitively clean [MEASURED]. The eight modules
that do reach them are all verification tooling. Verified to discriminate: with an injected edge from a
sealed entrypoint, the census reports it.

---

## 7. Whole-suite A/B [MEASURED]

`scripts/pytest_failset.py`, whole suite, `--continue-on-collection-errors`, compared as **sets**.

```
before 212ad7e6d: 683 bad     after acad79826 (+working tree): 685 bad
unchanged: 683   fixed: 0   REGRESSED: 2
```

**Neither regression is attributable to this work, and both are proven rather than asserted.**

1. `test_end_to_end_integration.py::TestCrossComponentIntegration::test_high_load_integration` — the
   known non-deterministic test that `GATE_G0_RECEIPT.md:118-120` already carries as noise. Reproduced
   here: **failed 2 of 3 identical isolated runs** [MEASURED].
2. `test_permissions.py::test_scheduler_v4_terminal_gate_carries_ultimate_candidate_package_shadow_packet`
   — a **git-LFS hydration difference between worktrees**, not a code change. See B30: the file is
   205,754 bytes in the worktree the baseline was captured in and a **131-byte pointer** here.
   Proven causally by hydrating it, re-running (**1 passed**), and restoring the original bytes —
   restore verified by SHA-256 and by a clean `git status` [MEASURED].

Comparand committed at `receipts/phase2_harness_after_full_suite.json`.

**H1 checked before and after:** zero code drift. The two `DRIFTED` rows are B2/B3's known
`/Users/borr/GTOSActive/repo` resolution, unchanged by this work [MEASURED]. No contract-bound file was
edited.

---

## 8. Verdict

**Session D complete.** The harness takes two arm outputs and reports where they differ at row and
field level, fails closed on nine distinct classes of difference it cannot classify, and does not cry
wolf on a known-identical pair — including on the 4 GB cold surfaces the prompt's third module was
supposed to reach and could not.

Two of the three named modules were not revived, with the evidence in §0. That is the prompt's own
instruction followed, not scope dropped.

---

## 9. Declared gaps — required output, not an admission

- **The `missed` role has no measured-unique identity key**, so cross-arm identity alignment is
  unavailable for the largest surface (154,299 rows / 7.6 GB logical). Positional works. A key can be
  declared with `--identity-key`, and uniqueness is verified at runtime, but I did not measure one.
- **`scorecard` and `decision` likewise have no declared key.** `decision` rows look keyable on
  `(row_type, symbol, decision_time_utc)` and `scorecard` on `(asof_utc, candidate_set_id)`, but I did
  **not** verify uniqueness across all four arms, so neither is declared.
- **No cross-arm comparison of the three cold roles has been run end to end.** `decision` was compared
  self-to-self (69,888 rows) and `scorecard` self-to-self; a cross-arm cold run is hours of wall clock
  and was not part of establishing the deliverable.
- **`compare_state_checkpoint_semantics` and the `candidate` role are out of scope.** They need the
  `.semantic-diagnostic` sibling directory, which exists for **S1R1 only** of the four arms
  [MEASURED]; regenerating it for the others means re-running the slice runner.
- **`validate_campaign_hash_closure` was not wired.** Without a supplied proof map, allowlisted hashes
  outside the four self-proving preimage patterns classify UNKNOWN. That is the safe direction, and it
  means a real accelerated-vs-reference run will report more unknowns than `task2` would with its proof
  map built. Building that map needs the `.semantic-diagnostic` order-preimage ledger — the gap above.
- **`replay_semantic_parity.py` (1,875 lines, unbound) was found and not used.** It has a genuine
  two-sided `compare_semantic_streams` plus relational validation (candidate identity, sidecar
  ownership, order sequences) that this harness does not do. It also raises rather than localises, and
  its receipt is role-level only, which is why `task2` was the better base. Its relational checks are
  the obvious next increment.
- **The harness has never been run against output from a *different engine*.** Everything measured here
  compares sealed arms with each other. The Phase-2 case — old engine vs new — does not exist yet by
  construction, so the positional path is exercised only on same-shape inputs.
- **`--end-day` gives a prefix, not a window.** Comparing day 17 alone still reads days 1–17.
- **One adversarial finding was left unfixed, deliberately.** `zstd` is resolved from `PATH` unpinned
  by the cold reader (`b7_5_cold_evidence.py:427-433`), so a `zstd` upgrade silently changes the
  decompressor underneath the harness. Its own `.cold` manifests pin the binary path *and* its SHA-256,
  so the material to close this exists — but the fix belongs in the reader, which is a different
  module's contract, not the harness's. The resolver is now constructed lazily, so a flat-only
  comparison no longer needs `zstd` present at all.
