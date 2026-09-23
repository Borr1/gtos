import MetaTrader5 as mt5, json
from datetime import datetime, timezone, timedelta

ok = mt5.initialize(path=r"C:\MT5\FTMO\terminal64.exe") or mt5.initialize()
print("init", ok, mt5.last_error())
now = datetime.now(timezone.utc)
print("now_utc", now.isoformat())

# position-scoped history
for pos_id in (181838721, 181838720):
    deals = mt5.history_deals_get(position=pos_id)
    print("POS_DEALS", pos_id, None if deals is None else len(deals), mt5.last_error())
    if deals:
        for d in deals:
            print(json.dumps({
                "ticket": d.ticket, "order": d.order, "position_id": d.position_id,
                "symbol": d.symbol, "type": d.type, "entry": d.entry, "vol": d.volume,
                "price": d.price, "profit": d.profit, "commission": d.commission,
                "swap": d.swap, "magic": d.magic, "reason": d.reason, "comment": d.comment,
                "time": datetime.fromtimestamp(d.time, tz=timezone.utc).isoformat(),
            }))

# wide window
from_ts = datetime(2026, 9, 6, 20, 0, tzinfo=timezone.utc)
deals = mt5.history_deals_get(from_ts, now) or []
print("WIDE_N", len(deals), "from", from_ts.isoformat())
closes = [d for d in deals if d.entry == 1]
print("WIDE_CLOSES", len(closes))
for d in sorted(closes, key=lambda x: x.time)[-15:]:
    print("CLOSE", json.dumps({
        "ticket": d.ticket, "order": d.order, "position_id": d.position_id,
        "symbol": d.symbol, "price": d.price, "profit": d.profit, "swap": d.swap,
        "commission": d.commission, "magic": d.magic, "reason": d.reason,
        "comment": d.comment,
        "time": datetime.fromtimestamp(d.time, tz=timezone.utc).isoformat(),
    }))

# day net like chair: from broker server day — use deals since 17:00Z prev
day0 = datetime(2026, 9, 6, 17, 0, tzinfo=timezone.utc)
dd = mt5.history_deals_get(day0, now) or []
print("DAY_DEALS", len(dd))
s = 0.0
for d in dd:
    s += (d.profit or 0) + (d.swap or 0) + (d.commission or 0)
print("DAY_SUM_ALL", s)
s2 = sum((d.profit or 0)+(d.swap or 0)+(d.commission or 0) for d in dd if d.entry==1)
print("DAY_SUM_EXITS", s2)
# also account
ai = mt5.account_info()
print("BAL_EQ", ai.balance, ai.equity)
mt5.shutdown()
