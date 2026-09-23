# G0 NOFILL Forward Source-Capture Implementation Synthesis Readiness Route Goal Prompt

Date: 2026-05-10
Owner lane: G0 synthesis/control plus shadow-readiness route
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Goal

Run a G0 synthesis/control route after the independent G12 acceptance of the additive NOFILL forward source-capture implementation.

The route must decide exactly what the accepted implementation enables next, what remains forbidden, what observation/readiness evidence is still needed, and what the next strongest goal lane should be.

This is not a result, cost, validation, promotion, registry, paid/API, remote, or live-behavior lane. It must not restart live orchestrators, change live trading behavior, edit prompts/config/risk/permissions/safety/selectors/canaries/MT5 order/account/history behavior, or open scoring. If a live restart, live observation, or owner action is needed to collect rows, record the exact owner-gated action and do not perform it.

Expected terminal decisions:

- `ACCEPT_AS_G0_SOURCE_CONTROL_SYNTHESIS_AND_SHADOW_READINESS_ROUTE`
- `ACCEPT_WITH_EXACT_SOURCE_CONTROL_REPAIR_BLOCKERS`
- `BLOCKED_WITH_EXACT_OWNER_OR_LIVE_OPERATION_APPROVAL_REQUIREMENT`
- `REJECT_INVALID_SYNTHESIS_OR_CONTEXT_DRIFT`

## Mandatory Preflight And Context

1. Run `python scripts\generate_live_state.py`.
2. Read `.context\LIVE_STATE.md`.
3. Read latest numbered `.context\02_session_handoffs\*`.
4. Read `.context\00_core\quick_reference_card.md`.
5. Read `.context\00_core\research_operating_doctrine.md`.
6. Read `.context\00_core\research_current_state.md`.
7. Read `.context\00_core\goal_session_research_discipline.md`.
8. Read `.context\00_core\local_heavy_data_inventory.md`.
9. Read this prompt and record exact HEAD and prompt path in a context anchor.

Do not rely on chat memory. If context compaction, resume, or uncertainty occurs, regenerate live state, re-read this prompt and core context docs, re-read the route context anchor/latest artifacts, and continue from disk.

## Controlling Inputs

Accepted implementation audit:

- `research/science_program_2026_05/06_outcome_testing/g12_nofill_forward_source_capture_additive_logger_implementation_audit/`
- `G12_NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION_AUDIT_DECISION_LEDGER_2026-05-10.json`
- `G12_NOFILL_FORWARD_SOURCE_CAPTURE_AUDIT_COMPLETION_AUDIT_2026-05-10.json`
- `G12_NOFILL_FORWARD_SOURCE_CAPTURE_RUNTIME_55_FIELD_CONTRACT_AUDIT_2026-05-10.json`
- `G12_NOFILL_FORWARD_SOURCE_CAPTURE_FUTURE_LOGGER_FIELD_AUDIT_2026-05-10.json`
- `G12_NOFILL_FORWARD_SOURCE_CAPTURE_FAILOPEN_NO_LIVE_BEHAVIOR_AUDIT_2026-05-10.json`
- `G12_NOFILL_FORWARD_SOURCE_CAPTURE_FORBIDDEN_REDACTION_NOLEAK_AUDIT_2026-05-10.json`
- `G12_NOFILL_FORWARD_SOURCE_CAPTURE_EXACT_REPAIR_BLOCKER_LEDGER_2026-05-10.json`

Accepted implementation package:

- `research/science_program_2026_05/06_outcome_testing/nofill_forward_source_capture_additive_logger_implementation/`
- `src/research_infra/forward_capture.py`
- `tests/test_forward_capture_shadow_loggers.py`

Upstream evidence chain:

- `g12_nofill_forward_source_capture_implementation_design_audit/`
- `nofill_forward_source_capture_implementation_design_plan/`
- `g12_nofill_forward_source_capture_text_gate_repair_reaudit/`
- `g12_nofill_forward_projection_repair_reaudit/`
- `nofill_forward_source_safe_projection_builder/`
- `nofill_cat_v3_source_control_rebuild/`
- `g12_nofill_cat_v3_source_control_audit/`
- `g12_nofill_cat_v3_quarantined_categorical_count_packet_audit/`
- `g0_nofill_cat_v3_categorical_evidence_synthesis_control_review/`

Potential runtime/source-control outputs to inspect if present:

- `shadow_logs/nofill_forward_source_capture.jsonl`
- `shadow_logs/live_candidate_strategy_rollups.jsonl`
- `shadow_logs/prefill_delivery_path.jsonl`
- `shadow_logs/context_control_ledger.jsonl`
- `shadow_logs/candidate_path_follow.jsonl`
- relevant `pipeline_state/` and generated status files only as context, not as committed evidence unless explicitly required

## Hardening Standard

Operate at maximum practical reasoning depth. Enforce curiosity, truthfulness, and active creativity, but keep this route in the G0 source/control and shadow-readiness evidence class.

Do not produce a shallow "next steps" note. Reconstruct the evidence chain from NOFILL CAT V3 through source-control rebuild, forward projection, source-capture contract, implementation design, additive implementation, and G12 implementation acceptance. Search local artifacts, code, tests, logs, manifests, prior route outputs, and relevant worktree-independent local roots before declaring any missing source or readiness blocker.

Examples and listed files are starting points, not boundaries. Check whether the prompt is boxed by the current worktree, latest summary, current timeframe, current symbol, current data modality, current logger, or first framing. If another local artifact, prior worktree, source contract, test, source/log/code path, cached doc, or local-heavy-data root could materially change the synthesis, inspect it or exactly rule it out.

