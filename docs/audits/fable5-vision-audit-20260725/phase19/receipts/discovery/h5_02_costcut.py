#!/usr/bin/env python3
"""h5 step 2 — the affordability frontier.

The pooled gross edge is +0.038342 R/trade.  Therefore the BREAK-EVEN broker-true cost
is 0.038342 R: any cell whose cost sits below it pays, IF the edge inside it is at least
the book edge.  This step measures that directly instead of inferring it:

  * a sweep of the cost cutoff over the whole book, with n kept, gross, cost, net, t,
    day-clustered t, days positive, and month-by-month reads;
  * the same sweep on FEBRUARY and MARCH alone (January is the developed month);
  * per-symbol affordability: what share of each symbol sits below break-even and what
    it earns there;
  * the gross-vs-cost decomposition of every ratio>1 cell — is the ratio bought with
    MORE EDGE or with LESS COST?

out: h5_COSTCUT_V1.json
"""
import gzip
import json
import math
import os
import sys

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import h5_lib  # noqa: E402

rows = [json.loads(x) for x in gzip.open(os.path.join(D, "h5_SUBSTRATE_V1.jsonl.gz"), "rt") if x.strip()]
BOOK = h5_lib.cell_stats(rows)
OUT = {"book": BOOK, "break_even_cost_R": BOOK["gross_R"]}

CUTS = [0.005, 0.0075, 0.01, 0.0125, 0.015, 0.02, 0.025, 0.03, 0.0383, 0.04, 0.05,
        0.06, 0.08, 0.10, 0.12, 0.15, 0.20, 0.30, 0.50, 1e9]


def sweep(rs, label):
    o = []
    for c in CUTS:
        sub = [r for r in rs if r["cost_true"] <= c]
        if len(sub) < 20:
            continue
        st = h5_lib.cell_stats(sub)
        st["cut"] = c
        st["share_of_book"] = round(len(sub) / len(rs), 4)
        st["trades_per_day"] = round(len(sub) / st["days"], 2)
        o.append(st)
    OUT.setdefault("cost_cut_sweep", {})[label] = o
    return o


sweep(rows, "ALL_3M")
for m in ("2026-01", "2026-02", "2026-03"):
    sweep([r for r in rows if r["month"] == m], m)
sweep([r for r in rows if r["month"] != "2026-01"], "FEB_MAR_holdout")

