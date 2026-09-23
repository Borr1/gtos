"""p1 step 1 — THE PERSISTENCE MATRIX.

For every cell definition, per window: n, mean gross R, mean cost R, mean net R.
Then all 28 pairwise Spearman rank correlations across the 8 windows, for COST
and for GROSS separately -- plus the two things b1 never measured:

  (a) SPLIT-HALF RELIABILITY CEILING (row split, same window): how much cell-level
      rank information is measurable at all at this sample size.  If gross rank
      persistence across months is low AND split-half is low, the failure is
      measurement power.  If split-half is high and cross-month is low, the edge
      is genuinely non-stationary.  This distinguishes SIGNAL from POWER.
  (b) DAY-SPLIT reliability (odd/even trading days, same window): stability at the
      day scale inside a month, i.e. persistence with the calendar held fixed.
"""
from __future__ import annotations
import numpy as np, json, itertools, sys
sys.path.insert(0, "/tmp/p1")
import p1_lib as L

ws, SYMS = L.load_all()
NW = len(ws)

POPS = {}
for w in ws:
    f = w.fil == 1
    clean = f & (w.past == 0) & (w.fam != 1)          # fam 1 = current_breaker_re_entry
    POPS.setdefault("ALL_FILLS", []).append(f)
    POPS.setdefault("CLEAN_FILLS", []).append(clean)
    POPS.setdefault("AT_MARKET", []).append(f & (w.atm == 1))

def cellkeys(w, kind):
    if kind == "instrument":   return w.sym.astype(np.int64)
    if kind == "family":       return w.fam.astype(np.int64)
    if kind == "broker_hour":  return w.bhour.astype(np.int64)
    if kind == "utc_hour":     return w.hour.astype(np.int64)
    if kind == "inst_x_family":return w.sym.astype(np.int64) * 100 + w.fam
    if kind == "inst_x_hour":  return w.sym.astype(np.int64) * 100 + w.bhour
    if kind == "fam_x_hour":   return w.fam.astype(np.int64) * 100 + w.bhour
    if kind == "side":         return w.side.astype(np.int64)
    if kind == "inst_x_side":  return w.sym.astype(np.int64) * 10 + w.side
    if kind == "vol_tercile":  return w.vol.astype(np.int64)
    if kind == "inst_x_vol":   return w.sym.astype(np.int64) * 10 + w.vol
    raise KeyError(kind)

KINDS = ["instrument", "family", "broker_hour", "utc_hour", "inst_x_family",
         "inst_x_hour", "fam_x_hour", "inst_x_side", "inst_x_vol"]

def cellstats(keys, g, c, minn):
    u, inv = np.unique(keys, return_inverse=True)
    n = np.bincount(inv, minlength=len(u)).astype(float)
    sg = np.bincount(inv, weights=g, minlength=len(u))
    sc = np.bincount(inv, weights=c, minlength=len(u))
    ok = n >= minn
    return u[ok], n[ok], (sg / n)[ok], (sc / n)[ok]

def pair_persist(cells, minn, key):
    """cells: list per window of (u,n,mg,mc). returns dict of rank-corr stats."""
    out = {"cost": [], "gross": [], "net": [], "pairs": []}
    for i, j in itertools.combinations(range(NW), 2):
        ui, ni, gi, ci = cells[i]; uj, nj, gj, cj = cells[j]
        common = np.intersect1d(ui, uj)
        if len(common) < 4: continue
        ai = np.searchsorted(ui, common); aj = np.searchsorted(uj, common)
        rc = L.spearman(ci[ai], cj[aj]); rg = L.spearman(gi[ai], gj[aj])
        rn = L.spearman((gi - ci)[ai], (gj - cj)[aj])
        out["cost"].append(rc); out["gross"].append(rg); out["net"].append(rn)
        out["pairs"].append({"a": L.WINDOWS[i], "b": L.WINDOWS[j], "k": int(len(common)),
                             "cost": rc, "gross": rg, "net": rn, "gap": j - i})
    def s(v):
        v = np.array(v, float); v = v[np.isfinite(v)]
        if len(v) == 0:
            return dict(mean=float("nan"), sd=0.0, min=float("nan"), max=float("nan"), n=0)
        return dict(mean=float(v.mean()), sd=float(v.std(ddof=1)) if len(v) > 1 else 0.0,
                    min=float(v.min()), max=float(v.max()), n=int(len(v)))
    return {"cost": s(out["cost"]), "gross": s(out["gross"]), "net": s(out["net"]),
            "adjacent": {k: float(np.nanmean([p[k] for p in out["pairs"] if p["gap"] == 1]))
                         for k in ("cost", "gross", "net")},
            "farthest": {k: float(np.nanmean([p[k] for p in out["pairs"] if p["gap"] >= 5]))
                         for k in ("cost", "gross", "net")},
            "pairs": out["pairs"]}

