"""B6 step 4 — three-way decomposition at a fixed cutoff. PAST-only vs FUTURE-only vs WHOLE day.
Panel = trades at hour>=CUT. If FUTURE-only carries the skill and PAST-only carries none, the
Lane 6 finding is a lookahead by construction."""
import numpy as np, pandas as pd, json, warnings
warnings.filterwarnings('ignore')
from scipy import stats
import b6_core as C
df=C.build_master()
E=df[df.elig].copy(); P=df[df.elig&df.filled].copy()
DIALS=['atr14_over_atr50','close_to_close_vol_8_over_48','compression_ratio_prior_bar','spread_r',
       'cost_r','risk_over_atr']
NAMES=['vol','ccvol','comp','spread','cost','risk']
def regime_from(mask_fn):
    sub=E[mask_fn(E)]
    g=sub.groupby('date',observed=True)
    R=g[DIALS].median(); R.columns=NAMES
    R['trendshare']=g.trend_state_m15.apply(lambda s: s.isin(['strong_up','strong_down']).mean())
    R['upshare']=g.trend_state_m15.apply(lambda s: s.isin(['strong_up','up']).mean())
    R['nc']=g.size(); R['dow']=R.index.dayofweek
    return R
def panel(regime,hmin,minf=5):
    Q=P[P.hour>=hmin]
    fd=Q.groupby(['origin_family','date'],observed=True).agg(n=('net_r','size'),y=('net_r','mean')).reset_index()
    fd=fd[fd.n>=minf].sort_values(['origin_family','date'])
    for L in (5,10,20):
        fd['mom%d'%L]=fd.groupby('origin_family',observed=True).y.transform(lambda s:s.shift(1).rolling(L,min_periods=3).mean())
    pd_=fd.groupby('date',observed=True).y.mean().sort_index()
    fd['poolmom10']=fd.date.map(pd_.shift(1).rolling(10,min_periods=3).mean())
    fd=fd.merge(regime.reset_index(),on='date',how='left')
    fams=sorted(fd.origin_family.unique()); INT=[]
    for f in fams:
        fd['f_'+f]=(fd.origin_family==f).astype(float)
        for r in ('vol','ccvol','trendshare','spread'):
            c='x_%s_%s'%(f,r); fd[c]=fd['f_'+f]*fd[r]; INT.append(c)
    REG=['vol','ccvol','comp','spread','cost','risk','trendshare','upshare','dow']
    fd=fd.dropna(subset=['mom20','poolmom10','vol']).sort_values('date').reset_index(drop=True)
    return fd,REG,INT
def run(fd,cols):
    X=fd[cols].fillna(0.).to_numpy(float); y=fd.y.to_numpy(float); w=fd.n.to_numpy(float)
    d=fd.date.to_numpy(); ud=np.array(sorted(set(d)))
    p=C.wf_ridge(X,y,w,d,ud,alpha=10.,causal_scaler=True); ok=~np.isnan(p)
    rho=stats.spearmanr(p[ok],y[ok]); sel=ok&(p>0)
    return dict(n=int(ok.sum()),rho=round(float(rho.statistic),5),p=float('%.3g'%rho.pvalue),
      trades=int(w[sel].sum()),
      delta=round(float(np.average(y[sel],weights=w[sel])-np.average(y[ok],weights=w[ok])),5))
out=[]
for CUT in (8,12,16):
    arms={'PAST-only  (hours <%d, causal)'%CUT:  lambda E,c=CUT: E.hour< c,
          'FUTURE-only(hours>=%d, anti-causal)'%CUT: lambda E,c=CUT: E.hour>=c,
          'WHOLE day  (Lane 6)':                 lambda E: E.hour>=0}
    print('\n=== trades at hour >= %d ==='%CUT)
    print('%-40s %6s %9s %10s %8s %9s'%('regime information set','n_oos','rho','p','trades','delta'))
    for lbl,fn in arms.items():
        R=regime_from(fn); fd,REG,INT=panel(R,CUT); r=run(fd,REG+INT)
        r['cut']=CUT; r['arm']=lbl; out.append(r)
        print('%-40s %6d %+9.4f %10s %8d %+9.5f'%(lbl,r['n'],r['rho'],r['p'],r['trades'],r['delta']))
json.dump(out,open('threeway.json','w'),indent=1)
