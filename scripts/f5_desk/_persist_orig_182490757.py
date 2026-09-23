import json
from pathlib import Path
from datetime import datetime, timezone

now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
TID = "182490757"
SL = 4361.03
TP = 4421.24
NOTE = (
    "fill XAUUSD 182490757: confirm orig SL 4361.03 TP 4421.24 from fill payload after ~2m; "
    "live==orig; judgment live+state+pipeline TP latched; leave orig; retain prior tickets"
)
adds_ticket = SL
adds_tp = TP

paths = [
    Path(r"host-local\redacted_host\repo\judgment\live\chair_orig_sl.json"),
    Path(r"host-local\redacted_host\repo\judgment\state\chair_orig_sl.json"),
    Path(r"host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\chair_orig_sl.json"),
    Path(r"host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\judgment\state\chair_orig_sl.json"),
    Path(r"host-local\redacted_host\repo\chair_orig_sl.json"),
]

def load(p: Path):
    raw = p.read_bytes()
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        text = raw.decode("utf-16")
    else:
        text = raw.decode("utf-8-sig")
    return json.loads(text)

results = []
for p in paths:
    m = load(p) if p.exists() else {"tickets": {}, "tps": {}, "note": "chair-persisted orig"}
    tickets = m.setdefault("tickets", {})
    tps = m.setdefault("tps", {})
    if not isinstance(tps, dict):
        tps = {}
        m["tps"] = tps
    before_sl = tickets.get(TID)
    before_tp = tps.get(TID)
    changed = False
    if TID not in tickets:
        tickets[TID] = adds_ticket
        changed = True
    if TID not in tps:
        tps[TID] = adds_tp
        changed = True
    if changed:
        m["tickets"] = tickets
        m["tps"] = tps
        m["updated_utc"] = now
        m["updated_by"] = f"f5-book-event-fill-{TID}"
        m["source"] = "f5-book-event-fill"
        m["note"] = NOTE
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(m, indent=1) + "\n", encoding="utf-8")
        results.append({"path": str(p), "action": "wrote", "before_sl": before_sl, "before_tp": before_tp, "sl": tickets[TID], "tp": tps[TID]})
    else:
        # already present — do not overwrite
        results.append({"path": str(p), "action": "unchanged", "sl": tickets.get(TID), "tp": tps.get(TID)})

# broker verify
broker = {}
try:
    import MetaTrader5 as mt5
    ok = mt5.initialize(path=r"C:\MT5\FTMO\terminal64.exe")
    acc = mt5.account_info()
    broker = {
        "ok": bool(ok),
        "login": int(acc.login) if acc else None,
        "bal": float(acc.balance) if acc else None,
        "eq": float(acc.equity) if acc else None,
    }
    live = {}
    for p in mt5.positions_get() or []:
        live[str(p.ticket)] = {
            "symbol": p.symbol,
            "side": "LONG" if p.type == 0 else "SHORT",
            "lots": float(p.volume),
            "entry": float(p.price_open),
            "sl": float(p.sl),
            "tp": float(p.tp),
            "pnl": float(p.profit),
            "magic": int(p.magic),
            "comment": p.comment,
        }
    broker["live"] = live
    mt5.shutdown()
except Exception as e:
    broker["exc"] = str(e)

print(json.dumps({"results": results, "broker": broker, "now": now}, indent=2))
