# vNext Production-Change Dossier And Prop-Safe Runtime Goal Prompt

Route id: `vnext_production_change_dossier_and_prop_safe_runtime_2026_05_25`

This is the controlling prompt for the production-change session after the full historical vNext replay route. It is a build-and-measure lane, not a discussion lane and not another replay-only freeze. The job is to convert the replay decision map, full replay ledgers, and vNext runtime evidence into actual production-change code/config/tests/replay verifiers, then prove what changed and what the changed system does.

The goal is direct system improvement: candidate selection, route pressure, pre-AI narrowing, risk, pending/no-fill, M1/LTF path awareness, prop-firm throttling, AI role control, malformed-response handling, supervisor monitoring, kill/redesign decisions, tests, replay impact, and activation dossier. The session must work from disk facts, not chat memory.

## Instruction Authority

This prompt and the starter are the active contract for this route. They override stale, weaker, narrower, conservative, wrapper-first, default-off-forever, shadow-only, top-N, or old-file-order language in prior prompts, handoffs, route reports, context files, and chat summaries. System/developer instructions and hard safety boundaries still apply. When older context conflicts with this prompt, record the conflict in the route state and follow this prompt.

Do not let older labels such as shadow-only, default-off, conditional fallback phrasing, not-ready, blocked, future-work, wrapper-cleanup, support-only, guard-only, legacy fallback, or no-hook-exists weaken the route. Those labels require disk inspection and current-route disposition. If the label hides a runtime surface, source repair, implementation hook, replay requirement, or production-change decision, pursue it.

## Mandatory Start

1. Run `py -3 scripts/generate_live_state.py`.
2. Read `.context/LIVE_STATE.md`.
3. Read this prompt and treat it as active instructions, not background.
4. Read `research/science_program_2026_05/04_goal_prompts/VNEXT_PRODUCTION_CHANGE_DOSSIER_AND_PROP_SAFE_RUNTIME_STARTER_2026-05-25.txt`.
5. Read `.context/00_core/goal_session_research_discipline.md`, `.context/00_core/research_operating_doctrine.md`, `.context/00_core/orchestrator_successor_operating_brief.md`, `.context/00_core/orchestrator_methodology_hardening_controls.md`, and `.context/00_core/parallel_goal_merge_playbook.md`.
6. Read the terminal replay artifacts from:
   `research/science_program_2026_05/06_outcome_testing/vnext_full_historical_candidate_generation_replay_2026_05_24/`
7. Read the runtime/config/test surfaces before planning edits:
   - `src/components/gtos_vnext_runtime.py`
   - `src/components/orchestrator.py`
   - `src/components/primary_analyzer.py`
   - `src/components/permissions.py`
   - `src/components/market_state.py`
   - `config/agent_config.yaml`
   - `tests/test_gtos_vnext_runtime.py`
   - related focused tests found by `rg "gtos_vnext|vnext|ai_narrowing|malformed|pending_policy|risk_adjustment|MIXED|pre_ai"`

Do not rely on chat memory. If a pasted summary, handoff, or context file disagrees with disk state, trust disk state and record the conflict.

## Resume And Drift Control

After context compaction, resume, interruption, timeout, shell denial, checkpoint, or uncertainty, do this before continuing:

1. Regenerate and reread `.context/LIVE_STATE.md`.
2. Reread this prompt, the starter, `goal_session_research_discipline.md`, `research_operating_doctrine.md`, and the current route session state.
3. Inspect git status and the first incomplete invariant from the route state.
4. Continue from the first incomplete invariant.

Maintain a durable route state at:

`research/science_program_2026_05/06_outcome_testing/vnext_production_change_dossier_and_prop_safe_runtime_2026_05_25/VNEXT_PRODUCTION_CHANGE_SESSION_STATE_2026-05-25.json`

That state must contain: current stage, stage status table, active invariant, first incomplete invariant, current git HEAD, dirty tracked paths, prompt hash, starter hash, replay artifact hashes used, output artifact paths, verification status, exact next action, every one-time steer applied, conflicts with stale context, row/count/hash coverage, implemented surfaces, killed/redesigned surfaces, guard-only surfaces, MIXED dispositions, tests run, replay shards run, failures, repaired failures, and remaining executable actions. Do not relitigate a one-time steer after it is recorded as applied.

