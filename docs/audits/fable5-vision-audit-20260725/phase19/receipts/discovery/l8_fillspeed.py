#!/usr/bin/env python3
"""l8_fillspeed — is the immediate-fill penalty real, or a proxy for geometry?
Cross fill speed x limit depth, and control within risk-distance deciles."""
import json, os, collections
import l8_lib as L
from l8_sweepN import enrich2
import l8_grid as G

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "L8_FILLSPEED_V1.json")
DECL = (G.TGT.index(2.0), G.STP.index(-1.0))


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
    return {"n": n, "mean": round(m, 5), "t": round(m / (sd / n ** 0.5), 3) if sd else 0.0,
            "res_win": round(c["target"] / res, 4) if res else None,
            "target_rate": round(c["target"] / n, 4), "stop_rate": round(c["stop"] / n, 4),
            "mark_rate": round(c["mark"] / n, 4), "nofill_rate": round(c["no_fill"] / n, 4),
            "gross_mean": round(sum(r["gross_r"] for r in rows) / n, 5),
            "median_rdp": round(sorted(r["rdp"] for r in rows if r.get("rdp") is not None)[n // 2], 5)}


def main():
    rows = L.load()
    enrich2(rows)
    lad = G.load_ladder()
    for r in rows:
        r["_l"] = lad.get((r["cid"], r["dt"]))
        fb = r["_l"]["fill_bar"]
        r["fill_bar"] = fb
        r["fs"] = ("never" if fb < 0 else "bar1" if fb == 1 else "b2_5" if fb <= 5
                   else "b6_15" if fb <= 15 else "b16_60" if fb <= 60 else "b61_120")
        m = r["mkt_r"]
        r["dep2"] = ("past_stop" if (m is not None and m <= -1) else "thru" if (m is not None and m < -1e-9)
                     else "at_market" if (m is not None and m <= 1e-9) else "resting" if m is not None else "null")
    clean = [r for r in rows if r["born"] != "born_past_stop"]
    res = {"pool_clean": agg(clean), "cross": {}, "rdp_control": {}, "resting_by_fillspeed": {}}

    print("CLEAN pool: " + json.dumps({k: res["pool_clean"][k] for k in ("n", "mean", "res_win", "gross_mean")}))
    print("\n=== fill speed x limit depth (CLEAN) ===")
    print("%-10s %-10s %6s %7s %9s %9s %8s %8s %8s" % ("depth", "fillspeed", "n", "resWin", "honestMean", "grossMean", "tgtRate", "stopRate", "markRate"))
    for dep in ["at_market", "resting", "thru"]:
        for fs in ["bar1", "b2_5", "b6_15", "b16_60", "b61_120", "never"]:
            sub = [r for r in clean if r["dep2"] == dep and r["fs"] == fs]
            if len(sub) < 30:
                continue
            a = agg(sub)
            res["cross"]["%s|%s" % (dep, fs)] = a
            print("%-10s %-10s %6d %7.4f %+9.4f %+9.4f %8.4f %8.4f %8.4f" % (
                dep, fs, a["n"], a["res_win"] or 0, a["mean"], a["gross_mean"],
                a["target_rate"], a["stop_rate"], a["mark_rate"]))

    print("\n=== at_market vs resting, WITHIN risk-distance quintile (CLEAN) ===")
    vals = sorted(r["rdp"] for r in clean if r.get("rdp") is not None)
    cuts = [vals[int(len(vals) * i / 5)] for i in range(1, 5)]
    print("rdp quintile cuts (%% of price): " + ", ".join("%.4f" % c for c in cuts))
    print("%-14s %-10s %6s %7s %9s %9s" % ("rdpQuintile", "kind", "n", "resWin", "honestMean", "grossMean"))
    for q in range(5):
        lo = -1e18 if q == 0 else cuts[q - 1]
        hi = 1e18 if q == 4 else cuts[q]
        qs = [r for r in clean if r.get("rdp") is not None and lo <= r["rdp"] < hi]
        for kind in ["at_market", "resting", "thru"]:
            sub = [r for r in qs if r["dep2"] == kind]
            if len(sub) < 40:
                continue
            a = agg(sub)
            res["rdp_control"]["q%d|%s" % (q, kind)] = a
            print("%-14s %-10s %6d %7.4f %+9.4f %+9.4f" % ("Q%d" % (q + 1), kind, a["n"], a["res_win"] or 0, a["mean"], a["gross_mean"]))
    json.dump(res, open(OUT, "w"), indent=1)


if __name__ == "__main__":
    main()
