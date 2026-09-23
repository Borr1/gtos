# GTOS Deep Active Monitoring Runbook - 2026-05-05

Status: active runbook
Scope: live-system health, shadow-data integrity, market tape, price-action event follow, cross-market context, orderflow/source context, and AI observation ledger
Promotion posture: `NO_PROMOTION_VERDICT`
Decision impact: none; monitoring is observational only

Use this with:

- `.context/05_operations/GTOS_DEEP_ACTIVE_MONITORING_GOAL_PROMPT_2026-05-05.md`
- `.context/05_operations/FORWARD_CAPTURE_MONITORING_RUNBOOK_2026-05-04.md`
- `research/program_control/LIMITATIONS_TO_OPPORTUNITIES_MILESTONE_REVIEW_2026-05-05.md`
- `.context/00_core/research_current_state.md`
- `.context/00_core/research_operating_doctrine.md`

## Purpose

The monitoring session is now a second intelligence layer, not only a watchdog. It must still verify the production system from the smallest moving part to the largest, but it must also watch the market the way a serious operator watches charts:

- What did price do around GTOS entries, stops, targets, order blocks, FVGs, breakers, and liquidity levels?
- Did price approach entry then reject, miss by a few ticks, fill and stall, sweep liquidity then displace, or run directly to TP without fill?
- Did candle timing matter: session open, first 15 minutes, London open, NY open, US30 open, London close, fix window, post-news window, or KZ end?
- Did candle shape matter: displacement candle, wick sweep, engulf, narrow pre-break range, failed continuation, impulsive close through POI, or absorption-looking pause?
- Did other markets agree or diverge: NQ/NAS100 versus YM/US30, GC/XAUUSD versus SI/XAGUSD, JPY pairs versus 6J, GBPUSD versus 6B, risk-on indices versus gold/metals?
- Did Sierra/Databento/source-status rows support or contradict the market read?
- Did the system capture enough linked evidence to learn from this event later?

The goal is to make every active monitoring session produce useful operational safety evidence and useful research intelligence, without changing live decisions.

## Hard Persistence Contract

- This monitoring session is not complete until all configured live sessions for the day have closed and the final closeout sequence is done.
- A clean process pulse, shadow-integrity verifier, or semantic data-health audit is a checkpoint, not a reason to stop.
- Do not mark a goal complete, send a final report, or stop the cadence during active KZ coverage, between-session waiting periods, or while a candidate/pending-limit/source path remains unresolved unless the owner explicitly tells you to stop.
- Final closeout requires this exact order: final candidate path follow, Sierra/status enrichment, dependent append-only audits, shadow-integrity verification, semantic data-health audit, KZ mini-syntheses, AI observation ledger update, and final monitoring report.
- If a tool or session state prevents keeping the formal goal open, state the limitation and continue operational monitoring in the thread.
- If sandbox or Windows permissions block necessary monitoring, tests, MT5 reads, temp directories, process inspection, or restart verification, request escalation immediately with a concrete reason. Do not treat access limits as GTOS health failures when owner-approved escalation can resolve them.

## Non-Negotiable Boundaries

- Do not place, modify, cancel, suggest, or override trades.
- Do not change prompts, risk settings, execution logic, safety gates, strategy selection, or order behavior.
- Do not promote filters, orderflow rules, ML outputs, exits, risk modifiers, or new strategies from monitoring observations.
- Preserve `NO_PROMOTION_VERDICT` in every report.
- Separate evidence classes:
  - `BROKER_ACTUAL_R`
  - `INTERNAL_LIMIT_LIFECYCLE`
  - `SYNTHETIC_PATH_R`
  - `FUTURES_PROXY_TRANSFER`
  - `SAME_MARKET_SOURCE_TRANSFER`
  - `CROSS_INSTRUMENT_CONTEXT`
  - `FORWARD_SHADOW`
  - `DISCOVERY_ONLY`
  - `CONTROL_ONLY`
  - `OPERATOR_AI_OBSERVATION`
