# vNext Production Candidate Failure Repair And EV Prop Governor Goal Prompt

Route id: `vnext_production_candidate_failure_repair_ev_prop_governor_2026_05_25`

This is the controlling prompt for the repair route after the failed vNext production-change route. It is a build, repair, replay, and decision route. It is not a discussion route, not a wrapper route, not another completion-audit route, and not a conservative safety freeze.

The previous route `vnext_production_change_dossier_and_prop_safe_runtime_2026_05_25` produced real code and artifacts, then incorrectly marked a failed production candidate complete. The new route must turn that failure into stronger runtime code, stronger replay semantics, stronger prop-firm governance, stronger acceptance gates, and a truthful production-candidate verdict.

## Instruction Authority

This prompt and the starter message are active instructions, not background reading. They override stale, weaker, narrower, conservative, wrapper-first, top-N, default-off-forever, shadow-only, or self-certifying language in prior prompts, handoffs, route reports, closeout messages, context summaries, and old route state files. System/developer instructions and hard forbidden surfaces still apply.

Do not rely on chat memory. Disk wins. Closeout prose is a claim, not evidence. Every claim must be verified from files, code, config, replay shards, ledgers, tests, verifiers, and git state.

The failed route must not be treated as a valid activation dossier. The failed route is input evidence and a diagnostic base. It is not the completion standard for this route.

Result materialization is mandatory: every repaired behavior must produce exact-R or proxy-R rows, expectancy, source-capture and source completeness status, branch decision, implementation decision, replay effect, and verifier evidence where the fields exist.

## Mandatory Context Use

At start, after any resume, after context compaction, after interruption, after timeout, after approval denial, after any long command, and before marking any stage complete:

1. Run `py -3 scripts/generate_live_state.py`.
2. Read `.context/LIVE_STATE.md`.
3. Read this prompt.
4. Read the starter file:
   `research/science_program_2026_05/04_goal_prompts/VNEXT_PRODUCTION_CANDIDATE_FAILURE_REPAIR_EV_PROP_GOVERNOR_STARTER_2026-05-25.txt`
5. Read:
   - `.context/00_core/goal_session_research_discipline.md`
   - `.context/00_core/research_operating_doctrine.md`
   - `.context/00_core/orchestrator_successor_operating_brief.md`
   - `.context/00_core/orchestrator_methodology_hardening_controls.md`
   - `.context/00_core/parallel_goal_merge_playbook.md`
6. Read the failed-route forensic report:
   `research/science_program_2026_05/06_outcome_testing/vnext_production_change_dossier_and_prop_safe_runtime_2026_05_25/VNEXT_PRODUCTION_CHANGE_FORENSIC_ACCOUNTABILITY_REPORT_DO_NOT_ACTIVATE_2026-05-25.md`
7. Read the failed Stage09/Stage10 artifacts and source:
   - `VNEXT_PRODUCTION_CHANGE_METRICS_SUMMARY_2026-05-25.json`
   - `VNEXT_PRODUCTION_CHANGE_REPLAY_COMPARISON_DOSSIER_2026-05-25.md`
   - `VNEXT_PRODUCTION_CHANGE_COMPLETION_AUDIT_2026-05-25.json`
   - `VNEXT_PRODUCTION_CHANGE_SESSION_STATE_2026-05-25.json`
   - `stage09_shards/*/replay_comparison.jsonl.gz`
   - `build_vnext_production_change_stage09_forward_replay_2026_05_25.py`
   - `test_vnext_production_change_stage09_forward_replay_2026_05_25.py`
   - `build_vnext_production_change_stage10_completion_audit_2026_05_25.py`
   - `test_vnext_production_change_stage10_completion_audit_2026_05_25.py`
8. Read runtime/config/test surfaces before edits:
   - `src/components/gtos_vnext_runtime.py`
   - `src/components/orchestrator.py`
   - `src/components/execution.py`
   - `src/components/primary_analyzer.py`
   - `src/components/ai_supervisor.py`
   - `src/components/permissions.py`
   - `config/agent_config.yaml`
   - `tests/test_gtos_vnext_runtime.py`
   - all focused tests found by `rg "prop_safe|vnext|Stage09|Stage10|ai_policy|ltf_path|mixed|legacy|avoid_blocks|pre_ai|candidate_failure_repair"`

