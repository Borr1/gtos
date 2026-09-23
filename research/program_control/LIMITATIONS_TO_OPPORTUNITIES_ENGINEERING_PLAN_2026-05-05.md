# Limitations To Opportunities Engineering Plan - 2026-05-05

**Schema:** `limitations_to_opportunities_engineering_plan_v1`  
**Source session:** 2026-05-04 full-day active monitoring  
**Generated:** `2026-05-04T19:25:00+00:00`  
**Promotion verdict:** `NO_PROMOTION_VERDICT`  
**Scope:** research/tooling, shadow capture, data health, source readiness, verifiers, and planning. No live trading logic, prompt, risk, execution, safety-gate, canary, or paid-data activation changes without explicit approval.

## Purpose

The 2026-05-04 monitoring day proved that "a logger exists" is not enough. A follow-data lane is only useful when it has a live caller, point-in-time source fields, append-only preservation, deterministic identity, duplicate-aware counting, stale-data checks, backfill rules, and a verifier that catches silent gaps.

This plan converts every known limitation and blocker into an engineering queue. It intentionally includes lower-priority, source-blocked, approval-blocked, and no-event lanes, not only the main high-priority items.

The plan has two coupled outcomes:

- better capture loops, so every live/shadow lane is fresh, joined, source-aware, and auditable;
- better ML, so K55/ML shadow inference receives validated as-of features, cleaner paired labels, source freshness/provenance flags, no-leak eligibility fields, and explicit blockers instead of stale or synthetic inputs.

Do not treat ML as a later consumer that passively benefits by accident. Each LTO item should declare whether it contributes model features, target/label quality, sample eligibility, source/proxy/freshness metadata, paired AI-vs-ML comparison fields, or an ML-blocker reason.

## Source Artifacts

- `research/program_control/GTOS_FULL_DAY_ACTIVE_MONITORING_FINAL_REPORT_2026-05-04.md`
- `research/program_control/LIVE_SHADOW_DATA_HEALTH_AUDIT_2026-05-04.md`
- `research/program_control/LIVE_SHADOW_FOLLOWUP_COVERAGE_AUDIT_2026-05-04.md`
- `research/program_control/FORWARD_CAPTURE_READINESS_VERIFICATION_2026-05-04.md`
- `research/program_control/SIERRA_FORWARD_CAPTURE_READINESS_2026-05-04.md`
- `research/program_control/LIVE_SHADOW_CAPTURE_GAP_AUDIT_2026-05-04.md`
- `research/program_control/LIVE_SHADOW_GAP_CLOSURE_FINAL_2026-05-04.md`
- `.context/00_core/research_current_state.md`

## Non-Negotiable Rules

1. Shadow capture is additive only unless the owner explicitly approves a behavior change.
2. Every row must be append-only, idempotent, and joinable by stable keys.
3. No field is allowed to move from `SOURCE_NOT_CAPTURED` to a value unless that exact value is present in point-in-time source data or is explicitly labeled as derived from as-of market data.
4. No replay result becomes live validation without pre-registration and unseen evidence.
5. Databento live collection must be event-triggered and cost-capped. No blind every-candle polling.
6. Sierra depth/heatmap data can be captured locally, but interpretation must carry source/proxy/parity status.
7. Duplicate active setups are evidence, not separate trade opportunities.
8. Same-candle TP/SL ambiguity stays non-scored unless lower-timeframe or tick ordering resolves it.
9. Verifiers must distinguish "no event", "not running", "source blocked", "approval blocked", and "fresh rows present".
10. Every fix must include tests, a backfill or blocker row, a verifier update, and a durable report.

## Resume Context Hygiene

- This plan is the active queue for resumed `/goal` work. If the session is already resumed, continue implementing the next unresolved LTO item; do not instruct the owner to run `/goal resume`.
- The owner's TikTok/orderflow context is already encoded as a hypothesis in Wave 2. Use it to keep footprint, Sierra Chart, volume profile, and depth/flow features in scope, but do not repeat-check whether it was included and do not treat it as validation evidence.
- After compaction, derive current status from `research/program_control/LIMITATIONS_TO_OPPORTUNITIES_QUEUE_STATE_2026-05-05.md`, `.context/LIVE_STATE.md`, and the latest committed artifacts.

## Execution Waves

### Wave 0 - Plan And Guardrails

Goal: freeze this queue and avoid losing items to context compaction.

Deliverables:

- This plan.
- Matching context pointer in `.context/00_core/research_current_state.md`.
- A future execution goal prompt if the owner wants a long-running implementation session.

Done when:

- Every item in the full follow-up coverage matrix has a row in this plan.
- Items that cannot be fixed immediately are classified with exact prerequisites.

### Wave 1 - Candidate Truth Core

Goal: make every candidate independently reviewable from deterministic live rows.

Includes:

- structural source fields,
- path ordering,
- pending lifecycle,
- opportunity duplicate lifecycle,
- candidate rollups,
- missed-opportunity comparators,
- actual broker/account truth scaffolding.

This wave is the highest leverage because every later strategy or data source depends on it.

