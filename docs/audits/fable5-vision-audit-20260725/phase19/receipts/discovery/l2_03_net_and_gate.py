"""l2 step 3 — the sweep in NET R, with the cost model handled term by term, plus the
cost-gate interaction and the exit-reason decomposition.

Why this matters: every cost term except the flat slippage allowance is denominated in PRICE,
so in the new risk unit it divides by k exactly as the P&L does:
    cost_new(k) = (spread_r + commission_r + swap_cost_r)/k + expected_slippage_r
(expected_slippage_r is a flat 0.02 R constant -- w0 dictionary D8 -- so it does NOT divide.)
Three cost regimes: FROZEN (as charged), SPREAD/7.3 and SPREAD/8.5 (the measured over-charge band).

Also measured: the cost gate is R-denominated (spread_r > 0.10 OR total_cost_r > 0.15,
broker_net_cost_engine.py:859-866 / :923-927), so widening the stop moves candidates THROUGH the
gate.  That is a selection effect and it is measured separately from the scaling effect.
Writes L2_NET_GATE_V1.json
"""
import sys, os, json, gzip
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
import w0_ws

KS = [0.25, 0.4, 0.5, 0.6, 0.7, 0.75, 0.8, 0.9, 1.0, 1.1, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0]
OUT = os.path.join(D, "L2_NET_GATE_V1.json")


def mean(v):
    v = [x for x in v if x is not None]
    return round(sum(v) / len(v), 6) if v else None


rows = w0_ws.load()
byk = {w0_ws.key(r): r for r in rows}
sw = {}
with gzip.open(os.path.join(D, "l2_SWEEP_ROWS_V1.jsonl.gz"), "rt") as f:
    for ln in f:
        e = json.loads(ln)
        sw[(e["cid"], e["dt"])] = e

pop = []
for k, e in sw.items():
    if e["A"] is None:
        continue
    if e["m"] is not None and e["m"] <= -1.0:
        continue                      # born_past_stop, never takeable
    r = byk[k]
    pop.append({"A": e["A"], "fam": e["fam"], "sym": e["sym"], "sess": e["sess"],
                "sp": r.get("spread_r") or 0.0, "cm": r.get("commission_r") or 0.0,
                "sw": r.get("swap_cost_r") or 0.0, "sl": r.get("expected_slippage_r") or 0.0,
                "cost": r.get("expected_cost_r") or 0.0})
N = len(pop)
res = {"n": N, "cost_model": "cost_new(k) = (spread_r+commission_r+swap_cost_r)/k + expected_slippage_r",
       "gate": "spread_r/k > 0.10 OR total_cost_r(k) > 0.15  ->  refused"}

res["cost_terms_mean_at_k1"] = {"spread_r": mean([p["sp"] for p in pop]),
                                "commission_r": mean([p["cm"] for p in pop]),
                                "swap_cost_r": mean([p["sw"] for p in pop]),
                                "expected_slippage_r": mean([p["sl"] for p in pop]),
                                "expected_cost_r": mean([p["cost"] for p in pop])}


def cost_at(p, kk, spread_div=1.0):
    sp = p["sp"] / spread_div
    return (sp + p["cm"] + p["sw"]) / kk + p["sl"]


tab = []
for ix, kk in enumerate(KS):
    g = [p["A"][ix][0] for p in pop]
    row = {"k": kk, "gross_newunit": mean(g), "gross_oldunit": round(mean(g) * kk, 6)}
    for lab, dv in (("frozen", 1.0), ("spread_div_7p3", 7.3), ("spread_div_8p5", 8.5)):
        c = [cost_at(p, kk, dv) for p in pop]
        net = [g[j] - c[j] for j in range(N)]
        row["cost_" + lab] = mean(c)
        row["net_" + lab] = mean(net)
    tab.append(row)
res["net_sweep_full_population"] = tab

# ---------------- gate interaction ----------------
gate = []
for ix, kk in enumerate(KS):
    for lab, dv in (("frozen", 1.0), ("spread_div_7p3", 7.3)):
        keep = []
        for p in pop:
            spk = (p["sp"] / dv) / kk
            tot = cost_at(p, kk, dv)
            if spk <= 0.10 and tot <= 0.15:
                keep.append(p)
        if not keep:
            gate.append({"k": kk, "regime": lab, "n_pass": 0}); continue
        gi = [p["A"][ix][0] for p in keep]
        ci = [cost_at(p, kk, dv) for p in keep]
        gate.append({"k": kk, "regime": lab, "n_pass": len(keep),
                     "pass_pct": round(100 * len(keep) / N, 3),
                     "gross_newunit_passers": mean(gi),
                     "gross_oldunit_passers": round(mean(gi) * kk, 6),
                     "cost_newunit_passers": mean(ci),
                     "net_newunit_passers": mean([gi[j] - ci[j] for j in range(len(keep))]),
                     "total_net_r": round(sum(gi[j] - ci[j] for j in range(len(keep))), 2)})
res["gate_interaction"] = gate

# ---------------- exit-reason decomposition at three k ----------------
dec = {}
for kk in (1.0, 2.0, 3.0):
    ix = KS.index(kk)
    by = {}
    for p in pop:
        r, ex = p["A"][ix]
        by.setdefault(ex, []).append(r)
    dec["k=%.1f" % kk] = {ex: {"n": len(v), "share_pct": round(100 * len(v) / N, 3),
                               "mean_r_newunit": mean(v),
                               "contribution_r_per_trade": round(sum(v) / N, 6)}
                          for ex, v in sorted(by.items())}
res["exit_decomposition"] = dec

with open(OUT, "w") as fh:
    json.dump(res, fh, indent=1)
print("wrote", OUT, "n", N)
print("costs@k1", res["cost_terms_mean_at_k1"])
for t in tab:
    print("k=%.2f gross_new=%+.5f gross_old=%+.5f | net_frozen=%+.5f net/7.3=%+.5f net/8.5=%+.5f"
          % (t["k"], t["gross_newunit"], t["gross_oldunit"], t["net_frozen"],
             t["net_spread_div_7p3"], t["net_spread_div_8p5"]))
print("--- gate ---")
for gr in gate:
    if gr.get("n_pass"):
        print("k=%.2f %-14s pass=%5d (%5.2f%%) gross_old=%+.5f net_new=%+.5f totR=%+9.1f"
              % (gr["k"], gr["regime"], gr["n_pass"], gr["pass_pct"], gr["gross_oldunit_passers"],
                 gr["net_newunit_passers"], gr["total_net_r"]))
