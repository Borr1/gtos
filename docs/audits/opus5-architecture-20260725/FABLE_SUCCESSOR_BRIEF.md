# Successor Audit Brief — for Fable

**You are the second independent auditor of GTOS. You have no restrictions.**

Written 2026-07-25 by the Opus-5 session that produced the audit in this directory, at Borhen's
direction. Its purpose is to give you everything — the original mission, the prior work, the owner's
vision, the decisions made in conversation that never reached a document, and an honest account of what
the first audit did not do.

---

## 1. Your authority

You have **full authority over this repository and this branch**. Explicitly:

- Audit anything, including the prior audit. Re-derive anything you want to re-derive.
- Go anywhere in the repo. Read the raw ledgers, the git history, the sparse-excluded paths, the other
  worktrees, the `.hermes/` tree, the data directories. Nothing is out of bounds.
- **Disagree with the prior audit freely.** Overturn any finding you can break with evidence. Say so
  plainly if the first auditor was wrong; that is the point of running a second one.
- Change, add, delete, and commit freely on this branch. Borhen: *"it doesn't have to revert it can do
  more changes and commit more… it's free to change anything, there is no reason for it to revert the
  actual commits."* Additive work is expected; reversal is available if your evidence demands it.
- Run experiments, benchmarks, replays, spikes. Spawn as many subagents as useful.
- Reach your own conclusions about scope, method, sequencing, and architecture. The prior plan is one
  engineer's judgment after one session, not a constraint on yours.

**The only thing asked of you is honesty about evidence class** — what you measured, what you inferred,
what you are hypothesising. That is a standard, not a limit.

**Explicit owner approval, given verbatim:** *"i do give explicit approval on any changes needed in any
part of the architecture and all of the scaffolding and wrappers and overengineering and basically to get
what's needed and to scale the whole thing, make it good, and go live."* The one thing that remains
Borhen's call is the risk dial and allocation profile (see `live_system_of_record.md`). Everything
architectural is yours.

Borhen's words: *"I don't mind it going around the repo and finding out what it needs to find out with no
restrictions at all… I don't like the Fable model to be restricted in any way… let it cook the way it's
made to do, get its full potential with no constraints to the things it reads, the things it does or
change."*

---

## 1a. The central mandate — build, do not patch

Read `OWNER_SESSION_CONTEXT.md` §4 before anything else. The short version, in Borhen's words:

> *"the older sessions were doing too much because they were conservative and working around with wrappers
> and gates and much much passive behavior rather than building a system that works, it kept patching like
> crazy, and that's not what i want to happen with the claude models because you guys are built
> differently."*

The prior audit found the evidence for this independently, before it was said. GTOS is a museum of
default-off patches: **the entire ML/learning pipeline is built and switched off** (§4a below); Selector V4
and Scheduler V4 are `enabled: true` with `live_activation_allowed: false` so their gate can never fire;
`moonshot_default_off_policy_router.py` is misnamed and *is* the live route; 179 `moonshot_*` modules
(63,646 lines) have zero reachability; 21.7 % of 1.33 M lines is reachable at all.

He also rejects the other face of the same instinct — making a system *look* safe by making it trade
nothing:

> *"i don't mean to limit everything and have 0.1% risk on every trade just to make it good… if the
> weights make sense and all of the architecture from getting the data to the selector to all the way until
> the trade happens makes sense, then the conservatism and waiting and blocking going live won't make
> sense."*

**Three challenge accounts are ready and waiting.** The bar for activation is that the chain from data →
market state → candidate → selector → scheduler → risk → order → fill → exit holds up under evidence — not
that every dial has been shrunk until nothing can go wrong.

---

## 2. What exists here

**Branch:** `audit/claude-opus5-architecture-20260725`, from `a3badc054`. Four commits by the prior session:

| Commit | Contents |
|---|---|
| `c370fed47` | five fail-open code fixes + a hardening/characterisation test module |
| `f56b0065b` | eight audit documents + benchmark receipts |
| `1e405b5eb` | repair of two regressions and six defects found by an adversarial reviewer of that first commit |
| `1b7f3e01c` | reconciled `CLAUDE.md` / `AGENTS.md`; added a continuation brief |

