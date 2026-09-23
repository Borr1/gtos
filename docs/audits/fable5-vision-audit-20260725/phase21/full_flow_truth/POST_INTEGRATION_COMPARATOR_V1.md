# Wave 21 — post-integration full-flow comparator, V1

Produced 2026-08-11 on branch `wave21/post-integration-measurements` (fresh worktree from
`origin/main = 2edefd48a`). This is the `ROUTE_STATUS.json` `full_flow_comparison` phase:
the fresh producer run of the retained multiday comparator (frozen development days
2025-10-28 / 2025-11-03 / 2025-11-07, preregistration `WAVE21_MINIMAL_REPAIR_MULTIDAY_
PREREGISTRATION.json`, sequential one-day-at-a-time) under integrated code, diffed against
the retained pre-integration results.

**Two headlines, both measured:**

1. **`main@2edefd48a` unmodified CANNOT run the comparator.** Two structural fail-closed
   walls (§2): the committed `source-worker` CLI's un-integrated v2 source-authority stub,
   and — deeper — a three-lane composition that kills every non-truth-mode
   `run_campaign` at its first candidate-bearing decision window. No fresh producer run
   had ever executed post-merge; these walls are why.
2. **A bounded two-edit compose repair (committed on this branch only) unblocks the
   producer path, and the three-day matrix was then executed serially into fresh
   `/private/tmp` roots.** Candidate populations are IDENTICAL to the retained runs
   (23,309 identities, zero churn, exact occurrence conservation both sides, all three
   days). The behavioral delta is concentrated in ONE stage — the selector/package-router
   layer — while cost, session, quote-walk and generation are byte-stable (§4). The
   independent verifier REFUSES all three fresh runs at a producer/verifier
   serialization divergence (§5) — so **no result-bearing economics claim is made**; the
   arm is an engineering comparator measurement of integrated-code behavior.

Frozen reserve days (2025-10-31, 2025-11-05) never touched; no READ_RESTRICTED pool
opened; `/private/tmp/w21-market-top-aprmay-r3` not read.

## 1. Runs of record

| arm | code | 2025-10-28 | 2025-11-03 | 2025-11-07 |
|---|---|---|---|---|
| retained pre-integration baseline | minimal-raw lane revisions (all ancestors of main) | `wave21-minimal-repair-20251028-875037f1b-r4` | `wave21-minimal-repair-20251103-f3ae1a210-r1` (final XAU-repair run) | `wave21-minimal-repair-20251107-875037f1b-r1` |
| fresh post-integration | `2edefd48a` + compose repair (this branch) | `wave21-postinteg-20251028-2edefd48a-repair-r1` | `wave21-postinteg-20251103-2edefd48a-repair-r1` | `wave21-postinteg-20251107-2edefd48a-repair-r1` |

Baseline-of-record identification is by receipt-sha256 match against
`WAVE21_MINIMAL_REPAIR_MULTIDAY_RESULT.json` `artifact_bindings`. Invocation:
`run_post_integration_comparator.py` (committed, this directory) — `run_source_bound_worker`'s
body with `source_authority=None` at `execute_full_flow`, which is byte-for-byte the
recorded producer semantics of every retained run and of the DAG-session's own fresh
one-day proof (all record `inputs.source_authority == {}`; verified by direct read). Estate
byte-verification and lane source loading unchanged. ~18 min and ≤2.14 GB peak footprint
per day, serial.

**The attribution boundary holds:** the two retained 2025-11-03 runs at different engine
revisions (`875037f1b` vs `f3ae1a210`, different code manifests) diff to **zero** — same
identities, same censuses, zero transitions
(`post_integration_comparator/CONTROL_20251103_875037f1b_vs_f3ae1a210.json`). Every delta
below therefore attributes to the post-`f3ae1a210` integration interval.

## 2. Why unmodified HEAD cannot run, and the two-edit repair

