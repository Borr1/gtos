# V104 Non-May Objective 5D Pre-Replay Brief

Generated: 2026-07-03T14:55:00Z

## Current Latest Completed Replay

- Prefix: `BROAD_LIVE_AS_IF_REPLAY_PASSIVE_DISTANCE_HARD_BLOCK_V104_20260513_20260517`
- Window: `2026-05-13..2026-05-17`
- Result: 49 trades, +25.69434914 net R, +30.22329715 gross/final R, cash +6361.76531572, W/L/F 28/21/0, 6 expired.
- Same-window transfer: 1101 package axes, 894 candidate axes, 30 scorecard/order axes, 28 filled axes, +24.76997972 actual executable R.
- Safety/truth: broker/live/final false; cost-refused/source-gap executed rows 0; degraded passive distance-breach filled/order rows 0.

## Baseline Comparison

- V104 vs V103 hostile: +1.22885245 net R, trades -15. The distance-breach hard block removed weak/displacing degraded passive queue transfers.
- V104 vs V102 hostile: +0.09684507 net R, trades -2. This is a correctness improvement, not a broad performance breakthrough.
- V104 vs V92 hostile: -3.66135322 net R. Remaining issue is downstream transfer/lifecycle/exit quality.
- V97 vs V92 hostile: V97 added 19 trades worth +0.99594545R but removed 23 V92 trades worth +13.53876156R, so the leak is not candidate generation but selector/scheduler/risk/order/lifecycle transfer.

## Running Process State

No broad replay or parity builder is running after V104 hostile parity materialized. A stale `git add` helper was killed before this brief; it did not leave staged files.

## Current Active Code Changes

- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`: distance-to-limit thesis-geometry breach removed from degraded passive fallback-only reason allowlist.
- `verify_denominator_to_deployment_execution.py`: degraded passive release validator rejects distance-breach quality failures and keeps broker-cost/source-gap hard blocks.
- `run_broad_live_as_if_replay_harness.py`: compact missed rows preserve passive fallback envelope numeric audit fields; repaired profile floor remains 0.40 for allowed fallback-only degraded release.
- Focused tests passed: py_compile and 9 targeted pytest tests.

## Incorporated Subagent Findings

- Erdos the 2nd: V97 regression is downstream transfer displacement, not source/candidate starvation.
- Copernicus the 2nd: V104 distance-breach hard block is a correctness repair; inspect zero degraded passive distance-breach fills/orders.
- Harvey the 3rd: next objective regime should be `2026-06-01..2026-06-05`, then `2026-06-01..2026-06-19`, then full holdout `2026-05-13..2026-06-19`.

## Known Mismatch Classes

- Source-bound -> candidate: not current choke; hostile windows keep 894/1101 candidate-generated axes.
- Candidate -> selector: guarded; broad cost REFUSED/source-gap rows stay non-executable.
- Selector -> scheduler -> risk: open major bottleneck; V104 hostile transfers only 30/894 candidate axes to scorecard/order presence and finalizer selects 0 reallocations from 24 admitted probes.
- Risk -> order/fillability: partially fixed; distance-breach degraded passive queue release is now hard-blocked.
- Order -> lifecycle/fill/exit: open; V104 remains below V92 and V97 removed lifecycle/exit-rich V92 winners.
- Ledger/verifier: patched for V104; focused tests pass.

## Next Replay

- Prefix: `BROAD_LIVE_AS_IF_REPLAY_PASSIVE_DISTANCE_HARD_BLOCK_V104_20260601_20260605`
- Window: `2026-06-01..2026-06-05`
- Purpose: objective non-May regime validation of the V104 correctness repair.
- Expected baseline from V102 non-May: 63 trades, +14.09604195 net R, +18.72525429 gross/final R, W/L/F 33/30/0, 26 expired, 35191 candidates, 480 scorecards, 32 scorecard/order axes, 27 filled axes.

## Success / Failure Read

- Helped: V104 non-May improves or remains close to V102 while keeping zero cost-refused/source-gap execution and zero degraded passive distance-breach execution.
- Failed: V104 non-May materially worsens without clear truth improvement; then the distance-breach hard block is not enough and the next patch must target finalizer selected-but-not-materialized reallocation/action-intent authority.
- Exposes deeper flaw: candidate/scorecard counts stay stable but scorecard/order/fill axes remain near 30/894; then the bottleneck is scheduler/risk finalizer transfer and lifecycle/exit behavior, not source-bound materialization.

Broker/live/final remain false; local replay/package authority remains full.
