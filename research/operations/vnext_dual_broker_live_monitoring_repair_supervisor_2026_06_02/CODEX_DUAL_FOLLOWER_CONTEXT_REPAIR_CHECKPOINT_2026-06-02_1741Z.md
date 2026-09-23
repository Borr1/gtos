# Codex Dual Follower Context Repair Checkpoint - 2026-06-02 17:41 UTC

## Status

- Scope: FTMO dual-broker execution follower only.
- Manual broker/order/position mutation: none.
- Full FTMO run_agent fleet: absent by design.
- redacted_account primary fleet: still 24 run_agent processes.
- redacted_account tick capture: 24/24 after scoped GBPJPY tick-capture relaunch.
- FTMO follower: reloaded after code repair, order-enabled, single process.

## Defect Found

The redacted_account `GER40` live intent recorded at `2026-06-02T17:31:14.619128+00:00`
was consumed by the FTMO follower but rejected with:

- First retryable event: `market_intent_deferred_target_tick_unavailable` for `GER40.cash`.
- Final non-retryable event: `market_intent_missing_target_execution_context`.
- Exact context error: `selected_cell_unresolved:condition_challenger_cell_join_missing_for_broader_origin_allowlist_entry`.

The intent itself carried complete vNext execution context:

- `gtos_vnext_production_execution_path: true`
- `gtos_vnext_dynamic_policy_selected: partial_be_runner`
- `gtos_vnext_execution_policy_id: vnext_exec_partial_50_at_1r_be_runner_to_3r`
- `gtos_vnext_dynamic_policy_applied: true`
- selected cell: `STAGE13-FN-RISK-CELL-000305`
- risk pct: `0.25`
- commission status: `SELECTED_CELL_RISK_LEDGER_VERIFIED_NO_EXECUTION_CRITICAL_COMMISSION_GAP`

Root cause: the intent bus already classifies
`condition_challenger_cell_join_missing_for_broader_origin_allowlist_entry`
as a non-fatal projection unresolved reason, but the live FTMO follower's
target execution context validator still treated it as fatal.

## Repair

- `scripts/dual_broker_execution_follower.py` now filters the same non-fatal
  context unresolved reason as the canonical intent bus.
- `tests/test_dual_broker_execution_follower.py` now proves:
  - the known non-fatal projection reason is allowed when all required vNext
    context and verified commission status are present.
  - fatal execution-critical unresolved reasons remain blocked.

## Verification

- `python -m pytest tests\test_dual_broker_execution_follower.py -q`
  - `24 passed`
- `python -m pytest tests\test_dual_broker_intent_bus.py -q`
  - `12 passed`
- `python research\operations\vnext_dual_broker_live_monitoring_repair_supervisor_2026_06_02\verify_dual_supervisor_checkpoint.py`
  - `PASS`, `failure_count=0`
- Read-only dual MT5 probe after reload:
  - redacted_account: 12 positions, 0 orders, 24/24 configured symbols with positive ticks.
  - FTMO: 8 positions, 0 orders, 24/24 configured symbols found, 20 positive ticks without mass-select, 4 lazy/unselected ticks.

## Reload Evidence

- Old FTMO follower PID before reload: `3888`.
- New FTMO follower PID after scoped reload: `1016`.
- New follower heartbeat: `2026-06-02T17:40:29.976061+00:00`.
- New follower checkpoint offset: `6127172`, matching the canonical intent log end.
- New follower order-enabled: `true`.
- New follower recovered active FTMO state: 8 active target trades.
- No replay/backfill was performed for the missed `GER40` intent.

## Current Runtime Footprint After Reload

- Python live process count: 52.
- redacted_account run_agent: 24.
- redacted_account tick_capture: 24.
- M1 capture: 1.
- Notification worker: 1.
- Dual projector: 1.
- FTMO execution follower: 1.
- MT5 terminals: 2.
- FTMO run_agent count: 0.
- Unscoped run_agent count: 0.
- Free physical memory around reload verification: 1815.61 MB, 22.16%.

## Remaining Work

- Future valid intents with this non-fatal projection reason should now pass
  the follower context validator, subject to FTMO tick availability and
  account-specific drawdown/risk budget.
- The missed `GER40` intent was not replayed because it was already past the
  live retry window and replay would create a late broker action.
- Continue candidate/trade lifecycle audit, risk/profile stale-cap review, and
  scoped commit/push of this repair.
