# Forward Capture And Intelligence Infrastructure Goal Prompt - 2026-05-04

Status: owner-requested next big goal prompt
Scope: research/tooling plus additive fail-open shadow infrastructure
Promotion posture: `NO_PROMOTION_VERDICT`
Live-trading behavior changes: prohibited

This prompt continues from:

- `research/program_control/EXPANDED_OOS_FULL_UNBLOCKING_OWNER_DEEP_DIVE_REPORT_2026-05-04.md`
- `research/program_control/EXPANDED_OOS_FULL_UNBLOCKING_FINAL_SYNTHESIS_2026-05-04.md`
- `.context/00_core/research_current_state.md`
- `.context/00_core/research_operating_doctrine.md`

## Purpose

The expanded-OOS full-unblocking pass proved that GTOS is no longer mainly blocked by idea generation. It is blocked by forward truth capture, label quality, source parity, lifecycle-aware replay, and enough no-leak live/forward evidence to turn promising research branches into valid promotion candidates later.

The owner has read and acknowledged the deep-dive report and now wants the next goal session to make the infrastructure ready so the research does not sit unused. This means extracting every actionable item from the deep dive and pursuing all of them: code, shadow logging, forward capture, Databento/Sierra usage, source-resolution work, validation ledgers, monitoring hooks, and any currently possible research.

Priority is not a reason to skip work. Execution order may be dependency-aware, but the goal is exhaustive: every item should end as `DONE`, `IMPLEMENTED_SHADOW_ONLY`, `RESEARCH_ARTIFACT_DONE`, `WAITING_FOR_FORWARD_ROWS_WITH_COLLECTOR_ACTIVE`, or `BLOCKED_WITH_EVIDENCE_AND_TRIGGER`.

## Copy-Paste Goal Prompt

