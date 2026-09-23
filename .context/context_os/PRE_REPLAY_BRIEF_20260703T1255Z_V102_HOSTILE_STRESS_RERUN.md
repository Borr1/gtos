# V102 Hostile Stress Pre-Replay Brief

Generated: 2026-07-03T12:55Z

## Current Latest Completed Replay

- Latest completed non-May objective regime run: `BROAD_LIVE_AS_IF_REPLAY_STOP_HAZARD_BLOCK_REPAIR_V102_20260601_20260605`.
- Result: 63 trades, +14.09604195 net R, +18.72525429 gross/final R, 2565.04589722 cash PnL, W/L/F 33/30/0, 26 expired unfilled.
- Transfer denominator for that exact window: 426601.3938625386 source-bound/package R, 1101 package axes, 894 candidate-generated axes, 32 scorecard/order axes, 32 order-present axes, 27 filled axes, +11.20397353 unique actual executable R.
- Interpretation: this smoke proves a local repair on 2026-06-01..2026-06-05; it does not prove total reservoir conversion.

## Process State

- No broad replay, parity builder, comparator, pytest, or compile process is running.
- Broker/live/final remain false. Local replay/package authority remains full.

## Baselines

- V92 hostile `BROAD_LIVE_AS_IF_REPLAY_LIFECYCLE_TRUTH_ADAPTIVE_AXIS_REPAIR_V92_20260513_20260517_REPAIRED_ONLY_COMPACT_FULLGRID`: 51 trades, +29.35570236 net R, +33.93212860 gross/final R, W/L/F 37/14/0, 62 expired unfilled.
- V97 hostile `BROAD_LIVE_AS_IF_REPLAY_DYNAMIC_SCOPE_REPAIR_V97_SEMANTICS_20260513_20260517_REPAIRED_ONLY_COMPACT_FULLGRID`: 47 trades, +13.89627731 net R, +18.23890670 gross/final R, W/L/F 23/24/0, 51 expired unfilled.
- V100 hostile `BROAD_LIVE_AS_IF_REPLAY_PASSIVE_FALLBACK_DISPLACEMENT_REPAIR_V100_20260513_20260517`: 52 trades, +24.50126904 net R, +29.33465208 gross/final R, W/L/F 29/23/0, 11 expired unfilled.
- V102 non-May versus V100 non-May: +10.29922102 net R from blocking the all-threshold stop-hazard transfer and reallocation; added 4 trades for +6.74411002R and removed 8 trades for -3.55511100R.

## Subagent Findings Incorporated

- Stop-geometry residual finding incorporated: cap/rank penalty was insufficient, so the same predecision all-threshold hazard class is blocked for the repaired profile.
- Same-symbol/pending replacement finding remains partially open: V100/V102 displacement helped, but same-symbol lifecycle veto still appears in missed-opportunity diagnostics and should be revisited after the hostile rerun.
- Comparator/status findings incorporated into this brief and the V102 comparison set.

## Known Mismatch Classes

- Source-bound to candidate: 823/1101 source axes had exact package-candidate match in V102 non-May; 894/1101 axes became candidates. Remaining non-generated axes are partly non-admission/redesign/source-required classes.
- Candidate to selector: cost-refused and negative broker-net EV rows stay non-executable; this is intended broker-calibrated cost authority, not the old candidate-cost proxy.
- Selector to scheduler: only 32/894 axes reached scorecard/order presence in V102 non-May. Scheduler/finalizer materialization remains the main transfer bottleneck.
- Scheduler to risk/order: all 90 V102 non-May accepted/order rows were open-reduced-risk; full-risk distribution remains open, but no refused-cost/source-gap rows executed.
- Order to fill/lifecycle: V102 non-May had 26 expired unfilled rows and same-symbol lifecycle veto remains visible in missed rows.
- Fill to exit: stops remain the largest realized damage class, but V102 removed the known all-threshold fragile stop subset on non-May.
- Ledger: compact missed rows preserve proxy R fields; parity reports exact replay-window denominator separately from global reservoir diagnostics.

## Patch Batch Under Test

- `run_broad_live_as_if_replay_harness.py`: repaired profile sets `scheduler_v4_best_trade_allocator_predecision_stop_hazard_guard_action = "block"`.
- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`: score penalty now applies to capped hazards when a profile uses cap semantics.
- Tests for repaired config and scheduler cap semantics passed before this rerun.

Patch classification: correctness/performance repair. It is a causal predecision guard over unit-risk ATR, distance-to-limit risk, limit fill probability, and action intent. It is not a date/symbol/session loss bucket.

## Expected Measurable Effect

- Candidate rows should remain around the V97/V100 hostile surface: 25006 candidates and 288 scorecard rows.
- V100 hostile had one all-threshold stop-hazard loser worth about -1.09623503R; V102 should block that row or reallocate it.
- Success is not positive-by-suppression: trade count may stay similar if reallocation works, and added transfers should not be net negative.
- Cost-refused/source-gap executed counts must remain zero.
- Report same-window source-bound R, package axes, candidate axes, scorecard/order axes, filled axes, executable R, missed positive/negative R, expired unfilled, added/removed trades, stress, and Monte Carlo.

## Result Interpretation

- Helped: V102 hostile improves over V100 or at least removes the known all-threshold hazard without adding worse replacements, while preserving cost authority.
- Failed: V102 worsens V100 materially, especially if removed transfers were positive or replacement rows are net negative.
- Exposed next flaw: if V102 helps but underperforms V92, the next batch should target scheduler/finalizer transfer and same-symbol lifecycle/expiry leaks rather than further one-day tuning.
