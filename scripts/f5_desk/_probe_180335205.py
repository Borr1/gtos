import json, subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path

WANT = 180335205
SYM = "ETHUSD"
LOGIN = 0
MT5_PATH = r"C:\MT5\FTMO\terminal64.exe"
HB = Path(r"host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\heartbeat.json")
ORIG = Path(r"host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\judgment\state\chair_orig_sl.json")
SLATE = Path(r"host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\judgment\state\latest_slate.json")
WEBHOOK_SL = 2466.44
WEBHOOK_TP = 2507.7
WEBHOOK_PRICE = 2480.6
WEBHOOK_VOL = 1.84

now = datetime.now(timezone.utc)
out = {"ok": False, "probe_utc": now.isoformat(), "want_ticket": WANT, "symbol": SYM}

try:
    t = subprocess.check_output(["schtasks", "/Query", "/TN", "GTOS_F5_FTMO", "/FO", "LIST", "/V"], text=True, errors="replace", timeout=20)
    keys = {}
    for line in t.splitlines():
        s = line.strip()
        for k in ("Status:", "Last Run Time:", "Last Result:"):
            if s.startswith(k):
                keys[k[:-1]] = s[len(k):].strip()
    out["task"] = keys
    out["writer"] = f"GTOS_F5_FTMO {keys.get('Status', '?')}"
except Exception as e:
    out["task"] = {"err": str(e)}
    out["writer"] = "unknown"

if HB.exists():
    hb = json.loads(HB.read_text(encoding="utf-8"))
    out["hb"] = {k: hb.get(k) for k in ("ts", "ts_utc", "as_of_utc", "pid", "healthy", "namespace", "status", "login") if k in hb}
    out["hb_mtime"] = datetime.fromtimestamp(HB.stat().st_mtime, tz=timezone.utc).isoformat()
    out["healthy"] = bool(hb.get("healthy", True))
    out["pair_pid"] = hb.get("pid")
else:
    out["hb"] = {"exists": False}
    out["healthy"] = None

if ORIG.exists():
    od = json.loads(ORIG.read_text(encoding="utf-8"))
    tickets = od.get("tickets") or od
    out["orig_file"] = tickets.get(str(WANT)) or tickets.get(WANT) if isinstance(tickets, dict) else None
else:
    out["orig_file"] = None

slate_hits = []
if SLATE.exists():
    sd = json.loads(SLATE.read_text(encoding="utf-8"))
    out["slate_meta"] = {k: sd.get(k) for k in ("slate_id", "built_at_utc", "fingerprint")}
    path = sd.get("path")
    body = None
    if path:
        p = Path(path)
        if not p.is_absolute():
            p = Path(r"host-local\redacted_host\repo\pipeline_state\ultimate_book\operator") / path
        if p.exists():
            body = json.loads(p.read_text(encoding="utf-8"))
    if body is None and isinstance(sd.get("candidates"), list):
        body = sd
    if isinstance(body, dict):
        cands = body.get("candidates") or body.get("intents") or body.get("rows") or []
        for c in (cands if isinstance(cands, list) else []):
            if not isinstance(c, dict):
                continue
            blob = json.dumps(c).upper()
            if "ETH" in blob or "ORB_CRYPTO" in blob or "CRYPTO" in blob or str(WANT) in blob:
                keep = {k: c.get(k) for k in ("symbol","ticket","side","direction","comment","price","sl","tp","volume","family","cid","candidate_id","type","limit","entry","stop","session") if k in c}
                if not keep:
                    keep = {k: c.get(k) for k in list(c)[:18]}
                slate_hits.append(keep)
out["slate_eth"] = slate_hits[:8]

import MetaTrader5 as mt5
ok = mt5.initialize(path=MT5_PATH)
if not ok:
    ok = mt5.initialize()
out["mt5_ok"] = bool(ok)
out["mt5_err"] = None if ok else str(mt5.last_error())
if not ok:
    print(json.dumps(out, default=str))
    raise SystemExit(1)

ai = mt5.account_info()
pos = mt5.positions_get() or []
ords = mt5.orders_get() or []
tick = mt5.symbol_info_tick(SYM)
xtick = mt5.symbol_info_tick("XAUUSD")
utick = mt5.symbol_info_tick("US30.cash")
ktick = mt5.symbol_info_tick("UK100.cash")
info = mt5.symbol_info(SYM)
TYPE_MAP = {0: "BUY", 1: "SELL", 2: "BUY_LIMIT", 3: "SELL_LIMIT", 4: "BUY_STOP", 5: "SELL_STOP"}
REASON_MAP = {
    0: "CLIENT", 1: "MOBILE", 2: "WEB", 3: "EXPERT",
    4: "SL", 5: "TP", 6: "SO", 7: "ROLLOVER", 8: "VMARGIN",
    9: "SPLIT", 10: "CORPORATE",
}

