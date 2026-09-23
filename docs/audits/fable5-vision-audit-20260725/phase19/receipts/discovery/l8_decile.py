#!/usr/bin/env python3
"""l8_decile — decile tables for every continuous decision-time-available field."""
import json, os
import l8_lib as L
from l8_sweepN import enrich2

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "L8_DECILES_V1.json")
FIELDS = ["ev_r", "prob", "spread_r", "cost_r", "rdp", "mkt_r", "fill_prob", "comm_r",
          "swap_r", "same_sym_risk", "same_side_risk", "opp_risk", "risk_rank",
          "policy_target_r", "risk_pct", "msc"]
NB = 10


def deciles(rows, f, nb=NB):
    vs = sorted((r[f] for r in rows if r.get(f) is not None))
    if len(vs) < nb * 20:
        nb = max(2, len(vs) // 200)
    if not vs:
        return None
    cuts = [vs[int(len(vs) * i / nb)] for i in range(1, nb)]
    out = []
    for i in range(nb):
        lo = -1e18 if i == 0 else cuts[i - 1]
        hi = 1e18 if i == nb - 1 else cuts[i]
        g = [r for r in rows if r.get(f) is not None and (r[f] >= lo if i == 0 else r[f] > lo) and (r[f] <= hi if i == nb - 1 else r[f] <= hi)]
        if not g:
            continue
        s = L.stats(g)
        hs = L.stats(g, "honest_r")
        th = {}
        for t in ["J1_d1_10", "J2_d11_20", "J3_d21_31"]:
            sub = [r for r in g if r["third"] == t]
            st = L.stats(sub) if sub else None
            th[t] = None if st is None else [st["n"], round(st["mean"], 4)]
        out.append({"bin": i, "lo": round(lo, 6) if lo > -1e17 else None, "hi": round(hi, 6) if hi < 1e17 else None,
                    "n": s["n"], "win": round(s["win"], 4), "mean": round(s["mean"], 5), "t": round(s["t"], 3),
                    "payoff": round(s["payoff"], 3), "edge_vs_be": round(s["win"] - s["be_win"], 4),
                    "honest_mean": round(hs["mean"], 5),
                    "thirds": th, "pos_thirds": sum(1 for v in th.values() if v and v[1] > 0)})
    return out


def main():
    rows = [r for r in L.load() if r["born"] != "born_past_stop"]
    enrich2(rows)
    res = {"population": "clean (born_past_stop dropped)", "n": len(rows), "fields": {}}
    for f in FIELDS:
        d = deciles(rows, f)
        if d:
            res["fields"][f] = d
    with open(OUT, "w") as fh:
        json.dump(res, fh, indent=1)
    for f, d in res["fields"].items():
        span = max(c["mean"] for c in d) - min(c["mean"] for c in d)
        mono = sum(1 for a, b in zip(d, d[1:]) if b["mean"] > a["mean"])
        print("%-18s bins=%2d span=%.4f monotone_up=%d/%d  top=%+.4f(n=%d) bot=%+.4f(n=%d)" % (
            f, len(d), span, mono, len(d) - 1,
            max(c["mean"] for c in d), [c["n"] for c in d if c["mean"] == max(x["mean"] for x in d)][0],
            min(c["mean"] for c in d), [c["n"] for c in d if c["mean"] == min(x["mean"] for x in d)][0]))


if __name__ == "__main__":
    main()
