"""x1-G — the entry-anchor time curve, and the two limit orders that exploit it.

x1-F found the confirm minute carries no information: E3 == P7 to 0.00004 R. What it
found instead is a MONOTONE decay in the entry minute. This maps that decay across a full
30-minute window (the decision bar and the one before it) and prices two implementable
limit-order contracts against it.

Every arm: entry at the close of minute m (m measured from the decision bar's open;
negative m = the previous M15 bar), stop at the ORIGINAL risk distance d0 from that entry,
target at target_rr * d0. Cost is therefore identical across arms and the pool's own cost_r
applies unchanged.

Two horizon conventions, both reported:
  HEND  every arm ends at decision_time + 120min (early arms get more time)
  HDUR  every arm runs 120 minutes from its own entry (equal duration)

LIMIT arms (fill-or-nothing, unfilled books 0.0):
  LOPEN  resting limit at the decision bar's OPEN price, live from the decision to +120min
  LMID   resting limit at the midpoint of (bar open, bar close)
"""
from __future__ import annotations

import csv
import gzip
import json
import math
import os
import statistics
import sys
from bisect import bisect_left
from collections import defaultdict
from datetime import datetime, timedelta

ROOT = "/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801"
DISC = f"{ROOT}/docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery"
BARS = ("/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/"
        "phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/bars")
M1DIRS = ["bridge_ftmo_m1_202512", "bridge_ftmo_m1_202601", "bridge_ftmo_m1_202602"]
MINUTES = list(range(-15, 15))


def load_m1(symbol):
    rows, seen = [], set()
    for d in M1DIRS:
        p = f"{BARS}/{d}/{symbol}_M1.csv"
        if not os.path.exists(p):
            continue
        with open(p, newline="") as f:
            rd = csv.reader(f); next(rd)
            for r in rd:
                if r[0] in seen:
                    continue
                seen.add(r[0]); rows.append((r[0], float(r[1]), float(r[2]), float(r[3]), float(r[4])))
    rows.sort(key=lambda x: x[0])
    return [x[0] for x in rows], rows


def walk(bars, side, entry, stop, tp):
    d = abs(entry - stop)
    if d <= 0 or not bars:
        return None
    for b in bars:
        _, o, h, l, c = b
        if side == "LONG":
            hs, ht = l <= stop, h >= tp
        else:
            hs, ht = h >= stop, l <= tp
        if hs:
            return -1.0
        if ht:
            return abs(tp - entry) / d
    c = bars[-1][4]
    return (c - entry) / d if side == "LONG" else (entry - c) / d


def cl(vals, days):
    g = defaultdict(list)
    for v, k in zip(vals, days):
        g[k].append(v)
    gm = [statistics.fmean(v) for v in g.values()]
    if not vals:
        return None
    se = statistics.stdev(gm) / math.sqrt(len(gm)) if len(gm) > 1 else 0.0
    return {"mean": round(statistics.fmean(vals), 6), "n": len(vals), "n_days": len(gm),
            "day_clustered_t": round(statistics.fmean(gm) / se, 4) if se > 0 else None,
            "days_positive": sum(1 for x in gm if x > 0)}


