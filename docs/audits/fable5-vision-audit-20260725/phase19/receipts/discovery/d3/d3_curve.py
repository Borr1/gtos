"""d3 D — THE ACCUMULATION CURVE, both systems in the same units.

A trading edge is a claim that a setup tells you where price will be LATER.  Its
signature is that the signal GROWS with the holding horizon.  Measure signal(H) for the
live sleeves and for the broad family on the same axis, in bps of price, both against a
matched PLACEBO-SIDE arm."""
import json,sys
from collections import defaultdict
import numpy as np
sys.path.insert(0,"/tmp/d3")
import d3_walk as W, d3_tape as D, d3_tape2 as T2, d3_reverse as R
from d3_pool import load, pool, row

HOR=[8,32,96,288,640,1280]; HH=[2,8,24,72,160,320]
# ---- live sleeves
rows=R.load_rows(); n=len(rows)
syms=sorted({p.name[:-len("_M15.csv")] for p in D.M15_DIR.glob("*_M15.csv")})
tape=T2.CTape(syms)
rr=[dict(s=r["s"],t=r["t"],f=r["sleeve"],d="L" if r["long"] else "S") for r in rows]
pos,W_h,W_l,W_c,W_t,t_dec=W.build_frames(tape,rr,list(range(n)))
entry=np.array([r["e"] for r in rows]); dnat=np.array([r["dnat"] for r in rows])
long=np.array([r["long"] for r in rows])
rng=np.random.default_rng(20260806); plong=rng.random(n)<0.5
bps=dnat/entry*1e4
res={}
for arm,side in (("REAL",long),("PLACEBO",plong)):
    e=entry[:,None]; dd=dnat[:,None]; sgn=np.where(side,1.0,-1.0)[:,None]
    rc=(W_c-e)/dd*sgn; rh=(W_h-e)/dd*sgn; rl=(W_l-e)/dd*sgn
    rhi=np.maximum(rh,rl); rlo=np.minimum(rh,rl)
    out=W.cell_walk(rc,rhi,rlo,3.0,HOR)
    res[arm]={h:out[h][0] for h in HOR}
live=[]
NB=4000
for h,hh in zip(HOR,HH):
    a=res["REAL"][h]; b=res["PLACEBO"][h]
    m=np.isfinite(a)&np.isfinite(b)
    d_r=(a-b)[m]; d_bps=((a-b)*bps)[m]
    ix=rng.integers(0,m.sum(),size=(NB,m.sum()))
    bs=d_bps[ix].mean(axis=1)
    live.append(dict(hours=hh,n=int(m.sum()),signal_r=float(d_r.mean()),
                     signal_bps=float(d_bps.mean()),
                     ci_lo=float(np.percentile(bs,2.5)),ci_hi=float(np.percentile(bs,97.5)),
                     p_le0=float((bs<=0).mean()),
                     gross_r=float(a[m].mean()),placebo_r=float(b[m].mean())))
# ---- broad family (already pooled)
P=load("D3"); tot,dayg,dayn,dayN,perwin=pool(P)
NATBPS=9.683
broad=[]
for h,hh in zip(HOR,HH):
    kr="REAL|native|3.0|%d|fixed"%h; kp=kr.replace("REAL","PLACEBO")
    a=row(tot,kr); b=row(tot,kp)
    broad.append(dict(hours=hh,n=a["n"],signal_r=a["gross"]-b["gross"],
                      signal_bps=(a["gross"]-b["gross"])*NATBPS,
                      gross_r=a["gross"],placebo_r=b["gross"]))
print("THE ACCUMULATION CURVE — signal (REAL minus PLACEBO-SIDE) vs holding horizon")
print()
print("%-8s | %-42s | %-28s"%("horizon","LIVE SLEEVES (n=134, own geometry)","BROAD FAMILY (n=144,725)"))
print("%-8s | %10s %10s %8s %10s | %10s %10s"%("hours","signal_R","signal_bps","p<=0","gross_R","signal_R","signal_bps"))
for L,B in zip(live,broad):
    print("%-8d | %10.4f %10.2f %8.4f %10.4f | %10.5f %10.4f"%(
        L["hours"],L["signal_r"],L["signal_bps"],L["p_le0"],L["gross_r"],B["signal_r"],B["signal_bps"]))
g_live=live[-1]["signal_bps"]/live[0]["signal_bps"] if live[0]["signal_bps"] else float('nan')
g_broad=broad[-1]["signal_bps"]/broad[0]["signal_bps"] if broad[0]["signal_bps"] else float('nan')
print()
print("GROWTH 2h -> 320h:  live sleeves %.2fx   broad family %.2fx"%(g_live,g_broad))
print("LEVEL at 320h:      live sleeves %.2f bps   broad family %.4f bps   ratio %.0fx"%(
    live[-1]["signal_bps"],broad[-1]["signal_bps"],live[-1]["signal_bps"]/broad[-1]["signal_bps"]))
json.dump(dict(live=live,broad=broad,growth_live=g_live,growth_broad=g_broad,
               live_median_stop_bps=float(np.median(bps)),broad_median_stop_bps=NATBPS),
          open("/tmp/d3/D3_CURVE.json","w"),indent=1)