### Wave 2 - External Data And Proxy Layer

Goal: make Sierra and Databento useful without creating cost, proxy, or no-leak errors.

Owner context to preserve: discretionary traders report meaningful RR improvement when moving from pure ICT-style structure into orderflow using footprints, Sierra Chart, and volume profile. Treat that as a forward hypothesis, not as validation. The engineering implication is to turn footprint delta/absorption, stacked imbalance, volume-profile POC/VAH/VAL/HVN/LVN context, depth thinness, liquidity pulls, and wall concentration into timestamped shadow features around the same GTOS structural setups. These features can test entry timing, bad-condition vetoes, stop/invalidation efficiency, and target/RR expansion only after joining to broker actual-R, cost/slippage, and lifecycle truth.

Includes:

- Databento event trigger policy and collector scaffold,
- Sierra depth background extraction,
- Sierra source/parity registry,
- GBPJPY proxy design,
- XAGUSD/SI and 6B common-second/depth-definition blockers,
- NAS100/NQ orderflow diagnostic readiness,
- X-1/X-2/X-3 orderflow primitive design.

### Wave 3 - Verifiers, Cadence, And No-Event Proof

Goal: prevent silent "looks fine" states.

Includes:

- freshness by lane type,
- no-event rows for event-driven monitors,
- watchdog/canary skip expiry governance,
- notification dead-zone policy,
- storage retention,
- trade-index and lifecycle completeness verifiers,
- all-row safety counter checks.

### Wave 4 - Research Expansion And Approval-Gated Shadow Systems

Goal: make lower-priority opportunities ready without smuggling behavior changes into production, and improve the ML shadow path with richer validated as-of inputs and cleaner outcome labels.

Includes:

- K55/ML target refresh, feature enrichment, and read-only shadow inference,
- explicit ML feature/label/sample-eligibility contributions from earlier LTO outputs,
- Component 3B/tool-grounding/Reflexion approval path,
- ES/MES pre-registration,
- XAUUSD same-market structural path guard,
- options/gamma/VRP/FlashAlpha source plan,
- external macro/source blockers,
- CL/ZN/VIX/VXM controls,
- S79/side-aware and regime/decay joins.

## Follow-Up Coverage Map

This table maps every row from `LIVE_SHADOW_FOLLOWUP_COVERAGE_AUDIT_2026-05-04.md` into the LTO queue. A row being `ROWS_PRESENT` does not remove it from the plan; it means the opportunity is now hardening, richer joining, no-event proof, or continued accumulation rather than initial capture.

| Follow ID | Audit lane | LTO owner(s) |
|---|---|---|
| `LIVE-FOLLOW-001` | AI-independent mechanical/MSO evaluation anchor | `LTO-001`, `LTO-039` |
| `LIVE-FOLLOW-002` | AI CANDIDATE terminal strategy registry and external confluence | `LTO-002`, `LTO-013` |
| `LIVE-FOLLOW-003` | Candidate path follow | `LTO-003`, `LTO-006`, `LTO-007` |
| `LIVE-FOLLOW-003B` | Opportunity-level duplicate protection | `LTO-004`, `LTO-039` |
| `LIVE-FOLLOW-004` | Pending-limit lifecycle truth | `LTO-005`, `LTO-026` |
| `LIVE-FOLLOW-005` | V2b forward pairs | `LTO-006`, `LTO-027` |
| `LIVE-FOLLOW-006` | V3/pre-fill delivery path | `LTO-007` |
| `LIVE-FOLLOW-007` | FVG/OB confluence ledger | `LTO-008` |
| `LIVE-FOLLOW-008` | CL/ZN/VIX/VXM context/control ledger | `LTO-009`, `LTO-035` |
| `LIVE-FOLLOW-009` | Databento targeted live confluence/orderflow | `LTO-010`, `LTO-033` |
| `LIVE-FOLLOW-010` | Sierra local depth confluence | `LTO-012`, `LTO-013` |
| `LIVE-FOLLOW-011` | NAS100/NQ orderflow adverse-selection diagnostic | `LTO-011`, `LTO-010` |
| `LIVE-FOLLOW-012` | Broker actual-R, slippage, cost, exit accounting | `LTO-015`, `LTO-025` |
| `LIVE-FOLLOW-013` | J46-J49 exit policy comparator | `LTO-016`, `LTO-015` |
| `LIVE-FOLLOW-014` | S79/side-aware compounding context | `LTO-017` |
| `LIVE-FOLLOW-015` | Regime classifier and monthly decay/OB continuation | `LTO-018` |
| `LIVE-FOLLOW-016` | Decision-layer diagnostics | `LTO-019` |
| `LIVE-FOLLOW-017` | Mechanical/dumb/proximity/liquidity/displacement/structure divergence | `LTO-020` |
| `LIVE-FOLLOW-018` | Exit-management shadows | `LTO-021`, `LTO-015` |
| `LIVE-FOLLOW-019` | Session volatility and US30 sweep divergence | `LTO-022` |
| `LIVE-FOLLOW-020` | K55 shadow / ML specialist labels | `LTO-023` |
| `LIVE-FOLLOW-021` | Component 3B debate / AI tool grounding / Reflexion | `LTO-024` |
| `LIVE-FOLLOW-022` | GBPJPY Sierra/orderflow proxy gap | `LTO-014` |
| `LIVE-FOLLOW-023` | Account/PnL truth and R-vs-dollar separation | `LTO-025`, `LTO-015` |
| `LIVE-FOLLOW-024` | O1 trade-index staleness and O8 lifecycle completeness | `LTO-026` |
| `LIVE-FOLLOW-025` | V2 structural oracle/as-of selector | `LTO-027`, `LTO-006` |
| `LIVE-FOLLOW-026` | XAUUSD same-market structural path extension and frozen-slice guard | `LTO-028` |
| `LIVE-FOLLOW-027` | ES/MES strategy-cohort pre-registration | `LTO-029` |
| `LIVE-FOLLOW-028` | 6B sampling alignment and SI source/depth blockers | `LTO-030`, `LTO-013` |
| `LIVE-FOLLOW-029` | External feed blockers | `LTO-031` |
| `LIVE-FOLLOW-030` | Options/gamma, VRP, FlashAlpha GEX | `LTO-032` |
| `LIVE-FOLLOW-031` | X-1/X-2/X-3 imbalance/meta-order-flow primitives | `LTO-033`, `LTO-010` |
| `LIVE-FOLLOW-032` | Live monitoring goal/runbook persistence | `LTO-034`, `LTO-040` |
| `LIVE-FOLLOW-033` | No-AI MSO shadow observer for tested non-orchestrator instruments | `LTO-035` |

