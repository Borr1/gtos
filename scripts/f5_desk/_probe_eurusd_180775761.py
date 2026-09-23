import json, MetaTrader5 as mt5, datetime as dt
out = {"ok": False}
if not mt5.initialize():
    out["err"] = str(mt5.last_error()); print(json.dumps(out)); raise SystemExit(1)
ai = mt5.account_info()
out.update({
  "login": ai.login, "balance": ai.balance, "equity": ai.equity,
  "floating": round(ai.equity - ai.balance, 2),
  "to_pass": round(105000 - ai.balance, 2),
  "probe_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
})
want = 180775761
positions = mt5.positions_get() or []
orders = mt5.orders_get() or []
open_rows = []
for p in positions:
    open_rows.append({
      "ticket": p.ticket, "symbol": p.symbol, "type": p.type,
      "side": "LONG" if p.type==0 else "SHORT",
      "lots": p.volume, "entry": p.price_open, "sl": p.sl, "tp": p.tp,
      "mark": p.price_current, "pnl": p.profit, "swap": p.swap,
      "comment": (p.comment or "")[:40],
    })
pend_rows = []
for o in orders:
    typemap = {0:"BUY",1:"SELL",2:"BUY_LIMIT",3:"SELL_LIMIT",4:"BUY_STOP",5:"SELL_STOP",6:"BUY_STOP_LIMIT",7:"SELL_STOP_LIMIT"}
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
# EURUSD tick + symbol info
sym = "EURUSD"
tick = mt5.symbol_info_tick(sym)
si = mt5.symbol_info(sym)
if tick:
    out["eurusd_bid"] = tick.bid; out["eurusd_ask"] = tick.ask
    out["eurusd_spread"] = round(tick.ask - tick.bid, 5)
if si:
    out["eurusd_point"] = si.point; out["eurusd_digits"] = si.digits
    out["eurusd_stops_level"] = si.trade_stops_level
    out["eurusd_tick_value"] = si.trade_tick_value
    out["eurusd_tick_size"] = si.trade_tick_size
    out["eurusd_volume_min"] = si.volume_min
# find want order details
for o in orders:
    if o.ticket == want:
        out["want"] = {
          "ticket": o.ticket, "symbol": o.symbol, "type": o.type,
          "type_name": {2:"BUY_LIMIT",3:"SELL_LIMIT",4:"BUY_STOP",5:"SELL_STOP"}.get(o.type, str(o.type)),
          "lots": o.volume_current, "price_open": o.price_open, "price_current": o.price_current,
          "sl": o.sl, "tp": o.tp, "comment": o.comment,
          "time_setup": o.time_setup, "expiration": o.time_expiration,
        }
for p in positions:
    if p.ticket == want:
        out["want_pos"] = {
          "ticket": p.ticket, "symbol": p.symbol, "type": p.type,
          "lots": p.volume, "entry": p.price_open, "sl": p.sl, "tp": p.tp,
          "mark": p.price_current, "pnl": p.profit, "comment": p.comment,
        }
# also scan history deals for this ticket today in case already filled+closed
from_dt = dt.datetime(2026,9,2,0,0,tzinfo=dt.timezone.utc)
deals = mt5.history_deals_get(from_dt, dt.datetime.now(dt.timezone.utc)) or []
want_deals = [d._asdict() if hasattr(d,'_asdict') else {
  "ticket": d.ticket, "order": d.order, "symbol": d.symbol, "type": d.type,
  "entry": d.entry, "price": d.price, "profit": d.profit, "volume": d.volume,
  "comment": d.comment, "time": d.time,
} for d in deals if d.order==want or d.position_id==want or d.ticket==want]
out["want_deals"] = want_deals[:10]
# writer process rough
import subprocess
try:
  r = subprocess.run(["powershell","-NoProfile","-Command",
    "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { $_.CommandLine -match 'GTOS_F5_FTMO|ultimate_book|book_owner' } | Select-Object ProcessId,CommandLine | ConvertTo-Json -Compress"],
    capture_output=True, text=True, timeout=15)
  out["writer_raw"] = (r.stdout or "")[:800]
except Exception as e:
  out["writer_err"] = str(e)
mt5.shutdown()
out["ok"] = True
print(json.dumps(out, default=str))
