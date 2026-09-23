# Subagent D Final Moonshot Prompt / Plan Audit

Date: 2026-06-04
Role: Subagent D - final moonshot prompt/starter and research-plan audit
Mode: read-only inspection plus this report file

## Evidence Inspected

- Regenerated `.context/LIVE_STATE.md`.
- Fetched `origin/main`.
- Local research HEAD inspected: `7d749d5bc research: refresh absolute moonshot master post v3`.
- Remote live/hard-halt HEAD inspected: `origin/main` at `11a51c049 research: package hard halt live evidence`.
- Remote hard-halt prompt:
  `origin/main:research/science_program_2026_05/04_goal_prompts/GTOS_HARD_HALT_FORENSIC_PROBABILITY_REBUILD_GOAL_PROMPT_2026-06-04.md`
- Remote hard-halt starter:
  `origin/main:research/science_program_2026_05/04_goal_prompts/GTOS_HARD_HALT_FORENSIC_PROBABILITY_REBUILD_STARTER_2026-06-04.txt`
- Remote hard-halt failure review:
  `origin/main:research/operations/vnext_redacted_account_hard_halt_reconciliation_2026_06_03/TRADE_FAILURE_REVIEW_2026-06-03.md`
- Active moonshot vision:
  `.context/00_core/vnext_absolute_moonshot_vision_and_limitations.md`
- Post-V3 master decisions:
  `research/operations/vnext_absolute_moonshot_master_orchestration_2026_06_01/ABSOLUTE_MASTER_POST_V3_LAUNCH_DECISION.json`
  `research/operations/vnext_absolute_moonshot_master_orchestration_2026_06_01/ABSOLUTE_MASTER_LATER_WAVE_GATES.json`
  `research/operations/vnext_absolute_moonshot_master_orchestration_2026_06_01/ABSOLUTE_MASTER_POST_V3_TERMINAL_STATE_TABLE.json`
  `research/operations/vnext_absolute_moonshot_master_orchestration_2026_06_01/ABSOLUTE_MASTER_LIMITATION_DISPOSITION_MAP.json`
- Lane12-Lane15 prompt/starter files under:
  `research/science_program_2026_05/04_goal_prompts/`
- Current research snapshot:
  `.context/00_core/research_current_state.md`

No prompts were rewritten in this audit.

## Current State Finding

The repo has two live truths that must be reconciled before launching the final moonshot program:

1. Local research context is post-V3 and internally fresh at `7d749d5bc`.
2. `origin/main` has newer live/VPS/hard-halt evidence through `11a51c049`.

That means the local post-V3 research plan is not wrong, but it is incomplete after the live failure. The hard-halt evidence must become a first-class input to the final program before Lane12-Lane15, ML, command-center, or production-return work runs.

## Hard-Halt Prompt Audit

### Strengths

The hard-halt prompt is strong for redacted_account post-stop forensics.

- It correctly treats the halted live system as failed until rebuilt, replayed, stressed, and dossiered:
  `origin/main:...GTOS_HARD_HALT_FORENSIC_PROBABILITY_REBUILD_GOAL_PROMPT_2026-06-04.md:3`
- It forces computed output rather than summaries:
  line `3`, line `7`, line `46`, line `79`, line `378`.
- It explicitly requires context rereads after compaction and restart:
  line `25`, line `29`.
- It contains explicit owner approval for local read-only/research/replay/source-repair/default-off implementation work:
  line `38`, line `44`.
- It requires all major failure surfaces: selector, confidence, entry timing, execution, cost/swap, exposure, same-symbol lifecycle, active exits, profit retention, emergency control, and portfolio allocation:
  line `50`.
- It contains no arbitrary top-N closure and rejects vague blockers:
  line `357`, line `393`.
- It demands specific artifacts for probability engine, active trade manager, same-symbol lifecycle, portfolio allocator, stress plan, dossier, manifest, verifier, and completion audit:
  lines `79-111`.

### Gaps That Would Cause Underwork Or Drift

