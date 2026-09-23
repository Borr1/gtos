# G12 SCID To As-Of Bar Derivation Contract And Candidate Generator Constraint Audit Goal Prompt

Date: 2026-05-11
Owner lane: independent G12 contract audit only
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Goal

Independently audit `SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AND_CANDIDATE_GENERATOR_CONSTRAINT` under:

`research/science_program_2026_05/06_outcome_testing/scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint/`

This G12 lane may audit parser rules, timestamp/as-of semantics, OHLCV/gap/session handling, duplicate/proxy controls, discovery-source exclusions, forbidden-field policy, fixture coverage, verifier/test evidence, and source-control gates. It must not execute validation, generate scored candidates, derive path-label outcomes, calculate R/PnL/win-rate/expectancy/performance/cost/slippage, promote anything, call AI/API, use paid/vendor/credential/remote routes, inspect broker account/order/history/deal/position evidence, commit raw market-data blobs, or touch live behavior/prompt/config/risk/safety/execution/canary/selector surfaces.

## Mandatory Preflight

1. Run `python scripts/generate_live_state.py`.
2. Read `.context/LIVE_STATE.md`.
3. Read the latest numbered `.context/02_session_handoffs/*`.
4. Read `.context/00_core/quick_reference_card.md`.
5. Read `.context/00_core/research_operating_doctrine.md`.
6. Read `.context/00_core/research_current_state.md`.
7. Read `.context/00_core/goal_session_research_discipline.md`.
8. Read this prompt and the controlling contract prompt.
9. Read the route artifacts, builder, verifier, focused tests, and upstream G12 repair acceptance artifacts referenced by the output manifest.

## Required G12 Audit Questions

1. Do all required artifacts exist and parse as JSON/Markdown where required?
2. Is the SCID parser contract exact, including `<4sIIHHI36s`, `<QffffIIII`, Sierra epoch, 56-byte header, 40-byte records, and source timestamp handling?
3. Are all 9 G12-accepted bounded SCID segments referenced by manifest/hash only, with no raw blob copy?
4. Is the interval/as-of policy left-closed/right-open and unable to read records after decision as-of?
5. Are OHLCV, bid/ask volume, trade count, empty bars, gaps, session closures, duplicate timestamps, same-millisecond records, and non-monotonic records handled fail-closed?
6. Do duplicate/proxy controls prevent full/mini/micro/proxy double-counting?
7. Are 365 discovery-source exclusions and all four adversarial baselines preserved exactly?
8. Does the forbidden-field ledger reject post-decision, path-label, result, broker/account/order/history, cost/slippage, AI/API, and live-effect fields?
9. Can a future candidate-generator input packet silently become validation execution? Reject if yes.
10. Do verifier, focused tests, JSON parse, and py_compile evidence pass or precisely separate environment friction?
11. Does the committed diff avoid raw market-data blobs and forbidden live-surface changes?

## Terminal Decisions

Allowed terminal decisions:

- `ACCEPT_AS_SOURCE_CONTROL_SCID_ASOF_CONTRACT_ONLY`
- `REJECT_CONTRACT_LEAK_OR_AMBIGUITY`
- `BLOCKED_EXACT_SOURCE_OR_ENVIRONMENT_REASON`

Acceptance may only unlock a future source-control bar-builder/input-packet lane. It must not unlock validation execution, result scoring, promotion, live behavior, AI/API, paid/vendor access, credentials, remotes, broker account/order/history/deal/position evidence, or prompt/config/risk/safety/execution/canary/selector changes. Any scoring route remains a separate sealed validation execution prompt only.

## One-Line Starter

`/goal Follow the full controlling prompt in research/science_program_2026_05/04_goal_prompts/G12_SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AND_CANDIDATE_GENERATOR_CONSTRAINT_AUDIT_GOAL_PROMPT_2026-05-11.md as the complete objective; do mandatory preflight and context refresh first; do not rely on chat memory; stay G12_SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AUDIT_ONLY with no validation execution, scored candidate generation, path-label/result outcomes, R/PnL/win-rate/expectancy/performance/cost/slippage scoring, promotion, live behavior, AI/API, paid/vendor access, credentials, remotes, broker account/order/history/deal/position evidence, raw market-data blob commits, or prompt/config/risk/safety/execution/canary/selector changes; audit the SCID parser/timestamp/interval/as-of/OHLCV/gap/session/duplicate/proxy/no-leak/forbidden-field/discovery-exclusion/adversarial-baseline contract to proof-or-reject; complete only with JSON+MD decision artifacts, verifier/focused tests reviewed, scoped commits, closeout verification, NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false.`
