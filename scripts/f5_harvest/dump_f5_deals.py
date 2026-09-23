#!/usr/bin/env python3
"""Broker-deals authority dump for the F5 book (magic 0). READ-ONLY.

Runs on the VPS under the prod venv:

    python scripts\\f5_harvest\\dump_f5_deals.py --out C:\\path\\to\\outdir

It imports MetaTrader5, initializes the FTMO terminal
(``C:\\MT5\\FTMO\\terminal64.exe``, portable), and dumps:

  deals_f5_<YYYYMMDD>.json    every deal with magic == 0 in the last
                              --days days (default 14): per-deal ticket, order,
                              position_id, entry side, raw broker epoch time,
                              price, volume, profit, commission, swap, fee,
                              symbol, comment — plus the matching history
                              ORDERS (sl/tp/price requested) so the Mac-side
                              ledger builder can recover entry price and the
                              initial stop distance for tickets whose
                              trade-record JSON never reached the Mac.
  bars_f5/<SYM>_M15.csv       (unless --no-bars) M15 OHLC for every symbol that
                              appears in the dumped deals, covering the same
                              window, with a ``.timebase.json`` sidecar
                              declaring time_column_basis == "broker_wall".

TIMEBASE DOCTRINE (CLAUDE.md section 4): MT5 ``time`` fields are BROKER WALL
CLOCK epoch, not UTC (FTMO-Server3 == America/New_York + 7 h). This script
never converts; it records the raw epoch plus a naive broker-wall ISO string
and declares the basis, so the consumer (build_f5_outcome_ledger.py
``broker_naive_to_utc``) owns the one conversion.

Read-only by construction: MetaTrader5 calls are initialize / account_info /
history_deals_get / history_orders_get / copy_rates_range / shutdown. No
order_send, no modify, no close. Never prints tokens or credentials.

Exit codes: 0 ok, 2 MetaTrader5 unavailable/initialize failed, 3 no deals
window readable (history_deals_get returned None).
"""
import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone

SCHEMA = "gtos.f5.broker_deals_dump.v1"
F5_MAGIC = 0
DEFAULT_TERMINAL = r"C:\MT5\FTMO\terminal64.exe"

DEAL_FIELDS = ("ticket", "order", "position_id", "entry", "time", "time_msc",
               "type", "volume", "price", "profit", "commission", "swap",
               "fee", "magic", "reason", "symbol", "comment")
ORDER_FIELDS = ("ticket", "position_id", "time_setup", "time_done", "type",
                "state", "magic", "volume_initial", "price_open", "sl", "tp",
                "price_current", "symbol", "comment", "reason")

TIMEBASE = {
    "time_column_basis": "broker_wall",
    "broker_clock_rule": "new_york_plus_7",
    "note": ("MT5 epoch fields are broker wall clock (FTMO-Server3 == "
             "America/New_York + 7h, measured; src/utils/broker_clock.py). "
             "Convert with build_f5_outcome_ledger.broker_naive_to_utc; "
             "never trust a *_utc reading of the raw epoch."),
}


