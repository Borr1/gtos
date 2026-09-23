"""x1-E — validate the x1-D walker against the shipped pool, and add the arm that
survives cost: enter early, keep the RISK DISTANCE the generator would have used.

E3: entry = close of minute k*, stop = entry -/+ d0 (the original risk distance),
    target = entry +/- target_rr * d0.  Risk container identical to the as-ran trade,
    so the pool's own cost_r applies UNCHANGED and the comparison is net-honest.

Validation: ARM A must reproduce the shipped `plain_walk_r`.
"""
from __future__ import annotations

import csv
import gzip
import json
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
        return None, "no_risk"
    for b in bars:
        _, o, h, l, c = b
        if side == "LONG":
            hs, ht = l <= stop, h >= tp
        else:
            hs, ht = h >= stop, l <= tp
        if hs:
            return -1.0, "stop"
        if ht:
            return abs(tp - entry) / d, "target"
    c = bars[-1][4]
    return ((c - entry) / d if side == "LONG" else (entry - c) / d), "path_end"


def summ(v):
    v = [x for x in v if x is not None]
    if not v:
        return None
    return {"n": len(v), "mean": round(statistics.fmean(v), 6), "sum": round(sum(v), 4),
            "median": round(statistics.median(v), 6),
            "stdev": round(statistics.pstdev(v), 6) if len(v) > 1 else 0.0}


def main():
    pool = {}
    with gzip.open(f"{DISC}/w0_WORKING_SET.jsonl.gz", "rt") as f:
        for line in f:
            r = json.loads(line)
            pool[(r["candidate_id"], r["decision_time_utc"])] = r
    ew = []
    with gzip.open(f"{DISC}/x1_D_EARLYWALK_ROWS_V1.jsonl.gz", "rt") as f:
        for line in f:
            ew.append(json.loads(line))
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
            rec = dict(r)
            k = r.get("kstar")
            if k is not None and r.get("side_k") == side and r.get("entry_k") is not None:
                lo = bisect_left(m1t, Topen.isoformat()); hi = bisect_left(m1t, T.isoformat())
                win = m1[lo:hi]
                end = bisect_left(m1t, (T + timedelta(minutes=121)).isoformat())
                tail = win[k + 1:] + m1[bisect_left(m1t, T.isoformat()):end]
                e = float(r["entry_k"])
                s3 = e - d0 if side == "LONG" else e + d0
                t3 = e + trr * d0 if side == "LONG" else e - trr * d0
                r3, rn3 = walk(tail, side, e, s3, t3)
                rec["E3_r"], rec["E3_reason"] = r3, rn3
            rec["plain_walk_r"] = p.get("plain_walk_r")
            rec["cost_r"] = p.get("cost_r")
            out.append(rec)

    with gzip.open(f"{DISC}/x1_E_E3_ROWS_V1.jsonl.gz", "wt") as f:
        for rec in out:
            f.write(json.dumps(rec) + "\n")

    # ---- validation of ARM A against the shipped plain_walk_r
    pairs = [(x["A_r"], x["plain_walk_r"]) for x in out
             if x.get("A_r") is not None and x.get("plain_walk_r") is not None]
    diffs = [abs(a - b) for a, b in pairs]
    val = {"n": len(pairs),
           "mean_A_r": round(statistics.fmean([a for a, _ in pairs]), 6),
           "mean_plain_walk_r": round(statistics.fmean([b for _, b in pairs]), 6),
           "mean_abs_diff": round(statistics.fmean(diffs), 6),
           "max_abs_diff": round(max(diffs), 6),
           "pct_within_0p01": round(100 * sum(1 for d in diffs if d <= 0.01) / len(diffs), 4),
           "pct_exact_sign_match": round(
               100 * sum(1 for a, b in pairs if (a >= 0) == (b >= 0)) / len(pairs), 4)}

    res = {"schema": "gtos.x1.e3.v1", "validation_A_vs_shipped_plain_walk": val,
           "per_family": {}, "pooled": {}}
    groups = defaultdict(list)
    for x in out:
        groups[x["origin_family"]].append(x); groups["ALL_FIVE"].append(x)
    for g, rs in groups.items():
        ok = [x for x in rs if x.get("E3_r") is not None and x.get("A_r") is not None]
        cs = [x for x in ok if x.get("cost_r") is not None]
        blk = {
            "n_paired": len(ok),
            "A_r": summ([x["A_r"] for x in ok]),
            "E1_r_in_orig_risk": summ([x.get("E1_r_in_orig_risk") for x in ok]),
            "E2_r": summ([x.get("E2_r") for x in ok]),
            "E3_r": summ([x["E3_r"] for x in ok]),
            "delta_E1orig_minus_A": summ([x["E1_r_in_orig_risk"] - x["A_r"] for x in ok
                                          if x.get("E1_r_in_orig_risk") is not None]),
            "delta_E2_minus_A": summ([x["E2_r"] - x["A_r"] for x in ok if x.get("E2_r") is not None]),
            "delta_E3_minus_A": summ([x["E3_r"] - x["A_r"] for x in ok]),
            "net_A": summ([x["A_r"] - x["cost_r"] for x in cs]),
            "net_E3": summ([x["E3_r"] - x["cost_r"] for x in cs]),
            "net_delta_E3_minus_A": summ([x["E3_r"] - x["A_r"] for x in cs]),
            "exit_reason_E3": {k: sum(1 for x in ok if x["E3_reason"] == k)
                               for k in sorted({y["E3_reason"] for y in ok})},
            "win_rate_A": round(100 * sum(1 for x in ok if x["A_r"] > 0) / len(ok), 4) if ok else None,
            "win_rate_E3": round(100 * sum(1 for x in ok if x["E3_r"] > 0) / len(ok), 4) if ok else None,
        }
        (res["pooled"] if g == "ALL_FIVE" else res["per_family"].setdefault(g, {})).update(blk)
    # per-day sign robustness on the pooled delta
    byday = defaultdict(list)
    for x in out:
        if x.get("E3_r") is not None and x.get("A_r") is not None:
            byday[x["decision_time_utc"][:10]].append(x["E3_r"] - x["A_r"])
    dm = {d: statistics.fmean(v) for d, v in byday.items()}
    res["pooled"]["daily_delta_E3_minus_A"] = {
        "n_days": len(dm), "n_days_positive": sum(1 for v in dm.values() if v > 0),
        "mean_of_daily_means": round(statistics.fmean(dm.values()), 6),
        "min_day": round(min(dm.values()), 6), "max_day": round(max(dm.values()), 6)}
    bysym = defaultdict(list)
    for x in out:
        if x.get("E3_r") is not None and x.get("A_r") is not None:
            bysym[x["symbol"]].append(x["E3_r"] - x["A_r"])
    res["pooled"]["symbol_delta_E3_minus_A"] = {
        s: {"n": len(v), "mean": round(statistics.fmean(v), 6)} for s, v in sorted(bysym.items())}
    with open(f"{DISC}/x1_E_E3_V1.json", "w") as f:
        json.dump(res, f, indent=1)
    sys.stderr.write(json.dumps(val) + "\n")


if __name__ == "__main__":
    main()
