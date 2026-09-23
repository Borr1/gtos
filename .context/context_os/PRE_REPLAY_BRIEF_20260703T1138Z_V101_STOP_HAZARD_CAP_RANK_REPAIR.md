# V101 Pre-Replay Brief - Stop-Hazard Cap Rank Repair

Generated: 2026-07-03T11:38Z

## Current Latest Completed Replays

- V100 hostile `BROAD_LIVE_AS_IF_REPLAY_PASSIVE_FALLBACK_DISPLACEMENT_REPAIR_V100_20260513_20260517`: 52 trades, +24.50126904 net R, +29.33465208 gross/final R, +6060.02005521 cash PnL, W/L/F 29/23/0, 11 expired unfilled.
- V100 non-May `BROAD_LIVE_AS_IF_REPLAY_PASSIVE_FALLBACK_DISPLACEMENT_REPAIR_V100_20260601_20260605`: 67 trades, +3.79682093 net R, +8.60745638 gross/final R, +1067.37003037 cash PnL, W/L/F 30/37/0, 26 expired unfilled.
- V100 non-May selected-window denominator: source-bound R 426601.3938625386R, package axes 1101, candidate-generated axes 894, scorecard/order axes 34, order-present count 78, filled-trade axes 29, actual executable R +0.90475251, final executable R +4.783134537.
- This smoke proves or disproves the local repair; it does not prove total reservoir conversion.

## Running Process State

- No broad replay, parity builder, comparator, pytest, or py_compile process is running.
- A Chronicle memory helper is the only Python process matching a broad process scan.

## Baseline Comparison

- V97 non-May: 62 trades, +2.21033496 net R, +7.10115419 gross/final R, W/L/F 28/34/0, 68 expired unfilled.
- V98 non-May: 48 trades, +4.65521903 net R, +8.38946808 gross/final R, W/L/F 23/25/0, 8 expired unfilled.
- V100 non-May versus V97: +5 trades, +1.58648597 net R, +1.50630219 final R, W/L delta +2/+3/0, expired -42. Added trades +2.24464332R; removed trades +0.65815735R.
- V100 non-May versus V98: +19 trades, -0.85839810 net R, +0.21798830 final R, W/L delta +7/+12/0, expired +18. Added trades +1.08080190R; removed trades +1.93920000R. V100 added net-positive trades but added too many stop losses and removed one V98 winner.
- V100 hostile versus V98: +8 trades, +6.40692321 net R, +7.07278081 final R. V100 hostile improved the passive-fallback displacement class.
- V100 hostile versus V92: +1 trade, -4.85443332 net R, -4.59747652 final R. V100 still trails V92 because removed V92 positives exceed added transfers.

## Dirty Files And Active Code Changes

- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`: stop-hazard cap rows now carry `predecision_stop_hazard_score_penalty` and capped rows apply that score penalty during ranking.
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py`: repaired profile stop-hazard score penalty raised from 0.20 to 1.25.
- `tests/test_moonshot_scheduler_v4_best_trade_allocator.py`: focused tests assert capped stop-hazard rows receive a negative score component and wide geometry remains unpenalized.
- `tests/test_broad_replay_repair_config.py`: repaired profile config test asserts the stronger stop-hazard penalty.

## Subagent Findings Incorporated

- Huygens: incorporated. Stop losses are the broad residual: V100 hostile stops 17 rows for -18.57882448R and V100 non-May stops 30 rows for -32.14113976R. The stop rows are not separated by expected_net/probability/fillability alone.
- Linnaeus: incorporated but deferred. Same-symbol replacement rewrite is real, but current hostile priced leak is +2.13476983R, smaller than stop residual unless non-May later proves it broader.
- Russell: incorporated. V100 non-May completed comparison/parity parse and showed V100 beats V97 but loses to V98.

## Root Mismatch Map

- source-bound -> candidate: stable at 894/1101 axes; not the current choke.
- candidate -> selector/scheduler: partially fixed. V100 non-May scorecard/order axes rose from V98 33 to V100 34 and order-present count from 59 to 78, but added transfer quality is weak.
- scheduler -> risk/finalizer: current stop-hazard cap semantics were miswired. Hazard rows were marked `capped`, but only `penalized` status consumed score penalty, so high-risk geometry kept normal ranking.
- risk -> order/fillability: broker-cost REFUSED/source-gap execution remains zero in completed runs.
- order -> lifecycle/fill: same-symbol replacement remains open, but not next by current cross-window impact.
- fill -> exit: stop-first path remains the largest residual loss bucket.
- ledger: stop-hazard fields are already propagated; this patch changes semantics, not ledger surface.

## Patch Batch

Files/components:

- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`: correctness/performance repair. Capped stop-hazard rows now have a score penalty and capped/penalized statuses both subtract it from scheduler score.
- `run_broad_live_as_if_replay_harness.py`: performance repair under repaired profile. Score penalty 1.25 gives all-threshold hazard rows meaningful rank demotion.
- Tests: correctness guardrails for cap score penalty and config propagation.

This is not a hardcoded symbol/date/session bucket. It uses only predecision geometry: unit-risk ATR, distance-to-limit risk, limit-fill probability, action intent, and existing guard thresholds.

## Expected Measurable Effect

- Candidate -> scorecard should remain 35191 candidate rows and 480 scorecards on non-May.
- Scorecard -> order transfer may fall or reshuffle if all-threshold hazard rows lose rank; this is acceptable only if added/removed transfer improves.
- Order -> fill transfer may fall from 67 if weak all-threshold hazards are displaced; it should not collapse.
- Missed positive R may increase if a capped hazard winner is skipped, but completed V100 evidence found all all-threshold hazard fills were losers in both hostile and non-May windows.
- Missed negative R should not improve solely by suppressing all trades; trade churn and close-reason distribution must show whether better candidates replaced hazards.
- Trade count may drop modestly or change composition.
- Net/gross/final R should improve versus V100 and preferably recover above V98 non-May.
- W/L/F should reduce stop losses more than it reduces targets.
- Cost REFUSED/source-gap executed counts must remain zero.
- Risk-reduced/full-risk provenance should remain preserved.

## Success And Failure Criteria

- Helped: V101 non-May beats V100 and V98 on net R or materially reduces stop losses while preserving target/time-stop positive transfer. Added-minus-removed transfer should be positive.
- Failed: V101 loses more than V100 because rank demotion removes positive target/time-stop rows or does not displace any stop rows.
- Exposes next flaw: if all-threshold hazards move but two-condition stop-first rows dominate while two-condition target rows remain strong, the next repair must be a richer predecision stop-hazard model rather than broader threshold gating.
