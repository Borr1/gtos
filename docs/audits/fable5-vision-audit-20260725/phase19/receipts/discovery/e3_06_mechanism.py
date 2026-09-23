"""e3 step 6 -- WHAT IS THE PASSIVITY AXIS ACTUALLY MADE OF?

dist_r = |entry - market| / |entry - stop|. A large dist_r can mean a FAR ENTRY or a
TIGHT STOP, and those are different findings with different repairs. The fill-probability
formula mixes them: risk_component uses |entry-market|/unit_risk, atr_component uses
|entry-market|/ATR. This decomposes them and asks which limb carries the gradient.
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
for r in tk:
    ep = r.get("entry_price") or 0
    rd = r.get("risk_distance") or 0
    a = r.get("atr14_m1")
    dr = max(0.0, r.get("dist_r") or 0.0)
    r["risk_pct"] = 100.0 * rd / ep if ep else None
    r["gap_pct"] = 100.0 * dr * rd / ep if ep else None
    r["risk_atr"] = (rd / a) if a else None
    r["gap_atr"] = (dr * rd / a) if a else None
OUT = {"n_takeable": len(tk), "months": MONTHS}


def qcut(sub, field, q=5):
    vals = sorted((r[field] for r in sub if r.get(field) is not None))
    if len(vals) < q * 20:
        return None
    edges = [vals[int(i * len(vals) / q)] for i in range(1, q)]
    def which(r):
        v = r.get(field)
        if v is None:
            return None
        i = 0
        while i < len(edges) and v >= edges[i]:
            i += 1
        return i
    return which, edges


def ladder(sub, field, label, q=5):
    w = qcut(sub, field, q)
    if not w:
        return
    which, edges = w
    d = collections.defaultdict(list)
    for r in sub:
        k = which(r)
        if k is not None:
            d[k].append(r)
    t = {}
    for k in sorted(d):
        v = d[k]
        s = E.stats([r["fill_honest_walk_r"] for r in v])
        res = [r for r in v if r["fill_honest_which_came_first"] in ("stop", "target")]
        t[f"Q{k+1}"] = {"n": s["n"], "honest": s["mean"], "t": s["t"], "zn": E.mean([E.hz(r) for r in v]),
                        "resolved_n": len(res), "resolved_mean": E.mean([r["fill_honest_walk_r"] for r in res]),
                        "resolved_win": (sum(1 for r in res if r["fill_honest_which_came_first"] == "target") / len(res)) if res else None,
                        "mean_field": E.mean([r.get(field) for r in v]),
                        "mean_dist_r": E.mean([max(0.0, r.get("dist_r") or 0) for r in v]),
                        "mean_risk_pct": E.mean([r.get("risk_pct") for r in v]),
                        "mean_cost_r": E.mean([r.get("cost_r") for r in v])}
    OUT.setdefault("ladders", {})[label] = {"edges": edges, "table": t}


ladder(tk, "dist_r", "dist_r")
ladder(tk, "risk_pct", "risk_pct")
ladder(tk, "gap_pct", "gap_pct")
ladder(tk, "risk_atr", "risk_atr")
ladder(tk, "gap_atr", "gap_atr")
ladder(tk, "cost_r", "cost_r")

# ------------------------------------------------------------- 2-way: does the passivity
# gradient survive INSIDE a risk-width stratum, and vice versa?
def twoway(a_field, b_field, label, q=4):
    wa = qcut(tk, a_field, q); wb = qcut(tk, b_field, q)
    if not wa or not wb:
        return
    d = collections.defaultdict(list)
    for r in tk:
        ka = wa[0](r); kb = wb[0](r)
        if ka is None or kb is None:
            continue
        d[(ka, kb)].append(r)
    t = {}
    for (ka, kb), v in sorted(d.items()):
        s = E.stats([r["fill_honest_walk_r"] for r in v])
        t[f"A{ka+1}_B{kb+1}"] = {"n": s["n"], "honest": s["mean"], "zn": E.mean([E.hz(r) for r in v])}
    # marginal gradients: within each b stratum, top-a minus bottom-a
    marg = {}
    for kb in range(q):
        lo = d.get((0, kb), []); hi = d.get((q - 1, kb), [])
        if lo and hi:
            sa = E.stats([r["fill_honest_walk_r"] for r in hi]); sb = E.stats([r["fill_honest_walk_r"] for r in lo])
            sd = ((sa["se"] or 0) ** 2 + (sb["se"] or 0) ** 2) ** 0.5
            marg[f"B{kb+1}"] = {"n_hi": sa["n"], "n_lo": sb["n"], "hi": sa["mean"], "lo": sb["mean"],
                                "delta_topA_minus_botA": sa["mean"] - sb["mean"],
                                "t": (sa["mean"] - sb["mean"]) / sd if sd else None}
    OUT.setdefault("twoway", {})[label] = {"cells": t, "within_B_gradient_of_A": marg}


twoway("dist_r", "risk_pct", "dist_r_within_risk_pct")
twoway("risk_pct", "dist_r", "risk_pct_within_dist_r")
twoway("gap_atr", "risk_pct", "gap_atr_within_risk_pct")

json.dump(OUT, open(os.path.join(D, "E3_MECHANISM_V1.json"), "w"), indent=1, default=str)

for lab, blk in OUT["ladders"].items():
    print("==", lab, "edges", [round(e, 5) for e in blk["edges"]])
    print(f"{'Q':>4} {'n':>6} {'honest':>8} {'t':>6} {'zn':>8} {'resN':>6} {'resMean':>8} {'resWin%':>7} {'field':>10} {'distR':>7} {'riskPct':>8} {'costR':>7}")
    for k, v in blk["table"].items():
        print(f"{k:>4} {v['n']:>6} {v['honest']:>+8.4f} {(v['t'] or 0):>+6.2f} {v['zn']:>+8.4f} {v['resolved_n']:>6} "
              f"{(v['resolved_mean'] or 0):>+8.4f} {100*(v['resolved_win'] or 0):>7.1f} {(v['mean_field'] or 0):>10.4f} "
              f"{(v['mean_dist_r'] or 0):>7.3f} {(v['mean_risk_pct'] or 0):>8.4f} {(v['mean_cost_r'] or 0):>7.4f}")
for lab, blk in OUT["twoway"].items():
    print("== 2WAY", lab)
    for k, v in blk["within_B_gradient_of_A"].items():
        print(f"   {k} n_hi {v['n_hi']:>5} n_lo {v['n_lo']:>5} hi {v['hi']:+.4f} lo {v['lo']:+.4f} "
              f"delta {v['delta_topA_minus_botA']:+.4f} t {(v['t'] or 0):+.2f}")