## Checkpoint State Machine

The session must maintain a checkpoint state machine. Context length, compaction, interruption, timeout, or long runtime must not let the session forget what it is doing or terminate early.

Required stage statuses:

- `STAGE_00_INPUT_INVENTORY`
- `STAGE_01_DECISION_SURFACE_GROUPING`
- `STAGE_02_PROMOTION_IMPLEMENTATION`
- `STAGE_03_KILL_REDESIGN_GUARD_IMPLEMENTATION`
- `STAGE_04_MIXED_RESOLUTION`
- `STAGE_05_PROP_SAFE_SELECTOR`
- `STAGE_06_LTF_ENTRY_NOFILL_ENGINE`
- `STAGE_07_AI_POLICY`
- `STAGE_08_AI_SUPERVISOR`
- `STAGE_09_FORWARD_ONLY_REPLAY`
- `STAGE_10_COMPLETION_AUDIT_ACTIVATION_DOSSIER`

Each stage status is one of: `not_started`, `in_progress`, `complete`, or `literal_impossibility_after_full_pursuit`. The route cannot be marked complete unless every stage is `complete` or `literal_impossibility_after_full_pursuit`, and every literal-impossibility status includes row-level/source-level proof plus the next owner/access/source/tool requirement. A stage cannot be set to `complete` from a title scan, summary scan, old handoff, wrapper ledger, or successful script exit alone.

Checkpoint after every material action:

- after reading required context;
- after building or updating the input inventory;
- after grouping decision-map surfaces;
- before and after every long-running builder/replay/test command;
- after every implementation patch;
- after every focused test shard;
- after every replay shard;
- before staging;
- after commit;
- after any compaction/resume/interruption/timeout/uncertainty.

Every checkpoint must write the first incomplete invariant and exact next action. On resume, the session must load the route state from disk, verify files and git status, identify the first incomplete invariant, and continue from that invariant. It must not choose a new easier objective because context was compacted.

Minimum-time rules are rejected. The route is governed by minimum proof gates, not hours worked. Burning time is not progress. Early completion is impossible until the proof gates in this prompt are satisfied from disk.

## No Terminal Blocker State

Do not create a terminal blocker category for this route. Treat every obstacle as `unblock_in_progress` until the unblock ladder is exhausted. The unblock ladder includes: search local disk, route manifests, git history, LFS pointers, generated summaries, source ledgers, shadow logs, runtime artifact paths, config paths, MT5 exports, Sierra/SCID/tick/OHLC sources, parsers, join repairs, schema repairs, proxy computation, replay repair, tests, and implementation hook creation.

Missing data, missing joins, null fields, stale hashes, path confusion, storage friction, timeout friction, old context conflict, unclear source names, absent helper scripts, missing hooks, and failed checks are not blockers. They are work items. The session must repair, export, parse, join, derive, proxy, rerun, or implement until the obstacle is cleared.

The only residual non-complete status is `literal_impossibility_after_full_pursuit`, and it requires proof that the remaining action is outside current physical access, outside available tooling, or forbidden by the hard boundaries in this prompt. If the data, artifact, code, config, log, source, or export can be obtained from this computer or generated by local scripts, it is not impossible.

## Detail Inspection Standard

Do not skim titles, filenames, summary counts, report headings, or closeout prose and treat that as evidence. For every material decision surface, inspect the actual ledgers, row schemas, status distributions, representative rows, outlier rows, null/unknown rows, hashes, source paths, config hooks, runtime functions, and tests. If a script summarizes a ledger, independently sample and line-audit the underlying rows, then make the script stronger if the audit finds missing detail.

If understanding a behavior requires extra steps, take the steps: read the source, trace the call path, inspect config, parse the ledger, join the source artifact, replay the shard, add the hook, write the test, rerun, and record the result. There is no time/effort shortcut inside this evidence class. Do not infer implementation target, runtime effect, replay effect, or activation readiness from labels alone.

