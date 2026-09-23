import MetaTrader5 as mt5, json, datetime as dt
from pathlib import Path
out_path = Path(r"host-local\redacted_host\repo\scripts\f5_desk\_hourly_sit_out.json")
ok = mt5.initialize(path=r"C:\MT5\FTMO\terminal64.exe")
acc = mt5.account_info()
pos = mt5.positions_get() or []
ords = mt5.orders_get() or []
rows = []
for p in pos:
    tick = mt5.symbol_info_tick(p.symbol)
    info = mt5.symbol_info(p.symbol)
    spread = (tick.ask - tick.bid) if tick else None
    stop_dist = abs(p.price_open - p.sl) if p.sl else None
    sor = (spread / stop_dist) if (spread is not None and stop_dist and stop_dist > 0) else None
    rows.append({
        "ticket": int(p.ticket), "symbol": p.symbol,
        "side": "LONG" if p.type == 0 else "SHORT",
        "magic": int(p.magic), "lots": float(p.volume),
        "entry": float(p.price_open), "live_sl": float(p.sl), "tp": float(p.tp),
        "pnl": float(p.profit), "comment": p.comment,
        "mark": float(tick.bid if p.type == 0 else tick.ask) if tick else None,
        "spread": float(spread) if spread is not None else None,
        "stop_dist": float(stop_dist) if stop_dist is not None else None,
        "spread_over_R": float(sor) if sor is not None else None,
        "trade_mode": int(info.trade_mode) if info else None,
        "broker_sl_present": bool(p.sl and p.sl > 0),
        "symbol_trading": bool(info is not None and info.trade_mode == 4),
        "time": dt.datetime.utcfromtimestamp(p.time).isoformat() + "Z",
    })
since = dt.datetime(2026, 9, 8, 5, 20, 0)
until = dt.datetime.utcnow() + dt.timedelta(minutes=5)
deals = mt5.history_deals_get(since, until) or []
closes, fills = [], []
for d in deals:
    if int(d.magic) not in (0, 20260401, 0):
        continue
    rec = {
        "ticket": int(d.position_id), "deal": int(d.ticket), "symbol": d.symbol,
        "profit": float(d.profit), "commission": float(d.commission), "swap": float(d.swap),
        "reason": int(d.reason), "comment": d.comment,
        "time": dt.datetime.utcfromtimestamp(d.time).isoformat() + "Z",
        "magic": int(d.magic), "volume": float(d.volume), "price": float(d.price),
        "type": int(d.type), "entry": int(d.entry), "order": int(d.order),
    }
    if d.entry == 1:
        closes.append(rec)
    elif d.entry == 0 and d.volume > 0 and d.type in (0, 1):
        fills.append(rec)
pend = []
for o in ords:
    age_m = (dt.datetime.utcnow() - dt.datetime.utcfromtimestamp(o.time_setup)).total_seconds() / 60.0
    pend.append({
        "ticket": int(o.ticket), "symbol": o.symbol, "type": int(o.type),
        "price": float(o.price_open), "sl": float(o.sl), "tp": float(o.tp),
        "magic": int(o.magic), "comment": o.comment,
        "time": dt.datetime.utcfromtimestamp(o.time_setup).isoformat() + "Z",
        "age_min": age_m,
    })
# also pull deal history for the two new tickets specifically
extra = {}
for tid in (182201750, 182201752, 181411441, 182151007):
    ds = mt5.history_deals_get(position=tid) or []
    extra[str(tid)] = [{
        "deal": int(d.ticket), "entry": int(d.entry), "type": int(d.type),
        "price": float(d.price), "volume": float(d.volume), "profit": float(d.profit),
        "comment": d.comment, "reason": int(d.reason), "magic": int(d.magic),
        "time": dt.datetime.utcfromtimestamp(d.time).isoformat() + "Z",
        "order": int(d.order), "sl": float(getattr(d, "sl", 0) or 0), "tp": float(getattr(d, "tp", 0) or 0),
    } for d in ds]
out = {
    "ok": bool(ok), "login": int(acc.login), "bal": float(acc.balance), "eq": float(acc.equity),
    "floating": float(acc.equity - acc.balance), "positions": rows, "pending": pend,
    "closes": closes, "fills": fills, "extra": extra,
    "ts_utc": dt.datetime.utcnow().isoformat() + "Z",
}
out_path.write_text(json.dumps(out, indent=2))
print(json.dumps(out))
mt5.shutdown()
