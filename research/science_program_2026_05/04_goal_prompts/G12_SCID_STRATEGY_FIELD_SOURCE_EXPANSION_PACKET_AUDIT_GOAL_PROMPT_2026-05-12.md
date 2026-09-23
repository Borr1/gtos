# G12 SCID Strategy-Field Source Expansion Packet Audit Goal Prompt

Date: 2026-05-12
Owner lane: independent G12 source-field packet audit only
Evidence class: `G12_SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_AUDIT_ONLY`
Input route: `research/science_program_2026_05/06_outcome_testing/scid_strategy_field_source_expansion_packet/`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Objective

Independently audit the SCID strategy-field source expansion packet. Accept it only if it covers all 3,014 accepted SCID candidate rows exactly once, preserves duplicate/proxy denominator keys, assigns valid field-closure statuses for every required field family, binds every closed field to approved source artifacts, fail-closes missing historical strategy intent/source-state without inference, emits exact prospective capture requirements, and keeps broker/account/order/history/deal/position evidence, target/result/performance scoring, AI/API, paid/vendor access, raw market-data blob commits, and live trading surfaces closed.

## Mandatory Preflight

1. Run `python scripts/generate_live_state.py`.
2. Read `.context/LIVE_STATE.md`.
3. Read `.context/00_core/quick_reference_card.md`.
4. Read `.context/00_core/research_operating_doctrine.md`.
5. Read `.context/00_core/goal_session_research_discipline.md`.
6. Read `.context/00_core/research_current_state.md`.
7. Read this prompt from disk.
8. Read the controlling builder prompt: `research/science_program_2026_05/04_goal_prompts/SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_GOAL_PROMPT_2026-05-12.md`.
9. Read the full builder route manifest and every artifact listed in it from disk.
10. Re-read the accepted G0/G12/target-packet evidence chain used by the builder.

Do not rely on chat memory. If interrupted, regenerate LIVE_STATE and resume from disk artifacts.

## Mandatory Context Use

Treat `.context/00_core/goal_session_research_discipline.md` and `.context/00_core/research_operating_doctrine.md` as active G12 audit instructions, not background reading.

In this lane:

- G12 posture is independent, skeptical, and acceptance-focused.
- Do not reject the packet merely because strategy-intent fields are absent historically; exact fail-closed absence with prospective capture requirements is valid source-control evidence.
- Do reject concrete source-field inference, vague capture requirements, denominator drift, row coverage gaps, hidden target/result fields, broker evidence leakage, or evidence-class violations.
- Separate warnings from blockers. A warning is a blocker only if it changes row coverage, field status validity, source binding, no-leak status, denominator correctness, or evidence-class boundary.
- Pursue every same-audit-class ambiguity until recomputed, ruled out, or converted into an exact repair requirement.

The final completion audit must record:

- whether `goal_session_research_discipline.md` was read after preflight;
- whether `research_operating_doctrine.md` was read after preflight;
- lane posture: `G12_SCID_STRATEGY_FIELD_PACKET_AUDIT_ACCEPTANCE_FOCUSED`;
- what was independently recomputed;
- exact accepted, warning, blocker, and repair boundaries;
- what this G12 deliberately did not answer because it crosses into validation, result scoring, AI/API, broker account/order evidence, paid/vendor access, raw data commits, live behavior, or G0 synthesis.

## Hard Boundaries

