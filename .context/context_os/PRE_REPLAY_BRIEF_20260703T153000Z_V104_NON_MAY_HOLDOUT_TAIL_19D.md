# V104 Non-May Holdout Tail 19D Pre-Replay Brief

Generated: 2026-07-03T15:30:00Z

## Current Completed Evidence

- V104 hostile `2026-05-13..2026-05-17`: 49 trades, +25.69434914 net R, W/L/F 28/21/0, 6 expired. It improved V103 by +1.22885245R and V102 by +0.09684507R while leaving zero degraded passive distance-breach fills/orders.
- V104 non-May objective `2026-06-01..2026-06-05`: 46 trades, +14.73101491 net R, +18.3617451 gross/final R, cash +2850.02330565, W/L/F 26/20/0, 9 expired.
- V104 non-May vs V102: +0.63497296R, trades -17. It added 2 losers (-2.08277581R) but removed 19 trades worth -2.71774877R, so improvement came from removing worse risk/order/fillability paths, not from adding a stronger transfer set.
- V104 non-May transfer: 1101 package axes, 894 candidate axes, 33 scorecard/order axes, 27 filled axes, +11.22066476 actual executable R.

## Open Root Cause

The distance-breach passive queue leak is fixed in two objective windows. The remaining major mismatch is still downstream transfer:

- Source-bound/candidate materialization is stable: 894/1101 candidate axes.
- Scorecard/order transfer remains tiny: 30/894 hostile, 33/894 non-May.
- Finalizer/reallocation remains weak: non-May V104 has 480 finalizer rows, 305 no-risk-admitted rows, 110 zero-trade no-risk-admitted rows, 320 reallocation probes, 18 admitted, 1 selected.
- Stop losses remain the largest realized loss bucket: non-May V104 has 14 stops for -15.23032781R.

## Next Replay

- Prefix: `BROAD_LIVE_AS_IF_REPLAY_PASSIVE_DISTANCE_HARD_BLOCK_V104_20260601_20260619`
- Window: `2026-06-01..2026-06-19`
- Reason: objective non-May holdout tail, outside the May hostile bucket, after two five-day correctness proofs.
- Expected size: roughly 3.8x the 5-day non-May run; cleanup freed disk from 9.5GB to 29GB before launch.

## Success / Failure Read

- Helped: 19-day result is positive, safety checks stay clean, and transfer percentages do not collapse versus the 5-day non-May slice.
- Failed: 19-day result weakens materially or becomes positive only by suppressing opportunity; then patch finalizer/scheduler reallocation/action-intent authority before broader 38-day holdout.
- Exposes deeper flaw: candidate rows and scorecards scale but order/fill axes stay near the same tiny share; then the bottleneck is scheduler/risk/lifecycle/exit transfer, not source-bound materialization.

Broker/live/final remain false; local replay/package authority remains full.
