#!/usr/bin/env python3
"""h5 step 5 — robustness of the surviving cells, and ONE pre-specified mechanism test.

A. CONCENTRATION / TRIM.  A cell mean is worthless if one day made it.  For every cell
   that cleared ratio_R > 1 at n >= 50 and survived all seven sub-samples, plus the
   pre-declared rules, report: best-day share of total net R, net R with the best day
   dropped, with the best three days dropped, the 10% trimmed mean, and the median.

B. THE INDEX-OPEN MECHANISM TEST, declared before it is read.  h5's grid surfaced
   GER40 at hour 08 and hour 14.  08:00 UTC is the Xetra cash open (09:00 CET, winter)
   and 14:00 UTC is the hour before the US cash open (14:30 UTC).  If that is a mechanism
   rather than a grid artifact it must appear on the OTHER index instruments too, so the
   test is six pre-specified cells, not a search:
       own cash open hour, UTC, Jan-Mar 2026 (winter offsets)
         GER40 08 (Xetra 09:00 CET)   UK100 08 (LSE 08:00 GMT)
         US30_cash 14 / SPX500 14 / NAS100 14 (NYSE 09:30 ET = 14:30 UTC)
         JP225 00 (TSE 09:00 JST)
   and the same six at the US cash-open hour 14, since every index is US-correlated.

out: h5_ROBUST_V1.json
"""
import gzip
import json
import os
import sys

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import h5_lib  # noqa: E402

rows = [json.loads(x) for x in gzip.open(os.path.join(D, "h5_SUBSTRATE_V1.jsonl.gz"), "rt") if x.strip()]
OUT = {}


