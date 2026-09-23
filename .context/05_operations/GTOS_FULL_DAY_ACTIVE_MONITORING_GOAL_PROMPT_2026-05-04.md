# GTOS Full-Day Active Monitoring Goal Prompt - 2026-05-04

Status: active launch wrapper
Scope: all-day live monitoring across GTOS trading, data, logging, notifications, Sierra forward capture, MT5, watchdog, and post-Tokyo storage cleanup
Posture: verify before classifying; minimal action; no trading decisions

Use this file to start a fresh `/goal` session.

## Short Goal Starter

```text
/goal
GTOS full-day active monitoring on 2026-05-04 across Tokyo, London, and NY kill zones.

You are working in C:\Users\MSI\Documents\ai-trading-agent.

Use .context\05_operations\GTOS_FULL_DAY_ACTIVE_MONITORING_GOAL_PROMPT_2026-05-04.md as the active goal specification.

The objective is to monitor the whole live system from smallest part to largest part all day today: MT5, Sierra Chart, Sierra .depth/.scid writes, Databento/cache status where relevant, GTOS orchestrators, tick-capture daemons, heartbeat files, watchdog, notification queue, Telegram path, live logs, shadow logs, stale data, stale decisions, stale verifiers, storage pressure, and forward-capture artifacts.

Also monitor the live-shadow/follow-data system explicitly: AI-independent MSO strategy snapshots, AI CANDIDATE terminal strategy registry rows, candidate price-path follow rows, live mechanical strategy shadow outcomes, V2b forward pairs and resolutions, V3/pre-fill delivery paths and resolutions, FVG/OB confluence rows and resolutions, lower-timeframe path ordering, missed-opportunity shadow rows, live candidate rollups, context-control rows, pending-limit lifecycle rows and join-backfills, Sierra/Databento confluence status, account/PnL truth lanes, O1/O8 verifiers, ML/proxy/source blocker rows, and every documented blocker in the live-shadow coverage audit and gap-closure final artifact.

For every live candidate and every shadow-only strategy signal, follow the actual chart path until a documented terminal or still-open state exists: limit filled, limit missed, entry touched without a production fill, entry never touched, price came close then rejected, price went through and returned, price went through and continued, TP1/TP/SL area reached, unresolved/in-flight, stale-source blocked, or source-not-captured. Shadow rows are observational only: never place, modify, cancel, recommend, or infer a live trade from them.

If a suspected issue appears, verify it with multiple evidence sources before classifying or acting. Do not make trading decisions. Do not change prompts, risk, execution logic, safety gates, or live decision behavior without explicit owner approval. Restart only the verified failing component when action is justified.
```

## Mandatory First Actions

