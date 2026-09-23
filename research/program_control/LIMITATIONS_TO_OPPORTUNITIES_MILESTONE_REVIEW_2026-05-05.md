# Limitations To Opportunities Milestone Review - 2026-05-05

**Status:** owner-facing technical review  
**Scope:** LTO-001 through LTO-040, plus the LTO-031/LTO-032 source-unblocking extension  
**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Trading behavior impact:** no live entry/filter/risk/prompt/safety-gate/order behavior was promoted or changed by this review  

## Evidence Basis

This document is based on current repo artifacts, not chat memory.

Primary source files:

- `research/program_control/LIMITATIONS_TO_OPPORTUNITIES_ENGINEERING_PLAN_2026-05-05.md`
- `research/program_control/LIMITATIONS_TO_OPPORTUNITIES_QUEUE_STATE_2026-05-05.md` / `.json`
- `research/program_control/LIMITATIONS_TO_OPPORTUNITIES_COMPLETION_AUDIT_2026-05-05.md` / `.json`
- `research/operations/SHADOW_LOG_INTEGRITY_VERIFICATION_LTO_COMPLETION_2026-05-05.json`
- `research/operations/LIVE_SHADOW_DATA_HEALTH_AUDIT_LTO_COMPLETION_2026-05-05.json`
- `research/program_control/GTOS_DAILY_MONITORING_CHECKLIST_2026-05-05.json`
- `research/program_control/LTO031_LTO032_SOURCE_UNBLOCKING_AND_REPLAY_PLAN_2026-05-05.md` / `.json`
- `.context/LIVE_STATE.md`, regenerated 2026-05-05
- `.context/00_core/research_current_state.md`

Verified completion state:

- LTO items: `40`
- LIVE-FOLLOW rows mapped: `34 / 34`
- Completion audit status: `ACHIEVED_WITH_DOCUMENTED_EXTERNAL_BLOCKERS`
- Queue counts: `DONE=37`, `APPROVAL_BLOCKED=1`, `SOURCE_BLOCKED=2`
- Completion audit can mark goal complete: `true`
- Fresh shadow integrity verifier after latest candidate refresh: `OK_WITH_DOCUMENTED_WAITING_LANES`, `issues=[]`, `jsonl_rows=60831`
- Fresh semantic live-shadow data-health audit after latest candidate refresh: `OK_WITH_DOCUMENTED_LIMITATIONS`, `issues=[]`, `latest_candidates=51`
- Focused regression tests: `79 passed` across LTO-027 readiness, shadow-integrity contracts, opportunity lifecycle audit, and V2b pair-resolution audit.
- Safety posture across the LTO goal: `NO_PROMOTION_VERDICT`

## Executive Answer

The LTO work did not make a new live trading strategy. It built the research and intelligence spine that lets the system learn from what it is already seeing, without lying to itself.

Before this work, many lanes were in the dangerous middle state: rows existed, but a row existing did not prove it was fresh, joined, complete, usable, non-leaking, source-legal, or connected to outcomes. After this work, the system has a much more explicit distinction between:

- live AI candidate rows,
- AI-independent MSO rows,
- path-follow rows,
- pending-limit lifecycle truth,
- broker/account-history truth,
- synthetic path labels,
- Sierra/Databento/source status,
- orderflow primitives,
- K55/ML feature eligibility,
- approval blockers,
- source blockers,
- no-event states,
- verifier health.

The direct live system still trades from the same approved GTOS structure: OB/FVG/breaker, deterministic gates, AI evaluation, permissions, and execution. The LTO work improves the system indirectly by making every future research and promotion decision much better grounded. That matters because future improvements need clean evidence, not isolated anecdotes.

My honest assessment: this is a major infrastructure milestone, not a profitability proof. It moves the system much closer to a compounding research machine, but the current bottleneck is still clean forward labels, especially broker actual-R joined to candidate/opportunity variants. The biggest future lift can come from turning this richer capture into proven filters, timing improvements, ML features, and orderflow/context-aware decisions after enough forward evidence accumulates.

## What "Shadow Impact" Means

Shadow logs do not directly tell the live system to enter, reject, resize, or exit. Their impact is indirect but important:

1. They preserve point-in-time evidence.
2. They separate real broker outcomes from synthetic path outcomes.
3. They make each candidate explainable after the fact.
4. They let us compare AI, mechanical alternatives, V2/V3 structural ideas, orderflow, regime, and risk context on the same candidate IDs.
5. They feed K55/ML with versioned, as-of, provenance-tagged features.
6. They tell us when a feature is missing because the source was not captured, not because the setup was invalid.
7. They provide future promotion dossiers with sample counts, label classes, source freshness, cost/slippage, concentration, and no-leak proof.

That is the correct foundation for a stronger trading system. It does not guarantee profitability, but it reduces the chance that we promote a fake improvement or miss a real one.

## Current System Cycle

Current live/research cycle after the LTO work:

