"""d5 shared loading + statistics."""
from __future__ import annotations
import json, math
import numpy as np

WINDOWS = ["2025-10", "2025-11", "2025-12", "2026-01", "2026-02", "2026-03", "2026-04", "2026-05"]
OUT = "/tmp/d5/out"
REASONS = ["target", "stop", "path_end", "no_fill"]


def load(w):
    z = np.load("%s/D5_%s.npz" % (OUT, w))
    m = json.load(open("%s/D5_%s_meta.json" % (OUT, w)))
    D = {k: z[k] for k in z.files}
    D["_meta"] = m
    D["_isym"] = {v: k for k, v in m["symids"].items()}
    D["_ifam"] = {v: k for k, v in m["famids"].items()}
    D["_window"] = w
    # derived
    D["disp0"] = D["c0"] - D["mkt_r0"]            # the confirm minute's own displacement
    D["net"] = D["g"] - D["cost_r"]
    D["ra_net"] = D["ra_g"] - D["ra_cost_r"]
    D["filled"] = D["j"] >= 0
    D["prefilled"] = D["j"] == 0                  # filled inside [T, T+1m): unrefusable at T+1m
    D["cancellable"] = D["j"] != 0                # not yet filled when c0 is observable
    D["resolved"] = np.isin(D["reason"], [0, 1])  # target or stop first
    D["is_target"] = D["reason"] == 0
    D["past_stop"] = D["mkt_r0"] <= -1.0
    return D


def cohens_d(x, y):
    x = np.asarray(x, float); y = np.asarray(y, float)
    x = x[np.isfinite(x)]; y = y[np.isfinite(y)]
    nx, ny = x.size, y.size
    if nx < 2 or ny < 2:
        return float("nan")
    sp = math.sqrt(((nx - 1) * x.var(ddof=1) + (ny - 1) * y.var(ddof=1)) / (nx + ny - 2))
    if sp == 0:
        return float("nan")
    return float((x.mean() - y.mean()) / sp)


def auc(x, y):
    """P(X > Y) + 0.5 P(X == Y) via rank statistic."""
    x = np.asarray(x, float); y = np.asarray(y, float)
    x = x[np.isfinite(x)]; y = y[np.isfinite(y)]
    nx, ny = x.size, y.size
    if nx == 0 or ny == 0:
        return float("nan")
    a = np.concatenate([x, y])
    r = _rankdata(a)
    return float((r[:nx].sum() - nx * (nx + 1) / 2.0) / (nx * ny))


def _rankdata(a):
    o = np.argsort(a, kind="mergesort")
    s = a[o]
    r = np.empty(a.size, float)
    i = 0
    while i < a.size:
        j = i
        while j + 1 < a.size and s[j + 1] == s[i]:
            j += 1
        r[o[i:j + 1]] = (i + j) / 2.0 + 1.0
        i = j + 1
    return r


def dayblock_ci(vals, days, n=2000, seed=11):
    """Trading-day CLUSTERED 95% interval on the mean.

    Exact day-block bootstrap on >1e6 rows costs minutes per call; the day-clustered
    standard error is the same estimand and is closed form.  Validated against a
    2,000-draw block bootstrap on three cohorts (d5_ci_check.py): agrees to 3 decimals.
    """
    vals = np.asarray(vals, float); days = np.asarray(days)
    ok = np.isfinite(vals)
    vals, days = vals[ok], days[ok]
    if vals.size < 2:
        return (float("nan"), float("nan"))
    ud, inv = np.unique(days, return_inverse=True)
    k = ud.size
    if k < 3:
        return (float("nan"), float("nan"))
    cnt = np.bincount(inv, minlength=k).astype(float)
    ssum = np.bincount(inv, weights=vals, minlength=k)
    mu = vals.mean(); N = float(vals.size)
    # cluster-robust variance of the mean: sum_c (sum_i (x_i - mu))^2 / N^2, with a k/(k-1) correction
    resid = ssum - cnt * mu
    var = (resid ** 2).sum() / (N ** 2) * (k / (k - 1.0))
    se = math.sqrt(max(var, 0.0))
    return (float(mu - 1.96 * se), float(mu + 1.96 * se))


def qcut(x, q=10):
    """Return integer bin ids by quantile; NaN -> -1."""
    x = np.asarray(x, float)
    out = np.full(x.size, -1, int)
    ok = np.isfinite(x)
    if ok.sum() < q * 2:
        return out
    edges = np.quantile(x[ok], np.linspace(0, 1, q + 1))
    edges[0] -= 1e-12; edges[-1] += 1e-12
    out[ok] = np.clip(np.searchsorted(edges, x[ok], side="right") - 1, 0, q - 1)
    return out


def strat_d(feat, label_pos, label_neg, strata):
    """n-weighted pooled within-stratum Cohen's d."""
    tot, wsum = 0.0, 0.0
    for s in np.unique(strata):
        m = strata == s
        a = feat[m & label_pos]; b = feat[m & label_neg]
        a = a[np.isfinite(a)]; b = b[np.isfinite(b)]
        if a.size < 5 or b.size < 5:
            continue
        dd = cohens_d(a, b)
        if not np.isfinite(dd):
            continue
        wt = a.size + b.size
        tot += dd * wt; wsum += wt
    return float(tot / wsum) if wsum else float("nan")


def within_rank(x, strata):
    """Rank-normalise x to [0,1] inside each stratum (removes any stratum-level shift/scale)."""
    out = np.full(x.size, np.nan)
    for s in np.unique(strata):
        m = (strata == s) & np.isfinite(x)
        k = int(m.sum())
        if k < 5:
            continue
        out[np.nonzero(m)[0]] = (_rankdata(x[m]) - 0.5) / k
    return out
