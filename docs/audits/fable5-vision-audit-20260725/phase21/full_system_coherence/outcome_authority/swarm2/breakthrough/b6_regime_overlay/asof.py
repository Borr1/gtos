"""B6 step 3 — THE DECISIVE CAUSALITY MEASUREMENT.
For cutoff hour h: regime = trailing-24h median over eligible candidates strictly BEFORE (day, h:00 UTC);
panel = family-day rows built only from candidates at hour >= h. Fully causal by construction.
Control arm: same hour>=h panel but Lane-6's whole-day (non-causal) regime, to separate
'the causality fix' from 'the subsetting'."""
import numpy as np, pandas as pd, json, warnings, sys, math
warnings.filterwarnings('ignore')
from scipy import stats
import b6_core as C

df=C.build_master()
E=df[df.elig].copy().sort_values('dts').reset_index(drop=True)
P=df[df.elig&df.filled].copy()
DIALS=['atr14_over_atr50','close_to_close_vol_8_over_48','compression_ratio_prior_bar','spread_r',
       'cost_r','risk_over_atr','close_position_in_lookback_range','trigger_bar_body_atr',
       'dist_to_prior_high20_atr','dist_to_prior_low20_atr']
NAMES=['vol','ccvol','comp','spread','cost','risk','rngpos','bodyatr','dhi','dlo']
M=E[DIALS].to_numpy(float)
tsu=E.trend_state_m15.isin(['strong_up','strong_down']).to_numpy(float)
tup=E.trend_state_m15.isin(['strong_up','up']).to_numpy(float)
ts=E.dts.to_numpy()
days=np.array(sorted(df[df.elig].date.unique()))

def trailing_regime(h):
    """median of each dial over eligible rows in [cut-24h, cut) where cut = day h:00 UTC"""
    cuts=pd.to_datetime(days)+pd.Timedelta(hours=h)
    cuts=cuts.tz_localize('UTC')
    lo=np.searchsorted(ts,(cuts-pd.Timedelta(hours=24)).to_numpy(),side='left')
    hi=np.searchsorted(ts,cuts.to_numpy(),side='left')
    out={}
    rows=[]
    for i in range(len(days)):
        a,b=lo[i],hi[i]
        if b-a<50: rows.append([np.nan]*(len(NAMES)+3)); continue
        med=np.nanmedian(M[a:b],axis=0)
        rows.append(list(med)+[tsu[a:b].mean(),tup[a:b].mean(),float(b-a)])
    R=pd.DataFrame(rows,columns=NAMES+['trendshare','upshare','nc'],index=pd.to_datetime(days))
    R.index.name='date'; R['dow']=R.index.dayofweek
    return R

def build_panel(regime, hmin, min_fills=5):
    Q=P[P.hour>=hmin]
    fd=Q.groupby(['origin_family','date'],observed=True).agg(n=('net_r','size'),y=('net_r','mean')).reset_index()
    fd=fd[fd.n>=min_fills].sort_values(['origin_family','date'])
    for L in (5,10,20):
        fd['mom%d'%L]=fd.groupby('origin_family',observed=True).y.transform(lambda s: s.shift(1).rolling(L,min_periods=3).mean())
    poolday=fd.groupby('date',observed=True).y.mean().sort_index()
    fd['poolmom10']=fd.date.map(poolday.shift(1).rolling(10,min_periods=3).mean())
    fd=fd.merge(regime.reset_index(),on='date',how='left')
    fams=sorted(fd.origin_family.unique())
    FAM=[];INT=[]
    for f in fams:
        fd['f_'+f]=(fd.origin_family==f).astype(float); FAM.append('f_'+f)
        for r in ('vol','ccvol','trendshare','spread'):
            c='x_%s_%s'%(f,r); fd[c]=fd['f_'+f]*fd[r]; INT.append(c)
    REG=['vol','ccvol','comp','spread','cost','risk','trendshare','upshare','dow']
    fd=fd.dropna(subset=['mom20','poolmom10','vol']).sort_values('date').reset_index(drop=True)
    return fd,dict(FAM=FAM,REG=REG,INT=INT,MOM=['mom5','mom10','mom20','poolmom10'])

def run(fd,cols,alpha=10.0):
    X=fd[cols].fillna(0.0).to_numpy(float); y=fd.y.to_numpy(float)
    w=fd.n.to_numpy(float); d=fd.date.to_numpy(); ud=np.array(sorted(set(d)))
    p=C.wf_ridge(X,y,w,d,ud,alpha=alpha,causal_scaler=True)
    ok=~np.isnan(p)
    if ok.sum()<50: return None
    rho=stats.spearmanr(p[ok],y[ok]); sel=ok&(p>0)
    rs=np.average(y[sel],weights=w[sel]) if sel.sum()>3 else np.nan
    ra=np.average(y[ok],weights=w[ok])
    return dict(n_oos=int(ok.sum()),rho=round(float(rho.statistic),5),p=float('%.3g'%rho.pvalue),
                trades=int(w[sel].sum()),trades_all=int(w[ok].sum()),
                r_sel=round(float(rs),5),r_all=round(float(ra),5),delta=round(float(rs-ra),5))

# whole-day (non-causal) regime, Lane-6 style
ELIG=df[df.elig].copy()
wd=C.day_regime(ELIG)[['vol','ccvol','comp','spread','cost','risk','trendshare','upshare','nc','dow']]

print('%-6s %-28s %6s %8s %10s %8s %9s'%('h','regime source','n_oos','rho','p','trades','delta'))
out=[]
for h in [0,2,4,6,8,10,12,14,16]:
    Rc=trailing_regime(h)
    fdc,Bc=build_panel(Rc,h)
    rc=run(fdc,Bc['REG']+Bc['INT'])
    fdn,Bn=build_panel(wd,h)
    rn=run(fdn,Bn['REG']+Bn['INT'])
    if rc: print('h>=%-3d %-28s %6d %+8.4f %10s %8d %+9.5f'%(h,'CAUSAL trailing-24h',rc['n_oos'],rc['rho'],rc['p'],rc['trades'],rc['delta']))
    if rn: print('%-6s %-28s %6d %+8.4f %10s %8d %+9.5f'%('',' control: whole-day (L6)',rn['n_oos'],rn['rho'],rn['p'],rn['trades'],rn['delta']))
    out.append(dict(h=h,causal=rc,noncausal=rn))
json.dump(out,open('asof_curve.json','w'),indent=1)
