#!/usr/bin/env python3
"""x5_40_cancel - IS THE 60-SECOND CANCEL STILL NEEDED ONCE ENTRY MOVES?

Two cancel rules, both priced at every rung on the SAME rows:

  CANCEL_ORIG   the estate's established rule: drop the candidate if its entry level was
                first traded inside the first minute after D (pool `bars_to_entry_touch`==1).
                Knowable at D+1min, so it is HONEST for every rung k>=1 and LOOK-AHEAD for
                k<=0.  Flagged per rung.
  ABORT1(th)    rung-native and honest at EVERY rung: enter at the rung, then if the close
                of the first bar after entry is <= -th R, exit there.  This is the
                implementable form of "refuse the adversely-selected immediate fill".

Ablation is computed on one common row set so the standalone values can never be summed.
Emits x5_CANCEL_V1.json.
"""
import json
import os
import sys
import time

import numpy as np

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import x5_lib as X  # noqa: E402

OUT = os.path.join(D, "x5_CANCEL_V1.json")
ABORT_TH = [0.0, 0.05, 0.10, 0.25]
KS = [-14, -10, -5, -3, -1, 0, 1, 2, 3, 4, 5, 6, 8, 10, 15, 20, 30, 45, 60]


def rung_full(w, k, denom, contract, nbars=120):
    """Price rung k and also return the first-post-entry-bar close in R (for ABORT1)."""
    o = X.rungs_walk(w, k, horizon="MATCH", denom=denom, contract=contract)
    ek = o["entry"]
    dd = w.d0 if denom == "SHIFTSTOP" else o["dk"]
    dd = np.where(dd > 0, dd, np.nan)
    c1 = w.C[:, X.sidx(k)].astype(np.float64)
    r1 = w.sgn * (c1 - ek) / dd                     # close of the FIRST bar after entry, in R
    return o, r1


def main():
    t0 = time.time()
    w = X.W()
    core = w.core
    cancel_orig = (w.bte == 1)
    print("core=%d  bte==1 share=%.4f" % (core.sum(), cancel_orig[core].mean()), flush=True)
    out = {"meta": {"n_core": int(core.sum()),
                    "cancel_orig_share_core": float(cancel_orig[core].mean()),
                    "abort_thresholds": ABORT_TH, "rungs": KS,
                    "note": "CANCEL_ORIG is look-ahead for k<=0 (bte is known only at D+1min)"}}

    # ---- how the established cancel rule composes with born state (why it works)
    b = []
    for q in range(4):
        m = core & (w.born == q)
        b.append({"born": w.born_labels[q], "n": int(m.sum()),
                  "bte1_share": float(cancel_orig[m].mean())})
    out["cancel_by_born"] = b

    grid = []
    for denom in ("STRUCTSTOP", "SHIFTSTOP"):
        for contract in ("INC", "FIXLEV") if denom == "STRUCTSTOP" else ("INC",):
            for k in KS:
                o, r1 = rung_full(w, k, denom, contract)
                r = o["r"]
                g = o["good"] & core & ~np.isnan(r)
                base = {"denom": denom, "contract": contract, "k": k}
                n0 = int(g.sum())
                m_all = float(r[g].mean())
                t_all = float(r[g].sum())
                # CANCEL_ORIG
                kp = g & ~cancel_orig
                rec = dict(base)
                rec.update({"n": n0, "mean_all": m_all, "total_all": t_all,
                            "n_keep_cancel_orig": int(kp.sum()),
                            "mean_cancel_orig": float(r[kp].mean()),
                            "total_cancel_orig": float(r[kp].sum()),
                            "mean_dropped_by_cancel": float(r[g & cancel_orig].mean()),
                            "cancel_value_per_taken": float(r[kp].mean() - m_all),
                            "cancel_value_per_candidate": float(r[kp].sum() / max(1, n0) - m_all)})
                # ABORT1 at each threshold (rung-native, honest everywhere)
                for th in ABORT_TH:
                    ab = g & ~np.isnan(r1) & (r1 <= -th)
                    ra = np.where(ab, r1, r)
                    rec["abort%.2f_share" % th] = float(ab[g].mean())
                    rec["abort%.2f_mean" % th] = float(ra[g].mean())
                    rec["abort%.2f_total" % th] = float(ra[g].sum())
                    rec["abort%.2f_value" % th] = float(ra[g].mean() - m_all)
                    # joint: cancel_orig AND abort
                    rj = np.where(ab, r1, r)
                    rec["abort%.2f_plus_cancel_mean" % th] = float(rj[kp].mean())
                    rec["abort%.2f_plus_cancel_perCand" % th] = float(rj[kp].sum() / max(1, n0))
                grid.append(rec)
            print("  %s %s done %.1fs" % (denom, contract, time.time() - t0), flush=True)
    out["grid"] = grid

    # ---- ABLATION on one common row set, primary arm
    denom, contract = "STRUCTSTOP", "INC"
    o0, r10 = rung_full(w, 0, denom, contract)
    g0 = o0["good"] & core & ~np.isnan(o0["r"])
    abl = []
    for k in KS:
        o, r1 = rung_full(w, k, denom, contract)
        g = g0 & o["good"] & ~np.isnan(o["r"]) & ~np.isnan(r1)
        r = o["r"]
        cells = {}
        for use_early in (False, True):
            for use_cancel in (False, True):
                for use_abort in (False, True):
                    rr = r if use_early else o0["r"]
                    r1u = r1 if use_early else r10
                    if use_abort:
                        ab = (r1u <= 0.0)
                        rr = np.where(ab, r1u, rr)
                    m = g & (~cancel_orig if use_cancel else np.ones(w.n, dtype=bool))
                    cells["E%d|C%d|A%d" % (use_early, use_cancel, use_abort)] = {
                        "n": int(m.sum()),
                        "mean": float(rr[m].mean()),
                        "per_candidate": float(rr[m].sum() / max(1, int(g.sum()))),
                        "total": float(rr[m].sum())}
        abl.append({"k": k, "n_common": int(g.sum()), "cells": cells})
        print("  ablation k=%+d %.1fs" % (k, time.time() - t0), flush=True)
    out["ablation"] = abl
    with open(OUT, "w") as f:
        json.dump(out, f)
    print("WROTE %s (%.1fs)" % (OUT, time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
