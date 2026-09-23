"""d5-05 — the EXIT decision: the one place where the confirm minute genuinely separates.

On honest fills that were already open when c0 became readable (mkt_r0 >= 0 and j == 0),
c0 separates target-first from stop-first at d = 0.538.  This lane asks the only question that
matters about that: given the separation, is any exit RULE worth anything, and if not, why not.

Mechanism probe: does the adversely-moved cohort recover, or is it doomed?
"""
import json, sys
import numpy as np
sys.path.insert(0, "/tmp/d5")
from d5_lib import *

ACC = []
for wi, w in enumerate(WINDOWS):
    D = load(w)
    keep = ["g", "net", "cost_r", "c0", "mkt_r0", "j", "reason", "sym", "fam", "hour", "geo"]
    ACC.append({k: D[k] for k in keep} | {"day": D["dayi"] + 1000 * wi,
                                          "win": np.full(D["g"].size, wi)})
A = {k: np.concatenate([a[k] for a in ACC]) for k in ACC[0]}
N = A["g"].size
g = A["g"]; net = A["net"]; c0 = A["c0"]; day = A["day"]; cost = A["cost_r"]
honest = A["mkt_r0"] >= 0.0
prefilled = A["j"] == 0
open_now = honest & prefilled                # you own this position when c0 is readable
R = {"n_total": int(N), "n_open_at_T1": int(open_now.sum())}

# ---- 1. does the adverse cohort recover?
rows = []
for lo, hi in [(-99, -1.0), (-1.0, -0.5), (-0.5, -0.3), (-0.3, -0.15), (-0.15, -0.05),
               (-0.05, 0.0), (0.0, 0.05), (0.05, 0.15), (0.15, 0.5), (0.5, 99)]:
    m = open_now & (c0 > lo) & (c0 <= hi)
    if m.sum() < 30:
        continue
    ex = np.maximum(c0[m], -1.0)
    rows.append({"c0_band": "(%.2f,%.2f]" % (lo, hi), "n": int(m.sum()),
                 "mean_c0": float(c0[m].mean()),
                 "exit_now_R_clamped": float(ex.mean()),
                 "hold_to_contract_R": float(g[m].mean()),
                 "recovery_hold_minus_exit": float(g[m].mean() - ex.mean()),
                 "stop_rate": float((A["reason"][m] == 1).mean()),
                 "target_rate": float((A["reason"][m] == 0).mean()),
                 "net_hold": float(net[m].mean())})
R["recovery_by_c0_band"] = rows
print("%-16s %8s %9s %9s %9s %8s" % ("c0 band", "n", "exit now", "hold", "recovery", "stop%"))
for r in rows:
    print("%-16s %8d %9.4f %9.4f %+9.4f %8.3f" % (r["c0_band"], r["n"], r["exit_now_R_clamped"],
                                                  r["hold_to_contract_R"],
                                                  r["recovery_hold_minus_exit"], r["stop_rate"]))

# ---- 2. exit-rule sweep, priced per opportunity over the WHOLE roster
base_g = float(g.mean()); base_n = float(net.mean())
R["baseline"] = {"pool_gross": base_g, "pool_net": base_n}
sweep = []
for th in (-0.75, -0.5, -0.4, -0.3, -0.2, -0.15, -0.10, -0.05, 0.0, 0.10, 0.25):
    m = open_now & (c0 <= th)
    ex = np.maximum(c0, -1.0)
    gv = np.where(m, ex, g); nv = np.where(m, ex - cost, net)
    sweep.append({"threshold": th, "n_exited": int(m.sum()),
                  "pool_gross": float(gv.mean()), "pool_net": float(nv.mean()),
                  "delta_gross": float(gv.mean() - base_g), "delta_net": float(nv.mean() - base_n),
                  "ci_delta_gross": dayblock_ci(gv - g, day)})
R["exit_sweep"] = sweep
print("\n%-10s %9s %11s %11s" % ("exit th", "n", "d_gross", "d_net"))
for s in sweep:
    print("%-10.2f %9d %+11.5f %+11.5f" % (s["threshold"], s["n_exited"],
                                           s["delta_gross"], s["delta_net"]))

# ---- 3. the mirror: take profit early on the favourable side
sweep2 = []
for th in (0.05, 0.10, 0.25, 0.50, 1.00):
    m = open_now & (c0 >= th)
    gv = np.where(m, c0, g); nv = np.where(m, c0 - cost, net)
    sweep2.append({"threshold": th, "n_exited": int(m.sum()),
                   "delta_gross": float(gv.mean() - base_g), "delta_net": float(nv.mean() - base_n)})
R["early_takeprofit_sweep"] = sweep2

# ---- 4. per-window replication of the best exit cell
best = min(sweep, key=lambda s: -s["delta_gross"])
R["best_exit_cell"] = best
pw = {}
for wi, w in enumerate(WINDOWS):
    mw = A["win"] == wi
    m = open_now & (c0 <= best["threshold"]) & mw
    ex = np.maximum(c0, -1.0)
    gv = np.where(m, ex, g); nv = np.where(m, ex - cost, net)
    pw[w] = {"delta_gross": float(gv[mw].mean() - g[mw].mean()),
             "delta_net": float(nv[mw].mean() - net[mw].mean()),
             "n_exited": int(m.sum()), "n": int(mw.sum())}
R["best_exit_per_window"] = pw
print("\nbest exit cell", best["threshold"], "delta_gross %.5f" % best["delta_gross"])
for w, v in pw.items():
    print("  %s dg %+.5f dn %+.5f n_exit %d" % (w, v["delta_gross"], v["delta_net"], v["n_exited"]))
json.dump(R, open("/tmp/d5/out/D5_05_EXIT.json", "w"), indent=1, default=float)
print("saved")
