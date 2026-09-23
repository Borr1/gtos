import MetaTrader5 as mt5
import datetime as dt

assert mt5.initialize()
acc = mt5.account_info()
print("login", acc.login, "bal", acc.balance, "eq", acc.equity, "server", acc.server)
now = dt.datetime.now(dt.timezone.utc)
# broker often needs naive local / broader window
from_ts = dt.datetime(2026, 9, 7, 20, 0)  # naive
to_ts = dt.datetime(2026, 9, 8, 12, 0)
deals = mt5.history_deals_get(from_ts, to_ts)
print("deals_count", 0 if deals is None else len(deals), "err", mt5.last_error())
want = {182118694, 182134088, 182118705, 182146604, 182062146}
if deals:
    for d in deals:
        if d.position_id in want or d.order in want or (d.symbol in ("XAUUSD", "GBPUSD", "AVAUSD") and d.time >= int(dt.datetime(2026,9,8,0,0,tzinfo=dt.timezone.utc).timestamp())):
            t = dt.datetime.utcfromtimestamp(d.time)
            print(
                "DEAL",
                d.ticket,
                "pos",
                d.position_id,
                "order",
                d.order,
                d.symbol,
                "entry",
                d.entry,
                "reason",
                d.reason,
                "type",
                d.type,
                "price",
                d.price,
                "profit",
                d.profit,
                "commission",
                d.commission,
                "swap",
                d.swap,
                "vol",
                d.volume,
                "comment",
                repr(d.comment),
                "magic",
                d.magic,
                "t_utc_naive",
                t.isoformat(),
            )
# also positions now
print("---POS---")
for p in mt5.positions_get() or []:
    print(p.ticket, p.symbol, p.magic, p.type, p.price_open, p.sl, p.tp, p.profit, p.comment)
print("---ORD---")
for o in mt5.orders_get() or []:
    # time_setup is unix
    setup = dt.datetime.utcfromtimestamp(o.time_setup)
    age_m = (dt.datetime.utcnow() - setup).total_seconds() / 60.0
    print(o.ticket, o.symbol, o.type, o.price_open, o.sl, o.tp, o.volume_current, "setup_utc", setup.isoformat(), "age_m", round(age_m,1), o.comment, o.magic)
# symbol trade check for opens
print("---MECH---")
for p in mt5.positions_get() or []:
    if p.magic != 0:
        continue
    si = mt5.symbol_info(p.symbol)
    tick = mt5.symbol_info_tick(p.symbol)
    spread = tick.ask - tick.bid
    stop = abs(p.price_open - p.sl) if p.sl else None
    print(p.ticket, p.symbol, "spread_over_R", (spread/stop if stop else None), "broker_sl", p.sl, "trade_mode", si.trade_mode if si else None, "tradeable", si.trade_mode == 4 if si else None)
mt5.shutdown()
