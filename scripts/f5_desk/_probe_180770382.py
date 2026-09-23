import json, subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path

WANT = 180770382
SYM = "US30.cash"
LOGIN = 0
MT5_PATH = r"C:\MT5\FTMO\terminal64.exe"
UNIT_USD = 150.0
PASS = 105000.0

HB = Path(r"host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\heartbeat.json")
STATUS = Path(r"host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\status.json")
LATEST = Path(r"host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\latest.json")
LATEST_SLATE = Path(r"host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\latest_slate.json")
ORIG_LIVE = Path(r"host-local\redacted_host\repo\judgment\live\chair_orig_sl.json")
ORIG_STATE = Path(r"host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\judgment\state\chair_orig_sl.json")
RECENT_ALLOWS = Path(r"host-local\redacted_host\repo\pipeline_state\ultimate_book\operator\recent_allows.json")
INBOX = Path(r"host-local\redacted_host\repo\judgment\live\verdict_inbox.jsonl")

now = datetime.now(timezone.utc)
ict = timezone(timedelta(hours=7))
out = {
    "ok": False,
    "probe_utc": now.isoformat(),
    "probe_ict": now.astimezone(ict).strftime("%Y-%m-%d %H:%M:%S ICT"),
    "want_ticket": WANT,
    "symbol": SYM,
    "comment_want": "dsp_isolated_spike_high",
}

TYPE_MAP = {0: "BUY", 1: "SELL", 2: "BUY_LIMIT", 3: "SELL_LIMIT", 4: "BUY_STOP", 5: "SELL_STOP"}
REASON_MAP = {
    0: "CLIENT", 1: "MOBILE", 2: "WEB", 3: "EXPERT",
    4: "SL", 5: "TP", 6: "SO", 7: "ROLLOVER", 8: "VMARGIN",
    9: "SPLIT", 10: "CORPORATE",
}

# --- writer task + pair ---
try:
    t = subprocess.check_output(
        ["schtasks", "/Query", "/TN", "GTOS_F5_FTMO", "/FO", "LIST", "/V"],
        text=True, errors="replace", timeout=20,
    )
    keys = {}
    for line in t.splitlines():
        s = line.strip()
        for k in ("Status:", "Last Run Time:", "Last Result:", "Next Run Time:"):
            if s.startswith(k):
                keys[k[:-1]] = s[len(k):].strip()
    out["task"] = keys
    out["writer"] = "GTOS_F5_FTMO %s" % keys.get("Status", "?")
except Exception as e:
    out["task"] = {"err": str(e)}
    out["writer"] = "unknown"

writers = []
try:
    ps = subprocess.check_output(
        ["powershell", "-NoProfile", "-Command",
         "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and ($_.CommandLine -match 'operator') } | "
         "ForEach-Object { [PSCustomObject]@{ pid=$_.ProcessId; parent=$_.ParentProcessId; name=$_.Name; "
         "has_size_150=[bool]($_.CommandLine -match 'f5-minimal-size-usd\\s+150'); "
         "has_size_250=[bool]($_.CommandLine -match 'f5-minimal-size-usd\\s+250'); "
         "has_frozen=[bool]($_.CommandLine -match 'frozen-intent-reprice'); "
         "cmd_tail=$_.CommandLine.Substring([Math]::Max(0,$_.CommandLine.Length-280)) } } | ConvertTo-Json -Compress -Depth 4"],
        text=True, errors="replace", timeout=30,
    )
    if ps.strip():
        parsed = json.loads(ps)
        writers = parsed if isinstance(parsed, list) else [parsed]
except Exception as e:
    out["writers_err"] = str(e)
out["writers"] = writers

def _read_json(path):
    if not path.exists():
        return None, False
    try:
        return json.loads(path.read_text(encoding="utf-8")), True
    except Exception as e:
        return {"error": str(e)}, True

hb, hb_ok = _read_json(HB)
out["hb"] = None
out["hb_exists"] = hb_ok
if hb_ok and isinstance(hb, dict) and "error" not in hb:
    out["hb"] = {k: hb.get(k) for k in ("ts", "ts_utc", "as_of_utc", "pid", "healthy", "namespace", "status", "login", "profile") if k in hb}
    out["hb_mtime"] = datetime.fromtimestamp(HB.stat().st_mtime, tz=timezone.utc).isoformat()
    out["pair_pid"] = hb.get("pid")
    out["healthy"] = bool(hb.get("healthy", True))
