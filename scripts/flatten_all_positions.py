"""Owner-ordered FLATTEN: close EVERY open position on BOTH live accounts (FTMO + redacted_account) and write
an audit record so the closes are durable + reconstructable. Robust: re-fetches each position, tries the
broker's supported filling modes (IOC/FOK/RETURN), and retries until the ticket is gone or tries exhaust.

This is an operator/owner brake action (explicit approval 2026-06-16). The running W7 books reconcile open
positions from broker truth every tick, so once a ticket is gone at the broker the book's in-memory
active_trade clears on its next manage tick -- the close "stays in the books". Set the per-namespace kill
flags BEFORE running this (placement frozen) so nothing re-opens during/after the flatten.

    python scripts/flatten_all_positions.py            # close all on both accounts
    python scripts/flatten_all_positions.py --dry-run  # show what WOULD be closed, send nothing
"""
import argparse
import datetime as dt
import json
import os
import time

import MetaTrader5 as mt5

ACCOUNTS = [
    ("FTMO", r"C:\MT5\FTMO\terminal64.exe"),
    ("redacted_account", r"C:\MT5\redacted_account\terminal64.exe"),
]
_DONE = (mt5.TRADE_RETCODE_DONE, getattr(mt5, "TRADE_RETCODE_DONE_PARTIAL", 10010))
_INVALID_FILL = getattr(mt5, "TRADE_RETCODE_INVALID_FILL", 10030)


def _close_one(pos, max_tries=6):
    """Close a single position fully. Returns (status, last_result, realized_comment)."""
    last = None
    for _ in range(max_tries):
        cur = mt5.positions_get(ticket=pos.ticket) or []
        if not cur:
            return ("CLOSED", last)
        p = cur[0]
        tick = mt5.symbol_info_tick(p.symbol)
        if tick is None:
            time.sleep(0.5)
            continue
        is_sell = (p.type == 1)
        price = tick.ask if is_sell else tick.bid          # close SELL=BUY@ask ; close BUY=SELL@bid
        otype = mt5.ORDER_TYPE_BUY if is_sell else mt5.ORDER_TYPE_SELL
        sent = None
        for filling in (mt5.ORDER_FILLING_IOC, mt5.ORDER_FILLING_FOK, mt5.ORDER_FILLING_RETURN):
            req = {"action": mt5.TRADE_ACTION_DEAL, "symbol": p.symbol, "volume": float(p.volume),
                   "type": otype, "position": int(p.ticket), "price": float(price), "deviation": 100,
                   "magic": int(p.magic), "comment": "owner_flatten", "type_filling": filling}
            sent = mt5.order_send(req)
            last = sent
            if sent is not None and sent.retcode in _DONE:
                break
            if sent is None or sent.retcode != _INVALID_FILL:
                break                                       # a real error (not a filling mismatch) -> retry loop
        if sent is not None and sent.retcode in _DONE:
            time.sleep(0.3)                                 # settle, then loop to verify / close any remainder
            continue
        time.sleep(0.5)
    cur = mt5.positions_get(ticket=pos.ticket) or []
    return ("CLOSED" if not cur else "FAILED", last)


def flatten_account(label, term, dry_run=False):
    out = {"account": label, "terminal": term, "positions": [], "closed": 0, "failed": 0}
    if not mt5.initialize(path=term, portable=True):
        out["error"] = f"init failed: {mt5.last_error()}"
        return out
    try:
        info = mt5.account_info()
        out["login"] = getattr(info, "login", None)
        out["equity_before"] = float(getattr(info, "equity", 0.0))
        positions = mt5.positions_get() or []
        for p in positions:
            rec = {"ticket": int(p.ticket), "symbol": p.symbol, "type": "SELL" if p.type == 1 else "BUY",
                   "volume": float(p.volume), "profit": float(p.profit), "comment": p.comment,
                   "magic": int(p.magic)}
            if dry_run:
                rec["status"] = "WOULD_CLOSE"
            else:
                status, res = _close_one(p)
                rec["status"] = status
                rec["retcode"] = getattr(res, "retcode", None)
                rec["close_price"] = getattr(res, "price", None)
                out["closed" if status == "CLOSED" else "failed"] += 1
            out["positions"].append(rec)
        info2 = mt5.account_info()
        out["equity_after"] = float(getattr(info2, "equity", 0.0))
        out["remaining_positions"] = len(mt5.positions_get() or [])
    finally:
        mt5.shutdown()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    now = dt.datetime.now(dt.timezone.utc)
    report = {"ts": now.isoformat(), "dry_run": args.dry_run, "accounts": []}
    for label, term in ACCOUNTS:
        r = flatten_account(label, term, dry_run=args.dry_run)
        report["accounts"].append(r)
        print(f"\n=== {label} (login={r.get('login')}) ===")
        if r.get("error"):
            print("  ERROR:", r["error"]); continue
        for rec in r["positions"]:
            print(f"  #{rec['ticket']} {rec['symbol']:11s} {rec['type']} {rec['volume']} "
                  f"P&L=${rec['profit']:+.0f} cmt='{rec['comment']}' -> {rec['status']} "
                  f"(retcode={rec.get('retcode')})")
        print(f"  closed={r.get('closed',0)} failed={r.get('failed',0)} "
              f"remaining={r.get('remaining_positions','?')} "
              f"equity {r.get('equity_before','?')}->{r.get('equity_after','?')}")
    # durable audit record
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logdir = os.path.join(repo, "shadow_logs")
    os.makedirs(logdir, exist_ok=True)
    stamp = now.strftime("%Y%m%d_%H%M%S")
    path = os.path.join(logdir, f"owner_flatten_{stamp}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\naudit record -> {path}")
    total_failed = sum(a.get("failed", 0) for a in report["accounts"])
    return 1 if total_failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
