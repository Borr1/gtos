# Session 54 Weekend Goal Handoff - No-Forward-Data Research Queue

**Date:** 2026-05-02  
**Purpose:** Prepare a fresh long-running `/goal` / overnight Codex session for weekend work that does not require active live-market data, new forward rows, or Sierra active-session capture.  
**Scope:** research/tooling only  
**Promotion posture:** `NO_PROMOTION_VERDICT`  
**Current HEAD at handoff prep:** `5d6521e docs: refresh research current state`  

## North Star

The owner goal is incremental improvement across every component and aspect of the system, with the practical end state of making GTOS as powerful, selective, structurally aware, and profitable as possible.

For this handoff, that means:

- mine every useful signal already present in existing data,
- find where current variants win, lose, and conflict,
- engineer better measurement and replay tools,
- turn ambiguities into testable questions,
- propose structural improvements backed by numbers and case evidence,
- avoid pretending a weekend discovery result is live-ready validation.

No research output from this goal may become a promotion, live rule, or spending decision by itself.

## Why This Handoff Exists

The owner wants to use unattended agent time while asleep. Because it is the weekend, the session must avoid tasks blocked on active market data or future live rows. The right workload is long, engineering-heavy research on existing data:

- build missing replay/diagnostic tooling,
- deepen V2/V2b forensics,
- push V3 exploratory replay and structural forensics as far as existing data honestly allows, including structurally motivated variants,
- harden methodology diagnostics,
- mine cached orderflow/Databento artifacts without new broad paid pulls,
- prepare shadow/telemetry specs and isolated loggers where safe,
- write durable artifacts with numbers, ambiguity ledgers, and next steps.

The agent must pursue ambiguities aggressively but keep claims strict.

## About `/goal`

Local verification:

- Installed package: `@openai/codex` version `0.128.0`.
- `codex --help` verifies normal interactive prompt launch plus `codex exec`, `resume`, and `fork`.
- `codex exec --help` verifies non-interactive overnight execution with prompt-from-stdin support.
- `codex features list` shows `goals` as `under development` and currently disabled.
- `codex --enable goals --help` does not expose more slash-command syntax.

Operationally, treat `/goal` as a fresh long-running objective prompt if your UI exposes it. If `/goal` is unavailable, use `codex exec` with the same prompt. The important properties are:

- the objective is explicit,
- preflight is mandatory,
- the task queue is ordered,
- every task has stop conditions,
- every result becomes a file,
- scoped commits are allowed,
- live trading behavior remains untouched.

## Launch Options

Reliable non-interactive overnight form:

```powershell
codex exec -C C:\Users\MSI\Documents\ai-trading-agent -s workspace-write -a never < .context\02_session_handoffs\SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md
```

Interactive form if you want to use the goals UI:

```powershell
codex --enable goals -C C:\Users\MSI\Documents\ai-trading-agent -s workspace-write -a on-request
```

Then paste `/goal` if the UI exposes it, followed by the **Goal Prompt** below. If the UI does not expose `/goal`, paste the prompt as the initial session objective.

Notes:

- `-a never` prevents an overnight run from stopping for approval prompts, but commands that truly require unsandboxed access may fail. The goal instructs the agent to write blockers and continue rather than stall.
- Do not use `--dangerously-bypass-approvals-and-sandbox` for this repo.

## Goal Prompt

