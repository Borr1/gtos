# NOFILL Forward Source-Capture Additive Logger Implementation Goal Prompt

Date: 2026-05-10
Owner lane: owner-approved additive source/control logger implementation
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Owner Approval

The owner explicitly approved this code-wiring lane on 2026-05-10 in response to the exact approval request:

`I approve the owner-gated additive NOFILL forward source-capture logger implementation lane, source/control only, no scoring, no validation, no promotion, no live behavior changes.`

This approval opens only the additive source/control logger implementation lane. It does not open scoring, validation, promotion, registry edits, paid/API routes, remote push, result/cost labels, MT5 order/account/history/deal/position behavior, risk/execution decision changes, or any live trading behavior change.

## Goal

Implement the accepted NOFILL forward source-capture design as an additive, fail-open, source/control-only logger/parser path.

The implementation must consume the G12-accepted design package and produce code that can emit or project the accepted 55-field source-capture contract without leaking raw broker/account/order/deal/position/result/cost values and without affecting trading decisions.

Target accepted evidence:

- `research/science_program_2026_05/06_outcome_testing/nofill_forward_source_capture_implementation_design_plan/`
- `research/science_program_2026_05/06_outcome_testing/g12_nofill_forward_source_capture_implementation_design_audit/`

Terminal implementation posture must remain:

- `NO_PROMOTION_VERDICT`
- `validation_safe=false`
- `outcome_review_opened=false`
- `live_effect=false`
- `opens_result_scoring=false`
- `opens_validation=false`
- `opens_promotion=false`
- `opens_live_trading_behavior=false`

## Mandatory Preflight And Context

1. Run `python scripts\generate_live_state.py`.
2. Read `.context\LIVE_STATE.md`.
3. Read latest numbered `.context\02_session_handoffs\*`.
4. Read `.context\00_core\quick_reference_card.md`.
5. Read `.context\00_core\research_operating_doctrine.md`.
6. Read `.context\00_core\research_current_state.md`.
7. Read `.context\00_core\goal_session_research_discipline.md`.
8. Read `.context\00_core\local_heavy_data_inventory.md`.
9. Read this prompt and record exact HEAD, owner approval line, and prompt path in the implementation context anchor.

Do not rely on chat memory. If context compaction, resume, or uncertainty occurs, regenerate live state, re-read this prompt and core context docs, re-read the implementation context anchor/latest artifacts, and continue from disk.

## Controlling Inputs

Primary accepted design/control artifacts:

- `NOFILL_FORWARD_SOURCE_CONTRACT_IMPLEMENTATION_MAP_2026-05-10.json`
- `NOFILL_FORWARD_SOURCE_CAPTURE_FUTURE_LOGGER_EMISSION_DESIGN_2026-05-10.json`
- `NOFILL_FORWARD_SOURCE_CAPTURE_PARSER_PROJECTION_SCHEMA_2026-05-10.json`
- `NOFILL_FORWARD_SOURCE_CAPTURE_FAIL_CLOSED_STATUS_VOCABULARY_2026-05-10.json`
- `NOFILL_FORWARD_SOURCE_CAPTURE_FORBIDDEN_FIELD_REDACTION_POLICY_2026-05-10.json`
- `NOFILL_FORWARD_SOURCE_CAPTURE_FIXTURE_TEST_MATRIX_2026-05-10.json`
- `NOFILL_FORWARD_SOURCE_CAPTURE_G12_ACCEPTANCE_CHECKLIST_2026-05-10.json`
- `NOFILL_FORWARD_SOURCE_CAPTURE_OPERATIONAL_RISK_ROLLBACK_LEDGER_2026-05-10.json`
- `NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DEPENDENCY_GRAPH_2026-05-10.json`
- `NOFILL_FORWARD_SOURCE_CAPTURE_OWNER_APPROVAL_GATE_LEDGER_2026-05-10.json`

Independent G12 acceptance artifacts:

- `G12_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_AUDIT_DECISION_LEDGER_2026-05-10.json`
- `G12_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_COMPLETION_AUDIT_2026-05-10.json`
- `G12_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_FUTURE_LOGGER_SUFFICIENCY_AUDIT_2026-05-10.json`
- `G12_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_REPAIR_BLOCKER_LEDGER_2026-05-10.json`
- `G12_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_SATURATION_REDTEAM_2026-05-10.json`
- `G12_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_INSTRUCTION_COVERAGE_CHECKLIST_2026-05-10.json`

