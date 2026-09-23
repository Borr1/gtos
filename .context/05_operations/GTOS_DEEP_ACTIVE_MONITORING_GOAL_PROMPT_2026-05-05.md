# GTOS Deep Active Monitoring Goal Prompt - 2026-05-05

Status: active launch wrapper
Scope: full live-system monitoring plus market tape, price-action events, cross-market context, source/orderflow context, ML/shadow awareness, and AI observation ledger
Promotion posture: `NO_PROMOTION_VERDICT`

Use this file to start a fresh `/goal` monitoring session.

## Short Goal Starter

```text
/goal
GTOS deep active monitoring for today's live sessions.

You are working in C:\Users\MSI\Documents\ai-trading-agent.

Use .context\05_operations\GTOS_DEEP_ACTIVE_MONITORING_GOAL_PROMPT_2026-05-05.md as the active goal specification.

Access/escalation rule:
The owner has approved requesting access when sandbox/permissions block necessary monitoring, testing, MT5 reads, temp-directory creation, process inspection, or restart verification. If an important command fails because of sandboxing or Windows permissions, request escalation immediately with a concrete reason, then rerun after approval. Do not misclassify access limitations as GTOS health failures, and do not keep working from stale or partial evidence when access can be requested.

Objective:
Monitor GTOS as both an operational safety system and a second AI intelligence layer. Do not only check whether processes are alive. Watch the market, the system, the shadow logs, the source feeds, and the linked evidence as a single live research-and-operations tape.

Persistence rule:
This goal remains active until all configured live sessions for the monitoring day are closed, the final post-writer follow/enrichment/audit/verifier sequence has run, KZ mini-syntheses and the final report are written, and the owner has not asked you to stop. Never mark the goal complete only because one monitor/verifier snapshot is clean. A clean snapshot is a checkpoint, not an endpoint. If tool state prevents keeping a formal goal open, state that limitation and keep monitoring operationally.

You must monitor every important update as it arrives: MT5 account/state, orchestrators, tick capture, Sierra Chart, Sierra .depth/.scid writes, Databento trigger/license/budget status, watchdog, notifications, storage, live logs, shadow logs, verifier outputs, candidate path follow, pending-limit lifecycle, broker/account truth, execution telemetry, ML shadow, orderflow/source status, and every LTO intelligence lane.

You must also actively follow price action: session opens, opening candles, KZ highs/lows, liquidity grabs, displacement candles, candles that approach entry and reject, candles that touch entry without fill, candles that miss entry and run to TP, candles that go through entry then return, SL/TP area touches, near misses, wick/body behavior, volatility bursts, structure breaks, and cross-market confirmation/divergence. Track whether these events are captured by structured logs or only by AI/operator observation.

For every live candidate, pending limit, shadow-only strategy event, or important price-action event, follow the actual chart path until a documented terminal or still-open state exists: limit filled, limit missed, internal pending still open, cancelled wrong-side, entry touched without production fill, entry never touched, price came close then rejected, price went through and returned, price went through and continued, TP/SL area reached, unresolved/in-flight, stale-source blocked, or source-not-captured.

Candidate price-action accountability rule:
Never let `no broker fill`, `no open position`, or a clean verifier snapshot be the whole update for a candidate. For every candidate/pending intent/path event, report two separate truths in the owner update and observation ledger:

1. Production truth: broker positions/orders, broker ticket, internal pending state, order-send status, fill/no-fill/cancel reason, realized broker/account PnL, and whether any live exposure existed.
2. Market-path truth: what price actually did after the decision using corrected UTC M15 bars plus M1/tick evidence when relevant. Include entry/SL/TP levels, first touch times, M15 OHLC sequence, current price, max high, min low, max favorable excursion, max adverse excursion, R-equivalent path metrics, rebound/continuation behavior, and whether the path was captured by structured logs or only by operator observation.

If price crosses entry, SL, TP, or an invalidation area while production has no fill, explicitly classify it as `PRICE_THROUGH_ENTRY_NO_FILL`, `SL_AREA_REACHED_NO_FILL`, `TP_AREA_REACHED_NO_FILL`, `ENTRY_TOUCH_NO_FILL`, or `ENTRY_THEN_SL_SAME_M1_AMBIGUOUS` as applicable. State clearly that these are path/intelligence outcomes, not realized broker outcomes. Do not summarize the event as "safe/no fill" without the adverse/favorable price-action context.

Expired POI reapproval limitation:
Read `.context\05_operations\GTOS_LIMITATION_EXPIRED_POI_REAPPROVAL_2026-05-06.md` before monitoring any expired/cancelled setup that the owner re-approves. Check `knowledge_base\meta\expired_poi_watches\expired_poi_watches_{SYMBOL}.jsonl` and `shadow_logs\expired_poi_revalidation.jsonl` when the watcher is loaded. If the owner points to an expired/cancelled POI and says it is still valid or authorizes execution, immediately state whether a production execution path exists right now: fresh candidate, active pending intent, broker order, or open position. If no approved path exists, say plainly: `I cannot place this manually through GTOS right now; if you want the discretionary trade, you must place it manually or we need a pre-approved override tool/runbook.` Do this before the level is missed. Also report current price, old entry, old SL, old TP, current RR if entered now, and whether that RR still satisfies `risk.min_rr`. Record the event as `EXPIRED_POI_REAPPROVAL_LIMITATION` in the AI observation ledger.

Latest expired-POI checkpoint (2026-05-06 08:05 UTC):
The XAUUSD 2026-05-05 08:15 London SHORT watch (`lim_XAUUSD_2026-05-05_081526`, watch `8c3b63ae1b30d8d8abf6`) is closed, not active. It first revalidated as `TOUCHED_SL_DISTANCE_TOO_TIGHT_NO_REARM`, then the 08:00 UTC London candle/tick invalidated the original short at/through old SL `4679.89`; the watcher wrote `INVALIDATED_BY_SL`. Code commit `21729f0e` added the shadow watcher, and `ccd77bff` makes terminal statuses append `WATCH_CLOSED` rows so stale/duplicate active watches do not keep reprocessing. Current sanity command expectation: `python scripts\follow_expired_poi_watches.py --symbol XAUUSD --mode live --no-write` should return `rows: []` unless a new active expired-POI watch is created later.

Latest shadow-data checkpoint (2026-05-06 16:48 UTC):
`python scripts\verify_shadow_log_integrity.py` is clean at `OK_WITH_DOCUMENTED_WAITING_LANES` after the dependent audit refresh; do not treat temporary `ACTION_REQUIRED` dependency-signature gaps as data corruption until the post-writer audit chain has run. `python scripts\audit_live_shadow_data_health.py` is `OK_WITH_DOCUMENTED_LIMITATIONS` with `issue_count=0`, `latest_candidates=86`, `COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY=21`, `DUPLICATE_ACTIVE_SETUP_NOT_COUNTABLE=64`, and `BLOCKED_ACTIVE_SAME_SYMBOL_TRADE_OVERLAP=1`. If `follow_live_candidate_paths.py` writes new rows during an active KZ, rerun the dependent audit refresh before trusting the verifier: candidate path contract, opportunity lifecycle, pending-limit lifecycle, V2b, prefill, FVG/OB, context control, broker actual-R, J46/J49, regime decay, decision diagnostics, mechanical context, exit-management no-event, K55 ML shadow, and current status rows for V2 readiness/XAU same-market/shadow-observer hardening. This prevents stale or duplicate dependency rows from being mistaken for live data corruption.

Latest stale-data incident checkpoint (2026-05-06 16:50 UTC):
After the owner-reported internet interruption, XAUUSD/XAGUSD/NAS100 orchestrators and all tick-capture daemons still had live PIDs/heartbeats, but production evaluation capture was stale. Evidence: `strategy_follow_evaluations.jsonl` stopped at `2026-05-06T11:00:22Z`, tick-capture `last_progress_utc` stopped around `11:00Z`, and live orchestrator logs showed repeated `Data incomplete: Insufficient D1 candles: got 0, need 30` plus equity-zero anomalies while a fresh MT5 process could read account/ticks/candles normally. Commit `9dec9be5` fixes the source paths: orchestrators retry MT5 ingest through disconnect/connect, then exit abnormally without a graceful marker after 3 consecutive data-incomplete candles; watchdog restarts tick captures whose progress heartbeat is stale even if PID is alive; `_live_monitor_iter.py` alerts on stale `strategy_follow_evaluations` during active KZ; equity anomaly rows now use the locked JSONL writer. Future monitoring must treat heartbeat/PID freshness as necessary but insufficient. During active KZ, verify all three liveness layers: process heartbeat, strategy-follow evaluation freshness, and tick-capture progress freshness.

For cross-market awareness, compare NAS100/NQ with US30/YM, XAUUSD/GC with XAGUSD/SI, USDJPY/GBPJPY with 6J and relevant FX context, GBPUSD with 6B, and gold/metals versus indices. Note whether related markets confirm, lead, lag, or diverge.

For source/orderflow awareness, use Sierra and Databento status intelligently: Sierra local depth/scid freshness, proxy class, extracted/pending/blocked depth features, Databento trigger decisions, live-license/budget/cooldown status, and orderflow primitive statuses. Do not let these feeds sit unused; if they are available, explain what they add to market understanding. If they are blocked, write the exact blocker.

For ML/shadow intelligence, check whether K55/ML and mechanical strategy-shadow rows agree, disagree, wait, or block for each important event. Treat ML and shadow systems as observational only.

Canary policy:
Live canary calls are intentionally disabled by the owner's committed cost-control change. Future monitoring sessions must not run, re-enable, or require live canary calls unless the owner explicitly reverses that policy. Treat canary status as an owner-approved disabled/cost-off state, not as a missing validation step.

Write a durable AI observation ledger during the session. Suggested file:
research\operations\AI_MARKET_MONITORING_OBSERVATIONS_YYYY-MM-DD.md

Every observation must preserve NO_PROMOTION_VERDICT and label whether it is structured evidence, broker/account truth, internal lifecycle evidence, futures/source-transfer context, or OPERATOR_AI_OBSERVATION/HYPOTHESIS_ONLY.

If a suspected issue appears, verify it with multiple evidence sources before classifying or acting. Restart only the verified failing component when action is justified and approved by the current instructions. Do not make trading decisions. Do not change prompts, risk, execution logic, safety gates, or live decision behavior.
```