```text
MT5 broker feed / Sierra local files / Databento trigger status / shadow observer
    -> GTOS orchestrators and no-AI observer rows
    -> strategy_follow_evaluations.jsonl
    -> strategy_follow_candidates.jsonl
    -> candidate path, LTF path, V2b, prefill, FVG/OB, lifecycle rows
    -> account-truth, broker actual-R, slippage/cost, trade-index audits
    -> Sierra/Databento/orderflow/source-status joins
    -> decision diagnostics, mechanical context, regime/decay, S79/J46 comparators
    -> K55/ML shadow feature bundle and prediction/status rows
    -> integrity verifier, semantic data-health verifier, queue/checklist status
    -> future promotion dossier only if evidence gates pass
```

The most important design choice is that everything routes through stable identity:

- `candidate_id`
- `decision_time_utc`
- `asof_cutoff_utc`
- source/proxy/freshness status
- evidence class
- promotion verdict

This creates an audit trail from a market event to a candidate, from a candidate to its paths and logs, from paths to possible strategy variants, and from variants to real or synthetic labels.

## Future Paid/Live Data Cycle

If Databento live, macro feeds, options/gamma feeds, or other paid services are later approved and licensed, the target cycle is:

```text
GTOS candidate trigger
    -> registered live data request policy
    -> Databento/Sierra/public-source fetch with budget/source/legal checks
    -> pre-decision feature extraction only
    -> append-only confluence/source ledger
    -> candidate_id + decision_time join
    -> broker actual-R / lifecycle / cost join after outcome
    -> source-value review
    -> K55/ML feature update
    -> promotion dossier if sample and validation gates pass
```

The future live services should not become blind always-on spending. The intended aggressive use is event-triggered and value-max:

- fetch around real GTOS candidates,
- use historical credits for counterfactual replay windows,
- use Sierra local capture immediately,
- keep every source row joined to candidate/outcome evidence,
- measure whether the source improves entry timing, bad-condition vetoes, stop/invalidation efficiency, target/RR expansion, or ML quality.

For now, LTO-031/LTO-032 are constrained by a hard `$0` new external cash-spend rule. Existing Databento historical credits and existing Sierra files/access are allowed; new paid feeds require separate approval.

## Per-Task Ledger

### LTO-001 - AI-Independent MSO Evaluation Anchor

Limitation: AI candidate review was too dependent on terminal AI output, making it harder to study what the deterministic market-state engine saw at decision time.

Solution: build an AI-independent MSO/evaluation anchor from `strategy_follow_evaluations.jsonl`, joined to candidates through source hashes and timestamps.

Logged/utilized: `strategy_follow_evaluations.jsonl` plus `candidate_mso_snapshot_joins.jsonl`. These rows become the canonical decision-time context for mechanical/V2/V3/ML comparison without needing another AI call.

Impact: data infrastructure and ML substrate. It gives every later strategy test a stable market-state snapshot.

Boundary: verifier recorded `46` exact MSO joins and `3` documented missing joins in the completion evidence. Missing rows are documented, not fabricated.

### LTO-002 - AI Candidate Registry And External Confluence

Limitation: candidate rows existed, but downstream consumers could confuse absent confluence with silently missing data.

Solution: candidate registry audits now require candidate identity, decision time, geometry, framework, L2 state, and explicit Sierra/Databento/source status.

Logged/utilized: `strategy_follow_candidates.jsonl`, `candidate_registry_audit.jsonl`, plus confluence fields attached through Sierra/Databento status logs.

Impact: infrastructure spine. This is the durable root for every candidate-scoped join.

Boundary: still no source value claim from source presence alone.

### LTO-003 - Candidate Path Follow

Limitation: candidate outcome context was too shallow; it did not preserve the path from decision to entry/TP/SL/no-fill well enough.

Solution: path-follow rows track entry touch, TP/SL touch, near-miss, continuation without entry, same-candle ambiguity, and unresolved states.

Logged/utilized: `candidate_path_follow.jsonl`, `candidate_ltf_path_order.jsonl`, and path-aligned derived rows.

Impact: opportunity intelligence and future strategy evaluation. This is how the system learns whether missed candidates, pending limits, and alternative exits had useful behavior.

Boundary: same-candle ambiguity remains explicit when lower timeframe cannot resolve the order.

### LTO-004 - Opportunity Duplicate Lifecycle

Limitation: duplicate active setups could be accidentally counted as separate opportunities, inflating research conclusions.

Solution: duplicate-aware opportunity lifecycle states distinguish `COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY` from duplicate active setup evidence.

Logged/utilized: `live_candidate_opportunity_clusters.jsonl` and opportunity lifecycle audits.

Impact: research validity. The fresh data-health audit recorded `51` latest candidates but only `10` countable unique opportunities and `41` duplicate active setup rows.

Boundary: duplicates are still useful evidence; they are just not separate trade opportunities.

### LTO-005 - Pending-Limit Lifecycle Truth

Limitation: pending limit state could be lost or partially joined, making fill/no-fill, cancellation, expiry, and missed-move analysis unreliable.

Solution: lifecycle truth is audited through pending intent keys, final states, and join-backfill rows.

Logged/utilized: `pending_limit_lifecycle.jsonl`, `pending_limit_lifecycle_audit.jsonl`, `pending_limit_lifecycle_join_backfill.jsonl`.

