#!/usr/bin/env python3
"""d7 stage 2 — the frontiers that convert a verdict into a decision.

(A) conditioner requirement: what discriminative power an ex-ante rule must have,
    at each selection rate, for the book to reach net >= 0 -- and what is attainable.
(B) the cheapest-toll question: ex-ante cost sorting, out of sample.
(C) persistence: cost-rank vs edge-rank across a train/test month split.
(D) the JOINT isoquant (cost cut x win-rate lift), because levers must be priced together.
(E) resolution: how many trades / how many years to tell whether it already pays.
(F) exit mix + loser composition + the loser-cut isoquant.
"""
import json, math, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = "/tmp/d7"
A = np.load(os.path.join(OUT, "d7_arrays.npz"))
NM = json.load(open(os.path.join(OUT, "d7_names.json")))
SYMS = {int(k): v for k, v in NM["syms"].items()}
FAMS = {int(k): v for k, v in NM["fams"].items()}
REAS = {int(k): v for k, v in NM["reasons"].items()}
WINDOWS = ["2025-10", "2025-11", "2025-12", "2026-01", "2026-02", "2026-03", "2026-04", "2026-05"]

g, c, d_bps = A["g"], A["c"], A["d_bps"]
sym, fam, win, reason = A["sym"], A["fam"], A["win"], A["reason"]
clean, atmkt, filled = A["clean"], A["atmkt"], A["filled"]

R = {"schema": "gtos.wave19.d7.stage2.v1"}

# ============================================================ population
M = clean
gm, cm, dm = g[M], c[M], d_bps[M]
netm = gm - cm
symm, famm, winm, reasm = sym[M], fam[M], win[M], reason[M]
n = len(gm)
G, C = float(gm.mean()), float(cm.mean())
p = float((gm > 0).mean())
a = float(gm[gm > 0].mean()); b = float((-gm[gm <= 0]).mean())
R["population"] = {"tag": "CLEAN roster, 8 windows, day-restricted", "n": int(n),
                   "gross": G, "cost": C, "net": G - C, "p": p, "a": a, "b": b}

# ============================================================ (F) exit mix
mix = {}
for i, nm in REAS.items():
    k = reasm == i
    if k.sum() == 0:
        continue
    mix[nm] = {"n": int(k.sum()), "share": float(k.mean()),
               "gross": float(gm[k].mean()), "cost": float(cm[k].mean())}
R["exit_mix_clean"] = mix
los = gm <= 0
R["loser_composition"] = {
    "n_losers": int(los.sum()), "share": float(los.mean()), "mean_b": b,
    "share_of_losers_at_exactly_-1R": float((gm[los] <= -0.999).mean()),
    "share_of_losers_between_-1_and_0": float(((gm[los] > -0.999) & (gm[los] <= 0)).mean()),
    "mean_b_of_hard_stops": float((-gm[los][gm[los] <= -0.999]).mean()),
    "mean_b_of_soft_losers": float((-gm[los][gm[los] > -0.999]).mean()),
}

# ============================================================ (A) conditioner requirement
rng = np.random.default_rng(20260806)
ranks = np.empty(n); order = np.argsort(netm, kind="stable"); ranks[order] = np.arange(n)
z_true = (ranks + 0.5) / n
from math import erf, sqrt
def probit(u):
    # inverse normal CDF, vectorised (Acklam)
    a_ = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
          1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b_ = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
          6.680131188771972e+01, -1.328068155288572e+01]
    c_ = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
          -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d_ = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
          3.754408661907416e+00]
    u = np.asarray(u, dtype=float)
    out = np.empty_like(u)
    lo, hi = u < 0.02425, u > 1 - 0.02425
    mid = ~(lo | hi)
    q = np.sqrt(-2 * np.log(u[lo]))
    out[lo] = (((((c_[0]*q+c_[1])*q+c_[2])*q+c_[3])*q+c_[4])*q+c_[5]) / ((((d_[0]*q+d_[1])*q+d_[2])*q+d_[3])*q+1)
    q = np.sqrt(-2 * np.log(1 - u[hi]))
    out[hi] = -(((((c_[0]*q+c_[1])*q+c_[2])*q+c_[3])*q+c_[4])*q+c_[5]) / ((((d_[0]*q+d_[1])*q+d_[2])*q+d_[3])*q+1)
    q = u[mid] - 0.5; r = q*q
    out[mid] = (((((a_[0]*r+a_[1])*r+a_[2])*r+a_[3])*r+a_[4])*r+a_[5])*q / (((((b_[0]*r+b_[1])*r+b_[2])*r+b_[3])*r+b_[4])*r+1)
    return out

