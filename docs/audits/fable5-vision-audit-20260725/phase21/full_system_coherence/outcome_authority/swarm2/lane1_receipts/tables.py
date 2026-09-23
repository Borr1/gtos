import pandas as pd, numpy as np, json
RES=pd.read_pickle('res.pkl')
RES['edge']=RES.R_engine+RES.cost_r          # realized - fair_value_null   (null = -E[cost_r])
rng=np.random.default_rng(20260812)

def boot(d,col,B=4000,cluster='trading_day'):
    keys=d[cluster].values; vals=d[col].values
    uk,inv=np.unique(keys,return_inverse=True)
    o=np.argsort(inv,kind='stable'); inv_s=inv[o]; v_s=vals[o]
    b=np.searchsorted(inv_s,np.arange(len(uk)+1))
    sums=np.add.reduceat(v_s,b[:-1]); sizes=np.diff(b); K=len(uk)
    idx=rng.integers(0,K,(B,K))
    out=sums[idx].sum(1)/sizes[idx].sum(1)
    return float(np.percentile(out,2.5)),float(np.percentile(out,97.5))

def tab(key,minn=800,fname=None):
    rows=[]
    for k,d in RES.groupby(key,observed=True):
        if len(d)<minn: continue
        lo,hi=boot(d,'edge')
        lv=d.leg.value_counts(normalize=True)
        rows.append(dict(cell=str(k),n=len(d),
            realized_net=d.R_engine.mean(), fair_null=-d.cost_r.mean(),
            edge=d.edge.mean(), lo=lo, hi=hi, sig=(lo>0)or(hi<0),
            gross=d.R_barrier.mean(), cost=d.cost_r.mean(),
            pT=lv.get('TARGET',0),pS=lv.get('STOP',0),pX=lv.get('TIME_STOP',0),
            w=d.stop_distance_atr.median()))
    t=pd.DataFrame(rows).sort_values('edge',ascending=False)
    if fname: t.to_csv(fname,index=False)
    return t

pd.set_option('display.width',250)
def show(t,title,n=40):
    print("\n"+"="*130); print(title)
    print(f"{'cell':<42}{'n':>7}{'realized':>10}{'fair_null':>11}{'EDGE':>9}{'95% CI':>22}{'sig':>5}{'cost':>7}{'pT':>6}{'pS':>6}{'pX':>6}{'w':>6}")
    for _,r in t.head(n).iterrows():
        print(f"{r.cell:<42}{r.n:7d}{r.realized_net:+10.4f}{r.fair_null:+11.4f}{r.edge:+9.4f}  [{r.lo:+7.4f},{r.hi:+7.4f}]{'  *' if r.sig else '   '}{r.cost:7.3f}{r.pT:6.3f}{r.pS:6.3f}{r.pX:6.3f}{r.w:6.2f}")

for key,title,mn in [('origin_family','A1. BY ORIGIN FAMILY',800),
                     ('symbol','A2. BY SYMBOL',800),
                     ('utc_session','A3. BY SESSION',800),
                     ('month','A4. BY MONTH',800),
                     ('proposed_order_type','A5. BY ORDER TYPE',800)]:
    t=tab(key,mn,f"edge_{key}.csv"); show(t,title)