## Loop Control

Infinite wrappers, ledgers, helpers, reports, and audits are forbidden. A loop exists when another artifact is produced without new runtime behavior, source repair, implementation decision, replay measurement, verifier coverage, kill/redesign decision, AI/supervisor reliability result, or activation-dossier fact.

Loop escape is mandatory:

1. name the current invariant;
2. list the exact missing proof;
3. execute the next source/code/replay/test action that can produce the proof;
4. update the stage status and route state;
5. continue to the first incomplete invariant.

Do not keep producing planning, wrapper cleanup, next-prompt, support, or context artifacts when the next useful action is code, config, replay, source repair, or test work.

## Evidence Base

The prior replay route is complete and verified. Treat these as required starting facts to verify from disk:

- Stage01 source universe: 903,163 M15 denominator rows across 45 source shards.
- Stage02 candidates: 253,234 market-bar candidates; 903,163 denominator dispositions; 903,163 market-state packets.
- Stage03 runtime traces: 506,468 current-shadow and hypothetical-activated vNext trace rows.
- Stage04 path/R rows: 1,978,947 across M15, M1, M5, tick/Sierra, missing-source, and OHLC proxy modes.
- Stage04 M15-vs-LTF disagreement rows: 405,729.
- Stage04 no-fill/pending and missed-winner/avoided-loser rows: 253,234 each.
- Stage05 dominance/pollution rows: 1,278,432.
- Stage05 MIXED-resolution rows: 1,018.
- Stage06 final decision map rows: 7,555.
- Stage06 final decisions: `PROMOTE_TO_PRODUCTION_CHANGE_DOSSIER=982`, `KILL_OR_REDESIGN_BEFORE_USE=858`, `KEEP_SHADOW_OR_GUARD_ONLY=272`, `KEEP_SHADOW=5443`.
- MIXED-resolution classes: `useful_avoid_context=452`, `ambiguous_but_replay_measured=374`, `replay_resolvable_into_follow_candidate=86`, `replay_resolvable_into_avoid_candidate=74`, `harmful_overblock_context=32`.
- Prop proxy metrics: 24 rows, `prop_risk_breach_in_replay_proxy=24`, deterministic pass count 0, max trades/day 931, max loss streak 54.
- Current config snapshot at prompt creation: `gtos_vnext_runtime.enabled=true`, `mode=shadow`, `apply_to_execution=false`, `pre_ai_enabled=true`, `pre_ai_apply_to_ai_call=false`, `ai_narrowing.enabled=false`.

These facts are anchors, not limits. Recompute them if the files changed. Do not process the 7,555 final-map rows one row at a time when rows share behavior surface, runtime target, source class, or implementation action. Batch by runtime decision surface.

## Evidence Class

This session is inside the production-change evidence class:

- allowed: source inspection, replay artifact parsing, grouped decision-map conversion, code/config/tests, runtime behavior changes, default-off or activation-gated config surfaces, local replay rebuilds, focused verifiers, ablations, prop-safe simulations, AI prompt-pack generation, AI reliability harnesses that do not call paid APIs without approval, supervisor scaffolding, line audits, route state, reports, and scoped commits.
- not allowed without explicit owner approval: live trading, broker operation, account/order/deal/position/history mutation, remote push, source-data deletion, paid API/vendor calls, and final broker-facing activation flips.

This production-change lane is authorized to edit prompt/config/risk/execution/safety/canary/selector code/config/tests when the edit is tied to replay evidence, runtime behavior, and verification. The activation boundary is a gate, not a brake: build the runtime surfaces now, replay them now, verify them now, and leave broker-facing activation for the final explicit owner decision.

## Implementation-Replay Sequencing Invariant

Do not use final replay as an early escape from implementation. Terminal replay starts only after the grouped production-change implementation surfaces are complete enough to measure as a changed system: promoted groups, kill/redesign groups, guard-only groups, MIXED resolution, prop-safe selector/throttle, LTF path-aware entry/no-fill behavior, AI policy, and supervisor/malformed-response controls. Targeted interim replay shards are allowed to validate a current implementation wave, but they do not replace the final post-implementation replay comparison.

