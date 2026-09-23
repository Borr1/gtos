#!/usr/bin/env python3
"""x5_30_conditional - the CONFIRMATION LADDER proper.

A rung is a RULE, not a fixed clock offset:

    "enter at the close of the first minute at which the setup's own condition has held
     for N consecutive minutes, at strength theta"

N=1  -> act the instant the condition is first true intra-bar (weakest confirmation)
N=15 -> the condition held for the WHOLE trigger bar; you act at the M15 close (k=0)
N>15 -> the condition also had to survive N-15 minutes past the close (the delay lever)

Candidates whose condition never reaches strength (theta,N) inside the scan window DO NOT
TRADE -- that is the survival column.

Conditions, all evaluated on CLOSED M1 bars only (no look-ahead):
  DIR      sg*(close_j - open_trigger)/d0 >= theta   "the forming bar is going my way"
  ANTI     the mirror, sg*(open_trigger - close_j)/d0 >= theta   (placebo / L7 inversion probe)
  LEVEL    price has traded at/through entry_price in the trade's direction  (theta ignored;
           the literal "condition first touched intra-bar" reading, limit fill at the level)

Entry is at the CLOSE of the qualifying minute; the forward walk starts at the NEXT bar, so
no rung ever gets same-bar credit.  Emits x5_COND_V1.json.
"""
import json
import os
import sys
import time

import numpy as np

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import x5_lib as X  # noqa: E402

OUT = os.path.join(D, "x5_COND_V1.json")
J_LO, J_HI = -15, 14            # scan stamps: whole trigger bar + 15 min past the close
THETAS = [0.0, 0.05, 0.10, 0.25, 0.50]
NS = [1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 18, 21, 25, 30]


def first_run(cond, valid, N):
    """cond,valid (n,S) bool.  Returns the column index of the first bar at which cond has
    been true for N consecutive VALID bars ending there, else -1."""
    n, S = cond.shape
    run = np.zeros(n, dtype=np.int32)
    out = np.full(n, -1, dtype=np.int32)
    for j in range(S):
        c = cond[:, j] & valid[:, j]
        run = np.where(c, run + 1, 0)
        hit = (out < 0) & (run >= N)
        out[hit] = j
    return out


def main():
    t0 = time.time()
    w = X.W()
    n = w.n
    core = w.core
    print("core=%d" % core.sum(), flush=True)
    stamps = list(range(J_LO, J_HI + 1))
    cols = [X.sidx(s) for s in stamps]
    Cw = w.C[:, cols].astype(np.float64)
    Hw = w.H[:, cols].astype(np.float64)
    Lw = w.L[:, cols].astype(np.float64)
    Otrig = w.O[:, X.sidx(-15)].astype(np.float64)
    valid = ~np.isnan(Cw) & core[:, None] & ~np.isnan(Otrig)[:, None]
    prog = w.sgn[:, None] * (Cw - Otrig[:, None]) / w.d0[:, None]     # R of progress vs bar open
    fav_hi = w.sgn[:, None] * (Hw - w.entry0[:, None]) / w.d0[:, None]
    fav_lo = w.sgn[:, None] * (Lw - w.entry0[:, None]) / w.d0[:, None]
    reach = np.where(fav_hi >= fav_lo, fav_hi, fav_lo)                # best R vs entry in bar
    lvl = (reach >= 0.0)                                              # entry level traded

    res = {"meta": {"n_core": int(core.sum()), "stamps": stamps, "thetas": THETAS, "Ns": NS,
                    "scan_note": "j index 0 == stamp -15 (first minute of the trigger bar); "
                                 "entry at close of qualifying bar, walk starts next bar"}}
    # baseline: the incumbent, unconditional, act at the M15 close
    b0 = X.rungs_walk(w, 0, horizon="MATCH", denom="STRUCTSTOP", contract="INC")
    base_r = b0["r"]
    res["baseline_k0"] = {"n": int(b0["good"].sum()), "mean": float(np.nanmean(base_r[b0["good"]])),
                          "total": float(np.nansum(base_r[b0["good"]]))}
    print("baseline", res["baseline_k0"], flush=True)

    rows = []
    for cname in ("DIR", "ANTI", "LEVEL"):
        ths = THETAS if cname in ("DIR", "ANTI") else [0.0]
        for th in ths:
            if cname == "DIR":
                cond = prog >= th
            elif cname == "ANTI":
                cond = (-prog) >= th
            else:
                cond = lvl
            for N in NS:
                jj = first_run(cond, valid, N)
                surv = jj >= 0
                s_entry = np.array(stamps, dtype=np.int32)[np.clip(jj, 0, len(stamps) - 1)]
                if cname == "LEVEL":
                    ent = np.where(surv, w.entry0, np.nan)
                else:
                    ent = np.where(surv, Cw[np.arange(n), np.clip(jj, 0, len(stamps) - 1)], np.nan)
                start = s_entry + 1
                for contract in ("INC", "FIXLEV"):
                    o = X.rungs_walk(w, 0, horizon="MATCH", denom="STRUCTSTOP",
                                     contract=contract, entry_px=ent, start_stamp=start)
                    g = o["good"] & surv & core
                    r = o["r"]
                    cst = w.cost_r * (w.d0 / np.where(o["dk"] > 0, o["dk"], np.nan))
                    net = r - cst
                    bookr = np.where(g, r, 0.0)
                    booknet = np.where(g & ~np.isnan(net), net, 0.0)
                    imp_bps = np.where(g, w.sgn * (w.entry0 - o["entry"]) / w.entry0 * 1e4, np.nan)
                    rec = {"cond": cname, "theta": th, "N": N, "contract": contract,
                           "n_taken": int(g.sum()),
                           "survival": float(g.sum() / max(1, core.sum())),
                           "mean_taken": float(np.nanmean(r[g])) if g.sum() else None,
                           "net_mean_taken": float(np.nanmean(net[g])) if g.sum() else None,
                           "total": float(np.nansum(r[g])),
                           "net_total": float(np.nansum(net[g & ~np.isnan(net)])),
                           "book_mean": float(bookr[core].mean()),
                           "book_net_mean": float(booknet[core].mean()),
                           "win_taken": float((r[g] > 0).mean()) if g.sum() else None,
                           "mean_entry_stamp": float(np.nanmean(s_entry[g])) if g.sum() else None,
                           "median_entry_stamp": float(np.nanmedian(s_entry[g])) if g.sum() else None,
                           "mean_dk_over_d0": float(np.nanmean(o["dk"][g] / w.d0[g])) if g.sum() else None,
                           "mean_entry_improve_bps": float(np.nanmean(imp_bps[g])) if g.sum() else None,
                           "tgt_rate": float((o["reason"][g] == 0).mean()) if g.sum() else None,
                           "stop_rate": float((o["reason"][g] == 1).mean()) if g.sum() else None,
                           }
                    # paired vs the incumbent on the rows this rung actually takes
                    m = g & ~np.isnan(base_r)
                    rec["paired_vs_k0_on_taken"] = float(np.nanmean(r[m] - base_r[m])) if m.sum() else None
                    rec["k0_mean_on_taken"] = float(np.nanmean(base_r[m])) if m.sum() else None
                    rows.append(rec)
            print("  %s th=%.2f done %.1fs" % (cname, th, time.time() - t0), flush=True)
    res["rungs"] = rows
    with open(OUT, "w") as f:
        json.dump(res, f)
    print("WROTE %s (%.1fs)" % (OUT, time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
