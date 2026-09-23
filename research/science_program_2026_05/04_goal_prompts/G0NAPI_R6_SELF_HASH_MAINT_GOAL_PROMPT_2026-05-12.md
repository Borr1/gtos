# SCID_TARGET_MANIFEST_SELF_HASH_POLICY_MAINTENANCE

Evidence class: `SCID_TARGET_MANIFEST_SELF_HASH_MAINTENANCE_ONLY`

Objective: Normalize the target output manifest policy so the manifest is excluded from its own blocking hash list or explicitly marked nonbinding, without treating the current G12 acceptance as blocked.

Do not rely on chat memory. Run mandatory preflight/context refresh before work. Current GTOS OB/retest logic is not the research horizon; examples and the accepted 40 cards are a floor, not a ceiling.

This is a maintenance lane, but it must still be exact and complete. Do not let a small maintenance issue become either a fake blocker or a broad refactor. Fix the self-referential manifest policy in the narrowest durable way, prove that card counts, packet counts, blocker counts, hashes, accepted G12 facts, route rankings, and safe flags did not change, and emit a reusable policy note so future builders avoid the same self-hash trap.

## Mandatory Context Use

1. `python scripts/generate_live_state.py`
2. `.context/LIVE_STATE.md`
3. `.context/00_core/goal_session_research_discipline.md`
4. `.context/00_core/research_operating_doctrine.md`
5. `.context/00_core/research_current_state.md`
6. `.context/00_core/local_heavy_data_inventory.md`
7. `.context/00_core/ai_in_loop_cost_control_research_plan.md`
8. this G0 synthesis route directory: `research/science_program_2026_05/06_outcome_testing/g0_scid_noapi_40card_prereg_replay_input_design_synthesis`

## Inputs

- `research/science_program_2026_05/06_outcome_testing/g12_scid_noapi_40card_prereg_replay_input_design_audit/G12_SCID_NOAPI_PREREG_AUDIT_DECISION_LEDGER_2026-05-12.json`
- `research/science_program_2026_05/06_outcome_testing/scid_noapi_40card_prereg_input_design/` output manifest and verifier artifacts
- `research/science_program_2026_05/06_outcome_testing/g0_scid_noapi_40card_prereg_replay_input_design_synthesis/G0_SCID_NOAPI_PREREG_SYNTHESIS_NONBLOCKING_FOLLOWUP_LEDGER_2026-05-12.json`
- route-local builder/verifier/test files whose manifest policy caused or checks the self-reference.

Search route-local artifacts before patching. Do not assume the exact manifest filename from memory.

## Required Work

1. Reproduce the nonblocking self-hash issue from disk and record the exact file(s), expected/current hash behavior, and why G12 accepted it as nonblocking.
2. Patch only the route-local manifest policy or verifier policy needed to exclude/mark self-referential output-manifest entries as nonbinding while keeping all source/input/payload hashes strict.
3. Rerun the affected builder/verifier/tests or the strongest route-local equivalent.
4. Prove counts and accepted facts are unchanged: 40 cards, 8 domains, readiness split 8/15/17, 33 outside-current-GTOS/OB, 8 ready packet designs, 32 blocked rows, 8 expansion candidates, and safe flags.
5. Emit a policy note or repair ledger for future builders: self-manifest hashes are nonbinding only for the manifest hashing itself; all other hash mismatches remain strict blockers.
6. Do not let this route edit unrelated live/runtime/shadow dirt or broaden into result scoring.

## Required Outputs

Create a route under:

`research/science_program_2026_05/06_outcome_testing/scid_target_manifest_self_hash_policy_maintenance/`

Required artifacts:

- `SCID_SELF_HASH_REPRODUCTION_LEDGER_2026-05-12.json`
- `SCID_SELF_HASH_POLICY_REPAIR_LEDGER_2026-05-12.json`
- `SCID_SELF_HASH_NO_DENOMINATOR_RESULT_CHANGE_PROOF_2026-05-12.json`
- `SCID_SELF_HASH_SATURATION_SELF_RED_TEAM_2026-05-12.md`
- `SCID_SELF_HASH_VERIFICATION_RESULT_2026-05-12.json`
- `SCID_SELF_HASH_COMPLETION_AUDIT_2026-05-12.json`
- focused tests or verifier evidence for the patched policy.

## Boundaries

- `may_open_outcomes_or_results_in_this_route=false`
- Preserve `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.
- Do not open validation/results/R/PnL/win-rate/expectancy/performance/promotion/AI/API/paid-vendor/broker-account-order-history-deal-position/raw-market-blob/live-restart/live-behavior/trading-risk-safety-prompt-decision changes.
- Do not collapse to OB-only, passive waiting, or treating nonblocking self-hash maintenance as a blocker to R1-R5 progress.
- Preserve accepted-card, blocked-card, and expansion-candidate denominator boundaries.

## No-Leak/As-Of/Duplicate Requirements

- manifest maintenance must not alter card/packet/blocker counts

## Post-Route Gates

- focused maintenance verifier

## Completion Standard

Complete only with versioned artifacts, a reproduced self-hash diagnosis, narrow policy repair, no denominator/result change proof, saturation/self-red-team, verifier/focused tests, scoped commits, safe flags intact, and exact blockers where dependencies cannot be cleared. If any result/validation step appears necessary, emit it as a separate future evidence-class prompt and stop before scoring.

This route is optional and nonblocking for research progress. If run in parallel, it must not hold up R1-R5 and must not touch unrelated runtime/shadow/live files.
