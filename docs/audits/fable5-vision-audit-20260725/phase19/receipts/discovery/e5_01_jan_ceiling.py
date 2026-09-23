"""e5 step 1 — the CEILING, measured rather than argued, on January.

L2-F6 asserts net_new(k) = (gross_price - cost_price)/(k*d) with BOTH numerator terms
k-invariant, hence a k-invariant sign and a ceiling of zero. That is an algebraic claim
resting on an empirical premise. This measures the premise directly:

  G(k) = mean price-space gross in ORIGINAL R units, over a fine k ladder up to k=inf
  C    = mean price-space cost in the same units (k-invariant by construction)

If max_k G(k) > C anywhere -- globally or in any cohort -- the ceiling is NOT zero there.
Writes E5_JAN_CEILING_V1.json
"""
import sys, os, json, gzip
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
import w0_ws, e5_lib

OUT = os.path.join(D, "E5_JAN_CEILING_V1.json")
KLADDER = [1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0, 6.0, 8.0, 10.0, 12.0,
           15.0, 20.0, 25.0, 30.0, 40.0, 50.0, 75.0, 100.0, e5_lib.INF_K]

rows = w0_ws.load()
byk = {w0_ws.key(r): r for r in rows}
anch = {}
with gzip.open(os.path.join(D, "w0cap2_DECISION_ANCHOR_V1.jsonl.gz"), "rt") as f:
    for ln in f:
        a = json.loads(ln)
        anch[(a["candidate_id"], a["decision_time_utc"])] = a

ents, st = e5_lib.build_entries(byk, w0_ws.iter_rpaths(), anch)
res = {"month": "january_2026", "build": st, "n": len(ents)}

for mode in ("A", "B"):
    res["ladder_" + mode] = [e5_lib.price_space(ents, k, mode) for k in KLADDER]

# reproduce the l2 rules through the new library (instrument check)
res["repro"] = {
    "baseline_k1": e5_lib.rule_eval(ents, lambda e: 1.0, "baseline k=1"),
    "S5": e5_lib.rule_eval(ents, lambda e: max(1.0, 5 * e["sp"]), "S(5)"),
    "S10": e5_lib.rule_eval(ents, lambda e: max(1.0, 10 * e["sp"]), "S(10)"),
    "S20": e5_lib.rule_eval(ents, lambda e: max(1.0, 20 * e["sp"]), "S(20)"),
    "k3": e5_lib.rule_eval(ents, lambda e: 3.0, "flat k=3"),
}


def cohort_ceiling(keyfn, label, min_n=100):
    groups = {}
    for e in ents:
        groups.setdefault(keyfn(e), []).append(e)
    out = {}
    for g, sub in groups.items():
        if g is None or len(sub) < min_n:
            continue
        best = None
        for mode in ("A", "B"):
            for k in KLADDER:
                p = e5_lib.price_space(sub, k, mode)
                if best is None or p["G_price"] > best["G_price"]:
                    best = dict(p); best["mode"] = mode
        base = e5_lib.price_space(sub, 1.0, "A")
        out[str(g)] = {
            "n": len(sub), "G_at_k1": base["G_price"],
            "best_G": best["G_price"], "best_k": best["k"], "best_mode": best["mode"],
            "C_frozen": base["C_frozen"], "C_sp73": base["C_sp73"], "C_sp85": base["C_sp85"],
            "ceiling_gap_frozen": round(best["G_price"] - base["C_frozen"], 6),
            "ceiling_gap_sp73": round(best["G_price"] - base["C_sp73"], 6),
            "ceiling_gap_sp85": round(best["G_price"] - base["C_sp85"], 6),
            "ceiling_gap_zerocost": round(best["G_price"], 6),
        }
    return {label: dict(sorted(out.items(), key=lambda kv: -kv[1]["ceiling_gap_sp73"]))}


res.update(cohort_ceiling(lambda e: e["fam"], "by_family"))
res.update(cohort_ceiling(lambda e: e["sym"], "by_symbol"))
res.update(cohort_ceiling(lambda e: e["sess"], "by_session"))
res.update(cohort_ceiling(lambda e: e["hour"], "by_hour"))
res.update(cohort_ceiling(lambda e: e["side"], "by_side"))

with open(OUT, "w") as fh:
    json.dump(res, fh, indent=1)

print("n", len(ents), "build", st)
print("%6s %10s %10s %9s %9s %8s %8s %8s" % ("k", "G_price", "gap/7.3", "stop%", "tgt%", "mark%", "win%", "netnew73"))
for p in res["ladder_A"]:
    print("%6s %+10.5f %+10.5f %9.2f %9.2f %8.2f %8.2f %+8.5f"
          % (p["k"] if p["k"] else "inf", p["G_price"], p["gap_sp73"], p["stop_pct"],
             p["target_pct"], p["mark_pct"], p["win_pct"], p["net_new_sp73"]))
print("--- convention B (target = 2k) ---")
for p in res["ladder_B"]:
    print("%6s %+10.5f %+10.5f %9.2f %9.2f %8.2f %8.2f %+8.5f"
          % (p["k"] if p["k"] else "inf", p["G_price"], p["gap_sp73"], p["stop_pct"],
             p["target_pct"], p["mark_pct"], p["win_pct"], p["net_new_sp73"]))
print("--- repro check ---")
for k, v in res["repro"].items():
    print("%-12s gross=%+.5f netFROZEN=%+.5f net73=%+.5f" % (k, v["gross_newunit"], v["net_frozen"], v["net_sp73"]))
print("wrote", OUT)
