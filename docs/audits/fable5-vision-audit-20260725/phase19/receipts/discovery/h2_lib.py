"""h2_lib — shared substrate for lane h2 (where is the EDGE biggest).

Population: the LIVE-EXPRESSIBLE (at-market) cohort, January + February + March 2026,
n = 43,755, built by e_build_atmkt.py.  Repaired contract = D1E1 = entry delayed k=5 M1
bars (market order at the close of path bar 5) + TRAIL025 exit (no target, initial stop
-1R, stop trails 0.25R behind the running MFE).

Reference cell (e-stack E_ATMKT_POOLED_V1.json -> D1E1G0):
    n 43755  gross +0.038342  cost 0.181834  net -0.143492  t_gross +12.345
"""
from __future__ import annotations

import gzip
import json
import math
import os
from datetime import date

D = os.path.dirname(os.path.abspath(__file__))
MONTHS = [("2026-01", "e_JAN_ATMKT_V1.jsonl.gz"),
          ("2026-02", "e_FEB_ATMKT_V1.jsonl.gz"),
          ("2026-03", "e_MAR_ATMKT_V1.jsonl.gz")]

GCOL = "K5_TRAIL025"        # the repaired contract
DOW = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def load(gcol=GCOL):
    rows = []
    for m, f in MONTHS:
        for line in gzip.open(os.path.join(D, f), "rt"):
            if not line.strip():
                continue
            r = json.loads(line)
            g = r.get(gcol)
            c = r.get("cost_true")
            if g is None or c is None:
                continue
            r["month"] = m
            r["g"] = float(g)
            r["c"] = float(c)
            r["net"] = r["g"] - r["c"]
            rdp = float(r["rdp"])
            r["g_bps"] = r["g"] * rdp * 1e4
            r["c_bps"] = r["c"] * rdp * 1e4
            r["net_bps"] = r["net"] * rdp * 1e4
            y, mo, dd = (int(x) for x in r["day"].split("-"))
            r["dow"] = DOW[date(y, mo, dd).weekday()]
            rows.append(r)
    return rows


def add_vol_state(rows, key="symbol", n_tiles=3, field="rdp", out="vol"):
    """Within-`key` tiles of `field` (ex-ante: risk_distance / entry_price)."""
    by = {}
    for r in rows:
        by.setdefault(r[key], []).append(float(r[field]))
    cuts = {}
    for k, v in by.items():
        v.sort()
        cuts[k] = [v[int(round(i * (len(v) - 1) / n_tiles))] for i in range(1, n_tiles)]
    lab = {3: ["lo", "mid", "hi"], 2: ["lo", "hi"],
           4: ["q1", "q2", "q3", "q4"], 5: ["p1", "p2", "p3", "p4", "p5"]}[n_tiles]
    for r in rows:
        x = float(r[field])
        i = 0
        for cv in cuts[r[key]]:
            if x > cv:
                i += 1
        r[out] = lab[i]
    return cuts


def add_global_tiles(rows, field, out, n_tiles=5):
    v = sorted(float(r[field]) for r in rows if r.get(field) is not None)
    cuts = [v[int(round(i * (len(v) - 1) / n_tiles))] for i in range(1, n_tiles)]
    for r in rows:
        x = r.get(field)
        if x is None:
            r[out] = None
            continue
        i = 0
        for cv in cuts:
            if float(x) > cv:
                i += 1
        r[out] = "d%d" % (i + 1)
    return cuts


# ------------------------------------------------------------------ statistics
def _mean(v):
    return sum(v) / len(v) if v else float("nan")


def _se(v):
    n = len(v)
    if n < 2:
        return float("nan")
    m = sum(v) / n
    return math.sqrt(sum((x - m) ** 2 for x in v) / (n - 1) / n)


def cluster_se(vals, clusters):
    """Cluster-robust SE of the mean, clustering on `clusters` (one per value).
    SE = sqrt( sum_g (sum_{i in g} (x_i - xbar))^2 ) / n , with the standard
    G/(G-1) small-sample correction."""
    n = len(vals)
    if n < 2:
        return float("nan")
    m = sum(vals) / n
    agg = {}
    for x, g in zip(vals, clusters):
        agg[g] = agg.get(g, 0.0) + (x - m)
    G = len(agg)
    if G < 2:
        return float("nan")
    s = sum(a * a for a in agg.values()) * G / (G - 1)
    return math.sqrt(s) / n