open_rows = []
want_pos = None
for p in pos:
    row = {
        "ticket": int(p.ticket), "symbol": p.symbol,
        "side": "LONG" if int(p.type) == 0 else "SHORT",
        "volume": float(p.volume), "entry": float(p.price_open),
        "sl": float(p.sl), "tp": float(p.tp), "pnl": float(p.profit),
        "comment": p.comment, "magic": int(getattr(p, "magic", 0) or 0),
        "time": int(getattr(p, "time", 0) or 0),
    }
    open_rows.append(row)
    if int(p.ticket) == WANT:
        want_pos = row

pending = []
for o in ords:
    pending.append({
        "ticket": int(o.ticket), "symbol": o.symbol,
        "type": TYPE_MAP.get(int(o.type), str(int(o.type))),
        "volume": float(o.volume_current), "price": float(o.price_open),
        "sl": float(o.sl), "tp": float(o.tp), "comment": o.comment,
        "magic": int(getattr(o, "magic", 0) or 0),
    })

bal = float(ai.balance) if ai else None
eq = float(ai.equity) if ai else None
out["login"] = int(ai.login) if ai else None
out["server"] = ai.server if ai else None
out["balance"] = bal
out["equity"] = eq
out["floating"] = (eq - bal) if (eq is not None and bal is not None) else None
out["to_pass"] = round(105000.0 - bal, 2) if bal is not None else None
# day open approx from earlier sits: start ~96156.94 then XAU take moved bal; use current bal-based day_net from equity vs yesterday close is hard — keep equity-balance floating + note bal
out["day_net_vs_96156"] = round(eq - 96156.94, 2) if eq is not None else None
out["open"] = open_rows
out["pending"] = pending
out["want_in_positions"] = want_pos is not None
out["want_in_orders"] = any(int(o["ticket"]) == WANT for o in pending)
out["want_pos"] = want_pos

out["eth_bid"] = float(tick.bid) if tick else None
out["eth_ask"] = float(tick.ask) if tick else None
out["eth_spread"] = float(tick.ask - tick.bid) if tick else None
out["xau_bid"] = float(xtick.bid) if xtick else None
out["xau_ask"] = float(xtick.ask) if xtick else None
out["us30_bid"] = float(utick.bid) if utick else None
out["us30_ask"] = float(utick.ask) if utick else None
out["uk100_bid"] = float(ktick.bid) if ktick else None
out["uk100_ask"] = float(ktick.ask) if ktick else None

if info:
    out["spec"] = {
        "point": float(info.point),
        "digits": int(info.digits),
        "tick_value": float(info.trade_tick_value),
        "tick_size": float(info.trade_tick_size),
        "contract": float(info.trade_contract_size),
        "stops_level": int(info.trade_stops_level),
        "spread": int(info.spread),
    }

deals = mt5.history_deals_get(now - timedelta(hours=24), now) or []
want_deals = []
for d in deals:
    if int(getattr(d, "position_id", 0) or 0) == WANT or int(getattr(d, "order", 0) or 0) == WANT or int(d.ticket) == WANT:
        raw_t = int(d.time)
        want_deals.append({
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
            "time_raw": raw_t,
            "time_as_utc": datetime.fromtimestamp(raw_t, tz=timezone.utc).isoformat(),
        })
out["want_deals"] = want_deals

orders_h = mt5.history_orders_get(now - timedelta(hours=24), now) or []
hist_ord = None
for o in orders_h:
    if int(o.ticket) == WANT or int(getattr(o, "position_id", 0) or 0) == WANT:
        hist_ord = {
            "ticket": int(o.ticket),
            "symbol": o.symbol,
            "type": TYPE_MAP.get(int(o.type), str(int(o.type))),
            "type_i": int(o.type),
            "state": int(getattr(o, "state", -1) or -1),
            "volume_initial": float(getattr(o, "volume_initial", 0) or 0),
            "price_open": float(o.price_open),
            "price_current": float(getattr(o, "price_current", 0) or 0),
            "sl": float(o.sl),
            "tp": float(o.tp),
            "comment": o.comment,
            "time_setup": int(getattr(o, "time_setup", 0) or 0),
            "time_done": int(getattr(o, "time_done", 0) or 0),
        }
        break
