import MetaTrader5 as mt5, json
from datetime import datetime, timezone, timedelta
out = {}
ok = mt5.initialize()
out["init"] = bool(ok); out["last_error"] = mt5.last_error()
ai = mt5.account_info()
if ai:
    out["account"] = {"login": ai.login, "equity": round(ai.equity,2), "balance": round(ai.balance,2), "profit": round(ai.profit,2)}
now = datetime.now(timezone.utc)
deals = mt5.history_deals_get(now - timedelta(hours=6), now) or []
rows = []
for d in deals:
    rows.append({"deal": d.ticket, "pos": d.position_id, "sym": d.symbol, "type": d.type, "entry": d.entry,
                 "vol": d.volume, "price": d.price, "profit": round(d.profit,2), "reason": d.reason,
                 "time": datetime.fromtimestamp(d.time, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "comment": d.comment})
out["deals_6h"] = rows
out["target"] = [r for r in rows if r["pos"] == 181295787]
pos = mt5.positions_get() or []
out["positions"] = [{"ticket": p.ticket, "sym": p.symbol, "type": p.type, "vol": p.volume, "open": p.price_open,
                     "sl": p.sl, "tp": p.tp, "cur": p.price_current, "profit": round(p.profit,2),
                     "time": datetime.fromtimestamp(p.time, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                     "comment": p.comment} for p in pos]
orders = mt5.orders_get() or []
out["orders"] = [{"ticket": o.ticket, "sym": o.symbol, "type": o.type, "vol": o.volume_current, "price": o.price_open,
                  "sl": o.sl, "tp": o.tp, "exp": o.time_expiration, "comment": o.comment} for o in orders]
ho = mt5.history_orders_get(now - timedelta(hours=6), now) or []
out["hist_orders_target"] = [{"ord": o.ticket, "pos": o.position_id, "sym": o.symbol, "type": o.type, "state": o.state,
                              "price_open": o.price_open, "sl": o.sl, "tp": o.tp,
                              "setup": datetime.fromtimestamp(o.time_setup, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                              "done": datetime.fromtimestamp(o.time_done, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") if o.time_done else None,
                              "comment": o.comment} for o in ho if o.position_id == 181295787 or o.ticket == 181295787]
for s in ("US30.cash",):
    t = mt5.symbol_info_tick(s)
    si = mt5.symbol_info(s)
    if t: out["tick_"+s] = {"bid": t.bid, "ask": t.ask, "spread_pts": (si.spread if si else None), "time": datetime.fromtimestamp(t.time, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
mt5.shutdown()
print(json.dumps(out, default=str))