def cell_stats(rows, min_n=1):
    """Full statistics for one cell of trades."""
    n = len(rows)
    if n < min_n:
        return None
    g = [r["g"] for r in rows]
    c = [r["c"] for r in rows]
    nt = [r["net"] for r in rows]
    gb = [r["g_bps"] for r in rows]
    cb = [r["c_bps"] for r in rows]
    days = [r["day"] for r in rows]
    mg, mc, mn = _mean(g), _mean(c), _mean(nt)
    seg, sen = _se(g), _se(nt)
    cseg, csen = cluster_se(g, days), cluster_se(nt, days)
    byday = {}
    for r in rows:
        byday.setdefault(r["day"], []).append(r["g"])
    dpos = sum(1 for v in byday.values() if _mean(v) > 0)
    bydn = {}
    for r in rows:
        bydn.setdefault(r["day"], []).append(r["net"])
    dposn = sum(1 for v in bydn.values() if _mean(v) > 0)
    bym = {}
    for r in rows:
        bym.setdefault(r["month"], []).append(r)
    mgb, mcb = _mean(gb), _mean(cb)
    out = {
        "n": n,
        "gross_r": round(mg, 6), "se_g": round(seg, 6),
        "t_g": round(mg / seg, 4) if seg and seg == seg and seg > 0 else None,
        "t_g_clu": round(mg / cseg, 4) if cseg == cseg and cseg > 0 else None,
        "cost_r": round(mc, 6),
        "net_r": round(mn, 6), "se_net": round(sen, 6),
        "t_net": round(mn / sen, 4) if sen and sen == sen and sen > 0 else None,
        "t_net_clu": round(mn / csen, 4) if csen == csen and csen > 0 else None,
        "gross_bps": round(mgb, 5), "cost_bps": round(mcb, 5),
        "net_bps": round(mgb - mcb, 5),
        "edge_cost_r": round(mg / mc, 4) if mc > 0 else None,
        "edge_cost_bps": round(mgb / mcb, 4) if mcb > 0 else None,
        "days": len(byday), "days_pos_gross": dpos,
        "day_pos_frac": round(dpos / len(byday), 4) if byday else None,
        "days_pos_net": dposn,
        "day_pos_frac_net": round(dposn / len(bydn), 4) if bydn else None,
        "win_rate": round(sum(1 for x in g if x > 0) / n, 4),
        "mean_rdp_bps": round(_mean([float(r["rdp"]) for r in rows]) * 1e4, 4),
        "months": len(bym),
    }
    for m, _f in MONTHS:
        sub = bym.get(m)
        if sub:
            out["g_" + m] = round(_mean([r["g"] for r in sub]), 6)
            out["net_" + m] = round(_mean([r["net"] for r in sub]), 6)
            out["n_" + m] = len(sub)
        else:
            out["g_" + m] = None
            out["net_" + m] = None
            out["n_" + m] = 0
    # split-half on day parity (day-of-month odd/even) -- within-window stability
    a = [r for r in rows if int(r["day"][8:10]) % 2 == 1]
    b = [r for r in rows if int(r["day"][8:10]) % 2 == 0]
    out["g_odd"] = round(_mean([r["g"] for r in a]), 6) if a else None
    out["g_even"] = round(_mean([r["g"] for r in b]), 6) if b else None
    out["net_odd"] = round(_mean([r["net"] for r in a]), 6) if a else None
    out["net_even"] = round(_mean([r["net"] for r in b]), 6) if b else None
    out["n_odd"], out["n_even"] = len(a), len(b)
    return out


def group(rows, keyfn):
    out = {}
    for r in rows:
        k = keyfn(r)
        if k is None:
            continue
        out.setdefault(k, []).append(r)
    return out


def spearman(x, y):
    n = len(x)
    if n < 3:
        return None

    def rk(v):
        idx = sorted(range(n), key=lambda i: v[i])
        r = [0.0] * n
        i = 0
        while i < n:
            j = i
            while j + 1 < n and v[idx[j + 1]] == v[idx[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1
            for k in range(i, j + 1):
                r[idx[k]] = avg
            i = j + 1
        return r
    rx, ry = rk(x), rk(y)
    mx, my = _mean(rx), _mean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    dx = math.sqrt(sum((a - mx) ** 2 for a in rx))
    dy = math.sqrt(sum((b - my) ** 2 for b in ry))
    return num / (dx * dy) if dx > 0 and dy > 0 else None


def pearson(x, y):
    n = len(x)
    if n < 3:
        return None
    mx, my = _mean(x), _mean(y)
    num = sum((a - mx) * (b - my) for a, b in zip(x, y))
    dx = math.sqrt(sum((a - mx) ** 2 for a in x))
    dy = math.sqrt(sum((b - my) ** 2 for b in y))
    return num / (dx * dy) if dx > 0 and dy > 0 else None
