#!/usr/bin/env python3
"""l8_final — receipt tables on the delayed-fill clean population + the stacked policy."""
import json, os, collections
import l8_lib as L
from l8_sweepN import enrich2
import l8_grid as G

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "L8_FINAL_V1.json")
TI, SI = G.TGT.index(2.0), G.STP.index(-1.0)
THIRDS = ["J1_d1_10", "J2_d11_20", "J3_d21_31"]


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
    a = {"n": n, "mean": round(m, 5), "t": round(m / (sd / n ** 0.5), 3) if sd else 0.0,
         "win": round(sum(1 for v in vs if v > 0) / n, 4),
         "res_win": round(c["target"] / res, 4) if res else None, "n_res": res,
         "target": c["target"], "stop": c["stop"], "mark": c["mark"], "no_fill": c["no_fill"],
         "gross_mean": round(sum(r["gross_r"] for r in rows) / n, 5), "total_R": round(sum(vs), 2)}
    th = {}
    for t in THIRDS:
        s2 = [r for r in rows if r["third"] == t]
        if len(s2) >= 12:
            v2 = [res1(r["_l"])[0] for r in s2]
            th[t] = [len(s2), round(sum(v2) / len(v2), 5)]
        else:
            th[t] = None
    a["thirds"] = th
    a["pos_thirds"] = sum(1 for v in th.values() if v and v[1] > 0)
    return a


def table(rows, ax, min_n=40):
    g = collections.defaultdict(list)
    for r in rows:
        g[str(r.get(ax))].append(r)
    out = []
    for v, sub in g.items():
        if len(sub) < min_n:
            continue
        a = agg(sub)
        a["value"] = v
        out.append(a)
    out.sort(key=lambda c: -c["mean"])
    return out


def main():
    rows = L.load()
    enrich2(rows)
    lad = G.load_ladder()
    for r in rows:
        r["_l"] = lad.get((r["cid"], r["dt"]))
    clean = [r for r in rows if r["born"] != "born_past_stop"]
    delayed = [r for r in clean if r["_l"]["fill_bar"] >= 2]
    res = {"base_delayed": agg(delayed), "tables": {}, "stack": []}
    for ax in ["cost_b", "spread_b", "hour_b", "hour", "family", "symbol", "dow", "prob_b",
               "ev_b", "rdp_b", "side", "route_session", "risk_pct", "fill_class", "msc",
               "born", "risk_rank_b", "first_em", "fs", "third"]:
        res["tables"][ax] = table(delayed, ax)

    # the stacked policy, priced per CANDIDATE-OPPORTUNITY over the whole raw pool
    N_ALL = len(rows)
    stack = [
        ("0. raw pool, honest 2R/-1R", rows),
        ("1. drop born_past_stop (untakeable, W0-capture)", clean),
        ("2. + one-minute entry delay (refuse bar-1 fills)", delayed),
        ("3. + shipped cost gate PASSES (spread<=0.10 AND cost<=0.15)",
         [r for r in delayed if r["spread_r"] <= 0.10 and r["cost_r"] <= 0.15]),
        ("3b. + cost_r in [0.10,0.15] band only",
         [r for r in delayed if 0.10 < r["cost_r"] <= 0.15]),
        ("4. + drop spread_r>1.0", [r for r in delayed if r["spread_r"] <= 1.0]),
        ("5. + drop hour_b in {h00_03,h12_15}",
         [r for r in delayed if r["hour_b"] not in ("h00_03", "h12_15")]),
    ]
    print("=== STACKED POLICY, priced per CANDIDATE-OPPORTUNITY over all %d pool rows ===" % N_ALL)
    print("%-58s %6s %9s %8s %11s %9s" % ("step", "n", "R/trade", "resWin", "R/opportunity", "totalR"))
    for name, pop in stack:
        a = agg(pop)
        a["step"] = name
        a["mean_per_opportunity_over_full_pool"] = round(a["total_R"] / N_ALL, 5)
        res["stack"].append(a)
        print("%-58s %6d %+9.5f %8.4f %+11.5f %+9.1f" % (
            name[:58], a["n"], a["mean"], a["res_win"] or 0,
            a["mean_per_opportunity_over_full_pool"], a["total_R"]))
    json.dump(res, open(OUT, "w"), indent=1)

    b = res["base_delayed"]
    print("\nDELAYED base n=%d mean=%+.5f resWin=%.4f" % (b["n"], b["mean"], b["res_win"]))
    for ax in ["cost_b", "hour_b", "family", "dow", "symbol"]:
        print("\n=== %s (delayed-fill clean, honest 2R/-1R) ===" % ax)
        print("%-24s %5s %9s %8s %7s %6s %s" % ("value", "n", "mean", "resWin", "t", "th+", "thirds"))
        for c in res["tables"][ax]:
            ts = " ".join(("%+.3f" % v[1]) if v else "   .  " for v in [c["thirds"][t] for t in THIRDS])
            print("%-24s %5d %+9.5f %8.4f %+7.2f %4d/3 %s" % (
                c["value"][:24], c["n"], c["mean"], c["res_win"] or 0, c["t"], c["pos_thirds"], ts))


if __name__ == "__main__":
    main()
