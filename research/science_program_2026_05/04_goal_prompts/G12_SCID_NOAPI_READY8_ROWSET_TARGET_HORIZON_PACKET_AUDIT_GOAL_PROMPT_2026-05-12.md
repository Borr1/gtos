# G12 SCID No-API Ready-8 Rowset / Target-Horizon Packet Audit

Evidence class: `G12_SCID_NOAPI_READY8_ROWSET_TARGET_HORIZON_PACKET_AUDIT_ONLY`

Objective: independently audit the materialized ready-8 source-control packet in `research/science_program_2026_05/06_outcome_testing/scid_noapi_ready8_rowset_target_horizon_result_packet_materialization/` before any result-opening route is allowed. This is a fair-adversarial audit: reject real leakage or count drift, but do not reject merely because the packet intentionally has no validation/results/performance yet.

## Mandatory Preflight And Context

1. Run `python scripts/generate_live_state.py`, then read `.context/LIVE_STATE.md`.
2. Read `.context/00_core/goal_session_research_discipline.md`, `.context/00_core/research_operating_doctrine.md`, `.context/00_core/research_current_state.md`, `.context/00_core/local_heavy_data_inventory.md`, and `.context/00_core/ai_in_loop_cost_control_research_plan.md`.
3. Read the controlling ready-8 materialization prompt and all route artifacts from disk, including output manifest, rowset manifest, rowset JSONL, source/as-of audit, duplicate denominator manifest, partition/control manifest, baseline/control manifest, target-horizon contract, blocker/dependency ledger, expansion observation ledger, no-leak audit, completion audit, verifier, and focused test.
4. Do not rely on chat memory, summaries, or pasted closeouts. If interrupted or resumed, regenerate context and continue from disk.

## Required Independent Audit

- Recompute the eight ready cards exactly: `ADV-001`, `ADV-003`, `BEH-001`, `HAZ-001`, `HAZ-005`, `MAC-001`, `MAC-004`, `UNC-004`.
- Recompute the source candidate denominator `3014`, ready-card denominator `8`, rowset equation `3014 * 8 = 24112`, blocked-card dependency count `32`, accepted-card denominator `40`, and row-level exclusions `0`.
- Rehash or independently validate rowset rows, row hashes, source hashes, parser/as-of versions, `source_observed_asof_utc <= decision_asof_utc`, duplicate/proxy keys, partitions, matched controls, baseline assignments, and deterministic seed policy.
- Verify the target-horizon contract defines future windows/contracts only. It must contain no observed outcome labels, target-hit/stop-hit booleans, R/PnL/win-rate/expectancy/performance, promotion, broker/account/order/history/deal/position evidence, AI/API, paid/vendor, raw market blob, live restart, live behavior, prompt/config/risk/safety/execution/canary/selector changes.
- Verify the three expansion observations stay outside the ready-8 denominator and do not mutate the accepted 40. Treat the accepted 40 as a floor for later science, not a ceiling.
- Run the route verifier and focused tests. If environment friction appears, separate it precisely from code/artifact failure.

## Required G12 Artifacts

Emit a scoped G12 audit route with a decision ledger, rowset count audit, hash/as-of audit, duplicate/denominator audit, partition/baseline/control audit, target-horizon no-result audit, expansion quarantine audit, no-leak/forbidden-surface audit, blocker/follow-up ledger, completion audit, verifier, and focused tests. Emit a next G0 future-result-opening gate prompt only if acceptance allows it.

## Saturation / Self-Red-Team

Before completion, answer from disk: what exact bug would inflate 24,112 rows, leak future target/stop labels, confuse ready cards with blocked cards, let expansion observations enter the denominator, make controls non-deterministic, or silently open scoring? Pursue any same-evidence-class repair before closeout. Stop only for a different evidence class, not for convenience.

Allowed terminal decisions:

- `ACCEPT_READY8_SOURCE_CONTROL_PACKET_FOR_FUTURE_G0_RESULT_GATE_ONLY`
- `ACCEPT_WITH_EXACT_NONBLOCKING_FOLLOWUPS`
- `REJECT_REPAIR_REQUIRED`

Safe flags must remain: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.
