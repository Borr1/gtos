# V100 Non-May Regime Pre-Replay Brief

Generated: 2026-07-03T10:58Z

## Current Completed Replay Prefix And Numbers

- Latest completed hostile/stress replay: `BROAD_LIVE_AS_IF_REPLAY_PASSIVE_FALLBACK_DISPLACEMENT_REPAIR_V100_20260513_20260517`.
- V100 hostile result: 52 trades, +24.50126904 net R, +29.33465208 gross/final R, +6060.02005521 cash PnL, W/L/F 29/23/0, 11 expired unfilled.
- V100 hostile selected-window transfer: source-bound R available inside the exact window 422103.4001250788R, package axes 1101, candidate-generated axes 894, scorecard/order axes 31, order-present axes 55, filled-trade axes 28, actual executable R +22.56964469.
- This smoke proves or disproves the local repair; it does not prove total reservoir conversion.

## Running Replay State

- No broad replay, parity builder, or comparator process is currently running.
- A Chronicle memory helper was the only Python process matching the broad process scan.
- `scripts/generate_live_state.py` was intentionally stopped after it sat idle in source grep; it was not a replay and did not hold route artifacts.

## Baseline Comparison

- V92 hostile `BROAD_LIVE_AS_IF_REPLAY_LIFECYCLE_TRUTH_ADAPTIVE_AXIS_REPAIR_V92_20260513_20260517_REPAIRED_ONLY_COMPACT_FULLGRID`: 51 trades, +29.35570236 net R, +33.93212860 gross/final R, W/L/F 37/14/0, 62 expired unfilled.
- V97 hostile `BROAD_LIVE_AS_IF_REPLAY_DYNAMIC_SCOPE_REPAIR_V97_SEMANTICS_20260513_20260517_REPAIRED_ONLY_COMPACT_FULLGRID`: 47 trades, +13.89627731 net R, +18.23890670 gross/final R, W/L/F 23/24/0, 51 expired unfilled.
- V98 hostile `BROAD_LIVE_AS_IF_REPLAY_SOURCE_BOUND_ROUTER_FLOOR_REPAIR_V98_20260513_20260517_REPAIRED_ONLY_COMPACT_FULLGRID_SKIPTICK`: 44 trades, +18.09434583 net R, +22.26187127 gross/final R, W/L/F 23/21/0, 6 expired unfilled.
- V99 hostile `BROAD_LIVE_AS_IF_REPLAY_PASSIVE_LIMIT_QUEUE_REPAIR_V99_20260513_20260517_REPAIRED_ONLY_COMPACT_FULLGRID_SKIPTICK`: 45 trades, +13.25940200 net R, +17.37183705 gross/final R, W/L/F 22/23/0, 19 expired unfilled.
- V100 hostile versus V99: +7 trades, +11.24186704 net R, +11.96281503 final R, +7 wins, 0 added losses, expired -8. Added trades +15.30831330R; removed trades +4.06644626R. Improvement came from better scheduler/finalizer/passive fallback transfer, not all-trade suppression.
- V100 hostile versus V98: +8 trades, +6.40692321 net R, +7.07278081 final R. Added trades +5.71407682R; removed trades -0.69284639R.
- V100 hostile versus V92: +1 trade, -4.85443332 net R, -4.59747652 final R. Added trades +9.62044227R; removed trades +12.71501533R. V100 still trails V92 because it removed stronger V92 positives and added more losses.
- V97 non-May baseline `BROAD_LIVE_AS_IF_REPLAY_DYNAMIC_SCOPE_REPAIR_V97_SEMANTICS_20260601_20260605_REPAIRED_ONLY_COMPACT_FULLGRID`: 62 trades, +2.21033496 net R, +7.10115419 gross/final R, W/L/F 28/34/0, 68 expired unfilled.
- V98 non-May baseline `BROAD_LIVE_AS_IF_REPLAY_SOURCE_BOUND_ROUTER_FLOOR_REPAIR_V98_20260601_20260605_REPAIRED_ONLY_COMPACT_FULLGRID_SKIPTICK`: 48 trades, +4.65521903 net R, +8.38946808 gross/final R, W/L/F 23/25/0, 8 expired unfilled.

## Dirty Files And Active Changes