def _row(obj, fields):
    if hasattr(obj, "_asdict"):
        raw = dict(obj._asdict())
    elif isinstance(obj, dict):
        raw = dict(obj)
    else:
        raw = {n: getattr(obj, n, None) for n in fields}
    out = {k: raw.get(k) for k in fields}
    t = out.get("time") or out.get("time_setup")
    if isinstance(t, (int, float)) and t > 0:
        # naive broker-wall ISO — the epoch read as a wall-clock datetime.
        out["time_broker_iso"] = datetime.fromtimestamp(
            float(t), tz=timezone.utc).replace(tzinfo=None).isoformat(sep=" ")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--days", type=int, default=14,
                    help="lookback window in days (default 14)")
    ap.add_argument("--magic", type=int, default=F5_MAGIC,
                    help="magic number filter (default %d)" % F5_MAGIC)
    ap.add_argument("--out", default=".",
                    help="output directory (default: cwd)")
    ap.add_argument("--terminal", default=DEFAULT_TERMINAL,
                    help="MT5 terminal64.exe path (default %s)" % DEFAULT_TERMINAL)
    ap.add_argument("--no-bars", action="store_true",
                    help="skip the M15 bars dump")
    ap.add_argument("--date", default=None,
                    help="stamp for the output filename (default: UTC today)")
    args = ap.parse_args(argv)

    try:
        import MetaTrader5 as mt5
    except ImportError as exc:
        print("FATAL MetaTrader5 unavailable: %r" % exc, file=sys.stderr)
        return 2

    if not mt5.initialize(path=args.terminal, portable=True):
        # try default attach before giving up (already-running terminal)
        if not mt5.initialize():
            print("FATAL mt5.initialize failed: %r" % (mt5.last_error(),),
                  file=sys.stderr)
            return 2
    try:
        acct = mt5.account_info()
        acct_block = None
        if acct is not None:
            acct_block = {"login": getattr(acct, "login", None),
                          "balance": getattr(acct, "balance", None),
                          "equity": getattr(acct, "equity", None),
                          "currency": getattr(acct, "currency", None)}

        # history_deals_get takes datetimes interpreted against the BROKER
        # clock; pad the window a day each side so no boundary deal is lost.
        now = datetime.now(timezone.utc)
        d_from = now - timedelta(days=args.days + 1)
        d_to = now + timedelta(days=1)
        deals_raw = mt5.history_deals_get(d_from, d_to)
        if deals_raw is None:
            print("FATAL history_deals_get returned None: %r"
                  % (mt5.last_error(),), file=sys.stderr)
            return 3
        deals = [_row(d, DEAL_FIELDS) for d in deals_raw
                 if getattr(d, "magic", None) == args.magic]

        orders_raw = mt5.history_orders_get(d_from, d_to) or []
        orders = [_row(o, ORDER_FIELDS) for o in orders_raw
                  if getattr(o, "magic", None) == args.magic]

        stamp = args.date or now.strftime("%Y%m%d")
        os.makedirs(args.out, exist_ok=True)
        out_path = os.path.join(args.out, "deals_f5_%s.json" % stamp)
        doc = {
            "schema": SCHEMA,
            "generated_at_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "magic": args.magic,
            "window_days": args.days,
            "timebase": TIMEBASE,
            "account": acct_block,
            "n_deals": len(deals),
            "n_orders": len(orders),
            "deals": deals,
            "orders": orders,
        }
        tmp = out_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, indent=1, default=str)
        os.replace(tmp, out_path)
        print("OK %s deals=%d orders=%d" % (out_path, len(deals), len(orders)))

        if not args.no_bars:
            bars_dir = os.path.join(args.out, "bars_f5")
            os.makedirs(bars_dir, exist_ok=True)
            symbols = sorted({d.get("symbol") for d in deals if d.get("symbol")})
            # copy_rates_range takes broker-basis datetimes too; same padding.
            n_ok = 0
            for sym in symbols:
                try:
                    rates = mt5.copy_rates_range(sym, mt5.TIMEFRAME_M15,
                                                 d_from, d_to)
                except Exception as exc:
                    print("WARN bars %s failed: %r" % (sym, exc),
                          file=sys.stderr)
                    continue
                if rates is None or len(rates) == 0:
                    print("WARN bars %s empty: %r" % (sym, mt5.last_error()),
                          file=sys.stderr)
                    continue
                path = os.path.join(bars_dir, "%s_M15.csv" % sym)
                tmp = path + ".tmp"
                with open(tmp, "w", encoding="utf-8", newline="") as fh:
                    fh.write("time,open,high,low,close,tick_volume\n")
                    for r in rates:
                        wall = datetime.fromtimestamp(
                            float(r["time"]), tz=timezone.utc
                        ).replace(tzinfo=None)
                        fh.write("%s,%s,%s,%s,%s,%s\n" % (
                            wall.strftime("%Y-%m-%d %H:%M:%S"),
                            r["open"], r["high"], r["low"], r["close"],
                            int(r["tick_volume"])))
                os.replace(tmp, path)
                with open(path + ".timebase.json", "w", encoding="utf-8") as fh:
                    json.dump(TIMEBASE, fh, indent=1)
                n_ok += 1
            print("OK bars_f5: %d/%d symbols" % (n_ok, len(symbols)))
        return 0
    finally:
        try:
            mt5.shutdown()
        except Exception:
            pass


if __name__ == "__main__":
    sys.exit(main())
