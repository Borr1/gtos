# G12 NOFILL Historical Sealed-Validation Partition Source-Binding Audit Goal Prompt

Date: 2026-05-10
Owner lane: independent G12 source/control audit
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Goal

Run an independent G12 audit of `NOFILL_HISTORICAL_SEALED_VALIDATION_PARTITION_AND_SOURCE_BINDING`.

The target route is:

- `research/science_program_2026_05/06_outcome_testing/nofill_historical_sealed_validation_partition_and_source_binding/`

The audit must decide whether the target route can be accepted as source/control historical partition and 55-field source-binding evidence only. It must not open validation execution, result/cost scoring, promotion, registry edits, paid/API routes, remote push, live restart, live trading behavior, broker actual-R reads, or MT5 order/account/history behavior.

Expected terminal decisions:

- `ACCEPT_AS_SOURCE_CONTROL_HISTORICAL_PARTITION_AND_FIELD_BINDING_EVIDENCE_ONLY`
- `ACCEPT_WITH_EXACT_REPAIR_OR_SOURCE_BLOCKERS`
- `REJECT_INVALID_PARTITION_OR_FIELD_BINDING`

Acceptance does not create validation-safe data. It only accepts the partition/source-binding control evidence and the fact that current committed CAT V3 NOFILL rows have zero sealed-validation rows.

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

Target partition/source-binding route:

- `NOFILL_HISTORICAL_SEALED_VALIDATION_DECISION_LEDGER_2026-05-10.json`
- `NOFILL_HISTORICAL_SEALED_VALIDATION_PARTITION_LEDGER_2026-05-10.json`
- `NOFILL_HISTORICAL_SEALED_VALIDATION_PARTITION_ROW_LEDGER_2026-05-10.jsonl`
- `NOFILL_HISTORICAL_SEALED_VALIDATION_CONTAMINATION_PROOF_LEDGER_2026-05-10.json`
- `NOFILL_HISTORICAL_SEALED_VALIDATION_55_FIELD_SOURCE_BINDING_MATRIX_2026-05-10.json`
- `NOFILL_HISTORICAL_SEALED_VALIDATION_FIELD_BLOCKERS_OWNER_REQUIREMENTS_LEDGER_2026-05-10.json`
- `NOFILL_HISTORICAL_SEALED_VALIDATION_DUPLICATE_DENOMINATOR_PURGE_EMBARGO_POLICY_2026-05-10.json`
- `NOFILL_HISTORICAL_SEALED_VALIDATION_SYMBOL_SESSION_REGIME_SPLIT_READINESS_LEDGER_2026-05-10.json`
- `NOFILL_HISTORICAL_SEALED_VALIDATION_LOCAL_HEAVY_DATA_PRIOR_ARTIFACT_SEARCH_LEDGER_2026-05-10.json`
- `NOFILL_HISTORICAL_SEALED_VALIDATION_FUTURE_VALIDATION_EXECUTION_PREREQUISITES_2026-05-10.json`
- `NOFILL_HISTORICAL_SEALED_VALIDATION_COMPLETION_AUDIT_2026-05-10.json`
- route builder, verifier, focused tests, and output manifest

Upstream evidence chain:

- `g0_nofill_forward_source_capture_implementation_synthesis_readiness_route/`
- `g12_nofill_forward_source_capture_additive_logger_implementation_audit/`
- `nofill_forward_source_capture_additive_logger_implementation/`
- `g12_nofill_forward_projection_repair_reaudit/`
- `nofill_cat_v3_source_control_rebuild/`
- `g12_nofill_cat_v3_source_control_audit/`
- `g12_nofill_cat_v3_quarantined_categorical_count_packet_audit/`
- `g0_nofill_cat_v3_categorical_evidence_synthesis_control_review/`
- `research/science_program_2026_05/05_synthesis/HISTORICAL_SEALED_VALIDATION_PROTOCOL_PLAN_2026-05-09.md`

## Hardening Standard

Operate at maximum practical reasoning depth. Enforce curiosity, truthfulness, and active creativity, but keep this audit in the G12 source/control acceptance evidence class.

Do not rubber-stamp the target route. Try to break the partitioning and source-binding:

- independently recompute CAT V3 universe totals and row-family counts;
- independently recompute that committed sealed-validation NOFILL row count is `0`;
- verify every committed CAT V3 NOFILL row is classified and contamination reasons are defensible;
- verify the route does not launder discovery/development/result/forensics/G12/G0 rows into sealed validation;
- independently recompute the 55-field source-binding matrix class counts;
- verify the 20 future-logger/source-extraction requirements are exact and not vague;
- verify the 7 forbidden/redacted fields remain status-only and no raw broker/account/order/deal/position/ticket/result/cost/slippage/execution-quality route is opened;
- verify duplicate/purge/embargo and symbol/session/regime ledgers are sufficient for a future validation prompt to build from, even if they do not execute validation now;
- verify local-heavy-data and prior-artifact search evidence is adequate before accepting zero sealed rows and field blockers;
- rerun or independently verify the target route verifier and focused tests;
- inspect committed diff scope and confirm no forbidden live or validation surfaces changed.

