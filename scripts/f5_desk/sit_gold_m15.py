import json
from datetime import datetime, timezone
import MetaTrader5 as mt5

TERM = r"C:\MT5\FTMO\terminal64.exe"
TICKET = 180274922
if not mt5.initialize(path=TERM):
    print(json.dumps({"ok": False, "error": str(mt5.last_error())}))
    raise SystemExit(3)
try:
    acc = mt5.account_info()
    pos = mt5.positions_get(ticket=TICKET)
    tick = mt5.symbol_info_tick("XAUUSD")
    rates = mt5.copy_rates_from_pos("XAUUSD", mt5.TIMEFRAME_M15, 0, 8)
    bars = []
    if rates is not None:
        for r in rates:
            bars.append({
                "t_utc": datetime.fromtimestamp(int(r["time"]), tz=timezone.utc).strftime("%H:%M"),
                "o": float(r["open"]),
                "h": float(r["high"]),
                "l": float(r["low"]),
                "c": float(r["close"]),
                "v": int(r["tick_volume"]),
            })
    out = {
        "login": None if acc is None else int(acc.login),
        "bal": None if acc is None else float(acc.balance),
        "eq": None if acc is None else float(acc.equity),
        "bid": None if tick is None else float(tick.bid),
        "ask": None if tick is None else float(tick.ask),
        "m15": bars,
    }
    if pos:
        p = pos[0]
        entry = float(p.price_open)
        orig = 4462.78
        tp = float(p.tp or 0)
        mark = float(p.price_current)
        r_orig = abs(entry - orig)
        mfe_low = min((b["l"] for b in bars), default=None)
        out["pos"] = {
            "entry": entry,
            "sl": float(p.sl or 0),
            "tp": tp,
            "vol": float(p.volume),
            "mark": mark,
            "pnl": float(p.profit),
            "r_live": None if r_orig == 0 else round((entry - mark) / r_orig, 2),
        }
        out["mfe_bar_low"] = mfe_low
    else:
        out["pos"] = None
    print(json.dumps(out))
finally:
    mt5.shutdown()
