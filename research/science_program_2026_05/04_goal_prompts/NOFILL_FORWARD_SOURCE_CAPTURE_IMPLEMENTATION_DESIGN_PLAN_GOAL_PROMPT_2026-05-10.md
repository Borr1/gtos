# NOFILL Forward Source-Capture Implementation Design Plan Goal Prompt

Date: 2026-05-10
Owner lane: source/control implementation-design plan
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Goal

Build a source/control-only implementation design plan for future NOFILL forward lifecycle source capture, using the now G12-accepted source-capture contract evidence.

This lane may rely on the accepted source/control contract after:

- `d2bd8cac research: text-gate nofill source capture hash fallback`
- `56177c4f research: add g12 source capture text-gate reaudit`
- terminal G12 verdict `ACCEPT_AS_SOURCE_CONTROL_CONTRACT_EVIDENCE_ONLY_AFTER_TEXT_GATE_REPAIR`

The output must define exactly how a future owner-approved implementation lane should capture the accepted 55-field source contract in live/shadow logs without leaking account/order/deal/position/result labels, without opening scoring, and without changing live trading behavior now.

This is a plan/prototype/spec lane only. Do not edit `src/`, `prompts/`, `config/`, `run_agent.py`, `start_all.bat`, MT5 EA, risk/execution/permission/safety/selectors/canary/order behavior, credentials, registries, or remote state.

## Mandatory Preflight And Context

1. Run `python scripts\generate_live_state.py`.
2. Read `.context\LIVE_STATE.md`.
3. Read latest numbered `.context\02_session_handoffs\*`.
4. Read `.context\00_core\quick_reference_card.md`.
5. Read `.context\00_core\research_operating_doctrine.md`.
6. Read `.context\00_core\research_current_state.md`.
7. Read `.context\00_core\goal_session_research_discipline.md`.
8. Read `.context\00_core\local_heavy_data_inventory.md`.
9. Re-read this prompt and record exact HEAD and prompt path in the context anchor.

Do not rely on chat memory. If context compaction occurs, regenerate live state, reread this prompt, and continue from disk artifacts.

## Controlling Inputs

Primary accepted source/control contract:

- `research/science_program_2026_05/06_outcome_testing/nofill_forward_source_capture_contract_hardening_offline_projection_prototype/`
- `research/science_program_2026_05/06_outcome_testing/g12_nofill_forward_source_capture_text_gate_repair_reaudit/`

Upstream source/control chain:

- `g0_nofill_forward_projection_synthesis_control_route/`
- `g12_nofill_forward_projection_repair_reaudit/`
- `nofill_forward_source_safe_projection_builder/`
- `g12_nofill_forward_lifecycle_capture_contract_audit/`
- `nofill_cat_v3_source_control_rebuild/`

Existing source/log/code inventory to inspect read-only:

- `src/research_infra/forward_capture.py`
- `src/components/pending_limit_lifecycle_logger.py`
- `shadow_logs/pending_limit_lifecycle*.jsonl`
- `shadow_logs/candidate_path_follow.jsonl`
- `shadow_logs/candidate_ltf_path_order.jsonl`
- `shadow_logs/live_candidate_strategy_rollups.jsonl`
- relevant `pipeline_state/`, `knowledge_base/`, and local heavy data roots if needed

## Hardening Standard

Operate at maximum practical reasoning depth. Enforce curiosity, truthfulness, and active creativity.

Do not stop at a shallow implementation checklist. Pursue the full design to proof-or-impossibility within this plan-only evidence class:

- map every accepted contract field to a source, source status, or exact blocker;
- separate already-captured fields from missing fields and forbidden fields;
- define parser/projection contracts and fail-closed missing/status vocabulary;
- prove no raw account/order/deal/position/result/cost values are required or allowed;
- define tests, fixture cases, hash manifests, rollout gates, rollback gates, and G12 acceptance criteria for the future implementation lane;
- identify exact owner approvals required before code wiring.

Split only when crossing into actual live logger code changes, result/cost scoring, sealed validation, promotion, registry edits, paid/API/live trading behavior, or remote push.

Field closure is mandatory. Every one of the accepted 55 source-capture contract fields must receive exactly one terminal implementation-design status:

