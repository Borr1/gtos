# Pre-Replay Brief - 2026-07-04T14:12Z - V119 Hostile 5D

Scope: `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20`.

Broker/live/final remain closed: `live_broker_authority=false`, `broker_mutation_enabled=false`, `final_selection_claim=false`. Local replay/package evaluation keeps full 82-sleeve authority.

Saved plan authority:

- `.context/context_os/ultimate_system_plan/IMPLEMENTATION_SEQUENCE_ULTIMATE_SYSTEM_FLOW_20260704.md`
- `.context/context_os/ultimate_system_plan/FABLE_ROOT_CAUSE_AUDIT_AND_IMPLEMENTATION_PLAN_20260704.md`

## Current Latest Completed Run

`BROAD_LIVE_AS_IF_REPLAY_V118E_SCORECARD_REPORTED_AUTHORITY_BACKFILL_20260513_REPAIRED_ONLY_COMPACT_FULLGRID`

- window: `2026-05-13..2026-05-13`
- profile: `repaired_package_conversion_v3`
- status: `broad_live_as_if_replay_zero_candidates_no_terminal_execution_broker_live_closed`
- scorecard rows: `96`
- compact candidate rows: `0`
- missed rows: `1202`
- order/trade rows: `0 / 0`
- package authority valid true/false: `45 / 51`
- order-executable true/false: `23 / 73`
- order-executable authority source present: `96 / 96`
- missed +R / -R / net: `64.67405875 / -741.87417482 / -677.20011607`
- cost-refused missed rows: `1094`
- false order-executable terminal rows: `0`

This is a one-day truth proof only. It proves the authority/proof fields needed for the next behavior run; it does not prove full-reservoir transfer.

## Active Process State

No broad replay or pytest process was active immediately before this brief. If a V119 process appears before launch, parse it instead of duplicating it.

## Baseline Anchors

- V92 hostile five-day: `51 trades`, `+29.35570236R`.
- V106 hostile five-day: `83 trades`, `+32.57834226R`, `288` scorecards, `91` order rows, `185` order events.
- V117 hostile five-day: `1 trade`, `-1.10389662R`, `288` scorecards, `3` order rows, `6` order events.
- V118E one-day: `0 trades`, `0.0R`, scorecard proof fields complete.
- V110B broad 19-day: `95 trades`, `+22.80442652R`.
- V111 broad 19-day: `45 trades`, `-4.19333138R`.

Compare V119 only same-window against hostile five-day anchors. Do not compare a five-day run directly to the global million-R reservoir.

## Dirty Files And Active Code Changes

Scoped active route/code files:

- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/verify_denominator_to_deployment_execution.py`
- `tests/test_v4_timewarp_simulated_live_research_loop.py`
- `tests/test_moonshot_scheduler_v4_best_trade_allocator.py`
- `tests/test_denominator_to_deployment_verifier.py`

Latest proof change: `scorecard_probe_quality_backfill_fields` now emits `scorecard_reported_*` fields from finalizer probe sources even when stale top-level helper fields are already present.

## Subagent Findings Status

- Avicenna: incorporated for raw/effective selector provenance and risk ladder raw action.
- Planck: incorporated partially for passive queue route and tier-demotion context; fallback-expiry clamp and terminal-veto regression remain open.
- Pascal: incorporated for order-executable split, false order-exec materialization block, missed attribution, and verifier source coverage.
- Rawls: incorporated for scorecard/finalizer package-authority propagation.
- Hegel: incorporated for false order-executable fatal handling and tests.
- Gibbs/Archimedes: unavailable after continuation; no findings are claimed.

## Known Mismatch Classes

- source-bound -> candidate: partially fixed; V119 must report same-window transfer.
- candidate -> selector: partially fixed; raw/effective action split exists, open-reduced/reject dominance remains.
- selector -> scheduler: partially fixed; V118E exposes signed/invalid and order-executable/non-executable package proof.
- scheduler -> risk: open; V118E had 23 order-executable scorecard probes and zero orders.
- risk -> order: open; false order-executable rows are non-terminal, valid rows need five-day proof.
- order -> lifecycle -> fill: open; V117 had only 3 orders and 1 fill.
- fill -> exit: open; V117 single fill lost `-1.10389662R`.
- ledger/verifier: partially fixed; focused compile and pytest authority/provenance/fillability slice are green.

## Next Run

Run:

`BROAD_LIVE_AS_IF_REPLAY_V119_ORDER_EXEC_AUTHORITY_SPLIT_20260513_20260517_REPAIRED_ONLY_COMPACT_FULLGRID`

Window: `2026-05-13..2026-05-17`.

Profile: `repaired_package_conversion_v3`.

Purpose: hostile five-day behavior transfer proof after V118E truth contract passed.

## Expected Measurement

- candidate -> scorecard -> order -> fill axes;
- valid/invalid package authority counts;
- order-executable true/false and source coverage;
- order/trade count;
- net/gross/final R and cash PnL if trades occur;
- W/L/F if trades occur;
- missed positive and missed negative R by reason;
- cost-refused/source-gap execution count, expected `0`;
- full-risk vs reduced-risk distribution if trades occur;
- expired/unfilled and lifecycle/fillability blocker buckets.

## Success / Failure Criteria

V119 helped if authority truth remains complete, false-order-executable terminal rows remain zero, and five-day artifacts explain valid-probe-to-order/fill transfer or exact predecision blockers.

V119 failed if source/authority fields regress, broker-cost-refused/source-gap/false-order-exec rows execute, or valid order-executable probes stay non-terminal without exact blocker attribution.

If V119 is clean but weak or negative, the next batch must target the largest V119 bucket: scheduler/risk reallocation, passive limit fillability/lifecycle expiry, or exit/stop geometry. Do not return to one-day tuning unless V119 exposes a hard truth/verifier violation.