# --- per-symbol affordability -------------------------------------------------
BE = BOOK["gross_R"]
per = []
for sym in sorted({r["symbol"] for r in rows}):
    rs = [r for r in rows if r["symbol"] == sym]
    st = h5_lib.cell_stats(rs)
    cheap = [r for r in rs if r["cost_true"] <= BE]
    stc = h5_lib.cell_stats(cheap) if len(cheap) >= 20 else None
    per.append({"symbol": sym, "n": len(rs),
                "gross_R": st["gross_R"], "cost_R": st["cost_R"], "net_R": st["net_R"],
                "ratio_R": st["ratio_R"], "ratio_bps": st["ratio_bps"],
                "median_cost_R": round(sorted(r["cost_true"] for r in rs)[len(rs) // 2], 6),
                "share_below_breakeven": round(len(cheap) / len(rs), 4),
                "cheap": ({"n": stc["n"], "gross_R": stc["gross_R"], "cost_R": stc["cost_R"],
                           "net_R": stc["net_R"], "ratio_R": stc["ratio_R"],
                           "t_net_day": stc["t_net_day"],
                           "m_jan": stc["m_2026-01"], "m_feb": stc["m_2026-02"],
                           "m_mar": stc["m_2026-03"]} if stc else None)})
per.sort(key=lambda r: -(r["ratio_R"] or 0))
OUT["per_symbol"] = per

# --- is the edge flat in cost? ------------------------------------------------
dec = {}
for r in rows:
    dec.setdefault(r["cost_dec"], []).append(r)
OUT["by_cost_decile"] = []
for k in sorted(dec):
    st = h5_lib.cell_stats(dec[k])
    OUT["by_cost_decile"].append({"cost_dec": k, "n": st["n"], "gross_R": st["gross_R"],
                                  "cost_R": st["cost_R"], "net_R": st["net_R"],
                                  "ratio_R": st["ratio_R"], "ratio_bps": st["ratio_bps"],
                                  "t_net_day": st["t_net_day"],
                                  "m_jan": st["m_2026-01"], "m_feb": st["m_2026-02"],
                                  "m_mar": st["m_2026-03"]})

g = [r[h5_lib.GROSS] for r in rows]
c = [r[h5_lib.COST] for r in rows]


def spearman(x, y):
    def rk(v):
        o = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(o):
            j = i
            while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1
            for k in range(i, j + 1):
                r[o[k]] = avg
            i = j + 1
        return r
    a, b = rk(x), rk(y)
    n = len(a)
    ma, mb = sum(a) / n, sum(b) / n
    num = sum((p - ma) * (q - mb) for p, q in zip(a, b))
    den = math.sqrt(sum((p - ma) ** 2 for p in a) * sum((q - mb) ** 2 for q in b))
    return num / den if den else None


OUT["spearman_gross_cost_trade_level"] = round(spearman(g, c), 4)
OUT["breakeven_share_of_book"] = round(sum(1 for x in c if x <= BE) / len(c), 4)

# --- decomposition of every ratio>1 cell --------------------------------------
cells = json.load(open(os.path.join(D, "h5_CELLS_V1.json")))
dcmp = []
for cl in cells:
    if cl["n"] < 50 or not cl["ratio_R"] or cl["ratio_R"] <= 1.0:
        continue
    dcmp.append({"grouping": cl["grouping"], "cell": cl["cell"], "n": cl["n"],
                 "ratio_R": cl["ratio_R"],
                 "gross_vs_book": round(cl["gross_R"] / BOOK["gross_R"], 3),
                 "cost_vs_book": round(cl["cost_R"] / BOOK["cost_R"], 3)})
OUT["ratio_gt1_decomposition"] = dcmp
gv = [d["gross_vs_book"] for d in dcmp]
cv = [d["cost_vs_book"] for d in dcmp]
OUT["ratio_gt1_decomposition_summary"] = {
    "n_cells": len(dcmp),
    "median_gross_vs_book": round(sorted(gv)[len(gv) // 2], 3),
    "median_cost_vs_book": round(sorted(cv)[len(cv) // 2], 3),
    "cells_where_cost_below_book": sum(1 for d in dcmp if d["cost_vs_book"] < 1),
    "cells_where_gross_above_book": sum(1 for d in dcmp if d["gross_vs_book"] > 1),
    "cells_where_BOTH": sum(1 for d in dcmp if d["cost_vs_book"] < 1 and d["gross_vs_book"] > 1),
    "cells_where_ONLY_cost": sum(1 for d in dcmp if d["cost_vs_book"] < 1 and d["gross_vs_book"] <= 1),
    "cells_where_ONLY_gross": sum(1 for d in dcmp if d["cost_vs_book"] >= 1 and d["gross_vs_book"] > 1),
}

json.dump(OUT, open(os.path.join(D, "h5_COSTCUT_V1.json"), "w"), indent=1)

print("BREAK-EVEN cost = pooled gross = %.6f R;  share of book below it = %.4f"
      % (BE, OUT["breakeven_share_of_book"]))
print("spearman(gross,cost) trade-level = %s" % OUT["spearman_gross_cost_trade_level"])
print("\n--- cost cutoff sweep, ALL 3 MONTHS ---")
print("%8s %7s %6s %9s %9s %10s %7s %7s %7s %6s" %
      ("cut", "n", "share", "gross", "cost", "net", "ratio", "t_net", "t_day", "d+/d"))
for s in OUT["cost_cut_sweep"]["ALL_3M"]:
    print("%8.4f %7d %6.3f %9.5f %9.5f %+10.5f %7.3f %7.2f %7.2f %3d/%d" %
          (s["cut"], s["n"], s["share_of_book"], s["gross_R"], s["cost_R"], s["net_R"],
           s["ratio_R"], s["t_net"] or 0, s["t_net_day"] or 0, s["days_net_pos"], s["days"]))
print("\n--- same, FEB+MAR holdout only ---")
for s in OUT["cost_cut_sweep"]["FEB_MAR_holdout"]:
    print("%8.4f %7d %6.3f %9.5f %9.5f %+10.5f %7.3f %7.2f %7.2f %3d/%d" %
          (s["cut"], s["n"], s["share_of_book"], s["gross_R"], s["cost_R"], s["net_R"],
           s["ratio_R"], s["t_net"] or 0, s["t_net_day"] or 0, s["days_net_pos"], s["days"]))
print("\n--- by cost decile ---")
print("%4s %7s %9s %9s %10s %7s %8s   jan/feb/mar ratio" % ("dec", "n", "gross", "cost", "net", "ratio", "t_day"))
for s in OUT["by_cost_decile"]:
    print("%4s %7d %9.5f %9.5f %+10.5f %7.3f %8.2f   %s / %s / %s" %
          (s["cost_dec"], s["n"], s["gross_R"], s["cost_R"], s["net_R"], s["ratio_R"],
           s["t_net_day"] or 0, s["m_jan"]["ratio_R"], s["m_feb"]["ratio_R"], s["m_mar"]["ratio_R"]))
print("\ndecomposition:", json.dumps(OUT["ratio_gt1_decomposition_summary"]))
