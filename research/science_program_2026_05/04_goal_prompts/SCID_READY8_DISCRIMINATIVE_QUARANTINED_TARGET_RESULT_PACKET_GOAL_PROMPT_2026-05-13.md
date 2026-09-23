# SCID READY8 Discriminative Quarantined Target-Result Packet

Date: 2026-05-13

Evidence class: `SCID_READY8_DISCRIMINATIVE_QUARANTINED_TARGET_RESULT_PACKET_ONLY`

Objective: build the separate quarantined no-API target-result/materialization packet authorized by `G0_SCID_READY8_DISCRIMINATIVE_RESULT_OPENING_GATE_AFTER_G12_AUDIT`. This route may materialize neutral target-result rows, but it is not validation, not promotion, not strategy performance scoring, and not a live-trading change.

This is a constructive result-packet builder. It must be exhaustive inside its evidence class, not conservative, boxed, sample-only, OB-only, or speed-limited. The hard boundaries below prevent contamination and false promotion; they must not be used as brakes against computing every authorized quarantined target-result row, sidecar diagnostic, concentration view, fail-closed reason, source-quality view, and repairable same-class issue.

## Mandatory Preflight And Context

1. Run `python scripts/generate_live_state.py`, then read `.context/LIVE_STATE.md`.
2. Read `.context/00_core/goal_session_research_discipline.md`, `.context/00_core/research_operating_doctrine.md`, `.context/00_core/research_current_state.md`, `.context/00_core/local_heavy_data_inventory.md`, and `.context/00_core/ai_in_loop_cost_control_research_plan.md`.
3. Read the G0 gate artifacts at `research/science_program_2026_05/06_outcome_testing/g0_scid_ready8_discriminative_result_opening_gate_after_g12_audit/`.
4. Read the accepted G12 audit route at `research/science_program_2026_05/06_outcome_testing/g12_scid_ready8_discriminative_card_rowset_repair_audit/`.
5. Read the repaired discriminative rowset route at `research/science_program_2026_05/06_outcome_testing/scid_ready8_discriminative_card_rowset_repair_and_sealed_validation_design/`.
6. Read the target-horizon contract at `research/science_program_2026_05/06_outcome_testing/scid_noapi_ready8_rowset_target_horizon_result_packet_materialization/SCID_NOAPI_READY8_TARGET_HORIZON_CONTRACT_2026-05-12.json` and use it only as the accepted neutral target-family/horizon contract.

Do not rely on chat memory. Recompute from disk. Do not use the old redundant ready-8 rowset rows or old target-result rows as the input rowset for this route.

## Bound Input

Use exactly:

- repaired discriminative rowset path: `research/science_program_2026_05/06_outcome_testing/scid_ready8_discriminative_card_rowset_repair_and_sealed_validation_design/SCID_READY8_DISCRIMINATIVE_CARD_ROWSET_ROWS_2026-05-13.jsonl`
- repaired discriminative rowset SHA256: `fa478206605376275ae971e283f977cc6c77a2d7fd395b82354df8380662c9e3`
- source candidate universe: `3,014`
- READY8 cards: `8`
- repaired rowset rows: `24,112`
- status vocabulary: `PASS_DESCRIPTOR_CONTRAST_ELIGIBLE`, `PASS_CARD_PREDICATE`, `ELIGIBLE_CONTRAST_CONTROL`, `NON_APPLICABLE_SOURCE_CONTEXT`, `FAIL_CLOSED_MISSING_PRIOR_CANDIDATE`, `FAIL_CLOSED_DESCRIPTOR_NOT_COMPUTABLE`
- row identity fields: `candidate_input_row_id`, `card_id`, `rowset_row_id`, `duplicate_proxy_denominator_key`, `row_hash`

## Denominator Rules

- `per_card_pass_row` rows may enter the per-card pass denominator.
- `per_card_contrast_row` rows are within-card controls and must remain visible.
- `per_card_non_applicable_row` rows remain visible and cannot enter pass denominators.
- `per_card_fail_closed_row` rows remain visible with exact `fail_closed_reasons` and `missing_source_requirements`; they cannot be dropped or counted as passes.
- `ADV-001` and `ADV-003` are adversarial/placebo control cards even when their row status is `PASS_DESCRIPTOR_CONTRAST_ELIGIBLE`; they are not edge-card pass claims.
- Blocked dependencies, blocked-card rows, and expansion candidates remain sidecars outside the accepted READY8 discriminative denominator unless a separate G12/G0 route admits them.

## Allowed Target Families And Horizons

Compute only these neutral target families:

