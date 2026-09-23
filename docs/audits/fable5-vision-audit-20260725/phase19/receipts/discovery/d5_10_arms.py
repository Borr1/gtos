"""d5-10 — the achievable-fill table.  Every arm priced PER OPPORTUNITY on the same rows.

An arm that refuses a candidate books exactly 0.0 for it, so all arms share one denominator
(the roster emission count) and are directly comparable.  Day-clustered 95 % intervals on the
PAIRED per-row difference against the baseline (the toll and the row set cancel exactly).
"""
import json, sys, glob, os
import numpy as np
sys.path.insert(0, "/tmp/d5")
from d5_lib import dayblock_ci

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
g0, c0, mk, j0 = A["g0"], A["c0"], A["mkt_r0"], A["j0"]
gd, jd, gm, gm0 = A["gd"], A["jd"], A["gm"], A["gm0"]
n0, nd = g0 - A["cost0"], gd - A["costd"]
nm, nm0 = gm - A["costm"], gm0 - A["costm0"]
day, win = A["day"], A["win"]
Z = np.zeros(N)

TH = -0.15
ARMS = {
    "A0_baseline_rest_limit_at_T": (g0, n0, "the shipped honest contract"),
    "A1_ORACLE_refuse_c0<=-0.15": (np.where(c0 <= TH, 0, g0), np.where(c0 <= TH, 0, n0),
                                   "UNACHIEVABLE ceiling: refuse on an observable that postdates the fill"),
    "A2_ACHIEVABLE_cancel_c0<=-0.15": (np.where((c0 <= TH) & (j0 > 0), 0, g0),
                                       np.where((c0 <= TH) & (j0 > 0), 0, n0),
                                       "cancel at T+1m only where the order is still unfilled"),
    "A3_delayed_placement_if_c0>-0.15": (np.where(c0 > TH, gd, 0), np.where(c0 > TH, nd, 0),
                                         "place nothing at T; place the same limit at T+1m if the confirm minute is clean"),
    "A3b_delayed_placement_unconditional": (gd, nd, "isolates the cost of waiting one minute"),
    "A4_market_at_T+1m_if_c0>-0.15": (np.where(c0 > TH, gm, 0), np.where(c0 > TH, nm, 0),
                                      "re-anchored market entry at the confirm close, same risk distance"),
    "A4b_market_at_T+1m_unconditional": (gm, nm, "re-anchor every row"),
    "A5_PRE_refuse_mkt_r0<=0_at_T": (np.where(mk > 0, g0, 0), np.where(mk > 0, n0, 0),
                                     "ACHIEVABLE AT T with no delay: place only orders sitting at price improvement"),
    "A6_market_at_T_unconditional": (gm0, nm0, "what the live engine does: market order at the decision instant"),
    "A7_market_at_T_if_mkt_r0<=0_else_limit": (np.where(mk > 0, g0, gm0), np.where(mk > 0, n0, nm0),
                                               "keep the limit where it is reachable, take the market where it is not"),
    "A8_A5_then_cancel_c0<=-0.15": (np.where(mk > 0, np.where((c0 <= TH) & (j0 > 0), 0, g0), 0),
                                    np.where(mk > 0, np.where((c0 <= TH) & (j0 > 0), 0, n0), 0),
                                    "both achievable filters together"),
}

R = {"windows": WINS, "N": int(N), "threshold": TH, "arms": {}}
base_g, base_n = g0, n0
for tag, (gv, nv, note) in ARMS.items():
    dg = gv - base_g
    dn = nv - base_n
    R["arms"][tag] = {
        "note": note,
        "pool_gross": float(gv.mean()), "pool_net": float(nv.mean()),
        "delta_gross": float(dg.mean()), "delta_net": float(dn.mean()),
        "delta_gross_ci95_dayclustered": dayblock_ci(dg, day),
        "delta_net_ci95_dayclustered": dayblock_ci(dn, day),
        "n_traded": int((gv != 0).sum()),
        "per_window_delta_net": {w: float(dn[win == i].mean()) for i, w in enumerate(WINS)},
        "per_window_pool_net": {w: float(nv[win == i].mean()) for i, w in enumerate(WINS)},
        "windows_improving_net": int(sum(1 for i in range(len(WINS)) if dn[win == i].mean() > 0)),
    }

# ---- the cost of waiting one minute, decomposed
lost = (j0 >= 0) & (jd < 0)
R["cost_of_waiting_one_minute"] = {
    "n_filled_at_T": int((j0 >= 0).sum()),
    "n_filled_if_placed_at_T+1m": int((jd >= 0).sum()),
    "n_fills_lost": int(lost.sum()),
    "share_of_fills_lost": float(lost.sum() / max((j0 >= 0).sum(), 1)),
    "mean_gross_of_the_lost_fills": float(g0[lost].mean()),
    "delta_gross_from_waiting": float((gd - g0).mean()),
    "n_fill_price_unchanged_j_shift": int(((j0 >= 0) & (jd >= 0)).sum()),
}

# ---- where the roster's negative gross actually lives
mkt_neg = mk < 0.0
R["gross_attribution"] = {
    "total_gross_R": float(g0.sum()),
    "rows_mkt_r0<0": int(mkt_neg.sum()),
    "share_of_rows": float(mkt_neg.mean()),
    "their_total_gross_R": float(g0[mkt_neg].sum()),
    "share_of_total_gross_R": float(g0[mkt_neg].sum() / g0.sum()) if g0.sum() else None,
    "their_mean_gross_as_walked": float(g0[mkt_neg].mean()),
    "their_mean_gross_if_market_at_T": float(gm0[mkt_neg].mean()),
    "rest_of_roster_mean_gross": float(g0[~mkt_neg].mean()),
    "rest_of_roster_mean_net": float(n0[~mkt_neg].mean()),
}

