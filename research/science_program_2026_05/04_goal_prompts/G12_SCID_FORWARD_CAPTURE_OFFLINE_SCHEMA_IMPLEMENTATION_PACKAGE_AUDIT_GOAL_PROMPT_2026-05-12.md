# G12 SCID Forward Capture Offline Schema Implementation Package Audit Goal Prompt

Date: 2026-05-12
Owner lane: independent G12 audit of SCID forward capture offline schema package
Evidence class: `G12_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_AUDIT_ONLY`
Input route: `research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package/`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Objective

Independently audit the SCID forward capture offline schema implementation package. Decide whether the package can be accepted as source/control evidence only for future capture implementation planning. Do not open validation, result scoring, strategy-edge claims, R/PnL/win-rate/expectancy/performance, AI/API, paid/vendor access, broker account/order/history/deal/position evidence, raw market-data blob commits, live behavior, or prompt/config/risk/safety/execution/canary/selector changes.

## Fair Audit Posture

This is an independent G12 audit, not a second builder, not a promotion review, and not conservative theater. Be adversarial about artifact truth, but do not create blockers because the package is offline-only or because live logger wiring is absent. Offline-only status and absent live wiring are required boundaries for this evidence class.

Accept if the package is complete, deterministic, fixture-tested, no-leak, redaction-safe, manifest-bound, read-only aligned, and auditable as future capture implementation planning evidence. Do not require production integration, live process changes, broker/account/order evidence, or strategy-result computation in this audit.

Repair or reject only for concrete artifact failures, such as missing capture groups, missing schema fields, incomplete type/nullability/as-of/source/hash/redaction/forbidden/fail-closed rules, fixture pass/fail mismatch, weak manifest-repair policy, read-only alignment not evidenced, row/denominator drift, forbidden-surface opening, raw blob leakage, no-leak failure, source/hash binding failure, or verifier/test failure.

## Mandatory Preflight

1. Run `python scripts/generate_live_state.py`.
2. Read `.context/LIVE_STATE.md`.
3. Read `.context/00_core/quick_reference_card.md`.
4. Read `.context/00_core/research_operating_doctrine.md`.
5. Read `.context/00_core/goal_session_research_discipline.md`.
6. Read `.context/00_core/research_current_state.md`.
7. Read this prompt from disk.
8. Read every JSON/MD/schema/fixture/verifier/test artifact in the input route directory.
9. Read the accepted G12/G0 combined source-capture artifacts cited by the input route manifest.

## Required Audit Checks

- Recompute that the package preserves the 3,014 `candidate_input_row_id` and 3,014 `duplicate_proxy_denominator_key` coverage expectations from the accepted G12 audit.
- Verify all accepted capture groups are present unchanged: side, entry, stop, target, POI, framework, lifecycle, LTF, orderflow/proxy, and baseline-control.
- Verify every group has explicit type, nullability, as-of timestamp semantics, source identifier, source hash or hash-deferral policy, redaction policy, forbidden-value policy, fail-closed missing status, and downstream G12 acceptance rule.
- Run or independently reimplement the fixture validator and confirm valid fixtures pass while missing-field, forbidden broker identifier, stale/as-of, and duplicate-mismatch fixtures fail closed.
- Verify the LTF unavailable and orderflow/proxy unavailable fixtures are accepted only as fail-closed unavailable rows.
- Verify read-only monitoring alignment inspected current artifact shapes without modifying producers or running processes.
- Verify manifest-binding repair continuity: current G12 prompt hash is rebound, builder output manifest self-hash is non-blocking, and every other source/input hash mismatch remains strict.
- Verify no forbidden surfaces were opened in the route diff or generated artifacts.
- Verify live wiring absence is treated as a required route boundary, not as a blocker.
- Verify any builder-emitted next prompts are handoff scaffolds only, not self-acceptance or promotion evidence.

## Completion Standard

1. Context/preflight use recorded.
2. Schema, fixture, validator, read-only alignment, manifest-repair, and no-leak checks independently recomputed.
3. Any repair or rejection is tied to concrete artifact evidence, not discomfort with offline-only status or absent live wiring.
4. Verifier and focused tests pass or concrete repair blockers are written.
5. Terminal decision is exactly one of:
   - `ACCEPT_AS_G12_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_CONTROL_EVIDENCE_ONLY`
   - `REPAIR_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_BEFORE_USE`
6. If accepted, emit the next G0 synthesis/control prompt; if not accepted, emit an exact repair prompt.
7. Safe flags remain `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.

## One-Line Starter

`/goal Follow the full controlling prompt in research/science_program_2026_05/04_goal_prompts/G12_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_AUDIT_GOAL_PROMPT_2026-05-12.md as the complete objective; do mandatory preflight and context refresh first; do not rely on chat memory; stay G12_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_AUDIT_ONLY with no validation/result-scoring/strategy-edge/R/PnL/win-rate/expectancy/performance/promotion/live behavior/AI/API/paid-vendor/broker-account-order-history-deal-position/raw-market-blob/prompt-config-risk-safety-execution-canary-selector changes; independently audit all offline schemas, parser/redaction/as-of/no-leak/fail-closed validators, synthetic fixtures, fixture validation ledgers, manifest-repair hash policy, read-only monitoring alignment, output manifest, verifier and focused tests; be adversarial but fair, so do not reject because live wiring is absent because offline-only is required here; reject or repair only concrete schema/fixture/validator/hash/alignment/no-leak/surface/verifier failures; preserve NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false; emit decision ledgers, completion audit, next G0 synthesis/control prompt or exact repair prompt, scoped commits, closeout verification; mark complete only when the prompt file's completion standard is fully satisfied.`