def splithalf(w, mask, kind, minn, reps=25, seed=11, mode="row"):
    keys = cellkeys(w, kind)[mask]; g = w.g[mask]; c = w.c[mask]
    d = w.day[mask]
    rng = np.random.default_rng(seed)
    rc, rg = [], []
    for r in range(reps):
        if mode == "row":
            h = rng.random(len(g)) < 0.5
        else:  # day blocks
            ud = np.unique(d)
            pick = set(rng.choice(ud, size=len(ud) // 2, replace=False).tolist())
            h = np.isin(d, list(pick))
        if h.sum() < minn or (~h).sum() < minn: continue
        A = cellstats(keys[h], g[h], c[h], minn // 2)
        B = cellstats(keys[~h], g[~h], c[~h], minn // 2)
        com = np.intersect1d(A[0], B[0])
        if len(com) < 4: continue
        ia = np.searchsorted(A[0], com); ib = np.searchsorted(B[0], com)
        rc.append(L.spearman(A[3][ia], B[3][ib]))
        rg.append(L.spearman(A[2][ia], B[2][ib]))
    f = lambda v: float(np.nanmean(v)) if v else float("nan")
    return {"cost": f(rc), "gross": f(rg), "reps": len(rc)}

RES = {}
for pop, masks in POPS.items():
    RES[pop] = {}
    for kind in KINDS:
        minn = 50 if kind in ("instrument", "family", "broker_hour", "utc_hour",
                              "side", "vol_tercile") else 30
        cells = []
        percell = []
        for w, m in zip(ws, masks):
            u, n, mg, mc = cellstats(cellkeys(w, kind)[m], w.g[m], w.c[m], minn)
            cells.append((u, n, mg, mc))
            percell.append({"window": w.w, "k": int(len(u)), "n": int(n.sum())})
        P = pair_persist(cells, minn, kind)
        sh_row = [splithalf(w, m, kind, minn, mode="row") for w, m in zip(ws, masks)]
        sh_day = [splithalf(w, m, kind, minn, mode="day") for w, m in zip(ws, masks)]
        P["split_half_row_ceiling"] = {
            "cost": float(np.nanmean([x["cost"] for x in sh_row])),
            "gross": float(np.nanmean([x["gross"] for x in sh_row]))}
        P["split_half_day"] = {
            "cost": float(np.nanmean([x["cost"] for x in sh_day])),
            "gross": float(np.nanmean([x["gross"] for x in sh_day]))}
        P["cells_per_window"] = percell
        RES[pop][kind] = P
        print(f"{pop:12s} {kind:15s} k~{percell[3]['k']:4d}  "
              f"COST cross {P['cost']['mean']:+.4f} splitrow {P['split_half_row_ceiling']['cost']:+.4f} "
              f"splitday {P['split_half_day']['cost']:+.4f} | "
              f"GROSS cross {P['gross']['mean']:+.4f} splitrow {P['split_half_row_ceiling']['gross']:+.4f} "
              f"splitday {P['split_half_day']['gross']:+.4f}", flush=True)

json.dump(RES, open("/tmp/p1/P1_MATRIX_V1.json", "w"))
print("WROTE /tmp/p1/P1_MATRIX_V1.json")