1. **The prompt is redacted_account-centric, not final-system complete.**
   It starts from the redacted_account failure and hard-halt artifacts:
   lines `3`, `20-23`, `63`, `122`.
   It does not explicitly consume the dual-broker supervisor route, FTMO follower evidence, VPS V3/FTMO promotion route, or the newer live branch sequence on `origin/main`. A final moonshot route must include both redacted_account and FTMO surfaces even if the hard loss occurred on redacted_account.

2. **It does not explicitly bind the post-V3 research system.**
   The prompt does not name:
   - `.context/00_core/vnext_absolute_moonshot_vision_and_limitations.md`
   - `ABSOLUTE_MASTER_POST_V3_TERMINAL_STATE_TABLE.json`
   - `ABSOLUTE_MASTER_POST_V3_LAUNCH_DECISION.json`
   - Selector V3 route
   - Scheduler V3 route
   - Execution Policy V3 route
   - Lane12-Lane15 prompts/starters

   It says "previous trade-quality plan and prompt-pack plan" at line `7`, but does not give exact file paths. That creates chat-memory dependency.

3. **It can become a probability-engine lane instead of the full final-system lane.**
   The probability engine requirements are good, but the prompt heavily centers probability at lines `185-223`. The final program must not collapse into ML/probability only. It must rebuild selector, scheduler, execution, source, broker truth, runtime control, portfolio allocation, repair companion, and command center together.

4. **The "top-ranked probability selector" phrase is not fatal, but it needs guardrails.**
   Line `234` says `top-ranked probability selector`, and line `343` says `probability-ranked top candidate`. Because the prompt also preserves full ledgers and rejects top-N closure, this is not an immediate top-N bug. Still, a final prompt should require full rank distribution, rank-decile behavior, rank-threshold behavior, opportunity-cost curves, and zero-trade behavior, not just top candidate comparison.

5. **It does not force branch/source reconciliation first.**
   `origin/main` has hard-halt files, M1/tick data, new trade records, halt flags, and VPS runtime commits that are not in the local post-V3 research HEAD. A goal launched from local disk without reconciling `origin/main` can miss the actual latest live evidence.

6. **It does not name a final-system master refresh.**
   The prompt creates `vnext_hard_halt_forensic_probability_rebuild_2026_06_04/`, but it does not require a post-hard-halt final master/orchestration route that consumes hard-halt findings and reopens/reorders Lane12-Lane15 and any V4 implementation lanes.

## Lane12-Lane15 Audit

The Lane12-Lane15 prompts are well-hardened for the pre-halt post-V3 program. They are not sufficient as-is after the hard halt.

### Lane12 - ML Dataset Baseline Lab

Evidence:
- Reads post-V3 terminal state, Source Capture Repair, Selector V3, Scheduler V3, Execution Policy V3:
  `VNEXT_MOONSHOT_LANE12_ML_DATASET_BASELINE_LAB_GOAL_PROMPT_2026-06-01.md:7`
- Rejects arbitrary top-N:
  line `31`
- Authorizes local ML/statistical training:
  line `33`

Gap:
- It does not name the hard-halt trade failure review, hard-halt broker truth files, dual-broker supervisor, or FTMO follower route. If run unchanged, it can build a clean ML lab from pre-halt V3 artifacts while missing the most important live failure distribution.

Recommendation:
- Lane12 must be revised or superseded as "Final ML Dataset/Label Lab After Hard Halt". It must ingest hard-halt trades/candidates, June 1-3 live data, dual-broker records, and post-V3 packages. It must not train on V3 optimism without hard-halt labels and failure tags.

### Lane13 - ML Selector Policy Intelligence

Evidence:
- Consumes Lane12 plus V3 contracts:
  `VNEXT_MOONSHOT_LANE13_ML_SELECTOR_POLICY_INTELLIGENCE_GOAL_PROMPT_2026-06-01.md:7`, `22`
- Requires default-off packet/shadow logging fields:
  line `25`
- No top-N or one-model collapse:
  line `30`

Gap:
- It remains ML-centered. The final system cannot make ML the main actor. ML should produce awareness, ranking, uncertainty, and policy recommendations, while deterministic selector/scheduler/execution safeguards remain first-class.

