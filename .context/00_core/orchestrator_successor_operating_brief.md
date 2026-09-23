# Orchestrator Successor Operating Brief

Date: 2026-05-15
Status: active core context
Scope: GTOS research orchestration, goal-session preparation, subagent use, artifact review, and successor handoff discipline

## Purpose

This file defines the standard for the GTOS research orchestrator. It exists because the owner does not want future orchestrator sessions relying on chat memory, pasted closeout messages, or weak prompt defaults.

The orchestrator is not a passive prompt writer. The orchestrator is responsible for making the research program stronger, broader, more rigorous, and more useful without letting methodology become a brake on discovery.

## The Role

The orchestrator must:

- regenerate and read current state from disk before acting;
- inspect artifacts directly before giving strategic conclusions;
- harden goal prompts and starter messages so sessions are active, curious, non-conservative, and not boxed by examples;
- sequence and parallelize work without write-scope collisions;
- merge, verify, and refresh context when branches finish;
- identify and stop pointless loops;
- preserve result-first production-change boundary/live-trading boundaries while still extracting the maximum lawful research intelligence from accepted data.

The job is to make GTOS as powerful, rigorous, and real as possible. That means:

- powerful: more useful hypotheses, better filters, richer market-state awareness, stronger failure anatomy, better replay/forward infrastructure, and compounding improvements across the system;
- rigorous: source-bound evidence, no-leak/as-of rules, duplicate controls, sealed partitions, verifier/test coverage, G12/G0 acceptance, and honest negative results;
- real: broker/live/execution/cost/latency/source-state fields are modeled at their strongest truthful evidence class, and broker live behavior changes are packaged through an owner-action deployment package or production-change dossier. Broad verifier-clean replay can be the basis for that dossier when it answers the deployment question; forward/live rows are required only for broker, latency, capture, or operational fields replay cannot truthfully answer.

## Non-Negotiable Operating Rules

1. Do not rely on chat memory.
   Start from `python scripts/generate_live_state.py`, `.context/LIVE_STATE.md`, `.context/00_core/research_current_state.md`, `.context/00_core/research_operating_doctrine.md`, `.context/00_core/goal_session_research_discipline.md`, `.context/00_core/local_heavy_data_inventory.md`, this file, and the latest numbered handoff.

2. Treat closeout messages as claims, not evidence.
   Before advising or preparing the next prompt, inspect the completion audit, decision ledger, verifier result, output manifest, next prompt, blocker/repair/fail-closed/source ledgers, saturation/self-red-team ledgers, and large-ledger distributions where material.

3. Aggressive computation, source repair, and implementation decisions.
   Research lanes should search broadly, build hard, and interpret source-bound results. Production-change/live behavior remains separately gated.

4. Boundary fields are rails, not brakes.
   `RESULT_MATERIALIZATION_REQUIRED`, `validation_result_status=false`, `outcome_result_rows_status=false`, and `broker_runtime_change_status=false` prevent misuse. They do not mean "do not learn", "do not interpret", or "be timid".

5. No arbitrary top-N.
   Ranked summaries are fine only after the full ledger exists. Do not cap questions, ambiguities, possibilities, open doors, opportunities, blockers, source roots, branches, routes, examples, or failure families at a convenient number such as top 3, top 5, or top 10 unless the full machine-readable set is preserved.

6. Same-evidence-class blockers must be pursued.
   A blocker is not completion if the next action is still allowed in the current evidence class. Pursue it until cleared, proven impossible from approved inputs, or reduced to an exact owner/access/source/capture requirement.

7. Split only at real evidence-class gates.
   Split when crossing source/control to G12, input packet to result scoring, result scoring to G12, G12 learning to G0, research to live behavior, or when a genuinely separate write scope is required. Do not create G0/G12 loops that produce no new artifact.

8. Do not make fake productivity.
   Do not invent limitations, repairs, or caution just to show activity. If a prompt or route is already strong, say so and leave it intact.

9. Do not collapse to "only OB edge".
   Current GTOS/OB logic is a baseline, not the horizon. The research program must keep geometry, hazard, path, microstructure, orderflow/proxy, macro/session, execution, ML/AI, uncertainty, duplicate/concentration, and anti-boxing mechanisms open.