The final completion audit must state how these context files were operationalized, not just that they were opened. It must include instruction-coverage evidence, prompt hash, starter hash, current HEAD, exact artifacts read, exact files changed, exact tests run, and exact remaining actions.

## Verified Failure Facts To Preserve And Recompute

These facts are starting evidence. Recompute from disk before using them in code or final decisions.

- Current failed-route terminal commit: `75a85d244 research: complete vnext production change route`.
- Failed Stage09 candidate rows: `253,234`.
- Failed new production mechanical selected: `10`.
- Failed new production mechanical result: `-4.999959R`, expectancy `-0.4999959197R`, win rate `20%`, profit factor `0.375005100375`.
- Baseline/current shadow selected: `35,983`, performance rows `33,845`, total `+4008.331701256812R`, expectancy `+0.118432019538R`, win rate `44.7658442901%`, profit factor `1.214657122925`.
- Transition counts:
  - baseline false -> new false: `217,247`
  - baseline false -> new true: `4`
  - baseline true -> new false: `35,977`
  - baseline true -> new true: `6`
- All `35,977` baseline-selected dropped rows were dropped by `prop_safe_selector_block_redacted_account_external_overall_10pct_static_budget`.
- Dropped baseline-selected rows summed to about `+4011.831701256811R`.
- The 10 selected trades were all `XAGUSD`, all January 2022, all `OHLC_M1_CSV`, with 8 losers and 2 winners.
- New mechanical nonzero skip reasons:
  - `prop_safe_selector_block_redacted_account_external_overall_10pct_static_budget`: `208,176`
  - `vnext_decision_avoid`: `37,047`
  - `pre_ai_skip_avoid_only`: `7,986`
  - `prop_safe_selector_defer_until_reset_gtos_internal_daily_overlay_budget`: `15`
- Route-decision distribution in the failed new replay:
  - `LEGACY`: `166,779`
  - `FOLLOW`: `41,774`
  - `AVOID`: `37,047`
  - `MIXED`: `7,634`
- Prop overall block contained `166,769` `LEGACY`, `37,215` `FOLLOW`, and `4,192` `MIXED` rows.
- Failed Stage09 modeled one continuous historical account path across 2022-2026 using `ScenarioMetrics.equity`; challenge/account attempts did not reset.
- First overall block occurred on `2022-01-05T09:45:00+00:00`, `XAGUSD`, with remaining overall cushion about `$92.35` and projected cushion about `-$2250.05`.
- Stage09 selected coverage was only `XAGUSD`, not the full universe. Any future coverage report must separate universe coverage, baseline-selected coverage, candidate-selected coverage, and rejected/blocked coverage.
- Stage09 `verify_summary()` accepted metric-key presence, not viability.
- Stage09 test allowed `selected_count=0`, `expectancy_r=None`, and false phase-pass proxies to pass.
- Stage10 instruction coverage was mostly self-certified and did not fail the route when Stage09 output was dead.
- The final audit inconsistency existed because Stage10 wrote the audit before updating route state.
- AI no-paid-call selected `0` because it had no `FOLLOW_WITHOUT_AI` path and paid AI was not called.
- Stage06 LTF path affected scoring/source truth but did not change Stage09 selection; Stage09 `ltf_action` and pending action were `PLACE_LIMIT` for all rows.
- vNext AVOID pressure must be remeasured. The known aggregate was harmful in the failed replay: `37,047` AVOID rows had net positive simulated R if taken. Do not preserve broad AVOID blocks without recomputing selected-only EV and row-level failure anatomy.

## Evidence Class And Hard Boundaries

This is a production-change repair evidence class. It is authorized to edit prompt/config/risk/execution/safety/canary/selector/runtime code, tests, replay builders, route-local artifacts, verifiers, config defaults, and activation-gated runtime surfaces when the edit is tied to source-bound replay evidence and focused tests.

