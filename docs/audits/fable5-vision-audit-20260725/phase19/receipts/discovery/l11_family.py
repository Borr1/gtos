#!/usr/bin/env python3
"""l11 step 3 — the per-family exit contract, designed then fitted then tested.

Three contracts are reported for every family, and the gap between them IS the finding:

  INCUMBENT   T2 / S1, one shared geometry for all ten families (what the engine runs)
  DESIGNED    two analytic choices only -- the family's own best target level and best stop
              level from the exit-vs-hold identity, each measured on TRAIN days only
  FITTED      argmax over a 3,840-cell contract space on TRAIN days

and all three are then read on TEST days, which is the only column that means anything.

Both sizing framings are reported, because they disagree about tight stops:
  FIXED SIZE   R on the ORIGINAL risk distance, costs constant  (research convention)
  FIXED RISK   resized so the contract's own stop is 1R, cost divided by the same S
               (what a live book with risk_per_trade_pct actually does)
"""
from __future__ import annotations

import itertools
import json
import os
import sys

import numpy as np

import l11_lib
import l11_walk

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "L11_FAMILY_V1.json")
SPLIT = "2026-01-16"

T_SET = [None, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0]
S_SET = [None, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0]
G_SET = [1, 10, 20]
TR_SET = [None, (0.5, 0.25), (1.0, 0.5), (2.0, 1.0)]
MB_SET = [30, 60, 90, 120]


def contracts():
    for T, S, G, TR, MB in itertools.product(T_SET, S_SET, G_SET, TR_SET, MB_SET):
        if T is None and S is None and TR is None and MB == 120 and G != 1:
            continue                      # identical to hold-to-wall, skip duplicates
        if S is None and TR is not None:
            continue                      # a trail needs a stop to tighten
        if G != 1 and T is None and S is None:
            continue
        yield {"target": T, "stop": S, "arm_bar": G,
               "trail_arm": None if TR is None else TR[0],
               "trail_gap": None if TR is None else TR[1],
               "max_bars": MB}


def label(c):
    return "T%s_S%s_G%d_TR%s_MB%d" % (
        "none" if c["target"] is None else "%.2f" % c["target"],
        "none" if c["stop"] is None else "%.2f" % c["stop"],
        c["arm_bar"],
        "none" if c["trail_arm"] is None else "%.2f-%.2f" % (c["trail_arm"], c["trail_gap"]),
        c["max_bars"])


