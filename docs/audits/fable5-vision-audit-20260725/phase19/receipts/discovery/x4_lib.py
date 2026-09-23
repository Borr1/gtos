#!/usr/bin/env python3
"""x4 shared substrate: join working set + decision anchor + intra-bar features,
define the exact populations and outcomes l3 used so effect sizes are comparable."""
from __future__ import annotations
import gzip, json, math, os, sys
import numpy as np

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import w0_ws

INTRA = os.path.join(D, "x4_INTRABAR_V1.jsonl.gz")
ANCH = os.path.join(D, "w0cap2_DECISION_ANCHOR_V1.jsonl.gz")

# features stamped by legality class
CONFIRM_PREFIX = "c0_"
NONFEAT = {"candidate_id", "decision_time_utc", "n_m1_in_bar", "c0_present"}


def load_joined():
    rows = w0_ws.load()
    anch = {}
    with gzip.open(ANCH, "rt") as f:
        for ln in f:
            a = json.loads(ln)
            anch[(a["candidate_id"], a["decision_time_utc"])] = a
    intra = {}
    with gzip.open(INTRA, "rt") as f:
        for ln in f:
            x = json.loads(ln)
            intra[(x["candidate_id"], x["decision_time_utc"])] = x
    out = []
    for r in rows:
        k = w0_ws.key(r)
        x = intra.get(k)
        if x is None:
            continue
        a = anch.get(k)
        rec = dict(r)
        rec["_mkt_r_close"] = a["mkt_r_close"] if a else None
        rec["_born"] = born(a["mkt_r_close"]) if a else None
        rec["_takeable"] = (a is not None and a["mkt_r_close"] > -1.0)
        rec["_day"] = r["decision_time_utc"][:10]
        rec["_f"] = x
        out.append(rec)
    return out


def born(m):
    if m is None:
        return None
    return ("born_past_stop" if m <= -1.0 else
            "born_marketable" if m < 0.0 else
            "born_at_limit" if m == 0.0 else "born_resting")


def feature_names(recs):
    ks = set()
    for r in recs[:4000]:
        ks |= set(r["_f"].keys())
    ks -= NONFEAT
    return sorted(ks)


def col(recs, name):
    return np.array([_num(r["_f"].get(name)) for r in recs], dtype=float)


def _num(v):
    if v is None:
        return np.nan
    if isinstance(v, bool):
        return 1.0 if v else 0.0
    try:
        f = float(v)
    except (TypeError, ValueError):
        return np.nan
    return f if math.isfinite(f) else np.nan


def cohens_d(a, b):
    a = a[np.isfinite(a)]; b = b[np.isfinite(b)]
    if len(a) < 8 or len(b) < 8:
        return np.nan
    va, vb = a.var(ddof=1), b.var(ddof=1)
    sp = math.sqrt(((len(a) - 1) * va + (len(b) - 1) * vb) / (len(a) + len(b) - 2))
    return (a.mean() - b.mean()) / sp if sp > 0 else np.nan


def auc(pos, neg):
    """Mann-Whitney AUC of `pos` scored above `neg`."""
    pos = pos[np.isfinite(pos)]; neg = neg[np.isfinite(neg)]
    if len(pos) < 8 or len(neg) < 8:
        return np.nan
    allv = np.concatenate([pos, neg])
    order = allv.argsort(kind="mergesort")
    ranks = np.empty(len(allv), dtype=float)
    ranks[order] = np.arange(1, len(allv) + 1, dtype=float)
    # average ties
    sv = allv[order]
    i = 0
    while i < len(sv):
        j = i
        while j + 1 < len(sv) and sv[j + 1] == sv[i]:
            j += 1
        if j > i:
            ranks[order[i:j + 1]] = (i + 1 + j + 1) / 2.0
        i = j + 1
    rp = ranks[:len(pos)].sum()
    return (rp - len(pos) * (len(pos) + 1) / 2.0) / (len(pos) * len(neg))


def iv_deciles(x, y, nb=10):
    """Information value of a numeric feature against a binary label, decile-binned."""
    m = np.isfinite(x)
    x, y = x[m], y[m]
    if len(x) < 200 or y.sum() < 20 or (1 - y).sum() < 20:
        return np.nan
    qs = np.unique(np.quantile(x, np.linspace(0, 1, nb + 1)))
    if len(qs) < 3:
        return np.nan
    idx = np.clip(np.searchsorted(qs, x, side="right") - 1, 0, len(qs) - 2)
    P, N = y.sum(), (1 - y).sum()
    iv = 0.0
    for b in range(len(qs) - 1):
        s = idx == b
        p = y[s].sum() / P
        q = (1 - y[s]).sum() / N
        if p > 0 and q > 0:
            iv += (p - q) * math.log(p / q)
    return iv


def outcomes(recs):
    """Return the population masks and label vectors used everywhere in x4."""
    take = np.array([bool(r["_takeable"]) for r in recs])
    band = np.array([r["outcome_band"] for r in recs])
    hon = np.array([r["fill_honest_which_came_first"] for r in recs])
    honr = np.array([_num(r["fill_honest_walk_r"]) for r in recs])
    gr = np.array([_num(r["gross_r"]) for r in recs])
    b1 = np.array([r["bars_to_entry_touch"] == 1 for r in recs])
    return {"takeable": take, "band": band, "hon": hon, "honr": honr, "gross": gr,
            "bar1": b1}


def day_block_boot(vals, days, n=2000, seed=17):
    """Block bootstrap by trading day. Returns (mean, lo95, hi95, p_le_0)."""
    vals = np.asarray(vals, dtype=float)
    m = np.isfinite(vals)
    vals, days = vals[m], np.asarray(days)[m]
    ud = np.unique(days)
    idx = {d: np.where(days == d)[0] for d in ud}
    rs = np.random.RandomState(seed)
    out = np.empty(n)
    for i in range(n):
        pick = rs.randint(0, len(ud), len(ud))
        sel = np.concatenate([idx[ud[p]] for p in pick])
        out[i] = vals[sel].mean()
    return (float(vals.mean()), float(np.percentile(out, 2.5)),
            float(np.percentile(out, 97.5)), float((out <= 0).mean()))


def perm_p(a, b, n=5000, seed=11):
    """Two-sided permutation p on the difference of means."""
    a = np.asarray(a, float); b = np.asarray(b, float)
    a = a[np.isfinite(a)]; b = b[np.isfinite(b)]
    obs = a.mean() - b.mean()
    pool = np.concatenate([a, b]); na = len(a)
    rs = np.random.RandomState(seed)
    cnt = 0
    for _ in range(n):
        rs.shuffle(pool)
        if abs(pool[:na].mean() - pool[na:].mean()) >= abs(obs) - 1e-15:
            cnt += 1
    return (cnt + 1) / (n + 1)
