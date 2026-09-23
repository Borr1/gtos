"""p1 step 3 — THE FEE-SCHEDULE TEST, run as an honest out-of-sample cell selection.

For each cell partition and each selection axis (GROSS rank / COST rank / NET rank),
fit the cell ordering on the training months, keep the top q fraction of cells by that
axis, apply to the held-out month, and decompose the realised change against the
whole-population baseline of that same month:

        d_net = d_gross - d_cost

Two protocols, both reported:
  EXPANDING : train on windows 0..t-1, test on t   (t = 1..7)  -- strictly chronological
  LOMO      : train on the other 7, test on this one          -- maximum training data
"""
from __future__ import annotations
import numpy as np, json, sys
sys.path.insert(0, "/tmp/p1")
import p1_lib as L

ws, SYMS = L.load_all()
NW = len(ws)

def kk(w, kind):
    if kind == "instrument":    return w.sym.astype(np.int64)
    if kind == "family":        return w.fam.astype(np.int64)
    if kind == "broker_hour":   return w.bhour.astype(np.int64)
    if kind == "inst_x_family": return w.sym.astype(np.int64) * 100 + w.fam
    if kind == "inst_x_hour":   return w.sym.astype(np.int64) * 100 + w.bhour
    if kind == "inst_x_fam_x_hour": return (w.sym.astype(np.int64) * 10000
                                            + w.fam.astype(np.int64) * 100 + w.bhour)
    raise KeyError

POPS = {}
for w in ws:
    f = w.fil == 1
    POPS["ALL_FILLS"] = POPS.get("ALL_FILLS", []) + [f]
    POPS["CLEAN_FILLS"] = POPS.get("CLEAN_FILLS", []) + [f & (w.past == 0) & (w.fam != 1)]
    POPS["AT_MARKET"] = POPS.get("AT_MARKET", []) + [f & (w.atm == 1)]

KINDS = ["instrument", "family", "broker_hour", "inst_x_family", "inst_x_hour",
         "inst_x_fam_x_hour"]
QS = [0.50, 0.25, 0.10]
MINN = {"instrument": 50, "family": 50, "broker_hour": 50,
        "inst_x_family": 30, "inst_x_hour": 30, "inst_x_fam_x_hour": 20}

def train_means(idxs, kind, masks, minn):
    ks, gs, cs = [], [], []
    for i in idxs:
        w = ws[i]; m = masks[i]
        ks.append(kk(w, kind)[m]); gs.append(w.g[m]); cs.append(w.c[m])
    k = np.concatenate(ks); g = np.concatenate(gs); c = np.concatenate(cs)
    u, inv = np.unique(k, return_inverse=True)
    n = np.bincount(inv, minlength=len(u)).astype(float)
    mg = np.bincount(inv, weights=g, minlength=len(u)) / n
    mc = np.bincount(inv, weights=c, minlength=len(u)) / n
    ok = n >= minn
    return u[ok], mg[ok], mc[ok], n[ok]

def apply_test(t, kind, masks, keep):
    w = ws[t]; m = masks[t]
    k = kk(w, kind)[m]
    sel = np.isin(k, keep)
    g = w.g[m]; c = w.c[m]
    base = dict(n=int(m.sum()), gross=float(g.mean()), cost=float(c.mean()),
                net=float((g - c).mean()))
    if sel.sum() < 20:
        return base, None
    s = dict(n=int(sel.sum()), gross=float(g[sel].mean()), cost=float(c[sel].mean()),
             net=float((g[sel] - c[sel]).mean()), share=float(sel.mean()))
    s["d_gross"] = s["gross"] - base["gross"]
    s["d_cost"] = s["cost"] - base["cost"]
    s["d_net"] = s["net"] - base["net"]
    s["cost_share_of_d_net"] = (-s["d_cost"] / s["d_net"]) if s["d_net"] != 0 else float("nan")
    return base, s

OUT = {}
for pop, masks in POPS.items():
    OUT[pop] = {}
    for kind in KINDS:
        minn = MINN[kind]
        OUT[pop][kind] = {}
        for proto in ("EXPANDING", "LOMO"):
            for axis in ("gross", "cost", "net"):
                for q in QS:
                    rows = []
                    tests = range(1, NW) if proto == "EXPANDING" else range(NW)
                    for t in tests:
                        tr = list(range(t)) if proto == "EXPANDING" else [i for i in range(NW) if i != t]
                        u, mg, mc, n = train_means(tr, kind, masks, minn)
                        if len(u) < 4: continue
                        score = {"gross": mg, "cost": -mc, "net": mg - mc}[axis]
                        nk = max(2, int(round(q * len(u))))
                        keep = u[np.argsort(-score)[:nk]]
                        base, s = apply_test(t, kind, masks, keep)
                        if s is None: continue
                        rows.append({"test": ws[t].w, "base": base, "sel": s})
                    if not rows: continue
                    agg = {}
                    for f in ("d_gross", "d_cost", "d_net"):
                        agg[f] = float(np.mean([r["sel"][f] for r in rows]))
                    agg["pooled_net"] = float(np.average([r["sel"]["net"] for r in rows],
                                                         weights=[r["sel"]["n"] for r in rows]))
                    agg["pooled_base_net"] = float(np.average([r["base"]["net"] for r in rows],
                                                              weights=[r["base"]["n"] for r in rows]))
                    agg["months_dnet_pos"] = int(sum(1 for r in rows if r["sel"]["d_net"] > 0))
                    agg["months_dgross_pos"] = int(sum(1 for r in rows if r["sel"]["d_gross"] > 0))
                    agg["months"] = len(rows)
                    agg["cost_share_of_d_net"] = (-agg["d_cost"] / agg["d_net"]) if agg["d_net"] else float("nan")
                    agg["net_positive_absolute"] = bool(agg["pooled_net"] > 0)
                    OUT[pop][kind][f"{proto}|{axis}|q{q:.2f}"] = {"agg": agg, "rows": rows}
        for key, v in OUT[pop][kind].items():
            if "LOMO" not in key: continue
            a = v["agg"]
            print(f"{pop:11s} {kind:18s} {key:22s} dgross {a['d_gross']:+.5f} "
                  f"dcost {a['d_cost']:+.5f} dnet {a['d_net']:+.5f} "
                  f"[gross+ {a['months_dgross_pos']}/{a['months']}] "
                  f"cost_share {a['cost_share_of_d_net']:+.2f} netabs {a['pooled_net']:+.5f}", flush=True)

json.dump(OUT, open("/tmp/p1/P1_OOS_V1.json", "w"))
print("WROTE /tmp/p1/P1_OOS_V1.json")
