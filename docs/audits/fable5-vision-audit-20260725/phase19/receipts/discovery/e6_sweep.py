#!/usr/bin/env python3
"""e6_sweep — the entry-delay instrument evaluated on every built month, plus the boundary search.

Reads e6_FRAME_<MONTH>.jsonl.gz. Writes E6_SWEEP_V1.json.
Everything is priced per candidate-OPPORTUNITY: a refused or never-filled candidate books 0.0 R,
so the skipped rows are charged honestly and k=0 vs k=1 is a like-for-like comparison.
"""
import collections, gzip, json, math, os, sys

D = os.path.dirname(os.path.abspath(__file__))
MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY"]
OUT = os.path.join(D, "E6_SWEEP_V1.json")


def load(month):
    p = os.path.join(D, "e6_FRAME_%s.jsonl.gz" % month)
    if not os.path.isfile(p):
        return None
    with gzip.open(p, "rt") as fh:
        return [json.loads(l) for l in fh if l.strip()]


def sweep(rows, k):
    n = len(rows)
    if n == 0:
        return None
    vs = []
    c = collections.Counter()
    for r in rows:
        if r["fb"] < 0:
            vs.append(0.0); c["no_fill"] += 1
        elif r["fb"] <= k:
            vs.append(0.0); c["refused"] += 1
        else:
            vs.append(r["hr"]); c[r["oc"]] += 1
    traded = c["target"] + c["stop"] + c["mark"]
    res = c["target"] + c["stop"]
    m = sum(vs) / n
    sd = (sum((v - m) ** 2 for v in vs) / (n - 1)) ** 0.5 if n > 1 else 0.0
    ts = sum(v for v in vs if v != 0.0)
    return {"k": k, "n_opp": n, "n_traded": traded, "traded_share": round(traded / n, 4),
            "R_per_opportunity": round(m, 5),
            "R_per_trade": round(ts / traded, 5) if traded else None,
            "sd": round(sd, 5),
            "t": round(m / (sd / n ** 0.5), 3) if sd else 0.0,
            "res_win": round(c["target"] / res, 4) if res else None,
            "target": c["target"], "stop": c["stop"], "mark": c["mark"],
            "refused": c["refused"], "no_fill": c["no_fill"],
            "total_R": round(sum(vs), 2)}


def delta_k(rows, k=1):
    """PAIRED per-candidate delta of the k-rule vs k=0, with its own t-stat.
    d_i = R_i(rule) - R_i(as-shipped); non-zero only on refused candidates."""
    ds = []
    for r in rows:
        if r["fb"] < 0:
            ds.append(0.0)
        elif r["fb"] <= k:
            ds.append(0.0 - r["hr"])
        else:
            ds.append(0.0)
    n = len(ds)
    if n < 2:
        return None
    m = sum(ds) / n
    sd = (sum((v - m) ** 2 for v in ds) / (n - 1)) ** 0.5
    return {"n": n, "delta_R_per_opportunity": round(m, 5),
            "t": round(m / (sd / n ** 0.5), 3) if sd else 0.0,
            "n_refused": sum(1 for r in rows if 0 < r["fb"] <= k)}


def cohorts(rows):
    out = {}
    for lab, lo, hi in [("bar1", 1, 1), ("bar2_5", 2, 5), ("bar6_15", 6, 15),
                        ("bar16_60", 16, 60), ("bar61_120", 61, 120), ("never", -1, -1)]:
        sub = [r for r in rows if (r["fb"] == -1 if lo == -1 else lo <= r["fb"] <= hi)]
        n = len(sub)
        if n == 0:
            out[lab] = None
            continue
        hm = sum(r["hr"] for r in sub) / n
        gv = [r["gross_r"] for r in sub if r["gross_r"] is not None]
        c = collections.Counter(r["oc"] for r in sub)
        res = c["target"] + c["stop"]
        out[lab] = {"n": n, "share": round(n / len(rows), 4),
                    "honest_mean": round(hm, 5),
                    "gross_mean": round(sum(gv) / len(gv), 5) if gv else None,
                    "res_win": round(c["target"] / res, 4) if res else None,
                    "target_rate": round(c["target"] / n, 4),
                    "stop_rate": round(c["stop"] / n, 4),
                    "mark_rate": round(c["mark"] / n, 4)}
    return out


def bucket_spread(v):
    if v is None: return "null"
    for e, lab in zip([0.05, 0.10, 0.20, 0.40, 1.0],
                      ["<=0.05", "0.05-0.10", "0.10-0.20", "0.20-0.40", "0.40-1.0"]):
        if v <= e: return lab
    return ">1.0"


