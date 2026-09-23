#!/usr/bin/env python3
"""l8_tables — full single-axis tables (raw / clean / honest / thirds) for the receipt."""
import json, os, collections
import l8_lib as L
from l8_sweepN import enrich2

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "L8_TABLES_V1.json")
THIRDS = ["J1_d1_10", "J2_d11_20", "J3_d21_31"]


def table(rows, ax, min_n=1):
    g = collections.defaultdict(list)
    for r in rows:
        g[str(r.get(ax))].append(r)
    out = []
    for v, sub in g.items():
        clean = [r for r in sub if r["born"] != "born_past_stop"]
        rs = L.stats(sub)
        cs = L.stats(clean) if clean else None
        hs = L.stats(sub, "honest_r")
        hcs = L.stats(clean, "honest_r") if clean else None
        th = {}
        for t in THIRDS:
            s2 = [r for r in clean if r["third"] == t]
            st = L.stats(s2) if s2 else None
            th[t] = None if st is None else [st["n"], round(st["win"], 4), round(st["mean"], 4)]
        out.append({
            "value": v, "n_raw": rs["n"], "raw_win": round(rs["win"], 4), "raw_mean": round(rs["mean"], 5),
            "raw_t": round(rs["t"], 3),
            "n": cs["n"] if cs else 0, "win": round(cs["win"], 4) if cs else None,
            "mean": round(cs["mean"], 5) if cs else None, "t": round(cs["t"], 3) if cs else None,
            "payoff": round(cs["payoff"], 3) if cs else None, "be_win": round(cs["be_win"], 4) if cs else None,
            "edge_vs_be": round(cs["win"] - cs["be_win"], 4) if cs else None,
            "mean_win": round(cs["mean_win"], 4) if cs else None, "mean_loss": round(cs["mean_loss"], 4) if cs else None,
            "honest_mean": round(hs["mean"], 5), "honest_win": round(hs["win"], 4),
            "honest_clean_mean": round(hcs["mean"], 5) if hcs else None,
            "honest_clean_win": round(hcs["win"], 4) if hcs else None,
            "n_past_stop": rs["n"] - (cs["n"] if cs else 0),
            "past_stop_share": round((rs["n"] - (cs["n"] if cs else 0)) / rs["n"], 4),
            "thirds": th,
            "pos_thirds": sum(1 for x in th.values() if x and x[2] > 0),
        })
    out.sort(key=lambda c: -(c["mean"] if c["mean"] is not None else -9))
    return out


def main():
    rows = L.load()
    enrich2(rows)
    axes = ["hour", "hour_b", "family", "symbol", "side", "route_session", "session", "msc",
            "risk_pct", "born", "rdp_b", "spread_b", "cost_b", "prob_b", "ev_b", "fillp_b",
            "fill_class", "dup_b", "first_em", "order_type", "sched", "lifecycle", "dow",
            "day", "third", "week", "blocker", "adm_risk_class", "sel_action", "limit_mkt",
            "ptr_b", "risk_rank_b", "which_first", "sched_disp", "miss_reason", "adm_count"]
    res = {"pool": {"raw": L.stats(rows), "clean": L.stats([r for r in rows if r["born"] != "born_past_stop"]),
                    "honest": L.stats(rows, "honest_r")}, "tables": {}}
    for a in axes:
        res["tables"][a] = table(rows, a)
    with open(OUT, "w") as fh:
        json.dump(res, fh, indent=1)
    print("wrote", OUT, "axes", len(axes))


if __name__ == "__main__":
    main()
