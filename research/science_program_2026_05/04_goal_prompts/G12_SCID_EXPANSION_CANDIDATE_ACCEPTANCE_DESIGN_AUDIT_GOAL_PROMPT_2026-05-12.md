# G12 SCID Expansion Candidate Acceptance Design Audit

Evidence class: `G12_SCID_EXPANSION_CANDIDATE_ACCEPTANCE_DESIGN_AUDIT_ONLY`

Objective: independently audit `research/science_program_2026_05/06_outcome_testing/scid_expansion_candidate_acceptance_and_design_route/` for source/control design acceptance only. The audit must verify the original 8 expansion candidates, the 4 G0-discovered candidates, and the 12 R4-discovered additional families remain outside the accepted 40 denominator while preserving them as real future research doors. This audit should be fair-adversarial: reject count drift, leakage, or lazy source claims, but do not punish the route for being exploratory, creative, or outside current GTOS/OB framing.

## Mandatory Preflight And Context

Run `python scripts/generate_live_state.py`; read `.context/LIVE_STATE.md`, `.context/00_core/goal_session_research_discipline.md`, `.context/00_core/research_operating_doctrine.md`, `.context/00_core/research_current_state.md`, `.context/00_core/local_heavy_data_inventory.md`, the R4 controlling prompt, and all R4 artifacts from disk. Do not rely on chat memory, pasted summaries, or prior beliefs about which edges are likely.

## Audit Requirements

- Recompute candidate counts: original 8, G0-discovered 4, R4-discovered 12, total 24, accepted-denominator overlap 0.
- Verify every candidate has `accepted_40_card_denominator_inclusion=false`, no result labels, and no mutation of the accepted 40. The accepted 40 is a floor, not a ceiling.
- Verify source-field designs, acceptance/rejection criteria, denominator quarantine proof, negative evidence, route ranking, and saturation self-red-team are disk-backed rather than narrative-only.
- Verify novelty and anti-boxing: the route must preserve non-OB framing, current-symbol expansion, local-heavy-data roots, source gaps, negative-evidence/failure-anatomy lanes, and route families that could open new sciences later.
- Verify searched-root claims include current worktree, accepted artifacts, absolute local-heavy roots, Sierra/proxy/source ledgers where applicable, prior worktrees, and explicit no-raw-blob policy.
- Run the route verifier and focused tests or stronger equivalents. If environment friction appears, separate it from artifact failure.

## Required G12 Outputs

Emit a scoped G12 audit route with decision ledger, candidate-count audit, source-field design audit, denominator quarantine audit, novelty/anti-boxing audit, source-search audit, negative-evidence audit, blocker/follow-up ledger, completion audit, verifier, focused tests, and next G0/source-packet prompt only if accepted.

Hard boundaries: no validation/results/R/PnL/win-rate/expectancy/performance/promotion/AI/API/paid-vendor/broker-account-order-history-deal-position/raw-market-blob/live-restart/live-behavior/trading-risk-safety-prompt-decision changes.

Safe flags must remain: `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.
