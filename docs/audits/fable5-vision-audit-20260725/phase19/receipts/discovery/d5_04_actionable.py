"""d5-04 — the ACTIONABLE test.

A separator is only worth anything on rows where an action is still available when it becomes
readable.  At T+1m that is exactly the PENDING set (j >= 1: the resting order has not been
touched).  Everything else is an exit decision on a position you already own.

Measures, on the honest population (mkt_r0 >= 0, i.e. the resting fill at e is physically
reachable):
  A. separation of every observable on PENDING rows (cancel decision) vs PREFILLED rows (exit)
  B. the economics of a cancel rule swept over thresholds, per opportunity, per window
  C. the leakage control for the T+5m features
"""
import json, sys
import numpy as np
sys.path.insert(0, "/tmp/d5")
from d5_lib import *

FEATS = ["mkt_r0", "geo", "barrng_r", "atr60_r", "risk_bps", "cost_r",
         "c0", "disp0", "c0_fav", "c0_adv", "c0_rng", "vol0_ratio",
         "c1", "c4", "fav5", "adv5", "mom5", "disp5"]
ACC = []
for wi, w in enumerate(WINDOWS):
    D = load(w)
    D["mom5"] = D["c4"] - D["c0"]
    D["disp5"] = D["c4"] - D["mkt_r0"]
    keep = FEATS + ["g", "net", "reason", "sym", "fam", "hour", "j"]
    ACC.append({k: D[k] for k in keep} | {"day": D["dayi"] + 1000 * wi, "win": np.full(D["g"].size, wi)})
A = {k: np.concatenate([a[k] for a in ACC]) for k in ACC[0]}
N = A["g"].size
resolved = np.isin(A["reason"], [0, 1]); is_t = A["reason"] == 0
honest = A["mkt_r0"] >= 0.0
pending = A["j"] >= 1
prefilled = A["j"] == 0
g = A["g"]; net = A["net"]; day = A["day"]

R = {"populations": {}, "sweep": {}, "per_window": {}}
POPS = {
    "HONEST_PENDING_RESOLVED (cancel is available)": resolved & honest & pending,
    "HONEST_PREFILLED_RESOLVED (only an exit is available)": resolved & honest & prefilled,
}
for pname, m in POPS.items():
    idx = np.nonzero(m)[0]
    lt = is_t[idx]
    rows = {}
    for f in FEATS:
        x = A[f][idx].astype(float)
        dd = cohens_d(x[lt], x[~lt]); aa = auc(x[lt], x[~lt])
        rows[f] = {"cohens_d": dd, "auc": aa, "beats_0.152": bool(abs(dd) > 0.152)}
    R["populations"][pname] = {"n": int(m.sum()), "n_target": int(lt.sum()),
                               "n_stop": int((~lt).sum()), "features": rows}
    print("==", pname, "n=", int(m.sum()))
    for f in FEATS:
        print("   %-12s d=%+.4f auc=%.4f %s" % (f, rows[f]["cohens_d"], rows[f]["auc"],
                                                "<-- beats ceiling" if rows[f]["beats_0.152"] else ""))

# ---- B. economics of every achievable cancel rule, swept
base_g = float(g.mean()); base_n = float(net.mean())
R["baseline"] = {"pool_gross": base_g, "pool_net": base_n, "n": int(N)}
canc = pending & honest          # rows where a cancel at T+1m is physically possible
R["cancellable_census"] = {"n": int(canc.sum()), "share": float(canc.mean()),
                           "gross_mean_of_cancellable": float(g[canc].mean()),
                           "net_mean_of_cancellable": float(net[canc].mean()),
                           "total_gross_R": float(g[canc].sum())}
for f in ("c0", "disp0", "c0_adv", "mom5", "disp5"):
    x = A[f]
    qs = np.nanquantile(x[canc], [0.05, 0.10, 0.20, 0.30, 0.50, 0.70, 0.90])
    cells = []
    for q, th in zip([0.05, 0.10, 0.20, 0.30, 0.50, 0.70, 0.90], qs):
        cut = canc & (x <= th)
        gv = np.where(cut, 0.0, g); nv = np.where(cut, 0.0, net)
        cells.append({"quantile": q, "threshold": float(th), "n_cancelled": int(cut.sum()),
                      "cancelled_gross_mean": float(g[cut].mean()) if cut.sum() else None,
                      "pool_gross": float(gv.mean()), "pool_net": float(nv.mean()),
                      "delta_gross": float(gv.mean() - base_g),
                      "delta_net": float(nv.mean() - base_n),
                      "ci_delta_gross": dayblock_ci(gv - g, day)})
        # also the mirror cut (cancel the TOP tail) as the symmetry control
        cut2 = canc & (x > th)
        gv2 = np.where(cut2, 0.0, g)
        cells[-1]["mirror_delta_gross"] = float(gv2.mean() - base_g)
    R["sweep"][f] = cells
    print("--", f, "best delta_gross", max(c["delta_gross"] for c in cells))

# ---- C. leakage control: T+5m features on PREFILLED rows are partly the trade itself
m = resolved & honest & prefilled
idx = np.nonzero(m)[0]
lt = is_t[idx]
lk = {}
for f in ("c0", "c4", "disp5"):
    x = A[f][idx]
    xt = x[lt]; xs = x[~lt]
    lk[f] = {"share_of_target_rows_already_at_or_past_2R": float((xt >= 2.0).mean()),
             "share_of_stop_rows_already_at_or_past_-1R": float((xs <= -1.0).mean()),
             "d_after_dropping_rows_already_resolved_at_the_observation_instant":
                 cohens_d(xt[xt < 2.0], xs[xs > -1.0]),
             "n_target_kept": int((xt < 2.0).sum()), "n_stop_kept": int((xs > -1.0).sum())}
R["leakage_control"] = lk
print(json.dumps(lk, indent=1, default=float))

# ---- per-window replication of the actionable separation
for wi, w in enumerate(WINDOWS):
    mw = A["win"] == wi
    sub = {}
    for f in ("c0", "disp0", "mom5", "disp5", "geo"):
        mm = mw & resolved & honest & pending
        x = A[f][mm].astype(float); lt2 = is_t[mm]
        sub[f] = {"d": cohens_d(x[lt2], x[~lt2]), "auc": auc(x[lt2], x[~lt2]), "n": int(mm.sum())}
    R["per_window"][w] = sub
json.dump(R, open("/tmp/d5/out/D5_04_ACTIONABLE.json", "w"), indent=1, default=float)
print("saved")
