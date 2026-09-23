import json, MetaTrader5 as mt5
from datetime import datetime, timezone, timedelta

mt5.initialize()
out = {}
out["account"] = {k: getattr(mt5.account_info(), k) for k in ("login","equity","balance","profit") if mt5.account_info()}
pos = mt5.positions_get()
out["positions"] = [p._asdict() for p in (pos or [])]
ordr = mt5.orders_get()
out["orders"] = [o._asdict() for o in (ordr or [])]

tickets = [179079162, 179258600, 179217216, 179221949, 179258599, 179145308]
from_dt = datetime(2026, 8, 26, tzinfo=timezone.utc)
to_dt = datetime.now(timezone.utc) + timedelta(hours=1)
deals = []
for t in tickets:
    d = mt5.history_deals_get(from_dt, to_dt, position=t)
    if d:
        deals.extend([x._asdict() for x in d])
    d2 = mt5.history_deals_get(from_dt, to_dt, ticket=t)
    if d2:
        deals.extend([x._asdict() for x in d2])
# also last 6h all deals
d3 = mt5.history_deals_get(datetime.now(timezone.utc) - timedelta(hours=8), to_dt)
out["recent_deals"] = [x._asdict() for x in (d3 or [])]
# orders history for named tickets
hist_orders = []
for t in tickets:
    ho = mt5.history_orders_get(from_dt, to_dt, position=t)
    if ho:
        hist_orders.extend([x._asdict() for x in ho])
    ho2 = mt5.history_orders_get(ticket=t)
    if ho2:
        hist_orders.extend([x._asdict() for x in ho2])
out["history_orders"] = hist_orders
out["ticket_deals"] = deals

syms = ["GER40.cash", "EURUSD", "XAUUSD", "GBPUSD", "US30.cash"]
bars = {}
for s in syms:
    rates = mt5.copy_rates_from_pos(s, mt5.TIMEFRAME_M15, 0, 24)
    if rates is None:
        bars[s] = {"error": str(mt5.last_error())}
        continue
    rows = []
    for r in rates:
        rows.append({
            "time": datetime.fromtimestamp(int(r["time"]), tz=timezone.utc).isoformat(),
            "o": float(r["open"]), "h": float(r["high"]), "l": float(r["low"]), "c": float(r["close"]),
            "tick_vol": int(r["tick_volume"]),
        })
    hi20 = max(x["h"] for x in rows[-20:]) if len(rows) >= 20 else max(x["h"] for x in rows)
    lo20 = min(x["l"] for x in rows[-20:]) if len(rows) >= 20 else min(x["l"] for x in rows)
    last = rows[-1]
    bars[s] = {"n": len(rows), "last": last, "hi20": hi20, "lo20": lo20, "bars": rows[-8:]}
out["m15"] = bars
print(json.dumps(out, default=str))
mt5.shutdown()
