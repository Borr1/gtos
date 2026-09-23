#!/usr/bin/env python3
"""e-coherence step 8 — ADJUDICATE the exit-contract level disagreement.

Same contract (+2R target / -1R stop), same population (24,142 takeable), two answers:
   L1  "declared T2/S1 = -0.0842"      L11 "INCUMBENT T2/S1 -0.084151"
   L2  "baseline -0.126526"            w0_WORKING_SET.fill_honest_walk_r = -0.126526
A 0.0424 R/trade gap on the single most-cited contract in the swarm.  Candidate causes,
each isolated: (i) the same-bar tie rule, (ii) whether the walk starts at the touch bar or
the bar after, (iii) policy_target_r (up to 505R on 1,229 rows) vs a flat 2.0R target,
(iv) whether a never-filled candidate books 0 or is dropped.
"""
import json, os, pickle, sys
import numpy as np
import pandas as pd

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import w0_ws  # noqa

df = pickle.load(open("/tmp/ecoh/e_base.pkl", "rb"))
keep = df["born"] != "past_stop"
sub = df.loc[keep]
keys = set(zip(sub["candidate_id"], sub["decision_time_utc"]))
tgt_map = dict(zip(zip(sub["candidate_id"], sub["decision_time_utc"]), sub["policy_target_r"]))
OUT = {}


def walk(fav, adv, cls, start, target, tie_stop_first):
    n = len(cls)
    for i in range(start, n):
        f, a = fav[i], adv[i]
        hs, ht = a <= -1.0, f >= target
        if hs and ht:
            return (-1.0 if tie_stop_first else target), "tie"
        if hs:
            return -1.0, "stop"
        if ht:
            return target, "target"
    return cls[n - 1], "wall"


variants = {}
for tie in (True, False):
    for tgtmode in ("policy", "flat2"):
        for startmode in ("at_touch", "after_touch", "bar1_no_fill_req"):
            variants[(tie, tgtmode, startmode)] = []

nofill = 0
for rp in w0_ws.iter_rpaths():
    kk = (rp["candidate_id"], rp["decision_time_utc"])
    if kk not in keys:
        continue
    fav, adv, cls, off = rp["fav"], rp["adv"], rp["cls"], rp["off"]
    n = len(cls)
    # first bar at which the entry price itself is traded (fav>=0>=adv brackets entry)
    touch = None
    for i in range(n):
        if fav[i] >= 0.0 >= adv[i]:
            touch = i
            break
    if touch is None:
        nofill += 1
    pol = tgt_map[kk]
    for (tie, tgtmode, startmode), acc in variants.items():
        target = 2.0 if tgtmode == "flat2" else float(pol)
        if startmode == "bar1_no_fill_req":
            start = 0
        else:
            if touch is None:
                acc.append(0.0)
                continue
            start = touch if startmode == "at_touch" else touch + 1
            if start >= n:
                acc.append(0.0)
                continue
        r, _ = walk(fav, adv, cls, start, target, tie)
        acc.append(r)

rows = []
for (tie, tgtmode, startmode), acc in variants.items():
    a = np.array(acc, dtype=float)
    rows.append({"tie_stop_first": tie, "target": tgtmode, "start": startmode,
                 "n": len(a), "mean": round(float(a.mean()), 6)})
rows.sort(key=lambda r: r["mean"])
OUT["variant_grid"] = rows
OUT["n_never_filled"] = nofill
OUT["reference_points"] = {
    "working_set_fill_honest_walk_r_mean": round(float(sub["fill_honest_walk_r"].mean()), 6),
    "L1_and_L11_declared_T2S1": -0.084151,
    "L2_baseline": -0.126526,
}
# isolate each factor from the canonical (tie=True, policy, at_touch)
base = {r["mean"] for r in rows if r["tie_stop_first"] and r["target"] == "policy" and r["start"] == "at_touch"}
b = list(base)[0]
iso = {}
for r in rows:
    tags = []
    if r["tie_stop_first"] is not True:
        tags.append("tie=target_first")
    if r["target"] != "policy":
        tags.append("target=flat2")
    if r["start"] != "at_touch":
        tags.append("start=" + r["start"])
    if len(tags) == 1:
        iso[tags[0]] = round(r["mean"] - b, 6)
OUT["single_factor_effects_vs_canonical"] = {"canonical_mean": round(b, 6), **iso}

json.dump(OUT, open(f"{D}/E_EXITADJ_V1.json", "w"), indent=1)
print(json.dumps(OUT["reference_points"]))
print("never filled:", nofill)
for r in rows:
    print(f"  tie_stop={str(r['tie_stop_first']):5s} target={r['target']:6s} start={r['start']:18s} n={r['n']:6d} mean={r['mean']:+.6f}")
print(json.dumps(OUT["single_factor_effects_vs_canonical"]))
