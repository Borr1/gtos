import json, MetaTrader5 as mt5, datetime as dt, subprocess
out = {"ok": False}
if not mt5.initialize():
    out["err"] = str(mt5.last_error()); print(json.dumps(out)); raise SystemExit(1)
ai = mt5.account_info()
out.update({
  "login": ai.login, "server": ai.server, "balance": ai.balance, "equity": ai.equity,
  "floating": round(ai.equity - ai.balance, 2),
  "to_pass": round(105000 - ai.balance, 2),
  "probe_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
})
want = 180775773
sym = "GBPUSD"
positions = mt5.positions_get() or []
orders = mt5.orders_get() or []
typemap = {0:"BUY",1:"SELL",2:"BUY_LIMIT",3:"SELL_LIMIT",4:"BUY_STOP",5:"SELL_STOP",6:"BUY_STOP_LIMIT",7:"SELL_STOP_LIMIT"}
open_rows = []
for p in positions:
    open_rows.append({
      "ticket": p.ticket, "symbol": p.symbol,
      "side": "LONG" if p.type==0 else "SHORT",
      "lots": p.volume, "entry": p.price_open, "sl": p.sl, "tp": p.tp,
      "mark": p.price_current, "pnl": p.profit, "swap": p.swap,
      "comment": (p.comment or "")[:40],
    })
pend_rows = []
for o in orders:
    pend_rows.append({
      "ticket": o.ticket, "symbol": o.symbol, "type": typemap.get(o.type, str(o.type)),
      "side": "LONG" if o.type in (0,2,4,6) else "SHORT",
      "lots": o.volume_current, "limit": o.price_open, "sl": o.sl, "tp": o.tp,
      "comment": (o.comment or "")[:40],
    })
out["open"] = open_rows
out["pending"] = pend_rows
out["want_ticket"] = want
out["want_in_positions"] = any(r["ticket"]==want for r in open_rows)
out["want_in_orders"] = any(r["ticket"]==want for r in pend_rows)
tick = mt5.symbol_info_tick(sym)
si = mt5.symbol_info(sym)
if tick:
    out["gbpusd_bid"] = tick.bid; out["gbpusd_ask"] = tick.ask
    out["gbpusd_spread"] = round(tick.ask - tick.bid, 5)
if si:
    out["tick_value"] = si.trade_tick_value
    out["tick_size"] = si.trade_tick_size
    out["point"] = si.point
for p in positions:
    if p.ticket == want:
        r_pts = abs(p.price_open - p.sl) if p.sl else None
        r_usd = None
        if r_pts and si and si.trade_tick_size:
            r_usd = round(r_pts / si.trade_tick_size * si.trade_tick_value * p.volume, 2)
        tp_r = None
        if r_pts and p.tp:
            tp_dist = abs(p.tp - p.price_open)
            tp_r = round(tp_dist / r_pts, 2) if r_pts else None
        r_now = None
        if r_pts and r_pts > 0:
            r_now = round((p.price_current - p.price_open) / r_pts if p.type==0 else (p.price_open - p.price_current) / r_pts, 4)
        out["want_pos"] = {
          "ticket": p.ticket, "symbol": p.symbol, "side": "LONG" if p.type==0 else "SHORT",
          "lots": p.volume, "entry": p.price_open, "sl": p.sl, "tp": p.tp,
          "mark": p.price_current, "pnl": p.profit, "swap": p.swap, "comment": p.comment,
          "r_pts": r_pts, "r_usd": r_usd, "tp_r": tp_r, "R_orig": r_now,
        }
from_dt = dt.datetime(2026,9,2,0,0,tzinfo=dt.timezone.utc)
deals = mt5.history_deals_get(from_dt, dt.datetime.now(dt.timezone.utc)) or []
want_deals = []
for d in deals:
    if d.order==want or d.position_id==want or d.ticket==want:
        want_deals.append({
          "ticket": d.ticket, "order": d.order, "position_id": d.position_id,
          "symbol": d.symbol, "type": d.type, "entry": d.entry,
          "price": d.price, "profit": d.profit, "volume": d.volume,
          "comment": d.comment, "time": d.time,
          "time_ict": dt.datetime.fromtimestamp(d.time, tz=dt.timezone.utc).astimezone(dt.timezone(dt.timedelta(hours=7))).strftime("%Y-%m-%d %H:%M ICT"),
        })
out["want_deals"] = want_deals[:12]
# hist orders for rest vs lift
orders_hist = mt5.history_orders_get(from_dt, dt.datetime.now(dt.timezone.utc)) or []
for o in orders_hist:
    if o.ticket == want:
        out["hist_order"] = {
          "type": typemap.get(o.type, str(o.type)),
          "price_open": o.price_open, "price_current": o.price_current,
          "sl": o.sl, "tp": o.tp, "volume_initial": o.volume_initial,
          "state": o.state, "comment": o.comment,
        }
# M15 last bars
rates = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_M15, 0, 6)
if rates is not None:
    out["m15_last"] = [{"t": int(r[0]), "o": float(r[1]), "h": float(r[2]), "l": float(r[3]), "c": float(r[4])} for r in rates]
# writer task
try:
  r = subprocess.run(["schtasks","/Query","/TN","GTOS_F5_FTMO","/FO","LIST","/V"],
    capture_output=True, text=True, timeout=15)
  status = None
  for line in (r.stdout or "").splitlines():
    if line.strip().startswith("Status:"):
      status = line.split(":",1)[1].strip(); break
  out["writer"] = f"GTOS_F5_FTMO {status or 'unknown'}"
except Exception as e:
  out["writer_err"] = str(e)
mt5.shutdown()
out["ok"] = True
print(json.dumps(out, default=str))