Allowed now:

- parse and audit failed replay shards;
- repair Stage09/Stage10 builders, verifiers, and tests;
- implement runtime/config/test changes;
- build new route-local ledgers, manifests, dossiers, state files, and replay shards;
- run local replay, ablation, segmented prop challenge simulation, EV-policy comparison, no-leak audits, selected-only coverage scans, and focused pytest;
- repair source joins, null fields, parsers, candidate eligibility rules, selected-stream semantics, route semantics, and opportunity-cost metrics;
- use local MT5/OHLC/M1/M5/tick/Sierra/SCID data already available on disk;
- request approvals when a source-safe local action needs permissions.

Forbidden without explicit owner approval:

- live trading;
- broker operation;
- broker/account/order/history/deal/position mutation;
- remote push;
- source-data deletion;
- paid API/vendor calls;
- credential changes;
- final broker-facing activation flips.

These boundaries are rails, not brakes. Do not hide behind owner-gated activation. A dead production candidate is a failed candidate even if activation is off.

## Builder Posture

No conservative brake. No prop-fear. No fake safety. No shallow replay. No verifier theater. No wrapper loops.

Literal impossibility means exactly: every executable read, export, search, parser, repair, proxy, ablation, metric, audit, replay, source join, code hook, test, and review action inside this evidence class has been executed, or the remaining action is forbidden by the hard boundaries above.

Full same-evidence-class pursuit is mandatory. Missing data, null fields, stale hashes, parser gaps, route confusion, replay gaps, selected-stream ambiguity, MT5 export need, Sierra/SCID/tick source need, storage friction, timeout friction, test slowness, and old context conflict are work items. Repair, export, parse, join, derive, proxy, rerun, or implement.

No arbitrary top-N, no top 3/5/10, no number-limited cutoff. Ranked summaries are allowed only after full ledgers preserve all material rows, all nonzero blocker families, all selected rows, all dropped baseline rows, all route-decision classes, all symbol/session/side/time/month partitions, all positive and negative EV families, all repair decisions, and all unresolved same-class gaps.

Speed is not the success standard. Correct source-bound behavior is the standard. Use chunking, checkpoints, single-writer locks, resumable shards, heartbeat files, and exact retry/resume logic so long runs do not waste prior work.

## Route State And Drift Control

Create and maintain:

`research/science_program_2026_05/06_outcome_testing/vnext_production_candidate_failure_repair_ev_prop_governor_2026_05_25/VNEXT_PRODUCTION_CANDIDATE_REPAIR_SESSION_STATE_2026-05-25.json`

The state must contain:

- current stage;
- stage status table;
- active invariant;
- first incomplete invariant;
- exact next action;
- current git HEAD;
- dirty tracked and untracked path summary;
- prompt path and hash;
- starter path and hash;
- forensic report path and hash;
- failed-route artifact hashes used;
- replay shard counts and hashes;
- output artifact paths;
- row/count/hash coverage;
- tests and verifiers run;
- failures found;
- repairs applied;
- active question and repair ledger with every open question from the forensic report, every new question discovered from row evidence, and the exact evidence path that closed or escalated it;
- remaining same-evidence-class actions;
- forbidden-boundary actions not taken;
- context refresh timestamps;
- one-time steers applied;
- completion gate status.

After compaction/resume/interruption/timeout/uncertainty, reload this state, regenerate `LIVE_STATE`, reread this prompt and required doctrine, inspect git status, identify first incomplete invariant, and continue. Do not pick a smaller objective because context was compacted.

## Required Stage Machine

Every stage must end with written artifacts, row counts, code/test references, and a verifier or focused test where code changed. A stage cannot complete from a successful script exit alone.

The named stages are control gates, not a limit. If any stage discovers more repair families, source gaps, policy bugs, replay bugs, data joins, execution semantics, AI semantics, prop-governor cases, or acceptance failures inside this evidence class, create substages or additional artifacts in the route state and pursue them before completion. Do not compress newly discovered work into a summary, parking label, wrapper cleanup, or deferred bucket.

