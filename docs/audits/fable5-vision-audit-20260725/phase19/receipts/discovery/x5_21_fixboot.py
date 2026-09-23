#!/usr/bin/env python3
"""x5_21_fixboot - recompute the paired day-block bootstrap vs k=0 with NaN masking.
x5_20 left 8 rungs NaN because a handful of rows carry no walkable path at those offsets."""
import json, os, sys
import numpy as np
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
import x5_lib as X

w = X.W()
b0 = X.rungs_walk(w, 0, horizon="MATCH", denom="STRUCTSTOP", contract="INC")
r0 = b0["r"]; g0 = b0["good"] & ~np.isnan(r0)
out = []
for k in X.RUNGS:
    o = X.rungs_walk(w, k, horizon="MATCH", denom="STRUCTSTOP", contract="INC")
    g = g0 & o["good"] & ~np.isnan(o["r"])
    bt = X.paired_boot(o["r"][g], r0[g], w.dayi[g], B=2000, seed=5000 + k + 100)
    bt["k"] = k; bt["n"] = int(g.sum())
    out.append(bt)
    print("%+4d n=%6d delta %+0.4f [%+0.4f,%+0.4f] p<=0 %.4f" % (k, bt["n"], bt["mean"], bt["lo"], bt["hi"], bt["p_le0"]), flush=True)
p = os.path.join(D, "x5_LADDER_V1.json")
d = json.load(open(p)); d["paired_boot_vs_k0"] = out
json.dump(d, open(p, "w"))
print("PATCHED x5_LADDER_V1.json")
