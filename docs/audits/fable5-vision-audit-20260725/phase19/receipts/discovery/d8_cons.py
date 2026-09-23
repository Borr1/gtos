"""d8_cons — THE AGGREGATION QUESTION NOBODY ASKED.

The estate has only ever priced this family ONE EMISSION AT A TIME.  Two aggregations have
never been tested, and both attack the toll rather than the edge, because the toll is paid
per TRADE and the family emits ~150,000 of them a month:

  A  INSTANT CONSENSUS — when k distinct families fire on the same symbol at the same
     instant, is the edge bigger?  Priced as a book at every k, real vs placebo-side.
  B  DAY CONSENSUS — take the emissions of a symbol-day BEFORE a cut time T as a vote,
     enter ONCE at T in the majority direction, hold H.  One trade per symbol-day instead
     of ~800, so the toll is paid ~60x less often.  Strictly ex ante: nothing after T is used.

Both arms are charged the h1 broker-true four-term toll and compared to a matched
placebo-side arm on identical rows, instants and toll.  Chronological TRAIN/TEST split:
TRAIN = 2025-10..2026-01, TEST = 2026-02..2026-05.  The three sealed 2025 months are not read.
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
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "pbg"))
sys.path.insert(0, "/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801")
import d8_lib as D  # noqa: E402
import pbg_econ as E  # noqa: E402

TRAIN = ("202510", "202511", "202512", "202601")
TEST = ("202602", "202603", "202604", "202605")
CUTS = (8, 16, 32, 48, 56)          # 02:00, 04:00, 08:00, 12:00, 14:00 UTC
HOLDS = (240, 1440)


def blockstats(v, blk, boot=2000, seed=20260806):
    v = np.asarray(v, np.float64)
    ok = np.isfinite(v)
    v, blk = v[ok], np.asarray(blk)[ok]
    if v.size == 0:
        return dict(n=0)
    ud, inv = np.unique(blk, return_inverse=True)
    nb = ud.size
    bs = np.bincount(inv, weights=v, minlength=nb)
    bn = np.bincount(inv, minlength=nb).astype(np.float64)
    r = np.random.default_rng(seed)
    dr = r.integers(0, nb, size=(boot, nb))
    ms = bs[dr].sum(1) / np.maximum(bn[dr].sum(1), 1)
    return dict(n=int(v.size), blocks=int(nb), mean=float(v.mean()),
                se=float(ms.std(ddof=1)), lo=float(np.percentile(ms, 2.5)),
                hi=float(np.percentile(ms, 97.5)), p_le0=float((ms <= 0).mean()),
                blocks_pos=int((bs / np.maximum(bn, 1) > 0).sum()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "d8"))
    ap.add_argument("--json", default=os.path.join(HERE, "D8_CONSENSUS_V1.json"))
    ap.add_argument("--boot", type=int, default=2000)
    a = ap.parse_args()
    months = [m for m in D.MONTHS
              if os.path.isfile(os.path.join(a.out, "D8_EMIT_%s.npz" % m))]
    cm = E.CostModel()
    rng = np.random.default_rng(20260806)

    A = defaultdict(list)     # instant consensus
    B = defaultdict(list)     # day consensus
    for mm in months:
        e = np.load(os.path.join(a.out, "D8_EMIT_%s.npz" % mm))
        g = np.load(os.path.join(a.out, "D8_GRID_%s.npz" % mm))
        syms = [str(x) for x in e["syms"]]
        base = D.base_dt(mm)
        tape = D.Tape(mm, symbols=syms)

        # ---------------------------------------------------------------- A
        n = e["i"].size
        L = e["long"]
        sym = np.array([syms[i] for i in e["sym"]])
        anchor = e["anchor"]
        iso = [(base + dt.timedelta(minutes=int(x))).isoformat() for x in e["i"]]
        flip = rng.random(n) < 0.5
        for h in HOLDS:
            r = e["ret_%d" % h].astype(np.float64)
            ok = np.isfinite(r) & np.isfinite(anchor) & (anchor > 0)
            toll = np.full(n, np.nan)
            for i in np.nonzero(ok)[0]:
                tot, _ = cm.cost_px(sym[i], iso[i], float(anchor[i]), bool(L[i]), hold_min=h)
                toll[i] = tot / anchor[i] * 1e4
            gross = np.where(L, 1.0, -1.0) * r
            gpl = np.where(flip, 1.0, -1.0) * r
            for k in range(1, 8):
                m = ok & (e["conc_nf"] == k)
                if m.sum() == 0:
                    continue
                A[(h, k, "g")].append(gross[m]); A[(h, k, "p")].append(gpl[m])
                A[(h, k, "t")].append(toll[m])
                A[(h, k, "b")].append(np.array([mm + ":" + str(x) for x in e["day"][m]]))
                A[(h, k, "m")].append(np.full(m.sum(), mm))

        # ---------------------------------------------------------------- B
        days = sorted(set(str(x) for x in g["day"]))
        dix = {d: i for i, d in enumerate(days)}
        gd = np.array([dix[str(x)] for x in g["day"]], np.int64)
        gs = g["sym"].astype(np.int64); gw = g["w"].astype(np.int64)
        gkey = (gs * len(days) + gd) * 96 + gw
        gret = {h: g["ret_%d" % h] for h in HOLDS}
        dmin = np.array([int((dt.datetime.fromisoformat(d + "T00:00:00+00:00") - base)
                             .total_seconds() // 60) for d in days], np.int64)
        ed = np.array([dix[str(x)] for x in e["day"]], np.int64)
        ew = (e["i"].astype(np.int64) - dmin[ed]) // 15
        es = e["sym"].astype(np.int64)
        efam = e["fam"].astype(np.int64)
        NC = len(syms) * len(days) * 96
        gpos = np.full(NC, -1, np.int64)
        gpos[gkey] = np.arange(gkey.size)

        for cut in CUTS:
            pre = ew < cut
            vote = defaultdict(int)          # (sym,day) -> net emissions
            fvote = defaultdict(set)         # family-unique long / short
            cntd = defaultdict(int)
            for i in np.nonzero(pre)[0]:
                k = (int(es[i]), int(ed[i]))
                vote[k] += (1 if L[i] else -1)
                cntd[k] += 1
                fvote[k].add((int(efam[i]), bool(L[i])))
            for k, v in vote.items():
                if v == 0:
                    continue
                s, dd = k
                cell = (s * len(days) + dd) * 96 + cut
                p = gpos[cell]
                if p < 0:
                    continue
                imin = int(dmin[dd] + 15 * cut)
                if not (0 <= imin < tape.n):
                    continue
                anc = tape.C[syms[s]][imin - 1] if imin >= 1 else np.nan
                if not np.isfinite(anc) or anc <= 0:
                    continue
                side = 1.0 if v > 0 else -1.0
                pls = 1.0 if rng.random() < 0.5 else -1.0
                isoT = (base + dt.timedelta(minutes=imin)).isoformat()
                nfam = len({f for f, _ in fvote[k]})
                for h in HOLDS:
                    rr = gret[h][p]
                    if not np.isfinite(rr):
                        continue
                    tot, _ = cm.cost_px(syms[s], isoT, float(anc), side > 0, hold_min=h)
                    tb = tot / anc * 1e4
                    B[(cut, h, "g")].append(side * float(rr))
                    B[(cut, h, "p")].append(pls * float(rr))
                    B[(cut, h, "t")].append(tb)
                    B[(cut, h, "b")].append(mm + ":" + days[dd])
                    B[(cut, h, "m")].append(mm)
                    B[(cut, h, "nv")].append(cntd[k])
                    B[(cut, h, "nf")].append(nfam)
                    B[(cut, h, "sy")].append(syms[s])
        print("cons", mm, flush=True)

    R = {"months": months, "train": TRAIN, "test": TEST, "A_instant": {}, "B_day": {}}
    for h in HOLDS:
        for k in range(1, 8):
            if (h, k, "g") not in A:
                continue
            gg = np.concatenate(A[(h, k, "g")]); pp = np.concatenate(A[(h, k, "p")])
            tt = np.concatenate(A[(h, k, "t")]); bb = np.concatenate(A[(h, k, "b")])
            mo = np.concatenate(A[(h, k, "m")])
            cell = dict(n=int(gg.size),
                        gross=blockstats(gg, bb, a.boot),
                        toll=float(np.nanmean(tt)),
                        net=blockstats(gg - tt, bb, a.boot),
                        placebo_net=blockstats(pp - tt, bb, a.boot),
                        signal=blockstats(gg - pp, bb, a.boot))
            for nm, sel in (("train", np.isin(mo, TRAIN)), ("test", np.isin(mo, TEST))):
                if sel.sum() > 30:
                    cell[nm] = dict(n=int(sel.sum()),
                                    gross=float(gg[sel].mean()),
                                    net=float((gg - tt)[sel].mean()),
                                    signal=blockstats((gg - pp)[sel], bb[sel], a.boot))
            R["A_instant"]["h%d_k%d" % (h, k)] = cell
    for cut in CUTS:
        for h in HOLDS:
            if (cut, h, "g") not in B:
                continue
            gg = np.array(B[(cut, h, "g")]); pp = np.array(B[(cut, h, "p")])
            tt = np.array(B[(cut, h, "t")]); bb = np.array(B[(cut, h, "b")])
            mo = np.array(B[(cut, h, "m")]); nv = np.array(B[(cut, h, "nv")])
            nf = np.array(B[(cut, h, "nf")])
            cell = dict(n=int(gg.size),
                        gross=blockstats(gg, bb, a.boot),
                        toll=float(tt.mean()),
                        net=blockstats(gg - tt, bb, a.boot),
                        placebo_net=blockstats(pp - tt, bb, a.boot),
                        signal=blockstats(gg - pp, bb, a.boot),
                        contrarian_net=blockstats(-gg - tt, bb, a.boot),
                        hit=float((gg > 0).mean()))
            for nm, sel in (("train", np.isin(mo, TRAIN)), ("test", np.isin(mo, TEST))):
                if sel.sum() > 30:
                    cell[nm] = dict(n=int(sel.sum()), gross=float(gg[sel].mean()),
                                    net=float((gg - tt)[sel].mean()),
                                    signal=blockstats((gg - pp)[sel], bb[sel], a.boot))
            # by vote strength
            vs = {}
            for lo, hi in ((1, 2), (3, 5), (6, 10), (11, 20), (21, 10 ** 6)):
                m = (nv >= lo) & (nv <= hi)
                if m.sum() < 40:
                    continue
                vs["%d-%d" % (lo, hi)] = dict(n=int(m.sum()), gross=float(gg[m].mean()),
                                              net=float((gg - tt)[m].mean()),
                                              signal=float((gg - pp)[m].mean()))
            cell["by_votes"] = vs
            fs = {}
            for k in range(1, 8):
                m = nf == k
                if m.sum() < 40:
                    continue
                fs[str(k)] = dict(n=int(m.sum()), gross=float(gg[m].mean()),
                                  net=float((gg - tt)[m].mean()))
            cell["by_families"] = fs
            R["B_day"]["cut%d_h%d" % (cut, h)] = cell
            print("B cut%d h%d n=%d gross %.4f toll %.4f net %.4f" % (
                cut, h, cell["n"], cell["gross"]["mean"], cell["toll"], cell["net"]["mean"]),
                flush=True)

    with open(a.json, "w") as fh:
        json.dump(R, fh, indent=1, default=float)
    print("wrote", a.json)


if __name__ == "__main__":
    main()
