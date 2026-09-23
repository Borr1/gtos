#!/usr/bin/env python3
"""e-coherence 8b — same adjudication, using the working set's OWN validated
bars_to_entry_touch (1-based) rather than a re-derived touch rule."""
import json, os, pickle, sys
import numpy as np

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import w0_ws  # noqa

df = pickle.load(open("/tmp/ecoh/e_base.pkl", "rb"))
keep = df["born"] != "past_stop"
sub = df.loc[keep]
K = list(zip(sub["candidate_id"], sub["decision_time_utc"]))
touch = dict(zip(K, sub["bars_to_entry_touch"]))
pol = dict(zip(K, sub["policy_target_r"]))
keys = set(K)
OUT = {}


def walk(fav, adv, cls, start, target, tie_stop_first):
    n = len(cls)
    for i in range(start, n):
        f, a = fav[i], adv[i]
        hs, ht = a <= -1.0, f >= target
        if hs and ht:
            return -1.0 if tie_stop_first else target
        if hs:
            return -1.0
        if ht:
            return target
    return cls[n - 1]


CFG = [("canonical_touchbar_policy_stopfirst", True, "policy", 0),
       ("touchbar_flat2", True, "flat2", 0),
       ("touchbar_targetfirst", False, "policy", 0),
       ("bar_after_touch", True, "policy", 1),
       ("no_fill_requirement_bar1", True, "policy", "b1"),
       ("no_fill_req_flat2", True, "flat2", "b1")]
acc = {c[0]: [] for c in CFG}
drop_unfilled = {c[0]: [] for c in CFG}
for rp in w0_ws.iter_rpaths():
    kk = (rp["candidate_id"], rp["decision_time_utc"])
    if kk not in keys:
        continue
    fav, adv, cls = rp["fav"], rp["adv"], rp["cls"]
    n = len(cls)
    t = touch[kk]
    tgt_pol = float(pol[kk])
    for name, tie, tm, off in CFG:
        target = 2.0 if tm == "flat2" else tgt_pol
        if off == "b1":
            start = 0
        else:
            if t is None or (isinstance(t, float) and np.isnan(t)):
                acc[name].append(0.0)
                continue
            start = int(t) - 1 + off
            if start >= n:
                acc[name].append(0.0)
                continue
        r = walk(fav, adv, cls, start, target, tie)
        acc[name].append(r)
        drop_unfilled[name].append(r)

rows = []
for name, _, _, _ in CFG:
    a = np.array(acc[name], dtype=float)
    b = np.array(drop_unfilled[name], dtype=float)
    rows.append({"config": name, "n": len(a), "mean_unfilled_books_0": round(float(a.mean()), 6),
                 "n_filled_only": len(b), "mean_drop_unfilled": round(float(b.mean()), 6)})
OUT["configs"] = rows
OUT["reference"] = {"working_set_fill_honest_walk_r": round(float(sub["fill_honest_walk_r"].mean()), 6),
                    "L1_L11_declared_T2S1": -0.084151, "L2_baseline": -0.126526,
                    "L11_HOLD_TO_WALL": -0.038647}
# HOLD to wall on the same rows, both conventions
hold_h, hold_b = [], []
for rp in w0_ws.iter_rpaths():
    kk = (rp["candidate_id"], rp["decision_time_utc"])
    if kk not in keys:
        continue
    cls = rp["cls"]
    t = touch[kk]
    hold_b.append(cls[-1])
    if t is None or (isinstance(t, float) and np.isnan(t)):
        hold_h.append(0.0)
    else:
        s = int(t) - 1
        hold_h.append(cls[-1] - (0.0 if s == 0 else 0.0))  # path R already measured from entry
OUT["hold_to_wall"] = {"n": len(hold_h),
                       "mean_fill_honest_unfilled_0": round(float(np.mean(hold_h)), 6),
                       "mean_no_fill_requirement": round(float(np.mean(hold_b)), 6)}
json.dump(OUT, open(f"{D}/E_EXITADJ_V2.json", "w"), indent=1)
print(json.dumps(OUT["reference"]))
for r in rows:
    print(f"  {r['config']:36s} unfilled=0 -> {r['mean_unfilled_books_0']:+.6f}   drop-unfilled -> {r['mean_drop_unfilled']:+.6f} (n={r['n_filled_only']})")
print(json.dumps(OUT["hold_to_wall"]))