out["hist_order"] = hist_ord

rates = mt5.copy_rates_from_pos(SYM, mt5.TIMEFRAME_M15, 0, 24)
m15 = []
if rates is not None:
    for r in rates:
        m15.append({
            "t": datetime.fromtimestamp(int(r["time"]), tz=timezone.utc).strftime("%H:%M"),
            "t_utc": datetime.fromtimestamp(int(r["time"]), tz=timezone.utc).isoformat(),
            "o": float(r["open"]), "h": float(r["high"]),
            "l": float(r["low"]), "c": float(r["close"]),
        })
out["m15"] = m15[-16:]
out["m15_last"] = m15[-1] if m15 else None
out["m15_session_low"] = min((b["l"] for b in m15), default=None) if m15 else None
out["m15_session_high"] = max((b["h"] for b in m15), default=None) if m15 else None

entry = want_pos["entry"] if want_pos else WEBHOOK_PRICE
sl = want_pos["sl"] if want_pos else WEBHOOK_SL
tp = want_pos["tp"] if want_pos else WEBHOOK_TP
vol = want_pos["volume"] if want_pos else WEBHOOK_VOL
side = want_pos["side"] if want_pos else "LONG"
limit_px = hist_ord["price_open"] if hist_ord else None
otype = hist_ord["type"] if hist_ord else None

r_pts = abs(entry - sl) if (entry is not None and sl is not None and sl != 0) else None
r_usd = None
if r_pts is not None and info and vol:
    ts = float(info.trade_tick_size) or 0.01
    tv = float(info.trade_tick_value)
    if ts:
        r_usd = r_pts / ts * tv * float(vol)
tp_r = abs(tp - entry) / r_pts if (tp and entry and r_pts) else None

lift = None
rest = None
market_buy = False
if otype and "LIMIT" in str(otype) and entry is not None and limit_px is not None:
    if "BUY" in otype:
        # lift = buy limit above ask (through-market); rest = tagged at/near limit
        lift = bool(float(limit_px) > float(entry) + 0.5)  # won't know prior ask; use fill vs limit
        # better heuristic: fill near limit = rest; fill much worse (higher) = possible lift through
        rest = abs(float(entry) - float(limit_px)) <= 1.0
        lift = (not rest) and (float(entry) > float(limit_px) + 0.5)
    elif "SELL" in otype:
        rest = abs(float(entry) - float(limit_px)) <= 1.0
        lift = (not rest) and (float(entry) < float(limit_px) - 0.5)
elif otype and otype == "BUY":
    lift = False
    rest = False
    market_buy = True
    out["order_kind_note"] = "market_buy"
elif otype and otype == "SELL":
    lift = False
    rest = False
    out["order_kind_note"] = "market_sell"

float_pnl = want_pos["pnl"] if want_pos else None
float_r = (float_pnl / r_usd) if (float_pnl is not None and r_usd) else None
mark = float(tick.bid) if tick and side == "LONG" else (float(tick.ask) if tick else None)
adv_pts = (mark - entry) if (mark is not None and entry is not None and side == "LONG") else ((entry - mark) if (mark is not None and entry is not None) else None)
adv_r = (adv_pts / r_pts) if (adv_pts is not None and r_pts) else None

out["geometry"] = {
    "entry": entry, "sl": sl, "tp": tp, "volume": vol, "side": side,
    "limit_price": limit_px, "order_type": otype,
    "r_orig_pts": round(r_pts, 4) if r_pts is not None else None,
    "r_orig_usd": round(r_usd, 2) if r_usd is not None else None,
    "tp_r": round(tp_r, 2) if tp_r is not None else None,
    "float_pnl": float_pnl,
    "float_r": round(float_r, 3) if float_r is not None else None,
    "mark": mark,
    "adv_pts": round(adv_pts, 4) if adv_pts is not None else None,
    "adv_r": round(adv_r, 3) if adv_r is not None else None,
    "lift": lift,
    "rest": rest,
    "market_buy": market_buy,
    "live_sl_eq_orig": bool(sl is not None and abs(float(sl) - WEBHOOK_SL) < 0.05),
    "webhook_sl": WEBHOOK_SL,
    "webhook_tp": WEBHOOK_TP,
    "webhook_price": WEBHOOK_PRICE,
}

in_deal = None
for d in want_deals:
    if d.get("entry") == 0:
        in_deal = d
        break
out["in_deal"] = in_deal

out["ok"] = True
print(json.dumps(out, default=str))
try:
    mt5.shutdown()
except Exception:
    pass
