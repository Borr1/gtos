#!/usr/bin/env python3
"""Chair pull of stale gold BUY_LIMIT 180155576. Owner word 2026-09-01 ~05:26 ICT."""
import json
import MetaTrader5 as mt5

TERM = r"C:\MT5\FTMO\terminal64.exe"
TICKET = 180155576
LIVE_LOGIN = 0
MAGIC = 0

def main() -> int:
    if not mt5.initialize(path=TERM):
        print(json.dumps({"ok": False, "error": "INIT_FAIL", "detail": str(mt5.last_error())}))
        return 3
    try:
        acc = mt5.account_info()
        if acc is None or int(acc.login) != LIVE_LOGIN:
            print(json.dumps({"ok": False, "error": "WRONG_LOGIN", "login": None if acc is None else int(acc.login)}))
            return 4
        ords = mt5.orders_get(ticket=TICKET)
        if not ords:
            leftover = mt5.orders_get() or []
            print(json.dumps({
                "ok": True,
                "already_gone": True,
                "ticket": TICKET,
                "pending_after": [int(o.ticket) for o in leftover],
                "open": len(mt5.positions_get() or []),
                "balance": float(acc.balance),
            }))
            return 0
        o = ords[0]
        req = {
            "action": mt5.TRADE_ACTION_REMOVE,
            "order": TICKET,
            "magic": int(getattr(o, "magic", 0) or MAGIC),
            "comment": "chair_pull_stale",
        }
        r = mt5.order_send(req)
        acc2 = mt5.account_info()
        leftover = mt5.orders_get() or []
        pos = mt5.positions_get() or []
        print(json.dumps({
            "ok": bool(r and r.retcode == mt5.TRADE_RETCODE_DONE),
            "retcode": None if r is None else int(r.retcode),
            "retcode_comment": None if r is None else r.comment,
            "ticket": TICKET,
            "symbol": o.symbol,
            "price": float(o.price_open),
            "sl": float(o.sl or 0),
            "pending_after": [{"ticket": int(x.ticket), "symbol": x.symbol, "price": float(x.price_open)} for x in leftover],
            "open": len(pos),
            "balance": float(acc2.balance) if acc2 else None,
            "equity": float(acc2.equity) if acc2 else None,
        }))
        return 0 if r and r.retcode == mt5.TRADE_RETCODE_DONE else 1
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    raise SystemExit(main())