zt = probit(z_true)                      # normal score of the true net rank
noise_base = rng.standard_normal(n)
pos = gm > 0                             # "winner" label for AUC reporting


def auc_of(score):
    o = np.argsort(score, kind="stable")
    rk = np.empty(n); rk[o] = np.arange(1, n + 1)
    npos = int(pos.sum()); nneg = n - npos
    return float((rk[pos].sum() - npos * (npos + 1) / 2.0) / (npos * nneg))


def mean_net_at(rho, f, reps=3):
    """mean net of the top-f fraction ranked by a score with rank-corr ~rho to true net."""
    k = max(1, int(round(f * n)))
    vals = []
    for r_ in range(reps):
        nz = noise_base if r_ == 0 else rng.standard_normal(n)
        s = rho * zt + math.sqrt(max(0.0, 1 - rho * rho)) * nz
        idx = np.argpartition(-s, k - 1)[:k]
        vals.append(float(netm[idx].mean()))
    return float(np.mean(vals))


rates = [0.50, 0.25, 0.10, 0.05, 0.02, 0.01, 0.005, 0.002, 0.001, 0.000484]
cond = []
for f in rates:
    k = max(1, int(round(f * n)))
    oracle = float(np.sort(netm)[-k:].mean())
    row = {"selection_rate": f, "n_selected": k, "oracle_net": oracle}
    if oracle <= 0:
        row["required_rho"] = None
        row["note"] = "even a PERFECT ranker cannot reach net>=0 at this rate"
    else:
        lo, hi = 0.0, 1.0
        if mean_net_at(1.0, f) < 0:
            row["required_rho"] = None
        else:
            for _ in range(24):
                mid = (lo + hi) / 2
                if mean_net_at(mid, f) >= 0:
                    hi = mid
                else:
                    lo = mid
            rho = hi
            row["required_rho"] = rho
            s = rho * zt + math.sqrt(max(0.0, 1 - rho * rho)) * noise_base
            row["required_auc_winner_vs_loser"] = auc_of(s)
            row["required_cohens_d"] = float(math.sqrt(2) * probit(np.array([row["required_auc_winner_vs_loser"]]))[0])
            row["net_at_required"] = mean_net_at(rho, f)
    cond.append(row)
R["conditioner_requirement"] = cond
R["conditioner_note"] = ("score = rho*probit(rank(true net)) + sqrt(1-rho^2)*N(0,1); "
                         "required_auc is that score's own winner-vs-loser AUC on the same rows; "
                         "3 noise draws per evaluation, seed 20260806.")

# attainable AUC from the system's OWN ex-ante observables, strictly out of sample
TR = np.isin(winm, [0, 1, 2, 3])     # Oct-Jan
TE = ~TR                             # Feb-May
att = {}
# a) risk distance alone
att["d_bps_raw"] = {"test_auc_winner": None}
o = np.argsort(dm[TE], kind="stable"); rk = np.empty(TE.sum()); rk[o] = np.arange(1, TE.sum() + 1)
pt = pos[TE]; npos = int(pt.sum()); nneg = int(TE.sum()) - npos
att["d_bps_raw"]["test_auc_winner"] = float((rk[pt].sum() - npos*(npos+1)/2.0)/(npos*nneg))
# b) train-fitted (sym,fam) mean net -> test score
key_tr = symm[TR].astype(np.int32) * 100 + famm[TR]
key_te = symm[TE].astype(np.int32) * 100 + famm[TE]
tab = {}
for kk in np.unique(key_tr):
    m = key_tr == kk
    if m.sum() >= 100:
        tab[int(kk)] = float((gm[TR][m] - cm[TR][m]).mean())
