"""d8x_geom — what the BID archive costs every path walk in this estate.

d8x_quoteside settles that the bar archive is BID on O/H/L/C (76,734 bars, 29 symbols,
close == last tick bid exactly).  The consequence has never been priced.

A long buys the ASK and sells the BID; a short sells the BID and buys the ASK.  Either way
the exit legs sit one spread away from the series the walks resolve on, so against a bid
series the true trigger conditions are

    stop   touched when adverse excursion >= d - s      (EASIER than walked by s)
    target touched when favourable excursion >= T*d + s (HARDER than walked by s)

with d the generator's risk distance and s the quoted spread, both in bps.  Every walk in
this estate uses d and T*d unshifted.  Charging a spread COST does not repair this: cost is
a level adjustment, the shift is a RESOLUTION adjustment, and they are different objects --
a trade booked as reaching target may in truth have stopped first.

This measures, over all 1,211,077 emissions in the 8 windows, at T = 1.5 (`risk.min_rr`)
and T = 2.0 (the downstream contract), at four horizons:
  * the distribution of s/d, the size of the shift in risk units
  * the change in stop-touch and target-touch rates
  * a first-order R bound on the omission
Spreads are this lane's own whole-archive tick measurement (D8X_TICK_TOLL_V1), FTMO,
2026-06-18..07-26 -- a MECHANISM transfer onto 2025-10..2026-05 emissions, exactly the
transfer x6 and h1 already make, and declared as such.
"""
from __future__ import annotations

import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
EMIT = os.path.join(HERE, "d8")
MONTHS = ("202510", "202511", "202512", "202601", "202602", "202603", "202604", "202605")
OUT = os.path.join(HERE, "D8X_GEOM_V1.json")