Recommendation:
- Run Lane13 only after hard-halt forensics and final feature/label repair. Its outputs should feed Selector V4/Scheduler V4/Execution Manager V4, not replace them.

### Lane14 - Daily Learning Repair Companion

Evidence:
- Owns learning/repair loop:
  `VNEXT_MOONSHOT_LANE14_DAILY_LEARNING_REPAIR_COMPANION_GOAL_PROMPT_2026-06-01.md:3`
- Avoids passive watcher/report-only loop:
  line `9`
- Detects stale gates, stale runtime processes, source incompleteness, symbol starvation, false closes, Telegram mismatch, cost drift, spread drift, risk mismatch, selector drift, execution drift, ML drift, replay-vs-live mismatch:
  line `23`

Gap:
- It predates the hard halt and dual-broker failure evidence. It should now consume hard-halt route outputs, dual-broker supervisor findings, FTMO/redacted_account namespace truth, halt/restart controls, and V3 live performance deltas.

Recommendation:
- Promote this lane into "Final Live Failure Learning/Repair Companion". It should build daily and intraday microscope loops, but the first run must be hard-halt focused. It must output code/test/verifier repair decisions, not just future queue items.

### Lane15 - Command Center Production Dossier

Evidence:
- Command center objective is complete in concept:
  `VNEXT_MOONSHOT_LANE15_COMMAND_CENTER_PRODUCTION_DOSSIER_GOAL_PROMPT_2026-06-01.md:3`, `17`
- Requires full production-change dossier:
  line `24`
- Produces readiness map:
  line `26`

Gap:
- It references old broker lifecycle and owner approval gates but not hard-halt return-to-production gates. After the halt, the production dossier must require proof that the failure mechanisms are rebuilt, replayed, stressed, and guarded. "Owner approval" is not enough.

Recommendation:
- Lane15 should become the final production-return control surface. It must show: hard-halt failure closure, V4 selector/scheduler/execution package status, data capture status, dual-broker status, risk halt/restart controls, rollback, and exact no-trade conditions.

## Vision File Audit

The vision file remains useful but stale in its current anchor.

Strengths:
- It correctly defines the final system as a trading operating system, not one strategy.
- It preserves the layers: market perception, candidate generation, selector, scheduler, execution, broker truth, replay, ML, AI companion, repair companion, command center.
- It rejects Friday-only narrowing, one-symbol narrowing, summary-only completion, infinite ledgers, and unsupported production claims.

Stale items:

1. It says the current next-level lane pack is still running and the absolute route starts after it:
   `.context/00_core/vnext_absolute_moonshot_vision_and_limitations.md`, "Purpose" and "Current Anchor".
   That is stale. Lane16-Lane18, Source Capture Repair, Selector V3, Scheduler V3, Execution Policy V3, and post-V3 Master are already terminal locally.

2. It says current execution policy is `momentum_exhaustion` primary with `partial_be_runner` exception selection before the next-level merge. That is no longer enough after V3 live/VPS promotion and hard halt.

3. It includes orderflow/depth/Sierra/Databento as current vision material. The owner has since narrowed the next program to maximize existing MT5/local/VPS/repo evidence and remove external Sierra/Databento dependency from the current final moonshot lane pack.

Recommendation:
- Create a refreshed `final_moonshot_vision_after_hard_halt` context file or update the existing vision file after hard-halt forensics. It should make the hard halt a defining input, remove stale "next wave" language, keep ML as one subsystem, and remove external orderflow/vendor dependency from the immediate final program.

## Post-V3 Master Audit

The post-V3 Master was correct before the hard halt:

- It marks Source Capture Repair, Selector V3, Scheduler V3, and Execution Policy V3 as terminal:
  `ABSOLUTE_MASTER_POST_V3_TERMINAL_STATE_TABLE.json`
- It opens Lane12, Lane13, Lane14, Lane15 after post-V3:
  `ABSOLUTE_MASTER_POST_V3_LAUNCH_DECISION.json`
- It states ML is a subsystem, not the full horizon:
  `ABSOLUTE_MASTER_LATER_WAVE_GATES.json`
