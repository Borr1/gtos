import MetaTrader5 as mt5, json
from datetime import datetime, timezone, timedelta
out = {}
mt5.initialize()
now_utc = datetime.now(timezone.utc)
# server clock offset probe
t = mt5.symbol_info_tick("US30.cash")
srv = datetime.fromtimestamp(t.time, timezone.utc)
off = round((srv - now_utc).total_seconds()/3600.0)
out["now_utc"] = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
out["server_now_naive"] = srv.strftime("%Y-%m-%dT%H:%M:%SZ")
out["server_offset_h"] = off
lo = now_utc - timedelta(hours=10) + timedelta(hours=off)
hi = now_utc + timedelta(hours=2) + timedelta(hours=off)
deals = mt5.history_deals_get(lo, hi) or []
def row(d):
    st = datetime.fromtimestamp(d.time, timezone.utc)
    return {"deal": d.ticket, "order": d.order, "pos": d.position_id, "sym": d.symbol, "type": d.type, "entry": d.entry,
            "vol": d.volume, "price": d.price, "profit": round(d.profit,2), "reason": d.reason,
            "srv_time": st.strftime("%H:%M:%S"), "utc_time": (st - timedelta(hours=off)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "comment": d.comment}
rows = [row(d) for d in deals]
out["n_deals"] = len(rows)
out["target_181295787"] = [r for r in rows if r["pos"] == 181295787]
out["target_181295784"] = [r for r in rows if r["pos"] == 181295784]
out["us30_deals"] = [r for r in rows if r["sym"].startswith("US30")][-14:]
out["recent_all"] = rows[-24:]
ho = mt5.history_orders_get(lo, hi) or []
out["hist_orders_target"] = [{"ord": o.ticket, "pos": o.position_id, "sym": o.symbol, "type": o.type, "state": o.state,
                              "price_open": o.price_open, "sl": o.sl, "tp": o.tp, "vol_init": o.volume_initial,
                              "setup_srv": datetime.fromtimestamp(o.time_setup, timezone.utc).strftime("%H:%M:%S"),
                              "done_srv": datetime.fromtimestamp(o.time_done, timezone.utc).strftime("%H:%M:%S") if o.time_done else None,
                              "exp": o.time_expiration, "comment": o.comment}
                             for o in ho if o.position_id in (181295787, 181295784, 181349108)]
mt5.shutdown()
print(json.dumps(out, default=str))
