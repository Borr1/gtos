import MetaTrader5 as mt5, json
from datetime import datetime, timezone, timedelta

ok = mt5.initialize(path=r"C:\MT5\FTMO\terminal64.exe") or mt5.initialize()
print("init", ok, mt5.last_error())
ai = mt5.account_info()
print("ACCOUNT", json.dumps({"login": ai.login, "balance": ai.balance, "equity": ai.equity, "profit": ai.profit}))
now = datetime.now(timezone.utc)
# day start broker roughly ICT midnight = 17:00 previous UTC
day0 = datetime(2026, 9, 6, 17, 0, tzinfo=timezone.utc)
deals_day = mt5.history_deals_get(day0, now) or []
day_net = sum((d.profit or 0) + (d.swap or 0) + (d.commission or 0) for d in deals_day if d.entry == 1)
print("DAY_NET", day_net)

pos = mt5.positions_get() or []
f5 = [p for p in pos if p.magic == 0]
print("N_POS_ALL", len(pos), "N_F5", len(f5), "N_ORD", len(mt5.orders_get() or []))
out = {"positions_f5": [], "positions_other": []}
for p in pos:
    tick = mt5.symbol_info_tick(p.symbol)
    si = mt5.symbol_info(p.symbol)
    spread = (tick.ask - tick.bid) if tick else None
    stop_dist = abs(p.price_open - p.sl) if p.sl else None
    svr = (spread / stop_dist) if (spread is not None and stop_dist and stop_dist > 0) else None
    row = {
        "ticket": p.ticket, "symbol": p.symbol,
        "side": "LONG" if p.type == 0 else "SHORT",
        "vol": p.volume, "entry": p.price_open, "sl": p.sl, "tp": p.tp,
        "profit": p.profit, "swap": p.swap, "comment": p.comment, "magic": p.magic,
        "bid": tick.bid if tick else None, "ask": tick.ask if tick else None,
        "spread": spread, "stop_dist": stop_dist,
        "spread_vs_R": round(svr, 4) if svr is not None else None,
        "broker_sl_present": bool(p.sl),
        "trade_mode": si.trade_mode if si else None,
        "time": datetime.fromtimestamp(p.time, tz=timezone.utc).isoformat(),
    }
    key = "positions_f5" if p.magic == 0 else "positions_other"
    out[key].append(row)
    print("POS", json.dumps(row))

# US30 close
deals = mt5.history_deals_get(now - timedelta(hours=3), now) or []
for d in deals:
    if d.position_id == 181838721 or (d.symbol and "US30" in d.symbol and d.entry == 1 and d.time > now.timestamp() - 3*3600):
        print("DEAL", json.dumps({
            "ticket": d.ticket, "order": d.order, "position_id": d.position_id,
            "symbol": d.symbol, "type": d.type, "entry": d.entry, "vol": d.volume,
            "price": d.price, "profit": d.profit, "commission": d.commission,
            "swap": d.swap, "magic": d.magic, "reason": d.reason, "comment": d.comment,
            "time": datetime.fromtimestamp(d.time, tz=timezone.utc).isoformat(),
        }))
# also any other F5 closes since 00:20 UTC (last sit ~00:26)
for d in deals:
    if d.magic == 0 and d.entry == 1:
        print("F5CLOSE", json.dumps({
            "ticket": d.ticket, "order": d.order, "position_id": d.position_id,
            "symbol": d.symbol, "price": d.price, "profit": d.profit,
            "swap": d.swap, "commission": d.commission, "reason": d.reason,
            "comment": d.comment,
            "time": datetime.fromtimestamp(d.time, tz=timezone.utc).isoformat(),
        }))
mt5.shutdown()
print("DONE")
