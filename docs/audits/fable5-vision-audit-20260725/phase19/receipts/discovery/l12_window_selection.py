#!/usr/bin/env python3
"""l12 step 5: window-level selection — the faithful form of what the scheduler does.

1,969 decision windows, median 13 candidates each. The scheduler ranks WITHIN a window
and the finalizer takes the top. So rank within window and take the top-1 (and top-2/3)
under each ablation of the score, and measure what the selection earned.

n = 1,969 selections per arm, on the same windows, so the arms are paired.
"""
import gzip
import json
import math
import os
import random
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import w0_ws  # noqa: E402

ANCHOR = os.path.join(HERE, "w0cap2_DECISION_ANCHOR_V1.jsonl.gz")

W_EV, W_P, W_CONF, W_COMP, W_FILL, W_XFER, W_COST = 0.55, 1.20, 0.20, 0.15, 0.10, 6.00, 0.80


def build_scores(r, spread_div=1.0):
    ev = r.get("candidate_ev_r")
    p = r.get("candidate_probability")
    c0 = r.get("cost_r")
    sp = r.get("spread_r")
    f = r.get("execution_fill_probability")
    k = r.get("source_completeness")
    conf = r.get("candidate_confidence")
    if None in (ev, p, c0, k, conf) or sp is None:
        return None
    c = c0 - sp + sp / spread_div
    if f is None:
        f = 0.0
    k = max(0.0, min(1.0, float(k)))
    pm = max(0.0, min(1.0, float(p)))
    fm = max(0.0, min(1.0, float(f)))
    net = ev - c
    base = W_EV * ev + W_P * (p - 0.50) + W_CONF * conf + W_COMP * k + W_FILL * f
    xfer = W_XFER * max(0.0, net) * pm * fm * k
    return {
        "A_as_is": base + xfer - W_COST * c,
        "B_single_charge_cost": base + xfer,
        "C_no_double_probability": base + W_XFER * max(0.0, net) * fm * k - W_COST * c,
        "D_no_fill_multiplier": base + W_XFER * max(0.0, net) * pm * k - W_COST * c,
        "E_no_double_p_no_fill": base + W_XFER * max(0.0, net) * k - W_COST * c,
        "F_plain_expected_net": net,
        "G_plain_ev": ev,
        "H_plain_probability": p,
        "I_neg_cost": -c,
        "L_neg_spread": -sp,
        "M_ev_over_cost": ev / (c + 1e-6),
    }


def summarise(vals):
    if not vals:
        return None
    n = len(vals)
    m = sum(vals) / n
    sd = (sum((x - m) ** 2 for x in vals) / max(1, n - 1)) ** 0.5
    return {"n": n, "mean": round(m, 6), "sd": round(sd, 4),
            "se": round(sd / math.sqrt(n), 5),
            "t": round(m / (sd / math.sqrt(n)), 3) if sd else None,
            "win": round(sum(1 for x in vals if x > 0) / n, 5),
            "sum": round(sum(vals), 2)}


def main():
    rows = w0_ws.load()
    by = {}
    for r in rows:
        by[(r.get("candidate_id"), r.get("decision_time_utc"))] = r
    with gzip.open(ANCHOR, "rt") as fh:
        for line in fh:
            if line.strip():
                a = json.loads(line)
                t = by.get((a.get("candidate_id"), a.get("decision_time_utc")))
                if t is not None:
                    t["_mkt_r"] = a.get("mkt_r_prev_close")

    out = {"arms": {}, "meta": {}}
    for spread_div, tag in ((1.0, "FROZEN_COST"), (7.3, "SPREAD_DIV_7p3")):
        for popname in ("ALL", "CLEAN"):
            usable = []
            for r in rows:
                if popname == "CLEAN" and not (
                        r.get("_mkt_r") is not None and r["_mkt_r"] > -1.0):
                    continue
                s = build_scores(r, spread_div)
                if s is None:
                    continue
                r["_s"] = s
                usable.append(r)
            wins = defaultdict(list)
            for r in usable:
                wins[r["decision_time_utc"]].append(r)
            keys = list(usable[0]["_s"].keys())
            arm = {"n_windows": len(wins), "n_cands": len(usable), "picks": {}}
            for key in keys:
                for topn in (1, 2, 3):
                    g, h, pw = [], [], []
                    for _, cands in wins.items():
                        sel = sorted(cands, key=lambda r: -r["_s"][key])[:topn]
                        for r in sel:
                            if r.get("gross_r") is not None:
                                g.append(r["gross_r"])
                            if r.get("fill_honest_walk_r") is not None:
                                h.append(r["fill_honest_walk_r"])
                            if r.get("plain_walk_r") is not None:
                                pw.append(r["plain_walk_r"])
                    arm["picks"]["%s_top%d" % (key, topn)] = {
                        "gross_r": summarise(g),
                        "fill_honest_walk_r": summarise(h),
                        "plain_walk_r": summarise(pw)}
            # random within-window baseline
            rng = random.Random(11)
            for topn in (1, 2, 3):
                acc_g, acc_h = [], []
                for _ in range(50):
                    g, h = [], []
                    for _, cands in wins.items():
                        sel = rng.sample(cands, min(topn, len(cands)))
                        for r in sel:
                            if r.get("gross_r") is not None:
                                g.append(r["gross_r"])
                            if r.get("fill_honest_walk_r") is not None:
                                h.append(r["fill_honest_walk_r"])
                    acc_g.append(sum(g) / len(g))
                    acc_h.append(sum(h) / len(h))
                arm["picks"]["Z_random_top%d" % topn] = {
                    "gross_r": {"n": len(g), "mean": round(sum(acc_g) / len(acc_g), 6)},
                    "fill_honest_walk_r": {"n": len(h),
                                           "mean": round(sum(acc_h) / len(acc_h), 6)}}
            arm["population_mean"] = {
                "gross_r": round(sum(r["gross_r"] for r in usable
                                     if r.get("gross_r") is not None) /
                                 sum(1 for r in usable if r.get("gross_r") is not None), 6),
                "fill_honest_walk_r": round(
                    sum(r["fill_honest_walk_r"] for r in usable
                        if r.get("fill_honest_walk_r") is not None) /
                    sum(1 for r in usable if r.get("fill_honest_walk_r") is not None), 6)}
            out["arms"]["%s__%s" % (tag, popname)] = arm

    dest = os.path.join(HERE, "L12_WINDOW_SELECTION_V1.json")
    with open(dest, "w") as fh:
        json.dump(out, fh, indent=1)

    for arm_name, arm in out["arms"].items():
        print("== %s  windows=%d cands=%d popmean g=%.4f h=%.4f" % (
            arm_name, arm["n_windows"], arm["n_cands"],
            arm["population_mean"]["gross_r"],
            arm["population_mean"]["fill_honest_walk_r"]))
        print("   %-26s %9s %9s %7s | %9s %9s %7s" % (
            "score(top1)", "gross", "t", "win", "honest", "t", "win"))
        for key in sorted(arm["picks"]):
            if not key.endswith("_top1"):
                continue
            v = arm["picks"][key]
            g, h = v["gross_r"], v["fill_honest_walk_r"]
            print("   %-26s %9.4f %9s %7s | %9.4f %9s %7s" % (
                key[:-5], g["mean"], g.get("t"), g.get("win"),
                h["mean"], h.get("t"), h.get("win")))
    print("WROTE", dest)


if __name__ == "__main__":
    main()