Use the hostile edge-review lens: attack the evidence chain as possibly fake or incomplete. Ask which claim could be mistaken for result evidence, which source field could hide leakage, which duplicate denominator could contaminate future counts, which runtime assumption could fail under restart or clock skew, and which future cost/execution/regime claim is not yet justified.

Split only if the next step crosses into result/cost scoring, validation, promotion, registry edits, paid/API/live trading behavior, remote push, credentials, or forbidden broker/account/order evidence. Inside source/control/readiness, pursue blockers until cleared, proven impossible from approved inputs, or reduced to an exact owner/access/source/capture/live-operation approval requirement.

## Required Questions

1. Is the accepted additive logger implementation now canonical source/control implementation evidence on main?
2. What exact source/control evidence has been accepted from CAT V3 through the G12 implementation audit?
3. What exact observation/readiness evidence is needed before forward NOFILL source-capture rows can be trusted as research-control inputs?
4. Does the current code/log path require a live orchestrator restart or other owner action before rows can be produced, and what exact action is owner-gated?
5. If rows already exist, do they conform to the 55-field schema, 20 future-field fail-close behavior, no-leak/redaction rules, and safe flags?
6. If rows do not exist, is that an expected no-row state, a restart/deployment state, a market-session state, or a broken logger state?
7. What verifier or monitor should be run later to check row count, schema, source hashes, fail-closed fields, duplicate keys, and forbidden leakage without touching live behavior?
8. What future evidence-class gates are required before result/cost scoring, sealed historical validation, forward validation, promotion, or live scaling?
9. Which historical sealed-validation route can run in parallel without waiting for forward rows, and which fields from the source-capture logger should feed it later?
10. What exact next goal prompt should be run after this synthesis, and why is it the strongest next move?

## Required Saturation And Self-Red-Team Pass

Before completion, write a lane-specific saturation pass that tries to reject the readiness route and then pursues any same-evidence-class gap it exposes.

The saturation pass must answer and act on these questions:

1. What exact mistake would make source-control implementation evidence look like result, cost, validation, or promotion evidence?
2. What exact mistake would let blocked, source-control, source-impossible, or rejected rows leak into future denominators?
3. What exact runtime state could make the logger silently produce no rows, malformed rows, duplicate rows, or rows with stale context?
4. What exact restart/deployment assumption could be false, and how should the owner verify it without changing trading logic?
5. What exact source/log/code path should be searched before accepting a no-row or missing-field blocker?
6. What exact monitor/verifier weakness would fail to catch forbidden raw value leakage or schema drift?
7. What would a skeptical G12/G0 reviewer reject in the current readiness chain?
8. What is deliberately not answered here, and what exact future lane owns it?

If any answer exposes an allowed same-evidence-class gap, pursue it inside this route until it is resolved, proven impossible, or converted into an exact owner/access/source/capture/live-operation approval requirement.

## Required Outputs

Create:

`research/science_program_2026_05/06_outcome_testing/g0_nofill_forward_source_capture_implementation_synthesis_readiness_route/`

At minimum produce:

- context anchor
- G0 decision ledger
- evidence-chain reconciliation from CAT V3 to accepted implementation
- source-control versus result/cost/validation/promotion separation ledger
- shadow-readiness and observation-state audit
- owner-gated restart/deployment/action ledger, even if no action is needed
- no-row/malformed-row/missing-field diagnostic decision tree
- future monitor/verifier specification
- duplicate/denominator contamination risk review
- historical sealed-validation parallel-route note
- forbidden route ledger
- saturation/self-red-team pass
- instruction-coverage checklist
- exact blocker or approval requirement ledger, even if empty
- next prompt pack with a one-line starter message using `.context/00_core/goal_session_research_discipline.md`
- completion audit
- route builder, verifier, and focused tests where useful

Update `.context/00_core/research_current_state.md` after the route commit.

## Verification Required

- Parse all generated JSON/JSONL/Markdown control artifacts.
- Re-read and cite the G12 implementation audit terminal decision and zero-blocker ledger.
- Inspect the runtime code path for source-capture writer location and whether a live restart/action is needed for active processes to use it.
- If `shadow_logs/nofill_forward_source_capture.jsonl` exists, parse it read-only and audit schema/no-leak/safe flags.
- If it does not exist, record exact no-row diagnostic status and whether that is expected before restart/new opportunities.
- Run new route verifier and focused tests.
- Run `python -B -m py_compile` or AST syntax fallback if Windows blocks bytecode writes.
- Confirm no generated artifact sets `validation_safe`, `outcome_review_opened`, or `live_effect` to true.
- Confirm no live trading prompt/config/risk/execution decision/permissions/safety/selector/canary/MT5 order-account-history behavior, registry promotion, paid/API route, credential, remote, scoring, validation, or promotion route opened.
- Regenerate `LIVE_STATE.md` at closeout and ensure research context is fresh or explain generated snapshot dirt.

## Completion Standard

The goal is complete only when G0 has an explicit terminal decision, every required artifact exists, machine-checkable verification passes, and the exact next route is specified.

Acceptance is allowed only if:

- the accepted implementation audit is reconciled on current main;
- source/control implementation evidence is clearly separated from result/cost/validation/promotion evidence;
- shadow readiness is diagnosed as ready, expected-no-row, exact-repair-blocked, or exact-owner/live-operation-approval-blocked;
- future monitor/verifier requirements are exact;
- historical sealed-validation and forward shadow realism are separated;
- saturation/self-red-team pass is complete;
- instruction coverage is complete;
- `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false` are preserved.

If accepted, the route remains G0 source/control synthesis and shadow-readiness evidence only. Result/cost scoring, validation, promotion, registry edits, paid/API routes, remote push, live restarts, and live trading behavior remain closed until separately approved and audited.