else:
    out["pair_pid"] = None
    out["healthy"] = None
    if hb_ok:
        out["hb"] = hb

st, st_ok = _read_json(STATUS)
out["status"] = st if st_ok else None
latest, latest_ok = _read_json(LATEST)
out["latest"] = latest if latest_ok else None
slate, slate_ok = _read_json(LATEST_SLATE)
out["latest_slate"] = slate if slate_ok else None
ra, ra_ok = _read_json(RECENT_ALLOWS)
out["recent_allows_exists"] = ra_ok
# filter recent allows for this ticket / sleeve
fuel_hits = []
def _scan_obj(obj, path="$"):
    if isinstance(obj, dict):
        blob = json.dumps(obj, default=str)
        if ("180770382" in blob) or ("dsp_isolated_spike_high" in blob and "US30" in blob):
            fuel_hits.append({"path": path, "obj": obj})
        for k, v in obj.items():
            _scan_obj(v, path + "." + str(k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj[:200]):
            _scan_obj(v, "%s[%d]" % (path, i))

if latest_ok:
    _scan_obj(latest, "latest")
if slate_ok:
    _scan_obj(slate, "latest_slate")
if ra_ok:
    _scan_obj(ra, "recent_allows")
    # also keep short list of recent allow ids
    if isinstance(ra, list):
        out["recent_allows_tail"] = ra[-8:]
    elif isinstance(ra, dict):
        items = ra.get("allows") or ra.get("items") or ra.get("recent") or []
        if isinstance(items, list):
            out["recent_allows_tail"] = items[-8:]

# inbox lines
inbox_hits = []
if INBOX.exists():
    try:
        lines = INBOX.read_text(encoding="utf-8", errors="replace").splitlines()
        for ln in lines[-200:]:
            if "180770382" in ln or ("dsp_isolated_spike_high" in ln and "US30" in ln):
                try:
                    inbox_hits.append(json.loads(ln))
                except Exception:
                    inbox_hits.append({"raw": ln[:500]})
    except Exception as e:
        out["inbox_err"] = str(e)
out["fillpath_fuel_hits"] = fuel_hits[:12]
out["inbox_hits"] = inbox_hits[-12:]

def _orig_from(path):
    if not path.exists():
        return None, False, None
    od = json.loads(path.read_text(encoding="utf-8"))
    tickets = od.get("tickets") or od
    val = None
    us30_map = {}
    if isinstance(tickets, dict):
        val = tickets.get(str(WANT))
        if val is None:
            val = tickets.get(WANT)
        # collect any US30-ish notes if structure has symbol
        for k, v in tickets.items():
            if isinstance(v, dict) and ("US30" in str(v.get("symbol", "")) or "us30" in str(v).lower()):
                us30_map[str(k)] = v
            elif k == str(WANT) or k == WANT:
                us30_map[str(k)] = v
    return val, True, {"n_tickets": len(tickets) if isinstance(tickets, dict) else None, "want": val, "us30_related": us30_map, "raw_mtime": datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()}

orig_live, orig_live_exists, orig_live_meta = _orig_from(ORIG_LIVE)
orig_state, orig_state_exists, orig_state_meta = _orig_from(ORIG_STATE)
out["chair_orig_sl"] = orig_live if orig_live is not None else orig_state
out["chair_orig_sl_live_exists"] = orig_live_exists
out["chair_orig_sl_state_exists"] = orig_state_exists
out["chair_orig_sl_live_meta"] = orig_live_meta
out["chair_orig_sl_state_meta"] = orig_state_meta

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
info = mt5.symbol_info(SYM)

open_rows = []
want_pos = None
for p in pos:
    tck = mt5.symbol_info_tick(p.symbol)
    side = "LONG" if int(p.type) == 0 else "SHORT"
    mark = None
    if tck:
        mark = float(tck.bid) if side == "LONG" else float(tck.ask)
    row = {
        "ticket": int(p.ticket), "symbol": p.symbol, "side": side,
        "type": TYPE_MAP.get(int(p.type), str(int(p.type))),
        "lots": float(p.volume), "volume": float(p.volume),
        "entry": float(p.price_open), "sl": float(p.sl), "tp": float(p.tp),
        "pnl": float(p.profit), "swap": float(getattr(p, "swap", 0) or 0),
        "comment": p.comment, "magic": int(getattr(p, "magic", 0) or 0),
        "time": int(getattr(p, "time", 0) or 0),
        "time_utc": datetime.fromtimestamp(int(p.time), tz=timezone.utc).isoformat() if getattr(p, "time", 0) else None,
        "mark": mark,
        "price_current": float(getattr(p, "price_current", 0) or 0),
    }
    open_rows.append(row)
    if int(p.ticket) == WANT:
        want_pos = row

pending = []
want_ord = None
for o in ords:
    row = {
        "ticket": int(o.ticket), "symbol": o.symbol,
        "type": TYPE_MAP.get(int(o.type), str(int(o.type))),
        "type_i": int(o.type),
        "lots": float(o.volume_current), "volume": float(o.volume_current),
        "limit": float(o.price_open), "price": float(o.price_open),
        "sl": float(o.sl), "tp": float(o.tp), "comment": o.comment,
        "magic": int(getattr(o, "magic", 0) or 0),
        "time_setup": int(getattr(o, "time_setup", 0) or 0),
        "time_setup_utc": datetime.fromtimestamp(int(o.time_setup), tz=timezone.utc).isoformat() if getattr(o, "time_setup", 0) else None,
    }
    pending.append(row)
    if int(o.ticket) == WANT:
        want_ord = row

bal = float(ai.balance) if ai else None
eq = float(ai.equity) if ai else None
out["login"] = int(ai.login) if ai else None
out["login_ok"] = bool(out["login"] == LOGIN)
out["server"] = ai.server if ai else None
out["balance"] = bal
out["equity"] = eq
out["floating"] = round(eq - bal, 2) if (eq is not None and bal is not None) else None
out["to_pass"] = round(PASS - bal, 2) if bal is not None else None
out["open"] = open_rows
out["pending"] = pending
out["n_open"] = len(open_rows)
out["n_pending"] = len(pending)
out["want_in_positions"] = want_pos is not None
out["want_in_orders"] = want_ord is not None
out["want_pos"] = want_pos
out["want_ord"] = want_ord
if want_pos is not None:
    out["want_status"] = "OPEN_POSITION"
elif want_ord is not None:
    out["want_status"] = "PENDING_ORDER"
else:
    out["want_status"] = "NEITHER"

bid = float(tick.bid) if tick else None
ask = float(tick.ask) if tick else None
spread = round(ask - bid, 4) if (bid is not None and ask is not None) else None
out["us30_bid"] = bid
out["us30_ask"] = ask
out["us30_spread"] = spread
out["us30_tick_size"] = float(info.trade_tick_size) if info else None
out["us30_tick_value"] = float(info.trade_tick_value) if info else None
out["us30_point"] = float(info.point) if info else None
out["us30_contract"] = float(info.trade_contract_size) if info else None

# geometry for want
geom = None
src = want_pos or want_ord
if src:
    entry = src.get("entry") if want_pos else src.get("limit")
    sl = src.get("sl")
    tp = src.get("tp")
    lots = src.get("lots")
    side = src.get("side") if want_pos else None
    typ = src.get("type")
    if side is None:
        if typ in ("BUY", "BUY_LIMIT", "BUY_STOP"):
            side = "LONG"
        elif typ in ("SELL", "SELL_LIMIT", "SELL_STOP"):
            side = "SHORT"
    r_pts = abs(entry - sl) if (entry is not None and sl is not None and sl != 0) else None
    tick_size = out["us30_tick_size"] or 0.01
    tick_value = out["us30_tick_value"] or 0.01
    r_usd = None
    if r_pts is not None and lots is not None and tick_size and tick_size > 0:
        r_usd = r_pts / tick_size * tick_value * lots
    # lift vs rest vs market
    lift = None
    if want_ord and bid is not None and ask is not None and entry is not None:
        if typ in ("BUY_LIMIT",):
            if entry > ask:
                lift = "lift"  # buy limit above ask = lift
            elif entry < bid:
                lift = "rest"
            else:
                lift = "at_market_band"
        elif typ in ("SELL_LIMIT",):
            if entry < bid:
                lift = "lift"  # sell limit below bid = lift
            elif entry > ask:
                lift = "rest"
            else:
                lift = "at_market_band"
        elif typ in ("BUY_STOP", "SELL_STOP"):
            lift = "stop_order"
        else:
            lift = "other"
    elif want_pos:
        lift = "filled_position"
    # stop vs spread
    slip = None
    # try pull slip from fuel hits
    for h in fuel_hits:
        o = h.get("obj") or {}
        if isinstance(o, dict):
            for key in ("slip", "slippage", "slip_pts"):
                if key in o and o[key] is not None:
                    try:
                        slip = float(o[key]); break
                    except Exception:
                        pass
            if slip is not None:
                break
            fuel = o.get("fuel") or o.get("geometry") or {}
            if isinstance(fuel, dict) and fuel.get("slip") is not None:
                try:
                    slip = float(fuel["slip"]); break
                except Exception:
                    pass
    if slip is None:
        slip = 0.0
    spr_plus_slip = (spread + slip) if spread is not None else None
    fail_stop = bool(r_pts is not None and spr_plus_slip is not None and r_pts <= spr_plus_slip)
    geom = {
        "side": side, "type": typ, "lots": lots,
        "entry_or_limit": entry, "sl": sl, "tp": tp,
        "comment": src.get("comment"), "magic": src.get("magic"),
        "R_orig_pts": r_pts,
        "R_orig_usd_approx": round(r_usd, 2) if r_usd is not None else None,
        "unit_usd_assumed": UNIT_USD,
        "lift_vs_rest": lift,
        "sl_dist": r_pts,
        "spread": spread,
        "slip": slip,
        "spr_plus_slip": spr_plus_slip,
        "fail_stop": fail_stop,
    }
out["geometry"] = geom
out["stop_vs_spread"] = None if not geom else {
    "sl_dist": geom["sl_dist"], "spread": geom["spread"], "slip": geom["slip"],
    "spr_plus_slip": geom["spr_plus_slip"], "fail_stop": geom["fail_stop"],
}

# history for want + US30 closes today
day0 = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
# broker server may be UTC+2/3; pull last 36h to be safe
frm = now - timedelta(hours=36)
deals = mt5.history_deals_get(frm.replace(tzinfo=None), now.replace(tzinfo=None) + timedelta(hours=1)) or []
want_deals = []
us30_closes_today = []
for d in deals:
    raw_t = int(d.time)
    t_utc = datetime.fromtimestamp(raw_t, tz=timezone.utc)
    row = {
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
        "time_as_utc": t_utc.isoformat(),
        "time_as_ict": t_utc.astimezone(ict).strftime("%Y-%m-%d %H:%M:%S ICT"),
    }
    if row["position_id"] == WANT or row["order"] == WANT or row["deal"] == WANT:
        want_deals.append(row)
    # US30 close today (entry==1 OUT) in ICT day 2026-09-02
    if "US30" in (row["symbol"] or "") and row["entry"] == 1:
        if t_utc.astimezone(ict).date().isoformat() == "2026-09-02":
            us30_closes_today.append(row)

out["want_deals"] = want_deals
out["us30_closes_today_ict"] = us30_closes_today

orders_h = mt5.history_orders_get(frm.replace(tzinfo=None), now.replace(tzinfo=None) + timedelta(hours=1)) or []
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
            "volume_current": float(getattr(o, "volume_current", 0) or 0),
            "price_open": float(o.price_open),
            "price_current": float(getattr(o, "price_current", 0) or 0),
            "sl": float(o.sl), "tp": float(o.tp), "comment": o.comment,
            "time_setup": int(getattr(o, "time_setup", 0) or 0),
            "time_done": int(getattr(o, "time_done", 0) or 0),
            "time_setup_utc": datetime.fromtimestamp(int(o.time_setup), tz=timezone.utc).isoformat() if getattr(o, "time_setup", 0) else None,
            "time_done_utc": datetime.fromtimestamp(int(o.time_done), tz=timezone.utc).isoformat() if getattr(o, "time_done", 0) else None,
        }
        break
out["want_hist_order"] = hist_ord

# if neither live nor hist — pre-send ghost
if out["want_status"] == "NEITHER" and not want_deals and hist_ord is None:
    out["want_status"] = "NEITHER_PRE_SEND_GHOST_OR_NOT_ON_BROKER"

out["ok"] = True
mt5.shutdown()
print(json.dumps(out, default=str))
