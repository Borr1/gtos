#!/usr/bin/env python3
"""a1 step 50 - the controls that decide what the step-30/40 numbers MEAN.

  C1 EQUAL-HOLD      is the delay lever just a shorter hold?  Re-price k=5 with the
                     bell moved to D+125 so the holding time is identical to k=0.
  C2 EXACT MIRROR    same entry price, same risk distance, stop reflected through the
                     entry, OPPOSITE side.  If the mirror gains too, the delay lever is
                     side-free drift (a contract repair), not information.
  C3 PLACEBO CONFIRM shuffle c0 within (symbol, day).  A gate that survives its own
                     placebo is reading something other than the trade it is attached to.
  C4 COST-STRATIFIED does the confirm gate add anything WITHIN a cost decile?  This is
                     the direct test of the step-30 reading that a1's limbs are
                     affordability filters.
  C5 CONCENTRATION   drop-top-N and cap-gains, b1's own caveat, applied to a1.
  C6 CUTS            per family / per broker hour / per symbol for the delay lever, and
                     the per-symbol rank persistence of the LEVER itself.
  C7 SUBSTITUTION    the 2-D surface: confirm threshold x entry delay, gross only.
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


def walk_mirror(M, k, stop=-1.0, bell=A.BELL):
    """Exact mirror: same fill price, same risk distance, opposite side."""
    ei = A.sidx(k - 1)
    s0, s1 = A.sidx(k), A.sidx(bell) + 1
    ck = -M.RC[:, ei]
    fav = (-M.ADV[:, s0:s1]) - ck[:, None]
    adv = (-M.FAV[:, s0:s1]) - ck[:, None]
    cls = (-M.RC[:, s0:s1]) - ck[:, None]
    hs = adv <= (stop + A.TOL)
    r = np.where(np.isnan(cls[:, -1]), 0.0, cls[:, -1])
    r = np.where(hs.any(axis=1), stop, r)
    return r


def walk_bell(M, k, bell, target=None, stop=-1.0):
    ei = A.sidx(k - 1)
    s0, s1 = A.sidx(k), A.sidx(bell) + 1
    ck = M.RC[:, ei]
    fav = M.FAV[:, s0:s1] - ck[:, None]
    adv = M.ADV[:, s0:s1] - ck[:, None]
    cls = M.RC[:, s0:s1] - ck[:, None]
    n, w = fav.shape
    BIG = w + 10
    hs = adv <= (stop + A.TOL)
    i_stop = np.where(hs.any(axis=1), hs.argmax(axis=1), BIG)
    if target is None:
        i_tgt = np.full(n, BIG)
    else:
        ht = fav >= (target - A.TOL)
        i_tgt = np.where(ht.any(axis=1), ht.argmax(axis=1), BIG)
    r = np.where(np.isnan(cls[:, -1]), 0.0, cls[:, -1])
    st = i_stop <= i_tgt
    r = np.where((i_stop < BIG) & st, stop, r)
    if target is not None:
        r = np.where((i_tgt < i_stop) & (i_tgt < BIG), target, r)
    return r


def main():
    arms = {mm: Arms(mm) for mm in MONTHS}
    R = {}
    rng = np.random.default_rng(1234)

    # ------------------------------------------------ C1 equal hold, C2 mirror
    c1, c2 = {}, {}
    for mm in MONTHS:
        M = arms[mm].M
        r0 = walk_bell(M, 0, A.BELL)
        r5 = walk_bell(M, 5, A.BELL)
        r5e = walk_bell(M, 5, A.BELL + 5)           # equal 120-minute hold
        ok = np.isfinite(r0) & np.isfinite(r5) & np.isfinite(r5e)
        c1[mm] = {
            "k0_bell120": float(r0[ok].mean()),
            "k5_bell120_shorter_hold": float(r5[ok].mean()),
            "k5_bell125_equal_hold": float(r5e[ok].mean()),
            "delta_shorter": A.dayboot((r5 - r0)[ok], M.day[ok])[0],
            "delta_equal": A.dayboot((r5e - r0)[ok], M.day[ok])[0],
            "delta_equal_ci": A.dayboot((r5e - r0)[ok], M.day[ok])[1:],
            "n": int(ok.sum()),
        }
        m0 = walk_mirror(M, 0)
        m5 = walk_mirror(M, 5)
        okm = np.isfinite(m0) & np.isfinite(m5)
        d_orig = (r5 - r0)[ok]
        d_mirr = (m5 - m0)[okm]
        c2[mm] = {
            "orig_k0": float(r0[ok].mean()), "orig_k5": float(r5[ok].mean()),
            "mirror_k0": float(m0[okm].mean()), "mirror_k5": float(m5[okm].mean()),
            "delta_orig": float(d_orig.mean()), "delta_mirror": float(d_mirr.mean()),
            "side_free_drift": 0.5 * float(d_orig.mean() + d_mirr.mean()),
            "directional_info": 0.5 * float(d_orig.mean() - d_mirr.mean()),
            "directional_share": (0.5 * float(d_orig.mean() - d_mirr.mean())
                                  / float(d_orig.mean())) if d_orig.mean() else None,
        }
        print("C1/C2 %s done" % mm, flush=True)
    R["C1_equal_hold"] = c1
    R["C2_exact_mirror_of_delay_lever"] = c2

    # ------------------------------------------------ C3 placebo confirm
    c3 = {}
    for mm in MONTHS:
        a = arms[mm]
        M = a.M
        r, _ = a.gross(5, "STOPONLY")
        real = M.c0 > -0.15
        # shuffle c0 within (symbol, day)
        key = np.array([s + "|" + d for s, d in zip(M.symbol, M.day)])
        sh = M.c0.copy()
        for k in np.unique(key):
            ix = np.where(key == k)[0]
            sh[ix] = M.c0[rng.permutation(ix)]
        plc = sh > -0.15
        def blk(m):
            return {"n": int(m.sum()),
                    "gross": float(r[m].mean()), "cost": float(M.cost[m].mean()),
                    "net": float((r[m] - M.cost[m]).mean())}
        c3[mm] = {"real_kept": blk(real), "real_refused": blk(~real),
                  "placebo_kept": blk(plc), "placebo_refused": blk(~plc),
                  "real_net_gap": blk(real)["net"] - blk(~real)["net"],
                  "placebo_net_gap": blk(plc)["net"] - blk(~plc)["net"],
                  "real_gross_gap": blk(real)["gross"] - blk(~real)["gross"],
                  "placebo_gross_gap": blk(plc)["gross"] - blk(~plc)["gross"],
                  "real_cost_gap": blk(real)["cost"] - blk(~real)["cost"],
                  "placebo_cost_gap": blk(plc)["cost"] - blk(~plc)["cost"]}
    R["C3_placebo_confirm"] = c3

    # ------------------------------------------------ C4 cost-stratified confirm
    c4 = {}
    for tag, mms in (("IS_jan", IS), ("OOS_febmar", OOS)):
        g, c, cc, day = [], [], [], []
        for mm in mms:
            a = arms[mm]
            M = a.M
            r, _ = a.gross(5, "STOPONLY")
            g.append(r); c.append(M.c0); cc.append(M.cost); day.append(M.day)
        g = np.concatenate(g); c = np.concatenate(c)
        cc = np.concatenate(cc); day = np.concatenate(day)
        q = np.quantile(cc, np.linspace(0, 1, 11))
        rows = []
        for i in range(10):
            m = (cc >= q[i]) & (cc <= q[i + 1] if i == 9 else cc < q[i + 1])
            kp = m & (c > -0.15)
            rf = m & ~(c > -0.15)
            if kp.sum() < 20 or rf.sum() < 20:
                continue
            rows.append({"decile": i, "cost_lo": float(q[i]), "cost_hi": float(q[i + 1]),
                         "n_kept": int(kp.sum()), "n_refused": int(rf.sum()),
                         "gross_kept": float(g[kp].mean()),
                         "gross_refused": float(g[rf].mean()),
                         "gross_gap": float(g[kp].mean() - g[rf].mean()),
                         "cost_kept": float(cc[kp].mean()),
                         "cost_refused": float(cc[rf].mean())})
        gaps = [r["gross_gap"] for r in rows]
        c4[tag] = {"deciles": rows, "mean_within_decile_gross_gap": float(np.mean(gaps)),
                   "deciles_with_positive_gap": int(sum(x > 0 for x in gaps)),
                   "deciles_tested": len(gaps),
                   "unconditional_gross_gap": float(g[c > -0.15].mean() - g[c <= -0.15].mean()),
                   "unconditional_cost_gap": float(cc[c > -0.15].mean() - cc[c <= -0.15].mean())}
    R["C4_cost_stratified_confirm"] = c4

    # ------------------------------------------------ C5 concentration
    c5 = {}
    for tag, mms in (("IS_jan", IS), ("OOS_febmar", OOS), ("all5", MONTHS)):
        nets = []
        for mm in mms:
            a = arms[mm]
            M = a.M
            g = a.gates(5)
            m = g["G"] & g["C"] & g["S"]
            r, _ = a.gross(5, "STOPONLY")
            nets.append((r - M.cost)[m])
        v = np.concatenate(nets)
        s = np.sort(v)[::-1]
        rec = {"n": int(len(v)), "net": float(v.mean())}
        for f in (0.001, 0.005, 0.01, 0.05):
            d = max(1, int(round(f * len(v))))
            rec["drop_top_%.1f%%" % (f * 100)] = float(s[d:].mean())
        for cap in (2.0, 3.0, 5.0):
            rec["cap_gains_%gR" % cap] = float(np.minimum(v, cap).mean())
        c5[tag] = rec
    # and for the delay-only arm (all rows), which is the lever that travels
    c5b = {}
    for tag, mms in (("IS_jan", IS), ("OOS_febmar", OOS), ("all5", MONTHS)):
        ds = []
        for mm in mms:
            a = arms[mm]
            r0, _ = a.gross(0, "STOPONLY")
            r5, _ = a.gross(5, "STOPONLY")
            ds.append(r5 - r0)
        v = np.concatenate(ds)
        s = np.sort(v)[::-1]
        rec = {"n": int(len(v)), "delta_gross": float(v.mean())}
        for f in (0.001, 0.005, 0.01, 0.05):
            d = max(1, int(round(f * len(v))))
            rec["drop_top_%.1f%%" % (f * 100)] = float(s[d:].mean())
        for cap in (1.0, 2.0, 5.0):
            rec["clip_delta_pm%gR" % cap] = float(np.clip(v, -cap, cap).mean())
        c5b[tag] = rec
    R["C5_concentration"] = {"a1_book": c5, "delay_lever_delta": c5b}

    # ------------------------------------------------ C6 cuts + lever rank persistence
    def lever_by(keyfn, mms):
        acc = {}
        for mm in mms:
            a = arms[mm]
            M = a.M
            r0, _ = a.gross(0, "STOPONLY")
            r5, _ = a.gross(5, "STOPONLY")
            kk = keyfn(M)
            for u in np.unique(kk):
                m = kk == u
                acc.setdefault(str(u), []).append((r5 - r0)[m])
        return {k: {"n": int(sum(len(x) for x in v)),
                    "delta": float(np.concatenate(v).mean())} for k, v in acc.items()}

    c6 = {
        "by_family_IS": lever_by(lambda M: M.family, IS),
        "by_family_OOS": lever_by(lambda M: M.family, OOS),
        "by_broker_hour_IS": lever_by(lambda M: M.broker_hour, IS),
        "by_broker_hour_OOS": lever_by(lambda M: M.broker_hour, OOS),
        "by_symbol_IS": lever_by(lambda M: M.symbol, IS),
        "by_symbol_OOS": lever_by(lambda M: M.symbol, OOS),
    }
    for dim in ("family", "broker_hour", "symbol"):
        a_is, a_oo = c6["by_%s_IS" % dim], c6["by_%s_OOS" % dim]
        com = [k for k in sorted(set(a_is) & set(a_oo))
               if a_is[k]["n"] >= 30 and a_oo[k]["n"] >= 30]
        c6["spearman_%s" % dim] = A.spearman([a_is[k]["delta"] for k in com],
                                             [a_oo[k]["delta"] for k in com])
        c6["n_%s_compared" % dim] = len(com)
        c6["sign_agree_%s" % dim] = float(np.mean([np.sign(a_is[k]["delta"]) ==
                                                   np.sign(a_oo[k]["delta"]) for k in com]))
    R["C6_cuts_and_lever_persistence"] = c6

    # ------------------------------------------------ C7 substitution surface
    c7 = {}
    for tag, mms in (("IS_jan", IS), ("OOS_febmar", OOS)):
        surf = {}
        for k in (0, 1, 3, 5, 10, 30):
            for th in (-1e9, -0.50, -0.25, -0.15, -0.05, 0.0):
                gs, cs, ds = [], [], []
                for mm in mms:
                    a = arms[mm]
                    M = a.M
                    r, _ = a.gross(k, "STOPONLY")
                    m = M.c0 > th
                    gs.append(r[m]); cs.append(M.cost[m]); ds.append(M.day[m])
                g_ = np.concatenate(gs); c_ = np.concatenate(cs)
                surf["k%d|c0>%s" % (k, "-inf" if th < -1e8 else "%.2f" % th)] = {
                    "n": int(len(g_)), "gross": float(g_.mean()),
                    "cost": float(c_.mean()), "net": float((g_ - c_).mean())}
        c7[tag] = surf
    R["C7_substitution_surface"] = c7

    with open(os.path.join(D, "A1_DIAG_V1.json"), "w") as f:
        json.dump(R, f, indent=1)
    print("\n=== C2 mirror decomposition of the delay lever ===")
    for mm, v in c2.items():
        print("%s  delta_orig %+.5f  delta_mirror %+.5f  side_free %+.5f  info %+.5f  info_share %.3f"
              % (mm, v["delta_orig"], v["delta_mirror"], v["side_free_drift"],
                 v["directional_info"], v["directional_share"]))
    print("\n=== C1 equal hold ===")
    for mm, v in c1.items():
        print("%s  k0 %+.5f  k5(short) %+.5f  k5(equal) %+.5f  delta_equal %+.5f %s"
              % (mm, v["k0_bell120"], v["k5_bell120_shorter_hold"],
                 v["k5_bell125_equal_hold"], v["delta_equal"], v["delta_equal_ci"]))
    print("\n=== C4 cost-stratified confirm ===")
    for t, v in c4.items():
        print(t, "within-decile gross gap %+.5f (%d/%d positive); unconditional gross gap %+.5f, cost gap %+.5f"
              % (v["mean_within_decile_gross_gap"], v["deciles_with_positive_gap"],
                 v["deciles_tested"], v["unconditional_gross_gap"], v["unconditional_cost_gap"]))
    print("\n=== C6 lever persistence ===")
    for dim in ("family", "broker_hour", "symbol"):
        print(dim, "spearman %.4f  sign-agree %.3f  n %d"
              % (c6["spearman_%s" % dim], c6["sign_agree_%s" % dim], c6["n_%s_compared" % dim]))


if __name__ == "__main__":
    main()