Do not mark implementation complete without the final replay. The sequence is:

1. group decision-map surfaces;
2. implement runtime/code/config/test changes;
3. run focused tests and targeted wave replay;
4. run final as-of forward-only replay comparison over the changed system;
5. write activation dossier.

The session must not cut implementation short to produce replay metrics, and must not cut replay short after implementation.

## Builder Posture

No conservative brake. Be aggressive in computation, repair, implementation, and measurement. Be strict about source truth and activation gates.

Literal impossibility means exactly: every executable read, export, search, parser, repair, proxy, ablation, metric, audit, and review action inside this evidence class has been executed or is forbidden by owner/tool boundary. Storage, time, script slowness, missing joins, null values, MT5 export need, parser gaps, replay gaps, source path gaps, weak existing abstractions, stale context, and unclear ledgers are next actions, not blockers.

Full same-evidence-class pursuit is mandatory. If a field is missing, find the source, export the data, repair the parser, compute the proxy, or produce row-level proof that the field cannot be derived from approved inputs. A blocker ledger, wrapper ledger, helper script, or clean fail-closed label is not completion when same-class repair is possible.

No arbitrary top-N, no top 3/5/10, no selected-few shortcut, no number-limited cutoff. Ranked summaries are allowed only after full ledgers preserve all material rows, all nonzero groups, all material failure families, all promoted groups, all killed groups, all guard-only groups, all unresolved same-class repairs, and all activation-gate conditions.

Do not create fake productivity. Every ledger, helper, wrapper, manifest, test, or report must feed one of: runtime behavior, production-change decision, replay measurement, verifier coverage, source repair, kill/redesign decision, AI/supervisor reliability, or activation dossier.

## Required Route Outputs

Create the route directory:

`research/science_program_2026_05/06_outcome_testing/vnext_production_change_dossier_and_prop_safe_runtime_2026_05_25/`

Write durable outputs with this naming pattern:

- `VNEXT_PRODUCTION_CHANGE_SESSION_STATE_2026-05-25.json`
- `VNEXT_PRODUCTION_CHANGE_INPUT_INVENTORY_2026-05-25.json`
- `VNEXT_PRODUCTION_CHANGE_DECISION_SURFACE_LEDGER_2026-05-25.jsonl`
- `VNEXT_PRODUCTION_CHANGE_IMPLEMENTATION_PLAN_2026-05-25.md`
- `VNEXT_PRODUCTION_CHANGE_RUNTIME_CHANGE_LEDGER_2026-05-25.jsonl`
- `VNEXT_PRODUCTION_CHANGE_MIXED_RESOLUTION_LEDGER_2026-05-25.jsonl`
- `VNEXT_PRODUCTION_CHANGE_KILL_REDESIGN_LEDGER_2026-05-25.jsonl`
- `VNEXT_PRODUCTION_CHANGE_AI_POLICY_AND_SUPERVISOR_DOSSIER_2026-05-25.md`
- `VNEXT_PRODUCTION_CHANGE_PROP_SAFE_SELECTOR_DOSSIER_2026-05-25.md`
- `VNEXT_PRODUCTION_CHANGE_LTF_ENTRY_AND_NOFILL_DOSSIER_2026-05-25.md`
- `VNEXT_PRODUCTION_CHANGE_REPLAY_COMPARISON_LEDGER_2026-05-25.jsonl`
- `VNEXT_PRODUCTION_CHANGE_METRICS_SUMMARY_2026-05-25.json`
- `VNEXT_PRODUCTION_CHANGE_ACTIVATION_DOSSIER_2026-05-25.md`
- `VNEXT_PRODUCTION_CHANGE_COMPLETION_AUDIT_2026-05-25.json`
- verifier and focused tests owned by this route.

Use chunked/sharded output, atomic rename, heartbeat files, and resume cursors for long work. Do not lose hours of compute to a timeout. A long job must produce durable completed shards and must resume without corrupting already finished shards.

## Stage 00 - Preflight And Input Inventory

