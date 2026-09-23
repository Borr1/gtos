import MetaTrader5 as mt5, json
from datetime import datetime, timezone
out = {"ok": False}
if not mt5.initialize():
    out["err"] = str(mt5.last_error()); print(json.dumps(out)); raise SystemExit(1)
acc = mt5.account_info()
out.update({
    "ok": True,
    "probe_utc": datetime.now(timezone.utc).isoformat(),
    "login": acc.login, "server": acc.server,
    "balance": acc.balance, "equity": acc.equity,
    "floating": acc.equity - acc.balance,
    "to_pass": 105000 - acc.balance if acc.balance < 105000 else 0,
})
# day net approx from deals today
from datetime import timedelta
day0 = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
# broker often UTC+3; use deals profit today loosely via positions+history
open_pos = []
for p in (mt5.positions_get() or []):
    open_pos.append({
        "ticket": p.ticket, "symbol": p.symbol, "side": "LONG" if p.type==0 else "SHORT",
        "volume": p.volume, "entry": p.price_open, "sl": p.sl, "tp": p.tp,
        "pnl": p.profit, "swap": p.swap, "comment": p.comment, "magic": p.magic,
    })
pending = []
for o in (mt5.orders_get() or []):
    tmap = {2:"BUY_LIMIT",3:"SELL_LIMIT",4:"BUY_STOP",5:"SELL_STOP"}
    pending.append({
        "ticket": o.ticket, "symbol": o.symbol, "type": tmap.get(o.type, str(o.type)),
        "type_i": o.type, "volume": o.volume_current, "price": o.price_open,
        "sl": o.sl, "tp": o.tp, "comment": o.comment, "magic": o.magic,
        "time_setup": o.time_setup,
    })
out["open"] = open_pos
out["pending"] = pending
tick = mt5.symbol_info_tick("GBPUSD")
if tick:
    out["gbpusd_bid"] = tick.bid; out["gbpusd_ask"] = tick.ask
    out["gbpusd_spread"] = round(tick.ask - tick.bid, 6)
want = 180775773
out["want_ticket"] = want
out["want_in_positions"] = any(p["ticket"]==want for p in open_pos)
out["want_in_orders"] = any(o["ticket"]==want for o in pending)
# M15 last bars for GBPUSD
rates = mt5.copy_rates_from_pos("GBPUSD", mt5.TIMEFRAME_M15, 0, 25)
if rates is not None and len(rates):
    bars = []
    for r in rates[-5:]:
        bars.append({"t": int(r["time"]), "o": float(r["open"]), "h": float(r["high"]),
                     "l": float(r["low"]), "c": float(r["close"])})
    out["m15_last5"] = bars
    lows = [float(r["low"]) for r in rates]
    out["m15_20_low"] = min(lows[-20:]) if len(lows)>=20 else min(lows)
    out["m15_20_high"] = max([float(r["high"]) for r in rates[-20:]])
# hist order for want
hist = mt5.history_orders_get(ticket=want)
if hist:
    h = hist[0]
    tmap = {0:"BUY",1:"SELL",2:"BUY_LIMIT",3:"SELL_LIMIT",4:"BUY_STOP",5:"SELL_STOP"}
    out["hist_order"] = {"type": tmap.get(h.type, str(h.type)), "price_open": h.price_open,
                         "sl": h.sl, "tp": h.tp, "volume_initial": h.volume_initial,
                         "state": h.state, "comment": h.comment}
# writer process rough
import subprocess
try:
    r = subprocess.run(["powershell","-NoProfile","-Command",
        "Get-Process | Where-Object { $_.ProcessName -match 'python|GTOS' } | Select-Object Id,ProcessName | ConvertTo-Json -Compress"],
        capture_output=True, text=True, timeout=8)
    out["ps_snip"] = (r.stdout or "")[:500]
except Exception as e:
    out["ps_err"] = str(e)
mt5.shutdown()
print(json.dumps(out, default=str))