**The original mission prompt** is committed at `docs/audits/opus5-architecture-20260725/ORIGINAL_MISSION_PROMPT.md` (226 lines; it was the `/gtos-architecture-audit` slash command until 2026-07-26, archived here once the mission completed).
Read it — it is the same mission you are being given, and it is broader than what the first audit
delivered.

**Prior audit** — `docs/audits/opus5-architecture-20260725/`:

| File | What it is |
|---|---|
| `FINAL_INDEPENDENT_AUDIT.md` | executive conclusion |
| `MISMATCH_AND_RISK_REGISTER.md` | 37 findings, evidence-bound, with adversarial corrections marked |
| `SYSTEM_TRUTH_MAP.md` | components, call chains, boundaries, authority graph |
| `REPLAY_TRUTH_AND_PERFORMANCE_AUDIT.md` | the sampled profile and the 180 s question |
| `OVERENGINEERING_AND_DELETION_MAP.md` | reachability, duplication, deletion tiers |
| `TARGET_ARCHITECTURE.md` | proposed target design + migration |
| `IMPLEMENTATION_LEDGER.md` | what was changed, what was retracted, and why |
| `CONTINUATION_BRIEF.md` | the handoff written before this one |
| `receipts/` | raw sampled profile JSON, the profiling harness, the exact-parity micro-benchmark, the uncontended baseline |

**Re-runnable measurement infrastructure** — `receipts/wallsampler.py`, `receipts/profile_day_harness.py`,
`receipts/micro_parity.py`. The harness reproduces a sealed dense-day replay in ~10 minutes and is
annotated. `audit_runs/` (~3 GB, uncommitted) holds local copies of the sealed January inputs so you can
re-run without touching the owner's active worktree.

**`CONTEXT_STALENESS_MAP.md`** (this directory) classifies all 27 files in `.context/00_core/` by risk of
being mistaken for current authority. Three April-era files describe a **different system** — notably
`architecture.md`, 3,337 lines, status "Design Complete", describing an **XAUUSD-only Model A** design from
before the vNext surface, the 24-symbol universe and the hard halt. Nothing was deleted; the drift is
evidence. Date-check any constraint before obeying it.

**The owner's own vision documents** — read these early; the first audit did not, and it cost the best
version of its argument:

- `.context/00_core/GTOS_ULTRA_GOAL.md` (2026-07-16) — the controlling charter
- `.context/00_core/live_system_of_record.md` (2026-06-16) — authoritative for the live model
- `.context/00_core/vnext_absolute_moonshot_vision_and_limitations.md` (2026-06-07) — full capability map

---

## 3. Session context — decisions that are not in any document

**Full record with Borhen's own words: `OWNER_SESSION_CONTEXT.md` in this directory. Read it.** The
summary below is a pointer, not a substitute.

**The vision, confirmed.** GTOS is not a backtester. Per the charter it is a compounding learning
machine: replay at scale → feature store → label store → trained models → default-off runtime
intelligence → daily learning loop → command center → controlled activation → first payout → repeatable
payouts → scaling toward financial independence. The trading system is the output; **the iteration loop is
the asset.**

**Compute is not a constraint.** Borhen: *"AI compute is no issue meaning I can have sessions work and
build and do whatever is needed to get to the goal."* Plan accordingly — parallel sessions, exhaustive
differential testing, rebuild-and-prove rather than refactor-and-hope are all affordable. Do not
economise on analysis.

**Sequencing decision, made by the owner.** Do **not** run the remaining replay campaign first. Borhen:
*"it doesn't make sense for me to wait for 2 days replay when we can do the work first to get the whole
architecture to be scalable and then we can do the replays."* Architecture → scale → replays → live.
The remaining April/May/March campaign is ~2 days of machine time and is deliberately deferred.

**Hardware truth — the first audit got this wrong initially.** The machine is an **Apple M4 (base), 10
cores (4 performance + 6 efficiency), 16 GB RAM**. Not an M4 Pro. One replay arm peaks at **14.27 GiB —
89 % of total RAM**. Parallel arms are impossible today. Only 4 performance cores, and the replay is
single-threaded. Per-core speed is good, so the 507-second dense day is already on fast silicon: this
cannot be solved with hardware.