Impact: execution/lifecycle intelligence. It tells us whether a candidate became an actual order, never filled, was cancelled, or was a no-fill that still moved.

Boundary: old rows that never captured enough identity remain documented limitations rather than reconstructed guesses.

### LTO-006 - V2b Forward Pair Resolution

Limitation: V2b ideas existed but were not accumulating clean forward evidence with actual/synthetic label separation.

Solution: V2b pairs and resolutions now join OB-boundary, J46, fixed-R, FVG, path, lifecycle, and ambiguity evidence.

Logged/utilized: `v2b_forward_pairs.jsonl`, `v2b_forward_pair_resolutions.jsonl`, `v2b_forward_pair_resolution_audit.jsonl`.

Impact: future strategy intelligence. This gives the project a fair way to evaluate V2b without forcing a live promotion.

Boundary: current labels are mostly `SYNTHETIC_PATH_R` or unresolved; they are not broker-realized validation.

### LTO-007 - V3 / Pre-Fill Delivery Path

Limitation: V3 and pre-fill delivery-path ideas could not be evaluated honestly because the exact decision-time fields were not always captured.

Solution: prefill rows now capture what is available at decision time and explicitly mark missing lock/reentry/FVG fields as source limitations.

Logged/utilized: `prefill_delivery_path.jsonl`, `prefill_delivery_path_resolutions.jsonl`, `prefill_delivery_path_audit.jsonl`.

Impact: future strategy design. This is the first step toward testing delivery-leg plus reversal-leg logic without post-event leakage.

Boundary: missing V3 historical fields remain `SOURCE_NOT_CAPTURED`; no V3 promotion exists.

### LTO-008 - FVG/OB Confluence And Disagreement

Limitation: FVG/OB agreement and disagreement were not structured enough to tell whether they are confirmation, separate setup families, or delivery/reversal sequencing.

Solution: confluence rows and resolution audits now track bucketed FVG/OB state, overlap, source capture status, and unresolved exact bounds.

Logged/utilized: `fvg_ob_confluence.jsonl`, `fvg_ob_confluence_resolutions.jsonl`, `fvg_ob_confluence_audit.jsonl`.

Impact: strategy intelligence. It turns discretionary structure questions into measurable candidate features.

Boundary: exact FVG lock state and some bounds remain incomplete for historical rows.

### LTO-009 - Context/Control Ledger For CL/ZN/VIX/VXM

Limitation: context instruments could be accidentally interpreted as validation of the traded symbol.

Solution: context/control rows are classified as `CONTROL_ONLY` or cross-instrument context with explicit evidence classes.

Logged/utilized: `context_control_ledger.jsonl`, `context_control_audit.jsonl`, and observer hardening status.

Impact: market-awareness research. Useful for context and future hypotheses, not direct signal validation.

Boundary: CL/ZN/VIX/VXM source fields remain context/control unless a separate source contract and validation lane are built.

### LTO-010 - Databento Targeted Live Confluence

Limitation: Databento was either blocked or at risk of being treated too conservatively or too broadly.

Solution: owner-approved event-trigger policy with symbols, schemas, spend caps, cooldown, env/API gates, confluence rows, and budget ledger.

Logged/utilized: `databento_live_trigger_decisions.jsonl`, `databento_live_confluence.jsonl`, `databento_live_budget_ledger.jsonl`.

Impact: market-awareness and orderflow infrastructure. It is the canonical API lane for futures proxy confluence when licensed.

Boundary: Databento live is license-blocked for GLBX live data. The collector should not start implicitly; it requires env/API/license/trigger/cap success.

### LTO-011 - NAS100/NQ Orderflow Adverse-Selection Diagnostic

Limitation: NAS100 could not tell whether bad candidates were associated with thin depth, unfavorable pressure, or liquidity pull.

Solution: NAS100/NQ adverse-selection readiness rows register what orderflow features are needed and how they will join to candidates and broker actual-R.

Logged/utilized: `nas100_orderflow_adverse_selection_status.jsonl`, Databento trigger/confluence logs, Sierra depth rows where present.

Impact: future entry-timing and veto research. It targets the most actionable orderflow question first.

Boundary: current NAS100 broker actual-R coverage is sparse; no live filter or risk modifier is allowed.

### LTO-012 - Sierra Local Depth Confluence

Limitation: Sierra `.depth` files existed, but local depth could stall, be too large, or be interpreted without source/proxy quality.

Solution: file-size guarded background depth enrichment and source/status rows.

Logged/utilized: `sierra_confluence_source_status.jsonl`, `sierra_depth_feature_snapshots.jsonl`, `sierra_depth_enrichment_status.jsonl`.

Impact: market-awareness and orderflow substrate. Sierra becomes immediately useful for local depth features where proxy/parity allows.

Boundary: feature extraction can be deferred for large files; missing proxy rows are explicitly blocked, not inferred.

### LTO-013 - Sierra Source/Parity Registry

Limitation: Sierra features could create false confidence if the broker symbol, futures proxy, and parity status were not explicit.