- Treat AI monitoring observations as hypotheses until joined to forward outcomes.
- Canary live calls are intentionally disabled by the owner's committed cost-control change. Do not run, re-enable, or require live canary calls in this monitoring workflow unless the owner explicitly reverses that policy.
- No paid Databento live calls unless a registered collector trigger, env enablement, schema, symbol, cooldown, and cost cap all pass.
- Use original decision-time source rows for backfills. Do not synthesize missing decision-time fields from later candles.

## Monitoring Layers

### Layer 0 - Preflight And Safety Pulse

Run at session start, after any restart, and before final closeout:

```powershell
python scripts\generate_live_state.py
python scripts\watchdog_e2e_verify.py --verbose
python scripts\_live_monitor_iter.py
python scripts\follow_live_candidate_paths.py --max-hours 12
python scripts\enrich_sierra_live_candidate_depth_features.py --max-hours 24 --pending-status-only
python scripts\verify_shadow_log_integrity.py
python scripts\audit_live_shadow_data_health.py
```

Also verify:

- MT5 read-only connection, account, `trade_allowed`, broker orders, broker positions, fresh ticks/rates.
- Seven orchestrators expected by active KZ, per-symbol heartbeat freshness, and current symbol logs.
- Seven tick-capture daemons, lock PIDs, `data\ticks\{SYMBOL}\.state.json`, and low-volume false-positive guards.
- Sierra Chart process, chartbook/operator status if visible, `.scid` and `.depth` freshness for active symbols.
- Watchdog scheduled task and latest `logs\watchdog.log`.
- Notification queue and critical alert path state.
- Storage free space and Sierra depth growth.

### Layer 1 - Shadow Capture Coverage

Every active-KZ pass must confirm that new candidates and new strategy-follow rows are linked across the relevant logs. The minimum watch list is:

- `shadow_logs/strategy_follow_evaluations.jsonl`
- `shadow_logs/strategy_follow_candidates.jsonl`
- `shadow_logs/candidate_path_follow.jsonl`
- `shadow_logs/candidate_ltf_path_order.jsonl`
- `shadow_logs/pending_limit_lifecycle.jsonl`
- `knowledge_base/meta/expired_poi_watches/expired_poi_watches_{SYMBOL}.jsonl`
- `shadow_logs/expired_poi_revalidation.jsonl`
- `shadow_logs/pending_limit_lifecycle_join_backfill.jsonl`
- `shadow_logs/live_mechanical_strategy_shadow_outcomes.jsonl`
- `shadow_logs/live_candidate_opportunity_clusters.jsonl`
- `shadow_logs/live_candidate_strategy_rollups.jsonl`
- `shadow_logs/live_structural_strategy_metadata.jsonl`
- `shadow_logs/missed_opportunity_shadow.jsonl`
- `shadow_logs/v2b_forward_pairs.jsonl`
- `shadow_logs/v2b_forward_pair_resolutions.jsonl`
- `shadow_logs/prefill_delivery_path.jsonl`
- `shadow_logs/prefill_delivery_path_resolutions.jsonl`
- `shadow_logs/fvg_ob_confluence.jsonl`
- `shadow_logs/fvg_ob_confluence_resolutions.jsonl`
- `shadow_logs/context_control_ledger.jsonl`
- `shadow_logs/candidate_features_log.jsonl`
- `shadow_logs/proximity_shadow_log.jsonl`
- `shadow_logs/liquidity_distance_log.jsonl`
- `shadow_logs/displacement_events.jsonl`
- `shadow_logs/touch_count_gate_decisions.jsonl`
- `shadow_logs/sl_beyond_ob_decisions.jsonl`
- `shadow_logs/d1_bias_lag.jsonl`
- `shadow_logs/direction_emission_xau_audit.jsonl`
- `shadow_logs/regime_classifications.jsonl`
- `shadow_logs/structure_detector_divergences.jsonl`
- `shadow_logs/s79_side_aware_risk_context.jsonl`
- `shadow_logs/j46_j49_exit_comparator_audit.jsonl`
- `shadow_logs/regime_decay_outcome_join.jsonl`
- `shadow_logs/decision_layer_diagnostics_join.jsonl`
- `shadow_logs/mechanical_context_diagnostics_join.jsonl`
- `shadow_logs/ml_shadow_predictions.jsonl`
- `shadow_logs/ml_shadow_status.jsonl`
- `shadow_logs/account_truth_reconciliation_status.jsonl`
- `shadow_logs/broker_actual_r_audit.jsonl`
- `shadow_logs/exit_management_shadow_status.jsonl`
- `shadow_logs/sierra_confluence_source_status.jsonl`
- `shadow_logs/sierra_depth_enrichment_status.jsonl`
- `shadow_logs/sierra_depth_feature_snapshots.jsonl`
- `shadow_logs/databento_live_trigger_decisions.jsonl`
- `shadow_logs/databento_live_confluence.jsonl`
- `shadow_logs/databento_live_budget_ledger.jsonl`
- `shadow_logs/orderflow_primitives_status.jsonl`
- `shadow_logs/external_source_blocker_status.jsonl`
- `shadow_logs/proxy_blocker_status.jsonl`

