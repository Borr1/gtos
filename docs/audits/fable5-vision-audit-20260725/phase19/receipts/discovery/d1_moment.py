"""d1_moment — the MOMENT placebo, per family.

The coin-flip control removes the family's DIRECTION call but keeps its rows, so it
still credits the family for choosing WHEN to be in the market.  This control removes
the moment as well:

  same symbol, same trading day, same relative risk distance (bps), a RANDOM instant
  drawn on the system's own 96-window M15 grid, market fill at the tape's last print
  before that instant, both sides walked, value = (g_long + g_short)/2.

Comparing the REAL rows' coin value to the DRAWN rows' coin value isolates exactly
one thing: does this family pick moments at which the shipped 2R:1R geometry pays
more than an arbitrary moment on the same instrument and day?

3 independent draws per real row.  Whole population, no sampling of rows.
"""
from __future__ import annotations

import glob
import gzip
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone

import numpy as np

REPO = "/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801"
PBG = REPO + "/docs/audits/fable5-vision-audit-20260725/phase19/receipts/pbg"
sys.path.insert(0, PBG)
sys.path.insert(0, REPO)
os.chdir(REPO)
import pbg_lib as L  # noqa: E402
import pbg_econ as E  # noqa: E402

sys.path.insert(0, "/tmp/d1")
from d1_walk import HOR, NEXT, walk_fixed  # noqa: E402

NDRAW = 3
T = 2.0


def main(window):
    z = np.load(f"/tmp/d1/out/D1_{window}.npz", allow_pickle=False)
    live = (~z["bad"]) & (z["nbars"] > 0)
    g_real = np.where(z["real_long"], z["gL_2.0"], z["gS_2.0"])
    clean = z["filled"] & live & np.isfinite(g_real) & (~z["past"])
    sel = np.nonzero(clean)[0]
    sym = z["sym"][sel]
    fam = z["fam"][sel]
    day = z["day"][sel]
    dbps = (z["d"] / z["e"] * 1e4)[sel]
    n = len(sel)
    print(f"[{window}] clean rows {n}", flush=True)

    months = [window.replace("-", "")] + ([NEXT[window]] if NEXT.get(window) else [])
    tape = E.Tape(list(L.SYMBOLS), months)
    cm = E.CostModel()
    rng = np.random.default_rng(int(window.replace("-", "")))

    out_g = np.full((NDRAW, n), np.nan)
    out_c = np.full((NDRAW, n), np.nan)
    for r in range(NDRAW):
        w = rng.integers(0, 96, size=n)
        inst = [
            (datetime.fromisoformat(day[a] + "T00:00:00+00:00")
             + timedelta(minutes=15 * int(w[a]))).isoformat()
            for a in range(n)
        ]
        EXTRA = HOR + 3
        W_c = np.full((n, EXTRA), np.nan)
        W_h = np.full((n, EXTRA), np.nan)
        W_l = np.full((n, EXTRA), np.nan)
        idx = np.array([tape.idx(s) for s in inst], dtype=np.int64)
        by = defaultdict(list)
        for a in range(n):
            by[sym[a]].append(a)
        for s, aa in by.items():
            c, h, lo = tape.c[s], tape.h[s], tape.l[s]
            aa = np.asarray(aa)
            base = idx[aa] - 1
            cols = base[:, None] + np.arange(EXTRA)[None, :]
            good = (cols >= 0) & (cols < tape.n)
            cl = np.clip(cols, 0, tape.n - 1)
            W_c[aa] = np.where(good, c[cl], np.nan)
            W_h[aa] = np.where(good, h[cl], np.nan)
            W_l[aa] = np.where(good, lo[cl], np.nan)
        entry = W_c[:, 0]
        d = dbps / 1e4 * entry
        ok = np.isfinite(entry) & (d > 0)
        sl_ = slice(2, 2 + HOR)
        ee = entry[:, None]
        dd = np.where(d > 0, d, np.nan)[:, None]
        rcL = (W_c[:, sl_] - ee) / dd
        raL = (W_h[:, sl_] - ee) / dd
        rbL = (W_l[:, sl_] - ee) / dd
        rhL = np.maximum(raL, rbL)
        rlL = np.minimum(raL, rbL)
        gL, _ = walk_fixed(rcL, rhL, rlL, T)
        gS, _ = walk_fixed(-rcL, -rlL, -rhL, T)
        gc = (gL + gS) / 2.0
        cc = np.full(n, np.nan)
        hourc = {}
        for a in range(n):
            if not ok[a] or not np.isfinite(gc[a]):
                continue
            iso = inst[a]
            hh = hourc.get(iso)
            if hh is None:
                hh = cm.broker_hour(iso)
                hourc[iso] = hh
            sp = cm.spread_bps(sym[a], hh) / 1e4 * entry[a]
            cmm = cm.comm_px(sym[a], entry[a])
            slp = cm.slip_bps.get(sym[a], ("M", 0.0))[1] / 1e4 * entry[a]
            swL = cm.swap_px(sym[a], True, entry[a], iso, HOR)
            swS = cm.swap_px(sym[a], False, entry[a], iso, HOR)
            cc[a] = (sp + cmm + slp + (swL + swS) / 2.0) / d[a]
        out_g[r] = np.where(ok, gc, np.nan)
        out_c[r] = cc
        print(f"[{window}] draw {r} coin_gross={np.nanmean(out_g[r]):+.5f} "
              f"cover={np.isfinite(out_g[r]).mean():.4f}", flush=True)

    np.savez_compressed(f"/tmp/d1/out/MOM_{window}.npz", sel=sel, sym=sym, fam=fam,
                        day=day, dbps=dbps, g=out_g, c=out_c)
    print(f"[{window}] wrote moment placebo", flush=True)


if __name__ == "__main__":
    main(sys.argv[1])
