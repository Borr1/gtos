# G12 FPB Sealed Source Pool Materialization Audit Goal Prompt

Date: 2026-05-11
Owner lane: independent G12 source-control audit after FPB source expansion and sealed-pool materialization
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Goal

Build `G12_FPB_SEALED_SOURCE_POOL_MATERIALIZATION_AUDIT`.

Independently audit the FPB source-expansion and sealed-pool materialization packet. The audit may accept, repair-block, or reject the packet as source-control evidence only. It must not validate an edge, approve validation execution, score performance, promote a family, alter live behavior, call AI/API, use paid/vendor access, read broker account/order/history/deal/position evidence, or change prompts/config/risk/safety/execution/canary/selector behavior.

Primary packet:

`research/science_program_2026_05/06_outcome_testing/fpb_source_expansion_and_sealed_pool_materialization/`

Expected current packet shape:

- Materialized native SCID sealed-pool candidates: `9`
- Local CSV candidates after corrected SCID-named CSV symbol/timeframe inference: `0`
- All `365` selected FPB discovery source hashes remain excluded.
- Safe flags: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`
- This is source-pool audit only, not validation approval.

## Mandatory Preflight And Context

1. Run `python scripts\generate_live_state.py`.
2. Read `.context\LIVE_STATE.md`.
3. Read the latest numbered `.context\02_session_handoffs\*`.
4. Read `.context\00_core\quick_reference_card.md`.
5. Read `.context\00_core\research_operating_doctrine.md`.
6. Read `.context\00_core\research_current_state.md`.
7. Read `.context\00_core\goal_session_research_discipline.md`.
8. Read `.context\00_core\local_heavy_data_inventory.md`.
9. Read `.context\00_core\ai_in_loop_cost_control_research_plan.md`.
10. Read `research\science_program_2026_05\05_synthesis\HISTORICAL_SEALED_VALIDATION_PROTOCOL_PLAN_2026-05-09.md`.
11. Read the source-expansion controlling prompt:
    `research\science_program_2026_05\04_goal_prompts\FPB_SOURCE_EXPANSION_AND_SEALED_POOL_MATERIALIZATION_GOAL_PROMPT_2026-05-11.md`.
12. Read the target packet route:
    `research\science_program_2026_05\06_outcome_testing\fpb_source_expansion_and_sealed_pool_materialization\`.
13. Read the upstream sealed packet and FPB evidence chain:
    - `research\science_program_2026_05\06_outcome_testing\g0_fpb_sealed_partition_and_adversarial_baseline_packet\`
    - `research\science_program_2026_05\06_outcome_testing\g0_fpb_discovery_synthesis_control_route\`
    - `research\science_program_2026_05\06_outcome_testing\no_api_mechanical_replay_family_path_behavior_discovery_result_screen\`
    - `research\science_program_2026_05\06_outcome_testing\g12_fpb_result_audit\`

Do not rely on chat memory. If there is compaction, restart, interruption, or uncertainty, regenerate live state and reread this controlling prompt, the target packet, and core context docs from disk before continuing.

Runtime and speed are not quality constraints. This audit must not shallow-pass because the packet is small. Check every candidate, every exclusion, every source/hash/as-of/no-leak/duplicate/partition claim, and every prompt-compliance boundary. If an allowed same-evidence-class repair or deeper audit is needed, run it, chunk it, checkpoint it, or route exact blockers.

## Evidence Class

`G12_FPB_SEALED_SOURCE_POOL_SOURCE_CONTROL_AUDIT_ONLY`.

Allowed:

- source-control audit,
- partition safety audit,
- SCID source hash and metadata recomputation,
- coverage-window and post-embargo eligibility audit,
- parser/as-of/no-leak audit,
- duplicate-source and discovery-source exclusion audit,
- four-baseline preservation audit,
- SCID-to-asof-bar derivation gate audit,
- candidate-generator constraint audit,
- dirty-state/scoped-diff audit,
- repair-blocker ledger,
- next prompt pack creation,
- verifier, focused tests, and scoped commits.

Forbidden:

- validation execution,
- replay/path-label/result scoring,
- R, PnL, win-rate, expectancy, performance, cost, slippage, or promotion claims,
- live behavior, live restart, prompt/config/risk/safety/execution/selector/canary changes,
- AI/API calls,
- paid/API/Databento routes,
- credentials,
- remote push,
- broker account/order/history/deal/position/ticket/live trade result reads.

## Required Audit Work

1. Independently rerun or inspect the target verifier and focused tests; record exact command/status.
2. Recompute or independently verify the target packet shape: `9` native SCID candidates, `0` local CSV candidates, `365` discovery source hashes excluded.
3. Verify all safe flags remain `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.
4. Rehash every proposed native SCID source file or verify the hash through an independent source-hash ledger audit. Record file path, SHA256, byte size if available, coverage start/end UTC, and parser metadata.
5. Confirm every proposed native SCID source-pool candidate has:
   - source hash,
   - source family,
   - symbol,
   - timeframe or SCID-native resolution status,
   - coverage start/end UTC,
   - post-embargo eligible segment,
   - parser/as-of status,
   - no-leak status,
   - duplicate-source decision,
   - partition assignment.