Candidate-triggered logs must advance when candidates advance. Event-driven logs may remain quiet if no fill/exit/source trigger exists, but they must have an explicit waiting/status row when expected by the current LTO contracts.

### Layer 2 - Market Tape And Price-Action Follow

For each active symbol and each new M15 close, produce a compact tape read:

- session and minutes since session open,
- latest M15 OHLC and candle body/wick description,
- relationship to active OB/FVG/breaker/POI if present,
- relationship to prior session high/low, current KZ high/low, and obvious liquidity sweep areas if available,
- displacement status and direction,
- proximity to active candidate entry, SL, TP1/TP, and invalidation,
- whether price has entered, rejected, swept, displaced away from, or stalled inside the setup area,
- whether a production pending limit exists and whether broker/internal lifecycle agrees,
- whether shadow-only strategy families agree or disagree with production state,
- Sierra/Databento/source-status state for that symbol/proxy,
- cross-market agreement/divergence.

Every active check cycle must produce at least one market-intelligence note. If there is no new candidate, write what price did around the active session range, KZ high/low, open range, nearby POIs, displacement candles, liquidity sweeps, and correlated markets. If the system logs did not capture a visually important event, mark it `OPERATOR_AI_OBSERVATION` and specify the structured evidence that is missing.

Expired-POI watch rule: when `expired_poi_watch.enabled` is true, monitor the watch registry and `shadow_logs/expired_poi_revalidation.jsonl` for every owner-reapproved or watch-eligible expired setup. Treat statuses as shadow-only: `APPROACHING_ENTRY`, `TOUCHED_RR_DECAYED_NO_REARM`, `TOUCHED_SL_DISTANCE_TOO_TIGHT_NO_REARM`, `TOUCHED_REVALIDATION_ELIGIBLE_SHADOW`, `INSIDE_POI_SL_DISTANCE_TOO_TIGHT_NO_REARM`, `INSIDE_POI_REVALIDATION_ELIGIBLE_SHADOW`, `INVALIDATED_BY_SL`, and `EXPIRED_WATCH_MAX_AGE`. None of these statuses authorizes execution while `expired_poi_watch.execution_override_enabled` is false.

### Layer 2B - Quantitative Candidate And Shadow Scoreboard

Every active check cycle must keep a current scoreboard, not just a narrative read. The scoreboard must include:

- production truth: broker positions, broker orders, account equity, internal pending intents, and mismatches,
- raw candidate count, countable primary opportunities, duplicate active setups, rejected candidates, and `LIMIT_PLACED` rows,
- per-symbol, per-session, per-side, and per-outcome candidate counts,
- entry, SL, TP1, RR, side, status, and trade id for production limit intents and countable primary opportunities,
- path/fill status: broker-filled, internal still-pending, no fill, cancelled wrong-side, entry touched, entry missed, TP/SL area reached, M15 ambiguous, unresolved/in-flight,
- proxy-R and score-status by lane: live baseline, pending-limit lifecycle, V2/V2B, J46/J49, S79, FVG/OB confluence, and any other active mechanical/shadow strategy,
- ML/K55 status for each important candidate: prediction, probability/score if available, artifact/blocker state if not,
- Sierra/Databento/orderflow/source status, including exact blocker and whether rows are source-status only or interpretable,
- a separation between realized broker PnL, internal lifecycle evidence, synthetic/path proxy-R, and operator/AI hypotheses.