## Complete Opportunity Register

### LTO-001 - AI-Independent MSO Evaluation Anchor

Current state: `ROWS_PRESENT`; `strategy_follow_evaluations.jsonl` has live MSO/no-AI rows.

Opportunity: turn MSO rows into a canonical "decision-time market state snapshot" that every shadow strategy can consume without depending on AI output.

Engineering action:

- Define a reusable MSO snapshot schema with h1/h4/d1 bias, framework qualification, candidate POI, structural state, session, symbol, and source hashes.
- Add a verifier that compares each candidate row to its nearest MSO row and flags missing or inconsistent decision-time context.

Backfill: join existing 2026-05-04 candidates to MSO rows where timestamps match exactly; otherwise write `MSO_JOIN_MISSING`.

Validation: unit tests for MSO join selection and `verify_shadow_log_integrity.py` candidate-to-MSO coverage.

### LTO-002 - AI Candidate Registry And External Confluence

Current state: `ROWS_PRESENT`; candidate rows exist, but some downstream source fields are still status-only.

Opportunity: make the candidate registry the single durable source of truth for the AI terminal decision, trade geometry, framework, L2 status, source status, and confluence availability.

Engineering action:

- Add schema-level requirements for `candidate_id`, `decision_time_utc`, `source_hash`, trade geometry, framework, L2 final state, Sierra status, Databento trigger status, and structural metadata presence flags.
- Add an audit that rejects candidate rows whose confluence fields are absent rather than explicitly blocked.

Backfill: write append-only candidate registry audit rows, not rewrites.

Validation: tests for complete and source-blocked candidate rows.

### LTO-003 - Candidate Path Follow

Current state: `ROWS_PRESENT`; path rows cover every candidate.

Opportunity: expand path following into a richer price-action trail, not only terminal label snapshots.

Engineering action:

- Track distance-to-entry, nearest approach, first entry touch, first TP1 touch, first SL touch, crossed-and-returned, crossed-and-continued, reached target area without entry, and unresolved state per as-of candle.
- Persist per-candle path deltas so the chart history can be reviewed without rerunning MT5 reads.

Backfill: derive per-candidate path deltas from available M15/M1 bars with clear `DERIVED_FROM_ASOF_OHLC` labels.

Validation: tests for no-fill near-miss, through-entry-then-return, through-entry-then-continue, same-candle ambiguity, and unresolved cases.

### LTO-004 - Opportunity Duplicate Lifecycle

Current state: duplicate-aware counting exists.

Opportunity: make duplicate/overlap rules explicit enough to prevent future summary drift.

Engineering action:

- Formalize opportunity lifecycle state: `NEW_COUNTABLE`, `DUPLICATE_ACTIVE_SETUP`, `BLOCKED_SAME_SYMBOL_OVERLAP`, `REOPENED_AFTER_TERMINAL`, and `NEW_AFTER_COOLDOWN`.
- Add tolerance bands for "same level" and "small pip offset" by instrument.
- Add a verifier that summaries only count `COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY`.

Backfill: append correction rows for any historical duplicate cluster whose primary/duplicate status changed.

Validation: tests for consecutive same candidate, nearby 2-pip duplicate, terminal-then-new-opportunity, and same-symbol overlap.

### LTO-005 - Pending-Limit Lifecycle Truth

Current state: lifecycle rows exist and were repaired, but old rows still need careful long-term migration.

Opportunity: make pending orders first-class evidence for fill/no-fill, cancellation, expiry, wrong-side abort, and missed move analysis.

