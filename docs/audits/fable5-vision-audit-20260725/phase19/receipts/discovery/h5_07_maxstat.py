#!/usr/bin/env python3
"""h5 step 7 — WESTFALL-YOUNG: pay the whole multiplicity bill for the whole grid, once.

Step 3 showed the COUNT of ratio>1 cells is not evidence: a null that keeps every symbol's
own gross distribution and the mechanical gross<->cost coupling, and destroys only the cell
structure, produces about as many ratio>1 cells and about as many seven-sub-sample
survivors as the real data does.  So the count criterion has a false-discovery rate near 1.

The statistic that CAN survive the whole grid is the MAXIMUM.  For each null replicate
record the largest day-clustered t on net R over all 4,130 cells at n>=50, and the largest
(ratio-1)*n.  A real cell whose statistic exceeds the null MAXIMUM in (say) 39 of 40
replicates is significant AFTER correcting for every one of the 4,130 looks -- that is the
Westfall-Young step-down maxT, single-step form.

Toll: HOUR-AWARE (`cost_true_hour`), the honest one (step 6).

Nulls: P2 (permute gross within symbol x month x within-symbol cost quintile -- prices the
sub-symbol axes, keeps the mechanical coupling) and P3 (permute within month x global cost
decile -- prices instrument selection too).

usage: python3 h5_07_maxstat.py [n_replicates]
out: h5_MAXSTAT_V1.json
"""
import bisect
import gzip
import json
import os
import random
import sys
import time

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import h5_lib  # noqa: E402
import h5_01_cells as C  # noqa: E402

NREP = int(sys.argv[1]) if len(sys.argv) > 1 else 40
h5_lib.COST = "cost_true_hour"
GROSS = h5_lib.GROSS


def load_v2():
    rows = [json.loads(x) for x in gzip.open(os.path.join(D, "h5_SUBSTRATE_V2.jsonl.gz"), "rt")
            if x.strip()]
    jan = [r for r in rows if r["month"] == "2026-01"]
    for name, col, k in (("rv_q", "rv_rel", 5), ("rdp_rel_q", "rdp_rel", 5),
                         ("prob_q", "prob", 5), ("efp_q", "efp", 5)):
        v = sorted(x[col] for x in jan if x.get(col) is not None)
        cc = [v[int(round(p * (len(v) - 1)))] for p in [i / k for i in range(1, k)]]
        for r in rows:
            x = r.get(col)
            r[name] = None if x is None else bisect.bisect_left(cc, x)
    days = sorted({r["day"] for r in rows if r["month"] == "2026-01"})
    idx = {d: i for i, d in enumerate(days)}
    for r in rows:
        r["_jday"] = idx.get(r["day"])
    # hour-aware cost decile, frozen on January, so cost_dec matches the toll in use
    cs = sorted(r["cost_true_hour"] for r in jan if r["cost_true_hour"] is not None)
    cuts = [cs[int(round(p * (len(cs) - 1)))] for p in [i / 10 for i in range(1, 10)]]
    for r in rows:
        r["cost_dec"] = (None if r["cost_true_hour"] is None
                         else bisect.bisect_left(cuts, r["cost_true_hour"]))
    return rows


def scan(rows, keep_cells=False):
    """max statistics over the identical 78-grouping / n>=50 grid."""
    maxt = -1e18
    maxscore = -1e18
    n1 = n05 = nex = surv = 0
    cells = []
    for gname, g in C.groupings(rows):
        for label, rs in g.items():
            if len(rs) < 50:
                continue
            nex += 1
            st = h5_lib.cell_stats(rs)
            if st["ratio_R"] is None:
                continue
            t = st["t_net_day"]
            if t is not None and t > maxt:
                maxt = t
            if st["ratio_R"] > 0.5:
                n05 += 1
            if st["ratio_R"] > 1.0:
                n1 += 1
                sc = (st["ratio_R"] - 1.0) * st["n"]
                if sc > maxscore:
                    maxscore = sc
                sp = C.splits(rs)
                ok = all(st["m_" + m] and st["m_" + m]["ratio_R"] and st["m_" + m]["ratio_R"] > 1
                         for m in ("2026-01", "2026-02", "2026-03"))
                for kk in ("jan_cal_A", "jan_cal_B", "jan_even", "jan_odd"):
                    v = sp.get(kk)
                    ok = ok and v is not None and v.get("ratio_R") is not None and v["ratio_R"] > 1
                if ok:
                    surv += 1
                if keep_cells:
                    rec = {"grouping": gname, "cell": label, "survive_all_7": ok,
                           "score": round(sc, 2)}
                    rec.update(st)
                    cells.append(rec)
    out = {"cells_n_ge_50": nex, "ratio_gt_1": n1, "ratio_gt_05": n05,
           "survive_all_7": surv, "max_t_net_day": round(maxt, 4),
           "max_score": round(maxscore, 2)}
    return (out, cells) if keep_cells else out


