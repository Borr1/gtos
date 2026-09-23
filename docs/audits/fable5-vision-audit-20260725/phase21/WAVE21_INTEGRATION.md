# Wave 21 integration — merge train receipt

Integrated by the wave-21 integration engineer (Fable 5), 2026-08-10, under owner approval
recorded for this merge train. Integration branch: `wave21/full-flow-truth-20260808`.
Base: `origin/main = 9392e9bbd` ("Wave 20 forward"). Commission commit `957195397` sits
directly on it.

## 1. What merged (branch -> merge commit on the integration branch)

Phase A — pre-integration truth lanes (fork points at/before `957195397`):

| branch | tip | merge commit | note |
|---|---|---|---|
| wave21/timewarp-flow-truth-20260808 | e8d9fcf29 | 378ae0303 | staging branch; **wave21/candidate-semantics (8ecc79018) lands HERE in superseding form** (its residual vs staging is 133 lines of older pre-image; verified before merge) |
| wave21/selector-truth | 07f81cc1f | 14328b185 | brings the truth-mode module |
| wave21/scheduler-risk-truth | c5857b0d3 | bc7865aa4 | tree-identical to selector-truth (verified empty diff) |
| wave21/full-flow-harness | ea3a2f4d9 | 7469a9181 | includes the recovery commit (see §3) |
| wave21/quote-execution-truth | 439020364 | c590414a3 | content already byte-identical in integ (cherry-picked lineage) |
| wave21/cost-truth | 38e65184d | 5ff341fbb | patch-id ≡ 7d6bbca7a already in integ |
| wave21/w7-recost-current | ba30c0d4b | d246f7de6 | 10 add/add conflicts resolved to branch side (strictly supersedes the cherry-picked first commit) |
| wave21/verification | 3ed0da7f7 | 99f245c79 | patch-id ≡ f4d46e959 |
| wave21/p3-stop-floor | 7fda591ef | 17e5b6371 | patch-id ≡ ce3be027a |
| ops/vps-ceremony-cm-cn-20260806 | 530b08b21 | bb11676bf | LN records; pure phase19 receipts/docs, no src/config |
| ops/vps-live-health-20260803 | a78c4e447 | (contained) | already-up-to-date under the ceremony merge |

Phase B — the coherence stack (fork point `ce3be027a`):

| branch | tip | merge commit | note |
|---|---|---|---|
| wave21/full-system-coherence-20260809 | dc53468b6 | d6f3355f9 | 47 commits; the one conflicted file composed (see §4) |
| wave21/minimal-raw-smoke-20260808 | c994eb564 | (contained) | ancestor of fsc |
| wave21/coherence-selector-quality | 01446b383 | (contained) | ancestor of fsc |
| audit/package-admission-order-route-20260809 | fe5ab2b15 | (contained) | ancestor of fsc |
| wave21/causal-graph-integrator-20260809 | 5a1b66cb7 | (contained) | ancestor of fsc |
| wave21/coherence-cost-accounting | 8c7755052 | 3d71d4626 | dup pair afe3f6908/8c7755052 — patch-id SAME, clean |
| wave21/coherence-timewarp-order | 7ffc7cbe9 | 4b87bcf6c | dup pairs 3b82310ac/7ffc7cbe9 + fe5ab2b15/fa3c4b448 — patch-id SAME; plan-doc conflict kept the owner-approved wording |
| wave21/coherence-candidate-lineage | 4737a1fb4 | 4ef05bf61 | all 7 unique commits patch-represented; zero content drift proven |
| wave21/coherence-full-flow-audit | 283b93bb4 | 5ff1379a7 | lineage join, ours on 3 supersession residuals |
| wave21/coherence-quote-execution | 8943cf6cf | a4dc6608a | ours incl. deliberate later "strictly-before-horizon" wording (3f359b5a9) |
| wave21/coherence-scheduler-risk | 3e3d508ad | 52a33ba49 | lineage join |
| wave21/coherence-verification-ab-guard-20260809 | d4b0b7a07 | dac9110fa | clean |
| wave21/professional-review-20260809 | 675f5fb43 | 9aaf6d872 | clean |
| wave21/poi-readiness-repair-20260809 | 925c22e55 | d4754c233 | ours on 1 supersession residual |
| wave21/m1-lifecycle-20260809 | 12ab16b89 | d10a575fd | clean |
| wave21/quote-resolver-foundation-20260809 | 299d8b15d | 58fe3b648 | ours: branch asserted retired RAW_CAMPAIGN_APPROVED_DAYS naming |
| wave21/jeffreys-development-fitter-20260809 | 2f34f6265 | f4a0ebd9f | clean |
| wave21/quote-cost-compatibility | 4a8174249 | 27f60ae3f | ours: HEAD carries identical binding logic + later VerifiedQuoteGeometryReceipt |
| codex/wave21-probability-truth-path-20260809 | 0a2a98b89 | 11df425c1 | the one genuinely new patch; conflicted files carried its EARLIER skip-and-record handling — HEAD's later fail-closed causal-graph semantics kept (token-level audit) |
| codex/wave21-probability-ev-truth-20260809 | 23da4d31e | cc9109216 | ours on 2 richer-in-HEAD artifacts |
| codex/wave21-outcome-authority-prereg-v1 | 8fe6fbf78 | c098da044 | clean |
| codex/wave21-scheduler-pristine-projection-20260809 | 68585782b | 1d9bc3a3a | allocator verified byte-identical pre-merge |

