# SCID Capture Schema To Runtime Test Harness With Synthetic-Only Fixtures

Date: 2026-05-12
Owner lane: prompt pack emitted by G0 SCID forward-capture offline-schema synthesis
Evidence class: `SCID_CAPTURE_SCHEMA_TO_RUNTIME_TEST_HARNESS_SYNTHETIC_ONLY_ONLY`
Input G0 route: `research/science_program_2026_05/06_outcome_testing/g0_scid_forward_capture_offline_schema_package_synthesis_control/`
Input G12 audit: `research/science_program_2026_05/06_outcome_testing/g12_scid_forward_capture_offline_schema_implementation_package_audit/`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Objective

Build a source/control-only runtime-facing test harness that feeds synthetic capture rows through the accepted offline schemas and validator contracts, proving fail-closed behavior before any live wiring exists.

Examples are starting points, not limits. Current GTOS OB/retest logic, current SCID-only framing, the ten accepted schema groups, and the listed route families are not the research horizon. Stay auditable, as-of, no-leak, source/control-only, and hard-boundary-compliant while maximizing useful implementation-readiness output.

This route must build a real research-lane harness, not a design memo. The harness should be executable, deterministic, synthetic-only, no-live, and useful to a later owner-approved implementation lane. It may create route-local adapters, generators, validators, fixtures, and tests, but must not import or mutate production runtime in a way that changes behavior.

## Maximum Output Requirements

Push the harness to the practical maximum inside the synthetic-only evidence class. Speed is not a quality constraint. Do not stop at one fixture per group if more negative cases are useful.

This route is complete only if it answers:

- Can every one of the ten capture groups pass through a deterministic parser/validator path?
- Can missing, stale/as-of, forbidden identifier, duplicate-key drift, unavailable-source, schema-version mismatch, unsafe flag, and manifest-repair cases fail closed?
- Can valid redacted rows pass without raw broker/account/order/deal/position or result/performance leakage?
- Can synthetic rows be generated and mutated without using live logs, raw market blobs, broker evidence, outcomes, or AI/API?
- What exact runtime-facing adapter shape should a later implementation lane use?
- What would make this route a shallow fixture exercise, and which emitted tests prevent that?

## Mandatory Preflight

1. Run `python scripts/generate_live_state.py`.
2. Read `.context/LIVE_STATE.md`.
3. Read `.context/00_core/quick_reference_card.md`.
4. Read `.context/00_core/research_operating_doctrine.md`.
5. Read `.context/00_core/goal_session_research_discipline.md`.
6. Read `.context/00_core/research_current_state.md`.
7. Read this prompt from disk.
8. Read the accepted G12 offline-schema audit decision, schema contract audit, fixture recomputation audit, manifest/read-only/no-leak audit, output manifest, verifier result, completion audit, and closeout verification.
9. Read the original offline schema package field-group schema ledger, parser/redaction/as-of/no-leak validator contract, fixture manifest, fixture validation result, read-only monitoring alignment ledger, manifest hash policy, output manifest, verifier result, and closeout verification.
10. Read the immediate upstream G0/G12 source-capture synthesis artifacts needed to preserve the 3,014 candidate boundary, ten capture groups, manifest-binding repair, and anti-boxing route bundle.

Do not rely on chat memory. If interrupted or compacted, regenerate `LIVE_STATE`, re-read this prompt and the current route artifacts from disk, and resume from the emitted context anchor.

## Mandatory Context Use

Treat `.context/00_core/goal_session_research_discipline.md` and `.context/00_core/research_operating_doctrine.md` as active instructions. Record in the completion audit:

- whether both were read after preflight;
- the builder/control posture applied;
- anti-boxing questions pursued;
- searched roots and artifacts inspected;
- proof-or-impossibility stop condition;
- any doctrine requirement deliberately not answered because it crosses validation, result scoring, broker evidence, AI/API, paid/vendor, raw-blob, prompt/config/risk/safety/execution/canary/selector, or live-behavior boundaries.

## Accepted Package Boundary

