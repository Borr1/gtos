"""B4 cross-sectional reversion engine.

The one design decision that matters here is the ANCHOR, so it is stated first.

For a bid-based close ``C_t`` carrying an idiosyncratic quote shock ``e_t``
(a wider spread at the print instant depresses the bid), the trailing return
``r_t = log C_t - log C_{t-1}`` is biased DOWN by ``e_t`` and the forward return
``r_{t+1} = log C_{t+1} - log C_t`` is biased UP by exactly the same ``e_t``.
The induced correlation is -1 on the shock component: a close-to-close signal
traded against a close-to-close forward manufactures reversal, in the time series
and cross-sectionally alike (cross-sectionally because ``var(e)`` differs across
symbols and days, so the ranking loads on it).

The D1 close of this archive is the last print before the broker-midnight
rollover, which is the widest-spread instant of the day: Lane 5 measured 17.6x
the 14:00 median in the candidate cache and 41x on EURUSD ticks.  So ``e_t`` here
is not a hypothetical.

Four anchors are therefore run side by side and reported together:

  A0  sig C[t-1]->C[t]   fwd C[t]->C[t+1]     shares C[t].  = Lane 5's pilot.
  A1  sig C[t-1]->C[t]   fwd C[t+1]->C[t+2]   gapped: shares nothing, not tradeable
                                              at t+1 (it is, at t+2).
  A2  sig C[t-1]->C[t]   fwd O[t+1]->C[t+1]   shares nothing. TRADEABLE.
  A3  sig C[t-1]->C[t]   fwd O[t+1]->O[t+2]   shares nothing. TRADEABLE, 1 full day.

A0 minus A2 is the size of the anchor artifact, measured rather than argued.
"""
from __future__ import annotations
import json, math, os, sys, collections
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from panel import d1_panel, classify, _fx_pair   # noqa: E402

OUT = os.path.join(HERE, "receipts")
os.makedirs(OUT, exist_ok=True)


# --------------------------------------------------------------------------
def build_matrices(min_hist=120):
    st = d1_panel()
    st["cls"] = st["sym"].map(classify)
    syms = sorted(st["sym"].unique())
    dates = np.array(sorted(st["bt"].unique()))
    si = {s: i for i, s in enumerate(syms)}
    di = {d: i for i, d in enumerate(dates)}
    N, T = len(syms), len(dates)
    C = np.full((T, N), np.nan); O = np.full((T, N), np.nan)
    H = np.full((T, N), np.nan); L = np.full((T, N), np.nan)
    r = st["bt"].map(di).values; c = st["sym"].map(si).values
    C[r, c] = st["close"].values; O[r, c] = st["open"].values
    H[r, c] = st["high"].values; L[r, c] = st["low"].values
    CL = np.array([classify(s) for s in syms])
    return dict(syms=np.array(syms), dates=dates, C=C, O=O, H=H, L=L, CL=CL,
                si=si, di=di, N=N, T=T)


def own_seq(M, P):
    """Per-symbol own-observation sequence: for each (t, i) with a valid price,
    the previous VALID price index for that symbol.  Weekends / holidays /
    listing gaps differ per symbol, so a global grid silently mixes a 1-day
    return with a 3-day one.  Lane 5 hit this (the naive grid collapses the
    universe to the 30 crypto symbols); we carry its fix."""
    T, N = P.shape
    prev = np.full((T, N), -1, dtype=np.int32)
    last = np.full(N, -1, dtype=np.int32)
    for t in range(T):
        prev[t] = last
        v = np.isfinite(P[t])
        last = np.where(v, t, last)
    return prev


def make_returns(M):
    """r_cc[t,i]  = log C[t] - log C[prev(t)]        (trailing, close-to-close)
       r_oc[t,i]  = log C[t] - log O[t]              (intraday, same session)
       r_oo[t,i]  = log O[t] - log O[prev(t)]        (open-to-open)"""
    C, O = M["C"], M["O"]
    prevC = own_seq(M, C)
    T, N = C.shape
    lC = np.log(C); lO = np.log(O)
    idx = np.arange(N)
    r_cc = np.full((T, N), np.nan); r_oo = np.full((T, N), np.nan)
    for t in range(T):
        p = prevC[t]
        ok = p >= 0
        r_cc[t, ok] = lC[t, ok] - lC[p[ok], idx[ok]]
        r_oo[t, ok] = lO[t, ok] - lO[p[ok], idx[ok]]
    r_oc = lC - lO
    M["prevC"] = prevC; M["r_cc"] = r_cc; M["r_oc"] = r_oc; M["r_oo"] = r_oo
    M["nextC"] = _next_valid(C)
    return M


