#!/usr/bin/env python3
"""x5_25_mirror - THE LOOK-AHEAD CONTROL, and it governs how every k<0 number is read.

Entering at k<0 means acting BEFORE the bar that produced the candidate had closed.  The
side and the levels are still the completed bar's.  So an unconditional early-entry ladder
can book the trigger bar's own move -- which is exactly the information that made the
candidate exist.  That is look-ahead, and it must be priced before anything is claimed.

The instrument is L7's exact mirror.  At every rung, price the SAME entry price and the
SAME risk distance on the OPPOSITE side:

    SHIFTSTOP  d = d0, stop rides with the entry -> fav_inv = -adv_orig exactly.
    STRUCTSTOP stop reflected through the entry (stop_inv = 2*entry - stop) -> d_k identical.

    info_k  = (r_inv - r_orig) / 2      directional content (>0 means the signal's own
                                        direction is WRONG at that rung)
    drift_k = (r_inv + r_orig) / 2      side-free component (cost/vol/geometry)

If the k<0 gain is the trigger bar's own move, `-info_k` rises steeply as k falls: the
original side beats its mirror precisely because the bar went that way.  Whatever is left
in `drift_k` is side-free and cannot be look-ahead in the DIRECTION.

Emits x5_MIRROR_V1.json.
"""
import json
import os
import sys
import time

import numpy as np

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import x5_lib as X  # noqa: E402

OUT = os.path.join(D, "x5_MIRROR_V1.json")


def price_rung(w, k, denom, flip, nbars=120):
    ek = w.entry_at(k)
    stop = w.stop if not flip else (2.0 * ek - w.stop)
    sg = w.sgn if not flip else -w.sgn
    dk = np.abs(ek - stop)
    good = w.core & ~np.isnan(ek) & (dk > 0)
    lo, hi = k, min(k + nbars - 1, X.S_HI)
    cols = list(range(X.sidx(lo), X.sidx(hi) + 1))
    hh = w.H[:, cols].astype(np.float64)
    ll = w.L[:, cols].astype(np.float64)
    cc = w.C[:, cols].astype(np.float64)
    dd = (w.d0 if denom == "SHIFTSTOP" else dk)
    dd = np.where(dd > 0, dd, np.nan)
    s = sg[:, None]; e = ek[:, None]; dv = dd[:, None]
    hr = s * (hh - e) / dv
    lr = s * (ll - e) / dv
    fav = np.where(hr >= lr, hr, lr)
    adv = np.where(hr >= lr, lr, hr)
    cls = s * (cc - e) / dv
    valid = (~np.isnan(cc)) & good[:, None]
    fav = np.nan_to_num(fav, nan=-9e9); adv = np.nan_to_num(adv, nan=9e9)
    r, reason, ebar = walk_inc(fav, adv, cls, valid)
    r[~good] = np.nan
    return r, good, dk


def walk_inc(fav, adv, cls, valid):
    return X.walk(fav, adv, cls, valid, "INC", tgt=np.full(fav.shape[0], 2.0))


def main():
    t0 = time.time()
    w = X.W()
    out = {"meta": {"n_core": int(w.core.sum()), "rungs": X.RUNGS}}
    tab = []
    for denom in ("SHIFTSTOP", "STRUCTSTOP"):
        for k in X.RUNGS:
            ro, go, dko = price_rung(w, k, denom, False)
            ri, gi, dki = price_rung(w, k, denom, True)
            g = go & gi & ~np.isnan(ro) & ~np.isnan(ri)
            info = (ri - ro) / 2.0
            drift = (ri + ro) / 2.0
            rec = {"denom": denom, "k": k, "n": int(g.sum()),
                   "orig": float(ro[g].mean()), "inv": float(ri[g].mean()),
                   "info": float(info[g].mean()), "drift": float(drift[g].mean())}
            # at-market subset: the geometry-free cell (entry == market at k=0)
            m = g & (w.born == 0)
            rec["atmkt_n"] = int(m.sum())
            rec["atmkt_orig"] = float(ro[m].mean())
            rec["atmkt_inv"] = float(ri[m].mean())
            rec["atmkt_info"] = float(info[m].mean())
            rec["atmkt_drift"] = float(drift[m].mean())
            if k in (-14, -10, -5, -1, 0, 1, 2, 5, 10, 15, 30, 60):
                b = X.dayblock_boot(info[g], w.dayi[g], B=800, seed=2000 + k)
                rec["info_boot"] = b
                b2 = X.dayblock_boot(drift[g], w.dayi[g], B=800, seed=3000 + k)
                rec["drift_boot"] = b2
            tab.append(rec)
        print("  %s done %.1fs" % (denom, time.time() - t0), flush=True)
    out["mirror"] = tab

    # ---- how much of the k<0 gain is the trigger bar's own move, in price terms
    px = []
    e0 = w.entry_at(0)
    for k in X.RUNGS:
        ek = w.entry_at(k)
        g = w.core & ~np.isnan(ek) & ~np.isnan(e0)
        adv_px = w.sgn * (e0 - ek) / w.d0          # R of price improvement vs the M15 close
        bps = w.sgn * (e0 - ek) / e0 * 1e4
        px.append({"k": k, "n": int(g.sum()),
                   "improve_R_mean": float(adv_px[g].mean()),
                   "improve_R_median": float(np.median(adv_px[g])),
                   "improve_bps_mean": float(bps[g].mean()),
                   "improve_bps_median": float(np.median(bps[g])),
                   "share_better": float((adv_px[g] > 0).mean())})
    out["price_improvement"] = px
    with open(OUT, "w") as f:
        json.dump(out, f)
    print("WROTE %s (%.1fs)" % (OUT, time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
