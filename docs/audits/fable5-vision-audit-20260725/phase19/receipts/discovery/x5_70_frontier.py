#!/usr/bin/env python3
"""x5_70_frontier - assemble every rung from every family onto ONE frontier and rank it.

HONESTY RULE, and it is simple: at the decision instant D the system knows the whole
trigger bar's M1 history AND its own entry/stop/target levels.  So a CONDITION that looks
back inside the trigger bar is legal; what is illegal is ACTING before D.  A rung is
therefore HONEST iff every taken row's entry stamp is >= 0.

Emits x5_RESULT.json (the lane's machine-readable receipt).
"""
import json
import os
import sys

import numpy as np

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)


def L(p):
    with open(os.path.join(D, p)) as f:
        return json.load(f)


def main():
    lad = L("x5_LADDER_V1.json")
    cond = L("x5_COND_V2.json")
    lim = L("x5_LIMIT_V1.json")
    joint = L("x5_JOINT_V1.json")
    mir = L("x5_MIRROR_V1.json")
    cost = L("x5_COST_V1.json")
    can = L("x5_CANCEL_V1.json")
    mat = L("x5_MATCHED_V1.json")
    lxm = L("x5_LEVELXM_V1.json")

    base = cond["meta"]["baseline_k0_mean"]
    ncore = cond["meta"]["n_core"]
    rows = []
    # unconditional rungs (primary arm)
    for r in lad["ladder"]:
        if not (r["horizon"] == "MATCH" and r["denom"] == "STRUCTSTOP" and r["contract"] == "INC"):
            continue
        rows.append({"family": "UNCOND", "label": "k%+d" % r["k"], "N": None, "theta": None,
                     "n_taken": r["n"], "survival": r["n"] / ncore,
                     "mean_taken": r["mean"], "total": r["total"],
                     "book_per_candidate": r["total"] / ncore,
                     "honest": r["k"] >= 0, "fill_realistic": True,
                     "entry_stamp_med": r["k"]})
    for r in cond["rungs"]:
        rows.append({"family": r["cond"], "label": "%s th%.2f N%d" % (r["cond"], r["theta"], r["N"]),
                     "N": r["N"], "theta": r["theta"], "n_taken": r["n_taken"],
                     "survival": r["survival"], "mean_taken": r["mean_taken"],
                     "total": r["total"], "book_per_candidate": r["book_mean"],
                     "honest": r["share_entry_before_close"] == 0.0,
                     "fill_realistic": (r["cond"] not in ("LEVEL", "LEVELX")) or r["N"] == 1,
                     "entry_stamp_med": r["median_entry_stamp"]})
    for r in lim["levelxm"]:
        rows.append({"family": "LEVELXM", "label": "LEVELXM N%d" % r["N"], "N": r["N"],
                     "theta": 0.0, "n_taken": r["n_taken"], "survival": r["survival"],
                     "mean_taken": r["mean_taken"],
                     "total": r["mean_taken"] * r["n_taken"],
                     "book_per_candidate": r["book_mean"],
                     "honest": r["share_pre_close"] == 0.0, "fill_realistic": True,
                     "entry_stamp_med": r["median_entry_stamp"]})

    def top(key, honest_only, k=12, minn=300, real_only=False):
        c = [r for r in rows if r["n_taken"] >= minn and (r["honest"] or not honest_only)
             and (r["fill_realistic"] or not real_only)]
        return sorted(c, key=lambda r: -r[key])[:k]

    front = {"baseline_k0_mean": base, "n_core": ncore,
             "top_by_R_per_trade_ALL": top("mean_taken", False),
             "top_by_R_per_trade_HONEST": top("mean_taken", True),
             "top_by_total_R_ALL": top("total", False),
             "top_by_total_R_HONEST": top("total", True),
             "top_by_book_per_candidate_HONEST": top("book_per_candidate", True),
             "top_by_R_per_trade_HONEST_REALISTIC": top("mean_taken", True, real_only=True),
             "top_by_book_HONEST_REALISTIC": top("book_per_candidate", True, real_only=True),
             "all_rungs": rows}

    res = {"lane": "x5", "question": "the confirmation trade-off, priced properly",
           "substrate": {"pool": "CJ true-UTC January 2026 S0R0, 27,658 candidates",
                         "core_rows": ncore,
                         "core_definition": "M1 window present for the whole trigger bar and "
                                            "the decision minute, d0>0",
                         "m1_source": "lane-inputs-true-utc-hold-20260805 bridge_ftmo_m1_202601",
                         "horizon": "120 M1 bars from entry (MATCH) unless stated",
                         "tie_rule": "same-bar target+stop -> STOP (conservative)",
                         "no_same_bar_credit": "every rung's walk starts at the bar AFTER the "
                                               "entry bar"},
           "frontier": front,
           "headline_numbers": {
               "uncond_k_minus14_vs_k0_paired": [b for b in lad["paired_boot_vs_k0"] if b["k"] == -14][0],
               "uncond_k_plus5_vs_k0_paired": [b for b in lad["paired_boot_vs_k0"] if b["k"] == 5][0],
               "uncond_k_plus13_vs_k0_paired": [b for b in lad["paired_boot_vs_k0"] if b["k"] == 13][0],
               "info_curve_atmkt": joint["info_curve_atmkt"],
               "limit_joint": joint["limit_joint"],
               "atmkt_joint": joint["atmkt_joint"],
               "stopok": lim["stopok"],
               "price_improvement": mir["price_improvement"],
               "cancel_by_born": can["cancel_by_born"],
               "cost": cost["cost"]},
           "mirror_shortlist": cond["mirror_shortlist"],
           "entry_time_matched_control": mat["matched"],
           "uncond_by_entry_stamp": mat["uncond_by_stamp"],
           "delay5_atmkt_robustness": mat["delay5_atmkt"],
           "levelxm_stressed": lxm["levelxm"]}
    with open(os.path.join(D, "x5_RESULT.json"), "w") as f:
        json.dump(res, f)

    # console frontier
    def show(name, lst):
        print("\n--- %s ---" % name)
        print("%-26s %8s %7s %10s %11s %12s %6s %6s" %
              ("rung", "n", "surv%", "R/trade", "totalR", "bookR/cand", "stamp", "honest"))
        for r in lst:
            print("%-26s %8d %6.1f%% %+10.4f %+11.1f %+12.4f %6.0f %6s" %
                  (r["label"], r["n_taken"], 100 * r["survival"], r["mean_taken"],
                   r["total"], r["book_per_candidate"], r["entry_stamp_med"],
                   "YES" if r["honest"] else "no"))
    print("baseline (incumbent k=0, all %d core rows): %+.4f R/trade, %+.1f total"
          % (ncore, base, base * ncore))
    show("TOP by R/trade  (ALL rungs, look-ahead included)", front["top_by_R_per_trade_ALL"])
    show("TOP by R/trade  (HONEST only)", front["top_by_R_per_trade_HONEST"])
    show("TOP by TOTAL R  (HONEST only)", front["top_by_total_R_HONEST"])
    show("TOP by R/trade (HONEST + FILL-REALISTIC)", front["top_by_R_per_trade_HONEST_REALISTIC"])
    show("TOP by BOOK R/candidate (HONEST + FILL-REALISTIC)", front["top_by_book_HONEST_REALISTIC"])
    print("\nWROTE x5_RESULT.json")


if __name__ == "__main__":
    main()
