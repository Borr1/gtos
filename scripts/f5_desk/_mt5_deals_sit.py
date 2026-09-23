import MetaTrader5 as mt5, json
from datetime import datetime, timezone, timedelta
mt5.initialize()
ai = mt5.account_info()
out = {
  "login": ai.login, "balance": ai.balance, "equity": ai.equity,
  "positions": [], "orders": [], "deals_recent": []
}
for p in (mt5.positions_get() or []):
  out["positions"].append({
    "ticket": p.ticket, "symbol": p.symbol, "type": int(p.type),
    "volume": p.volume, "price_open": p.price_open, "sl": p.sl, "tp": p.tp,
    "profit": p.profit, "comment": p.comment, "time": int(p.time)
  })
for o in (mt5.orders_get() or []):
  out["orders"].append({
    "ticket": o.ticket, "symbol": o.symbol, "type": int(o.type),
    "volume": o.volume_current, "price": o.price_open, "sl": o.sl, "tp": o.tp,
    "comment": o.comment
  })
now = datetime.now(timezone.utc)
deals = mt5.history_deals_get(now - timedelta(hours=6), now) or []
for d in deals:
  if d.entry in (0,1) or d.profit != 0:  # in/out
    out["deals_recent"].append({
      "ticket": d.ticket, "order": d.order, "position_id": d.position_id,
      "symbol": d.symbol, "type": int(d.type), "entry": int(d.entry),
      "volume": d.volume, "price": d.price, "profit": d.profit,
      "commission": d.commission, "swap": d.swap, "comment": d.comment,
      "time": int(d.time), "time_utc": datetime.fromtimestamp(d.time, tz=timezone.utc).isoformat()
    })
print(json.dumps(out, default=str))
mt5.shutdown()