Preserve `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.

Do not open validation execution, result scoring, strategy-edge claims, R/PnL/win-rate/expectancy/performance fields, broker account/order/history/deal/position evidence, AI/API calls, paid/vendor access, raw market-data blob commits, live behavior, or prompt/config/risk/safety/execution/canary/selector changes.

## Required Independent Recomputations

1. Recompute accepted source rowset from the descriptor freeze and candidate input rows.
2. Verify exactly 3,014 unique `candidate_input_row_id` values and exactly one closure row per candidate.
3. Verify every closure row carries all required field families:
   - `canonical_candidate_and_denominator`
   - `source_symbol_session_partition`
   - `intended_side_direction`
   - `intended_entry_reference`
   - `intended_stop_reference`
   - `intended_target_reference`
   - `poi_type_bounds_source`
   - `framework_setup_family`
   - `lifecycle_fill_cancel_expiry_source_status`
   - `lower_timeframe_asof_path_availability`
   - `source_control_coverage_not_computable_reasons`
   - `future_orderflow_depth_proxy_requirements`
   - `broker_account_order_history_deal_position_evidence`
4. Verify status enum validity: `CLOSED_FROM_SOURCE`, `FAIL_CLOSED_MISSING_SOURCE_FIELD`, `PROSPECTIVE_CAPTURE_REQUIRED`, `FORBIDDEN_IN_THIS_EVIDENCE_CLASS`.
5. Recompute row hashes from canonical JSON and report mismatches.
6. Verify closed source fields match descriptor/candidate packet values exactly.
7. Verify fail-closed fields do not contain inferred side, entry, stop, target, POI, setup family, or lifecycle truth.
8. Verify prospective capture requirements include exact future source/capture/logger field, parser, schema, redaction, as-of rule, and G12 acceptance requirement.
9. Verify no closure artifact contains target/result/performance fields or broker account/order/history/deal/position evidence.
10. Verify output manifest covers every required artifact and no raw `.scid`, `.parquet`, `.csv`, `.dly`, `.bin`, `.depth`, or market-data blob was introduced by the builder diff.
11. Verify no prompt/config/risk/safety/execution/canary/selector/source trading-surface files were edited by the builder route.

## Required Saturation And Self-Red-Team Pass

Before completion, explicitly answer and pursue same-audit-class issues exposed by these questions:

- Could any fail-closed strategy field actually have source evidence in the searched artifacts?
- Could any closed field be a projection or derived convenience field rather than source truth?
- Could any source inventory path omission make the missing-field conclusion too weak?
- Could any field status allow price-only inference of historical intent, side, entry, stop, target, POI, setup family, or lifecycle?
- Could duplicate/proxy denominator keys allow one candidate to borrow another candidate's source fields?
- Could prospective capture requirements be too vague for a future implementation/G12 to verify?
- Could any target/neutral behavior value leak into source-field status or field closure?
- Could the audit accidentally treat forbidden broker account/order/history/deal/position evidence as merely absent rather than forbidden?
- If accepted, what exact next G0 route should synthesize: result-design readiness, capture-only closure, broader source search, or negative learning?

If any answer exposes an allowed audit-class gap, pursue it before completion. If the next action crosses into G0 synthesis, validation, result scoring, broker evidence, AI/API, paid/vendor access, raw data commits, live behavior, or source-trading-surface changes, freeze it as a next prompt requirement instead.

## Fair Acceptance Boundary

Accept the packet if source-safe fields are closed, missing historical strategy-intent fields are fail-closed with exact prospective requirements, and forbidden surfaces remain closed. Do not reject merely because most strategy fields are fail-closed: the builder lane is allowed to prove absence and emit exact capture requirements. Reject if any field is inferred from price movement, any target/result/performance or broker evidence leaks in, row coverage or denominator keys drift, or requirements are vague.

## Required Outputs

Create a route under:

`research/science_program_2026_05/06_outcome_testing/g12_scid_strategy_field_source_expansion_packet_audit/`

Emit at minimum:

- context anchor;
- prerequisite evidence-chain reconciliation audit;
- row coverage and duplicate/denominator recomputation audit;
- field-status enum and closed-field recomputation audit;
- fail-closed/prospective/forbidden status audit;
- no-leak/forbidden-surface/raw-blob/trading-surface audit;
- source hash/input binding audit;
- saturation/self-red-team ledger;
- decision ledger;
- output manifest;
- standalone verifier;
- focused tests;
- completion audit;
- closeout verification;
- next G0 synthesis/control prompt if accepted, or exact repair prompt if rejected.

The next prompt must be a full hardened controlling prompt file, not a brief pack. If accepted, the next G0 prompt must decide whether the source-field packet opens result-design readiness, forward capture implementation, broader source search, or negative-learning route.

## Allowed Terminal Decisions

Use exactly one:

- `ACCEPT_AS_G12_SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_CONTROL_EVIDENCE_ONLY`
- `REPAIR_SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_REQUIRED`
- `REJECT_FOR_EVIDENCE_CLASS_VIOLATION`

## Completion Standard

Mark complete only after every required recomputation is written to disk, mandatory context use is recorded, saturation/self-red-team is complete, the verifier passes, focused tests pass, next G0-or-repair prompt is emitted, scoped commits are created, `.context/00_core/research_current_state.md` is refreshed if materially stale, final `python scripts/generate_live_state.py` is run, and no unrelated runtime/shadow/live dirt is staged.

## One-Line Starter

`/goal Follow the full controlling prompt in research/science_program_2026_05/04_goal_prompts/G12_SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_AUDIT_GOAL_PROMPT_2026-05-12.md as the complete objective; do mandatory preflight and context refresh first; do not rely on chat memory; stay G12_SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_AUDIT_ONLY with no validation/strategy-edge/R/PnL/win-rate/expectancy/performance/promotion/live behavior/AI/API/paid-vendor/broker-account-order-history-deal-position/raw-market-blob/prompt-config-risk-safety-execution-canary-selector changes; independently recompute row coverage, field statuses, source bindings, fail-closed/prospective/forbidden statuses, no-leak, denominator, raw-blob, and live-surface scope for all 3,014 SCID candidates; accept exact fail-closed historical absence when proven, reject inference/leakage/vague requirements, emit audit route, verifier, focused tests, next G0-or-repair prompt, scoped commits, closeout verification, NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false; mark complete only when the prompt file's completion standard is fully satisfied.`
