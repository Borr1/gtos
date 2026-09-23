# Next Improvements Right-Way Execution Plan - 2026-05-06

Status: owner-facing execution plan  
Mode: research, operations, and evidence-building first  
Promotion verdict: `NO_PROMOTION_VERDICT`  
Live trading behavior impact of this plan: none  

## Objective

Turn the May 5 monitoring findings into a disciplined work program that improves GTOS the correct way: clear evidence, no guessing, no hidden live behavior changes, no promotion from anecdotes, and every ambiguity pursued until it is answered, documented as externally blocked, or split into a sharper question.

This plan covers the next improvements proposed from the May 5 deep-dive:

1. Continuation/no-retrace shadow strategy.
2. Richer `m15_choch_exists` L2 rejection diagnostics.
3. XAGUSD fresh-OB late-NY opportunity tracking.
4. No-AI shadow observer restart and observer state hardening.
5. NAS100/US30 direct side-probe failure diagnosis.
6. Post-window heartbeat/process lifecycle review.
7. Sierra `.scid` footprint/profile extraction.
8. Databento historical-credit replay under cost caps.
9. K55 model artifact path.
10. Internal pending-limit telemetry clarity and possible native-pending design review.
11. Broker actual-R sample growth and claim discipline.

## Non-Negotiable Rules

- No live prompt, risk, safety-gate, execution, or order-placement behavior changes without explicit owner approval.
- All strategy work starts shadow-only.
- All new hypotheses are preregistered before outcome review.
- Synthetic path labels, no-fill labels, and broker actual-R labels stay separate.
- Duplicate active setup rows are never counted as independent opportunities.
- Every source feature must carry legal/access status, source freshness, as-of cutoff, no-leak status, and cost status.
- If an ambiguity remains, the deliverable must say exactly what is unknown and what evidence would resolve it.
- Every meaningful deliverable is a file and a commit.

## Definition Of Done For Each Workstream

Each workstream is done only when it has:

- A source/evidence inventory.
- A written hypothesis or operational question.
- A no-live-impact boundary.
- Implementation or audit artifacts, if code is needed.
- Tests or verifier updates for any code/data contract.
- A result artifact with counts, limitations, and next actions.
- A final `NO_PROMOTION_VERDICT` unless a separate owner-approved promotion dossier exists.

## Phase 0 - Workspace And Baseline Control

Purpose: establish a clean baseline before deeper work.

Actions:

- Regenerate `.context/LIVE_STATE.md`.
- Commit the current May 5 monitoring, LTO, shadow-log, and owner-synthesis artifacts in coherent groups.
- Confirm `git status --short` is clean after commits except for any intentionally ignored/live-runtime file that must remain uncommitted.
- Record any uncommitted runtime files that should not be tracked.

Acceptance:

- Relevant artifacts are committed.
- No unrelated changes are reverted.
- Workspace state is understandable and reproducible.

## Phase 1 - Operational Integrity First

These items protect evidence collection and process behavior. They do not change trading logic.

### 1A. No-AI Shadow Observer Restart And Reload Proof

Question:

- Is the running no-AI shadow observer using the latest observer hardening code?

Actions:

- Inventory current observer processes, run IDs, code timestamps, and latest observer status rows.
- Define a safe restart procedure that cannot place trades or call AI.
- Restart only the no-AI observer, not production orchestrators, unless separately justified.
- After restart, verify fresh `shadow_observer_status.jsonl` and `shadow_observer_hardening_status.jsonl` rows show the new run ID and no action-required status.

Acceptance:

- Observer restart proof artifact exists.
- `verify_shadow_log_integrity.py` and `audit_live_shadow_data_health.py` remain clean.
- No AI/canary/order/paid-data counters increment.

### 1B. Post-Window Heartbeat Lifecycle Review

Question:

- Why did XAUUSD and NAS100 heartbeats remain alive after the configured `17:00` NY end, and is that expected process behavior or a watchdog lifecycle bug?

Actions:

