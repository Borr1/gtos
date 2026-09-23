"""x1-F — the control x1-D/E owe: is the gain the CONFIRM MINUTE, or just "earlier price"?

Placebo arms P0/P3/P7/P11: identical E3 geometry (entry = close of minute m, stop at the
ORIGINAL risk distance d0 from that entry, target at target_rr * d0) but entered at a FIXED
minute of the decision bar regardless of whether the family's predicate is true yet.

If E3 ~ P7 the timing carries nothing and the whole effect is "an earlier price is a better
price". If E3 > P7 the moment the signal turns true is itself information.

Also: day-clustered statistics and the pooled figure with structural_distance_extreme removed.
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
PLACEBO_MINUTES = (0, 3, 7, 11)


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


def cl(vals, groups):
    """mean + day-clustered SE/t over group means."""
    g = defaultdict(list)
    for v, k in zip(vals, groups):
        g[k].append(v)
    gm = [statistics.fmean(v) for v in g.values()]
    m = statistics.fmean(vals)
    if len(gm) < 2:
        return {"mean": round(m, 6), "n": len(vals), "n_days": len(gm)}
    se = statistics.stdev(gm) / math.sqrt(len(gm))
    return {"mean": round(m, 6), "n": len(vals), "n_days": len(gm),
            "mean_of_day_means": round(statistics.fmean(gm), 6),
            "day_clustered_se": round(se, 6),
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
            lo = bisect_left(m1t, Topen.isoformat()); hi = bisect_left(m1t, T.isoformat())
            win = m1[lo:hi]
            end = bisect_left(m1t, (T + timedelta(minutes=121)).isoformat())
            fwd = m1[bisect_left(m1t, T.isoformat()):end]
            rec = dict(r)
            for m in PLACEBO_MINUTES:
                if m < len(win):
                    e = win[m][4]
                    s = e - d0 if side == "LONG" else e + d0
                    t = e + trr * d0 if side == "LONG" else e - trr * d0
                    rec[f"P{m}_r"] = walk(win[m + 1:] + fwd, side, e, s, t)
            out.append(rec)

    res = {"schema": "gtos.x1.placebo.v1", "placebo_minutes": list(PLACEBO_MINUTES),
           "note": ("P arms use the E3 geometry (original risk distance preserved) entered at a "
                    "FIXED minute of the decision bar, ignoring the predicate."),
           "pooled": {}, "pooled_excl_structural": {}, "per_family": {}}
    groups = defaultdict(list)
    for x in out:
        groups[x["origin_family"]].append(x)
        groups["ALL_FIVE"].append(x)
        if x["origin_family"] != "structural_distance_extreme":
            groups["EXCL_STRUCTURAL"].append(x)
    for g, rs in groups.items():
        ok = [x for x in rs if x.get("E3_r") is not None and x.get("A_r") is not None]
        days = [x["decision_time_utc"][:10] for x in ok]
        blk = {"n": len(ok),
               "A": cl([x["A_r"] for x in ok], days),
               "E3": cl([x["E3_r"] for x in ok], days),
               "E2": cl([x["E2_r"] for x in ok if x.get("E2_r") is not None],
                        [d for x, d in zip(ok, days) if x.get("E2_r") is not None]),
               "delta_E3_minus_A": cl([x["E3_r"] - x["A_r"] for x in ok], days),
               "delta_E2_minus_A": cl([x["E2_r"] - x["A_r"] for x in ok if x.get("E2_r") is not None],
                                      [d for x, d in zip(ok, days) if x.get("E2_r") is not None]),
               "kstar_median": statistics.median([x["kstar"] for x in ok if x.get("kstar") is not None]),
               }
        for m in PLACEBO_MINUTES:
            v = [(x[f"P{m}_r"], d) for x, d in zip(ok, days) if x.get(f"P{m}_r") is not None]
            if v:
                blk[f"P{m}"] = cl([a for a, _ in v], [b for _, b in v])
                pairs = [(x[f"P{m}_r"], x["E3_r"], d) for x, d in zip(ok, days)
                         if x.get(f"P{m}_r") is not None]
                blk[f"delta_E3_minus_P{m}"] = cl([b - a for a, b, _ in pairs],
                                                 [c for _, _, c in pairs])
        key = ("pooled" if g == "ALL_FIVE" else
               "pooled_excl_structural" if g == "EXCL_STRUCTURAL" else None)
        if key:
            res[key] = blk
        else:
            res["per_family"][g] = blk
    with open(f"{DISC}/x1_F_PLACEBO_V1.json", "w") as f:
        json.dump(res, f, indent=1)
    sys.stderr.write("done\n")


if __name__ == "__main__":
    main()
