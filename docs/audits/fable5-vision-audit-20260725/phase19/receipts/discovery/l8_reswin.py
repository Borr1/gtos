#!/usr/bin/env python3
"""l8_reswin — the RESOLUTION WIN RATE gradient: target/(target+stop) on the honest
2R/-1R first-touch contract. The pool sits at 0.2315 and needs 0.3333."""
import json, os, collections
import l8_lib as L
from l8_sweepN import enrich2
import l8_grid as G

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "L8_RESWIN_V1.json")
DECL = (G.TGT.index(2.0), G.STP.index(-1.0))
THIRDS = ["J1_d1_10", "J2_d11_20", "J3_d21_31"]


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
            "tgt": c["target"], "stop": c["stop"], "mark": c["mark"], "nofill": c["no_fill"],
            "res_win": round(c["target"] / res, 4) if res else None,
            "target_rate": round(c["target"] / n, 4), "stop_rate": round(c["stop"] / n, 4),
            "mark_rate": round(c["mark"] / n, 4), "nofill_rate": round(c["no_fill"] / n, 4),
            "gross_mean": round(sum(r["gross_r"] for r in rows) / n, 5)}


def table(rows, ax, min_n=50):
    g = collections.defaultdict(list)
    for r in rows:
        g[str(r.get(ax))].append(r)
    out = []
    for v, sub in g.items():
        if len(sub) < min_n:
            continue
        a = agg(sub)
        a["value"] = v
        th = {}
        for t in THIRDS:
            s2 = [r for r in sub if r["third"] == t]
            aa = agg(s2) if len(s2) >= 15 else None
            th[t] = None if aa is None else [aa["n"], aa["res_win"], aa["mean"]]
        a["thirds"] = th
        out.append(a)
    out.sort(key=lambda c: -(c["res_win"] or 0))
    return out


def main():
    rows = L.load()
    enrich2(rows)
    lad = G.load_ladder()
    for r in rows:
        r["_l"] = lad.get((r["cid"], r["dt"]))
        fb = r["_l"]["fill_bar"]
        r["fill_bar"] = fb
        r["fillspeed"] = ("never" if fb < 0 else "bar1" if fb == 1 else "b2_5" if fb <= 5
                          else "b6_15" if fb <= 15 else "b16_60" if fb <= 60 else "b61_120")
        m = r["mkt_r"]
        r["mkt_b"] = ("null" if m is None else "past_stop" if m <= -1 else "thru_-1_-0.5" if m <= -0.5
                      else "thru_-0.5_0" if m < -1e-9 else "at_0" if m <= 1e-9
                      else "away_0_0.25" if m <= 0.25 else "away_0.25_0.5" if m <= 0.5
                      else "away_0.5_1" if m <= 1.0 else "away_1_2" if m <= 2.0 else "away_gt2")
    clean = [r for r in rows if r["born"] != "born_past_stop"]
    res = {"pool_all": agg(rows), "pool_clean": agg(clean), "tables": {}}
    for ax in ["fillspeed", "mkt_b", "born", "fill_class", "hour", "hour_b", "family", "symbol",
               "side", "route_session", "spread_b", "cost_b", "rdp_b", "prob_b", "ev_b",
               "fillp_b", "msc", "risk_pct", "dow", "third", "order_type", "lifecycle",
               "risk_rank_b", "first_em", "dup_b", "sched"]:
        res["tables"][ax] = table(clean, ax)
    json.dump(res, open(OUT, "w"), indent=1)
    p = res["pool_clean"]
    print("POOL CLEAN n=%d resWin=%.4f mean=%+.5f | tgt %d stop %d mark %d nofill %d"
          % (p["n"], p["res_win"], p["mean"], p["tgt"], p["stop"], p["mark"], p["nofill"]))
    for ax in ["fillspeed", "mkt_b", "fill_class", "hour_b", "family"]:
        print("\n=== %s ===  (sorted by resolution win rate; 0.3333 = breakeven at 2R/-1R)" % ax)
        print("  %-22s %6s %7s %8s %8s %8s %8s %9s" % ("value", "n", "resWin", "tgtRate", "stopRate", "markRate", "mean", "grossMean"))
        for c in res["tables"][ax]:
            print("  %-22s %6d %7.4f %8.4f %8.4f %8.4f %+8.4f %+9.4f" % (
                c["value"][:22], c["n"], c["res_win"] or 0, c["target_rate"], c["stop_rate"],
                c["mark_rate"], c["mean"], c["gross_mean"]))


if __name__ == "__main__":
    main()
