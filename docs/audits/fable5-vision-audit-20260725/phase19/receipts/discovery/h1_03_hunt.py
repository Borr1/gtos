"""h1-03 -- the hunt: every cell whose edge already pays its own broker toll.

Reports EVERY cell that clears, with n, t, per-month split and per-day positivity, at
three depth thresholds. No multiplicity correction is applied here on purpose: a later
stage tests whether these travel, and under-reporting is the failure mode of this lane.

Cell families searched (all combinations are the whole population, nothing sampled):
    1-way   symbol, class, family, session, kill_zone, broker_hour, utc_hour, dow,
            side, rdp_decile, cost_band
    2-way   symbol x broker_hour, symbol x family, symbol x session, symbol x killzone,
            symbol x side, family x broker_hour, class x broker_hour, class x session,
            family x session, family x rdp_decile, symbol x rdp_decile
    3-way   symbol x family x session-half, class x family x broker-hour-block
Plus the two decision-shaped screens:
    A. cheap-and-deep  -- rank by absolute money cost with n floors
    B. affordable      -- edge_over_cost > 1 in R and/or bps
"""
from __future__ import annotations

import gzip
import json
import math
import os
import statistics as st
from collections import defaultdict

D = os.path.dirname(os.path.abspath(__file__))
SRC = f"{D}/h1_COST_ROWS_V1.jsonl.gz"
OUT = f"{D}/H1_HUNT_V1.json"
EDGE = "K5_TRAIL025"


def mean(v):
    return sum(v) / len(v) if v else None


def se(v):
    n = len(v)
    if n < 2:
        return None
    m = sum(v) / n
    return math.sqrt(sum((x - m) ** 2 for x in v) / (n - 1) / n)


def summarize(rows):
    n = len(rows)
    c_r = [r["total_r"] for r in rows]
    c_b = [r["total_bps"] for r in rows]
    g_r = [r[EDGE] for r in rows]
    g_b = [r[EDGE] * r["rdp"] * 1e4 for r in rows]
    net_r = [a - b for a, b in zip(g_r, c_r)]
    net_b = [a - b for a, b in zip(g_b, c_b)]
    mc, mg = mean(c_r), mean(g_r)
    mcb, mgb = mean(c_b), mean(g_b)
    sn, snb = se(net_r), se(net_b)
    byday = defaultdict(list)
    bymon = defaultdict(list)
    for r, x in zip(rows, net_r):
        byday[r["day"]].append(x)
        bymon[r["month"]].append(x)
    dm = {d: mean(v) for d, v in byday.items()}
    pos = sum(1 for v in dm.values() if v > 0)
    mon = {m: {"n": len(v), "net_r": mean(v)} for m, v in bymon.items()}
    return {
        "n": n,
        "cost_r": mc, "cost_bps": mcb,
        "gross_r": mg, "gross_bps": mgb,
        "net_r": mean(net_r), "net_bps": mean(net_b),
        "t_net_r": (mean(net_r) / sn) if sn else None,
        "t_net_bps": (mean(net_b) / snb) if snb else None,
        "edge_over_cost_R": (mg / mc) if mc else None,
        "edge_over_cost_bps": (mgb / mcb) if mcb else None,
        "days": len(dm), "days_positive": pos,
        "day_pos_frac": pos / len(dm) if dm else None,
        "months": mon,
        "months_positive": sum(1 for v in mon.values() if v["net_r"] > 0),
        "rdp": mean([r["rdp"] for r in rows]),
        "spread_bps": mean([r["spread_bps"] for r in rows]),
        "comm_bps": mean([r["comm_bps"] for r in rows]),
        "slip_bps": mean([r["slip_bps"] for r in rows]),
        "swap_bps": mean([r["swap_bps"] for r in rows]),
    }


