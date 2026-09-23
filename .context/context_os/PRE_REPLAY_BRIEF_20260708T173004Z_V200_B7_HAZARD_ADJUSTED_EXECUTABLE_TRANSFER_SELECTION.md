# V200 B7 Hazard-Adjusted Executable Transfer Selection Pre-Replay Brief

Broker/live/final remain closed. This is a local replay/package proof batch.

## Current Completed Replay

- Latest completed replay: `BROAD_LIVE_AS_IF_REPLAY_V199_B7_STOP_PRESSURE_RISK_TRANSFER_SOFT_PENALTY_20260513_20260517_TARGETED`.
- Window: `2026-05-13..2026-05-17`.
- Symbols: `XAUUSD USDJPY XAGUSD GER40 NAS100 SPX500 UK100 AUDUSD US30_cash`.
- Candidate / scorecard / order / headline trades: `14384 / 288 / 154 / 67`.
- W/L/F: `37/30/0`.
- Net/gross/final R: `-6.48266227 / -1.51201107 / -1.51201107`.
- Cash PnL: `-3276.73133579`.
- Expired unfilled: `3`.
- Executed broker-cost REFUSED/source-gap rows: `0/0`.

Same-symbol comparison versus V198:

- V198 same-symbol subset: `63` trades, `37/26/0`, net `-2.59265384R`.
- V199 delta: `+4` trades, `-3.89000843R`.
- Added trades: `7`, net `-5.86387023R`; six were stop-loss losers, net `-6.45900147R`.
- Removed trades: `3`, net `-1.97386180R`.
- V199 did not win by suppression. It reallocated into worse stop-pressure-heavy paths.

## Current Process State

- No broad replay is running.
- V199 completed and artifacts exist.
- No V200 replay has been started before this brief.

## Fable Matrix State

- B0-B6: closed or conditionally closed by prior focused artifacts in the saved Fable matrix.
- B7: PARTIAL. V198 failed hostile five-day value-transfer; V199 failed targeted behavior improvement.
- B8: OPEN. Broker/live/final stay false.

## Subagent Findings

- Meitner: INCORPORATED. V198 risk-expression/full-risk transfer was material; full tier and `risk_decision=trade` were net negative while reduced/open-reduced rows were positive.
- Pascal: INCORPORATED. V92/V97 removed winners are still candidates/missed, not candidate-generation losses; dominant removed-winner blocker is cost authority, with residual cost-passed rows blocked before scorecard/order.
- Kuhn: PENDING. Stop/exit lane did not return before V200 patch selection.
- Mencius/Copernicus/Gibbs: PENDING. New V199 delta, risk-expression, and B6 cost-authority lanes are running.

## Root Mismatch

V199 made the stop-pressure signal visible but not first-order. The soft-penalty reason appears in:

- scorecard rows: `205`;
- order rows: `131`;
- trade rows: `57`;
- missed rows: `516`.

But hard-dominance selection sorted by raw expected-transfer score before reallocation quality. Therefore the six added stop-loss losers still won when their raw expected-transfer score was high.

## Patch

Files changed:

- `src/research/moonshot_scheduler_v4_best_trade_allocator.py`
- `tests/test_moonshot_scheduler_v4_best_trade_allocator.py`

Repair:

- Add `_option_executable_transfer_selection_score()`.
- It returns the lower of raw expected-transfer score and risk/guard-adjusted reallocation-quality score.
- Use it as the first key for hard-dominance selection and same-window executable comparator diagnostics.
- Preserve raw expected-transfer score separately for audit.
- Keep broker-cost REFUSED/source-gap rows non-executable.
- Do not top-N narrow, hard block by date/symbol/session, or suppress all trades.

Focused verification passed before replay:

- `python3 -m py_compile src/research/moonshot_scheduler_v4_best_trade_allocator.py tests/test_moonshot_scheduler_v4_best_trade_allocator.py`
- `python3 -m pytest tests/test_moonshot_scheduler_v4_best_trade_allocator.py -k 'same_window_executable_comparator_hard_dominance_selects_best_transfer or same_window_hard_dominance_uses_hazard_adjusted_selection_score or reallocation_quality_penalizes_suppressed_stop_pressure_without_hard_veto' -q --tb=short`

## Expected Effect

- Candidate -> scorecard: neutral.
- Scorecard -> order: should reallocate away from high raw-score but stop-pressure-heavy candidates when a safer executable candidate has better adjusted selection score.
- Order -> fill: may shift; no broker/source-gap execution allowed.
- Missed positive/negative R: may change because demoted rows remain missed/scoreable.
- Trade count: may move modestly; zero-trade positivity is failure.
- Net/gross/final R: should improve versus V199 same targeted slice if stop-pressure was the correct current leak.
- W/L/F: added stop-loss rows should fall or be replaced by stronger non-stop paths.
- Full/reduced distribution: improvement must be attributable to better hazard-adjusted selection, not global risk suppression.

## Targeted Proof

Run:

- Prefix: `BROAD_LIVE_AS_IF_REPLAY_V200_B7_HAZARD_ADJUSTED_EXECUTABLE_TRANSFER_SELECTION_20260513_20260517_TARGETED`
- Window: `2026-05-13..2026-05-17`
- Symbols: `XAUUSD USDJPY XAGUSD GER40 NAS100 SPX500 UK100 AUDUSD US30_cash`
- Profile: `repaired_package_conversion_v3`

Helped if:

- executed REFUSED/source-gap remain `0/0`;
- net R improves versus V199 targeted `-6.48266227R`;
- added suppressed-stop-pressure stop-loss rows decrease versus V199;
- trade count does not collapse;
- improvement is from hazard-adjusted selection/reallocation, not from suppressing all opportunity.

Failed if:

- net R worsens materially;
- stop-loss count/net worsens;
- the same suppressed-stop-pressure rows still fill as before;
- improvement comes only from broad trade suppression.
