# V220R4 Nested Fillability Source Repair Targeted Proof

Generated UTC: 2026-07-11T02:24:41Z.

## Snapshot And Scope

- Base commit: `cc4bf946a`; current B7.2 work remains a scoped dirty batch.
- No replay, test, verifier, builder, or subagent process is running.
- Latest completed behavioral replay is still V219 hostile five-day:
  `25006/288/68/23/24972` candidate/scorecard/order/trade/missed,
  W/L/F `14/9/0`, net/gross/final
  `-2.82440031/-0.79141028/-0.79141028`, cash PnL
  `+204.17530212`, full/reduced fills `17/6`, executed
  REFUSED/source-gap `0/0`.
- V220R3 is a completed bounded structural run, not a value success:
  `1651/192/0/0/1651`, net/gross/final/cash `0/0/0/0`, W/L/F `0/0/0`,
  diagnostic scoreable missed rows/R `366/-118.10784844R`, stress/MC trade
  count `0/0`, executed REFUSED/source-gap `0/0`.
- Broker/live/final remain false. Local replay/package authority remains full.

This smoke proves or disproves the local source-contract repair only. It does
not prove hostile five-day value, broad holdout performance, total reservoir
conversion, final selection, or live readiness.

## Same-Window Comparators

- V218 same scope: 3 trades, W/L/F `3/0/0`, net/gross/final
  `+1.10761535/+1.35101129/+1.35101129`, cash `+989.52983936`,
  full/reduced fills `1/2`, executed REFUSED/source-gap `0/0`.
- V220R2 partial: `1651/192/0/0/1651`; eight valid signed executable rows
  were rejected by stale selected-policy projection.
- V220R3 removed that projection failure and serialized a final summary, but
  still produced no terminal execution.
- V89D/V90/V92 hostile five-day remain broad historical comparators only and
  are not directly compared to this two-day/three-symbol smoke.

## V220R3 Root Evidence

- `159/192` scorecard rows were directly blocked by atomic execution
  fillability source failure.
- The nested `predecision_limit_fillability` objects had causal M15 source
  time, safe predecision boundary, fill value, and no outcome fields.
- A stale outer sentinel,
  `execution_fillability_missing_source_bound_input`, was inherited into the
  nested object and masked its own canonical source.
- This was a producer/consumer precedence defect, not proof that the nested
  fillability was absent or untradeable.

## Same-Root Repair

1. Nested fillability uses an explicitly declared nested source when present.
2. It inherits an outer source/class only when that outer pair is itself
   authoritative execution-fillability provenance.
3. Otherwise it binds to canonical
   `predecision_limit_fillability.<value-field>` provenance and the passive
   limit authority class.
4. Explicitly unsafe nested sources, outcome-bound sources, temporal failures,
   numeric conflicts, and unsigned aliases remain fatal.
5. Candidate quality materialization and finalizer derived-authority consumers
   are covered with the exact outer-sentinel plus valid-nested production shape.

Classification: correctness repair with expected candidate-to-scorecard and
scorecard-to-order effect. It adds no policy suppression, cost bypass, or
date/symbol/session bucket.

## Frozen-Ledger Impact Before Replay

- V220R3 candidate rows analyzed: `1651`.
- Rows whose recorded flat execution fill was missing: `1651`.
- Rows recovered to complete causal nested fillability by current code: `1613`.
- Rows still honestly missing fillability: `38`.
- Recovered open-reduced source-bound-router rows: `89`.
- Recovered cost-refused rows: `834`; they remain non-executable because this
  repair does not alter broker-cost authority.

## Files And Consumers

- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`
- `src/research_infra/v4_timewarp_simulated_live_research_loop.py`
- scheduler atomic provenance tests
- runtime candidate-quality and finalizer integration tests
- unchanged materialization, bridge/parity, and verifier consumers revalidated

## Verification Barrier

- Python compile and scoped `git diff --check`: passed.
- Scheduler: `317 passed`.
- Runtime: `744 passed`.
- Materialization + bridge/parity + verifier: `536 passed`.
- Only warning is the existing unknown pytest `asyncio_mode` option.

## Expected Effect And Acceptance

- Candidate/scorecard counts should remain near `1651/192`; deleting
  opportunity is not acceptance.
- The `159` direct source-unrecognized scorecard failures must disappear.
- Cost-refused/source-gap rows remain missed and executed counts remain `0/0`.
- Valid package rows should reach order/risk/lifecycle processing, or expose a
  new exact causal blocker. Repeating `192 -> 0` for the same sentinel fails.
- Order/fill/trade count is not precommitted; ordered ticks, lifecycle, and risk
  truth remain authoritative.
- Report missed positive/negative R, selected/skipped/expired/filled, risk
  distribution, net/gross/final R, cash PnL, W/L/F, stress, and MC even if zero.
- A positive headline obtained only by suppressing candidates or missed rows
  fails acceptance.

## Targeted Command

`PYTHONUNBUFFERED=1 python3 research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/run_broad_live_as_if_replay_harness.py --start 2026-05-13 --end 2026-05-14 --profiles repaired_package_conversion_v3 --symbols XAUUSD USDCAD USDJPY --max-candidates-per-symbol-window 0 --output-prefix BROAD_LIVE_AS_IF_REPLAY_V220R4_NESTED_FILLABILITY_SOURCE_REPAIR_20260513_20260514_XAUUSD_USDCAD_USDJPY_REPAIRED_ONLY`

If structural transfer passes but execution remains zero or losing, select the
next blocker from current risk/order/lifecycle/fill/exit and missed-R buckets
before any hostile five-day replay. Existing V220R2 storage protections carry
forward; a new bounded storage checkpoint is required before a later broad run.
