"""S1 - replicate Lane 1's VR<1 cell, then dissect it three ways it was not dissected.

Lane 1's ``vr2.py`` did three things this file deliberately does not:

  (a) it grouped by *UTC* session, so the broker-midnight rollover (21:00 UTC on
      EDT, 22:00 on EST) is split across two buckets inside a seven-hour window
      and cannot be isolated;
  (b) it ran ``d = d[np.isfinite(d.lr) & (d.lr != 0)]`` -- dropping flat bars.
      A stale quote that prints (+x, 0, -x) becomes (+x, -x) once the zero is
      dropped, which *manufactures* first-order negative autocorrelation.  In
      the late session flat M15 bars are common, so this is not a small edit;
  (c) it spliced the session-filtered return series across day boundaries, so a
      q=16 partial sum can straddle a 17-hour hole.

This file measures, in broker time, on contiguous within-day blocks, both with
and without the zero-return drop, and by broker HOUR so the rollover is a single
bucket.  It also runs the statistic that decides tradeability, which VR is not:
the gapped reversion regression  r_fwd(k) = a + b * r_trail(k)  with g bars of
daylight between the two windows.  g=0 is contaminated by any anchor defect at
the shared price; g>=1 is not.
"""
from __future__ import annotations
import json, math, os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from panel import m15_syms, classify   # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "receipts")
os.makedirs(OUT, exist_ok=True)

# Lane 1's ranked cell, plus the majors it names.
CELL = ["CHFJPY", "EURGBP", "EURJPY", "NZDUSD", "GBPJPY", "USDCHF",
        "USDCAD", "GBPUSD", "AUDUSD", "EURUSD", "USDJPY", "AUDJPY"]


def lomac(r, q):
    r = np.asarray(r, float); r = r[np.isfinite(r)]; n = len(r)
    if n < 20 * q:
        return None
    x = r - r.mean(); var1 = np.sum(x ** 2) / (n - 1)
    if var1 <= 0:
        return None
    cs = np.concatenate([[0.0], np.cumsum(x)]); yq = cs[q:] - cs[:-q]
    m = q * (n - q + 1) * (1 - q / n)
    vr = (np.sum(yq ** 2) / m) / var1
    x2 = x ** 2; den = (np.sum(x2)) ** 2; theta = 0.0
    for j in range(1, q):
        theta += ((2 * (q - j) / q) ** 2) * (np.sum(x2[j:] * x2[:-j]) / den)
    if theta <= 0:
        return None
    return dict(vr=float(vr), z=float((vr - 1) / math.sqrt(theta)), n=int(n), var1=float(var1))


def block_vr(df, q, drop_zero):
    """VR over contiguous within-(broker-day, session) blocks only -- no splicing.

    Lo-MacKinlay is computed on the pooled return vector but the q-sums are
    formed inside blocks, so no partial sum crosses a hole.
    """
    r_all, ysq, cnt = [], 0.0, 0
    for _, g in df.groupby("blk", sort=False):
        r = g["lr"].values
        if drop_zero:
            r = r[r != 0]
        r = r[np.isfinite(r)]
        if len(r) < q + 1:
            if len(r):
                r_all.append(r)
            continue
        r_all.append(r)
    if not r_all:
        return None
    pooled = np.concatenate(r_all)
    if len(pooled) < 20 * q:
        return None
    mu = pooled.mean(); var1 = np.sum((pooled - mu) ** 2) / (len(pooled) - 1)
    if var1 <= 0:
        return None
    for r in r_all:
        if len(r) < q:
            continue
        x = r - mu
        cs = np.concatenate([[0.0], np.cumsum(x)])
        y = cs[q:] - cs[:-q]
        ysq += float(np.sum(y ** 2)); cnt += len(y)
    if cnt < 30:
        return None
    varq = ysq / (cnt * q) * (1.0)          # unbiased-ish; scale handled by /q below
    vr = (ysq / cnt) / (q * var1)
    x = pooled - mu; x2 = x ** 2; den = (np.sum(x2)) ** 2; theta = 0.0
    for j in range(1, q):
        theta += ((2 * (q - j) / q) ** 2) * (np.sum(x2[j:] * x2[:-j]) / den)
    z = (vr - 1) / math.sqrt(theta) if theta > 0 else np.nan
    return dict(vr=float(vr), z=float(z), n=int(len(pooled)), nblk=int(cnt), var1=float(var1))


