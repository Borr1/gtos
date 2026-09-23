import MetaTrader5 as mt5
from datetime import datetime, timezone, timedelta
ok = mt5.initialize()
print("init", ok, mt5.last_error())
now = datetime.now(timezone.utc)
d = mt5.history_deals_get(now - timedelta(hours=2), now) or []
print("n", len(d))
for x in d:
    print(x.ticket, x.position_id, x.symbol, x.type, x.entry, x.volume, x.price, round(x.profit, 2), x.reason, x.time, x.comment)
ai = mt5.account_info()
print("eq", ai.equity, "bal", ai.balance, "profit", ai.profit)
print("pos", mt5.positions_total(), "ord", mt5.orders_total())
mt5.shutdown()
