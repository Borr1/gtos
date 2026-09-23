"""e3 step 7 -- the cost gate x passivity interaction, and the fine resting ladder.

L9 sec 4.5 claims the cost gate is pointed at the same population backwards. But the raw
cost_r ladder says expensive candidates ARE worse. Both can be true only if the two axes
are entangled. This measures each inside the other.
"""
import collections, gzip, json, os, sys
D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import e3_lib as E

MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY"]
rows = []
for m in MONTHS:
    for l in gzip.open(os.path.join(D, f"e3_slim_{m}.jsonl.gz"), "rt"):
        r = json.loads(l)
        r["month"] = m
        rows.append(r)
tk = [r for r in rows if r["takeable"]]
OUT = {"n_takeable": len(tk)}

DBANDS = [(-1e18, 0.0, "A_marketable_or_at"), (0.0, 0.35, "B_0-0.35"), (0.35, 0.75, "C_0.35-0.75"),
          (0.75, 1.4175, "D_0.75-1.42"), (1.4175, 3.0, "E_1.42-3.0"), (3.0, 1e18, "F_>=3.0")]


def dband(r):
    v = r.get("dist_r")
    if v is None:
        return "null"
    for lo, hi, lab in DBANDS:
        if lo < v <= hi or (lab.startswith("A") and v <= 0):
            return lab
    return "F_>=3.0"


CBANDS = [0.05, 0.10, 0.15, 0.25, 0.50, 1.0]


def cband(r):
    v = r.get("cost_r")
    if v is None:
        return "null"
    for c in CBANDS:
        if v <= c:
            return f"c<={c}"
    return "c>1.0"


def cell(v):
    s = E.stats([r["fill_honest_walk_r"] for r in v])
    res = [r for r in v if r["fill_honest_which_came_first"] in ("stop", "target")]
    return {"n": s["n"], "honest": s["mean"], "t": s["t"], "zn": E.mean([E.hz(r) for r in v]),
            "resolved_n": len(res), "resolved_mean": E.mean([r["fill_honest_walk_r"] for r in res]),
            "resolved_win": (sum(1 for r in res if r["fill_honest_which_came_first"] == "target") / len(res)) if res else None,
            "mean_cost_r": E.mean([r.get("cost_r") for r in v]),
            "mean_dist_r": E.mean([r.get("dist_r") for r in v]),
            "mean_risk_pct": E.mean([100.0 * (r.get("risk_distance") or 0) / (r.get("entry_price") or 1) for r in v]),
            "net_at_spread_div_7p3": E.mean([r["fill_honest_walk_r"] - ((r.get("cost_r") or 0) - (r.get("spread_r") or 0) * (1 - 1 / 7.3)) for r in v])}


# fine dist ladder, pooled + per month
OUT["dist_ladder_pooled"] = {lab: cell(v) for lab, v in
                             sorted(collections.Counter and {k: [r for r in tk if dband(r) == k]
                                                             for k in {dband(r) for r in tk}}.items())}
for m in MONTHS:
    sub = [r for r in tk if r["month"] == m]
    OUT.setdefault("dist_ladder_by_month", {})[m] = {k: cell([r for r in sub if dband(r) == k])
                                                     for k in sorted({dband(r) for r in sub})}
# resting only
res = [r for r in tk if r["born_state"] == "resting"]
OUT["dist_ladder_resting_pooled"] = {k: cell([r for r in res if dband(r) == k])
                                     for k in sorted({dband(r) for r in res})}

# 2-way dist x cost
two = collections.defaultdict(list)
for r in tk:
    two[(dband(r), cband(r))].append(r)
OUT["twoway_dist_x_cost"] = {f"{a}|{b}": cell(v) for (a, b), v in sorted(two.items()) if len(v) >= 80}
# marginal: cost gradient inside each dist band; dist gradient inside each cost band
mg = {}
for db in sorted({dband(r) for r in tk}):
    sub = [r for r in tk if dband(r) == db]
    lo = [r for r in sub if (r.get("cost_r") or 0) <= 0.15]
    hi = [r for r in sub if (r.get("cost_r") or 0) > 0.15]
    if len(lo) >= 40 and len(hi) >= 40:
        a = E.stats([r["fill_honest_walk_r"] for r in lo]); b = E.stats([r["fill_honest_walk_r"] for r in hi])
        sd = ((a["se"] or 0) ** 2 + (b["se"] or 0) ** 2) ** 0.5
        mg[db] = {"n_cheap": a["n"], "cheap": a["mean"], "n_exp": b["n"], "exp": b["mean"],
                  "cost_gate_delta": a["mean"] - b["mean"], "t": (a["mean"] - b["mean"]) / sd if sd else None}
