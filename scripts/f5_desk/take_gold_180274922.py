import json
import MetaTrader5 as mt5

TERM = r"C:\MT5\FTMO\terminal64.exe"
TICKET = 180274922
LIVE_LOGIN = 0

def main() -> int:
    if not mt5.initialize(path=TERM):
        print(json.dumps({"ok": False, "error": "INIT", "detail": str(mt5.last_error())}))
        return 3
    try:
        acc = mt5.account_info()
        if acc is None or int(acc.login) != LIVE_LOGIN:
            print(json.dumps({"ok": False, "error": "WRONG_LOGIN"}))
            return 4
        pos = mt5.positions_get(ticket=TICKET)
        if not pos:
            print(json.dumps({"ok": False, "error": "NOT_OPEN", "ticket": TICKET}))
            return 5
        p = pos[0]
        vol = float(p.volume)
        req = {
            "action": mt5.TRADE_ACTION_DEAL,
            "position": TICKET,
            "symbol": p.symbol,
            "volume": vol,
            "type": mt5.ORDER_TYPE_BUY if int(p.type) == 1 else mt5.ORDER_TYPE_SELL,
            "deviation": 30,
            "magic": int(p.magic) or 0,
            "comment": "chair_take_mfe",
        }
        r = mt5.order_send(req)
        acc2 = mt5.account_info()
        still = mt5.positions_get(ticket=TICKET)
        print(json.dumps({
            "ok": bool(r and r.retcode == mt5.TRADE_RETCODE_DONE),
            "retcode": None if r is None else int(r.retcode),
            "comment": None if r is None else r.comment,
            "deal": None if r is None else int(getattr(r, "deal", 0) or 0),
            "price": None if r is None else float(getattr(r, "price", 0) or 0),
            "entry": float(p.price_open),
            "sl": float(p.sl or 0),
            "vol": vol,
            "pnl_before": float(p.profit),
            "still_open": bool(still),
            "bal": None if acc2 is None else float(acc2.balance),
            "eq": None if acc2 is None else float(acc2.equity),
        }))
        return 0 if r and r.retcode == mt5.TRADE_RETCODE_DONE else 1
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    raise SystemExit(main())