**Wall 1 — committed CLI.** `wave21_full_flow_harness.py source-worker` forwards the
verified estate authority into `execute_full_flow`;
`_loader_owned_raw_source_authority_fields_by_symbol` (`:2525-2537`) is a deliberately
fail-closed stub for the producer-attached v2 receipt machinery — the un-commissioned
truth-chain work `WAVE21_INTEGRATION.md` §11 left in the `wave21-timewarp-flow-truth`
worktree. Any non-empty authority raises
`loader_owned_source_authority_receipt_v2_dependency_not_integrated` (measured, attempt 0).
The committed `source-worker` has been structurally unrunnable since the harness recovery
commit `ea3a2f4d9` (verified at that revision).

**Wall 2 — three merged lanes compose into a dead end** (measured at the first
candidate-bearing window, probe committed:
`post_integration_comparator/PROBE_FIRST_WINDOW_REPORT.json`, 10/10 rows key-less):

| commit (2026-08-09) | lane | contribution |
|---|---|---|
| `9f1b8caa1` freeze candidate lineage through scheduler joins | coherence-candidate-lineage | `run_campaign` forces `_pristine_scheduler_sidecar_sink={}` into EVERY `schedule_window` (`v4_timewarp_simulated_live_research_loop.py:93447-93456`) |
| `fb522394a` bind scheduler pristine projection | scheduler-pristine-projection | with a sink, the allocator demands a non-empty strictly-recomputable `candidate_occurrence_key` on every window candidate (`moonshot_scheduler_v4_best_trade_allocator.py:28347-28362`), fail-closed |
| `54023d082` enforce causal source chronology and occurrence identity | chronology/coherence | the composed generator materializes occurrence keys **only under truth mode** (`broader_origin_generators.py:541-556` — `_materialize_candidate_occurrences` inside `if truth_mode:`) |

Non-truth candidates carry no occurrence fields, so
`scheduler_pristine_candidate_occurrence_missing` kills the window. The timewarp's own
inner conditional (`:83872-83890` — pristine path only when the sink is passed OR a
candidate claims the occurrence contract) and the downstream validator
(`validate_pristine_scheduler_candidate_options_by_occurrence` — clean return on
None-sidecar + no owners) both already encode the intended compose; the unconditional sink
at the caller is the one construct fighting them.

**The repair (this branch, commit-scoped, R2-forward-break register applies):** two edits
in `v4_timewarp_simulated_live_research_loop.py` — (1) build the sidecar sink exactly when
a window candidate claims the occurrence contract (the module's own
`candidate_occurrence_contract_claimed`), keep the capture assertion symmetric; (2)
None-guard one downstream read that only binds for truth-path instance keys. Truth-mode
behavior unchanged: claimed occurrences still force the sink and the full pristine
contract. This is repair route (2) of three; the durable fix remains the owning lane's
truth-chain landing (§6).

## 3. Delta tables (retained baseline -> fresh post-integration arm)

Machine-readable: `post_integration_comparator/REPAIR_ARM_DELTAS_V1.json` + the three
per-day `DIFF_*.json`; censuses recomputed identically on both sides by the committed
`diff_day.py`. Selector censuses are `raw_selector_*` over missed rows (8,661/8,276/6,345
rows post vs 8,662/8,273/6,345 pre) — not the RESULT.json effective-action census.

**3.1 Conserved exactly, all three days:**

| invariant | status |
|---|---|
| candidate occurrence identity sets | IDENTICAL (8,670 / 8,284 / 6,355; zero pre-only, zero post-only) |
| disjoint-terminal occurrence conservation | exact on both sides, every day (missed ∪ orders ∪ trades, zero overlaps) |
| generator call/slot counts | 2,304 slots/day, zero silent-continues, both sides |
| cost-reason censuses (`packet_refused` / `above_ceiling` / `ev_negative`) | byte-equal per day (1193/3057/410; 743/2199/282; 270/1517/41) |
| off-session census | byte-equal (520 / 533 / unchanged) |
| shared trades' `net_r` | byte-equal on every shared trade (4 across the three days) |

