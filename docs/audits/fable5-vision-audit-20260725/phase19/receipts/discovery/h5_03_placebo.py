#!/usr/bin/env python3
"""h5 step 3 — the PLACEBO: how many ratio>1 cells does this grid find when there is no
cell structure at all?

The census says 4,130 cells at n>=50 were examined and 243 clear ratio_R > 1.  That count
is meaningless without a null, because a cell's ratio is (mean gross)/(mean cost) and both
sides are noisy.  So: destroy the cell structure, keep everything else, re-run the IDENTICAL
78-grouping enumeration, and count.

Three nulls, increasingly tight:

  P1  permute gross_r within (symbol, month).  Destroys every within-symbol association --
      including the MECHANICAL one (both gross and cost scale as 1/risk_distance), so P1
      over-states the null count on the cost/stop-width axes.  Loose.
  P2  permute gross_r within (symbol, month, within-symbol cost quintile).  Preserves the
      mechanical gross<->cost coupling; destroys hour / family / side / vol / prob / efp
      structure.  This is the honest null for the SUB-SYMBOL axes.
  P3  permute gross_r within (month, global cost decile).  Destroys the symbol axis too,
      so it prices instrument selection (GER40) as well.

Per replicate it reports: cells n>=50 with ratio_R>1, with ratio_R>0.5, and the count
surviving all seven sub-samples (Jan, Feb, Mar, Jan calendar halves, Jan parity halves) --
the same seven the real run used.

usage: python3 h5_03_placebo.py [n_replicates]
out: h5_PLACEBO_V1.json
"""
import bisect
import gzip
import itertools
import json
import os
import random
import sys
import time

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import h5_lib  # noqa: E402
import h5_01_cells as C  # noqa: E402

NREP = int(sys.argv[1]) if len(sys.argv) > 1 else 30
GROSS = h5_lib.GROSS


def blocks(rows, kind):
    b = {}
    if kind == "P1":
        for r in rows:
            b.setdefault((r["symbol"], r["month"]), []).append(r)
    elif kind == "P2":
        tmp = {}
        for r in rows:
            tmp.setdefault((r["symbol"], r["month"]), []).append(r)
        for k, rs in tmp.items():
            cs = sorted(r["cost_true"] for r in rs)
            cuts = [cs[int(round(p * (len(cs) - 1)))] for p in (0.2, 0.4, 0.6, 0.8)]
            for r in rs:
                b.setdefault(k + (bisect.bisect_left(cuts, r["cost_true"]),), []).append(r)
    elif kind == "P3":
        for r in rows:
            b.setdefault((r["month"], r["cost_dec"]), []).append(r)
    return b


def stats_only(rows):
    """counts for one (permuted) dataset — identical grid to h5_01_cells."""
    n1 = n05 = nex = 0
    surv = 0
    for gname, g in C.groupings(rows):
        for label, rs in g.items():
            if len(rs) < 50:
                continue
            nex += 1
            st = h5_lib.cell_stats(rs)
            if st["ratio_R"] is None:
                continue
            if st["ratio_R"] > 0.5:
                n05 += 1
            if st["ratio_R"] > 1.0:
                n1 += 1
                sp = C.splits(rs)
                ok = all(st["m_" + m] and st["m_" + m]["ratio_R"] and st["m_" + m]["ratio_R"] > 1
                         for m in ("2026-01", "2026-02", "2026-03"))
                for k in ("jan_cal_A", "jan_cal_B", "jan_even", "jan_odd"):
                    v = sp.get(k)
                    ok = ok and v is not None and v.get("ratio_R") is not None and v["ratio_R"] > 1
                if ok:
                    surv += 1
    return {"cells_n_ge_50": nex, "ratio_gt_1": n1, "ratio_gt_05": n05, "survive_all_7": surv}


def main():
    t0 = time.time()
    rows, _cuts = C.load()
    real = stats_only(rows)
    OUT = {"real": real, "n_replicates": NREP, "nulls": {}}
    print("REAL:", json.dumps(real), flush=True)
    base = [r[GROSS] for r in rows]
    for kind in ("P1", "P2", "P3"):
        b = blocks(rows, kind)
        reps = []
        rnd = random.Random(20260806)
        for rep in range(NREP):
            for k, rs in b.items():
                v = [r[GROSS] for r in rs]
                rnd.shuffle(v)
                for r, x in zip(rs, v):
                    r[GROSS] = x
            reps.append(stats_only(rows))
            print("  %s rep %2d %s  %.1fs" % (kind, rep, json.dumps(reps[-1]),
                                              time.time() - t0), flush=True)
        for r, x in zip(rows, base):
            r[GROSS] = x
        agg = {}
        for k in ("ratio_gt_1", "ratio_gt_05", "survive_all_7"):
            v = sorted(x[k] for x in reps)
            agg[k] = {"mean": round(sum(v) / len(v), 2), "min": v[0], "max": v[-1],
                      "p50": v[len(v) // 2], "p95": v[int(0.95 * (len(v) - 1))],
                      "n_ge_real": sum(1 for x in v if x >= real[k]),
                      "emp_p": round((1 + sum(1 for x in v if x >= real[k])) / (len(v) + 1), 4)}
        OUT["nulls"][kind] = {"blocks": len(b), "per_rep": reps, "summary": agg}
        print(kind, json.dumps(agg), flush=True)
    OUT["seconds"] = round(time.time() - t0, 1)
    json.dump(OUT, open(os.path.join(D, "h5_PLACEBO_V1.json"), "w"), indent=1)
    print("DONE", OUT["seconds"])


if __name__ == "__main__":
    main()
