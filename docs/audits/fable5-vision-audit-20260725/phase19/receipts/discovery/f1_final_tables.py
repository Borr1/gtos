import json,gzip,glob,os
import numpy as np
def econ(g,c):
    g=np.asarray(g,float);c=np.asarray(c,float);net=g-c;n=g.size
    w=g>0;l=~w
    aw=float(g[w].mean()) if w.any() else 0.0; al=float(-g[l].mean()) if l.any() else 0.0
    po=aw/al if al else None; be=1/(1+po) if po else None
    rs=np.random.default_rng(17); b=net[rs.integers(0,n,(4000,n))].mean(axis=1)
    return dict(n=int(n),gross=float(g.mean()),cost=float(c.mean()),net=float(net.mean()),
      wr=float(w.mean()),avg_win=aw,avg_loss=al,payoff=po,breakeven=be,gap=float(w.mean())-be if be else None,
      net_sd=float(net.std(ddof=1)),net_se=float(net.std(ddof=1)/np.sqrt(n)),
      net_ci95=[float(np.percentile(b,2.5)),float(np.percentile(b,97.5))],
      net_total=float(net.sum()))
AD=json.load(open('/tmp/f1/arm_days.json'))
R={}
DROP={}
for f in sorted(glob.glob('/tmp/f1/out/RR_*.json.gz')):
    w=os.path.basename(f)[3:-8]
    with gzip.open(f,'rt') as fh: rows=json.load(fh)
    ok=set(AD[w]); n0=len(rows)
    rows=[r for r in rows if r['day'] in ok]
    DROP[w]=dict(before=n0,after=len(rows),days=len(ok))
    R[w]=rows
print('day-restricted to each arm own trading days:',DROP)
print('ROSTER windows available:',sorted(R))
OUT={'roster_by_window':{},'roster_pooled':{},'roster_clean_by_window':{}}
allg=[];allc=[];ALL=[]
for w,rows in sorted(R.items()):
    g=np.array([r['g'] for r in rows]);c=np.array([r['c'] for r in rows])
    fl=np.array([r['filled'] for r in rows]);past=np.array([r['past'] for r in rows])
    fam=np.array([r['fam'] for r in rows]);db=np.array([r['d_bps'] for r in rows])
    e_all=econ(g,c); e_all['fill_rate']=float(fl.mean()); e_all['n_emissions']=len(rows)
    e_fill=econ(g[fl],c[fl]); e_fill['d_bps_median']=float(np.median(db[fl]))
    e_fill['born_past_stop_share']=float(past[fl].mean())
    cl=fl&~past&(fam!='current_breaker_re_entry')
    e_cl=econ(g[cl],c[cl]); e_cl['d_bps_median']=float(np.median(db[cl]))
    OUT['roster_by_window'][w]={'all_emissions':e_all,'filled':e_fill,'filled_clean':e_cl}
    ALL+=rows
g=np.array([r['g'] for r in ALL]);c=np.array([r['c'] for r in ALL])
fl=np.array([r['filled'] for r in ALL]);past=np.array([r['past'] for r in ALL])
fam=np.array([r['fam'] for r in ALL]);db=np.array([r['d_bps'] for r in ALL])
cl=fl&~past&(fam!='current_breaker_re_entry')
OUT['roster_pooled']={'windows':sorted(R),'all_emissions':dict(econ(g,c),fill_rate=float(fl.mean()),n_emissions=len(ALL)),
  'filled':dict(econ(g[fl],c[fl]),d_bps_median=float(np.median(db[fl])),born_past_stop_share=float(past[fl].mean())),
  'filled_clean':dict(econ(g[cl],c[cl]),d_bps_median=float(np.median(db[cl])))}
# family table pooled
famtab={}
for f_ in sorted(set(fam)):
    m=(fam==f_); mf=m&fl
    if mf.sum()==0: continue
    famtab[f_]=dict(n_emissions=int(m.sum()),fill_rate=float(fl[m].mean()),n_filled=int(mf.sum()),
      **{k:v for k,v in econ(g[mf],c[mf]).items() if k in ('gross','cost','net','wr','payoff','breakeven','gap','net_ci95')},
      d_bps_median=float(np.median(db[mf])),born_past_stop_share=float(past[mf].mean()))
OUT['roster_family_pooled']=famtab
# decile table clean
g2,c2,d2=g[cl],c[cl],db[cl]
q=np.quantile(d2,np.linspace(0,1,11)); dec=[]
for i in range(10):
    m=(d2>=q[i])&(d2<=q[i+1]) if i==9 else (d2>=q[i])&(d2<q[i+1])
    dec.append(dict(decile=i+1,d_bps_lo=float(q[i]),d_bps_hi=float(q[i+1]),
      **{k:v for k,v in econ(g2[m],c2[m]).items() if k in ('n','gross','cost','net','wr','payoff','breakeven','gap')}))
OUT['roster_clean_risk_distance_deciles']=dec
OUT['day_restriction']=DROP
json.dump(OUT,open('/tmp/f1/final_roster.json','w'),indent=1)
p=OUT['roster_pooled']
print('\nPOOLED ROSTER over %d windows'%len(R))
for k in ('all_emissions','filled','filled_clean'):
    e=p[k]; print('  %-14s n=%7d gross=%+.5f cost=%.5f net=%+.5f wr=%.4f payoff=%s be=%s gap=%s'%(
      k,e['n'],e['gross'],e['cost'],e['net'],e['wr'],
      ('%.4f'%e['payoff']) if e['payoff'] else '-',('%.4f'%e['breakeven']) if e['breakeven'] else '-',
      ('%+.4f'%e['gap']) if e['gap'] is not None else '-'))
print('\nFAMILY (pooled, filled):')
print(f"{'family':34s} {'emit':>8s} {'fill':>6s} {'nfill':>8s} {'gross':>9s} {'cost':>8s} {'net':>9s} {'gap':>8s} {'dbps':>7s} {'past':>6s}")
for f_,e in sorted(famtab.items(),key=lambda kv:kv[1]['gross']):
    print(f"{f_:34s} {e['n_emissions']:8d} {e['fill_rate']:6.3f} {e['n_filled']:8d} {e['gross']:+9.5f} {e['cost']:8.5f} {e['net']:+9.5f} {e['gap']:+8.4f} {e['d_bps_median']:7.2f} {e['born_past_stop_share']:6.3f}")
