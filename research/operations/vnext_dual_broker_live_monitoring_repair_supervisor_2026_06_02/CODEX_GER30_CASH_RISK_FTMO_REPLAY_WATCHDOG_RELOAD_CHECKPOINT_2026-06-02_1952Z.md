# Codex GER30 Cash-Risk, FTMO Replay, And Watchdog Reload Checkpoint - 2026-06-02 19:52Z

## Scope

- Manual broker/order/position/deal mutation: none.
- Reload scope: redacted_account `run_agent.py` fleet and FTMO dual-broker execution follower.
- MT5 terminal restart: not performed; both MT5 terminal processes stayed up.

## Defects Repaired

1. GER30/GER40 live sizing used static tick-value metadata and recorded intended budget as `cash_risk_amount`.
   - Repair: live/vNext selected-cell sizing now uses broker `order_calc_profit` cash loss from entry to SL.
   - Persisted risk now records broker-verified cash risk, source/status, per-lot cash risk, and sizing diagnostics.
   - Live selected-cell entry fails closed when broker cash-risk geometry is unavailable.

2. FTMO failed-intent replay could become a late market-entry backfill.
   - Repair: recent retryable misses can retry inside the live recovery window.
   - Stale market-entry intents outside the window are audited skips, not fresh orders.
   - Closed or unproven source records fail closed.

3. Overlapping watchdog invocations created duplicate redacted_account `run_agent.py` workers during reload.
   - Immediate repair: stopped 20 duplicate workers and kept one lock-owned worker per symbol.
   - Durable repair: `scripts/watchdog.ps1` now takes a namespace-scoped single-instance file lock before launch loops.

## Verification

- `python -m pytest tests\test_execution.py tests\test_limit_order_flow.py tests\test_dual_broker_execution_follower.py tests\test_slippage_shadow_logger.py tests\test_start_all_runtime_contract.py -q`
  - `206 passed`
- `python -m pytest tests\test_start_all_runtime_contract.py -q`
  - `15 passed`
- PowerShell parse check for `scripts\watchdog.ps1`
  - passed
- `python scripts\generate_live_state.py`
  - regenerated `.context\LIVE_STATE.md` at `2026-06-02T19:52:30Z`
- `python research\operations\vnext_dual_broker_live_monitoring_repair_supervisor_2026_06_02\verify_dual_supervisor_checkpoint.py`
  - `PASS`, `failure_count=0`

## Live State After Repair

- redacted_account `run_agent.py`: 24
- Duplicate redacted_account run_agent symbols: none
- redacted_account tick capture: 24
- FTMO execution follower: 1
- Dual trade-record projector: 1
- FTMO full run_agent fleet: 0
- MT5 terminals: 2
- Free memory: about `2780.96 MB`, `33.95%`

## FTMO Replay Outcome

On restart, the follower found six reprocessable failed/stale intents and did not late-open any of them.

GER40/GER30 specifically was recorded as:

- event: `market_intent_reprocess_failed_retry_skipped_source_not_open`
- source record status: `source_record_terminal`
- source terminal exit time: `2026-06-02T18:50:22+00:00`

The corrected follower did not create a late FTMO GER40/GER30 position.
