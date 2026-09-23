import MetaTrader5 as mt5, json, os
from datetime import datetime, timezone, timedelta
from pathlib import Path

WANT = 180274922
ok = mt5.initialize(path=r"C:\MT5\FTMO\terminal64.exe")
if not ok:
    ok = mt5.initialize()
ai = mt5.account_info()
pos = mt5.positions_get() or []
ords = mt5.orders_get() or []
xtick = mt5.symbol_info_tick("XAUUSD")
si = mt5.symbol_info("XAUUSD")
now = datetime.now(timezone.utc)
deals = mt5.history_deals_get(now - timedelta(days=2), now) or []
TYPE_MAP = {0: "BUY", 1: "SELL", 2: "BUY_LIMIT", 3: "SELL_LIMIT", 4: "BUY_STOP", 5: "SELL_STOP"}
hits = []
xau_deals = []
for d in deals:
    rec = {
        "ticket": d.ticket, "order": d.order, "position_id": d.position_id,
        "symbol": d.symbol, "type": d.type, "entry": d.entry, "volume": d.volume,
        "price": d.price, "profit": d.profit, "commission": d.commission,
        "swap": d.swap, "comment": d.comment, "time": int(d.time),
        "time_utc": datetime.fromtimestamp(d.time, tz=timezone.utc).isoformat(),
        "magic": d.magic,
    }
    if d.position_id == WANT or d.order == WANT:
        hits.append(rec)
    if d.symbol in ("XAUUSD", "XAUUSD.") and d.magic in (0, 0):
        xau_deals.append(rec)
xau_deals = xau_deals[-12:]

# M15 last 8 bars
rates = mt5.copy_rates_from_pos("XAUUSD", mt5.TIMEFRAME_M15, 0, 8)
if rates is None:
    rates = []
bars = []
for r in rates:
    bars.append({
        "t": datetime.fromtimestamp(int(r["time"]), tz=timezone.utc).isoformat(),
        "o": float(r["open"]), "h": float(r["high"]), "l": float(r["low"]),
        "c": float(r["close"]), "v": int(r["tick_volume"]),
    })

out = {
    "ok": bool(ok),
    "init_err": mt5.last_error() if not ok else None,
    "login": ai.login if ai else None,
    "server": ai.server if ai else None,
    "balance": ai.balance if ai else None,
    "equity": ai.equity if ai else None,
    "floating": (ai.equity - ai.balance) if ai else None,
    "to_pass": (105000 - ai.balance) if ai else None,
    "open": [{
        "ticket": p.ticket, "symbol": p.symbol,
        "side": "LONG" if p.type == 0 else "SHORT",
        "volume": p.volume, "entry": p.price_open, "sl": p.sl, "tp": p.tp,
        "pnl": p.profit, "comment": p.comment, "magic": p.magic,
    } for p in pos],
    "pending": [{
        "ticket": o.ticket, "symbol": o.symbol, "type": TYPE_MAP.get(o.type, str(o.type)),
        "volume": o.volume_current, "price": o.price_open, "sl": o.sl, "tp": o.tp,
        "comment": o.comment, "magic": o.magic,
    } for o in ords],
    "xau_bid": xtick.bid if xtick else None,
    "xau_ask": xtick.ask if xtick else None,
    "xau_spread": (xtick.ask - xtick.bid) if xtick else None,
    "stops_level": si.trade_stops_level if si else None,
    "point": si.point if si else None,
    "probe_utc": now.isoformat(),
    "want_ticket": WANT,
    "want_in_positions": any(p.ticket == WANT for p in pos),
    "want_in_orders": any(o.ticket == WANT for o in ords),
    "hits": hits,
    "xau_deals_tail": xau_deals,
    "m15": bars,
}

# latest.json on VPS
LATEST = Path(r"host-local\redacted_host\repo\judgment\live\latest.json")
HB = Path(r"host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\heartbeat.json")
if LATEST.exists():
    try:
        lj = json.loads(LATEST.read_text(encoding="utf-8"))
        out["latest_mtime_utc"] = datetime.fromtimestamp(LATEST.stat().st_mtime, tz=timezone.utc).isoformat()
        out["latest_candidate_id"] = lj.get("candidate_id")
        ex = lj.get("execution") or {}
        ident = (ex.get("identity") or {})
        out["latest_symbol"] = ident.get("symbol")
        out["latest_action"] = ex.get("action")
        out["latest_generated_at_utc"] = ex.get("generated_at_utc")
        et = ex.get("entry_timing") or {}
        out["latest_entry"] = et.get("entry_price")
        out["latest_sl"] = et.get("stop_loss")
        out["latest_tp"] = et.get("take_profit_1")
        gc = ((ex.get("geometry_contract") or {}).get("contract") or {})
        si = gc.get("stop_invalidation") or {}
        td = gc.get("target_destination") or {}
        out["latest_direction"] = si.get("direction")
        out["latest_risk_distance"] = si.get("risk_distance")
        out["latest_final_target"] = td.get("final_target_price")
        out["latest_final_target_r"] = td.get("final_target_r")
        cc = ex.get("cost_context") or {}
        out["latest_spread_r"] = cc.get("spread_r")
        out["latest_max_spread_r"] = cc.get("max_spread_r")
        br = lj.get("broker") or {}
        req = ((br.get("order_send_observation") or {}).get("request") or {})
        out["latest_req"] = {k: req.get(k) for k in ("type","price","sl","tp","volume","comment","symbol")}
        out["fire_status"] = lj.get("fire_status")
        out["ticket_live"] = lj.get("ticket_live")
    except Exception as e:
        out["latest_err"] = str(e)
else:
    out["latest"] = "missing"
if HB.exists():
    try:
        out["hb"] = json.loads(HB.read_text(encoding="utf-8"))
        out["hb_mtime_utc"] = datetime.fromtimestamp(HB.stat().st_mtime, tz=timezone.utc).isoformat()
    except Exception as e:
        out["hb_err"] = str(e)

print(json.dumps(out, ensure_ascii=False, default=str))
mt5.shutdown()
