#!/usr/bin/env python3
"""x3_03_cuts — who gains from earliness and who is destroyed by it.

Cuts the offset curve by family, by instrument, by bar-direction (continuation vs fade),
by session hour, and measures the displacement-completion curve that bounds how early a
real-time detector could possibly have fired.
"""
from __future__ import annotations
import json, os, sys, collections
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import x3_lib as X

KS = [-15, -12, -10, -8, -6, -5, -4, -3, -2, -1, 0, 1, 2, 3, 5, 8, 10, 15, 20, 30]


def curve(t, z, mask, contract="pool"):
    o = {}
    for k in KS:
        r = z[f"{contract}_{k}"]
        m = mask & ~np.isnan(r)
        if m.sum() < 10:
            o[k] = None
            continue
        rr = r[m]
        o[k] = {"n": int(m.sum()), "gross_R": float(rr.mean()),
                "net_R": float((rr - t.cost_r[m]).mean()),
                "gross_bps": float((rr * t.bps_per_R[m]).mean()),
                "win": float((rr > 0).mean())}
    return o


def main():
    t = X.Tape()
    z = np.load(os.path.join(HERE, "x3_SWEEP_RAW.npz"), allow_pickle=False)
    sup = z["support"]; atm = z["atm"]
    base = atm & sup
    out = {"ks": KS, "n_base": int(base.sum())}

    # ---------- displacement completion: how much of the final M15 move exists at minute j
    j0 = t.j(-15)
    op = t.px[:, j0, 0]                     # open of the forming bar
    cl = t.px[:, t.j(-1), 3]                # close of the forming bar == entry (at-market)
    sgn = np.where(t.is_long, 1.0, -1.0)
    disp = (cl - op) * sgn / t.rdist        # signed displacement in the trade's direction, R
    comp = []
    for j in range(-15, 0):
        c = t.px[:, t.j(j), 3]
        d = (c - op) * sgn / t.rdist
        m = base & ~np.isnan(d) & ~np.isnan(disp) & (np.abs(disp) > 1e-9)
        frac = d[m] / disp[m]
        comp.append({"minute_into_bar": j + 16, "k": j,
                     "n": int(m.sum()),
                     "mean_completion_frac": float(frac.mean()),
                     "median_completion_frac": float(np.median(frac)),
                     "share_completion_ge_50pct": float((frac >= .5).mean()),
                     "share_completion_ge_80pct": float((frac >= .8).mean()),
                     "share_sign_already_correct": float((frac > 0).mean()),
                     "mean_running_disp_R": float(d[m].mean())})
    out["displacement_completion"] = comp
    print("=== how much of the forming bar's move already exists at minute j (at-market) ===")
    print(" min  k   med_frac  mean_frac  >=50%  >=80%  sign_right  running_disp_R")
    for c in comp:
        print(f"{c['minute_into_bar']:4d} {c['k']:+3d} {c['median_completion_frac']:9.4f} "
              f"{c['mean_completion_frac']:10.4f} {c['share_completion_ge_50pct']:6.4f} "
              f"{c['share_completion_ge_80pct']:6.4f} {c['share_sign_already_correct']:11.4f} "
              f"{c['mean_running_disp_R']:+8.4f}")
    out["bar_displacement_R"] = {
        "mean": float(np.nanmean(disp[base])), "median": float(np.nanmedian(disp[base])),
        "share_positive": float((disp[base] > 0).mean()),
    }
    print("\nforming-bar displacement in the trade's direction: mean %.4f R  median %.4f R  "
          "share>0 %.4f" % (out["bar_displacement_R"]["mean"], out["bar_displacement_R"]["median"],
                            out["bar_displacement_R"]["share_positive"]))

    # ---------- continuation vs fade
    cont = base & (disp > 0)
    fade = base & (disp <= 0)
    out["by_bar_direction"] = {
        "continuation_bar_moved_with_trade": curve(t, z, cont),
        "fade_bar_moved_against_trade": curve(t, z, fade),
        "n_continuation": int(cont.sum()), "n_fade": int(fade.sum())}
    print(f"\n=== continuation (n={cont.sum()}) vs fade (n={fade.sum()}) ===")
    print(f"{'k':>4s} {'cont_gross':>11s} {'fade_gross':>11s} {'cont_net':>10s} {'fade_net':>10s}")
    for k in KS:
        a = out["by_bar_direction"]["continuation_bar_moved_with_trade"][k]
        b = out["by_bar_direction"]["fade_bar_moved_against_trade"][k]
        print(f"{k:+4d} {a['gross_R']:+11.5f} {b['gross_R']:+11.5f} "
              f"{a['net_R']:+10.5f} {b['net_R']:+10.5f}")

    # ---------- families
    fams = sorted(set(t.fam[base]))
    out["by_family"] = {}
    print("\n=== by family (at-market cohort), POOL contract, gross R ===")
    hdr = "".join(f"{k:+8d}" for k in [-15, -10, -5, -2, 0, 2, 5, 10, 30])
    print(f"{'family':34s}{'n':>6s}" + hdr)
    for f in fams:
        m = base & (t.fam == f)
        c = curve(t, z, m)
        out["by_family"][f] = c
        row = "".join(f"{c[k]['gross_R']:+8.4f}" if c.get(k) else "     n/a"
                      for k in [-15, -10, -5, -2, 0, 2, 5, 10, 30])
        print(f"{f:34s}{int(m.sum()):6d}" + row)
    print("\n=== by family, best offset and its lift over k=0 ===")
    for f in fams:
        c = out["by_family"][f]
        vals = {k: v["gross_R"] for k, v in c.items() if v}
        if not vals or c.get(0) is None:
            print(f"  {f:34s} n<10 at some offsets - skipped")
            continue
        bk = max(vals, key=vals.get)
        print(f"  {f:34s} n={c[0]['n']:5d} k*={bk:+4d} gross={vals[bk]:+.5f} "
              f"k0={vals[0]:+.5f} lift={vals[bk]-vals[0]:+.5f}")

    # ---------- instruments
    syms = sorted(set(t.sym[base]))
    out["by_symbol"] = {}
    print("\n=== by instrument (at-market cohort), POOL gross R ===")
    print(f"{'symbol':12s}{'n':>6s}" + hdr)
    for s in syms:
        m = base & (t.sym == s)
        c = curve(t, z, m)
        out["by_symbol"][s] = c
        row = "".join(f"{c[k]['gross_R']:+8.4f}" if c.get(k) else "     n/a"
                      for k in [-15, -10, -5, -2, 0, 2, 5, 10, 30])
        print(f"{s:12s}{int(m.sum()):6d}" + row)

    # ---------- hours
    out["by_hour"] = {}
    for h in range(24):
        m = base & (t.hour == h)
        if m.sum() >= 50:
            out["by_hour"][h] = curve(t, z, m)

    # ---------- POI cohorts, for completeness
    for nm, st in (("born_resting", "born_resting"), ("born_marketable", "born_marketable"),
                   ("born_past_stop", "born_past_stop")):
        out[f"cohort_{nm}"] = curve(t, z, sup & (t.born == st))

    json.dump(out, open(os.path.join(HERE, "X3_CUTS_V1.json"), "w"), indent=1)
    print("\nwrote X3_CUTS_V1.json")


if __name__ == "__main__":
    main()