gl = float((gm[TR] - cm[TR]).mean())
score_te = np.array([tab.get(int(k_), gl) for k_ in key_te])
o = np.argsort(score_te, kind="stable"); rk = np.empty(len(score_te)); rk[o] = np.arange(1, len(score_te) + 1)
att["symfam_trainfit_net"] = {"test_auc_winner": float((rk[pt].sum() - npos*(npos+1)/2.0)/(npos*nneg)),
                              "cells": len(tab)}
# c) train-fitted (sym,fam) mean GROSS (edge only, no cost) -> test
tabg = {}
for kk in np.unique(key_tr):
    m = key_tr == kk
    if m.sum() >= 100:
        tabg[int(kk)] = float(gm[TR][m].mean())
ggl = float(gm[TR].mean())
sg = np.array([tabg.get(int(k_), ggl) for k_ in key_te])
o = np.argsort(sg, kind="stable"); rk = np.empty(len(sg)); rk[o] = np.arange(1, len(sg) + 1)
att["symfam_trainfit_gross"] = {"test_auc_winner": float((rk[pt].sum() - npos*(npos+1)/2.0)/(npos*nneg))}
for k_, v in att.items():
    v["cohens_d_equiv"] = float(math.sqrt(2) * probit(np.array([v["test_auc_winner"]]))[0])
R["attainable_auc_out_of_sample"] = att

# ============================================================ (B) cheapest-toll frontier
cost_price_bps = cm * dm            # the toll in price terms (bps), ~ a fee schedule
R["toll_dispersion"] = {}
for tag, keyarr, names in (("family", famm, FAMS), ("symbol", symm, SYMS)):
    rows = {}
    for i, nm in names.items():
        m = keyarr == i
        if m.sum() < 200:
            continue
        rows[nm] = {"n": int(m.sum()), "toll_R": float(cm[m].mean()),
                    "toll_price_bps": float(cost_price_bps[m].mean()),
                    "median_d_bps": float(np.median(dm[m])),
                    "gross": float(gm[m].mean()), "net": float(netm[m].mean()),
                    "win_rate": float((gm[m] > 0).mean())}
    vals = [v["toll_R"] for v in rows.values()]
    R["toll_dispersion"][tag] = {"cells": rows, "min": min(vals), "max": max(vals),
                                 "dispersion_x": max(vals) / min(vals)}

# ex-ante cost model: per-symbol median price-toll fitted on TRAIN, applied on TEST
med_tr = {}
for i in np.unique(symm[TR]):
    m = symm[TR] == i
    med_tr[int(i)] = float(np.median(cost_price_bps[TR][m]))
glob_med = float(np.median(cost_price_bps[TR]))
pred_te = np.array([med_tr.get(int(s_), glob_med) for s_ in symm[TE]]) / dm[TE]
gte, cte, nte = gm[TE], cm[TE], netm[TE]
front = []
order_te = np.argsort(pred_te, kind="stable")
NT = len(order_te)
for f in [1.0, 0.5, 0.25, 0.10, 0.05, 0.02, 0.01, 0.005]:
    k = max(1, int(round(f * NT)))
    idx = order_te[:k]
    gg = float(gte[idx].mean()); cc = float(cte[idx].mean())
    ww = float((gte[idx] > 0).mean())
    wl = gte[idx] > 0
    aa = float(gte[idx][wl].mean()) if wl.sum() else 0.0
    bb = float((-gte[idx][~wl]).mean()) if (~wl).sum() else 0.0
    preq = (bb + cc) / (aa + bb) if (aa + bb) > 0 else float("nan")
    front.append({"retain": f, "n": k, "toll_R": cc, "gross": gg, "net": gg - cc,
                  "win_rate": ww, "required_win_rate_for_net0": preq,
                  "gap_pp": (ww - preq) * 100.0,
                  "median_d_bps": float(np.median(dm[TE][idx])),
                  "toll_price_bps": float(cost_price_bps[TE][idx].mean()),
                  "edge_needed_R_per_trade": cc, "edge_present_R_per_trade": gg,
                  "shortfall_R": cc - gg})
