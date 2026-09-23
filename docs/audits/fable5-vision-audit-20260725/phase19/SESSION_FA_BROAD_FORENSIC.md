# Session FA — the broad-V4 full forensic: walk the decision cycle until it confesses

**Wave 19. Blocks B3050–B3099. Branch `phase19/broad-forensic`.**
Result doc: `phase19/SESSION_FA_BROAD_FORENSIC_RESULT.md`. Receipts: `phase19/receipts/forensic/`.
**You are Claude Fable 5** — this commission is owner-mandated to run on Fable, with **Fable
subagents through the Workflow tool**, not on Codex and not on Opus. The orchestrator (another
Fable session) reviews and merges your branch; you never touch `main`, the VPS, or any
broker-capable script.

## The owner's mandate, verbatim (2026-08-01)

> "listen here i dont know what gave you the authority to decide what is a good spent of research
> hours and what is not, what is worth machine compute time and what is not, that whole system is
> basically the result of all the research previously done and throwing it away is basically
> throwing away all the research done, a good system is not a good system in all months, it's
> basically a machine that knows what sleeve to trade at what time and what scenario in like a
> quantasized way, they say the best traders are who follow their systems and usually their
> systems can be made with mechanical rules, like when price does this then comes back then does
> this, then we do this and that, that's basically the system, to figuring out the architecture
> and the decision cycle and basically picking the decision that works by the systems discovered
> and tested and learnt and found in research in advanced sciences nad psychological conditions,
> if a system you said was done to the best repairs and it was all negative in all days, that
> makes absolutely no sense because you would be able to see what lost exactly and why it lost
> what it lost, was it wrong selection, was it a wrong sleeve, was the sleeve inaccurate, were
> the conditions inaccurate, why did the system leave the positive options and went for the
> negative option, is there a reason it was chosen, and the other ones declined, is there a way
> to make the system choose the good ones and not the bad one, i never allowed you to consider it
> dead, you just weren't able of fixing it yourself and that's why i want you to make a new fable
> session that will go through the system and basically solve all the puzzle of that system, not
> assuming, not signing codex and opus sessions to it, no, we have a fable session with workflow
> and subagents, and it goes through it in all its sections and find out all the changes needed
> and all of the subagents find exactly what is it causing the specific thing happening and the
> main fable session just figures out everything and sees if it's a sleeve problem or a mechanism
> problem or something must be wrong if it's negative in 20 days, the solution is not to throw it
> away and say 'no more hours on this' it's rather having the actual effort to figuring out whats
> wrong exactly with details and the sessions can do that with literally following the decision
> cycle in the replays from the top level until literally the last point of either trade or
> reject, not only see the results and the trades but actually follow the context and see where
> the defects are or what's happening exactly in the markets to make our system fail we need to
> understand all the reasons exactly with details to know, because i dont think you know the
> details yourself of why it's not working, you just saw the numbers and decided the opposite."

This is your charter. **The Workflow-tool multi-agent opt-in is standing for this session by the
owner's words above** ("a fable session with workflow and subagents"). Kill/park authority over
the family belongs to Borhen alone; your deliverable is understanding and repairs, never a
verdict to abandon.

## What the question is, precisely

The broad-V4 stack executed 57 trades on re-clocked January (−5.506 R realized, 21/21 negative
days) and 58 trades on virgin true-UTC February (−3.961 R realized, 0/20 positive days,
precision 0.309 vs 0.606 breakeven). **Meanwhile its own candidate pool provably contains
edge**: inverting one mechanism (`current_breaker_re_entry`, entry fixed, target 5D, stop 0.25D)
measures +11.88/+11.93 net R/trade on TRAIN/HOLDOUT January; a NY-session-LONG-metals cell
inside the same pool measures +0.089..+0.127 R/row. So the honest formulation of the owner's
question: **the selector stands in front of a surface that contains winners and losers, and it
systematically buys the losers and declines the winners — attribute exactly where and why, at
every stage of the decision cycle, with the context of each decision, not just its outcome.**

