"""d2_rankfeas — the REACHABLE ceiling of the ranking layer.

The ranking layer has the largest real-vs-oracle gap of any layer in the system
(+2.27 R/trade of range at the arm's own 3-trades-per-day capacity).  A gap is only an
engineering target if it can be reached from information available BEFORE the decision.

This fits a ranker on pre-decision observables only — toll, spread, risk distance, hour,
session, family, instrument, and the calendar-free interactions of those — on seven
months, and uses it to pick the top K rows of each day of the held-out eighth.  Ridge on
the realised net R, plus every single-field ranker, plus both signs of each.

Nothing here can see an outcome on the month it is scored on.
"""

from __future__ import annotations

import glob
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

OUT = Path("/tmp/d2/out")
K = 3          # the arm's own realised capacity, 507 trades / 172 roster trading days


def load():
    P = {}
    for p in sorted(glob.glob(str(OUT / "D2_2*_V1_ROWS.npz"))):
        m = Path(p).name.split("_")[1]
        P[m] = dict(np.load(p, allow_pickle=True))
    ks = sorted(P)
    cat = {k: np.concatenate([P[m][k] for m in ks]) for k in P[ks[0]]}
    cat["month"] = np.concatenate([np.full(len(P[m]["ok"]), m) for m in ks])
    return cat, ks


def topk(score, day, k, mask):
    keep = np.zeros(len(score), bool)
    by = defaultdict(list)
    for a in np.nonzero(mask)[0]:
        if np.isfinite(score[a]):
            by[day[a]].append(a)
    for d, aa in by.items():
        aa = np.asarray(aa)
        keep[aa[np.argsort(-score[aa])][:k]] = True
    return keep


def econ(g, c, mask, day):
    net = (g - c)[mask]
    if net.size == 0:
        return {"n": 0}
    by = defaultdict(float)
    for a, x in zip(day[mask], net):
        by[a] += x
    return {"n": int(mask.sum()), "gross": float(g[mask].mean()),
            "cost": float(c[mask].mean()), "net": float(net.mean()),
            "total_net_r": float(net.sum()),
            "days_pos": int(sum(1 for k in by if by[k] > 0)), "n_days": len(by)}


def main():
    D, months = load()
    g = D["gross"].astype(float)
    c = D["cost"].astype(float)
    ok = D["ok"].astype(bool) & np.isfinite(g) & np.isfinite(c)
    day = D["day"].astype(str)
    mo = D["month"].astype(str)
    net = np.where(ok, g, np.nan) - c
    net = np.nan_to_num(net, nan=0.0)
    sym = D["sym"].astype(str)
    fam = D["fam"].astype(str)
    feats = {
        "neg_cost_r": -c,
        "neg_spread_r": -D["spread"].astype(float),
        "risk_distance_bps": D["dbps"].astype(float),
        "neg_risk_distance_bps": -D["dbps"].astype(float),
        "in_session": D["sess"].astype(float),
        "hour": D["hour"].astype(float),
    }
    X = [np.ones(len(g))]
    names = ["const"]
    for k, v in feats.items():
        z = (v - np.nanmean(v)) / (np.nanstd(v) + 1e-12)
        X.append(np.nan_to_num(z, nan=0.0, posinf=0.0, neginf=0.0))
        names.append(k)
    for s in sorted(set(sym)):
        X.append((sym == s).astype(float))
        names.append("sym_" + s)
    for f in sorted(set(fam)):
        X.append((fam == f).astype(float))
        names.append("fam_" + f)
    X = np.vstack(X).T
    out = {"lane": "d2_rankfeas", "K_per_day": K, "n_features": X.shape[1],
           "features": names, "months": months}

    # ---------------- reference books on the held-out months, at the same capacity
    rows = []
    rng = np.random.default_rng(20260806)
    for held in months:
        te = ok & (mo == held)
        tr = ok & (mo != held)
        Xtr, ytr = X[tr], net[tr]
        lam = 10.0
        A = Xtr.T @ Xtr + lam * np.eye(X.shape[1])
        b = Xtr.T @ ytr
        w = np.linalg.solve(A, b)
        pred = X @ w
        r = {"held_out": held}
        r["RIDGE"] = econ(g, c, topk(pred, day, K, te), day)
        r["ORACLE"] = econ(g, c, topk(net, day, K, te), day)
        r["ANTI"] = econ(g, c, topk(-net, day, K, te), day)
        rr = []
        for _ in range(200):
            rr.append(econ(g, c, topk(rng.random(len(g)), day, K, te), day)["net"])
        r["RANDOM"] = {"net": float(np.mean(rr)), "sd": float(np.std(rr))}
        for fname, fv in feats.items():
            r["single_" + fname] = econ(g, c, topk(fv, day, K, te), day)
        rows.append(r)
    out["LEAVE_ONE_MONTH_OUT"] = rows

    def pool(key, sub=None):
        vals, ns = [], []
        for r in rows:
            v = r[key] if sub is None else r[key]
            if isinstance(v, dict) and v.get("n"):
                vals.append(v["net"])
                ns.append(v["n"])
            elif isinstance(v, dict) and "net" in v:
                vals.append(v["net"])
                ns.append(1)
        return float(np.average(vals, weights=ns)) if vals else None

    keys = ["RIDGE", "ORACLE", "ANTI", "RANDOM"] + ["single_" + k for k in feats]
    P = {k: pool(k) for k in keys}
    P["months_ridge_beats_random"] = int(sum(
        1 for r in rows if r["RIDGE"]["net"] > r["RANDOM"]["net"]))
    P["capture_ridge"] = (P["RIDGE"] - P["RANDOM"]) / (P["ORACLE"] - P["RANDOM"])
    best_single = max((k for k in keys if k.startswith("single_")), key=lambda k: P[k])
    P["best_single_field"] = best_single
    P["capture_best_single"] = (P[best_single] - P["RANDOM"]) / (P["ORACLE"] - P["RANDOM"])
    out["POOLED_OOS"] = P
    Path(OUT / "D2_RANKFEAS_V1.json").write_text(json.dumps(out, indent=1, default=str))
    print("K=%d/day, %d held-out months, %d features" % (K, len(months), X.shape[1]))
    for k in keys:
        print("%-30s pooled OOS net %+.5f" % (k, P[k]))
    print("ridge beats random in %d/8 months; capture %.4f; best single %s capture %.4f"
          % (P["months_ridge_beats_random"], P["capture_ridge"], best_single,
             P["capture_best_single"]))
    print("\nper month RIDGE / ORACLE / RANDOM")
    for r in rows:
        print("%s  ridge %+.5f (n=%d)  oracle %+.5f  random %+.5f"
              % (r["held_out"], r["RIDGE"]["net"], r["RIDGE"]["n"], r["ORACLE"]["net"],
                 r["RANDOM"]["net"]))


if __name__ == "__main__":
    main()
