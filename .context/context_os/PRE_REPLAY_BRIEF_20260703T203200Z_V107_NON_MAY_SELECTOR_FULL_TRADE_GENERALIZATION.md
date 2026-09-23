# V107 Non-May Selector-Full-Trade Generalization Brief

Generated UTC: 2026-07-03T20:32:00Z

This is a replay-control brief, not a final/live claim. Broker/live/final remain closed.

## Current Completed Replay

- Latest completed prefix: `BROAD_LIVE_AS_IF_REPLAY_V106_SELECTOR_FULL_TRADE_RELEASE_20260513_20260517_REPAIRED_ONLY_COMPACT_FULLGRID`
- Window: 2026-05-13..2026-05-17 hostile/stress bucket.
- Result: 83 trades, +32.57834226 net R, +39.15063139 gross/final R, +8761.18608031 cash, 56/27/0 W/L/F.
- Candidate/scorecard/order: 25006 candidate rows, 288 scorecard rows, 91 logical order rows, 185 order events.
- Missed scoreable: +2038.83087056R positive, -7903.90220859R negative, -5865.07133803R total.
- Transfer: 1101 package axes, 894 candidate-generated axes, 49 scorecard/order axes, 48 filled-trade axes, +31.27808878 unique actual executable R inside the replay window.

## Baseline Comparisons

- V92 hostile: 51 trades, +29.35570236 net R, +33.9321286 gross/final R, 37/14/0.
- V97 hostile: 47 trades, +13.89627731 net R, +18.2389067 gross/final R, 23/24/0.
- V97 vs V92: -4 trades, -15.45942505 net R, added 19 trades for +0.99594545R and removed 23 trades for +13.53876156R. Added transfers were net positive but displaced stronger V92 transfers.
- V105 hostile: 86 trades, +31.8594334 net R, +38.77147731 gross/final R, 58/28/0.
- V106 vs V105: -3 trades, +0.71890886 net R, +0.37915408 gross/final R, added 2 trades for +3.60220064R and removed 5 trades for +2.88329178R. This is a quality improvement, not a transfer expansion.

## Current Root Mismatch Map

- Source-bound -> candidate: partially fixed; hostile window still has 207 axes not candidate-generated or classified non-trade/non-executable.
- Candidate -> selector: V106 selector full-trade release improved quality but did not expand scorecard/order axes.
- Selector -> scheduler: open material leak; 209 generated axes remain not scheduler-selected in V106 repair plan with 325945.935780103 effective source-bound R.
- Scheduler -> finalizer: open correctness leak; finalizer synthetic all-candidate probes must not become executable without exact `all_options_preserved` scheduler binding.
- Risk/order/fill/lifecycle: partially fixed; V106 has 91 accepted pending orders and 83 fills, with one order-accepted-not-filled axis bucket.
- Exit/profit-harvest: still needs broader-regime read; V106 exits include giveback/protective/stop/target/time-stop paths.

## Next Replay

Run the same current V106 code/config on the objective non-May bucket:

- Prefix: `BROAD_LIVE_AS_IF_REPLAY_V107_SELECTOR_FULL_TRADE_RELEASE_20260601_20260605_REPAIRED_ONLY_COMPACT_FULLGRID`
- Window: 2026-06-01..2026-06-05
- Baseline: `BROAD_LIVE_AS_IF_REPLAY_V105_SOURCEFIELD_M1_PROFIT_HARVEST_20260601_20260605_REPAIRED_ONLY_COMPACT_FULLGRID`
- Baseline result: 109 trades, +16.0037838 net R, +24.00079247 gross/final R, +2953.25557512 cash, 67/42/0, 35191 candidate rows, 480 scorecard rows.

Success/failure criteria:

- Helped: V107 preserves or improves non-May net/gross/final R without suppressing broad opportunity, and added transfers are net positive versus removed transfers.
- Failed: V107 hostile improvement does not generalize, especially if added transfer is net negative, scorecard/order/fill transfer shrinks, or missed positive R grows materially.
- Exposes next flaw: finalizer/scheduler transfer or exit geometry dominates losses while selector release remains locally correct.
