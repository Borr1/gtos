"""p1 step 4 — IS THE GROSS-RANK PERSISTENCE REAL EDGE, OR THE STOP-WIDTH AXIS?

Selecting cells on train-fitted GROSS-in-R does lift OOS gross-in-R.  Two competing
explanations:
  (i)  a travelling directional edge ordering, or
  (ii) an artifact of the R metric -- R = price_move / d, so both gross-in-R and
       cost-in-R scale as 1/d, and 'high gross in R' is partly 'tight stop'.

Three tests that separate them:
  A. rank persistence of gross in PRICE units (bps) vs in R units, same cells.
  B. TOLL-NEUTRAL selection: regress train cell gross on train cell cost across
     cells, select on the RESIDUAL.  Real edge -> d_cost ~ 0 and d_net = d_gross > 0.
  C. RANDOM-cell null at the same selection share (200 draws) for every arm.
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
    POPS.setdefault("CLEAN_FILLS", []).append(f & (w.past == 0) & (w.fam != 1))
    POPS.setdefault("AT_MARKET", []).append(f & (w.atm == 1))

KINDS = ["instrument", "family", "broker_hour", "inst_x_family", "inst_x_hour",
         "inst_x_fam_x_hour"]
MINN = {"instrument": 50, "family": 50, "broker_hour": 50, "inst_x_family": 30,
        "inst_x_hour": 30, "inst_x_fam_x_hour": 20}
QS = [0.50, 0.25, 0.10]

# ---------- A. rank persistence, R units vs price units -----------------------
import itertools
A = {}
for pop, masks in POPS.items():
    A[pop] = {}
    for kind in KINDS:
        minn = MINN[kind]
        cells = []
        for w, m in zip(ws, masks):
            k = kk(w, kind)[m]
            gR = w.g[m]; cR = w.c[m]; d = w.d_bps[m]
            gB = gR * d; cB = cR * d
            u, inv = np.unique(k, return_inverse=True)
            n = np.bincount(inv, minlength=len(u)).astype(float)
            f = lambda x: np.bincount(inv, weights=x, minlength=len(u)) / n
            ok = n >= minn
            cells.append((u[ok], f(gR)[ok], f(cR)[ok], f(gB)[ok], f(cB)[ok]))
        acc = {"gR": [], "cR": [], "gB": [], "cB": []}
        for i, j in itertools.combinations(range(NW), 2):
            ui = cells[i][0]; uj = cells[j][0]
            com = np.intersect1d(ui, uj)
            if len(com) < 4: continue
            ai = np.searchsorted(ui, com); aj = np.searchsorted(uj, com)
            for t, idx in (("gR", 1), ("cR", 2), ("gB", 3), ("cB", 4)):
                acc[t].append(L.spearman(cells[i][idx][ai], cells[j][idx][aj]))
        A[pop][kind] = {t: float(np.nanmean(v)) for t, v in acc.items()}
        A[pop][kind]["k_jan"] = int(len(cells[3][0]))
        r = A[pop][kind]
        print(f"[A] {pop:11s} {kind:18s} k={r['k_jan']:4d}  gross_R {r['gR']:+.4f}  "
              f"gross_bps {r['gB']:+.4f}  cost_R {r['cR']:+.4f}  cost_bps {r['cB']:+.4f}", flush=True)

# ---------- B+C. toll-neutral selection, with a random-cell null ---------------
def run_axis(pop, masks, kind, axis, q, rng):
    minn = MINN[kind]
    rows = []
    for t in range(NW):
        tr = [i for i in range(NW) if i != t]
        ks, gs, cs = [], [], []
        for i in tr:
            m = masks[i]; ks.append(kk(ws[i], kind)[m]); gs.append(ws[i].g[m]); cs.append(ws[i].c[m])
        k = np.concatenate(ks); g = np.concatenate(gs); c = np.concatenate(cs)
        u, inv = np.unique(k, return_inverse=True)
        n = np.bincount(inv, minlength=len(u)).astype(float)
        mg = np.bincount(inv, weights=g, minlength=len(u)) / n
        mc = np.bincount(inv, weights=c, minlength=len(u)) / n
        ok = n >= minn
        u, mg, mc, n = u[ok], mg[ok], mc[ok], n[ok]
        if len(u) < 4: continue
        if axis == "gross":     score = mg
        elif axis == "cost":    score = -mc
        elif axis == "resid":
            X = np.vstack([np.ones_like(mc), mc, mc ** 2]).T
            beta, *_ = np.linalg.lstsq(X, mg, rcond=None)
            score = mg - X @ beta
        else: raise KeyError(axis)
        nk = max(2, int(round(q * len(u))))
        keep = u[np.argsort(-score)[:nk]]
        m = masks[t]; kt = kk(ws[t], kind)[m]
        sel = np.isin(kt, keep); g_t = ws[t].g[m]; c_t = ws[t].c[m]
        if sel.sum() < 20: continue
        base_g, base_c = g_t.mean(), c_t.mean()
        # random-cell null matched on selected-row share
        ut, invt = np.unique(kt, return_inverse=True)
        nt = np.bincount(invt, minlength=len(ut))
        tgt = sel.sum()
        nullg, nullc = [], []
        for _ in range(200):
            order = rng.permutation(len(ut)); tot = 0; pick = []
            for ii in order:
                pick.append(ut[ii]); tot += nt[ii]
                if tot >= tgt: break
            s2 = np.isin(kt, pick)
            nullg.append(g_t[s2].mean()); nullc.append(c_t[s2].mean())
        rows.append(dict(test=ws[t].w, n=int(sel.sum()), share=float(sel.mean()),
                         gross=float(g_t[sel].mean()), cost=float(c_t[sel].mean()),
                         net=float((g_t[sel] - c_t[sel]).mean()),
                         d_gross=float(g_t[sel].mean() - base_g),
                         d_cost=float(c_t[sel].mean() - base_c),
                         d_net=float((g_t[sel] - c_t[sel]).mean() - (base_g - base_c)),
                         null_d_gross=float(np.mean(nullg) - base_g),
                         null_d_gross_sd=float(np.std(nullg)),
                         null_d_cost=float(np.mean(nullc) - base_c),
                         z_gross=float((g_t[sel].mean() - np.mean(nullg)) / max(np.std(nullg), 1e-12))))
    if not rows: return None
    agg = {f: float(np.mean([r[f] for r in rows])) for f in
           ("d_gross", "d_cost", "d_net", "null_d_gross", "null_d_cost", "z_gross", "share")}
    agg["pooled_net"] = float(np.average([r["net"] for r in rows], weights=[r["n"] for r in rows]))
    agg["months_dgross_pos"] = int(sum(1 for r in rows if r["d_gross"] > 0))
    agg["months_dnet_pos"] = int(sum(1 for r in rows if r["d_net"] > 0))
    agg["months_beat_null_gross"] = int(sum(1 for r in rows if r["d_gross"] > r["null_d_gross"]))
    agg["months"] = len(rows)
    return {"agg": agg, "rows": rows}

rng = np.random.default_rng(5)
B = {}
for pop, masks in POPS.items():
    B[pop] = {}
    for kind in KINDS:
        for axis in ("gross", "resid", "cost"):
            for q in QS:
                r = run_axis(pop, masks, kind, axis, q, rng)
                if r is None: continue
                B[pop][f"{kind}|{axis}|q{q:.2f}"] = r
                a = r["agg"]
                print(f"[B] {pop:11s} {kind:18s} {axis:6s} q{q:.2f}  dgross {a['d_gross']:+.5f} "
                      f"(null {a['null_d_gross']:+.5f}, z {a['z_gross']:+.2f}, {a['months_beat_null_gross']}/{a['months']}) "
                      f"dcost {a['d_cost']:+.5f}  dnet {a['d_net']:+.5f} "
                      f"[{a['months_dnet_pos']}/{a['months']}]  netabs {a['pooled_net']:+.5f}", flush=True)

json.dump({"A_rank_units": A, "B_selection": B}, open("/tmp/p1/P1_TOLLNEUTRAL_V1.json", "w"))
print("WROTE /tmp/p1/P1_TOLLNEUTRAL_V1.json")
