"""h1-02 -- the dispersion tables. Every axis, both units, ranked.

Reads h1_COST_ROWS_V1.jsonl.gz, writes H1_SURFACE_V1.json (machine) and prints a
bounded digest. Nothing is sampled; every table is the whole population.

UNITS. Two views of the same money and they rank differently:
    cost_bps = cost_price / entry_price * 1e4      -- what the trade costs, absolutely
    cost_r   = cost_price / risk_distance          -- what the GATE sees
and cost_r = cost_bps / (rdp*1e4) where rdp = risk_distance/entry_price. So the R view is
the bps view divided by the stop width. Everywhere the two disagree, stop geometry is the
reason and not the broker.

EDGE. `K5_TRAIL025` -- the repaired contract the swarm established (market entry delayed
5 minutes, 0.25R trail, no other change). Pooled mean +0.038342 R/trade, reproduced here.
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
OUT = f"{D}/H1_SURFACE_V1.json"
EDGE = "K5_TRAIL025"


def load():
    return [json.loads(l) for l in gzip.open(SRC, "rt") if l.strip()]


def mean(v):
    return sum(v) / len(v) if v else None


def med(v):
    return st.median(v) if v else None


def se(v):
    n = len(v)
    if n < 2:
        return None
    m = sum(v) / n
    return math.sqrt(sum((x - m) ** 2 for x in v) / (n - 1) / n)


def cell(rows, cost_key="total_r", cost_bps_key="total_bps"):
    """The one summary every table uses."""
    n = len(rows)
    if n == 0:
        return None
    c_r = [r[cost_key] for r in rows]
    c_b = [r[cost_bps_key] for r in rows]
    g_r = [r[EDGE] for r in rows]
    g_b = [r[EDGE] * r["rdp"] * 1e4 for r in rows]
    net = [a - b for a, b in zip(g_r, c_r)]
    mg, mc = mean(g_r), mean(c_r)
    sg = se(g_r)
    sn = se(net)
    return {
        "n": n,
        "cost_r": mc, "cost_r_med": med(c_r),
        "cost_bps": mean(c_b), "cost_bps_med": med(c_b),
        "gross_r": mg, "gross_bps": mean(g_b),
        "net_r": mean(net), "net_bps": mean(g_b) - mean(c_b),
        "t_gross": (mg / sg) if sg else None,
        "t_net": (mean(net) / sn) if sn else None,
        "edge_over_cost_R": (mg / mc) if mc else None,
        "edge_over_cost_bps": (mean(g_b) / mean(c_b)) if mean(c_b) else None,
        "spread_r": mean([r["spread_r"] for r in rows]),
        "comm_r": mean([r["comm_r"] for r in rows]),
        "slip_r": mean([r["slip_r"] for r in rows]),
        "swap_r": mean([r["swap_r"] for r in rows]),
        "spread_bps": mean([r["spread_bps"] for r in rows]),
        "comm_bps": mean([r["comm_bps"] for r in rows]),
        "slip_bps": mean([r["slip_bps"] for r in rows]),
        "swap_bps": mean([r["swap_bps"] for r in rows]),
        "rdp": mean([r["rdp"] for r in rows]),
        "n_pos_days": None,
    }


def group(rows, keyfn):
    g = defaultdict(list)
    for r in rows:
        g[keyfn(r)].append(r)
    return g


def table(rows, keyfn, minn=1):
    g = group(rows, keyfn)
    out = {}
    for k, v in g.items():
        if len(v) < minn:
            continue
        out[str(k)] = cell(v)
    return out


def eta2(rows, keyfn, val=lambda r: math.log(max(r["total_bps"], 1e-9))):
    """Share of variance in log(cost) explained by this axis. The honest 'which axis
    carries the most' answer -- a range is dominated by its thinnest cell, eta^2 is not."""
    vals = [val(r) for r in rows]
    gm = mean(vals)
    sst = sum((x - gm) ** 2 for x in vals)
    g = group(rows, keyfn)
    ssb = 0.0
    for k, v in g.items():
        m = mean([val(r) for r in v])
        ssb += len(v) * (m - gm) ** 2
    return {"eta2": ssb / sst if sst else None, "k": len(g)}


def dispersion(tab, key):
    vals = [(k, v[key]) for k, v in tab.items() if v and v[key] is not None and v[key] > 0]
    if len(vals) < 2:
        return None
    vals.sort(key=lambda x: x[1])
    return {"min_cell": vals[0][0], "min": vals[0][1],
            "max_cell": vals[-1][0], "max": vals[-1][1],
            "ratio": vals[-1][1] / vals[0][1], "k": len(vals)}