### STAGE_00_INPUT_FREEZE_AND_FAILED_ROUTE_INVALIDATION

Preserve the failed route as evidence and invalidate its activation conclusion.

Required actions:

- verify failed-route artifacts and the forensic report from disk;
- if the forensic report is untracked, preserve it in the scoped repair route input manifest and stage or commit it only as part of a scoped checkpoint;
- write a failure-invalidation ledger and dossier stating that `75a85d244` is not activation-safe;
- prove current runtime activation flags remain broker-safe from config, but do not use that as completion;
- record exact dirty files and avoid staging unrelated dirt.

Outputs:

- `VNEXT_PRODUCTION_CANDIDATE_REPAIR_INPUT_MANIFEST_2026-05-25.json`
- `VNEXT_PRODUCTION_CANDIDATE_REPAIR_FAILED_ROUTE_INVALIDATION_2026-05-25.md`
- `VNEXT_PRODUCTION_CANDIDATE_REPAIR_FAILED_ROUTE_INVALIDATION_LEDGER_2026-05-25.jsonl`

### STAGE_01_FULL_FAILURE_ANATOMY_LEDGER

Build a full row-level failure anatomy from the failed Stage09 shards and old Stage09/10 code.

Required ledgers:

- all selected 10 rows with complete anchors, source paths, route decisions, prop action, risk, R, outcome, and baseline status;
- all nonzero skip reasons by scenario;
- baseline-to-new transition matrix;
- dropped baseline-selected rows with R, terminal outcome, source mode, symbol, session, side, framework, month, route decision, and prop state;
- prop-block rows by route decision, selected baseline status, symbol, session, side, framework, source mode, month, and outcome;
- selected-only coverage, baseline-selected coverage, universe coverage, and blocked coverage as separate tables;
- route-semantics bug ledger proving where `LEGACY` and `MIXED` reached prop budgeting;
- Stage09/Stage10 acceptance gate failure ledger with exact code lines and test lines;
- AVOID pressure ledger with actual source-component/evidence-family join, R if taken, winners blocked, losers avoided, net R, source mode, and partitions;
- LTF/M1/no-fill effect ledger showing whether LTF changed selection, scoring only, entry action, or pending action;
- AI/no-paid-call ledger showing when AI would be required, skipped, blocked, malformed, narrowed, or mechanically unnecessary.

Do not rely on summary tables alone. Read the gzip shards and join to Stage03/Stage04 source artifacts whenever the row-level cause is not fully proven.

### STAGE_02_ACCEPTANCE_GATE_REPAIR

Repair Stage09/Stage10 verifier and tests so catastrophic production candidates cannot pass.

Required failure gates:

- selected count cannot collapse relative to baseline without explicit `production_candidate_failed`;
- selected coverage cannot be universe coverage disguised as selected coverage;
- negative expectancy, PF below 1, phase-pass false, catastrophic missed-winner count, or extreme prop overblocking cannot mark the route complete;
- zero selected, null expectancy, or no-paid-AI zero-output scenarios must fail production viability unless explicitly classified as diagnostic-only;
- Stage10 cannot mark complete while Stage10 is still `in_progress`;
- instruction coverage cannot be hardcoded self-certification;
- Stage10 must fail if Stage09 records `production_candidate_failed`;
- the only allowed complete route states are: `production_candidate_viable`, `production_candidate_failed_with_full_anatomy`, or `redesign_required_with_exact_next_code_path`. It cannot be "complete" as artifact existence.

Write tests that would fail the old behavior.

### STAGE_03_EXECUTABLE_STREAM_AND_ROUTE_SEMANTICS_REPAIR

Repair replay semantics before rerunning the production candidate.

Required fixes:

- define executable stream separately from generated candidate universe;
- preserve current-system behavior for `LEGACY` and `MIXED`;
- do not treat generated `LEGACY` and `MIXED` rows as executable trades unless a rule explicitly and source-bound converts them into executable actions;
- decide whether `MIXED` goes to AI, context, micro-risk, follow/avoid, or no-trade by measurable policy, not default pass-through;
- apply prop budget only to executable candidate streams, not all generated route-local/off-KZ/LEGACY/MIXED rows;
- enforce session/KZ semantics and report off-KZ separately;
- produce selected-only coverage for every scenario.

The replay must include clean scenarios:

- current baseline executable stream;
- baseline plus segmented prop governance;
- vNext route pressure without prop governance;
- vNext executable stream with EV prop governance;
- external-budget-only prop comparison;
- AI/no-paid-call diagnostic;
- LTF entry/no-fill execution-change scenario;
- ablations that isolate vNext AVOID, pre-AI, LTF, prop governor, AI policy, and supervisor.

### STAGE_04_EV_OPTIMIZED_PROP_CHALLENGE_GOVERNOR

Replace passive prop-safe behavior with an EV-optimized prop-challenge governor.

The prop rules are constraints, not the objective. The objective is expected value, payout probability, time-to-payout, challenge survival, opportunity capture, and account scaling.

The governor must compare `ALLOW`, `REDUCE_RISK`, `MICRO_RISK`, `HIGH_QUALITY_ONLY`, `DEFER_UNTIL_RESET`, `ACCOUNT_ABANDON_OR_RESTART`, and `BLOCK` by:

- expected R and risk-adjusted R;
- breach probability;
- trade edge/quality;
- projected daily and overall cushion;
- phase target distance;
- time-to-payout;
- account replacement cost sensitivity;
- payout target sensitivity;
- recovery probability;
- opportunity cost of blocking;
- missed-winner cost and avoided-loser benefit;
- account loss rate;
- expected payout per attempt;
- expected value per account attempt.

Unknown account fee or payout assumptions are not blockers. Run parameterized sensitivity grids and expose the fields. The route must not pretend the numbers are known if they are not.

Near daily or max drawdown, do not auto-block by fear. Compute whether reduced risk, micro-risk, or high-quality-only participation has higher EV than stopping. If even minimum viable risk violates hard prop rules, model account abandon/restart economics as a scenario, not as a silent permanent block.

Segment replay into real challenge/account attempts. Do not use one continuous 2022-2026 account path. Simulate many attempts with GMT+3 daily reset, Phase 1 8 percent target, Phase 2 5 percent target, static 10 percent max loss, 5 percent daily loss, and configurable internal overlay. Record pass/fail, time to pass/fail, trades per attempt, payout proxy, account loss rate, and EV by policy.

### STAGE_05_VNEXT_AVOID_AND_PRE_AI_REPAIR

Do not preserve broad AVOID pressure just because it came from converted intelligence. Measure it.

Required:

- recompute every AVOID family and source component by net simulated R if taken, winners blocked, losers avoided, source mode, symbol, session, side, framework, month, route family, and evidence family;
- identify which AVOID families are useful, harmful, mixed, stale, duplicated, context-only, or require AI resolution;
- demote harmful broad AVOID families to context or redesign unless a partition proves value;
- preserve useful AVOID families as bounded avoid filters with source-bound scope;
- repair `__NULL__` or missing-source-component AVOID attribution by joining Stage03/Stage04/runtime artifacts or exact row-level proof;
- ensure pre-AI skip logic blocks only when it improves EV or prevents known failure, not as broad no-trade gravity;
- test config and runtime behavior for every changed avoid/pre-AI policy.

### STAGE_06_LTF_ENTRY_NOFILL_EXECUTION_REPAIR

The repaired system must not be blind for a full M15 candle when M1/M5/tick/Sierra path can improve entry and no-fill behavior.

Required:

- prove how current runtime uses M15, M1, M5, tick, and Sierra/SCID path sources;
- separate path truth scoring from actual entry decision behavior;
- convert LTF intelligence into execution-stage decisions where evidence supports it: market entry now, adjusted limit, pending monitor, cancel/reprice, avoid no-fill, or wait;
- test that LTF action can change the candidate execution path, not merely produce scoring after the decision;
- measure M15-vs-LTF disagreement by selected stream, not only universe rows;
- preserve no-leak: decisions use as-of path state only; outcome labels join after decision for scoring.