Existing code surfaces to inspect first:

- `src/research_infra/forward_capture.py`
- `src/components/pending_limit_lifecycle_logger.py`
- `src/research_infra/pending_limit_lifecycle_audit.py`
- existing tests for forward capture, pending lifecycle, shadow-log integrity, and source-control projection

## Allowed Write Scope

Allowed implementation write surfaces:

- `src/research_infra/forward_capture.py`
- `src/components/pending_limit_lifecycle_logger.py`
- new or existing tests under `tests/`
- new research/control artifacts under `research/science_program_2026_05/06_outcome_testing/nofill_forward_source_capture_additive_logger_implementation/`
- `.context/00_core/research_current_state.md`

Conditionally allowed only if strictly necessary and proven no-effect:

- the minimal existing shadow/logging call site that already emits research-only pending lifecycle or forward-capture rows. If this touches `src/components/execution.py`, the change must be limited to a fail-open call to the new source-capture writer, must not change order parameters, safety gates, return values, exceptions, decision branches, timing decisions, MT5 calls, or live state, and must be covered by a no-live-behavior regression test.

Forbidden write surfaces:

- `prompts/`
- `config/`
- risk, permissions, safety, selector, canary, registry, credential, remote, `start_all.bat`, `run_agent.py`, MT5 order/account/history/deal/position behavior, production order logic, or any file whose edit would alter trade decisions, order placement, risk sizing, model prompts, safety gates, or deployment configuration.

If implementation requires a forbidden surface, stop and record an exact implementation blocker instead of editing it.

## Hardening Standard

Operate at maximum practical reasoning depth. Enforce curiosity, truthfulness, and active creativity while staying inside this owner-approved implementation evidence class.

Do not implement a shallow placeholder. Pursue the lane to proof-or-impossibility:

- implement or project all accepted 55 fields;
- emit all 20 future logger fields or exact fail-closed statuses from the accepted vocabulary;
- preserve all 17 existing source-safe fields, 11 schema/control fields, and 7 forbidden/redacted status-only fields;
- never emit or hash raw broker account, order, deal, position, ticket, result, slippage-cost, execution-quality, actual-R, synthetic-R, win/loss, TP/SL outcome, or promotion fields;
- make the writer fail-open: exceptions are swallowed/logged and no return value is consumed by trading decisions;
- make the implementation additive: no existing shadow log field semantics are changed;
- include deterministic parser/projection helpers, fixture rows, source hash or code hash controls, and redaction/no-leak checks;
- include rollback proof: one obvious way to disable or ignore the new logger without touching order behavior;
- include a next G12 implementation acceptance prompt pack.

Examples and listed files are starting points, not boundaries. If another source-safe code path, prior lane, generated verifier, existing logger pattern, source contract, heavy-data root, or test could materially affect correctness, inspect it or exactly rule it out. Do not stop at "needs implementation"; this is the implementation lane. Stop only at proof, exact impossibility from approved routes, exact forbidden-boundary crossing, or exact owner/source approval need.

## Required Implementation Questions

1. What exact functions/classes/constants implement the 55-field source-capture contract?
2. How are the 20 future logger fields emitted or fail-closed?
3. How does the implementation preserve/redact the 7 forbidden or redacted fields without raw value leakage?
4. How does the writer stay fail-open and non-decision-impacting?
5. What exact source-safe input rows can build a projection without raw account/order/deal/position/result/cost leakage?
6. What exact fixture cases prove write-clock, clock-skew, pending-order observability, spread snapshot, lifecycle path, duplicate/hash, forbidden-field, and missing-status behavior?
7. What exact tests prove no live trading behavior, order parameters, safety gates, prompts, config, risk, permissions, selectors, canaries, MT5 account/order/history behavior, registry, paid/API, or remote route changed?
8. What exact G12 acceptance checks should the next audit run?
9. If any field cannot be implemented source-safely, what exact blocker remains and why was it not already closed by the design package?
10. What exact rollback or disable path exists without affecting existing trading behavior?

