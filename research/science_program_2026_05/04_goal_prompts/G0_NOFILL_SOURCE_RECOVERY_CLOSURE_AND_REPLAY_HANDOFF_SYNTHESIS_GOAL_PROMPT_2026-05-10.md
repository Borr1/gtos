# G0 NOFILL Source Recovery Closure And Replay Handoff Synthesis Goal Prompt

Date: 2026-05-10
Owner lane: G0 source/control synthesis and next-route selection
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Goal

Build `G0_NOFILL_SOURCE_RECOVERY_CLOSURE_AND_REPLAY_HANDOFF_SYNTHESIS`.

The purpose is to close the completed NOFILL source-recovery detour and route the research back to broader source expansion/replay infrastructure. Do not keep `OWNER-TICK-0020` and `OWNER-TICK-0021` as an open-ended blocker loop. The accepted G12 Sierra audit says the evidence-class answer is definitive: Sierra SCID is same-market context only; MT5-native bid/ask/flags remain open only if a future route specifically needs them.

Synthesize the full accepted chain:

- `NOFILL_HISTORICAL_SOURCE_EXPANSION_BUILDER_LOCAL_TICK_SHADOW_PACKET`
- `G12_NOFILL_HISTORICAL_SOURCE_EXPANSION_PACKET_AUDIT`
- `NOFILL_HISTORICAL_SOURCE_EXPANSION_PACKET_PARSER_HASH_REPAIR_REBUILD`
- `G12_NOFILL_HISTORICAL_SOURCE_EXPANSION_HASH_REPAIR_REAUDIT`
- `G0_NOFILL_HISTORICAL_SOURCE_EXPANSION_PACKET_SYNTHESIS_CONTROL_REVIEW`
- `NOFILL_SOURCE_STATE_CAPTURE_GAP_CLOSURE_AND_TICK_EXPORT_MANIFEST_ROUTE`
- `G12_NOFILL_SOURCE_STATE_GAP_CLOSURE_AND_TICK_EXPORT_MANIFEST_AUDIT`
- `NOFILL_READONLY_TICK_RECOVERY_EXPORT_SOURCE_CONTROL_ROUTE`
- `G12_NOFILL_READONLY_TICK_RECOVERY_EXPORT_SOURCE_CONTROL_AUDIT`
- `XAUUSD_2026_04_15_16_SIERRA_SCID_ALTERNATE_SOURCE_CONTROL_ROUTE`
- `G12_XAUUSD_2026_04_15_16_SIERRA_SCID_ALTERNATE_SOURCE_CONTROL_AUDIT`

The output must be a concrete next-route decision, not a passive summary. It should define what is now closed, what is still source-state-impossible historically, what can be used as context only, what can enter future no-API replay/source-expansion work, and what exact route should run next.

## Mandatory Preflight

1. Run `python scripts\generate_live_state.py`.
2. Read `.context\LIVE_STATE.md`.
3. Read the latest numbered `.context\02_session_handoffs\*`.
4. Read `.context\00_core\quick_reference_card.md`.
5. Read `.context\00_core\research_operating_doctrine.md`.
6. Read `.context\00_core\goal_session_research_discipline.md`.
7. Read `.context\00_core\local_heavy_data_inventory.md`.
8. Read `.context\00_core\ai_in_loop_cost_control_research_plan.md`.
9. Read `.context\00_core\research_current_state.md`.
10. Read the accepted artifacts for every route listed in the Goal section.

## Required Synthesis

- Reconcile the final source-control counts across the chain: admitted source-bound rows, original blockers, rejects, tick/export-dependent rows, recovered MT5 tick windows, remaining MT5-native requests, SCID context-only rows, contamination/embargo exclusions, and non-generatable historical GTOS source-state gaps.
- Prove that no route opened validation execution, result scoring, broker actual-R, MT5 account/order/history/deal/position values, hidden result labels, promotion, registry edit, paid/API/Databento route, remote push, live restart, prompt/config/risk/permissions/safety/selector/canary change, credential touch, or live trading behavior.
- Produce a source-status closure ledger with final statuses for:
  - recovered MT5 tick source evidence,
  - same-market Sierra SCID context evidence,
  - exact MT5-native bid/ask/flags fallback requests,
  - contamination/embargo exclusions,
  - non-generatable historical GTOS source-state requirements,
  - forward-capture-only requirements,
  - replay/source-expansion-eligible context.
- Decide whether any source-control repair remains necessary before broader replay/source expansion. If yes, write exact repair prompt(s). If no, explicitly close the recovery detour.
- Rank at least three next-route options, including:
  - a no-API historical replay/missed-opportunity inventory route,
  - a source-expansion packet V2/rebuild route using recovered/context evidence without violating source-state boundaries,
  - a forward-source-capture/readiness route for non-generatable GTOS intent/lifecycle truth.
- Select the rank-1 next route and write a full controlling prompt file plus one-line starter.
- Preserve the owner's methodology: aggressive historical replay and source use, no passive waiting, no "n too small" excuse when broader source-safe data can be used, strict truthfulness, and no fake backfill of source-state truth.

## Required Artifacts

Write a route directory under:

`research\science_program_2026_05\06_outcome_testing\g0_nofill_source_recovery_closure_and_replay_handoff_synthesis\`

Include at minimum:

- context anchor JSON/MD,
- source-chain reconciliation ledger,
- final source-status closure ledger,
- two-date closure memo,
- replay/source-expansion readiness synthesis,
- next-route ranking ledger,
- full rank-1 next controlling prompt file under `research\science_program_2026_05\04_goal_prompts\`,
- one-line starter artifact,
- no-leak/safety boundary audit,
- completion audit,
- builder, verifier, and focused tests.

## Hardening Requirements

This G0 route should be decisive. Do not re-litigate the two XAUUSD dates unless an upstream artifact contradicts the accepted G12 audit. Do not let manual MT5 export fallback block broader replay/source work. Do not drift into validation/result scoring. Do not box the research into NOFILL only; the rank-1 route may be NOFILL-specific only if it is genuinely the strongest next step toward broad historical replay and edge discovery.

If a next route needs more data, it must specify how to get it from local roots, Sierra, MT5 read-only extraction, prior worktrees, ignored heavy-data roots, or future forward capture. If a source-state fact is non-generatable historically, state it truthfully and route to forward capture or projection-only use; do not fake it.

## Completion Standard

Mark complete only when the chain is reconciled, the two-date recovery detour is closed for this evidence class, final statuses are explicit, no-leak/safety boundaries are preserved, the next route is ranked and selected with a full prompt and one-line starter, verifier/tests pass, and the completion audit records `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.