Phase C/D:

| item | commit |
|---|---|
| phase19/march-confirm lean landing (squash) | 04f314295 |
| independent verifier occurrence-DAG repair | f791a7c28 |

Every branch tip in the merge set is an ancestor of the integrated tip EXCEPT
`wave21/candidate-semantics` (by design: it lands via its staging branch per the
integration order; content verified superseded).

## 2. Dedupe verification

The three known duplicate pairs are patch-id-identical (`git patch-id --stable`):
`afe3f6908 ≡ 8c7755052` (exact-once spread), `3b82310ac ≡ 7ffc7cbe9` (sent-unfilled
exit link), `fe5ab2b15 ≡ fa3c4b448` (docs tighten). Three-way merges therefore saw
identical changes on both sides. Post-merge single-application greps:

- `spread_already_in_gross_must_not_be_deducted` — exactly 1 occurrence in
  `src/costs/lifecycle.py`; `spread_accounting_not_exactly_once` — exactly 1.
- `"terminal_outcome": oracle.get("terminal_outcome")` — 2 occurrences, verified to be
  two DIFFERENT dicts (the patched simulate_order terminal dict and a separate
  mfe/mae emission), not a double application.
- The docs-tighten pair landed once via the admission-route lineage; the timewarp-order
  copy merged clean with no text divergence.

Beyond the known pairs, `git cherry` patch-equivalence screening showed 13 of the 15
late coherence/codex branches carried ZERO unrepresented patches (their unique commits
were re-authored duplicates of already-merged content); each was merged as a lineage
join with conflicted paths resolved to HEAD only after per-file residual audits showed
supersession pre-images (counts recorded in each merge commit message).

## 3. Special case: harness recovery

`src/research_infra/wave21_full_flow_harness.py`, `wave21_full_flow_verifier.py`,
`tests/research_infra/test_wave21_full_flow_harness.py` and the two harness receipts
were untracked in the `wave21-full-flow-harness` worktree. Committed there as
`ea3a2f4d9` (recovery noted in the message), then merged.

## 4. The one composed source conflict

`src/components/broader_origin_generators.py` (fsc merge): the candidate-semantics
identity system (HEAD) and the coherence occurrence system (branch) both wire into the
same generation pipeline. Composed, not chosen: identity materialization + truth-mode
lineage gate first, then occurrence materialization + source association; both helper
blocks kept; audit comment took the later wording. Two test alignments toward the
STRICTER merged contract (witnessed four-timeframe fixtures; the pre-close boundary
case now asserts the fail-closed NOT_EVALUABLE_SOURCE_CHRONOLOGY terminal the
coherence plan defines instead of the pre-coherence silent walk-back). 133 focused
tests pass across both sides' suites.

## 5. march-confirm lean landing (giants excluded)

`phase19/march-confirm` (18 commits, tip `870d4cb53`, local-only) landed as squash
commit `04f314295` so the six giant arm-receipt blobs can never become reachable from
main (a true merge would carry them via parent trees; GitHub rejects >100MB). First,
the four modified tracked files recording that lane p2 SPENT the three held-out 2025
windows on 2026-08-06 were committed on the branch (`870d4cb53`).

Excluded giants (bytes sha256; git blob oid in branch history):