Solution: Sierra registry maps broker symbol to Sierra symbol, source file, proxy class, parity status, and allowed use.

Logged/utilized: `sierra_proxy_registry_status.jsonl`, `sierra_confluence_source_status.jsonl`, parity reports.

Impact: source reliability. It prevents treating a weak proxy as direct market truth.

Boundary: source-specific blockers remain for some symbols, especially direct GBPJPY and SI source/depth definition.

### LTO-014 - GBPJPY Sierra/Databento Proxy Gap

Limitation: GBPJPY has no direct clean futures depth proxy equivalent in the current registered setup.

Solution: the lane is now a documented proxy-design problem instead of a vague missing-source problem.

Logged/utilized: `gbpjpy_proxy_gap_status.jsonl`.

Impact: source governance. It stops accidental use of irrelevant depth data while keeping 6J/6B two-leg ideas available for future design.

Boundary: no GBPJPY orderflow confluence is claimed.

### LTO-015 - Broker Actual-R, Slippage, Cost, And Exit Accounting

Limitation: local R/path rows and notification PnL could be mistaken for broker-realized truth.

Solution: read-only MT5 account-history export plus broker actual-R audit. Close-side slippage telemetry was added to `execution.py` and `slippage_shadow_logger.py` with fail-open behavior and no order-decision effect.

Logged/utilized: `data/account_history/mt5_deals_2026-04-27_2026-05-05.jsonl`, `broker_actual_r_audit.jsonl`, `slippage.jsonl`, `daily_pnl_history.jsonl`, close-side fields such as close reason, partial close, time in trade, MT5 deal ID, commission status, and swap status.

Impact: outcome truth and execution-quality intelligence. It is the bridge between shadow candidates and real broker results.

Boundary: latest LTO-015 report recorded `22` MT5 deal rows, `58` audit rows available, `3` account-history-realized actual-R rows, and `51` live-R artifact rows. Actual-R claims are allowed only for account-history-realized rows.

### LTO-016 - J46-J49 Exit Policy Comparator

Limitation: exit-policy comparison could be confused with all candidates rather than filled trades or path-only context.

Solution: J46/J49 comparator rows now join to broker actual-R where available and keep no-fill/path-only rows separate.

Logged/utilized: `j46_j49_shadow_outcomes.jsonl`, `j46_j49_exit_comparator_audit.jsonl`.

Impact: future exit policy evaluation. It lets us compare actual policy vs hypothetical exits without changing execution.

Boundary: actual-R comparison requires `ACCOUNT_HISTORY_REALIZED`; synthetic path labels remain context.

### LTO-017 - S79 / Side-Aware Compounding Context

Limitation: side-aware/risk-policy context could be lost when reviewing candidates and fills.

Solution: candidate and fill rows carry risk-policy context and side-aware status without changing risk.

Logged/utilized: `s79_side_aware_risk_context.jsonl`, `daily_pnl_history.jsonl`, candidate rows, side-aware state.

Impact: risk/research context. It helps review whether side/risk policy interacts with outcomes.

Boundary: no risk parameters were changed by this lane.

### LTO-018 - Regime Classifier And Monthly Decay

Limitation: regime/decay information existed but was not consistently joined to candidate/fill outcomes.

Solution: regime and OB-continuation/decay context are joined into candidate and outcome rows.

Logged/utilized: `regime_classifications.jsonl`, `ob_continuation_daily.csv`, `regime_decay_outcome_join.jsonl`.

Impact: market-state awareness. It lets research ask whether setups behave differently by regime and whether edge is decaying.

Boundary: regime rows are shadow context, not automatic vetoes.

### LTO-019 - Decision-Layer Diagnostics

Limitation: accept/reject behavior could not always be explained from deterministic diagnostics.

Solution: joins candidate features, D1 lag, direction emission, SL beyond OB, touch-count, and L2 reason coverage.

Logged/utilized: `decision_layer_diagnostics_join.jsonl`, `candidate_features_log.jsonl`, `d1_bias_lag.jsonl`, `direction_emission_xau_audit.jsonl`, `sl_beyond_ob_decisions.jsonl`, `touch_count_gate_decisions.jsonl`.

Impact: explainability and debugging. It helps distinguish AI behavior, deterministic gate behavior, and data capture problems.

Boundary: diagnostic rows are not new gates.

### LTO-020 - Mechanical Baselines, Proximity, Liquidity, Displacement, Structure Divergence

Limitation: useful diagnostics were scattered across logs and not candidate-joined.

Solution: mechanical context joiner brings dumb baseline, OB proximity, liquidity distance, displacement, and structure divergence into one candidate-scoped context.

Logged/utilized: `mechanical_context_diagnostics_join.jsonl`, `dumb_baseline_hypotheticals.jsonl`, `proximity_shadow_log.jsonl`, `liquidity_distance_log.jsonl`, `displacement_events.jsonl`, `structure_detector_divergences.jsonl`.

Impact: feature discovery and ML substrate. It creates comparable explanatory variables for why a candidate was good or bad.

Boundary: discovery-only until validated.

