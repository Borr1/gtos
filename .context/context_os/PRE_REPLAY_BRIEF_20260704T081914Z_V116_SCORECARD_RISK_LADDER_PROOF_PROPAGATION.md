# Pre-Replay Brief: V116 Scorecard Risk-Ladder Proof Propagation

Generated: 2026-07-04T08:19:14Z

## Current Completed Replay

- Prefix: `BROAD_LIVE_AS_IF_REPLAY_V115_B3_B5_PROOF_PRECISION_20260603_REPAIRED_ONLY_COMPACT_FULLGRID_SKIPTICK`
- Window: 2026-06-03..2026-06-03
- Profile: `repaired_package_conversion_v3`
- Status: `broad_live_as_if_replay_materialized_broker_live_closed`
- Candidate rows: 6,603
- Scorecard rows: 96
- Order rows: 56 summary/order events
- Trades: 12
- Net R: -2.30082618
- Gross R / final R: -1.15118996 / -1.15118996
- Cash PnL: -230.28228129
- Risk cash / risk pct: 1200.53417139 / 1.2
- W/L/F: 3/9/0
- Filled / expired unfilled: 12 / 16
- Risk decisions: 28 `open-reduced-risk`

This is a one-day repair proof slice. It does not prove total reservoir conversion.

## Active Process State

No broad replay, pytest, py_compile, or stale Git helper is currently active. `scripts/generate_live_state.py` completed and wrote `.context/LIVE_STATE.md`; Context OS catalog and pack were refreshed.

## Baseline Comparison

- V89D hostile 5d 2026-05-13..17: 56 trades, +34.84520454R.
- V90 hostile 5d 2026-05-13..17: 51 trades, +28.84201157R.
- V92 hostile 5d 2026-05-13..17: 51 trades, +29.35570236R; same-window source-bound R 218,870.181480028; candidate axes 894; scorecard/order axes 39; filled axes 25.
- V110B broad 19d 2026-06-01..19: 95 trades, +22.80442652R; same-window source-bound R 342,126.925564897; candidate axes 944; scorecard/order axes 34; filled axes 33.
- V111 broad 19d 2026-06-01..19: 45 trades, -4.19333138R; disjoint replacement versus V110B.
- V115 vs V114C one-day: added trades 0, removed trades 0, net R delta 0.0; scorecard lost ladder/effective-action proof while order/trade rows carried `reduced`.

## Dirty Code / Active Changes

- `scripts/generate_live_state.py`: bounded source grep hygiene.
- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`: scheduler-side risk-expression ladder.
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`: risk ladder propagation, selected scorecard/primary probe proof propagation, effective selector action propagation.
- Route verifier/comparator/parity/bridge files under `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/`.
- Focused tests in `tests/test_v4_timewarp_simulated_live_research_loop.py`, `tests/test_moonshot_scheduler_v4_best_trade_allocator.py`, `tests/test_denominator_to_deployment_verifier.py`, and `tests/test_build_source_bound_execution_parity.py`.

## Subagent Findings

- Socrates: deferred to B4. Fill-realism issues remain open: source-time partial, passive first-touch optimism, missing `fill_realism_class`, M15 proxy split, same-bar conservative close.
- Feynman: incorporated. Verifier/comparator/parity/bridge precision gaps patched and tested.
- Lorentz: incorporated with open proof gap. B3 code existed but scorecard proof propagation was missing; V116 targets that gap.
- Parfit/Ampere/Huygens: reconciled before V115; no active blocker in this V116 batch.

## Mismatch Classes

- Source-bound -> candidate: partially fixed; full same-window reservoir conversion remains open.
- Candidate -> selector: partially fixed; raw/effective split exists, but V115 scorecard no-selected rows lost effective action.
- Selector -> scheduler: partially fixed; B2 fill-floor/reallocation remains open.
- Scheduler -> risk: partially fixed; ladder exists in scheduler/risk/order/trade, but V115 scorecard rows were blank.
- Risk -> order: partially fixed; REFUSED/source-gap rows remain non-executable and scoreable/missed.
- Order -> lifecycle -> fill: open; B4 fill realism and B2 fallback/reallocation/expiry remain next.
- Fill -> exit: open; do not tune exit from this one-day proof unless a truth violation appears.
- Ledger/verifier: partially fixed; V116 closes scorecard proof propagation.

## Patch Batch

Highest-leverage same-root batch: scorecard risk-ladder and effective selector proof propagation.

Files affected:

- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `tests/test_v4_timewarp_simulated_live_research_loop.py`

Patch type:

- Correctness repair: primary-probe, selected scheduler option, and pre-risk selected option now preserve `selector_action_origin`, `effective_selector_action`, and `risk_expression_ladder*`.
- Diagnostic/ledger repair: no-selected scorecards report primary-probe ladder/action truth under `scorecard_reported_*` while keeping `executable_finalized=false`.
- Performance repair: none expected in this batch.

## Expected Before Replay

- Candidate -> scorecard transfer: unchanged count, but scorecard rows should gain selected or `scorecard_reported_*` risk ladder/effective selector fields.
- Scorecard -> order transfer: unchanged.
- Order -> fill transfer: unchanged.
- Missed positive R: unchanged.
- Missed negative R: unchanged.
- Trade count: unchanged at 12 if behavior-neutral.
- Net/gross/final R: unchanged at -2.30082618 / -1.15118996 / -1.15118996 if behavior-neutral.
- W/L/F: unchanged at 3/9/0 if behavior-neutral.
- Cost-refused/source-gap execution: must remain zero.
- Risk-reduced/full-risk distribution: trade rows likely remain 12 reduced / 0 full; scorecard must expose reduced/diagnostic/no-selected reasons instead of blank fields.

## Proof Criteria

Helped:

- V116 one-day rerun has same or explainably equivalent behavior to V115.
- Scorecard selected rows have top-level ladder/action fields.
- Scorecard no-selected rows have `scorecard_reported_risk_expression_ladder*` and `scorecard_reported_effective_selector_action`.
- Order/trade rows still have zero executed REFUSED/source-gap rows.
- Full-risk verifier fatal remains active if any false full-risk row appears.

Failed:

- Scorecard rows still have blank ladder/effective-action proof for all 96 rows.
- Raw blocking selector action becomes executable without signed materialization.
- REFUSED/source-gap rows execute.
- Trade set changes without a causal code reason from this projection-only patch.

Next if helped: do not broaden yet for a proof-only patch. Move to B4 fill-simulation realism and B2 fillability/reallocation with targeted replay before hostile 5d / non-May regimes.