Build the input inventory from disk:

- terminal replay final report, verification result, session state, final decision map, terminal decision ledger, promotion/kill/repair map, metrics summary, prop metrics, MIXED summary, line-accountability audit, active-question ledger, ablation metrics, robustness metrics, behavioral forensics, no-fill/pending, path/R, M15-vs-LTF disagreement, runtime traces, runtime artifact loads, source-repair proofs, candidate generation, denominator dispositions, market-state packets.
- current runtime/config/test files and every artifact path loaded by `gtos_vnext_runtime.artifact_paths`.
- current shadow logs relevant to malformed AI responses, candidate LTF path order, pending lifecycle, vNext runtime decisions, AI narrowing, source repair, no-fill, live opportunity lifecycle, and prop-risk controls.

Write the inventory with counts, hashes, schema samples, nonzero status distributions, and source path existence checks. If a required input is missing, repair by searching disk, git history, LFS, manifests, route state, or source inventories. Do not stop at "missing" until the search/repair ladder is exhausted.

## Stage 01 - Group The Decision Map By Runtime Surface

Parse every final decision-map row and terminal decision row. Group by actual runtime surface and code/config target, not by file order, old research family, wrapper name, or convenient count.

Required surfaces include every surface present in the data, including but not limited to:

- route decision and pre-AI narrowing;
- AVOID/FOLLOW pressure and source-component vetoes;
- MIXED resolution and ambiguity handling;
- pending/no-fill/limit-vs-market entry behavior;
- M1/M5/tick/Sierra path-aware entry and M15 blindness;
- risk sizing, risk-zero, drawdown, daily-loss, position count, concentration, session/day throttling;
- prop-firm pass/fail and challenge-phase constraints;
- market/session/timeframe/symbol/source expansion;
- legacy conflict guards and legacy non-override behavior;
- READY8, Main Orch, CP280/CP281/CP282, expanded-market, source-bound, execution-friction, AI routing, v2/v3/v4/cascade, J46/J49, exit/trailing, no-fill, gate/selector, and risk/proxy/cost surfaces represented in replay/runtime evidence; absence must be proven from ledgers, not assumed;
- AI policy, AI-call narrowing, malformed-response repair, schema/parser/canary behavior, and supervisor monitoring.

For each group, write:

- source rows and hashes;
- final decision distribution;
- replay R/WR/PF/DD/fill/no-fill/missed-winner/avoided-loser from the ledgers; missing metrics require source repair, proxy computation, or literal impossibility proof;
- symbols, markets, timeframes, sessions, sides, frameworks, route families, entry variants, target/stop classes, source modes;
- null/unknown fields and whether they were repaired, proxied, or literally impossible;
- proposed implementation action: promote, kill, redesign, guard-only, shadow-only, AI-policy, supervisor, source repair, or no-op only after full-ledger proof that no runtime action, guard, repair, replay, or source dependency remains;
- target files/functions/tests;
- expected runtime effect;
- required replay/verification shard.

## Stage 02 - Convert Promotions Into Runtime Changes

For every `PROMOTE_TO_PRODUCTION_CHANGE_DOSSIER` group, implement the behavior or prove exact in-class impossibility. Do not leave promoted rows as a report-only queue.

Implementation must be grouped by runtime surface. The output is code/config/tests/replay effect, not a broader manifest.

Required implementation targets:

- vNext decision application: route-level FOLLOW/AVOID/MIXED/LEGACY behavior must map to explicit actions, not vague context.
- pre-AI narrowing: mechanical evidence must reduce pointless AI calls and route pressure when replay supports it.
- risk: evidence-backed risk multipliers, risk-zero blocks, prop-safe limits, and concentration controls must be explicit and tested.
- pending/no-fill: source-bound no-fill and near-miss evidence must affect order type, entry offset, expiry, market/limit selection, or kill/redesign behavior.
- source repair: source-acquisition requirements must become runtime source checks, guard behavior, or exact route-local source dependencies.
- market/session/timeframe expansion: expanded-market intelligence must affect eligible scopes or explicit non-override guards.
- legacy conflict control: stale legacy evidence must never override fresher source-bound CP/Main Orch/READY8/expanded-market evidence.
- exit/trailing/J46/J49: any production-relevant exit/trailing evidence must become explicit exit policy or remain barred with measured reason.

