# G12 SCID As-Of Bar Builder And Candidate Input Packet Source-Control Audit Goal Prompt

Date: 2026-05-11
Owner lane: independent G12 packet source-control audit only
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Goal

Independently audit `SCID_ASOF_BAR_BUILDER_AND_CANDIDATE_INPUT_PACKET_SOURCE_CONTROL` under:

`research/science_program_2026_05/06_outcome_testing/scid_asof_bar_builder_and_candidate_input_packet_source_control/`

This audit must decide whether the 7,567 source-control bars and 3,014 candidate-generator input rows can be accepted as input-only source-control packet evidence. It must independently verify source rehashes, as-of bar construction, warning repairs, no-leak gates, input-only candidate semantics, duplicate/proxy controls, discovery exclusions, adversarial baseline preservation, raw-data handling, dirty-state scope, and route verification.

Acceptance may only unlock a future G0/G12 source-control synthesis or sealed-validation design prompt. It must not unlock validation execution, scored candidate generation, path-label/result outcomes, R/PnL/win-rate/expectancy/performance/cost/slippage scoring, promotion, live behavior, AI/API routes, paid/vendor access, credentials/remotes, or broker account/order/history/deal/position evidence.

## Mandatory Preflight And Context

1. Run `python scripts/generate_live_state.py`.
2. Read `.context/LIVE_STATE.md`.
3. Read the latest numbered `.context/02_session_handoffs/*`.
4. Read `.context/00_core/quick_reference_card.md`.
5. Read `.context/00_core/research_operating_doctrine.md`.
6. Read `.context/00_core/research_current_state.md`.
7. Read `.context/00_core/goal_session_research_discipline.md`.
8. Read `.context/00_core/local_heavy_data_inventory.md`.
9. Read `.context/00_core/ai_in_loop_cost_control_research_plan.md`.
10. Read `research/science_program_2026_05/05_synthesis/HISTORICAL_SEALED_VALIDATION_PROTOCOL_PLAN_2026-05-09.md`.
11. Read this controlling prompt.
12. Read the target packet route, including builder, verifier, tests, JSON/JSONL artifacts, manifests, repair ledgers, completion audit, closeout ledger, and output manifest.
13. Read the G12 SCID-to-asof contract audit route:
    `research/science_program_2026_05/06_outcome_testing/g12_scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint_audit/`.
14. Read the SCID-to-asof contract route:
    `research/science_program_2026_05/06_outcome_testing/scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint/`.
15. Read the G12 SCID segment repair route:
    `research/science_program_2026_05/06_outcome_testing/g12_fpb_sealed_source_pool_immutable_scid_hash_freeze_repair_reaudit/`.
16. Read the bounded segment repair route:
    `research/science_program_2026_05/06_outcome_testing/fpb_sealed_source_pool_immutable_scid_hash_freeze_repair/`.
17. Read the G0 sealed partition route:
    `research/science_program_2026_05/06_outcome_testing/g0_fpb_sealed_partition_and_adversarial_baseline_packet/`.

Do not rely on chat memory, thread summaries, or compaction memory. If interrupted, resumed, or uncertain, regenerate `LIVE_STATE`, reread this controlling prompt and latest artifacts from disk, and continue from committed state.

Runtime and speed are not quality constraints. Do not accept the packet because target verifier passed alone. Independently recheck packet semantics and source-control boundaries.

## Evidence Class

`G12_SCID_ASOF_BAR_BUILDER_AND_CANDIDATE_INPUT_PACKET_SOURCE_CONTROL_AUDIT_ONLY`

Allowed:

- independent parsing of target JSON/JSONL/MD artifacts;
- independent rehash/recompute checks over accepted source segment references, bar manifests, and candidate packet manifests;
- rerunning target verifier and focused tests as supporting evidence;
- building a new G12 audit route, verifier, focused tests, decision ledger, blocker/warning ledger, packet audit, and completion audit;
- scoped commits for the G12 audit route and research-state refresh.

Forbidden:

- validation execution;
- sealed-validation row/result generation;
- scored candidate generation;
- replay/path-label/result outcome generation;
- R, PnL, win-rate, expectancy, performance, cost, slippage, or promotion claims;
- AI/API calls, paid/vendor access, credentials, remotes, broker account/order/history/deal/position evidence, or live trade result reads;
- live behavior, live restart, prompt/config/risk/safety/execution/canary/selector changes;
- committing raw `.scid`, `.parquet`, `.csv`, `.dly`, `.bin`, segment blobs, or other raw market-data files.

## Required Independent Audit Checks

