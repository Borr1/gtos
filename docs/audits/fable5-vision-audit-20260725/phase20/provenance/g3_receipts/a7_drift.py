"""g3: the premise's own timescale. Mean signed price drift (bps) after the decision,
by minute, per family. Side-mirror of a drift is exactly its negative, so mean drift IS
the direction signal; no separate control needed. Fill-honest start."""
import sys, collections, numpy as np, json
sys.path.insert(0,"docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery")
import w0_ws
rows=w0_ws.load()
P={}
for rp in w0_ws.iter_rpaths(): P[w0_ws.key(rp)]=np.asarray(rp['cls'])
MIN=[1,2,3,5,8,12,20,30,45,60,90,119]
fams=[f for f,_ in collections.Counter(r['origin_family'] for r in rows).most_common()]
res={}
print(f"{'family':34s} {'n':>5s} " + " ".join(f"{'m'+str(m):>8s}" for m in MIN))
for fam in fams+['__ALL__','__ATMKT__']:
    if fam=='__ALL__': sub=rows
    elif fam=='__ATMKT__': sub=[r for r in rows if not r['origin_family'].startswith('current_')]
    else: sub=[r for r in rows if r['origin_family']==fam]
    rb=np.array([float(r['risk_distance'])/float(r['entry_price'])*1e4 for r in sub])
    M=np.full((len(sub),len(MIN)),np.nan)
    for i,r in enumerate(sub):
        c=P[w0_ws.key(r)]
        for j,m in enumerate(MIN):
            k=min(m,len(c))-1
            M[i,j]=c[k]*rb[i]
    mu=np.nanmean(M,axis=0); se=np.nanstd(M,axis=0,ddof=1)/np.sqrt(len(sub))
    res[fam]={'n':len(sub),'minutes':MIN,'drift_bps':mu.tolist(),'se_bps':se.tolist()}
    print(f"{fam:34s} {len(sub):5d} " + " ".join(f"{v:+8.3f}" for v in mu))
    print(f"{'  (+-se)':34s} {'':5s} " + " ".join(f"{v:8.3f}" for v in se))
json.dump(res,open('/tmp/g3/DRIFT_V1.json','w'),indent=1)