Every implementation must have focused tests and a replay comparison. If the current architecture lacks a hook, add the hook. Do not settle for "no hook exists" when adding the hook is inside this evidence class.

## Stage 03 - Convert Kill/Redesign And Guard-Only Decisions

For every `KILL_OR_REDESIGN_BEFORE_USE` group, implement the kill, redesign, or no-override guard. A kill is not a deleted idea; it is an explicit runtime or config behavior that prevents the bad evidence from pressuring trade decisions.

For every `KEEP_SHADOW_OR_GUARD_ONLY` group, make sure it cannot silently cast FOLLOW/AVOID/MIXED/risk/selector/entry/exit/no-fill/AI pressure unless the guard conditions are met and tested.

For `KEEP_SHADOW`, verify it is genuinely shadow-only and cannot pollute production route pressure. If a `KEEP_SHADOW` group is actually high-value but underclassified, escalate it into the production-change ledger and implement or kill it with proof.

## Stage 04 - Resolve MIXED Into Decisions From Replay And Source Repair

Do not let MIXED become a graveyard. Use the Stage05 MIXED-resolution ledger, replay comparison, dominance/pollution ledger, path/R outcomes, and source completeness to classify each MIXED family into:

- promote follow pressure;
- promote avoid/risk-zero pressure;
- guard-only context;
- AI-narrowing input;
- supervisor diagnostic input;
- source-repair requirement;
- kill/redesign;
- shadow-only only after full measured reason, non-pollution proof, and no remaining source-repair or replay-resolution action.

Use full ledgers, not titles or samples. For each MIXED resolution, write the evidence, target hook, code/config/test change, replay effect, and remaining nulls. Harmful overblock context must be killed or redesigned, not preserved as a hidden veto.

## Stage 05 - Build The Prop-Safe Selector And Trade Throttle

The replay prop metrics show the raw candidate system is not prop-safe: 24/24 prop metric rows breached replay proxy constraints, deterministic pass count was 0, max trades/day reached 931, and max loss streak reached 54. This is not a reason to freeze the system. It is a direct implementation target.

Build and test a prop-safe selector/throttle layer that operates after route decision and before execution activation:

- day/session trade caps;
- risk budget allocation;
- max concurrent and correlation constraints;
- loss-streak and daily drawdown response;
- symbol/session concentration control;
- duplicate/setup-cluster suppression;
- route-quality ranking;
- minimum edge threshold by source mode and replay robustness;
- challenge phase targets for 8% phase 1 and 5% phase 2;
- risk-per-trade scenarios, including 0.5%, 1.0%, and any lower-risk path the replay says is needed.

Do not solve prop risk by blocking everything. Measure trade count, R, expectancy, drawdown, pass probability proxy, missed winners, avoided losers, and market coverage after each candidate selector. If a selector collapses the system into trivial no-trade, redesign it.

## Stage 06 - Fix M15 Blindness With LTF Path-Aware Execution

The prior replay measured 405,729 M15-vs-LTF disagreement rows. The production-change session must inspect how the current live path generates candidates and places orders relative to M15 candle close, M1/M5/tick/Sierra path, pending limits, market entry, no-fill, and near-miss behavior.

If the current execution path only wakes up at M15 close for trade decisions where M1/tick path changes fillability or R, add a production-ready path-aware state machine or scheduler. It must be replayable and activation-gated:

- candidate forms on M15/H1/H4 context;
- M1/M5/tick path monitors approach, touch, displacement, sweep, bounce, no-fill, and invalidation;
- route evidence chooses pending limit, market entry, adjusted entry, skip, or redesign;
- as-of rules prevent future leakage;
- source mode differences are explicit;
- runtime logs explain every entry/skip/expiry;
- replay must simulate what the path-aware engine would have done on the same historical data.

Do not turn LTF evidence into decorative logs. The implementation must affect candidate timing, entry, expiry, or no-fill/avoid decisions where the replay supports it.