def main():
    pool = {}
    with gzip.open(f"{DISC}/w0_WORKING_SET.jsonl.gz", "rt") as f:
        for line in f:
            r = json.loads(line)
            pool[(r["candidate_id"], r["decision_time_utc"])] = r
    ew = [json.loads(l) for l in gzip.open(f"{DISC}/x1_E_E3_ROWS_V1.jsonl.gz", "rt")]
    by_sym = defaultdict(list)
    for r in ew:
        by_sym[r["symbol"]].append(r)

    out = []
    for sym in sorted(by_sym):
        m1t, m1 = load_m1(sym)
        for r in by_sym[sym]:
            p = pool[(r["candidate_id"], r["decision_time_utc"])]
            T = datetime.fromisoformat(r["decision_time_utc"])
            Topen = T - timedelta(minutes=15)
            side = r["side"]; d0 = float(p["risk_distance"]); trr = float(p["policy_target_r"] or 2.0)
            if d0 <= 0:
                continue
            base = bisect_left(m1t, (Topen - timedelta(minutes=15)).isoformat())
            endT = bisect_left(m1t, (T + timedelta(minutes=121)).isoformat())
            rec = {"candidate_id": r["candidate_id"], "decision_time_utc": r["decision_time_utc"],
                   "symbol": sym, "origin_family": r["origin_family"], "side": side,
                   "A_r": r.get("A_r"), "cost_r": p.get("cost_r"), "kstar": r.get("kstar")}
            idx = {}
            for m in MINUTES:
                t = (Topen + timedelta(minutes=m)).isoformat()
                j = bisect_left(m1t, t)
                idx[m] = j if j < len(m1t) and m1t[j] == t else None
            for m in MINUTES:
                j = idx[m]
                if j is None:
                    continue
                e = m1[j][4]
                s = e - d0 if side == "LONG" else e + d0
                tp = e + trr * d0 if side == "LONG" else e - trr * d0
                rec[f"m{m}_hend"] = walk(m1[j + 1:endT], side, e, s, tp)
                jd = bisect_left(m1t, (Topen + timedelta(minutes=m + 121)).isoformat())
                rec[f"m{m}_hdur"] = walk(m1[j + 1:jd], side, e, s, tp)
            # limit arms: rest at a price from the decision onward
            j14 = idx[14]; j0 = idx[0]
            fwd = m1[bisect_left(m1t, T.isoformat()):endT]
            bar_open = m1[base:bisect_left(m1t, T.isoformat())]
            o_price = bar_open[0][1] if bar_open else None
            c_price = m1[j14][4] if j14 is not None else None
            for name, lp in (("LOPEN", o_price),
                             ("LMID", (o_price + c_price) / 2.0 if o_price and c_price else None)):
                if lp is None:
                    continue
                fill = None
                for i, b in enumerate(fwd):
                    if b[3] <= lp <= b[2]:
                        fill = i; break
                if fill is None:
                    rec[f"{name}_r"] = 0.0; rec[f"{name}_filled"] = False
                else:
                    s = lp - d0 if side == "LONG" else lp + d0
                    tp = lp + trr * d0 if side == "LONG" else lp - trr * d0
                    rec[f"{name}_r"] = walk(fwd[fill + 1:], side, lp, s, tp)
                    rec[f"{name}_filled"] = True
                    rec[f"{name}_fill_min"] = fill
            out.append(rec)

    with gzip.open(f"{DISC}/x1_G_ANCHOR_ROWS_V1.jsonl.gz", "wt") as f:
        for rec in out:
            f.write(json.dumps(rec) + "\n")

    res = {"schema": "gtos.x1.anchor_curve.v1", "n": len(out),
           "minutes": MINUTES, "curve": {}, "curve_excl_structural": {},
           "limits": {}, "limits_excl_structural": {}, "per_family_curve": {}}
    for tag, rs in (("curve", out),
                    ("curve_excl_structural",
                     [x for x in out if x["origin_family"] != "structural_distance_extreme"])):
        days = [x["decision_time_utc"][:10] for x in rs]
        for m in MINUTES:
            for h in ("hend", "hdur"):
                v = [(x[f"m{m}_{h}"], d) for x, d in zip(rs, days) if x.get(f"m{m}_{h}") is not None]
                if v:
                    res[tag][f"m{m}_{h}"] = cl([a for a, _ in v], [b for _, b in v])
        res[tag]["A_as_ran"] = cl([x["A_r"] for x in rs if x["A_r"] is not None],
                                  [d for x, d in zip(rs, days) if x["A_r"] is not None])
    for tag, rs in (("limits", out),
                    ("limits_excl_structural",
                     [x for x in out if x["origin_family"] != "structural_distance_extreme"])):
        days = [x["decision_time_utc"][:10] for x in rs]
        for name in ("LOPEN", "LMID"):
            v = [(x[f"{name}_r"], d) for x, d in zip(rs, days) if x.get(f"{name}_r") is not None]
            if v:
                res[tag][name] = cl([a for a, _ in v], [b for _, b in v])
                res[tag][f"{name}_fill_rate_pct"] = round(
                    100 * sum(1 for x in rs if x.get(f"{name}_filled")) / len(rs), 4)
                fm = [x[f"{name}_fill_min"] for x in rs if x.get(f"{name}_filled")]
                res[tag][f"{name}_fill_minute_median"] = statistics.median(fm) if fm else None
                cst = [(x[f"{name}_r"] - x["cost_r"], d) for x, d in zip(rs, days)
                       if x.get(f"{name}_r") is not None and x.get("cost_r") is not None
                       and x.get(f"{name}_filled")]
                if cst:
                    res[tag][f"{name}_net_on_fills"] = cl([a for a, _ in cst], [b for _, b in cst])
    fam = defaultdict(list)
    for x in out:
        fam[x["origin_family"]].append(x)
    for f_, rs in fam.items():
        days = [x["decision_time_utc"][:10] for x in rs]
        res["per_family_curve"][f_] = {
            f"m{m}_hdur": cl([x[f"m{m}_hdur"] for x in rs if x.get(f"m{m}_hdur") is not None],
                             [d for x, d in zip(rs, days) if x.get(f"m{m}_hdur") is not None])
            for m in (-15, -10, -5, 0, 3, 7, 11, 14)}
        res["per_family_curve"][f_]["A_as_ran"] = cl(
            [x["A_r"] for x in rs if x["A_r"] is not None],
            [d for x, d in zip(rs, days) if x["A_r"] is not None])
    with open(f"{DISC}/x1_G_ANCHOR_CURVE_V1.json", "w") as f:
        json.dump(res, f, indent=1)
    sys.stderr.write("done %d\n" % len(out))


if __name__ == "__main__":
    main()