## Hard Completion Contract

- Do not complete, close, or stop the monitoring goal during active or pending live-session coverage unless the owner explicitly tells you to stop.
- A clean `scripts\_live_monitor_iter.py`, `verify_shadow_log_integrity.py`, or `audit_live_shadow_data_health.py` result is only a checkpoint. Continue the cadence through the next candle/session until the end-of-day closeout criteria are met.
- End-of-day closeout is allowed only after: all configured live sessions for the day have closed, candidate/path writers are idle for the final snapshot, source enrichment and dependent audits have run after the last writer, final verifiers are clean or documented, KZ mini-syntheses are written, the AI observation ledger is updated, and the final monitoring report is produced.
- If a formal goal/task tool cannot remain active, keep monitoring operationally in the thread and state the limitation. Do not use tool-state limitations as a reason to stop watching the live tape.

## Mandatory First Actions

1. Run `python scripts\generate_live_state.py`.
2. Read `.context\LIVE_STATE.md`.
3. Read the latest handoff in `.context\02_session_handoffs\`.
4. Read `.context\00_core\quick_reference_card.md`.
5. Read `.context\00_core\research_operating_doctrine.md`.
6. Read `.context\00_core\research_current_state.md`.
7. Read `.context\05_operations\GTOS_DEEP_ACTIVE_MONITORING_RUNBOOK_2026-05-05.md`.
8. Read `.context\05_operations\FORWARD_CAPTURE_MONITORING_RUNBOOK_2026-05-04.md`.
9. Read `research\program_control\LIMITATIONS_TO_OPPORTUNITIES_MILESTONE_REVIEW_2026-05-05.md`.
10. Read `.context\05_operations\GTOS_LIMITATION_EXPIRED_POI_REAPPROVAL_2026-05-06.md`.
11. Inspect current `git status --short` and do not stage unrelated runtime dirt.

## Baseline Health Pass

At session start, run:

```powershell
python scripts\watchdog_e2e_verify.py --verbose
python scripts\_live_monitor_iter.py
python scripts\follow_live_candidate_paths.py --max-hours 12
python scripts\follow_expired_poi_watches.py --symbol XAUUSD --no-write
python scripts\enrich_sierra_live_candidate_depth_features.py --max-hours 24 --pending-status-only
python scripts\verify_shadow_log_integrity.py
python scripts\audit_live_shadow_data_health.py
```

Also check:

- MT5 read-only state: account connected, trade allowed, broker positions/orders, latest ticks/rates.
- Orchestrator and heartbeat freshness for active KZ symbols.
- Strategy-follow evaluation freshness during active KZ (`shadow_logs\strategy_follow_evaluations.jsonl` must advance after MSO computation; stale >30m during active KZ is critical).
- Tick-capture daemon/process/state freshness (`pipeline_state\daemon_heartbeat_tick_capture_*.json`, using `last_progress_utc`, not PID alone).
- Sierra process and current `.depth`/`.scid` freshness.
- Watchdog scheduled task/latest log.
- Notification queue status.
- Storage free space.
- Shadow observer process/status if applicable.

## Active Monitoring Protocol

During active KZ:

- Run `scripts\_live_monitor_iter.py` every 5 minutes.
- Run `scripts\follow_live_candidate_paths.py --max-hours 12` after any new candidate or at least once per active check cycle.
- Run `scripts\enrich_sierra_live_candidate_depth_features.py --max-hours 24 --pending-status-only` after the follow writer.
- Run read-only summaries/verifiers after writers complete, not in parallel with them.
- Treat fresh heartbeats/PIDs as insufficient if `strategy_follow_evaluations.jsonl`, `candidate_features_log.jsonl`, or tick-capture progress heartbeats are stale during active KZ. Confirm logs do not show repeated `Data incomplete`/equity-zero anomalies; if they do and read-only MT5 truth is healthy, restart the verified stale component.
- Do a full M15 tape read for active symbols at every candle close. This is mandatory market analysis, not optional commentary.
- Do an event-driven check between candles when price approaches entry, SL, TP, prior high/low, KZ high/low, a visible sweep area, or a pending limit lifecycle changes.
- After any candidate, pending-limit lifecycle change, or path-label change, immediately pull the corrected UTC M15 tape and M1/tick evidence for that symbol before giving the owner a summary. If the lifecycle says no fill but the path touched/crossed entry, SL, or TP, report both facts in the same update.
- Update the owner every 30 minutes and immediately for verified critical/high findings.

Every active check cycle must include a market-intelligence note, even when no new trade is placed:

- active sessions and minutes from open/close,
- latest M15 candle behavior for active symbols,
- current price relative to candidate entries, stops, TP areas, KZ highs/lows, open range, POIs, and invalidation areas,
- new candidates, rejected candidates, pending limits, near misses, touch/no-fill paths, and still-open paths,
- cross-market confirmation/divergence for NAS100/US30, XAUUSD/XAGUSD, JPY pairs/6J, GBPUSD/6B, and indices/metals when relevant,
- Sierra/Databento/source/orderflow status and exact blockers,
- ML/mechanical shadow agreement, disagreement, or waiting status,
- whether each important market event was captured by structured logs or only by `OPERATOR_AI_OBSERVATION/HYPOTHESIS_ONLY`.

Every active check cycle must also maintain a quantitative scoreboard:

- production broker truth: positions, broker orders, internal pending intents, account equity, and any mismatch,
- raw candidates, countable primary opportunities, duplicate active setups, rejected candidates, and production `LIMIT_PLACED` rows,
- per-symbol and per-session candidate counts,
- entry/SL/TP/RR for every production limit intent and every countable primary opportunity,
- fill/path state for each important row: filled, not filled, still pending, cancelled wrong-side, entry touched no fill, TP/SL area reached without fill, M15 ambiguous, or unresolved,
- market-path excursion metrics for each important candidate: max high, min low, last close/current price, first entry/SL/TP touch time, max favorable excursion, max adverse excursion, R-equivalent path movement, and rebound/continuation state,
- proxy-R and score status for production baseline, pending-limit lifecycle, V2/V2B, J46/J49, and other active mechanical/shadow lanes when available,
- ML/K55 prediction or blocker status for every important candidate,
- source/orderflow status and exact blockers for Sierra, Databento, futures proxies, and source-transfer lanes,
- a clear distinction between realized broker/account PnL, internal lifecycle evidence, synthetic/path proxy-R, and observation-only market hypotheses.

Between KZ:

- Check every 15 minutes.
- Focus on stale sources, watchdog, storage, shadow observer, unclosed pending intents, verifier health, and any post-candidate continuation/rebound that is still relevant to the session tape.
- Write KZ mini-synthesis after each session closes, including market behavior, candidates, path outcomes, source coverage, ML/shadow notes, and unresolved evidence gaps.

End of day:

- Run final path follow, source enrichment, dependent audits, and final verifiers in that order.
- Produce a final monitoring report with system health, market tape, price-action event ledger, source/orderflow status, ML/shadow observations, incidents/fixes, blockers, and hypotheses.
- Only then mark the monitoring objective complete.

## Required Observation Categories

Track and label these events when they appear:

- `OPENING_CANDLE_PATTERN`
- `SESSION_OPEN_RANGE_BREAK`
- `KZ_HIGH_LOW_BREAK`
- `LIQUIDITY_GRAB`
- `DISPLACEMENT_WITH_STRUCTURE`
- `DISPLACEMENT_WITHOUT_STRUCTURE`
- `ENTRY_APPROACH`
- `ENTRY_NEAR_MISS`
- `ENTRY_TOUCH_NO_FILL`
- `ENTRY_TOUCH_FILLED`
- `BOUNCE_FROM_ENTRY_ZONE`
- `PRICE_THROUGH_ENTRY_NO_FILL`
- `TP_AREA_REACHED_NO_FILL`
- `TP_AREA_REACHED_AFTER_FILL`
- `SL_AREA_REACHED_NO_FILL`
- `SL_AREA_REACHED_AFTER_FILL`
- `WRONG_SIDE_CANCEL_RISK`
- `STALE_PENDING_INTENT`
- `ORDERFLOW_SUPPORTS_SETUP`
- `ORDERFLOW_CONTRADICTS_SETUP`
- `SOURCE_NOT_CAPTURED_FOR_EVENT`
- `CROSS_MARKET_CONFIRMATION`
- `CROSS_MARKET_DIVERGENCE`
- `ML_SHADOW_AGREES`
- `ML_SHADOW_DISAGREES`
- `MONITOR_HYPOTHESIS`

## Required Logs And Lanes To Watch

Core live/follow lanes:

- `shadow_logs\strategy_follow_evaluations.jsonl`
- `shadow_logs\strategy_follow_candidates.jsonl`
- `shadow_logs\candidate_path_follow.jsonl`
- `shadow_logs\candidate_ltf_path_order.jsonl`
- `shadow_logs\pending_limit_lifecycle.jsonl`
- `shadow_logs\pending_limit_lifecycle_join_backfill.jsonl`
- `shadow_logs\live_mechanical_strategy_shadow_outcomes.jsonl`
- `shadow_logs\live_candidate_opportunity_clusters.jsonl`
- `shadow_logs\live_candidate_strategy_rollups.jsonl`
- `shadow_logs\live_structural_strategy_metadata.jsonl`
- `shadow_logs\missed_opportunity_shadow.jsonl`

Research/intelligence lanes:

- `shadow_logs\v2b_forward_pairs.jsonl`
- `shadow_logs\v2b_forward_pair_resolutions.jsonl`
- `shadow_logs\prefill_delivery_path.jsonl`
- `shadow_logs\prefill_delivery_path_resolutions.jsonl`
- `shadow_logs\fvg_ob_confluence.jsonl`
- `shadow_logs\fvg_ob_confluence_resolutions.jsonl`
- `shadow_logs\context_control_ledger.jsonl`
- `shadow_logs\candidate_features_log.jsonl`
- `shadow_logs\proximity_shadow_log.jsonl`
- `shadow_logs\liquidity_distance_log.jsonl`
- `shadow_logs\displacement_events.jsonl`
- `shadow_logs\touch_count_gate_decisions.jsonl`
- `shadow_logs\sl_beyond_ob_decisions.jsonl`
- `shadow_logs\d1_bias_lag.jsonl`
- `shadow_logs\direction_emission_xau_audit.jsonl`
- `shadow_logs\regime_classifications.jsonl`
- `shadow_logs\structure_detector_divergences.jsonl`

Outcome/execution/account lanes:

- `shadow_logs\account_truth_reconciliation_status.jsonl`
- `shadow_logs\broker_actual_r_audit.jsonl`
- `shadow_logs\exit_management_shadow_status.jsonl`
- `shadow_logs\j46_j49_exit_comparator_audit.jsonl`
- `shadow_logs\s79_side_aware_risk_context.jsonl`
- `shadow_logs\regime_decay_outcome_join.jsonl`
- `shadow_logs\decision_layer_diagnostics_join.jsonl`
- `shadow_logs\mechanical_context_diagnostics_join.jsonl`

Source/orderflow/ML lanes:

- `shadow_logs\sierra_confluence_source_status.jsonl`
- `shadow_logs\sierra_depth_enrichment_status.jsonl`
- `shadow_logs\sierra_depth_feature_snapshots.jsonl`
- `shadow_logs\databento_live_trigger_decisions.jsonl`
- `shadow_logs\databento_live_confluence.jsonl`
- `shadow_logs\databento_live_budget_ledger.jsonl`
- `shadow_logs\orderflow_primitives_status.jsonl`
- `shadow_logs\external_source_blocker_status.jsonl`
- `shadow_logs\proxy_blocker_status.jsonl`
- `shadow_logs\ml_shadow_predictions.jsonl`
- `shadow_logs\ml_shadow_status.jsonl`

Existing monitor outputs:

- `shadow_logs\live_monitor.jsonl`
- `shadow_logs\live_monitor_alerts.jsonl`

## AI Observation Ledger Template

Create or update:

```text
research\operations\AI_MARKET_MONITORING_OBSERVATIONS_YYYY-MM-DD.md
```

Use this structure:

```text
## HH:MM UTC - SYMBOL - EVENT_TYPE