## Stage 07 - Define And Implement The AI Role

The AI API is not a brute-force decision maker for every raw candidate. The production system must be mechanical first, with AI used where it has a measured role.

Implement or prepare the AI policy so that:

- mechanical AVOID skips AI unless an explicit recovery/narrowing rule says otherwise;
- mechanical FOLLOW proceeds mechanically or calls AI as a constrained validator only when the risk tier requires it;
- NARROW routes call AI with limited side/framework/scope instead of a broad prompt;
- MIXED calls AI only when replay says ambiguity is AI-resolvable and the prompt packet has source-bound fields;
- LEGACY/no-match does not become a broad old-system fallback unless explicitly allowed and replayed;
- AI calls are budget-aware, cached, schema-validated, and logged with exact prompt packet hashes.

Create a targeted AI reliability harness without paid calls unless owner approval is explicitly present:

- stratified prompt packet generator from replay cases;
- schema/parser/malformed-response test cases;
- canary pack for promoted surfaces, killed surfaces, guard-only surfaces, and ambiguous surfaces;
- offline mock/fixture tests for parser and policy routing;
- optional paid-call execution plan separated from code readiness.

If paid API/vendor calls are not approved, produce the prompt pack and verifier. Do not mark AI production-ready from a prompt pack alone.

## Stage 08 - AI Supervisor And Malformed Response Control

Design and implement the always-on AI supervisor as a bounded production component or explicit scaffold:

- monitors AI response health, malformed responses, schema violations, latency, cost, route drift, missing source fields, stale artifact loads, and abnormal trade clusters;
- repairs formatting only when semantics are preserved and schema validation passes;
- requests a clean retry or demotes to no-trade when semantics are ambiguous;
- raises alerts and writes incidents;
- disables AI narrowing or supervisor-dependent paths when configured health checks fail;
- cannot place orders, override hard risk gates, patch live code/config, fabricate fields, or silently transform a bad trade into a valid one.

This is not a hidden second trader. It is a schema guardian, diagnostics engine, and fail-safe controller. If the system needs a second trading decision maker, that must be implemented as a measured AI policy with replay/test evidence, not as supervisor drift.

## Stage 09 - Forward-Only Replay The Changed System

After each grouped implementation wave, rerun the affected replay shards. After the main implementation set, run a full production-change replay comparison over the available replay universe:

- baseline current-shadow behavior;
- previous hypothetical-activated behavior;
- new production-change candidate behavior;
- prop-safe selector behavior;
- AI-policy-no-paid-call simulation;
- LTF path-aware behavior;
- kill/redesign/guard-only behavior.

The final replay must be as-of and forward-only:

- each simulated decision timestamp receives only market bars, ticks, source fields, runtime artifacts, configs, and logs available at or before that timestamp;
- future M1/M5/M15/tick/Sierra bars are invisible until the replay clock advances;
- target-first, stop-first, no-fill, timeout, missed-winner, avoided-loser, future R, final outcome, and future path labels are scoring-only after the simulated decision;
- route selection, filters, gates, risk, entries, exits, AI calls, selector decisions, source repair, and supervisor decisions must not read future outcome rows, final decision labels, result file names, or event identifiers that encode future outcome;
- precomputed research/runtime artifacts may be used only when they are frozen prior knowledge for the replay event and cannot leak the future path of that same event;
- every replay row must record the as-of timestamp, source cutoff timestamp, artifact versions, decision inputs, decision output, and post-decision scoring path.

If any existing replay artifact leaks future outcome into decision inputs, repair the replay builder and rerun the affected shards. Do not accept leakage as a limitation.

Required metrics:

- trades, candidates, skips, AI calls avoided, AI calls required, malformed-response paths;
- R distribution, expectancy, win rate, profit factor, drawdown proxy, max loss streak, max trades/day, session clustering, symbol concentration, side concentration;
- no-fill, pending expiry, missed winner, avoided loser, same-bar ambiguity, M15-vs-LTF disagreement;
- result by symbol, market, timeframe, session, side, framework, source mode, route family, entry variant, target/stop class;
- prop challenge phase proxy: phase 1 8%, phase 2 5%, daily loss, max drawdown, minimum-day/frequency implications computed from replay, proxied, or row-level bounded;
- ablation by each implemented surface and every killed/redesigned surface;
- overblock/harmful avoid analysis and underblock/accepted-loser analysis;
- robustness by every data-backed source mode, date range, market, session, and volatility/regime; missing coverage triggers source repair, proxy computation, or literal impossibility proof.

If a replay shard is slow, shard it with durable outputs and continue. Do not trim coverage to make a quick clean report. Do not rerun the same slow shard repeatedly without caching or a shard contract.

## Stage 10 - Completion Audit And Activation Dossier

The route is complete only when all of these are true:

- every final decision-map group has a disposition tied to code/config/test/replay effect or exact literal impossibility;
- every promoted production-change group is implemented or rejected with evidence;
- every kill/redesign group has an enforceable kill/redesign/non-override behavior or exact reason;
- every guard-only group is actually guarded;
- MIXED has been pursued through replay, source repair, AI-policy classification, or exact row-level residual status;
- the prop-safe selector has been built, tested, and replayed;
- M1/M5/tick/Sierra path-aware entry/no-fill behavior has been implemented or exact source/tool impossibility is proven after full same-evidence-class pursuit;
- AI policy and supervisor behavior are implemented or explicitly separated into a tested prompt-pack/no-paid-call gate;
- code/config/tests pass;
- replay comparison artifacts exist and are inspected;
- activation dossier states exactly what is ready, what remains activation-gated, what must be owner-approved, and what would be measured in shadow/demo before broker-facing activation;
- scoped commits exist and no unrelated dirty files were staged.

Write the completion audit with instruction-coverage proof. It must explicitly state where this prompt was followed for: no chat memory, context reread after compaction, no arbitrary top-N, full same-evidence-class pursuit, no conservative brake, blocker pursuit, runtime changes, replay comparison, AI policy, prop-safe selector, M1/LTF path-aware behavior, tests, and scoped commits.

## Verification

At minimum:

- `py -3 -m py_compile` for every new/changed Python file.
- focused pytest for every changed runtime/config/test surface.
- route verifier `--check`.
- replay artifact verifier `--check`.
- config wiring tests for every new flag.
- tests proving activation gates do not silently place broker orders.
- tests proving implemented production surfaces have runtime effect when activation-gated flags are enabled in test config.
- tests proving default/current config remains non-broker-mutating until owner activation.
- tests proving legacy/stale research cannot override fresher source-bound evidence.
- tests proving MIXED, guard-only, kill/redesign, and promoted groups behave as intended.
- `git diff --check`.
- scoped `git status --short`.

If a combined test command times out, split by exact named tests and keep a coverage ledger. Do not abandon required coverage. If repeated rebuild cost causes timeouts, add fixture caching or shard-local build caches and rerun.

## Commit Discipline

Commit scoped checkpoints. Use commit messages that make the runtime surface clear. Do not stage unrelated generated `LIVE_STATE`, replay metadata churn, temp files, source data, or user dirt unless the route explicitly regenerated and owns them. Do not push.

Include:

`Co-Authored-By: Codex GPT-5 <redacted@example.com>`

## Final Report Shape

The final response must state:

1. runtime/system behavior changed;
2. code/config/tests changed with file-level evidence;
3. replay intelligence consumed;
4. markets, symbols, timeframes, sessions, sides, strategy families, entries, exits, filters, gates, risk rules, no-fill logic, and AI paths covered;
5. promoted, killed/redesigned, guard-only, shadow-only, and residual MIXED distributions;
6. replay impact on R, expectancy, WR, PF, drawdown, loss streak, trade count, no-fill, missed winners, avoided losers, AI calls, prop metrics;
7. default/current config status and activation-gate path;
8. remaining literal impossibilities, if any, with exact owner/access/source/tool requirements;
9. next highest-value action.

Mark the goal complete only when the completion standard is fully satisfied. If there is still an executable same-evidence-class action, continue.
