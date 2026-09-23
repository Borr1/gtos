import MetaTrader5 as mt5, json, datetime as dt
from pathlib import Path

out = Path(r"host-local\redacted_host\repo\scripts\f5_desk\_hourly_sit_out.json")
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
    spread_over_R = (spread / stop_dist) if (spread is not None and stop_dist and stop_dist > 0) else None
    side = "LONG" if p.type == 0 else "SHORT"
    rows.append({
        "ticket": int(p.ticket),
        "symbol": p.symbol,
        "side": side,
        "magic": int(p.magic),
        "lots": float(p.volume),
        "entry": float(p.price_open),
        "live_sl": float(p.sl),
        "tp": float(p.tp),
        "pnl": float(p.profit),
        "comment": p.comment,
        "time": dt.datetime.utcfromtimestamp(p.time).isoformat() + "Z",
        "bid": float(tick.bid) if tick else None,
        "ask": float(tick.ask) if tick else None,
        "spread": float(spread) if spread is not None else None,
        "stop_dist": float(stop_dist) if stop_dist is not None else None,
        "spread_over_R": float(spread_over_R) if spread_over_R is not None else None,
        "trade_mode": int(info.trade_mode) if info else None,
        "broker_sl_present": bool(p.sl and p.sl > 0),
        "symbol_trading": bool(info is not None and info.trade_mode == 4),
    })

since = dt.datetime(2026, 9, 8, 0, 33, 0)
until = dt.datetime.utcnow() + dt.timedelta(minutes=5)
deals = mt5.history_deals_get(since, until) or []
closes, fills = [], []
for d in deals:
    if int(d.magic) not in (0, 0) and int(d.magic) != 0:
        # keep all F5 magic; still record others lightly
        pass
    rec = {
        "ticket": int(d.position_id),
        "deal": int(d.ticket),
        "symbol": d.symbol,
        "profit": float(d.profit),
        "commission": float(d.commission),
        "reason": int(d.reason),
        "comment": d.comment,
        "time": dt.datetime.utcfromtimestamp(d.time).isoformat() + "Z",
        "magic": int(d.magic),
        "volume": float(d.volume),
        "price": float(d.price),
        "type": int(d.type),
        "entry": int(d.entry),
    }
    if d.entry == 1:
        closes.append(rec)
    elif d.entry == 0 and d.volume > 0 and d.type in (0, 1):
        fills.append(rec)

pendings = []
for o in ords:
    age_m = (dt.datetime.utcnow() - dt.datetime.utcfromtimestamp(o.time_setup)).total_seconds() / 60.0
    pendings.append({
        "ticket": int(o.ticket),
        "symbol": o.symbol,
        "type": int(o.type),
        "price": float(o.price_open),
        "sl": float(o.sl),
        "tp": float(o.tp),
        "time": dt.datetime.utcfromtimestamp(o.time_setup).isoformat() + "Z",
        "age_min": age_m,
        "comment": o.comment,
        "magic": int(o.magic),
    })

# load orig map if present
orig_path = Path(r"host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\judgment\state\chair_orig_sl.json")
orig = {}
if orig_path.exists():
    try:
        orig = json.loads(orig_path.read_text(encoding="utf-8"))
    except Exception as e:
        orig = {"_error": str(e)}

payload = {
    "ok": bool(ok),
    "last_error": list(mt5.last_error()) if ok is not None else None,
    "ts_utc": dt.datetime.utcnow().replace(tzinfo=dt.timezone.utc).isoformat().replace("+00:00", "Z"),
    "account": {
        "login": int(acc.login),
        "balance": float(acc.balance),
        "equity": float(acc.equity),
        "floating": float(acc.equity - acc.balance),
    },
    "positions": rows,
    "closes_since_0733": closes,
    "fills_since_0733": fills,
    "pendings": pendings,
    "orig_file": str(orig_path),
    "orig": orig,
}
out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(out)
print(json.dumps({
    "bal": payload["account"]["balance"],
    "eq": payload["account"]["equity"],
    "n_pos": len(rows),
    "n_close": len(closes),
    "n_fill": len(fills),
    "n_pend": len(pendings),
    "tickets": [(r["ticket"], r["symbol"], r["spread_over_R"], r["broker_sl_present"], r["trade_mode"], r["live_sl"]) for r in rows],
}, indent=2))
mt5.shutdown()
