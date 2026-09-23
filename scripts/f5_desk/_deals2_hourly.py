import MetaTrader5 as mt5
import json
from datetime import datetime, timezone, timedelta

mt5.initialize()
# use naive local? MT5 on Windows often wants server time or naive UTC
now = datetime.now(timezone.utc)
for label, from_ts in [
    ("utc_aware_3h", now - timedelta(hours=3)),
    ("naive_utc_3h", datetime.utcnow() - timedelta(hours=3)),
    ("naive_utc_8h", datetime.utcnow() - timedelta(hours=8)),
]:
    deals = mt5.history_deals_get(from_ts.replace(tzinfo=None) if from_ts.tzinfo else from_ts, datetime.utcnow())
    print(label, "count", len(deals or []))
    for d in (deals or [])[-15:]:
        if d.position_id in (180762411, 180886874, 180717112, 180770382, 180775761, 180622571, 180734064) or d.entry != 0:
            print(label, json.dumps({
                "ticket": d.ticket, "order": d.order, "position": d.position_id,
                "symbol": d.symbol, "type": d.type, "entry": d.entry,
                "price": d.price, "profit": d.profit, "comment": d.comment,
                "reason": d.reason, "time": str(datetime.utcfromtimestamp(d.time)),
            }))

# position-specific history
for pid in [180762411, 180886874]:
    deals = mt5.history_deals_get(position=pid)
    print("BY_POS", pid, len(deals or []))
    for d in deals or []:
        print(json.dumps({
            "ticket": d.ticket, "order": d.order, "position": d.position_id,
            "symbol": d.symbol, "type": d.type, "entry": d.entry,
            "volume": d.volume, "price": d.price, "profit": d.profit,
            "comment": d.comment, "reason": d.reason,
            "time": str(datetime.utcfromtimestamp(d.time)),
            "sl": getattr(d, "sl", None), "tp": getattr(d, "tp", None),
        }))

# also check symbol for 180762411 from spent / deals_recent
mt5.shutdown()
