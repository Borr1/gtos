#!/usr/bin/env python3
"""x5_45 - three corrections and the substitution test the lane turns on.

A. STOPOK.  Under the STRUCTSTOP contract a row whose structural stop is on the WRONG side
   of the rung's entry (born_past_stop, and any row the market has run through) is not a
   trade at all -- the -1R level ends up on the opposite side of the market from the stop.
   Every STRUCTSTOP claim is restated on the tradeable subset.

B. LIMIT-FILL, the estate's own contract.  A resting order at `entry_price`, PLACED at
   stamp p, filled at the first bar at or after p whose adverse extreme reaches the level,
   walked 2R/-1R in d0 from the NEXT bar, booked 0.0 R if it never fills.  p=0 is the
   shipped contract.  The 60-second cancel is then exactly "refuse the fill that happens on
   the first bar after placement".  This is the contract in which l8 measured the cancel's
   93.8 % recovery, so it is the only contract in which "is the cancel still needed?" can
   be answered.

C. LEVELXM.  x5_35's LEVELX filled AT the level after the price had been beyond it for N
   minutes, which is not a fill anyone can get.  LEVELXM re-prices the same condition with
   a MARKET entry at the qualifying minute.

Emits x5_LIMIT_V1.json.
"""
import json
import os
import sys
import time

import numpy as np

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import x5_lib as X  # noqa: E402

OUT = os.path.join(D, "x5_LIMIT_V1.json")
PLACE = [0, 1, 2, 3, 5, 8, 10, 15, 20, 30, 45, 60]


