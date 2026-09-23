"""CONDITIONAL ENGINE v1 — the anti-average. No static rule, no blended verdict.
At EVERY H4 bar, consider BOTH directions x several geometries. Learn the STATE->net-R map
from PAST data only (walk-forward, expanding window, embargoed). On each forward year, the
policy takes only what the CURRENT market state predicts is +EV, at the geometry the state
favours, sized by confidence. Report results BROKEN OUT by regime/session/day — never one average.
Fills via trusted geometry_lib (no lookahead). Real per-asset cost, scaled by geometry tightness.
Usage: python conditional_engine.py [n_symbols]
"""
import sys, json, statistics, collections, math
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from geometry_lib import simulate, atr14
import wave1_structure_setups_ict as w1
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL as AC
from sklearn.ensemble import HistGradientBoostingRegressor

NLIM = int(sys.argv[1]) if len(sys.argv) > 1 else 999
GEOMS = [(1.0, 2.0), (0.75, 3.0), (1.5, 1.5)]   # (stop_atr, R_multiple)
FEATS = ["vol_ratio","vol_pct","slope20","slope50","ma_dist","rng_pos","compression",
         "ret5","hour","dow","dist_hi","dist_lo","updays"]

def build_symbol_rows(sym):
    try: T, B = w1.load(sym)
    except Exception: return []
    n = len(B)
    if n < 400: return []
    base_cost = w1.cost_for(sym)
    A = [atr14(B, i) for i in range(n)]
    tr = [0.0]*n
    for i in range(1, n):
        tr[i] = max(B[i].h-B[i].l, abs(B[i].h-B[i-1].c), abs(B[i].l-B[i-1].c))
    C = [b.c for b in B]; Hh=[b.h for b in B]; Lo=[b.l for b in B]
    rows = []
    for i in range(110, n-90):
        a = A[i]
        if a <= 0: continue
        sma100 = sum(A[i-99:i+1])/100
        win = sorted(A[i-199:i+1]) if i>=199 else sorted(A[max(0,i-199):i+1])
        vol_pct = sum(1 for x in win if x <= a)/len(win)
        sma20 = sum(C[i-19:i+1])/20
        lo50 = min(Lo[i-49:i+1]); hi50 = max(Hh[i-49:i+1])
        rng_pos = (C[i]-lo50)/(hi50-lo50) if hi50>lo50 else 0.5
        comp = (sum(tr[i-4:i+1])/5)/(sum(tr[i-19:i+1])/20 or 1)
        hi20 = max(Hh[i-20:i]); lo20 = min(Lo[i-20:i])
        feat = {
            "vol_ratio": a/sma100 if sma100>0 else 1.0,
            "vol_pct": vol_pct,
            "slope20": (C[i]-C[i-20])/a,
            "slope50": (C[i]-C[i-50])/a,
            "ma_dist": (C[i]-sma20)/a,
            "rng_pos": rng_pos,
            "compression": comp,
            "ret5": (C[i]-C[i-5])/a,
            "hour": T[i].hour,
            "dow": T[i].weekday(),
            "dist_hi": (hi20-C[i])/a,
            "dist_lo": (C[i]-lo20)/a,
            "updays": sum(1 for k in range(i-9,i+1) if C[k]>C[k-1])/10.0,
        }
        for gi,(s_atr,rmult) in enumerate(GEOMS):
            sd = s_atr*a; td = rmult*sd
            cost = base_cost/s_atr
            for d in (+1,-1):
                r = simulate(B, i, d, stop_dist=sd, target_dist=td, cost=cost)
                rows.append((T[i], sym, i, d, gi, feat, max(-1.3, min(5.0, r)), r))
    return rows

def main():
    syms = [s for s in w1.SYMBOLS if AC.get(s)][:NLIM]
    allrows = []
    for s in syms:
        rr = build_symbol_rows(s); allrows += rr
        print(f"  {s}: {len(rr)} cand-rows (cum {len(allrows)})", flush=True)
    if not allrows: print("no rows"); return
    years = sorted(set(t.year for t,*_ in allrows))
    def X_of(rows):
        return np.array([[r[5][f] for f in FEATS]+[r[3], r[4]] for r in rows], dtype=float)
    print(f"\nWALK-FORWARD (train=past only, expanding, embargoed). years {years[0]}-{years[-1]}")
    print(f"{'test_yr':>7} {'n_cand':>8} {'COND n_taken':>12} {'COND R/trd':>11} {'COND wR':>9} {'STATIC R/trd':>13}")
    fwd_taken = []   # pooled forward taken trades w/ features for regime breakdown
    for T in years:
        if T <= years[2]: continue   # need >=3y history
        train = [r for r in allrows if r[0].year < T and not (r[0].year==T-1 and r[0].month==12)]
        test  = [r for r in allrows if r[0].year == T]
        if len(train) < 5000 or not test: continue
        m = HistGradientBoostingRegressor(max_iter=220, learning_rate=0.05, max_depth=6,
                                          min_samples_leaf=80, l2_regularization=1.0)
        m.fit(X_of(train), np.array([r[6] for r in train]))
        pred = m.predict(X_of(test))
        # group by (sym,bar) -> choose best (dir,geom)
        bybar = collections.defaultdict(list)
        for k,r in enumerate(test): bybar[(r[1],r[2])].append((pred[k], r))
        taken = []
        for key, opts in bybar.items():
            p_best, r_best = max(opts, key=lambda x: x[0])
            if p_best > 0.0:   # take only state-predicted +EV; not tuned
                taken.append((p_best, r_best))
        if not taken: 
            print(f"{T:>7} {len(bybar):>8} {0:>12}"); continue
        real = [r[7] for _,r in taken]
        w = [max(0.0, min(2.0, p)) for p,_ in taken]
        wR = sum(w[i]*real[i] for i in range(len(real)))/ (sum(w) or 1)
        # static baseline: take ALL candidates at geom0 long+short (the 'average' way)
        stat = [r[7] for r in test if r[4]==0]
        print(f"{T:>7} {len(bybar):>8} {len(taken):>12} {statistics.fmean(real):>+11.3f} {wR:>+9.3f} {statistics.fmean(stat):>+13.3f}")
        for p,r in taken: fwd_taken.append(r)
    # ---- regime breakdown of pooled forward taken trades (PROVE non-stationarity) ----
    if fwd_taken:
        print(f"\nFORWARD taken trades broken out by STATE (n={len(fwd_taken)}) — never a single average:")
        def bucket_report(name, keyfn, order=None):
            d = collections.defaultdict(list)
            for r in fwd_taken: d[keyfn(r)].append(r[7])
            print(f"  by {name}:")
            keys = order or sorted(d)
            for k in keys:
                if k in d and len(d[k])>=20:
                    print(f"      {str(k):>10}: {statistics.fmean(d[k]):+.3f}R  (n={len(d[k])}, win {sum(1 for x in d[k] if x>0)/len(d[k]):.0%})")
        bucket_report("vol_regime", lambda r: "hi_vol" if r[5]["vol_ratio"]>1.15 else ("lo_vol" if r[5]["vol_ratio"]<0.9 else "mid"))
        bucket_report("session", lambda r: "Asia" if r[5]["hour"]<8 else ("London" if r[5]["hour"]<16 else "NY"))
        bucket_report("dow", lambda r: r[5]["dow"], order=[0,1,2,3,4,6])
        bucket_report("trend", lambda r: "up" if r[5]["slope50"]>1 else ("down" if r[5]["slope50"]<-1 else "flat"))
        bucket_report("asset_class", lambda r: AC.get(r[1]))

if __name__ == "__main__":
    main()