def gapped_beta(df, k, g, price="close"):
    """r_fwd(k) on r_trail(k) with g bars of daylight, inside contiguous blocks.

    Returns OLS beta, Newey-West-free t (blocks are non-overlapping by
    construction: we step by k so no observation is reused), n, and the implied
    round-trip amplitude in bp.
    """
    xs, ys, dts = [], [], []
    lp = np.log(df[price].values)
    blk = df["blk"].values
    idx = df["bt"].values
    i = 0
    N = len(df)
    while i + 2 * k + g < N:
        j0, j1, j2, j3 = i, i + k, i + k + g, i + 2 * k + g
        if blk[j0] == blk[j3]:
            xs.append(lp[j1] - lp[j0]); ys.append(lp[j3] - lp[j2]); dts.append(idx[j1])
            i = j3                      # non-overlapping
        else:
            i += 1
    if len(xs) < 100:
        return None
    x = np.asarray(xs); y = np.asarray(ys)
    sx = x.std(ddof=1)
    if sx == 0:
        return None
    b = np.cov(x, y, ddof=1)[0, 1] / np.var(x, ddof=1)
    a = y.mean() - b * x.mean()
    res = y - (a + b * x)
    se = math.sqrt(np.sum(res ** 2) / (len(x) - 2) / np.sum((x - x.mean()) ** 2))
    return dict(beta=float(b), t=float(b / se), n=int(len(x)),
                sd_x_bp=float(sx * 1e4), sd_y_bp=float(y.std(ddof=1) * 1e4),
                # amplitude actually recoverable: |beta| * sd(x), one-way, in bp
                amp_bp=float(abs(b) * sx * 1e4),
                dates=[str(pd.Timestamp(dts[0]))[:10], str(pd.Timestamp(dts[-1]))[:10]])


def sess_utc(h):
    return "tokyo" if h < 7 else ("london" if h < 12 else ("newyork" if h < 17 else "late"))


def main():
    d = m15_syms(CELL)
    d["lr"] = np.nan
    res_vr, res_beta, res_hour = [], [], []
    for sym, g in d.groupby("sym", sort=True):
        g = g.sort_values("bt").reset_index(drop=True)
        g["lr"] = np.log(g["close"]).diff()
        g["uh"] = pd.DatetimeIndex(g["ut"]).hour
        g["sess"] = g["uh"].map(sess_utc)
        g = g.dropna(subset=["lr"])

        # ---- A. replicate Lane 1 exactly (UTC session, spliced, zeros dropped)
        for sname in ["ALL", "late"]:
            gg = g if sname == "ALL" else g[g.sess == "late"]
            v = gg["lr"].values
            v = v[np.isfinite(v) & (v != 0)]
            st = lomac(v, 16)
            if st:
                res_vr.append(dict(sym=sym, method="LANE1_repro", sess=sname, q=16,
                                   drop_zero=True, **st))

        # ---- B. same cell, contiguous blocks, zeros KEPT vs DROPPED
        gl = g[g.sess == "late"].copy()
        gl["blk"] = gl["bdate"].astype(str)
        for dz in (True, False):
            st = block_vr(gl, 16, dz)
            if st:
                res_vr.append(dict(sym=sym, method="BLOCK_late", sess="late", q=16,
                                   drop_zero=dz, **st))

        # ---- C. by BROKER hour: where does the reversion actually live?
        gb = g.copy(); gb["blk"] = gb["bdate"].astype(str) + "_" + gb["bh"].astype(str)
        for bh, gh in gb.groupby("bh"):
            v = gh["lr"].values; v = v[np.isfinite(v)]
            if len(v) < 2000:
                continue
            ac1 = float(np.corrcoef(v[:-1], v[1:])[0, 1])
            st = lomac(v[v != 0], 4)
            res_hour.append(dict(sym=sym, bh=int(bh), n=len(v), ac1=ac1,
                                 frac_zero=float((v == 0).mean()),
                                 sd_bp=float(v.std() * 1e4),
                                 vr4=st["vr"] if st else np.nan,
                                 z4=st["z"] if st else np.nan))

        # ---- D. THE test: gapped reversion regression on the late block
        gl2 = g[g.sess == "late"].copy()
        gl2["blk"] = gl2["bdate"].astype(str)
        gl2 = gl2.sort_values("bt").reset_index(drop=True)
        for k in (4, 8, 16):
            for gap in (0, 1, 2, 4):
                r = gapped_beta(gl2, k, gap)
                if r:
                    res_beta.append(dict(sym=sym, cell="late_utc", k=k, gap=gap, **r))
        # and the same on the rollover-excluded late block
        roll = gl2["bh"].isin([23, 0])           # broker 23:00-00:59 straddles rollover
        gl3 = gl2[~roll].copy()
        gl3["blk"] = gl3["bdate"].astype(str) + "_" + (gl3["bh"] >= 1).astype(int).astype(str)
        gl3 = gl3.sort_values("bt").reset_index(drop=True)
        for k in (4, 8, 16):
            for gap in (0, 1):
                r = gapped_beta(gl3, k, gap)
                if r:
                    res_beta.append(dict(sym=sym, cell="late_no_rollover", k=k, gap=gap, **r))
        print("done", sym, flush=True)

    pd.DataFrame(res_vr).to_csv(f"{OUT}/S1_VR_METHOD_AB.csv", index=False)
    pd.DataFrame(res_hour).to_csv(f"{OUT}/S1_VR_BY_BROKER_HOUR.csv", index=False)
    pd.DataFrame(res_beta).to_csv(f"{OUT}/S1_GAPPED_BETA.csv", index=False)
    print("written", OUT)


if __name__ == "__main__":
    main()
