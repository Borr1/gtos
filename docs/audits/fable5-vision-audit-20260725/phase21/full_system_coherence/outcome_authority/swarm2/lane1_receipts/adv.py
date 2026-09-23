import pandas as pd, numpy as np, gzip, pickle
from scipy import stats
RES=pd.read_pickle('res.pkl'); RES['edge']=RES.R_engine+RES.cost_r
rng=np.random.default_rng(7)
def boot(d,col,B=4000,cluster='trading_day'):
    keys=d[cluster].values; vals=d[col].values
    uk,inv=np.unique(keys,return_inverse=True); o=np.argsort(inv,kind='stable')
    inv_s=inv[o]; v_s=vals[o]; b=np.searchsorted(inv_s,np.arange(len(uk)+1))
    sums=np.add.reduceat(v_s,b[:-1]); sizes=np.diff(b); K=len(uk)
    idx=rng.integers(0,K,(B,K)); out=sums[idx].sum(1)/sizes[idx].sum(1)
    return float(np.percentile(out,2.5)),float(np.percentile(out,97.5))

print("=== ADV-1: edge = gross + spread_r  => independent of slippage/swap/commission model ===")
print("  max |edge - (R_barrier + spread_r)| =", float((RES.edge-(RES.R_barrier+RES.spread_r)).abs().max()))
print("  => the edge depends ONLY on the spread model, not the commission/swap/slippage model.")

print("\n=== ADV-2: is spread_r exactly the spread the labeler charged? (MARKET rows, lane-G price cache) ===")
tot=0; bad=0; mx=0.0
for m in ['feb','apr','may','jun','jul']:
    rows=pickle.load(gzip.open(f'/private/tmp/laneG-walk/lg_{m}.pkl.gz','rb'))
    for r in rows:
        rp=r.get('risk_price'); sp=r.get('spread_at_fill_price'); sr=r.get('spread_r_row')
        if rp and sp is not None and sr is not None:
            tot+=1; d=abs(sr-sp/rp); mx=max(mx,d)
            if d>1e-9: bad+=1
print(f"  n={tot}  rows where spread_r != spread_at_fill/risk_price: {bad}   max|diff|={mx:.3e}")

print("\n=== ADV-3: LONG vs SHORT.  For SHORTs the spread is paid at the EXIT bar, not the fill bar. ===")
print("    If spread_r (fill-bar) mis-states the short null, LONG and SHORT edges will diverge.")
for s in ['LONG','SHORT']:
    d=RES[RES.side==s]; lo,hi=boot(d,'edge')
    print(f"  {s:6s} n={len(d):6d} edge={d.edge.mean():+.5f} CI[{lo:+.5f},{hi:+.5f}] spread_r={d.spread_r.mean():.4f}")
dl=RES[RES.side=='LONG'].edge.mean(); ds=RES[RES.side=='SHORT'].edge.mean()
print(f"  LONG-SHORT gap = {dl-ds:+.5f} R")

print("\n=== ADV-4: is the 'edge' just cost_r overstatement? cell-level corr(edge, cost) ===")
for key in ['symbol','origin_family']:
    t=pd.read_csv(f'edge_{key}.csv')
    r,p=stats.pearsonr(t.cost,t.edge)
    rs,ps=stats.spearmanr(t.cost,t.edge)
    print(f"  {key:15s} k={len(t):3d}  pearson r={r:+.4f} p={p:.4f}   spearman={rs:+.4f} p={ps:.4f}")
print("  (a strong POSITIVE correlation would mean the edge is manufactured by an inflated spread model)")

print("\n=== ADV-5: edge with spread_r HALVED (spread model overstated 2x) and DOUBLED ===")
for f,lab in [(0.5,'half spread'),(1.0,'as modelled'),(2.0,'double spread')]:
    e=RES.R_barrier+f*RES.spread_r
    print(f"  {lab:14s} edge={e.mean():+.5f}")

print("\n=== ADV-6: five-month sign consistency + leave-one-month-out ===")
for m in ['feb','apr','may','jun','jul']:
    d=RES[RES.month!=m]; lo,hi=boot(d,'edge')
    print(f"  drop {m}: edge={d.edge.mean():+.5f} CI[{lo:+.5f},{hi:+.5f}] n={len(d)}")

print("\n=== ADV-7: LIMIT edge robustness — drop each month, and split by censor-rate of the day ===")
L=RES[RES.proposed_order_type=='LIMIT']
for m in ['feb','apr','may','jun','jul']:
    d=L[L.month!=m]; lo,hi=boot(d,'edge')
    print(f"  LIMIT drop {m}: edge={d.edge.mean():+.5f} CI[{lo:+.5f},{hi:+.5f}]")
