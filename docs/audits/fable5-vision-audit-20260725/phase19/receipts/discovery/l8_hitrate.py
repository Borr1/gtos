#!/usr/bin/env python3
"""l8_hitrate — THE LANE QUESTION, on the honest contract.

For every conditioning cell (singles + pairs over decision-time-available axes) measure:
  - honest first-touch R at the DECLARED 2R/-1R (entry must trade first)
  - target_rate / stop_rate / mark_rate / nofill_rate
  - RESOLUTION WIN RATE  = target/(target+stop) -- the number that must beat 1/3
  - the cell's best (T,S) on a reduced grid, and that cell's win rate
  - stability across January thirds
"""
import json, os, itertools, collections
import l8_lib as L
from l8_sweepN import enrich2
import l8_grid as G

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "L8_HITRATE_V1.json")
TI = [G.TGT.index(x) for x in (0.5, 0.75, 1.0, 1.5, 2.0, 3.0)]
SI = [G.STP.index(x) for x in (-0.5, -0.75, -1.0, -1.5)]
DECL = (G.TGT.index(2.0), G.STP.index(-1.0))
AXES = ["hour", "hour_b", "dow", "symbol", "family", "side", "route_session", "msc",
        "risk_pct", "born", "rdp_b", "spread_b", "cost_b", "prob_b", "ev_b", "fillp_b",
        "fill_class", "order_type", "sched", "lifecycle", "risk_rank_b", "first_em"]
MIN_N = 60
THIRDS = ["J1_d1_10", "J2_d11_20", "J3_d21_31"]


def precompute(rows, ladder):
    """attach per-row resolution vectors for the reduced grid + the declared contract"""
    for r in rows:
        l = ladder.get((r["cid"], r["dt"]))
        r["_l"] = l
        vec = {}
        for ti in TI:
            for si in SI:
                vec[(ti, si)] = G.resolve(l, ti, si)
        r["_v"] = vec


def agg(rows, ti, si):
    n = len(rows)
    if n == 0:
        return None
    s = 0.0
    c = {"target": 0, "stop": 0, "mark": 0, "no_fill": 0}
    vs = []
    for r in rows:
        v, o = r["_v"][(ti, si)]
        c[o] += 1
        s += v
        vs.append(v)
    m = s / n
    sd = (sum((v - m) ** 2 for v in vs) / (n - 1)) ** 0.5 if n > 1 else 0.0
    res = c["target"] + c["stop"]
    return {"n": n, "mean": round(m, 5), "t": round(m / (sd / n ** 0.5), 3) if sd > 0 else 0.0,
            "win": round(sum(1 for v in vs if v > 0) / n, 4),
            "target_rate": round(c["target"] / n, 4), "stop_rate": round(c["stop"] / n, 4),
            "mark_rate": round(c["mark"] / n, 4), "nofill_rate": round(c["no_fill"] / n, 4),
            "res_win": round(c["target"] / res, 4) if res else None, "n_res": res}


def cell(rows):
    d = agg(rows, *DECL)
    bestc = None
    for ti in TI:
        for si in SI:
            a = agg(rows, ti, si)
            if a and (bestc is None or a["mean"] > bestc["mean"]):
                a = dict(a)
                a["target"] = G.TGT[ti]
                a["stop"] = G.STP[si]
                bestc = a
    th = {}
    for t in THIRDS:
        sub = [r for r in rows if r["third"] == t]
        a = agg(sub, *DECL) if sub else None
        th[t] = None if a is None else [a["n"], a["mean"], a["res_win"]]
    return {"declared": d, "best": bestc, "thirds": th,
            "pos_thirds": sum(1 for v in th.values() if v and v[1] > 0)}


def main():
    rows = L.load()
    enrich2(rows)
    ladder = G.load_ladder()
    precompute(rows, ladder)
    clean = [r for r in rows if r["born"] != "born_past_stop"]
    res = {"pool_all": cell(rows), "pool_clean": cell(clean), "min_n": MIN_N,
           "singles": [], "pairs": [], "cells_examined": 0}
    ex = 0
    for ax in AXES:
        g = collections.defaultdict(list)
        for r in clean:
            g[str(r.get(ax))].append(r)
        for v, sub in g.items():
            ex += 1
            if len(sub) < MIN_N:
                continue
            c = cell(sub)
            c["keys"] = [ax]
            c["vals"] = [v]
            res["singles"].append(c)
    for a, b in itertools.combinations(AXES, 2):
        g = collections.defaultdict(list)
        for r in clean:
            g[(str(r.get(a)), str(r.get(b)))].append(r)
        for v, sub in g.items():
            ex += 1
            if len(sub) < MIN_N:
                continue
            c = cell(sub)
            c["keys"] = [a, b]
            c["vals"] = list(v)
            res["pairs"].append(c)
    res["cells_examined"] = ex
    res["singles"].sort(key=lambda c: -c["declared"]["mean"])
    res["pairs"].sort(key=lambda c: -c["declared"]["mean"])
    with open(OUT, "w") as fh:
        json.dump(res, fh, separators=(",", ":"))
    p = res["pool_clean"]["declared"]
    print("POOL CLEAN honest 2R/-1R: n=%d mean=%+.5f win=%.4f tgt=%.4f stop=%.4f mark=%.4f resWin=%.4f"
          % (p["n"], p["mean"], p["win"], p["target_rate"], p["stop_rate"], p["mark_rate"], p["res_win"]))
    print("cells examined %d | singles reported %d | pairs reported %d"
          % (ex, len(res["singles"]), len(res["pairs"])))
    print("\nSINGLES with positive honest 2R/-1R mean:")
    for c in res["singles"]:
        d = c["declared"]
        if d["mean"] <= 0:
            break
        print("  %-14s %-24s n=%5d mean=%+.4f resWin=%.4f t=%+.2f %d/3" % (
            c["keys"][0], c["vals"][0][:24], d["n"], d["mean"], d["res_win"] or 0, d["t"], c["pos_thirds"]))
    print("\nTOP 22 PAIRS by honest 2R/-1R mean (n>=120, 3/3 thirds):")
    sel = [c for c in res["pairs"] if c["declared"]["n"] >= 120 and c["pos_thirds"] == 3]
    for c in sel[:22]:
        d = c["declared"]
        print("  %-26s %-30s n=%5d mean=%+.4f resWin=%.4f t=%+.2f" % (
            "+".join(c["keys"])[:26], "|".join(c["vals"])[:30], d["n"], d["mean"], d["res_win"] or 0, d["t"]))


if __name__ == "__main__":
    main()
