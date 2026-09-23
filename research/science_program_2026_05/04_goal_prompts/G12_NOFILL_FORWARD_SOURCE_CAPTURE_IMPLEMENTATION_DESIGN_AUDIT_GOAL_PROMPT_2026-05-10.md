# G12 NOFILL Forward Source-Capture Implementation Design Audit Goal Prompt

Date: 2026-05-10
Owner lane: independent G12 source/control design acceptance audit
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Goal

Run an independent G12 audit of `NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_PLAN`.

The target package is:

- `research/science_program_2026_05/06_outcome_testing/nofill_forward_source_capture_implementation_design_plan/`

The audit must decide whether the design package is acceptable as source/control implementation-design evidence only, with no live logger wiring, no scoring, no validation, no promotion, no registry edit, no paid/API route, no remote push, and no live trading behavior.

Expected terminal decisions:

- `ACCEPT_AS_SOURCE_CONTROL_IMPLEMENTATION_DESIGN_EVIDENCE_ONLY`
- `ACCEPT_WITH_EXACT_REPAIR_BLOCKERS`
- `REJECT_INVALID_DESIGN_CLOSURE`

Do not treat acceptance as permission to edit live code. If accepted, the next implementation lane still requires explicit owner approval for additive logger wiring.

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

Primary target package:

- `NOFILL_FORWARD_SOURCE_CONTRACT_IMPLEMENTATION_MAP_2026-05-10.json`
- `NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_COMPLETION_AUDIT_2026-05-10.json`
- `NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DESIGN_VERIFICATION_RESULT_2026-05-10.json`
- `NOFILL_FORWARD_SOURCE_CAPTURE_FUTURE_LOGGER_EMISSION_DESIGN_2026-05-10.json`
- `NOFILL_FORWARD_SOURCE_CAPTURE_FORBIDDEN_FIELD_REDACTION_POLICY_2026-05-10.json`
- `NOFILL_FORWARD_SOURCE_CAPTURE_FAIL_CLOSED_STATUS_VOCABULARY_2026-05-10.json`
- `NOFILL_FORWARD_SOURCE_CAPTURE_PARSER_PROJECTION_SCHEMA_2026-05-10.json`
- `NOFILL_FORWARD_SOURCE_CAPTURE_FIXTURE_TEST_MATRIX_2026-05-10.json`
- `NOFILL_FORWARD_SOURCE_CAPTURE_SOURCE_HASH_MANIFEST_REQUIREMENTS_2026-05-10.json`
- `NOFILL_FORWARD_SOURCE_CAPTURE_OPERATIONAL_RISK_ROLLBACK_LEDGER_2026-05-10.json`
- `NOFILL_FORWARD_SOURCE_CAPTURE_G12_ACCEPTANCE_CHECKLIST_2026-05-10.json`
- `NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_DEPENDENCY_GRAPH_2026-05-10.json`
- `NOFILL_FORWARD_SOURCE_CAPTURE_OWNER_APPROVAL_GATE_LEDGER_2026-05-10.json`
- `NOFILL_FORWARD_SOURCE_CAPTURE_NEXT_PROMPT_PACK_2026-05-10.md`
- target builder, verifier, and focused tests in the same route folder

Required upstream context:

- `g12_nofill_forward_source_capture_text_gate_repair_reaudit/`
- `nofill_forward_source_capture_contract_hardening_offline_projection_prototype/`
- `g12_nofill_forward_projection_repair_reaudit/`
- `nofill_cat_v3_source_control_rebuild/`

## Hardening Standard

Operate at maximum practical reasoning depth. Enforce curiosity, truthfulness, and active creativity, but keep this audit in the source/control evidence class.

Do not rubber-stamp the design package. Try to break it:

- independently recompute the `55/55` field-closure equation;
- verify the five terminal status families and count equation;
- prove every `FUTURE_LOGGER_FIELD_REQUIRED` row contains exact source surface, schema field, redaction rule if applicable, fail-closed missing status, test fixture, rollback rule, and G12 acceptance check;
- prove every forbidden/redacted row avoids raw broker/account/order/deal/position/result/cost leakage;
- prove every schema-only/control row cannot be mistaken for an emitted result or live decision field;
- prove the owner-approval gates are complete and do not silently open live logger wiring;
- audit the implementation dependency graph for hidden live-surface edits;
- scan for placeholders, vague blockers, and lazy future-work wording;
- rerun or independently verify the target verifier/tests;
- check whether any same-evidence-class issue can be repaired by the audit or must become an exact repair blocker.

Examples and listed artifacts are starting points, not boundaries. If another local artifact, prior worktree, code path, source contract, heavy-data root, or generated verifier could materially affect the design acceptance decision, inspect it or record why it is irrelevant. Do not use small sample size or worktree-local file absence as a blocker for this design audit.

Split only if the next step would cross into actual live logger code edits, result/cost scoring, sealed validation, promotion, registry edits, paid/API/live trading behavior, remote push, or owner-only implementation approval.

## Required Saturation And Self-Red-Team Pass

Before completion, write a lane-specific saturation pass that tries to reject this audit and then pursues any same-evidence-class gap it exposes.

The saturation pass must answer and act on these questions:

1. What exact mistake would let source/control design evidence become live logger permission, result/cost scoring, validation, promotion, or live behavior?
2. What exact mistake would let a future logger field stay underspecified while appearing implementation-ready?
3. What exact mistake would let a schema-only or forbidden/redacted field become an emitted raw broker/account/order/deal/position/result/cost field?
4. What exact mistake would let missing-status vocabulary hide a silent capture failure?
5. What exact mistake would let owner approval gates or dependency graph wording silently authorize code wiring?
6. What exact mistake would let target package self-verification substitute for independent G12 acceptance?
7. Which prior lane, worktree, source contract, generated verifier, source/log/code path, or local-heavy-data root could materially change the audit answer, and was it inspected or exactly ruled out?
8. What would a skeptical G12/G0 reviewer reject, and did this audit preempt that rejection with proof or record an exact repair blocker?

If any answer exposes an allowed same-evidence-class gap, pursue it inside this audit until it is cleared, proven impossible from approved routes, or converted into an exact repair blocker. "Outside scope" is acceptable only when the next step crosses into live code wiring, scoring, validation, promotion, registry edit, paid/API, remote, credential, or forbidden broker/account/order evidence.

## Required Audit Questions

1. Does the package truly close exactly `55/55` fields with one allowed terminal status per field?
2. Do the status counts match the reported `17 existing`, `20 future_logger`, `11 schema_only`, `7 forbidden_or_redacted`, `0 blocked` equation?
3. Are any future logger requirements underspecified enough that a later implementation would need to reinterpret the source/control contract?
4. Are any fields incorrectly classified as existing, schema-only, or forbidden when they should be future logger fields or exact blockers?
5. Are redaction rules strong enough to prevent raw ticket/order/deal/account/history/result/cost leakage?
6. Do parser/projection schemas and missing-status vocabularies prevent silent evidence drift?
7. Are tests and fixtures sufficient to catch placeholder statuses, unsafe flags, forbidden fields, duplicate denominator drift, and live-surface changes?
8. Does the next prompt pack correctly wait for independent G12 acceptance and explicit owner approval before code wiring?
9. What exact repair blockers, if any, must be closed before implementation-design reliance?
10. What exact next lane is allowed if and only if this G12 audit accepts the design package?

## Required Outputs

Create:

`research/science_program_2026_05/06_outcome_testing/g12_nofill_forward_source_capture_implementation_design_audit/`

At minimum produce:

- context anchor
- G12 decision ledger
- independent 55-field closure audit
- future logger requirement sufficiency audit
- forbidden/redaction/no-leak audit
- schema/fail-closed/parser/projection audit
- owner approval and dependency-graph audit
- saturation/self-red-team pass
- instruction-coverage checklist
- verifier/test rerun report
- exact repair blocker ledger, even if empty
- next lane prompt pack, if accepted or accepted with repair blockers
- completion audit
- builder, verifier, and focused tests

Update `.context/00_core/research_current_state.md` after the audit commit.

## Verification Required

- Parse all generated JSON/JSONL/Markdown control artifacts.
- Run the target package verifier and focused tests, unless environment friction blocks them; if blocked, use AST/syntax fallback and record the exact environment failure separately from code failure.
- Run the new G12 verifier and focused tests.
- Recompute the 55-field closure equation and status counts from JSON, not from Markdown.
- Scan generated and target artifacts for unresolved placeholders including `TBD`, `TODO`, `unknown`, `maybe`, `later`, and `not yet decided`; distinguish quoted historical text from active terminal fields.
- Verify the saturation/self-red-team pass exists, answers every required question, and either closes each exposed gap or records an exact repair blocker.
- Verify the completion audit includes instruction-coverage status for the controlling prompt, hardening standard, saturation pass, verification steps, and forbidden-surface boundaries.
- Confirm no generated artifact sets `validation_safe`, `outcome_review_opened`, or `live_effect` to true.
- Confirm no live logger wiring, scoring, validation, promotion, registry edit, paid/API route, remote push, or live trading behavior opened.
- Check committed diff scope: no live trading prompts, `src` trading logic, config/risk/execution/permissions/safety/selectors/canary/order behavior, MT5 order/account/history/deal/position behavior, credentials, or registry promotion.
- Regenerate `LIVE_STATE.md` at closeout and ensure research context is fresh or explain generated snapshot dirt.

## Completion Standard

The goal is complete only when G12 has an explicit terminal decision, every required artifact exists, machine-checkable verification passes, and any blocker is exact enough for a repair lane.

Acceptance is allowed only if:

- `55/55` fields close with allowed statuses and no duplicates/missing fields;
- status counts match the target design claim or any discrepancy is explained and terminally decided;
- every future logger field is implementation-ready without reinterpretation;
- forbidden/redacted fields cannot leak raw broker/account/order/deal/position/result/cost data;
- owner approval gates and dependency graph keep live wiring closed;
- the saturation/self-red-team pass has tried to break the lane and pursued all same-evidence-class gaps it exposed;
- the instruction-coverage checklist proves no controlling-prompt requirement was skipped after compaction or resume;
- the next lane remains gated by explicit owner approval;
- `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false` are preserved.

If any same-evidence-class issue is discovered, pursue it inside this audit until cleared, proven impossible from approved routes, or converted into an exact repair blocker. Do not stop at vague "needs review" language.
