#!/usr/bin/env python3
"""Restore orig SL 4462.78 on XAU SHORT 180274922. Chair word LEAVE orig."""
import json
import MetaTrader5 as mt5

TERM = r"C:\MT5\FTMO\terminal64.exe"
TICKET = 180274922
LIVE_LOGIN = 0
ORIG = 4462.78

def main() -> int:
    if not mt5.initialize(path=TERM):
        print(json.dumps({"ok": False, "error": "INIT_FAIL", "detail": str(mt5.last_error())}))
        return 3
    try:
        acc = mt5.account_info()
        if acc is None or int(acc.login) != LIVE_LOGIN:
            print(json.dumps({"ok": False, "error": "WRONG_LOGIN", "login": None if acc is None else int(acc.login)}))
            return 4
        pos = mt5.positions_get(ticket=TICKET)
        if not pos:
            print(json.dumps({"ok": False, "error": "NOT_OPEN", "ticket": TICKET}))
            return 5
        p = pos[0]
        live_sl = float(p.sl or 0)
        tp = float(p.tp or 0)
        out = {
            "ticket": TICKET,
            "symbol": p.symbol,
            "side": "SHORT" if int(p.type) == 1 else "LONG",
            "entry": float(p.price_open),
            "volume": float(p.volume),
            "live_sl_before": live_sl,
            "orig": ORIG,
            "tp": tp,
            "mark": float(p.price_current),
            "profit": float(p.profit),
        }
        if abs(live_sl - ORIG) < 0.01:
            out["ok"] = True
            out["already_orig"] = True
            print(json.dumps(out))
            return 0
        req = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": TICKET,
            "symbol": p.symbol,
            "sl": ORIG,
            "tp": tp,
        }
        r = mt5.order_send(req)
        pos2 = mt5.positions_get(ticket=TICKET)
        p2 = pos2[0] if pos2 else None
        out["ok"] = bool(r and r.retcode == mt5.TRADE_RETCODE_DONE)
        out["retcode"] = None if r is None else int(r.retcode)
        out["retcode_comment"] = None if r is None else r.comment
        out["live_sl_after"] = None if p2 is None else float(p2.sl or 0)
        print(json.dumps(out))
        return 0 if out["ok"] else 1
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    raise SystemExit(main())
