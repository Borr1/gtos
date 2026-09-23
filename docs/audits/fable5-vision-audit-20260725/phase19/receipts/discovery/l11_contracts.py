#!/usr/bin/env python3
"""l11 step 2b — verify the analytic derivation on the paths, then sweep the contract
FAMILY the derivation points at (time-conditional exits), not the incumbent's grid.

Everything is per ORIGINAL candidate (a no-fill books 0.0 R) on TAKEABLE, fill REAL,
position size held fixed so costs are constant in R across contracts.
"""
from __future__ import annotations

import json
import os

import numpy as np

import l11_lib
import l11_walk

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "L11_CONTRACTS_V1.json")


def main():
    s = l11_lib.load()
    e = l11_walk.Engine(s)
    m = s.takeable
    idx = np.where(m)[0]
    n = len(idx)
    cost = s.cost_r()[idx]          # spread/7.3 + commission + slippage + swap
    costfr = s.costfr[idx]          # the frozen (over-charged) cost, for reference

    def ev(**kw):
        r, rs, eb = e.run(rows=m, **kw)
        filled = rs != 0
        net = r - np.where(filled, cost, 0.0)
        netfr = r - np.where(filled, costfr, 0.0)
        eb2 = eb[filled]
        return {"gross": round(float(r.sum() / n), 6),
                "net73": round(float(net.sum() / n), 6),
                "net_frozen": round(float(netfr.sum() / n), 6),
                "gross_se": round(float(r.std(ddof=1) / np.sqrt(n)), 6),
                "t": round(float(r.mean() / (r.std(ddof=1) / np.sqrt(n))), 3),
                "stop": int((rs == 1).sum()), "target": int((rs == 2).sum()),
                "mark": int((rs == 3).sum()), "no_fill": int((rs == 0).sum()),
                "win": round(float((r > 1e-9).sum() / max(filled.sum(), 1)), 5),
                "mean_exit_bar": round(float(eb2.mean()), 1) if len(eb2) else None,
                "worst": round(float(r.min()), 4)}

    out = {"lane": "l11", "pass": "CONTRACTS", "n": int(n),
           "population": "TAKEABLE, fill REAL, fixed position size",
           "cost_model": "spread_r/7.3 + commission_r + expected_slippage_r + swap_cost_r"}

    # ---------------------------------------------------------------- 1 baselines
    base = {}
    base["HOLD_TO_WALL (no target, no stop)"] = ev(target=None, stop=None)
    base["INCUMBENT T2 / S1"] = ev(target=2.0, stop=1.0)
    base["target_only_T2"] = ev(target=2.0, stop=None)
    base["stop_only_S1"] = ev(target=None, stop=1.0)
    for L in (0.5, 1.0, 1.5, 3.0, 5.0):
        base["target_only_T%.1f" % L] = ev(target=L, stop=None)
    for S in (0.25, 0.5, 1.5, 2.0, 3.0):
        base["stop_only_S%.2f" % S] = ev(target=None, stop=S)
    out["BASELINES"] = base

    # analytic-vs-measured check: predicted delta = P(touch) * (L - E[wall|touch])
    an = json.load(open(os.path.join(HERE, "L11_ANALYTIC_V1.json")))
    hold = base["HOLD_TO_WALL (no target, no stop)"]["gross"]
    chk = {}
    for L in (0.5, 1.0, 1.5, 2.0, 3.0, 5.0):
        k = "T%+.2f" % L
        if k in an["POOL"]["TARGET_LEVELS"]:
            pred = an["POOL"]["TARGET_LEVELS"][k]["value_per_candidate"]
            got = base.get("target_only_T%.1f" % L, ev(target=L, stop=None))["gross"] - hold
            chk[k] = {"predicted": pred, "measured": round(got, 6),
                      "abs_err": round(abs(pred - got), 6)}
    for S in (0.25, 0.5, 1.0, 1.5, 2.0, 3.0):
        k = "S-%.2f" % S
        if k in an["POOL"]["STOP_LEVELS"]:
            pred = an["POOL"]["STOP_LEVELS"][k]["value_per_candidate"]
            got = base.get("stop_only_S%.2f" % S, ev(target=None, stop=S))["gross"] - hold
            chk[k] = {"predicted": pred, "measured": round(got, 6),
                      "abs_err": round(abs(pred - got), 6)}
    out["ANALYTIC_VERIFICATION"] = {
        "identity": "gross(exit-only-at-L) - gross(hold) == P(touch L) * (L - E[wall|touch L])",
        "rows": chk,
        "max_abs_err": round(max(v["abs_err"] for v in chk.values()), 6)}

    # ---------------------------------------------------------------- 2 grace period
    grace = {}
    for G in (1, 3, 5, 8, 10, 15, 20, 30, 45, 60):
        grace["G%d_T2_S1" % G] = ev(target=2.0, stop=1.0, arm_bar=G)
        grace["G%d_stoponly_S1" % G] = ev(target=None, stop=1.0, stop_arm_bar=G)
        grace["G%d_targetonly_T2" % G] = ev(target=2.0, stop=None, target_arm_bar=G)
    out["GRACE_PERIOD"] = grace

    # ---------------------------------------------------------------- 3 trail / BE / partial
    tr = {}
    for arm, gap in [(0.5, 0.25), (0.5, 0.5), (1.0, 0.25), (1.0, 0.5), (1.0, 1.0),
                     (1.5, 0.5), (2.0, 0.5), (2.0, 1.0), (3.0, 1.0), (0.25, 0.25)]:
        tr["trail_arm%.2f_gap%.2f_S1_noT" % (arm, gap)] = ev(
            target=None, stop=1.0, trail_arm=arm, trail_gap=gap)
    for be in (0.25, 0.5, 1.0, 1.5, 2.0):
        tr["BE_at%.2f_T2_S1" % be] = ev(target=2.0, stop=1.0, be_at=be)
        tr["BE_at%.2f_noT_S1" % be] = ev(target=None, stop=1.0, be_at=be)
    for pa, pf in [(1.0, 0.5), (1.0, 0.25), (2.0, 0.5), (0.5, 0.5), (1.5, 0.5)]:
        tr["partial%.2f_frac%.2f_T2_S1" % (pa, pf)] = ev(
            target=2.0, stop=1.0, partial_at=pa, partial_frac=pf)
        tr["partial%.2f_frac%.2f_noT_S1" % (pa, pf)] = ev(
            target=None, stop=1.0, partial_at=pa, partial_frac=pf)
    out["TRAIL_BE_PARTIAL"] = tr

    # ---------------------------------------------------------------- 4 time stop
    ts = {}
    for mb in (5, 10, 15, 20, 30, 45, 60, 90, 120):
        ts["timestop%d_noT_noS" % mb] = ev(target=None, stop=None, max_bars=mb)
        ts["timestop%d_T2_S1" % mb] = ev(target=2.0, stop=1.0, max_bars=mb)
    out["TIME_STOP"] = ts

    with open(OUT, "w") as fh:
        json.dump(out, fh, indent=1)

    print("n=%d  cost73_mean=%.4f  cost_frozen_mean=%.4f" % (n, cost.mean(), costfr.mean()))
    print("%-34s %9s %9s %8s %6s %6s %6s" % ("contract", "gross", "net73", "t", "stop", "tgt", "mark"))
    for k, v in list(base.items()):
        print("%-34s %+9.5f %+9.5f %8.2f %6d %6d %6d"
              % (k[:34], v["gross"], v["net73"], v["t"], v["stop"], v["target"], v["mark"]))
    print("--- analytic check, max abs err %.5f" % out["ANALYTIC_VERIFICATION"]["max_abs_err"])
    print("--- grace period (arm both limbs at bar G)")
    for k in sorted(grace, key=lambda x: -grace[x]["gross"])[:12]:
        print("%-34s %+9.5f %+9.5f %8.2f" % (k, grace[k]["gross"], grace[k]["net73"], grace[k]["t"]))
    print("--- trail / BE / partial, best 10")
    for k in sorted(tr, key=lambda x: -tr[x]["gross"])[:10]:
        print("%-34s %+9.5f %+9.5f %8.2f" % (k, tr[k]["gross"], tr[k]["net73"], tr[k]["t"]))
    print("--- time stop, best 8")
    for k in sorted(ts, key=lambda x: -ts[x]["gross"])[:8]:
        print("%-34s %+9.5f %+9.5f %8.2f" % (k, ts[k]["gross"], ts[k]["net73"], ts[k]["t"]))


if __name__ == "__main__":
    main()
