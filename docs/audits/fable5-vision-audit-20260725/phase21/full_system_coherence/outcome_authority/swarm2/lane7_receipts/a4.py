import pandas as pd, numpy as np, json
df=pd.read_pickle('pool.pkl'); F=pd.read_pickle('filled.pkl')
# CORRECTED pre-cost gross: MARKET crosses the spread (in path); LIMIT fills at its own level (not in path)
F['precost_r']=np.where(F.proposed_order_type=='MARKET', F.gross_r+F.spread_r, F.gross_r)
F['spread_paid_r']=np.where(F.proposed_order_type=='MARKET', F.spread_r, 0.0)
F['allin_cost_r']=F.spread_paid_r+F.commission_r+F.swap_cost_r+F.expected_slippage_r
out={}
for lbl,sub in [('POOLED',F)]+[(k,g) for k,g in F.groupby('proposed_order_type')]:
    n=len(sub); se=lambda s: s.std(ddof=1)/np.sqrt(len(s))
    out[lbl]=dict(n=int(n), E_precost=float(sub.precost_r.mean()), precost_CI95=[float(sub.precost_r.mean()-1.96*se(sub.precost_r)),float(sub.precost_r.mean()+1.96*se(sub.precost_r))],
      E_spread_paid=float(sub.spread_paid_r.mean()), E_comm=float(sub.commission_r.mean()), E_swap=float(sub.swap_cost_r.mean()),
      E_slip=float(sub.expected_slippage_r.mean()), E_allin_cost=float(sub.allin_cost_r.mean()),
      E_net=float(sub.terminal_net_r.mean()), net_CI95=[float(sub.terminal_net_r.mean()-1.96*se(sub.terminal_net_r)),float(sub.terminal_net_r.mean()+1.96*se(sub.terminal_net_r))],
      total_net_R=float(sub.terminal_net_r.sum()), total_cost_R=float(sub.allin_cost_r.sum()), total_precost_R=float(sub.precost_r.sum()))
print(json.dumps(out,indent=1))
# identity check
chk=F.precost_r-F.allin_cost_r-F.terminal_net_r
print('identity precost-cost-net max|err|', float(np.abs(chk).max()))
F.to_pickle('filled.pkl')