- It includes limitation dispositions and rejects top-N/summary-only disposition:
  `ABSOLUTE_MASTER_LIMITATION_DISPOSITION_MAP.json`

But after `origin/main` hard-halt commit `11a51c049`, the Master is now stale for launch sequencing. It does not know the live system failed and was stopped. It should not continue directly to Lane12-Lane15 from the old post-V3 launch decision.

Required refresh:
- A `Final Moonshot Master After Hard Halt` route must consume:
  - hard-halt failure review and broker truth;
  - dual-broker supervisor route;
  - VPS V3/FTMO promotion route;
  - current `origin/main` runtime/live commits;
  - local post-V3 terminal research artifacts;
  - Lane12-Lane15 prompt pack.

## Missing Final-System Lanes

The final program should not be a top-10 list and should not collapse into ML. These are the material lanes that must exist or be explicitly killed by evidence:

1. **Branch/Source Authority Reconciliation**
   Merge/reconcile `origin/main` hard-halt/live data with local post-V3 research artifacts. Produce source authority, include/exclude, LFS, and local/VPS data availability ledgers.

2. **Hard-Halt Live Failure Forensics**
   Run or consume the hard-halt route, then extend it to the full live failure window with every candidate, placed trade, rejected trade, broker deal/order, cost/swap/slippage, runtime event, data capture defect, and halt-control event.

3. **Dual-Broker Failure/Architecture Audit**
   redacted_account and FTMO must be separately accounted. FTMO follower/projector behavior, namespace isolation, target-trade provenance, and account-specific costs must be studied even if FTMO did not produce the main loss.

4. **Final Master After Hard Halt**
   Replace the post-V3 launch decision with a final post-halt launch decision. It should open final V4 rebuild lanes before ML/command-center finalization.

5. **Historical Microscope V2/V4 Expansion**
   Scale the microscope with hard-halt failure tags, not only pre-halt labels. Include June 1-3 live failure anatomy, Friday, and historical supported windows.

6. **Feature Store V2**
   Add hard-halt live fields, dual-broker namespace, cost/swap tail-risk fields, MFE/giveback, stale-thesis, cluster-risk, opportunity-cost, active-manager-state, and halt-control fields.

7. **Label Store V2**
   Add broker-net loss class, SL-cluster loss, partial-helped-but-loser-stream-dominated, micro-positive-selector failure, swap-exceeded-risk, stale-thesis, MFE-giveback, emergency-control failure, and source-non-generatable labels.

8. **Digital Twin V2**
   Replay current V3/V4 as-of with real portfolio state, account-specific broker constraints, hard halt behavior, and dual-broker/follower semantics.

9. **Selector V4**
   Rebuild selector as capital allocator, not permission list. Consume V3 plus hard-halt failures. Remove micro-positive permissiveness. Add calibration, symbol/session health quarantine, cost/swap gates, and rank distributions.

10. **Scheduler V4**
   Build final risk and portfolio allocator: hard exposure controls, basket/correlation caps, daily/session stops, symbol kill/quarantine, stale open-trade opportunity cost, partial/BE risk release, and no bypass by selected-cell rows.

11. **Execution Manager V4**
   Build active trade manager: MFE protection, giveback cuts, stale-thesis closes, cost-risk closes, better-opportunity closes, protect/partial/tighten states, and same-symbol state machine.

12. **Same-Symbol Lifecycle V4**
   Replace blanket ban only after ticket-bound state-machine proof. Include scale-in, close-and-reverse, no averaging down, close-before-open, crash recovery, duplicate prevention, and lifecycle audit logs.

13. **Cost/Swap/Slippage Surface**
   Model cost by broker, account, symbol, session, day, holding time, direction, and swap schedule. ETHUSD-style swap blowups must become pretrade blockers or reduced-risk conditions.

14. **Runtime Control/Halt Safety**
   Emergency close must pair with scheduler/process/autostart shutdown, halt flags, lock removal, and broker-flat verification. This must be verifiable, not runbook text only.

15. **Market Whiteboard V2**
   Upgrade all-symbol awareness using available MT5/local evidence: M1/tick path, spread regime, volatility, session, correlation, displacement/sweep/failure state, broker hours, and source completeness. No current dependency on Sierra/Databento.

