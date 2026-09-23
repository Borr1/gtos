#!/usr/bin/env python3
"""l8_delay — the ENTRY-DELAY policy, priced, and its robustness to the same-bar tie rule.

POLICY: refuse any candidate whose entry level is first touched within the first k M1 bars
after the decision. Unfilled/refused candidates book 0.0 R (no trade, no loss).
Everything is measured per CANDIDATE-OPPORTUNITY so the skipped rows are priced honestly.
"""
import json, os, collections
import l8_lib as L
from l8_sweepN import enrich2
import l8_grid as G

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "L8_DELAY_V1.json")
DECL = (G.TGT.index(2.0), G.STP.index(-1.0))
TI, SI = DECL
THIRDS = ["J1_d1_10", "J2_d11_20", "J3_d21_31"]


def outcome(l, min_fill_bar=0):
    """Honest resolution; if the entry fills before min_fill_bar, the candidate is REFUSED."""
    fb = l["fill_bar"]
    if fb < 0 or fb <= min_fill_bar:
        return 0.0, ("refused_fast_fill" if 0 <= fb <= min_fill_bar and fb > 0 else "no_fill")
    bt, bs = l["tfav"][TI], l["tadv"][SI]
    if bs > 0 and (bt <= 0 or bs <= bt):
        return G.STP[SI], "stop"
    if bt > 0:
        return G.TGT[TI], "target"
    return l["r_end"], "mark"


def book(rows, k):
    n = len(rows)
    c = collections.Counter()
    vs = []
    for r in rows:
        v, o = outcome(r["_l"], k)
        c[o] += 1
        vs.append(v)
    m = sum(vs) / n
    sd = (sum((v - m) ** 2 for v in vs) / (n - 1)) ** 0.5 if n > 1 else 0.0
    traded = c["stop"] + c["target"] + c["mark"]
    res = c["stop"] + c["target"]
    tsum = sum(v for v in vs if v != 0.0)
    return {"k": k, "n_opportunities": n, "n_traded": traded,
            "traded_share": round(traded / n, 4),
            "mean_per_opportunity": round(m, 5),
            "mean_per_trade": round(tsum / traded, 5) if traded else None,
            "t_per_opportunity": round(m / (sd / n ** 0.5), 3) if sd else 0.0,
            "res_win": round(c["target"] / res, 4) if res else None,
            "target": c["target"], "stop": c["stop"], "mark": c["mark"],
            "refused": c["refused_fast_fill"], "no_fill": c["no_fill"],
            "total_R": round(sum(vs), 2)}


