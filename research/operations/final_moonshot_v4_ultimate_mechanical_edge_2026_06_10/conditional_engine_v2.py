"""CONDITIONAL ENGINE v2 — real SETUPS x conditional STATE-selection x dynamic geometry.
Not every bar: a library of triggers (FVG-retest, sweep-reclaim, breakout, reversion,
vol-expansion) generates STRUCTURED candidates. The walk-forward model then learns, per
market STATE (regime/session/day/trend/vol) and per trigger, the net-R map, and forward
takes only state-predicted +EV at the favoured geometry, sized by confidence.
Reports per-year, per-regime, AND per-trigger -> the conditional knowledge base.
No lookahead (features from closed bars; triggers use bar i info only). Real cost / geom tightness.
Usage: python conditional_engine_v2.py [n_symbols]
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
GEOMS = [(1.0,2.0),(0.75,3.0),(1.5,1.5),(0.5,4.0)]
FEATS = ["vol_ratio","vol_pct","slope20","slope50","ma_dist","rng_pos","compression",
         "ret5","hour","dow","dist_hi","dist_lo","updays","trig"]
TRIGS = ["fvg","sweep","breakout","reversion","volexp"]

def triggers(B, A, i, feat):
    """return list of (direction, trig_id) structured candidates at bar i."""
    out=[]; b=B[i]; a=A[i]
    tr = w1.htf_trend(B, i, 30)
    hi20=feat["_hi20"]; lo20=feat["_lo20"]
    # FVG retest continuation in HTF trend
    if tr==1:
        for k in range(i-2, max(i-9,60), -1):
            if B[k].l - B[k-2].h < 0.10*a: continue
            if b.l<=B[k].l and b.c>B[k-2].h and b.c>b.o: out.append((+1,0)); break
    elif tr==-1:
        for k in range(i-2, max(i-9,60), -1):
            if B[k-2].l - B[k].h < 0.10*a: continue
            if b.h>=B[k].h and b.c<B[k-2].l and b.c<b.o: out.append((-1,0)); break
    # sweep + reclaim
    if b.h>hi20 and b.c<hi20 and b.c<b.o: out.append((-1,1))
    if b.l<lo20 and b.c>lo20 and b.c>b.o: out.append((+1,1))
    # breakout (close beyond prior 20-bar extreme)
    if b.c>hi20 and b.c>b.o: out.append((+1,2))
    if b.c<lo20 and b.c<b.o: out.append((-1,2))
    # reversion from range extreme w/ reversal bar
    if feat["rng_pos"]>0.9 and b.c<b.o: out.append((-1,3))
    if feat["rng_pos"]<0.1 and b.c>b.o: out.append((+1,3))
    # vol-expansion momentum in trend
    if feat["vol_ratio"]>1.3 and abs(b.c-b.o)>0.6*a:
        out.append((+1 if b.c>b.o else -1, 4))
    return out

def build_symbol_rows(sym):
    try: T,B = w1.load(sym)
    except Exception: return []
    n=len(B)
    if n<400: return []
    base_cost=w1.cost_for(sym); A=[atr14(B,i) for i in range(n)]
    tr=[0.0]*n
    for i in range(1,n): tr[i]=max(B[i].h-B[i].l,abs(B[i].h-B[i-1].c),abs(B[i].l-B[i-1].c))
    C=[b.c for b in B];Hh=[b.h for b in B];Lo=[b.l for b in B]; rows=[]
    for i in range(110,n-90):
        a=A[i]
        if a<=0: continue
        sma100=sum(A[i-99:i+1])/100; sma20=sum(C[i-19:i+1])/20
        win=sorted(A[i-199:i+1]); vol_pct=sum(1 for x in win if x<=a)/len(win)
        lo50=min(Lo[i-49:i+1]);hi50=max(Hh[i-49:i+1])
        hi20=max(Hh[i-20:i]);lo20=min(Lo[i-20:i])
        feat={"vol_ratio":a/sma100 if sma100>0 else 1.0,"vol_pct":vol_pct,
              "slope20":(C[i]-C[i-20])/a,"slope50":(C[i]-C[i-50])/a,"ma_dist":(C[i]-sma20)/a,
              "rng_pos":(C[i]-lo50)/(hi50-lo50) if hi50>lo50 else .5,
              "compression":(sum(tr[i-4:i+1])/5)/(sum(tr[i-19:i+1])/20 or 1),
              "ret5":(C[i]-C[i-5])/a,"hour":T[i].hour,"dow":T[i].weekday(),
              "dist_hi":(hi20-C[i])/a,"dist_lo":(C[i]-lo20)/a,
              "updays":sum(1 for k in range(i-9,i+1) if C[k]>C[k-1])/10.0,
              "_hi20":hi20,"_lo20":lo20}
        cands=triggers(B,A,i,feat)
        for (d,trig) in cands:
            for gi,(s_atr,rmult) in enumerate(GEOMS):
                sd=s_atr*a; td=rmult*sd; cost=base_cost/s_atr
                r=simulate(B,i,d,stop_dist=sd,target_dist=td,cost=cost)
                rows.append((T[i],sym,i,d,gi,trig,feat,max(-1.3,min(5.0,r)),r))
    return rows

def main():
    syms=[s for s in w1.SYMBOLS if AC.get(s)][:NLIM]
    allrows=[]
    for s in syms:
        rr=build_symbol_rows(s); allrows+=rr
        print(f"  {s}: {len(rr)} (cum {len(allrows)})",flush=True)
    years=sorted(set(t.year for t,*_ in allrows))
    def X_of(rows): return np.array([[r[6][f] if f!='trig' else r[5] for f in FEATS]+[r[3],r[4]] for r in rows],dtype=float)
    print(f"\nWALK-FORWARD per year (train=past only). trigs={TRIGS} geoms={GEOMS}")
    print(f"{'yr':>5} {'cand':>7} {'taken':>6} {'COND R/t':>9} {'wR':>8} {'cum%@conf':>10} {'STATIC':>8}")
    fwd=[]
    for T in years:
        if T<=years[2]: continue
        train=[r for r in allrows if r[0].year<T and not(r[0].year==T-1 and r[0].month==12)]
        test=[r for r in allrows if r[0].year==T]
        if len(train)<3000 or not test: continue
        m=HistGradientBoostingRegressor(max_iter=250,learning_rate=0.05,max_depth=6,min_samples_leaf=60,l2_regularization=1.0)
        m.fit(X_of(train),np.array([r[7] for r in train]))
        pred=m.predict(X_of(test))
        bybar=collections.defaultdict(list)
        for k,r in enumerate(test): bybar[(r[1],r[2])].append((pred[k],r))
        taken=[max(o,key=lambda x:x[0]) for o in bybar.values()]
        taken=[(p,r) for p,r in taken if p>0.0]
        if not taken: print(f"{T:>5} {len(bybar):>7} {0:>6}"); continue
        real=[r[8] for _,r in taken]; w=[max(0,min(2.0,p)) for p,_ in taken]
        wR=sum(w[i]*real[i] for i in range(len(real)))/(sum(w) or 1)
        stat=[r[8] for r in test if r[4]==0]
        print(f"{T:>5} {len(bybar):>7} {len(taken):>6} {statistics.fmean(real):>+9.3f} {wR:>+8.3f} {sum(real):>+10.1f} {statistics.fmean(stat):>+8.3f}")
        fwd+=[(p,r) for p,r in taken]
    if fwd:
        print(f"\nFORWARD taken (n={len(fwd)}) by STATE — conditional knowledge base:")
        def br(name,keyfn,order=None):
            d=collections.defaultdict(list)
            for _,r in fwd: d[keyfn(r)].append(r[8])
            print(f"  by {name}:")
            for k in (order or sorted(d,key=str)):
                if k in d and len(d[k])>=15:
                    print(f"      {str(k):>10}: {statistics.fmean(d[k]):+.3f}R (n={len(d[k])}, win {sum(1 for x in d[k] if x>0)/len(d[k]):.0%})")
        br("trigger",lambda r:TRIGS[r[5]])
        br("vol_regime",lambda r:"hi" if r[6]["vol_ratio"]>1.15 else("lo" if r[6]["vol_ratio"]<0.9 else "mid"))
        br("session",lambda r:"Asia" if r[6]["hour"]<8 else("London" if r[6]["hour"]<16 else "NY"))
        br("trend",lambda r:"up" if r[6]["slope50"]>1 else("down" if r[6]["slope50"]<-1 else "flat"))
        br("asset_class",lambda r:AC.get(r[1]))
        # high-confidence slice
        hi=[r[8] for p,r in fwd if p>0.4]
        if hi: print(f"\n  HIGH-CONFIDENCE slice (pred>0.4R): n={len(hi)} mean {statistics.fmean(hi):+.3f}R win {sum(1 for x in hi if x>0)/len(hi):.0%} total {sum(hi):+.1f}R")
        # per (trigger x asset_class) top pockets
        cell=collections.defaultdict(list)
        for _,r in fwd: cell[(TRIGS[r[5]],AC.get(r[1]))].append(r[8])
        print("\n  TOP (trigger x asset_class) forward cells (n>=25):")
        rk=sorted([(k,statistics.fmean(v),len(v)) for k,v in cell.items() if len(v)>=25],key=lambda x:-x[1])
        for k,mu,nn in rk[:12]: print(f"      {k[0]:>10} x {k[1]:>8}: {mu:+.3f}R (n={nn})")