### LTO-021 - Exit-Management Shadows: BE, Partial Close, Time In Trade

Limitation: empty exit-management logs could mean either no event or broken capture.

Solution: explicit no-event/status rows distinguish no fill, no BE trigger, no partial trigger, no close event, and missing capture.

Logged/utilized: `exit_management_shadow_status.jsonl`, plus event logs when they exist: `be_shadow_log.jsonl`, `partial_close_shadow_log.jsonl`, `time_in_trade.jsonl`.

Impact: execution/exits research. It prevents false alarms and prepares future exit policy comparisons.

Boundary: current completion evidence shows no qualifying exit events in the audited latest candidates; that is documented no-event, not failure.

### LTO-022 - Session Volatility And US30 Sweep Divergence

Limitation: event monitors could appear stale or broken during quiet periods.

Solution: status rows and watchdog coverage show event/no-event freshness.

Logged/utilized: `session_volatility_log.csv`, `sweep_divergence_log.csv`, `session_volatility_sweep_status.jsonl`.

Impact: session context and no-event proof.

Boundary: shadow/context only.

### LTO-023 - K55 / ML Shadow

Limitation: K55 was blocked because the K54/K55 target line needed refresh and stale K54 artifacts should not be blindly wired.

Solution: K55 target and feature bundle were registered, read-only shadow rows were written, and inference stays disabled until a matching model artifact exists.

Logged/utilized: `ml_shadow_predictions.jsonl`, `research/ml_program/shadow/K55_TARGET_FEATURE_REGISTRY_2026-05-05.md`, `k55_shadow_registry_2026-05-05.json` policy.

Impact: ML substrate. Current K55 rows join LTO-001..020 features, Sierra/Databento/orderflow status, regime, diagnostics, account truth, mechanical context, S79, and J46/J49.

Boundary: `51` rows computed, `0` prediction-computed rows, `0` inference-enabled rows. The model artifact is missing by design; most rows are `ML_SHADOW_FEATURE_BUNDLE_READY_MODEL_ARTIFACT_PENDING`, with partial rows when optional source rows are not yet present.

### LTO-024 - Component 3B / Tool Grounding / Reflexion

Limitation: Component 3B/tool-grounding/Reflexion could add AI cost and behavior drift if activated casually.

Solution: approval dossier and static no-activation checks were written. No AI call or wiring was added.

Logged/utilized: `lto_blocked_lane_status.jsonl`, `LTO024_COMPONENT3B_TOOL_GROUNDING_REFLEXION_APPROVAL_DOSSIER_2026-05-05.md`.

Impact: governance. Keeps a future idea alive without smuggling it into production.

Boundary: still `APPROVAL_BLOCKED`.

### LTO-025 - Account/PnL Truth And Evidence-Class Separation

Limitation: dollar PnL, R, local aggregates, notification values, and broker actuals could be conflated.

Solution: evidence-class reconciliation separates actual dollars, actual R, local PnL aggregates, local risk-dollar projections, and none/no label.

Logged/utilized: `account_pnl_truth_reconciliation.jsonl`, `account_truth_reconciliation_status.jsonl`, MT5 account-history export, daily PnL rows.

Impact: truth discipline. It makes every performance claim state its evidence class.

Boundary: report recorded `15` reconciliation rows, `13` actual-dollar claim allowed rows, and only `2` actual-R claim allowed rows.

### LTO-026 - Trade Index Staleness And Lifecycle Completeness

Limitation: `_trade_index.json` and trade-record lifecycle completeness could be stale or incomplete.

Solution: trade inventory index and lifecycle audit check trade records and pending lifecycle coverage.

Logged/utilized: `trade_index_lifecycle_audit.jsonl`, `knowledge_base/index/trade_record_inventory_index_2026-05-05.json`, pending lifecycle logs.

Impact: data reliability. Prevents stale trade inventory from contaminating live/OOS counts.

Boundary: known lifecycle blockers are documented, not hidden.

### LTO-027 - V2 Structural Oracle / As-Of Selector

Limitation: structural selector ideas could look promising but lack broker-actual sample floor, lifecycle truth, cost/slippage, concentration, exact metadata, and dossier readiness.

Solution: V2 selector readiness audit creates a source-driven readiness row instead of wiring selector logic.

Logged/utilized: `v2_structural_selector_readiness.jsonl`, V2b rows, broker actual-R audit, MT5 export evidence.

Impact: promotion discipline. It says exactly why the selector is not promotable yet.

Boundary: current computed verdict is `NOT_READY`; MT5 account history helps filled broker outcomes but cannot reconstruct unfilled shadow alternatives or missing selector metadata.

### LTO-028 - XAUUSD Same-Market Structural Path Extension

Limitation: XAUUSD same-market extension could accidentally open outcomes before the cohort/source status was frozen.

Solution: preregistered source-status lane with outcome slices closed at registration.

Logged/utilized: `xauusd_same_market_extension_status.jsonl`, same-market/proxy source registry files.

Impact: future data expansion. It prepares XAUUSD same-market and GC/MGC proxy evidence safely.

Boundary: source-status only; no replay outcome opened.

