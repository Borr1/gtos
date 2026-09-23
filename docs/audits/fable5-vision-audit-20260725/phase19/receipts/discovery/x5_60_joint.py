#!/usr/bin/env python3
"""x5_60_joint - the joint optimum, priced on ONE row set, with the ablation.

Three questions closed here:

  1. On the geometry-free cell (born_at_limit, where L7's +0.0670 delay lever lives), what do
     DELAY, CANCEL and a CONFIRMATION FILTER do jointly?  Standalone values are NOT summable.
  2. On the estate's own LIMIT contract, what is the joint optimum of
     (placement offset p) x (cancel the first-bar fill) x (confirmation)?
  3. Where exactly, minute by minute, does the signal's directional content cross zero?

Emits x5_JOINT_V1.json.
"""
import json
import os
import sys
import time

import numpy as np

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import x5_lib as X  # noqa: E402

OUT = os.path.join(D, "x5_JOINT_V1.json")
KS = [-14, -10, -5, -1, 0, 1, 2, 3, 5, 8, 10, 15, 20, 30, 45, 60]
PLACE = [0, 1, 2, 3, 5, 8, 10, 15, 20, 30]


def main():
    t0 = time.time()
    w = X.W()
    core = w.core
    n = w.n
    atm = core & (w.born == 0)
    cancel = (w.bte == 1)
    out = {"meta": {"n_core": int(core.sum()), "n_atmkt": int(atm.sum())}}

    # ---------- 1. at-market cell: DELAY x CANCEL x CONFIRMATION, same rows ----------
    # confirmation filter, fully honest: price has held theta R in the trade's direction for
    # N minutes AFTER the M15 close (POST), evaluated at the entry minute.
    st = np.array(list(range(-15, 61)), dtype=np.int32)
    cols = [X.sidx(s) for s in st]
    Cw = w.C[:, cols].astype(np.float64)
    e0 = w.entry_at(0)
    progp = w.sgn[:, None] * (Cw - e0[:, None]) / w.d0[:, None]
    valid = ~np.isnan(Cw) & core[:, None]

    def conf_at(k, th, direction=1):
        """Is the POST condition satisfied at the entry stamp k-1 (i.e. knowable at entry)?"""
        j = int(np.where(st == (k - 1))[0][0])
        return (direction * progp[:, j] >= th) & valid[:, j]

    tab1 = []
    for k in KS:
        o = X.rungs_walk(w, k, horizon="MATCH", denom="SHIFTSTOP", contract="INC")
        r = o["r"]
        g = atm & o["good"] & ~np.isnan(r)
        base = X.rungs_walk(w, 0, horizon="MATCH", denom="SHIFTSTOP", contract="INC")
        gb = g & base["good"] & ~np.isnan(base["r"])
        cells = {}
        for use_e in (0, 1):
            rr = r if use_e else base["r"]
            for use_c in (0, 1):
                mc = gb & (~cancel if use_c else np.ones(n, bool))
                for use_f, th in ((0, None), (1, 0.0), (2, 0.10)):
                    if use_f == 0:
                        mf = mc
                    else:
                        cf = conf_at(k if use_e else 0, th) if k > 0 or not use_e else \
                             conf_at(1, th)
                        mf = mc & cf
                    if mf.sum() < 30:
                        continue
                    cells["E%d|C%d|F%d" % (use_e, use_c, use_f)] = {
                        "n": int(mf.sum()),
                        "mean": float(rr[mf].mean()),
                        "per_candidate": float(rr[mf].sum() / max(1, int(gb.sum())))}
        rec = {"k": k, "n_base": int(gb.sum()), "cells": cells}
        b = cells["E0|C0|F0"]["per_candidate"]
        for nm in ("E1|C0|F0", "E0|C1|F0", "E1|C1|F0", "E1|C1|F1", "E1|C1|F2"):
            if nm in cells:
                rec[nm + "_delta"] = cells[nm]["per_candidate"] - b
        if "E1|C0|F0" in cells and "E0|C1|F0" in cells and "E1|C1|F0" in cells:
            add = rec["E1|C0|F0_delta"] + rec["E0|C1|F0_delta"]
            rec["naive_sum_delta"] = add
            rec["actual_joint_delta"] = rec["E1|C1|F0_delta"]
            rec["overcount"] = add - rec["E1|C1|F0_delta"]
        tab1.append(rec)
    out["atmkt_joint"] = tab1
    print("1 done %.1fs" % (time.time() - t0), flush=True)

    # ---------- 2. LIMIT contract joint: placement x cancel x confirmation ----------
    lo, hi = -15, X.S_HI
    c2 = list(range(X.sidx(lo), X.sidx(hi) + 1))
    HH = w.H[:, c2].astype(np.float64); LL = w.L[:, c2].astype(np.float64)
    CC = w.C[:, c2].astype(np.float64)
    sg = w.sgn[:, None]; dv = w.d0[:, None]
    favb = np.maximum(sg * (HH - w.entry0[:, None]), sg * (LL - w.entry0[:, None])) / dv
    advb = np.minimum(sg * (HH - w.entry0[:, None]), sg * (LL - w.entry0[:, None])) / dv
    clsb = sg * (CC - w.entry0[:, None]) / dv
    okb = ~np.isnan(CC)
    stampv = np.arange(lo, hi + 1)
    tab2 = []
    for p in PLACE:
        j0 = int(np.searchsorted(stampv, p))
        touch = (advb <= 0.0) & okb
        touch[:, :j0] = False
        has = touch.any(axis=1)
        fj = touch.argmax(axis=1)
        fill_stamp = np.where(has, stampv[fj], 10 ** 6)
        start = fill_stamp + 1
        vmask = (stampv[None, :] >= start[:, None]) & \
                (stampv[None, :] <= start[:, None] + 119) & okb & core[:, None]
        r, reason, _ = X.walk(np.nan_to_num(favb, nan=-9e9), np.nan_to_num(advb, nan=9e9),
                              clsb, vmask, "INC", tgt=np.full(n, 2.0))
        r = np.where(has & core, np.nan_to_num(r, nan=0.0), 0.0)
        filled = has & core
        firstbar = filled & (fill_stamp == p)
        nc = int(core.sum())
        cells = {}
        for use_c in (0, 1):
            keep = filled & (~firstbar if use_c else np.ones(n, bool))
            cells["C%d" % use_c] = {"n": int(keep.sum()),
                                    "per_candidate": float(r[keep].sum() / nc),
                                    "mean_taken": float(r[keep].mean()) if keep.sum() else None}
        bt = X.dayblock_boot(np.where(filled & ~firstbar, r, 0.0)[core], w.dayi[core],
                             B=1000, seed=555)
        tab2.append({"p": p, "n_core": nc, "fill_rate": float(filled[core].mean()),
                     "cells": cells, "cancel_delta": cells["C1"]["per_candidate"] -
                     cells["C0"]["per_candidate"], "boot_cancel_book": bt})
        print("  limit p=%d %.1fs" % (p, time.time() - t0), flush=True)
    # ablation on the limit contract: place-delay x cancel, one row set
    b00 = tab2[0]["cells"]["C0"]["per_candidate"]
    for t in tab2:
        t["delay_only_delta"] = t["cells"]["C0"]["per_candidate"] - b00
        t["cancel_only_delta_at_p0"] = tab2[0]["cells"]["C1"]["per_candidate"] - b00
        t["joint_delta"] = t["cells"]["C1"]["per_candidate"] - b00
        t["naive_sum"] = t["delay_only_delta"] + t["cancel_only_delta_at_p0"]
        t["overcount"] = t["naive_sum"] - t["joint_delta"]
    out["limit_joint"] = tab2
    print("2 done %.1fs" % (time.time() - t0), flush=True)

    # ---------- 3. the minute-by-minute directional-content curve ----------
    curve = []
    for k in range(-14, 16):
        ek = w.entry_at(k)
        good = core & ~np.isnan(ek)
        loK, hiK = k, min(k + 119, X.S_HI)
        cc = list(range(X.sidx(loK), X.sidx(hiK) + 1))
        hh = w.H[:, cc].astype(np.float64); ll = w.L[:, cc].astype(np.float64)
        cl = w.C[:, cc].astype(np.float64)
        for flip in (0, 1):
            s = (w.sgn if not flip else -w.sgn)[:, None]
            e = ek[:, None]; d = w.d0[:, None]
            hr = s * (hh - e) / d; lr = s * (ll - e) / d
            fav = np.where(hr >= lr, hr, lr); adv = np.where(hr >= lr, lr, hr)
            cls = s * (cl - e) / d
            v = (~np.isnan(cl)) & good[:, None]
            rr, _, _ = X.walk(np.nan_to_num(fav, nan=-9e9), np.nan_to_num(adv, nan=9e9),
                              cls, v, "INC", tgt=np.full(n, 2.0))
            rr[~good] = np.nan
            if flip == 0:
                ro = rr
            else:
                ri = rr
        m = good & atm & ~np.isnan(ro) & ~np.isnan(ri)
        info = (ri - ro) / 2.0
        bt = X.dayblock_boot(info[m], w.dayi[m], B=600, seed=900 + k + 20)
        curve.append({"k": k, "n": int(m.sum()), "orig": float(ro[m].mean()),
                      "inv": float(ri[m].mean()), "info": float(info[m].mean()),
                      "info_lo": bt["lo"], "info_hi": bt["hi"]})
    out["info_curve_atmkt"] = curve
    with open(OUT, "w") as f:
        json.dump(out, f)
    print("WROTE %s (%.1fs)" % (OUT, time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