### STAGE_07_AI_POLICY_AND_SUPERVISOR_REPAIR

AI is not the brute-force replay engine and not a passive blocker.

Required:

- define when mechanical FOLLOW can trade without AI;
- define when MIXED or ambiguity calls AI;
- define when AI must be skipped because mechanical avoid/no edge is strong;
- define when a bounded supervisor repairs malformed format versus demotes to no-trade;
- prevent `new_ai_policy_no_paid_call` from becoming a zero-trade dead scenario unless classified diagnostic-only;
- generate prompt packets, schema checks, parser tests, malformed response tests, cache/hash logic, and no-paid-call replay diagnostics;
- do not run paid API/vendor calls without explicit owner approval.

### STAGE_08_REPAIRED_FORWARD_ONLY_REPLAY

Run the repaired as-of replay over the full available candidate universe and executable streams. A checkpoint shard is not completion; the full run remains first incomplete invariant until it has finished and passed verification.

Required metrics for every scenario:

- candidate universe rows;
- executable-stream rows;
- selected rows;
- performance rows;
- total R;
- risk-adjusted R;
- exact-R/proxy-R/source status;
- expectancy;
- win rate;
- profit factor;
- drawdown;
- max loss streak;
- trade frequency by month;
- symbol/session/side/framework/source-mode/timeframe/month coverage;
- selected-only coverage;
- missed winners;
- avoided losers;
- accepted losers;
- blocked winners;
- prop pass/fail rate;
- expected payout per attempt;
- account loss rate;
- time-to-pass/fail;
- opportunity cost of each block/defer/reduce decision;
- no-fill avoided;
- stop-first avoided;
- AI calls required, skipped, saved, malformed, repaired, and demoted;
- LTF changed-entry outcomes;
- off-KZ treatment.

Run ablations that isolate each layer. Do not let one huge combined result hide the failing layer.

### STAGE_09_PRODUCTION_CANDIDATE_DECISION_DOSSIER

Write a truthful decision dossier. The route ends in one of these states:

- `production_candidate_viable_after_repair`
- `production_candidate_failed_with_full_failure_anatomy`
- `redesign_required_with_exact_repair_backlog`

The dossier must not use artifact existence as success. It must answer:

- what runtime/system behavior changed;
- what code/config/tests changed;
- what research/replay intelligence was consumed;
- what markets, symbols, timeframes, sessions, sides, strategy families, entries, exits, filters, gates, risk rules, no-fill logic, and AI paths are covered;
- what still fails and why;
- what was made less conservative and why;
- what was made stricter and why;
- what was killed, demoted, redesigned, or promoted;
- whether expanded-market intelligence is truly executable or only preserved;
- whether default-off behavior has a concrete activation/replay/shadow path;
- exact next action before any broker-facing activation.

## Required Output Artifacts

Use this route directory:

`research/science_program_2026_05/06_outcome_testing/vnext_production_candidate_failure_repair_ev_prop_governor_2026_05_25/`

Minimum outputs are a floor, not a ceiling. Add every additional ledger, dossier, manifest, shard, verifier, and focused test needed to close the full evidence class.

