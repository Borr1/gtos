# V98 Pre-Replay Brief - Source-Bound Router-Refusal Floor Repair

Generated: 2026-07-03T08:22:37Z

## Current Completed Replays

- V92 hostile fullgrid baseline: `BROAD_LIVE_AS_IF_REPLAY_LIFECYCLE_TRUTH_ADAPTIVE_AXIS_REPAIR_V92_20260513_20260517_REPAIRED_ONLY_COMPACT_FULLGRID`
  - trades 51; net R 29.35570236; gross/final R 33.93212860; cash PnL 6228.63096022; W/L/F 37/14/0; expired unfilled 62.
  - source-bound R in selected window 218870.181480028; package axes 1101; candidate axes 894; scorecard/order axes 39; order-present 82; filled axes 25; exact executable R 17.76833767.
- V97 hostile fullgrid comparator: `BROAD_LIVE_AS_IF_REPLAY_DYNAMIC_SCOPE_REPAIR_V97_SEMANTICS_20260513_20260517_REPAIRED_ONLY_COMPACT_FULLGRID`
  - trades 47; net R 13.89627731; gross/final R 18.23890670; cash PnL 4461.09800786; W/L/F 23/24/0; expired unfilled 51.
  - source-bound R in selected window 222423.262022048; package axes 1101; candidate axes 894; scorecard/order axes 29; order-present 69; filled axes 18; exact executable R 13.48984606.
- V97 non-May objective bucket: `BROAD_LIVE_AS_IF_REPLAY_DYNAMIC_SCOPE_REPAIR_V97_SEMANTICS_20260601_20260605_REPAIRED_ONLY_COMPACT_FULLGRID`
  - trades 62; net R 2.21033496; gross/final R 7.10115419; cash PnL 1181.09009638; W/L/F 28/34/0; expired unfilled 68.
  - source-bound R in selected window 260850.564292173; package axes 1101; candidate axes 894; scorecard/order axes 38; order-present 94; filled axes 24; exact executable R -4.66956856.

## Current Process State

No broad replay is running. Stale long-running `git diff --numstat` helper processes were terminated before this brief.

## Baseline Comparison

- V89D/V90 are historical reference points for the same route family and remain comparator-only until same-window artifacts are parsed from disk for this checkpoint.
- V92 is the current same-window hostile baseline for 2026-05-13..2026-05-17.
- V97 regressed against V92 by -4 trades, -15.45942505 net R, -14 wins, +10 losses, -13 order-present axes, -7 filled axes, and -4.27849161 exact executable R.
- V97 added 19 trades for +0.99594545 net R and removed 23 V92 trades for +13.53876156 net R. Added transfers were weakly net positive, but removed transfers were strongly positive, so the regression is not positive-by-suppression; it is a source-bound authority/materialization contract mismatch.

## Active Code Changes

- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_selected_package_replay_bridge.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/build_source_bound_execution_parity.py`
- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`
- focused tests in:
  - `tests/test_v4_timewarp_simulated_live_research_loop.py`
  - `tests/test_broad_replay_repair_config.py`
  - `tests/test_build_source_bound_execution_parity.py`
  - `tests/test_moonshot_scheduler_v4_best_trade_allocator.py`

## Subagent Findings

- Lovelace the 2nd: incorporated. Identified scheduler materialization and signed source-bound router-refusal authority as a likely V97/V92 transfer gap.
- Avicenna the 2nd: incorporated. Proved V97 added weak trades while removing stronger V92 winners; the removed winners were mostly rejected by expected-net floor/signed authority, same-symbol lifecycle, daily drawdown absence, or competing-candidate effects.
- Plato the 2nd: incorporated. Proved the dominant current loss is not an active profit-harvest overlay; exit/profit harvest remains a later repair lane after materialization/admission is corrected.

## Mismatch Classes

- source-bound -> candidate: fixed enough for this slice; axes remain 894 candidate axes in both V92 and V97.
- candidate -> selector: partially fixed; source-bound router-refusal rows are materialized with route-harness floors, not strict positive-predecision floors.
- selector -> scheduler: partially fixed; router-refusal family no longer grants broad off-configured immediate-marketable authority without explicit off-session or router immediate authority.
- scheduler -> risk: open; V97 removed some valid V92 winners through finalizer and competing-candidate effects, to measure after this patch.
- risk -> order -> lifecycle -> fill: open; off-configured marketable route and lifecycle veto effects must be measured after this patch.
- fill -> exit: open, but not the first patch. Current evidence says stop-first losses are not caused by active profit-harvest headline authority.
- ledger: fixed for this checkpoint where bridge/parity/runtime floor semantics now agree.

## Patch Batch

Highest-leverage same-root batch: router-refusal authority contract alignment.

- Correctness repairs:
  - Split source-bound replay materialization floors from true positive-predecision router-refusal floors in runtime, selected bridge, and parity verifier code.
  - Keep broker-cost REFUSED/source-gap rows non-executable; this patch does not bypass cost authority.
  - Remove generic `router_refusal_softening` from off-configured immediate-marketable route-family authority so route session cannot be borrowed without explicit authority.
- Diagnostic/ledger repairs:
  - Focused tests prove source-bound rows use source-bound floors while positive-predecision rows keep strict floors.
- Performance repair:
  - Expected to restore valid signed source-bound router-refusal opportunities that V97 lost to strict floor drift, especially V92 removed winners with cost PASSED and source-bound cost authority present.

## Expected Measurable Effect

- candidate -> scorecard transfer: unchanged or modestly improved; no full-package narrowing.
- scorecard -> order transfer: should recover order-present axes for rows previously blocked by `router_refusal_expected_net_r_below_floor`.
- order -> fill transfer: should increase fills for valid signed source-bound rows if no later lifecycle/risk veto remains.
- missed positive R: should decrease for signed source-bound router-refusal rows.
- missed negative R: may also decrease; if recovered negative transfer exceeds recovered positive transfer, the patch exposes selector/ranking quality as the next deeper flaw.
- trade count: likely increases versus V97, but should not execute broker-cost REFUSED or source-gap rows.
- net/gross/final R and W/L/F: helped if recovered removed winners outweigh new recovered losers; failed if recovered rows are net negative; exposed deeper flaw if transfer rises but R falls.
- cost-refused/source-gap execution: must remain zero.
- risk-reduced/full-risk distribution: source-bound router-refusal rows remain reduced-risk authority, not full-risk live authority.

## Replay Criteria

Run targeted hostile fullgrid V98 first for 2026-05-13..2026-05-17. This smoke proves or disproves the local repair; it does not prove total reservoir conversion.

- Helped: order-present axes and filled axes increase versus V97, removed V92 winners are recovered, and added transfer is net positive without REFUSED/source-gap execution.
- Failed: recovered rows are net negative or the two known V92 winner rows remain missed for the same floor reason.
- Exposed next flaw: known rows pass authority floors but are lost later to scheduler/risk/lifecycle/order/fillability; next repair should patch that downstream class, not retune floors.
