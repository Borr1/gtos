"""d5-13 — the final tables for the receipt.  Pooled + per window, nothing sampled."""
import json, os, sys
import numpy as np
sys.path.insert(0, "/tmp/d5")
from d5_lib import cohens_d, auc, dayblock_ci

OUT = "/tmp/d5/out"
ALL = ("2025-10", "2025-11", "2025-12", "2026-01", "2026-02", "2026-03", "2026-04", "2026-05")
WINS = [w for w in ALL if os.path.isfile("%s/D9_%s.npz" % (OUT, w))]
ACC = []
for wi, w in enumerate(WINS):
    z = np.load("%s/D9_%s.npz" % (OUT, w))
    D = {k: z[k] for k in z.files}
    D["win"] = np.full(D["g0"].size, wi); D["day"] = D["dayi"] + 1000 * wi
    ACC.append(D)
A = {k: np.concatenate([a[k] for a in ACC]) for k in ACC[0]}
N = A["g0"].size
g0, gs, gd, gm, gm0 = A["g0"], A["gs"], A["gd"], A["gm"], A["gm0"]
j0, js, jd = A["j0"], A["js"], A["jd"]
c0, mk, cost, day, win = A["c0"], A["mkt_r0"], A["cost0"], A["day"], A["win"]
r0, rs = A["r0"], A["rs"]
n0 = g0 - np.where(j0 >= 0, cost, 0.0)
ns = gs - np.where(js >= 0, cost, 0.0)

R = {"windows": WINS, "N_emissions": int(N)}


def econ(gv, jv, tag):
    f = jv >= 0
    nv = gv - np.where(f, cost, 0.0)
    win_r = gv[f] > 0
    wins = gv[f][gv[f] > 0]; loss = gv[f][gv[f] <= 0]
    payoff = (wins.mean() / -loss.mean()) if loss.size and wins.size else None
    be = 1 / (1 + payoff) if payoff else None
    return {"tag": tag, "n_fills": int(f.sum()), "fill_rate": float(f.mean()),
            "gross_per_fill": float(gv[f].mean()), "toll_per_fill": float(cost[f].mean()),
            "net_per_fill": float(nv[f].mean()),
            "gross_per_opportunity": float(gv.mean()), "net_per_opportunity": float(nv.mean()),
            "win_rate": float(win_r.mean()), "payoff": payoff, "breakeven_wr": be,
            "gap_pp": float(win_r.mean() - be) * 100 if be else None,
            "ci_net_per_opportunity": dayblock_ci(nv, day)}


R["contracts"] = {
    "ESTATE_convention_limit_from_T": econ(g0, j0, "a BUY always fills on low<=e, even above market"),
    "SIDE_AWARE_from_T": econ(gs, js, "touch side chosen by which side of e the market is on at T"),
    "DELAYED_placement_T+1m": econ(gd, jd, "same limit, placed one minute later"),
    "MARKET_at_T": econ(gm0, np.zeros(N, int), "market order at the decision instant"),
    "MARKET_at_T+1m": econ(gm, np.zeros(N, int), "market order one minute later"),
}

# ---- the separator, three label sets, per window
def sep(feat, reason, ok, m):
    res = np.isin(reason, [0, 1]) & m & ok
    t = res & (reason == 0); s = res & (reason == 1)
    x, y = feat[t], feat[s]
    return {"n_target": int(t.sum()), "n_stop": int(s.sum()),
            "d": cohens_d(x, y), "auc": auc(x, y)}


ones = np.ones(N, bool)
R["separator"] = {"pooled": {}, "per_window": {}}
LSETS = {
    "ESTATE_labels_all_resolved": (r0, ones),
    "SIDE_AWARE_labels_all_resolved": (rs, ones),
    "SIDE_AWARE_labels_PENDING_only(actionable)": (rs, js > 0),
}
for tag, (reason, ok) in LSETS.items():
    R["separator"]["pooled"][tag] = sep(c0, reason, ok, ones)
for i, w in enumerate(WINS):
    m = win == i
    R["separator"]["per_window"][w] = {tag: sep(c0, reason, ok, m) for tag, (reason, ok) in LSETS.items()}

# ---- fill-timing partition of the adverse cohort, per window and pooled
R["actionability"] = {"pooled": {}, "per_window": {}}
for th in (-0.30, -0.15, -0.05, 0.0):
    ad = c0 <= th
    for contract, jv, gv in (("ESTATE", j0, g0), ("SIDE_AWARE", js, gs)):
        key = "%s@c0<=%.2f" % (contract, th)
        tot = float(gv[ad].sum())
        canc = ad & (jv > 0)
        R["actionability"]["pooled"][key] = {
            "n_adverse": int(ad.sum()), "adverse_gross": float(gv[ad].mean()),
            "share_already_filled_at_T+1m": float((jv[ad] == 0).mean()),
            "share_never_filled": float((jv[ad] < 0).mean()),
            "n_cancellable": int(canc.sum()),
            "pct_of_adverse_R_a_cancel_can_avoid": float(gv[canc].sum() / tot) if tot else None,
            "ORACLE_delta_gross_per_opportunity": float(np.where(ad, 0, gv).mean() - gv.mean()),
            "ACHIEVABLE_cancel_delta_gross_per_opportunity": float(np.where(canc, 0, gv).mean() - gv.mean()),
        }
