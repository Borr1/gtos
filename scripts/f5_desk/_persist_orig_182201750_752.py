import json
from pathlib import Path
from datetime import datetime, timezone

now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
adds = {
  "182201750": {"sl": 4393.89, "tp": 4450.4},
  "182201752": {"sl": 52910.05, "tp": 53109.48},
}
paths = [
    Path(r"host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\judgment\state\chair_orig_sl.json"),
    Path(r"host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\chair_orig_sl.json"),
    Path(r"host-local\redacted_host\repo\judgment\state\chair_orig_sl.json"),
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
    m = load(p) if p.exists() else {"tickets": {}, "tps": {}, "note": "chair-persisted orig SL from broker-held prints; never moved"}
    tickets = m.setdefault("tickets", {})
    tps = m.setdefault("tps", {})
    changed = False
    for tid, vals in adds.items():
        before_sl = tickets.get(tid)
        before_tp = tps.get(tid) if isinstance(tps, dict) else None
        if tid not in tickets:
            tickets[tid] = vals["sl"]
            changed = True
        if isinstance(tps, dict) and tid not in tps:
            tps[tid] = vals["tp"]
            changed = True
        results.append({"path": str(p), "ticket": tid, "before_sl": before_sl, "before_tp": before_tp, "sl": tickets.get(tid), "tp": tps.get(tid) if isinstance(tps, dict) else None})
    if changed:
        m["tickets"] = tickets
        m["tps"] = tps
        m["updated_utc"] = now
        m["updated_by"] = "f5-chair-sit-fill"
        m["source"] = "f5-chair-sit"
        m["note"] = "chair-persisted orig SL/TP from live broker on first sit after fill; never moved"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(m, indent=2), encoding="utf-8")
        results.append({"path": str(p), "action": "wrote", "updated_utc": now})
    else:
        results.append({"path": str(p), "action": "unchanged"})

# verify live eq
broker = {}
try:
    import MetaTrader5 as mt5
    ok = mt5.initialize(path=r"C:\MT5\FTMO\terminal64.exe")
    acc = mt5.account_info()
    broker = {"ok": bool(ok), "login": int(acc.login), "bal": float(acc.balance), "eq": float(acc.equity)}
    live = {}
    for p in mt5.positions_get() or []:
        if int(p.ticket) in (182201750, 182201752, 180734064, 181801555, 181801554):
            live[str(p.ticket)] = {
                "symbol": p.symbol, "side": "LONG" if p.type==0 else "SHORT",
                "lots": float(p.volume), "entry": float(p.price_open),
                "sl": float(p.sl), "tp": float(p.tp), "pnl": float(p.profit),
                "magic": int(p.magic), "comment": p.comment,
            }
    broker["live"] = live
    mt5.shutdown()
except Exception as e:
    broker["exc"] = str(e)

print(json.dumps({"results": results, "broker": broker}, indent=2))
