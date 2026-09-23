"""h3-06 -- INSTRUMENT SELECTION: the efficient frontier of (instruments kept, net bps).

Cost is the only thing in this problem with a 7x cross-sectional spread and a -0.980 rank
correlation with net, so dropping expensive instruments is the largest single toll lever
available. This prices it exactly, three ways:

  EX-ANTE      symbols ranked by mean broker-true toll, cheapest first. Uses no outcome
               information; runnable live today.
  IN-SAMPLE    symbols ranked by realised net bps. The ceiling, and selection on the answer.
  TRAIN/TEST   symbols ranked on JANUARY ONLY, frontier read on FEBRUARY+MARCH. This is the
               only arm that answers "does the choice travel".

Every row of every frontier carries n, keep rate, edge/toll/net in bps, and the same in R
per trade and per opportunity, because the two spaces answer different questions:
bps decides affordability, R decides money.
"""
import json
import os
import sys

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import h3_lib as H  # noqa: E402

COL = "K5_TRAIL025"
rows = H.load_atmkt()
H.add_hour_cost(rows)
out = {"lane": "h3", "step": "instruments", "contract": COL, "n": len(rows)}


def cell(rs, cost_key="cost_true"):
    g, t, n, keep = H.scored(rs, COL, cost_key)
    if not g:
        return None
    return {"n": len(g), "edge_bps": H.mean(g), "toll_bps": H.mean(t), "net_bps": H.mean(n),
            "edge_over_toll": H.mean(g) / H.mean(t) if H.mean(t) else None,
            "gross_r": H.mean([r[COL] for r in keep]),
            "cost_r": H.mean([r[cost_key] for r in keep]),
            "net_r": H.mean([r[COL] - r[cost_key] for r in keep]),
            "t_net_trade": H.tstat(n), "t_gross_trade": H.tstat(g),
            "mean_rdp_bps": H.mean([r["rdp_bps"] for r in keep]),
            "spread_bps": H.mean([r["real_spread_r"] * r["rdp"] * 1e4 for r in keep]),
            "comm_bps": H.mean([r["real_comm_r"] * r["rdp"] * 1e4 for r in keep]),
            "slip_bps": H.mean([r["real_slip_r"] * r["rdp"] * 1e4 for r in keep])}


syms = sorted({r["symbol"] for r in rows})
per = {s: [r for r in rows if r["symbol"] == s] for s in syms}
tab = {}
for s in syms:
    d = cell(per[s])
    d["symbol"] = s
    d["by_month"] = {m: cell([r for r in per[s] if r["month"] == m]) for m in sorted(H.MONTHS)}
    d["hour_aware"] = cell(per[s], "cost_true_hour")
    tab[s] = d
out["per_symbol"] = tab


def frontier(order, name, cost_key="cost_true", eval_rows=None, label_extra=None):
    ev = eval_rows if eval_rows is not None else rows
    ntot = len(ev)
    kept, fr = [], []
    for s in order:
        kept.append(s)
        ks = set(kept)
        sub = [r for r in ev if r["symbol"] in ks]
        d = cell(sub, cost_key)
        if d is None:
            continue
        d["k"] = len(kept)
        d["added"] = s
        d["keep_rate"] = len(sub) / ntot
        d["net_bps_per_opportunity"] = d["net_bps"] * d["keep_rate"]
        d["net_r_per_opportunity"] = d["net_r"] * d["keep_rate"]
        d["kept"] = list(kept)
        fr.append(d)
    return {"name": name, "order": list(order), "frontier": fr,
            "note": label_extra}


# ---- EX ANTE: cheapest toll first
ex = sorted(syms, key=lambda s: tab[s]["toll_bps"])
out["frontier_exante_cheapest_toll"] = frontier(
    ex, "EX ANTE: cheapest broker-true toll first",
    label_extra="uses no outcome information")

# ---- IN SAMPLE: best net first
ins = sorted(syms, key=lambda s: -tab[s]["net_bps"])
out["frontier_insample_best_net"] = frontier(
    ins, "IN SAMPLE: best realised net bps first",
    label_extra="SELECTION ON THE ANSWER -- a ceiling, not a rule")

# ---- IN SAMPLE: best edge:toll first
ratio = sorted(syms, key=lambda s: -(tab[s]["edge_over_toll"] or -9))
out["frontier_insample_best_ratio"] = frontier(
    ratio, "IN SAMPLE: best edge:toll first",
    label_extra="SELECTION ON THE ANSWER")

# ---- TRAIN JAN / TEST FEB+MAR
jan = [r for r in rows if r["month"] == "2026-01"]
fm = [r for r in rows if r["month"] != "2026-01"]
jt = {}
for s in syms:
    c = cell([r for r in jan if r["symbol"] == s])
    if c:
        jt[s] = c
