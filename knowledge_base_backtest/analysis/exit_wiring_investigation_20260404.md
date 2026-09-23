# Exit Wiring Investigation — 2026-04-04

## Q1: Code flow after open_trade() succeeds

**(c) Both — continues evaluating candles AND monitors trade.**

After `_process_candle()` returns (which calls `open_trade()`), the orchestrator's `_main_loop()` immediately calls `self.execution.check_and_manage_trade({})` on the same iteration (orchestrator.py:201). On subsequent iterations:
- During KZ: processes candles AND checks trade (lines 198, 200-201)
- Between KZs: checks trade + timeout trailing every ~60s (lines 204-207)
- After all KZs: checks trade + timeout trailing every 60s (lines 216-219)

## Q2: Position closure detection

`execution.check_and_manage_trade()` (execution.py:183) polls MT5 via `self.mt5.get_positions("XAUUSD")` and looks for the position by ticket number. Called from the orchestrator's main loop at each M15 candle close and during idle polling (~60s intervals).

If the position is not found: returns `"broker_closed"`, sets `self.active_trade = None`.

For TP hits: gets current tick via `self.mt5.get_tick("XAUUSD")`, compares price to TP levels, executes partial/full close via `safe_place_order`.

## Q3: Partial close vs full close differentiation

**Config-gated:** `tp1_close_pct` in config (default 100 = full close at TP1).

- When tp1_close_pct=100 (current): Full close at TP1. `_execute_tp1_partial` sends a market order for `trade.current_volume`, sets `active_trade = None`, returns `"tp1_full_close"`.
- When tp1_close_pct<100 (future): Closes fraction, discovers new ticket from MT5, tracks volume via `trade.current_volume = our_positions[0].volume`. TP2 closes another 25%. Runner continues.

Lot tracking: `TradeState.current_volume` updated after each partial close. `TradeState.initial_volume` preserved. `TradeState.partial_close_events` list tracks each event with type, time, price, volume_closed.

## Q4: Session timeout close

`_manage_timeout_trailing()` (orchestrator.py:574):
1. Calls `execution.handle_timeout_trailing()` — moves SL to breakeven
2. If 2 hours past last KZ end: calls `execution.close_position("timeout_2h")`

`close_position()` sends a market order for `trade.current_volume`, sets `active_trade = None`. Exit type is the `reason` parameter ("timeout_2h").

The close result has `result.price` (actual fill price) but this is only logged, not stored on TradeState.

## Q5: Crash recovery

`execution.reconcile_on_startup()` (execution.py:465):
1. Checks for execution checkpoint file (orphan order in flight)
2. Polls MT5 for open positions
3. If orphan position found (MT5 has position but `active_trade` is None): creates a new TradeState from position data (ticket, direction, entry_price, SL/TP, volume)
4. If phantom (we have active_trade but MT5 has no position): clears active_trade

**Trade record reconnection NOT currently implemented.** The orchestrator doesn't reconnect `_active_trade_record` to the adopted orphan. The adopted trade gets a synthetic trade_id like `"adopted_0"`.

**Recovery path for exit wiring:** Save `_active_trade_record_path` in crash data. On restart, if an orphan is adopted AND a matching trade record exists, reload the record and continue tracking.

## Q6: Price data during trade monitoring

**Real-time bid/ask from MT5** via `self.mt5.get_tick("XAUUSD")` — called inside `check_and_manage_trade()` (execution.py:208). Returns current bid and ask prices.

**Check frequency:** Varies:
- During KZ: every M15 candle close (~15 min intervals)
- Between/after KZs: every ~60 seconds (interruptible sleep)

So MFE/MAE resolution is ~60s at best, ~15min during active KZ. Using tick data (not candle OHLC) since real-time prices are available at each check point.
