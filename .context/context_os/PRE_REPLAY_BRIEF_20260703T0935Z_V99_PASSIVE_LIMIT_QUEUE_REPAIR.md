# V99 Pre-Replay Brief - Passive-Limit Queue/Fallback Envelope Split

Generated: 2026-07-03T09:35Z

## Current Completed Replays

- V92 hostile baseline `BROAD_LIVE_AS_IF_REPLAY_LIFECYCLE_TRUTH_ADAPTIVE_AXIS_REPAIR_V92_20260513_20260517_REPAIRED_ONLY_COMPACT_FULLGRID`: 51 trades, +29.35570236 net R, +33.93212860 gross/final R, 6228.63096022 cash PnL, W/L/F 37/14/0, 62 expired unfilled.
- V97 hostile comparator `BROAD_LIVE_AS_IF_REPLAY_DYNAMIC_SCOPE_REPAIR_V97_SEMANTICS_20260513_20260517_REPAIRED_ONLY_COMPACT_FULLGRID`: 47 trades, +13.89627731 net R, +18.23890670 gross/final R, 4461.09800786 cash PnL, W/L/F 23/24/0, 51 expired unfilled.
- V98 hostile router-floor repair `BROAD_LIVE_AS_IF_REPLAY_SOURCE_BOUND_ROUTER_FLOOR_REPAIR_V98_20260513_20260517_REPAIRED_ONLY_COMPACT_FULLGRID_SKIPTICK`: 44 trades, +18.09434583 net R, +22.26187127 gross/final R, 4705.69493624 cash PnL, W/L/F 23/21/0, 6 expired unfilled. V98 improved V97 by +4.19806852 net R, but remains -11.26135653 net R below V92.
- V97 non-May objective bucket `BROAD_LIVE_AS_IF_REPLAY_DYNAMIC_SCOPE_REPAIR_V97_SEMANTICS_20260601_20260605_REPAIRED_ONLY_COMPACT_FULLGRID`: 62 trades, +2.21033496 net R, +7.10115419 gross/final R, 1181.09009638 cash PnL, W/L/F 28/34/0, 68 expired unfilled.
- V98 non-May router-floor repair `BROAD_LIVE_AS_IF_REPLAY_SOURCE_BOUND_ROUTER_FLOOR_REPAIR_V98_20260601_20260605_REPAIRED_ONLY_COMPACT_FULLGRID_SKIPTICK`: 48 trades, +4.65521903 net R, +8.38946808 gross/final R, 1399.78369321 cash PnL, W/L/F 23/25/0, 8 expired unfilled. V98 improved V97 by +2.44488407 net R; added transfers +4.34552531R, removed transfers +1.90064124R.

## Selected-Window Denominators

- V97 hostile: source-bound R 222423.262022048; package axes 1101; candidate axes 894; scorecard/order axes 29; order-present count 69; filled axes 18; actual executable R +13.48984606.
- V98 hostile: source-bound R 422103.4001250788; package axes 1101; candidate axes 894; scorecard/order axes 27; order-present count 45; filled axes 25; actual executable R +17.16997641. Caveat: V98 hostile used skip-tick and physical candidate ledger; trade/order behavior is valid, denominator percentages are not directly comparable to V92/V97.
- V97 non-May: source-bound R 260850.564292173; package axes 1101; candidate axes 894; scorecard/order axes 38; order-present count 94; filled axes 24; actual executable R -4.66956856.
- V98 non-May: source-bound R 426601.3938625386; package axes 1101; candidate axes 894; scorecard/order axes 33; order-present count 59; filled axes 28; actual executable R +1.14486888.

## Subagent Findings Incorporated

- Ampere: incorporated. Route harness already enables same-decision extra slots and lifecycle scale-in gates in repaired profile; V97/V98 reallocation policy is not disabled. Reallocation is mostly blocked by strict original-relative quality/composite gates.
- Leibniz: incorporated. V98 hostile still loses 21 V92-positive removed trades worth +20.05007299R. The largest same-root bucket is `passive_limit_fallback_envelope_distance_to_limit_risk_above_thesis_geometry_ceiling`: 11 rows, +14.78420233 V92 R.
- Wegener: incorporated. Non-May V97/V98 show the stable leak is scheduler/finalizer/action conversion, while June-specific damage is more stop-first structural-distance/lifecycle quality than order-cost authority.

## Patch Batch

Root: passive-limit fallback envelope conflated the original passive-limit queue with the guarded-market fallback leg. A source-bound, broker-cost-passed passive-limit order was blocked before order materialization when the guarded fallback distance-to-limit envelope failed, even though the passive queue itself remained the honest executable route.

Files changed:

- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`: allow fallback-only envelope failures to degrade to passive-limit queue instead of blocking materialization; keep quality/source/time/cost failures blocked; preserve new ledger fields.
- `tests/test_v4_timewarp_simulated_live_research_loop.py`: focused tests for passive queue release and quality-failure block.

Patch type: correctness repair with performance impact.

## Expected V99 Effect

- Candidate axes should remain near 894/1101; scorecard rows should stay 288.
- Hostile order rows/trades should rise only through passive-limit queue rows that are source-bound, broker-cost passed, package-executable, and risk admitted.
- `passive_limit_fallback_envelope_distance_to_limit_risk_above_thesis_geometry_ceiling` missed rows should fall.
- Added transfers should be net positive; if added rows are net negative, the patch exposes downstream fill/exit/selection quality rather than proving the passive queue repair bad.
- Cost-refused/source-gap execution must remain zero.
- This smoke proves or disproves the local repair; it does not prove total reservoir conversion.