OUT["cost_gate_inside_dist_band"] = mg
mg2 = {}
for cb in sorted({cband(r) for r in tk}):
    sub = [r for r in tk if cband(r) == cb]
    lo = [r for r in sub if (r.get("dist_r") or -9) >= 1.4175]
    hi = [r for r in sub if (r.get("dist_r") or -9) < 1.4175]
    if len(lo) >= 40 and len(hi) >= 40:
        a = E.stats([r["fill_honest_walk_r"] for r in lo]); b = E.stats([r["fill_honest_walk_r"] for r in hi])
        sd = ((a["se"] or 0) ** 2 + (b["se"] or 0) ** 2) ** 0.5
        mg2[cb] = {"n_far": a["n"], "far": a["mean"], "n_near": b["n"], "near": b["mean"],
                   "passivity_delta": a["mean"] - b["mean"], "t": (a["mean"] - b["mean"]) / sd if sd else None}
OUT["passivity_inside_cost_band"] = mg2

# what the SHIPPED gate stack actually deletes, jointly
gate_pass = [r for r in tk if (r.get("cost_r") or 9) <= 0.15
             and (r.get("execution_fill_probability") if r.get("execution_fill_probability") is not None
                  else r.get("fp_hat_m1atr") or 9) >= 0.45]
gate_fail = [r for r in tk if r not in ()]  # placeholder replaced below
gp = set(id(r) for r in gate_pass)
gate_fail = [r for r in tk if id(r) not in gp]
OUT["shipped_gate_stack"] = {"pass": cell(gate_pass), "fail": cell(gate_fail)}

json.dump(OUT, open(os.path.join(D, "E3_COSTINTER_V1.json"), "w"), indent=1, default=str)

print("== dist ladder pooled")
print(f"{'band':>20} {'n':>6} {'honest':>8} {'t':>6} {'zn':>8} {'resN':>6} {'resMean':>8} {'resWin%':>7} {'costR':>7} {'riskPct':>8} {'net/7.3':>8}")
for k, v in OUT["dist_ladder_pooled"].items():
    print(f"{k:>20} {v['n']:>6} {v['honest']:>+8.4f} {(v['t'] or 0):>+6.2f} {v['zn']:>+8.4f} {v['resolved_n']:>6} "
          f"{(v['resolved_mean'] or 0):>+8.4f} {100*(v['resolved_win'] or 0):>7.1f} {(v['mean_cost_r'] or 0):>7.4f} "
          f"{(v['mean_risk_pct'] or 0):>8.4f} {v['net_at_spread_div_7p3']:>+8.4f}")
print("== dist ladder by month (honest)")
for m in MONTHS:
    print("  ", m, {k: (v["n"], round(v["honest"], 4)) for k, v in OUT["dist_ladder_by_month"][m].items()})
print("== cost gate INSIDE each dist band (cheap<=0.15 minus expensive)")
for k, v in OUT["cost_gate_inside_dist_band"].items():
    print(f"   {k:>20} n {v['n_cheap']:>5}/{v['n_exp']:<6} cheap {v['cheap']:+.4f} exp {v['exp']:+.4f} delta {v['cost_gate_delta']:+.4f} t {(v['t'] or 0):+.2f}")
print("== passivity INSIDE each cost band (far>=1.4175 minus near)")
for k, v in OUT["passivity_inside_cost_band"].items():
    print(f"   {k:>20} n {v['n_far']:>5}/{v['n_near']:<6} far {v['far']:+.4f} near {v['near']:+.4f} delta {v['passivity_delta']:+.4f} t {(v['t'] or 0):+.2f}")
print("== shipped gate stack:", {k: (v["n"], round(v["honest"], 4), round(v["zn"], 4), round(v["net_at_spread_div_7p3"], 4))
                                 for k, v in OUT["shipped_gate_stack"].items()})