```text
Weekend no-forward-data research goal for GTOS.

You are working in C:\Users\MSI\Documents\ai-trading-agent.

Objective:
Use the existing local data, existing replay tooling, existing Databento/cached orderflow artifacts, and current research validation framework to execute as many non-forward-data research/tooling tasks as possible. The work must be aggressive, engineering-heavy, and ambiguity-driven, but every output stays research/tooling only with NO_PROMOTION_VERDICT.

Mandatory preflight:
1. Run `python scripts\generate_live_state.py`.
2. Read `.context\LIVE_STATE.md`.
3. Read `.context\00_core\quick_reference_card.md`.
4. Read `.context\00_core\research_operating_doctrine.md`.
5. Read `.context\00_core\research_current_state.md`.
6. Read `.context\02_session_handoffs\SESSION_54_WEEKEND_GOAL_HANDOFF_2026-05-02.md`.
7. Read `research\phase_3_external_feed_validation\PHASE3_DEFERRED_TASKS_AND_NEXT_STEPS_LEDGER_2026-05-02.md`.

Non-negotiable constraints:
- Research/tooling only.
- Preserve NO_PROMOTION_VERDICT in every report.
- Do not change live trading logic, prompts, risk settings, or execution behavior.
- Do not push to remote.
- Do not stage unrelated runtime dirt.
- Do not run broad paid Databento pulls. Use cached/local data only unless a task explicitly says to create an estimate-only report.
- V3 outcome research is allowed in this weekend goal, but it is exploratory only: pre-register each tested variant before running it, label all selected lifts as discovery, report overfit risk, and preserve NO_PROMOTION_VERDICT.
- Do not treat same-dataset selected lifts as validation.
- Separate synthetic/path labels, actual broker R, and fill/no-fill labels.
- If a task blocks, write a blocker note/report and move to the next task.

Execution protocol:
For each task:
1. State the hypothesis/question before looking at new outputs.
2. Inspect existing scripts/tests/artifacts first.
3. Implement the smallest reusable research tool or test harness needed.
4. Run targeted tests. If tests fail, diagnose/fix/retest.
5. Run the full available existing-data analysis when applicable.
6. Produce a versioned report with numbers, synthesis, ambiguity ledger, opened questions, and next steps.
7. Commit only scoped research/tooling artifacts.
8. After major commits, update `.context\00_core\research_current_state.md` if the research map changes materially.

Start with P0/P1 tasks below. Continue sequentially while time remains. Prefer finishing fewer tasks rigorously over leaving many half-complete.
```

## Workspace Warning

Known runtime/local dirt at handoff prep:

- `.context/LIVE_STATE.md`
- `.gitignore`
- `pipeline_state/m5_refinement.json`
- `shadow_logs/daily_pnl.json`
- `src/components/tick_capture.py`
- untracked `shadow_logs/*` runtime files

Do not stage these unless the task explicitly diagnoses them and the owner has asked for it. Research artifacts should be committed in scoped commits.

## Task Queue Overview

| Priority | Task | Can run now? | Expected time | Main output |
|---:|---|---|---:|---|
| P0 | Confirm no-forward-data inventory and source map | Yes | 15-30m | Short source map / task kickoff note |
| P1-A | V2 confluence/disagreement deep dive | Yes | 2-5h | New full-corpus confluence deep-dive report |
| P1-B | Pre-fill delivery-path capture harness | Yes | 3-6h | Script/tests/report showing coverage and blockers |
| P1-C | V3 full exploratory replay + risk-bank forensics | Yes | 6-12h | Full-data V3 report with numbers, right/wrong taxonomy, and structural next ideas |
| P1-D | V2b rolling status/evaluator hardening | Yes | 1-3h | Status tool/tests/report; still no validation |
| P1-E | Cached NAS100 orderflow feature forensics | Yes, cached only | 2-5h | Feature-stability/concentration report |
| P1-F | Proxy mapping weak-window forensics | Yes, existing artifacts | 1-4h | USDJPY/6J and proxy-priority report |
| P2-G | Phase 3 methodology diagnostics harness | Yes | 3-6h | DSR/PBO/effective-N diagnostics scaffold/report |
| P2-H | 2022-2023 data-quality bias check | Yes | 2-6h | D-11 bias audit report |
| P2-I | Shadow telemetry specs / isolated logger tests | Mostly yes | 2-5h | Specs or isolated tests, no behavior change |
| P2-J | Small backlog ops docs | Yes | 1-3h | D-6 alias doc / O-1 triage note |

## P0 - Source Map And Run Plan

Purpose:

Create a short kickoff note that confirms which local files will be used and which tasks are skipped because they require forward data.

Read:

- `research/phase_3_external_feed_validation/PHASE3_DEFERRED_TASKS_AND_NEXT_STEPS_LEDGER_2026-05-02.md`
- `research/phase_3_external_feed_validation/PHASE3_EXECUTION_UPDATE_2026-05-02.md`
- `research/databento_orderflow_capture_2026-05-02/ORDERFLOW_FORWARD_COLLECTION_PLAN_OF_DATA_15_2026-05-02.md`
- `research/sierrachart_data_source_research_2026-05-02/SIERRACHART_NQM26_DEPTH_PROBE_2026-05-02.md`

