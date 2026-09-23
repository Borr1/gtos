# GTOS Full-Vision Plan — from today's repository to repeatable payouts

**Written by the Fable-5 second audit, 2026-07-25, for execution by the Opus implementation sessions.**
Companion to `SECOND_AUDIT.md` (findings and evidence). This document is the path: phases, gates,
falsification criteria, and the two decisions only Borhen can make. It covers the charter's whole
destination — replay at scale → feature/label stores → trained models → default-off runtime
intelligence → daily loop → command center → controlled activation → first payout → repeatable
payouts — not just the replay engine.

> **SUPERSEDED IN PART, 2026-07-27 — read this before executing anything below.**
> **This document's Phase 2–3 sequencing is superseded by `THIRD_REVIEW.md` §4** — the third
> independent review's constrained plan, **approved in full by Borhen on 2026-07-27.** The plan's own
> author (Fable 5) reviewed it against the evidence eight implementation sessions produced and found
> that its middle phases inverted the charter: they schedule a monolith-scale rebuild *before* any
> activation-bearing decision, for a policy family whose measured economics are negative in every
> campaign-grade window ever run (`THIRD_REVIEW.md` §1.1, §1.2).
>
> **What changed, specifically:**
>
> - **The unit of work is Stage 0 → Stage 1 → OD-3, not Gate G2.** OD-1 below is **reopened as OD-3**:
>   which surface GTOS activates. It is reached by two cheap measurements — re-cost the W7 book's
>   1,679-day validation at broker-true costs (F38: the cost model charges **zero commission**; F39:
>   tick erosion credited with the wrong sign), and port candidate **generation** to answer G4 — not by
>   an engine rebuild. Stage 1.2/1.3, ~0 replay machine-hours.
> - **`BroadV4Policy` is demoted** from Phase 2's primary build to Stage 5, "*if and when* a repaired
>   broad family seeks a slot through the walk-forward gate" (`THIRD_REVIEW.md` §4).
> - **The ≤3 GB/arm memory gate is withdrawn** (§7.2) — see the amendments at Phase 2 and Phase 3.
> - **The B7.5 campaign is parked with a price**, banked first (§6.2, §4 Stage 5).
> - **Gate G2 is re-scoped** from row-exact reproduction to decision-level parity, with byte parity
>   deferred to the projection gate (§7.9).
>
> **What survives unchanged** (§7.10): the policy-plural core; the harness-first ordering; the
> shadow-reducer-first truth sequencing; OD-2's forward-only re-seal split; refusing the 507-red suite
> as a blocker; and the walk-forward gate as the only door into a live book.
>
> **Status of the phases below:** Phase 0 and Phase 1 are **complete** (5 of 5). Phase 2 delivered
> three of six items, **two of which returned negative or scope-limited results that changed the
> plan** — the columnar layer works and moves nothing (B84/B85), and `SleeveBookPolicy` ports the
> decision half only, leaving candidate *generation* as the missing keystone. Phases 3–8 stand as
> design input, not as the sequence. **Read `THIRD_REVIEW.md` §1.2 and §4 before proposing any work
> against this plan.**

Design rules this plan obeys:

1. **Owner sequencing:** architecture → scale → replays → live. The remaining B7.5 windows run on the
   new engine, not before it.
2. **Build, don't patch** (`OWNER_SESSION_CONTEXT.md` §4). No new wrappers around known-broken
   authority; mechanisms get replaced, not gated.
