"""B6 step 6 — THE SHORT-LEG QUESTION, part 1: what the five months actually contained, and whether
the pool supports a short leg at all. Builds a bars-derived daily direction index from the cache
(no prices in the cache; derived from position-in-range + trend-state, then validated against the
pool's own realised long-short drift)."""
import numpy as np, pandas as pd, json, math, warnings
warnings.filterwarnings('ignore')
from scipy import stats
import b6_core as C
df=C.build_master()
E=df[df.elig].copy(); P=df[df.elig&df.filled].copy()

# ---- daily direction index, per symbol then pooled ----
g=E.groupby(['symbol','date'],observed=True)
sd=g.agg(dhi=('dist_to_prior_high20_atr','median'), dlo=('dist_to_prior_low20_atr','median'),
         rngpos=('close_position_in_lookback_range','median'), n=('cost_r','size')).reset_index()
ts=g.trend_state_m15
sd['up']=ts.apply(lambda s: s.isin(['strong_up','up']).mean()).to_numpy()
sd['dn']=ts.apply(lambda s: s.isin(['strong_down','down']).mean()).to_numpy()
sd['dir_sym']=(sd.dlo-sd.dhi)          # near highs => dlo big, dhi small => positive
sd['dir_ts']=sd.up-sd.dn
# pooled market direction: mean across symbols (equal weight), and index-only
IDX=['GER40','US30_cash','NAS100','JP225','UK100','EU50_cash','FRA40','SPX500']
mkt=sd.groupby('date',observed=True).agg(dir_all=('dir_ts','mean'), rng_all=('dir_sym','mean'),
                                         rngpos=('rngpos','mean'))
mi=sd[sd.symbol.isin(IDX)].groupby('date',observed=True).agg(dir_idx=('dir_ts','mean'),rng_idx=('dir_sym','mean'))
mkt=mkt.join(mi)
# validate against the pool's own realised drift
dd=P.groupby(['date','side'],observed=True).net_r.mean().unstack()
drift=(dd['LONG']-dd['SHORT'])
mkt['pool_drift']=drift
print('daily direction index vs the pool own LONG-SHORT realised drift, n=%d days'%mkt.pool_drift.notna().sum())
for c in ['dir_all','rng_all','dir_idx','rng_idx','rngpos']:
    r=stats.spearmanr(mkt[c],mkt.pool_drift,nan_policy='omit')
    print('  corr(%-9s, pool_drift) rho=%+.3f p=%.4f'%(c,r.statistic,r.pvalue))
DIRCOL='dir_idx' if abs(stats.spearmanr(mkt.dir_idx,mkt.pool_drift,nan_policy='omit').statistic)>=abs(stats.spearmanr(mkt.dir_all,mkt.pool_drift,nan_policy='omit').statistic) else 'dir_all'
print('\nusing %s as the daily direction index'%DIRCOL)

# ---- what did the five months contain? cumulative direction path + drawdown ----
m=mkt[DIRCOL].dropna()
cum=m.cumsum()
dd_path=cum-cum.cummax()
print('\nCUMULATIVE DIRECTION PATH (proxy index): start %.2f end %.2f | max drawdown %.2f (%.0f%% of range)'%(
   cum.iloc[0],cum.iloc[-1],dd_path.min(),100*abs(dd_path.min())/max(1e-9,cum.max()-cum.min())))
print('days with negative direction index: %d of %d (%.1f%%)'%((m<0).sum(),len(m),100*(m<0).mean()))
byq=pd.qcut(m,5,labels=False)
print('\nquintiles of the daily direction index (Q0 = most DOWN):')
print('%-4s %6s %10s %10s %10s %10s %10s'%('q','days','dir','LONG net','SHORT net','L-S','all net'))
rows=[]
for q in range(5):
    ds=m.index[byq==q]; S=P[P.date.isin(ds)]
    L=S[S.side=='LONG']; H=S[S.side=='SHORT']
    rows.append(dict(q=int(q),days=int(len(ds)),dir=round(float(m[byq==q].mean()),4),
        long=round(float(L.net_r.mean()),5),short=round(float(H.net_r.mean()),5),
        lms=round(float(L.net_r.mean()-H.net_r.mean()),5),alln=round(float(S.net_r.mean()),5),
        nl=int(len(L)),ns=int(len(H))))
    print('%-4d %6d %10.4f %+10.5f %+10.5f %+10.5f %+10.5f'%(q,len(ds),m[byq==q].mean(),
        L.net_r.mean(),H.net_r.mean(),L.net_r.mean()-H.net_r.mean(),S.net_r.mean()))
# dirinfo (pre-cost) version -- removes the side-dependent cost asymmetry
print('\nsame quintiles, DIRINFO (pre-cost directional information):')
for q in range(5):
    ds=m.index[byq==q]; S=P[P.date.isin(ds)]
    L=S[S.side=='LONG']; H=S[S.side=='SHORT']
    print('%-4d %6d %10.4f %+10.5f %+10.5f %+10.5f'%(q,len(ds),m[byq==q].mean(),
        L.dirinfo_r.mean(),H.dirinfo_r.mean(),L.dirinfo_r.mean()-H.dirinfo_r.mean()))
json.dump(dict(dircol=DIRCOL,quintiles=rows,
    corr={c:round(float(stats.spearmanr(mkt[c],mkt.pool_drift,nan_policy='omit').statistic),4) for c in ['dir_all','rng_all','dir_idx','rng_idx','rngpos']},
    neg_day_share=float((m<0).mean()), max_dd_proxy=float(dd_path.min())),
   open('direction_window.json','w'),indent=1)
mkt.to_csv('daily_direction_index.csv')