- `EXISTING_SOURCE_SAFE_CAPTURE_READY`
- `FUTURE_LOGGER_FIELD_REQUIRED`
- `SCHEMA_ONLY_CONTROL_FIELD`
- `FORBIDDEN_OR_REDACTED_SOURCE_ONLY`
- `BLOCKED_WITH_EXACT_OWNER_APPROVAL_OR_SOURCE_REQUIREMENT`

No field may remain as `TBD`, `unknown`, `maybe`, `later`, unstated, or generally deferred. If a blocker appears, pursue it to an exact terminal design answer inside this evidence class: already available source, required future logger field, schema-only control field, forbidden/redacted field, or exact owner/source approval requirement.

## Required Design Questions

1. Which of the 55 contract fields can be captured from existing source-safe logs/code without code changes?
2. Which fields require future logger additions, and where exactly should they be emitted?
3. Which raw fields are forbidden and must be redacted, omitted, replaced with status values, or hashed only as source-safe non-secret identifiers?
4. What exact schema should the future implementation emit?
5. What parser/projection/verifier/test fixtures are required before any future G12 acceptance?
6. What timing, latency, write-complete, and clock-skew fields must be captured to avoid future ambiguity?
7. What pending-order observability can be source-safe without exposing raw MT5 ticket/order/deal/account/history data?
8. What spread/slippage/execution-quality fields remain source-safe status fields, and what must stay closed until a separate result/cost lane?
9. What can go wrong operationally, and what fail-closed states prevent silent bad evidence?
10. What is the exact next implementation lane prompt after this plan, if and only if the plan passes G12 review and the owner approves code wiring?
11. What is the exact implementation dependency order from safest offline parser/spec work through any later owner-approved logger wiring?
12. Which verifier assertions prove that all 55 fields are closed, no placeholder statuses remain, and every future implementation requirement is testable without reinterpretation?

## Required Outputs

Create:

`research/science_program_2026_05/06_outcome_testing/nofill_forward_source_capture_implementation_design_plan/`

At minimum produce:

- context anchor
- source contract implementation map for all 55 fields
- 55-field terminal closure ledger with status counts summing to exactly 55
- existing source/code/log inventory
- future logger emission design
- forbidden-field/redaction policy
- fail-closed missing/status vocabulary
- parser/projection schema
- fixture/test matrix
- source hash manifest requirements
- operational risk and rollback ledger
- G12 acceptance checklist
- implementation dependency graph
- owner approval gate ledger
- exact next prompt pack
- completion audit
- builder, verifier, and focused tests

Update `.context/00_core/research_current_state.md` after the design commit.

## Verification Required

- Parse all generated JSON/JSONL.
- Run syntax checks without relying on writable `__pycache__` if Windows blocks bytecode writes.
- Run focused pytest with `-p no:cacheprovider` and a controlled existing `--basetemp`.
- Run the generated verifier.
- Scan generated outputs for unresolved placeholders including `TBD`, `TODO`, `unknown`, `maybe`, `later`, and `not yet decided`; any hit must be removed or justified as quoted historical input outside terminal decision fields.
- Confirm no `validation_safe=true`, no `outcome_review_opened=true`, no `live_effect=true`, no result/cost/live-wiring opening, and `NO_PROMOTION_VERDICT` is preserved.
- Check committed diff scope; no live trading prompts, `src` trading logic, config/risk/execution/permissions/safety/selectors/canary/order behavior, MT5 order/account/history/deal/position behavior, credentials, paid/API/Databento route, registry promotion, or remote push.
- Regenerate `LIVE_STATE.md` at closeout and ensure research context is fresh or explain generated snapshot dirt.

## Completion Standard

The goal is complete only when the future implementation design is specific enough that a later owner-approved code-wiring lane can implement it without reinterpreting the source/control contract. The plan must not itself open live wiring, scoring, validation, promotion, or trading behavior.

It is not complete unless the completion audit proves:

- 55/55 fields have terminal statuses from the allowed vocabulary.
- Status counts sum to 55 with zero duplicate or missing fields.
- Every `FUTURE_LOGGER_FIELD_REQUIRED` row names the target source surface, target schema field, redaction rule if applicable, fail-closed missing status, test fixture, rollback rule, and G12 acceptance check.
- Every `BLOCKED_WITH_EXACT_OWNER_APPROVAL_OR_SOURCE_REQUIREMENT` row names the exact approval or source route needed.
- The generated verifier fails on placeholder terminal statuses and passes on the committed artifacts.
- No forbidden live trading surface changed.
