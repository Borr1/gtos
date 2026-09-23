# G12 NOFILL Forward Source-Capture Additive Logger Implementation Audit Goal Prompt

Date: 2026-05-10
Owner lane: independent G12 implementation acceptance audit
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Goal

Run an independent G12 audit of `NOFILL_FORWARD_SOURCE_CAPTURE_ADDITIVE_LOGGER_IMPLEMENTATION`.

The target implementation package is:

- `research/science_program_2026_05/06_outcome_testing/nofill_forward_source_capture_additive_logger_implementation/`

The target code changes are:

- `src/research_infra/forward_capture.py`
- `tests/test_forward_capture_shadow_loggers.py`

The audit must decide whether the implementation is acceptable as source/control implementation evidence only. It must not open result/cost scoring, validation, promotion, registry edits, paid/API routes, remote push, live logger evidence promotion, or live trading behavior.

Expected terminal decisions:

- `ACCEPT_AS_SOURCE_CONTROL_IMPLEMENTATION_EVIDENCE_ONLY`
- `ACCEPT_WITH_EXACT_REPAIR_BLOCKERS`
- `REJECT_INVALID_IMPLEMENTATION`

Acceptance does not make the logger validation-safe or promotion-safe. If accepted, the next allowed route is shadow-only observation/readiness review or G0 synthesis; result/cost scoring and promotion remain separate future evidence-class gates.

## Mandatory Preflight And Context

1. Run `python scripts\generate_live_state.py`.
2. Read `.context\LIVE_STATE.md`.
3. Read latest numbered `.context\02_session_handoffs\*`.
4. Read `.context\00_core\quick_reference_card.md`.
5. Read `.context\00_core\research_operating_doctrine.md`.
6. Read `.context\00_core\research_current_state.md`.
7. Read `.context\00_core\goal_session_research_discipline.md`.
8. Read `.context\00_core\local_heavy_data_inventory.md`.
9. Read this prompt and record exact HEAD and prompt path in the audit context anchor.

Do not rely on chat memory. If context compaction, resume, or uncertainty occurs, regenerate live state, re-read this prompt and core context docs, re-read the audit context anchor/latest artifacts, and continue from disk.

## Controlling Inputs

Implementation artifacts:

- `NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DECISION_LEDGER_2026-05-10.json`
- `NOFILL_FORWARD_SOURCE_CAPTURE_55_FIELD_IMPLEMENTATION_COVERAGE_LEDGER_2026-05-10.json`
- `NOFILL_FORWARD_SOURCE_CAPTURE_NOLEAK_REDACTION_AUDIT_2026-05-10.json`
- `NOFILL_FORWARD_SOURCE_CAPTURE_FAILOPEN_NO_LIVE_BEHAVIOR_AUDIT_2026-05-10.json`
- `NOFILL_FORWARD_SOURCE_CAPTURE_FIXTURE_TEST_MATRIX_2026-05-10.json`
- `NOFILL_FORWARD_SOURCE_CAPTURE_SOURCE_CODE_HASH_MANIFEST_2026-05-10.json`
- `NOFILL_FORWARD_SOURCE_CAPTURE_ROLLBACK_DISABLE_LEDGER_2026-05-10.json`
- `NOFILL_FORWARD_SOURCE_CAPTURE_SATURATION_SELF_REDTEAM_2026-05-10.json`
- `NOFILL_FORWARD_SOURCE_CAPTURE_INSTRUCTION_COVERAGE_CHECKLIST_2026-05-10.json`
- `NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_COMPLETION_AUDIT_2026-05-10.json`
- `NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_VERIFICATION_RESULT_2026-05-10.json`
- implementation builder, verifier, and focused tests

Accepted upstream design/audit:

- `nofill_forward_source_capture_implementation_design_plan/`
- `g12_nofill_forward_source_capture_implementation_design_audit/`

Code surfaces:

- `src/research_infra/forward_capture.py`
- `tests/test_forward_capture_shadow_loggers.py`

## Hardening Standard

Operate at maximum practical reasoning depth. Enforce curiosity, truthfulness, and active creativity, but keep this audit in the implementation-acceptance evidence class.

Do not rubber-stamp the implementation. Try to break it:

- independently recompute the 55-field runtime contract from `NOFILL_FORWARD_SOURCE_CAPTURE_FIELDS`;
- verify the 20 future logger fields from `NOFILL_FORWARD_SOURCE_CAPTURE_FUTURE_LOGGER_FIELDS`;
- verify fail-closed status vocabulary and missing-status mapping;
- prove forbidden raw fields are neither emitted nor hashed;
- prove redaction status fields are status-only;
- prove `record_nofill_forward_source_capture` is fail-open and returns `None`;
- prove `record_live_candidate_forward_shadow` only makes an additive fail-open source-capture write and does not consume the new writer return value;
- prove no order parameters, safety gates, prompts, config, risk, permissions, selectors, canaries, MT5 order/account/history/deal/position behavior, registry, paid/API route, remote, scoring, validation, or promotion path changed;
- rerun or independently verify implementation tests and verifier;
- inspect the diff, not just generated artifacts;
- check whether any same-evidence-class issue can be repaired by the audit or must become an exact repair blocker.

