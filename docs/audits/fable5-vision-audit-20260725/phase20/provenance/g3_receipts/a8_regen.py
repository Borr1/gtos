"""g3 REGENERATION: emit range_extreme_reversion / liquidity_sweep_reclaim /
structural_distance_extreme directly from the same M15 tape the generator reads, using
broader_origin_generators.py's own arithmetic, over the WHOLE archive (24 symbols,
2025-06-01..2026-06-10).  Purpose: (a) exact stop decomposition, (b) the first
measurement range_extreme_reversion has ever had, (c) predicate-vs-cited-evidence check."""
import csv, json, os, sys, math
import numpy as np
from datetime import datetime, timezone

H=("/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/"
   "phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/bars/"
   "bridge_ftmo_m15_20250601_20260610")
SYMS=['AUDJPY','AUDUSD','BTCUSD','CHFJPY','ETHUSD','EURGBP','EURJPY','EURUSD','GBPJPY',
 'GBPUSD','GER40','JP225','NAS100','NZDUSD','SPX500','UK100','UKOIL_cash','US30_cash',
 'USDCAD','USDCHF','USDJPY','USOIL_cash','XAGUSD','XAUUSD']
HZ=[1,2,4,8,16,32,64,96]          # M15 bars forward  (15m .. 24h)

def roll_max(a,w,shift):  # max over [i-w+shift, i-1+shift]; shift=0 -> prior-w EXCLUSIVE
    n=len(a); out=np.full(n,np.nan)
    from numpy.lib.stride_tricks import sliding_window_view
    if n>=w:
        sw=sliding_window_view(a,w).max(axis=1)      # sw[j] = max a[j:j+w]
        out[w:] = sw[0:n-w]                          # prior w bars, exclusive of i
    return out
def roll_min(a,w):
    n=len(a); out=np.full(n,np.nan)
    from numpy.lib.stride_tricks import sliding_window_view
    if n>=w:
        sw=sliding_window_view(a,w).min(axis=1)
        out[w:] = sw[0:n-w]
    return out
def roll_max_incl(a,w):
    n=len(a); out=np.full(n,np.nan)
    from numpy.lib.stride_tricks import sliding_window_view
    if n>=w:
        sw=sliding_window_view(a,w).max(axis=1)
        out[w-1:] = sw
    return out
def roll_min_incl(a,w):
    n=len(a); out=np.full(n,np.nan)
    from numpy.lib.stride_tricks import sliding_window_view
    if n>=w:
        sw=sliding_window_view(a,w).min(axis=1)
        out[w-1:] = sw
    return out
def roll_mean_incl(a,w):
    n=len(a); out=np.full(n,np.nan)
    cs=np.concatenate(([0.0],np.cumsum(a)))
    out[w-1:]=(cs[w:]-cs[:-w])/w
    return out

