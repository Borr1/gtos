# HM Falsifier Reconciliation — Session FA (continuation), Phase A0

Date: 2026-08-03. Worktree: `/Users/borr/GTOSActive/worktrees/fa2-integration-20260803`
(branch `phase19/fa2-integration`, HEAD `4ae182bb675210357c77afec6e4edc06c77275af`). No commits made.

## 1. The gap being reconciled

Session HM froze its adapter falsifier
(`tests/research_infra/test_session_hm_p1_adapter_falsifier.py`, 70 tests) against adapter
sha256 `41ccd5de30318b758c54e1b977b08414ed9980bf93f9a661346f06e2db16074d` (43,805 bytes) at its
branch tip `ec4555696` — all 70 passed there
(`P1_ADAPTER_INDEPENDENT_FALSIFICATION.json → adapter_falsification.tested_source`).

Exactly **one** later commit changed the adapter:

- **`9059cfa06` — "fix(phase20): accept hash-proven sparse M1 bars"** (sole parent `f59fbb829`,
  the HN packet reconstruction). It rewrote the adapter to
  sha256 `4512f15f82b81dc1fb52d65d1c68e71929de3d95e683f80ce990e2121c1d9dd4` (47,434 bytes).

The falsifier test file itself was touched by **no commit** in `ec4555696..HEAD`
(`git log` over that path is empty), and HM's suite was never re-run after `9059cfa06`:
Session HP's A/B covered only the focused P1 set
(`SESSION_HP_COMPLETE.json → production_proofs.failure_set_ab`: parent 45 → source 52 passed).
Result on this branch before repair: **23 failed / 47 passed**.

## 2. What changed in the adapter (hunks of `9059cfa06` touching the falsifier's surface)

All in `docs/audits/fable5-vision-audit-20260725/phase20/receipts/wave20_complete_path_shadow.py`:

1. **Dependency identity-binding** — `run_complete_path_shadow` now refuses any stage callable
   that is not the exact in-module bound function, before invoking it, inside each stage's try
   block (so it records as a stage refusal with the denominator preserved):
   - `:903-904` `candidate_generator_dependency_not_bound` (bound: `source_bound_candidate_generator`, `:693-701`)
   - `:976-977` `dynamic_router_dependency_not_bound` (bound: `inert_admit_unchanged_router`, `:678-690`)
   - `:1023-1024` `scheduler_capture_dependency_not_bound` (bound: `inert_scheduler_capture`, `:704-715`)
   - `:1094-1095` `fill_projection_dependency_not_bound` (bound: `source_bound_fill_projection`, `:718-726`)
2. **Router mutation check** — `:978`, `:1006-1009`: routed candidate must canonical-hash-match
   the pre-router candidate (`dynamic_router_candidate_mutation_forbidden`).
3. **`FIXED_BREAKER_MEMBER_RECORD`** added (`:51-61`);
   `FIXED_BREAKER_MEMBER_CANONICAL_SHA256` changed `0de66ee7…` → `0de66ebe…` (now the canonical
   hash of the record, not of the bare member string).
4. **Top-level fail-closed integrity guard** — `:198-199`:
   `if canonical_sha256(FIXED_BREAKER_MEMBER_RECORD) != FIXED_BREAKER_MEMBER_CANONICAL_SHA256: raise RuntimeError(...)` —
   a module-body `ast.If` node.
