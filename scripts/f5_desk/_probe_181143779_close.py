import json
from datetime import datetime, timezone, timedelta
import MetaTrader5 as mt5

WANT = 181143779
ORIG_SL = 53137.71
ENTRY = 53149.42
TP = 53172.09
SYM = "US30.cash"

mt5.initialize(path=r"C:\MT5\FTMO\terminal64.exe") or mt5.initialize()
now = datetime.now(timezone.utc)
ict = timezone(timedelta(hours=7))

REASON_MAP = {
    0: "CLIENT", 1: "MOBILE", 2: "WEB", 3: "EXPERT",
    4: "SL", 5: "TP", 6: "SO", 7: "ROLLOVER", 8: "EXTERNAL_CLIENT",
    9: "VMARGIN", 10: "SPLIT", 11: "EXTERNAL_SERVICE", 12: "CLOSE_BY",
}

opens = []
for p in (mt5.positions_get() or []):
    opens.append({
        "ticket": int(p.ticket), "symbol": p.symbol, "type": int(p.type),
        "price_open": float(p.price_open), "sl": float(p.sl), "tp": float(p.tp),
        "volume": float(p.volume), "profit": float(p.profit), "comment": p.comment,
    })

still_open = any(int(p["ticket"]) == WANT for p in opens)

hits = []
try:
    deals_pos = mt5.history_deals_get(position=WANT) or []
except Exception:
    deals_pos = []
for d in deals_pos:
    hits.append({
        "deal": int(d.ticket), "order": int(getattr(d, "order", 0) or 0),
        "pos": int(getattr(d, "position_id", 0) or 0),
        "entry": int(getattr(d, "entry", 0) or 0),
        "price": float(d.price), "profit": float(d.profit),
        "swap": float(getattr(d, "swap", 0) or 0),
        "commission": float(getattr(d, "commission", 0) or 0),
        "comment": d.comment,
        "reason": int(getattr(d, "reason", 0) or 0),
        "reason_name": REASON_MAP.get(int(getattr(d, "reason", 0) or 0), "?"),
        "time_raw": int(d.time),
        "utc": datetime.fromtimestamp(int(d.time), tz=timezone.utc).isoformat(),
        "ict": datetime.fromtimestamp(int(d.time), tz=timezone.utc).astimezone(ict).strftime("%Y-%m-%d %H:%M:%S ICT"),
        "vol": float(d.volume), "symbol": d.symbol,
    })

if not hits:
    deals = mt5.history_deals_get(now - timedelta(hours=12), now + timedelta(hours=2)) or []
    for d in deals:
        if int(getattr(d, "position_id", 0) or 0) == WANT or int(getattr(d, "order", 0) or 0) == WANT:
            hits.append({
                "deal": int(d.ticket), "order": int(getattr(d, "order", 0) or 0),
                "pos": int(getattr(d, "position_id", 0) or 0),
                "entry": int(getattr(d, "entry", 0) or 0),
                "price": float(d.price), "profit": float(d.profit),
                "swap": float(getattr(d, "swap", 0) or 0),
                "commission": float(getattr(d, "commission", 0) or 0),
                "comment": d.comment,
                "reason": int(getattr(d, "reason", 0) or 0),
                "reason_name": REASON_MAP.get(int(getattr(d, "reason", 0) or 0), "?"),
                "time_raw": int(d.time),
                "utc": datetime.fromtimestamp(int(d.time), tz=timezone.utc).isoformat(),
                "ict": datetime.fromtimestamp(int(d.time), tz=timezone.utc).astimezone(ict).strftime("%Y-%m-%d %H:%M:%S ICT"),
                "vol": float(d.volume), "symbol": d.symbol,
            })

outs = [h for h in hits if h["entry"] == 1]
ins = [h for h in hits if h["entry"] == 0]
exit_deal = outs[-1] if outs else None
exit_class = None
exit_px = None
profit = None
broker_comment = None
if exit_deal:
    exit_px = exit_deal["price"]
    profit = exit_deal["profit"] + exit_deal.get("swap", 0) + exit_deal.get("commission", 0)
    broker_comment = exit_deal["comment"]
    rname = exit_deal["reason_name"]
    c = (broker_comment or "").lower()
    r_pts = abs(ENTRY - ORIG_SL)
    near_sl = abs(exit_px - ORIG_SL) <= max(0.5, 0.25 * r_pts) if r_pts else False
    near_tp = abs(exit_px - TP) <= max(0.5, 0.25 * abs(TP - ENTRY)) if TP else False
    import re
    m = re.search(r"\[sl\s+([0-9.]+)\]", c)
    if rname == "SL" or "[sl" in c or near_sl:
        exit_class = "orig_stop"
        if m:
            sl_lvl = float(m.group(1))
            if abs(sl_lvl - ORIG_SL) > 0.5 and abs(exit_px - ORIG_SL) > max(0.5, 0.25 * r_pts):
                exit_class = "moved_stop"
            else:
                exit_class = "orig_stop"
        elif abs(exit_px - ORIG_SL) > max(1.0, 0.5 * r_pts):
            exit_class = "moved_stop"
    elif rname == "TP" or "[tp" in c or near_tp:
        exit_class = "broker_tp"
    elif "so" in c or rname == "SO":
        exit_class = "flatten"
    elif "time" in c or "sleeve" in c or "time_stop" in c:
        exit_class = "time_stop"
    elif "expir" in c or "limit_exp" in c:
        exit_class = "limit_expired"
    elif rname in ("CLIENT", "MOBILE", "WEB"):
        exit_class = "chair_close"
    elif rname == "EXPERT":
        if near_sl:
            exit_class = "orig_stop"
        elif near_tp:
            exit_class = "broker_tp"
        elif "time" in c or "sleeve" in c:
            exit_class = "time_stop"
        else:
            exit_class = "flatten"
    else:
        exit_class = "flatten"

ai = mt5.account_info()
r_pts = abs(ENTRY - ORIG_SL)
unit_risk = 150.0
realised_r = (profit / unit_risk) if profit is not None else None
sl_dist = abs(exit_px - ORIG_SL) if exit_px is not None else None
tp_dist = abs(exit_px - TP) if exit_px is not None else None
entry_dist = abs(exit_px - ENTRY) if exit_px is not None else None

out = {
    "ok": True,
    "want": WANT,
    "still_open": still_open,
    "opens": opens,
    "hits": hits,
    "exit_deal": exit_deal,
    "exit_class": exit_class,
    "exit_px": exit_px,
    "profit": profit,
    "broker_comment": broker_comment,
    "orig_sl": ORIG_SL,
    "entry": ENTRY,
    "tp": TP,
    "r_pts": r_pts,
    "sl_dist": sl_dist,
    "tp_dist": tp_dist,
    "entry_dist": entry_dist,
    "realised_r_vs_unit150": realised_r,
    "bal": ai.balance if ai else None,
    "eq": ai.equity if ai else None,
    "login": ai.login if ai else None,
    "probe_ict": now.astimezone(ict).strftime("%Y-%m-%d %H:%M:%S ICT"),
}
print(json.dumps(out, indent=2))
mt5.shutdown()