Output:

- `research/phase_3_external_feed_validation/WEEKEND_NO_FORWARD_DATA_SOURCE_MAP_2026-05-03.md`

Must include:

- tasks that can run now,
- tasks that are explicitly skipped,
- data files/scripts to use,
- `NO_PROMOTION_VERDICT`.

## P1-A - V2 Confluence / Disagreement Deep Dive

Purpose:

Use existing V2 event logs to push the FVG/OB/Swing/Composite agreement-disagreement study further. This directly addresses the owner's idea that agreement/disagreement may reveal either confirmation, separate setup families, or a delivery-leg plus reversal-leg structure.

Existing anchors:

- `research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V2_STRUCTURE_CONFLUENCE_AUDIT_2026-05-02.md`
- `scripts/analyze_raw_ohlc_path_scaling_v2_confluence.py`
- `tests/test_raw_ohlc_path_scaling_v2_confluence.py`
- V2 event log under `data/external/validation/calendar_macro_bundle_v1/historical_opportunities/raw_ohlc_prequential_replay/path_scaling_v2_structural_levels/`

Questions to answer:

1. Are FVG-only rescue pockets concentrated by symbol/session/side/regime/year?
2. Are OB-after-FVG cases consistently better as tail-preservation floors?
3. Is Composite ever useful under clear arbitration conditions, or is it mostly overlock?
4. Which examples are market-structure coherent, not just numerically lucky?
5. Which forward-only confluence fields should V2b start collecting?

Suggested implementation:

- Add `scripts/analyze_raw_ohlc_path_scaling_v2_confluence_deepdive.py`.
- Add `tests/test_raw_ohlc_path_scaling_v2_confluence_deepdive.py`.
- Produce:
  - `research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V2_CONFLUENCE_DEEPDIVE_2026-05-03.md`
  - matching `.json`

Required diagnostics:

- full corpus and 2026-only slices,
- leave-one-symbol/session/side/year stress,
- bucket concentration caps,
- FVG-first/OB-second sequence stats,
- FVG-only and OB-only exemplar rows,
- Composite arbitration candidates,
- explicit `DISCOVERY_ONLY_NOT_REGISTERED`.

Stop condition:

- If the current event log lacks fields for a sub-question, document the missing field and continue with answerable parts.

## P1-B - Pre-Fill Delivery-Path Capture Harness

Purpose:

Build the missing data layer required to evaluate the owner's delivery-leg plus reversal-leg idea without guessing. Current V2 event logs are post-fill only. This task should not score the strategy yet; it should capture path rows and coverage.

Questions:

1. For historical setups, can we reconstruct the path from setup decision close to pending fill/expiry/cancel using existing M1/M5/M15 data?
2. How often is lower-timeframe pre-fill path available?
3. Which fields are available as-of, and which are missing?
4. Can we identify delivery-direction structures before the POI touch without lookahead?

Suggested implementation:

- Add `scripts/build_raw_ohlc_prefill_delivery_path.py`.
- Add `tests/test_raw_ohlc_prefill_delivery_path.py`.
- Produce:
  - `research/phase_3_external_feed_validation/RAW_OHLC_PREFILL_DELIVERY_PATH_COVERAGE_2026-05-03.md`
  - matching `.json` or sample `.jsonl`

Required fields if available:

- `setup_id`
- `symbol`
- `side`
- `setup_decision_close_utc`
- `pending_limit_created_utc`
- `entry_price`
- `original_poi_type_and_bounds`
- `pre_fill_path_timeframe`
- `pre_fill_path_rows`
- `fill_or_expiry_state`
- `lower_tf_available`
- `as_of_delivery_structure_flags`
- `ambiguity_flags`

Forbidden:

- Do not score a delivery-leg strategy as validated.
- Do not use post-fill information to define pre-fill structures.
- Do not invent missing broker fill states.

## P1-C - V3 Full Exploratory Replay + Risk-Bank Forensics

Purpose:

The owner explicitly wants to see where V3 can go if we chase the ambiguities around it, test it on all currently available data, understand where it is right/wrong, and propose more structural/organized/aware improvements. This task is allowed to run V3 outcome research, but only as research discovery under `NO_PROMOTION_VERDICT`.

This is not a random parameter hunt. The agent must connect V3 behavior to market structure, path state, cost/risk accounting, fill state, symbol/session/regime, and setup-family agreement/disagreement.

The risk-bank invariant remains mandatory:

```text
realized_closed_leg_r + sum(open_leg_stop_if_hit_r) - estimated_remaining_cost_r >= -1.0R
```

Questions:

1. What does current V3 do on every eligible row in existing data, with strict separation between actual broker R, path-synthetic R, and fill/no-fill labels?
2. Where does V3 improve V2/V2b behavior, and where does it degrade it?
3. Are the gains concentrated in a few symbols/sessions/regimes/setup families, or broad?
4. Which right/wrong cases explain the outcome structurally: continuation leg quality, pullback depth, delivery path, liquidity sweep, FVG/OB/swing agreement, time-of-day, spread/cost, or same-bar ambiguity?
5. Can the risk bank reject any reentry that would push aggregate worst-case below `-1.0R`?
6. Are costs charged per leg and per exit?
7. Are unfilled pending reentries excluded from realized R?
8. Are same-bar fill/exit ambiguities surfaced instead of fabricated?
9. What small set of pre-registered V3 variants is logically motivated by the failure taxonomy?
10. Do any variants remain interesting after DSR/PBO/effective-N diagnostics, or are they discovery-only artifacts?

Suggested implementation:

- First inventory all existing V3/V2/V2b scripts, reports, and data inputs. Do not duplicate an existing runner if it can be extended safely.
- Add or extend a research-only helper under `research/phase_3_external_feed_validation/tools/` or `scripts/` for V3 replay and risk-bank accounting.
- Add `tests/test_raw_ohlc_path_scaling_v3_risk_bank.py`.
- Add replay tests that cover label separation and blocked ambiguity states.
- Produce:
  - `research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V3_FULL_EXPLORATORY_REPLAY_2026-05-03.md`
  - matching `.json`
  - optional casebook CSV/JSON with only IDs/timestamps/feature summaries, not fabricated narratives.

Required test scenarios:

- initial leg stopped = exactly `-1R`,
- locked profit creates positive risk bank,
- same-size reentry rejected when risk budget breaks,
- resized reentry accepted when invariant holds,
- multiple reentries cannot silently exceed risk,
- unfilled pending leg does not change realized R,
- per-leg cost accumulation.
- actual broker R is never overwritten by path-synthetic R,
- same-bar fill/stop/target ambiguity is classified as ambiguous or bounded, not guessed,
- selected variant reports include variant count and discovery label.

Pre-registered variant discipline:

- Before running outcomes, write the baseline V3 definition and the variants into the report or a sidecar JSON.
- Keep the variant count small and structurally motivated.
- Suggested variant families:
  1. risk-bank sizing only,
  2. continuation-leg quality gate,
  3. FVG/OB/swing agreement gate,
  4. adverse excursion / failed-delivery reject,
  5. session/regime-aware cap,
  6. cost-aware minimum incremental R gate.
- If the agent invents a new variant after seeing results, label it `post_hoc_discovery` and do not compare it as if it was pre-registered.

Required analysis tables:

- V3 baseline vs V2/V2b: n, mean R, median R, total R, WR, loss tail, fill rate, ambiguity rate.
- By symbol, session, side, setup family, regime, year/quarter, and data source.
- Agreement/disagreement with Swing/FVG/OB-boundary/Composite variants.
- Top positive and negative cohorts by contribution, with effective-N.
- Casebook of representative wins/losses/ambiguous rows.
- Diagnostics: raw p where meaningful, DSR/PBO/effective-N where computable, and `not_computable` with reason where not.

Interpretation requirement:

- The report must answer in plain language: what V3 appears to be trying to capture, when it works, when it breaks, what is probably structural, and what is probably an artifact.
- It must propose next improvements as hypotheses with expected mechanism and required validation data.

Forbidden:

- No generic trailing-stop optimization.
- No blind grid search.
- No promotion verdict.
- No changing live code, prompts, risk config, or execution logic.

