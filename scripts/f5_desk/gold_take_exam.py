import json
from datetime import datetime, timezone, timedelta
import MetaTrader5 as mt5
TERM = r"C:\MT5\FTMO\terminal64.exe"
LIVE_LOGIN = 0
if not mt5.initialize(path=TERM):
    print(json.dumps({"ok": False, "error": "INIT", "detail": str(mt5.last_error())}))
    raise SystemExit(3)
try:
    acc = mt5.account_info()
    if acc is None or int(acc.login) != LIVE_LOGIN:
        print(json.dumps({"ok": False, "error": "WRONG_LOGIN", "login": None if acc is None else int(acc.login)}))
        raise SystemExit(4)
    ICT = timezone(timedelta(hours=7))
    out = {
        "ok": True,
        "ts_ict": datetime.now(ICT).strftime("%Y-%m-%d %H:%M:%S ICT"),
        "login": int(acc.login),
        "balance": round(float(acc.balance), 2),
        "equity": round(float(acc.equity), 2),
        "positions": [],
        "xau": {},
    }
    for p in mt5.positions_get() or []:
        tick = mt5.symbol_info_tick(p.symbol)
        out["positions"].append({
            "ticket": int(p.ticket),
            "symbol": p.symbol,
            "type": "BUY" if p.type == 0 else "SELL",
            "vol": float(p.volume),
            "entry": float(p.price_open),
            "sl": float(p.sl or 0),
            "tp": float(p.tp or 0),
            "mark": float(p.price_current),
            "pnl": round(float(p.profit), 2),
            "bid": None if tick is None else float(tick.bid),
            "ask": None if tick is None else float(tick.ask),
        })
    def bars(sym, tf, n):
        r = mt5.copy_rates_from_pos(sym, tf, 0, n)
        if r is None:
            return []
        rows = []
        for x in r:
            t = datetime.fromtimestamp(int(x["time"]), tz=timezone.utc).astimezone(ICT)
            rows.append({
                "t": t.strftime("%H:%M"),
                "o": round(float(x["open"]), 2),
                "h": round(float(x["high"]), 2),
                "l": round(float(x["low"]), 2),
                "c": round(float(x["close"]), 2),
            })
        return rows
    out["xau"]["m1"] = bars("XAUUSD", mt5.TIMEFRAME_M1, 12)
    out["xau"]["m5"] = bars("XAUUSD", mt5.TIMEFRAME_M5, 10)
    print(json.dumps(out))
finally:
    mt5.shutdown()