6. Confirm all `365` selected discovery source hashes and accepted FPB discovery path-label rows remain excluded from future sealed validation.
7. Confirm the corrected SCID-named CSV symbol/timeframe inference issue really leaves `0` CSV sealed candidates and does not hide a recoverable CSV sealed pool.
8. Confirm the four adversarial baselines remain exactly:
   - `baseline_random_session_control`
   - `baseline_shifted_entry_control`
   - `baseline_momentum_continuation`
   - `baseline_mean_reversion`
9. Confirm no validation prompt was emitted and no validation execution, result scoring, R/PnL/win-rate/expectancy/performance language, broker evidence, AI/API, paid/vendor, or live surface was opened.
10. Confirm any future use remains gated on both:
    - a SCID-to-asof-bar derivation contract, and
    - a candidate generator constrained to `eligible_segment_start_utc` onward.
11. Produce a repair-blocker ledger. Do not stop at the first issue; continue auditing all candidates and exclusions so the packet gets a complete finding set.
12. Produce a hardening-coverage ledger mapping goal-session discipline, local-heavy-data policy, sealed-validation doctrine, no-speed-shortcut, owner-access pursuit, and hostile audit controls to audit outputs.
13. Produce a no-leak/dirty-state/scoped-diff audit that separates unrelated live/runtime dirt from target/audit write scope.
14. Produce a saturation/self-red-team pass that asks what a skeptical G12 would reject and either repairs, blocks, or accepts narrowly.
15. Emit the exact next prompt:
    - if accepted: a source-control route for `SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AND_CANDIDATE_GENERATOR_CONSTRAINT`;
    - if repair-blocked: an exact repair prompt;
    - if rejected: an exact rejection/failure-anatomy route.
16. Produce builder, verifier, focused tests, output manifest, JSON + MD audit verdict, and completion audit.
17. Refresh `.context\00_core\research_current_state.md` if the research map changes materially.

## Required Saturation And Self-Red-Team Questions

Before completion, answer and pursue any allowed same-evidence-class gaps:

1. What exact mistake would allow discovery-exposed source rows into the sealed pool?
2. What exact mistake would let SCID context become validation input before as-of bar derivation is frozen?
3. What exact mistake would let the candidate generator use pre-eligible-segment data?
4. What exact mistake would hide a recoverable CSV sealed pool after the SCID-named CSV inference repair?
5. Are any of the 9 SCID candidates duplicates or near-duplicates of discovery sources by hash, symbol/timeframe/window, source family, or provenance?
6. Is any proposed SCID candidate proxy-only, parser-ambiguous, or no-leak/as-of invalid?
7. Would baseline preservation fail if the selected families later use these sources?
8. What source/access/repair action would materially change the audit, and can it be executed in this G12 evidence class?
9. If the packet is accepted, what exactly remains blocked before validation execution?
10. If the packet is rejected or repair-blocked, what exact next artifact closes it?

## Completion Standard

You may mark complete only if:

- every required audit artifact exists,
- all 9 native SCID candidates are audited,
- local CSV candidate status is independently checked,
- all 365 discovery source hashes remain excluded,
- the four adversarial baselines remain preserved,
- SCID-to-asof-bar and eligible-segment candidate-generator gates remain explicit,
- no validation, scoring, promotion, AI/API, broker, paid/vendor, remote, credential, prompt/config/risk/safety/execution/canary/selector, or live behavior surface is opened,
- safe flags remain `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`,
- repair blockers are exact and complete,
- verifier and focused tests pass,
- commits are scoped,
- research context is refreshed if materially changed.

## One-Line Starter

`/goal Follow the full controlling prompt in research/science_program_2026_05/04_goal_prompts/G12_FPB_SEALED_SOURCE_POOL_MATERIALIZATION_AUDIT_GOAL_PROMPT_2026-05-11.md as the complete objective; do mandatory preflight and context refresh first; do not rely on chat memory or compaction memory; stay G12_FPB_SEALED_SOURCE_POOL_SOURCE_CONTROL_AUDIT_ONLY with no validation execution, replay/path-label/result scoring, R/PnL/win-rate/expectancy/performance, promotion, live behavior, AI/API, paid/vendor access, credentials, remotes, broker account/order/history/deal/position data, or prompt/config/risk/safety changes; independently audit the FPB source-expansion packet, all 9 native SCID sealed-pool candidates, 0 CSV candidate status after corrected SCID-named CSV inference, all 365 discovery-source exclusions, source hashes, coverage windows, post-embargo eligible segments, parser/as-of/no-leak status, duplicate-source decisions, partition assignments, four adversarial baselines, SCID-to-asof-bar derivation gate, eligible-segment candidate-generator constraint, no-leak/dirty-state scope, hardening coverage, and saturation/self-red-team; do not stop at the first issue; pursue every same-evidence-class repair or blocker until accepted, repair-blocked with exact next artifact, rejected with failure anatomy, or proven impossible from approved routes; emit JSON+MD audit verdict, repair-blocker ledger, runnable next prompt, builder/verifier/focused tests, scoped commits, closeout verification, NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false; mark complete only when the prompt file's completion standard is fully satisfied.`
