#!/usr/bin/env python3
"""a1 step 60 - the two things step 50 forces.

 F  THE FADE BOOK.  The exact mirror of every candidate is POSITIVE GROSS in all five
    months (+0.095 .. +0.127) while the candidate itself is negative.  Price the fade
    as a book: with the broker-true toll, per month, by cost band, at k=0 and k=5.

 B  THE COST BAND.  b1's book dies at toll<=0.60 on Apr+May and survives at <=0.45.
    Sweep the threshold finely and show the sensitivity curve, so nobody reads a
    knife edge as a discovery.

 T  THE DELAY LEVER, SYMMETRICALLY STRESSED.  Trimmed means, median, share positive,
    and a day-label permutation null.
"""
from __future__ import annotations
import json
import os
import sys

import numpy as np

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import a1_lib as A  # noqa: E402
from a1_30_book import Arms, MONTHS, IS, OOS, OOS2  # noqa: E402
from a1_50_diag import walk_mirror  # noqa: E402


def mirror_inc(M, k, target=2.0, stop=-1.0, bell=A.BELL):
    ei = A.sidx(k - 1)
    s0, s1 = A.sidx(k), A.sidx(bell) + 1
    ck = -M.RC[:, ei]
    fav = (-M.ADV[:, s0:s1]) - ck[:, None]
    adv = (-M.FAV[:, s0:s1]) - ck[:, None]
    cls = (-M.RC[:, s0:s1]) - ck[:, None]
    n, w = fav.shape
    BIG = w + 10
    hs = adv <= (stop + A.TOL)
    ht = fav >= (target - A.TOL)
    i_s = np.where(hs.any(axis=1), hs.argmax(axis=1), BIG)
    i_t = np.where(ht.any(axis=1), ht.argmax(axis=1), BIG)
    r = np.where(np.isnan(cls[:, -1]), 0.0, cls[:, -1])
    r = np.where((i_s < BIG) & (i_s <= i_t), stop, r)
    r = np.where((i_t < i_s) & (i_t < BIG), target, r)
    return r


