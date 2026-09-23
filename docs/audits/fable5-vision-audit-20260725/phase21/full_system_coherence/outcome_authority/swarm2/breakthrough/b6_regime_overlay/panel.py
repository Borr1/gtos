"""B6 panel builder: family x day panel with a declared CAUSALITY LEVEL for the regime block."""
import numpy as np, pandas as pd, b6_core as C

def make_panel(df, regime_lag=0, reg_cols=None, inter_dials=('vol','ccvol','trendshare','spread'),
               min_fills=5, extra_regime=False):
    """regime_lag=0 -> Lane 6 original (same-day aggregates, NOT knowable at day open)
       regime_lag=1 -> causal: day d uses day d-1 aggregates (knowable at day d open)"""
    reg_cols = list(reg_cols or C.LANE6_REG)
    P=df[df.elig&df.filled].copy()
    ELIG=df[df.elig].copy()
    day=C.day_regime(ELIG)
    if extra_regime:
        # causal derived state: 5-day trailing level and 1-day change of each dial (strictly prior)
        for c in ['vol','ccvol','spread','cost','trendshare','upshare','rngpos','risk']:
            day[c+'_m5']=day[c].shift(1).rolling(5,min_periods=2).mean()
            day[c+'_d1']=day[c]-day[c].shift(1)
        day['nc_m5']=day['nc'].shift(1).rolling(5,min_periods=2).mean()
        day['nc_rel']=day['nc']/day['nc_m5']
    if regime_lag>0:
        keep=['dow']
        lagged=day.drop(columns=[c for c in keep if c in day.columns]).shift(regime_lag)
        day=pd.concat([lagged, day[keep]],axis=1)
    fd=P.groupby(['origin_family','date'],observed=True).agg(
        n=('net_r','size'),y=('net_r','mean'),ydi=('dirinfo_r','mean'),
        ylong=('net_r','mean')).reset_index()
    # side-split targets
    sd=P.groupby(['origin_family','date','side'],observed=True).net_r.agg(['size','mean']).reset_index()
    for sside in ('LONG','SHORT'):
        t=sd[sd.side==sside].set_index(['origin_family','date'])
        fd['n_'+sside]=fd.set_index(['origin_family','date']).index.map(t['size']).astype(float)
        fd['y_'+sside]=fd.set_index(['origin_family','date']).index.map(t['mean']).astype(float)
    fd=fd.drop(columns=['ylong'])
    fd=fd[fd.n>=min_fills].sort_values(['origin_family','date']).reset_index(drop=True)
    for L in (5,10,20):
        fd['mom%d'%L]=fd.groupby('origin_family',observed=True).y.transform(
            lambda s: s.shift(1).rolling(L,min_periods=3).mean())
    poolday=fd.groupby('date',observed=True).y.mean().sort_index()
    fd['poolmom10']=fd.date.map(poolday.shift(1).rolling(10,min_periods=3).mean())
    fd['fam_prior_mean']=fd.groupby('origin_family',observed=True).y.transform(
        lambda s: s.shift(1).expanding(min_periods=5).mean())
    fd=fd.merge(day.reset_index(),on='date',how='left')
    fams=sorted(fd.origin_family.unique())
    FAM=[]
    for f in fams:
        fd['f_'+f]=(fd.origin_family==f).astype(float); FAM.append('f_'+f)
    MOM=['mom5','mom10','mom20','poolmom10']
    REG=[c for c in reg_cols if c in fd.columns]
    INT=[]
    for f in fams:
        for r in inter_dials:
            if r not in fd.columns: continue
            c='x_%s_%s'%(f,r); fd[c]=fd['f_'+f]*fd[r]; INT.append(c)
    fd=fd.dropna(subset=['mom20','poolmom10']).sort_values('date').reset_index(drop=True)
    return fd, dict(FAM=FAM,MOM=MOM,REG=REG,INT=INT,fams=fams)
