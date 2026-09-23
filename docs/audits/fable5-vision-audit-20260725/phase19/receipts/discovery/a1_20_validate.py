#!/usr/bin/env python3
"""a1 step 20 - prove the substrate before anything is built on it.

V1  at-market anchor: close of stamp D-1 == entry_price to float equality
V2  reproduce h5's K0_STOPONLY / K5_STOPONLY per row (h5's bar-count convention)
V3  reproduce the published cost bases (B1_COSTJOIN_V1)
V4  reproduce x4's c0 split on January (a different substrate, so a sign/size check)
V5  quantify my wall-clock-stamp convention against h5's bar-count convention
V6  coverage of the confirm minute (x4 measured 97.75 % of rows have a bar stamped D)
"""
from __future__ import annotations
import json
import os
import sys

import numpy as np

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import a1_lib as A  # noqa: E402

MONTHS = ["202601", "202602", "202603", "202604", "202605"]
OUT = {}


def h5_barcount_walk(M, k, target=None, stop=-1.0):
    """Replicate e_lib/e_build_atmkt EXACTLY: path = available bars stamped in (D, D+120min],
    entry = close of path bar k (1-based), walk from path bar k+1 to the path end."""
    n = M.n
    s0, s1 = A.sidx(1), A.sidx(120) + 1
    fav = M.FAV[:, s0:s1]
    adv = M.ADV[:, s0:s1]
    cls = M.RC[:, s0:s1]
    raw = M.C[:, s0:s1]                      # NaN marks an absent bar
    r = np.zeros(n)
    reason = np.full(n, 2)
    ok = np.ones(n, dtype=bool)
    for i in range(n):
        idx = np.where(~np.isnan(raw[i]))[0]
        if len(idx) <= k:
            ok[i] = False
            continue
        ck = cls[i, idx[k - 1]] if k >= 1 else 0.0
        f = fav[i, idx[k:]] - ck
        a = adv[i, idx[k:]] - ck
        c = cls[i, idx[k:]] - ck
        hs = np.where(a <= stop + A.TOL)[0]
        ht = np.where(f >= (target - A.TOL))[0] if target is not None else np.array([], int)
        js = hs[0] if len(hs) else 10 ** 9
        jt = ht[0] if len(ht) else 10 ** 9
        if js <= jt and js < 10 ** 9:
            r[i] = stop
            reason[i] = 0
        elif jt < js:
            r[i] = target
            reason[i] = 1
        else:
            r[i] = c[-1]
    return r, reason, ok