1. Verify the prior G12 contract decision is `ACCEPT_WITH_EXACT_CONTRACT_WARNINGS` with zero terminal blockers.
2. Verify both exact warnings were repaired with executable tests and verifier checks:
   - `FORBIDDEN_SCAN_OVERMATCH_WIN_WINDOW`
   - `TARGET_TESTS_DO_NOT_EXECUTE_HARD_FLOOR_CASE`
3. Re-run JSON/JSONL parse checks across all route artifacts, including all 7,567 bar rows and 3,014 candidate input rows.
4. Re-run the target route verifier and focused pytest.
5. Recompute all 9 accepted SCID segment hashes from bounded byte ranges or verify an independent target rehash ledger that proves current local bytes match accepted segment hashes.
6. Verify every bar row uses only bytes inside its accepted segment boundaries and carries source segment/hash references.
7. Verify all bar intervals are left-closed/right-open.
8. Verify no bar or candidate input includes records at or after decision as-of.
9. Verify empty/gap/session-closed bars fail closed and cannot create eligible candidates through fill/inference.
10. Verify every candidate row has status `CANDIDATE_GENERATOR_INPUT_ONLY_NOT_VALIDATION`.
11. Verify candidate rows contain only input fields and no path-label/result/performance/cost/slippage/broker/account/order/history/deal/position/AI/API/live fields.
12. Verify forbidden-field scanner repair does not overmatch `bar_window_start_utc` / `bar_window_end_utc` and still catches true result/performance fields.
13. Verify hard-floor tests reject before-floor, before-segment, after-segment, and decision-as-of leakage cases.
14. Verify candidate row count `3014` and bar row count `7567` match manifests and are stable.
15. Verify candidate duplicate keys are unique or duplicate-policy-controlled exactly as frozen.
16. Verify duplicate/proxy denominator controls prevent GC/MGC and YM/MYM double counting.
17. Verify the 365 discovery-source exclusions and four adversarial baselines are preserved exactly.
18. Verify no raw `.scid`, `.parquet`, `.csv`, `.dly`, `.bin`, or segment blob market-data files are staged or committed.
19. Verify committed-diff scope avoids forbidden live-surface changes; record unrelated live/runtime/shadow dirt as informational only.
20. Emit exact blockers or warnings if any ambiguity remains. Do not accept vague "looks okay" evidence.

## Required Artifacts

Create a G12 audit route under:

`research/science_program_2026_05/06_outcome_testing/g12_scid_asof_bar_builder_and_candidate_input_packet_source_control_audit/`

Required artifacts:

- `G12_SCID_ASOF_PACKET_AUDIT_DECISION_LEDGER_2026-05-11.json`
- `G12_SCID_ASOF_PACKET_AUDIT_DECISION_LEDGER_2026-05-11.md`
- `G12_SCID_ASOF_PACKET_AUDIT_SOURCE_REHASH_REVIEW_2026-05-11.json`
- `G12_SCID_ASOF_PACKET_AUDIT_BAR_BOUNDARY_REVIEW_2026-05-11.json`
- `G12_SCID_ASOF_PACKET_AUDIT_CANDIDATE_INPUT_REVIEW_2026-05-11.json`
- `G12_SCID_ASOF_PACKET_AUDIT_WARNING_REPAIR_REVIEW_2026-05-11.json`
- `G12_SCID_ASOF_PACKET_AUDIT_DUPLICATE_PROXY_REVIEW_2026-05-11.json`
- `G12_SCID_ASOF_PACKET_AUDIT_DISCOVERY_BASELINE_REVIEW_2026-05-11.json`
- `G12_SCID_ASOF_PACKET_AUDIT_FORBIDDEN_FIELD_REVIEW_2026-05-11.json`
- `G12_SCID_ASOF_PACKET_AUDIT_BLOCKER_WARNING_LEDGER_2026-05-11.json`
- `G12_SCID_ASOF_PACKET_AUDIT_COMPLETION_AUDIT_2026-05-11.json`
- `G12_SCID_ASOF_PACKET_AUDIT_COMPLETION_AUDIT_2026-05-11.md`
- `G12_SCID_ASOF_PACKET_AUDIT_VERIFICATION_RESULT_2026-05-11.json`
- `verify_g12_scid_asof_packet_audit_2026_05_11.py`
- focused pytest file.

If accepted, emit the next prompt. The next prompt must be one of:

- a G0 source-control synthesis route if the packet needs route selection before validation design;
- a sealed-validation design prompt if all packet-control requirements are accepted and the next step is to design validation without executing it.

