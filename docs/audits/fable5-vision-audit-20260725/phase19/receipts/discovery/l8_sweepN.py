#!/usr/bin/env python3
"""l8_sweepN — pair and triple conditioning sweeps. Primary metric = CLEAN gross_r
(born_past_stop dropped: W0-capture proved those 3,516 rows were never takeable)."""
import json, os, sys, itertools, collections
import l8_lib as L
from l8_sweep1 import enrich

HERE = os.path.dirname(os.path.abspath(__file__))

AXES = ["family", "symbol", "side", "hour_b", "hour", "route_session", "msc", "risk_pct",
        "born", "rdp_b", "spread_b", "cost_b", "prob_b", "ev_b", "fillp_b", "fill_class",
        "dup_b", "first_em", "order_type", "sched", "lifecycle", "ptr_b", "dow",
        "adm_risk_class", "risk_rank_b", "limit_mkt"]

MIN_N = 50


def enrich2(rows):
    enrich(rows)
    for r in rows:
        h = r["hour"]
        r["hour_b"] = ("h00_03" if h < 4 else "h04_07" if h < 8 else "h08_11" if h < 12
                       else "h12_15" if h < 16 else "h16_19" if h < 20 else "h20_23")


def cell_row(g, keys, vals, thirds=("J1_d1_10", "J2_d11_20", "J3_d21_31")):
    clean = [r for r in g if r["born"] != "born_past_stop"]
    if len(clean) < MIN_N:
        return None
    cs = L.stats(clean)
    rs = L.stats(g)
    hs = L.stats(g, "honest_r")
    hcs = L.stats(clean, "honest_r")
    byt = {}
    for t in thirds:
        sub = [r for r in clean if r["third"] == t]
        st = L.stats(sub) if sub else None
        byt[t] = None if st is None else {"n": st["n"], "win": round(st["win"], 4), "mean": round(st["mean"], 4)}
    pos_thirds = sum(1 for v in byt.values() if v and v["mean"] > 0)
    ev_thirds = sum(1 for v in byt.values() if v and v["n"] >= 15)
    return {
        "keys": list(keys), "vals": [str(v) for v in vals],
        "n_raw": rs["n"], "raw_mean": round(rs["mean"], 5), "raw_win": round(rs["win"], 4),
        "n": cs["n"], "win": round(cs["win"], 4), "mean": round(cs["mean"], 5),
        "t": round(cs["t"], 3), "sum": round(cs["sum"], 2),
        "payoff": round(cs["payoff"], 3), "be_win": round(cs["be_win"], 4),
        "edge_vs_be": round(cs["win"] - cs["be_win"], 4),
        "mean_win": round(cs["mean_win"], 4), "mean_loss": round(cs["mean_loss"], 4),
        "honest_mean": round(hs["mean"], 5), "honest_win": round(hs["win"], 4),
        "honest_clean_mean": round(hcs["mean"], 5), "honest_clean_win": round(hcs["win"], 4),
        "thirds": byt, "pos_thirds": pos_thirds, "eval_thirds": ev_thirds,
    }


def sweep(rows, order, out_path):
    examined = 0
    cells = []
    for combo in itertools.combinations(AXES, order):
        groups = collections.defaultdict(list)
        for r in rows:
            groups[tuple(str(r.get(a)) for a in combo)].append(r)
        for vals, g in groups.items():
            examined += 1
            if len(g) < MIN_N:
                continue
            cr = cell_row(g, combo, vals)
            if cr:
                cells.append(cr)
    cells.sort(key=lambda c: -c["mean"])
    res = {"order": order, "min_n": MIN_N, "cells_examined": examined,
           "cells_reported": len(cells), "cells": cells}
    with open(out_path, "w") as fh:
        json.dump(res, fh, separators=(",", ":"))
    print("order=%d examined=%d reported=%d positive=%d" % (
        order, examined, len(cells), sum(1 for c in cells if c["mean"] > 0)))
    return res


if __name__ == "__main__":
    order = int(sys.argv[1])
    rows = L.load()
    enrich2(rows)
    sweep(rows, order, os.path.join(HERE, "L8_SWEEP%d_V1.json" % order))
