import json, MetaTrader5 as mt5
from datetime import datetime, timezone, timedelta
mt5.initialize()
from_dt = datetime(2026, 8, 27, 8, tzinfo=timezone.utc)
to_dt = datetime.now(timezone.utc) + timedelta(hours=2)
out = {}
out["orders"] = [{k: o._asdict().get(k) for k in ("ticket","symbol","type","volume_current","price_open","sl","tp","comment","state")} for o in (mt5.orders_get() or [])]
deals = []
for t in (179272698, 179258599, 179272692, 179221949, 179217216):
    d = mt5.history_deals_get(from_dt, to_dt, position=t)
    if d:
        for x in d:
            deals.append({k: x._asdict().get(k) for k in ("ticket","order","position_id","symbol","type","entry","volume","price","profit","comment","time","reason")})
out["deals"] = deals
tick = mt5.symbol_info_tick("XAUUSD")
if tick:
    out["xau"] = {"bid": tick.bid, "ask": tick.ask}
print(json.dumps(out, default=str))
mt5.shutdown()