# ---- c0 threshold sweep on the ACHIEVABLE arms only
sweep = {}
for th in (-0.50, -0.30, -0.15, -0.05, 0.0, 0.10):
    a2 = np.where((c0 <= th) & (j0 > 0), 0, g0)
    a3 = np.where(c0 > th, gd, 0); a3n = np.where(c0 > th, nd, 0)
    a4 = np.where(c0 > th, gm, 0); a4n = np.where(c0 > th, nm, 0)
    sweep["%.2f" % th] = {
        "A2_cancel_delta_gross": float((a2 - g0).mean()),
        "A3_delayed_gross": float(a3.mean()), "A3_delayed_net": float(a3n.mean()),
        "A4_market_T1_gross": float(a4.mean()), "A4_market_T1_net": float(a4n.mean()),
        "n_refused": int((c0 <= th).sum()),
    }
R["achievable_threshold_sweep"] = sweep

json.dump(R, open("%s/D5_10_ARMS.json" % OUT, "w"), indent=1, default=float)
print("windows", WINS, "N", N)
print("%-42s %9s %9s %9s %9s %4s" % ("arm", "gross", "net", "dgross", "dnet", "w+"))
for tag, v in R["arms"].items():
    print("%-42s %9.5f %9.5f %+9.5f %+9.5f %4d"
          % (tag, v["pool_gross"], v["pool_net"], v["delta_gross"], v["delta_net"],
             v["windows_improving_net"]))
print(json.dumps(R["cost_of_waiting_one_minute"], indent=1))
print(json.dumps(R["gross_attribution"], indent=1))

# ---- side-aware fill arm (appended)
if "gs" in A:
    gs = A["gs"]; js = A["js"]
    ns = gs - np.where(js >= 0, A["cost0"], 0.0)
    dg = gs - base_g; dn = ns - base_n
    R["arms"]["A11_side_aware_fill_at_T"] = {
        "note": "a BUY above the market fills as a STOP (high>=e), not as a limit — what a broker does",
        "pool_gross": float(gs.mean()), "pool_net": float(ns.mean()),
        "delta_gross": float(dg.mean()), "delta_net": float(dn.mean()),
        "delta_gross_ci95_dayclustered": dayblock_ci(dg, day),
        "delta_net_ci95_dayclustered": dayblock_ci(dn, day),
        "n_traded": int((js >= 0).sum()),
        "per_window_delta_net": {w: float(dn[win == i].mean()) for i, w in enumerate(WINS)},
        "per_window_pool_net": {w: float(ns[win == i].mean()) for i, w in enumerate(WINS)},
        "windows_improving_net": int(sum(1 for i in range(len(WINS)) if dn[win == i].mean() > 0)),
    }
    mn = mk < 0
    R["side_aware_detail"] = {
        "unreachable_rows": int(mn.sum()),
        "estate_convention_fill_rate": float((j0[mn] >= 0).mean()),
        "side_aware_fill_rate": float((js[mn] >= 0).mean()),
        "estate_convention_gross": float(g0[mn].mean()),
        "side_aware_gross": float(gs[mn].mean()),
        "side_aware_gross_on_filled_only": float(gs[mn][js[mn] >= 0].mean()) if (js[mn] >= 0).any() else None,
        "market_at_T_gross": float(gm0[mn].mean()),
        "whole_roster_gross_side_aware": float(gs.mean()),
        "whole_roster_net_side_aware": float(ns.mean()),
        "per_window_gross_side_aware": {w: float(gs[win == i].mean()) for i, w in enumerate(WINS)},
        "per_window_gross_estate": {w: float(g0[win == i].mean()) for i, w in enumerate(WINS)},
    }
    # does the confirm minute add anything on top of the side-aware contract?
    for th in (-0.15, -0.05, 0.0):
        adv = A["c0"] <= th
        canc = adv & (js > 0)
        R.setdefault("confirm_on_side_aware", {})["th=%.2f" % th] = {
            "n_adverse": int(adv.sum()),
            "adverse_gross_side_aware": float(gs[adv].mean()),
            "prefilled_share": float((js[adv] == 0).mean()),
            "n_cancellable": int(canc.sum()),
            "ORACLE_delta_gross": float(np.where(adv, 0, gs).mean() - gs.mean()),
            "ACHIEVABLE_cancel_delta_gross": float(np.where(canc, 0, gs).mean() - gs.mean()),
        }
    json.dump(R, open("%s/D5_10_ARMS.json" % OUT, "w"), indent=1, default=float)
    print("A11_side_aware_fill_at_T  gross %.5f net %.5f  dgross %+.5f dnet %+.5f  w+ %d"
          % (R["arms"]["A11_side_aware_fill_at_T"]["pool_gross"],
             R["arms"]["A11_side_aware_fill_at_T"]["pool_net"],
             R["arms"]["A11_side_aware_fill_at_T"]["delta_gross"],
             R["arms"]["A11_side_aware_fill_at_T"]["delta_net"],
             R["arms"]["A11_side_aware_fill_at_T"]["windows_improving_net"]))
    print(json.dumps(R["side_aware_detail"], indent=1))
    print(json.dumps(R["confirm_on_side_aware"], indent=1))
