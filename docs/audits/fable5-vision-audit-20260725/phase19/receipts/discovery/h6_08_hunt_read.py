"""h6 step 8 — read the hunt: where is edge:cost above 1, at what n, with what caveat."""
import gzip, json, os, sys
from collections import defaultdict

D = os.path.dirname(os.path.abspath(__file__))
rows = [json.loads(x) for x in gzip.open(f"{D}/h6_HUNT_V1.jsonl.gz", "rt") if x.strip()]
print("cells", len(rows), flush=True)

out = {"cells_searched": len(rows)}


def tab(rs, kf, n, title, cols=("sym", "k", "trail", "target", "maxbars", "band",
                               "gk", "gv", "n", "gross", "cost", "net", "tn", "rr",
                               "rb", "trunc", "months_pos", "totR")):
    rs = sorted(rs, key=kf, reverse=True)[:n]
    print("\n===", title, f"({len(rs)} shown)")
    print("  ".join(f"{c:>9}" for c in cols))
    for r in rs:
        print("  ".join(f"{str(r.get(c)):>9}" for c in cols))
    return rs


# --- census of ratio > 1
for key, lab in (("rr", "ratio_R"), ("rb", "ratio_bps")):
    for nmin in (40, 100, 300, 1000):
        sub = [r for r in rows if r["n"] >= nmin and (r.get(key) or 0) > 1]
        allc = [r for r in rows if r["n"] >= nmin]
        out.setdefault("census", {})[f"{lab}_gt1_n>={nmin}"] = {
            "cells": len(sub), "of": len(allc),
            "share": round(len(sub) / len(allc), 5) if allc else None,
            "pooled_ALL_cells": len([r for r in sub if r["sym"] == "ALL"])}
print(json.dumps(out["census"], indent=1))

# --- ALL-instrument (pooled) cells that pay
pool = [r for r in rows if r["sym"] == "ALL"]
out["pooled_cells"] = len(pool)
best_pool_rr = tab([r for r in pool if r["n"] >= 300], lambda r: r.get("rr") or -9, 20,
                   "POOLED cells, n>=300, ranked by ratio_R")
out["top_pooled_ratio_R_n300"] = best_pool_rr
best_pool_net = tab([r for r in pool if r["n"] >= 1000], lambda r: r["net"], 20,
                    "POOLED cells, n>=1000, ranked by NET R/trade")
out["top_pooled_net_n1000"] = best_pool_net

# --- per-instrument cells that pay, robust filter
robust = [r for r in rows if r["sym"] != "ALL" and r["n"] >= 150
          and r["months_pos"] == 3 and (r.get("rr") or 0) > 1]
out["robust_instrument_cells"] = len(robust)
tab(robust, lambda r: r["net"], 30,
    "PER-INSTRUMENT cells: n>=150, ALL 3 months net-positive, ratio_R>1, by net")
out["top_robust_instrument_cells"] = sorted(robust, key=lambda r: -r["net"])[:60]

# --- which instruments ever produce a robust paying cell
bysym = defaultdict(list)
for r in robust:
    bysym[r["sym"]].append(r)
out["instruments_with_robust_paying_cells"] = {
    s: {"cells": len(v), "best_net": max(x["net"] for x in v),
        "best_rr": max(x.get("rr") or 0 for x in v),
        "max_n": max(x["n"] for x in v)} for s, v in sorted(bysym.items())}
print("\n=== instruments with >=1 robust paying cell ===")
for s, v in out["instruments_with_robust_paying_cells"].items():
    print(f"{s:<12} cells {v['cells']:>4}  best_net {v['best_net']:+.5f}  "
          f"best_rr {v['best_rr']:.2f}  max_n {v['max_n']}")

# --- the ungated-instrument question: which symbols pay with NO cost gate at all
nog = [r for r in rows if r["sym"] != "ALL" and r["gv"] is None and r["band"] == "none"]
bysym2 = defaultdict(list)
for r in nog:
    bysym2[r["sym"]].append(r)
out["no_gate_best_per_symbol"] = {}
print("\n=== best contract per instrument with NO cost gate, no band (n = full cohort) ===")
print(f"{'sym':<12}{'k':>4}{'trail':>7}{'tgt':>5}{'mb':>5}{'n':>6}{'gross':>9}{'cost':>8}"
      f"{'net':>9}{'tn':>7}{'rr':>7}{'rb':>7}{'mo+':>5}{'trunc':>7}")
for s, v in sorted(bysym2.items()):
    b = max(v, key=lambda r: r["net"])
    out["no_gate_best_per_symbol"][s] = b
    print(f"{s:<12}{b['k']:>4}{str(b['trail']):>7}{str(b['target']):>5}{str(b['maxbars']):>5}"
          f"{b['n']:>6}{b['gross']:>9.4f}{b['cost']:>8.4f}{b['net']:>9.5f}"
          f"{(b['tn'] or 0):>7.2f}{(b['rr'] or 0):>7.2f}{(b['rb'] or 0):>7.2f}"
          f"{b['months_pos']:>5}{b['trunc']:>7.3f}")

json.dump(out, open(f"{D}/H6_HUNT_TOP_V1.json", "w"), indent=1)
print("\nwrote H6_HUNT_TOP_V1.json")
