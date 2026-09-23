import MetaTrader5 as mt5, json, os
from datetime import datetime, timezone

ok = mt5.initialize()
out = {"init": bool(ok), "err": list(mt5.last_error()) if not ok else None}
ai = mt5.account_info()
if ai:
    out["account"] = {
        "login": ai.login, "balance": ai.balance, "equity": ai.equity,
        "profit": ai.profit, "margin": ai.margin, "free": ai.margin_free,
    }
out["positions"] = []
for p in (mt5.positions_get() or []):
    out["positions"].append({
        "ticket": p.ticket, "symbol": p.symbol, "type": p.type, "volume": p.volume,
        "price_open": p.price_open, "sl": p.sl, "tp": p.tp, "profit": p.profit,
        "magic": p.magic, "comment": p.comment, "time": p.time,
    })
out["orders"] = []
for o in (mt5.orders_get() or []):
    out["orders"].append({
        "ticket": o.ticket, "symbol": o.symbol, "type": o.type,
        "volume_current": o.volume_current, "price_open": o.price_open,
        "sl": o.sl, "tp": o.tp, "comment": o.comment,
    })
deals = mt5.history_deals_get(position=182201750)
out["deals"] = []
for d in (deals or []):
    out["deals"].append({
        "ticket": d.ticket, "order": d.order, "time": d.time, "time_msc": d.time_msc,
        "type": d.type, "entry": d.entry, "position_id": d.position_id,
        "symbol": d.symbol, "volume": d.volume, "price": d.price,
        "profit": d.profit, "commission": d.commission, "swap": d.swap,
        "fee": d.fee, "reason": d.reason, "comment": d.comment, "magic": d.magic,
    })
# also scan recent history window in case position filter empty
from datetime import timedelta
utc_from = datetime(2026, 9, 8, 6, 0, tzinfo=timezone.utc)
utc_to = datetime(2026, 9, 8, 9, 0, tzinfo=timezone.utc)
deals2 = mt5.history_deals_get(utc_from, utc_to)
out["recent_xau"] = []
for d in (deals2 or []):
    if d.symbol == "XAUUSD" and (d.position_id == 182201750 or "182201750" in str(d.comment)):
        out["recent_xau"].append({
            "ticket": d.ticket, "order": d.order, "time": d.time, "type": d.type,
            "entry": d.entry, "position_id": d.position_id, "price": d.price,
            "profit": d.profit, "commission": d.commission, "swap": d.swap,
            "reason": d.reason, "comment": d.comment, "volume": d.volume,
        })
paths = {
    "trade_record": r"host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\trade_records\182201750.json",
    "chair_orig": r"host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\judgment\live\chair_orig_sl.json",
    "latest_slate": r"host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\judgment\state\latest_slate.json",
}
out["files"] = {}
for k, p in paths.items():
    out["files"][k] = {"path": p, "exists": os.path.exists(p)}
    if os.path.exists(p):
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
            if k == "chair_orig":
                # keep only our ticket
                if isinstance(data, dict):
                    hit = data.get("182201750") or data.get(182201750)
                    if hit is None and "tickets" in data and isinstance(data["tickets"], dict):
                        hit = data["tickets"].get("182201750") or data["tickets"].get(182201750)
                    if hit is None:
                        # scan
                        for kk, vv in data.items():
                            if str(kk) == "182201750" or (isinstance(vv, dict) and vv.get("ticket") == 182201750):
                                hit = vv
                                break
                    out["files"][k]["ticket"] = hit
                    out["files"][k]["n_keys"] = len(data) if isinstance(data, dict) else None
            elif k == "latest_slate":
                inner = data.get("slate") if isinstance(data.get("slate"), dict) else data
                out["files"][k]["slate_id"] = (inner or {}).get("slate_id")
                out["files"][k]["fingerprint"] = (inner or {}).get("fingerprint")
            else:
                out["files"][k]["data"] = data
        except Exception as e:
            out["files"][k]["error"] = str(e)
print(json.dumps(out, indent=2, default=str))
mt5.shutdown()
