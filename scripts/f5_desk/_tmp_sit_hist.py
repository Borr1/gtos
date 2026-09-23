import MetaTrader5 as mt5
from datetime import datetime, timezone
mt5.initialize()
print("ORDERS", mt5.orders_get())
print("POSITIONS", mt5.positions_get())
deals = mt5.history_deals_get(datetime(2026,8,31,0,0,tzinfo=timezone.utc), datetime.now(timezone.utc))
print("DEALS", len(deals) if deals else 0)
if deals:
  for d in deals:
    print(d.ticket, d.order, d.position_id, d.symbol, d.type, d.entry, d.volume, d.price, round(d.profit,2), d.time, d.comment)
orders = mt5.history_orders_get(datetime(2026,8,31,0,0,tzinfo=timezone.utc), datetime.now(timezone.utc))
print("HIST_ORDERS", len(orders) if orders else 0)
if orders:
  for o in orders:
    print(o.ticket, o.symbol, o.type, o.state, o.price_open, o.volume_initial, o.time_setup, o.time_done, o.comment)
mt5.shutdown()
