import MetaTrader5 as mt5, json
from datetime import datetime, timezone, timedelta

mt5.initialize(path=r"C:\MT5\FTMO\terminal64.exe")
# broader window + position-specific
windows = [
    ("since_1300ICT", datetime(2026, 9, 8, 6, 0, tzinfo=timezone.utc)),
    ("since_1430ICT", datetime(2026, 9, 8, 7, 30, tzinfo=timezone.utc)),
]
to = datetime.now(timezone.utc) + timedelta(minutes=5)
out = {"now": to.isoformat(), "by_window": {}, "pos_182201750": None}
for name, frm in windows:
    deals = mt5.history_deals_get(frm, to) or []
    out["by_window"][name] = {
        "n": len(deals),
        "deals": [{
            "ticket": d.ticket, "order": d.order, "position_id": d.position_id,
            "symbol": d.symbol, "type": int(d.type), "entry": int(d.entry),
            "volume": d.volume, "price": d.price, "profit": d.profit,
            "commission": d.commission, "swap": d.swap, "magic": d.magic,
            "reason": int(d.reason), "comment": d.comment, "time": int(d.time),
            "time_ict": datetime.fromtimestamp(d.time, tz=timezone(timedelta(hours=7))).strftime("%Y-%m-%d %H:%M:%S ICT"),
        } for d in deals if d.symbol in ("XAUUSD","US30.cash","DASHUSD","GER40.cash","UK100.cash") or d.position_id in (182201750,182201752,181801554,181801555,180734064,182187173,181411441)]
    }
# try history_deals_get by position
try:
    deals_pos = mt5.history_deals_get(position=182201750) or []
    out["pos_182201750"] = [{
        "ticket": d.ticket, "order": d.order, "position_id": d.position_id,
        "symbol": d.symbol, "type": int(d.type), "entry": int(d.entry),
        "volume": d.volume, "price": d.price, "profit": d.profit,
        "commission": d.commission, "swap": d.swap, "magic": d.magic,
        "reason": int(d.reason), "comment": d.comment, "time": int(d.time),
        "time_ict": datetime.fromtimestamp(d.time, tz=timezone(timedelta(hours=7))).strftime("%Y-%m-%d %H:%M:%S ICT"),
    } for d in deals_pos]
except Exception as e:
    out["pos_182201750_err"] = str(e)
# orders for that position
try:
    ords = mt5.history_orders_get(position=182201750) or []
    out["orders_182201750"] = [{
        "ticket": o.ticket, "position_id": o.position_id, "symbol": o.symbol,
        "type": int(o.type), "state": int(o.state), "reason": int(o.reason),
        "price_open": o.price_open, "price_current": o.price_current,
        "sl": o.sl, "tp": o.tp, "volume_initial": o.volume_initial,
        "comment": o.comment, "time_setup": int(o.time_setup), "time_done": int(o.time_done),
        "time_done_ict": datetime.fromtimestamp(o.time_done, tz=timezone(timedelta(hours=7))).strftime("%Y-%m-%d %H:%M:%S ICT") if o.time_done else None,
    } for o in ords]
except Exception as e:
    out["orders_err"] = str(e)
# also check if book event already covered
mt5.shutdown()
print(json.dumps(out, indent=2))
