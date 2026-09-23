#!/usr/bin/env python3
"""h5 step 10 — carry EVERY cell that cleared the bar on Jan-Mar into April and May.

The single number this lane owes the owner: of the cells the hunt found, what fraction is
still affordable on two months the hunt never saw, and is that fraction better than the
base rate of a cell chosen at random?

For every one of the 4,130 cells at n>=50 on the hour-aware toll:
    HUNT   Jan+Feb+Mar ratio_R, net_R, t_net_day
    OOS    Apr+May ratio_R, net_R, t_net_day (cell definition frozen, nothing refitted)
and the survival table, with the base rate computed on the SAME grid so the comparison is
like-for-like.

out: h5_OOS_ALL_V1.json
"""
import gzip
import json
import os
import sys

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import h5_lib  # noqa: E402
import h5_01_cells as C  # noqa: E402

h5_lib.COST = "cost_true_hour"
rows = [json.loads(x) for x in gzip.open(os.path.join(D, "h5_SUBSTRATE_5M.jsonl.gz"), "rt") if x.strip()]
hunt = [r for r in rows if r["month"] <= "2026-03"]
oos = [r for r in rows if r["month"] > "2026-03"]
for r in rows:
    r["_jday"] = None

cells = []
for gname, g in C.groupings(rows):
    gh, go = {}, {}
    for label, rs in g.items():
        gh[label] = [r for r in rs if r["month"] <= "2026-03"]
        go[label] = [r for r in rs if r["month"] > "2026-03"]
    for label in g:
        h, o = gh[label], go[label]
        if len(h) < 50:
            continue
        sh = h5_lib.cell_stats(h)
        so = h5_lib.cell_stats(o) if len(o) >= 30 else None
        cells.append({"grouping": gname, "cell": label,
                      "hunt_n": sh["n"], "hunt_ratio": sh["ratio_R"], "hunt_net": sh["net_R"],
                      "hunt_t_day": sh["t_net_day"],
                      "oos_n": (so["n"] if so else None),
                      "oos_ratio": (so["ratio_R"] if so else None),
                      "oos_net": (so["net_R"] if so else None),
                      "oos_t_day": (so["t_net_day"] if so else None)})

with_oos = [c for c in cells if c["oos_ratio"] is not None]
gt1 = [c for c in with_oos if c["hunt_ratio"] and c["hunt_ratio"] > 1]
le1 = [c for c in with_oos if c["hunt_ratio"] is not None and c["hunt_ratio"] <= 1]
gt05 = [c for c in with_oos if c["hunt_ratio"] and 0.5 < c["hunt_ratio"] <= 1]


def frac(v, pred):
    return round(sum(1 for c in v if pred(c)) / len(v), 4) if v else None


OUT = {
    "n_cells_scored": len(cells),
    "n_cells_with_oos": len(with_oos),
    "hunt_ratio_gt_1": len(gt1),
    "hunt_ratio_between_05_and_1": len(gt05),
    "hunt_ratio_le_05": len(le1) - len(gt05),
    "survival": {
        "of_hunt_ratio_gt_1__oos_ratio_gt_1": frac(gt1, lambda c: c["oos_ratio"] > 1),
        "of_hunt_ratio_gt_1__oos_net_gt_0": frac(gt1, lambda c: c["oos_net"] > 0),
        "of_hunt_ratio_le_1__oos_ratio_gt_1": frac(le1, lambda c: c["oos_ratio"] > 1),
        "of_hunt_ratio_le_1__oos_net_gt_0": frac(le1, lambda c: c["oos_net"] > 0),
        "of_hunt_05_to_1__oos_ratio_gt_1": frac(gt05, lambda c: c["oos_ratio"] > 1),
        "ALL_cells__oos_ratio_gt_1": frac(with_oos, lambda c: c["oos_ratio"] > 1),
    },
    "median_oos_ratio_by_hunt_bucket": {},
}
for lo, hi, lab in ((-1e9, 0.5, "hunt<=0.5"), (0.5, 1.0, "0.5-1.0"), (1.0, 1.5, "1.0-1.5"),
                    (1.5, 2.5, "1.5-2.5"), (2.5, 1e9, ">2.5")):
    v = [c["oos_ratio"] for c in with_oos if c["hunt_ratio"] is not None and lo < c["hunt_ratio"] <= hi]
    if v:
        s = sorted(v)
        OUT["median_oos_ratio_by_hunt_bucket"][lab] = {
            "n_cells": len(v), "median_oos_ratio": round(s[len(s) // 2], 4),
            "frac_oos_gt_1": round(sum(1 for x in v if x > 1) / len(v), 4)}

# rank correlation between hunt ratio and oos ratio
import math  # noqa: E402


def spearman(x, y):
    def rk(v):
        o = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(o):
            j = i
            while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]:
                j += 1
            for k in range(i, j + 1):
                r[o[k]] = (i + j) / 2.0 + 1
            i = j + 1
        return r
    a, b = rk(x), rk(y)
    n = len(a)
    ma, mb = sum(a) / n, sum(b) / n
    num = sum((p - ma) * (q - mb) for p, q in zip(a, b))
    den = math.sqrt(sum((p - ma) ** 2 for p in a) * sum((q - mb) ** 2 for q in b))
    return round(num / den, 4) if den else None


hv = [c["hunt_ratio"] for c in with_oos if c["hunt_ratio"] is not None]
ov = [c["oos_ratio"] for c in with_oos if c["hunt_ratio"] is not None]
OUT["spearman_hunt_ratio_vs_oos_ratio"] = spearman(hv, ov)
hn = [c["hunt_net"] for c in with_oos]
on = [c["oos_net"] for c in with_oos]
OUT["spearman_hunt_net_vs_oos_net"] = spearman(hn, on)

gt1.sort(key=lambda c: -(c["oos_net"] or -9))
OUT["hunt_gt1_cells_best_oos"] = gt1[:40]
OUT["hunt_gt1_cells_worst_oos"] = gt1[-15:]
both = [c for c in gt1 if c["oos_ratio"] > 1 and c["oos_net"] > 0]
both.sort(key=lambda c: -(c["oos_t_day"] or -9))
OUT["n_cells_gt1_in_BOTH"] = len(both)
OUT["cells_gt1_in_BOTH"] = both[:60]
json.dump(OUT, open(os.path.join(D, "h5_OOS_ALL_V1.json"), "w"), indent=1)

print(json.dumps({k: OUT[k] for k in ("n_cells_scored", "n_cells_with_oos", "hunt_ratio_gt_1",
                                      "hunt_ratio_between_05_and_1", "hunt_ratio_le_05",
                                      "n_cells_gt1_in_BOTH", "spearman_hunt_ratio_vs_oos_ratio",
                                      "spearman_hunt_net_vs_oos_net")}, indent=1))
print(json.dumps(OUT["survival"], indent=1))
print(json.dumps(OUT["median_oos_ratio_by_hunt_bucket"], indent=1))
print("\n--- cells with ratio>1 in BOTH windows, top 25 by OOS day-clustered t ---")
print("%-24s %-30s %6s %7s %7s %6s %7s %7s" % ("grouping", "cell", "hunt_n", "h_ratio", "h_net", "oos_n", "o_ratio", "o_tday"))
for c in both[:25]:
    print("%-24s %-30s %6d %7.2f %+7.4f %6d %7.2f %+7.2f" %
          (c["grouping"], c["cell"][:30], c["hunt_n"], c["hunt_ratio"], c["hunt_net"],
           c["oos_n"], c["oos_ratio"], c["oos_t_day"] or 0))