5. Docstring rewrites declaring the new contract (module `:5-7`: "supply the four exact
   in-module, source-bound stage callables"; `ShadowDependencies` `:148`: "all identity-bound by
   the runner before use"); base payload gains `fixed_breaker_member_canonical_sha256` (`:817`);
   `__all__` gains the record and the four bound callables.

## 3. Was the change deliberate and receipted? Yes — four independent declarations

1. **Same-commit sibling test rewrite** (`tests/research_infra/test_wave20_complete_path_shadow.py`
   in `9059cfa06`): `_dependencies` switched to the four bound callables;
   `test_zero_or_multiple_generated_candidates_fail_at_generation` renamed to
   `test_unbound_candidate_generator_fails_closed` expecting
   `candidate_generator_dependency_not_bound`; new tests
   `test_unbound_router_cannot_enter_geometry_path`,
   `test_unbound_scheduler_and_fill_dependencies_fail_closed`,
   `test_bound_router_preserves_candidate_geometry`; the new record hash pinned in
   `test_fixed_b0_identity_and_geometry_are_unchanged`.
2. **HP's canonical falsification receipt**
   (`science/P1_UPSTREAM_PACKET_INDEPENDENT_FALSIFICATION.json`):
   `tested_source_commit = 9059cfa06`, `u11_status = "U11_REPAIRED_ADAPTER_AND_REFERENCES_BOUND"`,
   `adapter.sha256 = 4512f15f…`, and `required_adapter_callables` naming
   `source_bound_candidate_generator`, `inert_admit_unchanged_router`, `inert_scheduler_capture`,
   `source_bound_fill_projection`.
3. **`SESSION_HP_COMPLETE.json`**: `accepted_source.commit = 9059cfa06` (canonical packet
   re-frozen against it).
4. **The adopted A0/HV runner** (`src/research_infra/p1_offline_complete_path_runner.py:95-96`)
   binds `ADAPTER_SHA256 = "4512f15f…"`, `ADAPTER_BYTES = 47_434` — i.e. **the current adapter
   bytes are the bound contract of record**. Verified on disk this session:
   `shasum -a 256` reproduces `4512f15f…` / 47,434 bytes exactly.

## 4. Per-test classification (23 failures)

**All 23 are TEST-STALE. Zero are ADAPTER-DEFECT.** For each, the pinned property was verified
to still hold under the new contract — in every case at equal or greater strength — before the
expectation was updated. HM defect-family references are to
`P1_ADAPTER_INDEPENDENT_FALSIFICATION.json → proven_defect_families`.

| # | test (params) | HM family | old expectation | why it broke | classification / declaring evidence | repair | pinned property under new contract |
|---|---|---|---|---|---|---|---|
| 1 | `test_ast_transitive_closure_has_no_effect_capabilities` | AST closure (`nondeclarative_import_time_nodes: 0`) | no non-declarative module-body statements | adapter `:198-199` added a top-level `if …: raise RuntimeError` integrity guard (`ast.If`) | TEST-STALE — guard added by `9059cfa06`; its hash target pinned by sibling `test_fixed_b0_identity_and_geometry_are_unchanged` | narrow allowance: a module-body `ast.If` whose body is exactly one `ast.Raise` with no `orelse` | import may only *fail closed*; it still cannot DO anything — the import/effect-call sweeps run over the whole AST including the guard, closure set unchanged (verified: the 4 `src/` closure files had no commits in range), all other top-level statement kinds still forbidden |
| 2–4 | `test_bad_generator_cardinality_preserves_eleven_stage_denominator` (zero / two / mapping) | HM-F7 | `candidate_generation_candidate_count_not_one:{0,2}` / `…_result_must_be_iterable_of_rows` | injected generator now refused as not-bound before invocation | TEST-STALE — binding declared per §3 (sibling renamed its twin test to `test_unbound_candidate_generator_fails_closed` with the same new reason) | expect `candidate_generator_dependency_not_bound`; exact-reason assertion doubles as non-invocation proof (an invoked lambda would have produced the old reason); 11-stage denominator still asserted; **new test added** `test_bound_generator_zero_candidates_is_exact_cardinality_miss` pinning `candidate_generation_candidate_count_not_one:0` through the bound generator (source without `synthetic_candidate`) | denominator conservation intact; cardinality taxonomy still pinned at the one arity the bound generator can produce; the other two arities are unreachable-by-construction (bound generator returns 0 or 1 rows) and remain defense-in-depth code |
| 5–10 | `test_invalid_injected_hash_refuses_before_fill_dependency` (6 hash shapes) | HM-F6 | miss at `order_preimage`, fill never invoked | the *default* `_dependencies` generator lambda was refused first, moving the miss to `candidate_generation` | TEST-STALE — collateral of the binding, not of the hash check (which is unchanged at `:489-499`) | `_dependencies` defaults switched to the four bound callables; test body and expectations unchanged | identical: bad `profile_snapshot_sha256` still refuses at `order_preimage` before the fill stage; the injected fill lambda remains the never-invoked instrument (`calls == []`), now doubly guaranteed by the binding |
| 11 | `test_scheduler_input_mutation_is_isolated_refused_and_cannot_change_preimage` | HM-F4 | `scheduler_capture_input_mutation_forbidden` after invoking the mutator | mutating scheduler refused as not-bound before invocation | TEST-STALE — binding declared per §3 | expect `scheduler_capture_dependency_not_bound`; added `invoked == []` counter; kept source-hash-unchanged and `order_preimage == NOT_REACHED_PRIOR_STAGE_MISS` assertions | strictly stronger: the hostile mutation can no longer run at all (detect-before vs detect-after); the detached-copy isolation and the mutation-forbidden check remain in the runner (`:1025-1042`) as defense in depth for the bound (pure) scheduler |
| 12 | `test_scheduler_writer_object_is_never_invoked_and_becomes_exact_miss` | HM-F4 | `canonical_payload_unsupported:Writer` in the run-path miss | scheduler lambda refused before it could construct the writer payload | TEST-STALE — binding declared per §3 | run-path expectation → `scheduler_capture_dependency_not_bound` with `called == []`; **taxonomy re-pinned at its source**: `canonical_sha256({"writer": Writer()})` must raise `canonical_payload_unsupported:Writer` without invoking the writer | both halves preserved: writer objects are never invoked (now they are never even constructed), and the canonical-payload refusal taxonomy is still exact |
| 13–17 | `test_generated_candidate_identity_alias_refuses_before_transform` (candidate_id / symbol / side / direction / decision_time_utc) | HM-F5 | `candidate_generation_identity_mismatch:*` via injected drifted candidate | injection route closed by the binding | TEST-STALE — binding declared per §3 | identity drift planted in `source["synthetic_candidate"][field]`; run with fully bound deps; same expectations, plus new assertion `fixed_breaker_transform == NOT_REACHED_PRIOR_STAGE_MISS` | identical property through the only admitted route: the composite identity is bound from the source's top-level fields, and a drifted embedded candidate still refuses at `candidate_generation` (`_candidate_identity_mismatch`, `:755-784`) before the transform — verified for all 5 fields (side/direction collapse to `…:side_direction`) |
| 18–21 | `test_dependency_exception_becomes_first_miss_without_denominator_loss` (4 stages) | HM-F7 | `dependency_exception:RuntimeError` at each injectable stage | throwing lambdas refused as not-bound before they can throw | TEST-STALE — binding declared per §3 | expected reason per stage → `candidate_generator_dependency_not_bound` / `dynamic_router_dependency_not_bound` / `scheduler_capture_dependency_not_bound` / `fill_projection_dependency_not_bound`; denominator/uniqueness/single-miss assertions kept; exact-reason assertion doubles as non-invocation proof | denominator conservation at all four stages intact; the not-bound refusals land inside the stage try blocks so they record as ordinary first-misses; the `dependency_exception:` taxonomy stays live and pinned (see #22) at the non-injectable stages, whose `except Exception` handlers are unchanged |
| 22 | `test_hdf_exception_becomes_first_miss_without_denominator_loss` | HM-F7 | `dependency_exception:TypeError` at `hdf_exit_or_terminal` | only the default-lambda collateral (as #5–10) | TEST-STALE (collateral) | none beyond the `_dependencies` default switch — body and expectations byte-identical | identical; this test is now the standing pin of the `dependency_exception:` taxonomy and its denominator conservation |
| 23 | `test_one_dependency_refusal_cannot_drop_or_duplicate_another_identity` | HM-F7 | `dependency_exception:LookupError` for "bad", 22 unique rows | per-source selective raising generator can no longer be injected | TEST-STALE — binding declared per §3 | the selective refusal is planted in the source itself ("bad" carries no `synthetic_candidate` → `candidate_generation_candidate_count_not_one:0`); kept 22-row count and (identity, stage) uniqueness; **added**: exactly one miss, it is "bad", and all 11 "good" rows are neither `REFUSED` nor `NOT_REACHED_PRIOR_STAGE_MISS` | strengthened: the original asserted only row uniqueness and the miss reason; the repaired test additionally proves the unaffected identity *completes* — no drop, no duplicate, no cross-identity contamination |

No test was deleted; no invariant (identity uniqueness, denominator conservation, stage-count
exactness, broker-inertness, never-invoked hostile callables) was weakened. One test was added.

## 5. Changed hunks in the falsifier (the only file modified)

`tests/research_infra/test_session_hm_p1_adapter_falsifier.py` — +153 / −50:

1. `_dependencies` defaults: synthetic lambdas → the four bound adapter callables (overrides kept).
2. AST closure test: allowance for module-body `If` with a single `Raise` and no `orelse` (only).
3. Cardinality test: params re-ided, expected reason → `candidate_generator_dependency_not_bound`.
4. NEW `test_bound_generator_zero_candidates_is_exact_cardinality_miss`.
5. Scheduler-mutation test: `invoked` counter; expected reason → `scheduler_capture_dependency_not_bound`.
6. Writer test: run-path reason → `scheduler_capture_dependency_not_bound`; added direct
   `canonical_sha256` pin of `canonical_payload_unsupported:Writer`.
7. Identity-alias test: drift moved into `source["synthetic_candidate"]`; added transform
   NOT_REACHED assertion.
8. Dependency-exception test: per-stage expected reasons → the four `*_dependency_not_bound` strings.
9. Two-identity isolation test: bound-generator selective-failure construction; added
   single-miss/bad-identity/good-completes assertions.

## 6. Final counts

| suite | before | after |
|---|---|---|
| `test_session_hm_p1_adapter_falsifier.py` | 23 failed / 47 passed | **71 passed, 0 failed** (70 repaired + 1 added) |
| `test_wave20_complete_path_shadow.py` | 33 passed | **33 passed** |
| `test_p1_upstream_packet_verifier.py` | 42 passed | **42 passed** |
| `test_p1_offline_complete_path_runner.py` | 33 passed | **33 passed** |
| `test_p1_upstream_reconstruction.py` | 19 passed | **19 passed** |
| (adjacent, same commit) `test_p1_upstream_m1_provenance_verifier.py` | — | **17 passed** |

## 7. STOP conditions

None hit. Adapter bytes unchanged: sha256
`4512f15f82b81dc1fb52d65d1c68e71929de3d95e683f80ce990e2121c1d9dd4`, 47,434 bytes — still exactly
the `ADAPTER_SHA256`/`ADAPTER_BYTES` bound in `p1_offline_complete_path_runner.py` and in HP's
canonical packet receipt. No March/live-forward data read. No commits made.
