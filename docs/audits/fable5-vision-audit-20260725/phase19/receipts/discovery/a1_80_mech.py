#!/usr/bin/env python3
"""a1 step 80 - the mechanism behind 'a1's limbs are affordability filters'.

M1  Both published separators share `risk_distance` with the cost denominator:
        geo      = risk_distance / trigger_bar_range
        cost_R   = cost_price     / risk_distance
    so geo and cost_R are mechanically anti-correlated.  Measure it.
M2  The confirm gate's own cost tilt, and what is left of it after the tilt is removed.
M3  The gate's marginal value at each fill, per month, day-block bootstrapped.
M4  The fade book's gross, per month, and the info level at each entry minute.
"""
from __future__ import annotations
import json
import os
import sys

import numpy as np

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import a1_lib as A  # noqa: E402
from a1_30_book import Arms, MONTHS, IS, OOS, OOS2  # noqa: E402
from a1_50_diag import walk_mirror  # noqa: E402


def main():
    arms = {mm: Arms(mm) for mm in MONTHS}
    R = {}

    # ------------------------------------------------------------------ M1 / M2
    m1 = {}
    for mm in MONTHS:
        M = arms[mm].M
        ok = np.isfinite(M.geo)
        m1[mm] = {
            "spearman_geo_vs_costR": A.spearman(M.geo[ok], M.cost[ok]),
            "spearman_geo_vs_riskdistance_pct": A.spearman(M.geo[ok], M.rdp[ok]),
            "spearman_c0_vs_costR": A.spearman(M.c0, M.cost),
            "spearman_absc0_vs_costR": A.spearman(np.abs(M.c0), M.cost),
            "cost_R_mean_geo_gt0.60": float(M.cost[ok & (M.geo > 0.60)].mean()),
            "cost_R_mean_geo_le0.60": float(M.cost[ok & (M.geo <= 0.60)].mean()),
            "cost_R_mean_c0_gt-0.15": float(M.cost[M.c0 > -0.15].mean()),
            "cost_R_mean_c0_le-0.15": float(M.cost[M.c0 <= -0.15].mean()),
            "rdp_median_geo_gt0.60": float(np.median(M.rdp[ok & (M.geo > 0.60)])),
            "rdp_median_geo_le0.60": float(np.median(M.rdp[ok & (M.geo <= 0.60)])),
        }
    R["M1_separator_is_a_cost_proxy"] = m1

    # ------------------------------------------------------------------ M3 gate marginal
    m3 = {}
    for mm in MONTHS:
        a = arms[mm]
        M = a.M
        g = M.c0 > -0.15
        rec = {}
        for k, cn in ((0, "INC"), (1, "INC"), (1, "STOPONLY"), (5, "STOPONLY")):
            r, _ = a.gross(k, cn)
            net = r - M.cost
            # marginal gross value of the gate = kept mean - all mean (unpaired,
            # so also report the refused-set mean per x4's own metric warning)
            rec["k%d_%s" % (k, cn)] = {
                "all_gross": float(r.mean()), "kept_gross": float(r[g].mean()),
                "refused_gross": float(r[~g].mean()),
                "gate_gross_gap": float(r[g].mean() - r[~g].mean()),
                "all_net": float(net.mean()), "kept_net": float(net[g].mean()),
                "refused_net": float(net[~g].mean()),
                "gate_net_gap": float(net[g].mean() - net[~g].mean()),
                "kept_n": int(g.sum()), "refused_n": int((~g).sum()),
                "executable": k >= 1,
            }
        m3[mm] = rec
    R["M3_gate_marginal_by_fill"] = m3

    # ------------------------------------------------------------------ M4 fade + info
    m4 = {}
    for mm in MONTHS:
        a = arms[mm]
        M = a.M
        rec = {"info_level_by_k": {}}
        for k in (0, 1, 2, 3, 5, 8, 10, 15, 30):
            ro, _ = a.gross(k, "STOPONLY")
            rm = walk_mirror(M, k)
            rec["info_level_by_k"]["k%d" % k] = {
                "orig_gross": float(ro.mean()), "mirror_gross": float(rm.mean()),
                "info_level": 0.5 * float(rm.mean() - ro.mean()),
                "info_ci": A.dayboot(0.5 * (rm - ro), M.day)[1:3],
            }
        rec["fade_net_all_rows_k0"] = float((walk_mirror(M, 0) - M.cost).mean())
        m4[mm] = rec
    R["M4_fade_and_info_level"] = m4

    with open(os.path.join(D, "A1_MECH_V1.json"), "w") as f:
        json.dump(R, f, indent=1)

    print("=== M1: the separators ARE cost ===")
    for mm, v in m1.items():
        print("%s geo~cost rho %+.4f | c0~cost rho %+.4f | cost_R geo>0.6 %.4f vs <=0.6 %.4f "
              "| cost_R c0>-0.15 %.4f vs <=-0.15 %.4f"
              % (mm, v["spearman_geo_vs_costR"], v["spearman_c0_vs_costR"],
                 v["cost_R_mean_geo_gt0.60"], v["cost_R_mean_geo_le0.60"],
                 v["cost_R_mean_c0_gt-0.15"], v["cost_R_mean_c0_le-0.15"]))
    print("\n=== M3: the confirm gate's gross gap, by fill ===")
    for mm, v in m3.items():
        print(mm, " ".join("%s:%+.4f%s" % (k, x["gate_gross_gap"],
                                           "" if x["executable"] else "*")
                           for k, x in v.items()), "   (* = not executable)")
    print("\n=== M4: info level (>0 means the signal's own side is WRONG) ===")
    for mm, v in m4.items():
        print(mm, " ".join("%s %+.4f" % (k, x["info_level"])
                           for k, x in v["info_level_by_k"].items()))


if __name__ == "__main__":
    main()
