"""d3 F — the surviving cohorts, priced honestly.

The pooled 3.19 bps toll is the wrong bar for a per-instrument cohort: XAGUSD's spread is
not EURUSD's.  Re-rank every cohort on signal(H) against ITS OWN measured toll, and carry
the per-window sign so a cohort that is one month's accident cannot pass."""
from __future__ import annotations
import json,sys,time
from collections import defaultdict
import numpy as np
sys.path.insert(0,"/tmp/d3")
import d3_walk as W, d3_tape as D, d3_tape2 as T2

HOR=[8,32,96,288,640,1280]; HH=[2,8,24,72,160,320]; TGT=3.0
WINS=list(D.WINDOWS)
sig=defaultdict(lambda: np.zeros(len(HOR)))     # sum of signal in bps
tollb=defaultdict(float)                        # sum of toll in bps (spread+comm+slip only)
tolls=defaultdict(float)                        # + swap at the 320h hold
cnt=defaultdict(float)
persig=defaultdict(lambda: defaultdict(lambda: np.zeros(len(HOR))))
percnt=defaultdict(lambda: defaultdict(float))

syms=sorted({p.name[:-len("_M15.csv")] for p in D.M15_DIR.glob("*_M15.csv")})
tape=T2.CTape(syms); C=W.Cost()
t0=time.time()
for win,indir in D.WINDOWS.items():
    rows=W.load_window(win,indir); n=len(rows)
    rng=np.random.default_rng(W.SEED+int(win.replace("-",""))+13)   # same seed as d3_search
    entry=np.array([float(r["e"]) for r in rows]); slp=np.array([float(r["sl"]) for r in rows])
    d=np.abs(entry-slp); long=np.array([r["d"]=="L" for r in rows]); plong=rng.random(n)<0.5
    fam=np.array([r["f"] for r in rows]); sym=np.array([r["s"] for r in rows])
    bps=d/entry*1e4
    basebps=np.zeros(n); swapbps=np.zeros(n)
    for a in range(n):
        b,_,_,_=C.base_px(sym[a],rows[a]["t"],entry[a]); basebps[a]=b/entry[a]*1e4
        pn=C.per_night_px(sym[a],bool(long[a]),entry[a])
        swapbps[a]=pn/entry[a]*1e4
    for c0 in range(0,n,6000):
        ix=list(range(c0,min(c0+6000,n)))
        pos,W_h,W_l,W_c,W_t,t_dec=W.build_frames(tape,rows,ix)
        sl_=np.array(ix); e=entry[sl_][:,None]; dd=d[sl_][:,None]
        R={}
        for arm,side in (("REAL",long[sl_]),("PLACEBO",plong[sl_])):
            sgn=np.where(side,1.0,-1.0)[:,None]
            rc=(W_c-e)/dd*sgn; rh=(W_h-e)/dd*sgn; rl=(W_l-e)/dd*sgn
            rhi=np.maximum(rh,rl); rlo=np.minimum(rh,rl)
            o=W.cell_walk(rc,rhi,rlo,TGT,HOR)
            R[arm]={h:(o[h][0],o[h][1]) for h in HOR}
        dif=np.stack([np.nan_to_num(R["REAL"][h][0]-R["PLACEBO"][h][0]) for h in HOR],axis=1)
        difb=dif*bps[sl_][:,None]
        # nights at the 320 h cell, for the swap term
        xb=R["REAL"][1280][1]
        tex=W_t[np.arange(len(sl_)),np.clip(xb,0,W_t.shape[1]-1)]
        hold=np.clip((tex+15-t_dec).astype(float),15,None)
        nights=hold/(60*24.0)
        f_=fam[sl_]; s_=sym[sl_]
        keys=[("SYM|"+x,(s_==x)) for x in np.unique(s_)]
        keys+=[("FXS|%s|%s"%(x,y),(f_==x)&(s_==y)) for x in np.unique(f_) for y in np.unique(s_[f_==x])]
        keys+=[("FAM|"+x,(f_==x)) for x in np.unique(f_)]+[("ALL",np.ones(len(sl_),bool))]
        for k,m in keys:
            if m.sum()==0: continue
            sig[k]+=difb[m].sum(axis=0); cnt[k]+=m.sum()
            tollb[k]+=float(basebps[sl_][m].sum())
            tolls[k]+=float((basebps[sl_][m]+swapbps[sl_][m]*nights[m]).sum())
            persig[k][win]+=difb[m].sum(axis=0); percnt[k][win]+=m.sum()
        del W_h,W_l,W_c,W_t
    print(win,n,round(time.time()-t0,1),flush=True)

out={}
for k in sig:
    if cnt[k]<200: continue
    v=sig[k]/cnt[k]; tb=tollb[k]/cnt[k]; ts=tolls[k]/cnt[k]
    pw=[]
    for w in WINS:
        if percnt[k].get(w,0)>=20: pw.append((persig[k][w]/percnt[k][w]).tolist())
        else: pw.append(None)
    out[k]=dict(n=int(cnt[k]),signal_bps=[float(x) for x in v],toll_bps_short=tb,
                toll_bps_320h=ts,
                ratio_by_h=[float(x/ (tb if i<3 else ts)) for i,x in enumerate(v)],
                best_ratio=float(max(v[i]/(tb if i<3 else ts) for i in range(len(v)))),
                per_window=pw,
                windows_positive_at_best=None)
for k,v in out.items():
    bi=int(np.argmax([v["signal_bps"][i]/(v["toll_bps_short"] if i<3 else v["toll_bps_320h"])
                      for i in range(len(HOR))]))
    v["best_h_index"]=bi; v["best_hours"]=HH[bi]
    v["windows_positive_at_best"]=int(sum(1 for pw in v["per_window"] if pw and pw[bi]>0))
    v["windows_evaluable"]=int(sum(1 for pw in v["per_window"] if pw))
json.dump(out,open("/tmp/d3/D3_COHORT.json","w"),indent=1)

print()
print("EVERY COHORT AGAINST ITS OWN TOLL.  ratio = signal_bps / toll_bps at the same horizon.")
print("A viable cohort needs ratio > 1 AND the sign to hold across windows.")
print("%-46s %6s %8s %8s %7s %8s %6s"%("cohort","n","best_h","signal","toll","ratio","wins+"))
ks=sorted(out,key=lambda k:-out[k]["best_ratio"])
for k in ks[:20]:
    v=out[k]; bi=v["best_h_index"]
    print("%-46s %6d %8d %8.3f %7.3f %8.3f %3d/%d"%(k[:46],v["n"],v["best_hours"],
        v["signal_bps"][bi],(v["toll_bps_short"] if bi<3 else v["toll_bps_320h"]),
        v["best_ratio"],v["windows_positive_at_best"],v["windows_evaluable"]))
print()
n1=sum(1 for v in out.values() if v["best_ratio"]>1.0)
n2=sum(1 for v in out.values() if v["best_ratio"]>1.0 and v["windows_positive_at_best"]>=int(0.75*v["windows_evaluable"]))
n3=sum(1 for v in out.values() if v["best_ratio"]>1.0 and v["windows_positive_at_best"]==v["windows_evaluable"])
print("cohorts with best-horizon ratio > 1        : %d of %d"%(n1,len(out)))
print("  ... and positive in >=75%% of windows     : %d"%n2)
print("  ... and positive in EVERY window         : %d"%n3)
print("looks taken: %d cohorts x %d horizons = %d"%(len(out),len(HOR),len(out)*len(HOR)))
print("ALL:", out["ALL"])
