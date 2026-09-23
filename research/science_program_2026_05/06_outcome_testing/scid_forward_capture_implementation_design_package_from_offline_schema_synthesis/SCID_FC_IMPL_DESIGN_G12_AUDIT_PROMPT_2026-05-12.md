# G12 Audit Prompt - SCID Forward Capture Implementation Design Package

Date: 2026-05-12
Owner lane: independent G12 audit of the SCID forward-capture implementation design package
Evidence class: `G12_SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE_AUDIT_ONLY`
Target route: `research/science_program_2026_05/06_outcome_testing/scid_forward_capture_implementation_design_package_from_offline_schema_synthesis/`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Objective

Audit the route-local design package to the highest practical source/control standard. The goal is not to be conservative for its own sake and not to invent reasons to break the package. The goal is to prove, from disk, whether the design is complete, source-bound, implementation-ready, and safely owner-gated. Accept it if the evidence supports acceptance; repair or reduce exact issues inside this G12 evidence class when possible; block only on concrete recomputation, manifest, hash, no-leak, scoped-diff, missing-artifact, or verifier/test failures.

This is not a promotion or edge-selection audit. Do not reject or weaken the package because it does not prove performance, does not produce an OB-only conclusion, or proposes future capture routes beyond current GTOS edge framing. Absence of validation/R/PnL/win-rate/expectancy is required in this lane, not a defect. Accept source/control design evidence if it is complete, scoped, auditable, owner-gated, no-leak, and safe inside this evidence class.

Do not open validation, result scoring, strategy-edge review, R/PnL/win-rate/expectancy/performance, AI/API, paid/vendor access, broker account/order/history/deal/position evidence, raw market-data blob commits, live restart, live behavior, registry edits, remote push, or prompt/config/risk/safety/execution/canary/selector changes.

## Mandatory Preflight

1. Run `python scripts/generate_live_state.py`.
2. Read `.context/LIVE_STATE.md`.
3. Read `.context/00_core/quick_reference_card.md`.
4. Read `.context/00_core/research_operating_doctrine.md`.
5. Read `.context/00_core/goal_session_research_discipline.md`.
6. Read `.context/00_core/research_current_state.md`.
7. Read this prompt from disk.
8. Read every target-route artifact from disk, not from chat output. Also read the accepted offline schema package, its G12 audit, the G0 offline-schema synthesis, the combined source-capture G12 audit, and the combined source-capture G0 synthesis artifacts cited by the target manifest.

## Audit Posture

- Be evidence-bound and fair. Do not create hypothetical blockers, vague warnings, or style objections.
- Do not stop at the first issue if the issue can be resolved by rereading, recomputing, rebuilding target-route audit outputs, stabilizing the verifier result, or refreshing context inside this G12 route.
- A terminal blocker must name the exact file, field, row, source hash, scoped-diff path, missing artifact, failing check, or evidence-class boundary that prevents acceptance.
- Known unrelated live/runtime dirt or untracked sibling helper drafts must be ledged as unrelated unless they touch the target route, live behavior, raw blobs, or forbidden surfaces.
- If the target package is acceptable with repair already performed inside this G12 lane, emit an `ACCEPT_AS_G12_SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE_CONTROL_EVIDENCE_ONLY` decision and list the repair evidence.

## Required Audit Checks

1. Reconcile the target package against the accepted G12 offline-schema audit and G0 synthesis route bundle.
2. Confirm the candidate boundary remains exactly `3,014` source candidates and is coverage/control evidence only.
3. Confirm exactly the ten accepted capture groups are mapped: `baseline_control_fields`, `framework_setup_family`, `future_orderflow_depth_proxy_requirements`, `intended_entry_reference`, `intended_side_direction`, `intended_stop_reference`, `intended_target_reference`, `lifecycle_fill_cancel_expiry_source_status`, `lower_timeframe_asof_path_availability`, `poi_type_bounds_source`.
4. For every group, verify source/as-of/no-leak/redaction/fail-closed/duplicate/rollback/test/G12 acceptance criteria.
5. Verify every future runtime code change is represented as a proposed patch artifact, insertion-point ledger row, rollback gate, test plan, and explicit owner-approval gate.
6. Verify no production `src/`, `config/`, `prompts/`, risk, execution, canary, selector, live restart, broker/API, paid/vendor, raw-blob, validation, result-scoring, or live-behavior change was made by the route.
7. Verify lifecycle, LTF, and orderflow groups preserve fail-closed unavailable behavior and block broker/result/raw-blob leakage.
8. Recompute route manifest hashes, parser/verifier hashes, completion audit fields, closeout verification, scoped dirty-state ledger, and safe flags.
9. Run the target verifier and focused tests. If pycache/temp friction blocks bytecode compilation, perform and record an AST syntax fallback for every audited Python file.
10. Emit a G12 decision ledger, source/hash audit, scoped-diff/no-leak audit, completion audit, verifier result, focused tests, and hardened next-route prompt if accepted or exact repair prompt if blocked.

## Completion Standard

Mark complete only after all required artifacts are committed and the final verifier reports `ok=true` or the terminal repair blocker ledger proves exactly why acceptance is impossible inside this evidence class. Terminal decision must be exactly one of:

- `ACCEPT_AS_G12_SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE_CONTROL_EVIDENCE_ONLY`
- `REPAIR_SCID_FORWARD_CAPTURE_IMPLEMENTATION_DESIGN_PACKAGE_BEFORE_USE`

Preserve `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false` throughout.

## One-Line Starter

`/goal Follow the full controlling prompt in research/science_program_2026_05/06_outcome_testing/scid_forward_capture_implementation_design_package_from_offline_schema_synthesis/SCID_FC_IMPL_DESIGN_G12_AUDIT_PROMPT_2026-05-12.md as the complete objective; do mandatory preflight/context refresh first and do not rely on chat memory; independently audit the target SCID implementation-design package from disk against accepted G12/G0 offline-schema and source-capture artifacts, recompute the 3,014 candidate boundary, ten capture groups, proposed patch gates, manifest/hash/no-leak/scoped-diff/dirty-state evidence, verifier/tests, and owner-gated rollback plan; be evidence-bound and fair, do not invent hypothetical blockers, do not collapse to OB-only, treat auditable new doors as valid next-route evidence, repair/recompute inside this G12 lane when possible, and block only on exact file/field/hash/source/verifier/evidence-class failures; preserve NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false and open no validation/result/strategy-edge/R/PnL/win-rate/expectancy/live/AI/API/paid/broker/raw-blob/prompt-config-risk-safety-execution-canary-selector surface; commit artifacts and mark complete only when the prompt completion standard is fully satisfied.`
