#!/usr/bin/env python3
"""l8_gatevalue — do the live gates SELECT or SUPPRESS? Measured on the delayed-fill
clean population (the only cohort that is not adversely selected), honest 2R/-1R.

Gate limbs measured exactly as shipped:
  spread_r > 0.10  (broker_net_cost_engine.py:859-866, agent_config.yaml:715)
  total cost_r > 0.15 (:923-927, :716)
and at the measured 7.3x / 8.5x spread overcharge correction."""
import json, os, collections
import l8_lib as L
from l8_sweepN import enrich2
import l8_grid as G

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "L8_GATEVALUE_V1.json")
TI, SI = G.TGT.index(2.0), G.STP.index(-1.0)


def res1(l):
    fb = l["fill_bar"]
    if fb < 0:
        return 0.0, "no_fill"
    bt, bs = l["tfav"][TI], l["tadv"][SI]
    if bs > 0 and (bt <= 0 or bs <= bt):
        return G.STP[SI], "stop"
    if bt > 0:
        return G.TGT[TI], "target"
    return l["r_end"], "mark"


def agg(rows):
    n = len(rows)
    if n == 0:
        return None
    c = collections.Counter()
    vs = []
    for r in rows:
        v, o = res1(r["_l"])
        c[o] += 1
        vs.append(v)
    m = sum(vs) / n
    sd = (sum((v - m) ** 2 for v in vs) / (n - 1)) ** 0.5 if n > 1 else 0.0
    res = c["target"] + c["stop"]
    return {"n": n, "mean": round(m, 5), "t": round(m / (sd / n ** 0.5), 3) if sd else 0.0,
            "res_win": round(c["target"] / res, 4) if res else None,
            "gross_mean": round(sum(r["gross_r"] for r in rows) / n, 5), "total_R": round(sum(vs), 2)}


def main():
    rows = L.load()
    enrich2(rows)
    lad = G.load_ladder()
    for r in rows:
        r["_l"] = lad.get((r["cid"], r["dt"]))
    clean = [r for r in rows if r["born"] != "born_past_stop"]
    delayed = [r for r in clean if r["_l"]["fill_bar"] >= 2]
    res = {"populations": {}, "gate_limbs": {}, "overcharge": {}}
    pops = {"pool_all": rows, "clean": clean, "delayed_clean": delayed,
            "bar1_clean": [r for r in clean if r["_l"]["fill_bar"] == 1]}
    for k, v in pops.items():
        res["populations"][k] = agg(v)
    print("populations: " + " | ".join("%s n=%d mean=%+.4f" % (k, a["n"], a["mean"]) for k, a in res["populations"].items()))

    print("\n=== DO THE SHIPPED GATES SELECT OR SUPPRESS? (delayed-fill clean pop, honest 2R/-1R) ===")
    print("%-40s %6s %9s %8s %8s %9s" % ("split", "n", "mean", "resWin", "t", "totalR"))
    tests = [
        ("spread_r <= 0.10  (PASSES shipped spread cap)", lambda r: r["spread_r"] <= 0.10),
        ("spread_r >  0.10  (REFUSED by spread cap)", lambda r: r["spread_r"] > 0.10),
        ("cost_r   <= 0.15  (PASSES shipped total cap)", lambda r: r["cost_r"] <= 0.15),
        ("cost_r   >  0.15  (REFUSED by total cap)", lambda r: r["cost_r"] > 0.15),
        ("PASSES BOTH shipped limbs", lambda r: r["spread_r"] <= 0.10 and r["cost_r"] <= 0.15),
        ("REFUSED by at least one shipped limb", lambda r: not (r["spread_r"] <= 0.10 and r["cost_r"] <= 0.15)),
        ("final_blocker_class == cost_authority", lambda r: r["blocker"] == "cost_authority"),
        ("final_blocker_class != cost_authority", lambda r: r["blocker"] != "cost_authority"),
    ]
    for name, pred in tests:
        a = agg([r for r in delayed if pred(r)])
        if a:
            res["gate_limbs"][name] = a
            print("%-40s %6d %+9.5f %8.4f %+8.2f %+9.1f" % (name, a["n"], a["mean"], a["res_win"] or 0, a["t"], a["total_R"]))

    print("\n=== the same gates at the MEASURED 7.3x / 8.5x spread overcharge (delayed clean) ===")
    print("%-46s %6s %9s %8s %9s" % ("split", "n", "mean", "resWin", "totalR"))
    for div in (1.0, 2.0, 4.0, 7.3, 8.5):
        for label, keep in (("PASSES", True), ("REFUSED", False)):
            def pred(r, d=div, k=keep):
                sp = r["spread_r"] / d
                tot = r["cost_r"] - r["spread_r"] + sp
                ok = (sp <= 0.10 and tot <= 0.15)
                return ok if k else (not ok)
            a = agg([r for r in delayed if pred(r)])
            if a:
                res["overcharge"]["div%.1f_%s" % (div, label)] = a
                print("%-46s %6d %+9.5f %8.4f %+9.1f" % ("spread/%.1f  %s both limbs" % (div, label), a["n"], a["mean"], a["res_win"] or 0, a["total_R"]))
        print()
    json.dump(res, open(OUT, "w"), indent=1)


if __name__ == "__main__":
    main()
