#!/usr/bin/env python3
"""l11 step 2a — derive the contract ANALYTICALLY before sweeping anything.

An exit at level L is worth, per candidate, exactly

      P(first-touch L)  x  ( L  -  E[ r_wall | first-touch L ] )

against the do-nothing baseline of marking at the 2-hour wall. That identity is what makes
a target or a stop pay: it is a bet that the level is a better place to stand than the
future. Measure both halves for every level and the contract designs itself.

Also measured, because a level is not a state:
  * the same table conditioned on WHEN the level was touched (early / mid / late)
  * the drift of the remaining path from the touch bar, so a trail can be priced
  * the conditional-drift surface g(t, r) = E[ r(t+k) - r(t) | mark r at bar t ]
"""
from __future__ import annotations

import json
import os

import numpy as np

import l11_lib
import l11_walk

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "L11_ANALYTIC_V1.json")

FAV_L = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0]
ADV_L = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0]


def first_touch(M, lvl, sign):
    hit = ((M >= lvl) if sign > 0 else (M <= lvl)) & ~np.isnan(M)
    any_ = hit.any(1)
    return np.where(any_, hit.argmax(1), -1), any_


def table(F, D, A, rem, name):
    n = len(rem)
    rw = A[np.arange(n), np.maximum(rem - 1, 0)].astype(np.float64)  # mark at wall
    rw[rem <= 0] = 0.0
    base = float(rw.mean())
    rows = {}
    for lvl in FAV_L:
        b, any_ = first_touch(F, lvl, +1)
        k = int(any_.sum())
        if k < 25:
            continue
        cond = rw[any_]
        # where the path stood at the touch bar is exactly lvl (first touch), so the
        # exit-vs-hold delta per touch is lvl - E[wall | touched]
        d = lvl - cond.mean()
        # split by touch time
        tb = b[any_]
        splits = {}
        for lab, sel in (("early_b1_10", tb <= 10), ("mid_b11_45", (tb > 10) & (tb <= 45)),
                         ("late_b46+", tb > 45)):
            if sel.sum() >= 20:
                splits[lab] = {"n": int(sel.sum()),
                               "E_wall": round(float(cond[sel].mean()), 5),
                               "delta": round(float(lvl - cond[sel].mean()), 5)}
        rows["T%+.2f" % lvl] = {
            "level": lvl, "p_touch": round(k / n, 5), "n_touch": k,
            "E_wall_given_touch": round(float(cond.mean()), 5),
            "delta_per_touch": round(float(d), 5),
            "value_per_candidate": round(float(k / n * d), 5),
            "median_touch_bar": float(np.median(tb)),
            "by_touch_time": splits,
        }
    srows = {}
    for lvl in ADV_L:
        b, any_ = first_touch(D, -lvl, -1)
        k = int(any_.sum())
        if k < 25:
            continue
        cond = rw[any_]
        d = -lvl - cond.mean()
        tb = b[any_]
        splits = {}
        for lab, sel in (("early_b1_10", tb <= 10), ("mid_b11_45", (tb > 10) & (tb <= 45)),
                         ("late_b46+", tb > 45)):
            if sel.sum() >= 20:
                splits[lab] = {"n": int(sel.sum()),
                               "E_wall": round(float(cond[sel].mean()), 5),
                               "delta": round(float(-lvl - cond[sel].mean()), 5)}
        srows["S-%.2f" % lvl] = {
            "level": -lvl, "p_touch": round(k / n, 5), "n_touch": k,
            "E_wall_given_touch": round(float(cond.mean()), 5),
            "delta_per_touch": round(float(d), 5),
            "value_per_candidate": round(float(k / n * d), 5),
            "median_touch_bar": float(np.median(tb)),
            "by_touch_time": splits,
        }
    return {"name": name, "n": n, "baseline_wall_mark": round(base, 6),
            "TARGET_LEVELS": rows, "STOP_LEVELS": srows}


def drift_surface(A, rem):
    """g(t, r) = E[r(min(t+k,end)) - r(t) | mark bucket r at bar t] for k = 15 and to wall."""
    n = len(rem)
    rw = A[np.arange(n), np.maximum(rem - 1, 0)].astype(np.float64)
    buckets = [(-99, -0.75), (-0.75, -0.5), (-0.5, -0.25), (-0.25, 0.0),
               (0.0, 0.25), (0.25, 0.5), (0.5, 1.0), (1.0, 2.0), (2.0, 99)]
    out = {}
    for t in (1, 3, 5, 10, 20, 30, 45, 60, 90):
        alive = rem > t
        if alive.sum() < 200:
            continue
        rt = A[:, t].astype(np.float64)
        row = {}
        for lo, hi in buckets:
            sel = alive & (rt >= lo) & (rt < hi) & ~np.isnan(rt)
            k = int(sel.sum())
            if k < 40:
                continue
            dw = rw[sel] - rt[sel]
            t15 = np.where(rem[sel] > t + 15, A[sel, np.minimum(t + 15, rem[sel] - 1)], rw[sel])
            d15 = t15.astype(np.float64) - rt[sel]
            row["r[%.2f,%.2f)" % (lo, hi)] = {
                "n": k,
                "to_wall": round(float(dw.mean()), 5),
                "to_wall_se": round(float(dw.std(ddof=1) / np.sqrt(k)), 5),
                "next15": round(float(d15.mean()), 5),
                "next15_se": round(float(d15.std(ddof=1) / np.sqrt(k)), 5)}
        out["t%d" % t] = row
    return out


def main():
    s = l11_lib.load()
    e = l11_walk.Engine(s)
    m = s.takeable
    F, D, A, rem = e.F[m], e.D[m], e.A[m], e.rem[m]
    fam = s.fam[m]
    out = {"lane": "l11", "pass": "ANALYTIC",
           "identity": "value_per_candidate = P(first-touch L) * (L - E[wall | touch L])",
           "baseline": "hold to the 2h wall, no target, no stop",
           "population": "TAKEABLE, fill REAL", "n": int(m.sum())}
    out["POOL"] = table(F, D, A, rem, "POOL")
    out["DRIFT_SURFACE_POOL"] = drift_surface(A, rem)
    out["by_family"] = {}
    for f in sorted(set(fam.tolist())):
        sel = fam == f
        if sel.sum() < 150:
            continue
        out["by_family"][f] = table(F[sel], D[sel], A[sel], rem[sel], f)
    with open(OUT, "w") as fh:
        json.dump(out, fh, indent=1)

    p = out["POOL"]
    print("POOL baseline wall mark %.5f  n=%d" % (p["baseline_wall_mark"], p["n"]))
    print("LVL    p_touch  E[wall|touch]  delta/touch  value/cand   med_bar")
    for k, v in p["TARGET_LEVELS"].items():
        print("%-7s %7.4f %13.4f %12.4f %11.5f %9.0f"
              % (k, v["p_touch"], v["E_wall_given_touch"], v["delta_per_touch"],
                 v["value_per_candidate"], v["median_touch_bar"]))
    for k, v in p["STOP_LEVELS"].items():
        print("%-7s %7.4f %13.4f %12.4f %11.5f %9.0f"
              % (k, v["p_touch"], v["E_wall_given_touch"], v["delta_per_touch"],
                 v["value_per_candidate"], v["median_touch_bar"]))


if __name__ == "__main__":
    main()