Engineering action:

- Enforce globally unique pending intent IDs.
- Require `candidate_id`, `decision_time_utc`, symbol, source symbol, entry/SL/TP, order-send status, cancel reason, and final state.
- Add lifecycle completeness verifier across trade records, pending intents, and shadow candidates.

Backfill: retain existing join-backfill rows; add a migration report for old rows that remain unjoinable.

Validation: tests for cross-symbol trade ID collision, no-fill but TP area reached, wrong-side cancel, pending still open, and broker position mismatch.

### LTO-006 - V2b Forward Pair Resolution

Current state: rows and resolver rows exist, but V2b remains prospective and not validated.

Opportunity: make every V2b pair accumulate post-cutoff evidence automatically, with actual/synthetic label separation.

Engineering action:

- Resolve OB-boundary, J46 baseline, fixed-R, and FVG comparator states from candidate path, LTF path, and lifecycle truth.
- Split `BROKER_ACTUAL_R`, `SYNTHETIC_PATH_R`, and `UNRESOLVED_PATH` fields.
- Add rolling status report: number of resolved pairs, symbol/session concentration, ambiguity rate, and no-leak status.

Backfill: current 48 candidates should have resolution rows; any missing strategy-specific exact fields stay `SOURCE_NOT_CAPTURED`.

Validation: tests for pair resolution, ambiguous exclusion, no-leak source fields, and rolling status counts.

### LTO-007 - V3 / Pre-Fill Delivery Path

Current state: decision-time rows exist, but exact V3 fields remain `SOURCE_NOT_CAPTURED`.

Opportunity: turn V3 from placeholder to live-scorable once its required state is captured at decision time.

Engineering action:

- Capture pre-fill arming time, original POI bounds, delivery-leg direction, reversal-leg state, fill/cancel/expiry state, and post-lock reentry eligibility.
- Keep V3 exploratory and `NO_PROMOTION_VERDICT`.

Backfill: do not fabricate missing V3 historical fields; write blockers and only compute fields that can be derived as-of.

Validation: tests for pre-fill arm, no-fill, reentry eligibility, blocked missing-state rows, and cost-aware min-R presence.

### LTO-008 - FVG/OB Confluence And Disagreement

Current state: rows/resolutions exist, but deeper confluence fields are incomplete.

Opportunity: capture whether FVG/OB agreement is confirmation, separate setup families, or delivery-leg plus reversal-leg structure.

Engineering action:

- Capture FVG bounds, OB bounds, sequencing, overlap, FVG-first/OB-second state, composite arbitration, and disagreement reason.
- Add source-status fields to prevent post-outcome confluence inference.

Backfill: existing rows can only be resolved from current candidate geometry and path labels; missing exact FVG lock state remains blocked.

Validation: tests for FVG-only, OB-only, overlap, sequence, and composite arbitration.

### LTO-009 - Context/Control Ledger For CL/ZN/VIX/VXM

Current state: context rows exist.

Opportunity: keep context instruments useful without accidentally treating them as validation of the traded instrument.

Engineering action:

- Tag every context row as `CONTROL_ONLY`.
- Add same-time context snapshots for event windows.
- Add reports that compare context behavior to candidate outcomes as exploratory context only.

Backfill: no direct strategy backfill; preserve context rows as controls.

Validation: verifier rejects any context/control row with direct strategy validation status.

### LTO-010 - Databento Targeted Live Confluence

Current state: trigger-decision rows exist; live confluence rows are waiting.

Opportunity: use Databento live data when it adds market-state awareness, without going rogue on every candle.

Engineering action:

- Implement a registered trigger policy: symbols, setups, windows, schema, spend cap, cooldown, and required reason.
- Add `databento_live_confluence.jsonl` writer with zero-order/no-AI/no-canary counters.
- Add budget ledger per trigger and per day.
- Separate trades-only, MBP, MBO, and depth/heatmap feature classes.

Backfill: none for live-only paid data; historical cached artifacts can be used only in research reports with evidence-class labels.

Validation: dry-run trigger tests, no-trigger tests, cost-cap tests, disabled-env tests, and paid-fetch counter checks.

Prerequisite: explicit owner approval before any paid live pull is enabled.

### LTO-011 - NAS100/NQ Orderflow Adverse-Selection Diagnostic

Current state: rows present only as source/status context; live Databento rows absent.

Opportunity: study whether depth/thinness/orderflow warns against bad NAS100 candidates or improves timing.

Engineering action:

- Register NAS100/NQ trigger criteria.
- Collect MBP10/MBO windows only around eligible candidates.
- Track broker actual-R >= 20 and MBP10 candidate rows >= 30 before any claim.

Backfill: use cached NAS100 orderflow artifacts for exploratory diagnostics only.

Validation: feature stability, concentration, leave-one-date, cost sensitivity, and actual-vs-synthetic coverage reports.

### LTO-012 - Sierra Local Depth Confluence

Current state: source/status coverage exists; many heavy feature rows are deferred.

Opportunity: use Sierra depth/heatmap as local confluence without blocking live capture.

