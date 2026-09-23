import MetaTrader5 as mt5, json
from datetime import datetime, timezone, timedelta

mt5.initialize(path=r"C:\MT5\FTMO\terminal64.exe")
ai = mt5.account_info()
out = {
    "login": ai.login,
    "bal": ai.balance,
    "eq": ai.equity,
    "ts_utc": datetime.now(timezone.utc).isoformat(),
}
pos = mt5.positions_get() or []
out["positions"] = []
for p in pos:
    out["positions"].append({
        "ticket": p.ticket,
        "symbol": p.symbol,
        "type": int(p.type),
        "volume": p.volume,
        "price_open": p.price_open,
        "sl": p.sl,
        "tp": p.tp,
        "profit": p.profit,
        "magic": p.magic,
        "comment": p.comment,
        "time": int(p.time),
    })
ords = mt5.orders_get() or []
out["pending"] = []
for o in ords:
    out["pending"].append({
        "ticket": o.ticket,
        "symbol": o.symbol,
        "type": int(o.type),
        "volume_current": o.volume_current,
        "price_open": o.price_open,
        "sl": o.sl,
        "tp": o.tp,
        "magic": o.magic,
        "comment": o.comment,
        "time_setup": int(o.time_setup),
    })
frm = datetime(2026, 9, 8, 7, 20, tzinfo=timezone.utc)
to = datetime.now(timezone.utc) + timedelta(minutes=2)
deals = mt5.history_deals_get(frm, to) or []
out["deals"] = []
for d in deals:
    out["deals"].append({
        "ticket": d.ticket,
        "order": d.order,
        "position_id": d.position_id,
        "symbol": d.symbol,
        "type": int(d.type),
        "entry": int(d.entry),
        "volume": d.volume,
        "price": d.price,
        "profit": d.profit,
        "commission": d.commission,
        "swap": d.swap,
        "magic": d.magic,
        "reason": int(d.reason),
        "comment": d.comment,
        "time": int(d.time),
    })
out["symbols"] = {}
for sym in sorted({p.symbol for p in pos}):
    si = mt5.symbol_info(sym)
    tick = mt5.symbol_info_tick(sym)
    out["symbols"][sym] = {
        "trade_mode": si.trade_mode,
        "spread": si.spread,
        "point": si.point,
        "digits": si.digits,
        "bid": tick.bid,
        "ask": tick.ask,
        "spread_price": tick.ask - tick.bid,
    }
# also check W7 ticket specifically if gone
hist = mt5.history_orders_get(frm, to) or []
out["orders_hist"] = []
for o in hist:
    if o.ticket in (181801554, 182201750, 182201752, 181801555, 180734064) or o.position_id in (181801554,):
        out["orders_hist"].append({
            "ticket": o.ticket,
            "position_id": o.position_id,
            "symbol": o.symbol,
            "type": int(o.type),
            "state": int(o.state),
            "reason": int(o.reason),
            "price_open": o.price_open,
            "sl": o.sl,
            "tp": o.tp,
            "volume_initial": o.volume_initial,
            "comment": o.comment,
            "time_setup": int(o.time_setup),
            "time_done": int(o.time_done),
        })
mt5.shutdown()
print(json.dumps(out, indent=2))
