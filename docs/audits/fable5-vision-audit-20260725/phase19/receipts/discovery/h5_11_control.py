#!/usr/bin/env python3
"""h5 step 11 — THE CONTROL THAT DECIDES WHAT THE 6.2x SURVIVAL MEANS.

Step 10 measured that cells with hunt-window ratio > 1 stay above 1 in April+May at 28.2%
against a 4.5% base rate.  There are two completely different explanations and they have
opposite consequences:

  (a) EDGE persists.  The cells carry more gross edge and that edge repeats.  Actionable.
  (b) COST persists.  A cheap cell is cheap in every month, and since ratio = gross/cost a
      low denominator alone lifts the ratio.  The survival is then a re-measurement of the
      broker's fee schedule, not of any edge, and is worth nothing.

Three tests separate them:

  T1  Spearman(hunt cost_R, oos cost_R)  vs  Spearman(hunt gross_R, oos gross_R).
      If (b), the first is ~1 and the second ~0.
  T2  Within each decile of cell cost, does the hunt ratio still predict the OOS ratio?
      Cost is held fixed by construction, so any remaining prediction is edge.
  T3  The gross-only hunt: rank cells by hunt gross_R alone (cost-blind) and measure the
      OOS gross_R of the top decile against the bottom.  A cost-free statement about
      whether the EDGE half of the ratio replicates at all.

out: h5_CONTROL_V1.json
"""
import gzip
import json
import math
import os
import sys

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import h5_lib  # noqa: E402
import h5_01_cells as C  # noqa: E402

h5_lib.COST = "cost_true_hour"
rows = [json.loads(x) for x in gzip.open(os.path.join(D, "h5_SUBSTRATE_5M.jsonl.gz"), "rt") if x.strip()]
for r in rows:
    r["_jday"] = None

cells = []
for gname, g in C.groupings(rows):
    for label, rs in g.items():
        h = [r for r in rs if r["month"] <= "2026-03"]
        o = [r for r in rs if r["month"] > "2026-03"]
        if len(h) < 50 or len(o) < 30:
            continue
        sh, so = h5_lib.cell_stats(h), h5_lib.cell_stats(o)
        cells.append({"grouping": gname, "cell": label,
                      "hn": sh["n"], "hg": sh["gross_R"], "hc": sh["cost_R"],
                      "hr": sh["ratio_R"], "hnet": sh["net_R"],
                      "on": so["n"], "og": so["gross_R"], "oc": so["cost_R"],
                      "orr": so["ratio_R"], "onet": so["net_R"], "ot": so["t_net_day"]})


def spearman(x, y):
    def rk(v):
        idx = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(idx):
            j = i
            while j + 1 < len(idx) and v[idx[j + 1]] == v[idx[i]]:
                j += 1
            for k in range(i, j + 1):
                r[idx[k]] = (i + j) / 2.0 + 1
            i = j + 1
        return r
    a, b = rk(x), rk(y)
    n = len(a)
    ma, mb = sum(a) / n, sum(b) / n
    num = sum((p - ma) * (q - mb) for p, q in zip(a, b))
    den = math.sqrt(sum((p - ma) ** 2 for p in a) * sum((q - mb) ** 2 for q in b))
    return round(num / den, 4) if den else None


OUT = {"n_cells": len(cells)}
OUT["T1"] = {
    "spearman_cost_hunt_vs_oos": spearman([c["hc"] for c in cells], [c["oc"] for c in cells]),
    "spearman_gross_hunt_vs_oos": spearman([c["hg"] for c in cells], [c["og"] for c in cells]),
    "spearman_ratio_hunt_vs_oos": spearman([c["hr"] for c in cells], [c["orr"] for c in cells]),
    "spearman_net_hunt_vs_oos": spearman([c["hnet"] for c in cells], [c["onet"] for c in cells]),
}

# T2 — within cost decile
s = sorted(c["hc"] for c in cells)
cuts = [s[int(round(p * (len(s) - 1)))] for p in [i / 10 for i in range(1, 10)]]
import bisect  # noqa: E402
buckets = {}
for c in cells:
    buckets.setdefault(bisect.bisect_left(cuts, c["hc"]), []).append(c)