Examples and listed artifacts are starting points, not boundaries. If another local artifact, prior worktree, source contract, test, source/log/code path, cached doc, or local-heavy-data root could materially change the audit answer, inspect it or exactly rule it out.

Split only if the next step crosses into validation execution, result/cost scoring, promotion, registry edits, paid/API/live trading behavior, remote push, credentials, or forbidden broker/account/order evidence. Inside this G12 source/control audit, pursue blockers until cleared, proven impossible from approved inputs, or reduced to an exact repair/source/capture requirement.

## Required Audit Questions

1. Does the target route prove the CAT V3 universe equation `298 = 225 accepted + 4 source_control + 4 source_impossible + 65 reject`?
2. Is `0` committed sealed-validation NOFILL rows correct, or did the route miss any source-safe untouched rows?
3. Are all 298 committed rows classified with exact contamination or partition reasons?
4. Does the 55-field binding matrix close every field into source-bound, future-logger/source-extraction-required, schema-only, or forbidden/redacted status-only classes?
5. Are all field blockers exact enough for a future source-binding/extraction route?
6. Do duplicate, purge, embargo, symbol, session, and regime controls prevent future effective-N inflation?
7. Does the route correctly separate historical sealed validation from forward shadow realism and contaminated discovery/development data?
8. Are local-heavy-data/prior-worktree search claims adequate and reproducible?
9. What exact repair blockers, if any, must be closed before the route can be accepted as control evidence?
10. What exact next route is allowed after G12 acceptance, and what remains forbidden?

## Required Saturation And Self-Red-Team Pass

Before completion, write a lane-specific saturation pass that tries to reject the target route and pursues any same-evidence-class gap it exposes.

The saturation pass must answer and act on:

1. What exact mistake would let a contaminated CAT V3 row become a future sealed-validation row?
2. What exact duplicate or row-family mistake would inflate effective N?
3. What exact field-binding mistake would allow future/post-outcome or forbidden broker data into inputs?
4. What exact local-heavy-data root or prior worktree could contradict the zero sealed-row conclusion?
5. What exact search or manifest gap would make the 20 future field requirements too vague?
6. What would a skeptical G12/G0 reviewer reject in the target route?
7. If a future validation-execution lane starts from this audit, what exact prerequisites must it enforce?
8. What is deliberately not answered here, and which future lane owns it?

If any answer exposes an allowed same-evidence-class gap, pursue it inside this audit until it is resolved, proven impossible, or converted into an exact repair/source/capture requirement.

## Required Outputs

Create:

`research/science_program_2026_05/06_outcome_testing/g12_nofill_historical_sealed_validation_partition_source_binding_audit/`

At minimum produce:

- context anchor
- G12 decision ledger
- CAT V3 universe and zero-sealed-row recomputation audit
- contamination proof reaudit
- 55-field source-binding matrix reaudit
- field blocker exactness audit
- duplicate/purge/embargo and symbol/session/regime audit
- local-heavy-data/prior-artifact search reaudit
- validation-boundary and forbidden-route audit
- target verifier/test rerun report
- saturation/self-red-team pass
- instruction-coverage checklist
- exact repair/source blocker ledger, even if empty
- next prompt pack with one-line starter
- completion audit
- G12 audit builder, verifier, and focused tests

Update `.context/00_core/research_current_state.md` after the audit commit.

## Verification Required

- Parse all generated JSON/JSONL/Markdown control artifacts.
- Parse target route JSON and JSONL artifacts.
- Rerun target route verifier and focused tests.
- Run new G12 verifier and focused tests.
- Run `python -B -m py_compile` or AST syntax fallback if Windows blocks bytecode writes.
- Recompute CAT V3 totals and zero sealed-row conclusion from target ledgers, not Markdown prose.
- Recompute the 55-field source-binding counts from the target matrix.
- Scan changed/generated artifacts for unresolved placeholders including `TBD`, `TODO`, `unknown`, `maybe`, `later`, and `not yet decided`.
- Confirm no generated artifact sets `validation_safe`, `outcome_review_opened`, or `live_effect` to true.
- Confirm no validation execution, result/cost scoring, promotion, registry edit, paid/API route, remote push, live restart, prompt/config/risk/execution/permissions/safety/selector/canary/MT5 order-account-history behavior, credential, or live trading behavior opened.
- Regenerate `LIVE_STATE.md` at closeout and ensure research context is fresh or explain generated snapshot dirt.

## Completion Standard

The goal is complete only when G12 has an explicit terminal decision, every required artifact exists, machine-checkable verification passes, and any blocker is exact enough for a repair/source-binding route.

Acceptance is allowed only if:

- CAT V3 universe totals reconcile;
- committed sealed-validation NOFILL row count is independently confirmed as `0`;
- contamination controls are complete for current committed rows;
- all 55 fields are classified and the 20 future requirements are exact;
- duplicate/purge/embargo and split controls are sufficient for a future validation prompt;
- local-heavy-data/prior-artifact search claims are audited;
- saturation/self-red-team pass is complete;
- instruction-coverage checklist is complete;
- `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false` are preserved.

If accepted, the target route remains source/control partition and field-binding evidence only. It does not authorize validation execution, result/cost scoring, promotion, registry edits, paid/API routes, remote push, live restart, or live trading behavior.
