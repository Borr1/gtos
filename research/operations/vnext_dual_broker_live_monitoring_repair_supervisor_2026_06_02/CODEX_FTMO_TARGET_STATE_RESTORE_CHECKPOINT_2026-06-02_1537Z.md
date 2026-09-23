# FTMO Target State Restore Checkpoint - 2026-06-02 15:37Z

Evidence class: `DUAL_BROKER_VPS_LIVE_RUNTIME_DATA_BROKER_PROCESS_REPAIR_SUPERVISION`

Runtime boundary: code reload and target-state persistence only. No manual broker order, deal, or position mutation was performed.

## Defect

The FTMO follower could recover target positions after restart through generic orphan adoption without the original vNext `TradeState`. For positions that had already reached TP1, the only available fallback could be an old action-log snapshot from before TP1. BTCUSD exposed the defect: the restarted follower treated residual FTMO volume as if TP1 had not happened and repeatedly attempted a second `partial_be_runner` TP1 close, which MT5 rejected with `Invalid volume`.

## Repair

- Persist active target `TradeState` snapshots in `pipeline_state\operator_profile\dual_broker_target_trade_state.json`.
- Restore target state by broker ticket on follower startup, preferring the compact store and falling back to action-log snapshots for pre-store deployments.
- Sync restored state against broker ticket, current volume, SL, and TP before management.
- Infer `tp1_hit=true` when broker reality shows residual volume or BE SL for a vNext runner, preventing duplicate TP1 close attempts after restart.
- Record `target_trade_state_path` and `target_active_trade_count` in the follower checkpoint.

## Verification

- `python -m py_compile scripts\dual_broker_execution_follower.py` passed.
- `python -m pytest tests\test_dual_broker_execution_follower.py -q` passed: `20 passed`.
- Corrected FTMO follower relaunched at `2026-06-02T15:31:27Z`, PID `5828`.
- Post-relaunch action log check from `2026-06-02T15:31:27Z`: `0` TP1 invalid-volume rows.
- Target state active symbols: `BTCUSD`, `GBPJPY`, `JP225`, `NAS100`, `NZDUSD`, `UK100`, `USDCAD`, `USDJPY`, `XAUUSD`.
- BTCUSD target state: ticket `155108232`, initial volume `0.23`, current volume `0.11`, `tp1_hit=true`, `sl_at_breakeven=true`, policy `partial_be_runner`.

## Live Shape

Post-check process/memory scan: 2 MT5 terminals, 24 redacted_account `run_agent.py`, 0 FTMO `run_agent.py`, 0 unscoped `run_agent.py`, 1 FTMO follower, 1 projector, 24 tick captures, 1 M1 capture, 1 notification worker. Free physical memory was about `1699.88 MB`.

Current architecture remains one full redacted_account selector/orchestrator fleet plus a lightweight FTMO execution follower. This checkpoint fixes restart lifecycle correctness for the follower; it does not add a duplicate FTMO brain.
