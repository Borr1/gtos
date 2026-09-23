#!/usr/bin/env python3
"""l8_exclude — the CONVERSE lane item: which cells are reliably terrible, and what does
excluding them buy? Greedy forward exclusion over causally-available axes only."""
import json, os, collections
import l8_lib as L
from l8_sweepN import enrich2

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "L8_EXCLUDE_V1.json")

# axes knowable AT the decision instant (no look-ahead)
CAUSAL = ["hour", "hour_b", "dow", "symbol", "family", "side", "route_session", "session",
          "msc", "risk_pct", "born", "rdp_b", "spread_b", "cost_b", "prob_b", "ev_b",
          "fillp_b", "fill_class", "order_type", "sched", "lifecycle", "risk_rank_b",
          "ptr_b", "limit_mkt", "adm_risk_class", "sel_action", "blocker", "first_em"]
THIRDS = ["J1_d1_10", "J2_d11_20", "J3_d21_31"]
MIN_N = 100


def cellinfo(g):
    s = L.stats(g)
    th = {}
    for t in THIRDS:
        sub = [r for r in g if r["third"] == t]
        st = L.stats(sub) if sub else None
        th[t] = None if st is None else [st["n"], round(st["mean"], 4)]
    return s, th


def main():
    allrows = L.load()
    enrich2(allrows)
    rows = [r for r in allrows if r["born"] != "born_past_stop"]
    base = L.stats(rows)

    # 1. every reliably-terrible cell (n>=MIN_N, mean < base, negative in ALL three thirds)
    bad = []
    examined = 0
    for ax in CAUSAL:
        g = collections.defaultdict(list)
        for r in rows:
            g[str(r.get(ax))].append(r)
        for v, sub in g.items():
            examined += 1
            if len(sub) < MIN_N:
                continue
            s, th = cellinfo(sub)
            neg3 = all(x is not None and x[1] < 0 for x in th.values())
            rest = [r for r in rows if str(r.get(ax)) != v]
            rs = L.stats(rest)
            bad.append({"axis": ax, "value": v, "n": s["n"], "win": round(s["win"], 4),
                        "mean": round(s["mean"], 5), "t": round(s["t"], 3),
                        "neg_all_thirds": neg3, "thirds": th,
                        "pool_after_drop_mean": round(rs["mean"], 5),
                        "pool_after_drop_n": rs["n"],
                        "lift": round(rs["mean"] - base["mean"], 5),
                        "share_dropped": round(s["n"] / base["n"], 4)})
    bad.sort(key=lambda c: -c["lift"])

    # 2. greedy forward exclusion (causal axes only, drop one cell at a time)
    cur = list(rows)
    steps = []
    used = set()
    for it in range(14):
        best = None
        for ax in CAUSAL:
            g = collections.defaultdict(list)
            for r in cur:
                g[str(r.get(ax))].append(r)
            for v, sub in g.items():
                if (ax, v) in used or len(sub) < 60:
                    continue
                rest = [r for r in cur if str(r.get(ax)) != v]
                if len(rest) < 4000:
                    continue
                rs = L.stats(rest)
                if best is None or rs["mean"] > best[0]:
                    best = (rs["mean"], ax, v, len(sub), rs["n"], L.stats(sub))
        if best is None:
            break
        m, ax, v, nd, nleft, ds = best
        cur = [r for r in cur if str(r.get(ax)) != v]
        used.add((ax, v))
        thirds = {}
        for t in THIRDS:
            sub = [r for r in cur if r["third"] == t]
            st = L.stats(sub) if sub else None
            thirds[t] = None if st is None else [st["n"], round(st["mean"], 4)]
        steps.append({"step": it + 1, "drop_axis": ax, "drop_value": v, "dropped_n": nd,
                      "dropped_mean": round(ds["mean"], 5), "dropped_win": round(ds["win"], 4),
                      "kept_n": nleft, "kept_mean": round(m, 5),
                      "kept_win": round(L.stats(cur)["win"], 4),
                      "kept_t": round(L.stats(cur)["t"], 3),
                      "kept_honest": round(L.stats(cur, "honest_r")["mean"], 5),
                      "kept_thirds": thirds})
        if m <= 0 and it > 12:
            break

    res = {"base": {"n": base["n"], "mean": round(base["mean"], 5), "win": round(base["win"], 4)},
           "cells_examined": examined, "bad_cells": bad, "greedy_exclusion": steps}
    with open(OUT, "w") as fh:
        json.dump(res, fh, indent=1)
    print("base clean n=%d mean=%+.5f win=%.4f | cells examined %d" % (base["n"], base["mean"], base["win"], examined))
    print("\nTOP 18 SINGLE EXCLUSIONS BY POOL LIFT")
    print("%-14s %-26s %6s %6s %9s %7s %8s %6s %s" % ("axis", "value", "n", "win", "cellMean", "lift", "poolAft", "%drop", "neg3"))
    for c in bad[:18]:
        print("%-14s %-26s %6d %6.3f %+9.4f %+7.4f %+8.4f %5.1f%% %s" % (
            c["axis"], c["value"][:26], c["n"], c["win"], c["mean"], c["lift"],
            c["pool_after_drop_mean"], 100 * c["share_dropped"], c["neg_all_thirds"]))
    print("\nGREEDY EXCLUSION CASCADE")
    print("%2s %-14s %-26s %6s %9s %7s %9s %+7s" % ("#", "axis", "value", "dropN", "dropMean", "keptN", "keptMean", "honest"))
    for s in steps:
        print("%2d %-14s %-26s %6d %+9.4f %7d %+9.5f %+7.4f" % (
            s["step"], s["drop_axis"], s["drop_value"][:26], s["dropped_n"], s["dropped_mean"],
            s["kept_n"], s["kept_mean"], s["kept_honest"]))


if __name__ == "__main__":
    main()
