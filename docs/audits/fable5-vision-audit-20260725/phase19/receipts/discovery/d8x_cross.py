"""d8x_cross — THE QUESTION NOBODY POSED: is the broad family a FILTER on the LIVE BOOK?

The estate has measured the broad V4 family exclusively as a standalone book, and the W7
sleeve book exclusively as a standalone book.  The two have never been placed on the same
rows.  That matters because the family's output is not only a set of trades -- it is a
per-instant, 24-instrument reading of "how many setups are firing and in which direction",
which is a market-state observable whether or not any of its own trades pay.

Substrate:
  * 22,354 sleeve trades (AQ_ESTATE_TRADES_V2, the estate walk of record, 32 sleeves,
    2017-2026); 4,352 of them fall inside the 8 broad-family windows.
  * broad emissions from d8/D8_EMIT_<mm>.npz (built by the concurrent d8 lane from the
    reproduced sealed rosters): symbol, family, day, minute-of-month, direction, risk bps.

Features at each sleeve entry instant t (all strictly BACKWARD-looking, no lookahead):
  same_n/same_net   same-symbol emissions in (t-60, t]
  agree             sign(same_net) == sleeve direction
  mkt_n             all-symbol emissions in (t-15, t]      (activity)
  mkt_breadth       distinct symbols emitting in (t-60, t]
  mkt_dir           net direction fraction across all symbols in (t-60, t]

Outcome: the sleeve's own r_gross from the estate walk.  Day-block bootstrap.
"""
from __future__ import annotations

import gzip
import json
import os
from collections import defaultdict
from datetime import datetime, timezone

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
EMIT = os.path.join(HERE, "d8")
TRADES = ("/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/docs/audits/"
          "fable5-vision-audit-20260725/phase11/receipts/AQ_ESTATE_TRADES_V2.json.gz")
MONTHS = ("202510", "202511", "202512", "202601", "202602", "202603", "202604", "202605")
OUT = os.path.join(HERE, "D8X_CROSS_V1.json")

EPOCH = datetime(2025, 10, 1, tzinfo=timezone.utc)


