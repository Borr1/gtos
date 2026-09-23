#!/usr/bin/env python3
"""l11 step 4c — THE ROBUST CONTRACT, chosen by minimax rather than by argmax.

L11_ROBUST showed the argmax contract dies to deduplication and to 0.05R of stop
slippage. So do not choose by argmax. Score every contract on all TWELVE convention
cells this pool admits and rank by the WORST cell. A contract that only wins at one
parameter value is not a contract; a contract that is best-in-worst-case is one.

Cells = {ALL_TAKEABLE, FIRST_EMISSION} x {real, strict} x {slip 0, 0.05}
        x {whole month, train, test}, evaluated as 12 gross numbers per contract.
"""
from __future__ import annotations

import itertools
import json
import os

import numpy as np

import l11_family
import l11_lib
import l11_walk

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "L11_MINIMAX_V1.json")
SPLIT = "2026-01-16"


def main():
    s = l11_lib.load()
    eng = {"real": l11_walk.Engine(s, "real"), "strict": l11_walk.Engine(s, "strict")}
    take = s.takeable
    cells = []
    for pop, fillm, slip, win in itertools.product(
            ("ALL", "FIRSTEM"), ("real", "strict"), (0.0, 0.05), ("TEST", "MONTH")):
        m = take.copy()
        if pop == "FIRSTEM":
            m &= s.firstem
        if win == "TEST":
            m &= (s.day >= SPLIT)
        cells.append(("%s|%s|slip%.2f|%s" % (pop, fillm, slip, win), m, fillm, slip))
    CL = list(l11_family.contracts())
    cost = s.cost_r()
    res = {}
    for c in CL:
        lab = l11_family.label(c)
        vals, nets = {}, {}
        for cname, m, fillm, slip in cells:
            r, rs, _ = eng[fillm].run(rows=m, stop_slip_r=slip, **c)
            vals[cname] = float(r.mean())
            nets[cname] = float((r - np.where(rs != 0, cost[m], 0.0)).mean())
        v = np.array(list(vals.values()))
        res[lab] = {"spec": c, "min": round(float(v.min()), 6),
                    "median": round(float(np.median(v)), 6),
                    "max": round(float(v.max()), 6),
                    "spread": round(float(v.max() - v.min()), 6),
                    "n_cells_positive": int((v > 0).sum()),
                    "net_min": round(float(min(nets.values())), 6),
                    "cells": {k: round(x, 6) for k, x in vals.items()}}
    order = sorted(res, key=lambda k: -res[k]["min"])
    inc = l11_family.label({"target": 2.0, "stop": 1.0, "arm_bar": 1, "trail_arm": None,
                            "trail_gap": None, "max_bars": 120})
    hold = l11_family.label({"target": None, "stop": None, "arm_bar": 1, "trail_arm": None,
                             "trail_gap": None, "max_bars": 120})
    out = {"lane": "l11", "pass": "MINIMAX", "n_contracts": len(CL),
           "n_cells": len(cells), "cell_names": [c[0] for c in cells],
           "criterion": "rank by the WORST of 12 convention cells (gross R per candidate)",
           "INCUMBENT": res[inc], "HOLD": res[hold],
           "TOP20_BY_WORST_CELL": {k: res[k] for k in order[:20]},
           "ALL": res}
    with open(OUT, "w") as fh:
        json.dump(out, fh, indent=1)
    print("%-40s %9s %9s %9s %7s %4s" % ("contract", "min", "median", "max", "spread", "pos"))
    for k in order[:15]:
        v = res[k]
        print("%-40s %+9.5f %+9.5f %+9.5f %7.4f %4d"
              % (k, v["min"], v["median"], v["max"], v["spread"], v["n_cells_positive"]))
    for k, lbl in ((inc, "INCUMBENT"), (hold, "HOLD")):
        v = res[k]
        print("%-40s %+9.5f %+9.5f %+9.5f %7.4f %4d  <-- %s"
              % (k, v["min"], v["median"], v["max"], v["spread"], v["n_cells_positive"], lbl))
    print("rank of incumbent by worst cell:", order.index(inc) + 1, "of", len(order))
    print("rank of hold      by worst cell:", order.index(hold) + 1, "of", len(order))


if __name__ == "__main__":
    main()
