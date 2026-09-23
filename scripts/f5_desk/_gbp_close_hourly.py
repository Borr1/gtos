import MetaTrader5 as mt5
import json
from datetime import datetime, timezone

mt5.initialize()
deals = mt5.history_deals_get(position=180775773) or []
print("GBPUSD deals", len(deals))
for d in deals:
    print(json.dumps({
        "ticket": d.ticket, "order": d.order, "position": d.position_id,
        "symbol": d.symbol, "type": d.type, "entry": d.entry,
        "price": d.price, "profit": d.profit, "comment": d.comment,
        "reason": d.reason,
        "time": datetime.fromtimestamp(d.time, tz=timezone.utc).isoformat(),
    }))
# any other closed positions today missing from open
for pid in [180775773, 180828069, 180839963, 180762411]:
    deals = mt5.history_deals_get(position=pid) or []
    outs = [d for d in deals if d.entry in (1,2,3)]
    if outs:
        d = outs[-1]
        print("OUT", pid, d.symbol, d.profit, d.comment, d.reason, datetime.fromtimestamp(d.time, tz=timezone.utc).isoformat())
mt5.shutdown()