def base_min(mm):
    d = datetime(int(mm[:4]), int(mm[4:]), 1, tzinfo=timezone.utc)
    return int((d - EPOCH).total_seconds() // 60)


def canon(s):
    """Map a sleeve symbol onto the broad universe's naming."""
    s = s.replace(".cash", "_cash").replace(".", "_")
    return s


def bs(v, blk, boot=4000, seed=7):
    v = np.asarray(v, np.float64)
    blk = np.asarray(blk)
    ok = np.isfinite(v)
    v, blk = v[ok], blk[ok]
    if v.size == 0:
        return dict(n=0)
    ud, inv = np.unique(blk, return_inverse=True)
    nb = ud.size
    s = np.bincount(inv, weights=v, minlength=nb)
    c = np.bincount(inv, minlength=nb).astype(float)
    r = np.random.default_rng(seed)
    dr = r.integers(0, nb, size=(boot, nb))
    ms = s[dr].sum(1) / np.maximum(c[dr].sum(1), 1)
    return dict(n=int(v.size), blocks=int(nb), mean=float(v.mean()),
                lo=float(np.percentile(ms, 2.5)), hi=float(np.percentile(ms, 97.5)),
                p_le0=float((ms <= 0).mean()), win=float((v > 0).mean()))


def diff_bs(va, ba, vb, bb, boot=4000, seed=11):
    """paired-by-day difference of two disjoint groups sharing a day index."""
    va, ba = np.asarray(va, np.float64), np.asarray(ba)
    vb, bb = np.asarray(vb, np.float64), np.asarray(bb)
    days = np.unique(np.concatenate([ba, bb]))
    idx = {d: i for i, d in enumerate(days)}
    nb = len(days)
    sa = np.zeros(nb); ca = np.zeros(nb); sb = np.zeros(nb); cb = np.zeros(nb)
    for v, b in zip(va, ba):
        i = idx[b]; sa[i] += v; ca[i] += 1
    for v, b in zip(vb, bb):
        i = idx[b]; sb[i] += v; cb[i] += 1
    r = np.random.default_rng(seed)
    dr = r.integers(0, nb, size=(boot, nb))
    ma = sa[dr].sum(1) / np.maximum(ca[dr].sum(1), 1e-9)
    mb = sb[dr].sum(1) / np.maximum(cb[dr].sum(1), 1e-9)
    d = ma - mb
    obs = (va.mean() if va.size else np.nan) - (vb.mean() if vb.size else np.nan)
    return dict(delta=float(obs), lo=float(np.percentile(d, 2.5)),
                hi=float(np.percentile(d, 97.5)),
                p_le0=float((d <= 0).mean()), n_a=int(va.size), n_b=int(vb.size))


def main():
    # ---- load emissions, converted to absolute minutes since 2025-10-01 --------------
    per_sym = defaultdict(list)      # sym -> list of (abs_min, dir)
    all_e = []                       # (abs_min, dir, sym_id)
    symnames = None
    for mm in MONTHS:
        p = os.path.join(EMIT, "D8_EMIT_%s.npz" % mm)
        if not os.path.isfile(p):
            print("MISSING", p)
            continue
        z = np.load(p, allow_pickle=True)
        syms = [str(x) for x in z["syms"]]
        symnames = syms if symnames is None else symnames
        b = base_min(mm)
        ai = z["i"].astype(np.int64) + b
        sd = np.where(z["long"], 1, -1).astype(np.int8)
        si = z["sym"].astype(np.int32)
        for k, s in enumerate(syms):
            m = si == k
            if m.any():
                per_sym[s].append(np.stack([ai[m], sd[m]]).T)
        all_e.append(np.stack([ai, sd, si]).T)
    ALL = np.concatenate(all_e)
    ALL = ALL[np.argsort(ALL[:, 0], kind="stable")]
    at = ALL[:, 0].astype(np.int64)
    ad = ALL[:, 1].astype(np.int64)
    asym = ALL[:, 2].astype(np.int64)
    # prefix sums for O(log n) window queries
    c_n = np.concatenate([[0], np.cumsum(np.ones_like(at))])
    c_d = np.concatenate([[0], np.cumsum(ad)])
    SYM = {}
    for s, chunks in per_sym.items():
        a = np.concatenate(chunks)
        a = a[np.argsort(a[:, 0], kind="stable")]
        SYM[s] = (a[:, 0].astype(np.int64),
                  np.concatenate([[0], np.cumsum(a[:, 1].astype(np.int64))]))

    # ---- load sleeve trades ---------------------------------------------------------
    d = json.load(gzip.open(TRADES, "rt"))
    rows = []
    lo_m, hi_m = base_min(MONTHS[0]), base_min("202606")
    for sl, tr in d["trades"].items():
        for r in tr:
            t = datetime.fromisoformat(r["entry_utc"])
            im = int((t - EPOCH).total_seconds() // 60)
            if not (lo_m <= im < hi_m):
                continue
            rows.append(dict(sleeve=sl, sym=canon(r["symbol"]), i=im,
                             dirn=int(r["direction"]), r=float(r["r_gross"]),
                             day=r["entry_utc"][:10], hold=r.get("hold_hours"),
                             tf=d["timeframe_by_sleeve"].get(sl)))
    print("sleeve trades in window:", len(rows))

    def win(arr_t, arr_c, i0, i1):
        a = np.searchsorted(arr_t, i0, "right")
        b = np.searchsorted(arr_t, i1, "right")
        return b - a, int(arr_c[b] - arr_c[a])

    unmapped = defaultdict(int)
    for r in rows:
        i = r["i"]
        s = r["sym"]
        if s in SYM:
            t_, c_ = SYM[s]
            n60, net60 = win(t_, c_, i - 60, i)
            n15, net15 = win(t_, c_, i - 15, i)
        else:
            unmapped[s] += 1
            n60 = net60 = n15 = net15 = None
        r["same_n60"], r["same_net60"] = n60, net60
        r["same_n15"], r["same_net15"] = n15, net15
        mn60, mnet60 = win(at, c_d, i - 60, i)
        mn15, mnet15 = win(at, c_d, i - 15, i)
        a = np.searchsorted(at, i - 60, "right")
        b = np.searchsorted(at, i, "right")
        r["mkt_n60"], r["mkt_net60"] = int(mn60), int(mnet60)
        r["mkt_n15"] = int(mn15)
        r["mkt_breadth60"] = int(np.unique(asym[a:b]).size) if b > a else 0
        r["mkt_dir60"] = float(mnet60) / mn60 if mn60 else 0.0

    res = dict(n_trades=len(rows), unmapped_symbols=dict(unmapped),
               emissions_total=int(at.size), months=list(MONTHS),
               broad_symbols=symnames)

    R = np.array([x["r"] for x in rows])
    D = np.array([x["day"] for x in rows])
    res["ALL"] = bs(R, D)

    # ---- 1. same-symbol agreement ---------------------------------------------------
    have = [x for x in rows if x["same_n60"] is not None]
    ag = [x for x in have if x["same_net60"] * x["dirn"] > 0]
    dg = [x for x in have if x["same_net60"] * x["dirn"] < 0]
    nz = [x for x in have if x["same_net60"] == 0]
    res["same_symbol_60m"] = dict(
        mappable=len(have),
        agree=bs([x["r"] for x in ag], [x["day"] for x in ag]),
        disagree=bs([x["r"] for x in dg], [x["day"] for x in dg]),
        neutral=bs([x["r"] for x in nz], [x["day"] for x in nz]),
        agree_minus_disagree=diff_bs([x["r"] for x in ag], [x["day"] for x in ag],
                                     [x["r"] for x in dg], [x["day"] for x in dg]))
    # any same-symbol emission at all
    q = [x for x in have if x["same_n60"] > 0]
    z = [x for x in have if x["same_n60"] == 0]
    res["same_symbol_any"] = dict(
        with_emission=bs([x["r"] for x in q], [x["day"] for x in q]),
        without=bs([x["r"] for x in z], [x["day"] for x in z]),
        delta=diff_bs([x["r"] for x in q], [x["day"] for x in q],
                      [x["r"] for x in z], [x["day"] for x in z]))

    # ---- 2. market-wide activity ----------------------------------------------------
    for key in ("mkt_n60", "mkt_n15", "mkt_breadth60"):
        v = np.array([x[key] for x in rows], float)
        cuts = np.percentile(v, [33.3, 66.7])
        g = np.digitize(v, cuts)
        cells = {}
        for k in (0, 1, 2):
            m = g == k
            cells["t%d" % k] = dict(range=[float(v[m].min()), float(v[m].max())] if m.any() else None,
                                    **bs(R[m], D[m]))
        cells["hi_minus_lo"] = diff_bs(R[g == 2], D[g == 2], R[g == 0], D[g == 0])
        cells["spearman_r_vs_feature"] = float(np.corrcoef(
            np.argsort(np.argsort(v)), np.argsort(np.argsort(R)))[0, 1])
        res[key] = cells

    # ---- 3. market-wide directional consensus vs sleeve direction -------------------
    md = np.array([x["mkt_dir60"] for x in rows])
    dirn = np.array([x["dirn"] for x in rows])
    aligned = md * dirn
    cuts = np.percentile(aligned, [33.3, 66.7])
    g = np.digitize(aligned, cuts)
    res["mkt_alignment"] = {"t%d" % k: dict(range=[float(aligned[g == k].min()),
                                                   float(aligned[g == k].max())],
                                            **bs(R[g == k], D[g == k])) for k in (0, 1, 2)}
    res["mkt_alignment"]["hi_minus_lo"] = diff_bs(R[g == 2], D[g == 2], R[g == 0], D[g == 0])

    # ---- 4. per-sleeve, on the sleeves with enough trades ---------------------------
    bysl = defaultdict(list)
    for x in rows:
        bysl[x["sleeve"]].append(x)
    ps = {}
    for sl, xs in sorted(bysl.items(), key=lambda kv: -len(kv[1])):
        if len(xs) < 60:
            continue
        v = np.array([x["mkt_n60"] for x in xs], float)
        if np.unique(v).size < 3:
            continue
        cuts = np.percentile(v, [33.3, 66.7])
        g = np.digitize(v, cuts)
        rr = np.array([x["r"] for x in xs]); dd = np.array([x["day"] for x in xs])
        ps[sl] = dict(n=len(xs),
                      lo=bs(rr[g == 0], dd[g == 0]), hi=bs(rr[g == 2], dd[g == 2]),
                      hi_minus_lo=diff_bs(rr[g == 2], dd[g == 2], rr[g == 0], dd[g == 0]))
    res["per_sleeve_mkt_n60"] = ps

    # ---- 5. armed set only ----------------------------------------------------------
    ARMED = ("crypto", "energy_agri", "sub_xvol_pullback", "sub_mid_dn_revert",
             "mx_btcusd_d1_donchian_20_breakout")
    a = [x for x in rows if x["sleeve"] in ARMED]
    if a:
        v = np.array([x["mkt_n60"] for x in a], float)
        rr = np.array([x["r"] for x in a]); dd = np.array([x["day"] for x in a])
        med = float(np.median(v))
        res["armed_only"] = dict(n=len(a), sleeves=sorted({x["sleeve"] for x in a}),
                                 all=bs(rr, dd), median_cut=med,
                                 hi=bs(rr[v > med], dd[v > med]),
                                 lo=bs(rr[v <= med], dd[v <= med]),
                                 delta=diff_bs(rr[v > med], dd[v > med],
                                               rr[v <= med], dd[v <= med]))

    json.dump(res, open(OUT, "w"), indent=1, default=float)
    print("wrote", OUT)
    print("ALL", res["ALL"])
    print("agree-disagree", res["same_symbol_60m"]["agree_minus_disagree"])
    print("mkt_n60 hi-lo", res["mkt_n60"]["hi_minus_lo"])


if __name__ == "__main__":
    main()