def by_axis(rows, axis_fn, minn=100, k=1):
    g = collections.defaultdict(list)
    for r in rows:
        g[str(axis_fn(r))].append(r)
    tab = {}
    for v, sub in g.items():
        if len(sub) < minn:
            continue
        s0, s1 = sweep(sub, 0), sweep(sub, k)
        d = delta_k(sub, k)
        tab[v] = {"n": len(sub), "k0": s0["R_per_opportunity"], "k1": s1["R_per_opportunity"],
                  "delta": round(s1["R_per_opportunity"] - s0["R_per_opportunity"], 5),
                  "paired_t": d["t"], "bar1_share": round(
                      sum(1 for r in sub if r["fb"] == 1) / len(sub), 4),
                  "bar1_mean": round(
                      sum(r["hr"] for r in sub if r["fb"] == 1) /
                      max(1, sum(1 for r in sub if r["fb"] == 1)), 5),
                  "later_mean": round(
                      sum(r["hr"] for r in sub if r["fb"] > 1) /
                      max(1, sum(1 for r in sub if r["fb"] > 1)), 5),
                  "k0_res_win": s0["res_win"], "k1_res_win": s1["res_win"]}
    return dict(sorted(tab.items(), key=lambda kv: -kv[1]["delta"]))


AXES = {
    "family": lambda r: r["fam"],
    "symbol": lambda r: r["sym"],
    "session": lambda r: r["sess"],
    "route_session": lambda r: r["rsess"],
    "hour": lambda r: "%02d" % r["hour"],
    "born": lambda r: r["born"],
    "side": lambda r: r["side"],
    "dtf": lambda r: r["dtf"],
    "spread_b": lambda r: bucket_spread(r.get("spread_r")),
    "dow": lambda r: r["dow"],
    "order_type": lambda r: r["otype"],
    "blocker": lambda r: r["blocker"],
}


def main():
    res = {"months": {}, "boundary": {}, "pooled": {}}
    allrows = []
    for m in MONTHS:
        rows = load(m)
        if rows is None:
            print("MISSING frame", m)
            continue
        for r in rows:
            r["month"] = m
        allrows.extend(rows)
        clean = [r for r in rows if r["born"] != "born_past_stop"]
        blk = {"n_all": len(rows), "n_clean": len(clean),
               "born_census": dict(collections.Counter(r["born"] for r in rows)),
               "cohorts_clean": cohorts(clean), "cohorts_all": cohorts(rows),
               "sweep_clean": [sweep(clean, k) for k in [0, 1, 2, 3, 5, 10, 20, 60]],
               "sweep_all": [sweep(rows, k) for k in [0, 1, 2, 5, 15]],
               "paired_delta_clean_k1": delta_k(clean, 1),
               "paired_delta_all_k1": delta_k(rows, 1),
               "gross_mean_all": round(sum(r["gross_r"] for r in rows if r["gross_r"] is not None) /
                                       max(1, sum(1 for r in rows if r["gross_r"] is not None)), 5)}
        res["months"][m] = blk
        print("%-4s n=%6d clean=%6d bar1share=%.4f | CLEAN k0 %+0.5f -> k1 %+0.5f (d %+0.5f, t %+.2f) | ALL k0 %+0.5f -> k1 %+0.5f (d %+0.5f, t %+.2f)" % (
            m, len(rows), len(clean),
            blk["cohorts_clean"]["bar1"]["share"] if blk["cohorts_clean"]["bar1"] else 0,
            blk["sweep_clean"][0]["R_per_opportunity"], blk["sweep_clean"][1]["R_per_opportunity"],
            blk["paired_delta_clean_k1"]["delta_R_per_opportunity"], blk["paired_delta_clean_k1"]["t"],
            blk["sweep_all"][0]["R_per_opportunity"], blk["sweep_all"][1]["R_per_opportunity"],
            blk["paired_delta_all_k1"]["delta_R_per_opportunity"], blk["paired_delta_all_k1"]["t"]))

    # pooled non-January (true out-of-sample for the find)
    for label, sel in [("ALL5", lambda r: True),
                       ("OOS_FEB_MAR_APR_MAY", lambda r: r["month"] != "JAN"),
                       ("UNREAD_APR_MAY", lambda r: r["month"] in ("APR", "MAY"))]:
        sub = [r for r in allrows if sel(r)]
        if not sub:
            continue
        cl = [r for r in sub if r["born"] != "born_past_stop"]
        res["pooled"][label] = {
            "n_all": len(sub), "n_clean": len(cl),
            "sweep_clean": [sweep(cl, k) for k in [0, 1, 2, 5, 20]],
            "sweep_all": [sweep(sub, k) for k in [0, 1, 5]],
            "paired_delta_clean_k1": delta_k(cl, 1),
            "paired_delta_all_k1": delta_k(sub, 1),
            "cohorts_clean": cohorts(cl)}
        print("POOL %-20s n=%6d clean=%6d CLEAN k0 %+0.5f -> k1 %+0.5f  t=%+.2f" % (
            label, len(sub), len(cl), res["pooled"][label]["sweep_clean"][0]["R_per_opportunity"],
            res["pooled"][label]["sweep_clean"][1]["R_per_opportunity"],
            res["pooled"][label]["paired_delta_clean_k1"]["t"]))

    # boundary search on the pooled clean population, per month and pooled
    cl_all = [r for r in allrows if r["born"] != "born_past_stop"]
    for ax, fn in AXES.items():
        res["boundary"][ax] = {"POOLED": by_axis(cl_all, fn)}
        for m in MONTHS:
            sub = [r for r in cl_all if r["month"] == m]
            if sub:
                res["boundary"][ax][m] = by_axis(sub, fn)

    json.dump(res, open(OUT, "w"), indent=1)
    print("->", OUT)


if __name__ == "__main__":
    main()