tr_net = sorted(jt, key=lambda s: -jt[s]["net_bps"])
tr_cost = sorted(jt, key=lambda s: jt[s]["toll_bps"])
out["train_jan_stats"] = jt
out["frontier_trainjan_net_testfebmar"] = frontier(
    tr_net, "TRAIN Jan by net -> TEST Feb+Mar", eval_rows=fm,
    label_extra="honest out-of-sample read of an in-sample instrument choice")
out["frontier_trainjan_cost_testfebmar"] = frontier(
    tr_cost, "TRAIN Jan by toll -> TEST Feb+Mar", eval_rows=fm,
    label_extra="cost ranking is near-deterministic, so this is close to the ex-ante arm")

# ---- rank stability of cost and of net across months
import itertools  # noqa: E402


def spear(a, b):
    ks = sorted(set(a) & set(b))
    ra = {k: i for i, k in enumerate(sorted(ks, key=lambda k: a[k]))}
    rb = {k: i for i, k in enumerate(sorted(ks, key=lambda k: b[k]))}
    n = len(ks)
    return 1 - 6 * sum((ra[k] - rb[k]) ** 2 for k in ks) / (n * (n * n - 1))


mm = sorted(H.MONTHS)
cost_m = {m: {s: tab[s]["by_month"][m]["toll_bps"] for s in syms if tab[s]["by_month"][m]} for m in mm}
net_m = {m: {s: tab[s]["by_month"][m]["net_bps"] for s in syms if tab[s]["by_month"][m]} for m in mm}
edge_m = {m: {s: tab[s]["by_month"][m]["edge_bps"] for s in syms if tab[s]["by_month"][m]} for m in mm}
out["rank_stability"] = {
    "toll": {f"{a}|{b}": spear(cost_m[a], cost_m[b]) for a, b in itertools.combinations(mm, 2)},
    "net": {f"{a}|{b}": spear(net_m[a], net_m[b]) for a, b in itertools.combinations(mm, 2)},
    "edge": {f"{a}|{b}": spear(edge_m[a], edge_m[b]) for a, b in itertools.combinations(mm, 2)}}

# ---- the affordability census
aff = [{"symbol": s, "edge_bps": tab[s]["edge_bps"], "toll_bps": tab[s]["toll_bps"],
        "ratio": tab[s]["edge_over_toll"], "n": tab[s]["n"],
        "net_bps": tab[s]["net_bps"], "net_r": tab[s]["net_r"],
        "months_net_positive": sum(1 for m in mm if tab[s]["by_month"][m]
                                   and tab[s]["by_month"][m]["net_bps"] > 0),
        "months_edge_positive": sum(1 for m in mm if tab[s]["by_month"][m]
                                    and tab[s]["by_month"][m]["edge_bps"] > 0)}
       for s in syms]
aff.sort(key=lambda d: -(d["ratio"] or -9))
out["affordability_census"] = aff
out["n_ratio_ge_1"] = sum(1 for d in aff if d["ratio"] and d["ratio"] >= 1)
out["n_net_positive"] = sum(1 for d in aff if d["net_bps"] > 0)

p = H.dump(out, "H3_INSTRUMENTS_V1.json")
print("%-12s %5s %8s %8s %8s %7s %8s %4s %4s" %
      ("symbol", "n", "edge", "toll", "net", "e/t", "net_r", "m+", "e+"))
for d in aff:
    print("%-12s %5d %8.4f %8.4f %8.4f %7.3f %8.5f %4d %4d" %
          (d["symbol"], d["n"], d["edge_bps"], d["toll_bps"], d["net_bps"],
           d["ratio"] or 0, d["net_r"], d["months_net_positive"], d["months_edge_positive"]))
for key in ("frontier_exante_cheapest_toll", "frontier_insample_best_net",
            "frontier_trainjan_net_testfebmar"):
    print("\n" + out[key]["name"])
    print("%3s %-12s %6s %6s %8s %8s %8s %7s %10s" %
          ("k", "added", "n", "keep", "edge", "toll", "net", "e/t", "net/opp"))
    for d in out[key]["frontier"]:
        print("%3d %-12s %6d %6.3f %8.4f %8.4f %8.4f %7.3f %10.5f" %
              (d["k"], d["added"], d["n"], d["keep_rate"], d["edge_bps"], d["toll_bps"],
               d["net_bps"], d["edge_over_toll"] or 0, d["net_bps_per_opportunity"]))
print("\nrank stability", json.dumps(out["rank_stability"], indent=1))
print("->", p)
