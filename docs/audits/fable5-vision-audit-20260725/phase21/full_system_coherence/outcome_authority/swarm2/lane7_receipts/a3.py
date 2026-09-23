import pandas as pd, numpy as np
F=pd.read_pickle('filled.pkl')
S=F[F.lifecycle_label_status=='RESOLVED_FILLED_STOP'].copy()
print("=== STOP-EXIT GROSS: is the entry spread in the path? ===")
print("theory (BarQuote.BID): if entry crosses the spread, gross = -1 - spread_r; if it fills at its own level, gross = -1")
for (ot,sd),g in S.groupby(['proposed_order_type','side']):
    gr=g.gross_r.values; sp=g.spread_r.values
    print(f"{ot:7s} {sd:5s} n={len(g):6d}  mean_gross={gr.mean():+.5f}  mean_spread_r={sp.mean():.5f}  "
          f"mean(gross+1)={np.mean(gr+1):+.5f}  mean(gross+1+spread)={np.mean(gr+1+sp):+.5f}  "
          f"corr(gross+1,-spread)={np.corrcoef(gr+1,-sp)[0,1]:+.3f}")
print()
print("=== TARGET-EXIT GROSS (target=2R by order; feature says 1.5 -- geometry defect) ===")
T=F[F.lifecycle_label_status=='RESOLVED_FILLED_TARGET']
for (ot,sd),g in T.groupby(['proposed_order_type','side']):
    print(f"{ot:7s} {sd:5s} n={len(g):6d}  mean_gross={g.gross_r.mean():+.5f}  mean(gross-2)={np.mean(g.gross_r-2):+.5f}  mean(gross-2+spread)={np.mean(g.gross_r-2+g.spread_r):+.5f}")
print()
print("=== spread_r composition: is LIMIT's lower spread_r a symbol/hour composition effect? ===")
F2=F.copy(); F2['key']=F2.symbol+'|'+F2.utc_hour
piv=F2.pivot_table(index='key', columns='proposed_order_type', values='spread_r', aggfunc='mean')
both=piv.dropna()
print(f'cells with both: {len(both)}; mean LIMIT {both.LIMIT.mean():.5f} vs MARKET {both.MARKET.mean():.5f}; '
      f'mean within-cell diff {(both.LIMIT-both.MARKET).mean():+.6f}')
# reweight LIMIT to MARKET's symbol-hour mix
w=F2[F2.proposed_order_type=='MARKET'].groupby('key').size()
sub=F2[F2.proposed_order_type=='LIMIT'].groupby('key').spread_r.mean()
common=w.index.intersection(sub.index)
print(f'LIMIT spread_r reweighted to MARKET mix: {np.average(sub[common], weights=w[common]):.5f} (raw LIMIT {F2[F2.proposed_order_type=="LIMIT"].spread_r.mean():.5f}, raw MARKET {F2[F2.proposed_order_type=="MARKET"].spread_r.mean():.5f})')
print()
print("=== family composition by order type ===")
print(pd.crosstab(F.origin_family, F.proposed_order_type))
