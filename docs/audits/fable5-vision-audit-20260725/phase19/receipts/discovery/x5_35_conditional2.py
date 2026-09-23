#!/usr/bin/env python3
"""x5_35_conditional2 - the confirmation ladder, with the decomposition that makes it readable.

Adds to x5_30:
  * NaN-safe booking (x5_30's BOOK column had NaNs)
  * the TIMING / SELECTION split of every rung's advantage over the incumbent
        total = E_taken[r(s_i)] - E_core[r(0)]
        TIMING    = E_taken[r(s_i)] - E_taken[r(0)]      (same rows, moved entry)
        SELECTION = E_taken[r(0)]   - E_core [r(0)]      (which rows the condition picks)
  * the exact MIRROR at each rung's own per-row entry stamp, so the share of a rung that is
    directional look-ahead (the trigger bar's own move) is stated, not assumed
  * POST / POSTANTI: conditions anchored at the M15 CLOSE and evaluated only on bars at or
    after D.  These use NOTHING that is unknown at the decision instant, so they are
    implementable today on `run_book.py --poll-seconds 60`.
  * LEVELX: a genuine CROSSING of the entry level (price on the wrong side of it at the
    trigger bar's open, then trades through) -- the honest subset of x5_30's LEVEL, which
    fired trivially at j=0 for every born_resting row.

Emits x5_COND_V2.json.
"""
import json
import os
import sys
import time

import numpy as np

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import x5_lib as X  # noqa: E402

OUT = os.path.join(D, "x5_COND_V2.json")
J_LO, J_HI = -15, 29
THETAS = [0.0, 0.05, 0.10, 0.25, 0.50]
NS = [1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 18, 21, 25, 30]


def first_run(cond, valid, N):
    n, S = cond.shape
    run = np.zeros(n, dtype=np.int32)
    out = np.full(n, -1, dtype=np.int32)
    for j in range(S):
        c = cond[:, j] & valid[:, j]
        run = np.where(c, run + 1, 0)
        hit = (out < 0) & (run >= N)
        out[hit] = j
    return out


def mirror_walk(w, ent, start, dk_from_stop=True):
    """Exact mirror at a per-row entry price/stamp: reflect the stop through the entry so
    the risk distance is identical, flip the side."""
    stop_m = 2.0 * ent - w.stop
    dk = np.abs(ent - stop_m)
    good = w.core & ~np.isnan(ent) & (dk > 0)
    lo = int(np.nanmin(np.where(good, start, 10 ** 6)))
    hi = min(int(np.nanmax(np.where(good, start, -10 ** 6))) + 119, X.S_HI)
    cols = list(range(X.sidx(lo), X.sidx(hi) + 1))
    hh = w.H[:, cols].astype(np.float64); ll = w.L[:, cols].astype(np.float64)
    cc = w.C[:, cols].astype(np.float64)
    stamp = np.arange(lo, hi + 1)[None, :]
    vmask = (stamp >= start[:, None]) & (stamp <= (start[:, None] + 119))
    sg = (-w.sgn)[:, None]; e = ent[:, None]; dv = np.where(dk > 0, dk, np.nan)[:, None]
    hr = sg * (hh - e) / dv; lr = sg * (ll - e) / dv
    fav = np.where(hr >= lr, hr, lr); adv = np.where(hr >= lr, lr, hr)
    cls = sg * (cc - e) / dv
    valid = (~np.isnan(cc)) & vmask & good[:, None]
    fav = np.nan_to_num(fav, nan=-9e9); adv = np.nan_to_num(adv, nan=9e9)
    r, reason, ebar = X.walk(fav, adv, cls, valid, "INC", tgt=np.full(w.n, 2.0))
    r[~good] = np.nan
    return r


