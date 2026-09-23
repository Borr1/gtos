import json
from datetime import datetime, timezone, timedelta
import MetaTrader5 as mt5

TERM = r"C:\MT5\FTMO\terminal64.exe"
WATCH = [
    179453737, 179489256, 179553082, 179566918,
    179453732, 179563723, 179495470, 179528677, 179380936,
]
if not mt5.initialize(path=TERM):
    print("INIT_FAIL", mt5.last_error())
    raise SystemExit(3)
try:
    acc = mt5.account_info()
    pos = mt5.positions_get() or []
    ords = mt5.orders_get() or []
    now = datetime.now(timezone.utc)
    start = now - timedelta(hours=18)
    deals = mt5.history_deals_get(start, now) or []
    deal_rows = []
    for d in deals:
        if int(getattr(d, "entry", 0) or 0) == 1 or int(d.ticket) in WATCH or int(getattr(d, "position_id", 0) or 0) in WATCH:
            deal_rows.append({
                "ticket": int(d.ticket),
                "order": int(getattr(d, "order", 0) or 0),
                "position_id": int(getattr(d, "position_id", 0) or 0),
                "symbol": d.symbol,
                "type": int(d.type),
                "entry": int(getattr(d, "entry", 0) or 0),
                "volume": float(d.volume),
                "price": float(d.price),
                "profit": float(d.profit),
                "comment": d.comment,
                "time": datetime.fromtimestamp(int(d.time), tz=timezone.utc).isoformat(),
            })
    out = {
        "written_at_utc": now.isoformat(),
        "login": int(acc.login) if acc else None,
        "balance": float(acc.balance) if acc else None,
        "equity": float(acc.equity) if acc else None,
        "n_open": len(pos),
        "n_pending": len(ords),
        "positions": [{
            "ticket": int(p.ticket), "symbol": p.symbol,
            "type": "BUY" if p.type == 0 else "SELL", "volume": float(p.volume),
            "price_open": float(p.price_open), "sl": float(p.sl or 0), "tp": float(p.tp or 0),
            "profit": float(p.profit), "swap": float(p.swap), "magic": int(p.magic),
            "comment": p.comment,
            "time": datetime.fromtimestamp(int(p.time), tz=timezone.utc).isoformat(),
        } for p in pos],
        "orders": [{
            "ticket": int(o.ticket), "symbol": o.symbol, "type": int(o.type),
            "volume_current": float(o.volume_current), "price_open": float(o.price_open),
            "sl": float(o.sl or 0), "tp": float(o.tp or 0), "magic": int(o.magic),
            "comment": o.comment,
        } for o in ords],
        "recent_exit_deals": deal_rows,
    }
    print(json.dumps(out, indent=2))
finally:
    mt5.shutdown()
