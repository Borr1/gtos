#!/usr/bin/env python3
"""x5_90_levelxm - stress the one separator that survived the entry-time-matched control.

LEVELXM(N): the price genuinely CROSSED the candidate's own entry level during or after the
trigger bar (it was on the wrong side of that level at the trigger bar's open) and then
stayed at/through it for N consecutive M1 closes; enter AT MARKET at that minute.

For N>=18 every entry lands at or after the M15 close, so nothing is acted on before D and
the level itself is known at D -- the rung is honest and fill-realistic.

Stresses: day-block bootstrap, per-day and per-symbol positivity vs the entry-time-matched
control, first-emission de-duplication, and the exact mirror.
Emits x5_LEVELXM_V1.json.
"""
import json
import os
import sys
import time

import numpy as np

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import x5_lib as X  # noqa: E402

OUT = os.path.join(D, "x5_LEVELXM_V1.json")


def main():
    t0 = time.time()
    w = X.W()
    core = w.core
    n = w.n
    st = np.array(list(range(-15, 30)), dtype=np.int32)
    cols = [X.sidx(x) for x in st]
    Cw = w.C[:, cols].astype(np.float64)
    Hw = w.H[:, cols].astype(np.float64); Lw = w.L[:, cols].astype(np.float64)
    Otrig = w.O[:, X.sidx(-15)].astype(np.float64)
    valid = ~np.isnan(Cw) & core[:, None] & ~np.isnan(Otrig)[:, None]
    reach = np.maximum(w.sgn[:, None] * (Hw - w.entry0[:, None]),
                       w.sgn[:, None] * (Lw - w.entry0[:, None])) / w.d0[:, None]
    wrong_open = (w.sgn * (Otrig - w.entry0) / w.d0) < 0.0
    lvlx = (reach >= 0.0) & wrong_open[:, None]
    # unconditional mean at every entry stamp -> the matched control
    uncond = {}
    for s in range(-14, 30):
        o = X.rungs_walk(w, s + 1, horizon="MATCH", denom="STRUCTSTOP", contract="INC")
        g = core & o["good"] & ~np.isnan(o["r"])
        uncond[s] = {"mean": float(o["r"][g].mean()), "r": o["r"], "good": g}
    print("controls %.1fs" % (time.time() - t0), flush=True)

    res = []
    for N in (10, 15, 18, 21, 25, 30):
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
        start = (s_entry + 1).astype(np.int32)
        o = X.rungs_walk(w, 0, horizon="MATCH", denom="STRUCTSTOP", contract="INC",
                         entry_px=ent, start_stamp=start)
        g = o["good"] & surv & core & ~np.isnan(o["r"])
        r = o["r"]
        # per-row matched control: the unconditional R for THAT row at THAT stamp
        # POPULATION-level control: replace each taken row by the CORE-population mean at
        # that same entry stamp.  (A per-row control is degenerate: the unconditional rung
        # at stamp s IS the same trade for that row.)
        ctrl = np.full(n, np.nan)
        for s in range(-14, 30):
            m = g & (s_entry == s)
            if m.any():
                ctrl[m] = uncond[s]["mean"]
        gm = g & ~np.isnan(ctrl)
        diff = r - ctrl
        bt = X.dayblock_boot(r[gm], w.dayi[gm], B=2000, seed=7001 + N)
        btd = X.dayblock_boot(diff[gm], w.dayi[gm], B=2000, seed=8001 + N)
        days = np.unique(w.dayi[gm]); syms = np.unique(w.symi[gm])
        dpos = sum(1 for d in days if diff[gm & (w.dayi == d)].mean() > 0)
        spos = sum(1 for s in syms if (gm & (w.symi == s)).sum() >= 20
                   and diff[gm & (w.symi == s)].mean() > 0)
        snn = sum(1 for s in syms if (gm & (w.symi == s)).sum() >= 20)
        fe = gm & w.firstem
        # mirror
        stop_m = 2.0 * ent - w.stop
        dkm = np.abs(ent - stop_m)
        goodm = core & ~np.isnan(ent) & (dkm > 0)
        lo = int(np.nanmin(np.where(goodm, start, 10 ** 6)))
        hi = min(int(np.nanmax(np.where(goodm, start, -10 ** 6))) + 119, X.S_HI)
        cc = list(range(X.sidx(lo), X.sidx(hi) + 1))
        hh = w.H[:, cc].astype(np.float64); ll = w.L[:, cc].astype(np.float64)
        cl = w.C[:, cc].astype(np.float64)
        stv = np.arange(lo, hi + 1)[None, :]
        vm = (stv >= start[:, None]) & (stv <= start[:, None] + 119) & (~np.isnan(cl)) & goodm[:, None]
        sg = (-w.sgn)[:, None]; e = ent[:, None]; dv = np.where(dkm > 0, dkm, np.nan)[:, None]
        hr = sg * (hh - e) / dv; lr = sg * (ll - e) / dv
        fav = np.where(hr >= lr, hr, lr); adv = np.where(hr >= lr, lr, hr)
        rinv, _, _ = X.walk(np.nan_to_num(fav, nan=-9e9), np.nan_to_num(adv, nan=9e9),
                            sg * (cl - e) / dv, vm, "INC", tgt=np.full(n, 2.0))
        gi = gm & ~np.isnan(rinv)
        bti = X.dayblock_boot(rinv[gi], w.dayi[gi], B=2000, seed=9001 + N)
        res.append({"N": N, "n": int(gm.sum()),
                    "survival": float(gm.sum() / core.sum()),
                    "mean": float(r[gm].mean()),
                    "boot95": [bt["lo"], bt["hi"]],
                    "matched_control_mean": float(ctrl[gm].mean()),
                    "CONFIRMATION_VALUE": float(diff[gm].mean()),
                    "conf_boot95": [btd["lo"], btd["hi"]],
                    "conf_p_le0": btd["p_le0"],
                    "days_positive": dpos, "days": len(days),
                    "symbols_positive": spos, "symbols_tested": snn,
                    "share_entry_post_close": float((s_entry[gm] >= 0).mean()),
                    "median_entry_stamp": float(np.median(s_entry[gm])),
                    "first_emission_n": int(fe.sum()),
                    "first_emission_mean": float(r[fe].mean()),
                    "first_emission_conf": float(diff[fe].mean()),
                    "mirror_inv_mean": float(rinv[gi].mean()),
                    "info": float(((rinv - r)[gi] / 2.0).mean()),
                    "mirror_inv_boot95": [bti["lo"], bti["hi"]],
                    "mirror_inv_p_le0": bti["p_le0"],
                    "tgt_rate": float((o["reason"][gm] == 0).mean()),
                    "stop_rate": float((o["reason"][gm] == 1).mean()),
                    "win": float((r[gm] > 0).mean()),
                    "mean_cost_r_at_rung": float(np.nanmean((w.cost_r * w.d0 /
                                                             np.where(o["dk"] > 0, o["dk"],
                                                                      np.nan))[gm]))})
        print("  N=%d done %.1fs" % (N, time.time() - t0), flush=True)
    with open(OUT, "w") as f:
        json.dump({"levelxm": res, "n_core": int(core.sum())}, f)
    print("WROTE %s (%.1fs)" % (OUT, time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
