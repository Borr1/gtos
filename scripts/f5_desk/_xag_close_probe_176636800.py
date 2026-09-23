import json
from datetime import datetime, timezone, timedelta
import MetaTrader5 as mt5
import subprocess

TERM = r"C:\MT5\FTMO\terminal64.exe"
WANT = 176636800
if not mt5.initialize(path=TERM):
    print(json.dumps({"error": "INIT_FAIL", "detail": str(mt5.last_error())}))
    raise SystemExit(3)
try:
    acc = mt5.account_info()
    pos = mt5.positions_get() or []
    ords = mt5.orders_get() or []
    now_utc = datetime.now(timezone.utc)
    frm = datetime.utcnow() - timedelta(days=90)
    to = datetime.utcnow() + timedelta(hours=6)
    deals = mt5.history_deals_get(frm, to) or []
    want_hits = []
    xag = []
    live_xag_close = []
    for d in deals:
        row = {
            "ticket": int(d.ticket),
            "order": int(getattr(d, "order", 0) or 0),
            "position_id": int(getattr(d, "position_id", 0) or 0),
            "symbol": d.symbol,
            "type": int(d.type),
            "entry": int(getattr(d, "entry", 0) or 0),
            "volume": float(d.volume),
            "price": float(d.price),
            "profit": float(d.profit),
            "swap": float(getattr(d, "swap", 0) or 0),
            "commission": float(getattr(d, "commission", 0) or 0),
            "comment": d.comment,
            "time_raw": int(d.time),
            "time_as_utc": datetime.fromtimestamp(int(d.time), tz=timezone.utc).isoformat(),
            "magic": int(getattr(d, "magic", 0) or 0),
        }
        if row["ticket"] == WANT or row["order"] == WANT or row["position_id"] == WANT:
            want_hits.append(row)
        if "XAG" in (row["symbol"] or ""):
            xag.append(row)
        if row["position_id"] == 180109102 or row["order"] == 180109102:
            live_xag_close.append(row)
    xag.sort(key=lambda r: r["time_raw"])
    last_real = None
    for r in reversed(xag):
        if r["entry"] == 1:
            last_real = r
            break
    open_rows = []
    for p in pos:
        open_rows.append({
            "ticket": int(p.ticket),
            "symbol": p.symbol,
            "side": "LONG" if int(p.type) == 0 else "SHORT",
            "volume": float(p.volume),
            "entry": float(p.price_open),
            "sl": float(p.sl),
            "tp": float(p.tp),
            "pnl": float(p.profit),
            "comment": p.comment,
            "magic": int(getattr(p, "magic", 0) or 0),
        })
    TYPE_MAP = {0: "BUY", 1: "SELL", 2: "BUY_LIMIT", 3: "SELL_LIMIT", 4: "BUY_STOP", 5: "SELL_STOP"}
    pending_rows = []
    for o in ords:
        pending_rows.append({
            "ticket": int(o.ticket),
            "symbol": o.symbol,
            "type": TYPE_MAP.get(int(o.type), str(int(o.type))),
            "volume": float(o.volume_current),
            "price": float(o.price_open),
            "sl": float(o.sl),
            "tp": float(o.tp),
        })
    tick = mt5.symbol_info_tick("XAGUSD")
    tick_xau = mt5.symbol_info_tick("XAUUSD")
    tick_us30 = mt5.symbol_info_tick("US30.cash")
    writer = "unknown"
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-ScheduledTask -TaskName GTOS_F5_FTMO | Select-Object -ExpandProperty State"],
            capture_output=True, text=True, timeout=20)
        writer = (r.stdout or "").strip() or (r.stderr or "").strip() or "empty"
    except Exception as e:
        writer = f"err:{e}"
    bal = float(acc.balance) if acc else None
    eq = float(acc.equity) if acc else None
    out = {
        "written_at_utc": now_utc.isoformat(),
        "login": int(acc.login) if acc else None,
        "server": getattr(acc, "server", None) if acc else None,
        "balance": bal,
        "equity": eq,
        "floating": (eq - bal) if (eq is not None and bal is not None) else None,
        "to_pass": (105000.0 - bal) if bal is not None else None,
        "n_open": len(pos),
        "n_pending": len(ords),
        "open": open_rows,
        "pending": pending_rows,
        "n_deals_90d": len(deals),
        "want_ticket": WANT,
        "want_hits": want_hits,
        "xag_n": len(xag),
        "last_real_xag": last_real,
        "live_xag_180109102": live_xag_close,
        "tick_xag": {"bid": float(tick.bid), "ask": float(tick.ask)} if tick else None,
        "tick_xau": {"bid": float(tick_xau.bid), "ask": float(tick_xau.ask)} if tick_xau else None,
        "tick_us30": {"bid": float(tick_us30.bid), "ask": float(tick_us30.ask)} if tick_us30 else None,
        "writer": writer,
    }
    print(json.dumps(out, indent=2))
finally:
    mt5.shutdown()
