#!/usr/bin/env python3
"""l8_depth — LIMIT DEPTH (mkt_r at the decision instant, in R) vs outcome.
mkt_r > 0  : the resting limit is mkt_r stop-widths away, on the favourable side
mkt_r = 0  : the limit is AT the market (an at-market order in all but name)
mkt_r < 0  : the market has already traded through the entry (adverse)
This is knowable at the decision instant with zero look-ahead."""
import json, os, collections
import l8_lib as L
from l8_sweepN import enrich2
import l8_grid as G

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "L8_DEPTH_V1.json")
DECL = (G.TGT.index(2.0), G.STP.index(-1.0))
THIRDS = ["J1_d1_10", "J2_d11_20", "J3_d21_31"]
EDGES = [-1.0, -0.5, -0.25, -1e-9, 1e-9, 0.1, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0, 10.0, 1e18]
LABELS = ["<=-1(past stop)", "-1..-0.5", "-0.5..-0.25", "-0.25..0", "=0 (at market)",
          "0..0.10", "0.10..0.25", "0.25..0.50", "0.50..0.75", "0.75..1.0", "1.0..1.5",
          "1.5..2.0", "2.0..3.0", "3.0..5.0", "5.0..10", ">10"]


def bucket(m):
    if m is None:
        return "null"
    for e, lab in zip(EDGES, LABELS):
        if m <= e:
            return lab
    return LABELS[-1]


def agg(rows):
    n = len(rows)
    if n == 0:
        return None
    c = collections.Counter()
    vs = []
    for r in rows:
        v, o = G.resolve(r["_l"], *DECL)
        c[o] += 1
        vs.append(v)
    m = sum(vs) / n
    sd = (sum((v - m) ** 2 for v in vs) / (n - 1)) ** 0.5 if n > 1 else 0.0
    res = c["target"] + c["stop"]
    gm = sum(r["gross_r"] for r in rows) / n
    rd = [r["rdp"] for r in rows if r.get("rdp") is not None]
    return {"n": n, "mean": round(m, 5), "t": round(m / (sd / n ** 0.5), 3) if sd else 0.0,
            "res_win": round(c["target"] / res, 4) if res else None, "n_res": res,
            "target_rate": round(c["target"] / n, 4), "stop_rate": round(c["stop"] / n, 4),
            "mark_rate": round(c["mark"] / n, 4), "nofill_rate": round(c["no_fill"] / n, 4),
            "gross_mean": round(gm, 5),
            "median_rdp": round(sorted(rd)[len(rd) // 2], 5) if rd else None,
            "median_spread_r": round(sorted(x["spread_r"] for x in rows)[n // 2], 5),
            "median_cost_r": round(sorted(x["cost_r"] for x in rows)[n // 2], 5)}


def main():
    rows = L.load()
    enrich2(rows)
    lad = G.load_ladder()
    for r in rows:
        r["_l"] = lad.get((r["cid"], r["dt"]))
        r["depth"] = bucket(r["mkt_r"])
    res = {"pool": agg(rows), "depth": [], "depth_by_family": {}, "depth_by_third": {},
           "depth_by_hourb": {}, "depth_by_symbol_top": {}}
    order = {lab: i for i, lab in enumerate(LABELS)}
    g = collections.defaultdict(list)
    for r in rows:
        g[r["depth"]].append(r)
    for lab in LABELS + ["null"]:
        sub = g.get(lab, [])
        if not sub:
            continue
        a = agg(sub)
        a["depth"] = lab
        th = {}
        for t in THIRDS:
            s2 = [r for r in sub if r["third"] == t]
            aa = agg(s2) if len(s2) >= 20 else None
            th[t] = None if aa is None else [aa["n"], aa["res_win"], aa["mean"], aa["gross_mean"]]
        a["thirds"] = th
        res["depth"].append(a)
    # cross tabs
    for ax in ["family", "third", "hour_b"]:
        d = collections.defaultdict(lambda: collections.defaultdict(list))
        for r in rows:
            d[str(r.get(ax))][r["depth"]].append(r)
        tab = {}
        for k, m in d.items():
            tab[k] = {lab: agg(v) for lab, v in sorted(m.items(), key=lambda kv: order.get(kv[0], 99)) if len(v) >= 40}
        res["depth_by_%s" % ("family" if ax == "family" else "third" if ax == "third" else "hourb")] = tab
    json.dump(res, open(OUT, "w"), indent=1)
    p = res["pool"]
    print("POOL(all) n=%d resWin=%.4f honestMean=%+.5f grossMean=%+.5f" % (p["n"], p["res_win"], p["mean"], p["gross_mean"]))
    print("\n=== LIMIT DEPTH AT DECISION (mkt_r, R units) — no look-ahead ===")
    print("%-16s %6s %7s %8s %8s %8s %9s %9s %8s %8s  thirds(resWin)" % (
        "depth", "n", "resWin", "tgtRate", "stopRate", "markRate", "honestMean", "grossMean", "medRDP%", "medCostR"))
    for a in res["depth"]:
        th = a["thirds"]
        ts = " ".join(("%.3f" % v[1]) if v and v[1] is not None else "  .  " for v in
                      [th["J1_d1_10"], th["J2_d11_20"], th["J3_d21_31"]])
        print("%-16s %6d %7.4f %8.4f %8.4f %8.4f %+9.4f %+9.4f %8.4f %8.4f  %s" % (
            a["depth"], a["n"], a["res_win"] or 0, a["target_rate"], a["stop_rate"], a["mark_rate"],
            a["mean"], a["gross_mean"], a["median_rdp"] or 0, a["median_cost_r"], ts))


if __name__ == "__main__":
    main()
