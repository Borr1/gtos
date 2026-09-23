import json, MetaTrader5 as mt5
from datetime import datetime, timezone, timedelta
mt5.initialize()
from_dt = datetime(2026, 8, 27, 10, tzinfo=timezone.utc)
to_dt = datetime.now(timezone.utc) + timedelta(hours=2)
out = {"orders": [], "deals": []}
out["orders"] = [{k: o._asdict().get(k) for k in ("ticket","symbol","type","volume_current","price_open","sl","tp","comment","state")} for o in (mt5.orders_get() or [])]
# deals by position
d = mt5.history_deals_get(from_dt, to_dt)
if d:
    for x in d:
        if x.position_id in (179258599, 179272692, 179079162, 179221949) or x.order in (179258599, 179221949):
            out["deals"].append({k: x._asdict().get(k) for k in ("ticket","order","position_id","symbol","type","entry","volume","price","profit","comment","time","reason")})
# last 30 min all
d2 = mt5.history_deals_get(datetime.now(timezone.utc) - timedelta(minutes=40), to_dt)
out["recent"] = [{k: x._asdict().get(k) for k in ("ticket","order","position_id","symbol","type","entry","volume","price","profit","comment","time")} for x in (d2 or [])]
print(json.dumps(out, default=str))
mt5.shutdown()