1. Run `python scripts\generate_live_state.py`.
2. Read `.context\LIVE_STATE.md`.
3. Read the latest handoff in `.context\02_session_handoffs\`.
4. Read `.context\00_core\quick_reference_card.md`.
5. Read `.context\05_operations\FORWARD_CAPTURE_MONITORING_RUNBOOK_2026-05-04.md`.
6. Read or regenerate `research\program_control\LIVE_SHADOW_FOLLOWUP_COVERAGE_AUDIT_2026-05-04.md`.
7. Read `research\program_control\LIVE_SHADOW_GAP_CLOSURE_FINAL_2026-05-04.md` and `.context\05_operations\LIVE_SHADOW_GAP_CLOSURE_PLAN_2026-05-04.md`; treat the final artifact as the post-closure source of truth and the plan as the completed checklist plus monitoring doctrine.
8. Run a baseline health pass:
   - `python scripts\watchdog_e2e_verify.py --verbose`
   - `python scripts\verify_forward_capture_readiness.py --output-json research\program_control\FORWARD_CAPTURE_READINESS_VERIFICATION_2026-05-04.json --output-md research\program_control\FORWARD_CAPTURE_READINESS_VERIFICATION_2026-05-04.md`
   - `python scripts\audit_live_shadow_followup_coverage.py --output-json research\program_control\LIVE_SHADOW_FOLLOWUP_COVERAGE_AUDIT_2026-05-04.json --output-md research\program_control\LIVE_SHADOW_FOLLOWUP_COVERAGE_AUDIT_2026-05-04.md`
   - MT5 read-only connectivity/fresh tick probe
   - Sierra forward depth freshness inventory
   - heartbeat and tick-capture state freshness
   - notification queue worker/queue status
   - storage free-space check
   - `python scripts\follow_live_candidate_paths.py --max-hours 12`
   - `python scripts\verify_shadow_log_integrity.py`

## Monitoring Cadence

- During an active kill zone: check every 5 minutes.
- Between kill zones: check every 15 minutes.
- Give the owner a concise status update every 30 minutes.
- Interrupt immediately for verified `URGENT` or `SERIOUS` findings.
- Keep a running issue ledger in the chat or a scratch note with: timestamp, component, symptom, evidence, false-positive checks, severity, action, status.

## System Scope

Monitor all of the following:

- MT5 terminal: initialized, connected, account usable, trade_allowed true, core symbols visible/tradable, fresh ticks/rates, no orphaned open positions.
- GTOS orchestrators: expected symbol processes, KZ-aware liveness, fresh per-symbol heartbeat files, current logs.
- Tick capture: all 7 `.tick_capture_*.lock` files, process liveness, `data\ticks\{SYMBOL}\.state.json` freshness, low-tick-cadence false-positive handling.
- Sierra Chart: `SierraChart_64` running/responding, `GTOS_FORWARD_DEPTH_CAPTURE.Cht` active by operator observation, `.depth` and `.scid` writes fresh for core forward symbols.
- Forward capture symbols: NQ/MNQ, ES/MES, YM/MYM, GC/MGC, SI/SIL, 6J/6B/6E, CL, ZN. VIX/VXM depth is optional/control-only unless explicitly promoted later.
- Watchdog and monitors: `watchdog.log`, OB continuation, API refusal, no-data, CUSUM candidate rate, correlation shock, calendar stale, canary cache.
- Notifications: notification queue process, queue file, Telegram monitor status. Do not send test Telegram messages unless explicitly approved.
- Logs/shadow logs: stale mtimes, repeated exceptions, traceback, malformed responses, pending limit lifecycle, slippage, daily PnL, touch-count decisions, forward-capture logs.
- Live-shadow follow data: `strategy_follow_evaluations.jsonl`, `strategy_follow_candidates.jsonl`, `candidate_path_follow.jsonl`, `live_mechanical_strategy_shadow_outcomes.jsonl`, `live_structural_strategy_metadata.jsonl`, `candidate_ltf_path_order.jsonl`, `v2b_forward_pairs.jsonl`, `v2b_forward_pair_resolutions.jsonl`, `prefill_delivery_path.jsonl`, `prefill_delivery_path_resolutions.jsonl`, `fvg_ob_confluence.jsonl`, `fvg_ob_confluence_resolutions.jsonl`, `missed_opportunity_shadow.jsonl`, `live_candidate_strategy_rollups.jsonl`, `context_control_ledger.jsonl`, `pending_limit_lifecycle.jsonl`, `pending_limit_lifecycle_join_backfill.jsonl`, `sierra_confluence_source_status.jsonl`, `databento_live_trigger_decisions.jsonl`, `databento_live_confluence.jsonl`, `account_truth_reconciliation_status.jsonl`, `proxy_blocker_status.jsonl`, `ml_shadow_status.jsonl`, `external_source_blocker_status.jsonl`, and the coverage/integrity statuses for blocked/source-gated items.
- Storage: free disk, Sierra depth growth, repo `data\external` growth, current-day file write continuity.

## Live-Shadow Outcome Monitoring

Every active-kill-zone monitoring pass must include:

- Run `python scripts\_live_monitor_iter.py`.
- Run `python scripts\follow_live_candidate_paths.py --max-hours 12` after any new M15 candidate/follow row appears or at least once per active KZ check cycle. This command writes append-only follow/backfill rows; let it complete before starting read-only summaries or verifiers.
- Run `python scripts\enrich_sierra_live_candidate_depth_features.py --max-hours 24 --pending-status-only` after the follow writer and before readers. This gives every candidate an explicit Sierra feature-lane state without letting heavy `.depth` parsing block live monitoring.
- Run dependent read-only checks sequentially after the follow writer finishes, not in parallel with it: `python scripts\summarize_live_shadow_opportunities.py`, then `python scripts\verify_shadow_log_integrity.py`, then `python scripts\audit_live_shadow_data_health.py`.
- Treat any non-empty `issues` from `verify_shadow_log_integrity.py` or `audit_live_shadow_data_health.py` as at least `SERIOUS` until explained. The data-health audit is the semantic check for cross-log candidate coverage, identity conflicts, latest-row alignment, mechanical strategy row completeness, opportunity duplicate counting, Sierra/Databento confluence presence, critical null/empty fields, explicit `SOURCE_NOT_CAPTURED` limitations, and paid-call/no-execution safety flags.
- Confirm each new `strategy_follow_candidates.jsonl` row has matching or waiting rows in the applicable shadow logs: path follow, mechanical outcomes, V2b/pre-fill/FVG resolutions, LTF path order, missed-opportunity, candidate rollup, Sierra status, Databento trigger decision, account-truth reconciliation, and pending-limit join if a limit intent exists.
- For any shadow strategy that records a hypothetical entry/fill/outcome, report it as `shadow-only` with strategy name, candidate id, entry status, path status, max favorable/adverse movement if available, TP/SL area status, and whether the production system placed/no-placed/filled/no-filled an order.
- If a production limit is placed, follow both the broker order lifecycle and the shadow market-entry/comparator lifecycle; distinguish `production_limit_not_filled` from `shadow_entry_touched`, `shadow_tp_reached`, or `missed_market_opportunity`.
- If fields are marked `SOURCE_NOT_CAPTURED`, do not synthesize them from later candles. Backfill them only when an original decision-time source row/file contains the exact value.
- Preserve append-only behavior and duplicate protection. Do not overwrite prior shadow rows from another source, session, day, or instrument.
- Do not make AI, canary, order, or paid Databento calls from monitoring/backfill scripts. Databento paid live data can only be used by a predeclared strategy trigger/budget path; otherwise log `paid_fetch_attempted=false` and `paid_data_calls=0`.
- Treat stale shadow logs differently from waiting lanes: event-driven files can wait for fills/exits, but candidate-triggered files must advance when candidates advance.
- For candidate/strategy comparisons, use the opportunity-level dedupe ledger at `shadow_logs/live_candidate_opportunity_clusters.jsonl` and the summary tool `scripts/summarize_live_shadow_opportunities.py`. Count only `COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY`; preserve but do not trade-count `DUPLICATE_ACTIVE_SETUP_NOT_COUNTABLE` or `BLOCKED_ACTIVE_SAME_SYMBOL_TRADE_OVERLAP`. Raw candidate rows are evidence, not the unit of trade-opportunity comparison. See `.context/05_operations/LIVE_SHADOW_OPPORTUNITY_DEDUPE_CONTEXT_2026-05-04.md`.

Concise owner updates during active monitoring should include: latest closed M15 candle, candidate count, new shadow rows, mechanical-shadow outcome count, pending-limit status, shadow-only trade/outcome highlights, verifier status, stale/source blockers, and whether any data was source-not-captured.

## Verification Rule

Never classify from one artifact alone unless the failure is direct and conclusive. For each suspected issue, cross-check at least two of:

- process is alive/responding
- file mtime/freshness
- latest log lines
- data row/tick count
- watchdog result
- MT5/Sierra observed state
- expected KZ/session cadence

Example: an old `api_refusal_monitor.log` is not enough to call API refusal broken; the monitor prints nothing on happy-path exit 0, so `watchdog.log` `[API_REFUSAL] OK` is the heartbeat.

## Severity Taxonomy And Actions

### URGENT

Verified issue can affect trade safety, order management, live decision data during an active KZ, or critical alerting.

Examples:
- MT5 disconnected, trade disabled, or symbol data unavailable during active KZ.
- Orchestrator for an in-KZ symbol dead and watchdog did not recover it.
- Per-symbol heartbeat stale beyond 300s during that symbol's KZ.
- Tick capture for all symbols down, or active symbol tick capture dead with no current `.state.json` movement.
- Sierra forward depth for active capture symbols not writing when it should be writing.
- Orphaned open broker position with no managing orchestrator.
- Heartbeat flatten or watchdog critical path broken.
- Telegram critical alert path verified broken for alerts that require operator action.

Action:
- Diagnose with evidence.
- Restart only the affected component once verified.
- Report immediately with evidence and action taken.
- Do not broad-restart the fleet unless the failure is fleet-wide and verified.

### SERIOUS

Verified issue degrades monitoring, logging, or data capture and could hide a problem, but does not directly alter live trade decisions right now.

Examples:
- One non-active symbol's tick capture stale.
- A monitor script failing while watchdog/orchestrators remain healthy.
- A core shadow log silently stopped writing when it should be writing.
- Canary/cache verifier drift that produces false failures.
- Sierra non-current historical symbol write failure outside active capture.

Action:
- If inside KZ and not worsening, defer restart/fix until between KZs.
- If between KZs, restart/fix the affected component only.
- Record action and re-check.

### MODERATE

Partial degradation or early warning with limited immediate impact.

Examples:
- CUSUM candidate-rate alarm requiring research review.
- Storage below comfort threshold but not below emergency threshold.
- One control-only context symbol missing depth.
- One low-volume symbol `.state.json` stale but ticks/logs show market quiet.

Action:
- Record and monitor.
- Queue for between-KZ fix or end-of-day review.
- Do not interrupt live components without a stronger signal.

### LOW

Cosmetic, documentation, stale non-critical artifact, log verbosity, or harmless cleanup issue.

Action:
- Batch for later.
- Do not restart live services.

### FALSE POSITIVE

The apparent issue is contradicted by stronger evidence.

Action:
- Explain why it is false.
- If the false positive comes from a stale verifier/check, patch the verifier if it is read-only and does not affect trading behavior; otherwise queue it.

## Post-Tokyo Storage Cleanup

After Tokyo KZ ends at 03:00 UTC / 11:00 MYT, perform only the approved safe cleanup scope if free space still matters:

- Target directory: `C:\SierraChart\Data\MarketDepthData`.
- Target files: Sierra `.depth` files with embedded date earlier than `2026-05-03`.
- Keep: all `2026-05-03` and `2026-05-04` files, all current-day files, all `.scid`, `.Cht`, `.StdyCollct`, and config files.
- Before deleting, print exact file count and estimated GB reclaim.
- Verify the delete list contains no `2026-05-03`, no `2026-05-04`, and no file without a parseable date.
- If any file is locked or deletion fails, stop and report; do not force around Sierra.
- After deletion, re-check free disk, Sierra process state, and current `.depth` writes.

Do not delete repo `data\external`, Sierra `.scid`, chartbooks, or non-core research bundles unless the owner approves a separate cleanup set.

## End-Of-Day Output

## 14:10 UTC Additive Monitoring Requirements

These are mandatory for the rest of the active goal after the NAS100 capture-gap repair:

- Before any shadow readers, run `python scripts\follow_live_candidate_paths.py --max-hours 12`; it now reconciles AI `CANDIDATE` trade records into missing strategy-follow candidate rows.
- If a strict reader immediately after a candle reports dependent-row gaps only for candidate rows whose `created_at_utc` is after the follow-writer snapshot, treat it first as a read-after-new-candidate race. Rerun `follow_live_candidate_paths.py --max-hours 12` and then rerun the readers before declaring a persistent capture gap.
- Treat `knowledge_base/trade_records/*/*.json` AI `CANDIDATE` rows as an original decision-time source that must have matching `strategy_follow_candidates.jsonl` coverage. Missing rows are a capture gap, not an acceptable limitation.
- Candidate shadow writes must not depend on full Sierra `.depth` feature extraction finishing inline. The live candidate row should capture exact Sierra source/status/path/mtime/size immediately; full heatmap feature extraction can be deferred/enriched later without blocking the candidate row.
- Sierra feature snapshots are now a separate append-only lane at `shadow_logs\sierra_depth_feature_snapshots.jsonl`. Run the status-only enrichment command after the follow writer so each candidate is either `FEATURES_EXTRACTED`, `FEATURE_EXTRACTION_PENDING_HEAVY_DEPTH_SCAN`, or `NO_REGISTERED_SIERRA_PROXY_FOR_SYMBOL`. Heavy depth scans are backfill/enrichment work, not an inline dependency for candidate capture.
- Keep the Databento policy explicit: local/cache/trigger-status only unless the registered live collector/env is enabled. The shadow pipeline itself must report `paid_fetch_attempted=false` and `paid_data_calls=0`.
- If `verify_shadow_log_integrity.py` reports invalid JSONL, repair with `scripts\repair_jsonl_invalid_rows.py --apply <path>` only after quarantining the raw invalid line; do not silently delete evidence.
- For opportunity-level comparisons, count only latest rows with `opportunity_counting_status=COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY`. Preserve but do not sum rows marked `DUPLICATE_ACTIVE_SETUP_NOT_COUNTABLE` or `BLOCKED_ACTIVE_SAME_SYMBOL_TRADE_OVERLAP`.
- For `PENDING_LIMIT_LIFECYCLE`, do not interpret generic M15 candidate-path proxy as lifecycle truth when a real live limit intent existed. Use latest `live_mechanical_strategy_shadow_outcomes.jsonl` rows after `follow_live_candidate_paths.py` reruns: real `LIMIT_PLACED` candidates must be scored from internal `pending_limit_lifecycle.jsonl` telemetry where available, with explicit append-only correction rows if older generic-path rows were superseded.
- For M15 path rows where both TP1 and SL are touched, do not score flat `0R` by fallback. Use `candidate_ltf_path_order.jsonl` terminal fields. TP/SL touches before entry are not filled-trade terminal events. Only resolved post-entry TP1/SL can score R; same-M1 entry/terminal ambiguity remains preserved evidence and must not contribute R without tick-order proof.
- If live code changes must be loaded from this tool session, use the existing Windows scheduled task `TradingAgentDaily` for durable orchestrator launch; tool-launched `Start-Process` children may be cleaned up when the shell job exits.

Produce a concise final report:

- Overall status: ready / degraded / action required.
- Incidents by severity with evidence and action.
- False positives and verifier updates.
- Storage before/after and remaining cleanup candidates.
- Sierra/MT5/watchdog/Telegram readiness.
- Live-shadow/follow-data readiness: which rows appeared, which are waiting for events/restart, which are source/approval/verifier blocked, and candidate path outcomes for each logged candidate.
- Any unresolved items and exact next action.