Decompose "why negative" into the owner's own axes and answer EACH with numbers:
- **Wrong selection?** (the gate/allocator chose badly from a mixed pool)
- **Wrong sleeve/mechanism?** (whole origin families are anti-predictive or noise — and which)
- **Inaccurate sleeve?** (right idea, wrong parameters/geometry/exits)
- **Inaccurate conditions?** (session/regime/context gating absent or mislabeled)
- **Why were the positive options declined?** (name the refusing stage per declined winner class)
- **Is there a rule that separates the good from the bad ex ante?** (the repair)

## Where everything is (verified paths, 2026-08-01)

Worktrees (read their artifacts in place; write only in YOUR worktree + your scratchpad):
- **January re-clocked truth**: `/Users/borr/GTOSActive/worktrees/wave16-rematerialization-20260731`
  — `docs/audits/fable5-vision-audit-20260725/phase16/receipts/`: `CJ_RECLOCKED_S0R0_V7_LANE/`
  (57-trade identity table), `CJ_RECLOCKED_POOL_S0R0_V1.json`,
  `pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz` (27,658 scoreable rows); full arm route (untracked,
  machine-local) under `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/attempt_5_typed_sparse/CJ_RECLOCKED_S0R0_V7/`
  (per-day ledgers, full economics export). The true-UTC lane estate root is
  `.hermes/evidence/phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/` (machine-local,
  read-only; registry via `--lane-input-registry` + `--purpose LANE_ITERATION`).
- **February truth**: `/Users/borr/GTOSActive/worktrees/wave18-true-utc-factory-20260801`
  — `phase18/receipts/`: `CP_FEBRUARY_FIRST_READ_{PROTOCOL,RESULT}_V1.json`,
  `CP_FEBRUARY_POOL_S0R0_V1.json`, `pools/CP_FEBRUARY_S0R0_POOL_V1.jsonl.gz`, the 58-trade
  table in the LANE receipt dir; full route (untracked) at `research/operations/.../attempt_5_typed_sparse/CP_FEBRUARY_TRUE_UTC_S0R0_V1/`.
  Also `CP_TRUE_UTC_B_TIME_MAP_V1.json` (83 cells, all negative) and
  `CP_TRUE_UTC_CANDIDATE_FACTORY_RESULT_V1.json` (the 1,092-look factory + the one survivor).
- **Path-complete January**: `/Users/borr/GTOSActive/worktrees/wave18-path-pools-20260801`
  — `phase18/receipts/`: `CQ_TRUE_UTC_S0R0_PATH_POOL_V1.json`,
  `pools/CQ_TRUE_UTC_S0R0_ORDERED_PATH_SIDECAR_V1.jsonl.gz` (**3,229,819 ordered post-decision
  observations covering all 27,658 candidates** — bid/ask-correct, 120-min horizon),
  `CQ_FROZEN_99_CELL_GRID_V1.json` (all 198 geometry×orientation cells for three populations),
  `CQ_CURRENT_BREAKER_REPAIR_V1.json` + `pools/CQ_CURRENT_BREAKER_REPAIR_TRADES_V1.jsonl.gz`,
  and the tools `cq_path_pool_grid.py` / `cq_repair_gate.py` (reuse them).
- **Engine code** (read-only; cite file:line): any current worktree of `main` — the decision cycle
  lives in `src/components/v4_timewarp_simulated_live_research_loop.py` (the loop),
  `src/components/selector_v4.py` (admission), `src/components/moonshot_scheduler_v4_best_trade_allocator.py`
  (selection/sizing), `src/components/permissions.py` (gates), with the lane runner in
  `src/research_infra/train_engine/` + `fast_engine/`.
- **Prior autopsies to extend, not repeat**: `phase16/SESSION_CK_MECHANISM_AUTOPSY_RESULT.md`,
  `phase18/SESSION_CQ_PATH_POOLS_RESULT.md`, `phase18/SESSION_CP_TRUE_UTC_FACTORY_RESULT.md`,
  CD's repair queue (`phase14`/`phase16` receipts).

**Bounded instrumented replay is available and cheap**: the lane path honors
`engineering_stop_after_day` (2 days ≈ 8 min / ~4 GB; 12 days ≈ 50 min — CB-3.3/CG receipts).
"Follow the decision cycle in the replays from the top level until literally the last point of
either trade or reject" — the owner's words — means at least one lane runs a short window with
instrumentation and walks EVERY candidate's fate on those days with full context: what the
market was doing, what each gate saw, what it passed/refused and why, what the allocator ranked,
what got sized, what the exit did. H3: never run two replay arms concurrently in one worktree.