def blocks(rows, kind):
    b = {}
    if kind == "P2":
        tmp = {}
        for r in rows:
            tmp.setdefault((r["symbol"], r["month"]), []).append(r)
        for k, rs in tmp.items():
            cs = sorted(r["cost_true_hour"] for r in rs)
            cuts = [cs[int(round(p * (len(cs) - 1)))] for p in (0.2, 0.4, 0.6, 0.8)]
            for r in rs:
                b.setdefault(k + (bisect.bisect_left(cuts, r["cost_true_hour"]),), []).append(r)
    else:
        for r in rows:
            b.setdefault((r["month"], r["cost_dec"]), []).append(r)
    return b


def main():
    t0 = time.time()
    rows = load_v2()
    real, cells = scan(rows, keep_cells=True)
    cells.sort(key=lambda r: -(r["t_net_day"] if r["t_net_day"] is not None else -1e18))
    OUT = {"toll": "cost_true_hour", "n_replicates": NREP, "real": real,
           "real_top_cells_by_t_net_day": cells[:60]}
    print("REAL:", json.dumps(real), flush=True)
    base = [r[GROSS] for r in rows]
    for kind in ("P2", "P3"):
        b = blocks(rows, kind)
        reps = []
        rnd = random.Random(20260806)
        for rep in range(NREP):
            for k, rs in b.items():
                v = [r[GROSS] for r in rs]
                rnd.shuffle(v)
                for r, x in zip(rs, v):
                    r[GROSS] = x
            reps.append(scan(rows))
            print("  %s rep %2d %s %.0fs" % (kind, rep, json.dumps(reps[-1]), time.time() - t0), flush=True)
        for r, x in zip(rows, base):
            r[GROSS] = x
        mt = sorted(x["max_t_net_day"] for x in reps)
        ms = sorted(x["max_score"] for x in reps)
        summ = {"blocks": len(b),
                "max_t_null": {"mean": round(sum(mt) / len(mt), 3), "p50": mt[len(mt) // 2],
                               "p95": mt[int(0.95 * (len(mt) - 1))], "max": mt[-1], "min": mt[0]},
                "max_score_null": {"mean": round(sum(ms) / len(ms), 1), "p50": ms[len(ms) // 2],
                                   "p95": ms[int(0.95 * (len(ms) - 1))], "max": ms[-1]}}
        for k in ("ratio_gt_1", "survive_all_7"):
            v = sorted(x[k] for x in reps)
            summ[k] = {"mean": round(sum(v) / len(v), 2), "p50": v[len(v) // 2],
                       "p95": v[int(0.95 * (len(v) - 1))], "max": v[-1],
                       "emp_p_real": round((1 + sum(1 for x in v if x >= real[k])) / (len(v) + 1), 4)}
        # Westfall-Young adjusted p for every real cell
        wy = []
        for c in cells:
            t = c["t_net_day"]
            if t is None:
                continue
            wy.append({"grouping": c["grouping"], "cell": c["cell"], "n": c["n"],
                       "ratio_R": c["ratio_R"], "net_R": c["net_R"], "t_net_day": t,
                       "wy_p": round((1 + sum(1 for x in mt if x >= t)) / (len(mt) + 1), 4)})
        wy.sort(key=lambda r: (r["wy_p"], -r["t_net_day"]))
        summ["westfall_young_top"] = wy[:40]
        summ["n_cells_wy_p_le_005"] = sum(1 for r in wy if r["wy_p"] <= 0.05)
        summ["n_cells_wy_p_le_010"] = sum(1 for r in wy if r["wy_p"] <= 0.10)
        summ["n_cells_wy_p_le_020"] = sum(1 for r in wy if r["wy_p"] <= 0.20)
        summ["per_rep"] = reps
        OUT[kind] = summ
        print(kind, json.dumps({k: v for k, v in summ.items()
                                if k not in ("per_rep", "westfall_young_top")}), flush=True)
    OUT["seconds"] = round(time.time() - t0, 1)
    json.dump(OUT, open(os.path.join(D, "h5_MAXSTAT_V1.json"), "w"), indent=1)
    print("DONE", OUT["seconds"])


if __name__ == "__main__":
    main()
