# V105 Hostile Transfer Exposure Pre-Replay Brief

Generated: 2026-07-03T19:07:30Z

## Current Replay State

- No broad replay is currently running.
- Latest completed current-code broader replay: `BROAD_LIVE_AS_IF_REPLAY_V105_SOURCEFIELD_M1_PROFIT_HARVEST_20260601_20260605_REPAIRED_ONLY_COMPACT_FULLGRID`.
- Broker/live/final remain closed. Local replay/package authority remains full.
- This next run is not policy tuning. It is hostile-window exposure for the current V105 source-field + M1 profit-harvest repair.

## Same-Window V92 vs V97 Hostile Comparator

- V92 `BROAD_LIVE_AS_IF_REPLAY_LIFECYCLE_TRUTH_ADAPTIVE_AXIS_REPAIR_V92_20260513_20260517_REPAIRED_ONLY_COMPACT_FULLGRID`: 51 trades, +29.35570236 net R, +33.9321286 gross/final R, cash +6228.63096022, W/L/F 37/14/0, 62 expired unfilled.
- V97 `BROAD_LIVE_AS_IF_REPLAY_DYNAMIC_SCOPE_REPAIR_V97_SEMANTICS_20260513_20260517_REPAIRED_ONLY_COMPACT_FULLGRID`: 47 trades, +13.89627731 net R, +18.2389067 gross/final R, cash +4461.09800786, W/L/F 23/24/0, 51 expired unfilled.
- Candidate rows and scorecards were unchanged at 25006 and 288. V97 order rows fell 119 -> 98 and order events fell 239 -> 196.
- Exact-window axes: V92 894 candidate axes, 39 scorecard/order axes, 25 filled axes, +17.76833767 actual executable R. V97 894 candidate axes, 29 scorecard/order axes, 18 filled axes, +13.48984606 actual executable R.
- Missed scoreable opportunity: V92 +2054.54396823 positive R and -7914.65328589 negative R. V97 +2059.22271586 positive R and -9738.85318535 negative R.
- V97 added 19 trades worth +0.99594545R, but removed 23 V92 trades worth +13.53876156R; added-minus-removed was -12.54281611R. Added transfers were net positive but weak; removed transfers were much stronger and included profit-harvest/protective exits.

## Newest Completed V105 Non-May Broad Result

- V104 baseline `BROAD_LIVE_AS_IF_REPLAY_PASSIVE_DISTANCE_HARD_BLOCK_V104_20260601_20260605`: 46 trades, +14.73101491 net R, +18.3617451 gross/final R, cash +2850.02330565, W/L/F 26/20/0, 9 expired.
- V105 `BROAD_LIVE_AS_IF_REPLAY_V105_SOURCEFIELD_M1_PROFIT_HARVEST_20260601_20260605_REPAIRED_ONLY_COMPACT_FULLGRID`: 109 trades, +16.0037838 net R, +24.00079247 gross/final R, cash +2953.25557512, W/L/F 67/42/0, 13 expired.
- V105 vs V104: +63 trades, +1.27276889 net R, +5.63904737 gross/final R, +41 wins, +22 losses, +68 order rows, +137 order events.
- V105 added 74 trades worth -0.7786178R and removed 11 trades worth +0.44791063R; added-minus-removed was -1.22652843R. The headline improvement came from common/exit behavior and lower missed negative R, not net-positive added transfer.
- Exact-window axes: candidate axes unchanged at 894/1101; scorecard/order axes improved 33 -> 62; filled axes improved 27 -> 58; actual executable R moved +11.22066476 -> +10.37690212, while axis-attributed actual R fell +13.36917856 -> +3.05393439.
- All 248 V105 order events remained `open-reduced-risk`.

## Current Root Mismatch Map

- Source-bound -> candidate: not the immediate choke on the compared windows. Candidate rows and candidate axes are stable.
- Candidate -> selector: partially fixed, but broker-cost refused rows must remain non-executable and source-required rows must remain honest.
- Selector -> scheduler -> risk: still the largest root leak. V105 has 196 `candidate_generated_not_scheduler_selected` bucket rows carrying +304548.612273349 source-bound R and zero executed R.
- Risk authority: all V105 order events are `open-reduced-risk`, so full-risk/risk-reduced translation and provenance must be audited after hostile replay.
- Order/fillability/lifecycle/exit: V105 restores profit-harvest headline exits in non-May, but added transfers are net negative; V92/V97 still shows displaced stronger lifecycle/profit-harvest paths.
- Ledger/verifier: V105 non-May artifacts materialized; hostile V105 artifacts are still pending.

## Next Replay

Run current V105 code on the hostile 2026-05-13..2026-05-17 fullgrid:

`BROAD_LIVE_AS_IF_REPLAY_V105_SOURCEFIELD_M1_PROFIT_HARVEST_20260513_20260517_REPAIRED_ONLY_COMPACT_FULLGRID`

Success is not “more trades.” The run helps only if it shows one of:

- better candidate -> scorecard/order transfer without adding net-negative transfers;
- better order -> fill transfer with added trades net positive;
- restored profit-harvest/lifecycle value versus V97 without suppressing opportunity;
- reduced missed negative R without masking missed positive R;
- or a clear same-root blocker for selector/scheduler/risk allocation.

Failure or deeper-flaw exposure is:

- V105 hostile remains below V92/V104 while added trades are net negative;
- all orders remain open-reduced-risk with higher exposure and worse drawdown;
- scorecard/order transfer improves but actual executable R or axis-attributed R falls;
- missed positive R rises materially or strong V92 lifecycle/profit-harvest trades remain displaced.

