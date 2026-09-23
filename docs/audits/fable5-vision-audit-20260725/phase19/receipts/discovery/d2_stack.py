"""d2_stack — every deployable improvement d2 found, priced JOINTLY and out of sample.

The estate's standing hazard is that levers are summed: six worth +1.266 alone delivered
+0.421 together.  So the four things d2 measured as reachable — the shipped cost gate, the
best fixed exit contract, the best fixed entry offset, and a pre-decision ranker at the
arm's own capacity — are priced here on the same rows, in one book, with the ranker fit on
seven months and scored on the eighth.

Step 1 (this file, --build) writes the j=5 entry / stop-only-horizon exit walk per row.
Step 2 (--price) builds the ablation lattice.
"""

from __future__ import annotations

import argparse
import glob
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "pbg"))
OUT = Path("/tmp/d2/out")
BEST_J = 5
K = 3


def build(indir, month, npz):
    import f2_ladder as F
    import f2_run as R2
    import pbg_econ as E
    import pbg_lib as L
    rows = F.load_close_rows(indir, set(F.AT_MARKET))
    tape = E.Tape(L.SYMBOLS, [month])
    cm = E.CostModel()
    fr = R2.build_frame(rows, tape, cm, horizon=F.HORIZON)
    d = dict(np.load(npz, allow_pickle=True))
    res = {}
    for j in (0, BEST_J):
        ej = fr["W_c"][:, j]
        okj = np.isfinite(ej) & fr["ok"]
        rcj, rhj, rlj = F.r_frames(fr["W_c"], fr["W_h"], fr["W_l"], ej, fr["d"],
                                   fr["long"], j, F.HORIZON)
        v2, _ = F.walk_fixed(rcj, rhj, rlj, F.SHIPPED_TARGET_R)
        vs, _ = F.walk_fixed(rcj, rhj, rlj, None)          # stop_only_horizon
        res["j%d_target2R" % j] = np.where(okj, v2, np.nan)
        res["j%d_stoponly" % j] = np.where(okj, vs, np.nan)
    d.update(res)
    np.savez_compressed(npz, **d)
    print(month, {k: float(np.nanmean(v)) for k, v in res.items()}, flush=True)


def load():
    P = {}
    for p in sorted(glob.glob(str(OUT / "D2_2*_V1_ROWS.npz"))):
        m = Path(p).name.split("_")[1]
        P[m] = dict(np.load(p, allow_pickle=True))
    ks = sorted(P)
    cat = {k: np.concatenate([P[m][k] for m in ks]) for k in P[ks[0]]}
    cat["month"] = np.concatenate([np.full(len(P[m]["ok"]), m) for m in ks])
    return cat, ks


def econ(g, c, mask, day):
    if not mask.any():
        return {"n": 0}
    net = (g - c)[mask]
    by = defaultdict(float)
    for a, x in zip(day[mask], net):
        by[a] += x
    return {"n": int(mask.sum()), "gross": float(g[mask].mean()),
            "cost": float(c[mask].mean()), "net": float(net.mean()),
            "total_net_r": float(net.sum()), "n_days": len(by),
            "days_pos": int(sum(1 for k in by if by[k] > 0))}


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


