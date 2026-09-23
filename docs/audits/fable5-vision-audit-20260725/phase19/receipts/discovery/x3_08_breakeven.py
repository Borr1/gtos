#!/usr/bin/env python3
"""x3_08_breakeven — the precision an intra-bar separator must reach for earliness to pay.

For each (polarity, theta, minute) cell of the unconditional early book:
    net(prec) = prec * net_confirmed + (1 - prec) * net_phantom
    break-even precision = -net_phantom / (net_confirmed - net_phantom)
and the gap between that and the precision a bare displacement trigger achieves.
"""
from __future__ import annotations
import json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)

d = json.load(open(os.path.join(HERE, "X3_BOOK_V1.json")))
base = d["baseline_m15_close"]
rows = []
for k, c in d["cells"].items():
    if c["mode"] != "UNCOND":
        continue
    a, b_ = c["net_R_confirmed"], c["net_R_phantom"]
    if a is None or b_ is None or a <= b_:
        continue
    be = -b_ / (a - b_)
    rows.append({"arm": c["arm"], "theta": c["theta"], "minute": c["minute"],
                 "k": c["k"], "n": c["n"], "precision_achieved": c["precision"],
                 "net_R_confirmed": a, "net_R_phantom": b_,
                 "breakeven_precision": float(be),
                 "gap": float(be - c["precision"]),
                 "net_R_at_achieved": c["net_R"],
                 "precision_to_beat_baseline": float((base["net_R"] - b_) / (a - b_)),
                 "net_bps": c["net_bps"]})
rows.sort(key=lambda r: r["gap"])
print(f"baseline (real candidates at the M15 close): net {base['net_R']:+.5f} R "
      f"({base['net_bps']:+.4f} bps), n={base['n']}\n")
print(f"{'arm':>5s} {'th':>5s} {'min':>4s} {'k':>4s} {'n':>6s} {'prec':>6s} {'net_conf':>9s} "
      f"{'net_phan':>9s} {'BE_prec':>8s} {'gap':>7s} {'BE_beat_base':>12s}")
for r in rows[:34]:
    print(f"{r['arm']:>5s} {r['theta']:5.2f} {r['minute']:4d} {r['k']:+4d} {r['n']:6d} "
          f"{r['precision_achieved']:6.4f} {r['net_R_confirmed']:+9.5f} "
          f"{r['net_R_phantom']:+9.5f} {r['breakeven_precision']:8.4f} {r['gap']:+7.4f} "
          f"{r['precision_to_beat_baseline']:12.4f}")

best_conf = max(rows, key=lambda r: r["net_R_confirmed"])
out = {"baseline": base, "cells": rows,
       "min_gap_cell": rows[0],
       "best_confirmed_cell": best_conf,
       "note": ("breakeven_precision = the share of early firings that must turn out to be "
                "real candidates for the unconditional early book to reach 0 net R; "
                "precision_to_beat_baseline = the share needed merely to beat entering the "
                "same names at the M15 close.")}
json.dump(out, open(os.path.join(HERE, "X3_BREAKEVEN_V1.json"), "w"), indent=1)
print("\nsmallest gap:", rows[0]["arm"], rows[0]["theta"], "min", rows[0]["minute"],
      "needs", round(rows[0]["breakeven_precision"], 4), "has",
      round(rows[0]["precision_achieved"], 4))
print("best confirmed leg:", best_conf["arm"], best_conf["theta"], "min", best_conf["minute"],
      "net_conf", round(best_conf["net_R_confirmed"], 5), "needs",
      round(best_conf["breakeven_precision"], 4), "has",
      round(best_conf["precision_achieved"], 4))
print("wrote X3_BREAKEVEN_V1.json")