3. **Evidence classes preserved.** Every gate below names what is measured and what would falsify it.
4. **Executable by a fresh agent.** Each phase states its inputs, outputs, and where the evidence
   lives. Compute is not a constraint (owner's word); wall-clock and RAM on this machine are, and are
   stated.
5. **The risk dial and allocation profile are Borhen's.** The plan reaches
   `CONTROLLED_CANARY_READY_PENDING_HUMAN` and stops there, per the charter.
6. **Time semantics — read before pacing yourself.** This plan is executed by agents, so phases are
   sized in **agent sessions** and ordered by dependency, not scheduled in human days; a phase
   labeled "one session" may be an hour of work, and nothing here licenses slow-burning. The only
   real durations in this plan are of three kinds, and each is labeled where it appears:
   **machine wall-clock** (replay arms, data transfer — e.g. ~16.5 h per serial month-window today),
   **calendar physics** (forward-shadow observation windows: real market time that no amount of
   intelligence compresses), and **owner decision points**. Everything else finishes as fast as the
   gates pass honestly — and no faster.
7. **This plan is judgment-input, not law** (the owner's standing directive applies to the plan
   itself). Gates are **evidence definitions, never waiting periods**: where a gate names a
   quantity, sufficiency is the implementing session's judgment, stated with its rationale in the
   gate receipt. The session may resequence, merge, or restructure phases with documented reasoning.
   What is *not* negotiable is the honesty layer — evidence tags, declared gaps, falsification
   criteria, fail-closed engineering, A/B verification — because that layer is what makes moving
   fast safe. Conservatism means unearned smallness and waiting; it does not mean truth-telling.

---

## 0. The two decisions that shape everything (owner, ~minutes each)

### OD-1 — Which policy surface is the activation candidate? **DECIDED BY OWNER (2026-07-25)**

`SECOND_AUDIT.md` F1 + Owner Decision Update: the W7 book went live 2026-06-18 → 2026-07-02 at the
2.0 % ceiling dial with the same-day-approved expanded composition, drew down (FTMO ≈ −5.3 %,
FN ≈ −3.0/−3.9 %), and Borhen deactivated it and chose the **current broad system as the activation
candidate** — build it to quality, then activate it.

The plan proceeds on that decision. Consequences applied below: Phase 2 builds `BroadV4Policy` as
the primary policy module (the replay already measures it — E1's divergence now closes by making the
*live* path run the same core, not by modeling the book); the former "Stack-B evidence audit" in
Phase 1 is re-scoped to **W7 live-vs-validation divergence forensics** — mine the only live-execution
evidence the modern stack has (the W7 fortnight: fills, slippage, spread blocks, reconciliation,
per-account asymmetry, dial/composition attribution) into the divergence matrix and the Phase-6 cost
calibration. W7 itself is retained cheaply as a benchmark/challenger policy inside the policy-plural
core, with the facts stated plainly: its sleeves are **not** contained in the current system (zero
signal-level overlap, verified against the hydrated registry), so retiring it is a real removal, not
a deduplication — and the walk-forward gate needs a non-trivial baseline anyway. The standing
implication of the owner's choice: the current system's own evidence is not yet positive either
(January cells, KIAP holdout), so activation is earned through the gates below, exactly as the owner
framed it ("make it good and go live when we finish all its work").

**OD-1 addendum — the combined book (owner follow-up, 2026-07-25).** Asked whether the two families
can share one sleeve inventory, the answer adopted here: **merge at the portfolio level, not the
signal level.** The families are structurally different (daily statistical sleeves vs intraday M15
geometry candidates) and neither format should absorb the other; both instead emit the same
**trade-intent contract** (symbol, side, entry, stop, size, provenance), and one portfolio layer —
one gross-risk budget, one governor, one exposure/correlation view — admits and sizes across the
combined pool. Rules that make the bigger pool an asset instead of diversified losing: (1) each
family **earns its slot individually** through the Phase-4 walk-forward gate (beats baseline,
positive after measured costs, survives stress) — merging combines edge, it does not create it;
(2) combination weights belong to the portfolio layer and the learned rerating path, never to
hand-argument; (3) "broad-only", "W7-only", and "combined-at-weights" are **configurations of the
policy-plural core** — replayed, MC'd, and compared before any activation-candidate freeze
(Phase 5/7). The activation candidate is whatever composition clears the gates; the broad system is
the primary build focus; the W7 sleeves remain in the pool as gateable components.

**Standing owner directive (2026-07-25, recorded for the implementing sessions).** Precedent is not
authority: *"what's done before doesn't automatically mean it's the bible… if it's wrong or doesn't
go with your judgment and Opus's judgment then obviously I give explicit approval for whatever is the
alternative and goes better for our goals and visions."* Operating translation: any prior policy,
contract, gate, verifier, or structure that this plan's executors judge wrong or valueless may be
replaced with the better alternative without further per-item permission — with the change and its
rationale documented so the evidence chain stays honest (that documentation discipline is what keeps
the seals and gates meaningful, and it is the same standard OD-2 applies to the decision contract).
The boundaries that remain the owner's: risk dial, allocation profile, and broker-real activation.

### OD-2 — Contract re-seal policy

Adopt the first audit's split: `input_bindings` → `executing_closure` (SHA-bound) +
`verification_tooling` (versioned, not bound). Re-seal **forward-only**: January stays accepted as-is;
April/May/March and every learned-arm campaign run under the new contract. This unblocks the queued
P1/P2 fixes and every future proof repair at zero re-run cost. (Owner decision D1 from the first
audit, answered.)

---

## Phase 0 — Reconcile the fork and unblock (one to two agent sessions; no replay cost)

The live lineage — entrypoint, protective companion, live-hardened book, and the book's entire
evidence route (661 files) — lives on the deploy-live/VPS branch family, not on mainline
(`SECOND_AUDIT.md` F4, F6). Nothing else in this plan is trustworthy until mainline holds one
reconciled truth.

Work items:

1. **Two-way merge of the live package.** Bring to HEAD: `run_book.py` (+ `bridge.config_bool_value`),
   the VPS `book_owner.py` live-hardening (~2,561 lines: broker deal/exit reconciliation, position
   protection, realized-P&L joins), the fourth gate `ultimate_book_live_broker_authority` (as code +
   config key, default `false`), `src/components/ai_companion/` + supervisor scripts + tests, and
   `.tools/monitor_books.py`. Carry the other direction: P4 (`create_mt5` mode validation) and the
   three `convergence_*` modules onto the VPS lineage record. Resolve the composition drift
   (`include_clean3: false` at HEAD vs the system-of-record's 11-sleeve description) with an explicit
   owner-visible note in `live_system_of_record.md`.
2. **Vendor the book's evidence route** (`final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/`,
   from `origin/deploy-live`) into mainline, read-only, so the declared live system's evidence is
   auditable from the audited branch for the first time.
3. **Fix F13** — the ten genuinely-red selector tests: decide whether the fill-probability lookup
   chain (`selector_v4.py:4004-4016`) should consult `entry_quality_fill_probability`, fix the code
   or the fixtures to the decided contract, and record the decision. The suite goes green for a true
   reason, not an LFS excuse (hydration is already done and fixed the eleventh).
4. **Invert the halt mechanism** (F2): introduce a per-account **activation token** — a signed file
   whose *presence* (bound to account contract + config digest + expiry) is required for any
   broker-mutating path; absence fails closed. Keep the legacy flags as an additional brake during
   transition. This converts the fail-open-on-missing-flag class (R6/F2) into fail-closed by
   construction and makes fresh clones safe by default.
5. **Re-seal per OD-2** and land the queued P1/P2 (parity NaN hole, authority-hash determinism) plus
   halt checks in the follower and `fn_smoke_trade` (or delete the latter; it bypasses every guard).
6. **Record the history graft (F28).** A short pointer doc in `.context/00_core/` naming the legacy
   repo (`…legacy-v238-20260712T192309Z`), the cutover record, and the dirty patch — so blame/bisect
   work on the engine's formative history is possible and no future auditor rediscovers this from
   scratch. Decide (owner-visible, cheap) whether to graft the legacy history into this repo via
   `git replace`/bundle or leave it referenced.

**Gate G0:** `run_book.py` imports and its tests pass at HEAD; book + companion test suites green;
A/B against parent commit shows only intended deltas; the H1 contract check passes under the new
split; an activation-token dry-run shows every mutating entrypoint fail closed without a token.
**Falsified if:** the two-way merge produces behavioral conflicts that can't be resolved from
evidence — then stop and surface the conflict set to Borhen rather than guessing.

---

## Phase 1 — Truth before speed (five workstreams, roughly one agent session each, runnable in parallel; no replay cost)

Independent workstreams; run concurrently in separate sessions if desired.

1. **Shadow reducer v2 — recompute R from prices.** The first audit's shadow reducer, upgraded by
   this audit's finding that the analyzer already re-aggregates ledger numbers but *nothing
   recomputes any trade's R from prices* (§3.5). Build ~400–600 lines, zero engine imports, that
   takes entry/exit/stop prices + costs from the trade/order/oracle ledgers and independently
   recomputes per-trade R and the five headline aggregates. Run it over all four sealed January arms
   + the April partial. **Gate G1a:** agreement with the analyzer within float tolerance, or a filed
   economic defect — either outcome is a win and is the first genuine economics check in GTOS
   history.
2. **W7 live-vs-validation divergence forensics** (re-scoped per OD-1's owner decision). The W7
   fortnight is the modern stack's only live-execution evidence; mine it before it goes stale:
   per-trade join of the VPS ledgers (runtime-learning packets, placement ledgers, trade records —
   on the VPS filesystem; the branch carries snapshots and digests) → realized R per sleeve family;
   attribute the −5.3 %/−3.9 % window across (a) validated core-8 vs same-day-approved candidate/
   market-expansion sleeves, (b) the 2.0 %-ceiling dial vs the dossier's 1.25 % recommendation,
   (c) execution friction (slippage/spread-blocks/swap vs the validation's cost model), (d) the
   FTMO-vs-FN asymmetry on identical signals. Deliverables: a live-divergence row set for the
   divergence matrix, measured cost inputs for Phase 6, and a one-page verdict on whether the
   validated core-8's live sample contradicts its 2014–2026 validation (at ~10 days it likely cannot
   — say so with the arithmetic). **Gate G1b:** every W7 live trade attributed to sleeve + dial +
   cost with no unexplained residual, or the gaps named.
3. **Close the live-path test gaps:** SHORT-side `_compute_r` coverage (F12); profile-overlay
   multiplier and currency-conversion sizing tests (the two unprotected sizing surfaces); a
   live-config-truth test asserting which gates are actually live (so E1c-class facts are pinned by
   CI rather than archaeology).
4. **Divergence matrix v2** as a first-class artifact beside every arm receipt: execution-model
   divergence (the E1 table) *plus* strategy-family divergence (F1) *plus* the clock divergence (F7),
   auto-generated, and required by the arm acceptance path under the new contract.
5. **Clock-truth repair (F7).** ✅ **DONE 2026-07-26** (Phase 1 Session B, branch `phase1/clock-truth`).
   Make true-UTC the only time base: the export path gains broker-offset
   correction with per-file offset provenance (the live path's `_broker_epoch_to_utc` logic, already
   written); existing research data gets either a re-export or a declared-offset view layer (offset
   is deterministic: ~~EET/EEST calendar~~ **the US DST calendar — this item named the wrong one; see
   the amendment below**); replay session tables then gate the same real-world hours as
   live. Deliverables: a one-page impact note on sealed evidence (arm-vs-arm contrasts unaffected;
   session-level attributions carry a caveat), and a regression test that fails if any ingest path
   ever emits a Friday bar after 22:05Z again. **Do this before any learning-lane training run** —
   session features trained on a mislabeled clock transfer wrong.

   > **Amendment.** The offset *is* deterministic, but from the **US** DST calendar, not EET/EEST:
   > broker wall clock = `America/New_York` + 7 h. The calendars disagree ~3 weeks each spring and
   > ~1 week each autumn, so a repair built on the EU rule would be an hour wrong in exactly those
   > windows — including **2026-03-09..28, inside the sealed March challenge**. The real seam in that
   > window is 2026-03-08, not 2026-03-29, which also corrects the note under Phase 5 item 2.
   > A **view layer** was chosen over re-export (offset exact and deterministic; re-export blocked on
   > iCloud re-materialisation; the sealed campaign must keep reading its sealed bytes either way).
   > Delivered: `src/utils/broker_clock.py`, `src/utils/research_timebase.py`,
   > `scripts/measure_broker_clock_offset.py`, `scripts/declare_research_timebase.py`,
   > `tests/test_broker_clock_truth.py`, `CLOCK_TRUTH_IMPACT_NOTE.md`, and three corrected exporters.
   > No SHA-contract-bound file was touched, so no re-seal and no replay re-run.

---

## Phase 2 — One decision core, policy-plural (the plan's largest build: a sequence of agent sessions, one per work item below; replay cost only at its verification gates)

The first audit's `gtos.core` design (three ports: Clock, Broker, Sink; attach at the existing
injection seam `run_campaign:90494-90499`) is upheld — with one structural amendment forced by F1:
**the core hosts N policy modules behind one `Policy` interface**, so "replay measures the thing that
trades" becomes true by construction for any OD-1 outcome, and E1 can never reopen.

- `SleeveBookPolicy` — ports `admission.admit_and_size` + governor semantics (the live formula chain
  verified in `AUDIT_STATE.md`): static sleeve registry, Kelly-lite bins, cluster collapse, smooth
  derisk, gross-cap shedding.
- `BroadV4Policy` — extracted from the monolith's evaluator/allocator/finalizer (the ~8 % that
  decides), leaving the 72 % evidence machinery behind (Phase 3 makes evidence a projection).