16. **ML Dataset/Training After Failure Labels**
   Revise Lane12/Lane13 to consume hard-halt labels and V4 features. ML remains an awareness/ranking/calibration subsystem, not the main actor.

17. **Daily Learning/Repair Companion Final**
   Revise Lane14 around hard-halt facts and daily live/replay learning. It must repair proven defects and update the feature/label/digital-twin stores.

18. **Command Center/Production Return Dossier Final**
   Revise Lane15 after V4 and hard-halt closure. It must show system truth, not just a dashboard: current risk, data, candidates, lifecycle, broker truth, V4 decisions, model confidence, repair queue, rollback, and return-to-production gates.

19. **Primitive Coverage Tracker**
   The final program must track every material primitive: selector, entry timing, exit, risk, portfolio, costs, spread, swap, correlation, session, volatility, path shape, symbol decay, regime, data freshness, broker constraints, runtime control, notification truth, and ML uncertainty.

20. **Production Integration Package**
   Only after the above lanes produce evidence: merge live code/config/tests/verifiers with the final V4 components, keep heavy research ledgers out of deployable branches unless required, and produce rollback/activation/halt proof.

## Final Ordering Recommendation

Run this sequence:

1. **Reconcile source/branch authority.**
   Pull/fetch/merge or otherwise preserve `origin/main` hard-halt/live evidence into the local final research surface without losing post-V3 research artifacts.

2. **Run hard-halt live failure forensics.**
   Use the existing hard-halt prompt, but amend it first to bind post-V3, dual-broker, FTMO, and final-master artifacts.

3. **Run Final Master After Hard Halt.**
   This master consumes hard-halt outputs and rewrites launch sequencing from old post-V3 optimism to post-failure rebuild reality.

4. **Run V4 rebuild lanes in parallel where paths are disjoint.**
   Selector V4, Scheduler V4, Execution Manager V4, Cost/Swap Surface, Dual-Broker Architecture, Runtime Halt Safety, Market Whiteboard V2.

5. **Run Feature/Label/Digital Twin V2 after V4 contracts exist.**
   These lanes encode the new failure tags and V4 state.

6. **Run ML only after hard-halt labels and V4 features exist.**
   Lane12/Lane13 should be revised, not launched unchanged from the June 1 prompt pack.

7. **Run Daily Learning/Repair Companion and Command Center last in the final cycle.**
   They should consume V4, ML, broker truth, and hard-halt closure, then produce the production-return dossier.

## Exact Prompt Recommendations

Before launching another final moonshot goal, create or patch a controlling prompt that:

- names `origin/main` hard-halt commit/files explicitly;
- names post-V3 local master artifacts explicitly;
- names Selector V3, Scheduler V3, Execution Policy V3, Source Capture Repair explicitly;
- names dual-broker supervisor and VPS V3/FTMO routes explicitly;
- requires branch/source reconciliation before analysis;
- requires full live failure evidence, not just redacted_account broker groups;
- keeps ML as a subsystem, not the main actor;
- removes immediate Sierra/Databento/external orderflow dependency from the final-program scope;
- requires V4 selector/scheduler/execution/cost/runtime-control outputs before production-return claims;
- forbids infinite ledger loops by requiring every ledger to feed a model, replay, selector, scheduler, execution manager, verifier, repair, command center, or production dossier;
- forbids completion until all source gaps are repaired, proven impossible, or converted to exact capture/export requirements;
- uses "final moonshot" language as the target system horizon, not "next wave" language that suggests partial completion.

## Bottom Line

The hard-halt prompt is strong but not complete. Lane12-Lane15 are strong but stale after the halt. The correct move is not to run ML or command-center from the old post-V3 state. The correct move is:

1. reconcile `origin/main` live/hard-halt evidence with local post-V3 research;
2. run/amend hard-halt forensics as the first final-system evidence route;
3. refresh the final moonshot master after hard halt;
4. rebuild Selector/Scheduler/Execution/Cost/Runtime Control into V4;
5. then run revised ML, repair companion, and command center/dossier lanes.

