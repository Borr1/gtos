#!/usr/bin/env python3
"""a1 step 40 - three things the step-30 result forces:

  (1) THE DELAY LADDER, per month, PAIRED - is the entry-timing lever the one
      anatomy result that travels?  Paired day-block bootstrap of
      gross(k) - gross(0) on identical rows, every month separately.

  (2) THE COST-GATE INTERACTION - a1's limbs are affordability filters in
      disguise (step 30).  So: reproduce b1-BOOK-V1, then add a1's limbs to it,
      and sweep the cost threshold.  Does the anatomy repair pay INSIDE the only
      cost band anyone has made positive?

  (3) THE SAME-TRAP DECOMPOSITION for every arm: gross retained vs toll moved.
"""
from __future__ import annotations
import json
import os
import sys

import numpy as np

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import a1_lib as A  # noqa: E402
from a1_30_book import Arms, GEO_TH, C0_TH, MONTHS, IS, OOS, OOS2  # noqa: E402

KS = [-14, -10, -5, -2, -1, 0, 1, 2, 3, 4, 5, 6, 8, 10, 15, 20, 30, 45]
COST_BPS = [0.30, 0.45, 0.60, 0.80, 1.00, 1.50, 2.00, 3.00, 1e9]


def paired_boot(delta, day, B=4000, seed=23):
    return A.dayboot(delta, day, B=B, seed=seed)


