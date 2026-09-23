import json
from datetime import datetime, timezone, timedelta
import MetaTrader5 as mt5

WANT = 180335205
SYM = "ETHUSD"
MT5_PATH = r"C:\MT5\FTMO\terminal64.exe"
TYPE_MAP = {0: "BUY", 1: "SELL", 2: "BUY_LIMIT", 3: "SELL_LIMIT", 4: "BUY_STOP", 5: "SELL_STOP"}
REASON_MAP = {0:"CLIENT",1:"MOBILE",2:"WEB",3:"EXPERT",4:"SL",5:"TP",6:"SO",7:"ROLLOVER",8:"VMARGIN",9:"SPLIT",10:"CORPORATE"}

ok = mt5.initialize(path=MT5_PATH) or mt5.initialize()
out = {"ok": bool(ok), "err": None if ok else str(mt5.last_error())}
if not ok:
    print(json.dumps(out)); raise SystemExit(1)

now = datetime.now(timezone.utc)
# try multiple windows: wall UTC and +3h broker skew
windows = []
for hours in (6, 24, 72):
    windows.append(("wall_%dh" % hours, now - timedelta(hours=hours), now + timedelta(hours=1)))
    windows.append(("skew3_%dh" % hours, now - timedelta(hours=hours) + timedelta(hours=3), now + timedelta(hours=4)))

# also from_pos style via date ints around position time 1788252383
pos_t = 1788252383
from datetime import timezone as tz
pos_dt = datetime.fromtimestamp(pos_t, tz=timezone.utc)

all_hits = []
seen = set()
for label, a, b in windows:
    deals = mt5.history_deals_get(a, b) or []
    for d in deals:
        if int(getattr(d, "position_id", 0) or 0) == WANT or int(getattr(d, "order", 0) or 0) == WANT:
            key = int(d.ticket)
            if key in seen: continue
            seen.add(key)
            all_hits.append({
                "via": label,
                "deal": int(d.ticket),
                "order": int(getattr(d, "order", 0) or 0),
                "position_id": int(getattr(d, "position_id", 0) or 0),
                "symbol": d.symbol,
                "type": int(d.type),
                "entry": int(getattr(d, "entry", 0) or 0),
                "volume": float(d.volume),
                "price": float(d.price),
                "profit": float(d.profit),
                "commission": float(getattr(d, "commission", 0) or 0),
                "comment": d.comment,
                "magic": int(getattr(d, "magic", 0) or 0),
                "reason": int(getattr(d, "reason", -1) or -1),
                "reason_name": REASON_MAP.get(int(getattr(d, "reason", -1) or -1)),
                "time_raw": int(d.time),
                "time_as_utc": datetime.fromtimestamp(int(d.time), tz=timezone.utc).isoformat(),
            })

# ETH deals recent
eth = []
deals = mt5.history_deals_get(now - timedelta(days=5), now + timedelta(hours=4)) or []
for d in deals:
    if d.symbol == "ETHUSD":
        eth.append({
            "deal": int(d.ticket), "order": int(getattr(d,"order",0) or 0),
            "position_id": int(getattr(d,"position_id",0) or 0),
            "type": int(d.type), "entry": int(getattr(d,"entry",0) or 0),
            "volume": float(d.volume), "price": float(d.price),
            "profit": float(d.profit), "comment": d.comment,
            "time_raw": int(d.time),
            "time_as_utc": datetime.fromtimestamp(int(d.time), tz=timezone.utc).isoformat(),
        })

orders_hits = []
for label, a, b in windows[:4]:
    orders_h = mt5.history_orders_get(a, b) or []
    for o in orders_h:
        if int(o.ticket) == WANT or int(getattr(o, "position_id", 0) or 0) == WANT or (o.symbol=="ETHUSD" and abs(int(getattr(o,"time_setup",0) or 0) - pos_t) < 600):
            orders_hits.append({
                "via": label,
                "ticket": int(o.ticket),
                "symbol": o.symbol,
                "type": TYPE_MAP.get(int(o.type), str(int(o.type))),
                "type_i": int(o.type),
                "state": int(getattr(o, "state", -1) or -1),
                "volume_initial": float(getattr(o, "volume_initial", 0) or 0),
                "price_open": float(o.price_open),
                "sl": float(o.sl), "tp": float(o.tp),
                "comment": o.comment,
                "position_id": int(getattr(o, "position_id", 0) or 0),
                "time_setup": int(getattr(o, "time_setup", 0) or 0),
                "time_done": int(getattr(o, "time_done", 0) or 0),
            })

