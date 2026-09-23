#!/usr/bin/env python3
"""x4 step 9 — MECHANISM ONLY, on tick data outside the January window (2026-06-18..07-24).

The whole x4 result rests on one observable measured at T+60 s. The live book already polls at
60 s (run_book.py:99). The operative question for the owner is: how much of that 60-second
signal exists EARLIER? Ticks are the only instrument that can answer it.

NEVER used to score a January candidate -- wrong window. Purely: how fast does the first-minute
displacement form, at every M15 boundary in the tick window.

`time`/`time_msc` are BROKER WALL CLOCK (new_york_plus_7, whole-hour offset), so M15 boundaries
coincide with UTC M15 boundaries and no conversion is needed for a WITHIN-minute study.
"""
import gzip, json, os, sys
import numpy as np
D = os.path.dirname(os.path.abspath(__file__))
TICKS = "/Users/borr/GTOSActive/vps-ticks-20260726/ftmo"
SYMS = ["EURUSD", "GER40_cash", "XAUUSD"]
LAGS = [1, 2, 3, 5, 10, 15, 20, 30, 45, 60]
out = {}
for sym in SYMS:
    p = os.path.join(TICKS, "FTMO_%s_ticks_20260618_to_20260726.csv.gz" % sym)
    marks = {}          # boundary -> {lag: mid}
    cur_b = None
    with gzip.open(p, "rt") as fh:
        fh.readline()
        for line in fh:
            c = line.split(",")
            t = int(c[0]); mid = (float(c[1]) + float(c[2])) / 2.0
            b = t - (t % 900)
            if t - b > 60:
                continue                      # only the first minute of each M15 bar
            d = marks.setdefault(b, {})
            if "t0" not in d:
                d["t0"] = mid
            off = t - b
            for L in LAGS:
                if off <= L:
                    d[L] = mid                # last tick at or before the lag
    rows = [v for v in marks.values() if "t0" in v and 60 in v and all(L in v for L in LAGS)]
    if len(rows) < 200:
        out[sym] = {"n_boundaries": len(rows), "note": "too few"}
        print(sym, "too few", len(rows), flush=True); continue
    d60 = np.array([v[60] - v["t0"] for v in rows])
    scale = np.median(np.abs(d60[d60 != 0])) or 1.0
    r = {"n_boundaries": len(rows), "median_abs_60s_move": float(scale)}
    nz = d60 != 0
    for L in LAGS[:-1]:
        dl = np.array([v[L] - v["t0"] for v in rows])
        m = nz & (dl != 0)
        r["lag_%ds" % L] = {
            "corr_with_60s": round(float(np.corrcoef(dl[nz], d60[nz])[0, 1]), 4),
            "sign_agreement": round(float((np.sign(dl[m]) == np.sign(d60[m])).mean()), 4),
            "median_abs_share_of_60s": round(float(np.median(np.abs(dl[m]) / np.abs(d60[m]))), 4),
            "share_already_moved": round(float((dl != 0).mean()), 4),
            "n_nonzero": int(m.sum())}
    out[sym] = r
    print("\n== %s  n=%d boundaries  median |60s move| = %.6g" % (sym, len(rows), scale))
    print("  %5s %10s %10s %12s %10s" % ("lag", "corr60", "signAgree", "medShare60", "moved"))
    for L in LAGS[:-1]:
        v = r["lag_%ds" % L]
        print("  %4ds %10.4f %10.4f %12.4f %10.4f" % (L, v["corr_with_60s"], v["sign_agreement"],
                                                      v["median_abs_share_of_60s"],
                                                      v["share_already_moved"]), flush=True)
with open(os.path.join(D, "X4_TICKS_V1.json"), "w") as f:
    json.dump(out, f, indent=1)
print("wrote X4_TICKS_V1.json")