Engineering action:

- Build a background Sierra depth feature extractor queue with per-symbol throttle, checkpointing, and file-size guards.
- Preserve source path, mtime, size, session, and proxy status immediately, then enrich features later.
- Add a depth feature version field.

Backfill: process pending heavy-depth rows where local files exist, using no future leakage beyond the declared as-of window.

Validation: extraction idempotency, CLEAR_BOOK replay bounds, timeout handling, no-live-blocking tests, and feature/null audit.

### LTO-013 - Sierra Source/Parity Registry

Current state: source statuses exist; several mappings remain caution or blocked.

Opportunity: avoid false confidence by making every Sierra feature carry its proxy and parity quality.

Engineering action:

- Create a registry of broker symbol -> Sierra symbol -> proxy class -> parity status -> allowed use.
- Include `VALIDATED_PROXY`, `SAME_MARKET_SOURCE_TRANSFER`, `FUTURES_PROXY_TRANSFER`, `CONTROL_ONLY`, `SOURCE_DEFINITION_BLOCKED`, and `NO_REGISTERED_PROXY`.

Backfill: attach registry status rows to all existing candidates.

Validation: tests for NAS100/NQ, XAGUSD/SI blocked status, GBPJPY no proxy, EURUSD/6E, GER40, UK100, and controls.

### LTO-014 - GBPJPY Sierra/Databento Proxy Gap

Current state: no registered direct proxy.

Opportunity: convert GBPJPY from "blind to external confluence" to an explicitly designed proxy problem.

Engineering action:

- Write a proxy design comparing 6J, 6B, JPY crosses, GBP futures, and possible weighted cross context.
- Define what the proxy can and cannot claim.
- Pre-register tests before opening outcomes.

Backfill: do not infer GBPJPY confluence for existing rows. Keep blocker rows.

Validation: correlation stability, lead/lag, session overlap, contract liquidity, and outcome-transfer caveat report.

### LTO-015 - Broker Actual-R, Slippage, Cost, And Exit Accounting

Current state: partial rows exist; canonical account-history join is not automated enough.

Opportunity: separate real broker truth from research proxy labels.

Engineering action:

- Build read-only MT5 account-history exporter and joiner.
- Tag rows as `ACCOUNT_HISTORY_REALIZED`, `LIVE_R_ARTIFACT`, `RESEARCH_MEASURED`, or `SYNTHETIC_PATH_R`.
- Join fills, partial exits, slippage, commissions, swaps, time-in-trade, and close reason.

Backfill: query historical account/deal data where available; do not use local stale PnL artifacts as truth.

Validation: account-history fixture tests, no-position tests, partial fill tests, mismatched R-vs-dollar warnings.

### LTO-016 - J46-J49 Exit Policy Comparator

Current state: rows exist only when fills exist.

Opportunity: compare actual exit policy vs older/hypothetical policy without contaminating live execution.

Engineering action:

- Ensure comparator rows join to actual broker fills and path labels.
- Add no-fill candidate context separately so fill-only rows are not mistaken for all candidates.

Backfill: only filled trades with known entry/exit can be actual-R; path-only remains synthetic.

Validation: filled-trade fixtures and no-fill exclusion tests.

### LTO-017 - S79 / Side-Aware Compounding Context

Current state: config and some state rows exist; forward fill rows are sparse.

Opportunity: preserve compounding/risk-policy context without changing risk.

Engineering action:

- Snapshot risk-policy context per candidate and per fill.
- Join to account truth and side-aware state.
- Keep all rows `SHIPPED_POLICY_CONTEXT` or `NO_PROMOTION_VERDICT`, not live tuning.

Backfill: candidate-level context from config; actual effect only when broker fills exist.

Validation: risk-context snapshot tests and no behavior-change assertions.

### LTO-018 - Regime Classifier And Monthly Decay

Current state: regime rows and OB continuation rows exist.

Opportunity: make regime/decay evidence actionable for review by joining it to candidate/fill outcomes.

Engineering action:

- Join regime classification to every candidate and actual/synthetic outcome.
- Produce cadence reports: daily candidate mix, weekly regime mix, monthly decay/OB continuation.

Backfill: join existing 2026-05-04 candidates to nearest regime rows.

Validation: timestamp-asof join tests, missing regime status, and monthly report freshness checks.

### LTO-019 - Decision-Layer Diagnostics

Current state: candidate features, D1 lag, direction emission, SL/touch gates exist.

Opportunity: make each rejection/acceptance explainable from deterministic diagnostics.

Engineering action:

- Build a candidate diagnostics join report covering candidate_features, D1 lag, direction, SL beyond OB, touch-count, and L2 reasons.
- Add mismatch checks between AI decision, deterministic gates, and emitted direction.

Backfill: join existing rows by symbol/time where possible.

Validation: no orphan diagnostics, direction mismatch fixtures, gate reason coverage.

### LTO-020 - Mechanical Baselines, Proximity, Liquidity, Displacement, Structure Divergence

Current state: rows exist but are not all joined into candidate/fill outcome summaries.