def main():
    arms = {mm: Arms(mm) for mm in MONTHS}
    R = {}

    # ------------------------------------------------------------------ F fade book
    fade = {}
    for mm in MONTHS:
        a = arms[mm]
        M = a.M
        tb = M.cost * M.rdp * 1e4
        rec = {}
        for k in (0, 3, 5):
            for cn, fn in (("STOPONLY", lambda kk: walk_mirror(M, kk)),
                           ("INC", lambda kk: mirror_inc(M, kk))):
                r = fn(k)
                ro, _ = a.gross(k, cn)
                for band, m in (("all", np.ones(M.n, bool)),
                                ("toll<=0.45", tb <= 0.45),
                                ("toll<=0.60", tb <= 0.60),
                                ("toll<=1.00", tb <= 1.00)):
                    if m.sum() < 30:
                        continue
                    rec["FADE_k%d_%s|%s" % (k, cn, band)] = A.summarize(
                        r[m], M.cost[m], M.day[m], M.rdp[m], label="fade")
                    rec["ORIG_k%d_%s|%s" % (k, cn, band)] = A.summarize(
                        ro[m], M.cost[m], M.day[m], M.rdp[m], label="orig")
        fade[mm] = rec
        print("fade %s done" % mm, flush=True)
    R["fade_per_month"] = fade

    def pool_arm(mms, kind, k, cn, tollmax, extra=None):
        gs, cs, ds, rd = [], [], [], []
        for mm in mms:
            a = arms[mm]
            M = a.M
            tb = M.cost * M.rdp * 1e4
            m = tb <= tollmax
            if extra is not None:
                m &= extra(a)
            if kind == "FADE":
                r = walk_mirror(M, k) if cn == "STOPONLY" else mirror_inc(M, k)
            else:
                r, _ = a.gross(k, cn)
            gs.append(r[m]); cs.append(M.cost[m]); ds.append(M.day[m]); rd.append(M.rdp[m])
        g = np.concatenate(gs); c = np.concatenate(cs)
        d = np.concatenate(ds); q = np.concatenate(rd)
        if len(g) < 20:
            return None
        return A.summarize(g, c, d, q, B=3000)

    fw = {}
    for kind in ("ORIG", "FADE"):
        for k, cn in ((0, "INC"), (0, "STOPONLY"), (5, "STOPONLY")):
            for tm in (0.45, 0.60, 1.00, 1e9):
                key = "%s|k%d_%s|toll<=%.2f" % (kind, k, cn, tm)
                fw[key] = {w: pool_arm(mms, kind, k, cn, tm)
                           for w, mms in (("IS_jan", IS), ("OOS_febmar", OOS),
                                          ("OOS2_aprmay", OOS2), ("all5", MONTHS))}
    R["fade_windows"] = fw

    # ------------------------------------------------------------------ B fine band
    band = {}
    for tm in [0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60,
               0.65, 0.70, 0.80, 0.90, 1.00]:
        for kind in ("ORIG", "FADE"):
            for k, cn in ((0, "INC"), (3, "STOPONLY"), (5, "STOPONLY")):
                key = "%.2f|%s|k%d_%s" % (tm, kind, k, cn)
                row = {}
                for w, mms in (("IS_jan", IS), ("OOS_febmar", OOS),
                               ("OOS2_aprmay", OOS2), ("all5", MONTHS)):
                    v = pool_arm(mms, kind, k, cn, tm)
                    row[w] = None if v is None else {
                        "n": v["n"], "net_R": v["net_R"], "gross_R": v["gross_R"],
                        "cost_R": v["cost_R"], "t_day": v["t_day"],
                        "p_net_le0": v["p_net_le0"], "days_positive": v.get("days_positive"),
                        "days_total": v.get("days_total")}
                band[key] = row
        print("band %.2f done" % tm, flush=True)
    R["cost_band_sweep"] = band

    # instrument composition per band
    comp = {}
    for tm in (0.30, 0.45, 0.60, 0.80, 1.00):
        acc = {}
        for mm in MONTHS:
            M = arms[mm].M
            tb = M.cost * M.rdp * 1e4
            for s in M.symbol[tb <= tm]:
                acc[s] = acc.get(s, 0) + 1
        comp["toll<=%.2f" % tm] = dict(sorted(acc.items(), key=lambda x: -x[1]))
    R["band_instrument_composition"] = comp

    # ------------------------------------------------------------------ T lever stress
    lev = {}
    for tag, mms in (("IS_jan", IS), ("OOS_febmar", OOS), ("OOS2_aprmay", OOS2),
                     ("all5", MONTHS)):
        ds, dys = [], []
        for mm in mms:
            a = arms[mm]
            r0, _ = a.gross(0, "STOPONLY")
            r5, _ = a.gross(5, "STOPONLY")
            ds.append(r5 - r0)
            dys.append(a.M.day)
        v = np.concatenate(ds)
        dy = np.concatenate(dys)
        s = np.sort(v)
        rec = {"n": int(len(v)), "mean": float(v.mean()), "median": float(np.median(v)),
               "share_positive": float((v > 1e-12).mean()),
               "share_zero": float((np.abs(v) <= 1e-12).mean()),
               "share_negative": float((v < -1e-12).mean())}
        for f in (0.005, 0.01, 0.025, 0.05, 0.10):
            d = max(1, int(round(f * len(v))))
            rec["trim_both_%.1f%%" % (f * 100)] = float(s[d:len(v) - d].mean())
        m, lo, hi, p = A.dayboot(v, dy, B=4000)
        rec.update(boot_lo=lo, boot_hi=hi, p_le0=p, t_day=A.tday(v, dy))
        # day-label permutation null: shuffle which row belongs to which day
        rng = np.random.default_rng(7)
        nul = []
        for _ in range(400):
            nul.append(float(v[rng.permutation(len(v))][:len(v)].mean()))
        rec["perm_null_mean_sd"] = float(np.std(nul, ddof=1))
        # per-day means
        u = sorted(set(dy.tolist()))
        pd = np.array([v[dy == x].mean() for x in u])
        rec["days"] = len(u)
        rec["days_positive"] = int((pd > 0).sum())
        lev[tag] = rec
    R["delay_lever_stress"] = lev

    with open(os.path.join(D, "A1_FADE_BAND_V1.json"), "w") as f:
        json.dump(R, f, indent=1)

    print("\n=== FADE vs ORIG, pooled windows (net R/trade) ===")
    print("%-38s %8s %9s %8s %9s %8s %9s" % ("arm", "IS_n", "IS_net", "OOS_n", "OOS_net", "O2_n", "O2_net"))
    for key, v in fw.items():
        i, o, o2 = v["IS_jan"], v["OOS_febmar"], v["OOS2_aprmay"]
        if not i:
            continue
        print("%-38s %8d %+9.5f %8d %+9.5f %8d %+9.5f"
              % (key, i["n"], i["net_R"], o["n"], o["net_R"],
                 o2["n"] if o2 else 0, o2["net_R"] if o2 else float("nan")))
    print("\n=== delay lever, symmetric stress ===")
    for t, v in lev.items():
        print("%-12s n=%6d mean %+.5f median %+.5f  trim1%% %+.5f trim5%% %+.5f  "
              "pos %.3f neg %.3f  days+ %d/%d  p<=0 %.4f"
              % (t, v["n"], v["mean"], v["median"], v["trim_both_1.0%"],
                 v["trim_both_5.0%"], v["share_positive"], v["share_negative"],
                 v["days_positive"], v["days"], v["p_le0"]))


if __name__ == "__main__":
    main()