def price():
    D, months = load()
    g0 = D["j0_target2R"].astype(float)
    c = D["cost"].astype(float)
    ok = D["ok"].astype(bool) & np.isfinite(g0) & np.isfinite(c)
    day = D["day"].astype(str)
    mo = D["month"].astype(str)
    gate = D["gate_real"].astype(bool)
    sym, fam = D["sym"].astype(str), D["fam"].astype(str)
    arms = {
        "j0_target2R_SHIPPED": D["j0_target2R"].astype(float),
        "j0_stoponly": D["j0_stoponly"].astype(float),
        "j5_target2R": D["j5_target2R"].astype(float),
        "j5_stoponly": D["j5_stoponly"].astype(float),
    }
    feats = {"neg_cost_r": -c, "neg_spread_r": -D["spread"].astype(float),
             "risk_distance_bps": D["dbps"].astype(float),
             "in_session": D["sess"].astype(float), "hour": D["hour"].astype(float)}
    X = [np.ones(len(c))]
    for v in feats.values():
        z = (v - np.nanmean(v)) / (np.nanstd(v) + 1e-12)
        X.append(np.nan_to_num(z))
    for s in sorted(set(sym)):
        X.append((sym == s).astype(float))
    for f in sorted(set(fam)):
        X.append((fam == f).astype(float))
    X = np.vstack(X).T

    out = {"lane": "d2_stack", "months": months, "K_per_day": K, "best_j": BEST_J}
    lat = {}
    rng = np.random.default_rng(20260806)
    for gname, gm in (("gate_off", ok), ("gate_on", ok & gate)):
        for aname, av in arms.items():
            for rname in ("rank_off", "rank_on", "rank_random", "rank_oracle"):
                cells = []
                for held in months:
                    te = gm & (mo == held)
                    tr = gm & (mo != held)
                    if rname == "rank_off":
                        m = te
                    else:
                        if rname == "rank_on":
                            y = np.nan_to_num(av - c, nan=0.0)
                            A = X[tr].T @ X[tr] + 10.0 * np.eye(X.shape[1])
                            w = np.linalg.solve(A, X[tr].T @ y[tr])
                            sc = X @ w
                        elif rname == "rank_random":
                            sc = rng.random(len(c))
                        else:
                            sc = np.nan_to_num(av - c, nan=-9e9)
                        m = topk(sc, day, K, te)
                    cells.append(econ(np.nan_to_num(av, nan=0.0), c, m, day))
                n = sum(x["n"] for x in cells)
                lat["%s|%s|%s" % (gname, aname, rname)] = {
                    "n": n,
                    "net": float(np.average([x["net"] for x in cells],
                                            weights=[x["n"] for x in cells])),
                    "gross": float(np.average([x["gross"] for x in cells],
                                              weights=[x["n"] for x in cells])),
                    "cost": float(np.average([x["cost"] for x in cells],
                                             weights=[x["n"] for x in cells])),
                    "total_net_r": float(sum(x["total_net_r"] for x in cells)),
                    "months_net_positive": int(sum(1 for x in cells if x["net"] > 0)),
                    "per_month": {m: x["net"] for m, x in zip(months, cells)},
                }
    out["LATTICE"] = lat
    ship = lat["gate_on|j0_target2R_SHIPPED|rank_off"]["net"]
    base = lat["gate_off|j0_target2R_SHIPPED|rank_off"]["net"]
    full = lat["gate_on|j5_stoponly|rank_on"]["net"]
    marg = {
        "shipped_stack": ship, "no_gate_baseline": base,
        "gate_alone": ship - base,
        "exit_alone_from_shipped": lat["gate_on|j0_stoponly|rank_off"]["net"] - ship,
        "entry_alone_from_shipped": lat["gate_on|j5_target2R|rank_off"]["net"] - ship,
        "rank_alone_from_shipped": lat["gate_on|j0_target2R_SHIPPED|rank_on"]["net"] - ship,
        "full_deployable_stack": full,
        "full_minus_shipped": full - ship,
    }
    marg["sum_of_standalone_three"] = (marg["exit_alone_from_shipped"]
                                       + marg["entry_alone_from_shipped"]
                                       + marg["rank_alone_from_shipped"])
    marg["double_count_factor"] = (marg["sum_of_standalone_three"]
                                   / max(abs(marg["full_minus_shipped"]), 1e-12))
    out["MARGINALS"] = marg
    Path(OUT / "D2_STACK_V1.json").write_text(json.dumps(out, indent=1, default=str))
    for k, v in sorted(lat.items()):
        print("%-46s n=%-6d gross %+.5f cost %.5f net %+.5f  months+ %d/8"
              % (k, v["n"], v["gross"], v["cost"], v["net"], v["months_net_positive"]))
    print("\n" + json.dumps(marg, indent=1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--in", dest="indir")
    ap.add_argument("--month")
    ap.add_argument("--npz")
    a = ap.parse_args()
    if a.build:
        build(a.indir, a.month, a.npz)
    else:
        price()


if __name__ == "__main__":
    main()