### LTO-029 - ES/MES Strategy-Cohort Pre-Registration

Limitation: ES/MES could become an accidental post-hoc strategy cohort.

Solution: source mapping, session windows, strategy family, evidence class, and no-lookahead rules were frozen before outcomes.

Logged/utilized: `es_mes_preregistration_status.jsonl`, ES/MES strategy cohort registry.

Impact: future expansion governance. It creates a clean entry point for equity-index proxy/control research.

Boundary: preregistration/source-status only.

### LTO-030 - 6B Sampling Alignment And SI Depth Definition

Limitation: GBPUSD/6B and XAGUSD/SI depth could be misread because sampling alignment and depth definitions differed by source.

Solution: 6B gets a common-second alignment policy; SI remains source/depth-definition blocked where parity is not good enough.

Logged/utilized: `sierra_6b_si_depth_policy_status.jsonl`, Sierra proxy/depth status logs.

Impact: source quality. Prevents bad cross-source comparisons from entering features.

Boundary: GBPUSD/6B policy is usable with caution; SI remains blocked until source semantics are fixed.

### LTO-031 - External Feed Blockers

Limitation: macro/history/external feed blockers were vague.

Solution: source-readiness artifact lists source families and required access/schema/publication/cache/no-lookahead contracts.

Logged/utilized: `LTO031_EXTERNAL_FEED_SOURCE_READINESS_2026-05-05.md`, `lto_blocked_lane_status.jsonl`, plus the source-unblocking extension plan.

Impact: future macro/history intelligence. It tells exactly what must be sourced before FX COT, BIS, Fed/FRED, KMW fix, H-K-M, pre-2022 OHLCV, or pre-2024 tick/LOB can influence research.

Boundary: still `SOURCE_BLOCKED`. Current continuation rule is `$0` new external cash spend for now.

### LTO-032 - Options/Gamma, VRP, FlashAlpha Basic GEX

Limitation: options/gamma/VRP/GEX context could be useful but lacks legal timestamped historical/source contracts.

Solution: source-readiness artifact separates FlashAlpha forward context from official/historical GEX, VIX1D/VIX9D, and VRP blockers.

Logged/utilized: `LTO032_OPTIONS_GAMMA_SOURCE_READINESS_2026-05-05.md`, `lto_blocked_lane_status.jsonl`, source-unblocking extension plan.

Impact: future volatility/gamma market-awareness lane.

Boundary: still `SOURCE_BLOCKED`; no paid source is allowed for now.

### LTO-033 - X-1/X-2/X-3 Imbalance / Meta-Order-Flow Primitives

Limitation: orderflow ideas were too broad and not measurable.

Solution: primitive registry defines footprint delta/absorption, stacked imbalance, depth thinness/walls, liquidity pull/depletion, queue behavior, and volume profile context with allowed schemas and roles.

Logged/utilized: `orderflow_primitives_status.jsonl`, `LTO033_ORDERFLOW_PRIMITIVES_2026-05-05.md`, Databento/Sierra source status.

Impact: future orderflow intelligence. It turns the "ICT to orderflow" hypothesis into measurable roles: entry timing, bad-condition veto, stop/invalidation efficiency, and target/RR expansion.

Boundary: no primitive is promoted, no threshold selected, no live filter changed.

### LTO-034 - Live Monitoring Goal / Runbook Persistence

Limitation: monitoring depended too much on chat memory and manual continuity.

Solution: daily checklist and runbook commands preserve what to run, expected lanes, restart policy, and blocker handling.

Logged/utilized: `GTOS_DAILY_MONITORING_CHECKLIST_2026-05-05.json`, `FORWARD_CAPTURE_MONITORING_RUNBOOK_2026-05-04.md`.

Impact: operations reliability. Future sessions can resume from files.

Boundary: checklist is not a daemon by itself; commands still need scheduled/goal/operator execution unless separately automated.

### LTO-035 - No-AI MSO Shadow Observer Instruments

Limitation: non-orchestrator instruments needed safe observation without AI or execution drift.

Solution: source registry and hardening status for EURUSD, GER40, UK100 active observer lanes and inactive/context/pre-registered lanes.

Logged/utilized: `shadow_observer_status.jsonl`, `shadow_observer_hardening_status.jsonl`, `strategy_follow_evaluations.jsonl`, `LTO035_SHADOW_OBSERVER_SOURCE_REGISTRY_2026-05-05.md`.

Impact: opportunity expansion. Lets the system observe tested non-orchestrator instruments without trading them.

Boundary: process check found the running shadow observer process was started before later observer-code commits; restart is the clean reload step for latest observer code.

### LTO-036 - Watchdog, Canary Skip, And Restart Governance

Limitation: canary skip and restart state could be confusing or look like failure.

Solution: governance status rows classify owner skip, expiry, cache freshness, and restart state.

Logged/utilized: `canary_restart_governance_status.jsonl`, daily checklist, watchdog verification.

Impact: operational safety. It makes cost-control overrides visible without weakening safety.

Boundary: does not fake canary pass rows.

### LTO-037 - Notification Queue Dead-Zone Policy

