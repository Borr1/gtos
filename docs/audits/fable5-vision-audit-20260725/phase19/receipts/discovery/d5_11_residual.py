"""d5-11 — the residual test.  Once the order geometry known AT T is removed, is the
confirm minute anything at all?

Population split by the DECISION ANCHOR mkt_r0 = s*(close of [T-1m,T) - e)/d, knowable at T:
  mkt_r0 > 0   the entry sits at price improvement -> a resting limit is physically reachable
  mkt_r0 == 0  the entry IS the market -> an at-market order, filled at T by construction
  mkt_r0 < 0   the entry sits BEYOND the market in the losing direction -> the estate's walk
               fills it at `e`, a price the market had already left (a fill it cannot have)
"""
import json, os, sys
import numpy as np
sys.path.insert(0, "/tmp/d5")
from d5_lib import dayblock_ci, cohens_d, auc

OUT = "/tmp/d5/out"
WINS = [w for w in ("2025-10", "2025-11", "2025-12", "2026-01", "2026-02", "2026-03",
                    "2026-04", "2026-05") if os.path.isfile("%s/D9_%s.npz" % (OUT, w))]
ACC = []
for wi, w in enumerate(WINS):
    z = np.load("%s/D9_%s.npz" % (OUT, w))
    D = {k: z[k] for k in z.files}
    D["day"] = D["dayi"] + 1000 * wi
    D["win"] = np.full(D["g0"].size, wi)
    ACC.append(D)
A = {k: np.concatenate([a[k] for a in ACC]) for k in ACC[0]}
N = A["g0"].size
g0, c0, mk, j0, gd, gm, gm0 = (A["g0"], A["c0"], A["mkt_r0"], A["j0"], A["gd"], A["gm"], A["gm0"])
n0 = g0 - A["cost0"]; nd = gd - A["costd"]; nm = gm - A["costm"]
day, win, r0 = A["day"], A["win"], A["r0"]
R = {"windows": WINS, "N": int(N)}

SEG = {"LIMIT_price_improvement_mkt_r0>0": mk > 0,
       "AT_MARKET_mkt_r0==0": mk == 0,
       "UNREACHABLE_mkt_r0<0": mk < 0}
R["segments"] = {}
for tag, m in SEG.items():
    res = r0[m]
    R["segments"][tag] = {
        "n": int(m.sum()), "share": float(m.mean()),
        "gross_as_walked": float(g0[m].mean()), "net_as_walked": float(n0[m].mean()),
        "total_gross_R": float(g0[m].sum()),
        "fill_rate": float((j0[m] >= 0).mean()),
        "prefilled_share_j0": float((j0[m] == 0).mean()),
        "share_c0<=-0.15": float((c0[m] <= -0.15).mean()),
        "gross_if_market_at_T": float(gm0[m].mean()),
        "exit_mix": {k: float((res == i).mean()) for i, k in enumerate(["target", "stop", "path_end", "no_fill"])},
        "median_mkt_r0": float(np.median(mk[m])),
    }

# ---- the residual: everything, restricted to the physically reachable limit rows
m = mk > 0
sub = {k: A[k][m] for k in ("g0", "c0", "j0", "gd", "gm", "r0", "day", "win", "cost0", "costd", "costm")}
sg, sc, sj = sub["g0"], sub["c0"], sub["j0"]
sn = sub["g0"] - sub["cost0"]; snd = sub["gd"] - sub["costd"]
resolved = np.isin(sub["r0"], [0, 1]); ist = sub["r0"] == 0
R["residual_separation_on_reachable_limits"] = {
    "n_resolved": int(resolved.sum()),
    "cohens_d_c0": cohens_d(sc[resolved & ist], sc[resolved & ~ist]),
    "auc_c0": auc(sc[resolved & ist], sc[resolved & ~ist]),
    "estate_ceiling": 0.152,
}
arms = {}
base_g = float(sg.mean()); base_n = float(sn.mean())
for th in (-0.30, -0.15, -0.05, 0.0):
    ad = sc <= th
    canc = ad & (sj > 0)
    a1 = np.where(ad, 0, sg); a2 = np.where(canc, 0, sg)
    a3 = np.where(~ad, sub["gd"], 0); a3n = np.where(~ad, snd, 0)
    arms["th=%.2f" % th] = {
        "n_adverse": int(ad.sum()), "adverse_share": float(ad.mean()),
        "adverse_gross": float(sg[ad].mean()) if ad.any() else None,
        "prefilled_share_of_adverse": float((sj[ad] == 0).mean()) if ad.any() else None,
        "ORACLE_refuse_delta_gross": float(a1.mean() - base_g),
        "ACHIEVABLE_cancel_delta_gross": float(a2.mean() - base_g),
        "DELAYED_placement_gross": float(a3.mean()), "DELAYED_placement_net": float(a3n.mean()),
        "DELAYED_delta_gross": float(a3.mean() - base_g),
        "DELAYED_delta_net": float(a3n.mean() - base_n),
        "DELAYED_delta_gross_ci": dayblock_ci(a3 - sg, sub["day"]),
        "per_window_DELAYED_delta_net": {w: float((a3n - sn)[sub["win"] == i].mean())
                                         for i, w in enumerate(WINS)},
    }
R["reachable_limits_baseline"] = {"gross": base_g, "net": base_n, "n": int(m.sum())}
R["reachable_limits_arms"] = arms

# ---- per-window headline table
R["per_window"] = {}
for i, w in enumerate(WINS):
    mw = win == i
    mm = mw & (mk > 0)
    R["per_window"][w] = {
        "n": int(mw.sum()),
        "gross_all": float(g0[mw].mean()), "net_all": float(n0[mw].mean()),
        "share_mkt_r0<0": float((mk[mw] < 0).mean()),
        "gross_excl_unreachable": float(g0[mw & (mk >= 0)].mean()),
        "net_excl_unreachable": float(n0[mw & (mk >= 0)].mean()),
        "share_c0<=-0.15": float((c0[mw] <= -0.15).mean()),
        "adverse_gross": float(g0[mw & (c0 <= -0.15)].mean()),
        "adverse_prefilled_share": float((j0[mw & (c0 <= -0.15)] == 0).mean()),
        "reachable_gross": float(g0[mm].mean()), "reachable_net": float(n0[mm].mean()),
    }
json.dump(R, open("%s/D5_11_RESIDUAL.json" % OUT, "w"), indent=1, default=float)
print(json.dumps(R["segments"], indent=1))
print(json.dumps(R["residual_separation_on_reachable_limits"], indent=1))
print("%-10s %8s %8s %8s %8s %9s %9s" % ("th", "n_adv", "advGr", "preFill", "ORACLE", "CANCEL", "DELAYdn"))
for k, v in arms.items():
    print("%-10s %8d %8.4f %8.4f %+8.5f %+9.5f %+9.5f"
          % (k, v["n_adverse"], v["adverse_gross"] or 0, v["prefilled_share_of_adverse"] or 0,
             v["ORACLE_refuse_delta_gross"], v["ACHIEVABLE_cancel_delta_gross"], v["DELAYED_delta_net"]))
