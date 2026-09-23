"""g3 separable experiment v2 — fill-honest, tie-audited.
INSTRUMENT: price captured in bps (invariant to stop scale k) + the intrabar-tie fraction."""
import sys, json, collections, numpy as np
sys.path.insert(0,"docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery")
import w0_ws
rows=w0_ws.load()
PATHS={}
for rp in w0_ws.iter_rpaths():
    PATHS[w0_ws.key(rp)]=(np.asarray(rp['fav']),np.asarray(rp['adv']),np.asarray(rp['cls']))

def ft(b):
    i=int(np.argmax(b)); return i if b[i] else -1

def walk(f,a,c,target,stop,mirror=False,require_fill=True):
    if mirror: f,a,c = -a,-f,-c
    n=len(f)
    st=0
    if require_fill:
        j=ft(a<=1e-12)
        if j<0: return 0.0,'no_fill',False
        st=j
    fs=f[st:]; as_=a[st:]
    s=ft(as_<=stop+1e-12); t=ft(fs>=target-1e-12)
    if s<0 and t<0: return c[n-1],'path_end',False
    if s<0: return target,'target',False
    if t<0: return stop,'stop',False
    tie = (s==t)
    return (stop,'stop',tie) if s<=t else (target,'target',tie)

KS=[0.5,1.0,1.5,2.0,3.0,4.0,6.0,8.0,12.0,20.0,32.0]
fams=collections.Counter(r['origin_family'] for r in rows)
res={}
print(f"{'family':34s} {'k':>5s} {'stopbps':>8s} {'grossR':>8s} {'grossbps':>9s} {'se':>6s} {'mirrbps':>8s} {'signal':>8s} {'TIE%':>6s} {'res%':>6s}")
for fam,_ in fams.most_common():
    sub=[r for r in rows if r['origin_family']==fam]
    rb=np.array([float(r['risk_distance'])/float(r['entry_price'])*1e4 for r in sub])
    per_k={}
    for k in KS:
        rr=np.empty(len(sub)); rm=np.empty(len(sub)); ties=0; resolved=0
        for i,r in enumerate(sub):
            f,a,c=PATHS[w0_ws.key(r)]
            v,why,tie=walk(f,a,c,2.0*k,-1.0*k); rr[i]=v
            if why in ('stop','target'): resolved+=1
            if tie: ties+=1
            v2,_,_=walk(f,a,c,2.0*k,-1.0*k,mirror=True); rm[i]=v2
        bps=rr*rb; bpsm=rm*rb
        d={'n':len(sub),'stop_bps_med':float(np.median(rb*k)),'gross_R':float(np.mean(rr)/k),
           'gross_bps':float(np.mean(bps)),'se':float(np.std(bps,ddof=1)/np.sqrt(len(bps))),
           'mirror_bps':float(np.mean(bpsm)),'signal_bps':float((np.mean(bps)-np.mean(bpsm))/2),
           'tie_pct':100*ties/len(sub),'resolved_pct':100*resolved/len(sub)}
        per_k[k]=d
        print(f"{fam if k==KS[0] else '':34s} {k:5.1f} {d['stop_bps_med']:8.2f} {d['gross_R']:8.4f} {d['gross_bps']:9.4f} {d['se']:6.3f} {d['mirror_bps']:8.4f} {d['signal_bps']:8.4f} {d['tie_pct']:6.1f} {d['resolved_pct']:6.1f}")
    res[fam]=per_k
    print()
json.dump(res,open('/tmp/g3/SEP_V2.json','w'),indent=1)
