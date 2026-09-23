# NOFILL Historical Sealed Validation Partition And Source Binding Goal Prompt

Date: 2026-05-10
Owner lane: source/control historical sealed-validation partitioning and field-binding
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Goal

Build the NOFILL historical sealed-validation partition ledger and source-field binding plan before any future NOFILL validation or result execution.

This route must define, from committed artifacts and local source/control evidence, which historical rows/windows/symbols/sessions/regimes are discovery, development, sealed-validation, stress/robustness, forward-shadow, or contaminated. It must bind the accepted NOFILL forward source-capture fields to source-safe historical equivalents where possible, and it must identify exact blockers for fields or slices that cannot be source-bound without new capture/extraction.

This is a source/control partitioning route only. It must not run result/cost scoring, validation execution, promotion, registry edits, paid/API calls, remote push, live restarts, prompt/config/risk/permissions/safety/selector/canary/MT5 order-account-history changes, broker actual-R reads, or live trading behavior changes.

Expected terminal decisions:

- `ACCEPT_AS_SOURCE_CONTROL_HISTORICAL_SEALED_PARTITION_AND_FIELD_BINDING_EVIDENCE`
- `ACCEPT_WITH_EXACT_SOURCE_FIELD_OR_PARTITION_BLOCKERS`
- `BLOCKED_WITH_EXACT_OWNER_ACCESS_SOURCE_CAPTURE_REQUIREMENT`
- `REJECT_INVALID_PARTITION_OR_CONTAMINATION_CONTROL`

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

Current G0 readiness route:

- `research/science_program_2026_05/06_outcome_testing/g0_nofill_forward_source_capture_implementation_synthesis_readiness_route/`
- `G0_NOFILL_FORWARD_SOURCE_CAPTURE_IMPLEMENTATION_SYNTHESIS_DECISION_LEDGER_2026-05-10.json`
- `G0_NOFILL_FORWARD_SOURCE_CAPTURE_SHADOW_READINESS_OBSERVATION_AUDIT_2026-05-10.json`
- `G0_NOFILL_FORWARD_SOURCE_CAPTURE_FUTURE_MONITOR_VERIFIER_SPEC_2026-05-10.json`
- `G0_NOFILL_FORWARD_SOURCE_CAPTURE_HISTORICAL_SEALED_VALIDATION_PARALLEL_ROUTE_NOTE_2026-05-10.json`
- `G0_NOFILL_FORWARD_SOURCE_CAPTURE_COMPLETION_AUDIT_2026-05-10.json`

Accepted implementation and source-control chain:

- `g12_nofill_forward_source_capture_additive_logger_implementation_audit/`
- `nofill_forward_source_capture_additive_logger_implementation/`
- `g12_nofill_forward_source_capture_implementation_design_audit/`
- `nofill_forward_source_capture_implementation_design_plan/`
- `g12_nofill_forward_projection_repair_reaudit/`
- `nofill_forward_source_safe_projection_builder/`
- `nofill_cat_v3_source_control_rebuild/`
- `g12_nofill_cat_v3_source_control_audit/`
- `nofill_cat_v3_quarantined_categorical_count_packet/`
- `g12_nofill_cat_v3_quarantined_categorical_count_packet_audit/`
- `g0_nofill_cat_v3_categorical_evidence_synthesis_control_review/`

Historical validation methodology:

- `research/science_program_2026_05/05_synthesis/HISTORICAL_SEALED_VALIDATION_PROTOCOL_PLAN_2026-05-09.md`
- `.context/00_core/research_operating_doctrine.md`
- `.context/00_core/goal_session_research_discipline.md`

Local source/log/data roots to search read-only where relevant:

- `shadow_logs/`
- `data/`
- `research/science_program_2026_05/`
- prior committed route artifacts and manifests
- absolute local-heavy roots named in `.context/00_core/local_heavy_data_inventory.md`

## Hardening Standard

Operate at maximum practical reasoning depth. Enforce curiosity, truthfulness, and active creativity, but keep this route in source/control partitioning and field-binding only.

Do not produce a generic validation plan. Build a concrete, machine-checkable partition ledger and field-binding ledger. Same-evidence-class continuation is mandatory: if a slice, field, source, or contamination status is unclear, search committed artifacts, source manifests, local logs, local heavy-data roots, and prior route outputs until it is classified, proven impossible from approved inputs, or reduced to an exact owner/access/source/capture requirement.

Examples and listed artifacts are starting points, not boundaries. Check whether the route is boxed by the current worktree, latest G0 summary, current timeframe, current symbol, current data modality, current logger, or first NOFILL framing. Search beyond the obvious NOFILL files if another GTOS artifact can identify discovery contamination, development leakage, source fields, duplicate keys, or sealed candidates.

Use the hostile edge-review lens: assume an apparent future edge could be fake because of contamination, duplicate denominators, post-outcome fields, cost/slippage blind spots, session artifacts, one-regime concentration, hidden selection, or stale context. The purpose is to prevent fake validation before any future scoring starts.