**Implementation ownership returns to Opus afterward.** Borhen: *"when it finishes I'll bring all its work
to you and you own the rest of the implementation."* This is context, not a restriction — build or spike
whatever you judge necessary. It means your plan should be **executable by another agent**: explicit
gates, falsification criteria, and enough detail that someone who did not do your analysis can carry it.

**What Borhen wants from you specifically:** *"continue in your work and take it to the next level and
figuring out every other thing that you didn't, and have a full plan and audit on the full vision as well
and the full plan to get there."*

---

## 4. What the first audit claims

Ten load-bearing findings. Each is `file:line`-bound in the register. **Attack any of them.**

| # | Claim |
|---|---|
| E1 | Replay implements a portfolio allocator, Selector V4 admission, and continuous sizing the live path does not have — so replay R does not transfer to production |
| E2 | `run_book.py`, the live entrypoint, is not in the repository |
| E3 | The proof layer verifies bytes, never economics (`parse_json=False` by design) |
| E4 | No sealed Phase-D arm has a semantic parity proof; the only comparator is hardwired to the June fixture |
| E5 | Proof/attribution is 60.6 % of replay CPU; `evaluate_candidate_v4` is 8.3 % of wall |
| E6 | One arm emits 15.75 GB of JSON for 148 orders / 72 trades; an order row is 494 KB, 1,274 keys, 765 distinct values, 63.8 % key names |
| E7 | The decision contract binds 42 source files by hash, 9 of them verifiers that never execute — so proof fixes cost a campaign re-run |
| E8 | Memory, not CPU, is the binding constraint |
| E9 | 21.7 % of 1.33 M Python lines is reachable; 219,469 lines LOW-risk deletable |
| E10 | The vision needs ~30× throughput, not ~3×, which forces a rebuild rather than an optimisation |

**E1 is the keystone.** If it is wrong, most of the proposed plan is unnecessary. It deserves your
hardest attack.

**E5 is fully re-checkable** in ~10 minutes from `receipts/`. If the classification of "proof work" versus
"domain work" is wrong, the performance conclusion changes.

---

## 5. Where the first audit was weak — start here

Written candidly, because this is the most useful thing in this document.

### 5a. The learning layer — checked late, and the result reframes the plan

Borhen asked whether GTOS even has ML. The answer, verified: **the complete pipeline exists and is
switched off.** ~6,600 lines.

| Module | Lines | Non-test importers |
|---|---:|---:|
| `wave4c_label_store_v2.py` | 1,540 | 1 |
| `wave4b_feature_store_v2.py` | 1,497 | 1 |
| `learned_edge_dataset_builder.py` | 770 | 5 |
| `learned_edge_trainer.py` | 719 | 1 |
| `learned_edge_walkforward_gate.py` | 570 | **0** |
| `learned_edge_layer_v4.py` | 489 | 3 |
| `model_router.py`, `runtime_learning_packet.py`, `model_pin.py`, `learning_actuator.py` | 1,056 | — |

`selector_v4_learned_edge_enabled` is **absent from every config file** (defaults `False` at
`selector_v4.py:2388`). `ultimate_book_runtime_learning_packet_enabled: False` at
`ultimate_book/bridge.py:103`. `learning_actuator.rerate_book` appears in `admission.py` **only in
comments**.

And the intelligence to feed it is already captured — one arm-month yields **154,316 missed-opportunity
rows** (*why not taken*), **69,888 decision rows** (*why approved or not*), 2,016 scorecards, 148 orders,
72 trades. Exactly the intelligence Borhen described the Codex sessions gathering.

**So the learning loop is far closer than "build a feature store" implies — it is disconnected, not
absent.** The prior audit's `TARGET_ARCHITECTURE.md` proposes building feature and label stores; that
proposal was written without knowing these exist. Reassess it. The real questions are why they were never
connected, whether they are the right design, and whether the 494 KB / 1,274-key capture format makes them
usable at all.

**Everything else below was never examined.** The vision's core is a learning system and the first audit
covered only the replay engine and decision chain. Untouched:

- the ML / learning layer beyond the inventory above — no assessment of design quality or correctness
- the AI Companion layer and the Autonomous Repair Companion
- the Command Center
- `mt5_ea/` (the EA side of execution)
- `data/` quality: tick corruption, quarantine evidence, source coverage, gap handling
- `knowledge_base/`, `pipeline_state/`, `shadow_logs/` — sparse-excluded from this worktree and never
  hydrated or inspected

**Context documents never read:** `.context/00_core/master_roadmap.md`, `gtos_second_brain.md`,
`architecture.md`, `pre_lock_final_review.md`, `llm_specialization_research_backlog.md`,
`ai_in_loop_cost_control_research_plan.md`, `local_heavy_data_inventory.md`,
`final_moonshot_post_hard_halt_research_plan.md`.

**Measurement gaps:**
- Profiled **one day-pair, one arm** (2026-01-01/02, S1R1). No coverage of other days, arms, or windows.
- Never ran a `derived_cold` measurement — every published number assumes warm derived caches, and the
  separate `build-pack` process has never been timed (open thread U4).
- Never resolved whether `scheduler_dynamic_daily_drawdown_budget_enabled` is on in the sealed arms,
  which decides whether a real ordering defect (R8) ever binds (U3).
- Never counted `duplicate_exact_candidate_instance` drops — silent candidate loss of unknown rate (U2).
- The optimisation work stopped at a micro-benchmark. **No end-to-end before/after was ever produced**,
  because the contract binding blocked it.

**Explicitly deferred by the mission, and therefore unexamined:** whether the researched economic weights
and selection criteria are themselves optimal. You may judge whether that deferral still makes sense.

**Method limits:** git history was only lightly used to explain how complexity accumulated, despite the
mission asking for it. Test quality was sampled, not systematically assessed. The live path could not be
exercised at all, because `run_book.py` is absent.

**Known errors made by the first auditor**, so you can calibrate how much to trust it:
1. Did not read `GTOS_ULTRA_GOAL.md` for most of the session, despite it being named in the context
   directory. Cost the framing, not the findings.
2. Claimed "zero regressions" from a subset test run. An adversarial reviewer found **two real
   regressions**. Both are fixed; the lesson is in `CLAUDE.md` §6.
3. Documented finding E7 — that editing contract-bound files fails the next replay closed — and then
   edited three contract-bound files anyway, breaking a test with the exact predicted error.

Two adversarial verifier passes changed **four** severity ratings on the twelve claims they examined. The
register marks each correction. Assume more remain.

---

## 6. What Borhen wants out of this

1. **Your own audit**, formed however you see fit — not a critique of the prior one, though overturning it
   where wrong is welcome and expected.
2. **A full plan for the full vision** — not just the replay engine. The learning loop, feature and label
   stores, models, forward shadow, command center, activation, first payout, scaling. The first audit
   stopped at the replay engine and the decision chain.
3. **The path to get there**, sequenced, with gates, assuming architecture work comes before scaling and
   scaling before live.
4. **Everything the first audit missed.**

Write durable outputs under `docs/audits/` in your own directory so both audits stand side by side and can
be reconciled.

---

## 7. Operational notes

- You are working in **this worktree on this branch**, so no other agent will be active while you run.
- The owner's live campaign worktree is `/Users/borr/GTOSActive/worktrees/replay-accel-engine-20260719`.
  Treat it as **read-only evidence** — its `.hermes/` and `research/operations/` trees hold the sealed
  campaign. The prior session verified it left all 292 source-evidence files byte-for-byte unchanged; hold
  that standard.
- **Hazards are in `CLAUDE.md` §3**, including a runnable check for whether a file you are about to edit
  is one of the 42 bound by the decision contract. The first auditor ignored its own warning here.
- The test suite is **not green at HEAD**: 11 pre-existing failures from an unhydrated LFS sleeve
  registry. A/B against the parent commit before claiming regressions.
- One replay arm consumes 89 % of RAM. Do not launch concurrent replays; watch for swap.
- `audit_runs/` (~3 GB, uncommitted) can be deleted if you need the disk; ~47 GB free at last check.