If a candidate is called "quality", define why using evidence: production status, countability, RR, path/fill state, source coverage, ML/shadow context, and whether it is duplicate or primary. Do not call a duplicate repeated setup a new trade.

Classify price-action observations with these event types:

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

Do not overstate. If the event is only visual/AI-observed and not yet logged by a structured script, mark `evidence_class=OPERATOR_AI_OBSERVATION` and `validation_status=HYPOTHESIS_ONLY`.

### Layer 3 - Cross-Market Awareness

At least once per active-KZ pass, scan for:

- NAS100 versus US30/YM: index continuation, divergence, opening drive, failed breakout, same-direction displacement.
- XAUUSD versus XAGUSD/GC/SI: metal agreement, silver lead/lag, gold-only defensive move, liquidity sweep mismatch.
- USDJPY and GBPJPY versus 6J: yen futures agreement, JPY cross split, proxy gap.
- GBPUSD versus 6B: cable agreement, London sweep, post-open drift.
- Gold versus indices: risk-on/risk-off split, simultaneous liquidity grabs, defensive rotation.
- Control context when available: CL, ZN, VIX/VXM rows are context/control only unless promoted later.

Cross-market notes should answer:

- Which market moved first?
- Did the proxy confirm the CFD/broker symbol?
- Did correlated markets break highs/lows together or diverge?
- Was there a session-timing reason?
- Did this create a candidate-quality warning, a missed-opportunity clue, or just context?

### Layer 4 - Source And Orderflow Context

Sierra and Databento should be used for understanding, not just storage. Monitoring must therefore record:

- Sierra `.depth`/`.scid` freshness and symbol/proxy class.
- Sierra depth feature status for each candidate: extracted, pending heavy scan, no proxy, blocked source definition, stale source.
- Databento trigger decision for each relevant candidate: not triggered, declared/waiting, license blocked, budget blocked, cooldown blocked, fetched/cached.
- Databento schema intent if triggered: `trades`, `mbp-10`, targeted `mbo`.
- Orderflow primitive status where available: thinness, depth imbalance, wall concentration, trades pressure, adverse-selection status, pull/add pressure if MBO exists.
- Whether source context supports, contradicts, or is unavailable for the candidate.

No orderflow note may become a live veto or entry trigger during monitoring. It can become a registered hypothesis for later validation.

### Layer 5 - ML And Strategy-Shadow Awareness

For each new candidate or meaningful path event:

- Check whether K55/ML shadow produced a status or prediction row.
- State whether ML is unavailable, waiting, source-blocked, target-version blocked, or produced observational output.
- Compare ML shadow direction/confidence/risk buckets to production outcome and mechanical shadow rows only as context.
- Do not treat ML as live advice.
- If ML repeatedly disagrees with production on a coherent event family, write a `MONITOR_HYPOTHESIS` item and require future outcome joins before action.

Also compare:

- production decision,
- J46/J49 comparator,
- S79 risk context,
- V2/V2b structural selector readiness,
- V3/pre-fill path readiness,
- FVG/OB confluence,
- pending-limit lifecycle truth,
- broker actual-R when available.

### Layer 6 - AI Observation Ledger

Every session must write a human-readable AI observation ledger. Suggested path:

```text
research/operations/AI_MARKET_MONITORING_OBSERVATIONS_YYYY-MM-DD.md
```

Each observation should use this template:

```text
## HH:MM UTC - SYMBOL - EVENT_TYPE

- Evidence class: OPERATOR_AI_OBSERVATION / FORWARD_SHADOW / INTERNAL_LIMIT_LIFECYCLE / etc.
- Candidate/trade ids: ...
- Session/timing: ...
- Price-action summary: ...
- Structured evidence checked: files/rows/scripts...
- Source/orderflow context: Sierra/Databento/MT5/proxy state...
- Cross-market context: ...
- Why it matters: ...
- Hypothesis status: HYPOTHESIS_ONLY / NEEDS_FORWARD_JOIN / EXPLAINED_BY_EXISTING_LOGIC / FALSE_POSITIVE
- Next evidence required: ...
- Promotion posture: NO_PROMOTION_VERDICT
```

Use this ledger for pattern discovery:

- opening-candle behavior,
- session high/low breaks,
- liquidity grabs,
- displacement timing,
- entry near-misses,
- missed TP runs,
- repeated L2 rejections that would have worked or failed,
- correlation-confirmed versus correlation-divergent moves,
- source-captured versus source-missing events,
- ML/strategy-shadow agreement families.

The ledger should be useful to a future research session without chat memory.

## Cadence

Active kill zone:

- Every 5 minutes: health pulse, candidate/path follow, pending-limit lifecycle, Sierra status-only enrichment, integrity/data-health if new candidate rows arrived.
- Every M15 close: full tape read for active symbols and any in-flight candidate/pending limit.
- Event-driven between candles: check immediately if price is near entry, SL, TP, prior KZ high/low, session open range, or if a pending limit lifecycle row changes.
- Every 30 minutes: owner update with health, new candidates, path events, source status, and market observations.
- Do not run read-only verifiers in parallel with writer/enrichment/backfill scripts. Writers first, then dependent audits, then verifiers.
- Do not stop at a clean pass. Continue to the next scheduled check or event trigger until final closeout is allowed by the hard persistence contract.

Between kill zones:

- Every 15 minutes: health pulse, stale-source checks, storage, watchdog, observer lanes.
- After a KZ closes: write a session mini-synthesis and update the AI observation ledger.

End of day:

- Run final candidate path follow, source enrichment, dependent audits, and final verifiers in that order.
- Produce a final report under `research/program_control/` or `research/operations/`.
- Separate incidents, false positives, market observations, hypothesis ledger, candidate/path outcomes, source blockers, and next triggers.
- Only after the final report is written may the monitoring objective be marked complete.

## Alert Severity

### Critical

Immediate safety or truth failure:

- MT5 disconnected/trade disabled in active KZ.
- Open broker position/order mismatch with GTOS state.
- In-KZ orchestrator dead and watchdog did not recover.
- Heartbeat stale beyond critical threshold during active KZ.
- Pending limit exists but lifecycle telemetry missing or contradictory.
- Shadow integrity/data-health `issues` show candidate identity conflict, malformed active JSONL, no-leak failure, or paid/order/AI-call violation.
- Sierra/Databento source marked available but rows prove stale/missing during an active source-dependent candidate.

### High

Important degradation or market event requiring focused observation:

- Candidate close to entry/SL/TP with stale source rows.
- Displacement against a live candidate.
- Liquidity grab plus immediate reversal around a candidate POI.
- Orderflow/source context contradicts the setup in a documented way.
- Cross-market divergence during a high-confluence candidate.
- ML or strategy shadow repeatedly disagrees on a coherent event family.

### Medium

Research-relevant pattern or limited operational issue:

- Repeated entry near-misses.
- Opening range behavior that repeats across symbols.
- Same L2 rejection family continues moving to target.
- Repeated source-not-captured for a high-value event type.
- Control-only context moves sharply but no direct candidate exists.

### Low

Cosmetic, stale non-critical report, expected waiting lane, or non-active source issue.

## Owner Update Format

Use short updates. During active monitoring include:

- current UTC/KL time and active KZ,
- system status: critical/high issues count,
- active positions/orders/pending intents,
- new candidates and path states,
- price-action events worth noticing,
- Sierra/Databento/source status if relevant,
- cross-market observation if relevant,
- verifier status and any source blockers,
- what you will watch next.

Example:

```text
07:45 UTC / 15:45 KL: London active. System health clean; no broker positions/orders. NAS100 pending limit is still no-fill, price has traded near TP area without touching entry, so this remains a missed-limit path, not a realized trade. Sierra NQ status is available; Databento live remains license-blocked. Watching whether the next M15 candle rejects the high or displaces again.
```

## Final Report Required Sections

- Overall system status.
- Production safety status.
- Process/watchdog/MT5/Sierra/tick/notification/storage status.
- Shadow-data integrity and semantic data-health status.
- Candidate and pending-limit lifecycle table.
- Market tape timeline by KZ.
- Price-action event ledger.
- Cross-market observations.
- Sierra/Databento/orderflow source status.
- ML/strategy-shadow observations.
- Incidents, false positives, and fixes/restarts.
- Open blockers and exact triggers.
- Hypotheses generated for later validation.
- `NO_PROMOTION_VERDICT`.