- (Phase 4 adds `LearnedEdgePolicy` variants.)

**Differential harness first, core second.** Revive, in order (test-quality agent's ranking):
`replay_acceleration_task2_semantic_acceptance` (row-level, fails closed on unknown differences),
`partial_golden_verifier` (successor-acceptance framing), `streaming_archive_verifier` (day-shard
granularity). These three are ~80 % of the harness a rebuild needs and are already written, tested,
and — per E7's irony — SHA-bound as if they mattered while never executing.

Work items: harness revival → `BroadV4Policy` vertical slice (one symbol, one day, against the sealed
January pack) → widen to the month → `SleeveBookPolicy` implemented against the reconciled Phase-0
book with its replay validated against the VPS placement ledgers / shadow `would_units` packets →
sub-window replay and portable seals in the new core (window is an input; seals bind content digests
+ repo-relative paths; the old engine stays sealed for comparability) → single-materialization
columnar source layer (kills the 5×-bar/4×-tick copies; ~~target < 4 GB/arm so four arms fit in
16 GB~~ **— this item was built, and its memory target does not survive its own measurement; see the
amendment below**).

> **Amendment — the columnar item is DONE and its result is NEGATIVE (2026-07-27, Session G, B84/B85;
> attribution in `THIRD_REVIEW.md` §A1).** The layer exists
> (`src/research_infra/replay_columnar_source.py` + `replay_columnar_bridge.py`, both unbound, no
> re-seal owed), it kills the copies **8.4× at the partition boundary**, and its arm output is proven
> identical over **1.78 M rows**. **Arm peak RSS did not fall**: 7.716 GB sealed → 7.986 GB columnar,
> **+3.5 %** on the same fixture, back-to-back on a quiet machine. What it did buy is **−9.0 % wall
> and −3.0 % instructions, free** (~1.5 h on a 16.5 h four-arm window) — banked, and that is the whole
> return. R20's five-bar/four-tick finding is correct as a *description* of the source layer and wrong
> as an *explanation* of the arm peak. The memory target is therefore **withdrawn, not re-derived**
> (`THIRD_REVIEW.md` §7.2): §A1's `tracemalloc` attribution at the Python-heap high-water mark puts
> the **source layer at 99 MB — 1.6 %** of the heap, against **3,866 MB — 60.6 %** in the monolith's
> per-day row/attribution accumulation. **No source-layer work of any kind can move the arm peak**, and
> four arms fit neither before nor after this work (~8 GB/arm measured × 4 on a 17.18 GB machine).
> Do not schedule further source-layer RSS work.

**Gate G2 (falsification gate, the plan's hardest):** the slice reproduces one sealed symbol-day
*exactly* (row-level, via the revived comparator), then a full January arm; the book policy
reproduces the VPS shadow-packet decisions over a sampled week. **Falsified if** exact reproduction
fails after the known-allowlist differences — then the decomposition is wrong; stop, report, and the
fallback is the first audit's "optimize in place" lane (Stage 0 wins are already banked:
canonicaliser fast path, query_cache, 4-arm parallelism).

---

## Phase 3 — Evidence as projection + the typed capture layer (several agent sessions, strictly after G2; verification gates carry the machine time)

One schema serves three masters. The chronological loop emits **fixed-width typed events**; ledgers,
scorecards, and authority blobs become offline projections (byte-parity gate against the old engine
via the Phase-2 harness). The same event stream **carries the learned-edge feature whitelist per
candidate** — `candidate_id`, `predecision_features` (computed today at
`broader_origin_generators.py:1929` and discarded), `probability_packet.selected_thesis`, entry
geometry, policy id, open/pending counts — which is exactly what F5 showed the learning lane starves
for. The 494 KB/1,274-key row problem and the ML-input problem are the same problem; this phase
solves both once.

Performance targets (measured baselines: dense day 507.6 s economic; proof-complex 72.4 % of
self-time; startup 63 s/process; ~~arm RSS 8.6 GB~~ **— that figure is a 2-day fixture, not an arm;
see the amendment below**):

> **Amendment — the ≤3 GB/arm target is WITHDRAWN, not re-derived (2026-07-27, `THIRD_REVIEW.md`
> §7.2).** Three corrections to the row below.
>
> **(1) The baseline is mis-scoped.** 8.6 GB is `receipts/bench_baseline_uncontended.json:829` —
> `day: 2026-01-01`, `end_day: 2026-01-02`, `arm: S1R1`, `wall_seconds: 603.678`: a **two-day
> fixture**. **No peak-RSS measurement of a full month arm exists anywhere on disk** (B81).
>
> **(2) The target's causal story is refuted.** ≤3 GB/arm was derived from R20 — the source layer's
> 5×-bar/4×-tick materialisation — as the cause of the peak. Session G killed the copies (8.4× at the
> partition boundary, output identity proven over 1.78 M rows) and the arm **did not shrink**: 7.716 →
> 7.986 GB, **+3.5 %** (B84/B85). A target derived from a refuted cause is not re-pointed at a new
> number; it is retired.
>
> **(3) Where the memory is, measured.** `THIRD_REVIEW.md` §A1 ran the sealed 2-day fixture under
> `tracemalloc` and attributed the Python-heap high-water mark:
> `v4_timewarp_simulated_live_research_loop.py`'s per-day row/attribution accumulation **3,866 MB =
> 60.6 %**; `moonshot_scheduler_v4_best_trade_allocator.py` 614 MB = 9.6 %; retained day-pack JSON
> 401 MB = 6.3 %; **source layer 99 MB = 1.6 %**. Traced heap grows monotonically through each replay
> day (0 → 5.5 GB day 1 → 6.38 GB day 2) and RSS spikes at the instant of the day-end collapse, when
> serialisation forces the accumulation resident. **The evidence machinery is simultaneously the
> memory (60.6 % of heap), the CPU (60.6 % self-time) and the bytes (>99.8 % never value-read) — one
> redesign, three resource problems.** §A1 deliberately declines to mint a successor number: if the
> monolith lane ever returns (`THIRD_REVIEW.md` §4 Stage 5), the target is re-derived from this
> attribution at design time. Two concurrent arms remain measured at ~1.1–1.3× net — still not worth
> running, but for the accumulation, not the source layer.

| Lever | Basis | Expected |
|---|---|---:|
| Evidence out of the hot loop | 72.4 % proof-complex self-time | dense day → ~150–250 s (stretch 80–150 s) |
| ~~Four-arm parallelism (Task-7 machinery + memory fix to **≤3 GB/arm**)~~ *[target withdrawn 2026-07-27 — amendment above]* | measured 59,221 s serial January; contended 2-way measured ~1.2× net (don't) | ~3.7× campaign wall |
| Exact-parity micro-wins (canonicaliser fast path, encoder reuse, query_cache) | measured 2.19×/1.56× on hash stage | ~5–10 % additional |
| Startup amortisation across windows | 63 s × process count | minutes per campaign |

Honest requirement framing (the E10 re-derivation): the charter's destination needs **~10–16×**
window throughput (policy-change 6-month re-replay overnight; 20-variant search in a weekend; 2-year
sweep in 1–2 days) — not the undeviated "~30×," which corresponds only to full-history re-replay
overnight, a workload the charter itself replaces with forward shadow. The two levers above compose
to **12.7–24.6×**: the band is reached without heroics, and the rebuild is justified by F1/F5/F7
(measure-what-trades, capture layer, clock truth) with throughput as a co-benefit.

**Gate G3:** offline projection reproduces today's ledgers byte-for-byte on the January fixture; the
learned-edge dataset builder consumes the new event stream through its adapter and emits a training
frame whose labels match a hand-checked sample; dense-day ≤ 250 s and four concurrent arms without
swap on this machine.

---

## Phase 4 — Learning loop v1 (overlaps Phase 3; the book lane is a single short session, the candidate lane a few, and training runs are machine time)

Ordered by value-per-effort, per F5:

1. **Book lane first (single short session):** a producer that reads ~~the B7.5 per-sleeve split
   evidence~~ **— those do not exist for W7 sleeves; this item named the wrong stack, see the
   amendment below —** into
   `SleeveEvidence` → `learning_actuator.rerate_book` → an owner-armed
   `ultimate_book_learning_rerate` recommendation report. The consumption path (bounded tilts ≤1.25,
   0.0-drop) is already implemented and tested. This is the first closed learning loop in GTOS and it
   points at the activation surface.

   > **Amendment — this item conflated the two stacks, and as written it would point a session at the
   > wrong registry (2026-07-27; `THIRD_REVIEW.md` §7.8).** `SleeveEvidence` /
   > `learning_actuator.rerate_book` re-rate the **W7 `ultimate_book`** sleeves — `metals_core`,
   > `crypto`, `energy_agri`, `fx_jpy`, `idxrev` and the rest of the 29-sleeve live book. **B7.5 has no
   > per-sleeve splits for any of them.** B7.5's sleeve vocabulary is the **broad** stack's `fpsc_*`
   > package families, which are a different policy family with **zero signal-level overlap** with the
   > book.
   >
   > **Verified for this amendment [MEASURED 2026-07-27]:**
   > `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/ULTIMATE_CANDIDATE_PACKAGE_SLEEVE_REGISTRY_LEDGER.jsonl`
   > holds **82 rows, and 82 of 82 `sleeve_id` values begin `fpsc_`** (e.g.
   > `fpsc_promote_default_off_signal_sleeve__origin_liquidity_sweep_reclaim__liquidity_sweep_reclaim__long`);
   > `origin_family` takes 11 values, all broad-origin generator names. Zero live book sleeve names
   > appear — the same measurement Session H recorded as **D12** in
   > `phase2/SLEEVE_BOOK_DEFECT_REGISTER.md` after its own brief named this file as the book's source
   > of truth and cost it a wrong first assumption.
   >
   > **Read-hazard, because it turns a wrong answer into an empty one:** that ledger is **git-LFS
   > tracked** — the committed blob is a **131-byte pointer** (`version https://git-lfs…`), hydrated to
   > 205,754 bytes only in worktrees that have fetched it. On a machine where it is a pointer, a naive
   > read returns **zero rows**, which reads as "no sleeves" rather than "wrong registry". Check the
   > first 40 bytes before trusting any count from it, and `git lfs checkout <path>` if it is a stub.
   >
   > **The book lane's real inputs** are the June deep-history Stack-B chain — which `SECOND_AUDIT.md`
   > itself ordered adversarially audited *before* reliance — plus the live packet evidence. Note also
   > that `recommend()` currently ignores `live_meanR`/`live_n` (~20-line extension), and that this lane
   > is now scheduled in `THIRD_REVIEW.md` §4 **Stage 5**, after Stage 1 supplies cost-true inputs.
2. **Candidate lane:** partition registry authored (Jan/Apr/May development = TRAIN/VALIDATION,
   March = SEALED, explicit ≥48 h embargo); trainer hygiene (per-fold numeric specs, boundary purge,
   populate-or-drop `n_competing_in_group`); train on the development arms; walk-forward gate — whose
   pass is by construction a beats-production claim (§3.5 of the audit).
3. **Learned arm as challenger:** a replay arm with `selector_v4_learned_edge_enabled` +
   (optionally) learned sizing, under a new contract generation — the honest experimental design,
   since the enable keys are contract-bound. Its read-out extends B7.5's factorial with the
   continuous sizing family the binary arms cannot express.
4. **Daily digest = command center v1:** a `gtos status` report-pack CLI over the existing JSONL
   feeds (~70 % of the vision's dashboard list already has a feed — companion agent's inventory). No
   web app, no server, nothing to babysit.

**Gate G4:** the rerate report reproduces from sealed inputs; a trained artifact passes the
walk-forward gate or its failure anatomy is filed; the learned challenger arm runs end-to-end on the
new engine.

---

## Phase 5 — Scale the replays, finish the campaign, widen the data (machine wall-clock, mostly unattended; agent effort is launch-and-verify)

1. **Re-run January on the new engine** (regression anchor — the sealed arms are the baseline the
   rebuild is judged against; they already exist and cost nothing).
2. **Finish B7.5 on the new engine:** April remainder, May development, freeze, sealed March
   challenge — per protocol, under the new contract. Measured cost today: 12 arm-months ≈ 49.3 h
   serial ≈ 2.05 days (matching the owner's estimate); at Phase-2/3 speeds it is 13.4 h → a few
   hours. Note for the March challenge read-out: the EU DST transition 2026-03-29 sits inside the
   window — apply the F7 clock caveat to any session-conditioned interpretation.
3. **Multi-window sweeps** for the learning lane, scoped by measured coverage: bar depth (M1
   2024-01→2026-06 across the surface; M15/H4/D1 to 2014) supports multi-year *bar-level* sweeps
   once the iCloud-evicted exports are re-materialised to local disk (a babysit-the-download task,
   not engineering); **ordered-tick truth covers 4 of 24 symbols × 7 months** — tick-realistic
   sweeps are metals+majors first by necessity. Acquisition workstream (VPS-side, parallel): probe
   FTMO server tick depth (the availability probes are evicted/unrun), re-export with the Phase-1
   clock fix, budget ≈ 290 GB raw for a full 2-year × 24-symbol tick backfill, and restart
   redacted_account-native capture when the shadow phase begins (it ran for exactly 2 days pre-halt).
   Also: move the canonical archive off iCloud eviction (local hot store + explicit cold policy) —
   53/96 files bound by the April bundle are currently dataless placeholders.
4. **Proof-budget rule enforced** (charter's own test): every verifier/receipt/ledger field retained
   in the new engine names the decision it changes, or it is deleted with the LOW tier — **under the
   E9 preconditions this audit added** (§5.4 of `SECOND_AUDIT.md`): materialize each tier as a
   reviewed manifest; exempt the `ultimate_book` + learning families and `emergency_close_*`; vendor
   `run_book.py` before any cascade math; per-file hidden-consumer sweep covering string/subprocess/
   config/receipt/VPS-branch consumers. The un-materialized tier as previously specified would have
   deleted the live book surface and the vision's walk-forward gate.

**Gate G5:** January parity on the new engine; B7.5 read-out delivered per protocol thresholds;
a ≥12-month × 4-arm sweep completes overnight on this machine.

---

## Phase 6 — Forward shadow (charter rung: `FORWARD_SHADOW_ACTIVE`)

**Owner facts (2026-07-25) that pre-start this phase:** the VPS is running and paid, and it has been
in shadow-intelligence mode **continuously since 2026-07-02** — candidate generation,
runtime-learning packets, MT5/account telemetry all still accumulating (52k+ packet rows by June 25
and growing). So weeks of W7-side forward-shadow data already exist before this phase formally
begins; the Phase-1 forensics should copy the full accumulated ledgers off the VPS, not just the
live-window slice. Account inventory for Phase 7 planning: FTMO #1 ≈ **108 k** (recovered by two
owner-manual trades after deactivation; forward capture kept on), redacted_account ≈ **96.1 k**, FTMO #2
**100 k untouched** — ≈ 304.1 k total across the three. Data acquisition on the Mac runs through the
colima/Docker MT5 bridge (`docs/STORAGE_AND_REMOTES.md`).

The chosen policy (per OD-1) runs continuously on genuinely current data through the same core —
same code, `WallClock` + `SimulatedBroker` ports — emitting timestamped canonical decisions and
simulated lifecycle. The calibration loop closes R12 with what actually exists: the 192-fill
`slippage.jsonl` distribution (global + asset-class buckets replaces the flat `0.02 R` constant) and
the 877-row `pending_limit_lifecycle.jsonl` fill/no-fill set calibrate immediately; the
`broker_order_lifecycle_capture_v4` channel — which has **never captured a row** — gets turned on
with the shadow phase so per-symbol × session cells accumulate. (After Phase 1's clock repair the
forward-vs-replay timestamp join is exact; before it, any such join is off by 8–12 M15 bars.) The vendored companion (F6) supervises with its bounded protective controls; the daily
digest runs on the shadow stream.

**Gate G6 (evidence-defined, no fixed duration):** the digital-twin property holds — zero
unexplained divergences between shadow decisions and same-day replay of the same inputs — over an
observation set the implementing session judges sufficient and states explicitly (e.g. decision
windows spanning the session grid and active symbols, enough fills to calibrate the cost model with
stated confidence), with the sufficiency rationale recorded in the gate receipt. Market observation
accrues in calendar time and the VPS has already been accumulating it since 2026-07-02 — count what
exists, don't restart a clock. If the evidence is sufficient in days, the gate passes in days.

---

## Phase 7 — Controlled canary package (charter rung: `CONTROLLED_CANARY_READY_PENDING_HUMAN`)

Assemble the immutable activation package: frozen config + policy fingerprint; per-account activation
tokens (Phase 0's mechanism) with hard account/symbol/exposure/risk bounds; fail-closed behavior
verified by chaos drills (kill the feed, kill MT5, malform a ledger — the book must pause/flatten per
its tested semantics); kill/rollback one-command path; reconciliation (broker truth vs local, the
VPS-hardened joins from Phase 0); operator handoff runbook. Execution host is the Windows VPS with
authenticated portable terminals — this is a deployment reality, not a gap (the Mac is the build
surface; MetaTrader5-python is Windows-only).

Rollout scope and dial are the owner's calls, made with the evidence in front of him — the package
must support single-account and all-three-from-day-one equally; the implementing session recommends
from the measured chain (W7's lesson cuts both ways: it went live at its ceiling dial with a
day-old composition — the failure mode was unearned aggression, and the fix is earned confidence,
not imposed smallness).

**Gate G7 = the charter's culmination standard A**, checked item by item (§ Culmination in
`GTOS_ULTRA_GOAL.md`). The recommendation to authorize is delivered candidly with the evidence; the
authorization itself is Borhen's.

---

## Phase 8 — First payout → repeatable payouts → scaling

- Payout mechanics: challenge-phase targets and daily/max-DD constraints are already encoded in the
  book's governor and MC; the monthly cadence becomes the learning loop's heartbeat (rerate tilts,
  drift checks, sleeve retire/add through the same walk-forward gate — never ad-hoc).
- Scaling levers in order of evidence: dial ladder per the MC (owner's call at each step) →
  additional accounts (the two-books model generalizes; per-account tokens/state already namespaced)
  → sleeve-book breadth via the incubator (learned candidates graduating through the gate) →
  compute scale-out for research (the core is portable after R23's absolute-path seals die in
  Phase 2; cloud replay becomes possible for the first time).
- The drawdown-survival invariants (static wall, daily stops, flatten semantics) are non-negotiable
  constants of every scaling step; scaling proposals that only raise the dial without new evidence
  are rejected by the plan's standing rule.

---

## What Opus should build first (the concrete starting queue)

1. Phase 0 item 1 (fork reconciliation) — nothing else is trustworthy until mainline is one truth.
2. Phase 1 item 1 (shadow reducer v2 over the sealed arms) — highest truth-per-hour in the plan.
3. Phase 1 item 2 (Stack-B evidence audit) — OD-1 is conditional on it.
4. Phase 2 harness revival — it de-risks everything after it.

## Standing risks and their falsification routes

| Risk | Signal | Response |
|---|---|---|
| The decomposition is wrong (G2 fails) | slice cannot reproduce a sealed day row-exactly | stop; fall back to optimize-in-place lane; report |
| Stack-B evidence does not survive audit (G1b fails) | sleeve EVs not reproducible / split leakage found | OD-1 reopens; broad-stack + learned lane becomes primary; activation timeline extends honestly |
| Learned lane underperforms its gate | walk-forward gate fails | file failure anatomy; the heuristic floors remain; retry per doctrine with materially different features |
| Fork reconciliation surfaces behavioral conflicts | G0 conflict set non-empty | owner adjudicates with the conflict evidence; do not guess |
| Data coverage insufficient for multi-year sweeps | coverage table gaps | scope sweeps to covered windows; acquisition workstream on the VPS |

*Numbers marked from measured baselines throughout; scale-scenario arithmetic cross-checked against
the independent E10 re-derivation (agent report in `AUDIT_STATE.md`).*
