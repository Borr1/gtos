import json
from datetime import datetime, timezone, timedelta
import MetaTrader5 as mt5
import subprocess

TERM = r"C:\MT5\FTMO\terminal64.exe"
WANT = 177634847
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
    btc = []
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
        if "BTCUSD" in (row["symbol"] or ""):
            btc.append(row)
    btc.sort(key=lambda r: r["time_raw"])
    last_real = None
    for r in reversed(btc):
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
            "word": "not_this_plate",
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
            "comment": o.comment,
        })
    tick = mt5.symbol_info_tick("BTCUSD")
    tick_xau = mt5.symbol_info_tick("XAUUSD")
    tick_us = mt5.symbol_info_tick("US30.cash")
    writer = "unknown"
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-ScheduledTask -TaskName GTOS_F5_FTMO | Select-Object -ExpandProperty State"],
            capture_output=True, text=True, timeout=20)
        writer = (r.stdout or "").strip() or (r.stderr or "").strip() or "empty"
    except Exception as e:
        writer = f"err:{e}"
    out = {
        "probe_utc": now_utc.isoformat(),
        "login": int(acc.login) if acc else None,
        "server": acc.server if acc else None,
        "balance": float(acc.balance) if acc else None,
        "equity": float(acc.equity) if acc else None,
        "floating": float(acc.profit) if acc else None,
        "to_pass": (105000.0 - float(acc.balance)) if acc else None,
        "n_deals_90d": len(deals),
        "want_hits": want_hits,
        "open": open_rows,
        "pending": pending_rows,
        "writer": writer,
        "btc_bid": float(tick.bid) if tick else None,
        "btc_ask": float(tick.ask) if tick else None,
        "xau_bid": float(tick_xau.bid) if tick_xau else None,
        "xau_ask": float(tick_xau.ask) if tick_xau else None,
        "us30_bid": float(tick_us.bid) if tick_us else None,
        "us30_ask": float(tick_us.ask) if tick_us else None,
        "last_real_btc": last_real,
        "btc_n": len(btc),
    }
    print(json.dumps(out))
finally:
    mt5.shutdown()