## Suggested decomposition (yours to redesign — this is a brief, not a script)

One Workflow (or several chained) with Fable subagents, e.g.: a decision-cycle cartographer
(every stage, file:line, inputs, refusal semantics); per-window trade walkers (January's 57,
February's 58 — per trade: mechanism, direction, session, context at decision time, which gates
passed it, exit path vs available path from the sidecar); a declined-winners auditor (which
stage refused the pool's positive candidates, per class); a mechanism × direction × session
decomposition over ALL origin families (generalize CQ's grid — which families are
anti-predictive/invertible, which noise, which cost-killed); an exit/geometry counterfactual on
executed trades (how much loss is exit geometry alone); a precision decomposition (where the
0.309-vs-0.606 gap lives, and whether a selectable subpopulation beats its own breakeven); the
instrumented short-window replay walk; then an adversarial verify pass (refute your own top
causal claims through independent lenses) before you synthesize. Loop until the attribution is
COMPLETE: every lost R in both windows assigned to a named stage/mechanism with evidence, and
every "declined winner" class assigned to the gate that declined it.

## Deliverables

1. `SESSION_FA_BROAD_FORENSIC_RESULT.md` — findings-first: the complete defect map (per stage,
   per mechanism, with numbers and file:line), the answer to each of the owner's six axes, and
   the ranked repair list (each repair: what changes, expected effect, how it gets gated at the
   ratified rule — `CANDIDATE_BOOK_V1`, `B_balanced` α = 0.10, V27 tip at 59 declared/57 looks).
2. Receipts for every quantitative claim under `phase19/receipts/forensic/` (committed, compact;
   big intermediates stay machine-local in your route).
3. Iteration-ledger rows for every look, declared, `billed:false`, class
   `FORENSIC_DIAGNOSTIC` — February re-decode rows carry `owner_mandate_20260801` provenance.
4. "What I got wrong" section — house style.
5. NO arming, no ceremony package, no verdict to retire the family — repairs go to the sealed
   gate as candidates; kill/park stays the owner's.

## Effort and independence (added at relaunch, 2026-08-01)

- You run at **maximum effort** (`--effort max`), with the ultracode standing opt-in: exhaustive,
  correct answers are the goal and token cost is not a constraint. Where your Workflow calls
  expose per-agent effort, run synthesis/verify/judge agents at `max` and walkers at `high` or
  above. No agent-count guideline binds completeness on this mandate — the owner's words are
  "as many sessions as needed"; loop until the attribution is complete, not until a budget
  feels spent.
- **Prior sessions' conclusions are HYPOTHESES here, not inherited facts.** CK/CQ/CP/CD verdicts
  quoted above exist so you don't pay full price to rediscover them — but anchor your analysis
  on the RAW artifacts (pools, sidecar paths, per-day ledgers, engine code), re-derive what you
  rely on, and treat any prior claim your own measurement contradicts as refuted, loudly. The
  one non-negotiable inheritance is the safety boundary, not anyone's analysis.
- Nothing in this commission is a verdict you must reach. If the evidence says the dominant
  defect is somewhere nobody has named — a data-plumbing fault, a sign convention, a horizon
  mismatch, an allocator interaction — say exactly that with the receipts, whatever it does to
  anyone's prior story, including the orchestrator's.

## Boundaries (absolute)

March 2026 outcomes NEVER (April source lookback ≠ outcome permission). Live-forward (2026-07-29+)
outcomes NEVER. February re-decode: authorized by the owner mandate above, attribution only;
label anything fitted to it. No VPS, no broker-capable scripts, no token-bound config bytes, no
activation tokens, no sealed-path replay launches (H1/H5). The R2 drift check reports CN's
authorized engine break + two ledger materialization rows — known, leave them. Scoped A/B fence
(`gtos-ab-receipt-v1` vs the committed ZERO baseline, currently 12,705) embedded in
`phase19/receipts/SESSION_FA_AB_RECEIPT.md` if you change any code/test; pure-receipt work still
records the fence. Retire your in-flight row (B3050–B3099) in your closing commit.