- `VNEXT_PRODUCTION_CANDIDATE_REPAIR_SESSION_STATE_2026-05-25.json`
- `VNEXT_PRODUCTION_CANDIDATE_REPAIR_INPUT_MANIFEST_2026-05-25.json`
- `VNEXT_PRODUCTION_CANDIDATE_REPAIR_FAILED_ROUTE_INVALIDATION_2026-05-25.md`
- `VNEXT_PRODUCTION_CANDIDATE_REPAIR_FAILURE_ANATOMY_LEDGER_2026-05-25.jsonl`
- `VNEXT_PRODUCTION_CANDIDATE_REPAIR_SELECTED_ROWS_LEDGER_2026-05-25.jsonl`
- `VNEXT_PRODUCTION_CANDIDATE_REPAIR_DROPPED_BASELINE_LEDGER_2026-05-25.jsonl`
- `VNEXT_PRODUCTION_CANDIDATE_REPAIR_AVOID_EV_LEDGER_2026-05-25.jsonl`
- `VNEXT_PRODUCTION_CANDIDATE_REPAIR_ROUTE_SEMANTICS_LEDGER_2026-05-25.jsonl`
- `VNEXT_PRODUCTION_CANDIDATE_REPAIR_PROP_ATTEMPT_LEDGER_2026-05-25.jsonl`
- `VNEXT_PRODUCTION_CANDIDATE_REPAIR_PROP_POLICY_COMPARISON_SUMMARY_2026-05-25.json`
- `VNEXT_PRODUCTION_CANDIDATE_REPAIR_LTF_ENTRY_EFFECT_LEDGER_2026-05-25.jsonl`
- `VNEXT_PRODUCTION_CANDIDATE_REPAIR_AI_POLICY_SUPERVISOR_LEDGER_2026-05-25.jsonl`
- `VNEXT_PRODUCTION_CANDIDATE_REPAIR_REPLAY_METRICS_SUMMARY_2026-05-25.json`
- `VNEXT_PRODUCTION_CANDIDATE_REPAIR_LAYER_ABLATION_SUMMARY_2026-05-25.json`
- `VNEXT_PRODUCTION_CANDIDATE_REPAIR_COMPLETION_AUDIT_2026-05-25.json`
- `VNEXT_PRODUCTION_CANDIDATE_REPAIR_DECISION_DOSSIER_2026-05-25.md`
- builders, verifiers, and focused tests for every material artifact and code change.

## Verification Requirements

Run focused tests and verifiers after every material code/config/replay repair. Required categories:

- `py_compile` or syntax parse for changed Python;
- focused pytest for Stage09/Stage10 verifier repairs;
- focused pytest for runtime prop governor behavior;
- focused pytest for route semantics and selected-only coverage;
- focused pytest for vNext AVOID/pre-AI policy changes;
- focused pytest for LTF entry/no-fill behavior;
- focused pytest for AI policy/supervisor behavior;
- route verifier for every builder output;
- full repaired replay check;
- `git diff --check`;
- `git diff --cached --check` before commits.

If a combined test command times out, split by named test boundary and run every named shard. Do not drop coverage because a combined command is slow. Do not rerun the same expensive ledger build repeatedly when a single process can share it. Add cache/checkpoint support if repeated rebuilds waste time.

## Commit Discipline

Commit scoped checkpoints. Do not stage unrelated dirt. Do not stage `.context/LIVE_STATE.md` unless the owner explicitly asks for context refresh. Do not stage old full-replay metadata churn unless the route intentionally repairs it. Do not push.

Use scoped commit messages. Include `Co-Authored-By: Codex GPT-5 <redacted@example.com>` when committing.

## Completion Standard

The route is complete only when:

- every stage is complete from disk evidence;
- every changed code/config path has focused tests;
- every replay builder has a verifier;
- every large output has count/hash/schema coverage;
- every nonzero skip/block/defer reason has row counts and EV/opportunity-cost anatomy;
- selected-only coverage is separated from universe coverage;
- prop replay uses segmented challenge/account attempts, not one continuous historical account;
- route semantics no longer auto-select generated `LEGACY`/`MIXED` rows by accident;
- AVOID/pre-AI decisions are repaired, bounded, or classified failed with row-level evidence;
- LTF/M1 path intelligence either changes execution behavior where justified or is explicitly measured as not ready with exact reason;
- AI/no-paid-call logic cannot become a silent zero-trade route unless diagnostic-only;
- Stage09/Stage10 failure gates reject the old catastrophic output;
- final replay produces either a viable candidate or a failed/redesign verdict with full anatomy;
- completion audit is evidence-based, not self-certified;
- no same-evidence-class repair remains feasible.

If the repaired system still fails, say it failed and preserve the failure anatomy. A failed system with exact repair intelligence is acceptable. A dead system marked complete is not.
