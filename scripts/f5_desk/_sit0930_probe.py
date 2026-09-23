import MetaTrader5 as mt5
import datetime as dt
import json

ok = mt5.initialize()
print("init", ok, mt5.last_error())
acc = mt5.account_info()
print("login", acc.login, "bal", acc.balance, "eq", acc.equity)
now = dt.datetime.now(dt.timezone.utc)
orders = mt5.orders_get() or []
for o in orders:
    t = dt.datetime.fromtimestamp(o.time_setup, dt.timezone.utc)
    age_m = (now - t).total_seconds() / 60.0
    print(
        "ORD",
        o.ticket,
        o.symbol,
        o.type,
        o.price_open,
        "setup",
        t.isoformat(),
        "age_m",
        round(age_m, 1),
        "magic",
        o.magic,
        "comment",
        o.comment,
    )
pos = mt5.positions_get() or []
for p in pos:
    si = mt5.symbol_info(p.symbol)
    tick = mt5.symbol_info_tick(p.symbol)
    spread = (tick.ask - tick.bid) if tick else None
    stop_dist = abs(p.price_open - p.sl) if p.sl else None
    spread_over_R = (spread / stop_dist) if (spread is not None and stop_dist and stop_dist > 0) else None
    print(
        "POS",
        p.ticket,
        p.symbol,
        "magic",
        p.magic,
        "type",
        p.type,
        "sl",
        p.sl,
        "tp",
        p.tp,
        "pnl",
        p.profit,
        "spread",
        spread,
        "stop_dist",
        stop_dist,
        "spread_over_R",
        spread_over_R,
        "trade_mode",
        getattr(si, "trade_mode", None),
    )
from_ts = dt.datetime(2026, 9, 8, 0, 30, tzinfo=dt.timezone.utc)
deals = mt5.history_deals_get(from_ts, now) or []
print("---exits since 00:30Z---")
for d in deals:
    if d.entry in (1, 3):
        t = dt.datetime.fromtimestamp(d.time, dt.timezone.utc)
        print(
            "EXIT",
            d.ticket,
            "pos",
            d.position_id,
            d.symbol,
            "reason",
            d.reason,
            "price",
            d.price,
            "profit",
            d.profit,
            "comment",
            d.comment,
            "magic",
            d.magic,
            "t",
            t.isoformat(),
            "volume",
            d.volume,
        )
print("---orders/deals for 182118694 / 182146604---")
for d in deals:
    if d.position_id in (182118694, 182146604) or d.order in (182118694, 182146604):
        t = dt.datetime.fromtimestamp(d.time, dt.timezone.utc)
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
            "price",
            d.price,
            "profit",
            d.profit,
            "comment",
            d.comment,
            "magic",
            d.magic,
            "t",
            t.isoformat(),
        )
# also look for XAU deal with that position around last sit
mt5.shutdown()
