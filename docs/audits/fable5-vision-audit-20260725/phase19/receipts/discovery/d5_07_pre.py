"""d5-07 — the one achievable repair the confirm minute was a shadow of.

68.1 % of the R the confirm-minute rule "avoids" sits in rows whose decision anchor is already
adverse AT T (mkt_r0 < 0: the market has already left the entry level in the losing direction, so
the resting order is a MARKETABLE limit and the estate's walk fills it at a price it cannot have).
That is knowable at the decision instant and refusable by simply not placing the order.

This lane prices it per window, against the alternative the live engine actually implements
(a market order at the prevailing price with the same risk distance).
"""
import json, sys
import numpy as np
sys.path.insert(0, "/tmp/d5")
from d5_lib import *

ACC = []
for wi, w in enumerate(WINDOWS):
    D = load(w)
    keep = ["g", "net", "cost_r", "c0", "mkt_r0", "j", "reason", "sym", "fam", "geo",
            "ra_g", "ra_net", "risk_bps"]
    ACC.append({k: D[k] for k in keep} | {"day": D["dayi"] + 1000 * wi,
                                          "win": np.full(D["g"].size, wi)})
A = {k: np.concatenate([a[k] for a in ACC]) for k in ACC[0]}
N = A["g"].size
g = A["g"]; net = A["net"]; mk = A["mkt_r0"]; day = A["day"]
rag = np.where(np.isfinite(A["ra_g"]), A["ra_g"], 0.0)
ran = np.where(np.isfinite(A["ra_net"]), A["ra_net"], 0.0)
mktable = mk < 0.0
R = {"N": int(N), "n_marketable_limit_rows": int(mktable.sum()),
     "share": float(mktable.mean())}

R["cohort"] = {
    "gross_as_the_estate_walks_it": float(g[mktable].mean()),
    "net_as_the_estate_walks_it": float(net[mktable].mean()),
    "gross_if_entered_at_market_instead": float(rag[mktable].mean()),
    "net_if_entered_at_market_instead": float(ran[mktable].mean()),
    "total_gross_R_booked_by_this_cohort": float(g[mktable].sum()),
    "share_of_all_roster_gross_R": float(g[mktable].sum() / g.sum()) if g.sum() else None,
    "stop_rate": float((A["reason"][mktable] == 1).mean()),
    "median_mkt_r0": float(np.median(mk[mktable])),
}
base_g = float(g.mean()); base_n = float(net.mean())
R["baseline"] = {"pool_gross": base_g, "pool_net": base_n}
arms = {}
for tag, gv, nv in (
    ("A_refuse_marketable_at_T", np.where(mktable, 0.0, g), np.where(mktable, 0.0, net)),
    ("B_enter_at_market_instead", np.where(mktable, rag, g), np.where(mktable, ran, net)),
):
    arms[tag] = {"pool_gross": float(gv.mean()), "pool_net": float(nv.mean()),
                 "delta_gross": float(gv.mean() - base_g), "delta_net": float(nv.mean() - base_n),
                 "ci_delta_gross": dayblock_ci(gv - g, day),
                 "per_window": {w: {"delta_gross": float(gv[A["win"] == i].mean() - g[A["win"] == i].mean()),
                                    "delta_net": float(nv[A["win"] == i].mean() - net[A["win"] == i].mean())}
                                for i, w in enumerate(WINDOWS)}}
# the geometry refusal, for comparison (also PRE, also achievable)
geo = A["geo"]
for th in (0.4, 0.6, 0.8):
    m = np.isfinite(geo) & (geo <= th)
    gv = np.where(m, 0.0, g); nv = np.where(m, 0.0, net)
    arms["C_refuse_geo<=%.1f" % th] = {
        "n_refused": int(m.sum()), "refused_gross": float(g[m].mean()),
        "pool_gross": float(gv.mean()), "pool_net": float(nv.mean()),
        "delta_gross": float(gv.mean() - base_g), "delta_net": float(nv.mean() - base_n),
        "per_window": {w: {"delta_gross": float(gv[A["win"] == i].mean() - g[A["win"] == i].mean())}
                       for i, w in enumerate(WINDOWS)}}
# joint
mj = mktable | (np.isfinite(geo) & (geo <= 0.6))
gv = np.where(mj, 0.0, g); nv = np.where(mj, 0.0, net)
arms["D_joint_marketable_or_geo<=0.6"] = {
    "n_refused": int(mj.sum()), "pool_gross": float(gv.mean()), "pool_net": float(nv.mean()),
    "delta_gross": float(gv.mean() - base_g), "delta_net": float(nv.mean() - base_n),
    "sum_of_standalone_deltas": float(arms["A_refuse_marketable_at_T"]["delta_net"]
                                      + arms["C_refuse_geo<=0.6"]["delta_net"]),
    "per_window": {w: {"delta_net": float(nv[A["win"] == i].mean() - net[A["win"] == i].mean())}
                   for i, w in enumerate(WINDOWS)}}
R["arms"] = arms
json.dump(R, open("/tmp/d5/out/D5_07_PRE.json", "w"), indent=1, default=float)
print(json.dumps(R["cohort"], indent=1, default=float))
for k, v in arms.items():
    print("%-34s dg %+.5f dn %+.5f" % (k, v["delta_gross"], v["delta_net"]))
    if "per_window" in v:
        print("      per-window dnet/dgross:", {w: round(list(x.values())[-1], 5)
                                                for w, x in v["per_window"].items()})
print("saved")
