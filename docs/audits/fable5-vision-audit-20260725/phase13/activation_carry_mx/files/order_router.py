"""order_router — turn a sized W7 book unit + its TradeIntent into a real FTMO order via the
FULL V4 route (the only live-order path; the plain route is blocked at execution.py:2689).

Per realized unit: resolve the live entry geometry from the broker tick, build the broker-real
account_state for the prop-firm headroom snapshot (SAME tick as the order — the <=900s rule),
assemble the 42-key V4 trade_params (execution_packets.build_book_trade_params), and call
ExecutionEngine.open_trade (which builds the pretrade cost model from the tick, runs the 3 fail-closed
gates, and places the order). open_trade inherits the runtime-halt guard, so while halted nothing
sends. Verified [RAN] (tests/ultimate_book/test_order_route.py): the trade_params clears all 3 gates.

SizedUnit has no symbol/direction/stop -> the caller pairs each realized unit with its TradeIntent(s)
(a cluster unit with n_trades>1 places one order per intent at the unit's risk_pct_per_trade).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from . import execution_packets as EP


class UltimateBookOrderRouter:
    def __init__(self, config: dict, namespace: str = "operator_profile",
                 frontier_exits: tuple = ()):
        self.config = config or {}
        self.namespace = namespace
        # The frontier-exit sleeve selection (Session AU, B1550). An EXPLICIT constructor argument
        # and NOT a config key, deliberately, following `--recover-pre-gap-bar` rather than
        # `--vol-level-tilt`: this flag is consumed here, on the placement path, so it never reaches
        # `bridge._bool` and therefore cannot produce the KeyError-against-DEFAULT_CONFIG failure AR
        # measured -- an armed book standing down every tick with a healthy heartbeat. A key that is
        # never read cannot be read wrong. Pinned by
        # `test_frontier_exit_contracts.py::test_the_selection_is_not_a_config_key_anywhere`.
        self.frontier_exits = tuple(frontier_exits or ())

    # ---- live account_state for the prop-firm headroom snapshot ----
    def account_state(self, mt5, *, day_start_baseline: float, reset_window_id: str,
                      account_login: Optional[int] = None) -> Optional[dict]:
        try:
            equity = float(mt5.get_account_equity())
            balance = float(mt5.get_account_balance())
        except Exception:
            return None
        if equity <= 0 or balance <= 0:
            return None
        login = account_login
        if login is None:
            login = (self.config.get("deployment", {}) or {}).get("mt5_login") or 0
        return {
            "current_equity": equity, "balance": balance, "account_login": login,
            "day_start_equity_or_balance_baseline": float(day_start_baseline),
            "daily_reset_window_id": reset_window_id,
        }

    # ---- entry geometry from the live tick ----
    def _geometry(self, intent, tick) -> Optional[dict]:
        d = int(intent.direction)
        sign = 1.0 if d > 0 else -1.0
        bid = getattr(tick, "bid", None)
        ask = getattr(tick, "ask", None)
        if not bid or not ask:
            return None
        entry = float(ask if d > 0 else bid)               # cross the spread on entry
        rd = float(intent.stop_dist)
        if rd <= 0:
            return None
        target_dist = float(
            getattr(intent, "target_dist", None)
            or (EP.DEFAULT_EXIT_PROFILE["final_target_r"] * rd)
        )
        return {
            "entry_price": entry, "risk_distance": rd,
            "stop_loss": entry - sign * rd, "take_profit_1": entry + sign * target_dist,
        }

    def build_trade_params(self, sized_unit, intent, tick, account_state) -> Optional[dict]:
        geom = self._geometry(intent, tick)
        if geom is None:
            return None
        return EP.build_book_trade_params(sized_unit, intent, geom, account_state,
                                          profile_namespace=self.namespace,
                                          frontier_exits=self.frontier_exits)

    # ---- placement (open_trade builds the cost model + runs the 3 gates + sends) ----
    def place(self, execution_engine, sized_unit, intent, tick, account_state,
              account_balance: float) -> dict:
        """Returns {placed, trade_state, reason}. NEVER raises; the book is best-effort."""
        try:
            tp = self.build_trade_params(sized_unit, intent, tick, account_state)
            if tp is None:
                return {"placed": False, "trade_state": None, "reason": "geometry_unavailable"}
            ts = execution_engine.open_trade(
                tp, account_balance, risk_pct_override=tp["risk_pct_override"],
                trigger="ultimate_book")
            placed = ts is not None and getattr(ts, "ticket", None) not in (None, 0)
            reason = "ok"
            if not placed:
                # surface the SPECIFIC block reason open_trade recorded (vnext_policy:* / no_tick_data /
                # runtime_halt_blocked / an order_send diagnostic status) instead of the opaque
                # "open_trade_returned_none" -- so the Telegram card + log show WHY a leg did not place.
                reason = getattr(execution_engine, "_last_open_trade_block_reason", None)
                if not reason:
                    diag = getattr(execution_engine, "_last_order_send_diagnostic", None)
                    reason = (diag.get("status") if isinstance(diag, dict) else None) or "open_trade_returned_none"
            return {"placed": placed, "trade_state": ts, "reason": reason,
                    "candidate_id": tp.get("candidate_id"), "trade_params": tp}
        except Exception as e:   # the book NEVER breaks the live path
            return {"placed": False, "trade_state": None, "reason": f"router_exception:{e!r}"}
