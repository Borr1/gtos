import json, MetaTrader5 as mt5
from datetime import datetime, timezone, timedelta
mt5.initialize()
out = {}
ai = mt5.account_info()
out["account"] = {"equity": ai.equity, "balance": ai.balance, "profit": ai.profit}
out["positions"] = [p._asdict() for p in (mt5.positions_get() or [])]
out["orders"] = [{k: o._asdict().get(k) for k in ("ticket","symbol","type","volume_current","price_open","sl","tp","comment","time_setup","state")} for o in (mt5.orders_get() or [])]
from_dt = datetime(2026, 8, 27, tzinfo=timezone.utc)
to_dt = datetime.now(timezone.utc) + timedelta(hours=1)
tickets = [179079162, 179258600, 179217216, 179221949, 179258599, 179145308]
deals = []
for t in tickets:
    d = mt5.history_deals_get(from_dt, to_dt, position=t)
    if d:
        for x in d:
            deals.append({k: x._asdict().get(k) for k in ("ticket","order","position_id","symbol","type","entry","volume","price","profit","comment","time","reason")})
out["named_deals"] = deals
# last 2h all deals
d3 = mt5.history_deals_get(datetime.now(timezone.utc) - timedelta(hours=3), to_dt)
out["recent_3h"] = [{k: x._asdict().get(k) for k in ("ticket","order","position_id","symbol","type","entry","volume","price","profit","comment","time")} for x in (d3 or [])]
# EURUSD / gold last
for s in ("EURUSD","XAUUSD","GER40.cash"):
    tick = mt5.symbol_info_tick(s)
    if tick:
        out.setdefault("ticks", {})[s] = {"bid": tick.bid, "ask": tick.ask, "time": datetime.fromtimestamp(tick.time, tz=timezone.utc).isoformat()}
print(json.dumps(out, default=str))
mt5.shutdown()
