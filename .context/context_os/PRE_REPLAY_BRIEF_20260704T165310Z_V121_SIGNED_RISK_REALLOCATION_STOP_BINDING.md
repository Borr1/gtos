# V121 Signed Risk / Reallocation / Stop Binding Pre-Replay Brief

Broker/live/final remain closed. Local replay/package authority remains full.

## Current Latest Completed Run

- Prefix: `BROAD_LIVE_AS_IF_REPLAY_V120F_SOURCE_BOUND_SELF_LOCK_REPAIR_20260515_REPAIRED_ONLY_FULLGRID`
- Window: `2026-05-15..2026-05-15`
- Result: `96` scorecards, `26` order events / `13` unique orders, `4` trades, `8161` missed rows.
- Trade result: `0/4/0` W/L/F, net `-3.80274600R`, gross/final `-3.36900465R`, cash PnL `-379.74586967`.
- V120E delta: trades `-2`, net `-2.97029230R`, cash PnL `-296.52393238`; V120F removed two optimistic/source-gap winners and added no trades.
- Truth state: executed cost-REFUSED/source-gap/ordered-tick-source-gap rows remain `0`.

This is a one-day local truth repair proof, not a full-reservoir transfer claim.

## Incorporated Subagent Findings

- Descartes: incorporated. Source-bound raw-reject materialization can still become effective `open-reduced-risk`, but the full-risk signed ladder is not behaviorally reachable for that path.
- Gauss: incorporated. Scheduler alternatives exist, but risk-finalizer selected reallocation remains `0` unless exact `all_options_preserved` candidates become risk-admitted and selected; unbound synthesized probes must stay diagnostic-only.
- Kierkegaard: incorporated. Fill realism/source-gap demotion is holding; surviving clean fills lose through adverse geometry, and stop-hazard configured action must be separated from effective action before order materialization.

## Same-Root Patch Batch

Patch files:

- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- `tests/test_moonshot_scheduler_v4_best_trade_allocator.py`
- `tests/test_v4_timewarp_simulated_live_research_loop.py`

Patch intent:

- Correctness: selector-reduced origin is provenance, not an automatic reduced-risk cap. Full risk is allowed only when all signed predecision conditions pass.
- Ledger/proof: propagate `package_risk_expression_full_risk_*` and `full_risk_*` fields into order/trade rows through the risk ledger helper.
- Correctness/diagnostic: split stop-hazard configured action from effective action so `status=passed, action=block` cannot be mistaken for an active block.
- Correctness if supported by focused tests: exact-bound reallocation can promote only preserved scheduler options with runtime eligibility, package authority, broker-cost PASS, and no terminal veto.

## Success / Failure Criteria

Helped if focused tests show signed top-ranked cost-passed/source-complete/fillable package rows can emit `ladder_tier=full`, ledgers preserve full-risk proof fields, stop-hazard effective action is explicit, and REFUSED/source-gap execution authority remains closed.

Failed if full risk can be reached without signed package authority, broker-cost PASS, source completeness, fillability, and top-rank proof; if any REFUSED/source-gap row becomes executable; or if stop-hazard `configured_action=block` is treated as an effective block when status is `passed`.

Replay after tests only. If a replay is run, it is a V121 one-day local proof slice and must be compared same-window against V120F/V120E.
