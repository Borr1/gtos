# G12 NO-API Mechanical Replay Family Path-Behavior Discovery Result Audit Goal Prompt

Date: 2026-05-10
Owner lane: post-result G12 audit after quarantined no-API discovery result screen
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Goal

Independently audit `NO_API_MECHANICAL_REPLAY_FAMILY_PATH_BEHAVIOR_DISCOVERY_RESULT_SCREEN`.

Target route:

`research/science_program_2026_05/06_outcome_testing/no_api_mechanical_replay_family_path_behavior_discovery_result_screen/`

This G12 route must decide whether the target result screen can be accepted as a quarantined discovery path-behavior ledger only. Acceptance must not validate an edge, promote a family, change live behavior, call AI/API, use paid/vendor access, read broker account/order/history/deal/position evidence, or describe path labels as wins, losses, R, PnL, expectancy, or performance.

## Mandatory Preflight And Context

1. Run `python scripts\generate_live_state.py`.
2. Read `.context\LIVE_STATE.md`.
3. Read the latest numbered `.context\02_session_handoffs\*`.
4. Read `.context\00_core\quick_reference_card.md`.
5. Read `.context\00_core\research_operating_doctrine.md`.
6. Read `.context\00_core\research_current_state.md`.
7. Read `.context\00_core\goal_session_research_discipline.md`.
8. Read the target route artifacts, builder, verifier, focused tests, and this prompt.
9. Read the accepted target/G12/G0 predecessor artifacts referenced by the target context anchor.

## Required Audit Work

1. Re-run the target verifier and focused tests.
2. Verify the target matrix used full-population aggregate evidence, not compact-only decisive ranking.
3. Verify counts match accepted headlines: raw candidate attempts `13540033`, duplicate candidate keys `687275`, unique denominator `12852758`, and path-label rows `12852758`.
4. Verify all 11 opened families and all four baseline controls are included.
5. Verify label vocabulary is exact and ambiguity/unresolved burdens are separated from other path labels.
6. Verify no artifact uses path labels as R, PnL, win-rate, expectancy, validation, promotion, broker actual-R, or performance.
7. Verify LFS pointer/materialization checks for the accepted compact JSONL artifacts and no new raw >100MB Git blobs.
8. Verify selection-bias, multiple-testing, compact-cap, context-anchor, instruction-coverage, no-leak/dirty-state, saturation/self-red-team, output manifest, and completion audit artifacts.
9. Verify no prompt/config/risk/safety/execution/live trading surfaces changed.
10. Emit an audit decision: `ACCEPT_AS_QUARANTINED_DISCOVERY_PATH_BEHAVIOR_LEDGER`, `ACCEPT_WITH_EXACT_REPAIR_REQUIREMENTS`, or `REJECT_FOR_RESULT_SCREEN_DEFECT`.

## Completion Standard

Complete only if the audit has independently inspected real target artifacts, rerun verifier/tests or recorded exact environment blockers, mapped every target prompt requirement to evidence, verified no forbidden surfaces opened, and emitted a clear accept/reject/repair decision with `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.

One-line starter:

`/goal Follow the full controlling prompt in research/science_program_2026_05/04_goal_prompts/G12_NO_API_MECHANICAL_REPLAY_FAMILY_PATH_BEHAVIOR_DISCOVERY_RESULT_AUDIT_GOAL_PROMPT_2026-05-10.md as the complete objective; do mandatory preflight and context refresh first; do not rely on chat memory; stay G12_SOURCE_CONTROL_AUDIT_ONLY with no AI/API, validation, promotion, live behavior, paid/vendor access, credentials, remotes, broker account/order/history/deal/position use, or prompt/config/risk/safety changes; independently audit the no-api family path-behavior result screen artifacts, full-population aggregate proof, denominator/duplicate freeze, LFS/materialization checks, baseline controls, label-boundary language, no-leak/dirty-state scope, selection-bias ledger, completion audit, builder/verifier/focused tests, and scoped commits; complete with an accept/reject/repair decision, NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false.`
