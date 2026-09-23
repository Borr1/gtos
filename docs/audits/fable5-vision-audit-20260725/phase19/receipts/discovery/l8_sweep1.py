#!/usr/bin/env python3
"""l8_sweep1 — single-axis conditioning sweep over the January diagnostic pool."""
import json, os, collections
import l8_lib as L

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "L8_SWEEP1_SINGLE_V1.json")

AXES = ["symbol", "family", "side", "session", "route_session", "kill_zone", "msc",
        "risk_pct", "sched", "blocker", "miss_reason", "lifecycle", "order_type",
        "fill_class", "limit_mkt", "sel_action", "sched_disp", "adm_risk_class",
        "adm_count", "first_em", "born", "which_first", "hour", "dow", "day",
        "rdp_b", "spread_b", "cost_b", "prob_b", "ev_b", "fillp_b",
        "third", "half", "week", "dup_b", "ptr_b", "risk_rank_b"]

MIN_N = 50


def enrich(rows):
    for r in rows:
        d = r.get("dup_count") or 1
        r["dup_b"] = "1" if d <= 1 else ("2-5" if d <= 5 else ("6-20" if d <= 20 else ">20"))
        p = r.get("policy_target_r")
        r["ptr_b"] = "2.0" if (p is not None and abs(p - 2.0) < 1e-9) else ("null" if p is None else ("<2" if p < 2 else "2-5" if p <= 5 else "5-20" if p <= 20 else ">20"))
        rr = r.get("risk_rank")
        try:
            rr = int(rr)
        except (TypeError, ValueError):
            rr = None
        r["risk_rank_b"] = "null" if rr is None else ("1" if rr == 1 else "2-3" if rr <= 3 else "4-10" if rr <= 10 else "11-30" if rr <= 30 else ">30")


def main():
    rows = L.load()
    enrich(rows)
    thirds = ["J1_d1_10", "J2_d11_20", "J3_d21_31"]
    res = {"pool": {"raw": L.stats(rows), "clean": L.stats([r for r in rows if r["born"] != "born_past_stop"]),
                    "honest": L.stats(rows, "honest_r")},
           "min_n": MIN_N, "axes": {}, "cells_examined": 0}
    total_cells = 0
    for ax in AXES:
        groups = collections.defaultdict(list)
        for r in rows:
            groups[str(r.get(ax))].append(r)
        cells = []
        for v, g in groups.items():
            total_cells += 1
            if len(g) < MIN_N:
                continue
            cs = L.cellstats(g)
            byt = {}
            for t in thirds:
                sub = [r for r in g if r["third"] == t]
                st = L.stats(sub) if sub else None
                byt[t] = None if st is None else {"n": st["n"], "win": round(st["win"], 4), "mean": round(st["mean"], 4)}
            cells.append({
                "axis": ax, "value": v,
                "n": cs["raw"]["n"], "win": round(cs["raw"]["win"], 4), "mean": round(cs["raw"]["mean"], 5),
                "t": round(cs["raw"]["t"], 3), "sum": round(cs["raw"]["sum"], 2),
                "payoff": round(cs["raw"]["payoff"], 3), "be_win": round(cs["raw"]["be_win"], 4),
                "mean_win": round(cs["raw"]["mean_win"], 4), "mean_loss": round(cs["raw"]["mean_loss"], 4),
                "n_past_stop": cs["n_past_stop"],
                "clean_n": cs["clean"]["n"] if cs["clean"] else 0,
                "clean_win": round(cs["clean"]["win"], 4) if cs["clean"] else None,
                "clean_mean": round(cs["clean"]["mean"], 5) if cs["clean"] else None,
                "clean_t": round(cs["clean"]["t"], 3) if cs["clean"] else None,
                "honest_win": round(cs["honest"]["win"], 4), "honest_mean": round(cs["honest"]["mean"], 5),
                "honest_t": round(cs["honest"]["t"], 3),
                "thirds": byt,
                "edge_vs_be": round(cs["raw"]["win"] - cs["raw"]["be_win"], 4),
                "impact": round(cs["raw"]["sum"], 2),
            })
        cells.sort(key=lambda c: -c["mean"])
        res["axes"][ax] = cells
    res["cells_examined"] = total_cells
    res["cells_reported"] = sum(len(v) for v in res["axes"].values())
    with open(OUT, "w") as fh:
        json.dump(res, fh, indent=1)
    print("cells examined", total_cells, "reported", res["cells_reported"])
    # compact stdout: every positive-mean cell, and the worst 12
    pos = [c for ax in res["axes"].values() for c in ax if c["mean"] > 0]
    pos.sort(key=lambda c: -c["mean"])
    print("\nPOSITIVE-MEAN CELLS (raw gross_r), n>=%d: %d" % (MIN_N, len(pos)))
    print("%-16s %-34s %6s %6s %9s %7s %9s %9s" % ("axis", "value", "n", "win", "mean", "t", "cleanMean", "honestMean"))
    for c in pos[:40]:
        print("%-16s %-34s %6d %6.3f %+9.4f %+7.2f %+9.4f %+9.4f" % (
            c["axis"], c["value"][:34], c["n"], c["win"], c["mean"], c["t"],
            c["clean_mean"] if c["clean_mean"] is not None else float("nan"), c["honest_mean"]))


if __name__ == "__main__":
    main()