T2 = []
for k in sorted(buckets):
    v = buckets[k]
    if len(v) < 30:
        continue
    gt1 = [c for c in v if c["hr"] and c["hr"] > 1]
    le1 = [c for c in v if c["hr"] is not None and c["hr"] <= 1]
    T2.append({"cost_decile": k, "n_cells": len(v),
               "median_hunt_cost_R": round(sorted(x["hc"] for x in v)[len(v) // 2], 5),
               "spearman_ratio": spearman([c["hr"] for c in v], [c["orr"] for c in v]),
               "spearman_gross": spearman([c["hg"] for c in v], [c["og"] for c in v]),
               "n_hunt_gt1": len(gt1),
               "frac_oos_gt1_given_hunt_gt1": (round(sum(1 for c in gt1 if c["orr"] > 1) / len(gt1), 4) if gt1 else None),
               "frac_oos_gt1_given_hunt_le1": (round(sum(1 for c in le1 if c["orr"] > 1) / len(le1), 4) if le1 else None)})
OUT["T2_within_cost_decile"] = T2
allg = [c for c in cells if c["hr"] and c["hr"] > 1]
alll = [c for c in cells if c["hr"] is not None and c["hr"] <= 1]
OUT["T2_pooled_within_decile"] = {
    "n_hunt_gt1": len(allg), "n_hunt_le1": len(alll),
    "frac_oos_gt1_given_hunt_gt1": round(sum(1 for c in allg if c["orr"] > 1) / len(allg), 4),
    "frac_oos_gt1_given_hunt_le1": round(sum(1 for c in alll if c["orr"] > 1) / len(alll), 4)}

# T3 — the cost-blind gross hunt
byg = sorted(cells, key=lambda c: -c["hg"])
k = max(1, len(byg) // 10)


def agg(v, key):
    return round(sum(c[key] for c in v) / len(v), 6)


OUT["T3_gross_only"] = {
    "top_decile_by_hunt_gross": {"n_cells": k, "mean_hunt_gross": agg(byg[:k], "hg"),
                                 "mean_oos_gross": agg(byg[:k], "og"),
                                 "mean_hunt_cost": agg(byg[:k], "hc"),
                                 "mean_oos_cost": agg(byg[:k], "oc"),
                                 "mean_oos_net": agg(byg[:k], "onet")},
    "bottom_decile_by_hunt_gross": {"n_cells": k, "mean_hunt_gross": agg(byg[-k:], "hg"),
                                    "mean_oos_gross": agg(byg[-k:], "og"),
                                    "mean_hunt_cost": agg(byg[-k:], "hc"),
                                    "mean_oos_cost": agg(byg[-k:], "oc"),
                                    "mean_oos_net": agg(byg[-k:], "onet")},
    "all_cells": {"mean_hunt_gross": agg(cells, "hg"), "mean_oos_gross": agg(cells, "og")},
}

# T4 — the same question at TRADE level, no cells: does a symbol's own gross edge persist?
per = []
for sym in sorted({r["symbol"] for r in rows}):
    h = [r for r in rows if r["symbol"] == sym and r["month"] <= "2026-03"]
    o = [r for r in rows if r["symbol"] == sym and r["month"] > "2026-03"]
    a, b = h5_lib.cell_stats(h), h5_lib.cell_stats(o)
    per.append({"symbol": sym, "hunt_gross": a["gross_R"], "oos_gross": b["gross_R"],
                "hunt_cost": a["cost_R"], "oos_cost": b["cost_R"],
                "hunt_ratio": a["ratio_R"], "oos_ratio": b["ratio_R"]})
OUT["T4_per_symbol"] = per
OUT["T4_spearman"] = {
    "gross": spearman([p["hunt_gross"] for p in per], [p["oos_gross"] for p in per]),
    "cost": spearman([p["hunt_cost"] for p in per], [p["oos_cost"] for p in per]),
    "ratio": spearman([p["hunt_ratio"] for p in per], [p["oos_ratio"] for p in per])}

json.dump(OUT, open(os.path.join(D, "h5_CONTROL_V1.json"), "w"), indent=1)
print("cells:", OUT["n_cells"])
print("T1:", json.dumps(OUT["T1"], indent=1))
print("\nT2 within cost decile:")
print("%4s %8s %12s %10s %10s %8s %10s %10s" % ("dec", "n_cells", "med_cost_R", "sp_ratio", "sp_gross",
                                                "n_gt1", "oos>1|gt1", "oos>1|le1"))
for t in T2:
    print("%4d %8d %12.5f %10s %10s %8d %10s %10s" %
          (t["cost_decile"], t["n_cells"], t["median_hunt_cost_R"], t["spearman_ratio"],
           t["spearman_gross"], t["n_hunt_gt1"], t["frac_oos_gt1_given_hunt_gt1"],
           t["frac_oos_gt1_given_hunt_le1"]))
print("\nT3:", json.dumps(OUT["T3_gross_only"], indent=1))
print("\nT4 spearman across 24 symbols:", json.dumps(OUT["T4_spearman"]))
print("%-12s %10s %10s %10s %10s %8s %8s" % ("symbol", "h_gross", "o_gross", "h_cost", "o_cost", "h_ratio", "o_ratio"))
for p in sorted(per, key=lambda x: -x["hunt_gross"]):
    print("%-12s %10.5f %10.5f %10.5f %10.5f %8.3f %8.3f" %
          (p["symbol"], p["hunt_gross"], p["oos_gross"], p["hunt_cost"], p["oos_cost"],
           p["hunt_ratio"], p["oos_ratio"]))