**3.2 What moved — one stage, the selector/package-router layer (first dispositions):**

| reason (missed rows) | 10-28 | 11-03 | 11-07 |
|---|---|---|---|
| `broker_net_probability_confluence_lifecycle_admission_passed` | 549 -> 5 | 664 -> 7 | 776 -> 5 |
| `ultimate_candidate_package_dynamic_router_refusal_softened_reduce_risk` | 662 -> 933 | 1109 -> 1522 | 624 -> 1035 |
| `admission_quality_dynamic_router_refused_candidate_use` | 850 -> 1213 | 662 -> 993 | 655 -> 1092 |
| `source_bound_router_refusal_open_reduced_materialized_for_replay` | 219 -> 406 | 271 -> 480 | 294 -> 522 |
| `numeric_confluence_structured_disagreement` | 1036 -> 758 | 1629 -> 1336 | 1230 -> 925 |

The clean-admission census collapses (~99% of previously admission-passed candidates now
land in package-router refusal/softening or open-reduced materialization) and part of the
confluence-disagreement census migrates into router reasons — i.e. the router now rules
earlier/wider than pre-integration.

**3.3 Orders and trades:**

| day | orders pre->post | trades pre->post | scoreable net R sum pre->post | shared trades |
|---|---|---|---|---|
| 2025-10-28 | 8 -> 9 | 6 -> 8 | +1.1146 (6) -> +2.3030 (6) | 1 (UK100 fvg, net byte-equal) |
| 2025-11-03 | 11 -> 8 | 9 -> 6 | +2.0687 (8) -> −5.3509 (5) | 1 (JP225 fvg, net byte-equal) |
| 2025-11-07 | 10 -> 10 | 10 -> 7 | −0.1934 (9) -> +2.5672 (5) | 2 (GER40, SPX500 fvg, nets byte-equal) |
| total | 29 -> 27 | 25 -> 21 | — | 4 |

**Family-selective signature** (full lists in `REPAIR_ARM_DELTAS_V1.json`): of the 17
gained trades, **14 are `current_fvg_fill`** (all 10 gained on 11-03/11-07, 4 of 7 on
10-28; the other three on 10-28 are 2 `session_open_range_break` + 1
`structural_distance_extreme`); the 21 lost trades are dominated by
`liquidity_sweep_reclaim`, `displacement_continuation`, `current_ob_retest`,
`session_open_range_break` — including the 2025-11-03 gold-trace XAUUSD 07:15
liquidity-sweep trade (−1.047 net, the anchor of the retained result's "gold trace"
narrative) and the day's three largest winners (+1.94, +1.71, +1.95) — with one honest
counter-instance (a UK100 `current_fvg_fill` also lost on 11-07). Lost trades' candidates
almost all transition to `source_bound_router_refusal_open_reduced_materialized_for_replay`.

The small trade samples mean the net-R swings carry no evidential weight; the
DISPOSITION movement (hundreds of rows per day, one-directional into the router layer) is
the measured effect.

## 4. Delta classification by stage and commit-class

| observed delta | stage | commit-class | evidence |
|---|---|---|---|
| none | generation / candidate identity | chronology + identity lanes: **no effect** | identity sets identical; slot counts equal; zero chronology terminals on these 2025 days |
| none | quote walk / exit pricing | quote-side lane: **no effect** on this population | every shared trade's `net_r` byte-equal |
| none | selector cost gate | cost-truth lane: **no effect at this stage** | three cost-reason censuses byte-equal per day |
| admission-pass collapse into router refusal/softening/open-reduced; trade-set exchange with `current_fvg_fill` concentration | selector/package-router | **identity/package-authority class** (candidate-package router + admission-order/coherence semantics merged in the fsc stack) | §3.2/§3.3 censuses + transitions |
| producer audit `status: FAIL` with `candidate_identity_contract_not_v2` on all candidates (while `occurrence_disposition_conservation_exact: true`) | verification | truth-chain/verification class (un-merged owning-lane contract) | fresh run receipts |
| independent verifier REFUSED | verification | see §5 | all three fresh runs |