Examples and listed artifacts are starting points, not boundaries. If another local artifact, prior worktree, generated verifier, source contract, test, source/log/code path, or local-heavy-data root could materially change the audit answer, inspect it or exactly rule it out.

Split only if the next step would cross into result/cost scoring, validation, promotion, registry edits, paid/API/live trading behavior, remote push, credentials, or a forbidden broker/account/order evidence route.

## Required Audit Questions

1. Does runtime code truly define exactly 55 source-capture fields and 20 future logger fields?
2. Does every accepted field emit or fail-close according to the G12-accepted design?
3. Does the implementation prevent raw broker/account/order/deal/position/ticket/result/cost/slippage/execution-quality leakage and raw-value hashing?
4. Is the writer fail-open, exception-safe, and return-value ignored by decision code?
5. Is `record_live_candidate_forward_shadow` still behaviorally equivalent for existing logs and trading decisions except for the additive source-capture JSONL write?
6. Do tests prove no existing shadow log semantics changed?
7. Does the verifier catch field-count drift, missing future fields, unsafe true flags, forbidden output keys, malformed hashes, and leakage?
8. Are source/code hash manifests and rollback/disable paths sufficient?
9. What exact repair blockers, if any, must be closed before source/control implementation reliance?
10. What exact next lane is allowed after acceptance, and what remains forbidden?

## Required Saturation And Self-Red-Team Pass

Before completion, write a lane-specific saturation pass that tries to reject the implementation and then pursues any same-evidence-class gap it exposes.

The saturation pass must answer and act on these questions:

1. What exact code mistake would let the additive writer change trading behavior?
2. What exact code mistake would let a raw ticket/order/deal/account/history/result/cost value leak into output or a hash?
3. What exact code mistake would let validation/promotion/result scoring be inferred from source/control fields?
4. What exact test weakness would let fixtures pass while real source-safe rows fail?
5. What exact diff-scope weakness would hide an execution/risk/safety/config change?
6. What exact rollback weakness would make the logger hard to disable or ignore?
7. What exact same-evidence-class repair can be done now if a weakness is found?
8. What would a skeptical G12/G0 reviewer reject, and did this audit preempt it with proof or record an exact repair blocker?

If any answer exposes an allowed same-evidence-class gap, pursue it inside this audit until it is resolved, proven impossible from approved routes, or converted into an exact repair blocker. "Outside scope" is acceptable only when the next step crosses into scoring, validation, promotion, registry edit, paid/API, remote, credential, forbidden broker/account/order evidence, or live trading behavior change.

## Required Outputs

Create:

`research/science_program_2026_05/06_outcome_testing/g12_nofill_forward_source_capture_additive_logger_implementation_audit/`

At minimum produce:

- context anchor
- G12 decision ledger
- runtime 55-field contract audit
- future logger field audit
- fail-open/no-live-behavior audit
- forbidden/redaction/no-leak audit
- diff-scope and call-path audit
- verifier/test rerun report
- source/code hash audit
- saturation/self-red-team pass
- instruction-coverage checklist
- exact repair blocker ledger, even if empty
- next lane prompt pack
- completion audit
- G12 audit builder, verifier, and focused tests

Update `.context/00_core/research_current_state.md` after the audit commit.

## Verification Required

- Parse all generated JSON/JSONL/Markdown control artifacts.
- Run implementation verifier and implementation focused tests.
- Run relevant existing focused tests for changed modules.
- Run new G12 verifier and focused tests.
- Run `python -B -m py_compile` or AST syntax fallback if Windows blocks bytecode writes.
- Recompute field counts from code constants, not Markdown.
- Inspect committed diff scope and verify only allowed source/test/research/context files changed.
- Scan changed code and generated artifacts for unresolved placeholders including `TBD`, `TODO`, `unknown`, `maybe`, `later`, and `not yet decided`.
- Scan changed code and generated artifacts for forbidden raw broker/account/order/deal/position/ticket/result/cost/slippage/execution-quality leakage or raw-value hashing.
- Confirm no generated artifact sets `validation_safe`, `outcome_review_opened`, or `live_effect` to true.
- Confirm no live trading prompt/config/risk/execution decision/permissions/safety/selector/canary/MT5 order-account-history behavior, registry promotion, paid/API route, credential, remote, scoring, validation, or promotion route opened.
- Regenerate `LIVE_STATE.md` at closeout and ensure research context is fresh or explain generated snapshot dirt.

## Completion Standard

The goal is complete only when G12 has an explicit terminal decision, every required artifact exists, machine-checkable verification passes, and any blocker is exact enough for a repair lane.

Acceptance is allowed only if:

- runtime code defines exactly 55 accepted fields and exactly 20 future logger fields;
- all future fields emit or fail-close using accepted status vocabulary;
- forbidden/redacted fields are status-only and no raw value/hash leaks;
- writer is fail-open and its return value is not consumed by trading decisions;
- existing shadow log behavior is not broken;
- diff scope is limited and no forbidden live surface changed;
- saturation/self-red-team pass is complete;
- instruction-coverage checklist is complete;
- `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false` are preserved.

If accepted, the implementation remains source/control evidence only. Result/cost scoring, validation, promotion, registry edits, paid/API routes, remote push, and live trading behavior remain closed until separately approved and audited.
