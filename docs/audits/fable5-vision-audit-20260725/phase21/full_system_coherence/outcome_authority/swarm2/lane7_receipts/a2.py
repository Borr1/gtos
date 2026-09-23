import pandas as pd, numpy as np, json
pd.set_option('display.width',250); pd.set_option('display.max_columns',60)
df=pd.read_pickle('pool.pkl')
F=df[df.lifecycle_label_status.str.startswith('RESOLVED_FILLED')].copy()
F['gross_r']=F.terminal_net_r+F.deductible_cost_r          # exact identity from candidate_funnel_analysis.py:172
F['precost_r']=F.gross_r+F.spread_r                         # approx: spread is in the path (Lane G)
F['allin_cost_r']=F.cost_r
n=len(F)
hdr={'n_filled':int(n),
 'E_precost_gross_R': float(F.precost_r.mean()),
 'E_path_gross_R(after spread)': float(F.gross_r.mean()),
 'E_net_R': float(F.terminal_net_r.mean()),
 'E_allin_cost_R': float(F.allin_cost_r.mean()),
 'components': {c: float(F[c].mean()) for c in ['spread_r','commission_r','swap_cost_r','expected_slippage_r']},
 'total_R_burned': {c: float(F[c].sum()) for c in ['spread_r','commission_r','swap_cost_r','expected_slippage_r']},
 'total_cost_R': float(F.cost_r.sum()), 'total_net_R': float(F.terminal_net_r.sum()),
 'total_precost_gross_R': float(F.precost_r.sum()),
 'cost_as_pct_of_precost_gross': float(F.cost_r.sum()/F.precost_r.sum()*100),
}
# CI on precost gross
se=F.precost_r.std(ddof=1)/np.sqrt(n); hdr['E_precost_gross_CI95']=[float(F.precost_r.mean()-1.96*se), float(F.precost_r.mean()+1.96*se)]
se2=F.terminal_net_r.std(ddof=1)/np.sqrt(n); hdr['E_net_CI95']=[float(F.terminal_net_r.mean()-1.96*se2), float(F.terminal_net_r.mean()+1.96*se2)]
print(json.dumps(hdr,indent=1))
print()
print("=== BY ORDER TYPE (filled) ===")
g=F.groupby('proposed_order_type').agg(n=('cost_r','size'), spread=('spread_r','mean'), comm=('commission_r','mean'),
    swap=('swap_cost_r','mean'), slip=('expected_slippage_r','mean'), cost=('cost_r','mean'),
    precost=('precost_r','mean'), net=('terminal_net_r','mean'), net_sum=('terminal_net_r','sum'), cost_sum=('cost_r','sum'))
print(g.round(5))
print()
print("=== FILL RATES BY ORDER TYPE (all candidates) ===")
tot=df.groupby('proposed_order_type').size()
fil=F.groupby('proposed_order_type').size()
nof=df[df.lifecycle_label_status=='RESOLVED_NO_FILL'].groupby('proposed_order_type').size()
cen=df[df.lifecycle_label_status.str.startswith('CENSORED')].groupby('proposed_order_type').size()
print(pd.DataFrame({'total':tot,'filled':fil,'no_fill':nof,'censored':cen,'fill_rate_of_total':(fil/tot).round(4),
                    'fill_rate_of_resolved':(fil/(fil+nof)).round(4)}))
print()
print("=== OUTCOME MIX BY ORDER TYPE ===")
ct=pd.crosstab(F.proposed_order_type, F.lifecycle_label_status, normalize='index').round(4)
print(ct)
print(pd.crosstab(F.proposed_order_type, F.lifecycle_label_status))
F.to_pickle('filled.pkl')