def main():
    rows = L.load()
    enrich2(rows)
    lad = G.load_ladder()
    for r in rows:
        r["_l"] = lad.get((r["cid"], r["dt"]))
    clean = [r for r in rows if r["born"] != "born_past_stop"]

    res = {"population": "clean (born_past_stop dropped)", "n": len(clean), "delay_sweep": [],
           "delay_sweep_all": [], "thirds": {}, "same_bar_tie": {}, "by_family": {}, "by_depth": {}}
    print("=== ENTRY-DELAY POLICY (CLEAN pool n=%d), honest 2R/-1R, per candidate-opportunity ===" % len(clean))
    print("%3s %8s %7s %14s %12s %8s %8s %8s" % ("k", "traded", "share", "R/opportunity", "R/trade", "resWin", "t", "totalR"))
    for k in [0, 1, 2, 3, 5, 8, 10, 15, 20, 30, 45, 60, 90]:
        b = book(clean, k)
        res["delay_sweep"].append(b)
        print("%3d %8d %7.4f %+14.5f %+12.5f %8.4f %+8.2f %+8.1f" % (
            k, b["n_traded"], b["traded_share"], b["mean_per_opportunity"], b["mean_per_trade"] or 0,
            b["res_win"] or 0, b["t_per_opportunity"], b["total_R"]))
    for k in [0, 1, 5, 15]:
        res["delay_sweep_all"].append(book(rows, k))
    print("\n(raw pool incl. born_past_stop) k=0 %+0.5f -> k=1 %+0.5f -> k=5 %+0.5f -> k=15 %+0.5f" % (
        res["delay_sweep_all"][0]["mean_per_opportunity"], res["delay_sweep_all"][1]["mean_per_opportunity"],
        res["delay_sweep_all"][2]["mean_per_opportunity"], res["delay_sweep_all"][3]["mean_per_opportunity"]))

    print("\n=== stability across January thirds (clean) ===")
    print("%-12s %8s %+12s %+12s %+12s" % ("third", "n", "k=0", "k=1", "k=5"))
    for t in THIRDS:
        sub = [r for r in clean if r["third"] == t]
        b0, b1, b5 = book(sub, 0), book(sub, 1), book(sub, 5)
        res["thirds"][t] = {"k0": b0, "k1": b1, "k5": b5}
        print("%-12s %8d %+12.5f %+12.5f %+12.5f" % (t, len(sub), b0["mean_per_opportunity"],
                                                     b1["mean_per_opportunity"], b5["mean_per_opportunity"]))

    # robustness: how much of the bar-1 penalty is the conservative same-bar tie rule?
    b1rows = [r for r in clean if r["_l"]["fill_bar"] == 1]
    stop_on_fill_bar = [r for r in b1rows if r["_l"]["tadv"][SI] == 1]
    tgt_on_fill_bar = [r for r in b1rows if r["_l"]["tfav"][TI] == 1]
    both = [r for r in b1rows if r["_l"]["tadv"][SI] == 1 and r["_l"]["tfav"][TI] == 1]
    # re-resolve bar-1 fills with the fill bar EXEMPT from the stop (optimistic bound)
    vs_opt = []
    for r in b1rows:
        l = r["_l"]
        bt, bs = l["tfav"][TI], l["tadv"][SI]
        if bs == 1:
            bs = -1
            for _ in ():
                pass
        if bs > 0 and (bt <= 0 or bs <= bt):
            vs_opt.append(G.STP[SI])
        elif bt > 0:
            vs_opt.append(G.TGT[TI])
        else:
            vs_opt.append(l["r_end"])
    b1_actual = book(b1rows, 0)
    res["same_bar_tie"] = {
        "n_bar1_fills": len(b1rows),
        "stop_touched_on_fill_bar": len(stop_on_fill_bar),
        "target_touched_on_fill_bar": len(tgt_on_fill_bar),
        "both_on_fill_bar": len(both),
        "actual_mean": b1_actual["mean_per_opportunity"],
        "mean_if_fill_bar_exempt_from_stop": round(sum(vs_opt) / len(vs_opt), 5),
    }
    print("\n=== same-bar tie-rule robustness on the %d bar-1 fills ===" % len(b1rows))
    print("stop touched on the fill bar: %d (%.2f%%) | target on fill bar: %d | both: %d" % (
        len(stop_on_fill_bar), 100 * len(stop_on_fill_bar) / len(b1rows), len(tgt_on_fill_bar), len(both)))
    print("actual mean %+0.5f | optimistic (fill bar cannot stop you) %+0.5f" % (
        b1_actual["mean_per_opportunity"], res["same_bar_tie"]["mean_if_fill_bar_exempt_from_stop"]))

    for ax in ["family", "depth", "hour_b", "symbol"]:
        g = collections.defaultdict(list)
        for r in clean:
            m = r["mkt_r"]
            r["depth"] = ("at_market" if (m is not None and abs(m) <= 1e-9) else
                          "thru" if (m is not None and m < 0) else "resting")
            g[str(r.get(ax))].append(r)
        tab = {}
        for v, sub in g.items():
            if len(sub) < 100:
                continue
            tab[v] = {"k0": book(sub, 0), "k1": book(sub, 1), "k5": book(sub, 5)}
        res["by_" + ax] = tab
    json.dump(res, open(OUT, "w"), indent=1)
    print("\n=== per family: R/opportunity at k=0 -> k=1 -> k=5 ===")
    print("%-32s %6s %10s %10s %10s %9s" % ("family", "n", "k=0", "k=1", "k=5", "k5-k0"))
    for v, d in sorted(res["by_family"].items(), key=lambda kv: -(kv[1]["k5"]["mean_per_opportunity"] - kv[1]["k0"]["mean_per_opportunity"])):
        print("%-32s %6d %+10.5f %+10.5f %+10.5f %+9.5f" % (
            v[:32], d["k0"]["n_opportunities"], d["k0"]["mean_per_opportunity"],
            d["k1"]["mean_per_opportunity"], d["k5"]["mean_per_opportunity"],
            d["k5"]["mean_per_opportunity"] - d["k0"]["mean_per_opportunity"]))


if __name__ == "__main__":
    main()