def main():
    tick = {r["symbol"]: r for r in json.load(open(os.path.join(HERE, "D8X_TICK_TOLL_V1.json")))
            if r.get("broker") == "FTMO" and r.get("n_ticks")}
    # tick-weighted mean spread in bps per symbol (the honest "what you pay at a random
    # instant"); median is reported too.
    SP = {k: v["mean_bps"] for k, v in tick.items()}
    SPMED = {k: float(v["q"]["0.5"]) for k, v in tick.items()}
    # roster naming -> tick-archive naming (the 5 index CFDs the archive suffixes)
    for a, b in (("GER40", "GER40_cash"), ("JP225", "JP225_cash"), ("NAS100", "US100_cash"),
                 ("SPX500", "US500_cash"), ("UK100", "UK100_cash")):
        if b in SP:
            SP[a], SPMED[a] = SP[b], SPMED[b]

    D, S, LONG, HI, LO, MON, SYMN = [], [], [], {}, {}, [], []
    H = (15, 60, 240, 1440)
    hi = {h: [] for h in H}
    lo = {h: [] for h in H}
    miss = set()
    for mm in MONTHS:
        p = os.path.join(EMIT, "D8_EMIT_%s.npz" % mm)
        if not os.path.isfile(p):
            continue
        z = np.load(p, allow_pickle=True)
        syms = [str(x) for x in z["syms"]]
        si = z["sym"].astype(int)
        names = np.array(syms)[si]
        sp = np.array([SP.get(s, np.nan) for s in syms])[si]
        spm = np.array([SPMED.get(s, np.nan) for s in syms])[si]
        for s in syms:
            if s not in SP:
                miss.add(s)
        D.append(z["d_bps"].astype(np.float64))
        S.append(np.stack([sp, spm]))
        LONG.append(z["long"])
        MON.append(np.full(z["d_bps"].size, mm))
        SYMN.append(names)
        for h in H:
            hi[h].append(z["hi_%d" % h].astype(np.float64))
            lo[h].append(z["lo_%d" % h].astype(np.float64))
    d = np.concatenate(D)
    sp = np.concatenate([x[0] for x in S])
    spm = np.concatenate([x[1] for x in S])
    lng = np.concatenate(LONG)
    mon = np.concatenate(MON)
    symn = np.concatenate(SYMN)
    HIa = {h: np.concatenate(hi[h]) for h in H}
    LOa = {h: np.concatenate(lo[h]) for h in H}
    n = d.size
    res = dict(n_emissions=int(n), months=list(MONTHS),
               symbols_without_tick_spread=sorted(miss),
               spread_source="D8X_TICK_TOLL_V1 FTMO tick-weighted mean bps, 2026-06-18..07-26",
               note="MECHANISM transfer, declared: spreads measured after the emission windows")

    ok = np.isfinite(d) & (d > 0) & np.isfinite(sp)
    ratio = sp[ok] / d[ok]
    res["s_over_d"] = dict(
        n=int(ok.sum()),
        mean=float(ratio.mean()),
        **{("p%d" % q): float(np.percentile(ratio, q)) for q in (1, 5, 10, 25, 50, 75, 90, 95, 99)},
        share_gt_10pct=float((ratio > 0.10).mean()),
        share_gt_25pct=float((ratio > 0.25).mean()),
        share_gt_50pct=float((ratio > 0.50).mean()),
        share_gt_100pct=float((ratio > 1.0).mean()),
        median_d_bps=float(np.median(d[ok])), median_spread_bps=float(np.median(sp[ok])))

    # per-symbol table
    tab = {}
    for s in sorted(set(symn.tolist())):
        m = (symn == s) & ok
        if m.sum() < 200:
            continue
        tab[s] = dict(n=int(m.sum()), median_d_bps=float(np.median(d[m])),
                      spread_bps=float(sp[m][0]),
                      s_over_d_median=float(np.median(sp[m] / d[m])),
                      share_gt_25pct=float((sp[m] / d[m] > 0.25).mean()))
    res["per_symbol"] = tab

    # touch-rate change, both targets, four horizons
    cells = {}
    for T in (1.5, 2.0):
        for h in H:
            fav = np.where(lng, HIa[h], LOa[h])     # favourable excursion in bps
            adv = np.where(lng, LOa[h], HIa[h])     # adverse excursion in bps
            m = ok & np.isfinite(fav) & np.isfinite(adv)
            dd, ss = d[m], sp[m]
            f, a = fav[m], adv[m]
            stop_w = a >= dd
            stop_t = a >= np.maximum(dd - ss, 0.0)
            tgt_w = f >= T * dd
            tgt_t = f >= (T * dd + ss)
            # first-order R bound: rows that flip
            flip_stop = (~stop_w) & stop_t
            flip_tgt = tgt_w & (~tgt_t)
            cells["T%.1f_h%d" % (T, h)] = dict(
                n=int(m.sum()),
                stop_walked=float(stop_w.mean()), stop_true=float(stop_t.mean()),
                stop_delta_pp=float((stop_t.mean() - stop_w.mean()) * 100),
                target_walked=float(tgt_w.mean()), target_true=float(tgt_t.mean()),
                target_delta_pp=float((tgt_t.mean() - tgt_w.mean()) * 100),
                rows_gaining_a_stop=int(flip_stop.sum()),
                rows_losing_a_target=int(flip_tgt.sum()),
                first_order_R_bound=float(-1.0 * flip_stop.mean() - T * flip_tgt.mean()),
                note=("first_order_R_bound charges a newly-touched stop at -1R and a lost "
                      "target at -T*R; it ignores ordering, so it is a BOUND not a book"))
    res["touch_rates"] = cells

    # by risk-distance decile at the shipped contract
    m = ok & np.isfinite(HIa[240]) & np.isfinite(LOa[240])
    dd = d[m]
    q = np.percentile(dd, np.arange(0, 101, 10))
    g = np.clip(np.searchsorted(q, dd, "right") - 1, 0, 9)
    fav = np.where(lng, HIa[240], LOa[240])[m]
    adv = np.where(lng, LOa[240], HIa[240])[m]
    ss = sp[m]
    dec = {}
    for k in range(10):
        s_ = g == k
        stop_w = adv[s_] >= dd[s_]
        stop_t = adv[s_] >= np.maximum(dd[s_] - ss[s_], 0)
        tgt_w = fav[s_] >= 2.0 * dd[s_]
        tgt_t = fav[s_] >= 2.0 * dd[s_] + ss[s_]
        dec["d%d" % k] = dict(n=int(s_.sum()), d_range=[float(dd[s_].min()), float(dd[s_].max())],
                              s_over_d=float(np.median(ss[s_] / dd[s_])),
                              stop_delta_pp=float((stop_t.mean() - stop_w.mean()) * 100),
                              target_delta_pp=float((tgt_t.mean() - tgt_w.mean()) * 100),
                              first_order_R_bound=float(
                                  -1.0 * ((~stop_w) & stop_t).mean() - 2.0 * (tgt_w & ~tgt_t).mean()))
    res["risk_distance_deciles_h240_T2"] = dec

    json.dump(res, open(OUT, "w"), indent=1)
    print(json.dumps(res["s_over_d"], indent=1))
    for k, v in res["touch_rates"].items():
        print("%-12s stop %+.2fpp  target %+.2fpp  bound %+.5f R" %
              (k, v["stop_delta_pp"], v["target_delta_pp"], v["first_order_R_bound"]))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