def main():
    s = l11_lib.load()
    e = l11_walk.Engine(s)
    take = s.takeable
    cost_all = s.cost_r()
    train_all = take & (s.day < SPLIT)
    test_all = take & (s.day >= SPLIT)

    def ev(mask, c, cost=None):
        r, rs, eb = e.run(rows=mask, **c)
        n = len(r)
        if n == 0:
            return None
        cc = cost_all[mask] if cost is None else cost
        net = r - np.where(rs != 0, cc, 0.0)
        S = c["stop"]
        risk = S if S is not None else max(1e-9, float(-np.percentile(r, 1)))
        sd = float(r.std(ddof=1)) if n > 1 else 0.0
        return {"n": int(n), "gross": round(float(r.mean()), 6),
                "net": round(float(net.mean()), 6),
                "t": round(float(r.mean() / (sd / np.sqrt(n))), 3) if sd > 0 else 0.0,
                "risk_unit": round(float(risk), 4),
                "gross_per_risk": round(float(r.mean() / risk), 6),
                "net_per_risk": round(float(net.mean() / risk), 6),
                "win": round(float((r > 1e-9).mean()), 5),
                "p01": round(float(np.percentile(r, 1)), 4),
                "stop_n": int((rs == 1).sum()), "tgt_n": int((rs == 2).sum()),
                "mark_n": int((rs == 3).sum())}

    CL = list(contracts())
    out = {"lane": "l11", "pass": "FAMILY", "split": SPLIT,
           "n_contracts_searched": len(CL),
           "framing": "gross/net are FIXED SIZE (R on the original risk distance); "
                      "*_per_risk divides by the contract's own stop = FIXED RISK",
           "families": {}}
    fams = sorted(set(s.fam[take].tolist()))
    an = json.load(open(os.path.join(HERE, "L11_ANALYTIC_V1.json")))

    INC = {"target": 2.0, "stop": 1.0, "arm_bar": 1, "trail_arm": None,
           "trail_gap": None, "max_bars": 120}
    HOLD = {"target": None, "stop": None, "arm_bar": 1, "trail_arm": None,
            "trail_gap": None, "max_bars": 120}

    for f in ["POOL"] + fams:
        fm = take if f == "POOL" else (take & (s.fam == f))
        tr = fm & (s.day < SPLIT)
        te = fm & (s.day >= SPLIT)
        if te.sum() < 60:
            continue
        rec = {"n": int(fm.sum()), "n_train": int(tr.sum()), "n_test": int(te.sum())}
        rec["INCUMBENT"] = {"spec": INC, "train": ev(tr, INC), "test": ev(te, INC),
                            "all": ev(fm, INC)}
        rec["HOLD"] = {"spec": HOLD, "train": ev(tr, HOLD), "test": ev(te, HOLD),
                       "all": ev(fm, HOLD)}
        # ---- DESIGNED: best target level and best stop level from the TRAIN analytic table
        F, D, A, rem = e.F[tr], e.D[tr], e.A[tr], e.rem[tr]
        tab = __import__("l11_analytic").table(F, D, A, rem, f + "|train")
        bt = max(tab["TARGET_LEVELS"].items(), key=lambda kv: kv[1]["value_per_candidate"])
        bs = max(tab["STOP_LEVELS"].items(), key=lambda kv: kv[1]["value_per_candidate"])
        des = {"target": bt[1]["level"] if bt[1]["value_per_candidate"] > 0 else None,
               "stop": -bs[1]["level"] if bs[1]["value_per_candidate"] > 0 else None,
               "arm_bar": 1, "trail_arm": None, "trail_gap": None, "max_bars": 120}
        rec["DESIGNED"] = {"spec": des, "train": ev(tr, des), "test": ev(te, des),
                           "train_analytic_target": bt[0], "train_analytic_stop": bs[0],
                           "target_value_train": bt[1]["value_per_candidate"],
                           "stop_value_train": bs[1]["value_per_candidate"]}
        # ---- FITTED: argmax gross on TRAIN over the whole contract space
        best, bestv = None, -1e18
        bestnet, bestnetv = None, -1e18
        for c in CL:
            v = ev(tr, c)
            if v is None:
                continue
            if v["gross"] > bestv:
                bestv, best = v["gross"], c
            if v["net"] > bestnetv:
                bestnetv, bestnet = v["net"], c
        rec["FITTED_GROSS"] = {"spec": best, "label": label(best),
                               "train": ev(tr, best), "test": ev(te, best)}
        rec["FITTED_NET"] = {"spec": bestnet, "label": label(bestnet),
                             "train": ev(tr, bestnet), "test": ev(te, bestnet)}
        out["families"][f] = rec
        print("%-30s inc %+.4f/%+.4f  hold %+.4f/%+.4f  des %+.4f/%+.4f  fit %+.4f/%+.4f  %s"
              % (f[:30], rec["INCUMBENT"]["train"]["gross"], rec["INCUMBENT"]["test"]["gross"],
                 rec["HOLD"]["train"]["gross"], rec["HOLD"]["test"]["gross"],
                 rec["DESIGNED"]["train"]["gross"], rec["DESIGNED"]["test"]["gross"],
                 rec["FITTED_GROSS"]["train"]["gross"], rec["FITTED_GROSS"]["test"]["gross"],
                 label(best)), flush=True)

    # ---- portfolio: per-family fitted policy applied to TEST, vs one shared contract
    for tag, key in (("DESIGNED", "DESIGNED"), ("FITTED_GROSS", "FITTED_GROSS")):
        tot_g = tot_n = 0.0
        tot_net = 0.0
        for f in fams:
            if f not in out["families"]:
                continue
            v = out["families"][f][key]["test"]
            tot_g += v["gross"] * v["n"]
            tot_net += v["net"] * v["n"]
            tot_n += v["n"]
        out["PORTFOLIO_TEST_" + tag] = {
            "n": int(tot_n), "gross": round(tot_g / tot_n, 6), "net": round(tot_net / tot_n, 6)}
    pt = out["families"]["POOL"]["INCUMBENT"]["test"]
    ph = out["families"]["POOL"]["HOLD"]["test"]
    out["PORTFOLIO_TEST_SHARED_INCUMBENT"] = {"n": pt["n"], "gross": pt["gross"], "net": pt["net"]}
    out["PORTFOLIO_TEST_SHARED_HOLD"] = {"n": ph["n"], "gross": ph["gross"], "net": ph["net"]}
    with open(OUT, "w") as fh:
        json.dump(out, fh, indent=1)
    print(json.dumps({k: v for k, v in out.items() if k.startswith("PORTFOLIO")}))


if __name__ == "__main__":
    main()
