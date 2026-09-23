"""B6 core: master frame + causal panel construction. Read-only on the sealed cache."""
import gzip, pickle, math, json, os
import numpy as np, pandas as pd

CACHE='/private/tmp/w21-puzzle-cache'
OUT=os.path.dirname(os.path.abspath(__file__))
MONTHS=['feb','apr','may','jun','jul']
MAX_COST_R=0.20
STATE={'RESOLVED_NO_FILL':'NO_FILL','RESOLVED_FILLED_TARGET':'TARGET',
       'RESOLVED_FILLED_STOP':'STOP','RESOLVED_FILLED_TIME_STOP':'TIME_STOP'}

def build_master(path=None):
    path = path or os.path.join(OUT,'master.parquet')
    if os.path.exists(path):
        return pd.read_parquet(path)
    frames=[]
    for mo in MONTHS:
        df=pd.DataFrame(pickle.load(gzip.open(f'{CACHE}/rows_{mo}.pkl.gz','rb')))
        df['month']=mo; frames.append(df)
    df=pd.concat(frames, ignore_index=True)
    df['state']=df['lifecycle_label_status'].map(STATE)
    df['censored']=df['state'].isna()
    df['elig']=df['predecision_geometry_valid'].astype(bool)&np.isfinite(df['cost_r'])&(df['cost_r']<=MAX_COST_R)
    df['filled']=df['state'].isin(['TARGET','STOP','TIME_STOP'])
    df['resolved']=df['state'].notna()
    df['net_r']=pd.to_numeric(df['terminal_net_r'],errors='coerce')
    df['gross_r']=df['net_r']+df['deductible_cost_r']
    df['dirinfo_r']=df['net_r']+df['cost_r']
    df['is_market']=(df['proposed_order_type']=='MARKET')
    df['hour']=df['utc_hour'].astype(int)
    df['dow']=df['weekday'].astype(int)
    df['day']=df['trading_day']
    df['date']=pd.to_datetime(df['trading_day'])
    df['pred']=pd.to_numeric(df['pred_month_boundary'],errors='coerce')
    # decision instant, from decision_window_id ('timewarp:<iso>')
    df['dts']=pd.to_datetime(df['decision_window_id'].str.replace('timewarp:','',regex=False),
                             format='ISO8601', utc=True)
    df['is_long']=(df['side']=='LONG').astype(float)
    df.to_parquet(path,index=False)
    return df

REG_AGG=dict(vol=('atr14_over_atr50','median'),
             ccvol=('close_to_close_vol_8_over_48','median'),
             comp=('compression_ratio_prior_bar','median'),
             spread=('spread_r','median'),
             cost=('cost_r','median'),
             risk=('risk_over_atr','median'),
             rngpos=('close_position_in_lookback_range','median'),
             bodyatr=('trigger_bar_body_atr','median'),
             dhi=('dist_to_prior_high20_atr','median'),
             dlo=('dist_to_prior_low20_atr','median'))

def day_regime(ELIG):
    """Day-level regime from ALL eligible candidates that day (Lane 6 original; NON-causal within day)."""
    d=ELIG.groupby('date',observed=True).agg(**REG_AGG)
    ts=ELIG.groupby('date',observed=True).trend_state_m15
    d['trendshare']=ts.apply(lambda s: s.isin(['strong_up','strong_down']).mean())
    d['upshare']=ts.apply(lambda s: s.isin(['strong_up','up']).mean())
    d['nc']=ELIG.groupby('date',observed=True).size()
    d=d.sort_index(); d['dow']=d.index.dayofweek
    return d

REGCOLS=['vol','ccvol','comp','spread','cost','risk','rngpos','bodyatr','dhi','dlo',
         'trendshare','upshare','dow']
LANE6_REG=['vol','ccvol','comp','spread','cost','risk','trendshare','upshare','dow']

def wf_ridge(X, y, w, d, ud, alpha=10.0, min_train_days=25, min_train_rows=100,
             causal_scaler=True, target=None):
    """Expanding-window walk-forward ridge. causal_scaler=True standardises on TRAIN ONLY."""
    from sklearn.linear_model import Ridge
    tgt = y if target is None else target
    pred=np.full(len(y),np.nan)
    for i,dd in enumerate(ud):
        if i<min_train_days: continue
        tr=(d<dd); te=(d==dd)
        msk=tr&~np.isnan(tgt)
        if msk.sum()<min_train_rows: continue
        Xtr=X[msk]; Xte=X[te]
        if causal_scaler:
            mu=Xtr.mean(0); sd=Xtr.std(0); sd[sd<1e-12]=1.0
            Xtr=(Xtr-mu)/sd; Xte=(Xte-mu)/sd
        m=Ridge(alpha=alpha); m.fit(Xtr,tgt[msk],sample_weight=w[msk])
        pred[te]=m.predict(Xte)
    return pred

def day_cluster_se(vals, days):
    vals=np.asarray(vals,dtype=float); days=np.asarray(days)
    mu=vals.mean()
    s=pd.Series(vals-mu).groupby(pd.Series(days)).sum().to_numpy()
    G=len(s); n=len(vals)
    if G<2: return float('nan')
    return math.sqrt((s**2).sum()/n**2*(G/(G-1)))

def day_boot_mean(vals, days, B=4000, seed=0):
    rng=np.random.default_rng(seed)
    g=pd.DataFrame({'v':np.asarray(vals,dtype=float),'d':np.asarray(days)}).groupby('d').v.agg(['sum','size'])
    S=g['sum'].to_numpy(); N=g['size'].to_numpy(); n=len(S)
    idx=rng.integers(0,n,size=(B,n))
    return S[idx].sum(1)/N[idx].sum(1)