def spearman(pairs):
    """pairs: list of (a, b). Returns rho."""
    if len(pairs) < 3:
        return None
    def ranks(xs):
        order = sorted(range(len(xs)), key=lambda i: xs[i])
        rk = [0.0] * len(xs)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1
            for t in range(i, j + 1):
                rk[order[t]] = avg
            i = j + 1
        return rk
    a = ranks([p[0] for p in pairs])
    b = ranks([p[1] for p in pairs])
    ma, mb = mean(a), mean(b)
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    da = math.sqrt(sum((x - ma) ** 2 for x in a))
    db = math.sqrt(sum((y - mb) ** 2 for y in b))
    return num / (da * db) if da and db else None


def main():
    rows = load()
    res = {"n_rows": len(rows), "edge_contract": EDGE}

    # ---------------------------------------------------------------- 1. pool + terms
    res["POOL"] = cell(rows)
    res["POOL_ALT_BASES"] = {
        k: {"cost_r": mean([r[k] for r in rows]),
            "cost_bps_equiv": mean([r[k] / r["rdp"] * 1e-4 * 1e4 * r["rdp"] * 1e4 for r in rows])}
        for k in ("total_r", "total_r_noswap", "total_r_flat", "total_r_era",
                  "swarm_cost_true_r", "cost_frozen_r")
    }
    res["POOL_ALT_BASES"] = {
        k: {"mean_cost_r": mean([r[k] for r in rows])}
        for k in ("total_r", "total_r_noswap", "total_r_flat", "total_r_era",
                  "swarm_cost_true_r", "cost_frozen_r")
    }
    # term dominance: which of the four terms is largest, per row, in bps and in R
    dom_b, dom_r = defaultdict(int), defaultdict(int)
    for r in rows:
        tb = {"spread": r["spread_bps"], "commission": r["comm_bps"],
              "slippage": r["slip_bps"], "swap": r["swap_bps"]}
        tr = {"spread": r["spread_r"], "commission": r["comm_r"],
              "slippage": r["slip_r"], "swap": r["swap_r"]}
        dom_b[max(tb, key=tb.get)] += 1
        dom_r[max(tr, key=tr.get)] += 1
    res["TERM_DOMINANCE"] = {"by_bps": dict(dom_b), "by_R": dict(dom_r)}
    res["TERM_SHARE_OF_TOTAL_BPS"] = {
        t: mean([r[f"{k}_bps"] for r in rows]) / mean([r["total_bps"] for r in rows])
        for t, k in (("spread", "spread"), ("commission", "comm"),
                     ("slippage", "slip"), ("swap", "swap"))}
    res["TERM_SHARE_OF_TOTAL_R"] = {
        t: mean([r[f"{k}_r"] for r in rows]) / mean([r["total_r"] for r in rows])
        for t, k in (("spread", "spread"), ("commission", "comm"),
                     ("slippage", "slip"), ("swap", "swap"))}

    # ---------------------------------------------------------------- 2. axes
    AXES = {
        "symbol": lambda r: r["symbol"],
        "instrument_class": lambda r: r["instrument_class"],
        "origin_family": lambda r: r["family"],
        "route_session": lambda r: r["session"],
        "kill_zone": lambda r: r.get("kill_zone"),
        "utc_hour": lambda r: r["utc_hour"],
        "broker_hour": lambda r: r["broker_hour"],
        "utc_dow": lambda r: r["utc_dow"],
        "broker_dow": lambda r: r["broker_dow"],
        "month": lambda r: r["month"],
        "side": lambda r: r["side"],
        "rdp_decile": None,   # filled below
    }
    rr = sorted(rows, key=lambda r: r["rdp"])
    dec = {}
    for i, r in enumerate(rr):
        dec[id(r)] = min(9, int(10 * i / len(rr)))
    AXES["rdp_decile"] = lambda r: dec[id(r)]

    res["AXES"] = {}
    res["AXIS_DISPERSION"] = {}
    res["AXIS_ETA2"] = {}
    for name, fn in AXES.items():
        tab = table(rows, fn)
        res["AXES"][name] = tab
        res["AXIS_DISPERSION"][name] = {
            "cost_bps": dispersion(tab, "cost_bps"),
            "cost_r": dispersion(tab, "cost_r"),
        }
        res["AXIS_ETA2"][name] = {
            "log_cost_bps": eta2(rows, fn),
            "log_cost_r": eta2(rows, fn,
                               val=lambda r: math.log(max(r["total_r"], 1e-9))),
        }

    # ---------------------------------------------------------------- 3. bps vs R
    for name in ("symbol", "origin_family", "instrument_class", "broker_hour",
                 "kill_zone", "route_session"):
        tab = res["AXES"][name]
        pairs = [(v["cost_bps"], v["cost_r"]) for v in tab.values() if v]
        res.setdefault("BPS_VS_R", {})[name] = {
            "spearman": spearman(pairs),
            "rank_moves": None,
        }
    # explicit per-symbol rank comparison
    tab = res["AXES"]["symbol"]
    by_b = sorted(tab, key=lambda k: tab[k]["cost_bps"])
    by_r = sorted(tab, key=lambda k: tab[k]["cost_r"])
    res["BPS_VS_R"]["symbol"]["rank_moves"] = {
        s: {"rank_bps": by_b.index(s) + 1, "rank_R": by_r.index(s) + 1,
            "move": (by_b.index(s) + 1) - (by_r.index(s) + 1),
            "cost_bps": tab[s]["cost_bps"], "cost_r": tab[s]["cost_r"],
            "rdp": tab[s]["rdp"]}
        for s in tab}

    # ---------------------------------------------------------------- 4. cross tables
    CROSS = {
        "symbol_x_broker_hour": lambda r: (r["symbol"], r["broker_hour"]),
        "symbol_x_family": lambda r: (r["symbol"], r["family"]),
        "symbol_x_session": lambda r: (r["symbol"], r["session"]),
        "symbol_x_killzone": lambda r: (r["symbol"], r.get("kill_zone")),
        "family_x_broker_hour": lambda r: (r["family"], r["broker_hour"]),
        "class_x_broker_hour": lambda r: (r["instrument_class"], r["broker_hour"]),
        "symbol_x_side": lambda r: (r["symbol"], r["side"]),
        "symbol_x_month": lambda r: (r["symbol"], r["month"]),
    }
    res["CROSS"] = {}
    for name, fn in CROSS.items():
        res["CROSS"][name] = {f"{k[0]}|{k[1]}": v
                              for k, v in
                              ((k, cell(v)) for k, v in group(rows, fn).items())}
        res["AXIS_ETA2"][name] = {"log_cost_bps": eta2(rows, fn)}

    # ---------------------------------------------------------------- 5. the hunt
    hits = []
    for tabname, tab in ([("axis:" + k, v) for k, v in res["AXES"].items()] +
                         [("cross:" + k, v) for k, v in res["CROSS"].items()]):
        for k, v in tab.items():
            if not v or v["edge_over_cost_R"] is None:
                continue
            if v["edge_over_cost_R"] > 1.0 or v["net_r"] > 0:
                hits.append({"table": tabname, "cell": k, **v})
    hits.sort(key=lambda h: -h["net_r"])
    res["HITS_edge_over_cost_gt_1_or_net_positive"] = hits

    json.dump(res, open(OUT, "w"), indent=1, default=str)

    # ------------------------------------------------------------------- digest
    P = res["POOL"]
    print("POOL n=%d  cost %.6f R / %.4f bps | gross %.6f R / %.4f bps | net %.6f R"
          % (P["n"], P["cost_r"], P["cost_bps"], P["gross_r"], P["gross_bps"], P["net_r"]))
    print("edge:toll  R=%.4f  bps=%.4f" % (P["edge_over_cost_R"], P["edge_over_cost_bps"]))
    print("term share of bps:", {k: round(v, 4) for k, v in res["TERM_SHARE_OF_TOTAL_BPS"].items()})
    print("term share of R  :", {k: round(v, 4) for k, v in res["TERM_SHARE_OF_TOTAL_R"].items()})
    print("dominant term by bps:", dict(dom_b), " by R:", dict(dom_r))
    print()
    print("%-22s %6s %8s %8s %8s %8s" % ("AXIS", "k", "eta2bps", "eta2R", "disp_bps", "disp_R"))
    for name in list(AXES) + list(CROSS):
        e = res["AXIS_ETA2"][name]
        db = (res["AXIS_DISPERSION"].get(name) or {}).get("cost_bps")
        dr = (res["AXIS_DISPERSION"].get(name) or {}).get("cost_r")
        print("%-22s %6d %8.4f %8s %8s %8s"
              % (name, e["log_cost_bps"]["k"], e["log_cost_bps"]["eta2"],
                 ("%.4f" % e["log_cost_r"]["eta2"]) if "log_cost_r" in e else "-",
                 ("%.1fx" % db["ratio"]) if db else "-",
                 ("%.1fx" % dr["ratio"]) if dr else "-"))
    print()
    print("HITS (edge/cost > 1 or net > 0):", len(hits))
    for h in hits[:25]:
        print("  %-28s %-34s n=%5d cost_R=%.4f gross_R=%.4f net_R=%+.4f e/c=%.2f t_net=%s"
              % (h["table"], h["cell"], h["n"], h["cost_r"], h["gross_r"], h["net_r"],
                 h["edge_over_cost_R"],
                 ("%+.2f" % h["t_net"]) if h["t_net"] is not None else "-"))


if __name__ == "__main__":
    main()