Split only if the next step crosses into result/cost scoring, validation execution, promotion, registry edits, paid/API/live trading behavior, remote push, credentials, or forbidden broker/account/order evidence. Inside source/control partitioning, pursue blockers until cleared, proven impossible from approved inputs, or reduced to an exact owner/access/source/capture approval requirement.

## Required Questions

1. What exact NOFILL rows, duplicate keys, duplicate groups, symbols, sessions, dates, and regimes have already been used for discovery, development, source repair, packet building, result counting, forensics, or G12/G0 synthesis?
2. Which rows/slices are contaminated for future validation because outcomes/path labels/source repair decisions were already inspected?
3. Which rows/slices can remain sealed historical validation candidates, and what proof shows their outcomes were not used for rule selection?
4. Which rows/slices belong to stress/robustness rather than sealed validation?
5. Which rows/slices belong to forward-shadow realism rather than historical validation?
6. Which of the accepted 55 NOFILL forward source-capture fields can be bound to historical source-safe fields, and which cannot?
7. Which fields require current/future logger evidence rather than historical reconstruction?
8. What duplicate policy, purging/embargo rule, symbol/session/regime split, and contamination rule must be frozen before a future validation execution lane?
9. What exact local roots and prior artifacts were searched before declaring any sealed-slice or field-binding blocker?
10. What exact next goal should run after this partitioning route?

## Required Saturation And Self-Red-Team Pass

Before completion, write a lane-specific saturation pass that tries to reject the partitioning and field-binding route and then pursues any same-evidence-class gap it exposes.

The saturation pass must answer and act on these questions:

1. What exact contamination mistake would let discovery/development rows become validation rows?
2. What exact duplicate-key or duplicate-group mistake would inflate effective N?
3. What exact field-binding mistake would let post-outcome, hidden path-label, broker actual-R, cost/slippage, ticket/order, or future-context data leak into a source-control field?
4. What exact historical slice looks sealed but is actually touched by prior packet/result/forensics/G12/G0 artifacts?
5. What exact source/log/data root could materially change the partition answer, and was it searched?
6. What exact small-N or missing-field issue requires expansion rather than passive waiting?
7. What would a skeptical G12/G0 reviewer reject before allowing a future validation execution route?
8. What is deliberately not answered here, and what exact future lane owns it?

If any answer exposes an allowed same-evidence-class gap, pursue it inside this route until resolved, proven impossible, or converted into an exact owner/access/source/capture requirement.

## Required Outputs

Create:

`research/science_program_2026_05/06_outcome_testing/nofill_historical_sealed_validation_partition_and_source_binding/`

At minimum produce:

- context anchor
- decision ledger
- historical universe/source inventory
- discovery/development/sealed-validation/stress/forward/contaminated partition ledger
- contamination proof ledger
- 55-field source-binding matrix for accepted NOFILL forward source-capture fields
- field blockers and owner/access/source/capture requirements ledger
- duplicate/denominator and purging/embargo policy draft
- symbol/session/regime split readiness ledger
- local-heavy-data and prior-artifact search ledger
- forbidden route ledger
- future validation execution prerequisites
- next prompt pack with one-line starter
- saturation/self-red-team pass
- instruction-coverage checklist
- completion audit
- builder, verifier, and focused tests where useful

Update `.context/00_core/research_current_state.md` after the route commit.

## Verification Required

- Parse all generated JSON/JSONL/Markdown control artifacts.
- Verify partition totals reconcile against the accepted NOFILL CAT V3 universe and any declared expansion inventory.
- Verify every field in the 55-field source-capture contract is either source-bound, future-logger-bound, schema-only, forbidden/redacted status-only, or exact-blocked.
- Verify no generated artifact sets `validation_safe`, `outcome_review_opened`, or `live_effect` to true.
- Verify no result/cost scoring, validation execution, promotion, registry edit, paid/API route, remote push, live restart, or live trading behavior is opened.
- Run route verifier and focused tests.
- Run `python -B -m py_compile` or AST syntax fallback if Windows blocks bytecode writes.
- Regenerate `LIVE_STATE.md` at closeout and ensure research context is fresh or explain generated snapshot dirt.

## Completion Standard

The goal is complete only when the route has an explicit terminal decision, every required artifact exists, machine-checkable verification passes, and every partition/field blocker is exact.

Acceptance is allowed only if:

- discovery/development/sealed-validation/stress/forward/contaminated partitions are explicitly defined;
- contamination controls and local search evidence are recorded;
- the 55-field source-binding matrix is complete;
- duplicate/purge/embargo and symbol/session/regime readiness rules are frozen enough for a future validation execution prompt;
- exact blockers or owner/source/capture requirements are recorded;
- saturation/self-red-team pass is complete;
- instruction coverage is complete;
- `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false` are preserved.

If accepted, the route remains source/control partitioning evidence only. It does not authorize validation execution, result/cost scoring, promotion, registry edits, paid/API routes, remote push, live restart, or live trading behavior.
