"""p1 step 7 — DO THE *USAGE* LEVERS PERSIST WHERE THE SIGNAL CELLS DO NOT?

d2 published, per window, the full 12-contract exit menu and the 15-offset entry-instant
sweep on the identical at-market population.  Those are usage axes, not signal cells.
Run the same rank-persistence test on them, and on d2's gate grid.
"""
from __future__ import annotations
import numpy as np, json, itertools, sys
sys.path.insert(0, "/tmp/p1")
import p1_lib as L
D = ("/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/"
     "docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery")
MON = ["202510", "202511", "202512", "202601", "202602", "202603", "202604", "202605"]
J = {m: json.load(open(f"{D}/D2_{m}_V1.json")) for m in MON}

def axis(getter, label):
    per = {}
    for m in MON:
        try: per[m] = getter(J[m])
        except Exception as e: print("skip", m, label, e); continue
    keys = sorted(set.intersection(*[set(v) for v in per.values()]))
    rows = {k: [per[m][k] for m in MON] for k in keys}
    def rk(field):
        cor = []
        for a, b in itertools.combinations(MON, 2):
            va = np.array([per[a][k][field] for k in keys], float)
            vb = np.array([per[b][k][field] for k in keys], float)
            cor.append(L.spearman(va, vb))
        return dict(mean=float(np.nanmean(cor)), min=float(np.nanmin(cor)),
                    max=float(np.nanmax(cor)), n_pairs=len(cor))
    pooled = {k: {f: float(np.average([per[m][k][f] for m in MON],
                                      weights=[per[m][k]["n"] for m in MON]))
                  for f in ("gross", "cost", "net")} for k in keys}
    best = max(keys, key=lambda k: pooled[k]["net"])
    # how often is the pooled-best cell the per-month best?
    hits = sum(1 for m in MON if max(keys, key=lambda k: per[m][k]["net"]) == best)
    # per-month rank of the pooled-best cell
    ranks = []
    for m in MON:
        order = sorted(keys, key=lambda k: -per[m][k]["net"])
        ranks.append(order.index(best) + 1)
    return dict(label=label, k=len(keys), best_pooled=best, pooled=pooled,
                rank_persistence={f: rk(f) for f in ("gross", "cost", "net")},
                best_is_month_best=hits, best_rank_by_month=ranks,
                per_month={m: per[m] for m in MON})

def g_exit(d):
    o = {}
    for k, v in d["LAYER_D_EXIT"]["each_fixed_contract"].items():
        o[k] = dict(n=v["n"], gross=v["gross"], cost=v["cost"], net=v["net"])
    return o

def g_entry(d):
    o = {}
    for k, v in d["LAYER_C_TIMING"]["FEASIBLE_fixed_offset"].items():
        o[str(k)] = dict(n=v["n"], gross=v["gross"], cost=v["cost"], net=v["net"])
    return o

def g_gate(d):
    o = {}
    for k, v in d["LAYER_A_FEASIBLE_GRID"].items():
        if v.get("n", 0) >= 200:
            o[k] = dict(n=v["n"], gross=v["gross"], cost=v["cost"], net=v["net"])
    return o

OUT = {}
for name, fn in (("EXIT_CONTRACT", g_exit), ("ENTRY_OFFSET", g_entry), ("GATE_GRID", g_gate)):
    try:
        r = axis(fn, name); OUT[name] = r
    except Exception as e:
        print("FAIL", name, e); continue
    rp = r["rank_persistence"]
    print(f"{name:14s} k={r['k']:4d}  RANK PERSISTENCE  net {rp['net']['mean']:+.4f} "
          f"[{rp['net']['min']:+.3f},{rp['net']['max']:+.3f}]  gross {rp['gross']['mean']:+.4f} "
          f"cost {rp['cost']['mean']:+.4f} | pooled best = {r['best_pooled']} "
          f"(is month-best in {r['best_is_month_best']}/8; per-month rank {r['best_rank_by_month']})", flush=True)
json.dump(OUT, open("/tmp/p1/P1_USAGE_V1.json", "w"))
print("WROTE /tmp/p1/P1_USAGE_V1.json")