- Active code changes are in `src/research_infra/v4_timewarp_simulated_live_research_loop.py`, `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py`, and focused tests.
- Existing unrelated dirty context-os and old science-program deletions remain outside this replay checkpoint.
- Broker/live/final authority remains closed.

## Incorporated Subagent Findings

- Goodall: incorporated. V99 degraded passive fallback rows were valid opportunities but reserved scarce risk/same-symbol state before stronger transfers; V100 added transfer score floor and rank demotion instead of disabling the entire fallback.
- Ramanujan: incorporated. Finalizer rank fields now carry degraded fallback labels and rank penalties.
- Einstein: incorporated. V99 scorecard supply was intact; regression was materialization/ranking churn, not missing candidate evidence.
- Euclid: incorporated. V100 comparison/parity checklist was used to materialize V100 hostile comparisons and parity artifacts.
- Dirac: incorporated as next open patch class. Same-symbol/pending replacement can still turn valid original actions into `replace_pending` and then lifecycle-veto them when replacement authority is not proven.
- Godel: incorporated as next open patch class. Stop geometry remains a residual loss source independent of passive fallback displacement.

## Root Mismatch Classes

- source-bound -> candidate: candidate axis generation is stable at 894/1101 for the hostile and non-May baselines; not the current choke.
- candidate -> selector: scorecard supply remains 288 rows in hostile runs; not missing evidence, but downstream materialization can prefer weaker rows.
- selector -> scheduler: partially fixed by source-bound router floor and passive fallback transfer ranking.
- scheduler -> risk/finalizer: partially fixed; weak degraded passive fallback rows no longer get equal scarce-state priority when transfer evidence is weak.
- risk -> order/fillability: broker-cost REFUSED/source-gap rows remain non-executable; V100 hostile had zero executed REFUSED/source-gap rows.
- order -> lifecycle/fill: still open. Same-symbol replacement and pending lifecycle can hide valid winners behind `same_symbol_lifecycle_veto`.
- fill -> exit: still open. Stop geometry is the largest residual loss bucket in completed hostile artifacts.
- ledger: diagnostic fields now preserve degraded fallback transfer score/rank penalty; same-symbol nested replacement reasons still need better top-level attribution before any patch.

## Highest-Leverage Same-Root Batch Before Next Patch

No new policy patch before the non-May replay. The next action is a same-config objective-regime run using the V100 code path on `2026-06-01..2026-06-05`.

Rationale: V100 repaired the passive-fallback displacement class on the hostile bucket and improved V99/V98, but it still trails V92. Before tuning same-symbol or stop geometry from the May 13-17 hostile window, the same V100 config must be tested outside that stress bucket.

## Components Affected By This Replay

- `run_broad_live_as_if_replay_harness.py` repaired profile.
- `v4_timewarp_simulated_live_research_loop.py` scheduler/finalizer/order lifecycle path.
- Route artifacts in `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/`.

Classification: diagnostic/proof replay for a correctness/performance repair already patched.

## Expected Measurable Effect

- Candidate -> scorecard transfer should stay near 25006 candidate rows and 288 scorecard rows if the non-May universe shape matches V97/V98.
- Scorecard -> order transfer should avoid V99-style weak degraded passive fallback churn without collapsing opportunities.
- Order -> fill transfer should keep executed REFUSED/source-gap counts at zero.
- Missed positive R may remain large; the key is whether added transfers versus V98/V97 are net positive and whether removed positives shrink.
- Trade count should not collapse to a positive-by-suppression shape.
- Net/gross/final R should improve over V98 non-May if V100 generalizes; if it degrades, added/removed trade churn will decide whether passive fallback repair overfiltered or exposed another root leak.
- W/L/F should improve by better transfer quality rather than only fewer trades.
- Risk-reduced/full-risk distribution must remain provenance-preserved.

## Success And Failure Criteria

- Helped: V100 non-May beats V98 and V97 on net/final R, added trades are net positive, removed trades are weaker or net negative, expired-unfilled pressure stays controlled, and cost REFUSED/source-gap execution remains zero.
- Failed: V100 non-May loses to V98 because removed positives exceed added transfer, or trade count collapses while missed positive R grows.
- Exposes next deeper flaw: V100 non-May improves transfer but remains weak because same-symbol replacement lifecycle or stop geometry dominates residual losses. In that case the next patch should target the same-root leak that is material across both hostile and non-May windows.