The next prompt must not execute validation unless a separate future lane explicitly opens validation execution after source-control acceptance.

## Required Saturation And Self-Red-Team

Before completion, answer and pursue same-evidence-class gaps:

1. What exact bug would let source bytes outside accepted segments enter a bar?
2. What exact bug would let a candidate input include future records at/after decision as-of?
3. What exact bug would make an input-only row look like a validation/result/path-label row?
4. What exact bug would let forbidden scanner repairs become too permissive?
5. What exact bug would let `bar_window_*` overmatch return and block legitimate fields again?
6. What exact bug would turn empty/gap/session-closed bars into eligible candidates?
7. What exact duplicate/proxy mistake could inflate the 3,014 candidate denominator?
8. What exact row-level or manifest evidence proves 365 discovery-source exclusions remain outside the packet?
9. What exact raw-data or Git/LFS issue could make the packet unsafe to push or clone?
10. What exact next evidence-class gate is required before any validation or scoring can happen?

If any answer exposes an allowed same-evidence-class gap, pursue it before closeout. "Outside scope" is valid only when the next step crosses into validation execution, scoring, G0 synthesis, registry edit, live behavior, paid spend, credentials/remotes, or forbidden broker/account/order evidence.

## Terminal Decisions

Allowed terminal decisions:

- `ACCEPT_AS_SOURCE_CONTROL_SCID_ASOF_CANDIDATE_INPUT_PACKET_ONLY`
- `ACCEPT_WITH_EXACT_PACKET_WARNINGS`
- `REPAIR_BLOCKED_PACKET`
- `REJECT_PACKET_LEAK_OR_AMBIGUITY`

Acceptance requires:

- both prior G12 warnings repaired;
- 9/9 source segments rehashed or independently proven by accepted rehash ledger;
- 7,567 bar rows source-bounded and as-of safe;
- 3,014 candidate input rows input-only and no-leak clean;
- duplicate/proxy controls accepted;
- 365 discovery-source exclusions and four adversarial baselines preserved;
- no raw market-data blobs committed;
- target verifier/tests and G12 verifier/tests pass;
- safe flags remain closed.

If any requirement fails, do not accept. Emit exact blockers naming failed artifact, failed rule, affected rows/counts, and required repair.

## Completion Standard

Mark complete only when:

- all required G12 artifacts exist;
- independent packet audit has run;
- terminal decision is frozen;
- next prompt exists if and only if acceptance allows it;
- verifier and focused tests pass or environment friction is precisely separated from code failure;
- scoped commits are made;
- closeout `LIVE_STATE` is regenerated;
- safe flags remain `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`;
- remaining worktree dirt is recorded as unrelated runtime/generated dirt, not hidden in the audit.

## One-Line Starter

`/goal Follow the full controlling prompt in research/science_program_2026_05/04_goal_prompts/G12_SCID_ASOF_BAR_BUILDER_AND_CANDIDATE_INPUT_PACKET_SOURCE_CONTROL_AUDIT_GOAL_PROMPT_2026-05-11.md as the complete objective; do mandatory preflight and context refresh first; do not rely on chat memory or compaction memory; stay G12_SCID_ASOF_BAR_BUILDER_AND_CANDIDATE_INPUT_PACKET_SOURCE_CONTROL_AUDIT_ONLY with no validation execution, sealed-validation row/result generation, scored candidate generation, replay/path-label/result outcomes, R/PnL/win-rate/expectancy/performance/cost/slippage scoring, promotion, live behavior, AI/API, paid/vendor access, credentials, remotes, broker account/order/history/deal/position evidence, raw market-data blob commits, or prompt/config/risk/safety/execution/canary/selector changes; independently audit the 7,567 source-control bars and 3,014 input-only candidate rows, proving both prior G12 warnings repaired, 9 SCID segment rehashes valid, bars source-bounded and as-of safe, candidates CANDIDATE_GENERATOR_INPUT_ONLY_NOT_VALIDATION with no forbidden fields, duplicate/proxy controls, 365 discovery exclusions, four baselines, raw-data safety, dirty-state scope, and future gates preserved; do not stop at target verifier pass; pursue every same-evidence-class ambiguity until accepted, exactly packet-blocked, rejected, or proven impossible from approved routes; emit JSON+MD decision/source/bar/candidate/warning/duplicate/discovery/forbidden/blocker/completion artifacts, G12 verifier/focused tests, next source-control/design prompt only if accepted, scoped commits, closeout verification, NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false; mark complete only when this prompt file's completion standard is fully satisfied.`