- Read current orchestrator session loop, heartbeat writing, KZ end, timeout-trail, and process shutdown/watchdog logic.
- Compare configured session windows to observed May 5 heartbeat rows and process IDs.
- Build a small read-only audit script or report if current logs do not make the reason obvious.
- Do not change process lifecycle until the intended behavior is proven from code and logs.

Acceptance:

- Root cause classified as expected, benign but noisy, or bug.
- If bug, implement a narrow lifecycle/telemetry fix with tests.
- If expected, update monitoring docs so future sessions do not treat it as a trading anomaly.

### 1C. NAS100/US30 Direct Side-Probe Failure

Question:

- Why do direct read-only probes fail for NAS100/US30 while tick capture and broker truth stay healthy?

Actions:

- Identify exactly which probe command/API path failed.
- Compare broker symbols: `NAS100`, `NDX100`, `US30_cash`, `US30.cash`, and current config symbol mappings.
- Check whether failure is symbol selection, MT5 terminal state, side-process API contention, stale handle, timeout, or account/symbol availability.
- Write a small read-only diagnostic if needed.

Acceptance:

- Failure class is known.
- Fix is either implemented with tests or explicitly documented as environment/operator blocked.
- No trading path changes are made.

### 1D. Pending-Limit Telemetry Clarity

Question:

- Are `LIMIT_PLACED` rows too easy to misread as broker-resting native pending orders?

Actions:

- Inventory every artifact/notification/report field that uses `LIMIT_PLACED`.
- Confirm current semantics from `src/components/execution.py`: internal candle-polled pending intent, not native MT5 pending.
- Decide whether to add additional telemetry fields such as `pending_order_mode=INTERNAL_CANDLE_POLLED_INTENT`, `broker_pending_order_created=false`, and `mt5_order_ticket=null`.
- Do not rename historical outcomes without migration planning.

Acceptance:

- New rows, reports, and audits make internal-intent versus broker-order state unambiguous.
- Existing historical joins remain backward compatible.
- Tests cover the new clarity fields if implemented.

## Phase 2 - Candidate/Entry Intelligence

These items address the biggest May 5 market insight: direction can be right while the retest entry is never touched.

### 2A. Continuation/No-Retrace Shadow Strategy

Hypothesis:

- Some candidates that reach TP area without touching the limit entry represent a tradable continuation class, not merely missed retests.

Initial cohort:

- Candidate path label: `continued_without_entry_touch_to_tp_area`.
- May 5 example cluster: XAGUSD repeated bearish H1 OB context during a real selloff.
- Exclusions: duplicate active rows must collapse to opportunity-level rows; no broker PnL claim from synthetic path labels.

Actions:

1. Preregister the strategy family:
   - Candidate eligibility.
   - Entry timing candidates.
   - Stop/invalidation candidates.
   - Target logic.
   - Duplicate counting.
   - Session/symbol/regime partitions.
   - No-leak field whitelist.
2. Build shadow-only rows:
   - `continuation_no_retrace_candidates.jsonl`
   - `continuation_no_retrace_resolutions.jsonl`
   - audit/status file.
3. Start with observation, not threshold selection:
   - how far price was from limit entry at decision,
   - displacement/ATR state,
   - M15/M5 path sequence,
   - whether continuation occurred before any retrace,
   - whether later retest happened,
   - synthetic R under preregistered entry/SL definitions.
4. Validate in layers:
   - existing-data discovery,
   - post-cutoff forward shadow,
   - broker actual-R comparison only when real fills exist,
   - concentration and cost sensitivity.

Acceptance:

- A continuation strategy spec exists before outcome-mining.
- Shadow rows are append-only and no-live-impact.
- Verifiers know whether the rows are missing, stale, source-blocked, or valid.
- No promotion claim until a separate dossier passes sample, no-leak, concentration, cost, and owner approval.

### 2B. `m15_choch_exists` Diagnostic Expansion

Hypothesis:

- The L2 CHoCH/BOS gate may be correctly blocking weak setups, but May 5 suggests a separate fast-continuation regime where the current retest confirmation can miss directional delivery.

Actions:

- Do not loosen the gate.
- Add diagnostic-only fields for every `m15_choch_exists` fail:
  - nearest qualifying/non-qualifying CHoCH/BOS candidate,
  - displacement size and reason for fail,
  - M15 swing context,
  - M5/M1 continuation context if available,
  - path label after follow-up,
  - duplicate/opportunity status.
- Build an audit that groups L2 rejects by later path outcome:
  - reached TP area without entry touch,
  - entry touched then TP,
  - entry touched then SL,
  - unresolved,
  - ambiguous.

Acceptance:

- We can explain not just that `m15_choch_exists` failed, but why.
- Any future gate change has evidence and a promotion dossier.

### 2C. XAGUSD Fresh-OB Late-NY Lane

Question:

- Is the 16:30 XAGUSD newer-OB shift a distinct opportunity class worth tracking separately?

Actions:

- Add or verify opportunity lifecycle classification for older-OB duplicate clusters versus fresh-OB resets.
- Track late-NY fresh OBs by symbol/session/time-to-close.
- Separate `entry_touched_unresolved` near close from same-day terminal labels.

Acceptance:

- Fresh-OB rows are not accidentally merged into old duplicate clusters.
- Late-session unresolved rows remain unresolved until enough path data exists.
- No trade claim from close-bound unresolved labels.

## Phase 3 - Source And Orderflow Capability

### 3A. Sierra `.scid` Footprint/Profile Extraction

Purpose:

- Convert existing Sierra local data into measured decision-time features before spending new cash.

Actions:

- Freeze `.scid` source semantics and parser assumptions.
- Build fixtures for bid/ask volume, delta, POC/HVN/LVN, and eventually VAH/VAL.
- Keep VAH/VAL blocked until session-profile definition is frozen.
- Join features by candidate_id and `decision_time_utc` with decision-time cutoff only.
- Keep post-decision fields forensic-only.

Acceptance:

- Parser tests exist.
- Candidate feature rows carry source freshness and no-leak status.
- SI/XAGUSD remains blocked where depth semantics are not solved.

### 3B. Databento Historical-Credit Replay

Purpose:

- Test whether paid/live orderflow would have added value using existing credits before spending new cash.

Actions:

- Build predeclared request manifests.
- Estimate cost before every fetch.
- Enforce caps: existing credits only, per-request and daily caps from the LTO plan.
- Start with NAS100/NQ, then US30/YM, XAUUSD/GC, XAGUSD/SI, USDJPY/6J, GBPUSD/6B.
- Separate decision-time features from post-outcome forensic features.

Acceptance:

- No live Databento collector starts implicitly.
- Every fetch has a manifest, cache row, cost row, source index, and no-leak test.
- Source-value review separates broker actual-R, synthetic path-R, and lifecycle labels.

### 3C. External Free/Public Source Contracts

Purpose:

- Unblock LTO-031/LTO-032 public-source lanes correctly.

Actions:

- Create source registry contracts for FX COT, BIS, FRED/Fed, public Cboe volatility indices, FlashAlpha forward snapshots, and any FX fix proxy.
- For each source define URL/vendor, legal access, cache schema, publication timestamp, update cadence, no-lookahead rule, and allowed feature role.
- Do not ingest a source until its contract exists.

Acceptance:

- Source contract tests prevent blocked sources from being marked validation-safe.
- Features are context/shadow only.

## Phase 4 - ML And Selector Readiness

### 4A. K55 Model Artifact Path

Question:

- What exact work is needed to move from feature bundle ready to a valid shadow inference artifact?

Actions:

- Freeze target contract.
- Confirm feature whitelist and forbidden post-event keys.
- Separate broker actual-R primary labels from synthetic path context labels.
- Build or train only a registered shadow model artifact; do not reuse stale K54 artifacts blindly.
- Add inference disabled/enabled tests.

Acceptance:

- K55 can run shadow inference only when the model artifact is present and compatible.
- Rows show model version, feature version, target version, label eligibility, and no-leak status.
- No live decision impact.

### 4B. V2/V3 Selector Readiness

Question:

- What exact metadata and sample gates must be filled before V2/V3 selector ideas can be considered?

Actions:

- Keep LTO-027 readiness gates as authority.
- Add missing decision-time metadata capture only if it is observational and no-live-impact.
- Track broker actual-R sample floor, lifecycle truth, cost/slippage, concentration, exact metadata, and promotion dossier state.

Acceptance:

- Readiness report remains explicit: ready or not ready, with blocker counts.
- No selector logic is wired into production.

## Phase 5 - Outcome Truth And Promotion Infrastructure

### 5A. Broker Actual-R Growth

Purpose:

- Increase real outcome labels without polluting them with synthetic labels.

Actions:

- Keep account-history exports fresh.
- Verify candidate-to-trade linking for every real fill.
- Track commission, swap, entry/exit slippage, close reason, time in trade, and partial/BE events.
- Review new broker actual-R rows event-by-event, not only by calendar delay.

Acceptance:

- Actual-R claim-allowed rows are explicit.
- No-fill and shadow alternatives remain non-actual-R.

### 5B. Promotion Dossier Template

Purpose:

- Make it impossible to accidentally promote a research idea.

Actions:

- Build or update a template requiring:
  - preregistration,
  - sample floor,
  - DSR/PBO or not-computable reason,
  - concentration,
  - actual-vs-synthetic label separation,
  - cost/slippage,
  - no-leak proof,
  - rollback plan,
  - owner approval.

Acceptance:

- Every future promotion proposal uses the same checklist.
- Current workstreams remain `NO_PROMOTION_VERDICT`.

## Execution Sequence

Recommended order:

1. Phase 0: commit cleanup and baseline.
2. Phase 1A/1B/1C: observer reload, heartbeat lifecycle, side-probe diagnosis.
3. Phase 1D: pending-limit telemetry clarity.
4. Phase 2B: L2 diagnostic expansion, because it informs the continuation strategy.
5. Phase 2A: continuation/no-retrace shadow strategy.
6. Phase 2C: XAGUSD fresh-OB lane.
7. Phase 3A: Sierra `.scid` extraction.
8. Phase 3B: Databento historical-credit replay.
9. Phase 3C: free/public source contracts.
10. Phase 4A/4B: K55 and V2/V3 readiness.
11. Phase 5: actual-R and promotion dossier infrastructure.

Rationale:

- Operational integrity comes first because bad processes create bad evidence.
- Diagnostics come before strategy design because they clarify whether missed moves are gate behavior, entry design, duplicate handling, or source gaps.
- Source/model work comes after the identity/outcome spine is clean.
- Promotion infrastructure stays last because no current lane is promotion-ready.

## Ambiguity Ledger To Pursue

These are not assumptions. Each must be answered or explicitly blocked:

- Did post-window heartbeat persistence come from timeout trailing, watchdog lifecycle, process stop policy, or stale heartbeat write cadence?
- Did NAS100/US30 direct probe failure come from broker symbol mapping, MT5 API contention, symbol selection, terminal state, or permissions?
- Does `continued_without_entry_touch_to_tp_area` contain a consistent tradable continuation entry, or is it just hindsight directionality?
- Is `m15_choch_exists` too strict in fast-continuation regimes, or correctly blocking structurally weak setups?
- Does XAGUSD late-NY fresh-OB behavior repeat enough to justify a separate lane?
- Can Sierra `.scid` provide valid bid/ask volume and profile features with frozen source semantics?
- Is SI/XAGUSD source-depth definition solvable locally, or does it require Databento/official source parity?
- Can K55 produce useful shadow inference when labels are mostly synthetic context and broker actual-R remains sparse?
- Would native MT5 pending orders improve real fills, or only add broker-side lifecycle complexity without solving no-entry-touch cases?

## Commit Discipline

Use focused commits:

- `docs/research: add monitoring synthesis and next-improvement plan`
- `research: refresh lto monitoring control artifacts`
- `data/shadow: commit may 5 forward shadow evidence`
- `ops: document observer and monitoring closeout artifacts`

Every commit should include:

`Co-Authored-By: Codex GPT-5 <redacted@example.com>`

## Current Verdict

This plan authorizes disciplined research and operational cleanup only. It does not authorize any live trading behavior change.

