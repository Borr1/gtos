# V112 Transfer-Contract Repair Pre-Replay Brief

Generated: 2026-07-04T04:00:57Z

## Current State

- No broad replay is running.
- The V111 parity builder completed and produced `SOURCE_BOUND_TO_EXECUTED_PARITY_V111_SCHEDULER_FILLABILITY_TRUTH_REPAIR_20260601_20260619_REPAIRED_ONLY_COMPACT_FULLGRID_SUMMARY.json`.
- A stale wide `git add` helper was terminated; no index lock remained.
- Broker/live/final remain closed. Local replay/package authority remains full.

## Same-Window Results

V92 hostile comparator, 2026-05-13..2026-05-17:
- 51 trades, +29.35570236 net R, +33.9321286 gross/final R, +6228.63096022 cash, W/L/F 37/14/0.
- 25006 candidates, 288 scorecard rows, 119 order rows, 62 expired unfilled.
- Window source-bound denominator +218870.181480028R; 1101 package axes, 894 candidate axes, 39 scorecard/order axes, 25 filled axes, +17.76833767 actual executable R.
- Missed positive +2054.54396823R; missed negative -7914.65328589R.

V97 same hostile window:
- 47 trades, +13.89627731 net R, +18.2389067 gross/final R, +4461.09800786 cash, W/L/F 23/24/0.
- 25006 candidates, 288 scorecard rows, 98 order rows, 51 expired unfilled.
- Window source-bound denominator +222423.262022048R; 1101 package axes, 894 candidate axes, 29 scorecard/order axes, 18 filled axes, +13.48984606 actual executable R.
- Missed positive +2059.22271586R; missed negative -9738.85318535R.
- V97 added 19 trades for +0.99594545R and removed 23 trades for +13.53876156R. Added transfers were net positive, but added-minus-removed was -12.54281611R.

V110B broad comparator, 2026-06-01..2026-06-19:
- 95 trades, +22.80442652 net R, +28.71092008 gross/final R, +3098.56483036 cash, W/L/F 52/43/0.
- 75274 candidates, 1056 scorecard rows, 96 order rows, 0 expired unfilled.
- Window source-bound denominator +342126.925564897R; 1101 package axes, 944 candidate axes, 34 scorecard/order axes, 33 filled axes, +21.88363795 actual executable R.

V111 same broad window:
- 45 trades, -4.19333138 net R, +0.53053553 gross/final R, -420.03678236 cash, W/L/F 12/33/0.
- 75911 candidates, 1056 scorecard rows, 73 order rows, 28 expired unfilled.
- Window source-bound denominator +342126.925564897R; 1101 package axes, 944 candidate axes, 16 scorecard/order axes, 13 filled axes, -2.06644961 actual executable R.
- V111 added 45 trades for -4.19333138R, removed 95 V110B trades for +22.80442652R, common stable trade keys 0.

These are bounded replay-window denominators. They do not prove full 1.249M reservoir conversion or failure.

## Incorporated Subagent Findings

- Hooke: incorporated. V111 is materialization displacement, not candidate availability.
- Schrodinger: incorporated. Raw selector action is overwritten by materialized action; scheduler/risk-action transfer collapsed.
- Erdos: incorporated. Cancel-replace is not primary; limit-first/fallback contract and fill-floor materialization are the order leak.
- Euclid: incorporated. Patch upstream scheduler/order transfer before exit tuning; V111 substituted off-session USOIL-heavy shorts and removed broad V110B source families.

## Root Mismatch Classes

- Source-bound -> candidate: not the current primary choke; candidates and axes remain broad.
- Candidate -> selector: partially fixed; router-refusal family parity must include `session_open_range_break`.
- Selector -> scheduler: open under patch; broad harness must keep raw `selector_action` immutable and materialized package authority in `effective_selector_action`.
- Scheduler -> risk -> order: open; V111 kept scorecard count flat but reduced orders/fills and selected zero reallocation probes.
- Order -> lifecycle -> fill: open; V111 reintroduced 28 expired unfilled and market fallback rows.
- Fill -> exit: deferred until transfer repair proof; V111 exit losses come from a substituted trade set.
- Ledger/verifier: partially fixed; V111 parity materialized, and selector/fallback parity now need focused tests.

## Patch Batch

Files:
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py`
- `tests/test_broad_replay_repair_config.py`
- `research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/build_source_bound_execution_parity.py`

Patch types:
- Correctness: preserve raw selector action; use `effective_selector_action` for replay materialization.
- Correctness: restore `session_open_range_break` in selector and scheduler router-refusal origin-family parity.
- Correctness: keep off-configured guarded-market fallback non-executable in broad replay unless signed route authority later proves it.
- Verifier/test: assert selector-action immutability, origin-family parity, and fallback false contract.
- Infrastructure: robust JSONL parity reader reopens after repeated read timeouts.

## Expected Measurable Effect

- Candidate -> scorecard transfer: should not collapse; scorecard should remain broad.
- Scorecard -> order transfer: should recover valid V110B-like source-family transfer if action/fallback parity was the leak.
- Order -> fill transfer: expired unfilled should fall versus V111 or become explicitly missed with guard reason.
- Missed positive R: may rise if unsafe fallback is demoted to missed; acceptable only with explicit scoreable reason.
- Missed negative R: should remain diagnostic for non-executable cost/refused rows.
- Trade count: should not collapse toward zero; compare against V111 45 and V110B 95.
- Net/gross/final R: helped if V112 improves versus V111 without suppressing opportunity.
- W/L/F: helped if retained/added transfer is not dominated by off-session substituted losers.
- Cost-refused/source-gap execution: must remain zero.
- Risk-reduced/full-risk: likely remains open-reduced until a separate signed full-risk promotion patch.

## Replay Proof Rule

Run focused tests first. Then run a targeted bucket replay before a full broad replay unless subagent/verifier findings prove the patch is global-only.

Helped:
- V112 improves versus V111 and/or restores removed positive source-family transfer while keeping refused/source-gap rows non-executable.

Failed:
- V112 remains disjoint and negative with V110B-like winners still removed and no explicit predecision blocker.

Next exposed flaw:
- If transfer recovers but losses remain, patch scale-in/time-stop/exit quality using causal predecision fields, not date/symbol/session buckets.