## P1-D - V2b Rolling Status / Evaluator Hardening

Purpose:

V2b cannot validate on current data, but its evaluator and reporting can be hardened now so future rows are harvested automatically and unambiguously.

Existing anchors:

- `scripts/evaluate_raw_ohlc_path_scaling_v2b_prospective.py`
- `tests/test_raw_ohlc_path_scaling_v2b_prospective.py`
- `research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V2B_FORWARD_VALIDATION_2026-05-02.md`

Questions:

1. Does the evaluator distinguish:
   - no post-cutoff rows,
   - post-cutoff rows but no wanted rows,
   - wanted rows but no resolved pairs,
   - resolved pairs below sample floor,
   - sample floor reached?
2. Does every report preserve `NO_PROMOTION_VERDICT`?
3. Does it log missing net-R reasons and lower-TF availability?

Suggested implementation:

- Extend the existing evaluator or add `scripts/build_v2b_forward_status_report.py`.
- Extend tests for all blocked states.
- Produce:
  - `research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V2B_ROLLING_STATUS_TOOL_2026-05-03.md`

Stop condition:

- If no new rows exist, the task still succeeds by improving blocked-state clarity and tests.

## P1-E - Cached NAS100 Orderflow Feature Forensics

Purpose:

Use only cached/existing Databento outputs to deepen NAS100 adverse-selection diagnostics without paying for new data.

Existing anchors:

- `research/databento_orderflow_capture_2026-05-02/ORDERFLOW_NAS100_MBO_VALIDATION_SYNTHESIS_2026-05-02.md`
- `research/databento_orderflow_capture_2026-05-02/ORDERFLOW_NAS100_MBO_FEATURE_DIAGNOSTIC_2026-05-02.json`
- `scripts/analyze_orderflow_mbo_nas100_features.py`
- `tests/test_orderflow_mbo_nas100_features.py`

Questions:

1. Are NAS100 MBO/MBP features stable under leave-one-date/event diagnostics?
2. Are candidate/context deltas driven by one date or one time window?
3. Does the apparent thin-depth clue survive label separation?
4. Which exact feature families deserve forward collection fields?
5. Can extractor runtime be optimized or chunked before any future larger run?

Suggested output:

- `research/databento_orderflow_capture_2026-05-02/ORDERFLOW_NAS100_CACHED_FEATURE_FORENSICS_2026-05-03.md`
- matching `.json`

Forbidden:

- No new broad paid Databento pulls.
- No threshold mining.
- No live filter.

## P1-F - Proxy Mapping Weak-Window Forensics

Purpose:

Use existing proxy-mapping artifacts to decide what can be investigated further without spending futures data credits blindly.

Existing anchors:

- `research/databento_orderflow_capture_2026-05-02/USDJPY_6J_INVERSE_RETURN_FOLLOWUP_VALIDATION_2026-05-02.md`
- `research/databento_orderflow_capture_2026-05-02/FUTURES_CFD_PROXY_EXPANSION_AUDIT_2026-05-02.md`
- `scripts/audit_orderflow_proxy_mapping_priorities.py`
- `tests/test_orderflow_proxy_mapping_priorities.py`

Questions:

1. What exactly caused USDJPY/6J's weak `2026-04-27` window at corr `0.825301`?
2. Is the weakness session-specific, roll-specific, timestamp-specific, or basis-specific?
3. Which unresolved symbol should be next if/when data is allowed?
4. Is GBPJPY two-book synthetic mapping conceptually feasible enough to register, or should it stay blocked?

Suggested output:

- `research/databento_orderflow_capture_2026-05-02/ORDERFLOW_PROXY_MAPPING_WEEKEND_FORENSICS_2026-05-03.md`
- matching `.json`

Forbidden:

- Do not activate USDJPY/6J proxy.
- Do not pull GBPJPY futures data without a separate registered mapping protocol.

## P2-G - Phase 3 Methodology Diagnostics Harness

Purpose:

Advance M-7/M-12/M-13 style infrastructure for Phase 3 so future structural/path/orderflow claims carry DSR/PBO/effective-N diagnostics consistently.

Existing anchors:

- `scripts/analyze_truth_layer_effective_n.py`
- `scripts/analyze_truth_layer_posthoc_pbo.py`
- `research/databento_orderflow_capture_2026-05-02/PHASE3_RESEARCH_CLAIM_VERIFICATION_LEDGER_2026-05-02.md`
- `research/ml_program/audit/dsr_diagnostics.json`

Questions:

1. Can a generic diagnostics tool compute or record effective-N/PBO/DSR placeholders for Phase 3 claims?
2. Which current claims are discovery-only and therefore should not get promotion-style p-values?
3. Can the claim ledger be made harder to misuse?

Suggested implementation:

- Add `scripts/analyze_phase3_methodology_diagnostics.py`.
- Add tests.
- Produce:
  - `research/phase_3_external_feed_validation/PHASE3_METHODOLOGY_DIAGNOSTICS_2026-05-03.md`
  - matching `.json`

Important:

- Diagnostics are not promotion.
- If a statistic is not computable, report `not_computable` with reason.

## P2-H - D-11 2022-2023 Data-Quality Bias Check

Purpose:

The master backlog keeps D-11 open. Use existing old backfill and live/mechanical records to test whether 2022-2023 mechanical extraction has bias versus more recent/live-like data.

Questions:

1. Are 2022-2023 rows structurally comparable to 2024-2026 rows?
2. Are symbol coverage gaps creating false confidence?
3. Are mechanical extractor labels comparable across periods?
4. Which old-data cohorts should be downweighted or excluded from future model work?

Suggested output:

- `research/ml_program/audit/D11_2022_2023_BACKFILL_BIAS_CHECK_2026-05-03.md`
- matching `.json`

Stop condition:

- If required source files are missing, write a precise missing-file ledger and replacement plan.

## P2-I - Shadow Telemetry Specs / Isolated Logger Tests

Purpose:

Prepare telemetry that will make future forward validation less ambiguous. This is especially relevant for pending-limit lifecycle, close-side slippage, and token usage.

Existing anchors:

- `research/databento_orderflow_capture_2026-05-02/PENDING_LIMIT_INTENT_TELEMETRY_SPEC_V0_2026-05-02.md`
- `research/operations/l6_l7_integration_ticket_2026-04-29.md`
- `tests/test_slippage_shadow_logger.py`

Allowed:

- improve specs,
- add isolated logger tests,
- create implementation tickets,
- implement pure research-only helpers outside live flow.

Requires caution:

- Do not wire new logger calls into live execution/orchestrator paths unless the change is additive, fail-open, tested, and clearly scoped as no decision impact.

Suggested outputs:

- `research/operations/pending_limit_lifecycle_telemetry_integration_ticket_2026-05-03.md`
- optional isolated tests if a helper is added.

## P2-J - Small Backlog Ops Docs

Purpose:

Use leftover time on small but useful open backlog items.

Candidates:

1. D-6 / O-2: NDX100 -> NAS100 alias documentation across codebase.
2. O-1: `_trade_index.json` frozen-at-2026-04-04 triage note.
3. O-8: `live_evaluations` + `trade_records` enrichment gap audit.

Outputs:

- versioned operation docs under `research/operations/`
- no live code unless the diagnosis is certain and tests are scoped.

## Explicitly Skip During Weekend Goal

Skip these unless the owner later changes the scope:

1. Active Sierra capture: market is closed; needs active session.
2. V2b validation claims: no resolved post-cutoff pairs yet.
3. Broad new Databento pulls: this goal is no-new-data / cached-only.
4. K54 v5/v6 architecture iteration on current cohort.
5. Q2 sequence models: deferred until n `>=5000`.
6. Prompt edits or live decision-logic changes.
7. Any production promotion dossier.

## Commit Discipline

After each finished task:

```powershell
git status --short
git add <only scoped files>
git commit -m "<type>: <short task result>"
```

Never stage unrelated runtime dirt. If a commit fails because of permissions, request escalation exactly for `git add` or `git commit`.

## Final Overnight Closeout

Before final response:

1. Run `python scripts\generate_live_state.py`.
2. Read `.context\LIVE_STATE.md` freshness block.
3. Summarize completed tasks, commits, tests, blockers, and remaining queue.
4. State explicitly that all outputs remain `NO_PROMOTION_VERDICT`.
5. If research_current_state became stale, update and commit it.
