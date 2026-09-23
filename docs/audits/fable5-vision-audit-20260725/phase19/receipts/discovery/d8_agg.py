"""d8_agg — pool the price-space forward statistics and answer three unasked questions.

Q1  Does an emission predict the SIZE of the coming move, as opposed to its sign?  Every
    estate measurement is in R units; R is the generator's own stop distance, which is
    volatility-scaled, so a magnitude signal is divided out by construction.
Q2  Does the family carry directional information at HORIZONS other than the two hours it
    trades — 15 min, 1 h, 4 h, 24 h — measured in bps against the broker toll in bps?
Q3  Does AGREEMENT (several distinct families firing on the same symbol at the same instant)
    carry information a single emission does not?

Controls, all leave-one-out and fully enumerated (nothing sampled):
    DAY   same symbol + same UTC day, the other 95 M15 windows
    HOUR  same symbol + same day + same clock hour, the other 3 windows
    SLOT  same symbol + same window-of-day index, the other days of the month
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from collections import defaultdict

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import d8_lib as D  # noqa: E402

H = D.HORIZONS
CTRLS = ("DAY", "HOUR", "SLOT")
QTY = ("ret_dir", "absret", "rng", "mfe", "mae")


def month_deltas(mm, out):
    e = np.load(os.path.join(out, "D8_EMIT_%s.npz" % mm))
    g = np.load(os.path.join(out, "D8_GRID_%s.npz" % mm))
    syms = [str(x) for x in e["syms"]]
    fams = [str(x) for x in e["fams"]]
    base = D.base_dt(mm)

    days = sorted(set(str(x) for x in g["day"]))
    dix = {d: i for i, d in enumerate(days)}
    ND, NS = len(days), len(syms)

    gd = np.array([dix[str(x)] for x in g["day"]], np.int64)
    gs = g["sym"].astype(np.int64)
    gw = g["w"].astype(np.int64)
    gcell = (gs * ND + gd) * 96 + gw                       # dense (sym, day, w) code

    ed = np.array([dix[str(x)] for x in e["day"]], np.int64)
    es = e["sym"].astype(np.int64)
    dmin = np.array([int((dt.datetime.fromisoformat(d + "T00:00:00+00:00") - base)
                         .total_seconds() // 60) for d in days], np.int64)
    ew = (e["i"].astype(np.int64) - dmin[ed]) // 15
    ecell = (es * ND + ed) * 96 + ew
    on_grid = (ew >= 0) & (ew < 96)

    ewc = np.clip(ew, 0, 95)
    keys = {
        "DAY": (gs * ND + gd, es * ND + ed, NS * ND),
        "HOUR": ((gs * ND + gd) * 24 + gw // 4, (es * ND + ed) * 24 + ewc // 4, NS * ND * 24),
        "SLOT": (gs * 96 + gw, es * 96 + ewc, NS * 96),
    }

    outrows = {}
    for h in H:
        gret = g["ret_%d" % h]; ghi = g["hi_%d" % h]; glo = g["lo_%d" % h]
        gok = np.isfinite(gret) & np.isfinite(ghi) & np.isfinite(glo)
        gq = {"ret_long": gret, "absret": np.abs(gret), "rng": ghi + glo,
              "hi": ghi, "lo": glo}
        # dense own-cell lookup
        NC = NS * ND * 96
        own_ok = np.zeros(NC, bool)
        own_v = {n: np.zeros(NC, np.float64) for n in gq}
        own_ok[gcell[gok]] = True
        for n in gq:
            own_v[n][gcell[gok]] = np.nan_to_num(gq[n][gok].astype(np.float64))

        eret = e["ret_%d" % h]; ehi = e["hi_%d" % h]; elo = e["lo_%d" % h]
        efin = np.isfinite(eret) & np.isfinite(ehi) & np.isfinite(elo) & on_grid
        L = e["long"]
        sgn = np.where(L, 1.0, -1.0)
        ev = {"ret_dir": sgn * eret, "absret": np.abs(eret), "rng": ehi + elo,
              "mfe": np.where(L, ehi, elo), "mae": np.where(L, elo, ehi)}

        for cname in CTRLS:
            gk, ek, K = keys[cname]
            cnt = np.bincount(gk[gok], minlength=K).astype(np.float64)
            sums = {n: np.bincount(gk[gok], weights=gq[n][gok].astype(np.float64), minlength=K)
                    for n in gq}
            oo = np.where(own_ok[ecell] & efin, 1.0, 0.0)
            n_eff = cnt[ek] - oo
            good = efin & (n_eff >= 1)
            cm = {}
            for n in gq:
                s = sums[n][ek] - np.where(oo > 0, own_v[n][ecell], 0.0)
                cm[n] = np.where(good, s / np.where(n_eff > 0, n_eff, 1.0), np.nan)
            cv = {"ret_dir": np.where(L, cm["ret_long"], -cm["ret_long"]),
                  "absret": cm["absret"], "rng": cm["rng"],
                  "mfe": np.where(L, cm["hi"], cm["lo"]),
                  "mae": np.where(L, cm["lo"], cm["hi"])}
            outrows[(h, cname)] = (good, ev, cv, n_eff)
    return e, syms, fams, outrows


def cellstats(vals, days, boot=2000, seed=20260806):
    """mean + day-block bootstrap CI over unique day blocks."""
    vals = np.asarray(vals, np.float64)
    ok = np.isfinite(vals)
    vals = vals[ok]; days = np.asarray(days)[ok]
    if vals.size == 0:
        return dict(n=0, mean=None)
    ud, inv = np.unique(days, return_inverse=True)
    nb = ud.size
    bs = np.bincount(inv, weights=vals, minlength=nb)
    bn = np.bincount(inv, minlength=nb).astype(np.float64)
    rng = np.random.default_rng(seed)
    draws = rng.integers(0, nb, size=(boot, nb))
    ms = bs[draws].sum(1) / np.maximum(bn[draws].sum(1), 1)
    m = float(vals.mean())
    return dict(n=int(vals.size), blocks=int(nb), mean=m,
                se=float(ms.std(ddof=1)),
                lo=float(np.percentile(ms, 2.5)), hi=float(np.percentile(ms, 97.5)),
                p_le0=float((ms <= 0).mean()), p_ge0=float((ms >= 0).mean()),
                blocks_pos=int((bs / np.maximum(bn, 1) > 0).sum()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "d8"))
    ap.add_argument("--months", default=",".join(D.MONTHS))
    ap.add_argument("--boot", type=int, default=2000)
    ap.add_argument("--json", default=os.path.join(HERE, "D8_PREDICT_V1.json"))
    a = ap.parse_args()
    months = [m for m in a.months.split(",")
              if os.path.isfile(os.path.join(a.out, "D8_EMIT_%s.npz" % m))]

    P = defaultdict(lambda: defaultdict(list))   # (h,ctrl,qty) -> {'d':[], 'e':[], 'c':[]}
    KEY = defaultdict(list)
    for mm in months:
        e, syms, fams, outrows = month_deltas(mm, a.out)
        famname = np.array([fams[i] for i in e["fam"]])
        symname = np.array([syms[i] for i in e["sym"]])
        blk = np.array([mm + ":" + str(d) for d in e["day"]])
        for (h, c), (good, ev, cv, n_eff) in outrows.items():
            gi = np.nonzero(good)[0]
            for q in QTY:
                P[(h, c, q)]["d"].append((ev[q][gi] - cv[q][gi]).astype(np.float64))
                P[(h, c, q)]["e"].append(ev[q][gi].astype(np.float64))
                P[(h, c, q)]["c"].append(cv[q][gi].astype(np.float64))
            KEY[(h, c)].append(dict(blk=blk[gi], fam=famname[gi], sym=symname[gi],
                                    hour=e["hour"][gi], nf=e["conc_nf"][gi],
                                    net=e["conc_net"][gi], dbps=e["d_bps"][gi],
                                    long=e["long"][gi]))
        print("agg", mm, flush=True)

    R = {"months": months, "horizons": list(H), "controls": list(CTRLS), "tables": {}}
    for (h, c) in sorted(KEY, key=lambda x: (x[0], x[1])):
        K = {k: np.concatenate([d[k] for d in KEY[(h, c)]]) for k in KEY[(h, c)][0]}
        cell = {}
        for q in QTY:
            dd = np.concatenate(P[(h, c, q)]["d"])
            ee = np.concatenate(P[(h, c, q)]["e"])
            cc = np.concatenate(P[(h, c, q)]["c"])
            cell[q] = dict(delta=cellstats(dd, K["blk"], a.boot),
                           raw=cellstats(ee, K["blk"], a.boot),
                           ctrl=cellstats(cc, K["blk"], a.boot),
                           emission_mean=float(np.nanmean(ee)),
                           control_mean=float(np.nanmean(cc)),
                           ratio=(float(np.nanmean(ee) / np.nanmean(cc))
                                  if np.nanmean(cc) not in (0.0, np.nan) else None))
        cell["n"] = int(K["blk"].size)
        R["tables"]["h%d_%s" % (h, c)] = cell
        # by family / hour / concurrency, on the two decisive quantities
        if c in ("DAY", "SLOT"):
            for q in ("rng", "ret_dir"):
                dd = np.concatenate(P[(h, c, q)]["d"])
                ee = np.concatenate(P[(h, c, q)]["e"])
                cc = np.concatenate(P[(h, c, q)]["c"])
                for axis, arr in (("family", K["fam"]), ("hour", K["hour"]),
                                  ("conc_nf", K["nf"]), ("symbol", K["sym"])):
                    tab = {}
                    for v in np.unique(arr):
                        m = arr == v
                        if m.sum() < 30:
                            continue
                        tab[str(v)] = dict(n=int(m.sum()),
                                           emission=float(np.nanmean(ee[m])),
                                           control=float(np.nanmean(cc[m])),
                                           delta=float(np.nanmean(dd[m])),
                                           ratio=float(np.nanmean(ee[m]) / np.nanmean(cc[m])))
                    R["tables"].setdefault("by_%s" % axis, {})["h%d_%s_%s" % (h, c, q)] = tab
        print("table h%d %s n=%d" % (h, c, cell["n"]), flush=True)

    with open(a.json, "w") as fh:
        json.dump(R, fh, indent=1, default=float)
    print("wrote", a.json)


if __name__ == "__main__":
    main()