Limitation: notification worker shutdown during dead zones could be misclassified as a broken alert path.

Solution: dead-zone status labels distinguish expected stop, unexpected stop, queue empty, and running states.

Logged/utilized: `notification_queue_dead_zone_status.jsonl`.

Impact: operations clarity. Prevents unnecessary restarts during expected dead-zone cleanup.

Boundary: notification behavior is not changed into a trading signal.

### LTO-038 - Storage, Retention, And Non-Overwrite

Limitation: Sierra/depth and temp files can create storage pressure; unsafe cleanup can destroy evidence.

Solution: retention classes and dry-run storage audit with delete allowlist.

Logged/utilized: `storage_retention_status.jsonl`, `LTO038_STORAGE_RETENTION_STATUS_2026-05-05.md` / `.json`.

Impact: data preservation. Protects raw source and evidence logs while identifying safe cleanup candidates.

Boundary: dry-run/control lane unless a separate deletion action is approved and path-safe.

### LTO-039 - Shadow Log Integrity And Semantic Data Health

Limitation: schema checks alone were not enough; a log can be well-formed but semantically wrong.

Solution: verifier now checks lane-specific semantics: identity, path geometry, lifecycle vs candidate outcome, source interpretation, duplicate counts, stale modes, blocked lanes, and action-required rows.

Logged/utilized: `verify_shadow_log_integrity.py`, `audit_live_shadow_data_health.py`, completion verifier reports.

Impact: quality control. This is one of the highest-leverage improvements because it detects silent corruption before research conclusions are made.

Fresh verification fix: during this review, a moving live-candidate window exposed a verifier/tooling edge case. Intermediate action-required audit rows can intentionally lack dependency-derived fields, and the LTO-027 readiness row-key needed to include all source-count inputs compared by the verifier. The tooling was patched and covered by the focused regression suite.

Boundary: verifier warnings/documented limitations are not promotions.

### LTO-040 - Research Queue / Master Backlog Integration

Limitation: work could duplicate, reopen stale items, or miss follow-up rows after context compaction.

Solution: queue state maps all 40 LTO items to all 34 LIVE-FOLLOW rows, with statuses and blocker artifacts.

Logged/utilized: `LIMITATIONS_TO_OPPORTUNITIES_QUEUE_STATE_2026-05-05.md` / `.json`.

Impact: project control. It keeps the LTO program complete and resumable.

Boundary: future work should append new LTO IDs rather than mutating the completed milestone.

## Current Hook And Restart Status

Verified process and source status on 2026-05-05:

- Production orchestrator processes for XAUUSD, USDJPY, GBPJPY, US30_cash, GBPUSD, XAGUSD, and NAS100 were started between `2026-05-05 07:46` and `08:01` local time. This is after the `3f85e401` broker actual-R / close-side slippage telemetry commit at `2026-05-05 06:47 +0800`, so the current production processes should have that execution telemetry code loaded.
- Heartbeats were fresh for sampled XAUUSD and NAS100.
- SierraChart process `SierraChart_64` was running, and `.depth` / `.scid` files showed fresh 2026-05-05 writes in local Sierra folders.
- The Databento live collector process was not running in the process query. That is correct unless a registered trigger, env/API key, live license, cooldown, and budget cap all pass.
- The no-AI shadow observer process was created on `2026-05-04 14:04`, before later shadow observer code/hardening commits. A shadow-observer restart is recommended to load the latest observer code. This is not a production trading restart and does not affect order placement.

Restart policy:

- Production orchestrators: no broad restart required from this document. Restart only after future additive capture code changes, verified active-KZ failure, or explicit operator decision.
- Shadow observer: restart recommended to load latest observer code/hardening.
- Sierra: do not restart unless capture stalls or chartbook/source setup changes require operator action.
- Databento: do not start live collector implicitly; live license is still blocked.
- Daily LTO/checklist scripts: many lanes are batch/backfill/verifier commands, not always-on daemons. They must be run by the monitoring checklist, scheduled job, or goal session.

## Scores And Confidence

These scores are engineering/readiness scores, not a promise of future profit.

