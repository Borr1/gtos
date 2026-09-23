import json
import MetaTrader5 as mt5
from datetime import datetime, timezone, timedelta
from pathlib import Path

ICT = timezone(timedelta(hours=7))
BROKER_OFFSET = timedelta(hours=3)
path = r"C:\MT5\FTMO\terminal64.exe"
assert mt5.initialize(path=path), mt5.last_error()

def wall(ts):
    broker_dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    wall_utc = broker_dt - BROKER_OFFSET
    return wall_utc, wall_utc.astimezone(ICT)

for pos, label in [(293611741, "XAU"), (293540988, "GBP")]:
    deals = list(mt5.history_deals_get(position=pos) or [])
    print("===", label, pos)
    tin = tout = None
    for d in deals:
        w, wi = wall(d.time)
        fmt = wi.strftime("%Y-%m-%d %H:%M ICT")
        print(
            " entry=%s deal=%s order=%s price=%s vol=%s profit=%s swap=%s comm=%s reason=%s comment=%r wall_utc=%s wall_ict=%s"
            % (d.entry, d.ticket, d.order, d.price, d.volume, d.profit, d.swap, d.commission, d.reason, d.comment, w.isoformat(), fmt)
        )
        if int(d.entry) == 0:
            tin = d
        if int(d.entry) == 1:
            tout = d
    if tin and tout:
        held = datetime.fromtimestamp(tout.time, tz=timezone.utc) - datetime.fromtimestamp(tin.time, tz=timezone.utc)
        net = float(tout.profit) + float(tout.swap) + float(tout.commission) + float(tin.commission)
        print(" held", held, "broker_net", round(net, 2), "R_unit150", round(net / 150.0, 2))

mt5.shutdown()

orig = json.loads(Path("judgment/live/chair_orig_sl.json").read_text(encoding="utf-8"))
print("orig_type", type(orig), "keys", list(orig.keys())[:12] if isinstance(orig, dict) else None)
inner = orig.get("tickets") if isinstance(orig.get("tickets"), dict) else orig
for k in ("293611741", "293540988"):
    print("orig", k, json.dumps(inner.get(k), default=str)[:500] if isinstance(inner, dict) else None)

for ticket in (293611741, 293540988):
    tr = json.loads(Path("pipeline_state/ultimate_book/operator/trade_records/%s.json" % ticket).read_text(encoding="utf-8"))
    print("TR", ticket, "keys", sorted(tr.keys())[:40])
    for k in sorted(tr.keys()):
        v = tr[k]
        if isinstance(v, (dict, list)) and len(json.dumps(v)) > 200:
            continue
        print(" ", k, "=", v)
