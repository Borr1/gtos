#!/usr/bin/env python3
"""Try deeper EURGBP M15 history beyond 50k from_pos cap."""
from __future__ import annotations
import csv
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
import MetaTrader5 as mt5

TERM = r"C:\MT5\FTMO\terminal64.exe"
OUT = Path(r"host-local\redacted_host\repo\research\warroom_20260920\EURGBP_M15_from_mt5.csv")
META = Path(r"host-local\redacted_host\repo\research\warroom_20260920\EURGBP_M15_from_mt5_meta.json")

def main():
    assert mt5.initialize(path=TERM), mt5.last_error()
    try:
        ai = mt5.account_info()
        assert int(ai.login) == 0
        sym = "EURGBP"
        assert mt5.symbol_select(sym, True)
        ti = mt5.terminal_info()
        print("terminal", ti.name if ti else None, "maxbars", getattr(ti, "maxbars", None))
        si = mt5.symbol_info(sym)
        print("symbol", si.name, "digits", si.digits)

        chunks = []
        notes = []
        # Walk backward in ~2y windows using copy_rates_range
        end = datetime.now(timezone.utc) + timedelta(days=1)
        for start_y in [2014, 2016, 2018, 2020, 2022, 2024]:
            start = datetime(start_y, 1, 1, tzinfo=timezone.utc)
            r = mt5.copy_rates_range(sym, mt5.TIMEFRAME_M15, start, end)
            n = 0 if r is None else len(r)
            first = last = None
            if r is not None and n:
                first = datetime.utcfromtimestamp(int(r[0]["time"])).isoformat()
                last = datetime.utcfromtimestamp(int(r[-1]["time"])).isoformat()
            notes.append({"start_y": start_y, "n": n, "first": first, "last": last, "err": str(mt5.last_error())})
            print(f"range from {start_y}: n={n} first={first} last={last}")

        # Also try copy_rates_from anchored at early dates
        for y in (2014, 2018, 2020, 2022):
            dt = datetime(y, 1, 1, tzinfo=timezone.utc)
            r = mt5.copy_rates_from(sym, mt5.TIMEFRAME_M15, dt, 100000)
            n = 0 if r is None else len(r)
            first = last = None
            if r is not None and n:
                first = datetime.utcfromtimestamp(int(r[0]["time"])).isoformat()
                last = datetime.utcfromtimestamp(int(r[-1]["time"])).isoformat()
            notes.append({"method": "from", "anchor": str(dt.date()), "n": n, "first": first, "last": last})
            print(f"from {y}: n={n} first={first} last={last}")

        # Best available: take the max n result from range starting 2014, or from_pos 100k
        best = None
        best_n = 0
        for start_y in [2014, 2018, 2020, 2022]:
            start = datetime(start_y, 1, 1, tzinfo=timezone.utc)
            r = mt5.copy_rates_range(sym, mt5.TIMEFRAME_M15, start, end)
            if r is not None and len(r) > best_n:
                best, best_n = r, len(r)

        # Also from_pos
        r2 = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_M15, 0, 200000)
        if r2 is not None and len(r2) > best_n:
            best, best_n = r2, len(r2)

        # Chunked backward merge: pull successive from_pos windows by shifting start
        # If terminal only keeps ~50k, we cannot get more without chart history load.
        # Try requesting history via copy_rates_range year by year and merge unique times.
        by_t = {}
        for y in range(2014, 2027):
            start = datetime(y, 1, 1, tzinfo=timezone.utc)
            end_y = datetime(y + 1, 1, 1, tzinfo=timezone.utc)
            r = mt5.copy_rates_range(sym, mt5.TIMEFRAME_M15, start, end_y)
            n = 0 if r is None else len(r)
            print(f"year chunk {y}: n={n}")
            if r is None:
                continue
            for row in r:
                by_t[int(row["time"])] = row

        print("merged unique bars", len(by_t))
        if len(by_t) > best_n:
            times_sorted = sorted(by_t.keys())
            best = [by_t[t] for t in times_sorted]
            best_n = len(best)
            print("using year-merge", best_n)

        rows = []
        for r in best:
            t = datetime.utcfromtimestamp(int(r["time"]))
            rows.append({
                "time": t.strftime("%Y-%m-%d %H:%M:%S"),
                "open": float(r["open"]),
                "high": float(r["high"]),
                "low": float(r["low"]),
                "close": float(r["close"]),
                "volume": int(r["tick_volume"]),
                "spread": int(r["spread"]) if "spread" in r.dtype.names else "",
            })
        with OUT.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["time","open","high","low","close","volume","spread"])
            w.writeheader()
            w.writerows(rows)
        t0 = datetime.strptime(rows[0]["time"], "%Y-%m-%d %H:%M:%S")
        t1 = datetime.strptime(rows[-1]["time"], "%Y-%m-%d %H:%M:%S")
        meta = {
            "ok": True,
            "login": int(ai.login),
            "resolved_symbol": sym,
            "n_bars": len(rows),
            "first": rows[0]["time"],
            "last": rows[-1]["time"],
            "span_days": (t1 - t0).days,
            "span_years_approx": round((t1 - t0).days / 365.25, 2),
            "out": str(OUT),
            "notes": notes,
            "maxbars_terminal": getattr(ti, "maxbars", None) if ti else None,
            "method": "deepest_available_year_merge_or_range",
        }
        META.write_text(json.dumps(meta, indent=2), encoding="utf-8")
        print(json.dumps({k: meta[k] for k in ("ok","n_bars","first","last","span_days","span_years_approx","maxbars_terminal")}, indent=2))
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    main()
