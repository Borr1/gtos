"""B6 step 9 — COMPOSITION. Build a P(fill) x E[net|fill] decision statistic (lane-2 shape) and a
directly-retrained selector (lane-3 shape) on the same walk-forward protocol, then stack the regime
interaction block as a feature and report whether it ADDS or OVERLAPS. Says which component works."""
import numpy as np, pandas as pd, json, math, warnings
warnings.filterwarnings('ignore')
from scipy import stats
from sklearn.linear_model import Ridge, LogisticRegression
import b6_core as C
from panel import make_panel
df=C.build_master()
R=df[df.elig&df.resolved].copy().sort_values('dts').reset_index(drop=True)
R['y_all']=R.net_r.fillna(0.0)             # economic outcome of PROPOSING (0 if no fill)
R['fill']=R.filled.astype(int)
print('eligible & resolved n=%d | fill rate %.4f | MARKET %.3f  LIMIT %.3f'%(
  len(R),R.fill.mean(),R[R.is_market].fill.mean(),R[~R.is_market].fill.mean()))
print('E[y_all]=%+0.5f  E[net|fill]=%+0.5f'%(R.y_all.mean(),R[R.fill==1].net_r.mean()))

NUM=['cost_r','spread_r','commission_r','swap_cost_r','risk_over_atr','atr14_over_atr50',
     'close_to_close_vol_8_over_48','compression_ratio_prior_bar','close_position_in_lookback_range',
     'trigger_bar_body_atr','trigger_bar_range_atr','dist_to_prior_high20_atr','dist_to_prior_low20_atr',
     'distance_to_limit_atr','distance_to_limit_risk','stop_distance_atr','target_distance_atr','hour','dow']
fams=sorted(R.origin_family.unique())
for f in fams: R['f_'+f]=(R.origin_family==f).astype(float)
FAM=['f_'+f for f in fams]
R['is_long']=(R.side=='LONG').astype(float); R['is_mkt']=R.is_market.astype(float)
BASE=NUM+FAM+['is_long','is_mkt']

# regime blocks joined on (family, date): causal (lag-1) and non-causal (Lane 6)
def regblock(lag):
    fd,B=make_panel(df,regime_lag=lag)
    cols=['origin_family','date']+B['REG']+B['INT']
    return fd[cols].copy(),B['REG']+B['INT']
rc,RCOLS=regblock(1); rn,NCOLS=regblock(0)
rc=rc.rename(columns={c:'c_'+c for c in RCOLS}); RC=['c_'+c for c in RCOLS]
rn=rn.rename(columns={c:'n_'+c for c in NCOLS}); NC=['n_'+c for c in NCOLS]
R=R.merge(rc,on=['origin_family','date'],how='left').merge(rn,on=['origin_family','date'],how='left')

d=R.date.to_numpy(); ud=np.array(sorted(set(d))); MINDAY=25
def wf_two_stage(cols, use_fill_stage=True):
    """returns per-row decision statistic, OOS"""
    X=R[cols].fillna(0.0).to_numpy(float)
    yf=R.fill.to_numpy(float); yn=R.net_r.to_numpy(float); ya=R.y_all.to_numpy(float)
    out=np.full(len(R),np.nan)
    for i,dd in enumerate(ud):
        if i<MINDAY: continue
        tr=d<dd; te=d==dd
        if tr.sum()<2000: continue
        Xtr=X[tr]; mu=Xtr.mean(0); sd=Xtr.std(0); sd[sd<1e-12]=1.
        Xtr=(Xtr-mu)/sd; Xte=(X[te]-mu)/sd
        if use_fill_stage:
            lf=LogisticRegression(C=0.1,max_iter=300); lf.fit(Xtr,yf[tr])
            pf=lf.predict_proba(Xte)[:,1]
            fm=tr&(R.fill.to_numpy()==1)
            Xf=(X[fm]-mu)/sd
            me=Ridge(alpha=100.); me.fit(Xf,yn[fm])
            out[te]=pf*me.predict(Xte)
        else:
            m=Ridge(alpha=100.); m.fit(Xtr,ya[tr]); out[te]=m.predict(Xte)
    return out
ARMS={'L3-shape  direct ridge on E[net_all]':(BASE,False),
      'L2-shape  P(fill) x E[net|fill]':(BASE,True),
      'L2 + CAUSAL regime block':(BASE+RC,True),
      'L2 + NON-CAUSAL regime block (artifact)':(BASE+NC,True)}
res={}
print('\n%-42s %8s %9s %10s %11s %11s %11s'%('arm','n_oos','rho','p','top-10% R','top-20% R','all R'))
store={}
for name,(cols,two) in ARMS.items():
    p=wf_two_stage(cols,two); ok=~np.isnan(p); store[name]=p
    ya=R.y_all.to_numpy()
    rho=stats.spearmanr(p[ok],ya[ok])
    q90=pd.Series(p[ok]).groupby(pd.Series(d[ok])).transform(lambda s:s.quantile(0.90)).to_numpy()
    q80=pd.Series(p[ok]).groupby(pd.Series(d[ok])).transform(lambda s:s.quantile(0.80)).to_numpy()
    idx=np.where(ok)[0]
    t10=ya[idx][p[ok]>=q90]; t20=ya[idx][p[ok]>=q80]
    res[name]=dict(n=int(ok.sum()),rho=round(float(rho.statistic),5),p=float('%.3g'%rho.pvalue),
       top10=round(float(t10.mean()),5),n10=int(len(t10)),top20=round(float(t20.mean()),5),
       allr=round(float(ya[ok].mean()),5))
    print('%-42s %8d %+9.4f %10s %+11.5f %+11.5f %+11.5f'%(name,ok.sum(),rho.statistic,'%.2g'%rho.pvalue,
       t10.mean(),t20.mean(),ya[ok].mean()))
# incremental value of each block, day-clustered
print('\nINCREMENTAL: does the regime block add to the L2 statistic? (top-decile book, day-bootstrap)')
ok=~np.isnan(store['L2-shape  P(fill) x E[net|fill]'])
for name in ['L2-shape  P(fill) x E[net|fill]','L2 + CAUSAL regime block','L2 + NON-CAUSAL regime block (artifact)']:
    p=store[name]; o=ok&~np.isnan(p)
    q=pd.Series(p[o]).groupby(pd.Series(d[o])).transform(lambda s:s.quantile(0.90)).to_numpy()
    sel=np.where(o)[0][p[o]>=q]
    v=R.y_all.to_numpy()[sel]; dd=d[sel]
    b=C.day_boot_mean(v,dd,seed=41)
    print('  %-42s top-decile n=%5d  R %+0.5f  95%%CI [%+0.5f,%+0.5f] P(<=0) %.4f'%(
      name,len(v),v.mean(),np.quantile(b,.025),np.quantile(b,.975),(b<=0).mean()))
json.dump(res,open('compose.json','w'),indent=1)
