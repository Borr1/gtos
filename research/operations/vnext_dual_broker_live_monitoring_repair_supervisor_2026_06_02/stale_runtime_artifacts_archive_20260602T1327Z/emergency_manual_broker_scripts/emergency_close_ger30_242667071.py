from __future__ import annotations

import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import MetaTrader5 as mt5


TICKET = 242667071
EXPECTED_SYMBOLS = {"GER30", "GER40", "GER30.cash", "GER40.cash"}
TERMINAL_PATH = r"C:\Program Files\MetaTrader 5\terminal64.exe"
DEVIATION = 50
MAGIC = 24052026


def _snapshot(obj):
    if obj is None:
        return None
    if hasattr(obj, "_asdict"):
        return obj._asdict()
    return str(obj)


def _jsonish(value):
    import json

    print(json.dumps(value, sort_keys=True, default=str))


def _position_by_ticket(ticket: int):
    positions = mt5.positions_get(ticket=ticket)
    if positions is None:
        raise RuntimeError(f"positions_get failed: {mt5.last_error()}")
    if len(positions) == 0:
        return None
    if len(positions) > 1:
        raise RuntimeError(f"ticket lookup returned {len(positions)} positions")
    return positions[0]


def _close_request(position):
    symbol = str(position.symbol)
    if symbol not in EXPECTED_SYMBOLS:
        raise RuntimeError(f"refusing to close unexpected symbol for ticket {TICKET}: {symbol}")

    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        raise RuntimeError(f"symbol_info_tick failed for {symbol}: {mt5.last_error()}")

    position_type = int(position.type)
    if position_type == mt5.POSITION_TYPE_BUY:
        order_type = mt5.ORDER_TYPE_SELL
        price = float(tick.bid)
    elif position_type == mt5.POSITION_TYPE_SELL:
        order_type = mt5.ORDER_TYPE_BUY
        price = float(tick.ask)
    else:
        raise RuntimeError(f"unknown position type for ticket {TICKET}: {position_type}")

    symbol_info = mt5.symbol_info(symbol)
    filling_mode = mt5.ORDER_FILLING_IOC
    if symbol_info is not None:
        raw_filling = getattr(symbol_info, "filling_mode", None)
        if raw_filling in (mt5.ORDER_FILLING_FOK, mt5.ORDER_FILLING_IOC, mt5.ORDER_FILLING_RETURN):
            filling_mode = raw_filling

    return {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": float(position.volume),
        "type": order_type,
        "position": int(position.ticket),
        "price": price,
        "deviation": DEVIATION,
        "magic": MAGIC,
        "comment": "closeger30",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": filling_mode,
    }


def main() -> int:
    started = datetime.now(timezone.utc).isoformat()
    if not mt5.initialize(path=TERMINAL_PATH):
        _jsonish({"event": "initialize_failed", "last_error": mt5.last_error(), "started_utc": started})
        return 2

    try:
        account = mt5.account_info()
        pos = _position_by_ticket(TICKET)
        if pos is None:
            _jsonish({
                "event": "position_already_absent",
                "ticket": TICKET,
                "account": _snapshot(account),
                "started_utc": started,
            })
            return 0

        request = _close_request(pos)
        _jsonish({
            "event": "close_request_prepared",
            "ticket": TICKET,
            "position": _snapshot(pos),
            "request": request,
            "account": _snapshot(account),
            "started_utc": started,
        })

        result = mt5.order_send(request)
        _jsonish({
            "event": "close_order_send_result",
            "ticket": TICKET,
            "result": _snapshot(result),
            "last_error": mt5.last_error(),
            "time_utc": datetime.now(timezone.utc).isoformat(),
        })

        if result is None:
            return 3
        retcode = int(getattr(result, "retcode", 0) or 0)
        if retcode not in (mt5.TRADE_RETCODE_DONE, mt5.TRADE_RETCODE_DONE_PARTIAL):
            return 4

        for attempt in range(10):
            time.sleep(0.5)
            remaining = _position_by_ticket(TICKET)
            if remaining is None:
                _jsonish({
                    "event": "position_closed_verified",
                    "ticket": TICKET,
                    "verify_attempt": attempt + 1,
                    "time_utc": datetime.now(timezone.utc).isoformat(),
                })
                return 0
            _jsonish({
                "event": "position_still_present_after_close_attempt",
                "ticket": TICKET,
                "verify_attempt": attempt + 1,
                "position": _snapshot(remaining),
                "time_utc": datetime.now(timezone.utc).isoformat(),
            })
        return 5
    finally:
        mt5.shutdown()


if __name__ == "__main__":
    sys.exit(main())
