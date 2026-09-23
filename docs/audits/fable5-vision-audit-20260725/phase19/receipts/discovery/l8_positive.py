#!/usr/bin/env python3
"""l8_positive — THE POSITIVE-CELL CENSUS. Singles + pairs + triples over decision-time
axes, on the DELAYED-FILL clean population (entry not touched in the first minute),
honest 2R/-1R first touch. Reports every cell n>=50 with a positive mean, plus the
converse (every reliably terrible cell)."""
import json, os, itertools, collections
import l8_lib as L
from l8_sweepN import enrich2
import l8_grid as G

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "L8_POSITIVE_V1.json")
TI, SI = G.TGT.index(2.0), G.STP.index(-1.0)
AXES = ["hour", "hour_b", "dow", "symbol", "family", "side", "route_session", "msc",
        "risk_pct", "born", "rdp_b", "spread_b", "cost_b", "prob_b", "ev_b", "fillp_b",
        "fill_class", "order_type", "lifecycle", "risk_rank_b", "first_em", "fs"]
THIRDS = ["J1_d1_10", "J2_d11_20", "J3_d21_31"]
MIN_N = 50


def res1(l):
    fb = l["fill_bar"]
    if fb < 0:
        return 0.0, "no_fill"
    bt, bs = l["tfav"][TI], l["tadv"][SI]
    if bs > 0 and (bt <= 0 or bs <= bt):
        return G.STP[SI], "stop"
    if bt > 0:
        return G.TGT[TI], "target"
    return l["r_end"], "mark"


def agg(rows):
    n = len(rows)
    if n == 0:
        return None
    c = collections.Counter()
    vs = []
    for r in rows:
        v, o = res1(r["_l"])
        c[o] += 1
        vs.append(v)
    m = sum(vs) / n
    sd = (sum((v - m) ** 2 for v in vs) / (n - 1)) ** 0.5 if n > 1 else 0.0
    res = c["target"] + c["stop"]
    return {"n": n, "mean": round(m, 5), "t": round(m / (sd / n ** 0.5), 3) if sd else 0.0,
            "win": round(sum(1 for v in vs if v > 0) / n, 4),
            "res_win": round(c["target"] / res, 4) if res else None, "n_res": res,
            "target": c["target"], "stop": c["stop"], "mark": c["mark"],
            "gross_mean": round(sum(r["gross_r"] for r in rows) / n, 5),
            "total_R": round(sum(vs), 2)}


def cell(rows, keys, vals):
    a = agg(rows)
    th = {}
    for t in THIRDS:
        s2 = [r for r in rows if r["third"] == t]
        aa = agg(s2) if len(s2) >= 12 else None
        th[t] = None if aa is None else [aa["n"], aa["mean"], aa["res_win"]]
    a["keys"] = list(keys)
    a["vals"] = [str(v) for v in vals]
    a["thirds"] = th
    a["pos_thirds"] = sum(1 for v in th.values() if v and v[1] > 0)
    a["eval_thirds"] = sum(1 for v in th.values() if v)
    return a


def main():
    rows = L.load()
    enrich2(rows)
    lad = G.load_ladder()
    for r in rows:
        r["_l"] = lad.get((r["cid"], r["dt"]))
        fb = r["_l"]["fill_bar"]
        r["fs"] = ("never" if fb < 0 else "bar1" if fb == 1 else "b2_5" if fb <= 5
                   else "b6_15" if fb <= 15 else "b16_60" if fb <= 60 else "b61_120")
    clean = [r for r in rows if r["born"] != "born_past_stop"]
    delayed = [r for r in clean if r["_l"]["fill_bar"] >= 2]
    base = agg(delayed)
    res = {"population": "clean AND entry first touched at bar>=2 (one-minute entry delay)",
           "base": base, "min_n": MIN_N, "cells_examined": 0, "positive": [], "negative": []}
    ex = 0
    cells = []
    for o in (1, 2, 3):
        for combo in itertools.combinations(AXES, o):
            g = collections.defaultdict(list)
            for r in delayed:
                g[tuple(str(r.get(a)) for a in combo)].append(r)
            for vals, sub in g.items():
                ex += 1
                if len(sub) < MIN_N:
                    continue
                cells.append(cell(sub, combo, vals))
    res["cells_examined"] = ex
    res["cells_reported"] = len(cells)
    pos = [c for c in cells if c["mean"] > 0]
    neg = [c for c in cells if c["mean"] < base["mean"] and c["n"] >= 100 and c["pos_thirds"] == 0]
    pos.sort(key=lambda c: -(c["mean"] * c["n"]))
    neg.sort(key=lambda c: c["mean"] * c["n"])
    res["positive"] = pos
    res["negative"] = neg[:400]
    json.dump(res, open(OUT, "w"), separators=(",", ":"))
    print("DELAYED-FILL base: n=%d mean=%+.5f resWin=%.4f win=%.4f totalR=%+.1f"
          % (base["n"], base["mean"], base["res_win"], base["win"], base["total_R"]))
    print("cells examined %d | reported (n>=%d) %d | positive %d | reliably-negative %d"
          % (ex, MIN_N, len(cells), len(pos), len(neg)))
    print("\nTOP 26 POSITIVE CELLS by n*mean (delayed-fill, honest 2R/-1R):")
    print("%-34s %-34s %5s %7s %7s %7s %6s %s" % ("axes", "values", "n", "mean", "resWin", "t", "totR", "th+"))
    for c in pos[:26]:
        print("%-34s %-34s %5d %+7.4f %7.4f %+7.2f %+6.1f %d/%d" % (
            "+".join(c["keys"])[:34], "|".join(c["vals"])[:34], c["n"], c["mean"],
            c["res_win"] or 0, c["t"], c["total_R"], c["pos_thirds"], c["eval_thirds"]))
    print("\nTOP 14 RELIABLY-NEGATIVE CELLS by n*mean (0/3 thirds positive):")
    for c in neg[:14]:
        print("%-34s %-34s %5d %+7.4f %7.4f %+7.2f %+6.1f" % (
            "+".join(c["keys"])[:34], "|".join(c["vals"])[:34], c["n"], c["mean"],
            c["res_win"] or 0, c["t"], c["total_R"]))


if __name__ == "__main__":
    main()