Opportunity: turn scattered diagnostics into comparable explanatory variables.

Engineering action:

- Add a per-candidate diagnostic joiner for dumb baseline, proximity, liquidity distance, displacement, and structure divergence.
- Produce feature availability and outcome correlation reports, clearly discovery-only.

Backfill: join by symbol/time window with as-of constraints.

Validation: no-lookahead window tests and orphan-row audit.

### LTO-021 - Exit-Management Shadows: BE, Partial Close, Time In Trade

Current state: event-waiting rows are correctly empty when no fill reaches the trigger.

Opportunity: make no-event proof explicit so empty files are not misread as broken capture.

Engineering action:

- Emit status/no-event rows per session or per fill state: `NO_FILLED_TRADE`, `NO_BE_TRIGGER`, `NO_PARTIAL_TRIGGER`, `NO_CLOSE_EVENT`.
- Keep actual event rows separate.

Backfill: for 2026-05-04, write no-event status if no fills qualified.

Validation: verifier differentiates missing file vs no-event file.

### LTO-022 - Session Volatility And US30 Sweep Divergence

Current state: rows now exist but cadence needs watchdog/readiness proof.

Opportunity: make event monitors auditable even during quiet sessions.

Engineering action:

- Add scheduled cadence checks and no-event rows.
- Include symbol/session coverage and latest run time.

Backfill: run over available 2026-05-04 windows and write no-event/event rows as appropriate.

Validation: watchdog wiring test and stale/no-event distinction.

### LTO-023 - K55 / ML Shadow

Current state: owner-approved for target refresh plus read-only shadow inference; implementation remains target-refresh/preregistration gated.

Opportunity: make the ML shadow path better, not merely present. The model should receive validated as-of market-state, strategy, lifecycle, account-truth, Sierra, Databento, orderflow, volatility, regime, and confluence features where available, with explicit source/proxy/freshness flags, so paired AI-vs-ML evidence starts accumulating from a stronger input substrate.

Engineering action:

- Refresh and preregister the K55 target after the K54 v4 failure; do not reuse stale target definitions blindly.
- Define ML shadow input schema, target version, feature-bundle version, inference version, model registry path, and output schema.
- Include only decision-time/as-of features; forbid post-event/order-outcome leakage.
- Join MSO/candidate geometry, lifecycle state, account-truth class, regime/decay context, mechanical comparators, Sierra/Databento/orderflow source statuses/features, volatility/session context, and diagnostic gates where each source is fresh and provenance-tagged.
- Write paired read-only rows to `shadow_logs/ml_shadow_predictions.jsonl` with AI decision, ML prediction, model version, feature availability, source freshness, and no-action counters.
- Keep disabled/status rows only until the target, feature bundle, and model artifact pass tests.

Backfill: status rows until target/model are refreshed; after that, backfill only rows whose features and labels are reconstructable from point-in-time evidence. Do not synthesize missing labels or infer unavailable source fields.

Validation: target-refresh report, disabled-mode tests, fixture inference tests, no-AI/no-order/no-canary/no-paid-call assertions, no-leak feature tests, stale-source tests, model-version/schema tests, and verifier coverage for paired AI-vs-ML rows.

Prerequisite: refreshed target, preregistered feature bundle, explicit model artifact/version, and green tests before inference is enabled. Owner approval for this read-only shadow path was granted in-session on 2026-05-05; promotion or decision impact still requires a separate promotion dossier and approval.

### LTO-024 - Component 3B / Tool Grounding / Reflexion

Current state: explicit owner-approval blocked.

Opportunity: avoid losing the idea while preventing cost/behavior drift.

Engineering action:

- Write an approval dossier template: expected cost, shadow-only mode, prompts affected, evaluation metrics, and stop conditions.
- Do not wire or call AI.

Backfill: no backfill until owner reopens.

Validation: static check that approval-blocked lane has zero AI/API calls.

### LTO-025 - Account/PnL Truth And Evidence-Class Separation

Current state: local PnL artifacts are known-risk; account history is the truth.

Opportunity: eliminate confusion between dollars, R, proxy R, and synthetic labels.

Engineering action:

- Build a canonical evidence-class reconciler and report.
- Require every PnL/R claim to state source class.

Backfill: reconcile visible 2026 account-history where MT5 deal history is available.

Validation: report fails if a dollar/R claim lacks evidence class.

### LTO-026 - Trade Index Staleness And Lifecycle Completeness

Current state: `_trade_index.json` is stale; lifecycle completeness has known gaps.

Opportunity: make trade-record inventory reliable.

Engineering action:

- Rebuild or migrate the trade index.
- Add a consumer migration plan if old index is deprecated.
- Verify every `LIMIT_PLACED` has execution or pending lifecycle state.

Backfill: rebuild index from current trade records; append audit report.

Validation: index count equals trade-record count, latest timestamps match, lifecycle completeness checks pass or list exact blockers.

### LTO-027 - V2 Structural Oracle / As-Of Selector

Current state: live snapshot exists, but selector remains discovery-only.

Opportunity: collect enough clean unseen evidence to know whether structural selector ideas deserve promotion work.