def _next_valid(P):
    T, N = P.shape
    nxt = np.full((T, N), -1, dtype=np.int32)
    nx = np.full(N, -1, dtype=np.int32)
    for t in range(T - 1, -1, -1):
        nxt[t] = nx
        v = np.isfinite(P[t])
        nx = np.where(v, t, nx)
    return nxt


# --------------------------------------------------------------------------
ANCHORS = {
    #  name: (signal source, forward legs)   legs are ('price', hops)
    "A0_cc_cc":  dict(fwd="cc", hop=1),      # shares C[t]
    "A1_cc_gap": dict(fwd="cc", hop=2),      # skip a day: shares nothing
    "A2_cc_oc":  dict(fwd="oc", hop=1),      # enter next open, exit next close
    "A3_cc_oo":  dict(fwd="oo", hop=2),      # enter next open, exit open after
}


def cell(M, anchor="A2_cc_oc", classes=None, exclude=None, lookback=1,
         quant=5, min_hist=120, start=None, end=None, vol_win=60,
         neutral=None, nperm=2000, seed=7, min_univ=12, cost_bps_leg=0.0,
         cost_map=None, weight="volparity"):
    """One measured cell.  Returns a dict of results plus the per-rebalance series."""
    C = M["C"]; T, N = C.shape
    r_cc, r_oc, r_oo = M["r_cc"], M["r_oc"], M["r_oo"]
    nxt = M["nextC"]; CL = M["CL"]; dates = M["dates"]; syms = M["syms"]
    idx = np.arange(N)

    # trailing signal over `lookback` own-observations
    sig = np.full((T, N), np.nan)
    if lookback == 1:
        sig = r_cc.copy()
    else:
        prevC = M["prevC"]; lC = np.log(C)
        for t in range(T):
            p = idx.copy()
            j = np.full(N, t)
            ok = np.ones(N, bool)
            for _ in range(lookback):
                pj = prevC[j, idx] if _ > 0 else prevC[t]
                ok &= pj >= 0
                j = np.where(ok, pj, j)
            sig[t, ok] = lC[t, ok] - lC[j[ok], idx[ok]]

    # realised vol, per symbol, trailing, own-observation
    VOL = pd.DataFrame(r_cc).rolling(vol_win, min_periods=vol_win // 2).std().values
    HC = np.cumsum(np.isfinite(C), axis=0)

    mask = np.ones(N, bool)
    if classes is not None:
        mask &= np.isin(CL, classes)
    if exclude is not None:
        mask &= ~np.isin(CL, exclude)

    cfg = ANCHORS[anchor]
    recs = []
    for t in range(1, T - 4):
        d = str(dates[t])[:10]
        if (start and d < start) or (end and d >= end):
            continue
        t1 = nxt[t]                       # per-symbol next valid observation
        ok = mask & np.isfinite(sig[t]) & np.isfinite(VOL[t]) & (VOL[t] > 0) & (HC[t] >= min_hist)
        ok &= (t1 >= 0)
        if cfg["hop"] == 2:
            t2 = np.where(t1 >= 0, nxt[np.clip(t1, 0, T - 1), idx], -1)
            ok &= (t2 >= 0)
        else:
            t2 = t1
        ii = np.where(ok)[0]
        if len(ii) < min_univ:
            continue
        if cfg["fwd"] == "cc":
            fwd = r_cc[t2[ii], ii] if cfg["hop"] == 2 else r_cc[t1[ii], ii]
        elif cfg["fwd"] == "oc":
            fwd = r_oc[t1[ii], ii]
        else:  # oo: open[t2] / open[t1]
            fwd = np.log(M["O"][t2[ii], ii]) - np.log(M["O"][t1[ii], ii])
        good = np.isfinite(fwd)
        ii = ii[good]; fwd = fwd[good]
        if len(ii) < min_univ:
            continue
        s = sig[t, ii] / (VOL[t, ii] * math.sqrt(lookback))
        v = VOL[t, ii]
        if neutral == "currency":
            s = _currency_neutralise(s, syms[ii])
            if s is None:
                continue
        f = fwd / v                       # vol-normalised forward (sigma units)
        o = np.argsort(s)
        q = max(3, len(ii) // quant)
        lo, hi = o[:q], o[-q:]            # lo = biggest losers (reversal buys them)
        if weight == "volparity":
            ret = float(f[lo].mean() - f[hi].mean())          # LONG losers, SHORT winners
        else:
            ret = float(fwd[lo].mean() - fwd[hi].mean()) / float(np.median(v))
        # transaction cost, in the same sigma unit
        if cost_map is not None:
            cl = np.array([cost_map.get(syms[k], np.nan) for k in ii])
            cb = np.nanmean(np.concatenate([cl[lo], cl[hi]])) * 1e-4
        else:
            cb = cost_bps_leg * 1e-4
        cost_sig = float(2.0 * cb / np.median(v))      # 2 legs (in + out) per side, vol units
        recs.append(dict(t=t, date=d, n=len(ii), ret=ret, cost=cost_sig,
                         medvol=float(np.median(v)),
                         lo=set(syms[ii[lo]]), hi=set(syms[ii[hi]]),
                         sig=s, f=f))
    if len(recs) < 30:
        return None

    a = np.array([r["ret"] for r in recs])
    cst = np.array([r["cost"] for r in recs])
    net = a - cst
    m = a.mean(); sd = a.std(ddof=1); n = len(a)
    tt = m / (sd / math.sqrt(n))
    mn = net.mean(); tn = mn / (net.std(ddof=1) / math.sqrt(n))

    rng = np.random.default_rng(seed)
    pm = np.empty(nperm)
    packed = [(r["sig"], r["f"], quant) for r in recs]
    for p in range(nperm):
        acc = 0.0
        for (s_, f_, qz) in packed:
            k = len(s_); pr = rng.permutation(k); qq = max(3, k // qz)
            acc += f_[pr[:qq]].mean() - f_[pr[qq:2 * qq]].mean()
        pm[p] = acc / len(packed)
    perm_p = float((np.abs(pm - pm.mean()) >= abs(m)).mean())

    turn = []
    for i in range(1, len(recs)):
        A, B = recs[i], recs[i - 1]
        turn.append((len(A["lo"] - B["lo"]) + len(A["hi"] - B["hi"])) /
                    max(1, len(A["lo"]) + len(A["hi"])))
    medvol = float(np.median([r["medvol"] for r in recs]))
    gross_bps = m * medvol * 1e4
    yr = collections.defaultdict(list)
    for r_, x in zip(recs, a):
        yr[r_["date"][:4]].append(x)

    return dict(
        anchor=anchor, n_rebal=n, median_universe=int(np.median([r["n"] for r in recs])),
        mean_sigma=float(m), t=float(tt), ci95=[float(m - 1.96 * sd / math.sqrt(n)),
                                                float(m + 1.96 * sd / math.sqrt(n))],
        perm_p=perm_p, sharpe_ann=float(m / sd * math.sqrt(252)) if sd > 0 else np.nan,
        mean_net_sigma=float(mn), t_net=float(tn),
        sharpe_net_ann=float(mn / net.std(ddof=1) * math.sqrt(252)) if net.std(ddof=1) > 0 else np.nan,
        gross_bps_per_rebal=float(gross_bps),
        cost_sigma=float(cst.mean()), cost_bps=float(cst.mean() * medvol * 1e4),
        turnover=float(np.mean(turn)) if turn else 1.0,
        breakeven_bps_leg=float(gross_bps / (2 * np.mean(turn))) if turn else np.nan,
        median_daily_vol=medvol,
        first=recs[0]["date"], last=recs[-1]["date"],
        pos_years=int(sum(1 for y in yr if np.mean(yr[y]) > 0)), tot_years=len(yr),
        by_year={y: [round(float(np.mean(v)), 5), len(v)] for y, v in sorted(yr.items())},
        _series=[(r["date"], float(x), float(c_)) for r, x, c_ in zip(recs, a, cst)],
    )


def _currency_neutralise(s, symnames):
    """Regress the signal on currency-exposure dummies and keep the residual.

    Lane 5 named this as the residual threat it could not eliminate: ranking
    EURUSD, EURGBP, EURJPY together mechanically produces a EUR basket, so part
    of any 'cross-sectional' result is single-currency reversal restated.  Each
    pair XXXYYY loads +1 on XXX and -1 on YYY; projecting the signal off that
    span leaves only genuinely pair-specific (relative-value) content.
    """
    ccy = sorted({c for sym in symnames for c in _fx_pair(sym) if c})
    if len(ccy) < 3:
        return None
    ci = {c: i for i, c in enumerate(ccy)}
    X = np.zeros((len(symnames), len(ccy)))
    for i, sym in enumerate(symnames):
        b, q = _fx_pair(sym)
        if not b or b not in ci or q not in ci:
            return None
        X[i, ci[b]] += 1.0; X[i, ci[q]] -= 1.0
    try:
        beta, *_ = np.linalg.lstsq(X, s, rcond=None)
    except np.linalg.LinAlgError:
        return None
    res = s - X @ beta
    if res.std() < 1e-12:
        return None
    return res
