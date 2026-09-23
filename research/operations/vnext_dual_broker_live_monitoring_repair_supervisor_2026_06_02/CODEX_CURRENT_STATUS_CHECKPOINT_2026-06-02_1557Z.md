# Codex Current Status Checkpoint - 2026-06-02 15:57Z

Evidence class: `DUAL_BROKER_VPS_LIVE_RUNTIME_DATA_BROKER_PROCESS_REPAIR_SUPERVISION`

Runtime effect boundary: read-only process, MT5, target-state, and risk inspection only; no manual broker order, deal, order, or position mutation.

## Current Runtime Shape

- Current HEAD: `d9de1d6596e95b697fb3bc8bef439ce9da5b5ab0`.
- Process shape: 24 redacted_account `run_agent.py` workers, 0 FTMO `run_agent.py` workers, 1 FTMO lightweight follower, 1 dual-broker projector, 2 MT5 terminals.
- Memory: about 2049 MB free physical memory at the process checkpoint.
- This is the intended memory-conscious dual-broker architecture: one full redacted_account brain plus one FTMO execution follower. No duplicate legacy/unscoped worker fleet was observed.

## Broker Read-Only Snapshot

- redacted_account: connected, trade allowed, 13 positions, 0 orders, equity about 101441.67.
- FTMO: connected, trade allowed, 9 positions, 0 orders, equity about 98596.48.
- FTMO target state reconciliation: 9 persisted target trades match 9 broker positions. No extra broker positions and no missing target state were found.
- BTC FTMO target state is correctly restored as a partial/BE runner: initial 0.23, current 0.11, `tp1_hit=true`, `sl_at_breakeven=true`.
- Only precision-only TP differences were observed on JP225, UK100, and USDCAD; no material volume/SL/lifecycle mismatch.

## Latest FTMO Non-Follows

Two new source intents reached the FTMO follower after the corrected reload:

- `US30_cash`, intent `e1376cd3bc6279e42b525e385e1dd9a4e735fbbbaea52656605eed2099ea0f64`, source record `knowledge_base\redacted_account_live_bee34003\trade_records\US30_cash\2026-06-02_ny_1530_broadorigin_1ac119b7b5f762a511c5922d.json`.
- `ETHUSD`, intent `530e78caed3466afe91200b0a53adde75e9632414303fae3910f71f15e1d8555`, source record `knowledge_base\redacted_account_live_bee34003\trade_records\ETHUSD\2026-06-02_off_configured_session_1545_broadorigin_3a82cefc242aee6274c8f027.json`.

Both were rejected by FTMO-side aggregate budget projection:

- US30: `target_account_drawdown_budget_blocked_by:internal_daily_drawdown_overlay`, available about 2.37, requested about 244.91.
- ETH: `target_account_drawdown_budget_blocked_by:internal_daily_drawdown_overlay`, available about 2.02, requested about 122.46.

The earlier `target_tick_unavailable` deferrals did not consume the intents. Current FTMO read-only tick probe showed live ticks and visible symbols for `US30.cash`, `ETHUSD`, `BTCUSD`, `US100.cash`, and `XAUUSD`.

## Current Interpretation

Current FTMO non-follows are explained by the configured aggregate drawdown projection binding on the 4pct internal daily overlay after existing open stop-loss exposure and buffer. They are not explained by stale `max_concurrent`, namespace collision, lost target trade state, broker alias absence, or MT5 disconnection.

## Remaining Work

- Directly inspect the latest redacted_account source trade records for US30 and ETH, including dynamic policy, LTF path, selector/risk context, and execution geometry.
- Continue candidate/rejection lifecycle inspection for any new rows after this checkpoint.
- Decide, in a scoped design/implementation checkpoint, whether FTMO needs broker-local trade management separate from source-intent copying.
- Commit and push the scoped checkpoint/state repair after focused validation and diff review.