R["cheapest_toll_frontier_oos"] = {"train": "2025-10..2026-01", "test": "2026-02..2026-05",
                                   "predictor": "per-symbol TRAIN median price-toll (bps) / this row's own risk distance (bps)",
                                   "rows": front}

# same frontier but sorting on REALISED cost (an upper bound on any ex-ante cost rule)
order_or = np.argsort(cte, kind="stable")
front_or = []
for f in [0.5, 0.25, 0.10, 0.05, 0.02, 0.01]:
    k = max(1, int(round(f * NT)))
    idx = order_or[:k]
    front_or.append({"retain": f, "n": k, "toll_R": float(cte[idx].mean()),
                     "gross": float(gte[idx].mean()), "net": float(nte[idx].mean())})
R["cheapest_toll_frontier_oracle_cost"] = front_or

# ============================================================ (C) persistence
def spearman(x, y):
    rx = np.argsort(np.argsort(x)).astype(float); ry = np.argsort(np.argsort(y)).astype(float)
    rx -= rx.mean(); ry -= ry.mean()
    return float((rx * ry).sum() / math.sqrt((rx * rx).sum() * (ry * ry).sum()))

pers = {}
for tag, keyarr, names in (("symbol", symm, SYMS), ("family", famm, FAMS)):
    ks, ct, cte_, gt, gte_ = [], [], [], [], []
    for i in names:
        m1 = (keyarr == i) & TR; m2 = (keyarr == i) & TE
        if m1.sum() < 200 or m2.sum() < 200:
            continue
        ks.append(names[i]); ct.append(cm[m1].mean()); cte_.append(cm[m2].mean())
        gt.append(gm[m1].mean()); gte_.append(gm[m2].mean())
    pers[tag] = {"cells": len(ks),
                 "cost_rank_spearman_train_test": spearman(np.array(ct), np.array(cte_)),
                 "gross_rank_spearman_train_test": spearman(np.array(gt), np.array(gte_)),
                 "names": ks}
R["persistence_train_test"] = pers

# realised value of acting on the train-fitted edge ranking, out of sample
picks = {}
for tag, keyarr, names in (("symbol", symm, SYMS), ("symfam", symm.astype(np.int32)*100+famm, None)):
    kt = keyarr[TR] if tag == "symbol" else keyarr[TR]
    ke = keyarr[TE] if tag == "symbol" else keyarr[TE]
    tabg2, tabn2 = {}, {}
    for kk in np.unique(kt):
        m = kt == kk
        if m.sum() >= 200:
            tabg2[int(kk)] = float(gm[TR][m].mean()); tabn2[int(kk)] = float(netm[TR][m].mean())
    good_g = {k_ for k_, v in tabg2.items() if v > 0}
    good_n = {k_ for k_, v in tabn2.items() if v > max(-0.15, np.percentile(list(tabn2.values()), 25))}
    mg = np.array([int(k_) in good_g for k_ in ke])
    picks[tag] = {
        "cells_fitted": len(tabg2),
        "cells_with_positive_train_gross": len(good_g),
        "test_n": int(mg.sum()),
        "test_gross_of_train_positive_cells": float(gte[mg].mean()) if mg.sum() else None,
        "test_gross_all": float(gte.mean()),
        "test_win_rate_of_train_positive_cells": float((gte[mg] > 0).mean()) if mg.sum() else None,
        "test_win_rate_all": float((gte > 0).mean()),
        "oos_win_rate_lift_pp": (float((gte[mg] > 0).mean()) - float((gte > 0).mean())) * 100.0 if mg.sum() else None,
        "oos_gross_lift_R": (float(gte[mg].mean()) - float(gte.mean())) if mg.sum() else None,
    }