def main():
    t0 = time.time()
    w = X.W()
    n = w.n
    core = w.core
    stamps = np.array(list(range(J_LO, J_HI + 1)), dtype=np.int32)
    cols = [X.sidx(s) for s in stamps]
    Cw = w.C[:, cols].astype(np.float64)
    Hw = w.H[:, cols].astype(np.float64)
    Lw = w.L[:, cols].astype(np.float64)
    Otrig = w.O[:, X.sidx(-15)].astype(np.float64)
    e0 = w.entry_at(0)
    valid = ~np.isnan(Cw) & core[:, None] & ~np.isnan(Otrig)[:, None]
    post_only = (stamps >= 0)[None, :] & valid
    prog = w.sgn[:, None] * (Cw - Otrig[:, None]) / w.d0[:, None]
    progp = w.sgn[:, None] * (Cw - e0[:, None]) / w.d0[:, None]
    fav_hi = w.sgn[:, None] * (Hw - w.entry0[:, None]) / w.d0[:, None]
    fav_lo = w.sgn[:, None] * (Lw - w.entry0[:, None]) / w.d0[:, None]
    reach = np.where(fav_hi >= fav_lo, fav_hi, fav_lo)
    lvl = reach >= 0.0
    # genuine crossing: on the wrong side of the entry at the trigger bar's OPEN
    wrong_at_open = (w.sgn * (Otrig - w.entry0) / w.d0) < 0.0
    lvlx = lvl & wrong_at_open[:, None]

    b0 = X.rungs_walk(w, 0, horizon="MATCH", denom="STRUCTSTOP", contract="INC")
    base_r = b0["r"]
    gb = b0["good"] & core & ~np.isnan(base_r)
    baseline = float(base_r[gb].mean())
    res = {"meta": {"n_core": int(core.sum()), "baseline_k0_mean": baseline,
                    "baseline_k0_n": int(gb.sum()), "thetas": THETAS, "Ns": NS,
                    "stamps": stamps.tolist()}}
    print("baseline %.5f n=%d" % (baseline, gb.sum()), flush=True)

    rows = []
    FAMS = [("DIR", prog, valid), ("ANTI", -prog, valid),
            ("POST", progp, post_only), ("POSTANTI", -progp, post_only),
            ("LEVEL", None, valid), ("LEVELX", None, valid)]
    for cname, arr, vmask in FAMS:
        ths = THETAS if arr is not None else [0.0]
        for th in ths:
            if arr is not None:
                cond = arr >= th
            elif cname == "LEVEL":
                cond = lvl
            else:
                cond = lvlx
            for N in NS:
                jj = first_run(cond, vmask, N)
                surv = jj >= 0
                jc = np.clip(jj, 0, len(stamps) - 1)
                s_entry = stamps[jc]
                if cname in ("LEVEL", "LEVELX"):
                    ent = np.where(surv, w.entry0, np.nan)
                else:
                    ent = np.where(surv, Cw[np.arange(n), jc], np.nan)
                start = (s_entry + 1).astype(np.int32)
                o = X.rungs_walk(w, 0, horizon="MATCH", denom="STRUCTSTOP",
                                 contract="INC", entry_px=ent, start_stamp=start)
                r = o["r"]
                g = o["good"] & surv & core & ~np.isnan(r)
                if g.sum() < 30:
                    continue
                m = g & gb                       # rows priceable under both rung and baseline
                cst = w.cost_r * (w.d0 / np.where(o["dk"] > 0, o["dk"], np.nan))
                net = r - cst
                bookr = np.where(g, r, 0.0)
                imp_bps = w.sgn * (e0 - o["entry"]) / e0 * 1e4
                rec = {"cond": cname, "theta": th, "N": N,
                       "n_taken": int(g.sum()),
                       "survival": float(g.sum() / max(1, int(gb.sum()))),
                       "mean_taken": float(r[g].mean()),
                       "book_mean": float(bookr[gb].mean()),
                       "total": float(r[g].sum()),
                       "win_taken": float((r[g] > 0).mean()),
                       "median_entry_stamp": float(np.median(s_entry[g])),
                       "mean_entry_stamp": float(s_entry[g].mean()),
                       "share_entry_before_close": float((s_entry[g] < 0).mean()),
                       "dk_over_d0_med": float(np.median((o["dk"] / w.d0)[g])),
                       "entry_bps_vs_close": float(np.nanmean(imp_bps[g])),
                       "tgt_rate": float((o["reason"][g] == 0).mean()),
                       "stop_rate": float((o["reason"][g] == 1).mean()),
                       "net_mean_taken": float(np.nanmean(net[g])),
                       "TOTAL_vs_incumbent": float(r[m].mean() - baseline),
                       "TIMING": float((r[m] - base_r[m]).mean()),
                       "SELECTION": float(base_r[m].mean() - baseline)}
                rows.append(rec)
            print("  %s th=%.2f  %.1fs" % (cname, th, time.time() - t0), flush=True)
    res["rungs"] = rows

    # ---- MIRROR + bootstrap on a shortlist: the best rung of each family by book_mean
    short = []
    for cname in ("DIR", "ANTI", "POST", "POSTANTI", "LEVEL", "LEVELX"):
        rr = [r for r in rows if r["cond"] == cname]
        if not rr:
            continue
        short.append(max(rr, key=lambda r: r["book_mean"]))
        short.append(max(rr, key=lambda r: r["mean_taken"]))
    seen = set(); shortlist = []
    for r in short:
        k = (r["cond"], r["theta"], r["N"])
        if k in seen:
            continue
        seen.add(k); shortlist.append(r)
    mir = []
    for rr in shortlist:
        cname, th, N = rr["cond"], rr["theta"], rr["N"]
        arr = {"DIR": prog, "ANTI": -prog, "POST": progp, "POSTANTI": -progp}.get(cname)
        vmask = post_only if cname in ("POST", "POSTANTI") else valid
        cond = (arr >= th) if arr is not None else (lvl if cname == "LEVEL" else lvlx)
        jj = first_run(cond, vmask, N)
        surv = jj >= 0
        jc = np.clip(jj, 0, len(stamps) - 1)
        s_entry = stamps[jc]
        ent = (np.where(surv, w.entry0, np.nan) if cname in ("LEVEL", "LEVELX")
               else np.where(surv, Cw[np.arange(n), jc], np.nan))
        start = (s_entry + 1).astype(np.int32)
        o = X.rungs_walk(w, 0, horizon="MATCH", denom="STRUCTSTOP", contract="INC",
                         entry_px=ent, start_stamp=start)
        rinv = mirror_walk(w, ent, start)
        g = o["good"] & surv & core & ~np.isnan(o["r"]) & ~np.isnan(rinv)
        info = (rinv - o["r"]) / 2.0
        drift = (rinv + o["r"]) / 2.0
        bt = X.dayblock_boot(o["r"][g], w.dayi[g], B=1000, seed=4242)
        mir.append({"cond": cname, "theta": th, "N": N, "n": int(g.sum()),
                    "orig": float(o["r"][g].mean()), "inv": float(rinv[g].mean()),
                    "info": float(info[g].mean()), "drift": float(drift[g].mean()),
                    "lookahead_share_of_edge": (float(-info[g].mean() /
                                                      (o["r"][g].mean() - baseline))
                                                if abs(o["r"][g].mean() - baseline) > 1e-9 else None),
                    "boot": bt})
        print("  mirror %s th=%.2f N=%d %.1fs" % (cname, th, N, time.time() - t0), flush=True)
    res["mirror_shortlist"] = mir

    # ---- born-state split for the best POST rung and the best DIR rung
    with open(OUT, "w") as f:
        json.dump(res, f)
    print("WROTE %s (%.1fs)" % (OUT, time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
