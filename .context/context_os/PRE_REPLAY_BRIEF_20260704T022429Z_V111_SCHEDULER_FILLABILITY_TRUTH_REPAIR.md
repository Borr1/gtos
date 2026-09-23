# V111 Scheduler Fillability Truth Repair Pre-Replay Brief

Generated UTC: 2026-07-04T02:24:29Z

Broker/live/final remain closed. Local replay/package evaluation keeps full 82-sleeve authority and missed-opportunity accounting.

## Current Completed Comparator

Hostile five-day window, 2026-05-13..2026-05-17:

- V92: 51 trades, +29.35570236 net R, +33.9321286 gross/final R, +6228.63096022 cash, 37/14/0 W/L/F, 62 expired unfilled, 894 candidate axes, 39 scorecard/order axes, 25 filled axes, +17.76833767 same-window executable R.
- V97: 47 trades, +13.89627731 net R, +18.2389067 gross/final R, +4461.09800786 cash, 23/24/0 W/L/F, 51 expired unfilled, 894 candidate axes, 29 scorecard/order axes, 18 filled axes, +13.48984606 same-window executable R.
- V97 vs V92: -4 trades, -15.45942505 net R, -15.6932219 gross/final R, -1767.53295236 cash, -11 expired unfilled, -10 scorecard/order axes, -7 filled axes.
- V97 added 19 trades for +0.99594545R and removed 23 V92 trades for +13.53876156R. Added transfers were net positive, but the transfer swap was net negative by -12.54281611R.

This proves V97 was not a sufficient hostile-bucket improvement. It does not prove full-reservoir failure or success.

## Current Broad Baseline

V110B, 2026-06-01..2026-06-19, repaired-only compact fullgrid:

- 95 trades, +22.80442652 net R, +28.71092008 gross/final R, +3098.56483036 cash, 52/43/0 W/L/F.
- 75,274 candidate rows, 1,056 scorecard rows, 193 order-event rows, 96 filled order rows, 95 trade rows, 0 expired.
- Same-window transfer denominator: 342,126.925564897 source-bound R, 1,101 package axes, 944 candidate-generated axes, 34 scorecard/order axes, 33 filled axes, +21.88363795 actual executable R.
- V110B beat V109 on this 19-day window by +23.42641597 net R, but transfer remained tiny and mostly open-reduced-risk.

## Subagent Disposition

- Goodall: mostly incorporated. Patched terminal lifecycle close-missing-R as non-filled/deferred, filled order/oracle without trade as fatal, signed package selector action immutability, oracle bridge conflict preservation, and stale stop-hazard cap clearing. Broader oracle/order/trade action parity scanner remains optional verifier hardening.
- Banach: incorporated into this replay lane. Top effective leak is scheduler ranking/reallocation: 183 candidate-generated-not-scheduler-selected axes, 245,158.7788728301R effective source-bound R. Dominant reason is fill probability below execution-authority floor; secondary reasons include marketable entry guard, signed authority displacement, missing risk/cell, lifecycle scale-in, passive-limit, and stop-hazard.
- Zeno: accepted and deferred. Risk reduction frequency is configured selector authority, not dynamic-budget collapse. Full-risk promotion needs a signed verifier-visible authority path, not silent reinterpretation of open-reduced rows.

## Current Patch Batch

Files/components:

- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`: stop-hazard target binding/pressure routing and passive-limit execution-authority fill-floor classification.
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`: scheduler geometry propagation, stop-hazard field propagation, lifecycle missing-close-R deferral, signed authority immutability.
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_selected_package_replay_bridge.py`: filled oracle/order without trade disposition, oracle conflict preservation, stale stop-hazard cap clearing.
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/verify_denominator_to_deployment_execution.py`: fatal verifier disposition for filled oracle/order without trade.
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py`: repaired-profile stop-hazard target/pressure config.

Focused verification passed: py_compile plus scheduler, timewarp lifecycle/authority, bridge/profile/stop-hazard, and verifier selected-package focused pytest slices.

## Replay Plan

Run repaired-only compact fullgrid on 2026-06-01..2026-06-19:

`BROAD_LIVE_AS_IF_REPLAY_V111_SCHEDULER_FILLABILITY_TRUTH_REPAIR_20260601_20260619_REPAIRED_ONLY_COMPACT_FULLGRID`

Expected proof criteria:

- Candidate rows should stay near 75,274 and candidate axes near 944; collapse means over-filtering.
- Scorecard/order/fill transfer should improve only through executable passive-limit/stop-hazard truth, not REFUSED/source-gap execution.
- Filled oracle/order without trade must remain impossible or verifier-fatal.
- Missed positive R should fall only if positive opportunity becomes actual order/fill transfer.
- Net R should improve versus V110B +22.80442652 or, if it worsens, added/removed/common trade decomposition must show the next root leak.
- Risk distribution is expected to remain open-reduced unless a later signed full-risk promotion path is implemented.

This is a 19-day broad repair proof, not a full 1.249M reservoir conversion claim.
