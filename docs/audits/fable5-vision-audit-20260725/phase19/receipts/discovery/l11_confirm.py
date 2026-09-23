#!/usr/bin/env python3
"""l11 step 4b — the invariance matrix for the ONE prescription worth acting on.

The per-family design dies to deduplication and to 0.05R of stop slippage (L11_ROBUST).
The claim that has to survive everything is the simpler one: the shared 2R/-1R contract
the engine runs is DOMINATED by having no exit contract at all. Test it under every
convention this pool admits, simultaneously, and report the whole grid rather than the
best corner.

Also priced here: how big is the designed stop next to the SPREAD it has to clear.
"""
from __future__ import annotations

import itertools
import json
import os

import numpy as np

import l11_lib
import l11_walk

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "L11_CONFIRM_V1.json")

CONTRACTS = {
    "INCUMBENT_T2_S1": dict(target=2.0, stop=1.0),
    "HOLD_TO_WALL": dict(target=None, stop=None),
    "TIMESTOP_90": dict(target=None, stop=None, max_bars=90),
    "TIMESTOP_90_S3": dict(target=None, stop=3.0, max_bars=90),
    "T2_S1_TIMESTOP_90": dict(target=2.0, stop=1.0, max_bars=90),
    "STOP_ONLY_S1": dict(target=None, stop=1.0),
    "TARGET_ONLY_T2": dict(target=2.0, stop=None),
    "WIDE_T5_S3": dict(target=5.0, stop=3.0),
}


def main():
    s = l11_lib.load()
    eng = {"real": l11_walk.Engine(s, "real"), "strict": l11_walk.Engine(s, "strict")}
    take = s.takeable
    out = {"lane": "l11", "pass": "CONFIRM",
           "question": "does 'the incumbent exit contract is worse than no exit contract' "
                       "survive every convention at once?"}

    grid = {}
    for pop, fillm, slip, costdiv in itertools.product(
            ("ALL_TAKEABLE", "FIRST_EMISSION", "ALL_INCL_PASTSTOP"),
            ("real", "strict"), (0.0, 0.05), (7.3, 1.0)):
        e = eng[fillm]
        m = take.copy()
        if pop == "FIRST_EMISSION":
            m &= s.firstem
        elif pop == "ALL_INCL_PASTSTOP":
            m = np.ones(s.N, bool)
        cost = s.cost_r(spread_div=costdiv)[m]
        cell = {}
        for name, c in CONTRACTS.items():
            r, rs, _ = e.run(rows=m, stop_slip_r=slip, **c)
            cell[name] = {"gross": round(float(r.mean()), 6),
                          "net": round(float((r - np.where(rs != 0, cost, 0.0)).mean()), 6)}
        inc = cell["INCUMBENT_T2_S1"]["gross"]
        best = max(cell.items(), key=lambda kv: kv[1]["gross"])
        cell["_n"] = int(m.sum())
        cell["_incumbent_minus_hold"] = round(inc - cell["HOLD_TO_WALL"]["gross"], 6)
        cell["_best"] = best[0]
        cell["_best_minus_incumbent"] = round(best[1]["gross"] - inc, 6)
        grid["%s|%s|slip%.2f|div%.1f" % (pop, fillm, slip, costdiv)] = cell
    out["INVARIANCE_GRID"] = grid
    out["INCUMBENT_IS_DOMINATED_IN_ALL_CELLS"] = all(
        v["_incumbent_minus_hold"] < 0 for v in grid.values())
    out["RANGE_incumbent_minus_hold"] = [
        round(min(v["_incumbent_minus_hold"] for v in grid.values()), 6),
        round(max(v["_incumbent_minus_hold"] for v in grid.values()), 6)]

    # ---- how big is a 0.25R stop next to the spread it has to clear?
    sp73 = s.spread[take] / 7.3
    tot = s.cost_r()[take]
    out["SPREAD_VS_STOP_GEOMETRY"] = {
        "truthed_spread_r_mean": round(float(sp73.mean()), 5),
        "truthed_spread_r_median": round(float(np.median(sp73)), 5),
        "total_cost_r_mean": round(float(tot.mean()), 5),
        "share_rows_truthed_spread_ge_0.25R": round(float((sp73 >= 0.25).mean()), 5),
        "share_rows_total_cost_ge_0.25R": round(float((tot >= 0.25).mean()), 5),
        "share_rows_total_cost_ge_1.00R": round(float((tot >= 1.0).mean()), 5),
        "note": "a designed 0.25R stop is a level the round-trip cost alone eats on "
                "this share of rows; under FIXED-RISK sizing the same cost is "
                "multiplied by 1/0.25 = 4x"}

    # ---- fixed-risk framing of the headline contracts
    fr = {}
    for name, c in CONTRACTS.items():
        r, rs, _ = eng["real"].run(rows=take, **c)
        S = c.get("stop") or float(-np.percentile(r, 1))
        cost = s.cost_r()[take]
        fr[name] = {"risk_unit_R": round(float(S), 4),
                    "gross_fixed_size": round(float(r.mean()), 6),
                    "gross_per_unit_risk": round(float(r.mean() / S), 6),
                    "net_per_unit_risk": round(float((r - np.where(rs != 0, cost, 0)).mean() / S), 6)}
    out["FIXED_RISK_FRAMING"] = fr

    with open(OUT, "w") as fh:
        json.dump(out, fh, indent=1)
    print("incumbent dominated in ALL cells:", out["INCUMBENT_IS_DOMINATED_IN_ALL_CELLS"],
          "range", out["RANGE_incumbent_minus_hold"])
    print("%-46s %8s %8s %8s %8s %-16s %8s" %
          ("cell", "inc", "hold", "ts90", "inc-hold", "best", "best-inc"))
    for k, v in grid.items():
        print("%-46s %+8.4f %+8.4f %+8.4f %+8.4f %-16s %+8.4f"
              % (k, v["INCUMBENT_T2_S1"]["gross"], v["HOLD_TO_WALL"]["gross"],
                 v["TIMESTOP_90"]["gross"], v["_incumbent_minus_hold"],
                 v["_best"][:16], v["_best_minus_incumbent"]))
    print(json.dumps(out["SPREAD_VS_STOP_GEOMETRY"]))


if __name__ == "__main__":
    main()