REC=[]
for s in SYMS:
    p=os.path.join(H,f"{s}_M15.csv")
    if not os.path.isfile(p): continue
    t=[];o=[];h=[];l=[];c=[]
    with open(p,newline='') as fh:
        for r in csv.DictReader(fh):
            t.append(r['time']); o.append(float(r['open'])); h.append(float(r['high']))
            l.append(float(r['low'])); c.append(float(r['close']))
    h=np.array(h);l=np.array(l);c=np.array(c);o=np.array(o);n=len(c)
    atr14=roll_mean_incl(h-l,14)                    # _atr == mean(high-low), NOT true range
    ph50=roll_max(h,50,0); pl50=roll_min(l,50)      # _prior_high/_prior_low : EXCLUSIVE of i
    ph20=roll_max(h,20,0); pl20=roll_min(l,20)
    hi50i=roll_max_incl(h,50); lo50i=roll_min_incl(l,50)   # _close_position : INCLUSIVE of i
    pos50=(c-lo50i)/np.where(hi50i>lo50i,hi50i-lo50i,np.nan)
    # mine V2's own predicate: 48-bar INCLUSIVE
    hi48i=roll_max_incl(h,48); lo48i=roll_min_incl(l,48)
    pos48=(c-lo48i)/np.where(hi48i>lo48i,hi48i-lo48i,np.nan)
    rng=h-l
    range50=ph50-pl50
    rpos=(c-pl50)/np.where(range50>0,range50,np.nan)     # SHIPPED range_extreme_reversion
    idx=np.arange(n)
    ok=(idx>=51)&np.isfinite(atr14)&(atr14>0)&np.isfinite(ph50)&np.isfinite(pl50)&np.isfinite(ph20)&np.isfinite(pl20)
    for i in np.nonzero(ok)[0]:
        ent=c[i]; a=atr14[i]
        rows=[]
        # ---- structural_distance_extreme (:865/:883)
        if pos50[i]>=0.97:
            rows.append(('structural_distance_extreme','SHORT',h[i]+0.25*a,h[i]-ent,0.25*a,pos50[i]))
        elif pos50[i]<=0.03:
            rows.append(('structural_distance_extreme','LONG',l[i]-0.25*a,ent-l[i],0.25*a,pos50[i]))
        # ---- liquidity_sweep_reclaim (:713/:730)
        sh = h[i]>ph20[i] and c[i]<ph20[i]
        sl = l[i]<pl20[i] and c[i]>pl20[i]
        if sh and not sl:
            rows.append(('liquidity_sweep_reclaim','SHORT',h[i]+0.25*a,h[i]-ent,0.25*a,(h[i]-ph20[i])/a))
        elif sl and not sh:
            rows.append(('liquidity_sweep_reclaim','LONG',l[i]-0.25*a,ent-l[i],0.25*a,(pl20[i]-l[i])/a))
        # ---- range_extreme_reversion (:682/:696) -- gated OFF in every shipped config
        if range50[i]>0 and rng[i]<1.5*a and np.isfinite(rpos[i]):
            if rpos[i]<=0.25:
                rows.append(('range_extreme_reversion','LONG',ent-1.0*a,0.0,1.0*a,rpos[i]))
            elif rpos[i]>=0.75:
                rows.append(('range_extreme_reversion','SHORT',ent+1.0*a,0.0,1.0*a,rpos[i]))
        if not rows: continue
        # forward measurement on the SAME M15 tape
        fw={}
        for hz in HZ:
            j=min(i+hz,n-1)
            fw[hz]=(c[j], h[i+1:j+1].max() if j>i else c[i], l[i+1:j+1].min() if j>i else c[i])
        for fam,side,stop,wick,atrterm,pred in rows:
            risk=abs(ent-stop)
            if risk<=0: continue
            rec={'sym':s,'t':t[i],'fam':fam,'side':side,'entry':ent,'risk_bps':risk/ent*1e4,
                 'wick_bps':wick/ent*1e4,'atrterm_bps':atrterm/ent*1e4,'pred':float(pred),
                 'atr14_bps':a/ent*1e4,'pos48':float(pos48[i]) if np.isfinite(pos48[i]) else None,
                 'pos50':float(pos50[i]) if np.isfinite(pos50[i]) else None,
                 'rpos':float(rpos[i]) if np.isfinite(rpos[i]) else None,
                 'rngatr':float(rng[i]/a)}
            sgn=1.0 if side=='LONG' else -1.0
            for hz in HZ:
                cl,hh,ll=fw[hz]
                rec[f'd{hz}']=sgn*(cl-ent)/ent*1e4
                rec[f'f{hz}']=(sgn*(hh-ent) if side=='LONG' else sgn*(ll-ent))/ent*1e4
                rec[f'a{hz}']=(sgn*(ll-ent) if side=='LONG' else sgn*(hh-ent))/ent*1e4
            REC.append(rec)
    print("done",s,len(REC),file=sys.stderr)

import gzip
with gzip.open('/tmp/g3/REGEN_V1.jsonl.gz','wt') as fh:
    for r in REC: fh.write(json.dumps(r)+"\n")
print("TOTAL",len(REC))
