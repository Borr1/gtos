import pandas as pd, numpy as np
df=pd.read_pickle('df.pkl')
df['cls']=np.where(df.lifecycle_label_status=='RESOLVED_NO_FILL','NO_FILL',
          np.where(df.lifecycle_label_status.str.startswith('RESOLVED_FILLED'),'RESOLVED','CENSORED'))
print("=== population by order type x class ===")
ct=pd.crosstab(df.proposed_order_type,df.cls,margins=True)
print(ct)
print("\n=== censored breakdown by order type ===")
cen=df[df.cls=='CENSORED']
print(pd.crosstab(cen.lifecycle_label_status,cen.proposed_order_type,margins=True))
print("\n=== FILLABLE population (RESOLVED + CENSORED), censoring rate ===")
fil=df[df.cls!='NO_FILL']
for ot in ['LIMIT','MARKET']:
    s=fil[fil.proposed_order_type==ot]
    r=(s.cls=='CENSORED').mean()
    print(f"  {ot:7s} n_fillable={len(s):7d}  censored={int((s.cls=='CENSORED').sum()):6d}  rate={r:.4f}")
print("\n=== THE FABRICATED CHARGE ===")
print("funnel books a censored selection at  -1.0 - deductible_cost_r   (candidate_funnel_analysis.py:290)")
for ot in ['LIMIT','MARKET']:
    s=fil[fil.proposed_order_type==ot]; c=s[s.cls=='CENSORED']; r=s[s.cls=='RESOLVED']
    charge=(-1.0-c.deductible_cost_r).mean()
    fair=-c.cost_r.mean()
    rate=(s.cls=='CENSORED').mean()
    print(f"  {ot:7s} censor_rate={rate:.4f}  mean_charge={charge:+.5f}  fair_value=-E[cost]={fair:+.5f}  "
          f"excess={charge-fair:+.5f}  contribution_to_book={rate*(charge-fair):+.5f} R/fillable-candidate")
print("\n=== is CENSOR rate outcome-predictable? day-level correlation of censor-rate vs resolved-edge ===")
fil2=fil.copy(); fil2['edge']=fil2.R_engine+fil2.cost_r
g=fil2.groupby('trading_day').apply(lambda d: pd.Series({
    'censor_rate':(d.cls=='CENSORED').mean(),
    'edge':d.loc[d.cls=='RESOLVED','edge'].mean(),
    'n':len(d)}),include_groups=False)
g=g.dropna()
print(f"  days={len(g)}  corr(censor_rate, resolved_edge) = {g.censor_rate.corr(g.edge):+.4f}")
from scipy import stats
r,p=stats.pearsonr(g.censor_rate,g.edge); print(f"  pearson r={r:+.4f} p={p:.4f}")
hi=g[g.censor_rate>g.censor_rate.median()]; lo=g[g.censor_rate<=g.censor_rate.median()]
print(f"  high-censor days edge={hi.edge.mean():+.5f} (n={len(hi)})   low-censor days edge={lo.edge.mean():+.5f} (n={len(lo)})")