```text
Forward capture and intelligence infrastructure goal for GTOS.

You are working in C:\Users\MSI\Documents\ai-trading-agent.

Objective:
Turn the expanded-OOS full-unblocking deep-dive into complete forward-capture and research-infrastructure readiness. Go through the full deep-dive report, final synthesis, current research state, and related open questions. Extract every opportunity, unresolved question, data constraint, missing logger, missing replay label, missing source-alignment step, Databento/Sierra forward-capture opportunity, and validation blocker. Then implement or produce the research/tooling artifacts needed so GTOS starts capturing the missing evidence in live/forward operation.

This is not a strategy-promotion session. It is an infrastructure-readiness and intelligence-compounding session. The output should make the next active monitoring session able to verify whether all shadow logs, forward data captures, Databento/Sierra captures, label joins, and validation ledgers are running and filling correctly.

Mandatory preflight:
1. Run `python scripts\generate_live_state.py`.
2. Read `.context\LIVE_STATE.md`.
3. Read the latest handoff in `.context\02_session_handoffs\`.
4. Read `.context\00_core\quick_reference_card.md`.
5. Read `.context\00_core\research_operating_doctrine.md`.
6. Read `.context\00_core\research_current_state.md`.
7. Read `research/program_control/EXPANDED_OOS_FULL_UNBLOCKING_OWNER_DEEP_DIVE_REPORT_2026-05-04.md`.
8. Read `research/program_control/EXPANDED_OOS_FULL_UNBLOCKING_FINAL_SYNTHESIS_2026-05-04.md`.
9. Read `research/program_control/EXPANDED_OOS_FIRST_WAVE_FAMILY_STATUS_MATRIX_2026-05-04.md`.
10. Read `research/program_control/EXPANDED_OOS_SIERRA_DEPTH_SAMPLING_AUDIT_SYNTHESIS_2026-05-04.md`.
11. Read `research/operations/pending_limit_lifecycle_telemetry_integration_ticket_2026-05-03.md`.
12. Read `research/program_control/AI_AND_ORDERFLOW_EXECUTION_DISCUSSION_CONTEXT_2026-05-03.md`.
13. Read the Databento/orderflow forward collection artifacts under `research/databento_orderflow_capture_2026-05-02/`, especially files whose names contain `FORWARD_COLLECTION`, `EVENT_WINDOW_MANIFEST`, `FETCH_PLAN`, `ACTUAL_OUTCOME_COVERAGE`, `NAS100`, `MBO`, or `MBP10`.
14. Inspect current git status and current tracked/untracked dirt before editing. Do not stage unrelated runtime dirt.

Core owner direction:
- The owner wants every action item from the deep-dive addressed, not only the highest-priority subset.
- The owner approves research/tooling work and additive fail-open shadow logging that does not alter live trading decisions.
- The owner wants Databento API usage to be part of forward data capture where it is useful, targeted, declared, and cost-logged.
- The owner wants SierraChart data/depth capture utilized where it can compound system intelligence.
- The owner wants all unresolved questions converted into collectors, registries, tests, research artifacts, or precise blockers.
- The owner wants the infrastructure ready for a later active monitoring session that checks freshness, row counts, coverage, failures, and whether the evidence is accumulating.

Hard constraints:
- Preserve `NO_PROMOTION_VERDICT` in every report from this goal.
- Do not change live trading logic, prompt behavior, risk sizing, execution decisions, safety gates, or order-placement behavior.
- Additive fail-open shadow logging is allowed when it cannot change decisions and has tests.
- If touching `src/components/execution.py`, `src/components/orchestrator.py`, or any live-flow file, keep changes strictly observational: no return-value decisions, no branch decisions, no mutation of trading objects except existing behavior, no extra API/AI call in the live path.
- Do not run Component 3B debate.
- Do not run broad AI/LLM replay.
- Do not promote any strategy, filter, exit, risk, or AI change.
- Do not collapse evidence classes. Keep actual broker R, internal lifecycle labels, synthetic/path labels, futures proxy labels, source-transfer diagnostics, and control/context labels separate.
- Do not use same-slice tuning as validation.
- Do not push to remote.

Allowed work:
- New research-only scripts.
- New tests.
- New fail-open shadow loggers.
- New append-only JSONL logs under `shadow_logs/`.
- New research manifests, registries, ledgers, and runbooks.
- New source indices and cost ledgers.
- Targeted Databento fetch/cache wrappers and manifests for forward/event windows.
- Sierra `.scid` and `.depth` parser, watcher, parity, and source-status improvements.
- MT5 read-only export/probe scripts.
- Verification/monitoring scripts that inspect local logs and data freshness.
- Context updates and operations prompts.

Definition of done:
Every item in this prompt must end in one of these states:
- `DONE`: implemented and verified.
- `IMPLEMENTED_SHADOW_ONLY`: additive fail-open telemetry/logging exists, tests pass, no live decision impact.
- `RESEARCH_ARTIFACT_DONE`: a report/spec/registry/runbook exists with exact next trigger.
- `WAITING_FOR_FORWARD_ROWS_WITH_COLLECTOR_ACTIVE`: collector/logging exists and only future events are missing.
- `BLOCKED_WITH_EVIDENCE_AND_TRIGGER`: blocker is proven by file/command/source evidence and the exact unblock trigger is written.

Do not leave any item as vague `pending`, `later`, `needs research`, or `needs data`.

Execution protocol:
1. Build a live action ledger before code edits. The ledger should enumerate all tracks below, current status, intended files, tests, and blocker triggers.
2. Work track by track. Dependency-aware order is fine, but do not drop lower-ranked tracks.
3. For each code/tooling item, inspect existing local scripts/tests first and reuse patterns.
4. Add tests before or with new tooling.
5. Run targeted tests for each changed area.
6. Write versioned research/operations artifacts for every major result.
7. Commit scoped changes periodically with `Co-Authored-By: Codex GPT-5 <redacted@example.com>`.
8. After material research-state changes, update `.context\00_core\research_current_state.md`.
9. Before final closeout, run `python scripts\generate_live_state.py` and inspect the freshness block.

Track A - Master action ledger and schema discipline:
1. Create a versioned action ledger under `research/program_control/` for this goal.
2. Include every action item from the deep-dive sections 16 through 29, plus the final synthesis remaining triggers.
3. Each ledger row must include: action id, source report section, system aspect, exact objective, implementation target, expected output path, tests, decision-impact risk, evidence class, completion status, and blocker trigger.
4. Define canonical evidence labels: `BROKER_ACTUAL_R`, `INTERNAL_LIMIT_LIFECYCLE`, `SYNTHETIC_PATH_R`, `FUTURES_PROXY_TRANSFER`, `SAME_MARKET_SOURCE_TRANSFER`, `CROSS_INSTRUMENT_CONTEXT`, `FORWARD_SHADOW`, `DISCOVERY_ONLY`, `CONTROL_ONLY`.
5. Define common metadata fields for forward logs: `schema_version`, `created_at_utc`, `symbol`, `broker_symbol`, `source_symbol`, `session`, `kill_zone`, `side`, `regime`, `candidate_id`, `trade_id`, `evidence_class`, `decision_time_utc`, `asof_cutoff_utc`, `source_file`, `source_hash`, `no_leak_status`, and `promotion_verdict`.

Track B - Pending-limit lifecycle telemetry:
1. Implement or fully prepare the pending-limit lifecycle logger described in `research/operations/pending_limit_lifecycle_telemetry_integration_ticket_2026-05-03.md`.
2. Required output log: `shadow_logs/pending_limit_lifecycle.jsonl` or a clearly versioned equivalent.
3. Required states: `still_pending_no_trigger`, `expired_48h`, `triggered_tick_missing_retry`, `cancelled_wrong_side`, `cancelled_sl_too_close`, `order_send_success_filled`, `order_send_failed_retry`, `manual_or_system_cancelled`.
4. Required fields: pending-created time, ticket if known, fill time if known, expiry/cancel reason, broker fill state, entry price, stop, TP, spread, slippage if available, actual R if available, synthetic/path R separately, fill/no-fill label, candle OHLC used for the check, tick bid/ask if triggered, and source branch.
5. Add isolated unit tests for logger append, fail-open disk failure, schema fields, and every lifecycle state.
6. If wiring into live-flow files is safe and additive, wire it fail-open with tests. If runtime/approval boundary blocks wire-in, create a precise integration patch plan and leave status `RESEARCH_ARTIFACT_DONE`, not vague pending.
7. Preserve all existing execution behavior.

Track C - Actual broker-R and account/deal truth:
1. Audit current trade records and account/deal artifacts for actual broker-R availability.
2. Create or update a broker-R reconciliation artifact that separates MT5/account-history truth from internal synthetic/path R.
3. Add a join plan or script that can map lifecycle rows, slippage rows, trade records, and MT5 deal/position history by ticket/trade id/time.
4. Produce a coverage report: count of rows with `BROKER_ACTUAL_R`, rows with internal fill only, rows with synthetic/path only, rows unrecoverable.
5. Do not infer broker actual R from path simulation.
6. If MT5/account history access is unavailable, write the exact probe command, failure evidence, and next trigger.

Track D - V2b forward pair collector:
1. Build or update a forward collector for every qualifying post-cutoff setup.
2. Required paired labels: OB-boundary outcome, J46 baseline outcome, fixed-R comparator, FVG comparator.
3. Required context: symbol, session, side, regime, lower-timeframe availability, same-bar ambiguity state, cost sensitivity, source period, path label status, actual/synthetic label lane.
4. Required output: append-only forward pair JSONL plus weekly/rolling summary report.
5. If there are no resolved rows yet, status should be `WAITING_FOR_FORWARD_ROWS_WITH_COLLECTOR_ACTIVE`.
6. Include sample-floor tracking toward the required resolved OB-boundary/J46 pair count.

Track E - V3 and pre-fill delivery-path capture:
1. Do not validate V3 from same-dataset results.
2. Capture pre-fill delivery path before scoring delivery-leg plus reversal-leg or V3 reentry.
3. Required fields: structural setup id, original POI bounds, entry arming time, pre-fill candles/ticks, delivery leg direction, reversal leg timing, whether fill happened, fill delay, cancel/expiry/abort reason, lower-timeframe path ordering, FVG/OB/swing state at arm/fill/cancel.
4. Add a pre-fill delivery-path logger or research-only extractor, depending on what the current code can support safely.
5. Create a V3 readiness report that states which lifecycle/pre-fill fields are now captured and which remain blocked.

Track F - FVG/OB confluence and disagreement ledger:
1. Build a forward-only confluence ledger for structural opportunities.
2. Required buckets: both FVG and OB fire, FVG-only, OB-only, neither, OB-after-FVG, FVG-after-OB, Composite overlock, disagreement, no POI.
3. Include side, session, regime, touch count, POI quality, lower-timeframe availability, and candidate outcome lane.
4. Use the ledger for future research only. No filter promotion.
5. Add validation that every row is as-of decision time and no post-outcome fields leak into decision-time fields.

Track G - NAS100/NQ orderflow forward diagnostic:
1. Treat NAS100/NQ as the strongest orderflow forward branch because NQ depth parity was exact in tested windows.
2. Build or update the forward orderflow capture plan so every relevant NAS100 candidate/context window can request or join:
   - Databento MBP-10,
   - Databento trades,
   - Databento MBO only for targeted declared windows,
   - Sierra full-depth `.depth` where available,
   - MT5 tick features,
   - actual broker outcome labels.
3. Required output: event-window manifest, fetch-plan/cost ledger, feature rows, outcome join, coverage report, and rolling readiness report.
4. Target floors to track: actual broker-R >=20 and MBP10 candidate rows >=30 before considering any filter dossier.
5. Keep orderflow use as diagnostic, timing, abort, and exit research. Do not create a live binary filter.
6. Explicitly test whether thin-depth/adverse-selection behavior is one-date concentrated.

Track H - Databento forward capture infrastructure:
1. Databento API usage is approved for targeted forward capture and parity/event windows when predeclared and cost-capped.
2. Create a durable Databento forward capture runbook under `research/databento_orderflow_capture_2026-05-02/` or `research/program_control/`.
3. Create or update a manifest format that records dataset, schema, raw symbol, stype, start/end UTC, reason, expected fields, expected cost, actual cost if known, cache path, and no-leak usage policy.
4. Build or update scripts so a future active session can request:
   - candidate-centered MBP10 windows,
   - candidate-centered trades windows,
   - targeted MBO windows for NAS100/NQ,
   - parity windows against Sierra `.depth`,
   - context windows around non-trade candidate rejects.
5. Use cached data first; fetch only declared windows.
6. Save raw/cached outputs and source indexes.
7. If API/network/sandbox access blocks the fetch, write the exact approval request/command and leave the manifest ready.

Track I - Sierra forward capture infrastructure:
1. Treat Sierra as active/recent full-depth capture infrastructure, not a full historical MBO replacement.
2. Build or update a Sierra capture inventory script/runbook that checks `.scid` and `.depth` freshness, size, row count, symbol coverage, and active-session nonblank status.
3. Cover first-wave/core futures symbols: NQ/MNQ, YM/MYM, GC/MGC, SI/SIL, 6J, 6B, 6E, ES/MES, CL, ZN, VXM/VXMM where files exist.
4. Add a monitoring/check artifact that reports stale/missing `.depth` files, sparse `.scid` warnings, and likely market-closed samples.
5. Keep chartbook/operator steps explicit where Codex cannot force Sierra to open/download a symbol.
6. Produce a Sierra-forward-capture readiness report with exact symbols ready, caution, blocked, and operator-triggered.

Track J - 6B sampling alignment:
1. Implement common-second/declarative sampling alignment for Sierra 6B vs cached Databento comparison.
2. Rerun 6B parity with the new policy.
3. Report all-seconds deltas and common-second deltas separately.
4. If 6B becomes clean enough, classify GBPUSD/6B as usable diagnostic branch with explicit proxy caveat.
5. If not, write the remaining mismatch fields and trigger.

Track K - SI source-definition investigation:
1. Resolve or narrow the SI blocker before using SI depth in replay synthesis.
2. Investigate continuous-contract mapping, `SIM` vs `SIL`, Databento `SI.v.0`, standard vs micro silver, book definition, roll/date alignment, and price scale.
3. Compare Sierra and Databento on the same timestamp windows after source definition is fixed or narrowed.
4. Until resolved, keep SI/XAGUSD depth status `BLOCKED_SOURCE_OR_DEPTH_DEFINITION`.
5. Produce a source-definition report with `use`, `do_not_use`, or `blocked_with_trigger`.

Track L - GC/XAUUSD same-market and futures-proxy extension:
1. Extend the XAUUSD same-market structural source-transfer diagnostic honestly.
2. Pre-register frozen slices before opening outcomes.
3. Preserve evidence class: same-market source transfer for `XAUUSD.scid`, futures proxy transfer for GC/MGC.
4. Target at least `n>=30` resolved rows before any validation-strength discussion.
5. Include cost/slippage assumptions and lower-timeframe fill truth.
6. Keep `NO_PROMOTION_VERDICT`.

Track M - EURUSD/6E and ES/MES pre-registration:
1. Do not open outcomes until each family has a registered question.
2. For EURUSD/6E, define cohort, session, side, comparator, evidence class, label policy, source mapping, and reserved holdout.
3. For ES/MES, decide whether the question is direct expansion, equity-index control, NAS/US30 context, or separate strategy family. Register before outcomes.
4. Create registry artifacts even if no replay is run in this goal.
5. If a registered cohort can be run with existing converted rows, run it with evidence-class separation.

Track N - CL/ZN/VIX context and control questions:
1. Do not use CL/ZN/VIX as direct strategy validation sources.
2. Register named context questions before using them:
   - VIX/VXM volatility-regime filter/context,
   - ZN rates/macro stress context,
   - CL liquidity/macro stress context.
3. Define as-of timestamp convention and no-leak join rules.
4. Build a forward context ledger that can later join to candidate decisions without outcome leakage.
5. Produce a control/context readiness report.

Track O - Lower-timeframe path and same-bar ambiguity:
1. Treat the XAGUSD/SI M15 false positive as proof that M15-only optimism is unsafe.
2. Ensure future path/replay reports track lower-timeframe availability and same-bar ambiguity.
3. Build or update an ambiguity classifier for: no LTF data, same-bar TP/SL ambiguity, no fill, fill-before-invalidation, invalidation-before-fill, TP-before-SL, SL-before-TP, unresolved.
4. Add tests on synthetic candles where possible.
5. Ensure all path-management reports surface ambiguity rates.

Track P - Cost, slippage, spread, and exit accounting:
1. Audit current slippage and time-in-trade shadow loggers.
2. Ensure entry spread, entry slippage, close-side spread/cost, and time-in-trade fields are available or have integration tickets.
3. Link cost/slippage fields to V2b/V3/path-management outcomes.
4. Build a report showing how many current/future labels have usable cost data.
5. Keep partial-close, trailing, BE, and exit variants research-only until actual fill/cost labels exist.

Track Q - AI decision-layer shadow intelligence:
1. Do not alter PrimaryAnalyzer behavior or prompts.
2. Build or specify shadow-only paired labels that help evaluate the AI layer against mechanical/replay outcomes later.
3. Record what no-leak structured context would have been available at decision time: POI quality, confluence state, regime, orderflow availability, lifecycle state, prior similar outcomes if allowed by current memory policy.
4. Identify whether existing `ai_tools` scaffolding can support future grounded structured tools without live behavior changes.
5. Produce an AI-layer readiness note: current score, missing evidence, and exact shadow labels needed.

Track R - Data/history constraints and source map maintenance:
1. Update the source map with current MT5, Sierra, Databento, cached orderflow, and shadow-log coverage.
2. Track pre-2024 tick/LOB blocker, pre-2022 all-symbol OHLCV blocker, older MT5 tick retention limits, and alternate provider/archive candidates.
3. Preserve source-period flags for old labels and D-11 supplements.
4. Build or update a broker symbol map from MT5 where possible.
5. Record which constraints Sierra/Databento solve and which they cannot solve.

Track S - Validation and claim-ledger automation:
1. Build or update a claim ledger for forward-capture research.
2. Every claim row must include evidence class, opened slice, sample size, actual-vs-synthetic label lane, cost model, DSR/PBO/effective-N if computable, and `not_computable` reason if not.
3. Add opened/burned/reserved slice ledger updates for every new replay or Databento/Sierra opened window.
4. Add promotion-dossier template or checklist for future use, but do not fill one as promotable.
5. Add focused tests for ledger schema if tooling is created.

Track T - Monitoring-session readiness:
1. Create a monitoring prompt/runbook for the next active monitoring session.
2. The monitoring runbook must check:
   - pending-limit lifecycle log freshness and schema,
   - V2b forward pair rows and resolved-pair counts,
   - NAS100/NQ orderflow manifest/fetch/feature/outcome coverage,
   - Databento cost ledger and cache paths,
   - Sierra `.depth` and `.scid` freshness,
   - 6B/SI/GC source-status changes,
   - FVG/OB confluence ledger row counts,
   - pre-fill delivery-path capture rows,
   - cost/slippage fields,
   - claim ledger status,
   - any live log errors or stale captures.
3. Create or update a verification script if practical. If not practical, create a command checklist with exact `rg`, `python`, and path checks.

Track U - Final synthesis:
1. Produce a final infrastructure-readiness synthesis.
2. Include:
   - completed files,
   - tests run,
   - changed code paths,
   - every ledger item status,
   - loggers active,
   - collectors active,
   - Databento/Sierra capture readiness,
   - exact blockers and triggers,
   - what the next monitoring session should verify,
   - what remains forbidden from live promotion.
3. Explicitly state `NO_PROMOTION_VERDICT`.

Suggested action ids:
- `FCI-ACTION-001` master action ledger
- `FCI-ACTION-002` pending-limit lifecycle logger
- `FCI-ACTION-003` broker-R/deal reconciliation
- `FCI-ACTION-004` V2b forward pair collector
- `FCI-ACTION-005` pre-fill delivery path capture
- `FCI-ACTION-006` FVG/OB confluence ledger
- `FCI-ACTION-007` NAS100/NQ orderflow forward diagnostic
- `FCI-ACTION-008` Databento forward capture manifests/fetch wrappers
- `FCI-ACTION-009` Sierra forward capture readiness
- `FCI-ACTION-010` 6B sampling alignment
- `FCI-ACTION-011` SI source-definition resolution
- `FCI-ACTION-012` XAUUSD frozen-slice extension
- `FCI-ACTION-013` EURUSD/6E pre-registration
- `FCI-ACTION-014` ES/MES pre-registration
- `FCI-ACTION-015` CL/ZN/VIX context ledgers
- `FCI-ACTION-016` lower-timeframe ambiguity classifier
- `FCI-ACTION-017` cost/slippage/exit accounting coverage
- `FCI-ACTION-018` AI decision-layer shadow labels/readiness
- `FCI-ACTION-019` data/source-map maintenance
- `FCI-ACTION-020` claim-ledger automation
- `FCI-ACTION-021` monitoring-session prompt/runbook
- `FCI-ACTION-022` final synthesis

Recommended tests to inspect/reuse before adding new ones:
- `tests/test_slippage_shadow_logger.py`
- `tests/test_time_in_trade_shadow_logger.py`
- `tests/test_orderflow_forward_collection_plan.py`
- `tests/test_orderflow_event_manifest.py`
- `tests/test_orderflow_depth_mbp10_features.py`
- `tests/test_orderflow_candidate_outcome_join.py`
- `tests/test_orderflow_actual_outcome_coverage.py`
- `tests/test_orderflow_nas100_cached_feature_forensics.py`
- `tests/test_databento_futures.py`
- `tests/test_fetch_databento_manifest.py`
- `tests/test_extract_sierra_depth_features.py`
- `tests/test_audit_sierra_depth_sampling_parity.py`
- `tests/test_raw_ohlc_path_scaling_v2b_registration.py`
- `tests/test_raw_ohlc_path_scaling_v2b_prospective.py`
- `tests/test_phase3_research_claim_ledger.py`
- `tests/components/test_trade_record_instrumentation.py`

Databento policy for this goal:
- Use Databento for forward capture and parity/event-window work when it directly supports the action ledger.
- Use cached data first.
- Before any new paid pull, create a request artifact naming symbol, dataset, schema, date/time window, fields, reason, expected use, estimated cost, and evidence class.
- Fetch only declared windows.
- Save output under a versioned/cached path and update source index/cost ledger.
- Do not use a pulled window for both tuning and validation.
- If API/network approval is required, request it through the tool immediately with precise justification.

Sierra policy for this goal:
- Use Sierra `.scid` and `.depth` as local forward/recent source infrastructure.
- Do not treat Sierra as historical MBO replacement.
- Keep operator/manual Sierra chartbook steps explicit when code cannot force new symbol capture.
- Respect family-specific parity status: NQ/YM exact in tested windows, GC near, 6B needs sampling alignment, SI blocked until source definition is resolved.

Commit discipline:
- Commit scoped docs/tooling/code changes periodically.
- Do not stage unrelated runtime dirt.
- Use commit trailer: `Co-Authored-By: Codex GPT-5 <redacted@example.com>`.
- Regenerate `LIVE_STATE.md` after material commits.
- Update `.context\00_core\research_current_state.md` if the research map changes.

Final closeout:
1. Run focused tests for new/changed tooling.
2. Run `python scripts\generate_live_state.py`.
3. Inspect `.context\LIVE_STATE.md` research freshness and git status.
4. List commits.
5. State which action ids are `DONE`, `IMPLEMENTED_SHADOW_ONLY`, `WAITING_FOR_FORWARD_ROWS_WITH_COLLECTOR_ACTIVE`, or `BLOCKED_WITH_EVIDENCE_AND_TRIGGER`.
6. State exactly what the next monitoring session should check.
7. State explicitly: `NO_PROMOTION_VERDICT`.
```

## Recommended Launch Forms

Interactive, approval-capable:

```powershell
codex --enable goals -C C:\Users\MSI\Documents\ai-trading-agent -s workspace-write -a on-request
```

Then paste the goal prompt above.

Non-interactive file launch:

```powershell
codex exec -C C:\Users\MSI\Documents\ai-trading-agent -s workspace-write -a on-request < research\program_control\FORWARD_CAPTURE_AND_INTELLIGENCE_INFRASTRUCTURE_GOAL_PROMPT_2026-05-04.md
```

Use `-a on-request` rather than `-a never` if the session should use Databento/network/filesystem approvals. Use `-a never` only when an unattended run should write blocker notes instead of requesting approvals.