def robust(rs, label):
    net = [r[h5_lib.GROSS] - r[h5_lib.COST] for r in rs]
    n = len(net)
    byday = {}
    for r, x in zip(rs, net):
        byday.setdefault(r["day"], []).append(x)
    tot = sum(net)
    dsum = sorted(byday.items(), key=lambda kv: -sum(kv[1]))
    drop1 = [x for d, v in dsum[1:] for x in v]
    drop3 = [x for d, v in dsum[3:] for x in v]
    s = sorted(net)
    k = int(0.10 * n)
    trim = s[k:n - k] if n - 2 * k >= 5 else s
    st = h5_lib.cell_stats(rs)
    return {"label": label, "n": n, "net_R": st["net_R"], "ratio_R": st["ratio_R"],
            "t_net_day": st["t_net_day"], "days": len(byday),
            "total_net_R": round(tot, 4),
            "best_day_share": round(sum(dsum[0][1]) / tot, 4) if tot else None,
            "best3_day_share": round(sum(x for _d, v in dsum[:3] for x in v) / tot, 4) if tot else None,
            "net_R_drop_best_day": round(sum(drop1) / len(drop1), 6) if drop1 else None,
            "net_R_drop_best_3_days": round(sum(drop3) / len(drop3), 6) if drop3 else None,
            "net_R_trimmed10": round(sum(trim) / len(trim), 6),
            "net_R_median": round(s[n // 2], 6),
            "frac_trades_net_positive": round(sum(1 for x in net if x > 0) / n, 4),
            "days_net_pos": sum(1 for v in byday.values() if sum(v) > 0)}


SURV12 = [("hour", "cost_dec", "14", "0"), ("family", "cost_dec", "regime_transition_break", "0"),
          ("symbol", "hour", "GER40", "8"), ("symbol", "hour", "GER40", "14"),
          ("rdp_dec", "cost_dec", "4", "1"), ("symbol", "hour", "NAS100", "16"),
          ("symbol", "family", "GER40", "structural_distance_extreme"),
          ("symbol", "rv_q", "GER40", "2"), ("symbol", "rdp_dec", "UK100", "4"),
          ("symbol", "cost_dec", "UK100", "3"), ("hour", "rdp_dec", "20", "9"),
          ("symbol", "hour", "UK100", "15")]

# rv_q is a derived quantile column; rebuild it here exactly as h5_01_cells did
import bisect  # noqa: E402
jan = [r for r in rows if r["month"] == "2026-01"]
v = sorted(x["rv_rel"] for x in jan if x["rv_rel"] is not None)
cuts = [v[int(round(p * (len(v) - 1)))] for p in (0.2, 0.4, 0.6, 0.8)]
for r in rows:
    r["rv_q"] = None if r["rv_rel"] is None else bisect.bisect_left(cuts, r["rv_rel"])

res = []
for a, b, va, vb in SURV12:
    rs = [r for r in rows if str(r.get(a)) == va and str(r.get(b)) == vb]
    res.append(robust(rs, f"{a}*{b}={va}|{vb}"))
INDEX = ["GER40", "US30_cash", "NAS100", "UK100", "SPX500", "JP225"]
res.append(robust([r for r in rows if r["symbol"] == "GER40"], "RULE R1 GER40 all"))
res.append(robust([r for r in rows if r["symbol"] == "GER40" and r["hour"] in (8, 14)], "RULE R9 GER40 h8,h14"))
res.append(robust([r for r in rows if r["cost_true"] <= 0.0075], "RULE R4 cost<=0.0075"))
res.append(robust([r for r in rows if r["family"] == "regime_transition_break" and r["cost_dec"] == 0],
                  "RULE R10 regime_break costdec0"))
res.append(robust(rows, "WHOLE BOOK"))
OUT["robustness"] = res

# ---------------------------------------------------- B. index-open mechanism
OPEN = {"GER40": 8, "UK100": 8, "US30_cash": 14, "SPX500": 14, "NAS100": 14, "JP225": 0}
mech = []
for sym, h in OPEN.items():
    a = [r for r in rows if r["symbol"] == sym and r["hour"] == h]
    b = [r for r in rows if r["symbol"] == sym and r["hour"] != h]
    sa = h5_lib.cell_stats(a) if len(a) >= 20 else None
    sb = h5_lib.cell_stats(b)
    mech.append({"symbol": sym, "own_open_hour_utc": h,
                 "open": (None if sa is None else
                          {"n": sa["n"], "gross_R": sa["gross_R"], "cost_R": sa["cost_R"],
                           "net_R": sa["net_R"], "ratio_R": sa["ratio_R"],
                           "t_net": sa["t_net"], "t_net_day": sa["t_net_day"],
                           "jan": sa["m_2026-01"]["ratio_R"], "feb": sa["m_2026-02"]["ratio_R"],
                           "mar": sa["m_2026-03"]["ratio_R"]}),
                 "rest": {"n": sb["n"], "net_R": sb["net_R"], "ratio_R": sb["ratio_R"]}})
OUT["index_own_open_hour"] = mech
allopen = [r for r in rows if r["symbol"] in OPEN and r["hour"] == OPEN[r["symbol"]]]
allrest = [r for r in rows if r["symbol"] in OPEN and r["hour"] != OPEN[r["symbol"]]]
OUT["index_own_open_pooled"] = {"open": h5_lib.cell_stats(allopen), "rest": h5_lib.cell_stats(allrest)}

us14 = []
for sym in INDEX:
    a = [r for r in rows if r["symbol"] == sym and r["hour"] == 14]
    if len(a) >= 20:
        s = h5_lib.cell_stats(a)
        us14.append({"symbol": sym, "n": s["n"], "gross_R": s["gross_R"], "cost_R": s["cost_R"],
                     "net_R": s["net_R"], "ratio_R": s["ratio_R"], "t_net_day": s["t_net_day"],
                     "jan": s["m_2026-01"]["ratio_R"], "feb": s["m_2026-02"]["ratio_R"],
                     "mar": s["m_2026-03"]["ratio_R"]})
OUT["index_at_us_open_hour_14"] = us14
OUT["index_at_us_open_pooled"] = h5_lib.cell_stats([r for r in rows if r["symbol"] in INDEX and r["hour"] == 14])

# every symbol, hour 14, as the widest read of the same mechanism
h14 = []
for sym in sorted({r["symbol"] for r in rows}):
    a = [r for r in rows if r["symbol"] == sym and r["hour"] == 14]
    if len(a) >= 20:
        s = h5_lib.cell_stats(a)
        h14.append({"symbol": sym, "n": s["n"], "net_R": s["net_R"], "ratio_R": s["ratio_R"]})
h14.sort(key=lambda r: -(r["ratio_R"] or 0))
OUT["all_symbols_hour_14"] = h14
OUT["all_symbols_hour_14_pooled"] = h5_lib.cell_stats([r for r in rows if r["hour"] == 14])

json.dump(OUT, open(os.path.join(D, "h5_ROBUST_V1.json"), "w"), indent=1)

print("%-42s %5s %9s %7s %9s %9s %9s %9s %6s %6s" %
      ("cell / rule", "n", "net", "ratio", "dropBest1", "dropBest3", "trim10", "median", "bestD%", "d+/d"))
for r in res:
    print("%-42s %5d %+9.5f %7.2f %+9.5f %+9.5f %+9.5f %+9.5f %6.3f %3d/%d" %
          (r["label"][:42], r["n"], r["net_R"], r["ratio_R"] or 0, r["net_R_drop_best_day"] or 0,
           r["net_R_drop_best_3_days"] or 0, r["net_R_trimmed10"], r["net_R_median"],
           r["best_day_share"] or 0, r["days_net_pos"], r["days"]))
print("\n--- index at its OWN cash-open hour (pre-specified) ---")
for m in mech:
    o = m["open"]
    print("  %-11s h%02d  n=%4d net=%+8.5f ratio=%6.2f tday=%+5.2f  jan/feb/mar %.2f/%.2f/%.2f   rest n=%4d net=%+8.5f ratio=%5.2f" %
          (m["symbol"], m["own_open_hour_utc"], o["n"], o["net_R"], o["ratio_R"] or 0,
           o["t_net_day"] or 0, o["jan"] or 0, o["feb"] or 0, o["mar"] or 0,
           m["rest"]["n"], m["rest"]["net_R"], m["rest"]["ratio_R"] or 0))
p = OUT["index_own_open_pooled"]
print("  POOLED open n=%d net=%+.5f ratio=%.3f t=%.2f tday=%.2f  |  rest n=%d net=%+.5f ratio=%.3f" %
      (p["open"]["n"], p["open"]["net_R"], p["open"]["ratio_R"], p["open"]["t_net"],
       p["open"]["t_net_day"], p["rest"]["n"], p["rest"]["net_R"], p["rest"]["ratio_R"]))
print("\n--- indices at the US open hour 14 ---")
for m in us14:
    print("  %-11s n=%4d net=%+8.5f ratio=%6.2f tday=%+5.2f  jan/feb/mar %.2f/%.2f/%.2f" %
          (m["symbol"], m["n"], m["net_R"], m["ratio_R"] or 0, m["t_net_day"] or 0,
           m["jan"] or 0, m["feb"] or 0, m["mar"] or 0))
q = OUT["index_at_us_open_pooled"]
print("  POOLED n=%d net=%+.5f ratio=%.3f t=%.2f tday=%.2f" % (q["n"], q["net_R"], q["ratio_R"], q["t_net"], q["t_net_day"]))
q = OUT["all_symbols_hour_14_pooled"]
print("  ALL 24 SYMBOLS hour 14: n=%d net=%+.5f ratio=%.3f tday=%.2f" % (q["n"], q["net_R"], q["ratio_R"], q["t_net_day"]))
