#!/usr/bin/env python3
"""h5 step 1 — enumerate EVERY cell on EVERY axis and EVERY pair, and rank by edge/cost.

Contract fixed (see h5_lib docstring): at-market entry delayed 5 min, TRAIL025 exit,
broker-true cost, live-expressible cohort, 43,755 trades, Jan+Feb+Mar 2026.

Twelve axes, all ex-ante knowable at the decision instant:
    symbol family session hour side dow rdp_dec cost_dec rv_q rdp_rel_q prob_q efp_q
Singles (12) + all unordered pairs (66) = 78 groupings.  Every cell is scored; the
examined-cell census at each n floor is written out so multiplicity can be priced later.

out: h5_CELLS_V1.json (every cell with n>=20), h5_CELLS_CENSUS_V1.json
"""
import bisect
import gzip
import itertools
import json
import os
import sys
import time

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import h5_lib  # noqa: E402

SUB = os.path.join(D, "h5_SUBSTRATE_V1.jsonl.gz")
AXES = ["symbol", "family", "session", "hour", "side", "dow",
        "rdp_dec", "cost_dec", "rv_q", "rdp_rel_q", "prob_q", "efp_q"]
NFLOOR_REPORT = 20


def qcuts(vals, k):
    s = sorted(v for v in vals if v is not None)
    return [s[int(round(p * (len(s) - 1)))] for p in [i / k for i in range(1, k)]]


def load():
    rows = [json.loads(x) for x in gzip.open(SUB, "rt") if x.strip()]
    jan = [r for r in rows if r["month"] == "2026-01"]
    cuts = {}
    for name, col, k in (("rv_q", "rv_rel", 5), ("rdp_rel_q", "rdp_rel", 5),
                         ("prob_q", "prob", 5), ("efp_q", "efp", 5)):
        c = qcuts([r[col] for r in jan], k)
        cuts[name] = {"col": col, "k": k, "cuts": [round(x, 8) for x in c]}
        for r in rows:
            v = r.get(col)
            r[name] = None if v is None else bisect.bisect_left(c, v)
    # trading-day index for the interleaved split-half
    days = sorted({r["day"] for r in rows if r["month"] == "2026-01"})
    idx = {d: i for i, d in enumerate(days)}
    for r in rows:
        r["_jday"] = idx.get(r["day"])
    return rows, cuts


def groupings(rows):
    """yield (grouping_name, {cell_label: [row,...]})"""
    for a in AXES:
        g = {}
        for r in rows:
            g.setdefault(str(r.get(a)), []).append(r)
        yield a, g
    for a, b in itertools.combinations(AXES, 2):
        g = {}
        for r in rows:
            g.setdefault(f"{r.get(a)}|{r.get(b)}", []).append(r)
        yield f"{a}*{b}", g


def splits(rs):
    """January split-half (calendar and interleaved) for one cell."""
    jan = [r for r in rs if r["month"] == "2026-01"]
    out = {}
    A = [r for r in jan if r["day"] <= "2026-01-15"]
    B = [r for r in jan if r["day"] > "2026-01-15"]
    out["jan_cal_A"] = h5_lib.cell_stats(A) if len(A) >= 10 else None
    out["jan_cal_B"] = h5_lib.cell_stats(B) if len(B) >= 10 else None
    E = [r for r in jan if r["_jday"] is not None and r["_jday"] % 2 == 0]
    O = [r for r in jan if r["_jday"] is not None and r["_jday"] % 2 == 1]
    out["jan_even"] = h5_lib.cell_stats(E) if len(E) >= 10 else None
    out["jan_odd"] = h5_lib.cell_stats(O) if len(O) >= 10 else None
    return out


def main():
    t0 = time.time()
    rows, cuts = load()
    print("rows", len(rows), round(time.time() - t0, 1), flush=True)

    allcells = []
    census = {"groupings": 0, "cells_total": 0}
    floors = [20, 50, 100, 200, 500]
    for f in floors:
        census[f"cells_n_ge_{f}"] = 0
        census[f"ratio_gt_1_n_ge_{f}"] = 0
        census[f"ratio_gt_05_n_ge_{f}"] = 0
    per_grouping = {}

    for gname, g in groupings(rows):
        census["groupings"] += 1
        pg = {"cells": len(g), "cells_n_ge_50": 0, "ratio_gt_1_n_ge_50": 0}
        for label, rs in g.items():
            census["cells_total"] += 1
            st = h5_lib.cell_stats(rs)
            if st is None:
                continue
            for f in floors:
                if st["n"] >= f:
                    census[f"cells_n_ge_{f}"] += 1
                    if st["ratio_R"] is not None and st["ratio_R"] > 1.0:
                        census[f"ratio_gt_1_n_ge_{f}"] += 1
                    if st["ratio_R"] is not None and st["ratio_R"] > 0.5:
                        census[f"ratio_gt_05_n_ge_{f}"] += 1
            if st["n"] >= 50:
                pg["cells_n_ge_50"] += 1
                if st["ratio_R"] is not None and st["ratio_R"] > 1.0:
                    pg["ratio_gt_1_n_ge_50"] += 1
            if st["n"] >= NFLOOR_REPORT:
                rec = {"grouping": gname, "cell": label}
                rec.update(st)
                rec["score"] = round(h5_lib.rank_score(st), 2)
                if st["ratio_R"] is not None and st["ratio_R"] > 0.5 and st["n"] >= 50:
                    rec["splits"] = splits(rs)
                allcells.append(rec)
        per_grouping[gname] = pg
        print("  %-28s cells=%4d  n>=50=%4d  ratio>1=%3d" %
              (gname, pg["cells"], pg["cells_n_ge_50"], pg["ratio_gt_1_n_ge_50"]), flush=True)

    allcells.sort(key=lambda r: -r["score"])
    census["per_grouping"] = per_grouping
    census["quantile_cuts_frozen_on_january"] = cuts
    census["seconds"] = round(time.time() - t0, 1)
    census["book"] = h5_lib.cell_stats(rows)

    json.dump(allcells, open(os.path.join(D, "h5_CELLS_V1.json"), "w"))
    json.dump(census, open(os.path.join(D, "h5_CELLS_CENSUS_V1.json"), "w"), indent=1)
    print(json.dumps({k: v for k, v in census.items()
                      if k not in ("per_grouping", "quantile_cuts_frozen_on_january", "book")}))
    print("BOOK:", json.dumps({k: census["book"][k] for k in
                               ("n", "gross_R", "cost_R", "net_R", "ratio_R",
                                "edge_bps", "toll_bps", "ratio_bps", "t_gross", "t_net")}))


if __name__ == "__main__":
    main()
