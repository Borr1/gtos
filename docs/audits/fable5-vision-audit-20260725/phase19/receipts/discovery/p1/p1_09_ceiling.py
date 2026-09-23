"""p1 step 9 — THE ORACLE CEILING OF CELL SELECTION.

From the variance decomposition (P1_VAR_V1): true between-cell sd tau.  An oracle that
knew each cell's TRUE edge and kept the best fraction q gains at most
    E[top-q of N(0,tau)] = tau * phi(z_q) / q          (normal approximation)
This is the hard ceiling on what ANY cell-conditioning rule can be worth, with perfect
foreknowledge and no estimation error at all.  Reported for GROSS against COST.
"""
import json, numpy as np, math
V = json.load(open("/tmp/p1/P1_VAR_V1.json"))
def phi(x): return math.exp(-x*x/2)/math.sqrt(2*math.pi)
def z_of(q):
    # inverse normal cdf at 1-q, Acklam-free: use bisection
    lo, hi = -8.0, 8.0
    tgt = 1 - q
    for _ in range(200):
        mid = (lo+hi)/2
        c = 0.5*(1+math.erf(mid/math.sqrt(2)))
        if c < tgt: lo = mid
        else: hi = mid
    return (lo+hi)/2
OUT = {}
for pop in V:
    OUT[pop] = {}
    for kind in V[pop]:
        a = V[pop][kind]["pooled_mean"]
        tg, tc = a["gross"]["true_sd"], a["cost"]["true_sd"]
        row = {"true_sd_gross": tg, "true_sd_cost": tc}
        for q in (0.50, 0.25, 0.10):
            g = phi(z_of(q))/q
            row[f"oracle_gain_gross_q{q:.2f}"] = tg*g
            row[f"oracle_gain_cost_q{q:.2f}"] = tc*g
        OUT[pop][kind] = row
        print(f"{pop:12s} {kind:14s} tau_gross {tg:.5f} tau_cost {tc:.5f} | "
              f"ORACLE q50 gross {row['oracle_gain_gross_q0.50']:+.5f} cost {row['oracle_gain_cost_q0.50']:+.5f} | "
              f"q10 gross {row['oracle_gain_gross_q0.10']:+.5f} cost {row['oracle_gain_cost_q0.10']:+.5f}")
json.dump(OUT, open("/tmp/p1/P1_CEILING_V1.json","w"))