for i, w in enumerate(WINS):
    m = win == i
    ad = (c0 <= -0.15) & m
    R["actionability"]["per_window"][w] = {
        "n_adverse": int(ad.sum()),
        "ESTATE_adverse_gross": float(g0[ad].mean()),
        "ESTATE_share_already_filled": float((j0[ad] == 0).mean()),
        "ESTATE_cancel_delta": float(np.where(ad & (j0 > 0), 0, g0)[m].mean() - g0[m].mean()),
        "SIDE_AWARE_adverse_gross": float(gs[ad].mean()),
        "SIDE_AWARE_share_already_filled": float((js[ad] == 0).mean()),
        "SIDE_AWARE_cancel_delta": float(np.where(ad & (js > 0), 0, gs)[m].mean() - gs[m].mean()),
    }

# ---- segments by the decision anchor
R["segments"] = {}
for tag, m in (("LIMIT_mkt_r0>0", mk > 0), ("AT_MARKET_mkt_r0==0", mk == 0),
               ("UNREACHABLE_mkt_r0<0", mk < 0)):
    R["segments"][tag] = {
        "n": int(m.sum()), "share": float(m.mean()),
        "share_c0<=-0.15": float((c0[m] <= -0.15).mean()),
        "ESTATE_fill_rate": float((j0[m] >= 0).mean()), "ESTATE_gross_per_opp": float(g0[m].mean()),
        "SIDE_AWARE_fill_rate": float((js[m] >= 0).mean()), "SIDE_AWARE_gross_per_opp": float(gs[m].mean()),
        "MARKET_at_T_gross_per_opp": float(gm0[m].mean()),
        "ESTATE_total_R": float(g0[m].sum()), "SIDE_AWARE_total_R": float(gs[m].sum()),
        "ESTATE_stop_share": float((r0[m] == 1).mean()), "SIDE_AWARE_stop_share": float((rs[m] == 1).mean()),
    }

# ---- achievable arms, pooled + per window
TH = -0.15
nd = gd - np.where(jd >= 0, cost, 0.0)
ARMS = {
    "A0_estate_limit_at_T": (g0, n0),
    "A1_ORACLE_refuse_c0<=-0.15": (np.where(c0 <= TH, 0, g0), np.where(c0 <= TH, 0, n0)),
    "A2_ACHIEVABLE_cancel_at_T+1m": (np.where((c0 <= TH) & (j0 > 0), 0, g0),
                                     np.where((c0 <= TH) & (j0 > 0), 0, n0)),
    "A3_delayed_placement_if_c0>-0.15": (np.where(c0 > TH, gd, 0), np.where(c0 > TH, nd, 0)),
    "A3b_delayed_placement_uncond": (gd, nd),
    "A5_PRE_refuse_mkt_r0<=0_at_T": (np.where(mk > 0, g0, 0), np.where(mk > 0, n0, 0)),
    "A11_side_aware_fill_at_T": (gs, ns),
    "A11b_side_aware_then_cancel_c0<=-0.15": (np.where((c0 <= TH) & (js > 0), 0, gs),
                                              np.where((c0 <= TH) & (js > 0), 0, ns)),
    "A6_market_at_T": (gm0, gm0 - A["costm0"]),
}
R["arms"] = {}
for tag, (gv, nv) in ARMS.items():
    R["arms"][tag] = {
        "gross_per_opportunity": float(gv.mean()), "net_per_opportunity": float(nv.mean()),
        "delta_gross": float((gv - g0).mean()), "delta_net": float((nv - n0).mean()),
        "delta_net_ci95": dayblock_ci(nv - n0, day),
        "per_window_net": {w: float(nv[win == i].mean()) for i, w in enumerate(WINS)},
        "windows_net_improving": int(sum(1 for i in range(len(WINS)) if (nv - n0)[win == i].mean() > 0)),
    }

# ---- cost of waiting
lost = (j0 >= 0) & (jd < 0)
R["cost_of_waiting_one_minute"] = {
    "fills_at_T": int((j0 >= 0).sum()), "fills_at_T+1m": int((jd >= 0).sum()),
    "fills_lost": int(lost.sum()), "share_lost": float(lost.sum() / max((j0 >= 0).sum(), 1)),
    "mean_gross_of_lost_fills": float(g0[lost].mean()),
    "delta_gross_per_opportunity": float((gd - g0).mean()),
}
json.dump(R, open("%s/D5_13_FINAL.json" % OUT, "w"), indent=1, default=float)
print("WINDOWS", WINS, "N", N)
for k, v in R["contracts"].items():
    print("%-28s fills %7d (%.3f) gross/fill %+8.5f toll %.5f net/opp %+8.5f wr %.4f be %.4f"
          % (k, v["n_fills"], v["fill_rate"], v["gross_per_fill"], v["toll_per_fill"],
             v["net_per_opportunity"], v["win_rate"], v["breakeven_wr"] or 0))
print()
for k, v in R["separator"]["pooled"].items():
    print("%-46s d=%+.4f auc=%.4f nT=%d nS=%d" % (k, v["d"], v["auc"], v["n_target"], v["n_stop"]))
print()
for k, v in R["arms"].items():
    print("%-42s gross %+8.5f net %+8.5f  dnet %+8.5f  w+ %d/%d"
          % (k, v["gross_per_opportunity"], v["net_per_opportunity"], v["delta_net"],
             v["windows_net_improving"], len(WINS)))
