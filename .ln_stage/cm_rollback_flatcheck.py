"""Read-only precondition check for the CM rollback (2026-08-10).

Confirms BOTH accounts have zero open positions AND zero pending orders.
Read-only: initialize/positions_get/orders_get/shutdown only. No mutations.
"""
import datetime as dt
import json
import sys

import MetaTrader5 as mt5

ACCOUNTS = [
    ("FTMO", r"C:\MT5\FTMO\terminal64.exe", 531325516, "operator_profile"),
    ("redacted_account", r"C:\MT5\redacted_account\terminal64.exe", 0, "redacted_account_live_bee34003"),
]

out = {"checked_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "accounts": []}
ok = True

for label, path, want_login, ns in ACCOUNTS:
    rec = {"label": label, "namespace": ns, "expected_login": want_login}
    if not mt5.initialize(path=path, portable=True):
        rec["error"] = f"CONNECT FAIL {mt5.last_error()}"
        out["accounts"].append(rec)
        ok = False
        continue
    try:
        info = mt5.account_info()
        pos = mt5.positions_get() or []
        orders = mt5.orders_get() or []
        rec["login"] = int(info.login) if info else None
        rec["login_matches"] = (int(info.login) == want_login) if info else False
        rec["equity"] = round(float(info.equity), 2) if info else None
        rec["balance"] = round(float(info.balance), 2) if info else None
        rec["n_positions"] = len(pos)
        rec["n_pending_orders"] = len(orders)
        rec["positions"] = [
            {"symbol": p.symbol, "volume": p.volume, "type": int(p.type),
             "profit": float(p.profit), "comment": p.comment, "magic": int(p.magic)}
            for p in pos
        ]
        rec["pending_orders"] = [
            {"symbol": o.symbol, "volume": float(o.volume_current), "type": int(o.type),
             "comment": o.comment, "magic": int(o.magic)}
            for o in orders
        ]
        rec["flat"] = (len(pos) == 0 and len(orders) == 0)
        if not rec["flat"] or not rec["login_matches"]:
            ok = False
    finally:
        mt5.shutdown()
    out["accounts"].append(rec)

out["all_flat_and_identified"] = ok
print(json.dumps(out, indent=2))
sys.exit(0 if ok else 1)