def main():
    # ---------------- V1 / V6 / V3
    v1 = {}
    v6 = {}
    v3 = {}
    Ms = {}
    for mm in MONTHS:
        M = A.Month(mm)
        Ms[mm] = M
        v1[mm] = {"n": M.n,
                  "max_abs_anchor_R": float(np.nanmax(np.abs(M.anchor))),
                  "rows_anchor_gt_1e-9": int((np.abs(M.anchor) > 1e-9).sum())}
        v6[mm] = {"bar_stamped_D_present": float((~np.isnan(M.C[:, A.sidx(0)])).mean()),
                  "trigger_bar_range_present": float(np.isfinite(M.trig_range).mean()),
                  "geo_median": float(np.nanmedian(M.geo))}
        v3[mm] = {"cost_frozen": float(M.cost_frozen.mean()),
                  "cost_true": float(M.cost_true.mean()),
                  "cost_true_hour3": float(M.cost_hour3.mean()),
                  "cost_hour4_w_swap": float(M.cost_hour4.mean()),
                  "cost_h1_4term": float(np.nanmean(M.cost_h1)) if M.has_h1.any() else None,
                  "has_h1_share": float(M.has_h1.mean()),
                  "mean_bps_h1": float(np.nanmean(M.cost_h1 * M.rdp * 1e4)) if M.has_h1.any() else None}
    OUT["V1_at_market_anchor"] = v1
    OUT["V6_confirm_minute_coverage"] = v6
    OUT["V3_cost_bases"] = v3

    # 3-month pooled cost check against B1_COSTJOIN_V1
    g = {"cost_true": [], "cost_true_hour": [], "cost_h1": [], "rdp": []}
    for mm in MONTHS[:3]:
        M = Ms[mm]
        g["cost_true"].append(M.cost_true)
        g["cost_true_hour"].append(M.cost_hour3)
        g["cost_h1"].append(M.cost_h1)
        g["rdp"].append(M.rdp)
    cat = {k: np.concatenate(v) for k, v in g.items()}
    pub = json.load(open(os.path.join(D, "B1_COSTJOIN_V1.json")))["bases"]
    OUT["V3_vs_b1_3month"] = {
        "n": int(len(cat["rdp"])), "published_n": pub and 43755,
        "cost_true_mean_R": float(cat["cost_true"].mean()),
        "published_cost_true": pub["swarm_flat_cost_true"]["mean_R"],
        "cost_true_hour_mean_R": float(cat["cost_true_hour"].mean()),
        "published_cost_true_hour": pub["b1_headline_cost_true_hour"]["mean_R"],
        "cost_h1_mean_R": float(np.nanmean(cat["cost_h1"])),
        "published_cost_h1": pub["h1_broker_true_4term"]["mean_R"],
        "cost_h1_mean_bps": float(np.nanmean(cat["cost_h1"] * cat["rdp"] * 1e4)),
        "published_cost_h1_bps": pub["h1_broker_true_4term"]["mean_bps"],
    }

    # ---------------- V2 reproduce h5's prewalked columns
    v2 = {}
    for mm in MONTHS[:3]:
        M = Ms[mm]
        rec = {}
        for k, col in ((0, "K0_STOPONLY"), (5, "K5_STOPONLY")):
            pubv = np.array([np.nan if v is None else v for v in M.meta[col]], dtype=float)
            r, _, ok = h5_barcount_walk(M, k, target=None, stop=-1.0)
            m = ok & np.isfinite(pubv)
            diff = np.abs(r[m] - pubv[m])
            rec[col] = {"n_compared": int(m.sum()),
                        "max_abs_diff": float(diff.max()) if m.sum() else None,
                        "mean_abs_diff": float(diff.mean()) if m.sum() else None,
                        "share_within_1e-6": float((diff < 1e-6).mean()) if m.sum() else None,
                        "mine_mean": float(r[m].mean()), "published_mean": float(pubv[m].mean())}
        for k, col in ((0, "K0_TRAIL025"), (5, "K5_TRAIL025")):
            pubv = np.array([np.nan if v is None else v for v in M.meta[col]], dtype=float)
            rec[col] = {"published_mean": float(np.nanmean(pubv))}
        v2[mm] = rec
    OUT["V2_reproduce_h5_prewalk"] = v2

    # ---------------- V5 stamp convention vs bar-count convention
    v5 = {}
    for mm in MONTHS[:3]:
        M = Ms[mm]
        rs, _, _ = M.walk(5, target=None, stop=-1.0)      # my wall-clock D+5min
        rb, _, ok = h5_barcount_walk(M, 5, target=None)   # h5's 5-bar
        v5[mm] = {"stamp_mean": float(rs.mean()), "barcount_mean": float(rb[ok].mean()),
                  "delta": float(rs.mean() - rb[ok].mean()),
                  "share_identical": float((np.abs(rs[ok] - rb[ok]) < 1e-9).mean())}
    OUT["V5_convention_delta"] = v5

    # ---------------- V4 x4's confirm split, at-market cohort, January
    M = Ms["202601"]
    r0, _, _ = M.walk(0, target=2.0, stop=-1.0)     # shipped-style barrier, at-market
    for th in (-0.05, -0.15, -0.25):
        keep = M.c0 > th
        OUT.setdefault("V4_x4_confirm_split_jan", {})["c0>%.2f" % th] = {
            "kept_n": int(keep.sum()), "kept_gross_R": float(r0[keep].mean()),
            "refused_n": int((~keep).sum()), "refused_gross_R": float(r0[~keep].mean()),
            "gap": float(r0[keep].mean() - r0[~keep].mean())}
    OUT["V4_x4_confirm_split_jan"]["baseline_gross_R_k0_target2"] = float(r0.mean())

    with open(os.path.join(D, "A1_VALIDATE_V1.json"), "w") as f:
        json.dump(OUT, f, indent=1)
    print(json.dumps(OUT, indent=1)[:6000])


if __name__ == "__main__":
    main()
