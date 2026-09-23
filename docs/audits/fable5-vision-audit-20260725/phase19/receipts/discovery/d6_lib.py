"""d6_lib — loaders and estimators over the d6 per-trade dataset."""
from __future__ import annotations

import glob
import gzip
import json
import os
from collections import Counter, defaultdict

import numpy as np

TRADES = "/tmp/d6/trades"

AT_MARKET = (
    "displacement_continuation", "liquidity_sweep_reclaim",
    "structural_distance_extreme", "volatility_compression_expansion",
    "session_open_range_break", "regime_transition_break", "cross_asset_lead_lag",
)
EARLY5 = (
    "displacement_continuation", "liquidity_sweep_reclaim",
    "session_open_range_break", "regime_transition_break",
    "volatility_compression_expansion",
)
POI = ("current_fvg_fill", "current_ob_retest", "current_breaker_re_entry")


def months_available():
    return sorted(os.path.basename(p)[:6] for p in glob.glob(os.path.join(TRADES, "*.jsonl.gz")))


def load(month, fams=None):
    p = os.path.join(TRADES, f"{month}.jsonl.gz")
    out = []
    with gzip.open(p, "rt") as fh:
        for line in fh:
            r = json.loads(line)
            if fams is not None and r["f"] not in fams:
                continue
            out.append(r)
    return out


# ------------------------------------------------------------------ estimators

def summarise(trades, label="", tkey="C", target=2.0):
    """trades: list of (row, armkey). Returns the standard economics block."""
    g, c, days, ex, tr, risk = [], [], [], [], [], []
    by_day = defaultdict(lambda: [0.0, 0])
    gk = "g2" if target == 2.0 else "g15"
    xk = "x2" if target == 2.0 else "x15"
    ck = "cr" if target == 2.0 else "cr15"
    for r, arm in trades:
        a = r.get(arm)
        if not a:
            continue
        gg = a[gk]
        cc = a[ck]
        g.append(gg)
        c.append(cc)
        ex.append(a[xk])
        risk.append(a["d"])
        d = r["day_part"] if arm in ("P", "D") else r["day_close"]
        by_day[d][0] += gg - cc
        by_day[d][1] += 1
    if not g:
        return {"label": label, "n": 0}
    g = np.array(g)
    c = np.array(c)
    n = g - c
    exc = Counter(ex)
    return {
        "label": label, "n": int(len(g)),
        "gross_r": float(g.mean()), "cost_r": float(c.mean()),
        "net_r": float(n.mean()),
        "total_net_r": float(n.sum()),
        "win_rate_gross": float((g > 0).mean()),
        "truncation_share": exc.get("path_end", 0) / len(g),
        "exit_mix": {k: v / len(g) for k, v in exc.items()},
        "median_risk_px": float(np.median(risk)),
        "n_days": len(by_day),
        "days_net_positive": sum(1 for d in by_day if by_day[d][0] > 0),
        "boot": bootstrap_days(by_day),
    }


def bootstrap_days(by_day, n=4000, seed=20260806):
    days = sorted(by_day)
    if not days:
        return None
    s = np.array([by_day[d][0] for d in days], dtype=float)
    cnt = np.array([by_day[d][1] for d in days], dtype=float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(days), size=(n, len(days)))
    num = s[idx].sum(axis=1)
    den = cnt[idx].sum(axis=1)
    den[den == 0] = np.nan
    m = num / den
    m = m[~np.isnan(m)]
    return {
        "mean": float(s.sum() / cnt.sum()) if cnt.sum() else None,
        "ci95_lo": float(np.percentile(m, 2.5)),
        "ci95_hi": float(np.percentile(m, 97.5)),
        "p_le_0": float((m <= 0).mean()),
        "n_days": len(days),
        "days_positive": int(sum(1 for d in days if by_day[d][0] > 0)),
    }


def paired_delta(rows, a="P", b="C", target=2.0, day_from="close"):
    """Per-row (arm a) - (arm b), day-blocked bootstrap of the mean."""
    gk = "g2" if target == 2.0 else "g15"
    ck = "cr" if target == 2.0 else "cr15"
    by_day = defaultdict(lambda: [0.0, 0])
    vals = []
    for r in rows:
        A, B = r.get(a), r.get(b)
        if not A or not B:
            continue
        d = (A[gk] - A[ck]) - (B[gk] - B[ck])
        day = r["day_close"] if day_from == "close" else r["day_part"]
        by_day[day][0] += d
        by_day[day][1] += 1
        vals.append(d)
    if not vals:
        return None
    out = bootstrap_days(by_day)
    out["n"] = len(vals)
    return out


def paired_delta_gross(rows, a="P", b="C", target=2.0):
    gk = "g2" if target == 2.0 else "g15"
    by_day = defaultdict(lambda: [0.0, 0])
    n = 0
    for r in rows:
        A, B = r.get(a), r.get(b)
        if not A or not B:
            continue
        by_day[r["day_close"]][0] += A[gk] - B[gk]
        by_day[r["day_close"]][1] += 1
        n += 1
    if not n:
        return None
    out = bootstrap_days(by_day)
    out["n"] = n
    return out