| Area | Score | Confidence | Why |
|---|---:|---|---|
| Core live trading safety and deterministic gates | 7.5/10 | Medium-high | Existing gates, watchdog, heartbeat, permissions, account checks, and emergency rules are strong; forward edge still needs live confirmation. |
| Candidate identity and audit spine | 8.5/10 | High | 51 latest candidates have broad candidate-driven coverage, stable IDs, registry/path/confluence/lifecycle audits, and zero data-health issues. |
| Path and opportunity intelligence | 8.0/10 | High | Path, LTF, duplicate, V2b, prefill, FVG/OB, and mechanical rows are joined. Remaining weakness is exact missing historical lock metadata. |
| Broker/account truth | 6.5/10 | Medium | Read-only MT5 export and account-history evidence classes exist, but actual-R sample size is sparse and not all variants are candidate-linked. |
| Execution/slippage/cost telemetry | 7.0/10 | Medium | Entry and close-side slippage telemetry exists and production processes should load it; commission/swap often still require account-history join. |
| Sierra local orderflow/source layer | 6.5/10 | Medium | Sierra process/files are live and feature rows exist; NQ/YM/GC areas are useful, but some proxies and SI/6B semantics require caution. |
| Databento orderflow layer | 5.0/10 | Medium | Policy/collector/cost ledgers are engineered; live data is license-blocked and NAS100 actual-R labels are sparse. Historical credits can still add replay value. |
| Orderflow primitive design | 6.0/10 | Medium | Primitive registry is strong; stacked imbalance, VAH/VAL, and live MBO remain source/license/cost blocked. |
| K55/ML shadow substrate | 6.0/10 | Medium | Feature bundle is strong and joins many sources; no model artifact is active and labels are mostly synthetic/path context. |
| Strategy expansion/preregistration discipline | 7.5/10 | High | ES/MES, XAUUSD same-market, observer lanes, V2 selector readiness, and external sources are preregistered or blocked cleanly. |
| Verifier/data-health infrastructure | 8.5/10 | High | Integrity and semantic data-health verifiers catch many silent failure classes and currently report no issues. |
| Promotion readiness of new ideas | 3.0/10 | High | Intentionally low. The project has many promising lanes, but no LTO lane produced a promotion dossier or validated live filter. |

Overall current state: `7/10` as a research/operating system, `5/10` as a proven adaptive/profit-improving machine, and `3/10` for immediate promotion of new LTO-derived trading logic. That split is healthy: the infrastructure is ahead of the evidence, and the promotion bar is still doing its job.

## How Close Are We To The North Star?

The north star is a system that finds good opportunities, understands market condition, executes safely, learns from outcomes, and improves across data, strategy, execution, and ML.

Current position:

- Opportunity finding: good foundation, but still too dependent on existing GTOS structure until orderflow/regime/ML features prove incremental value.
- Data capture: much stronger after LTO; still needs more automation cadence and fewer source blockers.
- Market awareness: materially improved in structure/path/regime/Sierra-status terms; orderflow and macro/gamma are not fully alive yet.
- Execution intelligence: improved with account-history and close-side telemetry; still needs more fills to evaluate costs and exits.
- ML: better substrate, but not yet a live model advantage.
- Validation discipline: strong. This is the best-developed part of the project after LTO.

My view: the project is not yet "up there" as a fully adaptive, deeply orderflow-aware, ML-enhanced trading system. It is much closer than before because the missing layer was not another rule; it was the infrastructure to know which rules actually help. The next level is converting this capture into measured lift on forward broker-realized outcomes.

## Biggest Open Doors

1. Broker actual-R sample growth
   - Most important blocker. Without more account-history-realized labels, strategy/ML/orderflow improvements cannot be promoted cleanly.

2. Databento historical-credit replay
   - Use existing credits on predeclared candidate windows to test what live Databento would have added, especially NAS100/NQ depth/adverse-selection.

3. Sierra footprint and volume-profile conversion
   - Current Sierra depth is useful; next value is `.scid` footprint-style bid/ask volume, delta, profile POC/HVN/LVN, and eventually VAH/VAL if source semantics are frozen.

4. K55 model artifact
   - The feature substrate is ready. A real K55 model artifact still needs target-compatible training, no-leak checks, and a shadow-only inference registry.

5. V2b/V3 structural validation
   - The forward rows exist, but exact source fields and actual broker labels are still limiting. This is one of the most important strategy research lanes.

6. Exit policy and cost accounting
   - Close-side telemetry is in place. More actual fills are needed to evaluate BE, partials, J46/J49, time-in-trade, commission, swap, and slippage impact.

7. LTO-031/LTO-032 source-unblocking
   - Free/public macro and volatility sources should be implemented first with `$0` new spend; paid sources stay deferred.

8. Shadow observer reload and cadence automation
   - Observer code should be restarted to load the latest changes. Daily checklist commands should eventually become a scheduled or supervised cadence, not manual memory.

## What I Would Prioritize Next

1. Keep the daily LTO monitoring checklist running so the rows stay fresh.
2. Restart the no-AI shadow observer at a safe moment to load latest observer code.
3. Implement LTO-031/LTO-032 free/public source contracts under `$0` new spend.
4. Use existing Databento historical credits only for predeclared replay windows with cost caps.
5. Build Sierra `.scid` footprint/profile feature extraction around existing candidates.
6. Build the K55 model artifact only after feature/target/no-leak tests are green.
7. Review every block of new broker actual-R rows, not on a fixed one-month wait.
8. Do not promote any LTO-derived filter until a separate promotion dossier proves sample size, concentration, no-leak, cost, and actual-R evidence.

## Bottom Line

The LTO goal converted a long list of limitations into a structured evidence machine. The system is now much better at capturing what happened, why it happened, what source was available, what label class is valid, and what is still blocked.

That is the right path to a stronger and more profitable system, but it is not the same as already having proven a stronger live strategy. The next milestone is evidence conversion: use the improved capture stack to find which orderflow, regime, ML, path, exit, and source features actually improve broker-realized outcomes, then promote only the ones that survive strict validation.