## Required Saturation And Self-Red-Team Pass

Before completion, write a lane-specific saturation pass that tries to reject the implementation and then pursues any same-evidence-class gap it exposes.

The saturation pass must answer and act on these questions:

1. What exact mistake would let the additive logger affect order placement, risk, safety gates, prompts, config, or MT5 behavior?
2. What exact mistake would let a raw ticket/order/deal/account/history/result/cost value leak into the new log or hash?
3. What exact mistake would let result scoring, validation, or promotion be inferred from source/control fields?
4. What exact mistake would let fail-closed statuses mask missing required source data?
5. What exact mistake would let existing shadow log semantics change?
6. What exact mistake would let a broad code edit hide inside "logger wiring"?
7. What exact mistake would make tests pass on fixtures but fail on real source-safe rows?
8. What would a skeptical G12 audit reject, and did this implementation preempt it with proof or record an exact repair blocker?

If any answer exposes an allowed same-evidence-class gap, pursue it inside this implementation until it is resolved, proven impossible from approved routes, or converted into an exact repair blocker. "Outside scope" is acceptable only when the next step crosses into scoring, validation, promotion, registry edit, paid/API, remote, credential, forbidden broker/account/order evidence, or live trading behavior change.

## Required Outputs

Create:

`research/science_program_2026_05/06_outcome_testing/nofill_forward_source_capture_additive_logger_implementation/`

At minimum produce:

- implementation context anchor with owner approval line
- implementation decision ledger
- 55-field implementation coverage ledger
- no-leak/redaction audit
- fail-open/no-live-behavior audit
- fixture/test matrix
- source/code hash manifest
- rollback/disable ledger
- saturation/self-red-team pass
- instruction-coverage checklist
- next G12 implementation acceptance prompt pack
- completion audit
- implementation verifier and focused tests

Update `.context/00_core/research_current_state.md` after the implementation commit.

## Verification Required

- Parse all generated JSON/JSONL/Markdown control artifacts.
- Run `python -B -m py_compile` or AST syntax fallback if Windows blocks bytecode writes.
- Run focused pytest with `-p no:cacheprovider` and controlled `--basetemp`.
- Run the new implementation verifier.
- Run relevant existing focused tests for changed modules, at minimum tests covering forward capture, pending lifecycle logger, and any touched call site.
- Recompute the 55-field implementation coverage from code/tests/artifacts.
- Scan generated artifacts and changed source for unresolved placeholders including `TBD`, `TODO`, `unknown`, `maybe`, `later`, and `not yet decided`; distinguish quoted historical text from active implementation fields.
- Scan changed code/artifacts for forbidden raw broker/account/order/deal/position/result/cost field emission or hashing.
- Confirm no generated artifact sets `validation_safe`, `outcome_review_opened`, or `live_effect` to true.
- Confirm committed diff scope matches allowed write surfaces.
- Confirm no live trading prompt/config/risk/execution decision/permissions/safety/selector/canary/MT5 order-account-history behavior, registry promotion, paid/API route, credential, remote, scoring, validation, or promotion route opened.
- Regenerate `LIVE_STATE.md` at closeout and ensure research context is fresh or explain generated snapshot dirt.

## Completion Standard

The goal is complete only when the additive source-capture implementation is in code, tested, verified, committed, and still source/control-only.

Completion requires:

- 55/55 accepted source-capture fields implemented or fail-closed according to the accepted design;
- all 20 future logger fields are emitted or fail-closed with accepted status vocabulary;
- forbidden/redacted fields emit status only and no raw value/hash;
- writer is fail-open and no return value is consumed by trading decisions;
- no existing trading behavior, prompts, config, risk, permissions, safety, selectors, canaries, MT5 behavior, registry, remote, scoring, validation, promotion, or paid/API route changed;
- saturation/self-red-team pass complete;
- instruction-coverage checklist complete;
- verifier and focused tests pass or environment friction is separated from code failure;
- next G12 implementation acceptance prompt pack exists.

This implementation does not itself make the logger evidence validation-safe or promotion-safe. The next required gate after this goal is independent G12 acceptance of the implementation package.
