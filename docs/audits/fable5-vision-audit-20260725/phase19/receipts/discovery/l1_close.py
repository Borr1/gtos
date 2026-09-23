#!/usr/bin/env python3
"""l1 pass 8 — close the lane.

(1) TRAIN/TEST the path-dependent variants (trail / BE / partial / time stop) exactly as
    the fixed cells were tested, so "a trail beats the best fixed cell" is a tested claim.
(2) Diagnose WHY the families with the best path geometry still lose: the R-denominated
    cost is a function of how tight the stop was set, not of the path.
(3) The composed best policy and its net.
"""
from __future__ import annotations
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import w0_ws  # noqa
from l1_lib import load, mean, q, stats, cell, pop, TOUCH, FAV, ADV, FI, AI  # noqa
from l1_variants import walk, build_variants  # noqa

OUT = os.path.join(HERE, "l1_CLOSE_V1.json")
N_ORIG = 27658


def corrected(r):
    return (r["spread_r"] or 0.0) / 7.3 + (r["commission_r"] or 0.0) + (r["slip_r"] or 0.0) + (r["swap_r"] or 0.0)


def main():
    meta = {}
    for r in load(TOUCH):
        r["_day"] = int(r["decision_time_utc"][8:10])
        meta[(r["candidate_id"], r["decision_time_utc"])] = r
    V = build_variants()
    names = list(V)
    # accumulate per variant x split x population
    acc = {}
    for nm in names:
        acc[nm] = {"TR": [0.0, 0], "TE": [0.0, 0], "TE_nm": [0.0, 0], "ALLTAK": [0.0, 0],
                   "SDE": [0.0, 0], "RESTLONG": [0.0, 0]}
    for rp in w0_ws.iter_rpaths():
        k = (rp["candidate_id"], rp["decision_time_utc"])
        m = meta.get(k)
        if m is None or m["born"] == "born_past_stop":
            continue
        st = m["s_real"]
        if st is None:
            continue
        fav, adv, cls = rp["fav"], rp["adv"], rp["cls"]
        tr = m["_day"] <= 15
        nm_ok = m["born"] != "born_marketable"
        sde = m["family"] == "structural_distance_extreme"
        rl = m["born"] == "born_resting" and m["side"] == "LONG"
        for nm in names:
            r, why, ib = walk(fav, adv, cls, st, **V[nm])
            a = acc[nm]
            a["ALLTAK"][0] += r; a["ALLTAK"][1] += 1
            if tr:
                a["TR"][0] += r; a["TR"][1] += 1
            else:
                a["TE"][0] += r; a["TE"][1] += 1
                if nm_ok:
                    a["TE_nm"][0] += r; a["TE_nm"][1] += 1
            if sde:
                a["SDE"][0] += r; a["SDE"][1] += 1
            if rl:
                a["RESTLONG"][0] += r; a["RESTLONG"][1] += 1
    tab = {}
    for nm in names:
        a = acc[nm]
        tab[nm] = {p: (round(v[0] / v[1], 6) if v[1] else None) for p, v in a.items()}
        tab[nm]["n"] = {p: v[1] for p, v in a.items()}
    best_tr = max((nm for nm in names), key=lambda nm: tab[nm]["TR"])
    res = {"VARIANT_SPLIT": tab,
           "VARIANT_BEST_ON_TRAIN": {"variant": best_tr, "spec": V[best_tr],
                                     "train_R": tab[best_tr]["TR"], "test_R": tab[best_tr]["TE"],
                                     "shrinkage": round(tab[best_tr]["TE"] - tab[best_tr]["TR"], 6)},
           "VARIANT_BEST_ON_TEST": None}
    best_te = max((nm for nm in names), key=lambda nm: tab[nm]["TE"])
    res["VARIANT_BEST_ON_TEST"] = {"variant": best_te, "test_R": tab[best_te]["TE"],
                                   "train_R": tab[best_te]["TR"]}

    # ---------- (2) cost vs geometry diagnosis
    recs = load(TOUCH)
    ep = {}
    for w in w0_ws.iter_rows():
        ep[(w["candidate_id"], w["decision_time_utc"])] = w.get("entry_price")
    for r in recs:
        r["entry_price"] = ep.get((r["candidate_id"], r["decision_time_utc"]))
    tak = pop(recs, "TAKEABLE")
    fam = {}
    for r in tak:
        fam.setdefault(r["family"], []).append(r)
    diag = {}
    for f, rows in sorted(fam.items()):
        rd = [(r["risk_distance"] / r["entry_price"] * 100.0) for r in rows
              if r["entry_price"] and r["risk_distance"]]
        diag[f] = {
            "n": len(rows),
            "mean_cost_frozen_r": round(mean(r["cost_r"] or 0.0 for r in rows), 5),
            "mean_cost_sp73_r": round(mean(corrected(r) for r in rows), 5),
            "mean_spread_r": round(mean(r["spread_r"] or 0.0 for r in rows), 5),
            "median_spread_r": round(q([r["spread_r"] or 0.0 for r in rows], .5), 5),
            "mean_commission_r": round(mean(r["commission_r"] or 0.0 for r in rows), 5),
            "median_risk_distance_pct_of_price": round(q(rd, .5), 6),
            "p25_risk_distance_pct": round(q(rd, .25), 6),
            "mfe_mean": round(mean(r["mfe_r"] for r in rows if r.get("tf_r") is not None), 5),
            "share_cost73_gt_MFE": round(sum(1 for r in rows if r.get("tf_r") is not None
                                             and corrected(r) > r["mfe_r"]) / len(rows), 5),
        }
    res["COST_VS_GEOMETRY"] = diag
    # pool-level: how many candidates have corrected cost > their own MFE
    fl = [r for r in tak if r.get("tf_r") is not None]
    res["POOL_COST_VS_MFE"] = {
        "n": len(fl),
        "share_cost73_gt_MFE": round(sum(1 for r in fl if corrected(r) > r["mfe_r"]) / len(fl), 5),
        "share_costFROZEN_gt_MFE": round(sum(1 for r in fl if (r["cost_r"] or 0) > r["mfe_r"]) / len(fl), 5),
        "share_cost73_gt_0.25R": round(sum(1 for r in fl if corrected(r) > 0.25) / len(fl), 5),
        "share_cost73_gt_1R": round(sum(1 for r in fl if corrected(r) > 1.0) / len(fl), 5),
        "mean_cost73": round(mean(corrected(r) for r in fl), 5),
        "median_cost73": round(q([corrected(r) for r in fl], .5), 5),
    }
    # ---------- (3) composed policies, per ORIGINAL candidate, net at corrected cost
    def compose(pred, T, S, label):
        rows = [r for r in tak if pred(r)]
        g = sum(cell(r, T, S, "r")[0] for r in rows)
        c = sum(corrected(r) for r in rows)
        return {"label": label, "n": len(rows), "T": T, "S": S,
                "gross_per_ORIGINAL": round(g / N_ORIG, 5),
                "gross_per_TAKEN": round(g / len(rows), 5) if rows else None,
                "net73_per_ORIGINAL": round((g - c) / N_ORIG, 5),
                "net73_per_TAKEN": round((g - c) / len(rows), 5) if rows else None}
    comp = []
    cheap = lambda r: corrected(r) <= 0.15
    comp.append(compose(lambda r: True, 2.0, 1.0, "TAKEABLE, declared T2/S1"))
    comp.append(compose(lambda r: True, 0.75, 0.25, "TAKEABLE, tested cell T0.75/S0.25"))
    comp.append(compose(lambda r: r["born"] != "born_marketable", 0.75, 0.25, "+ decline marketable"))
    comp.append(compose(lambda r: cheap(r), 2.0, 1.0, "+ corrected cost <= 0.15R, declared T2/S1"))
    comp.append(compose(lambda r: cheap(r), 0.75, 0.25, "+ corrected cost <= 0.15R, tested cell"))
    comp.append(compose(lambda r: cheap(r) and r["born"] != "born_marketable", 2.0, 1.0,
                        "cheap + not marketable, declared T2/S1"))
    comp.append(compose(lambda r: cheap(r) and r["born"] == "born_resting", 2.0, 1.0,
                        "cheap + born_resting only, declared T2/S1"))
    comp.append(compose(lambda r: cheap(r) and r["born"] == "born_resting" and r["side"] == "LONG", 2.0, 1.0,
                        "cheap + resting + LONG (DIRECTIONAL - month artifact risk), declared T2/S1"))
    comp.append(compose(lambda r: cheap(r) and r["born"] == "born_resting", 3.0, 1.0,
                        "cheap + resting, T3/S1"))
    res["COMPOSED"] = comp
    with open(OUT, "w") as fh:
        json.dump(res, fh, indent=1)

    print("VARIANT best-on-TRAIN %s  train %+.5f -> TEST %+.5f (shrink %+.5f)"
          % (best_tr, tab[best_tr]["TR"], tab[best_tr]["TE"], res["VARIANT_BEST_ON_TRAIN"]["shrinkage"]))
    print("VARIANT best-on-TEST  %s  test %+.5f (train %+.5f)" % (best_te, tab[best_te]["TE"], tab[best_te]["TR"]))
    print("--- top-10 variants by TEST ---")
    for nm in sorted(names, key=lambda n: -tab[n]["TE"])[:10]:
        print("  %-26s TR %+.5f TE %+.5f ALL %+.5f SDE %+.5f RESTLONG %+.5f"
              % (nm, tab[nm]["TR"], tab[nm]["TE"], tab[nm]["ALLTAK"], tab[nm]["SDE"], tab[nm]["RESTLONG"]))
    print("--- cost vs geometry ---")
    for f, d in sorted(diag.items(), key=lambda kv: -kv[1]["mean_cost_sp73_r"]):
        print("  %-32s n%5d cost73 %.4f frozen %.4f spr_med %.4f riskdist_med%% %.4f MFE %.3f cost>MFE %.3f"
              % (f[:32], d["n"], d["mean_cost_sp73_r"], d["mean_cost_frozen_r"], d["median_spread_r"],
                 d["median_risk_distance_pct_of_price"], d["mfe_mean"], d["share_cost73_gt_MFE"]))
    print("POOL cost73>MFE %.4f | frozen>MFE %.4f | mean cost73 %.4f median %.4f"
          % (res["POOL_COST_VS_MFE"]["share_cost73_gt_MFE"], res["POOL_COST_VS_MFE"]["share_costFROZEN_gt_MFE"],
             res["POOL_COST_VS_MFE"]["mean_cost73"], res["POOL_COST_VS_MFE"]["median_cost73"]))
    print("--- composed (per ORIGINAL candidate) ---")
    for c in comp:
        print("  %-52s n%6d gross %+.5f net73 %+.5f | perTAKEN g %+.4f n %+.4f"
              % (c["label"][:52], c["n"], c["gross_per_ORIGINAL"], c["net73_per_ORIGINAL"],
                 c["gross_per_TAKEN"], c["net73_per_TAKEN"]))


if __name__ == "__main__":
    main()
