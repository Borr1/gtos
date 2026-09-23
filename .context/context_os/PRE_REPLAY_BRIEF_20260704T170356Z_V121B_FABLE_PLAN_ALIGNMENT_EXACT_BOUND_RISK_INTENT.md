# V121B Fable Plan Alignment / Exact-Bound Risk Intent Pre-Replay Brief

Broker/live/final remain closed. Local replay/package authority remains full. The saved Fable plan files are the controlling dependency map:

- `.context/context_os/ultimate_system_plan/IMPLEMENTATION_SEQUENCE_ULTIMATE_SYSTEM_FLOW_20260704.md`
- `.context/context_os/ultimate_system_plan/FABLE_ROOT_CAUSE_AUDIT_AND_IMPLEMENTATION_PLAN_20260704.md`

Both saved files match the current attachments by SHA-256.

## Current Process State

No broad replay, pytest, or stale git helper process is active from the resolved process check. Do not duplicate a replay. The next run is a targeted one-day proof slice only.

## Latest Completed Replay

- Prefix: `BROAD_LIVE_AS_IF_REPLAY_V120F_SOURCE_BOUND_SELF_LOCK_REPAIR_20260515_REPAIRED_ONLY_FULLGRID`
- Window: `2026-05-15..2026-05-15`
- Result: `96` scorecards, `26` order events / `13` unique orders, `4` trades, `8161` missed rows.
- Trade result: W/L/F `0/4/0`, net `-3.80274600R`, gross/final `-3.36900465R`, cash PnL `-379.74586967`.
- Expired unfilled: `9`.
- Executed REFUSED/source-gap/ordered-tick source-gap rows: `0`.

This is a one-day local proof baseline. It does not prove total reservoir conversion.

## Comparator Context

Hostile five-day comparators remain context only for this one-day V121B proof:

| Run | Window | Trades | Net R | Gross/Final R | Cash | W/L/F |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| V89D | 2026-05-13..17 | 56 | +34.84520454 | +39.93441037 | +8178.90660707 | 41/15/0 |
| V90 | 2026-05-13..17 | 51 | +28.84201157 | +33.36349114 | +6371.80465431 | 37/14/0 |
| V92 | 2026-05-13..17 | 51 | +29.35570236 | +33.93212860 | +6228.63096022 | 37/14/0 |

V92 five-day same-window source-bound context: `218870.181480028R`, `894` candidate axes, `39` scorecard/order axes, `25` filled axes, `+17.76833767R` executable R. These are not the V121B one-day denominator.

## Current Dirty Code / Active Changes

Active touched surfaces include selector, scheduler, timewarp replay, broker/fill realism helper, verifier/comparison/bridge route scripts, config, and focused tests. The current code already contains substantial Fable B0-B5 implementation. The open checkpoint is not to restart at B0; it is to prove the current exact-bound risk-intent repair and then continue through the Fable ladder from the first failing gate.

## Subagent Findings

- Herschel: incorporated. Risk-intent recovery must require signed authority, source completeness, broker-cost pass, no fallback cost authority, and exact candidate-time/scheduler binding.
- Lorentz: incorporated. `selected_cell_or_requested_risk_missing_nonpositive` is scheduler-produced before finalizer ranking; recovery must be scheduler/package exact-bound, with synthesized probes diagnostic-only.

## Known Mismatch Classes

- source-bound -> candidate: V120F source-bound self-lock is locally fixed; candidate ledger omitted in the smoke, so transfer proof uses scorecard/order/missed artifacts until the next run.
- candidate -> selector: raw selector action and effective materialized action are separated; raw-reject promotion remains signed-contract-only.
- selector -> scheduler: exact-bound bounded `risk_per_trade_pct` now rehydrates scheduler requested risk for rows previously vetoed as nonpositive.
- scheduler -> risk: if rows become eligible but still do not order, finalizer reallocation is the next suspected leak.
- risk -> order: REFUSED/source-gap/ordered-tick source-gap execution must stay zero.
- order -> lifecycle/fill: stricter fill realism may turn added orders into missed/diagnostic rows instead of fills.
- fill -> exit: do not tune exits until transfer truth is clean; V120F surviving fills all lost.
- ledger: risk ladder and gross/net identity are under focused tests and must be verified in replay artifacts.

## Projection Before Replay

Projection over `BROAD_LIVE_AS_IF_REPLAY_V120F_SOURCE_BOUND_SELF_LOCK_REPAIR_20260515_REPAIRED_ONLY_FULLGRID_MISSED_OPPORTUNITY_LEDGER.jsonl`:

- Blocker: `selected_cell_or_requested_risk_missing_nonpositive`
- Rows rehydrating positive bounded risk: `873`
- Rows still not rehydrated: `0`
- Risk source: `bounded_package_risk_per_trade_pct`
- Requested risk range: `0.25..2.0`
- Sessions: off-configured `607`, london `173`, ny `88`, tokyo `5`

This proves the code path changes the local blocker classification. It does not prove performance.

## Next Proof

Prefix: `BROAD_LIVE_AS_IF_REPLAY_V121B_EXACT_BOUND_RISK_INTENT_SOURCE_GAP_CLOSURE_20260515_REPAIRED_ONLY_FULLGRID_SKIPTICK_SOURCE_STALL_BYPASS`

Window: `2026-05-15..2026-05-15`

Mode note: the first V121B launch without `--skip-tick-source` stalled during source discovery before producing artifacts. This proof uses the existing targeted repair-smoke `--skip-tick-source` path and labels the prefix with `SKIPTICK_SOURCE_STALL_BYPASS`.

Expected measurable effects:

- candidate -> scorecard: unchanged or explicitly attributable.
- scorecard -> order: may increase if runtime-ineligible options become selectable.
- order -> fill: may increase or shift to exact fillability/lifecycle blockers.
- missed positive/negative R: blocker reasons should move from nonpositive risk to exact downstream reasons.
- trade count/net/gross/final R/W/L/F: may improve or worsen; worsening is acceptable only if it exposes honest risk expression or a deeper leak.
- cost-refused/source-gap execution: must stay `0`.
- risk-reduced/full-risk distribution: must be present and separated.

Helped if the nonpositive-risk blocker drops and added/removed orders/trades are causally attributed without REFUSED/source-gap execution. Failed if rows execute without signed/cost-passed/source-complete/exact-bound authority, if source-gap execution reappears, or if nothing changes and the blocker stays the same.

## Verification Already Done

- `py_compile`: passed for touched scheduler/timewarp/verifier/test modules.
- Focused pytest: `9 passed, 1 warning`.