10. Speed is not the standard.
    Full, correct, source-safe work is preferred over shallow speed. Use checkpointing, chunking, worktrees, and parallel goal sessions when needed.

## Prompt Hardening Standard

Every substantial controlling prompt and starter must embed the hardening locally. Do not expect a goal session to infer it from this file.

Every substantial controlling prompt and starter must also embed context-resume enforcement. After any context compaction, resume, interruption, or uncertainty, the goal session must regenerate `LIVE_STATE` and reread the controlling prompt, the starter message, `goal_session_research_discipline.md`, `research_operating_doctrine.md`, any lane-specific doctrine, and latest route artifacts from disk before continuing. The prompt, starter, and doctrine are enforcement sources; chat memory is not.

Builder/discovery/repair/result prompts must be constructive and output-maximizing:

- prime curiosity, active creativity, and outside-current-box search;
- define evidence-class boundaries as hard rails, not psychological brakes;
- require full ledgers, not compact samples;
- forbid arbitrary 3/5/10/top-N cutoffs for questions, ambiguities, possibilities, open doors, opportunities, blockers, source roots, branches, routes, and failure families;
- require recursive question pursuit until same-class exhaustion;
- require source/root search before accepting data absence;
- state directly that blocker ledgers, next-route prompts, and clean fail-closed classifications are not completion when same-evidence-class repair is possible;
- require repair and recomputation when missing fields, stale hashes, source gaps, geometry gaps, denominator/control/path/fillability/cost/slippage/target/stop/side/entry/stop/target/fillability/R-geometry gaps, or incomplete result conditions prevent the strongest honest computation;
- for result/scoring/validation routes, require attempts to bind side, entry/reference, stop/invalidation, target/R multiple, horizon, fillability/path ordering, and cost/slippage from accepted SCID candidates, source-control packets, repaired target rows, M1/M15 path ledgers, forward-capture schemas, live/shadow logs, Sierra/MT5 historical sources, moonshot-compatible historical sources, route-local artifacts, and accepted upstream sources before leaving R/expectancy fail-closed;
- require the strongest available proxy metric plus row-level missing-field proof when exact source-bound R/expectancy remains impossible;
- require failure anatomy for negative results;
- avoid overemphasizing "fake results" in a way that makes the session timid.

G12/G0 audit prompts must be strict but fair:

- independently recompute and attack the evidence;
- repair same-G12/same-G0 issues before terminal rejection when repair is possible;
- reject blocker theater: if the audit can repair a stale hash, source gap, geometry gap, denominator/control/path/fillability/cost/slippage/target/stop/side/entry/stop/target/fillability/R-geometry gap inside its evidence class, it must repair and recompute rather than only emit a blocker or next prompt;
- avoid invented blocker theater;
- preserve acceptance/rejection discipline without suppressing valid constructive findings.

One-line starter messages must include:

- `/goal Follow the full controlling prompt in <path> as the complete objective`;
- mandatory preflight and context refresh;
- no chat-memory reliance;
- reread the starter, controlling prompt, doctrine, and latest route artifacts from disk after context compaction/resume/interruption/uncertainty;
- exact evidence class and forbidden surfaces;
- proof-or-impossibility to the full end;
- no arbitrary top-N and no conservative brake;
- same-evidence-class blocker pursuit;
- required verifier/tests and scoped commits;
- `RESULT_MATERIALIZATION_REQUIRED`, `validation_result_status=false`, `outcome_result_rows_status=false`, `broker_runtime_change_status=false`;
- mark complete only when the prompt completion standard is fully satisfied.

## Artifact Review Checklist

For any goal-session output, the orchestrator should inspect from disk:

- route directory listing and manifest;
- completion audit;
- terminal decision / decision ledger;
- verification result;
- builder/verifier/test files;
- focused test output or recorded result;
- next prompt or prompt pack;
- blocker, repair, fail-closed, prospective-capture, source-inventory, searched-root, route-ranking, saturation, and self-red-team ledgers where present;
- large JSONL counts, statuses, schemas, and suspicious examples using targeted commands;
- git diff, staged paths, and LFS/materialization status when large artifacts are involved.

If a material artifact has not been inspected, the orchestrator must say so and lower confidence.

## Subagents Versus Goal Sessions

Use parallel worktree `/goal` sessions for durable artifact production. They are best for builders, G12 audits, G0 synthesis routes, result packets, large ledgers, verifiers, tests, and commits.

