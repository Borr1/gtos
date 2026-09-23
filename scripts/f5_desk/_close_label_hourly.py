import MetaTrader5 as mt5
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

mt5.initialize()
# deals around close of 180762411 and any OUT since last hour
from_ts = datetime(2026, 9, 2, 11, 0, tzinfo=timezone.utc)
to_ts = datetime.now(timezone.utc)
deals = mt5.history_deals_get(from_ts, to_ts) or []
print("DEALS_SINCE_11Z", len(deals))
for d in deals:
    print(json.dumps({
        "ticket": d.ticket, "order": d.order, "position": d.position_id,
        "symbol": d.symbol, "deal_type": d.type, "entry": d.entry,
        "volume": d.volume, "price": d.price, "profit": d.profit,
        "swap": d.swap, "commission": d.commission, "comment": d.comment,
        "reason": d.reason, "magic": d.magic,
        "time": datetime.fromtimestamp(d.time, tz=timezone.utc).isoformat(),
    }, default=str))

# reason codes: 0 CLIENT, 1 EXPERT, 2 DEALER, 3 SL, 4 TP, 5 SO, 6 ROLLOVER, 7 VARIATION, 8 BONUS, 9 COMMISSION, ...
# Actually MT5 DEAL_REASON: 0=CLIENT, 1=MOBILE, 2=WEB, 3=EXPERT, 4=SL, 5=TP, 6=SO, ...
print("REASON_MAP note: 3=EXPERT 4=SL 5=TP typically depending on build")

# orders history for those positions
for pos_id in [180762411, 180886874]:
    orders = mt5.history_orders_get(from_ts, to_ts) or []
    for o in orders:
        if o.position_id == pos_id or o.ticket == pos_id:
            print("ORD", json.dumps({
                "ticket": o.ticket, "position_id": o.position_id, "symbol": o.symbol,
                "type": o.type, "state": o.state, "reason": o.reason,
                "price_open": o.price_open, "sl": o.sl, "tp": o.tp,
                "price_current": o.price_current,
                "comment": o.comment,
                "time_setup": datetime.fromtimestamp(o.time_setup, tz=timezone.utc).isoformat() if o.time_setup else None,
                "time_done": datetime.fromtimestamp(o.time_done, tz=timezone.utc).isoformat() if o.time_done else None,
            }, default=str))

mt5.shutdown()

# book event emitted for close/fill
live = Path(r"host-local\redacted_host\repo\judgment\live")
be = json.loads((live / "book_event_watch_state.json").read_text(encoding="utf-8"))
em = be.get("emitted") or {}
for k in list(em.keys()):
    if "180762411" in k or "180886874" in k or "180717112" in k or "180770382" in k:
        print("EMITTED", k, em[k])

# open tickets snapshot
print("OPEN_TICKETS_STATE", json.dumps(be.get("open_tickets"), default=str)[:2000])
print("SEEN", json.dumps(be.get("seen_tickets"), default=str)[:2000])