def main():
    rows = [json.loads(l) for l in gzip.open(SRC, "rt") if l.strip()]
    rr = sorted(rows, key=lambda r: r["rdp"])
    for i, r in enumerate(rr):
        r["_rdpdec"] = min(9, int(10 * i / len(rr)))
    rb = sorted(rows, key=lambda r: r["total_bps"])
    for i, r in enumerate(rb):
        r["_costdec"] = min(9, int(10 * i / len(rb)))
    for r in rows:
        r["_hblock"] = "%02d-%02d" % (r["broker_hour"] // 4 * 4, r["broker_hour"] // 4 * 4 + 3)

    KEYS = {
        "symbol": lambda r: r["symbol"],
        "class": lambda r: r["instrument_class"],
        "family": lambda r: r["family"],
        "session": lambda r: r["session"],
        "kill_zone": lambda r: r.get("kill_zone"),
        "broker_hour": lambda r: "bh%02d" % r["broker_hour"],
        "broker_hour_block": lambda r: "bhb" + r["_hblock"],
        "utc_hour": lambda r: "uh%02d" % r["utc_hour"],
        "dow": lambda r: "dow%d" % r["broker_dow"],
        "side": lambda r: r["side"],
        "rdp_decile": lambda r: "rdp%d" % r["_rdpdec"],
        "cost_decile": lambda r: "cost%d" % r["_costdec"],
        "symbol_x_broker_hour": lambda r: "%s|bh%02d" % (r["symbol"], r["broker_hour"]),
        "symbol_x_hblock": lambda r: "%s|bhb%s" % (r["symbol"], r["_hblock"]),
        "symbol_x_family": lambda r: "%s|%s" % (r["symbol"], r["family"]),
        "symbol_x_session": lambda r: "%s|%s" % (r["symbol"], r["session"]),
        "symbol_x_killzone": lambda r: "%s|%s" % (r["symbol"], r.get("kill_zone")),
        "symbol_x_side": lambda r: "%s|%s" % (r["symbol"], r["side"]),
        "symbol_x_rdpdec": lambda r: "%s|rdp%d" % (r["symbol"], r["_rdpdec"]),
        "family_x_broker_hour": lambda r: "%s|bh%02d" % (r["family"], r["broker_hour"]),
        "family_x_hblock": lambda r: "%s|bhb%s" % (r["family"], r["_hblock"]),
        "family_x_session": lambda r: "%s|%s" % (r["family"], r["session"]),
        "family_x_rdpdec": lambda r: "%s|rdp%d" % (r["family"], r["_rdpdec"]),
        "class_x_broker_hour": lambda r: "%s|bh%02d" % (r["instrument_class"], r["broker_hour"]),
        "class_x_session": lambda r: "%s|%s" % (r["instrument_class"], r["session"]),
        "class_x_family": lambda r: "%s|%s" % (r["instrument_class"], r["family"]),
        "symbol_x_family_x_hblock": lambda r: "%s|%s|bhb%s" % (r["symbol"], r["family"], r["_hblock"]),
        "class_x_family_x_hblock": lambda r: "%s|%s|bhb%s" % (r["instrument_class"], r["family"], r["_hblock"]),
    }

    tables = {}
    for name, fn in KEYS.items():
        g = defaultdict(list)
        for r in rows:
            g[fn(r)].append(r)
        tables[name] = {k: summarize(v) for k, v in g.items()}

    res = {"n_rows": len(rows), "edge_contract": EDGE,
           "pool": summarize(rows), "tables": tables}

    # ------------------------------------------------------------------ the hunt
    hits = []
    for tname, tab in tables.items():
        for k, v in tab.items():
            if v["edge_over_cost_R"] is None:
                continue
            if v["edge_over_cost_R"] > 1.0 or v["edge_over_cost_bps"] > 1.0 or v["net_r"] > 0:
                hits.append({"table": tname, "cell": k, **v})
    hits.sort(key=lambda h: -(h["edge_over_cost_R"] or -9))
    res["ALL_HITS"] = hits
    res["HIT_COUNTS_BY_DEPTH"] = {
        str(t): sum(1 for h in hits if h["n"] >= t) for t in (1, 10, 25, 50, 100, 200, 400)}

    # ------------------------------------------------------------ cheap-and-deep
    for t in (100, 300):
        cheap = sorted(
            [{"table": tn, "cell": k, **v} for tn, tab in tables.items()
             for k, v in tab.items() if v["n"] >= t],
            key=lambda h: h["cost_bps"])[:60]
        res[f"CHEAPEST_CELLS_n_ge_{t}"] = cheap

    # --------------------------------------------------------- best edge:toll deep
    for t in (100, 300):
        best = sorted(
            [{"table": tn, "cell": k, **v} for tn, tab in tables.items()
             for k, v in tab.items() if v["n"] >= t],
            key=lambda h: -(h["edge_over_cost_R"] or -9))[:60]
        res[f"BEST_EDGE_OVER_COST_n_ge_{t}"] = best

    json.dump(res, open(OUT, "w"), indent=1, default=str)

    # ------------------------------------------------------------------- digest
    print("pool: n=%d cost_R=%.4f cost_bps=%.4f gross_R=%+.5f net_R=%+.5f e/c=%.4f"
          % (res["pool"]["n"], res["pool"]["cost_r"], res["pool"]["cost_bps"],
             res["pool"]["gross_r"], res["pool"]["net_r"], res["pool"]["edge_over_cost_R"]))
    print("hits by depth:", res["HIT_COUNTS_BY_DEPTH"])
    print()
    hdr = ("%-26s %-38s %5s %8s %8s %9s %9s %7s %7s %6s %5s %3s"
           % ("table", "cell", "n", "cost_R", "costbps", "gross_R", "net_R", "e/c_R",
              "e/c_bps", "t_net", "days+", "mo+"))
    print(hdr)
    for h in [x for x in hits if x["n"] >= 100][:45]:
        print("%-26s %-38s %5d %8.4f %8.4f %+9.5f %+9.5f %7.3f %7.3f %6s %5s %3d"
              % (h["table"], h["cell"][:38], h["n"], h["cost_r"], h["cost_bps"],
                 h["gross_r"], h["net_r"], h["edge_over_cost_R"], h["edge_over_cost_bps"],
                 ("%+.2f" % h["t_net_r"]) if h["t_net_r"] is not None else "-",
                 "%d/%d" % (h["days_positive"], h["days"]), h["months_positive"]))


if __name__ == "__main__":
    main()