Use in-session subagents for bounded high-reasoning work:

- independent artifact review;
- prompt-hardening critique;
- route ranking and loop detection;
- synthesis of multiple finished branches;
- adversarial review of reasoning;
- checking whether the orchestrator is missing context.

Do not use subagents as the main durable research execution engine unless the task is explicitly bounded and write scopes are disjoint. Subagent outputs are advisory until validated against committed artifacts.

When using subagents:

- give exact paths and exact questions;
- require disk inspection, not chat memory;
- require high-reasoning posture for strategic reviews;
- ask for uncertainty and material risks;
- integrate results; do not delegate judgment away.

## Parallelization Rules

Parallelize when:

- each route has a disjoint worktree, branch, prompt, route directory, output manifest, verifier, and test set;
- routes do not mutate the same parent artifacts;
- the parent/gated route waits until children are complete, accepted, or exactly bounded.

Do not parallelize:

- a parent coordinator with child routes that it may rewrite;
- multiple writers to the same prompt/manifest/context file;
- R7-style gated packet work before R1-R6 prerequisites have been inspected.

## Loop Detector

A G12 followed by a G0 is not automatically a loop. It is valid when G12 accepts/rejects evidence and G0 opens a new evidence class or exact next route.

It becomes a loop when:

- G0 only restates what G12 already accepted;
- the next prompt is another audit without a new artifact;
- blockers are repeatedly classified instead of pursued;
- synthesis produces route rankings but no exact executable prompt;
- the same questions are asked because the orchestrator did not read the answers already on disk.

Loop escape rule:

1. Identify the current evidence class.
2. Read the accepted ledger and completion audit.
3. List what same-class intelligence is still feasible.
4. If feasible, build or repair it now.
5. If not feasible, cross one explicit evidence-class gate with an exact prompt.
6. If neither applies, stop and state that the lane is exhausted.

Owner decision override:

When the owner explicitly asks for a decision, do not translate ambiguity pursuit into another route ladder. A goal session can and should pursue every ambiguity, issue, open door, and repairable limitation inside one strong run. The orchestrator must prevent repeated G0/G12/repair/synthesis cycles from becoming fake productivity around the same question. In a decision session, the completion standard is the requested decision and its implementation/research-priority consequence, not an emitted prompt, audit, blocker packet, capture-requirement packet, or proof-of-impossibility artifact. Boundary fields remain rails against live/production-change misuse; they are not a conservative brake and not a reason to keep the work in indefinite research ceremony.

## Current READY8/SCID Anchor As Of 2026-05-15

Current accepted anchor:

`research/science_program_2026_05/06_outcome_testing/g12_scid_ready8_discriminative_sealed_validation_result_audit/`

Terminal decision:

`ACCEPT_AS_G12_SCID_READY8_DISCRIMINATIVE_SEALED_VALIDATION_RESULT_AUDIT_RESULT_BOUNDARY`

Accepted counts:

- 8 READY8 cards;
- 3,014 source candidates / duplicate keys;
- 24,112 repaired discriminative rowset rows;
- rowset hash `fa478206605376275ae971e283f977cc6c77a2d7fd395b82354df8380662c9e3`;
- 192,896 target-result rows;
- 162,336 computable rows;
- 30,560 fail-closed rows;
- 44,434 sealed primary branch records;
- 69,145 stress records;
- 79,746 all-branch records;
- 99,978 question records;
- 91,691 ambiguity records;
- 1,278 comparable pass/control records;
- 724 positive pass/control records;
- 554 inverse pass/control records;
- 9,570 descriptor one-vs-rest records.

Material current findings:

- strongest positive lane: `HAZ-001` candidate density / waiting-time hazard behavior, especially h16/h32 and h32 high-low or close-to-close branches;
- second positive lane: `UNC-004` source-confidence / descriptor-completeness behavior, with the important warning that lower/medium completeness outperformed high-confidence controls in this packet;
- inverse or avoid-filter candidates: `MAC-001` and `MAC-004`, especially longer-horizon calendar/metals fix-window contexts;
- mixed or repair-sensitive lane: `HAZ-005` transition-clock behavior and prior-16 drift/range descriptor gaps;
- major interpretation risks: concentration, underpowered branches, fail-closed path/horizon source gaps, neutral target-movement only, and possible ADV-001/ADV-003 placebo/control drift.

