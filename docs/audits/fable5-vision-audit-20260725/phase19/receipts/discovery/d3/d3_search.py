"""d3 E — THE COMPLETENESS SEARCH.  The pooled family shows zero accumulation.  Before
concluding, look inside it: is there ANY origin family, ANY instrument, or any
family x instrument cohort whose signal GROWS with horizon the way a live sleeve's does?
Whole population, no sampling, matched PLACEBO-SIDE at every horizon."""
from __future__ import annotations
import json,sys,time
from collections import defaultdict
from datetime import datetime
import numpy as np
sys.path.insert(0,"/tmp/d3")
import d3_walk as W, d3_tape as D, d3_tape2 as T2

HOR=[8,32,96,288,640,1280]; HH=[2,8,24,72,160,320]
TGT=3.0
acc=defaultdict(lambda: np.zeros(len(HOR)))
cnt=defaultdict(float)
bpsum=defaultdict(float)
daysig=defaultdict(lambda: defaultdict(lambda: np.zeros(len(HOR))))
dayn=defaultdict(lambda: defaultdict(float))

syms=sorted({p.name[:-len("_M15.csv")] for p in D.M15_DIR.glob("*_M15.csv")})
tape=T2.CTape(syms)
t0=time.time()
for win,indir in D.WINDOWS.items():
    rows=W.load_window(win,indir); n=len(rows)
    rng=np.random.default_rng(W.SEED+int(win.replace("-",""))+13)
    entry=np.array([float(r["e"]) for r in rows]); slp=np.array([float(r["sl"]) for r in rows])
    d=np.abs(entry-slp); long=np.array([r["d"]=="L" for r in rows]); plong=rng.random(n)<0.5
    fam=np.array([r["f"] for r in rows]); sym=np.array([r["s"] for r in rows])
    day=np.array([win+"|"+r["t"][:10] for r in rows])
    bps=d/entry*1e4
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
            R[arm]={h:o[h][0] for h in HOR}
        dif=np.stack([np.nan_to_num(R["REAL"][h]-R["PLACEBO"][h]) for h in HOR],axis=1)
        difb=dif*bps[sl_][:,None]
        f_=fam[sl_]; s_=sym[sl_]; dy=day[sl_]
        for key,mask in (
            [("FAM|"+x, f_==x) for x in np.unique(f_)] +
            [("SYM|"+x, s_==x) for x in np.unique(s_)] +
            [("ALL", np.ones(len(sl_),dtype=bool))]):
            if mask.sum()==0: continue
            acc[key]+=difb[mask].sum(axis=0); cnt[key]+=mask.sum()
            bpsum[key]+=float(bps[sl_][mask].sum())
        for x in np.unique(f_):
            for y in np.unique(s_[f_==x]):
                m=(f_==x)&(s_==y)
                k="FXS|%s|%s"%(x,y)
                acc[k]+=difb[m].sum(axis=0); cnt[k]+=m.sum(); bpsum[k]+=float(bps[sl_][m].sum())
        for dd_ in np.unique(dy):
            m=dy==dd_
            daysig["ALL"][dd_]+=difb[m].sum(axis=0); dayn["ALL"][dd_]+=m.sum()
        del W_h,W_l,W_c,W_t
    print(win,n,round(time.time()-t0,1),flush=True)

out={}
for k in acc:
    if cnt[k]<200: continue
    v=acc[k]/cnt[k]
    out[k]=dict(n=int(cnt[k]),mean_stop_bps=bpsum[k]/cnt[k],
                signal_bps=[float(x) for x in v],
                growth=float(v[-1]/v[0]) if v[0]!=0 else None,
                max_bps=float(v.max()), at320=float(v[-1]))
json.dump(out,open("/tmp/d3/D3_SEARCH.json","w"),indent=1)
tolls={"broad_toll_bps_per_trade":3.19}
print()
print("SIGNAL IN BPS OF PRICE BY HORIZON — every cohort with n>=200.  Broker toll ~3.19 bps/trade.")
print("%-46s %7s %8s %8s %8s %8s %8s %8s %8s"%("cohort","n","2h","8h","24h","72h","160h","320h","max"))
def show(pref):
    ks=[k for k in out if k.startswith(pref)]
    ks.sort(key=lambda k:-out[k]["max_bps"])
    for k in ks[:14]:
        v=out[k]
        print("%-46s %7d %s %8.3f"%(k[:46],v["n"]," ".join("%8.3f"%x for x in v["signal_bps"]),v["max_bps"]))
show("ALL"); print("--- by origin family (7) ---"); show("FAM|")
print("--- by instrument, top 14 by max signal ---"); show("SYM|")
print("--- by family x instrument, top 14 by max signal (168 cohorts) ---"); show("FXS|")
print()
n_over=sum(1 for k,v in out.items() if v["max_bps"]>3.19)
print("cohorts whose BEST horizon beats the 3.19 bps toll: %d of %d"%(n_over,len(out)))
