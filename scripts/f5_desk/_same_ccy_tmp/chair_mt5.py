"""Thin MT5 I/O for the F5 chair desk. No observation math lives here.

Importing this module does not initialize the terminal. ``snapshot()`` is the
only read entry. Mutating helpers are risk-reducing and validate through
``chair_card.tighten_allowed`` before they touch a ticket.
"""
from __future__ import annotations

import time
from typing import Any

MAGIC = 0
LOGIN = 0
MT5_PATH = r"C:\MT5\FTMO\terminal64.exe"


def _mt5():
    import MetaTrader5 as mt5
    return mt5


def snapshot(*, path: str = MT5_PATH, orig_ledger: dict | None = None) -> dict[str, Any]:
    """One init, one read, one shutdown. Returns a chair_observe snapshot."""
    mt5 = _mt5()
    if not mt5.initialize(path=path):
        raise RuntimeError(f"INIT_FAIL {mt5.last_error()}")
    try:
        acct = mt5.account_info()
        if acct is None:
            raise RuntimeError(f"NO_ACCOUNT {mt5.last_error()}")
        positions = []
        ticks: dict[str, dict[str, Any]] = {}
        now = time.time()
        for pos in mt5.positions_get() or []:
            if int(getattr(pos, "magic", 0) or 0) != MAGIC:
                continue
            side = "LONG" if int(pos.type) == 0 else "SHORT"
            tick = mt5.symbol_info_tick(pos.symbol)
            mark = None
            t_unix = None
            if tick is not None:
                mark = float(tick.bid) if side == "LONG" else float(tick.ask)
                t_unix = float(getattr(tick, "time", 0) or 0) or None
                ticks[pos.symbol] = {"mark": mark, "time_unix": t_unix}
            comment = str(getattr(pos, "comment", "") or "")
            sleeve = comment.split(":", 1)[-1] if ":" in comment else comment
            positions.append({
                "ticket": int(pos.ticket),
                "symbol": pos.symbol,
                "sleeve": sleeve,
                "side": side,
                "lots": float(pos.volume),
                "entry": float(pos.price_open),
                "sl": float(pos.sl or 0) or None,
                "tp": float(pos.tp or 0) or None,
                "profit": float(pos.profit),
                "mark": mark,
            })
        _ORDER_NAMES = {
            2: "BUY_LIMIT", 3: "SELL_LIMIT", 4: "BUY_STOP", 5: "SELL_STOP",
            6: "BUY_STOP_LIMIT", 7: "SELL_STOP_LIMIT",
        }
        orders = []
        for order in mt5.orders_get() or []:
            if int(getattr(order, "magic", 0) or 0) != MAGIC:
                continue
            otype = int(order.type)
            comment = str(getattr(order, "comment", "") or "")
            sleeve = comment.split(":", 1)[-1] if ":" in comment else comment
            orders.append({
                "ticket": int(order.ticket),
                "symbol": order.symbol,
                "type": otype,
                "type_name": _ORDER_NAMES.get(otype, str(otype)),
                "price": float(order.price_open),
                "comment": comment,
                "sleeve": sleeve,
                "side": "LONG" if otype in (0, 2, 4, 6) else "SHORT",
            })
        return {
            "account": {
                "login": int(acct.login),
                "balance": float(acct.balance),
                "equity": float(acct.equity),
            },
            "positions": positions,
            "orders": orders,
            "ticks": ticks,
            "orig_ledger": orig_ledger or {},
            "now_unix": now,
        }
    finally:
        mt5.shutdown()
