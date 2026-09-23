"""b1_lib — ONE scorer for the book, over the five-month at-market substrate.

SUBSTRATE
    h5_SUBSTRATE_5M.jsonl.gz : 69,480 live-expressible (at-market) candidates,
    2026-01 .. 2026-05, built by h5 with the UNMODIFIED e_build_atmkt.py.
    Contract menu precomputed at k in {0,1,2,3,5,10,15,20,30,45,60} x
    {INC, TRAIL025, TS90S1, STOPONLY, T3S1, TS60S1}.

COST
    cost_true       = flat per-symbol tick-median spread + broker commission +
                      measured live slippage  (l10 / e_lib.real_cost_parts)
    cost_true_hour  = the same, with the spread taken at the row's own BROKER HOUR
                      (NEW_YORK_PLUS_7, correct across the 2026-03 DST split).
                      This lane uses cost_true_hour for every headline number: it is
                      the strictest cost basis any lane in the wave built and it is
                      21.2% above the flat basis the swarm published (h6-F7).

    cost_bps        = cost_true_hour * rdp * 1e4        (round-trip toll, price space)
    All bps figures are trade-weighted means of per-row bps, i.e. a CONSTANT-NOTIONAL
    book; all R figures are a CONSTANT-RISK book. Both are reported, always.

NO TRAIL.
    The estate's ratified honest-trail bound (B613 / AD 95.8% intrabar; h6-F8) shows a
    trail tested only from the next bar manufactures +0.084 R/trade of bar-resolution
    premium -- 2.19x the entire swarm headline. Every contract this lane ships is
    trail-free by construction, so no number here contains that premium.
"""
from __future__ import annotations

import gzip
import json
import math
import os

D = os.path.dirname(os.path.abspath(__file__))
SUB = f"{D}/h5_SUBSTRATE_5M.jsonl.gz"
HUNT_MONTHS = ("2026-01", "2026-02", "2026-03")
OOS_MONTHS = ("2026-04", "2026-05")

_cache = {}


def load(months=None):
    if "rows" not in _cache:
        rows = []
        for ln in gzip.open(SUB, "rt"):
            if not ln.strip():
                continue
            r = json.loads(ln)
            r["cost_bps"] = (r["cost_true_hour"] * r["rdp"] * 1e4
                             if r.get("cost_true_hour") is not None else None)
            r["cost_bps_flat"] = (r["cost_true"] * r["rdp"] * 1e4
                                  if r.get("cost_true") is not None else None)
            rows.append(r)
        _cache["rows"] = rows
    rows = _cache["rows"]
    if months is None:
        return rows
    ms = set(months)
    return [r for r in rows if r["month"] in ms]


# ------------------------------------------------------------------ statistics
def _mean(v):
    return sum(v) / len(v) if v else None


def _t(v):
    n = len(v)
    if n < 3:
        return None
    m = sum(v) / n
    s2 = sum((x - m) ** 2 for x in v) / (n - 1)
    if s2 <= 0:
        return None
    return m / math.sqrt(s2 / n)


def score(rs, gross_key, cost_key="cost_true_hour"):
    """Every number b1 reports for one book, on one row set."""
    n = len(rs)
    if n == 0:
        return {"n": 0}
    g = [r[gross_key] for r in rs]
    c = [r[cost_key] for r in rs]
    net = [a - b for a, b in zip(g, c)]
    rdp = [r["rdp"] for r in rs]
    gb = [a * d * 1e4 for a, d in zip(g, rdp)]
    cb = [b * d * 1e4 for b, d in zip(c, rdp)]
    nb = [a - b for a, b in zip(gb, cb)]

    mg, mc, mn = _mean(g), _mean(c), _mean(net)
    mgb, mcb, mnb = _mean(gb), _mean(cb), _mean(nb)

    byday = {}
    for r, x in zip(rs, net):
        byday.setdefault(r["day"], []).append(x)
    t_day = None
    if len(byday) >= 3 and mn is not None:
        ss = sum((sum(x - mn for x in v)) ** 2 for v in byday.values())
        if ss > 0:
            G = len(byday)
            se = math.sqrt(ss) / n * math.sqrt(G / max(G - 1, 1))
            t_day = mn / se

    days = sorted(byday)
    cum, eq, peak, dd = 0.0, [], -1e18, 0.0
    for d in days:
        cum += sum(byday[d])
        eq.append(cum)
        peak = max(peak, cum)
        dd = min(dd, cum - peak)

    out = {
        "n": n,
        "gross_R": mg, "cost_R": mc, "net_R": mn,
        "ratio_R": (mg / mc if mc else None),
        "gross_bps": mgb, "cost_bps": mcb, "net_bps": mnb,
        "ratio_bps": (mgb / mcb if mcb else None),
        "win_rate": sum(1 for x in net if x > 0) / n,
        "win_rate_gross": sum(1 for x in g if x > 0) / n,
        "t_net": _t(net), "t_gross": _t(g), "t_net_day": t_day,
        "n_days": len(byday),
        "n_days_net_pos": sum(1 for d in days if _mean(byday[d]) > 0),
        "n_symbols": len({r["symbol"] for r in rs}),
        "months": sorted({r["month"] for r in rs}),
        "total_net_R": cum, "max_dd_R": dd,
        "equity_net_R": [round(x, 4) for x in eq],
        "equity_days": days,
        "mean_rdp_bps": _mean([d * 1e4 for d in rdp]),
    }
    for m in ("2026-01", "2026-02", "2026-03", "2026-04", "2026-05"):
        sub = [i for i, r in enumerate(rs) if r["month"] == m]
        if not sub:
            out["m_" + m] = None
            continue
        gm, cm = _mean([g[i] for i in sub]), _mean([c[i] for i in sub])
        out["m_" + m] = {"n": len(sub), "gross_R": gm, "cost_R": cm,
                         "net_R": gm - cm, "ratio_R": (gm / cm if cm else None),
                         "net_bps": _mean([nb[i] for i in sub])}
    return out


def bootstrap_days(rs, gross_key, cost_key="cost_true_hour", B=2000, seed=20260806):
    """Day-block bootstrap on mean net R. Days are the resampling unit."""
    import random
    rnd = random.Random(seed)
    byday = {}
    for r in rs:
        byday.setdefault(r["day"], []).append(r[gross_key] - r[cost_key])
    ds = list(byday.values())
    if len(ds) < 3:
        return None
    G = len(ds)
    out = []
    for _ in range(B):
        s, k = 0.0, 0
        for _ in range(G):
            v = ds[rnd.randrange(G)]
            s += sum(v)
            k += len(v)
        out.append(s / k)
    out.sort()
    return {"B": B, "p025": out[int(0.025 * B)], "p50": out[B // 2],
            "p975": out[int(0.975 * B) - 1],
            "p_le_0": sum(1 for x in out if x <= 0) / B}


def by_group(rs, key, gross_key, cost_key="cost_true_hour", minn=1):
    g = {}
    for r in rs:
        g.setdefault(r[key] if not callable(key) else key(r), []).append(r)
    return {k: score(v, gross_key, cost_key) for k, v in g.items() if len(v) >= minn}


def slim(s, drop=("equity_net_R", "equity_days")):
    return {k: (round(v, 6) if isinstance(v, float) else v)
            for k, v in s.items() if k not in drop}
