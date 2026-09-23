# G12 Audit Goal Prompt - SCID Capture Runtime Harness Synthetic Only

You are auditing the route-local synthetic-only runtime harness for the accepted
SCID forward capture offline schema package.

This is a G12 control audit, not an edge-selection or promotion audit. Do not reject or weaken the harness because it does not prove performance, does not produce an OB-only conclusion, or opens non-OB future capture/test doors. Absence of validation/R/PnL/win-rate/expectancy is required in this lane. New doors are acceptable when they are auditable, source/control scoped, no-leak, and routed to exact next evidence classes.

## Mandatory Preflight

1. Run `python scripts/generate_live_state.py`.
2. Read `.context/LIVE_STATE.md`.
3. Read `.context/00_core/quick_reference_card.md`.
4. Read `.context/00_core/research_operating_doctrine.md`.
5. Read `.context/00_core/goal_session_research_discipline.md`.
6. Read `.context/00_core/research_current_state.md`.
7. Read this prompt from disk.
8. Read every route artifact listed below directly from disk.

## Required Reads
- `research/science_program_2026_05/06_outcome_testing/scid_capture_schema_to_runtime_test_harness_synthetic_only/SCID_CAPTURE_RUNTIME_HARNESS_SYNTHETIC_ONLY_CONTEXT_ANCHOR_AND_G12_RECONCILIATION_2026-05-12.md`
- `research/science_program_2026_05/06_outcome_testing/scid_capture_schema_to_runtime_test_harness_synthetic_only/SCID_CAPTURE_RUNTIME_HARNESS_SYNTHETIC_ONLY_FIXTURE_MANIFEST_2026-05-12.json`
- `research/science_program_2026_05/06_outcome_testing/scid_capture_schema_to_runtime_test_harness_synthetic_only/SCID_CAPTURE_RUNTIME_HARNESS_SYNTHETIC_ONLY_NEGATIVE_FIXTURE_MATRIX_2026-05-12.json`
- `research/science_program_2026_05/06_outcome_testing/scid_capture_schema_to_runtime_test_harness_synthetic_only/SCID_CAPTURE_RUNTIME_HARNESS_SYNTHETIC_ONLY_LEAK_REDACTION_AUDIT_2026-05-12.json`
- `research/science_program_2026_05/06_outcome_testing/scid_capture_schema_to_runtime_test_harness_synthetic_only/SCID_CAPTURE_RUNTIME_HARNESS_SYNTHETIC_ONLY_SATURATION_SELF_REDTEAM_LEDGER_2026-05-12.json`
- `research/science_program_2026_05/06_outcome_testing/scid_capture_schema_to_runtime_test_harness_synthetic_only/runtime_harness_synthetic_only_2026_05_12.py`
- `research/science_program_2026_05/06_outcome_testing/scid_capture_schema_to_runtime_test_harness_synthetic_only/verify_scid_capture_runtime_harness_synthetic_only_2026_05_12.py`

## Audit Scope
0. Be evidence-bound and fair: do not invent hypothetical blockers, vague warnings, or style objections. If an issue can be resolved inside this G12 lane by rereading, recomputing, refreshing context, rebuilding audit outputs, or stabilizing the verifier result, do that before declaring repair-blocked. Block only on exact file/field/hash/source/no-leak/scoped-diff/verifier/test/evidence-class failures.
1. Confirm the harness consumes only synthetic fixtures plus committed accepted schema/control artifacts.
2. Recompute the ten-group positive and fail-closed fixture matrix.
3. Recompute negative routes for missing, stale as-of, forbidden identifier, duplicate denominator drift, unavailable-source, unsafe flag, manifest-repair, schema-version, unexpected-field, and enum violations.
4. Confirm LTF/orderflow unavailable-source cases are accepted only as source-unavailable fail-closed rows and that the eight historical source-truth groups fail closed.
5. Confirm recursive redaction catches broker/account/order/deal/position/result/performance markers in deliberate negative fixtures and that accepted rows are clean.
6. Confirm no `src/`, `prompts/`, broker/API, raw market blob, result scoring, strategy edge, validation, risk, safety, execution, canary, selector, or live behavior surface is opened.
7. Preserve the G12 manifest-binding repair policy exactly: current G12 prompt hash repair and output-manifest self-hash drift are nonblocking; all other source/input hashes are strict blockers.

## Completion Standard

Emit a decision ledger, recomputation audit, no-leak audit, verifier result, focused-test result, completion audit, and either acceptance or exact repair blockers. Do not stop early because the work is large. Known unrelated live/runtime dirt must be recorded as scoped/unscoped and cannot become a blocker unless it touches the target route or forbidden surfaces. Terminal decision must be exactly one of:

- `ACCEPT_AS_G12_SCID_CAPTURE_SCHEMA_TO_RUNTIME_TEST_HARNESS_SYNTHETIC_ONLY_CONTROL_EVIDENCE_ONLY`
- `REPAIR_SCID_CAPTURE_SCHEMA_TO_RUNTIME_TEST_HARNESS_SYNTHETIC_ONLY_BEFORE_USE`

Preserve `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.

## One-Line Starter
`/goal Follow the full controlling prompt in research/science_program_2026_05/04_goal_prompts/G12_SCID_CAPTURE_SCHEMA_TO_RUNTIME_TEST_HARNESS_SYNTHETIC_ONLY_AUDIT_GOAL_PROMPT_2026-05-12.md as the complete objective; do mandatory preflight/context refresh first and do not rely on chat memory; independently audit the synthetic-only SCID capture runtime harness from disk, recompute the ten-group fixture matrix, 109 fixture cases, positive/fail-closed/negative routes, recursive redaction/no-leak checks, manifest-binding policy, verifier/tests, and scoped dirty-state evidence; be evidence-bound and fair, do not invent hypothetical blockers, do not collapse to OB-only, treat auditable new doors as valid next-route evidence, repair/recompute inside this G12 lane when possible, and block only on exact file/field/hash/source/no-leak/scoped-diff/verifier/test/evidence-class failures; preserve NO_PROMOTION_VERDICT validation_safe=false outcome_review_opened=false live_effect=false and open no validation/result/strategy-edge/R/PnL/win-rate/expectancy/live/AI/API/paid/broker/raw-blob/prompt-config-risk-safety-execution-canary-selector surface; commit artifacts and mark complete only when the prompt completion standard is fully satisfied.`