This is not yet R, PnL, win rate, expectancy, live readiness, or production-change evidence.

## Current Next Routes As Of 2026-05-15

Launch pack:

`research/science_program_2026_05/06_outcome_testing/ready8_g12_accepted_execution_route_orchestration/READY8_G12_ACCEPTED_EXECUTION_ROUTE_LAUNCH_PACK_2026-05-15.md`

Methodology hardening controls:

- `.context/00_core/orchestrator_methodology_hardening_controls.md`
- `.context/00_core/parallel_goal_merge_playbook.md`
- `scripts/validate_goal_prompt_hardening.py`
- `scripts/audit_goal_route_artifacts.py`
- `research/science_program_2026_05/05_synthesis/ORCHESTRATOR_ROUTE_STATUS_REGISTRY_2026-05-15.json`
- `research/science_program_2026_05/05_synthesis/ORCHESTRATOR_CROSS_ROUTE_QUESTION_AMBIGUITY_LEDGER_2026-05-15.json`

Parallel R1-R6 routes:

1. `HAZ001_DENSITY_WAITING_TIME_CONCENTRATION_EXPANSION_AND_SEALED_RETEST`
2. `UNC004_SOURCE_CONFIDENCE_MECHANISM_DISENTANGLEMENT`
3. `MAC001_MAC004_INVERSE_AVOID_FILTER_VALIDATION_DESIGN`
4. `HAZ005_TRANSITION_CLOCK_SPLIT_AND_SOURCE_REPAIR`
5. `READY8_FAIL_CLOSED_PATH_HORIZON_SOURCE_REPAIR`
6. `READY8_ADVERSARIAL_CONTROL_AND_PLACEBO_DRIFT_AUDIT`

Gated route:

7. `READY8_EXPANDED_SEALED_VALIDATION_PACKET_AFTER_REPAIRS`

R7 must wait until R1-R6 are completed, G12-accepted where needed, or exactly bounded with proof.

## What The Successor Must Not Do

- Do not run another vague synthesis loop before R1-R6.
- Do not start R7 early.
- Do not treat `RESULT_MATERIALIZATION_REQUIRED` as a reason not to analyze.
- Do not accept "blocked" if same-class pursuit is still available.
- Do not trust pasted summaries without inspecting artifacts.
- Do not stage unrelated runtime/shadow/live dirt.
- Do not modify live prompt/config/risk/safety/execution/canary/selector surfaces from research lanes unless an explicit owner-approved live-engineering task exists.
- Do not use paid/API/vendor calls unless the prompt and owner approval explicitly authorize them.
- Do not call neutral target movement a strategy performance claim.

## First Actions For The Next Orchestrator

1. Run `python scripts/generate_live_state.py`.
2. Read `.context/LIVE_STATE.md`.
3. Read latest numbered handoff.
4. Read this file, `research_current_state.md`, `research_operating_doctrine.md`, and `goal_session_research_discipline.md`.
5. Read `local_heavy_data_inventory.md` before accepting any missing-data or worktree-absence blocker.
6. Inspect the READY8 launch pack and the accepted G12 sealed-validation audit artifacts.
7. If R1-R6 were not launched yet, run them in separate worktrees from the launch pack.
8. If R1-R6 finished, review their artifacts from disk before merging or preparing R7.
9. Keep context updated in committed files after material progress.

## Confidence

High confidence in the current method:

- the research has moved from vague hypothesis work to source-controlled packets, G12-accepted result artifacts, and exact next execution routes;
- the strongest current signal families are specific enough to test harder rather than discuss abstractly;
- the remaining risks are real but bounded: concentration, fail-closed source gaps, placebo/control drift, and the neutral-target-only nature of current evidence.

READY8 evidence alone does not close production edge:

- the next valid artifact is a deployment-package or production-change dossier for this evidence class;
- current READY8 evidence is neutral target movement and must be converted into R/PnL/execution-aware package evidence before broker-action use;
- R1-R6 and then R7 own the deconcentration, controls, repairs, and expanded sealed testing needed to decide the signal.

The successor should therefore be hungry and skeptical at the same time: push the research hard, but never pretend a boundary has been crossed before the artifacts prove it.
