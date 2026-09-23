import json,gzip,glob,os
import numpy as np
R=[]
for f in sorted(glob.glob('/tmp/f1/out/RR_*.json.gz')):
    w=os.path.basename(f)[3:-8]
    with gzip.open(f,'rt') as fh:
        for r in json.load(fh): r['w']=w; R.append(r)
print('roster rows',len(R),'windows',sorted(set(r['w'] for r in R)))
g=np.array([r['g'] for r in R]); c=np.array([r['c'] for r in R])
db=np.array([r['d_bps'] for r in R]); fl=np.array([r['filled'] for r in R])
past=np.array([r['past'] for r in R])
print('\nWHOLE ROSTER (all emissions, honest fill, 2R, 120 M1 bars, h1 broker-true cost)')
print('  n=%d  fill_rate=%.4f  gross=%+.5f cost=%.5f net=%+.5f'%(len(R),fl.mean(),g.mean(),c.mean(),(g-c).mean()))
print('  FILLED ONLY n=%d gross=%+.5f cost=%.5f net=%+.5f wr=%.4f'%(fl.sum(),g[fl].mean(),c[fl].mean(),(g-c)[fl].mean(),(g[fl]>0).mean()))
gg=g[fl]; w=gg>0
print('  FILLED payoff=%.4f breakeven=%.4f actual_wr=%.4f gap=%+.4f'%(gg[w].mean()/-gg[~w].mean(),1/(1+gg[w].mean()/-gg[~w].mean()),w.mean(),w.mean()-1/(1+gg[w].mean()/-gg[~w].mean())))
print('  born_past_stop share=%.4f (gross %+.5f)'%(past.mean(),g[past].mean()))
print('\nROSTER FILLED by risk-distance decile:')
sel0=fl
d2=db[sel0];g2=g[sel0];c2=c[sel0];p2=past[sel0]
q=np.quantile(d2,np.linspace(0,1,11))
print(f"{'dec':>3s} {'lo':>8s} {'hi':>8s} {'n':>7s} {'gross':>9s} {'cost':>8s} {'net':>9s} {'wr':>7s} {'past':>6s}")
for i in range(10):
    s=(d2>=q[i])&(d2<=q[i+1]) if i==9 else (d2>=q[i])&(d2<q[i+1])
    print(f"{i+1:3d} {q[i]:8.2f} {q[i+1]:8.2f} {s.sum():7d} {g2[s].mean():+9.5f} {c2[s].mean():8.5f} {(g2[s]-c2[s]).mean():+9.5f} {(g2[s]>0).mean():7.4f} {p2[s].mean():6.3f}")
print('\nROSTER FILLED, past-stop rows EXCLUDED:')
s=fl&~past
print('  n=%d gross=%+.5f cost=%.5f net=%+.5f wr=%.4f'%(s.sum(),g[s].mean(),c[s].mean(),(g-c)[s].mean(),(g[s]>0).mean()))
print('\nROSTER by family (filled only):')
fams=sorted(set(r['fam'] for r in R))
fa=np.array([r['fam'] for r in R])
print(f"{'family':34s} {'n_emit':>8s} {'fill':>6s} {'n_fill':>8s} {'gross':>9s} {'cost':>8s} {'net':>9s} {'d_bps':>7s}")
for f_ in fams:
    m=(fa==f_)
    mf=m&fl
    if mf.sum()==0: continue
    print(f"{f_:34s} {m.sum():8d} {fl[m].mean():6.3f} {mf.sum():8d} {g[mf].mean():+9.5f} {c[mf].mean():8.5f} {(g-c)[mf].mean():+9.5f} {np.median(db[mf]):7.2f}")
# matched: taken vs roster
T=[]
for f in sorted(glob.glob('/tmp/f1/out/M_*.json')):
    w=os.path.basename(f)[2:-5]
    if w not in ('2026-01','2026-02'): continue
    for r in json.load(open(f)).get('taken',[]): r['w']=w; T.append(r)
idx={}
for i,r in enumerate(R):
    idx.setdefault((r['w'],r['sym']),[]).append(i)
dl=[];tg=[];cg=[];n=0
for t in T:
    ii=idx.get((t['w'],t['sym']),[])
    lo,hi=t['d_bps']*0.75,t['d_bps']*1.25
    mm=[i for i in ii if lo<=R[i]['d_bps']<=hi and R[i]['filled']]
    if len(mm)<5: continue
    n+=1; tg.append(t['g']); cg.append(np.mean([g[i] for i in mm])); dl.append(t['g']-np.mean([g[i] for i in mm]))
d=np.array(dl)
rs=np.random.default_rng(5); b=d[rs.integers(0,d.size,(4000,d.size))].mean(axis=1)
print('\nMATCHED taken vs ROSTER (Jan+Feb, same window+symbol, d within +-25%%, >=5 filled controls)')
print('  n=%d  taken %.5f  roster-matched %.5f  DELTA %+0.5f  CI95 [%+0.5f,%+0.5f] p(<=0)=%.4f'%(
    n,np.mean(tg),np.mean(cg),d.mean(),np.percentile(b,2.5),np.percentile(b,97.5),float((b<=0).mean())))
