#!/usr/bin/env python3
"""READ-ONLY EURGBP M15 export from Challenge MT5. No order_send."""
from __future__ import annotations
import csv
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

import MetaTrader5 as mt5

TERM = r"C:\MT5\FTMO\terminal64.exe"
OUT = Path(r"host-local\redacted_host\repo\research\warroom_20260920\EURGBP_M15_from_mt5.csv")
META = Path(r"host-local\redacted_host\repo\research\warroom_20260920\EURGBP_M15_from_mt5_meta.json")
OUT.parent.mkdir(parents=True, exist_ok=True)

def resolve_symbol():
    # Prefer exact EURGBP; then EURGBP.; then any containing EURGBP
    candidates = []
    for s in mt5.symbols_get() or []:
        name = s.name
        if name == "EURGBP":
            return name
        if "EURGBP" in name.upper():
            candidates.append(name)
    for pref in ("EURGBP.", "EURGBP.r", "EURGBPm", "EURGBP.a"):
        if pref in candidates:
            return pref
    return candidates[0] if candidates else None

def main():
    meta = {"ok": False, "terminal": TERM}
    if not mt5.initialize(path=TERM):
        meta["error"] = f"init_fail {mt5.last_error()}"
        META.write_text(json.dumps(meta, indent=2), encoding="utf-8")
        print(json.dumps(meta))
        return 3
    try:
        ai = mt5.account_info()
        meta["login"] = getattr(ai, "login", None)
        meta["server"] = getattr(ai, "server", None)
        meta["company"] = getattr(ai, "company", None)
        if not ai or int(ai.login) != 0:
            meta["error"] = "LOGIN_MISMATCH expected 0"
            META.write_text(json.dumps(meta, indent=2), encoding="utf-8")
            print(json.dumps(meta))
            return 4

        sym = resolve_symbol()
        meta["resolved_symbol"] = sym
        if not sym:
            meta["error"] = "no EURGBP symbol"
            # dump a few FX symbols for debug
            fx = [s.name for s in (mt5.symbols_get() or []) if "EUR" in s.name.upper()][:40]
            meta["eur_symbols_sample"] = fx
            META.write_text(json.dumps(meta, indent=2), encoding="utf-8")
            print(json.dumps(meta))
            return 5

        if not mt5.symbol_select(sym, True):
            meta["error"] = f"symbol_select_fail {mt5.last_error()}"
            META.write_text(json.dumps(meta, indent=2), encoding="utf-8")
            print(json.dumps(meta))
            return 6

        info = mt5.symbol_info(sym)
        meta["symbol_info"] = {
            "name": getattr(info, "name", None),
            "visible": getattr(info, "visible", None),
            "trade_mode": getattr(info, "trade_mode", None),
        }

        # Deep pull: try copy_rates_from_pos with large count, then copy_rates_range from 2014
        # MT5 clamps to available history.
        attempts = []
        rates = None
        # Attempt A: from_pos large
        for count in (500000, 200000, 100000, 50000):
            r = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_M15, 0, count)
            n = 0 if r is None else len(r)
            attempts.append({"method": "from_pos", "count_req": count, "n": n, "err": str(mt5.last_error())})
            if r is not None and len(r) > 0:
                rates = r
                break

        # Attempt B: range from 2014 / 2020 if from_pos thin
        if rates is None or len(rates) < 20000:
            for y in (2014, 2018, 2020, 2022):
                start = datetime(y, 1, 1, tzinfo=timezone.utc)
                end = datetime.now(timezone.utc) + timedelta(days=1)
                r = mt5.copy_rates_range(sym, mt5.TIMEFRAME_M15, start, end)
                n = 0 if r is None else len(r)
                attempts.append({"method": "range", "start": str(start.date()), "n": n, "err": str(mt5.last_error())})
                if r is not None and (rates is None or len(r) > len(rates)):
                    rates = r

        meta["attempts"] = attempts
        if rates is None or len(rates) == 0:
            meta["error"] = "empty_rates"
            META.write_text(json.dumps(meta, indent=2), encoding="utf-8")
            print(json.dumps(meta))
            return 7

        # Write CSV: time,open,high,low,close,volume (+ spread if avail)
        # time: broker epoch as UTC-labeled naive string (same style as GBPJPY historical)
        rows = []
        for r in rates:
            t = datetime.utcfromtimestamp(int(r["time"]))
            row = {
                "time": t.strftime("%Y-%m-%d %H:%M:%S"),
                "open": float(r["open"]),
                "high": float(r["high"]),
                "low": float(r["low"]),
                "close": float(r["close"]),
                "volume": int(r["tick_volume"]),
                "spread": int(r["spread"]) if "spread" in r.dtype.names else "",
            }
            rows.append(row)

        with OUT.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["time", "open", "high", "low", "close", "volume", "spread"])
            w.writeheader()
            w.writerows(rows)

        meta["ok"] = True
        meta["out"] = str(OUT)
        meta["n_bars"] = len(rows)
        meta["first"] = rows[0]["time"]
        meta["last"] = rows[-1]["time"]
        # span years approx
        t0 = datetime.strptime(rows[0]["time"], "%Y-%m-%d %H:%M:%S")
        t1 = datetime.strptime(rows[-1]["time"], "%Y-%m-%d %H:%M:%S")
        meta["span_days"] = (t1 - t0).days
        meta["span_years_approx"] = round((t1 - t0).days / 365.25, 2)
        meta["note"] = "READ-ONLY copy_rates; time field is MT5 bar epoch as utcfromtimestamp (broker-local labeled; same class as prior historical CSVs)"
        META.write_text(json.dumps(meta, indent=2), encoding="utf-8")
        print(json.dumps({k: meta[k] for k in ("ok","login","resolved_symbol","n_bars","first","last","span_days","span_years_approx","out")}, indent=2))
        return 0
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    raise SystemExit(main())