R["oos_edge_selection"] = picks

# ============================================================ (D) joint isoquant
iso = []
for kappa in [0.0, 0.10, 0.25, 0.50, 0.75, 0.90, 1.00]:
    Ck = C * (1 - kappa)
    p_req = (b + Ck) / (a + b)
    iso.append({"cost_cut_frac": kappa, "toll_after": Ck,
                "required_win_rate": p_req, "current_win_rate": p,
                "required_delta_pp": (p_req - p) * 100.0,
                "feasible": p_req <= 1.0})
R["joint_isoquant_cost_x_winrate"] = iso

# loser-cut isoquant: for a target mean loser b*, how much win rate may be sacrificed?
iso2 = []
for bstar in [0.90105, 0.80, 0.70, 0.60, 0.50, 0.426, 0.40, 0.30, 0.20, 0.10, 0.0]:
    # net(p', b*) = p'*a - (1-p')*b* - C = 0  ->  p' = (b*+C)/(a+b*)
    p_req = (bstar + C) / (a + bstar)
    iso2.append({"loser_mean_b": bstar, "cut_vs_today_pct": (1 - bstar / b) * 100.0,
                 "required_win_rate": p_req, "delta_pp_vs_today": (p_req - p) * 100.0,
                 "win_rate_headroom_pp": (p - p_req) * 100.0})
R["joint_isoquant_losercut_x_winrate"] = iso2

# ============================================================ (E) resolution / power
def resolution(nm_, sd, deficit, per_month):
    n_eq = (1.96 * sd / deficit) ** 2
    return {"cohort": nm_, "sd_net": sd, "deficit": deficit,
            "n_trades_for_ci95_halfwidth_eq_deficit": n_eq,
            "n_trades_for_ci95_halfwidth_eq_half_deficit": (1.96 * sd / (deficit / 2)) ** 2,
            "trades_per_month": per_month,
            "months_to_resolve": n_eq / per_month if per_month else None,
            "years_to_resolve": n_eq / per_month / 12.0 if per_month else None}

R["resolution"] = {}
taken = {"n": 464, "gross": 0.055045276646551726, "cost": 0.07436622613154095,
         "net": -0.01932094948275863, "net_sd": 1.031561497474603}
R["taken_set"] = taken
R["resolution"]["TAKEN"] = resolution("TAKEN (the trades the system actually made)",
                                      taken["net_sd"], taken["cost"] - taken["gross"], 507 / 8.0)
sdc = float(netm.std(ddof=1))
R["resolution"]["CLEAN"] = resolution("CLEAN roster", sdc, C - G, n / 8.0 / 1.0)

# ============================================================ account terms
R["account_terms"] = {
    "risk_unit_pct_of_account": 0.1,
    "taken_trades_per_month": 507 / 8.0,
    "taken_net_pct_per_month": taken["net"] * 0.1 * (507 / 8.0),
    "taken_net_pct_8_months": taken["net"] * 0.1 * 507,
    "r_per_trade_needed_for_8pct_in_60_trading_days": None,
}
# what R/trade at the measured cadence reaches an 8% phase-1 target in 3 / 6 / 12 months
for months in (3, 6, 12):
    R["account_terms"][f"r_per_trade_needed_for_8pct_in_{months}m"] = 8.0 / (0.1 * (507 / 8.0) * months)

json.dump(R, open(os.path.join(OUT, "D7_STAGE2.json"), "w"), indent=1, default=float)
print("wrote D7_STAGE2.json")
for row in cond:
    print(row.get("selection_rate"), "oracle", round(row["oracle_net"], 4),
          "rho*", row.get("required_rho"), "auc*", row.get("required_auc_winner_vs_loser"))
print("attainable:", json.dumps(att, indent=0))
print("frontier:", json.dumps(front[:8], indent=0)[:1200])