| file | size | sha256 |
|---|---|---|
| FA2_M_ARM_I_RECEIPT_ECONOMICS.json | 258.6MiB | bd5f48c8b70595265af3b523771eef6ece81d8c4f955d8a0ecbc18c588580c2e |
| FA2_M_ARM_II_RECEIPT_ECONOMICS.json | 158.8MiB | 08aeecb46c9160cd23cc8f862abee9e66a48190a49f3bedaa0743615368b60c6 |
| FA2_M_ARM_III_RECEIPT_ECONOMICS.json | 142.3MiB | 980ebd17cd07fddb5d53a9c39589444800e79a0ff6889352edb5eefb1ec16d2d |
| FA2_M_ARM_IV_RECEIPT_ECONOMICS.json | 208.5MiB | 2b4dd8d6dafcbb5d800631ac8574a7ee7efee74a809e72f501f4820a383211ea |
| FA2_M_ARM_V_RECEIPT_ECONOMICS.json | 141.0MiB | 79bf757230d0553509409eced2f4a5f623716f23abcfe38ffc35ee6b030492ff |
| FA2_M_R0_RECEIPT_ECONOMICS.json | 208.5MiB | 9717e315a31e393604b3000cd9dbb806f717eed6ad41df785c87110af904e3fc |

Durable holders: local branch `phase19/march-confirm` (worktree
`fa2-integration-20260803`) and TWO verified bundles at
`/Users/borr/GTOSActive/hermes-evidence-hold-20260727/branch-bundles-20260810/`:
`phase19-march-confirm.bundle` (covers `c3152876e`) and
`phase19-march-confirm-with-spent-markers.bundle` (covers `870d4cb53`; prerequisite
`2ecea327b`, present locally). `git bundle verify` passes on both. No READ_RESTRICTED
pool file was opened at any point.

The `lane_rematerialization.py` conflict was resolved by COMPOSING the two March
fuses: the branch's one-shot authorization fuse now honors HEAD's wave-21
`allow_registered_march_metadata` read-only allowance; 42 lane tests pass including
the fuse tests, and the new `test_march_one_shot.py` (20 tests) passes.

## 6. Verifier occurrence-DAG repair (stop-line #1)

Commit `f791a7c28`; evidence
`phase21/full_flow_truth/verifier_dag_repair/DAG_REPAIR_RECEIPT_V1.json`.

The independent verifier (and the producer audit it mirrors) demanded a truth-chain
occurrence ordinal on every candidate row and chain rows for every occurrence; the
real comparator graph emits neither. Every retained fingerprint stored a FAIL-shaped
audit (`candidate_occurrence_ordinal_missing_or_invalid` on all rows,
`truth_stage_row_count 0`) and independent verification stopped at
`independent_occurrence_stage_dag_mismatch`.

`dag_model`: `pass_indexed_window_fixed_point_v1` ->
`candidate_occurrence_disjoint_terminal_v1`: candidate occurrence -> exactly one
disjoint terminal disposition — **missed | trade | terminal_unfilled** — joined on
`canonical_replay_candidate_instance_key`, with orders ⊆ candidates, trades ⊆ orders,
filled-order-must-trade, and exact conservation. Truth-chain walking is retained and
still enforced whenever truth-stage rows exist (ordinal requirement under chains
pinned by a new test). No assertion weakened; the code-manifest identity refusal on
retained artifacts is untouched (full `verify()` against them correctly refuses with
`code_manifest_file_hash_mismatch` because integrated code differs from producing
code — that is the "not runnable" arm of the instruction).

Repaired-audit recomputation over ALL 11 retained comparator ledgers (one-day
2025-10-27 x2 and multiday 2025-10-28 x3 / 2025-11-03 x5 / 2025-11-07 x2 across six
engine revisions): status PASS, exact conservation, and producer/verifier
mirror-hash-equality on every one — including runs with nonzero `terminal_unfilled`
(e.g. 2025-10-28: 8,670 = 8,662 missed + 6 trade + 2 terminal_unfilled). 24 harness
tests pass (16 pre-existing unchanged + 8 new behavioral).

## 7. R2 bound-files-changed register (no reseal attempted)

Five of R2's bound paths changed between `origin/main` and the integrated tip:

1. `src/components/broker_net_cost_engine.py` — extends the CN-precedent authorized
   forward seal break (broker-wall rollover swap; owner sign-off on record)
2. `src/research/moonshot_scheduler_v4_best_trade_allocator.py`
3. `src/research_infra/replay_acceleration_attempt5_typed_sparse_runner.py`
4. `src/research_infra/replay_compact_event_sink.py`
5. `src/research_infra/v4_timewarp_simulated_live_research_loop.py`

Standing owner rule (CN precedent, plan-position 2026-08-01): any future sealed
replay regenerates its decision contract first. The multiday result already recorded
the scheduler seal break as `FORWARD_SEAL_BREAK_REQUIRES_RESEAL_FOR_AFFECTED_SEALED_CAMPAIGNS`.
No reseal was attempted here.

## 8. Fences

