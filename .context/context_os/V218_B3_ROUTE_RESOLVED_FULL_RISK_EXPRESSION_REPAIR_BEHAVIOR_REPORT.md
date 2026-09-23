# V218 B3 Route-Resolved Full-Risk Expression Repair - Behavior Report

Generated UTC: 2026-07-09T17:10:00Z.

## Replay Scope

- Prefix: `BROAD_LIVE_AS_IF_REPLAY_V218_B3_ROUTE_RESOLVED_FULL_RISK_EXPRESSION_REPAIR_20260513_20260514_XAUUSD_USDCAD_USDJPY_REPAIRED_ONLY`.
- Window: `2026-05-13..2026-05-14`.
- Symbols: `XAUUSD, USDCAD, USDJPY`.
- Profile: `repaired_package_conversion_v3`.
- Purpose: targeted B3 proof. This is not a full reservoir conversion claim.

## V218 Numbers

- source universe / candidate / scorecard / order ledger / terminal order /
  trade rows: `29 / 1651 / 192 / 8 / 4 / 3`.
- missed opportunity / bucket rows: `1647 / 57`.
- W/L/F: `3/0/0`.
- net/gross/final R: `+1.10761535 / +1.35101129 / +1.35101129`.
- cash PnL: `+989.52983936`.
- risk cash / risk pct: `2257.97537016 / 2.25`.
- expected cost R: `0.24339594`.
- trade frequency: `1.5 trades/day`.
- order status: `filled=3`, `expired_unfilled=1`, `pending_accepted=4`.
- selected action counts: `new_position=4`, `zero_trade=188`.
- fill realism: trades `ordered_tick_entry_touch=3`; orders
  `ordered_tick_entry_touch=3`, `not_filled=1`.
- executed broker-cost REFUSED/source-gap rows: `0/0`.
- missed diagnostic opportunity net R: `-118.29693857`.
- missed executable scoreable net R: `0.0`.
- stress: raw `+1.10761535R`; extra-cost stress net R:
  `+0.95761535` at +0.05R/trade, `+0.80761535` at +0.10R/trade,
  `+0.50761535` at +0.20R/trade.
- Monte Carlo: `200` iterations, total net `+1.10761535R`, trade count `3`,
  max drawdown p05/p50/worst `0.0/0.0/0.0`.

## V217 -> V218 Delta

Same two-day, three-symbol scope.

- candidates / scorecards / trades: unchanged at `1651 / 192 / 3`.
- net/gross/final R: unchanged at `+1.10761535 / +1.35101129 / +1.35101129`.
- W/L/F: unchanged at `3/0/0`.
- expected cost R: unchanged at `0.24339594`.
- missed rows: unchanged at `1647`.
- missed diagnostic opportunity net R: unchanged at `-118.29693857`.
- cash PnL: `+277.0648589 -> +989.52983936`, delta `+712.46498046`.
- risk cash: `750.86709783 -> 2257.97537016`, delta `+1507.10827233`.
- risk pct: `0.75 -> 2.25`, delta `+1.50`.
- order/trade risk decisions changed from all reduced-risk to mixed:
  - trades: `open-reduced-risk=2`, `trade=1`;
  - orders: `open-reduced-risk=6`, `trade=2`.
- full-risk ladder surfaced:
  - trades: `full-risk=1`, `reduced-risk=2`;
  - orders: `full-risk=2`, `reduced-risk=6`.

Interpretation: the B3 patch changed risk expression, not selection. The trade
set and R-multiple were neutral; cash and risk expression increased because one
filled trade and its order pair became full-risk.

## Trade-Level Risk Behavior

- `2026-05-14T08:15:00Z XAUUSD LONG`: reduced-risk,
  runtime risk `0.625`, net R `+0.2991515`, final R `+0.38163102`.
  Route-resolution bypass was true, but final runtime control reduced it.
- `2026-05-14T10:00:00Z XAUUSD LONG`: full-risk,
  runtime risk `1.0`, net R `+0.78846385`, final R `+0.86886489`.
  Route-resolution bypass true, full-risk allowed/applied true, failures `[]`.
- `2026-05-14T13:00:00Z XAUUSD LONG`: reduced-risk,
  runtime risk `0.625`, net R `+0.02`, final R `+0.10051538`.
  Route-resolution bypass was true, but final runtime control reduced it.

## Source-Bound Transfer In Replay Window

- source-bound R available inside exact replay window: `83516.534265543`.
- package axes available: `1101`.
- candidate-generated axes: `827` (`75.113533%`).
- scorecard/order-present axes: `2` (`0.241838%` of generated axes).
- filled trade axes: `2` (`100%` of scorecard/order axes).
- actual executable R inside replay window: `+1.10761535`.
- cash PnL inside replay window: `+989.52983936`.
- full global reservoir remains diagnostic only for this smoke; no total
  reservoir conversion claim is allowed from V218.

## Remaining Dominant Transfer Buckets

From V218 source-bound parity:

- candidate not generated axes: `274`.
- scheduler option present count: `361`.
- scorecard selected count: `3`.
- trade count: `3`.
- leakage labels include:
  - `candidate_generated_broker_cost_refused_not_executable=14`;
  - `candidate_generated_not_scheduler_selected=37`;
  - `candidate_generated_selector_reduce_risk_not_scheduler_selected=1`;
  - `source_axis_selected_package_bridge_materialized_pair_broadcast_lifecycle_context_source_window_missing_pending_created_proxy_only=298`;
  - `source_axis_selected_package_bridge_materialized_no_lifecycle_label_context=164`;
  - `redesign_repair_axis_not_executable_generator_authority=144`;
  - `selected_package_lifecycle_context_without_current_replay_source_materialization=86`.

Next blocker after B3 local proof: run the hostile five-day B7.2 window under
V218 code and classify whether full-risk promotion helps, hurts, or exposes the
next scheduler/lifecycle/source-window transfer leak. Do not judge the full
million-R reservoir from this two-day smoke.

## Verification

- `py_compile`: passed for touched module/test and route builder/verifier/analyzers.
- Focused full-risk expression pytest cluster: `10 passed`.
- Replay harness status: `broad_live_as_if_replay_materialized_broker_live_closed`.
- Flow diagnostics: written, `bucket_row_count=283`.
- Source-bound parity: written, `2942` parity rows and `1101` leakage bucket rows.
- Route builder: manifest bound to V218 quality parity and V211 holdout gate.
- Route verifier: `ok=true`, `issue_count=0`, verified UTC
  `2026-07-09T17:06:25Z`.
- Route artifact audit: `ok=true`, `missing_required=[]`,
  `missing_warnings=[]`.
- Prompt hardening: `ok=true`.

Broker/live/final remain closed.
