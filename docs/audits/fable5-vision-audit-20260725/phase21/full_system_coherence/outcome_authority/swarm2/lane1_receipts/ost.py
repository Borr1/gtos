import pandas as pd, numpy as np, json, sys
df=pd.read_pickle('df.pkl')
A,B=1.0,2.0   # engine-booked barrier magnitudes in R (modes verified: stop -1.0, target +2.0)
RES=df[df.lifecycle_label_status.str.startswith('RESOLVED_FILLED')].copy()
RES['leg']=RES.lifecycle_label_status.str.replace('RESOLVED_FILLED_','',regex=False)
rng=np.random.default_rng(20260812)

def cell(d, rcol='R_barrier'):
    n=len(d)
    if n==0: return None
    g=d.groupby('leg')[rcol]
    cnt=g.size(); mu=g.mean()
    pT=cnt.get('TARGET',0)/n; pS=cnt.get('STOP',0)/n; pX=cnt.get('TIME_STOP',0)/n
    mT=mu.get('TARGET',np.nan); mS=mu.get('STOP',np.nan); mX=mu.get('TIME_STOP',np.nan)
    delta=d[rcol].mean()
    mX_fair=(pS*A-pT*B)/pX if pX>0 else np.nan
    LT=pT*(mT-B) if pT>0 else 0.0
    LS=pS*(mS+A) if pS>0 else 0.0
    LX=pX*(mX-mX_fair) if pX>0 else 0.0
    return dict(n=n,pT=pT,pS=pS,pX=pX,mT=mT,mS=mS,mX=mX,mX_fair=mX_fair,
                delta=delta,leg_target=LT,leg_stop=LS,leg_time=LX,
                net=d['R_engine'].mean(), zerocost=d['R_zerocost'].mean(),
                cost=d['cost_r'].mean(), deduct=d['deductible_cost_r'].mean(),
                touch_ratio=pT/(pT+pS) if (pT+pS)>0 else np.nan)

def boot_ci(d, col, B_=2000, cluster='trading_day'):
    """cluster bootstrap on trading_day; returns (lo,hi) of the mean"""
    keys=d[cluster].values
    vals=d[col].values
    uk,inv=np.unique(keys,return_inverse=True)
    order=np.argsort(inv,kind='stable')
    inv_s=inv[order]; vals_s=vals[order]
    bounds=np.searchsorted(inv_s,np.arange(len(uk)+1))
    sums=np.add.reduceat(vals_s,bounds[:-1]); sizes=np.diff(bounds)
    K=len(uk); out=np.empty(B_)
    for b in range(B_):
        idx=rng.integers(0,K,K)
        out[b]=sums[idx].sum()/sizes[idx].sum()
    return float(np.percentile(out,2.5)), float(np.percentile(out,97.5)), float(out.std(ddof=1))

def clustered_se(d,col,cluster='trading_day'):
    g=d.groupby(cluster)[col]
    s=g.sum(); k=g.size()
    n=k.sum(); mbar=d[col].mean(); K=len(s)
    # cluster-robust SE of the mean
    u=(s-k*mbar).values
    var=(K/(K-1))*np.sum(u**2)/n**2
    return float(np.sqrt(var)), K

print("="*100)
print("POOLED, five months, RESOLVED_FILLED only")
for col in ['R_engine','R_barrier','R_zerocost']:
    m=RES[col].mean(); se,K=clustered_se(RES,col)
    lo,hi,_=boot_ci(RES,col)
    print(f"  {col:11s} n={len(RES)} mean={m:+.5f}  cluster-SE(day,K={K})={se:.5f}  t={m/se:+.2f}  95%CI[{lo:+.5f},{hi:+.5f}]")
c=cell(RES)
print("\nOST DECOMPOSITION (gross-at-barrier R_barrier; null: delta=0 exactly under martingale+exact marking)")
print(json.dumps({k:(round(v,6) if isinstance(v,float) else v) for k,v in c.items()},indent=2))
print(f"\n  identity check: legs sum = {c['leg_target']+c['leg_stop']+c['leg_time']:+.6f}   delta = {c['delta']:+.6f}")
RES.to_pickle('res.pkl')