- `neutral_close_to_close_return_m15_horizons_v1`
- `neutral_high_low_excursion_m15_horizons_v1`

Compute only horizons `1`, `4`, `16`, and `32` closed M15 bars from `entry_reference_time_utc` using accepted source-control bar rows and strict source hashes. No additional target family or horizon is open in this route unless disk evidence inside the accepted G0 gate artifacts explicitly proves it source-safe and the route freezes it before computation.

## Required Work

- Materialize target-result rows for all `24,112` repaired discriminative rowset rows across both target families and all four horizons, preserving row status and denominator role.
- Emit per-card/family JSONL packets or an equivalently auditable sharded layout with exact counts and hashes.
- Build target-source join, denominator/status, duplicate/concentration, no-leak/as-of, fail-closed, blocker/repair, saturation/self-red-team, output-manifest, and completion-audit artifacts.
- Prove the next packet references the repaired discriminative rowset hash `fa478206605376275ae971e283f977cc6c77a2d7fd395b82354df8380662c9e3` and does not bind the old redundant rowset hash.
- Keep broad sidecar diagnostics for source quality, partition, symbol/session/source-proxy/source-segment concentration, and descriptor-control coverage, but do not convert sidecars into accepted-card denominators.
- Emit the exact next G12 audit prompt/starter for the discriminative target-result packet.
- Add standalone builder, verifier, and focused tests.

## No-Loop Materialization And Blocker Pursuit Contract

Do not convert materialization problems into another prompt unless the problem truly crosses an evidence-class or forbidden-surface boundary.

If any source join, target-bar lookup, row hash, row count, manifest hash, fail-closed reason, denominator-role handling, duplicate/concentration view, no-leak/as-of proof, sidecar diagnostic, shard layout, parser behavior, text EOL/hash issue, Windows filesystem friction, or prompt weakness appears, pursue it in this route until it is:

- repaired/recomputed/rebound/rehashed/re-manifested/reverified;
- exactly fail-closed at row level with the missing source field/window/path/hash and search evidence preserved;
- proven impossible from the accepted inputs and approved local routes;
- or proven to require a separate evidence-class gate such as G12 post-result audit, validation, promotion, live behavior, AI/API, paid/vendor access, broker/account/order/deal/position evidence, raw market blob commit, registry edit, remote push, or trading-surface change.

The route may not stop at "needs follow-up", "blocked by missing data", "top examples only", "representative rows", "compact sample", "likely okay", or "G12 can sort it out" when the issue is answerable by continuing this result-packet materialization. If a row cannot be computed, keep it in the packet as an auditable fail-closed row; do not silently drop it, replace it with a proxy, or move it to a vague future-work bucket.

No arbitrary caps are allowed. If a ledger has many rows, shard it, stream it, hash it, use Git LFS where appropriate, or write machine-readable full ledgers plus readable summaries. Rankings and examples are summaries only, never replacements for the full packet.

Before completion, run a saturation/self-red-team pass that asks what authorized target/result/source/denominator/partition/duplicate/concentration/no-leak/fail-closed intelligence remains unextracted. If any same-evidence-class answer remains feasible, continue instead of closing.

## Forbidden Surfaces

Do not compute or claim R, PnL, win rate, expectancy, Sharpe, performance, strategy edge, validation, promotion, live readiness, broker actual-R, account/order/history/deal/position labels, AI/API decisions, paid/vendor pulls, raw market blob commits, credentials, registry edits, remote pushes, live restarts, or trading prompt/config/risk/safety/execution/canary/selector behavior changes.

Neutral target movement is quarantined result materialization only. It must not be described as trading performance or a promotion signal.

## G12 Post-Result Audit Requirement

The result packet is incomplete until a separate G12 audit recomputes rowset hash, target-family/horizon counts, target-row hashes, target-source joins, fail-closed statuses, duplicate/concentration ledgers, no-leak/as-of proof, sidecar quarantine, and forbidden-surface closure. The G12 audit must reject any packet that binds the old redundant ready-8 rowset instead of the repaired discriminative rowset.

## Terminal Decisions

- `MATERIALIZED_SCID_READY8_DISCRIMINATIVE_QUARANTINED_TARGET_RESULT_PACKET_G12_AUDIT_REQUIRED`
- `KEEP_SCID_READY8_DISCRIMINATIVE_TARGET_RESULT_PACKET_CLOSED_WITH_EXACT_REPAIR_OR_SOURCE_BLOCKERS`

Preserve `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false` in every artifact. Complete only after materialization or exact blocker proof, verifier/focused tests, updated context, and scoped commits.