def main():
    t0 = time.time()
    w = X.W()
    core = w.core
    n = w.n
    out = {"meta": {"n_core": int(core.sum())}}

    # ------------------------------------------------------------------ A. STOPOK
    A = []
    for k in X.RUNGS:
        ek = w.entry_at(k)
        stopok = core & (w.sgn * (ek - w.stop) > 0)
        o = X.rungs_walk(w, k, horizon="MATCH", denom="STRUCTSTOP", contract="INC")
        os_ = X.rungs_walk(w, k, horizon="MATCH", denom="SHIFTSTOP", contract="INC")
        g = core & o["good"] & ~np.isnan(o["r"])
        gs = g & stopok
        A.append({"k": k, "n_core": int(g.sum()), "n_stopok": int(gs.sum()),
                  "stopok_share": float(stopok[g].mean()),
                  "structstop_core": float(o["r"][g].mean()),
                  "structstop_stopok": float(o["r"][gs].mean()),
                  "shiftstop_core": float(np.nanmean(os_["r"][g])),
                  "shiftstop_stopok": float(np.nanmean(os_["r"][gs]))})
    out["stopok"] = A
    print("A done %.1fs" % (time.time() - t0), flush=True)

    # ------------------------------------------------------------------ B. LIMIT-FILL
    e0 = w.entry0.astype(np.float64)
    lo, hi = -15, X.S_HI
    cols = list(range(X.sidx(lo), X.sidx(hi) + 1))
    HH = w.H[:, cols].astype(np.float64); LL = w.L[:, cols].astype(np.float64)
    CC = w.C[:, cols].astype(np.float64)
    sg = w.sgn[:, None]; dv = w.d0[:, None]
    favb = np.maximum(sg * (HH - e0[:, None]), sg * (LL - e0[:, None])) / dv
    advb = np.minimum(sg * (HH - e0[:, None]), sg * (LL - e0[:, None])) / dv
    clsb = sg * (CC - e0[:, None]) / dv
    okb = ~np.isnan(CC)
    stampv = np.arange(lo, hi + 1)
    B = []
    for p in PLACE:
        j0 = np.searchsorted(stampv, p)
        touch = (advb <= 0.0) & okb
        touch[:, :j0] = False
        has = touch.any(axis=1)
        fj = np.where(has, touch.argmax(axis=1), -1)
        # walk from the bar AFTER the fill bar, 120 bars
        start = np.where(has, stampv[np.clip(fj, 0, len(stampv) - 1)] + 1, 10 ** 6)
        vmask = (stampv[None, :] >= start[:, None]) & \
                (stampv[None, :] <= start[:, None] + 119) & okb & core[:, None]
        fav = np.nan_to_num(favb, nan=-9e9); adv = np.nan_to_num(advb, nan=9e9)
        r, reason, ebar = X.walk(fav, adv, clsb, vmask, "INC", tgt=np.full(n, 2.0))
        r = np.where(has & core, np.nan_to_num(r, nan=0.0), 0.0)
        filled = has & core
        first_bar_fill = filled & (stampv[np.clip(fj, 0, len(stampv) - 1)] == p)
        g = core
        rec = {"place_stamp": p, "n_core": int(g.sum()),
               "fill_rate": float(filled[g].mean()),
               "first_bar_fill_share_of_filled": float(first_bar_fill[filled].mean()),
               "mean_all_candidates": float(r[g].mean()),
               "mean_filled": float(r[filled].mean()),
               "total": float(r[g].sum())}
        keep = filled & ~first_bar_fill
        rec.update({"n_keep": int(keep.sum()),
                    "mean_first_bar_fills": float(r[first_bar_fill].mean()),
                    "mean_keep": float(r[keep].mean()),
                    "book_all": float(r[g].mean()),
                    "book_cancel": float(np.where(keep, r, 0.0)[g].mean()),
                    "cancel_value_per_candidate": float(np.where(keep, r, 0.0)[g].mean()
                                                        - r[g].mean())})
        # the established rule as the estate applies it: drop on pool bte==1
        keep2 = filled & (w.bte != 1)
        rec["book_cancel_bte1"] = float(np.where(keep2, r, 0.0)[g].mean())
        rec["cancel_bte1_value"] = rec["book_cancel_bte1"] - rec["book_all"]
        B.append(rec)
        print("  place p=%d %.1fs" % (p, time.time() - t0), flush=True)
    out["limitfill"] = B

    # ------------------------------------------------------------------ C. LEVELXM
    J_LO, J_HI = -15, 29
    st = np.array(list(range(J_LO, J_HI + 1)), dtype=np.int32)
    c2 = [X.sidx(s) for s in st]
    Cw = w.C[:, c2].astype(np.float64)
    Hw = w.H[:, c2].astype(np.float64); Lw = w.L[:, c2].astype(np.float64)
    Otrig = w.O[:, X.sidx(-15)].astype(np.float64)
    valid = ~np.isnan(Cw) & core[:, None] & ~np.isnan(Otrig)[:, None]
    reach = np.maximum(w.sgn[:, None] * (Hw - w.entry0[:, None]),
                       w.sgn[:, None] * (Lw - w.entry0[:, None])) / w.d0[:, None]
    wrong_open = (w.sgn * (Otrig - w.entry0) / w.d0) < 0.0
    lvlx = (reach >= 0.0) & wrong_open[:, None]
    b0 = X.rungs_walk(w, 0, horizon="MATCH", denom="STRUCTSTOP", contract="INC")
    base_r = b0["r"]
    gb = b0["good"] & core & ~np.isnan(base_r)
    baseline = float(base_r[gb].mean())
    C = []
    for N in [1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 18, 21, 25, 30]:
        run = np.zeros(n, dtype=np.int32); jj = np.full(n, -1, dtype=np.int32)
        for j in range(len(st)):
            c = lvlx[:, j] & valid[:, j]
            run = np.where(c, run + 1, 0)
            hit = (jj < 0) & (run >= N)
            jj[hit] = j
        surv = jj >= 0
        jc = np.clip(jj, 0, len(st) - 1)
        s_entry = st[jc]
        ent = np.where(surv, Cw[np.arange(n), jc], np.nan)
        o = X.rungs_walk(w, 0, horizon="MATCH", denom="STRUCTSTOP", contract="INC",
                         entry_px=ent, start_stamp=(s_entry + 1).astype(np.int32))
        g = o["good"] & surv & core & ~np.isnan(o["r"])
        if g.sum() < 30:
            continue
        m = g & gb
        C.append({"N": N, "n_taken": int(g.sum()),
                  "survival": float(g.sum() / max(1, int(gb.sum()))),
                  "mean_taken": float(o["r"][g].mean()),
                  "book_mean": float(np.where(g, o["r"], 0.0)[gb].mean()),
                  "median_entry_stamp": float(np.median(s_entry[g])),
                  "share_pre_close": float((s_entry[g] < 0).mean()),
                  "TOTAL_vs_incumbent": float(o["r"][m].mean() - baseline),
                  "TIMING": float((o["r"][m] - base_r[m]).mean()),
                  "SELECTION": float(base_r[m].mean() - baseline),
                  "dk_over_d0_med": float(np.median((o["dk"] / w.d0)[g]))})
    out["levelxm"] = C
    out["meta"]["baseline_k0_mean"] = baseline
    with open(OUT, "w") as f:
        json.dump(out, f)
    print("WROTE %s (%.1fs)" % (OUT, time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