- **Live-path byte identity**: `git diff origin/main..HEAD -- book_owner.py
  run_book.py src/execution.py selector_v4.py mt5_real.py config/` is EMPTY
  (config included). The single live-relevant change in the whole range is the
  approved `src/components/broker_net_cost_engine.py` (+72/−5, broker-wall rollover
  swap, fail-closed on unknown broker clocks). `scripts/run_book_supervisor.ps1` has
  NO diff vs origin/main.
- **Blob gate**: 450 new blobs in `origin/main..HEAD`; largest 10.6MB
  (`LP_october_2025_S0R0_POOL_V1.jsonl.gz`); zero ≥90MB.
- **Full-suite failure-set A/B**: see §9.

## 9. Full-suite failure-set A/B

Context: this worktree (sparse cone of eleven patterns — the protocol's ten plus
`research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20`,
added so `test_lane_rematerialization` collects), LFS smudge --skip, one stable copy of
`pytest_failset.py` + `wave21_verification.py` (held at `.wave21_ab_tools/`, untracked,
identical for all captures). Captures per the protocol env
(`env -u FORCE_COLOR NO_COLOR=1 PY_COLORS=0 PYTHONDONTWRITEBYTECODE=1`, `--continue-on-collection-errors`,
failure identity = normalized node ID).

| capture | commit | failed | error | bad (set) | passed | wall s | max RSS |
|---|---|---:|---:|---:|---:|---:|---:|
| A (baseline) | 9392e9bbd origin/main | 207 | 46 | 253 | 12,976 | 1,111.7 | 1.082 GB |
| B (integrated, pre-repair) | f791a7c28 | 241 | 47 | 288 | 13,264 | 1,196.3 | 1.131 GB |
| C (integrated + repairs) | 8c51893ae | 208 | 46 | 254 | 13,301 | 1,137.5 | 1.257 GB |
| D (…+ harness-loader fix) | 972dd502c | 208 | 46 | 254 | 13,302 | 1,071.5 | 2.034 GB |
| **E (final, verdict of record)** | **972dd502c** | **207** | **46** | **253** | **13,303** | 1,078.7 | 1.862 GB |

`ab-guard` A-vs-B: `same_scope=true`, zero context mismatches, verdict REGRESSION with
**35 regressed identities, 0 fixed** — the integration surfaced real breakage: the wave-21
lanes changed `src/costs`/clock/timewarp semantics and never ran the pre-existing consumer
tests (their sparse worktrees did not collect them). Every one of the 34 identities in
files existing at baseline was repaired (§9.1); the 35th was a new-at-B harness node that
passes in isolation and in its module (suite-order interaction, settled by capture C).

A-vs-C: one regressed identity (the harness two-day loader — a DETERMINISTIC suite-order
failure: a cached integration-bound typed-sparse runner poisoned the harness config
loader's contamination guard). Root-caused and repaired in `972dd502c` (the loader now
neutralizes the cached module — fresh target-bound import under the patched resolver,
cached identity restored — with a new behavioral pin test).

A-vs-D: one regressed identity, a DIFFERENT node
(`test_replay_columnar_source.py::test_verification_retains_no_rows`) — failed only in
that run (max RSS 2.03GB) of five monolithic captures, passed 4/4 focused reruns, file and
source byte-identical to origin/main, and the assertion is a memory-delta bound —
adjudicated pre-existing load-sensitive nondeterminism (recorded in `AB_SUMMARY.json`).

**A-vs-E (verdict of record): `NO_REGRESSION`, `same_scope=true`, zero context
mismatches, 253 bad -> 253 bad with IDENTICAL failure-identity sets — `regressed=[]`,
`fixed=[]` — and +327 net new passing tests.** Guards and captures:
`phase21/receipts/wave21_integration_ab/` (A and E captures committed in full; B/C/D
totals + sha256s in `AB_SUMMARY.json`).

### 9.1 The regression repairs (7 commits, `80e132747..8c51893ae`)

All repairs move TOWARD the wave-21 contracts; none weakens an assertion:

1. **Cost-layer consumer fixtures** (`test_costs_peer_transfer`,
   `test_cost_artifact_absence_message`, `test_gate_partial_universe_stamp`): synthetic
   symbols (FAKE.cash, GOOD/BAD/ABSENT) are refused by the new symbol authority before the
   behavior under test is reached — replaced with real declared identities
   (UKOIL.cash / EURUSD / GBPUSD / XAUUSD); the BD absence message moved intact into
   `load_broker_true_costs` and the test repointed; the slippage-slot peer-transfer refusal
   is superseded by structural inertness and asserted as poisoned==clean identity.
