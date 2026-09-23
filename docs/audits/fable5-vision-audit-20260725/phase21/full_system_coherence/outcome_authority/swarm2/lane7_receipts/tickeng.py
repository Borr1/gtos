import numpy as np, glob, os, gzip, pickle, pandas as pd, json
M1DIR='/Users/borr/.claude/jobs/adb9e69b/tmp/m1'
SYMMAP={'GER40':'GER40_cash','JP225':'JP225_cash','UK100':'UK100_cash','NAS100':'US100_cash','SPX500':'US500_cash'}
def load(broker='FTMO'):
    out={}
    for f in glob.glob(f'{M1DIR}/{broker}_*.npz'):
        z=np.load(f, allow_pickle=True); s=str(z['symbol'])
        o=np.argsort(z['minute_utc'])
        out[s]=dict(t=z['minute_utc'][o].astype('int64'), bh=z['bh'][o],bl=z['bl'][o],ah=z['ah'][o],al=z['al'][o],
                    bo=z['bo'][o],ao=z['ao'][o],bc=z['bc'][o],ac=z['ac'][o],n=z['n'][o],sp=z['sp_sum'][o]/np.maximum(z['n'][o],1))
    return out
def load_lg(months=('jun','jul')):
    rows=[]
    for m in months:
        rows.extend(pickle.load(gzip.open(f'/private/tmp/laneG-walk/lg_{m}.pkl.gz','rb')))
    return rows
if __name__=='__main__':
    T=load('FTMO'); print('symbols',len(T))
    rows=load_lg(); print('lg rows',len(rows))
    lo=min(v['t'][0] for v in T.values()); hi=max(v['t'][-1] for v in T.values())
    print('tick minute range UTC', pd.Timestamp(lo*60,unit='s'), pd.Timestamp(hi*60,unit='s'))
    df=pd.DataFrame([{k:r[k] for k in ('symbol','side','decision_utc','entry_price','stop_price','target_price','risk_price','horizon_min','order_type','spread_at_fill_price','spread_r_row','cost_r','commission_r','swap_r','slippage_r','family','day','key')} for r in rows])
    df['tsym']=df.symbol.map(lambda s: SYMMAP.get(s,s))
    df['dt']=pd.to_datetime(df.decision_utc, utc=True)
    df['min_utc']=(df.dt.dt.tz_convert('UTC').dt.tz_localize(None).astype('datetime64[s]').astype('int64')//60).astype('int64')
    cov=df.tsym.isin(T.keys()) & (df.min_utc>=lo) & (df.min_utc+df.horizon_min.fillna(120)<=hi)
    print('in tick coverage:', int(cov.sum()), '/', len(df))
    print(df[cov].symbol.value_counts().to_dict())
    print('horizon_min dist:', df.horizon_min.value_counts().head(10).to_dict())
    df[cov].to_pickle('lg_cov.pkl')
