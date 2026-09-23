# V199 B7 Stop-Pressure Risk-Transfer Soft Penalty Pre-Replay Brief

Broker/live/final remain closed. This is a local replay/package proof batch.

## Current Replay State

- Latest completed replay: `BROAD_LIVE_AS_IF_REPLAY_V198_B7_2_HOSTILE_5D_TICK_HYDRATED_CURRENT_RUNTIME_TRANSFER_POLICY_20260513_20260517_FULLGRID`.
- Window: `2026-05-13..2026-05-17`, full 24-symbol surface, tick source resolved when available.
- Candidate / scorecard / order / headline trades: `25006 / 288 / 178 / 74`.
- W/L/F: `43/31/0`; net/gross/final R: `-3.84033809 / 1.79005938 / 1.79005938`.
- Cash PnL: `-3530.29276461`; expired unfilled: `5`.
- Executed broker-cost REFUSED/source-gap rows: `0/0`.

Comparators:

- V92 hostile 5d: `51` trades, `+29.35570236R`; V198 delta `-33.19604045R`.
- V97 hostile 5d: `47` trades, `+13.89627731R`; V198 delta `-17.73661540R`.
- V126 hostile 5d: `55` trades, `-4.43962487R`; V198 delta `+0.59928678R`.

## Incorporated Findings

- Meitner: risk-expression/finalizer transfer is the current executable issue. Full tier `26 / -5.77054256R`; trade risk decision `29 / -5.28127306R`; reduced/open-reduced rows positive.
- Pascal: V92/V97 removed winners are still generated in V198 candidate-index/missed ledgers, but 0 reach scorecard/order/trade. Dominant removed-winner blocker is broker-cost REFUSED, which remains non-executable absent B6 recalibration proof.
- Local parse: stop-loss bucket is `23 / -24.96552858R`; non-stop close reasons are net positive. Stop pressure is ledgered but inert when base fragility suppresses cap/block.

## Patch

Files:

- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`
- `tests/test_moonshot_scheduler_v4_best_trade_allocator.py`

Repair:

- Keep stop-pressure-suppressed rows executable and scoreable.
- Add a causal soft guard penalty to reallocation/ranking when pressure score triggered, pressure was suppressed by base-fragility requirement, and no cap was applied.
- Do not hard-block rows, loosen broker-cost REFUSED authority, or hardcode date/symbol/session buckets.

Focused verification already passed:

- `python3 -m py_compile src/research/moonshot_scheduler_v4_best_trade_allocator.py tests/test_moonshot_scheduler_v4_best_trade_allocator.py`
- `python3 -m pytest tests/test_moonshot_scheduler_v4_best_trade_allocator.py -k 'reallocation_quality_promotes_signed_source_bound_soft_guard_candidate or reallocation_quality_penalizes_suppressed_stop_pressure_without_hard_veto or reallocation_quality_refuses_negative_signed_source_bound_soft_guard_candidate or scheduler_predecision_stop_hazard_guard_suppresses_pressure_without_base_fragility or scheduler_predecision_stop_hazard_guard_does_not_block_pressure_without_base_fragility' -q --tb=short`

## Expected Effect

- Candidate -> scorecard: neutral or small trade-set shift.
- Scorecard -> order: may reallocate away from stop-pressure-heavy cost-passed rows when stronger executable alternatives exist.
- Order -> fill: neutral.
- Missed positive/negative R: may rise because demoted rows remain scoreable missed.
- Trade count: may decrease modestly or shift; zero-trade positivity is failure.
- Net/gross/final R: should improve if stop pressure was a useful ranking signal.
- Full/reduced distribution: negative full/trade exposure should fall or be reallocated.

## Targeted Proof

Run before another broad replay:

- Window: `2026-05-13..2026-05-17`.
- Symbols: `XAUUSD USDJPY XAGUSD GER40 NAS100 SPX500 UK100 AUDUSD US30_cash`.
- Profile: `repaired_package_conversion_v3`.
- Prefix: `BROAD_LIVE_AS_IF_REPLAY_V199_B7_STOP_PRESSURE_RISK_TRANSFER_SOFT_PENALTY_20260513_20260517_TARGETED`.

Helped if REFUSED/source-gap executions remain `0/0`, stop-pressure soft penalty is visible, stop-loss net R or full/trade negative exposure improves versus the same V198 targeted slice, and trade count does not collapse.
