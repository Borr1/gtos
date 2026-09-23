import pandas as pd, numpy as np
RES=pd.read_pickle('res.pkl')
rng=np.random.default_rng(20260812)
def cse(d,col,cluster='trading_day'):
    g=d.groupby(cluster)[col]; s=g.sum(); k=g.size(); n=k.sum(); mbar=d[col].mean(); K=len(s)
    u=(s-k*mbar).values
    return float(np.sqrt((K/(K-1))*np.sum(u**2)/n**2))
# does cost_r scale as 1/stop width in price?
RES['risk_price_proxy']=RES['risk_fraction_of_entry']            # |entry-stop|/entry
RES['w']=RES['stop_distance_atr']
q=pd.qcut(RES['w'],10,labels=False,duplicates='drop')
print(f"{'decile':>6} {'n':>7} {'w_med':>7} {'riskfrac':>9} {'cost_r':>8} {'spread_r':>8} {'R_zero':>9} {'seZ':>7} {'R_barr':>9} {'R_eng':>9} {'seE':>7} {'pT':>6} {'pS':>6} {'pX':>6}")
rows=[]
for i in sorted(q.dropna().unique()):
    d=RES[q==i]
    lv=d.leg.value_counts(normalize=True)
    r=dict(dec=int(i),n=len(d),w_med=d.w.median(),riskfrac=d.risk_fraction_of_entry.median(),
           cost=d.cost_r.mean(),spread=d.spread_r.mean(),
           Rz=d.R_zerocost.mean(),seZ=cse(d,'R_zerocost'),
           Rb=d.R_barrier.mean(),Re=d.R_engine.mean(),seE=cse(d,'R_engine'),
           pT=lv.get('TARGET',0),pS=lv.get('STOP',0),pX=lv.get('TIME_STOP',0))
    rows.append(r)
    print(f"{r['dec']:6d} {r['n']:7d} {r['w_med']:7.3f} {r['riskfrac']:9.5f} {r['cost']:8.4f} {r['spread']:8.4f} {r['Rz']:+9.4f} {r['seZ']:7.4f} {r['Rb']:+9.4f} {r['Re']:+9.4f} {r['seE']:7.4f} {r['pT']:6.3f} {r['pS']:6.3f} {r['pX']:6.3f}")
w=np.array([r['w_med'] for r in rows]); c=np.array([r['cost'] for r in rows])
print("\ncost_r * stop_distance_atr (should be ~const if cost_r ∝ 1/width):", np.round(w*c,4))
print("corr(log cost_r, log width) =", np.corrcoef(np.log(w),np.log(c))[0,1].round(4),
      " slope=",np.polyfit(np.log(w),np.log(c),1)[0].round(4))
# Rz flat?
z=np.array([r['Rz'] for r in rows]); sz=np.array([r['seZ'] for r in rows])
print("R_zerocost across width deciles: mean %.4f  spread %.4f ; weighted-chi2 vs const:"%(z.mean(),z.std()),
      round(float(np.sum(((z-np.average(z,weights=1/sz**2))/sz)**2)),2), "on 9 df")
