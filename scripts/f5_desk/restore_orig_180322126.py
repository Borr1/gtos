import json
import MetaTrader5 as mt5
TERM = r"C:\MT5\FTMO\terminal64.exe"
TICKET = 180322126
LIVE_LOGIN = 0
ORIG = 4418.26
if not mt5.initialize(path=TERM):
    print(json.dumps({"ok": False, "error": "INIT", "detail": str(mt5.last_error())}))
    raise SystemExit(3)
try:
    acc = mt5.account_info()
    if acc is None or int(acc.login) != LIVE_LOGIN:
        print(json.dumps({"ok": False, "error": "WRONG_LOGIN"}))
        raise SystemExit(4)
    pos = mt5.positions_get(ticket=TICKET)
    if not pos:
        print(json.dumps({"ok": False, "error": "NOT_OPEN"}))
        raise SystemExit(5)
    p = pos[0]
    live_sl = float(p.sl or 0)
    tp = float(p.tp or 0)
    out = {"ticket": TICKET, "entry": float(p.price_open), "live_sl_before": live_sl, "orig": ORIG, "tp": tp, "mark": float(p.price_current), "pnl": float(p.profit)}
    if abs(live_sl - ORIG) < 0.01:
        out["ok"] = True
        out["already_orig"] = True
        print(json.dumps(out))
        raise SystemExit(0)
    r = mt5.order_send({"action": mt5.TRADE_ACTION_SLTP, "position": TICKET, "symbol": p.symbol, "sl": ORIG, "tp": tp})
    pos2 = mt5.positions_get(ticket=TICKET)
    out["ok"] = bool(r and r.retcode == mt5.TRADE_RETCODE_DONE)
    out["retcode"] = None if r is None else int(r.retcode)
    out["comment"] = None if r is None else r.comment
    out["live_sl_after"] = None if not pos2 else float(pos2[0].sl or 0)
    print(json.dumps(out))
finally:
    mt5.shutdown()