**The commit-level CAUSE of the router-layer movement inside the integrated interval is
left OPEN — deliberately not smoothed.** The class is established (package-router
authority; not cost, not quote, not chronology, not generation identity); whether the
specific router semantics are the intended composed contract or a defect (e.g. a
package-role/family join now refusing families it should admit) is exactly the
adjudication the owning lane must make, with per-commit bisection arms if wanted. Until
then, the fresh arm's trade set must not be treated as "the post-integration truth of what
would have traded" — only as the measured behavior of the integrated router layer.

## 5. Verification layer: what still refuses, precisely

1. **Producer in-band DAG audit** stamps `status: FAIL` on all three fresh runs:
   `candidate_pre_scheduler_contract_failure_count` = all candidates
   (`candidate_identity_contract_not_v2`) while simultaneously proving
   `occurrence_disposition_conservation_exact: true` under the repaired
   `candidate_occurrence_disjoint_terminal_v1` model. The v2 identity contract is part of
   the un-merged truth-chain surface.
2. **Independent verifier REFUSES all three runs** at
   `independent_occurrence_stage_dag_mismatch` (`wave21_full_flow_verifier.py:2183`).
   Root-caused by standalone recompute: the producer's stored audit and the verifier's
   recomputation agree on every count and every failure REASON but serialize
   candidate-contract failure records in different shapes (producer embeds the identity
   blob; verifier emits `reason` + row index), so the stable-hash comparison fails. The
   f791a7c28 DAG repair aligned the model and was mirror-proved on retained ledgers whose
   failure records were of the ordinal class; the `candidate_identity_contract_not_v2`
   record shape was never co-executed until this session — no fresh producer run existed.
3. **Relational identity audit v2** on fresh runs: `identity_coverage_exact: true` (all
   unions exact) but `exact: false` because the v2 schema additionally demands
   exit/account terminal reconciliation
   (`status: incomplete_identity_coverage_only_requires_exit_account_terminal_reconciliation`).
   A strictness increase, not a conservation break.

Consequence: **result-bearing economics claims from the comparator remain blocked**, now
for named, exact reasons in the verification layer rather than an unmeasured "not rerun
yet".

## 6. What unblocks what (repair routes, unchanged in substance)

1. **Land the owning lane's truth-chain window-flow work** (`wave21-timewarp-flow-truth`
   worktree: `wave21_truth_stage_chain.py`, `wave21_truth_window_flow.py`, +642 timewarp
   lines, +82 sink lines; §11 of the integration receipt routes it to its own session +
   A/B). Expected to supply: v2 identity contract, producer-attached occurrence/source
   authority (un-stubbing the committed `source-worker`), and the audit/verifier record
   alignment.
2. This branch's two-edit compose repair — adequate for engineering-comparator producer
   runs; adopt or supersede at the owning lane's discretion.
3. Producer/verifier failure-record serialization alignment — small, but belongs with (1)
   so the record shape is designed once.
4. The package-router adjudication of §4 — decide intended-vs-defect for the
   family-selective admission collapse before any downstream consumer reads the fresh
   trade set as truth.

## 7. Scope and claim boundary

Offline `research_timewarp` engineering comparator; no broker client, no activation token,
no live state, no config byte changed; SimulatedBroker only; abstract R sizing. The three
frozen days are already-opened development data. Nothing here is production parity, broker
fill truth, or a strategy-profit result; the retained runs' own claim boundaries carry
over unchanged. The compose repair lives on this branch, is NOT merged to main by this
session, and its two touched files stay on the wave-21 R2 forward-seal-break register the
integration receipt §7 already carries for them.