Carry forward the accepted G12 decision `ACCEPT_AS_G12_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_CONTROL_EVIDENCE_ONLY`. Preserve exactly:

- offline schema/parser/fixture/validator/read-only alignment evidence only;
- live wiring absent and required as a future gate;
- 3,014 `candidate_input_row_id` values and 3,014 `duplicate_proxy_denominator_key` values as source/control coverage expectations only, not result denominators;
- ten capture groups: side, entry, stop, target, POI, framework, lifecycle, LTF, orderflow/proxy, baseline-control;
- manifest-binding repair: current G12 prompt hash rebound, self-referential output manifest hash drift non-blocking, all other hash mismatches strict.

## Hard Boundaries

Preserve `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`. Do not open validation/result-scoring/strategy-edge/R/PnL/win-rate/expectancy/performance/promotion/live behavior/AI/API/paid-vendor/broker-account-order-history-deal-position/raw-market-blob/prompt-config-risk/safety/execution/canary/selector changes.

Use checkpointing, chunking, and resumable ledgers rather than accepting shallow summaries. Do not stage unrelated runtime, shadow, live-monitoring, raw market-data, or production-code dirt.

## Route-Specific Requirements

- Do not wire the harness into live producers, watchdog, orchestrator, execution, permissions, prompts, canaries, selectors, or config.
- All fixtures must be synthetic/control-only and visibly redacted.
- If a runtime code import would touch production behavior, replace it with a pure test adapter or document the future approval gate.
- Build route-local synthetic row generators and mutation helpers for all ten groups.
- Include positive and negative fixture categories for every group where possible; if a category cannot apply, prove why in a fixture coverage ledger.
- Add deterministic hash/manifest checks for fixture and schema inputs so later G12 can rerun the harness.

## Required Outputs

- context anchor and accepted-audit reconciliation
- synthetic-only fixture expansion ledger
- runtime-facing parser/harness contract with no producer wiring
- route-local harness module or script
- negative fixture matrix for missing, stale, forbidden, duplicate, unavailable, unsafe-flag, manifest-repair, and schema-version cases
- fixture generator and mutation ledger
- leak/redaction audit for generated rows
- future implementation adapter contract
- G12 harness audit prompt and one-line starter
- standalone verifier, focused tests, completion audit, closeout verification

## Completion Standard

1. Harness uses only synthetic fixtures and committed schema/control artifacts.
2. No raw market blobs, live logs, broker/account/order/deal/position evidence, validation, result labels, or AI/API calls are consumed.
3. All ten capture groups have positive and fail-closed fixture routes, or exact proof why a specific fixture category is inapplicable.
4. Route-local harness, generator/mutator, verifier, and focused tests are emitted.
5. Saturation/self-red-team ledger proves the route did not stop at shallow fixture coverage.
6. Verifier and focused tests pass or exact blockers are recorded.

## One-Line Starter

`/goal Follow the full controlling prompt in research/science_program_2026_05/04_goal_prompts/SCID_CAPTURE_SCHEMA_TO_RUNTIME_TEST_HARNESS_SYNTHETIC_ONLY_FROM_OFFLINE_SCHEMA_SYNTHESIS_GOAL_PROMPT_2026-05-12.md as the complete objective; do mandatory preflight and context refresh first; do not rely on chat memory; stay SCID_CAPTURE_SCHEMA_TO_RUNTIME_TEST_HARNESS_SYNTHETIC_ONLY_ONLY with no validation/result-scoring/strategy-edge/R/PnL/win-rate/expectancy/performance/promotion/live behavior/AI/API/paid-vendor/broker-account-order-history-deal-position/raw-market-blob/prompt-config-risk-safety-execution-canary-selector changes; preserve accepted G12 offline schema package, 3,014 coverage boundary, ten capture groups, manifest-binding repair, offline-only/live-wiring-absent boundary, NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false; build an executable route-local synthetic harness with generators, mutators, positive/negative fixtures, leak/redaction audits, future adapter contract, verifier/tests, G12 prompt, and saturation proof that this is not shallow fixture coverage; pursue proof-or-impossibility until the prompt file's completion standard is fully satisfied.`