2. **Train-engine spread/ruler tests**: rewritten to the native model-first fail-closed
   engine (spec constants and floor tables cannot price at all; incomplete packets refuse
   with nonnumeric totals; retrofit patches are inert and census "kept"; the composed
   stack's component-sum identity holds with broker-wall rollover swap).
3. **`scripts/canary_watch.py` — a REAL live-tool repair**: the wave-21 layer requires
   `entry_utc` (JPY commission FX at entry; broker-wall swap); the canary never passed it,
   so 6 of 8 live-corpus fills refused and C1 went silent — the exact
   alert-indistinguishable-from-all-clear failure the tool exists to prevent. entry_utc
   threaded; zero-priced-fills is now a HIGH C1 alert with the refusal census.
4. **VPS carry sync**: both carry packages' `broker_clock.py` re-synced to mainline's
   deliberate pre-2007 DST calendar repair — phase5 rebuilt mechanically via its own
   `build_carry.py` (pinned shared hash bumped, documented); phase4 file+manifest+diff
   updated. Historical receipts quoting the old hash deliberately untouched.
5. **Regime-spine port parity**: accepts exactly the known pre-2007 old-clock +1h relabel
   (one bar: XAUUSD 2005-03-23) with matching geometry; anything else still fails.
6. **CS breaker-fold reproductions — a decision-bearing finding** (see §11): pinned to the
   measured restricted-universe values with the cause named inline.
7. **R8 characterization**: re-pinned to the repaired finaliser-order materialisation and
   trips if the lexical loop reappears.

## 10. Decision-bearing finding: the CS/CQ breaker candidate does not survive the wave-21 cost authority

The wave-21 artifact-bound slippage model prices only its reconciled FTMO sample set
(16 symbols). Six of the CQ inverted-breaker sleeve's sixteen symbols — AUDJPY, CHFJPY,
EURJPY, UKOIL.cash, USOIL.cash, XAGUSD — have no reconciled price-domain slippage sample
and now refuse (fail-closed, NOT_EVALUABLE). Measured consequences on the ratified gate
re-run at HEAD:

- evaluable universe: 10 of 16 symbols, 63.556% of trades (coverage_frac 0.6355569…);
- repaired verdict: ADMIT (q 0.0576) → **REJECT** (q 0.3169 at the 59-member bill;
  the only failing gate is `significance`);
- exact-null tail 2 → 11 of 2048; MC tail 25 → 80 of 10,000; fold means
  [12.2497, 7.6666, 1.7106], pooled 7.20899 (still large; the multiplicity bill is what
  fails at the sealed α);
- the gate's own stamp says it precisely: the restriction "does not bias the estimate —
  but it does narrow the claim."

The published CS numbers remain correct under their own sealed inputs. They are NOT
reproducible at current cost authority. The restoration path is a **slippage capture for
the six symbols** (broker-history-reconciled entry fills), not a threshold change. This
affects the wave-19 CQ gate-completing captures' standing and belongs in front of the
owner with the next candidate-status review.

## 11. Open items (ROUTE_STATUS)

- `full_flow_comparison` — PENDING: the comparator matrix (published base /
  foundational / forward / integrated candidate) has not been run under the
  integrated code; the retained runs bind pre-integration code hashes.
- `same_class_closure` — IN_PROGRESS: the wave-21 defect surfaces are partially
  closed by the merged lanes; the remaining named surfaces need the integrated
  comparator run.
- `w7_separate_measurement` — PENDING: `w7_current_recost.py` is integrated and
  fail-closed on source gaps; the exact-current W7 recost on its own stack has not
  been re-executed post-integration.
- A fresh producer run under the integrated code is required before any
  result-bearing economics claim (the verifier now has a real graph model to hold
  it to).
- The CS/CQ slippage capture (§10) — six symbols need broker-history-reconciled
  price-domain samples before the breaker candidate can be re-gated on its full universe.
- The wave21-verification import-closure diagnostic reports `run_book.py` unresolvable in
  THIS sparse worktree (tracked at HEAD, outside the cone on disk); the seven new >5MiB
  plain blobs since base are exactly the six LP pools + the phase14 training-ledger append
  (all deliberate march-confirm evidence, largest 10.6MB, push gate is 90MB).
- Uncommitted producer-side work remains in the `wave21-timewarp-flow-truth-20260808`
  worktree (`wave21_truth_stage_chain.py`, `wave21_truth_window_flow.py`, +642 lines
  in the timewarp loop, +82 in the compact event sink, +101 test lines) — the
  truth-chain window-flow machinery. It was NOT in the commissioned merge set; left
  untouched for its owning lane. If it is wanted, it needs its own session and A/B.