- Evidence class:
- Candidate/trade ids:
- Session/timing:
- Price-action summary:
- Production truth:
- Market-path truth:
- Structured evidence checked:
- Source/orderflow context:
- Cross-market context:
- ML/shadow context:
- Why it matters:
- Hypothesis status:
- Next evidence required:
- Promotion posture: NO_PROMOTION_VERDICT
```

## Owner Update Format

Every update should include:

- active session/time,
- critical/high issue count,
- broker positions/orders/pending intents,
- new candidates and path states,
- for every active or recently resolved candidate: separate production truth from market-path truth, including adverse/favorable excursion and rebound/continuation behavior,
- important price-action events,
- Sierra/Databento/orderflow source status when relevant,
- cross-market context when relevant,
- verifier status,
- what is being watched next.

## Final Output

Write a final report with:

- overall readiness/degradation/action-required status,
- production safety status,
- process/watchdog/MT5/Sierra/tick/notification/storage status,
- shadow-data integrity and data-health status,
- candidate and pending-limit lifecycle table,
- market tape timeline by KZ,
- price-action event ledger,
- cross-market observations,
- Sierra/Databento/orderflow source status,
- ML/strategy-shadow observations,
- incidents, false positives, and fixes/restarts,
- open blockers and exact triggers,
- hypotheses generated for later validation,
- `NO_PROMOTION_VERDICT`.

Do not treat this monitoring session as a trading recommendation, strategy promotion, or authorization to alter live decision behavior.
