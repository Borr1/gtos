#!/usr/bin/env python3
"""l1 pass 3 — exit-contract VARIANTS that a first-touch (T,S) cell cannot express:
break-even moves, trailing stops, partial scale-outs with a runner, and time stops.
Streams the bar-level R paths once and evaluates every variant on the same path.

Fill convention REAL: fill at bar 0 when the order was born at-or-through the market
(mkt_r_prev_close <= 0), else wait for the first bar with adv <= 0.  Population TAKEABLE
(everything except born_past_stop).  Ties inside a bar go to the STOP.
"""
from __future__ import annotations
import gzip, json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import w0_ws  # noqa
from l1_lib import load, mean, stats, TOUCH  # noqa

OUT = os.path.join(HERE, "l1_VARIANTS_V1.json")


def walk(fav, adv, cls, start, target=None, stop=1.0, be_at=None, trail=None,
         partial_at=None, partial_frac=0.5, be_after_partial=False, max_bars=None):
    """Returns (r, reason, exit_bar0). stop is a POSITIVE magnitude; internal level is -stop."""
    n = len(fav)
    last = min(n, start + max_bars) if max_bars else n
    lvl = -stop
    peak = -1e18
    booked = 0.0
    rem = 1.0
    for i in range(start, last):
        f, a = fav[i], adv[i]
        if a <= lvl + 1e-12:                      # stop first (conservative tie rule)
            return booked + rem * lvl, ("stop" if rem == 1.0 else "stop_after_partial"), i
        if partial_at is not None and rem > partial_frac and f >= partial_at - 1e-12:
            booked += partial_frac * partial_at
            rem -= partial_frac
            if be_after_partial and lvl < 0.0:
                lvl = 0.0
        if target is not None and f >= target - 1e-12:
            return booked + rem * target, "target", i
        if f > peak:
            peak = f
        if be_at is not None and peak >= be_at - 1e-12 and lvl < 0.0:
            lvl = 0.0
        if trail is not None and peak >= trail:
            lvl = max(lvl, peak - trail)
    j = last - 1
    return booked + rem * cls[j], ("time_stop" if max_bars and last < n else "path_end"), j


def build_variants():
    V = {}
    for T in (2.0, 3.0, 5.0, None):
        tn = ("T%.1f" % T) if T else "Tnone"
        V["%s_S1.0" % tn] = dict(target=T, stop=1.0)
        for be in (0.25, 0.5, 0.75, 1.0, 1.5):
            V["%s_S1.0_BE%.2f" % (tn, be)] = dict(target=T, stop=1.0, be_at=be)
        for tr in (0.25, 0.5, 0.75, 1.0, 1.5, 2.0):
            V["%s_S1.0_TRAIL%.2f" % (tn, tr)] = dict(target=T, stop=1.0, trail=tr)
        for pa in (0.5, 1.0, 1.5):
            V["%s_S1.0_P50@%.1f" % (tn, pa)] = dict(target=T, stop=1.0, partial_at=pa)
            V["%s_S1.0_P50@%.1f_BE" % (tn, pa)] = dict(target=T, stop=1.0, partial_at=pa, be_after_partial=True)
    for mb in (5, 15, 30, 45, 60, 90):
        V["T2.0_S1.0_MAX%d" % mb] = dict(target=2.0, stop=1.0, max_bars=mb)
        V["T5.0_S1.25_MAX%d" % mb] = dict(target=5.0, stop=1.25, max_bars=mb)
        V["Tnone_S1.0_MAX%d" % mb] = dict(target=None, stop=1.0, max_bars=mb)
    V["T5.0_S1.25"] = dict(target=5.0, stop=1.25)
    V["T1.0_S0.5"] = dict(target=1.0, stop=0.5)
    V["T5.0_S1.25_TRAIL1.0"] = dict(target=5.0, stop=1.25, trail=1.0)
    V["T5.0_S1.25_BE0.75"] = dict(target=5.0, stop=1.25, be_at=0.75)
    V["Tnone_S1.0_TRAIL0.5"] = dict(target=None, stop=1.0, trail=0.5)
    return V


def main():
    t0 = time.time()
    meta = {}
    for r in load(TOUCH):
        meta[(r["candidate_id"], r["decision_time_utc"])] = (r["born"], r["s_real"], r["family"],
                                                             r["symbol"], r["side"], r["hour"],
                                                             r["cost_r"], r["spread_r"],
                                                             r["commission_r"], r["slip_r"], r["swap_r"])
    V = build_variants()
    names = list(V)
    acc = {k: [0.0, 0, 0, {}] for k in names}   # total, n_filled, n_win, reason counts
    fam_acc = {k: {} for k in names}
    N = 0
    for rp in w0_ws.iter_rpaths():
        k = (rp["candidate_id"], rp["decision_time_utc"])
        m = meta.get(k)
        if m is None or m[0] == "born_past_stop":
            continue
        born, s_real, fam = m[0], m[1], m[2]
        N += 1
        if s_real is None:
            for nm in names:
                acc[nm][3]["no_fill"] = acc[nm][3].get("no_fill", 0) + 1
            continue
        fav, adv, cls = rp["fav"], rp["adv"], rp["cls"]
        for nm in names:
            r, why, ib = walk(fav, adv, cls, s_real, **V[nm])
            a = acc[nm]
            a[0] += r
            a[1] += 1
            if r > 0:
                a[2] += 1
            a[3][why] = a[3].get(why, 0) + 1
            fa = fam_acc[nm].setdefault(fam, [0.0, 0])
            fa[0] += r
            fa[1] += 1
    res = {"population": "TAKEABLE (ex born_past_stop)", "fill": "REAL", "n": N,
           "elapsed_s": round(time.time() - t0, 1), "variants": {}}
    for nm in names:
        tot, nf, nw, why = acc[nm]
        res["variants"][nm] = {"spec": V[nm], "n": N, "filled": nf,
                               "gross_per_candidate": round(tot / N, 6),
                               "win_rate_filled": round(nw / nf, 6) if nf else None,
                               "reasons": why,
                               "by_family": {f: round(v[0] / v[1], 6) for f, v in sorted(fam_acc[nm].items())}}
    with open(OUT, "w") as fh:
        json.dump(res, fh, indent=1)
    top = sorted(res["variants"].items(), key=lambda kv: -kv[1]["gross_per_candidate"])[:18]
    print("n=%d  elapsed=%.1fs" % (N, res["elapsed_s"]))
    for nm, d in top:
        print("%-26s %+.5f  win %.4f" % (nm, d["gross_per_candidate"], d["win_rate_filled"] or 0))
    print("--- baselines ---")
    for nm in ("T2.0_S1.0", "T5.0_S1.25", "Tnone_S1.0"):
        d = res["variants"][nm]
        print("%-26s %+.5f  win %.4f" % (nm, d["gross_per_candidate"], d["win_rate_filled"] or 0))


if __name__ == "__main__":
    main()