Engineering action:

- Keep selector output as shadow-only.
- Require resolved V2b rows, lifecycle truth, cost/slippage, concentration diagnostics, and preregistered promotion gates before any behavior change.

Backfill: no behavior backfill; use existing rows for discovery reports only.

Validation: promotion-readiness report must remain `NOT_READY` until gates pass.

### LTO-028 - XAUUSD Same-Market Structural Path Extension

Current state: source-status required with forward snapshot.

Opportunity: expand XAUUSD same-market structural/path evidence while protecting against frozen-slice leakage.

Engineering action:

- Pre-register same-market source-transfer slice before opening outcomes.
- Keep live rows separate from replay evidence.

Backfill: only source-status and preregistration records until cohort is frozen.

Validation: opened-outcome count at registration must be zero.

### LTO-029 - ES/MES Strategy-Cohort Pre-Registration

Current state: preregistration required.

Opportunity: prepare ES/MES as a future strategy cohort without accidental outcome mining.

Engineering action:

- Define source mapping, session windows, strategy family, evidence class, and no-lookahead rules.
- Freeze before outcomes.

Backfill: none before registration.

Validation: registry test proves outcome files were unopened at registration.

### LTO-030 - 6B Sampling Alignment And SI Depth Definition

Current state: source-status blocked with trigger.

Opportunity: make GBPUSD/6B and XAGUSD/SI usable with precise sampling rules.

Engineering action:

- Implement common-second alignment policy for 6B.
- Define SI depth source semantics and parity requirements before interpreting features.

Backfill: current rows keep source/depth blockers.

Validation: common-second alignment tests and SI parity/source report.

### LTO-031 - External Feed Blockers

Current state: documented source blockers for pre-2024 tick, pre-2022 OHLCV, FX COT, KMW fix, H-K-M, BIS, Fed research feed, and similar sources.

Opportunity: convert vague source blockers into precise acquisition plans.

Engineering action:

- For each source, define URL/vendor, legal access path, cache schema, publication-time/no-lookahead convention, cost, and expected use.
- Do not validate from unavailable sources.

Backfill: source-index rows only.

Validation: source readiness report with `READY`, `BLOCKED`, or `DROPPED_LOW_VALUE` statuses.

### LTO-032 - Options/Gamma, VRP, FlashAlpha Basic GEX

Current state: partial forward context plus source blockers.

Opportunity: register legal, timestamped volatility/gamma context if it can be sourced reliably.

Engineering action:

- Define allowed data source, delay, publication timestamp, instrument mapping, and no-lookahead convention.
- Collect forward rows only after source legality and schema are settled.

Backfill: none unless legal historical source and timestamps are available.

Validation: source evidence, timestamp tests, and context-only verifier.

### LTO-033 - X-1/X-2/X-3 Imbalance / Meta-Order-Flow Primitives

Current state: source blocked; Databento confluence rows are empty.

Opportunity: turn orderflow ideas into measurable primitives instead of general opinions.

Engineering action:

- Define each primitive: imbalance window, absorption/stacking/depletion measure, threshold-free continuous features first, candidate trigger, and cost cap.
- Include footprint-style delta/absorption, stacked imbalance, Sierra/Databento depth thinness, liquidity pulls, wall concentration, and volume-profile context (`POC`, `VAH`, `VAL`, `HVN`, `LVN`) as candidate feature families.
- Evaluate roles separately: entry timing, bad-condition veto, stop/invalidation efficiency, and target/RR expansion around the same GTOS structural setup.
- Keep post-event features forensic unless pre-decision windows are available.

Backfill: use cached data for exploratory feature design only.

Validation: primitive extractor tests, no-lookahead checks, cost estimate, and feature stability report.

### LTO-034 - Live Monitoring Goal / Runbook Persistence

Current state: runbook and monitor exist.

Opportunity: make monitoring resumable without relying on chat memory.

Engineering action:

- Add a daily monitoring checklist generator that reads the active runbook and prints required commands, expected lanes, and restart policy.
- Persist latest plan pointer in `.context/00_core/research_current_state.md`.

Backfill: none.

Validation: generated checklist includes every implemented and blocked lane.

### LTO-035 - No-AI MSO Shadow Observer Instruments

Current state: EURUSD/GER40/UK100 active; ES/MES prereg-blocked; CL/ZN/VIX controls.

Opportunity: expand non-orchestrator follow-data safely while keeping it no-execution/no-AI.

Engineering action:

- Harden observer lifecycle, status rows, restart policy, and final closeout detection.
- Add per-instrument source/proxy/evidence-class registry.

Backfill: existing observer status remains as evidence; future rows use normalized schema.

Validation: observer tests, no-AI/no-order counters, stale observer detection, and GER40 extended-session closeout fixture.

### LTO-036 - Watchdog, Canary Skip, And Restart Governance

Current state: watchdog E2E warns during owner-approved canary skip.

Opportunity: make cost-control overrides visible without weakening safety.

Engineering action:

- Add expiry and owner-approved reason display to monitoring reports.
- Alert when skip expires or canary cache remains stale after skip expiry.
- Keep canary calls manual/approved when expensive.

Backfill: status rows for 2026-05-04 owner skip.

Validation: tests for active skip, expired skip, malformed marker, and stale cache without skip.

### LTO-037 - Notification Queue Dead-Zone Policy

Current state: worker is correctly killed by watchdog during dead-zone, but earlier classification was confusing.

Opportunity: make notification worker state explainable.

Engineering action:

- Add status labels: `RUNNING`, `STOPPED_EXPECTED_DEAD_ZONE`, `STOPPED_UNEXPECTED_DURING_ACTIVE_WINDOW`, `QUEUE_EMPTY`, `QUEUE_PENDING`.
- Update monitor report to avoid manual restarts during dead-zone.

Backfill: append status/no-event row if a notification status log exists; otherwise document in next runbook.

Validation: tests for active-window missing worker vs dead-zone cleanup.

### LTO-038 - Storage, Retention, And Non-Overwrite

Current state: storage is acceptable after cleanup; old files can create pressure.

Opportunity: prevent data loss from storage pressure while preserving useful evidence.

Engineering action:

- Define retention classes: raw source, derived features, temp/cache, logs, lock files, reports.
- Add storage monitor with warning thresholds and deletion allowlist.
- Never delete raw source or evidence logs without archival policy.

Backfill: classify current large Sierra/depth files and temp directories.

Validation: dry-run cleanup report and path-safety tests.

### LTO-039 - Shadow Log Integrity And Semantic Data Health

Current state: final reports are clean, but verifier depth can increase.

Opportunity: make the verifier detect deeper value anomalies, not only schema and null health.

Engineering action:

- Add lane-specific semantic checks for path label vs geometry, lifecycle vs candidate outcome, source status vs feature interpretation, duplicate counts vs raw count, and stale by lane type.
- Add expectation mode: active KZ, dead-zone, event-driven, source-driven, approval-blocked.

Backfill: no data change; reports only.

Validation: negative fixtures for each silent-corruption class.

### LTO-040 - Research Queue / Master Backlog Integration

Current state: master queue exists, but this new plan should become the active limitation/opportunity queue.

Opportunity: prevent duplicated work and stale route restarts.

Engineering action:

- Add these LTO IDs to the master queue or create a linked LTO queue state.
- Mark each item as `ACTIVE`, `READY_TO_IMPLEMENT`, `APPROVAL_BLOCKED`, `SOURCE_BLOCKED`, `EVENT_WAITING`, or `DONE`.

Backfill: map LTO IDs to LIVE-FOLLOW IDs and prior gap IDs.

Validation: queue builder reports zero unmapped LIVE-FOLLOW rows.

## Implementation Order

1. LTO-040 queue integration and LTO-034 runbook generator.
2. LTO-039 verifier expansion.
3. LTO-001 through LTO-008 candidate truth, path, structural, and confluence core.
4. LTO-005, LTO-015, LTO-025, and LTO-026 lifecycle and account-truth work.
5. LTO-010 through LTO-014 and LTO-030 through LTO-033 external feed/proxy work.
6. LTO-021, LTO-022, LTO-036, LTO-037, and LTO-038 operational no-event/status/retention work.
7. LTO-016 through LTO-020 strategy diagnostic joins.
8. LTO-023, LTO-024, LTO-027, LTO-028, and LTO-029 approval/preregistration research lanes.
9. LTO-035 observer hardening and expansion controls.

This order is dependency-driven. It does not mean lower items are unimportant; it means they depend on candidate identity, verifier depth, source registry, account truth, or approval gates.

## Validation Standard For Each LTO Item

Each item is complete only when all are true:

- Code or report artifact exists.
- Tests or verifier checks exist.
- Current live-session data is backfilled or explicitly marked unrecoverable/source-blocked.
- Report states `NO_PROMOTION_VERDICT`.
- Safety counters are present where relevant: `ai_calls=0`, `canary_calls=0`, `order_calls=0`, `paid_data_calls=0`.
- `scripts/verify_shadow_log_integrity.py` and `scripts/audit_live_shadow_data_health.py` either pass cleanly or list documented waiting/source-blocked lanes.
- `.context/00_core/research_current_state.md` is updated when the research map changes materially.

## Restart Policy

Most plan items do not need immediate restart because they are research/tooling or batch verifiers. Restart is needed only after future capture code changes that affect live appenders or observer services:

- production orchestrators: restart only after additive capture code is changed and tests pass,
- shadow observer: restart after observer schema/lifecycle changes,
- watchdog/notification: restart or wait for scheduled watchdog only after dead-zone policy changes,
- Sierra: do not restart unless file capture stalls or chartbook/source setup changes require it,
- Databento: no live collector start until trigger policy and approval are in place.

## Definition Of "All Opportunities"

For this plan, "all" means every lane in the final follow-up coverage audit plus every open limitation in the final report/data-health audit, every previously repaired but still maturation-worthy gap from the gap audit, and every source/approval blocker named in the current research state. Future sessions should append new LTO IDs rather than replacing this list.
