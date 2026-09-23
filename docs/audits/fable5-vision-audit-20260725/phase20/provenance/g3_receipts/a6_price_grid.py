"""g3: PRICE-SPACE geometry grid. Stop and target set in bps of price, identically for
every family -> 'hold the stop, vary the idea' and 'hold the idea, vary the stop' fall out
of one table. Signal = (real - side_mirror)/2 in bps, which is immune to any symmetric
per-fill price bias (the bid-series error) because it cancels in the difference."""
import sys, json, collections, numpy as np
sys.path.insert(0,"docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery")
import w0_ws
rows=w0_ws.load()
P={}
for rp in w0_ws.iter_rpaths():
    P[w0_ws.key(rp)]=(np.asarray(rp['fav']),np.asarray(rp['adv']),np.asarray(rp['cls']))
def ft(b):
    i=int(np.argmax(b)); return i if b[i] else -1
def walk(f,a,c,tgt,stp,mirror):
    if mirror: f,a,c=-a,-f,-c
    j=ft(a<=1e-12)
    if j<0: return 0.0
    fs=f[j:]; as_=a[j:]
    s=ft(as_<=stp+1e-12); t=ft(fs>=tgt-1e-12)
    if s<0 and t<0: return c[-1]
    if s<0: return tgt
    if t<0: return stp
    return stp if s<=t else tgt
STOPS=[2.5,5,10,20,40,80]; TGTS=[5,10,20,40,80,160]
fams=[f for f,_ in collections.Counter(r['origin_family'] for r in rows).most_common()]
out={}
for fam in fams+['__ALL__']:
    sub=rows if fam=='__ALL__' else [r for r in rows if r['origin_family']==fam]
    rb=np.array([float(r['risk_distance'])/float(r['entry_price'])*1e4 for r in sub])
    keys=[w0_ws.key(r) for r in sub]
    print(f"=== {fam}  n={len(sub)}  native stop {np.median(rb):.2f} bps ===")
    print(f"{'stop_bps':>8s} " + " ".join(f"{'T='+str(t):>14s}" for t in TGTS))
    tab={}
    for S in STOPS:
        cells=[]
        for T in TGTS:
            if T<=S: cells.append(None); continue
            real=np.empty(len(sub)); mirr=np.empty(len(sub))
            for i,k in enumerate(keys):
                f,a,c=P[k]; d=rb[i]
                real[i]=walk(f,a,c,T/d,-S/d,False)*d
                mirr[i]=walk(f,a,c,T/d,-S/d,True)*d
            sig=(real.mean()-mirr.mean())/2
            se=np.std(real-mirr,ddof=1)/np.sqrt(len(real))/2
            cells.append((float(real.mean()),float(sig),float(se)))
            tab[f"{S}|{T}"]={'gross_bps':float(real.mean()),'signal_bps':float(sig),'se':float(se)}
        print(f"{S:8.1f} " + " ".join("      .       " if c is None else f"{c[1]:+7.3f}±{c[2]:5.3f}" for c in cells))
    out[fam]=tab
    print()
json.dump(out,open('/tmp/g3/PRICE_GRID_V1.json','w'),indent=1)