# also orders_get history by ticket
ord_by = mt5.history_orders_get(ticket=WANT)
out["hist_orders_by_ticket"] = None
if ord_by:
    out["hist_orders_by_ticket"] = [{
        "ticket": int(o.ticket), "type": TYPE_MAP.get(int(o.type), str(int(o.type))),
        "type_i": int(o.type), "price_open": float(o.price_open),
        "sl": float(o.sl), "tp": float(o.tp), "comment": o.comment,
        "volume_initial": float(getattr(o,"volume_initial",0) or 0),
        "state": int(getattr(o,"state",-1) or -1),
        "time_setup": int(getattr(o,"time_setup",0) or 0),
        "time_done": int(getattr(o,"time_done",0) or 0),
        "position_id": int(getattr(o,"position_id",0) or 0),
    } for o in ord_by]

deal_by = mt5.history_deals_get(position=WANT)
out["deals_by_position"] = None
if deal_by:
    out["deals_by_position"] = [{
        "deal": int(d.ticket), "order": int(getattr(d,"order",0) or 0),
        "position_id": int(getattr(d,"position_id",0) or 0),
        "type": int(d.type), "entry": int(getattr(d,"entry",0) or 0),
        "volume": float(d.volume), "price": float(d.price),
        "profit": float(d.profit), "commission": float(getattr(d,"commission",0) or 0),
        "comment": d.comment, "reason": int(getattr(d,"reason",-1) or -1),
        "reason_name": REASON_MAP.get(int(getattr(d,"reason",-1) or -1)),
        "time_raw": int(d.time),
        "time_as_utc": datetime.fromtimestamp(int(d.time), tz=timezone.utc).isoformat(),
    } for d in deal_by]

out["want_hits"] = all_hits
out["eth_recent"] = eth[-12:]
out["orders_hits"] = orders_hits[:8]
out["pos_time_as_utc"] = pos_dt.isoformat()
# slate path scan for orb_crypto
from pathlib import Path
base = Path(r"host-local\redacted_host\repo\pipeline_state\ultimate_book\operator")
slate = base / "judgment" / "state" / "latest_slate.json"
hits = []
if slate.exists():
    sd = json.loads(slate.read_text(encoding="utf-8"))
    path = sd.get("path")
    body = None
    if path:
        p = Path(path) if Path(path).is_absolute() else base / path
        if p.exists():
            body = json.loads(p.read_text(encoding="utf-8"))
    if body is None:
        body = sd
    for c in (body.get("candidates") or body.get("intents") or []) if isinstance(body, dict) else []:
        blob = json.dumps(c).lower()
        if "eth" in blob or "orb_crypto" in blob or "crypto" in blob:
            hits.append({k:c.get(k) for k in list(c)[:20]})
out["slate_crypto"] = hits[:10]
# also list recent slate files
jdir = base / "judgment" / "state"
files = sorted(jdir.glob("*slate*"), key=lambda p: p.stat().st_mtime, reverse=True)[:6]
out["slate_files"] = [f.name for f in files]
# intent / events for this ticket
for rel in [
    r"judgment\state\events.jsonl",
    r"events.jsonl",
    r"judgment\live\events.jsonl",
]:
    p = base / rel
    if p.exists():
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()[-80:]
        matched = [l for l in lines if "180335205" in l or ("ETHUSD" in l and "orb" in l.lower())]
        out["events_"+rel.replace("\\","_")] = matched[-6:]

print(json.dumps(out, default=str))
mt5.shutdown()
