# GTOS Master Research-Program Goal Prompt

Date: 2026-05-03
Status: active durable /goal spec
Scope: research/tooling only unless explicit CEO approval is obtained
Promotion posture: NO_PROMOTION_VERDICT by default

## How To Use This File

This file is the durable goal specification for a long-running `/goal` session.

The short `/goal` starter message should point to this file and instruct the agent to adopt it as the active goal. The agent must not rely on chat memory for the goal. It must reread this file from disk whenever context is compacted, memory feels incomplete, or a major task boundary is reached.

## Objective

Run the GTOS research program as a sequential goal queue across all research lanes until there are no unblocked research/tooling tasks left.

Reconcile the master backlog, execute the highest-EV tasks lane by lane, add new questions and follow-ups into the queue as they appear, and keep looping until each task is classified as one of:

- DONE
- REJECTED_FAILED
- ACCEPTED_CANDIDATE_DISCOVERY
- STRONGER_THAN_BASELINE_CANDIDATE
- BLOCKED_WITH_REASON
- DEFERRED_WITH_TRIGGER
- FILED_FOR_APPROVAL
- STILL_PENDING_RANKED

The parent goal is not allowed to fake completion by ignoring blocked tasks. It must convert every ambiguity into evidence, a rejected hypothesis, an implementation ticket, a data requirement, an owner approval request, or a precise future trigger.

## North Star

Incrementally improve every component and aspect of GTOS so the system becomes more powerful, selective, structurally aware, and ultimately more profitable.

The work should compound across:

- market-state awareness,
- candidate selection,
- failure filtering,
- path management,
- V2/V2b/V3/V4 structural replay,
- setup agreement/disagreement,
- orderflow and futures proxy awareness,
- data quality and label truth,
- validation discipline,
- execution observability,
- risk/research tooling,
- backlog clarity.

Aggressive research, strict promotion.

## Existing-Data Policy For This Goal

Do not be passive just because future/live data is needed for final validation.

Existing data can and should be used hard for:

- discovery,
- candidate ranking,
- structural explanation,
- rejection of weak ideas,
- comparison against J46-J49,
- promotion-dossier preparation,
- forward-shadow logging design,
- precise future validation triggers.

J46-J49 itself was established through rigorous historical/existing-data research and survived DSR in the current research record. Therefore, if V2b, V3, V4, or any other structurally motivated variant beats J46-J49 on the same available data under stricter or equal methodology, the agent must not dismiss it as useless. It should classify it as a stronger candidate, document why, compare it against J46-J49 and all relevant baselines, test concentration/decay/no-leak/cost sensitivity, and file the next validation or approval path.

But existing-data superiority is not the same thing as live promotion. Same-dataset selected lifts remain discovery unless a separate promotion dossier is explicitly requested and built with the required validation evidence.

## Mandatory Preflight

At the start of the `/goal` session:

1. Run `python scripts\generate_live_state.py`.
2. Read `.context\LIVE_STATE.md`.
3. Read the latest handoff in `.context\02_session_handoffs\`.
4. Read `.context\00_core\quick_reference_card.md`.
5. Read `.context\00_core\research_operating_doctrine.md`.
6. Read `.context\00_core\research_current_state.md`.
7. Read `research\ml_program\MASTER_BACKLOG.md`.
8. Read `research\phase_3_external_feed_validation\PHASE3_DEFERRED_TASKS_AND_NEXT_STEPS_LEDGER_2026-05-02.md`.
9. Inspect recent commits and current git dirt before editing anything.

Do not assume the original Session 54 queue is still open. Some tasks may already be completed by later commits. Use `LIVE_STATE.md`, `research_current_state.md`, git log, and committed artifacts to decide what remains open, what is blocked, and what follow-up questions were created.

## Memory And Compaction Protocol

Before each major task, after any context compaction, and before final closeout:

1. Reread this file.
2. Regenerate and reread `.context\LIVE_STATE.md`.
3. Reread `.context\00_core\research_current_state.md`.
4. Reread the most relevant artifact for the task being resumed.
5. Continue from committed evidence, not from memory.

If the session gets lost, recover with:

```text
Reread .context\05_operations\WEEKEND_RESEARCH_GOAL_PROMPT_2026-05-03.md, regenerate LIVE_STATE, read research_current_state, inspect latest commits and queue state, then continue the highest-priority unblocked research/tooling task.
```

## Hard Constraints

- Research/tooling only unless explicit CEO approval is obtained.
- Preserve NO_PROMOTION_VERDICT in every research report unless the CEO explicitly asks for a promotion dossier.
- Do not change live trading logic, prompts, risk settings, execution behavior, or active safety gates without explicit CEO approval.
- Do not push to remote.
- Do not stage unrelated runtime dirt.
- Do not run broad paid Databento pulls. Use local/cached data. For paid-data ideas, write estimate-only plans unless explicitly approved.
- Do not treat same-dataset selected lifts as validation.
- Separate actual broker R, synthetic/path R, fill/no-fill, internal intent, and counterfactual path labels.
- Do not use post-event features in as-of decision rules.
- Do not invent numbers, files, costs, samples, or validation status.
- Use versioned output files; do not overwrite previous research artifacts.
- If a task is blocked by live data, market hours, paid data, missing owner action, or live-code approval, write the blocker/trigger and continue to the next task.
- Never call a deferred task DONE just because it is blocked; classify it precisely.

## Program Control Loop

1. Build a master queue from:
   - `research\ml_program\MASTER_BACKLOG.md`
   - `.context\00_core\research_current_state.md`
   - `research\phase_3_external_feed_validation\PHASE3_DEFERRED_TASKS_AND_NEXT_STEPS_LEDGER_2026-05-02.md`
   - latest weekend research artifacts
   - any newly opened questions from reports produced during this goal.
2. Normalize each task into:
   - `id`
   - `lane`
   - `status`
   - `blocked_by`
   - `artifact_required`
   - `tests_required`
   - `promotion_allowed`
   - `candidate_strength_vs_j46_j49`
   - `priority`
   - `dependencies`
   - `new_followups_opened`
3. Before executing any lane, produce or update:
   - `research/program_control/MASTER_RESEARCH_QUEUE_STATE_YYYY-MM-DD.md`
   - `research/program_control/MASTER_RESEARCH_QUEUE_STATE_YYYY-MM-DD.json`
4. Execute tasks in priority order within the lane.
5. After each completed task:
   - write a versioned artifact/report,
   - run targeted tests if code/tooling changed,
   - update the queue state,
   - update `.context\00_core\research_current_state.md` if the research map changed materially,
   - update `research\ml_program\MASTER_BACKLOG.md` only when the status change is directly supported by committed artifacts,
   - commit scoped artifacts.
6. If a task opens new follow-ups, add them to the queue immediately with status `OPEN_ADDED`, priority, dependencies, and blocker state.
7. Continue until no unblocked task remains in the current lane, then move to the next lane.
8. At the end, regenerate `.context\LIVE_STATE.md` and produce a final queue report.

## Task Execution Loop

For each task:

1. State the question or hypothesis before looking at new outputs.
2. Identify the evidence files, scripts, data, and prior reports.
3. Check whether the task is already completed, stale, blocked, or still open.
4. Implement the smallest reusable tool/test/report needed.
5. Run targeted tests.
6. Run the full applicable existing-data analysis.
7. Report numbers with denominators, dates, data source, cost assumptions, and label type.
8. Compare against J46-J49 and other relevant baselines when the task produces a strategy/path/filter candidate.
9. Add concentration, cost, decay, no-leak, and label-truth diagnostics when applicable.
10. Add an ambiguity ledger.
11. Add concrete next steps.
12. Commit only scoped files.
13. Update queue state and research current state when needed.

Prefer fewer completed, verified tasks over many shallow partials, but do not stop early while unblocked research/tooling work remains.

## Lane Order

### Lane 0 - Backlog Reconciliation / Control Tower

- Parse `research\ml_program\MASTER_BACKLOG.md` mechanically.
- Reconcile stale statuses from committed artifacts.
- Include at minimum:
  - D-11 / U-11 backfill bias audit
  - D-6 / O-2 NAS100/NDX100 alias triage
  - O-1 `_trade_index.json` staleness refresh
  - O-8 live_evaluations/trade_records enrichment gap audit
  - P2-I pending-limit lifecycle telemetry ticket
- Do not blindly mark implementation tasks DONE if only a spec/triage exists.
- Output backlog delta report and queue state.

### Lane 1 - Methodology Infrastructure

Priority items:

- M-7 training-overlap-weighted SE replacement.
- M-12 effective-N/trial counter.
- M-13 PBO baked into primary evaluation pipelines.
- Methodology diagnostics hardening columns:
  - `methodology_status`
  - `dsr_status`
  - `pbo_status`
  - `effective_n_status`
  - `promotion_p_value_allowed`
  - `not_computable_reason`
  - `latest_artifact_path`

Goal: no future lift claim can bypass DSR/PBO/effective-N discipline.

If implementation touches only research scripts/tooling, proceed. If it touches live trading behavior, file approval ticket and skip.

### Lane 2 - Path Scaling: V2 / V2b / V3 / V4

Priority items:

- Continue V2b forward-status tooling until resolved post-cutoff OB-boundary/J46 pairs exist.
- Do not let missing forward rows block existing-data research. If validation is blocked, continue discovery forensics, tooling, queueing, and forward-shadow design.
- Add/prepare forward-only confluence ledger:
  - FVG/OB both fire
  - FVG-only
  - OB-only
  - neither
  - sequence
  - floor R
  - Composite-vs-best-single
- Continue V2 confluence/disagreement forensics as discovery-only.
- Push V3 aggressively as discovery tooling:
  - POI-bound aware variants
  - lifecycle-aware variants
  - aggregate worst-case risk invariant
  - actual-vs-synthetic label separation
  - right/wrong case taxonomy
  - comparison against J46-J49 and V2/V2b
- If a V3 follow-up naturally becomes a cleaner V4, define V4 explicitly, pre-register the structural mechanism, and test it on existing data with strict discovery labeling.
- Candidate variants that outperform J46-J49 on existing data should be classified and documented, not ignored:
  - `STRONGER_THAN_BASELINE_CANDIDATE`
  - `PROMOTION_DOSSIER_CANDIDATE`
  - `FORWARD_SHADOW_PRIORITY`
- Do not validate or promote V3/V4 until unseen/forward resolved rows and required lifecycle telemetry exist, unless CEO explicitly requests a promotion dossier.

### Lane 3 - Execution / Telemetry / Label Truth

Priority items:

- Pending-limit lifecycle logger isolated tests/spec.
- O-8 trade-record completeness verifier design or research-only implementation.
- L-6/O-6 token-usage logging integration plan; implement only if approved and fail-open.
- L-7/O-7 close-side slippage extension plan/tests; implement only if approved and fail-open.
- `_trade_index.json` rebuild/replacement plan or verifier.

Goal: close ambiguity between broker actual R, internal fills, expired limits, rejected orders, and counterfactual path touches.

### Lane 4 - Orderflow / Proxy / Sierra

Priority items:

- NAS100 `OF-NAS100-DEPTH-ADVERSE-SELECTION-V1` forward diagnostic.
- Add rows until actual-R and winner-side gates improve.
- Keep depth availability/thinness as primary diagnostic; imbalance secondary; MBO pull/add pressure low-confidence.
- USDJPY/6J registered price-transfer follow-up plan before depth pulls.
- GBPJPY synthetic mapping remains blocked until both 6B and 6J legs pass and two-book semantics are solved.
- Sierra active-session parity spec:
  - active `NQM26-CME` delayed depth sample
  - Sierra parser probe
  - matching price alignment
  - Databento parity window
- Optimize/split MBO extractor before larger full-depth runs.
- No broad paid pulls without explicit approval.

### Lane 5 - Data / Backfill / ML Cohort Quality

Priority items:

- Regenerate or locate GBPJPY and US30_cash 2022-2023 mechanical labels.
- Add `source_period` and `mechanical_vs_live_like` feature/source flags before pooling old backfill with live-like rows.
- Audit regime-source asymmetry across old backfill, 2026 backfill, and live regime logs.
- Treat K54/K55 work as shadow/refinement unless cohort expansion or data-quality trigger exists.
- Do not restart K54 v5/v6 on the same current cohort.
- Do not reopen sequence models until n>=5000 regime-balanced labels.

### Lane 6 - Asset / Risk / Vol / Edge Mechanism

Work where research-only and data exists:

- A-section asset specialists as as-of feature feasibility studies.
- R-section risk policy as simulations over DSR-surviving baselines only; do not override safety gates.
- V-section vol-conditioning as symbol-specific or Phase 5 research, not immediate broad sizing.
- E-section edge mechanism validation:
  - stop clusters / latent liquidity
  - OB decay
  - uncorrelated edge discovery

Any result remains discovery unless separately validated.

### Lane 7 - Recurring / Literature / Open Questions

- RR recurring research tasks only when they unblock a ranked lane.
- U open questions should be answered when they directly unblock methodology, data, orderflow, or path-scaling work.
- Literature can generate measurable hypotheses but is not proof.
- Use local evidence first. If external browsing is required, cite primary sources and keep outputs research-only.

## Stop Conditions

Stop only when:

1. all unblocked tasks in the queue are DONE, REJECTED_FAILED, ACCEPTED_CANDIDATE_DISCOVERY, STRONGER_THAN_BASELINE_CANDIDATE, or FILED_WITH_ARTIFACT;
2. every remaining task has a precise blocker and trigger;
3. `research/program_control/MASTER_RESEARCH_QUEUE_STATE_YYYY-MM-DD.md` and `.json` are current;
4. `.context\00_core\research_current_state.md` is current;
5. `.context\LIVE_STATE.md` is regenerated;
6. final summary lists counts by status, lane, and next trigger.

## Final Deliverables

- Updated `research\ml_program\MASTER_BACKLOG.md` only where artifact-supported.
- `research/program_control/MASTER_RESEARCH_QUEUE_STATE_YYYY-MM-DD.md`
- `research/program_control/MASTER_RESEARCH_QUEUE_STATE_YYYY-MM-DD.json`
- Per-task reports under the relevant research directories.
- Updated `.context\00_core\research_current_state.md`.
- Final closeout report with:
  - total backlog count
  - done
  - accepted candidate discovery
  - stronger-than-baseline candidates
  - rejected/failed
  - pending
  - blocked
  - deferred
  - filed for approval
  - new tasks opened
  - lane-by-lane residual ambiguity map
  - recommended next owner approvals/actions.

## Final Closeout

Before final response:

1. Run `python scripts\generate_live_state.py`.
2. Read `.context\LIVE_STATE.md`.
3. Run `git status --short`.
4. Summarize completed tasks, files, commits, tests, numbers, blockers, and remaining queue.
5. State explicitly that all outputs remain NO_PROMOTION_VERDICT unless a separate CEO-requested promotion dossier was created.
6. If `.context\00_core\research_current_state.md` is stale, update and commit it.