def main():
    arms = {mm: Arms(mm) for mm in MONTHS}
    R = {}

    # ---------------------------------------------------- (1) the delay ladder
    lad = {}
    for mm in MONTHS:
        a = arms[mm]
        M = a.M
        base_s, _ = a.gross(0, "STOPONLY")
        base_i, _ = a.gross(0, "INC")
        rows = {}
        for k in KS:
            for cn in ("STOPONLY", "INC"):
                r, reason = a.gross(k, cn)
                ok = np.isfinite(r)
                base = base_s if cn == "STOPONLY" else base_i
                dlt = r - base
                m, lo, hi, p = paired_boot(dlt[ok], M.day[ok])
                rows["k%d_%s" % (k, cn)] = {
                    "k": k, "contract": cn, "n": int(ok.sum()),
                    "gross_R": float(r[ok].mean()),
                    "net_R": float((r[ok] - M.cost[ok]).mean()),
                    "delta_vs_k0_same_contract": m,
                    "ci_lo": lo, "ci_hi": hi, "p_delta_le0": p,
                    "share_stop": float((reason[ok] == 0).mean()),
                    "share_bell": float((reason[ok] == 2).mean()),
                }
        lad[mm] = rows
        print("%s ladder done" % mm, flush=True)
    R["delay_ladder"] = lad

    # pooled cross-month persistence of the k=5 lever
    per = {}
    for k in (1, 2, 3, 5, 8, 10, 15, 30):
        vals = [lad[mm]["k%d_STOPONLY" % k]["delta_vs_k0_same_contract"] for mm in MONTHS]
        per["k%d" % k] = {"per_month": dict(zip(MONTHS, vals)),
                          "mean": float(np.mean(vals)), "sd": float(np.std(vals, ddof=1)),
                          "min": float(np.min(vals)), "max": float(np.max(vals)),
                          "months_positive": int(sum(v > 0 for v in vals))}
    # the full entry+exit repair: k0/INC -> k5/STOPONLY
    rep = {}
    for mm in MONTHS:
        a = arms[mm]
        ri, _ = a.gross(0, "INC")
        rs, _ = a.gross(5, "STOPONLY")
        ok = np.isfinite(ri) & np.isfinite(rs)
        m, lo, hi, p = paired_boot((rs - ri)[ok], a.M.day[ok])
        rep[mm] = {"delta_gross": m, "ci_lo": lo, "ci_hi": hi, "p_le0": p,
                   "n": int(ok.sum())}
    R["lever_persistence"] = {"delay_only_same_contract": per, "entry_plus_exit_repair": rep}

    # ---------------------------------------------------- (2) cost-gate interaction
    def build(mms, tollbps, limbs, k, contract):
        gs, cs, ds, rd, rs, sy = [], [], [], [], [], []
        for mm in mms:
            a = arms[mm]
            M = a.M
            g = a.gates(k)
            m = np.ones(M.n, dtype=bool)
            if "G" in limbs:
                m &= g["G"]
            if "C" in limbs:
                m &= g["C"]
            if "S" in limbs:
                m &= g["S"]
            if tollbps < 1e8:
                m &= (M.cost * M.rdp * 1e4) <= tollbps
            r, reason = a.gross(k, contract)
            ok = m & np.isfinite(r)
            gs.append(r[ok]); cs.append(M.cost[ok]); ds.append(M.day[ok])
            rd.append(M.rdp[ok]); rs.append(reason[ok]); sy.append(M.symbol[ok])
        if not sum(len(x) for x in gs):
            return None
        g_ = np.concatenate(gs); c_ = np.concatenate(cs); d_ = np.concatenate(ds)
        rd_ = np.concatenate(rd); rs_ = np.concatenate(rs); sy_ = np.concatenate(sy)
        o = A.summarize(g_, c_, d_, rd_, rs_, B=2000)
        o["instruments"] = sorted(set(sy_.tolist()))
        return o

    grid = {}
    for tb in COST_BPS:
        for limbs in ("", "C", "GCS"):
            for k, cn in ((0, "INC"), (3, "STOPONLY"), (5, "STOPONLY")):
                key = "toll%.2f|limbs=%s|k%d_%s" % (tb, limbs or "-", k, cn)
                grid[key] = {
                    "IS_jan": build(IS, tb, limbs, k, cn),
                    "OOS_febmar": build(OOS, tb, limbs, k, cn),
                    "OOS2_aprmay": build(OOS2, tb, limbs, k, cn),
                    "hunt3m": build(MONTHS[:3], tb, limbs, k, cn),
                    "all5": build(MONTHS, tb, limbs, k, cn),
                }
        print("toll %.2f done" % tb, flush=True)
    R["cost_gate_grid"] = grid

    # b1 reproduction check
    b1 = grid["toll0.60|limbs=-|k3_STOPONLY"]
    R["b1_reproduction"] = {
        "published": {"n_hunt3m": 3728, "net_R": 0.076498, "gross_R": 0.123169,
                      "cost_R": 0.046671, "edge_toll": 2.6391,
                      "instruments": ["GER40", "NAS100", "US30_cash"],
                      "share_bell": 0.4925},
        "a1_stamp_convention": {k: b1["hunt3m"][k] for k in
                                ("n", "net_R", "gross_R", "cost_R", "edge_toll",
                                 "share_bell", "instruments", "t_day", "p_net_le0")},
        "note": ("a1 walks WALL-CLOCK stamps (D+k minutes); b1/h5 walk BAR COUNTS "
                 "(the k-th available M1 bar after D). Identical on rows with no "
                 "missing minutes; ~51 % of rows differ (A1_VALIDATE_V1 V5)."),
    }

    # ---------------------------------------------------- (3) trap decomposition per arm
    trap = {}
    for key, v in grid.items():
        i, o, o2 = v["IS_jan"], v["OOS_febmar"], v["OOS2_aprmay"]
        if not i or not o or i["n"] < 100 or o["n"] < 100:
            continue
        trap[key] = {
            "IS_n": i["n"], "IS_net": i["net_R"], "IS_gross": i["gross_R"], "IS_cost": i["cost_R"],
            "OOS_n": o["n"], "OOS_net": o["net_R"], "OOS_gross": o["gross_R"], "OOS_cost": o["cost_R"],
            "delta_net": o["net_R"] - i["net_R"],
            "edge_component": o["gross_R"] - i["gross_R"],
            "cost_component": -(o["cost_R"] - i["cost_R"]),
            "gross_retained": (o["gross_R"] / i["gross_R"]) if i["gross_R"] else None,
            "toll_moved": (o["cost_R"] / i["cost_R"] - 1.0) if i["cost_R"] else None,
            "OOS2_net": o2["net_R"] if o2 else None,
            "OOS2_n": o2["n"] if o2 else None,
        }
    R["trap_by_arm"] = trap

    with open(os.path.join(D, "A1_COSTGATE_V1.json"), "w") as f:
        json.dump(R, f, indent=1)

    print("\n=== delay lever persistence (gross delta vs k=0, same contract) ===")
    for k, v in per.items():
        print("%-4s mean %+.5f sd %.5f  months+ %d/5   %s"
              % (k, v["mean"], v["sd"], v["months_positive"],
                 {m: round(x, 5) for m, x in v["per_month"].items()}))
    print("\n=== b1 reproduction (stamp convention) ===")
    print(json.dumps(R["b1_reproduction"]["a1_stamp_convention"], indent=1))
    print("\n=== cost-gate grid: net R by window ===")
    print("%-42s %7s %8s %7s %8s %7s %8s" % ("arm", "IS_n", "IS_net", "OOS_n", "OOS_net", "O2_n", "O2_net"))
    for key, v in grid.items():
        i, o, o2 = v["IS_jan"], v["OOS_febmar"], v["OOS2_aprmay"]
        if not i or i["n"] < 50:
            continue
        print("%-42s %7d %+8.5f %7d %+8.5f %7d %+8.5f"
              % (key, i["n"], i["net_R"], o["n"], o["net_R"],
                 o2["n"] if o2 else 0, o2["net_R"] if o2 else float("nan")))


if __name__ == "__main__":
    main()
